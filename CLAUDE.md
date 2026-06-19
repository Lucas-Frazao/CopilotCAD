# CopilotCAD

Spec-driven desktop CAD IDE: Electron/React/TypeScript frontend + Python JSON-RPC backend (stdio).

## Workflow

- Features are **F-0xx** in `docs/Docs_001/feature_roadmap_001.md`.
- Contracts live in `specs/specs_001/F-0xx_<name>.md` — **do not implement** until the user approves the spec.
- Do not edit `docs/Docs_001/feature_roadmap_001.md` or `docs/Docs_001/architecture_001.md` unless the user explicitly asks.

## Architecture boundaries

- OCCT imports only in `backend/kernel/occt_bridge.py`.
- Frontend never writes project files; backend owns the filesystem.
- Renderer: `nodeIntegration: false`, `contextIsolation: true`.
- No new JSON-RPC methods unless the active feature spec requires IPC changes.

## Commands

```powershell
# Backend tests
.cursor/skills/verify-backend/scripts/verify-backend.ps1

# Or manually
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

OCCT tests skip when `pythonocc-core` is unavailable (e.g. Windows ARM64).

## Automations

Full setup and usage: **`.cursor/README.md`**

| Tool | Skills / agents |
|------|-----------------|
| Cursor | `.cursor/skills/` — `/implement-f-feature`, `/verify-backend`, `/spec-reviewer`, `/dual-stack-reviewer` |
| Claude Code | `.claude/skills/` (mirror), `.claude/agents/` subagents, hooks in `.claude/settings.json` |

Set feature scope in `.cursor/feature-scope.json` when implementing a scoped F-0xx feature.
