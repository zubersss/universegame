"""ART v6 "cel on painted" (D-199, docs/STYLE_V6.md section 3): the PAINTING - brush paint, never a drawn line.

Everything that is stage is painted with this module (sky, far and near backdrops, the ground and what is under it).
A picture is built the way a gouache is:
  1. an UNDERPAINTING: soft colour fields (bands, shapes, noise) that say what colour each place is;
  2. the BRUSH: thousands of dabs - each one flat stroke of ONE colour, taken from the underpainting where it lands
     and mixed a little off in value and hue - laid over each other. Every edge is whatever the dabs leave: large and
     soft far away, small and crisp near. Shapes are masks that say where dabs may land; no outline exists anywhere;
  3. LIGHT: warm pools laid over the paint, violet-blue shadow between them;
  4. a fine paper tooth over the whole painting.
numpy only, lock-free. Coordinates are px, y down.
"""
import math

import numpy as np


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def box(a, r):
    """A box blur of radius r px (the edge value repeated beyond the edges)."""
    if r < 1:
        return a
    k = 2 * r + 1
    for axis in (0, 1):
        pad = [(0, 0)] * a.ndim
        pad[axis] = (r + 1, r)
        c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
        n = c.shape[axis]
        a = ((np.take(c, range(k, n), axis=axis) - np.take(c, range(0, n - k), axis=axis)) / k).astype(np.float32)
    return a


def field(h, w, cell, rng, sx=1.0):
    """Smooth noise in [-1, 1] over h x w px, one random value per `cell` px (sx stretches the cells along x)."""
    cx = cell * sx
    gh, gw = int(h / cell) + 3, int(w / cx) + 3
    g = rng.uniform(-1, 1, (gh, gw)).astype(np.float32)
    y, x = np.arange(h, dtype=np.float32) / cell, np.arange(w, dtype=np.float32) / cx
    y0, x0 = y.astype(int), x.astype(int)
    fy, fx = y - y0, x - x0
    fy, fx = (fy * fy * (3 - 2 * fy))[:, None], (fx * fx * (3 - 2 * fx))[None, :]
    a, b, c, d = g[y0][:, x0], g[y0][:, x0 + 1], g[y0 + 1][:, x0], g[y0 + 1][:, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(h, w, cell, rng, octaves=3, sx=1.0):
    out, amp, tot = np.zeros((h, w), np.float32), 1.0, 0.0
    for _ in range(octaves):
        out += amp * field(h, w, cell, rng, sx)
        tot += amp
        amp, cell = amp * 0.5, max(2.0, cell * 0.5)
    return out / tot


def line1(w, cell, rng, octaves=2):
    """Smooth 1-D noise in [-1, 1] along x: a ridge line, a stratum's edge."""
    return fbm(1, w, cell, rng, octaves)[0]


def below(h, w, yline, soft=1.0):
    """The mask of everything below the line y = yline[x] (soft px wide at the edge)."""
    y = np.arange(h, dtype=np.float32)[:, None]
    return np.clip((y - np.asarray(yline, np.float32)[None, :]) / max(soft, 1e-3) + 0.5, 0, 1)


def lerp(a, b, t):
    t = t[..., None] if (np.ndim(t) == 2 and np.ndim(a) in (1, 3)) else t
    return a * (1 - t) + b * t


class Painting:
    """An opaque painting of W x H px (float RGB)."""
    def __init__(self, W, H, seed=1):
        self.W, self.H = W, H
        self.img = np.zeros((H, W, 3), np.float32)
        self.rng = np.random.default_rng(seed)
        self.warp = fbm(H, W, 46.0, self.rng, 3)                # the frame's own noise: shapes borrow it for their edges
        self.fine = fbm(H, W, 9.0, self.rng, 2)
        self.count = 0                                          # dabs laid (the sheet prints it)

    def lay(self, colour, mask):
        """Paint laid flat through a mask (colour: one rgb or an H x W x 3 underpainting)."""
        m = mask[..., None]
        self.img = self.img * (1 - m) + colour * m

    def dab(self, cx, cy, a, b, th, col, alpha=1.0, edge=3.0, streak=0.25):
        """ONE stroke of the brush: a flat oval of one colour, half-length a along th, half-width b; edge: 1 = soft and
        wet, 5 = crisp; streak: how dry its tail and bristles are."""
        R = int(math.ceil(max(a, b))) + 1
        x0, x1, y0, y1 = max(int(cx) - R, 0), min(int(cx) + R + 1, self.W), max(int(cy) - R, 0), min(int(cy) + R + 1, self.H)
        if x1 <= x0 or y1 <= y0:
            return
        dx = np.arange(x0, x1, dtype=np.float32)[None, :] - cx
        dy = np.arange(y0, y1, dtype=np.float32)[:, None] - cy
        c, s = math.cos(th), math.sin(th)
        u, v = (dx * c + dy * s) / a, (-dx * s + dy * c) / b
        m = np.clip((1 - (u * u + v * v)) * edge, 0, 1)
        if streak:
            m = m * (1 - streak * (0.5 + 0.5 * np.sin(v * 8.0 + cx * 0.7)) * np.clip(u + 0.4, 0, 1))
        m = (m * alpha)[..., None]
        sub = self.img[y0:y1, x0:x1]
        self.img[y0:y1, x0:x1] = sub * (1 - m) + col * m
        self.count += 1

    def brush(self, under, where, n, size, aspect=(2.0, 4.0), angle=0.0, spread=0.3, alpha=(0.7, 1.0), jitter=0.05,
              hue=0.012, edge=3.0, streak=0.25, clip=None):
        """n dabs where `where` (H x W, 0..1: how likely a dab lands there) allows. Each takes its colour from `under`
        (an underpainting, or one rgb) at its own centre, a little off in value (jitter) and hue; angle: radians, or a
        function of (x, y). clip: a mask the dab's CENTRE must also be inside (kept simple: dabs may spill a little -
        that spill is the painted edge)."""
        rng = self.rng
        p = where.astype(np.float64).ravel()
        if clip is not None:
            p = p * (clip.ravel() > 0.5)
        tot = p.sum()
        if tot <= 0 or n <= 0:
            return
        idx = np.searchsorted(np.cumsum(p), rng.uniform(0, tot, n))
        idx = np.clip(idx, 0, p.size - 1)
        ys, xs = idx // self.W, idx % self.W
        flat = np.ndim(under) == 1
        for cy, cx in zip(ys, xs):
            a = rng.uniform(*size)
            b = max(0.6, a / rng.uniform(*aspect))
            th = (angle(cx, cy) if callable(angle) else angle) + rng.normal(0, spread)
            col = (under if flat else under[cy, cx]) * (1 + rng.normal(0, jitter)) + rng.normal(0, hue, 3).astype(np.float32)
            self.dab(cx + rng.uniform(-0.5, 0.5), cy + rng.uniform(-0.5, 0.5), a, b, th, np.clip(col, 0, 1), rng.uniform(*alpha), edge, streak)

    def stroke(self, pts, w0, w1, col, edge=4.0, jitter=0.03):
        """A long brush stroke along a polyline (a root, a trunk's plane, a grass blade): dabs laid end to end, the width
        running from w0 to w1."""
        rng = self.rng
        pts = np.asarray(pts, np.float32)
        seg = np.hypot(*np.diff(pts, axis=0).T)
        s = np.r_[0.0, np.cumsum(seg)]
        L = float(s[-1])
        if L < 1e-3:
            return
        step = max(1.0, 0.8 * min(w0, w1) + 0.6)
        n = max(2, int(L / step))
        for i in range(n + 1):
            t = i / n
            x, y = np.interp(t * L, s, pts[:, 0]), np.interp(t * L, s, pts[:, 1])
            j = min(np.searchsorted(s, t * L, side="right"), len(pts) - 1)
            th = math.atan2(pts[j, 1] - pts[j - 1, 1], pts[j, 0] - pts[j - 1, 0])
            w = w0 * (1 - t) + w1 * t
            self.dab(x, y, max(step * 1.2, w), max(0.6, w / 2), th, np.clip(col * (1 + rng.normal(0, jitter)), 0, 1), 1.0, edge, 0.0)

    def blob(self, cx, cy, rx, ry, soft=0.35, wobble=0.35):
        """A soft-edged, uneven oval mask (H x W): a cloud's lobe, a tree's crown, a pool of light."""
        x0, x1 = max(int(cx - rx * 1.6), 0), min(int(cx + rx * 1.6) + 1, self.W)
        y0, y1 = max(int(cy - ry * 1.6), 0), min(int(cy + ry * 1.6) + 1, self.H)
        out = np.zeros((self.H, self.W), np.float32)
        if x1 <= x0 or y1 <= y0:
            return out
        dx = (np.arange(x0, x1, dtype=np.float32)[None, :] - cx) / rx
        dy = (np.arange(y0, y1, dtype=np.float32)[:, None] - cy) / ry
        d = np.sqrt(dx * dx + dy * dy) + wobble * self.warp[y0:y1, x0:x1] + 0.4 * wobble * self.fine[y0:y1, x0:x1]
        out[y0:y1, x0:x1] = np.clip((1 - d) / max(soft, 1e-3), 0, 1)
        return out

    def glaze(self, mask, tint, strength=1.0):
        """A wash over the paint: every colour under the mask times `tint` (shadow: a violet-blue below 1; a pool of
        light: a warm tint above 1)."""
        self.img *= 1 + (mask * strength)[..., None] * (np.array(tint, np.float32) - 1)

    def tooth(self, strength=0.02):
        """A fine paper tooth over the whole painting, nothing coarser."""
        n = box(self.rng.standard_normal((self.H, self.W)).astype(np.float32), 1)
        self.img *= (1 + strength * n / max(float(n.std()), 1e-3))[..., None]

    def done(self):
        return np.clip(self.img, 0, 1)
