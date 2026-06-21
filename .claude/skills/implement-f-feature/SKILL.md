---
name: implement-f-feature
description: >-
  Implements a CopilotCAD F-0xx feature using spec-driven development. Reads
  specs/specs_001/F-0xx_*.md and docs, sets feature scope, implements only what the spec
  allows, runs backend tests, and updates spec status. Use when the user asks to
  implement F-000, F-001, F-003, or any F-0xx feature after spec approval.
---

# Implement F-Feature (CopilotCAD)

## Prerequisites

- User has approved the spec for this feature (or explicitly asked to implement).
- Spec exists at `specs/specs_001/F-<id>_<name>.md`.

## Workflow

Copy and track:

```text
- [ ] Read specs/specs_001/F-0xx_*.md (full contract)
- [ ] Read matching section in docs/Docs_001/feature_roadmap_001.md
- [ ] Read relevant docs/Docs_001/architecture_001.md sections (do not edit unless asked)
- [ ] Set .cursor/feature-scope.json for this feature
- [ ] Implement only files/requirements in the spec
- [ ] Run verify-backend and/or verify-frontend (match the stack you changed)
- [ ] Update spec Status to Implemented when acceptance criteria pass
```

## Step 1 — Load contract

1. Find `specs/specs_001/F-<id>_*.md`.
2. Read Summary, Requirements, Data model, Acceptance criteria, Non-goals.
3. If spec conflicts with roadmap/architecture, STOP and report conflict.

## Step 2 — Set feature scope

Edit `.cursor/feature-scope.json`:

```json
{
  "feature": "F-004",
  "allowed_prefixes": [
    "backend/engine/",
    "backend/kernel/",
    "tests/backend/",
    "specs/specs_001/"
  ],
  "blocked_prefixes": ["docs/Docs_001/feature_roadmap_001.md", "docs/Docs_001/architecture_001.md"],
  "notes": "Backend-only feature; no frontend/IPC unless spec requires."
}
```

Adjust `allowed_prefixes` to match the spec Non-goals (e.g. omit `frontend/` for backend-only features).

## Step 3 — Implement

Architecture boundaries (always):

- OCCT imports only in `backend/kernel/occt_bridge.py`.
- Frontend never writes project files; backend owns filesystem.
- No new JSON-RPC methods unless the feature spec requires IPC changes.
- Do not edit `docs/Docs_001/feature_roadmap_001.md` or `docs/Docs_001/architecture_001.md` unless user explicitly asked.

Match existing code style in surrounding modules.

## Step 4 — Verify

Run the verify skill(s) matching what the feature changed:

- **Backend changes** → `verify-backend`
  (`.cursor/skills/verify-backend/scripts/verify-backend.ps1`, or the `.sh` on macOS/Linux).
- **Frontend changes** → `verify-frontend`
  (`.cursor/skills/verify-frontend/scripts/verify-frontend.ps1`, or the `.sh` on macOS/Linux).

Run both for a dual-stack feature. Or ask the user to run `/verify-backend` and/or
`/verify-frontend`.

## Step 5 — Close out

- Update spec `**Status:**` line when all acceptance criteria met.
- Summarize files changed and pytest result.
- Do not start the next F-0xx without user confirmation.

## Examples

**User:** "Implement F-004 per the approved spec."

1. Read `specs/specs_001/F-004_*.md`
2. Set feature-scope for `backend/engine/`, `tests/backend/`
3. Implement executor + handlers per spec only
4. Run verify-backend
5. Update spec status
