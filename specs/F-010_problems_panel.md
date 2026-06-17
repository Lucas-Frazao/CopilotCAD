# F-010 — Problems panel

## Summary

Add a **Problems panel** that lists everything CopilotCAD thinks is wrong, risky, or incomplete after you use chat — missing answers, unconfirmed assumptions, geometry failures, traceability gaps, and more — in one place instead of only inline in chat.

**Status:** Pending approval.

## Why this matters

F-006 already detects problems on the backend and F-008 shows some inline in chat. A dedicated panel gives engineers a **checklist of open issues** they can scan while modeling, similar to the “Problems” tab in an IDE linter.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Problem** | A structured warning or error object: what went wrong, how serious it is, and what to do next. |
| **Severity** | How urgent: `warning` (should fix), `error` (something failed), `blocking` (cannot proceed safely). |
| **Problems engine** | Backend code (F-006) that inspects the Intent IR and execution results and produces Problem objects. |
| **Traceability** | Linking geometry back to specs and requirements so you know *why* a part exists. |

## MVP problem types (what users may see)

| Type | What it means (plain language) |
|------|--------------------------------|
| `missing_required_input` | CopilotCAD asked a blocking question and you haven’t answered it yet. |
| `unresolved_assumption` | The AI guessed something important and you haven’t confirmed or reject it. |
| `geometry_generation_failure` | A modeling step failed (bad parameters, missing kernel, etc.). |
| `interface_conflict` | Two parts’ connection definitions clash. |
| `invalid_mate` | An assembly mate (how parts fit together) is malformed. |
| `manufacturing_rule_warning` | Process/material info exists but dimensions are missing. |
| `traceability_gap` | A part has no link to its spec document in the project. |

## What the user will experience

1. After sending a chat message that runs compile + execute, the Problems panel updates.
2. Each row shows: problem type, short message, affected part (if any), and suggested next steps.
3. Problems group or sort by severity (blocking first).
4. Clicking a problem highlights related context — e.g. scroll chat to the message that produced it, or select a file in the explorer (F-009).

## What we will build

### Frontend

| Piece | Purpose |
|-------|---------|
| `ProblemsPanel.tsx` | Replaces placeholder; lists current problems |
| `ProblemItem.tsx` | One row/card per problem |
| State source | Problems from latest `executeIntent` result (app store or shared context with ChatPanel) |

### Data flow

1. ChatPanel completes `executeIntent` → receives `problems[]`.
2. Problems panel reads the same list (Zustand `appStore` or equivalent shared state).
3. On new execution, replace or merge the problem list.

### Interactions (MVP)

- Click problem → highlight chat message id if stored, or open explorer path if `part_id` maps to `parts/<id>/`.
- No “fix in panel” buttons yet — fixes still happen through chat (F-023 adds assumption confirm).

## Acceptance criteria

1. All seven MVP problem types can appear in the panel when triggered.
2. Panel updates automatically after each chat execution (no manual refresh).
3. Each item shows type, message, severity, and at least one suggested next step.
4. Click navigates to chat or explorer context when possible.
5. Empty state when no problems: friendly “No problems” message.

## Dependencies

- **F-006** — Problem schema and `evaluate_problems()`.
- **F-008** — `executeIntent` returns `problems` in the frontend.
- **F-009** — Optional but recommended for click-to-file navigation.

## Out of scope (not in F-010)

- Fixing problems from the panel (chat remains the write path).
- Problems from `compile_intent` alone without execute (optional future).
- Filtering UI beyond severity ordering.
- Email or external notifications.

## Notes for reviewers

Problems are **computed**, not typed in by the user. They are CopilotCAD’s engineering linter for the Intent IR pipeline.
