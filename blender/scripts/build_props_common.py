"""Builds blender/sources/props/common.blend: props batch 1 (B-014).

One collection per prop (`prop_<name>`), real scale (PPU 128), standing on z = 0 with the
origin at the bottom centre (the sprite pivot). Worn-industrial materials reuse the Pilgrim's
paint (panel seams, grime toward the ground, chipped metal) so the set matches the ship.
Interactables (landing_pad, shelter_door, smelter, storage_crate, lamp) carry
`meridian_rim = 0.1` on every material -> mask R (Bible §9: 10% brighter rim). Deterministic:

  blender --background --factory-startup --python blender/scripts/build_props_common.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import box, cyl, flat_material, paint_material, sphere  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "common.blend")
INTERACTABLE = {"landing_pad", "shelter_door", "smelter", "storage_crate", "lamp"}


def materials(rim):
    M = {
        "panel": paint_material("panel", (188, 186, 178), (150, 146, 136)),
        "dark": paint_material("dark_metal", (82, 84, 88), (62, 62, 64)),
        "olive": paint_material("olive", (104, 112, 82), (82, 88, 64)),
        "deck": paint_material("deck", (112, 114, 116), (86, 86, 86)),
        "yellow": flat_material("hazard_yellow", (222, 172, 40), rough=0.6),
        "black": flat_material("hazard_black", (38, 36, 33), rough=0.7),
        "metal": flat_material("bare_metal", (120, 122, 126), metallic=1.0, rough=0.35),
        "glass": flat_material("glass", (26, 34, 44), emit=(120, 190, 255), strength=0.3, rough=0.1),
        "amber": flat_material("amber_light", (110, 70, 20), emit=(255, 176, 60), strength=1.0),
        "green": flat_material("green_light", (30, 80, 40), emit=(90, 255, 120), strength=1.0),
        "furnace": flat_material("furnace_glow", (90, 40, 20), emit=(255, 128, 40), strength=1.0),
        "lamp": flat_material("lamp_lens", (230, 226, 210), emit=(255, 236, 196), strength=1.0),
    }
    for m in M.values():
        m["meridian_rim"] = rim
    return M


def landing_pad(c, M):
    box("deck", (0, 0, 0.27), (3.6, 1.2, 0.16), c, M["deck"], bevel=0.03)
    for x in (-1.5, -0.5, 0.5, 1.5):
        box(f"leg_{x}", (x, 0, 0.1), (0.18, 1.0, 0.2), c, M["dark"], bevel=0.02)
    for k in range(18):                               # hazard edge on the front face
        box(f"chev_{k}", (-1.7 + k * 0.2, -0.605, 0.27), (0.1, 0.01, 0.12), c, M["yellow" if k % 2 == 0 else "black"], bevel=0)
    for x in (-1.6, 0.0, 1.6):
        box(f"edge_light_{x}", (x, -0.61, 0.36), (0.12, 0.02, 0.04), c, M["amber"], bevel=0.005)


def shelter_wall(c, M):
    box("panel", (0, 0, 1.25), (1.0, 0.25, 2.5), c, M["panel"], bevel=0.02)
    for x in (-0.38, 0.0, 0.38):
        box(f"rib_{x}", (x, -0.135, 1.25), (0.06, 0.03, 2.4), c, M["dark"], bevel=0.008)
    box("seam", (0, -0.13, 1.25), (0.98, 0.02, 0.05), c, M["dark"], bevel=0.005)
    for z in (0.1, 2.4):
        for x in (-0.44, 0.44):
            sphere(f"bolt_{x}_{z}", (x, -0.13, z), 0.025, c, M["metal"])


def shelter_door(c, M):
    for x in (-0.54, 0.54):
        box(f"post_{x}", (x, 0, 1.25), (0.12, 0.3, 2.5), c, M["dark"], bevel=0.015)
    box("lintel", (0, 0, 2.44), (1.2, 0.3, 0.12), c, M["dark"], bevel=0.015)
    box("door", (0, 0.02, 1.15), (0.96, 0.1, 2.26), c, M["panel"], bevel=0.02)
    box("window", (0, -0.035, 1.75), (0.32, 0.02, 0.26), c, M["glass"], bevel=0.01)
    box("kick", (0, -0.035, 0.18), (0.9, 0.02, 0.22), c, M["yellow"], bevel=0.005)
    box("handle", (0.34, -0.06, 1.1), (0.04, 0.05, 0.22), c, M["metal"], bevel=0.008)
    box("status", (0.54, -0.16, 1.55), (0.06, 0.02, 0.08), c, M["green"], bevel=0.005)


def smelter(c, M):
    for x in (-0.6, 0.6):
        box(f"leg_{x}", (x, 0, 0.15), (0.16, 0.9, 0.3), c, M["dark"], bevel=0.02)
    box("body", (0, 0, 0.9), (1.6, 1.0, 1.2), c, M["dark"], bevel=0.04)
    box("hopper", (-0.25, 0, 1.68), (0.7, 0.7, 0.36), c, M["panel"], bevel=0.03)
    cyl("chimney", (0.45, 0.1, 1.75), 0.14, 0.9, c, M["metal"], verts=24)
    cyl("cap", (0.45, 0.1, 2.22), 0.19, 0.05, c, M["dark"], verts=24)
    box("window", (-0.1, -0.505, 0.85), (0.6, 0.02, 0.36), c, M["furnace"], bevel=0.01)
    for k in range(5):                                # grate bars over the glow
        box(f"bar_{k}", (-0.34 + k * 0.12, -0.52, 0.85), (0.03, 0.02, 0.4), c, M["black"], bevel=0)
    box("panel_box", (0.58, -0.51, 1.15), (0.28, 0.03, 0.22), c, M["panel"], bevel=0.01)
    box("panel_led", (0.64, -0.53, 1.18), (0.05, 0.01, 0.04), c, M["amber"], bevel=0.003)


def storage_crate(c, M):
    box("crate", (0, 0, 0.4), (1.0, 0.8, 0.8), c, M["olive"], bevel=0.03)
    for z in (0.04, 0.76):
        box(f"band_{z}", (0, 0, z), (1.02, 0.82, 0.06), c, M["dark"], bevel=0.01)
    for x in (-0.47, 0.47):
        box(f"corner_{x}", (x, -0.405, 0.4), (0.07, 0.02, 0.8), c, M["dark"], bevel=0.006)
    box("stencil", (0, -0.405, 0.44), (0.5, 0.01, 0.08), c, M["yellow"], bevel=0)
    box("latch", (0, -0.42, 0.62), (0.12, 0.03, 0.1), c, M["metal"], bevel=0.008)


def lamp(c, M):
    cyl("base", (0, 0, 0.04), 0.18, 0.08, c, M["dark"], verts=32)
    cyl("pole", (0, 0, 1.08), 0.045, 2.0, c, M["panel"], verts=16)
    box("arm", (0.08, 0, 2.1), (0.22, 0.08, 0.05), c, M["dark"], bevel=0.01)
    box("head", (0.14, 0, 2.03), (0.26, 0.2, 0.12), c, M["dark"], bevel=0.02)
    box("lens", (0.14, 0, 1.965), (0.22, 0.16, 0.012), c, M["lamp"], bevel=0.004)
    box("lens_front", (0.272, 0, 2.02), (0.012, 0.16, 0.06), c, M["lamp"], bevel=0.003)
    # The side camera looks along +Y: give it glowing surfaces it can see (bulb + side lens).
    sphere("bulb", (0.14, 0, 1.93), 0.055, c, M["lamp"])
    box("lens_side", (0.14, -0.102, 2.02), (0.2, 0.008, 0.06), c, M["lamp"], bevel=0.003)


PROPS = {"landing_pad": landing_pad, "shelter_wall": shelter_wall, "shelter_door": shelter_door,
         "smelter": smelter, "storage_crate": storage_crate, "lamp": lamp}


# ---------------------------------------------------------------- B-069 aerostat + giant gear
# Built after batch 1 with its own materials, so batch 1 stays identical. Venus aerostat look
# (cream hull, orange band, grated deck, translucent cream envelope).

def materials2(rim):
    M = {
        "hull": paint_material("a_hull", (226, 206, 168), (196, 170, 70)),
        "orange": paint_material("a_orange", (214, 120, 52), (170, 120, 50), seams=False),
        "grate": flat_material("a_grate", (70, 66, 62), metallic=0.7, rough=0.5),
        "metal": flat_material("a_metal", (110, 104, 96), metallic=0.8, rough=0.45),
        "silver": paint_material("a_silver", (206, 212, 220), (170, 178, 188), seams=False, scratches=False),
        "dark": flat_material("a_dark", (52, 54, 58), metallic=0.5, rough=0.45),
        "status": flat_material("a_status", (120, 50, 16), emit=(255, 140, 60), strength=1.6),
        "cyan": flat_material("a_cyan", (30, 110, 140), emit=(90, 220, 255), strength=1.4),
    }
    env = bpy.data.materials.new("a_envelope")
    env.use_nodes = True
    pr = env.node_tree.nodes["Principled BSDF"]
    pr.inputs["Base Color"].default_value = (0.92, 0.84, 0.66, 1)
    pr.inputs["Roughness"].default_value = 0.45
    pr.inputs["Alpha"].default_value = 0.8
    M["envelope"] = env
    for m in M.values():
        m["meridian_rim"] = rim
    return M


def _own(c, ob):
    for co in list(ob.users_collection):
        co.objects.unlink(ob)
    c.objects.link(ob)
    return ob


def aerostat_deck(c, M):
    """Deck plate exactly 2.0 m long (x -1..1): flat grated top (walk line at 0.42 m), cream keel
    beam with the orange band, identical end flanges, so plates tile at a 2 m pitch."""
    box("deck", (0, 0, 0.38), (2.0, 1.2, 0.08), c, M["grate"], bevel=0.0)
    box("keel", (0, 0, 0.2), (2.0, 0.9, 0.28), c, M["hull"], bevel=0.0)
    box("band", (0, -0.46, 0.2), (2.0, 0.03, 0.08), c, M["orange"], bevel=0.0)
    for x in (-0.97, 0.97):                                      # end flanges (mirror-identical)
        box(f"flange{x}", (x, 0, 0.2), (0.06, 0.95, 0.32), c, M["metal"], bevel=0.0)
    for k in range(3):                                           # bolts at 0.5 m pitch (period divides 2 m)
        box(f"bolt{k}", (-0.5 + 0.5 * k, -0.47, 0.3), (0.04, 0.02, 0.04), c, M["metal"], bevel=0.0)


def aerostat_strut(c, M):
    """Vertical truss exactly 2.0 m tall (z 0..2), two rails and X-bracing repeating every 0.5 m,
    so struts stack seamlessly."""
    for x in (-0.12, 0.12):
        box(f"rail{x}", (x, 0, 1.0), (0.05, 0.05, 2.0), c, M["metal"], bevel=0.0)
    for k in range(4):
        z0 = 0.5 * k
        for s in (-1, 1):
            box(f"brace{k}{s}", (0, -0.01, z0 + 0.25), (0.33, 0.025, 0.025), c, M["orange"], bevel=0.0,
                rot=(0, s * math.atan2(0.5, 0.24), 0))
        box(f"tie{k}", (0, 0, z0 + 0.0125), (0.24, 0.04, 0.025), c, M["metal"], bevel=0.0)


def aerostat_cell(c, M):
    """Gas cell ~1.6 m: translucent cream envelope with three straps and a mount ring at the
    bottom (origin), a small status light."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=1.0, location=(0, 0, 1.0))
    env = _own(c, bpy.context.active_object)
    env.scale = (0.8, 0.7, 0.78)
    bpy.ops.object.shade_smooth()
    env.data.materials.append(M["envelope"])
    for k in range(3):
        a = math.pi * (k - 1) / 4
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.015, location=(0, 0, 1.0), rotation=(0, math.pi / 2, a))
        st = _own(c, bpy.context.active_object)
        st.scale = (0.81, 0.71, 0.79)
        st.data.materials.append(M["metal"])
    cyl("mount", (0, 0, 0.12), 0.32, 0.18, c, M["hull"], verts=32)
    cyl("mount_band", (0, 0, 0.12), 0.33, 0.06, c, M["orange"], verts=32)
    sphere("status", (0.0, -0.33, 0.14), 0.035, c, M["status"])


def _float_pack(c, M, body, band, light):
    """Back-mounted float cell pack (~0.5 m): two pill cells on a harness frame."""
    box("frame", (0, 0.06, 0.25), (0.26, 0.05, 0.46), c, M["dark"], bevel=0.01)
    for k, z in enumerate((0.13, 0.36)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=(0, 0, z))
        cell = _own(c, bpy.context.active_object)
        cell.scale = (0.16, 0.1, 0.1)
        bpy.ops.object.shade_smooth()
        cell.data.materials.append(body)
        box(f"band{k}", (0, 0, z), (0.05, 0.21, 0.21), c, band, bevel=0.01)
        sphere(f"light{k}", (0.1, -0.09, z + 0.03), 0.015, c, light)


def float_cell_pack_mk1(c, M):
    _float_pack(c, M, M["hull"], M["orange"], M["status"])


def float_cell_pack_mk2(c, M):
    _float_pack(c, M, M["silver"], M["cyan"], M["cyan"])


def grapple_hook(c, M):
    """Rig grapple head (~0.4 m, points +x): three tines swept back from the tip, a shaft and a
    spool; the line attaches at the tail, which sits at the origin (the sprite pivot)."""
    z, ox = 0.0, 0.19                                            # tail (spool back) at x = 0
    cyl("shaft", (ox, 0, z), 0.03, 0.26, c, M["metal"], rot=(0, math.pi / 2, 0), verts=12)
    cyl("spool", (ox - 0.14, 0, z), 0.05, 0.05, c, M["orange"], rot=(math.pi / 2, 0, 0), verts=16)
    cyl("tip", (ox + 0.16, 0, z), 0.035, 0.08, c, M["dark"], rot=(0, math.pi / 2, 0), verts=12, r2=0.0)
    for k, a in enumerate((50, 0, -50)):                         # tines fan out up/straight/down
        r = math.radians(a)
        box(f"tine{k}", (ox + 0.07 + 0.04 * math.cos(r), 0.0, z + 0.07 * math.sin(r)), (0.12, 0.02, 0.02), c, M["metal"],
            bevel=0.004, rot=(0, -r, 0))


PROPS2 = {"aerostat_deck": aerostat_deck, "aerostat_strut": aerostat_strut, "aerostat_cell": aerostat_cell,
          "float_cell_pack_mk1": float_cell_pack_mk1, "float_cell_pack_mk2": float_cell_pack_mk2,
          "grapple_hook": grapple_hook}


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for name, fn in PROPS.items():
        coll = bpy.data.collections.new(f"prop_{name}")
        scene.collection.children.link(coll)
        fn(coll, materials(0.1 if name in INTERACTABLE else 0.0))
    for name, fn in PROPS2.items():                            # B-069, after batch 1
        coll = bpy.data.collections.new(f"prop_{name}")
        scene.collection.children.link(coll)
        fn(coll, materials2(0.0))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


# ---------------------------------------------------------------- contract v2 models (B-081)
MODEL_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "common_model.blend")


def landing_pad_v2(c, M):
    """2.0 m pad module (x -1..1), 3 m deep (the Pilgrim's feet sit 1.2 m off centre in depth);
    identical ends, so modules tile at a 2 m pitch (two modules = 4 m for the Pilgrim's 3.52 m
    gear footprint)."""
    box("deck", (0, 0, 0.27), (2.0, 3.0, 0.16), c, M["deck"], bevel=0.0)
    for x in (-0.5, 0.5):
        box(f"leg_{x}", (x, 0, 0.1), (0.18, 2.8, 0.2), c, M["dark"], bevel=0.02)
    for k in range(10):                               # hazard edge on the front face (period 0.2 m divides 2 m)
        box(f"chev_{k}", (-0.9 + k * 0.2, -1.505, 0.27), (0.1, 0.01, 0.12), c, M["yellow" if k % 2 == 0 else "black"], bevel=0)
    for x in (-0.5, 0.5):
        box(f"edge_light_{x}", (x, -1.51, 0.36), (0.12, 0.02, 0.04), c, M["amber"], bevel=0.005)
    for k in range(5):                                # deck plates seams across, also 0.4 m pitch
        box(f"seam_{k}", (-0.8 + 0.4 * k, 0, 0.352), (0.02, 2.9, 0.006), c, M["dark"], bevel=0)


def shelter_door_v2(c, M):
    """Door frame on `root`, leaf on `door`; clip `open` (18 frames): the leaf slides +X behind
    the right post."""
    import math as _m
    from mathutils import Vector
    shelter_door(c, M)
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
        bone = "door" if ob.name in ("door", "window", "kick", "handle") or ob.name.startswith(("door", "window", "kick", "handle")) else "root"
        mw = ob.matrix_world.copy()
        ob.parent, ob.parent_type, ob.parent_bone = rig, "BONE", bone
        bpy.context.view_layer.update()
        ob.matrix_world = mw
    rig.animation_data_create()
    act = bpy.data.actions.new("open")
    act.use_fake_user = True
    rig.animation_data.action = act
    pb = rig.pose.bones["door"]
    for f, k in ((1, 0.0), (4, 0.08), (15, 0.92), (19, 1.0)):     # ease in/out over 18 frames
        pb.location = (0.96 * k, 0.0, 0.0)                         # bone-local X = world X
        pb.keyframe_insert("location", frame=f)
    rig.animation_data.action = None
    rig.animation_data.action = act


def lamp_v2(c, M):
    lamp(c, M)
    s = bpy.data.objects.new("socket_light", None)
    s.empty_display_size = 0.05
    c.objects.link(s)
    s.location = (0.14, 0.0, 1.93)                    # at the bulb, Unity hangs a spot light here


MODEL_PROPS = {"landing_pad": landing_pad_v2, "shelter_wall": shelter_wall, "shelter_door": shelter_door_v2,
               "smelter": smelter, "storage_crate": storage_crate, "lamp": lamp_v2}


def build_model(out_path=MODEL_OUT):
    """Contract v2 props batch 1 (B-081): one collection per prop, real scale, base at z = 0."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    for name, fn in MODEL_PROPS.items():
        coll = bpy.data.collections.new(f"prop_{name}")
        scene.collection.children.link(coll)
        fn(coll, materials(0.1 if name in INTERACTABLE else 0.0))
    scene.frame_start, scene.frame_end = 1, 19
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
