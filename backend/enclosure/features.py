"""Named feature records attached to generated enclosure solids."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class NamedFeature:
    """One named cutout, pocket, hole, or boss used by the gate runner."""

    id: str
    type: str
    cx: float
    cy: float
    cz: float
    size: dict[str, float] = field(default_factory=dict)
    probe_points: tuple[tuple[float, float, float], ...] = ()
    mates: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["probe_points"] = [list(point) for point in self.probe_points]
        return payload


def features_by_id(features: list[NamedFeature]) -> dict[str, NamedFeature]:
    return {item.id: item for item in features}
