"""Contract v2 terrain block materials (§9 terrain row, B-080): per tile material a tileable
`top` and `side` PBR set at 512^2 with 2 m per repeat (256 px/m), plus the planet's back wall.

Writes Assets/_Game/Art/terrain/<planet>/<material>/{top,side}_{color,normal,mask}.png and
terrain/<planet>/backwall_{color,normal,mask}.png; mask = (R metallic, G ambient occlusion,
B rim, A smoothness). Derived from the v1 recipes in gen_terrain.py: the recipes run on a
512 px period with every noise wavelength doubled, so features keep their real size (v1 was
128 px per 1 m tile, here 256 px/m). Pure numpy; called by render.py for "terrain3d" entries.

Manifest fields per entry: key terrain/<planet>/<material> (or .../backwall), `top` and `side`
recipe dicts (same fields as gen_terrain entries: recipe, dark, light, ...), `smooth`
(smoothness 0-1), `normal_strength`.
"""
import os

import numpy as np

import gen_terrain as GT
from meridian import pngio
from meridian.noise import fft_noise as _fft_noise

N = 512
SCALE = 2.0                       # 256 px/m vs v1's 128 px/m


def _scaled_noise(rng, h, w, lo, hi, slope=1.0):
    return _fft_noise(rng, h, w, lo * SCALE, hi * SCALE, slope)


def _recipe(spec, seed):
    """Run a v1 recipe on a 512 px period with doubled wavelengths."""
    old_T, old_fft = GT.T, GT.fft_noise
    GT.T, GT.fft_noise = N, _scaled_noise
    try:
        col, h = GT.RECIPES[spec["recipe"]](np.random.default_rng(seed), spec)
    finally:
        GT.T, GT.fft_noise = old_T, old_fft
    return np.clip(col, 0, 1).astype(np.float32), (h * SCALE).astype(np.float32)


def _strata(col, h, spec, seed):
    """Side faces of layered materials (sand, snow, soil): soft horizontal bands that tile
    (band period divides 512)."""
    if not spec.get("strata"):
        return col, h
    k, period = spec["strata"]
    rng = np.random.default_rng(seed + 7)
    yy = np.arange(N, dtype=np.float32)[:, None]
    wob = _scaled_noise(rng, 1, N, 30, 256, 1.0)[0][None, :] * 3.0
    band = 0.5 + 0.5 * np.sin(2 * np.pi * (yy + wob) / period)
    col = col * (1 - k * 0.35 * band[..., None]) + col * k * 0.15
    return np.clip(col, 0, 1), h - 1.5 * band


def _mask(h, smooth, metal=0.0):
    """G = cavity AO from the height field (blurred difference), A = smoothness."""
    blur = h.copy()
    for _ in range(6):
        blur = 0.2 * (blur + np.roll(blur, 1, 0) + np.roll(blur, -1, 0) + np.roll(blur, 1, 1) + np.roll(blur, -1, 1))
    ao = np.clip(1.0 + 0.12 * (h - blur), 0.55, 1.0)
    return np.dstack([np.full(h.shape, metal, np.float32), ao, np.zeros(h.shape, np.float32),
                      np.full(h.shape, smooth, np.float32)])


def _normal(h, strength):
    n = GT.normals_from_height(h, np.zeros_like(h), strength)
    return n * 0.5 + 0.5


def _write(path, rgb_or_rgba):
    a = rgb_or_rgba
    if a.shape[2] == 3:
        a = np.dstack([a, np.ones(a.shape[:2], np.float32)])
    pngio.write_png(path, pngio.to_u8(np.clip(a, 0, 1)))


def make_face(spec, seed, smooth, strength):
    col, h = _recipe(spec, seed)
    col, h = _strata(col, h, spec, seed)
    return {"color": col, "normal": _normal(h, strength), "mask": _mask(h, smooth)}


def seam_score(img):
    """Mean |wrap step| over the mean interior step, both axes (1.0 = invisible seam)."""
    a = img[..., :3]
    inner = np.abs(np.diff(a, axis=1)).mean() + 1e-6
    sx = np.abs(a[:, 0] - a[:, -1]).mean() / inner
    sy = np.abs(a[0] - a[-1]).mean() / (np.abs(np.diff(a, axis=0)).mean() + 1e-6)
    return round(float(sx), 2), round(float(sy), 2)


def export_terrain3d(entry, art_dir):
    _, planet, material = entry["key"].split("/")
    seed = int(entry.get("seed", 1))
    smooth = float(entry.get("smooth", 0.25))
    strength = float(entry.get("normal_strength", 0.35))
    out = {}
    if material == "backwall":
        d = os.path.join(art_dir, "terrain", planet)
        os.makedirs(d, exist_ok=True)
        face = make_face(entry["side"], seed, smooth, strength)
        for m, a in face.items():
            _write(os.path.join(d, f"backwall_{m}.png"), a)
        out["backwall"] = (face, seam_score(face["color"]))
        return out
    d = os.path.join(art_dir, "terrain", planet, material)
    os.makedirs(d, exist_ok=True)
    for fname, spec, s in (("top", entry["top"], seed), ("side", entry["side"], seed + 100)):
        face = make_face(spec, s, smooth, strength)
        for m, a in face.items():
            _write(os.path.join(d, f"{fname}_{m}.png"), a)
        out[fname] = (face, seam_score(face["color"]))
    return out


def contact(results, path, stamp_fn=None, stamp_src=None):
    """2x2 tiled colour + relit (light upper right) per face, side by side."""
    L = np.array([0.55, 0.55, 0.63], np.float32)
    L /= np.linalg.norm(L)
    panels = []
    for name, (face, seam) in results:
        c = face["color"]
        n = face["normal"] * 2 - 1
        lit = c * (0.3 + 0.8 * np.clip(n @ L, 0, 1))[..., None] * face["mask"][..., 1:2]
        tile = np.vstack([np.hstack([lit, lit]), np.hstack([lit, lit])])[::2, ::2]   # 2x2 at half size
        panels.append(np.pad(tile, ((4, 4), (4, 4), (0, 0)), constant_values=0.12))
    sheet = np.hstack(panels)
    if stamp_fn and stamp_src:
        stamp_fn(sheet, stamp_src)
    pngio.write_png(path, np.dstack([pngio.to_u8(np.clip(sheet, 0, 1)), np.full(sheet.shape[:2], 255, np.uint8)]))
