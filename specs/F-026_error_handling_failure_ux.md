# F-026 — Error handling and failure UX

## Summary

Ensure **every failure** in CopilotCAD produces a **clear, actionable message** in chat (what failed, why, what to try next) — while **preserving partial work** on disk when execution stops halfway.

**Status:** Pending approval.

## Why this matters

CAD pipelines fail often (bad params, missing kernel, LLM drift). Raw errors like `COPILOTCAD_RPC:...` destroy trust. F-026 systematizes **failure UX** across compile, execute, export, and slash commands.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Structured error** | JSON object with `error_type`, `message`, `details`, `suggested_next_steps` — not a stack trace in the UI. |
| **Partial work preserved** | If step 1–2 succeed and step 3 fails, earlier geometry and files remain — not rolled back silently. |
| **Actionable** | User gets 2–3 concrete next steps (“confirm assumption a2”, “add thickness to prompt”). |
| **Failure mode** | A known way things break — each should have a mapped UX response. |

## Failure modes to cover

| Area | Example failure | User should see |
|------|----------------|-----------------|
| Compile | LLM returns invalid JSON | “Couldn’t parse plan — try rephrasing with dimensions.” |
| Compile | IR validation failed | Field hints + example prompt. |
| Execute | Missing step param | Which op failed + param name. |
| Execute | OCCT / kernel error | Geometry failure + problems panel entry. |
| Export | No geometry | “Model this part first” + link to chat. |
| Slash | Bad args | “Usage: /part <name>”. |
| IPC | Backend down | “Backend not running — restart app.” |
| Config | No API key | “Set ANTHROPIC_API_KEY”. |

## What we will build

### Backend

- Audit all `Error` / `CompileError` / `ExecutionError` returns — consistent `error_type`, `suggested_next_steps`.
- Document error catalog in `backend/errors/catalog.py` (optional).

### Frontend

- Central `formatUserError(err)` used by ChatPanel, slash handlers, export.
- Parse `COPILOTCAD_RPC:` wrapper (extend F-008 bridge work).
- Chat error messages: title line + bullet suggestions + link to Problems panel when relevant.
- Never show raw JSON-RPC blobs to users.

### Tests

- Each failure mode has a test asserting user-facing message contains key guidance strings.

## Acceptance criteria

1. No user-facing raw `Error invoking remote method` strings in normal flows.
2. Execute partial success keeps completed steps’ geometry and history.
3. Problems panel shows errors from failed execute (F-010).
4. Error catalog documents ≥10 failure modes with expected messages.
5. Regression test for mounting plate compile failure → friendly message.

## Dependencies

- **F-008** — Chat error display.
- **F-010** — Problems panel for errors.
- **F-006** — Problems from execution failures.
- Prior IPC error normalization work on `spec-planning` branch.

## Out of scope (not in F-026)

- Automatic retry of LLM calls.
- Crash reporting to external services.
- Localized translations (English only MVP).

## Notes for reviewers

F-026 is **cross-cutting polish** — can land incrementally but should be “done” when the failure catalog is complete and golden path failures are humane.
