"""
Pending Intent Store — High-Risk Approval Queue (F-022)
=======================================================

WHAT THIS FILE DOES
-------------------
When the risk classifier marks an intent as "high", execution is paused and the
intent is stored here until the user approves or rejects it.

IN-MEMORY STORE
---------------
``PendingIntentStore`` keeps records in a dict keyed by pending_id (UUID hex).
This is process-local — restarting the backend clears pending items.

WORKFLOW
--------
  add(intent) → pending_id
  get(pending_id) → intent dict
  mark_executed / mark_rejected → update status
  reject_pending → mark rejected + optional history log
"""

from __future__ import annotations

import uuid  # Generate unique pending_id values
from dataclasses import dataclass, field  # Lightweight record types
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class PendingRecord:
    """One queued high-risk intent awaiting user decision."""
    intent: dict[str, Any]
    created_at: str
    status: str = "pending"  # pending | executed | rejected
    rejected_at: str | None = None


class PendingIntentStore:
    """In-memory map of pending_id → PendingRecord."""

    def __init__(self) -> None:
        self._records: dict[str, PendingRecord] = {}

    def add(self, intent: dict[str, Any]) -> str:
        """Store intent and return its pending_id."""
        pending_id = uuid.uuid4().hex
        self._records[pending_id] = PendingRecord(
            intent=intent,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return pending_id

    def get(self, pending_id: str) -> dict[str, Any] | None:
        record = self._records.get(pending_id)
        return record.intent if record else None

    def is_executed(self, pending_id: str) -> bool:
        record = self._records.get(pending_id)
        return record is not None and record.status == "executed"

    def mark_executed(self, pending_id: str) -> None:
        record = self._records.get(pending_id)
        if record:
            record.status = "executed"

    def mark_rejected(self, pending_id: str) -> None:
        record = self._records.get(pending_id)
        if record:
            record.status = "rejected"
            record.rejected_at = datetime.now(timezone.utc).isoformat()


def log_rejection_to_history(
    workspace: Path,
    part_id: str,
    pending_id: str,
    summary: str,
) -> None:
    """Write an 'approval' rejection event to parts/<id>/history.json."""
    from project.history import append_history_entry

    append_history_entry(
        workspace,
        part_id,
        {
            "id": f"reject-{pending_id[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "approval",
            "summary": summary,
            "step_ids": [],
        },
    )


def reject_pending(
    store: PendingIntentStore,
    pending_id: str,
    *,
    workspace_path: Path | None = None,
) -> None:
    """Reject a pending intent and optionally log to part history."""
    intent = store.get(pending_id)
    if intent is None:
        raise KeyError(f"pending intent not found: {pending_id}")

    store.mark_rejected(pending_id)

    if workspace_path is not None:
        target = intent.get("target", {})
        part_id = target.get("part_id") if isinstance(target, dict) else None
        if part_id:
            log_rejection_to_history(
                workspace_path,
                part_id,
                pending_id,
                f"Rejected high-risk action: {intent.get('summary', 'delete')}",
            )
