"""Stdio MCP entry for Grok CAD Bot / CoS.

Adds the repo ``backend/`` package path, then runs the enclosure MCP loop.
Install by pointing the host at this file — see ``docs/dogfood/grok_cad_bot_loop.md``.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from enclosure.mcp_server import main  # noqa: E402  # path bootstrap above

if __name__ == "__main__":
    main()
