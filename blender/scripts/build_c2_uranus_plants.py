"""B-158 (C2 Uranus design prep): five faceless Uranus flora as (d, M, pose) drawing functions in the C2 manner
(build_c2_earth_plants' hose stems and leaves), in the Uranus palette (D-142). No faces (D-101): personality through motion
only. At 0.89 g and in the dim sideways light they are tall and thin, with pale tips that catch what light there is; the
ember amber (the palette's one warm accent) appears only in the Embermoss's heart. Part functions so the rig set can cut
them later. Drawn 1.6x.

  sunturner  a tall frost-mint stalk whose cupped ice-white head faces the low sun (turn -1 left .. 1 right); react: folds shut
  fogbell    an arching frost-mint stalk hung with three methane-cyan bells dripping condensed fog; react: they close
  hailcatch  a low basin plant with a cupped ice-white bowl collecting hail pebbles (0-4); react: the bowl tips and spills
  embermoss  a dark-half cushion with an ember glow at its heart (a tone) that breathes; react: it dims and curls
  prismfern  a stiff fern of faceted ice-white fronds where the diamond rain falls; they glint; react: they clatter flat

  python -I build_c2_uranus_plants.py <preview dir>      lock-free (meridian.fakegp)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_earth_plants as C  # noqa: E402  (the real gp_draw in Blender, the fake outside)
from meridian import v3  # noqa: E402

G = C.G
P = v3.PALETTES["uranus"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
hose_stem, leaf, rot = C.hose_stem, C.leaf, C.rot
SCALE = 1.6
FW, FH = 160, 192


def SH(h):
    return v3.shadow_of(h, "uranus")


def DP(h):
    return v3.deep_of(h, "uranus")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, "uranus_" + name, **kw)
    out = {"ink": m("ink", fill=None)}
    for key, slot in (("mint", "green"), ("ember", "red"), ("sage", "mustard"), ("cyan", "teal"), ("ice", "offwhite"),
                      ("fog", "sky"), ("slate", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
    out["stem_fill"], out["stem_sh"] = out["mint_f"], out["mint_sh"]
    return out


def xf(d, sx=1.0, sz=1.0, dx=0.0, dz=0.0):
    return G.Xf(d, lambda pts: [(x * sx + dx, z * sz + dz) for x, z in pts])


# ---------------------------------------------------------------- sunturner (the lit decks)
def sunturner_stalk(d, M):
    hose_stem(d, M, G.bezier((0.0, 0.0), (0.03, 0.30), (0.0, 0.62), n=9), 0.045, rib_every=0.15)
    leaf(d, M, (0.0, 0.16), math.radians(155), 0.15, 0.04, veins=1)
    leaf(d, M, (0.01, 0.30), math.radians(30), 0.13, 0.035, veins=1)


def sunturner_head(d, M, turn=0.0, shut=0.0):
    """The cupped head above (0, 0), its opening facing the sun: turn -1 (left) .. 0 (up) .. 1 (right); shut 0..1."""
    a = math.radians(90 - 60 * turn)
    c, s_ = math.cos(a), math.sin(a)
    w = 0.12 * (1 - 0.6 * shut)

    def at(u, v):                                                                          # u along the facing, v across
        return (c * u - s_ * v, 0.04 + s_ * u + c * v)
    cup = [at(0.0, -0.03), at(0.06, -w), at(0.16, -w * 0.9), at(0.16, w * 0.9), at(0.06, w), at(0.0, 0.03)]
    G.stroke(d, cup, M["ice_f"], 0.0, cyclic=True)
    G.stroke(d, [at(0.16, -w * 0.9), at(0.16, w * 0.9), at(0.13, w * 0.7), at(0.13, -w * 0.7)], M["fog_sh"], 0.0, cyclic=True)   # the inside
    G.seam(d, [at(0.02, 0.0), at(0.14, 0.0)], M["ink"])
    G.stroke(d, cup, M["ink"], O, cyclic=True)


def sunturner(d, M, p):
    s = xf(d, 1.0, p.get("squash", 1.0))
    sunturner_stalk(s, M)
    sunturner_head(xf(s, 1.0, 1.0, 0.0, 0.62), M, p.get("turn", 0.0), p.get("shut", 0.0))


# ---------------------------------------------------------------- fogbell (decks 1-2)
FB_ARCH = G.bezier((0.0, 0.0), (-0.02, 0.62), (0.36, 0.80), (0.46, 0.48), n=24)
FB_T = (0.45, 0.7, 0.92)


def fogbell_stalk(d, M):
    hose_stem(d, M, FB_ARCH, 0.04, rib_every=0.15)
    leaf(d, M, (0.0, 0.14), math.radians(150), 0.15, 0.04, veins=1)


def fogbell_bell(d, M, shut=0.0, drip=0.0):
    """One bell hanging from (0, 0): methane cyan, an ice-white lip, a fog drip below it (drip 0..1 falls)."""
    w = 0.06 * (1 - 0.45 * shut)
    bell = [(-0.01, 0.0), (0.01, 0.0)] + G.bezier((0.01, 0.0), (w, -0.04), (w * 1.1, -0.12), n=6)[1:] + \
        [(w * 0.4, -0.13), (-w * 0.4, -0.13)] + G.bezier((-w * 1.1, -0.12), (-w, -0.04), (-0.01, 0.0), n=6)
    G.stroke(d, bell, M["cyan_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in bell if q[0] > 0.01] + [(0.01, -0.06)], M["cyan_sh"], 0.0, cyclic=True)
    G.stroke(d, [(w * 1.1, -0.12), (w * 0.4, -0.13), (-w * 0.4, -0.13), (-w * 1.1, -0.12), (-w, -0.105), (w, -0.105)], M["ice_f"], 0.0, cyclic=True)
    G.stroke(d, bell, M["ink"], O, cyclic=True)
    if shut < 0.5:
        G.stroke(d, G.lumpy_ellipse(0.0, -0.16 - 0.08 * drip, 0.012, 0.016, n=8, seed=5), M["ice"], I, cyclic=True)


def fogbell(d, M, p):
    s = xf(d, 1.0, p.get("squash", 1.0))
    fogbell_stalk(s, M)
    for k, t in enumerate(FB_T):
        q = FB_ARCH[int(t * (len(FB_ARCH) - 1))]
        a = 0.3 * math.sin(p.get("phase", 0.0) - 1.1 * k) * (1 - p.get("react", 0.0))
        G.stroke(s, [q, (q[0], q[1] - 0.04)], M["ink"], I)
        fogbell_bell(G.Xf(s, lambda pts, q=q, a=a: [(q[0] + x * math.cos(a) - z * math.sin(a), q[1] - 0.04 + x * math.sin(a) + z * math.cos(a))
                                                     for x, z in pts]), M, p.get("react", 0.0), (p.get("phase", 0.0) / TAU + 0.3 * k) % 1.0)


# ---------------------------------------------------------------- hailcatch (deck 2)
def hailcatch_base(d, M):
    for k in (-1, 1):
        leaf(d, M, (0.0, 0.03), math.radians(90 + 70 * k), 0.17, 0.05, veins=1)
    hose_stem(d, M, [(0.0, 0.0), (0.01, 0.12), (0.0, 0.22)], 0.05, rib_every=0.2)


def hailcatch_bowl(d, M, hail=2, tip=0.0):
    """The bowl above (0, 0): ice white, the hail pebbles inside (0-4); tip 0..1 tilts it and spills them."""
    a = math.radians(-70 * tip)
    R = G.Xf(d, lambda pts: [(x * math.cos(a) - z * math.sin(a), x * math.sin(a) + z * math.cos(a)) for x, z in pts])
    bowl = G.bezier((-0.18, 0.12), (-0.15, -0.02), (0.0, -0.01), n=8) + G.bezier((0.0, -0.01), (0.15, -0.02), (0.18, 0.12), n=8)[1:] + \
        [(0.14, 0.12), (0.0, 0.03), (-0.14, 0.12)]
    G.stroke(R, bowl, M["ice_f"], 0.0, cyclic=True)
    G.stroke(R, [(0.0, 0.03), (0.14, 0.12), (0.18, 0.12), (0.15, -0.02), (0.0, -0.01)], M["fog_sh"], 0.0, cyclic=True)
    G.stroke(R, bowl, M["ink"], O, cyclic=True)
    for k in range(int(hail * (1 - tip))):
        G.stroke(R, G.lumpy_ellipse(-0.08 + 0.055 * k, 0.07 + 0.01 * (k % 2), 0.024, 0.02, n=8, lump=0.1, seed=11 + k), M["ice"], I, cyclic=True)
    if tip > 0.3:                                                                          # the spill
        for k in range(3):
            G.stroke(d, G.lumpy_ellipse(0.22 + 0.06 * k, -0.05 - 0.06 * k * tip, 0.02, 0.018, n=8, seed=21 + k), M["ice"], I, cyclic=True)


def hailcatch(d, M, p):
    s = xf(d, 1.0, p.get("squash", 1.0))
    hailcatch_base(s, M)
    hailcatch_bowl(xf(s, 1.0, 1.0, 0.0, 0.22), M, p.get("hail", 2), p.get("tip", 0.0))


# ---------------------------------------------------------------- embermoss (the dark half)
def embermoss(d, M, p):
    curl = p.get("curl", 0.0)
    s = xf(d, 1.0 + 0.1 * curl, (1.0 - 0.3 * curl) * p.get("squash", 1.0))
    dome = [(x, max(z, 0.0)) for x, z in G.lumpy_ellipse(0.0, 0.03, 0.26, 0.17, n=30, lump=0.08, seed=31)]
    G.stroke(s, dome, M["cyan_dp"], 0.0, cyclic=True)
    G.stroke(s, [q for q in dome if q[0] > 0.08] + [(0.08, 0.03)], M["slate_f"], 0.0, cyclic=True)
    glow = p.get("glow", 1.0) * (1 - 0.7 * curl)
    G.stroke(s, G.lumpy_ellipse(-0.02, 0.07, 0.07 + 0.05 * glow, 0.05 + 0.03 * glow, n=16, lump=0.1, seed=32), M["ember_sh"], 0.0, cyclic=True)   # the glow (a tone)
    G.stroke(s, G.lumpy_ellipse(-0.02, 0.08, 0.035 + 0.02 * glow, 0.025 + 0.012 * glow, n=12, seed=33), M["ember_f"], 0.0, cyclic=True)
    for k in range(7):                                                                     # moss tufts along the top
        a = math.pi * (0.1 + 0.8 * k / 6)
        x, z = 0.24 * math.cos(a), 0.03 + 0.16 * math.sin(a)
        G.stroke(s, [(x, z), (x * 1.08, z + 0.05), (x * 1.02 + 0.015, z + 0.01)], M["mint"], I, cyclic=True)
    G.stroke(s, dome, M["ink"], O, cyclic=True)


# ---------------------------------------------------------------- prismfern (deck 3, the deep: the diamond rain)
def prismfern_stem(d, M):
    hose_stem(d, M, G.bezier((0.0, 0.0), (0.02, 0.28), (0.0, 0.56), n=9), 0.04, rib_every=0.14)


def prismfern_frond(d, M, z, side, L, flat=0.0, glint=False):
    """A faceted ice-white frond off the stem at height z, to one side; flat 0..1 lays it down."""
    a = math.radians(90 - side * (55 + 30 * flat))
    c, s_ = math.cos(a), math.sin(a)

    def at(u, v):
        return (c * u * L - s_ * v * 0.04, z + s_ * u * L + c * v * 0.04)
    sh = [at(0, -0.6), at(0.6, -1.0), at(1.0, 0.0), at(0.6, 1.0), at(0, 0.6)]
    G.stroke(d, sh, M["ice_f"], 0.0, cyclic=True)
    G.stroke(d, [at(0, 0.0), at(1.0, 0.0), at(0.6, -1.0), at(0, -0.6)], M["fog_sh"], 0.0, cyclic=True)
    G.stroke(d, sh, M["ink"], I, cyclic=True)
    if glint:
        tx, tz = at(1.0, 0.0)
        for ang in (0.0, math.pi / 2):
            G.stroke(d, [(tx - 0.03 * math.cos(ang), tz - 0.03 * math.sin(ang)), (tx + 0.03 * math.cos(ang), tz + 0.03 * math.sin(ang))], M["ice"], I)


FRONDS = ((0.14, 1, 0.20), (0.22, -1, 0.22), (0.30, 1, 0.21), (0.38, -1, 0.19), (0.46, 1, 0.16), (0.53, -1, 0.12))


def prismfern(d, M, p):
    s = xf(d, 1.0, p.get("squash", 1.0))
    prismfern_stem(s, M)
    for k, (z, side, L) in enumerate(FRONDS):
        prismfern_frond(s, M, z, side, L, p.get("flat", 0.0), glint=(k == p.get("glint", -1)))


PLANTS = {"sunturner": sunturner, "fogbell": fogbell, "hailcatch": hailcatch, "embermoss": embermoss, "prismfern": prismfern}


def poses(name):
    ph = [TAU * i / 8 for i in range(8)]
    idle = {"sunturner": [dict(turn=math.sin(a), squash=1 + 0.02 * math.cos(a)) for a in ph],
            "fogbell": [dict(phase=a) for a in ph],
            "hailcatch": [dict(hail=(i // 2) % 5, squash=1 + 0.02 * math.cos(a)) for i, a in enumerate(ph)],
            "embermoss": [dict(glow=0.6 + 0.4 * math.sin(a), squash=1 + 0.02 * math.cos(a)) for a in ph],
            "prismfern": [dict(glint=i % 6 if i % 2 == 0 else -1, squash=1 + 0.02 * math.cos(a)) for i, a in enumerate(ph)]}[name]
    react = {"sunturner": [dict(shut=0.5), dict(shut=1.0), dict(shut=1.0, squash=0.95), dict(shut=0.3)],
             "fogbell": [dict(react=0.5, phase=0.5), dict(react=1.0), dict(react=1.0), dict(react=0.3, phase=1.0)],
             "hailcatch": [dict(hail=4, tip=0.3), dict(hail=4, tip=0.8), dict(hail=4, tip=1.0), dict(hail=0, tip=0.2)],
             "embermoss": [dict(curl=0.4, glow=0.6), dict(curl=1.0, glow=0.3), dict(curl=1.0, glow=0.2), dict(curl=0.4, glow=0.5)],
             "prismfern": [dict(flat=0.4), dict(flat=1.0), dict(flat=1.0, squash=0.95), dict(flat=0.3)]}[name]
    return idle, react


def render(name, pose, scale=1, seed=7):
    from meridian import fakegp
    import gp_raster as GR
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    PLANTS[name](G.Xf(d, lambda pts: [(x * SCALE, z * SCALE) for x, z in pts]), M, pose)
    return GR.render_frame(fakegp.strokes_of(d, gp), FW * scale, FH * scale, 64 * scale, (0.5, 0.0), ss=2, seed=seed)


def uranus_strip(W, H):
    """A Uranus stand-in: the cyan fog (dim, barely banded), the low ember sun's rim glow at the left edge, a floe band."""
    import numpy as np
    rgb = lambda h: np.array(v3.hex_rgb(h), np.float32) / 255   # noqa: E731
    bg = np.empty((H, W, 3), np.float32)
    t = (np.arange(H) / H)[:, None, None]
    bg[:] = rgb(P["sky"]) * (1 - 0.25 * t) + rgb(P["teal"]) * 0.25 * t
    x = np.arange(W)[None, :, None]
    bg[:] = bg * (1 - 0.18 * np.exp(-x / 160.0)) + rgb(P["red"]) * 0.18 * np.exp(-x / 160.0)   # the low sun, sideways
    g = H - 40
    bg[g:g + 14] = rgb(P["offwhite"])
    bg[g:g + 3] = rgb(v3.INK)
    bg[g + 14:] = rgb(P["teal"])
    rng = np.random.default_rng(3)
    bg *= (1 + 0.02 * rng.standard_normal((H, W, 1))).astype(np.float32)
    return bg, g


def preview(out_dir):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    W = 1960
    rows = []
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, "b-158 uranus flora designs (faceless, d-101; the uranus palette d-142): sunturner, fogbell, hailcatch, embermoss (dark half), prismfern", 6, 8)
    rows.append(head)
    widths, sheets = [], []
    scene, ground = uranus_strip(W, 300)
    x = 30
    for name in PLANTS:
        img, w = render(name, poses(name)[0][0])
        widths += w
        sheets.append(img)
        review._over(scene, img, x, ground - FH + 8)
        review._label(scene, name, x + 10, ground + 18, scale=1)
        x += FW + 40
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, x + 20, ground - fr.shape[0] + int(round(piv[1] * fr.shape[0])) + 8)
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, "1x on a uranus stand-in (the cyan fog, the low ember sun sideways, a floe band) beside the surveyor (2 m)", 6, 6)
    rows.append(scene)
    for name in PLANTS:
        idle, react = poses(name)
        r = np.tile(review.PAPER, (FH * 2 + 30, W, 1)).astype(np.float32)
        review._label(r, f"{name}: idle 8 (on the beat) | react 4  at 2x", 6, 4)
        for j, pz in enumerate(idle + react):
            img, w = render(name, pz, scale=2, seed=11 + j)
            widths += [(a / 2, b / 2, c / 2) for a, b, c in w]
            xx = 8 + j * (FW * 2 - 100) + (24 if j >= 8 else 0)
            if xx + FW * 2 > W:
                break
            review._over(r, img, xx, 24)
        rows.append(r)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    per = [v3.palette_hits(s_, "uranus") for s_ in sheets]
    hits, off = min(h for h, _o in per), [c for _h, o in per for c in o]
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; uranus palette hits >= {hits * 100:.1f}% per plant {off[:3]}; faces: none", 6, 8)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " preview (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b158_uranus_plants_preview.png")
    review.write(out, img)
    print("written", out, f"ink {min(w[1] for w in outer):.2f}-{max(w[2] for w in outer):.2f} / {min(w[1] for w in inner):.2f}-{max(w[2] for w in inner):.2f}",
          f"palette {hits * 100:.1f}% {off[:3]}")


if __name__ == "__main__":
    preview(sys.argv[1])
