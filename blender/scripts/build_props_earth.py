"""Builds blender/sources/props/earth.blend: Earth POI props (B-020) for the abandoned coastal
launch complex and the Survey Archive (Bible §7.1).

Same conventions as build_props_common.py: one collection per prop (`prop_<name>`), real scale
(PPU 128, so ≤ 4 m to fit the 512 px cap), standing on z = 0, origin = bottom centre.
Weathered, documentary-naturalistic: faded paint with heavy rust grime. The launch structures
are stackable sections, not whole towers: `launch_gantry` is a 3.8 m lattice segment that tiles
vertically (top and bottom chords line up), `launch_tower_ruin` its broken top. `beacon`
keeps all emission in the lamp so UNITY can pulse it. Interactables (archive_door,
archive_terminal, beacon) carry meridian_rim 0.1 -> mask R. Deterministic:

  blender --background --factory-startup --python blender/scripts/build_props_earth.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import box, cyl, flat_material, paint_material, sphere  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "earth.blend")
INTERACTABLE = {"archive_door", "archive_terminal", "beacon"}


def materials(rim):
    M = {
        "steel": paint_material("weathered_steel", (164, 160, 150), (128, 92, 66)),       # faded paint over rust
        "rust": paint_material("rust", (128, 84, 58), (96, 62, 44), seams=False),
        "concrete": paint_material("concrete", (150, 148, 140), (118, 114, 106), seams=True),
        "door": paint_material("blast_door", (120, 124, 116), (92, 90, 84)),
        "dark": flat_material("dark", (48, 50, 52), metallic=0.3, rough=0.6),
        "yellow": flat_material("hazard_yellow", (196, 152, 44), rough=0.7),
        "black": flat_material("hazard_black", (36, 34, 32), rough=0.7),
        "screen": flat_material("screen", (20, 40, 46), emit=(90, 220, 200), strength=0.9, rough=0.2),
        "panel": flat_material("panel_light", (40, 60, 40), emit=(120, 255, 150), strength=0.8),
        "beacon": flat_material("beacon_lamp", (120, 30, 20), emit=(255, 60, 40), strength=1.0, rough=0.2),
    }
    for m in M.values():
        m["meridian_rim"] = rim
    return M


def strut(c, name, p0, p1, w, m):
    """A square strut between two points in the XZ plane (lattice member)."""
    dx, dz = p1[0] - p0[0], p1[1] - p0[1]
    length = math.hypot(dx, dz)
    ang = math.atan2(dx, dz)
    box(name, ((p0[0] + p1[0]) / 2, 0, (p0[1] + p1[1]) / 2), (w, w, length), c, m, bevel=w * 0.15, rot=(0, ang, 0))


def launch_gantry(c, M):
    H, Wd = 3.8, 2.4
    for x in (-Wd / 2, Wd / 2):                                   # main legs
        box(f"leg_{x}", (x, 0, H / 2), (0.16, 0.16, H), c, M["steel"], bevel=0.02)
    for z in (0.08, H / 2, H - 0.08):                             # chords line up when stacked
        box(f"chord_{z}", (0, 0, z), (Wd, 0.12, 0.12), c, M["steel"], bevel=0.015)
    for k, (z0, z1) in enumerate(((0.08, H / 2), (H / 2, H - 0.08))):
        strut(c, f"brace_a{k}", (-Wd / 2, z0), (Wd / 2, z1), 0.08, M["rust"])
        strut(c, f"brace_b{k}", (Wd / 2, z0), (-Wd / 2, z1), 0.08, M["rust"])
    box("walkway", (0.0, -0.15, H / 2 + 0.07), (Wd + 0.5, 0.5, 0.06), c, M["dark"], bevel=0.01)
    for x in (-Wd / 2 - 0.2, Wd / 2 + 0.2):
        box(f"rail_post_{x}", (x, -0.35, H / 2 + 0.45), (0.04, 0.04, 0.75), c, M["yellow"], bevel=0.005)
    box("rail", (0, -0.35, H / 2 + 0.8), (Wd + 0.44, 0.04, 0.04), c, M["yellow"], bevel=0.005)


def launch_tower_ruin(c, M):
    H, Wd = 3.0, 2.4
    box("leg_l", (-Wd / 2, 0, H / 2), (0.16, 0.16, H), c, M["rust"], bevel=0.02)
    box("leg_r", (Wd / 2, 0, 1.1), (0.16, 0.16, 2.2), c, M["rust"], bevel=0.02)       # sheared off
    strut(c, "leg_r_bent", (Wd / 2, 2.15), (Wd / 2 - 0.6, 2.8), 0.15, M["rust"])        # buckled stub
    box("chord_low", (0, 0, 0.08), (Wd, 0.12, 0.12), c, M["steel"], bevel=0.015)
    strut(c, "brace_a", (-Wd / 2, 0.08), (Wd / 2, 2.0), 0.08, M["rust"])
    strut(c, "brace_b", (Wd / 2, 0.08), (-Wd / 2, 2.6), 0.08, M["steel"])
    strut(c, "chord_hang", (-Wd / 2, H - 0.1), (0.2, H - 0.75), 0.11, M["rust"])        # dangling chord
    box("rubble_a", (0.5, 0.1, 0.12), (0.5, 0.4, 0.24), c, M["concrete"], bevel=0.05)
    box("rubble_b", (-0.4, -0.1, 0.09), (0.35, 0.3, 0.18), c, M["concrete"], bevel=0.04, rot=(0, 0, 0.4))


def archive_door(c, M):
    box("frame", (0, 0.1, 1.6), (3.2, 0.5, 3.2), c, M["concrete"], bevel=0.04)
    box("door", (0, -0.18, 1.35), (2.4, 0.1, 2.6), c, M["door"], bevel=0.03)
    for k in range(10):                                           # hazard band across the door foot
        box(f"stripe_{k}", (-1.08 + k * 0.24, -0.24, 0.25), (0.12, 0.01, 0.22), c, M["yellow" if k % 2 == 0 else "black"], bevel=0)
    for z in (0.9, 1.8):
        box(f"bolt_bar_{z}", (0, -0.25, z), (2.2, 0.03, 0.08), c, M["dark"], bevel=0.01)
    box("panel", (1.35, -0.18, 1.3), (0.24, 0.04, 0.34), c, M["dark"], bevel=0.01)
    box("panel_light", (1.35, -0.21, 1.36), (0.14, 0.01, 0.12), c, M["panel"], bevel=0.004)


def archive_terminal(c, M):
    box("base", (0, 0, 0.45), (0.9, 0.6, 0.9), c, M["concrete"], bevel=0.04)
    box("console", (0, -0.05, 1.05), (1.0, 0.5, 0.3), c, M["door"], bevel=0.03, rot=(0.35, 0, 0))
    box("screen", (0, -0.3, 1.1), (0.7, 0.02, 0.22), c, M["screen"], bevel=0.008, rot=(0.35, 0, 0))
    for k in range(5):
        box(f"key_{k}", (-0.3 + k * 0.15, -0.28, 0.9), (0.1, 0.06, 0.03), c, M["dark"], bevel=0.008)


def beacon(c, M):
    box("footing", (0, 0, 0.12), (0.6, 0.6, 0.24), c, M["concrete"], bevel=0.03)
    cyl("mast", (0, 0, 1.75), 0.06, 3.0, c, M["steel"], verts=16)
    for z in (1.0, 2.0):
        box(f"band_{z}", (0, 0, z), (0.16, 0.16, 0.08), c, M["yellow"], bevel=0.01)
    cyl("lamp_base", (0, 0, 3.28), 0.11, 0.06, c, M["dark"], verts=24)
    sphere("lamp", (0, 0, 3.4), 0.12, c, M["beacon"])            # the only emissive part (pulse-ready)


PROPS = {"launch_gantry": launch_gantry, "launch_tower_ruin": launch_tower_ruin, "archive_door": archive_door,
         "archive_terminal": archive_terminal, "beacon": beacon}


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for name, fn in PROPS.items():
        coll = bpy.data.collections.new(f"prop_{name}")
        scene.collection.children.link(coll)
        fn(coll, materials(0.1 if name in INTERACTABLE else 0.0))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
