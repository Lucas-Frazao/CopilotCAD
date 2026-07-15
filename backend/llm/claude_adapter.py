"""
Claude Adapter — Anthropic API for Intent IR (F-005)
====================================================

WHAT THIS FILE DOES
-------------------
Calls the Anthropic Claude API with a strict system prompt so the model returns
JSON matching the Intent IR schema — no markdown fences or commentary.

CONFIGURATION (environment variables)
-------------------------------------
- ANTHROPIC_API_KEY — required API key
- COPILOTCAD_CLAUDE_MODEL — optional override (default: claude-sonnet-4-6)

SECURITY NOTE
-------------
Project context is JSON-serialized, capped at MAX_CONTEXT_CHARS, and wrapped in
XML-like tags so it is clearly separated from the user's instruction.
"""

import json  # Serialize project_context dict for the prompt
import os  # Read API key and model from environment
from typing import Any

from anthropic import Anthropic, APIError  # Official Anthropic Python SDK

from llm.adapter import LLMAdapter
from llm.errors import LLMConfigurationError, LLMError
from llm.prompts import build_system_prompt

DEFAULT_MODEL = "claude-sonnet-4-6"
MODEL_ENV = "COPILOTCAD_CLAUDE_MODEL"
API_KEY_ENV = "ANTHROPIC_API_KEY"

# Limit injected context size — controls token cost and prompt-injection surface
MAX_CONTEXT_CHARS = 8000


class ClaudeAdapter(LLMAdapter):
    """Calls Anthropic Claude with a JSON-only Intent IR contract."""

    def __init__(
        self,
        client: Anthropic | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        resolved_key = api_key or os.environ.get(API_KEY_ENV)
        if not resolved_key:
            raise LLMConfigurationError(
                f"{API_KEY_ENV} is not set; required for ClaudeAdapter"
            )
        self._model = model or os.environ.get(MODEL_ENV, DEFAULT_MODEL)
        self._client = client or Anthropic(api_key=resolved_key)

    def generate_structured_json(
        self,
        user_message: str,
        project_context: dict[str, Any] | None = None,
    ) -> str:
        user_content = user_message

        if project_context:
            # default=str avoids TypeError on non-JSON-native values (e.g. datetime)
            context_json = json.dumps(project_context, default=str)
            if len(context_json) > MAX_CONTEXT_CHARS:
                context_json = context_json[:MAX_CONTEXT_CHARS] + "…[truncated]"
            user_content = (
                "<project_context>\n"
                f"{context_json}\n"
                "</project_context>\n\n"
                "<user_message>\n"
                f"{user_message}\n"
                "</user_message>"
            )

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=build_system_prompt(),
                messages=[{"role": "user", "content": user_content}],
            )
        except APIError as exc:
            raise LLMError(f"Anthropic API error: {exc}") from exc
        except Exception as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc

        # Response may contain multiple content blocks; collect all text parts
        text_parts: list[str] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)

        if not text_parts:
            raise LLMError("Anthropic response contained no text content")

        return "\n".join(text_parts).strip()
