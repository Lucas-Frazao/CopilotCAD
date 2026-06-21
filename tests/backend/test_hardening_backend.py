"""Backend robustness/hardening tests (cross-cutting fixes).

Covers fixes identified in code review:
- LLM JSON parser: nested braces, decoy braces, string-aware extraction.
- Workspace file reads: dir allow-list, size cap, binary guard, absolute/UNC rejection.
- JSON-RPC main loop: survives a malformed line and keeps serving.
- Executor: unexpected (non-ExecutionError) exceptions are surfaced, not silently identical.
- Claude adapter: project context is delimited and length-capped before sending.
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


# --- LLM JSON parser (M4) -------------------------------------------------


def test_parse_llm_json_handles_nested_objects():
    text = '{"type": "part_create", "constraints": {"dimensions": {"length_mm": 100}}}'
    data = parse_llm_json(text)
    assert data["constraints"]["dimensions"]["length_mm"] == 100


def test_parse_llm_json_ignores_prose_before_and_after():
    text = 'Sure, here is the IR:\n{"type": "part_create", "summary": "ok"}\nLet me know!'
    data = parse_llm_json(text)
    assert data["type"] == "part_create"
    assert data["summary"] == "ok"


def test_parse_llm_json_respects_braces_inside_strings():
    text = '{"type": "part_create", "summary": "uses a } brace in text"}'
    data = parse_llm_json(text)
    assert data["summary"] == "uses a } brace in text"


def test_parse_llm_json_prefers_fenced_block_over_decoy():
    text = (
        "Here is an example {not: valid} you should ignore.\n"
        '```json\n{"type": "part_create", "summary": "real"}\n```'
    )
    data = parse_llm_json(text)
    assert data["summary"] == "real"


def test_parse_llm_json_raises_on_garbage():
    with pytest.raises(IRParseError):
        parse_llm_json("not json at all")


# --- Workspace file read guards (C2, M1) ----------------------------------


def _make_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "proj"
    create_workspace(workspace, "proj")
    create_part_folder(workspace, "mounting_plate")
    return workspace


def test_read_rejects_file_outside_allowed_dirs(tmp_path: Path):
    workspace = _make_workspace(tmp_path)
    # copilotcad.json exists at the workspace root but is not under an allowed dir.
    with pytest.raises(WorkspacePathError):
        read_workspace_file(workspace, "copilotcad.json")


def test_read_rejects_binary_file(tmp_path: Path):
    workspace = _make_workspace(tmp_path)
    blob = workspace / "parts" / "mounting_plate" / "blob.bin"
    blob.write_bytes(b"\xff\xfe\x00\x01\x02")
    with pytest.raises(WorkspacePathError):
        read_workspace_file(workspace, "parts/mounting_plate/blob.bin")


def test_read_rejects_oversized_file(tmp_path: Path, monkeypatch):
    import project.workspace_tree as wt

    monkeypatch.setattr(wt, "MAX_FILE_BYTES", 8, raising=True)
    workspace = _make_workspace(tmp_path)
    big = workspace / "parts" / "mounting_plate" / "big.txt"
    big.write_text("0123456789", encoding="utf-8")  # 10 bytes > 8
    with pytest.raises(WorkspacePathError):
        read_workspace_file(workspace, "parts/mounting_plate/big.txt")


def test_read_rejects_unc_and_absolute_paths(tmp_path: Path):
    workspace = _make_workspace(tmp_path)
    for bad in ("//server/share/x.txt", "/etc/passwd"):
        with pytest.raises(WorkspacePathError):
            read_workspace_file(workspace, bad)


def test_read_allows_normal_part_file(tmp_path: Path):
    workspace = _make_workspace(tmp_path)
    contents = read_workspace_file(workspace, "parts/mounting_plate/spec.yaml")
    assert isinstance(contents, str)


# --- JSON-RPC main loop resilience (C1) -----------------------------------


def test_main_loop_survives_malformed_line(monkeypatch, capsys):
    stdin = io.StringIO(
        "this is not json\n"
        + json.dumps({"jsonrpc": "2.0", "method": "ping", "id": 1})
        + "\n"
    )
    monkeypatch.setattr("sys.stdin", stdin)
    main_module.main()
    out_lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    # The bad line did not crash the loop; ping still produced a pong.
    assert any('"pong"' in line for line in out_lines)


# --- Executor unexpected-exception handling (M2) --------------------------


def test_executor_surfaces_unexpected_exception():
    # A non-numeric param makes the handler raise ValueError (not ExecutionError).
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
    # Unexpected errors are marked distinctly so they are not mistaken for user errors.
    assert "internal" in (result.error or "").lower()


# --- Claude adapter context limiting (M3) ---------------------------------


class _FakeBlock:
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.content = [_FakeBlock(text)]


class _FakeMessages:
    def __init__(self) -> None:
        self.captured: dict[str, Any] | None = None

    def create(self, **kwargs: Any) -> _FakeResponse:
        self.captured = kwargs
        return _FakeResponse('{"type": "part_create"}')


class _FakeClient:
    def __init__(self) -> None:
        self.messages = _FakeMessages()


def test_claude_adapter_delimits_and_caps_context():
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
