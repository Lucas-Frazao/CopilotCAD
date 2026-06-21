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


# Capture the inner body of the first fenced block; the object inside is then
# located by a string-aware brace scan rather than a (greedy/non-greedy) regex,
# which mis-handles nested objects and braces inside string literals.
_FENCED_BLOCK = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _first_json_object(text: str) -> str | None:
    """Return the first balanced ``{...}`` object, respecting string literals."""
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return None


def _extract_json_text(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        raise IRParseError("empty LLM output", snippet=stripped)

    # Prefer the first fenced block (the model's intended answer), then fall back
    # to scanning the whole message for the first balanced object.
    fence_match = _FENCED_BLOCK.search(stripped)
    if fence_match:
        fenced = _first_json_object(fence_match.group(1))
        if fenced is not None:
            return fenced

    obj = _first_json_object(stripped)
    if obj is not None:
        return obj

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
