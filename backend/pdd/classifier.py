"""
PDD Complexity Classifier — When to Suggest Part-Driven Design (F-013)
======================================================================

WHAT THIS FILE DOES
-------------------
Analyzes a user chat message and decides whether it is a simple single-part
request or complex enough to suggest Part-Driven Design (PDD) workflow.

MIRROR OF FRONTEND
------------------
Logic matches ``frontend/renderer/pdd/classifier.ts`` so backend RPC and UI
agree on the same classification rules.

CLASSIFICATIONS
---------------
- "simple" — model directly with Intent IR
- "suggest_pdd" — offer /vision and structured design docs first
"""

from __future__ import annotations

import re  # Regex for "100 x 50 mm" style dimension patterns
from typing import Any

# Words that hint at multi-part or system-level design
ASSEMBLY_KEYWORDS = [
    "assembly",
    "frame",
    "drone",
    "robot",
    "multi-part",
    "motor mount",
]
# e.g. "100 x 50 mm" or "10×20"
SIMPLE_DIMENSION_PATTERN = re.compile(r"\d+\s*(mm|cm|m|×|x)\s*\d+", re.IGNORECASE)


def classify_request_complexity(
    message: str,
    context: dict[str, Any] | None = None,
) -> dict[str, str]:
    """
    Return {classification, reason} for a chat message.

    Heuristics:
    - Assembly keywords → suggest_pdd
    - Long message without dimensions → suggest_pdd
    - Otherwise → simple
    """
    del context  # Reserved for future workspace-aware rules (part count, etc.)
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
    """Build UI payload with action buttons for the PDD suggestion banner."""
    return {
        "kind": "pdd_suggestion",
        "message": message,
        "classification": "suggest_pdd",
        "actions": [
            {"label": "Start with /vision", "command": "/vision"},
            {"label": "Continue without PDD", "command": "Continue without PDD"},
        ],
    }
