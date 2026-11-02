"""Contract v2 skydome (§9 depth-bands row, B-083): a 2048x1024 equirect `color` per region,
derived from the v1 layer0 skies (gen_backdrop.py presets: sky_top, sky_horizon, haze, cloud,
cloud_shade, clouds). Row 0 = zenith, row 512 = horizon, below the horizon a haze floor that
darkens toward the nadir (hidden by terrain in game). Clouds: a soft band of cumulus above the
horizon from x-periodic noise (tiles around the dome). Pure numpy.
"""
import os

import numpy as np

from meridian import pngio
from meridian.noise import fft_noise

W, H = 2048, 1024


def C(c):
    return np.array(c, np.float32) / 255.0


def skydome(P, seed):
    rng = np.random.default_rng(seed)
    v = (np.arange(H, dtype=np.float32) + 0.5)[:, None] / H              # 0 zenith .. 1 nadir
    up = np.clip(1 - v / 0.5, 0, 1)                                       # 1 at the zenith, 0 at the horizon
    t = (1 - up) ** 1.6
    sky = C(P["sky_top"]) * (1 - t[..., None]) + C(P["sky_horizon"]) * t[..., None]
    sky = np.broadcast_to(sky, (H, W, 3)).copy()
    below = v > 0.5
    floor = C(P["haze"]) * np.clip(1.15 - (v - 0.5) * 1.2, 0.5, 1)[..., None]
    sky = np.where(below[..., None], np.broadcast_to(floor, (H, W, 3)), sky)
    k = float(P.get("clouds", 0.0))
    if k > 0:
        # v2: long soft wavelengths + a smooth threshold (a first pass with 6-60 px noise and a
        # hard clip read as salt-speckle, not cumulus).
        n = fft_noise(rng, H, W, 90, 1000, 1.5) + 0.22 * fft_noise(rng, H, W, 24, 140, 0.9)
        band = np.exp(-((v - 0.38) / 0.08) ** 2) * (v < 0.49)             # cumulus band above the horizon
        x = np.clip((n - (0.9 - k)) / 0.9, 0, 1)
        dens = (x * x * (3 - 2 * x)) * band * 0.95
        shade = np.clip(0.55 + 0.45 * np.roll(n, -10, axis=0) - 0.3 * np.roll(n, 8, axis=0), 0, 1)   # lit tops, shaded bases
        cc = C(P["cloud_shade"]) * (1 - shade[..., None]) + C(P["cloud"]) * shade[..., None]
        sky = sky * (1 - dens[..., None]) + cc * dens[..., None]
    return np.clip(sky, 0, 1)


def export_skydome(entry, art_dir):
    import gen_backdrop as GB
    _, name, _variant = entry["key"].split("/")
    P = dict(GB.PRESETS[entry.get("sky_preset", name)]) if entry.get("sky_preset", name) in GB.PRESETS else {}
    P.update(entry.get("sky", {}))
    img = skydome(P, int(entry.get("seed", 1)))
    d = os.path.join(art_dir, "backgrounds", name)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "skydome_color.png")
    pngio.write_png(path, np.dstack([pngio.to_u8(img), np.full((H, W), 255, np.uint8)]))
    seam = float(np.abs(img[:, 0] - img[:, -1]).mean() / (np.abs(np.diff(img, axis=1)).mean() + 1e-6))
    return path, img, round(seam, 2)
