# F-006 — Problems engine

## Summary

After each plan runs, automatically detect **engineering issues** — unanswered questions, unconfirmed assumptions, geometry failures, traceability gaps — and return structured **Problem** objects with the execution result.

**Status:** Implemented.

## Why this matters

CAD tools need a **linter for intent**. Problems are not user notes; they are computed signals that say “something needs attention before you trust this part.” F-010 will show them in a panel; F-008 shows some inline in chat.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Problem** | Structured object: type, severity, message, suggested next steps. |
| **Severity** | `warning`, `error`, or `blocking` — how urgent. |
| **Problems engine** | `evaluate_problems(intent, execution_result)` — pure function, no disk reads in MVP. |
| **Traceability gap** | Part exists but isn’t linked to spec documents in `links.spec_refs`. |
| **Unresolved assumption** | AI guessed something important; user hasn’t confirmed it. |

## MVP problem types

| Type | Plain meaning |
|------|----------------|
| `missing_required_input` | Blocking question still open. |
| `unresolved_assumption` | High-importance assumption still “proposed.” |
| `geometry_generation_failure` | Execution failed (kernel/handler error). |
| `interface_conflict` | Duplicate or clashing interface ids in assembly IR. |
| `invalid_mate` | Mate step missing required params. |
| `manufacturing_rule_warning` | Process set but dimensions missing. |
| `traceability_gap` | Part create/edit without `links.spec_refs`. |

## What the user will experience

In F-006, problems appear only in **API responses** (JSON-RPC `execute_intent` includes `problems: []`). After F-008/F-010, users see them in chat and the Problems panel after each modeling action.

## What we will build

### Schema (`backend/schemas/problem.py`)

- `Problem`, `ProblemType`, `ProblemSeverity` (strict Pydantic).
- Fields: `id`, `type`, `severity`, `message`, optional `part_id`, `step_id`, `suggested_next_steps`.

### Engine (`backend/problems/engine.py`)

- `evaluate_problems(intent, execution_result=None) -> list[Problem]`
- `problems_to_dicts()` for JSON-RPC serialization.

### Wiring (`backend/main.py`)

Update `execute_intent`:

1. Validate → execute → evaluate problems.
2. Include `problems` on success and on execution failure payloads.

### Tests (`tests/backend/test_problems_engine.py`)

One test per problem type; clean IR returns empty; JSON-RPC includes problems on failure.

## Acceptance criteria

1. All seven problem types implemented per trigger table.
2. Clean mounting plate + successful execution yields no problems (or only expected warnings with fixture tuned).
3. Each type has a dedicated pytest.
4. `execute_intent` JSON-RPC always includes `problems` array.
5. No frontend changes.
6. F-001–F-005 tests still pass.

## Dependencies

- **F-001** — IR fields (questions, assumptions, links, constraints).
- **F-004** — `ExecutionResult`, `execute_intent_ir`.

## Out of scope (not in F-006)

- Problems panel UI (F-010).
- Real-time IPC events (`problems.update`).
- Loading `spec.yaml` from disk for traceability (IR-only heuristics).
- Full assembly/mate validation (stubs until F-018–F-021).
- Problems on `compile_intent` only (execute path focus).
- Approval workflow (F-022).

## Notes for reviewers

Problems are **actionable hints**, not errors that always block work — severity communicates urgency.
