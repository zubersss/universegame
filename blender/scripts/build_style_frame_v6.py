"""B-248 (D-199, milestone C5): ONE STYLE FRAME of the Earth camp in ART v6 "cel on painted" - previews only.

The frame the owner judges the whole style on (docs/STYLE_V6.md): 1920x1080 at the game's zoom (64 px per metre), the
camp on the surface and a dug pit under it.
  THE PAINTING (paint_v6.py; no drawn line anywhere): a plains backdrop in three depths - far (pale, cool, soft), middle
  (clear silhouettes in two or three values), near (dark, crisp shapes at the frame's sides); the ground's surface edge
  as paint (turf, grass blades, a crumbling lip); the cut through the earth as painted beds with stones and roots; the
  dug pit as darker painted earth with a soft inner shadow; a warm pool of light at the camp, violet-blue shadow beside.
  THE CELS (cel_v6.py; a pencil line and flat paint): the round 3 surveyor twice (idle at the camp; the dig pose in the
  pit, its paint re-keyed for the pit's shadow), the camp's crates and smelter redrawn as cels, the shovel, a few clods
  in the air; ONE flat shadow shape under each.
Everything is made at TWICE the game's size (Q = 2: the painting at 3840x2160, the cels shrunk 4 times from their 512 px
per metre drawings) and the frame is that picture shrunk; the sheet's 2x close-ups are windows of it (D-198: nothing is
ever enlarged). Under the frame, today's game in the same view at the same size (UNITY's capture u195).

  python -I build_style_frame_v6.py <review png>     the lock-free sheet; the frame and the crops go to <dir>/b248/
"""
import math
import os
import struct
import sys
import time
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio  # noqa: E402
import cel_v6 as CEL  # noqa: E402
import paint_v6 as PT  # noqa: E402
import build_surveyor_v5 as SV  # noqa: E402
import gp_raster as GR  # noqa: E402

S, P_, F, C = CEL.S, CEL.P, CEL.F, CEL.C
LINE = CEL.LINE
rgb, lerp = PT.rgb, PT.lerp
W, H, PPM, Q = 1920, 1080, 64, 2
GY = 470                                          # the ground line's row: 7.3 m of sky and backdrop above, 9.5 m of earth below
PX0 = 930                                         # the pit's left rim (frame px)
PIT = [(-0.05, -0.2), (0.25, 1.0), (0.95, 1.95), (1.35, 2.95), (2.9, 3.0), (3.25, 2.72), (3.75, 2.55), (4.35, 2.2),
       (4.6, 1.1), (4.55, -0.2)]                  # the pit's outline, metres from its rim (x right, depth down)
FLOOR = 2.97                                      # ... its floor's depth where the digger stands (m)
TODAY = ("the camp, UNITY's capture U-195", "u195/5_camp_first_view_scoop.png")
REPORTS = os.path.normpath(os.path.join(HERE, "..", "..", "coordination", "reports", "unity"))
WARM, COOL = np.array([1.16, 1.10, 0.86], np.float32), np.array([0.76, 0.80, 0.98], np.float32)   # a pool of light; the shadow beside it


# ---------------------------------------------------------------- the painting
def paint_stage(seed=7):
    """The stage: everything that is not a cel -> (the Painting, the surface line per pixel column, {name: seconds})."""
    P = PT.Painting(W, H, seed, Q)
    rng, yy, xx = P.rng, P.yy, P.xx
    T, t0 = {}, time.time()

    def lap(name):
        nonlocal t0
        T[name] = time.time() - t0
        t0 = time.time()

    def three(v, a, b, c0, c1, c2):
        """Three flat values of one hue, by a field v: dark below a, light above b."""
        return np.where((v < a)[..., None], c0, np.where((v < b)[..., None], c1, c2)).astype(np.float32)

    # ---- the sky: a graded wash laid in long level strokes; clouds as soft lobes, cream above and lavender under
    t = np.clip(yy / GY, 0, 1)
    sky = np.where(t[..., None] < 0.55, lerp(rgb("#96AFC0"), rgb("#C5CCD6"), t / 0.55), lerp(rgb("#C5CCD6"), rgb("#EADBC2"), (t - 0.55) / 0.45))
    sky = (sky * (1 + 0.03 * P.fbm(160, 2, sx=3)[..., None])).astype(np.float32)
    P.img[:] = sky
    above = (yy < GY + 10).astype(np.float32)
    P.brush(sky, above, 2400, (40, 110), (3.5, 6.0), 0.0, 0.07, (0.5, 0.9), 0.022, 0.006, 1.5, 0.15)
    del sky
    for cx, cy, sc in ((330, 120, 1.0), (980, 80, 1.25), (1560, 170, 0.9)):
        m = np.zeros((P.ph, P.pw), np.float32)
        for _ in range(6):
            m = np.maximum(m, P.blob(cx + rng.uniform(-120, 120) * sc, cy + rng.uniform(-14, 14) * sc, rng.uniform(50, 95) * sc, rng.uniform(20, 34) * sc, 0.5, 0.45))
        cl = lerp(rgb("#F3EBDC"), rgb("#C9C5D3"), np.clip((yy - (cy - 30 * sc)) / (60 * sc), 0, 1))
        P.lay(cl, m * 0.8)
        P.brush(cl, m, int(220 * sc), (12, 34), (1.3, 2.4), 0.0, 0.8, (0.4, 0.8), 0.02, 0.005, 1.4, 0.1)
    lap("sky")

    # ---- FAR: pale, cool, low contrast; two ridges of soft blobs that only suggest hills and a tree line
    r1 = 262 + 46 * P.line1(520) + 7 * P.line1(70)
    m1 = P.below(r1, 9.0) * above
    u1 = lerp(rgb("#A9B9CB"), rgb("#D0D3CF"), np.clip((yy - 230) / 150, 0, 1))
    P.lay(u1, m1 * 0.9)
    P.brush(u1, m1, 1300, (18, 54), (1.6, 3.2), 0.0, 0.3, (0.45, 0.8), 0.02, 0.006, 1.4, 0.1)
    r2 = 334 + 24 * P.line1(300) + 7 * P.line1(30)
    m2 = P.below(r2, 6.0) * above
    u2 = lerp(rgb("#9DB1AC"), rgb("#C4CEBB"), np.clip((yy - 320) / 100, 0, 1))
    P.lay(u2, m2 * 0.9)
    P.brush(u2, m2, 1300, (14, 40), (1.5, 3.0), 0.0, 0.3, (0.45, 0.8), 0.022, 0.006, 1.5, 0.1)
    del m1, m2
    for c in range(3):                                                          # far away everything is soft and wet
        P.img[..., c] = P.box(P.img[..., c], 2)
    lap("far")

    # ---- MIDDLE: a rise of rolling ground in three values of one sage, then the plain in level strokes, cooler at its
    # far edge, lighter and warmer toward the stage
    r3a = 388 + 17 * P.line1(330) + 3 * P.line1(44)
    m3a = P.below(r3a, 2.5) * above
    u3a = three(0.5 + 0.9 * P.fbm(110, 2, sx=3.0) + 0.012 * (yy - 400), 0.38, 0.72, rgb("#7F9370"), rgb("#90A279"), rgb("#A6B285"))
    P.lay(u3a, m3a)
    P.brush(u3a, m3a, 1800, (10, 30), (2.6, 5.0), 0.0, 0.18, (0.6, 0.95), 0.035, 0.01, 2.8, 0.2)
    del u3a
    r3 = 430 + 9 * P.line1(380) + 2.5 * P.line1(40)
    m3 = P.below(r3, 2.5) * above
    u3 = lerp(rgb("#98A77C"), rgb("#B4B983"), np.clip((yy - 422) / (GY - 422), 0, 1))
    u3 = (u3 * (1 + 0.05 * P.fbm(90, 2, sx=3.0)[..., None])).astype(np.float32)
    P.lay(u3, m3)
    P.brush(u3, m3, 2400, (10, 34), (3.0, 6.0), 0.0, 0.12, (0.55, 0.95), 0.04, 0.012, 2.6, 0.2)
    del u3
    # LIGHT IN POOLS (LEAD 07:2x (4)): ONE clear warm patch on the ground where the surveyor, the crates and the smelter
    # stand; cooler violet either side of it (a fainter second pool far right)
    pool = np.maximum(P.blob(540, GY - 14, 400, 44, 0.5, 0.25), 0.5 * P.blob(1560, GY - 8, 170, 22, 0.6, 0.3))
    ground = np.maximum(m3, 0.6 * m3a)
    P.glaze(ground * np.clip(0.55 + 1.4 * P.fbm(120, 2, sx=3.5), 0, 1) * (1 - pool), COOL, 1.0)
    P.glaze(ground * pool, WARM, 1.0)
    poolrow = pool[P.pix(0, GY - 8)[0]].copy()                                  # the pool along the ground, per pixel column
    del pool, ground, m3, m3a

    def crown(m, cxm, cym, R, pale, n_per, lo, hi):
        """A crown's paint: three values of one grey-green by height and side (lit from the upper right), then leaf dabs."""
        rows, cols = np.flatnonzero(m.any(axis=1)), np.flatnonzero(m.any(axis=0))
        if not len(rows):
            return
        y0, y1, x0, x1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
        v = 0.5 + 0.35 * (xx[:, x0:x1] - cxm) / R - 0.7 * (yy[y0:y1] - cym) / R + 0.5 * P.fine[y0:y1, x0:x1]
        u = np.zeros((P.ph, P.pw, 3), np.float32)
        u[y0:y1, x0:x1] = three(v, 0.30, 0.8, *(lerp(rgb(c), rgb("#B9C4B4"), pale) for c in ("#5F7A5E", "#7C9670", "#A2B685")))
        P.lay(u, m)
        P.brush(u, m, int(n_per * float(m.sum()) / (Q * Q)), (lo, hi), (1.4, 2.4), 0.0, 1.2, (0.7, 1.0), 0.035, 0.01, 3.6, 0.1)

    def tree(x, h, pale=0.0, line=None):
        """A tree of the middle distance: a clear silhouette on a forked trunk, a crown of several lobes wider than tall."""
        base = P.at(r3 if line is None else line, x) + 3
        lean = rng.uniform(-0.1, 0.1) * h
        tc = lerp(rgb("#6A5B50"), rgb("#A9B0A6"), pale)
        P.stroke([(x, base), (x + lean * 0.4, base - 0.25 * h), (x + lean, base - 0.5 * h)], 0.08 * h, 0.045 * h, tc, 4.0)
        for s in (-1, 1):                                                       # two boughs into the crown
            P.stroke([(x + lean * 0.5, base - 0.3 * h), (x + lean + s * 0.2 * h, base - 0.56 * h)], 0.04 * h, 0.02 * h, tc, 4.0)
        cxm, cym, R = x + lean, base - 0.66 * h, 0.30 * h
        m = np.zeros((P.ph, P.pw), np.float32)
        for ox, oy, k in ((-0.95, 0.15, 0.7), (-0.35, -0.3, 0.9), (0.4, -0.38, 0.85), (1.0, 0.1, 0.72), (0.05, 0.2, 0.8)):
            m = np.maximum(m, P.blob(cxm + (ox + rng.uniform(-0.15, 0.15)) * R, cym + (oy + rng.uniform(-0.1, 0.1)) * R, k * R, k * R * rng.uniform(0.7, 0.9), 0.12, 0.3))
        crown(m, cxm, cym, R, pale, 0.035, 0.035 * h, 0.085 * h)

    def hedge(x0, x1, hh, line, pale):
        """A hedgerow along a rise: a low band of lobes, the same three values."""
        m = np.zeros((P.ph, P.pw), np.float32)
        for x in np.arange(x0, x1, hh * 1.1):
            m = np.maximum(m, P.blob(x, P.at(line, x) - hh * 0.3, hh * rng.uniform(0.9, 1.4), hh * rng.uniform(0.7, 1.0), 0.14, 0.35))
        crown(m, (x0 + x1) / 2, P.at(line, (x0 + x1) / 2) - hh * 0.3, hh * 3.0, pale, 0.03, 3, 8)
    hedge(300, 520, 9, r3a, 0.35)
    hedge(1250, 1500, 10, r3a, 0.35)
    for x, h, pale in ((640, 52, 0.4), (700, 40, 0.45), (1120, 44, 0.45), (880, 34, 0.5), (1700, 60, 0.35)):       # on the rise
        tree(x, h, pale, r3a)
    for x, h, pale in ((230, 96, 0.1), (300, 70, 0.15), (420, 60, 0.2), (1400, 74, 0.15), (1585, 124, 0.0), (1650, 84, 0.05)):   # on the plain
        tree(x, h, pale)
    lap("middle")

    # ---- NEAR, the part behind the ground: a dark trunk at the left edge and its crown (crisp leaf dabs, lit strokes)
    tr = [(70, GY + 8), (62, 380), (76, 250), (68, 120), (90, -10)]
    P.stroke(tr, 48, 34, rgb("#4B4144"), 4.5)
    P.stroke([(86, GY + 2), (80, 380), (93, 250), (86, 130), (104, 0)], 9, 7, rgb("#7B6B5E"), 3.0)                   # its lit plane
    for _ in range(46):                                                                                             # bark: dry strokes
        y = rng.uniform(0, GY)
        cxt = float(np.interp(y, [p[1] for p in tr][::-1], [p[0] for p in tr][::-1]))
        P.dab(cxt + rng.uniform(-9, 9), y, rng.uniform(4, 8), rng.uniform(1.2, 2.2), rng.normal(0.15, 0.2), rgb("#3A3236") if rng.random() < 0.6 else rgb("#6B5D55"), 0.9, 4.0, 0.3)
    cm = np.zeros((P.ph, P.pw), np.float32)
    for cx, cy, rx, ry in ((40, 56, 150, 78), (222, 36, 160, 66), (330, 104, 92, 48), (122, 150, 112, 44), (-6, 178, 84, 58)):
        cm = np.maximum(cm, P.blob(cx, cy, rx, ry, 0.10, 0.5))
    cu = np.where((P.warp > 0.05)[..., None], rgb("#557048"), rgb("#3F5340")).astype(np.float32)
    P.lay(cu, cm)
    P.brush(cu, cm, 1000, (6, 14), (1.8, 3.0), 0.0, 1.3, (0.8, 1.0), 0.04, 0.01, 5.0, 0.1)
    P.brush(rgb("#86A262"), cm * (P.warp > 0.12) * (P.fine > 0.0), 260, (5, 11), (1.8, 3.0), -0.5, 0.9, (0.8, 1.0), 0.05, 0.012, 5.0, 0.1)
    del cu, cm
    lap("near trunk")

    # ---- THE EARTH: beds as soft bands with broken edges, laid in level dabs; no line at its surface or anywhere.
    # LEAD 07:2x (1): quieter than the cels - the beds a fifth less saturated, the lower ones greyer and cooler still
    yb = GY + 2.2 * P.line1(38) + 1.2 * P.line1(7)
    E = P.below(yb, 1.2)
    d = (yy - GY) / PPM                                                         # depth in metres
    strata = (("#4F4B37", 0.16, 0.03, 0.03), ("#5E4A3B", 0.55, 0.05, 0.08), ("#A8824F", 1.25, 0.08, 0.14), ("#BA965E", 1.7, 0.07, 0.12),
              ("#9C7848", 2.4, 0.08, 0.16), ("#A56B5B", 3.1, 0.09, 0.16), ("#B67C66", 3.6, 0.07, 0.12), ("#96594F", 4.5, 0.09, 0.18),
              ("#8E99A3", 5.15, 0.08, 0.14), ("#7E7682", 6.2, 0.10, 0.18), ("#74676C", 7.4, 0.10, 0.2), ("#8A7A7C", 8.1, 0.08, 0.16),
              ("#625A62", 99.0, 0.1, 0.0))
    under = rgb(strata[0][0])
    for i in range(len(strata) - 1):
        _c, b, soft, amp = strata[i]
        off = amp * (P.line1(340) + 0.35 * P.line1(45))[None, :]
        w = np.clip((d - (b + off)) / soft + 0.5, 0, 1)
        under = lerp(under, rgb(strata[i + 1][0]), w * w * (3 - 2 * w)).astype(np.float32)
    under *= (1 + 0.07 * P.fbm(70, 2, sx=2.5))[..., None]
    for _ in range(9):                                                          # lenses: lighter and darker pockets in the beds
        m = P.blob(rng.uniform(0, W), GY + rng.uniform(0.8, 8.5) * PPM, rng.uniform(60, 170), rng.uniform(7, 16), 0.5, 0.3)
        under *= (1 + m * rng.choice([-0.12, 0.14]))[..., None]
    deep = np.clip((d - 2.5) / 5.0, 0, 1)[..., None]
    g = under.mean(axis=2, keepdims=True)
    under = ((g + (under - g) * (0.8 - 0.28 * deep)) * (1 + deep * (np.array([0.96, 0.98, 1.04], np.float32) - 1))).astype(np.float32)
    del g
    P.lay(under, E)
    P.brush(under, E * (d > 0.3), 9000, (8, 26), (2.2, 4.5), 0.0, 0.25, (0.55, 0.95), 0.05, 0.012, 2.6, 0.25)
    P.brush(under, E * (d <= 0.3) * (d > 0.04), 1600, (3, 9), (2.0, 3.5), 0.0, 0.12, (0.6, 0.95), 0.05, 0.012, 3.0, 0.1)
    P.glaze(E * np.clip(d / 9.0, 0, 1), (0.88, 0.86, 0.93), 1.0)                # the deep earth cooler and darker
    P.glaze(E * (d < 0.7) * poolrow[None, :], WARM, 0.6)                        # the camp's light on the turf

    poly = CEL.fillet([((PX0 + x * PPM) * Q, (GY + z * PPM) * Q) for x, z in PIT], 14 * Q)
    pit = GR._poly_mask(np.array([p[0] for p in poly]), np.array([p[1] for p in poly]), P.ph, P.pw).astype(np.float32)
    pit = np.clip((P.box(pit, 2) - 0.5 + 0.20 * P.fine) * 5 + 0.5, 0, 1) * E     # a crumbling edge; open to the sky above
    near_pit = P.box(pit, 16) > 0.02

    def stone(sx_, sy_, a):
        """A stone (LEAD 07:2x (2): run 2's were glossy beads): an angular shape of five to seven corners with a brushed
        edge, in two or three FLAT planes - its top lit, its underside dark, no highlight."""
        n = int(rng.integers(5, 8))
        ang, rad = np.sort(rng.uniform(0, 2 * math.pi, n)), a * rng.uniform(0.6, 1.0, n)
        sq, th = rng.uniform(0.55, 0.8), rng.uniform(-0.4, 0.4)
        px = (sx_ + rad * np.cos(ang) * math.cos(th) - rad * sq * np.sin(ang) * math.sin(th)) * Q
        py = (sy_ + rad * np.cos(ang) * math.sin(th) + rad * sq * np.sin(ang) * math.cos(th)) * Q
        x0, x1, y0, y1 = max(int(px.min()) - 4, 0), min(int(px.max()) + 5, P.pw), max(int(py.min()) - 4, 0), min(int(py.max()) + 5, P.ph)
        if x1 <= x0 or y1 <= y0:
            return
        m = GR._poly_mask(px, py, P.ph, P.pw)[y0:y1, x0:x1].astype(np.float32)
        m = np.clip((PT.box(m, Q) - 0.5 + 0.22 * P.fine[y0:y1, x0:x1]) * 4 + 0.5, 0, 1)[..., None]
        mid = lerp(rgb("#8E8F96"), under[P.pix(sx_, sy_)], 0.35)
        k = th + rng.uniform(-0.3, 0.3)
        v = (yy[y0:y1] - sy_) * math.cos(k) - (xx[:, x0:x1] - sx_) * math.sin(k)   # the height across the stone
        col = np.where((v < -0.16 * a * sq)[..., None], mid * 1.13, np.where((v > 0.30 * a * sq)[..., None], mid * 0.72, mid))
        P.img[y0:y1, x0:x1] = P.img[y0:y1, x0:x1] * (1 - m) + col * m
    for _ in range(38):
        sx_, sy_ = rng.uniform(0, W), GY + rng.uniform(0.7, 9.2) * PPM
        if not near_pit[P.pix(sx_, sy_)]:
            stone(sx_, sy_, rng.uniform(9, 22))
    mouth = (PX0 - 6, PX0 + PIT[-1][0] * PPM + 6)
    for x in (150, 420, 705, 1330, 1545, 1790):                                 # roots: pale brushed curves from the turf down
        L, drift, pts = rng.uniform(0.6, 1.4) * PPM, rng.uniform(-0.5, 0.5), []
        for i in range(5):
            pts.append((x + drift * L * (i / 4) ** 1.5 + rng.uniform(-3, 3) * (i > 0), P.at(yb, x) + 6 + L * i / 4))
        pts = CEL.catmull(pts, False, 5)
        col = rgb("#C4B08A") if rng.random() < 0.6 else rgb("#8F7B5E")
        P.stroke(pts, rng.uniform(2.6, 3.6), 0.8, col, 4.0)
        k = len(pts) // 2
        P.stroke([pts[k], (pts[k][0] - drift * 22 - 10, pts[k][1] + 12), (pts[k][0] - drift * 30 - 16, pts[k][1] + 30)], 1.8, 0.7, col, 4.0)
    lap("earth")

    # ---- THE PIT: the same earth, darker and cooler (its back wall), a soft inner shadow, a trodden floor
    wall = under * np.array([0.56, 0.52, 0.62], np.float32)
    del under
    P.lay(wall, pit)
    P.brush(wall, (P.box(pit, 14) > 0.97).astype(np.float32), 1300, (10, 26), (1.6, 3.2), 0.0, 0.5, (0.5, 0.9), 0.05, 0.012, 1.8, 0.2)
    P.brush(wall, (pit > 0.9) * (P.box(pit, 5) < 0.97), 700, (3, 7), (1.4, 2.6), 0.0, 0.8, (0.6, 0.95), 0.05, 0.012, 2.6, 0.1)
    del wall
    P.glaze(np.clip((1 - P.box(P.box(pit, 12), 12)) * 2.0, 0, 1) * pit, (0.62, 0.60, 0.72), 1.0)
    P.glaze(pit * np.clip((xx - (PX0 + 2.3 * PPM)) / (2.3 * PPM), 0, 1), (0.85, 0.84, 0.92), 0.8)   # the side turned from the light
    P.stroke([(PX0 + 1.5 * PPM, GY + FLOOR * PPM - 5), (PX0 + 2.2 * PPM, GY + FLOOR * PPM - 4), (PX0 + 2.85 * PPM, GY + FLOOR * PPM - 3)], 5, 4, rgb("#8C7860"), 2.2)
    del pit, near_pit, E
    lap("pit")

    # ---- THE SURFACE EDGE as paint: grass blades over the turf, dark first, the lit ones last (warm in the camp's pool of
    # light, cooler beside it); a few flowers
    for col, n in ((rgb("#5E7645"), 1400), (rgb("#7E9753"), 1300), (rgb("#A9B96C"), 520), (rgb("#C2B36E"), 200)):
        for x in rng.uniform(0, W - 1, n):
            if mouth[0] < x < mouth[1]:
                continue
            L = rng.uniform(16, 26) if rng.random() < 0.1 else rng.uniform(5, 14)
            th = -math.pi / 2 + rng.normal(0, 0.32)
            k = float(poolrow[P.pix(x, 0)[1]])
            c = col * (1 + rng.normal(0, 0.05)) * (1 + k * (WARM - 1) * 0.8) * (1 + (1 - k) * (COOL - 1) * 0.45)
            base = P.at(yb, x) + 2
            P.dab(x + math.cos(th) * L / 2, base + math.sin(th) * L / 2, L / 2, rng.uniform(0.8, 1.5), th, np.clip(c, 0, 1), 1.0, 5.0, 0.0)
    for x in rng.uniform(0, W - 1, 18):
        if not mouth[0] - 8 < x < mouth[1] + 8:
            P.dab(x, P.at(yb, x) - rng.uniform(3, 9), 1.9, 1.9, 0.0, rgb("#F0E6C8") if rng.random() < 0.6 else rgb("#E2C261"), 1.0, 5.0, 0.0)
    lap("grass")

    # ---- NEAR, the part in front of the ground: dark, saturated, crisp shapes at the frame's right side, lighter strokes
    # on their lit sides
    bush = np.maximum(P.blob(1860, GY - 34, 96, 52, 0.10, 0.5), P.blob(1760, GY - 14, 60, 26, 0.10, 0.5))
    bu = np.where((P.warp > 0.0)[..., None], rgb("#506A46"), rgb("#3D5038")).astype(np.float32)
    P.lay(bu, bush)
    P.brush(bu, bush, 420, (5, 12), (1.8, 3.0), 0.0, 1.3, (0.8, 1.0), 0.04, 0.01, 5.0, 0.1)
    P.brush(rgb("#7F9B56"), bush * (P.fine > 0.15), 90, (4, 9), (1.8, 3.0), -0.5, 0.9, (0.8, 1.0), 0.05, 0.012, 5.0, 0.1)
    del bu, bush
    for x0, x1, n, lo, hi in ((0, 200, 46, 16, 40), (1690, W - 1, 60, 20, 54)):                                     # tall grass: broad blades
        for x in rng.uniform(x0, x1, n):
            L, th = rng.uniform(lo, hi), -math.pi / 2 + rng.normal(0, 0.22)
            col = rgb("#7F9B56") if rng.random() < 0.18 else (rgb("#3D5038") if rng.random() < 0.6 else rgb("#4C6340"))
            base = P.at(yb, x) + 3
            P.stroke([(x, base), (x + math.cos(th) * L * 0.5, base + math.sin(th) * L * 0.5), (x + math.cos(th + 0.25) * L, base + math.sin(th + 0.25) * L)], 5.5, 1.2, col, 5.0)
    lap("near")
    return P, yb, T


# ---------------------------------------------------------------- the cels
TONES = {"wood": "#9A7650", "red": "#C8553D", "cream": "#F2E6CF", "brass": "#D9A93F", "belly": "#6E5241", "teal": "#3E8A86",
         "soot": "#4A4242", "glow": "#E8923F", "glow_hi": "#F6CE6A", "earth": "#B08A5A", "smoke": "#F2E6CF"}


def mats(gp):
    M = {"ln": CEL.mat(gp, "p_ln")}
    for k, h in TONES.items():
        M[k] = CEL.mat(gp, f"p_{k}", fill=h)
        M[k + "_f"] = CEL.mat(gp, f"p_{k}_f", fill=h, line=False)
    return M


def crate(d, M):
    """The camp's storage crate as a cel (150 x 124 design px, its foot on row 116): wood, a red band and brass corners as
    paint patches, two plank lines, one flat shadow along its foot."""
    S(d, [(11, 16), (139, 16), (139, 116), (11, 116)], M["wood"], LINE, cyclic=True, rnd=3, keep="box")
    P_(d, [(5, 56), (145, 56), (145, 80), (5, 80)], M["red_f"], sharp=True, clip="box")
    P_(d, [(66, 62), (84, 62), (84, 74), (66, 74)], M["cream_f"], rnd=2)
    for cx, cy, sx, sy in ((11, 16, 1, 1), (139, 16, -1, 1), (139, 116, -1, -1), (11, 116, 1, -1)):
        P_(d, [(cx, cy), (cx + 17 * sx, cy), (cx, cy + 17 * sy)], M["brass_f"], sharp=True, clip="box")
    P_(d, [(5, 100), (145, 100), (145, 120), (5, 120)], M["wood_f"], sharp=True, clip="box", shade=True)
    F(d, M, [(18, 36), (75, 35), (132, 36)])
    F(d, M, [(18, 98), (75, 99), (132, 98)])


def smelter(d, M):
    """The camp's smelter as a cel (250 x 320 design px, its feet on row 306): a round belly on splayed legs, a hopper, a
    chimney; the brass bands and the fire's core are paint patches, the belly's underside one flat shadow. (No knob beside
    the door: a dot over an arch is a face.)"""
    S(d, [(80, 236), (100, 242), (86, 306), (62, 306)], M["brass"], LINE, cyclic=True, rnd=3, gap=0)
    S(d, [(150, 242), (170, 236), (190, 306), (166, 306)], M["brass"], LINE, cyclic=True, rnd=3, gap=0)
    S(d, [(160, 62), (184, 62), (184, 150), (160, 150)], M["teal"], LINE, cyclic=True, rnd=2)
    S(d, [(153, 50), (191, 50), (191, 63), (153, 63)], M["soot"], LINE * 0.9, cyclic=True, rnd=2, gap=0)
    S(d, [(38, 98), (106, 98), (90, 152), (56, 152)], M["brass"], LINE, cyclic=True, rnd=3)
    S(d, [(32, 88), (112, 88), (112, 100), (32, 100)], M["brass"], LINE * 0.9, cyclic=True, rnd=2, gap=0)
    S(d, C(125, 192, 94, 48, ry=70), M["belly"], LINE, cyclic=True, at=0.3, keep="belly")
    for y in (154, 222):
        P_(d, [(20, y), (230, y), (230, y + 9), (20, y + 9)], M["brass_f"], sharp=True, clip="belly")
    P_(d, [(20, 236), (230, 236), (230, 270), (20, 270)], M["belly_f"], sharp=True, clip="belly", shade=True)
    S(d, [(88, 212), (88, 186), (96, 172), (110, 166), (124, 172), (132, 186), (132, 212)], M["glow"], LINE * 0.9, cyclic=True, rnd=5, gap=0, keep="door")
    P_(d, [(98, 212), (98, 192), (110, 182), (122, 192), (122, 212)], M["glow_hi_f"], rnd=4, clip="door")
    P_(d, C(176, 30, 11, 16, ry=9), M["smoke_f"])                                # two puffs: a cel effect, flat, no line
    P_(d, C(189, 12, 7, 14, ry=6), M["smoke_f"])


def clod(seed, r):
    def draw(d, M):
        rng = np.random.default_rng(seed)
        pts = [(24 + r * (1 + rng.uniform(-0.2, 0.2)) * math.cos(2 * math.pi * i / 8), 24 + 0.8 * r * (1 + rng.uniform(-0.2, 0.2)) * math.sin(2 * math.pi * i / 8)) for i in range(8)]
        S(d, pts, M["earth"], LINE * 0.75, cyclic=True, rnd=3, gap=0)
    return draw


def cel_image(draw, w, h, tag):
    """A prop drawn as a cel at the large size, shrunk to the painting's size -> (premultiplied float, its line stats)."""
    c = CEL.Canvas(w, h, 4, tag=tag)
    draw(c.dm, mats(c.gp))
    paint, line, st = c.render()
    return CEL.down(CEL.premul(CEL.compose(paint, CEL.dry(line, zlib.crc32(tag.encode()) & 0xFFFF))), 8 // Q), st


def over(dst, img, x, y):
    """A premultiplied float image over the opaque picture, its top-left at pixel (x, y), clipped."""
    h, w = img.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    s = img[y0 - y:y1 - y, x0 - x:x1 - x]
    dst[y0:y1, x0:x1] = s[..., :3] + dst[y0:y1, x0:x1] * (1 - s[..., 3:4])


def cels(P, yb):
    """Everything that acts, laid on the painting (frame units in) -> (the pencil's stats, seconds, the blade's tip)."""
    t0 = time.time()
    frame, stats = P.img, []

    def put(img, fx, fy, ax, ay):
        """An image with its anchor (ax, ay: frame units inside it) at the frame point (fx, fy)."""
        over(frame, img, int(round((fx - ax) * Q)), int(round((fy - ay) * Q)))

    def shadow(cx, cy, rx, ry, a=0.30):
        """A cel's shadow on the painting: ONE flat violet shape (the film's shadow cel), a clean edge, no blend."""
        cx, cy, rx, ry = cx * Q, cy * Q, rx * Q, ry * Q
        x0, x1, y0, y1 = max(int(cx - rx) - 2, 0), min(int(cx + rx) + 3, P.pw), max(int(cy - ry) - 2, 0), min(int(cy + ry) + 3, P.ph)
        dx = (np.arange(x0, x1, dtype=np.float32)[None, :] - cx) / rx
        dy = (np.arange(y0, y1, dtype=np.float32)[:, None] - cy) / ry
        m = (np.clip((1 - np.sqrt(dx * dx + dy * dy)) * min(rx, ry), 0, 1) * a)[..., None]
        frame[y0:y1, x0:x1] = frame[y0:y1, x0:x1] * (1 - m) + np.array([0.33, 0.31, 0.47], np.float32) * m

    def prop(draw, w, h, tag):
        im, st = cel_image(draw, w, h, tag)
        stats.extend(st)
        return im

    def ground(x):
        return round(P.at(yb, x)) + 2
    cr, sm = prop(crate, 150, 124, "crate"), prop(smelter, 250, 320, "smelter")
    for x in (286, 364):                                                        # two crates and one on them
        shadow(x + 4, ground(x) + 1, 40, 5)
        put(cr, x, ground(x), 37.5, 58)
    put(cr, 326, ground(326) - 50, 37.5, 58)
    shadow(536, ground(536) + 1, 64, 6)
    put(sm, 536, ground(536), 62.5, 153)
    parts, lay = SV.all_parts()
    for st in SV.STATS.values():
        stats.extend(st)
    ax, ay = SV.PCX / 2, SV.PG / 2                                              # a pose cell's feet, in frame units
    fx = 744
    shadow(fx + 2, ground(fx) + 1, 30, 5)
    put(CEL.down(SV.pose_image(parts, "side", SV.POSES["idle"]), 8 // Q), fx, ground(fx), ax, ay)
    # the digger stands in the pit's shadow: the whole figure's PAINT re-keyed a step darker and cooler (STYLE_V6 2.5),
    # the pencil the same
    keyed, _lay = SV.all_parts(paint_of=lay, key=(0.86, (0.0, 0.012, 0.045)))
    sh_u8, sh_piv = SV.shovel_cel()
    dx, dy = PX0 + int(2.02 * PPM), GY + int(FLOOR * PPM)
    shadow(dx + 6, dy + 1, 44, 5, 0.34)
    put(CEL.down(SV.pose_image(keyed, "side", SV.POSES["dig"], prop=(sh_u8, sh_piv, SV.DIG_AIM)), 8 // Q), dx, dy, ax, ay)
    w = SV.solve("side", SV.POSES["dig"])                                       # the blade's tip: where the clods leave from
    hx, hz, ha = w["hand_f"]
    t = math.radians(ha)
    gx, gz = hx + SV.GRIP[0] * math.cos(t) - SV.GRIP[1] * math.sin(t), hz + SV.GRIP[0] * math.sin(t) + SV.GRIP[1] * math.cos(t)
    ta = math.radians(ha + SV.DIG_AIM)
    tx, ty = dx + (gx + 1.33 * math.cos(ta)) * PPM, dy - (gz + 1.33 * math.sin(ta)) * PPM
    clods = [prop(clod(11 + i, r), 48, 48, f"clod{i}") for i, r in enumerate((16, 13, 10, 8))]
    for i, (ox, oy) in enumerate(((-14, -40), (12, -66), (36, -46), (54, -22), (-34, -16), (66, -60), (22, -94))):
        im = clods[i % len(clods)]
        put(im[:, ::-1] if i % 2 else im, tx + ox, ty + oy, 12, 12)
    return stats, time.time() - t0, (tx, ty)


# ---------------------------------------------------------------- today's game, for comparison
def read_png(path):
    """An 8-bit RGB or RGBA PNG -> H x W x 3 uint8 (numpy only; UNITY's captures are RGB, which pngio does not read)."""
    data = open(path, "rb").read()
    pos, idat = 8, b""
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        tag, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        if tag == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", body[:10])
            if bd != 8 or ct not in (2, 6):
                raise ValueError(f"{path}: bit depth {bd}, colour type {ct}")
        elif tag == b"IDAT":
            idat += body
        pos += 12 + n
    bpp = 3 if ct == 2 else 4
    raw = zlib.decompress(idat)
    stride = w * bpp
    out = np.zeros((h, stride), np.uint8)
    prev = np.zeros(stride, np.int32)
    for y in range(h):
        f = raw[y * (stride + 1)]
        cur = np.frombuffer(raw, np.uint8, stride, y * (stride + 1) + 1).astype(np.int32)
        if f == 1:
            cur = (np.cumsum(cur.reshape(-1, bpp), axis=0) & 255).reshape(-1)
        elif f == 2:
            cur = (cur + prev) & 255
        elif f in (3, 4):
            c, p = cur.tolist(), prev.tolist()
            for x in range(stride):
                a = c[x - bpp] if x >= bpp else 0
                b = p[x]
                if f == 3:
                    c[x] = (c[x] + (a + b) // 2) & 255
                else:
                    cc = p[x - bpp] if x >= bpp else 0
                    q = a + b - cc
                    pa, pb, pc = abs(q - a), abs(q - b), abs(q - cc)
                    c[x] = (c[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else cc)) & 255
            cur = np.array(c, np.int32)
        out[y] = cur
        prev = cur
    return out.reshape(h, w, bpp)[..., :3].copy()


def today(cache_dir):
    """UNITY's capture of the camp at its own size (H x W x 3 float), cached beside the preview (decoding it is slow)."""
    label, rel = TODAY
    src = os.path.join(REPORTS, *rel.split("/"))
    npy = os.path.join(cache_dir, "today_" + rel.split("/")[0] + "_full.npy")
    if os.path.isfile(npy):
        return label, np.load(npy).astype(np.float32) / 255.0
    if not os.path.isfile(src):
        return label, None
    im = read_png(src)
    np.save(npy, im)
    return label, im.astype(np.float32) / 255.0


# ---------------------------------------------------------------- the sheet
CROPS = (("the surveyor and the smelter on the painting", "crop_surveyor_2x.png", (440, 300, 900, 500)),
         ("the pit's edge", "crop_pit_2x.png", (900, 440, 1260, 680)))          # frame windows (x0, y0, x1, y1), shown at 2x


def preview(out):
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    t0 = time.time()
    dd = os.path.join(os.path.dirname(out), "b248")
    os.makedirs(dd, exist_ok=True)
    P, yb, T = paint_stage()
    t_stage = time.time() - t0
    stats, t_cels, tip = cels(P, yb)
    mean_w, min_w, max_w, n_lines = CEL.line_stats(stats)
    frame = PT.tooth(P.shrunk(), 5)

    def save(name, rgbf):
        return pngio.write_png(os.path.join(dd, name), np.dstack([pngio.to_u8(np.clip(rgbf, 0, 1)), np.full(rgbf.shape[:2], 255, np.uint8)]))
    nbytes = save("style_frame_v6.png", frame)
    paper = np.array(review.PAPER, np.float32)

    def head(text, h=22):
        hd = np.tile(paper, (h, W, 1)).astype(np.float32)
        review._label(hd, text, 6, 5, scale=1)
        return hd
    rows = [head("B-248 (D-199): ONE STYLE FRAME in ART v6 'cel on painted' - the Earth camp at the game's zoom (1920x1080, 64 px per metre). The stage is PAINT (no drawn line); what acts is a CEL (pencil line, flat paint). PREVIEW", 26),
            frame]
    label, cap = today(dd)
    if cap is not None:
        rows.append(head(f"TODAY'S GAME in the same view at the same size: {label} (with its HUD)"))
        r = np.tile(paper, (cap.shape[0], W, 1)).astype(np.float32)
        r[:, :min(W, cap.shape[1])] = cap[:, :W]
        rows.append(r)
    rows.append(head("AT 2x (windows of the picture as it was made, at twice the game's size; nothing enlarged): " + " | ".join(c[0] for c in CROPS)))
    r = np.tile(paper, (max((c[2][3] - c[2][1]) * Q for c in CROPS) + 8, W, 1)).astype(np.float32)
    x = 4
    for i, (_label, name, (x0, y0, x1, y1)) in enumerate(CROPS):
        c = PT.tooth(np.clip(P.img[y0 * Q:y1 * Q, x0 * Q:x1 * Q], 0, 1), 11 + i)
        save(name, c)
        r[4:4 + c.shape[0], x:x + c.shape[1]] = c
        x += c.shape[1] + 16
    rows.append(r)
    lines = [f"THE PAINTING: {P.count} brush dabs over soft underpaintings, no line, made at {P.pw}x{P.ph} and shrunk; {t_stage:.0f} s (" + ", ".join(f"{k} {v:.1f}" for k, v in T.items()) + " s)",
             f"THE CELS: the surveyor twice (the digger's paint re-keyed for the pit's shadow), three crates, the smelter, the shovel, seven clods; {n_lines} pencil strokes, mean {mean_w:.2f} px at the game's zoom ({min_w:.2f}-{max_w:.2f}); {t_cels:.0f} s",
             f"files in b248/: style_frame_v6.png ({nbytes // 1024} KB), " + ", ".join(c[1] for c in CROPS) + f"; this run {time.time() - t0:.0f} s"]
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-248 style frame preview (lock-free, numpy; nothing exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)
    print(f"the blade's tip at ({tip[0]:.0f}, {tip[1]:.0f}) frame px; the pit's floor row {GY + FLOOR * PPM:.0f}")


if __name__ == "__main__":
    preview(sys.argv[1])
