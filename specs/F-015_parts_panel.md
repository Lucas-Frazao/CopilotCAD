# F-015 — Parts panel

## Summary

Add a **Parts panel** listing every part in the project with name, maturity status, and open problem count — click a part to focus it in the explorer and viewport.

**Status:** Pending approval.

## Why this matters

As projects grow beyond one part, users need a **part-centric view** (not only a file tree). The Parts panel is the “inventory of engineering objects” CopilotCAD cares about.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Part** | A first-class engineering object: folder under `parts/<id>/` with spec, assumptions, history, and geometry. |
| **Maturity status** | Lifecycle label in spec (e.g. draft, in review, released) — indicates how “done” a part is. |
| **Active part** | The part currently selected for chat context, viewport, and history. |

## What the user will experience

1. Left sidebar tab “Parts” shows a list of all parts.
2. Each row: part id/name, maturity badge, count of open problems.
3. Click a part → explorer expands that folder, viewport loads its geometry, chat context switches `active_part_id`.

## What we will build

### Backend

- **`list_parts`** — Read workspace manifest + each `parts/*/spec.yaml` for id, display name, maturity, problem counts (problems from last evaluation or lightweight re-scan).

### Frontend

| Piece | Purpose |
|-------|---------|
| `PartsPanel.tsx` | Replaces placeholder |
| Shared `activePartId` in app store |
| Click handler | Updates explorer selection, triggers mesh load, sets chat context |

## Acceptance criteria

1. All folders under `parts/` with valid `spec.yaml` appear in the list.
2. Maturity and problem count match backend state after chat actions.
3. Selecting a part updates explorer and viewport (when geometry exists).
4. Empty project shows helpful empty state (“No parts yet — describe one in chat or use /part”).

## Dependencies

- **F-002** — Part folders and spec.yaml.
- **F-006 / F-010** — Problem counts.
- **F-009** — Explorer navigation.
- **F-011** — Viewport load on selection.

## Out of scope (not in F-015)

- Creating parts from the panel (use chat or `/part`).
- Drag reorder, duplicate, delete from panel (delete via chat + F-022 approval later).
- Assembly instances list (F-018).

## Notes for reviewers

Parts panel is **navigation**, not a second write path. It mirrors disk state the backend already owns.
