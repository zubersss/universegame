"""Builds blender/sources/creatures/saturn.blend: Saturn cloud-column creatures (B-060, Bible §7.7).

Same conventions as build_creatures_jupiter.py (fliers centred on the origin, pivot = centre,
standard clip frames, rigid parts on bones). Saturn palette: pale gold, butter, cream.

  * helium_jelly (~1.6 m bell, 320 px): translucent pale-gold bell with a faint inner glow,
    frilled rim and trailing tentacles. Extra clip "rise" (frames 47-52): when hit it puffs up
    and floats upward (Bible: floats up when hit).
  * hex_drake (~2.6 m, 320 px): winged, rides the hexagon walls. Butter-gold scales, darker
    gold back ridge, cream membrane wings flapping about the body axis (never flat), long neck
    and tail, amber eyes.
  * floe_moth (~0.35 m, 128 px): cream moth with gold eyespots (faint glow), two wing pairs.

  blender --background --factory-startup --python blender/scripts/build_creatures_saturn.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_creatures_earth import CLIP_LEN, CLIP_ORDER, CLIP_START, set_pose  # noqa: E402
from build_creatures_jupiter import _frames, finish, key_all, make_rig, new_coll, part, set_pose_x  # noqa: E402
from build_pilgrim import flat_material, paint_material  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "creatures", "saturn.blend")
RISE_START, RISE_LEN = 47, 6          # extra clip after death (death ends at 44)


def _translucent(name, base, alpha, emit, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    pr = m.node_tree.nodes["Principled BSDF"]
    pr.inputs["Base Color"].default_value = tuple(c / 255 for c in base) + (1,)
    pr.inputs["Roughness"].default_value = 0.3
    pr.inputs["Alpha"].default_value = alpha
    pr.inputs["Emission Color"].default_value = tuple(c / 255 for c in emit) + (1,)
    pr.inputs["Emission Strength"].default_value = strength
    return m


# ---------------------------------------------------------------- helium jelly

def build_helium_jelly(scene):
    sp = "helium_jelly"
    coll = new_coll(scene, sp)
    n_t = 6
    bones = [("root", (0, 0, 0.2), (0, 0, 0.6), None)]
    for k in range(n_t):
        x = -0.5 + k * 0.2
        bones.append((f"tA{k}", (x, 0, -0.15), (x - 0.03, 0, -0.65), "root"))
        bones.append((f"tB{k}", (x - 0.03, 0, -0.65), (x - 0.08, 0, -1.15), f"tA{k}"))
    rig = make_rig(sp, coll, bones)
    bell_m = _translucent(f"{sp}_bell", (246, 228, 170), 0.62, (255, 230, 150), 0.6)
    core_m = _translucent(f"{sp}_core", (255, 214, 120), 0.85, (255, 214, 120), 1.6)
    frill_m = _translucent(f"{sp}_frill", (236, 206, 140), 0.7, (255, 220, 140), 0.3)
    tent_m = _translucent(f"{sp}_tent", (240, 220, 168), 0.65, (255, 226, 160), 0.4)
    bell = part(coll, rig, "root", "bell", bell_m, (0, 0, 0.2), (0.8, 0.7, 0.55), segs=40)
    for v in bell.data.vertices:                                   # open bell: flatten the underside
        if v.co.z < -0.1:
            v.co.z = -0.1 + (v.co.z + 0.1) * 0.25
    core = part(coll, rig, "root", "core", core_m, (0, 0, 0.18), (0.3, 0.26, 0.22))
    for k in range(12):                                            # frilled rim
        a = 2 * math.pi * k / 12
        part(coll, rig, "root", f"frill{k}", frill_m, (0.76 * math.cos(a), 0.64 * math.sin(a), -0.08),
             (0.12, 0.12, 0.06), segs=12)
    for k in range(n_t):
        x = -0.5 + k * 0.2
        part(coll, rig, f"tA{k}", f"ta{k}", tent_m, (x - 0.015, 0, -0.4), (0.025, 0.025, 0.26), segs=10)
        part(coll, rig, f"tB{k}", f"tb{k}", tent_m, (x - 0.055, 0, -0.9), (0.018, 0.018, 0.26), segs=10)
    frames = list(_frames()) + [("rise", i, RISE_START + i) for i in range(RISE_LEN)]
    for name, i, f in frames:
        ln = RISE_LEN if name == "rise" else CLIP_LEN[name]
        t = i / ln
        s2 = math.sin(2 * math.pi * t)
        z, puff, tsw, tlag, pitch = 0.0, 1.0, 6 * s2, 0.0, 0.0
        if name == "idle":
            z, puff = 0.04 * s2, 1.0 + 0.06 * s2                   # slow pulse
        elif name == "walk":
            puff, tlag, pitch = 1.0 + 0.12 * math.sin(2 * math.pi * t), -14.0, -6.0
        elif name == "attack":
            k = [0.0, 0.4, 1.0, 0.8, 0.4, 0.1][i]
            tlag, puff = 40 * k, 1.0 - 0.1 * k                     # tentacles whip forward
        elif name == "hurt":
            k = [1.0, 0.5][i]
            puff, tsw = 0.85 + 0.15 * (1 - k), -12 * k
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            puff, z, pitch, tlag = 1.0 - 0.5 * k, -0.3 * k, 30 * k, 25 * k
        elif name == "rise":
            k = (i + 1) / RISE_LEN
            puff, z, tlag = 1.0 + 0.3 * k, 0.5 * k, 30 * k          # puffs up and floats upward, tentacles trail
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        for k in range(n_t):
            ph = 0.7 * k
            set_pose(rig, f"tA{k}", tlag + tsw * math.cos(ph))
            set_pose(rig, f"tB{k}", 0.6 * tlag + 1.5 * tsw * math.cos(ph + 0.9))
        bell.scale = (0.8 * puff ** 0.5, 0.7 * puff ** 0.5, 0.55 * puff)
        core.scale = (0.3 * puff, 0.26 * puff, 0.22 * puff)
        key_all(rig, f, extra=[(bell, "scale"), (core, "scale")])
    finish([rig, bell, core])


# ---------------------------------------------------------------- hex drake

def build_hex_drake(scene):
    sp = "hex_drake"
    coll = new_coll(scene, sp)
    rig = make_rig(sp, coll, [
        ("root", (-0.3, 0, 0), (0.3, 0, 0), None),
        ("neck", (0.4, 0, 0.05), (0.85, 0, 0.2), "root"),
        ("head", (0.85, 0, 0.2), (1.15, 0, 0.18), "neck"),
        ("tail1", (-0.45, 0, 0), (-0.95, 0, -0.05), "root"),
        ("tail2", (-0.95, 0, -0.05), (-1.45, 0, -0.08), "tail1"),
        ("wing_L", (0.0, -0.15, 0.08), (0.0, -1.3, 0.08), "root"),
        ("wing_R", (0.0, 0.15, 0.08), (0.0, 1.3, 0.08), "root"),
    ])
    scale_m = paint_material(f"{sp}_scale", (232, 204, 130), (196, 160, 92), seams=False, scratches=False)
    ridge_m = flat_material(f"{sp}_ridge", (176, 132, 64), rough=0.5)
    belly_m = flat_material(f"{sp}_belly", (244, 230, 190), rough=0.6)
    wing_m = flat_material(f"{sp}_wing", (238, 222, 180), rough=0.5)
    bone_m = flat_material(f"{sp}_bone", (186, 146, 80), rough=0.5)
    eye_m = flat_material(f"{sp}_eye", (150, 90, 20), emit=(255, 176, 60), strength=1.6)
    part(coll, rig, "root", "body", scale_m, (0.0, 0, 0.02), (0.5, 0.2, 0.18))
    part(coll, rig, "root", "belly", belly_m, (0.0, 0, -0.06), (0.45, 0.17, 0.11))
    for k in range(5):
        part(coll, rig, "root", f"ridge{k}", ridge_m, (0.3 - 0.15 * k, 0, 0.2), (0.04, 0.02, 0.05), kind="cone", segs=6)
    part(coll, rig, "neck", "neck", scale_m, (0.62, 0, 0.12), (0.26, 0.1, 0.09), rot=(0, -0.3, 0))
    part(coll, rig, "head", "head", scale_m, (0.98, 0, 0.2), (0.17, 0.09, 0.08))
    part(coll, rig, "head", "snout", ridge_m, (1.14, 0, 0.18), (0.08, 0.06, 0.05))
    part(coll, rig, "head", "horn", ridge_m, (0.92, 0, 0.29), (0.04, 0.02, 0.07), kind="cone", segs=6, rot=(0, -0.6, 0))
    part(coll, rig, "head", "eye", eye_m, (1.03, -0.08, 0.23), (0.025, 0.015, 0.02), segs=10)
    part(coll, rig, "tail1", "tail1", scale_m, (-0.7, 0, -0.02), (0.27, 0.08, 0.07))
    part(coll, rig, "tail2", "tail2", scale_m, (-1.2, 0, -0.065), (0.27, 0.05, 0.045))
    part(coll, rig, "tail2", "fin", ridge_m, (-1.47, 0, -0.08), (0.08, 0.015, 0.07))
    for b, s in (("wing_L", -1), ("wing_R", 1)):
        part(coll, rig, b, f"arm{s}", bone_m, (0.05, 0.65 * s, 0.08), (0.04, 0.6, 0.03))
        part(coll, rig, b, f"mem{s}", wing_m, (-0.12, 0.7 * s, 0.08), (0.32, 0.6, 0.02), rot=(0, 0, 0.2 * s))
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        s2 = math.sin(2 * math.pi * t)
        pitch, z, base, amp, neck, tail = 0.0, 0.0, 40.0, 14.0, 0.0, 0.0
        if name == "idle":
            z, tail, neck = 0.05 * s2, 8 * s2, 3 * s2
        elif name == "walk":
            amp, pitch, tail = 28.0, -6.0, 12 * math.sin(4 * math.pi * t)
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            pitch, neck, amp, base = -12 * k, -30 * k, 8.0, 40 + 15 * k     # head strikes, wings flare
        elif name == "hurt":
            k = [1.0, 0.5][i]
            pitch, neck, amp = 14 * k, 20 * k, 4.0
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            pitch, z, base, amp, neck, tail = 60 * k, -0.35 * k, 40 - 12 * k, 0.0, 35 * k, -25 * k
        a = base + amp * s2
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        set_pose_x(rig, "wing_L", a)
        set_pose_x(rig, "wing_R", -a)
        set_pose(rig, "neck", neck)
        set_pose(rig, "tail1", tail)
        set_pose(rig, "tail2", tail * 1.3)
        key_all(rig, f)
    finish([rig])


# ---------------------------------------------------------------- floe moth

def build_floe_moth(scene):
    sp = "floe_moth"
    coll = new_coll(scene, sp)
    rig = make_rig(sp, coll, [
        ("root", (-0.04, 0, 0), (0.04, 0, 0), None),
        ("wf_L", (0.02, -0.02, 0.02), (0.02, -0.18, 0.02), "root"),
        ("wf_R", (0.02, 0.02, 0.02), (0.02, 0.18, 0.02), "root"),
        ("wh_L", (-0.03, -0.02, 0.02), (-0.03, -0.14, 0.02), "root"),
        ("wh_R", (-0.03, 0.02, 0.02), (-0.03, 0.14, 0.02), "root"),
    ])
    body_m = flat_material(f"{sp}_body", (176, 150, 104), rough=0.6)
    wing_m = paint_material(f"{sp}_wing", (244, 232, 200), (214, 196, 150), seams=False, scratches=False)
    spot_m = flat_material(f"{sp}_spot", (196, 150, 60), emit=(255, 214, 120), strength=1.0)
    eye_m = flat_material(f"{sp}_eye", (30, 24, 20), rough=0.3)
    part(coll, rig, "root", "body", body_m, (0, 0, 0), (0.07, 0.025, 0.025))
    part(coll, rig, "root", "head", body_m, (0.075, 0, 0.005), (0.022, 0.02, 0.02), segs=12)
    part(coll, rig, "root", "eye", eye_m, (0.085, -0.016, 0.01), (0.008, 0.005, 0.008), segs=8)
    for k, s in enumerate((-1, 1)):
        part(coll, rig, "root", f"ant{k}", body_m, (0.1, 0.008 * s, 0.03), (0.003, 0.003, 0.03), rot=(0, -0.7, 0))
    for b, s, ln, hx in (("wf_L", -1, 0.1, 0.02), ("wf_R", 1, 0.1, 0.02), ("wh_L", -1, 0.075, -0.03), ("wh_R", 1, 0.075, -0.03)):
        part(coll, rig, b, f"{b}_m", wing_m, (hx - 0.01, s * (0.02 + ln), 0.02), (0.045, ln, 0.003))
        part(coll, rig, b, f"{b}_s", spot_m, (hx - 0.01, s * (0.02 + ln * 1.2), 0.024), (0.015, 0.015, 0.002), segs=10)
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        s2 = math.sin(2 * math.pi * t * 2)
        pitch, z, base, amp = 0.0, 0.0, 45.0, 22.0
        if name == "idle":
            z = 0.008 * math.sin(2 * math.pi * t)
        elif name == "walk":
            pitch, amp = -8.0, 28.0
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            pitch, amp = -20 * k, 30.0                                  # darts forward
        elif name == "hurt":
            pitch, amp = 25.0 * [1.0, 0.5][i], 6.0
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            pitch, z, base, amp = 120 * k, -0.06 * k, 45 - 15 * k, 0.0
        a = base + amp * s2
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        set_pose_x(rig, "wf_L", a)
        set_pose_x(rig, "wf_R", -a)
        set_pose_x(rig, "wh_L", a * 0.85)
        set_pose_x(rig, "wh_R", -a * 0.85)
        key_all(rig, f)
    finish([rig])


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    build_helium_jelly(scene)
    build_hex_drake(scene)
    build_floe_moth(scene)
    scene.frame_start = 1
    scene.frame_end = RISE_START + RISE_LEN - 1
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
