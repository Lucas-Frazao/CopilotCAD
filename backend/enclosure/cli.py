"""
Gate-runner CLI for Evie enclosure dogfood.

Examples (from backend/):

    python -m enclosure generate --part badge --out /tmp/evie_badge.step
    python -m enclosure validate --part cover --report /tmp/cover.json
    python -m enclosure validate --part faceplate
    python -m enclosure serve --port 8765
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from enclosure.report import write_report
from enclosure.service import export_part, generate_part, validate_part


def _print_json(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")


def _cmd_generate(args: argparse.Namespace) -> int:
    result = generate_part(args.part)
    if args.out:
        exported = export_part(args.format, args.out, artifact_id=result["artifact_id"])
        result["export"] = exported
    _print_json(result)
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    report = validate_part(args.part, spec_path=args.spec)
    if args.report:
        write_report(report, args.report)
        report["report_path"] = str(Path(args.report).resolve())
    _print_json(report)
    return 0 if report.get("passed") else 2


def _cmd_export(args: argparse.Namespace) -> int:
    result = export_part(args.format, args.out, part=args.part)
    _print_json(result)
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    from enclosure.http_api import serve_forever

    serve_forever(host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="copilotcad-enclosure",
        description="Evie enclosure generate / validate / export (dogfood)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Build a parametric part")
    gen.add_argument("--part", required=True, choices=["badge", "cover", "faceplate", "brick"])
    gen.add_argument("--out", help="Optional export path")
    gen.add_argument("--format", default="step", choices=["step", "stl", "iges"])
    gen.set_defaults(func=_cmd_generate)

    val = sub.add_parser("validate", help="Run hard gates and print a JSON report")
    val.add_argument("--part", required=True, choices=["badge", "cover", "faceplate", "brick"])
    val.add_argument("--spec", help="Override path to evie_enclosure_v3_spec.yaml")
    val.add_argument("--report", help="Write the JSON report to this path")
    val.set_defaults(func=_cmd_validate)

    exp = sub.add_parser("export", help="Generate and write STEP/STL/IGES")
    exp.add_argument("--part", required=True, choices=["badge", "cover", "faceplate"])
    exp.add_argument("--out", required=True)
    exp.add_argument("--format", default="step", choices=["step", "stl", "iges"])
    exp.set_defaults(func=_cmd_export)

    srv = sub.add_parser("serve", help="Thin HTTP connector for Grok / CoS")
    srv.add_argument("--host", default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8765)
    srv.set_defaults(func=_cmd_serve)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        code = args.func(args)
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        _print_json({"ok": False, "error": str(exc)})
        raise SystemExit(1) from exc
    raise SystemExit(code)
