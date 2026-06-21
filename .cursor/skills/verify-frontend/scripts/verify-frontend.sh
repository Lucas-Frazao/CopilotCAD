#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
FRONTEND="$REPO_ROOT/frontend"

if [[ ! -d "$FRONTEND/node_modules" ]]; then
  echo "frontend/node_modules not found. Run: cd frontend && npm install" >&2
  exit 1
fi

cd "$FRONTEND"
npm run typecheck
npm test
