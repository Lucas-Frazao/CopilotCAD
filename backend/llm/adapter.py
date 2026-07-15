"""
LLM Adapter Interface — Abstract Base Class (F-005)
===================================================

WHAT THIS FILE DOES
-------------------
Defines the contract every LLM backend must implement. The chat pipeline asks
an adapter to turn natural language into raw text containing a JSON Intent IR.

WHY AN ABC (Abstract Base Class)?
---------------------------------
Swapping providers (Claude today, local model later) only requires a new class
that implements ``generate_structured_json`` — no changes to the RPC layer.
"""

from abc import ABC, abstractmethod  # ABC = cannot instantiate; @abstractmethod = must override
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
