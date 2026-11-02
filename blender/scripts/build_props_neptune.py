"""Builds blender/sources/props/neptune.blend: Neptune POI props (B-068, Bible §7.9).

Same conventions as build_props_jupiter.py (one collection per prop, real scale, standing on
z = 0, origin bottom centre) and the SAME materials (riveted cream Meridian hull, rust/orange
band), so the expedition reads as one fleet (LEAD cycle 164).

- wind_anchor: a floe anchor post: a driven spike with guy cables, a wind vane and a small
  blinking light. Interactable.
- meridian_wreck_bow / _mid / _stern: the *Meridian* herself in three standable segments
  (~3.8 m each), alive in the Great Dark Spot: hull plates with the orange band, a flat walkable
  top deck line, faint running lights (port red, starboard green, white strobes), lit
  portholes, torn ends where the segments broke apart. bow carries the bridge windows, mid a
  hatch and antenna, stern the engine bells with a dim glow. Bow and mid are interactable
  (the story beacon broadcasts from the bridge).

  blender --background --factory-startup --python blender/scripts/build_props_neptune.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import box, cyl, flat_material, sphere  # noqa: E402
from build_props_jupiter import _link, materials as jupiter_materials  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "neptune.blend")
INTERACTABLE = {"wind_anchor", "meridian_wreck_bow", "meridian_wreck_mid"}


def materials(rim):
    M = jupiter_materials(rim)
    extra = {
        "green": flat_material("ngreen", (20, 80, 40), emit=(90, 255, 140), strength=1.6),
        "white": flat_material("nwhite", (120, 120, 130), emit=(240, 244, 255), strength=1.8),
        "port": flat_material("nport", (60, 50, 30), emit=(255, 214, 150), strength=1.1),
        "engine": flat_material("nengine", (40, 50, 110), emit=(110, 140, 255), strength=1.2),
        "torn": flat_material("ntorn", (40, 36, 34), metallic=0.6, rough=0.6),
    }
    for m in extra.values():
        m["meridian_rim"] = rim
    M.update(extra)
    return M


HULL_R, HULL_Z = 1.05, 1.15          # hull cylinder radius and axis height: top of hull ~2.2 m


def _hull_section(c, M, x0, x1, name):
    """Horizontal hull cylinder from x0 to x1 with the orange band and a flat deck on top."""
    ln = x1 - x0
    cx = (x0 + x1) / 2
    cyl(f"{name}_hull", (cx, 0, HULL_Z), HULL_R, ln, c, M["hull"], rot=(0, math.pi / 2, 0), verts=40)
    box(f"{name}_band", (cx, -HULL_R * 0.99, HULL_Z - 0.3), (ln, 0.04, 0.24), c, M["orange"], bevel=0.01)   # stripe on the flank (a full cylinder covered the lower half)
    box(f"{name}_deck", (cx, 0, HULL_Z + HULL_R - 0.02), (ln, 1.2, 0.08), c, M["grate"], bevel=0.02)   # flat walk line
    for k in range(int(ln / 0.55)):                                  # rib seams
        box(f"{name}_rib{k}", (x0 + 0.3 + k * 0.55, -HULL_R * 0.98, HULL_Z), (0.04, 0.04, 1.6), c, M["hull_dark"], bevel=0.01)


def _torn_end(c, M, x, name, s):
    """Jagged broken bulkhead at x (s = +1 facing +x)."""
    box(f"{name}_bulk", (x, 0, HULL_Z), (0.08, 1.9, 1.9), c, M["torn"], bevel=0.02)
    for k in range(7):
        z = HULL_Z - 0.9 + k * 0.3
        box(f"{name}_shard{k}", (x + s * (0.08 + 0.06 * (k % 3)), -0.6 + 0.2 * (k % 4), z),
            (0.16 + 0.05 * (k % 2), 0.05, 0.12), c, M["hull"], bevel=0.01, rot=(0.3 * k, 0.4 * s, 0))


def _skids(c, M, x0, x1, name):
    for x in (x0 + 0.5, x1 - 0.5):
        box(f"{name}_skid{x}", (x, 0, 0.06), (0.5, 1.0, 0.12), c, M["metal"], bevel=0.02)
        box(f"{name}_leg{x}", (x, 0, 0.18), (0.18, 0.18, 0.2), c, M["metal"], bevel=0.02)


def _portholes(c, M, xs, name, z=HULL_Z + 0.25):
    for k, x in enumerate(xs):
        cyl(f"{name}_pr{k}", (x, -HULL_R * 0.97, z), 0.12, 0.05, c, M["metal"], rot=(math.pi / 2, 0, 0), verts=20)
        cyl(f"{name}_pg{k}", (x, -HULL_R * 1.0, z), 0.08, 0.03, c, M["port"], rot=(math.pi / 2, 0, 0), verts=20)


def meridian_wreck_bow(c, M):
    _hull_section(c, M, -1.9, 0.9, "bow")
    # Nose cone: tapered to +x, bridge windows on its upper face.
    cyl("nose", (1.4, 0, HULL_Z), HULL_R, 1.0, c, M["hull"], rot=(0, math.pi / 2, 0), verts=40, r2=0.45)
    for k in range(3):
        box(f"bridge{k}", (1.25 + 0.22 * k, -0.62 + 0.06 * k, HULL_Z + 0.55 - 0.08 * k), (0.18, 0.05, 0.16), c, M["port"],
            bevel=0.01, rot=(0, 0.35, 0))
    _portholes(c, M, (-1.2, -0.5, 0.2), "bow")
    _torn_end(c, M, -1.9, "bow", -1)
    sphere("port_light", (1.8, -0.5, HULL_Z), 0.06, c, M["red"])         # faint running lights
    sphere("strobe", (0.6, 0, HULL_Z + HULL_R + 0.12), 0.06, c, M["white"])
    _skids(c, M, -1.9, 1.6, "bow")


def meridian_wreck_mid(c, M):
    _hull_section(c, M, -1.9, 1.9, "mid")
    box("hatch", (0.0, -HULL_R * 0.98, HULL_Z - 0.05), (0.7, 0.08, 0.95), c, M["hull_dark"], bevel=0.04)
    box("hatch_seam", (0.0, -HULL_R * 1.03, HULL_Z - 0.05), (0.03, 0.02, 0.85), c, M["seam"], bevel=0.004)
    _portholes(c, M, (-1.3, -0.7, 0.8, 1.4), "mid")
    cyl("antenna", (0.9, 0, HULL_Z + HULL_R + 0.45), 0.03, 0.8, c, M["metal"], verts=8)
    sphere("antenna_light", (0.9, 0, HULL_Z + HULL_R + 0.88), 0.06, c, M["beacon"])   # the broadcast
    sphere("green_light", (-1.6, -HULL_R * 0.95, HULL_Z + 0.6), 0.05, c, M["green"])
    _torn_end(c, M, -1.9, "mid_a", -1)
    _torn_end(c, M, 1.9, "mid_b", 1)
    _skids(c, M, -1.9, 1.9, "mid")


def meridian_wreck_stern(c, M):
    _hull_section(c, M, -0.9, 1.9, "stern")
    cyl("taper", (-1.25, 0, HULL_Z), 0.75, 0.7, c, M["hull"], rot=(0, -math.pi / 2, 0), verts=40, r2=HULL_R)
    for k, z in enumerate((HULL_Z + 0.35, HULL_Z - 0.35)):          # engine bells
        cyl(f"bell{k}", (-1.75, 0, z), 0.3, 0.45, c, M["metal"], rot=(0, -math.pi / 2, 0), verts=24, r2=0.18)
        cyl(f"glow{k}", (-1.97, 0, z), 0.26, 0.02, c, M["engine"], rot=(0, math.pi / 2, 0), verts=24)
    box("fin", (-0.6, 0, HULL_Z + HULL_R + 0.35), (0.9, 0.08, 0.6), c, M["hull_dark"], bevel=0.03)
    _portholes(c, M, (0.2, 0.9), "stern")
    _torn_end(c, M, 1.9, "stern", 1)
    sphere("strobe", (-0.6, 0, HULL_Z + HULL_R + 0.68), 0.06, c, M["white"])
    sphere("green_light", (-1.0, -0.6, HULL_Z), 0.05, c, M["green"])
    _skids(c, M, -1.6, 1.9, "stern")


def wind_anchor(c, M):
    cyl("spike", (0, 0, 1.2), 0.1, 2.4, c, M["metal"], verts=12)
    cyl("collar", (0, 0, 0.3), 0.22, 0.25, c, M["orange"], verts=20)
    box("plate", (0, 0, 0.05), (0.9, 0.9, 0.1), c, M["grate"], bevel=0.02)
    for k, (x, y) in enumerate(((-0.8, -0.4), (0.8, -0.4), (0.0, 0.7))):   # guy cables
        dx, dz = x, -2.0
        ln = math.hypot(math.hypot(x, y), 2.0)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.012, depth=ln, location=(x / 2, y / 2, 1.1))
        cab = _link(c, bpy.context.active_object)
        cab.rotation_euler = (math.atan2(-y, 2.0), math.atan2(x, 2.0), 0)
        cab.data.materials.append(M["metal"])
    box("vane", (0.35, 0, 2.6), (0.6, 0.03, 0.3), c, M["hull"], bevel=0.02)
    box("vane_tip", (0.68, 0, 2.6), (0.08, 0.04, 0.34), c, M["orange"], bevel=0.01)
    sphere("blink", (0, 0, 2.5), 0.07, c, M["red"])


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


PROPS = {"wind_anchor": wind_anchor, "meridian_wreck_bow": meridian_wreck_bow,
         "meridian_wreck_mid": meridian_wreck_mid, "meridian_wreck_stern": meridian_wreck_stern}


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
