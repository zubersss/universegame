"""Builds blender/sources/props/mars.blend: Mars POI props (B-021) for the crashed Halcyon
hauler and the Warden outpost (Bible §7.2).

Same conventions as build_props_common.py: one collection per prop (`prop_<name>`), real scale
(PPU 128, ≤ 4 m for the 512 px cap), standing on z = 0, origin = bottom centre. Everything is
rust-dusted (Mars §9 palette): worn hauler paint with red dust in the grime. warden_pylon and
meridian_beacon carry emission; meridian_beacon keeps it in the lamp (pulse-ready).
Interactables (hauler_cargo, warden_pylon, meridian_beacon) carry meridian_rim 0.1 -> mask R.
Deterministic:

  blender --background --factory-startup --python blender/scripts/build_props_mars.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import box, cyl, flat_material, paint_material, sphere  # noqa: E402
from build_props_earth import strut  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "mars.blend")
INTERACTABLE = {"hauler_cargo", "warden_pylon", "meridian_beacon"}


def materials(rim):
    M = {
        "hull": paint_material("hauler_hull", (172, 166, 156), (178, 112, 78)),        # paint under red dust
        "hull_dark": paint_material("hauler_dark", (86, 84, 82), (140, 88, 62)),
        "dust": paint_material("regolith_drift", (168, 96, 62), (140, 78, 50), seams=False, scratches=False),
        "container": paint_material("container", (70, 96, 120), (150, 96, 70)),
        "crate": paint_material("crate", (104, 112, 82), (150, 98, 70)),
        "metal": flat_material("scorched_metal", (70, 64, 60), metallic=0.8, rough=0.5),
        "glass": flat_material("cracked_glass", (30, 30, 34), rough=0.2),
        "pylon": paint_material("pylon_stone", (58, 56, 64), (40, 38, 46), seams=False),
        "seam": flat_material("pylon_seam", (40, 60, 80), emit=(120, 210, 255), strength=1.0),
        "lamp": flat_material("beacon_lamp", (40, 80, 60), emit=(110, 255, 180), strength=1.0, rough=0.2),
        "dish": flat_material("dish", (190, 190, 186), metallic=0.4, rough=0.4),
    }
    for m in M.values():
        m["meridian_rim"] = rim
    return M


def hauler_hull_a(c, M):
    """Cockpit section nose-down in the regolith, tilted ~14 degrees."""
    t = math.radians(14)
    box("section", (0, 0, 1.05), (2.6, 1.8, 1.7), c, M["hull"], bevel=0.12, rot=(0, t, 0))
    box("nose", (1.45, 0, 0.7), (0.8, 1.4, 1.0), c, M["hull"], bevel=0.22, rot=(0, t + 0.15, 0))
    box("canopy", (1.1, -0.2, 1.4), (0.8, 1.0, 0.08), c, M["glass"], bevel=0.02, rot=(0, t - 0.5, 0))
    box("panel_torn", (-1.25, -0.91, 1.5), (0.12, 0.04, 1.1), c, M["metal"], bevel=0.01, rot=(0, 0.3, 0))
    box("band", (-0.4, -0.91, 0.95), (0.45, 0.02, 1.55), c, M["hull_dark"], bevel=0.01, rot=(0, t, 0))
    box("drift", (0.9, 0, 0.16), (2.2, 2.2, 0.32), c, M["dust"], bevel=0.15)            # regolith piled at the nose


def hauler_hull_b(c, M):
    """Rear section: torn front edge, main nozzle, a fin."""
    box("section", (0, 0, 1.0), (2.6, 2.0, 1.8), c, M["hull"], bevel=0.12)
    for k, z in enumerate((0.4, 1.0, 1.6)):                        # jagged torn edge (front)
        box(f"tear_{k}", (1.32, 0, z), (0.12, 1.9, 0.5), c, M["metal"], bevel=0.02, rot=(0, 0.15 * (k - 1), 0))
    cyl("nozzle", (-1.6, 0, 1.0), 0.55, 0.7, c, M["metal"], rot=(0, math.pi / 2, 0), verts=32, r2=0.75)
    strut(c, "fin", (-0.9, 1.9), (-1.4, 3.0), 0.12, M["hull_dark"])
    box("drift", (0.3, 0, 0.12), (3.0, 2.4, 0.24), c, M["dust"], bevel=0.11)


def hauler_cargo(c, M):
    """Burst container with spilled crates."""
    box("container", (-0.4, 0, 0.75), (2.4, 1.4, 1.5), c, M["container"], bevel=0.04)
    box("door", (1.05, -0.5, 0.75), (0.06, 0.6, 1.4), c, M["container"], bevel=0.02, rot=(0, 0, -0.9))
    box("crate_a", (1.35, 0.1, 0.3), (0.6, 0.6, 0.6), c, M["crate"], bevel=0.03, rot=(0, 0.2, 0.3))
    box("crate_b", (1.7, -0.2, 0.22), (0.45, 0.45, 0.45), c, M["crate"], bevel=0.03, rot=(0.3, 0, -0.4))
    box("drift", (-0.2, 0, 0.08), (3.2, 1.8, 0.16), c, M["dust"], bevel=0.07)


def warden_pylon(c, M):
    """Tall faceted obelisk with glowing seams (Warden outpost marker)."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.42, depth=3.2, location=(0, 0, 1.7))
    ob = bpy.context.active_object
    for co in list(ob.users_collection):
        co.objects.unlink(ob)
    c.objects.link(ob)
    ob.name = "obelisk"
    top = max(v.co.z for v in ob.data.vertices)
    for v in ob.data.vertices:                                     # taper and point the top
        f = 0.55 + 0.45 * (1 - (v.co.z + 1.6) / 3.2)              # mesh-local z: -1.6 .. 1.6
        v.co.x *= f
        v.co.y *= f
        if v.co.z >= top - 1e-6:
            v.co.x *= 0.2
            v.co.y *= 0.2
            v.co.z += 0.35
    bpy.ops.object.shade_flat()
    ob.data.materials.append(M["pylon"])
    for k, z in enumerate((0.9, 1.7, 2.5)):                        # glowing seam rings
        cyl(f"seam_{k}", (0, 0, z), 0.42 - 0.06 * k, 0.04, c, M["seam"], verts=6)
    box("base", (0, 0, 0.1), (1.1, 1.1, 0.2), c, M["pylon"], bevel=0.04)


def meridian_beacon(c, M):
    """Tripod mast with a dish and a lamp (the lamp holds all emission)."""
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        strut(c, f"leg_{k}", (0.9 * math.cos(a), 0.0), (0.0, 2.2), 0.07, M["hull_dark"])
    cyl("mast", (0, 0, 2.6), 0.05, 0.9, c, M["metal"], verts=16)
    cyl("dish", (0.35, -0.1, 2.5), 0.4, 0.12, c, M["dish"], rot=(0, math.radians(60), 0), verts=32, r2=0.08)
    sphere("lamp", (0, 0, 3.12), 0.1, c, M["lamp"])
    box("drift", (0, 0, 0.06), (2.0, 1.4, 0.12), c, M["dust"], bevel=0.05)


PROPS = {"hauler_hull_a": hauler_hull_a, "hauler_hull_b": hauler_hull_b, "hauler_cargo": hauler_cargo,
         "warden_pylon": warden_pylon, "meridian_beacon": meridian_beacon}


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
