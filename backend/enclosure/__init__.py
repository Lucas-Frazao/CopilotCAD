"""
Evie enclosure dogfood package — generate / validate / export for Grok bots.

Builders and gates call ``engine.kernel_adapter`` (never OCCT directly).
Product STL print-GO stays with CAD Leader + EVIE Project Leader; this is
platform dogfood only.
"""

from enclosure.service import export_part, generate_part, validate_part

__all__ = ["export_part", "generate_part", "validate_part"]
