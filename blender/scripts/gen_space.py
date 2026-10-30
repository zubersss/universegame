"""Procedural generators for the Sun surface and the top-down space layers (B-005), called by
render.py. Everything is seeded numpy, periodic by construction (FFT noise, wrapped star
positions), so every map tiles in x and y and re-renders byte-identically. No external inputs.

Variants by key:
  planets/sun/surface      - equirect photosphere: granulation, faint supergranule mottling,
                             a few sunspot groups; color and emission (the Sun is self-lit)
  backgrounds/space/layer0 - opaque far layer: near-black, Milky Way band with dust lanes,
                             dense faint stars
  backgrounds/space/layer1 - transparent mid layer: small stars
  backgrounds/space/layer2 - transparent near layer: few bright stars with soft halos
Manifest fields: `seed`, `stars` (count), `star_size` (px sigma), `star_gain`.
"""
import numpy as np


def _u8(a):
    return np.clip(np.rint(a * 255.0), 0, 255).astype(np.uint8)


def fft_noise(rng, h, w, lo, hi, slope=1.0):
    """Periodic band-limited noise in [-1, 1]-ish (unit std). lo/hi: wavelength in px."""
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.rfftfreq(w)[None, :]
    f = np.hypot(fy, fx)
    f[0, 0] = 1.0
    band = (f >= 1.0 / hi) & (f <= 1.0 / lo)
    spec = (rng.standard_normal(f.shape) + 1j * rng.standard_normal(f.shape)) * band / f ** slope
    spec[0, 0] = 0
    n = np.fft.irfft2(spec, s=(h, w))
    return n / (n.std() + 1e-9)


# ---------------------------------------------------------------- stars

STAR_COLORS = np.array([      # sRGB 0-1, rough spectral classes O/B .. M, weighted toward G/K/M
    (0.70, 0.78, 1.00), (0.82, 0.87, 1.00), (0.97, 0.97, 1.00),
    (1.00, 0.96, 0.88), (1.00, 0.86, 0.68), (1.00, 0.74, 0.52)], np.float32)
STAR_WEIGHTS = np.array([0.04, 0.10, 0.20, 0.26, 0.24, 0.16])


def splat_stars(rng, h, w, n, sigma, gain, density=None, power=2.2):
    """Gaussian star splats with wrap-around. Returns premultiplied rgb (h,w,3) and alpha.
    density: optional (h,w) map 0..1 that biases where stars land."""
    if density is not None:
        p = (density / density.sum()).ravel()
        idx = rng.choice(h * w, size=n, p=p)
        ys = idx // w + rng.random(n)
        xs = idx % w + rng.random(n)
    else:
        ys, xs = rng.random(n) * h, rng.random(n) * w
    mag = rng.random(n) ** power * gain                      # many faint, few bright
    col = STAR_COLORS[rng.choice(len(STAR_COLORS), size=n, p=STAR_WEIGHTS)]
    sig = sigma * (0.7 + 0.6 * rng.random(n)) * (1 + 0.6 * mag / max(gain, 1e-6))
    r = int(np.ceil(3 * sigma * 1.6 * 1.6)) + 1
    off = np.arange(-r, r + 1)
    acc = np.zeros((h, w, 3), np.float32)
    a = np.zeros((h, w), np.float32)
    for y, x, m, c, s in zip(ys, xs, mag, col, sig):
        iy, ix = int(y), int(x)
        gy = np.exp(-((iy + off + 0.5 - y) ** 2) / (2 * s * s))
        gx = np.exp(-((ix + off + 0.5 - x) ** 2) / (2 * s * s))
        k = (gy[:, None] * gx[None, :] * m).astype(np.float32)
        rows = (iy + off) % h
        cols = (ix + off) % w
        a[np.ix_(rows, cols)] += k
        acc[np.ix_(rows, cols)] += k[..., None] * c
    return acc, a


def _halo(rgb_pm, a, radius, strength):
    """Soft periodic halo around bright stars (Gaussian blur via FFT)."""
    h, w = a.shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.rfftfreq(w)[None, :]
    g = np.exp(-2 * (np.pi * radius) ** 2 * (fy ** 2 + fx ** 2))
    blur = lambda img: np.fft.irfft2(np.fft.rfft2(img) * g, s=(h, w))
    a2 = a + strength * blur(a)
    rgb2 = rgb_pm + strength * np.dstack([blur(rgb_pm[..., i]) for i in range(3)])
    return rgb2, a2


def _transparent(rgb_pm, a):
    """Premultiplied -> straight RGBA uint8 with RGB dilated under alpha 0 (contract §2)."""
    from meridian import post
    a = np.clip(a, 0, 1)
    rgb = np.where(a[..., None] > 1e-4, rgb_pm / np.maximum(a[..., None], 1e-4), 0)
    rgb = np.clip(rgb, 0, 1)
    a8 = _u8(a)
    rgb, _ = post.dilate(rgb, a8 > 0, 8)
    return np.dstack([_u8(rgb), a8])


# ---------------------------------------------------------------- variants

def sun_surface(entry, rng, h, w):
    s = w / 2048.0
    gran = fft_noise(rng, h, w, 3 * s, 10 * s, 0.3)          # granulation cells
    gran = np.tanh(gran * 0.9)
    superg = fft_noise(rng, h, w, 40 * s, 160 * s, 0.5)       # supergranule mottling
    t = 0.80 + 0.07 * gran + 0.05 * superg
    # Sunspot groups: umbra/penumbra, kept within ±35° latitude, periodic in x.
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    for _ in range(int(entry.get("spots", 5))):
        cy = h / 2 + (rng.random() - 0.5) * 0.4 * h
        cx = rng.random() * w
        for _k in range(rng.integers(1, 4)):
            oy, ox = rng.normal(0, 6 * s, 2)
            rad = (2.5 + 5 * rng.random()) * s
            dx = (xx - cx - ox + w / 2) % w - w / 2
            d = np.hypot(dx, yy - cy - oy)
            t -= 0.35 * np.exp(-(d / rad) ** 2) + 0.15 * np.exp(-(d / (2.2 * rad)) ** 2)
    t = np.clip(t, 0.15, 1.0)
    # Temperature ramp: dark spots deep orange, photosphere warm yellow-white.
    lo = np.array([0.55, 0.18, 0.03], np.float32)
    mid = np.array([1.00, 0.62, 0.18], np.float32)
    hi = np.array([1.00, 0.93, 0.70], np.float32)
    k = t[..., None]
    rgb = np.where(k < 0.7, lo + (mid - lo) * (k / 0.7), mid + (hi - mid) * ((k - 0.7) / 0.3))
    one = np.ones((h, w), np.float32)
    return {"color": _u8(np.dstack([rgb, one])), "emission": _u8(np.dstack([rgb, one]))}


def space_layer0(entry, rng, h, w):
    s = w / 2048.0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # Band centre line: periodic in x so the layer tiles; tilted look from a sine.
    centre = h * 0.5 + 0.12 * h * np.sin(2 * np.pi * xx / w + 0.6)
    dy = (yy - centre + h / 2) % h - h / 2                     # periodic in y as well
    sigma = 0.11 * h * (1 + 0.25 * fft_noise(rng, h, w, 200 * s, 900 * s, 0.6))
    band = np.exp(-(dy / sigma) ** 2)
    # Galactic-centre bulge: brighter, warmer around one longitude.
    bx = (xx - 0.62 * w + w / 2) % w - w / 2
    bulge = np.exp(-(bx / (0.16 * w)) ** 2) * np.exp(-(dy / (0.16 * h)) ** 2)
    clouds = 0.6 + 0.4 * np.tanh(fft_noise(rng, h, w, 6 * s, 220 * s, 0.9))
    dust = np.clip(fft_noise(rng, h, w, 4 * s, 120 * s, 1.0), 0, None)
    dust = 1 - 0.75 * np.tanh(dust * 1.2) * np.exp(-(dy / (0.45 * sigma)) ** 2)
    glow = (0.11 * band * clouds + 0.16 * bulge * clouds) * dust
    warm = np.array([1.00, 0.86, 0.68], np.float32)
    cool = np.array([0.70, 0.78, 1.00], np.float32)
    mix = np.clip(bulge * 2.5, 0, 1)[..., None]
    rgb = glow[..., None] * (cool * (1 - mix) + warm * mix)
    rgb += np.array([0.012, 0.014, 0.024], np.float32)       # near-black, faintly blue
    # Unresolved star haze + faint stars concentrated in the band.
    dens = 0.15 + band * clouds
    st, sa = splat_stars(rng, h, w, int(entry.get("stars", 9000) * s * s), 0.55 * s,
                         float(entry.get("star_gain", 0.55)), dens, power=3.0)
    rgb = rgb * (1 - np.clip(sa, 0, 1)[..., None]) + st
    rgb = np.clip(rgb, 0, 1)
    return {"color": np.dstack([_u8(rgb), np.full((h, w), 255, np.uint8)])}


def space_stars(entry, rng, h, w, halo):
    s = w / 2048.0
    st, sa = splat_stars(rng, h, w, int(entry.get("stars", 1500) * s * s),
                         float(entry.get("star_size", 0.7)) * s, float(entry.get("star_gain", 1.0)))
    if halo:
        st, sa = _halo(st, sa, 3.0 * s, 0.6)
    return {"color": _transparent(st, sa)}


def generate(entry, ctx):
    w, h = entry["size"]
    if ctx["preview"]:
        w, h = w // 4, h // 4
    rng = np.random.default_rng(int(entry.get("seed", 1)))
    key = entry["key"]
    if key == "planets/sun/surface":
        return sun_surface(entry, rng, h, w)
    if key == "backgrounds/space/layer0":
        return space_layer0(entry, rng, h, w)
    if key == "backgrounds/space/layer1":
        return space_stars(entry, rng, h, w, halo=False)
    if key == "backgrounds/space/layer2":
        return space_stars(entry, rng, h, w, halo=True)
    raise ValueError(f"gen_space: no generator for '{key}'")
