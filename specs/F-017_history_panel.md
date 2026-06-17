# F-017 — History panel

## Summary

Add a **History panel** showing what happened to the active part: chat actions, geometry changes, and assumption updates — with timestamps, summaries, and diffs.

**Status:** Pending approval.

## Why this matters

CAD without history is hard to trust. Users need to see **what CopilotCAD did** after each chat turn — the same transparency as “git log” or an IDE timeline, but for modeling actions.

## Key concepts

| Term | Plain meaning |
|------|----------------|
| **Action history** | Log of user prompts, IR summaries, and execution outcomes. |
| **Feature history** | Geometry-level timeline (which modeling steps were added/changed). |
| **history.json** | Per-part JSON file on disk storing history entries (F-002). |
| **Diff** | What changed compared to the previous state (steps added, assumptions updated). |

## What the user will experience

1. “History” tab with two sub-tabs: **Actions** and **Features**.
2. **Actions** — Each chat-driven change: time, short summary, link to chat message, assumption changes noted.
3. **Features** — Modeling steps/features in order (sketch, extrude, holes, etc.).
4. Selecting an entry shows expanded diff detail (read-only).
5. New chat execution appends entries automatically.

## What we will build

### Backend

- Ensure `execute_intent` and slash handlers **append** to `parts/<id>/history.json` with structured entries.
- **`get_part_history(part_id)`** — Return parsed history for UI.

### Frontend

| Piece | Purpose |
|-------|---------|
| `HistoryPanel.tsx` | Replaces placeholder; tabbed Actions / Features |
| Entry component | Timestamp, summary, expandable diff |
| Sync | Refresh on execute; filter by `activePartId` |

### History entry schema (MVP)

```json
{
  "id": "h1",
  "timestamp": "ISO-8601",
  "type": "execute",
  "summary": "Added corner holes",
  "step_ids": ["s3"],
  "assumption_ids_changed": ["a2"]
}
```

## Acceptance criteria

1. After golden path (F-012), history.json contains entries matching chat actions.
2. Panel shows entries for active part only (switch part → switch history).
3. Action tab links to chat when message id stored.
4. Feature tab lists modeling steps from IR/execution.
5. `/history` slash command (F-014) shows same data in chat or focuses panel.

## Dependencies

- **F-002** — history.json read/write.
- **F-008** — Execute events to log.
- **F-015** — Active part selection.

## Out of scope (not in F-017)

- Undo/redo from history UI.
- Global project history (part-scoped only in MVP).
- Diff visualization in 3D viewport.

## Notes for reviewers

History is **audit trail**, not version control. It complements chat diffs (F-008) with a persistent per-part log.
