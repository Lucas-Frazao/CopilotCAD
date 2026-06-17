"""Local model adapter stub (F-005)."""

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
