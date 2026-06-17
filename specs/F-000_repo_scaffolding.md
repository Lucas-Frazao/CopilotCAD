# F-000 — Repo and project scaffolding

## Summary

Establish the CopilotCAD monorepo layout, a minimal Electron + React + TypeScript desktop shell, a Python backend JSON-RPC server over stdio, and a working IPC bridge that proves the frontend can spawn the backend and exchange messages. This feature delivers no user-facing CAD functionality; it is the foundation all later features build on.

**Status:** Implemented.

## Context and goals

CopilotCAD is split into an Electron frontend and a Python backend communicating via JSON-RPC over stdio (`docs/architecture.md`). Before Intent IR, geometry, or project files can be built, the repository must exist with the correct module boundaries, a runnable desktop app, and verified process-level IPC.

Goals for F-000:

- Mirror the repo structure defined in `docs/tech_stack.md` so `frontend/`, `backend/`, `example_project/`, `tests/`, and `docs/` coexist at the repository root.
- Provide placeholder modules and files for future backend and frontend work without implementing business logic.
- Run a blank Electron window with React mounted and no panel UI.
- Start the Python backend as a child process from the Electron main process and confirm JSON-RPC `ping` → `pong` in the terminal on app startup.
- Keep renderer security defaults: `contextIsolation` enabled, `nodeIntegration` disabled, preload script via `contextBridge`.

## Non-goals

- Chat panel, viewport, explorer, or any IDE panels beyond a blank shell.
- Intent IR models, validation, or LLM integration.
- Project file creation, geometry kernel, or STEP export.
- JSON-RPC methods beyond `ping` (e.g. `chat.send`, `project.open`).
- Renderer-to-backend IPC for application messages (only main-process ↔ backend stdio in F-000).
- Production packaging, installers, or CI pipelines.
- Enforcing edition/capabilities or workspace manifests (F-002).

## Requirements

### Repository layout

The repository root must contain:

| Path | Purpose |
|------|---------|
| `docs/` | Product and engineering documentation |
| `frontend/` | Electron + React + TypeScript app |
| `backend/` | Python backend with module stubs per `docs/architecture.md` |
| `example_project/` | Golden-path example project stubs (mounting plate) |
| `tests/frontend/` | Frontend test placeholder directory |
| `tests/backend/` | Backend test placeholder directory |
| `pdd_methodology_full_guide.md` | PDD reference (pre-existing) |

`frontend/` must include:

- `electron/main.ts` — main process (window lifecycle, backend spawn, IPC ping).
- `electron/preload.ts` — preload script exposing a minimal `contextBridge` API.
- `renderer/` — React entry (`main.tsx`, `app.tsx`) and placeholder directories: `panels/`, `components/`, `store/`, `ipc/`.
- `package.json`, `tsconfig.json`, `tsconfig.electron.json`, `vite.config.ts`, `index.html`.

`backend/` must include placeholder modules:

- `main.py` — stdio JSON-RPC entry point.
- `ir/`, `engine/`, `kernel/`, `project/`, `problems/`, `llm/`, `schemas/` with stub files named per `docs/architecture.md`.

### Frontend shell

- Electron main process creates a `BrowserWindow` (default size acceptable, e.g. 1200×800).
- Renderer loads the Vite dev server URL in development (`VITE_DEV_SERVER_URL`) or built `dist/index.html` in production.
- `renderer/app.tsx` renders a blank shell (no panels, no chrome beyond the empty window).
- Preload exposes `window.copilotcad` via `contextBridge` (may be an empty object in F-000).

### Backend JSON-RPC server

- `backend/main.py` reads newline-delimited JSON-RPC 2.0 requests from stdin and writes newline-delimited responses to stdout.
- Uses `jsonrpcserver` with `dispatch()` (not the HTTP `serve()` helper).
- Registers a `ping` method that returns the string `"pong"`.
- Process stays alive and handles multiple requests on stdin (line loop).

### IPC bridge (Electron main ↔ Python backend)

- On `app.whenReady`, before or when creating the window, the main process:
  1. Spawns `backend/main.py` using the backend virtualenv Python when `backend/.venv` exists, otherwise system `python` / `python3`.
  2. Sets working directory to `backend/`.
  3. Uses stdio pipes (`stdin`, `stdout`, `stderr`).
- Main process sends one JSON-RPC request after spawn:

```json
{"jsonrpc":"2.0","id":1,"method":"ping","params":{}}
```

- Main process reads stdout until a response with matching `id` is received.
- On success, main process logs a line to the terminal containing `IPC ping → pong` and the result value `"pong"`.
- On failure, main process logs an error but may still open the window (startup diagnostic, not a hard gate for F-000 unless acceptance criteria require success).
- On app quit, the backend child process is terminated.

### Development workflow

- `frontend/package.json` must provide a `dev` script that compiles Electron TypeScript, starts Vite, waits for the dev server, and launches Electron.
- Documented run path: install frontend deps, install backend `jsonrpcserver` in venv, run `npm run dev` from `frontend/`.

## Data model and contracts

### JSON-RPC over stdio

- **Transport:** One JSON object per line on stdin/stdout; messages are UTF-8 text terminated by `\n`.
- **Request shape:** `{"jsonrpc":"2.0","id":<number|string>,"method":<string>,"params":<object>}`.
- **Response shape (success):** `{"jsonrpc":"2.0","id":<same id>,"result":<value>}`.
- **Response shape (error):** `{"jsonrpc":"2.0","id":<same id>,"error":{...}}`.

### `ping` method contract

| Direction | Field | Value |
|-----------|-------|-------|
| Request | `method` | `"ping"` |
| Request | `params` | `{}` (empty object) |
| Response | `result` | `"pong"` (string) |

### Process spawn contract

| Setting | Value |
|---------|-------|
| Executable | `backend/.venv/Scripts/python.exe` (Windows) or `backend/.venv/bin/python` (Unix) if present; else `python` / `python3` |
| Arguments | `["main.py"]` |
| Working directory | `backend/` |
| stdio | `["pipe", "pipe", "pipe"]` |

### Frontend security contract

| `webPreferences` | Required value |
|------------------|----------------|
| `contextIsolation` | `true` |
| `nodeIntegration` | `false` |
| `preload` | Path to compiled `preload.js` |

## Acceptance criteria

1. **Repo structure:** All directories and placeholder files listed in Requirements exist at the paths defined in `docs/tech_stack.md`.
2. **Blank window:** Running `npm run dev` from `frontend/` opens an Electron window with no panel UI (empty React shell).
3. **Backend standalone:** Piping `{"jsonrpc":"2.0","id":1,"method":"ping","params":{}}` plus newline to `backend/main.py` prints a single line response with `"result":"pong"` and matching `"id":1`.
4. **IPC on startup:** Running `npm run dev` prints a terminal line matching `IPC ping → pong: "pong"` (or equivalent JSON-stringified pong) before or while the window is shown.
5. **No F-001/F-002 behavior:** No Intent IR validation, no `copilotcad.json` creation API, and no chat/geometry IPC methods are required in F-000.
6. **Security:** Renderer has `nodeIntegration: false` and `contextIsolation: true` with preload script loaded.
