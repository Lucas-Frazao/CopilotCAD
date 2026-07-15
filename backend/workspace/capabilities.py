"""
Workspace Capabilities — Edition Limit Checks (F-027)
=====================================================

WHAT THIS FILE DOES
-------------------
Reads limits from ``copilotcad.json`` (community vs paid edition) and soft-checks
whether an action exceeds them. MVP logs a warning but does not block.

EXAMPLE LIMITS
--------------
max_parts, max_assemblies — compared against current_count in check_capability.

RETURNS
-------
"ok"   — within limit or no limit defined
"warn" — over limit (logged via Python logging)
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from schemas.workspace_manifest import WorkspaceManifest

logger = logging.getLogger(__name__)

CapabilityResult = Literal["ok", "warn"]


def format_limit_warning(limit_key: str, *, limit: int, current: int) -> str:
    """Human-readable message for UI or logs."""
    return (
        f"Community edition limit reached for {limit_key} "
        f"({current}/{limit}). Upgrade for higher limits."
    )


def check_capability(
    manifest: WorkspaceManifest,
    limit_key: str,
    *,
    current_count: int,
) -> CapabilityResult:
    """Soft-limit check — logs a warning but does not raise in MVP."""
    caps = manifest.capabilities
    limit = getattr(caps, limit_key, None)
    if not isinstance(limit, int):
        return "ok"

    if current_count > limit:
        message = format_limit_warning(limit_key, limit=limit, current=current_count)
        logger.warning(message)
        return "warn"
    return "ok"


def capabilities_payload(manifest: WorkspaceManifest) -> dict[str, Any]:
    """Flatten manifest edition + capabilities for JSON-RPC responses."""
    caps = manifest.capabilities.model_dump()
    return {
        "edition": manifest.edition,
        "capabilities": caps,
        **caps,
    }
