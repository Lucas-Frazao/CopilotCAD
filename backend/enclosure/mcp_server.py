"""
Stdio MCP server for the Evie enclosure connector.

Grok CAD Bot / CoS install this as a local MCP server and call:

  get_evie_spec, generate, validate, export

Transport: newline-delimited JSON-RPC 2.0 (MCP stdio). No Electron. No OnShape.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from enclosure.auth import BotAuthError, authorize_mcp
from enclosure.service import (
    EXPORT_FORMATS,
    export_part,
    generate_part,
    get_evie_spec,
    validate_part,
)
from enclosure.spec_loader import repo_root

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "copilotcad-enclosure"
SERVER_VERSION = "0.2.0"


def _tool_dir() -> Path:
    return repo_root() / "mcps" / "copilotcad" / "tools"


def load_tool_schemas() -> list[dict[str, Any]]:
    """Load machine-readable tool contracts from ``mcps/copilotcad/tools``."""
    directory = _tool_dir()
    tools: list[dict[str, Any]] = []
    for name in ("get_evie_spec", "generate", "validate", "export"):
        path = directory / f"{name}.json"
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        tools.append(
            {
                "name": payload["name"],
                "description": payload.get("description", ""),
                "inputSchema": payload.get("inputSchema") or {"type": "object"},
            }
        )
    return tools


def _text_result(payload: dict[str, Any], *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
        "isError": is_error,
    }


def _call_generate(args: dict[str, Any]) -> dict[str, Any]:
    return generate_part(
        args.get("part"),
        inline_spec=args.get("inline_spec"),
    )


def _call_validate(args: dict[str, Any]) -> dict[str, Any]:
    return validate_part(
        args.get("part"),
        artifact_id=args.get("artifact_id"),
        mate_artifact_id=args.get("mate_artifact_id"),
        inline_spec=args.get("inline_spec"),
    )


def _call_export(args: dict[str, Any]) -> dict[str, Any]:
    fmt = str(args.get("format") or "step").lower()
    if fmt not in EXPORT_FORMATS:
        raise ValueError(f"format must be one of {EXPORT_FORMATS}")
    dest = args.get("dest")
    if dest:
        dest_path = Path(dest)
    else:
        dest_path = Path(tempfile.mkdtemp(prefix="copilotcad-enclosure-")) / f"part.{fmt}"
    return export_part(
        fmt,
        dest_path,
        part=args.get("part"),
        artifact_id=args.get("artifact_id"),
        inline_spec=args.get("inline_spec"),
    )


def _call_get_evie_spec(args: dict[str, Any]) -> dict[str, Any]:
    return get_evie_spec(format=str(args.get("format") or "yaml"))


_HANDLERS = {
    "generate": _call_generate,
    "validate": _call_validate,
    "export": _call_export,
    "get_evie_spec": _call_get_evie_spec,
}


def call_tool(name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    """Dispatch one MCP tool. Used by tests and the stdio loop."""
    args = dict(arguments or {})
    authorize_mcp(args.pop("token", None))
    try:
        handler = _HANDLERS[name]
    except KeyError as exc:
        raise ValueError(f"unknown tool {name!r}; expected one of {sorted(_HANDLERS)}") from exc
    result = handler(args)
    if name == "validate" and not result.get("passed", True):
        return _text_result(result, is_error=False)
    return _text_result(result)


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    """
    Handle one JSON-RPC message. Notifications return ``None``.

    Unknown methods get JSON-RPC ``-32601``. Tool failures are MCP ``isError``.
    """
    method = message.get("method")
    msg_id = message.get("id")
    params = message.get("params") or {}

    if method is None:
        return _rpc_error(msg_id, -32600, "invalid request")

    if msg_id is None:
        return None

    if method == "initialize":
        return _rpc_result(
            msg_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": (
                    "Evie enclosure dogfood connector. Interview until you have a "
                    "machine-readable YAML/JSON spec, then get_evie_spec → generate "
                    "(part or inline_spec) → validate → export. Present the gate "
                    "report and artifact paths for approve/revise. Not product print-GO."
                ),
            },
        )

    if method == "ping":
        return _rpc_result(msg_id, {})

    if method == "tools/list":
        tools = load_tool_schemas()
        if not tools:
            tools = [
                {"name": name, "description": name, "inputSchema": {"type": "object"}}
                for name in _HANDLERS
            ]
        return _rpc_result(msg_id, {"tools": tools})

    if method == "tools/call":
        name = params.get("name")
        if not name:
            return _rpc_error(msg_id, -32602, "tools/call requires name")
        try:
            result = call_tool(str(name), params.get("arguments"))
        except BotAuthError as exc:
            return _rpc_result(msg_id, _text_result({"ok": False, "error": str(exc)}, is_error=True))
        except (ValueError, KeyError, FileNotFoundError, TypeError, json.JSONDecodeError) as exc:
            return _rpc_result(
                msg_id,
                _text_result({"ok": False, "error": str(exc)}, is_error=True),
            )
        except Exception as exc:  # noqa: BLE001
            return _rpc_result(
                msg_id,
                _text_result(
                    {"ok": False, "error": f"{type(exc).__name__}: {exc}"},
                    is_error=True,
                ),
            )
        return _rpc_result(msg_id, result)

    if method in {"resources/list", "prompts/list"}:
        key = "resources" if method == "resources/list" else "prompts"
        return _rpc_result(msg_id, {key: []})

    return _rpc_error(msg_id, -32601, f"method not found: {method}")


def _rpc_result(msg_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _rpc_error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def serve_stdio(
    stdin: Any = None,
    stdout: Any = None,
) -> None:
    """Read newline-delimited JSON-RPC from stdin and write responses to stdout."""
    incoming = stdin if stdin is not None else sys.stdin
    outgoing = stdout if stdout is not None else sys.stdout
    for raw in incoming:
        line = raw.strip() if isinstance(raw, str) else raw.decode("utf-8").strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            outgoing.write(
                json.dumps(_rpc_error(None, -32700, "parse error"), separators=(",", ":")) + "\n"
            )
            outgoing.flush()
            continue
        if not isinstance(message, dict):
            outgoing.write(
                json.dumps(_rpc_error(None, -32600, "invalid request"), separators=(",", ":"))
                + "\n"
            )
            outgoing.flush()
            continue
        response = handle_request(message)
        if response is None:
            continue
        outgoing.write(json.dumps(response, separators=(",", ":")) + "\n")
        outgoing.flush()


def main(argv: list[str] | None = None) -> None:  # noqa: ARG001
    serve_stdio()


if __name__ == "__main__":
    main()
