"""
Gate-runner CLI for Evie enclosure dogfood.

Examples (from backend/):

    python -m enclosure generate --part badge --out /tmp/evie_badge.step
    python -m enclosure validate --part cover --report /tmp/cover.json
    python -m enclosure validate --part faceplate
    python -m enclosure spec --format yaml
    python -m enclosure serve --port 8765
    python -m enclosure mcp
    python -m enclosure smoke
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib.util import find_spec
from pathlib import Path

from enclosure.http_api import serve_forever
from enclosure.mcp_server import handle_request, serve_stdio
from enclosure.report import write_report
from enclosure.service import export_part, generate_part, get_evie_spec, validate_part
from enclosure.spec_loader import parse_inline_spec


def _print_json(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")


def _load_inline(value: str | None) -> dict | None:
    if not value:
        return None
    if value == "-":
        return parse_inline_spec(sys.stdin.read())
    return parse_inline_spec(value)


def _cmd_generate(args: argparse.Namespace) -> int:
    result = generate_part(args.part, inline_spec=_load_inline(args.inline_spec))
    if args.out:
        exported = export_part(args.format, args.out, artifact_id=result["artifact_id"])
        result["export"] = exported
    _print_json(result)
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    report = validate_part(
        args.part,
        spec_path=args.spec,
        inline_spec=_load_inline(args.inline_spec),
    )
    if args.report:
        write_report(report, args.report)
        report["report_path"] = str(Path(args.report).resolve())
    _print_json(report)
    return 0 if report.get("passed") else 2


def _cmd_export(args: argparse.Namespace) -> int:
    result = export_part(
        args.format,
        args.out,
        part=args.part,
        inline_spec=_load_inline(args.inline_spec),
    )
    _print_json(result)
    return 0


def _cmd_spec(args: argparse.Namespace) -> int:
    payload = get_evie_spec(format=args.format)
    if args.text_only:
        sys.stdout.write(payload["text"])
        return 0
    _print_json(payload)
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    serve_forever(host=args.host, port=args.port)
    return 0


def _cmd_mcp(args: argparse.Namespace) -> int:  # noqa: ARG001
    serve_stdio()
    return 0


def _cmd_smoke(args: argparse.Namespace) -> int:
    """Handshake + get_evie_spec; optionally generate/validate if OCCT is present."""
    init = handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    listed = handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    spec_call = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_evie_spec", "arguments": {"format": "json"}},
        }
    )
    tools = ((listed or {}).get("result") or {}).get("tools") or []
    names = [tool.get("name") for tool in tools]
    payload: dict = {
        "ok": True,
        "initialize": (init or {}).get("result", {}).get("serverInfo"),
        "tools": names,
        "spec_ok": bool(((spec_call or {}).get("result") or {}).get("content")),
        "occt": False,
    }
    if args.skip_geometry:
        _print_json(payload)
        return 0
    if find_spec("OCC") is None:
        payload["geometry"] = "skipped (pythonocc-core unavailable)"
        _print_json(payload)
        return 0

    generated = generate_part("badge")
    report = validate_part(artifact_id=generated["artifact_id"])
    dest = Path(args.out or "/tmp/evie_smoke_badge.step")
    exported = export_part("step", dest, artifact_id=generated["artifact_id"])
    payload["occt"] = True
    payload["generate"] = generated
    payload["validate_passed"] = report.get("passed")
    payload["export_path"] = exported.get("path")
    payload["ok"] = bool(report.get("passed"))
    _print_json(payload)
    return 0 if payload["ok"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="copilotcad-enclosure",
        description="Evie enclosure generate / validate / export (dogfood)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Build a parametric part")
    gen.add_argument("--part", choices=["badge", "cover", "faceplate", "brick"])
    gen.add_argument("--inline-spec", help="YAML/JSON string, file path, or '-' for stdin")
    gen.add_argument("--out", help="Optional export path")
    gen.add_argument("--format", default="step", choices=["step", "stl", "iges"])
    gen.set_defaults(func=_cmd_generate)

    val = sub.add_parser("validate", help="Run hard gates and print a JSON report")
    val.add_argument("--part", choices=["badge", "cover", "faceplate", "brick"])
    val.add_argument("--spec", help="Override path to evie_enclosure_v3_spec.yaml")
    val.add_argument("--inline-spec", help="YAML/JSON string, file path, or '-' for stdin")
    val.add_argument("--report", help="Write the JSON report to this path")
    val.set_defaults(func=_cmd_validate)

    exp = sub.add_parser("export", help="Generate and write STEP/STL/IGES")
    exp.add_argument("--part", choices=["badge", "cover", "faceplate"])
    exp.add_argument("--inline-spec", help="YAML/JSON string, file path, or '-' for stdin")
    exp.add_argument("--out", required=True)
    exp.add_argument("--format", default="step", choices=["step", "stl", "iges"])
    exp.set_defaults(func=_cmd_export)

    spec = sub.add_parser("spec", help="Print the checked-in Evie SoT (get_evie_spec)")
    spec.add_argument("--format", default="yaml", choices=["yaml", "json"])
    spec.add_argument("--text-only", action="store_true", help="Write raw YAML/JSON only")
    spec.set_defaults(func=_cmd_spec)

    srv = sub.add_parser("serve", help="Thin HTTP connector for Grok / CoS")
    srv.add_argument("--host", default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8765)
    srv.set_defaults(func=_cmd_serve)

    mcp = sub.add_parser("mcp", help="Stdio MCP server (generate/validate/export/get_evie_spec)")
    mcp.set_defaults(func=_cmd_mcp)

    smoke = sub.add_parser("smoke", help="MCP handshake + optional badge generate/validate")
    smoke.add_argument("--skip-geometry", action="store_true")
    smoke.add_argument("--out", help="STEP path when OCCT is available")
    smoke.set_defaults(func=_cmd_smoke)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        code = args.func(args)
    except Exception as exc:
        _print_json({"ok": False, "error": str(exc)})
        raise SystemExit(1) from exc
    raise SystemExit(code)
