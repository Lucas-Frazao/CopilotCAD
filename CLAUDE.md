# CopilotCAD

Spec-driven desktop CAD IDE: Electron/React/TypeScript frontend + Python JSON-RPC backend over stdio.
English authoring → strict Intent IR → traceable parametric CAD.

> This file is the single source of truth for both Claude Code and Cursor.
> Cursor loads it via `.cursor/rules/_index.mdc`.

## Workflow (spec-driven — do this first)

- Features are **F-0xx** in `docs/Docs_001/feature_roadmap_001.md`.
- Each feature's contract lives in `specs/specs_001/F-0xx_<name>.md`.
- **Do not implement a feature until the user approves its spec.**
- **Do not edit** `docs/Docs_001/feature_roadmap_001.md` or `docs/Docs_001/architecture_001.md` unless the user explicitly asks.
- When implementing: set `.cursor/feature-scope.json`, code only within the spec, then run backend tests.

## Architecture

```
backend/    Python JSON-RPC server (entry: main.py)
  kernel/   OCCT bridge — the ONLY place OCCT may be imported
  ir/       Intent IR models + validation
  engine/   parametric build/evaluation
  llm/      Anthropic-backed authoring
  problems/ diagnostics
  project/  filesystem owner (load/save project files)
  schemas/  Pydantic schemas
frontend/   Electron + React + TS + Three.js + zustand (Vite)
specs/specs_001/   F-0xx contracts
docs/Docs_001/     roadmap, architecture, scope, tech_stack
```

### Boundaries (hard rules)

- OCCT imports **only** in `backend/kernel/occt_bridge.py`.
- Frontend never writes project files — the backend owns the filesystem.
- Renderer runs with `nodeIntegration: false`, `contextIsolation: true`.
- No new JSON-RPC methods unless the active feature spec requires IPC changes.

## Commands

### Backend (Python 3.11–3.12)

```bash
cd backend
# First-time setup
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"     # Windows: .venv\Scripts\python.exe -m pip install -e ".[dev]"

# Tests (run from backend/; tests live in tests/backend/)
.venv/bin/python -m pytest -v                    # Windows: .venv\Scripts\python.exe -m pytest -v
```

OCCT (`pythonocc-core`) is unavailable on some platforms (e.g. Windows ARM64); geometry tests skip there. Use x64 Python for geometry work.

### Frontend

```bash
cd frontend
npm install
npm run dev      # build Electron main + Vite + launch Electron
npm test         # vitest
npm run build    # production bundle
```

## Conventions

- Python: ruff (`line-length = 100`); a hook auto-runs `ruff check --fix` on `backend/` edits.
- No silent failures — raise loudly; no broad `except`/`.get(default)`/`or 0` on critical data.
- Essential tests only (happy path + branched failures), readable code, no premature abstraction.

## Automations

Both tool stacks share the same scripts and skills. Full setup/usage: **`.cursor/README.md`**.

| Tool | Config | Skills / agents |
|------|--------|-----------------|
| Cursor | `.cursor/` (`hooks.json`, `mcp.json`, `rules/`) | `.cursor/skills/` — `/implement-f-feature`, `/verify-backend`, `/spec-reviewer`, `/dual-stack-reviewer` |
| Claude Code | `.claude/settings.json`, `.mcp.json` | `.claude/skills/` (mirror), `.claude/agents/` subagents |
