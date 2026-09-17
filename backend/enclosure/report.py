"""JSON gate-report helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from enclosure.features import NamedFeature

REPORT_SCHEMA = "copilotcad.enclosure.gate_report.v1"


def build_report(
    part: str,
    spec: dict[str, Any],
    measured: dict[str, Any],
    gates: list[dict[str, Any]],
    features: list[NamedFeature] | None = None,
) -> dict[str, Any]:
    scored = [gate for gate in gates if not gate.get("skipped")]
    passed = all(gate["passed"] for gate in scored)
    return {
        "schema": REPORT_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": spec.get("project"),
        "enclosure": spec.get("enclosure"),
        "spec_schema_version": spec.get("schema_version"),
        "part": part,
        "units": spec.get("units", "mm"),
        "design_mm_only": True,
        "passed": passed,
        "measured": measured,
        "features": [item.to_dict() for item in (features or [])],
        "gates": gates,
        "ownership": {
            "product_stl_print_go": (spec.get("owners") or {}).get("product_stl_print_go"),
            "note": "Dogfood only — this report does not grant product print-GO.",
        },
    }


def write_report(report: dict[str, Any], path: Path | str) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out
