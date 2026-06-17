# F-003 — Geometry kernel stub and OCCT bridge

## Summary

Install and integrate `pythonOCC-core` as the geometry kernel, implement a thin OCCT bridge with three working modeling operations (`sketch_rectangle`, `extrude`, `hole_pattern_corners`), add minimal STEP export from a `TopoDS_Shape`, and prove the mounting plate golden example can be built and exported to a valid STEP file using Python alone. F-003 delivers kernel-level geometry capability only; it does not execute Intent IR, wire IPC, or touch the frontend.

**Status:** Implemented (OCCT tests require `pythonocc-core`; skipped when unavailable, e.g. Windows ARM64).

## Context and goals

CopilotCAD’s geometry kernel is Open CASCADE Technology (OCCT) accessed via `pythonOCC-core` (`docs/architecture.md`, `docs/tech_stack.md`). Application logic must never call OCCT directly; all kernel access goes through `backend/kernel/occt_bridge.py` so the kernel can be swapped later.

F-001 defines the mounting plate golden Intent IR (three steps: rectangle sketch → extrude → corner hole pattern). F-004 will execute that IR through `kernel_adapter.py` and step handlers. F-003 must make the underlying geometry operations real and testable first.

Goals:

- Ensure `pythonOCC-core` is installable via the backend dependency set (`backend/pyproject.toml`) on supported developer platforms (Python 3.11+).
- Implement `occt_bridge.py` with working B-Rep operations for the three ops needed by the mounting plate golden path.
- Implement STEP export from a final solid shape to a file on disk.
- Provide a standalone pytest (or equivalent) that builds the mounting plate by calling the bridge directly and writes a STEP file that is non-empty and parseable as STEP.
- Establish clear boundaries so F-004 can wrap the bridge without redesign.

## Non-goals

- **Intent IR execution** — no `executor.py`, no step handlers, no `kernel_adapter.py` (F-004).
- **JSON-RPC / IPC** — no changes to `main.py`, Electron, or frontend (F-000 wiring stays as-is).
- **LLM / IR compiler** — no parsing, validation changes, or API calls (F-005).
- **Project file writes** — no `part.cad`, no writing to `exports/` via `project/export.py` workspace integration (F-004 / F-024).
- **Full MVP op catalog** — only `sketch_rectangle`, `extrude`, and `hole_pattern_corners` are implemented in F-003; all other ops remain stubs until F-004.
- **IGES export** — STEP only in F-003 (IGES deferred to F-024).
- **Viewport / tessellation** — no mesh data for Three.js (F-011).
- **Assembly mates, fillets, patterns** — not required in F-003.
- **Problems engine, history, assumptions** — no post-geometry validation or project updates.

## Requirements

### Dependency and environment

- `pythonocc-core>=7.7` must remain declared in `backend/pyproject.toml` (already present per `docs/tech_stack.md`).
- Backend targets Python 3.11+ (`requires-python` in `pyproject.toml`).
- Document in test or module docstring if a platform cannot install `pythonocc-core` (e.g. some Windows ARM builds); tests may be marked skipped on unsupported platforms rather than failing the whole suite.

### Module: `backend/kernel/occt_bridge.py`

Single module owning all direct `pythonOCC` / OCCT imports for F-003. No other backend module may import OCCT except this file (enforced by convention; F-004 `kernel_adapter` calls into this module only).

#### Responsibilities

| Responsibility | Owner in F-003 |
|----------------|----------------|
| OCCT / pythonOCC imports | `occt_bridge.py` only |
| Sketch → face/wire construction | `occt_bridge.py` |
| Solid build (extrude) and boolean cut (holes) | `occt_bridge.py` |
| STEP file write from `TopoDS_Shape` | `occt_bridge.py` |
| Parameter validation for op inputs | `occt_bridge.py` (raise clear `ValueError` or dedicated `GeometryError`) |
| Intent IR parsing / step sequencing | Not F-003 (F-004) |
| Project path resolution | Not F-003 (F-002 / F-004) |

#### What “geometry kernel stub” means at F-003

- **Implemented:** Three ops with real OCCT geometry output, plus STEP export. Enough to produce a valid mounting plate solid in isolation.
- **Stub (not implemented):** All other MVP ops in `MVP_STEP_OPS` (`specs/F-001_intent_ir_validation.md`), IR-driven sequencing, shape caching in `.cad`, and integration with `engine/` modules.
- **F-004 carries forward:** `kernel_adapter.py` as a thin pass-through to `occt_bridge`, `executor.py` sequencing, per-op `step_handlers/`, and execution from validated `IntentIR`.

### Operations to implement

Each operation returns a geometry handle the next operation can consume. The canonical handle type for F-003 is OCCT `TopoDS_Shape` (or a small wrapper dataclass containing `TopoDS_Shape` and optional metadata). All functions must be pure at the API level: inputs + prior shape → new shape; no global mutable kernel state.

#### `sketch_rectangle`

Build a planar rectangular sketch suitable for extrusion.

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `length` | float | Yes | Full length (mm) |
| `width` | float | Yes | Full width (mm) |
| `plane` | str | Yes | MVP: `"XY"` only |
| `mode` | str | Yes | MVP: `"center"` (rectangle centered on origin) |

Returns: shape representing the sketch profile (wire or face) on the requested plane.

#### `extrude`

Extrude a profile shape into a solid.

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `profile` | `TopoDS_Shape` | Yes | Output of `sketch_rectangle` |
| `distance` | float | Yes | Extrusion distance (mm) |
| `direction` | str | Yes | MVP: `"+Z"` only |
| `mode` | str | Yes | MVP: `"add"` (single solid add; no cut/revolve variants) |

Returns: `TopoDS_Shape` solid.

#### `hole_pattern_corners`

Cut a pattern of holes at the four corners of a rectangular plate solid.

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `solid` | `TopoDS_Shape` | Yes | Output of `extrude` |
| `diameter` | float | Yes | Hole diameter (mm) |
| `offset` | float | Yes | Edge offset from plate boundary to hole center (mm) |

Returns: `TopoDS_Shape` solid with holes cut.

Implementation note: op name in IR is `hole_pattern_corners` (`specs/F-001_intent_ir_validation.md`); bridge function name may be `hole_pattern_corners` or equivalent; must match what F-004 step handler will call.

#### `export_step`

Write a shape to a STEP file.

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| `shape` | `TopoDS_Shape` | Yes | Final solid |
| `path` | `pathlib.Path` or `str` | Yes | Output file path |

Behavior:

- Creates parent directories if missing.
- Writes AP214 or AP203 STEP via OCCT `STEPControl` (per `docs/tech_stack.md`).
- Raises on write failure with a clear exception message.
- Does not update workspace `exports/` or manifest; caller chooses path (tests use `tmp_path`).

### Golden mounting plate (Python-only pipeline)

Standalone test and documentation reference the same sequence aligned with F-001 golden IR and `docs/tech_stack.md` `.cad` feature params:

1. `sketch_rectangle(length=100.0, width=50.0, plane="XY", mode="center")`
2. `extrude(profile, distance=6.0, direction="+Z", mode="add")`
3. `hole_pattern_corners(solid, diameter=6.0, offset=8.0)`
4. `export_step(final_solid, output_path)`

Expected result: a single solid mounting plate (100×50 mm footprint, 6 mm thick, four corner holes).

### Unit / integration test

- Location: `tests/backend/test_occt_bridge_mounting_plate.py` (or equivalent name under `tests/backend/`).
- Must run without Electron, IPC, or Intent IR validator.
- Steps:
  1. Call the three geometry functions in order with golden parameters.
  2. Export STEP to a temporary path.
  3. Assert output file exists and size &gt; 0 bytes.
  4. Assert file content begins with STEP header convention (e.g. starts with `ISO-10303-21` or contains `STEP`/`HEADER` per common STEP text format) **or** re-import via OCCT STEP reader and confirm a non-null shape (preferred if import is reliable in test env).
- Test may use `pytest.mark.skipif` when `pythonocc-core` is not installed.

### Error handling

- Invalid parameters (negative dimensions, unsupported `plane`/`direction`) raise a dedicated `GeometryError` (or `ValueError` with stable message prefix) before invoking OCCT.
- OCCT failures must not be silently swallowed; propagate or wrap in `GeometryError` with context.

## Data model and contracts

### Geometry handle

| Name | Type | Description |
|------|------|-------------|
| `TopoDS_Shape` | OCCT shape | Canonical geometry object passed between bridge functions |

Optional future wrapper (not required in F-003):

```python
@dataclass
class GeometryResult:
    shape: TopoDS_Shape
```

### Golden mounting plate parameters (canonical)

| Step | Op | Params |
|------|-----|--------|
| 1 | `sketch_rectangle` | `length=100.0`, `width=50.0`, `plane="XY"`, `mode="center"` |
| 2 | `extrude` | `distance=6.0`, `direction="+Z"`, `mode="add"` |
| 3 | `hole_pattern_corners` | `diameter=6.0`, `offset=8.0` |

Aligns with `tests/backend/test_intent_ir_validation.py` `mounting_plate_ir()` step params and `specs/F-001_intent_ir_validation.md` golden IR.

### Bridge function contracts (summary)

| Function | Input | Output |
|----------|-------|--------|
| `sketch_rectangle(...)` | numeric + enum-like strings | `TopoDS_Shape` (profile) |
| `extrude(profile, ...)` | profile shape + params | `TopoDS_Shape` (solid) |
| `hole_pattern_corners(solid, ...)` | solid + params | `TopoDS_Shape` (solid) |
| `export_step(shape, path)` | solid + path | `None` (writes file) |

### STEP file contract

| Property | Requirement |
|----------|-------------|
| Format | STEP AP203 or AP214 via `STEPControl` |
| Content | Single solid representing mounting plate |
| Min size | &gt; 0 bytes |
| Validity | Readable by OCCT STEP import **or** identifiable STEP text header |

### Boundary with F-004

| Layer | F-003 | F-004 |
|-------|-------|-------|
| `occt_bridge.py` | Real ops + `export_step` | Same; may add more ops |
| `engine/kernel_adapter.py` | Not implemented | Thin wrapper calling bridge |
| `engine/step_handlers/*` | Not implemented | Map IR step params → bridge calls |
| `engine/executor.py` | Not implemented | Sequence IR steps |
| `project/export.py` | Not implemented | May call `export_step` for workspace paths |

## Acceptance criteria

1. **Install:** `uv pip install pythonocc-core` (or full backend deps) succeeds on a supported CI/dev platform with Python 3.11; import of `OCC.Core.TopoDS` (or equivalent) works in tests.
2. **Bridge module:** `backend/kernel/occt_bridge.py` implements `sketch_rectangle`, `extrude`, `hole_pattern_corners`, and `export_step` with no OCCT imports elsewhere in `backend/`.
3. **Mounting plate geometry:** Chaining the three ops with golden parameters produces a non-null `TopoDS_Shape` without exception.
4. **STEP export:** `export_step` writes a file; file exists, is non-empty, and passes STEP validity check defined in Requirements.
5. **Standalone test:** `pytest` for the mounting plate OCCT test passes on supported platforms (skipped with clear reason on unsupported platforms if needed).
6. **No IPC changes:** `backend/main.py` still only exposes `ping`; no new JSON-RPC methods.
7. **No frontend changes:** No files under `frontend/` modified for F-003.
8. **No IR execution:** `executor.py`, `kernel_adapter.py`, and step handlers remain stubs or unchanged beyond any import path prep; mounting plate is **not** built via `validate_intent_ir` + executor in F-003.
9. **F-001 alignment:** Golden parameters match F-001 mounting plate IR step params (100×50×6 mm plate, 6 mm holes, 8 mm corner offset).
