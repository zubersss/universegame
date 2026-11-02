"""Builds blender/sources/creatures/jupiter.blend: Jupiter cloud-column creatures (B-056, Bible §7.6).

Fliers and floaters, so no ground: each creature is centred on the origin, sheet pivot = centre
(as the Venus fliers, B-032). Same clip set and frame numbering as every creature (idle, walk,
attack, hurt, death; build_creatures_earth CLIP_*), so the Unity loader needs nothing new.
Rigid parts ride bones (the Venus gondola/sac approach): robust, no weight painting. Jupiter
palette (§9): cream, rust, brick; emission where the Bible says glow.

  * stormglider (~3 m span manta floater, 320 px): cream back, brick belly, rust wing edges
    with pale-gold glow spots. Wings flap about the body axis and never go flat (a flat wing is
    edge-on to the side camera and vanishes).
  * lightning_eel (~3.2 m, 320 px, Deck 2): dark umber body in 8 segments undulating in the side
    plane, cyan-white emissive stripe and spots along the body, glowing mouth on attack.
  * belt_wasp (~0.45 m swarm unit, 128 px, Deck 1): rust carapace with cream bands, radiation-
    adapted (pale yellow-green emissive stinger and eyes), two wing pairs, never flat.
  * ballast_tortoise (huge slow floater, 400 px, serpent precedent D-042: 5 columns, 25 of the
    keyed frames): the living animal of B-055's husk_tortoise. Same shell silhouette (pressed flat
    crown, rim ridge), head up, four paddling flippers, an inflated gas bladder below. Its death
    clip ends close to the husk pose (head down, flippers limp, bladder deflated).

  blender --background --factory-startup --python blender/scripts/build_creatures_jupiter.py
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_creatures_earth import CLIP_LEN, CLIP_ORDER, CLIP_START, set_pose  # noqa: E402
from build_pilgrim import flat_material, paint_material  # noqa: E402
from build_surveyor import _constant  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "creatures", "jupiter.blend")


# ---------------------------------------------------------------- helpers

def _select_only(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)


def _frames():
    for name in CLIP_ORDER:
        for i in range(CLIP_LEN[name]):
            yield name, i, CLIP_START[name] + i


def make_rig(sp, coll, bones):
    """bones: [(name, head, tail, parent_name|None)]."""
    ad = bpy.data.armatures.new(f"{sp}_rig")
    rig = bpy.data.objects.new(f"{sp}_rig", ad)
    coll.objects.link(rig)
    _select_only(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = ad.edit_bones
    for name, head, tail, parent in bones:
        b = eb.new(name)
        b.head, b.tail = Vector(head), Vector(tail)
        if parent:
            b.parent = eb[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


def part(coll, rig, bone, name, m, loc, scale, rot=(0, 0, 0), kind="sphere", segs=24):
    """A rigid mesh part parented to `bone`, keeping its world placement."""
    if kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=max(8, segs // 2), radius=1.0, location=loc)
    elif kind == "cone":
        bpy.ops.mesh.primitive_cone_add(vertices=segs, radius1=1.0, radius2=0.0, depth=2.0, location=loc)
    else:
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=loc)
    ob = bpy.context.active_object
    ob.name = f"{rig.name[:-4]}_{name}"
    ob.scale = scale
    ob.rotation_euler = rot
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    if kind != "cube":
        bpy.ops.object.shade_smooth()
    ob.data.materials.append(m)
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent, ob.parent_type, ob.parent_bone = rig, "BONE", bone
    bpy.context.view_layer.update()
    ob.matrix_world = mw
    return ob


def set_pose_x(rig, name, deg):
    """Rotate pose bone `name` by `deg` about the world X axis (the body axis: wing flap)."""
    pb = rig.pose.bones[name]
    M = rig.data.bones[name].matrix_local.to_3x3()
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (M.inverted() @ Matrix.Rotation(math.radians(deg), 3, "X") @ M).to_quaternion()


def key_all(rig, f, extra=()):
    rig.keyframe_insert("rotation_euler", frame=f)
    rig.keyframe_insert("location", frame=f)
    for pb in rig.pose.bones:
        pb.keyframe_insert("rotation_quaternion", frame=f)
    for ob, path in extra:
        ob.keyframe_insert(path, frame=f)


def finish(objs):
    for ob in objs:
        if ob.animation_data and ob.animation_data.action:
            _constant(ob.animation_data.action)


def new_coll(scene, sp):
    coll = bpy.data.collections.new(sp)
    scene.collection.children.link(coll)
    return coll


# ---------------------------------------------------------------- stormglider

def build_stormglider(scene):
    sp = "stormglider"
    coll = new_coll(scene, sp)
    rig = make_rig(sp, coll, [
        ("root", (-0.2, 0, 0), (0.4, 0, 0), None),
        ("wing_L", (0.0, -0.2, 0), (0.0, -1.4, 0), "root"),     # near wing (camera at -y)
        ("wing_R", (0.0, 0.2, 0), (0.0, 1.4, 0), "root"),
        ("tail", (-0.7, 0, 0), (-1.5, 0, 0), "root"),
    ])
    back = paint_material(f"{sp}_back", (222, 204, 170), (176, 140, 104), seams=False, scratches=False)
    belly = flat_material(f"{sp}_belly", (150, 84, 60), rough=0.7)
    edge = flat_material(f"{sp}_edge", (170, 96, 56), rough=0.6)
    glow = flat_material(f"{sp}_glow", (120, 96, 40), emit=(255, 226, 150), strength=1.8)
    eye = flat_material(f"{sp}_eye", (24, 18, 16), rough=0.3)
    part(coll, rig, "root", "body", back, (0.1, 0, 0.03), (0.75, 0.42, 0.16))
    part(coll, rig, "root", "belly", belly, (0.1, 0, -0.04), (0.7, 0.38, 0.12))
    for s in (-1, 1):                                            # cephalic fins (manta horns)
        part(coll, rig, "root", f"horn{s}", belly, (0.82, 0.18 * s, -0.02), (0.18, 0.04, 0.07), rot=(0, 0.3, 0))
    part(coll, rig, "root", "eye", eye, (0.72, -0.3, 0.04), (0.04, 0.03, 0.04), segs=12)
    for side, s in (("wing_L", -1), ("wing_R", 1)):
        part(coll, rig, side, f"wing{s}", back, (-0.05, 0.85 * s, 0.0), (0.55, 0.75, 0.035), rot=(0, 0, -0.35 * s))
        part(coll, rig, side, f"wedge{s}", edge, (-0.3, 1.25 * s, 0.0), (0.28, 0.28, 0.03), rot=(0, 0, -0.6 * s))
        for k in range(3):
            part(coll, rig, side, f"spot{s}{k}", glow, (0.05 - 0.22 * k, (0.7 + 0.2 * k) * s, 0.03),
                 (0.05, 0.05, 0.015), segs=10)
    part(coll, rig, "tail", "tail", belly, (-1.1, 0, 0.0), (0.45, 0.025, 0.025), kind="cone", segs=10,
         rot=(0, math.pi / 2, 0))
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        s2 = math.sin(2 * math.pi * t)
        pitch, z, flap, amp, tail = 0.0, 0.0, 35.0, 10.0, 0.0
        if name == "idle":
            z, amp, tail = 0.05 * s2, 10.0, 6 * s2
        elif name == "walk":
            amp, pitch, tail = 25.0, -5.0, 10 * math.sin(4 * math.pi * t)
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            pitch, flap, amp = -28 * k, 35 - 15 * k, 5.0                   # dives, wings swept back
        elif name == "hurt":
            k = [1.0, 0.5][i]
            pitch, z, amp = 14 * k, 0.06 * k, 4.0
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            pitch, z, flap, amp, tail = 50 * k, -0.3 * k, 35 - 10 * k, 0.0, -20 * k   # tumbles, wings droop
        f_ang = flap + amp * s2
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        set_pose_x(rig, "wing_L", f_ang)                         # near wing up; never flat (>= 20 deg)
        set_pose_x(rig, "wing_R", -f_ang)
        set_pose(rig, "tail", tail)
        key_all(rig, f)
    finish([rig])


# ---------------------------------------------------------------- lightning eel

def build_lightning_eel(scene):
    sp = "lightning_eel"
    coll = new_coll(scene, sp)
    n, seg = 8, 0.38
    bones = [("root", (1.4, 0, 0), (1.0, 0, 0), None)]
    for k in range(n):
        x0 = 1.4 - k * seg
        bones.append((f"s{k}", (x0, 0, 0), (x0 - seg, 0, 0), "root" if k == 0 else f"s{k - 1}"))
    rig = make_rig(sp, coll, bones)
    skin = flat_material(f"{sp}_skin", (64, 52, 46), rough=0.5)
    belly = flat_material(f"{sp}_belly", (118, 92, 70), rough=0.6)
    stripe = flat_material(f"{sp}_stripe", (60, 110, 130), emit=(170, 240, 255), strength=2.2)
    mouth = flat_material(f"{sp}_mouth", (80, 120, 140), emit=(200, 250, 255), strength=2.6)
    eye = flat_material(f"{sp}_eye", (40, 90, 110), emit=(170, 240, 255), strength=1.5)
    for k in range(n):
        cx = 1.4 - (k + 0.5) * seg
        r = 0.15 * (1 - 0.65 * (k / (n - 1)) ** 1.4)
        part(coll, rig, f"s{k}", f"seg{k}", skin, (cx, 0, 0), (seg * 0.62, r, r * 1.05))
        part(coll, rig, f"s{k}", f"bel{k}", belly, (cx, 0, -r * 0.35), (seg * 0.55, r * 0.8, r * 0.6))
        part(coll, rig, f"s{k}", f"str{k}", stripe, (cx, -r * 0.55, r * 0.2), (seg * 0.5, r * 0.5, r * 0.12))
        if k % 2 == 0:
            part(coll, rig, f"s{k}", f"spot{k}", stripe, (cx, -r * 0.8, -r * 0.2), (0.03, 0.02, 0.03), segs=10)
    part(coll, rig, "s0", "head", skin, (1.48, 0, 0.0), (0.2, 0.13, 0.12))
    part(coll, rig, "s0", "mouth", mouth, (1.64, 0, -0.03), (0.06, 0.08, 0.025))
    part(coll, rig, "s0", "eye", eye, (1.56, -0.11, 0.04), (0.025, 0.015, 0.025), segs=10)
    part(coll, rig, f"s{n - 1}", "fin", belly, (1.4 - n * seg - 0.08, 0, 0), (0.14, 0.02, 0.08))
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        amp, ph, pitch, z = 9.0, 2 * math.pi * t, 0.0, 0.0
        if name == "idle":
            amp, z = 6.0, 0.03 * math.sin(ph)
        elif name == "walk":
            amp = 14.0
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            amp, pitch = 6.0 + 10 * k, -10 * k                    # strikes forward-down, body coils
        elif name == "hurt":
            amp, pitch = 18.0 * [1.0, 0.5][i], 10.0
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            amp, pitch, z = 12 * (1 - k), 70 * k, -0.4 * k          # goes limp, sinks head-down
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        for k in range(n):
            set_pose(rig, f"s{k}", amp * math.sin(ph - 0.9 * k) * (0.4 + 0.6 * k / n))
        key_all(rig, f)
    finish([rig])


# ---------------------------------------------------------------- belt wasp

def build_belt_wasp(scene):
    sp = "belt_wasp"
    coll = new_coll(scene, sp)
    rig = make_rig(sp, coll, [
        ("root", (-0.05, 0, 0), (0.05, 0, 0), None),
        ("abd", (-0.05, 0, 0), (-0.22, 0, -0.04), "root"),
        ("wf_L", (0.02, -0.03, 0.05), (0.02, -0.2, 0.05), "root"),
        ("wf_R", (0.02, 0.03, 0.05), (0.02, 0.2, 0.05), "root"),
        ("wh_L", (-0.03, -0.03, 0.05), (-0.03, -0.16, 0.05), "root"),
        ("wh_R", (-0.03, 0.03, 0.05), (-0.03, 0.16, 0.05), "root"),
    ])
    rust = flat_material(f"{sp}_rust", (150, 78, 44), rough=0.45)
    cream = flat_material(f"{sp}_cream", (226, 206, 168), rough=0.5)
    dark = flat_material(f"{sp}_dark", (40, 30, 26), rough=0.4)
    sting = flat_material(f"{sp}_sting", (110, 130, 40), emit=(220, 255, 120), strength=2.0)
    wing = flat_material(f"{sp}_wing", (210, 200, 176), rough=0.3)
    part(coll, rig, "root", "head", rust, (0.09, 0, 0.01), (0.045, 0.04, 0.04))
    part(coll, rig, "root", "eye", sting, (0.11, -0.03, 0.02), (0.015, 0.01, 0.018), segs=10)
    part(coll, rig, "root", "thorax", rust, (0.01, 0, 0.0), (0.055, 0.045, 0.045))
    for k in range(3):                                               # banded abdomen
        part(coll, rig, "abd", f"abd{k}", rust if k % 2 == 0 else cream,
             (-0.09 - 0.05 * k, 0, -0.012 - 0.008 * k), (0.035, 0.045 - 0.006 * k, 0.04 - 0.006 * k))
    part(coll, rig, "abd", "sting", sting, (-0.25, 0, -0.04), (0.04, 0.01, 0.01), kind="cone", segs=8,
         rot=(0, -math.pi / 2, 0))
    for k, x in enumerate((0.04, 0.0, -0.04)):                        # legs, tucked
        part(coll, rig, "root", f"leg{k}", dark, (x, -0.03, -0.05), (0.008, 0.008, 0.035), rot=(0, 0.4, 0))
    for b, s, ln in (("wf_L", -1, 0.11), ("wf_R", 1, 0.11), ("wh_L", -1, 0.08), ("wh_R", 1, 0.08)):
        hx = 0.02 if b.startswith("wf") else -0.03
        part(coll, rig, b, f"{b}_m", wing, (hx - 0.02, s * (0.03 + ln), 0.05), (0.035, ln, 0.004))
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        s2 = math.sin(2 * math.pi * t * 2)                             # fast beat
        pitch, z, base, amp, abd = 0.0, 0.0, 40.0, 18.0, 0.0
        if name == "idle":
            z = 0.01 * math.sin(2 * math.pi * t)
        elif name == "walk":
            pitch, amp = -10.0, 22.0
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            pitch, abd = 15 * k, 55 * k                                # abdomen curls forward to sting
        elif name == "hurt":
            pitch, amp = 25.0 * [1.0, 0.5][i], 6.0
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            pitch, z, base, amp, abd = 150 * k, -0.08 * k, 40 - 15 * k, 0.0, 30 * k   # flips and falls
        a = base + amp * s2
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        set_pose_x(rig, "wf_L", a)
        set_pose_x(rig, "wf_R", -a)
        set_pose_x(rig, "wh_L", a * 0.85)
        set_pose_x(rig, "wh_R", -a * 0.85)
        set_pose(rig, "abd", -abd)
        key_all(rig, f)
    finish([rig])


# ---------------------------------------------------------------- ballast tortoise

def build_ballast_tortoise(scene):
    """Living Ballast tortoise; shell and proportions match props/jupiter/husk_tortoise
    (shell ellipsoid 1.75 x 1.2 x 0.72 with the crown pressed flat), centred on the origin."""
    sp = "ballast_tortoise"
    coll = new_coll(scene, sp)
    zc = 0.0                                                          # shell centre (husk: 0.82)
    rig = make_rig(sp, coll, [
        ("root", (0, 0, zc), (0.4, 0, zc), None),
        ("neck", (1.55, 0, zc - 0.1), (1.95, 0, zc - 0.02), "root"),
        ("head", (1.95, 0, zc - 0.02), (2.3, 0, zc - 0.05), "neck"),
        ("ff_L", (1.0, -0.75, zc - 0.25), (1.6, -1.0, zc - 0.45), "root"),
        ("ff_R", (1.0, 0.75, zc - 0.25), (1.6, 1.0, zc - 0.45), "root"),
        ("hf_L", (-1.1, -0.7, zc - 0.25), (-1.5, -0.9, zc - 0.45), "root"),
        ("hf_R", (-1.1, 0.7, zc - 0.25), (-1.5, 0.9, zc - 0.45), "root"),
        ("bladder", (0, 0, zc - 0.5), (0, 0, zc - 0.9), "root"),
    ])
    shell_m = paint_material(f"{sp}_shell", (196, 156, 116), (142, 92, 62), seams=False, scratches=False)
    edge_m = flat_material(f"{sp}_edge", (120, 72, 50), rough=0.75)
    hide_m = flat_material(f"{sp}_hide", (150, 112, 92), rough=0.8)
    belly_m = flat_material(f"{sp}_belly", (210, 186, 150), rough=0.7)
    eye_m = flat_material(f"{sp}_eye", (24, 18, 16), rough=0.2)
    bl_m = bpy.data.materials.new(f"{sp}_bladder")
    bl_m.use_nodes = True
    pr = bl_m.node_tree.nodes["Principled BSDF"]
    pr.inputs["Base Color"].default_value = (0.78, 0.5, 0.38, 1)
    pr.inputs["Roughness"].default_value = 0.4
    pr.inputs["Alpha"].default_value = 0.72
    pr.inputs["Emission Color"].default_value = (1.0, 0.55, 0.3, 1)
    pr.inputs["Emission Strength"].default_value = 0.25           # faint warm gas glow
    shell = part(coll, rig, "root", "shell", shell_m, (0, 0, zc), (1.75, 1.2, 0.72), segs=48)
    for v in shell.data.vertices:                                 # same pressed-flat crown as the husk
        if v.co.z > 0.62:
            v.co.z = 0.62 + (v.co.z - 0.62) * 0.08
    part(coll, rig, "root", "rim", edge_m, (0, 0, zc - 0.22), (1.8, 1.24, 0.12), segs=48)
    part(coll, rig, "root", "plastron", belly_m, (0, 0.05, zc - 0.42), (1.45, 0.95, 0.26))
    for k, x in enumerate((-1.24, -0.62, 0.0, 0.62, 1.24)):        # living scute seams on the flank
        lx = x / 1.75
        for j, zz in enumerate((-0.05, 0.15, 0.3)):
            lz = zz / 0.72
            y = -1.2 * math.sqrt(max(0.0, 1 - lx * lx - lz * lz))
            if y < -0.05:
                part(coll, rig, "root", f"seam{k}{j}", edge_m, (x, y - 0.01, zc + zz), (0.02, 0.02, 0.08), kind="cube")
    part(coll, rig, "neck", "neck", hide_m, (1.75, 0, zc - 0.06), (0.32, 0.2, 0.17))
    part(coll, rig, "head", "head", hide_m, (2.12, 0, zc - 0.03), (0.24, 0.18, 0.16))
    part(coll, rig, "head", "beak", edge_m, (2.33, 0, zc - 0.07), (0.07, 0.1, 0.06))
    part(coll, rig, "head", "eye", eye_m, (2.2, -0.15, zc + 0.03), (0.035, 0.02, 0.035), segs=12)
    for b, x, y, ln in (("ff_L", 1.3, -0.88, 0.48), ("ff_R", 1.3, 0.88, 0.48), ("hf_L", -1.3, -0.8, 0.34), ("hf_R", -1.3, 0.8, 0.34)):
        part(coll, rig, b, f"{b}_m", hide_m, (x, y, zc - 0.36), (ln, 0.14, 0.06), rot=(0, 0.35 if x > 0 else -0.35, 0))
    bl = part(coll, rig, "bladder", "bladder", bl_m, (0, 0, zc - 0.72), (1.0, 0.75, 0.32), segs=32)
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        s2 = math.sin(2 * math.pi * t)
        pitch, z, neck, head, ff, hf, blad = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0
        if name == "idle":
            z, ff, hf, neck = 0.04 * s2, 12 * s2, -8 * s2, 3 * s2
        elif name == "walk":
            ff, hf, pitch, neck = 32 * s2, -24 * s2, -3.0, 5 * math.sin(4 * math.pi * t)
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            neck, head, pitch = -18 * k, 22 * k, -4 * k                    # head lunges forward-down, bites
        elif name == "hurt":
            k = [1.0, 0.5][i]
            neck, pitch, ff = 20 * k, 6 * k, -20 * k
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            neck, head, ff, hf, blad, z = 40 * k, 25 * k, 35 * k, -35 * k, 1.0 - 0.75 * k, -0.25 * k   # toward the husk pose
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        set_pose(rig, "neck", neck)
        set_pose(rig, "head", head)
        for b, a in (("ff_L", ff), ("ff_R", ff * 0.8), ("hf_L", hf), ("hf_R", hf * 0.8)):
            set_pose(rig, b, a)
        bl.scale = (1.0 * (0.6 + 0.4 * blad), 0.75 * (0.6 + 0.4 * blad), 0.32 * blad)
        key_all(rig, f, extra=[(bl, "scale")])
    finish([rig, bl])


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    build_stormglider(scene)
    build_lightning_eel(scene)
    build_belt_wasp(scene)
    build_ballast_tortoise(scene)
    scene.frame_start = 1
    scene.frame_end = max(CLIP_START[c] + CLIP_LEN[c] - 1 for c in CLIP_ORDER)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
