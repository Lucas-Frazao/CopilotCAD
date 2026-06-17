#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
BACKEND="$REPO_ROOT/backend"
PYTHON="$BACKEND/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "Backend venv not found at $PYTHON" >&2
  echo "Run: cd backend && uv venv && uv pip install pydantic pyyaml pytest" >&2
  exit 1
fi

cd "$BACKEND"
exec "$PYTHON" -m pytest -v
