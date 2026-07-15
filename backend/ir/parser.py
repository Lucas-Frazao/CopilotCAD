# =============================================================================
# LLM Output Parser (Feature F-005)
# =============================================================================
#
# WHAT THIS FILE DOES
# -------------------
# The LLM (Claude) answers in plain text, often wrapped in markdown fences:
#
#     ```json
#     { "type": "part_create", ... }
#     ```
#
# This module extracts the first JSON *object* from that text and parses it
# into a Python dict. It is deliberately careful about nested braces inside
# string values — naive regex would break on those.
# =============================================================================

# json — parse the extracted text into a Python dict
import json

# re — find markdown ```json ... ``` fenced blocks
import re

# Any — the parsed top-level value is a dict[str, Any]
from typing import Any


class IRParseError(Exception):
    """Raised when LLM output cannot be turned into a JSON object."""

    def __init__(self, message: str, snippet: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.snippet = snippet  # first ~200 chars shown in error details


# Regex: capture everything inside the first ``` or ```json fence (non-greedy body).
# We still locate the actual { ... } with _first_json_object below.
_FENCED_BLOCK = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _first_json_object(text: str) -> str | None:
    """
    Return the first balanced ``{...}`` substring, respecting JSON strings.

    Walks character-by-character:
    - Inside "quoted strings", braces don't affect depth
    - Backslash escapes the next character inside strings
    - When depth returns to 0, we found the closing brace
    """
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

    return None  # unbalanced — no complete object found


def _extract_json_text(text: str) -> str:
    """
    Pick the best candidate JSON substring from raw LLM text.

    Priority:
    1. First balanced object inside a markdown fence (model's intended answer)
    2. First balanced object anywhere in the message
    3. Whole stripped text (last resort before json.loads fails)
    """
    stripped = text.strip()
    if not stripped:
        raise IRParseError("empty LLM output", snippet=stripped)

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
    """
    Public API: LLM text → validated JSON object dict.

    Raises IRParseError if empty, invalid JSON, or top-level value isn't {}.
    """
    json_text = _extract_json_text(text)
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as exc:
        snippet = json_text[:200] + ("..." if len(json_text) > 200 else "")
        raise IRParseError(f"invalid JSON: {exc.msg}", snippet=snippet) from exc

    if not isinstance(parsed, dict):
        raise IRParseError("LLM output must be a JSON object", snippet=json_text[:200])

    return parsed
