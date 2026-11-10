"""B-248 (D-200): FOUR MORE FOREST KINDS as specimens, in ART v6 - previews only, nothing exported.

LEAD 11-10 08:5x, the first four of the plan in coordination/reports/blender/v6_earth_kinds.md, in this order:
  the EMERGENT TREE (a tall pale trunk rising clear, buttress roots as thin planes at its foot, a small high crown);
  the FAN PALM (a ringed, leaning trunk; pleated fans on stalks, every blade of a fan its own stroke);
  the BROAD-LEAVED UNDERSTOREY in two more leaf shapes (a long paddle with torn edges; a heart-shaped leaf on a stalk);
  the BAMBOO CLUMP (jointed canes that taper, a ring at every node, sprays of small lance leaves).
Painted by the form-following brush of build_specimens_v6 (tube / facet / ball) under the same ONE light; no drawn
line. Each at the game's size (64 px per metre) and at 2x (the painting as made).

  python -I build_forest_kinds_v6.py <review png>     the lock-free sheet
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


def canvas(w, h, seed, gy, shade=(0, 0, 0)):
    P = PT.Painting(w, h, seed, Q)
    P.img[:] = rgb(SP.BACK)
    SP.ground(P, gy, int(w * 0.8))
    if shade[2]:
        SP.shade_pool(P, shade[0], gy + 6, shade[1], shade[2])
    return P


def limb(P, pts, r0, r1, cols, flare=0.0, n_per=0.05, rings=0.0):
    """A trunk, bough or cane: lit as a cylinder, its strokes laid across it (rings: a darker ring every `rings` px along)."""
    m, v, ang, s = SP.tube(P, pts, lambda t: r1 + (r0 - r1) * (1 - t) + flare * (1 - t) ** 4)
    lam = SP.lit_tube(v, ang) + 0.10 * P.fine
    u = SP.values(lam, (0.05, 0.36, 0.7), cols)
    P.lay(u, m)
    area = float(m.sum()) / (Q * Q)
    P.brush(u, m, int(n_per * area), (2.0, 2.0 + r0 * 0.55), (2.2, 4.0), SP.at(P, ang + math.pi / 2 + 0.55 * v), 0.12, (0.7, 1.0), 0.06, 0.012, 3.6, 0.3, clip=m)
    P.brush(cols[0], m * (v < -0.72), int(0.03 * area), (2.0, 5.0), (2.5, 4.0), SP.at(P, ang), 0.1, (0.6, 0.9), 0.04, 0.008, 4.0, 0.1, clip=m)
    if rings:                                                                   # nodes: a dark ring and a lighter band under it
        ctr = CEL.catmull([tuple(p) for p in pts], False, 8) if len(pts) >= 3 else [tuple(p) for p in pts]
        ln = sum(math.hypot(ctr[i + 1][0] - ctr[i][0], ctr[i + 1][1] - ctr[i][1]) for i in range(len(ctr) - 1))
        d, nxt = 0.0, rings * 0.6
        for i in range(len(ctr) - 1):
            (x0, y0), (x1, y1) = ctr[i], ctr[i + 1]
            step = math.hypot(x1 - x0, y1 - y0)
            while nxt <= d + step and step > 0:
                t = (nxt - d) / step
                x, y, a = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, math.atan2(y1 - y0, x1 - x0) + math.pi / 2
                r = r1 + (r0 - r1) * (1 - nxt / ln)
                P.dab(x, y, r * 1.05, 0.9, a, cols[0], 1.0, 4.5, 0.0, clip=m)
                P.dab(x + 1.6 * math.cos(a - math.pi / 2), y + 1.6 * math.sin(a - math.pi / 2), r * 0.9, 0.8, a, cols[3], 0.8, 4.0, 0.0, clip=m)
                nxt += rings * P.rng.uniform(0.85, 1.15)
            d += step
    return m


def cluster(P, cx, cy, r, cols, dim=0.0, n_per=0.055):
    """A leaf cluster lit as a ball, laid leaf by leaf, with leaves past its edge."""
    rng = P.rng
    m = np.zeros((P.ph, P.pw), np.float32)
    for _ in range(4):
        m = np.maximum(m, P.blob(cx + rng.uniform(-0.4, 0.4) * r, cy + rng.uniform(-0.3, 0.3) * r, r * rng.uniform(0.7, 1.0), r * rng.uniform(0.55, 0.8), 0.10, 0.45))
    dx, dy = (P.xx - cx) / r, (P.yy - cy) / r
    lam = dx * LIGHT[0] + dy * LIGHT[1] + np.sqrt(np.clip(1 - dx * dx - dy * dy, 0, 1)) * LIGHT[2] + 0.25 * P.fine - dim
    u = SP.values(lam, (0.05, 0.42, 0.78), cols)
    P.lay(u, m)
    out = lambda x, y: math.atan2(y - cy, x - cx)                               # noqa: E731
    area = float(m.sum()) / (Q * Q)
    P.brush(u, m, int(n_per * area), (3.0, 5.6), (1.7, 2.6), out, 0.55, (0.8, 1.0), 0.05, 0.012, 4.6, 0.1)
    P.brush(u, (P.box(m, 3) > 0.03) * (m < 0.5), int(0.02 * area), (3.0, 5.6), (1.9, 2.8), out, 0.7, (0.85, 1.0), 0.05, 0.012, 5.0, 0.0)


def leaf(P, pts, rad, cols, near=1.0, veins=0, tears=0, vein_a=1.05):
    """One broad leaf along a midrib: the half toward the light, the half away, a darker tip; strokes along it; a midrib;
    side veins as lighter strokes; tears as dark slits from the edge toward the midrib (a paddle leaf's torn edge)."""
    m, v, ang, s = SP.tube(P, pts, rad)
    if not m.any():
        return
    rib = CEL.catmull([tuple(p) for p in pts], False, 8)
    n = len(rib)
    for k in range(tears):                                                      # tears: thin wedges CUT out of the leaf's edge
        i = min(max(int(n * (0.2 + 0.62 * k / max(tears - 1, 1))), 1), n - 2)   # (runs 1-2 drew them as dark slits: thorns)
        (x0, y0), (x1, y1) = rib[i - 1], rib[i + 1]
        a = math.atan2(y1 - y0, x1 - x0)
        r = rad(i / (n - 1))
        b = a + (1 if k % 2 else -1) * vein_a
        apex = (rib[i][0] + math.cos(b) * r * 0.5, rib[i][1] + math.sin(b) * r * 0.5)
        e = (rib[i][0] + math.cos(b) * r * 1.3, rib[i][1] + math.sin(b) * r * 1.3)
        wedge = [apex, (e[0] - math.cos(a) * 2.0, e[1] - math.sin(a) * 2.0), (e[0] + math.cos(a) * 2.0, e[1] + math.sin(a) * 2.0)]
        m = m * (1 - GR._poly_mask(np.array([p[0] for p in wedge], np.float32) * Q, np.array([p[1] for p in wedge], np.float32) * Q, P.ph, P.pw))
    lam = v * (-np.sin(ang) * LIGHT[0] + np.cos(ang) * LIGHT[1])
    u = SP.values(lam + 0.1 * P.fine - 0.5 * (s > 0.9), (-0.12, 0.16), cols)
    P.lay(u, m)
    area = float(m.sum()) / (Q * Q)
    P.brush(u, m, int(0.07 * area), (3.5, 7.5), (2.8, 4.4), SP.at(P, ang), 0.1, (0.7, 1.0), 0.04, 0.01, 4.2, 0.2, clip=m)
    P.brush(cols[0] * 0.8, m * (np.abs(v) > 0.8) * (lam < 0), int(0.03 * area), (2.5, 5), (3, 4.5), SP.at(P, ang), 0.08, (0.6, 0.9), 0.03, 0.008, 4.4, 0.0, clip=m)
    for k in range(veins):                                                      # side veins, both ways from the midrib
        i = min(max(int(n * (0.14 + 0.72 * k / max(veins - 1, 1))), 1), n - 2)
        (x0, y0), (x1, y1) = rib[i - 1], rib[i + 1]
        a = math.atan2(y1 - y0, x1 - x0)
        r = rad(i / (n - 1))
        for side in (-1, 1):
            b = a + side * vein_a
            e = (rib[i][0] + math.cos(b) * r * 0.8, rib[i][1] + math.sin(b) * r * 0.8)
            P.stroke([rib[i], e], 0.9, 0.5, np.clip(cols[2] * 1.1 + 0.03, 0, 1), 4.0)
    P.stroke(rib[2:-3], 1.7, 0.6, lerp(cols[2], rgb("#DDE0A8"), 0.45) if near > 0.5 else cols[0] * 0.85, 4.0)


def greens(near, dark=0.0):
    return [lerp(rgb(c0), rgb(c1), near) * (1 - 0.35 * dark) for c0, c1 in (("#3F5A45", "#557A4C"), ("#56775A", "#7FA25F"), ("#7E9A6E", "#B5CC84"))]


# ---------------------------------------------------------------- the four kinds (frame units = px at the game's size)
def emergent(seed=41):
    """An emergent tree about 7.5 m tall: a pale trunk rising clear, four buttress roots as thin planes, a small high crown."""
    P = canvas(270, 520, seed, 486, (112, 84, 9))
    bark = [rgb(c) for c in ("#57504C", "#7C7468", "#A69C88", "#CFC5AC")]
    leafs = [rgb(c) for c in ("#4E6A49", "#6C8B58", "#93AE6E", "#BACB8A")]
    cluster(P, 134, 96, 36, leafs, 0.45)                                        # the crown's far side
    for sx, w, h, tone, a in ((-1, 54, 88, 1, 1.15), (1, 50, 80, 3, 1.95), (-1, 26, 54, 0, 1.3), (1, 24, 46, 2, 1.8)):   # buttresses: thin planes
        x0 = 138 + sx * 9
        poly = [(x0, 486 - h), (x0 + sx * w * 0.45, 486 - h * 0.34), (x0 + sx * w, 488), (x0, 488)]
        m = GR._poly_mask(np.array([p[0] for p in poly], np.float32) * Q, np.array([p[1] for p in poly], np.float32) * Q, P.ph, P.pw).astype(np.float32)
        m = np.clip((P.box(m, 0.5) - 0.5 + 0.1 * P.fine) * 5 + 0.5, 0, 1)
        P.lay(bark[tone], m)
        P.brush(bark[tone], m, int(0.05 * float(m.sum()) / (Q * Q)), (4, 9), (2.6, 4.2), a, 0.12, (0.7, 1.0), 0.06, 0.012, 3.6, 0.3, clip=m)
        P.stroke([poly[0], poly[1], poly[2]], 2.0, 1.2, bark[3] if sx > 0 else bark[0], 3.8)        # the plane's upper edge: lit or dark, as paint
    limb(P, [(138, 488), (135, 380), (141, 260), (136, 150)], 12.5, 7.5, bark, flare=4, n_per=0.045)
    for pts, r0, r1 in (([(136, 156), (118, 122), (94, 100)], 6, 2.2), ([(137, 152), (150, 112), (176, 92)], 6, 2.2), ([(136, 150), (136, 108), (130, 76)], 5.5, 2)):
        limb(P, pts, r0, r1, bark)
    for cx, cy, r in ((92, 92, 30), (132, 66, 34), (178, 84, 30), (112, 118, 22), (160, 116, 22)):
        cluster(P, cx, cy, r, leafs)
    return P


def fan_palm(seed=43):
    """A fan palm about 4.5 m tall: a ringed, leaning trunk; nine pleated fans on stalks, every blade its own stroke."""
    P = canvas(240, 330, seed, 300, (96, 60, 7))
    rng = P.rng
    bark = [rgb(c) for c in ("#4A3F3C", "#6A5A4C", "#8C7A62", "#AE9C7C")]
    top = (126, 112)
    fans = []
    for i in range(9):
        a = math.radians(-178 + 176 * i / 8 + rng.uniform(-7, 7))
        fans.append((abs(math.cos(a)) + rng.uniform(0, 0.3), a, rng.uniform(26, 40), rng.uniform(30, 40)))
    for depth, a, stalk, ln in sorted(fans, reverse=True):                      # the side fans first, the upright ones last
        near = 1.0 - min(1.0, depth / 1.3) * 0.7
        g = greens(near)
        droop = 0.45 * stalk * abs(math.cos(a))
        c = (top[0] + math.cos(a) * stalk, top[1] + math.sin(a) * stalk + droop)
        P.stroke([top, ((top[0] + c[0]) / 2, (top[1] + c[1]) / 2 - 3), c], 2.0, 1.2, g[0] * 0.8, 4.0)        # the stalk
        fa = math.atan2(c[1] - top[1], c[0] - top[0])
        for j in range(13):                                                     # the fan: thirteen blades over 160 degrees, pleated
            b = fa - math.radians(80) + math.radians(160) * j / 12
            L = ln * (0.72 + 0.28 * math.sin(math.pi * j / 12))
            lit = (math.cos(b) * LIGHT[0] + math.sin(b) * LIGHT[1]) > -0.1
            col = (g[2] if lit else g[1]) if j % 2 == 0 else (g[1] if lit else g[0])
            tip = (c[0] + math.cos(b) * L, c[1] + math.sin(b) * L + 0.1 * L * abs(math.cos(b)))
            P.stroke([c, ((c[0] + tip[0]) / 2, (c[1] + tip[1]) / 2), tip], 4.2, 0.8, np.clip(col * (1 + rng.normal(0, 0.04)), 0, 1), 4.6)
    limb(P, [(118, 302), (126, 232), (116, 168), top], 8.5, 5.5, bark, flare=4, n_per=0.07, rings=11)
    return P


def understorey(seed=47):
    """Two more broad-leaved plants: a PADDLE plant (long leaves with side veins and torn edges) and a HEART-leaf plant
    (each leaf on its own stalk, broad at the stalk and pointed at the tip, veins fanning from the stalk)."""
    P = canvas(360, 210, seed, 184, (120, 150, 9))
    rng = P.rng
    base, leaves = (100, 182), []
    for i in range(7):                                                          # the paddle plant
        a = math.radians(-150 + 120 * i / 6 + rng.uniform(-6, 6))
        ln = rng.uniform(96, 128) * (0.78 + 0.22 * abs(math.sin(a)))
        droop = 0.5 * ln * abs(math.cos(a)) ** 1.5
        leaves.append((rng.uniform(0, 1) + 0.5 * abs(math.cos(a)), [base, (base[0] + math.cos(a) * ln * 0.5, base[1] + math.sin(a) * ln * 0.6), (base[0] + math.cos(a) * ln, base[1] + math.sin(a) * ln + droop)], rng.uniform(13, 17)))
    for depth, pts, w in sorted(leaves, key=lambda t: t[0]):
        near = min(1.0, depth / 1.2)
        leaf(P, pts, lambda t, w=w: 1.2 + w * math.sin(math.pi * min(1.0, 0.08 + t * 0.94) ** 0.9) ** 0.55, greens(near), near, veins=6, tears=4)
    base, leaves = (262, 182), []
    for i in range(8):                                                          # the heart-leaf plant
        a = math.radians(-160 + 140 * i / 7 + rng.uniform(-8, 8))
        st = rng.uniform(40, 74) * (0.7 + 0.3 * abs(math.sin(a)))
        leaves.append((rng.uniform(0, 1) + 0.5 * abs(math.cos(a)), a, st, rng.uniform(15, 21)))
    for depth, a, st, w in sorted(leaves):
        near = min(1.0, depth / 1.2)
        g = greens(near)
        j = (base[0] + math.cos(a) * st, base[1] + math.sin(a) * st)                 # where the stalk meets the leaf
        P.stroke([base, ((base[0] + j[0]) / 2 + 3 * math.cos(a + 1.57), (base[1] + j[1]) / 2 + 3 * math.sin(a + 1.57)), j], 2.2, 1.4, g[0] * 0.9, 4.0)
        b = a + rng.uniform(0.5, 0.9) * (1 if math.cos(a) > 0 else -1) + (0.6 if abs(math.cos(a)) < 0.3 else 0.0)   # the leaf hangs outward from its stalk
        ln = w * 2.5
        tip = (j[0] + math.cos(b) * ln, j[1] + math.sin(b) * ln + 0.25 * ln)
        back = (j[0] - math.cos(b) * w * 0.35, j[1] - math.sin(b) * w * 0.35)        # the two lobes behind the stalk's joint
        leaf(P, [back, j, ((j[0] + tip[0]) / 2, (j[1] + tip[1]) / 2 - 2), tip], lambda t, w=w: 0.8 + w * (math.sin(math.pi * min(1.0, 0.1 + t * 0.9) ** 0.45) ** 0.9), g, near, veins=4, vein_a=0.75)
    return P


def bamboo(seed=53):
    """A bamboo clump about 6 m tall: nine canes that taper, a ring at every node, sprays of small lance leaves."""
    P = canvas(230, 410, seed, 380, (100, 70, 8))
    rng = P.rng
    canes = []
    for i in range(9):
        x0 = 100 + rng.uniform(-22, 26)
        h, lean = rng.uniform(250, 356), rng.uniform(-0.16, 0.2)
        canes.append((rng.random(), x0, h, lean, rng.uniform(3.4, 4.8)))
    for depth, x0, h, lean, r0 in sorted(canes):
        k = 0.45 + 0.55 * depth
        cols = [lerp(rgb("#8E9A80"), rgb(c), k) for c in ("#5C6B3C", "#86924E", "#B4BA6C", "#D2D08A")]
        g = greens(depth)
        pts = [(x0, 382), (x0 + lean * h * 0.3, 382 - h * 0.4), (x0 + lean * h * 0.75, 382 - h * 0.75), (x0 + lean * h * 1.25, 382 - h)]
        limb(P, pts, r0, 1.4, cols, n_per=0.09, rings=rng.uniform(24, 32))
        ctr = CEL.catmull(pts, False, 8)
        for i in range(int(len(ctr) * 0.45), len(ctr) - 1, 3):                  # sprays of lance leaves at the upper nodes
            x, y = ctr[i]
            side = 1 if rng.random() < 0.5 else -1
            for _ in range(int(rng.integers(3, 6))):
                b = math.radians(rng.uniform(10, 70)) * side + (0 if side > 0 else math.pi)
                L = rng.uniform(14, 22)
                tip = (x + math.cos(b) * L, y + abs(math.sin(b)) * L * 0.9)
                lit = math.cos(b) * LIGHT[0] > 0
                P.stroke([(x, y), ((x + tip[0]) / 2, (y + tip[1]) / 2 - 1.5), tip], 3.2, 0.6, np.clip((g[2] if lit else g[1]) * (1 + rng.normal(0, 0.05)), 0, 1), 4.8)
    return P


KINDS = (("an emergent tree", emergent), ("a fan palm", fan_palm), ("a bamboo clump", bamboo), ("two understorey plants", understorey))


# ---------------------------------------------------------------- the sheet
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
            head("AT 2x: " + made[3][0] + " (a paddle plant with side veins and torn edges; a heart-leaf plant, each leaf on its stalk)"), row(made[3:], 2)]
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
