"""B-259 (art v7, D-205; STYLE_V7 section 3: scanned earth through the same paint treatment, as tiles on today's sizes):
THE UNDERGROUND, pilot. numpy only:  python -I build_v7_underground.py <review sheet png>
WRITTEN 11-10 15:1x AS SOURCE, UNRUN (UNITY's want and the RAM gate); its sheet waits for B-258 part 3's verdict (one
treatment for the surface and the ground).

Reads the painted ground maps (v7_frame_pieces.py ground: blender/preview/b258/pieces/ground_<name>.png, 1024 x 1024,
tiling, laid at 256 px per metre = 4 m) and today's v3 files (Assets/_Game/Art/terrain/earth/ground_fill_color.png,
512 x 512 = 8 m at 64 px per metre; back_wall_t1_color.png, 256 x 256 = 4 m). Makes, at 64 and at 96 px per metre:
  the FILL of tier 1 (topsoil) and tier 2 (subsoil with stones) as 8 m tiles (two copies of a 4 m map cross-faded by a
      mask of the tile's own period, so the 4 m period does not show and the 8 m tile still butts);
  the BACK WALL of each (the same earth in shade: darker, cooler, calmer: what stands behind a dug hole);
  A MOCK: a 10 m shaft and a side tunnel with the rim's shadow, the grey 1.84 m mannequin standing in both;
  each tile BUTTED across a screen width; today's v3 fill and wall beside it at the same size;
  THE FIGURE'S CONTRAST against the wall as a number (the WCAG ratio of the mannequin's grey to the wall behind it).
Download list for the real tiers (Poly Haven, CC0; real sizes from its API; NOT fetched yet): roots (1.67 m), brown_mud_02
(1.3 m: plant debris, roots, sticks), red_mud_stones (1.5 m), brown_mud_rocks_01 (1.3 m), rock_face_03 (2.7 m),
cliff_side (1.83 m). In hand: brown_mud_leaves_01, excavated_soil_wall, red_laterite_soil_stones, forest_floor.
NOTE: a 1.3 m scan laid over 4 m shows its leaves and stones three times life size, as the stage's plants are (x2.5-3).
"""
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from meridian import pngio  # noqa: E402
import paint_v6 as PT  # noqa: E402
import v7_paint as VP  # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
PD = os.path.join(REPO, "blender", "preview", "b258", "pieces")
OUT = os.path.join(REPO, "blender", "preview", "b259")
V3 = os.path.join(REPO, "Assets", "_Game", "Art", "terrain", "earth")
W, H, GROW = 1920, 1080, 96                       # the frame; the ground line's row
MAP_PPM, TILE_M = 256.0, 8.0
SHADE = np.array([0.52, 0.56, 0.64], np.float32)  # the back wall: the earth out of the light
TIERS = {1: (("excavated_soil_wall", 0.65), ("brown_mud_leaves_01", 0.35)), 2: (("red_laterite_soil_stones", 1.0),)}
SPLIT_M = 5.0                                     # where tier 2 begins in the mock (the game's depths are UNITY's)


def ground_map(name, ppm):
    tex = pngio.read_png_np(os.path.join(PD, f"ground_{name}.png")).astype(np.float32)[..., :3] / 255.0
    s = ppm / MAP_PPM
    return VP.resize(np.concatenate([tex, np.ones(tex.shape[:2] + (1,), np.float32)], axis=2), s)[..., :3] if abs(s - 1) > 1e-3 else tex


def fill_tile(tier, ppm, seed=0):
    """An 8 m tile of a tier's fill at ppm px per metre: every map laid twice (straight, and mirrored with an offset),
    cross-faded by a smooth mask that has the TILE's period; several maps mixed by a second such mask."""
    n = int(TILE_M * ppm)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    w2 = 2 * math.pi / n

    def mask(p1, p2, sharp=2.2):
        m = np.sin(xx * w2 + p1 + 1.3 * np.sin(yy * w2 * 2 + p2)) * np.sin(yy * w2 + p2 + 1.1 * np.sin(xx * w2 * 2 + p1))
        return np.clip(m * sharp + 0.5, 0, 1)[..., None]
    out = None
    for i, (name, wgt) in enumerate(TIERS[tier]):
        tex = ground_map(name, ppm)
        th, tw = tex.shape[:2]                                                               # 4 m: it divides the tile
        ys, xs = np.arange(n), np.arange(n)
        a = tex[np.ix_(ys % th, xs % tw)]
        b = tex[np.ix_((ys + int(0.43 * th)) % th, (-xs + int(0.31 * tw)) % tw)]
        m = mask(0.7 + seed + i, 2.1 + 2 * i)
        layer = a * (1 - m) + b * m
        if out is None:
            out = layer
        else:                                                                                # a second map in patches: about wgt of the tile
            mm = np.clip(mask(4.0 + i, 0.4 + seed, sharp=3.0) - (0.5 - wgt), 0, 1)
            out = out * (1 - mm) + layer * mm
    return np.clip(out, 0, 1)


def wall_of(fill):
    """The back wall: the fill in shade (darker, cooler), its small contrasts calmed, so a figure reads against it."""
    calm = np.dstack([PT.box(fill[..., c], 1) for c in range(3)])
    mean = calm.mean(axis=(0, 1), keepdims=True)
    return np.clip((mean + (calm - mean) * 0.70) * SHADE[None, None, :], 0, 1)


def lum(rgb):
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return lin @ np.array([0.2126, 0.7152, 0.0722], np.float32)


def contrast(a, b):
    la, lb = float(lum(np.asarray(a, np.float32))), float(lum(np.asarray(b, np.float32)))
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def rbox(xm, ym, cx, cy, hx, hy, r):
    """The signed distance (metres) to a rounded box."""
    qx, qy = np.abs(xm - cx) - (hx - r), np.abs(ym - cy) - (hy - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def mock(ppm, fills, walls):
    """A 10 m shaft and a side tunnel in the two tiers, the mannequin in both. -> (H x W x 3, the wall's mean colour
    behind the shaft's mannequin)."""
    k = float(ppm)
    xm = ((np.arange(W, dtype=np.float32) + 0.5) / k)[None, :]
    ym = ((GROW - (np.arange(H, dtype=np.float32) + 0.5)) / k)[:, None]
    depth = -ym
    n = fills[1].shape[0]
    ys, xs = np.arange(H) - GROW, np.arange(W)
    rng = np.random.default_rng(4)
    split = SPLIT_M + PT.fbm(1, W, 200.0, rng, 3)[0][None, :] * 0.35
    t2 = np.clip((depth - split) / 0.35 + 0.5, 0, 1)[..., None]
    fill = fills[1][np.ix_(ys % n, xs % n)] * (1 - t2) + fills[2][np.ix_(ys % n, xs % n)] * t2
    wall = walls[1][np.ix_(ys % n, xs % n)] * (1 - t2) + walls[2][np.ix_(ys % n, xs % n)] * t2
    wall = wall * np.clip(1 - 0.035 * depth, 0.6, 1)[..., None]                                # darker with depth (U-196's sense)
    sx = W / k / 2.0 + 1.0                                                                      # the shaft's middle
    d = np.minimum(rbox(xm, ym, sx, -4.5, 1.0, 5.5, 0.35), rbox(xm, ym, sx - 3.25, -9.0, 3.25, 1.0, 0.40))
    inside = np.clip(0.5 - d * k / 1.5, 0, 1)[..., None]
    rim = np.clip(1 + d / 0.55, 0, 1)[..., None] ** 1.6                                          # the rim's shadow: darkest at the edge, gone 0.55 m in
    wall = wall * (1 - 0.42 * rim)
    seat = np.clip(1 - np.abs(d - 0.02) / 0.035, 0, 1)[..., None]                                # where the fill meets the hole: a dark seam
    img = (fill * (1 - 0.35 * seat)) * (1 - inside) + wall * inside
    sky = np.array([0.80, 0.86, 0.76], np.float32)
    img[:GROW] = sky[None, None, :]
    strip = pngio.read_png_np(os.path.join(PD, "ground_forest_floor.png")).astype(np.float32)[..., :3] / 255.0
    sh = max(4, int(0.30 * k))
    band = VP._axis(VP.resize(np.concatenate([strip, np.ones(strip.shape[:2] + (1,), np.float32)], axis=2), k / MAP_PPM)[..., :3], sh, 0)
    cols = np.arange(W) % band.shape[1]
    open_ = (np.abs(xm - sx) < 1.0)[0]
    img[GROW - sh:GROW, ~open_] = band[:, cols][:, ~open_]
    fx, fy = sx * k + 0.3 * k, GROW + 10.0 * k
    behind = wall[int(fy - 1.6 * k):int(fy - 0.3 * k), int(fx - 0.4 * k):int(fx + 0.4 * k)].reshape(-1, 3).mean(axis=0)
    VP.mannequin(img, k, fx, fy)
    VP.mannequin(img, k, (sx - 4.6) * k, fy)
    return np.clip(img, 0, 1), behind


def v3_tile(name, to_px):
    p = os.path.join(V3, name)
    if not os.path.isfile(p):
        return None
    a = pngio.read_png_np(p).astype(np.float32) / 255.0
    return VP.resize(a, to_px / a.shape[1]) if a.shape[1] != to_px else a


def butted(tile, h=256):
    """The tile laid side by side across the screen, its top h rows."""
    n = tile.shape[1]
    return tile[:h][:, np.arange(W) % n]


def sheet(out):
    import review
    os.makedirs(OUT, exist_ok=True)
    paper = np.array(review.PAPER, np.float32)

    def head(text, h=20):
        hd = np.tile(paper, (h, W, 1)).astype(np.float32)
        review._label(hd, text[:310], 6, 4, scale=1)
        return hd

    def save(name, rgb):
        pngio.write_png(os.path.join(OUT, name), np.concatenate([pngio.to_u8(rgb), np.full(rgb.shape[:2] + (1,), 255, np.uint8)], axis=2))
    rows = [head("B-259 (ART v7): THE UNDERGROUND, pilot - Earth's first two tiers from CC0 scanned soil (Poly Haven), laid as strokes and made to tile. PREVIEW, nothing exported", 26)]
    lines = []
    for ppm in (64, 96):
        t0 = time.time()
        fills = {t: fill_tile(t, ppm, seed=t) for t in (1, 2)}
        walls = {t: wall_of(fills[t]) for t in (1, 2)}
        img, behind = mock(ppm, fills, walls)
        for t in (1, 2):
            save(f"fill_t{t}_{ppm}.png", fills[t])
            save(f"back_wall_t{t}_{ppm}.png", walls[t])
        save(f"mock_{ppm}.png", img)
        rows += [head(f"A 10 m SHAFT AND A SIDE TUNNEL at {ppm} px per metre: tier 1 above {SPLIT_M:g} m, tier 2 below; the back wall is the same earth in shade; a grey 1.84 m mannequin in both"), img]
        c7 = contrast(VP.GREY, behind)
        lines.append(f"{ppm} px per metre: an 8 m fill tile is {fills[1].shape[0]} px a side ({fills[1].shape[0] ** 2 * 4 / 1048576:.1f} MB RGBA32); the figure's contrast against the v7 wall "
                     f"(the mannequin's grey to the wall's mean behind it): {c7:.2f} : 1; made in {time.time() - t0:.1f} s")
        if ppm == 64:
            rows += [head("EACH TILE BUTTED ACROSS A SCREEN WIDTH at 64 px per metre (its top 4 m): the tier 1 fill | the tier 2 fill | the tier 1 back wall"),
                     butted(fills[1]), butted(fills[2]), butted(walls[1])]
            f3, w3 = v3_tile("ground_fill_color.png", 512), v3_tile("back_wall_t1_color.png", 256)
            if f3 is not None:
                rows += [head("TODAY'S v3 beside it at the same size: ground_fill (tier 1) | back_wall_t1 over the fill at 0.45 (my stand-in for how the game seats it)"), butted(f3[..., :3])]
                if w3 is not None:
                    under = butted(f3[..., :3]) * 0.45
                    bw = butted(w3)
                    v3wall = bw[..., :3] * bw[..., 3:4] + under * (1 - bw[..., 3:4])
                    rows.append(v3wall)
                    lines.append(f"the same grey against today's v3 wall (as stood in above): {contrast(VP.GREY, v3wall.reshape(-1, 3).mean(axis=0)):.2f} : 1")
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:310], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-259: the v7 underground pilot (painted scans, numpy; nothing exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    sheet(sys.argv[1])
