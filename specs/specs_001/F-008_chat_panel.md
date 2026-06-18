# F-008 — Chat panel (full interaction UI)

## Summary

Upgrade minimal chat into the **full interaction surface**: structured messages, assumption tags, execution diff summaries, slash-command picker, blocking-question UI, and **compile → execute** on each send so users see plan + results + problems in one thread.

**Status:** Implemented.

## Why this matters

F-007 only **compiles** English to a plan summary. F-008 closes the loop users care about: describe a part → see what CopilotCAD understood → see which modeling steps ran → see warnings — before explorer and viewport (F-009–F-011) show files and 3D.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Compile** | English → Intent IR (`compile_intent`). |
| **Execute** | Run IR steps on geometry kernel (`execute_intent`). |
| **Diff summary** | Short report of which steps ran and whether execution succeeded. |
| **Assumption tag** | Inline chip showing something the AI inferred (e.g. “6 mm thickness — proposed”). |
| **Slash command picker** | Dropdown when typing `/` listing commands like `/part`, `/export`. |
| **Blocking question** | Required clarification from IR — UI to type answer and Accept (local state in F-008). |

## What the user will experience

1. Welcome: *“What to do first? Ask about this CAD model or we can start creating one.”*
2. Type a part prompt (not a bare slash command) → user message, then assistant message with:
   - Summary text  
   - Assumption tags (if any)  
   - Diff block (step ids, success/failure)  
   - Inline problem lines (warnings/errors)  
3. Type `/` → filterable list of 12 MVP slash commands; pick one to insert into input.
4. Send slash-only command (e.g. `/export`) → placeholder hint that handler comes in F-014.
5. Greetings like “Hello” → friendly local reply without calling the LLM (implementation enhancement).
6. Blocking questions show text field + Accept below assistant message (local UI only until F-023).

## What we will build

### IPC extensions

- Preload / bridge: `executeIntent(ir)` → `ExecuteIntentResult` with `problems[]`.
- Types: `IntentIRPayload`, `ProblemPayload`, `ExecuteIntentResult`, `ChatMessageData`.

### Components

| Component | Role |
|-----------|------|
| `ChatPanel.tsx` | Input, send, message list, slash picker orchestration |
| `ChatMessage.tsx` | User vs CopilotCAD labels; body by message kind |
| `AssumptionTag.tsx` | Assumption text, importance, status badge |
| `DiffSummary.tsx` | Execution one-liner from step ids |
| `SlashCommandPicker.tsx` | Filter `/vision`, `/part`, … `/history` |

### Send flow (normal message)

1. Append user message.  
2. `compileIntent(text)`  
3. `executeIntent(intent)`  
4. Append `compile_result` assistant message with intent + execution.  
5. On compile failure → `error` message with friendly text.  
6. On execute failure → still show summary/assumptions; diff shows failure; problems inline.

### Styling

- Extend `app.css`: tags, diff block, slash dropdown, blocking-question row (dark IDE theme).

### Tests

- `chat-utils.test.ts` — diff text, slash helpers, error formatting.
- `ipc/types.test.ts` — `ExecuteIntentResult` shape.
- Manual: mounting plate prompt → summary + diff + problems.

### Backend

No new methods required — uses existing `compile_intent` and `execute_intent`.

## Acceptance criteria

1. `executeIntent` exposed through preload, bridge, and types.
2. `ChatMessage` renders user and assistant with correct labels.
3. Successful flow shows summary, assumptions, diff after compile + execute.
4. Failed execution shows error in diff and inline problems when present.
5. Slash picker on `/` with filterable MVP commands.
6. Blocking questions with accept/edit UI (local state).
7. Welcome message on first load.
8. `npm test` in `frontend/` passes.
9. Backend pytest unchanged.
10. `nodeIntegration: false`, `contextIsolation: true` unchanged.

## Dependencies

- **F-007** — Shell, IPC, minimal chat.
- **F-005** — `compile_intent`.
- **F-004 / F-006** — `execute_intent` + `problems`.

## Out of scope (not in F-008)

- Slash command **execution** (F-014).
- Dedicated Problems panel (F-010) — inline only here.
- Explorer / viewport refresh (F-009, F-011).
- Backend assumption confirm/reject (F-023).
- High-risk approval (F-022).

## Notes for reviewers

F-008 is the **primary write UX** for MVP Phase 1. Panels around it (explorer, viewport, problems list) deepen visibility in F-009–F-010.
