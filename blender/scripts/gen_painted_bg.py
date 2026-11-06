"""Painted watercolour backgrounds + planet palette strips (contract v3.0 §11.4 / §9.1; B-114).

numpy only (no scene, no bpy): run inside render.py or with Blender's bundled python.

backgrounds/<planet>/<scene>: layer0..N_color.png (N+1 parallax layers, 0 = farthest), each
2048 wide (horizontally tileable: every shape and noise is periodic in x), <= 1024 tall,
watercolour: flat washes with low-frequency pigment variation, darker pooled edges, soft
noisy bleeding edges, paper grain; NO ink outline. Plus <scene>.json:
  {"key", "style": "v3", "ppu": 64, "anchor": "bottom",
   "layers": [{"n", "parallax", "y_m", "height_px"}]}
  y_m = world height (m) of the layer's bottom edge relative to the surface line (ground = 0).

ui/palettes/<planet>: strip_color.png, 8x1, the Bible §9.1 colours in strip order, + strip.json.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio, v3  # noqa: E402

W = 2048


def _rgb(h):
    return np.array(v3.hex_rgb(h), np.float32) / 255.0


def _mix(a, b, t):
    return a * (1 - t) + b * t


def periodic_noise(rng, H, sigma_x, sigma_y=None):
    """Gaussian-filtered noise, periodic in x (and y), unit std. sigma in px."""
    sigma_y = sigma_x if sigma_y is None else sigma_y
    w = rng.standard_normal((H, W))
    fy, fx = np.fft.fftfreq(H)[:, None], np.fft.fftfreq(W)[None, :]
    g = np.exp(-2 * np.pi ** 2 * ((sigma_x * fx) ** 2 + (sigma_y * fy) ** 2))
    out = np.real(np.fft.ifft2(np.fft.fft2(w) * g))
    return out / (out.std() + 1e-9)


def blur(a, s):
    """Gaussian blur (px): periodic in x (tiling), edge-padded in y so a layer's solid bottom never
    wraps onto its top row."""
    pad = int(3 * s) + 8
    a = np.pad(a, ((pad, pad), (0, 0)), mode="edge")
    H, Wd = a.shape
    fy, fx = np.fft.fftfreq(H)[:, None], np.fft.fftfreq(Wd)[None, :]
    g = np.exp(-2 * np.pi ** 2 * s * s * (fx ** 2 + fy ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g))[pad:-pad]


def ridge(rng, harmonics, base, amp):
    """A periodic hill line (px from the top) across W: integer harmonics only, so it tiles."""
    x = np.arange(W) / W
    y = np.full(W, float(base))
    for k, a in harmonics:
        y += amp * a * np.sin(2 * np.pi * k * x + rng.uniform(0, 2 * np.pi))
    return y


def wash(rng, H, mask, colour, var=0.05, edge_dark=0.16, bleed=2.5):
    """A watercolour wash of `colour` over the soft `mask` (H x W, 0..1): pigment variation,
    a darker pooled rim, bleeding edges. Returns (rgb, alpha)."""
    n1 = periodic_noise(rng, H, 90, 60)
    n2 = periodic_noise(rng, H, 18)
    edge_noise = periodic_noise(rng, H, 3)
    m = np.clip(blur(mask, bleed) + 0.10 * edge_noise * (blur(mask, bleed) * (1 - blur(mask, bleed)) * 4), 0, 1)
    pool = np.clip(m - blur(m, 12), 0, 1) * 2.5            # just inside the edge: pigment pools darker
    shade = 1 + var * n1 + 0.4 * var * n2 - edge_dark * np.clip(pool, 0, 1)
    rgb = colour[None, None, :] * shade[..., None]
    return np.clip(rgb, 0, 1), m


def paper(rng, H, strength=0.035):
    """Paper grain: fine fibres + a faint tooth, multiplied over everything (periodic)."""
    g = 0.6 * periodic_noise(rng, H, 0.8) + 0.4 * periodic_noise(rng, H, 6, 1.5)
    return 1 + strength * g / 1.0


def _composite(layers):
    rgb = np.zeros(layers[0][0].shape, np.float32)
    a = np.zeros(layers[0][1].shape, np.float32)
    for c, m in layers:
        rgb = c * m[..., None] + rgb * (1 - m[..., None])
        a = m + a * (1 - m)
    return rgb, a


def _ridge_mask(H, line, soft=1.5):
    y = np.arange(H)[:, None] + 0.5
    return np.clip((y - line[None, :]) / soft + 0.5, 0, 1)


def earth_plains(seed):
    """3 layers: far sky + soft clouds + distant teal hills; mid rolling green hills with a few
    tree blobs; near meadow with dabbed grass and flower dots. Earth palette washes."""
    rng = np.random.default_rng(seed)
    pal = {k: _rgb(v) for k, v in v3.PALETTES["earth"].items()}
    out = []

    # layer0: 2048 x 1024, opaque: sky wash lighter toward the horizon, clouds, far hills
    H = 1024
    yy = (np.arange(H) / H)[:, None, None]
    sky = _mix(pal["sky"], _mix(pal["sky"], pal["offwhite"], 0.55), np.clip(yy * 1.2, 0, 1))
    sky = sky * (1 + 0.04 * periodic_noise(rng, H, 140, 80)[..., None])
    sky = np.broadcast_to(sky, (H, W, 3)).copy()
    stack = [(sky, np.ones((H, W), np.float32))]
    cm = np.zeros((H, W), np.float32)
    xs = np.arange(W)[None, :]
    for k in range(7):                                     # soft cloud lumps, wrapped in x
        cx, cy = rng.uniform(0, W), rng.uniform(140, 520)
        for j in range(5):
            px, py = cx + rng.uniform(-150, 150), cy + rng.uniform(-30, 25)
            rx, ry = rng.uniform(70, 150), rng.uniform(35, 60)
            dx = np.minimum(np.abs(xs - px), W - np.abs(xs - px))
            dy = np.arange(H)[:, None] - py
            cm = np.maximum(cm, ((dx / rx) ** 2 + (dy / ry) ** 2 <= 1).astype(np.float32) * (dy < ry * 0.55))
    stack.append(wash(rng, H, cm, pal["offwhite"], var=0.03, edge_dark=0.06, bleed=5.0))
    far = ridge(rng, [(1, 0.5), (3, 0.35), (7, 0.15)], base=820, amp=60)
    stack.append(wash(rng, H, _ridge_mask(H, far), _mix(pal["teal"], pal["sky"], 0.55), var=0.05, edge_dark=0.06, bleed=3.0))
    rgb, a = _composite(stack)
    out.append((rgb * paper(rng, H)[..., None], a))

    # layer1: 2048 x 512, rolling green hills + tree blobs, transparent sky
    H = 512
    hill = ridge(rng, [(2, 0.5), (5, 0.3), (9, 0.12)], base=250, amp=70)
    hm = _ridge_mask(H, hill)
    tm = np.zeros((H, W), np.float32)
    for k in range(9):
        cx = rng.uniform(0, W)
        r = rng.uniform(22, 40)
        cy = hill[int(cx) % W] + r * 0.35
        dx = np.minimum(np.abs(xs - cx), W - np.abs(xs - cx))
        dy = np.arange(H)[:, None] - cy
        tm = np.maximum(tm, ((dx / r) ** 2 + (dy / (r * 1.1)) ** 2 <= 1).astype(np.float32))
    stack = [wash(rng, H, hm, _mix(pal["green"], pal["sky"], 0.30), var=0.06, edge_dark=0.08),
             wash(rng, H, tm, _mix(pal["green"], pal["teal"], 0.45), var=0.07, edge_dark=0.10, bleed=2.0)]
    rgb, a = _composite(stack)
    out.append((rgb * paper(rng, H)[..., None], a))

    # layer2: 2048 x 384, near meadow: deeper green, dabbed grass, mustard and red flower dots
    H = 384
    mead = ridge(rng, [(3, 0.5), (8, 0.25), (16, 0.1)], base=150, amp=35)
    mm = _ridge_mask(H, mead)
    gm = np.zeros((H, W), np.float32)
    for k in range(260):                                   # grass dabs: short soft strokes on the rim
        cx = rng.uniform(0, W)
        top = mead[int(cx) % W]
        cy = top + rng.uniform(-6, 40)
        L, ang = rng.uniform(10, 22), rng.uniform(-0.5, 0.5)
        x0, y0 = int(cx), int(cy)
        for t in np.linspace(0, 1, 8):
            px, py = (cx + math.sin(ang) * L * t) % W, cy - math.cos(ang) * L * t
            gm[max(int(py) - 1, 0):int(py) + 2, int(px) % W] = 1.0
    fm = {"mustard": np.zeros((H, W), np.float32), "red": np.zeros((H, W), np.float32)}
    for k in range(70):
        c = "mustard" if k % 3 else "red"
        cx = rng.uniform(0, W)
        cy = mead[int(cx) % W] + rng.uniform(10, 120)
        r = rng.uniform(3, 6)
        dx = np.minimum(np.abs(xs - cx), W - np.abs(xs - cx))
        dy = np.arange(H)[:, None] - cy
        fm[c] = np.maximum(fm[c], ((dx / r) ** 2 + (dy / r) ** 2 <= 1).astype(np.float32))
    stack = [wash(rng, H, mm, _mix(pal["green"], pal["brown"], 0.12), var=0.07, edge_dark=0.08),
             wash(rng, H, gm * mm.clip(0.0, 1.0) + gm * (1 - mm) * 0.9, _mix(pal["green"], pal["teal"], 0.30), var=0.06, edge_dark=0.05, bleed=1.0),
             wash(rng, H, fm["mustard"] * mm, pal["mustard"], var=0.05, edge_dark=0.10, bleed=1.2),
             wash(rng, H, fm["red"] * mm, pal["red"], var=0.05, edge_dark=0.10, bleed=1.2)]
    rgb, a = _composite(stack)
    out.append((rgb * paper(rng, H)[..., None], a))

    layers = [{"n": 0, "parallax": 0.1, "y_m": -2.0}, {"n": 1, "parallax": 0.35, "y_m": -1.0},
              {"n": 2, "parallax": 0.6, "y_m": -0.5}]
    return out, layers


SCENES = {("earth", "plains"): earth_plains}


def to_u8(rgb, a):
    return np.dstack([pngio.to_u8(np.clip(rgb, 0, 1)), pngio.to_u8(np.clip(a, 0, 1))])


def seam(img):
    """Wrap seam vs interior column step on premultiplied colour (post.seam_score, axis x)."""
    f = img[..., :3].astype(np.float32) * (img[..., 3:4].astype(np.float32) / 255)
    interior = np.abs(np.diff(f, axis=1)).mean()
    return float(np.abs(f[:, -1] - f[:, 0]).mean() / max(interior, 0.5))


def export_background(entry, art):
    _cat, planet, scene = entry["key"].split("/")
    imgs, layers = SCENES[(planet, scene)](int(entry.get("seed", 1)))
    d = os.path.join(art, "backgrounds", planet, scene)
    os.makedirs(d, exist_ok=True)
    info = []
    for (rgb, a), L in zip(imgs, layers):
        img = to_u8(rgb, a)
        H = img.shape[0]
        if H > 1024 or img.shape[1] > 2048:
            raise ValueError(f"layer{L['n']} {img.shape[1]}x{H} over 2048x1024")
        p = os.path.join(d, f"layer{L['n']}_color.png")
        n = pngio.write_png(p, img)
        if n > v3.MAX_FILE_BYTES:
            raise ValueError(f"layer{L['n']} {n / 2**20:.1f} MB over 4 MB")
        L["height_px"] = H
        info.append((p, img, n, seam(img)))
    meta = {"key": entry["key"], "style": "v3", "ppu": v3.PPU, "anchor": "bottom", "tile_x": True, "layers": layers}
    with open(os.path.join(d, f"{scene}.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    return info, meta


def export_palette(entry, art):
    _cat, _g, planet = entry["key"].split("/")
    pal = v3.PALETTES[planet]
    strip = np.array([[list(v3.hex_rgb(pal[k])) + [255] for k in v3.PALETTE_ORDER]], np.uint8)
    d = os.path.join(art, "ui", "palettes", planet)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "strip_color.png")
    pngio.write_png(p, strip)
    with open(os.path.join(d, "strip.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"key": f"ui/palettes/{planet}/strip", "style": "v3", "palette": True,
                   "colors": [{"name": k, "hex": pal[k], "shadow": v3.shadow_of(pal[k], planet) if k != "ink" else None}
                              for k in v3.PALETTE_ORDER]}, f, indent=2)
        f.write("\n")
    return p, strip


if __name__ == "__main__":
    # scripts-only test: write the layers into a scratch folder and print seams
    out = sys.argv[1]
    info, meta = export_background({"key": "backgrounds/earth/plains", "seed": 11401}, out)
    for p, img, n, s in info:
        print(os.path.basename(p), img.shape, n // 1024, "KB", "seam", round(s, 3), "alpha>0", round(float((img[..., 3] > 0).mean()), 3))
    p, strip = export_palette({"key": "ui/palettes/earth"}, out)
    print("strip", strip.shape)
