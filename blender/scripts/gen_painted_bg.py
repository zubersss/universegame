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


def straighten(rgb, a):
    """D-147: a layer composited over a transparent base holds colour x alpha, but the contract (§3) and
    ParallaxLayer.shader read straight alpha, so translucent pixels must have the alpha divided back out (else
    fog reads grey and soft edges get dark rims). Opaque pixels (a >= 0.999) are left exactly as they are, so an
    opaque layer (every layer0) stays byte-identical."""
    a3 = a[..., None]
    fix = (a3 > 1e-4) & (a3 < 0.999)
    return np.where(fix, rgb / np.maximum(a3, 1e-4), rgb).astype(rgb.dtype)


CONTINUE_ROWS = 64                     # D-169: a near layer's bottom strip, vertically tileable, that UNITY repeats below it


def tile_bottom(rgb, a, rows=CONTINUE_ROWS):
    """D-169: make the bottom `rows` rows tile vertically and continue the rows above: strip row k = (1 - k/(rows-1)) x the
    layer's own row k + k/(rows-1) x the row `rows` above it. Row 0 is the layer's own (it follows the painting above), the last
    row equals the row just above the strip, so a copy stacked under the strip joins it as the painting itself does. Every
    feature must keep out of the bottom 2 x rows (or be constant down them), or it ghosts at half strength."""
    H = rgb.shape[0]
    s = (np.arange(rows, dtype=np.float32) / (rows - 1))[:, None]
    lo, up = slice(H - rows, H), slice(H - 2 * rows, H - rows)
    rgb[lo] = rgb[lo] * (1 - s[..., None]) + rgb[up] * s[..., None]
    a[lo] = a[lo] * (1 - s) + a[up] * s
    return rgb, a


def feather_top(rgb, a, rows=48):
    """B-188 (LEAD 12:0x, smoke_42): an opaque layer's top edge (every far sky layer) showed as a hard pale line when it came
    into view with the camera low; fade its top `rows` rows to transparent (smoothstep), the colour kept (straight alpha)."""
    t = np.arange(rows, dtype=np.float32) / (rows - 1)
    a[:rows] = a[:rows] * (t * t * (3 - 2 * t))[:, None]
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
    rgb = straighten(rgb, a)                                  # D-147
    out.append(feather_top(rgb * paper(rng, H)[..., None], a))   # B-188: the sky's top edge feathered

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
    rgb = straighten(rgb, a)                                  # D-147
    out.append((rgb * paper(rng, H)[..., None], a))

    # layer2: 2048 x 480, near meadow: deeper green, dabbed grass, mustard and red flower dots; D-169: 480 tall (was 384), its
    # bottom at 2 m under the line (y_m -2.0), the last 64 rows a vertically tileable meadow strip (continue_rows)
    H = 384 + 96
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
    rgb = straighten(rgb, a)                                  # D-147
    out.append(tile_bottom(rgb * paper(rng, H)[..., None], a))

    layers = [{"n": 0, "parallax": 0.1, "y_m": -2.0}, {"n": 1, "parallax": 0.35, "y_m": -1.0},
              {"n": 2, "parallax": 0.6, "y_m": -2.0, "continue_rows": CONTINUE_ROWS}]   # D-169
    return out, layers


def _star(cx, cy, r, H, rot=0.0):
    """5-point cartoon star polygon mask (wrapped in x and y on the H x W torus)."""
    m = np.zeros((H, W), bool)
    pts = [(cx + r * (1.0 if k % 2 == 0 else 0.45) * math.cos(rot - math.pi / 2 + math.pi * k / 5),
            cy + r * (1.0 if k % 2 == 0 else 0.45) * math.sin(rot - math.pi / 2 + math.pi * k / 5)) for k in range(10)]
    R = int(r) + 3
    ys = np.arange(int(cy) - R, int(cy) + R + 1)
    xs = np.arange(int(cx) - R, int(cx) + R + 1)
    Y, X = np.meshgrid(ys + 0.5, xs + 0.5, indexing="ij")
    inside = np.zeros(Y.shape, bool)
    for i in range(10):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % 10]
        cond = (y0 > Y) != (y1 > Y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = x0 + (Y - y0) * (x1 - x0) / (y1 - y0)
        inside ^= cond & (X < xi)
    m[np.ix_(ys % H, xs % W)] |= inside
    return m


def space_starfield(seed):
    """2048x1024 night sky tiling in x AND y (ArtImporter caps background layers at 1024 tall;
    a 2048x1024 tile repeated vertically covers any view) with soft dabbed stars of three sizes,
    the big ones as inked cartoon stars; plus 3 nebula cards (<= 1024^2, alpha)."""
    rng = np.random.default_rng(seed)
    pal = {k: _rgb(v) for k, v in v3.PALETTES["earth"].items()}
    H = 1024
    night = _mix(pal["ink"], pal["teal"], 0.22)
    sky = np.broadcast_to(night, (H, W, 3)).copy()
    sky *= (1 + 0.10 * periodic_noise(rng, H, 160) + 0.04 * periodic_noise(rng, H, 25))[..., None]
    sky = _mix(sky, _mix(pal["ink"], pal["sky"], 0.18), np.clip(0.25 * periodic_noise(rng, H, 300), 0, 1)[..., None])
    acc = [(sky, np.ones((H, W), np.float32))]
    yy, xx = np.mgrid[0:H, 0:W]
    small = np.zeros((H, W), np.float32)
    for _ in range(450):                                   # tiny specks: 1-2 px soft dabs
        x, y = rng.integers(0, W), rng.integers(0, H)
        small[y, x] = max(small[y, x], rng.uniform(0.35, 0.9))
    small = np.clip(blur_xy(small, 0.6) * 4, 0, 1)
    mid = np.zeros((H, W), np.float32)
    for _ in range(70):                                    # medium: 3-5 px lumpy dots
        cx, cy, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.5, 2.6)
        dx = np.minimum(np.abs(xx - cx), W - np.abs(xx - cx))
        dy = np.minimum(np.abs(yy - cy), H - np.abs(yy - cy))
        sel = (dx < 5) & (dy < 5)
        mid[sel] = np.maximum(mid[sel], np.clip(r + 0.5 - np.hypot(dx[sel], dy[sel]), 0, 1))
    acc.append((np.broadcast_to(_mix(pal["offwhite"], pal["sky"], 0.25), (H, W, 3)), small))
    acc.append((np.broadcast_to(pal["offwhite"], (H, W, 3)), mid))
    big_fill = np.zeros((H, W), bool)
    big_ink = np.zeros((H, W), bool)
    for k in range(11):                                    # big: inked 5-point cartoon stars
        cx, cy, r, rot = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(7, 12), rng.uniform(-0.3, 0.3)
        outer = _star(cx, cy, r + 2.5, H, rot)
        inner = _star(cx, cy, r, H, rot)
        big_ink |= outer
        big_fill |= inner
    big_ink &= ~big_fill
    acc.append((np.broadcast_to(pal["ink"], (H, W, 3)), big_ink.astype(np.float32)))
    acc.append((np.broadcast_to(_mix(pal["mustard"], pal["offwhite"], 0.45), (H, W, 3)), big_fill.astype(np.float32)))
    rgb, a = _composite(acc)
    layers = [(rgb * paper(rng, H)[..., None], a)]
    cards = []
    for k, (c1, c2) in enumerate(((pal["red"], pal["mustard"]), (pal["teal"], pal["sky"]), (pal["mustard"], pal["green"]))):
        N = 1024
        # a soft cloud: blurred blob field, colour mixing across it, alpha <= 0.55, edges bled
        f = np.zeros((N, N), np.float32)
        for j in range(14):
            cx, cy = rng.uniform(260, 764), rng.uniform(280, 744)
            rx, ry = rng.uniform(150, 300), rng.uniform(90, 200)
            f = np.maximum(f, ((((np.arange(N)[None, :] - cx) / rx) ** 2 + ((np.arange(N)[:, None] - cy) / ry) ** 2) <= 1).astype(np.float32))
        f = blur_xy(f, 70)
        f = np.clip((f - 0.05) / 0.6, 0, 1) * (0.8 + 0.2 * np.clip(blur_xy(rng.standard_normal((N, N)).astype(np.float32), 20) * 14, -1, 1))
        edge = 1 - np.clip(np.hypot(np.arange(N)[None, :] - N / 2, np.arange(N)[:, None] - N / 2) / (N * 0.48), 0, 1) ** 4
        alpha = np.clip(f * edge, 0, 1) * 0.55
        mixk = np.clip(blur_xy(rng.standard_normal((N, N)).astype(np.float32), 60) * 8 + 0.5, 0, 1)[..., None]
        col = c1 * (1 - mixk) + c2 * mixk
        col = _mix(col, pal["ink"], 0.35)                  # night-muted
        cards.append((col, alpha))
    return layers, cards


def blur_xy(a, s):
    """Gaussian blur periodic in both axes (any shape)."""
    H_, W_ = a.shape
    fy, fx = np.fft.fftfreq(H_)[:, None], np.fft.fftfreq(W_)[None, :]
    g = np.exp(-2 * np.pi ** 2 * s * s * (fx ** 2 + fy ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g)).astype(np.float32)


def export_space(entry, art):
    """backgrounds/space/starfield (contract §11.4 space, in the key form ArtImporter v13 accepts:
    backgrounds/<planet>/<scene>/layer<N>): layer0 = the starfield 2048x1024 (tiles in x and y),
    layer1..3 = the nebula cards 1024^2, + starfield.json in the SceneLayout schema (n, parallax,
    y_m) with tile flags. Returns ([(path, img, bytes, seam_x, seam_y)], meta)."""
    layers, cards = space_starfield(int(entry.get("seed", 1)))
    d = os.path.join(art, "backgrounds", "space", "starfield")
    os.makedirs(d, exist_ok=True)
    info = []
    img = to_u8(*layers[0])
    p = os.path.join(d, "layer0_color.png")
    n = pngio.write_png(p, img)
    info.append((p, img, n, seam(img), seam(np.ascontiguousarray(img.transpose(1, 0, 2)))))
    for k, (col, al) in enumerate(cards):
        im = to_u8(col, al)
        pk = os.path.join(d, f"layer{k + 1}_color.png")
        nk = pngio.write_png(pk, im)
        info.append((pk, im, nk, None, None))
    for p_, im, n_, _sx, _sy in info:
        if n_ > v3.MAX_FILE_BYTES:
            raise ValueError(f"{os.path.basename(p_)} {n_ / 2**20:.1f} MB over 4 MB")
        if im.shape[0] > 1024 or im.shape[1] > 2048:
            raise ValueError(f"{os.path.basename(p_)} {im.shape[1]}x{im.shape[0]} over the 2048x1024 layer cap")
    meta = {"key": "backgrounds/space/starfield", "style": "v3", "ppu": v3.PPU, "anchor": "center",
            "layers": [{"n": 0, "parallax": 0.05, "y_m": 0.0, "height_px": 1024, "tile": True, "tile_y": True, "role": "starfield"},
                       {"n": 1, "parallax": 0.12, "y_m": 0.0, "height_px": 1024, "tile": False, "role": "nebula"},
                       {"n": 2, "parallax": 0.18, "y_m": 0.0, "height_px": 1024, "tile": False, "role": "nebula"},
                       {"n": 3, "parallax": 0.25, "y_m": 0.0, "height_px": 1024, "tile": False, "role": "nebula"}]}
    with open(os.path.join(d, "starfield.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    return info, meta


SCENES = {("earth", "plains"): earth_plains}


def to_u8(rgb, a):
    return np.dstack([pngio.to_u8(np.clip(rgb, 0, 1)), pngio.to_u8(np.clip(a, 0, 1))])


def seam(img):
    """Wrap seam vs interior column step on premultiplied colour (post.seam_score, axis x)."""
    f = img[..., :3].astype(np.float32) * (img[..., 3:4].astype(np.float32) / 255)
    interior = np.abs(np.diff(f, axis=1)).mean()
    return float(np.abs(f[:, -1] - f[:, 0]).mean() / max(interior, 0.5))


CONTINUE_PLANETS = ("jupiter", "saturn", "uranus", "neptune")          # B-220 (B-201 0.6.0 #1 / #14): the floating-deck scenes,
CONTINUE_KEYS = ("backgrounds/venus/deck",)                          # where the camera drops below the layers' bottoms


def wants_continue(entry):
    """B-220: does this painted row get a tileable bottom band on every layer?"""
    _c, planet, _s = entry["key"].split("/")
    return bool(entry.get("continue_rows")) or planet in CONTINUE_PLANETS or entry["key"] in CONTINUE_KEYS


CONTINUE_MIN_COVER = 0.25         # B-220 rev (11:4x sheets): a band continues only where it is a fill (cloud body, sky, ice pillars)


def band_cover(a, rows=CONTINUE_ROWS):
    """The share of the bottom band's pixels that are solid (alpha > 0.5)."""
    return float((a[-rows:] > 0.5).mean())


def feather_bottom(rgb, a, rows=CONTINUE_ROWS):
    """B-220 rev: a sparse bottom (lightning, the storm ring's haze) fades to transparent over its last `rows` rows (smoothstep)
    instead of repeating - a repeated bolt / streak stacked as slats and dashes under the layer."""
    t = 1.0 - np.arange(rows, dtype=np.float32) / (rows - 1)
    a = a.copy()
    a[-rows:] = a[-rows:] * (t * t * (3 - 2 * t))[:, None]
    return rgb, a


def continue_layer(rgb, a, L):
    """B-220: one layer's bottom for the floating decks. Its own band kept; a fill gets D-169's tileable band (tile_bottom above:
    json continue_rows, UNITY repeats it); a sparse bottom is feathered out and gets no continue_rows. Returns rgb, a, the decision."""
    if "continue_rows" in L:
        return rgb, a, "own band"
    if rgb.shape[0] >= 2 * CONTINUE_ROWS and band_cover(a) >= CONTINUE_MIN_COVER:
        rgb, a = tile_bottom(rgb.copy(), a.copy())
        L["continue_rows"] = CONTINUE_ROWS
        return rgb, a, "continues"
    rgb, a = feather_bottom(rgb, a)
    return rgb, a, "feathered"


def band_seam(rgb, a, rows=CONTINUE_ROWS):
    """The repeat junction (the band's last row -> its first) vs the band's mean row step, on premultiplied colour (< ~1.5 = clean)."""
    f = rgb[-rows:] * a[-rows:, :, None]
    interior = float(np.abs(np.diff(f, axis=0)).mean())
    return float(np.abs(f[-1] - f[0]).mean() / max(interior, 1e-4))


def continue_rows_for(planet):
    """The manifest's painted rows that get B-220's band, for one planet (venus: its deck only)."""
    man = json.load(open(os.path.join(os.path.dirname(HERE), "manifest.json"), encoding="utf-8"))
    rows = man["assets"] if isinstance(man, dict) else man
    return [e for e in rows if e.get("painted_bg") and e["key"].startswith(f"backgrounds/{planet}/") and wants_continue(e)]


def preview_continue(planet, out, footnote=None):
    """B-220's sheet for one planet: every floating-deck scene, each layer at 1/4 as export_background makes it (continue_layer): a
    fill's band repeated 3x below it (the way UNITY will continue it) with its repeat seam and its step from the row above; a sparse
    layer feathered out, nothing under it. One scene in memory at a time."""
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_backdrop_v3 as BB
    q = 4
    paper = np.array(review.PAPER, np.float32)
    rows, lines = [], []
    head = np.tile(paper, (28, 3 * (2048 // q) + 40, 1)).astype(np.float32)
    review._label(head, f"b-220 {planet}: deck layers (1/{q}); a fill's 64-row band repeated 3x below it as UNITY continues it, a sparse layer feathered out", 6, 8)
    rows.append(head)
    for e in continue_rows_for(planet):
        _c, _p, scene = e["key"].split("/")
        fn = SCENES.get((planet, scene)) or BB.SCENES[(planet, scene)]
        imgs, layers = fn(int(e.get("seed", 1)))
        cells = []
        for (rgb, a), L in zip(imgs, layers):
            cover = band_cover(a)
            rgb, a, how = continue_layer(rgb, a, L)
            nb = int(L.get("continue_rows", CONTINUE_ROWS))
            reps = 0 if how == "feathered" else 3
            band_rgb, band_a = rgb[-nb:], a[-nb:]
            stack_rgb = np.vstack([rgb] + [band_rgb] * reps)
            stack_a = np.vstack([a] + [band_a] * reps)
            hh = stack_rgb.shape[0] // q * q
            ww = stack_rgb.shape[1] // q * q
            sr = stack_rgb[:hh, :ww].reshape(hh // q, q, ww // q, q, 3).mean(axis=(1, 3))
            sa = stack_a[:hh, :ww].reshape(hh // q, q, ww // q, q).mean(axis=(1, 3))[..., None]
            cell = np.tile(paper, (sr.shape[0], sr.shape[1], 1)).astype(np.float32)
            cell = sr * sa + cell * (1 - sa)
            y_cut = rgb.shape[0] // q                                                     # mark where the layer ends
            cell[y_cut:y_cut + 1, ::6] = (0.85, 0.2, 0.2)
            cells.append(cell)
            if how == "feathered":
                tail = f", alpha of the last row {float(a[-1].max()):.2f}: ends, no continue_rows"
            else:
                js = band_seam(rgb, a, nb)
                step = float(np.abs(rgb[-nb] * a[-nb, :, None] - rgb[-nb - 1] * a[-nb - 1, :, None]).mean())
                tail = f", repeat seam {js:.2f}, step into the band {step * 255:.1f}/255"
            lines.append(f"{scene} layer{L['n']}: {rgb.shape[1]}x{rgb.shape[0]}, band cover {cover:.2f} -> {how}{tail}")
        del imgs
        Hc = max(c.shape[0] for c in cells)
        r = np.tile(paper, (Hc + 22, 3 * (2048 // q) + 40, 1)).astype(np.float32)
        x = 10
        for c in cells:
            r[20:20 + c.shape[0], x:x + c.shape[1]] = c
            x += c.shape[1] + 10
        review._label(r, f"{e['key']} (seed {e.get('seed')})", 6, 4, scale=1)
        rows.append(r)
    Wd = max(r.shape[1] for r in rows)
    foot = np.tile(paper, (24 + 16 * len(lines), Wd, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack([np.pad(r, ((0, 0), (0, Wd - r.shape[1]), (0, 0)), constant_values=0.9) for r in rows] + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-220 design preview (lock-free, numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


def export_background(entry, art):
    _cat, planet, scene = entry["key"].split("/")
    fn = SCENES.get((planet, scene))
    if fn is None:                       # B-133: the Earth biome sets live in build_backdrop_v3 (same helpers)
        import build_backdrop_v3 as BB
        fn = BB.SCENES[(planet, scene)]
    imgs, layers = fn(int(entry.get("seed", 1)))
    if wants_continue(entry):                                        # B-220: a fill's tileable band, a sparse bottom feathered
        out = []
        for (rgb, a), L in zip(imgs, layers):
            rgb, a, how = continue_layer(rgb, a, L)
            print(f"B-220 {entry['key']} layer{L['n']}: {how}")
            out.append((rgb, a))
        imgs = out
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


if __name__ == "__main__" and len(sys.argv) > 3 and sys.argv[1] == "--continue":   # B-220: python -I gen_painted_bg.py --continue <planet> <png>
    preview_continue(sys.argv[2], sys.argv[3])
elif __name__ == "__main__":
    # scripts-only test: write the layers into a scratch folder and print seams
    out = sys.argv[1]
    info, meta = export_background({"key": "backgrounds/earth/plains", "seed": 11401}, out)
    for p, img, n, s in info:
        print(os.path.basename(p), img.shape, n // 1024, "KB", "seam", round(s, 3), "alpha>0", round(float((img[..., 3] > 0).mean()), 3))
    p, strip = export_palette({"key": "ui/palettes/earth"}, out)
    print("strip", strip.shape)
