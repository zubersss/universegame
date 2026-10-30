"""FX frame sheets (B-012, contract §4 `fx/<name>`), called by render.py as a generator.

Seeded numpy, returns {"frames": [{map: HxWx4 uint8}, ...]}; render.py packs the sheet
(4 px gutters) and writes base.json from the manifest's `animations`. Looping effects use
noise that loops in time: either rolled by exactly one period over the cycle, or a
cos/sin blend of two fields. Emission is the colour premultiplied by intensity (black where
nothing glows); colour alpha is coverage.

  thruster     : downward exhaust flame, nozzle at the top (pivot), hot core -> orange -> red
  dust         : rising, spreading puff (neutral tan; tint per planet in Unity), no emission
  dig_sparks   : burst of hot streaks from the centre, fading
  escape_band  : horizontal glowing band that flows along x; tiles in x (no side padding)
  heat_shimmer : faint rising wavy streaks for heat haze
"""
import numpy as np

from meridian.noise import fft_noise

PAD = 8


def C(c):
    return np.array(c, np.float32) / 255.0


def _u8(a):
    return np.clip(np.rint(a * 255.0), 0, 255).astype(np.uint8)


def _frame(rgb, a, glow=None):
    """uint8 maps for one frame; RGB under alpha 0 stays the local colour (no halos)."""
    a = np.clip(a, 0, 1)
    out = {"color": np.dstack([_u8(rgb), _u8(a)])}
    if glow is not None:
        out["emission"] = np.dstack([_u8(rgb * np.clip(glow, 0, 1)[..., None]), np.full(a.shape, 255, np.uint8)])
    return out


def _ramp(t, stops):
    """Piecewise-linear colour ramp; stops = [(pos, rgb0-1), ...] ascending."""
    t = np.clip(t, 0, 1)[..., None]
    out = np.zeros(t.shape[:-1] + (3,), np.float32) + stops[0][1]
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        k = np.clip((t - p0) / max(p1 - p0, 1e-6), 0, 1)
        out = np.where(t >= p0, c0 + (c1 - c0) * k, out)
    return out


def thruster(rng, w, h, n):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = (xx + 0.5 - w / 2) / (w / 2 - PAD)
    v = (yy + 0.5 - PAD) / (h - 2 * PAD)                  # 0 at the nozzle (top), 1 at the tail
    base1 = fft_noise(rng, h, w, 6, 60, 0.8)
    base2 = fft_noise(rng, h, w, 3, 16, 0.4)
    frames = []
    for i in range(n):
        shift = int(round(i * h / n))                     # flows down one full period per loop
        nz = 0.65 * np.roll(base1, shift, axis=0) + 0.35 * np.roll(base2, 2 * shift, axis=0)
        vv = np.clip(v, 0, 1)
        width = 0.5 * (0.35 + 0.65 * (1 - vv) ** 0.6) * (1 + 0.12 * nz)
        I = np.exp(-2.2 * (u / np.maximum(width, 1e-3)) ** 2) * (1 - vv) ** 1.3 * (0.85 + 0.3 * nz)
        I *= ((v > 0) & (v < 1)) * _inside(h, w)
        core =np.exp(-(u / (0.35 * width)) ** 2) * np.exp(-vv * 5.0)
        heat = np.clip(0.75 * I + 0.6 * core, 0, 1)
        col = _ramp(heat, [(0.0, C((150, 40, 16))), (0.35, C((235, 110, 36))), (0.7, C((255, 196, 110))),
                           (1.0, C((228, 238, 255)))])
        frames.append(_frame(col, I * 1.5, glow=np.clip(I * 1.3 + core * _inside(h, w), 0, 1)))
    return frames


def dust(rng, w, h, n):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nz = fft_noise(rng, h, w, 4, 40, 0.7)
    frames = []
    for i in range(n):
        t = i / max(n - 1, 1)
        r = (14 + 38 * t) * w / 128
        cx, cy = w / 2, h - PAD - r * 0.9 - 6 * t * h / 128
        d = np.hypot((xx - cx) / 1.25, yy - cy) / r
        dens = np.clip(1 - d + 0.32 * np.roll(nz, int(-t * 20), axis=0), 0, 1)
        a = dens ** 1.3 * 0.85 * (1 - t) ** 1.2
        shade = np.clip(0.88 + 0.22 * ((xx - cx) - (yy - cy)) / (2 * r), 0.7, 1.15)   # lit upper-right
        col = C((188, 170, 146))[None, None, :] * shade[..., None]
        frames.append(_frame(col, a * _inside(h, w)))
    return frames


def dig_sparks(rng, w, h, n):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    k = 46
    ang = rng.uniform(-np.pi * 0.95, -np.pi * 0.05, k)    # mostly upward (image y down)
    spd = rng.uniform(0.55, 1.15, k) * (w / 2 - PAD - 4)
    life = rng.uniform(0.55, 1.0, k)
    frames = []
    for i in range(n):
        t = (i + 1) / n
        I = np.zeros((h, w), np.float32)
        for a0, s, L in zip(ang, spd, life):
            if t > L:
                continue
            p1 = np.array([w / 2 + np.cos(a0) * s * t, h / 2 + np.sin(a0) * s * t + 30 * t * t * h / 128])
            p0 = np.array([w / 2 + np.cos(a0) * s * max(t - 0.12, 0), h / 2 + np.sin(a0) * s * max(t - 0.12, 0)
                           + 30 * max(t - 0.12, 0) ** 2 * h / 128])
            d = _seg_dist(xx, yy, p0, p1)
            I = np.maximum(I, np.exp(-(d / 1.4) ** 2) * (1 - (t / L) ** 2.5))   # bright until late
        I *= _inside(h, w)
        col = _ramp(I, [(0.0, C((220, 90, 30))), (0.5, C((255, 170, 70))), (1.0, C((255, 240, 200)))])
        frames.append(_frame(col, I * 1.4, glow=I))
    return frames


def escape_band(rng, w, h, n):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    n1 = fft_noise(rng, h, w, 8, 128, 1.0)
    n2 = fft_noise(rng, h, w, 4, 32, 0.6)
    frames = []
    for i in range(n):
        shift = int(round(i * w / n))                     # flows along x one full period per loop
        a1, a2 = np.roll(n1, shift, axis=1), np.roll(n2, -2 * shift, axis=1)
        cy = h / 2 + 3 * a1
        sig = 6 + 2.5 * a2
        I = np.exp(-((yy - cy) / np.maximum(sig, 2)) ** 2) * (0.65 + 0.35 * np.tanh(a1))
        I *= ((yy >= PAD) & (yy < h - PAD))
        col = _ramp(I, [(0.0, C((40, 140, 210))), (0.6, C((120, 220, 255))), (1.0, C((236, 250, 255)))])
        frames.append(_frame(col, I, glow=I))
    return frames


def heat_shimmer(rng, w, h, n):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    base = fft_noise(rng, h, w, 3, 24, 0.5)
    env = np.clip(1 - np.hypot((xx - w / 2) / (w / 2 - PAD), (yy - h / 2) / (h / 2 - PAD)), 0, 1) ** 1.5
    frames = []
    for i in range(n):
        shift = int(round(-i * h / n))                    # rises one period per loop
        s = np.roll(base, shift, axis=0)
        streak = np.clip(np.sin(xx * 0.35 + 2.2 * s) * 0.5 + 0.5, 0, 1) ** 4
        a = 0.22 * streak * env
        frames.append(_frame(np.broadcast_to(C((255, 246, 232)), (h, w, 3)).copy(), a))
    return frames


def _inside(h, w):
    """1 inside the padded area, 0 in the 8 px margin."""
    m = np.zeros((h, w), np.float32)
    m[PAD:h - PAD, PAD:w - PAD] = 1
    return m


def _seg_dist(xx, yy, p0, p1):
    d = p1 - p0
    L2 = max(float(d @ d), 1e-6)
    t = np.clip(((xx - p0[0]) * d[0] + (yy - p0[1]) * d[1]) / L2, 0, 1)
    return np.hypot(xx - (p0[0] + t * d[0]), yy - (p0[1] + t * d[1]))


GEN = {"thruster": thruster, "dust": dust, "dig_sparks": dig_sparks, "escape_band": escape_band,
       "heat_shimmer": heat_shimmer}


def generate(entry, ctx):
    name = entry["key"].split("/")[1]
    w, h = entry["size"]
    n = sum(int(c["length"]) for c in entry["animations"]["clips"])
    frames = GEN[name](np.random.default_rng(int(entry.get("seed", 1))), w, h, n)
    if ctx["preview"]:
        frames = [{k: v[::4, ::4].copy() for k, v in f.items()} for f in frames]
    return {"frames": frames}
