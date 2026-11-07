"""C2 Earth prep for LEAD (D-109 while-waiting): a cartoon Earth ground strip to replace U-100's
placeholder, in the same contract: `terrain/earth/ground_strip`, 8 frames of 64x128 px (1 m wide x
2 m tall at PPU 64), one per terrain column, every frame joining every other at the column edges.

Frame anatomy (metres, x -0.5..0.5, z 0..2): the ground surface line at z = SURF (2.5 px ink, the
same height at both edges of every frame), a dusty-green grass lip above it with tufts that never
cross an edge, flat dirt below with one mid-shadow band under the lip, and per-frame interior detail
(pebbles, a root, strata hatch, specks) kept >= 5 px from the edges so tiles join cleanly; the
bottom 24 px are plain dirt = the fill tile UNITY cuts for the depth below. v3.1 ink, no faces.

  python -I build_c2_ground_strip.py <out.png>     (lock-free: meridian.fakegp, no Blender)
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp  # noqa: E402

G = fakegp.install()
P = G.PALETTES["earth"]
O, I = G.OUTER, G.INNER
SURF = 1.62                        # the surface line height inside the 2 m frame
EDGE = 5 / 64.0                    # detail keeps this far from the column edges
DIRT = G.rgb_hex([0.62 * a + 0.38 * b for a, b in zip(G.hex_rgb(P["brown"]), G.hex_rgb(P["mustard"]))])


def mats(gp):
    return {
        "dirt": G.mat(gp, "dirt", fill=DIRT, ink=False),
        "dirt_sh": G.mat(gp, "dirt_mid", fill=G.shadow_of(DIRT), ink=False),
        "dirt_dp": G.mat(gp, "dirt_deep", fill=G.deep_of(DIRT), ink=False),
        "grass": G.mat(gp, "grass", fill=P["green"], ink=False),
        "grass_sh": G.mat(gp, "grass_mid", fill=G.shadow_of(P["green"]), ink=False),
        "tuft": G.mat(gp, "tuft", fill=P["green"], behind=True),
        "pebble": G.mat(gp, "pebble", fill=G.shadow_of(P["offwhite"])),
        "ink": G.mat(gp, "ink", fill=None, ink=True),
    }


def frame(d, M, k):
    rnd = random.Random(1000 + k)
    L, R = -0.5, 0.5
    # dirt body (full frame below the surface) + the mid band under the lip
    G.stroke(d, [(L, 0.0), (R, 0.0), (R, SURF), (L, SURF)], M["dirt"], 0.0, cyclic=True)
    G.stroke(d, [(L, SURF - 0.20), (R, SURF - 0.20), (R, SURF), (L, SURF)], M["dirt_sh"], 0.0, cyclic=True)
    # grass lip: a wavy band above the surface whose ends sit at the same height on both edges
    lip = [(x, SURF + 0.10 + 0.03 * math.sin(math.pi * (x - L) * (2 + k % 3)) * math.sin(math.pi * (x - L)))
           for x in [L + i / 16 for i in range(17)]]
    G.stroke(d, [(L, SURF - 0.03)] + lip + [(R, SURF - 0.03)], M["grass"], 0.0, cyclic=True)
    G.stroke(d, [(L, SURF - 0.03)] + [(x, z - 0.06) for x, z in lip] + [(R, SURF - 0.03)], M["grass_sh"], 0.0, cyclic=True)
    # tufts (never crossing an edge): ink-behind blades
    for t in range(2 + k % 3):
        cx = rnd.uniform(L + EDGE + 0.08, R - EDGE - 0.08)
        for b in range(3):
            a = math.radians(-25 + 25 * b + rnd.uniform(-8, 8))
            h = rnd.uniform(0.13, 0.22)
            base = SURF + 0.06
            tip = (cx + h * math.sin(a), base + h * math.cos(a))
            blade = [(cx - 0.018, base), tip, (cx + 0.018, base)]
            G.stroke(d, blade, M["tuft"], I, cyclic=True)
    # the surface ink line: same z at both edges, a slight bow and wobble between
    surf = [(x, SURF + 0.012 * math.sin(math.pi * (x - L)) * (1 if k % 2 else -1)) for x in [L + i / 12 for i in range(13)]]
    G.stroke(d, surf, M["ink"], O)
    # interior detail, kept off the edges
    for p in range(rnd.randint(1, 3)):                             # pebbles
        px, pz = rnd.uniform(L + EDGE + 0.06, R - EDGE - 0.06), rnd.uniform(0.55, SURF - 0.32)
        r = rnd.uniform(0.035, 0.06)
        G.stroke(d, G.lumpy_ellipse(px, pz, r * 1.3, r, n=14, lump=0.08, seed=k * 10 + p), M["pebble"], I, cyclic=True)
        G.seam(d, [(px - r * 0.6, pz - r * 0.2), (px + r * 0.5, pz - r * 0.45)], M["ink"])
    if k % 2 == 0:                                                 # a root curling down from the lip
        rx = rnd.uniform(L + EDGE + 0.15, R - EDGE - 0.15)
        G.seam(d, G.bezier((rx, SURF - 0.02), (rx + 0.10, SURF - 0.25), (rx - 0.05, SURF - 0.45), n=8), M["ink"])
        G.seam(d, G.bezier((rx + 0.04, SURF - 0.22), (rx + 0.10, SURF - 0.28), (rx + 0.13, SURF - 0.36), n=5), M["ink"])
    hx, hz = rnd.uniform(L + EDGE + 0.12, R - EDGE - 0.12), rnd.uniform(0.6, 1.15)
    G.hatch(d, hx, hz, M["ink"], n=3, length=0.09, spacing=0.03, angle_deg=rnd.choice((15, 165)), seed=k)   # strata scratches
    G.specks(d, [(rnd.uniform(L + EDGE, R - EDGE), rnd.uniform(0.45, SURF - 0.25)) for _ in range(4)], M["ink"])
    G.stroke(d, G.lumpy_ellipse(rnd.uniform(L + EDGE + 0.1, R - EDGE - 0.1), rnd.uniform(0.7, 1.2), 0.06, 0.035, n=12, seed=k + 50),
             M["dirt_dp"], 0.0, cyclic=True)                       # a darker clod


def main(out):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import v3
    gp = fakegp.FakeGP()
    M = mats(gp)
    frames, allw = [], []
    for k in range(8):
        d = fakegp.FakeDrawing()
        frame(d, M, k)
        img, w = fakegp.render(d, gp, 64, 128, pivot=(0.5, 0.0), ss=4, seed=k + 1)
        frames.append(img)
        allw += w
    # edge check: every frame's left column vs every frame's right column (they must join)
    worst = 0.0
    for a in frames:
        for b in frames:
            worst = max(worst, float(np.abs(a[:, -1, :3].astype(np.int32) - b[:, 0, :3].astype(np.int32)).mean()))
    W = 8 + 8 * (64 * 3 + 8) + 16
    sky = np.array([0.62, 0.72, 0.72], np.float32)
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "c2 earth ground strip design (terrain/earth/ground_strip, 8 frames 64x128 = 1x2 m, joins at every edge); lock-free fakegp", 6, 8)
    big = np.tile(sky, (128 * 3 + 40, W, 1)).astype(np.float32)
    for j, im in enumerate(frames):
        review._over(big, np.repeat(np.repeat(im, 3, 0), 3, 1), 8 + j * (64 * 3 + 8), 20)
        review._label(big, f"frame {j}", 8 + j * (64 * 3 + 8), 4)
    # 1x mock: 20 columns of random frames, one column dug 1 m deeper (its walls inked like U-100's edge)
    mock = np.tile(sky, (340, W, 1)).astype(np.float32)
    rnd = np.random.default_rng(4)
    x0 = 40
    for c in range(20):
        im = frames[int(rnd.integers(0, 8))]
        dz = 64 if c == 9 else 0
        review._over(mock, im, x0 + c * 64, 120 + dz)
        mock[120 + dz + 128:, x0 + c * 64:x0 + c * 64 + 64] = np.array(v3.hex_rgb(DIRT), np.float32) / 255   # the fill below
        if c == 9:
            mock[120 + 104:120 + dz + 104, x0 + c * 64:x0 + c * 64 + 2] = 0.12
            mock[120 + 104:120 + dz + 104, x0 + c * 64 + 62:x0 + c * 64 + 64] = 0.12
    review._label(mock, "1x: 20 columns of random frames + the flat fill below; column 9 dug 1 m (ink walls as U-100 draws them)", 6, 6)
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior "
                        f"{min(w[1] for w in inner):.1f}-{max(w[2] for w in inner):.1f} px; edge join: mean |left - right| over all "
                        f"frame pairs {worst:.1f}/255; dirt {DIRT}", 6, 8)
    review._label(foot, "lead: approve the look, then it exports as a v3 sheet under the gate (one 1004x260 png)", 6, 28)
    review.write(out, np.vstack([head, big, mock, foot]))
    print("written", out, "edge", round(worst, 2))


if __name__ == "__main__":
    main(sys.argv[1])
