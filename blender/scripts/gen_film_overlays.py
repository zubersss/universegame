"""Film overlays for the v4 film pass (contract §11.6, Bible §9.1 film treatment; B-115).

fx/film/grain, fx/film/dust, fx/film/scratches: 512x512, seamless in x and y, greyscale in RGB
with alpha, subtle. numpy only (no scene). Everything is built periodic on the 512 torus
(FFT-filtered noise, shapes stamped with wrap-around), so the tiles have no seam.

  grain     RGB = 128 +- fine clumped noise (std ~ 18/255), alpha 255: the shader blends it
            as overlay around mid-grey.
  dust      <= 8 specks per tile (irregular dark blots 1.5-4 px and one curly fibre), RGB dark
            warm grey, alpha = coverage (peak <= 0.7); everything else alpha 0.
  scratches 1-2 hairline vertical scratches (0.6-1.2 px, light), running the full height with
            a slow sideways wander and breaks; alpha = coverage (peak <= 0.55).
"""
import numpy as np

N = 512


def _periodic_noise(rng, sigma_px):
    """Gaussian-filtered white noise on the torus (FFT), unit std."""
    w = rng.standard_normal((N, N))
    f = np.fft.fftfreq(N)
    k2 = f[:, None] ** 2 + f[None, :] ** 2
    g = np.exp(-2 * (np.pi * sigma_px) ** 2 * k2)
    out = np.real(np.fft.ifft2(np.fft.fft2(w) * g))
    return out / (out.std() + 1e-9)


def _stamp_wrap(acc, cx, cy, r_fn, rad):
    """Max-accumulate a soft shape centred (cx, cy) with wrap-around. r_fn(dx, dy) -> coverage."""
    R = int(np.ceil(rad)) + 2
    ys = (np.arange(int(cy) - R, int(cy) + R + 1)) % N
    xs = (np.arange(int(cx) - R, int(cx) + R + 1)) % N
    dy = (np.arange(int(cy) - R, int(cy) + R + 1) + 0.5 - cy)[:, None]
    dx = (np.arange(int(cx) - R, int(cx) + R + 1) + 0.5 - cx)[None, :]
    cov = r_fn(dx, dy)
    sub = acc[np.ix_(ys, xs)]
    acc[np.ix_(ys, xs)] = np.maximum(sub, cov)


def _ss_disc(r, lump=None):
    """Antialiased (4x4 supersampled) disc coverage with an optional angular lump function."""
    def fn(dx, dy):
        tot = 0.0
        for oy in (-0.375, -0.125, 0.125, 0.375):
            for ox in (-0.375, -0.125, 0.125, 0.375):
                x, y = dx + ox, dy + oy
                rr = r * (1 + (lump(np.arctan2(y, x)) if lump else 0))
                tot = tot + ((x * x + y * y) <= rr * rr)
        return tot / 16.0
    return fn


def grain(rng):
    n = 0.7 * _periodic_noise(rng, 0.6) + 0.3 * _periodic_noise(rng, 1.4)
    n /= n.std()
    v = np.clip(128 + 18 * n, 0, 255)
    rgb = np.repeat(v[..., None], 3, -1)
    return np.dstack([rgb, np.full((N, N), 255.0)])


def dust(rng):
    acc = np.zeros((N, N))
    n_specks = 7
    for _ in range(n_specks):
        cx, cy = rng.uniform(0, N, 2)
        r = rng.uniform(0.8, 2.0)
        ph = rng.uniform(0, 6.28, 2)
        lump = lambda t, ph=ph: 0.25 * np.sin(2 * t + ph[0]) + 0.15 * np.sin(3 * t + ph[1])  # noqa: E731
        a = rng.uniform(0.45, 0.7)
        _stamp_wrap(acc, cx, cy, lambda dx, dy, r=r, lump=lump, a=a: a * _ss_disc(r, lump)(dx, dy), r * 1.5)
    # one curly fibre (counts as the 8th speck): a short wandering hair
    x, y = rng.uniform(0, N, 2)
    ang = rng.uniform(0, 6.28)
    for i in range(70):
        ang += 0.12 * np.sin(i * 0.21) + rng.normal(0, 0.05)
        x, y = x + 0.5 * np.cos(ang), y + 0.5 * np.sin(ang)
        _stamp_wrap(acc, x, y, lambda dx, dy: 0.5 * _ss_disc(0.55)(dx, dy), 1.0)
    rgb = np.full((N, N, 3), 46.0)
    rgb[..., 0] += 6                        # warm dark grey, still near-neutral
    return np.dstack([rgb, 255 * np.clip(acc, 0, 1)]), n_specks + 1


def scratches(rng):
    acc = np.zeros((N, N))
    count = 2
    for s in range(count):
        x0 = rng.uniform(40, N - 40)
        width = rng.uniform(0.6, 1.2)
        peak = rng.uniform(0.35, 0.55)
        # periodic wander in x and periodic breaks along y, so the line wraps top to bottom
        y = np.arange(N) + 0.5
        k = rng.integers(1, 3)
        wob = 3.0 * np.sin(2 * np.pi * k * y / N + rng.uniform(0, 6.28)) + \
            1.0 * np.sin(2 * np.pi * 5 * y / N + rng.uniform(0, 6.28))
        fade = np.clip(0.6 + 0.6 * np.sin(2 * np.pi * 3 * y / N + rng.uniform(0, 6.28)), 0, 1)
        X = np.arange(N) + 0.5
        d = np.abs(X[None, :] - (x0 + wob)[:, None])
        cov = np.clip(width / 2 + 0.5 - d, 0, 1)
        acc = np.maximum(acc, peak * fade[:, None] * cov)
    rgb = np.full((N, N, 3), 236.0)
    return np.dstack([rgb, 255 * np.clip(acc, 0, 1)]), count


def generate(entry, ctx):
    rng = np.random.default_rng(int(entry.get("seed", 1)))
    variant = entry["key"].split("/")[2]
    if variant == "grain":
        img = grain(rng)
    elif variant == "dust":
        img, _n = dust(rng)
    elif variant == "scratches":
        img, _n = scratches(rng)
    else:
        raise ValueError(f"unknown film overlay '{variant}'")
    return {"color": np.clip(np.rint(img), 0, 255).astype(np.uint8)}
