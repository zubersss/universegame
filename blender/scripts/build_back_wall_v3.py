"""B-230 (D-183, the owner: "the part that gets dug should look like a hole, not an opaque part"): the hole's back wall.

  terrain/<planet>/back_wall_t<n>   256x256 @ PPU 64 (4 m), tileable in x and y, n = 1..5 (Topsoil, Subsoil, Stone, Deep,
                                    Core), for earth / mars / mercury / venus: the dug cell's back face as cut earth seen in
                                    section, in the tier's own colours (taken from its exported ground_fill / ground_fill_t<n>
                                    and snapped to the planet's palette and its shadow tones), one step darker than the fill:
                                      T1 roots and worm holes   T2 pebbles and ore flecks   T3 strata lines and cracks
                                      T4 crystal seams + glints T5 dark glassy veins and a few embers
                                    Painted shapes with soft edges and paper grain; NO ink outline (it sits behind the fill;
                                    UNITY darkens it with depth and distance from the opening, U-196).
  (terrain/common/rim_shadow, a 256x64 ink fade for the dug edges, was exported with the walls and retired the same day:
   UNITY draws its own rim gradient. rim_shadow() below still paints it into the sheet's dug cells.)

  python -I build_back_wall_v3.py <review png> [planet]   the lock-free sheet per planet: each tier tiled 2x2 beside its
                                                          fill at 1x, and a 10 m shaft mock-up with the darkening painted in
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio, v3  # noqa: E402

ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
PLANETS = ("earth", "mars", "mercury", "venus")
TIER_NAMES = {1: "Topsoil", 2: "Subsoil", 3: "Stone", 4: "Deep", 5: "Core"}
S = 256                    # the tile (px), PPU 64 = 4 m
SS = 2                     # drawn at 2x, box-filtered down
N = S * SS


def keys():
    return [f"terrain/{p}/back_wall_t{t}" for p in PLANETS for t in range(1, 6)]


# ---------------------------------------------------------------- colours: the tier's fill snapped to the palette
def palette(planet):
    return {k: np.array(v3.hex_rgb(h), np.float32) / 255.0 for k, h in v3.palette_with_shadows(planet).items()}


def nearest(pal, c, avoid=()):
    best, bd = None, 1e9
    for k, v in pal.items():
        if k in avoid:
            continue
        dd = float(np.abs(v - c).sum())
        if dd < bd:
            best, bd = k, dd
    return best


def fill_png(planet, t):
    name = "ground_fill_color.png" if t == 1 else f"ground_fill_t{t}_color.png"
    p = os.path.join(ART, "terrain", planet, name)
    return pngio.read_png_np(p) if os.path.isfile(p) else None


def tier_colours(planet, t):
    """The fill's palette roles by share (opaque pixels snapped to the nearest palette tone), and the back wall's tones."""
    pal = palette(planet)
    img = fill_png(planet, t)
    if img is None:
        counts = {"brown_deep": 1.0}
    else:
        px = img[..., :3][img[..., 3] > 250].astype(np.float32) / 255.0
        px = px[:: max(1, len(px) // 20000)]
        names = list(pal)
        P = np.stack([pal[k] for k in names])
        idx = np.abs(px[:, None, :] - P[None, :, :]).sum(-1).argmin(-1)
        u, c = np.unique(idx, return_counts=True)
        counts = {names[i]: n / c.sum() for i, n in zip(u, c)}
    order = sorted(counts, key=lambda k: -counts[k])
    # rev (the 16:05 Earth sheet): snapping the wall to the NEAREST darker palette tone left the fill's hue - Stone's grey wall
    # came out teal, Subsoil's stayed the fill's own brown (brown is the palette's darkest tone but ink). The wall is now the
    # fill's own tones mixed toward ink, as the painted backdrops mix their darks (BG._mix(..., ink, t)): the same material,
    # one step darker
    main = order[0]
    others = [k for k in order[1:8] if k != "ink" and counts[k] >= 0.01]
    back = toward_ink(pal[main])                                          # T5's fill is mostly ink: its wall stays ink
    dark = toward_ink(back, 0.45)                                         # holes, cracks
    light = toward_ink(pal[main] * 0.55 + pal["offwhite"] * 0.45, 0.2)    # roots, strata lines: the main tone, paler
    accents = [toward_ink(pal[k]) for k in others[:3]] or [light]         # pebbles: the fill's other tones, as dark as the wall
    brightest = max(order[:8], key=lambda k: float(pal[k].max() - pal[k].min()) + float(pal[k].mean()) * 0.3)
    names = {"fill_main": main, "wall": f"{main} mixed {DARKEN:.2f} toward ink", "accents": others[:3], "bright": brightest}
    return pal, {"back": back, "dark": dark, "light": light, "accents": accents, "bright": toward_ink(pal[brightest], 0.15)}, names


INK = np.array(v3.hex_rgb(v3.INK), np.float32) / 255.0
DARKEN = 0.35              # the wall = the fill's tones mixed this far toward ink (UNITY's depth darkening multiplies on top)


def toward_ink(c, t=None):
    t = DARKEN if t is None else t
    return c * (1 - t) + INK * t


def quiet_roll(f):
    """Roll a periodic tile so its wrap falls on its quietest row and column (build_backdrop_v3.finish's lesson: a strata
    line that happened to lie on row 0 scored 3.81 on the seam check although the tile is continuous)."""
    ky = int(np.argmin(np.abs(f - np.roll(f, 1, axis=0)).sum(-1).mean(1)))
    f = np.roll(f, -ky, axis=0)
    kx = int(np.argmin(np.abs(f - np.roll(f, 1, axis=1)).sum(-1).mean(0)))
    return np.roll(f, -kx, axis=1)


# ---------------------------------------------------------------- periodic drawing at 2x
def pdist(X, cx, n=N):
    return (X - cx + n / 2) % n - n / 2


GRID = None


def grid():
    global GRID
    if GRID is None:
        GRID = np.mgrid[0:N, 0:N].astype(np.float32)
    return GRID


def ellipse(mask, cx, cy, rx, ry, rot=0.0, val=1.0, soft=1.5):
    Y, X = grid()
    dx, dy = pdist(X, cx), pdist(Y, cy)
    c, s = math.cos(rot), math.sin(rot)
    u, v = (dx * c + dy * s) / rx, (-dx * s + dy * c) / ry
    r = np.sqrt(u * u + v * v)
    np.maximum(mask, np.clip((1 - r) * min(rx, ry) / soft + 0.5, 0, 1) * val, out=mask)


def stroke(mask, pts, r0, r1=None, val=1.0):
    """A wrapped polyline of discs, radius r0 -> r1 along it (a tapering root, a vein)."""
    r1 = r0 if r1 is None else r1
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])) or 1.0
    run = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(2, int(L / 0.7))
        for i in range(n):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            r = r0 + (r1 - r0) * (run + L * t) / total
            k = int(math.ceil(r + 2))
            xs = (np.arange(int(x) - k, int(x) + k + 1)) % N
            ys = (np.arange(int(y) - k, int(y) + k + 1)) % N
            gx = np.arange(int(x) - k, int(x) + k + 1)[None, :] + 0.5 - x
            gy = np.arange(int(y) - k, int(y) + k + 1)[:, None] + 0.5 - y
            m = np.clip(r + 0.6 - np.sqrt(gx * gx + gy * gy), 0, 1) * val
            sub = mask[np.ix_(ys, xs)]
            mask[np.ix_(ys, xs)] = np.maximum(sub, m)
        run += L


def wander(rng, x, y, ang, steps, step, turn):
    pts = [(x, y)]
    for _ in range(steps):
        ang += rng.uniform(-turn, turn)
        x, y = x + math.cos(ang) * step, y + math.sin(ang) * step
        pts.append((x, y))
    return pts


def periodic_noise(rng, cells):
    """A smooth periodic noise field on the 2x grid (bilinear of a cells x cells random lattice)."""
    g = rng.standard_normal((cells, cells)).astype(np.float32)
    Y, X = grid()
    fx, fy = X / N * cells, Y / N * cells
    ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - ix, fy - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = g[iy % cells, ix % cells] * (1 - tx) + g[iy % cells, (ix + 1) % cells] * tx
    b = g[(iy + 1) % cells, ix % cells] * (1 - tx) + g[(iy + 1) % cells, (ix + 1) % cells] * tx
    return a * (1 - ty) + b * ty


def chip(mask, pts, val=1.0):
    """A filled polygon (even-odd) on the periodic 2x grid: an angular fragment."""
    xs_, ys_ = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = int(min(xs_)) - 1, int(max(xs_)) + 2, int(min(ys_)) - 1, int(max(ys_)) + 2
    X = np.arange(x0, x1)[None, :] + 0.5
    Y = np.arange(y0, y1)[:, None] + 0.5
    inside = np.zeros((y1 - y0, x1 - x0), bool)
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        if ay == by:
            continue
        inside ^= ((ay > Y) != (by > Y)) & (X < ax + (Y - ay) * (bx - ax) / (by - ay))
    ix = np.ix_(np.arange(y0, y1) % N, np.arange(x0, x1) % N)
    mask[ix] = np.maximum(mask[ix], inside * val)


def crack_net(rng, n, w):
    """Polygonal cracks on the periodic grid: the borders of n random cells (where the nearest and the second-nearest of n
    seeds are almost equally far), about w px wide at 2x."""
    Y, X = grid()
    d1 = np.full((N, N), 1e9, np.float32)
    d2 = np.full((N, N), 1e9, np.float32)
    seeds, tries = [], 0
    while len(seeds) < n and tries < 4000:                               # no two seeds within 96 px (2x): the first run had a
        tries += 1                                                       # near-coincident pair, and the whole cell between
        sx, sy = rng.uniform(0, N), rng.uniform(0, N)                    # them filled as "crack" (a dark polygon every 4 m)
        if all(math.hypot(pdist(sx, x), pdist(sy, y)) >= 96 for x, y in seeds):
            seeds.append((sx, sy))
    cell = np.zeros((N, N), np.int16)
    for i, (sx, sy) in enumerate(seeds):
        dd = np.hypot(pdist(X, sx), pdist(Y, sy))
        d2 = np.minimum(d2, np.maximum(d1, dd))
        cell[dd < d1] = i
        d1 = np.minimum(d1, dd)
    return np.clip(1.5 - (d2 - d1) / w, 0, 1), cell


def t1_marks(planet, rng, R):
    """The top tier's marks, per planet -> ([(mask, colour)], the crack polygons' cell index per pixel or None): Earth pale branching roots; Mars frost-crack polygons (some
    stretches holding frost) and short dry cracks; Mercury breccia chips (angular fragments in the regolith's tones); Venus
    thin sulfur threads. Earth's draws are in their accepted order (its tile is byte-identical)."""
    if planet == "earth":
        roots = np.zeros((N, N), np.float32)
        for _ in range(9):
            x, y = rng.uniform(0, N), rng.uniform(0, N)
            main = wander(rng, x, y, rng.uniform(1.2, 1.9), 22, rng.uniform(7, 11), 0.35)
            stroke(roots, main, rng.uniform(3.2, 4.6), 1.0)
            for j in range(2, len(main) - 4, 5):                          # side rootlets
                bx, by = main[j]
                stroke(roots, wander(rng, bx, by, rng.uniform(0, math.tau), 8, 5, 0.6), 1.8, 0.6)
        return [(roots, R["light"])], None
    if planet == "mars":
        net, cell = crack_net(rng, 12, 2.2)
        frost = np.clip(periodic_noise(rng, 6) * 1.5, 0, 1)
        dry = np.zeros((N, N), np.float32)
        for _ in range(5):
            stroke(dry, wander(rng, rng.uniform(0, N), rng.uniform(0, N), rng.uniform(0, math.tau), 9, 8, 0.7), 1.8, 0.6)
        return [(net * 0.85, R["dark"]), (net * frost, R["light"]), (dry, R["dark"])], cell
    if planet == "mercury":
        tones = [R["light"], R["light"]] + R["accents"][:2]
        masks = [np.zeros((N, N), np.float32) for _ in tones]
        placed, tries, i = [], 0, 0
        while len(placed) < 22 and tries < 6000:                         # rev: larger (4-12 px at 1x; the first read as
            tries += 1                                                   # confetti), four to six corners (a triangle is an
            cx, cy, r = rng.uniform(0, N), rng.uniform(0, N), 8 + 16 * rng.uniform() ** 1.6   # arrowhead), none near another
            i = len(placed) % len(tones)                                 # (two tip to tip made a bow), and no two DARK chips
            dark = i >= 2                                                # within 60 px at 1x (two side by side over a pit: a face)
            if any(math.hypot(pdist(cx, x), pdist(cy, y)) < max(r + q + 30, 120 if dark and d else 0) for x, y, q, d in placed):
                continue
            placed.append((cx, cy, r, dark))
            k, a0 = int(rng.integers(4, 7)), rng.uniform(0, math.tau)
            pts = []
            for j in range(k):
                a, rr = a0 + math.tau * j / k + rng.uniform(-0.3, 0.3), r * rng.uniform(0.55, 1.0)
                pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
            chip(masks[i % len(tones)], pts, 0.9)
        return list(zip(masks, tones)), None
    th = np.zeros((N, N), np.float32)                                    # venus
    for _ in range(7):
        pts = wander(rng, rng.uniform(0, N), rng.uniform(0, N), rng.uniform(-0.35, 0.35), 26, 11, 0.28)
        stroke(th, pts, 1.5, 1.1)
        if rng.uniform() < 0.5:                                          # a short side thread
            bx, by = pts[int(rng.integers(6, 20))]
            stroke(th, wander(rng, bx, by, rng.uniform(0.6, 1.2) * (1 if rng.uniform() < 0.5 else -1), 7, 8, 0.3), 1.1, 0.7)
    return [(th, R["bright"])], None


# ---------------------------------------------------------------- the tiers
def draw_tier(planet, t):
    """-> (RGBA uint8 256x256, the roles used)."""
    pal, R, names = tier_colours(planet, t)
    rng = np.random.default_rng(23000 + 100 * PLANETS.index(planet) + t)
    layers = []                                                          # (mask, colour) painted in order over the back tone
    if t == 1:                                                           # the top tier, per planet (LEAD 17:2x: roots are
        marks, cell_of = t1_marks(planet, rng, R)                        # Earth's alone; no roots on a lifeless planet)
        holes, rims = np.zeros((N, N), np.float32), np.zeros((N, N), np.float32)   # Earth: worm holes; elsewhere: vesicles
        earth = planet == "earth"                                        # Earth's numbers are its accepted tile's (byte-identical)
        near, lvl_dy, lvl_dx, count, cap = {"earth": (70, 26, 120, 9, 800),       # Venus: four, 75 px apart (kept off its threads,
                                            "venus": (150, 40, 180, 4, 8000)}.get(planet, (90, 40, 180, 6, 8000))   # six bunched
        #                                                                  in the one open patch: three in a triangle, a face)

        def too_near(cx, cy):
            """Earth: within 35 px (1x) of another hole, or level with one (within 13 px of its height and 60 px to its side):
            two ringed dots side by side read as a pair of eyes (D-101). The lifeless planets: 45 px, 20 px and 90 px, and six
            pits for nine (17:22's sheets at 3x: two level pits 62 px apart over a third read as a face). Distances wrap."""
            for x, y in spots:
                dx, dy = abs((cx - x + N / 2) % N - N / 2), abs((cy - y + N / 2) % N - N / 2)
                if math.hypot(dx, dy) < near or (dy < lvl_dy and dx < lvl_dx):
                    return True
            return False
        spots, tries, used = [], 0, set()
        busy = None if earth else np.maximum.reduce([m for m, _ in marks])   # a pit on a crack's corner read as a rivet, on a
        while len(spots) < count and tries < cap:                         # thread as a bead, beside a chip as an eye; two pits in
            tries += 1                                                    # one crack polygon as eyes in a head
            cx, cy, r = rng.uniform(0, N), rng.uniform(0, N), rng.uniform(5, 10)
            if too_near(cx, cy):
                continue
            if busy is not None:                                          # clear of a crack by 4 px (1x), of a chip by 26 (a dark
                k = int(r) + {"mercury": 52, "venus": 44}.get(planet, 9)   # chip beside a pit: a pair), of a thread by 22 (a pit
                #                                                           between two threads: an eye)
                if busy[np.ix_(np.arange(int(cy) - k, int(cy) + k + 1) % N, np.arange(int(cx) - k, int(cx) + k + 1) % N)].max() > 0.25:
                    continue
            if cell_of is not None:
                c = int(cell_of[int(cy) % N, int(cx) % N])
                if c in used:
                    continue
                used.add(c)
            spots.append((cx, cy))
            ellipse(rims, cx, cy, r + 3, r * 0.8 + 3, rng.uniform(0, 3))
            ellipse(holes, cx, cy, r, r * 0.8, rng.uniform(0, 3))
        layers += marks + [(rims, R["light"]), (holes, R["dark"])]
    elif t == 2:                                                         # Subsoil: pebbles and ore flecks
        lit = np.zeros((N, N), np.float32)                               # rev: larger pebbles (5-11 px at 1x; the first read
        for k, col in enumerate(R["accents"][:3] + [R["light"]]):        # as a rash of specks), each with a lit top
            peb = np.zeros((N, N), np.float32)
            for _ in range(7 - k):
                cx, cy, rx, ry, rot = rng.uniform(0, N), rng.uniform(0, N), rng.uniform(10, 22), rng.uniform(7, 14), rng.uniform(-0.5, 0.5)
                ellipse(peb, cx, cy, rx, ry, rot)
                ellipse(lit, cx - rx * 0.15, cy - ry * 0.35, rx * 0.55, ry * 0.35, rot, val=0.45)
            layers.append((peb, col))
        layers.append((lit, R["light"]))
        fl = np.zeros((N, N), np.float32)
        for _ in range(24):
            ellipse(fl, rng.uniform(0, N), rng.uniform(0, N), rng.uniform(1.5, 3), rng.uniform(1.2, 2.2), rng.uniform(0, 3))
        layers.append((fl, R["bright"]))
    elif t == 3:                                                         # Stone: strata lines and cracks
        Y, X = grid()
        for k, col in enumerate((R["light"], R["dark"], R["light"], R["dark"], R["light"])):   # rev: five thin strata LINES
            y0 = (k + rng.uniform(0.2, 0.8)) * N / 5                    # (1.6-3 px at 1x), spread down the tile; the first
            wave = sum(rng.uniform(2, 6) * np.sin(2 * math.pi * (h * X / N + rng.uniform(0, 1))) for h in (1, 2, 3))   # three were
            band = np.clip(1.6 - np.abs(pdist(Y, y0) - wave) / rng.uniform(1.0, 1.9), 0, 1) * 0.8             # 14 px bands: a pipe
            layers.append((band, col))
        cr = np.zeros((N, N), np.float32)
        for _ in range(6):
            stroke(cr, wander(rng, rng.uniform(0, N), rng.uniform(0, N), rng.uniform(0.6, 2.4), 14, 9, 0.9), 2.2, 0.8)
        layers.append((cr, R["dark"]))
    elif t == 4:                                                         # Deep: crystal seams and glints
        seams, glints = np.zeros((N, N), np.float32), np.zeros((N, N), np.float32)
        for _ in range(7):
            x, y, a = rng.uniform(0, N), rng.uniform(0, N), rng.uniform(0, math.pi)
            pts = [(x, y)]
            for _j in range(6):                                          # angular: straight runs with sharp turns
                a += rng.choice([-0.7, 0.5, 0.0, 0.9])
                L = rng.uniform(18, 40)
                x, y = x + math.cos(a) * L, y + math.sin(a) * L
                pts.append((x, y))
            stroke(seams, pts, 2.6, 1.4)
            if _ % 2 == 0:                                               # LEAD 17:1x: a spark ON a facet of every other seam
                cx, cy = pts[int(rng.integers(1, 4))]                    # (four a tile), none loose in the field: sixteen
                r = rng.uniform(4, 6.5)                                  # scattered ones with the gold zig-zags read as a night
                ellipse(glints, cx, cy, r, 1.2, 0.0)                     # sky with constellations
                ellipse(glints, cx, cy, 1.2, r, 0.0)
        layers += [(seams, R["bright"]), (glints, toward_ink(pal["offwhite"], 0.2))]
    else:                                                                # Core: dark glassy veins, a few embers
        veins, gloss, emb = np.zeros((N, N), np.float32), np.zeros((N, N), np.float32), np.zeros((N, N), np.float32)
        for _ in range(6):                                               # rev: straighter dark-teal glass with a thin lit edge
            pts = wander(rng, rng.uniform(0, N), rng.uniform(0, N), rng.uniform(0, math.tau), 12, 14, 0.28)   # (the first were
            stroke(veins, pts, 5.0, 2.0)                                                                       # brown squiggles:
            stroke(gloss, [(x - 1.5, y - 1.5) for x, y in pts[1:-3]], 0.9, 0.4)                               # worms)
        for _ in range(10):
            ellipse(emb, rng.uniform(0, N), rng.uniform(0, N), rng.uniform(1.8, 3.2), rng.uniform(1.5, 2.6))
        glass = toward_ink(pal["teal"], 0.5)
        layers += [(veins, glass), (gloss, toward_ink(pal["sky"], 0.3)), (emb, pal["red"])]
    out = np.broadcast_to(R["back"], (N, N, 3)).copy()
    for m, col in layers:
        out = out * (1 - m[..., None]) + col[None, None, :] * m[..., None]
    small = out.reshape(S, SS, S, SS, 3).mean(axis=(1, 3))
    grain = periodic_noise(rng, 64)[::SS, ::SS] * 0.6 + periodic_noise(rng, 16)[::SS, ::SS] * 0.4
    small = quiet_roll(small * (1 + 0.035 * grain[..., None]))
    img = np.dstack([np.clip(np.rint(small * 255), 0, 255).astype(np.uint8), np.full((S, S), 255, np.uint8)])
    return img, names


def rim_shadow():
    rng = np.random.default_rng(23999)
    H = 64
    x = np.arange(S) / S
    foot = 46 + sum(rng.uniform(2, 5) * np.sin(2 * math.pi * (h * x + rng.uniform(0, 1))) for h in (2, 5, 9))   # a ragged foot
    y = np.arange(H, dtype=np.float32)[:, None]
    a = 0.55 * np.clip(1 - y / foot[None, :], 0, 1) ** 1.6
    ink = np.array(v3.hex_rgb(v3.INK), np.uint8)
    img = np.zeros((H, S, 4), np.uint8)
    img[..., :3] = ink
    img[..., 3] = np.clip(np.rint(a * 255), 0, 255).astype(np.uint8)
    return img


def seam_score(img):
    f = img[..., :3].astype(np.float32)
    inter = max(float(np.abs(np.diff(f, axis=1)).mean()), 0.5)
    return float(np.abs(f[:, -1] - f[:, 0]).mean() / inter), float(np.abs(f[-1] - f[0]).mean() / max(float(np.abs(np.diff(f, axis=0)).mean()), 0.5))


# ---------------------------------------------------------------- export
def export(art):
    out = []
    for planet in PLANETS:
        for t in range(1, 6):
            img, R = draw_tier(planet, t)
            sx, sy = seam_score(img)
            if max(sx, sy) > 1.6:
                raise ValueError(f"B-230 checks: {planet} t{t} seam {sx:.2f} / {sy:.2f}")
            base = os.path.join(art, "terrain", planet, f"back_wall_t{t}")
            n = pngio.write_png(base + "_color.png", img)
            with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
                json.dump({"key": f"terrain/{planet}/back_wall_t{t}", "style": "v3", "width": S, "height": S, "ppu": 64, "palette": planet,
                           "tile_x": True, "tile_y": True, "tier": t, "tier_name": TIER_NAMES[t], "roles": R,
                           "note": "B-230 (D-183): the dug cell's back face as cut earth, one step darker than the tier's fill; no ink "
                                   "outline; UNITY darkens it with depth and distance from the opening (U-196)"}, f, indent=2)
                f.write("\n")
            out.append((f"terrain/{planet}/back_wall_t{t}", S, S, n))
    # terrain/common/rim_shadow is no longer exported (LEAD 18:2x: UNITY keeps its own rim gradient, no draw call, so the strip
    # was imported but unused); rim_shadow() stays for the sheet's mock-up of a dug cell
    return out


# ---------------------------------------------------------------- the review sheet
def preview(out, planet="earth", footnote=None):
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    paper = np.array(review.PAPER, np.float32)
    rows, lines = [], []
    W = 1600
    head = np.tile(paper, (28, W, 1)).astype(np.float32)
    review._label(head, f"B-230 {planet}: each tier's back wall tiled 2x2 (8 m) beside its fill at 1x, then a cell dug out of the fill", 6, 8)
    rows.append(head)
    prof = (rim_shadow().astype(np.float32) / 255.0)[..., 3].mean(axis=1)                 # the rim shadow's mean profile (64)

    def tiled(img, h, w):
        f = img[..., :3].astype(np.float32) / 255.0
        return np.tile(f, (-(-h // f.shape[0]), -(-w // f.shape[1]), 1))[:h, :w]

    def dug(fill, wall, x0, y0, x1, y1, open_top=False):
        """The hole (x0..x1, y0..y1) cut in the fill: the wall darkened with depth below the opening (y0) and away from the hole's
        centre line (U-196's ambient, painted in roughly), the rim shadow on every dug edge (not the open top)."""
        out = fill.copy()
        H, Wd = fill.shape[:2]
        yy = np.arange(H, dtype=np.float32)[:, None]
        xx = np.arange(Wd, dtype=np.float32)[None, :]
        depth = np.clip((yy - y0) / 64.0, 0, None)
        side = np.abs(xx - (x0 + x1) / 2) / max((x1 - x0) / 2, 1)
        dk = np.clip(1.0 - 0.075 * depth, 0.55, 1.0) * (1.0 - 0.12 * side)                 # U-196: to 55 % at 6 m
        out[y0:y1, x0:x1] = (wall * dk[..., None])[y0:y1, x0:x1]
        n, sh = len(prof), np.zeros((H, Wd), np.float32)
        for k in range(n):
            if x0 + k < x1:
                sh[y0:y1, x0 + k] = np.maximum(sh[y0:y1, x0 + k], prof[k])
            if x1 - 1 - k >= x0:
                sh[y0:y1, x1 - 1 - k] = np.maximum(sh[y0:y1, x1 - 1 - k], prof[k])
            if y1 - 1 - k >= y0:
                sh[y1 - 1 - k, x0:x1] = np.maximum(sh[y1 - 1 - k, x0:x1], prof[k])
            if not open_top and y0 + k < y1:
                sh[y0 + k, x0:x1] = np.maximum(sh[y0 + k, x0:x1], prof[k])
        out[y0:y1, x0:x1] *= (1 - sh[y0:y1, x0:x1, None])
        return out

    walls = {}
    for t in range(1, 6):
        img, R = draw_tier(planet, t)
        walls[t] = img
        sx, sy = seam_score(img)
        lines.append(f"t{t} {TIER_NAMES[t]}: fill mostly {R['fill_main']}; wall = {R['wall']}; pebbles / accents from {', '.join(R['accents']) or '-'}; bright {R['bright']}; seam x {sx:.2f} y {sy:.2f}")
        r = np.tile(paper, (548, W, 1)).astype(np.float32)
        review._label(r, f"t{t} {TIER_NAMES[t]}: the back wall 2x2 | the fill | a 3 m x 5 m cell dug out of it", 6, 4, scale=1)
        r[24:24 + 2 * S, 10:10 + 2 * S] = tiled(img, 2 * S, 2 * S)
        fill = fill_png(planet, t)
        if fill is not None:
            ft = tiled(fill, 2 * S, 2 * S)
            r[24:24 + 2 * S, 30 + 2 * S:30 + 4 * S] = ft
            r[24:24 + 2 * S, 50 + 4 * S:50 + 6 * S] = dug(ft, tiled(img, 2 * S, 2 * S), 160, 96, 352, 416)
        rows.append(r)
    r = np.tile(paper, (3 * S + 34, W, 1)).astype(np.float32)                                  # LEAD 17:1x: the pair check seen
    review._label(r, "t1 at 3x, one whole tile: its marks (earth roots, mars frost-crack polygons, mercury breccia chips, venus sulfur threads) and pits (none within 35 px of another, none level within 60 px: D-101) | t4 at 3x: every glint on a seam", 6, 4, scale=1)
    for i, t in enumerate((1, 4)):
        big = np.repeat(np.repeat(walls[t][..., :3].astype(np.float32) / 255.0, 3, 0), 3, 1)
        r[24:24 + 3 * S, 10 + i * (3 * S + 14):10 + i * (3 * S + 14) + 3 * S] = big
    rows.append(r)
    fill1 = fill_png(planet, 1)                                                                # a 10 m shaft (640 px) from the surface
    if fill1 is not None:
        r = np.tile(paper, (800, W, 1)).astype(np.float32)
        review._label(r, "a 10 m shaft, 2 m wide, dug from the surface through the topsoil: the back wall darkening with depth, the rim shadow on its sides and floor", 6, 4, scale=1)
        sky = np.array(v3.hex_rgb(v3.PALETTES[planet]["sky"]), np.float32) / 255.0
        scene = np.empty((760, W - 20, 3), np.float32)
        scene[:80] = sky
        scene[80:] = tiled(fill1, 680, W - 20)
        scene = dug(scene, tiled(walls[1], 760, W - 20), 736, 80, 864, 720, open_top=True)
        r[24:784, 10:W - 10] = scene
        rows.append(r)
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-230 design preview (lock-free, numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_back_wall_v3.py <review png> [planet]
    preview(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "earth")
