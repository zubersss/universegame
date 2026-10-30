"""Builds blender/sources/props/common.blend: props batch 1 (B-014).

One collection per prop (`prop_<name>`), real scale (PPU 128), standing on z = 0 with the
origin at the bottom centre (the sprite pivot). Worn-industrial materials reuse the Pilgrim's
paint (panel seams, grime toward the ground, chipped metal) so the set matches the ship.
Interactables (landing_pad, shelter_door, smelter, storage_crate, lamp) carry
`meridian_rim = 0.1` on every material -> mask R (Bible §9: 10% brighter rim). Deterministic:

  blender --background --factory-startup --python blender/scripts/build_props_common.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import box, cyl, flat_material, paint_material, sphere  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "common.blend")
INTERACTABLE = {"landing_pad", "shelter_door", "smelter", "storage_crate", "lamp"}


def materials(rim):
    M = {
        "panel": paint_material("panel", (188, 186, 178), (150, 146, 136)),
        "dark": paint_material("dark_metal", (82, 84, 88), (62, 62, 64)),
        "olive": paint_material("olive", (104, 112, 82), (82, 88, 64)),
        "deck": paint_material("deck", (112, 114, 116), (86, 86, 86)),
        "yellow": flat_material("hazard_yellow", (222, 172, 40), rough=0.6),
        "black": flat_material("hazard_black", (38, 36, 33), rough=0.7),
        "metal": flat_material("bare_metal", (120, 122, 126), metallic=1.0, rough=0.35),
        "glass": flat_material("glass", (26, 34, 44), emit=(120, 190, 255), strength=0.3, rough=0.1),
        "amber": flat_material("amber_light", (110, 70, 20), emit=(255, 176, 60), strength=1.0),
        "green": flat_material("green_light", (30, 80, 40), emit=(90, 255, 120), strength=1.0),
        "furnace": flat_material("furnace_glow", (90, 40, 20), emit=(255, 128, 40), strength=1.0),
        "lamp": flat_material("lamp_lens", (230, 226, 210), emit=(255, 236, 196), strength=1.0),
    }
    for m in M.values():
        m["meridian_rim"] = rim
    return M


def landing_pad(c, M):
    box("deck", (0, 0, 0.27), (3.6, 1.2, 0.16), c, M["deck"], bevel=0.03)
    for x in (-1.5, -0.5, 0.5, 1.5):
        box(f"leg_{x}", (x, 0, 0.1), (0.18, 1.0, 0.2), c, M["dark"], bevel=0.02)
    for k in range(18):                               # hazard edge on the front face
        box(f"chev_{k}", (-1.7 + k * 0.2, -0.605, 0.27), (0.1, 0.01, 0.12), c, M["yellow" if k % 2 == 0 else "black"], bevel=0)
    for x in (-1.6, 0.0, 1.6):
        box(f"edge_light_{x}", (x, -0.61, 0.36), (0.12, 0.02, 0.04), c, M["amber"], bevel=0.005)


def shelter_wall(c, M):
    box("panel", (0, 0, 1.25), (1.0, 0.25, 2.5), c, M["panel"], bevel=0.02)
    for x in (-0.38, 0.0, 0.38):
        box(f"rib_{x}", (x, -0.135, 1.25), (0.06, 0.03, 2.4), c, M["dark"], bevel=0.008)
    box("seam", (0, -0.13, 1.25), (0.98, 0.02, 0.05), c, M["dark"], bevel=0.005)
    for z in (0.1, 2.4):
        for x in (-0.44, 0.44):
            sphere(f"bolt_{x}_{z}", (x, -0.13, z), 0.025, c, M["metal"])


def shelter_door(c, M):
    for x in (-0.54, 0.54):
        box(f"post_{x}", (x, 0, 1.25), (0.12, 0.3, 2.5), c, M["dark"], bevel=0.015)
    box("lintel", (0, 0, 2.44), (1.2, 0.3, 0.12), c, M["dark"], bevel=0.015)
    box("door", (0, 0.02, 1.15), (0.96, 0.1, 2.26), c, M["panel"], bevel=0.02)
    box("window", (0, -0.035, 1.75), (0.32, 0.02, 0.26), c, M["glass"], bevel=0.01)
    box("kick", (0, -0.035, 0.18), (0.9, 0.02, 0.22), c, M["yellow"], bevel=0.005)
    box("handle", (0.34, -0.06, 1.1), (0.04, 0.05, 0.22), c, M["metal"], bevel=0.008)
    box("status", (0.54, -0.16, 1.55), (0.06, 0.02, 0.08), c, M["green"], bevel=0.005)


def smelter(c, M):
    for x in (-0.6, 0.6):
        box(f"leg_{x}", (x, 0, 0.15), (0.16, 0.9, 0.3), c, M["dark"], bevel=0.02)
    box("body", (0, 0, 0.9), (1.6, 1.0, 1.2), c, M["dark"], bevel=0.04)
    box("hopper", (-0.25, 0, 1.68), (0.7, 0.7, 0.36), c, M["panel"], bevel=0.03)
    cyl("chimney", (0.45, 0.1, 1.75), 0.14, 0.9, c, M["metal"], verts=24)
    cyl("cap", (0.45, 0.1, 2.22), 0.19, 0.05, c, M["dark"], verts=24)
    box("window", (-0.1, -0.505, 0.85), (0.6, 0.02, 0.36), c, M["furnace"], bevel=0.01)
    for k in range(5):                                # grate bars over the glow
        box(f"bar_{k}", (-0.34 + k * 0.12, -0.52, 0.85), (0.03, 0.02, 0.4), c, M["black"], bevel=0)
    box("panel_box", (0.58, -0.51, 1.15), (0.28, 0.03, 0.22), c, M["panel"], bevel=0.01)
    box("panel_led", (0.64, -0.53, 1.18), (0.05, 0.01, 0.04), c, M["amber"], bevel=0.003)


def storage_crate(c, M):
    box("crate", (0, 0, 0.4), (1.0, 0.8, 0.8), c, M["olive"], bevel=0.03)
    for z in (0.04, 0.76):
        box(f"band_{z}", (0, 0, z), (1.02, 0.82, 0.06), c, M["dark"], bevel=0.01)
    for x in (-0.47, 0.47):
        box(f"corner_{x}", (x, -0.405, 0.4), (0.07, 0.02, 0.8), c, M["dark"], bevel=0.006)
    box("stencil", (0, -0.405, 0.44), (0.5, 0.01, 0.08), c, M["yellow"], bevel=0)
    box("latch", (0, -0.42, 0.62), (0.12, 0.03, 0.1), c, M["metal"], bevel=0.008)


def lamp(c, M):
    cyl("base", (0, 0, 0.04), 0.18, 0.08, c, M["dark"], verts=32)
    cyl("pole", (0, 0, 1.08), 0.045, 2.0, c, M["panel"], verts=16)
    box("arm", (0.08, 0, 2.1), (0.22, 0.08, 0.05), c, M["dark"], bevel=0.01)
    box("head", (0.14, 0, 2.03), (0.26, 0.2, 0.12), c, M["dark"], bevel=0.02)
    box("lens", (0.14, 0, 1.965), (0.22, 0.16, 0.012), c, M["lamp"], bevel=0.004)
    box("lens_front", (0.272, 0, 2.02), (0.012, 0.16, 0.06), c, M["lamp"], bevel=0.003)
    # The side camera looks along +Y: give it glowing surfaces it can see (bulb + side lens).
    sphere("bulb", (0.14, 0, 1.93), 0.055, c, M["lamp"])
    box("lens_side", (0.14, -0.102, 2.02), (0.2, 0.008, 0.06), c, M["lamp"], bevel=0.003)


PROPS = {"landing_pad": landing_pad, "shelter_wall": shelter_wall, "shelter_door": shelter_door,
         "smelter": smelter, "storage_crate": storage_crate, "lamp": lamp}


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
