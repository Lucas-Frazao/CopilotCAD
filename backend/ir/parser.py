"""LLM output → parsed JSON dict (F-005)."""

import json
import re
from typing import Any


class IRParseError(Exception):
    """Raised when LLM output cannot be parsed as JSON."""

    def __init__(self, message: str, snippet: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.snippet = snippet


_FENCED_JSON = re.compile(r"```(?:json)?\s*([\{].*?[\}])\s*```", re.DOTALL | re.IGNORECASE)


def _extract_json_text(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        raise IRParseError("empty LLM output", snippet=stripped)

    fence_match = _FENCED_JSON.search(stripped)
    if fence_match:
        return fence_match.group(1).strip()

    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        inner = "\n".join(lines).strip()
        if inner:
            return inner

    return stripped


def parse_llm_json(text: str) -> dict[str, Any]:
    """Parse LLM text into a JSON object dict."""
    json_text = _extract_json_text(text)
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as exc:
        snippet = json_text[:200] + ("..." if len(json_text) > 200 else "")
        raise IRParseError(f"invalid JSON: {exc.msg}", snippet=snippet) from exc

    if not isinstance(parsed, dict):
        raise IRParseError("LLM output must be a JSON object", snippet=json_text[:200])

    return parsed
