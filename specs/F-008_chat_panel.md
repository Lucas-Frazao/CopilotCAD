# F-008 — Chat panel (full interaction UI)

## Summary

Upgrade the F-007 minimal chat into a full chat interaction surface: structured `ChatMessage` rendering, inline assumption tags, diff summaries after IR execution, slash-command picker UI, and blocking-question prompts. Wire `compile_intent` → `execute_intent` so a single send shows summary, assumptions, step diff, and problems in chat. Slash commands are detected and listed in UI only (handlers deferred to F-014).

**Status:** Implemented.

## Context and goals

F-007 delivers compile-only chat with plain text summaries. F-008 makes the chat panel the primary interaction surface for the compile → execute loop, matching roadmap “prompt → IR → diff summary” visibility before explorer/viewport work (F-009–F-011).

Goals:

- Refactor chat to use `ChatMessage`, `AssumptionTag`, `DiffSummary`, `SlashCommandPicker` components.
- Extend IPC bridge with `executeIntent(ir)` returning execution result + `problems`.
- On send (non-slash): `compileIntent` → `executeIntent` → assistant message with summary, assumptions, diff, problems inline.
- Slash input: show picker for MVP commands; selecting a command inserts command text (no backend handler in F-008).
- Blocking questions from IR: render accept/edit controls (local UI state; no backend answer RPC yet).
- Optional Zustand `appStore` for chat message list (or keep local state in `ChatPanel` if simpler).

**Done when (roadmap):** a complete chat interaction (prompt → IR → diff summary) is visible in the UI.

## Non-goals

- **Slash command execution** — no project file writes from `/vision`, `/part`, etc. (F-014).
- **Problems panel** — problems shown inline in chat only (F-010).
- **Explorer / viewport updates** — no geometry mesh or file tree refresh (F-009, F-011).
- **Backend `chat.send`** — continue using `compile_intent` + `execute_intent`.
- **Assumption confirm/reject to backend** — accept/edit updates local display only (F-023).
- **High-risk approval workflow** — no `ir.pending` (F-022).
- **Editing** `docs/feature_roadmap.md` or `docs/architecture.md`.

## Requirements

### IPC extensions

**Preload / main** — add:

```typescript
executeIntent(ir: Record<string, unknown>): Promise<ExecuteIntentResult>
```

**Types** (`frontend/renderer/ipc/types.ts`):

- Extend `IntentIRPayload` with typed `assumptions`, `questions` arrays (minimal fields for UI).
- `ProblemPayload` — align with `schemas/problem.py` fields: `id`, `type`, `severity`, `message`, `suggested_next_steps`.
- `ExecuteIntentResult` — `{ success, step_ids, final_step_id?, error?, problems: ProblemPayload[] }`.

**Bridge** — `executeIntent(ir: IntentIRPayload): Promise<ExecuteIntentResult>`.

### Chat message model

```typescript
type ChatMessageKind = "text" | "compile_result" | "error" | "slash_hint";

interface ChatMessageData {
  id: string;
  role: "user" | "assistant";
  kind: ChatMessageKind;
  text?: string;
  intent?: IntentIRPayload;
  execution?: ExecuteIntentResult;
}
```

### Components

| Component | Responsibility |
|-----------|----------------|
| `ChatMessage.tsx` | Renders label (You / CopilotCAD), body by `kind` |
| `AssumptionTag.tsx` | Single assumption: text, importance, status badge |
| `DiffSummary.tsx` | Lists executed `step_ids`, `final_step_id`, success/error one-liner |
| `SlashCommandPicker.tsx` | Filterable list when input starts with `/`; MVP 12 commands from roadmap F-014 |
| `ChatPanel.tsx` | Orchestrates input, picker, send flow, message list |

### Send flow (non-slash)

1. Append user message.
2. `compileIntent(text)` → `IntentIRPayload`.
3. `executeIntent(result)` → `ExecuteIntentResult`.
4. Append assistant `compile_result` message with `intent` + `execution`.
5. `ChatMessage` renders: `summary` text, `AssumptionTag` list from `intent.assumptions`, `DiffSummary` from execution, inline problem lines from `execution.problems`.

On compile failure: assistant `error` message (preserve F-007 error formatting).

On execute failure: still show compiled IR summary/assumptions if compile succeeded; `DiffSummary` shows failure; problems from error payload.

### Slash command UI

- When input value starts with `/`, show `SlashCommandPicker` above input.
- Static command list: `/vision`, `/constitution`, `/architecture`, `/manufacturing`, `/part`, `/interface`, `/plan`, `/review`, `/release`, `/export`, `/assumptions`, `/history`.
- Filter by typed prefix; click or Enter selects → sets input to command + space (does not auto-send).
- Sending a slash-only message shows assistant text: “Slash command recognized (handler not implemented until F-014).”

### Blocking questions UI

- If `intent.questions` contains `blocking: true` and `status: "open"`, render below assistant message:
  - Question text
  - Text input (edit answer)
  - Accept button → sets local `status` display to answered (store in component state map by question id)
- No IPC call on accept in F-008.

### Styling

- Extend `app.css` for assumption tags, diff block, slash picker dropdown, question prompt row.
- Keep dark IDE-like theme consistent with F-007.

### Tests

- `frontend/renderer/components/DiffSummary.test.tsx` or `chat-utils.test.ts` — pure function building diff text from mock `ExecuteIntentResult`.
- `frontend/renderer/ipc/types.test.ts` — extend with `ExecuteIntentResult` shape smoke test.
- Manual: `npm run dev` → send mounting plate prompt → see summary, assumptions (if any), step list, problems (e.g. traceability_gap).

### Backend

- **No changes** — `compile_intent` and `execute_intent` already exist.

## Acceptance criteria

1. `executeIntent` exposed through preload, bridge, and types.
2. `ChatMessage` renders user and assistant messages with correct labels.
3. Assistant compile result shows `summary`, assumption tags, and diff summary after successful compile + execute.
4. Failed execution shows error in diff area and inline problems when present.
5. Slash picker appears when typing `/` and lists filterable MVP commands.
6. Blocking questions render with accept/edit UI (local state only).
7. F-007 welcome message still shown on first load.
8. `npm test` in `frontend/` passes (existing + new unit tests).
9. Backend pytest unchanged and passing.
10. `nodeIntegration: false`, `contextIsolation: true` unchanged in `main.ts`.

## Dependencies

- **F-007** — shell, IPC, minimal chat.
- **F-005** — `compile_intent`.
- **F-004 / F-006** — `execute_intent` + `problems` in response.

## Overlap note

F-008 replaces/extends F-007 `ChatPanel` implementation. F-010 may later bind `execution.problems` to Problems panel; F-008 shows them in chat.
