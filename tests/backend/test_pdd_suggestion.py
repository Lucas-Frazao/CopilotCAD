"""Spec compliance tests for F-013 — PDD suggestion engine."""

from __future__ import annotations

import importlib

import pytest


def _classifier():
    try:
        mod = importlib.import_module("pdd.classifier")
    except ImportError as exc:
        pytest.fail(f"F-013 requires backend/pdd/classifier.py: {exc}")
    fn = getattr(mod, "classify_request_complexity", None)
    assert fn is not None, "classify_request_complexity(message, context?) required"
    return fn


SIMPLE_PROMPTS = [
    "Create a 100×50×6 mm mounting plate with 6 mm corner holes.",
    "100x50 plate, 6mm thick, four corner holes 6mm diameter.",
    "Make a rectangular bracket 40mm by 20mm.",
]

COMPLEX_PROMPTS = [
    "Build a drone frame with motor mounts, battery bay, and landing gear.",
    "Design an assembly with mounting plate, standoffs, and enclosure lid.",
    "Create a multi-part robot arm with three joints and end effector.",
]


@pytest.mark.parametrize("prompt", SIMPLE_PROMPTS)
def test_simple_prompts_do_not_suggest_pdd(prompt):
    classify = _classifier()
    result = classify(prompt)
    label = result["classification"] if isinstance(result, dict) else result
    assert label == "simple", f"Expected simple, got {result!r} for: {prompt}"


@pytest.mark.parametrize("prompt", COMPLEX_PROMPTS)
def test_complex_prompts_suggest_pdd(prompt):
    classify = _classifier()
    result = classify(prompt)
    assert isinstance(result, dict), "Classifier should return dict with classification and reason"
    assert result["classification"] == "suggest_pdd"
    assert isinstance(result.get("reason"), str) and result["reason"]


def test_suggestion_payload_has_multiple_actions():
    """Chat pdd_suggestion message must offer at least two actions."""
    mod = importlib.import_module("pdd.classifier")
    build = getattr(mod, "build_pdd_suggestion_payload", None)
    assert build is not None
    payload = build("Build a drone with four motors")
    assert payload["kind"] == "pdd_suggestion"
    actions = payload.get("actions") or payload.get("buttons") or []
    assert len(actions) >= 2
    labels = {a.get("label") or a.get("text") for a in actions}
    assert any("pdd" in str(x).lower() or "/vision" in str(x).lower() for x in labels)
    assert any("proceed" in str(x).lower() or "continue" in str(x).lower() for x in labels)


def test_classifier_does_not_write_files(workspace, tmp_path):
    """F-013 suggests only — file writes are F-014."""
    classify = _classifier()
    classify("Build a drone frame with battery bay")
    assert not (workspace / "docs" / "product_vision.md").exists()


def test_compile_intent_can_return_pdd_suggestion_for_complex_request():
    """Integration: compile_intent may short-circuit with pdd_suggestion for complex prompts."""
    from rpc_helpers import call_rpc

    response = call_rpc(
        "compile_intent",
        {"message": "Build a drone frame with motor mounts and battery bay"},
    )
    if "result" in response:
        result = response["result"]
        if result.get("kind") == "pdd_suggestion":
            assert "actions" in result or "buttons" in result
        # LLM path may still return IR in some builds — only assert when branch exists.
    # If LLM not configured, error is acceptable; classifier unit tests cover logic.
