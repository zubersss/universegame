"""B-133: Earth biome backdrops in the B-114 manner (contract §11.4, Bible §9.1 backgrounds): painted watercolour
layer sets for the forest and the coast, backgrounds/earth/forest/layer0..2 and backgrounds/earth/coast/layer0..2
+ <scene>.json (SceneLayout), the plains set unchanged. numpy only (gen_painted_bg's washes, ridges and paper);
every shape and noise is periodic in x, so each layer tiles at 2048. No ink outlines, nothing face-like.

  forest  layer0 2048x1024  sky, clouds, two far ridges fringed with pale conifers and round crowns
          layer1 2048x640   the tree line: trunks under round crowns and tiered conifers, a shaded understorey
          layer2 2048x384   near undergrowth: bushes, arching fern fronds, a stump and a log, bluebell dots
  coast   layer0 2048x1024  sky, clouds, the sea to the horizon with a pale headland and sparkle dabs
          layer1 2048x512   nearer sea with foam crests, a grassy cliff headland and two sea stacks
          layer2 2048x384   dunes with marram tufts, pebbles, shells and driftwood

Folders follow the contract and ParallaxLayers.ConfigureFor(planet, scene): backgrounds/<planet>/<scene>/.
  python -I build_backdrop_v3.py <preview dir>      lock-free previews (1080p composite + 2x seam check)
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_painted_bg as BG  # noqa: E402
from meridian import v3  # noqa: E402

W = BG.W


def _pal(planet="earth"):
    return {k: BG._rgb(v) for k, v in v3.PALETTES[planet].items()}


def wash32(rng, H, mask, colour, **kw):
    """gen_painted_bg.wash cast to float32 at once: a layer holds up to six washes, so this halves the peak (the
    accepted plains export keeps its float64 path untouched)."""
    rgb, m = BG.wash(rng, H, mask, colour, **kw)
    return rgb.astype(np.float32), m.astype(np.float32)


# ---------------------------------------------------------------- stamps (bounding-box only, wrapped in x)

def ell(mask, cx, cy, rx, ry, val=1.0, cut=None):
    """A filled ellipse; cut = keep only rows above cy + cut * ry (a flat-bottomed blob)."""
    H = mask.shape[0]
    y0, y1 = max(int(cy - ry) - 1, 0), min(int(cy + ry) + 2, H)
    if y0 >= y1:
        return
    xs = np.arange(int(cx - rx) - 1, int(cx + rx) + 2)
    ys = np.arange(y0, y1)[:, None] + 0.5
    inside = ((xs[None, :] + 0.5 - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 <= 1
    if cut is not None:
        inside &= ys < cy + cut * ry
    cols = xs % W
    mask[y0:y1, cols] = np.maximum(mask[y0:y1][:, cols], inside * val)


def tri(mask, cx, top, base, hw, val=1.0, droop=0.0):
    """A triangle (apex up) from row top to row base, half-width hw at the base; droop bows the sides out."""
    H = mask.shape[0]
    for y in range(max(int(top), 0), min(int(base) + 1, H)):
        t = (y - top) / max(base - top, 1)
        half = hw * (t + droop * math.sin(math.pi * t))
        xs = np.arange(int(cx - half), int(cx + half) + 1) % W
        mask[y, xs] = val


def rect(mask, x0, x1, y0, y1, val=1.0):
    H = mask.shape[0]
    xs = np.arange(int(x0), int(x1) + 1) % W
    mask[max(int(y0), 0):min(int(y1), H), xs] = val


def conifer(mask, cx, base, height, width, tiers=3):
    """Tiered fir: overlapping drooping triangles, each tier a little narrower."""
    for k in range(tiers):
        top = base - height + k * height * 0.22
        bot = base - height * (0.55 - 0.18 * k) if k < tiers - 1 else base
        tri(mask, cx, top, bot, width * (0.55 + 0.22 * k), droop=0.12)


def dab(mask, cx, cy, L, ang, w=1):
    """A short brush dab (grass blade, frond leaflet) from (cx, cy) upward at angle ang (rad from vertical)."""
    H = mask.shape[0]
    for t in np.linspace(0, 1, max(int(L / 2), 4)):
        px, py = (cx + math.sin(ang) * L * t) % W, cy - math.cos(ang) * L * t
        if 0 <= py < H:
            mask[max(int(py) - w, 0):int(py) + w + 1, int(px) % W] = 1.0


def frond(mask, cx, cy, L, ang, bend):
    """An arching fern frond: a curved rib with leaflet dabs on both sides."""
    pts = []
    for t in np.linspace(0, 1, int(L / 3)):
        a = ang + bend * t
        if not pts:
            pts.append((cx, cy))
        x, y = pts[-1]
        pts.append((x + math.sin(a) * 3, y - math.cos(a) * 3))
    for i, (x, y) in enumerate(pts):
        mask[int(y) % mask.shape[0], int(x) % W] = 1.0
        if i % 2 == 0 and 0 < i < len(pts) - 2:
            s = 1 - i / len(pts)
            for side in (-1, 1):
                dab(mask, x, y, 8 * s + 3, ang + bend * i / len(pts) + side * 1.1, w=1)


def seam_column(q):
    """The column k (0..W-1) whose step from column k-1 is the smallest (premultiplied, on the 8-bit image): putting
    the wrap there keeps an object edge off the tile seam. q: H x W x 4 uint8."""
    f = q[..., :3].astype(np.float32) * (q[..., 3:4].astype(np.float32) / 255)
    step = np.abs(f - np.roll(f, 1, axis=1)).sum(-1).mean(0)
    return int(np.argmin(step))


class Stack:
    """Composites each wash as it is appended (gen_painted_bg._composite's formula and order), so a layer holds one
    rgb + alpha instead of six washes: the B-141 Mars sets use it (the Earth sets keep their lists, unchanged)."""
    def __init__(self, items=()):
        self.rgb = self.a = None
        for it in items:
            self.append(it)

    def append(self, item):
        c, m = item
        if self.rgb is None:
            self.rgb, self.a = np.zeros(c.shape, np.float32), np.zeros(m.shape, np.float32)
        self.rgb = c * m[..., None] + self.rgb * (1 - m[..., None])
        self.a = m + self.a * (1 - m)

    def paint(self, item):
        """Paint colour onto the surface already composited, leaving the alpha as it is (the rgb holds colour x
        alpha, so the paint is scaled by the alpha under it): light-dependent strokes on a Uranus deck must not
        change a layer's alpha, or the season crossfade morphs a silhouette (D-142)."""
        c, m = item
        self.rgb = c * (m * self.a)[..., None] + self.rgb * (1 - m[..., None])


def finish(stack, rng, H, straight=True, roll=None):
    """Composite + paper grain, then roll the (periodic) layer so the wrap sits on the quietest column: a soft edge
    that happened to fall on column 0 scored 2.7 on the seam check although the tile is continuous.
    straight: the composite over a transparent base holds colour x alpha (premultiplied), but the PNG is read as
    straight alpha (ParallaxLayer.shader: Blend SrcAlpha OneMinusSrcAlpha; review._over), so translucent shapes
    darken twice (offwhite fog wisps read as grey streaks, soft edges get dark rims). straight=True divides the alpha
    back out (BG.straighten; opaque pixels untouched, so every layer0 stays byte-identical). D-147: the default for
    every layer (the exporter was at fault; the contract §3 says straight alpha)."""
    rgb, a = (stack.rgb, stack.a) if isinstance(stack, Stack) else BG._composite(stack)
    if straight:
        rgb = BG.straighten(rgb, a)
    rgb = rgb * BG.paper(rng, H)[..., None]
    k = seam_column(BG.to_u8(rgb, a)) if roll is None else int(roll) % W      # roll: a fixed wrap (Uranus: one per deck, D-142)
    return np.roll(rgb, -k, axis=1), np.roll(a, -k, axis=1)


def geometry_roll(mask):
    """The wrap column from a light-independent mask (the lit variants of one deck must roll alike, or the season
    crossfade slides the clouds)."""
    m = np.repeat(np.clip(mask, 0, 1)[..., None], 3, axis=2)
    return seam_column(BG.to_u8(m, np.ones(mask.shape, np.float32)))


def sky_layer(rng, pal, H=1024, clouds=7):
    yy = (np.arange(H) / H)[:, None, None]
    sky = BG._mix(pal["sky"], BG._mix(pal["sky"], pal["offwhite"], 0.55), np.clip(yy * 1.2, 0, 1))
    sky = sky * (1 + 0.04 * BG.periodic_noise(rng, H, 140, 80)[..., None])
    stack = [(np.broadcast_to(sky, (H, W, 3)).astype(np.float32), np.ones((H, W), np.float32))]
    cm = np.zeros((H, W), np.float32)
    for k in range(clouds):
        cx, cy = rng.uniform(0, W), rng.uniform(140, 480)
        for j in range(5):
            ell(cm, cx + rng.uniform(-150, 150), cy + rng.uniform(-30, 25), rng.uniform(70, 150), rng.uniform(35, 60), cut=0.55)
    stack.append(wash32(rng, H, cm, pal["offwhite"], var=0.03, edge_dark=0.06, bleed=5.0))
    return stack


# ---------------------------------------------------------------- forest

def earth_forest(seed):
    rng = np.random.default_rng(seed)
    pal = _pal()
    out = []
    # layer0: sky, clouds, two far ridges fringed with pale trees (aerial perspective: paler = farther)
    H = 1024
    stack = sky_layer(rng, pal, H, clouds=6)
    for base, amp, col, n, hmax in ((735, 55, BG._mix(pal["teal"], pal["sky"], 0.68), 150, 34),
                                    (835, 45, BG._mix(BG._mix(pal["green"], pal["teal"], 0.5), pal["sky"], 0.45), 120, 52)):
        line = BG.ridge(rng, [(1, 0.5), (3, 0.35), (6, 0.15)], base=base, amp=amp)
        m = BG._ridge_mask(H, line)
        for k in range(n):
            cx = (k + rng.uniform(-0.4, 0.4)) * W / n
            top = line[int(cx) % W]
            if rng.uniform() < 0.6:
                h = rng.uniform(0.5, 1.0) * hmax
                tri(m, cx, top - h, top + 4, h * 0.32, droop=0.1)
            else:
                r = rng.uniform(0.35, 0.6) * hmax
                ell(m, cx, top - r * 0.5, r * 0.8, r * 0.75)
        stack.append(wash32(rng, H, m, col, var=0.05, edge_dark=0.07, bleed=2.5))
    out.append(finish(stack, rng, H))

    # layer1: the tree line, 640 tall: understorey band, trunks, round crowns and tiered firs, crown shade
    H = 640
    floor = BG.ridge(rng, [(2, 0.5), (5, 0.3), (11, 0.12)], base=520, amp=18)
    under = BG._ridge_mask(H, floor - 40)
    trunks = np.zeros((H, W), np.float32)
    crowns = np.zeros((H, W), np.float32)
    firs = np.zeros((H, W), np.float32)
    n = 22
    for k in range(n):
        cx = (k + rng.uniform(-0.3, 0.3)) * W / n
        base = floor[int(cx) % W]
        if k % 3 == 1:                                          # a fir
            h = rng.uniform(260, 380)
            rect(trunks, cx - 5, cx + 5, base - 60, base + 6)
            conifer(firs, cx, base - 40, h, rng.uniform(70, 95))
        else:                                                   # a round deciduous crown on a trunk
            th = rng.uniform(150, 230)
            tw = rng.uniform(8, 13)
            rect(trunks, cx - tw, cx + tw, base - th, base + 6)
            cy = base - th - rng.uniform(30, 60)
            for j in range(5):
                ell(crowns, cx + rng.uniform(-60, 60), cy + rng.uniform(-50, 30), rng.uniform(55, 85), rng.uniform(45, 70))
    shade = crowns * (np.arange(H)[:, None] > (floor[None, :] - 290)).astype(np.float32)
    dapple = np.zeros((H, W), np.float32)
    for k in range(60):
        cx = rng.uniform(0, W)
        cy = rng.uniform(150, 380)
        ell(dapple, cx, cy, rng.uniform(6, 12), rng.uniform(4, 8))
    dapple *= crowns
    stack = [wash32(rng, H, under, BG._mix(pal["green"], pal["brown"], 0.35), var=0.06, edge_dark=0.06),
             wash32(rng, H, trunks, BG._mix(pal["brown"], pal["green"], 0.25), var=0.06, edge_dark=0.12, bleed=1.5),
             wash32(rng, H, firs, BG._mix(pal["teal"], pal["green"], 0.35), var=0.06, edge_dark=0.10, bleed=2.0),
             wash32(rng, H, crowns, BG._mix(pal["green"], pal["teal"], 0.25), var=0.07, edge_dark=0.10, bleed=2.5),
             wash32(rng, H, shade, BG._mix(pal["green"], pal["brown"], 0.30), var=0.05, edge_dark=0.04, bleed=6.0),
             wash32(rng, H, dapple, BG._mix(pal["green"], pal["mustard"], 0.45), var=0.04, edge_dark=0.03, bleed=2.0)]
    out.append(finish(stack, rng, H))

    # layer2: near undergrowth, 384 tall: bushes, fern fronds, a stump and a log, bluebells
    H = 384
    line = BG.ridge(rng, [(3, 0.5), (7, 0.3), (15, 0.1)], base=200, amp=22)
    ground = BG._ridge_mask(H, line)
    bush = np.zeros((H, W), np.float32)
    for k in range(34):
        cx = rng.uniform(0, W)
        top = line[int(cx) % W]
        for j in range(3):
            ell(bush, cx + rng.uniform(-40, 40), top + rng.uniform(-10, 25), rng.uniform(28, 55), rng.uniform(22, 40))
    fern = np.zeros((H, W), np.float32)
    for k in range(40):
        cx = rng.uniform(0, W)
        cy = line[int(cx) % W] + rng.uniform(15, 60)
        for j in range(5):
            frond(fern, cx, cy, rng.uniform(40, 75), -1.0 + 0.5 * j + rng.uniform(-0.15, 0.15), bend=(0.8 if j < 2 else -0.8 if j > 2 else 0.0))
    wood = np.zeros((H, W), np.float32)
    rings = np.zeros((H, W), np.float32)
    sx = rng.uniform(300, 700)
    sb = line[int(sx) % W] + 40
    rect(wood, sx - 34, sx + 34, sb - 70, sb + 10)                 # a stump with a flat cut top
    ell(rings, sx, sb - 70, 32, 9)
    lx = sx + 1000
    lb = line[int(lx) % W] + 55
    rect(wood, lx - 130, lx + 120, lb - 38, lb)                    # a fallen log, end grain to the right
    ell(rings, lx + 120, lb - 19, 13, 19)
    bells = np.zeros((H, W), np.float32)
    for k in range(60):
        cx = rng.uniform(0, W)
        ell(bells, cx, line[int(cx) % W] + rng.uniform(25, 140), rng.uniform(2.5, 4.5), rng.uniform(3, 5))
    stack = [wash32(rng, H, ground, BG._mix(pal["green"], pal["brown"], 0.30), var=0.07, edge_dark=0.08),
             wash32(rng, H, bush * np.maximum(ground, 0.0) + bush * (1 - ground), BG._mix(pal["green"], pal["teal"], 0.30), var=0.07, edge_dark=0.10, bleed=2.0),
             wash32(rng, H, fern, BG._mix(pal["green"], pal["mustard"], 0.25), var=0.06, edge_dark=0.05, bleed=0.9),
             wash32(rng, H, wood, BG._mix(pal["brown"], pal["mustard"], 0.25), var=0.06, edge_dark=0.14, bleed=1.2),
             wash32(rng, H, rings, BG._mix(pal["mustard"], pal["offwhite"], 0.4), var=0.04, edge_dark=0.18, bleed=1.0),
             wash32(rng, H, bells * ground, BG._mix(pal["sky"], pal["teal"], 0.35), var=0.05, edge_dark=0.10, bleed=1.0)]
    out.append(finish(stack, rng, H))
    layers = [{"n": 0, "parallax": 0.1, "y_m": -2.0}, {"n": 1, "parallax": 0.35, "y_m": -1.0},
              {"n": 2, "parallax": 0.6, "y_m": -0.5}]
    return out, layers


# ---------------------------------------------------------------- coast

def earth_coast(seed):
    rng = np.random.default_rng(seed)
    pal = _pal()
    out = []
    # layer0: sky, clouds, the sea to a horizon at row 760, a pale headland, sparkle dabs
    H = 1024
    stack = sky_layer(rng, pal, H, clouds=7)
    hz = 760
    x = np.arange(W) / W
    bump = 70 * np.exp(-((np.minimum(np.abs(x - 0.3), 1 - np.abs(x - 0.3))) / 0.07) ** 2) + \
        30 * np.exp(-((np.minimum(np.abs(x - 0.78), 1 - np.abs(x - 0.78))) / 0.04) ** 2)
    land = BG._ridge_mask(H, hz - bump + 2) * (np.arange(H)[:, None] < hz + 3)
    stack.append(wash32(rng, H, land, BG._mix(pal["teal"], pal["sky"], 0.70), var=0.04, edge_dark=0.05, bleed=2.0))
    sea = BG._ridge_mask(H, np.full(W, float(hz)), soft=1.0)
    yy = np.clip((np.arange(H)[:, None] - hz) / (H - hz), 0, 1)
    seacol = BG._mix(pal["teal"], pal["sky"], 0.45)
    srgb, sa = wash32(rng, H, sea, seacol, var=0.04, edge_dark=0.02, bleed=1.0)
    srgb = srgb * (1 - 0.12 * yy[..., None])                              # deeper toward the viewer
    stack.append((srgb, sa))
    spark = np.zeros((H, W), np.float32)
    for k in range(140):
        cx, cy = rng.uniform(0, W), rng.uniform(hz + 8, H - 20)
        L = rng.uniform(6, 22) * (0.5 + (cy - hz) / (H - hz))
        rect(spark, cx - L, cx + L, cy, cy + 2)
    stack.append(wash32(rng, H, spark, BG._mix(pal["offwhite"], pal["sky"], 0.2), var=0.03, edge_dark=0.0, bleed=0.8))
    out.append(finish(stack, rng, H))

    # layer1: 512 tall: nearer sea with foam crests, one grassy cliff headland and two sea stacks
    H = 512
    sl = BG.ridge(rng, [(4, 0.6), (9, 0.4)], base=250, amp=4)
    seam_ = BG._ridge_mask(H, sl, soft=1.0)
    foam = np.zeros((H, W), np.float32)
    trough = np.zeros((H, W), np.float32)
    for row in range(8):
        y = 270 + row * 30 + row * row * 2
        ph = rng.uniform(0, 2 * np.pi)
        k = 6 + row
        for cx in np.arange(0, W, W / (k * 3)):
            yc = y + 6 * math.sin(2 * math.pi * k * cx / W + ph)
            L = rng.uniform(14, 30) * (1 + row * 0.15)
            rect(foam, cx - L, cx + L, yc, yc + 2 + row // 3)
            rect(trough, cx - L * 1.4, cx + L * 1.4, yc + 4, yc + 10 + row)
    cliff = np.zeros((H, W), np.float32)
    grass = np.zeros((H, W), np.float32)
    c0 = rng.uniform(150, 350)
    prof = [(0, 330), (40, 120), (120, 80), (260, 70), (380, 95), (470, 150), (540, 330)]   # x offset, top row
    for (xa, ya), (xb, yb) in zip(prof[:-1], prof[1:]):
        for xx in range(int(xa), int(xb)):
            t = (xx - xa) / max(xb - xa, 1)
            top = ya + (yb - ya) * t + 6 * math.sin(xx * 0.09)
            rect(cliff, c0 + xx, c0 + xx, top, 340)
            if 60 < xx < 470:
                rect(grass, c0 + xx, c0 + xx, top - 4, top + 14 + 6 * math.sin(xx * 0.05))
    for sx_, sh in ((c0 + 720, 90), (c0 + 790, 55)):
        for xx in range(-28, 29):
            rect(cliff, sx_ + xx, sx_ + xx, 300 - sh * math.sqrt(max(0.0, 1 - (xx / 28) ** 2)) + 4 * math.sin(xx * 0.4), 300)
    stack = [wash32(rng, H, seam_, BG._mix(pal["teal"], pal["sky"], 0.25), var=0.05, edge_dark=0.03, bleed=1.0),
             wash32(rng, H, trough * seam_, BG._mix(pal["teal"], pal["brown"], 0.15), var=0.04, edge_dark=0.02, bleed=2.5),
             wash32(rng, H, foam * seam_, pal["offwhite"], var=0.03, edge_dark=0.02, bleed=1.0),
             wash32(rng, H, cliff, BG._mix(pal["brown"], pal["sky"], 0.40), var=0.08, edge_dark=0.14, bleed=1.5),
             wash32(rng, H, grass, BG._mix(pal["green"], pal["sky"], 0.15), var=0.06, edge_dark=0.08, bleed=1.2)]
    out.append(finish(stack, rng, H))

    # layer2: 384 tall: dunes, marram tufts, pebbles, shells, driftwood
    H = 384
    line = BG.ridge(rng, [(2, 0.5), (5, 0.35), (11, 0.12)], base=190, amp=30)
    dune = BG._ridge_mask(H, line)
    flank = dune * np.clip(BG.periodic_noise(rng, H, 60, 25) * 0.8 + 0.1, 0, 1) * (np.arange(H)[:, None] > line[None, :] + 25)
    tufts = np.zeros((H, W), np.float32)
    for k in range(48):
        cx = rng.uniform(0, W)
        top = line[int(cx) % W]
        for j in range(9):
            BG_x = cx + rng.uniform(-12, 12)
            dab(tufts, BG_x, top + rng.uniform(2, 14), rng.uniform(18, 34), rng.uniform(-0.6, 0.6))
    bits = {"pebble": np.zeros((H, W), np.float32), "shell": np.zeros((H, W), np.float32), "wood": np.zeros((H, W), np.float32)}
    for k in range(70):
        cx = rng.uniform(0, W)
        cy = line[int(cx) % W] + rng.uniform(40, 170)
        if k % 3:
            ell(bits["pebble"], cx, cy, rng.uniform(3, 6), rng.uniform(2, 4))
        else:
            ell(bits["shell"], cx, cy, rng.uniform(3, 5), rng.uniform(2.5, 4), cut=0.3)
    for k in range(2):
        cx = rng.uniform(0, W)
        cy = line[int(cx) % W] + rng.uniform(60, 110)
        rect(bits["wood"], cx - 70, cx + 70, cy, cy + 9)
        rect(bits["wood"], cx + 30, cx + 36, cy - 16, cy + 2)
    sand = BG._mix(pal["mustard"], pal["offwhite"], 0.55)
    stack = [wash32(rng, H, dune, sand, var=0.05, edge_dark=0.07),
             wash32(rng, H, flank, BG._mix(sand, pal["brown"], 0.18), var=0.04, edge_dark=0.03, bleed=6.0),
             wash32(rng, H, tufts, BG._mix(pal["green"], pal["mustard"], 0.35), var=0.06, edge_dark=0.05, bleed=0.9),
             wash32(rng, H, bits["pebble"] * dune, BG._mix(pal["sky"], pal["brown"], 0.4), var=0.04, edge_dark=0.12, bleed=0.8),
             wash32(rng, H, bits["shell"] * dune, pal["offwhite"], var=0.03, edge_dark=0.10, bleed=0.8),
             wash32(rng, H, bits["wood"] * dune, BG._mix(pal["brown"], pal["offwhite"], 0.35), var=0.05, edge_dark=0.12, bleed=1.0)]
    out.append(finish(stack, rng, H))
    layers = [{"n": 0, "parallax": 0.1, "y_m": -2.0}, {"n": 1, "parallax": 0.35, "y_m": -1.0},
              {"n": 2, "parallax": 0.6, "y_m": -0.5}]
    return out, layers


# ---------------------------------------------------------------- Mars (B-141, the D-125 palette): canyon + dust storm

def notch(line, rng, n, depth, width):
    """V-shaped dips in a rim line (gullies cut into a plateau edge), wrapped in x."""
    x = np.arange(W)
    for _k in range(n):
        c, d, w = rng.uniform(0, W), rng.uniform(0.5, 1.0) * depth, rng.uniform(0.6, 1.0) * width
        dx = np.abs((x - c + W / 2) % W - W / 2)
        line = line + d * np.clip(1 - dx / w, 0, 1) ** 1.5
    return line


def terrace(line, step):
    """Quantise a rim line into flat steps (mesa ledges), softened so a step is a short slope, not a cliff pixel."""
    q = np.round(line / step) * step
    k = np.exp(-0.5 * (np.arange(-12, 13) / 4.0) ** 2)
    k /= k.sum()
    return np.convolve(np.concatenate([q[-12:], q, q[:12]]), k, mode="same")[12:-12]


def strata(H, wall, rng, y0, y1, n, thick=(8, 16)):
    """Horizontal sediment bands inside a wall mask, gently waving and periodic in x."""
    m = np.zeros((H, W), np.float32)
    y = np.arange(H)[:, None] + 0.5
    for k in range(n):
        yk = y0 + (y1 - y0) * (k + rng.uniform(0.2, 0.8)) / n
        wave = BG.ridge(rng, [(2, 0.6), (5, 0.3), (9, 0.1)], base=yk, amp=rng.uniform(4, 10))
        t = rng.uniform(*thick)
        m = np.maximum(m, ((y > wave[None, :]) & (y < wave[None, :] + t)).astype(np.float32))
    return m * wall


def tint(rng, H, mask, colour, opacity, **kw):
    """A wash over a full-strength mask, its alpha scaled afterwards: a translucent shape keeps a clean body (a
    fractional mask turns the wash's edge noise into speckle over its whole area). opacity: a number or an H x 1 ramp."""
    rgb, m = wash32(rng, H, mask, colour, **kw)
    return rgb, (m * opacity).astype(np.float32)


def mars_sky(rng, pal, H, storm):
    yy = (np.arange(H) / H)[:, None, None]
    top = BG._mix(BG._mix(pal["sky"], pal["mustard"], 0.30), pal["sky"], 0.5 * storm)
    low = BG._mix(pal["sky"], pal["offwhite"], 0.45 - 0.25 * storm)
    sky = BG._mix(top, low, np.clip(yy * 1.25, 0, 1)) * (1 + 0.04 * BG.periodic_noise(rng, H, 140, 80)[..., None])
    stack = Stack([(np.broadcast_to(sky, (H, W, 3)).astype(np.float32), np.ones((H, W), np.float32))])
    wisp = np.zeros((H, W), np.float32)
    for _k in range(9):                                        # thin high wisps (Mars has no fat cumulus)
        cx, cy = rng.uniform(0, W), rng.uniform(90, 420)
        for _j in range(3):
            ell(wisp, cx + rng.uniform(-120, 120), cy + rng.uniform(-6, 6), rng.uniform(160, 340), rng.uniform(5, 11))
    stack.append(tint(rng, H, wisp, BG._mix(pal["offwhite"], pal["sky"], 0.25 + 0.4 * storm), 0.7, var=0.03, edge_dark=0.02, bleed=4.0))
    return stack


def mars_canyon(seed, storm=0.0):
    """Valles Marineris. storm > 0 washes every colour toward the salmon haze (the dust-storm set reuses layers 0-1)."""
    rng = np.random.default_rng(seed)
    pal = _pal("mars")

    def hz(c, t=0.0):
        return BG._mix(c, pal["sky"], min(1.0, t + 0.45 * storm))
    out = []
    # layer0: the opposite canyon wall (a flat rim with gullies, strata bands) and its nearer buttresses, in haze
    H = 1024
    stack = mars_sky(rng, pal, H, storm)
    rim = notch(BG.ridge(rng, [(2, 0.5), (5, 0.3), (9, 0.2)], base=300, amp=12), rng, 7, 46, 70)    # above layer1's tiers
    wall = BG._ridge_mask(H, rim)
    stack.append(wash32(rng, H, wall, hz(BG._mix(pal["red"], pal["sky"], 0.55)), var=0.04, edge_dark=0.05, bleed=2.5))
    stack.append(wash32(rng, H, strata(H, wall, rng, 340, 900, 9), hz(BG._mix(pal["red"], pal["brown"], 0.25), 0.40), var=0.04, edge_dark=0.03, bleed=3.0))
    spur = terrace(notch(BG.ridge(rng, [(3, 0.5), (7, 0.35), (13, 0.15)], base=410, amp=35), rng, 5, 50, 90), 22)
    near = BG._ridge_mask(H, spur)
    stack.append(wash32(rng, H, near, hz(BG._mix(pal["red"], pal["sky"], 0.32)), var=0.05, edge_dark=0.07, bleed=2.0))
    stack.append(wash32(rng, H, strata(H, near, rng, 450, 1000, 7, (6, 12)), hz(BG._mix(pal["red"], pal["brown"], 0.30), 0.25), var=0.04, edge_dark=0.03, bleed=2.5))
    floor = BG._ridge_mask(H, BG.ridge(rng, [(4, 0.6), (9, 0.4)], base=960, amp=8))
    stack.append(wash32(rng, H, floor, hz(BG._mix(pal["sky"], pal["mustard"], 0.30)), var=0.04, edge_dark=0.03, bleed=6.0))
    out.append(finish(stack, rng, H))

    # layer1: nearer stepped walls (three terraced tiers), umber ledge shadows, gullies
    H = 640
    stack = Stack()
    for i, (base, amp, col) in enumerate(((150, 50, BG._mix(pal["red"], pal["sky"], 0.22)), (290, 46, pal["red"]),
                                          (420, 40, BG._mix(pal["red"], pal["brown"], 0.18)))):
        line = terrace(notch(BG.ridge(rng, [(2, 0.45), (5, 0.35), (11, 0.2)], base=base, amp=amp), rng, 4, 34, 60), 18)
        m = BG._ridge_mask(H, line)
        stack.append(wash32(rng, H, m, hz(col), var=0.06, edge_dark=0.09, bleed=1.8))
        y = np.arange(H)[:, None] + 0.5
        lens = 26 + 40 * np.clip(BG.ridge(rng, [(3, 0.5), (8, 0.5)], base=0.5, amp=0.5), 0, 1)
        ledge = ((y > line[None, :] + 6) & (y < line[None, :] + 6 + lens[None, :])).astype(np.float32) * m
        stack.append(wash32(rng, H, ledge, hz(BG._mix(pal["brown"], pal["red"], 0.30), 0.10), var=0.05, edge_dark=0.04, bleed=4.0))
        gul = np.zeros((H, W), np.float32)
        for _k in range(14):
            cx = rng.uniform(0, W)
            top = line[int(cx) % W] + 10
            for t in range(int(rng.uniform(40, 110))):
                gul[min(int(top + t), H - 1), int(cx + 3 * math.sin(t / 9.0)) % W] = 1.0
        stack.append(wash32(rng, H, gul * m, hz(BG._mix(pal["brown"], pal["red"], 0.4), 0.05), var=0.03, edge_dark=0.0, bleed=1.2))
    out.append(finish(stack, rng, H))

    # layer2: near scree slopes with boulders and pebbles (the canyon); the storm replaces it with the dust overlay
    if storm > 0:
        out.append(mars_storm_overlay(rng, pal))
        return out, [{"n": 0, "parallax": 0.1, "y_m": -2.0}, {"n": 1, "parallax": 0.35, "y_m": -1.0},
                     {"n": 2, "parallax": 0.7, "y_m": -0.5}]
    H = 384
    line = BG.ridge(rng, [(3, 0.5), (7, 0.3), (15, 0.2)], base=200, amp=26)
    ground = BG._ridge_mask(H, line)
    rocks, shade, pebbles, basalt = (np.zeros((H, W), np.float32) for _ in range(4))
    for _k in range(26):
        cx = rng.uniform(0, W)
        b = line[int(cx) % W] + rng.uniform(10, 120)
        rx, ry = rng.uniform(22, 60), rng.uniform(16, 40)
        ell(rocks, cx, b - ry * 0.6, rx, ry, cut=0.6)
        ell(shade, cx + rx * 0.25, b - ry * 0.35, rx * 0.8, ry * 0.55, cut=0.6)
    for _k in range(110):
        cx = rng.uniform(0, W)
        ell(pebbles, cx, line[int(cx) % W] + rng.uniform(8, 170), rng.uniform(3, 7), rng.uniform(2, 4))
    for _k in range(18):
        cx = rng.uniform(0, W)
        ell(basalt, cx, line[int(cx) % W] + rng.uniform(30, 150), rng.uniform(8, 16), rng.uniform(5, 10), cut=0.5)
    stack = Stack()
    stack.append(wash32(rng, H, ground, BG._mix(pal["red"], pal["brown"], 0.20), var=0.07, edge_dark=0.08))
    stack.append(wash32(rng, H, rocks, BG._mix(pal["red"], pal["sky"], 0.20), var=0.06, edge_dark=0.12, bleed=1.4))
    stack.append(wash32(rng, H, shade * rocks, BG._mix(pal["brown"], pal["red"], 0.35), var=0.04, edge_dark=0.04, bleed=2.0))
    stack.append(wash32(rng, H, pebbles * ground, BG._mix(pal["sky"], pal["brown"], 0.40), var=0.04, edge_dark=0.10, bleed=0.8))
    stack.append(wash32(rng, H, basalt * ground, BG._mix(pal["brown"], pal["sky"], 0.25), var=0.04, edge_dark=0.12, bleed=0.9))
    out.append(finish(stack, rng, H))
    return out, [{"n": 0, "parallax": 0.1, "y_m": -2.0}, {"n": 1, "parallax": 0.35, "y_m": -1.0},
                 {"n": 2, "parallax": 0.6, "y_m": -0.5}]


def mars_storm_overlay(rng, pal, H=768):
    """The dust storm as the NEAR layer (overlays that must read through the stack go on the nearest layer): a thin
    veil over everything, rolling billows low down with darker undersides, long drawn wind streaks; translucent."""
    y = (np.arange(H)[:, None] / H).astype(np.float32)
    ramp = np.clip((y - 0.05) / 0.45, 0, 1) * 0.18                       # the veil fades in from nothing at the top
    bill, under = np.zeros((H, W), np.float32), np.zeros((H, W), np.float32)
    for _k in range(16):
        cx, cy = rng.uniform(0, W), rng.uniform(450, 700)
        for _j in range(4):
            x, y_ = cx + rng.uniform(-160, 160), cy + rng.uniform(-40, 40)
            rx, ry = rng.uniform(110, 220), rng.uniform(60, 120)
            ell(bill, x, y_, rx, ry)
            ell(under, x + rx * 0.1, y_ + ry * 0.45, rx * 0.85, ry * 0.45)
    streaks = [np.zeros((H, W), np.float32) for _ in range(3)]
    for _k in range(45):
        ell(streaks[_k % 3], rng.uniform(0, W), rng.uniform(120, 740), rng.uniform(120, 380), rng.uniform(1.5, 4.0))
    stack = Stack()
    stack.append(tint(rng, H, np.ones((H, W), np.float32), BG._mix(pal["sky"], pal["mustard"], 0.25), ramp, var=0.02, edge_dark=0.0, bleed=1.0))
    stack.append(tint(rng, H, bill, BG._mix(pal["sky"], pal["offwhite"], 0.35), 0.6, var=0.05, edge_dark=0.05, bleed=6.0))
    stack.append(tint(rng, H, under * bill, BG._mix(pal["sky"], pal["brown"], 0.30), 0.5, var=0.04, edge_dark=0.02, bleed=8.0))
    for k, op in enumerate((0.2, 0.3, 0.4)):
        stack.append(tint(rng, H, streaks[k], BG._mix(pal["offwhite"], pal["sky"], 0.55), op, var=0.03, edge_dark=0.0, bleed=1.5))
    return finish(stack, rng, H)


def mars_storm(seed):
    return mars_canyon(seed, storm=1.0)


# ---------------------------------------------------------------- Mercury (B-145, D-130 palette): day / twilight / night

def mars_plains(seed):
    """B-141's third set (LEAD's catch, cycle 267): the open Martian plain. layer0 the butterscotch sky with wind streaks
    and far flat-topped mesas with strata, the plain's hazy far edge; layer1 the rolling rust plain with shallow craters,
    boulders and a faint dust devil; layer2 near rust ground with boulders, pebbles, ripple marks and low drifting dust."""
    rng = np.random.default_rng(seed)
    pal = _pal("mars")
    out = []
    H = 1024
    stack = mars_sky(rng, pal, H, 0.0)
    streaks = np.zeros((H, W), np.float32)
    for _k in range(14):                                                                  # wind streaks low in the sky
        cx, cy = rng.uniform(0, W), rng.uniform(520, 760)
        ell(streaks, cx, cy, rng.uniform(220, 420), rng.uniform(2.5, 5))
    stack.append(tint(rng, H, streaks, BG._mix(pal["offwhite"], pal["sky"], 0.35), 0.55, var=0.03, edge_dark=0.0, bleed=3.0))
    mesas, tops = np.zeros((H, W), np.float32), np.zeros((H, W), np.float32)
    for _k in range(6):                                                                   # far flat-topped mesas
        cx, w, h = rng.uniform(0, W), rng.uniform(140, 300), rng.uniform(80, 170)
        base = 640.0                                                                      # above layer1's skyline (at 880 they were hidden)
        poly(mesas, [(cx - w * 0.5 - h * 0.6, base), (cx - w * 0.5, base - h), (cx + w * 0.5, base - h), (cx + w * 0.5 + h * 0.6, base)])
        rect(tops, cx - w * 0.5, cx + w * 0.5, base - h, base - h + 10)
    stack.append(wash32(rng, H, mesas, BG._mix(pal["red"], pal["sky"], 0.55), var=0.04, edge_dark=0.05, bleed=2.5))
    stack.append(wash32(rng, H, strata(H, mesas, rng, 470, 640, 5, (5, 10)), BG._mix(pal["red"], pal["brown"], 0.25), var=0.04, edge_dark=0.03, bleed=3.0))
    stack.append(tint(rng, H, tops * mesas, pal["offwhite"], 0.35, var=0.0, edge_dark=0.0, bleed=1.5))   # the lit caprock
    edge = BG._ridge_mask(H, BG.ridge(rng, [(3, 0.6), (8, 0.4)], base=630, amp=10))      # the plain's far edge: the horizon
    devil = np.zeros((H, W), np.float32)
    dx = rng.uniform(300, 1700)
    for t in np.linspace(0, 1, 30):                                                       # a faint dust devil on the opaque sky
        ell(devil, dx + 14 * math.sin(t * 9), 640 - 300 * t, 8 + 30 * t, 8)               # (over layer1's transparency it went dark)
    stack.append(tint(rng, H, devil, BG._mix(pal["sky"], pal["offwhite"], 0.55), 0.4, var=0.03, edge_dark=0.0, bleed=5.0))
    stack.append(wash32(rng, H, edge, BG._mix(pal["sky"], pal["mustard"], 0.30), var=0.04, edge_dark=0.03, bleed=6.0))
    out.append(finish(stack, rng, H))
    # layer1: the rolling rust plain
    H = 640
    stack = Stack()
    line = BG.ridge(rng, [(2, 0.5), (5, 0.3), (12, 0.2)], base=330, amp=26)
    plain = BG._ridge_mask(H, line)
    stack.append(wash32(rng, H, plain, BG._mix(pal["red"], pal["sky"], 0.28), var=0.06, edge_dark=0.07, bleed=2.0))
    rim, bowl, shade = crater_field(rng, H, line, 6, 30, 70, 1.6)
    stack.append(wash32(rng, H, rim * plain, BG._mix(pal["red"], pal["sky"], 0.40), var=0.04, edge_dark=0.06, bleed=1.6))
    stack.append(wash32(rng, H, bowl * plain, BG._mix(pal["red"], pal["brown"], 0.25), var=0.04, edge_dark=0.04, bleed=1.6))
    rocks = np.zeros((H, W), np.float32)
    for _k in range(22):
        cx = rng.uniform(0, W)
        b = line[int(cx) % W] + rng.uniform(40, 260)
        rx, ry = rng.uniform(12, 30), rng.uniform(8, 18)
        ell(rocks, cx, b - ry * 0.6, rx, ry, cut=0.6)
    stack.append(wash32(rng, H, rocks * plain, BG._mix(pal["red"], pal["brown"], 0.35), var=0.05, edge_dark=0.10, bleed=1.2))
    out.append(finish(stack, rng, H))
    # layer2: near rust ground, boulders with shade, pebbles, ripple marks, low drifting dust
    H = 384
    line = BG.ridge(rng, [(3, 0.5), (7, 0.3), (15, 0.2)], base=210, amp=18)
    ground = BG._ridge_mask(H, line)
    rocks, shade, pebbles, ripples, dust = (np.zeros((H, W), np.float32) for _ in range(5))
    for _k in range(18):
        cx = rng.uniform(0, W)
        b = line[int(cx) % W] + rng.uniform(10, 120)
        rx, ry = rng.uniform(20, 54), rng.uniform(14, 34)
        ell(rocks, cx, b - ry * 0.6, rx, ry, cut=0.6)
        ell(shade, cx + rx * 0.25, b - ry * 0.35, rx * 0.8, ry * 0.55, cut=0.6)
    for _k in range(90):
        cx = rng.uniform(0, W)
        ell(pebbles, cx, line[int(cx) % W] + rng.uniform(8, 170), rng.uniform(3, 7), rng.uniform(2, 4))
    for _k in range(40):                                                                  # ripple marks (thin darker arcs)
        cx, cy = rng.uniform(0, W), 0.0
        cy = line[int(cx) % W] + rng.uniform(20, 160)
        ell(ripples, cx, cy, rng.uniform(20, 46), 1.2)
    for _k in range(10):                                                                  # low drifting dust
        cx = rng.uniform(0, W)
        ell(dust, cx, line[int(cx) % W] - rng.uniform(2, 14), rng.uniform(120, 260), rng.uniform(5, 10))
    stack = Stack()
    stack.append(wash32(rng, H, ground, BG._mix(pal["red"], pal["brown"], 0.18), var=0.07, edge_dark=0.08))
    stack.append(wash32(rng, H, ripples * ground, BG._mix(pal["red"], pal["brown"], 0.40), var=0.03, edge_dark=0.0, bleed=0.8))
    stack.append(wash32(rng, H, rocks, BG._mix(pal["red"], pal["sky"], 0.22), var=0.06, edge_dark=0.12, bleed=1.4))
    stack.append(wash32(rng, H, shade * rocks, BG._mix(pal["brown"], pal["red"], 0.35), var=0.04, edge_dark=0.04, bleed=2.0))
    stack.append(wash32(rng, H, pebbles * ground, BG._mix(pal["sky"], pal["brown"], 0.40), var=0.04, edge_dark=0.10, bleed=0.8))
    stack.append(tint(rng, H, dust, BG._mix(pal["sky"], pal["offwhite"], 0.3), 0.4, var=0.03, edge_dark=0.0, bleed=4.0))
    out.append(finish(stack, rng, H))
    return out, [{"n": 0, "parallax": 0.1, "y_m": -2.0}, {"n": 1, "parallax": 0.35, "y_m": -1.0},
                 {"n": 2, "parallax": 0.6, "y_m": -0.5}]


def merc_sky(rng, pal, H, mode):
    """The day sky is the ink itself with sharp stars; twilight adds a violet band low down; night is ink + more stars."""
    ink = BG._rgb(v3.INK)
    yy = (np.arange(H) / H)[:, None, None]
    if mode == "twilight":
        band = np.clip((yy - 0.45) / 0.35, 0, 1)
        sky = ink * (1 - band) + pal["sky"] * band
    else:
        sky = np.broadcast_to(ink, (H, 1, 3)) * np.ones_like(yy)
    stack = Stack([(np.broadcast_to(sky, (H, W, 3)).astype(np.float32), np.ones((H, W), np.float32))])
    stars = np.zeros((H, W), np.float32)
    for _k in range({"day": 60, "twilight": 90, "night": 220}[mode]):
        ell(stars, rng.uniform(0, W), rng.uniform(8, H * (0.55 if mode == "twilight" else 0.8)), rng.uniform(0.9, 2.2), rng.uniform(0.9, 2.2))
    stack.append(tint(rng, H, stars, pal["offwhite"], 0.9, var=0.0, edge_dark=0.0, bleed=0.6))
    return stack


def huge_sun(stack, rng, pal, H, cx, cy, R):
    """The huge Sun low in the sky (B-137's look as a painted disc): a gold body, an off-white core, a corona ring."""
    corona = np.zeros((H, W), np.float32)
    ell(corona, cx, cy, R * 1.28, R * 1.28)
    stack.append(tint(rng, H, corona, BG._mix(pal["mustard"], pal["offwhite"], 0.5), 0.35, var=0.03, edge_dark=0.0, bleed=10.0))
    body = np.zeros((H, W), np.float32)
    ell(body, cx, cy, R, R)
    stack.append(wash32(rng, H, body, pal["mustard"], var=0.04, edge_dark=0.06, bleed=2.0))
    core = np.zeros((H, W), np.float32)
    ell(core, cx - R * 0.15, cy - R * 0.1, R * 0.55, R * 0.55)
    stack.append(tint(rng, H, core, pal["offwhite"], 0.7, var=0.02, edge_dark=0.0, bleed=12.0))


def crater_field(rng, H, line, n, rmin, rmax, depth):
    """Bowls along a rim line: (rim mask, bowl mask, shadow mask), the shadows on the bowls' sunward (left) walls."""
    rim, bowl, shade = (np.zeros((H, W), np.float32) for _ in range(3))
    for _k in range(n):
        cx = rng.uniform(0, W)
        r = rng.uniform(rmin, rmax)
        cy = line[int(cx) % W] + depth * r
        ell(rim, cx, cy - r * 0.28, r * 1.18, r * 0.42, cut=0.2)
        ell(bowl, cx, cy - r * 0.25, r, r * 0.30)
        ell(shade, cx - r * 0.35, cy - r * 0.26, r * 0.62, r * 0.26)
    return rim, bowl, shade * bowl


def mercury_scene(seed, mode="day"):
    rng = np.random.default_rng(seed)
    pal = _pal("mercury")
    lit = {"day": pal["offwhite"], "twilight": BG._mix(pal["offwhite"], pal["sky"], 0.35), "night": BG._mix(pal["brown"], pal["teal"], 0.25)}[mode]
    dark = {"day": pal["brown"], "twilight": BG._mix(pal["brown"], pal["sky"], 0.3), "night": pal["brown"]}[mode]
    out = []
    # layer0: the sky (ink), the huge Sun (day / twilight), the far crater rims
    H = 1024
    stack = merc_sky(rng, pal, H, mode)
    if mode == "day":
        huge_sun(stack, rng, pal, H, 420, 610, 230)
    elif mode == "twilight":
        huge_sun(stack, rng, pal, H, 1500, 905, 260)                       # half below the horizon: the terminator
    far = BG.ridge(rng, [(2, 0.5), (5, 0.3), (11, 0.2)], base=860, amp=20)
    stack.append(wash32(rng, H, BG._ridge_mask(H, far), BG._mix(lit, dark, 0.35), var=0.04, edge_dark=0.05, bleed=2.0))
    rim, bowl, shade = crater_field(rng, H, far, 9, 30, 70, 0.6)
    stack.append(wash32(rng, H, rim, BG._mix(lit, dark, 0.25), var=0.04, edge_dark=0.06, bleed=1.6))
    stack.append(wash32(rng, H, bowl, BG._mix(lit, dark, 0.55), var=0.04, edge_dark=0.04, bleed=1.6))
    out.append(finish(stack, rng, H))
    # layer1: nearer crater rims, the blinding regolith with hard shadows
    H = 640
    stack = Stack()
    near = BG.ridge(rng, [(2, 0.45), (6, 0.35), (13, 0.2)], base=360, amp=34)
    stack.append(wash32(rng, H, BG._ridge_mask(H, near), lit, var=0.05, edge_dark=0.07, bleed=1.8))
    rim, bowl, shade = crater_field(rng, H, near, 7, 60, 140, 0.9)
    stack.append(wash32(rng, H, rim, BG._mix(lit, pal["offwhite"], 0.3), var=0.04, edge_dark=0.08, bleed=1.4))
    stack.append(wash32(rng, H, bowl, BG._mix(lit, dark, 0.35), var=0.04, edge_dark=0.05, bleed=1.4))
    stack.append(wash32(rng, H, shade, dark, var=0.03, edge_dark=0.02, bleed=1.2))       # hard shadows (no air: crisp)
    if mode == "night":
        glint = np.zeros((H, W), np.float32)
        for _k in range(26):
            cx = rng.uniform(0, W)
            ell(glint, cx, near[int(cx) % W] + rng.uniform(60, 220), rng.uniform(4, 10), rng.uniform(2, 4))
        stack.append(tint(rng, H, glint * BG._ridge_mask(H, near), pal["teal"], 0.9, var=0.03, edge_dark=0.1, bleed=0.8))
    out.append(finish(stack, rng, H))
    # layer2: near regolith, rocks with hard shadows; twilight: Glassreed tufts; day: heat-shimmer dabs
    H = 384
    stack = Stack()
    line = BG.ridge(rng, [(3, 0.5), (7, 0.3), (15, 0.2)], base=210, amp=20)
    ground = BG._ridge_mask(H, line)
    stack.append(wash32(rng, H, ground, BG._mix(lit, dark, 0.12), var=0.06, edge_dark=0.07))
    rocks, rshade = np.zeros((H, W), np.float32), np.zeros((H, W), np.float32)
    for _k in range(30):
        cx = rng.uniform(0, W)
        b = line[int(cx) % W] + rng.uniform(10, 130)
        rx, ry = rng.uniform(14, 44), rng.uniform(10, 28)
        ell(rocks, cx, b - ry * 0.6, rx, ry, cut=0.6)
        ell(rshade, cx - rx * 0.3, b - ry * 0.3, rx * 0.75, ry * 0.5, cut=0.6)
    stack.append(wash32(rng, H, rocks, BG._mix(lit, pal["offwhite"], 0.2), var=0.05, edge_dark=0.12, bleed=1.2))
    stack.append(wash32(rng, H, rshade * rocks, dark, var=0.03, edge_dark=0.03, bleed=1.0))
    if mode == "twilight":
        reeds = np.zeros((H, W), np.float32)
        for _k in range(22):
            cx = rng.uniform(0, W)
            base = line[int(cx) % W] + rng.uniform(20, 70)
            for j in range(4):
                dab(reeds, cx + 6 * j, base, rng.uniform(26, 60), -0.3 + 0.2 * j, w=1)
        stack.append(wash32(rng, H, reeds * ground, pal["teal"], var=0.04, edge_dark=0.05, bleed=0.8))
    if mode == "day":
        shimmer = np.zeros((H, W), np.float32)
        for _k in range(20):
            cx = rng.uniform(0, W)
            ell(shimmer, cx, line[int(cx) % W] - rng.uniform(4, 16), rng.uniform(30, 80), rng.uniform(1.5, 3))
        stack.append(tint(rng, H, shimmer, pal["offwhite"], 0.35, var=0.0, edge_dark=0.0, bleed=1.5))
    out.append(finish(stack, rng, H))
    return out, [{"n": 0, "parallax": 0.1, "y_m": -2.0}, {"n": 1, "parallax": 0.35, "y_m": -1.0},
                 {"n": 2, "parallax": 0.6, "y_m": -0.5}]


def mercury_day(seed):
    return mercury_scene(seed, "day")


def mercury_twilight(seed):
    return mercury_scene(seed, "twilight")


def mercury_night(seed):
    return mercury_scene(seed, "night")


# ---------------------------------------------------------------- Venus (B-147, D-134 palette): the cloud deck and the surface dive

def cloud_tower(mask, cx, base, h, w, rng):
    """A cumulus tower: a broad flat-bottomed base of three lumps, then tiers of fewer, smaller lumps climbing with a lean
    to a cauliflower crown (a stack of single balls read as dumplings)."""
    n = max(3, int(h / (w * 0.6)) + 1)                                                   # tiers overlap (no floating lumps)
    lean = rng.uniform(-0.3, 0.3) * w
    ell(mask, cx + 0.5 * lean, base - 0.45 * h, 0.75 * w, 0.5 * h, cut=0.9)              # the core binding the tiers
    for k in range(n):
        t = k / max(n - 1, 1)
        ww = w * (1.0 - 0.4 * t)
        m = 3 if t < 0.7 else 2
        for j in range(m):
            off = ((j - (m - 1) / 2) * 0.75 + rng.uniform(-0.15, 0.15)) * ww
            r = ww * rng.uniform(0.6, 0.85)
            ell(mask, cx + lean * t + off, base - t * h - rng.uniform(0.0, 0.2) * r, r, r * 0.8, cut=0.6 if k == 0 else None)


def poly(mask, pts, val=1.0):
    """A filled polygon (even-odd), x wrapping (tileable)."""
    xs_, ys_ = [q[0] for q in pts], [q[1] for q in pts]
    y0, y1 = max(int(min(ys_)), 0), min(int(max(ys_)) + 2, mask.shape[0])
    xa = np.arange(int(min(xs_)) - 1, int(max(xs_)) + 2)
    X, Y = xa[None, :] + 0.5, np.arange(y0, y1)[:, None] + 0.5
    inside = np.zeros((y1 - y0, len(xa)), bool)
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        if ay == by:
            continue
        cross = ((ay > Y) != (by > Y)) & (X < ax + (Y - ay) * (bx - ax) / (by - ay))
        inside ^= cross
    cols = xa % W
    mask[y0:y1, cols] = np.maximum(mask[y0:y1][:, cols], inside * val)


def lining(mask, dy, dx):
    """The backlit cream lining: the mask itself shifted up-left and up-right (it follows the cloud; wraps in x)."""
    return np.maximum(np.roll(mask, (-dy, dx), (0, 1)), np.roll(mask, (-dy, -dx), (0, 1)))


def venus_deck(seed):
    rng = np.random.default_rng(seed)
    pal = _pal("venus")
    out = []
    # layer0: the apricot sky over cream, drifting sulphur-haze bands, backlit cloud towers far off
    H = 1024
    yy = (np.arange(H) / H)[:, None, None]
    sky = BG._mix(pal["sky"], pal["offwhite"], np.clip(yy * 1.1, 0, 1) * 0.55) * (1 + 0.03 * BG.periodic_noise(rng, H, 160, 90)[..., None])
    stack = Stack([(np.broadcast_to(sky, (H, W, 3)).astype(np.float32), np.ones((H, W), np.float32))])
    bands = np.zeros((H, W), np.float32)
    for k in range(6):
        y0 = 120 + 120 * k + rng.uniform(-20, 20)
        line = BG.ridge(rng, [(2, 0.6), (5, 0.4)], base=y0, amp=10)
        y = np.arange(H)[:, None] + 0.5
        bands = np.maximum(bands, ((y > line[None, :]) & (y < line[None, :] + rng.uniform(14, 30))).astype(np.float32))
    stack.append(tint(rng, H, bands, BG._mix(pal["mustard"], pal["sky"], 0.5), 0.35, var=0.04, edge_dark=0.0, bleed=8.0))
    towers = np.zeros((H, W), np.float32)
    for _k in range(7):
        cx = rng.uniform(0, W)
        base, h, w = rng.uniform(780, 900), rng.uniform(260, 460), rng.uniform(70, 115)
        cloud_tower(towers, cx, base, h, w, rng)
    rims = lining(towers, 6, 5)
    stack.append(tint(rng, H, rims, pal["offwhite"], 0.85, var=0.03, edge_dark=0.03, bleed=3.0))   # the backlit cream edges
    stack.append(wash32(rng, H, towers, BG._mix(pal["sky"], pal["red"], 0.15), var=0.05, edge_dark=0.06, bleed=3.0))
    out.append(finish(stack, rng, H))
    # layer1: nearer towers and a floating station's silhouette
    H = 640
    stack = Stack()
    near = np.zeros((H, W), np.float32)
    for _k in range(5):
        cx = rng.uniform(0, W)
        base, h, w = rng.uniform(560, 620), rng.uniform(220, 380), rng.uniform(80, 130)
        cloud_tower(near, cx, base, h, w, rng)
    nrim = lining(near, 8, 6)
    stack.append(tint(rng, H, nrim, pal["offwhite"], 0.9, var=0.03, edge_dark=0.03, bleed=2.5))
    stack.append(wash32(rng, H, near, BG._mix(pal["sky"], pal["mustard"], 0.2), var=0.05, edge_dark=0.07, bleed=2.5))
    station, bag, ribs, sheen, wins = (np.zeros((H, W), np.float32) for _ in range(5))
    sx, sy = rng.uniform(300, 1700), 170                                                  # above the near cloud tops
    ell(bag, sx, sy, 130, 44)                                                             # the gasbag
    for sg in (-1, 1):                                                                    # the swept tail fins
        poly(station, [(sx - 152, sy + sg * 46), (sx - 96, sy + sg * 12), (sx - 140, sy + sg * 6)])
    for k in range(5):
        rect(station, sx - 52 + 26 * k, sx - 50 + 26 * k, sy + 38, sy + 78)               # the rigging
    rect(station, sx - 74, sx + 74, sy + 76, sy + 96)                                     # the deck
    rect(station, sx - 44, sx + 8, sy + 54, sy + 78)                                      # the deckhouse
    station = np.maximum(station, bag)
    for k in range(-3, 4):
        ell(ribs, sx + 34 * k, sy, 2.5, 44)                                               # the gasbag ribs
    ell(sheen, sx + 12, sy - 22, 84, 7)
    for k in range(3):
        rect(wins, sx - 38 + 16 * k, sx - 30 + 16 * k, sy + 60, sy + 68)                  # warm deckhouse windows
    body = BG._mix(pal["brown"], pal["sky"], 0.35)
    stack.append(wash32(rng, H, station, body, var=0.03, edge_dark=0.06, bleed=1.2))
    stack.append(tint(rng, H, ribs * bag, pal["brown"], 0.55, var=0.0, edge_dark=0.0, bleed=0.8))
    stack.append(tint(rng, H, sheen * bag, pal["offwhite"], 0.35, var=0.0, edge_dark=0.0, bleed=2.0))
    stack.append(tint(rng, H, wins, pal["mustard"], 0.95, var=0.0, edge_dark=0.0, bleed=0.6))
    out.append(finish(stack, rng, H))
    # layer2: cloud tops near the deck with gaps showing the dark surface far below and its tiny vent glows
    H = 384
    stack = Stack()
    floor = np.zeros((H, W), np.float32)
    rect(floor, 0, W, 210, H)
    stack.append(wash32(rng, H, floor, BG._mix(pal["brown"], pal["sky"], 0.25), var=0.05, edge_dark=0.0, bleed=4.0))
    glows = np.zeros((H, W), np.float32)
    for _k in range(30):
        ell(glows, rng.uniform(0, W), rng.uniform(230, 360), rng.uniform(3, 7), rng.uniform(2, 4))
    stack.append(tint(rng, H, glows, pal["red"], 0.9, var=0.03, edge_dark=0.0, bleed=1.5))
    tops = np.zeros((H, W), np.float32)
    for _k in range(26):
        cx = rng.uniform(0, W)
        for j in range(3):
            ell(tops, cx + rng.uniform(-90, 90), rng.uniform(150, 260), rng.uniform(70, 150), rng.uniform(40, 70))
    stack.append(wash32(rng, H, tops, BG._mix(pal["offwhite"], pal["sky"], 0.35), var=0.05, edge_dark=0.05, bleed=4.0))
    out.append(finish(stack, rng, H))
    return out, [{"n": 0, "parallax": 0.1, "y_m": -2.0}, {"n": 1, "parallax": 0.35, "y_m": -1.0},
                 {"n": 2, "parallax": 0.6, "y_m": -0.5}]


def venus_surface(seed):
    rng = np.random.default_rng(seed)
    pal = _pal("venus")
    out = []
    # layer0: the orange-cream haze ceiling over a dark basalt horizon
    H = 1024
    yy = (np.arange(H) / H)[:, None, None]
    sky = BG._mix(BG._mix(pal["sky"], pal["red"], 0.25), pal["offwhite"], np.clip(1 - yy * 1.3, 0, 1) * 0.35)
    stack = Stack([(np.broadcast_to(sky, (H, W, 3)).astype(np.float32), np.ones((H, W), np.float32))])
    haze = np.zeros((H, W), np.float32)
    for k in range(5):
        line = BG.ridge(rng, [(2, 0.6), (4, 0.4)], base=150 + 140 * k, amp=16)
        y = np.arange(H)[:, None] + 0.5
        haze = np.maximum(haze, ((y > line[None, :]) & (y < line[None, :] + 40)).astype(np.float32))
    stack.append(tint(rng, H, haze, pal["offwhite"], 0.25, var=0.04, edge_dark=0.0, bleed=10.0))
    far = BG.ridge(rng, [(2, 0.5), (5, 0.3), (11, 0.2)], base=840, amp=30)
    stack.append(wash32(rng, H, BG._ridge_mask(H, far), BG._mix(pal["brown"], pal["sky"], 0.35), var=0.04, edge_dark=0.05, bleed=2.0))
    out.append(finish(stack, rng, H))
    # layer1: black glassy basalt plains and tesserae ridges, lit from below by vent glows
    H = 640
    stack = Stack()
    ridge = terrace(BG.ridge(rng, [(2, 0.45), (6, 0.35), (13, 0.2)], base=340, amp=44), 16)
    land = BG._ridge_mask(H, ridge)
    stack.append(wash32(rng, H, land, pal["brown"], var=0.05, edge_dark=0.06, bleed=1.8))
    glows, cores, glints = (np.zeros((H, W), np.float32) for _ in range(3))
    for _k in range(9):
        cx = rng.uniform(0, W)
        cy = ridge[int(cx) % W] + rng.uniform(40, 200)
        ell(glows, cx, cy, rng.uniform(60, 120), rng.uniform(30, 50))
        ell(cores, cx, cy + 6, rng.uniform(10, 18), rng.uniform(5, 8))
    for _k in range(40):
        cx = rng.uniform(0, W)
        ell(glints, cx, ridge[int(cx) % W] + rng.uniform(10, 260), rng.uniform(8, 20), rng.uniform(1.5, 3))
    stack.append(tint(rng, H, glows * land, pal["red"], 0.45, var=0.03, edge_dark=0.0, bleed=14.0))   # vent glow (a tone)
    stack.append(wash32(rng, H, cores * land, BG._mix(pal["red"], pal["mustard"], 0.5), var=0.03, edge_dark=0.05, bleed=1.2))
    stack.append(tint(rng, H, glints * land, pal["offwhite"], 0.55, var=0.0, edge_dark=0.0, bleed=1.0))  # glassy sheen
    out.append(finish(stack, rng, H))
    # layer2: near basalt with glassy highlights, heat shimmer, acid-rain streaks that stop mid-air
    H = 384
    stack = Stack()
    line = BG.ridge(rng, [(3, 0.5), (7, 0.3), (15, 0.2)], base=220, amp=20)
    ground = BG._ridge_mask(H, line)
    stack.append(wash32(rng, H, ground, BG._mix(pal["brown"], pal["sky"], 0.08), var=0.06, edge_dark=0.07))
    rocks, sheen = np.zeros((H, W), np.float32), np.zeros((H, W), np.float32)
    for _k in range(26):
        cx = rng.uniform(0, W)
        b = line[int(cx) % W] + rng.uniform(10, 130)
        rx, ry = rng.uniform(16, 46), rng.uniform(10, 28)
        ell(rocks, cx, b - ry * 0.6, rx, ry, cut=0.6)
        ell(sheen, cx - rx * 0.25, b - ry * 0.95, rx * 0.4, ry * 0.18)
    stack.append(wash32(rng, H, rocks, BG._mix(pal["brown"], pal["sky"], 0.15), var=0.05, edge_dark=0.12, bleed=1.2))
    stack.append(tint(rng, H, sheen * rocks, pal["offwhite"], 0.6, var=0.0, edge_dark=0.0, bleed=0.8))
    rain = np.zeros((H, W), np.float32)
    for _k in range(60):
        cx, cy = rng.uniform(0, W), rng.uniform(10, 140)
        for t in range(int(rng.uniform(10, 26))):
            rain[min(int(cy + t), H - 1), int(cx + 0.3 * t) % W] = 1.0
    stack.append(tint(rng, H, rain, BG._mix(pal["teal"], pal["offwhite"], 0.4), 0.5, var=0.0, edge_dark=0.0, bleed=0.6))
    out.append(finish(stack, rng, H))
    return out, [{"n": 0, "parallax": 0.1, "y_m": -2.0}, {"n": 1, "parallax": 0.35, "y_m": -1.0},
                 {"n": 2, "parallax": 0.6, "y_m": -0.5}]


TAU_BG = 2 * math.pi


# ---------------------------------------------------------------- Jupiter (B-155, D-137 palette): the cloud column's decks
# Scenes deck1 / deck2 / deck3 / deep (Bible §7.5's bands of the column) and spot (the Great Red Spot overlay: deck1 with
# layer1 replaced by the swirl). Overlays that must read through the cloud stack sit on layer2 (the near-layer rule): the
# lightning under the floor and the CRUSH band. Scene names are plain; when Saturn reuses them, SEEDS / PLANET_OF become
# (planet, scene) keyed.

def cloud_bank(mask, line, rng, rmin, rmax, n):
    """A bank of overlapping lumps whose tops follow `line` (a ridge), its body filled down to the layer's bottom."""
    H = mask.shape[0]
    for _k in range(n):
        cx = rng.uniform(0, W)
        r = rng.uniform(rmin, rmax)
        ell(mask, cx, line[int(cx) % W] + r * 0.55, r * rng.uniform(1.2, 1.8), r)
    mask[:] = np.maximum(mask, BG._ridge_mask(H, line + rmax * 0.6))


def bands(rng, H, specs, pal):
    """Horizontal wavy bands (the planet's stripes seen edge-on): [(y0, thickness, colour, opacity)] -> a list of tints."""
    out = []
    y = np.arange(H)[:, None] + 0.5
    for y0, th, col, op in specs:
        line = BG.ridge(rng, [(2, 0.6), (5, 0.4)], base=y0, amp=th * 0.35)
        m = ((y > line[None, :]) & (y < line[None, :] + th)).astype(np.float32)
        out.append(tint(rng, H, m, col, op, var=0.04, edge_dark=0.0, bleed=6.0))
    return out


def moon(stack, rng, H, cx, cy, R, body, marks, n):
    """A small painted moon disc in the thin sky: a body, n blotches, an ink-dark rim through edge_dark."""
    disc = np.zeros((H, W), np.float32)
    ell(disc, cx, cy, R, R)
    stack.append(wash32(rng, H, disc, body, var=0.05, edge_dark=0.12, bleed=1.0))
    spots = np.zeros((H, W), np.float32)
    for _k in range(n):
        a, r = rng.uniform(0, TAU_BG), rng.uniform(0, R * 0.65)
        ell(spots, cx + r * math.cos(a), cy + r * math.sin(a), R * rng.uniform(0.12, 0.25), R * rng.uniform(0.08, 0.18))
    stack.append(tint(rng, H, spots * disc, marks, 0.7, var=0.03, edge_dark=0.0, bleed=0.8))


def bolt(mask, rng, x, y, L, depth=0):
    """A forked lightning bolt downward from (x, y): jagged dabs, one or two forks."""
    while L > 6:
        seg = rng.uniform(10, 22)
        ang = math.pi + rng.uniform(-0.6, 0.6)
        dab(mask, x, y, seg, ang, w=2 if depth else 3)
        x, y = x + math.sin(ang) * seg, y - math.cos(ang) * seg
        L -= seg
        if depth < 1 and rng.random() < 0.18:
            bolt(mask, rng, x, y, L * 0.45, depth + 1)


def crush_band(stack, rng, pal, H):
    """Bible §7.5: the Crush Line drawn as a dark band labelled CRUSH: a deep-umber band along layer2's bottom, the label
    in Limelight (cream with a drawn-ink edge, build_ui_v3's TrueType reader) every 1024 px so the layer tiles."""
    import build_ui_v3 as UI
    band = np.zeros((H, W), np.float32)
    top = BG.ridge(rng, [(4, 0.6), (9, 0.4)], base=H - 168, amp=4)
    band[:] = BG._ridge_mask(H, top) * (np.arange(H)[:, None] < H - 90)                  # 78 px tall, 90 px above the foot
    stack.append(wash32(rng, H, band, BG._mix(pal["brown"], BG._rgb(v3.INK), 0.45), var=0.03, edge_dark=0.15, bleed=1.2))
    tm = UI.text_mask(UI.LIMELIGHT, "CRUSH", 58, tracking=0.12, wobble=0.5, seed=7)
    h, w = tm.shape
    fill, edge = np.zeros((H, W), np.float32), np.zeros((H, W), np.float32)
    grow = tm.copy()
    for dy, dx in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        grow = np.maximum(grow, np.roll(np.roll(tm, dy, 0), dx, 1))
    y0 = H - 129 - h // 2
    for x0 in (256 - w // 2, 1280 - w // 2):
        fill[y0:y0 + h, x0:x0 + w] = np.maximum(fill[y0:y0 + h, x0:x0 + w], tm)
        edge[y0:y0 + h, x0:x0 + w] = np.maximum(edge[y0:y0 + h, x0:x0 + w], grow)
    stack.append((np.broadcast_to(BG._rgb(v3.INK), (H, W, 3)).astype(np.float32), edge.astype(np.float32)))
    stack.append((np.broadcast_to(pal["offwhite"], (H, W, 3)).astype(np.float32), fill.astype(np.float32)))


def spiral_mask(H, cx, cy, R, k=0, arms=3, thr=0.35, sx=1.6, sz=0.55, wind=2.4, r0=0.32):
    """Arm k of `arms` interleaved log-spiral bands round (cx, cy) (angle - wind ln r), squashed by sx / sz, tapering at
    the rim: a full-size mask (x wraps)."""
    x0, x1 = int(cx - (sx + 0.1) * R), int(cx + (sx + 0.1) * R)
    y0, y1 = max(int(cy - (sz + 0.07) * R), 0), min(int(cy + (sz + 0.07) * R), H)
    X, Y = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
    u, v = (X - cx) / sx, (Y - cy) / sz
    r = np.hypot(u, v)
    sp = np.arctan2(v, u) - wind * np.log(np.maximum(r, 1.0) / R)
    ring = (r > r0 * R) & (r < R * (0.92 + 0.08 * np.sin(5 * np.arctan2(v, u))))
    m = np.zeros((H, W), np.float32)
    m[y0:y1, np.arange(x0, x1) % W] = ((np.cos(arms * sp - k * TAU_BG / arms) > thr) & ring).astype(np.float32)
    return m


def spot_swirl(stack, rng, pal, H, cx, cy, R):
    """The Great Red Spot: a brick oval eye inside three interleaved spiral arms (brick, cream, rust-brick) cut from a
    log-spiral coordinate (angle - 2.4 ln r), tapering out at the rim; UNITY turns it slowly."""
    for k, col in enumerate((pal["red"], pal["offwhite"], BG._mix(pal["red"], pal["mustard"], 0.5))):
        stack.append(tint(rng, H, spiral_mask(H, cx, cy, R, k), col, 0.8, var=0.04, edge_dark=0.04, bleed=2.0))
    eye = np.zeros((H, W), np.float32)
    ell(eye, cx, cy, R * 0.55, R * 0.24)
    stack.append(wash32(rng, H, eye, pal["red"], var=0.05, edge_dark=0.10, bleed=2.0))
    core = np.zeros((H, W), np.float32)
    ell(core, cx - R * 0.08, cy - R * 0.03, R * 0.28, R * 0.1)
    stack.append(tint(rng, H, core, BG._mix(pal["red"], pal["offwhite"], 0.4), 0.8, var=0.03, edge_dark=0.0, bleed=4.0))


def jupiter_scene(seed, deck="deck1"):
    rng = np.random.default_rng(seed)
    pal = _pal("jupiter")
    top_c = {"deck1": pal["sky"], "deck2": BG._mix(pal["sky"], pal["brown"], 0.35), "deck3": BG._mix(pal["brown"], pal["red"], 0.25),
             "deep": BG._mix(pal["brown"], BG._rgb(v3.INK), 0.35), "spot": pal["sky"]}[deck]
    low_c = {"deck1": pal["offwhite"], "deck2": pal["sky"], "deck3": BG._mix(pal["brown"], pal["mustard"], 0.3),
             "deep": pal["brown"], "spot": pal["offwhite"]}[deck]
    out = []
    # layer0: the sky gradient, the bands rolling past (decks 1-2), Io + Europa (deck 1), far cloud walls / towers / swirls
    H = 1024
    yy = (np.arange(H) / H)[:, None, None]
    sky = top_c * (1 - yy * 0.8) + low_c * yy * 0.8
    stack = Stack([(np.broadcast_to(sky, (H, W, 3)).astype(np.float32), np.ones((H, W), np.float32))])
    if deck in ("deck1", "spot", "deck2"):
        cream, rust = pal["offwhite"], pal["mustard"]
        for t in bands(rng, H, [(140, 46, cream, 0.55), (230, 30, rust, 0.5), (300, 54, cream, 0.5), (400, 22, pal["red"], 0.45),
                                (470, 40, cream, 0.45), (560, 26, rust, 0.4)], pal):
            stack.append(t)
    if deck in ("deck1", "spot"):
        moon(stack, rng, H, 1500, 120, 34, pal["mustard"], pal["red"], 7)                # Io: sulphur and brick blotches
        moon(stack, rng, H, 560, 90, 26, pal["offwhite"], pal["sky"], 5)                 # Europa: cream with tan streaks
    far = BG.ridge(rng, [(2, 0.5), (5, 0.3), (11, 0.2)], base=760, amp=40)
    wall = np.zeros((H, W), np.float32)
    cloud_bank(wall, far, rng, 40, 90, 22)
    far_c = {"deck1": BG._mix(pal["offwhite"], pal["sky"], 0.4), "spot": BG._mix(pal["offwhite"], pal["sky"], 0.4),
             "deck2": BG._mix(pal["sky"], pal["brown"], 0.45), "deck3": BG._mix(pal["brown"], pal["red"], 0.35), "deep": pal["brown"]}[deck]
    stack.append(tint(rng, H, lining(wall, 6, 4), BG._mix(far_c, pal["offwhite"], 0.5), 0.8, var=0.03, edge_dark=0.03, bleed=3.0))
    stack.append(wash32(rng, H, wall, far_c, var=0.05, edge_dark=0.05, bleed=3.0))
    if deck == "deck3":                                                                  # storm towers, lit from below
        towers = np.zeros((H, W), np.float32)
        for _k in range(6):
            cloud_tower(towers, rng.uniform(0, W), rng.uniform(820, 900), rng.uniform(300, 480), rng.uniform(70, 110), rng)
        glow = np.roll(towers, 8, 0) * (1 - towers)
        stack.append(tint(rng, H, np.maximum(glow, 0), pal["red"], 0.6, var=0.03, edge_dark=0.0, bleed=3.0))
        stack.append(wash32(rng, H, towers, BG._mix(pal["brown"], pal["red"], 0.3), var=0.05, edge_dark=0.07, bleed=2.5))
    if deck == "deep":                                                                   # slow brick-and-umber swirls (spiral bands)
        for k in range(5):
            cx, cy, R = rng.uniform(250, W - 250), rng.uniform(320, 680), rng.uniform(110, 170)
            stack.append(tint(rng, H, spiral_mask(H, cx, cy, R, 0, arms=2, thr=0.2, sx=1.8, sz=0.5, wind=2.0, r0=0.15),
                              BG._mix(pal["red"], pal["brown"], 0.5), 0.45, var=0.04, edge_dark=0.0, bleed=4.0))
    out.append(finish(stack, rng, H))
    # layer1: the nearer banks (frosted tops on deck 1), a station (deck 2), anvils + a Stormglider's shadow (deck 3),
    # the Red Spot's swirl (spot), heat shimmer (deep)
    H = 640
    stack = Stack()
    if deck == "spot":
        spot_swirl(stack, rng, pal, H, 1024, 300, 260)
    else:
        line = BG.ridge(rng, [(2, 0.45), (6, 0.35), (13, 0.2)], base=360, amp=50)
        bank = np.zeros((H, W), np.float32)
        cloud_bank(bank, line, rng, 50, 110, 18)
        body = {"deck1": pal["offwhite"], "deck2": BG._mix(pal["sky"], pal["brown"], 0.3), "deck3": BG._mix(pal["brown"], pal["mustard"], 0.25),
                "deep": BG._mix(pal["brown"], pal["red"], 0.2)}[deck]
        stack.append(tint(rng, H, lining(bank, 7, 5), pal["offwhite"] if deck == "deck1" else BG._mix(body, pal["offwhite"], 0.4), 0.85,
                          var=0.03, edge_dark=0.03, bleed=2.5))
        stack.append(wash32(rng, H, bank, body, var=0.05, edge_dark=0.07, bleed=2.5))
        if deck == "deck2":                                                              # a distant station on its gasbags
            st = np.zeros((H, W), np.float32)
            sx = rng.uniform(300, 1700)
            for k in (-1, 0, 1):
                ell(st, sx + 70 * k, 150, 42, 30)
            rect(st, sx - 100, sx + 100, 205, 228)
            for k in range(6):
                rect(st, sx - 90 + 36 * k, sx - 88 + 36 * k, 178, 206)
            stack.append(wash32(rng, H, st, BG._mix(pal["brown"], pal["sky"], 0.4), var=0.03, edge_dark=0.05, bleed=1.2))
        if deck == "deck3":
            anv = np.zeros((H, W), np.float32)
            for _k in range(3):
                ax = rng.uniform(0, W)
                cloud_tower(anv, ax, 330, 220, 90, rng)
                poly(anv, [(ax - 120, 152), (ax - 90, 100), (ax + 230, 90), (ax + 262, 112), (ax + 160, 142), (ax + 70, 166)])   # a broad anvil, sheared downwind (a thin long wedge read as a beak)
            stack.append(wash32(rng, H, anv, BG._mix(pal["brown"], pal["sky"], 0.35), var=0.05, edge_dark=0.06, bleed=2.0))
            gl = np.zeros((H, W), np.float32)                                            # a Stormglider's shadow (no face)
            gx, gy = rng.uniform(300, 1700), 230
            ell(gl, gx, gy, 46, 14)
            for sg in (-1, 1):
                poly(gl, [(gx - 20, gy), (gx + 30, gy), (gx - 10, gy + sg * 62)])
            poly(gl, [(gx - 40, gy - 3), (gx - 110, gy - 1), (gx - 40, gy + 3)])
            stack.append(tint(rng, H, gl, BG._mix(pal["brown"], BG._rgb(v3.INK), 0.3), 0.55, var=0.02, edge_dark=0.0, bleed=1.5))
        if deck == "deep":
            sh = np.zeros((H, W), np.float32)
            for _k in range(30):
                cx = rng.uniform(0, W)
                ell(sh, cx, rng.uniform(80, 400), rng.uniform(30, 80), rng.uniform(1.5, 3))
            stack.append(tint(rng, H, sh, pal["red"], 0.4, var=0.0, edge_dark=0.0, bleed=1.5))
    out.append(finish(stack, rng, H))
    # layer2 (near): wisps (decks 1 / spot), lightning under the floor (deck 2), rain curtains (deck 3), the CRUSH band (deep)
    H = 384
    stack = Stack()
    if deck in ("deck1", "spot", "deck2"):
        wisps = np.zeros((H, W), np.float32)
        for _k in range(26):
            cx, cy = rng.uniform(0, W), rng.uniform(40, 300)
            for j in range(3):
                ell(wisps, cx + 70 * j, cy + rng.uniform(-4, 4), rng.uniform(60, 140), rng.uniform(3, 7))
        stack.append(tint(rng, H, wisps, pal["offwhite"] if deck != "deck2" else BG._mix(pal["sky"], pal["offwhite"], 0.4), 0.55,
                          var=0.03, edge_dark=0.0, bleed=2.5))
    if deck == "deck2":
        glow, bolts = np.zeros((H, W), np.float32), np.zeros((H, W), np.float32)
        for _k in range(4):
            bx, by = rng.uniform(0, W), rng.uniform(110, 160)
            ell(glow, bx, by + 70, 130, 55)
            bolt(bolts, rng, bx, by, 140)
        halo = bolts.copy()
        for dy, dx in ((-2, 0), (2, 0), (0, -2), (0, 2), (-3, 0), (3, 0)):
            halo = np.maximum(halo, np.roll(np.roll(bolts, dy, 0), dx, 1))
        stack.append(tint(rng, H, glow, BG._mix(pal["offwhite"], pal["teal"], 0.3), 0.45, var=0.03, edge_dark=0.0, bleed=14.0))   # the flash (a tone)
        stack.append(tint(rng, H, halo, pal["teal"], 0.7, var=0.0, edge_dark=0.0, bleed=1.0))
        stack.append(tint(rng, H, bolts, pal["offwhite"], 1.0, var=0.0, edge_dark=0.0, bleed=0.5))
    if deck == "deck3":
        rain = np.zeros((H, W), np.float32)
        for _k in range(140):
            dab(rain, rng.uniform(0, W), rng.uniform(150, 384), rng.uniform(40, 120), 0.18, w=0)
        stack.append(tint(rng, H, rain, pal["teal"], 0.35, var=0.0, edge_dark=0.0, bleed=0.8))
    if deck == "deep":
        crush_band(stack, rng, pal, H)
    out.append(finish(stack, rng, H))
    return out, [{"n": 0, "parallax": 0.1, "y_m": -2.0}, {"n": 1, "parallax": 0.35, "y_m": -1.0},
                 {"n": 2, "parallax": 0.6, "y_m": -0.5}]


def jupiter_deck1(seed):
    return jupiter_scene(seed, "deck1")


def jupiter_deck2(seed):
    return jupiter_scene(seed, "deck2")


def jupiter_deck3(seed):
    return jupiter_scene(seed, "deck3")


def jupiter_deep(seed):
    return jupiter_scene(seed, "deep")


def jupiter_spot(seed):
    return jupiter_scene(seed, "spot")


# ---------------------------------------------------------------- Saturn (B-157, the D-141 palette): the ring world's column
# The Jupiter column's decks with Saturn's rings: seen edge-on from the equatorial decks (a bright cream line across the sky
# and its shadow band on the cloud tops) and tilted from the polar Hexagon (a wide pale arc with the Cassini gap); soft low
# sunlight (long warm lining on the cloud tops, cool slate shadows). Scenes sdeck1 / sdeck2 / sdeck3 / sdeep / hexagon
# (Saturn's keys are backgrounds/saturn/<deck1..deep, hexagon>; the scene names carry an s here only so SEEDS / PLANET_OF
# stay keyed by scene name).

def ring_line(stack, rng, pal, H, y0):
    """The ring plane edge-on (Saturn's signature from the equatorial decks, LEAD 11:4x): a bright cream line 4 px thick across
    the whole sky with a wide soft glow, a thin dark underside under it so it parts from the pale sky. Its shadow falls on the
    cloud tops (layer1), not on the sky."""
    y = np.arange(H)[:, None] + 0.5
    line = y0 + 2 * np.sin(np.arange(W)[None, :] / W * TAU_BG)
    glow = ((y > line - 16) & (y < line + 16)).astype(np.float32)
    stack.append(tint(rng, H, glow, pal["offwhite"], 0.4, var=0.0, edge_dark=0.0, bleed=8.0))
    under = ((y > line + 2) & (y < line + 4.5)).astype(np.float32)                        # the ring's unlit underside
    stack.append(tint(rng, H, under, BG._mix(pal["teal"], pal["brown"], 0.4), 0.6, var=0.0, edge_dark=0.0, bleed=0.5))
    over = ((y > line - 3.6) & (y < line - 2)).astype(np.float32)                         # an ink line above too: the bright 4 px reads as an inked stroke
    stack.append(tint(rng, H, over, BG._mix(pal["teal"], pal["brown"], 0.4), 0.55, var=0.0, edge_dark=0.0, bleed=0.5))
    core = ((y > line - 2) & (y < line + 2)).astype(np.float32)                           # 4 px: reads at 1x
    stack.append(tint(rng, H, core, pal["offwhite"], 1.0, var=0.0, edge_dark=0.0, bleed=0.4))


def ring_arc(stack, rng, pal, H, cy, R):
    """The rings tilted (seen from the high decks): a wide pale arc across the sky, the Cassini gap as a darker line."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = (xx - W / 2) / (R * 1.0), (yy - cy) / (R * 0.32)
    r = np.hypot(u, v)
    upper = yy < cy + R * 0.05
    band = ((r > 0.78) & (r < 1.0) & upper).astype(np.float32)
    stack.append(tint(rng, H, band, BG._mix(pal["offwhite"], pal["mustard"], 0.25), 0.7, var=0.03, edge_dark=0.0, bleed=2.5))
    gap = ((r > 0.885) & (r < 0.9) & upper).astype(np.float32)
    stack.append(tint(rng, H, gap, pal["teal"], 0.6, var=0.0, edge_dark=0.0, bleed=0.8))


def hexagon_walls(stack, rng, pal, H):
    """The North Polar Hexagon (LEAD option B): six upright translucent cloud curtains at different depths standing between
    the floes and the calm eye - the nearer ones wider and denser - each with swirling edges, rising wind streaks and a lit
    edge; the eye (the layer's middle) left clear. UNITY rotates the walls (moves them along x)."""
    xs = (180, 520, 760, 1290, 1530, 1870)                                                 # the eye between 760 and 1290
    for k, x0 in enumerate(xs):
        dep = (0.45, 0.8, 0.6, 0.6, 0.8, 0.45)[k]                                         # 1 = near
        w = 40 + 90 * dep
        top = 60 + 160 * (1 - dep)
        n = 40
        ys = [top + (H - top) * i / (n - 1) for i in range(n)]

        def edge(sg, k=k, x0=x0, w=w):
            return [(x0 + sg * w * (0.55 + 0.45 * (y - top) / (H - top)) + 10 * dep * math.sin(y / 38.0 + k * 1.7 + sg), y) for y in ys]
        wall = np.zeros((H, W), np.float32)
        poly(wall, [(x0 - w * 0.4, top - 20 * dep)] + edge(-1) + edge(1)[::-1] + [(x0 + w * 0.4, top - 20 * dep)])   # a rounded crown
        stack.append(tint(rng, H, wall, pal["teal"], 0.16 + 0.24 * dep, var=0.05, edge_dark=0.03, bleed=4.0))
        swirl = np.zeros((H, W), np.float32)                                              # swirling lobes along both edges
        for j in range(9):
            y = top + (H - top) * (j + 0.5) / 9
            for sg in (-1, 1):
                ex = x0 + sg * w * (0.55 + 0.45 * (y - top) / (H - top))
                ell(swirl, ex + sg * 6, y, 14 + 10 * dep, 20 + 8 * dep)
        stack.append(tint(rng, H, swirl, BG._mix(pal["teal"], pal["offwhite"], 0.35), 0.18 + 0.2 * dep, var=0.04, edge_dark=0.0, bleed=3.0))
        streaks = np.zeros((H, W), np.float32)
        for _j in range(int(14 + 20 * dep)):                                              # rising wind streaks
            dab(streaks, x0 + rng.uniform(-0.8, 0.8) * w, rng.uniform(top + 30, H - 10), rng.uniform(30, 80), rng.uniform(-0.15, 0.15), w=1)
        stack.append(tint(rng, H, streaks * wall, pal["offwhite"], 0.55 + 0.3 * dep, var=0.0, edge_dark=0.0, bleed=1.0))
        stack.append(tint(rng, H, lining(wall, 0, 3) * (1 - wall), pal["offwhite"], 0.4 + 0.3 * dep, var=0.0, edge_dark=0.0, bleed=1.5))


def saturn_scene(seed, deck="sdeck1"):
    rng = np.random.default_rng(seed)
    pal = _pal("saturn")
    top_c = {"sdeck1": pal["sky"], "sdeck2": BG._mix(pal["sky"], pal["mustard"], 0.2), "sdeck3": BG._mix(pal["sky"], pal["brown"], 0.35),
             "sdeep": BG._mix(pal["brown"], BG._rgb(v3.INK), 0.3), "hexagon": BG._mix(pal["sky"], pal["teal"], 0.25)}[deck]
    low_c = {"sdeck1": pal["offwhite"], "sdeck2": pal["offwhite"], "sdeck3": BG._mix(pal["sky"], pal["red"], 0.2),
             "sdeep": pal["brown"], "hexagon": pal["offwhite"]}[deck]
    out = []
    # layer0: the sky, pale gold and butter bands, the rings (edge-on or tilted), Titan + Enceladus, far banks
    H = 1024
    yy = (np.arange(H) / H)[:, None, None]
    sky = top_c * (1 - yy * 0.8) + low_c * yy * 0.8
    stack = Stack([(np.broadcast_to(sky, (H, W, 3)).astype(np.float32), np.ones((H, W), np.float32))])
    if deck in ("sdeck1", "sdeck2", "hexagon"):
        for t in bands(rng, H, [(170, 50, pal["offwhite"], 0.45), (260, 28, pal["mustard"], 0.4), (340, 56, pal["offwhite"], 0.4),
                                (450, 24, pal["mustard"], 0.35), (520, 40, pal["offwhite"], 0.35)], pal):
            stack.append(t)
    if deck in ("sdeck1", "sdeck2"):
        ring_line(stack, rng, pal, H, 252)                                                # frame y ~216 at 1x (layer0 top at y -36): a fifth of the way down
    if deck == "hexagon":
        ring_arc(stack, rng, pal, H, 300, 900)
    if deck in ("sdeck1", "hexagon"):
        moon(stack, rng, H, 1560, 170, 40, BG._mix(pal["mustard"], pal["red"], 0.35), pal["mustard"], 4)   # Titan: hazy orange-gold
        moon(stack, rng, H, 420, 60, 16, pal["offwhite"], pal["teal"], 2)                                  # Enceladus: tiny, bright
    far = BG.ridge(rng, [(2, 0.5), (5, 0.3), (11, 0.2)], base=760, amp=36)
    wall = np.zeros((H, W), np.float32)
    cloud_bank(wall, far, rng, 40, 90, 20)
    far_c = {"sdeck1": BG._mix(pal["offwhite"], pal["sky"], 0.35), "sdeck2": BG._mix(pal["offwhite"], pal["mustard"], 0.3),
             "sdeck3": BG._mix(pal["sky"], pal["brown"], 0.4), "sdeep": pal["brown"], "hexagon": BG._mix(pal["offwhite"], pal["teal"], 0.2)}[deck]
    stack.append(tint(rng, H, lining(wall, 7, 3), BG._mix(far_c, pal["offwhite"], 0.6), 0.85, var=0.03, edge_dark=0.02, bleed=3.0))   # low warm sunlight
    stack.append(wash32(rng, H, wall, far_c, var=0.05, edge_dark=0.05, bleed=3.0))
    if deck == "sdeep":
        for k in range(4):
            cx, cy, R = rng.uniform(250, W - 250), rng.uniform(320, 680), rng.uniform(110, 170)
            stack.append(tint(rng, H, spiral_mask(H, cx, cy, R, 0, arms=2, thr=0.2, sx=1.8, sz=0.5, wind=2.0, r0=0.15),
                              BG._mix(pal["red"], pal["brown"], 0.5), 0.4, var=0.04, edge_dark=0.0, bleed=4.0))
    out.append(finish(stack, rng, H))
    # layer1: nearer banks (the ring shadow across their tops on the equatorial decks), a helium trap rig (deck 2), soft storm
    # towers (deck 3), the Hexagon's walls (hexagon)
    H = 640
    stack = Stack()
    if deck == "hexagon":
        hexagon_walls(stack, rng, pal, H)
    else:
        line = BG.ridge(rng, [(2, 0.45), (6, 0.35), (13, 0.2)], base=360, amp=44)
        bank = np.zeros((H, W), np.float32)
        cloud_bank(bank, line, rng, 50, 110, 18)
        body = {"sdeck1": pal["offwhite"], "sdeck2": BG._mix(pal["offwhite"], pal["sky"], 0.4), "sdeck3": BG._mix(pal["sky"], pal["brown"], 0.3),
                "sdeep": BG._mix(pal["brown"], pal["red"], 0.15)}[deck]
        stack.append(tint(rng, H, lining(bank, 8, 4), pal["offwhite"], 0.85, var=0.03, edge_dark=0.02, bleed=2.5))
        stack.append(wash32(rng, H, bank, body, var=0.05, edge_dark=0.07, bleed=2.5))
        if deck in ("sdeck1", "sdeck2"):                                                  # the ring's shadow: one straight band across the cloud tops
            y = np.arange(H)[:, None] + 0.5
            yb = 300 + 4 * np.sin(np.arange(W)[None, :] / W * TAU_BG)                      # frame y ~584-622 at 1x (layer1 top at y 284)
            sh = ((y > yb) & (y < yb + 38)).astype(np.float32) * bank
            stack.append(tint(rng, H, sh, BG._mix(pal["teal"], pal["brown"], 0.3), 0.45, var=0.02, edge_dark=0.0, bleed=3.0))
        if deck == "sdeck2":                                                              # a helium trap rig on its gasbag
            st = np.zeros((H, W), np.float32)
            sx = rng.uniform(300, 1700)
            ell(st, sx, 150, 70, 36)
            poly(st, [(sx - 40, 190), (sx + 40, 190), (sx + 12, 250), (sx - 12, 250)])
            stack.append(wash32(rng, H, st, BG._mix(pal["brown"], pal["sky"], 0.45), var=0.03, edge_dark=0.05, bleed=1.2))
        if deck == "sdeck3":
            towers = np.zeros((H, W), np.float32)
            for _k in range(4):
                cloud_tower(towers, rng.uniform(0, W), 340, rng.uniform(180, 260), rng.uniform(70, 100), rng)
            stack.append(tint(rng, H, lining(towers, 6, 4), pal["offwhite"], 0.7, var=0.03, edge_dark=0.02, bleed=2.5))
            stack.append(wash32(rng, H, towers, BG._mix(pal["sky"], pal["brown"], 0.4), var=0.05, edge_dark=0.06, bleed=2.5))
    out.append(finish(stack, rng, H))
    # layer2 (near): wisps (decks 1-2, hexagon), helium-3 condensate drops (deck 2), the CRUSH band (deep)
    H = 384
    stack = Stack()
    if deck in ("sdeck1", "sdeck2", "hexagon"):
        wisps = np.zeros((H, W), np.float32)
        for _k in range(24):
            cx, cy = rng.uniform(0, W), rng.uniform(40, 300)
            for j in range(3):
                ell(wisps, cx + 70 * j, cy + rng.uniform(-4, 4), rng.uniform(60, 140), rng.uniform(3, 7))
        stack.append(tint(rng, H, wisps, pal["offwhite"], 0.5, var=0.03, edge_dark=0.0, bleed=2.5))
    if deck == "sdeck2":
        drops = np.zeros((H, W), np.float32)
        for _k in range(70):
            ell(drops, rng.uniform(0, W), rng.uniform(20, 300), rng.uniform(2.5, 4), rng.uniform(3.5, 5.5))
        stack.append(tint(rng, H, drops, pal["offwhite"], 0.8, var=0.0, edge_dark=0.0, bleed=0.8))
    if deck == "sdeep":
        crush_band(stack, rng, pal, H)
    if deck == "sdeck3":
        rain = np.zeros((H, W), np.float32)
        for _k in range(120):
            dab(rain, rng.uniform(0, W), rng.uniform(150, 384), rng.uniform(40, 110), 0.15, w=0)
        stack.append(tint(rng, H, rain, pal["teal"], 0.3, var=0.0, edge_dark=0.0, bleed=0.8))
    out.append(finish(stack, rng, H))
    return out, [{"n": 0, "parallax": 0.1, "y_m": -2.0}, {"n": 1, "parallax": 0.35, "y_m": -1.0},
                 {"n": 2, "parallax": 0.6, "y_m": -0.5}]


def saturn_sdeck1(seed):
    return saturn_scene(seed, "sdeck1")


def saturn_sdeck2(seed):
    return saturn_scene(seed, "sdeck2")


def saturn_sdeck3(seed):
    return saturn_scene(seed, "sdeck3")


def saturn_sdeep(seed):
    return saturn_scene(seed, "sdeep")


def saturn_hexagon(seed):
    return saturn_scene(seed, "hexagon")


# ---------------------------------------------------------------- Uranus (B-158, D-142): the sideways winter's column
# Each deck ships as three lit sets that share their geometry (UNITY cross-fades them by the season clock, so the clouds
# must not morph): sun_left / sun_right (the low ember sun wheels around the horizon: the lining on the sun's side of every
# cloud, a cool shade on the other, a warm horizon band) and night (the dark half: no lining, sparkles, distant ember glows),
# plus survey (the lit geometry with the methane-sage bands lifted; UNITY uses its layer0 when the Survey module is on).
# The geometry draws from rng (seed only), the shared washes from wr (seed only), the light-dependent strokes from wl, so
# the variants differ only where the light does. A fixed sun disc would repeat across the tiling layers; the light lives in
# the cloud edges instead.

U_LIGHTS = ("sun_left", "sun_right", "night", "survey")


def side_lining(mask, dy, dx):
    """A rim on one side only: the mask shifted up and toward the sun (dx < 0: the left / dx > 0: the right edges), outside it."""
    return np.clip(np.roll(mask, (-dy, dx), (0, 1)) - mask, 0, 1)


def side_faces(mask, sun, k_lit, k_shade, dy):
    """Form light on a bank lit from one side (sun -1 left / +1 right): the lit inner band along each lobe's sun-facing upper
    edge, and the shaded inner band on the far side (each the mask minus itself shifted, inside the mask)."""
    lit = mask * (1 - np.roll(mask, (dy, -sun * k_lit), (0, 1)))
    shade = mask * (1 - np.roll(mask, (0, sun * k_shade), (0, 1)))
    return np.clip(lit, 0, 1), np.clip(shade, 0, 1)


def long_shadows(mask, sun, length, thick, sink=6, win=70, gap=90):
    """The long shadows that turn (LEAD, D-142): from each lobe's peak on a bank's top profile, a long soft streak lying
    across the bank tops AWAY from the sun (sun -1: they run right, +1: left), clipped to the bank."""
    H_, W_ = mask.shape
    solid = mask > 0.5
    top = np.where(solid.any(0), solid.argmax(0), H_).astype(np.int32)
    run = np.full(W_, H_, np.int32)
    for d in range(-win, win + 1, 5):
        run = np.minimum(run, np.roll(top, d))
    out = np.zeros_like(mask)
    last = -10 ** 6
    for x in range(W_):
        if top[x] < H_ and top[x] == run[x] and x - last >= gap:
            last = x
            cx = x - sun * length / 2                                                     # starts at the peak, runs away from the sun
            ell(out, cx, top[x] + sink + thick, length / 2, thick)
            ell(out, cx - sun * length * 0.15, top[x] + sink + 3.2 * thick, length * 0.32, max(1.0, thick * 0.6))   # a fainter second streak
    return np.clip(out, 0, 1) * mask


def sparkle_field(mask, rng, n, y0, y1, r):
    """Tiny four-point crystalline sparkles (the diamond rain, frost glints)."""
    for _k in range(n):
        cx, cy = rng.uniform(0, W), rng.uniform(y0, y1)
        dab(mask, cx, cy + r, 2 * r, 0.0, w=0)
        dab(mask, cx - r, cy, 2 * r, math.pi / 2, w=0)


def uranus_scene(seed, deck="deck1", light="sun_left"):
    rng = np.random.default_rng(seed)                     # geometry: identical across the lights
    wr = np.random.default_rng(seed + 1000)               # the shared washes
    wl = np.random.default_rng(seed + 2000 + U_LIGHTS.index(light))   # light-dependent strokes
    pal = _pal("uranus")
    night = light == "night"
    sun = {"sun_left": -1, "sun_right": 1}.get(light, -1)  # survey: lit from the left
    dark = {"deck1": 0.0, "deck2": 0.15, "deck3": 0.35, "deep": 0.6}[deck]
    top_c = BG._mix(pal["sky"], pal["brown"], dark + (0.55 if night else 0.0))
    low_c = BG._mix(pal["offwhite"], pal["teal"], dark + (0.5 if night else 0.0))
    if night:
        low_c = BG._mix(low_c, pal["brown"], 0.4)
    out = []
    # layer0: the fog sky, the methane bands (a whisper; lifted in survey), the warm horizon (lit), Miranda (deck 1), far banks
    H = 1024
    yy = (np.arange(H) / H)[:, None, None]
    sky = top_c * (1 - yy * 0.7) + low_c * yy * 0.7
    stack = Stack([(np.broadcast_to(sky, (H, W, 3)).astype(np.float32), np.ones((H, W), np.float32))])
    band_specs = [(200, 40, pal["mustard"]), (320, 26, pal["offwhite"]), (430, 50, pal["mustard"]), (560, 30, pal["teal"])]
    band_op = 0.4 if light == "survey" else 0.07
    for t in bands(wr, H, [(y0, th, col, band_op) for y0, th, col in band_specs], pal):
        stack.append(t)
    import copy
    rp = copy.deepcopy(rng)                                 # replay the far banks' geometry: layer0's roll, the same in every light
    if deck == "deck1":
        rp.uniform(300, 1700)
    wall_p = np.zeros((H, W), np.float32)
    cloud_bank(wall_p, BG.ridge(rp, [(2, 0.5), (5, 0.3), (11, 0.2)], base=760, amp=34), rp, 40, 90, 20)
    k0 = geometry_roll(wall_p)
    del wall_p, rp
    sx = ({-1: 360.0, 1: 1560.0}[sun] + k0) % W            # the low sun, on its side of the 1920 frame after the roll
    if not night:
        y = np.arange(H)[:, None] + 0.5
        dxs = np.abs(np.arange(W)[None, :] - sx)
        ramp = np.clip(1 - np.minimum(dxs, W - dxs) / 1100.0, 0, 1)                      # warm toward the sun's side (wrapped)
        horizon = (((y > 380) & (y < 760)).astype(np.float32) * ramp).astype(np.float32)          # frame y ~344-724: above the near banks
        stack.append(tint(wl, H, horizon, BG._mix(pal["offwhite"], pal["red"], 0.45), 0.4, var=0.02, edge_dark=0.0, bleed=40.0))
        glow = np.zeros((H, W), np.float32)
        ell(glow, sx, 470, 150, 110)
        stack.append(tint(wl, H, glow, BG._mix(pal["offwhite"], pal["red"], 0.2), 0.45, var=0.0, edge_dark=0.0, bleed=45.0))   # its haze
        disc = np.zeros((H, W), np.float32)
        ell(disc, sx, 470, 17, 17)                                                      # frame y ~434, clear of the near banks
        stack.append(tint(wl, H, disc, pal["offwhite"], 1.0, var=0.0, edge_dark=0.0, bleed=1.2))      # the distant sun: small, bright
    if deck == "deck1":
        mx, my = rng.uniform(300, 1700), 140.0
        moon(stack, wr, H, mx, my, 22, BG._mix(pal["offwhite"], pal["sky"], 0.3), pal["teal"], 3)    # Miranda
        plume = np.zeros((H, W), np.float32)
        for t in np.linspace(0, 1, 12):
            ell(plume, mx + 6 * math.sin(t * 5), my - 22 - 50 * t, 4 + 8 * t, 5)                     # its ice geyser
        stack.append(tint(wr, H, plume, pal["offwhite"], 0.45, var=0.0, edge_dark=0.0, bleed=3.0))
    far = BG.ridge(rng, [(2, 0.5), (5, 0.3), (11, 0.2)], base=760, amp=34)
    wall = np.zeros((H, W), np.float32)
    cloud_bank(wall, far, rng, 40, 90, 20)
    far_c = BG._mix(BG._mix(pal["sky"], pal["teal"], 0.3 + dark), pal["brown"], 0.5 if night else 0.0)
    if not night:
        stack.append(tint(wl, H, side_lining(wall, 6, 5 * sun), BG._mix(pal["offwhite"], pal["red"], 0.25), 0.85, var=0.02, edge_dark=0.0, bleed=2.5))
    stack.append(wash32(wr, H, wall, far_c, var=0.05, edge_dark=0.05, bleed=3.0))
    if not night:
        lit, shade = side_faces(wall, sun, 18, 30, 8)
        stack.append(tint(wl, H, lit, BG._mix(pal["offwhite"], pal["red"], 0.15), 0.55, var=0.02, edge_dark=0.0, bleed=5.0))   # the sun-facing upper edges
        stack.append(tint(wl, H, shade, BG._mix(pal["teal"], pal["brown"], 0.3), 0.42, var=0.02, edge_dark=0.0, bleed=7.0))    # the far sides
        stack.append(tint(wl, H, long_shadows(wall, sun, 300, 5), pal["brown"], 0.5, var=0.0, edge_dark=0.0, bleed=4.0))      # long shadows, leaning away
    else:
        y = np.arange(H)[:, None] + 0.5
        haze = np.broadcast_to(((y > 600) & (y < 780)).astype(np.float32), (H, W)).copy()
        stack.append(tint(wl, H, haze, pal["red"], 0.14, var=0.02, edge_dark=0.0, bleed=40.0))      # night: the ember only as a low haze
        sp0 = np.zeros((H, W), np.float32)
        sparkle_field(sp0, wl, 40, 80, 620, 3)                                                       # night glints, on the opaque far layer
        stack.append(tint(wl, H, sp0, pal["offwhite"], 0.85, var=0.0, edge_dark=0.0, bleed=0.4))
    out.append(finish(stack, wr, H, roll=k0))
    # layer1: nearer fog banks, the same light; the deep: slow swirls
    H = 640
    stack = Stack()
    line = BG.ridge(rng, [(2, 0.45), (6, 0.35), (13, 0.2)], base=360, amp=44)
    bank = np.zeros((H, W), np.float32)
    cloud_bank(bank, line, rng, 50, 110, 18)
    body = BG._mix(BG._mix(pal["offwhite"], pal["sky"], 0.4 + dark), pal["brown"], 0.45 if night else 0.0)
    stack.append(wash32(wr, H, bank, body, var=0.05, edge_dark=0.07, bleed=2.5))
    if not night:                                         # painted onto the bank: the alpha is the same in every light (D-142)
        rim, _ = side_faces(bank, sun, 7, 1, 8)
        stack.paint(tint(wl, H, rim, BG._mix(pal["offwhite"], pal["red"], 0.2), 1.0, var=0.02, edge_dark=0.0, bleed=1.5))       # the lit rim, inside
        lit, shade = side_faces(bank, sun, 26, 44, 10)
        stack.paint(tint(wl, H, lit, BG._mix(pal["offwhite"], pal["red"], 0.15), 0.65, var=0.02, edge_dark=0.0, bleed=6.0))
        stack.paint(tint(wl, H, shade, BG._mix(pal["teal"], pal["brown"], 0.35), 0.48, var=0.02, edge_dark=0.0, bleed=8.0))
        stack.paint(tint(wl, H, long_shadows(bank, sun, 480, 8), pal["brown"], 0.6, var=0.0, edge_dark=0.0, bleed=5.0))      # long shadows, leaning away
    if deck == "deep":
        for k in range(3):
            cx, cy, R = rng.uniform(250, W - 250), rng.uniform(120, 300), rng.uniform(90, 140)
            stack.append(tint(wr, H, spiral_mask(H, cx, cy, R, 0, arms=2, thr=0.2, sx=1.8, sz=0.5, wind=2.0, r0=0.15),
                              BG._mix(pal["teal"], pal["brown"], 0.5), 0.35, var=0.03, edge_dark=0.0, bleed=4.0))
    out.append(finish(stack, wr, H, roll=geometry_roll(bank)))
    # layer2 (near): fog wisps, hail (deck 3), the diamond-rain sparkle + the CRUSH band (deep), night sparkles + ember glows
    H = 384
    stack = Stack()
    wisps = np.zeros((H, W), np.float32)
    for _k in range(22):
        cx, cy = rng.uniform(0, W), rng.uniform(40, 280)
        for j in range(3):
            ell(wisps, cx + 70 * j, cy + rng.uniform(-4, 4), rng.uniform(60, 140), rng.uniform(3, 7))
    stack.append(tint(wr, H, wisps, BG._mix(pal["offwhite"], pal["brown"], 0.5 if night else 0.0), 0.45, var=0.03, edge_dark=0.0, bleed=2.5))
    if deck == "deck3":
        hail = np.zeros((H, W), np.float32)
        for _k in range(110):
            dab(hail, rng.uniform(0, W), rng.uniform(120, 384), rng.uniform(14, 30), 0.25, w=1)
        stack.append(tint(wr, H, hail, pal["offwhite"], 0.55, var=0.0, edge_dark=0.0, bleed=0.6))
    sp = np.zeros((H, W), np.float32)
    sparkle_field(sp, rng, {"deck1": 0, "deck2": 10, "deck3": 40, "deep": 90}[deck], 20, 300, 3)              # the same in every light
    stack.append(tint(wr, H, sp, pal["offwhite"], 0.9, var=0.0, edge_dark=0.0, bleed=0.4))
    if deck == "deep":
        crush_band(stack, wr, pal, H)
    out.append(finish(stack, wr, H, roll=geometry_roll(wisps)))
    return out, [{"n": 0, "parallax": 0.1, "y_m": -2.0}, {"n": 1, "parallax": 0.35, "y_m": -1.0},
                 {"n": 2, "parallax": 0.6, "y_m": -0.5}]


def uranus_deck_check(out_dir, deck):
    """D-142 proven, not eyeballed (LEAD): the md5 of every layer's alpha in all four lights of one deck (the preview's
    layer PNGs under <out_dir>/b158/u<deck>_<light>/); fails if any layer's alpha differs across the lights, if a
    render is missing, or if a render is older than this file (a stale render from before a code change)."""
    import hashlib
    from meridian import pngio
    code_t = os.path.getmtime(os.path.abspath(__file__))
    ok = True
    for n in range(3):
        sums = {}
        for light in U_LIGHTS:
            path = os.path.join(out_dir, "b158", f"u{deck}_{light}", f"layer{n}_color.png")
            if not os.path.isfile(path):
                print(f"  {deck} layer{n} {light}: MISSING")
                ok = False
                continue
            if os.path.getmtime(path) < code_t:
                print(f"  {deck} layer{n} {light}: STALE (rendered before the current code)")
                ok = False
            sums[light] = hashlib.md5(pngio.read_png_np(path)[..., 3].tobytes()).hexdigest()
        same = len(sums) == len(U_LIGHTS) and len(set(sums.values())) == 1
        ok = ok and same
        print(f"{deck} layer{n} alpha md5: " + ", ".join(f"{k} {v[:10]}" for k, v in sums.items()) + ("  SAME" if same else "  DIFFER"))
    print(f"{deck}: {'PASS' if ok else 'FAIL'} (D-142: one alpha per layer across {', '.join(U_LIGHTS)})")
    return ok


def _uranus_fn(deck, light):
    return lambda seed: uranus_scene(seed, deck, light)


SCENES = {("earth", "forest"): earth_forest, ("earth", "coast"): earth_coast, ("mars", "plains"): mars_plains,
          ("mars", "canyon"): mars_canyon, ("mars", "storm"): mars_storm,
          ("mercury", "day"): mercury_day, ("mercury", "twilight"): mercury_twilight, ("mercury", "night"): mercury_night,
          ("venus", "deck"): venus_deck, ("venus", "surface"): venus_surface,
          ("jupiter", "deck1"): jupiter_deck1, ("jupiter", "deck2"): jupiter_deck2, ("jupiter", "deck3"): jupiter_deck3,
          ("jupiter", "deep"): jupiter_deep, ("jupiter", "spot"): jupiter_spot,
          ("saturn", "deck1"): saturn_sdeck1, ("saturn", "deck2"): saturn_sdeck2, ("saturn", "deck3"): saturn_sdeck3,   # the export keys
          ("saturn", "deep"): saturn_sdeep, ("saturn", "hexagon"): saturn_hexagon,
          ("saturn", "sdeck1"): saturn_sdeck1, ("saturn", "sdeck2"): saturn_sdeck2, ("saturn", "sdeck3"): saturn_sdeck3,   # the preview names
          ("saturn", "sdeep"): saturn_sdeep}
SEEDS = {"forest": 13301, "coast": 13302, "canyon": 14101, "storm": 14102, "plains": 14103, "day": 14501, "twilight": 14502, "night": 14503,
         "deck": 14701, "surface": 14702, "deck1": 14801, "deck2": 14802, "deck3": 14803, "deep": 14804, "spot": 14805,
         "sdeck1": 14901, "sdeck2": 14902, "sdeck3": 14903, "sdeep": 14904, "hexagon": 14905}
PLANET_OF = {"forest": "earth", "coast": "earth", "canyon": "mars", "storm": "mars", "plains": "mars", "day": "mercury", "twilight": "mercury", "night": "mercury",
             "deck": "venus", "surface": "venus",
             "deck1": "jupiter", "deck2": "jupiter", "deck3": "jupiter", "deep": "jupiter", "spot": "jupiter",
             "sdeck1": "saturn", "sdeck2": "saturn", "sdeck3": "saturn", "sdeep": "saturn", "hexagon": "saturn"}
for _d, _s0 in (("deck1", 15001), ("deck2", 15002), ("deck3", 15003), ("deep", 15004)):     # Uranus (D-142): four decks x four lights
    for _l in U_LIGHTS:
        SCENES[("uranus", f"{_d}_{_l}")] = _uranus_fn(_d, _l)                              # the export key backgrounds/uranus/<deck>_<light>
        SCENES[("uranus", f"u{_d}_{_l}")] = _uranus_fn(_d, _l)                             # the preview name (SEEDS / PLANET_OF are keyed by name)
        SEEDS[f"u{_d}_{_l}"] = _s0                                                         # one seed per deck: the lights share their geometry
        PLANET_OF[f"u{_d}_{_l}"] = "uranus"


# ---------------------------------------------------------------- lock-free preview: 1080p composite at 1x + the 2x seam check

def preview(out_dir, scenes=("forest", "coast"), from_png=False):
    """from_png: rebuild the review from the layer PNGs a previous preview wrote (rolled to their quiet seam column
    the way finish() now rolls them: the same pixels the generator writes), without the FFT washes (light)."""
    import json
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import pngio
    import build_c2_ground_strip as GS
    import preview_c2_earth_rigs as PR
    for scene in scenes:
        planet = PLANET_OF[scene]
        tag = {"earth": "b133", "mars": "b141", "mercury": "b145", "venus": "b147", "jupiter": "b155", "saturn": "b157", "uranus": "b158"}[planet]
        d = os.path.join(out_dir, tag, scene)
        os.makedirs(d, exist_ok=True)
        u8, info = [], []
        if from_png:
            layers = json.load(open(os.path.join(d, f"{scene}.json"), encoding="utf-8"))["layers"]
            imgs = []
            for L in layers:
                q = pngio.read_png_np(os.path.join(d, f"layer{L['n']}_color.png"))
                imgs.append(np.roll(q, -seam_column(q), axis=1))
        else:
            gen, layers = SCENES[(planet, scene)](SEEDS[scene])
            imgs = [BG.to_u8(rgb, a) for rgb, a in gen]
            del gen
        for img, L in zip(imgs, layers):
            p = os.path.join(d, f"layer{L['n']}_color.png")
            n = pngio.write_png(p, img)
            L["height_px"] = img.shape[0]
            u8.append(img)
            info.append((p, n, BG.seam(img)))
        del imgs
        with open(os.path.join(d, f"{scene}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"key": f"backgrounds/{planet}/{scene}", "style": "v3", "ppu": v3.PPU, "anchor": "bottom", "tile_x": True,
                       "layers": layers}, f, indent=2)
        # (1) the 1080p frame at 1x: layers bottom-anchored by y_m, ground strips under the line, the surveyor
        F = np.zeros((1080, 1920, 3), np.float32)
        gl = 860
        for img, L in zip(u8, layers):
            h = img.shape[0]
            y_bot = gl + int(round(-L["y_m"] * v3.PPU))
            y_top = y_bot - h
            src = img[max(0, -y_top):h - max(0, y_bot - 1080), :1920]
            review._over(F, src, 0, max(0, y_top))
        if planet == "mars":                                      # B-139 regolith strip (build_c2_mars_ground)
            import build_c2_mars_ground as MG
            S, _w = GS.sheets(("regolith",), MG.mats)
            strip = "regolith"
        elif planet in ("jupiter", "saturn", "uranus"):           # B-155 / B-157 / B-158: a floe of ice (the tiles; D-137's caps unused here)
            JF = __import__(f"build_c2_{planet}_floes")
            S, _w = JF.sheets(("ice",))
            strip = "ice"
        elif planet in ("mercury", "venus"):                      # no strip yet: the Earth stone recipe stands in
            S, _w = GS.sheets(("stone",))
            strip = "stone"
        else:
            S, _w = GS.sheets()
            strip = "sand" if scene == "coast" else "grass"      # the coast stands on the B-130 sand variant
        rnd = np.random.default_rng(5)
        for c in range(30):
            im = S[strip][int(rnd.integers(0, 8))]
            y0 = gl - (GS.FH - int(round(GS.SURF * 64)))
            review._over(F, im[:max(0, min(GS.FH, 1080 - y0))], c * 64, y0)
            F[min(y0 + GS.FH, 1080):, c * 64:c * 64 + 64] = np.array(S[strip][0][-4, 30, :3], np.float32) / 255
        try:
            fr, piv = PR.surveyor_frame()
            review._over(F, fr, 860, gl - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
        except Exception:  # noqa: BLE001
            pass
        review._label(F, f"{tag[0]}-{tag[1:]} {planet} {scene}: 1920x1080 at 1x (ppu 64), layers by y_m, {strip} ground strips, the surveyor (2 m)", 6, 6)
        # (2) each layer tiled 2x (half size), and the seam column at 1x
        rows = [F]
        for (p, n, s), img, L in zip(info, u8, layers):
            t = np.tile(img, (1, 2, 1))[::2, ::2]
            panel = np.tile(review.PAPER, (t.shape[0] + 40, 2048 + 16, 1)).astype(np.float32)
            chk = (((np.arange(t.shape[0])[:, None] // 16) + (np.arange(t.shape[1])[None, :] // 16)) % 2) * 0.15 + 0.7
            panel[30:30 + t.shape[0], 8:8 + t.shape[1]] = chk[..., None]
            review._over(panel, t, 8, 30)
            panel[30:30 + t.shape[0], 8 + 1024] = (0.8, 0.2, 0.2)
            review._label(panel, f"layer{L['n']} {img.shape[1]}x{img.shape[0]} {n // 1024} kb (<= 4096)  2x tiled at half size, seam at the red line: "
                                 f"score {s:.2f} (wrap step / interior step, pass <= 2.0)  parallax {L['parallax']}  y_m {L['y_m']}", 6, 6, scale=1)
            seamcrop = np.concatenate([img[:, -200:], img[:, :200]], axis=1)
            sc = np.tile(review.PAPER, (seamcrop.shape[0] + 10, 400 + 16, 1)).astype(np.float32)
            sc[:seamcrop.shape[0], 8:408] = chk[:seamcrop.shape[0], :400, None] if chk.shape[0] >= seamcrop.shape[0] else 0.8
            review._over(sc, seamcrop, 8, 0)
            rows.append(panel)
            rows.append(np.pad(sc, ((0, 0), (0, max(0, 2064 - sc.shape[1])), (0, 0)), constant_values=0.91)[:, :2064])
        Wd = max(r.shape[1] for r in rows)
        img = np.vstack([np.pad(r, ((0, 0), (0, Wd - r.shape[1]), (0, 0)), constant_values=0.91) for r in rows])
        review._label(img, __import__("time").strftime("%m-%d %H:%M") + " preview (not exported)", 2, img.shape[0] - 16)
        out = os.path.join(out_dir, f"review_{tag}_{planet}_{scene}_preview.png")
        review.write(out, img)
        print(scene, ", ".join(f"layer{i} {u8[i].shape[1]}x{u8[i].shape[0]} {n // 1024} KB seam {s:.2f}" for i, (p, n, s) in enumerate(info)), "->", out)


if __name__ == "__main__":
    if "--uranus-check" in sys.argv:                      # python -I build_backdrop_v3.py <preview dir> --uranus-check deck2
        sys.exit(0 if uranus_deck_check(sys.argv[1], sys.argv[sys.argv.index("--uranus-check") + 1]) else 1)
    preview(sys.argv[1], tuple(sys.argv[2].split(",")) if len(sys.argv) > 2 else ("forest", "coast"), from_png="--from-png" in sys.argv)
