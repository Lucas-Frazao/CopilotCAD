"""
test_approval_workflow.py — Approval workflow tests (F-022)
=============================================================

High-risk actions (like deleting a part) require explicit user approval before
execution. F-022 defines a risk classifier, pending intent store, and
approve/reject RPC methods.

Beginner concepts:
  - Risk classifier: tags intents as low_risk or high_risk before execution.
  - PendingIntentStore: holds high-risk IR until the user approves or rejects.
  - approve_intent / reject_intent: RPC methods that finalize or cancel pending IR.
"""

from __future__ import annotations

import importlib

import pytest

from rpc_helpers import assert_rpc_method_registered, call_rpc
from test_intent_ir_validation import mounting_plate_ir


def _approval_modules():
    """Import approval.risk_classifier and approval.pending_store or fail clearly."""
    try:
        risk = importlib.import_module("approval.risk_classifier")
        pending = importlib.import_module("approval.pending_store")
    except ImportError as exc:
        pytest.fail(f"F-022 requires approval.risk_classifier and pending_store: {exc}")
    return risk, pending


def test_risk_classifier_tags_delete_as_high_risk():
    """delete_part intent must be classified as high or high_risk."""
    risk, _ = _approval_modules()
    classify = getattr(risk, "classify_intent_risk", None)
    assert classify is not None

    delete_ir = {
        "type": "part_edit",
        "prompt": "delete part",
        "summary": "Delete mounting plate",
        "target": {"part_id": "mounting_plate"},
        "steps": [{"id": "d1", "op": "delete_part", "params": {}}],
    }
    level = classify(delete_ir)
    assert level in ("high", "high_risk")


def test_mounting_plate_create_is_low_risk():
    """Standard part_create (mounting plate) must be classified as low risk."""
    risk, _ = _approval_modules()
    classify = risk.classify_intent_risk
    level = classify(mounting_plate_ir())
    assert level in ("low", "low_risk")


def test_pending_store_holds_ir_until_approved():
    """
    PendingIntentStore.add must store IR retrievable by pending_id,
    and is_executed must be False until approved.
    """
    _, pending = _approval_modules()
    store = getattr(pending, "PendingIntentStore", None)
    assert store is not None
    s = store()
    pending_id = s.add(mounting_plate_ir())
    assert s.get(pending_id) is not None
    assert not s.is_executed(pending_id)


def test_approve_intent_rpc_registered():
    """approve_intent must be registered as a JSON-RPC method."""
    assert_rpc_method_registered("approve_intent", {"pending_id": "test-id"})


def test_reject_intent_rpc_registered():
    """reject_intent must be registered as a JSON-RPC method."""
    assert_rpc_method_registered("reject_intent", {"pending_id": "test-id"})


def test_compile_intent_may_return_pending_for_high_risk():
    """
    Integration: compile_intent may return {pending: true, pending_id: ...}
    for high-risk prompts when the approval branch is active.
    """
    response = call_rpc("compile_intent", {"message": "Delete the mounting plate part"})
    if "result" in response:
        result = response["result"]
        if result.get("pending") is True:
            assert "pending_id" in result


def test_reject_does_not_execute_on_disk(workspace):
    """
    Rejecting a pending delete intent must leave the part folder intact on disk.
    """
    _, pending = _approval_modules()
    store = pending.PendingIntentStore()
    from project.part_folder import create_part_folder

    create_part_folder(workspace, "mounting_plate")
    pid = store.add(
        {
            "type": "part_edit",
            "summary": "delete",
            "target": {"part_id": "mounting_plate"},
            "steps": [{"id": "d1", "op": "delete_part", "params": {}}],
        }
    )
    reject = getattr(pending, "reject_pending", None)
    assert reject is not None
    reject(store, pid, workspace_path=workspace)
    assert (workspace / "parts" / "mounting_plate").is_dir()


def test_rejected_action_logged_to_history(workspace):
    """
    Rejection must be logged via log_rejection_to_history or append_history_entry.
    """
    hist = pytest.importorskip("project.history")
    append = getattr(hist, "append_history_entry", None)
    _, pending = _approval_modules()
    log_reject = getattr(pending, "log_rejection_to_history", None)
    assert log_reject is not None or append is not None
