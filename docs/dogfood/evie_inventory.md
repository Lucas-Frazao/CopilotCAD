# Evie dogfood — existing stack vs gaps

Short map of what CopilotCAD already had vs what week-1 added. Product STLs
and print-GO stay with CAD Leader + EVIE Project Leader.

| Area | Already existed | Gap (week-1) |
|------|-----------------|--------------|
| Agent rules | `AGENTS.md`, `CLAUDE.md`, `.cursor/skills/` | — |
| Intent IR | `backend/schemas/intent_ir.py`, validator, sanitizer, compiler | No enclosure-specific IR ops (hole_simple / shell / cut_extrude still stubs) |
| Executor | `engine/executor.py` + handlers for sketch / extrude / `hole_pattern_corners` | Builders call the adapter directly rather than waiting on new IR ops |
| OCCT | `kernel/occt_bridge.py` — sketch, extrude, corner holes, fuse, box, STEP/IGES, tessellate | Arbitrary cut/cylinder/polygon, volume, manifold, point classify, STL |
| Kernel boundary | `engine/kernel_adapter.py` (lazy OCCT) | Wrappers for the new bridge primitives |
| Project FS | workspace / part folders / history / export polish | Not used by the bot connector (in-memory artifacts) |
| Frontend | Electron + JSON-RPC stdio | **Unchanged** — bots do not need the IDE |
| MCP | `mcps/github/*`, `mcps/context7/*` only | CAD generate/validate/export tool schemas |
| HTTP | none | `enclosure.http_api` on localhost |
| Evie spec | none | `specs/evie/evie_enclosure_v3_spec.yaml` (+ json) |
| Gates | Problems engine is IR/workspace warnings, not solid gates | `enclosure.gates` + CLI JSON report |
| Golden STLs | referenced at `/workspace/evie-stl/` (external) | Not checked in; dogfood builders only |

## Reuse decisions

- **No CadQuery.** The repo already cannot import CadQuery; OCCT via the bridge is the kernel.
- **No new JSON-RPC methods.** Grok/CoS call HTTP (or the same service functions the MCP schemas describe).
- **No Electron work.** Connector is backend-only.
- **IR path reused at the kernel layer** (same adapter the step handlers use), not by inventing a parallel modeller.
