# CopilotCAD — Tech Stack (v0.01)

## About this document

This document describes the **technology choices for CopilotCAD version 0.01 only**. CopilotCAD is living software; future versions may change stack decisions. Scope and vision for v0.01: `docs/Docs_001/scope_001.md`. Architecture: `docs/Docs_001/architecture_001.md`. Roadmap: `docs/Docs_001/feature_roadmap_001.md`.

## Summary

| Layer | Technology | Reason |
|---|---|---|
| Desktop shell | Electron | Cross-platform, full control, no VS Code dependency |
| Frontend language | TypeScript | Type safety, large ecosystem, pairs well with Electron |
| Frontend framework | React | Component model fits panel-based IDE layout |
| Frontend 3D | Three.js | WebGL viewport for geometry display in Electron renderer |
| Frontend state | Zustand | Lightweight, simple, no boilerplate |
| Frontend styling | Tailwind CSS | Fast, utility-first, good for dense IDE UIs |
| Backend language | Python 3.11+ | Best LLM tooling, pythonOCC bindings, fast prototyping |
| Backend schema validation | Pydantic v2 | Strict schema enforcement for Intent IR and project models |
| Geometry kernel | Open CASCADE (OCCT) via pythonOCC-core | Full B-Rep solid modeling, STEP/IGES native |
| LLM integration | Claude API (Anthropic) via anthropic SDK | Primary LLM for IR generation |
| IPC bridge | JSON-RPC over stdio | Simple, language-agnostic, easy to debug |
| Project file format | YAML (specs), JSON (history, IR), .cad (native) | Human readable, inspectable |
| Native format | Proprietary .cad (JSON-based) | Stores parametric history + IR links + geometry state |
| Export formats | STEP, IGES via pythonOCC | Industry-standard CAD exchange |
| Package manager (frontend) | pnpm | Fast, disk-efficient |
| Package manager (backend) | uv | Fast modern Python package manager |
| Testing (frontend) | Vitest + Playwright | Unit + E2E |
| Testing (backend) | pytest | Unit and integration |
| Linting (frontend) | ESLint + Prettier | |
| Linting (backend) | ruff | |

---

## Frontend stack detail

### Electron

- Main process: spawns Python backend as child process, manages IPC bridge, handles file system dialogs.
- Renderer process: React app rendering all panels.
- Preload script: exposes safe IPC API to renderer (contextBridge).
- No `nodeIntegration` in renderer — all backend calls go through the preload bridge.

### React panel architecture

Each panel is an independent React component:

```
renderer/
├── app.tsx                    # Root layout
├── panels/
│   ├── ExplorerPanel.tsx
│   ├── ViewportPanel.tsx
│   ├── ChatPanel.tsx
│   ├── ProblemsPanel.tsx
│   ├── PartsPanel.tsx
│   ├── InterfacesPanel.tsx
│   └── HistoryPanel.tsx
├── components/
│   ├── FileTree.tsx
│   ├── ChatMessage.tsx
│   ├── AssumptionTag.tsx
│   ├── DiffSummary.tsx
│   ├── ProblemItem.tsx
│   └── SlashCommandPicker.tsx
├── store/
│   └── appStore.ts            # Zustand store
└── ipc/
    └── bridge.ts              # Typed IPC calls to main process
```

### Three.js viewport

- Renders STEP geometry loaded and tessellated by the Python backend.
- Backend sends tessellated mesh data (vertices + faces) over IPC after each geometry update.
- Viewport supports: orbit/pan/zoom, face/edge selection, part highlighting.
- Selection events are sent as context to the chat panel.
- No direct geometry editing from the viewport.

---

## Backend stack detail

### Python 3.11+

Minimum version: 3.11 for improved typing and performance.

### Pydantic v2

All schema models (IntentIR, PartSpec, Assumptions, AssemblySpec, HistoryEvent, Problems) are Pydantic models. IR validation is the primary use case. Strict mode enabled for all IR models.

### pythonOCC-core

The primary interface to Open CASCADE Technology.

Key OCCT modules used in MVP:
- `BRepBuilderAPI` — solid construction
- `BRepPrimAPI` — primitive shapes
- `BRepAlgoAPI` — boolean operations (cut)
- `BRepFilletAPI` — fillets and chamfers
- `gp`, `GeomAPI` — geometry primitives and transforms
- `STEPControl` — STEP import/export
- `IGESControl` — IGES export
- `BRep_Builder`, `TopoDS` — shape manipulation

### LLM adapter

Abstract base class `LLMAdapter` with concrete implementations:
- `ClaudeAdapter` — primary, uses Anthropic Python SDK.
- `LocalAdapter` — stub for future local model support.

The LLM is always called with:
- system prompt (product behavior rules, IR schema, step catalog),
- current project context (spec, assumptions, active part),
- user message.

Output is always expected as structured JSON matching IntentIR schema. If LLM output does not parse, the IR compiler returns a structured error.

### IPC bridge (JSON-RPC over stdio)

Simple request/response protocol:

```json
// Request (frontend → backend)
{"jsonrpc": "2.0", "id": "1", "method": "chat.send", "params": {"message": "...", "context": {...}}}

// Response (backend → frontend)
{"jsonrpc": "2.0", "id": "1", "result": {"type": "ir.applied", "diff": {...}, "problems": [...]}}
```

---

## Native `.cad` format

The `.cad` file is a JSON document storing:

```json
{
  "format": "copilotcad",
  "version": "0.1",
  "part_id": "mounting_plate",
  "features": [
    {
      "id": "s1",
      "op": "sketch_rectangle",
      "params": {"length": 100.0, "width": 50.0, "plane": "XY", "mode": "center"}
    },
    {
      "id": "s2",
      "op": "extrude",
      "from": "s1",
      "params": {"distance": 6.0, "direction": "+Z", "mode": "add"}
    }
  ],
  "links": {
    "spec": "spec.yaml",
    "assumptions": "assumptions.yaml",
    "history": "history.json"
  },
  "geometry_cache": "<base64 BREP or STEP bytes>"
}
```

- `features` is the parametric history. It is the source of truth for regeneration.
- `geometry_cache` is a cached geometry state so the viewport can load without replaying history every time.
- `links` tie the `.cad` file to its sibling PDD artifacts.

---

## Repo structure

```
CopilotCAD/
├── docs/                          # Product docs
│   └── Docs_001/                  # v0.01 scope, architecture, roadmap, tech stack
│       ├── scope_001.md
│       ├── architecture_001.md
│       ├── tech_stack_001.md
│       └── feature_roadmap_001.md
├── specs/                         # Feature specs
│   └── specs_001/                 # v0.01 feature specs (F-000–F-027)
├── pdd_methodology_full_guide.md  # Existing PDD reference
├── frontend/                      # Electron + React app
│   ├── electron/
│   │   ├── main.ts
│   │   └── preload.ts
│   ├── renderer/
│   │   ├── app.tsx
│   │   ├── panels/
│   │   ├── components/
│   │   ├── store/
│   │   └── ipc/
│   ├── package.json
│   └── tsconfig.json
├── backend/                       # Python backend
│   ├── main.py
│   ├── ir/
│   ├── engine/
│   ├── kernel/
│   ├── project/
│   ├── problems/
│   ├── llm/
│   └── schemas/
├── example_project/               # Golden path example project (mounting plate)
│   ├── copilotcad.json
│   ├── docs/
│   ├── parts/
│   │   └── mounting_plate/
│   │       ├── spec.yaml
│   │       ├── assumptions.yaml
│   │       └── history.json
│   └── exports/
└── tests/
    ├── frontend/
    └── backend/
```

---

## Key dependencies

### Frontend (`frontend/package.json`)

```json
{
  "dependencies": {
    "electron": "^30.0.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "three": "^0.165.0",
    "zustand": "^4.5.0",
    "tailwindcss": "^3.4.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "electron-builder": "^24.0.0",
    "vitest": "^1.6.0",
    "playwright": "^1.44.0",
    "eslint": "^9.0.0",
    "prettier": "^3.3.0"
  }
}
```

### Backend (`backend/pyproject.toml`)

```toml
[project]
name = "copilotcad-backend"
python = ">=3.11"

dependencies = [
  "pydantic>=2.7",
  "pythonocc-core>=7.7",
  "anthropic>=0.28",
  "ruamel.yaml>=0.18",
  "jsonrpcserver>=5.0"
]

[tool.ruff]
line-length = 100
```
