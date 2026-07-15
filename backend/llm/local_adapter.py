"""
Local LLM Adapter — Future On-Device Model Stub (F-005)
=========================================================

WHAT THIS FILE DOES
-------------------
Placeholder for a future local/offline LLM. Implements the same interface as
``ClaudeAdapter`` but is not wired up in the MVP.

MVP STATUS
----------
Explicitly out of scope per F-005 non-goals — calling it raises
``NotImplementedError`` with a helpful message.
"""

from typing import Any

from llm.adapter import LLMAdapter


class LocalAdapter(LLMAdapter):
    """Stub for future local LLM support."""

    def generate_structured_json(
        self,
        user_message: str,
        project_context: dict[str, Any] | None = None,
    ) -> str:
        raise NotImplementedError(
            "LocalAdapter is not implemented in MVP; use ClaudeAdapter (F-005 non-goals)."
        )
