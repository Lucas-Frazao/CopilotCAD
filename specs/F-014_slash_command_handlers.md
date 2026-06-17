# F-014 — Slash command handlers

## Summary

Make the **12 MVP slash commands** actually work: typing `/vision`, `/part`, `/export`, etc. in chat creates or updates the correct project documents and artifacts through the backend — not just the picker UI from F-008.

**Status:** Pending approval.

## Why this matters

Slash commands are CopilotCAD’s **structured shortcuts** for PDD workflows. Without handlers, users see “handler not implemented” (F-008). F-014 turns commands into real project files on disk.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Slash command** | Text starting with `/` in chat (e.g. `/part motor_mount`) — like slash commands in Slack or Discord. |
| **Scaffold** | Create a starter file from a template with placeholders, not a finished engineering doc. |
| **Intent IR** | The strict JSON plan the backend executes; slash commands may compile to IR or direct file ops via controlled backend handlers. |

## The 12 MVP commands

| Command | What it should do (plain language) |
|---------|-----------------------------------|
| `/vision` | Create or open starter `docs/product_vision.md` from template. |
| `/constitution` | Scaffold `docs/constitution.md` (engineering principles). |
| `/architecture` | Scaffold `docs/system_architecture.md`. |
| `/manufacturing` | Scaffold `docs/manufacturing_stack.md`. |
| `/part <id>` | Create new part folder under `parts/<id>/` with `spec.yaml`, `assumptions.yaml`, `history.json`. |
| `/interface` | Define or scaffold an interface object in the active part spec. |
| `/plan` | Create or update `plan.md` for the active part. |
| `/review` | Run or scaffold a review checklist for the active part. |
| `/release` | Set part maturity to “released” in spec metadata. |
| `/export` | Export current part or assembly to STEP/IGES in `exports/`. |
| `/assumptions` | Show and manage assumptions for current part (list in chat; confirm in F-023). |
| `/history` | Show action history for current part in chat or open history panel context. |

## What we will build

### Backend

- **`handle_slash_command(command, args, context)`** JSON-RPC or branch inside compile pipeline.
- Each command maps to allowed file operations via existing `workspace.py`, `part_folder.py`, `export.py` — **never** raw frontend writes.
- Return structured result: files created, summary message for chat, optional IR to execute.

### Frontend

- Replace F-008 “handler not implemented” path with real execution.
- Chat shows success/failure summary and refreshes explorer (F-009).

### Templates

- Markdown/YAML templates under `backend/templates/` or `docs/templates/` for scaffolded docs.

## Acceptance criteria

1. Each of the 12 commands produces the correct artifact(s) on disk when run in a valid workspace.
2. Invalid args return clear errors in chat (e.g. `/part` without name).
3. Commands do not bypass Intent IR for geometry-changing ops — `/export` uses export module; `/part` creates folders only until user models via chat.
4. Explorer refreshes after command completes.
5. Unit tests per command for file side effects.

## Dependencies

- **F-002** — Project file system.
- **F-008** — Slash picker and slash-only message detection.
- **F-009** — Explorer refresh visibility.
- **F-024** — `/export` may share polish with export flow.

## Out of scope (not in F-014)

- Custom user-defined slash commands.
- Slash commands that edit arbitrary file paths outside allowed templates.
- Full assumption confirm/reject UI (F-023).

## Notes for reviewers

Slash commands are **power tools for structured authoring** — they must stay on the “backend writes files” rule, same as chat.
