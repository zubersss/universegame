"""Earth flora rig set v2 (contract v3.1 §11.3, Bible 4.1 §9.3; B-126): the "snoozle", no face.

A dandelion clock with personality through motion only (D-101: no eyes or mouths on plants):
a two-segment dusty-green rubber-hose stem with ribs, a pair of leaves that lift like arms,
and a seed-puff head that opens, half-shuts and shuts into a green bud (a slow yawn) and pops
open when the player comes near. v3.1 ink (D-100): 2-3 px outer / 1-1.5 px detail, seed-head
rays and specks, stem ribs, leaf veins, mid + deep shadow tones.

Every part is drawn in its own local frame with the PIVOT AT THE ORIGIN (metres, x right, z up),
once as a rig part (build: one GP object `part_<name>`) and once posed by the same bone chain for
the 12-frame preview loop (build_preview), so the review shows what Unity's bones will do.

Rig json (beyond the §11.3 example; JsonUtility ignores unknown fields):
  bone.offset_m [x, z]  where the bone starts in its parent's frame (default: the parent's tip)
  bone.order            draw order (low first)
  plant.slots           [{"slot", "bone", "offset_m", "order", "replaces_part"}]: a swap slot that
                        replaces_part swaps the bone's own sprite (head, leaves) instead of adding one
The bones carry the resting parts (head_open, leaves_rest), so a runtime that only knows the
v1 eyes/mouth slots still draws a correct, swaying plant.
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
PUFF_C, PUFF_R = 0.27, 0.26        # puff centre above the head pivot (the neck) and its radius
BONES = [
    {"name": "root", "part": "stem_lower", "parent": None, "length": L_STEM1, "order": 0},
    {"name": "leaves", "part": "leaves_rest", "parent": "root", "length": 0.25, "offset_m": [0.0, 0.24], "order": 1},
    {"name": "stem2", "part": "stem_upper", "parent": "root", "length": L_STEM2, "order": 2},
    {"name": "head", "part": "head_open", "parent": "stem2", "length": L_HEAD, "order": 3},
]
SLOTS = [{"slot": "head", "bone": "head", "offset_m": [0.0, 0.0], "order": 3, "replaces_part": True},
         {"slot": "leaves", "bone": "leaves", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True}]
PLANT = {
    "name": "snoozle",
    "bones": BONES,
    "swaps": {"head": ["head_open", "head_half", "head_closed"], "leaves": ["leaves_rest", "leaves_up"]},
    "slots": SLOTS,
    "idle": {"type": "sway", "amplitude_deg": 12, "beat_bpm": 110, "squash": 0.08,
             "swap_cycle": {"slot": "head", "sequence": ["head_open", "head_half", "head_closed", "head_half"],
                            "beats": [8, 1, 3, 1]}},
    "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "head_open", "also": {"leaves": "leaves_up"}},
}


def mats(gp):
    return {
        "stem": G.mat(gp, "stem_green", fill=P["green"]),
        "stem_sh": G.mat(gp, "stem_green_mid", fill=G.shadow_of(P["green"]), ink=False),
        "stem_dp": G.mat(gp, "stem_green_deep", fill=G.deep_of(P["green"]), ink=False),
        "puff": G.mat(gp, "puff_offwhite", fill=P["offwhite"]),
        "puff_fill": G.mat(gp, "puff_offwhite_fill", fill=P["offwhite"], ink=False),
        "puff_sh": G.mat(gp, "puff_mid", fill=G.shadow_of(P["offwhite"]), ink=False),
        "puff_dp": G.mat(gp, "puff_deep", fill=G.deep_of(P["offwhite"]), ink=False),
        "core": G.mat(gp, "puff_core", fill=P["mustard"], ink=False),
        "leaf": G.mat(gp, "leaf_green", fill=P["green"]),
        "leaf_fill": G.mat(gp, "leaf_green_fill", fill=P["green"], ink=False),
        "leaf_sh": G.mat(gp, "leaf_green_mid", fill=G.shadow_of(P["green"]), ink=False),
        "ink": G.mat(gp, "ink_line", fill=None, ink=True),
    }


def crescent(pts, cx, cz, k=0.78, dx=0.02, dz=0.02):
    return pts + [(cx + (x - cx) * k + dx, cz + (z - cz) * k + dz) for x, z in pts][::-1]


# ---------------------------------------------------------------- parts (local frames, pivot at 0)

def part_stem(L, bend):
    def fn(d, M):
        c = G.bezier((0, 0), (bend, L * 0.5), (0, L), n=10)
        out = G.hose_outline(c, 0.15)
        G.stroke(d, out, M["stem"], 0.0, cyclic=True)
        G.stroke(d, G.hose_outline([(x + 0.035, z) for x, z in c], 0.05), M["stem_sh"], 0.0, cyclic=True)
        G.stroke(d, G.hose_outline([(x + 0.05, z) for x, z in c[2:-2]], 0.018), M["stem_dp"], 0.0, cyclic=True)
        G.ribs(d, c[1:-1], 0.15, M["ink"], every=0.09, frac=0.55)
        G.stroke(d, out, M["ink"], O, cyclic=True)
    return fn


def sepals(d, M, spread, height):
    """Green sepals cupping the base of the head (spread 0 = wrapped bud, 1 = flared)."""
    for s in (-1, 1):
        tip = (s * (0.06 + 0.10 * spread), height)
        pts = G.bezier((0.0, 0.02), (s * (0.05 + 0.10 * spread), 0.04), tip, n=8) + \
            G.bezier(tip, (s * (0.02 + 0.05 * spread), height * 0.75), (0.0, 0.06), n=8)[1:]
        G.stroke(d, pts, M["leaf_fill"], 0.0, cyclic=True)
        G.seam(d, G.bezier((0.0, 0.04), (s * 0.04, height * 0.5), (tip[0] * 0.8, tip[1] * 0.85), n=6), M["ink"])
        G.stroke(d, pts, M["ink"], O, cyclic=True)


def puff_head(squeeze):
    """The seed puff, squeeze 1 = round open clock, ~0.55 = half shut (tall and narrow)."""
    def fn(d, M):
        rx, rz = PUFF_R * squeeze, PUFF_R * (1.0 + 0.25 * (1 - squeeze))
        cz = PUFF_C + 0.04 * (1 - squeeze)
        rim = []
        for i in range(90):
            t = 2 * math.pi * i / 90
            r = 1 + 0.075 * abs(math.sin(7 * t + 0.4)) + 0.02 * math.sin(3 * t)
            rim.append((rx * r * math.cos(t), cz + rz * r * math.sin(t)))
        sepals(d, M, spread=squeeze, height=0.10 + 0.06 * (1 - squeeze))
        G.stroke(d, rim, M["puff_fill"], 0.0, cyclic=True)
        lo = [q for q in rim if q[0] * 0.6 + (q[1] - cz) < -0.10 * squeeze]
        if len(lo) > 3:
            G.stroke(d, crescent(lo, 0.0, cz, 0.80, -0.01, 0.02), M["puff_sh"], 0.0, cyclic=True)
        dp = [q for q in rim if q[0] * 0.6 + (q[1] - cz) < -0.20 * squeeze]
        if len(dp) > 3:
            G.stroke(d, crescent(dp, 0.0, cz, 0.90, -0.005, 0.01), M["puff_dp"], 0.0, cyclic=True)
        # seed-head detail: pappus rays from the core, each ending in a tiny fork, core specks
        for k in range(13):
            a = 2 * math.pi * k / 13 + 0.2
            x0, z0 = 0.05 * squeeze * math.cos(a), cz + 0.05 * math.sin(a)
            x1, z1 = 0.78 * rx * math.cos(a), cz + 0.78 * rz * math.sin(a)
            G.seam(d, G.bowed_line((x0, z0), (x1, z1), bow=0.05, n=5), M["ink"])
            fx, fz = -math.sin(a) * 0.02, math.cos(a) * 0.02
            G.seam(d, [(x1 + fx * 0.8 + 0.006 * math.cos(a), z1 + fz * 0.8 + 0.006 * math.sin(a)), (x1 + 0.012 * math.cos(a), z1 + 0.012 * math.sin(a)),
                       (x1 - fx * 0.8 + 0.006 * math.cos(a), z1 - fz * 0.8 + 0.006 * math.sin(a))], M["ink"])   # a flat pappus tuft, not an arrowhead
        G.stroke(d, G.lumpy_ellipse(0.0, cz, 0.05 * squeeze + 0.01, 0.05, n=16, seed=7), M["core"], 0.0, cyclic=True)
        G.specks(d, [(0.012, cz + 0.01), (-0.015, cz - 0.008), (0.002, cz - 0.02)], M["ink"])
        G.hatch(d, -0.55 * rx, cz - 0.45 * rz, M["ink"], n=2, length=0.05, spacing=0.025, angle_deg=40, seed=3)
        G.stroke(d, rim, M["ink"], O, cyclic=True)
    return fn


def head_closed(d, M):
    """Shut: the sepals wrapped into a green bud with a white tuft peeking at the top."""
    tuft = G.lumpy_ellipse(0.0, 0.25, 0.05, 0.05, n=18, lump=0.08, seed=5)
    G.stroke(d, tuft, M["puff"], O, cyclic=True)
    bud = G.bezier((0.0, 0.02), (0.13, 0.06), (0.03, 0.26), n=10) + G.bezier((0.03, 0.26), (0.0, 0.24), (-0.03, 0.26), n=4)[1:] + \
        G.bezier((-0.03, 0.26), (-0.13, 0.06), (0.0, 0.02), n=10)[1:-1]
    G.stroke(d, bud, M["leaf_fill"], 0.0, cyclic=True)
    G.stroke(d, [q for q in bud if q[0] > 0.04] + [(0.03, 0.1)], M["leaf_sh"], 0.0, cyclic=True)
    for s in (-1, 1):                                   # the wrapped sepal edges and their veins
        G.seam(d, G.bezier((s * 0.01, 0.04), (s * 0.07, 0.10), (s * 0.015, 0.24), n=7), M["ink"])
    G.stitches(d, G.bezier((0.0, 0.05), (0.0, 0.14), (0.0, 0.22), n=6), M["ink"], every=0.05, length=0.02)
    G.stroke(d, bud, M["ink"], O, cyclic=True)


def leaf_pair(lift):
    """Both leaves on one part; lift 0 = resting (out and down), 1 = raised like arms."""
    def fn(d, M):
        for s in (-1, 1):
            a = math.radians(-12 + 62 * lift)
            ca, sa = math.cos(a), math.sin(a)

            def R(p):
                return (s * (p[0] * ca - p[1] * sa), p[0] * sa + p[1] * ca)
            top = G.bezier((0, 0.03), (0.12, 0.22), (0.28, 0.13), n=10)
            mit = G.lumpy_ellipse(0.31, 0.06, 0.085, 0.075, n=18, lump=0.05, seed=70 + (s > 0))
            mit = [q for q in mit if (q[0] - 0.31) > -0.03]
            mit.sort(key=lambda q: -math.atan2(q[1] - 0.06, q[0] - 0.31))
            bot = G.bezier((0.28, -0.02), (0.12, -0.13), (0.0, -0.05), n=10)
            pts = [R(p) for p in top + mit + bot]
            G.stroke(d, pts, M["leaf_fill"], 0.0, cyclic=True)
            G.stroke(d, [R(p) for p in bot] + [R((0.14, 0.0))], M["leaf_sh"], 0.0, cyclic=True)
            G.seam(d, [R(p) for p in G.bezier((0.02, -0.005), (0.15, 0.05), (0.30, 0.05), n=8)], M["ink"])   # midrib
            for t in (0.12, 0.21):                                                                    # side veins
                G.seam(d, [R((t, 0.03 + 0.1 * t)), R((t + 0.04, 0.09 + 0.1 * t))], M["ink"])
                G.seam(d, [R((t, 0.02 + 0.1 * t)), R((t + 0.035, -0.03 + 0.05 * t))], M["ink"])
            G.stroke(d, pts, M["ink"], O, cyclic=True)
    return fn


PARTS = {
    "stem_lower": part_stem(L_STEM1, 0.05),
    "stem_upper": part_stem(L_STEM2, -0.04),
    "head_open": puff_head(1.0),
    "head_half": puff_head(0.55),
    "head_closed": head_closed,
    "leaves_rest": leaf_pair(0.0),
    "leaves_up": leaf_pair(1.0),
}


# ---------------------------------------------------------------- the bone chain (preview)

def affine(m):
    a, b, c, dd, tx, tz = m
    return lambda pts: [(a * x + b * z + tx, c * x + dd * z + tz) for x, z in pts]


def compose(m1, m2):
    a1, b1, c1, d1, x1, z1 = m1
    a2, b2, c2, d2, x2, z2 = m2
    return (a1 * a2 + b1 * c2, a1 * b2 + b1 * d2, c1 * a2 + d1 * c2, c1 * b2 + d1 * d2,
            a1 * x2 + b1 * z2 + x1, c1 * x2 + d1 * z2 + z1)


def rot_t(deg):
    r = math.radians(deg)
    return (math.cos(r), -math.sin(r), math.sin(r), math.cos(r), 0.0, 0.0)


def pose_mats(angles, squash):
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


def draw_posed(d, M, ang, squash, head, leaves):
    W = pose_mats(ang, squash)
    parts = {"root": "stem_lower", "leaves": leaves, "stem2": "stem_upper", "head": head}
    for b in sorted(BONES, key=lambda b: b["order"]):
        PARTS[parts[b["name"]]](G.Xf(d, affine(W[b["name"]])), M)


def preview_pose(i, n=12):
    """The idle Unity plays: sway on the beat (12 deg) with follow-through up the chain, 8 % squash;
    the head's slow yawn (open, half, closed, half) from the idle swap_cycle, compressed to 12 frames."""
    ph = 2 * math.pi * i / n
    ang = {"root": 6 * math.sin(ph), "stem2": 6 * math.sin(ph - 0.6), "head": 5 * math.sin(ph - 1.1),
           "leaves": 4 * math.sin(ph - 1.4)}
    squash = 1 + 0.04 * math.cos(2 * ph)
    head = ["head_open"] * 6 + ["head_half", "head_closed", "head_closed", "head_closed", "head_half", "head_open"]
    return ang, squash, head[i], "leaves_rest"


def build(out=os.path.join(SRC, "earth_rigset.blend")):
    """One GP object per part, drawn around its pivot (the object origin); the plant json on the scene."""
    import json
    scene = G.new_scene()
    scene["rig_plants"] = json.dumps([PLANT])
    coll = G.collection("parts")
    for name, fn in PARTS.items():
        ob, gp = G.gp_object("part_" + name, coll)
        layer = gp.layers.new("art")
        fn(G.drawing(layer, 1), mats(gp))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


def build_preview(out=os.path.join(SRC, "earth_rigset_preview.blend")):
    scene = G.new_scene()
    coll = G.collection("plant")
    ob, gp = G.gp_object("snoozle", coll)
    M = mats(gp)
    layer = gp.layers.new("art")
    for i in range(12):
        draw_posed(G.drawing(layer, i + 1), M, *preview_pose(i))
    # react (turn_bounce): squash down, bounce up with the head popping open and the leaves lifting, settle
    for k, (sq, lean, head, leaves) in enumerate([(0.86, 3.0, "head_half", "leaves_rest"), (1.14, -4.0, "head_open", "leaves_up"),
                                                  (1.0, 1.5, "head_open", "leaves_up")]):
        ang = {"root": lean, "stem2": lean * 0.6, "head": -lean * 0.5, "leaves": 0.0}
        draw_posed(G.drawing(layer, 13 + k), M, ang, sq, head, leaves)
    G.mark_clips(scene, [("idle", 12), ("react", 3)])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out
