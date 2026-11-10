"""ART v6 "cel on painted" (D-199, docs/STYLE_V6.md section 2): the CEL - a pencil line over flat paint.

Everything that acts is drawn with this module (the surveyor, creatures, tools, things picked up, built or dug loose):
  - the LINE is a pencil line: dark charcoal, one stroke with pressure in it (it swells and thins about 40 % along its
    length), tapered ends, a slightly dry, broken edge; a closed outline may stop short of closing (a small gap where
    the stroke began). Mean width 1.5 px at the game's 1080p zoom.
  - the PAINT is flat: one opaque colour an area, no texture, no gradient, no grain; at most one flat shadow shape per
    form (shade(): a step darker in the same hue, a clean edge); two colours may meet with no line between them (a
    paint patch: P()).
  - the two are kept as two layers (paint, line) until compose(), so a second LINE pass over the same paint costs only
    the line (the 12 Hz boil, STYLE_V6 2.6) and a figure can be re-keyed (far limbs, night) without touching its line.

Lock-free: fakegp drawings (gp_draw strokes) rasterised with gp_raster's masks in numpy; no blender.exe.
Units: a DESIGN px is 1 / 128 m (a 2.0 m figure is 256 design px); a canvas is W x H design px, y down, rendered K
times as large (K = 4: 512 px per metre, D-198: only ever shrunk in play). The game's 1080p zoom is 64 px per metre =
half a design px.
"""
import math
import os
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp  # noqa: E402

G = fakegp.install()
import gp_raster as GR  # noqa: E402

PPU = 64                              # canvas units: a design px is 1 / PPU of a unit
CHARCOAL = "#2A2624"                  # the pencil: dark charcoal, not black (LEAD 11-10 07:1x: darker than run 4's #3A3533)
LINE = 1.33 / PPU                     # a contour's nominal radius: 2.66 design px wide = 1.33 px at the game's zoom (the
#                                       tapered ends and the thinner flicks bring the measured mean to 1.2 px; LEAD 07:1x:
#                                       the film's photocopied line is tight and clean - run 4's 1.5 px read as a crayon)
FLICK = 0.8 * LINE                    # folds, strands, small forms
LINE_A = 0.96                         # the pencil's opacity over the paint
PRESS = 0.50                          # the pressure's swing about the nominal width (0.5-2.0 px at the game's zoom)
PERIOD = 26.0                         # ... over about this many design px
WOBBLE, WPERIOD = 0.30, 16.0          # the hand's wobble (design px) and its period: under a pixel at the game's zoom
E0 = 0.25                             # a tapered end's width against the stroke's
SHADOW = (0.80, 0.78, 0.84)           # the one flat shadow shape: the paint times this (a step darker, the hue kept)
TAU = 2 * math.pi


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def mat(gp, name, fill=None, line=True, alpha=1.0):
    """A cel material: flat paint (fill hex or None) and / or the pencil line. Returns its index."""
    return G.mat(gp, name, fill=fill, ink=line, ink_hex=CHARCOAL, fill_alpha=alpha)


# ---------------------------------------------------------------- shapes (design px, y down)
def fillet(pts, rad, n=5):
    """A polygon with every corner rounded: `rad` design px along each edge (at most half the shorter edge), so long
    edges stay straight and short ones flow into each other."""
    out, m = [], len(pts)
    for i in range(m):
        (xp, yp), (x, y), (xn, yn) = pts[i - 1], pts[i], pts[(i + 1) % m]
        lp, ln = math.hypot(xp - x, yp - y), math.hypot(xn - x, yn - y)
        dd = min(rad, 0.5 * lp, 0.5 * ln)
        if dd < 1e-6:
            out.append((x, y))
            continue
        ax, ay = x + (xp - x) * dd / lp, y + (yp - y) * dd / lp
        bx, by = x + (xn - x) * dd / ln, y + (yn - y) * dd / ln
        for j in range(n + 1):
            t = j / n
            out.append(((1 - t) ** 2 * ax + 2 * t * (1 - t) * x + t * t * bx, (1 - t) ** 2 * ay + 2 * t * (1 - t) * y + t * t * by))
    return out


def catmull(pts, closed, sub=4):
    """A spline THROUGH the points: sampled curves (ovals, tapers, lines of three points and more) lose their facets."""
    n = len(pts)
    if n < 3:
        return list(pts)
    out = []
    for i in range(n if closed else n - 1):
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[0]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[-1]
        for j in range(sub):
            t = j / sub
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    if not closed:
        out.append(pts[-1])
    return out


def C(cx, cy, r, n=28, ry=None, a0=0.0, a1=TAU):
    """A circle / oval / arc as points (angles clockwise on screen from +x, y down)."""
    ry = r if ry is None else ry
    closed = abs(a1 - a0 - TAU) < 1e-6
    k = n if closed else n + 1
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(k)]


def hose(pts, w):
    """A tube round a centre line (splined first, so the tube bends smoothly)."""
    return G.hose_outline(catmull(list(pts), False, 6) if len(pts) >= 3 else list(pts), w, cap_n=10)


def taper(p0, p1, w0, w1, n=14, bulge=0.0, cap0=0.0):
    """A limb segment's outline from p0 (width w0) to p1 (width w1), its sides gently bulged; it starts at p0's side:
    n + 1 points down one side, 9 round p1, n + 1 back up, 9 round p0 (that cap's radius less cap0)."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        w = (w0 * (1 - t) + w1 * t) / 2 + bulge * math.sin(math.pi * t)
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        left.append((cx + nx * w, cy + ny * w))
        right.append((cx - nx * w, cy - ny * w))
    capb = C(x1, y1, w1 / 2, 10, a0=math.atan2(ny, nx), a1=math.atan2(ny, nx) - math.pi)
    capa = C(x0, y0, w0 / 2 - cap0, 10, a0=math.atan2(-ny, -nx), a1=math.atan2(-ny, -nx) - math.pi)
    return left + capb[1:-1] + right[::-1] + capa[1:-1]


def crescent(cx, cy, r, a0, a1, w, n=18):
    """A flat highlight: an arc of radius r from a0 to a1, w wide in its middle, pointed at both ends."""
    outer = C(cx, cy, r, n, a0=a0, a1=a1)
    inner = [(cx + (r - w * math.sin(math.pi * i / n) ** 0.8) * math.cos(a0 + (a1 - a0) * i / n),
              cy + (r - w * math.sin(math.pi * i / n) ** 0.8) * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    return outer + inner[-2:0:-1]


# ---------------------------------------------------------------- strokes
def S(d, pts, m, r=LINE, cyclic=False, rnd=None, sharp=False, **opt):
    """One stroke of a cel. Closed shapes: corners rounded `rnd` design px (default 3; shapes of 12 points and more are
    splined), sharp = as given. Open lines of three points and more are splined.
    opt: keep=name   remember this shape's paint mask (for clip=)
         clip=name   the paint is cut to that shape (a patch on a form)
         under=True  the paint goes UNDER the lines already drawn (a patch on a form keeps the form's lines)
         shade=True  the shape is a flat SHADOW: the paint under it a step darker in its own hue (times SHADOW)
         gap=px      a closed line stops this far short of closing (default 2.5 on outlines of 70 px and more, else 0)
         at=0..1     where on the loop the line starts (and its gap sits); default 0 = the first point given
         ends=(a, b) the lengths of an open line's start and end tapers (default 2.5 and 6; a gapped outline 4 and 4)
         press=      the pressure swing (default PRESS)"""
    pts = list(pts)
    if not sharp:
        if cyclic:
            pts = catmull(pts, True, 3) if (len(pts) >= 12 and rnd is None) else fillet(pts, 3.0 if rnd is None else rnd)
        elif len(pts) >= 3:
            pts = catmull(pts, False, 5)
    s = G.stroke(d, pts, m, r, cyclic=cyclic)
    s.cel = opt
    return s


def P(d, pts, m, **opt):
    """A paint patch: flat colour, no line of its own, laid under the lines already drawn (paint edges without line)."""
    opt.setdefault("under", True)
    return S(d, pts, m, 0.0, cyclic=True, **opt)


def F(d, M, pts, w=1.0, **opt):
    """A flick: a fold, a strand, a seam - one short pencil line, M["ln"]."""
    return S(d, pts, M["ln"], FLICK * w, **opt)


# ---------------------------------------------------------------- the pencil
def _noise(t, seed, period, wrap=None):
    """Smooth value noise in [-1, 1] along t (cosine-interpolated lattice); wrap = a loop's length: the noise closes."""
    rng = np.random.default_rng(seed)
    if wrap:
        m = max(3, int(round(wrap / period)))
        lat = rng.uniform(-1, 1, m)
        k = t / wrap * m
        i = np.floor(k).astype(int)
        w = (1 - np.cos(np.pi * (k - i))) / 2
        return lat[i % m] * (1 - w) + lat[(i + 1) % m] * w
    k = t / period
    lat = rng.uniform(-1, 1, int(k.max()) + 3)
    i = np.floor(k).astype(int)
    w = (1 - np.cos(np.pi * (k - i))) / 2
    return lat[i] * (1 - w) + lat[i + 1] * w


def pencil(pts, r_nom, cyclic, sid, f, boil=0, gap=None, at=0.0, ends=None, press=PRESS):
    """A stroke's path as the pencil draws it. pts (n, 2) raster px, r_nom the nominal radius (px), f px per design px.
    -> (points (m, 2), radii (m,), closed) or None. The gap and the path are the stroke's own (sid); the pressure and
    the wobble change with the line pass (boil), so two passes over one drawing differ by under a pixel."""
    q = np.vstack([pts, pts[:1]]) if cyclic else np.asarray(pts, np.float64)
    seg = np.hypot(*np.diff(q, axis=0).T)
    ok = np.r_[True, seg > 1e-9]
    q = q[ok]
    if len(q) < 2:
        return None
    s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(q, axis=0).T))]
    L = float(s[-1])
    n = max(2, int(math.ceil(L / (0.75 * f))))
    closed = False
    if cyclic:
        if gap is None:
            gap = 2.5 if L / f >= 70 else 0.0
        if gap > 0:
            t = np.linspace(gap * f / 2, L - gap * f / 2, n + 1)
        else:
            t, closed = np.linspace(0.0, L, n + 1)[:-1], True
        tt = (t + at * L) % L
    else:
        t = np.linspace(0.0, L, n + 1)
        tt = t
    x, y = np.interp(tt, s, q[:, 0]), np.interp(tt, s, q[:, 1])
    wrap = L if closed else None
    r = r_nom * (1.0 + press * _noise(t, sid * 31 + boil * 7919 + 5, PERIOD * f, wrap))
    if not closed:
        a, b = ends or ((4.0, 4.0) if cyclic else (2.5, 6.0))
        a, b = max(min(a * f, 0.3 * L), 1e-6), max(min(b * f, 0.45 * L), 1e-6)
        e = np.minimum(E0 + (1 - E0) * np.clip((t - t[0]) / a, 0, 1) ** 0.6, E0 + (1 - E0) * np.clip((t[-1] - t) / b, 0, 1) ** 0.6)
        r = r * e
    x = x + WOBBLE * f * _noise(t, sid * 17 + boil * 104729 + 1, WPERIOD * f, wrap)
    y = y + WOBBLE * f * _noise(t, sid * 17 + boil * 104729 + 2, WPERIOD * f, wrap)
    return np.c_[x, y], r, closed


def _box(px, py, pad, HH, WW):
    return (max(int(math.floor(py.min() - pad)), 0), min(int(math.ceil(py.max() + pad)) + 1, HH),
            max(int(math.floor(px.min() - pad)), 0), min(int(math.ceil(px.max() + pad)) + 1, WW))


def render(d, gp, W, H, K=4, ss=2, boil=0, tag="cel", paint=True):
    """A fakegp drawing (canvas units, the Canvas below) -> (paint: H*K x W*K x 4 float32 premultiplied, line: H*K x W*K
    float32 coverage, stats: per pencil stroke (length in design px, mean / min / max width in px at the game's zoom)).
    A fill hides the lines drawn before it (unless under=True); lines never hide paint until compose()."""
    f = K * ss
    HH, WW = H * f, W * f
    pa = np.zeros((HH, WW, 4), np.float32)
    ln = np.zeros((HH, WW), np.float32)
    keep, stats = {}, []
    for si, s in enumerate(d.strokes):
        m = gp.materials[s.material_index]
        o = getattr(s, "cel", None) or {}
        xy = np.array([(p.position[0], p.position[2]) for p in s.points], np.float64) * PPU
        px, py = xy[:, 0] * f, HH - xy[:, 1] * f
        rn = float(np.median([p.radius for p in s.points])) * PPU * f
        if m["fill"] is not None and s.cyclic and len(px) >= 3:
            y0, y1, x0, x1 = _box(px, py, 2, HH, WW)
            if y1 > y0 and x1 > x0:
                full = GR._poly_mask(px, py, HH, WW)
                if o.get("clip"):
                    full &= keep[o["clip"]]
                if o.get("keep"):
                    keep[o["keep"]] = full
                a = full[y0:y1, x0:x1].astype(np.float32) * m["fill_alpha"]
                if paint and o.get("shade"):                                   # a flat shadow shape: what is under it, darker
                    pa[y0:y1, x0:x1, :3] *= 1 - a[..., None] * (1 - np.array(SHADOW, np.float32))
                elif paint:
                    sub = pa[y0:y1, x0:x1]
                    sub[..., :3] = rgb(m["fill"]) * a[..., None] + sub[..., :3] * (1 - a[..., None])
                    sub[..., 3] = a + sub[..., 3] * (1 - a)
                if not o.get("under"):
                    ln[y0:y1, x0:x1] *= 1 - a
        if m["ink"] is not None and rn * 2 / ss >= 0.5:
            sid = zlib.crc32(f"{tag}|{si}".encode()) & 0xFFFFFF
            res = pencil(np.c_[px, py], rn, s.cyclic, sid, f, boil, o.get("gap"), o.get("at", 0.0), o.get("ends"), o.get("press", PRESS))
            if res is None:
                continue
            q, r, closed = res
            y0, y1, x0, x1 = _box(q[:, 0], q[:, 1], float(r.max()) + 3, HH, WW)
            if y1 > y0 and x1 > x0:
                lm = GR._ink_mask(q[:, 0], q[:, 1], r, closed, HH, WW)[y0:y1, x0:x1]
                ln[y0:y1, x0:x1] = np.maximum(ln[y0:y1, x0:x1], lm)
                wg = r / f                                                     # the width at the game's zoom (px)
                stats.append((len(r) * 0.75, float(wg.mean()), float(wg.min()), float(wg.max())))
    pa = pa.reshape(H * K, ss, W * K, ss, 4).mean(axis=(1, 3))
    ln = ln.reshape(H * K, ss, W * K, ss).mean(axis=(1, 3))
    return pa, ln, stats


class Canvas:
    """One cel drawing: strokes in design px (y down) on a W x H canvas, rendered K times as large."""
    def __init__(self, W, H, K=4, tag="cel"):
        self.W, self.H, self.K, self.tag = W, H, K, tag
        self.gp = fakegp.FakeGP()
        self.d = fakegp.FakeDrawing()
        self.dm = G.Xf(self.d, lambda pts: [(x / PPU, (self.H - y) / PPU) for x, y in pts])

    def render(self, boil=0, ss=2, paint=True):
        return render(self.d, self.gp, self.W, self.H, self.K, ss, boil, self.tag, paint)


# ---------------------------------------------------------------- finishing (numpy, on the rendered layers)
def box(a, r):
    """A box blur of radius r px (zero beyond the edges)."""
    if r < 1:
        return a
    k = 2 * r + 1
    for axis in (0, 1):
        pad = [(0, 0)] * a.ndim
        pad[axis] = (r + 1, r)
        c = np.cumsum(np.pad(a, pad), axis=axis, dtype=np.float64)
        n = c.shape[axis]
        a = ((np.take(c, range(k, n), axis=axis) - np.take(c, range(0, n - k), axis=axis)) / k).astype(np.float32)
    return a


def shift(a, dy, dx):
    """a moved dy rows down and dx columns right, zero-filled."""
    out = np.zeros_like(a)
    h, w = a.shape
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def shade(paint, band, K=4, back=1, tint=SHADOW):
    """The ONE flat shadow shape of a form, lit from above: a band `band` design px deep along its underside and its
    back edge (back = +1: the left of a part drawn facing right), a clean edge, the paint under it a step darker in
    its own hue. No blend, no texture."""
    a = paint[..., 3]
    dpx = max(2, int(round(band * K)))
    m = np.clip(a - shift(a, -dpx, back * dpx), 0, 1)
    m = np.clip((box(m, max(1, dpx // 8)) - 0.5) * 5.0 + 0.5, 0, 1)            # one shape: slivers go, corners round
    out = paint.copy()
    out[..., :3] *= 1 - m[..., None] * (1 - np.array(tint, np.float32))
    return out


def dry(line, seed, amount=0.5):
    """The pencil's dry, slightly broken edge: the line's edge roughened by under a pixel (of the large drawing) and
    a few specks of the cel left bare inside it. (amount 1.0 was run 4's: a crayon at 4x; LEAD 07:1x: half of it.)"""
    rng = np.random.default_rng(seed)
    n1 = box(rng.standard_normal(line.shape).astype(np.float32), 1)
    n1 /= max(float(n1.std()), 1e-3)
    e = box(line, 1)
    near = np.clip(e * 4.0, 0, 1)                                              # the noise acts only where the line is (run 1:
    cov = np.clip((e - 0.5 + 0.10 * amount * n1 * near) * 3.0 + 0.5, 0, 1)     # it left specks all over the cel)
    n2 = box(rng.standard_normal(line.shape).astype(np.float32), 1)
    n2 /= max(float(n2.std()), 1e-3)
    return cov * (1 - 0.5 * amount * np.clip((n2 - 1.5) * 2.5, 0, 1))


def compose(paint, line, key=None):
    """The line over the paint -> straight RGBA uint8. key: (mul, add rgb) re-keys the PAINT only (far limbs, night);
    the pencil stays the pencil."""
    p = paint
    if key is not None:
        p = paint.copy()
        p[..., :3] = p[..., :3] * key[0] + np.array(key[1], np.float32) * p[..., 3:4]
    c = (line * LINE_A)[..., None]
    a = c + p[..., 3:4] * (1 - c)
    col = (rgb(CHARCOAL) * c + p[..., :3] * (1 - c)) / np.maximum(a, 1e-5)
    return np.clip(np.rint(np.dstack([np.clip(col, 0, 1), np.clip(a, 0, 1)]) * 255), 0, 255).astype(np.uint8)


def premul(u8):
    f = u8.astype(np.float32) / 255.0
    f[..., :3] *= f[..., 3:4]
    return f


def down(img, f):
    """An image shrunk f times by block means (premultiplied float in, the same out): how every plate is made."""
    if f <= 1:
        return img
    h, w = img.shape[0] // f * f, img.shape[1] // f * f
    return img[:h, :w].reshape((h // f, f, w // f, f) + img.shape[2:]).mean(axis=(1, 3))


def line_stats(stats):
    """(mean, min, max) pencil width in px at the game's zoom over all strokes (the mean weighted by length), and the
    number of pencil strokes."""
    if not stats:
        return 0.0, 0.0, 0.0, 0
    tot = sum(s[0] for s in stats)
    return sum(s[0] * s[1] for s in stats) / tot, min(s[2] for s in stats), max(s[3] for s in stats), len(stats)
