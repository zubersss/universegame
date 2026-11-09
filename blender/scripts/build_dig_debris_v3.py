"""B-232 (D-183 / D-184): dig debris in v3 ink, cream + ink so UNITY tints it to the dug cell's tier, as B-226's shovel flick.

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

  python -I build_dig_debris_v3.py <review png>   the lock-free sheet, shared with B-238 (LEAD 16:5x): each tier's four clips
                                                  over ITS OWN fill in its own tone; the dig stroke on Topsoil and on Stone -
                                                  B-238's new low dust (build_ground_v3.draw_puff) with the clods thrown over
                                                  it, at 1x and frames 2-4 at 4x, beside the old puff; the flick without its
                                                  clod (build_shovel_v3.flick_frame) at 1x and 2x; the rubble tiles 2x2.
                                                  Tints are UNITY's DigFeel.Tone: the tier's chip colour 35 % toward white
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
TIER_CHIP = {1: "#8C5A33", 2: "#B8843F", 3: "#7E7F86", 4: "#46516F", 5: "#9E3828"}   # D1Tables.json: each tier's chip colour
FW = 64                                                                              # one clod per frame (LEAD 14:2x)
RW = 64
COLS = 6                                                                             # a clip per row
CLODS = ((10.0, 1), (8.5, -1), (7.5, 1), (6.5, -1))                                  # clod_1..clod_4: (radius px, turn direction)
THROW = ((60, 3.2), (105, 2.6), (135, 3.4), (40, 2.4))                               # the sheet's mock throw: (deg up from +x, m/s)


def keys():
    return [f"fx/dig_clods/t{t}" for t in range(1, 6)] + ["fx/rubble/base"]


def tone_of(tier):
    """UNITY's DigFeel.Tone: the tier's chip colour lifted 35 % toward white - the multiply tint of the clods and the puff."""
    return np.array(v3.hex_rgb(TIER_CHIP[tier]), np.float32) / 255.0 * 0.65 + 0.35


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
                             "cell, a random clip each, and move them in code (U-195); cream + ink: tint by the dug cell's tier tone; "
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


def _bbox_m(fr):
    """A frame's drawn width and height in metres at PPU 64 (0, 0 when empty)."""
    a = fr[..., 3] > 8
    if not a.any():
        return 0.0, 0.0
    ys, xs = np.where(a.any(axis=1))[0], np.where(a.any(axis=0))[0]
    return (xs[-1] - xs[0] + 1) / 64.0, (ys[-1] - ys[0] + 1) / 64.0


def preview(out, footnote=None):
    import time
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_rig_tools_v3 as RT
    import build_ground_v3 as GV                                                           # B-238's puff
    import build_shovel_v3 as BS                                                           # B-238's flick
    K = kit()
    puff = [GV.render_piece("dig_puff", "earth", k)[0] for k in range(8)]
    flick = [BS.flick_frame(k) for k in range(6)]
    oldp = os.path.join(ART, "terrain", "earth", "dig_puff_color.png")                     # the puff as exported (B-184)
    old = None
    if os.path.isfile(oldp):
        osh = pngio.read_png_np(oldp)
        old = [osh[:, i * (128 + v3.GUTTER):i * (128 + v3.GUTTER) + 128] for i in range(8)]
    paper = np.array(review.PAPER, np.float32)
    sky = np.array(v3.hex_rgb(v3.PALETTES["earth"]["sky"]), np.float32) / 255.0
    W = 1760
    rows = []
    head = np.tile(paper, (28, W, 1)).astype(np.float32)
    review._label(head, "B-232 + B-238 at 1x: each tier's clod clips on its own fill in its own tone; the dig stroke (the new low dust under the clods) on Topsoil and Stone", 6, 8)
    rows.append(head)

    fills = {}

    def fill_of(tier):
        if tier not in fills:
            fp = os.path.join(ART, "terrain", "earth", "ground_fill_color.png" if tier == 1 else f"ground_fill_t{tier}_color.png")
            fills[tier] = pngio.read_png_np(fp).astype(np.float32)[..., :3] / 255.0 if os.path.isfile(fp) else None
        return fills[tier]

    def ground(tier, h, w):
        """An h x w patch of the tier's fill (tiled), or flat grey without it."""
        f = fill_of(tier)
        if f is None:
            return np.full((h, w, 3), 0.5, np.float32)
        return np.tile(f, (-(-h // f.shape[0]), -(-w // f.shape[1]), 1))[:h, :w].copy()

    def scene(tier, h, w, line):
        """The dug cell's mouth on row `line`: the tier's ground from it down; above it the sky (Topsoil) or, deeper, the
        room's back (the fill at 62 %)."""
        g = ground(tier, h, w)
        g[:line] = sky if tier == 1 else g[:line] * 0.62
        return g

    # ---- B-232: every tier's four clips, on that tier's fill, in that tier's tone
    CLIP_H = 84
    r = np.tile(paper, (24 + 5 * CLIP_H + 8, W, 1)).astype(np.float32)
    review._label(r, "fx/dig_clods/t1..t5: clips clod_1..4 (one clod turning in place, 6 frames), each tier on its own fill, tinted by its own tone (DigFeel.Tone)", 6, 4, scale=1)
    for i, (key, _sheet, _extra, frames) in enumerate(K[:5]):
        y = 24 + i * CLIP_H
        review._label(r, key, 6, y + 30, scale=1)
        for j in range(4):
            cell = ground(i + 1, FW, 6 * FW)
            for k in range(6):
                RT._ov(cell, frames[6 * j + k], k * FW, 0, tint=tone_of(i + 1))
            r[y + 10:y + 10 + FW, 150 + j * 400:150 + j * 400 + 6 * FW] = cell
    rows.append(r)

    # ---- B-238 + B-232: the stroke on Topsoil and on Stone
    CW_, CH_, CX, LINE = 208, 150, 104, 112                                                # a stroke cell; the mouth at (CX, LINE)
    for tier in (1, 3):
        tint = tone_of(tier)
        cl = K[tier - 1][3]
        r = np.tile(paper, (24 + CH_ + 26 + 256 + 26 + 128 + 12, W, 1)).astype(np.float32)
        review._label(r, f"the dig stroke on {TIER_NAMES[tier]} (tone {TIER_CHIP[tier]} lifted 35 %): B-238's dust, 8 frames, with four t{tier} clods thrown over it as U-195 does (2.4-3.4 m/s, gravity, gone at 0.6 s)", 6, 4, scale=1)
        cells = []
        for k in range(8):
            cell = scene(tier, CH_, CW_, LINE)
            RT._ov(cell, puff[k], CX - 64, LINE - 96, tint=tint)                           # the puff's pivot (0.5, 0.25)
            t = (k + 0.5) / 12.0
            if t <= 0.6:
                for j, (a, v) in enumerate(THROW):
                    x = v * math.cos(math.radians(a)) * t
                    z = v * math.sin(math.radians(a)) * t - 4.9 * t * t
                    if z > -0.05:
                        RT._ov(cell, cl[6 * j + k % 6], int(round(CX + x * 64)) - FW // 2, int(round(LINE - z * 64)) - FW // 2, tint=tint)
            cells.append(cell)
            r[24:24 + CH_, 10 + k * (CW_ + 4):10 + k * (CW_ + 4) + CW_] = cell
        y = 24 + CH_ + 6
        review._label(r, "frames 2, 3, 4 at 4x (the clods read first, the dust behind them)", 6, y, scale=1)
        for i, k in enumerate((2, 3, 4)):
            crop = cells[k][LINE - 52:LINE + 12, CX - 52:CX + 52]
            r[y + 18:y + 18 + 256, 10 + i * 424:10 + i * 424 + 416] = np.repeat(np.repeat(crop, 4, 0), 4, 1)
        y += 18 + 256 + 6
        review._label(r, "the old puff (B-184, as exported) in the same place and tone, 8 frames, for comparison" if old else "the old puff: not found", 6, y, scale=1)
        if old:
            for k in range(8):
                cell = scene(tier, 128, 128, 96)
                RT._ov(cell, old[k], 0, 0, tint=tint)
                r[y + 16:y + 16 + 128, 10 + k * 132:10 + k * 132 + 128] = cell
        rows.append(r)

    # ---- B-238: the flick without its clod
    r = np.tile(paper, (24 + 128 + 22 + 256 + 10, W, 1)).astype(np.float32)
    review._label(r, "fx/shovel_flick (B-238: no big clod, a short lift of crumbs): frames 0-5 at 1x on Topsoil, then at 2x", 6, 4, scale=1)
    for k in range(6):
        cell = scene(1, 128, 128, 96)
        RT._ov(cell, flick[k], 0, 0, tint=tone_of(1))
        r[24:24 + 128, 10 + k * 132:10 + k * 132 + 128] = cell
        r[24 + 128 + 22:24 + 128 + 22 + 256, 10 + k * 260:10 + k * 260 + 256] = np.repeat(np.repeat(cell, 2, 0), 2, 1)
    rows.append(r)

    # ---- B-232: the rubble tiles
    r = np.tile(paper, (24 + 2 * RW + 10, W, 1)).astype(np.float32)
    review._label(r, "fx/rubble/base: 3 variants, each tiled 2x2, on Topsoil (left three) and on Stone (right three), in the tier's tone", 6, 4, scale=1)
    for n, tier in enumerate((1, 3)):
        for v, tile in enumerate(K[5][3]):
            cell = ground(tier, 2 * RW, 2 * RW)
            RT._ov(cell, np.tile(tile, (2, 2, 1)), 0, 0, tint=tone_of(tier))
            x = 10 + (3 * n + v) * 140
            r[20:20 + 2 * RW, x:x + 2 * RW] = cell
    rows.append(r)

    m = v3.EDGE_MARGIN
    lines = [f"{key}: {img.shape[1]}x{img.shape[0]}, palette {v3.palette_hits(img, 'earth')[0] * 100:.1f}%" for key, img, _e, _f in K]
    sizes = [_bbox_m(f) for f in puff]
    edge = [k for k, f in enumerate(puff) if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any()]
    lines.append("dig_puff (B-238, earth): drawn w x h per frame (m) " + ", ".join(f"{w_:.2f}x{h_:.2f}" for w_, h_ in sizes)
                 + f"; tallest {max(h_ for _w, h_ in sizes):.2f} m (limit 0.35), widest cloud {max(w_ for w_, _h in sizes[:4]):.2f} m; "
                 + f"palette {min(v3.palette_hits(f, 'earth')[0] for f in puff) * 100:.1f}%; " + ("inside the 2 px edge" if not edge else f"TOUCHES THE EDGE in frames {edge}"))
    fs = [_bbox_m(f) for f in flick]
    lines.append("shovel_flick (B-238): drawn w x h per frame (m) " + ", ".join(f"{w_:.2f}x{h_:.2f}" for w_, h_ in fs)
                 + f"; empty frames: {[k for k, f in enumerate(flick) if not f[..., 3].any()] or 'none'}; palette {min(v3.palette_hits(f, 'earth')[0] for f in flick) * 100:.1f}%")
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-232 + B-238 design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_dig_debris_v3.py <review png>
    preview(sys.argv[1])
