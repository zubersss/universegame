"""ART v6 "cel on painted" (D-199, docs/STYLE_V6.md section 3): the PAINTING - brush paint, never a drawn line.

Everything that is stage is painted with this module (sky, far and near backdrops, the ground and what is under it).
A picture is built the way a gouache is:
  1. an UNDERPAINTING: soft colour fields (bands, shapes, noise) that say what colour each place is;
  2. the BRUSH: thousands of dabs - each one flat stroke of ONE colour, taken from the underpainting where it lands
     and mixed a little off in value and hue - laid over each other. Every edge is whatever the dabs leave: large and
     soft far away, small and crisp near. Shapes are masks that say where dabs may land; no outline exists anywhere;
  3. LIGHT: warm pools laid over the paint, violet-blue shadow between them;
  4. a fine paper tooth over the finished picture (tooth()).
A Painting is written in FRAME units (px of the picture as the game shows it, y down) and painted Q times as large
(Q = 2: a 1920x1080 frame is painted at 3840x2160 and shrunk, so a 2x close-up is a window of the painting itself,
never an enlarged pixel: D-198's rule). numpy only, lock-free.
"""
import math

import numpy as np


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def box(a, r):
    """A box blur of radius r px (the edge value repeated beyond the edges)."""
    r = int(r)
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
    return ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy).astype(np.float32)


def fbm(h, w, cell, rng, octaves=3, sx=1.0):
    out, amp, tot = np.zeros((h, w), np.float32), 1.0, 0.0
    for _ in range(octaves):
        out += amp * field(h, w, cell, rng, sx)
        tot += amp
        amp, cell = amp * 0.5, max(2.0, cell * 0.5)
    return out / tot


def lerp(a, b, t):
    t = t[..., None] if (np.ndim(t) == 2 and np.ndim(a) in (1, 3)) else t
    return a * (1 - t) + b * t


def tooth(img, seed, strength=0.0085):
    """A fine paper tooth over a finished picture (float RGB), nothing coarser. (0.014 read as digital noise in a sky.)"""
    n = box(np.random.default_rng(seed).standard_normal(img.shape[:2]).astype(np.float32), 1)
    return np.clip(img * (1 + strength * n / max(float(n.std()), 1e-3))[..., None], 0, 1)


class Painting:
    """An opaque painting of W x H frame units, painted Q times as large. yy (rows x 1) and xx (1 x columns) are the
    pixels' frame coordinates: underpaintings are written with them."""
    def __init__(self, W, H, seed=1, Q=1):
        self.W, self.H, self.Q = W, H, Q
        self.pw, self.ph = W * Q, H * Q
        self.img = np.zeros((self.ph, self.pw, 3), np.float32)
        self.rng = np.random.default_rng(seed)
        self.yy = (np.arange(self.ph, dtype=np.float32) / Q)[:, None]
        self.xx = (np.arange(self.pw, dtype=np.float32) / Q)[None, :]
        self.warp = self.fbm(46.0, 3)                           # the picture's own noise: shapes borrow it for their edges
        self.fine = self.fbm(9.0, 2)
        self.count = 0                                          # dabs laid (the sheet prints it)

    # ---- fields and masks (frame units in, pixel arrays out)
    def fbm(self, cell, octaves=2, sx=1.0):
        return fbm(self.ph, self.pw, cell * self.Q, self.rng, octaves, sx)

    def line1(self, cell, octaves=2):
        """Smooth 1-D noise in [-1, 1] along x, one value per pixel column: a ridge line, a bed's edge."""
        return fbm(1, self.pw, cell * self.Q, self.rng, octaves)[0]

    def below(self, yline, soft=1.0):
        """The mask of everything below the line y = yline[column] (soft frame px wide at the edge)."""
        return np.clip((self.yy - np.asarray(yline, np.float32)[None, :]) / max(soft, 1e-3) + 0.5, 0, 1)

    def at(self, line, x):
        """A per-column line's value at frame x."""
        return float(line[int(np.clip(x * self.Q, 0, self.pw - 1))])

    def pix(self, x, y):
        """The pixel (row, column) of a frame point, clipped."""
        return int(np.clip(y * self.Q, 0, self.ph - 1)), int(np.clip(x * self.Q, 0, self.pw - 1))

    def box(self, a, r):
        return box(a, int(round(r * self.Q)))

    def full(self, a):
        """A mask or an underpainting broadcast to the whole picture (a view)."""
        return np.broadcast_to(a, (self.ph, self.pw) + np.shape(a)[2:])

    def blob(self, cx, cy, rx, ry, soft=0.35, wobble=0.35):
        """A soft-edged, uneven oval mask: a cloud's lobe, a tree's crown, a pool of light."""
        q = self.Q
        cx, cy, rx, ry = cx * q, cy * q, rx * q, ry * q
        x0, x1 = max(int(cx - rx * 1.6), 0), min(int(cx + rx * 1.6) + 1, self.pw)
        y0, y1 = max(int(cy - ry * 1.6), 0), min(int(cy + ry * 1.6) + 1, self.ph)
        out = np.zeros((self.ph, self.pw), np.float32)
        if x1 <= x0 or y1 <= y0:
            return out
        dx = (np.arange(x0, x1, dtype=np.float32)[None, :] - cx) / rx
        dy = (np.arange(y0, y1, dtype=np.float32)[:, None] - cy) / ry
        d = np.sqrt(dx * dx + dy * dy) + wobble * self.warp[y0:y1, x0:x1] + 0.4 * wobble * self.fine[y0:y1, x0:x1]
        out[y0:y1, x0:x1] = np.clip((1 - d) / max(soft, 1e-3), 0, 1)
        return out

    # ---- paint
    def lay(self, colour, mask):
        """Paint laid flat through a mask (colour: one rgb or an underpainting); only the mask's own box is touched."""
        mask = self.full(mask)
        rows, cols = np.flatnonzero(mask.any(axis=1)), np.flatnonzero(mask.any(axis=0))
        if not len(rows):
            return
        y0, y1, x0, x1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
        m = mask[y0:y1, x0:x1, None]
        col = colour if np.ndim(colour) == 1 else self.full(colour)[y0:y1, x0:x1]
        self.img[y0:y1, x0:x1] = self.img[y0:y1, x0:x1] * (1 - m) + col * m

    def _dab(self, cx, cy, a, b, th, col, alpha, edge, streak, clip=None):
        """ONE stroke of the brush, in pixels: a flat oval of one colour, half-length a along th, half-width b."""
        R = int(math.ceil(max(a, b))) + 1
        x0, x1, y0, y1 = max(int(cx) - R, 0), min(int(cx) + R + 1, self.pw), max(int(cy) - R, 0), min(int(cy) + R + 1, self.ph)
        if x1 <= x0 or y1 <= y0:
            return
        dx = np.arange(x0, x1, dtype=np.float32)[None, :] - cx
        dy = np.arange(y0, y1, dtype=np.float32)[:, None] - cy
        c, s = math.cos(th), math.sin(th)
        u, v = (dx * c + dy * s) / a, (-dx * s + dy * c) / b
        m = np.clip((1 - (u * u + v * v)) * edge, 0, 1)
        if streak:
            m = m * (1 - streak * (0.5 + 0.5 * np.sin(v * 8.0 + cx * 0.7)) * np.clip(u + 0.4, 0, 1))
        if clip is not None:                                    # a stroke that must stay ON a form (bark on a trunk, a leaf)
            m = m * clip[y0:y1, x0:x1]
        m = (m * alpha)[..., None]
        sub = self.img[y0:y1, x0:x1]
        self.img[y0:y1, x0:x1] = sub * (1 - m) + col * m
        self.count += 1

    def dab(self, cx, cy, a, b, th, col, alpha=1.0, edge=3.0, streak=0.25, clip=None):
        """One dab in frame units. edge: 1 = soft and wet, 5 = crisp; streak: how dry its tail and bristles are."""
        q = self.Q
        self._dab(cx * q, cy * q, a * q, max(0.6, b * q), th, col, alpha, edge, streak, clip)

    def brush(self, under, where, n, size, aspect=(2.0, 4.0), angle=0.0, spread=0.3, alpha=(0.7, 1.0), jitter=0.05,
              hue=0.012, edge=3.0, streak=0.25, clip=None, win=None):
        """n dabs where `where` (0..1: how likely a dab lands there) allows. Each takes its colour from `under` (an
        underpainting, or one rgb) at its own centre, a little off in value (jitter) and hue; angle: radians, or a
        function of the frame point (x, y). Dabs spill past the mask by their own size: that spill is the painted edge
        (clip = a whole-picture mask they must stay on). win = (row slice, column slice): `where` and `under` are given
        for that window of the picture only (a small thing in a large picture is not worth a pass over all of it)."""
        rng, q = self.rng, self.Q
        if win is None:
            p, oy, ox, wpw = self.full(where).astype(np.float64).ravel(), 0, 0, self.pw
        else:
            p, oy, ox, wpw = np.asarray(where, np.float64).ravel(), win[0].start, win[1].start, where.shape[1]
        tot = p.sum()
        if tot <= 0 or n <= 0:
            return
        idx = np.clip(np.searchsorted(np.cumsum(p), rng.uniform(0, tot, n)), 0, p.size - 1)
        ys, xs = idx // wpw, idx % wpw
        flat = np.ndim(under) == 1
        if not flat and win is None:
            under = self.full(under)
        for cy, cx in zip(ys, xs):
            a = rng.uniform(*size) * q
            b = max(0.6, a / rng.uniform(*aspect))
            th = (angle((cx + ox) / q, (cy + oy) / q) if callable(angle) else angle) + rng.normal(0, spread)
            col = (under if flat else under[cy, cx]) * (1 + rng.normal(0, jitter)) + rng.normal(0, hue, 3).astype(np.float32)
            self._dab(cx + ox + rng.uniform(-0.5, 0.5), cy + oy + rng.uniform(-0.5, 0.5), a, b, th, np.clip(col, 0, 1), rng.uniform(*alpha), edge, streak, clip)

    def stroke(self, pts, w0, w1, col, edge=4.0, jitter=0.03):
        """A long brush stroke along a polyline (a root, a trunk's plane, a grass blade): dabs laid end to end, the width
        running from w0 to w1 (frame units)."""
        rng, q = self.rng, self.Q
        pts = np.asarray(pts, np.float32) * q
        w0, w1 = w0 * q, w1 * q
        s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
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
            self._dab(x, y, max(step * 1.2, w), max(0.6, w / 2), th, np.clip(col * (1 + rng.normal(0, jitter)), 0, 1), 1.0, edge, 0.0)

    def glaze(self, mask, tint, strength=1.0):
        """A wash over the paint: every colour under the mask times `tint` (shadow: a violet-blue below 1; a pool of
        light: a warm tint above 1)."""
        self.img *= 1 + (mask * strength)[..., None] * (np.array(tint, np.float32) - 1)

    def shrunk(self):
        """The picture at the frame's own size (block means of the Q x Q pixels)."""
        q = self.Q
        im = np.clip(self.img, 0, 1)
        return im if q == 1 else im.reshape(self.H, q, self.W, q, 3).mean(axis=(1, 3))
