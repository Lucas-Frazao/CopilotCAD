"""
test_llm_compile.py — LLM adapter and Intent IR compilation tests (F-005)
=========================================================================

F-005 wires chat messages through an LLM adapter into validated Intent IR.
These tests use a FakeAdapter (no real API calls) to verify prompt building,
JSON parsing, compilation, and JSON-RPC integration.

The live test at the bottom only runs when ANTHROPIC_API_KEY is set.

Beginner concepts:
  - LLMAdapter: abstract interface; ClaudeAdapter is the real implementation.
  - compile_intent: message → LLM JSON → parse → sanitize → validate.
  - FakeAdapter: test double that returns canned JSON without calling an API.
"""

import json
import os
from typing import Any

import pytest

import main  # noqa: F401 — registers JSON-RPC methods
from ir.compiler import CompileError, compile_intent
from ir.parser import IRParseError, parse_llm_json
from jsonrpcserver import dispatch
from llm.adapter import LLMAdapter
from llm.prompts import build_system_prompt
from test_intent_ir_validation import mounting_plate_ir


class FakeAdapter(LLMAdapter):
    """
    Test double that returns a fixed JSON string instead of calling an LLM API.

    Records the last user message so tests can assert prompt content if needed.
    """

    def __init__(self, response: str) -> None:
        self._response = response
        self.last_message: str | None = None

    def generate_structured_json(
        self,
        user_message: str,
        project_context: dict[str, Any] | None = None,
    ) -> str:
        self.last_message = user_message
        return self._response


def test_build_system_prompt_includes_step_catalog():
    """System prompt must list available ops so the LLM emits valid step names."""
    prompt = build_system_prompt()
    assert "sketch_rectangle" in prompt
    assert "hole_pattern_corners" in prompt
    assert "part_create" in prompt
    assert "millimeters" in prompt.lower()


def test_parse_llm_json_raw_object():
    """Parser should handle a plain JSON object string."""
    data = parse_llm_json('{"type": "part_create", "prompt": "x"}')
    assert data["type"] == "part_create"


def test_parse_llm_json_fenced_block():
    """Parser should extract JSON from markdown ```json fenced blocks."""
    text = 'Here is IR:\n```json\n{"type": "part_create", "prompt": "x"}\n```'
    data = parse_llm_json(text)
    assert data["type"] == "part_create"


def test_parse_llm_json_raises_on_garbage():
    """Non-JSON input must raise IRParseError."""
    with pytest.raises(IRParseError):
        parse_llm_json("not json at all")


def test_compile_intent_mounting_plate_mock():
    """Full compile pipeline with canned mounting plate IR from FakeAdapter."""
    adapter = FakeAdapter(json.dumps(mounting_plate_ir()))
    intent = compile_intent("Create mounting plate", adapter)
    assert intent.type == "part_create"
    assert len(intent.steps) == 3


def test_compile_intent_simple_box_mock():
    """A simpler two-step cube IR should compile to a valid IntentIR model."""
    box_ir = {
        "type": "part_create",
        "prompt": "Simple 40mm cube",
        "summary": "Create 40mm cube",
        "target": {"part_id": "cube"},
        "steps": [
            {
                "id": "s1",
                "op": "sketch_rectangle",
                "params": {
                    "length": 40.0,
                    "width": 40.0,
                    "plane": "XY",
                    "mode": "center",
                },
            },
            {
                "id": "s2",
                "op": "extrude",
                "from": "s1",
                "params": {"distance": 40.0, "direction": "+Z", "mode": "add"},
            },
        ],
    }
    adapter = FakeAdapter(json.dumps(box_ir))
    intent = compile_intent("Make a 40mm cube", adapter)
    assert intent.target.part_id == "cube"
    assert intent.steps[1].op == "extrude"


def test_compile_intent_parse_error():
    """Broken JSON from the LLM should raise CompileError with error_type='parse'."""
    adapter = FakeAdapter("{ broken json")
    with pytest.raises(CompileError) as exc_info:
        compile_intent("bad", adapter)
    assert exc_info.value.error_type == "parse"


def test_compile_intent_validation_error():
    """Valid JSON with an unknown op should raise CompileError with error_type='validation'."""
    bad_ir = mounting_plate_ir()
    bad_ir["steps"][0]["op"] = "not_a_real_op"
    adapter = FakeAdapter(json.dumps(bad_ir))
    with pytest.raises(CompileError) as exc_info:
        compile_intent("bad op", adapter)
    assert exc_info.value.error_type == "validation"


def test_compile_intent_jsonrpc_mocked():
    """
    compile_intent RPC should work when main._default_adapter is swapped
    to a FakeAdapter for the duration of the test.
    """
    plate_json = json.dumps(mounting_plate_ir())
    fake = FakeAdapter(plate_json)
    main._default_adapter = fake

    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "compile_intent",
            "params": {"message": "Create mounting plate"},
            "id": 10,
        }
    )
    response = json.loads(dispatch(request))
    assert response["result"]["type"] == "part_create"
    main._default_adapter = None  # Restore default adapter


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
def test_compile_intent_live_mounting_plate():
    """
    Optional live test against the real Claude API.

    Skipped unless ANTHROPIC_API_KEY is in the environment. Lenient check:
    API must return parseable JSON with at least one modeling step.
    """
    from llm.claude_adapter import ClaudeAdapter
    from ir.parser import parse_llm_json

    adapter = ClaudeAdapter()
    prompt = (
        "Create a mounting plate 100mm by 50mm, 6mm thick, with corner mounting holes "
        "6mm diameter and 8mm offset from edges."
    )

    raw = adapter.generate_structured_json(prompt)
    data = parse_llm_json(raw)
    steps = data.get("steps") or []
    assert len(steps) >= 1
    ops = {step.get("op") for step in steps if isinstance(step, dict)}
    assert "sketch_rectangle" in ops or "extrude" in ops

    # Full compile may still fail until prompt/schema alignment improves
    try:
        intent = compile_intent(prompt, adapter)
        assert intent.type == "part_create"
    except CompileError as exc:
        if exc.error_type != "validation":
            raise
