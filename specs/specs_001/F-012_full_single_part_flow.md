# F-012 — Full single-part flow (golden path)

## Summary

Prove the **end-to-end MVP path** for one part: user describes a mounting plate in chat → system creates files, shows 3D geometry, lists problems, and can export STEP — with **all panels staying in sync**.

**Status:** Implemented.

## Why this matters

Individual features (F-008–F-011) can work alone but still fail together. F-012 is the **integration test as a product milestone**: the canonical “mounting plate” example must run through the real UI, not just Python scripts.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Golden path** | The one happy-path scenario the team trusts as “MVP works.” |
| **Golden example** | Mounting plate: 100×50 mm, 6 mm thick, 6 mm corner holes — defined in specs and tests. |
| **STEP** | A standard CAD file format for exchanging 3D models between tools. |
| **Panel sync** | Explorer, chat, problems, and viewport all reflect the same project state after one action. |

## The golden path scenario

**User prompt (example):**

> Create a 100×50×6 mm mounting plate with 6 mm corner holes.

**Expected system behavior:**

1. **Chat** — Shows summary, assumptions, diff (steps executed), inline problems.
2. **Backend** — Creates/updates `parts/mounting_plate/` with `spec.yaml`, `assumptions.yaml`, `history.json`, geometry artifact.
3. **Explorer** — Tree shows new part folder and files.
4. **Viewport** — 3D plate visible; navigable and selectable.
5. **Problems** — Lists warnings (e.g. unresolved assumptions, traceability) where applicable.
6. **Export** — STEP file written to `exports/` (via execute path or explicit export step).

## What we will build

F-012 is primarily **integration and polish**, not a large new subsystem:

| Work area | Details |
|-----------|---------|
| Automated E2E test | Playwright or scripted flow: launch app, send prompt (mocked LLM optional), assert panels |
| Backend wiring gaps | Ensure execute path writes part folder artifacts when missing |
| Refresh orchestration | Single “project state updated” hook after execute |
| Bug fixes | Anything blocking the golden path |
| Documentation | Update spec status; short “how to run golden path” in test README |

## Acceptance criteria

1. Manual test: mounting plate prompt completes without raw RPC errors in chat.
2. Explorer shows `parts/mounting_plate/` with expected YAML/JSON files.
3. Viewport displays plate geometry.
4. Problems panel reflects post-execute problems.
5. STEP file exists in `exports/` after flow completes.
6. Automated test covers the flow (mocked LLM acceptable for CI).
7. No regression in backend pytest or frontend vitest.

## Dependencies

- **F-008** — Chat compile + execute UI.
- **F-009** — Explorer tree and preview.
- **F-010** — Problems panel.
- **F-011** — Viewport mesh rendering.
- **F-002, F-004** — File system and executor.

## Out of scope (not in F-012)

- Assembly flows (Phase 3).
- Slash command file scaffolding (F-014).
- Approval workflow (F-022).
- Performance optimization beyond “works for one part.”

## Notes for reviewers

If F-012 fails, we **fix the pipeline** rather than weakening the golden example. This feature is the gate for calling Phase 1 “done.”
