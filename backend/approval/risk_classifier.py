"""Intent risk classification for approval workflow (F-022)."""

from __future__ import annotations

from typing import Any

HIGH_RISK_OPS = frozenset({"delete_part", "delete_assembly", "wipe_workspace"})
HIGH_RISK_KEYWORDS = frozenset({"delete", "remove", "wipe", "destroy"})


def classify_intent_risk(intent: dict[str, Any]) -> str:
    summary = str(intent.get("summary", "")).lower()
    prompt = str(intent.get("prompt", "")).lower()

    for step in intent.get("steps", []):
        if not isinstance(step, dict):
            continue
        op = step.get("op")
        if op in HIGH_RISK_OPS:
            return "high"

    if any(keyword in summary or keyword in prompt for keyword in HIGH_RISK_KEYWORDS):
        return "high"

    return "low"