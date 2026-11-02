"""Builds blender/sources/props/jupiter.blend: Jupiter cloud-deck props (B-055, Bible §7.5-7.6).

Same conventions as build_props_venus.py: one collection per prop (`prop_<name>`), real scale,
standing on z = 0, origin = bottom centre. Jupiter palette: cream/rust/brick (§9), Meridian
hulls in cream with the orange band, rust-ochre NH4SH staining, ammonia frost on upper faces.

- husk_tortoise: the husk of a dead Ballast tortoise, a standable platform. Low domed shell
  with a flattened top plateau (the walkable surface), plated scutes, the drooped skull at +x,
  hanging flipper stubs and a torn, deflated gas bladder under it. B-056's ballast_tortoise
  must keep this shell silhouette.
- derelict_pod: a buoyant Meridian-expedition cargo pod, battered, with a torn float envelope
  draped over it and a weak red emergency light. Interactable (salvage).
- beacon_vault: Jupiter's beacon: an armoured vault on a floating deck, lit door seams and a
  mast with the beacon lamp. Interactable.

  blender --background --factory-startup --python blender/scripts/build_props_jupiter.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import box, cyl, flat_material, paint_material, sphere  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "jupiter.blend")
INTERACTABLE = {"derelict_pod", "beacon_vault"}


def materials(rim):
    M = {
        "hull": paint_material("jhull", (222, 204, 170), (150, 96, 56)),            # cream, rust stain
        "hull_dark": paint_material("jhull_dark", (96, 80, 66), (70, 52, 40), seams=False),
        "orange": paint_material("jorange", (210, 116, 50), (150, 90, 44), seams=False),
        "metal": flat_material("jmetal", (104, 100, 96), metallic=0.8, rough=0.45),
        "grate": flat_material("jgrate", (66, 62, 58), metallic=0.7, rough=0.5),
        "frost": flat_material("jfrost", (232, 236, 240), rough=0.85),
        "red": flat_material("jred", (90, 20, 14), emit=(255, 70, 50), strength=1.4),
        "beacon": flat_material("jbeacon", (120, 70, 20), emit=(255, 214, 140), strength=2.4),
        "seam": flat_material("jseam", (110, 60, 20), emit=(255, 170, 80), strength=1.4),
        # Ballast tortoise husk: leathery cream-brick scutes, dark underside, bone skull.
        "scute": paint_material("tscute", (196, 150, 108), (140, 84, 56), seams=False, scratches=False),
        "scute_edge": flat_material("tscute_edge", (112, 62, 44), rough=0.8),
        "hide": flat_material("thide", (98, 70, 58), rough=0.85),
        "bone": flat_material("tbone", (214, 200, 176), rough=0.7),
    }
    bl = bpy.data.materials.new("bladder")
    bl.use_nodes = True
    pr = bl.node_tree.nodes["Principled BSDF"]
    pr.inputs["Base Color"].default_value = (0.62, 0.42, 0.34, 1)
    pr.inputs["Roughness"].default_value = 0.5
    pr.inputs["Alpha"].default_value = 0.75
    M["bladder"] = bl
    env = bpy.data.materials.new("torn_envelope")
    env.use_nodes = True
    pr = env.node_tree.nodes["Principled BSDF"]
    pr.inputs["Base Color"].default_value = (0.86, 0.76, 0.58, 1)
    pr.inputs["Roughness"].default_value = 0.6
    pr.inputs["Alpha"].default_value = 0.85
    M["envelope"] = env
    for m in M.values():
        m["meridian_rim"] = rim
    return M


def _link(c, ob):
    for co in list(ob.users_collection):
        co.objects.unlink(ob)
    c.objects.link(ob)
    return ob


def _ellipsoid(name, c, m, loc, scale, segs=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=1.0, location=loc)
    ob = _link(c, bpy.context.active_object)
    ob.name = name
    ob.scale = scale
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(m)
    return ob


def husk_tortoise(c, M):
    """Dead Ballast tortoise husk ~3.7 m long, top plateau at ~1.55 m (standable)."""
    shell = _ellipsoid("shell", c, M["scute"], (0, 0, 0.82), (1.75, 1.2, 0.72), 48, 24)
    for v in shell.data.vertices:                     # flatten the crown into a walkable plateau
        if v.co.z > 0.62:
            v.co.z = 0.62 + (v.co.z - 0.62) * 0.25
    _ellipsoid("rim", c, M["scute_edge"], (0, 0, 0.62), (1.82, 1.25, 0.16), 48, 12)      # marginal scutes ridge
    _ellipsoid("plastron", c, M["hide"], (0, 0, 0.42), (1.5, 1.0, 0.3))                   # dark underside
    # Scutes: two rows of low plates on the plateau and the shoulders, frost on the top row.
    for k in range(5):
        x = -1.2 + k * 0.6
        _ellipsoid(f"scute_top{k}", c, M["scute"], (x, -0.2, 1.36), (0.27, 0.5, 0.06), 16, 8)
        _ellipsoid(f"frost{k}", c, M["frost"], (x + 0.05, -0.25, 1.4), (0.18, 0.34, 0.03), 12, 6)
    for k in range(6):
        x = -1.35 + k * 0.54
        z = 1.05 + 0.18 * math.cos((x / 1.75) * math.pi / 2)
        _ellipsoid(f"scute_side{k}", c, M["scute"], (x, -0.82, z), (0.24, 0.18, 0.22), 16, 8)
    # Skull drooping at +x: bone, empty dark eye socket, slack jaw.
    _ellipsoid("neck", c, M["hide"], (1.85, -0.1, 0.62), (0.4, 0.26, 0.22))
    skull = _ellipsoid("skull", c, M["bone"], (2.2, -0.1, 0.42), (0.32, 0.24, 0.24))
    skull.rotation_euler = (0, 0.5, 0)
    _ellipsoid("socket", c, M["scute_edge"], (2.3, -0.32, 0.5), (0.07, 0.03, 0.06), 12, 6)
    _ellipsoid("jaw", c, M["bone"], (2.25, -0.1, 0.22), (0.24, 0.18, 0.08), 16, 8)
    # Flipper stubs hanging limp, tail stub at -x.
    for k, x in enumerate((-1.0, 1.0)):
        fl = _ellipsoid(f"flipper{k}", c, M["hide"], (x, -0.7, 0.3), (0.42, 0.12, 0.14), 16, 8)
        fl.rotation_euler = (0, 0.6 if x > 0 else -0.6, 0)
    _ellipsoid("tail", c, M["hide"], (-1.95, -0.05, 0.5), (0.3, 0.12, 0.1), 16, 8)
    # Torn, deflated gas bladder sagging below the plastron (translucent).
    bl = _ellipsoid("bladder", c, M["bladder"], (-0.3, -0.1, 0.22), (0.9, 0.6, 0.14), 24, 12)
    for v in bl.data.vertices:
        v.co.z += 0.25 * math.sin(v.co.x * 5.0) * 0.3


def derelict_pod(c, M):
    """Meridian cargo pod ~2.6 m, lying on its side, dented, torn float envelope over it."""
    body = cyl("body", (0, 0, 0.62), 0.58, 2.2, c, M["hull"], rot=(0, math.pi / 2, 0.06), verts=40)
    for v in body.data.vertices:                                  # dents
        if v.co.z > 0.3 and abs(v.co.y) < 0.3:
            v.co.z -= 0.05
    for x in (-1.15, 1.15):
        cyl(f"cap{x}", (x, 0, 0.62), 0.5, 0.16, c, M["hull_dark"], rot=(0, math.pi / 2, 0.06), verts=32, r2=0.36)
    cyl("band", (0.45, 0, 0.62), 0.6, 0.22, c, M["orange"], rot=(0, math.pi / 2, 0.06), verts=40)
    # Hatch with a sprung-open door and a weak red emergency light.
    box("hatch", (-0.3, -0.52, 0.66), (0.7, 0.1, 0.56), c, M["hull_dark"], bevel=0.04)
    box("door", (-0.35, -0.66, 0.6), (0.6, 0.05, 0.5), c, M["metal"], bevel=0.02, rot=(0.0, 0.0, 0.35))
    sphere("emergency", (0.2, -0.56, 0.98), 0.05, c, M["red"])
    for x in (-0.9, 0.9):                                        # skid rails
        box(f"skid{x}", (x * 0.8, 0, 0.06), (0.7, 0.9, 0.1), c, M["metal"], bevel=0.02)
    # Torn float envelope draped over the top (flattened, rippled sheet).
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=12, size=1.0, location=(0.1, 0, 1.18))
    env = _link(c, bpy.context.active_object)
    env.name = "envelope"
    env.scale = (2.0, 1.3, 1.0)
    for v in env.data.vertices:
        r = abs(v.co.y) * 2
        v.co.z = -0.55 * r * r + 0.05 * math.sin(v.co.x * 14.0)    # drape down the sides
    env.data.materials.append(M["envelope"])
    for k in range(3):                                            # snapped rigging lines
        cyl(f"line{k}", (-0.8 + k * 0.8, -0.3, 1.45), 0.012, 0.6, c, M["metal"], rot=(0.4, 0.2 * (k - 1), 0), verts=6)


def beacon_vault(c, M):
    """Beacon vault ~2.6 m wide, 3.8 m with the mast: armoured cream vault on a float deck."""
    box("deck", (0, 0, 0.12), (2.6, 1.4, 0.24), c, M["grate"], bevel=0.03)
    box("keel", (0, 0, 0.3), (2.3, 1.2, 0.14), c, M["orange"], bevel=0.03)
    vault = cyl("vault", (0, 0, 1.2), 0.95, 1.6, c, M["hull"], verts=8)
    vault.rotation_euler.z = math.pi / 8
    cyl("roof", (0, 0, 2.08), 0.95, 0.18, c, M["hull_dark"], verts=8, r2=0.7).rotation_euler.z = math.pi / 8
    for k in range(4):                                            # armour bands
        box(f"band{k}", (0, 0, 0.6 + k * 0.42), (1.98, 1.98, 0.06), c, M["metal"], bevel=0.01)
    box("door", (0, -0.9, 1.05), (0.8, 0.12, 1.3), c, M["hull_dark"], bevel=0.04)
    box("seam_v", (0, -0.97, 1.05), (0.03, 0.02, 1.2), c, M["seam"], bevel=0.004)
    box("seam_h", (0, -0.97, 1.7), (0.76, 0.02, 0.03), c, M["seam"], bevel=0.004)
    box("rust", (0.55, -0.88, 1.5), (0.18, 0.02, 0.9), c, M["orange"], bevel=0.004)
    cyl("mast", (0.3, 0, 2.85), 0.05, 1.4, c, M["metal"], verts=10)
    for k, z in enumerate((2.5, 3.0)):                            # mast cross-arms
        box(f"arm{k}", (0.3, 0, z), (0.5 - 0.12 * k, 0.04, 0.04), c, M["metal"], bevel=0.005)
    sphere("beacon", (0.3, 0, 3.62), 0.14, c, M["beacon"])
    for k, z in enumerate((3.5, 3.74)):                           # cage rings (open, the lamp shows)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.015, location=(0.3, 0, z))
        _link(c, bpy.context.active_object).data.materials.append(M["grate"])
    box("frost_roof", (0, 0, 2.2), (1.2, 1.2, 0.03), c, M["frost"], bevel=0.01)


PROPS = {"husk_tortoise": husk_tortoise, "derelict_pod": derelict_pod, "beacon_vault": beacon_vault}


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
