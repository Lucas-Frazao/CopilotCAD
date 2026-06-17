# F-007 — Electron shell and IPC bridge

## Summary

Deliver a minimal but functional Electron IDE shell: main process owns the Python backend child and proxies JSON-RPC to the renderer via `contextBridge`; renderer shows a 3-column layout with placeholder panels; a basic chat panel sends user text to the backend and displays a text response. TypeScript types align with current backend methods (`ping`, `compile_intent`, `execute_intent`).

**Status:** Implemented.

## Context and goals

F-000 proved main-process spawn + `ping`. F-005 adds `compile_intent`; F-004/006 add `execute_intent` with `problems`. F-007 connects the renderer to that backend over secure IPC so chat can drive the IR compiler pipeline.

Goals:

- **Electron main** — single long-lived backend child; `ipcMain.handle` routes renderer requests to stdio JSON-RPC; clean shutdown on quit.
- **Preload** — `contextBridge` exposes `window.copilotcad` with `ping()` and `compileIntent(message)` (and optional generic `rpc(method, params)` for tests).
- **Renderer shell** — `app.tsx` 3-column layout: left explorer placeholder, center viewport placeholder, right chat (matches `docs/product_vision.md` left / center / right).
- **IPC types** — `frontend/renderer/ipc/types.ts` for JSON-RPC request/response shapes matching backend.
- **Minimal chat** — input, send button, scrollable message list (user + CopilotCAD labels); on send, call `compileIntent`, show `summary` as assistant text or structured error message.
- **Security** — `contextIsolation: true`, `nodeIntegration: false` (preserve F-000 contract).

**Done when (roadmap):** user can type in the chat panel and receive a text response from the backend.

## Non-goals

- **Full chat UX** — assumption tags, diff summaries, slash commands, blocking question UI (F-008).
- **Explorer tree, viewport 3D, problems/parts/history panels** — labeled placeholders only; no backend file reads (F-009–F-011).
- **Backend `chat.send` method** — F-007 uses existing `compile_intent` JSON-RPC; `chat.send` alias may be added in F-008 if needed.
- **Auto execute IR / geometry / project writes** — chat does not call `execute_intent` in F-007 (compile-only response).
- **Zustand store wiring** — optional stub; F-008 may own chat state patterns.
- **Production electron-builder packaging** — dev workflow (`npm run dev`) is sufficient.
- **Editing** `docs/feature_roadmap.md` or `docs/architecture.md`.

## Requirements

### Electron main (`frontend/electron/main.ts`)

- Spawn one `backend/main.py` process on `app.whenReady` (reuse F-000 venv resolution).
- Replace startup-only ping with reusable `sendJsonRpc(method, params, id?)` used by IPC handlers.
- Register `ipcMain.handle("copilotcad:rpc", async (_, method: string, params: unknown) => ...)`.
  - Serialize JSON-RPC 2.0 line to backend stdin; parse response line; throw on JSON-RPC `error`.
  - Support concurrent requests via request `id` matching (incrementing counter).
- On `window-all-closed` / quit: kill backend process.
- Keep `webPreferences`: `preload`, `contextIsolation: true`, `nodeIntegration: false`.

### Preload (`frontend/electron/preload.ts`)

Expose on `window.copilotcad`:

```typescript
ping(): Promise<string>
compileIntent(message: string, context?: Record<string, unknown>): Promise<CompileIntentResult>
```

Where `CompileIntentResult` is the backend `IntentIR` dict on success. Errors from main propagate as promise rejections with message + optional `data`.

Add `frontend/renderer/ipc/window.d.ts` for `Window` augmentation.

### Renderer IPC bridge (`frontend/renderer/ipc/bridge.ts`)

- Typed wrappers calling `window.copilotcad` methods.
- Throw clear error if API missing (not running in Electron).

### Types (`frontend/renderer/ipc/types.ts`)

Minimum types:

- `JsonRpcError` — `code`, `message`, `data?`
- `IntentIRPayload` — mirror key fields: `type`, `prompt`, `summary`, `target`, `steps` (loose `Record` / index signature acceptable for F-007)
- `CompileIntentResult` = `IntentIRPayload`

Document mapping to backend methods in comments.

### App shell (`frontend/renderer/app.tsx`)

- CSS grid or flex: **left** ~240px, **center** flex-grow, **right** ~360px; full viewport height.
- Mount placeholder panels: `ExplorerPanel`, `ViewportPanel`, `ChatPanel`.
- Minimal inline or simple CSS (Tailwind optional if already configured; avoid large design pass).

### Placeholder panels

- `ExplorerPanel`, `ViewportPanel` — visible label/header only (“Explorer”, “Viewport”); no data loading.
- Other panels (`ProblemsPanel`, etc.) — not mounted in F-007 layout (F-010+).

### Chat panel (`frontend/renderer/panels/ChatPanel.tsx`) — F-007 minimal scope

- Local state: `messages: { id, role: 'user' | 'assistant', text }[]`.
- Text input + Send button (and Enter to send).
- On send: append user message; call `compileIntent(text)`; append assistant message with `result.summary` on success.
- On failure (no API key, compile error): append assistant message with error text from rejection (no crash).
- Optional welcome line matching product vision (static string).

This is intentionally simpler than F-008 `ChatPanel` requirements.

### Backend

- **No changes required** if `compile_intent` and `ping` suffice.
- Do not add new JSON-RPC methods in F-007 unless implementation needs a thin `chat.send` wrapper (prefer `compile_intent`).

### Tests

- `tests/frontend/ipc-types.test.ts` or extend `placeholder.test.ts` — type-level or vitest smoke that `types.ts` exports expected shapes (no Electron required).
- Manual acceptance: `cd frontend && npm run dev` → type message → see assistant summary when `ANTHROPIC_API_KEY` set; see error message when not.

### Dev workflow

- Document in spec acceptance: `npm install` in `frontend/` if needed; `npm run dev` starts Vite + Electron.

## Data flow

```
ChatPanel → bridge.compileIntent(message)
    → preload invoke → ipcMain copilotcad:rpc
    → main sendJsonRpc("compile_intent", { message })
    → Python backend → IntentIR dict
    → summary shown as chat response
```

## Acceptance criteria

1. Main process spawns backend and handles `ipcMain` RPC proxy without per-request respawn.
2. Preload exposes `ping` and `compileIntent`; renderer cannot access `nodeIntegration` APIs.
3. `app.tsx` renders 3-column shell with explorer, viewport, and chat regions.
4. Explorer and viewport show placeholder headers; no filesystem or Three.js work.
5. User can send a chat message and see a CopilotCAD text response (`summary` from compiled IR) when API key is configured.
6. Compile failures show a readable error in chat (no white screen / uncaught exception).
7. `ping()` works from renderer (dev console or optional status indicator).
8. TypeScript types exist for compile result and errors in `renderer/ipc/types.ts`.
9. Backend pytest suite still passes unchanged.
10. `nodeIntegration: false` and `contextIsolation: true` remain in `main.ts`.

## Dependencies

- **F-000** — Electron scaffold, security defaults, backend spawn pattern.
- **F-005** — `compile_intent` JSON-RPC.
- **F-006** — not surfaced in UI in F-007.

## Overlap with F-008

| Concern | F-007 | F-008 |
|---------|-------|-------|
| Chat input + send | Yes | Yes (enhanced) |
| Message history styling | Basic | Full labels, assumptions, diffs |
| Slash commands | No | Yes |
| `execute_intent` / geometry | No | Partial / diff display |

F-007 `ChatPanel.tsx` may be refactored in F-008; keep implementation small.

## Open questions (defaults)

| Question | Default |
|----------|---------|
| Tailwind for layout | Simple CSS or minimal Tailwind classes if postcss already wired |
| `chat.send` backend method | Use `compile_intent` only |
| Execute after compile | No — F-012 golden path |
