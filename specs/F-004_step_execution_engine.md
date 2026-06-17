# F-004 — Step execution engine

## Summary

Implement the Intent IR execution pipeline in Python: sequence validated `steps[]`, dispatch each step to a handler, call the geometry kernel through a thin `kernel_adapter`, and produce a final solid for the mounting plate golden IR. Register stub handlers for every MVP `op` in `MVP_STEP_OPS` so F-004 establishes the full handler catalog; only `sketch_rectangle`, `extrude`, and `hole_pattern_corners` perform real geometry (via F-003 `occt_bridge`). Expose execution through a Python API and a single JSON-RPC method for stdio integration tests.

**Status:** Implemented (OCCT geometry tests skip when `pythonocc-core` unavailable, e.g. Windows ARM64).

## Context and goals

F-001 validates Intent IR; F-003 implements OCCT operations in isolation. F-004 connects them: `validate_intent_ir` → `executor` → `step_handlers` → `kernel_adapter` → `occt_bridge`.

Goals:

- Run the mounting plate golden IR (`tests/backend/test_intent_ir_validation.py` `mounting_plate_ir()`) end-to-end in Python and export a valid STEP file.
- Topological execution order respecting `steps[].from` dependencies.
- Per-step geometry cache keyed by step `id` (output shape passed to dependent steps).
- Handler registry covering all `MVP_STEP_OPS`; unimplemented ops raise a clear `StepNotImplementedError`.
- Thin `kernel_adapter.py` — no new OCCT imports outside `occt_bridge.py`.
- Wire execution into `backend/main.py` via JSON-RPC `execute_intent` (validate + execute).
- Minimal `project/export.py` wrapper calling `occt_bridge.export_step`.

## Non-goals

- **LLM / IR generation** — no `llm/`, no `ir/parser.py` changes (F-005).
- **Problems engine** — no post-execution validation (F-006).
- **Frontend / Electron** — no `frontend/` changes (F-007+).
- **Project file writes** — no updating `spec.yaml`, `assumptions.yaml`, `history.json`, or `part.cad` (F-008+ / golden path).
- **Workspace integration** — no `create_part_folder` or `exports/` writes as part of executor (tests may write STEP to `tmp_path`).
- **Risk classifier / `ir.pending`** — no approval workflow (F-022).
- **Full implementation of all MVP ops** — only three geometry ops are real; others are stubs.
- **Assembly mates** — mate handlers are stubs only.
- **Viewport tessellation / mesh IPC** — no `geometry.update` events (F-011).
- **Editing** `docs/feature_roadmap.md` or `docs/architecture.md`.

## Requirements

### Execution result model

- Location: `backend/engine/execution_result.py` (or types in `executor.py`).
- `ExecutionResult` fields (minimum):
  - `success: bool`
  - `step_ids: list[str]` — ids executed in order
  - `final_step_id: str | None` — last step id when successful
  - `error: str | None` — message when `success` is false
- Optional: `shapes_by_step_id` for tests (internal or test-only accessor); do not serialize OCCT shapes over JSON-RPC.

### `backend/engine/kernel_adapter.py`

Thin pass-through to `kernel/occt_bridge.py` only:

| Adapter method | Bridge call |
|----------------|-------------|
| `sketch_rectangle(...)` | `occt_bridge.sketch_rectangle` |
| `extrude(...)` | `occt_bridge.extrude` |
| `hole_pattern_corners(...)` | `occt_bridge.hole_pattern_corners` |

No direct `OCC` imports in `kernel_adapter.py`.

### `backend/engine/step_handlers/`

| File / module | `op` | F-004 behavior |
|---------------|------|----------------|
| `sketch_rectangle.py` | `sketch_rectangle` | Read `params`: `length`, `width`, `plane`, `mode` → adapter |
| `extrude.py` | `extrude` | Requires input shape from `from` step; `distance`, `direction`, `mode` |
| `hole_pattern.py` | `hole_pattern_corners` | Requires input solid from `from`; `diameter`, `offset` |
| `stub.py` (or per-op stubs) | All other `MVP_STEP_OPS` | Raise `StepNotImplementedError` with `op` name |

Handlers receive: `step: IRStep`, `inputs: dict[str, TopoDS_Shape]` (shapes keyed by prior step id). Return `TopoDS_Shape`.

`StepNotImplementedError` and `ExecutionError` (or `StepExecutionError`) must be distinct from `GeometryError` and `IntentIRValidationError`.

### Handler registry

- Location: `backend/engine/handler_registry.py` (or registry inside `executor.py`).
- `get_handler(op: str) -> StepHandler` — returns callable or raises for unknown op (validator already blocks unknown ops in IR).
- Register all `MVP_STEP_OPS` entries.

### `backend/engine/executor.py`

Public API:

```python
def execute_intent_ir(intent: IntentIR) -> ExecutionResult
```

Behavior:

1. Reject empty `steps` with structured failure (or succeed with no geometry — prefer explicit error for F-004 golden test which has steps).
2. Build dependency order: steps with `from` null first, then steps whose `from` references an earlier `id`; detect missing/forward `from` references → `ExecutionError`.
3. For each step in order: resolve input shape from cache via `from`; invoke handler; store output shape under step `id`.
4. On `GeometryError`, `StepNotImplementedError`, or handler failure: return `ExecutionResult(success=False, error=...)`.
5. On success: `final_step_id` is the last step in execution order.

Must not call `validate_intent_ir` internally if caller already validated — but `execute_intent` RPC path must validate first.

### `backend/project/export.py`

```python
def export_step_file(shape: TopoDS_Shape, path: Path) -> None
```

Delegates to `kernel.occt_bridge.export_step`. No other export formats in F-004.

### JSON-RPC: `execute_intent`

In `backend/main.py`:

```python
@method
def execute_intent(ir: dict) -> Success | Error
```

- Validate with `validate_intent_ir(ir)`; on failure return JSON-RPC error with `IntentIRValidationError.to_dict()`.
- Call `execute_intent_ir(intent)`.
- On execution failure return error with `error` message.
- On success return `{"success": true, "step_ids": [...], "final_step_id": "..."}` (no shape payload).

`ping` remains available. No other new JSON-RPC methods.

### Step parameter mapping (golden alignment)

Must match F-001 / F-003 golden mounting plate:

| Step id | op | params |
|---------|-----|--------|
| s1 | `sketch_rectangle` | `length`, `width`, `plane`, `mode` |
| s2 | `extrude` | `distance`, `direction`, `mode`; `from` → s1 |
| s3 | `hole_pattern_corners` | `diameter`, `offset`; `from` → s2 |

## Data model and contracts

### Execution flow

```
IntentIR (validated)
    → executor.execute_intent_ir
    → for each step in dependency order:
        handler_registry.get_handler(step.op)
        → step_handler(step, shapes_cache)
        → kernel_adapter (optional)
        → occt_bridge
    → ExecutionResult
```

### Boundary with adjacent features

| Layer | F-003 | F-004 |
|-------|-------|-------|
| `occt_bridge.py` | Real ops | Unchanged (called via adapter) |
| `kernel_adapter.py` | Placeholder | Thin wrapper |
| `step_handlers/*` | Placeholder | Real + stubs |
| `executor.py` | Placeholder | Full sequencer |
| `main.py` | `ping` only | `ping` + `execute_intent` |
| `project/export.py` | Placeholder | `export_step_file` wrapper |

## Acceptance criteria

1. **Handler registry:** Every op in `MVP_STEP_OPS` has a registered handler; unknown op at runtime cannot occur for validated IR.
2. **Stub ops:** Calling `execute_intent_ir` with a single-step IR using e.g. `fillet` raises/returns failure with `StepNotImplementedError` semantics.
3. **Dependency errors:** IR with `from` referencing missing or future step id fails before geometry runs.
4. **Mounting plate execution:** `execute_intent_ir(validate_intent_ir(mounting_plate_ir()))` succeeds; `final_step_id == "s3"`.
5. **STEP export:** After successful execution, `export_step_file(final_shape, path)` writes non-empty STEP; `read_step(path)` succeeds on platforms with OCCT (same skip rules as F-003 tests).
6. **JSON-RPC:** Stdio dispatch of `execute_intent` with `mounting_plate_ir()` returns success JSON; invalid IR returns validation error.
7. **OCCT boundary:** `rg "from OCC" backend --glob "!kernel/occt_bridge.py"` has no matches.
8. **No frontend changes:** No files under `frontend/` modified.
9. **Tests:** New `tests/backend/test_executor_mounting_plate.py` (and any registry/stub tests) pass; existing F-001/F-002/F-003 tests still pass.
10. **OCCT skip:** Mounting plate executor + STEP tests use `pytest.importorskip("OCC.Core.TopoDS")` or equivalent when `pythonocc-core` unavailable.

## Dependencies

- **F-001** — `IntentIR`, `validate_intent_ir`, `MVP_STEP_OPS`, mounting plate IR fixture.
- **F-003** — `occt_bridge` ops and `export_step` / `read_step`.
- **F-002** — not required for F-004 execution (no workspace writes).
