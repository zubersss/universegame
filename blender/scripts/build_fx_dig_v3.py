"""B-216 (D1): the dig loop's FX in v3 ink, replacing B-012's v2 renders under the SAME keys and clips (no code change):

  fx/dig_sparks/base   6 frames 128x128 @ ppu 128 (SideFx plays it at scale 2: 2 m), pivot centre = the cut, clip 'burst'
                       (once, 15 fps): an ink impact star, then brown dirt chips tumbling out and falling, hot red / gold
                       flecks streaking off and shrinking away. No glow: the v2 emission map goes (UNITY drops its .meta)
  fx/dust/base         6 frames 128x128 @ ppu 128, pivot [0.5, 0.0625] = the feet on the ground, clip 'puff' (once, 12 fps):
                       a low cartoon landing puff - two cream clouds rolling out along the ground from the feet, breaking into
                       small balls. Cream paper with an ink outline so UNITY's ground tint multiplies through it

  python -I build_fx_dig_v3.py <review png>     the lock-free sheet (each at its in-game size over a dug ground / the turf)
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
import build_fx_rare_v3 as FR  # noqa: E402
from meridian import v3  # noqa: E402

G, O, I = U.G, U.O, U.I
TAU = 2 * math.pi
circ, extra, done = ST.circ, ST.extra, ST.done
ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art")
F = 128
GROUND_Y = F - 8                                           # dust's pivot row (0.0625 up from the bottom)


# ---------------------------------------------------------------- dig_sparks
def chip(cx, cy, r, rot, seed):
    rng = np.random.default_rng(seed)
    n = 5
    return [(cx + r * (0.7 + 0.3 * rng.random()) * math.cos(rot + TAU * k / n), cy + r * (0.7 + 0.3 * rng.random()) * math.sin(rot + TAU * k / n)) for k in range(n)]


def sparks_frame(k, seed=1200):
    c = U.Canvas(F, F)
    d, M = c.dm, extra(c)
    cx = cy = F / 2
    rng = np.random.default_rng(seed)
    if k <= 1:                                                                               # the impact star at the cut, ink burst
        r = (17, 11)[k]                                                                      # lines round it (rev: 13 px read small)
        for j in range(6):
            a = TAU * j / 6 + 0.3
            r0, r1 = r + 3 + 4 * k, r + 9 + 6 * k
            G.stroke(d, G.hose_outline([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))], 1.8),
                     M["ink_f"], 0.0, cyclic=True)
        G.stroke(d, FR.star4(cx, cy, r, rot=0.0), M["mustard"], I, cyclic=True)
        G.stroke(d, FR.star4(cx, cy, r * 0.45, rot=0.0), M["offwhite_f"], 0.0, cyclic=True)
    t = k + 0.6
    for j in range(8):                                                                       # chips: out, up, then falling - ink chips
        a = math.radians(rng.uniform(-165, -15) if j < 6 else rng.uniform(10, 50) * (1 if j == 6 else -1) + (0 if j == 6 else 180))
        s = rng.uniform(9.5, 13.5)                                                           # (LEAD) with a few pale stone chips that
        x, y = cx + s * t * math.cos(a), cy + s * t * math.sin(a) + 1.7 * t * t              # read on the dark tiers
        r = rng.uniform(4.2, 6.4) * (1.0 if k < 4 else 0.8)
        if not (r + 4 < x < F - r - 4 and r + 4 < y < F - r - 4):
            continue
        pts = chip(x, y, r, 0.9 * t + j, seed + j)
        if j % 3 == 2:
            G.stroke(d, pts, M["offwhite_sh"], 0.0, cyclic=True)
            G.stroke(d, pts, M["ink"], I, cyclic=True)
        else:
            G.stroke(d, pts, M["ink_f"], 0.0, cyclic=True)
    for j in range(8):                                                                       # hot flecks: fast, shrinking away
        if k >= 5:
            break
        a = math.radians(rng.uniform(-175, -5))
        s = rng.uniform(15, 19)
        x, y = cx + s * t * math.cos(a), cy + s * t * math.sin(a) + 0.8 * t * t
        L = 8.0 * (1 - k / 5.0) + 2.0
        w = 2.4 * (1 - k / 6.0) + 0.6
        if not (L + 4 < x < F - L - 4 and L + 4 < y < F - L - 4):
            continue
        ux, uy = math.cos(a), math.sin(a)
        pts = [(x + ux * L / 2, y + uy * L / 2), (x - uy * w, y + ux * w), (x - ux * L / 2, y - uy * L / 2), (x + uy * w, y - ux * w)]
        G.stroke(d, pts, M["red" if j % 2 == 0 else "mustard"], I * 0.6, cyclic=True)
    return done(c, seed + k)[0]


# ---------------------------------------------------------------- dust (the landing puff)
def cloud(d, M, cx, r, rise, side, seed):
    """Three overlapping balls on the ground, rolling outward (side -1 / +1); one outline round the union."""
    gy = GROUND_Y - rise
    balls = [(cx, gy - r * 0.85, r), (cx + side * r * 0.85, gy - r * 0.55, r * 0.68), (cx - side * r * 0.75, gy - r * 0.45, r * 0.55)]
    for x, y, rr in balls:
        G.stroke(d, circ(x, y, rr, 24), M["offwhite"], O * 0.8, cyclic=True)                   # fills + ink outlines
    for x, y, rr in balls:
        G.stroke(d, circ(x, y, rr - 1.3, 24), M["offwhite_f"], 0.0, cyclic=True)              # cover the inner lines: the union's
    G.stroke(d, [(cx - side * r * 0.2, gy - r * 1.1), (cx + side * r * 0.25, gy - r * 1.3)], M["ln_offwhite"], I)   # outline stays


def dust_frame(k, seed=1300):
    c = U.Canvas(F, F)
    d, M = c.dm, extra(c)
    cx = F / 2
    R = (7.0, 11.0, 13.0, 12.0, 9.0, 6.0)[k]
    off = 8 + 9 * k
    rise = (0, 1, 3, 5, 7, 9)[k]
    if k <= 1:                                                                               # the first puff at the feet
        G.stroke(d, circ(cx, GROUND_Y - 5 - 2 * k, 6 + 2 * k, 20, 4 + k), M["offwhite"], O * 0.8, cyclic=True)
    for side in (-1, 1):
        x = cx + side * off
        if k <= 3:
            cloud(d, M, x, R, rise, side, seed + side)
        else:                                                                                # breaking up into small balls
            for j, (dx, dy, rr) in enumerate(((0, 0, R), (-side * R * 1.4, R * 0.6, R * 0.6))):        # (the small one trails inward)
                G.stroke(d, circ(x + dx, GROUND_Y - rise - R * 0.8 + dy, rr, 18), M["offwhite"], O * 0.8, cyclic=True)
    return done(c, seed + k)[0]


# ---------------------------------------------------------------- kit / export
FX = {   # key: (frame fn, n, pivot, clip, fps, note)
    "fx/dig_sparks/base": (sparks_frame, 6, [0.5, 0.5], "burst", 15,
                           "B-216: the Beam's cut - an ink impact star, dirt chips tumbling out, hot flecks streaking off (no glow; v3 replaces B-012)"),
    "fx/dust/base": (dust_frame, 6, [0.5, 0.0625], "puff", 12,
                     "B-216: the landing puff - two cream clouds rolling out along the ground (cream + ink: UNITY's ground tint multiplies through; v3 replaces B-012)"),
}
V2_REMOVE = ["fx/dig_sparks/base_emission.png"]                                           # the v2 glow map (UNITY drops the .meta)


def kit():
    out = []
    for key, (fn, n, piv, clip, fps, note) in FX.items():
        frames = [fn(k) for k in range(n)]
        sheet, cols = FR.sheet_of(frames)
        meta = {"key": key, "style": "v3", "ppu": 128, "gutter": v3.GUTTER, "fps": fps, "pivot": piv, "frame_width": F, "frame_height": F,
                "columns": cols, "frames": n, "facing": "right", "animations": [{"name": clip, "start": 0, "length": n, "loop": False}], "note": note}
        out.append((key, frames, sheet, meta))
    return out


def checks(key, frames, sheet):
    p = []
    m = v3.EDGE_MARGIN
    hit = v3.palette_hits(sheet, "earth")[0]
    if hit < 0.995:
        p.append(f"{key}: palette {hit * 100:.1f}%")
    if sheet.shape[1] % 4 or sheet.shape[0] % 4:
        p.append(f"{key}: sheet {sheet.shape[1]}x{sheet.shape[0]} not a multiple of 4")
    for i, f in enumerate(frames):
        if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any():
            p.append(f"{key} frame {i}: touches the {m} px edge")
    return p


def export(art):
    from meridian import pngio
    built, problems = [], []
    for key, frames, sheet, meta in kit():
        problems += checks(key, frames, sheet)
        built.append((key, sheet, meta))
    if problems:
        raise ValueError("B-216 fx checks: " + "; ".join(problems))
    out = []
    for key, sheet, meta in built:
        base = os.path.join(art, *key.split("/"))
        n = pngio.write_png(base + "_color.png", sheet)
        with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((key, sheet.shape[1], sheet.shape[0], n))
    for rel in V2_REMOVE:
        p = os.path.join(art, *rel.split("/"))
        if os.path.isfile(p):
            os.remove(p)
    return out


def keys():
    return list(FX)


# ---------------------------------------------------------------- the review sheet
def preview(out, footnote=None):
    import time
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    K = kit()
    Wd = 1500
    paper = np.array(review.PAPER, np.float32)
    pal = {k: np.array(v3.hex_rgb(v), np.float32) / 255.0 for k, v in v3.PALETTES["earth"].items()}
    rows = []
    head = np.tile(paper, (28, Wd, 1))
    review._label(head, "B-216 the dig FX in ink, at their in-game size (scale 2 at ppu 128 = 64 px/m): sparks at a cut in Earth's Stone tier; dust under the feet on turf, then tinted", 6, 8)
    rows.append(head)
    fill = pngio.read_png_np(os.path.join(ART, "terrain", "earth", "ground_fill_t3_color.png"))
    surv = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))[:192, :192]
    for key, frames, sheet, meta in K:
        name = key.split("/")[1]
        r = np.empty((F * 2 + 60, Wd, 3), np.float32)
        r[:] = paper
        review._label(r, f"{key} (1x, frames 0-{len(frames) - 1}; then frames at 2x)", 6, 4, scale=1)
        for i, fr in enumerate(frames):
            x = 10 + i * (F + 8)
            cell = np.empty((F, F, 3), np.float32)
            if name == "dig_sparks":
                cell[:] = np.tile(fill, (2, 2, 1))[:F, :F, :3].astype(np.float32) / 255.0
                cell[F // 2:, :] *= 0.55                                                     # the cut: dug below, the Stone above
            else:
                cell[:] = pal["sky"]
                cell[GROUND_Y:] = pal["green"]
                cell[GROUND_Y + 4:] = pal["brown"]
                ST.ov(cell, surv, F // 2 - 96 + 4, GROUND_Y - 192 + 6, alpha=1.0) if i == 0 else None
            ST.ov(cell, fr, 0, 0)
            r[22:22 + F, x:x + F] = cell
        x0 = 10 + len(frames) * (F + 8) + 20
        for j, kk in enumerate((0, 1, 2) if name == "dig_sparks" else (1, 3)):
            f2 = np.repeat(np.repeat(frames[kk], 2, 0), 2, 1)
            cell = np.empty((2 * F, 2 * F, 3), np.float32)
            cell[:] = pal["sky"] if name == "dust" else pal["brown"]
            ST.ov(cell, f2, 0, 0)
            if x0 + 2 * F <= Wd:
                r[22:22 + 2 * F, x0:x0 + 2 * F] = cell
            x0 += 2 * F + 8
        rows.append(r)
        if name == "dust":                                                                   # tinted, as UNITY multiplies a ground
            t = np.empty((F + 40, Wd, 3), np.float32)
            t[:] = paper
            review._label(t, "dust frame 2 tinted by ground (multiply): Earth soil, Mars regolith, Mercury, Venus", 6, 4, scale=1)
            for i, pl in enumerate(("earth", "mars", "mercury", "venus")):
                tint = np.array(v3.hex_rgb(v3.PALETTES[pl]["brown" if pl == "earth" else "red" if pl == "mars" else "sky" if pl == "mercury" else "mustard"]), np.float32) / 255.0
                tint = 0.45 + 0.55 * tint
                fr = frames[2].astype(np.float32) / 255.0
                fr[..., :3] *= tint
                cell = np.empty((F, F, 3), np.float32)
                cell[:] = pal["sky"]
                cell[GROUND_Y:] = pal["brown"]
                a = fr[..., 3:4]
                cell[:] = fr[..., :3] * a + cell * (1 - a)
                x = 10 + i * (F + 8)
                t[22:22 + F, x:x + F] = cell
            rows.append(t)
    lines = []
    for key, frames, sheet, _m in K:
        hit = v3.palette_hits(sheet, "earth")[0] * 100
        bad = [p for p in checks(key, frames, sheet) if "palette" not in p]
        lines.append(f"{key}: {sheet.shape[1]}x{sheet.shape[0]}, palette {hit:.1f}%" + (f"; {'; '.join(bad)}" if bad else ""))
    foot = np.tile(paper, (24 + 16 * len(lines), Wd, 1))
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_fx_dig_v3.py <review png>
    preview(sys.argv[1])
