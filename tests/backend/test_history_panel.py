"""
test_history_panel.py — History panel spec compliance tests (F-017)
===================================================================

The history panel shows an audit log of actions on each part: executes, exports,
assumption changes, etc. F-017 defines get_part_history and append_history_entry.

These tests verify RPC registration, history.json read/write, schema fields,
and that execute_intent appends history on the golden path.

Beginner concepts:
  - history.json: JSON file under parts/<id>/ with an events[] array.
  - History entry: {id, timestamp, type, summary, step_ids, ...}.
  - append_history_entry: backend function that appends one event to the log.
"""

from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone

import pytest

from project.part_folder import HISTORY_FILENAME, create_part_folder
from rpc_helpers import assert_rpc_method_registered, call_rpc, assert_rpc_success
from spec_fixtures import read_history_events


def _history_module():
    """Import project.history or fail with a clear F-017 pending message."""
    try:
        return importlib.import_module("project.history")
    except ImportError as exc:
        pytest.fail(f"F-017 requires backend/project/history.py: {exc}")


def test_get_part_history_rpc_registered(workspace):
    """get_part_history must be registered as a JSON-RPC method."""
    create_part_folder(workspace, "mounting_plate")
    assert_rpc_method_registered(
        "get_part_history",
        {"workspace_path": str(workspace), "part_id": "mounting_plate"},
    )


def test_append_execute_history_entry(workspace):
    """
    append_history_entry should write one execute event to history.json
    with the expected summary and step_ids.
    """
    hist = _history_module()
    append = getattr(hist, "append_history_entry", None)
    assert append is not None

    create_part_folder(workspace, "mounting_plate")
    append(
        workspace,
        "mounting_plate",
        {
            "id": "h1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "execute",
            "summary": "Added corner holes",
            "step_ids": ["s3"],
            "assumption_ids_changed": ["a2"],
        },
    )
    events = read_history_events(workspace, "mounting_plate")
    assert len(events) == 1
    assert events[0]["summary"] == "Added corner holes"
    assert events[0]["step_ids"] == ["s3"]


def test_get_part_history_returns_parsed_entries(workspace):
    """get_part_history should parse history.json and return the events list."""
    hist = _history_module()
    get_history = getattr(hist, "get_part_history", None)
    assert get_history is not None

    create_part_folder(workspace, "mounting_plate")
    path = workspace / "parts" / "mounting_plate" / HISTORY_FILENAME
    path.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "id": "h1",
                        "timestamp": "2026-01-01T00:00:00Z",
                        "type": "execute",
                        "summary": "Sketch rectangle",
                        "step_ids": ["s1"],
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    entries = get_history(workspace, "mounting_plate")
    assert len(entries) == 1
    assert entries[0]["type"] == "execute"


def test_get_part_history_jsonrpc(workspace):
    """get_part_history RPC should return actions, events, or a list."""
    create_part_folder(workspace, "mounting_plate")
    response = call_rpc(
        "get_part_history",
        {"workspace_path": str(workspace), "part_id": "mounting_plate"},
    )
    result = assert_rpc_success(response)
    assert "actions" in result or "events" in result or isinstance(result, list)


def test_history_entry_schema_mvp_fields():
    """
    History module must expose HistoryEntry or validate_history_entry
    to enforce the MVP entry schema (id, timestamp, type, summary, step_ids).
    """
    hist = _history_module()
    schema = getattr(hist, "HistoryEntry", None) or getattr(hist, "validate_history_entry", None)
    assert schema is not None, "History module must validate entry schema"


def test_execute_appends_history_on_golden_path(workspace, mounting_plate_ir_dict):
    """
    End-to-end: execute_intent on the golden plate IR must append at least one
    history entry (depends on OCCT being available).
    """
    pytest.importorskip("OCC.Core.TopoDS")
    from rpc_helpers import call_rpc

    create_part_folder(workspace, "mounting_plate")
    ir = dict(mounting_plate_ir_dict)
    ir["context"] = {"workspace_path": str(workspace), "active_part_id": "mounting_plate"}
    call_rpc("execute_intent", {"ir": ir, "workspace_path": str(workspace)})

    events = read_history_events(workspace, "mounting_plate")
    assert len(events) >= 1
