# F-009 — Explorer panel (project file tree)

## Summary

Add a **file explorer** on the left side of the app so users can see everything CopilotCAD has created on disk — documents, parts, assemblies, and exports — and open files to read them without leaving the app.

**Status:** Pending approval.

## Why this matters

Today the Explorer column only shows placeholder text. After F-008, chat can compile and execute modeling plans, but users cannot *see* the project files those actions create or update. The explorer makes the workspace tangible: it proves that CopilotCAD is a real local project, not a black box.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Workspace** | The folder on your computer that holds one CopilotCAD project (like a VS Code project folder). |
| **Explorer** | A tree view of folders and files, similar to the file sidebar in VS Code. |
| **IPC** | How the Electron UI talks to the Python backend (messages sent locally between the two processes). |
| **Read-only preview** | Opening a file to view its contents in the UI without editing it directly in the explorer. |

## What the user will experience

1. Open CopilotCAD with a project loaded.
2. See a tree: `docs/`, `parts/`, `assemblies/`, `exports/` at the top level.
3. Expand `parts/<part_name>/` to see `spec.yaml`, `assumptions.yaml`, `history.json` (and `part.cad` when present).
4. Click a file → a preview panel or inline area shows the file contents (YAML/JSON as formatted text).
5. After chat creates or updates files, the tree refreshes so new files appear without restarting the app.

## What we will build

### Backend (Python)

New JSON-RPC methods (names may be finalized during implementation):

- **`list_workspace_tree`** — Returns a nested structure describing folders and files under the active workspace path.
- **`read_workspace_file`** — Returns text contents for a relative path inside the workspace (with safety checks: no paths outside the project).

The backend reads the real filesystem via existing `workspace.py` / project layout conventions from F-002.

### Frontend (Electron + React)

| Piece | Purpose |
|-------|---------|
| `ExplorerPanel.tsx` | Replaces placeholder; hosts the tree and preview |
| `FileTree.tsx` | Renders expandable folder/file nodes |
| IPC bridge + types | `listWorkspaceTree()`, `readWorkspaceFile(path)` |
| `app.css` | Tree indentation, selection highlight, preview pane styling |

### Refresh behavior

- After each successful `execute_intent` from chat, refresh the tree (or subscribe to a simple “workspace changed” signal from the backend).
- Initial load when the app opens a workspace.

## Acceptance criteria

1. Explorer shows the four top-level folders when they exist in the project.
2. Part folders expand to show standard part artifacts (`spec.yaml`, `assumptions.yaml`, `history.json`).
3. Clicking a text file shows its contents in a read-only preview.
4. Tree updates after chat actions that create or modify project files.
5. Attempting to read paths outside the workspace is rejected safely on the backend.
6. No direct file writes from the frontend — explorer is read-only (writes still go through chat → IR → backend).

## Dependencies

- **F-002** — Project folder layout and `copilotcad.json` manifest.
- **F-007** — Electron shell and IPC bridge.
- **F-008** — Chat triggers compile/execute (explorer refresh hooks into that flow).

## Out of scope (not in F-009)

- Editing files in the explorer (double-click to edit).
- Drag-and-drop file organization.
- Opening assemblies in a special viewer (F-018+).
- Git integration or external file watchers beyond simple refresh after actions.

## Notes for reviewers

This feature is **navigation and inspection only**. It does not change how parts are created; it makes existing project structure visible to humans.
