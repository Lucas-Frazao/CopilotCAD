# F-001 — Intent IR schema and validation

## Summary

Define **Intent IR** — the strict JSON “plan” every CopilotCAD action must follow — and a **validator** that rejects bad plans before any geometry or files are touched. Think of it as a compiler’s type checker for hardware intent.

**Status:** Implemented.

## Why this matters

CopilotCAD’s core promise is **English → structured plan → CAD**, not “text → random shape.” F-001 defines what a valid plan looks like and catches mistakes early (wrong step types, broken dependencies) with clear errors instead of silent corruption.

## Key concepts


| Term                    | Plain meaning                                                                                                                    |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Intent IR**           | Intermediate Representation — a JSON document describing what to do: part type, summary, modeling steps, assumptions, questions. |
| **Pydantic**            | Python library that validates data against a schema (like TypeScript types at runtime).                                          |
| **Step**                | One modeling operation in order — e.g. sketch rectangle, then extrude, then drill holes.                                         |
| **Step catalog**        | Allowed operation names (`sketch_rectangle`, `extrude`, `hole_pattern_corners`, mates, etc.).                                    |
| **Dependency (`from`)** | A step that needs output from a previous step — e.g. extrude must reference the sketch step id.                                  |
| **Validator**           | Code that checks IR dicts and returns a typed object or structured errors.                                                       |


## What the user will experience

End users do not interact with Intent IR directly in F-001. What this enables:

- Later, when chat compiles English to IR, **invalid AI output fails safely** with explainable errors instead of crashing the kernel.
- Engineers can unit-test “good” and “bad” plans without running geometry.

## What we will build

### Schema (`backend/schemas/intent_ir.py`)

Models for: `IntentIR`, `IRTarget`, `IRContext`, `IRQuestion`, `IRAssumption`, `IRConstraints`, `IRStep`, `IRLinks`.

- Strict mode: unknown fields are rejected.
- `MVP_STEP_OPS` — frozen set of all allowed `steps[].op` values (sketch, extrude, holes, mates, patterns, etc.).
- Intent types: `part_create`, `part_edit`, `assembly_create`, `doc_scaffold`, `export`, `release`.

### Validator (`backend/ir/validator.py`)

- `validate_intent_ir(data: dict) -> IntentIR`
- `IntentIRValidationError` with `field_errors`, `invalid_ops`, and `to_dict()` for APIs.
- Rules: unique step ids, `from` only references earlier steps, ops must be in catalog.

### Golden mounting plate IR (test fixture)

Three steps aligned with the canonical example:

1. `sketch_rectangle` — 100×50 mm on XY plane
2. `extrude` — 6 mm, from sketch
3. `hole_pattern_corners` — 6 mm diameter, 8 mm offset

### Tests (`tests/backend/test_intent_ir_validation.py`)

Valid IR passes; missing fields, bad ops, and forward dependencies fail with structured errors.

## Acceptance criteria

1. All eight model types importable from `schemas.intent_ir`.
2. Extra unknown fields fail validation (strict mode).
3. Golden mounting plate IR passes with three steps and correct `from` chain.
4. Invalid op types appear in `invalid_ops` and field errors.
5. Invalid step dependencies raise `invalid_step_dependency`.
6. Pytest for `test_intent_ir_validation.py` passes.
7. No changes to `main.py` or Electron — validation is library-only in F-001.

## Dependencies

- **F-000** — repo and Python package layout.

## Out of scope (not in F-001)

- LLM prompting or JSON parsing from AI text (F-005).
- Executing steps or calling OCCT (F-003, F-004).
- IPC exposure of validation (F-007+).
- Full `spec.yaml` schemas (separate from IR).
- Per-op parameter validation inside handlers (F-004).

## Notes for reviewers

Intent IR is the **contract** between AI, backend, and UI. F-001 makes that contract explicit and testable.