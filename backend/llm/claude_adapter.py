"""Claude API implementation of LLMAdapter (F-005)."""

import json
import os
from typing import Any

from anthropic import Anthropic, APIError

from llm.adapter import LLMAdapter
from llm.errors import LLMConfigurationError, LLMError
from llm.prompts import build_system_prompt

DEFAULT_MODEL = "claude-sonnet-4-20250514"
MODEL_ENV = "COPILOTCAD_CLAUDE_MODEL"
API_KEY_ENV = "ANTHROPIC_API_KEY"


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
            user_content = (
                f"Project context (JSON):\n{json.dumps(project_context)}\n\n"
                f"User message:\n{user_message}"
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

        text_parts: list[str] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)

        if not text_parts:
            raise LLMError("Anthropic response contained no text content")

        return "\n".join(text_parts).strip()
