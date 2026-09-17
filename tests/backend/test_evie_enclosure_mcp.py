"""
test_evie_enclosure_mcp.py — Grok CAD Bot MCP / inline_spec connector
====================================================================

Protocol + get_evie_spec run without OCCT. Generate/validate/export via MCP
skip when pythonocc-core is missing (same as week-1 enclosure tests).
"""

from __future__ import annotations

import io
import json
from importlib.util import find_spec
from pathlib import Path

import pytest

from enclosure.auth import DEFAULT_TOKEN, BotAuthError, authorize_mcp
from enclosure.cli import main as enclosure_main
from enclosure.mcp_server import call_tool, handle_request, load_tool_schemas, serve_stdio
from enclosure.service import generate_part, get_evie_spec, validate_part
from enclosure.spec_loader import infer_part, parse_inline_spec

HAS_OCCT = find_spec("OCC") is not None
needs_occt = pytest.mark.skipif(not HAS_OCCT, reason="pythonocc-core not installed")


MINIMAL_BADGE_SPEC = {
    "schema_version": "1.1",
    "project": "Evie",
    "enclosure": "v3",
    "units": "mm",
    "parts": {
        "badge": {
            "extents": {"x": 45, "y": 15, "z": 2},
            "extents_tol": 1.0,
        }
    },
}


def _rpc(method: str, params: dict | None = None, msg_id: int = 1) -> dict:
    message = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        message["params"] = params
    response = handle_request(message)
    assert response is not None
    return response


def test_parse_inline_spec_accepts_yaml_json_and_path(tmp_path: Path):
    yaml_text = "parts:\n  badge:\n    extents: {x: 45, y: 15, z: 2}\n"
    from_yaml = parse_inline_spec(yaml_text)
    from_obj = parse_inline_spec(MINIMAL_BADGE_SPEC)
    path = tmp_path / "badge.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    from_path = parse_inline_spec(str(path))
    assert "badge" in from_yaml["parts"]
    assert from_obj["project"] == "Evie"
    assert "badge" in from_path["parts"]


def test_parse_inline_spec_rejects_empty_and_scalar():
    with pytest.raises(ValueError):
        parse_inline_spec("")
    with pytest.raises(TypeError):
        parse_inline_spec("badge")
    with pytest.raises(ValueError):
        parse_inline_spec({"project": "Evie"})


def test_infer_part_from_single_public_key():
    assert infer_part(None, MINIMAL_BADGE_SPEC) == "badge"
    assert infer_part("cover", MINIMAL_BADGE_SPEC) == "cover"
    with pytest.raises(ValueError):
        infer_part(None, None)


def test_get_evie_spec_returns_checked_in_sot():
    payload = get_evie_spec(format="json")
    assert payload["ok"] is True
    assert payload["project"] == "Evie"
    assert "badge" in payload["parts"]
    assert '"project": "Evie"' in payload["text"] or '"project":"Evie"' in payload["text"]
    yaml_payload = get_evie_spec(format="yaml")
    assert "project:" in yaml_payload["text"]


def test_mcp_initialize_and_tools_list():
    init = _rpc("initialize", {})
    info = init["result"]["serverInfo"]
    assert info["name"] == "copilotcad-enclosure"
    listed = _rpc("tools/list", {}, msg_id=2)
    names = {tool["name"] for tool in listed["result"]["tools"]}
    assert names == {"generate", "validate", "export", "get_evie_spec"}
    schemas = {tool["name"] for tool in load_tool_schemas()}
    assert schemas == names


def test_mcp_get_evie_spec_tool():
    response = _rpc(
        "tools/call",
        {"name": "get_evie_spec", "arguments": {"format": "json"}},
    )
    result = response["result"]
    assert result["isError"] is False
    body = json.loads(result["content"][0]["text"])
    assert body["ok"] is True
    assert body["project"] == "Evie"


def test_mcp_notification_has_no_response():
    assert handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


def test_mcp_unknown_method():
    response = _rpc("nope/nope", {})
    assert response["error"]["code"] == -32601


def test_mcp_auth_default_stub_allows_omitted_token(monkeypatch):
    monkeypatch.delenv("COPILOTCAD_BOT_TOKEN", raising=False)
    authorize_mcp(None)
    authorize_mcp(DEFAULT_TOKEN)
    with pytest.raises(BotAuthError):
        authorize_mcp("wrong-token")


def test_mcp_auth_custom_token_required(monkeypatch):
    monkeypatch.setenv("COPILOTCAD_BOT_TOKEN", "secret-bot")
    with pytest.raises(BotAuthError):
        authorize_mcp(None)
    authorize_mcp("secret-bot")
    response = _rpc(
        "tools/call",
        {"name": "get_evie_spec", "arguments": {"format": "json"}},
    )
    body = json.loads(response["result"]["content"][0]["text"])
    assert body["ok"] is False
    assert "token" in body["error"]

    ok = _rpc(
        "tools/call",
        {
            "name": "get_evie_spec",
            "arguments": {"format": "json", "token": "secret-bot"},
        },
        msg_id=2,
    )
    ok_body = json.loads(ok["result"]["content"][0]["text"])
    assert ok_body["ok"] is True


def test_mcp_stdio_roundtrip_get_evie_spec():
    request = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "get_evie_spec", "arguments": {"format": "json"}},
        }
    )
    stdin = io.StringIO(request + "\n")
    stdout = io.StringIO()
    serve_stdio(stdin=stdin, stdout=stdout)
    lines = [line for line in stdout.getvalue().splitlines() if line.strip()]
    assert len(lines) == 1
    message = json.loads(lines[0])
    body = json.loads(message["result"]["content"][0]["text"])
    assert body["ok"] is True


def test_mcp_generate_requires_part_or_inline_spec():
    response = _rpc("tools/call", {"name": "generate", "arguments": {}})
    assert response["result"]["isError"] is True
    body = json.loads(response["result"]["content"][0]["text"])
    assert body["ok"] is False


@needs_occt
def test_mcp_generate_validate_export_badge_inline_spec(tmp_path: Path):
    generated = call_tool("generate", {"part": "badge", "inline_spec": MINIMAL_BADGE_SPEC})
    assert generated["isError"] is False
    body = json.loads(generated["content"][0]["text"])
    artifact_id = body["artifact_id"]
    assert body["spec_source"] == "inline"

    report_msg = call_tool("validate", {"artifact_id": artifact_id})
    report = json.loads(report_msg["content"][0]["text"])
    assert report["passed"] is True

    dest = tmp_path / "badge.step"
    exported_msg = call_tool(
        "export",
        {"artifact_id": artifact_id, "format": "step", "dest": str(dest)},
    )
    exported = json.loads(exported_msg["content"][0]["text"])
    assert exported["bytes"] > 0
    assert dest.is_file()


@needs_occt
def test_inline_spec_revise_fails_then_sot_passes():
    wrong = {
        "schema_version": "1.1",
        "project": "Evie",
        "units": "mm",
        "parts": {
            "badge": {
                "extents": {"x": 10, "y": 10, "z": 10},
                "extents_tol": 0.2,
            }
        },
    }
    generated = generate_part("badge", inline_spec=MINIMAL_BADGE_SPEC)
    failed = validate_part(artifact_id=generated["artifact_id"], inline_spec=wrong)
    assert failed["passed"] is False
    passed = validate_part(artifact_id=generated["artifact_id"], inline_spec=MINIMAL_BADGE_SPEC)
    assert passed["passed"] is True


def test_cli_spec_and_smoke_skip_geometry(capsys):
    with pytest.raises(SystemExit) as spec_exit:
        enclosure_main(["spec", "--format", "json"])
    assert spec_exit.value.code == 0
    spec_out = json.loads(capsys.readouterr().out)
    assert spec_out["ok"] is True
    assert spec_out["project"] == "Evie"

    with pytest.raises(SystemExit) as smoke_exit:
        enclosure_main(["smoke", "--skip-geometry"])
    assert smoke_exit.value.code == 0
    smoke_out = json.loads(capsys.readouterr().out)
    assert smoke_out["ok"] is True
    assert "get_evie_spec" in smoke_out["tools"]
