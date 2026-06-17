# F-002 — Project file system (manifest + parts)

## Summary

Implement programmatic creation and loading of CopilotCAD workspaces on disk: root manifest (`copilotcad.json`) with edition and capabilities, standard top-level directories, and stub part folders with empty `spec.yaml`, `assumptions.yaml`, and `history.json`. F-002 makes local-first project layout a tested, schema-backed contract. Assembly YAML, STEP export, and full read/write of part artifacts are deferred.

**Status:** Implemented (scoped subset; see Non-goals).

## Context and goals

CopilotCAD projects are folders on disk (`docs/product_vision.md`, `docs/architecture.md`). The backend owns all file writes; the frontend never writes project files directly. F-002 establishes the first backend APIs for workspace and part-folder scaffolding so later features (IR execution, explorer panel, golden path) can assume a consistent tree.

Goals:

- Define `WorkspaceManifest` and `Capabilities` Pydantic models matching `docs/architecture.md` edition/capabilities example.
- Implement `create_workspace(path, project_name)` to create directory layout and default manifest.
- Implement `load_workspace(path)` to read and validate `copilotcad.json`.
- Implement `create_part_folder(workspace, part_id)` to create `parts/<part-id>/` with stub artifacts.
- Raise clear, typed errors for missing or invalid manifests.
- Unit test create/load workspace and part folder creation.

## Non-goals

- `assembly_folder.py` — create/read assembly YAML (deferred; roadmap mentions in broader F-002 but not this delivery).
- `export.py` — STEP/IGES export via pythonOCC (F-003/F-024).
- Creating `part.cad`, `interfaces/`, or populated PDD content in part folders.
- Reading or updating `spec.yaml` / `assumptions.yaml` / `history.json` after creation (full read/write deferred).
- IPC methods `project.new` / `project.open` (F-007+).
- Enforcing `capabilities` limits (e.g. max assembly parts) at runtime (F-027 / future).
- Cloud sync, templates, or migration of existing projects.
- Updating `example_project/` in the repo (may remain illustrative stubs separate from API tests).

## Requirements

### Workspace manifest schema

- Location: `backend/schemas/workspace_manifest.py`.
- Models: `Capabilities`, `WorkspaceManifest`.
- Pydantic v2 strict mode (`extra="forbid", strict=True`).
- Helper: `default_capabilities()` returning community defaults.

### Workspace module

- Location: `backend/project/workspace.py`.
- Constants: `MANIFEST_FILENAME = "copilotcad.json"`, `WORKSPACE_DIRS = ("docs", "parts", "assemblies", "exports")`.
- Exceptions:
  - `WorkspaceError` (base)
  - `WorkspaceNotFoundError` — missing path or manifest
  - `WorkspaceInvalidError` — invalid JSON or schema

#### `create_workspace(path: Path, project_name: str) -> WorkspaceManifest`

Must:

1. Create `path` if it does not exist (`mkdir(parents=True)`).
2. Create empty directories: `docs/`, `parts/`, `assemblies/`, `exports/` under `path`.
3. Write `copilotcad.json` with:
   - `project_name` = argument value
   - `version` = `"0.1"`
   - `edition` = `"community"`
   - `capabilities` = default community capabilities (see Data model).
4. Return the in-memory `WorkspaceManifest` instance written to disk.

#### `load_workspace(path: Path) -> WorkspaceManifest`

Must:

1. Require `path` to be an existing directory; otherwise raise `WorkspaceNotFoundError`.
2. Require `path/copilotcad.json` to exist; otherwise raise `WorkspaceNotFoundError` with message indicating missing manifest.
3. Parse JSON; on decode error raise `WorkspaceInvalidError`.
4. Validate with `WorkspaceManifest.model_validate`; on failure raise `WorkspaceInvalidError` including path context.
5. Return validated `WorkspaceManifest`.

### Part folder module

- Location: `backend/project/part_folder.py`.
- Constants: `PARTS_DIR = "parts"`, `SPEC_FILENAME = "spec.yaml"`, `ASSUMPTIONS_FILENAME = "assumptions.yaml"`, `HISTORY_FILENAME = "history.json"`.

#### `create_part_folder(workspace: Path, part_id: str) -> Path`

Must:

1. Create `workspace/parts/<part_id>/` (`mkdir(parents=True)`).
2. Write stub files:
   - `spec.yaml` — empty YAML mapping `{}` (or equivalent empty document).
   - `assumptions.yaml` — `assumptions: []`
   - `history.json` — `{"events": []}` as JSON (not YAML).
3. Return the `Path` to the part folder.

Must not create `part.cad`, `interfaces/`, or other files in F-002.

### Unit tests

| File | Coverage |
|------|----------|
| `tests/backend/test_workspace_manifest.py` | `create_workspace` creates dirs and manifest; `load_workspace` round-trip; missing manifest; invalid JSON; invalid schema |
| `tests/backend/test_part_folder.py` | `create_part_folder` creates three stub files with expected empty content |

Tests use temporary directories (`tmp_path`); they must not depend on `example_project/`.

## Data model and contracts

### `copilotcad.json` (workspace manifest)

Written by `create_workspace` and validated by `load_workspace`:

```json
{
  "project_name": "<string>",
  "version": "0.1",
  "edition": "community",
  "capabilities": {
    "max_assembly_parts": 5,
    "advanced_pdd": false,
    "scripting": false,
    "plugin_marketplace": false
  }
}
```

### `Capabilities` fields

| Field | Type | Default |
|-------|------|---------|
| `max_assembly_parts` | int | `5` |
| `advanced_pdd` | bool | `false` |
| `scripting` | bool | `false` |
| `plugin_marketplace` | bool | `false` |

### `WorkspaceManifest` fields

| Field | Type | Default |
|-------|------|---------|
| `project_name` | string | required |
| `version` | string | `"0.1"` |
| `edition` | `community` \| `pro` \| `team` | `community` |
| `capabilities` | `Capabilities` | default community capabilities |

### Workspace directory layout (after `create_workspace`)

```
<workspace>/
├── copilotcad.json
├── docs/
├── parts/
├── assemblies/
└── exports/
```

### Part folder layout (after `create_part_folder`)

```
<workspace>/parts/<part_id>/
├── spec.yaml          # {}
├── assumptions.yaml   # assumptions: []
└── history.json       # {"events": []}
```

### Error contracts

| Condition | Exception | User-visible message pattern |
|-----------|-----------|------------------------------|
| Workspace path not a directory | `WorkspaceNotFoundError` | `Workspace path does not exist` |
| No `copilotcad.json` | `WorkspaceNotFoundError` | `Missing workspace manifest` |
| Invalid JSON in manifest | `WorkspaceInvalidError` | `Invalid JSON in workspace manifest` |
| Schema validation failure | `WorkspaceInvalidError` | `Invalid workspace manifest` |

## Acceptance criteria

1. **Schema:** `WorkspaceManifest` and `Capabilities` validate the architecture example JSON; unknown fields are rejected.
2. **Create workspace:** Calling `create_workspace(tmp_path / "proj", "proj")` creates all four top-level dirs and `copilotcad.json` with `edition: community` and default capabilities.
3. **Load workspace:** `load_workspace` on a workspace created by `create_workspace` returns a manifest with matching `project_name` and `edition`.
4. **Missing manifest:** `load_workspace` on a directory without `copilotcad.json` raises `WorkspaceNotFoundError`.
5. **Invalid manifest:** Malformed JSON or JSON missing `project_name` raises `WorkspaceInvalidError`.
6. **Create part folder:** `create_part_folder(workspace, "mounting_plate")` creates `parts/mounting_plate/` with `spec.yaml`, `assumptions.yaml`, and `history.json` containing empty/stub content as specified.
7. **Tests pass:** `pytest` for `test_workspace_manifest.py` and `test_part_folder.py` reports all tests green.
8. **Scope boundary:** No assembly YAML helpers, no STEP export, no IPC changes, and no `part.cad` creation in F-002.
