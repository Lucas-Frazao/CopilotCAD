---
name: verify-backend
description: >-
  Runs CopilotCAD backend pytest from backend/.venv. Use after implementing or
  changing backend Python code, or when the user asks to verify F-0xx tests.
disable-model-invocation: true
---

# Verify Backend (CopilotCAD)

Run the backend test suite exactly as configured in `backend/pyproject.toml`.

## Commands

**Windows (PowerShell):**

```powershell
.cursor/skills/verify-backend/scripts/verify-backend.ps1
```

**macOS / Linux:**

```bash
.cursor/skills/verify-backend/scripts/verify-backend.sh
```

**Manual:**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

## Expected behavior

- All non-skipped tests pass.
- `test_occt_bridge_mounting_plate.py` is skipped when `pythonocc-core` is not installed (e.g. Windows ARM64).

## If pytest fails

1. Read failure output.
2. Fix only issues related to the current feature scope.
3. Re-run verify-backend before claiming the feature is done.

## Optional: single test file

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v ..\tests\backend\test_intent_ir_validation.py
```

Replace with the relevant test module for the active F-0xx feature.
