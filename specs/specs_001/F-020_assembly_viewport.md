# F-020 — Assembly viewport

## Summary

Extend the 3D viewport to **show entire assemblies** — multiple parts in correct relative positions — with an assembly tree and per-instance selection for chat context.

**Status:** Pending approval.

## Why this matters

F-011 shows one part. Users assembling hardware need to **see the full mechanism** — plate + bracket + standoffs — not each piece in isolation.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Assembly viewport** | 3D view rendering all instances with transforms from mates (F-019). |
| **Instance selection** | Click one part in the assembly → chat knows which instance you mean. |
| **Assembly tree** | UI list of instances in the viewport or sidebar (hierarchy of parts in the assembly). |

## What the user will experience

1. Open or create an assembly → viewport shows all parts positioned per mates.
2. Assembly tree lists instances (names from part specs).
3. Click an instance → highlights in viewport; sets chat context to that instance/part.
4. Orbit/pan/zoom works for the full assembly bounds.

## What we will build

### Backend

- **`get_assembly_mesh(assembly_id)`** — Tessellate each instance mesh with world transform; return array of meshes with `instance_id`, `part_id`, face id maps.

### Frontend

- Viewport loads multiple meshes with transforms.
- Assembly tree component (in viewport overlay or ViewportPanel sidebar).
- Selection passes `instance_id` + `part_id` + optional `face_id` to chat context store.

## Acceptance criteria

1. 2-part mated assembly (F-019) renders with correct relative placement.
2. User can select individual instances.
3. Selection context available for next chat message compile `context`.
4. Single-part mode still works when no assembly active.
5. Performance acceptable for ≤5 parts (MVP limit).

## Dependencies

- **F-011** — Base viewport and Three.js setup.
- **F-019** — Mated assembly geometry.
- **F-018** — Assembly YAML and instances.

## Out of scope (not in F-020)

- Exploded view animation.
- Section cuts or clipping planes.
- Assembly-level export UI (F-024).

## Notes for reviewers

This feature connects **spatial assembly data** to the same viewport users already learned in F-011.
