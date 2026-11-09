"""B-211 (D-174; Bible 5.2 §8.1): the dig run's HUD pieces in B-121's brass-and-paper style (build_hud_v3's Canvas: numpy
fills + jittered ink), Earth palette, no glow, no faces.

  ui/hud/gauge_pack    one 384x320 sheet: dial_pack (320x320, the B-121 dial with its red zone at the TOP end, past 90 %, and
                       a pack icon) + needle_pack (48x150); json parts / needles.pack {"danger_above": 0.9} like gauges.json
  ui/hud/scrip_tag     176x56, slice 60 14 18 14: a paper tag with a brass Scrip coin in its left end (the amount lettered at
                       runtime)
  ui/hud/rank_slot     72x72: a brass ring with a paper centre where the Rank insignia (ui/rank/insignia_<n> at 48 px) sits
  ui/hud/pack_full     256x96: a red-ink rubber stamp "PACK FULL" (Limelight), a little askew, the ink broken in places
  ui/hud/depth_marker  one 140x68 sheet, parts topside / below (68x68 each): a paper roundel - topside: the sun over the dashed
                       Surface Line with its pennant; below: the dashed line overhead, a down chevron into the dirt

  python -I build_hud_d1_v3.py <review png>     the 1080p mock-up: the whole HUD topside, and at 50 m with the pack full
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_hud_v3 as H  # noqa: E402
from meridian import pngio, v3  # noqa: E402

PAL, Canvas, circle, arc, mix, shade = H.PAL, H.Canvas, H.circle, H.arc, H.mix, H.shade


def SH(k):
    """A palette colour's shadow tone (palette-true; B-121's mix() tones are not)."""
    return np.array(v3.hex_rgb(v3.shadow_of(v3.PALETTES["earth"][k], "earth")), np.float32) / 255.0
OUT_W, IN_W, SWEEP = H.OUT_W, H.IN_W, H.SWEEP
ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art")


def pack_dial(seed=41):
    """B-121's dial face, the zone flipped: brown up to 90 %, red past it (the pack's limit), a pack icon under the hub."""
    S = 320
    c = Canvas(S, S)
    cx = cy = S / 2
    c.shape(circle(cx, cy, 150, seed=seed), mix(PAL["brown"], PAL["mustard"], 0.35))
    face = circle(cx, cy, 124, seed=seed + 1)
    c.fill(face, shade(PAL["offwhite"]))
    c.fill(circle(cx - 9, cy - 9, 119, seed=seed + 1), PAL["offwhite"])
    c.ink(face, IN_W, cyclic=True)
    a0, a1 = SWEEP
    split = a0 + (a1 - a0) * 0.9
    c.shape(arc(cx, cy, 108, a0, split, n=40) + arc(cx, cy, 92, split, a0, n=40), PAL["brown"], IN_W)       # the load
    c.shape(arc(cx, cy, 108, split, a1, n=8) + arc(cx, cy, 92, a1, split, n=8), PAL["red"], IN_W)          # past 90 %: red
    for k in range(11):
        a = a0 + (a1 - a0) * k / 10
        r0 = 70 if k % 5 == 0 else 78
        c.ink([(cx + r0 * math.cos(a), cy - r0 * math.sin(a)), (cx + 88 * math.cos(a), cy - 88 * math.sin(a))], IN_W)
    ix, iy = cx, cy + 58                                                                         # the pack icon
    c.shape([(ix - 20, iy - 18), (ix + 20, iy - 18), (ix + 22, iy + 24), (ix - 22, iy + 24)], PAL["brown"], IN_W)
    c.shape([(ix - 21, iy - 20), (ix + 21, iy - 20), (ix + 21, iy - 2)] + arc(ix, iy - 2, 21, 0.0, -math.pi, 10)[1:] + [(ix - 21, iy - 2)],
            PAL["mustard"], IN_W)
    c.shape([(ix - 4, iy + 6), (ix + 4, iy + 6), (ix + 4, iy + 12), (ix - 4, iy + 12)], PAL["offwhite"], IN_W)
    c.ink(arc(ix, iy - 20, 8, math.pi, 0.0, 8), IN_W * 1.4)                                       # its carry loop
    for a in (0.785, 2.356, 3.927, 5.498):
        sx_, sy_ = cx + 137 * math.cos(a), cy + 137 * math.sin(a)
        c.shape(circle(sx_, sy_, 5, n=12, seed=int(a * 10)), mix(PAL["mustard"], PAL["offwhite"], 0.3), IN_W)
        c.ink([(sx_ - 3 * math.cos(a + 1.2), sy_ - 3 * math.sin(a + 1.2)), (sx_ + 3 * math.cos(a + 1.2), sy_ + 3 * math.sin(a + 1.2))], IN_W)
    for j in range(3):
        hx, hy = cx + 70 + 9 * j, cy + 78 - 9 * j
        c.ink([(hx - 7, hy + 7), (hx + 7, hy - 7)], IN_W)
    c.ink(circle(cx, cy, 150, seed=seed), OUT_W, cyclic=True)
    return c.image()


def gauge_pack():
    dial_img = pack_dial()
    needle_img, pv = H.needle(141)
    W_, H_ = 384, 320
    sheet = np.zeros((H_, W_, 4), np.uint8)
    sheet[:, :320] = dial_img
    sheet[H_ - 150:, 324:372] = needle_img
    parts = [{"name": "dial_pack", "rect": [0, 0, 320, 320], "pivot": [0.5, 0.5]},
             {"name": "needle_pack", "rect": [324, 0, 48, 150], "pivot": [round(pv[0], 4), round(pv[1], 4)]}]
    meta = {"rect_origin": "bottom_left", "parts": parts,
            "needles": {"pack": {"dial": "dial_pack", "needle": "needle_pack", "hub": [0.5, 0.5],
                                 "min_deg": round(math.degrees(SWEEP[0]) - 90, 1), "max_deg": round(math.degrees(SWEEP[1]) - 90, 1),
                                 "danger_above": 0.9, "reads": "the pack's kg / its limit"}}}
    return sheet, meta, dial_img, needle_img


def scrip_tag(seed=51):
    W_, H_ = 176, 56
    c = Canvas(W_, H_)
    body = [(14, 28), (28, 8), (W_ - 6, 8), (W_ - 6, H_ - 8), (28, H_ - 8)]
    c.fill(body, PAL["offwhite"])
    c.fill([(20, 38), (W_ - 6, 38), (W_ - 6, H_ - 8), (28, H_ - 8)], shade(PAL["offwhite"]))
    c.ink(body, OUT_W, cyclic=True)
    c.shape(circle(38, 28, 15, n=36, seed=seed), PAL["mustard"], OUT_W)                         # the Scrip coin
    c.fill(circle(38, 28, 10, n=28, seed=seed + 1), shade(PAL["mustard"]))
    star = [(38 + (7 if k % 2 == 0 else 3) * math.cos(-math.pi / 2 + math.pi * k / 5), 28 + (7 if k % 2 == 0 else 3) * math.sin(-math.pi / 2 + math.pi * k / 5))
            for k in range(10)]
    c.shape(star, PAL["mustard"], IN_W)
    return c.image()


def rank_slot(seed=61):
    S = 72
    c = Canvas(S, S)
    cx = cy = S / 2
    c.shape(circle(cx, cy, 31, n=48, seed=seed), SH("mustard"))                                   # (palette brass; inside the margin)
    c.shape(circle(cx, cy, 25, n=44, seed=seed + 1), PAL["offwhite"], IN_W)
    for a in (0.785, 2.356, 3.927, 5.498):
        c.shape(circle(cx + 28 * math.cos(a), cy + 28 * math.sin(a), 2.2, n=10, seed=int(a * 10)), PAL["mustard"], IN_W * 0.8)
    return c.image()


def pack_full(seed=71):
    """The red rubber stamp: a double border and PACK FULL in Limelight, rotated a little, the ink broken (no glow)."""
    import build_ui_v3 as U
    W_, H_ = 256, 96
    yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)
    m0 = np.zeros((H_, W_), np.float32)                                                           # drawn square first
    cu, cv = xx + 0.5 - W_ / 2, yy + 0.5 - H_ / 2
    for half_w, half_h, t in ((110, 33, 4.5), (102, 25, 2.0)):                                   # the double border
        ring = (np.abs(cu) <= half_w) & (np.abs(cv) <= half_h) & ~((np.abs(cu) <= half_w - t) & (np.abs(cv) <= half_h - t))
        m0 = np.maximum(m0, ring.astype(np.float32))
    tm = U.text_mask(U.LIMELIGHT, "PACK  FULL", 30, wobble=0.3, seed=seed)                    # rev: a wider word space, sized to sit
    if tm.shape[1] > 190:                                                                         # inside the inner border (38 px ran
        k = tm.shape[1] / 190.0                                                                   # over it)
        idx_y = np.clip((np.arange(int(tm.shape[0] / k)) * k).astype(int), 0, tm.shape[0] - 1)
        idx_x = np.clip((np.arange(190) * k).astype(int), 0, tm.shape[1] - 1)
        tm = tm[idx_y][:, idx_x]
    th, tw = tm.shape
    y0, x0 = (H_ - th) // 2, (W_ - tw) // 2
    m0[y0:y0 + th, x0:x0 + tw] = np.maximum(m0[y0:y0 + th, x0:x0 + tw], tm)
    ang = math.radians(-6)                                                                        # then turned a little, bilinear
    su = cu * math.cos(ang) + cv * math.sin(ang) + W_ / 2 - 0.5                                   # (nearest sampling broke the
    sv = -cu * math.sin(ang) + cv * math.cos(ang) + H_ / 2 - 0.5                                  # thin letters)
    x_i, y_i = np.floor(su).astype(int), np.floor(sv).astype(int)
    fx, fy = su - x_i, sv - y_i
    pad = np.pad(m0, 1)

    def at(yv, xv):
        return pad[np.clip(yv + 1, 0, H_ + 1), np.clip(xv + 1, 0, W_ + 1)]
    m = (at(y_i, x_i) * (1 - fx) * (1 - fy) + at(y_i, x_i + 1) * fx * (1 - fy) + at(y_i + 1, x_i) * (1 - fx) * fy + at(y_i + 1, x_i + 1) * fx * fy)
    rng = np.random.default_rng(seed)                                                             # the broken ink of a stamp
    speck = rng.random((H_ // 2 + 1, W_ // 2 + 1)) < 0.05                                         # rev: finer, sparser (12 % of 3 px
    holes = np.repeat(np.repeat(speck, 2, 0), 2, 1)[:H_, :W_]                                    # cells ate the letters)
    m = m * np.where(holes, 0.0, 1.0)
    m[:2] = m[-2:] = 0
    m[:, :2] = m[:, -2:] = 0
    out = np.zeros((H_, W_, 4), np.uint8)
    out[..., :3] = np.rint(PAL["red"] * 255)
    out[..., 3] = np.rint(np.clip(m, 0, 1) * 235)
    return out


def depth_marker(state, seed=81):
    S = 68
    c = Canvas(S, S)
    cx = cy = S / 2
    c.shape(circle(cx, cy, 30, n=48, seed=seed), PAL["offwhite"], OUT_W)                         # (inside the 2 px margin)
    if state == "topside":                                                                        # (palette tones only)
        c.fill(arc(cx, cy, 29, math.radians(160), math.radians(20), 20) + [(cx + 27, cy + 4), (cx - 27, cy + 4)], PAL["sky"])
        c.shape(arc(cx - 6, cy + 4, 11, 0.0, math.pi, 12), PAL["mustard"], IN_W)                     # the sun over the line
        c.fill(arc(cx, cy, 29, math.radians(200), math.radians(340), 16), PAL["brown"])
        c.ink([(cx + 12, cy + 4), (cx + 12, cy - 18)], IN_W * 1.4)                                    # the pennant
        c.shape([(cx + 12, cy - 18), (cx + 12, cy - 9), (cx + 24, cy - 13)], PAL["red"], IN_W)
    else:
        c.fill(arc(cx, cy, 29, math.radians(200), math.radians(340), 16) + [(cx + 27, cy - 10), (cx - 27, cy - 10)], PAL["brown"])
        c.fill(arc(cx, cy, 29, math.radians(160), math.radians(20), 20) + [(cx + 27, cy - 10), (cx - 27, cy - 10)], SH("mustard"))
        c.shape([(cx - 9, cy - 2), (cx + 9, cy - 2), (cx, cy + 14)], PAL["mustard"], IN_W)            # the chevron down
    for k in range(5):                                                                            # the dashed Surface Line
        x0 = cx - 26 + 11 * k
        z = cy + 4 if state == "topside" else cy - 10
        c.fill([(x0, z - 2), (x0 + 7, z - 2), (x0 + 7, z + 2), (x0, z + 2)], PAL["offwhite"])
        c.ink([(x0 + 1, z), (x0 + 6, z)], IN_W)
    c.ink(circle(cx, cy, 30, n=48, seed=seed), OUT_W, cyclic=True)
    return c.image()


def depth_sheet():
    a, b = depth_marker("topside"), depth_marker("below", 82)
    sheet = np.zeros((68, 140, 4), np.uint8)
    sheet[:, :68], sheet[:, 72:] = a, b
    return sheet, {"rect_origin": "bottom_left", "parts": [{"name": "topside", "rect": [0, 0, 68, 68], "pivot": [0.5, 0.5]},
                                                           {"name": "below", "rect": [72, 0, 68, 68], "pivot": [0.5, 0.5]}]}


# ---------------------------------------------------------------- the export (on LEAD's OK)
def kit():
    sheet, meta, _d, _n = gauge_pack()
    dm, dmeta = depth_sheet()
    return [("gauge_pack", sheet, {**meta, "note": "B-211: the fourth brass gauge, the pack's kg against its limit; B-121's colours (LEAD: matching the three)"}),
            ("scrip_tag", scrip_tag(), {"slice": [60, 14, 18, 14], "lettering": "runtime", "note": "B-211: the Scrip purse; the amount in Patrick Hand, ink"}),
            ("rank_slot", rank_slot(), {"insignia_px": 48, "note": "B-211: the Rank insignia (ui/rank/insignia_<n>) sits centred in it at 48 px"}),
            ("pack_full", pack_full(), {"note": "B-211: the red-ink stamp shown while the pack is full (no glow)"}),
            ("depth_marker", dm, {**dmeta, "note": "B-211: topside above the Surface Line, below under it (with the depth lettered beside it)"})]


def export(art):
    from meridian import pngio as _png
    built, problems = [], []
    for name, img, extra_meta in kit():
        h, w = img.shape[:2]
        meta = {"key": f"ui/hud/{name}", "style": "v3", "ppu": v3.PPU, "pivot": [0.5, 0.5], "width": w, "height": h, **extra_meta}
        m = v3.EDGE_MARGIN
        if w % 4 or h % 4:
            problems.append(f"{name}: {w}x{h} not a multiple of 4")
        if name != "gauge_pack" and v3.palette_hits(img, "earth")[0] < 0.995:
            problems.append(f"{name}: palette {v3.palette_hits(img, 'earth')[0] * 100:.1f}%")
        if name not in ("gauge_pack", "depth_marker") and (img[:m, :, 3].any() or img[-m:, :, 3].any() or img[:, :m, 3].any() or img[:, -m:, 3].any()):
            problems.append(f"{name}: touches the {m} px edge")
        built.append((meta["key"], img, meta))
    if problems:
        raise ValueError("B-211 HUD checks: " + "; ".join(problems))
    out = []
    for key, img, meta in built:
        base = os.path.join(art, *key.split("/"))
        os.makedirs(os.path.dirname(base), exist_ok=True)
        n = _png.write_png(base + "_color.png", img)
        with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((key, img.shape[1], img.shape[0], n))
    return out


def keys():
    return [f"ui/hud/{n}" for n in ("gauge_pack", "scrip_tag", "rank_slot", "pack_full", "depth_marker")]


# ---------------------------------------------------------------- the 1080p mock-up
def preview(out, footnote=None):
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_ui_v3 as U
    sheet, meta, dial_p, needle_p = gauge_pack()
    tag, slot, stamp = scrip_tag(), rank_slot(), pack_full()
    dm, _dmeta = depth_sheet()
    g = pngio.read_png_np(os.path.join(ART, "ui", "hud", "gauges_color.png"))
    gj = json.load(open(os.path.join(ART, "ui", "hud", "gauges.json"), encoding="utf-8"))

    def part(name):
        for p_ in gj["parts"]:
            if p_["name"] == name:
                x, yb, w, h = p_["rect"]
                return g[g.shape[0] - (yb + h):g.shape[0] - yb, x:x + w], p_["pivot"]
    ins = pngio.read_png_np(os.path.join(ART, "ui", "rank", "insignia_3_color.png"))

    def ov(dst, fr, x, y, s=1.0):
        if s != 1.0:
            k = int(round(1 / s))
            fr = np.rint(fr.astype(np.float32).reshape(fr.shape[0] // k, k, fr.shape[1] // k, k, 4).mean(axis=(1, 3))).astype(np.uint8)
        h, w = fr.shape[:2]
        x, y = int(x), int(y)
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
        f = fr[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32) / 255.0
        a = f[..., 3:4]
        dst[y0:y1, x0:x1] = f[..., :3] * a + dst[y0:y1, x0:x1] * (1 - a)

    def rotated(fr, piv, deg):
        h, w = fr.shape[:2]
        R = int(math.hypot(w, h)) + 2
        o = np.zeros((2 * R, 2 * R, 4), np.uint8)
        yy, xx = np.mgrid[0:2 * R, 0:2 * R]
        a = math.radians(deg)
        px, py = piv[0] * w, (1 - piv[1]) * h
        u = (xx - R) * math.cos(a) + (yy - R) * math.sin(a) + px
        v = -(xx - R) * math.sin(a) + (yy - R) * math.cos(a) + py
        ok = (u >= 0) & (u < w) & (v >= 0) & (v < h)
        o[ok] = fr[v[ok].astype(int), u[ok].astype(int)]
        return o, R

    def gauge(dst, dial_img, needle_img, npiv, value, x, y):
        ov(dst, dial_img, x, y, 0.5)
        deg = (math.degrees(SWEEP[0]) - 90) + ((math.degrees(SWEEP[1]) - 90) - (math.degrees(SWEEP[0]) - 90)) * value
        nimg, R = rotated(needle_img, npiv, -deg)
        ov(dst, nimg[::2, ::2], x + 80 - R // 2, y + 80 - R // 2)

    def lettered(dst, text, x, y, size, font=None, col=None):
        m = U.text_mask(font or U.PATRICK, text, size, wobble=0.2, seed=2)
        c = np.array(v3.hex_rgb(col or v3.INK), np.float32) / 255.0
        sub = dst[y:y + m.shape[0], x:x + m.shape[1]]
        sub[:] = c * m[:sub.shape[0], :sub.shape[1], None] + sub * (1 - m[:sub.shape[0], :sub.shape[1], None])

    def hud(dst, topside, pack_v):
        gauge(dst, *[part("dial_suit_power")[0], part("needle_suit_power")[0], part("needle_suit_power")[1]], 0.8, 30, 900)
        gauge(dst, *[part("dial_oxygen")[0], part("needle_oxygen")[0], part("needle_oxygen")[1]], 0.62 if not topside else 1.0, 200, 900)
        gauge(dst, *[part("dial_gravity")[0], part("needle_gravity")[0], part("needle_gravity")[1]], 0.5, 370, 900)
        gauge(dst, dial_p, needle_p, meta["parts"][1]["pivot"], pack_v, 540, 900)
        t = U.nine_slice(tag, [60, 14, 18, 14], 220, 56)
        ov(dst, t, 30, 30)
        lettered(dst, "1 240", 100, 40, 28)
        ov(dst, slot, 262, 22)
        ov(dst, ins, 274, 34, 0.5)
        ov(dst, dm[:, :68] if topside else dm[:, 72:], 1920 - 100, 26)
        lettered(dst, "topside" if topside else "50 m below", 1920 - 260, 46, 26)
        if pack_v >= 0.95:
            ov(dst, stamp, 960 - 128, 140)

    # topside: the sky, the ground band and fill, the surveyor
    Wd, Hd = 1920, 1080
    top = np.empty((Hd, Wd, 3), np.float32)
    top[:] = np.array(v3.hex_rgb(v3.PALETTES["earth"]["sky"]), np.float32) / 255.0
    E = os.path.join(ART, "terrain", "earth")
    band = pngio.read_png_np(os.path.join(E, "ground_band_color.png"))
    fill = pngio.read_png_np(os.path.join(E, "ground_fill_color.png"))
    gl = 760
    tt = np.tile(fill, (2, 4, 1))[:Hd - gl, :Wd]
    top[gl:] = tt[..., :3].astype(np.float32) / 255.0
    ov(top, np.tile(band, (1, 4, 1))[:, :Wd], 0, gl - 24)
    sv = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))[:192, :192]
    ov(top, sv, 860, gl - 192)
    hud(top, True, 0.35)
    # 50 m below: the Stone tier's fill, a dug pocket, the pack full
    low = np.empty((Hd, Wd, 3), np.float32)
    t3 = pngio.read_png_np(os.path.join(E, "ground_fill_t3_color.png"))
    low[:] = np.tile(t3, (3, 4, 1))[:Hd, :Wd, :3].astype(np.float32) / 255.0
    yy, xx = np.mgrid[0:Hd, 0:Wd]
    pocket = ((xx - 960) / 260.0) ** 2 + ((yy - 640) / 170.0) ** 2 <= 1
    low[pocket] = low[pocket] * 0.35 + np.array((0.16, 0.13, 0.11), np.float32) * 0.65
    ov(low, sv, 860, 800 - 192)
    hud(low, False, 0.97)
    head = np.tile(np.array(review.PAPER, np.float32), (26, Wd, 1))
    review._label(head, "B-211 the D1 HUD at 1080p: topside (pack 35 %) | at 50 m below with the pack full (97 %: past the red line, the PACK FULL stamp)", 6, 6)
    spr = np.tile(np.array(review.PAPER, np.float32), (340, Wd, 1))                               # the new pieces at 2x
    x = 10
    for n, im in (("pack_full", stamp), ("scrip_tag", tag), ("rank_slot", slot), ("depth_marker", dm), ("dial_pack", dial_p)):
        im2 = np.repeat(np.repeat(im, 2, 0), 2, 1) if n != "dial_pack" else im
        ov(spr, im2, x, 24)
        review._label(spr, n + (" (1x)" if n == "dial_pack" else " (2x)"), x, 6, scale=1)
        x += im2.shape[1] + 30
    img = np.vstack([head, top, low, spr])
    lines = []
    for n, im in (("gauge_pack", sheet), ("scrip_tag", tag), ("rank_slot", slot), ("pack_full", stamp), ("depth_marker", dm)):
        hit = v3.palette_hits(im, "earth")[0] * 100
        m = v3.EDGE_MARGIN
        edge = im[:m, :, 3].any() or im[-m:, :, 3].any() or im[:, :m, 3].any() or im[:, -m:, 3].any()
        lines.append(f"ui/hud/{n}: {im.shape[1]}x{im.shape[0]}, palette {hit:.1f}%" + ("; EDGE" if edge else ""))
    foot = np.tile(np.array(review.PAPER, np.float32), (40, Wd, 1))
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6 + (i % 3) * 640, 6 + 16 * (i // 3), scale=1)
    img = np.vstack([img, foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_hud_d1_v3.py <review png>
    preview(sys.argv[1])
