"""Part history read/write (F-017)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from project.part_folder import HISTORY_FILENAME

HistoryType = Literal["execute", "export", "slash", "approval", "assumption"]


class HistoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    timestamp: str
    type: HistoryType
    summary: str
    step_ids: list[str] = Field(default_factory=list)
    assumption_ids_changed: list[str] = Field(default_factory=list)


def validate_history_entry(entry: dict[str, Any]) -> HistoryEntry:
    return HistoryEntry.model_validate(entry)


def _history_path(workspace: Path, part_id: str) -> Path:
    return workspace / "parts" / part_id / HISTORY_FILENAME


def _read_events(workspace: Path, part_id: str) -> list[dict[str, Any]]:
    path = _history_path(workspace, part_id)
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    events = data.get("events", [])
    return events if isinstance(events, list) else []


def _write_events(workspace: Path, part_id: str, events: list[dict[str, Any]]) -> None:
    path = _history_path(workspace, part_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"events": events}, indent=2) + "\n", encoding="utf-8")


def append_history_entry(workspace: Path, part_id: str, entry: dict[str, Any]) -> HistoryEntry:
    validated = validate_history_entry(entry)
    events = _read_events(workspace, part_id)
    events.append(validated.model_dump())
    _write_events(workspace, part_id, events)
    return validated


def get_part_history(workspace: Path, part_id: str) -> list[dict[str, Any]]:
    return _read_events(workspace, part_id)


def append_export_history(
    workspace: Path,
    part_id: str,
    export_path: Path,
    export_format: str,
) -> HistoryEntry:
    entry = {
        "id": f"export-{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "export",
        "summary": f"Exported {export_format.upper()} to {export_path.name}",
        "step_ids": [],
    }
    return append_history_entry(workspace, part_id, entry)