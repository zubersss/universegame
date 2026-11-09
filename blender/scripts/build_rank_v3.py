"""B-206 (D-175; Bible 5.3 §8.1): the Surveyor Rank and expedition art in UiKit's style (B-146 / B-151 / B-208), Earth palette,
no faces, nothing from combat (no shields, no blades: D-087).

  ui/rank/insignia_<1..10>      96x96    ten Rank insignia, one rising family, read at the HUD's 48 px:
                                         1 a plain survey pin, 2 the pin with its pennant, 3 a round enamel badge with a compass
                                         needle, 4-5 the badge with one / two gold chevrons, 6 a brass medallion with the needle,
                                         7 + a ribbon, 8 + half a laurel, 9 + the full laurel, 10 the starred brass medallion (laurel,
                                         ribbon, rays)
  ui/rank/expedition_badge      112x128  the expedition badge: a teal award rosette with ribbon tails and a blank cream plate where
                                         UNITY sets the numeral (I-X; json "numeral_rect")
  ui/rank/expedition_badge_laurel        the same in a laurel, for expedition XI and on
  ui/rank/certificate           384x288  slice 72 72 104 104: the New Expedition certificate, B-208's flat paper (tile
                                         ui/panels/grain over it), a double ornamental border, corner flourishes, a red wax seal on
                                         ribbons in the bottom-right slice; lettered at runtime

  python -I build_rank_v3.py <review png>     the lock-free sheet: the insignia at 1x and 48 px, the badge at I / II / V / X and
                                              the laurel, the certificate at 1x and stretched, lettered as UNITY would
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
circ, arc, scallop, extra, done = ST.circ, ST.arc, ST.scallop, ST.extra, ST.done
INS, BW, BH = 96, 112, 128
CW, CH, CSL = 384, 288, [72, 72, 104, 104]
KEY = "ui/rank/{}"


# ---------------------------------------------------------------- parts (px, y down)
def star(cx, cy, r, ri=None, n=5, a0=-TAU / 4):
    ri = ri or r * 0.42
    return [(cx + (r if k % 2 == 0 else ri) * math.cos(a0 + TAU * k / (2 * n)), cy + (r if k % 2 == 0 else ri) * math.sin(a0 + TAU * k / (2 * n)))
            for k in range(2 * n)]


def needle(d, M, cx, cy, L, w):
    """A compass needle: red north half, cream south half, a pin at its hub."""
    G.stroke(d, [(cx - w, cy), (cx, cy - L), (cx + w, cy)], M["red"], I, cyclic=True)
    G.stroke(d, [(cx - w, cy), (cx, cy + L), (cx + w, cy)], M["offwhite"], I, cyclic=True)
    G.stroke(d, circ(cx, cy, w * 0.45, 10), M["mustard"], I * 0.8, cyclic=True)


def chevron(d, M, cx, cy, w, h, t):
    G.stroke(d, [(cx - w, cy), (cx, cy - h), (cx + w, cy), (cx + w, cy + t), (cx, cy - h + t), (cx - w, cy + t)], M["mustard"], I, cyclic=True)


def ribbon(d, M, cx, top, w, L, role="red"):
    """Two ribbon tails hanging from under a medallion, notched ends."""
    for s in (-1, 1):
        x0 = cx + s * w * 0.35
        pts = [(x0 - w * 0.3, top), (x0 + w * 0.3, top), (x0 + w * 0.3 + s * w * 0.25, top + L), (x0 + s * w * 0.25, top + L - w * 0.25),
               (x0 - w * 0.3 + s * w * 0.25, top + L)]
        G.stroke(d, pts, M[role], I, cyclic=True)


def laurel(d, M, cx, cy, r, sides=(-1, 1), leaves=7):
    """A laurel: leaves along arcs up both sides of a medallion, a stem under them."""
    for s in sides:
        G.stroke(d, arc(cx, cy, r, math.radians(90 + s * 20), math.radians(90 + s * 160), 14), M["ln_brown"], I)
        for k in range(leaves):
            a = math.radians(90 + s * (30 + 125 * k / (leaves - 1)))
            lx, ly = cx + r * math.cos(a), cy + r * math.sin(a)
            ang = a + s * math.radians(70)
            pts = [(lx + 6.5 * math.cos(ang) * t - 3.0 * math.sin(ang) * math.sin(math.pi * (t + 1) / 2) * (1 if j == 0 else -1),
                    ly + 6.5 * math.sin(ang) * t + 3.0 * math.cos(ang) * math.sin(math.pi * (t + 1) / 2) * (1 if j == 0 else -1))
                   for j in (0, 1) for t in ([-1 + 2 * i / 6 for i in range(7)] if j == 0 else [1 - 2 * i / 6 for i in range(7)])]
            G.stroke(d, pts, M["green"], I * 0.8, cyclic=True)


def pin(d, M, cx, cy, s, pennant=False):
    """The survey pin: a steel needle with a round head (a marker pin, driven in), its pennant at rank 2."""
    G.stroke(d, [(cx - 2 * s, cy - 2 * s), (cx + 2 * s, cy - 2 * s), (cx, cy + 30 * s)], M["sky_sh"], I, cyclic=True)
    if pennant:
        G.stroke(d, [(cx + 1.5 * s, cy - 24 * s), (cx + 1.5 * s, cy - 8 * s), (cx + 22 * s, cy - 15 * s)], M["red"], I, cyclic=True)
        G.stroke(d, [(cx + 1.5 * s, cy - 26 * s), (cx + 1.5 * s, cy - 2 * s)], M["ink"], I * 1.2)
    G.stroke(d, circ(cx, cy - 6 * s, 9 * s, 24), M["mustard" if pennant else "sky"], O, cyclic=True)
    G.stroke(d, arc(cx, cy - 6 * s, 6 * s, math.radians(200), math.radians(250), 6), M["ln_offwhite"], I * 1.2)


def badge(d, M, cx, cy, r):
    G.stroke(d, circ(cx, cy, r, 48), M["teal"], O, cyclic=True)
    G.stroke(d, circ(cx, cy, r - 6, 44), M["offwhite"], I, cyclic=True)
    needle(d, M, cx, cy, r - 12, 5.5)


def medallion(d, M, cx, cy, r, centre="needle"):
    G.stroke(d, scallop(cx, cy, r, 16, 0.06), M["mustard"], O, cyclic=True)
    G.stroke(d, circ(cx, cy, r - 6, 44), M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, circ(cx, cy, r - 9, 44), M["mustard"], I, cyclic=True)
    G.stroke(d, ST.sector(cx, cy, r - 13, r - 10, math.radians(200), math.radians(250), 6), M["offwhite_f"], 0.0, cyclic=True)   # sheen
    if centre == "needle":
        needle(d, M, cx, cy, r - 14, 5.0)
    else:
        G.stroke(d, star(cx, cy, r - 12), M["offwhite"], I, cyclic=True)


def insignia(rank, seed=200):
    c = U.Canvas(INS, INS)
    d, M = c.dm, extra(c)
    cx, cy = INS / 2, INS / 2
    if rank == 1:
        pin(d, M, cx, cy - 4, 1.25)
    elif rank == 2:
        pin(d, M, cx - 6, cy - 2, 1.25, pennant=True)
    elif rank <= 5:
        badge(d, M, cx, cy - (6 if rank > 3 else 0), 30)
        for k in range(rank - 3):
            chevron(d, M, cx, cy + 34 + 9 * k, 20, 8, 5)
    elif rank <= 9:
        if rank >= 7:
            ribbon(d, M, cx, cy + 14, 18, 30)
        if rank >= 8:
            laurel(d, M, cx, cy - 4, 37, sides=(-1,) if rank == 8 else (-1, 1))
        medallion(d, M, cx, cy - 4, 28)
    else:                                                                                     # rank 10: the starred medallion
        for k in range(12):                                                                   # rays behind it
            a = TAU * k / 12 + TAU / 24
            G.stroke(d, [(cx + 30 * math.cos(a - 0.08), cy - 4 + 30 * math.sin(a - 0.08)), (cx + 44 * math.cos(a), cy - 4 + 44 * math.sin(a)),
                         (cx + 30 * math.cos(a + 0.08), cy - 4 + 30 * math.sin(a + 0.08))], M["mustard_sh"], 0.0, cyclic=True)
        ribbon(d, M, cx, cy + 14, 18, 30)
        laurel(d, M, cx, cy - 4, 37)
        medallion(d, M, cx, cy - 4, 28, centre="star")
    return done(c, seed + rank)


NUMERAL_RECT = [28, 30, 56, 40]                                                               # x, y (from the top), w, h px


def expedition_badge(laurel_ring=False, seed=230):
    c = U.Canvas(BW, BH)
    d, M = c.dm, extra(c)
    cx, cy = BW / 2, 52
    for s in (-1, 1):                                                                         # the ribbon tails
        x0 = cx + s * 14
        G.stroke(d, [(x0 - 10, 76), (x0 + 10, 76), (x0 + 10 + s * 8, 124), (x0 + s * 8, 116), (x0 - 10 + s * 8, 124)], M["teal_sh"], I, cyclic=True)
    if laurel_ring:
        laurel(d, M, cx, cy, 46, leaves=8)
    G.stroke(d, scallop(cx, cy, 42, 18, 0.1), M["teal"], O, cyclic=True)                     # the rosette
    G.stroke(d, circ(cx, cy, 34, 44), M["mustard"], I, cyclic=True)
    x, y, w, h = NUMERAL_RECT                                                                 # the blank plate
    G.stroke(d, U.wavy_rect(x, y, x + w, y + h, 0.4, seed), M["offwhite"], I, cyclic=True)
    return done(c, seed + (1 if laurel_ring else 0))


def certificate(seed=260):
    c = U.Canvas(CW, CH)
    d, M = c.dm, extra(c)
    outer = U.wavy_rect(6, 6, CW - 6, CH - 6, 1.0, seed)
    G.stroke(d, outer, M["offwhite_f"], 0.0, cyclic=True)
    for inset, w, mat in ((18, I * 1.4, "ln_brown"), (24, I * 0.8, "ln_mustard_sh")):         # the double border
        G.stroke(d, U.wavy_rect(inset, inset, CW - inset, CH - inset, 0.3, seed + inset), M[mat], w, cyclic=True)
    for (x, y, fx, fy) in ((24, 24, 1, 1), (CW - 24, 24, -1, 1), (24, CH - 24, 1, -1)):       # corner flourishes (the seal takes the 4th)
        G.stroke(d, [(x + fx * (4 + 30 * t), y + fy * (4 + 14 * math.sin(math.pi * t) * 0.6 + 2 * t)) for t in [i / 12 for i in range(13)]], M["ln_brown"], I)
        G.stroke(d, [(x + fx * (4 + 2 * t + 14 * math.sin(math.pi * t) * 0.6), y + fy * (4 + 30 * t)) for t in [i / 12 for i in range(13)]], M["ln_brown"], I)
        G.stroke(d, star(x + fx * 12, y + fy * 12, 5, 2, 4, 0.0), M["mustard"], I * 0.7, cyclic=True)
    sx, sy = CW - 58, CH - 58                                                                  # the wax seal on its ribbons
    for s in (-1, 1):
        G.stroke(d, [(sx + s * 6 - 7, sy + 14), (sx + s * 6 + 7, sy + 14), (sx + s * 18 + 7, sy + 46), (sx + s * 18, sy + 40), (sx + s * 18 - 7, sy + 46)],
                 M["mustard"], I, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(sx, sy, 27, 26, n=30, lump=0.08, seed=seed), M["red"], O, cyclic=True)
    G.stroke(d, circ(sx, sy, 18, 36), M["ln_red"], I, cyclic=True)
    G.stroke(d, star(sx, sy, 12, 5), M["red_sh"], 0.0, cyclic=True)
    G.stroke(d, star(sx, sy, 12, 5), M["ink"], I * 0.7, cyclic=True)
    G.stroke(d, outer, M["ink"], O, cyclic=True)
    return done(c, seed)


# ---------------------------------------------------------------- the export (on LEAD's OK)
def kit():
    out = [(f"insignia_{r}", insignia(r)[0], {"rank": r, "display_px": 48, "note": f"Surveyor Rank {r}: the HUD shows it at 48 px, the tree panel at 96"})
           for r in range(1, 11)]
    out.append(("expedition_badge", expedition_badge()[0], {"numeral_rect": NUMERAL_RECT, "rect_origin": "top_left", "numerals": "I-X",
                                                            "lettering": "runtime", "note": "UNITY sets the expedition's numeral (Limelight, ink) centred in numeral_rect"}))
    out.append(("expedition_badge_laurel", expedition_badge(True)[0], {"numeral_rect": NUMERAL_RECT, "rect_origin": "top_left", "numerals": "XI and on",
                                                                       "lettering": "runtime", "note": "from expedition XI: the badge in a laurel"}))
    out.append(("certificate", certificate()[0], {"slice": list(CSL), "grain": U.GRAIN_KEY, "lettering": "runtime",
                                                  "slice_order": "[left, top, right, bottom] px in from each edge (contract 11.6); Unity's Sprite.border is (left, bottom, right, top)",
                                                  "note": "the New Expedition certificate (B-208's flat paper: tile ui/panels/grain over it, masked); the seal sits in the bottom-right slice"}))
    return out


def export(art):
    import json
    from meridian import pngio
    built, problems = [], []
    for name, img, extra_meta in kit():
        h, w = img.shape[:2]
        meta = {"key": KEY.format(name), "style": "v3", "ppu": U.PPU, "pivot": [0.5, 0.5], "width": w, "height": h, "palette": "earth", **extra_meta}
        hit = v3.palette_hits(img, "earth")[0]
        m = v3.EDGE_MARGIN
        if w % 4 or h % 4:
            problems.append(f"{name}: {w}x{h} not a multiple of 4")
        if hit < 0.995:
            problems.append(f"{name}: palette {hit * 100:.1f}%")
        if name != "certificate" and (img[:m, :, 3].any() or img[-m:, :, 3].any() or img[:, :m, 3].any() or img[:, -m:, 3].any()):
            problems.append(f"{name}: touches the {m} px edge")
        built.append((meta["key"], img, meta))
    if problems:
        raise ValueError("B-206 rank kit checks: " + "; ".join(problems))
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


def keys():
    return [KEY.format(n) for n in [f"insignia_{r}" for r in range(1, 11)] + ["expedition_badge", "expedition_badge_laurel", "certificate"]]


# ---------------------------------------------------------------- the review sheet
def preview(out, footnote=None):
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    paper = np.array(review.PAPER, np.float32)
    ink = np.array(v3.hex_rgb(v3.INK), np.float32) / 255.0

    def down2(ic):
        return np.rint(ic.astype(np.float32).reshape(ic.shape[0] // 2, 2, ic.shape[1] // 2, 2, 4).mean(axis=(1, 3))).astype(np.uint8)

    def letter(dst, text, cx, cy, size, font):
        m = U.text_mask(font, text, size, wobble=0.2, seed=3)
        h, w = m.shape
        x, y = int(cx - w / 2), int(cy - h / 2)
        sub = dst[y:y + h, x:x + w]
        sub[:] = ink * m[..., None] + sub * (1 - m[..., None])
    W = 1400
    rows = []
    head = np.tile(paper, (28, W, 1)).astype(np.float32)
    review._label(head, "B-206 the Surveyor Rank insignia (1x 96 px | the HUD's 48 px), the expedition badge (I, II, V, X; the laurel from XI), the New Expedition certificate", 6, 8)
    rows.append(head)
    r1 = np.tile(paper, (96 + 48 + 60, W, 1)).astype(np.float32)
    ins = [insignia(r)[0] for r in range(1, 11)]
    for i, im in enumerate(ins):
        x = 12 + i * 136
        ST.ov(r1, im, x, 22)
        ST.ov(r1, down2(im), x + 24, 22 + 96 + 10)
        review._label(r1, f"rank {i + 1}", x + 20, 6, scale=1)
    rows.append(r1)
    r2 = np.tile(paper, (BH + 40, W, 1)).astype(np.float32)
    b, bl = expedition_badge()[0], expedition_badge(True)[0]
    x = 12
    for num in ("I", "II", "V", "X"):
        ST.ov(r2, b, x, 24)
        nx, ny, nw, nh = NUMERAL_RECT
        letter(r2, num, x + nx + nw / 2, 24 + ny + nh / 2 + 1, 28, U.LIMELIGHT)
        review._label(r2, f"expedition {num}", x + 10, 6, scale=1)
        x += BW + 30
    ST.ov(r2, bl, x, 24)
    letter(r2, "XI", x + NUMERAL_RECT[0] + NUMERAL_RECT[2] / 2, 24 + NUMERAL_RECT[1] + NUMERAL_RECT[3] / 2 + 1, 26, U.LIMELIGHT)
    review._label(r2, "XI and on (laurel)", x, 6, scale=1)
    x += BW + 30
    ST.ov(r2, b, x, 24)
    review._label(r2, "blank, as exported", x + 4, 6, scale=1)
    rows.append(r2)
    cert = certificate()[0]
    g = U.grain_tile().astype(np.float32) / 255.0

    def grained(img):
        h, w = img.shape[:2]
        t = np.tile(g, (h // U.GRAIN_PX + 1, w // U.GRAIN_PX + 1, 1))[:h, :w]
        f = img.astype(np.float32) / 255.0
        a = t[..., 3:4] * (f[..., 3:4] > 0)
        f[..., :3] = f[..., :3] * (1 - a) + g[0, 0, :3] * a
        return np.rint(f * 255).astype(np.uint8)
    big = U.nine_slice(cert, CSL, 760, 440)
    r3 = np.tile(np.array([0.36, 0.36, 0.40], np.float32), (460 + 40, W, 1)).astype(np.float32)
    ST.ov(r3, grained(cert), 12, 28)
    ST.ov(r3, grained(big), 12 + CW + 40, 28)
    cx0 = 12 + CW + 40
    letter(r3, "New Expedition", cx0 + 380 - 40, 28 + 92, 50, U.LIMELIGHT)
    for k, ln in enumerate(("You leave behind: your Skill Tree, Scrip, Rank, the pack and the holds.",
                            "You keep: the Catalogue, the story, Datacores, the planets and your buildings.",
                            "Every Skill Tree bonus x 1.25 on Expedition II.")):
        letter(r3, ln, cx0 + 360, 28 + 170 + 40 * k, 24, U.PATRICK)
    review._label(r3, "certificate 1x (384x288, slice 72 72 104 104) | stretched to 760x440, lettered as UNITY would, the B-208 grain tiled", 12, 8, scale=1)
    rows.append(r3)
    lines = []
    for name, img, _m in kit():
        hit = v3.palette_hits(img, "earth")[0] * 100
        m = v3.EDGE_MARGIN
        edge = name != "certificate" and (img[:m, :, 3].any() or img[-m:, :, 3].any() or img[:, :m, 3].any() or img[:, -m:, 3].any())
        lines.append(f"{KEY.format(name)}: {img.shape[1]}x{img.shape[0]}, palette {hit:.1f}%" + ("; EDGE" if edge else ""))
    foot = np.tile(paper, (24 + 16 * ((len(lines) + 1) // 2), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6 + (i % 2) * 700, 6 + 16 * (i // 2), scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_rank_v3.py <review png>
    preview(sys.argv[1])
