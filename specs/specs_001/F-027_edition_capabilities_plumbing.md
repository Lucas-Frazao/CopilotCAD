# F-027 — Edition and capabilities plumbing

## Summary

Add **edition and capabilities** to the workspace manifest so CopilotCAD knows whether this project is **Community** or a future paid tier — and the UI can **warn** when limits are approached (without hard-blocking MVP).

**Status:** Implemented.

## Why this matters

MVP ships as **Community** with conservative limits (e.g. assembly size). Plumbing now avoids rework when Pro/Team editions add features — UI can adapt early with soft warnings.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Edition** | Product tier label stored in project manifest (`community`, `pro`, `team` — only `community` active in MVP). |
| **Capabilities** | Feature flags and limits — max parts, assemblies enabled, export formats, etc. |
| **`copilotcad.json`** | Workspace manifest file at project root (F-002). |
| **Soft enforcement** | Show warnings in chat or status bar; do not block actions in MVP unless documented. |

## What we will build

### Schema

Extend `WorkspaceManifest` (Pydantic):

```json
{
  "edition": "community",
  "capabilities": {
    "max_parts": 10,
    "max_assembly_parts": 5,
    "assembly_enabled": true,
    "export_step": true,
    "export_iges": true
  }
}
```

Defaults for new projects: `edition: community`, conservative limits matching roadmap deferrals.

### Backend

- `create_workspace` sets default edition and capabilities.
- **`get_workspace_capabilities`** JSON-RPC — returns effective capabilities for active workspace.
- Helper `check_capability(name)` for future hard checks (log warning only in MVP).

### Frontend

- Load capabilities on workspace open.
- Example UI: when assembly has 5 parts, status bar or chat warning “Community limit reached.”
- No hidden feature gates that break core MVP flows without message.

## Acceptance criteria

1. New projects have `edition` and `capabilities` in `copilotcad.json`.
2. Frontend receives capabilities via IPC on load.
3. At least one visible warning when exceeding a documented soft limit (test with fixture).
4. Existing projects without fields get defaults on load (backward compatible).
5. Unit tests for manifest schema and defaults.

## Dependencies

- **F-002** — Workspace manifest.
- **F-007** — IPC to frontend.
- **F-025** — New project sets defaults.

## Out of scope (not in F-027)

- Payment, license keys, or online activation.
- Hard enforcement blocking export or assembly (unless product later requires).
- Team collaboration features.

## Notes for reviewers

This is **foundation for business model**, not a user-facing feature by itself. MVP users should barely notice except optional limit warnings.
