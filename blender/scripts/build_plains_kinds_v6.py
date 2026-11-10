"""B-248 (D-200): THE PLAINS' KINDS in ART v6 - written 11-10 10:0x as SOURCE, UNRUN (LEAD: while the owner looks and the
0.6.3 sweep holds the machine; any yes from the owner uses them). Nothing here has been painted yet: the first run is
a look at every shape, not a sheet.

The plan's kinds 9 and 10 (coordination/reports/blender/v6_earth_kinds.md):
  9.  GRASSES IN THREE HEIGHTS: TURF (short blades along a width of ground), the CLUMP (the specimen sheet's grass, made
      placeable) and a tall PLUMED GRASS (a tussock of arching blades, stems that rise clear of it, a feathered seed
      head of small dabs on each). `dry` = how much of it is straw: the plains are drier than the forest.
  10. the FLAT-TOPPED SAVANNA TREE (a short forked trunk, boughs that spread wide and level, a thin layered crown of
      SHELVES: balls pressed flat, lit along the top and dark under) and the THORN BUSH (the same crown at knee height on
      many thin stems, pale thorns).
The rules are build_forest_kinds_v6's: every kind is written about its own foot (0, 0) in px at 64 px per metre (y up is
negative) and painted through a placement (tf, s), so a specimen sheet and a frame use the same code; every angle is
taken from the PLACED points, so a mirrored or leaning plant is lit by the same ONE light. No drawn line.

  python -I build_plains_kinds_v6.py <review png>     the lock-free specimen sheet (the game's size and 2x)
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
import build_specimens_v6 as SP  # noqa: E402
import build_forest_kinds_v6 as FK  # noqa: E402

rgb, lerp = PT.rgb, PT.lerp
Q, LIGHT, HAZE = SP.Q, SP.LIGHT, FK.HAZE
STRAW = ("#8E8250", "#B7A765", "#D9CC8E")                  # dry grass: in shade, mid, lit
BLADE = ("#4A6540", "#9DB868")                             # green grass: the far blade, the near blade (the specimen's)
PLUME = ("#A99A76", "#D6C9A0", "#F0E8C8")                  # a seed head: in shade, mid, lit
SAV_BARK = ("#4A3F38", "#6B5A4A", "#8F7C62", "#B5A280")    # deep, shade, mid, lit
SAV_LEAF = ("#4F6340", "#6F8550", "#97A866", "#BFC784")    # an olive, drier green than the forest's


def blade_col(rng, depth, pale=0.0, dark=0.0, dry=0.1):
    """One blade's colour: far blades dark, near ones lit; `dry` of them straw."""
    c0, c1 = (STRAW[0], STRAW[2]) if rng.random() < dry else BLADE
    c = lerp(rgb(c0), rgb(c1), depth)
    return np.clip(lerp(c, HAZE, pale) * (1 - 0.35 * dark) * (1 + rng.normal(0, 0.05)), 0, 1)


def ang_of(p0, p1):
    return math.atan2(p1[1] - p0[1], p1[0] - p0[0])


def lit_way(p0, p1):
    """Does the placed direction p0 -> p1 lean toward the light (upper right)?"""
    d = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) or 1e-6
    return ((p1[0] - p0[0]) * LIGHT[0] + (p1[1] - p0[1]) * LIGHT[1]) / d


# ---------------------------------------------------------------- 9. grasses in three heights
def turf_into(P, tf, s=1.0, pale=0.0, dark=0.0, width=128, dry=0.15, n=None):
    """TURF: short blades (0.1-0.3 m) along `width` px of ground about the foot, every blade its own tapering stroke."""
    rng, bl = P.rng, []
    for _ in range(int(width * 0.9) if n is None else n):
        bl.append((rng.random(), rng.uniform(-width / 2, width / 2), -math.pi / 2 + rng.normal(0, 0.35), rng.uniform(7, 18), rng.normal(0.2, 0.3)))
    for depth, bx, a, ln, bend in sorted(bl):
        P.stroke([tf(bx, 1), tf(bx + math.cos(a) * ln * 0.55, math.sin(a) * ln * 0.55), tf(bx + math.cos(a + bend) * ln, math.sin(a + bend) * ln)],
                 2.0 * s, 0.5 * s, blade_col(rng, depth, pale, dark, dry), 5.0)


def clump_into(P, tf, s=1.0, pale=0.0, dark=0.0, n=46, dry=0.1, spread=11):
    """The CLUMP (0.4-1.0 m): the specimen sheet's grass made placeable - the far blades dark, the near ones lit with a
    thin lighter stroke down their lit side."""
    rng, bl = P.rng, []
    for _ in range(n):
        bl.append((rng.random(), rng.uniform(-spread, spread), -math.pi / 2 + rng.normal(0, 0.42), rng.uniform(26, 62), rng.normal(0.25, 0.25) * (1 if rng.random() < 0.7 else -1)))
    for depth, bx, a, ln, bend in sorted(bl):
        col = blade_col(rng, depth, pale, dark, dry)
        p0, pm = tf(bx, 1), tf(bx + math.cos(a) * ln * 0.55, math.sin(a) * ln * 0.55)
        pt = tf(bx + math.cos(a + bend) * ln, math.sin(a + bend) * ln + 0.24 * ln * abs(bend))
        P.stroke([p0, pm, pt], 3.0 * s, 0.7 * s, col, 5.0)
        if depth > 0.6:
            P.stroke([(p0[0] + 0.8 * s, p0[1] - 2 * s), (pm[0] + 0.9 * s, pm[1])], 0.9 * s, 0.5 * s, np.clip(col * 1.18 + 0.03, 0, 1), 5.0)


def plume_grass_into(P, tf, s=1.0, pale=0.0, dark=0.0, n=9, dry=0.35, blades=44):
    """A tall PLUMED GRASS about 2-2.5 m: a tussock of long blades that arch over, `n` stems that rise clear of it, and
    on each a feathered seed head: a nodding spindle of small dabs, pale on its lit side."""
    rng = P.rng
    things = []
    for _ in range(blades):                                                     # the tussock
        things.append((rng.random(), "blade", rng.uniform(-9, 9), -math.pi / 2 + rng.normal(0, 0.5), rng.uniform(58, 108), 0.0))
    for _ in range(n):                                                          # the stems, standing a little straighter
        things.append((rng.uniform(0.25, 1.0), "stem", rng.uniform(-6, 6), -math.pi / 2 + rng.normal(0, 0.2), rng.uniform(118, 158), rng.uniform(28, 42)))
    pl = FK.hz(PLUME, pale, dark)
    for depth, what, bx, a, ln, head in sorted(things, key=lambda t: t[0]):
        out = 1 if math.cos(a) >= 0 else -1                                     # the way it leans, in its own px
        if what == "blade":
            droop = ln * (0.18 + 0.5 * abs(math.cos(a)))                        # a long blade bends over under its own weight
            tip_y = min(math.sin(a) * ln + droop, -3.0)                         # (run 1: tips went into the ground; and three points made a kink)
            arc = CEL.catmull([(bx, 1), (bx + math.cos(a) * ln * 0.5, math.sin(a) * ln * 0.62), (bx + math.cos(a) * ln + out * 0.12 * ln, tip_y)], False, 6)
            P.stroke([tf(*p) for p in arc], 3.2 * s, 0.6 * s, blade_col(rng, depth, pale, dark, dry), 5.0)
            continue
        straw = np.clip(lerp(lerp(rgb(STRAW[0]), rgb(STRAW[2]), depth), HAZE, pale) * (1 - 0.35 * dark), 0, 1)
        top = (bx + math.cos(a) * ln + out * 0.05 * ln, math.sin(a) * ln)
        stem = CEL.catmull([(bx, 1), (bx + math.cos(a) * ln * 0.5, math.sin(a) * ln * 0.5), top], False, 6)
        P.stroke([tf(*p) for p in stem], 1.7 * s, 0.9 * s, straw, 4.6)
        nod = rng.uniform(0.25, 0.6) * out                                      # the head nods over to the side the stem leans
        axis = [top, (top[0] + math.cos(a + nod * 0.5) * head * 0.5, top[1] + math.sin(a + nod * 0.5) * head * 0.5),
                (top[0] + math.cos(a + nod) * head, top[1] + math.sin(a + nod) * head + 0.12 * head)]
        ctr = CEL.catmull(axis, False, 10)
        hw = rng.uniform(4.0, 6.0)                                              # the spindle's half-width, px
        for i in range(1, len(ctr)):
            t = i / (len(ctr) - 1)
            wd = 0.6 + hw * math.sin(math.pi * min(1.0, t ** 0.8)) ** 0.7
            c0, c1 = tf(*ctr[i - 1]), tf(*ctr[i])
            along = ang_of(c0, c1)
            for side in (-1, 1):
                for _k in range(2):
                    off = side * rng.uniform(0.1, 1.0) * wd * s
                    px, py = c1[0] - math.sin(along) * off, c1[1] + math.cos(along) * off
                    b = along + side * rng.uniform(0.25, 0.7)                   # every seed tuft feathers out and back
                    lit = (-math.sin(along) * side * LIGHT[0] + math.cos(along) * side * LIGHT[1]) > 0
                    col = pl[2] if (lit and depth > 0.45) else pl[1] if (lit or depth > 0.6) else pl[0]
                    P.dab(px, py, rng.uniform(2.6, 4.2) * s, max(0.7, rng.uniform(0.9, 1.4) * s), b, np.clip(col * (1 + rng.normal(0, 0.04)), 0, 1), 1.0, 4.4, 0.1)


# ---------------------------------------------------------------- 10. the flat-topped savanna tree and the thorn bush
def shelf(P, cx, cy, rx, ry, cols, dim=0.0, n_per=0.06, s=1.0):
    """One flat layer of a crown (frame px): a ball pressed flat - lit along its top, mid across its face, dark under
    it - laid leaf by leaf in near-level strokes, with leaves past its edge."""
    rng = P.rng
    y0, y1 = max(int((cy - 2.4 * ry) * Q), 0), min(int((cy + 2.4 * ry) * Q) + 1, P.ph)
    x0, x1 = max(int((cx - 1.5 * rx) * Q), 0), min(int((cx + 1.5 * rx) * Q) + 1, P.pw)
    if y1 <= y0 or x1 <= x0:
        return
    w = (slice(y0, y1), slice(x0, x1))
    m = np.zeros((y1 - y0, x1 - x0), np.float32)
    for _ in range(5):
        m = np.maximum(m, P.blob(cx + rng.uniform(-0.45, 0.45) * rx, cy + rng.uniform(-0.25, 0.25) * ry, rx * rng.uniform(0.5, 0.75), ry * rng.uniform(0.7, 1.0), 0.10, 0.4)[w])
    if not m.any():
        return
    dx, dy = (P.xx[:, w[1]] - cx) / rx, (P.yy[w[0]] - cy) / ry
    lam = 0.5 * dx * LIGHT[0] + 1.25 * dy * LIGHT[1] + 0.8 * np.sqrt(np.clip(1 - dx * dx - dy * dy, 0, 1)) * LIGHT[2] + 0.25 * P.fine[w] - dim
    u = SP.values(lam, (0.05, 0.42, 0.78), cols)
    FK.into(P, w, u, m)
    level = lambda x, y: 0.3 * max(-1.0, min(1.0, (y - cy) / ry)) * (1 if x >= cx else -1)   # noqa: E731  near-level, tilting out at the ends
    k = max(s, 0.6)
    area = float(m.sum()) / (Q * Q) / (k * k)
    P.brush(u, m, int(n_per * area), (3.0 * k, 5.6 * k), (1.8, 2.8), level, 0.4, (0.8, 1.0), 0.05, 0.012, 4.6, 0.1, win=w)
    P.brush(u, (PT.box(m, int(round(3 * k * Q))) > 0.03) * (m < 0.5), int(0.025 * area), (3.0 * k, 5.6 * k), (1.9, 2.8), level, 0.5, (0.85, 1.0), 0.05, 0.012, 5.0, 0.0, win=w)


def savanna_tree_into(P, tf, s=1.0, pale=0.0, dark=0.0):
    """A flat-topped savanna tree about 5 m tall and 7 m wide: a short trunk that forks low, three boughs that spread wide
    and rise little, twigs up into a thin crown of shelves with sky between them."""
    bark = FK.hz(SAV_BARK, pale, dark)
    leafs = FK.hz(SAV_LEAF, pale, dark)
    T = lambda pts: [tf(*p) for p in pts]                                      # noqa: E731
    fork = (4, -118)
    for cx, cy, rx, ry in ((14, -276, 196, 20), (-150, -250, 60, 12)):          # the crown's far side, in shade, behind the wood
        shelf(P, *tf(cx, cy), rx * s, ry * s, leafs, 0.45, s=s)
    for pts, r0, r1 in (([(-4, -7), (-16, 0), (-27, 4)], 7.5, 3.0), ([(5, -7), (17, 0), (29, 4)], 7.5, 3.0)):
        FK.limb(P, T(pts), r0 * s, r1 * s, bark, s=s)                           # two short thick roots (run 1: long thin ones read as a bird's feet)
    FK.limb(P, T([(0, 3), (-7, -42), (-2, -84), fork]), 11 * s, 8.5 * s, bark, flare=6 * s, s=s)   # the trunk, leaning a little
    boughs = (([fork, (-48, -186), (-116, -228), (-176, -246)], 7.5, 2.6),
              ([fork, (12, -186), (30, -244), (38, -282)], 7.0, 2.4),
              ([fork, (62, -192), (130, -236), (192, -258)], 7.5, 2.6))
    for pts, r0, r1 in boughs:
        FK.limb(P, T(pts), r0 * s, r1 * s, bark, s=s)
    for pts in ([(-48, -186), (-66, -232), (-82, -262)], [(-116, -228), (-128, -252), (-146, -266)], [(62, -192), (86, -242), (102, -274)],
                [(130, -236), (146, -262), (166, -280)], [(12, -186), (-10, -236), (-30, -278)], [(30, -244), (58, -276), (74, -296)]):
        FK.limb(P, T(pts), 3.4 * s, 1.2 * s, bark, n_per=0.08, s=s)             # twigs up into the shelves
    for cx, cy, rx, ry in ((-178, -248, 46, 11), (-126, -264, 84, 16), (-48, -288, 80, 17), (38, -304, 94, 18), (128, -286, 90, 17), (198, -268, 56, 13)):
        shelf(P, *tf(cx, cy), rx * s, ry * s, leafs, s=s)


def thorn_bush_into(P, tf, s=1.0, pale=0.0, dark=0.0, n=8):
    """A thorn bush about 1.2 m tall and 2 m wide: many thin stems fanned from one foot, pale thorns on them, the savanna
    tree's shelves at knee height."""
    rng = P.rng
    bark = FK.hz(SAV_BARK, pale, dark)
    leafs = FK.hz(SAV_LEAF, pale, dark)
    thorn = np.clip(lerp(rgb("#DCD3B4"), HAZE, pale) * (1 - 0.35 * dark), 0, 1)
    shelf(P, *tf(2, -56), 62 * s, 10 * s, leafs, 0.45, s=s)                     # the far side, in shade
    shelf(P, *tf(-4, -38), 46 * s, 9 * s, leafs, 0.5, s=s)                      # (run 1: an umbrella on sticks, a small tree; a bush is leafy to its knees)
    for i in range(n):
        a = math.radians(-152 + 124 * i / (n - 1) + rng.uniform(-5, 5))
        ln = rng.uniform(44, 62) * (0.8 + 0.2 * abs(math.sin(a)))
        bx = rng.uniform(-5, 5)
        pts = [tf(bx, 1), tf(bx + math.cos(a) * ln * 0.5, math.sin(a) * ln * 0.58), tf(bx + math.cos(a) * ln, math.sin(a) * ln + 0.1 * ln * abs(math.cos(a)))]
        P.stroke(pts, 2.6 * s, 1.1 * s, bark[1], 4.4)
        if lit_way(pts[0], pts[2]) > -0.2:                                      # the light down one side of a stem
            P.stroke([(p[0] + 0.8 * s, p[1] - 0.4 * s) for p in pts[:2]], 0.9 * s, 0.5 * s, bark[3], 4.6)
        ctr = CEL.catmull(pts, False, 6)
        for j in range(3, len(ctr) - 2, 3):                                     # thorns: short pale ticks, set alternately
            x, y = ctr[j]
            b = ang_of(ctr[j - 1], ctr[j]) + (1 if (j // 3) % 2 else -1) * rng.uniform(0.9, 1.3)
            P.stroke([(x, y), (x + math.cos(b) * 5.0 * s, y + math.sin(b) * 5.0 * s)], 1.0 * s, 0.4 * s, thorn, 5.0)
    for cx, cy, rx, ry in ((-46, -36, 26, 8), (42, -34, 28, 8), (-36, -60, 34, 9), (10, -72, 42, 10), (46, -58, 30, 8), (0, -24, 22, 7)):
        shelf(P, *tf(cx, cy), rx * s, ry * s, leafs, s=s)                       # low side shelves first, the top ones over them, a low one in front


# ---------------------------------------------------------------- the specimen sheet (first run 11-10 10:14)
def grasses(seed=61):
    P = FK.canvas(430, 210, seed, 184, (170, 190, 8))
    turf_into(P, FK.at(72, 184), width=110)
    clump_into(P, FK.at(200, 184))
    plume_grass_into(P, FK.at(336, 184))
    return P


def savanna_tree(seed=67):
    P = FK.canvas(560, 380, seed, 348, (236, 204, 10))
    savanna_tree_into(P, FK.at(280, 348))
    return P


def thorn_bush(seed=71):
    P = FK.canvas(220, 140, seed, 118, (96, 82, 6))
    thorn_bush_into(P, FK.at(110, 118))
    return P


KINDS = (("three grasses", grasses), ("a savanna tree", savanna_tree), ("a thorn bush", thorn_bush),
         ("a tree fern", FK.tree_fern))                    # the forest's kind 4b, unrun too: shown here, FK's own sheet is accepted as it is


def preview(out):
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    t0 = time.time()
    dd = os.path.join(os.path.dirname(out), "b248_plains")
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
            im = m[idx][:, :max(0, Wd - x)]
            r[pad + hmax - im.shape[0]:pad + hmax, x:x + im.shape[1]] = im
            x += im.shape[1] + 24
        return r
    rows = [head("B-248 (D-200): THE PLAINS' KINDS in ART v6 (the plan's 9 and 10) and the TREE FERN (4) - the form-following brush, the same ONE light, no drawn line. PREVIEW, nothing exported", 26),
            head("AT THE GAME'S SIZE (64 px per metre): " + " | ".join(m[0] for m in made)), row(made, 1),
            head("AT 2x (as painted): " + made[0][0] + " (turf, the clump, the plumed grass) | " + made[2][0] + " | " + made[3][0]), row([made[0], made[2], made[3]], 2),
            head("AT 2x: " + made[1][0] + " (a short forked trunk, level boughs, a thin crown of shelves with sky between them)"), row(made[1:2], 2)]
    lines = ["WHAT EACH COST: " + "; ".join(f"{m[0]} {m[3]} dabs, {m[4]:.1f} s" for m in made),
             f"this run: {time.time() - t0:.0f} s. Files in b248_plains/: " + ", ".join(m[0].split()[-1] + "_2x.png" for m in made)]
    foot = np.tile(paper, (24 + 16 * len(lines), Wd, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-248 the plains' kinds preview (lock-free, numpy; nothing exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    preview(sys.argv[1])
