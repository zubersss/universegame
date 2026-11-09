"""B-232 (D-183 / D-184): dig debris in v3 ink, cream + ink so UNITY tints it to the ground, as B-226's shovel flick.

  fx/dig_clods/t<n>   n = 1..5 (Topsoil, Subsoil, Stone, Deep, Core). LEAD's ruling 14:2x (it replaces the card's 128 px burst
                      frames): 24 frames x 64x64 @ PPU 64 (1 m) in 4 rows of 6 (404x268 with the contract's 4 px gutters),
                      pivot [0.5, 0.5], four looping clips clod_1..clod_4 of 6 frames (12 fps), each ONE clod turning a full
                      turn IN PLACE at the frame's centre: no travel, no baked arc, no crumbs. UNITY spawns 4-8 per opened cell,
                      a random clip each, and does the arc in code (U-195). The clods' shape is the tier's: T1 soft crumbly
                      lumps, T2 denser lumps with a pale pebble in them, T3 angular stone chips with a crack, T4 sharp crystal
                      shards with a facet ridge and a glint, T5 dark glassy shards with a lit edge. Sized as shovel_flick's
                      clod (radius 6.5-10 px); the light stays upper-left while the clod turns.
  fx/rubble/base      3 frames x 64x64 @ PPU 64 (1 m = one cell), pivot [0.5, 0.5], tileable in x and y: loose clods heaped as
                      a fallen cell (D-184's rubble), three variants (json "variants": 3, no clip); tinted per tier as the clods.

  python -I build_dig_debris_v3.py <review png>   the lock-free sheet, on Earth T1 and T3 ground (tinted by multiply): each
                                                  tier's four clips as rows, a mock burst per tier (the clips placed on arcs,
                                                  as U-195's code would throw them), the rubble tiles 2x2
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
FW = 64                                                                              # one clod per frame (LEAD 14:2x)
RW = 64
COLS = 6                                                                             # a clip per row
CLODS = ((10.0, 1), (8.5, -1), (7.5, 1), (6.5, -1))                                  # clod_1..clod_4: (radius px, turn direction)
MOCK = ((-2.2, 34), (-1.25, 42), (-0.55, 30), (-2.75, 26))                           # the sheet's mock burst: (launch rad, speed)


def keys():
    return [f"fx/dig_clods/t{t}" for t in range(1, 6)] + ["fx/rubble/base"]


def _turn(cx, cy, rot, pts):
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts]


def shape(t, cx, cy, r, rot, seed):
    """One clod's outline for tier t (px, y down): built about its centre, then turned rigidly by `rot` (so a clip's frames
    are one shape turning, never a shape that morphs)."""
    rnd = np.random.default_rng(seed)
    if t in (1, 2):
        pts = G.lumpy_ellipse(0.0, 0.0, r, r * rnd.uniform(0.72, 0.9), n=14, lump=0.26 if t == 1 else 0.16, seed=seed)
    elif t == 3:                                                                     # a chipped stone: 6 corners
        pts = []
        for k in range(6):
            a = TAU * k / 6 + rnd.uniform(-0.25, 0.25)
            pts.append((r * rnd.uniform(0.7, 1.1) * math.cos(a), r * rnd.uniform(0.6, 0.95) * math.sin(a)))
    else:                                                                            # T4 / T5: a shard, pointed both ends
        L, w = r * rnd.uniform(1.3, 1.7), r * rnd.uniform(0.45, 0.6)
        pts = [(L, 0.0), (L * 0.2, w), (-L * 0.7, w * 0.6), (-L, 0.0), (-L * 0.3, -w * 0.8)]
    return _turn(cx, cy, rot, pts)


def details(d, M, t, cx, cy, r, rot, seed):
    """The tier's interior mark, turning with the clod."""
    if t == 2:                                                                       # a pebble in the lump: pale + inked (in the
        px, py = _turn(cx, cy, rot, [(r * 0.25, r * 0.2)])[0]                        # shade tone it sat unseen on the clod's shade)
        G.stroke(d, G.lumpy_ellipse(px, py, r * 0.32, r * 0.26, n=10, lump=0.1, seed=seed + 5, rot=rot), M["offwhite"], I * 0.8, cyclic=True)
    elif t == 3:                                                                     # a crack across the chip
        G.stroke(d, _turn(cx, cy, rot, [(-r * 0.4, 0.0), (r * 0.1, r * 0.15), (r * 0.4, r * 0.2)]), M["ink"], I * 0.8)
    elif t == 4:                                                                     # the crystal's facet ridge (its glint goes
        G.stroke(d, _turn(cx, cy, rot, [(-r * 0.75, 0.0), (r * 1.0, 0.0)]), M["ink"], I * 0.7)   # over the ink, in clod())
    elif t == 5:                                                                     # the glassy lit edge (on the dark body)
        c, s = math.cos(rot), math.sin(rot)
        L = r * 1.3
        G.stroke(d, G.hose_outline([(cx + (L * 0.7) * c, cy + (L * 0.7) * s - 1), (cx - (L * 0.5) * c, cy - (L * 0.5) * s - 2)], 2.0), M["offwhite_f"], 0.0, cyclic=True)


def clod(d, M, t, x, y, r, rot, seed, ink):
    """One clod of tier t (px, y down): the body, its shade lower-right, the tier's detail, the ink; T5 is dark glass (the shade
    tone as its body, so the lit edge shows), T4 carries one glint over its ink (cream on a cream body drew nothing)."""
    pts = shape(t, x, y, r, rot, seed)
    body, shade = ("offwhite_sh", "offwhite_dp") if t == 5 else ("offwhite_f", "offwhite_sh")
    G.stroke(d, pts, M[body], 0.0, cyclic=True)
    G.stroke(d, [(x + (px - x) * 0.55 + r * 0.18, y + (py - y) * 0.55 + r * 0.22) for px, py in pts], M[shade], 0.0, cyclic=True)
    details(d, M, t, x, y, r, rot, seed)
    G.stroke(d, pts, M["ink"], ink, cyclic=True)
    if t == 4:
        gx, gy = x + r * 1.1 * math.cos(rot), y + r * 1.1 * math.sin(rot)
        for a in (0.0, math.pi / 2):
            G.stroke(d, G.hose_outline([(gx - 4 * math.cos(a), gy - 4 * math.sin(a)), (gx + 4 * math.cos(a), gy + 4 * math.sin(a))], 1.6), M["offwhite_f"], 0.0, cyclic=True)


def clod_frame(t, j, k, seed=4100):
    """Frame k (0..5) of clip clod_<j + 1> for tier t: one clod at the frame's centre, k/6 of a full turn on (in place)."""
    c = U.Canvas(FW, FW)
    d, M = c.dm, ST.extra(c)
    r, turn = CLODS[j]
    rot0 = float(np.random.default_rng(seed + 10 * t + j).uniform(0, TAU))
    clod(d, M, t, FW / 2, FW / 2, r, rot0 + turn * TAU * k / 6, seed + 100 * t + j, O * 0.8)
    return ST.done(c, seed + 7 * j + k)[0]


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
                    clod(d, M, int(t), cx, cy, r, rot, seed + int(x * 7 + y), O * 0.7)
    return ST.done(c, seed + v)[0]


def grid(frames, cols):
    """Row-major sheet with the contract's gutters (FR.sheet_of would lay 24 frames in one row)."""
    fh, fw = frames[0].shape[:2]
    rows = -(-len(frames) // cols)
    g = v3.GUTTER
    sheet = np.zeros((rows * fh + (rows - 1) * g, cols * fw + (cols - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw] = im
    return sheet


def kit():
    import build_fx_rare_v3 as FR
    out = []
    for t in range(1, 6):
        frames = [clod_frame(t, j, k) for j in range(4) for k in range(6)]
        out.append((f"fx/dig_clods/t{t}", grid(frames, COLS),
                    {"ppu": 64, "frame_width": FW, "frame_height": FW, "columns": COLS, "gutter": v3.GUTTER, "frames": 24, "fps": 12,
                     "pivot": [0.5, 0.5], "tier": t, "tier_name": TIER_NAMES[t],
                     "animations": [{"name": f"clod_{j + 1}", "start": 6 * j, "length": 6, "loop": True, "loop_from": 0} for j in range(4)],
                     "note": "B-232 (D-183, LEAD 14:2x): four clips, each ONE clod turning in place (no travel): spawn 4-8 per opened "
                             "cell, a random clip each, and move them in code (U-195); cream + ink: tint per ground (as dig_puff); "
                             "mirror freely"}, frames))
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
        if img.shape[1] % 4 or img.shape[0] % 4:
            problems.append(f"{key}: {img.shape[1]}x{img.shape[0]} not a multiple of 4")
        if not key.startswith("fx/rubble"):
            for i, f in enumerate(frames):
                if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any():
                    problems.append(f"{key} frame {i}: touches the {m} px edge")
                if not f[..., 3].any():
                    problems.append(f"{key} frame {i}: empty")
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
    W = 1760
    CLIP_H, BURST = 84, 128
    rows = []
    head = np.tile(paper, (28, W, 1)).astype(np.float32)
    review._label(head, "B-232 dig debris at 1x on Earth T1 and T3 ground: each tier's clips clod_1..4 (one clod turning in place), a mock burst, the rubble tiles", 6, 8)
    rows.append(head)
    for tier in (1, 3):                                                                    # tinted on two grounds
        fp = os.path.join(ART, "terrain", "earth", "ground_fill_color.png" if tier == 1 else f"ground_fill_t{tier}_color.png")
        fill = pngio.read_png_np(fp).astype(np.float32) / 255.0 if os.path.isfile(fp) else None
        tint = (fill[..., :3][fill[..., 3] > 0.9].mean(axis=0) if fill is not None else np.array([0.5, 0.4, 0.3], np.float32))
        tint = 0.45 + 0.55 * tint / max(float(tint.max()), 1e-3)

        def ground(h, w):
            """An h x w patch of the tier's fill (tiled), or flat grey without it."""
            if fill is None:
                return np.full((h, w, 3), 0.5, np.float32)
            return np.tile(fill[..., :3], (-(-h // fill.shape[0]), -(-w // fill.shape[1]), 1))[:h, :w].copy()

        def tinted(f):
            ff = f.astype(np.float32).copy()
            ff[..., :3] *= tint
            return ff.astype(np.uint8)
        y0 = 24 + 5 * CLIP_H + 20
        r = np.tile(paper, (y0 + 5 * 140 + 170, W, 1)).astype(np.float32)
        review._label(r, f"on Earth T{tier} ground (tinted by multiply): each tier's four clips, 6 frames each", 6, 4, scale=1)
        for i, (key, _sheet, _extra, frames) in enumerate(K[:5]):
            y = 24 + i * CLIP_H
            review._label(r, key, 6, y + 30, scale=1)
            for j in range(4):
                cell = ground(FW, 6 * FW)
                for k in range(6):
                    RT._ov(cell, tinted(frames[6 * j + k]), k * FW, 0)
                r[y + 10:y + 10 + FW, 150 + j * 400:150 + j * 400 + 6 * FW] = cell
        review._label(r, "a mock burst per tier: the four clips placed on arcs over 6 steps, as U-195's code would throw them (128 px = 2 m cells)", 6, y0 - 12, scale=1)
        for i, (key, _sheet, _extra, frames) in enumerate(K[:5]):
            y = y0 + i * 140
            review._label(r, key.split("/")[-1], 6, y + 60, scale=1)
            for k in range(6):
                tt = k / 5.0
                cell = ground(BURST, BURST)
                for j, (a, sp) in enumerate(MOCK):
                    x = 64 + math.cos(a) * sp * tt * 2.0
                    yy = 70 + math.sin(a) * sp * tt * 2.0 + 70 * tt * tt                   # up and out, then gravity
                    RT._ov(cell, tinted(frames[6 * j + k]), int(round(x)) - FW // 2, int(round(yy)) - FW // 2)
                r[y + 4:y + 4 + BURST, 150 + k * 136:150 + k * 136 + BURST] = cell
        y = y0 + 5 * 140
        review._label(r, "fx/rubble/base: 3 variants, each tiled 2x2", 6, y + 2, scale=1)
        for v, tile in enumerate(K[5][3]):
            big = np.tile(tile, (2, 2, 1)).astype(np.float32)
            big[..., :3] *= tint
            cell = ground(2 * RW, 2 * RW)
            RT._ov(cell, big.astype(np.uint8), 0, 0)
            r[y + 16:y + 16 + 2 * RW, 150 + v * 140:150 + v * 140 + 2 * RW] = cell
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
