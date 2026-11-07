"""Cartoon HUD art (Bible §9.3, contract §11.6; B-121). numpy only (gp_raster fills + capsules).

ui/hud/gauges: one 1024^2 sheet with three dial faces (Suit power, Oxygen, Gravity readout) and
their needles as separate parts (rects bottom-left origin, pivots 0..1, like a rig set); dials
are aged paper with ink, one shadow tone, a coloured zone arc, hand-drawn ticks and an icon
(lightning bolt, three bubbles, a falling apple). gauges.json gives each needle's sweep.
ui/hud/escape_line: 512x64 tileable hand-painted dotted line (dots repeat every 64 px).
ui/hud/escape_sign: <= 256^2 little painted sign on a post; the lettering (Patrick Hand,
D-090) is added once the font is in the repo (json "lettering": "pending").

  python build_hud_v3.py <out_dir> [--art]     preview (or export into <out_dir> as Art)
"""
import json
import math
import os
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gp_raster as GR  # noqa: E402
from meridian import pngio, v3  # noqa: E402

SS = 4
PAL = {k: np.array(v3.hex_rgb(h), np.float32) / 255 for k, h in v3.PALETTES["earth"].items()}
OUT_W, IN_W = 2.5, 1.25              # v3.1 (D-100): outer 2.0-3.0, interior 1.0-1.5 px after jitter


def mix(a, b, t):
    return a * (1 - t) + b * t


def shade(c):
    return mix(c, PAL["brown"], 0.3)


class Canvas:
    """W x H px at 1x; draw in px (y down) with fills and jittered ink, read back straight alpha."""
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.acc = np.zeros((h * SS, w * SS, 4), np.float32)
        self.n = 0

    def _over(self, m, rgb, a=1.0):
        al = m.astype(np.float32)[..., None] * a
        self.acc[..., :3] = rgb * al + self.acc[..., :3] * (1 - al)
        self.acc[..., 3:] = al + self.acc[..., 3:] * (1 - al)

    def fill(self, pts, rgb, a=1.0):
        p = np.asarray(pts, np.float64) * SS
        self._over(GR._poly_mask(p[:, 0], p[:, 1], self.h * SS, self.w * SS), rgb, a)

    def ink(self, pts, width, cyclic=False, rgb=None):
        p = np.asarray(pts, np.float64)
        self.n += 1
        xz = np.c_[p[:, 0], -p[:, 1]] / 64.0
        r = GR.jittered_radius(xz, np.full(len(p), width / 2 / 64.0), zlib.crc32(str(self.n).encode()), 64.0) * 64.0 * SS
        self._over(GR._ink_mask(p[:, 0] * SS, p[:, 1] * SS, r, cyclic, self.h * SS, self.w * SS),
                   PAL["ink"] if rgb is None else rgb)

    def shape(self, pts, rgb, width=OUT_W):
        self.fill(pts, rgb)
        self.ink(pts, width, cyclic=True)

    def image(self):
        s = self.acc.reshape(self.h, SS, self.w, SS, 4).mean(axis=(1, 3))
        a = s[..., 3:4]
        rgb = np.where(a > 1e-6, s[..., :3] / np.maximum(a, 1e-6), 0)
        return np.clip(np.rint(np.dstack([rgb, a]) * 255), 0, 255).astype(np.uint8)


def circle(cx, cy, r, n=64, lump=0.012, seed=0):
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.28, 2)
    return [(cx + r * (1 + lump * math.sin(3 * t + ph[0]) + 0.6 * lump * math.sin(5 * t + ph[1])) * math.cos(t),
             cy + r * (1 + lump * math.sin(3 * t + ph[0]) + 0.6 * lump * math.sin(5 * t + ph[1])) * math.sin(t))
            for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def arc(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(a), cy - r * math.sin(a)) for a in np.linspace(a0, a1, n)]


SWEEP = (math.radians(215), math.radians(-35))      # needle from min (lower left) to max (lower right)


def dial(name, colour, icon, seed):
    """One dial face 320x320: rim, paper face with a shadow crescent, a zone arc, ticks, icon."""
    S = 320
    c = Canvas(S, S)
    cx = cy = S / 2
    c.shape(circle(cx, cy, 150, seed=seed), mix(PAL["brown"], PAL["mustard"], 0.35))          # bezel
    face = circle(cx, cy, 124, seed=seed + 1)
    c.fill(face, shade(PAL["offwhite"]))                                         # one shadow tone: lower-right crescent
    c.fill(circle(cx - 9, cy - 9, 119, seed=seed + 1), PAL["offwhite"])
    c.ink(face, IN_W, cyclic=True)
    a0, a1 = SWEEP
    zone_lo = arc(cx, cy, 108, a0, a0 + (a1 - a0) * 0.25)                                       # danger zone: red
    zone_hi = arc(cx, cy, 92, a0 + (a1 - a0) * 0.25, a0, n=12)
    c.shape(zone_lo + zone_hi, PAL["red"], IN_W)
    ok_a = arc(cx, cy, 108, a0 + (a1 - a0) * 0.25, a1, n=40)
    ok_b = arc(cx, cy, 92, a1, a0 + (a1 - a0) * 0.25, n=40)
    c.shape(ok_a + ok_b, colour, IN_W)
    for k in range(11):                                                                         # ticks
        a = a0 + (a1 - a0) * k / 10
        r0 = 70 if k % 5 == 0 else 78
        c.ink([(cx + r0 * math.cos(a), cy - r0 * math.sin(a)), (cx + 88 * math.cos(a), cy - 88 * math.sin(a))],
              IN_W)                                                     # major ticks are longer, not thicker (v3.1)
    ix, iy = cx, cy + 58                                                                        # icon below the hub
    if icon == "bolt":
        c.shape([(ix + 6, iy - 30), (ix - 14, iy + 2), (ix - 1, iy + 2), (ix - 8, iy + 30), (ix + 15, iy - 6), (ix + 2, iy - 6)],
                PAL["mustard"], IN_W)
    elif icon == "bubbles":
        for bx, by, br in ((ix - 12, iy + 8, 13), (ix + 12, iy - 2, 10), (ix - 2, iy - 20, 7)):
            c.shape(circle(bx, by, br, n=24, seed=seed + int(bx)), mix(PAL["sky"], PAL["offwhite"], 0.4), IN_W)
    else:                                                                                       # gravity: a falling apple + arrow
        c.shape(circle(ix, iy - 6, 15, n=28, seed=seed + 5), PAL["red"], IN_W)
        c.ink([(ix, iy - 21), (ix + 4, iy - 30)], IN_W)
        c.ink([(ix - 24, iy - 16), (ix - 24, iy + 22)], IN_W)
        c.ink([(ix - 31, iy + 13), (ix - 24, iy + 23), (ix - 17, iy + 13)], IN_W)
    for a in (0.785, 2.356, 3.927, 5.498):                       # bezel screws with their slots
        sx_, sy_ = cx + 137 * math.cos(a), cy + 137 * math.sin(a)
        c.shape(circle(sx_, sy_, 5, n=12, seed=int(a * 10)), mix(PAL['mustard'], PAL['offwhite'], 0.3), IN_W)
        c.ink([(sx_ - 3 * math.cos(a + 1.2), sy_ - 3 * math.sin(a + 1.2)), (sx_ + 3 * math.cos(a + 1.2), sy_ + 3 * math.sin(a + 1.2))], IN_W)
    for j in range(3):                                          # hatch in the shadow crescent
        hx, hy = cx + 70 + 9 * j, cy + 78 - 9 * j
        c.ink([(hx - 7, hy + 7), (hx + 7, hy - 7)], IN_W)
    c.ink(circle(cx, cy, 150, seed=seed), OUT_W, cyclic=True)
    return c.image()


def needle(seed):
    """Needle part 48x150, pivot at the hub (pointing up); red with an ink outline + brass hub."""
    c = Canvas(48, 150)
    cx, hy = 24, 124
    c.shape([(cx - 6, hy), (cx - 2, 18), (cx, 10), (cx + 2, 18), (cx + 6, hy)], PAL["red"], OUT_W)
    c.ink([(cx, hy - 20), (cx, 30)], IN_W)                     # the needle's centre ridge
    c.shape(circle(cx, hy, 14, n=28, seed=seed), PAL["mustard"], OUT_W)
    c.ink(circle(cx, hy, 4, n=12, seed=seed + 1), IN_W, cyclic=True)
    return c.image(), (cx / 48, 1 - hy / 150)


def escape_line():
    """512x64 tileable dotted line: 8 painted mustard dots with ink every 64 px, sizes jittered;
    period-exact so tiles join (dot k at x = 32 + 64 k)."""
    c = Canvas(512, 64)
    rng = np.random.default_rng(3)
    for k in range(8):
        r = rng.uniform(9, 12)
        c.shape(circle(32 + 64 * k, 32 + rng.uniform(-2, 2), r, n=24, lump=0.06, seed=k), PAL["mustard"], OUT_W)
    return c.image()


def escape_sign():
    """<= 256^2 sign: a brown post with a slightly crooked off-white board; lettering pending."""
    c = Canvas(192, 224)
    c.shape([(88, 222), (86, 120), (104, 118), (106, 222)], PAL["brown"])
    for gx in (92, 99):                                         # post grain
        c.ink([(gx, 214), (gx + 1, 180), (gx - 1, 150), (gx, 128)], IN_W)
    board = [(14, 46), (176, 34), (182, 120), (20, 130)]
    c.shape(board, PAL["offwhite"])
    c.fill([(20, 112), (180, 102), (182, 120), (20, 130)], shade(PAL["offwhite"]))
    for gy, b in ((62, 0.0), (80, 2.0), (98, -1.5)):            # board grain, slightly bowed
        c.ink([(28, gy + b), (90, gy - 2 + b), (168, gy - 6 + b)], IN_W)
    c.ink(board, OUT_W, cyclic=True)
    for nx, ny in ((30, 56), (166, 46)):
        c.shape(circle(nx, ny, 5, n=12, seed=nx), PAL["brown"], IN_W)
    return c.image()


def build(out, art=False):
    d = os.path.join(out, "ui", "hud") if art else out
    os.makedirs(d, exist_ok=True)
    dials = [("suit_power", PAL["mustard"], "bolt"), ("oxygen", PAL["teal"], "bubbles"), ("gravity", PAL["green"], "apple")]
    parts, imgs = [], []
    for k, (name, col, icon) in enumerate(dials):
        imgs.append(("dial_" + name, dial(name, col, icon, 10 * k + 1), (0.5, 0.5)))
    for k, (name, _c, _i) in enumerate(dials):
        im, pv = needle(100 + k)
        imgs.append(("needle_" + name, im, pv))
    pos, W, H = v3.shelf_pack([(im.shape[1], im.shape[0]) for _n, im, _p in imgs])
    W, H = 1024, 1024                                      # the card's one 1024^2 sheet
    sheet = np.zeros((H, W, 4), np.uint8)
    for (name, im, pv), (x, ytop) in zip(imgs, pos):
        h, w = im.shape[:2]
        sheet[ytop:ytop + h, x:x + w] = im
        parts.append({"name": name, "rect": [x, H - (ytop + h), w, h], "pivot": [round(pv[0], 4), round(pv[1], 4)]})
    meta = {"key": "ui/hud/gauges", "style": "v3", "ppu": v3.PPU, "rect_origin": "bottom_left", "parts": parts,
            "needles": {n: {"dial": "dial_" + n, "needle": "needle_" + n, "hub": [0.5, 0.5],
                            "min_deg": round(math.degrees(SWEEP[0]) - 90, 1), "max_deg": round(math.degrees(SWEEP[1]) - 90, 1),
                            "danger_below": 0.25} for n, _c, _i in dials}}
    files = {"gauges_color.png": sheet, "escape_line_color.png": escape_line(), "escape_sign_color.png": escape_sign()}
    for fn, im in files.items():
        n = pngio.write_png(os.path.join(d, fn), im)
        print(fn, im.shape, n // 1024, "KB")
    with open(os.path.join(d, "gauges.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    for fn, extra in (("escape_line.json", {"tile": True, "tile_x": True, "period_px": 64}),
                      ("escape_sign.json", {"pivot": [0.5, 0.0], "lettering": "pending Patrick Hand (D-090)"})):
        with open(os.path.join(d, fn), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"key": "ui/hud/" + fn[:-5], "style": "v3", "ppu": v3.PPU, **extra}, f, indent=2)
            f.write("\n")
    return files, meta


def review_sheet(out, files, meta_dir=None, out_name="review_b121_hud_preview.png", stamp_paths=()):
    """Compose the HUD at 1080p over the B-114 plains (layers composited 1:1 from their PNGs needs
    bpy; here the plains are regenerated by gen_painted_bg in numpy, same seed)."""
    sys.path.insert(0, os.path.dirname(HERE))
    import gen_painted_bg as B
    import review
    imgs, _l = B.earth_plains(11401)
    Hs, Ws = 1080, 1920
    can = np.zeros((Hs, Ws, 3), np.float32)
    can[:] = imgs[0][0][0, 0]                       # sky colour above layer0's 1024 px
    for (rgb, a), off in zip(imgs, (0, 90, 0)):
        h = rgb.shape[0]
        y0 = Hs - h - off
        can[y0:y0 + h] = rgb[:, :Ws] * a[:, :Ws, None] + can[y0:y0 + h] * (1 - a[:, :Ws, None])
    g = files["gauges_color.png"]
    # dials at half size in the top-left corner, needles composited at 30 / 60 / 90 %
    meta = json.load(open(os.path.join(meta_dir or out, "gauges.json"), encoding="utf-8"))
    parts = {p["name"]: p for p in meta["parts"]}
    for k, (n, frac) in enumerate((("suit_power", 0.3), ("oxygen", 0.6), ("gravity", 0.9))):
        p = parts["dial_" + n]
        x, y, w, h = p["rect"]
        im = g[1024 - (y + h):1024 - y, x:x + w]
        dx, dy = 24 + k * 200, 24
        small = im[::2, ::2]
        review._over(can, np.ascontiguousarray(small), dx, dy)
        q = parts["needle_" + n]
        x, y, w, h = q["rect"]
        nd = g[1024 - (y + h):1024 - y, x:x + w][::2, ::2]
        ang = meta["needles"][n]["min_deg"] + (meta["needles"][n]["max_deg"] - meta["needles"][n]["min_deg"]) * frac
        hh, ww = nd.shape[:2]
        piv = (q["pivot"][0] * ww, (1 - q["pivot"][1]) * hh)
        rot = np.zeros((160, 160, 4), np.uint8)
        yy, xx = np.mgrid[0:160, 0:160] - 80
        a = math.radians(ang)
        sx = xx * math.cos(a) - yy * math.sin(a) + piv[0]
        sy = xx * math.sin(a) + yy * math.cos(a) + piv[1]
        ok = (sx >= 0) & (sx < ww) & (sy >= 0) & (sy < hh)
        rot[ok] = nd[sy[ok].astype(int), sx[ok].astype(int)]
        review._over(can, rot, dx + 80 - 80, dy + 80 - 80)
    line = files["escape_line_color.png"]
    for k in range(3):
        review._over(can, line, 200 + k * 512, Hs - 300)
    review._over(can, files["escape_sign_color.png"], 1500, Hs - 300 - 190)
    review.draw(can, "hud at 1080p over the b-114 plains: suit 30%, oxygen 60%, gravity 90%; escape line + sign (lettering pending)", 8, Hs - 18, (1.0, 0.97, 0.85))
    for i, p in enumerate(stamp_paths):
        review.draw(can, os.path.basename(p) + " " + review.stamp_text(p), 8, 8 + 18 * i, (1.0, 1.0, 0.85))
    review.write(os.path.join(out, out_name), can)


if __name__ == "__main__":
    out = sys.argv[1]
    files, meta = build(out, art="--art" in sys.argv)
    if "--art" not in sys.argv:
        review_sheet(out, files)
        print("review written")
