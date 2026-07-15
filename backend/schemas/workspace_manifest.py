# =============================================================================
# Workspace Manifest Schema — Edition and Capabilities
# =============================================================================
#
# WHAT THIS FILE DEFINES
# ----------------------
# Every CopilotCAD project folder has a manifest (JSON) describing:
#   - project_name, schema version
#   - edition (community / pro / team)
#   - capabilities (limits and feature flags)
#
# The backend reads this on load_workspace() and enforces limits via
# workspace.capabilities (e.g. max_assembly_parts).
# =============================================================================

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Product tier — controls default capability limits
Edition = Literal["community", "pro", "team"]


class Capabilities(BaseModel):
    """
    Feature flags and numeric limits for this workspace edition.

    Defaults match the community edition unless overridden in the manifest.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    max_assembly_parts: int = 5
    advanced_pdd: bool = False
    scripting: bool = False
    plugin_marketplace: bool = False


class WorkspaceManifest(BaseModel):
    """Top-level manifest stored when create_workspace() initializes a project."""

    model_config = ConfigDict(extra="forbid", strict=True)

    project_name: str
    version: str = "0.1"
    edition: Edition = "community"
    capabilities: Capabilities = Field(default_factory=Capabilities)


def default_capabilities() -> Capabilities:
    """Return fresh community-edition capabilities (used when manifest omits them)."""
    return Capabilities()
