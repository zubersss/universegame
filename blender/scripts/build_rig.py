"""Builds blender/sources/items/rig.blend: the Rig's held-tool modules (B-037, Bible §8):
Beam (mine/dig), Lance (weapon), Survey (scan), Builder (place).

Each tool is modelled pointing +X (the aim direction) with its GRIP AT THE ORIGIN, the point
the surveyor's hand holds. The manifest gives every tool the same frame (128 x 64 px at PPU
128) and pivot [0.375, 0.5], so in Unity the sprite pivot = the grip: place it on the hand
and rotate about it to aim. Muzzle/emitter tips sit at x ~ 0.45-0.52 m (documented per tool
in MUZZLE for the FX spawn point). Distinct silhouettes and emission colours so each reads at
60 px/m: Beam cyan (matches the surveyor's beam tip), Lance orange, Survey green, Builder amber.

  blender --background --factory-startup --python blender/scripts/build_rig.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import box, cyl, flat_material, paint_material, sphere  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "rig.blend")   # props/rig/<tool>: contract has no items category
# Muzzle / emitter point per tool, metres from the grip (x forward, z up): FX spawn here.
MUZZLE = {"beam": (0.47, 0.03), "lance": (0.52, 0.035), "survey": (0.3, 0.06), "builder": (0.44, 0.03)}


def mats():
    return {
        "body": paint_material("rig_body", (196, 198, 194), (70, 64, 60)),
        "dark": flat_material("rig_dark", (46, 48, 52), metallic=0.6, rough=0.45),
        "metal": flat_material("rig_metal", (120, 124, 130), metallic=1.0, rough=0.3),
        "hazard": paint_material("rig_hazard", (222, 176, 40), (70, 60, 40), hazard=True),
        "cyan": flat_material("rig_cyan", (40, 80, 90), emit=(110, 230, 255), strength=1.4),
        "orange": flat_material("rig_orange", (90, 40, 20), emit=(255, 120, 50), strength=1.4),
        "green": flat_material("rig_green", (30, 80, 50), emit=(120, 255, 170), strength=1.2),
        "amber": flat_material("rig_amber", (90, 60, 20), emit=(255, 184, 70), strength=1.4),
    }


def grip(c, M):
    """Shared pistol grip: handle down-back from the origin, trigger guard."""
    box("grip", (-0.03, 0, -0.08), (0.06, 0.05, 0.16), c, M["dark"], bevel=0.015, rot=(0, math.radians(-12), 0))
    box("guard", (0.03, 0, -0.06), (0.05, 0.03, 0.012), c, M["dark"], bevel=0.004)


def beam(c, M):
    """Mining beam: chunky housing, ribbed focusing barrel, cyan emitter ring and tip."""
    grip(c, M)
    box("housing", (0.06, 0, 0.03), (0.26, 0.07, 0.09), c, M["body"], bevel=0.02)
    box("pack", (-0.12, 0, 0.03), (0.1, 0.075, 0.07), c, M["dark"], bevel=0.015)
    cyl("barrel", (0.3, 0, 0.03), 0.032, 0.24, c, M["metal"], rot=(0, math.pi / 2, 0), verts=24)
    for k, x in enumerate((0.24, 0.3, 0.36)):
        cyl(f"rib_{k}", (x, 0, 0.03), 0.04, 0.012, c, M["dark"], rot=(0, math.pi / 2, 0), verts=24)
    cyl("emitter", (0.43, 0, 0.03), 0.046, 0.03, c, M["cyan"], rot=(0, math.pi / 2, 0), verts=24)
    sphere("tip", (0.46, 0, 0.03), 0.024, c, M["cyan"])
    box("strip", (0.06, -0.037, 0.05), (0.18, 0.004, 0.012), c, M["cyan"], bevel=0.002)


def lance(c, M):
    """Weapon: long slim rail, twin prongs at the muzzle, orange coil bands, stock."""
    grip(c, M)
    box("receiver", (0.04, 0, 0.035), (0.2, 0.06, 0.08), c, M["dark"], bevel=0.015)
    box("stock", (-0.13, 0, 0.02), (0.16, 0.05, 0.06), c, M["body"], bevel=0.015)   # meets the receiver
    box("rail", (0.3, 0, 0.035), (0.34, 0.03, 0.03), c, M["metal"], bevel=0.006)
    for sz in (-1, 1):
        box(f"prong_{sz}", (0.45, 0, 0.035 + sz * 0.028), (0.14, 0.02, 0.014), c, M["metal"], bevel=0.004)
    for k, x in enumerate((0.18, 0.25, 0.32)):
        box(f"coil_{k}", (x, 0, 0.035), (0.022, 0.046, 0.052), c, M["orange"], bevel=0.006)
    box("sight", (0.02, 0, 0.09), (0.06, 0.02, 0.025), c, M["dark"], bevel=0.005)


def survey(c, M):
    """Scanner: boxy body with a green screen facing the camera, scan dish, antenna."""
    grip(c, M)
    box("body", (0.1, 0, 0.05), (0.26, 0.08, 0.12), c, M["body"], bevel=0.02)
    box("screen", (0.08, -0.042, 0.06), (0.14, 0.004, 0.07), c, M["green"], bevel=0.004)
    cyl("dish", (0.245, 0, 0.06), 0.065, 0.03, c, M["metal"], rot=(0, math.pi / 2, 0), verts=24, r2=0.035)   # on the body
    sphere("lens", (0.275, 0, 0.06), 0.022, c, M["green"])
    cyl("antenna", (-0.02, 0, 0.135), 0.006, 0.05, c, M["dark"], verts=8)    # stays inside the frame margin
    sphere("antenna_tip", (-0.02, 0, 0.168), 0.011, c, M["green"])


def builder(c, M):
    """Placement projector: hazard-banded body, wide projector head with an amber grid."""
    grip(c, M)
    box("body", (0.08, 0, 0.035), (0.22, 0.075, 0.09), c, M["hazard"], bevel=0.018)
    box("neck", (0.25, 0, 0.035), (0.08, 0.05, 0.06), c, M["dark"], bevel=0.01)
    box("head", (0.35, 0, 0.035), (0.12, 0.1, 0.13), c, M["body"], bevel=0.02)
    box("lens", (0.415, 0, 0.035), (0.012, 0.08, 0.1), c, M["amber"], bevel=0.004)
    for k, z in enumerate((-0.005, 0.035, 0.075)):
        box(f"grid_{k}", (0.42, -0.051, z), (0.006, 0.004, 0.006), c, M["amber"], bevel=0.001)
    box("cell", (-0.1, 0, 0.03), (0.08, 0.07, 0.07), c, M["dark"], bevel=0.012)


TOOLS = {"beam": beam, "lance": lance, "survey": survey, "builder": builder}


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    M = mats()
    for name, fn in TOOLS.items():
        coll = bpy.data.collections.new(f"tool_{name}")
        scene.collection.children.link(coll)
        fn(coll, M)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
