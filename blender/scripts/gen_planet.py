"""Generator for top-down planet maps (contract §4 `planets/<planet>/`), called by render.py.

Variant by key:
  surface - equirect albedo resampled from `input` (public-domain imagery), opaque, tiles in x
  clouds  - grayscale cloud cover from `input` -> white RGB, alpha = density, tiles in x
  glow    - procedural atmosphere halo, color + emission. The planet disc edge sits at
            `disc_radius` px from the center (default 200 of a 512 sprite), so in game the
            glow sprite's width = 2R * (size / 2) / disc_radius (2.56 R at the defaults).

Manifest fields: `input` (path relative to blender/), `glow_color` (sRGB 0-255),
`glow_peak` (0-1), `glow_width` (px falloff outside the disc), `cloud_gain`, `cloud_floor`.
"""
import os

import numpy as np


def _load_resampled(path, w, h):
    """Raw stored values (sRGB stays sRGB), resampled with Blender's box filter, row 0 = top."""
    import bpy
    img = bpy.data.images.load(path, check_existing=False)
    try:
        img.colorspace_settings.name = "Non-Color"
        img.scale(w, h)
        buf = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(buf)
        return buf.reshape(h, w, 4)[::-1].copy()
    finally:
        bpy.data.images.remove(img)


def _u8(a):
    return np.clip(np.rint(a * 255.0), 0, 255).astype(np.uint8)


def _wrap_blend(rgb, cols=4):
    """Average the outermost columns across the date line so the x seam is invisible after
    resampling (the source wraps; the box filter treats edges as clamped)."""
    seam = 0.5 * (rgb[:, 0] + rgb[:, -1])
    for i in range(cols):
        t = (cols - i) / (cols + 1)          # pull toward the seam value, strongest at the edge
        rgb[:, i] = (1 - t) * rgb[:, i] + t * seam
        rgb[:, -1 - i] = (1 - t) * rgb[:, -1 - i] + t * seam
    return rgb


def surface(entry, ctx, w, h):
    if entry.get("procedural") == "bands":
        return bands(entry, w, h)
    if entry.get("procedural") == "moon":
        return moon(entry, w, h)
    px = _load_resampled(os.path.join(ctx["blender_dir"], entry["input"]), w, h)
    rgb = _wrap_blend(px[..., :3].copy())
    if entry.get("tint"):                              # e.g. grey Mercury basemap -> §9 palette
        rgb = np.clip(rgb * (np.array(entry["tint"], np.float32) / 255.0), 0, 1)
    return {"color": _u8(np.dstack([rgb, np.ones((h, w), np.float32)]))}


def bands(entry, w, h):
    """Procedural banded atmosphere (giants, Venus cloud tops): colour picked by latitude from
    `palette` (list of sRGB stops), with latitude warped by periodic turbulence so the bands
    meander and swirl; optional oval storms `storms` [[lon01, lat01, w01, h01, sRGB], ...].
    Periodic in x by construction (FFT noise over the full width)."""
    from meridian.noise import fft_noise
    rng = np.random.default_rng(int(entry.get("seed", 1)))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    lat = (yy + 0.5) / h                                               # 0 north .. 1 south
    warp = float(entry.get("warp", 0.02))
    turb = (fft_noise(rng, h, w, 40 * w / 2048, 600 * w / 2048, 1.2) * warp
            + fft_noise(rng, h, w, 6 * w / 2048, 60 * w / 2048, 0.6) * warp * 0.25)
    # Zonal shear: turbulence is stretched along x, like real jet streams.
    turb = 0.5 * (turb + np.roll(turb, int(w * 0.01), axis=1))
    t = np.clip(lat + turb, 0, 1)
    pal = np.array(entry["palette"], np.float32) / 255.0
    pos = np.linspace(0, 1, len(pal))
    rgb = np.stack([np.interp(t, pos, pal[:, c]) for c in range(3)], axis=-1)
    detail = fft_noise(rng, h, w, 2 * w / 2048, 20 * w / 2048, 0.4)
    rgb = rgb * (1 + float(entry.get("detail", 0.03)) * detail[..., None])
    for lon, la, ew, eh, col in entry.get("storms", []):
        dx = ((xx / w - lon + 0.5) % 1.0 - 0.5) / ew                   # wraps in longitude
        d = np.sqrt(dx ** 2 + ((lat - la) / eh) ** 2)
        k = np.clip(1.2 - d, 0, 1) ** 1.5
        rgb = rgb * (1 - k[..., None]) + (np.array(col, np.float32) / 255.0) * k[..., None]
    return {"color": _u8(np.dstack([np.clip(rgb, 0, 1), np.ones((h, w), np.float32)]))}


def moon(entry, w, h):
    """Procedural airless moon (Luna): grey highlands, dark maria from thresholded low-frequency
    noise, and craters with dark floors and bright rims/rays. Equirect, periodic in x
    (craters wrap in longitude). Original work, no external input."""
    from meridian.noise import fft_noise
    rng = np.random.default_rng(int(entry.get("seed", 1)))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    hi = np.array(entry.get("highland", [168, 166, 160]), np.float32) / 255.0
    ma = np.array(entry.get("mare", [92, 92, 94]), np.float32) / 255.0
    n = fft_noise(rng, h, w, 40 * w / 512, 300 * w / 512, 1.4)
    mare = np.clip((n - 0.5) * 1.6, 0, 1)
    mare *= np.clip(1.4 - 2.2 * np.abs((yy + 0.5) / h - 0.5), 0, 1)       # maria favour low latitudes
    tex = 1 + 0.06 * fft_noise(rng, h, w, 2, 30 * w / 512, 0.4)
    rgb = (hi * (1 - mare[..., None]) + ma * mare[..., None]) * tex[..., None]
    for _ in range(int(entry.get("craters", 140))):
        cx, cy = rng.random() * w, (0.08 + 0.84 * rng.random()) * h
        r = (1.5 + 14 * rng.random() ** 3) * w / 512
        dx = (xx - cx + w / 2) % w - w / 2
        d = np.hypot(dx * np.cos(np.pi * (cy / h - 0.5)), yy - cy) / r   # less stretched at the poles
        floor = np.clip(1 - d, 0, 1) * 0.12
        rim = np.exp(-((d - 1) / 0.18) ** 2) * 0.16
        rgb = rgb * (1 - floor[..., None]) + rim[..., None] * 0.9
    rgb = _moon_features(entry, rng, rgb, xx, yy, w, h)
    return {"color": _u8(np.dstack([np.clip(rgb, 0, 1), np.ones((h, w), np.float32)]))}


def _moon_features(entry, rng, rgb, xx, yy, w, h):
    """B-070 optional surface features for the giants' moons (all periodic in x):
    `patches` [sRGB, k, wavelength_px]: blotchy terrain (Miranda's coronae, Triton's cantaloupe),
    `cracks` [sRGB, k, count]: long thin curved lineae (Europa), wrapping in longitude,
    `stripes` [sRGB, k, lat01]: a few parallel 'tiger stripes' near one latitude (Enceladus),
    `hotspots` [count, sRGB core, sRGB halo]: volcanic spots with dark centres and coloured
    deposits (Io), `cap` [sRGB, lat01_start, k]: a polar cap from lat01_start to the pole."""
    from meridian.noise import fft_noise, fft_noise_1d
    lat = (yy + 0.5) / h
    if entry.get("patches"):
        col, k, wl = entry["patches"]
        n = fft_noise(rng, h, w, wl * 0.3 * w / 512, wl * w / 512, 1.0)
        m = np.clip((np.abs(n) - 0.5) * 2.5, 0, 1) * k
        rgb = rgb * (1 - m[..., None]) + (np.array(col, np.float32) / 255) * m[..., None]
    if entry.get("cracks"):
        col, k, count = entry["cracks"]
        c = np.array(col, np.float32) / 255
        for _ in range(int(count)):
            y0 = rng.uniform(0.15, 0.85) * h
            amp = rng.uniform(4, 22) * h / 256
            path = y0 + amp * fft_noise_1d(rng, w, w / 3, w, 1.0)          # periodic in x
            tilt = rng.uniform(-0.12, 0.12) * h                             # gentle: lineae cross at varied angles, not as waves
            ph = rng.uniform(0, 2 * np.pi)
            yc = path + tilt * np.sin(2 * np.pi * np.arange(w) / w + ph)
            d = np.abs(yy - yc[None, :])
            m = np.exp(-(d / rng.uniform(0.6, 1.4)) ** 2) * k
            rgb = rgb * (1 - m[..., None]) + c * m[..., None]
    if entry.get("stripes"):
        col, k, la = entry["stripes"]
        c = np.array(col, np.float32) / 255
        for s in range(4):
            yc = (la + 0.025 * s) * h + 2.0 * np.sin(2 * np.pi * (xx / w) * 3 + s)
            m = np.exp(-((yy - yc) / 0.9) ** 2) * k * np.clip(np.sin(np.pi * ((xx / w + 0.1 * s) % 1.0)) * 1.5, 0, 1)
            rgb = rgb * (1 - m[..., None]) + c * m[..., None]
    if entry.get("hotspots"):
        count, core, halo = entry["hotspots"]
        cc, hc = np.array(core, np.float32) / 255, np.array(halo, np.float32) / 255
        for _ in range(int(count)):
            cx, cy = rng.random() * w, (0.12 + 0.76 * rng.random()) * h
            r = rng.uniform(2.0, 6.0) * w / 512
            dx = (xx - cx + w / 2) % w - w / 2
            d = np.hypot(dx, yy - cy) / r
            ring = np.clip(1.6 - d, 0, 1) ** 1.5 * 0.7
            rgb = rgb * (1 - ring[..., None]) + hc * ring[..., None]
            dot = np.clip(1 - d * 1.6, 0, 1)
            rgb = rgb * (1 - dot[..., None]) + cc * dot[..., None]
    if entry.get("cap"):
        col, start, k = entry["cap"]
        m = np.clip((lat - start) / 0.08, 0, 1) * k
        rgb = rgb * (1 - m[..., None]) + (np.array(col, np.float32) / 255) * m[..., None]
    return rgb


# Saturn's rings, radii in units of Saturn's equatorial radius (60,268 km), inner -> outer,
# with optical-depth-like opacity and brightness. A-ring outer edge 2.269 R matches Bible §3
# (radius 96 units, rings to 220).
RINGS = [  # (r_in, r_out, opacity, brightness)
    (1.239, 1.527, 0.18, 0.62),   # C ring: faint, greyish
    (1.527, 1.951, 0.90, 1.00),   # B ring: dense, brightest
    (1.951, 2.027, 0.06, 0.55),   # Cassini Division
    (2.027, 2.214, 0.62, 0.86),   # A ring (inner part)
    (2.214, 2.220, 0.04, 0.5),    # Encke Gap
    (2.220, 2.269, 0.55, 0.84),   # A ring (outer part)
]


def rings(entry, ctx, w, h):
    """Face-on ring system as a transparent annulus. The A-ring outer edge sits at
    `ring_outer` px from the centre (default: half the size minus 12 px of margin), so the
    planet radius R in px = ring_outer / 2.269."""
    from meridian.noise import fft_noise_1d
    rng = np.random.default_rng(int(entry.get("seed", 1)))
    s = w / 1024.0
    outer = float(entry.get("ring_outer", w / 2 - 12 * s))
    R = outer / RINGS[-1][1]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot(xx + 0.5 - w / 2, yy + 0.5 - h / 2) / R               # in Saturn radii
    a = np.zeros((h, w), np.float32)
    b = np.zeros((h, w), np.float32)
    for r0, r1, op, br in RINGS:
        edge = 0.004
        m = np.clip((r - r0) / edge + 0.5, 0, 1) * np.clip((r1 - r) / edge + 0.5, 0, 1)
        a = np.maximum(a, m * op)
        b = np.where(m > 0.5, br, b)
    # Fine ringlets: radial-only 1D noise (rings are circularly symmetric).
    n = 2048
    fine = fft_noise_1d(rng, n, 3, 60, 0.6)
    idx = np.clip((r / RINGS[-1][1] * (n - 1)).astype(int), 0, n - 1)
    a = np.clip(a * (1 + 0.18 * fine[idx]), 0, 1)
    b = np.clip(b * (1 + 0.06 * fine[idx]), 0, 1.2)
    col = np.array(entry.get("ring_color", [214, 196, 160]), np.float32) / 255.0
    rgb = np.clip(col[None, None, :] * b[..., None], 0, 1)
    return {"color": _u8(np.dstack([rgb, a]))}


def clouds(entry, ctx, w, h):
    px = _load_resampled(os.path.join(ctx["blender_dir"], entry["input"]), w, h)
    g = px[..., :3].mean(axis=2)
    floor, gain = float(entry.get("cloud_floor", 0.08)), float(entry.get("cloud_gain", 1.15))
    a = np.clip((g - floor) / (1 - floor) * gain, 0, 1)
    a = _wrap_blend(a[..., None].repeat(3, axis=2))[..., 0]
    rgb = np.ones((h, w, 3), np.float32)
    return {"color": _u8(np.dstack([rgb, a]))}


def glow(entry, ctx, w, h):
    s = w / 512.0
    rd = float(entry.get("disc_radius", 200)) * s
    width = float(entry.get("glow_width", 14)) * s
    peak = float(entry.get("glow_peak", 0.85))
    edge = min(w, h) / 2 - 8 * s                      # contract padding
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot(xx + 0.5 - w / 2, yy + 0.5 - h / 2)
    inner = np.clip((r - 0.8 * rd) / (0.2 * rd), 0, 1)
    inner = inner * inner * (3 - 2 * inner)
    outer = np.exp(-np.maximum(r - rd, 0) / width)
    fade = np.clip((edge - r) / (16 * s), 0, 1)       # reach zero before the margin
    a = peak * np.where(r < rd, inner, outer) * fade
    # B-070 geyser plumes (Enceladus, Triton): jets rising from the limb, `plumes`
    # [[angle_deg (0 = up, clockwise), length_px, width_px, strength], ...].
    for ang, ln, wd, st in entry.get("plumes", []):
        th = np.radians(ang)
        ux, uy = np.sin(th), -np.cos(th)                               # image y points down
        px, py = xx + 0.5 - w / 2, yy + 0.5 - h / 2
        along = px * ux + py * uy - rd                                 # distance out from the limb
        across = -px * uy + py * ux
        spread = wd * s * (0.5 + along / max(ln * s, 1))
        jet = np.exp(-(across / np.maximum(spread, 1)) ** 2) * np.clip(1 - along / (ln * s), 0, 1) * (along > -4 * s)
        a = np.maximum(a, st * jet * fade)
    col = np.array(entry.get("glow_color", [110, 170, 255]), np.float32) / 255.0
    rgb = np.broadcast_to(col, (h, w, 3)).copy()
    color = _u8(np.dstack([rgb, a]))
    emission = _u8(np.dstack([rgb * a[..., None], np.ones((h, w), np.float32)]))
    return {"color": color, "emission": emission}


def generate(entry, ctx):
    w, h = entry["size"]
    if ctx["preview"]:
        w, h = w // 4, h // 4
    variant = entry["key"].split("/")[2]
    fn = {"surface": surface, "clouds": clouds, "glow": glow, "rings": rings}.get(variant)
    if fn is None:
        raise ValueError(f"gen_planet: no generator for variant '{variant}'")
    return fn(entry, ctx, w, h)
