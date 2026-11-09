"""B-212 (D-174; Bible 5.2 §8.1): rare finds, visible - tier-coloured ink sparkle bursts for drops and the "pocket found" pop.
v3 ink in UiKit's px Canvas (build_ui_v3), Earth palette, no glow (bright cores are cream paint, not light), no faces.

  fx/rare/sparkle_t<2..5>  8 frames 96x96, pivot [0.5, 0.5], clip 'burst' (once): a flash, then four-point stars and small
                           diamonds fly out and shrink away. The tier's own colours: T2 rust (the Subsoil), T3 teal crystal
                           (the Stone's veins), T4 gold (the Deep's seams), T5 diamond cream with ember red (the Core)
  fx/rare/pocket_pop       8 frames 128x128, pivot [0.5, 0.5], clip 'pop' (once): a jagged paper burst swells with ink burst
                           lines, holds, then tears into three paper scraps that fly off

  python -I build_fx_rare_v3.py <review png>     the lock-free sheet: each burst at 1x / 2x, and over its tier's fill with a drop
"""
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
circ, extra, done = ST.circ, ST.extra, ST.done
ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art")
TIER_TONES = {2: ("red", "mustard"), 3: ("teal", "offwhite"), 4: ("mustard", "offwhite"), 5: ("offwhite", "red")}   # (spark, core;
                                                                                              # an inked fill: the _sh roles are fill-only)
SPARK = 96
POP = 128


def star4(cx, cy, r, ri=None, rot=0.0):
    ri = ri or r * 0.32
    return [(cx + (r if k % 2 == 0 else ri) * math.cos(rot + TAU * k / 8), cy + (r if k % 2 == 0 else ri) * math.sin(rot + TAU * k / 8)) for k in range(8)]


def diamond(cx, cy, r):
    return [(cx, cy - r), (cx + r * 0.6, cy), (cx, cy + r), (cx - r * 0.6, cy)]


def sparkle(tier, k, seed=500):
    """Frame k of the tier's burst."""
    c = U.Canvas(SPARK, SPARK)
    d, M = c.dm, extra(c)
    cx = cy = SPARK / 2
    tone, core = TIER_TONES[tier]
    rng = np.random.default_rng(seed + tier)
    angs = [TAU * j / 6 + rng.uniform(-0.25, 0.25) for j in range(6)]
    if k <= 1:                                                                                # the flash at the drop
        r = 12 if k == 0 else 18
        G.stroke(d, star4(cx, cy, r, rot=0.0), M[tone], I, cyclic=True)
        G.stroke(d, star4(cx, cy, r * 0.5, rot=0.0), M[core + "_f"] if core + "_f" in M else M[core], 0.0, cyclic=True)
    t = max(0.0, (k - 1) / 6.0)
    if k >= 1:
        for j, a in enumerate(angs):                                                          # the stars fly out and shrink
            rr = 10 + 30 * math.sqrt(t)
            sz = 9 * (1 - t) ** 0.8 + (1 if k < 7 else 0)
            if sz < 1.5:
                continue
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            if j % 2 == 0:
                G.stroke(d, star4(x, y, sz, rot=0.2 * j), M[tone], I * 0.9, cyclic=True)
                G.stroke(d, star4(x, y, sz * 0.45, rot=0.2 * j), M[core + "_f"], 0.0, cyclic=True)
            else:
                G.stroke(d, diamond(x, y, sz * 0.75), M[tone], I * 0.8, cyclic=True)
    if tier == 5 and 2 <= k <= 5:                                                             # the Core's ember flecks
        for j in range(4):
            a = TAU * j / 4 + 0.4
            rr = 16 + 22 * t
            G.stroke(d, circ(cx + rr * math.cos(a), cy + rr * math.sin(a), 2.2 * (1 - t) + 0.8, 8), M["red_f"], 0.0, cyclic=True)
    return done(c, seed + 10 * tier + k)[0]


def jag(cx, cy, r, n=12, depth=0.32, rot=0.0):
    return [(cx + r * (1 - depth * (k % 2)) * math.cos(rot + TAU * k / (2 * n)), cy + r * (1 - depth * (k % 2)) * math.sin(rot + TAU * k / (2 * n)))
            for k in range(2 * n)]


def pocket_pop(k, seed=600):
    c = U.Canvas(POP, POP)
    d, M = c.dm, extra(c)
    cx = cy = POP / 2
    scale = [0.35, 0.75, 1.05, 1.0, 1.0, 0.0, 0.0, 0.0][k]
    if 1 <= k <= 4:                                                                           # ink burst lines round it
        for j in range(10):
            a = TAU * j / 10 + 0.15
            r0, r1 = 44 + 3 * k, 54 + 4 * k
            if r1 < 60:
                G.stroke(d, G.hose_outline([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))], 2.2),
                         M["ink_f"], 0.0, cyclic=True)
    if scale > 0:                                                                             # the paper burst
        R = 40 * scale
        G.stroke(d, jag(cx, cy, R, rot=0.1), M["mustard"], O, cyclic=True)
        G.stroke(d, jag(cx, cy, R * 0.72, rot=0.1), M["offwhite"], I, cyclic=True)
        G.stroke(d, star4(cx, cy, R * 0.42, rot=0.0), M["red"], I, cyclic=True)               # a star at its heart (no lettering)
    else:                                                                                     # torn: three scraps fly off
        t = (k - 4) / 3.0
        for j, a in enumerate((-0.6, 1.5, 3.4)):
            x, y = cx + 34 * t * math.cos(a), cy + 34 * t * math.sin(a) + 8 * t * t
            s = 14 * (1 - 0.5 * t)
            pts = [(x + s * math.cos(a + 0.4 + TAU * i / 5) * (1 if i % 2 else 0.6), y + s * math.sin(a + 0.4 + TAU * i / 5) * (1 if i % 2 else 0.6)) for i in range(5)]
            G.stroke(d, pts, M["mustard" if j != 1 else "offwhite"], I, cyclic=True)
    return done(c, seed + k)[0]


def sheet_of(frames):
    fw, fh = frames[0].shape[1], frames[0].shape[0]
    cols = v3.columns_for(fw, len(frames))
    rows = -(-len(frames) // cols)
    g = v3.GUTTER
    sheet = np.zeros((rows * fh + (rows - 1) * g, cols * fw + (cols - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw] = im
    return sheet, cols


def kit():
    out = []
    for t in (2, 3, 4, 5):
        fr = [sparkle(t, k) for k in range(8)]
        sheet, cols = sheet_of(fr)
        out.append((f"fx/rare/sparkle_t{t}", fr, sheet, {"frame_width": SPARK, "frame_height": SPARK, "columns": cols, "frames": 8, "tier": t,
                                                          "animations": [{"name": "burst", "start": 0, "length": 8, "loop": False}],
                                                          "note": f"B-212: a drop's sparkle burst in tier {t}'s colours (no glow); played once where the drop lands"}))
    fr = [pocket_pop(k) for k in range(8)]
    sheet, cols = sheet_of(fr)
    out.append(("fx/rare/pocket_pop", fr, sheet, {"frame_width": POP, "frame_height": POP, "columns": cols, "frames": 8,
                                                 "animations": [{"name": "pop", "start": 0, "length": 8, "loop": False}],
                                                 "note": "B-212: the 'pocket found' pop: a paper burst swells, holds, tears into scraps; played once at the pocket"}))
    return out


def export(art):
    import json
    from meridian import pngio
    built, problems = [], []
    for key, frames, sheet, extra_meta in kit():
        meta = {"key": key, "style": "v3", "ppu": U.PPU, "gutter": v3.GUTTER, "fps": v3.FPS, "pivot": [0.5, 0.5], "facing": "right", **extra_meta}
        hit = v3.palette_hits(sheet, "earth")[0]
        m = v3.EDGE_MARGIN
        if hit < 0.995:
            problems.append(f"{key}: palette {hit * 100:.1f}%")
        for i, f in enumerate(frames):
            if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any():
                problems.append(f"{key} frame {i}: touches the {m} px edge")
        built.append((key, sheet, meta))
    if problems:
        raise ValueError("B-212 fx checks: " + "; ".join(problems))
    out = []
    for key, sheet, meta in built:
        base = os.path.join(art, *key.split("/"))
        os.makedirs(os.path.dirname(base), exist_ok=True)
        n = pngio.write_png(base + "_color.png", sheet)
        with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((key, sheet.shape[1], sheet.shape[0], n))
    return out


def keys():
    return [f"fx/rare/sparkle_t{t}" for t in (2, 3, 4, 5)] + ["fx/rare/pocket_pop"]


def preview(out, footnote=None):
    import time
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    K = kit()
    W = 1700
    rows = []
    head = np.tile(np.array(review.PAPER, np.float32), (26, W, 1))
    review._label(head, "B-212 rare finds: the tier sparkle bursts (8 frames each) over their tier's fill with a drop, and the pocket-found pop", 6, 6)
    rows.append(head)
    fills = {t: pngio.read_png_np(os.path.join(ART, "terrain", "earth", f"ground_fill_t{t}_color.png")) for t in (2, 3, 4, 5)}
    drops = {2: "copper", 3: "silica", 4: "graphite", 5: "deep_diamond"}
    for (key, frames, _sheet, meta) in K:
        fw = frames[0].shape[1]
        r = np.empty((fw * 2 + 40, W, 3), np.float32)
        t = meta.get("tier")
        if t:
            r[:] = np.tile(fills[t], (2, 4, 1))[:r.shape[0], :W, :3].astype(np.float32) / 255.0
        else:
            r[:] = np.array(review.PAPER, np.float32)
        review._label(r, key + ((f" over tier {t}'s fill, a {drops[t]} drop at its heart") if t else " (1x, then frames 1-3 at 2x)"), 6, 4, scale=1)
        icon = None
        if t:
            p = os.path.join(ART, "icons", drops[t], "base_color.png")
            if os.path.isfile(p):
                ic = pngio.read_png_np(p)
                f_ = ic.shape[0] // 32
                icon = np.rint(ic.astype(np.float32).reshape(32, f_, 32, f_, 4).mean(axis=(1, 3))).astype(np.uint8)
        for k, fr in enumerate(frames):
            x = 10 + k * (fw + 14)
            if icon is not None:
                ST.ov(r, icon, x + fw // 2 - 16, 24 + fw // 2 - 16)
            ST.ov(r, fr, x, 24)
        x = 10 + 8 * (fw + 14) + 20
        for k in (1, 2, 3):
            f2 = np.repeat(np.repeat(frames[k], 2, 0), 2, 1)
            if x + f2.shape[1] > W:
                break
            if icon is not None:
                ST.ov(r, np.repeat(np.repeat(icon, 2, 0), 2, 1), x + fw - 32, 24 + fw - 32)
            ST.ov(r, f2, x, 24)
            x += f2.shape[1] + 10
        rows.append(r)
    lines = []
    for key, frames, sheet, _m in K:
        hit = v3.palette_hits(sheet, "earth")[0] * 100
        m = v3.EDGE_MARGIN
        bad = [i for i, f in enumerate(frames) if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any()]
        lines.append(f"{key}: {sheet.shape[1]}x{sheet.shape[0]}, palette {hit:.1f}%" + (f"; EDGE {bad}" if bad else ""))
    foot = np.tile(np.array(review.PAPER, np.float32), (24 + 16 * ((len(lines) + 2) // 3), W, 1))
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6 + (i % 3) * 560, 6 + 16 * (i // 3), scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_fx_rare_v3.py <review png>
    preview(sys.argv[1])
