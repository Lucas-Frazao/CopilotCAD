"""
Intent Risk Classifier — Approval Gate (F-022)
==============================================

WHAT THIS FILE DOES
-------------------
Scores an Intent IR dict as "low" or "high" risk before execution. High-risk
intents require explicit user approval (see pending_store.py).

HIGH-RISK SIGNALS
-------------------
1. Step ops in HIGH_RISK_OPS (delete_part, delete_assembly, wipe_workspace)
2. Destructive keywords in summary or prompt (delete, remove, wipe, destroy)

RETURNS
-------
"high" — pause and queue for approval
"low"  — execute immediately
"""

from __future__ import annotations

from typing import Any

# Ops that always require approval when present in steps[]
HIGH_RISK_OPS = frozenset({"delete_part", "delete_assembly", "wipe_workspace"})
# Keywords scanned in human-readable summary and original prompt text
HIGH_RISK_KEYWORDS = frozenset({"delete", "remove", "wipe", "destroy"})


def classify_intent_risk(intent: dict[str, Any]) -> str:
    """Return 'high' or 'low' based on ops and keywords in the intent."""
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
