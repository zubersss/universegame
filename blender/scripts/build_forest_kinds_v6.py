"""B-248 (D-200): FOUR MORE FOREST KINDS in ART v6 - as specimens on one sheet, and as plants the frame can place.

LEAD 11-10 08:5x, the first four of the plan in coordination/reports/blender/v6_earth_kinds.md:
  the EMERGENT TREE (a tall pale trunk rising clear, buttress roots as thin planes at its foot, a small high crown);
  the FAN PALM (a ringed, leaning trunk; pleated fans on stalks, every blade of a fan its own stroke);
  the BAMBOO CLUMP (jointed canes that taper, a ring at every node, sprays of small lance leaves);
  the BROAD-LEAVED UNDERSTOREY in two more leaf shapes (a PADDLE leaf with side veins and a notched edge; a HEART
  leaf on its own stalk).
Painted by the form-following brush of build_specimens_v6 (tube / facet / ball) under the same ONE light; no drawn
line. Every kind is written about its own foot (0, 0) in px at 64 px per metre and painted through a placement
(tf, s) - where it stands and how large - so the specimen sheet and build_forest_frame_v6 use the same rules; each
part is painted inside its own window of the picture. pale = how far the haze has taken it (distance).

  python -I build_forest_kinds_v6.py <review png>     the lock-free specimen sheet (the game's size and 2x)
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
import build_specimens_v6 as SP  # noqa: E402

rgb, lerp = PT.rgb, PT.lerp
Q, LIGHT = SP.Q, SP.LIGHT
HAZE = rgb("#BFCBBE")


def hz(cols, pale, dark=0.0):
    return [lerp(rgb(c) if isinstance(c, str) else c, HAZE, pale) * (1 - 0.35 * dark) for c in cols]


def win_of(m, pad=0):
    rows, cols = np.flatnonzero(m.any(axis=1)), np.flatnonzero(m.any(axis=0))
    if not len(rows):
        return None
    return (slice(max(int(rows[0]) - pad, 0), int(rows[-1]) + 1 + pad), slice(max(int(cols[0]) - pad, 0), int(cols[-1]) + 1 + pad))


def into(P, w, u, m):
    P.img[w] = P.img[w] * (1 - m[..., None]) + u * m[..., None]


def flipped(tf):
    return tf(1, 0)[0] < tf(0, 0)[0]


def limb(P, pts, r0, r1, cols, flare=0.0, n_per=0.05, rings=0.0, s=1.0):
    """A trunk, bough or cane (frame px): lit as a cylinder, strokes laid across it; rings: a dark ring every `rings` px."""
    m, v, ang, _s = SP.tube(P, pts, lambda t: r1 + (r0 - r1) * (1 - t) + flare * (1 - t) ** 4)
    w = win_of(m)
    if w is None:
        return None
    mw = m[w]
    u = SP.values(SP.lit_tube(v[w], ang[w]) + 0.10 * P.fine[w], (0.05, 0.36, 0.7), cols)
    into(P, w, u, mw)
    k = max(s, 0.4)
    area = float(mw.sum()) / (Q * Q) / (k * k)
    P.brush(u, mw, int(n_per * area), (2.0 * k, (2.0 + r0 / k * 0.55) * k), (2.2, 4.0), SP.at(P, ang + math.pi / 2 + 0.55 * v), 0.12, (0.7, 1.0), 0.06, 0.012, 3.6, 0.3, clip=m, win=w)
    P.brush(cols[0], mw * (v[w] < -0.72), int(0.03 * area), (2.0 * k, 5.0 * k), (2.5, 4.0), SP.at(P, ang), 0.1, (0.6, 0.9), 0.04, 0.008, 4.0, 0.1, clip=m, win=w)
    if rings:
        ctr = CEL.catmull([tuple(p) for p in pts], False, 8) if len(pts) >= 3 else [tuple(p) for p in pts]
        ln = sum(math.hypot(ctr[i + 1][0] - ctr[i][0], ctr[i + 1][1] - ctr[i][1]) for i in range(len(ctr) - 1)) or 1e-6
        d, nxt = 0.0, rings * 0.6
        for i in range(len(ctr) - 1):
            (x0, y0), (x1, y1) = ctr[i], ctr[i + 1]
            step = math.hypot(x1 - x0, y1 - y0)
            while nxt <= d + step and step > 0:
                t = (nxt - d) / step
                x, y, a = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, math.atan2(y1 - y0, x1 - x0) + math.pi / 2
                r = r1 + (r0 - r1) * (1 - nxt / ln)
                P.dab(x, y, r * 1.05, max(0.6, 0.9 * s), a, cols[0], 1.0, 4.5, 0.0, clip=m)
                P.dab(x + 1.6 * s * math.cos(a - math.pi / 2), y + 1.6 * s * math.sin(a - math.pi / 2), r * 0.9, max(0.6, 0.8 * s), a, cols[3], 0.8, 4.0, 0.0, clip=m)
                nxt += rings * P.rng.uniform(0.85, 1.15)
            d += step
    return m


def cluster(P, cx, cy, r, cols, dim=0.0, n_per=0.055, s=1.0):
    """A leaf cluster (frame px) lit as a ball, laid leaf by leaf, with leaves past its edge."""
    rng = P.rng
    y0, y1 = max(int((cy - 2 * r) * Q), 0), min(int((cy + 2 * r) * Q) + 1, P.ph)
    x0, x1 = max(int((cx - 2 * r) * Q), 0), min(int((cx + 2 * r) * Q) + 1, P.pw)
    if y1 <= y0 or x1 <= x0:
        return
    w = (slice(y0, y1), slice(x0, x1))
    m = np.zeros((y1 - y0, x1 - x0), np.float32)
    for _ in range(4):
        m = np.maximum(m, P.blob(cx + rng.uniform(-0.4, 0.4) * r, cy + rng.uniform(-0.3, 0.3) * r, r * rng.uniform(0.7, 1.0), r * rng.uniform(0.55, 0.8), 0.10, 0.45)[w])
    if not m.any():
        return
    dx, dy = (P.xx[:, w[1]] - cx) / r, (P.yy[w[0]] - cy) / r
    lam = dx * LIGHT[0] + dy * LIGHT[1] + np.sqrt(np.clip(1 - dx * dx - dy * dy, 0, 1)) * LIGHT[2] + 0.25 * P.fine[w] - dim
    u = SP.values(lam, (0.05, 0.42, 0.78), cols)
    into(P, w, u, m)
    out = lambda x, y: math.atan2(y - cy, x - cx)                               # noqa: E731
    k = max(s, 0.6)
    area = float(m.sum()) / (Q * Q) / (k * k)
    P.brush(u, m, int(n_per * area), (3.0 * k, 5.6 * k), (1.7, 2.6), out, 0.55, (0.8, 1.0), 0.05, 0.012, 4.6, 0.1, win=w)
    P.brush(u, (PT.box(m, int(round(3 * k * Q))) > 0.03) * (m < 0.5), int(0.02 * area), (3.0 * k, 5.6 * k), (1.9, 2.8), out, 0.7, (0.85, 1.0), 0.05, 0.012, 5.0, 0.0, win=w)


def facet(P, poly, col, ang, s=1.0):
    """A flat plane (frame px): one value, strokes down its slope, a brushed edge."""
    full = GR._poly_mask(np.array([p[0] for p in poly], np.float32) * Q, np.array([p[1] for p in poly], np.float32) * Q, P.ph, P.pw).astype(np.float32)
    w = win_of(full, 3)
    if w is None:
        return
    m = np.clip((PT.box(full[w], 1) - 0.5 + 0.1 * P.fine[w]) * 5 + 0.5, 0, 1)
    full[w] = m
    into(P, w, col, m)
    k = max(s, 0.5)
    P.brush(col, m, int(0.05 * float(m.sum()) / (Q * Q) / (k * k)), (4 * k, 9 * k), (2.6, 4.2), ang, 0.12, (0.7, 1.0), 0.06, 0.012, 3.6, 0.3, clip=full, win=w)


def leaf(P, pts, rad, cols, near=1.0, veins=0, tears=0, vein_a=1.05, s=1.0):
    """One broad leaf along a midrib (frame px; rad(t) its half-width): the half toward the light, the half away, a darker
    tip; strokes along it; a midrib; side veins as lighter strokes; tears as thin wedges cut out of its edge."""
    m, v, ang, sa = SP.tube(P, pts, rad)
    w = win_of(m)
    if w is None:
        return
    rib = CEL.catmull([tuple(p) for p in pts], False, 8)
    n = len(rib)
    for k in range(tears):
        i = min(max(int(n * (0.2 + 0.62 * k / max(tears - 1, 1))), 1), n - 2)
        (x0, y0), (x1, y1) = rib[i - 1], rib[i + 1]
        a = math.atan2(y1 - y0, x1 - x0)
        r = rad(i / (n - 1))
        b = a + (1 if k % 2 else -1) * vein_a
        apex = (rib[i][0] + math.cos(b) * r * 0.5, rib[i][1] + math.sin(b) * r * 0.5)
        e = (rib[i][0] + math.cos(b) * r * 1.3, rib[i][1] + math.sin(b) * r * 1.3)
        wedge = [apex, (e[0] - math.cos(a) * 2.0 * s, e[1] - math.sin(a) * 2.0 * s), (e[0] + math.cos(a) * 2.0 * s, e[1] + math.sin(a) * 2.0 * s)]
        m = m * (1 - GR._poly_mask(np.array([p[0] for p in wedge], np.float32) * Q, np.array([p[1] for p in wedge], np.float32) * Q, P.ph, P.pw))
    m = m.astype(np.float32)
    mw, vw, aw = m[w], v[w], ang[w]
    lam = vw * (-np.sin(aw) * LIGHT[0] + np.cos(aw) * LIGHT[1])
    u = SP.values(lam + 0.1 * P.fine[w] - 0.5 * (sa[w] > 0.9), (-0.12, 0.16), cols)
    into(P, w, u, mw)
    k = max(s, 0.6)
    area = float(mw.sum()) / (Q * Q) / (k * k)
    P.brush(u, mw, int(0.07 * area), (3.5 * k, 7.5 * k), (2.8, 4.4), SP.at(P, ang), 0.1, (0.7, 1.0), 0.04, 0.01, 4.2, 0.2, clip=m, win=w)
    P.brush(cols[0] * 0.8, mw * (np.abs(vw) > 0.8) * (lam < 0), int(0.03 * area), (2.5 * k, 5 * k), (3, 4.5), SP.at(P, ang), 0.08, (0.6, 0.9), 0.03, 0.008, 4.4, 0.0, clip=m, win=w)
    for j in range(veins):
        i = min(max(int(n * (0.14 + 0.72 * j / max(veins - 1, 1))), 1), n - 2)
        (x0, y0), (x1, y1) = rib[i - 1], rib[i + 1]
        a = math.atan2(y1 - y0, x1 - x0)
        r = rad(i / (n - 1))
        for side in (-1, 1):
            b = a + side * vein_a
            P.stroke([rib[i], (rib[i][0] + math.cos(b) * r * 0.8, rib[i][1] + math.sin(b) * r * 0.8)], 0.9 * k, 0.5 * k, np.clip(cols[2] * 1.1 + 0.03, 0, 1), 4.0)
    P.stroke(rib[2:-3], 1.7 * k, 0.6 * k, lerp(cols[2], rgb("#DDE0A8"), 0.45) if near > 0.5 else cols[0] * 0.85, 4.0)


GREENS = (("#3F5A45", "#557A4C"), ("#56775A", "#7FA25F"), ("#7E9A6E", "#B5CC84"))


def greens(near, pale=0.0, dark=0.0):
    return hz([lerp(rgb(c0), rgb(c1), near) for c0, c1 in GREENS], pale, dark)


# ---------------------------------------------------------------- the kinds, each about its own foot (0, 0); y up is negative
def emergent_into(P, tf, s=1.0, pale=0.0, trunk_pale=None):
    """An emergent tree about 7.5 m tall: a pale trunk rising clear, four buttress roots as thin planes, a small high crown."""
    bark = hz(("#57504C", "#7C7468", "#A69C88", "#CFC5AC"), pale if trunk_pale is None else trunk_pale)   # (a far one: its trunk may be paler than its crown)
    leafs = hz(("#4E6A49", "#6C8B58", "#93AE6E", "#BACB8A"), pale)
    T = lambda pts: [tf(*p) for p in pts]                                      # noqa: E731
    fl = flipped(tf)
    cluster(P, *tf(-4, -392), 36 * s, leafs, 0.45, s=s)
    for sx, wd, h, tone, a in ((-1, 54, 88, 1, 1.15), (1, 50, 80, 3, 1.95), (-1, 26, 54, 0, 1.3), (1, 24, 46, 2, 1.8)):
        poly = T([(sx * 9, -h), (sx * 9 + sx * wd * 0.45, -h * 0.34), (sx * 9 + sx * wd, 2), (sx * 9, 2)])
        lit = (sx > 0) != fl
        facet(P, poly, bark[tone ^ 2 if fl else tone], math.pi - a if fl else a, s)       # mirrored: the lit and the dark sides change places
        P.stroke(poly[:3], 2.0 * s, 1.2 * s, bark[3] if lit else bark[0], 3.8)
    limb(P, T([(0, 2), (-3, -106), (3, -226), (-2, -336)]), 12.5 * s, 7.5 * s, bark, flare=4 * s, n_per=0.045, s=s)
    for pts, r0, r1 in (([(-2, -330), (-20, -364), (-44, -386)], 6, 2.2), ([(-1, -334), (12, -374), (38, -394)], 6, 2.2), ([(-2, -336), (-2, -378), (-8, -410)], 5.5, 2)):
        limb(P, T(pts), r0 * s, r1 * s, bark, s=s)
    for cx, cy, r in ((-46, -394, 30), (-6, -420, 34), (40, -402, 30), (-26, -368, 22), (22, -370, 22)):
        cluster(P, *tf(cx, cy), r * s, leafs, s=s)


def fan_palm_into(P, tf, s=1.0, pale=0.0, dark=0.0):
    """A fan palm about 4.5 m tall: a ringed, leaning trunk; nine pleated fans on stalks, every blade its own stroke."""
    rng = P.rng
    bark = hz(("#4A3F3C", "#6A5A4C", "#8C7A62", "#AE9C7C"), pale, dark)
    top = (8, -190)
    fans = []
    for i in range(9):
        a = math.radians(-178 + 176 * i / 8 + rng.uniform(-7, 7))
        fans.append((abs(math.cos(a)) + rng.uniform(0, 0.3), a, rng.uniform(26, 40), rng.uniform(30, 40)))
    for depth, a, stalk, ln in sorted(fans, reverse=True):
        g = greens(1.0 - min(1.0, depth / 1.3) * 0.7, pale, dark)
        c = (top[0] + math.cos(a) * stalk, top[1] + math.sin(a) * stalk + 0.45 * stalk * abs(math.cos(a)))
        P.stroke([tf(*top), tf((top[0] + c[0]) / 2, (top[1] + c[1]) / 2 - 3), tf(*c)], 2.0 * s, 1.2 * s, g[0] * 0.8, 4.0)
        fa = math.atan2(c[1] - top[1], c[0] - top[0])
        for j in range(13):
            b = fa - math.radians(80) + math.radians(160) * j / 12
            L = ln * (0.72 + 0.28 * math.sin(math.pi * j / 12))
            tip = (c[0] + math.cos(b) * L, c[1] + math.sin(b) * L + 0.1 * L * abs(math.cos(b)))
            p0, p1 = tf(*c), tf(*tip)
            lit = ((p1[0] - p0[0]) * LIGHT[0] + (p1[1] - p0[1]) * LIGHT[1]) > -0.1 * L * s
            col = (g[2] if lit else g[1]) if j % 2 == 0 else (g[1] if lit else g[0])
            P.stroke([p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), p1], 4.2 * s, 0.8 * s, np.clip(col * (1 + rng.normal(0, 0.04)), 0, 1), 4.6)
    limb(P, [tf(*p) for p in ((0, 2), (8, -68), (-2, -132), top)], 8.5 * s, 5.5 * s, bark, flare=4 * s, n_per=0.07, rings=11 * s, s=s)


def bamboo_into(P, tf, s=1.0, pale=0.0, n=9, dark=0.0):
    """A bamboo clump about 6 m tall: canes that taper, a ring at every node, sprays of small lance leaves."""
    rng = P.rng
    canes = []
    for _ in range(n):
        canes.append((rng.random(), rng.uniform(-22, 26), rng.uniform(250, 356), rng.uniform(-0.16, 0.2), rng.uniform(3.4, 4.8)))
    for depth, x0, h, lean, r0 in sorted(canes):
        k = 0.45 + 0.55 * depth
        cols = hz([lerp(rgb("#8E9A80"), rgb(c), k) for c in ("#5C6B3C", "#86924E", "#B4BA6C", "#D2D08A")], pale, dark)
        g = greens(depth, pale, dark)
        pts = [tf(*p) for p in ((x0, 2), (x0 + lean * h * 0.3, -h * 0.4), (x0 + lean * h * 0.75, -h * 0.75), (x0 + lean * h * 1.25, -h))]
        limb(P, pts, r0 * s, 1.4 * s, cols, n_per=0.09, rings=rng.uniform(24, 32) * s, s=s)
        ctr = CEL.catmull(pts, False, 8)
        for i in range(int(len(ctr) * 0.45), len(ctr) - 1, 3):
            x, y = ctr[i]
            side = 1 if rng.random() < 0.5 else -1
            for _j in range(int(rng.integers(3, 6))):
                b = math.radians(rng.uniform(10, 70)) * side + (0 if side > 0 else math.pi)
                L = rng.uniform(14, 22) * s
                tip = (x + math.cos(b) * L, y + abs(math.sin(b)) * L * 0.9)
                P.stroke([(x, y), ((x + tip[0]) / 2, (y + tip[1]) / 2 - 1.5 * s), tip], 3.2 * s, 0.6 * s, np.clip((g[2] if math.cos(b) * LIGHT[0] > 0 else g[1]) * (1 + rng.normal(0, 0.05)), 0, 1), 4.8)


def paddle_into(P, tf, s=1.0, pale=0.0, dark=0.0, n=7):
    """A paddle plant: long leaves with a strong midrib, side veins and a notched (torn) edge."""
    rng, leaves = P.rng, []
    for i in range(n):
        a = math.radians(-150 + 120 * i / (n - 1) + rng.uniform(-6, 6))
        ln = rng.uniform(96, 128) * (0.78 + 0.22 * abs(math.sin(a)))
        droop = 0.5 * ln * abs(math.cos(a)) ** 1.5
        leaves.append((rng.uniform(0, 1) + 0.5 * abs(math.cos(a)), [tf(0, -2), tf(math.cos(a) * ln * 0.5, math.sin(a) * ln * 0.6), tf(math.cos(a) * ln, math.sin(a) * ln + droop)], rng.uniform(13, 17) * s))
    for depth, pts, w in sorted(leaves, key=lambda t: t[0]):
        near = min(1.0, depth / 1.2)
        leaf(P, pts, lambda t, w=w: 1.2 * s + w * math.sin(math.pi * min(1.0, 0.08 + t * 0.94) ** 0.9) ** 0.55, greens(near, pale, dark), near, veins=6, tears=4, s=s)


def heart_into(P, tf, s=1.0, pale=0.0, dark=0.0, n=8):
    """A heart-leaf plant: each leaf on its own stalk, broad at the stalk and pointed at the tip, veins fanning from the joint."""
    rng, leaves = P.rng, []
    for i in range(n):
        a = math.radians(-160 + 140 * i / (n - 1) + rng.uniform(-8, 8))
        leaves.append((rng.uniform(0, 1) + 0.5 * abs(math.cos(a)), a, rng.uniform(40, 74) * (0.7 + 0.3 * abs(math.sin(a))), rng.uniform(15, 21)))
    for depth, a, st, w in sorted(leaves):
        near = min(1.0, depth / 1.2)
        g = greens(near, pale, dark)
        j = (math.cos(a) * st, math.sin(a) * st)
        P.stroke([tf(0, 0), tf(j[0] / 2 + 3 * math.cos(a + 1.57), j[1] / 2 + 3 * math.sin(a + 1.57)), tf(*j)], 2.2 * s, 1.4 * s, g[0] * 0.9, 4.0)
        b = a + rng.uniform(0.5, 0.9) * (1 if math.cos(a) > 0 else -1) + (0.6 if abs(math.cos(a)) < 0.3 else 0.0)
        ln = w * 2.5
        tip = (j[0] + math.cos(b) * ln, j[1] + math.sin(b) * ln + 0.25 * ln)
        back = (j[0] - math.cos(b) * w * 0.35, j[1] - math.sin(b) * w * 0.35)
        leaf(P, [tf(*back), tf(*j), tf((j[0] + tip[0]) / 2, (j[1] + tip[1]) / 2 - 2), tf(*tip)],
             lambda t, w=w: 0.8 * s + w * s * (math.sin(math.pi * min(1.0, 0.1 + t * 0.9) ** 0.45) ** 0.9), g, near, veins=4, vein_a=0.75, s=s)


# ---------------------------------------------------------------- ferns (written 11-10 10:0x, UNRUN: the plan's kind 4)
FERN = ("#476244", "#66894F", "#9DB96A")


def frond(P, tf, s, base, a, ln, droop, cols, n=13, taper=False, wide=0.22):
    """One frond (its own px about the plant's foot): a rachis that arcs out and droops, a leaflet down each side at
    every step, each its own dab. The frame's Scene.frond made placeable; the light is read from the PLACED rachis.
    taper: a fern's frond - broad at its base and narrowing to the tip, thinner leaflets (a palm's is widest midway)."""
    rng = P.rng
    pts = [base, (base[0] + math.cos(a) * ln * 0.5, base[1] + math.sin(a) * ln * 0.55), (base[0] + math.cos(a) * ln, base[1] + math.sin(a) * ln + droop)]
    rib = CEL.catmull(pts, False, n)
    p0, p1 = tf(*rib[0]), tf(*rib[-1])
    lit = ((p1[0] - p0[0]) * LIGHT[0] + (p1[1] - p0[1]) * LIGHT[1]) > 0
    fl = flipped(tf)
    for i in range(2, len(rib) - 1):
        (x0, y0), (x1, y1) = rib[i - 1], rib[i]
        t = i / len(rib)
        ang = math.atan2(y1 - y0, x1 - x0)
        if taper and t < 0.14:
            continue                                                            # a bare stalk at the crown's heart (run 2: the broad bases merged into one green mass)
        ll = (ln * 0.2 * (1 - t) ** 0.7 + 2) if taper else (ln * wide * math.sin(math.pi * min(1.0, t * 1.05)) ** 0.6 + 2)   # wide: the leaflet's length as a part of the frond's
        for side in (-1, 1):
            b = ang + side * 1.0
            c = cols[2] if (lit and side < 0) else cols[1] if lit else cols[0] if side > 0 else cols[1]
            px, py = tf(x1 + math.cos(b) * ll * 0.5, y1 + math.sin(b) * ll * 0.5)
            P.dab(px, py, ll * 0.5 * s, max(0.9, ll * (0.085 if taper else 0.12) * s), math.pi - b if fl else b, np.clip(c * (1 + rng.normal(0, 0.05)), 0, 1), 1.0, 4.6, 0.0)
    P.stroke([tf(*p) for p in rib], 1.6 * s, 0.6 * s, cols[0] * 0.85, 4.0)


def fern_into(P, tf, s=1.0, pale=0.0, dark=0.0, n=9):
    """A ground fern about 0.8 m: fronds from one base, the outer ones first (the frame's Scene.fern, placeable)."""
    rng, cols = P.rng, hz(FERN, pale, dark)
    for i in sorted(range(n), key=lambda i: abs(i - (n - 1) / 2), reverse=True):
        a = math.radians(-160 + 140 * i / (n - 1) + rng.uniform(-6, 6))
        ln = rng.uniform(34, 52)
        frond(P, tf, s, (0, 0), a, ln, ln * (0.25 + 0.5 * abs(math.cos(a))), cols)


def tree_fern_into(P, tf, s=1.0, pale=0.0, dark=0.0, n=13):
    """A tree fern about 3 m tall: a short shaggy trunk ringed with old frond bases, dead fronds hanging against it, a
    wide crown of long arching fronds (the far ones behind the trunk, darker), two young croziers at its heart."""
    rng = P.rng
    bark = hz(("#3A302C", "#54463A", "#746350", "#978466"), pale, dark)
    cols, back = hz(FERN, pale, dark), hz(FERN, pale, min(1.0, dark + 0.5))
    dead = hz(("#5E4C38", "#7A6548", "#94805A"), pale, dark)                    # (run 3: pale, in two matched pairs they hung like a doll's legs)
    top = (5, -150)
    fr = []
    for i in range(n):
        a = math.radians(-176 + 172 * i / (n - 1) + rng.uniform(-6, 6))
        fr.append((a, rng.uniform(84, 110)))
    # (Run 1: a weeping palm - the fronds hung halfway down the trunk, the far ones all on one side, a ringed palm's
    # trunk. Now: the fronds arch out and only their tips droop; far and near fronds alternate round the crown; each
    # frond tapers from a broad base; the trunk is fibrous, with old frond scars instead of rings.)
    for a, ln in fr[1::2]:                                                      # every other frond is on the far side, behind the trunk
        frond(P, tf, s, top, a, ln, ln * (0.12 + 0.42 * abs(math.cos(a))), back, 22, taper=True)
    trunk = ((0, 2), (-5, -52), (3, -104), top)
    mt = limb(P, [tf(*p) for p in trunk], 9 * s, 7 * s, bark, flare=3 * s, n_per=0.08, s=s)
    if mt is not None:
        ctr = CEL.catmull(list(trunk), False, 8)
        for _ in range(30):                                                     # old frond scars: small slanting marks, dark and pale
            i = int(rng.integers(1, len(ctr) - 1))
            p0, p1 = tf(*ctr[i - 1]), tf(*ctr[i])
            along = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            off = rng.uniform(-6, 6) * s
            P.dab(p1[0] - math.sin(along) * off, p1[1] + math.cos(along) * off, 3.2 * s, 1.5 * s, along + rng.choice((-0.7, 0.7)),
                  bark[0] if rng.random() < 0.6 else bark[3], 0.9, 4.2, 0.1, clip=mt)
    for i in range(7):                                                          # dead fronds hang down against the trunk: uneven, close to it
        side = 1 if i % 3 else -1
        x0, y0, ln = top[0] + side * rng.uniform(1, 5), top[1] + rng.uniform(3, 16), rng.uniform(18, 50)
        P.stroke([tf(x0, y0), tf(x0 + side * rng.uniform(4, 8), y0 + ln * 0.45), tf(x0 + side * rng.uniform(4, 10), y0 + ln)], 2.2 * s, 0.8 * s, dead[int(rng.integers(0, 3))], 4.2)
    for a, ln in fr[0::2]:                                                      # the near fronds
        frond(P, tf, s, top, a, ln, ln * (0.12 + 0.42 * abs(math.cos(a))), cols, 22, taper=True)
    for d, h in ((1, rng.uniform(16, 22)), (-1, rng.uniform(12, 17))):          # young fronds, still curled
        tx, ty = top
        P.stroke([tf(tx, ty), tf(tx + d * 2, ty - h * 0.6), tf(tx + d * 5, ty - h), tf(tx + d * 9, ty - h * 0.82), tf(tx + d * 7, ty - h * 0.62)], 2.2 * s, 1.2 * s, cols[1], 4.4)


# ---------------------------------------------------------------- the specimen sheet
def canvas(w, h, seed, gy, shade):
    P = PT.Painting(w, h, seed, Q)
    P.img[:] = rgb(SP.BACK)
    SP.ground(P, gy, int(w * 0.8))
    SP.shade_pool(P, shade[0], gy + 6, shade[1], shade[2])
    return P


def at(ox, oy):
    return lambda x, y: (ox + x, oy + y)


def emergent(seed=41):
    P = canvas(270, 520, seed, 486, (112, 84, 9))
    emergent_into(P, at(138, 486))
    return P


def fan_palm(seed=43):
    P = canvas(240, 330, seed, 300, (96, 60, 7))
    fan_palm_into(P, at(118, 300))
    return P


def bamboo(seed=53):
    P = canvas(230, 410, seed, 380, (100, 70, 8))
    bamboo_into(P, at(102, 380))
    return P


def understorey(seed=47):
    P = canvas(360, 210, seed, 184, (120, 150, 9))
    paddle_into(P, at(100, 184))
    heart_into(P, at(262, 182))
    return P


def tree_fern(seed=59):                                    # UNRUN; shown on build_plains_kinds_v6's sheet, not in KINDS (this sheet is accepted as it is)
    P = canvas(250, 270, seed, 244, (108, 92, 8))
    tree_fern_into(P, at(120, 244))
    return P


KINDS = (("an emergent tree", emergent), ("a fan palm", fan_palm), ("a bamboo clump", bamboo), ("two understorey plants", understorey))


def preview(out):
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    t0 = time.time()
    dd = os.path.join(os.path.dirname(out), "b248_kinds")
    os.makedirs(dd, exist_ok=True)
    paper = np.array(review.PAPER, np.float32)
    Wd = 1920
    made = []
    for name, fn in KINDS:
        t1 = time.time()
        P = fn()
        big = np.clip(P.img, 0, 1)
        made.append((name, PT.tooth(P.shrunk(), 3), PT.tooth(big, 4), P.count, time.time() - t1))
        pngio.write_png(os.path.join(dd, name.split()[-1] + "_2x.png"), np.dstack([pngio.to_u8(made[-1][2]), np.full(big.shape[:2], 255, np.uint8)]))

    def head(text, h=22):
        hd = np.tile(paper, (h, Wd, 1)).astype(np.float32)
        review._label(hd, text, 6, 5, scale=1)
        return hd

    def row(items, idx, pad=12):
        hmax = max(m[idx].shape[0] for m in items)
        r = np.tile(paper, (hmax + 2 * pad, Wd, 1)).astype(np.float32)
        x = pad
        for m in items:
            im = m[idx]
            r[pad + hmax - im.shape[0]:pad + hmax, x:x + im.shape[1]] = im[:, :max(0, Wd - x)]
            x += im.shape[1] + 24
        return r
    rows = [head("B-248 (D-200): FOUR MORE FOREST KINDS in ART v6 (the plan's first four) - the form-following brush, the same ONE light, no drawn line. PREVIEW, nothing exported", 26),
            head("AT THE GAME'S SIZE (64 px per metre): " + " | ".join(m[0] for m in made)), row(made, 1),
            head("AT 2x (the paintings as made): " + " | ".join(m[0] for m in made[:3])), row(made[:3], 2),
            head("AT 2x: " + made[3][0] + " (a paddle plant with side veins and a notched edge; a heart-leaf plant, each leaf on its stalk)"), row(made[3:], 2)]
    lines = ["WHAT EACH COST: " + "; ".join(f"{m[0]} {m[3]} dabs, {m[4]:.1f} s" for m in made),
             f"this run: {time.time() - t0:.0f} s. Files in b248_kinds/: " + ", ".join(m[0].split()[-1] + "_2x.png" for m in made)]
    foot = np.tile(paper, (24 + 16 * len(lines), Wd, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-248 four forest kinds preview (lock-free, numpy; nothing exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    preview(sys.argv[1])
