"""B-248 (D-200): a SPECIMEN SHEET of scenery in ART v6 - previews only, nothing exported.

docs/STYLE_V6.md 4a, scenery: THINGS, not shapes - a tree with a trunk that has weight, roots and tapering branches; a
rock turned by its planes; a broad-leaved plant painted leaf by leaf; a grass clump of single blades; a square metre of
covered ground - and THE BRUSH FOLLOWS THE FORM, under ONE light direction (from the upper right, a little toward us).

How the brush is made to follow form here: every specimen first gets a FORM FIELD, computed, not drawn -
  - a TUBE (a trunk, a branch, a root, a leaf): a centre line with a radius along it gives every pixel inside it its
    place ACROSS the form (v, -1 .. 1), its place ALONG it (s) and the axis's direction. Across-the-form is a cylinder's
    normal, so the light picks one of three or four flat values per pixel; and the brush is turned to lie across the
    tube and to curl with v, so bark strokes wrap the trunk (a leaf's strokes run along it instead);
  - a FACET (a rock's plane): a polygon with one value from its facing and one stroke direction down its slope;
  - a BALL (a crown's leaf cluster): a sphere's normal for the value, leaf dabs pointing out from its middle.
Then paint_v6's brush lays its dabs with those angles and values. No line is drawn anywhere; dark accents are paint.

  python -I build_specimens_v6.py <review png>     the lock-free sheet; each specimen at the game's size and at 2x
"""
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio  # noqa: E402
import cel_v6 as CEL  # noqa: E402
import paint_v6 as PT  # noqa: E402
import gp_raster as GR  # noqa: E402

rgb, lerp = PT.rgb, PT.lerp
Q = 2
LIGHT = np.array([0.58, -0.62, 0.53], np.float32)          # ONE light: from the upper right, a little toward the viewer (x right, y down, z out)
LIGHT /= np.linalg.norm(LIGHT)
GROUND = ("#7C7A55", "#96905F", "#B3A66E")                 # the earth under every specimen: three values of one olive ochre
BACK = "#CBD0BA"                                           # the sheet's quiet ground behind the specimens


def tube(P, pts, rad):
    """A curved, tapering form along a centre line (frame units), rad(s) its radius along it ->
    (mask, v: across it -1 .. 1, the axis's angle, s: along it 0 .. 1), per pixel."""
    q = P.Q
    pts = np.asarray(CEL.catmull([tuple(p) for p in pts], False, 6) if len(pts) >= 3 else pts, np.float32) * q
    seg = np.hypot(*np.diff(pts, axis=0).T)
    s = np.r_[0.0, np.cumsum(seg)]
    L = float(s[-1]) or 1e-6
    m = np.zeros((P.ph, P.pw), np.float32)
    v, ang, ss = np.zeros_like(m), np.zeros_like(m), np.zeros_like(m)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        r0, r1 = rad(s[i] / L) * q, rad(s[i + 1] / L) * q
        R = max(r0, r1) + 2
        x0, x1 = int(max(min(a[0], b[0]) - R, 0)), int(min(max(a[0], b[0]) + R + 1, P.pw))
        y0, y1 = int(max(min(a[1], b[1]) - R, 0)), int(min(max(a[1], b[1]) + R + 1, P.ph))
        if x1 <= x0 or y1 <= y0:
            continue
        X = np.arange(x0, x1, dtype=np.float32)[None, :] + 0.5
        Y = np.arange(y0, y1, dtype=np.float32)[:, None] + 0.5
        dx, dy = float(b[0] - a[0]), float(b[1] - a[1])
        t = np.clip(((X - a[0]) * dx + (Y - a[1]) * dy) / (dx * dx + dy * dy + 1e-9), 0, 1)
        px, py = X - (a[0] + t * dx), Y - (a[1] + t * dy)
        dist = np.hypot(px, py)
        r = r0 + (r1 - r0) * t
        inside = dist <= r
        sub = (slice(y0, y1), slice(x0, x1))
        m[sub] = np.where(inside, 1.0, m[sub])
        v[sub] = np.where(inside, np.sign(dx * py - dy * px) * dist / np.maximum(r, 1e-3), v[sub])
        ang[sub] = np.where(inside, math.atan2(dy, dx), ang[sub])
        ss[sub] = np.where(inside, (s[i] + t * seg[i]) / L, ss[sub])
    return m, v, ang, ss


def lit_tube(v, ang):
    """How much light a tube's surface takes, per pixel: a cylinder's normal (across it and out of the picture) on LIGHT."""
    side = -np.sin(ang) * LIGHT[0] + np.cos(ang) * LIGHT[1]                     # the across direction on the light
    return v * side + np.sqrt(np.clip(1 - v * v, 0, 1)) * LIGHT[2]


def values(lam, cuts, cols):
    """Flat values by the light: cols[0] below cuts[0], ... cols[-1] above cuts[-1]."""
    out = np.broadcast_to(cols[0], lam.shape + (3,)).astype(np.float32).copy()
    for c, col in zip(cuts, cols[1:]):
        out[lam > c] = col
    return out


def at(P, arr):
    """A brush-angle or colour lookup: the field's value at a frame point."""
    return lambda x, y: float(arr[P.pix(x, y)])


def ground(P, y0, seed_dabs=260):
    """The earth a specimen stands on: level dabs in three values, darker under the thing (its own shade is laid later)."""
    yy = P.yy
    m = np.clip((yy - y0) / 3.0 + 0.5, 0, 1) * np.ones((1, P.pw), np.float32)
    v = 0.5 + 0.9 * P.fbm(26, 2, sx=2.5)
    u = values(v, (0.38, 0.7), [rgb(c) for c in GROUND])
    P.lay(u, m)
    P.brush(u, m, seed_dabs, (4, 11), (2.4, 4.5), 0.0, 0.2, (0.6, 0.95), 0.05, 0.012, 3.0, 0.2)
    return m


def shade_pool(P, cx, cy, rx, ry, k=0.9):
    """The shadow a thing throws on the ground: violet-blue, soft, away from the light (down and to the left)."""
    P.glaze(P.blob(cx, cy, rx, ry, 0.6, 0.25), (0.62, 0.62, 0.80), k)


# ---------------------------------------------------------------- the specimens (frame units = px at the game's size)
def tree(seed=3):
    """A tree about 5 m tall: a trunk with weight (a flared foot), three roots, three tapering branches and twigs; bark
    strokes that WRAP the trunk; a crown of leaf clusters lit as balls, laid leaf by leaf."""
    P = PT.Painting(300, 366, seed, Q)
    P.img[:] = rgb(BACK)
    rng = P.rng
    ground(P, 334)
    shade_pool(P, 118, 342, 78, 9)
    bark = [rgb(c) for c in ("#3E3438", "#5A4B44", "#7C6A58", "#A08F74")]       # deep, shade, mid, lit
    leafs = [rgb(c) for c in ("#4E6A49", "#6C8B58", "#93AE6E", "#BACB8A")]

    def limb(pts, r0, r1, n_per=0.05, flare=0.0):
        m, v, ang, s = tube(P, pts, lambda t: r1 + (r0 - r1) * (1 - t) + flare * (1 - t) ** 4)
        lam = lit_tube(v, ang) + 0.10 * P.fine
        u = values(lam, (0.05, 0.36, 0.7), bark)
        P.lay(u, m)
        wrap = ang + math.pi / 2 + 0.55 * v                                     # across the limb, curling toward its edges
        P.brush(u, m, int(n_per * float(m.sum()) / (Q * Q)), (2.2, 2.2 + r0 * 0.55), (2.2, 4.0), at(P, wrap), 0.12, (0.7, 1.0), 0.06, 0.012, 3.6, 0.3, clip=m)   # (run 1: unclipped, the strokes stood out of the trunk as thorns)
        P.brush(bark[0], m * (v < -0.72), int(0.03 * float(m.sum()) / (Q * Q)), (2.0, 5.0), (2.5, 4.0), at(P, ang), 0.1, (0.6, 0.9), 0.04, 0.008, 4.0, 0.1, clip=m)   # a dark painted edge

    def cluster(cx, cy, r, dim=0.0, n_per=0.055):
        m = np.zeros((P.ph, P.pw), np.float32)
        for _ in range(4):
            m = np.maximum(m, P.blob(cx + rng.uniform(-0.4, 0.4) * r, cy + rng.uniform(-0.3, 0.3) * r, r * rng.uniform(0.7, 1.0), r * rng.uniform(0.55, 0.8), 0.10, 0.45))
        dx, dy = (P.xx - cx) / r, (P.yy - cy) / r
        lam = dx * LIGHT[0] + dy * LIGHT[1] + np.sqrt(np.clip(1 - dx * dx - dy * dy, 0, 1)) * LIGHT[2] + 0.25 * P.fine - dim
        u = values(lam, (0.05, 0.42, 0.78), leafs)
        P.lay(u, m)
        out = np.arctan2(P.yy - cy, P.xx - cx)                                  # every leaf points out from the cluster's middle
        P.brush(u, m, int(n_per * float(m.sum()) / (Q * Q)), (3.0, 5.6), (1.7, 2.6), at(P, out + np.zeros((P.ph, P.pw), np.float32)), 0.55, (0.8, 1.0), 0.05, 0.012, 4.6, 0.1)
    cluster(150, 104, 44, 0.45)                                                 # the crown's far side, in shade
    cluster(102, 132, 30, 0.4)
    for pts, r0, r1 in (([(140, 320), (114, 331), (94, 338)], 9, 2), ([(162, 322), (190, 332), (212, 338)], 9, 2), ([(151, 326), (150, 338)], 8, 4)):
        limb(pts, r0, r1)                                                       # the roots
    limb([(150, 334), (146, 290), (154, 240), (157, 196)], 13, 12, flare=13)    # the trunk, flared at its foot
    limb([(157, 200), (160, 152), (150, 112), (152, 82)], 9, 3)                 # three branches
    limb([(156, 204), (122, 152), (98, 114), (86, 86)], 10.5, 3)
    limb([(158, 200), (186, 152), (212, 120), (226, 94)], 10, 3)
    for pts in ([(122, 152), (100, 150), (80, 138)], [(186, 152), (208, 150), (232, 136)], [(160, 152), (176, 126), (184, 104)]):
        limb(pts, 4, 1.4, 0.08)                                                 # twigs
    for cx, cy, r in ((86, 82, 44), (126, 58, 48), (166, 52, 50), (208, 68, 46), (240, 100, 36), (62, 122, 30), (254, 134, 26), (190, 104, 28)):
        cluster(cx, cy, r)
    return P


def rock(seed=5):
    """A rock about 2 m wide: five planes, each one value from its facing and strokes that run down its own slope; lit
    edges where a plane meets the top; half sunk in the ground."""
    P = PT.Painting(190, 136, seed, Q)
    P.img[:] = rgb(BACK)
    rng = P.rng
    ground(P, 112, 150)
    shade_pool(P, 70, 116, 70, 8)
    cols = {k: rgb(c) for k, c in (("lit", "#CBC4B0"), ("half", "#ADA694"), ("mid", "#8C887F"), ("shade", "#6B6871"), ("deep", "#4F4D59"))}
    facets = ((("lit", 0.12), [(42, 60), (72, 42), (106, 38), (134, 52), (120, 72), (80, 64)]),                 # the top
              (("shade", 1.22), [(26, 86), (42, 60), (80, 64), (68, 116), (30, 116)]),                          # turned from the light
              (("mid", 1.5), [(80, 64), (120, 72), (112, 116), (68, 116)]),                                     # the front
              (("half", 1.92), [(120, 72), (134, 52), (152, 78), (156, 116), (112, 116)]))                      # toward the light
    for (tone, a), poly in facets:
        px, py = np.array([p[0] for p in poly], np.float32) * Q, np.array([p[1] for p in poly], np.float32) * Q
        m = GR._poly_mask(px, py, P.ph, P.pw).astype(np.float32)
        m = np.clip((P.box(m, 0.5) - 0.5 + 0.12 * P.fine) * 5 + 0.5, 0, 1)
        u = cols[tone] * (1 + 0.05 * P.fbm(18, 2))[..., None]
        P.lay(u.astype(np.float32), m)
        P.brush(u, m, int(0.05 * float(m.sum()) / (Q * Q)), (4, 10), (2.4, 4.2), a, 0.14, (0.6, 0.95), 0.05, 0.01, 3.4, 0.3, clip=m)
        if tone in ("shade", "mid"):                                            # a few cracks, as paint (run 1: on the lit top they read as holes)
            P.brush(cols["deep"], m * (P.fine < -0.3), int(0.005 * float(m.sum()) / (Q * Q)), (3, 7), (3.5, 5.5), a, 0.1, (0.5, 0.8), 0.04, 0.008, 4.0, 0.1, clip=m)
    for pts, tone in (([(42, 60), (80, 64), (120, 72), (134, 52)], "lit"), ([(80, 64), (72, 92), (68, 114)], "deep"), ([(120, 72), (116, 96), (112, 114)], "shade")):
        P.stroke(pts, 2.2, 1.2, cols[tone], 3.5)                                # the edges where planes meet: lit, or dark, as paint
    for x in rng.uniform(24, 160, 26):                                          # the earth and grass come up over its foot
        P.dab(x, 114 + rng.uniform(-2, 3), rng.uniform(4, 8), rng.uniform(1.6, 3), rng.normal(0, 0.3), rgb(GROUND[int(rng.integers(0, 3))]), 1.0, 3.5, 0.1)
    return P


def plant(seed=11):
    """A broad-leaved plant about 1.2 m tall, leaf by leaf: each leaf two or three values (the half toward the light,
    the half away, a darker tip), its strokes along its length, a midrib stroke, a dark painted edge on its shaded side."""
    P = PT.Painting(180, 156, seed, Q)
    P.img[:] = rgb(BACK)
    rng = P.rng
    ground(P, 136, 150)
    shade_pool(P, 66, 140, 62, 8)
    base = (90, 134)
    leaves = []
    for i in range(13):
        a = math.radians(-168 + 156 * i / 12 + rng.uniform(-6, 6))               # fanned from the left round to the right
        ln = rng.uniform(52, 82) * (0.75 + 0.25 * abs(math.sin(a)))
        droop = 0.45 * ln * (0.25 + abs(math.cos(a)))                            # a leaf leaning out bends over under its weight
        mid = (base[0] + math.cos(a) * ln * 0.55, base[1] + math.sin(a) * ln * 0.6)
        tip = (base[0] + math.cos(a) * ln, base[1] + math.sin(a) * ln + droop)
        leaves.append((rng.uniform(0, 1) + 0.6 * abs(math.cos(a)), [base, mid, tip], rng.uniform(9, 14)))
    for depth, pts, w in sorted(leaves, key=lambda t: t[0]):                     # the far leaves first
        near = min(1.0, depth / 1.2)
        m, v, ang, s = tube(P, pts, lambda t: 0.8 + w * math.sin(math.pi * min(1.0, t * 1.02) ** 0.75) ** 0.85)
        lam = v * (-np.sin(ang) * LIGHT[0] + np.cos(ang) * LIGHT[1])              # which half of the leaf faces the light
        dark, midc, lit = (lerp(rgb(c0), rgb(c1), near) for c0, c1 in (("#3F5A45", "#557A4C"), ("#56775A", "#7FA25F"), ("#7E9A6E", "#B5CC84")))
        u = values(lam + 0.1 * P.fine - 0.5 * (s > 0.86), (-0.12, 0.16), (dark, midc, lit))
        P.lay(u, m)
        P.brush(u, m, int(0.07 * float(m.sum()) / (Q * Q)), (3.5, 7.5), (2.8, 4.4), at(P, ang), 0.1, (0.7, 1.0), 0.04, 0.01, 4.2, 0.2, clip=m)
        P.brush(dark * 0.8, m * (np.abs(v) > 0.8) * (lam < 0), int(0.03 * float(m.sum()) / (Q * Q)), (2.5, 5), (3, 4.5), at(P, ang), 0.08, (0.6, 0.9), 0.03, 0.008, 4.4, 0.0, clip=m)
        rib = CEL.catmull([tuple(p) for p in pts], False, 6)
        P.stroke(rib[2:-3], 1.5, 0.6, lerp(lit, rgb("#DDE0A8"), 0.45) if near > 0.5 else dark * 0.85, 4.0)   # the midrib
    return P


def grass(seed=17):
    """A grass clump about 0.8 m tall: every blade its own tapering stroke, the far ones dark, the near ones lit, a few dry."""
    P = PT.Painting(120, 104, seed, Q)
    P.img[:] = rgb(BACK)
    rng = P.rng
    ground(P, 90, 90)
    shade_pool(P, 44, 93, 40, 6)
    blades = []
    for _ in range(46):
        a = -math.pi / 2 + rng.normal(0, 0.42)
        ln, bend = rng.uniform(26, 62), rng.normal(0.25, 0.25) * (1 if rng.random() < 0.7 else -1)
        x0 = 60 + rng.uniform(-11, 11)
        blades.append((rng.random(), x0, a, ln, bend))
    for depth, x0, a, ln, bend in sorted(blades):
        col = rgb("#C4B36C") if rng.random() < 0.1 else lerp(rgb("#4A6540"), rgb("#9DB868"), depth) * (1 + rng.normal(0, 0.05))
        m = (x0 + math.cos(a) * ln * 0.55, 91 + math.sin(a) * ln * 0.55)
        t = (x0 + math.cos(a + bend) * ln, 91 + math.sin(a + bend) * ln + 0.12 * ln * abs(bend) * 2)
        P.stroke([(x0, 92), m, t], 3.0, 0.7, np.clip(col, 0, 1), 5.0)
        if depth > 0.6:                                                         # the lit side of a near blade: a thin lighter stroke
            P.stroke([(x0 + 0.8, 90), (m[0] + 0.9, m[1])], 0.9, 0.5, np.clip(col * 1.18 + 0.03, 0, 1), 5.0)
    for x in rng.uniform(40, 82, 14):
        P.dab(x, 92 + rng.uniform(-1, 2), rng.uniform(3, 6), rng.uniform(1.5, 2.5), rng.normal(0, 0.3), rgb(GROUND[int(rng.integers(0, 3))]), 1.0, 3.5, 0.1)
    return P


def ground_m2(seed=23):
    """One square metre of covered ground (64 x 64 px at the game's size, painted with a margin): earth, fallen leaves each
    with a lit edge, twigs, two low plants, a half-buried stone, a pool of light across one corner and violet shade."""
    P = PT.Painting(96, 96, seed, Q)
    rng = P.rng
    v = 0.5 + 0.9 * P.fbm(20, 2)
    u = values(v, (0.36, 0.7), [rgb(c) for c in ("#6E6A4C", "#857E57", "#9E9466")])
    P.img[:] = u
    full = np.ones((P.ph, P.pw), np.float32)
    P.brush(u, full, 520, (3, 8), (2.0, 4.0), 0.0, 0.5, (0.6, 0.95), 0.05, 0.012, 3.2, 0.2)
    for cx, cy, a, sc in ((58, 60, 0.3, 1.0),):                                 # the stone: its top lit, its side in shade, earth over its foot
        for tone, poly in (("#6B6871", [(-13, 2), (-9, -6), (4, -8), (13, -2), (11, 7), (-10, 8)]), ("#C6BFAC", [(-9, -6), (4, -8), (13, -2), (3, 0), (-6, -1)])):
            px = np.array([cx + p[0] * sc for p in poly], np.float32) * Q
            py = np.array([cy + p[1] * sc for p in poly], np.float32) * Q
            m = GR._poly_mask(px, py, P.ph, P.pw).astype(np.float32)
            P.lay(rgb(tone), np.clip((P.box(m, 0.5) - 0.5 + 0.12 * P.fine) * 5 + 0.5, 0, 1))
        for x in rng.uniform(cx - 14, cx + 13, 12):
            P.dab(x, cy + 7 + rng.uniform(-1.5, 2), rng.uniform(3, 6), rng.uniform(1.4, 2.4), rng.normal(0, 0.3), u[P.pix(x, cy + 9)], 1.0, 3.5, 0.1)
    litter = [rgb(c) for c in ("#A8884E", "#8E6A42", "#B79A5C", "#7C8250", "#96593F")]
    for _ in range(70):                                                         # fallen leaves: a flat leaf, a lighter edge toward the light
        x, y, a = rng.uniform(0, 96), rng.uniform(0, 96), rng.uniform(0, math.pi)
        c = litter[int(rng.integers(0, len(litter)))] * (1 + rng.normal(0, 0.06))
        ln = rng.uniform(4.0, 6.5)
        P.dab(x, y, ln, ln * 0.42, a, np.clip(c, 0, 1), 1.0, 4.5, 0.0)
        P.dab(x + 0.9, y - 0.9, ln * 0.7, ln * 0.14, a, np.clip(c * 1.22 + 0.03, 0, 1), 0.9, 4.5, 0.0)
    for _ in range(5):                                                          # twigs
        x, y, a, ln = rng.uniform(8, 88), rng.uniform(8, 88), rng.uniform(0, math.pi), rng.uniform(10, 20)
        P.stroke([(x, y), (x + math.cos(a) * ln * 0.5, y + math.sin(a) * ln * 0.5 + 1), (x + math.cos(a) * ln, y + math.sin(a) * ln)], 1.3, 0.7, rgb("#4E4036"), 4.5)
    for cx, cy in ((24, 30), (70, 22)):                                         # two low plants: a few small leaves each
        for k in range(6):
            a = -math.pi * (0.1 + 0.8 * k / 5)
            P.dab(cx + math.cos(a) * 4.5, cy + math.sin(a) * 4.5, 4.6, 1.9, a, rgb("#5F8250") if k % 2 else rgb("#86A866"), 1.0, 4.6, 0.0)
    P.glaze(P.blob(70, 26, 40, 30, 0.7, 0.3), (1.14, 1.08, 0.88), 0.9)          # light across one corner, violet shade across the other
    P.glaze(P.blob(20, 74, 44, 32, 0.7, 0.3), (0.74, 0.76, 0.94), 0.8)
    return P


SPECIMENS = (("a tree", tree, None), ("a rock", rock, None), ("a broad-leaved plant", plant, None), ("a grass clump", grass, None),
             ("a square metre of ground", ground_m2, (16, 16, 80, 80)))


# ---------------------------------------------------------------- the sheet
def preview(out):
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    t0 = time.time()
    dd = os.path.join(os.path.dirname(out), "b248_specimens")
    os.makedirs(dd, exist_ok=True)
    paper = np.array(review.PAPER, np.float32)
    Wd = 1920
    made = []
    for name, fn, win in SPECIMENS:
        t1 = time.time()
        P = fn()
        big = np.clip(P.img, 0, 1)
        if win:
            big = big[win[1] * Q:win[3] * Q, win[0] * Q:win[2] * Q]
        small = big.reshape(big.shape[0] // Q, Q, big.shape[1] // Q, Q, 3).mean(axis=(1, 3))
        made.append((name, PT.tooth(small, 3), PT.tooth(big, 4), P.count, time.time() - t1))
        pngio.write_png(os.path.join(dd, name.split()[-1] + "_2x.png"), np.dstack([pngio.to_u8(made[-1][2]), np.full(big.shape[:2], 255, np.uint8)]))

    def head(text, h=22):
        hd = np.tile(paper, (h, Wd, 1)).astype(np.float32)
        review._label(hd, text, 6, 5, scale=1)
        return hd

    def row(idx, pad=12):
        hmax = max(m[idx].shape[0] for m in made)
        r = np.tile(paper, (hmax + 2 * pad, Wd, 1)).astype(np.float32)
        x = pad
        for m in made:
            im = m[idx]
            r[pad + hmax - im.shape[0]:pad + hmax, x:x + im.shape[1]] = im[:, :max(0, Wd - x)]
            x += im.shape[1] + 24
        return r
    rows = [head("B-248 (D-200): SCENERY SPECIMENS in ART v6 - things, not shapes; the brush follows the form (a computed form field); ONE light, from the upper right; no drawn line (dark accents are paint). PREVIEW, nothing exported", 26),
            head("AT THE GAME'S SIZE (64 px per metre): " + " | ".join(m[0] for m in made)), row(1),
            head("AT 2x (the paintings as they were made; nothing enlarged)"), row(2)]
    lines = ["WHAT EACH COST: " + "; ".join(f"{m[0]} {m[3]} dabs, {m[4]:.1f} s" for m in made),
             f"this run: {time.time() - t0:.0f} s. Files in b248_specimens/: " + ", ".join(m[0].split()[-1] + "_2x.png" for m in made)]
    foot = np.tile(paper, (24 + 16 * len(lines), Wd, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-248 scenery specimens preview (lock-free, numpy; nothing exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    preview(sys.argv[1])
