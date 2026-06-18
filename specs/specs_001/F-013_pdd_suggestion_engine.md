# F-013 — PDD suggestion engine

## Summary

When a user’s chat request is **complex** (multi-part, vague, or assembly-scale), CopilotCAD should **suggest Part-Driven Design (PDD)** in chat — with quick-reply buttons — instead of blindly generating a weak single-part plan.

**Status:** Pending approval.

## Why this matters

Simple parts can go straight to geometry. Complex hardware benefits from structured docs (vision, architecture, part specs) before modeling. The suggestion engine teaches good habits without **forcing** a wizard or blocking simple work.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **PDD (Part-Driven Design)** | A methodology where each part has a spec document (purpose, interfaces, constraints) — not just a 3D file. |
| **Complexity classification** | Backend or LLM logic that labels a request as “simple part” vs “needs more structure.” |
| **Quick-reply buttons** | Tappable options in chat (e.g. “Start with /vision”, “Proceed with part only”) — no separate form UI. |

## What the user will experience

**Simple prompt** (e.g. “100×50 plate with holes”):

- System proceeds normally — compile → execute — no PDD nag.

**Complex prompt** (e.g. “Build a drone frame with motor mounts and battery bay”):

- Chat shows a CopilotCAD message explaining that PDD could help structure the project.
- Buttons or suggested slash commands: `/vision`, `/architecture`, `/part`, or “Continue without PDD.”
- Choosing a button inserts the slash command or sends a follow-up message (wired in F-014 for actual file creation).

## What we will build

### Backend

- **`classify_request_complexity(message, context?)`** — Returns `simple` | `suggest_pdd` with optional reason string.
- Heuristics MVP: keyword count, multi-part mentions, assembly words, missing dimensions, LLM optional tier.
- Integrate into `compile_intent` path **before** full IR generation, or as post-classify branch that returns a special chat payload.

### Frontend

- New chat message kind: `pdd_suggestion` with reason text and action buttons.
- Buttons call chat input setter or trigger slash command stubs.

## Acceptance criteria

1. Clearly simple prompts do not show PDD suggestion.
2. Clearly complex prompts show suggestion with at least two actions (use PDD / proceed anyway).
3. Suggestion is a chat message only — no modal wizard.
4. Classification logic has unit tests with example prompts.
5. Does not write files by itself (F-014 handles slash scaffolding).

## Dependencies

- **F-005** — LLM / compile pipeline.
- **F-008** — Chat message rendering extensions.

## Out of scope (not in F-013)

- Implementing slash command file writes (F-014).
- Mandatory PDD gate — user can always proceed.
- ML model training for classification — heuristics + optional LLM call suffice for MVP.

## Notes for reviewers

PDD is **suggested, never required** — aligned with product vision. This feature is about timing and UX, not new geometry ops.
