# F-005 — LLM adapter and IR generation

## Summary

Turn **English chat text into validated Intent IR** using Claude (Anthropic API): system prompt, JSON parsing, validation, and structured errors when the model or schema fails.

**Status:** Implemented (live API test skips without `ANTHROPIC_API_KEY`).

## Why this matters

Users speak English; the engine speaks Intent IR. F-005 is the **compiler front-end** — the bridge from natural language to the strict plan F-004 executes. Without it, chat could only run pre-written test IRs.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **LLM** | Large Language Model — AI that generates text (here, JSON plans). |
| **ClaudeAdapter** | CopilotCAD’s connector to Anthropic’s Claude API. |
| **System prompt** | Instructions telling the model how to format Intent IR and which ops exist. |
| **compile_intent** | Pipeline: user message → LLM → parse JSON → validate → `IntentIR` object. |
| **CompileError** | Unified failure: parse, validation, or API/configuration errors. |
| **ANTHROPIC_API_KEY** | Environment variable holding your Anthropic API key for live calls. |

## What the user will experience

After F-007/F-008 wire the UI, users type a part description and the backend **compiles** it into a plan before executing. In F-005 alone:

- Developers call `compile_intent("Create a mounting plate…")` in Python or JSON-RPC `compile_intent`.
- Success returns full IR dict; failure returns structured error (missing API key, bad JSON, invalid op).

## What we will build

### `backend/llm/adapter.py`

Abstract `LLMAdapter.generate_structured_json(message, context?)`.

### `backend/llm/claude_adapter.py`

- Anthropic SDK, API key from environment.
- Model configurable (e.g. Claude Sonnet family).
- Errors wrapped as `LLMError` / `LLMConfigurationError`.

### `backend/llm/prompts.py`

- `build_system_prompt()` — IR fields, intent types, full `MVP_STEP_OPS` list, JSON-only output rules, mounting plate example shape.

### `backend/ir/parser.py`

- `parse_llm_json(text)` — raw JSON or ```json fenced blocks → dict.
- `IRParseError` on garbage input.

### `backend/ir/compiler.py`

- `compile_intent(message, adapter, context?)` → `IntentIR` or `CompileError`.

### JSON-RPC: `compile_intent`

- Params: `message`, optional `context`.
- Success: IR as JSON dict (`model_dump`).
- Failure: structured `CompileError` details.

### `backend/llm/local_adapter.py`

Stub — `NotImplementedError` (local models deferred).

### Tests (`tests/backend/test_llm_compile.py`)

Mocked Claude for mounting plate, simple box, parse errors, validation errors, JSON-RPC smoke. Optional live test with API key.

## Acceptance criteria

1. `ClaudeAdapter` and `LLMAdapter` implemented.
2. System prompt includes step catalog and IR rules.
3. `parse_llm_json` handles plain and fenced JSON.
4. Mocked `compile_intent` returns validated IR for golden fixture.
5. Parse/validation failures are `CompileError`, not uncaught exceptions.
6. JSON-RPC `compile_intent` works in stdio tests (mocked).
7. Five+ mocked scenarios pass without network.
8. Live test skips without API key.
9. No frontend changes; F-001–F-004 tests still pass.

## Dependencies

- **F-001** — `validate_intent_ir`, `MVP_STEP_OPS`, fixtures.

## Out of scope (not in F-005)

- Executing IR (F-004 — separate RPC).
- Problems engine (F-006).
- Frontend chat wiring (F-007+).
- Reading workspace files for context (optional dict only).
- Local model inference.
- IR sanitizer for LLM drift (added later on implementation branch).

## Notes for reviewers

F-005 quality depends on **prompt + validator**. Live LLM output may need sanitizer/normalization (separate work) even when F-005 is “done.”
