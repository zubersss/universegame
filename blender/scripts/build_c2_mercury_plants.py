"""B-145 (C2 Mercury design prep): five faceless Mercury plant designs as (d, M, pose) drawing functions, Grease Pencil
strokes in the Earth / Mars C2 manner (build_c2_earth_plants' hose stems and leaves), in the proposed Mercury palette
(build_c2_mercury_palette.MERCURY). No faces (D-101): personality through motion only. Heat side, twilight, shadow side.
Design previews only; the rig parts and bones follow after LEAD accepts (one Mercury rig set, the Mars pattern).

  sunfan      a fan of stiff sun-gold blades on a short ember stem; tilts edge-on on the beat; react: snaps shut, reopens
  embercap    a squat ember cap with a cracked crust and a gold underside on a stubby sage foot; breathes; react: spark dust
  glassreed   cold-teal blades with a violet edge and off-white glints (teal so they read on the violet twilight band);
              sway out of phase; react: the blades clack together
  shadebloom  a frost-tipped violet bud on a coiled sage stem; opens and closes slowly; react: shuts tight
  coilwort    a sage coil-spring stem with a teal ice bead; bounces on the beat; react: compresses, springs, settles

  python -I build_c2_mercury_plants.py <preview dir>      lock-free (meridian.fakegp)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_earth_plants as C  # noqa: E402  (the real gp_draw in Blender, the fake outside)
import build_c2_mercury_palette as MP  # noqa: E402
from meridian import v3  # noqa: E402

G = C.G
v3.PALETTES.setdefault("mercury", {k: h for k, (h, _r) in MP.MERCURY.items()})
P = v3.PALETTES["mercury"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
hose_stem, leaf, rot = C.hose_stem, C.leaf, C.rot
SCALE = 1.5                          # 0.38 g like Mars: drawn 1.5x
FW, FH = 128, 192


def SH(h):
    return v3.shadow_of(h, "mercury")


def DP(h):
    return v3.deep_of(h, "mercury")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, "mercury_" + name, **kw)
    out = {"ink": m("ink", fill=None)}
    for key, slot in (("sage", "green"), ("ember", "red"), ("gold", "mustard"), ("ice", "teal"), ("white", "offwhite"),
                      ("violet", "sky"), ("slate", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
    out["stem_fill"], out["stem_sh"] = out["sage_f"], out["sage_sh"]          # hose_stem / leaf keys
    return out


def blade(base, ang, L, W, tip=0.35):
    """A stiff narrow blade with a rounded tip, from base along ang (radians from +x)."""
    c, s = math.cos(ang), math.sin(ang)

    def at(u, v):
        return (base[0] + c * u * L - s * v * W, base[1] + s * u * L + c * v * W)
    return [at(0.0, -0.35), at(0.55, -0.5), at(1.0 - tip * 0.5, -0.42)] + \
        [at(1.0 - tip * 0.5 + tip * 0.5 * math.cos(a), 0.42 * math.sin(a) * -1) for a in (math.pi / 2 - t * math.pi / 6 for t in range(1, 6))] + \
        [at(1.0 - tip * 0.5, 0.42), at(0.55, 0.5), at(0.0, 0.35)]


# ---------------------------------------------------------------- sunfan (heat side)
def sunfan(d, M, p):
    sq, edge, shut = p.get("squash", 1.0), p.get("edge", 0.0), p.get("react", 0.0)
    S = G.Xf(d, lambda pts: [(x / math.sqrt(sq), z * sq) for x, z in pts])
    leaf(S, M, (0.0, 0.06), math.radians(160), 0.18, 0.05, veins=1)
    leaf(S, M, (0.0, 0.08), math.radians(22), 0.16, 0.045, veins=1)
    G.stroke(S, G.hose_outline(G.bezier((0.0, 0.0), (0.02, 0.16), (0.0, 0.32), n=6), 0.06), M["ember"], O, cyclic=True)
    hub = (0.0, 0.34)
    kx = 1.0 - 0.55 * edge                                                   # tilting edge-on to the Sun: the fan narrows
    F = G.Xf(S, lambda pts: [(hub[0] + (x - hub[0]) * kx, z) for x, z in pts])
    spread = 1.0 - 0.85 * shut
    for k in (0, 4, 1, 3, 2):                                                # five broad blades, the outer ones behind
        a = math.pi / 2 + (k - 2) * math.radians(30) * spread
        L = 0.30 - 0.03 * abs(k - 2)
        bl = blade(hub, a, L, 0.17)
        G.stroke(F, bl, M["gold_f"], 0.0, cyclic=True)
        G.stroke(F, blade(hub, a, L * 0.38, 0.17), M["gold_sh"], 0.0, cyclic=True)                       # the mid tone at the base
        G.seam(F, [(hub[0] + 0.07 * math.cos(a), hub[1] + 0.07 * math.sin(a)), (hub[0] + 0.19 * math.cos(a), hub[1] + 0.19 * math.sin(a))], M["ink"])
        G.stroke(F, bl, M["ink"], O, cyclic=True)
    G.stroke(F, G.lumpy_ellipse(hub[0], hub[1], 0.045, 0.04, n=12, seed=5), M["ember"], I, cyclic=True)


# ---------------------------------------------------------------- embercap (heat side)
def embercap(d, M, p):
    b, puff = p.get("breathe", 0.0), p.get("puff")
    sq = p.get("squash", 1.0) * (1 + 0.04 * b)
    S = G.Xf(d, lambda pts: [(x / math.sqrt(sq), z * sq) for x, z in pts])
    G.stroke(S, G.hose_outline([(0.0, 0.0), (0.01, 0.14)], 0.13), M["sage"], O, cyclic=True)              # the stubby foot
    G.stroke(S, G.hose_outline([(0.03, 0.0), (0.04, 0.14)], 0.05), M["sage_sh"], 0.0, cyclic=True)
    cap = [(x, max(z, 0.15)) for x, z in G.lumpy_ellipse(0.0, 0.17, 0.26, 0.15, n=36, lump=0.04, seed=11)]
    under = [(x, z) for x, z in G.lumpy_ellipse(0.0, 0.15, 0.24, 0.035, n=20, lump=0.02, seed=12)]
    G.stroke(S, under, M["gold"], I, cyclic=True)                                                         # the gold underside
    G.stroke(S, cap, M["ember_f"], 0.0, cyclic=True)
    G.stroke(S, [q for q in cap if q[0] > 0.06] + [(0.06, 0.15)], M["ember_sh"], 0.0, cyclic=True)
    for x, z, r in ((-0.12, 0.24, 0.05), (0.02, 0.29, 0.045), (0.13, 0.22, 0.04)):                        # crust plates
        G.stroke(S, G.lumpy_ellipse(x, z, r * 1.3, r, n=10, lump=0.1, seed=int(x * 100) + 20), M["ember_dp"], 0.0, cyclic=True)
    for pts in (((-0.18, 0.2), (-0.12, 0.27), (-0.05, 0.25)), ((0.04, 0.31), (0.08, 0.25), (0.15, 0.27)), ((-0.05, 0.18), (0.02, 0.22))):
        G.seam(S, list(pts), M["ink"])                                                                     # cracks
    G.stroke(S, cap, M["ink"], O, cyclic=True)
    if puff is not None:                                                                                  # spark dust
        r = 0.05 + 0.07 * puff
        blob = G.lumpy_ellipse(0.03 * puff, 0.36 + 0.22 * puff, r * 1.2, r, n=14, lump=0.12, seed=13)
        G.stroke(S, blob, M["white"], I, cyclic=True)
        G.stroke(S, [q for q in blob if q[1] < 0.36 + 0.22 * puff - 0.3 * r] + [(0.03 * puff, 0.36 + 0.22 * puff - 0.3 * r)], M["white_sh"], 0.0, cyclic=True)
        G.specks(S, [(-0.10 - 0.05 * puff, 0.4 + 0.1 * puff), (0.14 + 0.04 * puff, 0.45 + 0.08 * puff)], M["ink"])


# ---------------------------------------------------------------- glassreed (twilight)
REEDS = [(-0.09, 0.62, 100), (-0.03, 0.88, 94), (0.03, 0.74, 86), (0.08, 0.52, 78), (-0.13, 0.42, 112)]


def glassreed(d, M, p):
    a0, clack, k = p.get("sway", 0.0), p.get("react", 0.0), p.get("k", 0)
    G.stroke(d, G.lumpy_ellipse(0.0, 0.03, 0.15, 0.045, n=16, seed=31), M["slate"], O, cyclic=True)        # the base tuft
    for j, (x, L, deg) in enumerate(sorted(REEDS, key=lambda r: -r[1])):
        lean = math.radians(deg) + a0 * (1 + 0.3 * j) * math.sin(j * 1.3 + 1) - clack * (math.radians(deg) - math.pi / 2) * 0.85
        bl = blade((x, 0.04), lean, L, 0.05, tip=0.2)
        G.stroke(d, bl, M["ice_f"], 0.0, cyclic=True)                                                   # teal blades: they live on the
        edge = [(x + 0.012 * math.cos(lean + math.pi / 2) + t * L * math.cos(lean), 0.04 + 0.012 * math.sin(lean + math.pi / 2) + t * L * math.sin(lean))
                for t in (0.05, 0.9)]
        G.stroke(d, G.hose_outline(edge, 0.016), M["violet_sh"], 0.0, cyclic=True)                          # violet twilight band, a violet edge
        t = 0.45 + 0.25 * ((k + j) % 3) / 2                                                                  # the glint walks up
        G.stroke(d, G.lumpy_ellipse(x + t * L * math.cos(lean) - 0.006, 0.04 + t * L * math.sin(lean), 0.012, 0.03, n=8, seed=40 + j,
                                    rot=lean - math.pi / 2), M["white_f"], 0.0, cyclic=True)
        G.stroke(d, bl, M["ink"], O, cyclic=True)


# ---------------------------------------------------------------- shadebloom (shadow side)
def shadebloom(d, M, p):
    o, sq = p.get("open", 0.5), p.get("squash", 1.0)
    S = G.Xf(d, lambda pts: [(x / math.sqrt(sq), z * sq) for x, z in pts])
    coil = [(0.04 * math.sin(t * 3.2), t * 0.46) for t in [i / 30 for i in range(31)]]                      # the coiled stem
    leaf(S, M, (0.0, 0.08), math.radians(150), 0.16, 0.045, veins=1)
    hose_stem(S, M, coil, 0.05, rib_every=0.12)
    top = (coil[-1][0], coil[-1][1] + 0.02)
    for k in range(5):                                                                                      # petals: bud (o 0) .. open star (o 1)
        a = math.pi / 2 + (k - 2) * math.radians(14 + 26 * o)
        pet = blade(top, a, 0.17 + 0.03 * o, 0.09 + 0.03 * o, tip=0.5)
        G.stroke(S, pet, M["violet"] if k % 2 == 0 else M["violet_sh"], O, cyclic=True)
        tip = (top[0] + 0.15 * math.cos(a), top[1] + 0.15 * math.sin(a))
        G.stroke(S, G.lumpy_ellipse(tip[0], tip[1], 0.022, 0.018, n=8, seed=50 + k), M["white"], I, cyclic=True)   # frost tips
        G.seam(S, [(top[0] + 0.03 * math.cos(a), top[1] + 0.03 * math.sin(a)), (top[0] + 0.11 * math.cos(a), top[1] + 0.11 * math.sin(a))], M["ink"])
    if o > 0.4:
        G.stroke(S, G.lumpy_ellipse(top[0], top[1] + 0.02, 0.03, 0.03, n=10, seed=56), M["ice"], I, cyclic=True)


# ---------------------------------------------------------------- coilwort (cold traps)
def coilwort(d, M, p):
    h = p.get("height", 0.36)
    G.stroke(d, G.lumpy_ellipse(0.0, 0.02, 0.07, 0.03, n=12, seed=61), M["slate"], I, cyclic=True)
    spring = [(0.085 * math.sin(t * TAU * 2.5) * (1 - 0.25 * t), 0.03 + t * h) for t in [i / 48 for i in range(49)]]
    G.stroke(d, G.hose_outline(spring, 0.055), M["sage"], O, cyclic=True)
    G.stroke(d, G.hose_outline([(x + 0.012, z) for x, z in spring], 0.02), M["sage_sh"], 0.0, cyclic=True)    # the shaded side
    G.seam(d, spring[22:27], M["ink"])
    bx, bz = spring[-1][0], spring[-1][1] + 0.06
    G.stroke(d, G.lumpy_ellipse(bx, bz, 0.07, 0.065, n=16, lump=0.02, seed=62), M["ice"], O, cyclic=True)   # the ice bead
    G.stroke(d, [q for q in G.lumpy_ellipse(bx, bz, 0.07, 0.065, n=16, lump=0.02, seed=62) if q[0] > bx + 0.01] + [(bx + 0.01, bz)],
             M["ice_sh"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(bx - 0.025, bz + 0.025, 0.018, 0.014, n=8, seed=63), M["white_f"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(bx, bz, 0.07, 0.065, n=16, lump=0.02, seed=62), M["ink"], O, cyclic=True)


PLANTS = {"sunfan": sunfan, "embercap": embercap, "glassreed": glassreed, "shadebloom": shadebloom, "coilwort": coilwort}


def poses(name):
    """The idle (8 frames on the beat) and the react (4) for one plant."""
    ph = [TAU * i / 8 for i in range(8)]
    idle = {"sunfan": [dict(edge=0.5 + 0.5 * math.sin(a), squash=1 + 0.02 * math.cos(a)) for a in ph],
            "embercap": [dict(breathe=math.cos(a)) for a in ph],
            "glassreed": [dict(sway=0.06 * math.sin(a), k=i) for i, a in enumerate(ph)],
            "shadebloom": [dict(open=0.5 + 0.45 * math.sin(a), squash=1 + 0.02 * math.cos(a)) for a in ph],
            "coilwort": [dict(height=0.36 + 0.04 * math.sin(a)) for a in ph]}[name]
    react = {"sunfan": [dict(react=0.6, squash=0.95), dict(react=1.0, squash=0.9), dict(react=0.7), dict(react=0.2, squash=1.03)],
             "embercap": [dict(squash=0.9, puff=0.1), dict(squash=1.06, puff=0.5), dict(puff=0.9), dict(puff=1.2, squash=0.98)],
             "glassreed": [dict(react=0.5, k=1), dict(react=1.0, k=2), dict(react=1.0, sway=0.02, k=2), dict(react=0.4, k=3)],
             "shadebloom": [dict(open=0.3, squash=0.95), dict(open=0.0, squash=0.9), dict(open=0.0), dict(open=0.15, squash=1.02)],
             "coilwort": [dict(height=0.22), dict(height=0.50), dict(height=0.32), dict(height=0.38)]}[name]
    return idle, react


def render(name, pose, scale=1, seed=7):
    from meridian import fakegp
    import gp_raster as GR
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    PLANTS[name](G.Xf(d, lambda pts: [(x * SCALE, z * SCALE) for x, z in pts]), M, pose)
    return GR.render_frame(fakegp.strokes_of(d, gp), FW * scale, FH * scale, 64 * scale, (0.5, 0.0), ss=2, seed=seed)


def mercury_strip(W, H):
    """A Mercury stand-in for the design review: an ink-black day sky, a violet twilight band low down, the blinding
    regolith ground with a slate shadow edge."""
    import numpy as np
    rgb = lambda h: np.array(v3.hex_rgb(h), np.float32) / 255   # noqa: E731
    bg = np.empty((H, W, 3), np.float32)
    t = (np.arange(H) / H)[:, None, None]
    bg[:] = rgb(v3.INK) * (1 - np.clip((t - 0.45) / 0.3, 0, 1)) + rgb(P["sky"]) * np.clip((t - 0.45) / 0.3, 0, 1)
    rng = np.random.default_rng(3)
    for _k in range(40):
        y, x = int(rng.uniform(5, H * 0.4)), int(rng.uniform(0, W))
        bg[y, x] = rgb(P["offwhite"])
    bg[H - 40:] = rgb(P["offwhite"])
    bg[H - 40:H - 36] = rgb(SH(P["offwhite"]))
    bg *= (1 + 0.02 * rng.standard_normal((H, W, 1))).astype(np.float32)
    return bg, H - 40


def preview(out_dir):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    W = 1960
    rows = []
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, "b-145 mercury plant designs (faceless, d-101; proposed mercury palette): sunfan, embercap, glassreed, shadebloom, coilwort; lock-free fakegp", 6, 8)
    rows.append(head)
    widths, sheets = [], []
    scene, ground = mercury_strip(W, 300)
    x = 30
    for name in PLANTS:
        img, w = render(name, poses(name)[0][0])
        widths += w
        sheets.append(img)
        review._over(scene, img, x, ground - FH + 8)
        review._label(scene, name, x + 10, ground + 14, scale=1)
        x += FW + 40
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, x + 20, ground - fr.shape[0] + int(round(piv[1] * fr.shape[0])) + 8)
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, "1x on a mercury stand-in (ink-black day sky, a violet twilight band, the blinding regolith) beside the surveyor (2 m)", 6, 6)
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
    per = [v3.palette_hits(s_, "mercury") for s_ in sheets]
    hits, off = min(h for h, _o in per), [c for _h, o in per for c in o]
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; mercury palette hits >= {hits * 100:.1f}% per plant {off[:3]}; faces: none", 6, 8)
    review._label(foot, "designs only: rig parts + bones (<= 6) and one mercury rig set after lead accepts; biomes per plant in c2_mercury_designs.md", 6, 28)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " preview (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b145_mercury_plants_preview.png")
    review.write(out, img)
    print("written", out, f"ink {min(w[1] for w in outer):.2f}-{max(w[2] for w in outer):.2f} / {min(w[1] for w in inner):.2f}-{max(w[2] for w in inner):.2f}",
          f"palette {hits * 100:.1f}% {off[:3]}")


if __name__ == "__main__":
    preview(sys.argv[1])
