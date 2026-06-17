# F-024 — STEP/IGES export polish

## Summary

Make **export reliable and visible**: user can export any part or assembly to **STEP or IGES** via chat or `/export`, files land in `exports/`, and the action appears in history.

**Status:** Pending approval.

## Why this matters

MVP success includes exporting to standard CAD formats for manufacturing or sharing. F-002 stubbed export; F-024 makes it a **complete user-facing flow** with clear feedback.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **STEP** | Common 3D exchange format (.step / .stp) — most CAM and CAD tools read it. |
| **IGES** | Older exchange format (.iges / .igs) — still used in some shops. |
| **`exports/`** | Project folder where CopilotCAD writes exported files. |
| **Export IR** | Intent type `export` or dedicated export RPC after geometry exists. |

## What the user will experience

1. User says “Export the mounting plate as STEP” or types `/export`.
2. Chat confirms file path: `exports/mounting_plate.step`.
3. Explorer shows new file under `exports/`.
4. History logs the export action.
5. Export failure (no geometry) shows clear error + suggested fix in chat.

## What we will build

### Backend

- Polish `export.py` for single parts and assemblies (compound shape from F-019/F-020).
- Support STEP and IGES via OCCT writers.
- **`export_part(part_id, format)`** and **`export_assembly(assembly_id, format)`** JSON-RPC.
- Wire `/export` slash handler (F-014) to same module.
- Optional `export` Intent IR type execution path.

### Frontend

- Chat success message with clickable path (opens in explorer).
- Explorer refresh on export.

## Acceptance criteria

1. Golden plate exports valid STEP openable in external viewer (or OCCT read-back test).
2. Assembly export produces single file with all instances (MVP: positioned compound).
3. IGES export works for same geometry.
4. Export without geometry fails gracefully with problems/errors.
5. History entry created per export.

## Dependencies

- **F-003** — OCCT export bridge.
- **F-012** — Golden path part exists.
- **F-014** — `/export` command.
- **F-017** — History logging.
- **F-020** — Assembly geometry for assembly export.

## Out of scope (not in F-024)

- STL, 3MF, or other formats.
- Cloud upload or email.
- Batch export all parts in one click (unless trivial).

## Notes for reviewers

Export is the **handoff to the real world** — file must be valid, path predictable, and traceable in history.
