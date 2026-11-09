"""B-221 (B-201 0.6.0 #10: the title menu still showed B-046's v2 render): a v3 title scene, composed from the exported v3 art.

  ui/title/background   1920x1080: Earth's camp at dusk - the Pilgrim (ships/pilgrim/rig, assembled from its side plant) on its
                        landing pad, the smelter and crates, the surveyor; the plains set's forest and meadow bands under a dusk
                        sky wash; the turf (ground_band), the topsoil cutaway (ground_fill) with the dashed Surface Line 2 m down
                        (surface_line) and a dug shaft with a ladder (props/dig/ladder) running down through it. The left third
                        stays calm (sky, far forest, meadow) for the logo and the menu (MenuController's rectangles).

  python -I build_title_v3.py <review png>     the lock-free 1080p preview with the logo / menu rectangles outlined
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio, v3  # noqa: E402

ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
W, H = 1920, 1080
GY = 812                                                   # the turf's surface line on screen (px from the top)
PPU = 64
KEY = "ui/title/background"
MENU_RECTS = [(50, 268, 592, 352), (140, 488, 500, 552), (140, 568, 500, 632), (140, 648, 500, 712), (140, 728, 500, 792)]   # logo, 4 buttons
PAL = {k: np.array(v3.hex_rgb(h), np.float32) / 255.0 for k, h in v3.PALETTES["earth"].items()}


def png(*parts):
    return pngio.read_png_np(os.path.join(ART, *parts)).astype(np.float32) / 255.0


def over(dst, src, x, y):
    """Straight-alpha RGBA src over an RGB float dst, top-left at (x, y), clipped."""
    h, w = src.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4]
    dst[y0:y1, x0:x1] = s[..., :3] * a + dst[y0:y1, x0:x1] * (1 - a)


def tile_x(img, width):
    reps = -(-width // img.shape[1]) + 1
    return np.tile(img, (1, reps, 1))[:, :width]


def frame(sheet_rel, json_rel, i=0):
    m = json.load(open(os.path.join(ART, *json_rel.split("/")), encoding="utf-8"))
    s = png(*sheet_rel.split("/"))
    fw, fh, cols, g = m["frame_width"], m["frame_height"], m["columns"], m.get("gutter", 4)
    r, c = divmod(i, cols)
    return s[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw], m


def pilgrim():
    """The Pilgrim assembled at rest from ships/pilgrim/rig's side plant -> (RGBA, the root's ground point in px within it)."""
    m = json.load(open(os.path.join(ART, "ships", "pilgrim", "rig.json"), encoding="utf-8"))
    sheet = png("ships", "pilgrim", "rig_color.png")
    SH = sheet.shape[0]
    parts = {p["name"]: p for p in m["parts"]}
    plant = next(p for p in m["plants"] if p["name"] == "pilgrim_side")
    root = next(b for b in plant["bones"] if b["parent"] is None)
    items = []
    for b in plant["bones"]:
        off = root["offset_m"] if b is root else [root["offset_m"][0] + b["offset_m"][0], root["offset_m"][1] + b["offset_m"][1]]
        items.append((b["order"], b["part"], off))
    for s in plant.get("slots", []):
        part = plant["swaps"][s["slot"]][0]
        items.append((s["order"], part, [root["offset_m"][0] + s["offset_m"][0], root["offset_m"][1] + s["offset_m"][1]]))
    C = 900                                                                                   # a canvas 900 px round the ground point
    canvas = np.zeros((C, C, 4), np.float32)
    gx, gy = C // 2, C - 40
    for _o, name, (mx, mz) in sorted(items, key=lambda t: t[0]):
        p = parts[name]
        x, y, w, h = p["rect"]                                                                # bottom-left origin in the sheet
        img = sheet[SH - y - h:SH - y, x:x + w]
        px, py = p["pivot"]
        ax, ay = gx + mx * PPU, gy - mz * PPU                                                 # the pivot's place on the canvas
        sub = canvas
        X, Y = int(round(ax - px * w)), int(round(ay - (1 - py) * h))
        hh, ww = img.shape[:2]
        x0, y0, x1, y1 = max(X, 0), max(Y, 0), min(X + ww, C), min(Y + hh, C)
        s = img[y0 - Y:y1 - Y, x0 - X:x1 - X]
        a = s[..., 3:4]
        sub[y0:y1, x0:x1, :3] = s[..., :3] * a + sub[y0:y1, x0:x1, :3] * (1 - a)
        sub[y0:y1, x0:x1, 3:4] = a + sub[y0:y1, x0:x1, 3:4] * (1 - a)
    return canvas, (gx, gy)


def dusk_sky(sky):
    """The plains set's layer0 graded to dusk: deeper blue overhead, a warm mustard / rose band toward the horizon (painted, so the
    wash mixes palette tones like the backdrops do)."""
    h = sky.shape[0]
    t = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    deep = PAL["sky"] * 0.62 + PAL["brown"] * 0.18
    warm = PAL["mustard"] * 0.55 + PAL["red"] * 0.25 + PAL["offwhite"] * 0.2
    grade = deep * (1 - t) ** 1.4 + warm * (1 - (1 - t) ** 1.4)
    out = sky.copy()
    out[..., :3] = sky[..., :3] * 0.35 + grade * 0.65
    return out


def compose():
    img = np.empty((H, W, 3), np.float32)
    meta = json.load(open(os.path.join(ART, "backgrounds", "earth", "plains", "plains.json"), encoding="utf-8"))
    for L in meta["layers"]:                                                                 # the plains set, bottom-anchored at the turf
        lay = png("backgrounds", "earth", "plains", f"layer{L['n']}_color.png")
        if L["n"] == 0:
            lay = dusk_sky(lay)
            band = tile_x(lay, W)
            ys = np.clip(np.arange(H) * band.shape[0] // H, 0, band.shape[0] - 1)
            img[:] = band[ys][..., :3]                                                       # the sky fills the frame
            continue
        lay = lay.copy()
        lay[..., :3] = lay[..., :3] * 0.82 + (PAL["red"] * 0.25 + PAL["mustard"] * 0.75) * 0.18   # a touch of dusk light on the land
        band = tile_x(lay, W)
        bottom = GY - int(round(L.get("y_m", 0.0) * PPU))
        over(img, band, 0, bottom - band.shape[0])
    fill = png("terrain", "earth", "ground_fill_color.png")                                  # the topsoil cutaway
    ft = np.tile(fill, (2, 5, 1))[:H - GY, :W]
    img[GY:] = ft[..., :3] * ft[..., 3:4] + img[GY:] * (1 - ft[..., 3:4])
    sl = png("terrain", "earth", "surface_line_color.png")                                   # the Surface Line, 2 m down (its line on row 40)
    over(img, tile_x(sl, W), 0, GY + 2 * PPU - 40)
    bandf, bm = frame("terrain/earth/ground_band_color.png", "terrain/earth/ground_band.json")
    row = bm.get("surface_row", 24)
    over(img, tile_x(bandf, W), 0, GY - row)                                                 # the turf
    # the dug shaft, down through the Surface Line, a ladder in it
    sx0, sx1 = 1660, 1736
    shaft = np.zeros((H - GY + 6, sx1 - sx0 + 8, 4), np.float32)
    shaft[:, 4:-4, :3] = PAL["brown"] * 0.55
    shaft[:, 4:-4, 3] = 1.0
    shaft[:, :4, :3] = v3.hex_rgb(v3.INK)[0] / 255.0
    shaft[:, :4, 3] = 1.0
    shaft[:, -4:, :3] = v3.hex_rgb(v3.INK)[0] / 255.0
    shaft[:, -4:, 3] = 1.0
    over(img, shaft, sx0 - 4, GY - 4)
    lad = png("props", "dig", "ladder_color.png")
    for y in range(GY - 32, H, lad.shape[0]):
        over(img, lad, (sx0 + sx1) // 2 - lad.shape[1] // 2, y)
    top = png("props", "dig", "ladder_top_color.png")
    over(img, top, (sx0 + sx1) // 2 - top.shape[1] // 2, GY - top.shape[0] + 6)
    # the camp: the pad and the Pilgrim, the smelter and the crates, the surveyor
    pad = png("props", "common", "landing_pad_color.png")
    rocket, (rgx, rgy) = pilgrim()
    RX = 1170
    over(img, pad, RX - pad.shape[1] // 2, GY - pad.shape[0] + 10)
    over(img, rocket, RX - rgx, GY - 8 - rgy)
    smelter = png("props", "common", "smelter_color.png")
    over(img, smelter, 1440, GY - smelter.shape[0] + 6)
    crate = png("props", "common", "storage_crate_color.png")
    for x, y in ((1530, 0), (1584, 0), (1556, 1)):
        over(img, crate, x, GY - crate.shape[0] * (y + 1) + 4)
    surv, sm = frame("characters/surveyor/side_color.png", "characters/surveyor/side.json", 0)
    over(img, surv, 1610 - sm["frame_width"] // 2, GY - sm["frame_height"] + int(round(sm["pivot"][1] * sm["frame_height"])) + 2)
    return np.clip(img, 0.0, 1.0)


def export(art):
    img = compose()
    u8 = np.dstack([np.rint(img * 255).astype(np.uint8), np.full((H, W), 255, np.uint8)])
    base = os.path.join(art, *KEY.split("/"))
    n = pngio.write_png(base + "_color.png", u8)
    meta = {"key": KEY, "style": "v3", "width": W, "height": H, "palette": "earth",
            "note": "B-221: the title scene - Earth's camp at dusk (the Pilgrim on its pad, the camp, the surveyor; the plains set; the turf, "
                    "the topsoil cutaway with the Surface Line and a dug shaft with a ladder); the left third clear for the logo and the menu"}
    with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    return [(KEY, W, H, n)]


def keys():
    return [KEY]


def preview(out, footnote=None):
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    img = compose()
    for i, (x0, y0, x1, y1) in enumerate(MENU_RECTS):                                         # the logo / menu rectangles, outlined
        col = np.array([0.85, 0.2, 0.2], np.float32)
        img[y0:y0 + 3, x0:x1] = col
        img[y1 - 3:y1, x0:x1] = col
        img[y0:y1, x0:x0 + 3] = col
        img[y0:y1, x1 - 3:x1] = col
        review._label(img, "logo" if i == 0 else f"menu {i}", x0 + 6, y0 + 6, scale=1)
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-221 design preview (the logo / menu rectangles outlined)"), 2, H - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, W, "x", H)


if __name__ == "__main__":                       # python -I build_title_v3.py <review png>
    preview(sys.argv[1])
