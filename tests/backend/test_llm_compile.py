"""Tests for LLM adapter and Intent IR compilation (F-005)."""

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
    prompt = build_system_prompt()
    assert "sketch_rectangle" in prompt
    assert "hole_pattern_corners" in prompt
    assert "part_create" in prompt
    assert "millimeters" in prompt.lower()


def test_parse_llm_json_raw_object():
    data = parse_llm_json('{"type": "part_create", "prompt": "x"}')
    assert data["type"] == "part_create"


def test_parse_llm_json_fenced_block():
    text = 'Here is IR:\n```json\n{"type": "part_create", "prompt": "x"}\n```'
    data = parse_llm_json(text)
    assert data["type"] == "part_create"


def test_parse_llm_json_raises_on_garbage():
    with pytest.raises(IRParseError):
        parse_llm_json("not json at all")


def test_compile_intent_mounting_plate_mock():
    adapter = FakeAdapter(json.dumps(mounting_plate_ir()))
    intent = compile_intent("Create mounting plate", adapter)
    assert intent.type == "part_create"
    assert len(intent.steps) == 3


def test_compile_intent_simple_box_mock():
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
    adapter = FakeAdapter("{ broken json")
    with pytest.raises(CompileError) as exc_info:
        compile_intent("bad", adapter)
    assert exc_info.value.error_type == "parse"


def test_compile_intent_validation_error():
    bad_ir = mounting_plate_ir()
    bad_ir["steps"][0]["op"] = "not_a_real_op"
    adapter = FakeAdapter(json.dumps(bad_ir))
    with pytest.raises(CompileError) as exc_info:
        compile_intent("bad op", adapter)
    assert exc_info.value.error_type == "validation"


def test_compile_intent_jsonrpc_mocked():
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
    main._default_adapter = None


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
def test_compile_intent_live_mounting_plate():
    from llm.claude_adapter import ClaudeAdapter

    adapter = ClaudeAdapter()
    intent = compile_intent(
        "Create a mounting plate 100mm by 50mm, 6mm thick, with corner mounting holes "
        "6mm diameter and 8mm offset from edges.",
        adapter,
    )
    assert intent.type == "part_create"
    assert len(intent.steps) >= 1
    ops = {step.op for step in intent.steps}
    assert "sketch_rectangle" in ops or "extrude" in ops
