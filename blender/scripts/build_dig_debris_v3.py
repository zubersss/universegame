"""B-232 (D-183 / D-184): dig debris in v3 ink, cream + ink so UNITY tints it to the ground, as B-226's shovel flick.

  fx/dig_clods/t<n>   n = 1..5 (Topsoil, Subsoil, Stone, Deep, Core): 6 frames x 128x128 @ PPU 64 (2 m), pivot [0.5, 0.5] =
                      the opened cell, clip 'tumble' (once, 12 fps): four clods thrown up and out of the cell, tumbling as they
                      arc and fall, the last frames scattering crumbs. The clods' shape is the tier's: T1 soft crumbly lumps,
                      T2 denser lumps with a pebble in them, T3 angular stone chips, T4 sharp crystal shards with a glint,
                      T5 glassy shards with a lit edge. UNITY throws 4-8 per opened cell (D-183) and may mirror / rotate them.
  fx/rubble/base      3 frames x 64x64 @ PPU 64 (1 m = one cell), pivot [0.5, 0.5], tileable in x and y: loose clods heaped as
                      a fallen cell (D-184's rubble), three variants (json "variants": 3, no clip); tinted per tier as the clods.

  python -I build_dig_debris_v3.py <review png>   the lock-free sheet: the five clod sheets and the rubble tiles at 1x,
                                                  tinted on Earth T1 and T3 ground
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ui_v3 as U  # noqa: E402
import build_skilltree_v3 as ST  # noqa: E402
from meridian import v3  # noqa: E402

G, O, I = U.G, U.O, U.I
TAU = 2 * math.pi
ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
TIER_NAMES = {1: "Topsoil", 2: "Subsoil", 3: "Stone", 4: "Deep", 5: "Core"}
FW = 128
RW = 64


def keys():
    return [f"fx/dig_clods/t{t}" for t in range(1, 6)] + ["fx/rubble/base"]


def shape(t, cx, cy, r, rot, seed):
    """One clod's outline for tier t (px, y down), turned `rot`."""
    rnd = np.random.default_rng(seed)
    if t in (1, 2):
        return G.lumpy_ellipse(cx, cy, r, r * rnd.uniform(0.72, 0.9), n=14, lump=0.26 if t == 1 else 0.16, seed=seed, rot=rot)
    if t == 3:                                                                       # a chipped stone: 6 corners
        n = 6
        return [(cx + r * rnd.uniform(0.7, 1.1) * math.cos(rot + TAU * k / n + rnd.uniform(-0.25, 0.25)),
                 cy + r * rnd.uniform(0.6, 0.95) * math.sin(rot + TAU * k / n + rnd.uniform(-0.25, 0.25))) for k in range(n)]
    L, w = r * rnd.uniform(1.3, 1.7), r * rnd.uniform(0.45, 0.6)                     # T4 / T5: a shard, pointed both ends
    pts = [(L, 0.0), (L * 0.2, w), (-L * 0.7, w * 0.6), (-L, 0.0), (-L * 0.3, -w * 0.8)]
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


def details(d, M, t, cx, cy, r, rot, seed):
    if t == 2:                                                                       # a pebble in the lump
        G.stroke(d, G.lumpy_ellipse(cx + r * 0.25, cy + r * 0.2, r * 0.32, r * 0.26, n=10, lump=0.1, seed=seed + 5), M["offwhite_sh"], I * 0.8, cyclic=True)
    elif t == 3:                                                                     # a crack across the chip
        G.stroke(d, [(cx - r * 0.4 * math.cos(rot), cy - r * 0.4 * math.sin(rot)), (cx + r * 0.1, cy + r * 0.15),
                     (cx + r * 0.45 * math.cos(rot + 0.5), cy + r * 0.45 * math.sin(rot + 0.5))], M["ink"], I * 0.8)
    elif t == 4:                                                                     # a glint
        gx, gy = cx + r * 0.3 * math.cos(rot), cy + r * 0.3 * math.sin(rot) - r * 0.2
        for a in (0.0, math.pi / 2):
            G.stroke(d, G.hose_outline([(gx - 4 * math.cos(a), gy - 4 * math.sin(a)), (gx + 4 * math.cos(a), gy + 4 * math.sin(a))], 1.6), M["offwhite_f"], 0.0, cyclic=True)
    elif t == 5:                                                                     # the glassy lit edge
        c, s = math.cos(rot), math.sin(rot)
        L = r * 1.3
        G.stroke(d, G.hose_outline([(cx + (L * 0.7) * c, cy + (L * 0.7) * s - 1), (cx - (L * 0.5) * c, cy - (L * 0.5) * s - 2)], 2.0), M["offwhite_f"], 0.0, cyclic=True)


def clod_frame(t, k, seed=4100):
    c = U.Canvas(FW, FW)
    d, M = c.dm, ST.extra(c)
    rng = np.random.default_rng(seed + 10 * t)
    cx0, cy0 = 64, 70
    tt = k / 5.0
    clods = [(-2.2, 34, 9.5), (-1.25, 42, 8.0), (-0.55, 30, 7.0), (-2.75, 26, 6.0)]          # (launch angle rad, speed, radius)
    for j, (a, sp, r) in enumerate(clods):
        a += rng.uniform(-0.1, 0.1)
        x = cx0 + math.cos(a) * sp * tt * 1.3
        y = cy0 + math.sin(a) * sp * tt * 1.3 + 46 * tt * tt                                   # up and out, then gravity
        rr = r * (1.0 - 0.18 * tt)
        rot = rng.uniform(0, TAU) + (2.2 + j) * tt * (1 if j % 2 else -1)                       # tumbling
        if not (rr + 4 < x < FW - rr - 4 and rr + 4 < y < FW - rr - 4):
            continue
        pts = shape(t, x, y, rr, rot, seed + 100 * t + j)
        G.stroke(d, pts, M["offwhite"], O * 0.8, cyclic=True)
        sh = [(x + (px - x) * 0.55 + rr * 0.18, y + (py - y) * 0.55 + rr * 0.22) for px, py in pts]   # a shade lower-left
        G.stroke(d, sh, M["offwhite_sh"], 0.0, cyclic=True)
        details(d, M, t, x, y, rr, rot, seed + 100 * t + j)
    for j in range(8 if k >= 2 else 0):                                                    # crumbs after them
        a = rng.uniform(-3.0, -0.2)
        s = rng.uniform(14, 40)
        x, y = cx0 + math.cos(a) * s * tt, cy0 + math.sin(a) * s * tt + 30 * tt * tt
        rr = rng.uniform(1.4, 2.6)
        if rr + 4 < x < FW - rr - 4 and rr + 4 < y < FW - rr - 4:
            G.stroke(d, G.lumpy_ellipse(x, y, rr, rr * 0.85, n=8, lump=0.15, seed=seed + 300 + j), M["offwhite"], I * 0.8, cyclic=True)
    if k <= 1:                                                                             # the cell bursting open
        G.stroke(d, G.lumpy_ellipse(cx0, cy0 + 2, 15 - 4 * k, 6, n=16, lump=0.15, seed=seed + 7), M["offwhite"], I, cyclic=True)
    return ST.done(c, seed + k)[0]


def rubble_tile(v, seed=4700):
    """A loose heap of clods filling one cell, drawn periodically (each clod at the 9 wrap offsets) so it tiles."""
    c = U.Canvas(RW, RW)
    d, M = c.dm, ST.extra(c)
    rng = np.random.default_rng(seed + v)
    G.stroke(d, [(-2, -2), (RW + 2, -2), (RW + 2, RW + 2), (-2, RW + 2)], M["offwhite_sh"], 0.0, cyclic=True)   # the gaps between clods
    items = [(rng.uniform(0, RW), rng.uniform(0, RW), rng.uniform(7, 12), rng.uniform(0, TAU), rng.integers(1, 4)) for _ in range(11)]
    items.sort(key=lambda it: it[1])
    for (x, y, r, rot, t) in items:
        for ox in (-RW, 0, RW):
            for oy in (-RW, 0, RW):
                cx, cy = x + ox, y + oy
                if -r - 4 < cx < RW + r + 4 and -r - 4 < cy < RW + r + 4:
                    pts = shape(int(t), cx, cy, r, rot, seed + int(x * 7 + y))
                    G.stroke(d, pts, M["offwhite"], O * 0.7, cyclic=True)
                    G.stroke(d, [(cx + (px - cx) * 0.55 + r * 0.18, cy + (py - cy) * 0.55 + r * 0.22) for px, py in pts], M["offwhite_sh"], 0.0, cyclic=True)
    return ST.done(c, seed + v)[0]


def kit():
    import build_fx_rare_v3 as FR
    out = []
    for t in range(1, 6):
        frames = [clod_frame(t, k) for k in range(6)]
        sheet, cols = FR.sheet_of(frames)
        out.append((f"fx/dig_clods/t{t}", sheet, {"ppu": 64, "frame_width": FW, "frame_height": FW, "columns": cols, "gutter": v3.GUTTER,
                                                   "frames": 6, "fps": 12, "pivot": [0.5, 0.5], "tier": t, "tier_name": TIER_NAMES[t],
                                                   "animations": [{"name": "tumble", "start": 0, "length": 6, "loop": False}],
                                                   "note": "B-232 (D-183): four clods thrown out of the opened cell, tumbling; cream + ink: tint per "
                                                           "ground (as dig_puff); throw 4-8 per cell, mirror / rotate freely"}, frames))
    tiles = [rubble_tile(v) for v in range(3)]
    sheet, cols = FR.sheet_of(tiles)
    out.append(("fx/rubble/base", sheet, {"ppu": 64, "frame_width": RW, "frame_height": RW, "columns": cols, "gutter": v3.GUTTER, "frames": 3,
                                          "variants": 3, "pivot": [0.5, 0.5], "tile_x": True, "tile_y": True,
                                          "note": "B-232 (D-184): a fallen cell's loose clods, 3 variants (no clip), each tileable; cream + ink: "
                                                  "tint per tier as the clods"}, tiles))
    return out


def export(art):
    from meridian import pngio
    built, problems = [], []
    m = v3.EDGE_MARGIN
    for key, img, extra, frames in kit():
        meta = {"key": key, "style": "v3", "width": img.shape[1], "height": img.shape[0], "palette": "earth", **extra}
        if v3.palette_hits(img, "earth")[0] < 0.995:
            problems.append(f"{key}: palette")
        if not key.startswith("fx/rubble"):
            for i, f in enumerate(frames):
                if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any():
                    problems.append(f"{key} frame {i}: touches the {m} px edge")
        built.append((key, img, meta))
    if problems:
        raise ValueError("B-232 checks: " + "; ".join(problems))
    out = []
    for key, img, meta in built:
        base = os.path.join(art, *key.split("/"))
        os.makedirs(os.path.dirname(base), exist_ok=True)
        n = pngio.write_png(base + "_color.png", img)
        with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((key, img.shape[1], img.shape[0], n))
    return out


def preview(out, footnote=None):
    import time
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_rig_tools_v3 as RT
    K = kit()
    paper = np.array(review.PAPER, np.float32)
    W = 1600
    rows = []
    head = np.tile(paper, (28, W, 1)).astype(np.float32)
    review._label(head, "B-232 dig debris: the five tiers' clod sheets (frames 0-5) and the rubble tiles at 1x, tinted on Earth T1 and T3 ground", 6, 8)
    rows.append(head)
    for tier in (1, 3):                                                                    # tinted on two grounds
        fp = os.path.join(ART, "terrain", "earth", "ground_fill_color.png" if tier == 1 else f"ground_fill_t{tier}_color.png")
        fill = pngio.read_png_np(fp).astype(np.float32) / 255.0 if os.path.isfile(fp) else None
        tint = (fill[..., :3][fill[..., 3] > 0.9].mean(axis=0) if fill is not None else np.array([0.5, 0.4, 0.3], np.float32))
        tint = 0.45 + 0.55 * tint / max(float(tint.max()), 1e-3)
        r = np.tile(paper, (5 * 140 + 120, W, 1)).astype(np.float32)
        review._label(r, f"on Earth T{tier} ground (tinted by multiply)", 6, 4, scale=1)
        for i, (key, sheet, extra, frames) in enumerate(K[:5]):
            y = 24 + i * 140
            review._label(r, key, 6, y + 2, scale=1)
            for k, f in enumerate(frames):
                cell = np.tile(fill[:FW, :FW, :3], (1, 1, 1)) if fill is not None else np.full((FW, FW, 3), 0.5, np.float32)
                ff = f.astype(np.float32).copy()
                ff[..., :3] *= tint
                RT._ov(cell, ff.astype(np.uint8), 0, 0)
                r[y + 10:y + 10 + FW, 130 + k * 136:130 + k * 136 + FW] = cell
        y = 24 + 5 * 140
        review._label(r, "fx/rubble/base: 3 variants, each tiled 2x2", 6, y + 2, scale=1)
        for v, tile in enumerate(K[5][3]):
            big = np.tile(tile, (2, 2, 1)).astype(np.float32)
            big[..., :3] *= tint
            cell = np.tile(fill[:2 * RW, :2 * RW, :3], (1, 1, 1)) if fill is not None else np.full((2 * RW, 2 * RW, 3), 0.5, np.float32)
            RT._ov(cell, big.astype(np.uint8), 0, 0)
            r[y + 14:y + 14 + 2 * RW, 130 + v * 140:130 + v * 140 + 2 * RW] = cell
        rows.append(r)
    lines = [f"{key}: {img.shape[1]}x{img.shape[0]}, palette {v3.palette_hits(img, 'earth')[0] * 100:.1f}%" for key, img, _e, _f in K]
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-232 design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_dig_debris_v3.py <review png>
    preview(sys.argv[1])
