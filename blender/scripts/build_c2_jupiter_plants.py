"""B-155 (C2 Jupiter design prep): five faceless Jupiter flora as (d, M, pose) drawing functions in the C2 manner
(build_c2_earth_plants' hose stems and leaves), in the Jupiter palette (D-137). No faces (D-101): personality through
motion only. At 2.53 g the floe forms are low and broad (no tall stalks); the float-cell form floats, so gravity reads in
its tether, drawn taut downward. The wind (12 m/s in the Spot, steady elsewhere) blows to +x. Each plant is built from
part functions so the rig set can cut it later. Drawn 1.6x so they read beside the 2 m surveyor (1.4x read too small).

  driftbulb     a float-cell form: a cream gas bulb with a rust band and ribbed seams on a taut sage tether to its floe;
                bobs with a squash; react: deflates and dips, then refills
  bandstreamer  a squat sage holdfast on a floe edge trailing three cream-and-rust striped streamers on the wind; the
                streamers wave (a cascade); react: they wrap round the holdfast
  frostrosette  a low rosette of cream ammonia-ice crystal leaves with festoon blue-grey facets; a glint walks the tips on
                the beat; react: the crystals fold shut
  phosphorcup   brick-red cup blooms with phosphor specks on a coiled sage stem (the Red Spot floes); the cups open / close;
                react: they close and the plant spins once (the Spot's wind)
  stormreed     a clump of short stiff sage reeds tipped with festoon blue-grey bulbs; the tips flicker (a tone, no
                emission) as lightning walks under the floor; react: the reeds flatten

  python -I build_c2_jupiter_plants.py <preview dir>      lock-free (meridian.fakegp)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_earth_plants as C  # noqa: E402  (the real gp_draw in Blender, the fake outside)
from meridian import v3  # noqa: E402

G = C.G
P = v3.PALETTES["jupiter"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
hose_stem, leaf, rot = C.hose_stem, C.leaf, C.rot
SCALE = 1.6                          # drawn 1.6x like Venus' (at 1.4x the floe preview showed the Frostrosette barely over the frost lip)
FW, FH = 160, 192


def SH(h):
    return v3.shadow_of(h, "jupiter")


def DP(h):
    return v3.deep_of(h, "jupiter")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, "jupiter_" + name, **kw)
    out = {"ink": m("ink", fill=None)}
    for key, slot in (("sage", "green"), ("brick", "red"), ("rust", "mustard"), ("festoon", "teal"), ("cream", "offwhite"),
                      ("tan", "sky"), ("umber", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
    out["stem_fill"], out["stem_sh"] = out["sage_f"], out["sage_sh"]
    return out


def xf(d, sx=1.0, sz=1.0, dx=0.0, dz=0.0):
    """Scale about the root then shift (the spin's x squash, a bob, a squash)."""
    return G.Xf(d, lambda pts: [(x * sx + dx, z * sz + dz) for x, z in pts])


def lens(cx, cz, rx, rz, z0, z1, n=8):
    """The slice of the ellipse (cx, cz, rx, rz) between heights z0 < z1, as a closed polygon (a band round a bulb)."""
    def half(z):
        u = max(0.0, 1.0 - ((z - cz) / rz) ** 2)
        return rx * math.sqrt(u)
    zs = [z0 + (z1 - z0) * k / (n - 1) for k in range(n)]
    return [(cx - half(z), z) for z in zs] + [(cx + half(z), z) for z in reversed(zs)]


# ---------------------------------------------------------------- driftbulb (a float-cell form, decks 1-2)
def driftbulb_tether(d, M):
    """The holdfast knot on the floe and the taut tether up to the bulb's knot at (0.02, 0.40)."""
    G.stroke(d, G.lumpy_ellipse(0.0, 0.02, 0.06, 0.025, n=12, lump=0.1, seed=31), M["sage_sh"], I, cyclic=True)
    hose_stem(d, M, G.bezier((0.0, 0.02), (0.012, 0.2), (0.02, 0.40), n=7), 0.04, rib_every=0.14)            # wide enough for the sage to show


def driftbulb_bulb(d, M, fill=1.0):
    """The bulb above its knot at (0, 0): cream, one rust band, two ribbed seams, the lee side in mid tone; fill 1 full .. 0.45 sagging."""
    rx, rz = 0.15 * (0.75 + 0.25 * fill), 0.17 * (0.6 + 0.4 * fill)
    cz = 0.03 + rz
    bulb = G.lumpy_ellipse(0.0, cz, rx, rz, n=28, lump=0.02 + 0.06 * (1 - fill), seed=32)
    G.stroke(d, bulb, M["cream_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in bulb if q[0] > rx * 0.25] + [(rx * 0.25, cz)], M["cream_sh"], 0.0, cyclic=True)
    G.stroke(d, lens(0.0, cz, rx * 0.98, rz, cz - 0.03, cz + 0.035), M["rust_f"], 0.0, cyclic=True)
    for k in (-1, 1):
        G.seam(d, G.bezier((0.0, 0.035), (rx * 0.75 * k, cz), (0.0, cz + rz - 0.01), n=7), M["ink"])
    G.stroke(d, bulb, M["ink"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, 0.025, 0.03, 0.022, n=10, seed=33), M["sage"], I, cyclic=True)    # the knot


def driftbulb(d, M, p):
    driftbulb_tether(d, M)
    sq = p.get("squash", 1.0)
    b = xf(d, 1.0 / math.sqrt(sq), sq, 0.02 + p.get("sway", 0.0), 0.40 + p.get("bob", 0.0))
    driftbulb_bulb(b, M, p.get("fill", 1.0))


# ---------------------------------------------------------------- bandstreamer (deck 1, floe edges)
STREAMERS = ((0.04, 0.13, 0.62, 0.0), (0.06, 0.10, 0.50, 1.2), (0.02, 0.15, 0.44, 2.3))     # (x, z, length, phase offset)


def bandstreamer_holdfast(d, M):
    dome = [(x, max(z, 0.0)) for x, z in G.lumpy_ellipse(0.0, 0.03, 0.12, 0.10, n=22, lump=0.06, seed=41)]
    G.stroke(d, dome, M["sage_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in dome if q[0] > 0.03] + [(0.03, 0.0)], M["sage_sh"], 0.0, cyclic=True)
    for x in (-0.06, 0.0, 0.06):
        G.seam(d, [(x, 0.01), (x * 1.2, 0.09)], M["ink"])
    G.stroke(d, dome, M["ink"], O, cyclic=True)


def bandstreamer_streamer(d, M, k, phase=0.0, wrap=0.0):
    """Streamer k from its root on the holdfast, trailing to +x on the wind (wrap 1 = wound round the holdfast)."""
    x0, z0, L, ph0 = STREAMERS[k]
    n = 14
    pts = []
    for i in range(n + 1):
        t = i / n
        free = (x0 + L * t, z0 + 0.10 * t + 0.05 * t * math.sin(phase + ph0 - 5.0 * t))
        a = math.pi * 0.6 - TAU * 0.85 * t                                                # the wrapped path: round the dome
        wound = (0.13 * math.cos(a) * (1 - 0.2 * t), 0.06 + 0.11 * math.sin(a) * (1 - 0.2 * t))
        pts.append((free[0] * (1 - wrap) + wound[0] * wrap, free[1] * (1 - wrap) + wound[1] * wrap))
    w = 0.03
    out = G.hose_outline(pts, w)
    G.stroke(d, out, M["cream_f"], 0.0, cyclic=True)
    for i in range(1, n - 1, 3):                                                          # the rust stripes
        G.stroke(d, G.hose_outline(pts[i:i + 2], w * 0.98), M["rust_f"], 0.0, cyclic=True)
    G.stroke(d, out, M["ink"], I, cyclic=True)


def bandstreamer(d, M, p):
    s = xf(d, 1.0 / math.sqrt(p.get("squash", 1.0)), p.get("squash", 1.0))
    for k in (1, 2):                                                                      # two behind the holdfast
        bandstreamer_streamer(s, M, k, p.get("phase", 0.0), p.get("wrap", 0.0))
    bandstreamer_holdfast(s, M)
    bandstreamer_streamer(s, M, 0, p.get("phase", 0.0), p.get("wrap", 0.0))


# ---------------------------------------------------------------- frostrosette (deck 1, floe tops; Cryo 2)
CRYSTALS = ((25, 0.22), (52, 0.29), (76, 0.34), (98, 0.31), (122, 0.27), (148, 0.21), (88, 0.19))   # (deg, length)


def frostrosette_crystal(d, M, deg, L, glint=False):
    """One ammonia-ice crystal leaf from (0, 0.01): a faceted cream shard, its far facet in festoon blue-grey."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)

    def at(u, v):
        return (c * u * L - s * v * 0.065, 0.01 + s * u * L + c * v * 0.065)
    sh = [at(0, -0.7), at(0.7, -1.0), at(1.0, 0.0), at(0.7, 1.0), at(0, 0.7)]
    G.stroke(d, sh, M["cream_f"], 0.0, cyclic=True)
    G.stroke(d, [at(0, 0.0), at(1.0, 0.0), at(0.7, -1.0), at(0, -0.7)], M["festoon_f"], 0.0, cyclic=True)
    G.seam(d, [at(0.15, 0.0), at(0.85, 0.0)], M["ink"])
    G.stroke(d, sh, M["ink"], I if L < 0.24 else O, cyclic=True)
    if glint:                                                                             # a four-point glint at the tip
        tx, tz = at(1.0, 0.0)
        for ang in (0.0, math.pi / 2):
            G.stroke(d, [(tx - 0.035 * math.cos(ang), tz - 0.035 * math.sin(ang)), (tx + 0.035 * math.cos(ang), tz + 0.035 * math.sin(ang))],
                     M["cream"], I)


def frostrosette(d, M, p):
    fold = p.get("fold", 0.0)
    s = xf(d, 1.0 / math.sqrt(p.get("squash", 1.0)), p.get("squash", 1.0))
    G.stroke(s, G.lumpy_ellipse(0.0, 0.01, 0.10, 0.025, n=12, seed=51), M["festoon_sh"], I, cyclic=True)
    order = sorted(range(len(CRYSTALS)), key=lambda k: -abs(CRYSTALS[k][0] - 90))       # the outer crystals first
    for k in order:
        deg, L = CRYSTALS[k]
        deg = deg + (90 - deg) * 0.75 * fold
        frostrosette_crystal(s, M, deg, L * (1 - 0.35 * fold), glint=(k == p.get("glint", -1)))


# ---------------------------------------------------------------- phosphorcup (the Great Red Spot's floes)
CUP_TIPS = ((-0.10, 0.36, 160), (0.06, 0.42, 20), (0.14, 0.30, 0))                       # (x, z, the cup's facing deg)


def phosphorcup_stem(d, M):
    """A coiled sage stem: one loop above the floe, then three short pedicels to the cups."""
    coil = [(0.05 * math.sin(TAU * t * 1.0) - 0.0, 0.03 + 0.20 * t + 0.035 * (1 - math.cos(TAU * t))) for t in [k / 14 for k in range(15)]]
    hose_stem(d, M, coil, 0.06, rib_every=0.1)
    top = coil[-1]
    for x, z, _deg in CUP_TIPS:
        hose_stem(d, M, G.bezier(top, ((top[0] + x) / 2, z - 0.02), (x, z), n=6), 0.045, rib_every=0.2)
    leaf(d, M, (0.02, 0.10), math.radians(25), 0.13, 0.04, veins=1)


def phosphorcup_cup(d, M, open_=1.0, seed=61):
    """One brick cup above (0, 0): open 1 a wide bowl with a rust inside and cream phosphor specks, 0 a closed bud."""
    w = 0.035 + 0.05 * open_
    h = 0.10 - 0.02 * open_
    cup = G.bezier((-0.01, 0.0), (-w * 1.2, h * 0.3), (-w, h), n=7) + G.bezier((w, h), (w * 1.2, h * 0.3), (0.01, 0.0), n=7)
    if open_ < 0.3:
        cup = G.bezier((-0.01, 0.0), (-w * 1.3, h * 0.5), (0.0, h * 1.15), n=8) + G.bezier((0.0, h * 1.15), (w * 1.3, h * 0.5), (0.01, 0.0), n=8)[1:]
    G.stroke(d, cup, M["brick_f"], 0.0, cyclic=True)
    if open_ >= 0.3:
        G.stroke(d, G.lumpy_ellipse(0.0, h, w, 0.022 * open_ + 0.005, n=14, seed=seed), M["rust_f"], 0.0, cyclic=True)   # the inside
        G.specks(d, [(-w * 0.4, h + 0.004), (w * 0.3, h - 0.004), (0.0, h + 0.008)], M["cream"])
    G.stroke(d, [q for q in cup if q[0] > 0.0] + [(0.0, 0.0)], M["brick_sh"], 0.0, cyclic=True)
    G.stroke(d, cup, M["ink"], O, cyclic=True)


def phosphorcup(d, M, p):
    s = xf(d, p.get("spin", 1.0) / math.sqrt(p.get("squash", 1.0)), p.get("squash", 1.0))
    phosphorcup_stem(s, M)
    for k, (x, z, deg) in enumerate(CUP_TIPS):
        a = math.radians(deg) * 0.25
        cup = G.Xf(s, lambda pts, x=x, z=z, a=a: [(x + px * math.cos(a) - pz * math.sin(a), z + px * math.sin(a) + pz * math.cos(a)) for px, pz in pts])
        phosphorcup_cup(cup, M, p.get("open", 1.0) * (1.0 - 0.15 * k * p.get("stagger", 0.0)), seed=61 + k)


# ---------------------------------------------------------------- stormreed (decks 2-3)
REEDS = ((-0.11, 0.26, 106), (-0.05, 0.36, 97), (0.0, 0.30, 88), (0.06, 0.40, 81), (0.11, 0.24, 70))   # (x, length, deg)


def stormreed_tuft(d, M):
    G.stroke(d, G.lumpy_ellipse(0.0, 0.02, 0.13, 0.035, n=14, lump=0.08, seed=71), M["umber_sh"], I, cyclic=True)


def stormreed_reed(d, M, x, L, deg, lit=False):
    """One stiff reed from (x, 0.02) and its festoon bulb; lit = the flicker (the bulb paled to cream, a tone)."""
    a = math.radians(deg)
    tip = (x + L * math.cos(a), 0.02 + L * math.sin(a))
    hose_stem(d, M, [(x, 0.02), (x + 0.5 * L * math.cos(a) + 0.01, 0.02 + 0.5 * L * math.sin(a)), tip], 0.045, rib_every=0.12)
    bulb = G.lumpy_ellipse(tip[0], tip[1] + 0.02, 0.032, 0.04, n=14, lump=0.04, seed=int(x * 100) + 72)
    G.stroke(d, bulb, M["cream_f" if lit else "festoon_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in bulb if q[0] > tip[0] + 0.005] + [(tip[0] + 0.005, tip[1] + 0.02)], M["cream_sh" if lit else "festoon_sh"], 0.0, cyclic=True)
    G.stroke(d, bulb, M["ink"], I, cyclic=True)


def stormreed(d, M, p):
    s = xf(d, 1.0 / math.sqrt(p.get("squash", 1.0)), p.get("squash", 1.0))
    stormreed_tuft(s, M)
    flat = p.get("flat", 0.0)
    for k, (x, L, deg) in enumerate(REEDS):
        side = 1 if deg >= 88 else -1                                                     # flatten away from the centre
        dd = deg + side * 62 * flat + 4 * math.sin(p.get("phase", 0.0) + k)
        stormreed_reed(s, M, x, L * (1 - 0.1 * flat), dd, lit=(k in p.get("lit", ())))


PLANTS = {"driftbulb": driftbulb, "bandstreamer": bandstreamer, "frostrosette": frostrosette, "phosphorcup": phosphorcup,
          "stormreed": stormreed}


def poses(name):
    ph = [TAU * i / 8 for i in range(8)]
    idle = {"driftbulb": [dict(bob=0.03 * math.sin(a), sway=0.015 * math.sin(a - 0.8), squash=1 + 0.04 * math.cos(2 * a)) for a in ph],
            "bandstreamer": [dict(phase=a * 2) for a in ph],
            "frostrosette": [dict(glint=i % 7 if i % 2 == 0 else -1, squash=1 + 0.02 * math.cos(a)) for i, a in enumerate(ph)],
            "phosphorcup": [dict(open=0.6 + 0.4 * math.cos(a), stagger=1.0, squash=1 + 0.02 * math.cos(a)) for a in ph],
            "stormreed": [dict(phase=a, lit=(i % 5, (i + 2) % 5) if i in (2, 3, 6) else ()) for i, a in enumerate(ph)]}[name]
    react = {"driftbulb": [dict(fill=0.7, bob=-0.04, squash=0.92), dict(fill=0.45, bob=-0.08, squash=0.88), dict(fill=0.7, bob=-0.04), dict(fill=1.0, squash=1.05)],
             "bandstreamer": [dict(wrap=0.4, phase=1.0), dict(wrap=0.85), dict(wrap=1.0), dict(wrap=0.5, phase=2.0)],
             "frostrosette": [dict(fold=0.4, squash=0.96), dict(fold=1.0, squash=0.92), dict(fold=1.0), dict(fold=0.3)],
             "phosphorcup": [dict(open=0.2, spin=0.5), dict(open=0.0, spin=-0.5), dict(open=0.0, spin=-1.0), dict(open=0.4, spin=1.0)],   # never narrower than half (all ink)
             "stormreed": [dict(flat=0.5, lit=(0, 1, 2, 3, 4)), dict(flat=1.0), dict(flat=1.0, squash=0.95), dict(flat=0.4)]}[name]
    return idle, react


def render(name, pose, scale=1, seed=7):
    from meridian import fakegp
    import gp_raster as GR
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    PLANTS[name](G.Xf(d, lambda pts: [(x * SCALE, z * SCALE) for x, z in pts]), M, pose)
    return GR.render_frame(fakegp.strokes_of(d, gp), FW * scale, FH * scale, 64 * scale, (0.5, 0.0), ss=2, seed=seed)


def jupiter_strip(W, H):
    """A Jupiter stand-in: a zone-tan sky with far cream and rust bands, a floe band (cream ice top, a frost lip, an umber
    underside fading to the cloud)."""
    import numpy as np
    rgb = lambda h: np.array(v3.hex_rgb(h), np.float32) / 255   # noqa: E731
    bg = np.empty((H, W, 3), np.float32)
    bg[:] = rgb(P["sky"])
    y = np.arange(H)[:, None]
    x = np.arange(W)[None, :]
    for k, (y0, th, col) in enumerate(((40, 26, "offwhite"), (90, 18, "mustard"), (140, 30, "offwhite"), (190, 14, "red"))):
        line = y0 + 6 * np.sin(x / W * TAU * (2 + k) + k)
        band = (y > line) & (y < line + th)
        bg[band] = bg[band] * 0.45 + rgb(P[col]) * 0.55
    g = H - 40
    bg[g:g + 14] = rgb(P["offwhite"])
    bg[g:g + 3] = rgb(v3.INK)
    bg[g + 14:] = rgb(SH(P["sky"]))
    bg[g + 14:g + 16] = rgb(DP(P["sky"]))
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
    review._label(head, "b-155 jupiter flora designs (faceless, d-101; the jupiter palette d-137): driftbulb, bandstreamer, frostrosette (deck 1), "
                        "phosphorcup (the red spot), stormreed (decks 2-3)", 6, 8)
    rows.append(head)
    widths, sheets = [], []
    scene, ground = jupiter_strip(W, 300)
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
    review._label(scene, "1x on a jupiter stand-in (zone tan with far cream / rust bands, a floe band) beside the surveyor (2 m)", 6, 6)
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
    per = [v3.palette_hits(s_, "jupiter") for s_ in sheets]
    hits, off = min(h for h, _o in per), [c for _h, o in per for c in o]
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; jupiter palette hits >= {hits * 100:.1f}% per plant {off[:3]}; faces: none", 6, 8)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " preview (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b155_jupiter_plants_preview.png")
    review.write(out, img)
    print("written", out, f"ink {min(w[1] for w in outer):.2f}-{max(w[2] for w in outer):.2f} / {min(w[1] for w in inner):.2f}-{max(w[2] for w in inner):.2f}",
          f"palette {hits * 100:.1f}% {off[:3]}")


if __name__ == "__main__":
    preview(sys.argv[1])
