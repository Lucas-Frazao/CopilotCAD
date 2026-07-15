"""
test_hardening_backend.py — Backend robustness and hardening tests
===================================================================

Cross-cutting hardening fixes identified in code review. These tests are not
tied to a single F-0xx spec — they guard against regressions in:

  - LLM JSON parser (nested braces, decoy braces, string-aware extraction)
  - Workspace file read guards (dir allow-list, size cap, binary guard)
  - JSON-RPC main loop resilience (survives malformed input lines)
  - Executor unexpected-exception handling (distinct from user errors)
  - Claude adapter context limiting (length cap, delimiters)

Beginner concepts:
  - Hardening: defensive fixes that prevent crashes or security issues.
  - monkeypatch: pytest fixture that temporarily replaces module attributes.
  - capsys: pytest fixture that captures stdout/stderr during a test.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest

import main as main_module
from ir.parser import IRParseError, parse_llm_json
from project.part_folder import create_part_folder
from project.workspace import create_workspace
from project.workspace_tree import WorkspacePathError, read_workspace_file
from schemas.intent_ir import IRStep, IRTarget, IntentIR


# --- LLM JSON parser hardening (M4) -----------------------------------------


def test_parse_llm_json_handles_nested_objects():
    """Parser must handle nested JSON objects, not just flat key-value pairs."""
    text = '{"type": "part_create", "constraints": {"dimensions": {"length_mm": 100}}}'
    data = parse_llm_json(text)
    assert data["constraints"]["dimensions"]["length_mm"] == 100


def test_parse_llm_json_ignores_prose_before_and_after():
    """
    LLMs often wrap JSON in prose; parser must extract the object and ignore
    surrounding text.
    """
    text = 'Sure, here is the IR:\n{"type": "part_create", "summary": "ok"}\nLet me know!'
    data = parse_llm_json(text)
    assert data["type"] == "part_create"
    assert data["summary"] == "ok"


def test_parse_llm_json_respects_braces_inside_strings():
    """
    A closing brace inside a JSON string value must not prematurely end parsing.
    """
    text = '{"type": "part_create", "summary": "uses a } brace in text"}'
    data = parse_llm_json(text)
    assert data["summary"] == "uses a } brace in text"


def test_parse_llm_json_prefers_fenced_block_over_decoy():
    """
    When both a decoy brace block and a ```json fenced block exist,
    the fenced block must win.
    """
    text = (
        "Here is an example {not: valid} you should ignore.\n"
        '```json\n{"type": "part_create", "summary": "real"}\n```'
    )
    data = parse_llm_json(text)
    assert data["summary"] == "real"


def test_parse_llm_json_raises_on_garbage():
    """Completely unparseable input must raise IRParseError."""
    with pytest.raises(IRParseError):
        parse_llm_json("not json at all")


# --- Workspace file read guards (C2, M1) ----------------------------------


def _make_workspace(tmp_path: Path) -> Path:
    """Helper: create a workspace with a mounting_plate part folder."""
    workspace = tmp_path / "proj"
    create_workspace(workspace, "proj")
    create_part_folder(workspace, "mounting_plate")
    return workspace


def test_read_rejects_file_outside_allowed_dirs(tmp_path: Path):
    """
    copilotcad.json exists at the workspace root but is not under an allowed
    read directory (docs/, parts/, etc.) — must be rejected.
    """
    workspace = _make_workspace(tmp_path)
    with pytest.raises(WorkspacePathError):
        read_workspace_file(workspace, "copilotcad.json")


def test_read_rejects_binary_file(tmp_path: Path):
    """Binary files (.bin) must not be returned as text — raise WorkspacePathError."""
    workspace = _make_workspace(tmp_path)
    blob = workspace / "parts" / "mounting_plate" / "blob.bin"
    blob.write_bytes(b"\xff\xfe\x00\x01\x02")
    with pytest.raises(WorkspacePathError):
        read_workspace_file(workspace, "parts/mounting_plate/blob.bin")


def test_read_rejects_oversized_file(tmp_path: Path, monkeypatch):
    """
    Files larger than MAX_FILE_BYTES must be rejected.

    monkeypatch temporarily sets MAX_FILE_BYTES to 8 for this test only.
    """
    import project.workspace_tree as wt

    monkeypatch.setattr(wt, "MAX_FILE_BYTES", 8, raising=True)
    workspace = _make_workspace(tmp_path)
    big = workspace / "parts" / "mounting_plate" / "big.txt"
    big.write_text("0123456789", encoding="utf-8")  # 10 bytes > 8 byte cap
    with pytest.raises(WorkspacePathError):
        read_workspace_file(workspace, "parts/mounting_plate/big.txt")


def test_read_rejects_unc_and_absolute_paths(tmp_path: Path):
    """
    UNC paths (//server/share) and absolute paths (/etc/passwd) must be rejected
    to prevent reading files outside the workspace sandbox.
    """
    workspace = _make_workspace(tmp_path)
    for bad in ("//server/share/x.txt", "/etc/passwd"):
        with pytest.raises(WorkspacePathError):
            read_workspace_file(workspace, bad)


def test_read_allows_normal_part_file(tmp_path: Path):
    """A normal spec.yaml under parts/ must be readable as a string."""
    workspace = _make_workspace(tmp_path)
    contents = read_workspace_file(workspace, "parts/mounting_plate/spec.yaml")
    assert isinstance(contents, str)


# --- JSON-RPC main loop resilience (C1) -------------------------------------


def test_main_loop_survives_malformed_line(monkeypatch, capsys):
    """
    The backend main loop must skip malformed JSON lines and keep serving.

    monkeypatch replaces sys.stdin with a fake stream; capsys captures stdout.
    """
    stdin = io.StringIO(
        "this is not json\n"
        + json.dumps({"jsonrpc": "2.0", "method": "ping", "id": 1})
        + "\n"
    )
    monkeypatch.setattr("sys.stdin", stdin)
    main_module.main()
    out_lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    # The bad line did not crash the loop; ping still produced a pong response.
    assert any('"pong"' in line for line in out_lines)


# --- Executor unexpected-exception handling (M2) ----------------------------


def test_executor_surfaces_unexpected_exception():
    """
    A non-numeric param makes the handler raise ValueError (not ExecutionError).
    The executor must mark this as an internal error, distinct from user errors.
    """
    intent = IntentIR.model_construct(
        type="part_create",
        prompt="bad params",
        summary="unexpected error",
        target=IRTarget(part_id="p1"),
        steps=[
            IRStep.model_construct(
                id="s1",
                op="sketch_rectangle",
                params={"length": "not-a-number", "width": 10.0, "plane": "XY", "mode": "center"},
                from_step=None,
            )
        ],
    )
    from engine.executor import execute_intent_ir

    result = execute_intent_ir(intent)
    assert not result.success
    assert "internal" in (result.error or "").lower()


# --- Claude adapter context limiting (M3) -----------------------------------


class _FakeBlock:
    """Minimal stand-in for an Anthropic API content block."""

    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class _FakeResponse:
    """Minimal stand-in for an Anthropic API response object."""

    def __init__(self, text: str) -> None:
        self.content = [_FakeBlock(text)]


class _FakeMessages:
    """Captures kwargs passed to messages.create for assertion."""

    def __init__(self) -> None:
        self.captured: dict[str, Any] | None = None

    def create(self, **kwargs: Any) -> _FakeResponse:
        self.captured = kwargs
        return _FakeResponse('{"type": "part_create"}')


class _FakeClient:
    """Minimal stand-in for an Anthropic client with a messages API."""

    def __init__(self) -> None:
        self.messages = _FakeMessages()


def test_claude_adapter_delimits_and_caps_context():
    """
    ClaudeAdapter must wrap project context in XML delimiters and truncate
    oversized context before sending to the API.
    """
    from llm.claude_adapter import MAX_CONTEXT_CHARS, ClaudeAdapter

    client = _FakeClient()
    adapter = ClaudeAdapter(client=client, api_key="test-key")

    huge_context = {"blob": "x" * (MAX_CONTEXT_CHARS * 2)}
    adapter.generate_structured_json("make a plate", project_context=huge_context)

    sent = client.messages.captured["messages"][0]["content"]
    assert "<project_context>" in sent
    assert "<user_message>" in sent
    assert "truncated" in sent.lower()
    # The full huge blob must not be passed through verbatim.
    assert len(sent) < MAX_CONTEXT_CHARS * 2
