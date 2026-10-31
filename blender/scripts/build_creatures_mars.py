"""Builds blender/sources/creatures/mars.blend: Mars creatures, dustskater and scree stalker (B-016).

Same method as the Earth creatures (B-015 v3, the creature standard): skeleton -> metaball body
-> one mesh bound to the armature with automatic weights, rest-pose marking masks, same clip set.
Bible §7.2 / §9: grounded anatomy with ONE bold alien exaggeration each, readable at 60 px/m,
Mars palette (rust / umber / salmon, silicate materials). Mars has thin air, so neither species
has external ears.
  * dustskater (0.8 m scavenger, flees): low, quick, long balancing tail; exaggeration = huge
    flat skate-pad feet that ride over loose dust.
  * scree stalker (1.6 m canyon pack hunter): lanky, long low head, long hind legs for 2.6x
    jumps; exaggeration = a ridge of overlapping stone plates from neck to tail (scree hide).

  blender --background --factory-startup --python blender/scripts/build_creatures_mars.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_creatures_earth import _rig_child, build as build_species_set  # noqa: E402
from build_icons import mat  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "creatures", "mars.blend")


def skate_pads(front, hind, leg_y, r, length, width):
    """Flat ellipsoid pads (metaball extras) under each foot, slightly forward of the toe."""
    out = []
    for pts in (front, hind):
        x, z = pts[-1][0], pts[-1][1]
        for sy in (-1, 1):
            out.append((x + 0.02, sy * leg_y, z + r * 0.45, r, length, width, 0.6))
    return out


def scree_plates(sp, S, rig, coll):
    """Overlapping stone slabs along the back, tilted tail-ward so each edge breaks the
    silhouette (the stalker's exaggeration). Neck plates ride the neck bone, the rest the body
    bone, so the ridge follows the pose (tail plates read as stray dots at size; dropped)."""
    m = mat(f"{sp}_plate", (98, 80, 70), (66, 54, 48), 0, 0.85, 14, 0.6)
    plates = []                                     # (x, z, length, height, bone)
    neck = S["neck"]
    for t in (0.35, 0.75):
        x = neck[0][0] + (neck[-1][0] - neck[0][0]) * t
        z = neck[0][1] + (neck[-1][1] - neck[0][1]) * t + neck[1][2] * 0.85
        plates.append((x, z, 0.2, 0.14, "neck"))
    spine = S["spine"]
    x0, x1 = spine[0][0] + 0.05, spine[-1][0] - 0.02
    n = 6
    for k in range(n):
        x = x1 - (x1 - x0) * k / (n - 1)
        _, zc, r = min(spine, key=lambda p: abs(p[0] - x))          # nearest spine point
        size = 1.0 - 0.25 * abs(k - 2) / 3                  # biggest over the shoulders
        plates.append((x, zc + r * 0.8, 0.34 * size, 0.24 * size, "body"))   # bold at 60 px/m (~14 px tall)
    for i, (x, z, L, H, bone) in enumerate(plates):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0.0, z))
        ob = bpy.context.active_object
        ob.name = f"{sp}_plate{i}"
        ob.scale = (L, 0.11 if bone != "tail" else 0.07, H)
        ob.rotation_euler = (0.0, math.radians(-28 - 6 * (i % 2)), 0.0)    # leading edge up, tail-ward lean
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        bev = ob.modifiers.new("bevel", "BEVEL")
        bev.width, bev.segments = 0.012, 1
        _rig_child(ob, rig, bone, coll, m)
        bpy.ops.object.shade_flat()                                    # broken stone faces


DUST_FRONT = [(0.13, 0.25, 0.04), (0.12, 0.17, 0.028), (0.14, 0.09, 0.02), (0.15, 0.035, 0.016), (0.18, 0.0, 0.018)]
DUST_HIND = [(-0.13, 0.26, 0.05), (-0.08, 0.17, 0.032), (-0.16, 0.09, 0.02), (-0.15, 0.035, 0.016), (-0.12, 0.0, 0.018)]

SPECIES = {
    "dustskater": dict(
        spine=[(-0.2, 0.29, 0.06), (-0.11, 0.3, 0.075), (0.0, 0.3, 0.08), (0.1, 0.31, 0.08), (0.18, 0.32, 0.068)],
        neck=[(0.18, 0.32, 0.058), (0.24, 0.36, 0.048), (0.28, 0.39, 0.044)],
        head=[(0.28, 0.39, 0.05), (0.34, 0.39, 0.042), (0.4, 0.37, 0.026), (0.43, 0.36, 0.017)],
        tail=[(-0.2, 0.29, 0.034), (-0.31, 0.29, 0.028), (-0.39, 0.32, 0.02), (-0.44, 0.37, 0.013)],   # fits 128 px at ppu >= 100
        front=DUST_FRONT, hind=DUST_HIND,
        blobs=skate_pads(DUST_FRONT, DUST_HIND, 0.05, 0.05, 2.6, 1.5),        # pads ~0.26 m: bold at 60 px/m
        leg_y=0.05, ears=0.0, ruff=0.0, socks_z=0.07, mb_res=0.008, eye_scale=0.55,
        belly_z=(0.22, 0.27), far=(0.03, 0.2),
        coat=((198, 140, 96), (160, 104, 70)), belly=(224, 190, 152), socks=(84, 56, 44),
        antler=None),
    "scree_stalker": dict(
        spine=[(-0.55, 0.82, 0.14), (-0.32, 0.84, 0.18), (0.0, 0.84, 0.19), (0.3, 0.86, 0.2), (0.48, 0.88, 0.17)],
        neck=[(0.48, 0.88, 0.15), (0.62, 0.96, 0.12), (0.74, 1.02, 0.1)],
        head=[(0.74, 1.02, 0.1), (0.9, 1.0, 0.085), (1.06, 0.95, 0.055), (1.16, 0.92, 0.03)],
        tail=[(-0.55, 0.82, 0.08), (-0.8, 0.74, 0.065), (-1.0, 0.68, 0.045), (-1.14, 0.66, 0.025)],
        front=[(0.34, 0.74, 0.09), (0.32, 0.54, 0.06), (0.34, 0.27, 0.038), (0.35, 0.08, 0.03), (0.4, 0.0, 0.034)],
        hind=[(-0.36, 0.76, 0.11), (-0.22, 0.5, 0.07), (-0.42, 0.3, 0.038), (-0.38, 0.08, 0.03), (-0.33, 0.0, 0.034)],
        leg_y=0.11, ears=0.0, ruff=0.0, socks_z=0.18,
        belly_z=(0.62, 0.72), far=(0.05, 0.66),
        coat=((132, 98, 78), (100, 72, 58)), belly=(176, 136, 106), socks=(64, 46, 40),
        antler=None, extras=scree_plates),
}


def build(out_path=DEFAULT_OUT):
    """render.py's stale-source guard calls build(out) with no species: this module's own
    build must pin the Mars table (the imported Earth build defaults to stag/wolf)."""
    build_species_set(out_path, SPECIES)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
