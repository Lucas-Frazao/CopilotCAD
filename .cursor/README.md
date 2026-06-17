# CopilotCAD Cursor automations

Project-level skills, hooks, and MCP configuration for spec-driven development on CopilotCAD.

## Quick start

| What | How |
|------|-----|
| Run the full pipeline (spec → implement → next) | `/feature-pipeline-loop` — see skill for one-iteration vs unattended prompts |
| Implement a feature | Chat: **Implement F-004** (after spec approved) or invoke skill **implement-f-feature** |
| Run backend tests | `/verify-backend` or `.cursor/skills/verify-backend/scripts/verify-backend.ps1` |
| Review a spec before coding | `/spec-reviewer` with feature id |
| Review a PR for architecture | `/dual-stack-reviewer` |
| Set scoped edits | Edit `.cursor/feature-scope.json` (see below) |

Restart Cursor after changing hooks or MCP config so they reload.

---

## MCP servers

Configured in `.cursor/mcp.json`:

### GitHub

**Setup:**

1. Create a GitHub PAT with `repo` scope (or minimal scopes for PR/issues).
2. Set environment variable **before starting Cursor**:

   ```powershell
   [System.Environment]::SetEnvironmentVariable("GITHUB_PERSONAL_ACCESS_TOKEN", "ghp_...", "User")
   ```

3. Restart Cursor.
4. Enable the **github** MCP server in **Cursor Settings → MCP**.

**Use:** Ask the agent to list PR checks, read issue context, or summarize PR comments on this repo.

### context7

**Setup:** Enable **context7** in **Cursor Settings → MCP** (uses `npx`; no token required for basic use).

**Use:** Ask for live docs when implementing OCCT, Electron IPC, Pydantic, Three.js, or Anthropic SDK — e.g. "use context7 for pythonOCC STEP export API."

---

## Skills

Project skills live in `.cursor/skills/`.

### `implement-f-feature`

**Invoke:** Type `/implement-f-feature` in chat, or say "implement F-004 per the approved spec."

**Does:** Reads spec → sets feature scope → implements per contract → runs pytest → updates spec status.

### `verify-backend`

**Invoke:** `/verify-backend` (user-only; won't auto-run).

**Does:** Runs `pytest -v` from `backend/` using `.venv`.

```powershell
.cursor\skills\verify-backend\scripts\verify-backend.ps1
```

### `spec-reviewer`

**Invoke:** `/spec-reviewer` then provide feature id (e.g. "review F-003 spec").

**Does:** Checklist review against roadmap and architecture; outputs APPROVE/REVISE/CONFLICT.

### `dual-stack-reviewer`

**Invoke:** `/dual-stack-reviewer` before merging an F-0xx branch.

**Does:** Greps for OCCT import leaks, IPC drift, renderer security, frontend file writes.

---

## Hooks

Configured in `.cursor/hooks.json`.

### Ruff after Python edit

When a file under `backend/` is edited, runs:

```text
ruff check --fix <file>
```

Uses `backend/.venv/Scripts/ruff.exe` if present, else `ruff` on PATH.

**Install Ruff (optional but recommended):**

```powershell
cd backend
uv pip install ruff
```

**Debug:** Cursor **Settings → Hooks** or Hooks output channel.

### Spec scope guard

On **Write / StrReplace / ApplyPatch / EditNotebook**:

- **Blocks** edits to `docs/feature_roadmap.md` and `docs/architecture.md` (always).
- **Asks** for confirmation if `.cursor/feature-scope.json` has `feature` + `allowed_prefixes` and the edit path is outside allowed prefixes.

**Set scope for a feature:**

```json
{
  "feature": "F-004",
  "allowed_prefixes": ["backend/engine/", "tests/backend/", "specs/"],
  "blocked_prefixes": ["docs/feature_roadmap.md", "docs/architecture.md"],
  "notes": "Backend-only; no frontend."
}
```

Clear `allowed_prefixes` to `[]` when not working on a scoped feature (no path restriction except blocked docs).

---

## Rules

`.cursor/rules/spec-driven-development.mdc` — always-on reminder for spec-first workflow.

---

## Claude Code plugins (optional, not in repo)

If you also use **Claude Code** CLI:

- **feature-dev** — planning checklists for large features (F-007–F-012).
- **frontend-design** — IDE panel UI patterns for upcoming frontend work.

Install from Claude Code marketplace: `/plugin` or Extensions.

Equivalent in Cursor: use `implement-f-feature` + `dual-stack-reviewer` skills above.

---

## Claude Code parity

This repo also ships Claude Code config:

| Asset | Path |
|-------|------|
| Project memory | `CLAUDE.md` |
| MCP (team) | `.mcp.json` |
| Hooks | `.claude/settings.json` → same scripts under `.cursor/hooks/` |
| Skills | `.claude/skills/` (mirror of `.cursor/skills/`) |
| Subagents | `.claude/agents/spec-reviewer.md`, `dual-stack-reviewer.md` |

**Cursor** uses `.cursor/hooks.json` and `.cursor/mcp.json`. **Claude Code** uses `.claude/settings.json` and `.mcp.json`.

Enable plugins in Claude Code (you may already have `feature-dev` globally):

```text
/plugin → feature-dev
/plugin → frontend-design
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Hooks not running | Save `hooks.json`, restart Cursor, check Hooks tab |
| MCP github fails | Set `GITHUB_PERSONAL_ACCESS_TOKEN`, restart Cursor |
| Ruff hook silent | Install ruff in `backend/.venv` |
| OCCT tests skip | Expected on Windows ARM; use x64 Python for geometry tests |
| Scope guard too aggressive | Clear `allowed_prefixes` in `feature-scope.json` |
