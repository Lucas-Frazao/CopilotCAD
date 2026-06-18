# F-004 — Step execution engine

## Summary

Build the **execution engine** that takes a validated Intent IR plan, runs each modeling step in order, calls the geometry kernel, and returns success or failure — plus JSON-RPC `execute_intent` so other layers can trigger runs.

**Status:** Implemented (OCCT geometry tests skip when `pythonocc-core` unavailable).

## Why this matters

F-001 defines the plan; F-003 defines the geometry primitives. F-004 **connects them**: “run step 1, pass result to step 2, …” — the heart of the compile → execute pipeline chat will use.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Executor** | Code that walks `steps[]` in dependency order and invokes handlers. |
| **Step handler** | Small function for one op type — reads params, calls kernel adapter. |
| **Handler registry** | Map from op name (`extrude`) to handler function. |
| **kernel_adapter** | Thin wrapper over `occt_bridge` — no direct OCCT imports in engine code. |
| **ExecutionResult** | Outcome object: `success`, `step_ids`, `final_step_id`, `error`. |
| **Stub handler** | Registered handler that raises “not implemented” for ops beyond MVP geometry. |

## What the user will experience

Still no full UI in F-004. Developers and tests can:

1. Pass mounting plate IR to `execute_intent` via JSON-RPC.
2. Get back success with step ids `s1`, `s2`, `s3`.
3. Export resulting solid to STEP via `export_step_file`.

Chat will call this automatically in F-008.

## What we will build

### `backend/engine/executor.py`

- `execute_intent_ir(intent: IntentIR) -> ExecutionResult`
- Dependency ordering, shape cache keyed by step id, clear errors on missing `from` refs.

### Step handlers (`backend/engine/step_handlers/`)

| Op | F-004 behavior |
|----|----------------|
| `sketch_rectangle`, `extrude`, `hole_pattern_corners` | Real geometry via adapter |
| All other `MVP_STEP_OPS` | Stub → `StepNotImplementedError` |

### `backend/engine/kernel_adapter.py`

Pass-through to `occt_bridge` only — no `OCC` imports here.

### `backend/project/export.py`

- `export_step_file(shape, path)` → delegates to `export_step`.

### JSON-RPC: `execute_intent`

- Validate IR → execute → return `{ success, step_ids, final_step_id, error? }` (no shapes over JSON).

### Tests (`tests/backend/test_executor_mounting_plate.py`)

Golden IR end-to-end, stub op failure, dependency errors, JSON-RPC dispatch.

## Acceptance criteria

1. Every `MVP_STEP_OPS` entry has a registered handler.
2. Stub op (e.g. `fillet`) fails with clear not-implemented semantics.
3. Bad `from` dependencies fail before geometry runs.
4. Mounting plate IR executes; `final_step_id == "s3"`.
5. STEP export after execution works on OCCT platforms.
6. JSON-RPC `execute_intent` succeeds for golden IR; validation errors for bad IR.
7. No OCCT imports outside `kernel/occt_bridge.py`.
8. No frontend changes; existing F-001–F-003 tests still pass.

## Dependencies

- **F-001** — `IntentIR`, validator, mounting plate fixture.
- **F-003** — `occt_bridge` operations and STEP export.

## Out of scope (not in F-004)

- LLM / compile (F-005).
- Problems engine (F-006).
- Frontend (F-007+).
- Writing `spec.yaml`, history, or `part.cad` on execute.
- Approval workflow (F-022).
- Viewport mesh IPC (F-011).

## Notes for reviewers

F-004 is **orchestration**. Three real ops + stubs for the rest is intentional — the catalog is complete for later features to fill in.
