#!/usr/bin/env python3
"""
Stop-hook: continue the learning-edition commenting loop until every in-scope file is done.

Reads `.cursor/learning-edition-progress.json` and, when `active` is true and files
remain in `pending`, returns a follow-up message so the agent processes the next batch.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROGRESS_FILE = Path(".cursor/learning-edition-progress.json")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if not PROGRESS_FILE.exists():
        return 0

    try:
        progress = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0

    if not progress.get("active"):
        return 0

    pending: list[str] = progress.get("pending") or []
    if not pending:
        progress["active"] = False
        try:
            PROGRESS_FILE.write_text(
                json.dumps(progress, indent=2) + "\n", encoding="utf-8"
            )
        except OSError:
            pass
        print(
            json.dumps(
                {
                    "followup_message": (
                        "Learning-edition commenting is complete. All in-scope files "
                        "have been commented. Set active=false in progress file if you "
                        "need to re-run."
                    )
                }
            )
        )
        return 0

    batch_size = int(progress.get("batch_size") or 4)
    batch = pending[:batch_size]
    completed_count = len(progress.get("completed") or [])
    total = completed_count + len(pending)

    followup = (
        "Continue the permanent learning-edition commenting loop. "
        f"Progress: {completed_count}/{total} files done. "
        f"Next batch ({len(batch)} files): {', '.join(batch)}. "
        "For each file: rewrite all comments for a beginner (mix line-by-line and "
        "block comments), explain every import, add a plain-English file header. "
        "Update `.cursor/learning-edition-progress.json` (move batch from pending to "
        "completed). Commit after each batch. Do not stop until pending is empty."
    )

    print(json.dumps({"followup_message": followup}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
