---
name: verify-frontend
description: >-
  Runs CopilotCAD frontend typecheck (tsc) and vitest from frontend/. Use after
  implementing or changing frontend TypeScript/React/Electron code, or when the
  user asks to verify a frontend F-0xx feature.
disable-model-invocation: true
---

# Verify Frontend (CopilotCAD)

Typecheck the Electron and renderer projects, then run the vitest suite.

## Commands

**Windows (PowerShell):**

```powershell
.cursor/skills/verify-frontend/scripts/verify-frontend.ps1
```

**macOS / Linux:**

```bash
.cursor/skills/verify-frontend/scripts/verify-frontend.sh
```

**Manual:**

```powershell
cd frontend
npm run typecheck
npm test
```

## Expected behavior

- `npm run typecheck` reports no errors for either `tsconfig.electron.json` or
  `tsconfig.json`.
- `npm test` (vitest) passes all suites under `frontend/`.

## If it fails

1. Read the typecheck / test output.
2. Fix only issues related to the current feature scope.
3. Re-run verify-frontend before claiming the feature is done.

## Prerequisite

Run `npm install` in `frontend/` once so `node_modules` exists.
