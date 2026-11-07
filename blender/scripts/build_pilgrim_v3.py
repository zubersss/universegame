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
    if view == "top":
        return draw_top(d, M, p, seed)
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
            r = (0.45 + 0.20 * k) * (0.6 + 0.4 * t)
            x = -L2 - 0.9 - 0.7 * k * (0.7 + 0.4 * t) - r * 0.6
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


def draw_top(d, M, p, seed):
    """Seen from above (Space view, nose to +x): cigar hull with the band, the mustard nose with
    the two porthole eyes looking ahead, the side fins spread port and starboard, the top fin as
    a ridge; no legs, no grille (it is under the chin). Centred on z = 0 (pivot 0.5, 0.5)."""
    sx, sz = p["sx"], p["sz"]

    def T(x, z):
        return (x * sx, z * sz + p["bend"] * 0.0)

    def TL(pts):
        return [T(x, z) for x, z in pts]
    for s in (-1, 1):                                   # side fins, wobbling
        a = p["fin"] * s
        bx = -4.3
        tipx, tipz = bx - 1.6 + 0.4 * math.sin(a), s * (radius_at(bx / L2) * 0.85 + 1.7 + 0.25 * math.cos(a))
        pts = G.bezier((bx + 1.3, s * 0.9), (bx + 0.2, s * 1.8), (tipx, tipz), n=10) + \
            G.bezier((tipx, tipz), (bx - 1.2, s * 1.5), (bx - 0.6, s * 0.9), n=10)[1:]
        G.stroke(d, TL(pts), M["fin"], O, cyclic=True)
        G.stroke(d, TL(G.lumpy_ellipse(tipx + 0.05, tipz - s * 0.15, 0.32, 0.26, n=18, seed=seed + 60 + s)), M["tip"], O, cyclic=True)
    bell = [(-L2 + 0.3, 0.75), (-L2 - 0.9, 1.05), (-L2 - 0.9, -1.05), (-L2 + 0.3, -0.75)]
    G.stroke(d, TL(bell), M["bell"], O, cyclic=True)
    n = 70
    top = [(L2 * (2 * i / n - 1), radius_at(2 * i / n - 1)) for i in range(n + 1)]
    bot = [(L2 * (2 * i / n - 1), -radius_at(2 * i / n - 1)) for i in range(n, -1, -1)]
    hull = TL(top + bot[1:-1])
    G.stroke(d, hull, M["hull"], 0.0, cyclic=True)
    shadow = [(x, z) for x, z in bot[1:-1]]
    G.stroke(d, TL(shadow + [(x, -radius_at(x / L2) * 0.55) for x, _z in shadow][::-1]), M["hull_sh"], 0.0, cyclic=True)
    band = [(x, radius_at(x / L2)) for x in [-0.6 + 1.2 * i / 8 for i in range(9)]] + \
        [(x, -radius_at(x / L2)) for x in [0.6 - 1.2 * i / 8 for i in range(9)]]
    G.stroke(d, TL(band), M["band"], I, cyclic=True)
    G.stroke(d, TL([(-3.8, 0.0), (-1.6, 0.0)]), M["ink"], I)          # the top fin as a ridge line
    G.stroke(d, hull, M["ink"], O, cyclic=True)
    ntop = [(x, radius_at(x / L2)) for x in [3.2 + (L2 - 3.2) * i / 20 for i in range(21)]]
    nbot = [(x, -radius_at(x / L2)) for x in [L2 - (L2 - 3.2) * i / 20 for i in range(21)]]
    seam = G.bezier((3.2, -radius_at(3.2 / L2)), (2.95, 0.0), (3.2, radius_at(3.2 / L2)), n=10)
    nose = TL(ntop + nbot[1:] + seam[1:-1])
    G.stroke(d, nose, M["nose"], 0.0, cyclic=True)
    G.stroke(d, TL(seam), M["ink"], I)
    G.stroke(d, nose, M["ink"], O, cyclic=True)
    for k, ez in enumerate((0.48, -0.48)):
        cx, cz = T(4.6, ez)
        G.stroke(d, G.lumpy_ellipse(cx, cz, 0.42, 0.42, n=28, seed=seed + 70 + k), M["bell"], I, cyclic=True)
        G.pie_eye(d, cx, cz, 0.34, 0.34, M["pupil"], M["glass"], look=(0.6, 0.0), seed=seed + 72 + k,
                  closed=p["blink"], m_lid=M["ink"])


def draw_puff(d, M, f, n=8):
    """The exhaust puff loop (128^2 at 1x, pivot at the bell on the right): three round puffs
    born at the bell, growing and drifting left, the oldest shrinking away; hot mustard core."""
    for k in range(3):
        t = ((f / n) + k / 3) % 1.0
        r = 0.18 + 0.42 * math.sin(math.pi * min(t * 1.2, 1.0))
        x = -0.2 - 1.15 * t
        z = 0.05 * math.sin(6.28 * t + k)
        if r > 0.06:
            G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.92, n=24, lump=0.07, seed=31 * k + f),
                     M["puff_hot"] if t < 0.22 else M["puff"], O, cyclic=True)


# ---- B-122 sheets: clips per contract §11.2 caps (thrust stretch capped at 1.12 so frames fit 1016 px)
TAU = 2 * math.pi
SIDE_IDLE = [dict(fin=0.12 * math.sin(TAU * i / 8), sz=1 + 0.02 * math.cos(TAU * i / 8), sx=1 - 0.01 * math.cos(TAU * i / 8),
                  blink=1.0 if i == 5 else 0.0, look=(0.5, -0.1)) for i in range(8)]
SIDE_THRUST = [dict(legs=0.0, sx=1.08 + 0.04 * math.sin(TAU * i / 8), sz=0.93 - 0.03 * math.sin(TAU * i / 8),
                    fin=-0.30 + 0.10 * math.sin(TAU * i / 8 - 1.2), look=(0.8, 0.0), bend=0.45) for i in range(8)]
SIDE_CUT = [dict(legs=0.0, sx=s_x, sz=s_z, fin=fn, blink=bl) for s_x, s_z, fn, bl in
            ((0.88, 1.12, 0.35, 0.6), (0.92, 1.09, 0.25, 0.0), (1.04, 0.97, -0.15, 0.0),
             (0.98, 1.02, 0.08, 0.0), (1.01, 0.99, -0.03, 0.0), (1.0, 1.0, 0.0, 0.0))]
SIDE_LAND = [dict(legs=lg, sx=s_x, sz=s_z, fin=fn, look=(0.3, -0.5)) for lg, s_x, s_z, fn in
             ((0.0, 1.0, 1.0, 0.0), (0.35, 1.0, 1.02, -0.05), (0.7, 0.99, 1.03, -0.08), (1.0, 1.0, 1.02, -0.05),
              (1.0, 1.08, 0.86, 0.30), (1.0, 0.97, 1.05, -0.12), (1.0, 1.01, 0.99, 0.05), (1.0, 1.0, 1.0, 0.0))]
TOP_IDLE = [dict(view="top", fin=0.12 * math.sin(TAU * i / 8), sz=1 + 0.02 * math.cos(TAU * i / 8), blink=1.0 if i == 5 else 0.0)
            for i in range(8)]
TOP_THRUST = [dict(view="top", sx=1.08 + 0.04 * math.sin(TAU * i / 8), sz=0.93 - 0.03 * math.sin(TAU * i / 8),
                   fin=-0.30 + 0.10 * math.sin(TAU * i / 8 - 1.2)) for i in range(8)]
SHEET_CLIPS = [("idle", SIDE_IDLE), ("thrust", SIDE_THRUST), ("cut", SIDE_CUT), ("land", SIDE_LAND),
               ("top_idle", TOP_IDLE), ("top_thrust", TOP_THRUST)]
SHEETS_OUT = os.path.join(os.path.dirname(HERE), "sources", "ships", "pilgrim_v3.blend")


def build_sheets(out=SHEETS_OUT):
    """All Pilgrim clips in one source (markers per clip); the manifest's side_a..d / top_a..b
    entries each pick theirs. The puff loop is its own object (collection 'puff')."""
    scene = G.new_scene()
    coll = G.collection("pilgrim")
    ob, gp = G.gp_object("pilgrim", coll)
    M = materials(gp)
    layer = gp.layers.new("art")
    f = 1
    clips = []
    for name, poses in SHEET_CLIPS:
        for i, pose in enumerate(poses):
            draw_pilgrim(G.drawing(layer, f), M, pose, seed=7 * f)
            f += 1
        clips.append((name, len(poses)))
    pc = G.collection("puff")
    pob, pgp = G.gp_object("puff", pc)
    PM = materials(pgp)
    play = pgp.layers.new("art")
    for i in range(8):
        draw_puff(G.drawing(play, f + i), PM, i)
    clips.append(("puff", 8))
    G.mark_clips(scene, clips)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


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




# ======================================================================== B-123: upright, faceless
# D-102: the Pilgrim stands on its tail (fins = legs) and flies nose-up in the atmosphere, thrust
# along its own up axis, A/D tilt to +-35 deg. D-101: no face: ONE off-centre brass porthole (never
# two side by side), panel seams, rivet rows, hatch marks; v3.1 ink + mid / deep tones (D-100).
# Local frame: x lateral, z up from the landing pads (z = 0); the pose transform stretches about
# the centre of mass, bends the axis a little, tilts about the centre of mass and lifts the ship.

UP_Z0, UP_Z1 = 1.6, 11.4          # hull from the engine bell top to the nose tip
UP_ZC = 6.2                       # centre of mass (tilt and stretch pivot)


def up_radius(z):
    t = (z - (UP_Z0 + UP_Z1) / 2) / ((UP_Z1 - UP_Z0) / 2)
    return radius_at(max(-1.0, min(1.0, t)))


def materials_v2(gp):
    M = materials(gp)
    M.update({
        "hull_dp": G.mat(gp, "hull_teal_deep", fill=G.deep_of(P["teal"]), ink=False),
        "fin_sh": G.mat(gp, "fin_mustard_mid", fill=G.shadow_of(P["mustard"]), ink=False),
        "brass": G.mat(gp, "porthole_brass", fill=P["mustard"]),
        "port_glass": G.mat(gp, "porthole_glass_sky", fill=G.shadow_of(P["sky"]), ink=False),
        "glint": G.mat(gp, "glint", fill=None, ink=True, ink_hex=P["offwhite"]),
        "bell_dp": G.mat(gp, "bell_deep", fill=G.deep_of(P["brown"]), ink=False),
    })
    return M


def up_puffs(D, M, k_puffs, seed):
    """Round puffs from the bell along -z (the ship's own down axis): drawn in local coordinates."""
    for k in range(5):
        r = (0.40 + 0.18 * k) * (0.6 + 0.4 * k_puffs)
        z = UP_Z0 - 0.9 - 0.75 * k * (0.7 + 0.5 * k_puffs) - r * 0.6
        x = 0.18 * math.sin(k * 1.9 + seed)
        G.stroke(D, G.lumpy_ellipse(x, z, r, r * 0.92, n=26, lump=0.07, seed=seed + 40 + k),
                 M["puff_hot"] if k == 0 and k_puffs > 0.5 else M["puff"], O, cyclic=True)
        if k > 0:
            G.seam(D, G.bezier((x - r * 0.5, z - r * 0.15), (x, z - r * 0.45), (x + r * 0.45, z - r * 0.2), n=6), M["ink"])


def up_fin(D, M, side, fin):
    """A side fin that is also a leg: from the hull flank down and out to a round landing pad."""
    a = fin * side
    top = (side * up_radius(3.6) * 0.92, 3.6)
    root = (side * up_radius(2.0) * 0.95, 2.0)
    tip = (side * (2.25 + 0.15 * a), 0.30 + 0.12 * a)
    pts = G.bezier(top, (side * 1.9, 2.9), tip, n=12) + G.bezier(tip, (side * 1.6, 0.9), root, n=10)[1:]
    G.stroke(D, pts, M["fin"], 0.0, cyclic=True)
    shade = [q for q in pts if q[1] < 1.6]
    if len(shade) > 3:
        G.stroke(D, shade, M["fin_sh"], 0.0, cyclic=True)
    G.seam(D, G.bezier((top[0] * 0.98, 3.3), (side * 1.75, 2.4), (tip[0] * 0.92, 0.55), n=8), M["ink"])
    G.rivets(D, [(side * 1.25, 3.05), (side * 1.5, 2.55), (side * 1.75, 2.0)], M["ink"])
    G.stroke(D, pts, M["ink"], O, cyclic=True)
    pad = G.lumpy_ellipse(tip[0], 0.16 + O * 1.25, 0.42, 0.16, n=22, seed=60 + side)
    G.stroke(D, pad, M["foot"], 0.0, cyclic=True)
    G.stroke(D, [q for q in pad if q[1] < 0.16 + O * 1.25 - 0.04], M["bell_dp"], 0.0, cyclic=True)
    G.stroke(D, pad, M["ink"], O, cyclic=True)
    tipm = G.lumpy_ellipse(top[0] + side * 0.05, top[1] + 0.05, 0.22, 0.17, n=16, seed=63 + side)
    G.stroke(D, tipm, M["tip"], O, cyclic=True)


UP_POSE = dict(sx=1.0, sz=1.0, tilt=0.0, lift=0.0, bend=0.0, lean=0.0, fin=0.0, puffs=0.0, center_fin=True, door=True)


def up_xf(p):
    """The pose transform of the upright ship (local metres -> sprite metres, pivot at the pads):
    stretch/squash about the centre of mass, a bend, a lean (shear about the CoM: the body leans,
    the fins drag), a tilt about the CoM, a lift. Shared by the drawing and the sockets."""
    ca, sa = math.cos(math.radians(p["tilt"])), math.sin(math.radians(p["tilt"]))

    def TL(pts):
        out = []
        for x, z in pts:
            x2 = x * p["sx"] + p["bend"] * ((z - UP_ZC) / 5.0) ** 2 * 0.5 + p["lean"] * (z - UP_ZC)
            z2 = UP_ZC + (z - UP_ZC) * p["sz"]
            dx, dz = x2, z2 - UP_ZC                  # tilt about the centre of mass (+ = leans right)
            out.append((dx * ca + dz * sa, UP_ZC + (-dx * sa + dz * ca) + p["lift"]))
        return out
    return TL


# B-122 sockets (local metres, before the pose): where the game attaches things
UP_SOCKETS = {"tail_exhaust": (0.0, UP_Z0 - 0.75), "leg_l": (-2.25, 0.16), "leg_c": (0.0, 0.16),
              "leg_r": (2.25, 0.16), "door": (-0.05, 2.35)}


def up_sockets(pose):
    p = dict(UP_POSE)
    p.update(pose or {})
    TL = up_xf(p)
    return {k: [round(c, 4) for c in TL([v])[0]] for k, v in UP_SOCKETS.items()}


def draw_upright(d, M, pose=None, seed=0):
    p = dict(UP_POSE)
    p.update(pose or {})
    TL = up_xf(p)
    D = G.Xf(d, TL)
    if p["puffs"] > 0:
        up_puffs(D, M, p["puffs"], seed)
    up_fin(D, M, -1, p["fin"])                          # far-left fin behind the hull
    if p["center_fin"]:                                 # the face-on centre fin-leg, behind bell and hull
        cf = [(-0.22, 3.0), (0.22, 3.0), (0.16, 0.45), (-0.16, 0.45)]
        G.stroke(D, cf, M["fin"], 0.0, cyclic=True)
        G.stroke(D, [(-0.22, 3.0), (-0.05, 3.0), (-0.04, 0.45), (-0.16, 0.45)], M["fin_sh"], 0.0, cyclic=True)
        G.seam(D, [(0.0, 2.8), (0.0, 0.7)], M["ink"])
        G.stroke(D, cf, M["ink"], O, cyclic=True)
        pad = G.lumpy_ellipse(0.0, 0.16 + O * 1.25, 0.34, 0.15, n=20, seed=seed + 8)
        G.stroke(D, pad, M["foot"], O, cyclic=True)
    # engine bell under the hull
    bell = G.bezier((-0.70, UP_Z0 + 0.25), (-0.80, UP_Z0 - 0.3), (-0.95, UP_Z0 - 0.75), n=6) + \
        [(0.95, UP_Z0 - 0.75)] + G.bezier((0.95, UP_Z0 - 0.75), (0.80, UP_Z0 - 0.3), (0.70, UP_Z0 + 0.25), n=6)[1:]
    G.stroke(D, bell, M["bell"], 0.0, cyclic=True)
    G.stroke(D, [q for q in bell if q[0] < -0.3], M["bell_dp"], 0.0, cyclic=True)
    for zz in (UP_Z0 - 0.25, UP_Z0 - 0.5):
        G.seam(D, G.bowed_line((-0.85, zz), (0.85, zz), bow=-0.04, n=6), M["ink"])
    G.stroke(D, bell, M["ink"], O, cyclic=True)
    # hull: fill, mid + deep shadow down the left flank, riveted band, panel seams, rivet rows, hatch
    zs = [UP_Z0 + (UP_Z1 - UP_Z0) * i / 60 for i in range(61)]
    right = [(up_radius(z), z) for z in zs]
    left = [(-up_radius(z), z) for z in zs[::-1]]
    hull = right + left[1:-1]
    G.stroke(D, hull, M["hull"], 0.0, cyclic=True)
    G.stroke(D, [(-up_radius(z), z) for z in zs] + [(-up_radius(z) * 0.45, z) for z in zs[::-1]], M["hull_sh"], 0.0, cyclic=True)
    G.stroke(D, [(-up_radius(z), z) for z in zs] + [(-up_radius(z) * 0.80, z) for z in zs[::-1]], M["hull_dp"], 0.0, cyclic=True)
    band = [(up_radius(z), z) for z in (5.0, 5.15, 5.3, 5.45, 5.6)] + [(-up_radius(z), z) for z in (5.6, 5.45, 5.3, 5.15, 5.0)]
    G.stroke(D, band, M["band"], I, cyclic=True)
    G.rivets(D, [(x, 5.3) for x in (-1.05, -0.6, -0.15, 0.3, 0.75, 1.15)], M["ink"])
    for zz in (3.3, 8.2):
        r = up_radius(zz)
        G.seam(D, G.bowed_line((-r * 0.97, zz), (r * 0.97, zz), bow=-0.03, n=8), M["ink"])
        G.rivets(D, [(x * r, zz + 0.16) for x in (-0.7, -0.35, 0.0, 0.35, 0.7)], M["ink"])
    G.seam(D, [(0.62 * up_radius(z), z) for z in [2.0 + 0.4 * i for i in range(8)]], M["ink"])       # a vertical panel seam
    G.seam(D, [(-0.55 * up_radius(z), z) for z in [5.8 + 0.3 * i for i in range(9)]], M["ink"])
    G.hatch(D, -1.0, 4.2, M["ink"], n=4, length=0.45, spacing=0.14, angle_deg=72, seed=seed + 3)
    G.hatch(D, -0.95, 7.0, M["ink"], n=3, length=0.4, spacing=0.14, angle_deg=72, seed=seed + 4)
    G.specks(D, [(0.9, 6.4), (1.0, 6.6), (0.85, 6.9), (-0.2, 2.6)], M["ink"])
    if p["door"]:                                       # the boarding hatch (socket "door" at its sill)
        door = G.bezier((-0.42, 2.35), (-0.45, 3.4), (-0.30, 4.05), n=8) + G.bezier((-0.30, 4.05), (-0.05, 4.25), (0.20, 4.05), n=6)[1:] + \
            G.bezier((0.20, 4.05), (0.33, 3.4), (0.32, 2.35), n=8)[1:]
        G.stroke(D, door, M["hull_sh"], I, cyclic=True)
        G.rivets(D, [(-0.36, 2.6), (-0.39, 3.2), (-0.37, 3.8), (0.26, 2.6), (0.28, 3.2), (0.26, 3.8)], M["ink"])
        G.seam(D, [(-0.42, 3.0), (-0.52, 3.0)], M["ink"])                 # hinges
        G.seam(D, [(-0.43, 3.6), (-0.53, 3.6)], M["ink"])
        G.stroke(D, G.lumpy_ellipse(0.17, 3.15, 0.05, 0.05, n=10, seed=seed + 9), M["brass"], I, cyclic=True)   # handle
    G.stroke(D, hull, M["ink"], O, cyclic=True)
    # nose cone (mustard) with its seam and a red knob on the tip
    nz = 9.2
    cone = [(up_radius(z), z) for z in [nz + (UP_Z1 - nz) * i / 20 for i in range(21)]] + \
        [(-up_radius(z), z) for z in [UP_Z1 - (UP_Z1 - nz) * i / 20 for i in range(21)]][1:]
    G.stroke(D, cone, M["nose"], 0.0, cyclic=True)
    G.stroke(D, [(-up_radius(z), z) for z in [nz + (UP_Z1 - nz) * i / 20 for i in range(21)]] +
             [(-up_radius(z) * 0.5, z) for z in [UP_Z1 - (UP_Z1 - nz) * i / 20 for i in range(21)]], M["nose_sh"], 0.0, cyclic=True)
    G.seam(D, G.bowed_line((-up_radius(nz), nz), (up_radius(nz), nz), bow=-0.06, n=8), M["ink"])
    G.stitches(D, [(0.0, nz + 0.25), (0.0, UP_Z1 - 0.5)], M["ink"], every=0.25, length=0.12)
    G.stroke(D, cone, M["ink"], O, cyclic=True)
    G.stroke(D, G.lumpy_ellipse(0.0, UP_Z1 + 0.12, 0.2, 0.17, n=16, seed=seed + 5), M["tip"], O, cyclic=True)
    # ONE porthole, off-centre (a single round window can never read as a pair of eyes)
    px, pz = 0.38, 7.25
    G.stroke(D, G.lumpy_ellipse(px, pz, 0.62, 0.62, n=30, seed=seed + 6), M["brass"], O, cyclic=True)
    G.stroke(D, G.lumpy_ellipse(px, pz, 0.44, 0.44, n=26, seed=seed + 7), M["port_glass"], 0.0, cyclic=True)
    G.stroke(D, G.lumpy_ellipse(px, pz, 0.44, 0.44, n=26, seed=seed + 7), M["ink"], I, cyclic=True)
    G.stroke(D, [(px + 0.30 * math.cos(a), pz + 0.30 * math.sin(a)) for a in [1.9 + 0.13 * k for k in range(8)]], M["glint"], I)
    G.rivets(D, [(px + 0.53 * math.cos(a), pz + 0.53 * math.sin(a)) for a in [2 * math.pi * k / 8 + 0.2 for k in range(8)]], M["ink"])
    # near fin: the right side fin in front of the hull
    up_fin(D, M, 1, p["fin"])


def draw_top_v2(d, M, pose=None, seed=0):
    """Space view, seen from above, nose to +x: hull, band, nose cone, three fins (two spread, one
    as a ridge), ONE porthole on the upper hull; no face (D-101)."""
    p = dict(sx=1.0, sz=1.0, fin=0.0, cz=4.0)
    p.update(pose or {})

    def TL(pts):
        return [(x * p["sx"], p["cz"] + z * p["sz"]) for x, z in pts]
    D = G.Xf(d, TL)
    for s in (-1, 1):
        a = p["fin"] * s
        bx = -4.3
        tipx, tipz = bx - 1.6 + 0.4 * math.sin(a), s * (radius_at(bx / L2) * 0.85 + 1.7 + 0.25 * math.cos(a))
        pts = G.bezier((bx + 1.3, s * 0.9), (bx + 0.2, s * 1.8), (tipx, tipz), n=10) + \
            G.bezier((tipx, tipz), (bx - 1.2, s * 1.5), (bx - 0.6, s * 0.9), n=10)[1:]
        G.stroke(D, pts, M["fin"], 0.0, cyclic=True)
        G.seam(D, G.bezier((bx + 0.9, s * 1.0), (bx - 0.4, s * 1.6), (tipx * 0.98, tipz * 0.9), n=6), M["ink"])
        G.stroke(D, pts, M["ink"], O, cyclic=True)
        G.stroke(D, G.lumpy_ellipse(tipx + 0.05, tipz - s * 0.15, 0.30, 0.24, n=18, seed=seed + 60 + s), M["tip"], O, cyclic=True)
    bell = [(-L2 + 0.3, 0.75), (-L2 - 0.9, 1.05), (-L2 - 0.9, -1.05), (-L2 + 0.3, -0.75)]
    G.stroke(D, bell, M["bell"], O, cyclic=True)
    n = 70
    top = [(L2 * (2 * i / n - 1), radius_at(2 * i / n - 1)) for i in range(n + 1)]
    bot = [(L2 * (2 * i / n - 1), -radius_at(2 * i / n - 1)) for i in range(n, -1, -1)]
    hull = top + bot[1:-1]
    G.stroke(D, hull, M["hull"], 0.0, cyclic=True)
    G.stroke(D, bot[1:-1] + [(x, -radius_at(x / L2) * 0.45) for x, _z in bot[1:-1]][::-1], M["hull_sh"], 0.0, cyclic=True)
    G.stroke(D, bot[1:-1] + [(x, -radius_at(x / L2) * 0.80) for x, _z in bot[1:-1]][::-1], M["hull_dp"], 0.0, cyclic=True)
    band = [(x, radius_at(x / L2)) for x in [-0.6 + 1.2 * i / 8 for i in range(9)]] + \
        [(x, -radius_at(x / L2)) for x in [0.6 - 1.2 * i / 8 for i in range(9)]]
    G.stroke(D, band, M["band"], I, cyclic=True)
    G.rivets(D, [(0.0, z) for z in (-1.0, -0.5, 0.0, 0.5, 1.0)], M["ink"])
    G.stroke(D, [(-3.8, 0.0), (-1.6, 0.0)], M["ink"], I)
    for xx in (-2.8, 2.2):
        r = radius_at(xx / L2)
        G.seam(D, G.bowed_line((xx, -r * 0.95), (xx, r * 0.95), bow=0.03, n=6), M["ink"])
    G.hatch(D, -1.8, -0.95, M["ink"], n=3, length=0.4, spacing=0.14, angle_deg=20, seed=seed + 2)
    G.stroke(D, hull, M["ink"], O, cyclic=True)
    ntop = [(x, radius_at(x / L2)) for x in [3.2 + (L2 - 3.2) * i / 20 for i in range(21)]]
    nbot = [(x, -radius_at(x / L2)) for x in [L2 - (L2 - 3.2) * i / 20 for i in range(21)]]
    seam = G.bezier((3.2, -radius_at(3.2 / L2)), (2.95, 0.0), (3.2, radius_at(3.2 / L2)), n=10)
    nose = ntop + nbot[1:] + seam[1:-1]
    G.stroke(D, nose, M["nose"], 0.0, cyclic=True)
    G.seam(D, seam, M["ink"])
    G.stroke(D, nose, M["ink"], O, cyclic=True)
    G.stroke(D, G.lumpy_ellipse(L2 + 0.1, 0.0, 0.18, 0.16, n=14, seed=seed + 5), M["tip"], O, cyclic=True)
    px, pz = 1.4, 0.45                                   # the one porthole, off the centre line
    G.stroke(D, G.lumpy_ellipse(px, pz, 0.5, 0.5, n=26, seed=seed + 6), M["brass"], O, cyclic=True)
    G.stroke(D, G.lumpy_ellipse(px, pz, 0.34, 0.34, n=22, seed=seed + 7), M["port_glass"], I, cyclic=True)
    G.rivets(D, [(px + 0.42 * math.cos(a), pz + 0.42 * math.sin(a)) for a in [2 * math.pi * k / 6 for k in range(6)]], M["ink"])


# ---- B-122 upright sheets (clips per the card; the puff loop is its own object)
TAU = 2 * math.pi
UP_IDLE = [dict(fin=0.15 * math.sin(TAU * i / 8), sz=1 + 0.015 * math.cos(TAU * i / 8), sx=1 - 0.008 * math.cos(TAU * i / 8))
           for i in range(8)]
UP_THRUST = [dict(sz=1.08 + 0.04 * math.sin(TAU * i / 8), sx=0.95 - 0.02 * math.sin(TAU * i / 8),
                  fin=-0.30 + 0.10 * math.sin(TAU * i / 8 - 1.2)) for i in range(8)]
UP_CUT = [dict(sx=s_x, sz=s_z, fin=fn) for s_x, s_z, fn in
          ((1.10, 0.86, 0.35), (1.07, 0.90, 0.25), (0.97, 1.04, -0.15), (1.01, 0.98, 0.08), (0.995, 1.005, -0.03), (1.0, 1.0, 0.0))]
UP_TILT_L = [dict(lean=l_, bend=b_, fin=f_) for l_, b_, f_ in ((-0.04, -0.1, 0.10), (-0.10, -0.25, 0.25), (-0.13, -0.3, 0.32), (-0.11, -0.25, 0.28))]
UP_TILT_R = [dict(lean=l_, bend=b_, fin=f_) for l_, b_, f_ in ((0.04, 0.1, -0.10), (0.10, 0.25, -0.25), (0.13, 0.3, -0.32), (0.11, 0.25, -0.28))]
UP_LAND = [dict(sz=s_z, sx=s_x, fin=fn) for s_z, s_x, fn in
           ((1.04, 0.97, -0.25), (1.02, 0.98, -0.15), (0.90, 1.06, 0.30), (0.86, 1.08, 0.40), (0.96, 1.02, 0.10),
            (1.02, 0.99, -0.08), (0.995, 1.0, 0.03), (1.0, 1.0, 0.0))]
TOP_UP_IDLE = [dict(fin=0.12 * math.sin(TAU * i / 8), sz=1 + 0.015 * math.cos(TAU * i / 8)) for i in range(8)]
TOP_UP_THRUST = [dict(sx=1.08 + 0.04 * math.sin(TAU * i / 8), sz=0.95 - 0.02 * math.sin(TAU * i / 8),
                      fin=-0.30 + 0.10 * math.sin(TAU * i / 8 - 1.2)) for i in range(8)]
UP_CLIPS = [("idle", UP_IDLE, "up"), ("thrust", UP_THRUST, "up"), ("cut", UP_CUT, "up"), ("tilt_left", UP_TILT_L, "up"),
            ("tilt_right", UP_TILT_R, "up"), ("land", UP_LAND, "up"), ("top_idle", TOP_UP_IDLE, "top"), ("top_thrust", TOP_UP_THRUST, "top")]
UP_SHEETS_OUT = os.path.join(os.path.dirname(HERE), "sources", "ships", "pilgrim_v3_up.blend")


def draw_up_puff(d, M, f, n=8):
    """Exhaust puff loop from the tail (pivot at the bell, top centre): puffs born at the bell,
    growing and drifting down, the oldest shrinking away; hot mustard core near the bell."""
    for k in range(3):
        t = ((f / n) + k / 3) % 1.0
        r = 0.16 + 0.40 * math.sin(math.pi * min(t * 1.2, 1.0))
        z = -0.2 - 1.15 * t
        x = 0.05 * math.sin(6.28 * t + k)
        if r > 0.06:
            G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.92, n=24, lump=0.07, seed=31 * k + f),
                     M["puff_hot"] if t < 0.22 else M["puff"], O, cyclic=True)
            if r > 0.25:
                G.seam(d, G.bezier((x - r * 0.5, z - r * 0.15), (x, z - r * 0.45), (x + r * 0.45, z - r * 0.2), n=6), M["ink"])


def build_sheets_up(out=UP_SHEETS_OUT):
    """B-122: every upright clip in one source (a marker per clip; the manifest's sheet entries
    pick theirs), the puff loop as its own object, per-frame sockets on the scene as json."""
    import json
    scene = G.new_scene()
    coll = G.collection("pilgrim")
    ob, gp = G.gp_object("pilgrim", coll)
    M = materials_v2(gp)
    layer = gp.layers.new("art")
    f = 1
    clips, sockets = [], {}
    for name, poses, kind in UP_CLIPS:
        for i, pose in enumerate(poses):
            if kind == "up":
                draw_upright(G.drawing(layer, f), M, pose, seed=7 * f)
                sockets[str(f)] = up_sockets(pose)
            else:
                draw_top_v2(G.drawing(layer, f), M, dict(pose, cz=0.0), seed=7 * f)
            f += 1
        clips.append((name, len(poses)))
    pc = G.collection("puff")
    pob, pgp = G.gp_object("puff", pc)
    PM = materials_v2(pgp)
    play = pgp.layers.new("art")
    for i in range(8):
        draw_up_puff(G.drawing(play, f + i), PM, i)
    clips.append(("puff", 8))
    G.mark_clips(scene, clips)
    scene["sockets"] = json.dumps(sockets)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


DESIGN_UP = [dict(kind="up"), dict(kind="up", tilt=-35, lift=3.4, puffs=0.7, fin=0.3, bend=-0.3),
             dict(kind="up", tilt=35, lift=3.4, puffs=0.7, fin=-0.3, bend=0.3),
             dict(kind="up", sx=0.90, sz=1.15, lift=6.5, puffs=1.0, fin=0.25),
             dict(kind="up", sx=1.08, sz=0.88, lift=3.4, puffs=0.15, fin=-0.25),
             dict(kind="top", cz=5.2)]


def build_design_up(out=OUT):
    """B-123 step 1: the upright, faceless Pilgrim design sheet (standing, tilted +-35 deg in
    flight, thrust stretch, cut squash, top view)."""
    scene = G.new_scene()
    coll = G.collection("pilgrim")
    ob, gp = G.gp_object("pilgrim", coll)
    M = materials_v2(gp)
    layer = gp.layers.new("art")
    for i, pose in enumerate(DESIGN_UP):
        pose = dict(pose)
        kind = pose.pop("kind")
        (draw_upright if kind == "up" else draw_top_v2)(G.drawing(layer, i + 1), M, pose, seed=10 * i)
    G.mark_clips(scene, [("design", len(DESIGN_UP))])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


if __name__ == "__main__":
    build_design_up()
