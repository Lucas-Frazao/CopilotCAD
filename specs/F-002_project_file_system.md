# F-002 — Project file system

## Summary

Implement how CopilotCAD **creates and loads projects on disk**: workspace manifest (`copilotcad.json`), standard folders (`docs/`, `parts/`, etc.), and stub **part folders** with empty spec, assumptions, and history files.

**Status:** Implemented.

## Why this matters

CopilotCAD is **local-first** — your project lives in a folder you own. F-002 defines that folder layout so explorer, chat, and export features all agree on where files live. The backend owns all writes; the UI never edits project files directly.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Workspace** | One project folder on disk with `copilotcad.json` at the root. |
| **Manifest** | `copilotcad.json` — metadata: project name, version, edition, capabilities. |
| **Part folder** | `parts/<part_id>/` — holds everything for one engineering part. |
| **spec.yaml** | Part specification document (purpose, interfaces, constraints — PDD). |
| **assumptions.yaml** | List of inferred or confirmed assumptions for the part. |
| **history.json** | Log of actions and changes for the part. |
| **Edition / capabilities** | Product tier and feature limits (Community defaults in F-002). |

## What the user will experience

F-002 is **backend-only** for users. After later features wire it up:

- New projects get a sensible folder tree automatically.
- Each new part gets a folder with starter files — not an empty void.

Developers can call `create_workspace` and `create_part_folder` in Python tests and see files appear on disk.

## What we will build

### Workspace manifest (`backend/schemas/workspace_manifest.py`)

- `WorkspaceManifest`, `Capabilities` models (strict Pydantic).
- Defaults: `edition: community`, conservative capability limits.

### Workspace module (`backend/project/workspace.py`)

- `create_workspace(path, project_name)` — creates dirs + writes `copilotcad.json`.
- `load_workspace(path)` — read and validate manifest.
- Typed errors: `WorkspaceNotFoundError`, `WorkspaceInvalidError`.

### Layout after `create_workspace`

```
<workspace>/
├── copilotcad.json
├── docs/
├── parts/
├── assemblies/
└── exports/
```

### Part folder module (`backend/project/part_folder.py`)

- `create_part_folder(workspace, part_id)` — creates:
  - `spec.yaml` — `{}`
  - `assumptions.yaml` — `assumptions: []`
  - `history.json` — `{"events": []}`

### Tests

- `test_workspace_manifest.py` — create, load, missing manifest, invalid JSON/schema.
- `test_part_folder.py` — stub files created with expected empty content.

## Acceptance criteria

1. `create_workspace` creates four top-level dirs and valid `copilotcad.json`.
2. `load_workspace` round-trips manifest data.
3. Missing or invalid manifest raises typed errors.
4. `create_part_folder` creates three stub files under `parts/<id>/`.
5. Pytest passes for workspace and part folder tests.
6. No assembly YAML helpers, STEP export, IPC, or `part.cad` in F-002.

## Dependencies

- **F-000** — repo layout and Python backend.

## Out of scope (not in F-002)

- Assembly YAML read/write (later phases).
- STEP/IGES export (`export.py` — F-003/F-024).
- Populated PDD content or reading/updating specs after creation.
- IPC `project.new` / `project.open` (F-007+).
- Runtime enforcement of capability limits (F-027).
- Updating `example_project/` in repo (may stay illustrative).

## Notes for reviewers

F-002 is the **on-disk contract** for local-first CAD. Everything that “creates a part” later should use these helpers.
