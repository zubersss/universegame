"""Side-view parallax backgrounds (contract §4 `backgrounds/<planet>/layer0..2`), called by
render.py. 2048x1024 each, seeded numpy, periodic in x (ridges are FFT noise over the width,
tree/rock positions wrap), so every layer tiles horizontally.

  layer0 far : opaque sky gradient, clouds, distant range under heavy haze
  layer1 mid : transparent above a hazed ridge (forest or mesas), fog toward its base
  layer2 near: transparent above a near ridge with readable detail, light haze

Haze grows with distance (layer2 -> layer0), which is what gives depth with no lighting.
Planet look comes from PRESETS (Bible §7 / §9 palettes); the manifest picks it by key.
"""
import numpy as np

from meridian import post, pngio
from meridian.noise import fft_noise, fft_noise_1d

W_, H_ = 2048, 1024


def C(c):
    return np.array(c, np.float32) / 255.0


PRESETS = {
    "earth": dict(
        sky_top=(82, 132, 192), sky_horizon=(196, 214, 226), haze=(184, 202, 214), cloud=(246, 247, 250),
        cloud_shade=(176, 188, 204), clouds=0.55,
        far=dict(color=(118, 140, 162), snow=(214, 224, 234), level=0.66, amp=150, haze=0.55),
        mid=dict(color=(70, 104, 76), level=0.52, amp=70, haze=0.42, trees=420, tree_h=(26, 46), kind="forest",
                 tree_cols=[(58, 92, 62), (66, 104, 66), (80, 112, 64)]),
        near=dict(color=(52, 84, 44), level=0.36, amp=55, haze=0.10, trees=70, tree_h=(110, 230), kind="forest",
                  tree_cols=[(40, 70, 40), (48, 84, 44), (62, 96, 46), (34, 60, 38)], ground_detail=(86, 110, 52)),
    ),
    # Bible §7.2: butterscotch sky, rust/umber/salmon, thin haze; mesas, dunes, basalt boulders.
    "mars": dict(
        sky_top=(150, 108, 78), sky_horizon=(222, 184, 142), haze=(214, 170, 128), cloud=(236, 214, 188),
        cloud_shade=(206, 168, 132), clouds=0.04,
        far=dict(color=(172, 116, 86), level=0.62, amp=90, haze=0.58, terrace=2),
        mid=dict(color=(160, 90, 58), level=0.50, amp=110, haze=0.36, terrace=3,
                 strata=(22, 0.10, (196, 126, 88))),
        near=dict(color=(146, 78, 48), level=0.30, amp=40, haze=0.08, kind="rocks", rocks=90, rock_h=(18, 90),
                  rock_cols=[(70, 52, 46), (88, 62, 52), (58, 44, 40)], ground_detail=(178, 108, 72), detail_k=0.3),
    ),
}


def terrace(line, levels, amp):
    """Mesa profile: flatten the ridge into `levels` plateaus joined by steep cliffs."""
    lo, hi = line.min(), line.max()
    t = (line - lo) / max(hi - lo, 1e-3) * levels
    k = np.floor(t)
    f = t - k
    f = np.clip((f - 0.75) / 0.25, 0, 1)                 # cliff over the last quarter of each step
    out = (lo + (k + f * f * (3 - 2 * f)) / levels * (hi - lo)).astype(np.float32)
    # Talus: a short circular blur turns vertical walls into steep slopes (periodic).
    kw = 15
    out = np.convolve(np.r_[out[-(kw // 2):], out, out[:kw // 2]], np.ones(kw) / kw, "valid").astype(np.float32)
    # Still periodic; rotate so the wrap column sits on a plateau, not on a cliff face.
    step = np.abs(out - np.roll(out, 1))
    flat = np.convolve(np.r_[step[-8:], step, step[:8]], np.ones(17), "valid")
    return np.roll(out, -int(np.argmin(flat)))


def boulder(rng, h, w):
    """Alpha patch of a squat rock: a few overlapping ellipses, flat-bottomed."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.zeros((h, w), np.float32)
    for _ in range(5):
        cx = w / 2 + (rng.random() - 0.5) * w * 0.5
        cy = h * (0.55 + 0.3 * rng.random())
        rx, ry = w * (0.22 + 0.15 * rng.random()), h * (0.35 + 0.2 * rng.random())
        d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
        a = np.maximum(a, np.clip((1 - d) * min(rx, ry) + 0.5, 0, 1))
    return a


def _u8(a):
    return np.clip(np.rint(a * 255.0), 0, 255).astype(np.uint8)


def ridge(rng, level, amp, lo=80, hi=1024, slope=1.2, detail=0.15):
    """Row (from the top) of a periodic ridge line for every column."""
    y = fft_noise_1d(rng, W_, lo, hi, slope)
    y += detail * fft_noise_1d(rng, W_, 6, 40, 0.5)
    return (H_ * (1 - level) - amp * y).astype(np.float32)


def fill_below(line, soft=1.0):
    rows = np.arange(H_, dtype=np.float32)[:, None] + 0.5
    return np.clip((rows - line[None, :]) / soft + 0.5, 0, 1)


def shade_mix(a, b, t):
    return a + (b - a) * np.clip(t, 0, 1)[..., None]


# ---------------------------------------------------------------- trees

def conifer(h, w):
    """Alpha patch (h x w) of a layered conifer, apex at the top centre."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = (yy + 0.5) / h                                   # 0 apex .. 1 base
    tiers = 5 + int(h / 40)
    saw = 0.62 + 0.38 * ((t * tiers) % 1.0)
    hw = (w / 2) * np.clip(t * 1.05, 0, 1) * saw
    trunk = (t > 0.9) & (np.abs(xx + 0.5 - w / 2) < max(1.0, w * 0.05))
    a = np.clip(hw - np.abs(xx + 0.5 - w / 2) + 0.5, 0, 1)
    return np.maximum(a * (t < 0.93), trunk.astype(np.float32))


def broadleaf(rng, h, w):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.zeros((h, w), np.float32)
    crown_h = h * 0.72
    for _ in range(16):
        cx = w / 2 + (rng.random() - 0.5) * w * 0.62
        cy = crown_h * (0.25 + 0.55 * rng.random())
        r = w * (0.11 + 0.11 * rng.random())
        a = np.maximum(a, np.clip(r - np.hypot(xx - cx, yy - cy) + 0.5, 0, 1))
    trunk = (yy > crown_h * 0.7) & (np.abs(xx + 0.5 - w / 2) < max(1.0, w * 0.045))
    return np.maximum(a, trunk.astype(np.float32))


def stamp(canvas_rgb, canvas_a, patch_a, col, x0, y_base, light_top=0.12, rng=None):
    """Composite a tree patch (bottom-centre at x0, y_base) with x wrap; vertical light."""
    h, w = patch_a.shape
    top = int(round(y_base)) - h
    cols = (np.arange(w) + int(round(x0 - w / 2))) % W_
    r0, r1 = max(top, 0), min(top + h, H_)
    if r1 <= r0:
        return
    pa = patch_a[r0 - top:r1 - top]
    grad = 1 + light_top * (1 - 2 * (np.arange(r0 - top, r1 - top, dtype=np.float32) / h))[:, None]
    var = 1.0 if rng is None else float(1 + 0.08 * rng.standard_normal())   # one tint per tree
    tint = col[None, None, :] * grad[..., None] * var
    sub_rgb = canvas_rgb[r0:r1][:, cols]
    sub_a = canvas_a[r0:r1][:, cols]
    pa3 = pa[..., None]
    canvas_rgb[r0:r1, cols] = sub_rgb * (1 - pa3) + tint * pa3
    canvas_a[r0:r1, cols] = sub_a + pa * (1 - sub_a)


# ---------------------------------------------------------------- layers

def layer0(P, rng):
    rgb = sky_rgb(P, rng)
    return _layer0_range(P, rng, rgb)


def sky_rgb(P, rng):
    """Painted sky: vertical gradient plus a soft cumulus band (none when clouds ~ 0)."""
    rows = (np.arange(H_, dtype=np.float32) / H_)[:, None]
    t = np.clip(rows / 0.72, 0, 1) ** 1.3
    sky = shade_mix(np.broadcast_to(C(P["sky_top"]), (H_, W_, 3)), C(P["sky_horizon"]),
                    np.broadcast_to(t, (H_, W_)))
    # Cumulus band: large soft masses from low-frequency noise, shaded undersides.
    n = fft_noise(rng, H_, W_, 50, 800, 1.4) + 0.2 * fft_noise(rng, H_, W_, 10, 50, 0.6)
    band = np.exp(-((rows - 0.34) / 0.12) ** 2)
    x = np.clip((n * band - (1.0 - P["clouds"])) * 1.2, 0, 1)
    cov = x * x * (3 - 2 * x) if P["clouds"] > 0.05 else np.zeros_like(x)   # Mars: none
    under = np.clip(np.roll(cov, -10, axis=0) - cov + 0.3, 0, 1)        # darker toward bases
    cloud = shade_mix(np.broadcast_to(C(P["cloud"]), (H_, W_, 3)), C(P["cloud_shade"]), under)
    return shade_mix(sky, cloud, cov * 0.92)


def _layer0_range(P, rng, rgb):
    f = P["far"]
    if f.get("terrace"):
        line = terrace(ridge(rng, f["level"], f["amp"], 220, 1024, 1.6, 0.0), f["terrace"], f["amp"])
    else:
        line = ridge(rng, f["level"], f["amp"], 120, 1024, 1.5, 0.06)
    a = fill_below(line)
    rows_px = np.arange(H_, dtype=np.float32)[:, None]
    depth = np.clip((rows_px - line[None, :]) / 140, 0, 1)
    rock = C(f["color"]) * (0.93 + 0.07 * fft_noise(rng, H_, W_, 8, 200, 1.0))[..., None]
    if "snow" in f:
        # Snow above an altitude (row) line, ragged by noise, only near the surface.
        snowline = H_ * (1 - f["level"]) - f["amp"] * 0.45
        s = np.clip((snowline - rows_px) / 50 + 0.6 * fft_noise(rng, H_, W_, 6, 60, 0.6), 0, 1)
        rock = shade_mix(rock, C(f["snow"]), s * (1 - np.clip(depth * 1.5, 0, 1)) * 0.9)
    rng_haze = f["haze"] + (1 - f["haze"]) * 0.6 * depth                 # haze thickens downward
    rock = shade_mix(rock, C(P["haze"]), rng_haze)
    rgb = shade_mix(rgb, rock, a)
    return {"color": np.dstack([_u8(rgb), np.full((H_, W_), 255, np.uint8)])}


def hill_layer(P, rng, spec, near):
    if spec.get("terrace"):
        line = terrace(ridge(rng, spec["level"], spec["amp"], 220, 1024, 1.6, 0.0), spec["terrace"], spec["amp"])
    else:
        line = ridge(rng, spec["level"], spec["amp"], 50, 1024, 1.1, 0.2)
    rows = np.arange(H_, dtype=np.float32)[:, None]
    a = fill_below(line)
    tex = 0.9 + 0.1 * fft_noise(rng, H_, W_, 3, 60, 0.6)
    rgb = C(spec["color"])[None, None, :] * tex[..., None]
    if spec.get("strata"):
        # Layered rock: horizontal bands, gently warped so they don't read as ruled lines.
        period, k, band_col = spec["strata"]
        warp = 6 * fft_noise(rng, H_, W_, 40, 400, 1.0)
        s = 0.5 + 0.5 * np.sin(2 * np.pi * (rows + warp) / period)
        rgb = shade_mix(rgb, C(band_col), s * k * 4)
    if near and "ground_detail" in spec:
        g = np.clip(fft_noise(rng, H_, W_, 2, 10, 0.2) - 0.8, 0, 1)
        rgb = shade_mix(rgb, C(spec["ground_detail"]), g * spec.get("detail_k", 0.8))
    rgb = np.ascontiguousarray(rgb, np.float32)
    a = np.ascontiguousarray(a, np.float32)
    if spec.get("kind") == "forest":
        lo, hi = spec["tree_h"]
        xs = np.sort(rng.random(spec["trees"]) * W_)
        hs = lo + (hi - lo) * rng.random(spec["trees"]) ** 1.5
        order = np.argsort(hs)                                            # small (far) first
        cols = [C(c) for c in spec["tree_cols"]]
        for k in order:
            x0, h = xs[k], int(hs[k])
            sink = (0.15 + 0.25 * rng.random()) * h * (0.3 if near else 0.6)
            yb = line[int(x0) % W_] + sink
            if rng.random() < (0.55 if near else 0.7):
                patch = conifer(h, max(6, int(h * (0.36 + 0.1 * rng.random()))))
            else:
                patch = broadleaf(rng, h, max(8, int(h * (0.7 + 0.2 * rng.random()))))
            stamp(rgb, a, patch, cols[rng.integers(len(cols))], x0, yb, rng=rng)
    elif spec.get("kind") == "rocks":
        lo, hi = spec["rock_h"]
        n = spec["rocks"]
        xs = rng.random(n) * W_
        hs = lo + (hi - lo) * rng.random(n) ** 2.2
        cols = [C(c) for c in spec["rock_cols"]]
        for k in np.argsort(hs):
            h = int(hs[k])
            patch = boulder(rng, h, max(8, int(h * (1.3 + 0.8 * rng.random()))))
            yb = line[int(xs[k]) % W_] + h * (0.15 + 0.2 * rng.random()) + (hi - h) * 0.4
            stamp(rgb, a, patch, cols[rng.integers(len(cols))], xs[k], yb, light_top=0.25, rng=rng)
    # Haze: whole layer by distance, plus fog pooling toward the base of the mid layer.
    hz = np.full((H_, W_), spec["haze"], np.float32)
    if not near:
        hz = hz + (1 - spec["haze"]) * 0.5 * np.clip((rows - line[None, :] - 40) / 300, 0, 1)
    rgb = shade_mix(rgb, C(P["haze"]), hz)
    rgb, _ = post.dilate(rgb, a >= 0.5, 8)
    return {"color": np.dstack([_u8(rgb), _u8(a)])}


def generate(entry, ctx):
    _, planet, layer = entry["key"].split("/")
    P = PRESETS[entry.get("preset", planet)]
    rng = np.random.default_rng(int(entry.get("seed", 1)))
    if layer == "layer0":
        maps = layer0(P, rng)
    elif layer == "layer1":
        maps = hill_layer(P, rng, P["mid"], near=False)
    elif layer == "layer2":
        maps = hill_layer(P, rng, P["near"], near=True)
    else:
        raise ValueError(f"gen_backdrop: unknown layer '{layer}'")
    if ctx["preview"]:
        maps = {k: v[::4, ::4].copy() for k, v in maps.items()}
    return maps
