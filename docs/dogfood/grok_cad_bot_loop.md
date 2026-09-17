# Grok CAD Bot — Spec → code → CAD loop

Dogfood only. A passing gate report does **not** grant Evie product STL print-GO.
Never automate OnShape (or any CAD GUI). CopilotCAD builds solids through OCCT
code; the bot interviews, emits a spec, and calls generate / validate / export.

## What the bot does

```text
interview  →  YAML/JSON spec  →  generate  →  validate  →  export
                 ↑                    │            │
                 └──── revise ────────┴────────────┘
                        (failed gates or user reject)
```

1. Interview the human until every hard-gate field is explicit (mm, design-only).
2. Emit a machine-readable spec (YAML or JSON) in the Evie v3 shape.
3. Call CopilotCAD tools — MCP preferred, HTTP if the host has no MCP.
4. Present the gate report plus artifact paths. Ask **approve** or **revise**.
5. On revise: update the spec (and/or ask for a builder-code change). Never click a GUI.

Geometry comes from the checked-in OCCT builders (`backend/enclosure/builders.py`).
`inline_spec` is the **contract the gates score against**, not a second modeller.

## Interview checklist

Ask until each row has a numeric or enumerated answer. Prefer `get_evie_spec`
as the template so the human edits the SoT instead of inventing a new schema.

| Ask | Why it is required | Evie v3 default (design mm) |
|-----|--------------------|-----------------------------|
| Which solid? `badge` / `cover` / `faceplate` | `generate` needs a part | all three exist |
| XY extents + Z | `extents_within_tol` | badge 45×15×2; cover 115×65×1.75 (Z 1.5–2.0); faceplate body 115×65×28 |
| Extents tolerance | same gate | ±1 mm |
| Faceplate fill band | `faceplate_fill_band` rejects an ~80% brick | solid volume fraction 0.20–0.25 |
| Named cutouts | `named_cutouts_present` | pico_bay 51×21, mute Ø10, mic Ø6, speaker Ø8, status_led Ø2, hid USB-C |
| Cover hole pattern | `cover_hole_pattern_aligns_bosses` | 4 corners, mates faceplate bosses |
| Units / shrink | `design_mm_only` | mm, scale 100% — **do not** apply Adventurer 5M shrink (~90–91%) |
| Print-GO owner | ownership reminder | still CAD Leader + EVIE Project Leader |

Do **not** proceed to `generate` while any row is “TBD”. If the human wants a
non-Evie envelope, say so in the spec and expect extents/fill gates to fail
until builders are changed in this repo (code revise, not GUI).

## Emit the spec

SoT files:

- `specs/evie/evie_enclosure_v3_spec.yaml`
- `specs/evie/evie_enclosure_v3_spec.json`

Minimum shape the connector accepts:

```yaml
schema_version: "1.1"
project: Evie
enclosure: v3
units: mm
part: badge          # or pass part= in the tool call
parts:
  badge:
    extents: { x: 45, y: 15, z: 2 }
    extents_tol: 1.0
```

A full Evie spec (all three parts) is what `get_evie_spec` returns. When the
document lists multiple parts, the tool call must also set `part`.

## Tool calls (MCP)

Installable server: `mcps/copilotcad/server.py` (stdio JSON-RPC).

| Tool | Purpose | Typical arguments |
|------|---------|-------------------|
| `get_evie_spec` | Interview template | `format`: `yaml` or `json` |
| `generate` | Build OCCT solid | `part` **or** `inline_spec` (or both) |
| `validate` | Hard gates → JSON report | `artifact_id` from generate; optional `inline_spec`, `mate_artifact_id` |
| `export` | Write STEP/STL/IGES | `artifact_id`, `format`, optional `dest` |

Auth: local stub `local-dogfood`. Override with `COPILOTCAD_BOT_TOKEN`.
MCP stdio is trusted when the stub is unchanged; if the env token is customized,
pass `token` on every tool call. HTTP always requires the header.

### Happy path

```text
get_evie_spec(format=yaml)
generate(part=badge, inline_spec=<emitted spec>)
validate(artifact_id=<id>)
export(artifact_id=<id>, format=step)
# repeat generate/validate/export for cover, then faceplate
# cover vs faceplate bosses:
validate(part=cover, artifact_id=<cover-id>, mate_artifact_id=<faceplate-id>)
```

### What to show the human

From `validate` (`schema`: `copilotcad.enclosure.gate_report.v1`):

- `passed` (true/false)
- each `gates[].id` + `passed` + `detail`
- `artifact_id`
- `ownership.note` (dogfood, not print-GO)

From `export`:

- `path` (absolute)
- `bytes`
- `format`

Then ask: **approve** this artifact, or **revise** the spec / builder.

`200` / MCP `isError=false` on validate still means “report delivered”.
A failed hard gate is `passed: false` (HTTP `422`). Treat
`faceplate_fill_band` or `named_cutouts_present` failure as a brick /
missing-feature reject — do not print.

## Example revise flow

1. Human: “Make the badge 50 mm wide.”
2. Bot updates `parts.badge.extents.x` to `50` and calls
   `validate(artifact_id=…, inline_spec=<new spec>)` (or regenerate + validate).
3. `extents_within_tol` fails because the OCCT badge builder is still 45 mm.
4. Bot reports the failed gate and the two options:
   - **Spec revise** — keep 45 mm (SoT) and tell the human the builder will not move.
   - **Code revise** — change `backend/enclosure/builders.py` / constants in this
     repo, re-run generate. Still no OnShape, no Electron click-path.
5. Human picks one. Bot does not silently loosen a hard gate.

Failed-then-fixed smoke (spec-only, badge SoT):

```text
# 1) wrong contract (expect extents fail)
validate(part=badge, inline_spec=parts.badge.extents {x: 10, y: 10, z: 10})

# 2) SoT contract (expect pass)
validate(part=badge)          # or inline_spec from get_evie_spec
export(artifact_id=…, format=step)
```

## How CoS installs the connector

**CoS** here is the Cursor / Claude Code / Grok host that loads MCP servers.
Copy `mcps/copilotcad/mcp.example.json` (or the blocks below). Restart the host
after editing MCP config. Use the same Python that has project deps (`pyyaml`;
`pythonocc-core` for generate/validate/export).

### Cursor

Merge into `.cursor/mcp.json` (or Cursor **Settings → MCP**):

```json
"copilotcad-enclosure": {
  "command": "python",
  "args": ["${workspaceFolder}/mcps/copilotcad/server.py"],
  "env": {
    "COPILOTCAD_BOT_TOKEN": "local-dogfood"
  }
}
```

Prefer the venv / micromamba interpreter that already runs `python -m enclosure`
if the default `python` lacks OCCT.

### Claude Code

Same server block in `.mcp.json`.

### Grok CAD Bot without MCP

```bash
cd backend
export COPILOTCAD_BOT_TOKEN=local-dogfood   # optional; this is the default
python -m enclosure serve --host 127.0.0.1 --port 8765
```

```http
Authorization: Bearer local-dogfood
Content-Type: application/json

GET  /v1/spec?format=yaml
POST /v1/generate   {"part":"badge","inline_spec":{...}}
POST /v1/validate   {"artifact_id":"<id>"}
POST /v1/export     {"artifact_id":"<id>","format":"step"}
```

CLI equivalent (no server):

```bash
python -m enclosure spec --format yaml
python -m enclosure generate --part badge --inline-spec ../specs/evie/evie_enclosure_v3_spec.yaml
python -m enclosure validate --part badge
python -m enclosure export --part badge --format step --out /tmp/evie_badge.step
```

HTTP payload details: `docs/dogfood/evie_connector.md`.

## Smoke test

From `backend/` (or repo root with `PYTHONPATH=backend`):

```bash
# Always — no OCCT required
python -m enclosure spec --format json
python -m enclosure smoke --skip-geometry

# MCP handshake on stdio (one-shot)
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_evie_spec","arguments":{"format":"json"}}}' \
  | python -m enclosure mcp
```

With `pythonocc-core` (same as week-1 dogfood):

```bash
python -m enclosure smoke
python -m enclosure validate --part badge
python -m enclosure validate --part cover
python -m enclosure validate --part faceplate
# brick must fail faceplate_fill_band (exit 2)
python -m enclosure validate --part brick ; echo $?
```

HTTP:

```bash
python -m enclosure serve --port 8765
curl -s http://127.0.0.1:8765/health
curl -s -H "Authorization: Bearer local-dogfood" \
  "http://127.0.0.1:8765/v1/spec?format=json"
curl -s -H "Authorization: Bearer local-dogfood" \
  -H "Content-Type: application/json" \
  -d '{"part":"badge"}' http://127.0.0.1:8765/v1/generate
```

Pytest (keep green):

```bash
# from backend/, project venv or CI micromamba
python -m pytest -v ../tests/backend/test_evie_enclosure_gates.py \
  ../tests/backend/test_evie_enclosure_http.py \
  ../tests/backend/test_evie_enclosure_mcp.py
```

OCCT tests skip when `pythonocc-core` is missing; MCP handshake + spec tests still run.

## Ownership reminder

`owners.product_stl_print_go` in the spec is **not** transferred by a passing
dogfood report. Golden fixtures under `/workspace/evie-stl/` are external and
must not be overwritten by this connector.
