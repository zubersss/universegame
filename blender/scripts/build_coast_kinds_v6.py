"""B-248 (D-200): THE COAST'S KINDS in ART v6 - written 11-10 10:1x as SOURCE, UNRUN (LEAD: files only while the 0.6.3
sweep holds the machine). Nothing here has been painted yet: the first run is a look at every shape, not a sheet.

The plan's kinds 11 and 12 (coordination/reports/blender/v6_earth_kinds.md):
  11. the LEANING COCONUT PALM (a long ringed trunk curving seaward, drooping fronds, a cluster of nuts under them) and
      DUNE GRASS (long blades in a tuft, all bent one way by the sea wind).
  12. SEA-WORN ROCKS (a dark boulder in planes whose lower parts are WET: a darker, cooler value under a pale lit edge,
      weed hanging from that line, barnacles above it), the TIDE LINE (a low strip of wrack on the sand) and
      DRIFTWOOD (a bleached log, a broken end, a branch stub, a few cracks).
The rules are build_forest_kinds_v6's (FK): every kind about its own foot (0, 0) in px at 64 px per metre (y up is
negative), painted through a placement (tf, s); every angle is taken from the PLACED points. No drawn line.
The specimens stand on the sheet's olive earth (FK.canvas); the coast's own sand palette is not written yet.

  python -I build_coast_kinds_v6.py <review png>      the lock-free specimen sheet (the game's size and 2x)
"""
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio  # noqa: E402
import paint_v6 as PT  # noqa: E402
import build_specimens_v6 as SP  # noqa: E402
import build_forest_kinds_v6 as FK  # noqa: E402
import build_plains_kinds_v6 as PK  # noqa: E402

rgb, lerp = PT.rgb, PT.lerp
LIGHT, HAZE = SP.LIGHT, FK.HAZE
PALM_BARK = ("#4A3F3C", "#6A5A4C", "#8C7A62", "#AE9C7C")   # the forest palms' bark: deep, shade, mid, lit
NUT = ("#6E5A3A", "#93794C", "#B89A62")
MARRAM = ("#5E7358", "#A9BC8A")                            # dune grass: a grey sea green, the far blade and the near blade
ROCK = {"lit": "#A9A49A", "half": "#8B877F", "mid": "#6E6B69", "shade": "#54525C"}
WET = (0.72, 0.78, 0.90)                                   # a wet plane: its own value, darker and cooler
WEED = ("#4A4A30", "#6A6240", "#8A7A50")
DRIFT = ("#8C867A", "#ADA696", "#CCC5B2", "#E6E0CE")       # bleached wood: deep, shade, mid, lit


def tone(c, pale=0.0, dark=0.0):
    return np.clip(lerp(rgb(c) if isinstance(c, str) else c, HAZE, pale) * (1 - 0.35 * dark), 0, 1)


# ---------------------------------------------------------------- 11. the leaning coconut palm and dune grass
def coconut_palm_into(P, tf, s=1.0, pale=0.0, dark=0.0, n=13):
    """A coconut palm about 6.5 m: a long ringed trunk that leans and curves toward +x (mirror it to face the sea), a
    crown of long drooping fronds in a far and a near half, a cluster of nuts under them."""
    rng = P.rng
    bark = FK.hz(PALM_BARK, pale, dark)
    cols, back = FK.hz(FK.FERN, pale, dark), FK.hz(FK.FERN, pale, min(1.0, dark + 0.5))
    nuts = FK.hz(NUT, pale, dark)
    top = (126, -372)
    fr = []
    for i in range(n):
        a = math.radians(-204 + 228 * i / (n - 1) + rng.uniform(-6, 6))         # from hanging at the left, over the top, to hanging at the right
        fr.append((rng.random() + 0.4 * abs(math.cos(a)), a, rng.uniform(96, 128)))
    fr.sort()
    for depth, a, ln in fr[:n // 2]:
        FK.frond(P, tf, s, top, a, ln, ln * (0.3 + 0.9 * abs(math.cos(a))), back, 20)
    FK.limb(P, [tf(*p) for p in ((0, 2), (26, -120), (70, -250), top)], 9 * s, 5.5 * s, bark, flare=5 * s, n_per=0.07, rings=10 * s, s=s)
    for ox, oy in ((-7, 9), (2, 13), (10, 8), (-2, 5), (6, 3)):                 # the nuts, each a round dab with its lit side
        x, y = tf(top[0] + ox, top[1] + oy)
        P.dab(x, y, 5.0 * s, 4.4 * s, 0.0, nuts[1], 1.0, 4.4, 0.0)
        P.dab(x + 1.4 * s * LIGHT[0], y + 1.4 * s * LIGHT[1], 2.4 * s, 2.0 * s, 0.0, nuts[2], 1.0, 4.0, 0.0)
        P.dab(x - 1.8 * s * LIGHT[0], y - 1.8 * s * LIGHT[1], 2.6 * s, 1.6 * s, 0.6, nuts[0], 0.9, 4.0, 0.0)
    for depth, a, ln in fr[n // 2:]:
        FK.frond(P, tf, s, top, a, ln, ln * (0.3 + 0.9 * abs(math.cos(a))), cols, 20)


def dune_grass_into(P, tf, s=1.0, pale=0.0, dark=0.0, n=34, dry=0.45, wind=1):
    """A tuft of DUNE GRASS about 0.6-1.2 m: long thin blades, every one bent the same way by the wind (wind = +1: toward
    +x in its own px)."""
    rng, bl = P.rng, []
    for _ in range(n):
        bl.append((rng.random(), rng.uniform(-8, 8), -math.pi / 2 + rng.normal(0.12 * wind, 0.3), rng.uniform(40, 80), wind * rng.uniform(0.5, 1.1)))
    for depth, bx, a, ln, bend in sorted(bl):
        c0, c1 = (PK.STRAW[0], PK.STRAW[2]) if rng.random() < dry else MARRAM
        col = tone(lerp(rgb(c0), rgb(c1), depth), pale, dark) * (1 + rng.normal(0, 0.05))
        pts = [tf(bx, 1), tf(bx + math.cos(a) * ln * 0.5, math.sin(a) * ln * 0.55), tf(bx + math.cos(a + bend) * ln, math.sin(a + bend) * ln + 0.2 * ln * abs(bend))]
        P.stroke(pts, 2.4 * s, 0.5 * s, np.clip(col, 0, 1), 5.0)


# ---------------------------------------------------------------- 12. sea-worn rocks, the tide line, driftwood
def sea_rock_into(P, tf, s=1.0, pale=0.0, dark=0.0, wet_y=-12):
    """A sea-worn boulder about 1.5 m wide and 0.9 m tall: a lit top, three side planes, and below the line y = wet_y the
    same planes WET (darker, cooler) under a thin pale edge; weed hangs from that line, barnacles sit above it."""
    rng = P.rng
    fl = FK.flipped(tf)
    T = lambda poly: [tf(*p) for p in poly]                                    # noqa: E731
    planes = (("lit", 0.12, [(-34, -44), (-8, -56), (22, -54), (40, -40), (26, -30), (-10, -34)], None),
              ("shade", 1.22, [(-46, wet_y - 2), (-34, -44), (-10, -34), (-18, wet_y)], [(-48, 2), (-46, wet_y - 2), (-18, wet_y), (-20, 2)]),
              ("mid", 1.5, [(-10, -34), (26, -30), (22, wet_y), (-18, wet_y)], [(-18, wet_y), (22, wet_y), (20, 2), (-20, 2)]),
              ("half", 1.92, [(26, -30), (40, -40), (50, -18), (48, wet_y), (22, wet_y)], [(22, wet_y), (48, wet_y), (50, 2), (20, 2)]))
    for name, a, dry_poly, wet_poly in planes:
        if fl:                                                                  # mirrored: the planes toward and away from the light change places
            name = {"shade": "half", "half": "shade"}.get(name, name)
        c = tone(ROCK[name], pale, dark)
        ang = math.pi - a if fl else a
        FK.facet(P, T(dry_poly), c, ang, s)
        if wet_poly is not None:
            FK.facet(P, T(wet_poly), np.clip(c * np.array(WET, np.float32), 0, 1), ang, s)
    P.stroke(T([(-46, wet_y - 2), (-18, wet_y), (22, wet_y), (48, wet_y)]), 1.4 * s, 1.0 * s, tone("#C9CDD0", pale, dark), 3.6)   # the wet line's lit edge
    P.stroke(T([(-34, -44), (-10, -34), (26, -30), (40, -40)]), 2.0 * s, 1.2 * s, tone("#C4BFB2", pale, dark), 3.5)                # the top's lit rim
    weed = FK.hz(WEED, pale, dark)
    for _ in range(11):                                                         # weed hangs from the wet line
        x, y = tf(rng.uniform(-42, 44), wet_y + rng.uniform(2, 6))
        P.dab(x, y, rng.uniform(3.5, 6.0) * s, 1.7 * s, math.pi / 2 + rng.normal(0, 0.3), weed[int(rng.integers(0, 3))], 1.0, 4.2, 0.1)
    barn = tone("#D8D4C4", pale, dark)
    for cx, cy in ((-24, wet_y - 6), (6, wet_y - 5), (34, wet_y - 7)):          # barnacles: small pale dots in three patches above it
        for _ in range(5):
            x, y = tf(cx + rng.uniform(-6, 6), cy + rng.uniform(-3, 3))
            P.dab(x, y, 1.5 * s, 1.3 * s, 0.0, barn, 0.95, 4.6, 0.0)


def wrack_into(P, tf, s=1.0, pale=0.0, dark=0.0, width=200):
    """The TIDE LINE: a low wavering strip of wrack along `width` px of sand - dark weed in small heaps, a few pale shell
    flecks - no higher than 0.1 m."""
    rng = P.rng
    weed = FK.hz(WEED, pale, dark)
    shell = tone("#E4DDC6", pale, dark)
    for _ in range(int(width * 0.55)):
        bx = rng.uniform(-width / 2, width / 2)
        heap = 0.5 + 0.5 * math.sin(bx / 23.0) * math.sin(bx / 7.0 + 1.3)        # it gathers in heaps and thins between them
        if rng.random() > 0.35 + 0.65 * heap:
            continue
        x, y = tf(bx, -rng.uniform(0, 5) * heap)
        P.dab(x, y, rng.uniform(3, 6.5) * s, rng.uniform(1.2, 2.2) * s, rng.normal(0, 0.35), weed[int(rng.integers(0, 3))], 1.0, 4.0, 0.15)
    for _ in range(max(3, int(width / 28))):
        x, y = tf(rng.uniform(-width / 2, width / 2), -rng.uniform(0, 2))
        P.dab(x, y, 1.8 * s, 1.1 * s, rng.normal(0, 0.5), shell, 1.0, 4.6, 0.0)


def driftwood_into(P, tf, s=1.0, pale=0.0, dark=0.0):
    """DRIFTWOOD about 2.4 m long: a bleached log lying on the sand, a little bent, one branch stub, a broken end with its
    rings, a few cracks along the grain."""
    rng = P.rng
    wood = FK.hz(DRIFT, pale, dark)
    ctr = [(-76, -9), (-30, -11), (24, -8), (78, -12)]
    FK.limb(P, [tf(*p) for p in ctr], 9 * s, 6.5 * s, wood, n_per=0.06, s=s)
    FK.limb(P, [tf(*p) for p in ((18, -12), (30, -28), (46, -38))], 3.6 * s, 1.4 * s, wood, n_per=0.08, s=s)   # a branch stub
    e0, e1 = tf(*ctr[0]), tf(*ctr[1])
    across = PK.ang_of(e0, e1) + math.pi / 2
    for a_, b_, c in ((8.6, 3.4, wood[1]), (5.6, 2.2, wood[0]), (2.6, 1.0, wood[2])):                           # the broken end: three rings
        P.dab(e0[0], e0[1], a_ * s, b_ * s, across, c, 1.0, 4.6, 0.0)
    crack = tone("#6E6A60", pale, dark)
    for _ in range(5):                                                          # cracks along the grain
        t = rng.uniform(0.15, 0.85)
        x = ctr[0][0] + (ctr[3][0] - ctr[0][0]) * t
        y = -10 + rng.uniform(-3, 3)
        ln = rng.uniform(10, 22)
        P.stroke([tf(x, y), tf(x + ln, y + rng.uniform(-1, 1))], 0.9 * s, 0.4 * s, crack, 4.6)


# ---------------------------------------------------------------- the specimen sheet (unrun)
def palm_and_grass(seed=73):
    P = FK.canvas(480, 550, seed, 520, (170, 200, 9))       # the fronds stand up to 2 m above the trunk's top (372 px)
    coconut_palm_into(P, FK.at(100, 520))
    dune_grass_into(P, FK.at(400, 520))
    return P


def shore(seed=79):
    P = FK.canvas(460, 130, seed, 104, (150, 200, 7))
    sea_rock_into(P, FK.at(76, 104))
    wrack_into(P, FK.at(214, 104), width=120)
    driftwood_into(P, FK.at(362, 104))
    return P


KINDS = (("a coconut palm and dune grass", palm_and_grass), ("a sea rock, the tide line and driftwood", shore))


def sheet(out, title, kinds, folder):
    """A specimen sheet for any list of (name, fn -> Painting): every kind at the game's size, then at 2x, the rows
    packed to the sheet's width."""
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    t0 = time.time()
    dd = os.path.join(os.path.dirname(out), folder)
    os.makedirs(dd, exist_ok=True)
    paper = np.array(review.PAPER, np.float32)
    Wd, pad, gap = 1920, 12, 24
    made = []
    for name, fn in kinds:
        t1 = time.time()
        P = fn()
        big = np.clip(P.img, 0, 1)
        made.append((name, PT.tooth(P.shrunk(), 3), PT.tooth(big, 4), P.count, time.time() - t1))
        pngio.write_png(os.path.join(dd, name.split()[-1] + "_2x.png"), np.dstack([pngio.to_u8(made[-1][2]), np.full(big.shape[:2], 255, np.uint8)]))

    def head(text, h=22):
        hd = np.tile(paper, (h, Wd, 1)).astype(np.float32)
        review._label(hd, text[:300], 6, 5, scale=1)
        return hd

    def rows_of(idx):
        """The items packed left to right into as many rows as the width needs."""
        out_rows, cur, x = [], [], pad
        for m in made:
            wd = m[idx].shape[1]
            if cur and x + wd > Wd - pad:
                out_rows.append(cur)
                cur, x = [], pad
            cur.append(m)
            x += wd + gap
        if cur:
            out_rows.append(cur)
        res = []
        for items in out_rows:
            hmax = max(m[idx].shape[0] for m in items)
            r = np.tile(paper, (hmax + 2 * pad, Wd, 1)).astype(np.float32)
            x = pad
            for m in items:
                im = m[idx][:, :max(0, Wd - x)]
                r[pad + hmax - im.shape[0]:pad + hmax, x:x + im.shape[1]] = im
                x += im.shape[1] + gap
            res.append(head("  " + " | ".join(m[0] for m in items), 18))
            res.append(r)
        return res
    rows = [head(title, 26), head("AT THE GAME'S SIZE (64 px per metre):")] + rows_of(1) + [head("AT 2x (as painted):")] + rows_of(2)
    lines = ["WHAT EACH COST: " + "; ".join(f"{m[0]} {m[3]} dabs, {m[4]:.1f} s" for m in made),
             f"this run: {time.time() - t0:.0f} s. Files in {folder}/: " + ", ".join(m[0].split()[-1] + "_2x.png" for m in made)]
    foot = np.tile(paper, (24 + 16 * len(lines), Wd, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + title[:60] + " (lock-free, numpy; nothing exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


def preview(out):
    sheet(out, "B-248 (D-200): THE COAST'S KINDS in ART v6 (the plan's 11 and 12) - the form-following brush, the same ONE light, no drawn line. PREVIEW, nothing exported", KINDS, "b248_coast")


if __name__ == "__main__":
    preview(sys.argv[1])
