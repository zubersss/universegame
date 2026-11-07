"""C2 Earth prep for LEAD (D-109 while-waiting list): five faceless Earth plant designs.

Personality through motion only (Bible 4.1 §9.3, D-101: no eyes or mouths on plants); v3.1 ink
(2-3 px outline, 1-1.5 px detail) with veins, ribs, spines and texture marks; mid + deep tones.
Each plant is a drawing function (d, M, pose) in local metres with the root at (0, 0), so the same
code can later become a §11.3 rig set (parts per bone) like the snoozle. Rendered lock-free with
meridian.fakegp into blender/preview/review_c2_earth_plants_preview.png (no Blender):

  python -I build_c2_earth_plants.py <out.png>
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp  # noqa: E402

G = fakegp.install()
P = G.PALETTES["earth"]
O, I = G.OUTER, G.INNER


def mats(gp):
    return {
        "stem": G.mat(gp, "stem", fill=P["green"]), "blade": G.mat(gp, "blade", fill=P["green"], behind=True), "blade_sh": G.mat(gp, "blade_mid", fill=G.shadow_of(P["green"]), behind=True), "stem_fill": G.mat(gp, "stem_f", fill=P["green"], ink=False),
        "stem_sh": G.mat(gp, "stem_mid", fill=G.shadow_of(P["green"]), ink=False),
        "stem_dp": G.mat(gp, "stem_deep", fill=G.deep_of(P["green"]), ink=False),
        "bell": G.mat(gp, "bell_sky", fill=P["sky"]), "bell_sh": G.mat(gp, "bell_mid", fill=G.shadow_of(P["sky"]), ink=False),
        "bell_in": G.mat(gp, "bell_deep", fill=G.deep_of(P["sky"]), ink=False),
        "cactus": G.mat(gp, "cactus", fill=P["teal"]), "cactus_fill": G.mat(gp, "cactus_f", fill=P["teal"], ink=False),
        "cactus_sh": G.mat(gp, "cactus_mid", fill=G.shadow_of(P["teal"]), ink=False),
        "cactus_dp": G.mat(gp, "cactus_deep", fill=G.deep_of(P["teal"]), ink=False),
        "mustard": G.mat(gp, "mustard", fill=P["mustard"]), "mustard_sh": G.mat(gp, "mustard_mid", fill=G.shadow_of(P["mustard"]), ink=False),
        "red": G.mat(gp, "red", fill=P["red"]), "red_sh": G.mat(gp, "red_mid", fill=G.shadow_of(P["red"]), ink=False),
        "red_dp": G.mat(gp, "red_deep", fill=G.deep_of(P["red"]), ink=False),
        "offwhite": G.mat(gp, "offwhite", fill=P["offwhite"]),
        "brown": G.mat(gp, "brown", fill=P["brown"]), "brown_dp": G.mat(gp, "brown_deep", fill=G.deep_of(P["brown"]), ink=False),
        "ink": G.mat(gp, "ink", fill=None, ink=True),
    }


def rot(pts, a, cx=0.0, cz=0.0):
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (z - cz) * sa, cz + (x - cx) * sa + (z - cz) * ca) for x, z in pts]


def hose_stem(d, M, center, width, rib_every=0.10):
    out = G.hose_outline(center, width)
    G.stroke(d, out, M["stem_fill"], 0.0, cyclic=True)
    G.stroke(d, G.hose_outline([(x + width * 0.25, z) for x, z in center], width * 0.35), M["stem_sh"], 0.0, cyclic=True)
    G.ribs(d, center[1:-1], width, M["ink"], every=rib_every, frac=0.55)
    G.stroke(d, out, M["ink"], O, cyclic=True)


def leaf(d, M, base, ang, L, W, veins=2):
    pts = G.bezier((0, 0), (L * 0.45, W), (L, 0.0), n=10) + G.bezier((L, 0.0), (L * 0.45, -W * 0.8), (0, 0), n=10)[1:-1]
    pts = [(base[0] + p[0], base[1] + p[1]) for p in rot(pts, ang)]
    G.stroke(d, pts, M["stem_fill"], 0.0, cyclic=True)
    lo = rot(G.bezier((L, 0.0), (L * 0.45, -W * 0.8), (0, 0), n=10), ang)
    G.stroke(d, [(base[0] + p[0], base[1] + p[1]) for p in lo] + [(base[0], base[1])], M["stem_sh"], 0.0, cyclic=True)
    mid = rot([(L * t, W * 0.15 * math.sin(math.pi * t)) for t in (0.05, 0.3, 0.6, 0.9)], ang)
    G.seam(d, [(base[0] + p[0], base[1] + p[1]) for p in mid], M["ink"])
    for k in range(veins):
        t = 0.3 + 0.5 * k / max(veins - 1, 1)
        v = rot([(L * t, 0.0), (L * (t + 0.12), W * 0.55)], ang)
        G.seam(d, [(base[0] + p[0], base[1] + p[1]) for p in v], M["ink"])
    G.stroke(d, pts, M["ink"], O, cyclic=True)


# ---------------------------------------------------------------- 1. Nodbell (plains / forest)

def nodbell(d, M, pose):
    """An arching stem with three sky-blue bells hanging from it; the bells swing behind the
    stem's sway (secondary motion) and nod together on react."""
    sway, nod = pose.get("sway", 0.0), pose.get("nod", 0.0)
    top = (0.30 + 0.25 * sway, 1.05)
    c = G.bezier((0, 0), (0.05 + 0.2 * sway, 0.75), top, n=14)
    hose_stem(d, M, c, 0.07, rib_every=0.14)
    leaf(d, M, (0.0, 0.16), math.radians(150), 0.34, 0.08)
    leaf(d, M, (0.0, 0.28), math.radians(25), 0.30, 0.07)
    arc = G.bezier(top, (top[0] + 0.25, top[1] + 0.12), (top[0] + 0.42, top[1] - 0.05), n=10)
    hose_stem(d, M, arc, 0.05, rib_every=0.2)
    for k, t in enumerate((0.25, 0.55, 0.9)):
        bx, bz = arc[int(t * (len(arc) - 1))]
        swing = math.radians(-14 * sway * (1 + 0.4 * k) + 18 * nod)
        bell = G.bezier((-0.07, 0.0), (-0.09, -0.12), (-0.11, -0.17), n=6) + \
            [(-0.07, -0.20), (-0.02, -0.17), (0.02, -0.20), (0.07, -0.17)] + \
            G.bezier((0.11, -0.17), (0.09, -0.12), (0.07, 0.0), n=6)
        bell = [(bx + p[0], bz - 0.03 + p[1]) for p in rot(bell, swing)]
        G.stroke(d, [(bx, bz), (bx, bz - 0.03)], M["ink"], I)
        G.stroke(d, bell, M["bell"], 0.0, cyclic=True)
        G.stroke(d, [q for q in bell if q[0] < bx - 0.02] + [(bx - 0.02, bz - 0.15)], M["bell_sh"], 0.0, cyclic=True)
        mouth = [(bx + p[0], bz - 0.03 + p[1]) for p in rot([(-0.08, -0.17), (0.0, -0.13), (0.08, -0.17), (0.0, -0.19)], swing)]
        G.stroke(d, mouth, M["bell_in"], 0.0, cyclic=True)
        G.seam(d, [(bx + p[0], bz - 0.03 + p[1]) for p in rot([(0.0, -0.02), (0.01, -0.12)], swing)], M["ink"])
        G.stroke(d, bell, M["ink"], O, cyclic=True)


# ---------------------------------------------------------------- 2. Shiverbarrel (desert)

def shiverbarrel(d, M, pose):
    """A squat ribbed barrel cactus with spine ticks along its ribs and a mustard crown flower;
    it shivers (fast small squash + jitter) and the flower pops open on react."""
    sh, open_ = pose.get("shiver", 0.0), pose.get("open", 0.6)
    sx, sz = 1 + 0.09 * sh, 1 - 0.08 * sh
    body = G.lumpy_ellipse(0.0, 0.30, 0.30 * sx, 0.30 * sz, n=40, lump=0.04, seed=3)
    body = [(x + 0.022 * sh * math.sin(z * 40), z) for x, z in body]
    body = [(x, max(z, 0.02)) for x, z in body]
    G.stroke(d, body, M["cactus_fill"], 0.0, cyclic=True)
    G.stroke(d, [q for q in body if q[0] < -0.10] + [(-0.10, 0.05)], M["cactus_sh"], 0.0, cyclic=True)
    G.stroke(d, [q for q in body if q[0] < -0.22] + [(-0.22, 0.10)], M["cactus_dp"], 0.0, cyclic=True)
    for k, xr in enumerate((-0.18, -0.06, 0.06, 0.18)):                 # ribs with spine ticks
        rib = [(xr * sx * (1 - 0.25 * ((z - 0.30) / 0.30) ** 2), z) for z in [0.06 + 0.48 * t / 8 for t in range(9)]]
        G.seam(d, rib, M["ink"])
        for x, z in rib[1:-1:2]:
            G.seam(d, [(x, z), (x + 0.035 * (1 if k % 2 else -1), z + 0.025)], M["ink"])
    G.stroke(d, body, M["ink"], O, cyclic=True)
    n = 7
    for k in range(n):                                                  # crown flower petals
        a = math.pi / 2 + (k - (n - 1) / 2) * (0.28 + 0.10 * open_)
        tip = (0.19 * math.cos(a) * (0.5 + 0.5 * open_), 0.58 + 0.16 * math.sin(a) * (0.6 + 0.4 * open_))
        pet = G.bezier((0.0, 0.58), (tip[0] * 0.6 - 0.02, (0.58 + tip[1]) / 2 + 0.02), tip, n=6) + \
            G.bezier(tip, (tip[0] * 0.6 + 0.02, (0.58 + tip[1]) / 2 - 0.01), (0.0, 0.58), n=6)[1:-1]
        G.stroke(d, pet, M["mustard"], O, cyclic=True)
    G.specks(d, [(-0.01, 0.6), (0.015, 0.61), (0.0, 0.625)], M["ink"])


# ---------------------------------------------------------------- 3. Curlfrond (forest / taiga)

def curlfrond(d, M, pose):
    """Three fern fronds whose tips are fiddlehead spirals that uncurl (curl 1 = tight, 0 = open);
    leaflets along each frond; the fronds curl up tight on react."""
    curl = pose.get("curl", 0.5)
    for k, (bx, lean) in enumerate(((-0.08, -0.5), (0.0, 0.05), (0.09, 0.55))):
        pts = [(bx, 0.0)]
        a, step = math.pi / 2 + lean * 0.6, 0.06
        L = 0.95 - 0.15 * abs(lean)
        n = int(L / step)
        for i in range(n):
            t = i / n
            a -= (0.04 + (2.6 * curl) * t ** 3) * (1 if lean >= 0 else -1) * (0.6 + 0.4 * (1 - curl))
            x, z = pts[-1]
            pts.append((x + step * math.cos(a), z + step * math.sin(a)))
        hose_stem(d, M, pts, 0.06, rib_every=1.0)
        for i in range(2, len(pts) - 3, 2):                             # leaflets
            (x0, z0), (x1, z1) = pts[i], pts[i + 1]
            ta = math.atan2(z1 - z0, x1 - x0)
            size = 0.17 * (1 - i / len(pts)) * (1 - 0.55 * curl * (i / len(pts)))
            for s in (-1, 1):
                L_, W_ = max(0.05, size), max(0.022, size * 0.38)
                lf = G.bezier((0, 0), (L_ * 0.45, W_), (L_, 0.0), n=8) + G.bezier((L_, 0.0), (L_ * 0.45, -W_ * 0.8), (0, 0), n=8)[1:-1]
                lf = [(x0 + q[0], z0 + q[1]) for q in rot(lf, ta + s * 1.1)]
                G.stroke(d, lf, M["blade"], I, cyclic=True)                  # ink-behind at interior weight
                mid_ = rot([(L_ * 0.1, 0.0), (L_ * 0.8, 0.0)], ta + s * 1.1)
                G.seam(d, [(x0 + q[0], z0 + q[1]) for q in mid_], M["ink"])
        G.hatch(d, pts[2][0] - 0.03, pts[2][1] + 0.03, M["ink"], n=2, length=0.04, spacing=0.018, angle_deg=70, seed=k)


# ---------------------------------------------------------------- 4. Whiptuft (plains / coast)

def whiptuft(d, M, pose):
    """A clump of long grass blades, three of them carrying mustard seed heads that whip with the
    wind and bounce back; blades flatten outward on react."""
    whip, flat = pose.get("whip", 0.0), pose.get("flat", 0.0)
    for k in range(9):
        base = -0.12 + 0.03 * k
        lean = (k - 4) * 0.10 * (1 + 1.2 * flat) + whip * 0.35
        L = 0.55 + 0.25 * math.sin(k * 1.7) ** 2
        tip = (base + L * math.sin(lean), L * math.cos(lean) * (1 - 0.3 * flat))
        mid = (base + 0.5 * L * math.sin(lean * 0.6), 0.55 * tip[1])
        blade = G.bezier((base - 0.026, 0.0), mid, tip, n=8) + G.bezier(tip, (mid[0] + 0.028, mid[1]), (base + 0.026, 0.0), n=8)[1:-1]
        G.stroke(d, blade, M["blade"] if k % 3 else M["blade_sh"], O, cyclic=True)   # ink-behind: thin blades keep their green
        if k in (2, 5, 7):                                              # seed heads whip further (follow-through)
            ha = lean + whip * 0.25
            hx, hz = tip
            head = G.lumpy_ellipse(hx + 0.06 * math.sin(ha), hz + 0.06 * math.cos(ha), 0.035, 0.08, n=16, lump=0.08, seed=k, rot=-ha)
            G.stroke(d, head, M["mustard"], O, cyclic=True)
            for j in range(3):
                G.seam(d, [(hx + 0.06 * math.sin(ha) - 0.025, hz + 0.04 + 0.03 * j), (hx + 0.06 * math.sin(ha) + 0.025, hz + 0.05 + 0.03 * j)], M["ink"])
    G.specks(d, [(-0.10, 0.02), (0.05, 0.03), (0.15, 0.015)], M["ink"])


# ---------------------------------------------------------------- 5. Thriftcushion (coast / tundra)

def thriftcushion(d, M, pose):
    """A low cushion of narrow leaves with five soft-red pom flowers on wiry stems; the poms bob
    out of phase on the beat and all rise together on react."""
    bob, rise = pose.get("bob", 0.0), pose.get("rise", 0.0)
    cushion = G.lumpy_ellipse(0.0, 0.07, 0.30, 0.10, n=36, lump=0.06, seed=11)
    cushion = [(x, max(z, 0.0)) for x, z in cushion]
    G.stroke(d, cushion, M["stem_fill"], 0.0, cyclic=True)
    G.stroke(d, [q for q in cushion if q[1] < 0.05], M["stem_dp"], 0.0, cyclic=True)
    for k in range(9):
        x = -0.24 + 0.06 * k
        G.seam(d, [(x, 0.03), (x + 0.02 * math.sin(k), 0.13 + 0.02 * math.cos(k))], M["ink"])
    G.stroke(d, cushion, M["ink"], O, cyclic=True)
    for k, (bx, h) in enumerate(((-0.18, 0.42), (-0.08, 0.55), (0.02, 0.48), (0.12, 0.58), (0.21, 0.40))):
        phase = math.sin(bob * 2 * math.pi + k * 1.3)
        hz = h + 0.03 * phase + 0.12 * rise
        hx = bx + 0.04 * math.sin(k * 2.1) + 0.02 * phase
        G.stroke(d, G.bezier((bx, 0.10), (bx + 0.03, (hz + 0.1) / 2), (hx, hz - 0.06), n=8), M["ink"], I)
        pom = G.lumpy_ellipse(hx, hz, 0.075, 0.07, n=24, lump=0.10, seed=20 + k)
        G.stroke(d, pom, M["red"], 0.0, cyclic=True)
        G.stroke(d, [q for q in pom if q[0] - hx + (q[1] - hz) < -0.04] + [(hx - 0.02, hz - 0.02)], M["red_sh"], 0.0, cyclic=True)
        G.specks(d, [(hx + 0.02, hz + 0.02), (hx - 0.01, hz + 0.035), (hx + 0.03, hz - 0.01), (hx - 0.03, hz)], M["ink"])
        G.stroke(d, pom, M["ink"], O, cyclic=True)


PLANTS = [
    ("nodbell", nodbell, [dict(sway=0.0), dict(sway=0.8), dict(sway=-0.8), dict(sway=0.2, nod=1.0)],
     ["rest", "sway right", "sway left (bells trail)", "react: bells nod"],
     "plains / forest: sky-blue bells that swing behind the stem and nod when you pass"),
    ("shiverbarrel", shiverbarrel, [dict(shiver=0.0, open=0.5), dict(shiver=1.0, open=0.5), dict(shiver=-1.0, open=0.5), dict(shiver=0.6, open=1.0)],
     ["rest", "shiver +", "shiver -", "react: crown pops open"],
     "desert: a ribbed barrel cactus that shivers, spines ticking, crown flower popping open"),
    ("curlfrond", curlfrond, [dict(curl=0.15), dict(curl=0.55), dict(curl=0.9), dict(curl=1.0)],
     ["open", "half curled", "curled", "react: curled tight"],
     "forest / taiga: fiddlehead fronds that slowly uncurl and curl back on the beat"),
    ("whiptuft", whiptuft, [dict(whip=0.0), dict(whip=1.0), dict(whip=-0.6), dict(whip=0.3, flat=1.0)],
     ["rest", "whip right (heads follow through)", "spring back", "react: flattens outward"],
     "plains / coast: grass whose seed heads whip and bounce on the wind"),
    ("thriftcushion", thriftcushion, [dict(bob=0.0), dict(bob=0.25), dict(bob=0.5), dict(bob=0.1, rise=1.0)],
     ["bob 0", "bob 1/4", "bob 1/2", "react: poms rise together"],
     "coast / tundra: soft-red poms on wiry stems bobbing out of phase over a leafy cushion"),
]


def main(out):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import v3
    fw, fh = 160, 112
    rows = []
    W = 16 + 4 * (fw * 2 + 12) + 260
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "c2 earth plants: five faceless designs for lead (d-101); v3.1 ink; rendered lock-free (meridian.fakegp); 1x row + 2x poses", 6, 8)
    rows.append(head)
    allw = []
    for name, fn, poses, labels, ours in PLANTS:
        gp = fakegp.FakeGP()
        M = mats(gp)
        frames = []
        for pose in poses:
            d = fakegp.FakeDrawing()
            fn(d, M, pose)
            img, w = fakegp.render(d, gp, fw, fh, pivot=(0.5, 0.0), ss=4, seed=3)
            frames.append(img)
            allw += w
        row = np.tile(np.array([0.62, 0.72, 0.66], np.float32), (fh * 2 + 46, W, 1))   # a pale meadow wash
        review._label(row, f"{name}: {ours}"[:150], 6, 4)
        for j, (im, lab) in enumerate(zip(frames, labels)):
            x = 8 + j * (fw * 2 + 12)
            review._over(row, np.repeat(np.repeat(im, 2, 0), 2, 1), x, 22)
            review._label(row, lab[:38], x, 22 + fh * 2 + 4, scale=1)
        review._over(row, frames[0], W - 240, 22 + fh)          # the rest pose at 1x
        review._label(row, "1x", W - 240, 22 + fh - 14)
        rows.append(row)
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    foot = np.tile(review.PAPER, (60, W, 1)).astype(np.float32)
    review._label(foot, f"measured ink: outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior "
                        f"{min(w[1] for w in inner):.1f}-{max(w[2] for w in inner):.1f} px; no eyes or mouths on any plant (d-101); "
                        "each is a (d, m, pose) function ready to become a rig set", 6, 8)
    review._label(foot, "lead: pick, cut or redirect; c2 then turns the picks into flora/earth/rigset parts + swaps (head/leaf states) like snoozle v2", 6, 30)
    rows.append(foot)
    review.write(out, np.vstack(rows))
    print("written", out)


if __name__ == "__main__":
    main(sys.argv[1])
