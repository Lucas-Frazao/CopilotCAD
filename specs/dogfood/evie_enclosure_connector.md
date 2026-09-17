# Evie enclosure connector (week-1 dogfood)

## Summary

Add a **generate / validate / export** connector on top of CopilotCAD’s existing
Intent IR → kernel adapter → OCCT path so a Grok bot can produce enclosure-class
parts (Evie faceplate tray, bottom lid, badge) and run **hard validation gates**.

**Status:** Implemented (dogfood). Not an F-0xx roadmap feature; do not treat
this as product STL print-GO.

## Why this exists

Lucas’s personal AI CAD MVP needs a bot-callable surface with gates that reject
an ~80% solid brick and accept a proper open-tray shell. CopilotCAD already has
the kernel and STEP export; it did not have enclosure builders, a gate runner,
or an HTTP/MCP connector.

## Requirements

1. Check in `specs/evie/evie_enclosure_v3_spec.yaml` (+ JSON) as SoT.
2. Gate runner CLI + JSON report implementing:
   - extents ±1 mm (cover Z uses 1.5–2.0; faceplate Z may document `feet_extra_z`)
   - manifold + no floating shells (NOT closed-volume watertight)
   - faceplate `solid_volume_fraction` 0.20–0.25
   - named cutouts: pico_bay 51×21, mute Ø10, mic Ø6, speaker Ø8, LED Ø2, hid USB-C
   - cover 4-hole pattern mates corner bosses
   - design-mm only (ignore FDM shrink)
3. Parametric builders for badge + cover, then faceplate shell, via
   `engine.kernel_adapter` (no CadQuery; no OCCT imports outside `occt_bridge.py`).
4. Thin HTTP **and installable MCP stdio**: generate / validate / export /
   get_evie_spec. `generate` accepts `part` and/or `inline_spec`.
   Auth = local/bot token stub (`COPILOTCAD_BOT_TOKEN`, default `local-dogfood`).
5. Tests: ~80% brick fails fill-band; proper shell passes; badge+cover smoke.
6. No Electron / JSON-RPC changes. No OnShape. No overwrite of product print-GO.

## Non-goals

- Rebuilding the Electron IDE
- New JSON-RPC methods
- Product release / print-GO ownership
- Closed-volume watertight checks on the open tray
- Printer shrink compensation

## Acceptance criteria

1. `python -m enclosure validate --part badge` and `--part cover` exit 0.
2. `python -m enclosure validate --part faceplate` exits 0 on the shell builder.
3. `python -m enclosure validate --part brick` fails `faceplate_fill_band`.
4. HTTP `POST /v1/generate|validate|export` works with a bearer token.
5. Inventory + connector docs live under `docs/dogfood/`.
6. MCP stdio (`python -m enclosure mcp` / `mcps/copilotcad/server.py`) lists
   and calls generate / validate / export / get_evie_spec.
7. `docs/dogfood/grok_cad_bot_loop.md` documents interview → spec → tools →
   approve/revise for Grok CAD Bot / CoS.
