"""Workspace edition capability checks (F-027)."""

from __future__ import annotations

import logging
from typing import Any, Literal

from schemas.workspace_manifest import WorkspaceManifest

logger = logging.getLogger(__name__)

CapabilityResult = Literal["ok", "warn"]


def format_limit_warning(limit_key: str, *, limit: int, current: int) -> str:
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
    caps = manifest.capabilities.model_dump()
    return {
        "edition": manifest.edition,
        "capabilities": caps,
        **caps,
    }