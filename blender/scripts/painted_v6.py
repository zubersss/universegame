"""B-251 (D-202; the owner on USER-44: "find a painter's hand"): LOADERS FOR PAINTED MATERIAL in ART v6.
WRITTEN 11-10 12:1x AS SOURCE, UNRUN: only 200 px previews of the two source images exist yet
(docs/art_sources/v6_painted/strokes_01_preview200.png, plant_01_preview200.png). Nothing here has read a full-size file.

The painting stays ours (build_specimens_v6 / build_forest_kinds_v6: a form field says where a stroke goes, how long,
which way, what value). What changes is the STROKE ITSELF and, for whole things, the PLATE:
  strokes(path) -> [Stroke]   a sheet of painted strokes on white: every stroke cut out as its own shape (alpha from
                              how far it is from the paper, so dry bristle gaps stay gaps), its long axis found, its
                              own light-and-dark kept as a tone map, sorted by kind (leaf / long / curl / dry)
  stamp(P, st, ...)           one such stroke laid as a dab: placed, turned, sized, in the colour the painting asks for
  brush(P, bank, ...)         paint_v6.Painting.brush with painted strokes instead of the oval dab (the same arguments)
  plate(path, ...) -> Plate   one painted thing on a plain pale ground: cut out (the ground found from the border and
                              flooded in from it, so pale lights inside the thing are not eaten), the edge un-mixed
                              from the ground, trimmed, its foot found
  rekey(pl, cols, ...)        the plate's values carried onto the frame's own palette (a three-value ramp, as the
                              kinds use), under the frame's ONE light, hazed with distance
  place(P, pl, tf, s)         the plate laid into a painting through a placement (tf, s), as the kinds are

Files must be 8-bit RGB or RGBA PNG, not interlaced (crop_png.read_any; no JPEG: numpy only, no bpy, no PIL).
D-202's rules for the material itself are LEAD's (a medium and a period in the prompt, never a film, studio, character
or artist; credited in docs/credits/lead.md); a piece that resembles a known design is dropped, and I say so if I see it.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import crop_png  # noqa: E402
import paint_v6 as PT  # noqa: E402
import build_specimens_v6 as SP  # noqa: E402

LIGHT = SP.LIGHT


def read_rgb(path):
    """-> float32 HxWx3 in 0..1 (an RGBA file's alpha is ignored: these sheets are painted on an opaque ground)."""
    return crop_png.read_any(path)[..., :3].astype(np.float32) / 255.0


def border_colour(img, ring=6):
    """The ground: the median colour of a ring round the picture's edge."""
    r = max(1, min(ring, img.shape[0] // 8, img.shape[1] // 8))
    edge = np.concatenate([img[:r].reshape(-1, 3), img[-r:].reshape(-1, 3), img[:, :r].reshape(-1, 3), img[:, -r:].reshape(-1, 3)])
    return np.median(edge, axis=0).astype(np.float32)


def shrink(a, f):
    """Block means (f an integer), the picture cut to a multiple of f."""
    if f <= 1:
        return a
    h, w = (a.shape[0] // f) * f, (a.shape[1] // f) * f
    a = a[:h, :w]
    return a.reshape((h // f, f, w // f, f) + a.shape[2:]).mean(axis=(1, 3))


def labels(mask):
    """Connected regions of a boolean mask (8-neighbours), numpy only: every pixel takes the largest index among itself
    and its neighbours until nothing changes. -> (int32 labels, 0 = none; the labels in use). Meant for a mask a few
    hundred px on a side (shrink first)."""
    h, w = mask.shape
    lab = np.where(mask, np.arange(1, h * w + 1, dtype=np.int32).reshape(h, w), 0)
    while True:
        p = np.pad(lab, 1)
        best = lab
        for dy in (0, 1, 2):
            for dx in (0, 1, 2):
                best = np.maximum(best, p[dy:dy + h, dx:dx + w])
        best = np.where(mask, best, 0)
        if (best == lab).all():
            break
        lab = best
    return lab, [int(v) for v in np.unique(lab) if v]


# ---------------------------------------------------------------- painted strokes
class Stroke:
    """One painted stroke, its long axis along +x: mask (0..1, HxW), tone (its own light and dark about 1.0), the
    half-length and half-width of its body in the mask's px, its kind."""
    def __init__(self, mask, tone, a, b, kind):
        self.mask, self.tone, self.a, self.b, self.kind = mask, tone, a, b, kind
        self._mips = None

    def mips(self):
        """[(mask, tone)] at full size, half, a quarter ...: a stroke painted 300 px long is laid 20 to 60 px long, and
        sampled straight from the large picture it would shimmer."""
        if self._mips is None:
            m, t = self.mask, self.tone
            self._mips = [(m, t)]
            while min(m.shape) >= 6:
                m, t = shrink(m, 2).astype(np.float32), shrink(t, 2).astype(np.float32)
                self._mips.append((m, t))
        return self._mips


def _turn(img, deg, fill=0.0):
    """img turned by deg (counter-clockwise on screen) about its middle onto a canvas that holds it, bilinear."""
    h, w = img.shape[:2]
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    W, H = int(math.ceil(abs(w * c) + abs(h * s))) + 2, int(math.ceil(abs(w * s) + abs(h * c))) + 2
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = xx - W / 2.0, yy - H / 2.0
    sx, sy = u * c - v * s + w / 2.0 - 0.5, u * s + v * c + h / 2.0 - 0.5
    ix, iy = np.floor(sx).astype(int), np.floor(sy).astype(int)
    fx, fy = sx - ix, sy - iy

    def tap(ax, ay):
        ok = (ax >= 0) & (ax < w) & (ay >= 0) & (ay < h)
        o = np.full(ax.shape, fill, np.float32)
        o[ok] = img[ay[ok], ax[ok]]
        return o
    return tap(ix, iy) * (1 - fx) * (1 - fy) + tap(ix + 1, iy) * fx * (1 - fy) + tap(ix, iy + 1) * (1 - fx) * fy + tap(ix + 1, iy + 1) * fx * fy


def strokes(path, lo=0.06, hi=0.30, min_px=600, join=3):
    """A sheet of painted strokes on a white (or pale) ground -> [Stroke], the largest first.
    alpha = how far a pixel is from the ground in its darkest channel (lo..hi -> 0..1): the body is opaque, the dry
    bristle marks half so, the paper between bristles stays clear. Strokes are told apart on a 4x smaller mask, the
    bristles of one stroke joined by `join` px of blur there; a region under min_px (full size) is a speck, dropped."""
    img = read_rgb(path)
    ground = border_colour(img)
    alpha = np.clip(((ground[None, None, :] - img).max(axis=2) - lo) / (hi - lo), 0, 1)
    lum = img @ np.array([0.30, 0.59, 0.11], np.float32)
    f = 4
    small = PT.box(shrink(alpha, f).astype(np.float32), join) > 0.04
    lab, ids = labels(small)
    out = []
    for i in ids:
        ys, xs = np.where(lab == i)
        y0, y1, x0, x1 = ys.min() * f, (ys.max() + 1) * f, xs.min() * f, (xs.max() + 1) * f
        own = np.repeat(np.repeat(lab[ys.min():ys.max() + 1, xs.min():xs.max() + 1] == i, f, 0), f, 1)
        a = alpha[y0:y1, x0:x1] * own[:y1 - y0, :x1 - x0]
        if a.sum() < min_px or min(a.shape) < 6:
            continue
        gy, gx = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(np.float32)
        m = float(a.sum())
        cx, cy = float((gx * a).sum() / m), float((gy * a).sum() / m)
        dx, dy = gx - cx, gy - cy
        sxx, syy, sxy = float((dx * dx * a).sum() / m), float((dy * dy * a).sum() / m), float((dx * dy * a).sum() / m)
        ang = 0.5 * math.atan2(2 * sxy, sxx - syy)                               # the long axis (screen, y down)
        mask = _turn(a, math.degrees(ang))                                       # ... laid along +x
        body = lum[y0:y1, x0:x1]
        mean = float((body * a).sum() / m)
        tone = _turn(np.clip(body / max(mean, 1e-3), 0.75, 1.25) * (a > 0.2) + (a <= 0.2), math.degrees(ang), 1.0)
        on = np.where(mask > 0.15)
        if not len(on[0]):
            continue
        mask = mask[on[0].min():on[0].max() + 1, on[1].min():on[1].max() + 1]
        tone = tone[on[0].min():on[0].max() + 1, on[1].min():on[1].max() + 1]
        ha, hb = mask.shape[1] / 2.0, mask.shape[0] / 2.0
        fill = float(mask.mean())
        rows = np.arange(mask.shape[0], dtype=np.float32)[:, None]
        mid = (mask * rows).sum(axis=0) / np.maximum(mask.sum(axis=0), 1e-3)     # the body's middle line, column by column
        bend = float(np.ptp(mid[mask.sum(axis=0) > 1.0])) / max(2 * hb, 1.0) if (mask.sum(axis=0) > 1.0).any() else 0.0
        kind = "dry" if fill < 0.42 else "long" if ha / hb >= 3.5 else "curl" if bend > 0.45 else "leaf"
        if mask[:, :mask.shape[1] // 2].sum() < mask[:, mask.shape[1] // 2:].sum():   # the heavy end first: a stroke starts full and runs dry
            mask, tone = mask[:, ::-1], tone[:, ::-1]
        out.append(Stroke(np.ascontiguousarray(mask, np.float32), np.ascontiguousarray(tone, np.float32), ha, hb, kind))
    out.sort(key=lambda st: -st.mask.size)
    return out


def stamp(P, st, cx, cy, a, th, col, alpha=1.0, clip=None, wide=1.0):
    """One painted stroke as a dab, in the painting's PIXELS: its middle at (cx, cy), its half-length a along th
    (radians, screen), its width kept in proportion (x wide), in colour col times the stroke's own tone."""
    k = a / st.a
    b = st.b * k * wide
    R = int(math.ceil(math.hypot(a, b))) + 1
    x0, x1, y0, y1 = max(int(cx) - R, 0), min(int(cx) + R + 1, P.pw), max(int(cy) - R, 0), min(int(cy) + R + 1, P.ph)
    if x1 <= x0 or y1 <= y0:
        return
    dx = np.arange(x0, x1, dtype=np.float32)[None, :] - cx
    dy = np.arange(y0, y1, dtype=np.float32)[:, None] - cy
    c, s = math.cos(th), math.sin(th)
    mips = st.mips()
    lv = min(len(mips) - 1, max(0, int(math.floor(math.log2(1.0 / max(k, 1e-6)) + 0.5)))) if k < 1 else 0   # the mip nearest the size it is laid at
    mask, tone = mips[lv]
    f = float(2 ** lv)
    u, v = ((dx * c + dy * s) / k + st.a) / f - 0.5, ((-dx * s + dy * c) / (k * wide) + st.b) / f - 0.5
    ix, iy = np.floor(u).astype(int), np.floor(v).astype(int)
    fx, fy = u - ix, v - iy
    h, w = mask.shape

    def tap(src, ax, ay, fill):
        ok = (ax >= 0) & (ax < w) & (ay >= 0) & (ay < h)
        o = np.full(ax.shape, fill, np.float32)
        o[ok] = src[ay[ok], ax[ok]]
        return o

    def sample(src, fill):
        return (tap(src, ix, iy, fill) * (1 - fx) * (1 - fy) + tap(src, ix + 1, iy, fill) * fx * (1 - fy)
                + tap(src, ix, iy + 1, fill) * (1 - fx) * fy + tap(src, ix + 1, iy + 1, fill) * fx * fy)
    m = sample(mask, 0.0)
    if clip is not None:
        m = m * clip[y0:y1, x0:x1]
    m = (m * alpha)[..., None]
    paint = np.clip(np.asarray(col, np.float32)[None, None, :] * sample(tone, 1.0)[..., None], 0, 1)
    sub = P.img[y0:y1, x0:x1]
    P.img[y0:y1, x0:x1] = sub * (1 - m) + paint * m
    P.count += 1


def brush(P, bank, under, where, n, size, aspect=None, angle=0.0, spread=0.3, alpha=(0.7, 1.0), jitter=0.05, hue=0.012,
          edge=None, streak=None, clip=None, win=None, kind=None):
    """paint_v6.Painting.brush laid with PAINTED strokes: the same arguments (aspect, edge and streak are the oval dab's
    and are ignored: a painted stroke has its own shape), plus kind = "leaf" / "long" / "curl" / "dry" / None (any)."""
    rng, q = P.rng, P.Q
    pool = [st for st in bank if kind is None or st.kind == kind] or list(bank)
    if not pool:
        return
    if win is None:
        p, oy, ox, wpw = P.full(where).astype(np.float64).ravel(), 0, 0, P.pw
    else:
        p, oy, ox, wpw = np.asarray(where, np.float64).ravel(), win[0].start, win[1].start, where.shape[1]
    tot = p.sum()
    if tot <= 0 or n <= 0:
        return
    idx = np.clip(np.searchsorted(np.cumsum(p), rng.uniform(0, tot, n)), 0, p.size - 1)
    ys, xs = idx // wpw, idx % wpw
    flat = np.ndim(under) == 1
    if not flat and win is None:
        under = P.full(under)
    for cy, cx in zip(ys, xs):
        st = pool[int(rng.integers(0, len(pool)))]
        th = (angle((cx + ox) / q, (cy + oy) / q) if callable(angle) else angle) + rng.normal(0, spread)
        if rng.random() < 0.5:
            th += math.pi                                                       # a stroke is laid either way along its line
        col = (under if flat else under[cy, cx]) * (1 + rng.normal(0, jitter)) + rng.normal(0, hue, 3).astype(np.float32)
        stamp(P, st, cx + ox + rng.uniform(-0.5, 0.5), cy + oy + rng.uniform(-0.5, 0.5), rng.uniform(*size) * q, th, np.clip(col, 0, 1), rng.uniform(*alpha), clip)


# ---------------------------------------------------------------- painted plates
class Plate:
    """One painted thing cut from its ground: rgb (HxWx3, straight, the edge un-mixed), alpha (HxW), its foot (px in
    the plate: where it stands) and its height in metres as it should stand in the world."""
    def __init__(self, rgb, alpha, foot, height_m):
        self.rgb, self.alpha, self.foot, self.height_m = rgb, alpha, foot, height_m
        self._mips = None

    def mips(self):
        """Premultiplied RGBA at full size, half, a quarter ...: a plate is drawn far smaller than it was painted."""
        if self._mips is None:
            cur = np.dstack([self.rgb * self.alpha[..., None], self.alpha]).astype(np.float32)
            self._mips = [cur]
            while min(cur.shape[:2]) >= 8:
                cur = shrink(cur, 2).astype(np.float32)
                self._mips.append(cur)
        return self._mips


def plate(path, height_m, lo=0.045, hi=0.12, feather=2):
    """A painted thing on a plain pale ground -> Plate. The ground is the border's colour; it is FLOODED IN from the
    border (on a 4x smaller picture), so a pale light inside the thing, as near the ground's colour as the ground is,
    stays in the plate. alpha runs lo..hi of colour distance within `feather` px of that flood, 1 inside; the edge's
    colour is un-mixed from the ground; the plate is trimmed; its foot is the middle of its lowest rows."""
    img = read_rgb(path)
    ground = border_colour(img)
    d = np.sqrt(((img - ground[None, None, :]) ** 2).sum(axis=2))
    f = 4
    like = shrink((d < hi).astype(np.float32), f) > 0.5
    lab, ids = labels(like)
    rim = set(int(v) for v in np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]) if v)
    bg = np.repeat(np.repeat(np.isin(lab, list(rim)), f, 0), f, 1)
    full = np.zeros(d.shape, bool)
    full[:bg.shape[0], :bg.shape[1]] = bg
    near = PT.box(full.astype(np.float32), feather) > 0.01                       # the ground and a thin band beside it
    alpha = np.where(near, np.clip((d - lo) / (hi - lo), 0, 1), 1.0).astype(np.float32)
    alpha[full & (d < lo)] = 0.0
    rgb = np.clip((img - (1 - alpha[..., None]) * ground[None, None, :]) / np.maximum(alpha[..., None], 0.08), 0, 1)
    ys, xs = np.where(alpha > 0.05)
    if not len(ys):
        raise ValueError(path + ": nothing stands out from the ground")
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgb, alpha = rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1]
    low = alpha[-max(2, alpha.shape[0] // 40):].sum(axis=0)
    fx = float((np.arange(low.size) * low).sum() / max(float(low.sum()), 1e-3))
    return Plate(np.ascontiguousarray(rgb, np.float32), np.ascontiguousarray(alpha, np.float32), (fx, float(alpha.shape[0])), height_m)


def rekey(pl, cols, mix=0.7, light=0.10, pale=0.0, haze=None):
    """The plate on the frame's palette: its values (the 10th, 50th and 90th hundredths of its own luminance) are
    carried onto cols = (dark, mid, lit), `mix` of the way (1.0 = wholly the frame's colours, 0.0 = the painter's);
    then the frame's ONE light: the side toward it a little lighter and warmer, the side away darker and cooler;
    then the haze of distance. -> a new Plate."""
    lum = pl.rgb @ np.array([0.30, 0.59, 0.11], np.float32)
    on = pl.alpha > 0.5
    p10, p50, p90 = (float(np.percentile(lum[on], q)) for q in (10, 50, 90))
    t = np.clip((lum - p10) / max(p90 - p10, 1e-3), -0.25, 1.25)
    k = (p50 - p10) / max(p90 - p10, 1e-3)                                       # where the middle value sits on that scale
    d, m, l = (np.asarray(c, np.float32) for c in cols)
    lo_part = d[None, None, :] + (m - d)[None, None, :] * np.clip(t / max(k, 1e-3), -0.5, 1)[..., None]
    hi_part = m[None, None, :] + (l - m)[None, None, :] * np.clip((t - k) / max(1 - k, 1e-3), 0, 1.5)[..., None]
    ramp = np.where((t < k)[..., None], lo_part, hi_part)
    rgb = pl.rgb * (1 - mix) + ramp * mix
    h, w = lum.shape
    gy, gx = np.mgrid[0:h, 0:w].astype(np.float32)
    side = ((gx - w / 2.0) / (w / 2.0)) * LIGHT[0] + ((gy - h / 2.0) / (h / 2.0)) * LIGHT[1]      # toward the light: +
    rgb = rgb * (1 + light * side[..., None] * np.array([1.0, 0.95, 0.8], np.float32)[None, None, :])
    if pale and haze is not None:
        rgb = rgb * (1 - pale) + np.asarray(haze, np.float32)[None, None, :] * pale
    return Plate(np.clip(rgb, 0, 1).astype(np.float32), pl.alpha, pl.foot, pl.height_m)


def place(P, pl, tf, s=1.0, opacity=1.0):
    """The plate laid into a painting through a placement (tf, s) as the kinds are: tf maps a kind's own px (64 a
    metre, its foot at (0, 0), y down) to the frame, so the plate stands height_m tall on that foot, mirrored and
    leaning with the placement. Drawn from the mip nearest its size on the painting."""
    q = P.Q
    o, ex, ey = tf(0.0, 0.0), tf(1.0, 0.0), tf(0.0, 1.0)
    ax, ay = ((ex[0] - o[0]) * q, (ex[1] - o[1]) * q), ((ey[0] - o[0]) * q, (ey[1] - o[1]) * q)   # the kind's px axes in painting px
    k = pl.height_m * 64.0 / pl.alpha.shape[0]                                    # kind px a plate px
    scale = k * math.hypot(*ay)                                                   # painting px a plate px
    mips = pl.mips()
    lv = min(len(mips) - 1, max(0, int(math.floor(math.log2(1.0 / max(scale, 1e-6)) + 0.5)))) if scale < 1 else 0
    src, f = mips[lv], float(2 ** lv)
    h, w = src.shape[:2]
    corners = []
    for px, py in ((0, 0), (pl.alpha.shape[1], 0), (0, pl.alpha.shape[0]), (pl.alpha.shape[1], pl.alpha.shape[0])):
        kx, ky = (px - pl.foot[0]) * k, (py - pl.foot[1]) * k
        corners.append((o[0] * q + kx * ax[0] + ky * ay[0], o[1] * q + kx * ax[1] + ky * ay[1]))
    x0, x1 = max(int(min(c[0] for c in corners)) - 1, 0), min(int(max(c[0] for c in corners)) + 2, P.pw)
    y0, y1 = max(int(min(c[1] for c in corners)) - 1, 0), min(int(max(c[1] for c in corners)) + 2, P.ph)
    if x1 <= x0 or y1 <= y0:
        return
    det = ax[0] * ay[1] - ax[1] * ay[0]
    if abs(det) < 1e-9:
        return
    dx = np.arange(x0, x1, dtype=np.float32)[None, :] + 0.5 - o[0] * q
    dy = np.arange(y0, y1, dtype=np.float32)[:, None] + 0.5 - o[1] * q
    kx, ky = (dx * ay[1] - dy * ay[0]) / det, (-dx * ax[1] + dy * ax[0]) / det    # back into the kind's px
    u, v = (kx / k + pl.foot[0]) / f - 0.5, (ky / k + pl.foot[1]) / f - 0.5
    ix, iy = np.floor(u).astype(int), np.floor(v).astype(int)
    fx, fy = (u - ix)[..., None], (v - iy)[..., None]

    def tap(ax_, ay_):
        ok = (ax_ >= 0) & (ax_ < w) & (ay_ >= 0) & (ay_ < h)
        t = np.zeros(ax_.shape + (4,), np.float32)
        t[ok] = src[ay_[ok], ax_[ok]]
        return t
    smp = (tap(ix, iy) * (1 - fx) * (1 - fy) + tap(ix + 1, iy) * fx * (1 - fy) + tap(ix, iy + 1) * (1 - fx) * fy + tap(ix + 1, iy + 1) * fx * fy) * opacity
    sub = P.img[y0:y1, x0:x1]
    P.img[y0:y1, x0:x1] = smp[..., :3] + sub * (1 - smp[..., 3:4])
