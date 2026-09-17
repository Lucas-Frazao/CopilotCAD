"""Shared design-mm constants for Evie v3 enclosure builders."""

from __future__ import annotations

# Faceplate / cover XY (design mm). Cover Z is thinner; faceplate body Z=28.
FACEPLATE_X = 115.0
FACEPLATE_Y = 65.0
FACEPLATE_Z = 28.0

COVER_Z = 1.75
COVER_Z_MIN = 1.5
COVER_Z_MAX = 2.0

BADGE_X = 45.0
BADGE_Y = 15.0
BADGE_Z = 2.0
BADGE_RAISE_MM = 0.3

# Tray shell — tuned so solid_volume_fraction lands in 0.20–0.25.
WALL_MM = 2.2
FLOOR_MM = 4.8

# M2 / M2.5 class corner pattern (same XY on faceplate bosses and cover holes).
CORNER_OFFSET_MM = 5.5
COVER_HOLE_DIA = 2.8
BOSS_OUTER_DIA = 6.0
BOSS_HEIGHT_MM = 8.0
BOSS_BORE_DIA = 2.4

# Named faceplate features (XY origin at plate center, Z=0 at body bottom).
PICO_BAY_SIZE = (51.0, 21.0)
PICO_BAY_DEPTH = 4.0
PICO_BAY_CENTER = (12.0, 0.0)

MUTE_DIA = 10.0
MUTE_CENTER = (-38.0, 16.0)

MIC_DIA = 6.0
MIC_CENTER = (-38.0, 0.0)

SPEAKER_DIA = 8.0
SPEAKER_CENTER = (-38.0, -16.0)

LED_DIA = 2.0
LED_CENTER = (38.0, 16.0)

USBC_SIZE = (9.0, 3.5)  # width x height
USBC_Z = 6.0

EXTENTS_TOL_MM = 1.0
HOLE_ALIGN_TOL_MM = 0.5
POINT_PROBE_TOL = 1.0e-3


def corner_xy_centers(length: float, width: float, offset: float) -> list[tuple[float, float]]:
    """Four corner centers for a plate centered on the origin."""
    hx = length / 2.0
    hy = width / 2.0
    return [
        (hx - offset, hy - offset),
        (-hx + offset, hy - offset),
        (hx - offset, -hy + offset),
        (-hx + offset, -hy + offset),
    ]
