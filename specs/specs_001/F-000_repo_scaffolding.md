# F-000 — Repo and project scaffolding

## Summary

Create the **foundation of the CopilotCAD codebase**: folder layout, a minimal desktop app window, a Python backend process, and proof that the two can talk to each other. No CAD features yet — only “hello world” over the wire.

**Status:** Implemented.

## Why this matters

Every later feature (chat, geometry, file trees) needs a **reliable split**: Electron UI on one side, Python engine on the other, connected locally. F-000 proves that split works before anyone builds modeling logic.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Electron** | Framework for desktop apps using web technology (HTML/React) plus a Node.js “main” process. |
| **Renderer** | The window users see — runs React, like a browser tab inside the app. |
| **Backend** | Python process that will eventually run CAD logic; started as a child of the Electron app. |
| **JSON-RPC** | A simple message format: send `{"method":"ping"}` as JSON, get `{"result":"pong"}` back. |
| **stdio** | Standard input/output pipes — how Electron sends lines to Python without network sockets. |
| **IPC** | Inter-process communication — here, Electron main ↔ Python via stdio, and later renderer ↔ main via Electron IPC. |
| **Preload / contextBridge** | Secure bridge so the UI can call main-process features without exposing full Node.js to the web page. |
| **contextIsolation** | Security mode: renderer cannot directly access Node; must use the preload bridge. |

## What the user will experience

After F-000 there is **no product UX yet**. A developer runs `npm run dev` and sees:

1. An empty Electron window (blank React shell).
2. In the terminal: a line like `IPC ping → pong: "pong"` confirming the backend answered.

That is the acceptance signal — not something an end user would demo.

## What we will build

### Repository layout

| Path | Purpose |
|------|---------|
| `docs/` | Product and engineering documentation |
| `frontend/` | Electron + React + TypeScript app |
| `backend/` | Python backend with module stubs |
| `example_project/` | Golden-path example stubs (mounting plate) |
| `tests/frontend/`, `tests/backend/` | Test directories |

### Frontend shell

- `electron/main.ts` — spawn backend, create window, security settings.
- `electron/preload.ts` — minimal `window.copilotcad` via `contextBridge`.
- `renderer/` — React entry, blank `app.tsx`, placeholder folders for panels.
- `npm run dev` — Vite dev server + Electron.

### Backend JSON-RPC server

- `backend/main.py` — read JSON-RPC lines from stdin, write responses to stdout.
- `ping` method returns the string `"pong"`.
- Uses `jsonrpcserver` library.

### IPC bridge (Electron main ↔ Python)

- On app start: spawn `python main.py` in `backend/` (prefer `.venv` Python if present).
- Send one `ping` request; log result to terminal.
- Kill backend when app quits.

### Security contract

| Setting | Value |
|---------|-------|
| `contextIsolation` | `true` |
| `nodeIntegration` | `false` |
| Preload script | Required |

## Acceptance criteria

1. All required directories and placeholder modules exist per tech stack doc.
2. `npm run dev` opens a blank Electron window.
3. Piping a `ping` JSON-RPC line to `backend/main.py` returns `"pong"`.
4. `npm run dev` logs successful IPC ping to the terminal.
5. No Intent IR, project files, chat UI, or geometry in F-000.
6. Renderer security settings remain as specified above.

## Dependencies

None — this is the first feature.

## Out of scope (not in F-000)

- Chat, explorer, viewport, or any IDE panels.
- Intent IR, LLM, geometry kernel, STEP export.
- JSON-RPC methods beyond `ping`.
- Renderer calling backend directly (only main process talks to Python in F-000).
- Installers, CI, or production packaging.

## Notes for reviewers

F-000 is **infrastructure only**. If ping works and the repo layout matches the architecture doc, the foundation is solid.
