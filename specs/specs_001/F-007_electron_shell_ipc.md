# F-007 — Electron shell and IPC bridge

## Summary

Deliver the **desktop app shell**: Electron spawns Python, proxies JSON-RPC to the UI securely, shows a **three-column layout** (explorer / viewport / chat placeholders), and a **minimal chat** that compiles English to Intent IR and shows the summary.

**Status:** Implemented.

## Why this matters

F-000 proved ping; F-005 added `compile_intent`. F-007 is the first **user-visible CopilotCAD window** — type in chat, get a response from the backend — with the layout users will recognize as the IDE.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Electron main process** | Node.js side that spawns Python and handles `ipcMain` requests. |
| **Renderer** | React UI in the browser window. |
| **Preload** | Script exposing `window.copilotcad.ping()` and `compileIntent()` safely. |
| **copilotcad:rpc** | IPC channel: renderer asks main to forward JSON-RPC to Python. |
| **Three-column layout** | Left: explorer placeholder; center: viewport placeholder; right: chat. |
| **Compile-only chat** | F-007 shows IR `summary` text — does not run geometry (`execute_intent` is F-008). |

## What the user will experience

1. Run `npm run dev` → CopilotCAD window opens with three regions labeled Explorer, Viewport, Chat.
2. Type a message in chat → see “You” and “CopilotCAD” labels.
3. With `ANTHROPIC_API_KEY` set: assistant replies with compile **summary** (short description of the plan).
4. Without API key or on compile error: readable error in chat, no crash.
5. Explorer and viewport show placeholders only — no files or 3D yet.

## What we will build

### Electron main (`frontend/electron/main.ts`)

- Long-lived backend child; reusable `sendJsonRpc`.
- `ipcMain.handle("copilotcad:rpc", …)` with request id matching.
- Kill backend on quit.
- `contextIsolation: true`, `nodeIntegration: false`.

### Preload (`frontend/electron/preload.ts`)

```typescript
ping(): Promise<string>
compileIntent(message, context?): Promise<CompileIntentResult>
```

### Renderer

| Piece | Purpose |
|-------|---------|
| `app.tsx` | 3-column grid (~240px / flex / ~360px) |
| `ExplorerPanel`, `ViewportPanel` | Header placeholders only |
| `ChatPanel.tsx` | Input, send, message list, welcome line |
| `ipc/bridge.ts`, `ipc/types.ts`, `window.d.ts` | Typed IPC wrappers |

### Data flow

```
Chat → compileIntent → preload → main → Python compile_intent → summary in chat
```

### Tests

- Vitest smoke on IPC types; manual dev acceptance.

## Acceptance criteria

1. Backend spawned once per app session; RPC proxy works.
2. Preload exposes `ping` and `compileIntent`; renderer cannot use Node directly.
3. Three-column shell with explorer, viewport, chat visible.
4. Chat send shows `summary` when API key configured.
5. Compile failures show readable chat errors.
6. `ping()` works from renderer.
7. TypeScript types for compile result exist.
8. Backend pytest unchanged.
9. Security settings unchanged from F-000.

## Dependencies

- **F-000** — Electron scaffold and backend spawn.
- **F-005** — `compile_intent` JSON-RPC.

## Out of scope (not in F-007)

- Full chat UX (assumptions, diffs, slash picker — F-008).
- Explorer tree, 3D viewport, problems panel (F-009–F-011).
- `execute_intent` from chat (F-008).
- Production packaging.
- Backend `chat.send` alias (use `compile_intent`).

## Notes for reviewers

F-007 is **“chat talks to compiler.”** F-008 adds execute loop and rich message rendering on the same shell.
