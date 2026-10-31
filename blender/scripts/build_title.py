"""Title art (B-046) and app icon (B-047), called by render.py as a generator (2D, numpy).

ui/title/background  1920x1080 key art composed from the game's own exported art (no new
                     scene): Earth sky + forest parallax layers re-graded to dawn, the Pilgrim
                     (side, legs deployed) lifting off a run of landing-pad modules with its
                     belly thrusters lit and pad dust, Mars a rust dot in the sky; the left third
                     darkened and kept calm for the menu buttons.
ui/title/logo        MERIDIAN wordmark from hand-built letterforms (signed-distance strokes; no
                     font file, so no licence to credit beyond our own), cream with a dark edge,
                     crossed by a thin orange "meridian line".
"""
import json
import math
import os

import numpy as np

from meridian import pngio

ART = None


def load(rel):
    return pngio.read_png(os.path.join(ART, rel))


def resize(img, w, h):
    """Bilinear resize of an HxWxC float image."""
    H, W = img.shape[:2]
    ys = (np.arange(h) + 0.5) * H / h - 0.5
    xs = (np.arange(w) + 0.5) * W / w - 0.5
    y0 = np.clip(np.floor(ys).astype(int), 0, H - 1); y1 = np.clip(y0 + 1, 0, H - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, W - 1); x1 = np.clip(x0 + 1, 0, W - 1)
    fy = np.clip(ys - y0, 0, 1)[:, None, None]; fx = np.clip(xs - x0, 0, 1)[None, :, None]
    a = img[y0][:, x0]; b = img[y0][:, x1]; c = img[y1][:, x0]; d = img[y1][:, x1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def over(dst, src, x, y, alpha_k=1.0):
    """Alpha-composite RGBA `src` onto RGB `dst` with its top-left at (x, y); clipped."""
    H, W = dst.shape[:2]
    h, w = src.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4] * alpha_k
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a


def add(dst, src, x, y, k=1.0):
    H, W = dst.shape[:2]
    h, w = src.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 > x0 and y1 > y0:
        s = src[y0 - y:y1 - y, x0 - x:x1 - x]
        dst[y0:y1, x0:x1] = np.clip(dst[y0:y1, x0:x1] + s[..., :3] * s[..., 3:4] * k, 0, 1)   # premultiplied


def frame(sheet_rel, idx):
    meta = json.load(open(os.path.join(ART, sheet_rel + ".json"), encoding="utf-8"))
    img = load(sheet_rel + "_color.png")
    fw, fh, cols, g = meta["frame_width"], meta["frame_height"], meta["columns"], meta["gutter"]
    r, c = divmod(idx, cols)
    out = img[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw].copy()
    ep = os.path.join(ART, sheet_rel + "_emission.png")
    if os.path.exists(ep):
        e = pngio.read_png(ep)[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw]
        out[..., :3] = np.clip(out[..., :3] + e[..., :3] * 0.8, 0, 1)
    return out


def _blob_index(mask):
    """Sheet index of a reduced 8-neighbour mask, as BlobAutotile.cs (canonical masks ascending)."""
    def reduce(m):
        if not (m & 1 and m & 4): m &= ~2
        if not (m & 16 and m & 4): m &= ~8
        if not (m & 16 and m & 64): m &= ~32
        if not (m & 1 and m & 64): m &= ~128
        return m
    canon = [m for m in range(256) if reduce(m) == m]
    return canon.index(reduce(mask))


def tile(rel, mask, size):
    """One 128 px terrain tile (8 columns, no gutters), resized to `size`."""
    sheet = load(rel)
    i = _blob_index(mask)
    r, c = divmod(i, 8)
    return resize(sheet[r * 128:(r + 1) * 128, c * 128:(c + 1) * 128], size, size)


def background(W=1920, H=1080):
    def cover(rel):                                  # scale a 2048x1024 layer to cover the frame
        img = load(rel)
        s = H / img.shape[0]
        w = int(round(img.shape[1] * s))
        r = resize(img, w, H)
        x = (w - W) // 2 + 60
        return r[:, x:x + W]
    sky = cover("backgrounds/earth/layer0_color.png")[..., :3]
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    # Dawn: deep violet-blue top, rose-orange horizon (re-grade, then pull toward the dawn hues).
    lum = sky.mean(axis=2, keepdims=True)
    t = np.clip((yy - 0.05) / 0.6, 0, 1)
    hue = (1 - t) * np.array([0.22, 0.24, 0.48]) + t * np.array([1.0, 0.62, 0.42])
    out = np.clip(lum * 1.15 * hue + sky * 0.25, 0, 1)
    xx = np.arange(W, dtype=np.float32)[None, :]
    yv = np.arange(H, dtype=np.float32)[:, None]
    sun = np.exp(-(((xx - 0.86 * W) / 260) ** 2 + ((yv - 0.6 * H) / 150) ** 2))[..., None]
    out = np.clip(out + sun * np.array([0.55, 0.32, 0.12]), 0, 1)
    mars = np.exp(-(((xx - 0.8 * W) ** 2 + (yv - 0.15 * H) ** 2) / 6.0 ** 2))[..., None]
    halo = np.exp(-(((xx - 0.8 * W) ** 2 + (yv - 0.15 * H) ** 2) / 22.0 ** 2))[..., None]
    out = np.clip(out * (1 - mars) + mars * np.array([0.82, 0.38, 0.2]) + halo * np.array([0.08, 0.03, 0.01]), 0, 1)
    warm = np.array([0.86, 0.76, 0.7])                                  # low dawn light on the land
    # B-046 v2: dawn on the foliage. Sunward (right) side warms toward rose/amber, the shadow
    # side and dark values cool toward blue-violet (a flat multiply left it midday green).
    side = np.clip(xx / W, 0, 1)[..., None]
    sun_tint = (1 - side) * np.array([0.72, 0.74, 0.92]) + side * np.array([1.18, 0.86, 0.66])
    for rel in ("backgrounds/earth/layer1_color.png", "backgrounds/earth/layer2_color.png"):
        lay = cover(rel)
        c = lay[..., :3]
        lum = c.mean(axis=2, keepdims=True)
        shadow = np.clip((0.32 - lum) / 0.32, 0, 1)
        c = c * sun_tint
        c = c * (1 - 0.45 * shadow) + np.array([0.16, 0.16, 0.3]) * 0.45 * shadow
        g = c.mean(axis=2, keepdims=True)                                   # pull green saturation down
        lay[..., :3] = np.clip(g + (c - g) * 0.72, 0, 1)
        over(out, lay, 0, 0)
    # Pad: four landing-pad modules in a row; the Pilgrim lifting off above it.
    s = 0.5
    pad = load("props/common/landing_pad_color.png")
    pad = resize(pad, int(pad.shape[1] * s), int(pad.shape[0] * s))
    cx = int(W * 0.64)
    pw = pad.shape[1]
    ship = load("ships/pilgrim/side_legs_color.png")
    em = load("ships/pilgrim/side_legs_emission.png")
    ship[..., :3] = np.clip(ship[..., :3] * warm + em[..., :3] * 0.8, 0, 1)
    sw, sh = int(ship.shape[1] * s), int(ship.shape[0] * s)
    ship = resize(ship, sw, sh)
    lift = 110
    sx, sy = cx - sw // 2, int(H * 0.46)
    # B-046 v2: the real landing-pad art (deck on legs) at a readable scale, three modules,
    # standing on a short strip of grass-topped soil built from the Earth terrain tiles.
    big = load("props/common/landing_pad_color.png")
    ps = 0.8
    pad = resize(big, int(big.shape[1] * ps), int(big.shape[0] * ps))
    pw = pad.shape[1]
    ground = sy + int(sh * 0.93) + lift + int(pad.shape[0] * (1 - 0.138889))   # pad deck under the skids
    ts = 64
    n = (3 * pw) // ts + 3
    x0 = cx - n * ts // 2
    for k in range(n):
        top_mask = 4 | 8 | 16 | 32 | 64                                   # E SE S SW W (grass top)
        soil_mask = 255
        if k == 0:
            top_mask, soil_mask = 4 | 8 | 16, 1 | 2 | 4 | 8 | 16
        elif k == n - 1:
            top_mask, soil_mask = 16 | 32 | 64, 1 | 16 | 32 | 64 | 128
        over(out, tile("terrain/earth/grass_color.png", top_mask, ts), x0 + k * ts, ground)
        for row in (1, 2, 3):
            over(out, tile("terrain/earth/soil_color.png", soil_mask, ts), x0 + k * ts, ground + row * ts)
    for k in range(3):
        over(out, pad, cx - 3 * pw // 2 + k * pw, ground - int(pad.shape[0] * (1 - 0.138889)))
    # Belly thrusters (pods at ~0.25 and ~0.69 of the ship length, pod bottoms ~0.82 of height).
    flame = frame("fx/thruster/base", 2)
    fs = 0.85
    flame = resize(flame, int(flame.shape[1] * fs), int(flame.shape[0] * fs))
    for px in (0.25, 0.69):
        fx = sx + int(sw * px) - flame.shape[1] // 2
        fy = sy + int(sh * 0.8)
        add(out, flame, fx, fy, 0.9)
    dust = frame("fx/dust/base", 5)
    dust = resize(dust, int(dust.shape[1] * 2.6), int(dust.shape[0] * 2.6))
    for px in (0.2, 0.32, 0.64, 0.76):
        over(out, dust, sx + int(sw * px) - dust.shape[1] // 2, ground - dust.shape[0] + 10, 0.55)
    over(out, ship, sx, sy)
    # Left third calm for the menu: a soft dark gradient.
    lg = np.clip(1 - xx / (0.48 * W), 0, 1)[..., None] ** 0.9           # B-046 v2: visibly darker
    out = out * (1 - 0.68 * lg) + np.array([0.04, 0.04, 0.08]) * 0.68 * lg
    return out


# ---------------------------------------------------------------- wordmark

def _seg(px, py, a, b):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = max(dx * dx + dy * dy, 1e-9)
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0, 1)
    return np.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _arc(cx, cy, r, a0, a1, n=14):
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


GLYPHS = {                                            # polylines in a cell (x 0..w, y 0..1, y up)
    "M": (1.0, [[(0, 0), (0, 1), (0.5, 0.42), (1, 1), (1, 0)]]),
    "E": (0.8, [[(0.8, 1), (0, 1), (0, 0), (0.8, 0)], [(0, 0.5), (0.66, 0.5)]]),
    "R": (0.86, [[(0, 0), (0, 1), (0.55, 1)] + _arc(0.55, 0.75, 0.25, math.pi / 2, -math.pi / 2) + [(0, 0.5)],
                 [(0.4, 0.5), (0.86, 0)]]),
    "I": (0.0, [[(0, 0), (0, 1)]]),
    "D": (0.9, [[(0.4, 0), (0, 0), (0, 1), (0.4, 1)] + _arc(0.4, 0.5, 0.5, math.pi / 2, -math.pi / 2)]),
    "A": (1.0, [[(0, 0), (0.5, 1), (1, 0)], [(0.22, 0.36), (0.78, 0.36)]]),
    "N": (0.86, [[(0, 0), (0, 1), (0.86, 0), (0.86, 1)]]),
}


def logo(W=1280, H=320):
    """MERIDIAN in hand-built geometric strokes; cream fill, dark edge, orange meridian line."""
    text = "MERIDIAN"
    cap = 200.0                                       # letter height px
    th = 0.13                                         # stroke half-width in cap units... (scaled below)
    gap = 0.34
    widths = [GLYPHS[c][0] for c in text]
    total = sum(widths) + gap * (len(text) - 1)
    scale = min(cap, (W - 80) / total)                # fit the canvas (first pass clipped M and N)
    cap = scale
    x = (W - total * scale) / 2
    base = (H + cap) / 2
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.full((H, W), 1e9, np.float32)
    for c, w in zip(text, widths):
        for poly in GLYPHS[c][1]:
            pts = [(x + px * scale, base - py * scale) for px, py in poly]
            for a, b in zip(pts, pts[1:]):
                d = np.minimum(d, _seg(xx, yy, a, b))
        x += (w + gap) * scale
    half = th * scale / 2
    fill = np.clip(half - d + 0.75, 0, 1)
    edge = np.clip(half + 5 - d + 0.75, 0, 1)
    # Meridian line: thin orange line through the word at 46% cap height, tapering at both ends.
    ly = base - 0.46 * cap
    span = total * scale / 2 + 90
    lx = np.abs(xx - W / 2) / span
    line = np.clip(2.6 - np.abs(yy - ly), 0, 1) * np.clip((1 - lx) * 6, 0, 1) * (lx < 1)
    top = np.clip((base - yy) / cap, 0, 1)[..., None]
    cream = np.array([0.96, 0.92, 0.82]) * (0.92 + 0.08 * top)
    rgb = np.zeros((H, W, 3), np.float32) + np.array([0.06, 0.06, 0.08])
    rgb = rgb * (1 - line[..., None]) + np.array([0.92, 0.48, 0.2]) * line[..., None]
    rgb = rgb * (1 - fill[..., None]) + cream * fill[..., None]
    a = np.clip(np.maximum(edge * 0.85, line), 0, 1)
    a = np.maximum(a, fill)
    return np.dstack([rgb, a])


def generate(entry, ctx):
    global ART
    ART = os.path.normpath(os.path.join(ctx["root"], "Assets", "_Game", "Art"))
    name = entry["key"].split("/", 1)[1]
    if name == "title/background":
        rgb = background(*entry["size"])
        out = np.dstack([pngio.to_u8(rgb), np.full(rgb.shape[:2], 255, np.uint8)])
    elif name == "title/logo":
        img = logo(*entry["size"])
        out = np.dstack([pngio.to_u8(img[..., :3]), pngio.to_u8(img[..., 3])])
    else:
        raise ValueError(entry["key"])
    if ctx["preview"]:
        out = out[::4, ::4]
    return {"color": out}
