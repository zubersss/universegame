"""Builds blender/sources/props/uranus.blend: Uranus POI props (B-068, Bible §7.8).

Same conventions and Meridian materials as build_props_jupiter.py; frost-pale accents read in
Uranus' dim light.

- tilted_derelict: the Uranus beacon on a Meridian derelict leaning hard over (a nod to the
  98-degree axial tilt): a hull section tipped ~35 deg onto a float pontoon, its beacon mast
  still upright-ish and lit. Interactable (beacon).
- umbrella_platform: a diamond-catching umbrella: a mast on a float, a wide shallow canopy whose
  flat top is standable, diamonds caught along the rim (bright, faintly emissive).

  blender --background --factory-startup --python blender/scripts/build_props_uranus.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import box, cyl, flat_material, sphere  # noqa: E402
from build_props_jupiter import materials as jupiter_materials  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "uranus.blend")
INTERACTABLE = {"tilted_derelict"}


def materials(rim):
    M = jupiter_materials(rim)
    extra = {
        "diamond": flat_material("udiamond", (220, 240, 250), emit=(200, 240, 255), strength=1.2, rough=0.05),
        "canopy": flat_material("ucanopy", (176, 208, 214), rough=0.5),
        "port": flat_material("uport", (60, 50, 30), emit=(255, 214, 150), strength=1.0),
    }
    for m in extra.values():
        m["meridian_rim"] = rim
    M.update(extra)
    return M


def tilted_derelict(c, M):
    box("pontoon", (0, 0, 0.18), (3.2, 1.3, 0.36), c, M["hull_dark"], bevel=0.06)
    tilt = math.radians(35)
    cx, cz = 0.2, 1.25
    hull = cyl("hull", (cx, 0, cz), 0.75, 2.6, c, M["hull"], rot=(0, math.pi / 2 - tilt, 0), verts=40)
    cyl("band", (cx - 0.35 * math.cos(tilt), 0, cz - 0.35 * math.sin(tilt)), 0.76, 0.3, c, M["orange"],
        rot=(0, math.pi / 2 - tilt, 0), verts=40)
    ux, uz = math.cos(tilt), math.sin(tilt)                        # along the tilted hull axis
    for k, t in enumerate((-0.6, 0.1, 0.8)):
        cyl(f"port{k}", (cx + ux * t, -0.74, cz + uz * t), 0.09, 0.04, c, M["port"], rot=(math.pi / 2, 0, 0), verts=16)
    cyl("cap_hi", (cx + ux * 1.32, 0, cz + uz * 1.32), 0.6, 0.12, c, M["hull_dark"], rot=(0, math.pi / 2 - tilt, 0), verts=32)
    box("frost", (cx + ux * 0.4 - 0.05, 0, cz + uz * 0.4 + 0.72), (1.6, 0.9, 0.04), c, M["frost"], bevel=0.01, rot=(0, -tilt, 0))
    mx, mz = cx - ux * 0.5, cz - uz * 0.5 + 0.75                   # mast from the hull's upper side
    cyl("mast", (mx, 0, mz + 0.6), 0.04, 1.2, c, M["metal"], verts=8, rot=(0, -0.15, 0))
    sphere("beacon", (mx + 0.09, 0, mz + 1.25), 0.13, c, M["beacon"])
    hull.name = "derelict_hull"


def umbrella_platform(c, M):
    box("float", (0, 0, 0.16), (1.2, 1.0, 0.32), c, M["hull_dark"], bevel=0.06)
    cyl("mast", (0, 0, 1.05), 0.08, 1.5, c, M["metal"], verts=12)
    cyl("canopy", (0, 0, 1.9), 1.7, 0.22, c, M["canopy"], verts=48, r2=1.55)
    cyl("canopy_top", (0, 0, 2.02), 1.5, 0.04, c, M["grate"], verts=48)        # flat standable top
    cyl("rim", (0, 0, 1.8), 1.72, 0.06, c, M["orange"], verts=48)
    for k in range(9):                                             # caught diamonds along the rim
        a = 2 * math.pi * k / 9 + 0.2
        x, y = 1.6 * math.cos(a), 1.3 * math.sin(a)
        if y < 0.4:
            bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.07, radius2=0.0, depth=0.14, location=(x, y, 2.08))
            d = bpy.context.active_object
            for co in list(d.users_collection):
                co.objects.unlink(d)
            c.objects.link(d)
            d.rotation_euler = (0.3 * k, 0.2, 0)
            d.data.materials.append(M["diamond"])
    for k, x in enumerate((-0.6, 0.6)):                            # braces
        box(f"brace{k}", (x * 0.6, 0, 1.45), (0.04, 0.04, 0.9), c, M["metal"], bevel=0.01, rot=(0, 0.6 * math.copysign(1, x), 0))


def _ground(coll):
    """Lift the whole prop so its lowest evaluated vertex sits exactly on z = 0 (rotated or
    bevelled parts dipped below the ground line into the bottom margin)."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    low = None
    for ob in coll.all_objects:
        if ob.type != "MESH":
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        for v in me.vertices:
            z = (ev.matrix_world @ v.co).z
            low = z if low is None else min(low, z)
        ev.to_mesh_clear()
    if low is not None and abs(low) > 1e-4:
        for ob in coll.all_objects:
            if ob.parent is None:
                ob.location.z -= low


PROPS = {"tilted_derelict": tilted_derelict, "umbrella_platform": umbrella_platform}


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for name, fn in PROPS.items():
        coll = bpy.data.collections.new(f"prop_{name}")
        scene.collection.children.link(coll)
        fn(coll, materials(0.1 if name in INTERACTABLE else 0.0))
        _ground(coll)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
