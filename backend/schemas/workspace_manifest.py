"""Workspace manifest schema — edition and capabilities."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Edition = Literal["community", "pro", "team"]


class Capabilities(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    max_assembly_parts: int = 5
    advanced_pdd: bool = False
    scripting: bool = False
    plugin_marketplace: bool = False


class WorkspaceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    project_name: str
    version: str = "0.1"
    edition: Edition = "community"
    capabilities: Capabilities = Field(default_factory=Capabilities)


def default_capabilities() -> Capabilities:
    return Capabilities()
