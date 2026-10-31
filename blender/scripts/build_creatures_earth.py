"""Builds blender/sources/creatures/earth.blend: Earth creatures (B-015), stag and grey wolf.

Same approach as the surveyor (build_surveyor.py): a hierarchy of empties as the rig, soft
Skin-modifier body parts parented to it, poses keyed per frame, and a 2D forward-kinematics
pass that puts the lowest hoof/paw on z = 0. Faces +X (right); near side -Y; far-side legs
15% darker so they read behind the body in 2D. Collections `stag` and `wolf`.

Standard creature set (contract §5): idle 6, walk 8 (four-beat gait), attack 6, hurt 2,
death 6 = 28 frames. Bible §9: grounded anatomy with one alien exaggeration per species.
Earth is home, so these stay naturalistic: the stag's exaggeration is oversized antlers, the
wolf's a heavy ruff. Deterministic:

  blender --background --factory-startup --python blender/scripts/build_creatures_earth.py
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_icons import mat  # noqa: E402
from build_surveyor import _constant, attach, empty, soft_limb  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "creatures", "earth.blend")

CLIP_ORDER = ["idle", "walk", "attack", "hurt", "death"]
CLIP_LEN = {"idle": 6, "walk": 8, "attack": 6, "hurt": 2, "death": 6}
CLIP_START = {}
_f = 1
for _c in CLIP_ORDER:
    CLIP_START[_c] = _f
    _f += CLIP_LEN[_c] + 4

# Proportions (m). half = half the hip-to-shoulder distance; legs: upper, lower, foot height.
SPECIES = {
    "stag": dict(half=0.55, upper=0.46, lower=0.56, foot=0.05, body_r=(0.26, 0.3, 0.32), neck=0.55,
                 neck_angle=55, head=0.42, tail=0.14, ears=0.14, antler=0.62,
                 coat=((142, 100, 64), (112, 78, 50)), belly=(196, 168, 128), dark=(58, 44, 34)),
    "wolf": dict(half=0.38, upper=0.31, lower=0.33, foot=0.04, body_r=(0.17, 0.2, 0.22), neck=0.3,
                 neck_angle=30, head=0.34, tail=0.48, ears=0.1, antler=0.0, ruff=True,
                 coat=((128, 124, 118), (92, 88, 84)), belly=(196, 190, 180), dark=(46, 44, 44)),
}


# ---------------------------------------------------------------- poses
# Angles in degrees. leg swing a_<leg> (+ forward), knee flex k_<leg>; legs: fn fr hn hr
# (front/hind, near/far). pitch (+ nose down), neck (+ head up), head (+ nose down), tail
# (+ up), lift (m).

LEGS = ("fn", "ff", "hn", "hf")


def pose(name, i, sp):
    n = CLIP_LEN[name]
    t = i / n
    p = {f"a_{l}": 0.0 for l in LEGS}
    p.update({f"k_{l}": 4.0 for l in LEGS})
    p.update(pitch=0.0, neck=0.0, head=0.0, tail=0.0)
    if name == "idle":
        s = math.sin(2 * math.pi * t)
        p.update(neck=3 * s, head=-2 * s, tail=6 * s)
    elif name == "walk":
        phase = {"hn": 0.0, "fn": 0.25, "hf": 0.5, "ff": 0.75}           # four-beat walk
        for l, ph in phase.items():
            u = 2 * math.pi * (t + ph)
            p[f"a_{l}"] = 22 * math.sin(u)
            p[f"k_{l}"] = 6 + 46 * max(0.0, math.cos(u))                 # flex while swinging forward
        p.update(neck=-4 + 3 * math.sin(4 * math.pi * t), tail=8 * math.sin(2 * math.pi * t))
    elif name == "attack":
        k = [0.0, 0.35, 0.8, 1.0, 0.6, 0.15][i]                          # wind-up, strike, recover
        if sp == "stag":                                                 # head-down antler charge
            p.update(pitch=8 * k, neck=-38 * k, head=30 * k, a_fn=-14 * k, a_ff=-10 * k, a_hn=18 * k, a_hf=14 * k)
        else:                                                            # lunge and bite
            p.update(pitch=-6 * k, neck=10 * k, head=-12 * k, a_fn=26 * k, a_ff=20 * k, a_hn=-22 * k, a_hf=-18 * k,
                     k_fn=4 + 30 * k, tail=20 * k)
    elif name == "hurt":
        k = [1.0, 0.5][i]
        p.update(pitch=-8 * k, neck=16 * k, head=-10 * k, a_fn=12 * k, a_ff=8 * k, a_hn=-10 * k, a_hf=-6 * k, tail=-15 * k)
    elif name == "death":
        k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]                       # legs buckle, body sinks
        for l in LEGS:                                                   # legs tuck under the body
            p[f"k_{l}"] = 4 + 110 * k
            p[f"a_{l}"] = (-30 if l.startswith("f") else 25) * k
        p.update(neck=-50 * k, head=25 * k, tail=-20 * k, pitch=6 * k)
    return p


def lowest(p, sp):
    """Lowest z relative to the root (body centre) over feet, body and head samples (2D FK)."""
    S = SPECIES[sp]
    r = math.radians(p["pitch"])

    def rot(x, z, a):
        return (x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a))
    pts = []
    for l in LEGS:
        x0 = S["half"] if l.startswith("f") else -S["half"]
        sx, sz = rot(x0, -S["body_r"][1] * 0.5, r)
        a1 = math.radians(p[f"a_{l}"]) - r
        kx, kz = sx + S["upper"] * math.sin(a1), sz - S["upper"] * math.cos(a1)
        a2 = a1 - math.radians(p[f"k_{l}"])
        fx, fz = kx + S["lower"] * math.sin(a2), kz - S["lower"] * math.cos(a2)
        pts += [fz - S["foot"], kz - 0.05]
    for x in (-S["half"], 0.0, S["half"]):                              # belly
        pts.append(rot(x, 0.0, r)[1] - S["body_r"][1])
    hx, hz = rot(S["half"] + 0.1, 0.1, r)
    na = math.radians(S["neck_angle"] + p["neck"]) - r
    pts.append(hz + S["neck"] * math.sin(na) - 0.12)                      # head underside
    return min(pts)


# ---------------------------------------------------------------- build

def build_species(sp, scene):
    S = SPECIES[sp]
    coll = bpy.data.collections.new(sp)
    scene.collection.children.link(coll)
    coat = {"n": mat(f"{sp}_coat_n", S["coat"][0], S["coat"][1], 0, 0.9, 40, 0.5),
            "f": mat(f"{sp}_coat_f", tuple(int(c * 0.85) for c in S["coat"][0]), tuple(int(c * 0.85) for c in S["coat"][1]), 0, 0.9, 40, 0.5)}
    belly = mat(f"{sp}_belly", S["belly"], tuple(int(c * 0.9) for c in S["belly"]), 0, 0.9, 40, 0.4)
    dark = mat(f"{sp}_dark", S["dark"], tuple(int(c * 0.8) for c in S["dark"]), 0, 0.6, 20, 0.2)
    hip_z = S["upper"] + S["lower"] + S["foot"] + S["body_r"][1] * 0.5
    root = empty("root", (0, 0, hip_z), None, coll)
    body = empty("body", (0, 0, hip_z), root, coll)
    h, (r0, r1, r2) = S["half"], S["body_r"]
    attach(soft_limb(f"{sp}_torso", (-h - 0.1, 0, hip_z + 0.02), (h + 0.12, 0, hip_z + 0.06), (r0, r1, r2), coat["n"]), body, coll)
    attach(soft_limb(f"{sp}_belly", (-h * 0.6, 0, hip_z - r1 * 0.55), (h * 0.7, 0, hip_z - r1 * 0.5), (r1 * 0.5, r1 * 0.55, r1 * 0.5), belly), body, coll)
    # Neck and head.
    na = math.radians(S["neck_angle"])
    nb = Vector((h + 0.08, 0, hip_z + r2 * 0.5))
    neck = empty("neck", tuple(nb), body, coll)
    nt = nb + Vector((math.cos(na), 0, math.sin(na))) * S["neck"]
    attach(soft_limb(f"{sp}_neck", tuple(nb), tuple(nt), (r2 * 0.7, r2 * 0.5, r2 * 0.4), coat["n"]), neck, coll)
    if S.get("ruff"):
        attach(soft_limb(f"{sp}_ruff", tuple(nb + Vector((-0.04, 0, 0.02))), tuple(nb.lerp(nt, 0.7)), (r2 * 0.95, r2 * 0.85, r2 * 0.55), coat["n"]), neck, coll)
    head = empty("head", tuple(nt), neck, coll)
    hd = Vector((math.cos(math.radians(-35)), 0, math.sin(math.radians(-35))))
    tip = nt + hd * S["head"]
    attach(soft_limb(f"{sp}_head", tuple(nt + Vector((-0.04, 0, 0.02))), tuple(tip), (r2 * 0.5, r2 * 0.38, r2 * 0.18), coat["n"]), head, coll)
    attach(soft_limb(f"{sp}_nose", tuple(tip - hd * 0.04), tuple(tip + hd * 0.02), (0.03, 0.03, 0.025), dark), head, coll)
    for sy in (-1, 1):
        e0 = nt + Vector((-0.03, sy * r2 * 0.25, r2 * 0.3))
        attach(soft_limb(f"{sp}_ear_{sy}", tuple(e0), tuple(e0 + Vector((-0.05, sy * 0.03, S["ears"]))), (0.035, 0.03, 0.008), coat["n"]), head, coll)
        eye = nt + hd * (S["head"] * 0.35) + Vector((0, sy * r2 * 0.3, 0.03))
        attach(soft_limb(f"{sp}_eye_{sy}", tuple(eye), tuple(eye + Vector((0.005, 0, 0))), (0.016, 0.016, 0.016), dark), head, coll)
    if S["antler"]:                                                     # main beam + tines, both sides
        bone = mat(f"{sp}_antler", (206, 188, 156), (170, 150, 120), 0, 0.6, 30, 0.3)
        for sy in (-1, 1):
            b0 = nt + Vector((0.0, sy * r2 * 0.2, r2 * 0.35))
            beam = [b0, b0 + Vector((-0.12, sy * 0.06, S["antler"] * 0.45)), b0 + Vector((0.02, sy * 0.1, S["antler"] * 0.85)),
                    b0 + Vector((0.14, sy * 0.08, S["antler"]))]
            for k in range(3):
                attach(soft_limb(f"{sp}_beam_{sy}_{k}", tuple(beam[k]), tuple(beam[k + 1]), (0.03, 0.026, 0.022), bone), head, coll)
            for k, (base, d) in enumerate(((1, (0.16, 0, 0.12)), (2, (0.14, 0, 0.16)), (2, (-0.12, 0, 0.14)))):
                attach(soft_limb(f"{sp}_tine_{sy}_{k}", tuple(beam[base]), tuple(beam[base] + Vector(d)), (0.022, 0.016, 0.008), bone), head, coll)
    # Tail.
    tb = Vector((-h - 0.12, 0, hip_z + r0 * 0.4))
    tail = empty("tail", tuple(tb), body, coll)
    tdir = Vector((-0.75, 0, -0.66 if sp == "wolf" else 0.3)).normalized()
    attach(soft_limb(f"{sp}_tail", tuple(tb), tuple(tb + tdir * S["tail"]),
                     (0.06, 0.07, 0.03) if sp == "wolf" else (0.05, 0.05, 0.02), coat["n"]), tail, coll)
    # Legs.
    J = {}
    for l in LEGS:
        x0 = h if l.startswith("f") else -h
        sy = -1 if l.endswith("n") else 1
        side = "n" if l.endswith("n") else "f"
        top = Vector((x0, sy * r1 * 0.55, hip_z - r1 * 0.5))
        hip = empty(f"hip_{l}", tuple(top), body, coll)
        knee_p = top - Vector((0, 0, S["upper"]))
        thick = r1 * (0.5 if l.startswith("h") else 0.42)
        attach(soft_limb(f"{sp}_upper_{l}", tuple(top + Vector((0, 0, 0.1))), tuple(knee_p), (thick, thick * 0.7, thick * 0.4), coat[side]), hip, coll)
        knee = empty(f"knee_{l}", tuple(knee_p), hip, coll)
        foot_p = knee_p - Vector((0, 0, S["lower"]))
        attach(soft_limb(f"{sp}_lower_{l}", tuple(knee_p), tuple(foot_p), (thick * 0.4, thick * 0.3, thick * 0.28), coat[side]), knee, coll)
        attach(soft_limb(f"{sp}_foot_{l}", tuple(foot_p + Vector((0, 0, 0.01))), tuple(foot_p + Vector((0.04, 0, -S["foot"]))),
                         (thick * 0.3, thick * 0.32, thick * 0.3), dark), knee, coll)
        J[l] = (hip, knee)
    animate(sp, root, body, neck, head, tail, J, hip_z)


def key(ob, frame, rot_y=None, loc=None):
    if rot_y is not None:
        ob.rotation_euler = (0.0, math.radians(rot_y), 0.0)
        ob.keyframe_insert("rotation_euler", frame=frame)
    if loc is not None:
        ob.location = loc
        ob.keyframe_insert("location", frame=frame)


def animate(sp, root, body, neck, head, tail, J, hip_z):
    for name in CLIP_ORDER:
        for i in range(CLIP_LEN[name]):
            p = pose(name, i, sp)
            f = CLIP_START[name] + i
            key(root, f, rot_y=p["pitch"], loc=(0.0, 0.0, -lowest(p, sp)))
            key(body, f, rot_y=0.0)
            key(neck, f, rot_y=-p["neck"])
            key(head, f, rot_y=p["head"])
            key(tail, f, rot_y=p["tail"])        # tail points -x: + rotation raises it
            for l in LEGS:
                key(J[l][0], f, rot_y=-p[f"a_{l}"])
                key(J[l][1], f, rot_y=p[f"k_{l}"])
    for ob in bpy.data.objects:
        if ob.animation_data and ob.animation_data.action:
            _constant(ob.animation_data.action)


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for sp in SPECIES:
        build_species(sp, scene)
    scene.frame_start = 1
    scene.frame_end = max(CLIP_START[c] + CLIP_LEN[c] - 1 for c in CLIP_ORDER)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
