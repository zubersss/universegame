"""Builds blender/sources/props/jupiter.blend: Jupiter cloud-deck props (B-055, Bible §7.5-7.6).

Same conventions as build_props_venus.py: one collection per prop (`prop_<name>`), real scale,
standing on z = 0, origin = bottom centre. Jupiter palette: cream/rust/brick (§9), Meridian
hulls in cream with the orange band, rust-ochre NH4SH staining, ammonia frost on upper faces.

- husk_tortoise: the long-dead husk of a Ballast tortoise, a standable platform (v2, LEAD
  cycle 156): flat walk line on a pressed shell, cracked plates with two missing and ammonia
  rime in the cracks, head slumped and half hidden with an empty socket, withered legs. B-056's ballast_tortoise
  must keep this shell silhouette.
- derelict_pod: a buoyant Meridian-expedition cargo pod, battered, with a torn float envelope
  draped over it and a weak red emergency light. Interactable (salvage).
- beacon_vault: Jupiter's beacon: an armoured vault on a floating deck, lit door seams and a
  mast with the beacon lamp. Interactable.

  blender --background --factory-startup --python blender/scripts/build_props_jupiter.py
"""
import math
import random
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
        # Ballast tortoise husk v2: long-dead, dried, desaturated cream/rust; holes read dark.
        "husk_shell": paint_material("hshell", (150, 132, 112), (96, 74, 58), seams=False),
        "husk_edge": flat_material("hedge", (70, 54, 46), rough=0.85),
        "husk_hide": flat_material("hhide", (72, 62, 56), rough=0.9),
        "husk_bone": flat_material("hbone", (118, 108, 96), rough=0.85),
        "husk_rime": flat_material("hrime", (176, 184, 190), rough=0.9),
        "husk_hole": flat_material("hhole", (38, 28, 24), rough=0.95),
    }
    bl = bpy.data.materials.new("bladder")
    bl.use_nodes = True
    pr = bl.node_tree.nodes["Principled BSDF"]
    pr.inputs["Base Color"].default_value = (0.42, 0.32, 0.28, 1)
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


def _flank_y(x, z, cx=0.0, cz=0.82, rx=1.75, ry=1.2, rz=0.72):
    """Camera-side (-y) surface of the shell ellipsoid at world (x, z)."""
    lx, lz = (x - cx) / rx, (z - cz) / rz
    return -ry * math.sqrt(max(0.0, 1.0 - lx * lx - lz * lz))


def husk_tortoise(c, M):
    """Dead Ballast tortoise husk ~4.4 m long (B-055 v2, LEAD cycle 156): a long-dead, dried
    shell with a flat walkable top line (~1.3 m), cracked plates with two missing, ammonia rime
    in the cracks, the head slumped down and half hidden behind the shell, no eye (a dark empty
    socket), withered legs tucked under, one gone. Darker, desaturated cream/rust."""
    shell = _ellipsoid("shell", c, M["husk_shell"], (0, 0, 0.82), (1.75, 1.2, 0.72), 64, 32)
    for v in shell.data.vertices:                     # press the crown flat: one level walk line
        if v.co.z > 0.62:
            v.co.z = 0.62 + (v.co.z - 0.62) * 0.08
    _ellipsoid("rim", c, M["husk_edge"], (0, 0, 0.6), (1.8, 1.24, 0.12), 64, 12)
    _ellipsoid("plastron", c, M["husk_hide"], (0, 0.05, 0.4), (1.45, 0.95, 0.26))
    # Flat top plates, flush with the plateau (the walk line), two rows with gaps, two missing.
    top = 0.82 + 0.72 * (0.62 + 0.38 * 0.08)
    missing = {(1, 0), (2, 1)}
    for i in range(4):
        for j in range(2):
            x, y = -0.93 + i * 0.62, -0.32 + j * 0.64
            if (i, j) in missing:
                box(f"hole{i}{j}", (x, y, top - 0.02), (0.56, 0.58, 0.04), c, M["husk_hole"], bevel=0.01)
                continue
            box(f"plate{i}{j}", (x, y, top + 0.015), (0.56, 0.58, 0.03), c, M["husk_shell"], bevel=0.01)
    rnd = random.Random(55)
    # Flank cracks: irregular dark polylines that wander roughly along the old plate joints;
    # pale ammonia rime only in some segments (v2b: the even white grid read as stitching).
    def crack(name, x, z, steps, dx, dz, rime_p):
        for k in range(steps):
            nx, nz = x + dx + rnd.uniform(-0.05, 0.05), z + dz + rnd.uniform(-0.04, 0.04)
            mx, mz = (x + nx) / 2, (z + nz) / 2
            y = _flank_y(mx, mz)
            if y < -0.05:
                ln = math.hypot(nx - x, nz - z)
                a = -math.atan2(nz - z, nx - x)
                box(f"{name}{k}", (mx, y - 0.012, mz), (ln + 0.02, 0.03, 0.022), c, M["husk_edge"], bevel=0.004, rot=(0, a, 0))
                if rnd.random() < rime_p:
                    box(f"{name}r{k}", (mx, y - 0.026, mz), (ln * 0.7, 0.012, 0.01), c, M["husk_rime"], bevel=0.002, rot=(0, a, 0))
            x, z = nx, nz
    for k, x in enumerate((-1.28, -0.58, 0.05, 0.66, 1.22)):
        crack(f"cv{k}_", x + rnd.uniform(-0.06, 0.06), 0.7, 5, rnd.uniform(-0.04, 0.04), 0.1, 0.35)
    crack("ch_", -1.5, 0.97 + rnd.uniform(-0.02, 0.02), 12, 0.26, 0.0, 0.3)
    for k, (x, z) in enumerate(((-0.95, 0.84), (0.4, 1.06), (1.28, 0.9), (-0.2, 0.78))):
        crack(f"cs{k}_", x, z, 3, rnd.choice((-1, 1)) * 0.08, rnd.uniform(-0.07, 0.07), 0.5)
    # Missing flank plates: ragged dark-brown recesses (overlapping rotated pieces), not clean boxes.
    for k, (x, z) in enumerate(((-0.31, 1.12), (0.93, 0.84))):
        for p in range(4):
            px, pz = x + rnd.uniform(-0.14, 0.14), z + rnd.uniform(-0.05, 0.05)
            box(f"flank_hole{k}_{p}", (px, _flank_y(px, pz) - 0.02, pz),
                (rnd.uniform(0.18, 0.3), 0.04, rnd.uniform(0.09, 0.16)), c, M["husk_hole"], bevel=0.01,
                rot=(0, rnd.uniform(-0.5, 0.5), 0))
    # Head slumped to the ground and mostly behind the shell (+y is away from the camera); dark,
    # weathered bone; the socket is a slanted shadowed hollow, not a round pupil.
    neck = _ellipsoid("neck", c, M["husk_hide"], (1.6, 0.35, 0.3), (0.32, 0.15, 0.1), 20, 10)
    neck.rotation_euler = (0, 0.6, 0)
    skull = _ellipsoid("skull", c, M["husk_bone"], (1.9, 0.45, 0.14), (0.22, 0.16, 0.13), 20, 10)
    skull.rotation_euler = (0, 0.45, -0.4)
    sk = _ellipsoid("socket", c, M["husk_hole"], (1.98, 0.3, 0.18), (0.09, 0.03, 0.035), 12, 6)
    sk.rotation_euler = (0, 0.5, 0)
    _ellipsoid("brow", c, M["husk_hide"], (1.95, 0.29, 0.22), (0.1, 0.035, 0.025), 12, 6)
    _ellipsoid("jaw", c, M["husk_bone"], (1.95, 0.42, 0.04), (0.18, 0.12, 0.035), 16, 8)
    # Withered legs tucked under the rim (thin, bent), the rear left one gone (a stub).
    for k, (x, y, rot) in enumerate(((-1.05, -0.62, -0.9), (1.0, -0.62, 0.9), (1.05, 0.6, 0.9))):
        cyl(f"leg{k}", (x, y, 0.22), 0.06, 0.42, c, M["husk_hide"], rot=(0, rot, 0), verts=10, r2=0.035)
    _ellipsoid("stub", c, M["husk_hide"], (-1.05, 0.6, 0.3), (0.09, 0.07, 0.06), 12, 6)
    # Dried, torn gas bladder sagging under the plastron.
    bl = _ellipsoid("bladder", c, M["bladder"], (-0.25, 0.0, 0.16), (0.85, 0.55, 0.1), 24, 12)
    for v in bl.data.vertices:
        v.co.z += 0.08 * math.sin(v.co.x * 5.0)


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
