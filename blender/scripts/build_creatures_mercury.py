"""Builds blender/sources/creatures/mercury.blend: Mercury creatures, glassback and cinderling (B-029).

The creature standard (B-015 v3): skeleton -> metaball body -> one mesh bound to the armature
with automatic weights, rest-pose marking masks, same clip set. Bible §7.3 / §9: grounded
anatomy, ONE bold exaggeration each, readable at 60 px/m; materials match Mercury (silicate
glass, basalt). Airless, so no external ears.
  * glassback (1.7 m silicate grazer riding the twilight band): stocky, low-carried grazing
    head; exaggeration = clusters of crystalline glass shards along the back.
  * cinderling (0.5 m, swarms at dawn): small, round, short-legged, basalt-dark hide;
    exaggeration = glowing orange cracks (emission map).

  blender --background --factory-startup --python blender/scripts/build_creatures_mercury.py
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_creatures_earth import _rig_child, build as build_species_set  # noqa: E402
from build_icons import mat  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "creatures", "mercury.blend")


def glass_shards(sp, S, rig, coll):
    """Clusters of 3-4 faceted glass shards along the back, leaning tail-ward and outward so
    the ridge reads as crystal (tall, sharp, pale) against black sky and grey regolith."""
    m = mat(f"{sp}_glass", (226, 222, 242), (182, 176, 214), 0, 0.12, 10, 0.15)
    rnd = random.Random(29001)
    spine = S["spine"]
    xs = [0.42, 0.22, 0.0, -0.22, -0.42]
    k = 0
    for ci, x in enumerate(xs):
        _, zc, r = min(spine, key=lambda p: abs(p[0] - x))
        tall = 0.42 - 0.08 * abs(ci - 2)                  # tallest mid-back
        for j in range(4 if ci in (1, 2, 3) else 3):
            h = tall * rnd.uniform(0.55, 1.0)
            dx = rnd.uniform(-0.07, 0.07)
            dy = rnd.uniform(-0.06, 0.06)
            bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=h * 0.2, radius2=0.0, depth=h,
                                            location=(x + dx, dy, zc + r * 0.75 + h * 0.42))
            ob = bpy.context.active_object
            ob.name = f"{sp}_shard{k}"
            ob.rotation_euler = (math.radians(rnd.uniform(-14, 14) + 12 * math.copysign(1, dy)),
                                 math.radians(-rnd.uniform(8, 30)), rnd.uniform(0, 6.28))
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            _rig_child(ob, rig, "body", coll, m)
            bpy.ops.object.shade_flat()                    # crisp facets
            k += 1


SPECIES = {
    "glassback": dict(
        spine=[(-0.6, 0.74, 0.2), (-0.35, 0.78, 0.26), (0.0, 0.8, 0.28), (0.3, 0.78, 0.26), (0.5, 0.74, 0.21)],
        neck=[(0.5, 0.74, 0.18), (0.64, 0.7, 0.14), (0.76, 0.66, 0.12)],             # head carried low: grazer
        head=[(0.76, 0.66, 0.12), (0.9, 0.6, 0.1), (1.02, 0.52, 0.07), (1.08, 0.48, 0.05)],
        tail=[(-0.6, 0.74, 0.1), (-0.78, 0.66, 0.07), (-0.9, 0.58, 0.045), (-0.96, 0.54, 0.025)],
        front=[(0.36, 0.6, 0.12), (0.36, 0.42, 0.09), (0.37, 0.22, 0.06), (0.37, 0.07, 0.05), (0.41, 0.0, 0.055)],
        hind=[(-0.4, 0.62, 0.14), (-0.3, 0.4, 0.1), (-0.44, 0.22, 0.06), (-0.42, 0.07, 0.05), (-0.38, 0.0, 0.055)],
        leg_y=0.14, ears=0.0, ruff=0.0, socks_z=0.16,
        belly_z=(0.5, 0.6), far=(0.07, 0.55),
        coat=((150, 146, 150), (116, 112, 118)), belly=(184, 180, 184), socks=(78, 74, 80),
        antler=None, extras=glass_shards),
    "cinderling": dict(
        spine=[(-0.16, 0.2, 0.07), (-0.08, 0.21, 0.085), (0.0, 0.21, 0.09), (0.08, 0.21, 0.085), (0.14, 0.2, 0.07)],
        neck=[(0.14, 0.2, 0.06), (0.18, 0.22, 0.055), (0.21, 0.23, 0.05)],
        head=[(0.21, 0.23, 0.055), (0.26, 0.22, 0.045), (0.3, 0.2, 0.032), (0.32, 0.19, 0.022)],
        tail=[(-0.16, 0.2, 0.04), (-0.22, 0.18, 0.03), (-0.27, 0.15, 0.02), (-0.3, 0.13, 0.014)],
        front=[(0.09, 0.16, 0.04), (0.09, 0.1, 0.03), (0.1, 0.05, 0.024), (0.1, 0.02, 0.02), (0.12, 0.0, 0.022)],
        hind=[(-0.09, 0.16, 0.045), (-0.06, 0.1, 0.032), (-0.1, 0.05, 0.024), (-0.1, 0.02, 0.02), (-0.08, 0.0, 0.022)],
        leg_y=0.05, ears=0.0, ruff=0.0, socks_z=0.04, mb_res=0.007, eye_scale=0.45,
        belly_z=(0.12, 0.16), far=(0.03, 0.14),
        coat=((58, 52, 52), (36, 32, 34)), belly=(74, 64, 60), socks=(30, 26, 28),
        cracks=dict(scale=14.0, width=0.07, color=(255, 128, 36), strength=3.0),
        antler=None),
}


def build(out_path=DEFAULT_OUT):
    """render.py's stale-source guard calls build(out) with no species: pin the Mercury table."""
    build_species_set(out_path, SPECIES)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
