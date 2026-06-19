---
name: spec-reviewer
description: >-
  Reviews a CopilotCAD F-0xx spec against docs/Docs_001/feature_roadmap_001.md and
  docs/Docs_001/architecture_001.md for conflicts, missing acceptance criteria, and scope
  creep. Use before approving a spec or before merging an F-0xx PR.
disable-model-invocation: true
---

# Spec Reviewer (CopilotCAD)

Review a feature spec as the contract before implementation or merge.

## Inputs

- Feature id (e.g. `F-004`)
- Spec path: `specs/specs_001/F-<id>__<name>.md`

## Review checklist

1. **Roadmap alignment** — Requirements match `docs/Docs_001/feature_roadmap_001.md` section for this F-id.
2. **Architecture alignment** — No contradiction with `docs/Docs_001/architecture_001.md` (IPC, kernel adapter, file ownership).
3. **Prior specs** — Dependencies on F-000–F-003 (or later) are explicit; no duplicate scope.
4. **Non-goals** — IPC, frontend, LLM, and file-system boundaries are clear.
5. **Acceptance criteria** — Each criterion is testable (pytest, manual command, or grep).
6. **Data model** — Contracts match existing schemas (`specs/specs_001/F-001_*`, F-002 workspace manifest, etc.).
7. **Scope creep** — Nothing in Requirements that belongs in a later F-id.

## Output format

```markdown
## Spec review: F-0xx

### Verdict: APPROVE | REVISE | CONFLICT

### Strengths
- ...

### Issues (must fix before implement)
- ...

### Conflicts with docs
- ...

### Suggested acceptance criteria additions
- ...
```

## How to run (agent)

1. Read the spec file in full.
2. Read the F-0xx section in `docs/Docs_001/feature_roadmap_001.md`.
3. Read relevant sections in `docs/Docs_001/architecture_001.md`.
4. Produce the review using the template above.
5. Do not modify code or specs unless the user asks for edits.

## Optional: launch explore subagent

For large diffs after implementation, use Task `subagent_type=explore` with prompt:
"Compare specs/specs_001/F-0xx_*.md acceptance criteria against changed files in the branch."
