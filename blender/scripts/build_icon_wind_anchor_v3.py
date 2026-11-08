"""B-197 (LEAD cycle 283): the wind anchor's shared inventory icon, icons/wind_anchor/base (UNITY's U-159 guard
InventoryTests.ItemIconsAreSharedArt: item icons come from icons/ or props/common/; until now this item borrowed
props/neptune/wind_anchor). Drawn from the Neptune prop (build_props_neptune_v3.wind_anchor: the banded stake, the coral
cap, the striped windsock, the guy lines to two pegs) in its palette and ink, so the two read as the same thing: here the
sock fills with wind (an icon reads at 32 px) and the stake is a touch bolder. 128x128 like the item icons around it in the
inventory, pivot centre, the B-128 icon json (style v3, icon: true). The prop-sheet API so render.py's do_prop_sheet_set
exports the row (names = ["base"]).

  python -I build_icon_wind_anchor_v3.py <review png>   lock-free preview: the icon at 1x beside the item icons, at 32 px,
                                                         and beside the prop it is drawn from
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_props_neptune_v3 as NP  # noqa: E402  (gp_draw through fakegp outside Blender; the prop's palette + materials)
from meridian import fakegp, v3  # noqa: E402
import gp_raster as GR  # noqa: E402

G = NP.G
O, I = NP.O, NP.I
KEY = "icons/wind_anchor/{}"
SIZE = 128
PPU = 55                                        # the anchor (-0.08 .. 2.05 m with the stake's end cap and ink) in ~117 px of 128
CX, CZ = 0.21, 0.985                            # the drawing's centre (m), set on the frame centre (measured 15:1x: rows 4-126 at 57 / 1.01)


def icon(d, M, k=0):
    for x0 in (-0.48, 0.44):                                                              # guy lines to two pegs (closer, bigger:
        G.stroke(d, G.bowed_line((0.0, 1.35), (x0, 0.08), bow=0.02, n=8), M["ink"], I)   # the 32 px slot, rev 15:0x)
        G.stroke(d, [(x0 - 0.08, 0.0), (x0 + 0.08, 0.0), (x0 + 0.03, 0.18), (x0 - 0.03, 0.18)], M["coral"], I, cyclic=True)
    G.stroke(d, G.bowed_line((0.0, 1.35), (0.16, 0.08), bow=0.01, n=6), M["blue_ln"], I)
    stake = [(0.0, 0.0), (0.01, 0.9), (0.0, 1.8)]
    G.stroke(d, G.hose_outline(stake, 0.13), M["blue_dp"], 0.0, cyclic=True)              # the stake (bolder than the prop's)
    G.stroke(d, G.hose_outline([(0.035, 0.05), (0.045, 0.9), (0.035, 1.75)], 0.036), M["blue_sh"], 0.0, cyclic=True)
    G.stroke(d, G.hose_outline(stake, 0.13), M["ink"], O, cyclic=True)
    for z in (0.35, 0.8, 1.25):
        G.seam(d, [(-0.07, z), (0.08, z + 0.01)], M["ink"])
    G.stroke(d, [(-0.17, 0.0), (0.17, 0.0), (0.09, 0.15), (-0.09, 0.15)], M["indigo_sh"], I, cyclic=True)   # the foot plate
    top = G.bezier((0.07, 1.96), (0.38, 1.98), (0.68, 1.88), (0.98, 1.72), n=10)          # the sock, full of wind (fuller)
    bot = G.bezier((0.98, 1.5), (0.68, 1.54), (0.38, 1.52), (0.07, 1.56), n=10)
    sock = top + bot
    G.stroke(d, sock, M["wisp_f"], 0.0, cyclic=True)
    G.stroke(d, [(x, z) for x, z in bot] + [(0.07, 1.62), (0.98, 1.56)], M["wisp_sh"], 0.0, cyclic=True)
    for t0, t1 in ((0.3, 0.42), (0.6, 0.72)):                                              # two coral bands
        a, b = top[int(t0 * 10)], top[int(t1 * 10)]
        c, e = bot[10 - int(t1 * 10)], bot[10 - int(t0 * 10)]
        G.stroke(d, [a, b, c, e], M["coral_f"], 0.0, cyclic=True)
    G.stroke(d, sock, M["ink"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.07, 1.76, 0.035, 0.2, n=12, seed=43), M["wisp"], I, cyclic=True)    # the hoop at its mouth
    cap = G.lumpy_ellipse(0.0, 1.9, 0.14, 0.13, n=16, seed=41)
    G.stroke(d, cap, M["coral_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in cap if q[0] > 0.04] + [(0.04, 1.9)], M["coral_sh"], 0.0, cyclic=True)
    G.stroke(d, cap, M["ink"], O, cyclic=True)


PROPS = {"base": (icon, SIZE, SIZE, None, 1, False)}


def render_all():
    gp = fakegp.FakeGP()
    M = NP.mats(gp)
    d = fakegp.FakeDrawing()
    icon(d, M)
    piv = (0.5 - CX * PPU / SIZE, 0.5 - CZ * PPU / SIZE)
    img, w = GR.render_frame(fakegp.strokes_of(d, gp), SIZE, SIZE, PPU, piv, ss=4, seed=7)
    return {"base": [img]}, {"base": w}


def checks(img):
    m = v3.EDGE_MARGIN
    a = img[..., 3]
    p = []
    if a[:m].any() or a[-m:].any() or a[:, :m].any() or a[:, -m:].any():
        p.append(f"touches the {m} px edge")
    hit, off = v3.palette_hits(img, "neptune")
    if hit < 0.98:
        p.append(f"palette {hit * 100:.1f}% (off {' '.join(off[:3])})")
    return p, hit


def export(art, imgs=None, names=None):
    import json
    from meridian import pngio
    if imgs is None:
        imgs, _w = render_all()
    img = imgs["base"][0]
    problems, _hit = checks(img)
    if problems:
        raise ValueError("B-197 export checks: " + "; ".join(problems))
    d = os.path.join(art, "icons", "wind_anchor")
    os.makedirs(d, exist_ok=True)
    n = pngio.write_png(os.path.join(d, "base_color.png"), img)
    with open(os.path.join(d, "base.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"key": KEY.format("base"), "style": "v3", "ppu": PPU, "pivot": [0.5, 0.5], "icon": True,
                   "note": "B-197: drawn from props/neptune/wind_anchor (its palette and ink)"}, f, indent=2)
        f.write("\n")
    return [(KEY.format("base"), SIZE, SIZE, n)], {}, []


def main(out, imgs=None, widths=None, stamp_paths=()):
    """The icon at 1x in a row of item icons on the inventory paper, the row again at 32 px (the slot size), and the icon
    beside the Neptune prop it is drawn from."""
    import time
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    if imgs is None:
        imgs, widths = render_all()
    img = imgs["base"][0]
    ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art")
    names = ["iron", "copper", "float_cell_mk1", "deep_diamond", "solarite_capacitor", "soil", "tessera", "ammonia_ice"]
    icons = []
    for n in names:
        p = os.path.join(ART, "icons", n, "base_color.png")
        if os.path.isfile(p):
            icons.append((n, pngio.read_png_np(p)))
    row = [("wind_anchor (NEW)", img)] + icons
    W = 8 + len(row) * 152
    paper = np.array(review.PAPER, np.float32)
    A = np.empty((26 + 128 + 30, W, 3), np.float32)
    A[:] = paper
    B = np.empty((26 + 32 + 30, W, 3), np.float32)
    B[:] = paper
    for i, (n, ic) in enumerate(row):
        x = 8 + i * 152
        A[26:154, x:x + 128] = paper * 0.9
        review._over(A, ic, x + (128 - ic.shape[1]) // 2, 26 + (128 - ic.shape[0]) // 2)
        review._label(A, n, x, 160, scale=1)
        f = 128 // 32 if ic.shape[0] == 128 else 2                                       # the 32 px slot: box-filtered
        small = ic.reshape(ic.shape[0] // f, f, ic.shape[1] // f, f, 4).astype(np.float32).mean(axis=(1, 3)).astype(np.uint8)
        B[26:58, x:x + 32] = paper * 0.9
        review._over(B, small, x, 26)
    review._label(A, "1x (128 px; the tile items' drawn cubes are 64 px)", 8, 6, scale=1)
    review._label(B, "at 32 px, the inventory slot", 8, 6, scale=1)
    C = np.empty((26 + 200, W, 3), np.float32)
    C[:] = paper
    review._label(C, "beside the prop it is drawn from: props/neptune/wind_anchor at 1x (read from Art)", 8, 6, scale=1)
    sky = np.array(v3.hex_rgb(v3.PALETTES["neptune"]["sky"]), np.float32) / 255.0
    C[26:218, 8:8 + 128] = sky
    pp = os.path.join(ART, "props", "neptune", "wind_anchor_color.png")
    if os.path.isfile(pp):
        review._over(C, pngio.read_png_np(pp)[:192, :128], 8, 26)
    C[58:186, 160:288] = sky
    review._over(C, img, 160, 58)
    problems, hit = checks(img)
    lines = [f"icons/wind_anchor/base 128x128, pivot centre, palette {hit * 100:.1f}% (neptune), problems: {'; '.join(problems) or 'none'}"]
    for p in stamp_paths:
        lines.append("exported " + review.stamp_text(p))
    foot = np.empty((30 + 16 * len(lines), W, 3), np.float32)
    foot[:] = paper
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    head = np.empty((26, W, 3), np.float32)
    head[:] = paper
    review._label(head, "B-197: the wind anchor's shared inventory icon (icons/wind_anchor/base), drawn from the Neptune prop", 6, 6, scale=1)
    out_img = np.vstack([head, A, B, C, foot])
    review.draw(out_img, time.strftime("%m-%d %H:%M") + " " + ("exported" if stamp_paths else "design preview (lock-free, fakegp + numpy)"),
                2, out_img.shape[0] - 16, (1.0, 1.0, 0.85))
    np.clip(out_img, 0.0, 1.0, out=out_img)
    u8 = np.empty(out_img.shape[:2] + (4,), np.uint8)
    u8[..., :3] = np.rint(out_img * 255.0)
    u8[..., 3] = 255
    pngio.write_png(out, u8)
    print("written", out, u8.shape[1], "x", u8.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    main(sys.argv[1])
    fakegp.restore()
