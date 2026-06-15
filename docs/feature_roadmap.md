# CopilotCAD — Feature Roadmap

## Guiding principle

Every feature must serve the core product thesis: English authoring → strict Intent IR → traceable parametric CAD. Features that do not serve that thesis do not belong in MVP.

MVP is considered complete when a solo engineer can: start a local project, describe a part or small hardware concept in English, have the system create and manage one or more parametric parts and a small assembly through chat, and export the result to STEP/IGES with a full local workspace preserved.

---

## Phase 0 — Foundation (build this first)

Before any user-facing features exist, the core pipeline must work end-to-end.

### F-000 — Repo and project scaffolding
- Initialize repo structure: `frontend/`, `backend/`, `example_project/`, `tests/`, `docs/`.
- Set up Electron + React + TypeScript frontend shell (blank window).
- Set up Python backend entry point (`main.py`) with JSON-RPC server.
- Wire IPC bridge: frontend spawns backend, sends `ping`, receives `pong`.
- Confirm bidirectional communication works before proceeding.

**Done when:** frontend can send a message to backend and receive a response.

### F-001 — Intent IR schema and validation
- Define all Pydantic models: `IntentIR`, `IRStep`, `IRAssumption`, `IRConstraints`, `IRTarget`, `IRLinks`.
- Write IR validator: checks required fields, valid op types, step dependency graph.
- Write unit tests for valid and invalid IR objects.
- Define complete step catalog as a registry of valid `op` types and required params.

**Done when:** validator accepts known-good IRs and rejects known-bad IRs with structured errors.

### F-002 — Project file system
- Implement `workspace.py`: create new project folder, initialize `copilotcad.json`.
- Implement `part_folder.py`: create part folder, write/read `spec.yaml`, `assumptions.yaml`, `history.json`.
- Implement `assembly_folder.py`: create/read assembly YAML.
- Implement `export.py`: write STEP file via pythonOCC.
- Write unit tests for all read/write operations.

**Done when:** a new project and part folder can be created programmatically with all required artifacts.

### F-003 — Geometry kernel stub and OCCT bridge
- Install pythonOCC-core.
- Implement `occt_bridge.py` with working implementations for:
  - `sketch_rectangle`
  - `extrude`
  - `hole_pattern_corners`
- Implement STEP export from a TopoDS shape.
- Write a standalone test that creates a mounting plate and exports to STEP.

**Done when:** the mounting plate golden example can be generated and exported to a valid STEP file via Python alone, with no UI.

### F-004 — Step execution engine
- Implement `executor.py`: takes a validated IntentIR, sequences steps, calls kernel adapter.
- Implement stub step handlers for the full MVP op catalog.
- Implement `kernel_adapter.py` as thin wrapper.
- Wire executor into backend main loop.
- Test with the mounting plate IntentIR from the golden example.

**Done when:** the full mounting plate IntentIR can be executed end-to-end in Python and produce a STEP file.

---

## Phase 1 — Minimal working product (chat → part → export)

### F-005 — LLM adapter and IR generation
- Implement `LLMAdapter` abstract base class.
- Implement `ClaudeAdapter` using Anthropic Python SDK.
- Write system prompt for IR generation: rules, IR schema, step catalog, project context injection.
- Wire: user message → Claude API → structured JSON → IR parser → IntentIR object.
- Handle LLM output parse failures with structured error responses.
- Test with 5 representative prompts covering simple parts.

**Done when:** a raw English prompt can be reliably converted to a valid IntentIR object via the Claude API.

### F-006 — Problems engine
- Implement `problems/engine.py` with all 7 MVP problem types.
- Wire problems engine to run after every IR execution.
- Return structured `Problem` objects to frontend via IPC.
- Write unit tests for each problem type with triggering conditions.

**Done when:** each problem type can be triggered and returned correctly.

### F-007 — Electron shell and IPC bridge
- Build minimal Electron main process: spawns backend, manages lifecycle.
- Build preload script with contextBridge exposing typed IPC methods.
- Build renderer app shell: 3-column layout with placeholder panels.
- Implement IPC bridge TypeScript types matching backend message types.
- Wire chat panel to send messages and receive responses.

**Done when:** user can type in the chat panel and receive a text response from the backend.

### F-008 — Chat panel
- Build `ChatPanel.tsx`: message history, input field, send button.
- Render chat messages with sender labels (user / CopilotCAD).
- Render assumption tags inline when assumptions are returned.
- Render diff summaries after IR is applied.
- Implement slash command detection and picker UI (`/vision`, `/part`, etc.).
- Render blocking question prompts with accept/edit inputs.

**Done when:** a complete chat interaction (prompt → IR → diff summary) is visible in the UI.

### F-009 — Explorer panel
- Build `ExplorerPanel.tsx`: renders project folder tree from backend file system state.
- Show `docs/`, `parts/`, `assemblies/`, `exports/` nodes.
- Expand part folders to show `spec.yaml`, `assumptions.yaml`, `history.json`.
- File click opens read-only preview.
- Refresh tree on project file system events.

**Done when:** user can see the project tree and open files for inspection.

### F-010 — Problems panel
- Build `ProblemsPanel.tsx`: lists current problems by type.
- Each problem shows: type, description, affected part/file, suggested next step.
- Problems update in real time after each IR execution.
- Click on problem highlights relevant chat context or file.

**Done when:** problems appear and update correctly after a chat action.

### F-011 — Three.js viewport (basic)
- Build `ViewportPanel.tsx` with Three.js renderer.
- Backend sends tessellated mesh data after geometry updates.
- Viewport renders mesh with basic material.
- Orbit, pan, zoom controls.
- Part face/edge selection: selected geometry ID sent as context to chat.
- Highlight selected faces.

**Done when:** a generated part appears in the viewport and user can select faces to provide chat context.

### F-012 — Full single-part flow (golden path)
- End-to-end test: user types mounting plate prompt → IR generated → part folder created → geometry shown in viewport → STEP exported.
- All panels update correctly: explorer, problems, chat diff summary.
- This is the MVP golden path test.

**Done when:** the mounting plate example from the canonical spec runs completely through the product UI.

---

## Phase 2 — PDD integration

### F-013 — PDD suggestion engine
- After IR is generated, classify request complexity.
- Simple single part: proceed directly.
- Complex or multi-part: suggest PDD and offer slash commands.
- Suggestion appears as a chat message with quick-reply buttons.

**Done when:** a complex prompt triggers a PDD suggestion in chat.

### F-014 — Slash command handlers
Implement all 12 MVP slash commands:
- `/vision` — scaffold `docs/product_vision.md` via chat.
- `/constitution` — scaffold `docs/constitution.md`.
- `/architecture` — scaffold `docs/system_architecture.md`.
- `/manufacturing` — scaffold `docs/manufacturing_stack.md`.
- `/part` — create a new part folder and spec.
- `/interface` — define an interface object.
- `/plan` — create or update `plan.md` for a part.
- `/review` — trigger review checklist for a part.
- `/release` — set part maturity to released.
- `/export` — export current part or assembly to STEP/IGES.
- `/assumptions` — show and manage assumptions for current part.
- `/history` — show action history for current part.

**Done when:** all 12 slash commands produce correct project artifacts.

### F-015 — Parts panel
- Build `PartsPanel.tsx`: lists all parts in the project.
- Each part shows: name, maturity status, open problems count.
- Click navigates to part in explorer and loads it in viewport.

**Done when:** parts panel reflects project state correctly.

### F-016 — Interfaces panel
- Build `InterfacesPanel.tsx`: lists all interface objects across the project.
- Shows interface status: open, linked, verified.
- Interface conflict problems link here.

**Done when:** interface panel shows current interface state correctly.

### F-017 — History panel
- Build `HistoryPanel.tsx`: shows action/chat history and feature/geometry history for active part.
- Two tabs: Action history and Feature history.
- Each action entry shows: timestamp, summary, diff, assumptions changed.

**Done when:** history panel is accurate and updates after each action.

---

## Phase 3 — Assembly support

### F-018 — Assembly creation
- Implement `asm_create` IntentIR type.
- Execute assembly creation: create `assemblies/<id>.yaml` with part instances.
- Scaffold part folders for each instance if they don't exist.

**Done when:** user can create a 2-part assembly via chat and see it in the explorer.

### F-019 — Assembly mates
- Implement mate step handlers: `mate_fix`, `mate_coincident`, `mate_concentric`, `mate_distance`.
- Wire mates into OCCT assembly model.
- Detect invalid mate conditions and surface as problems.

**Done when:** a valid 2-part assembly can be mated and rendered in the viewport.

### F-020 — Assembly viewport
- Extend viewport to render assemblies: multiple parts in correct relative positions.
- Assembly tree visible in viewport (part instances listed).
- Clicking a part instance in viewport selects it and provides context to chat.

**Done when:** a 2-part assembly renders correctly with mating applied.

### F-021 — Interface linking in assemblies
- When a mate is created, link the relevant interface objects across parts.
- Update `connects_to` in both part specs.
- Propagate interface conflict detection.

**Done when:** interface objects in part specs correctly link across assemblies.

---

## Phase 4 — Polish and MVP completion

### F-022 — Approval workflow for high-risk actions
- High-risk IR actions send `ir.pending` to frontend before execution.
- Chat panel renders approval prompt: summary + diff preview + approve/reject buttons.
- Backend holds state until approved or rejected.
- Rejected actions are logged to history but not executed.

**Done when:** deleting a part requires approval and can be cancelled.

### F-023 — Assumption management
- Assumptions panel or inline assumption tags in chat.
- User can confirm, reject, or edit assumptions from chat.
- Status changes propagate to `assumptions.yaml` and Problems engine.

**Done when:** user can confirm an AI-proposed assumption and see it reflected in the file.

### F-024 — STEP/IGES export polish
- Ensure export flow works for single parts and assemblies.
- Export writes to `exports/` folder.
- Export action appears in history.
- `/export` slash command triggers this.

**Done when:** user can export any part or assembly via chat or slash command.

### F-025 — New project onboarding
- On new project: blank workspace + guided chat opener.
- Chat says: "What to do first? Ask about this CAD model or we can start creating one."
- No wizard or form. Everything through chat.

**Done when:** new project flow is fully chat-driven with no form UI.

### F-026 — Error handling and failure UX
- All failure cases return structured errors.
- Chat renders: failure explanation, blocking issue, 2-3 suggested next steps.
- Partial work is preserved on failure.
- Problems panel shows active errors.

**Done when:** every known failure mode produces a useful, actionable error in the chat.

---

## Out of scope for MVP (deferred)

- CAM toolpath generation.
- Full 2D drawing workflow.
- Advanced simulation or FEA.
- Large assemblies (more than 5 parts).
- Cloud sync or collaboration.
- Plugin or extension marketplace.
- Advanced tolerance analysis.
- Full release governance workflows.
- BOM generation.
- Local LLM support (stub only in MVP).

---

## Build order summary

```
Phase 0: F-000 → F-001 → F-002 → F-003 → F-004
Phase 1: F-005 → F-006 → F-007 → F-008 → F-009 → F-010 → F-011 → F-012
Phase 2: F-013 → F-014 → F-015 → F-016 → F-017
Phase 3: F-018 → F-019 → F-020 → F-021
Phase 4: F-022 → F-023 → F-024 → F-025 → F-026
```

Do not skip phases. Each phase assumes the previous phase is working and tested.
```
