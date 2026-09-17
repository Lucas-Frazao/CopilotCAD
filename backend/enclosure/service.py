"""
Generate / validate / export orchestration for the Evie enclosure connector.

In-process artifact store so a Grok bot can generate, then validate/export
the same solid without a workspace project.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from enclosure.builders import BuiltPart, build_approx_brick, build_part
from enclosure.features import NamedFeature
from enclosure.gates import run_gates
from enclosure.report import build_report
from enclosure.spec_loader import (
    PUBLIC_PARTS as PUBLIC_PARTS,
    default_spec_json_path,
    default_spec_path,
    dump_spec,
    infer_part,
    load_enclosure_spec,
    parse_inline_spec,
)
from engine import kernel_adapter

EXPORT_FORMATS = ("step", "stl", "iges")
SPEC_FORMATS = ("yaml", "json")


@dataclass
class Artifact:
    artifact_id: str
    part: str
    shape: Any
    features: list[NamedFeature] = field(default_factory=list)
    spec: dict[str, Any] | None = None


_STORE: dict[str, Artifact] = {}


def _put(built: BuiltPart, spec: dict[str, Any] | None = None) -> Artifact:
    artifact_id = uuid.uuid4().hex
    artifact = Artifact(
        artifact_id=artifact_id,
        part=built.part,
        shape=built.shape,
        features=list(built.features),
        spec=spec,
    )
    _STORE[artifact_id] = artifact
    return artifact


def get_artifact(artifact_id: str) -> Artifact:
    try:
        return _STORE[artifact_id]
    except KeyError as exc:
        raise KeyError(f"unknown artifact_id {artifact_id!r}") from exc


def _resolve_spec(
    *,
    inline_spec: Any = None,
    spec_path: str | Path | None = None,
    stored: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if inline_spec is not None:
        return parse_inline_spec(inline_spec)
    if spec_path is not None:
        return load_enclosure_spec(spec_path)
    if stored is not None:
        return stored
    return load_enclosure_spec()


def generate_part(
    part: str | None = None,
    *,
    fill: float | None = None,
    inline_spec: Any = None,
    spec_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a parametric part and stash it for later validate/export."""
    spec = _resolve_spec(inline_spec=inline_spec, spec_path=spec_path) if (
        inline_spec is not None or spec_path is not None
    ) else None
    target = infer_part(part, spec)

    if target == "brick":
        built = build_approx_brick(0.80 if fill is None else fill)
    else:
        if target not in PUBLIC_PARTS and target != "brick":
            raise ValueError(f"unknown part {target!r}")
        built = build_part(target)

    if spec is None:
        spec = load_enclosure_spec()
    artifact = _put(built, spec)
    xmin, ymin, zmin, xmax, ymax, zmax = kernel_adapter.shape_bbox(built.shape)
    spec_source = "inline" if inline_spec is not None else (
        "path" if spec_path is not None else "checked-in"
    )
    return {
        "ok": True,
        "part": built.part,
        "artifact_id": artifact.artifact_id,
        "extents": {
            "dx": xmax - xmin,
            "dy": ymax - ymin,
            "dz": zmax - zmin,
        },
        "feature_ids": [item.id for item in built.features],
        "spec_source": spec_source,
        "ownership": "dogfood — not product print-GO",
    }


def validate_part(
    part: str | None = None,
    *,
    artifact_id: str | None = None,
    spec_path: str | Path | None = None,
    mate_artifact_id: str | None = None,
    inline_spec: Any = None,
) -> dict[str, Any]:
    """Run hard gates against a stored or freshly generated solid."""
    if artifact_id:
        artifact = get_artifact(artifact_id)
        target_part = part or artifact.part
        shape = artifact.shape
        features = artifact.features
        stored_spec = artifact.spec
    else:
        if not part and inline_spec is None:
            raise ValueError("part, artifact_id, or inline_spec is required")
        generated = generate_part(part, inline_spec=inline_spec, spec_path=spec_path)
        artifact = get_artifact(generated["artifact_id"])
        target_part = artifact.part
        shape = artifact.shape
        features = artifact.features
        stored_spec = artifact.spec

    spec = _resolve_spec(
        inline_spec=inline_spec,
        spec_path=spec_path,
        stored=stored_spec,
    )
    gate_part = target_part if target_part in spec.get("parts", {}) else "faceplate"
    if target_part == "brick":
        gate_part = "faceplate"

    mate_features = None
    if mate_artifact_id:
        mate_features = get_artifact(mate_artifact_id).features

    measured, gates = run_gates(
        gate_part,
        spec,
        shape,
        features=features,
        mate_features=mate_features,
    )
    report = build_report(gate_part, spec, measured, gates, features)
    report["artifact_id"] = artifact.artifact_id
    report["generated_part"] = target_part
    return report


def export_part(
    format: str,
    dest: Path | str,
    *,
    part: str | None = None,
    artifact_id: str | None = None,
    inline_spec: Any = None,
) -> dict[str, Any]:
    """Write STEP / STL / IGES. Dogfood artifact — not a product release."""
    fmt = format.lower().lstrip(".")
    if fmt not in EXPORT_FORMATS:
        raise ValueError(f"format must be one of {EXPORT_FORMATS}, got {format!r}")

    if artifact_id:
        artifact = get_artifact(artifact_id)
    else:
        if not part and inline_spec is None:
            raise ValueError("part, artifact_id, or inline_spec is required")
        generated = generate_part(part, inline_spec=inline_spec)
        artifact = get_artifact(generated["artifact_id"])

    dest_path = Path(dest)
    if dest_path.suffix == "":
        dest_path = dest_path.with_suffix(f".{fmt}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "step":
        kernel_adapter.export_step(artifact.shape, dest_path)
    elif fmt == "stl":
        kernel_adapter.export_stl(artifact.shape, dest_path)
    else:
        kernel_adapter.export_iges(artifact.shape, dest_path)

    return {
        "ok": True,
        "part": artifact.part,
        "artifact_id": artifact.artifact_id,
        "format": fmt,
        "path": str(dest_path.resolve()),
        "bytes": dest_path.stat().st_size,
        "ownership": "dogfood — not product print-GO",
    }


def get_evie_spec(*, format: str = "yaml") -> dict[str, Any]:
    """Return the checked-in Evie v3 SoT for Grok interviews / revise templates."""
    fmt = format.lower().lstrip(".")
    if fmt not in SPEC_FORMATS:
        raise ValueError(f"format must be one of {SPEC_FORMATS}, got {format!r}")

    path = default_spec_json_path() if fmt == "json" else default_spec_path()
    spec = load_enclosure_spec(path if path.is_file() else None)
    return {
        "ok": True,
        "project": spec.get("project"),
        "enclosure": spec.get("enclosure"),
        "schema_version": spec.get("schema_version"),
        "path": str(path.resolve()) if path.is_file() else str(default_spec_path().resolve()),
        "format": fmt,
        "spec": spec,
        "text": dump_spec(spec, fmt),
        "parts": sorted((spec.get("parts") or {}).keys()),
        "ownership": "dogfood — not product print-GO",
    }
