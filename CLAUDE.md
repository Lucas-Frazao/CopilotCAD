# CopilotCAD

Spec-driven desktop CAD IDE: Electron/React/TypeScript frontend + Python JSON-RPC
backend (stdio).

## Canonical instructions

**Read [`AGENTS.md`](./AGENTS.md) before working in this repo — it is the single source
of truth** for workflow rules, architecture boundaries, commands, and automations.
This file is intentionally thin so the Cursor and Claude Code rule sets cannot drift;
add or change rules in `AGENTS.md`, not here.

The non-negotiable invariants (full detail in `AGENTS.md`):

- OCCT imports only in `backend/kernel/occt_bridge.py`.
- Frontend never writes project files; the backend owns the filesystem.
- Renderer stays sandboxed: `nodeIntegration: false`, `contextIsolation: true`.
- No new JSON-RPC methods unless the active feature spec requires them.
- Do not implement an F-0xx feature before its spec is approved; do not edit
  `docs/Docs_001/feature_roadmap_001.md` or `docs/Docs_001/architecture_001.md` unless
  explicitly asked.
