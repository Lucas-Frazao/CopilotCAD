# CopilotCAD — System Architecture (v0.01)

## About this document

This document describes the **system architecture for CopilotCAD version 0.01 only**. CopilotCAD is living software; later versions may extend or replace parts of this design. Scope and vision for v0.01: `docs/Docs_001/scope_001.md`. Tech stack: `docs/Docs_001/tech_stack_001.md`. Roadmap: `docs/Docs_001/feature_roadmap_001.md`.

## Overview

CopilotCAD is a local-first, chat-native CAD IDE built on a Python backend and an Electron/TypeScript frontend. The product is structured as two separate processes — a frontend shell and a backend engine — communicating over a local IPC bridge. All write operations are gated by a strict Intent IR compiler pipeline before any geometry or project files are modified.

The architecture is designed so that the authoring model (chat → IR → geometry) is the central pipeline, and all other subsystems (UI, file system, problems, history) are consumers of that pipeline rather than parallel write paths.

---

## High-level architecture

```
┌─────────────────────────────────────────────────────┐
│                  Electron Frontend                  │
│                                                     │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ Explorer │  │  3D Viewport │  │  Chat Panel   │ │
│  │  Panel   │  │  (Three.js / │  │  (React)      │ │
│  │  (React) │  │   OCCT WASM) │  │               │ │
│  └──────────┘  └──────────────┘  └───────────────┘ │
│                                                     │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ Problems │  │    Parts     │  │  Interfaces   │ │
│  │  Panel   │  │    Panel     │  │    Panel      │ │
│  └──────────┘  └──────────────┘  └───────────────┘ │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │              History Panel                   │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────┘
                          │ IPC (JSON-RPC over stdio)
┌─────────────────────────▼───────────────────────────┐
│                  Python Backend                     │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │              Intent IR Compiler              │  │
│  │  chat text → parse → validate → IR object   │  │
│  └──────────────────────┬───────────────────────┘  │
│                         │                          │
│  ┌──────────────────────▼───────────────────────┐  │
│  │              Execution Engine                │  │
│  │  IR → step sequencer → kernel adapter       │  │
│  └──────────────────────┬───────────────────────┘  │
│                         │                          │
│  ┌──────────────────────▼───────────────────────┐  │
│  │              Geometry Kernel                 │  │
│  │  pythonOCC (Open CASCADE Technology)        │  │
│  └──────────────────────┬───────────────────────┘  │
│                         │                          │
│  ┌──────────────────────▼───────────────────────┐  │
│  │           Project File System                │  │
│  │  read/write spec.yaml, assumptions.yaml,    │  │
│  │  history.json, part.cad, copilotcad.json    │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │              LLM Adapter                     │  │
│  │  local model or API (Claude / OpenAI)       │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │              Problems Engine                 │  │
│  │  validates IR, geometry state, traceability │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Frontend (Electron + TypeScript + React)

### Responsibilities

- Render all UI panels.
- Capture user chat input and send to backend via IPC.
- Receive IR results, geometry updates, problems, history events from backend.
- Render 3D geometry in viewport (STEP/IGES geometry loaded via Three.js or OCCT WASM).
- Allow viewport navigation, inspection, and geometry selection (selection passed as context to chat).
- Render project file tree in explorer.
- Render Problems, Parts, Interfaces, and History panels.
- Slash command parsing in chat input (`/vision`, `/part`, etc.) before sending to backend.

### What the frontend must NOT do

- The frontend must never write project files directly.
- The frontend must never invoke geometry operations directly.
- The frontend must never modify the IR.
- All write operations originate from chat and go through the backend pipeline.

### Panel layout

```
┌────────────────────────────────────────────────────────┐
│  Menu bar                                              │
├──────────┬─────────────────────────────┬───────────────┤
│ Explorer │                             │               │
│ Parts    │       3D Viewport           │  Chat Panel   │
│ Ifaces   │      (center, main)         │               │
│ History  │                             │               │
│ Problems │                             │               │
├──────────┤                             │               │
│ (tabs)   │                             │               │
└──────────┴─────────────────────────────┴───────────────┘
│ Status bar                                             │
└────────────────────────────────────────────────────────┘
```

---

## Backend (Python)

### Responsibilities

- Receive raw chat messages from frontend via IPC.
- Run LLM inference or API call to produce a structured Intent IR candidate.
- Validate Intent IR against schema (pydantic models).
- Sequence IR steps through the execution engine.
- Call pythonOCC kernel adapter per step.
- Write and update project files (`spec.yaml`, `assumptions.yaml`, `history.json`, `part.cad`).
- Run the Problems engine after each action.
- Return viewport geometry (STEP bytes or Three.js-compatible mesh data) to frontend.
- Return structured events (diffs, assumptions updates, new problems) to frontend.

### Backend modules

```
backend/
├── main.py                    # IPC entry point (JSON-RPC server)
├── ir/
│   ├── models.py              # Pydantic models for IntentIR, steps, assumptions, etc.
│   ├── parser.py              # LLM output → IntentIR object
│   └── validator.py           # Schema and constraint validation
├── engine/
│   ├── executor.py            # Sequences IR steps
│   ├── step_handlers/         # One handler per op type
│   │   ├── sketch_rectangle.py
│   │   ├── extrude.py
│   │   ├── hole_pattern.py
│   │   └── ... (one per op)
│   └── kernel_adapter.py      # Thin wrapper over pythonOCC calls
├── kernel/
│   └── occt_bridge.py         # Direct pythonOCC calls, returns TopoDS shapes
├── project/
│   ├── workspace.py           # Read/write copilotcad.json and top-level structure
│   ├── part_folder.py         # Read/write spec.yaml, assumptions.yaml, history.json
│   ├── assembly_folder.py     # Read/write assembly YAML
│   └── export.py              # STEP/IGES export via pythonOCC
├── problems/
│   └── engine.py              # Validates workspace state, returns Problem objects
├── llm/
│   ├── adapter.py             # Abstract LLM adapter interface
│   ├── claude_adapter.py      # Claude API implementation
│   └── local_adapter.py       # Local model implementation (stub for now)
└── schemas/
    ├── intent_ir.py           # IntentIR pydantic model
    ├── part_spec.py           # PartSpec model
    ├── assumptions.py         # Assumptions model
    ├── history.py             # HistoryEvent model
    └── assembly_spec.py       # AssemblySpec model
```

---

## IPC bridge

Frontend (TypeScript) spawns the Python backend as a child process. Communication is JSON-RPC over stdio.

### Key message types

**Frontend → Backend**
- `chat.send` — raw user message + current selection context
- `project.open` — open a project folder
- `project.new` — create a new project
- `ir.approve` — user approves a pending high-risk IR action
- `ir.reject` — user rejects a pending action

**Backend → Frontend**
- `ir.pending` — IR compiled, awaiting approval (high-risk actions)
- `ir.applied` — IR applied, includes diff summary
- `geometry.update` — new geometry bytes ready for viewport
- `problems.update` — updated problems list
- `assumptions.update` — updated assumptions list
- `history.update` — new history event appended
- `chat.response` — LLM response text for display in chat panel
- `error` — structured error with type, blocking issue, and suggested next steps

---

## Intent IR compiler pipeline

This is the central pipeline. Every write operation must go through it.

```
chat text
    │
    ▼
LLM call (with project context + system prompt)
    │
    ▼
LLM output (structured JSON)
    │
    ▼
IR parser → IntentIR object
    │
    ▼
IR validator (pydantic + constraint checks)
    │
    ├── validation failure → Problems engine → frontend error
    │
    ▼
Risk classifier
    │
    ├── high risk → send ir.pending to frontend → wait for approval
    │
    ▼
Step sequencer (executor.py)
    │
    ▼
Kernel adapter (one call per step)
    │
    ├── kernel failure → geometry generation failure problem
    │
    ▼
Project file writer (spec, assumptions, history, part.cad)
    │
    ▼
Problems engine (post-action validation)
    │
    ▼
Broadcast events to frontend
```

---

## Geometry kernel

CopilotCAD uses Open CASCADE Technology (OCCT) via the pythonOCC-core bindings as its geometry kernel.

Reasons:
- Full-featured B-Rep solid modeling kernel.
- STEP and IGES import/export natively supported.
- Actively maintained open-source project.
- Python bindings (pythonOCC) are stable and well-documented.

The kernel is wrapped in a thin `occt_bridge.py` adapter. Step handlers call the adapter, not OCCT directly, so the kernel can be swapped without changing the rest of the engine.

---

## Project file system

```
project-root/
├── copilotcad.json            # Root manifest
├── docs/
│   ├── product_vision.md
│   ├── constitution.md
│   ├── system_architecture.md
│   ├── manufacturing_stack.md
│   └── relation_architecture.md
├── parts/
│   └── <part-id>/
│       ├── part.cad           # Native format (geometry + IR links)
│       ├── spec.yaml
│       ├── assumptions.yaml
│       ├── history.json
│       └── interfaces/
├── assemblies/
│   └── <assembly-id>.yaml
└── exports/
    └── <part-id>.step
```

### Edition and capabilities

The root `copilotcad.json` file also encodes the edition and effective capabilities. This allows different distributions (Community, Pro, Team) to share the same codebase while enabling or disabling features cleanly.

Example:

```jsonc
{
  "project_name": "robot_arm_v1",
  "version": "0.1",
  "edition": "community",          // community | pro | team
  "capabilities": {
    "max_assembly_parts": 5,
    "advanced_pdd": false,
    "scripting": false,
    "plugin_marketplace": false
  }
}
```

At MVP, these capabilities are mostly placeholders and are not strictly enforced. They exist so that Pro/Team builds and future licensing logic have a single, explicit place to read project-level feature flags.

---

## Problems engine

The problems engine runs after every IR execution and validates:

| Problem type | Trigger |
|---|---|
| Missing required input | IR has unanswered blocking questions |
| Unresolved assumption | High-importance assumption still proposed |
| Geometry generation failure | Kernel step returned error |
| Interface conflict | Mating interfaces are incompatible |
| Invalid mate / assembly error | Mate constraint cannot be satisfied |
| Manufacturing rule warning | Part violates declared process limits |
| Traceability gap | Part spec missing required trace links |

---

## History model

Two separate layers, linked by `intent_id`:

- **Feature/geometry history** — parametric feature tree stored in `part.cad`.
- **Action/chat history** — structured events in `history.json`, one entry per IR execution.

Each history event records: timestamp, source (chat/slash command), intent_id, summary, steps executed, diff, and assumptions changed.

---

## AI trust and autonomy rules

### Low-risk actions (execute immediately)
- Create new feature on existing body.
- Add or modify a single dimension or parameter.
- Add assumptions or update assumption status.
- Scaffold new doc files.

### High-risk actions (require explicit approval)
- Delete a part.
- Overwrite major geometry.
- Change interfaces used by assemblies.
- Change manufacturing assumptions.
- Change project units.
- Regenerate from a fundamentally different interpretation.
- Bulk changes across multiple parts.
- Release or export actions.

---

## Key architecture principles

1. Chat is the only write interface.
2. No write operation happens before IR is compiled and validated.
3. The frontend is purely reactive — it renders state, it does not own state.
4. Project files are the source of truth, not in-memory state.
5. The geometry kernel is always behind an adapter — never called directly from application logic.
6. Assumptions are first-class objects, not comments.
7. Problems are computed, not manually entered.
