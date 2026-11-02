"""Builds blender/sources/creatures/uranus.blend: Uranus creatures (B-064, Bible §7.8).

Same conventions as build_creatures_jupiter.py (rigid parts on bones, standard clip frames).
Uranus light is dim (sunlight 0.25), so albedos are kept light (pale cyan, cream, slate) and
the key features glow: they must read on the contact sheet relit at 0.25.

  * frostwisp (~0.5 m, 128 px): luminous cyan-white floater, a glowing core in a translucent
    shell with three trailing wisp ribbons. Leads you to warmth or danger.
  * methane_ray (~2.4 m span, 320 px): pale cyan glider, teal back, glowing edge dots; wings
    flap about the body axis and never go flat.
  * hailcrab (~1.4 m walker, 320 px, pivot on the ground): slate-blue legs, a domed pale shell
    studded with caught diamonds (bright, faintly emissive). Extra clip "defend" (frames 47-52):
    legs tuck and the shell tilts up over the body.
  * tiltbird (~0.5 m flock unit, 128 px): cream-and-teal migrating bird, long wings that flap
    in the side plane (always visible), forked tail.

  blender --background --factory-startup --python blender/scripts/build_creatures_uranus.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_creatures_earth import CLIP_LEN, CLIP_ORDER, CLIP_START, ground_exactly, set_pose  # noqa: E402
from build_creatures_jupiter import _frames, finish, key_all, make_rig, new_coll, part, set_pose_x  # noqa: E402
from build_creatures_saturn import _translucent  # noqa: E402
from build_pilgrim import flat_material, paint_material  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "creatures", "uranus.blend")
DEFEND_START, DEFEND_LEN = 47, 6


# ---------------------------------------------------------------- frostwisp

def build_frostwisp(scene):
    sp = "frostwisp"
    coll = new_coll(scene, sp)
    bones = [("root", (0, 0, 0), (0.1, 0, 0), None)]
    for k in range(3):
        y = (k - 1) * 0.04
        bones.append((f"rA{k}", (-0.08, y, 0), (-0.25, y, 0.02), "root"))
        bones.append((f"rB{k}", (-0.25, y, 0.02), (-0.45, y, 0.0), f"rA{k}"))
    rig = make_rig(sp, coll, bones)
    core = part(coll, rig, "root", "core", flat_material(f"{sp}_core", (160, 230, 240), emit=(200, 250, 255), strength=3.0),
                (0, 0, 0), (0.07, 0.07, 0.07), segs=16)
    shell = part(coll, rig, "root", "shell", _translucent(f"{sp}_shell", (190, 236, 244), 0.45, (150, 230, 250), 0.8),
                 (0, 0, 0), (0.14, 0.12, 0.12), segs=20)
    rib = _translucent(f"{sp}_rib", (200, 240, 248), 0.6, (170, 240, 255), 1.4)
    for k in range(3):
        y, zz = (k - 1) * 0.04, (k - 1) * 0.02
        part(coll, rig, f"rA{k}", f"ra{k}", rib, (-0.17, y, 0.01 + zz), (0.09, 0.012, 0.018), segs=10)
        part(coll, rig, f"rB{k}", f"rb{k}", rib, (-0.35, y, 0.01 + zz), (0.1, 0.008, 0.012), segs=10)
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        s2 = math.sin(2 * math.pi * t)
        z, glow, sw, lag, pitch = 0.0, 1.0, 10 * s2, 0.0, 0.0
        if name == "idle":
            z, glow = 0.02 * s2, 1.0 + 0.1 * s2
        elif name == "walk":
            lag, pitch = 12.0, -8.0
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            glow, lag = 1.0 + 0.4 * k, -10 * k                         # flares bright
        elif name == "hurt":
            glow, sw = 0.8, 25 * [1.0, 0.5][i]
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            glow, z, lag = 1.0 - 0.8 * k, -0.08 * k, 30 * k             # fades and drops
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        for k in range(3):
            set_pose(rig, f"rA{k}", lag + sw * math.cos(0.8 * k))
            set_pose(rig, f"rB{k}", lag * 0.6 + 1.5 * sw * math.cos(0.8 * k + 1.0))
        core.scale = (0.07 * glow, 0.07 * glow, 0.07 * glow)
        shell.scale = (0.14 * glow ** 0.5, 0.12 * glow ** 0.5, 0.12 * glow ** 0.5)
        key_all(rig, f, extra=[(core, "scale"), (shell, "scale")])
    finish([rig, core, shell])


# ---------------------------------------------------------------- methane ray

def build_methane_ray(scene):
    sp = "methane_ray"
    coll = new_coll(scene, sp)
    rig = make_rig(sp, coll, [
        ("root", (-0.2, 0, 0), (0.3, 0, 0), None),
        ("wing_L", (0.0, -0.15, 0), (0.0, -1.2, 0), "root"),
        ("wing_R", (0.0, 0.15, 0), (0.0, 1.2, 0), "root"),
        ("tail", (-0.6, 0, 0), (-1.3, 0, 0), "root"),
    ])
    back = paint_material(f"{sp}_back", (120, 186, 196), (90, 150, 164), seams=False, scratches=False)
    belly = flat_material(f"{sp}_belly", (214, 236, 236), rough=0.6)
    dots = flat_material(f"{sp}_dots", (90, 170, 190), emit=(160, 240, 255), strength=2.0)
    eye = flat_material(f"{sp}_eye", (20, 30, 34), rough=0.3)
    part(coll, rig, "root", "body", back, (0.05, 0, 0.02), (0.6, 0.36, 0.13))
    part(coll, rig, "root", "belly", belly, (0.05, 0, -0.03), (0.56, 0.33, 0.1))
    part(coll, rig, "root", "eye", eye, (0.55, -0.24, 0.04), (0.035, 0.025, 0.035), segs=12)
    for b, s in (("wing_L", -1), ("wing_R", 1)):
        part(coll, rig, b, f"wing{s}", back, (-0.08, 0.72 * s, 0), (0.45, 0.62, 0.03), rot=(0, 0, -0.3 * s))
        for k in range(4):
            part(coll, rig, b, f"dot{s}{k}", dots, (0.12 - 0.15 * k, (0.95 + 0.1 * k) * s, 0.02), (0.035, 0.035, 0.012), segs=10)
    part(coll, rig, "tail", "tail", belly, (-0.95, 0, 0), (0.38, 0.02, 0.02), kind="cone", segs=8, rot=(0, math.pi / 2, 0))
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        s2 = math.sin(2 * math.pi * t)
        pitch, z, base, amp, tail = 0.0, 0.0, 30.0, 8.0, 0.0
        if name == "idle":
            z, tail = 0.04 * s2, 5 * s2
        elif name == "walk":
            amp, pitch, tail = 20.0, -4.0, 8 * math.sin(4 * math.pi * t)
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            pitch, base, amp = -24 * k, 30 - 8 * k, 4.0
        elif name == "hurt":
            k = [1.0, 0.5][i]
            pitch, z, amp = 12 * k, 0.05 * k, 3.0
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            pitch, z, base, amp, tail = 45 * k, -0.3 * k, 30 - 8 * k, 0.0, -18 * k
        a = base + amp * s2
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        set_pose_x(rig, "wing_L", a)
        set_pose_x(rig, "wing_R", -a)
        set_pose(rig, "tail", tail)
        key_all(rig, f)
    finish([rig])


# ---------------------------------------------------------------- hailcrab

def build_hailcrab(scene):
    """Walker: built standing on z = 0; ground_exactly keys the rig so the lowest vertex sits on
    the ground every frame (pivot at the feet, as the Venus pressure crab)."""
    sp = "hailcrab"
    coll = new_coll(scene, sp)
    legs = [(0.35, -1), (0.0, -1), (-0.35, -1), (0.35, 1), (0.0, 1), (-0.35, 1)]
    bones = [("root", (0, 0, 0.45), (0.3, 0, 0.45), None), ("shell", (-0.1, 0, 0.6), (0.3, 0, 0.6), "root"),
             ("claw", (0.45, -0.3, 0.4), (0.8, -0.35, 0.35), "root")]
    for k, (x, s) in enumerate(legs):
        bones.append((f"lu{k}", (x, 0.25 * s, 0.4), (x + 0.12, 0.45 * s, 0.25), "root"))
        bones.append((f"ll{k}", (x + 0.12, 0.45 * s, 0.25), (x + 0.2, 0.5 * s, 0.0), f"lu{k}"))
    rig = make_rig(sp, coll, bones)
    leg_m = flat_material(f"{sp}_leg", (96, 120, 140), rough=0.5)
    body_m = flat_material(f"{sp}_body", (130, 156, 172), rough=0.5)
    shell_m = paint_material(f"{sp}_shell", (206, 222, 228), (150, 172, 184), seams=False)
    dia_m = flat_material(f"{sp}_diamond", (230, 248, 255), emit=(200, 240, 255), strength=1.4, rough=0.05)
    eye_m = flat_material(f"{sp}_eye", (60, 140, 160), emit=(150, 230, 255), strength=1.6)
    part(coll, rig, "root", "body", body_m, (0.05, 0, 0.45), (0.48, 0.34, 0.16))
    shell = part(coll, rig, "shell", "shell", shell_m, (0.0, 0, 0.6), (0.62, 0.48, 0.28), segs=32)
    for k in range(9):                                               # caught diamonds on the shell
        a, rr = 2.4 * k, 0.25 + 0.03 * (k % 3)
        x, y = rr * math.cos(a) * 1.6, rr * math.sin(a) * 1.4
        part(coll, rig, "shell", f"dia{k}", dia_m, (x, y - 0.05, 0.6 + 0.24 - 0.12 * (rr / 0.31) ** 2 + 0.03),
             (0.04, 0.04, 0.05), kind="cone", segs=4, rot=(0.3 * k, 0.2, 0))
    part(coll, rig, "root", "eye", eye_m, (0.5, -0.12, 0.55), (0.03, 0.02, 0.03), segs=10)
    part(coll, rig, "claw", "claw", leg_m, (0.62, -0.32, 0.38), (0.2, 0.08, 0.07))
    part(coll, rig, "claw", "pincer", body_m, (0.82, -0.34, 0.36), (0.09, 0.06, 0.05))
    for k, (x, s) in enumerate(legs):
        part(coll, rig, f"lu{k}", f"lu{k}", leg_m, (x + 0.06, 0.35 * s, 0.33), (0.04, 0.12, 0.04), rot=(0.9 * s, 0, 0))
        part(coll, rig, f"ll{k}", f"ll{k}", leg_m, (x + 0.16, 0.48 * s, 0.13), (0.03, 0.03, 0.14), rot=(0, -0.35, 0))
    frames = list(_frames()) + [("defend", i, DEFEND_START + i) for i in range(DEFEND_LEN)]
    for name, i, f in frames:
        ln = DEFEND_LEN if name == "defend" else CLIP_LEN[name]
        t = i / ln
        ph = 2 * math.pi * t
        swing, lift, sh, claw, pitch = 0.0, 0.0, 0.0, 0.0, 0.0
        if name == "idle":
            claw = 6 * math.sin(ph)
        elif name == "walk":
            swing, lift = 18.0, 14.0
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            claw, pitch = -45 * k, -5 * k                               # claw snaps forward
        elif name == "hurt":
            pitch, sh = 8 * [1.0, 0.5][i], 10 * [1.0, 0.5][i]
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            lift, sh, pitch = 40 * k, 15 * k, 10 * k                    # legs fold, shell slumps
        elif name == "defend":
            k = min(1.0, (i + 1) / 3)
            lift, sh = 50 * k, -35 * k                                  # legs tuck, shell tilts up over the body
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, 0.0)
        set_pose(rig, "shell", sh)
        set_pose(rig, "claw", claw)
        for k, (x, s) in enumerate(legs):
            p = ph + (math.pi if k % 2 else 0.0)
            set_pose(rig, f"lu{k}", swing * math.sin(p) - lift)
            set_pose(rig, f"ll{k}", max(0.0, lift * 0.8 + 10 * math.cos(p) * (swing > 0)))
        key_all(rig, f)
    finish([rig])
    # Plant the feet: ground_exactly walks the standard clips; key the defend frames the same way.
    ground_exactly(rig)
    scene_ = bpy.context.scene
    meshes = [o for o in rig.children_recursive if o.type == "MESH"]
    dg = bpy.context.evaluated_depsgraph_get()
    for i in range(DEFEND_LEN):
        f = DEFEND_START + i
        scene_.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        low = min((o.evaluated_get(dg).matrix_world @ v.co).z for o in meshes for v in o.evaluated_get(dg).data.vertices)
        rig.location.z -= low
        rig.keyframe_insert("location", frame=f)
    finish([rig])


# ---------------------------------------------------------------- tiltbird

def build_tiltbird(scene):
    sp = "tiltbird"
    coll = new_coll(scene, sp)
    rig = make_rig(sp, coll, [
        ("root", (-0.05, 0, 0), (0.05, 0, 0), None),
        ("wing", (0.0, -0.02, 0.03), (-0.05, -0.02, 0.33), "root"),      # near wing, in the side plane
        ("wing2", (0.0, 0.02, 0.03), (-0.05, 0.02, 0.33), "root"),
        ("tail", (-0.1, 0, 0), (-0.22, 0, -0.01), "root"),
    ])
    cream = flat_material(f"{sp}_cream", (236, 232, 214), rough=0.6)
    teal = flat_material(f"{sp}_teal", (70, 140, 150), rough=0.5)
    beak = flat_material(f"{sp}_beak", (210, 170, 90), rough=0.4)
    eye = flat_material(f"{sp}_eye", (30, 60, 70), emit=(140, 220, 240), strength=1.0)
    part(coll, rig, "root", "body", cream, (0, 0, 0), (0.1, 0.035, 0.035))
    part(coll, rig, "root", "back", teal, (-0.01, 0, 0.018), (0.085, 0.03, 0.02))
    part(coll, rig, "root", "head", cream, (0.1, 0, 0.012), (0.03, 0.026, 0.026), segs=12)
    part(coll, rig, "root", "beak", beak, (0.14, 0, 0.008), (0.022, 0.006, 0.006), kind="cone", segs=6, rot=(0, math.pi / 2, 0))
    part(coll, rig, "root", "eye", eye, (0.112, -0.02, 0.02), (0.006, 0.004, 0.006), segs=8)
    for b, y, m in (("wing", -0.04, teal), ("wing2", 0.04, cream)):
        part(coll, rig, b, f"{b}_m", m, (-0.03, y, 0.17), (0.05, 0.005, 0.15), rot=(0, -0.2, 0))
    for k, s in enumerate((-1, 1)):
        part(coll, rig, "tail", f"tail{k}", teal, (-0.17, 0.006 * s, -0.005), (0.06, 0.004, 0.012), rot=(0, 0, 0.25 * s))
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        s2 = math.sin(2 * math.pi * t * 2)
        pitch, z, base, amp = 0.0, 0.0, -30.0, 70.0
        if name == "idle":
            z, amp = 0.01 * math.sin(2 * math.pi * t), 55.0
        elif name == "walk":
            pitch = -6.0
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            pitch, amp = -30 * k, 40.0                                  # dives
        elif name == "hurt":
            pitch, amp = 25.0 * [1.0, 0.5][i], 20.0
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            pitch, z, base, amp = 130 * k, -0.1 * k, -30 - 40 * k, 0.0
        a = base + amp * s2                                             # side-plane flap: sweeps up and down
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        set_pose(rig, "wing", a)
        set_pose(rig, "wing2", a - 8)
        set_pose(rig, "tail", 6 * math.sin(2 * math.pi * t))
        key_all(rig, f)
    finish([rig])


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    build_frostwisp(scene)
    build_methane_ray(scene)
    build_hailcrab(scene)
    build_tiltbird(scene)
    scene.frame_start = 1
    scene.frame_end = DEFEND_START + DEFEND_LEN - 1
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
