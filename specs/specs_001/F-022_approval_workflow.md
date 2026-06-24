# F-022 — Approval workflow for high-risk actions

## Summary

Before CopilotCAD runs **dangerous or irreversible actions** (delete a part, release to production, mass file changes), show an **approval prompt in chat** with summary and diff preview — user must approve or reject before execution continues.

**Status:** Implemented.

## Why this matters

Chat-native authoring is fast; **guardrails** prevent accidental destruction. Users see exactly what will happen and can cancel — matching the product thesis of visible diffs and explicit control.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **High-risk action** | IR operations that delete data, overwrite released parts, or remove assemblies. |
| **`ir.pending`** | IPC/event payload sent to frontend *before* execution, holding the proposed IR until approved. |
| **Approval prompt** | Chat UI with Approve / Reject buttons and diff summary. |
| **Rejected action** | Logged to history but **not** executed on disk or geometry. |

## What the user will experience

1. User asks: “Delete the old mounting plate part.”
2. Chat shows: “This will remove parts/mounting_plate and related files” + diff preview.
3. **Approve** → backend executes; explorer updates.
4. **Reject** → nothing deleted; history notes rejection.
5. Low-risk actions (create plate, add hole) skip approval — no extra click.

## What we will build

### Backend

- **Risk classifier** — Tag IR types/ops as low vs high risk (delete, release, bulk scaffold).
- Pending state store (in-memory per session MVP): hold IR until `approve_intent(id)` or `reject_intent(id)`.
- JSON-RPC: `compile_intent` may return `pending: true` + `pending_id` instead of immediate execute.
- `approve_intent(pending_id)` → run execute; `reject_intent` → log only.

### Frontend

- Chat message kind `approval_required` with Approve/Reject buttons.
- Wire buttons to new IPC methods.
- Disable send while pending approval exists (optional).

## Acceptance criteria

1. Delete part request triggers approval UI — cannot execute without approve.
2. Approve runs execute and updates project; reject leaves files unchanged.
3. Rejected actions appear in history (F-017) with status rejected.
4. Low-risk mounting plate create does not require approval.
5. Unit tests for classifier and pending state lifecycle.

## Dependencies

- **F-008** — Chat message types and execute flow.
- **F-017** — History logging for rejections.
- **F-004** — Executor (actual delete implementation if not yet present).

## Out of scope (not in F-022)

- Multi-user approval chains (solo user MVP).
- Timeout auto-reject (optional future).
- Approval for every IR regardless of risk.

## Notes for reviewers

This feature is **safety UX**, not bureaucracy. Risk rules should be documented and easy to extend.
