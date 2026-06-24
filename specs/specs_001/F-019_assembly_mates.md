# F-019 — Assembly mates

## Summary

Implement **mates** — rules that define how two parts in an assembly fit together (coincident faces, concentric holes, fixed offsets) — in the geometry kernel and execution engine.

**Status:** Implemented.

## Why this matters

An assembly YAML listing parts is not enough; parts must be **positioned** relative to each other. Mates are the CAD equivalent of “bolt these faces together” or “align these holes.”

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Mate** | A constraint between two parts in an assembly (fix, coincident, concentric, distance). |
| **Mate step** | An Intent IR modeling step with ops like `mate_fix`, `mate_coincident`, `mate_concentric`, `mate_distance`. |
| **Invalid mate** | Mate references missing geometry or incompatible faces — surfaces as a Problem (F-006). |
| **OCCT assembly** | Open CASCADE’s way of building compound shapes with transforms and constraints. |

## Mate types (MVP)

| Op | Plain meaning |
|----|----------------|
| `mate_fix` | Lock a part’s position (no movement). |
| `mate_coincident` | Two faces/planes touch and align. |
| `mate_concentric` | Two cylindrical features share an axis. |
| `mate_distance` | Keep parts separated by a fixed distance along an axis. |

## What the user will experience

1. User describes mating in chat: “Mount the plate flush to the bracket face.”
2. IR includes mate steps referencing part instances and faces (by id from selection or inferred).
3. Execution applies mates in OCCT assembly model.
4. Invalid mates show as problems — not silent failure.

## What we will build

### Backend

- Step handlers in `engine/step_handlers/` for each mate op.
- `kernel_adapter` + `occt_bridge` assembly support.
- Validate mate params: target instance ids, mate type, references to geometry ids where required.
- `invalid_mate` problem when params or geometry missing.

### Tests

- 2-part assembly with at least one coincident or fix mate executes without error.
- Deliberately bad mate triggers `invalid_mate` problem.

## Acceptance criteria

1. All four mate ops registered in handler registry.
2. Valid 2-part assembly with mates produces positioned compound shape.
3. Invalid mates fail with structured problems, not crashes.
4. Mate steps appear in history (F-017) and chat diff (F-008).

## Dependencies

- **F-018** — Assembly exists with instances.
- **F-003 / F-004** — Kernel and executor.
- **F-006** — `invalid_mate` problem type.

## Out of scope (not in F-019)

- Viewport rendering of mated assembly (F-020).
- Interactive mate picking in 3D (selection ids may be stubbed).
- Physics simulation or collision analysis.

## Notes for reviewers

Mates are **precision geometry constraints** — this is where assembly IR meets the kernel. Expect iterative tuning with OCCT.
