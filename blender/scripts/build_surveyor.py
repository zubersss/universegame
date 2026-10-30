"""Builds blender/sources/characters/surveyor.blend: the player character (B-009).

A 1.82 m surveyor in a worn EVA suit: helmet with a faintly glowing visor, chest lamp,
life-support pack, and the Beam tool in the near hand. Rig = a hierarchy of empties (one per
joint); each suit part is a rigid mesh parented to its joint, so there is no skinning to go
wrong. Faces +X (right). The near side (toward the side camera) is -Y; far-side limbs use
15% darker materials so they read behind the body in 2D.

Animation clips are keyed one pose per frame from the tables in CLIPS. A 2D forward-kinematics
pass puts the lowest point of the body on z = 0 (plus any `lift`), so feet stay on the ground
line that the sprite pivot marks. Blender frame ranges per clip are in CLIP_START (also used
by the manifest). Deterministic; re-run any time:

  blender --background --factory-startup --python blender/scripts/build_surveyor.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import flat_material, lin, paint_material  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "characters", "surveyor.blend")

# Skeleton (metres). Hip joint is the root; z up, x forward.
HIP_Z = 1.0
THIGH, SHIN, ANKLE_H = 0.45, 0.45, 0.10
UPPER, FORE = 0.30, 0.28
SHOULDER_Z = 0.44          # above the hip
NECK_Z = 0.53              # head joint above the hip
HIP_Y, SHOULDER_Y = 0.10, 0.22

# ---------------------------------------------------------------- clips
# Angles in degrees. hip/sh: swing forward (+). kn: knee bend (+). el: elbow bend (+).
# torso/head/rot: lean forward (+). an: extra toe-up on top of "foot flat". lift: m above ground.
# _n = near side (toward camera), _f = far side.

CLIP_ORDER = ["idle", "walk", "run", "jump", "fall", "land", "dig", "aim", "hurt", "death"]
CLIP_LEN = {"idle": 6, "walk": 8, "run": 8, "jump": 3, "fall": 2, "land": 3, "dig": 6, "aim": 2, "hurt": 2, "death": 6}
CLIP_LOOP = {"idle": True, "walk": True, "run": True, "fall": True, "dig": True, "aim": True}
CLIP_START = {}
_f = 1
for _c in CLIP_ORDER:
    CLIP_START[_c] = _f
    _f += CLIP_LEN[_c] + 4      # gaps keep clips apart on the timeline


def pose_idle(i, n):
    t = 2 * math.pi * i / n
    s = math.sin(t)
    return dict(torso=2 + 1.2 * s, head=-2 + 1.0 * s, sh_n=4 + 1.5 * s, el_n=12, sh_f=6 - 1.5 * s, el_f=14,
                hip_n=2, kn_n=4, hip_f=-2, kn_f=4)


def pose_walk(i, n):
    t = 2 * math.pi * i / n
    s, c = math.sin(t), math.cos(t)
    return dict(torso=5, head=-3, hip_n=26 * s, hip_f=-26 * s,
                kn_n=6 + 48 * max(0.0, c), kn_f=6 + 48 * max(0.0, -c),
                sh_n=-22 * s, sh_f=22 * s, el_n=18 + 8 * max(0.0, -s), el_f=18 + 8 * max(0.0, s))


def pose_run(i, n):
    t = 2 * math.pi * i / n
    s, c = math.sin(t), math.cos(t)
    return dict(torso=14, head=-10, hip_n=42 * s + 6, hip_f=-42 * s + 6,
                kn_n=12 + 80 * max(0.0, c), kn_f=12 + 80 * max(0.0, -c),
                sh_n=-38 * s, sh_f=38 * s, el_n=85, el_f=85, lift=0.05 * max(0.0, math.sin(2 * t)))


JUMP = [dict(torso=24, head=-14, hip_n=48, kn_n=88, hip_f=44, kn_f=84, sh_n=-30, el_n=30, sh_f=-24, el_f=30),
        dict(torso=6, head=-4, hip_n=-6, kn_n=6, hip_f=-12, kn_f=10, sh_n=78, el_n=34, sh_f=66, el_f=36),
        dict(torso=10, head=-6, hip_n=46, kn_n=72, hip_f=34, kn_f=78, sh_n=60, el_n=40, sh_f=48, el_f=45)]
# Airborne clips stay planted on the pivot line: the game moves the body, the sprite poses it.
FALL = [dict(torso=-4, head=4, hip_n=22, kn_n=26, hip_f=-8, kn_f=36, sh_n=76, el_n=34, sh_f=62, el_f=35),
        dict(torso=-6, head=6, hip_n=16, kn_n=32, hip_f=-12, kn_f=30, sh_n=70, el_n=38, sh_f=66, el_f=30)]
LAND = [dict(torso=30, head=-18, hip_n=62, kn_n=104, hip_f=58, kn_f=100, sh_n=40, el_n=40, sh_f=30, el_f=45),
        dict(torso=16, head=-10, hip_n=36, kn_n=62, hip_f=34, kn_f=60, sh_n=16, el_n=25, sh_f=12, el_f=30),
        dict(torso=5, head=-3, hip_n=10, kn_n=16, hip_f=8, kn_f=14, sh_n=6, el_n=14, sh_f=6, el_f=16)]


def pose_dig(i, n):
    t = 2 * math.pi * i / n
    s = math.sin(t)
    return dict(torso=18 + 1.5 * s, head=-6, hip_n=22, kn_n=28, hip_f=-14, kn_f=10,
                sh_n=56 + 4 * s, el_n=14 - 3 * s, sh_f=42, el_f=55)


AIM = [dict(torso=3, head=0, hip_n=12, kn_n=8, hip_f=-8, kn_f=6, sh_n=80, el_n=3, sh_f=66, el_f=40, x=-0.03),
       dict(torso=4, head=1, hip_n=12, kn_n=9, hip_f=-8, kn_f=7, sh_n=81.5, el_n=3, sh_f=67, el_f=40, x=-0.03)]
HURT = [dict(torso=-18, head=-16, hip_n=6, kn_n=16, hip_f=-6, kn_f=14, sh_n=-30, el_n=40, sh_f=50, el_f=30, x=-0.04),
        dict(torso=-9, head=-8, hip_n=4, kn_n=10, hip_f=-4, kn_f=10, sh_n=-12, el_n=30, sh_f=30, el_f=25, x=-0.02)]
DEATH = [dict(torso=-10, head=-10, hip_n=10, kn_n=26, hip_f=6, kn_f=24, sh_n=-20, el_n=30, sh_f=20, el_f=30),
         dict(rot=-6, torso=-14, head=-12, hip_n=30, kn_n=52, hip_f=26, kn_f=50, sh_n=-10, el_n=40, sh_f=30, el_f=30, x=0.02),
         dict(rot=-32, torso=-8, head=-10, hip_n=40, kn_n=60, hip_f=36, kn_f=58, sh_n=20, el_n=40, sh_f=40, el_f=30, x=0.02),
         dict(rot=-60, torso=-4, head=-6, hip_n=55, kn_n=70, hip_f=50, kn_f=66, sh_n=40, el_n=40, sh_f=50, el_f=30, x=-0.03),
         dict(rot=-84, torso=0, head=-4, hip_n=66, kn_n=82, hip_f=60, kn_f=80, sh_n=30, el_n=30, sh_f=40, el_f=30, x=0.04),
         dict(rot=-88, torso=0, head=-10, hip_n=64, kn_n=84, hip_f=58, kn_f=82, sh_n=24, el_n=24, sh_f=36, el_f=26, x=0.04)]


def clip_pose(name, i):
    n = CLIP_LEN[name]
    if name == "idle":
        return pose_idle(i, n)
    if name == "walk":
        return pose_walk(i, n)
    if name == "run":
        return pose_run(i, n)
    if name == "dig":
        return pose_dig(i, n)
    return {"jump": JUMP, "fall": FALL, "land": LAND, "aim": AIM, "hurt": HURT, "death": DEATH}[name][i]


# ---------------------------------------------------------------- 2D forward kinematics

def _rot(v, a):
    """Rotate (x, z) by lean angle a (rad, + = top toward +x)."""
    x, z = v
    return (x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a))


def lowest_point(p):
    """Lowest z (relative to the hip) of the body's hull samples for pose p."""
    r = math.radians(p.get("rot", 0))
    pts = []
    # Downward limbs measure "forward" from straight down; a body lean (top toward +x) swings
    # them backward, so a limb's world angle is its joint angle minus the lean above it.
    for side in ("n", "f"):
        h = math.radians(p.get(f"hip_{side}", 0))
        k = math.radians(p.get(f"kn_{side}", 0))
        a1 = h - r
        knee = (THIGH * math.sin(a1), -THIGH * math.cos(a1))
        a2 = a1 - k
        ankle = (knee[0] + SHIN * math.sin(a2), knee[1] - SHIN * math.cos(a2))
        # Foot is held flat relative to the body roll plus any extra toe-up.
        fa = r - math.radians(p.get(f"an_{side}", 0))
        for dx in (-0.09, 0.21):
            fx, fz = _rot((dx, -ANKLE_H), fa)
            pts.append((ankle[0] + fx, ankle[1] + fz))
        pts.append((knee[0], knee[1] - 0.09))
    # Torso, head and pack, rotated with the body and the torso lean.
    t = r + math.radians(p.get("torso", 0))
    for v, rad in (((0.0, 0.0), 0.15), ((0.0, 0.5), 0.16), ((-0.24, 0.12), 0.08), ((-0.24, 0.48), 0.08),
                   ((-0.36, 0.12), 0.06), ((-0.36, 0.48), 0.06), ((0.02, NECK_Z + 0.13), 0.16)):
        x, z = _rot(v, t)
        pts.append((x, z - rad))
    for side in ("n", "f"):
        sx, sz = _rot((0.0, SHOULDER_Z), t)
        a1 = math.radians(p.get(f"sh_{side}", 0)) - t
        el = (sx + UPPER * math.sin(a1), sz - UPPER * math.cos(a1))
        a2 = a1 + math.radians(p.get(f"el_{side}", 0))
        wr = (el[0] + FORE * math.sin(a2), el[1] - FORE * math.cos(a2))
        pts += [(el[0], el[1] - 0.07), (wr[0], wr[1] - 0.12)]
    return min(z for _, z in pts)


# ---------------------------------------------------------------- build

def rbox(name, size, center, mat, bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=center)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    mod = ob.modifiers.new("bevel", "BEVEL")
    mod.width = min(bevel, min(size) * 0.45)
    mod.segments = 3
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob


def ball(name, radius, center, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=radius, location=center)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob


def tube(name, radius, depth, center, mat, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=center, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    return ob


def empty(name, loc, parent, coll):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    coll.objects.link(e)
    e.location = loc
    bpy.context.view_layer.update()
    if parent is not None:
        set_parent(e, parent)
    return e


def set_parent(ob, parent):
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = parent
    ob.matrix_parent_inverse = parent.matrix_world.inverted()
    ob.matrix_world = mw


def attach(ob, parent, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    set_parent(ob, parent)


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    coll = bpy.data.collections.new("surveyor")
    scene.collection.children.link(coll)

    def suit(name, a, b, dark=1.0):
        return paint_material(name, tuple(int(c * dark) for c in a), tuple(int(c * dark) for c in b),
                              seams=False, grime=False, scratches=False)

    M = {}
    for side, k in (("n", 1.0), ("f", 0.85)):
        M["suit_" + side] = suit("suit_" + side, (206, 201, 188), (168, 160, 146), k)
        M["orange_" + side] = suit("orange_" + side, (206, 104, 38), (160, 78, 32), k)
        M["joint_" + side] = flat_material("joint_" + side, tuple(int(c * k) for c in (64, 66, 70)), metallic=0.3, rough=0.6)
        M["boot_" + side] = suit("boot_" + side, (74, 70, 64), (54, 50, 46), k)
        M["glove_" + side] = flat_material("glove_" + side, tuple(int(c * k) for c in (70, 72, 76)), rough=0.7)
    pack = suit("pack", (118, 124, 112), (92, 96, 86))
    visor = flat_material("visor", (34, 28, 18), metallic=0.8, emit=(90, 200, 255), strength=0.22, rough=0.15)
    lamp = flat_material("chest_lamp", (220, 220, 210), emit=(255, 232, 186), strength=1.0)
    tool_m = flat_material("beam_tool", (62, 64, 70), metallic=1.0, rough=0.35)
    tip = flat_material("beam_tip", (40, 70, 80), emit=(110, 230, 255), strength=1.0)

    root = empty("root", (0, 0, HIP_Z), None, coll)
    attach(rbox("pelvis", (0.28, 0.36, 0.2), (0, 0, HIP_Z + 0.02), M["suit_n"]), root, coll)
    torso = empty("torso", (0, 0, HIP_Z), root, coll)
    attach(rbox("chest", (0.30, 0.40, 0.46), (0, 0, HIP_Z + 0.27), M["suit_n"], 0.08), torso, coll)
    attach(rbox("chest_plate", (0.05, 0.30, 0.18), (0.14, 0, HIP_Z + 0.33), M["orange_n"], 0.02), torso, coll)
    attach(tube("lamp", 0.045, 0.04, (0.17, -0.08, HIP_Z + 0.38), lamp, rot=(0, math.pi / 2, 0)), torso, coll)
    attach(rbox("pack", (0.20, 0.34, 0.44), (-0.25, 0, HIP_Z + 0.30), pack, 0.05), torso, coll)
    attach(tube("pack_tank", 0.05, 0.40, (-0.36, 0.1, HIP_Z + 0.30), M["joint_n"]), torso, coll)
    attach(tube("collar", 0.13, 0.06, (0, 0, HIP_Z + NECK_Z - 0.01), M["joint_n"]), torso, coll)

    head = empty("head", (0, 0, HIP_Z + NECK_Z), torso, coll)
    hz = HIP_Z + NECK_Z + 0.13
    attach(ball("helmet", 0.15, (0, 0, hz), M["suit_n"]), head, coll)
    attach(ball("visor", 0.142, (0.035, 0, hz - 0.005), visor, scale=(1.0, 0.86, 0.72)), head, coll)
    attach(tube("helmet_light", 0.02, 0.06, (0.02, -0.15, hz + 0.08), M["joint_n"], rot=(math.pi / 2, 0, 0)), head, coll)

    joints = {}
    for side, sy in (("n", -1), ("f", 1)):
        sh = empty(f"sh_{side}", (0, sy * SHOULDER_Y, HIP_Z + SHOULDER_Z), torso, coll)
        attach(ball(f"shoulder_pad_{side}", 0.1, (0, sy * SHOULDER_Y, HIP_Z + SHOULDER_Z), M["orange_" + side], (1, 0.9, 0.85)), sh, coll)
        attach(rbox(f"upper_arm_{side}", (0.12, 0.12, UPPER), (0, sy * SHOULDER_Y, HIP_Z + SHOULDER_Z - UPPER / 2 + 0.01), M["suit_" + side], 0.05), sh, coll)
        el = empty(f"el_{side}", (0, sy * SHOULDER_Y, HIP_Z + SHOULDER_Z - UPPER), sh, coll)
        attach(ball(f"elbow_{side}", 0.065, (0, sy * SHOULDER_Y, HIP_Z + SHOULDER_Z - UPPER), M["joint_" + side]), el, coll)
        attach(rbox(f"forearm_{side}", (0.11, 0.11, FORE), (0, sy * SHOULDER_Y, HIP_Z + SHOULDER_Z - UPPER - FORE / 2), M["suit_" + side], 0.045), el, coll)
        wz = HIP_Z + SHOULDER_Z - UPPER - FORE
        attach(rbox(f"glove_{side}", (0.10, 0.09, 0.11), (0.01, sy * SHOULDER_Y, wz - 0.05), M["glove_" + side], 0.03), el, coll)
        if side == "n":
            attach(tube("beam_tool", 0.035, 0.30, (0.02, sy * (SHOULDER_Y + 0.02), wz - 0.14), tool_m), el, coll)
            attach(ball("beam_tip", 0.032, (0.02, sy * (SHOULDER_Y + 0.02), wz - 0.29), tip), el, coll)

        hp = empty(f"hip_{side}", (0, sy * HIP_Y, HIP_Z), root, coll)
        attach(rbox(f"thigh_{side}", (0.17, 0.17, THIGH + 0.02), (0, sy * HIP_Y, HIP_Z - THIGH / 2), M["suit_" + side], 0.06), hp, coll)
        attach(rbox(f"thigh_band_{side}", (0.18, 0.18, 0.06), (0, sy * HIP_Y, HIP_Z - 0.16), M["orange_" + side], 0.02), hp, coll)
        kn = empty(f"kn_{side}", (0, sy * HIP_Y, HIP_Z - THIGH), hp, coll)
        attach(ball(f"knee_{side}", 0.085, (0.02, sy * HIP_Y, HIP_Z - THIGH), M["joint_" + side]), kn, coll)
        attach(rbox(f"shin_{side}", (0.14, 0.14, SHIN), (0, sy * HIP_Y, HIP_Z - THIGH - SHIN / 2 + 0.02), M["suit_" + side], 0.05), kn, coll)
        az = HIP_Z - THIGH - SHIN
        an = empty(f"an_{side}", (0, sy * HIP_Y, az), kn, coll)
        attach(rbox(f"boot_{side}", (0.29, 0.14, ANKLE_H + 0.04), (0.06, sy * HIP_Y, az - ANKLE_H / 2 + 0.02), M["boot_" + side], 0.035), an, coll)
        joints[side] = dict(sh=sh, el=el, hip=hp, kn=kn, an=an)

    animate(root, torso, head, joints)
    scene.frame_start = 1
    scene.frame_end = max(CLIP_START[c] + CLIP_LEN[c] - 1 for c in CLIP_ORDER)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


def key(ob, frame, rot_y=None, loc=None):
    if rot_y is not None:
        ob.rotation_euler = (0.0, math.radians(rot_y), 0.0)
        ob.keyframe_insert("rotation_euler", frame=frame)
    if loc is not None:
        ob.location = loc
        ob.keyframe_insert("location", frame=frame)


def animate(root, torso, head, J):
    for name in CLIP_ORDER:
        for i in range(CLIP_LEN[name]):
            p = clip_pose(name, i)
            f = CLIP_START[name] + i
            ground = -lowest_point(p)                       # hip height that puts the body on z = 0
            key(root, f, rot_y=p.get("rot", 0), loc=(p.get("x", 0.0), 0.0, ground + p.get("lift", 0.0)))
            key(torso, f, rot_y=p.get("torso", 0))
            key(head, f, rot_y=p.get("head", 0))
            for s in ("n", "f"):
                hip, kn = p.get(f"hip_{s}", 0), p.get(f"kn_{s}", 0)
                key(J[s]["hip"], f, rot_y=-hip)
                key(J[s]["kn"], f, rot_y=kn)
                # Foot flat in the body frame: undo hip and knee, then any toe-up.
                key(J[s]["an"], f, rot_y=hip - kn - p.get(f"an_{s}", 0))
                key(J[s]["sh"], f, rot_y=-p.get(f"sh_{s}", 0))
                key(J[s]["el"], f, rot_y=-p.get(f"el_{s}", 0))
    for ob in bpy.data.objects:
        if ob.animation_data and ob.animation_data.action:
            _constant(ob.animation_data.action)


def _constant(action):
    """Constant interpolation: each frame is exactly its pose (no in-betweens needed)."""
    fcurves = getattr(action, "fcurves", None)
    if fcurves is None:          # Blender 5 layered actions
        fcurves = [fc for layer in action.layers for strip in layer.strips
                   for bag in strip.channelbags for fc in bag.fcurves]
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
