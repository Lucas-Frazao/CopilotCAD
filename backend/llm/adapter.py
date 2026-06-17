"""Abstract LLM adapter interface (F-005)."""

from abc import ABC, abstractmethod
from typing import Any


class LLMAdapter(ABC):
    """Generates raw text containing a JSON object for Intent IR compilation."""

    @abstractmethod
    def generate_structured_json(
        self,
        user_message: str,
        project_context: dict[str, Any] | None = None,
    ) -> str:
        """Return raw text expected to contain a JSON Intent IR object."""
