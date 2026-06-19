# CopilotCAD — Scope & Vision (v0.01)

## About this document

CopilotCAD is **living software** — it will receive many updates over time. This file is **Scope 001**: the scope and vision for **version 0.01 only**. It is not a permanent definition of the entire product.

Future releases will have their own scope documents (`scope_002.md`, etc.). When this document describes long-term direction (for example business model or editions), that content is **aspirational** unless it also appears under **v0.01 scope** or **Definition of v0.01 success**.

**Related v0.01 docs:** `docs/Docs_001/architecture_001.md`, `docs/Docs_001/tech_stack_001.md`, `docs/Docs_001/feature_roadmap_001.md`.

> **Note:** Inside a **user project**, PDD still uses a separate artifact called **Product Vision** at `docs/product_vision.md` (created via `/vision`). That is a project document, not this repo file.

---

## One-line promise (v0.01)

**CopilotCAD v0.01 lets you author hardware in English and compile it into structured, editable CAD. A cursor for CAD.**

Not prompt-to-shape. Intent-to-CAD.

---

## What v0.01 is

CopilotCAD v0.01 is a local-first, chat-native CAD IDE for solo engineers and students building hardware projects. It combines a VS Code-inspired workspace, a strict intermediate representation (Intent IR) for all write operations, and a Part-Driven Design (PDD) methodology layer that keeps intent, interfaces, assumptions, and geometry connected instead of scattering them across disconnected files and tools.

Local-first means files live on disk, no cloud is required to work, and there is no cloud sync option. The project is always owned by the user on their own machine.

v0.01 is not positioned as "magic text-to-CAD." It is an engineering authoring environment where English is the front-end language, but geometry creation only happens after the request has been compiled into a strict schema capturing intent, assumptions, constraints, interfaces, and modeling steps.

---

## Why CopilotCAD should exist

Traditional CAD workflows are strong at geometry creation but weak at preserving intent, assumptions, interfaces, manufacturing context, and traceability in a way that is easy for solo builders and AI systems to use consistently.

PDD addresses this by treating each part as an intent contract containing:

- Purpose
- Functional requirements
- Physical and logical interfaces
- Constraints
- Material and manufacturing assumptions
- Assembly and relation context
- Validation criteria
- Revision and maturity status

v0.01 is the **first slice** of that vision: a hardware IDE where the part is the core engineering object, the workspace is the project container, and the AI operates as a constrained assistant over structured artifacts rather than a freeform shape generator.

---

## Target user (v0.01)

The primary user for v0.01 is a **solo engineer or student building hardware projects independently**.

v0.01 is not aimed at large teams, enterprise CAD departments, or production machine shops. The design center is the technically ambitious individual builder who wants a more structured and AI-native way to create hardware than today's ribbon-heavy CAD interfaces.

---

## Design principles for v0.01

CopilotCAD v0.01 is built on six core beliefs:

1. **English should be the front-end language** for hardware authoring, but only when backed by strict structured representations.
2. **Every part should be a first-class engineering object**, not just a geometry file.
3. **PDD should always be suggested** because it improves structure, reuse, traceability, manufacturability, and AI usefulness — but it should never be mandatory.
4. **The user should own the project locally**, with no cloud requirement and no sync dependency.
5. **Chat should be the only write interface**, while the rest of the UI supports inspection, context selection, review, and navigation.
6. **AI must operate like a compiler pipeline** with explicit assumptions and visible diffs, not like a magic generator.

---

## User experience vision (v0.01)

A user launches CopilotCAD v0.01 and sees an IDE closely resembling VS Code:

- **Left panel**: project explorer (files/folders) with tabbed panels for Parts, Interfaces, Problems, and History.
- **Center panel**: 3D model viewport for rendering, navigation, inspection, and selection.
- **Right panel**: chat interface — the sole write surface.

On first launch of a new project, the chat panel displays:

> "What to do first? Ask about this CAD model or we can start creating one."

No wizard. No forms. Everything through conversation.

The user describes what they want to build in plain English. CopilotCAD:

1. Asks only 2–3 blocking questions when necessary.
2. Proceeds with the rest as explicit, visible assumptions.
3. Compiles the request into a strict Intent IR.
4. Executes the IR through the geometry kernel.
5. Updates the project files, history, and viewport.
6. Shows a diff summary in chat.
7. Flags any problems in the Problems panel.

If the request appears complex or system-like, CopilotCAD suggests PDD and offers slash-command shortcuts. If the request is simple, it proceeds directly while still maintaining assumptions and traceability.

---

## Interface model (v0.01)

| Panel | Role |
|---|---|
| Explorer | Files and folders only |
| Parts panel | Structured list of project parts and maturity status |
| Interfaces panel | First-class interface objects and their status |
| History panel | Feature history and action/chat history (two tabs) |
| Problems panel | Actionable issues affecting correctness or progress |
| Viewport | 3D geometry rendering, navigation, inspection, selection |
| Chat panel | The only place where write actions originate |

The viewport allows navigation, inspection, and geometry selection to provide context to chat. Direct geometry editing is not allowed. All design changes are authored through language and compiled through structured intent.

---

## Authoring model (v0.01)

CopilotCAD uses English as the user-facing authoring language, but all write operations must compile into a strict **Intent IR** object before any geometry or project files are changed.

Intent IR captures:

- User intent type (part create, part edit, assembly create, etc.)
- Target part or assembly
- Blocking questions and their answers
- Assumptions (scope, source, importance, status)
- Constraints (dimensions, material, process, tolerance, interfaces)
- Ordered modeling steps (op type + parameters)
- Traceability links (spec, requirements, architecture elements)

This compiler-like model ensures geometry changes are inspectable, reproducible, and tied to engineering intent.

---

## PDD strategy (v0.01)

PDD is always suggested but never required. This creates two interaction paths:

**Lightweight path**
- Simple single-part requests proceed directly after blocking questions and explicit assumptions.

**PDD-guided path**
- Complex parts or small systems trigger suggestions to scaffold Product Vision, Constitution, System Architecture, Manufacturing Stack, Part Specs, and interfaces before geometry work proceeds.

The goal is always to aim the user toward PDD because it produces better, more traceable, more reusable design artifacts.

---

## v0.01 scope

### In scope for v0.01

- Local-first desktop project workflow, no cloud.
- VS Code-like workspace UI: explorer, viewport, chat.
- Chat-first authoring only.
- Strict Intent IR compilation before all write operations.
- PDD suggestion engine.
- Slash commands: `/vision`, `/constitution`, `/architecture`, `/manufacturing`, `/part`, `/interface`, `/plan`, `/review`, `/release`, `/export`, `/assumptions`, `/history`.
- Single-part modeling.
- Very small assemblies (2–5 parts).
- Explicit interface objects.
- Part folders with: `part.cad`, `spec.yaml`, `assumptions.yaml`, `history.json`, `interfaces/`.
- STEP and IGES export.
- Proprietary `.cad` format for native workspace persistence.
- Assumption tracking, diff summaries, and visible history.
- Problems panel with 7 MVP problem types.

### Out of scope for v0.01

- Full CAM generation.
- Full 2D drawing workflow.
- Advanced simulation or FEA.
- Large assemblies (more than 5 parts).
- Cloud sync or collaboration.
- Plugin or extension marketplace.
- Advanced tolerance analysis.
- Full release governance workflows.
- BOM generation.
- Local LLM support (stub only).

---

## Definition of v0.01 success

v0.01 is successful when a solo engineer can:

1. Start a local CopilotCAD project.
2. Describe a part or small hardware concept in English.
3. Have the system suggest and scaffold PDD when useful.
4. Create one or more parametric parts and a very small assembly through chat.
5. Inspect and refine the result through explicit assumptions and diffs.
6. Export parts to STEP or IGES.
7. Preserve a full local `.cad` workspace with traceable docs, part specs, interfaces, and history.

---

## Modeling vocabulary (v0.01)

The minimum modeling vocabulary for v0.01:

**Sketch**
- `sketch_rectangle`
- `sketch_circle`

**Solid creation and removal**
- `extrude`
- `cut_extrude`
- `revolve`

**Holes**
- `hole_simple`
- `hole_pattern_corners`

**Edge operations**
- `fillet`
- `chamfer`

**Patterns and mirror**
- `pattern_linear`
- `pattern_circular`
- `mirror`

**Other**
- `shell`
- `offset_face`
- `create_plane`
- `create_axis`
- `create_point`

**Assembly**
- `mate_fix`
- `mate_coincident`
- `mate_concentric`
- `mate_distance`

---

## Project and file structure (v0.01)

Every CopilotCAD project is a local folder:

```
project-root/
├── copilotcad.json            # Root manifest
├── docs/                      # Narrative PDD documents (Markdown)
├── parts/
│   └── <part-id>/
│       ├── part.cad           # Native format
│       ├── spec.yaml          # PDD Part Spec
│       ├── assumptions.yaml   # Structured assumptions
│       ├── history.json       # Action and feature history
│       └── interfaces/        # Interface definitions
├── assemblies/                # Assembly YAML files
└── exports/                   # STEP and IGES outputs
```

Human-facing docs use Markdown. Machine-structured config and spec files use YAML or JSON.

---

## Native `.cad` format (v0.01)

The `.cad` file is not a shape container. It stores:

- Structured parametric history (the feature tree)
- References to sibling PDD artifacts (spec, assumptions, history)
- Interface links
- Geometry state cache

STEP and IGES are export targets. `.cad` is the local-first authoring format.

---

## Problems panel taxonomy (v0.01)

| Problem type | Trigger |
|---|---|
| Missing required input | Blocking info is absent and IR cannot proceed |
| Unresolved assumption | High-importance assumption still proposed |
| Geometry generation failure | Kernel step returned error |
| Interface conflict | Mating interfaces are incompatible |
| Invalid mate / assembly error | Assembly constraint cannot be satisfied |
| Manufacturing rule warning | Design violates declared process limits |
| Traceability gap | Part spec missing expected trace links |

---

## AI trust and autonomy model (v0.01)

### Low-risk actions (execute immediately)
- Create new feature on existing body.
- Add or modify a single dimension or parameter.
- Add or update assumptions.
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

### Failure behavior
When CopilotCAD fails, it must:
- Explain the failure clearly.
- Identify the blocking issue.
- Suggest 2–3 next steps.
- Preserve partial work.
- Never hide failure.

---

## AI personality (v0.01)

CopilotCAD's AI is adaptive but defaults to:

- Concise.
- Engineering-formal.
- Explicit about every assumption it makes.
- Transparent about what it does not know.

It does not over-question. It asks only blocking questions, then proceeds with visible assumptions rather than interrogating the user endlessly.

---

## Positioning (v0.01)

CopilotCAD v0.01 is not a generic text-to-CAD tool. The product avoids:

- "Turn plain English into perfect CAD" framing.
- "Generate production-ready parts instantly" claims.
- Any positioning that implies magic or removes engineering judgment.

The correct framing:

- Not prompt-to-shape.
- Intent-to-CAD.
- Local-first.
- Structured and editable.
- Traceable across parts, docs, and interfaces.

The central value is not that the model generates geometry from words. The central value is that it helps author hardware in English while preserving the structure, traceability, and editability that real engineering work requires.

---

## Business model and licensing direction (long-term)

> **Not v0.01 delivery scope.** This section describes direction beyond v0.01. Community edition behavior for v0.01 is defined in v0.01 scope and `docs/Docs_001/architecture_001.md`.

CopilotCAD is designed from the start to support an open-core, Red Hat–inspired business model.

The long-term plan is:

- **Community edition (open source)**  
  The core CopilotCAD desktop app will be open source and free to use for solo engineers and students. It will remain local-first, with no cloud requirement and no lock-in. The Community edition will support small projects and very small assemblies and will expose a stable plugin/SDK surface so the community can extend the tool.

- **Pro edition (paid, individual)**  
  A paid Pro edition will unlock advanced capabilities for power users. Examples include larger assemblies, more advanced PDD tooling and validation, richer Problems checks, automation and scripting features, and premium integrations. Pro remains local-first and continues to use the same `.cad` project structure as Community.

- **Team / Business edition (paid, organizations)**  
  A Team/Business edition will target small companies and engineering teams. It will focus on shared templates and constitutions, shared interface libraries, organization-level policies and review flows, internal plugin distribution, and support/SLAs. The goal is to help teams standardize their hardware design process around CopilotCAD and PDD.

- **Plugins, SDK, and customization services**  
  CopilotCAD will expose a plugin SDK for adding agents and skills to the chat interface, registering new slash commands, and extending validation and Problems checks. A plugin marketplace will allow both community and commercial plugins. Revenue will come from Pro and Team subscriptions and from customization work for companies that need tailored agents, integrations, and workflows.

Across all editions, CopilotCAD will keep the same core principles: local-first, user-owned data, and structured, inspectable project artifacts. Paid tiers add more scale, automation, validation, integrations, and support rather than taking away ownership or control from the user.

---

## Open questions for v0.01 (and later)

- Exact Intent IR schema (see `docs/Docs_001/architecture_001.md`).
- Structure of `spec.yaml` and `assumptions.yaml` field-level definitions.
- Assembly and interface schema detail.
- Command execution pipeline from prompt to IR to geometry.
- Review and release lifecycle in v0.01.
- Visual hierarchy and behavior of each UI panel.
- How manufacturability warnings are surfaced without full CAM.
- Whether `.cad` geometry cache is per-part or workspace-linked.
