"""Planet discs for the space view (contract v3.0 §11.5, Bible §9.3; B-119). numpy only.

Painted watercolour discs with an ink outline that still read as the real planets, each with a
subtle personality idle at 12 fps. Space scale: SPACE_PPU px per space unit (PlanetConfig
.visualRadius), so Jupiter is ~636 px across; Jupiter and the Saturn body get 9-frame idles
(3x3 sheet <= 2048), the others 12. Saturn's rings are two static parts (behind / in front of
the body) whose wobble Unity plays from disc_rig.json.

Look: flat washes with pigment variation and paper grain (gen_painted_bg), one shadow tone on
the night side (light from the upper right, as the Sun sits screen-left of most views is NOT
assumed: the space view lights discs from the Sun at runtime is not v4; the crescent is drawn),
ink on the outline, ring edges and a few interior marks (night-side hatching, band-edge fragments);
no faces or expressions on any planet (D-101): Neptune's character is its wandering dark storm.

  python build_discs_v3.py <out_dir>      writes every disc + a review sheet (preview)
"""
import math
import os
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gp_raster as GR  # noqa: E402
import giants_v3 as GT  # noqa: E402  (B-239: the four giants' belts, storms and rings as one table)
from meridian import pngio, v3  # noqa: E402

SPACE_PPU = 3.0
RADIUS_U = {"mercury": 14, "venus": 24, "earth": 25, "mars": 17, "jupiter": 106, "saturn": 96,
            "uranus": 57, "neptune": 56, "luna": 7}
FRAMES = {"jupiter": 9, "saturn": 9}
SS = 2
OUT_PX = 2.5                     # v3.1 (D-100): outline 2.5 px nominal -> 2.0-3.0 with the +-20 % jitter
IN_PX = 1.25                     # interior marks 1.25 px -> 1.0-1.5
WIDTHS = []                      # (nominal, min, max) px of every ink stroke drawn (review measurement)
PAL = {k: np.array(v3.hex_rgb(h), np.float32) / 255 for k, h in v3.PALETTES["earth"].items()}


def mix(a, b, t):
    return a * (1 - t) + b * t


def shade(c):
    return mix(c, PAL["brown"], 0.3)          # the one shadow tone (v3.shadow_of)


def noise2(rng, n, sigma):
    """Smooth periodic noise on an n x n torus (unit std)."""
    sigma = min(sigma, n / 8)                # small discs: keep some variance (no NaN)
    w = rng.standard_normal((n, n))
    f = np.fft.fftfreq(n)
    g = np.exp(-2 * np.pi ** 2 * sigma ** 2 * (f[:, None] ** 2 + f[None, :] ** 2))
    o = np.real(np.fft.ifft2(np.fft.fft2(w) * g))
    return np.clip(o / max(float(o.std()), 1e-3), -3, 3)


class Disc:
    """Pixel grid of one disc frame at SS supersampling: u, v in [-1, 1] (v up), r, a lumpy rim."""
    def __init__(self, name, R_px, pad, seed):
        self.name, self.R = name, R_px
        self.size = int(2 * (R_px + pad))
        self.size += (-self.size) % 4
        n = self.size * SS
        c = n / 2
        yy, xx = np.mgrid[0:n, 0:n] + 0.5
        self.u = (xx - c) / (R_px * SS)
        self.v = -(yy - c) / (R_px * SS)
        rng = np.random.default_rng(seed)
        ang = np.arctan2(self.v, self.u)
        self.rim = 1.0 + 0.012 * np.sin(3 * ang + rng.uniform(0, 6)) + 0.008 * np.sin(5 * ang + rng.uniform(0, 6))
        self.r = np.hypot(self.u, self.v)
        self.inside = self.r <= self.rim
        self.grain = 1 + 0.03 * noise2(rng, n, 0.8 * SS) + 0.03 * noise2(rng, n, 30 * SS)
        self.pig = 1 + 0.05 * noise2(rng, n, 60 * SS)
        self.rng = rng



class NearDisc(Disc):
    """B-143 (D-128): the far disc's frame-0 drawing at k x its resolution. paint() works in u / v, so the drawing
    scales; the rim phases and the large-scale grain + pigment noise are the far frame's own (the same rng draws,
    resampled at each near pixel's u / v), only the 0.8 px paper fibre is drawn fresh at the near size."""
    def __init__(self, name, R_base, k, pad, seed):
        self.name, self.R, self.R_base = name, R_base * k, R_base
        self.size = int(2 * (self.R + pad))
        self.size += (-self.size) % 4
        n = self.size * SS
        c = n / 2
        yy, xx = np.mgrid[0:n, 0:n] + 0.5
        self.u = (xx - c) / (self.R * SS)
        self.v = -(yy - c) / (self.R * SS)
        rng = np.random.default_rng(seed)                 # the far Disc's draws, in its order
        ph3, ph5 = rng.uniform(0, 6), rng.uniform(0, 6)
        nb = Disc(name, R_base, pad, seed).size * SS
        _fine = noise2(rng, nb, 0.8 * SS)
        coarse = noise2(rng, nb, 30 * SS)
        pign = noise2(rng, nb, 60 * SS)
        ang = np.arctan2(self.v, self.u)
        self.rim = 1.0 + 0.012 * np.sin(3 * ang + ph3) + 0.008 * np.sin(5 * ang + ph5)
        self.r = np.hypot(self.u, self.v)
        self.inside = self.r <= self.rim
        bx = nb / 2 + self.u * R_base * SS - 0.5          # the far frame's pixel coordinates of each near pixel
        by = nb / 2 - self.v * R_base * SS - 0.5
        fine = noise2(np.random.default_rng(seed + 7), n, 0.8 * SS)
        self.grain = 1 + 0.03 * fine + 0.03 * _bilinear(coarse, bx, by)
        self.pig = 1 + 0.05 * _bilinear(pign, bx, by)
        self.rng = rng


def _bilinear(f, x, y):
    """f sampled at float pixel coords (x, y), wrapping (noise2 fields are periodic)."""
    n = f.shape[0]
    x0, y0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = (x - x0).astype(np.float32), (y - y0).astype(np.float32)
    x0, y0 = x0 % n, y0 % n
    x1, y1 = (x0 + 1) % n, (y0 + 1) % n
    return (f[y0, x0] * (1 - fx) + f[y0, x1] * fx) * (1 - fy) + (f[y1, x0] * (1 - fx) + f[y1, x1] * fx) * fy


NEAR_CAP = 512                   # D-128: each near frame <= 512^2 (and <= 1 MB)
NEAR_KMAX = 8.0                  # at most 8x the D-098 resolution
NEAR_PAD = 10                    # px around the disc on the near frame (the ink + its jitter), not scaled
NEAR_MIN_GAIN = 2.0              # D-128 amended: a near frame only where it is >= 2x the far disc (Luna, Mercury, Mars, Venus, Earth)


def near_scale(name, cap=None):
    """The near frame's scale vs the far disc: min(8x, the largest that fits cap^2); under NEAR_MIN_GAIN, no near frame."""
    R = RADIUS_U[name] * SPACE_PPU
    return min(NEAR_KMAX, (((cap or NEAR_CAP) // 4) * 4 / 2 - NEAR_PAD) / R)


def build_near(name, cap=None):
    """-> (frame RGBA uint8, k) or (None, k) when the cap leaves less than NEAR_MIN_GAIN (the giants: a later card)."""
    k = near_scale(name, cap)
    if k < NEAR_MIN_GAIN:
        return None, k
    R = RADIUS_U[name] * SPACE_PPU
    d = NearDisc(name, R, k, NEAR_PAD, seed=zlib.crc32(name.encode()) % 1000)
    rgb, ink, rgba = paint(name, d, 0, FRAMES.get(name, 12))
    return finish(d, rgb, ink, rgba), k


def finish(d, rgb, extra_ink=(), extra_rgba=()):
    """Paint -> premultiplied canvas: disc colour (+ grain), extra rgba layers, outline ink,
    extra ink strokes [(pts_px_at_ss, width_px_1x)]; box-down to 1x straight alpha uint8."""
    n = d.size * SS
    a = d.inside.astype(np.float32)
    col = np.clip(rgb * (d.grain * d.pig)[..., None], 0, 1) * a[..., None]
    acc = np.dstack([col, a])
    for lay in extra_rgba:                      # rgba float layers over the disc (rings front etc.)
        la = lay[..., 3:4]
        acc[..., :3] = lay[..., :3] * la + acc[..., :3] * (1 - la)
        acc[..., 3:] = la + acc[..., 3:] * (1 - la)
    ink = PAL["ink"]
    t = np.linspace(0, 2 * np.pi, int(160 * max(1.0, d.R / getattr(d, "R_base", d.R))), endpoint=False)
    ux = np.cos(t)
    vy = np.sin(t)
    k = d.R * SS
    c = n / 2
    rimv = np.array([d.rim[int(np.clip(c - vv * k, 0, n - 1)), int(np.clip(c + uu * k, 0, n - 1))] for uu, vv in zip(ux, vy)])
    px, py = c + ux * rimv * k, c - vy * rimv * k
    strokes = [(px, py, OUT_PX, True)] + [(p[:, 0], p[:, 1], w, False) for p, w in extra_ink]
    for i, (sx, sy, w, cyc) in enumerate(strokes):
        xz = np.c_[sx, -sy] / (SS * 64.0)        # jitter along arclength in "metres" at 64 px/m
        r = GR.jittered_radius(xz, np.full(len(sx), w / 2 / 64.0), 977 * i + len(sx), 64.0) * 64.0 * SS
        WIDTHS.append((w, float(r.min()) * 2 / SS, float(r.max()) * 2 / SS))
        m = GR._ink_mask(sx, sy, r, cyc, n, n).astype(np.float32)[..., None]
        acc[..., :3] = ink * m + acc[..., :3] * (1 - m)
        acc[..., 3:] = m + acc[..., 3:] * (1 - m)
    small = acc.reshape(d.size, SS, d.size, SS, 4).mean(axis=(1, 3))
    al = small[..., 3:4]
    rgbo = np.where(al > 1e-6, small[..., :3] / np.maximum(al, 1e-6), 0)
    return np.clip(np.rint(np.dstack([rgbo, al]) * 255), 0, 255).astype(np.uint8)


def bands(d, spec, phase, wob=0.05, freq=3.0):
    """Horizontal bands: spec [(v_top, colour)] from the top; edges wobble with u + phase."""
    v = d.v + wob * np.sin(freq * np.pi * d.u + phase) * (1 - d.v ** 2)
    out = np.zeros(d.u.shape + (3,), np.float32)
    out[:] = spec[-1][1]
    for vt, col in reversed(spec):
        out[v <= vt] = out[v <= vt]
    for i, (vt, col) in enumerate(spec):
        lo = spec[i + 1][0] if i + 1 < len(spec) else -2
        out[(v <= vt) & (v > lo)] = col
    return out


def sphere_u(d, shift):
    """Surface longitude coordinate for features that rotate across the disc (periodic)."""
    s = np.arcsin(np.clip(d.u / np.sqrt(np.maximum(1 - d.v ** 2, 1e-6)), -1, 1)) / np.pi   # -0.5..0.5 on the face
    return (s + shift) % 1.0


def blobs(d, pts, su):
    m = np.zeros(d.u.shape, bool)
    for (lon, lat, rad) in pts:
        dl = np.minimum(np.abs(su - lon), 1 - np.abs(su - lon)) * np.pi * np.sqrt(np.maximum(1 - d.v ** 2, 0))
        m |= (dl ** 2 + (d.v - lat) ** 2) < rad ** 2
    return m


def paint(name, d, f, nf):
    t = f / nf
    rng = np.random.default_rng(91 + zlib.crc32(name.encode()) % 7)
    nightm = d.inside & (np.hypot(d.u - 0.30, d.v - 0.30) > 1.06)  # curved terminator: night crescent lower left
    extra_ink, extra_rgba = [], []
    if name == "mercury":
        base = mix(PAL["brown"], PAL["offwhite"], 0.55)
        rgb = np.broadcast_to(base, d.u.shape + (3,)).copy()
        su = sphere_u(d, t * 0.25)
        cr = [(rng.uniform(0, 1), rng.uniform(-0.8, 0.8), rng.uniform(0.07, 0.18)) for _ in range(14)]
        m = blobs(d, cr, su)
        rgb[m] = shade(base)
        rim = blobs(d, [(a, b, c * 0.75) for a, b, c in cr], su)
        rgb[m & ~rim] = mix(base, PAL["offwhite"], 0.4)
    elif name == "venus":
        a, b = mix(PAL["mustard"], PAL["offwhite"], 0.55), mix(PAL["mustard"], PAL["offwhite"], 0.25)
        vv = d.v + 0.22 * np.abs(d.u) ** 1.6 + 0.06 * np.sin(2 * np.pi * (sphere_u(d, t) * 2))
        rgb = np.where((np.floor(vv * 4.5) % 2 == 0)[..., None], a, b)
    elif name == "earth" or name == "luna":
        if name == "luna":
            base = mix(PAL["offwhite"], PAL["sky"], 0.35)
            rgb = np.broadcast_to(base, d.u.shape + (3,)).copy()
            m = blobs(d, [(0.2, 0.3, 0.25), (0.45, -0.1, 0.3), (0.05, -0.4, 0.2)], sphere_u(d, 0.0))
            rgb[m] = shade(base)
        else:
            rgb = np.broadcast_to(PAL["teal"], d.u.shape + (3,)).copy()
            su = sphere_u(d, t * 0.5)
            land = blobs(d, [(0.10, 0.35, 0.30), (0.18, 0.05, 0.22), (0.22, -0.35, 0.28), (0.52, 0.40, 0.34),
                             (0.60, -0.05, 0.25), (0.78, 0.30, 0.22), (0.83, -0.45, 0.2)], su)
            rgb[land] = PAL["green"]
            dry = land & blobs(d, [(0.20, -0.30, 0.15), (0.58, 0.30, 0.15)], su)
            rgb[dry] = mix(PAL["green"], PAL["mustard"], 0.5)
            rgb[np.abs(d.v) > 0.84 + 0.04 * np.sin(9 * d.u + 1.3)] = PAL["offwhite"]
            streaks = [(lon + 0.012 * j, lat + 0.03 * math.sin(0.5 * j), 0.075) for lon, lat in
                       ((0.05, 0.55), (0.30, -0.15), (0.48, 0.12), (0.70, -0.60), (0.90, 0.25)) for j in range(-8, 9)]
            cl = blobs(d, streaks, sphere_u(d, t * 0.75 + 0.1))
            rgb[cl] = PAL["offwhite"]
    elif name == "mars":
        base = mix(PAL["red"], PAL["mustard"], 0.25)
        rgb = np.broadcast_to(base, d.u.shape + (3,)).copy()
        su = sphere_u(d, t * 0.5)
        rgb[blobs(d, [(0.1, 0.2, 0.25), (0.35, -0.2, 0.3), (0.62, 0.1, 0.22), (0.85, -0.3, 0.2)], su)] = shade(base)
        rgb[d.v > 0.80] = PAL["offwhite"]
        rgb[d.v < -0.88] = mix(PAL["offwhite"], base, 0.3)
    elif name == "jupiter":
        ph = 2 * np.pi * t
        spec = [(1.1, mix(PAL["offwhite"], PAL["mustard"], 0.3)), (0.62, mix(PAL["brown"], PAL["mustard"], 0.45)),
                (0.42, PAL["offwhite"]), (0.18, mix(PAL["mustard"], PAL["red"], 0.25)), (-0.05, PAL["offwhite"]),
                (-0.25, mix(PAL["brown"], PAL["red"], 0.35)), (-0.52, mix(PAL["offwhite"], PAL["mustard"], 0.4)),
                (-0.75, mix(PAL["brown"], PAL["mustard"], 0.5))]
        rgb = bands(d, spec, ph, wob=0.045, freq=4.0)
        su = sphere_u(d, t * 0.35)
        spot = blobs(d, [(0.25, -0.38, 0.13)], su)
        rgb[spot] = PAL["red"]
    elif name == "saturn":
        spec = [(1.1, mix(PAL["mustard"], PAL["offwhite"], 0.6)), (0.5, mix(PAL["mustard"], PAL["offwhite"], 0.3)),
                (0.15, mix(PAL["mustard"], PAL["offwhite"], 0.55)), (-0.2, mix(PAL["mustard"], PAL["brown"], 0.15)),
                (-0.6, mix(PAL["mustard"], PAL["offwhite"], 0.5))]
        rgb = bands(d, spec, 2 * np.pi * t, wob=0.025, freq=3.0)
    elif name == "uranus":
        rgb = bands(d, [(1.1, mix(PAL["sky"], PAL["teal"], 0.2)), (0.3, mix(PAL["sky"], PAL["offwhite"], 0.3)),
                        (-0.3, mix(PAL["sky"], PAL["teal"], 0.3))], 2 * np.pi * t, wob=0.02)
    elif name == "neptune":
        rgb = bands(d, [(1.1, PAL["teal"]), (0.35, mix(PAL["teal"], PAL["sky"], 0.4)), (-0.1, PAL["teal"]),
                        (-0.5, mix(PAL["teal"], PAL["brown"], 0.25))], 2 * np.pi * t, wob=0.03)
        rgb[blobs(d, [(0.22, -0.25, 0.12)], sphere_u(d, t * 0.4))] = shade(PAL["teal"])
        # no face (D-101): a bright companion cloud trails the dark storm as both drift
        rgb[blobs(d, [(0.30 + 0.011 * j, -0.12 + 0.004 * j, 0.032) for j in range(-8, 9)], sphere_u(d, t * 0.4))] = \
            mix(PAL["offwhite"], PAL["sky"], 0.3)
    rgb = np.asarray(rgb, np.float32)
    rgb[nightm] = shade(rgb[nightm])
    extra_ink = list(extra_ink) + interior_marks(name, d, f, nf)
    return rgb, extra_ink, extra_rgba


BAND_EDGES = {"jupiter": (0.62, 0.42, 0.18, -0.05, -0.25, -0.52), "saturn": (0.5, 0.15, -0.2),
              "uranus": (0.3, -0.3), "neptune": (0.35, -0.1)}


def interior_marks(name, d, f, nf):
    """v3.1 (D-100) interior line work: two small hatch groups in the night crescent, and on the
    giants a few short band-edge fragments that drift with the bands (in px at SS)."""
    k, c = d.R * SS, d.size * SS / 2
    marks = []
    L = max(0.10, 6.0 / getattr(d, "R_base", d.R))   # at least ~6 px long on the small far discs (kept on near frames)
    for (u0, v0) in ((-0.62, -0.42), (-0.30, -0.80)):
        for j in range(3):
            uu, vv = u0 + 0.06 * j, v0 + 0.06 * j
            if uu * uu + vv * vv > 0.86:
                continue
            marks.append((np.array([(c + (uu - L / 2) * k, c - (vv - L / 2) * k), (c + (uu + L / 2) * k, c - (vv + L / 2) * k)]), IN_PX))
    ph = 2 * np.pi * f / nf
    for vb in BAND_EDGES.get(name, ()):
        for u0 in (-0.35, 0.25):
            uu = u0 + 0.05 * math.sin(ph + vb * 7)
            if (abs(uu) + 0.22) ** 2 + vb * vb > 0.9:
                continue
            pts = [(c + (uu + t_) * k, c - (vb + 0.04 * math.sin(4.0 * (uu + t_) + ph)) * k) for t_ in np.linspace(0, 0.22, 6)]
            marks.append((np.array(pts), IN_PX))
    return marks


LIMB_PX = 2.0                    # B-143: the soft alpha limb's width in texels


def soft_limb(img, width=LIMB_PX, solid=250):
    """B-143: a soft alpha limb OUTSIDE the silhouette, so near-range bilinear zoom (10x at space_6) draws a round edge, not
    1-texel stairs. Every pixel with alpha >= `solid` stays byte-identical (the ink and the fill); a pixel outside gets
    alpha max(its own, ramp(distance to the nearest solid pixel)), ramp = 1 - (d - 0.5) / width (0.75 at d 1, ~0.25 at 2),
    and a fully transparent one takes the ink colour (the outline is the outermost thing on every disc and ring edge)."""
    a = img[..., 3]
    S = a >= solid
    H, W = a.shape
    k = int(np.ceil(width + 0.5))
    P = np.pad(S, k)
    dist = np.full((H, W), np.inf, np.float32)
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            d = (dx * dx + dy * dy) ** 0.5
            if 0 < d <= width + 0.5:
                hit = P[k + dy:k + dy + H, k + dx:k + dx + W]
                dist = np.where(hit & (d < dist), np.float32(d), dist)
    ramp = np.clip(1.0 - (dist - 0.5) / width, 0.0, 1.0)
    want = np.rint(ramp * 255).astype(np.uint8)
    out = img.copy()
    grow = (~S) & (want > a)
    empty = grow & (a == 0)
    ink = np.rint(PAL["ink"] * 255).astype(np.uint8)
    out[empty, :3] = ink
    out[grow, 3] = want[grow]
    return out


def saturn_rings(R, tilt=0.30, limb=False):       # limb: B-143's soft limb, SHELVED by D-128's amendment (see build_disc)
    """Rings as two static parts (back = the half behind the body, front = in front): bands
    1.24-2.27 R with the Cassini gap, ink on the outer and inner edges. -> (back, front) uint8."""
    Rr = 2.27 * R
    W = int(2 * Rr + 24)
    W += (-W) % 4
    H = int(2 * Rr * tilt + 24)
    H += (-H) % 4
    n_w, n_h = W * SS, H * SS
    yy, xx = np.mgrid[0:n_h, 0:n_w] + 0.5
    u = (xx - n_w / 2) / (R * SS)
    v = (yy - n_h / 2) / (R * SS * tilt)
    rr = np.hypot(u, v)
    ring = (rr >= 1.24) & (rr <= 2.27) & ~((rr > 1.95) & (rr < 2.03))
    col = np.zeros((n_h, n_w, 3), np.float32)
    col[:] = mix(PAL["mustard"], PAL["offwhite"], 0.55)
    col[(rr > 1.55) & (rr < 1.95)] = mix(PAL["mustard"], PAL["offwhite"], 0.25)
    col[(rr > 2.03)] = mix(PAL["brown"], PAL["mustard"], 0.5)
    acc = np.dstack([col * ring[..., None], ring.astype(np.float32)])
    t = np.linspace(0, 2 * np.pi, 220, endpoint=False)
    for i, rad in enumerate((2.27, 1.24)):
        px = n_w / 2 + np.cos(t) * rad * R * SS
        py = n_h / 2 + np.sin(t) * rad * R * SS * tilt
        xz = np.c_[px, -py] / (SS * 64.0)
        w = OUT_PX if i == 0 else IN_PX
        r = GR.jittered_radius(xz, np.full(len(px), w / 2 / 64.0), 31 + i, 64.0) * 64.0 * SS
        WIDTHS.append((w, float(r.min()) * 2 / SS, float(r.max()) * 2 / SS))
        m = GR._ink_mask(px, py, r, True, n_h, n_w).astype(np.float32)[..., None]
        acc[..., :3] = PAL["ink"] * m + acc[..., :3] * (1 - m)
        acc[..., 3:] = m + acc[..., 3:] * (1 - m)
    small = acc.reshape(H, SS, W, SS, 4).mean(axis=(1, 3))
    al = small[..., 3:4]
    img = np.clip(np.rint(np.dstack([np.where(al > 1e-6, small[..., :3] / np.maximum(al, 1e-6), 0), al]) * 255), 0, 255).astype(np.uint8)
    if limb:                                   # B-143: before the split, so the cut line is never feathered twice
        img = soft_limb(img)
    back, front = img.copy(), img.copy()
    back[H // 2:] = 0                          # upper half passes behind the body
    front[:H // 2] = 0
    return back, front


def build_disc(name, limb=False):
    """The far disc's frames. limb=True adds B-143's soft alpha limb, which D-128's amendment SHELVED ("code kept, never
    run", c43c8da3): the exported far discs have none. B-239 (11-09): the default was still True, so export() and the
    review would have re-drawn every far disc's limb (about 4,000 pixels a Jupiter frame: the first proof run's finding);
    it is False now, and only b143() asks for the limb."""
    R = RADIUS_U[name] * SPACE_PPU
    nf = FRAMES.get(name, 12)
    pad = 10 if name != "uranus" else 10
    frames = []
    for f in range(nf):
        d = Disc(name, R, pad, seed=zlib.crc32(name.encode()) % 1000)
        rgb, ink, rgba = paint(name, d, f, nf)
        im = finish(d, rgb, ink, rgba)
        frames.append(soft_limb(im) if limb else im)
    return frames, R


def sheet_meta(key, frames, R_px, name):
    fw = frames[0].shape[1]
    cols = v3.columns_for(fw, len(frames))
    return {"key": key, "style": "v3", "frame_width": fw, "frame_height": frames[0].shape[0], "columns": cols,
            "gutter": v3.GUTTER, "frames": len(frames), "fps": v3.FPS, "pivot": [0.5, 0.5], "facing": "right",
            "ppu": SPACE_PPU, "space_ppu": SPACE_PPU, "radius_u": RADIUS_U[name], "radius_px": round(R_px, 1),
            "animations": [{"name": "idle", "start": 0, "length": len(frames), "loop": True, "loop_from": 0}]}


ORDER = ["mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"]


def export(art, preview_dir, stamp=None, prebuilt=None):
    """D-098 / contract §11.5: planets/<planet>/disc_color.png + disc.json (Luna: planets/earth/
    luna_*), Saturn's rings_back / rings_front + disc_rig.json; validated; then the review sheet
    (built from the same frames). Returns [(key, w, h, frames, kb)]."""
    import json as _json
    out = []
    tiles = {}
    for name in ORDER + ["luna"]:
        frames, R = prebuilt[name] if prebuilt else build_disc(name)
        tiles[name] = (frames, R)
        planet, variant = ("earth", "luna") if name == "luna" else (name, "disc")
        key = f"planets/{planet}/{variant}"
        meta = sheet_meta(key, frames, R, name)
        sheet = pack(frames, meta["columns"])
        probs = v3.validate_sheet(meta, sheet.shape, ppu=SPACE_PPU)
        if probs:
            raise ValueError(f"{key}: " + "; ".join(probs))
        d = os.path.join(art, "planets", planet)
        os.makedirs(d, exist_ok=True)
        n = pngio.write_png(os.path.join(d, f"{variant}_color.png"), sheet)
        if n > v3.MAX_FILE_BYTES:
            raise ValueError(f"{key}: {n / 2**20:.1f} MB over 4 MB")
        with open(os.path.join(d, f"{variant}.json"), "w", encoding="utf-8", newline="\n") as f:
            _json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((key, sheet.shape[1], sheet.shape[0], len(frames), n // 1024))
    back, front = prebuilt["_rings"] if prebuilt else saturn_rings(RADIUS_U["saturn"] * SPACE_PPU)
    d = os.path.join(art, "planets", "saturn")
    for nm, im in (("rings_back", back), ("rings_front", front)):
        n = pngio.write_png(os.path.join(d, f"{nm}_color.png"), im)
        with open(os.path.join(d, f"{nm}.json"), "w", encoding="utf-8", newline="\n") as f:
            _json.dump({"key": f"planets/saturn/{nm}", "style": "v3", "ppu": SPACE_PPU, "space_ppu": SPACE_PPU,
                        "radius_u": RADIUS_U["saturn"], "pivot": [0.5, 0.5]}, f, indent=2)
            f.write("\n")
        out.append((f"planets/saturn/{nm}", im.shape[1], im.shape[0], 1, n // 1024))
    rig = {"key": "planets/saturn/disc_rig", "style": "v3", "space_ppu": SPACE_PPU,
           "parts": [{"name": "rings_back", "order": 0, "pivot": [0.5, 0.5]}, {"name": "disc", "order": 1},
                     {"name": "rings_front", "order": 2, "pivot": [0.5, 0.5]}],
           "wobble": {"parts": ["rings_back", "rings_front"], "scale_y": 0.04, "rotate_deg": 1.5, "beat_bpm": 110,
                      "stepped_hz": 12}}
    with open(os.path.join(d, "disc_rig.json"), "w", encoding="utf-8", newline="\n") as f:
        _json.dump(rig, f, indent=2)
        f.write("\n")
    return out, tiles


def pack(frames, cols, gutter=v3.GUTTER):
    fh, fw = frames[0].shape[:2]
    rows = -(-len(frames) // cols)
    c = min(cols, len(frames))
    s = np.zeros((rows * fh + (rows - 1) * gutter, c * fw + (c - 1) * gutter, 4), np.uint8)
    for i, f in enumerate(frames):
        r, k = divmod(i, cols)
        s[r * (fh + gutter):r * (fh + gutter) + fh, k * (fw + gutter):k * (fw + gutter) + fw] = f
    return s


OURS = {
    "mercury": "a pocked grey-brown pebble turning slowly, craters drawn with rims",
    "venus": "cream-and-mustard chevron cloud bands drifting across a hidden world",
    "earth": "teal seas, dusty-green land and streaky clouds turning at two speeds, Luna at its shoulder",
    "mars": "rust-red with darker plains and a white polar cap, turning",
    "jupiter": "wavy mustard, cream and brown bands that swirl, the red spot drifting",
    "saturn": "pale banded body inside two-piece rings that wobble on the beat",
    "uranus": "soft sky-teal bands, quiet and pale",
    "neptune": "deep teal bands with a dark storm wandering and a bright cloud trailing it",
}


def preview(out_dir, tiles=None, out_name="review_b119_discs_preview.png", stamp_paths=()):
    """Contract §11.7 review for the disc set: (1) all eight at the space scale (+ Luna, Saturn's
    two ring parts, sized so the rings never overlap a neighbour), (2) every frame of every disc as
    a numbered strip (2x for the small discs, 1x for Jupiter and Saturn, wrapped), (3) a panel with
    the palette (colour, mid, deep), the measured ink widths, the ten §9.7 boxes and one "ours" line
    per disc. tiles: frames already built by export(); stamp_paths: exported PNGs to stamp."""
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    if tiles is None:
        tiles = {}
        for name in ORDER + ["luna"]:
            frames, R = build_disc(name)
            tiles[name] = (frames, R)
            print(name, len(frames), frames[0].shape, f"{time.time() - t0:.1f}s", flush=True)
    back, front = saturn_rings(RADIUS_U["saturn"] * SPACE_PPU)
    bg = mix(PAL["ink"], PAL["teal"], 0.18)
    sw = tiles["saturn"][0][0].shape[1]
    ov = max(0, back.shape[1] // 2 - sw // 2)          # ring overhang on each side of Saturn's frame
    H = max(760, back.shape[0] + 80, max(tiles[n][0][0].shape[0] for n in ORDER) + 80)
    W = 16 + sum(tiles[n][0][0].shape[1] + 24 for n in ORDER) + 2 * ov + 16
    canvas = np.zeros((H, W, 3), np.float32)
    canvas[:] = bg
    x = 16
    for n in ORDER:
        fr = tiles[n][0][0]
        h, w = fr.shape[:2]
        if n == "saturn":
            x += ov
        y = H // 2 - h // 2
        if n == "saturn":
            bh, bw = back.shape[:2]
            review._over(canvas, back, x + w // 2 - bw // 2, H // 2 - bh // 2)
        review._over(canvas, fr, x, y)
        if n == "saturn":
            review._over(canvas, front, x + w // 2 - bw // 2, H // 2 - bh // 2)
        if n == "earth":
            lf = tiles["luna"][0][0]
            review._over(canvas, lf, x + w - 10, max(0, y - lf.shape[0] // 2))
        review.draw(canvas, n, x, 8, (1.0, 0.97, 0.85))
        x += w + 24 + (ov if n == "saturn" else 0)
    review.draw(canvas, f"planet discs at the space scale ({SPACE_PPU:g} px per unit, D-098), frame 0 each; sky = placeholder",
                8, H - 18, (1.0, 0.97, 0.85))
    u8 = lambda a: np.clip(np.rint(a * 255), 0, 255).astype(np.uint8)   # panels go to uint8 as they finish (peak RAM)
    rows = [u8(canvas)]
    del canvas
    # every frame of every clip, numbered (contract §11.7), wrapped
    for n in ORDER + ["luna"]:
        frs = tiles[n][0]
        fh, fw = frs[0].shape[:2]
        sc = 1 if n in ("jupiter", "saturn") else 2
        per = max(1, (W - 16) // (fw * sc + 8))
        for r0 in range(0, len(frs), per):
            row = np.tile(bg, (fh * sc + 30, W, 1)).astype(np.float32)
            for j, fr in enumerate(frs[r0:r0 + per]):
                xx = 8 + j * (fw * sc + 8)
                review._over(row, np.repeat(np.repeat(fr, sc, 0), sc, 1), xx, 26)
                review.draw(row, f"{n} idle {r0 + j}", xx, 6, (1.0, 0.97, 0.85))
            rows.append(u8(row))
    # panel: palette, measured widths, ten boxes, ours per disc
    from meridian import v3
    panel = np.tile(review.PAPER, (420, W, 1)).astype(np.float32)
    pal = v3.PALETTES["earth"]
    review._label(panel, "palette earth (space discs): colour, mid shadow, deep shadow", 8, 6)
    for i, kname in enumerate(v3.PALETTE_ORDER):
        xx = 8 + i * 46
        panel[26:62, xx:xx + 40] = review._hexf(pal[kname])
        if kname != "ink":
            panel[64:80, xx:xx + 40] = review._hexf(v3.shadow_of(pal[kname]))
            panel[82:98, xx:xx + 40] = review._hexf(v3.deep_of(pal[kname]))
    outer = [w for w in WIDTHS if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in WIDTHS if w[0] < v3.OUTER_SPLIT]
    ow = (min(w[1] for w in outer), max(w[2] for w in outer)) if outer else (0, 0)
    iw = (min(w[1] for w in inner), max(w[2] for w in inner)) if inner else (0, 0)
    ink_ok = bool(outer) and bool(inner) and v3.OUTER_PX[0] - 0.05 <= ow[0] and ow[1] <= v3.OUTER_PX[1] + 0.05 \
        and v3.INNER_PX[0] - 0.05 <= iw[0] and iw[1] <= v3.INNER_PX[1] + 0.05
    review._label(panel, f"measured ink: outer {ow[0]:.1f}-{ow[1]:.1f} px (2-3), interior {iw[0]:.1f}-{iw[1]:.1f} px (1-1.5), "
                         f"{len(inner)} interior marks over all frames", 8, 108)
    res = {"ink": ("x" if ink_ok else "!", "measured; night-side hatching + band-edge fragments"),
           "cel": ("s", "watercolour fill per contract §11.5 (bands, caps, spots), one night tone"),
           "face": ("s", "no faces or expressions on any planet (D-101)"),
           "twos": ("x", "12 fps; 12 frames, Jupiter and Saturn 9 (D-098)"),
           "motion": ("s", "bands swirl, clouds and storms drift, Saturn's rings wobble via disc_rig.json"),
           "idle": ("x", "every disc loops an idle"),
           "original": ("s", "the real planets, painted; no existing character"),
           "sheet": ("x", "sheets + disc.json validated (space_ppu 3), ring parts with v3 sidecars"),
           "budget": ("x", "every sheet <= 2048, <= 4 MB"),
           "style": ("s", "C1 space art; LEAD judges against the C0 reference")}
    review._label(panel, "bible 4.1 9.7 ten-box checklist", 8, 132)
    for i, (key, text) in enumerate(review.BOXES):
        mark, note = res[key]
        review._label(panel, f"[{mark}] {text}  -  {note}"[:150], 8, 150 + i * 16)
    for i, n in enumerate(ORDER):
        review._label(panel, f"ours, {n}: {OURS[n]}"[:150], 8 + (i % 2) * (W // 2), 320 + (i // 2) * 16)
    rows.append(u8(panel))
    # per-disc ten-box table: one row per disc, one column per §9.7 box (x measured, s self-check)
    tbl = np.tile(review.PAPER, (40 + 18 * (len(ORDER) + 1), W, 1)).astype(np.float32)
    keys = [k for k, _t in review.BOXES]
    review._label(tbl, "per-disc ten-box table   " + "  ".join(f"{i + 1}:{k}" for i, k in enumerate(keys)), 8, 6)
    for r, n in enumerate(ORDER + ["luna"]):
        nf = len(tiles[n][0])
        fw_ = tiles[n][0][0].shape[1]
        marks = {"ink": res["ink"][0], "cel": "s", "face": "s", "twos": "x" if nf <= 12 else "!", "motion": "s",
                 "idle": "x", "original": "s", "sheet": "x", "budget": "x" if fw_ * min(nf, 3) <= 2048 else "!", "style": "s"}
        cells = "".join(f"[{marks[k]}]" for k in keys)
        review._label(tbl, f"{n:8s} {cells}  {nf} frames {fw_}px  no face; " + OURS.get(n, "Earth's moon, slowly turning")[:70], 8, 26 + 18 * r)
    rows.append(u8(tbl))
    if stamp_paths:                                  # one stamp per exported sheet in its own small panel
        sp = np.tile(review.PAPER, (18 * len(stamp_paths) + 4, W, 1)).astype(np.float32)
        for i, p in enumerate(stamp_paths):
            review.draw(sp, os.path.relpath(p, review.ART).replace("\\", "/") + " " + review.stamp_text(p), 4, 2 + 18 * i, (1.0, 1.0, 0.85))
        rows.append(u8(sp))
    img = np.vstack(rows)
    del rows
    pngio.write_png(os.path.join(out_dir, out_name), np.dstack([img, np.full(img.shape[:2], 255, np.uint8)]))
    print("review written", img.shape, f"{time.time() - t0:.1f}s", "ink", ow, iw, len(inner))


def near_export(art, preview_dir, review=None, cap=None, write=True):
    """B-143 (D-128): planets/<planet>/disc_near_color.png + disc_near.json (Luna: planets/earth/luna_near), one static frame
    each (frame 0 of the idle at k x), <= cap^2 and <= 1 MB; proves first that the far frames re-render byte-identical
    to the committed sheets (the far path is untouched); the review shows each near frame beside its far disc at ~33x."""
    import json as _json
    out, nears, problems = [], {}, []
    for name in ORDER + ["luna"]:
        planet, variant = ("earth", "luna") if name == "luna" else (name, "disc")
        old = _old_frames(art, planet, variant)
        far, _R = build_disc(name, limb=False)
        if not all(o.shape == f.shape and (o == f).all() for o, f in zip(old, far)):
            problems.append(f"{planet}/{variant}: the far frames no longer re-render byte-identical")
        im, k = build_near(name, cap)
        if im is None:
            out.append((f"planets/{planet}/{variant}_near", 0, 0, 0, k))
            continue
        nears[name] = (im, k, old[0])
        key = f"planets/{planet}/{variant}_near"
        meta = {"key": key, "style": "v3", "frame_width": im.shape[1], "frame_height": im.shape[0], "columns": 1, "gutter": v3.GUTTER,
                "frames": 1, "fps": v3.FPS, "pivot": [0.5, 0.5], "facing": "right", "ppu": round(SPACE_PPU * k, 4),
                "space_ppu": round(SPACE_PPU * k, 4), "radius_u": RADIUS_U[name], "radius_px": round(RADIUS_U[name] * SPACE_PPU * k, 1),
                "near_of": f"planets/{planet}/{variant}", "scale_vs_far": round(k, 4), "animations": [],
                "note": f"D-128: the far disc's frame 0 at {k:.2f}x for near-range zoom (DiscSprite swaps above ~6x); a static frame"}
        bad = [m for m in v3.validate_sheet(meta, im.shape, ppu=meta["ppu"]) if "sum of clip lengths" not in m]
        if im.shape[0] > (cap or NEAR_CAP) or im.shape[1] > (cap or NEAR_CAP):
            bad.append(f"{im.shape[1]}x{im.shape[0]} over {cap or NEAR_CAP}^2")
        problems += [f"{key}: {b}" for b in bad]
        out.append((key, im.shape[1], im.shape[0], meta, k))
    if problems:
        raise ValueError("B-143 near frames: " + "; ".join(problems))
    rows = []
    for i, (key, w, h, meta, k) in enumerate(out):
        if not w:
            rows.append((key, None, k))
            continue
        planet, nm = key.split("/")[1], key.split("/")[2]
        name = "luna" if nm == "luna_near" else planet
        dd = os.path.join(art, "planets", planet) if write else os.path.join(preview_dir, "b143_near")
        os.makedirs(dd, exist_ok=True)
        n = pngio.write_png(os.path.join(dd, f"{nm}_color.png"), nears[name][0])
        if n > 1024 * 1024:
            raise ValueError(f"{key}: {n / 2**20:.2f} MB over 1 MB")
        with open(os.path.join(dd, f"{nm}.json"), "w", encoding="utf-8", newline="\n") as f:
            _json.dump(meta, f, indent=2)
            f.write("\n")
        rows.append((key, (w, h, n), k))
    if review:
        near_review(review, nears, rows, stamp="export" if write else "dry run (not exported)")
    return rows


def _zoom_crop(img, zoom, cx, cy, size):
    """A size x size window of img magnified `zoom`x with bilinear filtering (a GPU sampler's look), centred on (cx, cy)."""
    ys, xs = np.mgrid[0:size, 0:size] + 0.5
    x = cx + (xs - size / 2) / zoom - 0.5
    y = cy + (ys - size / 2) / zoom - 0.5
    f = img.astype(np.float32) / 255
    pm = np.dstack([f[..., :3] * f[..., 3:], f[..., 3:]])
    H, W = img.shape[:2]
    x0, y0 = np.clip(np.floor(x).astype(int), 0, W - 1), np.clip(np.floor(y).astype(int), 0, H - 1)
    x1, y1 = np.clip(x0 + 1, 0, W - 1), np.clip(y0 + 1, 0, H - 1)
    fx, fy = np.clip(x - np.floor(x), 0, 1)[..., None], np.clip(y - np.floor(y), 0, 1)[..., None]
    o = (pm[y0, x0] * (1 - fx) + pm[y0, x1] * fx) * (1 - fy) + (pm[y1, x0] * (1 - fx) + pm[y1, x1] * fx) * fy
    bg = np.array([0.10, 0.10, 0.16], np.float32)
    return o[..., :3] + bg * (1 - o[..., 3:])


def near_review(path, nears, rows, stamp):
    """Per disc: the far frame 0 and the near frame magnified so the disc is ~33x the far texel size on screen, over the
    same limb window (upper right, where the light catches the ink), bilinear like the GPU; and the near frame whole."""
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    S = 360
    W = 8 + S + 12 + S + 12 + 380
    out = [np.tile(review.PAPER, (30, W, 1)).astype(np.float32)]
    review._label(out[0], "b-143 (d-128) near frames: far frame 0 at 33x | the near frame at 33/k x (the same screen size) | the near frame whole; bilinear", 6, 8)
    for key, info, k in rows:
        name = "luna" if key.endswith("luna_near") else key.split("/")[1]
        r = np.tile(review.PAPER, (S + 30, W, 1)).astype(np.float32)
        if info is None:
            review._label(r, f"{key}: none (the cap leaves {k:.2f}x, under the 2x floor: the giants' close view is a later card)", 6, 6)
            out.append(r[:40])
            continue
        im, k, far = nears[name]
        R = RADIUS_U[name] * SPACE_PPU
        a = math.radians(40)
        fc = (far.shape[1] / 2 + R * math.cos(a), far.shape[0] / 2 - R * math.sin(a))
        nc = (im.shape[1] / 2 + R * k * math.cos(a), im.shape[0] / 2 - R * k * math.sin(a))
        r[24:24 + S, 8:8 + S] = _zoom_crop(far, 33.0, fc[0], fc[1], S)
        r[24:24 + S, 20 + S:20 + 2 * S] = _zoom_crop(im, 33.0 / k, nc[0], nc[1], S)
        st = -(-im.shape[0] // 340)                     # a whole-frame thumbnail no taller than the 360 px panel
        th = im[::st, ::st]
        review._over(r, th, 32 + 2 * S, 24)
        w, h, n = info
        review._label(r, f"{key} {w}x{h} at {k:.2f}x ({(n or 0) // 1024} kb): far 33x | near {33 / k:.1f}x | whole", 6, 6)
        out.append(r)
    img = np.vstack(out)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " " + stamp, 2, img.shape[0] - 16)
    review.write(path, img)


def _old_frames(art, planet, variant):
    """The committed sheet's frames (B-143's "before")."""
    import json as _json
    m = _json.load(open(os.path.join(art, "planets", planet, f"{variant}.json"), encoding="utf-8"))
    sh = pngio.read_png_np(os.path.join(art, "planets", planet, f"{variant}_color.png"))
    fw, fh, g, c = m["frame_width"], m["frame_height"], m.get("gutter", v3.GUTTER), m["columns"]
    return [sh[(i // c) * (fh + g):(i // c) * (fh + g) + fh, (i % c) * (fw + g):(i % c) * (fw + g) + fw] for i in range(m["frames"])]


def b143(art, preview_dir, report, write=True):
    """B-143 in one run: rebuild every disc + Luna + the ring parts with the soft limb, prove against the committed
    sheets that every pixel solid before is byte-identical and only the limb changed, then (write=True) export and write
    the evidence (a limb-row diff per disc: the centre row's alpha across the left limb, before -> after)."""
    import time as _t
    t0 = _t.time()
    rows, problems, built = [], [], {}
    for name in ORDER + ["luna"]:
        planet, variant = ("earth", "luna") if name == "luna" else (name, "disc")
        old = _old_frames(art, planet, variant)
        frames, R = build_disc(name, limb=True)                 # (the shelved soft limb is this function's whole subject)
        built[name] = (frames, R)
        if len(old) != len(frames) or old[0].shape != frames[0].shape:
            problems.append(f"{name}: shape {old[0].shape} x{len(old)} -> {frames[0].shape} x{len(frames)}")
            continue
        same_in = changed = outside_only = 0
        for o, n in zip(old, frames):
            S = o[..., 3] >= 250
            same_in += int((o[S] == n[S]).all())
            diff = (o != n).any(-1)
            changed += int(diff.sum())
            outside_only += int(not (diff & S).any())
        if same_in != len(frames) or outside_only != len(frames):
            problems.append(f"{name}: solid pixels changed in {len(frames) - same_in} frames")
        o, n = old[0], frames[0]
        cy = o.shape[0] // 2
        xs = np.nonzero(o[cy, :, 3] >= 250)[0]
        x0 = int(xs.min()) if len(xs) else 0
        seg = slice(max(0, x0 - 4), x0 + 2)
        rows.append(f"| {planet}/{variant} | {len(frames)} | {frames[0].shape[1]} | {same_in}/{len(frames)} | {changed // len(frames)} | "
                    f"{' '.join(str(v) for v in o[cy, seg, 3])} | {' '.join(str(v) for v in n[cy, seg, 3])} |")
    back, front = saturn_rings(RADIUS_U["saturn"] * SPACE_PPU, limb=True)
    built["_rings"] = (back, front)
    for nm, im in (("rings_back", back), ("rings_front", front)):
        o = pngio.read_png_np(os.path.join(art, "planets", "saturn", f"{nm}_color.png"))
        S = o[..., 3] >= 250
        ok = o.shape == im.shape and (o[S] == im[S]).all()
        if not ok:
            problems.append(f"saturn/{nm}: solid pixels changed or shape {o.shape} -> {im.shape}")
        cx = o.shape[1] // 2
        col = o[:, cx, 3]
        ys = np.nonzero(col >= 250)[0]
        y0 = int(ys.min()) if len(ys) else 0
        seg = slice(max(0, y0 - 4), y0 + 2)
        rows.append(f"| saturn/{nm} | 1 | {im.shape[1]} | {int(ok)}/1 | {int((o != im).any(-1).sum()) if o.shape == im.shape else -1} | "
                    f"{' '.join(str(v) for v in o[seg, cx, 3])} | {' '.join(str(v) for v in im[seg, cx, 3])} |")
    if problems:
        raise ValueError("B-143 checks: " + "; ".join(problems))
    out = []
    if write:
        out, _tiles = export(art, preview_dir, prebuilt=built)
    with open(report, "w", encoding="utf-8", newline="\n") as f:
        f.write("# B-143 soft alpha limb: evidence (BLENDER, " + _t.strftime("%Y-%m-%d %H:%M") + ")\n\n")
        f.write(f"`build_discs_v3.soft_limb` ({LIMB_PX:.0f} texels, outside the silhouette): every pixel with alpha >= 250 in the\n"
                "committed sheet is byte-identical in the new one (ink and fill); only the limb changed. Limb row = the frame's centre\n"
                "row (a ring part: its centre column, top edge), alpha from 4 px outside the first solid pixel to 1 px inside.\n\n")
        f.write("| key | frames | frame px | solid identical | changed px / frame | limb alpha before | limb alpha after |\n|---|---|---|---|---|---|---|\n")
        f.write("\n".join(rows) + "\n\n")
        f.write(("Exported: " + ", ".join(f"{k} {w}x{h} {kb} KB" for k, w, h, _n, kb in out) if write else "Dry run (nothing written to Assets).")
                + f"\n\n{_t.time() - t0:.0f} s.\n")
    return rows, out


PAINT_FROM_TABLE = False         # B-239: False while paint() still holds the giants' numbers inline (the BEFORE run)


def b239(art, out_dir):
    """B-239's proof and drafts: rebuild the four giants' far discs and Saturn's two ring parts, write each to out_dir and
    compare the written file BYTE FOR BYTE with the exported one under art (and the sheet json's text); then write the
    close.json drafts (GT.close_json) into out_dir. Nothing under art is written. -> (lines, how many differ)."""
    import hashlib
    import json as _json
    os.makedirs(out_dir, exist_ok=True)
    lines, bad = [f"B-239 proof: paint() reads the giants from {'giants_v3.GIANTS' if PAINT_FROM_TABLE else 'its own inline numbers (BEFORE)'}"], 0

    def sha(p):
        with open(p, "rb") as fh:
            return hashlib.sha1(fh.read()).hexdigest()

    def compare(label, new, ref, shape, extra=""):
        nonlocal bad
        a, b = sha(new), sha(ref)
        same = a == b
        note = ""
        if not same:
            bad += 1
            pa, pb = pngio.read_png_np(new), pngio.read_png_np(ref)
            px = pa.shape == pb.shape and bool((pa == pb).all())
            note = " (the pixels are equal: only the file's encoding differs)" if px else (
                f" ({int((pa != pb).any(axis=-1).sum())} pixels differ)" if pa.shape == pb.shape else f" (shape {pa.shape} against {pb.shape})")
        lines.append(f"{label}: {shape[1]}x{shape[0]}{extra}, {os.path.getsize(new)} bytes | rebuilt sha1 {a} | exported sha1 {b} | "
                     + ("BYTE-IDENTICAL" if same else "DIFFERS" + note))

    for name in GT.GIANTS:
        frames, R = build_disc(name)
        key = f"planets/{name}/disc"
        meta = sheet_meta(key, frames, R, name)
        sheet = pack(frames, meta["columns"])
        new = os.path.join(out_dir, f"{name}_disc_color.png")
        pngio.write_png(new, sheet)
        compare(key, new, os.path.join(art, "planets", name, "disc_color.png"), sheet.shape, f", {len(frames)} frames")
        with open(os.path.join(art, "planets", name, "disc.json"), encoding="utf-8") as fh:
            same_json = fh.read() == _json.dumps(meta, indent=2) + "\n"
        lines.append(f"{key}.json: " + ("text identical" if same_json else "TEXT DIFFERS"))
        bad += 0 if same_json else 1
        del frames, sheet
    back, front = saturn_rings(RADIUS_U["saturn"] * SPACE_PPU)
    for nm, im in (("rings_back", back), ("rings_front", front)):
        new = os.path.join(out_dir, f"saturn_{nm}_color.png")
        pngio.write_png(new, im)
        compare(f"planets/saturn/{nm}", new, os.path.join(art, "planets", "saturn", f"{nm}_color.png"), im.shape)
    for name in GT.GIANTS:                                       # the close.json drafts (preview only)
        p = os.path.join(out_dir, f"{name}_close.json")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            _json.dump(GT.close_json(name, PAL, lambda c: v3.rgb_hex([float(x) * 255 for x in c]), RADIUS_U[name], FRAMES.get(name, 12), v3.FPS), fh, indent=2)
            fh.write("\n")
        lines.append(f"draft written: {p.replace(os.sep, '/')}")
    lines.append(f"RESULT: {'all byte-identical' if not bad else str(bad) + ' DIFFER'}")
    return lines, bad


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[1] == "--b239":             # build_discs_v3.py --b239 <art> <out dir>
        _lines, _bad = b239(sys.argv[2], sys.argv[3])
        print("\n".join(_lines))
        sys.exit(1 if _bad else 0)
    if len(sys.argv) > 2 and sys.argv[1] == "--near":            # build_discs_v3.py --near <art> <preview dir> <review png> [--dry]
        for row in near_export(sys.argv[2], sys.argv[3], review=sys.argv[4], write="--dry" not in sys.argv):
            print(row[0], row[1] if row[1] else "none", f"k {row[2]:.2f}")
    elif len(sys.argv) > 2 and sys.argv[1] == "--b143":           # build_discs_v3.py --b143 <art> <preview dir> <report> [--dry]
        print("\n".join(b143(sys.argv[2], sys.argv[3], sys.argv[4], write="--dry" not in sys.argv)[0]))
    else:
        preview(sys.argv[1])
