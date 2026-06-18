# F-003 — Geometry kernel stub and OCCT bridge

## Summary

Connect CopilotCAD to a real **3D geometry kernel** (Open CASCADE via `pythonOCC`) and implement three modeling operations plus **STEP export** — enough to build the canonical **mounting plate** in Python alone, with no UI.

**Status:** Implemented (OCCT tests skip when `pythonocc-core` is unavailable, e.g. some Windows ARM builds).

## Why this matters

Text plans are useless without **real solids**. F-003 proves the kernel can sketch, extrude, drill corner holes, and export industry-standard STEP files before the execution engine (F-004) orchestrates those calls from Intent IR.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **OCCT / Open CASCADE** | Open-source precise CAD kernel — industry-grade B-rep (boundary representation) solids. |
| **pythonOCC** | Python bindings for OCCT (`pythonocc-core` package). |
| **B-rep / TopoDS_Shape** | Internal precise shape object passed between kernel functions. |
| **sketch_rectangle** | Create a flat rectangular profile on a plane (e.g. XY). |
| **extrude** | Sweep a profile into a 3D solid (add thickness). |
| **hole_pattern_corners** | Cut four holes near the corners of a rectangular plate. |
| **STEP** | Standard file format for exchanging 3D CAD models (.step / .stp). |
| **occt_bridge** | Single module that owns all direct OCCT imports — swap kernel later by changing this file only. |

## What the user will experience

No UI in F-003. A developer or CI job runs pytest and:

1. Builds 100×50×6 mm plate with 6 mm corner holes in memory.
2. Writes a STEP file to a temp path.
3. File is non-empty and recognizable as valid STEP.

That geometry becomes what users **see in the viewport** after F-011.

## What we will build

### Module: `backend/kernel/occt_bridge.py`

Only this file imports OCCT directly.

| Function | Purpose |
|----------|---------|
| `sketch_rectangle(length, width, plane, mode)` | Rectangular profile (MVP: XY, center mode) |
| `extrude(profile, distance, direction, mode)` | Solid from profile (MVP: +Z, add) |
| `hole_pattern_corners(solid, diameter, offset)` | Four corner holes |
| `export_step(shape, path)` | Write STEP AP203/AP214 |

### Golden mounting plate sequence

1. Sketch 100×50 mm  
2. Extrude 6 mm  
3. Corner holes 6 mm diameter, 8 mm offset  
4. Export STEP  

### Tests (`tests/backend/test_occt_bridge_mounting_plate.py`)

Chain ops, export, verify file exists and is valid STEP (or skip if OCCT not installed).

### Error handling

Invalid dimensions or unsupported plane/direction raise clear `GeometryError` before OCCT runs.

## Acceptance criteria

1. `pythonocc-core` declared in backend dependencies; import works on supported platforms.
2. All four bridge functions implemented; no OCCT imports elsewhere in `backend/`.
3. Golden parameter chain produces non-null shape.
4. `export_step` writes non-empty valid STEP file.
5. Standalone pytest passes (or skips with clear reason on unsupported platforms).
6. No IPC changes — `main.py` still only `ping`.
7. No frontend changes.
8. Mounting plate **not** built via Intent IR executor in F-003.

## Dependencies

- **F-000** — Python backend.
- **F-001** — golden IR params align with bridge parameters (conceptual; no executor yet).

## Out of scope (not in F-003)

- Intent IR execution, step handlers, `kernel_adapter` (F-004).
- JSON-RPC, LLM, project file writes to `exports/`.
- Other MVP ops beyond the three implemented (stubs come in F-004).
- IGES export (F-024), viewport meshes (F-011), assembly mates.
- Problems engine, history, assumptions.

## Notes for reviewers

F-003 is **kernel proof**. If the mounting plate STEP opens in an external viewer, the geometry layer is real.
