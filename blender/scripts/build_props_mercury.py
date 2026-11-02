"""Builds blender/sources/props/mercury.blend: Mercury POI props (B-033, Bible §7.3) for the
flare shelters, the Mercury beacon, the Warden-guarded Sowing vault and Solarite.

Same conventions as build_props_mars.py: one collection per prop (`prop_<name>`), real scale
(PPU 128, <= 4 m for the 512 px cap), standing on z = 0, origin = bottom centre. Mercury
palette (white / black / violet): flare-scorched ceramic white shells, black regolith, violet
status light. Harsh airless light, so shapes are bold and bevelled for clean normals.
Emission: shelter_door status strip, meridian_beacon lamp (pulse-ready), warden_vault_gate
seams, solarite_cluster crystals (fused by flares). Interactables carry meridian_rim 0.1.
Deterministic:

  blender --background --factory-startup --python blender/scripts/build_props_mercury.py
"""
import math
import os
import random
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import box, cyl, flat_material, paint_material, sphere  # noqa: E402
from build_props_earth import strut  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "mercury.blend")
INTERACTABLE = {"shelter_door", "meridian_beacon", "warden_vault_gate", "solarite_cluster"}


def materials(rim):
    M = {
        "shell": paint_material("ceramic_shell", (228, 226, 222), (52, 46, 48)),      # white, flare scorch
        "shell_dark": paint_material("shell_band", (40, 38, 44), (20, 18, 22)),
        "regolith": paint_material("regolith", (92, 90, 96), (60, 58, 64), seams=False, scratches=False),
        "metal": flat_material("scorched_metal", (64, 60, 62), metallic=0.8, rough=0.45),
        "door": paint_material("door_panel", (210, 208, 206), (60, 52, 56)),
        "violet": flat_material("status_violet", (60, 40, 90), emit=(176, 120, 255), strength=1.2),
        "lamp": flat_material("beacon_lamp", (60, 40, 90), emit=(200, 160, 255), strength=1.0, rough=0.2),
        "vault": paint_material("vault_stone", (34, 32, 40), (18, 16, 22), seams=False, scratches=False),   # flecks read as stars
        "seam": flat_material("vault_seam", (50, 30, 80), emit=(160, 110, 255), strength=1.2),
        "solarite": flat_material("solarite", (255, 214, 140), emit=(255, 200, 110), strength=1.6, rough=0.15),
        "solarite_core": flat_material("solarite_core", (255, 246, 220), emit=(255, 240, 210), strength=2.2, rough=0.1),
    }
    for m in M.values():
        m["meridian_rim"] = rim
    return M


def _link(c, ob):
    for co in list(ob.users_collection):
        co.objects.unlink(ob)
    c.objects.link(ob)


def flare_shelter(c, M):
    """Half-buried ceramic dome bunker, 3.6 m wide: thick white shell scorched on top, a dark
    band, an entrance recess, regolith banked against it (radiation shielding)."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.8, location=(0, 0, 0.0))
    dome = bpy.context.active_object
    dome.name = "dome"
    dome.scale = (1.0, 0.8, 1.05)
    _link(c, dome)
    bm = bmesh.new()                                      # half-buried: keep only z >= 0
    bm.from_mesh(dome.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context="VERTS")
    bm.to_mesh(dome.data)
    bm.free()
    dome.data.materials.append(M["shell"])
    bpy.ops.object.shade_smooth()
    box("band", (0, 0, 0.55), (3.5, 2.9, 0.16), c, M["shell_dark"], bevel=0.06)
    box("entry", (0.0, -1.45, 0.62), (0.9, 0.5, 1.2), c, M["shell_dark"], bevel=0.08)    # in front of the band
    box("bank_l", (-1.45, 0, 0.2), (0.8, 2.6, 0.4), c, M["regolith"], bevel=0.18)
    box("bank_r", (1.45, 0, 0.2), (0.8, 2.6, 0.4), c, M["regolith"], bevel=0.18)
    cyl("vent", (0.7, 0, 1.75), 0.12, 0.3, c, M["metal"], verts=12)
    box("status", (0.0, -1.72, 1.3), (0.5, 0.03, 0.07), c, M["violet"], bevel=0.01)


def shelter_door(c, M):
    """Heavy blast door 1.2 x 2.4 m in a dark frame, chevron bands, violet status strip."""
    box("frame", (0, 0, 1.25), (1.4, 0.3, 2.5), c, M["shell_dark"], bevel=0.05)
    box("door", (0, -0.12, 1.2), (1.16, 0.12, 2.3), c, M["door"], bevel=0.04)
    for k, z in enumerate((0.55, 1.2, 1.85)):
        box(f"rib_{k}", (0, -0.2, z), (1.0, 0.04, 0.08), c, M["metal"], bevel=0.01)
    box("status", (0, -0.2, 2.25), (0.6, 0.03, 0.06), c, M["violet"], bevel=0.01)
    box("sill", (0, 0, 0.05), (1.5, 0.5, 0.1), c, M["metal"], bevel=0.02)


def meridian_beacon(c, M):
    """Squat tripod beacon with a heat-shield cap over the lamp (it lives in a flare shelter)."""
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        strut(c, f"leg_{k}", (0.8 * math.cos(a), 0.0), (0.0, 1.9), 0.07, M["metal"])
    cyl("mast", (0, 0, 2.35), 0.06, 1.0, c, M["metal"], verts=16)                   # runs up to the cap (no floating cap)
    sphere("lamp", (0, 0, 2.62), 0.12, c, M["lamp"])
    cyl("cap", (0, 0, 2.86), 0.34, 0.08, c, M["shell"], verts=24, r2=0.12)        # flare shield
    box("plinth", (0, 0, 0.08), (1.8, 1.2, 0.16), c, M["shell_dark"], bevel=0.05)


def warden_vault_gate(c, M):
    """Monolithic dark gate 3.6 x 3.2 m: two leaves of faceted black stone split by a glowing
    violet seam, with a stepped lintel and seam lines (Warden architecture, as on Mars)."""
    box("lintel", (0, 0, 3.0), (3.6, 0.9, 0.4), c, M["vault"], bevel=0.06)
    box("lintel_2", (0, 0, 3.3), (2.8, 0.8, 0.2), c, M["vault"], bevel=0.05)
    for sx in (-1, 1):
        box(f"jamb_{sx}", (sx * 1.6, 0, 1.4), (0.4, 0.9, 2.8), c, M["vault"], bevel=0.05)
        box(f"leaf_{sx}", (sx * 0.71, -0.1, 1.4), (1.38, 0.5, 2.78), c, M["vault"], bevel=0.04)
        for k, z in enumerate((0.8, 1.6, 2.3)):
            box(f"line_{sx}_{k}", (sx * 0.71, -0.36, z), (1.1, 0.02, 0.04), c, M["seam"], bevel=0.005)
    box("seam", (0, -0.36, 1.4), (0.05, 0.02, 2.7), c, M["seam"], bevel=0.005)
    box("step", (0, -0.2, 0.08), (3.8, 1.3, 0.16), c, M["vault"], bevel=0.04)


def solarite_cluster(c, M):
    """Flare-fused crystal cluster ~1.3 m: amber-white hexagonal spires on a scorched basalt
    boss, all emissive (harvestable glow), brightest cores in the tallest spires."""
    rnd = random.Random(33005)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.45, location=(0, 0, 0.23))
    boss = bpy.context.active_object
    boss.name = "boss"
    boss.scale = (1.4, 1.0, 0.5)
    _link(c, boss)
    boss.data.materials.append(M["metal"])
    bpy.ops.object.shade_flat()
    for k in range(9):
        h = rnd.uniform(0.45, 1.15) if k else 1.2
        lean = rnd.uniform(-0.45, 0.45) if k else 0.05
        x = rnd.uniform(-0.4, 0.4) if k else 0.0
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.09 + 0.06 * h, radius2=0.0, depth=h,
                                        location=(x + math.sin(lean) * h / 2, rnd.uniform(-0.15, 0.15),
                                                  0.2 + math.cos(lean) * h / 2),
                                        rotation=(rnd.uniform(-0.2, 0.2), lean, rnd.uniform(0, 6.28)))
        ob = bpy.context.active_object
        ob.name = f"spire_{k}"
        _link(c, ob)
        ob.data.materials.append(M["solarite_core"] if h > 0.95 else M["solarite"])
        bpy.ops.object.shade_flat()


PROPS = {"flare_shelter": flare_shelter, "shelter_door": shelter_door, "meridian_beacon": meridian_beacon,
         "warden_vault_gate": warden_vault_gate, "solarite_cluster": solarite_cluster}


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


# ---------------------------------------------------------------- contract v2 models (B-095)
MODEL_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "mercury_model.blend")


def _door_rig(c, leaf_names, slide=(1.16, 0.0, 0.0), frames=18):
    """Frame on `root`, the leaf parts on `door`; clip `open`: the leaf slides by `slide`
    (world axes, bone-local X/Y/Z = world X/Z/-Y for an upright bone) with ease in/out."""
    from mathutils import Vector
    ad = bpy.data.armatures.new("door_rig")
    rig = bpy.data.objects.new("door_rig", ad)
    c.objects.link(rig)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    r = ad.edit_bones.new("root")
    r.head, r.tail = Vector((0, 0, 0)), Vector((0, 0, 0.5))
    d = ad.edit_bones.new("door")
    d.head, d.tail, d.parent = Vector((0, 0, 0)), Vector((0, 0, 0.5)), r
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.update()
    for ob in list(c.objects):
        if ob.type != "MESH":
            continue
        bone = "door" if any(ob.name == n or ob.name.startswith(n + "_") or ob.name.startswith(n + ".") for n in leaf_names) else "root"
        mw = ob.matrix_world.copy()
        ob.parent, ob.parent_type, ob.parent_bone = rig, "BONE", bone
        bpy.context.view_layer.update()
        ob.matrix_world = mw
    rig.animation_data_create()
    act = bpy.data.actions.new("open")
    act.use_fake_user = True
    rig.animation_data.action = act
    pb = rig.pose.bones["door"]
    sx, sy, sz = slide
    for f, k in ((1, 0.0), (4, 0.08), (frames - 3, 0.92), (frames + 1, 1.0)):
        pb.location = (sx * k, sz * k, -sy * k)
        pb.keyframe_insert("location", frame=f)
    return rig


def shelter_door_v2(c, M):
    shelter_door(c, M)
    _door_rig(c, ["door", "rib", "status"])


def equipment_locker(c, M):
    """Mercury equipment locker ~1.0 x 0.6 x 2.0 m: ceramic-white double doors in a dark frame,
    chevron vents, two violet status LEDs, bolted to a plinth."""
    box("body", (0, 0, 1.0), (1.0, 0.6, 2.0), c, M["shell_dark"], bevel=0.03)
    for s in (-1, 1):
        box(f"door_{s}", (s * 0.245, -0.31, 1.02), (0.46, 0.04, 1.86), c, M["door"], bevel=0.015)
        box(f"handle_{s}", (s * 0.06, -0.345, 1.0), (0.03, 0.03, 0.22), c, M["metal"], bevel=0.005)
        for k in range(4):
            box(f"vent_{s}_{k}", (s * 0.245, -0.335, 0.3 + 0.08 * k), (0.3, 0.01, 0.025), c, M["shell_dark"], bevel=0.0)
        box(f"led_{s}", (s * 0.245, -0.34, 1.88), (0.1, 0.01, 0.03), c, M["violet"], bevel=0.003)
    box("plinth", (0, 0, 0.04), (1.1, 0.7, 0.08), c, M["metal"], bevel=0.015)


def _solarite(c, M, state):
    """Three states of the cluster (B-095): glowing (v1), crusted (flare scorch over dimmed
    crystals, a few cores still showing), cut (harvested: short flat-topped stumps, faint glow)."""
    rnd = random.Random(33005)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.45, location=(0, 0, 0.23))
    boss = bpy.context.active_object
    boss.name = "boss"
    boss.scale = (1.4, 1.0, 0.5)
    _link(c, boss)
    boss.data.materials.append(M["metal"])
    bpy.ops.object.shade_flat()
    for k in range(9):
        h = rnd.uniform(0.45, 1.15) if k else 1.2
        lean = rnd.uniform(-0.45, 0.45) if k else 0.05
        x = rnd.uniform(-0.4, 0.4) if k else 0.0
        y = rnd.uniform(-0.15, 0.15)
        rot = (rnd.uniform(-0.2, 0.2), lean, rnd.uniform(0, 6.28))
        if state == "cut":
            hh = min(h, 0.22)                                     # stumps, flat tops
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.09 + 0.06 * h, depth=hh,
                                                location=(x + math.sin(lean) * hh / 2, y, 0.2 + math.cos(lean) * hh / 2), rotation=rot)
            ob = bpy.context.active_object
            ob.data.materials.append(M["solarite_dim"])
        else:
            bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.09 + 0.06 * h, radius2=0.0, depth=h,
                                            location=(x + math.sin(lean) * h / 2, y, 0.2 + math.cos(lean) * h / 2), rotation=rot)
            ob = bpy.context.active_object
            if state == "glowing":
                ob.data.materials.append(M["solarite_core"] if h > 0.95 else M["solarite"])
            else:                                                 # crusted: scorch over all but two cores
                ob.data.materials.append(M["solarite_core"] if h > 1.05 else M["crust"])
        ob.name = f"spire_{k}"
        _link(c, ob)
        bpy.ops.object.shade_flat()
    if state == "crusted":
        for k in range(5):                                        # scorch crust lumps between spires
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.1, 0.18),
                                                  location=(rnd.uniform(-0.45, 0.45), rnd.uniform(-0.2, 0.2), rnd.uniform(0.3, 0.55)))
            lump = bpy.context.active_object
            _link(c, lump)
            lump.data.materials.append(M["crust"])
            bpy.ops.object.shade_flat()


MODEL_PROPS = {"flare_shelter": flare_shelter, "shelter_door": shelter_door_v2, "meridian_beacon": meridian_beacon,
               "warden_vault_gate": warden_vault_gate, "equipment_locker": equipment_locker,
               "solarite_cluster": lambda c, M: _solarite(c, M, "glowing"),
               "solarite_crusted": lambda c, M: _solarite(c, M, "crusted"),
               "solarite_cut": lambda c, M: _solarite(c, M, "cut")}
MODEL_INTERACTABLE = INTERACTABLE | {"equipment_locker", "solarite_crusted", "solarite_cut"}


def build_model(out_path=MODEL_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    for name, fn in MODEL_PROPS.items():
        coll = bpy.data.collections.new(f"prop_{name}")
        scene.collection.children.link(coll)
        M = materials(0.1 if name in MODEL_INTERACTABLE else 0.0)
        M["crust"] = paint_material("solarite_crust", (54, 44, 50), (30, 24, 28), seams=False, scratches=False)
        M["solarite_dim"] = flat_material("solarite_dim", (200, 170, 120), emit=(255, 200, 110), strength=0.35, rough=0.3)
        for m in (M["crust"], M["solarite_dim"]):
            m["meridian_rim"] = 0.1 if name in MODEL_INTERACTABLE else 0.0
        fn(coll, M)
    scene.frame_start, scene.frame_end = 1, 19
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
