# F-011 — Three.js viewport (basic 3D view)

## Summary

Add a **3D viewport** in the center of the app where users can **see** the parts CopilotCAD generates, rotate/zoom the model, and **click faces** to send selection context back to chat.

**Status:** Implemented.

## Why this matters

Chat and file trees describe parts in text. A viewport makes geometry **visible** — the core promise of a CAD tool. Selection also enables “fix this face” or “add a hole here” workflows later.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Three.js** | A JavaScript library for drawing 3D graphics in the browser/Electron renderer. |
| **Mesh** | A 3D surface made of triangles that approximates a solid shape. |
| **Tessellation** | Converting precise CAD geometry (B-rep from Open CASCADE) into triangles for display. |
| **TopoDS / OCCT** | Open CASCADE Technology — the precise geometry kernel in the Python backend. |
| **Orbit / pan / zoom** | Standard 3D navigation: rotate around the model, move the view, zoom in/out. |
| **Selection ID** | An identifier for a face or edge so chat knows what you clicked. |

## What the user will experience

1. After chat creates a part, a 3D model appears in the center panel.
2. Mouse drag rotates the view; scroll zooms; middle-click or modifier pans (standard conventions).
3. Click a face → it highlights; selection is stored as context for the next chat message.
4. If geometry fails to generate, viewport shows empty state with a short explanation (problems panel has details).

## What we will build

### Backend

New JSON-RPC method(s):

- **`get_part_mesh`** (or mesh bundled in execute response) — After geometry updates, return tessellated mesh data: vertices, normals, face indices, optional face-id map for picking.

Mesh generation path: OCCT shape → tessellate in `occt_bridge` or dedicated export helper → JSON-friendly arrays.

### Frontend

| Piece | Purpose |
|-------|---------|
| `ViewportPanel.tsx` | Three.js scene, camera, lights, renderer |
| Orbit controls | `@react-three/fiber` or manual Three.js controls |
| Picking | Raycast on click → face id → store in app context |
| IPC types | Mesh payload TypeScript interfaces |

### Integration

- After successful `executeIntent`, if `final_step_id` exists, request mesh for active part.
- Viewport subscribes to “geometry updated” events from shared store.

## Acceptance criteria

1. A generated mounting plate (golden example) renders as a visible solid in the viewport.
2. User can orbit, pan, and zoom without breaking the renderer.
3. Clicking a face highlights it and records selection for chat context.
4. Viewport clears or shows placeholder when no geometry exists.
5. Mesh updates when chat produces new geometry for the active part.

## Dependencies

- **F-003 / F-004** — OCCT geometry and step execution produce shapes.
- **F-007** — Electron renderer hosts Three.js.
- **F-008** — Chat triggers execution that produces geometry.

## Out of scope (not in F-011)

- Multiple parts in one view (F-020 assembly viewport).
- Materials, textures, or realistic rendering.
- OCCT WASM in the renderer (backend tessellation only for MVP).
- Dimension annotations or measurement tools.
- Export from viewport (F-024).

## Notes for reviewers

The viewport is **read-only for geometry** — users do not sketch directly in 3D in MVP. All modeling still goes through chat → Intent IR → backend.
