"""Builds blender/sources/props/saturn.blend: Saturn POI props (B-068, Bible §7.7).

Same conventions and Meridian materials as build_props_jupiter.py.

- ring_rig: the ring-mining rig with the Saturn beacon: a float deck, ore hopper, a crane arm
  with a grab, and the beacon mast with its lamp. Interactable (beacon).
- helium_trap: a Deck 2-3 helium-rain trap: a wide collector funnel over a pressure tank on a
  small float deck, a blue-white fill gauge (emission). Interactable.
- hexagon_wall_marker: a wind-wall marker pylon (hexagonal, banded orange/cream) with three
  amber warning lights up its side.

  blender --background --factory-startup --python blender/scripts/build_props_saturn.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import box, cyl, flat_material, sphere  # noqa: E402
from build_props_jupiter import materials as jupiter_materials  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "saturn.blend")
INTERACTABLE = {"ring_rig", "helium_trap"}


def materials(rim):
    M = jupiter_materials(rim)
    extra = {
        "gauge": flat_material("sgauge", (60, 110, 140), emit=(170, 230, 255), strength=1.6),
        "amber": flat_material("samber", (120, 80, 20), emit=(255, 190, 80), strength=1.6),
        "ore": flat_material("sore", (176, 168, 156), rough=0.8),
    }
    for m in extra.values():
        m["meridian_rim"] = rim
    M.update(extra)
    return M


def ring_rig(c, M):
    box("deck", (0, 0, 0.12), (3.2, 1.4, 0.24), c, M["grate"], bevel=0.03)
    box("keel", (0, 0, 0.3), (2.9, 1.2, 0.14), c, M["orange"], bevel=0.03)
    box("hopper", (-0.8, 0, 0.85), (1.0, 0.9, 0.9), c, M["hull"], bevel=0.05)
    cyl("hopper_mouth", (-0.8, 0, 1.4), 0.5, 0.2, c, M["hull_dark"], verts=4, r2=0.62).rotation_euler.z = math.pi / 4
    for k in range(4):
        sphere(f"ore{k}", (-1.0 + 0.15 * k, -0.1 + 0.05 * k, 1.42), 0.12, c, M["ore"])
    cyl("crane_post", (0.6, 0, 1.1), 0.12, 1.6, c, M["metal"], verts=12)
    box("crane_arm", (1.05, 0, 1.9), (1.3, 0.12, 0.12), c, M["orange"], bevel=0.02, rot=(0, -0.25, 0))
    cyl("cable", (1.62, 0, 1.55), 0.015, 0.7, c, M["metal"], verts=6)
    box("grab", (1.62, 0, 1.15), (0.3, 0.2, 0.18), c, M["metal"], bevel=0.03)
    cyl("mast", (-0.2, 0, 2.6), 0.05, 1.4, c, M["metal"], verts=10)
    for z in (2.3, 2.8):
        box(f"arm{z}", (-0.2, 0, z), (0.4, 0.04, 0.04), c, M["metal"], bevel=0.005)
    sphere("beacon", (-0.2, 0, 3.4), 0.14, c, M["beacon"])
    for z in (3.28, 3.52):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.015, location=(-0.2, 0, z))
        ob = bpy.context.active_object
        for co in list(ob.users_collection):
            co.objects.unlink(ob)
        c.objects.link(ob)
        ob.data.materials.append(M["grate"])


def helium_trap(c, M):
    box("deck", (0, 0, 0.1), (2.2, 1.2, 0.2), c, M["grate"], bevel=0.03)
    cyl("tank", (0, 0, 0.75), 0.5, 1.1, c, M["hull"], verts=32)
    cyl("tank_cap", (0, 0, 1.33), 0.52, 0.08, c, M["hull_dark"], verts=32)
    cyl("funnel", (0, 0, 1.95), 1.05, 1.0, c, M["metal"], verts=40, r2=0.18)
    cyl("funnel_lip", (0, 0, 2.46), 1.08, 0.06, c, M["orange"], verts=40)
    box("gauge_frame", (0, -0.5, 0.75), (0.16, 0.04, 0.7), c, M["metal"], bevel=0.01)
    box("gauge", (0, -0.53, 0.68), (0.1, 0.02, 0.5), c, M["gauge"], bevel=0.005)
    for x in (-0.85, 0.85):
        box(f"strut{x}", (x * 0.7, 0, 1.45), (0.06, 0.06, 1.0), c, M["metal"], bevel=0.01, rot=(0, -0.45 * math.copysign(1, x), 0))


def hexagon_wall_marker(c, M):
    cyl("base", (0, 0, 0.15), 0.42, 0.3, c, M["hull_dark"], verts=6)
    for k in range(6):                                           # banded pylon
        cyl(f"band{k}", (0, 0, 0.55 + k * 0.5), 0.26, 0.5, c, M["orange" if k % 2 else "hull"], verts=6)
    cyl("cap", (0, 0, 3.4), 0.3, 0.2, c, M["hull_dark"], verts=6, r2=0.12)
    for k, z in enumerate((1.3, 2.3, 3.2)):
        sphere(f"warn{k}", (0, -0.27, z), 0.07, c, M["amber"])


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


PROPS = {"ring_rig": ring_rig, "helium_trap": helium_trap, "hexagon_wall_marker": hexagon_wall_marker}


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
