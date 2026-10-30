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
    px = _load_resampled(os.path.join(ctx["blender_dir"], entry["input"]), w, h)
    rgb = _wrap_blend(px[..., :3].copy())
    return {"color": _u8(np.dstack([rgb, np.ones((h, w), np.float32)]))}


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
    fn = {"surface": surface, "clouds": clouds, "glow": glow}.get(variant)
    if fn is None:
        raise ValueError(f"gen_planet: no generator for variant '{variant}'")
    return fn(entry, ctx, w, h)
