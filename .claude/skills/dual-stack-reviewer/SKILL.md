---
name: dual-stack-reviewer
description: >-
  Reviews CopilotCAD changes for frontend/backend boundary violations: OCCT
  imports outside occt_bridge, frontend project writes, nodeIntegration in
  renderer, IPC changes without spec. Use when reviewing PRs or before merging
  F-0xx work.
disable-model-invocation: true
---

# Dual-Stack Reviewer (CopilotCAD)

CopilotCAD splits Electron/React (frontend) and Python (backend). This review enforces architectural boundaries.

## Checklist

Run these greps (or equivalent) on the changed branch:

```text
1. OCCT only in kernel bridge
   rg "from OCC" backend --glob "!kernel/occt_bridge.py"
   → expect: no matches

2. Frontend must not import python or write workspace files
   rg "copilotcad.json|create_workspace|writeFile.*parts/" frontend/
   → expect: no inappropriate writes (IPC bridge stubs are OK)

3. Renderer security (F-000 contract)
   rg "nodeIntegration" frontend/electron/main.ts
   → expect: nodeIntegration: false, contextIsolation: true

4. IPC surface
   rg "method|@method" backend/main.py
   → compare to active feature spec; ping-only unless spec allows more

5. Backend owns geometry
   rg "three|TopoDS|occt" frontend/
   → Three.js in renderer OK; no OCCT in frontend
```

## Red flags

| Finding | Severity |
|---------|----------|
| `from OCC` outside `backend/kernel/occt_bridge.py` | Critical |
| `nodeIntegration: true` in renderer | Critical |
| New JSON-RPC methods without spec | High |
| React component writing `parts/` or `copilotcad.json` | Critical |
| `validate_intent_ir` skipped before geometry writes | High (post-F-004) |

## Output format

```markdown
## Dual-stack review

### Verdict: PASS | FAIL

### Critical
- ...

### Warnings
- ...

### Notes
- ...
```

## How to run (agent)

1. `git diff main...HEAD --name-only` (or current branch vs main).
2. Run checklist on changed paths.
3. Cross-check against active `specs/specs_001/F-0xx_*.md` Non-goals.
4. Report using template above.

## Optional: launch code-reviewer subagent

Use Task `subagent_type=code-reviewer` on branch changes with prompt:
"Focus on CopilotCAD dual-process boundaries per .cursor/skills/dual-stack-reviewer/SKILL.md."
