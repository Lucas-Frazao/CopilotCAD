# CopilotCAD enclosure MCP

Stdio MCP server so a Grok CAD Bot (or CoS) can run the Spec → code → CAD
loop without the Electron GUI and without OnShape.

## Tools

| Tool | Schema |
|------|--------|
| `get_evie_spec` | `tools/get_evie_spec.json` |
| `generate` | `tools/generate.json` (`part` and/or `inline_spec`) |
| `validate` | `tools/validate.json` |
| `export` | `tools/export.json` |

Auth: `COPILOTCAD_BOT_TOKEN` (default `local-dogfood`).

## Install

See `docs/dogfood/grok_cad_bot_loop.md` (interview checklist, revise flow, CoS
install, smoke tests). Example host config: `mcp.example.json`.

```bash
python mcps/copilotcad/server.py
# or, from backend/:
python -m enclosure mcp
```
