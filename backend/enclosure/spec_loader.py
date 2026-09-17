"""Load the Evie enclosure machine-readable spec (YAML or JSON)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

SPEC_RELATIVE = Path("specs/evie/evie_enclosure_v3_spec.yaml")
SPEC_JSON_RELATIVE = Path("specs/evie/evie_enclosure_v3_spec.json")

PUBLIC_PARTS = ("badge", "cover", "faceplate")


def repo_root() -> Path:
    """Walk parents until AGENTS.md is found (repo root)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "AGENTS.md").is_file():
            return parent
    raise FileNotFoundError("Could not locate CopilotCAD repo root (missing AGENTS.md)")


def default_spec_path() -> Path:
    return repo_root() / SPEC_RELATIVE


def default_spec_json_path() -> Path:
    return repo_root() / SPEC_JSON_RELATIVE


def _as_mapping(loaded: Any, source: str) -> dict[str, Any]:
    if not isinstance(loaded, dict):
        raise TypeError(f"Enclosure spec must be a mapping, got {type(loaded).__name__} ({source})")
    return loaded


def load_enclosure_spec(path: Path | str | None = None) -> dict[str, Any]:
    """
    Load the Evie v3 enclosure spec.

    Accepts ``.yaml`` / ``.yml`` / ``.json``. Defaults to the checked-in SoT.
    """
    spec_path = Path(path) if path is not None else default_spec_path()
    if not spec_path.is_file():
        raise FileNotFoundError(f"Enclosure spec not found: {spec_path}")

    text = spec_path.read_text(encoding="utf-8")
    suffix = spec_path.suffix.lower()
    if suffix == ".json":
        loaded = json.loads(text)
    else:
        loaded = yaml.safe_load(text)

    spec = _as_mapping(loaded, str(spec_path))
    validate_spec_shape(spec)
    return spec


def validate_spec_shape(spec: dict[str, Any]) -> None:
    """Require the Grok-bot contract: a ``parts`` mapping of enclosure solids."""
    parts = spec.get("parts")
    if not isinstance(parts, dict) or not parts:
        raise ValueError("spec must include a non-empty parts mapping (badge/cover/faceplate)")


def parse_spec_text(text: str, *, source: str = "inline") -> dict[str, Any]:
    """Parse a YAML or JSON document into a spec mapping."""
    stripped = text.strip()
    if not stripped:
        raise ValueError("inline_spec is empty")
    if stripped.startswith("{") or stripped.startswith("["):
        loaded = json.loads(stripped)
    else:
        loaded = yaml.safe_load(stripped)
    spec = _as_mapping(loaded, source)
    validate_spec_shape(spec)
    return spec


def parse_inline_spec(inline_spec: Any) -> dict[str, Any]:
    """
    Accept a mapping, YAML/JSON string, or filesystem path to a spec file.

    Paths ending in ``.yaml`` / ``.yml`` / ``.json`` that are missing raise
    ``FileNotFoundError`` instead of being parsed as YAML scalars.
    """
    if inline_spec is None:
        raise ValueError("inline_spec is required")
    if isinstance(inline_spec, dict):
        validate_spec_shape(inline_spec)
        return inline_spec
    if not isinstance(inline_spec, str):
        raise TypeError(
            f"inline_spec must be a mapping, YAML/JSON string, or path, got {type(inline_spec).__name__}"
        )

    text = inline_spec.strip()
    if not text:
        raise ValueError("inline_spec is empty")

    as_path = Path(text)
    looks_like_path = text.endswith((".yaml", ".yml", ".json")) or as_path.is_file()
    if looks_like_path:
        if not as_path.is_file():
            raise FileNotFoundError(f"Enclosure spec not found: {as_path}")
        return load_enclosure_spec(as_path)
    return parse_spec_text(text, source="inline_spec")


def infer_part(part: str | None, spec: dict[str, Any] | None) -> str:
    """
    Resolve which solid to build.

    Order: explicit ``part`` argument, then ``spec.part`` / ``spec.generate_part``,
    then a single public key under ``spec.parts``.
    """
    if part:
        return str(part)
    if spec is None:
        raise ValueError("part or inline_spec is required")
    explicit = spec.get("part") or spec.get("generate_part")
    if explicit:
        return str(explicit)
    parts = spec.get("parts") or {}
    known = [name for name in parts if name in PUBLIC_PARTS]
    if len(known) == 1:
        return known[0]
    raise ValueError(
        "part is required when inline_spec does not name exactly one of "
        f"{list(PUBLIC_PARTS)} (got {sorted(parts)})"
    )


def dump_spec(spec: dict[str, Any], fmt: str = "yaml") -> str:
    """Serialize a spec mapping to YAML or JSON text."""
    normalized = fmt.lower().lstrip(".")
    if normalized == "json":
        return json.dumps(spec, indent=2) + "\n"
    if normalized in {"yaml", "yml"}:
        return yaml.safe_dump(spec, sort_keys=False)
    raise ValueError(f"format must be yaml or json, got {fmt!r}")
