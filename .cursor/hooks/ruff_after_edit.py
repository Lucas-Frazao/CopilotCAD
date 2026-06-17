#!/usr/bin/env python3
"""Post-edit hook: run Ruff on backend Python files."""

import json
import subprocess
import sys
from pathlib import Path


def _extract_path(payload: dict) -> str | None:
    for key in ("file_path", "path", "file"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value.replace("\\", "/")

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("path", "file_path", "target_file"):
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                return value.replace("\\", "/")

    return None


def _ruff_executable(repo_root: Path) -> list[str]:
    windows = repo_root / "backend" / ".venv" / "Scripts" / "ruff.exe"
    unix = repo_root / "backend" / ".venv" / "bin" / "ruff"
    if windows.exists():
        return [str(windows)]
    if unix.exists():
        return [str(unix)]
    return ["ruff"]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    file_path = _extract_path(payload)
    if not file_path:
        return 0

    if not file_path.endswith(".py") or "/backend/" not in f"/{file_path.lstrip('/')}":
        return 0

    repo_root = Path(__file__).resolve().parents[2]
    target = (repo_root / file_path).resolve()
    if not target.is_file():
        return 0

    cmd = _ruff_executable(repo_root) + ["check", "--fix", str(target)]
    subprocess.run(cmd, cwd=repo_root / "backend", check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
