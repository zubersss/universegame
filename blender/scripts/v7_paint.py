"""Art v7 (D-205), B-258 part 3: THE PAINTER'S HAND ON A RENDER. numpy only (it runs inside Blender for a piece and in
Blender's bundled python for the frame).

LEAD's verdict on part 1 (11-10 14:0x): real form, light and detail for almost nothing, but the plant is a clean render,
not paint. What a painter does that a renderer does not, and what this module does to a rendered piece:
  flatten_values()   FEWER, FLATTER VALUES: a form is painted in three or four values with a clear step between them (the
                     step IS the designed shadow shape), warm in the light and cool in the shade; a render shades smoothly.
  paint_over()       THE BRUSH: the picture laid again as strokes, each ONE colour taken from under its middle, along the
                     form's own grain; then VEINS AND GRAIN AS STROKES IN TWO VALUES (a lighter and a darker one), in
                     place of the scan's photographic detail.
  bleed()            colour carried outward past the silhouette, so a stroke over the edge has paint.
A still piece only (scenery): these strokes are laid in the picture, so on a moving figure they would crawl; a figure's
paint stays in its materials (LEAD's ruling 13:3x).
  resize()           a straight-alpha picture at another size: area means when shrinking (never an enlarged pixel in a
                     near layer), bilinear when enlarging (a far veil: soft is right).
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paint_v6 as PT  # noqa: E402
import painted_v6 as PV  # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
STROKES = os.path.join(REPO, "docs", "art_sources", "v6_painted", "strokes_01.png")   # LEAD's AI-painted stroke sheet (credited in docs/credits/lead.md)
LUM = np.array([0.30, 0.59, 0.11], np.float32)
_BANK = None


def bank():
    global _BANK
    if _BANK is None:
        _BANK = PV.strokes(STROKES)
    return _BANK


def bleed(arr, radii=(2, 4, 8, 14)):
    """The colour inside the silhouette carried outward (rgb only; H x W x 3)."""
    known = arr[..., 3] > 0.5
    ext = arr[..., :3] * known[..., None]
    for r in radii:
        ba = PT.box(known.astype(np.float32), r)
        bc = np.dstack([PT.box(ext[..., c] * known, r) for c in range(3)])
        new = (~known) & (ba > 0.02)
        ext[new] = bc[new] / ba[new][:, None]
        known = known | new
    return ext.astype(np.float32)


def flatten_values(arr, steps=4, soft=0.30, amount=0.8, temp=0.5, warm=(1.06, 1.01, 0.90), cool=(0.90, 0.98, 1.12)):
    """A piece's values gathered into `steps` plateaus between its own darkest and lightest (the 3rd and 97th hundredths
    of its luminance), with a step `soft` of a plateau wide between them; `amount` of the way (1 = poster flat); the
    light plateaus a little warmer, the dark ones cooler (temp). arr: straight RGBA 0..1. -> the same shape."""
    rgb, a = arr[..., :3], arr[..., 3]
    on = a > 0.5
    if not on.any():
        return arr
    L = rgb @ LUM
    lo, hi = (float(v) for v in np.percentile(L[on], (3, 97)))
    t = np.clip((L - lo) / max(hi - lo, 1e-3), 0, 1) * steps
    u = t - 0.5
    k = np.floor(u)
    s = np.clip((u - k - 0.5) / max(soft, 1e-3) + 0.5, 0, 1)
    s = s * s * (3 - 2 * s)
    t2 = np.clip((k + s + 0.5) / steps, 0, 1)
    L2 = L * (1 - amount) + (lo + t2 * (hi - lo)) * amount
    out = rgb * (L2 / np.maximum(L, 1e-3))[..., None]
    tint = np.asarray(cool, np.float32)[None, None, :] + (np.asarray(warm, np.float32) - np.asarray(cool, np.float32))[None, None, :] * t2[..., None]
    out = out * (1 + temp * (tint - 1))
    return np.concatenate([np.clip(out, 0, 1), a[..., None]], axis=2).astype(np.float32)


def grain(lum, r=5):
    """The direction a form's own lines run at every pixel (radians, screen): along its edges, veins and cracks."""
    gy, gx = np.gradient(lum)
    j11, j22, j12 = PT.box(gx * gx, r), PT.box(gy * gy, r), PT.box(gx * gy, r)
    return (0.5 * np.arctan2(2 * j12, j11 - j22) + np.pi / 2).astype(np.float32)


def paint_over(arr, kind="leaf", size=(8.0, 18.0), density=1.0, seed=5, accents=1.0, acc_size=(6.0, 14.0), up=1.26, down=0.72,
               acc_kind="long", detail=None):
    """The picture laid again with the brush (see the module's head). size / acc_size: a stroke's half-length in px, from
    .. to; density: how many times over the form is covered; accents: how strongly veins and grain come back as strokes
    in two values (0 = none); detail: the picture the veins are read from (default: arr itself, before the strokes).
    -> (straight RGBA, strokes laid)."""
    h, w = arr.shape[:2]
    a = arr[..., 3]
    ext = bleed(arr)
    src = ext if detail is None else bleed(detail)
    lum = src @ LUM
    along = grain(PT.box(lum, 2))
    ang = lambda x, y: float(along[min(max(int(y), 0), h - 1), min(max(int(x), 0), w - 1)])   # noqa: E731
    cover = (PT.box(a, 1) > 0.3).astype(np.float32)
    area = float(cover.sum())
    if area < 4:
        return arr, 0
    mean = (size[0] + size[1]) / 2.0
    n = int(density * area / (2.0 * mean * (2.0 * mean / 3.5)) * 2.2)
    P = PT.Painting(w, h, seed, 1)
    P.img[:] = ext
    PV.brush(P, bank(), ext, cover, n, size, angle=ang, spread=0.18, alpha=(0.75, 1.0), jitter=0.035, hue=0.008, kind=kind)
    if accents > 0:
        calm = P.img.copy()                                                              # the stroke's colour: the painted form's, a value up or down
        hp = lum - PT.box(lum, 4)
        s = float(np.percentile(np.abs(hp[cover > 0.5]), 90)) + 1e-4
        light, dark = np.clip(hp / s - 0.45, 0, 1) * cover, np.clip(-hp / s - 0.45, 0, 1) * cover
        m2 = (acc_size[0] + acc_size[1]) / 2.0
        for mask, k in ((dark, down), (light, up)):
            na = int(accents * float(mask.sum()) / (2.0 * m2 * 1.6) * 1.6)
            PV.brush(P, bank(), np.clip(calm * k, 0, 1), mask, na, acc_size, angle=ang, spread=0.07, alpha=(0.7, 0.95), jitter=0.02, hue=0.004, kind=acc_kind)
    return np.concatenate([np.clip(P.img, 0, 1), a[..., None]], axis=2).astype(np.float32), P.count


GREY = np.array([0.50, 0.50, 0.50], np.float32)   # the mannequin: neutral, for scale only


def mannequin(img, k, fx, fy, colour=GREY):
    """A plain neutral-grey figure 1.84 m tall, side view, facing right, for SCALE only (no design: capsules and an
    oval head). Drawn into img (opaque RGB) at k px per metre, its feet at pixel (fx, fy)."""
    capsules(img, k, fx, fy, ((0.0, 1.50, 0.0, 1.02, 0.135, 0.12), (0.0, 1.02, 0.0, 0.92, 0.125, 0.12),            # chest, hips
                              (0.01, 1.60, 0.02, 1.52, 0.055, 0.06),                                              # neck
                              (-0.02, 0.92, -0.07, 0.50, 0.085, 0.060), (-0.07, 0.50, -0.10, 0.07, 0.058, 0.042),  # the back leg
                              (0.03, 0.92, 0.09, 0.50, 0.085, 0.060), (0.09, 0.50, 0.10, 0.07, 0.058, 0.042),      # the front leg
                              (-0.11, 0.035, 0.03, 0.035, 0.035, 0.035), (0.09, 0.035, 0.24, 0.035, 0.035, 0.035),  # feet
                              (0.0, 1.46, 0.02, 1.17, 0.052, 0.042), (0.02, 1.17, 0.10, 0.92, 0.042, 0.036)),      # the arm
             colour, ovals=((0.025, 1.725, 0.098, 0.115),))                                                        # the head: 0.23 m


def capsules(img, k, fx, fy, caps, colour=GREY, ovals=()):
    """Capsules [(ax, ay, bx, by, ra, rb)] and ovals [(cx, cy, rx, ry)], metres from the pixel (fx, fy) (x right, y up),
    filled with ONE flat colour into img (opaque RGB) at k px per metre: the grey mannequin's parts."""
    xs = [v for c in caps for v in (c[0] - max(c[4], c[5]), c[2] - max(c[4], c[5]), c[0] + max(c[4], c[5]), c[2] + max(c[4], c[5]))] + \
         [v for o in ovals for v in (o[0] - o[2], o[0] + o[2])]
    ys = [v for c in caps for v in (c[1] - max(c[4], c[5]), c[3] - max(c[4], c[5]), c[1] + max(c[4], c[5]), c[3] + max(c[4], c[5]))] + \
         [v for o in ovals for v in (o[1] - o[3], o[1] + o[3])]
    bx0, by0 = int(fx + (min(xs) - 0.02) * k), int(fy - (max(ys) + 0.02) * k)
    bw, bh = int((max(xs) - min(xs) + 0.04) * k) + 2, int((max(ys) - min(ys) + 0.04) * k) + 2
    xm = ((np.arange(bx0, bx0 + bw, dtype=np.float32) + 0.5 - fx) / k)[None, :]
    ym = ((fy - (np.arange(by0, by0 + bh, dtype=np.float32) + 0.5)) / k)[:, None]
    d = np.full((bh, bw), 9.0, np.float32)
    for ax, ay, bx_, by_, ra, rb in caps:
        vx, vy = bx_ - ax, by_ - ay
        t = np.clip(((xm - ax) * vx + (ym - ay) * vy) / max(vx * vx + vy * vy, 1e-6), 0, 1)
        d = np.minimum(d, np.hypot(xm - (ax + t * vx), ym - (ay + t * vy)) - (ra + (rb - ra) * t))
    for cx, cy, rx, ry in ovals:
        d = np.minimum(d, np.hypot((xm - cx) / rx, (ym - cy) / ry) * min(rx, ry) - min(rx, ry))
    a = np.clip(0.5 - d * k, 0, 1)
    x0, y0, x1, y1 = max(bx0, 0), max(by0, 0), min(bx0 + bw, img.shape[1]), min(by0 + bh, img.shape[0])
    if x1 > x0 and y1 > y0:
        m = a[y0 - by0:y1 - by0, x0 - bx0:x1 - bx0, None]
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - m) + np.asarray(colour, np.float32)[None, None, :] * m


def _axis(a, n_out, axis):
    n = a.shape[axis]
    if n_out == n:
        return a
    shape = [1] * a.ndim
    shape[axis] = -1
    if n_out < n:                                                                        # area means: the running sum read at the new pixels' edges
        c = np.cumsum(a, axis=axis, dtype=np.float64)
        c = np.concatenate([np.zeros_like(np.take(c, [0], axis=axis)), c], axis=axis)
        e = np.linspace(0.0, n, n_out + 1)
        i = np.minimum(np.floor(e).astype(int), n - 1)
        f = (e - i).reshape(shape)
        ce = np.take(c, i, axis=axis) * (1 - f) + np.take(c, i + 1, axis=axis) * f
        return (np.diff(ce, axis=axis) * (n_out / n)).astype(np.float32)
    x = (np.arange(n_out) + 0.5) * n / n_out - 0.5
    i = np.clip(np.floor(x).astype(int), 0, max(n - 2, 0))
    f = np.clip(x - i, 0, 1).reshape(shape).astype(np.float32)
    return (np.take(a, i, axis=axis) * (1 - f) + np.take(a, np.minimum(i + 1, n - 1), axis=axis) * f).astype(np.float32)


def resize(arr, s):
    """A straight-alpha RGBA picture at s times its size (colour premultiplied for the means)."""
    h, w = arr.shape[:2]
    H, W = max(1, int(round(h * s))), max(1, int(round(w * s)))
    pm = np.concatenate([arr[..., :3] * arr[..., 3:4], arr[..., 3:4]], axis=2).astype(np.float32)
    pm = _axis(_axis(pm, H, 0), W, 1)
    al = pm[..., 3:4]
    return np.concatenate([np.where(al > 1e-4, pm[..., :3] / np.maximum(al, 1e-4), 0.0), np.clip(al, 0, 1)], axis=2).astype(np.float32)
