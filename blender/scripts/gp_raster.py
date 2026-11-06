"""Grease Pencil -> 1x RGBA frames, rasterized in numpy (contract §11.1/11.2, B-110).

Why not EEVEE/Workbench: they need a GPU context in shared RAM on an 8 GB laptop, and their
stroke widths depend on the view. Here each stroke of the *evaluated* GP object (modifiers
such as Line Art or noise applied) is drawn in paint order:

  objects by their "order" custom property (then name) -> layers bottom to top -> strokes,
  each stroke: fill polygon (even-odd) when its material shows fill, then its ink as a chain
  of capsules whose radius is the point radius x a ±20 % jitter along the stroke.

Everything is drawn at `ss`x supersampling into premultiplied RGBA and box-filtered down to
1x, then un-premultiplied: straight alpha, no colour outside the drawn shapes. Ink widths
(px, after jitter) are collected per frame so the review sheet can print them.
"""
import math
import zlib

import numpy as np

JITTER = 0.20


def _hex(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def _lin_to_srgb(c):
    c = np.clip(np.asarray(c, np.float32), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def _mat_colours(m):
    st = m.grease_pencil
    def get(prop, key):
        if key in m.keys():
            return _hex(m[key])
        v = np.array(getattr(st, prop)[:3], np.float32)
        return v if st.bl_rna.properties[prop].subtype == "COLOR_GAMMA" else _lin_to_srgb(v)
    fill = get("fill_color", "srgb_fill") if st.show_fill else None
    ink = get("color", "srgb_ink") if st.show_stroke else None
    return fill, ink


def collect(scene, objects, frame):
    """Strokes visible at `frame`, in paint order, in world metres (x, z)."""
    import bpy
    scene.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    gps = [o for o in objects if o.type == "GREASEPENCIL" and not o.hide_render]
    gps.sort(key=lambda o: (float(o.get("order", 0.0)), o.name))
    out = []
    for ob in gps:
        ev = ob.evaluated_get(dg)
        data = ev.data
        mw = np.array(ev.matrix_world, np.float64)
        for layer in data.layers:
            if layer.hide:
                continue
            fr = layer.current_frame()
            if fr is None or fr.drawing is None:
                continue
            lm = np.array(layer.matrix_local, np.float64)
            M = mw @ lm
            d = fr.drawing
            pos = np.empty(len(d.attributes["position"].data) * 3, np.float32)
            if len(pos) == 0:
                continue
            d.attributes["position"].data.foreach_get("vector", pos)
            pos = pos.reshape(-1, 3).astype(np.float64)
            pos = (np.c_[pos, np.ones(len(pos))] @ M.T)[:, :3]
            rad = np.empty(len(pos), np.float32)
            d.attributes["radius"].data.foreach_get("value", rad)
            scale = float(np.cbrt(abs(np.linalg.det(M[:3, :3]))) or 1.0)
            offs = list(d.curve_offsets)
            offs = [o.value for o in offs]
            for si, s in enumerate(d.strokes):
                a, b = offs[si], offs[si + 1]
                mi = s.material_index
                if mi >= len(data.materials) or data.materials[mi] is None:
                    continue
                fill, ink = _mat_colours(data.materials[mi])
                out.append({
                    "xz": pos[a:b][:, [0, 2]], "radius": rad[a:b] * scale,
                    "cyclic": bool(s.cyclic), "fill": fill, "ink": ink,
                    "behind": bool(data.materials[mi].get("ink_behind", False)),
                    "id": zlib.crc32(f"{ob.name}|{layer.name}|{si}".encode()) & 0xFFFFFF,
                })
    return out


# ---------------------------------------------------------------- raster primitives

def _poly_mask(px, py, H, W):
    """Even-odd fill of polygon (px, py in pixel units, pixel centres at +0.5)."""
    m = np.zeros((H, W), bool)
    y0i, y1i = max(int(math.floor(py.min())), 0), min(int(math.ceil(py.max())) + 1, H)
    x0i, x1i = max(int(math.floor(px.min())), 0), min(int(math.ceil(px.max())) + 1, W)
    if y1i <= y0i or x1i <= x0i:
        return m
    ys = np.arange(y0i, y1i) + 0.5
    xa, ya = px, py
    xb, yb = np.roll(px, -1), np.roll(py, -1)
    Y = ys[:, None]
    cross = (ya[None, :] > Y) != (yb[None, :] > Y)
    with np.errstate(divide="ignore", invalid="ignore"):
        xi = xa[None, :] + (Y - ya[None, :]) * (xb - xa)[None, :] / (yb - ya)[None, :]
    toggles = np.zeros((len(ys), x1i - x0i + 1), np.int32)
    rr, ee = np.nonzero(cross)
    cols = np.clip(np.ceil(xi[rr, ee] - 0.5).astype(np.int64) - x0i, 0, x1i - x0i)
    np.add.at(toggles, (rr, cols), 1)
    inside = (np.cumsum(toggles, axis=1)[:, :-1] % 2) == 1
    m[y0i:y1i, x0i:x1i] = inside
    return m


def _ink_mask(px, py, r, cyclic, H, W):
    """Union of capsules between consecutive points with linearly varying radius r (px)."""
    m = np.zeros((H, W), bool)
    n = len(px)
    if n == 0:
        return m
    segs = [(i, i + 1) for i in range(n - 1)]
    if cyclic and n > 2:
        segs.append((n - 1, 0))
    if n == 1:
        segs = [(0, 0)]
    for i, j in segs:
        ax, ay, bx, by, ra, rb = px[i], py[i], px[j], py[j], r[i], r[j]
        R = max(ra, rb)
        x0, x1 = max(int(min(ax, bx) - R - 1), 0), min(int(max(ax, bx) + R + 2), W)
        y0, y1 = max(int(min(ay, by) - R - 1), 0), min(int(max(ay, by) + R + 2), H)
        if x1 <= x0 or y1 <= y0:
            continue
        X = np.arange(x0, x1) + 0.5
        Y = (np.arange(y0, y1) + 0.5)[:, None]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = np.zeros((y1 - y0, x1 - x0)) if L2 == 0 else np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
        qx, qy = ax + t * dx - X, ay + t * dy - Y
        m[y0:y1, x0:x1] |= (qx * qx + qy * qy) <= (ra + (rb - ra) * t) ** 2
    return m


def _noise1d(s, seed, period):
    """Smooth value noise in [-1, 1] along arclength s (cosine-interpolated lattice)."""
    rng = np.random.default_rng(seed)
    k = s / period
    n = int(k.max()) + 2 if len(k) else 2
    lat = rng.uniform(-1, 1, n)
    i = np.floor(k).astype(int)
    f = k - i
    w = (1 - np.cos(np.pi * f)) / 2
    return lat[i] * (1 - w) + lat[np.minimum(i + 1, n - 1)] * w


def jittered_radius(xz, radius, seed, ppu, period_m=0.18):
    seg = np.r_[0.0, np.hypot(*np.diff(xz, axis=0).T)] if len(xz) > 1 else np.zeros(1)
    s = np.cumsum(seg)
    return radius * (1.0 + JITTER * _noise1d(s, seed, period_m))


def render_frame(strokes, fw, fh, ppu, pivot=(0.5, 0.0), ss=4, seed=0, origin_x=0.0):
    """-> (HxWx4 uint8 straight alpha, ink widths [(nominal_px, min_px, max_px), ...])."""
    H, W = fh * ss, fw * ss
    acc = np.zeros((H, W, 4), np.float32)         # premultiplied
    widths = []

    def over(mask, rgb):
        a = mask.astype(np.float32)[..., None]
        acc[..., :3] = rgb * a + acc[..., :3] * (1 - a)
        acc[..., 3:] = a + acc[..., 3:] * (1 - a)
    k = ppu * ss
    for st in strokes:
        xz = st["xz"]
        px = (xz[:, 0] - origin_x) * k + W * pivot[0]
        py = H * (1.0 - pivot[1]) - xz[:, 1] * k
        has_fill = st["fill"] is not None and st["cyclic"] and len(xz) >= 3
        behind = bool(st.get("behind")) and has_fill
        if has_fill and not behind:
            over(_poly_mask(px, py, H, W), st["fill"])
        if st["ink"] is not None:
            r_m = jittered_radius(xz, st["radius"].astype(np.float64), seed * 7919 + st["id"], ppu)
            r = r_m * k
            if r.max() * 2 / ss >= 0.5:       # hairline 'fill-only' strokes carry ~0 radius
                # ink behind (small parts): a 2r capsule under the fill shows exactly 2r outside the
                # shape, the same visible width as a centred r line, and the colour keeps its area
                over(_ink_mask(px, py, r * (2 if behind else 1), st["cyclic"], H, W), st["ink"])
                nom = float(np.median(st["radius"])) * ppu * 2
                widths.append((round(nom, 2), float(r_m.min() * ppu * 2), float(r_m.max() * ppu * 2)))
        if behind:
            over(_poly_mask(px, py, H, W), st["fill"])
    small = acc.reshape(fh, ss, fw, ss, 4).mean(axis=(1, 3))
    a = small[..., 3:4]
    rgb = np.where(a > 1e-6, small[..., :3] / np.maximum(a, 1e-6), 0.0)
    img = np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])
    return np.clip(np.rint(img * 255), 0, 255).astype(np.uint8), widths
