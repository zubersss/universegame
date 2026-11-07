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


def _pal():
    return {k: BG._rgb(v) for k, v in v3.PALETTES["earth"].items()}


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


def finish(stack, rng, H):
    """Composite + paper grain, then roll the (periodic) layer so the wrap sits on the quietest column: a soft edge
    that happened to fall on column 0 scored 2.7 on the seam check although the tile is continuous."""
    rgb, a = BG._composite(stack)
    rgb = rgb * BG.paper(rng, H)[..., None]
    k = seam_column(BG.to_u8(rgb, a))
    return np.roll(rgb, -k, axis=1), np.roll(a, -k, axis=1)


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


SCENES = {("earth", "forest"): earth_forest, ("earth", "coast"): earth_coast}
SEEDS = {"forest": 13301, "coast": 13302}


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
        d = os.path.join(out_dir, "b133", scene)
        os.makedirs(d, exist_ok=True)
        u8, info = [], []
        if from_png:
            layers = json.load(open(os.path.join(d, f"{scene}.json"), encoding="utf-8"))["layers"]
            imgs = []
            for L in layers:
                q = pngio.read_png_np(os.path.join(d, f"layer{L['n']}_color.png"))
                imgs.append(np.roll(q, -seam_column(q), axis=1))
        else:
            gen, layers = SCENES[("earth", scene)](SEEDS[scene])
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
            json.dump({"key": f"backgrounds/earth/{scene}", "style": "v3", "ppu": v3.PPU, "anchor": "bottom", "tile_x": True,
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
        S, _w = GS.sheets()
        strip = "sand" if scene == "coast" else "grass"          # the coast stands on the B-130 sand variant
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
        review._label(F, f"b-133 earth {scene}: 1920x1080 at 1x (ppu 64), layers by y_m, b-130 ground strips, the surveyor (2 m)", 6, 6)
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
        out = os.path.join(out_dir, f"review_b133_earth_{scene}_preview.png")
        review.write(out, img)
        print(scene, ", ".join(f"layer{i} {u8[i].shape[1]}x{u8[i].shape[0]} {n // 1024} KB seam {s:.2f}" for i, (p, n, s) in enumerate(info)), "->", out)


if __name__ == "__main__":
    preview(sys.argv[1], tuple(sys.argv[2].split(",")) if len(sys.argv) > 2 else ("forest", "coast"), from_png="--from-png" in sys.argv)
