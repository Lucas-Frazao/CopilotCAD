# F-018 — Assembly creation

## Summary

Let users **create assemblies via chat** — combinations of multiple parts in one mechanical design — with assembly files on disk and visibility in the explorer.

**Status:** Implemented.

## Why this matters

Real hardware is rarely one part. Assembly support is required for CopilotCAD to handle “small hardware concepts” from the MVP definition — motor + bracket + plate, etc.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Assembly** | A collection of part **instances** (references to parts) arranged together — stored as `assemblies/<id>.yaml`. |
| **Part instance** | One usage of a part in an assembly (same part file can appear twice with different transforms). |
| **`asm_create`** | Intent IR type for “create this assembly” requests. |
| **Scaffold** | Create placeholder part folders if referenced parts don’t exist yet. |

## What the user will experience

1. User says: “Create an assembly with a mounting plate and a standoff bracket.”
2. Chat compiles to `assembly_create` Intent IR with instance list.
3. Backend creates `assemblies/<id>.yaml` and scaffolds missing part folders.
4. Explorer shows `assemblies/` node; Parts panel lists instances’ parts.

## What we will build

### Backend

- Implement **`assembly_create`** execution in executor (or dedicated assembly module).
- **`assembly_folder.py`** — create/read assembly YAML (extend F-002).
- Assembly YAML MVP fields: `id`, `name`, `instances[]` with `part_id`, optional `transform`, optional `instance_id`.
- Scaffold part folders via `create_part_folder` when `part_id` missing.

### Intent IR

- Validate `assembly_create` type with `target.assembly_id` and steps or instance list in IR (align with F-001 schema extensions).

### Frontend

- Explorer shows assemblies folder entries.
- Parts panel may show “in assembly X” badge (optional MVP).

## Acceptance criteria

1. Chat can create a 2-part assembly YAML via execute path.
2. Missing part folders are created with default spec stubs.
3. Explorer lists the assembly file.
4. Unit tests for assembly YAML read/write and execute path.
5. Problems engine flags basic assembly issues (interface stubs from F-006).

## Dependencies

- **F-001** — IR types for `assembly_create`.
- **F-002** — Workspace and part folders.
- **F-004** — Executor extension.
- **F-009** — Explorer display.

## Out of scope (not in F-018)

- Mates and 3D positioning (F-019, F-020).
- Interface auto-linking (F-021).
- Large assemblies (>5 parts — deferred per roadmap).

## Notes for reviewers

F-018 creates **structure on disk** — parts exist and are listed together. Physical positioning comes next.
