"""Builds blender/sources/ships/pilgrim_v3_design.blend: the Pilgrim redesigned (B-117 step 1).

Original design (Bible §9.3 ship, §9.8): a bendy vintage rocket ~12 m long. A fat teal cigar
hull with a slight banana bend; a mustard nose cap that is the face: two porthole eyes (pie-cut
pupils behind the glass) and a brown grille mouth; an off-white riveted belly band; three mustard
fins with soft-red tips that wobble; hose-strut landing legs on round feet; a brown engine bell
breathing round cartoon puffs. Deliberately no checkerboard hull, no film rocket silhouette.

draw_pilgrim(d, M, pose): pose keys view 'side' | 'tq' | 'front', sx / sz (thrust stretch,
cut squash), fin (wobble rad), puffs (0 none .. 1 full thrust), legs (0 tucked .. 1 down),
look (pupil offset), blink.
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gp_draw as G  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "sources", "ships", "pilgrim_v3_design.blend")
P = G.PALETTES["earth"]
O, I = G.OUTER, G.INNER
L2 = 6.0                         # half length (m)
CZ = 2.6                         # hull centre height over the landing feet


def materials(gp):
    return {
        "hull": G.mat(gp, "hull_teal", fill=P["teal"]),
        "hull_sh": G.mat(gp, "hull_teal_shadow", fill=G.shadow_of(P["teal"]), ink=False),
        "nose": G.mat(gp, "nose_mustard", fill=P["mustard"]),
        "nose_sh": G.mat(gp, "nose_mustard_shadow", fill=G.shadow_of(P["mustard"]), ink=False),
        "band": G.mat(gp, "band_offwhite", fill=P["offwhite"]),
        "fin": G.mat(gp, "fin_mustard", fill=P["mustard"]),
        "tip": G.mat(gp, "fin_tip_red", fill=P["red"]),
        "bell": G.mat(gp, "bell_brown", fill=P["brown"]),
        "grille": G.mat(gp, "grille_brown", fill=P["brown"]),
        "glass": G.mat(gp, "porthole_glass", fill=P["offwhite"]),
        "pupil": G.mat(gp, "pupil", fill=G.INK, ink=False),
        "leg": G.mat(gp, "leg_offwhite", fill=P["offwhite"]),
        "foot": G.mat(gp, "foot_brown", fill=P["brown"]),
        "puff": G.mat(gp, "puff_offwhite", fill=P["offwhite"]),
        "puff_hot": G.mat(gp, "puff_mustard", fill=P["mustard"]),
        "ink": G.mat(gp, "ink_line", fill=None, ink=True),
        "rivet": G.mat(gp, "rivet", fill=G.INK, ink=False),
    }


def radius_at(t):
    """Hull radius profile along t in [-1 (tail) .. 1 (nose)]: fat cigar, rounder nose."""
    return 1.45 * (1 - abs(t) ** 2.6) ** 0.55 + 0.25 * (t < 0) * (1 - abs(t))


def draw_pilgrim(d, M, pose=None, seed=0):
    p = dict(view="side", sx=1.0, sz=1.0, fin=0.0, puffs=0.0, legs=1.0, look=(0.5, 0.0), blink=0.0, bend=0.35)
    p.update(pose or {})
    view = p["view"]
    if view == "front":
        return draw_front(d, M, p, seed)
    fx = 0.62 if view == "tq" else 1.0            # 3/4: the length foreshortened

    def T(x, z):                                   # stretch/squash about the hull centre, bend, foreshorten
        x2 = x * p["sx"] * fx
        return (x2, CZ + (z - CZ) * p["sz"] + p["bend"] * (x / L2) ** 2 * 0.6)

    def TL(pts):
        return [T(x, z) for x, z in pts]

    # exhaust puffs behind the bell (drawn first: behind the hull)
    if p["puffs"] > 0:
        for k in range(5):
            t = p["puffs"]
            r = (0.45 + 0.28 * k) * (0.6 + 0.5 * t)
            x = -L2 - 0.9 - 0.8 * k * (0.7 + 0.4 * t) - r * 0.6
            z = CZ - 0.1 * k + 0.12 * math.sin(k * 1.7 + seed)
            G.stroke(d, TL(G.lumpy_ellipse(x, z, r, r * 0.92, n=28, lump=0.07, seed=seed + 40 + k)),
                     M["puff_hot"] if k == 0 and t > 0.5 else M["puff"], O, cyclic=True)
    # legs (behind the hull): hose struts with round feet
    if p["legs"] > 0:
        for k, x0 in enumerate((-3.0, 2.4)):
            top = T(x0, CZ - 1.0)
            foot = (top[0] - 0.5 + 1.0 * k * 0.0, 0.25 + (1 - p["legs"]) * 1.4)
            mid = ((top[0] + foot[0]) / 2 - 0.35, (top[1] + foot[1]) / 2)
            G.stroke(d, G.hose_outline(G.bezier(top, mid, foot, n=10), 0.32), M["leg"], O, cyclic=True)
            G.stroke(d, G.lumpy_ellipse(foot[0], foot[1] - 0.04 + O * 1.25, 0.55, 0.22, n=24, seed=seed + 50 + k),
                     M["foot"], O, cyclic=True)
    # far fin (top) behind the hull
    def fin(base_x, side, ang):
        bx, bz = base_x, CZ + side * radius_at(base_x / L2) * 0.85
        a = ang + p["fin"] * side
        tipx, tipz = bx - 1.6 + 0.6 * math.sin(a), bz + side * (1.7 + 0.3 * math.cos(a))
        pts = G.bezier((bx + 1.3, bz), (bx + 0.2, bz + side * 0.9), (tipx, tipz), n=10) + \
            G.bezier((tipx, tipz), (bx - 1.2, bz + side * 0.6), (bx - 0.6, bz), n=10)[1:]
        G.stroke(d, TL(pts), M["fin"], O, cyclic=True)
        tip = G.lumpy_ellipse(tipx + 0.05, tipz - side * 0.15, 0.32, 0.26, n=18, seed=seed + 60 + side)
        G.stroke(d, TL(tip), M["tip"], O, cyclic=True)
    fin(-4.3, 1, 0.0)
    fin(-4.3, -1, 0.15)
    # engine bell
    bell = [(-L2 + 0.3, CZ + 0.75), (-L2 - 0.9, CZ + 1.05), (-L2 - 0.9, CZ - 1.05), (-L2 + 0.3, CZ - 0.75)]
    G.stroke(d, TL(G.bezier(bell[0], (-L2 - 0.3, CZ + 0.95), bell[1], n=6) + [bell[2]] +
                   G.bezier(bell[2], (-L2 - 0.3, CZ - 0.95), bell[3], n=6)[1:]), M["bell"], O, cyclic=True)
    # hull: fill, shadow belly, ink
    n = 70
    top = [(L2 * (2 * i / n - 1), CZ + radius_at(2 * i / n - 1)) for i in range(n + 1)]
    bot = [(L2 * (2 * i / n - 1), CZ - radius_at(2 * i / n - 1)) for i in range(n, -1, -1)]
    hull = TL(top + bot[1:-1])
    G.stroke(d, hull, M["hull"], 0.0, cyclic=True)
    belly = [(x, z) for x, z in bot[1:-1]]
    inner = [(x, CZ - radius_at(x / L2) * 0.55 - 0.05) for x, z in belly][::-1]
    G.stroke(d, TL(belly + inner), M["hull_sh"], 0.0, cyclic=True)
    # off-white riveted band
    band = [(x, CZ + radius_at(x / L2) * s) for s in (1,) for x in [-0.6 + 1.2 * i / 8 for i in range(9)]] + \
        [(x, CZ - radius_at(x / L2)) for x in [0.6 - 1.2 * i / 8 for i in range(9)]]
    G.stroke(d, TL(band), M["band"], I, cyclic=True)
    for k in range(5):
        zz = CZ + radius_at(0) * (0.8 - 0.4 * k)
        G.stroke(d, TL(G.lumpy_ellipse(0.0, zz, 0.06, 0.06, n=10, seed=k)), M["rivet"], 0.0, cyclic=True)
    G.stroke(d, hull, M["ink"], O, cyclic=True)
    # the nose cap = the face
    nose_x0 = 3.2
    ntop = [(x, CZ + radius_at(x / L2)) for x in [nose_x0 + (L2 - nose_x0) * i / 20 for i in range(21)]]
    nbot = [(x, CZ - radius_at(x / L2)) for x in [L2 - (L2 - nose_x0) * i / 20 for i in range(21)]]
    seam = G.bezier((nose_x0, CZ - radius_at(nose_x0 / L2)), (nose_x0 - 0.25, CZ), (nose_x0, CZ + radius_at(nose_x0 / L2)), n=10)
    nose = TL(ntop + nbot[1:] + seam[1:-1])
    G.stroke(d, nose, M["nose"], 0.0, cyclic=True)
    lo = [q for q in TL(nbot)][:-1]
    G.stroke(d, lo + TL([(x, CZ - radius_at(x / L2) * 0.6) for x, _z in nbot][:-1])[::-1], M["nose_sh"], 0.0, cyclic=True)
    G.stroke(d, TL(seam), M["ink"], I)
    G.stroke(d, nose, M["ink"], O, cyclic=True)
    # porthole eyes (back eye smaller in 3/4) and the grille mouth
    for k, (ex, ez, r) in enumerate(((4.15, CZ + 0.38, 0.46), (5.05, CZ + 0.38, 0.40 if view == "side" else 0.30))):
        cx, cz = T(ex, ez)
        G.stroke(d, G.lumpy_ellipse(cx, cz, r * fx ** 0.3 + 0.08, r + 0.08, n=28, seed=seed + 70 + k), M["bell"], I, cyclic=True)
        G.pie_eye(d, cx, cz, r * fx ** 0.3, r, M["pupil"], M["glass"], look=p["look"], seed=seed + 72 + k,
                  closed=p["blink"], m_lid=M["ink"])
    gx, gz = T(4.75, CZ - 0.62)
    gw, gh = 0.95 * fx ** 0.5, 0.40
    grille = G.lumpy_ellipse(gx, gz, gw / 2 + 0.08, gh / 2 + 0.05, n=24, lump=0.02, seed=seed + 80)
    G.stroke(d, grille, M["grille"], I, cyclic=True)
    for k in range(4):
        sx_ = gx - gw / 2 + gw * (k + 1) / 5
        G.stroke(d, [(sx_, gz - gh / 2 + 0.05), (sx_, gz + gh / 2 - 0.05)], M["ink"], I)
    # near fin (middle, in front of the hull)
    a = p["fin"]
    bx, bz = -4.0, CZ - 0.2
    tipx, tipz = bx - 2.2 + 0.5 * math.sin(a), bz - 0.5 + 0.3 * math.cos(a)
    pts = G.bezier((bx + 1.2, bz + 0.25), (bx - 0.4, bz + 0.4), (tipx, tipz), n=10) + \
        G.bezier((tipx, tipz), (bx - 0.6, bz - 0.5), (bx + 0.9, bz - 0.15), n=10)[1:]
    G.stroke(d, TL(pts), M["fin"], O, cyclic=True)
    G.stroke(d, TL(G.lumpy_ellipse(tipx + 0.1, tipz, 0.3, 0.24, n=18, seed=seed + 63)), M["tip"], O, cyclic=True)
    # a porthole glint on the hull
    G.stroke(d, TL(G.bezier((-2.0, CZ + 1.15), (-0.9, CZ + 1.35), (0.0, CZ + 1.32), n=8)), M["band"], 0.0)


def draw_front(d, M, p, seed):
    """Head-on: round nose face (two porthole eyes, grille), fins out to the sides, legs."""
    R = 1.45
    for s in (-1, 1):                               # side fins + legs
        a = p["fin"] * s
        pts = G.bezier((s * 1.1, CZ + 0.4), (s * 2.0, CZ + 0.9 + 0.3 * a), (s * 2.6, CZ + 0.2 + 0.4 * a), n=10) + \
            G.bezier((s * 2.6, CZ + 0.2 + 0.4 * a), (s * 2.0, CZ - 0.4), (s * 1.1, CZ - 0.5), n=10)[1:]
        G.stroke(d, pts, M["fin"], O, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(s * 2.55, CZ + 0.15 + 0.4 * a, 0.3, 0.26, n=18, seed=seed + 61 + s), M["tip"], O, cyclic=True)
        top, foot = (s * 0.9, CZ - 1.0), (s * 1.9, 0.25)
        G.stroke(d, G.hose_outline(G.bezier(top, (s * 1.7, CZ - 0.8), foot, n=10), 0.32), M["leg"], O, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(foot[0], foot[1] - 0.04 + O * 1.25, 0.5, 0.22, n=24, seed=seed + 51 + s), M["foot"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0, CZ, R, R, n=60, lump=0.02, seed=seed + 1), M["nose"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0, CZ - 0.05, R * 0.55, R * 0.55, n=40, seed=seed + 2), M["nose_sh"], 0.0, cyclic=True)
    for k, ex in enumerate((-0.55, 0.55)):
        G.stroke(d, G.lumpy_ellipse(ex, CZ + 0.38, 0.5, 0.5, n=28, seed=seed + 70 + k), M["bell"], I, cyclic=True)
        G.pie_eye(d, ex, CZ + 0.38, 0.42, 0.42, M["pupil"], M["glass"], look=(0.0, 0.0), seed=seed + 72 + k,
                  closed=p["blink"], m_lid=M["ink"])
    grille = G.lumpy_ellipse(0, CZ - 0.62, 0.55, 0.24, n=24, lump=0.02, seed=seed + 80)
    G.stroke(d, grille, M["grille"], I, cyclic=True)
    for k in range(4):
        x = -0.44 + 0.88 * (k + 1) / 5
        G.stroke(d, [(x, CZ - 0.80), (x, CZ - 0.44)], M["ink"], I)
    G.stroke(d, G.lumpy_ellipse(0, CZ + R + 0.15, 0.18, 0.18, n=16, seed=seed + 3), M["tip"], O, cyclic=True)


DESIGN = [dict(view="side"), dict(view="tq"), dict(view="front"),
          dict(view="side", sx=1.18, sz=0.88, puffs=1.0, legs=0.0, fin=0.35),
          dict(view="side", sx=0.86, sz=1.14, puffs=0.15, legs=0.0, fin=-0.3, blink=0.6),
          dict(view="side", puffs=0.55, legs=1.0, look=(0.3, -0.4))]


def build(out=OUT):
    scene = G.new_scene()
    coll = G.collection("pilgrim")
    ob, gp = G.gp_object("pilgrim", coll)
    M = materials(gp)
    layer = gp.layers.new("art")
    for i, pose in enumerate(DESIGN):
        draw_pilgrim(G.drawing(layer, i + 1), M, pose, seed=10 * i)
    G.mark_clips(scene, [("design", len(DESIGN))])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


if __name__ == "__main__":
    build()
