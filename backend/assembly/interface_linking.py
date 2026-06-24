"""Interface linking for assembly mates (F-021)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from project.part_folder import PARTS_DIR, SPEC_FILENAME
from schemas.intent_ir import IntentIR
from schemas.problem import Problem


def resolve_interface_pair(intent: IntentIR) -> tuple[str, str] | None:
    refs = intent.links.interface_refs
    if len(refs) >= 2:
        return refs[0], refs[1]
    return None


def _load_part_spec(workspace: Path, part_id: str) -> dict[str, Any] | None:
    path = workspace / PARTS_DIR / part_id / SPEC_FILENAME
    if not path.is_file():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def _save_part_spec(workspace: Path, part_id: str, spec: dict[str, Any]) -> None:
    path = workspace / PARTS_DIR / part_id / SPEC_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")


def _find_interface_owner(workspace: Path, interface_id: str) -> tuple[str, dict[str, Any]] | None:
    parts_dir = workspace / PARTS_DIR
    if not parts_dir.is_dir():
        return None

    for part_dir in parts_dir.iterdir():
        if not part_dir.is_dir():
            continue
        spec = _load_part_spec(workspace, part_dir.name)
        if not spec:
            continue
        interfaces = spec.get("interfaces", [])
        if not isinstance(interfaces, list):
            continue
        for interface in interfaces:
            if isinstance(interface, dict) and interface.get("id") == interface_id:
                return part_dir.name, spec
    return None


def _set_connects_to(
    spec: dict[str, Any],
    interface_id: str,
    *,
    part_id: str,
    remote_interface_id: str,
) -> None:
    interfaces = spec.get("interfaces", [])
    for interface in interfaces:
        if interface.get("id") != interface_id:
            continue
        interface["connects_to"] = {
            "part_id": part_id,
            "interface_id": remote_interface_id,
        }


def apply_interface_links_for_mate(workspace: Path, intent: IntentIR) -> None:
    pair = resolve_interface_pair(intent)
    if pair is None:
        return

    iface_a, iface_b = pair
    owner_a = _find_interface_owner(workspace, iface_a)
    owner_b = _find_interface_owner(workspace, iface_b)
    if owner_a is None or owner_b is None:
        return

    part_a, spec_a = owner_a
    part_b, spec_b = owner_b

    _set_connects_to(spec_a, iface_a, part_id=part_b, remote_interface_id=iface_b)
    _set_connects_to(spec_b, iface_b, part_id=part_a, remote_interface_id=iface_a)

    _save_part_spec(workspace, part_a, spec_a)
    _save_part_spec(workspace, part_b, spec_b)


def evaluate_interface_conflicts(workspace: Path) -> list[Problem]:
    problems: list[Problem] = []
    interfaces_by_part: list[tuple[str, dict[str, Any]]] = []

    parts_dir = workspace / PARTS_DIR
    if not parts_dir.is_dir():
        return problems

    for part_dir in parts_dir.iterdir():
        if not part_dir.is_dir():
            continue
        spec = _load_part_spec(workspace, part_dir.name)
        if not spec:
            continue
        interfaces = spec.get("interfaces", [])
        if not isinstance(interfaces, list):
            continue
        for interface in interfaces:
            if isinstance(interface, dict):
                interfaces_by_part.append((part_dir.name, interface))

    seen_pairs: set[tuple[str, str]] = set()
    for index_a, (part_a, iface_a) in enumerate(interfaces_by_part):
        for part_b, iface_b in interfaces_by_part[index_a + 1 :]:
            if part_a == part_b:
                continue
            pair_key = tuple(sorted((f"{part_a}:{iface_a.get('id')}", f"{part_b}:{iface_b.get('id')}")))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            local_pattern = iface_a.get("bolt_pattern")
            remote_pattern = iface_b.get("bolt_pattern")
            if local_pattern and remote_pattern and local_pattern != remote_pattern:
                problems.append(
                    Problem(
                        id=f"interface_conflict:{part_a}:{iface_a.get('id')}",
                        type="interface_conflict",
                        severity="error",
                        message=(
                            f"Interface bolt pattern mismatch: {local_pattern} vs {remote_pattern}"
                        ),
                        part_id=part_a,
                        suggested_next_steps=[
                            "Align bolt patterns on both interface specs.",
                            "Update mate constraints to use matching fasteners.",
                        ],
                    )
                )

    return problems