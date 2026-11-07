"""B-161 (C2 Neptune design prep): five faceless Neptune flora as (d, M, pose) drawing functions in the C2 manner
(build_c2_earth_plants' hose stems and leaves), in the Neptune palette (D-148). No faces (D-101): personality through motion
only. At 1.14 g and in a gale they are low, anchored and streamlined, or they fly on tethers. Each is drawn UPRIGHT (D-148):
the wind is a lean of the root bone that UNITY sets from the local wind, mirrored for a -x wind; the idles below are each
plant's own motion on the 110 bpm beat. Beacon coral (the palette's one warm accent) never appears on a plant. Part
functions so the rig set can cut them later. Drawn 1.6x.

  kitebloom     a wind-cyan kite leaf with wisp-white ribs on a long tether from a clenched root knot; it bobs and loops;
                react: it reels in and folds flat against the root
  gripweed      a low tangle of abyss-sage tendrils hooked over the floe edge; the tips flutter; react: they clench and curl in
  pipereed      hollow wind-cyan reeds with wisp-white mouths cut like organ pipes; a travelling bow; react: they duck in a row
  stormlantern  a storm-violet bulb on a short curled stem, a faint glow (a tone) breathing with the storm's 8-beat clock;
                react: it dims and draws its stem in
  rimecomb      a stiff fan of wisp-white ice combs on Superionic floes, storm-violet tips; rime flakes tick off on the beat;
                react: the combs snap shut like a folding fan

  python -I build_c2_neptune_plants.py <preview dir>      lock-free (meridian.fakegp)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_earth_plants as C  # noqa: E402  (the real gp_draw in Blender, the fake outside)
from meridian import v3  # noqa: E402

G = C.G
P = v3.PALETTES["neptune"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
hose_stem, leaf, rot = C.hose_stem, C.leaf, C.rot
SCALE = 1.6
FW, FH = 160, 192


def SH(h):
    return v3.shadow_of(h, "neptune")


def DP(h):
    return v3.deep_of(h, "neptune")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, "neptune_" + name, **kw)
    out = {"ink": m("ink", fill=None)}
    for key, slot in (("sage", "green"), ("coral", "red"), ("violet", "mustard"), ("cyan", "teal"), ("wisp", "offwhite"),
                      ("blue", "sky"), ("indigo", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
        out[key + "_ln"] = m(key + "_line", fill=None, ink_hex=h)              # a line drawn in the colour itself
    out["stem_fill"], out["stem_sh"] = out["sage_f"], out["sage_sh"]
    return out


def with_stem(M, key):
    """M with the hose / leaf fill switched to another colour (the reeds are wind cyan, not sage)."""
    out = dict(M)
    out["stem_fill"], out["stem_sh"] = M[key + "_f"], M[key + "_sh"]
    return out


def xf(d, sx=1.0, sz=1.0, dx=0.0, dz=0.0):
    return G.Xf(d, lambda pts: [(x * sx + dx, z * sz + dz) for x, z in pts])


def rotated(d, a, cx=0.0, cz=0.0):
    return G.Xf(d, lambda pts: rot(pts, a, cx, cz))


# ---------------------------------------------------------------- kitebloom (decks 1-2)
def kitebloom_root(d, M):
    knot = [(x, max(z, 0.0)) for x, z in G.lumpy_ellipse(0.0, 0.03, 0.09, 0.07, n=20, lump=0.12, seed=41)]
    G.stroke(d, knot, M["sage_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in knot if q[0] > 0.02] + [(0.02, 0.03)], M["sage_dp"], 0.0, cyclic=True)
    for k in (-1, 1):                                                                       # two gripping root toes
        G.stroke(d, G.bezier((0.05 * k, 0.01), (0.10 * k, 0.02), (0.13 * k, -0.005), n=6), M["ink"], I)
    G.seam(d, [(-0.04, 0.05), (0.0, 0.07), (0.04, 0.05)], M["ink"])
    G.stroke(d, knot, M["ink"], O, cyclic=True)


def kitebloom_kite(d, M, fold=0.0):
    """The kite leaf centred on (0, 0), nose up: a wind-cyan diamond with wisp-white ribs; fold 0..1 narrows it shut."""
    w = 0.13 * (1 - 0.8 * fold)
    kite = [(0.0, 0.17), (w, 0.03), (0.0, -0.14), (-w, 0.03)]
    kite = [p for a, b in zip(kite, kite[1:] + kite[:1]) for p in G.bowed_line(a, b, bow=0.02, n=5)[:-1]]
    G.stroke(d, kite, M["cyan_f"], 0.0, cyclic=True)
    G.stroke(d, [(0.0, 0.17), (w, 0.03), (0.0, -0.14), (0.0, 0.03)], M["cyan_sh"], 0.0, cyclic=True)
    G.stroke(d, [(0.0, 0.15), (0.0, -0.12)], M["wisp_ln"], I)                              # the ribs
    G.stroke(d, [(-w * 0.85, 0.03), (w * 0.85, 0.03)], M["wisp_ln"], I)
    G.stroke(d, kite, M["ink"], O, cyclic=True)


def kitebloom(d, M, p):
    reel = p.get("reel", 0.0)
    s = xf(d, 1.0, p.get("squash", 1.0))
    a = p.get("phase", 0.0)
    kx = (0.34 + 0.05 * math.cos(a)) * (1 - reel) + 0.08 * reel                            # the kite flies downwind (+x)
    kz = (0.78 + 0.07 * math.sin(a)) * (1 - reel) + 0.16 * reel
    tether = G.bezier((0.0, 0.08), (0.02, 0.4 * (1 - reel) + 0.1 * reel), (kx - 0.12, kz - 0.05), (kx, kz - 0.12), n=14)
    G.stroke(s, tether, M["ink"], I)
    for k in range(2):                                                                      # tail ribbons
        tx, tz = kx - 0.02 * k, kz - 0.14
        G.stroke(s, G.bezier((tx, tz), (tx - 0.05, tz - 0.06), (tx + 0.02 - 0.03 * math.sin(a + k), tz - 0.13), n=8), M["ink"], I)
    kitebloom_root(s, M)
    tilt = 0.35 * (1 - reel) + 0.15 * math.sin(a) * (1 - reel) - 1.2 * reel
    kitebloom_kite(G.Xf(s, lambda pts: [(kx + q[0], kz + q[1]) for q in rot(pts, -tilt)]), M, reel)


# ---------------------------------------------------------------- gripweed (every deck)
GRIP = ((-0.22, 0.15, 0.18), (-0.07, 0.23, 0.22), (0.08, 0.20, 0.24), (0.21, 0.12, 0.19))


def gripweed(d, M, p):
    clench, flut = p.get("clench", 0.0), p.get("flutter", 0.0)
    s = xf(d, 1.0, p.get("squash", 1.0))
    mound = [(x, max(z, 0.0)) for x, z in G.lumpy_ellipse(0.02, 0.0, 0.24, 0.09, n=26, lump=0.1, seed=51)]
    G.stroke(s, mound, M["sage_sh"], 0.0, cyclic=True)
    for k, (bx, h, L) in enumerate(GRIP):
        reach = L * (1 - 0.45 * clench)
        tip = (bx + reach * 0.9 + 0.035 * math.sin(flut + 1.3 * k) * (1 - clench), h + 0.06 + 0.02 * math.cos(flut + k))
        stem = G.bezier((bx * 0.5, 0.03), (bx, h + 0.05), (tip[0] - 0.05, tip[1] + 0.02), tip, n=10)
        hose_stem(s, M, stem, 0.036, rib_every=0.3)
        r = 0.045 * (1 + 0.5 * clench)                                                     # the hooked tip curls further in when it clenches
        hook = [(tip[0] + r * math.sin(t), tip[1] - r + r * math.cos(t)) for t in [math.pi * (0.0 + 1.3 * j / 7) * (1 + 0.4 * clench) for j in range(8)]]
        G.stroke(s, hook, M["ink"], I)
    for k in range(4):                                                                      # little tendril leaves on the mound
        leaf(s, M, (-0.16 + 0.11 * k, 0.05), math.radians(70 + 15 * (k % 2) - 10 * k), 0.07, 0.022, veins=0)
    G.specks(s, [(-0.1, 0.04), (0.06, 0.05), (0.18, 0.03)], M["ink"])
    G.stroke(s, mound, M["ink"], O, cyclic=True)


# ---------------------------------------------------------------- pipereed (decks 2-3)
REEDS = ((-0.17, 0.42, 0.040), (-0.06, 0.66, 0.048), (0.06, 0.54, 0.044), (0.16, 0.34, 0.036))


def pipereed_reed(d, M, h, w):
    """One reed from (0, 0) to its angled mouth at height h: a wind-cyan tube, a wisp-white rim, the dark inside."""
    Mc = with_stem(M, "cyan")
    hose_stem(d, Mc, [(0.0, 0.0), (0.004, h * 0.5), (0.0, h)], w, rib_every=0.12)
    mouth = G.lumpy_ellipse(0.0, h + 0.012, w * 1.15, w * 0.45, n=14, lump=0.05, seed=int(h * 100), rot=math.radians(-18))
    G.stroke(d, mouth, M["wisp_f"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, h + 0.012, w * 0.75, w * 0.25, n=12, lump=0.04, seed=int(h * 100) + 1, rot=math.radians(-18)),
             M["indigo_f"], 0.0, cyclic=True)
    G.stroke(d, mouth, M["ink"], I, cyclic=True)


def pipereed(d, M, p):
    s = xf(d, 1.0, p.get("squash", 1.0))
    duck = p.get("duck", 0.0)
    base = [(x, max(z, 0.0)) for x, z in G.lumpy_ellipse(0.0, 0.0, 0.25, 0.05, n=20, lump=0.08, seed=61)]
    G.stroke(s, base, M["sage_f"], 0.0, cyclic=True)
    for k, (bx, h, w) in enumerate(REEDS):
        a = -(0.12 * math.sin(p.get("phase", 0.0) - 0.9 * k)) * (1 - duck) - math.radians(72) * min(1.0, max(0.0, duck * 1.6 - 0.2 * k))
        pipereed_reed(G.Xf(s, lambda pts, bx=bx, a=a: [(bx + q[0], q[1]) for q in rot(pts, a)]), M, h, w)
    for k in (-1, 1):
        leaf(s, M, (0.2 * k, 0.03), math.radians(90 - 60 * k), 0.12, 0.03, veins=1)
    G.stroke(s, base, M["ink"], O, cyclic=True)


# ---------------------------------------------------------------- stormlantern (the storm, deck 3)
def stormlantern(d, M, p):
    draw_in, glow = p.get("draw_in", 0.0), p.get("glow", 1.0)
    s = xf(d, 1.0, p.get("squash", 1.0))
    h = 0.36 * (1 - 0.4 * draw_in)
    stem = G.bezier((0.0, 0.0), (-0.10, h * 0.45), (0.08, h * 0.7), (0.0, h), n=12)
    hose_stem(s, M, stem, 0.042, rib_every=0.12)
    leaf(s, M, (0.0, 0.05), math.radians(160), 0.13, 0.035, veins=1)
    leaf(s, M, (0.0, 0.05), math.radians(25), 0.11, 0.03, veins=1)
    g = glow * (1 - 0.7 * draw_in)
    bz = h + 0.1
    halo = G.lumpy_ellipse(0.0, bz, 0.10 + 0.05 * g, 0.12 + 0.05 * g, n=20, lump=0.06, seed=71)
    G.stroke(s, halo, M["violet_sh"], 0.0, cyclic=True)                                      # the glow (a tone)
    bulb = G.lumpy_ellipse(0.0, bz, 0.09, 0.11, n=22, lump=0.05, seed=72)
    G.stroke(s, bulb, M["violet_f"], 0.0, cyclic=True)
    G.stroke(s, [q for q in bulb if q[0] > 0.02] + [(0.02, bz)], M["violet_sh"], 0.0, cyclic=True)
    G.stroke(s, G.lumpy_ellipse(-0.015, bz + 0.01, 0.02 + 0.025 * g, 0.03 + 0.03 * g, n=12, seed=73), M["wisp_f"], 0.0, cyclic=True)
    for k in (-1, 1):                                                                       # the bulb's two seams
        G.seam(s, G.bezier((0.04 * k, bz + 0.1), (0.07 * k, bz), (0.04 * k, bz - 0.1), n=8), M["ink"])
    hood = [(-0.07, bz + 0.08), (0.0, bz + 0.15), (0.07, bz + 0.08), (0.0, bz + 0.11)]       # a sage leaf hood
    G.stroke(s, hood, M["sage_f"], 0.0, cyclic=True)
    G.stroke(s, hood, M["ink"], I, cyclic=True)
    G.stroke(s, bulb, M["ink"], O, cyclic=True)


# ---------------------------------------------------------------- rimecomb (the deep, on Superionic floes)
COMBS = (-0.62, -0.31, 0.0, 0.31, 0.62)        # blade angles from upright (rad)


def rimecomb_blade(d, M, L):
    """One comb blade from (0, 0) up to L: a wisp-white strip with teeth on its right edge and a storm-violet tip."""
    w0, w1 = 0.035, 0.05
    left = [(-w0, 0.0), (-w1, L)]
    teeth = [(w1, L)] + [p for j in range(5) for p in ((w1 - 0.002 * j + 0.025, L * (0.85 - 0.16 * j)), (w1 - 0.004 * j, L * (0.78 - 0.16 * j)))] + [(w0, 0.0)]
    blade = left + teeth
    G.stroke(d, blade, M["wisp_f"], 0.0, cyclic=True)
    G.stroke(d, [(0.0, 0.0), (0.0, L), (w1, L), (w0, 0.0)], M["blue_sh"], 0.0, cyclic=True)
    tip = [(-w1, L), (0.0, L + 0.05), (w1, L)]
    G.stroke(d, tip + [(w1, L - 0.04), (-w1, L - 0.04)], M["violet_f"], 0.0, cyclic=True)
    G.stroke(d, blade + [(w1, L), (0.0, L + 0.05)], M["ink"], I, cyclic=True)


def rimecomb(d, M, p):
    shut = p.get("shut", 0.0)
    s = xf(d, 1.0, p.get("squash", 1.0))
    for k, a in enumerate(COMBS):
        L = 0.42 - 0.08 * abs(k - 2)
        rimecomb_blade(G.Xf(s, lambda pts, a=a: rot(pts, a * (1 - shut))), M, L)
    base = [(x, max(z, 0.0)) for x, z in G.lumpy_ellipse(0.0, 0.0, 0.10, 0.07, n=18, lump=0.08, seed=81)]
    G.stroke(s, base, M["indigo_f"], 0.0, cyclic=True)
    G.stroke(s, [(-0.05, 0.03), (0.0, 0.05), (0.05, 0.03)], M["violet_ln"], I)
    G.stroke(s, base, M["ink"], O, cyclic=True)
    flake = p.get("flake", -1)
    if flake >= 0:                                                                          # a rime flake ticking off a blade, downwind
        a = COMBS[flake % 5] * (1 - shut)
        L = 0.42 - 0.08 * abs(flake % 5 - 2)
        fx, fz = rot([(0.06, L * 0.7)], a)[0]
        for j in range(2):
            G.stroke(s, G.lumpy_ellipse(fx + 0.05 + 0.06 * j, fz - 0.03 - 0.05 * j, 0.014, 0.011, n=7, seed=90 + j), M["wisp"], I, cyclic=True)


PLANTS = {"kitebloom": kitebloom, "gripweed": gripweed, "pipereed": pipereed, "stormlantern": stormlantern, "rimecomb": rimecomb}


def poses(name):
    ph = [TAU * i / 8 for i in range(8)]
    idle = {"kitebloom": [dict(phase=a, squash=1 + 0.02 * math.cos(a)) for a in ph],
            "gripweed": [dict(flutter=a, squash=1 + 0.02 * math.cos(a)) for a in ph],
            "pipereed": [dict(phase=a) for a in ph],
            "stormlantern": [dict(glow=0.6 + 0.4 * math.sin(a), squash=1 + 0.02 * math.cos(a)) for a in ph],
            "rimecomb": [dict(flake=i if i % 2 == 0 else -1, squash=1 + 0.02 * math.cos(a)) for i, a in enumerate(ph)]}[name]
    react = {"kitebloom": [dict(reel=0.4, phase=0.5), dict(reel=1.0), dict(reel=1.0, squash=0.95), dict(reel=0.5, phase=1.0)],
             "gripweed": [dict(clench=0.5), dict(clench=1.0), dict(clench=1.0, squash=0.95), dict(clench=0.4, flutter=1.0)],
             "pipereed": [dict(duck=0.5), dict(duck=1.0), dict(duck=1.0, squash=0.95), dict(duck=0.3, phase=1.0)],
             "stormlantern": [dict(draw_in=0.5, glow=0.6), dict(draw_in=1.0, glow=0.3), dict(draw_in=1.0, glow=0.2), dict(draw_in=0.4, glow=0.5)],
             "rimecomb": [dict(shut=0.5), dict(shut=1.0), dict(shut=1.0, squash=0.95), dict(shut=0.3)]}[name]
    return idle, react


def render(name, pose, scale=1, seed=7):
    from meridian import fakegp
    import gp_raster as GR
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    PLANTS[name](G.Xf(d, lambda pts: [(x * SCALE, z * SCALE) for x, z in pts]), M, pose)
    return GR.render_frame(fakegp.strokes_of(d, gp), FW * scale, FH * scale, 64 * scale, (0.5, 0.0), ss=2, seed=seed)


def neptune_strip(W, H):
    """A Neptune stand-in: the Neptune-blue sky darkening toward the indigo, long wisp-white wind streaks, a floe band."""
    import numpy as np
    rgb = lambda h: np.array(v3.hex_rgb(h), np.float32) / 255   # noqa: E731
    bg = np.empty((H, W, 3), np.float32)
    t = (np.arange(H) / H)[:, None, None]
    bg[:] = rgb(P["sky"]) * (1 - 0.35 * t) + rgb(P["brown"]) * 0.35 * t
    rng = np.random.default_rng(3)
    for _k in range(9):                                                                     # long thin streaks, blowing +x
        y, x0, ln = int(rng.integers(20, H - 90)), int(rng.integers(-200, W)), int(rng.integers(300, 900))
        xs = np.arange(max(0, x0), min(W, x0 + ln))
        if xs.size:
            fade = np.sin(np.pi * (xs - x0) / ln)[None, :, None] * 0.45
            bg[y:y + 3, xs] = bg[y:y + 3, xs] * (1 - fade) + rgb(P["offwhite"]) * fade
    g = H - 40
    bg[g:g + 14] = rgb(P["offwhite"])
    bg[g:g + 3] = rgb(v3.INK)
    bg[g + 14:] = rgb(P["teal"])
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
    review._label(head, "b-161 neptune flora designs (faceless, d-101; the neptune palette d-148; drawn upright, d-148): kitebloom, gripweed, pipereed, stormlantern, rimecomb", 6, 8)
    rows.append(head)
    widths, sheets = [], []
    scene, ground = neptune_strip(W, 300)
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
    review._label(scene, "1x on a neptune stand-in (the neptune blue toward the indigo, wind streaks blowing +x, a floe band) beside the surveyor (2 m)", 6, 6)
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
    per = [v3.palette_hits(s_, "neptune") for s_ in sheets]
    hits, off = min(h for h, _o in per), [c for _h, o in per for c in o]
    edge = [n for n, s_ in zip(PLANTS, sheets) if s_[:, :v3.EDGE_MARGIN, 3].any() or s_[:, -v3.EDGE_MARGIN:, 3].any() or s_[:v3.EDGE_MARGIN, :, 3].any()]
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; neptune palette hits >= {hits * 100:.1f}% per plant {off[:3]}; faces: none; "
                        f"touching the 2 px edge: {edge or 'none'}", 6, 8)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " preview (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b161_neptune_plants_preview.png")
    review.write(out, img)
    print("written", out, f"ink {min(w[1] for w in outer):.2f}-{max(w[2] for w in outer):.2f} / {min(w[1] for w in inner):.2f}-{max(w[2] for w in inner):.2f}",
          f"palette {hits * 100:.1f}% {off[:3]}", f"edge {edge or '-'}")


if __name__ == "__main__":
    preview(sys.argv[1])
