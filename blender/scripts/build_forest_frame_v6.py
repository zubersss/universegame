"""B-248 (D-200): THE ONE FRAME - Earth's forest edge with the camp, in ART v6; previews only, nothing exported.

The same place painted twice, each at its own scale (nothing enlarged): today's on-foot camera (64 px per metre, 30 m
across) and a closer one (96 px per metre, 20 m across, centred on the camp and the pit). docs/STYLE_V6.md 4a:
  NEAR  a trunk and overhanging leaves at one side, broad-leaved plants and grass in the lower corners: dark, crisp;
  MIDDLE a thicket: trees (each its own lean, fork and crown), a palm, ferns with separate fronds, bushes;
  FAR   hazy forest silhouettes;
  THE STAGE a clearing in a warm pool of light, quiet behind the figures; covered ground; the dug pit in painted beds;
  CELS  the redesigned surveyor idle at the camp and at the dig's contact in the pit (re-keyed for its shade), three
        crates, the smelter, clods; one flat shadow shape under each.
Everything painted is laid by the form-following brush of build_specimens_v6 (tubes, facets, balls) under ONE light.
The scene is written in METRES; a camera (px per metre, the frame's left edge, the ground's row) turns it into a picture
made at twice its size and shrunk.

  python -I build_forest_frame_v6.py <review png>     the lock-free sheet; the two frames go to <dir>/b248_forest/
"""
import math
import os
import sys
import time
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio  # noqa: E402
import cel_v6 as CEL  # noqa: E402
import paint_v6 as PT  # noqa: E402
import gp_raster as GR  # noqa: E402
import build_specimens_v6 as SP  # noqa: E402
import build_surveyor_v6 as SV  # noqa: E402
import build_style_frame_v6 as SF  # noqa: E402  (the crate, the smelter and the clod as cels)
import build_forest_kinds_v6 as FK  # noqa: E402  (the emergent tree, the fan palm, the bamboo, the paddle and heart plants)

rgb, lerp = PT.rgb, PT.lerp
W, H, Q = 1920, 1080, 2
LIGHT = SP.LIGHT
HAZE = rgb("#BFCBBE")                                     # what distance does to every colour
CAMERAS = (("today's on-foot camera, 64 px per metre", 64, 0.0, 600, 4, "forest_frame_64.png"),
           ("a closer camera, 96 px per metre", 96, 5.0, 660, 3, "forest_frame_96.png"))   # name, px per metre, left edge (m), ground row, the cels' K, file
PIT_X, PIT = 14.6, SF.PIT                                 # the pit's left rim (m) and its outline (m from the rim, depth down)
FLOOR = SF.FLOOR
WARM, COOL = SF.WARM, SF.COOL


class Scene:
    """The painting of one camera: metres in, a Painting at twice the frame's size."""
    def __init__(self, ppm, x0, gy, seed=31):
        self.ppm, self.x0, self.gy, self.s = ppm, x0, gy, ppm / 64.0
        self.P = PT.Painting(W, H, seed, Q)
        self.rng = self.P.rng

    def fx(self, x):
        return (x - self.x0) * self.ppm

    def fy(self, z):
        return self.gy - z * self.ppm

    def local(self, x, z, k=1.0, flip=1, lean=0.0):
        """A specimen's own px (its foot at (0, 0), y down, drawn for 64 px per metre) -> the frame: at world (x, z), k times
        as large, mirrored, leaning."""
        ox, oy, s = self.fx(x), self.fy(z), self.s * k
        return (lambda px, py: (ox + flip * (px - lean * py) * s, oy + py * s)), s

    # ---- the form-following painters (the specimen sheet's rules, placed and varied)
    @staticmethod
    def win(m, pad=0):
        """The window of the picture a mask lives in (row slice, column slice), or None: a small thing is painted in its
        own window, not in a pass over the whole picture."""
        rows, cols = np.flatnonzero(m.any(axis=1)), np.flatnonzero(m.any(axis=0))
        if not len(rows):
            return None
        return (slice(max(int(rows[0]) - pad, 0), int(rows[-1]) + 1 + pad), slice(max(int(cols[0]) - pad, 0), int(cols[-1]) + 1 + pad))

    def into(self, w, u, m):
        """Paint laid through a mask, inside a window."""
        self.P.img[w] = self.P.img[w] * (1 - m[..., None]) + u * m[..., None]

    def limb(self, tf, s, pts, r0, r1, cols, flare=0.0, n_per=0.05):
        P = self.P
        m, v, ang, _s = SP.tube(P, [tf(*p) for p in pts], lambda t: (r1 + (r0 - r1) * (1 - t) + flare * (1 - t) ** 4) * s)
        w = self.win(m)
        if w is None:
            return
        mw = m[w]
        u = SP.values(SP.lit_tube(v[w], ang[w]) + 0.10 * P.fine[w], (0.05, 0.36, 0.7), cols)
        self.into(w, u, mw)
        area = float(mw.sum()) / (Q * Q)
        P.brush(u, mw, int(n_per * area / max(s, 0.3) ** 2), (2.2 * s, (2.2 + r0 * 0.55) * s), (2.2, 4.0), SP.at(P, ang + math.pi / 2 + 0.55 * v), 0.12, (0.7, 1.0), 0.06, 0.012, 3.6, 0.3, clip=m, win=w)
        P.brush(cols[0], mw * (v[w] < -0.72), int(0.03 * area / max(s, 0.3) ** 2), (2.0 * s, 5.0 * s), (2.5, 4.0), SP.at(P, ang), 0.1, (0.6, 0.9), 0.04, 0.008, 4.0, 0.1, clip=m, win=w)

    def crown(self, tf, s, centres, cols, holes=3, dim=0.0):
        """A crown: leaf clusters lit as balls; its outline broken by leaves that stand out past it; a few sky holes."""
        P, rng = self.P, self.rng
        hole = np.zeros((P.ph, P.pw), np.float32)
        for _ in range(holes):
            cx, cy, r = centres[int(rng.integers(0, len(centres)))]
            hx, hy = tf(cx + rng.uniform(-0.5, 0.5) * r, cy + rng.uniform(-0.3, 0.5) * r)
            hole = np.maximum(hole, P.blob(hx, hy, rng.uniform(5, 9) * s, rng.uniform(4, 7) * s, 0.2, 0.5))
        for cx, cy, r in centres:
            x, y = tf(cx, cy)
            rr = r * s
            y0, y1 = max(int((y - 2 * rr) * Q), 0), min(int((y + 2 * rr) * Q) + 1, P.ph)
            x0, x1 = max(int((x - 2 * rr) * Q), 0), min(int((x + 2 * rr) * Q) + 1, P.pw)
            if y1 <= y0 or x1 <= x0:
                continue
            w = (slice(y0, y1), slice(x0, x1))
            m = np.zeros((y1 - y0, x1 - x0), np.float32)
            for _ in range(4):
                m = np.maximum(m, P.blob(x + rng.uniform(-0.4, 0.4) * rr, y + rng.uniform(-0.3, 0.3) * rr, rr * rng.uniform(0.7, 1.0), rr * rng.uniform(0.55, 0.8), 0.10, 0.45)[w])
            m = m * (1 - hole[w])
            if not m.any():
                continue
            dx, dy = (P.xx[:, w[1]] - x) / rr, (P.yy[w[0]] - y) / rr
            lam = dx * LIGHT[0] + dy * LIGHT[1] + np.sqrt(np.clip(1 - dx * dx - dy * dy, 0, 1)) * LIGHT[2] + 0.25 * P.fine[w] - dim
            u = SP.values(lam, (0.05, 0.42, 0.78), cols)
            self.into(w, u, m)
            out = lambda px, py, x=x, y=y: math.atan2(py - y, px - x)           # noqa: E731  (every leaf points out from the middle)
            area = float(m.sum()) / (Q * Q)
            leaf = (3.0 * max(s, 0.6), 5.6 * max(s, 0.6))
            P.brush(u, m, int(0.055 * area / max(s, 0.5) ** 2), leaf, (1.7, 2.6), out, 0.55, (0.8, 1.0), 0.05, 0.012, 4.6, 0.1, win=w)
            ring = (PT.box(m, int(round(3 * s * Q))) > 0.03) * (m < 0.5) * (1 - hole[w])   # leaves that stand out past the cluster's edge
            P.brush(u, ring, int(0.02 * area / max(s, 0.5) ** 2), leaf, (1.9, 2.8), out, 0.7, (0.85, 1.0), 0.05, 0.012, 5.0, 0.0, win=w)

    def tree(self, x, z, k=1.0, pale=0.0, crown=True):
        """One tree: its own lean, fork, side and crown (no two alike)."""
        rng = self.rng
        tf, s = self.local(x, z, k, 1 if rng.random() < 0.5 else -1, rng.uniform(-0.14, 0.14))
        f = rng.uniform(0.7, 1.3)                                               # how wide it forks
        bark = [lerp(rgb(c), HAZE, pale) for c in ("#3E3438", "#5A4B44", "#7C6A58", "#A08F74")]
        leafs = [lerp(rgb(c), HAZE, pale) for c in ("#4E6A49", "#6C8B58", "#93AE6E", "#BACB8A")]
        tips = [(-64 * f + rng.uniform(-8, 8), -248 + rng.uniform(-12, 12)), (2 + rng.uniform(-10, 10), -252 + rng.uniform(-14, 10)), (76 * f + rng.uniform(-8, 8), -240 + rng.uniform(-12, 12))]
        if crown:
            self.crown(tf, s, [(tips[1][0] - 4, tips[1][1] + 22, 44), (tips[0][0] + 22, tips[0][1] + 44, 30)], leafs, 0, 0.45)   # the far side, in shade
        for pts, r0, r1 in (([(-10, -14), (-36, -3), (-56, 4)], 9, 2), ([(12, -12), (40, -2), (62, 4)], 9, 2)):
            self.limb(tf, s, pts, r0, r1, bark)                                 # two roots
        self.limb(tf, s, [(0, 0), (-4, -44), (4, -94), (7, -138)], 13, 12, bark, flare=13)
        self.limb(tf, s, [(7, -134), (10, -182), (0, -222), tips[1]], 9, 3, bark)
        self.limb(tf, s, [(6, -130), (-28 * f, -182), (-52 * f, -220), tips[0]], 10.5, 3, bark)
        self.limb(tf, s, [(8, -134), (36 * f, -182), (62 * f, -214), tips[2]], 10, 3, bark)
        if crown:
            cs = [(t[0] + rng.uniform(-10, 10), t[1] - 4 + rng.uniform(-8, 8), rng.uniform(40, 52)) for t in tips]
            cs += [(tips[0][0] - 24, tips[0][1] + 40, 30), (tips[2][0] + 26, tips[2][1] + 40, 28), ((tips[1][0] + tips[2][0]) / 2, tips[1][1] + 46, 28), ((tips[0][0] + tips[1][0]) / 2, tips[1][1] + 2, 44)]
            self.crown(tf, s, cs, leafs, 3)

    def frond(self, tf, s, base, a, ln, droop, cols, n=13):
        """One frond: a rachis that arcs out and droops, and leaflets down both its sides, each its own dab."""
        P = self.P
        pts = [base, (base[0] + math.cos(a) * ln * 0.5, base[1] + math.sin(a) * ln * 0.55), (base[0] + math.cos(a) * ln, base[1] + math.sin(a) * ln + droop)]
        rib = CEL.catmull(pts, False, n)
        lit = (math.cos(a) * LIGHT[0] + math.sin(a) * LIGHT[1]) > 0
        for i in range(2, len(rib) - 1):
            (x0, y0), (x1, y1) = rib[i - 1], rib[i]
            t = i / len(rib)
            ang = math.atan2(y1 - y0, x1 - x0)
            ll = ln * 0.22 * math.sin(math.pi * min(1.0, t * 1.05)) ** 0.6 + 2
            for side in (-1, 1):
                b = ang + side * 1.0
                c = cols[2] if (lit and side < 0) else cols[1] if lit else cols[0] if side > 0 else cols[1]
                px, py = tf(x1 + math.cos(b) * ll * 0.5, y1 + math.sin(b) * ll * 0.5)
                P.dab(px, py, ll * 0.5 * s, max(0.9, ll * 0.12 * s), b if tf(1, 0)[0] > tf(0, 0)[0] else math.pi - b, np.clip(c * (1 + self.rng.normal(0, 0.05)), 0, 1), 1.0, 4.6, 0.0)
        P.stroke([tf(*p) for p in rib], 1.6 * s, 0.6 * s, cols[0] * 0.85, 4.0)

    def fern(self, x, z, k=1.0, pale=0.0, n=9):
        tf, s = self.local(x, z, k)
        cols = [lerp(rgb(c), HAZE, pale) for c in ("#476244", "#66894F", "#9DB96A")]
        for i in sorted(range(n), key=lambda i: abs(i - (n - 1) / 2), reverse=True):   # the outer fronds first
            a = math.radians(-160 + 140 * i / (n - 1) + self.rng.uniform(-6, 6))
            ln = self.rng.uniform(34, 52)
            self.frond(tf, s, (0, 0), a, ln, ln * (0.25 + 0.5 * abs(math.cos(a))), cols)

    def palm(self, x, z, k=1.0, pale=0.0):
        tf, s = self.local(x, z, k, 1, self.rng.uniform(-0.2, 0.2))
        bark = [lerp(rgb(c), HAZE, pale) for c in ("#4A3F3C", "#6A5A4C", "#8C7A62", "#AE9C7C")]
        cols = [lerp(rgb(c), HAZE, pale) for c in ("#476244", "#66894F", "#9DB96A")]
        self.limb(tf, s, [(0, 0), (6, -70), (-2, -150), (4, -214)], 9, 6, bark, flare=5, n_per=0.07)
        for i in sorted(range(11), key=lambda i: abs(i - 5), reverse=True):
            a = math.radians(-172 + 164 * i / 10 + self.rng.uniform(-6, 6))
            ln = self.rng.uniform(62, 84)
            self.frond(tf, s, (4, -214), a, ln, ln * (0.3 + 0.7 * abs(math.cos(a))), cols, 16)

    def leaf(self, pts, w, cols, near=1.0):
        """One broad leaf (frame px): the half toward the light, the half away, a darker tip, strokes along it, a midrib."""
        P = self.P
        m, v, ang, s_ = SP.tube(P, pts, lambda t: 0.8 + w * math.sin(math.pi * min(1.0, t * 1.02) ** 0.75) ** 0.85)
        wn = self.win(m)
        if wn is None:
            return
        mw, vw, aw = m[wn], v[wn], ang[wn]
        lam = vw * (-np.sin(aw) * LIGHT[0] + np.cos(aw) * LIGHT[1])
        u = SP.values(lam + 0.1 * P.fine[wn] - 0.5 * (s_[wn] > 0.86), (-0.12, 0.16), cols)
        self.into(wn, u, mw)
        area = float(mw.sum()) / (Q * Q)
        sc = max(self.s, 0.6)
        P.brush(u, mw, int(0.07 * area / sc ** 2), (3.5 * sc, 7.5 * sc), (2.8, 4.4), SP.at(P, ang), 0.1, (0.7, 1.0), 0.04, 0.01, 4.2, 0.2, clip=m, win=wn)
        P.brush(cols[0] * 0.8, mw * (np.abs(vw) > 0.8) * (lam < 0), int(0.03 * area / sc ** 2), (2.5 * sc, 5 * sc), (3, 4.5), SP.at(P, ang), 0.08, (0.6, 0.9), 0.03, 0.008, 4.4, 0.0, clip=m, win=wn)
        rib = CEL.catmull([tuple(p) for p in pts], False, 6)
        P.stroke(rib[2:-3], 1.5 * sc, 0.6 * sc, lerp(cols[2], rgb("#DDE0A8"), 0.45) if near > 0.5 else cols[0] * 0.85, 4.0)

    def plant(self, x, z, k=1.0, dark=0.0, n=11):
        """A broad-leaved plant, leaf by leaf (dark: a near, shaded one)."""
        tf, s = self.local(x, z, k)
        rng, leaves = self.rng, []
        for i in range(n):
            a = math.radians(-168 + 156 * i / (n - 1) + rng.uniform(-6, 6))
            ln = rng.uniform(52, 82) * (0.75 + 0.25 * abs(math.sin(a)))
            droop = 0.45 * ln * (0.25 + abs(math.cos(a)))
            leaves.append((rng.uniform(0, 1) + 0.6 * abs(math.cos(a)), [tf(0, -2), tf(math.cos(a) * ln * 0.55, math.sin(a) * ln * 0.6), tf(math.cos(a) * ln, math.sin(a) * ln + droop)], rng.uniform(9, 14) * s))
        for depth, pts, w in sorted(leaves, key=lambda t: t[0]):
            near = min(1.0, depth / 1.2)
            cols = [lerp(rgb(c0), rgb(c1), near) * (1 - 0.35 * dark) for c0, c1 in (("#3F5A45", "#557A4C"), ("#56775A", "#7FA25F"), ("#7E9A6E", "#B5CC84"))]
            self.leaf(pts, w, cols, near)

    def blades(self, x, z, k=1.0, n=40, dark=0.0):
        """A grass clump of single blades."""
        tf, s = self.local(x, z, k)
        rng, P, bl = self.rng, self.P, []
        for _ in range(n):
            bl.append((rng.random(), rng.uniform(-11, 11), -math.pi / 2 + rng.normal(0, 0.42), rng.uniform(26, 62), rng.normal(0.25, 0.25) * (1 if rng.random() < 0.7 else -1)))
        for depth, bx, a, ln, bend in sorted(bl):
            col = rgb("#C4B36C") if rng.random() < 0.08 else lerp(rgb("#4A6540"), rgb("#9DB868"), depth) * (1 - 0.35 * dark) * (1 + rng.normal(0, 0.05))
            P.stroke([tf(bx, 0), tf(bx + math.cos(a) * ln * 0.55, math.sin(a) * ln * 0.55), tf(bx + math.cos(a + bend) * ln, math.sin(a + bend) * ln + 0.24 * ln * abs(bend))], 3.0 * s, 0.7 * s, np.clip(col, 0, 1), 5.0)

    def rock(self, x, z, k=1.0, under=None):
        """A rock: its planes jittered, one corner rounded off, moss on its top, litter at its foot (LEAD 08:3x)."""
        tf, s = self.local(x, z, k, 1 if self.rng.random() < 0.5 else -1)
        P, rng = self.P, self.rng
        j = lambda p: (p[0] + rng.uniform(-5, 5), p[1] + rng.uniform(-4, 4))    # noqa: E731
        a, b, c, d_, e, f, g, h, r1, r2, bl, br, m1, m2 = (j(p) for p in ((-54, -22), (-38, -48), (-8, -66), (26, -70), (46, -62), (56, -50), (72, -30), (76, 2), (0, -44), (40, -36), (-50, 4), (32, 4), (-12, 4), (32, 4)))
        cols = {k_: rgb(c_) for k_, c_ in (("lit", "#C6BFAB"), ("half", "#A9A290"), ("mid", "#8A867D"), ("shade", "#6B6871"), ("deep", "#4F4D59"))}
        for tone, ang, poly in (("lit", 0.12, [b, c, d_, e, f, r2, r1]), ("shade", 1.22, [a, b, r1, m1, bl]), ("mid", 1.5, [r1, r2, br, m1]), ("half", 1.92, [r2, f, g, h, br])):
            pts = [tf(*p) for p in poly]
            full = GR._poly_mask(np.array([p[0] for p in pts], np.float32) * Q, np.array([p[1] for p in pts], np.float32) * Q, P.ph, P.pw).astype(np.float32)
            w = self.win(full, 3)
            if w is None:
                continue
            m = np.clip((PT.box(full[w], 1) - 0.5 + 0.12 * P.fine[w]) * 5 + 0.5, 0, 1)
            full[w] = m
            u = (cols[tone] * (1 + 0.05 * P.warp[w])[..., None]).astype(np.float32)
            self.into(w, u, m)
            P.brush(u, m, int(0.05 * float(m.sum()) / (Q * Q) / max(s, 0.5) ** 2), (4 * s, 10 * s), (2.4, 4.2), ang if tf(1, 0)[0] > tf(0, 0)[0] else math.pi - ang, 0.14, (0.6, 0.95), 0.05, 0.01, 3.4, 0.3, clip=full, win=w)
            if tone == "lit":                                                   # moss on the top, as paint
                P.brush(rgb("#7F9257"), m * (P.warp[w] > 0.1), int(0.012 * float(m.sum()) / (Q * Q) / max(s, 0.5) ** 2), (3 * s, 7 * s), (1.6, 2.6), 0.2, 0.6, (0.7, 0.95), 0.06, 0.012, 3.6, 0.1, clip=full, win=w)
        P.stroke([tf(*p) for p in (b, r1, r2, f)], 2.2 * s, 1.2 * s, cols["lit"], 3.5)
        P.stroke([tf(*p) for p in (r1, m1)], 2.0 * s, 1.2 * s, cols["deep"], 3.5)
        for _ in range(int(22 * k)):                                            # the earth and litter over its foot
            px, py = tf(rng.uniform(-58, 78), 2 + rng.uniform(-3, 3))
            P.dab(px, py, rng.uniform(4, 8) * s, rng.uniform(1.6, 3) * s, rng.normal(0, 0.3), rgb(SP.GROUND[int(rng.integers(0, 3))]) if under is None else under, 1.0, 3.5, 0.1)


# ---------------------------------------------------------------- the place
def paint(ppm, x0, gy):
    S_ = Scene(ppm, x0, gy)
    P, rng, s = S_.P, S_.rng, S_.s
    yy, xx = P.yy, P.xx
    fx, fy = S_.fx, S_.fy
    T, t0 = {}, time.time()

    def lap(name):
        nonlocal t0
        T[name] = time.time() - t0
        t0 = time.time()
    above = (yy < gy + 10 * s).astype(np.float32)
    # ---- the air: a warm haze low between the trunks, cooler above; no sky to speak of at a forest's edge
    t = np.clip(yy / gy, 0, 1)
    air = (lerp(rgb("#BCCDC0"), rgb("#E6E0C0"), t) * (1 + 0.03 * P.fbm(160 * s, 2, sx=3)[..., None])).astype(np.float32)
    P.img[:] = air
    P.brush(air, above, 1600, (40 * s, 110 * s), (3.0, 5.5), 0.0, 0.1, (0.5, 0.9), 0.02, 0.006, 1.5, 0.15)
    # ---- FAR: hazy forest silhouettes, two ranks, soft
    span = np.clip((xx - fx(6.5)) / (2.5 * ppm), 0, 1) * np.clip((fx(22.5) - xx) / (2.5 * ppm), 0, 1)   # behind the clearing
    for z_top, col, amp, keep in ((7.6, "#A9BEB3", 1.3, 1.0), (5.4, "#96AE9C", 1.1, 0.25)):   # behind the clearing the nearer band gives way to the drawn ranks below
        line = fy(z_top) + amp * ppm * (0.6 * P.line1(190 * s) + 0.4 * P.line1(40 * s))
        m = P.below(line, 10 * s) * above * (1 - (1 - keep) * span)
        u = lerp(rgb(col), rgb("#D5D9C0"), np.clip((yy - fy(z_top)) / (z_top * ppm), 0, 1) * 0.8)
        P.lay(u, m * 0.92)
        P.brush(u, m, 1500, (12 * s, 34 * s), (1.2, 2.2), 0.0, 1.2, (0.4, 0.8), 0.03, 0.008, 1.5, 0.1)
    for c in range(3):
        P.img[..., c] = P.box(P.img[..., c], 2.5 * s)
    lap("air and far")
    # ---- MIDDLE: the thicket - behind the clearing pale and small (quiet behind the figures), fuller at the sides
    # RE-PLANTED (LEAD 11-10 09:0x): a jungle, not an orchard - five kinds (the canopy tree, the emergent tree, the feather
    # and the fan palm, bamboo), uneven spacing, clumps and gaps, plants overlapping in depth (a rank is painted back to
    # front; later in a list = in front), two or three sizes of each, the emergent tree rising above the rest.
    def put(kind, x, z, k, pale, flip=None, lean=0.0, **kw):
        tf_, s_ = S_.local(x, z, k, (1 if rng.random() < 0.5 else -1) if flip is None else flip, lean)
        kind(P, tf_, s_, pale, **kw)
    E_, FP, BA = FK.emergent_into, FK.fan_palm_into, FK.bamboo_into
    wv, m_ = W / ppm, 64.0 / ppm                                                # the frame's width (m); a near thing's size on screen

    def shade_at(x, z, k):
        """CAST SHADE (LEAD 09:1x): what stands in front darkens what is behind it, down and to the left of it (the light
        comes from the upper right). Laid just before the plant itself is painted."""
        P.glaze(P.blob(fx(x - 0.5 * k), fy(z + 1.7 * k), 1.3 * k * ppm, 2.1 * k * ppm, 0.6, 0.3), (0.80, 0.82, 0.93), 0.5)

    def liana(p0, p1, sag, leaves=7):
        """A liana slung between two points (m): a thin sagging stem and a few leaves hanging from it."""
        at_ = lambda t: (fx(p0[0] + (p1[0] - p0[0]) * t), fy(p0[1] + (p1[1] - p0[1]) * t - sag * 4 * t * (1 - t)))   # noqa: E731
        FK.limb(P, [at_(t) for t in (0, 0.2, 0.4, 0.6, 0.8, 1.0)], 2.2 * s, 1.8 * s, FK.hz(("#3E3438", "#5A4B44", "#7C6A58", "#A08F74"), 0.15), s=s)
        g = FK.greens(0.6, 0.15)
        for _ in range(leaves):
            x, y = at_(rng.uniform(0.1, 0.9))
            P.dab(x + rng.uniform(-3, 3) * s, y + 7 * s, 6 * s, 2.4 * s, math.pi / 2 + rng.normal(0, 0.4), g[int(rng.integers(0, 3))], 1.0, 4.6, 0.0)

    # THE FAR RANKS AS HAZE (LEAD 09:1x): behind the clearing a soft mass with a few lights in it - not small pale copies of
    # the near kinds; trunks only hinted; two emergent trees rise out of it as pale shapes
    # (Runs 4-5 made it an even band of mist with dark trunk smears: fog where version 4 had forest. LEAD 09:2x: FOREST
    # SEEN THROUGH HAZE - a silhouette of crowns along its top (lobed, uneven, a palm head or two and two emergent crowns
    # breaking it), two pale ranks (a bluer one behind a greener one), each fading into mist toward the ground, a few
    # lights in it, and NOTHING in it darker than the mass: no trunk strokes.)
    # (Runs 6-7: big soft lobes on a band of their own value read as CLOUD. Run 8: every crown is a dome of small lobes with
    # a scalloped, fairly crisp edge on a rounded body; the old nearer band is paled behind the clearing so the silhouette
    # has paler air behind it; the light touches each crown's upper right; pale gaps stand for the spaces between trunks.)
    def far_crown(x, z, w, h, z_body):
        """One far crown's silhouette (m; w, h = half sizes): a dome of lobes on a rounded body down to its rank."""
        m = np.maximum(P.blob(fx(x), fy(z), 0.62 * w * ppm, 0.7 * h * ppm, 0.12, 0.22),
                       P.blob(fx(x), fy((z + z_body) / 2), 0.72 * w * ppm, max(0.1, (z - z_body) * 0.62) * ppm, 0.12, 0.2))
        for i in range(6):
            a = math.radians(200 - 44 * i + rng.uniform(-10, 10))
            r = rng.uniform(0.32, 0.46) * w
            m = np.maximum(m, P.blob(fx(x + 0.72 * w * math.cos(a)), fy(z + 0.62 * h * math.sin(a)), r * ppm, 0.85 * r * ppm, 0.12, 0.22))
        return m

    def far_rank(z_body, crowns, c_top, c_mist, extra=None):
        m = P.below(fy(z_body) + 0.12 * ppm * P.line1(40 * s), 5 * s)
        lit = None
        for x, z, w, h in crowns:
            m = np.maximum(m, far_crown(x, z, w, h, z_body))
            b = P.blob(fx(x + 0.3 * w), fy(z + 0.3 * h), 0.5 * w * ppm, 0.45 * h * ppm, 0.7, 0.3)
            lit = b if lit is None else np.maximum(lit, b)
        if extra is not None:
            m = np.maximum(m, extra)
        m = m * above * span
        top = max(z + h for _, z, _, h in crowns)
        u = lerp(rgb(c_top), rgb(c_mist), np.clip((yy - fy(top)) / (top * ppm), 0, 1) ** 1.2)   # fading into mist toward the ground
        P.lay(u, m * 0.95)
        P.brush(u, m, int(700 * s), (8 * s, 20 * s), (1.2, 2.0), 0.0, 1.2, (0.3, 0.6), 0.02, 0.006, 2.5, 0.1, clip=m)
        P.lay(lerp(u, rgb(c_mist), 0.38), lit * m * 0.6)                        # the light on each crown: paler, never darker

    ex, ez = 15.2, 5.5                                                          # a far emergent crown on its stem, breaking the top (run 8: at 5.9 on a long bare stem it was a lollipop)
    palms = ((12.8, 4.3), (19.5, 4.4))                                          # two palm heads breaking the nearer rank's top
    far_rank(3.5, ((7.3, 4.1, 1.2, 0.7), (9.4, 4.9, 1.4, 0.85), (10.9, 4.0, 0.8, 0.5), (12.7, 4.7, 1.3, 0.75), (14.6, 4.1, 1.0, 0.55), (16.6, 4.5, 1.4, 0.7),
                   (18.5, 5.0, 1.1, 0.8), (19.8, 4.1, 0.9, 0.5), (21.5, 4.6, 1.3, 0.8)), "#8EABAD", "#C9D5C8",
             np.maximum(far_crown(ex, ez, 1.0, 0.42, ez - 0.25), P.blob(fx(ex), fy(4.7), 0.1 * ppm, 0.9 * ppm, 0.3, 0.1)))
    far_rank(2.5, ((7.9, 3.1, 1.1, 0.6), (9.6, 3.7, 1.0, 0.7), (11.9, 3.0, 1.4, 0.55), (13.5, 3.6, 0.9, 0.65), (15.6, 3.1, 1.3, 0.6), (16.9, 3.5, 0.9, 0.6),
                   (18.7, 3.1, 1.0, 0.55), (20.6, 3.6, 1.3, 0.7), (22.2, 3.0, 0.9, 0.6)), "#80A389", "#CCD6BC",
             np.maximum(*[P.blob(fx(x), fy((z + 2.6) / 2), 0.055 * ppm, (z - 2.6) * 0.53 * ppm, 0.4, 0.05) for x, z in palms]))   # their stems are of the mass (run 8: a stroke showed darker inside it)
    green_ = rgb("#80A389")
    for x, z in palms:                                                          # the heads, in the rank's own value
        for i in range(9):
            a = math.radians(-172 + 164 * i / 8)
            ln = rng.uniform(0.85, 1.15) * ppm
            P.stroke([(fx(x), fy(z)), (fx(x) + math.cos(a) * ln * 0.5, fy(z) + math.sin(a) * ln * 0.5), (fx(x) + math.cos(a) * ln, fy(z) + math.sin(a) * ln + 0.5 * ln * abs(math.cos(a)))],
                     6 * s, 1.2 * s, green_, 2.5)
    for x, z, rx, rz in ((10.4, 2.2, 1.2, 1.2), (15.9, 1.9, 1.4, 1.1), (19.0, 2.4, 1.0, 1.3),                 # a few lights in it ...
                         (9.0, 1.7, 0.2, 1.2), (13.9, 1.8, 0.26, 1.4), (17.0, 1.7, 0.22, 1.3), (20.4, 1.6, 0.2, 1.1)):   # ... and pale gaps between trunks
        P.lay(rgb("#E6E6C8"), P.blob(fx(x), fy(z), rx * ppm, rz * ppm, 0.8, 0.3) * span * 0.32)
    for c in range(3):
        P.img[..., c] = P.box(P.img[..., c], 1.6 * s)
    put(E_, 11.5, 0.5, 0.74, 0.66, trunk_pale=0.82)                             # the two pale emergent trees before it (LEAD: they stay;
    put(E_, 17.9, 0.5, 0.68, 0.68, trunk_pale=0.84)                             # their trunks no darker than their crowns)
    # THE SIDES, two ranks; TANGLE (LEAD 09:1x): plants half hidden behind others and cut by the frame's edges (placed
    # from this camera's own edges), each throwing its shade on what is behind it
    for kind, x, k, pale, lean in ((E_, 4.4, 0.9, 0.34, 0.0), ("tree", 3.5, 0.8, 0.34, 0), ("palm", 5.6, 0.9, 0.3, 0), ("tree", 5.1, 0.86, 0.3, 0), (BA, 6.3, 0.82, 0.32, 0.0),
                                   (FP, 7.3, 0.86, 0.3, 0.16), ("tree", 22.1, 0.8, 0.32, 0), (E_, 26.1, 0.94, 0.32, 0.0), ("tree", 24.9, 0.86, 0.3, 0), (BA, 23.2, 0.86, 0.3, 0.0),
                                   ("palm", 24.0, 0.92, 0.26, 0), (FP, 27.4, 0.84, 0.32, -0.14), ("tree", 28.5, 0.82, 0.34, 0)):
        shade_at(x, 0.3, k)
        if kind == "tree":
            S_.tree(x, 0.3, k, pale)
        elif kind == "palm":
            S_.palm(x, 0.25, k, pale)
        else:
            put(kind, x, 0.3, k, pale, lean=lean)
    for kind, x, k, pale, lean in ((BA, x0 + 0.2, 1.05, 0.14, 0.0), ("tree", 2.4, 1.0, 0.14, 0), (BA, 3.3, 1.0, 0.16, 0.0), (FP, 8.0, 0.98, 0.18, 0.2), ("tree", 20.9, 0.98, 0.16, 0),
                                   (FP, 20.2, 0.9, 0.18, -0.1), ("palm", 21.9, 1.0, 0.14, 0), (BA, 27.7, 1.02, 0.14, 0.0), ("tree", 29.3, 1.0, 0.14, 0),
                                   ("tree", x0 + wv + 0.6, 1.1, 0.12, 0)):
        shade_at(x, 0.12, k)
        if kind == "tree":
            S_.tree(x, 0.12, k, pale)
        elif kind == "palm":
            S_.palm(x, 0.12, k, pale)
        else:
            put(kind, x, 0.12, k, pale, lean=lean)
    liana((20.9, 3.5), (22.3, 4.1), 1.1)                                        # lianas slung between trunks
    liana((2.4, 3.7), (4.4, 4.6), 1.0)
    liana((24.0, 3.0), (26.1, 5.0), 0.9, 5)
    for kind, x, k, pale in ((FK.paddle_into, 2.0, 0.9, 0.16), (FK.heart_into, 3.9, 0.85, 0.18), (FK.paddle_into, 5.6, 0.8, 0.2), (FK.heart_into, 7.0, 0.8, 0.2),
                             (FK.paddle_into, 22.6, 0.85, 0.18), (FK.heart_into, 24.2, 0.9, 0.16), (FK.paddle_into, 26.4, 0.9, 0.16), (FK.heart_into, 28.6, 0.85, 0.18)):
        put(kind, x, 0.08, k, pale, flip=1)                                     # the understorey massed at their feet
    lap("thicket")
    # ---- THE CLEARING'S FLOOR behind the surface edge: undergrowth in level and upward dabs; the warm pool of light
    ug = fy(0.55) + 0.2 * ppm * P.line1(60 * s)
    mu = P.below(ug, 4 * s) * above
    v = 0.5 + 0.9 * P.fbm(70 * s, 2, sx=2.5) + 0.3 * np.clip((yy - fy(0.55)) / (0.55 * ppm), 0, 1)
    uu = SP.values(v, (0.42, 0.78), [rgb(c) for c in ("#6F8758", "#8DA066", "#B1B77A")])
    P.lay(uu, mu)
    P.brush(uu, mu, int(2600 * s), (5 * s, 14 * s), (2.0, 3.6), -math.pi / 2, 0.6, (0.6, 0.95), 0.05, 0.012, 3.0, 0.2)
    pool = np.maximum(P.blob(fx(12.6), fy(0.9), 6.4 * ppm, 2.3 * ppm, 0.6, 0.25), 0.6 * P.blob(fx(17.0), fy(1.2), 3.6 * ppm, 2.0 * ppm, 0.6, 0.3))
    P.glaze(above * pool, WARM, 0.75)
    P.glaze(above * (1 - pool) * np.clip(0.5 + 1.2 * P.fbm(140 * s, 2, sx=2.5), 0, 1), COOL, 0.55)
    poolrow = np.clip(pool[P.pix(0, fy(0.3))[0]] * 1.3, 0, 1).copy()
    for x, k, pale in ((6.1, 0.9, 0.16), (8.4, 0.8, 0.2), (19.9, 0.85, 0.2), (21.8, 0.95, 0.14), (25.3, 0.9, 0.16), (3.6, 1.0, 0.1)):
        S_.fern(x, 0.1, k, pale)
    # the near layer's shade on the ground beside the stage (LEAD 09:1x): violet, soft, at both sides of the warm pool
    for cx_ in (x0 + 2.6 * m_, x0 + wv - 2.2 * m_):
        P.glaze(above * P.blob(fx(cx_), fy(0.3), 3.4 * m_ * ppm, 0.55 * ppm, 0.6, 0.3), (0.72, 0.75, 0.94), 0.75)
    # a fallen log at the clearing's edge: a lying trunk, its cut end with growth rings, moss along its top, a fern on it
    lg = [(fx(19.2), fy(0.27)), (fx(20.2), fy(0.31)), (fx(21.3), fy(0.37))]
    P.glaze(above * P.blob(fx(20.0), fy(0.07), 1.3 * ppm, 0.13 * ppm, 0.6, 0.2), COOL, 0.7)
    mlog = FK.limb(P, lg, 0.2 * ppm, 0.17 * ppm, FK.hz(("#3E3438", "#5A4B44", "#7C6A58", "#A08F74"), 0.12), s=s)
    for a_, b_, c_ in ((0.19, 0.075, "#B8A078"), (0.125, 0.048, "#9A8460"), (0.06, 0.024, "#C0AA80")):
        P.dab(lg[0][0], lg[0][1], a_ * ppm, b_ * ppm, math.pi / 2 + 0.04, rgb(c_), 1.0, 4.6, 0.0)
    if mlog is not None:
        for t_ in rng.uniform(0.08, 0.98, 18):
            P.dab(lg[0][0] + (lg[2][0] - lg[0][0]) * t_, lg[0][1] + (lg[2][1] - lg[0][1]) * t_ - 0.15 * ppm, rng.uniform(5, 9) * s, 2.6 * s, rng.normal(0, 0.3), rgb("#7F9257"), 0.95, 3.6, 0.1, clip=mlog)
    S_.fern(20.7, 0.45, 0.6, 0.1, 7)
    lap("floor")
    # ---- NEAR, behind the ground's edge: the big trunk at the left and leaves hanging in from above it
    tf, s2 = S_.local(x0 + 1.3 * 64 / ppm, -0.1, 1.75, 1, 0.06)                 # (near things are placed from the frame's own edges)
    dk = [rgb(c) for c in ("#2F282C", "#463A38", "#62534A", "#84735F")]
    S_.limb(tf, s2, [(0, 0), (-4, -60), (6, -140), (2, -260), (10, -360)], 15, 12, dk, flare=16, n_per=0.045)
    S_.limb(tf, s2, [(-10, -8), (-44, 4), (-70, 12)], 10, 3, dk)
    S_.limb(tf, s2, [(12, -6), (44, 4), (66, 10)], 10, 3, dk)
    dl = [rgb(c) for c in ("#33493A", "#4A6A45", "#7C9A5C")]
    # the overhang: a bough out of the trunk across the top corner and sprays of leaves hanging from it, leaf by leaf
    # (run 1 hung fifteen single leaves in the air: they read as falling leaves)
    tx = fx(x0 + 1.3 * 64 / ppm) + 14 * s
    bough = [(tx, 96 * s), (tx + 120 * s, 62 * s), (tx + 250 * s, 50 * s), (tx + 370 * s, 66 * s)]
    S_.limb(lambda px, py: (px, py), s * 1.3, bough, 8, 2.5, dk)
    for i, t in enumerate((0.16, 0.34, 0.52, 0.7, 0.86, 1.0)):
        k = t * 3
        j0 = min(int(k), 2)
        b0 = (bough[j0][0] + (bough[j0 + 1][0] - bough[j0][0]) * (k - j0), bough[j0][1] + (bough[j0 + 1][1] - bough[j0][1]) * (k - j0) + 3 * s)
        for j in sorted(range(7), key=lambda j: abs(j - 3), reverse=True):      # each spray: seven leaves fanned downward
            a, ln = math.radians(28 + 124 * j / 6 + rng.uniform(-8, 8)), rng.uniform(0.6, 1.0) * ppm * (0.8 + 0.2 * math.sin(math.pi * j / 6))
            S_.leaf([b0, (b0[0] + math.cos(a) * ln * 0.5, b0[1] + math.sin(a) * ln * 0.42), (b0[0] + math.cos(a) * ln, b0[1] + math.sin(a) * ln)], 0.13 * ppm, dl, 0.25 + 0.75 * (1 - abs(j - 3) / 3))
    for pts in ([(tx + 190 * s, 56 * s), (tx + 150 * s, 170 * s), (tx + 80 * s, 236 * s), (tx + 26 * s, 170 * s), (tx + 6 * s, 120 * s)],
                [(tx + 330 * s, 60 * s), (tx + 338 * s, 140 * s), (tx + 326 * s, 230 * s)]):
        FK.limb(P, pts, 2.8 * s, 2.0 * s, dk, s=s)                              # lianas from the bough: a loop back to the trunk, a free end
        for px_, py_ in CEL.catmull(pts, False, 3)[1::2]:
            P.dab(px_ + 4 * s, py_ + 6 * s, 7 * s, 2.8 * s, 1.2, dl[int(rng.integers(0, 3))], 1.0, 4.8, 0.0)
    lap("near trunk")
    # ---- THE EARTH: the first frame's beds, quiet; angular stones; roots; the pit
    yb = gy + (2.2 * P.line1(38 * s) + 1.2 * P.line1(7 * s)) * s
    E = P.below(yb, 1.2)
    d = (yy - gy) / ppm
    under = rgb(SF_STRATA[0][0])
    for i in range(len(SF_STRATA) - 1):
        _c, b, soft, amp = SF_STRATA[i]
        off = amp * (P.line1(340 * s) + 0.35 * P.line1(45 * s))[None, :]
        w = np.clip((d - (b + off)) / soft + 0.5, 0, 1)
        under = lerp(under, rgb(SF_STRATA[i + 1][0]), w * w * (3 - 2 * w)).astype(np.float32)
    under *= (1 + 0.07 * P.fbm(70 * s, 2, sx=2.5))[..., None]
    deep = np.clip((d - 2.5) / 5.0, 0, 1)[..., None]
    g = under.mean(axis=2, keepdims=True)
    under = ((g + (under - g) * (0.8 - 0.28 * deep)) * (1 + deep * (np.array([0.96, 0.98, 1.04], np.float32) - 1))).astype(np.float32)
    del g
    P.lay(under, E)
    P.brush(under, E * (d > 0.3), int(8000 * s), (8 * s, 26 * s), (2.2, 4.5), 0.0, 0.25, (0.55, 0.95), 0.05, 0.012, 2.6, 0.25)
    P.brush(under, E * (d <= 0.3) * (d > 0.04), int(1500 * s), (3 * s, 9 * s), (2.0, 3.5), 0.0, 0.12, (0.6, 0.95), 0.05, 0.012, 3.0, 0.1)
    P.glaze(E * np.clip(d / 9.0, 0, 1), (0.88, 0.86, 0.93), 1.0)
    P.glaze(E * (d < 0.7) * poolrow[None, :], WARM, 0.6)
    poly = CEL.fillet([(fx(PIT_X + x) * Q, fy(-z) * Q) for x, z in PIT], 14 * s * Q)
    pit = GR._poly_mask(np.array([p[0] for p in poly]), np.array([p[1] for p in poly]), P.ph, P.pw).astype(np.float32)
    pit = np.clip((P.box(pit, 2 * s) - 0.5 + 0.20 * P.fine) * 5 + 0.5, 0, 1) * E
    for _ in range(int(26 * s)):
        wx, wz = rng.uniform(x0, x0 + W / ppm), -rng.uniform(0.9, (H - gy) / ppm - 0.3)
        if not PIT_X - 0.8 < wx < PIT_X + 5.4 or wz < -3.9:
            S_.rock(wx, wz, rng.uniform(0.14, 0.3), under[P.pix(fx(wx), fy(wz))])
    for wx in (2.3, 6.5, 11.0, 20.6, 24.1, 27.9):
        L, drift, pts = rng.uniform(0.6, 1.4) * ppm, rng.uniform(-0.5, 0.5), []
        for i in range(5):
            pts.append((fx(wx) + drift * L * (i / 4) ** 1.5 + rng.uniform(-3, 3) * (i > 0), P.at(yb, fx(wx)) + 6 * s + L * i / 4))
        P.stroke(CEL.catmull(pts, False, 5), 3.0 * s, 0.8 * s, rgb("#C4B08A") if rng.random() < 0.6 else rgb("#8F7B5E"), 4.0)
    wall = under * np.array([0.56, 0.52, 0.62], np.float32)
    del under
    P.lay(wall, pit)
    P.brush(wall, (P.box(pit, 14 * s) > 0.97).astype(np.float32), int(1300 * s), (10 * s, 26 * s), (1.6, 3.2), 0.0, 0.5, (0.5, 0.9), 0.05, 0.012, 1.8, 0.2)
    P.brush(wall, (pit > 0.9) * (P.box(pit, 5 * s) < 0.97), int(700 * s), (3 * s, 7 * s), (1.4, 2.6), 0.0, 0.8, (0.6, 0.95), 0.05, 0.012, 2.6, 0.1)
    del wall
    P.glaze(np.clip((1 - P.box(P.box(pit, 12 * s), 12 * s)) * 2.0, 0, 1) * pit, (0.62, 0.60, 0.72), 1.0)
    P.glaze(pit * np.clip((xx - fx(PIT_X + 2.3)) / (2.3 * ppm), 0, 1), (0.85, 0.84, 0.92), 0.8)
    del pit, E
    lap("earth and pit")
    # ---- THE SURFACE EDGE: covered ground - litter in the frame's own ochres and olives (larger leaves, few accents),
    # grass blades, a half-buried stone; warm in the pool, cooler beside it
    mouth = (fx(PIT_X) - 6 * s, fx(PIT_X + PIT[-1][0]) + 6 * s)
    litter = [rgb(c) for c in ("#A8935A", "#8E7A4C", "#B7A468", "#7E8452", "#9A7B4E")]

    def keyed(col, x):
        k = float(poolrow[P.pix(x, 0)[1]])
        return np.clip(col * (1 + rng.normal(0, 0.05)) * (1 + k * (WARM - 1) * 0.8) * (1 + (1 - k) * (COOL - 1) * 0.45), 0, 1)
    S_.rock(21.3, -0.12, 0.42)
    for x in rng.uniform(0, W - 1, int(260 * s)):
        if mouth[0] < x < mouth[1]:
            continue
        c, a, ln = keyed(litter[int(rng.integers(0, 5))], x), rng.uniform(-0.5, 0.5), rng.uniform(5, 9) * s
        y = P.at(yb, x) + rng.uniform(-1, 5) * s
        P.dab(x, y, ln, ln * 0.4, a, c, 1.0, 4.5, 0.0)
        P.dab(x + 0.9 * s, y - 0.9 * s, ln * 0.7, ln * 0.13, a, np.clip(c * 1.2 + 0.03, 0, 1), 0.9, 4.5, 0.0)
    for col, n in ((rgb("#5E7645"), 1200), (rgb("#7E9753"), 1100), (rgb("#A9B96C"), 420), (rgb("#C2B36E"), 120)):
        for x in rng.uniform(0, W - 1, int(n * s)):
            if mouth[0] < x < mouth[1]:
                continue
            L = (rng.uniform(16, 26) if rng.random() < 0.1 else rng.uniform(5, 14)) * s
            th = -math.pi / 2 + rng.normal(0, 0.32)
            P.dab(x + math.cos(th) * L / 2, P.at(yb, x) + 2 * s + math.sin(th) * L / 2, L / 2, rng.uniform(0.8, 1.5) * s, th, keyed(col, x), 1.0, 5.0, 0.0)
    lap("ground")
    # ---- NEAR, in front: broad-leaved plants and grass in the lower corners, dark and crisp
    # (re-planted, LEAD 09:0x: denser - a bamboo clump cutting up the right edge; paddle and heart-leaf plants, the first
    # broad-leaved plant and ferns massed in both lower corners; placed from the frame's own edges, in metres of this camera)
    wv = W / ppm                                                                # the frame's width in metres
    m_ = 64.0 / ppm                                                             # a near thing keeps its size ON SCREEN at either camera
    put(FK.bamboo_into, x0 + wv - 0.9 * m_, -0.1, 1.7, 0.0, flip=1, n=5, dark=0.5)
    for kind, dx, k in ((FK.paddle_into, 0.6, 1.45), ("plant", 1.7, 1.2), (FK.heart_into, 2.6, 1.25), (FK.heart_into, wv - 0.7, 1.4), ("plant", wv - 1.8, 1.25), (FK.paddle_into, wv - 2.9, 1.3)):
        if kind == "plant":
            S_.plant(x0 + dx * m_ if dx < wv / 2 else x0 + wv - (wv - dx) * m_, -0.12, k, 0.55)
        else:
            put(kind, x0 + dx * m_ if dx < wv / 2 else x0 + wv - (wv - dx) * m_, -0.12, k, 0.0, flip=1, dark=0.5)
    for dx, k in ((1.2, 1.3), (3.4, 1.0), (wv - 3.6, 1.1), (wv - 1.2, 1.3)):
        S_.blades(x0 + dx * m_ if dx < wv / 2 else x0 + wv - (wv - dx) * m_, -0.1, k, 34, 0.45)
    for dx, k in ((3.6, 1.2), (wv - 4.2, 1.15)):
        S_.fern(x0 + dx * m_ if dx < wv / 2 else x0 + wv - (wv - dx) * m_, -0.08, k, 0.0)
    lap("near plants")
    return P, yb, T


SF_STRATA = (("#4F4B37", 0.16, 0.03, 0.03), ("#5E4A3B", 0.55, 0.05, 0.08), ("#A8824F", 1.25, 0.08, 0.14), ("#BA965E", 1.7, 0.07, 0.12),
             ("#9C7848", 2.4, 0.08, 0.16), ("#A56B5B", 3.1, 0.09, 0.16), ("#B67C66", 3.6, 0.07, 0.12), ("#96594F", 4.5, 0.09, 0.18),
             ("#8E99A3", 5.15, 0.08, 0.14), ("#7E7682", 6.2, 0.10, 0.18), ("#74676C", 7.4, 0.10, 0.2), ("#8A7A7C", 8.1, 0.08, 0.16),
             ("#625A62", 99.0, 0.1, 0.0))                 # the first frame's beds (colour, its floor in m, edge softness, edge wander)


# ---------------------------------------------------------------- the cels
def cels(P, yb, ppm, x0, gy, K):
    """Everything that acts, drawn at K x 128 px per metre and shrunk to the painting's size."""
    t0 = time.time()
    frame, f = P.img, (K * 128) // (ppm * Q)
    fx = lambda x: (x - x0) * ppm                                               # noqa: E731

    def put(img, wx, y, ax, ay):
        """An image whose anchor (ax, ay: px of the image) goes to the frame point (world x, frame row y)."""
        SF.over(frame, img, int(round(fx(wx) * Q - ax)), int(round(y * Q - ay)))

    def shadow(wx, y, rx, ry, a=0.30):
        cx, cy, rx, ry = fx(wx) * Q, y * Q, rx * ppm / 64 * Q, ry * ppm / 64 * Q
        xa, xb, ya, yb_ = max(int(cx - rx) - 2, 0), min(int(cx + rx) + 3, P.pw), max(int(cy - ry) - 2, 0), min(int(cy + ry) + 3, P.ph)
        if xb <= xa or yb_ <= ya:
            return
        dx = (np.arange(xa, xb, dtype=np.float32)[None, :] - cx) / rx
        dy = (np.arange(ya, yb_, dtype=np.float32)[:, None] - cy) / ry
        m = (np.clip((1 - np.sqrt(dx * dx + dy * dy)) * min(rx, ry), 0, 1) * a)[..., None]
        frame[ya:yb_, xa:xb] = frame[ya:yb_, xa:xb] * (1 - m) + np.array([0.33, 0.31, 0.47], np.float32) * m

    def prop(draw, w, h, tag):
        c = CEL.Canvas(w, h, K, tag=tag)
        draw(c.dm, SF.mats(c.gp))
        paint_, line, _st = c.render()
        return CEL.down(CEL.premul(CEL.compose(paint_, CEL.dry(line, zlib.crc32(tag.encode()) & 0xFFFF))), f)

    def ground(wx):
        return round(P.at(yb, fx(wx))) + 2 * ppm / 64
    u = K / f                                                                   # painting px per design px
    cr, sm = prop(SF.crate, 150, 124, "crate"), prop(SF.smelter, 250, 320, "smelter")
    for wx in (8.9, 10.12):
        shadow(wx + 0.06, ground(wx) + 1, 40, 5)
        put(cr, wx, ground(wx), 75 * u, 116 * u)
    put(cr, 9.52, ground(9.52) - 0.78 * ppm, 75 * u, 116 * u)
    shadow(11.75, ground(11.75) + 1, 64, 6)
    put(sm, 11.75, ground(11.75), 125 * u, 306 * u)
    SV.K, SV.RHYTHM = K, True                                                    # the figure with its rhythm rules on (LEAD 09:0x)
    idle, _st, _sec = SV.figure("idle", "side", w=200, cx=96, h=290).render()
    shadow(13.25, ground(13.25) + 1, 26, 5)
    put(CEL.down(idle, f), 13.2, ground(13.2), 96 * u, 270 * u)
    fig = SV.figure("dig", "side", w=340, cx=130)
    paint_, line, _st = fig.c.render()
    dig = CEL.premul(CEL.compose(paint_, CEL.dry(line, 7), (0.86, (0.0, 0.012, 0.045))))   # re-keyed for the pit's shade
    dx_, dy_ = PIT_X + 1.75, gy + FLOOR * ppm
    shadow(dx_ + 0.2, dy_ + 1, 46, 5, 0.34)
    put(CEL.down(dig, f), dx_, dy_, 130 * u, 330 * u)
    SV.K = 4                                                                     # (RHYTHM is the figure's default now)
    clods = [prop(SF.clod(11 + i, r), 48, 48, f"clod{i}") for i, r in enumerate((16, 13, 10, 8))]
    tx, ty = dx_ + 1.36, dy_ - 0.05 * ppm                                        # about where the blade bites
    for i, (ox, oy) in enumerate(((-14, -40), (12, -66), (36, -46), (54, -22), (-34, -16), (66, -60), (22, -94))):
        im = clods[i % len(clods)]
        put(im[:, ::-1] if i % 2 else im, tx + ox / 64.0, ty + oy * ppm / 64.0, 24 * u, 24 * u)
    return time.time() - t0


# ---------------------------------------------------------------- the sheet
def preview(out):
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    t_all = time.time()
    dd = os.path.join(os.path.dirname(out), "b248_forest")
    os.makedirs(dd, exist_ok=True)
    paper = np.array(review.PAPER, np.float32)

    def head(text, h=22):
        hd = np.tile(paper, (h, W, 1)).astype(np.float32)
        review._label(hd, text, 6, 5, scale=1)
        return hd
    rows = [head("B-248 (D-200): THE ONE FRAME - Earth's forest edge with the camp, in ART v6. The same place painted twice, each at its own scale (nothing enlarged). The stage is PAINT laid by a form-following brush under one light; what acts is a CEL. PREVIEW", 26)]
    lines = []
    for name, ppm, x0, gy, K, fname in [c for c in CAMERAS if ONLY is None or c[1] in ONLY]:
        t0 = time.time()
        P, yb, T = paint(ppm, x0, gy)
        t_paint = time.time() - t0
        t_cels = cels(P, yb, ppm, x0, gy, K)
        frame = PT.tooth(P.shrunk(), 5)
        nb = pngio.write_png(os.path.join(dd, fname), np.dstack([pngio.to_u8(frame), np.full((H, W), 255, np.uint8)]))
        rows += [head(name.upper() + f": the surveyor stands {1.89 * ppm:.0f} px tall, the head {0.35 * ppm:.0f} px"), frame]
        lines.append(f"{name}: {P.count} dabs, the painting {t_paint:.0f} s (" + ", ".join(f"{k} {v:.0f}" for k, v in T.items()) + f" s), the cels {t_cels:.0f} s; b248_forest/{fname} {nb // 1024} KB")
        del P
    lines.append(f"this run: {time.time() - t_all:.0f} s for both frames")
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-248 the forest-edge frame (lock-free, numpy; nothing exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


ONLY = None                                       # the cameras to paint (px per metre), or all


if __name__ == "__main__":                       # <png> [--only 96 [64]]
    if len(sys.argv) > 3 and sys.argv[2] == "--only":
        ONLY = {int(a) for a in sys.argv[3:]}
    preview(sys.argv[1])
