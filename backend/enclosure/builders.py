"""
Parametric Evie enclosure builders (badge, cover, faceplate, test brick).

All geometry goes through ``engine.kernel_adapter`` — no OCCT imports here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from enclosure.constants import (
    BADGE_RAISE_MM,
    BADGE_X,
    BADGE_Y,
    BADGE_Z,
    BOSS_BORE_DIA,
    BOSS_HEIGHT_MM,
    BOSS_OUTER_DIA,
    CORNER_OFFSET_MM,
    COVER_HOLE_DIA,
    COVER_Z,
    FACEPLATE_X,
    FACEPLATE_Y,
    FACEPLATE_Z,
    FLOOR_MM,
    LED_CENTER,
    LED_DIA,
    MIC_CENTER,
    MIC_DIA,
    MUTE_CENTER,
    MUTE_DIA,
    PICO_BAY_CENTER,
    PICO_BAY_DEPTH,
    PICO_BAY_SIZE,
    SPEAKER_CENTER,
    SPEAKER_DIA,
    USBC_SIZE,
    USBC_Z,
    WALL_MM,
    corner_xy_centers,
)
from enclosure.features import NamedFeature
from engine import kernel_adapter


@dataclass
class BuiltPart:
    """Generated solid plus the named-feature map the gates consume."""

    part: str
    shape: Any
    features: list[NamedFeature] = field(default_factory=list)


def _centered_box(length: float, width: float, height: float, zmin: float = 0.0) -> Any:
    return kernel_adapter.make_box_at(
        length,
        width,
        height,
        -length / 2.0,
        -width / 2.0,
        zmin,
    )


def _fuse_all(shapes: list[Any]) -> Any:
    if not shapes:
        raise ValueError("nothing to fuse")
    result = shapes[0]
    for extra in shapes[1:]:
        result = kernel_adapter.fuse_shapes(result, extra)
    return result


def _letter_e(origin_x: float, origin_y: float, zmin: float, height: float) -> Any:
    """Block-letter E as fused boxes (letter height 8, width 5.5)."""
    stem = kernel_adapter.make_box_at(1.4, 8.0, height, origin_x, origin_y, zmin)
    bottom = kernel_adapter.make_box_at(5.5, 1.4, height, origin_x, origin_y, zmin)
    mid = kernel_adapter.make_box_at(5.0, 1.4, height, origin_x, origin_y + 3.3, zmin)
    top = kernel_adapter.make_box_at(5.5, 1.4, height, origin_x, origin_y + 6.6, zmin)
    return _fuse_all([stem, bottom, mid, top])


def _letter_v(origin_x: float, origin_y: float, zmin: float, height: float) -> Any:
    """V as a single polygon extruded to ``height`` (width 6, letter height 8)."""
    points = [
        (origin_x + 0.0, origin_y + 8.0),
        (origin_x + 1.7, origin_y + 8.0),
        (origin_x + 3.0, origin_y + 2.2),
        (origin_x + 4.3, origin_y + 8.0),
        (origin_x + 6.0, origin_y + 8.0),
        (origin_x + 3.7, origin_y + 0.0),
        (origin_x + 2.3, origin_y + 0.0),
    ]
    face = kernel_adapter.sketch_polygon(points)
    solid = kernel_adapter.extrude(face, height, "+Z", "add")
    if zmin == 0.0:
        return solid
    return kernel_adapter.translate_shape(solid, 0.0, 0.0, zmin)


def _letter_i(origin_x: float, origin_y: float, zmin: float, height: float) -> Any:
    return kernel_adapter.make_box_at(1.6, 8.0, height, origin_x, origin_y, zmin)


def build_badge() -> BuiltPart:
    """45×15×2 mm plate with raised EVIE legend (0.3 mm)."""
    plate = _centered_box(BADGE_X, BADGE_Y, BADGE_Z, 0.0)

    # Letter row width: E 5.5 + 1.6 + V 6.0 + 1.6 + I 1.6 + 1.6 + E 5.5 = 23.4
    start_x = -11.7
    base_y = -4.0
    zmin = BADGE_Z
    raise_h = BADGE_RAISE_MM
    e1 = _letter_e(start_x, base_y, zmin, raise_h)
    v_solid = _letter_v(start_x + 7.1, base_y, zmin, raise_h)
    letter_i = _letter_i(start_x + 14.7, base_y, zmin, raise_h)
    e2 = _letter_e(start_x + 17.9, base_y, zmin, raise_h)
    letters = _fuse_all([e1, v_solid, letter_i, e2])
    solid = kernel_adapter.fuse_shapes(plate, letters)

    features = [
        NamedFeature(
            id="legend_evie",
            type="raised_text",
            cx=0.0,
            cy=0.0,
            cz=BADGE_Z + BADGE_RAISE_MM / 2.0,
            size={"raise_mm": BADGE_RAISE_MM},
        )
    ]
    return BuiltPart(part="badge", shape=solid, features=features)


def build_cover() -> BuiltPart:
    """115×65×1.75 mm lid with the 4-hole pattern that mates faceplate bosses."""
    plate = _centered_box(FACEPLATE_X, FACEPLATE_Y, COVER_Z, 0.0)
    solid = kernel_adapter.hole_pattern_corners(plate, COVER_HOLE_DIA, CORNER_OFFSET_MM)

    features: list[NamedFeature] = []
    for index, (cx, cy) in enumerate(corner_xy_centers(FACEPLATE_X, FACEPLATE_Y, CORNER_OFFSET_MM)):
        features.append(
            NamedFeature(
                id=f"cover_hole_{index + 1}",
                type="hole",
                cx=cx,
                cy=cy,
                cz=COVER_Z / 2.0,
                size={"diameter": COVER_HOLE_DIA},
                probe_points=((cx, cy, COVER_Z / 2.0),),
                mates="faceplate.corner_bosses",
            )
        )
    return BuiltPart(part="cover", shape=solid, features=features)


def _cut_through_hole(solid: Any, cx: float, cy: float, diameter: float, zmax: float) -> Any:
    radius = diameter / 2.0
    tool = kernel_adapter.make_cylinder(radius, zmax + 0.4, cx, cy, -0.2, "+Z")
    return kernel_adapter.cut_shape(solid, tool)


def build_faceplate() -> BuiltPart:
    """Open tray: 115×65×28 body, walls/floor, named cutouts, corner bosses."""
    outer = _centered_box(FACEPLATE_X, FACEPLATE_Y, FACEPLATE_Z, 0.0)
    inner_x = FACEPLATE_X - 2.0 * WALL_MM
    inner_y = FACEPLATE_Y - 2.0 * WALL_MM
    inner_z = FACEPLATE_Z - FLOOR_MM + 1.0
    inner = kernel_adapter.make_box_at(
        inner_x,
        inner_y,
        inner_z,
        -inner_x / 2.0,
        -inner_y / 2.0,
        FLOOR_MM,
    )
    tray = kernel_adapter.cut_shape(outer, inner)

    pico_x, pico_y = PICO_BAY_SIZE
    pico_cx, pico_cy = PICO_BAY_CENTER
    pico_tool = kernel_adapter.make_box_at(
        pico_x,
        pico_y,
        PICO_BAY_DEPTH + 0.2,
        pico_cx - pico_x / 2.0,
        pico_cy - pico_y / 2.0,
        FLOOR_MM - PICO_BAY_DEPTH,
    )
    tray = kernel_adapter.cut_shape(tray, pico_tool)

    for cx, cy, dia in (
        (*MUTE_CENTER, MUTE_DIA),
        (*MIC_CENTER, MIC_DIA),
        (*SPEAKER_CENTER, SPEAKER_DIA),
        (*LED_CENTER, LED_DIA),
    ):
        tray = _cut_through_hole(tray, cx, cy, dia, FACEPLATE_Z)

    usbc_w, usbc_h = USBC_SIZE
    usbc = kernel_adapter.make_box_at(
        usbc_w,
        WALL_MM + 2.0,
        usbc_h,
        -usbc_w / 2.0,
        -FACEPLATE_Y / 2.0 - 1.0,
        USBC_Z,
    )
    tray = kernel_adapter.cut_shape(tray, usbc)

    boss_solids: list[Any] = []
    for cx, cy in corner_xy_centers(FACEPLATE_X, FACEPLATE_Y, CORNER_OFFSET_MM):
        boss = kernel_adapter.make_cylinder(
            BOSS_OUTER_DIA / 2.0,
            BOSS_HEIGHT_MM,
            cx,
            cy,
            FLOOR_MM,
            "+Z",
        )
        boss_solids.append(boss)
    tray = _fuse_all([tray, *boss_solids])

    for cx, cy in corner_xy_centers(FACEPLATE_X, FACEPLATE_Y, CORNER_OFFSET_MM):
        tray = _cut_through_hole(tray, cx, cy, BOSS_BORE_DIA, FACEPLATE_Z)

    floor_probe_z = FLOOR_MM / 2.0
    pico_probe_z = FLOOR_MM - PICO_BAY_DEPTH / 2.0
    usbc_probe = (0.0, -FACEPLATE_Y / 2.0 + WALL_MM / 2.0, USBC_Z + USBC_SIZE[1] / 2.0)

    features = [
        NamedFeature(
            id="pico_bay",
            type="pocket",
            cx=pico_cx,
            cy=pico_cy,
            cz=pico_probe_z,
            size={"x": pico_x, "y": pico_y},
            probe_points=((pico_cx, pico_cy, pico_probe_z),),
        ),
        NamedFeature(
            id="mute",
            type="boss_bore",
            cx=MUTE_CENTER[0],
            cy=MUTE_CENTER[1],
            cz=floor_probe_z,
            size={"diameter": MUTE_DIA},
            probe_points=((MUTE_CENTER[0], MUTE_CENTER[1], floor_probe_z),),
        ),
        NamedFeature(
            id="mic",
            type="hole",
            cx=MIC_CENTER[0],
            cy=MIC_CENTER[1],
            cz=floor_probe_z,
            size={"diameter": MIC_DIA},
            probe_points=((MIC_CENTER[0], MIC_CENTER[1], floor_probe_z),),
        ),
        NamedFeature(
            id="speaker",
            type="hole",
            cx=SPEAKER_CENTER[0],
            cy=SPEAKER_CENTER[1],
            cz=floor_probe_z,
            size={"diameter": SPEAKER_DIA},
            probe_points=((SPEAKER_CENTER[0], SPEAKER_CENTER[1], floor_probe_z),),
        ),
        NamedFeature(
            id="status_led",
            type="hole",
            cx=LED_CENTER[0],
            cy=LED_CENTER[1],
            cz=floor_probe_z,
            size={"diameter": LED_DIA},
            probe_points=((LED_CENTER[0], LED_CENTER[1], floor_probe_z),),
        ),
        NamedFeature(
            id="hid_usbc",
            type="edge_cutout",
            cx=0.0,
            cy=-FACEPLATE_Y / 2.0 + WALL_MM / 2.0,
            cz=USBC_Z + USBC_SIZE[1] / 2.0,
            size={"x": USBC_SIZE[0], "y": USBC_SIZE[1]},
            probe_points=(usbc_probe,),
        ),
    ]
    for index, (cx, cy) in enumerate(corner_xy_centers(FACEPLATE_X, FACEPLATE_Y, CORNER_OFFSET_MM)):
        features.append(
            NamedFeature(
                id=f"corner_boss_{index + 1}",
                type="boss",
                cx=cx,
                cy=cy,
                cz=FLOOR_MM + BOSS_HEIGHT_MM / 2.0,
                size={"diameter": BOSS_OUTER_DIA, "count": 4},
                mates="cover.holes",
            )
        )
    return BuiltPart(part="faceplate", shape=tray, features=features)


def build_approx_brick(fill: float = 0.80) -> BuiltPart:
    """
    ~``fill`` solid brick with the faceplate envelope.

    Used as a negative fixture: an 80% brick must fail ``faceplate_fill_band``.
    """
    if not 0.05 < fill < 0.99:
        raise ValueError(f"fill must be between 0.05 and 0.99, got {fill}")

    outer = _centered_box(FACEPLATE_X, FACEPLATE_Y, FACEPLATE_Z, 0.0)
    cavity_fraction = 1.0 - fill
    # Keep a rectangular cavity centered in XY, sitting on a thin floor.
    cavity_x = FACEPLATE_X * 0.55
    cavity_y = FACEPLATE_Y * 0.55
    cavity_z = (FACEPLATE_X * FACEPLATE_Y * FACEPLATE_Z * cavity_fraction) / (cavity_x * cavity_y)
    cavity_z = min(cavity_z, FACEPLATE_Z * 0.9)
    cavity = kernel_adapter.make_box_at(
        cavity_x,
        cavity_y,
        cavity_z,
        -cavity_x / 2.0,
        -cavity_y / 2.0,
        FACEPLATE_Z - cavity_z,
    )
    brick = kernel_adapter.cut_shape(outer, cavity)
    return BuiltPart(part="brick", shape=brick, features=[])


BUILDERS = {
    "badge": build_badge,
    "cover": build_cover,
    "faceplate": build_faceplate,
    "brick": build_approx_brick,
}


def build_part(part: str) -> BuiltPart:
    try:
        builder = BUILDERS[part]
    except KeyError as exc:
        raise ValueError(f"unknown part {part!r}; expected one of {sorted(BUILDERS)}") from exc
    return builder()
