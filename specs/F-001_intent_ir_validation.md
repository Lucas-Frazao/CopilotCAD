# F-001 — Intent IR schema and validation

## Summary

Define the slim Intent IR as strict Pydantic v2 models and a validator that rejects invalid IR before any geometry or project writes occur. F-001 establishes the contract between LLM output (future F-005), the compiler pipeline (`docs/architecture.md`), and the execution engine (F-004). No IPC, LLM, or file-system integration is required in this feature.

**Status:** Implemented.

## Context and goals

Every write operation in CopilotCAD must compile into a structured Intent IR object (`docs/product_vision.md`, `docs/architecture.md`). F-001 makes that object explicit, machine-validated, and testable.

Goals:

- Encode the slim IR fields: `type`, `prompt`, `summary`, `target`, `context`, `questions`, `assumptions`, `constraints`, `steps`, `links`.
- Enforce Pydantic strict mode (`extra="forbid"`) so unknown fields fail validation.
- Restrict `steps[].op` to the MVP step catalog from `docs/product_vision.md`.
- Validate step identity and dependency order (`from` references only prior steps).
- Expose `validate_intent_ir(data: dict) -> IntentIR` with structured errors for schema, field, and op-type failures.
- Provide unit tests using the mounting plate golden IR as a known-good example.

## Non-goals

- LLM prompting, parsing, or `ir/parser.py` implementation (F-005).
- Risk classification or approval workflow (F-022).
- Per-op required-parameter validation beyond op-type allowlisting (may be added later in F-004 step handlers).
- Execution of steps or geometry kernel calls (F-003, F-004).
- IPC exposure of validation (F-007+).
- Full `spec.yaml` / `assumptions.yaml` / `part_spec.py` schemas (separate schemas; F-002+).
- Validating traceability against live project files on disk.

## Requirements

### Schema module

- Location: `backend/schemas/intent_ir.py`.
- All models use Pydantic v2 with `model_config = ConfigDict(extra="forbid", strict=True)` (except `IRStep`, which also uses `populate_by_name=True` for the `from` alias).

### Models to define

| Model | Role |
|-------|------|
| `IntentIR` | Root IR document |
| `IRTarget` | Part, assembly, or doc target |
| `IRContext` | Active part, selection, workspace path |
| `IRQuestion` | Blocking or non-blocking questions |
| `IRAssumption` | Scoped assumption with status |
| `IRConstraints` | Dimensions, material, process, tolerance, interfaces |
| `IRStep` | Ordered modeling or mate step |
| `IRLinks` | Traceability references |

### `IntentIR` required and default fields

| Field | Required | Default / notes |
|-------|----------|----------------|
| `type` | Yes | One of MVP intent types (see Data model) |
| `prompt` | Yes | Original user message |
| `summary` | Yes | Short execution summary |
| `target` | Yes | `IRTarget` |
| `context` | No | Empty `IRContext` if omitted |
| `questions` | No | Empty list |
| `assumptions` | No | Empty list |
| `constraints` | No | Empty `IRConstraints` |
| `steps` | No | Empty list |
| `links` | No | Empty `IRLinks` |

### MVP step catalog (`MVP_STEP_OPS`)

The validator must reject any `steps[].op` not in this set:

- Sketch: `sketch_rectangle`, `sketch_circle`
- Solid: `extrude`, `cut_extrude`, `revolve`
- Holes: `hole_simple`, `hole_pattern_corners`
- Edges: `fillet`, `chamfer`
- Patterns: `pattern_linear`, `pattern_circular`, `mirror`
- Other: `shell`, `offset_face`, `create_plane`, `create_axis`, `create_point`
- Assembly mates: `mate_fix`, `mate_coincident`, `mate_concentric`, `mate_distance`

Export `MVP_STEP_OPS` as a `frozenset[str]` from `intent_ir.py` for use by the validator and tests.

### Validator module

- Location: `backend/ir/validator.py`.
- Function: `validate_intent_ir(data: dict) -> IntentIR`.
- Exception: `IntentIRValidationError` with:
  - `message` (str)
  - `field_errors` (list of dicts with `loc`, `msg`, `type`)
  - `invalid_ops` (list of str)
  - `to_dict()` for serialization

Validation order:

1. Collect invalid op types from `data["steps"]` (if present).
2. Validate step dependency graph on raw step dicts.
3. Run `IntentIR.model_validate(data)`.
4. If any errors accumulated, raise `IntentIRValidationError` with all field errors and invalid ops.
5. On success, return validated `IntentIR`.

### Step dependency rules

- Each `steps[].id` must be unique within the IR.
- If `steps[].from` is present, it must be a string referencing the `id` of a step that appears earlier in the `steps` list.
- Forward references and references to unknown ids must fail with `type: "invalid_step_dependency"`.
- Duplicate ids must fail with `type: "duplicate_step_id"`.

### Unit tests

- Location: `tests/backend/test_intent_ir_validation.py`.
- **Valid IR:** Mounting plate example (see Data model) passes `validate_intent_ir` and returns `IntentIR` with expected `type`, `target.part_id`, step count, and `from` linkage.
- **Missing required field:** Removing `summary` (or another required field) raises `IntentIRValidationError` with a field error whose `loc` includes that field.
- **Invalid op type:** Setting a step `op` to a value outside `MVP_STEP_OPS` raises `IntentIRValidationError` with that op in `invalid_ops` and a field error with `type: "invalid_op_type"`.
- **Invalid dependency:** Setting `from` to a forward or unknown step id raises `IntentIRValidationError` with `type: "invalid_step_dependency"`.

## Data model and contracts

### Intent types (`IntentIR.type`)

Allowed values:

- `part_create`
- `part_edit`
- `assembly_create`
- `doc_scaffold`
- `export`
- `release`

### `IRTarget`

| Field | Type | Required |
|-------|------|----------|
| `part_id` | string \| null | No (default null) |
| `assembly_id` | string \| null | No |
| `doc_path` | string \| null | No |

### `IRContext`

| Field | Type | Default |
|-------|------|---------|
| `active_part_id` | string \| null | null |
| `selection` | list of string | `[]` |
| `workspace_path` | string \| null | null |

### `IRQuestion`

| Field | Type | Default |
|-------|------|---------|
| `id` | string | required |
| `text` | string | required |
| `blocking` | bool | `false` |
| `status` | `open` \| `answered` \| `dismissed` | `open` |
| `answer` | string \| null | null |

### `IRAssumption`

| Field | Type | Default |
|-------|------|---------|
| `id` | string | required |
| `text` | string | required |
| `scope` | `part` \| `assembly` \| `project` | `part` |
| `source` | `user` \| `ai` \| `spec` | `ai` |
| `importance` | `low` \| `medium` \| `high` | `medium` |
| `status` | `proposed` \| `confirmed` \| `rejected` | `proposed` |

### `IRConstraints`

| Field | Type | Default |
|-------|------|---------|
| `dimensions` | object (arbitrary keys) | `{}` |
| `material` | string \| null | null |
| `process` | string \| null | null |
| `tolerance` | object | `{}` |
| `interfaces` | list of string | `[]` |

### `IRStep`

| Field | JSON key | Type | Default |
|-------|----------|------|---------|
| `id` | `id` | string | required |
| `op` | `op` | string | required (must be in `MVP_STEP_OPS` after validator) |
| `params` | `params` | object | `{}` |
| `from_step` | `from` | string \| null | null |

### `IRLinks`

| Field | Type | Default |
|-------|------|---------|
| `spec_refs` | list of string | `[]` |
| `requirement_refs` | list of string | `[]` |
| `architecture_refs` | list of string | `[]` |

### `IntentIRValidationError` payload (`to_dict()`)

```json
{
  "message": "Intent IR validation failed",
  "field_errors": [
    { "loc": ["summary"], "msg": "...", "type": "missing" }
  ],
  "invalid_ops": ["magic_extrude"]
}
```

### Golden mounting plate IR (known-good test fixture)

Minimal valid IR used in tests and referenced by F-004:

- `type`: `part_create`
- `target.part_id`: `mounting_plate`
- `steps`:
  1. `s1` — `sketch_rectangle` with `length`, `width`, `plane`, `mode` params
  2. `s2` — `extrude`, `from`: `s1`, with `distance`, `direction`, `mode`
  3. `s3` — `hole_pattern_corners`, `from`: `s2`, with `diameter`, `offset`

## Acceptance criteria

1. **Models importable:** `from schemas.intent_ir import IntentIR, MVP_STEP_OPS` succeeds; all eight model types are defined.
2. **Strict mode:** An IR dict with an extra top-level field fails validation.
3. **Valid mounting plate:** Golden IR dict passes `validate_intent_ir` and yields `IntentIR` with three steps and correct `from` chain on step `s2`.
4. **Missing required field:** Validator raises `IntentIRValidationError` with field errors identifying the missing field.
5. **Invalid op:** Validator raises `IntentIRValidationError` with `invalid_ops` containing the bad op and `field_errors` including `invalid_op_type`.
6. **Invalid dependency:** Validator raises `IntentIRValidationError` with `invalid_step_dependency` when `from` points forward or to a missing id.
7. **Tests pass:** `pytest` for `tests/backend/test_intent_ir_validation.py` reports all tests green.
8. **No pipeline wiring:** `main.py` and Electron code are unchanged; no new JSON-RPC methods in F-001.
