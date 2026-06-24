# F-016 — Interfaces panel

## Summary

Add an **Interfaces panel** listing every **interface** defined across the project — connection points between parts (mounting faces, bolt patterns, electrical ports) — with status: open, linked, or verified.

**Status:** Implemented.

## Why this matters

Hardware is built from **connections**, not isolated shapes. Interfaces document how parts mate and connect. Surfacing them helps users spot missing links before assembly work (Phase 3).

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Interface** | A defined connection on a part — e.g. “M3 bolt pattern on top face”, “USB-C port cutout”. Stored in part `spec.yaml`. |
| **Open** | Interface defined but not linked to another part’s interface. |
| **Linked** | Two interfaces reference each other across parts. |
| **Verified** | Linked and checked (mate or manual confirmation) — MVP may stub verification. |
| **Interface conflict** | Two definitions clash (problem type from F-006). |

## What the user will experience

1. “Interfaces” tab lists all interfaces from all parts.
2. Columns: part id, interface id/name, type, status, connected part (if any).
3. Interface conflict problems (F-010) link here — click highlights the row.
4. Click row → open part in explorer / set active part.

## What we will build

### Backend

- **`list_interfaces`** — Aggregate `interfaces` sections from all `parts/*/spec.yaml`.
- Status computation: parse `connects_to` fields and assembly YAML when available (F-021 extends linking).

### Frontend

| Piece | Purpose |
|-------|---------|
| `InterfacesPanel.tsx` | Replaces placeholder |
| Status badges | open / linked / verified |
| Link from Problems panel | `interface_conflict` → scroll/select row |

## Acceptance criteria

1. Interfaces from example `mounting_plate` spec appear when defined.
2. Status reflects linked vs open based on spec content.
3. Panel updates when specs change via chat or slash commands.
4. Empty state when no interfaces defined.

## Dependencies

- **F-002** — spec.yaml structure.
- **F-010** — Problem cross-links.
- **F-021** — Full cross-part linking logic (panel can ship with simpler status first).

## Out of scope (not in F-016)

- Creating interfaces from the panel (chat or `/interface` command).
- 3D highlighting of interface geometry in viewport (future).
- Full verification workflow.

## Notes for reviewers

Interfaces are **engineering metadata** — the panel makes PDD visible without reading YAML by hand.
