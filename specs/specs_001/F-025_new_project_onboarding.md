# F-025 — New project onboarding

## Summary

When a user creates a **new CopilotCAD project**, open a blank workspace and show the **guided chat opener** — no wizard, no forms — everything starts in conversation.

**Status:** Implemented.

## Why this matters

Product vision promises: launch → chat says *“What to do first? Ask about this CAD model or we can start creating one.”* F-025 ensures **new project flow** matches that vision end-to-end, not only on hardcoded welcome in F-008.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Onboarding** | First-run experience for a new workspace — not a tutorial video, just chat guidance. |
| **Blank workspace** | `copilotcad.json` + empty `docs/`, `parts/`, `assemblies/`, `exports/` folders. |
| **Chat-driven** | User never fills a “New Part” dialog — they describe intent in chat. |

## What the user will experience

1. User chooses “New project” (menu or CLI) → picks folder location.
2. CopilotCAD creates workspace structure on disk.
3. App opens with empty explorer, empty viewport, chat welcome message.
4. User describes first part or asks questions — same flow as existing project.

## What we will build

### Backend

- **`create_workspace(path, project_name)`** exposed via JSON-RPC (may extend F-002 `create_workspace`).
- Return manifest for frontend.

### Frontend

- Menu: File → New Project → folder picker (Electron `dialog.showOpenDialog` or save dialog for new folder).
- IPC `createWorkspace` → load workspace path in app state.
- Reset panels (empty explorer, viewport, problems).
- Show WELCOME chat message (same text as F-008).

### Optional

- File → Open Project for existing `copilotcad.json` folder.

## Acceptance criteria

1. New project creates valid `copilotcad.json` and standard subfolders.
2. Chat shows welcome opener on first load of new project.
3. No modal wizard or multi-step form for onboarding.
4. User can create first part entirely via chat after onboarding.
5. Tests for workspace creation RPC.

## Dependencies

- **F-002** — `create_workspace`.
- **F-007** — Electron menus and IPC.
- **F-008** — Welcome message pattern.

## Out of scope (not in F-025)

- Sample project templates (user may copy `example_project` manually).
- Account signup or cloud project creation.
- Import from other CAD formats on new project.

## Notes for reviewers

F-025 is mostly **product polish and menu wiring** — the philosophy is “chat is the front door.”
