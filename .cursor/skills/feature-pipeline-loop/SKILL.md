---
name: feature-pipeline-loop
description: >-
  Orchestrates CopilotCAD spec-driven development: find the next F-0xx from the
  roadmap build order, draft its spec, get approval, implement via implement-f-feature,
  then repeat. Use when the user wants to automate the feature pipeline or run
  "next feature" until blocked or done.
---

# Feature pipeline loop (CopilotCAD)

Runs **one feature per iteration** (recommended). Repeat by re-invoking or using `/loop`.

## Build order (do not skip phases)

Read `docs/Docs_001/feature_roadmap_001.md` — **Build order summary** at the bottom.

```
Phase 0: F-000 → F-001 → F-002 → F-003 → F-004
Phase 1: F-005 → F-006 → F-007 → … → F-012
Phase 2: F-013 → … → F-017
Phase 3: F-018 → … → F-021
Phase 4: F-022 → … → F-026
```

(F-027 is listed separately in the roadmap; treat after F-026 unless user reorders.)

## Step 0 — Preconditions

- Working on the correct git branch (feature branch per F-0xx or agreed integration branch).
- Backend venv exists; run verify-backend when touching backend code.
- **F-005+** needs `ANTHROPIC_API_KEY` in environment; stop loop and report if missing.
- **F-007+** needs frontend deps (`npm install` in `frontend/`); stop if broken.
- OCCT tests may skip on Windows ARM — not a loop blocker for non-geometry features.

## Step 1 — Find next feature

1. List `specs/specs_001/F-*.md` and read each `**Status:**` line.
2. Walk build order; the **first** id that is not `Implemented` is `next`.
3. If no spec file exists for `next`, it still counts — spec must be written first.
4. If user named a stop id (e.g. "through F-004"), stop after that id is Implemented.

**Current typical state:** F-000–F-003 Implemented → **next is F-004**.

## Step 2 — Draft spec (if missing or not approved)

1. Read the F-id section in `docs/Docs_001/feature_roadmap_001.md` (do not edit roadmap).
2. Read `docs/Docs_001/architecture_001.md` sections for IPC, kernel, filesystem, frontend boundaries.
3. Read prior specs for data models and dependencies.
4. Create `specs/specs_001/F-<id>_<short_name>.md` matching existing spec structure:

   - Summary (include `**Status:** Draft` or `Pending approval`)
   - Context and goals
   - Non-goals (explicit boundaries — critical for dual-stack)
   - Requirements (testable)
   - Data model / modules (if applicable)
   - Acceptance criteria (checkboxes or numbered, each testable)
   - Dependencies on other F-ids

5. Run mental **spec-reviewer** checklist (or invoke `/spec-reviewer` on the draft).

## Step 3 — Approval gate (required by default)

**Do not implement** until the user approves the spec.

Present:

- Feature id and one-paragraph summary
- Non-goals highlights
- Acceptance criteria count
- Ask: **"Approve spec and implement F-0xx?"**

If the user said **unattended / auto-approve**, skip the ask only for that session and note auto-approve in the commit message.

## Step 4 — Implement (implement-f-feature)

Follow `.cursor/skills/implement-f-feature/SKILL.md`:

1. Set `.cursor/feature-scope.json` from spec Non-goals.
2. Implement only what the spec allows.
3. Run `.cursor/skills/verify-backend/scripts/verify-backend.ps1` (and frontend tests if spec requires).
4. Update spec `**Status:**` to `Implemented` when acceptance criteria pass.
5. Clear scope: `feature: null`, `allowed_prefixes: []`.

## Step 5 — Repeat or stop

**Stop and report** when:

- Stop id reached and Implemented
- Spec CONFLICT with architecture (user must resolve)
- Missing credentials / env (F-005 API key, etc.)
- pytest or required tests fail after fix attempt
- User cancels

**Continue** when:

- User says "next feature" or loop tick fires
- More ids remain in scope

Start again at Step 1.

## One iteration prompt (copy-paste)

```text
Run feature-pipeline-loop for one iteration: find next unimplemented F-0xx,
draft spec if needed, show me for approval, then implement after I approve.
Stop at F-004 unless I say otherwise.
```

## Unattended prompt (use carefully)

```text
Run feature-pipeline-loop unattended through F-004: auto-approve specs,
implement each feature, commit per feature, stop on any test failure or conflict.
```

## Loop integration

Re-invoke each iteration manually, or use Cursor `/loop` dynamic mode:

```text
/loop Run one iteration of feature-pipeline-loop (spec + implement next F-0xx). Stop if tests fail.
```

Prefer **one feature per loop tick** — not all 27 features in one session (context, cost, review).

## Cursor Automation

Create a **manual or scheduled** Cloud/Local automation with this instruction:

```text
In repo CopilotCAD, run skill feature-pipeline-loop for ONE iteration:
next unimplemented F-0xx per roadmap, draft spec if missing, pause for approval
unless AUTONOMOUS=true in prompt, implement, verify tests, update spec status.
Report feature id and pytest result. Do not start a second feature in the same run.
```

Trigger: manual button, or `git` push to your integration branch after merges.

## What this loop does NOT do

- Edit `docs/Docs_001/feature_roadmap_001.md` or `docs/Docs_001/architecture_001.md` (blocked by scope guard).
- Skip spec approval by default (spec-driven contract).
- Guarantee unattended success through Phase 1+ (UI, API keys, E2E need human checks).
