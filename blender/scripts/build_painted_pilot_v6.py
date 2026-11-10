"""B-251 (D-202): THE PAINTER'S-HAND PILOT. Painted material made by LEAD (AI-painted, credited in docs/credits/lead.md):
docs/art_sources/v6_painted/strokes_01.png (about thirty gouache strokes on white) and plant_01.png (one broad-leaved
plant on plain pale grey), 2048 x 2048 each. One sheet:
  (a) THE STROKES AS THE BRUSH: the bank the loader cut out, by kind; then the SAME specimens (the broad-leaved plant,
      the tree with its bark) painted twice by the same rules - once with my oval dab, once with the painted strokes;
  (b) THE PLANT AS A PLATE: cut from its ground, re-keyed to the frame's greens under its light, and placed three
      times in the 96 px forest frame beside my own plants.
Nothing is exported; nothing here goes into Assets.

  python -I build_painted_pilot_v6.py <review png> [a | b | ab]      (default ab; a alone is about 40 s, b adds the frame)
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
import painted_v6 as PV  # noqa: E402

SRC = os.path.normpath(os.path.join(HERE, "..", "..", "docs", "art_sources", "v6_painted"))
PLATE_M = 1.3                                     # the painted plant's height in the world (m)


class painted_brush:
    """While open, every Painting.brush lays PAINTED strokes from the bank instead of the oval dab: the specimens' own
    rules run unchanged. The kind is chosen from the dab the rule asked for: a round leaf dab -> "leaf", a bark or ground
    dab -> "dry", a long stroke along a leaf -> "long". grow: a painted stroke is thinner than the oval it replaces."""
    def __init__(self, bank, grow=1.2):
        self.bank, self.grow = bank, grow

    def __enter__(self):
        self.orig = PT.Painting.brush
        bank, grow = self.bank, self.grow

        def brush(P, under, where, n, size, aspect=(2.0, 4.0), angle=0.0, spread=0.3, alpha=(0.7, 1.0), jitter=0.05, hue=0.012,
                  edge=3.0, streak=0.25, clip=None, win=None):
            asp = (aspect[0] + aspect[1]) / 2.0
            kind = "leaf" if asp < 2.4 else "dry" if asp < 3.3 else "long"
            PV.brush(P, bank, under, where, n, (size[0] * grow, size[1] * grow), aspect, angle, spread, alpha, jitter, hue, edge, streak, clip, win, kind=kind)
        PT.Painting.brush = brush
        return self

    def __exit__(self, *exc):
        PT.Painting.brush = self.orig
        return False


def pilot(out, parts="ab"):
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    t0 = time.time()
    paper = np.array(review.PAPER, np.float32)
    Wd = 1920
    dd = os.path.join(os.path.dirname(out), "b251")
    os.makedirs(dd, exist_ok=True)
    rows, lines = [], []

    def head(text, h=20):
        hd = np.tile(paper, (h, Wd, 1)).astype(np.float32)
        review._label(hd, text[:310], 6, 4, scale=1)
        return hd

    def row(cells, gap=10, bg=None):
        H = max(c.shape[0] for c in cells)
        r = np.tile(paper if bg is None else bg, (H, Wd, 1)).astype(np.float32)
        x = 0
        for c in cells:
            w = max(0, min(c.shape[1], Wd - x))
            r[H - c.shape[0]:, x:x + w] = c[:, :w, :3]
            x += c.shape[1] + gap
        return r

    def save(name, img):
        pngio.write_png(os.path.join(dd, name), np.dstack([pngio.to_u8(np.clip(img[..., :3], 0, 1)), np.full(img.shape[:2], 255, np.uint8)]))

    def zoom(im, k):
        return np.repeat(np.repeat(im, k, 0), k, 1)

    rows.append(head("B-251 (D-202): THE PAINTER'S-HAND PILOT - AI-painted strokes as my brush, and an AI-painted plant as a plate. PREVIEW, nothing exported", 26))
    if "a" in parts:
        t1 = time.time()
        bank = PV.strokes(os.path.join(SRC, "strokes_01.png"))
        kinds = {}
        for st in bank:
            kinds[st.kind] = kinds.get(st.kind, 0) + 1
        lines.append(f"(a) strokes_01.png: {len(bank)} strokes cut out in {time.time() - t1:.0f} s; by kind: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items()))
                     + f"; their bodies {min(2 * st.a for st in bank):.0f}-{max(2 * st.a for st in bank):.0f} px long, {min(2 * st.b for st in bank):.0f}-{max(2 * st.b for st in bank):.0f} px wide")
        lines.append("    bands of paint across the stroke (a dry drag is over " + f"{PV.DRY_AT}): " + "; ".join(
            f"{k} {min(st.ragged for st in bank if st.kind == k):.2f}-{max(st.ragged for st in bank if st.kind == k):.2f}" for k in sorted(kinds)))
        # the bank, every stroke laid along +x at one size, in ink, by kind: what the loader found
        B = PT.Painting(Wd, 120, 1, 1)
        B.img[:] = paper
        x, order = 30.0, sorted(bank, key=lambda st: ("leaf", "long", "curl", "dry").index(st.kind))
        last = None
        for st in order[:44]:
            if st.kind != last:
                x += 0 if last is None else 30
                review._label(B.img, st.kind, int(x), 4, scale=1)
                last = st.kind
            half = min(26.0, 20.0 * st.a / max(st.b * 4.0, 1.0) + 8.0)
            PV.stamp(B, st, x + half, 68.0, half, 0.0, np.array((0.16, 0.26, 0.2), np.float32))
            x += 2 * half + 10
            if x > Wd - 60:
                break
        rows += [head("(a) THE BANK: every stroke the loader cut from strokes_01.png, turned onto its long axis, by kind (its own dry edges and tone kept)"), B.img.copy()]
        save("bank.png", B.img)
        made = {}
        for name, fn in (("plant", SP.plant), ("tree", SP.tree)):
            t2 = time.time()
            oval = fn()
            with painted_brush(bank):
                pai = fn()
            made[name] = (oval, pai)
            lines.append(f"    {name}: the oval dab {oval.count} dabs; the painted strokes {pai.count} strokes; both {time.time() - t2:.0f} s")
            for tag, P in (("oval", oval), ("painted", pai)):
                save(f"{name}_{tag}_2x.png", PT.tooth(np.clip(P.img, 0, 1), 4))
        rows.append(head("(a) THE SAME RULES, TWO BRUSHES, at the game's size: the plant with my OVAL dab | with the PAINTED strokes | the tree with the OVAL dab | with the PAINTED strokes"))
        rows.append(row([PT.tooth(P.shrunk(), 3) for name in ("plant", "tree") for P in made[name]]))
        rows.append(head("(a) the same four AS PAINTED (2x): oval | painted | oval | painted"))
        rows.append(row([PT.tooth(np.clip(P.img, 0, 1), 4) for name in ("plant", "tree") for P in made[name]]))
        del made, bank
    if "b" in parts:
        import build_forest_frame_v6 as FF
        t1 = time.time()
        src = PV.read_rgb(os.path.join(SRC, "plant_01.png"))
        pl = PV.plate(os.path.join(SRC, "plant_01.png"), PLATE_M)
        lines.append(f"(b) plant_01.png: cut out in {time.time() - t1:.0f} s: the plate {pl.alpha.shape[1]}x{pl.alpha.shape[0]} px of {src.shape[1]}x{src.shape[0]}, "
                     f"{float((pl.alpha > 0.5).mean()) * 100:.0f} % of its box opaque, {float(((pl.alpha > 0.02) & (pl.alpha < 0.98)).mean()) * 100:.1f} % edge; its foot at x {pl.foot[0]:.0f}; stands {PLATE_M} m")
        src4 = PV.shrink(src, 4)
        del src
        pl = PV.smaller(pl, 2)                                                   # (run 1 carried three plates at 1720 px: a peak of 1540 MB)
        near = PV.rekey(pl, FK.greens(1.0), 0.7)
        mid = PV.rekey(pl, FK.greens(0.6, 0.25), 0.7, pale=0.25, haze=FK.HAZE)
        shade = PV.rekey(pl, FK.greens(1.0, 0.0, 0.5), 0.7)

        def on_stage(p, f=2):
            m = p.mips()[int(math.log2(f))]
            st = np.tile(np.array((0.665, 0.725, 0.571), np.float32), m.shape[:2] + (1,))
            return m[..., :3] + st * (1 - m[..., 3:4])
        rows.append(head("(b) THE PLATE at a quarter of its painted size: the source on its grey | cut out, on the stage tone (the edge) | re-keyed to the frame's greens, near and lit"))
        rows.append(row([src4, on_stage(pl), on_stage(near)]))                  # (run 3: five cells in one row ran off the sheet)
        rows.append(head("(b) re-keyed for the middle distance (hazed, lit) | for the near layer in shade | my own broad-leaved plant by the same light, at the same height (the specimen, 2x)"))
        mine = SP.plant()
        rows.append(row([on_stage(mid), on_stage(shade), PT.tooth(np.clip(mine.img, 0, 1), 4)]))
        save("plate_cut.png", on_stage(pl, 1))
        spots = []

        def hook(stage, P, S_):
            # (Run 1: the mid-distance plate stood behind my near plants, unseen; a LIT plate in the shaded right corner
            # looked pasted on. Now: one in the open behind the pit, hazed and lit; two in the near corners in their
            # neighbours' shade, one mirrored.)
            m_ = 64.0 / S_.ppm
            wv = FF.W / S_.ppm
            if stage == "understorey":
                x, z, k = 16.3, 0.3, 0.9
                tf, s = S_.local(x, z, k, 1, 0.0)
                PV.place(P, mid, tf, s)
                spots.append(("mid-distance, hazed, lit", x, z, k))
            elif stage == "near":
                for dx, k, flip in ((4.5, 1.2, 1), (wv - 5.0, 1.25, -1)):
                    x = S_.x0 + dx * m_ if dx < wv / 2 else S_.x0 + wv - (wv - dx) * m_
                    tf, s = S_.local(x, -0.1, k, flip, 0.0)
                    PV.place(P, shade, tf, s)
                    spots.append(("near, in shade" + (", mirrored" if flip < 0 else ""), x, -0.1, k))
        name, ppm, x0, gy, K, _fn = [c for c in FF.CAMERAS if c[1] == 96][0]
        t2 = time.time()
        P, yb, T = FF.paint(ppm, x0, gy, hook=hook)
        FF.cels(P, yb, ppm, x0, gy, K)
        frame = PT.tooth(P.shrunk(), 5)
        del P
        save("forest_frame_96_plates.png", frame)
        lines.append(f"    the 96 px frame with three plates: {time.time() - t2:.0f} s; b251/forest_frame_96_plates.png")
        rows += [head("(b) THE 96 px FRAME WITH THREE PLATES among my own plants: " + "; ".join(f"{w} at x {x:.1f} m" for w, x, _z, _k in spots)), frame]
        crops = []
        for w, x, z, k in spots:
            cx, cy = int((x - x0) * ppm), int(gy - z * ppm)
            hh = int(PLATE_M * k * ppm * 1.25)
            c = frame[max(cy - hh, 0):min(cy + 40, frame.shape[0]), max(cx - 155, 0):min(cx + 155, frame.shape[1])]   # (run 3: 400 px crops at 2x ran off the sheet)
            crops.append(zoom(c, 2))
        rows.append(head("(b) each plate at 2x with its neighbours (my plants beside it): " + " | ".join(w for w, _x, _z, _k in spots)))
        rows.append(row(crops))
    lines.append(f"this run: {time.time() - t0:.0f} s. Files in b251/.")
    foot = np.tile(paper, (24 + 16 * len(lines), Wd, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:310], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-251 the painter's-hand pilot (lock-free, numpy; nothing exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    pilot(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "ab")
