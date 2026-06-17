#!/usr/bin/env python3
"""Pre-tool hook: warn or block edits outside active feature scope."""

import json
import sys
from pathlib import Path


def _extract_write_path(payload: dict) -> str | None:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("path", "file_path", "target_file"):
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                return value.replace("\\", "/")
    return None


def _load_scope(repo_root: Path) -> dict:
    scope_path = repo_root / ".cursor" / "feature-scope.json"
    if not scope_path.is_file():
        return {}
    try:
        return json.loads(scope_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _is_blocked(path: str, blocked_prefixes: list[str]) -> str | None:
    normalized = path.lstrip("/")
    for prefix in blocked_prefixes:
        prefix = prefix.replace("\\", "/").lstrip("/")
        if normalized == prefix or normalized.startswith(prefix):
            return prefix
    return None


def _is_outside_allowed(path: str, allowed_prefixes: list[str]) -> bool:
    if not allowed_prefixes:
        return False
    normalized = path.lstrip("/")
    return not any(
        normalized == prefix.replace("\\", "/").lstrip("/")
        or normalized.startswith(prefix.replace("\\", "/").lstrip("/") + "/")
        or normalized.startswith(prefix.replace("\\", "/").lstrip("/"))
        for prefix in allowed_prefixes
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"permission": "allow"}))
        return 0

    tool_name = str(payload.get("tool_name", ""))
    if tool_name not in {"Write", "StrReplace", "ApplyPatch", "EditNotebook"}:
        print(json.dumps({"permission": "allow"}))
        return 0

    path = _extract_write_path(payload)
    if not path:
        print(json.dumps({"permission": "allow"}))
        return 0

    repo_root = Path(__file__).resolve().parents[2]
    scope = _load_scope(repo_root)
    blocked = scope.get("blocked_prefixes") or []
    allowed = scope.get("allowed_prefixes") or []
    feature = scope.get("feature")

    blocked_match = _is_blocked(path, blocked)
    if blocked_match:
        response = {
            "permission": "deny",
            "user_message": f"Edit blocked: {path} matches protected prefix {blocked_match}.",
            "agent_message": (
                "Do not modify docs/feature_roadmap.md or docs/architecture.md "
                "unless the user explicitly asked to edit those docs."
            ),
        }
        print(json.dumps(response))
        return 0

    if feature and allowed and _is_outside_allowed(path, allowed):
        response = {
            "permission": "ask",
            "user_message": (
                f"Feature {feature} scope is active. Path {path} is outside "
                f"allowed prefixes: {', '.join(allowed)}. Allow this edit?"
            ),
            "agent_message": (
                f"Active feature scope {feature} allows only: {allowed}. "
                f"Confirm with the user before editing {path}."
            ),
        }
        print(json.dumps(response))
        return 0

    print(json.dumps({"permission": "allow"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
