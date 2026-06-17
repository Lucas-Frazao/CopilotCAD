# F-005 — LLM adapter and IR generation

## Summary

Implement the LLM side of the Intent IR compiler: abstract `LLMAdapter`, `ClaudeAdapter` using the Anthropic Python SDK, a system prompt that encodes IR rules and the MVP step catalog, parsing of LLM JSON output, and a `compile_intent` pipeline that returns a validated `IntentIR` or structured errors. Expose compilation via Python API and JSON-RPC for tests. `LocalAdapter` remains a stub.

**Status:** Implemented (live API test skips without `ANTHROPIC_API_KEY`).

## Context and goals

F-001 defines and validates Intent IR; F-004 executes validated IR. F-005 fills the gap: natural language → structured IR object via Claude.

Goals:

- `LLMAdapter` abstract interface: given user message + optional project context, return raw structured JSON from the model.
- `ClaudeAdapter`: call Anthropic API with system prompt + user message; require JSON object response.
- System prompt includes: product behavior rules, slim IR field summary, `MVP_STEP_OPS` list, JSON-only output instruction.
- `ir/parser.py`: extract JSON from model text (plain JSON or fenced code blocks) → `dict`.
- `compile_intent(message, context, adapter)`: adapter → parse → `validate_intent_ir` → `IntentIR` or `CompileError` with parse/validation/API details.
- JSON-RPC `compile_intent` on `main.py` for stdio testing (no `chat.send` yet).
- Unit tests with **mocked** Claude responses for five representative part prompts; optional live test skipped without `ANTHROPIC_API_KEY`.

## Non-goals

- **IR execution** — no changes to `engine/executor.py` or `execute_intent` (F-004).
- **Problems engine** — no post-compile validation (F-006).
- **Frontend / `chat.send` IPC** — full chat wiring is F-007; F-005 adds `compile_intent` only.
- **Project file writes** — context injection may include read-only dict fields passed by caller; no workspace loading in F-005.
- **Risk classifier / approval** — no `ir.pending` (F-022).
- **Local model inference** — `LocalAdapter` raises `NotImplementedError` or remains explicit stub.
- **Editing** `docs/feature_roadmap.md` or `docs/architecture.md`.

## Requirements

### `backend/llm/adapter.py`

Abstract base class `LLMAdapter`:

```python
def generate_structured_json(
    self,
    user_message: str,
    project_context: dict[str, Any] | None = None,
) -> str:
    """Return raw text expected to contain a JSON object."""
```

`project_context` is optional opaque dict (e.g. `active_part_id`, `spec_snippet`) serialized into the user or system side per adapter design.

### `backend/llm/claude_adapter.py`

- Uses `anthropic` SDK (`Anthropic` client).
- API key from environment variable `ANTHROPIC_API_KEY`; raise clear `LLMConfigurationError` if missing when adapter is constructed or on first call.
- Model: `claude-sonnet-4-20250514` or configurable via env `COPILOTCAD_CLAUDE_MODEL` with sensible default documented in module.
- Request structured JSON: use API JSON mode / `response_format` or prompt contract requiring a single JSON object (no markdown prose).
- On API errors, wrap in `LLMError` with message (no silent failure).

### `backend/llm/local_adapter.py`

Stub: `generate_structured_json` raises `NotImplementedError` with message pointing to F-005 non-goals.

### `backend/llm/prompts.py` (or `llm/system_prompt.py`)

Function `build_system_prompt()` returning string including:

- Role: CopilotCAD IR compiler; output **only** valid JSON matching Intent IR.
- List of intent `type` values from `schemas/intent_ir.py`.
- List of valid `steps[].op` from `MVP_STEP_OPS`.
- Required top-level fields: `type`, `prompt`, `summary`, `target`, etc.
- Step dependency rules: `from` references prior step ids.
- Units: millimeters for dimensions unless stated otherwise.

Keep prompt maintainable; may reference golden mounting plate as example shape (not full dump of all Pydantic schemas).

### `backend/ir/parser.py`

```python
def parse_llm_json(text: str) -> dict[str, Any]
```

- Strip whitespace; accept raw JSON object string.
- If fenced block present (```json ... ```), extract inner JSON.
- On `json.JSONDecodeError`, raise `IRParseError` with snippet context.

### `backend/ir/compiler.py`

```python
class CompileError(Exception):
    error_type: Literal["parse", "validation", "llm"]
    message: str
    details: dict[str, Any]

def compile_intent(
    user_message: str,
    adapter: LLMAdapter,
    project_context: dict[str, Any] | None = None,
) -> IntentIR
```

Flow: `adapter.generate_structured_json` → `parse_llm_json` → `validate_intent_ir`. Map `IRParseError`, `IntentIRValidationError`, `LLMError` to `CompileError`.

### JSON-RPC: `compile_intent`

In `backend/main.py`:

```python
@method
def compile_intent(message: str, context: dict | None = None) -> Success | Error
```

- Uses default `ClaudeAdapter` instance (lazy singleton or per-request).
- On success: return `IntentIR.model_dump()` (JSON-serializable dict).
- On `CompileError`: return `Error` with structured `details`.
- On missing API key: return `Error` with configuration message.

`ping` and `execute_intent` remain unchanged.

### Tests (`tests/backend/test_llm_compile.py`)

**Mocked tests (must pass without API key):**

1. Mounting plate prompt → mock JSON matching `mounting_plate_ir()` → `compile_intent` succeeds.
2. Simple plate / box variant prompt → mock valid minimal `part_create` IR.
3. Invalid JSON from mock → `CompileError` type `parse`.
4. Valid JSON but invalid op → `CompileError` type `validation`.
5. Parser unit tests: raw JSON and fenced JSON for `parse_llm_json`.

Use `unittest.mock` to patch `ClaudeAdapter.generate_structured_json` (or Anthropic client).

**Optional live test:**

- `@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"))` 
- One real call with mounting plate English prompt; assert `validate_intent_ir` would accept result (lenient:至少 1 step with sketch or extrude).

### Dependencies

- `anthropic>=0.28` already in `pyproject.toml`.

## Data model

### Error types

| Exception | When |
|-----------|------|
| `LLMConfigurationError` | Missing API key |
| `LLMError` | Anthropic API failure |
| `IRParseError` | JSON parse failure |
| `IntentIRValidationError` | Existing F-001 validator |
| `CompileError` | Unified compile pipeline wrapper |

## Acceptance criteria

1. `LLMAdapter` ABC and `ClaudeAdapter` implemented per Requirements.
2. `build_system_prompt()` includes MVP step catalog and IR field rules.
3. `parse_llm_json` handles plain and fenced JSON; raises `IRParseError` on garbage.
4. `compile_intent` returns validated `IntentIR` for mocked mounting plate JSON.
5. Parse and validation failures return structured `CompileError` (not uncaught exceptions).
6. JSON-RPC `compile_intent` works in stdio dispatch test (mocked adapter or injected test path).
7. Five representative mocked prompt scenarios pass in pytest without network.
8. Optional live test skips without `ANTHROPIC_API_KEY`.
9. No OCCT imports added outside `kernel/occt_bridge.py`.
10. No `frontend/` changes.
11. Existing F-001–F-004 tests still pass.

## Dependencies

- **F-001** — `IntentIR`, `validate_intent_ir`, `MVP_STEP_OPS`, mounting plate IR fixture.
- **F-004** — not invoked in F-005 (compile only).

## Open questions for implementer (defaults if user does not override)

| Question | Default in spec |
|----------|-----------------|
| Claude model id | `claude-sonnet-4-20250514` or env override |
| Live API tests in CI | Skipped without key; mocked tests required |
| `ir/models.py` placeholder | Leave as stub or re-export from `schemas.intent_ir` — prefer no duplicate models |
