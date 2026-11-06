"""Earth flora rig set (contract v3.0 §11.3, Bible §9.3 flora; B-112): the "snoozle".

An original meadow flower with a face: a dandelion clock (a lumpy off-white seed puff, seed
ticks at the rim, green sepals) with the face set in the puff,
a dusty-green rubber-hose stem in two segments, two leaf hands with rounded mitten tips, pie-cut
eyes. Swaps: eyes open / blink, mouth smile / yawn / giggle. 5 bones.

Every part is drawn in its own local frame with the PIVOT AT THE ORIGIN (metres, x right,
z up), once as a rig part (build: one GP object `part_<name>` per part) and once posed by the
same bone chain for the preview loop (build_preview: 12 drawings), so the preview shows
exactly what Unity's bones will do with the parts.

Rig json extras beyond the §11.3 example (JsonUtility ignores unknown fields):
  bone.offset_m [x, z]   where the bone starts in its parent's frame (default: the parent's tip,
                         i.e. [0, parent.length]); the leaves hang off the lower stem.
  bone.order             draw order (low first).
  plant.slots            where each swap slot sits: [{"slot", "bone", "offset_m", "order"}].
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gp_draw as G  # noqa: E402

SRC = os.path.join(os.path.dirname(HERE), "sources", "flora")
P = G.PALETTES["earth"]
O, I = G.OUTER, G.INNER

L_STEM1, L_STEM2, L_HEAD = 0.42, 0.36, 0.30
FACE_C = 0.27                     # face centre above the head pivot (the neck)
BONES = [
    {"name": "root", "part": "stem_lower", "parent": None, "length": L_STEM1, "order": 0},
    {"name": "leaf_l", "part": "leaf_l", "parent": "root", "length": 0.30, "offset_m": [0.0, 0.20], "order": 1},
    {"name": "leaf_r", "part": "leaf_r", "parent": "root", "length": 0.30, "offset_m": [0.0, 0.28], "order": 2},
    {"name": "stem2", "part": "stem_upper", "parent": "root", "length": L_STEM2, "order": 3},
    {"name": "head", "part": "head", "parent": "stem2", "length": L_HEAD, "order": 4},
]
SLOTS = [{"slot": "eyes", "bone": "head", "offset_m": [0.0, FACE_C + 0.05], "order": 5},
         {"slot": "mouth", "bone": "head", "offset_m": [0.0, FACE_C - 0.08], "order": 6}]
PLANT = {
    "name": "snoozle",
    "bones": BONES,
    "swaps": {"eyes": ["eyes_open", "eyes_blink"], "mouth": ["mouth_smile", "mouth_yawn", "mouth_giggle"]},
    "slots": SLOTS,
    "idle": {"type": "sway", "amplitude_deg": 12, "beat_bpm": 110, "squash": 0.08},
    "react": {"radius_m": 3.0, "action": "turn_look", "swap": "mouth_giggle"},
}


# ---------------------------------------------------------------- parts (local frames, pivot at 0)

def mats(gp):
    return {
        "stem": G.mat(gp, "stem_green", fill=P["green"]),
        "stem_sh": G.mat(gp, "stem_green_shadow", fill=G.shadow_of(P["green"]), ink=False),
        "petal": G.mat(gp, "petal_mustard", fill=P["mustard"]),
        "petal_sh": G.mat(gp, "petal_mustard_shadow", fill=G.shadow_of(P["mustard"]), ink=False),
        "face": G.mat(gp, "face_offwhite", fill=P["offwhite"]),
        "cheek": G.mat(gp, "cheek", fill=G.shadow_of(P["offwhite"]), ink=False),
        "ink": G.mat(gp, "ink_line", fill=None, ink=True),
        "pupil": G.mat(gp, "pupil", fill=G.INK, ink=False),
        "eye": G.mat(gp, "eye_white", fill=P["offwhite"]),
        "red": G.mat(gp, "mouth_red", fill=P["red"]),
        "red_sh": G.mat(gp, "cheek_red", fill=G.shadow_of(P["red"]), ink=False),
        "leaf": G.mat(gp, "leaf_green", fill=P["green"]),
    }


def part_stem(L, bend):
    def fn(d, M, xf):
        c = G.bezier((0, 0), (bend, L * 0.5), (0, L), n=10)
        out = G.hose_outline(c, 0.15)
        G.stroke(d, xf(out), M["stem"], O, cyclic=True)
        sh = G.hose_outline([(x + 0.035, z) for x, z in c], 0.05)
        G.stroke(d, xf(sh), M["stem_sh"], 0.0, cyclic=True)
        G.stroke(d, xf(out), M["ink"], O, cyclic=True)
    return fn


def part_head(d, M, xf):
    """A dandelion clock: a lumpy off-white seed puff (scalloped rim, one shadow tone), seed
    ticks at the rim, two green sepals cupping the neck. The face swaps sit on the puff."""
    for k, s in enumerate((-1, 1)):            # sepals under the puff
        sep = G.bezier((0.0, 0.02), (0.10 * s, 0.02), (0.15 * s, 0.10), n=8) + \
            G.bezier((0.15 * s, 0.10), (0.06 * s, 0.10), (0.0, 0.08), n=8)[1:]
        G.stroke(d, xf(sep), M["leaf"], O, cyclic=True)
    R = 0.27
    rim = []
    for i in range(90):
        t = 2 * math.pi * i / 90
        r = R * (1 + 0.075 * abs(math.sin(7 * t + 0.4)) + 0.02 * math.sin(3 * t))
        rim.append((r * math.cos(t), FACE_C + r * math.sin(t)))
    G.stroke(d, xf(rim), M["face"], 0.0, cyclic=True)
    lo = [q for q in rim if (q[0] - 0.05) + (q[1] - FACE_C) * 1.4 < -0.10]
    if len(lo) > 3:
        inner = [(x * 0.80 - 0.02, FACE_C + (z - FACE_C) * 0.80 - 0.02) for x, z in lo][::-1]
        G.stroke(d, xf(lo + inner), M["cheek"], 0.0, cyclic=True)
    G.stroke(d, xf(rim), M["ink"], O, cyclic=True)
    for k in range(7):                         # seed ticks on the upper rim
        a = 0.45 + 2.25 * k / 6
        x0, z0 = 0.80 * R * math.cos(a), FACE_C + 0.80 * R * math.sin(a)
        G.stroke(d, xf([(x0, z0), (x0 + 0.05 * math.cos(a), z0 + 0.05 * math.sin(a))]), M["ink"], I)
    for k, cx in enumerate((-0.12, 0.12)):     # cheeks
        G.stroke(d, xf(G.lumpy_ellipse(cx, FACE_C - 0.07, 0.035, 0.025, n=14, seed=60 + k)), M["red_sh"], 0.0, cyclic=True)


def part_leaf(side):
    def fn(d, M, xf):
        s = side
        top = G.bezier((0, 0.03), (0.12 * s, 0.16), (0.27 * s, 0.10), n=10)
        mit = G.lumpy_ellipse(0.31 * s, 0.05, 0.085, 0.075, n=18, lump=0.05, seed=70 + (s > 0))
        mit = [q for q in mit if (q[0] - 0.31 * s) * s > -0.03]      # the mitten's round tip
        mit.sort(key=lambda q: -math.atan2(q[1] - 0.05, (q[0] - 0.31 * s) * s))
        bot = G.bezier((0.27 * s, -0.01), (0.12 * s, -0.08), (0.0, -0.04), n=10)
        pts = top + mit + bot
        G.stroke(d, xf(pts), M["leaf"], O, cyclic=True)
        G.stroke(d, xf(G.bezier((0.02 * s, -0.005), (0.13 * s, 0.05), (0.24 * s, 0.04), n=8)), M["ink"], I)
    return fn


def part_eyes(closed):
    def fn(d, M, xf):
        for k, ex in enumerate((-0.065, 0.065)):
            G.pie_eye(G.Xf(d, xf), ex, 0.0, 0.045, 0.06, M["pupil"], M["eye"], look=(0.0, -0.1),
                      seed=80 + k, closed=closed, m_lid=M["ink"])
    return fn


def part_mouth(kind):
    def fn(d, M, xf):
        if kind == "smile":
            G.stroke(d, xf(G.bezier((-0.06, 0.01), (0.0, -0.035), (0.06, 0.01), n=10)), M["ink"], I)
        elif kind == "yawn":
            G.stroke(d, xf(G.lumpy_ellipse(0, -0.01, 0.045, 0.065, n=20, seed=3)), M["red"], I, cyclic=True)
        else:                                    # giggle: a wide open grin
            pts = G.bezier((-0.07, 0.015), (0.0, -0.075), (0.07, 0.015), n=12) + \
                G.bezier((0.07, 0.015), (0.0, 0.0), (-0.07, 0.015), n=8)[1:-1]
            G.stroke(d, xf(pts), M["red"], I, cyclic=True)
    return fn


PARTS = {
    "stem_lower": part_stem(L_STEM1, 0.05),
    "stem_upper": part_stem(L_STEM2, -0.04),
    "head": part_head,
    "leaf_l": part_leaf(-1),
    "leaf_r": part_leaf(1),
    "eyes_open": part_eyes(0.0),
    "eyes_blink": part_eyes(1.0),
    "mouth_smile": part_mouth("smile"),
    "mouth_yawn": part_mouth("yawn"),
    "mouth_giggle": part_mouth("giggle"),
}


# ---------------------------------------------------------------- transforms

def ident(pts):
    return list(pts)


def affine(m):
    """m = (a, b, c, d, tx, tz): x' = a x + b z + tx, z' = c x + d z + tz."""
    a, b, c, dd, tx, tz = m
    return lambda pts: [(a * x + b * z + tx, c * x + dd * z + tz) for x, z in pts]


def compose(m1, m2):
    """m1 after m2."""
    a1, b1, c1, d1, x1, z1 = m1
    a2, b2, c2, d2, x2, z2 = m2
    return (a1 * a2 + b1 * c2, a1 * b2 + b1 * d2, c1 * a2 + d1 * c2, c1 * b2 + d1 * d2,
            a1 * x2 + b1 * z2 + x1, c1 * x2 + d1 * z2 + z1)


def rot_t(deg, tx=0.0, tz=0.0):
    r = math.radians(deg)                     # + = counter-clockwise (leans left), like Unity z
    return (math.cos(r), -math.sin(r), math.sin(r), math.cos(r), tx, tz)


def pose_mats(angles, squash):
    """World matrix per bone from local angles (deg) and the root squash (scale z, 1/sqrt x)."""
    sx = 1 / math.sqrt(squash)
    world = {}
    for b in BONES:
        local = rot_t(angles.get(b["name"], 0.0))
        if b["parent"] is None:
            world[b["name"]] = compose((sx, 0, 0, squash, 0, 0), local)
        else:
            pb = next(x for x in BONES if x["name"] == b["parent"])
            off = b.get("offset_m", [0.0, pb["length"]])
            world[b["name"]] = compose(world[b["parent"]], compose((1, 0, 0, 1, off[0], off[1]), local))
    return world


# ---------------------------------------------------------------- builds

def build(out=os.path.join(SRC, "earth_rigset.blend")):
    """One GP object per part, drawn around its pivot (the object origin). The plant (bones,
    swaps, slots, idle, react) is stored on the scene as json for render.py's rig json."""
    import json
    scene = G.new_scene()
    scene["rig_plants"] = json.dumps([PLANT])
    coll = G.collection("parts")
    for name, fn in PARTS.items():
        ob, gp = G.gp_object("part_" + name, coll)
        M = mats(gp)
        layer = gp.layers.new("art")
        fn(G.drawing(layer, 1), M, ident)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


def preview_pose(i, n=12):
    """The idle the rig plays: sway on the beat (12 deg), follow-through up the chain,
    8 % squash, leaves waving behind; a blink on 8-9 and a yawn on 3-5 for the review."""
    ph = 2 * math.pi * i / n
    ang = {"root": 6 * math.sin(ph), "stem2": 6 * math.sin(ph - 0.6), "head": 5 * math.sin(ph - 1.1),
           "leaf_l": -12 * math.sin(ph - 1.4) - 8, "leaf_r": 12 * math.sin(ph - 1.4) + 8}
    squash = 1 + 0.04 * math.cos(2 * ph)          # +-4 % = 8 % peak to peak (the rig's squash 0.08)
    eyes = "eyes_blink" if i in (8, 9) else "eyes_open"
    mouth = "mouth_yawn" if i in (3, 4, 5) else "mouth_smile"
    return ang, squash, eyes, mouth


def draw_posed(d, M, ang, squash, eyes, mouth):
    W = pose_mats(ang, squash)
    items = [(b["order"], b["part"], W[b["name"]], (0, 0)) for b in BONES]
    for s in SLOTS:
        part = eyes if s["slot"] == "eyes" else mouth
        items.append((s["order"], part, W[s["bone"]], s["offset_m"]))
    for _o, part, m, off in sorted(items, key=lambda t: t[0]):
        PARTS[part](d, M, affine(compose(m, (1, 0, 0, 1, off[0], off[1]))))


def build_preview(out=os.path.join(SRC, "earth_rigset_preview.blend")):
    scene = G.new_scene()
    coll = G.collection("plant")
    ob, gp = G.gp_object("snoozle", coll)
    M = mats(gp)
    layer = gp.layers.new("art")
    for i in range(12):
        draw_posed(G.drawing(layer, i + 1), M, *preview_pose(i))
    # three react drawings after the loop (turn to look, giggle)
    for k, (turn, mouth) in enumerate([(8, "mouth_smile"), (14, "mouth_giggle"), (10, "mouth_giggle")]):
        ang = {"root": 2.0, "stem2": 4.0, "head": turn, "leaf_l": -20, "leaf_r": 30}
        draw_posed(G.drawing(layer, 13 + k), M, ang, 1.03, "eyes_open", mouth)
    G.mark_clips(scene, [("idle", 12), ("react", 3)])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out
