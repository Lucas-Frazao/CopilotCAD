"""PDD complexity classifier — mirrors frontend/renderer/pdd/classifier.ts (F-013)."""

from __future__ import annotations

import re
from typing import Any

ASSEMBLY_KEYWORDS = [
    "assembly",
    "frame",
    "drone",
    "robot",
    "multi-part",
    "motor mount",
]
SIMPLE_DIMENSION_PATTERN = re.compile(r"\d+\s*(mm|cm|m|×|x)\s*\d+", re.IGNORECASE)


def classify_request_complexity(
    message: str,
    context: dict[str, Any] | None = None,
) -> dict[str, str]:
    del context  # reserved for future workspace-aware classification
    lower = message.lower()
    word_count = len(lower.split())

    has_assembly_cue = any(keyword in lower for keyword in ASSEMBLY_KEYWORDS)
    has_dimensions = bool(SIMPLE_DIMENSION_PATTERN.search(message))

    if has_assembly_cue or (word_count > 12 and not has_dimensions):
        return {
            "classification": "suggest_pdd",
            "reason": (
                "This request spans multiple parts or systems — "
                "Part-Driven Design can help structure it."
            ),
        }

    return {
        "classification": "simple",
        "reason": "Single-part request with enough structure to model directly.",
    }


def build_pdd_suggestion_payload(message: str) -> dict[str, Any]:
    return {
        "kind": "pdd_suggestion",
        "message": message,
        "classification": "suggest_pdd",
        "actions": [
            {"label": "Start with /vision", "command": "/vision"},
            {"label": "Continue without PDD", "command": "Continue without PDD"},
        ],
    }