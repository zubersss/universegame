"""B-248 (D-199, milestone C5): ONE STYLE FRAME of the Earth camp in ART v6 "cel on painted" - previews only.

The frame the owner judges the whole style on (docs/STYLE_V6.md): 1920x1080 at the game's zoom (64 px per metre), the
camp on the surface and a dug pit under it.
  THE PAINTING (paint_v6.py; no drawn line anywhere): a plains backdrop in three depths - far (pale, cool, soft), middle
  (clear silhouettes in two or three values), near (dark, crisp shapes at the frame's sides); the ground's surface edge
  as paint (turf, grass blades, a crumbling lip); the cut through the earth as painted strata with stones and roots; the
  dug pit as darker painted earth with a soft inner shadow; warm pools of light, violet-blue shadow between them.
  THE CELS (cel_v6.py; a pencil line and flat paint): the round 3 surveyor twice (idle at the camp, the dig pose in the
  pit), the camp's crates and smelter redrawn as cels, the shovel, a few clods in the air; a flat shadow shape under
  each.
Beside it, today's game: two of UNITY's captures (the camp, a shaft), shrunk to half size.

  python -I build_style_frame_v6.py <review png>     the lock-free sheet; the frame alone goes to <dir>/b248/
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

S, P_, F, C, hose = CEL.S, CEL.P, CEL.F, CEL.C, CEL.hose
LINE = CEL.LINE
rgb, lerp = PT.rgb, PT.lerp
W, H, PPM = 1920, 1080, 64
GY = 470                                          # the ground line's row: 7.3 m of sky and backdrop above, 9.5 m of earth below
PX0 = 930                                         # the pit's left rim (px)
PIT = [(-0.05, -0.2), (0.25, 1.0), (0.95, 1.95), (1.35, 2.95), (2.9, 3.0), (3.25, 2.72), (3.75, 2.55), (4.35, 2.2),
       (4.6, 1.1), (4.55, -0.2)]                  # the pit's outline, metres from its rim (x right, depth down)
FLOOR = 2.97                                      # ... its floor's depth where the digger stands (m)
CAPTURES = (("the camp (U-195)", "u195/5_camp_first_view_scoop.png"), ("a shaft (U-196)", "u196/1_camp_shaft_10m.png"))
REPORTS = os.path.normpath(os.path.join(HERE, "..", "..", "coordination", "reports", "unity"))


# ---------------------------------------------------------------- the painting
def paint_stage(seed=7):
    """The stage: everything that is not a cel -> (H x W x 3 float, the dabs laid, {name: seconds})."""
    P = PT.Painting(W, H, seed)
    rng = P.rng
    yy = np.arange(H, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)
    xx = np.ones((H, 1), np.float32) * np.arange(W, dtype=np.float32)[None, :]
    T, t0 = {}, time.time()

    def lap(name):
        nonlocal t0
        T[name] = time.time() - t0
        t0 = time.time()

    # ---- the sky: a graded wash laid in long level strokes; clouds as soft lobes, cream above and lavender under
    t = np.clip(yy / GY, 0, 1)
    sky = np.where(t[..., None] < 0.55, lerp(rgb("#96AFC0"), rgb("#C5CCD6"), t / 0.55), lerp(rgb("#C5CCD6"), rgb("#EADBC2"), (t - 0.55) / 0.45))
    sky = sky * (1 + 0.03 * PT.fbm(H, W, 160, rng, 2, sx=3)[..., None])
    P.img[:] = sky
    above = (yy < GY + 10).astype(np.float32)
    P.brush(sky, above, 2400, (40, 110), (3.5, 6.0), 0.0, 0.07, (0.5, 0.9), 0.022, 0.006, 1.5, 0.15)
    for cx, cy, sc in ((330, 120, 1.0), (980, 80, 1.25), (1560, 170, 0.9), (1240, 262, 0.6)):
        m = np.zeros((H, W), np.float32)
        for _ in range(6):
            m = np.maximum(m, P.blob(cx + rng.uniform(-120, 120) * sc, cy + rng.uniform(-14, 14) * sc, rng.uniform(50, 95) * sc, rng.uniform(20, 34) * sc, 0.5, 0.45))
        cl = lerp(rgb("#F3EBDC"), rgb("#C9C5D3"), np.clip((yy - (cy - 30 * sc)) / (60 * sc), 0, 1))
        P.lay(cl, m * 0.8)
        P.brush(cl, m, int(220 * sc), (12, 34), (1.3, 2.4), 0.0, 0.8, (0.4, 0.8), 0.02, 0.005, 1.4, 0.1)
    lap("sky")

    # ---- FAR: pale, cool, low contrast; two ridges of soft blobs that only suggest hills and a tree line
    # (run 1 kept all three depths in the last 120 px above the ground: the far ridges did not read. They now climb to a
    # third of the sky.)
    r1 = 262 + 46 * PT.line1(W, 520, rng) + 7 * PT.line1(W, 70, rng)
    m1 = PT.below(H, W, r1, 9.0) * above
    u1 = lerp(rgb("#A9B9CB"), rgb("#D0D3CF"), np.clip((yy - 230) / 150, 0, 1))
    P.lay(u1, m1 * 0.9)
    P.brush(u1, m1, 1300, (18, 54), (1.6, 3.2), 0.0, 0.3, (0.45, 0.8), 0.02, 0.006, 1.4, 0.1)
    r2 = 334 + 24 * PT.line1(W, 300, rng) + 7 * PT.line1(W, 30, rng)
    m2 = PT.below(H, W, r2, 6.0) * above
    u2 = lerp(rgb("#9DB1AC"), rgb("#C4CEBB"), np.clip((yy - 320) / 100, 0, 1))
    P.lay(u2, m2 * 0.9)
    P.brush(u2, m2, 1300, (14, 40), (1.5, 3.0), 0.0, 0.3, (0.45, 0.8), 0.022, 0.006, 1.5, 0.1)
    P.img = PT.box(P.img, 2)                                                    # far away everything is soft and wet
    lap("far")

    # ---- MIDDLE: a rise of rolling ground in two or three values of one sage, then the plain in level strokes, cooler at
    # its far edge, lighter and warmer toward the stage
    r3a = 388 + 17 * PT.line1(W, 330, rng) + 3 * PT.line1(W, 44, rng)
    m3a = PT.below(H, W, r3a, 2.5) * above
    v3 = 0.5 + 0.9 * PT.fbm(H, W, 110, rng, 2, sx=3.0) + 0.012 * (yy - 400)
    u3a = np.where(v3[..., None] < 0.38, rgb("#7F9370"), np.where(v3[..., None] < 0.72, rgb("#90A279"), rgb("#A6B285"))).astype(np.float32)
    P.lay(u3a, m3a)
    P.brush(u3a, m3a, 1800, (10, 30), (2.6, 5.0), 0.0, 0.18, (0.6, 0.95), 0.035, 0.01, 2.8, 0.2)
    r3 = 430 + 9 * PT.line1(W, 380, rng) + 2.5 * PT.line1(W, 40, rng)
    m3 = PT.below(H, W, r3, 2.5) * above
    u3 = lerp(rgb("#98A77C"), rgb("#B4B983"), np.clip((yy - 422) / (GY - 422), 0, 1))
    u3 = u3 * (1 + 0.05 * PT.fbm(H, W, 90, rng, 2, sx=3.0)[..., None])
    P.lay(u3, m3)
    P.brush(u3, m3, 2400, (10, 34), (3.0, 6.0), 0.0, 0.12, (0.55, 0.95), 0.04, 0.012, 2.6, 0.2)
    # light in pools: the lightest, quietest place is where the figures stand; violet-blue shadow lies between the pools
    pool = np.maximum(P.blob(900, GY - 14, 560, 46, 0.6, 0.3), P.blob(1500, GY - 8, 200, 24, 0.6, 0.3))
    pool = np.maximum(pool, P.blob(330, GY - 10, 240, 26, 0.6, 0.3))
    shade = np.clip(0.5 + 1.6 * PT.fbm(H, W, 120, rng, 2, sx=3.5), 0, 1) * (1 - pool)
    P.glaze(m3 * shade, (0.80, 0.83, 0.97), 0.9)
    P.glaze(m3 * pool, (1.10, 1.06, 0.90), 0.9)

    def tree(x, h, pale=0.0, line=None):
        """A tree of the middle distance: a clear silhouette in three values of one grey-green, lit from the upper right;
        a forked trunk, a crown of several lobes wider than it is tall (run 1's were balls on sticks)."""
        base = float((r3 if line is None else line)[int(np.clip(x, 0, W - 1))]) + 3
        lean = rng.uniform(-0.1, 0.1) * h
        tc = lerp(rgb("#6A5B50"), rgb("#A9B0A6"), pale)
        P.stroke([(x, base), (x + lean * 0.4, base - 0.25 * h), (x + lean, base - 0.5 * h)], 0.08 * h, 0.045 * h, tc, 4.0)
        for s in (-1, 1):                                                       # two boughs into the crown
            P.stroke([(x + lean * 0.5, base - 0.3 * h), (x + lean + s * 0.2 * h, base - 0.56 * h)], 0.04 * h, 0.02 * h, tc, 4.0)
        cxm, cym, R = x + lean, base - 0.66 * h, 0.30 * h
        m = np.zeros((H, W), np.float32)
        for ox, oy, k in ((-0.95, 0.15, 0.7), (-0.35, -0.3, 0.9), (0.4, -0.38, 0.85), (1.0, 0.1, 0.72), (0.05, 0.2, 0.8)):
            m = np.maximum(m, P.blob(cxm + (ox + rng.uniform(-0.15, 0.15)) * R, cym + (oy + rng.uniform(-0.1, 0.1)) * R, k * R, k * R * rng.uniform(0.7, 0.9), 0.12, 0.3))
        v = 0.5 + 0.35 * (xx - cxm) / R - 0.7 * (yy - cym) / R + 0.5 * P.fine
        dark, mid, light = (lerp(rgb(c), rgb("#B9C4B4"), pale) for c in ("#5F7A5E", "#7C9670", "#A2B685"))
        u = np.where(v[..., None] < 0.30, dark, np.where(v[..., None] < 0.8, mid, light)).astype(np.float32)
        P.lay(u, m)
        P.brush(u, m, int(0.035 * float(m.sum())), (0.035 * h, 0.085 * h), (1.4, 2.4), 0.0, 1.2, (0.7, 1.0), 0.035, 0.01, 3.6, 0.1)

    def hedge(x0, x1, hh, line, pale):
        """A hedgerow along a rise: a low band of lobes, the same three values."""
        m = np.zeros((H, W), np.float32)
        for x in np.arange(x0, x1, hh * 1.1):
            m = np.maximum(m, P.blob(x, float(line[int(np.clip(x, 0, W - 1))]) - hh * 0.3, hh * rng.uniform(0.9, 1.4), hh * rng.uniform(0.7, 1.0), 0.14, 0.35))
        v = 0.5 - 0.06 * (yy - line[None, :] + hh * 0.3) + 0.6 * P.fine
        dark, mid, light = (lerp(rgb(c), rgb("#B9C4B4"), pale) for c in ("#5F7A5E", "#7C9670", "#A2B685"))
        u = np.where(v[..., None] < 0.35, dark, np.where(v[..., None] < 0.85, mid, light)).astype(np.float32)
        P.lay(u, m)
        P.brush(u, m, int(0.03 * float(m.sum())), (3, 8), (1.4, 2.4), 0.0, 1.2, (0.7, 1.0), 0.035, 0.01, 3.4, 0.1)
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
    crown = np.zeros((H, W), np.float32)
    for cx, cy, rx, ry in ((40, 56, 150, 78), (222, 36, 160, 66), (330, 104, 92, 48), (122, 150, 112, 44), (-6, 178, 84, 58)):
        crown = np.maximum(crown, P.blob(cx, cy, rx, ry, 0.10, 0.5))
    cu = np.where((P.warp > 0.05)[..., None], rgb("#557048"), rgb("#3F5340")).astype(np.float32)
    P.lay(cu, crown)
    P.brush(cu, crown, 1000, (6, 14), (1.8, 3.0), 0.0, 1.3, (0.8, 1.0), 0.04, 0.01, 5.0, 0.1)
    P.brush(rgb("#86A262"), crown * (P.warp > 0.12) * (P.fine > 0.0), 260, (5, 11), (1.8, 3.0), -0.5, 0.9, (0.8, 1.0), 0.05, 0.012, 5.0, 0.1)
    lap("near trunk")

    # ---- THE EARTH: strata as soft bands with broken edges, laid in level dabs; no line at its surface or anywhere
    yb = GY + 2.2 * PT.line1(W, 38, rng) + 1.2 * PT.line1(W, 7, rng)
    E = PT.below(H, W, yb, 1.2)
    d = (yy - GY) / PPM                                                         # depth in metres
    # (run 1 had five fat stripes; the beds are now thinner, each a step from its neighbour, the deep rock less violet)
    strata = (("#4F4B37", 0.16, 0.03, 0.03), ("#5E4A3B", 0.55, 0.05, 0.08), ("#A8824F", 1.25, 0.08, 0.14), ("#BA965E", 1.7, 0.07, 0.12),
              ("#9C7848", 2.4, 0.08, 0.16), ("#A56B5B", 3.1, 0.09, 0.16), ("#B67C66", 3.6, 0.07, 0.12), ("#96594F", 4.5, 0.09, 0.18),
              ("#8E99A3", 5.15, 0.08, 0.14), ("#7E7682", 6.2, 0.10, 0.18), ("#74676C", 7.4, 0.10, 0.2), ("#8A7A7C", 8.1, 0.08, 0.16),
              ("#625A62", 99.0, 0.1, 0.0))
    under = np.broadcast_to(rgb(strata[0][0]), (H, W, 3)).astype(np.float32)
    for i in range(len(strata) - 1):
        _c, b, soft, amp = strata[i]
        off = amp * (PT.line1(W, 340, rng) + 0.35 * PT.line1(W, 45, rng))[None, :]
        w = np.clip((d - (b + off)) / soft + 0.5, 0, 1)
        under = lerp(under, rgb(strata[i + 1][0]), w * w * (3 - 2 * w))
    under = under * (1 + 0.07 * PT.fbm(H, W, 70, rng, 2, sx=2.5)[..., None])
    for _ in range(9):                                                          # lenses: lighter and darker pockets in the beds
        lx, ld = rng.uniform(0, W), rng.uniform(0.8, 8.5)
        m = P.blob(lx, GY + ld * PPM, rng.uniform(60, 170), rng.uniform(7, 16), 0.5, 0.3)
        under = under * (1 + (m * rng.choice([-0.12, 0.14]))[..., None])
    P.lay(under, E)
    P.brush(under, E * (d > 0.3), 9000, (8, 26), (2.2, 4.5), 0.0, 0.25, (0.55, 0.95), 0.05, 0.012, 2.6, 0.25)
    P.brush(under, E * (d <= 0.3) * (d > 0.04), 1600, (3, 9), (2.0, 3.5), 0.0, 0.12, (0.6, 0.95), 0.05, 0.012, 3.0, 0.1)
    P.glaze(E * np.clip(d / 9.0, 0, 1), (0.88, 0.86, 0.93), 1.0)                # the deep earth cooler and darker

    poly = CEL.fillet([(PX0 + x * PPM, GY + z * PPM) for x, z in PIT], 14)
    pit = GR._poly_mask(np.array([p[0] for p in poly]), np.array([p[1] for p in poly]), H, W).astype(np.float32)
    pit = np.clip((PT.box(pit, 2) - 0.5 + 0.20 * P.fine) * 5 + 0.5, 0, 1) * E    # a crumbling edge; open to the sky above
    near_pit = PT.box(pit, 16) > 0.02
    for _ in range(30):                                                         # stones: brushed shapes of three flat planes
        sx_, sd = rng.uniform(0, W), rng.uniform(0.7, 9.2)
        sy_ = GY + sd * PPM
        if near_pit[min(int(sy_), H - 1), int(sx_)]:
            continue
        a = rng.uniform(7, 20)
        b, th = a * rng.uniform(0.55, 0.75), rng.uniform(-0.3, 0.3)
        mid = lerp(rgb("#8B909B"), under[min(int(sy_), H - 1), int(sx_)], 0.25)
        P.dab(sx_ + 1.5, sy_ + 2.0, a, b, th, mid * 0.66 + np.array([0.02, 0.02, 0.06], np.float32), 1.0, 4.5, 0.0)
        P.dab(sx_ - 0.5, sy_ - 1.0, a * 0.92, b * 0.86, th, mid, 1.0, 4.5, 0.0)
        P.dab(sx_ - 0.25 * a, sy_ - 0.32 * b, a * 0.5, b * 0.42, th, np.clip(mid * 1.22 + 0.03, 0, 1), 1.0, 4.0, 0.0)
    mouth = (PX0 - 6, PX0 + PIT[-1][0] * PPM + 6)
    for x in (150, 420, 705, 1330, 1545, 1790):                                 # roots: pale brushed curves from the turf down
        L, drift, pts = rng.uniform(0.6, 1.4) * PPM, rng.uniform(-0.5, 0.5), []  # (run 1's jittered points read as cracks)
        for i in range(5):
            pts.append((x + drift * L * (i / 4) ** 1.5 + rng.uniform(-3, 3) * (i > 0), float(yb[int(x)]) + 6 + L * i / 4))
        pts = CEL.catmull(pts, False, 5)
        col = rgb("#C4B08A") if rng.random() < 0.6 else rgb("#8F7B5E")
        P.stroke(pts, rng.uniform(2.6, 3.6), 0.8, col, 4.0)
        k = len(pts) // 2
        P.stroke([pts[k], (pts[k][0] - drift * 22 - 10, pts[k][1] + 12), (pts[k][0] - drift * 30 - 16, pts[k][1] + 30)], 1.8, 0.7, col, 4.0)
    lap("earth")

    # ---- THE PIT: the same earth, darker and cooler (its back wall), a soft inner shadow, a trodden floor
    wall = under * np.array([0.56, 0.52, 0.62], np.float32)
    P.lay(wall, pit)
    P.brush(wall, (PT.box(pit, 14) > 0.97).astype(np.float32), 1300, (10, 26), (1.6, 3.2), 0.0, 0.5, (0.5, 0.9), 0.05, 0.012, 1.8, 0.2)
    P.brush(wall, (pit > 0.9).astype(np.float32) * (PT.box(pit, 5) < 0.97), 700, (3, 7), (1.4, 2.6), 0.0, 0.8, (0.6, 0.95), 0.05, 0.012, 2.6, 0.1)
    inner = np.clip((1 - PT.box(PT.box(pit, 12), 12)) * 2.0, 0, 1) * pit
    P.glaze(inner, (0.62, 0.60, 0.72), 1.0)
    P.glaze(pit * np.clip((xx - (PX0 + 2.3 * PPM)) / (2.3 * PPM), 0, 1), (0.85, 0.84, 0.92), 0.8)   # the side turned from the light
    P.stroke([(PX0 + 1.5 * PPM, GY + FLOOR * PPM - 5), (PX0 + 2.2 * PPM, GY + FLOOR * PPM - 4), (PX0 + 2.85 * PPM, GY + FLOOR * PPM - 3)], 5, 4, rgb("#8C7860"), 2.2)
    lap("pit")

    # ---- THE SURFACE EDGE as paint: grass blades over the turf, dark first, the lit ones last; a few flowers
    tones = ((rgb("#5E7645"), 1400), (rgb("#7E9753"), 1300), (rgb("#A9B96C"), 520), (rgb("#C2B36E"), 200))
    for col, n in tones:
        for x in rng.uniform(0, W - 1, n):
            if mouth[0] < x < mouth[1]:
                continue
            L = rng.uniform(16, 26) if rng.random() < 0.1 else rng.uniform(5, 14)
            th = -math.pi / 2 + rng.normal(0, 0.32)
            base = float(yb[int(x)]) + 2
            P.dab(x + math.cos(th) * L / 2, base + math.sin(th) * L / 2, L / 2, rng.uniform(0.8, 1.5), th, np.clip(col * (1 + rng.normal(0, 0.05)), 0, 1), 1.0, 5.0, 0.0)
    for x in rng.uniform(0, W - 1, 18):
        if not mouth[0] - 8 < x < mouth[1] + 8:
            P.dab(x, float(yb[int(x)]) - rng.uniform(3, 9), 1.9, 1.9, 0.0, rgb("#F0E6C8") if rng.random() < 0.6 else rgb("#E2C261"), 1.0, 5.0, 0.0)
    lap("grass")

    # ---- NEAR, the part in front of the ground: dark, saturated, crisp shapes at the frame's sides, lighter strokes on
    # their lit sides (the trunk and its crown were painted before the earth)
    bush = np.maximum(P.blob(1860, GY - 34, 96, 52, 0.10, 0.5), P.blob(1760, GY - 14, 60, 26, 0.10, 0.5))
    bu = np.where((P.warp > 0.0)[..., None], rgb("#506A46"), rgb("#3D5038")).astype(np.float32)
    P.lay(bu, bush)
    P.brush(bu, bush, 420, (5, 12), (1.8, 3.0), 0.0, 1.3, (0.8, 1.0), 0.04, 0.01, 5.0, 0.1)
    P.brush(rgb("#7F9B56"), bush * (P.fine > 0.15), 90, (4, 9), (1.8, 3.0), -0.5, 0.9, (0.8, 1.0), 0.05, 0.012, 5.0, 0.1)
    for x0, x1, n, lo, hi in ((0, 200, 46, 16, 40), (1690, W - 1, 60, 20, 54)):                                     # tall grass: broad
        for x in rng.uniform(x0, x1, n):                                                                            # blades (run 1's thin
            L, th = rng.uniform(lo, hi), -math.pi / 2 + rng.normal(0, 0.22)                                         # ones read as pen lines)
            col = rgb("#7F9B56") if rng.random() < 0.18 else (rgb("#3D5038") if rng.random() < 0.6 else rgb("#4C6340"))
            base = float(yb[int(x)]) + 3
            P.stroke([(x, base), (x + math.cos(th) * L * 0.5, base + math.sin(th) * L * 0.5), (x + math.cos(th + 0.25) * L, base + math.sin(th + 0.25) * L)], 5.5, 1.2, col, 5.0)
    lap("near")
    P.tooth(0.014)
    return P.done(), P.count, T, yb


# ---------------------------------------------------------------- the cels
TONES = {"wood": "#9A7650", "red": "#C8553D", "cream": "#F2E6CF", "brass": "#D9A93F", "belly": "#6E5241", "teal": "#3E8A86",
         "soot": "#4A4242", "glow": "#E8923F", "glow_hi": "#F6CE6A", "steel": "#B4C3C4", "earth": "#B08A5A", "smoke": "#F2E6CF"}


def mats(gp):
    M = {"ln": CEL.mat(gp, "p_ln")}
    for k, h in TONES.items():
        M[k] = CEL.mat(gp, f"p_{k}", fill=h)
        M[k + "_f"] = CEL.mat(gp, f"p_{k}_f", fill=h, line=False)
    return M


def crate(d, M):
    """The camp's storage crate as a cel (150 x 124 design px, its foot on row 116): wood, a red band and brass corners as
    paint patches, two plank lines."""
    S(d, [(11, 16), (139, 16), (139, 116), (11, 116)], M["wood"], LINE, cyclic=True, rnd=3, keep="box")
    P_(d, [(5, 56), (145, 56), (145, 80), (5, 80)], M["red_f"], sharp=True, clip="box")
    P_(d, [(66, 62), (84, 62), (84, 74), (66, 74)], M["cream_f"], rnd=2)
    for cx, cy, sx, sy in ((11, 16, 1, 1), (139, 16, -1, 1), (139, 116, -1, -1), (11, 116, 1, -1)):
        P_(d, [(cx, cy), (cx + 17 * sx, cy), (cx, cy + 17 * sy)], M["brass_f"], sharp=True, clip="box")
    F(d, M, [(18, 36), (75, 35), (132, 36)])
    F(d, M, [(18, 98), (75, 99), (132, 98)])


def smelter(d, M):
    """The camp's smelter as a cel (250 x 320 design px, its feet on row 306): a round belly on splayed legs, a hopper, a
    chimney; the brass bands and the fire's core are paint patches. (No knob beside the door: a dot over an arch is a face.)"""
    S(d, [(80, 236), (100, 242), (86, 306), (62, 306)], M["brass"], LINE, cyclic=True, rnd=3, gap=0)
    S(d, [(150, 242), (170, 236), (190, 306), (166, 306)], M["brass"], LINE, cyclic=True, rnd=3, gap=0)
    S(d, [(160, 62), (184, 62), (184, 150), (160, 150)], M["teal"], LINE, cyclic=True, rnd=2)
    S(d, [(153, 50), (191, 50), (191, 63), (153, 63)], M["soot"], LINE * 0.9, cyclic=True, rnd=2, gap=0)
    S(d, [(38, 98), (106, 98), (90, 152), (56, 152)], M["brass"], LINE, cyclic=True, rnd=3)
    S(d, [(32, 88), (112, 88), (112, 100), (32, 100)], M["brass"], LINE * 0.9, cyclic=True, rnd=2, gap=0)
    S(d, C(125, 192, 94, 48, ry=70), M["belly"], LINE, cyclic=True, at=0.3, keep="belly")
    for y in (154, 222):
        P_(d, [(20, y), (230, y), (230, y + 9), (20, y + 9)], M["brass_f"], sharp=True, clip="belly")
    S(d, [(88, 212), (88, 186), (96, 172), (110, 166), (124, 172), (132, 186), (132, 212)], M["glow"], LINE * 0.9, cyclic=True, rnd=5, gap=0, keep="door")
    P_(d, [(98, 212), (98, 192), (110, 182), (122, 192), (122, 212)], M["glow_hi_f"], rnd=4, clip="door")
    P_(d, C(176, 30, 11, 16, ry=9), M["smoke_f"])                                # two puffs: a cel effect, flat, no line
    P_(d, C(189, 12, 7, 14, ry=6), M["smoke_f"])


def shovel(d, M):
    """B-226's shovel as a cel, on its own sprite's layout (192 x 64 design px, the grip at (12.8, 32), the tip 1.33 m on)."""
    S(d, hose([(18, 32), (124, 32)], 5.0), M["teal"], LINE * 0.8, cyclic=True, gap=0)
    S(d, [(5, 22), (13, 22), (13, 42), (5, 42)], M["brass"], LINE * 0.8, cyclic=True, rnd=3, gap=0)
    blade = [(12.8 + 128 * x, 32 + 128 * y) for x, y in ((0.97, -0.13), (1.04, -0.145), (1.14, -0.14), (1.25, -0.10), (1.33, 0.0),
                                                          (1.25, 0.10), (1.14, 0.14), (1.04, 0.145), (0.97, 0.13))]
    S(d, blade, M["steel"], LINE, cyclic=True, rnd=4)
    P_(d, [(118, 28), (130, 28), (130, 36), (118, 36)], M["brass_f"], rnd=1.5, under=False)


def clod(seed, r):
    def draw(d, M):
        rng = np.random.default_rng(seed)
        pts = [(24 + r * (1 + rng.uniform(-0.2, 0.2)) * math.cos(TAU_ * i / 8), 24 + 0.8 * r * (1 + rng.uniform(-0.2, 0.2)) * math.sin(TAU_ * i / 8)) for i in range(8)]
        S(d, pts, M["earth"], LINE * 0.75, cyclic=True, rnd=3, gap=0)
    return draw


TAU_ = 2 * math.pi


def cel_layers(draw, w, h, band=0, tag="prop"):
    """A prop drawn as a cel at the large size -> straight RGBA uint8 (K = 4), and its line stats."""
    c = CEL.Canvas(w, h, 4, tag=tag)
    draw(c.dm, mats(c.gp))
    paint, line, st = c.render()
    if band:
        paint = CEL.shade(paint, band, 4)
    return CEL.compose(paint, CEL.dry(line, zlib.crc32(tag.encode()) & 0xFFFF)), st


def over(dst, img, x, y):
    """A premultiplied float image over the opaque frame, its top-left at (x, y), clipped."""
    h, w = img.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    s = img[y0 - y:y1 - y, x0 - x:x1 - x]
    dst[y0:y1, x0:x1] = s[..., :3] + dst[y0:y1, x0:x1] * (1 - s[..., 3:4])


def shadow(dst, cx, cy, rx, ry, a=0.30):
    """A cel's shadow on the painting: ONE flat violet shape (the film's shadow cel), a clean edge, no blend."""
    x0, x1, y0, y1 = max(int(cx - rx) - 2, 0), min(int(cx + rx) + 3, W), max(int(cy - ry) - 2, 0), min(int(cy + ry) + 3, H)
    dx = (np.arange(x0, x1, dtype=np.float32)[None, :] - cx) / rx
    dy = (np.arange(y0, y1, dtype=np.float32)[:, None] - cy) / ry
    m = (np.clip((1 - np.sqrt(dx * dx + dy * dy)) * min(rx, ry), 0, 1) * a)[..., None]
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - m) + np.array([0.33, 0.31, 0.47], np.float32) * m


def cels(frame, yb):
    """Everything that acts, laid on the painting -> (the pencil's stats, seconds)."""
    t0 = time.time()
    stats = []

    def prop(draw, w, h, band, tag, f=8):
        u8, st = cel_layers(draw, w, h, band, tag)
        stats.extend(st)
        return CEL.down(CEL.premul(u8), f)

    def ground(x):
        return int(round(float(yb[int(x)]))) + 2
    cr, sm = prop(crate, 150, 124, 10, "crate"), prop(smelter, 250, 320, 14, "smelter")
    for x in (286, 364):                                                        # two crates and one on them; each foot on row 58
        shadow(frame, x + 4, ground(x) + 1, 40, 5)
        over(frame, cr, x - 37, ground(x) - 58)
    over(frame, cr, 326 - 37, ground(326) - 58 - 50)
    shadow(frame, 536, ground(536) + 1, 64, 6)
    over(frame, sm, 536 - 62, ground(536) - 153)
    P, _lay = SV.all_parts()
    for st in SV.STATS.values():
        stats.extend(st)
    idle = CEL.down(SV.pose_image(P, "side", SV.POSES["idle"]), 8)
    fx = 744
    shadow(frame, fx + 2, ground(fx) + 1, 30, 5)
    over(frame, idle, fx - SV.PCX * SV.K // 8, ground(fx) - SV.PG * SV.K // 8)
    sh_u8, st = cel_layers(shovel, 192, 64, 3, "shovel")
    stats.extend(st)
    # the digger stands in the pit's shadow: the whole figure's PAINT re-keyed a step darker and cooler (STYLE_V6 2.5),
    # the pencil the same
    PK, _lay = SV.all_parts(paint_of=_lay, key=(0.86, (0.0, 0.012, 0.045)))
    dig = CEL.down(SV.pose_image(PK, "side", SV.POSES["dig"], prop=(sh_u8, (12.8 * 4, 32 * 4), SV.DIG_AIM)), 8)
    dx, dy = PX0 + int(2.02 * PPM), GY + int(FLOOR * PPM)
    shadow(frame, dx + 6, dy + 1, 44, 5, 0.34)
    over(frame, dig, dx - SV.PCX * SV.K // 8, dy - SV.PG * SV.K // 8)
    w = SV.solve("side", SV.POSES["dig"])                                       # the blade's tip: where the clods leave from
    hx, hz, ha = w["hand_f"]
    t = math.radians(ha)
    gx, gz = hx + SV.GRIP[0] * math.cos(t) - SV.GRIP[1] * math.sin(t), hz + SV.GRIP[0] * math.sin(t) + SV.GRIP[1] * math.cos(t)
    ta = math.radians(ha + SV.DIG_AIM)
    tx, ty = dx + (gx + 1.33 * math.cos(ta)) * PPM, dy - (gz + 1.33 * math.sin(ta)) * PPM
    clods = [prop(clod(11 + i, r), 48, 48, 3, f"clod{i}") for i, r in enumerate((16, 13, 10, 8))]   # (run 1's were dark specks)
    for i, (ox, oy) in enumerate(((-14, -40), (12, -66), (36, -46), (54, -22), (-34, -16), (66, -60), (22, -94))):
        im = clods[i % len(clods)]
        im = im[:, ::-1] if i % 2 else im
        over(frame, im, int(tx + ox) - 12, int(ty + oy) - 12)
    return stats, time.time() - t0, (tx, ty)


# ---------------------------------------------------------------- today's game, for comparison
def read_png(path):
    """An 8-bit RGB or RGBA PNG -> H x W x 3 float (numpy only; UNITY's captures are RGB, which pngio does not read)."""
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
    return out.reshape(h, w, bpp)[..., :3].astype(np.float32) / 255.0


def today(cache_dir):
    """UNITY's two captures at half size (block means), cached beside the preview (decoding them is slow)."""
    out = []
    for label, rel in CAPTURES:
        src = os.path.join(REPORTS, *rel.split("/"))
        npy = os.path.join(cache_dir, "today_" + rel.split("/")[0] + ".npy")
        if os.path.isfile(npy):
            out.append((label, np.load(npy)))
        elif os.path.isfile(src):
            im = read_png(src)
            hh, ww = im.shape[0] // 2 * 2, im.shape[1] // 2 * 2
            im = im[:hh, :ww].reshape(hh // 2, 2, ww // 2, 2, 3).mean(axis=(1, 3)).astype(np.float32)
            np.save(npy, im)
            out.append((label, im))
    return out


# ---------------------------------------------------------------- the sheet
def preview(out):
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    t0 = time.time()
    dd = os.path.join(os.path.dirname(out), "b248")
    os.makedirs(dd, exist_ok=True)
    frame, dabs, T, yb = paint_stage()
    t_stage = time.time() - t0
    stats, t_cels, tip = cels(frame, yb)
    mean_w, min_w, max_w, n_lines = CEL.line_stats(stats)
    u8 = np.dstack([pngio.to_u8(np.clip(frame, 0, 1)), np.full((H, W), 255, np.uint8)])
    nbytes = pngio.write_png(os.path.join(dd, "style_frame_v6.png"), u8)
    paper = np.array(review.PAPER, np.float32)

    def head(text, h=22):
        hd = np.tile(paper, (h, W, 1)).astype(np.float32)
        review._label(hd, text, 6, 5, scale=1)
        return hd
    rows = [head("B-248 (D-199): ONE STYLE FRAME in ART v6 'cel on painted' - the Earth camp at the game's zoom (1920x1080, 64 px per metre). The stage is PAINT (no drawn line); what acts is a CEL (pencil line, flat paint). PREVIEW", 26),
            frame]
    caps = today(dd)
    if caps:
        rows.append(head("TODAY'S GAME for comparison, at half size: " + " | ".join(lb for lb, _im in caps)))
        r = np.tile(paper, (max(im.shape[0] for _lb, im in caps), W, 1)).astype(np.float32)
        x = 0
        for _lb, im in caps:
            r[:im.shape[0], x:x + im.shape[1]] = im[:, :W - x]
            x += im.shape[1]
        rows.append(r)
    lines = [f"THE PAINTING: {dabs} brush dabs over soft underpaintings, no line; {t_stage:.0f} s (" + ", ".join(f"{k} {v:.1f}" for k, v in T.items()) + " s)",
             f"THE CELS: the surveyor twice, three crates, the smelter, the shovel, seven clods; {n_lines} pencil strokes, mean {mean_w:.2f} px ({min_w:.2f}-{max_w:.2f}); {t_cels:.0f} s",
             f"the frame alone: b248/style_frame_v6.png, {nbytes // 1024} KB; this run {time.time() - t0:.0f} s"]
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-248 style frame preview (lock-free, numpy; nothing exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)
    print(f"the blade's tip at ({tip[0]:.0f}, {tip[1]:.0f}) px; the pit's floor row {GY + FLOOR * PPM:.0f}")


if __name__ == "__main__":
    preview(sys.argv[1])
