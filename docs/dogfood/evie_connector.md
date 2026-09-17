# How CoS / Grok should call the Evie enclosure connector

Dogfood only. This API does **not** grant Evie product STL print-GO.

## Spec SoT

- YAML: `specs/evie/evie_enclosure_v3_spec.yaml`
- JSON: `specs/evie/evie_enclosure_v3_spec.json`

Gates are design-mm. Do not apply Adventurer 5M shrink (~90–91%).

## CLI (from `backend/`)

```bash
python -m enclosure generate --part badge --out /tmp/evie_badge.step
python -m enclosure generate --part cover --out /tmp/evie_cover.step
python -m enclosure validate --part badge --report /tmp/badge_gates.json
python -m enclosure validate --part cover --report /tmp/cover_gates.json
python -m enclosure validate --part faceplate --report /tmp/faceplate_gates.json
python -m enclosure export --part cover --format stl --out /tmp/evie_cover.stl
python -m enclosure serve --host 127.0.0.1 --port 8765
```

Exit code `0` = all applicable gates passed; `2` = a hard gate failed.

## HTTP

Default token: `local-dogfood` (override with `COPILOTCAD_BOT_TOKEN`).

```http
Authorization: Bearer local-dogfood
Content-Type: application/json
```

### Health

```http
GET /health
```

### Generate

```http
POST /v1/generate
{"part": "badge"}
```

`part` is `badge` | `cover` | `faceplate`. Response includes `artifact_id`.

### Validate

```http
POST /v1/validate
{"part": "cover"}
```

Or reuse a solid:

```http
POST /v1/validate
{"artifact_id": "<id-from-generate>"}
```

To check cover holes against faceplate bosses:

```http
POST /v1/validate
{"part": "cover", "mate_artifact_id": "<faceplate-artifact-id>"}
```

`200` = passed; `422` = hard gate failed (body is still the JSON report).

### Export

```http
POST /v1/export
{"part": "badge", "format": "step"}
```

`format`: `step` | `stl` | `iges`. Writes a file and returns `path` + `bytes`.
Optional `dest` and `artifact_id`.

## MCP tool schemas

Machine-readable contracts (same payloads as HTTP):

- `mcps/copilotcad/tools/generate.json`
- `mcps/copilotcad/tools/validate.json`
- `mcps/copilotcad/tools/export.json`

A bot runtime can shell out to `python -m enclosure` or HTTP; both call
`enclosure.service`.

## Suggested Grok flow

1. `POST /v1/generate` `{part: badge}` then `{part: cover}` then `{part: faceplate}`.
2. `POST /v1/validate` each `artifact_id`.
3. If `passed`, `POST /v1/export` `format=step` (and `stl` if a mesh is needed).
4. If `faceplate_fill_band` or `named_cutouts_present` fails, treat the solid as
   a brick / missing-feature reject — do not print.

## Ownership reminder

`owners.product_stl_print_go` in the spec is **not** transferred by a passing
dogfood report. Golden fixtures under `/workspace/evie-stl/` are external and
are not overwritten by this connector.
