# F-023 — Assumption management

## Summary

Let users **confirm, reject, or edit AI assumptions** from chat (inline tags) and persist changes to `assumptions.yaml` — so the Problems engine stops nagging about resolved items.

**Status:** Implemented.

## Why this matters

F-008 shows assumptions as read-only tags. F-006 warns on **unresolved** high-importance assumptions. Users need a clear way to say “yes, 6 mm holes are correct” without retyping in chat.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Assumption** | Something CopilotCAD inferred (thickness, material, hole depth) that isn’t explicitly confirmed. |
| **Proposed** | AI suggested, user hasn’t decided. |
| **Confirmed / Rejected** | User accepted or dismissed the assumption. |
| **`assumptions.yaml`** | Per-part file listing all assumptions and statuses (F-002). |

## What the user will experience

1. After compile, assumption tags appear in chat (F-008 `AssumptionTag`).
2. Each tag has actions: **Confirm**, **Reject**, **Edit** (change text).
3. Confirm → status `confirmed`; tag style updates; `unresolved_assumption` problem clears.
4. Changes saved to `parts/<id>/assumptions.yaml` and reflected in explorer preview.

## What we will build

### Backend

- **`update_assumption(part_id, assumption_id, status, text?)`** JSON-RPC.
- Validate status enum; write YAML; optionally append history entry.
- Re-run problems evaluation for that part after update.

### Frontend

- Extend `AssumptionTag.tsx` with action buttons (not local-only).
- Call IPC on confirm/reject/edit; refresh problems panel and tags.

## Acceptance criteria

1. Confirming assumption updates YAML on disk.
2. Problems panel removes `unresolved_assumption` for that id after confirm/reject.
3. Edit text updates YAML and chat display.
4. `/assumptions` (F-014) lists same data as files.
5. Unit tests for YAML round-trip and problem clearing.

## Dependencies

- **F-008** — AssumptionTag UI (currently local-only).
- **F-006** — `unresolved_assumption` problem.
- **F-002** — assumptions.yaml.
- **F-010** — Problems panel refresh.

## Out of scope (not in F-023)

- Assumption suggestions from LLM without user action.
- Cross-part assumption linking.
- Assumption versioning across history branches.

## Notes for reviewers

Assumption management is **human-in-the-loop** for AI inference — central to “compiler, not magic generator.”
