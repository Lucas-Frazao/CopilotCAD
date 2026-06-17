# F-006 — Problems engine

## Summary

Implement the MVP Problems engine: a Pydantic `Problem` model, seven typed detectors aligned with `docs/architecture.md`, and `evaluate_problems()` that runs after Intent IR execution (and on IR-only pre-checks). Wire into `execute_intent` JSON-RPC so results include a `problems` list. Unit tests trigger each problem type with constructed IR and execution outcomes.

**Status:** Implemented.

## Context and goals

Problems are computed signals — not user-entered notes — surfaced after compile/execute paths (`docs/product_vision.md`, `docs/architecture.md`). F-006 delivers backend detection and structured objects; F-010 renders them in the UI.

Goals:

- Define `Problem` schema with stable `type` identifiers for all 7 MVP problem types.
- Implement `problems/engine.py` with `evaluate_problems(intent, execution_result=None)`.
- Run IR-level checks before or without geometry (blocking questions, assumptions, traceability, manufacturing hints, assembly/interface stubs).
- Run execution-level checks when `ExecutionResult.success` is false (`geometry_generation_failure`).
- Extend `execute_intent` JSON-RPC success and failure responses to include `problems: [...]`.
- Unit test each problem type with a minimal triggering fixture.

## Non-goals

- **Frontend / Problems panel** — no `frontend/` changes (F-010).
- **`chat.send` / `problems.update` IPC events** — event broadcast is F-007+; F-006 returns problems in `execute_intent` result JSON only.
- **Live workspace file reads** — no loading `spec.yaml` from disk for traceability; use IR `links` and `target` only (file-based traceability deferred).
- **Full assembly/mate validation** — interface and mate problems use IR-level heuristics/stubs until F-018–F-021.
- **Problems after `compile_intent` only** — F-006 focuses on post-`execute_intent` wiring; optional IR-only problems on validated IR passed to `evaluate_problems` without execution.
- **Risk classifier / `ir.pending`** — F-022.
- **Editing** `docs/feature_roadmap.md` or `docs/architecture.md`.

## MVP problem types

| Type id | Trigger (F-006 implementation) |
|---------|--------------------------------|
| `missing_required_input` | Any `questions[]` item with `blocking=true` and `status="open"` |
| `unresolved_assumption` | Any `assumptions[]` with `importance="high"` and `status="proposed"` |
| `geometry_generation_failure` | `execution_result` provided and `success=false` |
| `interface_conflict` | `type` is `assembly_create` and `constraints.interfaces` lists duplicate interface ids |
| `invalid_mate` | Any step `op` starts with `mate_` and `params` missing required mate fields (`target`, `mate_type`, or empty `params`) |
| `manufacturing_rule_warning` | `constraints.process` set and `constraints.dimensions` empty (cannot verify process without dimensions) |
| `traceability_gap` | `type` is `part_create` or `part_edit` with `target.part_id` set and empty `links.spec_refs` |

Severity defaults:

| Type | Default severity |
|------|------------------|
| `missing_required_input` | `blocking` |
| `unresolved_assumption` | `warning` |
| `geometry_generation_failure` | `error` |
| `interface_conflict` | `error` |
| `invalid_mate` | `error` |
| `manufacturing_rule_warning` | `warning` |
| `traceability_gap` | `warning` |

## Requirements

### Schema: `backend/schemas/problem.py`

Pydantic v2 strict models:

```python
ProblemType = Literal[
    "missing_required_input",
    "unresolved_assumption",
    "geometry_generation_failure",
    "interface_conflict",
    "invalid_mate",
    "manufacturing_rule_warning",
    "traceability_gap",
]

ProblemSeverity = Literal["warning", "error", "blocking"]
```

`Problem` fields (minimum):

| Field | Type | Required |
|-------|------|----------|
| `id` | str | Yes — stable slug per detection pass, e.g. `{type}:{part_id or "global"}` |
| `type` | ProblemType | Yes |
| `severity` | ProblemSeverity | Yes |
| `message` | str | Yes — human-readable |
| `part_id` | str | No — from `target.part_id` or context |
| `step_id` | str | No — related IR step when applicable |
| `suggested_next_steps` | list[str] | No — 1–3 short strings |

Export `ProblemList` as `list[Problem]` alias or wrapper if useful for typing.

### Module: `backend/problems/engine.py`

```python
def evaluate_problems(
    intent: IntentIR,
    execution_result: ExecutionResult | None = None,
) -> list[Problem]:
```

- Pure function: no filesystem, no network.
- Returns empty list when no issues detected.
- Multiple problems may be returned in one pass.
- `geometry_generation_failure` only when `execution_result` is not None and `not execution_result.success`; message should include `execution_result.error` when present.

Optional helper:

```python
def problems_to_dicts(problems: list[Problem]) -> list[dict[str, Any]]:
```

using `model_dump()` for JSON-RPC.

### Wiring: `backend/main.py`

Update `execute_intent`:

1. Validate IR (unchanged).
2. Run `execute_intent_ir(intent)`.
3. Run `evaluate_problems(intent, result)`.
4. Return `Success({**result.to_dict(), "problems": problems_to_dicts(problems)})` on execution success.
5. On execution failure, still return `Error` but include `problems` in error `data` payload alongside existing execution fields.

Do not change `compile_intent` or `ping` in F-006.

### Tests: `tests/backend/test_problems_engine.py`

One test function per problem type (minimum), plus:

- `test_evaluate_problems_clean_ir_returns_empty` — mounting plate IR + successful mock execution → no problems (or only warnings if assumptions proposed — use confirmed assumptions in fixture).
- `test_execute_intent_jsonrpc_includes_problems` — failed execution (stub op) returns problems including `geometry_generation_failure`.

Use `IntentIR` from dict via `validate_intent_ir` where possible.

## Data model

### Integration with F-004

```
validate_intent_ir(ir)
    → execute_intent_ir(intent)
    → evaluate_problems(intent, execution_result)
    → JSON-RPC result { success, step_ids, ..., problems: [...] }
```

### Boundary with F-010

F-010 consumes the same `Problem` shape via IPC `problems.update`. F-006 establishes the schema and backend computation only.

## Acceptance criteria

1. `schemas/problem.py` defines `Problem`, `ProblemType`, `ProblemSeverity` with strict Pydantic config.
2. `evaluate_problems` implements all 7 MVP problem type detectors per table above.
3. `evaluate_problems` returns an empty list for a clean mounting plate IR with successful execution and no blocking questions / high proposed assumptions.
4. Each problem type has a dedicated pytest that triggers exactly that type (may include others but must assert target type present).
5. `execute_intent` JSON-RPC response includes `problems` array on success and on execution failure.
6. No `frontend/` file changes.
7. No OCCT imports outside `kernel/occt_bridge.py`.
8. Existing F-001–F-005 tests still pass (update `test_execute_intent_jsonrpc_*` if response shape adds `problems` field).

## Dependencies

- **F-001** — `IntentIR`, questions, assumptions, links, constraints.
- **F-004** — `ExecutionResult`, `execute_intent_ir`.
- **F-005** — not required for F-006 (no compile path changes).
