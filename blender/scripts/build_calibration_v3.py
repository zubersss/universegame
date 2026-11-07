"""Builds blender/sources/characters/calibration_v3.blend: the v3 pipeline test blob (B-110).

A round lumpy blob with pie-cut eyes, hose legs and gloved hose arms, drawn frame by frame in
Grease Pencil at 12 drawings per second: `idle` (8, squash bob + a blink) and `walk` (12,
bouncy, head bob on every step, big arm swing). Earth palette (Bible §9.1). Deterministic.

  blender --background --factory-startup --python blender/scripts/build_calibration_v3.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gp_draw as G  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "characters", "calibration_v3.blend")
CLIPS = [("idle", 8), ("walk", 12)]
P = G.PALETTES["earth"]


def squash(pts, sx, sz, cx=0.0, cz=0.0):
    return [(cx + (x - cx) * sx, cz + (z - cz) * sz) for x, z in pts]


def draw_blob(d, M, bob=0.0, sz=1.0, lean=0.0, legs=((0.0, 0.0), (0.0, 0.0)), arms=(0.0, 0.0),
              blink=0.0, look=(0.35, 0.1), seed=0):
    """One drawing. legs: (foot_dx, foot_lift) back, front; arms: swing angles (rad)."""
    sx = 1.0 / math.sqrt(sz)
    body_cz = 0.95 + bob
    ground = 0.0

    def body_xf(pts):
        pts = squash(pts, sx, sz, 0.0, 0.5)
        return [(x + lean * (z - 0.5), z + bob) for x, z in pts]

    # legs (behind the body): hips under the body, feet on the ground
    for k, (dx, lift) in enumerate(legs):
        hip = (-0.13 + 0.26 * k + lean * 0.1, 0.58 + bob)
        foot = (hip[0] + dx, ground + 0.07 + lift)
        knee = ((hip[0] + foot[0]) / 2 + 0.10, (hip[1] + foot[1]) / 2)
        c = G.bezier(hip, knee, foot, n=10)
        G.stroke(d, G.hose_outline(c, 0.075), M["leg"], G.OUTER, cyclic=True)
        G.ribs(d, c[1:-1], 0.075, M["ink"], every=0.07)
        shoe = G.lumpy_ellipse(foot[0] + 0.07, foot[1] - 0.07 + 0.07 * 1.04 + G.OUTER * 1.25, 0.13, 0.07, n=24, lump=0.04, seed=seed + 11 + k)
        G.stroke(d, shoe, M["shoe"], 0.0, cyclic=True)
        zmin = min(q[1] for q in shoe)
        sole = [q for q in shoe if q[1] < zmin + 0.035]
        if len(sole) > 3:
            G.stroke(d, sole, M["shoe_deep"], 0.0, cyclic=True)
            G.seam(d, G.bowed_line((min(q[0] for q in sole) + 0.01, zmin + 0.035), (max(q[0] for q in sole) - 0.01, zmin + 0.035), bow=0.03, n=6), M["ink"])
        G.stroke(d, shoe, M["ink"], G.OUTER, cyclic=True)

    # back arm
    def arm(side, ang):
        sh = (side * 0.42, 0.95)
        sh = body_xf([sh])[0]
        hand = (sh[0] + 0.30 * math.sin(ang) * side + side * 0.10, sh[1] - 0.30 * math.cos(ang))
        mid = ((sh[0] + hand[0]) / 2 + side * 0.08, (sh[1] + hand[1]) / 2 + 0.03)
        G.stroke(d, G.hose_outline(G.bezier(sh, mid, hand, n=10), 0.06), M["leg"], G.OUTER, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(hand[0], hand[1], 0.085, 0.08, n=20, lump=0.05, seed=seed + 21 + side),
                 M["glove"], G.OUTER, cyclic=True)
        for j in (-1, 1):
            G.seam(d, G.bowed_line((hand[0] + j * 0.025, hand[1] - 0.005), (hand[0] + j * 0.03, hand[1] - 0.06), bow=0.1, n=4), M["ink"])
    arm(-1, arms[0])

    # body: fill, one shadow tone (lower crescent), then the ink outline on top
    outline = body_xf(G.lumpy_ellipse(0.0, 0.95, 0.46, 0.42, n=56, lump=0.03, seed=seed))
    G.stroke(d, outline, M["body"], 0.0, cyclic=True)
    n = len(outline)
    lo = [i for i in range(n) if math.sin(6.283185 * i / n) < -0.15]
    cx, cz = body_xf([(0.0, 0.95)])[0]
    outer_arc = [outline[i] for i in lo]
    inner_arc = [(cx + (x - cx) * 0.80 + 0.03, cz + (z - cz) * 0.62 + 0.02) for x, z in outer_arc][::-1]
    G.stroke(d, outer_arc + inner_arc, M["body_shadow"], 0.0, cyclic=True)
    deep = [outline[i] for i in range(n) if math.sin(6.283185 * i / n) < -0.45 and math.cos(6.283185 * i / n) < 0.35]
    if len(deep) > 3:
        deep_in = [(cx + (x - cx) * 0.88 + 0.02, cz + (z - cz) * 0.80 + 0.03) for x, z in deep][::-1]
        G.stroke(d, deep + deep_in, M["body_deep"], 0.0, cyclic=True)
    belly = body_xf(G.bezier((-0.40, 0.80), (0.0, 0.64), (0.41, 0.80), n=14))
    G.seam(d, belly, M["ink"])
    G.stitches(d, body_xf(G.bezier((-0.36, 0.765), (0.0, 0.615), (0.37, 0.765), n=14)), M["ink"], every=0.07, length=0.025)
    hx_, hz_ = body_xf([(-0.27, 0.72)])[0]
    G.hatch(d, hx_, hz_, M["ink"], n=3, length=0.08, spacing=0.03, angle_deg=60, seed=seed + 5)
    G.specks(d, body_xf([(0.30, 1.20), (0.35, 1.14), (0.26, 1.13), (-0.30, 1.16)]), M["ink"])
    G.stroke(d, outline, M["ink"], G.OUTER, cyclic=True)

    # face: two pie-cut eyes and a smile (interior lines)
    for k, ex in enumerate((0.03, 0.23)):
        e = body_xf([(ex, 1.07)])[0]
        G.pie_eye(d, e[0], e[1], 0.085, 0.12 * sz ** 0.5, M["pupil"], M["eye"], look=look,
                  seed=seed + 31 + k, closed=blink, m_lid=M["ink"])
    m0, m1, m2 = body_xf([(-0.02, 0.86), (0.15, 0.77), (0.30, 0.87)])
    G.stroke(d, G.bezier(m0, m1, m2, n=12), M["ink"], G.INNER)
    arm(1, arms[1])


def build(out=DEFAULT_OUT):
    scene = G.new_scene()
    coll = G.collection("blob")
    ob, gp = G.gp_object("blob", coll)
    M = {
        "body": G.mat(gp, "blob_body", fill=P["red"], ink=False),
        "body_shadow": G.mat(gp, "blob_body_shadow", fill=G.shadow_of(P["red"]), ink=False),
        "body_deep": G.mat(gp, "blob_body_deep", fill=G.deep_of(P["red"]), ink=False),
        "shoe_deep": G.mat(gp, "shoe_brown_deep", fill=G.deep_of(P["brown"]), ink=False),
        "ink": G.mat(gp, "ink_line", fill=None, ink=True),
        "leg": G.mat(gp, "hose_teal", fill=P["teal"]),
        "shoe": G.mat(gp, "shoe_brown", fill=P["brown"]),
        "glove": G.mat(gp, "glove_white", fill=P["offwhite"]),
        "eye": G.mat(gp, "eye_white", fill=P["offwhite"]),
        "pupil": G.mat(gp, "pupil_black", fill=G.INK, ink=False),
    }
    layer = gp.layers.new("art")
    f = 1
    # idle: 8 drawings, squash bob on the beat (down on 0 and 4), blink on 5-6
    for i in range(8):
        ph = 2 * math.pi * i / 8
        sz = 1.0 + 0.07 * math.cos(2 * ph)
        blink = {5: 0.6, 6: 1.0}.get(i, 0.0)
        draw_blob(G.drawing(layer, f), M, bob=0.015 * math.cos(2 * ph),
                  sz=sz, arms=(0.15 * math.sin(ph), -0.15 * math.sin(ph)), blink=blink, seed=100 + i)
        f += 1
    # walk: 12 drawings, feet cycle, bob twice per cycle (head bob on every step), arms swing
    for i in range(12):
        ph = 2 * math.pi * i / 12
        legs = []
        for k in range(2):
            p = ph + math.pi * k
            legs.append((0.24 * math.sin(p), max(0.0, 0.14 * math.cos(p))))
        bob = 0.06 * abs(math.cos(ph)) - 0.02      # high at passing (ph 0, pi), low at contact
        sz = 1.0 + 0.06 * math.cos(2 * ph)
        draw_blob(G.drawing(layer, f), M, bob=bob, sz=sz, lean=0.10, legs=legs,
                  arms=(0.7 * math.sin(ph), -0.7 * math.sin(ph)), look=(0.6, 0.0), seed=200 + i)
        f += 1
    G.mark_clips(scene, CLIPS)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


def build_rigtest(out):
    """§11.3 packer test (preview only): a stem segment, a flower head, a leaf and face swaps,
    one GP object per part with its origin at the part's pivot."""
    G.new_scene()
    coll = G.collection("parts")

    def part(name, fn):
        ob, gp = G.gp_object("part_" + name, coll)
        layer = gp.layers.new("art")
        fn(G.drawing(layer, 1), gp)

    def stem(d, gp):
        c = G.bezier((0, 0), (0.05, 0.3), (0, 0.6), n=10)
        G.stroke(d, G.hose_outline(c, 0.09), G.mat(gp, "stem_green", fill=P["green"]), G.OUTER, cyclic=True)

    def head(d, gp):
        m = G.mat(gp, "petal_mustard", fill=P["mustard"])
        for k in range(7):
            a = 6.283 * k / 7
            G.stroke(d, G.lumpy_ellipse(0.24 * math.cos(a), 0.24 * math.sin(a), 0.13, 0.09, n=20, seed=k, rot=a),
                     m, G.OUTER, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(0, 0, 0.2, 0.19, n=36, seed=9), G.mat(gp, "face_off", fill=P["offwhite"]),
                 G.OUTER, cyclic=True)

    def leaf(d, gp):
        pts = G.bezier((0, 0), (0.12, 0.12), (0.30, 0.02), n=10) + G.bezier((0.30, 0.02), (0.14, -0.08), (0, 0), n=10)[1:-1]
        G.stroke(d, pts, G.mat(gp, "leaf_green", fill=P["green"]), G.OUTER, cyclic=True)

    def mouth(kind):
        def fn(d, gp):
            ink = G.mat(gp, "ink_line", fill=None, ink=True)
            if kind == "smile":
                G.stroke(d, G.bezier((-0.07, 0.0), (0, -0.05), (0.07, 0.0), n=10), ink, G.INNER)
            else:
                G.stroke(d, G.lumpy_ellipse(0, 0, 0.045, 0.06, n=20, seed=3), G.mat(gp, "mouth_red", fill=P["red"]),
                         G.INNER, cyclic=True)
        return fn

    def eyes(closed):
        def fn(d, gp):
            ink = G.mat(gp, "ink_line", fill=None, ink=True)
            for ex in (-0.06, 0.06):
                G.pie_eye(d, ex, 0, 0.04, 0.055, G.mat(gp, "pupil_black", fill=G.INK, ink=False),
                          G.mat(gp, "eye_white", fill=P["offwhite"]), closed=closed, m_lid=ink, seed=int(ex * 100))
        return fn
    part("stem", stem)
    part("head", head)
    part("leaf", leaf)
    part("mouth_smile", mouth("smile"))
    part("mouth_yawn", mouth("yawn"))
    part("eyes_open", eyes(0.0))
    part("eyes_blink", eyes(1.0))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(argv[0] if argv else DEFAULT_OUT)
