# CopilotCAD — Agent Instructions (canonical)

This file is the **single source of truth** for how agents work in this repo. Cursor
reads `AGENTS.md` and `.cursor/rules/*.mdc` automatically; Claude Code reads
`CLAUDE.md`. Both `CLAUDE.md` and `.cursor/rules/spec-driven-development.mdc` are thin
pointers to this file — edit rules **here** so the two tools never drift.

CopilotCAD is a spec-driven desktop CAD IDE: Electron/React/TypeScript frontend +
Python JSON-RPC backend (stdio).

## Workflow

- Features are **F-0xx** in `docs/Docs_001/feature_roadmap_001.md`. Build order is the
  one listed there; do not skip phases.
- Each feature has a contract in `specs/specs_001/F-0xx_<name>.md`.
- **Do not implement** a feature until the user approves its spec.
- **Do not edit** `docs/Docs_001/feature_roadmap_001.md` or
  `docs/Docs_001/architecture_001.md` unless the user explicitly asks. (A hook enforces
  this.)
- When implementing F-0xx: read the spec, set `.cursor/feature-scope.json`, implement
  only what the spec allows, then run the matching verify skill (backend and/or
  frontend), and update the spec Status.

## Architecture boundaries (always enforced)

- **OCCT imports only in `backend/kernel/occt_bridge.py`.** Step handlers and project
  code go through `engine/kernel_adapter.py` / the bridge, never `OCC.*` directly.
- **The frontend never writes project files.** The backend owns the filesystem; all
  writes originate from chat → IR pipeline.
- **Renderer stays sandboxed:** `nodeIntegration: false`, `contextIsolation: true`, and
  a minimal `contextBridge` surface. No raw `ipcRenderer` in the renderer.
- **No new JSON-RPC methods** unless the active feature spec requires IPC changes.

## Commands

Backend tests (cross-platform — pick the script for your shell):

```powershell
# Windows / PowerShell
.cursor/skills/verify-backend/scripts/verify-backend.ps1
```

```bash
# macOS / Linux
.cursor/skills/verify-backend/scripts/verify-backend.sh
```

Frontend tests + typecheck:

```powershell
# Windows / PowerShell
.cursor/skills/verify-frontend/scripts/verify-frontend.ps1
```

```bash
# macOS / Linux
.cursor/skills/verify-frontend/scripts/verify-frontend.sh
```

Or directly, from `frontend/`: `npm test` and `npm run typecheck`. From `backend/`:
`python -m pytest -v` using the project venv. OCCT tests skip when `pythonocc-core` is
unavailable (e.g. Windows ARM64).

## Automations

Full setup and usage: **`.cursor/README.md`**.

| Tool | Skills / agents |
|------|-----------------|
| Cursor | `.cursor/skills/` — `implement-f-feature`, `verify-backend`, `verify-frontend`, `spec-reviewer`, `dual-stack-reviewer`, `feature-pipeline-loop` |
| Claude Code | `.claude/skills/` (mirror), `.claude/agents/` subagents, hooks in `.claude/settings.json` |

Set feature scope in `.cursor/feature-scope.json` when implementing a scoped F-0xx
feature.
