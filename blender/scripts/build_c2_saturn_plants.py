"""B-157 (C2 Saturn design prep): five faceless Saturn flora as (d, M, pose) drawing functions in the C2 manner
(build_c2_earth_plants' hose stems and leaves), in the proposed Saturn palette (build_c2_saturn_palette; registered with
setdefault until LEAD accepts it into v3.PALETTES). No faces (D-101): personality through motion only. At 1.06 g the
forms stand taller than Jupiter's. Each plant is built from part functions so the rig set can cut it later. Drawn 1.6x
(the Venus / Jupiter scale).

  ringreed     tall pale-moss reeds whose tips carry thin cream rings (little halos, like the planet's); the rings tilt and
               catch the light on the beat; react: the rings drop down the stems
  heliumbell   a pale-gold bell on a coiled stem (helium inside); bobs, the bell swells; react: it rises on its stretched
               stem, then sinks back
  frostfan     a fan of cream ice fronds edged ring-ice blue-grey on a floe top; opens / closes on the beat; react: folds flat
  hexmoss      a low cushion of hexagon cells (the pole's pattern) with dusk-salmon rims; the cells pulse in a ring; react:
               it hunkers down
  butterpuff   a cluster of butter-cream puffballs on short stalks; they breathe; react: a spore puff (cream tone dots)

  python -I build_c2_saturn_plants.py <preview dir>      lock-free (meridian.fakegp)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_earth_plants as C  # noqa: E402  (the real gp_draw in Blender, the fake outside)
from meridian import v3  # noqa: E402

G = C.G
P = v3.PALETTES["saturn"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
hose_stem, leaf, rot = C.hose_stem, C.leaf, C.rot
SCALE = 1.6
FW, FH = 160, 192


def SH(h):
    return v3.shadow_of(h, "saturn")


def DP(h):
    return v3.deep_of(h, "saturn")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, "saturn_" + name, **kw)
    out = {"ink": m("ink", fill=None)}
    for key, slot in (("moss", "green"), ("salmon", "red"), ("gold", "mustard"), ("ice", "teal"), ("cream", "offwhite"),
                      ("butter", "sky"), ("slate", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
    out["stem_fill"], out["stem_sh"] = out["moss_f"], out["moss_sh"]
    return out


def xf(d, sx=1.0, sz=1.0, dx=0.0, dz=0.0):
    return G.Xf(d, lambda pts: [(x * sx + dx, z * sz + dz) for x, z in pts])


# ---------------------------------------------------------------- ringreed (decks 1-2)
REEDS = ((-0.07, 0.58, 98), (0.0, 0.74, 91), (0.07, 0.50, 83))                          # (x, length, deg)


def ringreed_tuft(d, M):
    G.stroke(d, G.lumpy_ellipse(0.0, 0.02, 0.10, 0.03, n=12, lump=0.08, seed=81), M["moss_sh"], I, cyclic=True)


def ringreed_reed(d, M, k, tilt=0.0, drop=0.0):
    """Reed k from (x, 0.02) and the cream ring round its tip (tilt -1..1 turns the ring's ellipse; drop 0..1 slides it down)."""
    x, L, deg = REEDS[k]
    a = math.radians(deg)
    tip = (x + L * math.cos(a), 0.02 + L * math.sin(a))
    hose_stem(d, M, [(x, 0.02), (x + 0.5 * L * math.cos(a), 0.02 + 0.5 * L * math.sin(a)), tip], 0.045, rib_every=0.14)
    G.stroke(d, G.lumpy_ellipse(tip[0], tip[1] + 0.02, 0.022, 0.03, n=10, seed=82 + k), M["moss"], I, cyclic=True)   # the tip bud
    rz = tip[1] - 0.05 - drop * (L * 0.6)
    rx_ = tip[0] - drop * (L * 0.6) * math.cos(a)
    ring = G.lumpy_ellipse(rx_, rz, 0.12, 0.028 + 0.022 * abs(tilt), n=24, lump=0.0, seed=84 + k, rot=0.35 * tilt)   # big enough to read at 1x
    inner = G.lumpy_ellipse(rx_, rz, 0.075, 0.012 + 0.014 * abs(tilt), n=20, lump=0.0, seed=85 + k, rot=0.35 * tilt)
    G.stroke(d, ring + inner[::-1], M["cream_f"], 0.0, cyclic=True)
    G.stroke(d, ring, M["ink"], I, cyclic=True)
    G.stroke(d, inner, M["ink"], I, cyclic=True)


def ringreed(d, M, p):
    s = xf(d, 1.0 / math.sqrt(p.get("squash", 1.0)), p.get("squash", 1.0))
    ringreed_tuft(s, M)
    for k in range(len(REEDS)):
        ringreed_reed(s, M, k, p.get("tilt", 0.0) * (1 if k % 2 else -1), p.get("drop", 0.0))


# ---------------------------------------------------------------- heliumbell (decks 2-3)
def heliumbell_stem(d, M, stretch=1.0):
    """A coiled stem from the floe to (0, 0.38 * stretch): its coils open as it stretches."""
    n = 18
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((0.045 * math.sin(TAU * 2.5 * t) * (1.2 - 0.6 * stretch * t), 0.02 + 0.36 * stretch * t))
    hose_stem(d, M, pts, 0.04, rib_every=0.2)
    leaf(d, M, (0.0, 0.10), math.radians(150), 0.13, 0.04, veins=1)


def heliumbell_bell(d, M, swell=0.0):
    """The bell from its stalk tip at (0, 0) downward-opening: pale gold, a cream lip, a salmon inside; swell 0..1."""
    w = 0.11 * (1 + 0.25 * swell)
    h = 0.17 * (1 + 0.15 * swell)
    bell = G.bezier((-0.015, 0.0), (-w * 1.1, -h * 0.2), (-w, -h), n=8) + [(-w * 0.5, -h - 0.02), (w * 0.5, -h - 0.02)] + \
        G.bezier((w, -h), (w * 1.1, -h * 0.2), (0.015, 0.0), n=8)
    G.stroke(d, bell, M["gold_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in bell if q[0] > w * 0.3] + [(w * 0.3, -h * 0.5)], M["gold_sh"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, -h - 0.005, w * 0.75, 0.025, n=14, seed=91), M["salmon_dp"], 0.0, cyclic=True)   # the inside
    G.stroke(d, [(-w, -h), (-w * 0.5, -h - 0.02), (w * 0.5, -h - 0.02), (w, -h), (w * 0.85, -h + 0.03), (-w * 0.85, -h + 0.03)], M["cream_f"], 0.0, cyclic=True)
    G.seam(d, [(0.0, -0.02), (0.0, -h * 0.85)], M["ink"])
    G.stroke(d, bell, M["ink"], O, cyclic=True)


def heliumbell(d, M, p):
    st = p.get("stretch", 1.0)
    s = xf(d, 1.0, 1.0, 0.0, p.get("bob", 0.0))
    heliumbell_stem(s, M, st)
    heliumbell_bell(xf(s, 1.0, 1.0, 0.0, 0.02 + 0.36 * st + 0.02), M, p.get("swell", 0.0))
    G.stroke(s, [(0.0, 0.02 + 0.36 * st), (0.0, 0.04 + 0.36 * st)], M["ink"], I)


# ---------------------------------------------------------------- frostfan (deck 1, floe tops)
def frostfan_frond(d, M, deg, L, k):
    """One cream ice frond from (0, 0.02): a long lens edged ring-ice blue-grey."""
    a = math.radians(deg)
    c, s_ = math.cos(a), math.sin(a)

    def at(u, v):
        return (c * u * L - s_ * v * 0.045, 0.02 + s_ * u * L + c * v * 0.045)
    sh = [at(0, 0)] + [at(t, math.sin(math.pi * t) * (1.2 - 0.4 * t)) for t in (0.2, 0.45, 0.7, 0.9)] + [at(1.0, 0.0)] + \
        [at(t, -math.sin(math.pi * t) * (1.2 - 0.4 * t)) for t in (0.9, 0.7, 0.45, 0.2)]
    G.stroke(d, sh, M["cream_f"], 0.0, cyclic=True)
    G.stroke(d, [at(0.15, 0.0)] + [at(t, -math.sin(math.pi * t) * (1.2 - 0.4 * t)) for t in (0.2, 0.45, 0.7, 0.9)] + [at(1.0, 0.0)], M["ice_f"], 0.0, cyclic=True)
    G.seam(d, [at(0.1, 0.0), at(0.85, 0.0)], M["ink"])
    G.stroke(d, sh, M["ink"], I if L < 0.3 else O, cyclic=True)


FAN = (30, 52, 72, 90, 108, 128, 150)


def frostfan(d, M, p):
    open_ = p.get("open", 1.0)
    s = xf(d, 1.0 / math.sqrt(p.get("squash", 1.0)), p.get("squash", 1.0))
    G.stroke(s, G.lumpy_ellipse(0.0, 0.015, 0.09, 0.025, n=12, seed=95), M["ice_sh"], I, cyclic=True)
    order = sorted(range(len(FAN)), key=lambda k: -abs(FAN[k] - 90))
    for k in order:
        deg = 90 + (FAN[k] - 90) * open_
        frostfan_frond(s, M, deg, 0.40 - 0.08 * abs(FAN[k] - 90) / 60, k)


# ---------------------------------------------------------------- hexmoss (the Hexagon's eye)
HEX_CELLS = [(-0.16, 0.05), (0.0, 0.05), (0.16, 0.05), (-0.08, 0.13), (0.08, 0.13), (0.0, 0.205)]


def hexmoss(d, M, p):
    """A low cushion of hexagon cells; `pulse` lights cell k (a salmon rim); hunker squashes it flat."""
    hk = 1.0 - 0.35 * p.get("hunker", 0.0)
    s = xf(d, 1.0 / math.sqrt(hk), hk * p.get("squash", 1.0))
    dome = [(x, max(z, 0.0)) for x, z in G.lumpy_ellipse(0.0, 0.04, 0.28, 0.22, n=30, lump=0.04, seed=96)]
    G.stroke(s, dome, M["moss_f"], 0.0, cyclic=True)
    G.stroke(s, [q for q in dome if q[0] > 0.1] + [(0.1, 0.04)], M["moss_sh"], 0.0, cyclic=True)
    for k, (cx, cz) in enumerate(HEX_CELLS):
        hexa = [(cx + 0.075 * math.cos(a), cz + 0.05 * math.sin(a)) for a in [j * TAU / 6 + math.pi / 6 for j in range(6)]]
        lit = k == p.get("pulse", -1)
        G.stroke(s, hexa, M["salmon_f"] if lit else M["moss_dp"], 0.0, cyclic=True)
        G.stroke(s, hexa, M["salmon"] if lit else M["ink"], I, cyclic=True)
    G.stroke(s, dome, M["ink"], O, cyclic=True)


# ---------------------------------------------------------------- butterpuff (decks 1-2)
PUFFS = ((-0.10, 0.22, 0.07), (0.02, 0.30, 0.08), (0.12, 0.18, 0.06), (-0.02, 0.14, 0.05))   # (x, height, radius)


def butterpuff(d, M, p):
    s = xf(d, 1.0 / math.sqrt(p.get("squash", 1.0)), p.get("squash", 1.0))
    G.stroke(s, G.lumpy_ellipse(0.0, 0.02, 0.12, 0.03, n=12, seed=97), M["moss_sh"], I, cyclic=True)
    br = p.get("breathe", 0.0)
    for k, (x, h, r) in enumerate(PUFFS):
        hose_stem(s, M, [(x * 0.4, 0.02), (x * 0.8, h * 0.5), (x, h)], 0.038, rib_every=0.3)      # wide enough for the moss to show
        rr = r * (1 + 0.08 * math.sin(br + k))
        ball = G.lumpy_ellipse(x, h + rr * 0.8, rr, rr * 0.92, n=18, lump=0.06, seed=98 + k)
        G.stroke(s, ball, M["butter_f"], 0.0, cyclic=True)
        G.stroke(s, [q for q in ball if q[0] > x + rr * 0.2] + [(x + rr * 0.2, h + rr * 0.8)], M["butter_sh"], 0.0, cyclic=True)
        G.specks(s, [(x - rr * 0.3, h + rr * 1.0), (x + rr * 0.1, h + rr * 0.6)], M["ink"])
        G.stroke(s, ball, M["ink"], I, cyclic=True)
    t = p.get("spores")
    if t is not None:                                                                     # a spore puff: cream tone dots rising
        for k in range(7):
            a = k * 0.9
            G.stroke(s, G.lumpy_ellipse(0.02 + 0.12 * math.cos(a) * t, 0.42 + 0.22 * t + 0.03 * math.sin(a * 3), 0.014, 0.014, n=8, seed=99 + k),
                     M["cream"], I, cyclic=True)


PLANTS = {"ringreed": ringreed, "heliumbell": heliumbell, "frostfan": frostfan, "hexmoss": hexmoss, "butterpuff": butterpuff}


def poses(name):
    ph = [TAU * i / 8 for i in range(8)]
    idle = {"ringreed": [dict(tilt=math.sin(a), squash=1 + 0.02 * math.cos(a)) for a in ph],
            "heliumbell": [dict(bob=0.02 * math.sin(a), swell=0.5 + 0.5 * math.sin(a)) for a in ph],
            "frostfan": [dict(open=0.85 + 0.15 * math.cos(a), squash=1 + 0.02 * math.cos(a)) for a in ph],
            "hexmoss": [dict(pulse=i % 6, squash=1 + 0.02 * math.cos(a)) for i, a in enumerate(ph)],
            "butterpuff": [dict(breathe=a, squash=1 + 0.02 * math.cos(a)) for a in ph]}[name]
    react = {"ringreed": [dict(drop=0.4), dict(drop=1.0), dict(drop=1.0, tilt=0.5), dict(drop=0.3)],
             "heliumbell": [dict(stretch=1.4, swell=1.0), dict(stretch=1.8, swell=1.0), dict(stretch=1.5, swell=0.6), dict(stretch=1.1)],
             "frostfan": [dict(open=0.5), dict(open=0.05, squash=0.92), dict(open=0.05), dict(open=0.6)],
             "hexmoss": [dict(hunker=0.5), dict(hunker=1.0), dict(hunker=1.0, pulse=0), dict(hunker=0.3)],
             "butterpuff": [dict(spores=0.2, squash=0.9), dict(spores=0.6), dict(spores=1.0), dict(squash=1.03)]}[name]
    return idle, react


def render(name, pose, scale=1, seed=7):
    from meridian import fakegp
    import gp_raster as GR
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    PLANTS[name](G.Xf(d, lambda pts: [(x * SCALE, z * SCALE) for x, z in pts]), M, pose)
    return GR.render_frame(fakegp.strokes_of(d, gp), FW * scale, FH * scale, 64 * scale, (0.5, 0.0), ss=2, seed=seed)


def saturn_strip(W, H):
    """A Saturn stand-in: a butter haze with pale gold bands, the ring plane as a bright cream line with its shadow band,
    a floe band (cream ice top) at the bottom."""
    import numpy as np
    rgb = lambda h: np.array(v3.hex_rgb(h), np.float32) / 255   # noqa: E731
    bg = np.empty((H, W, 3), np.float32)
    bg[:] = rgb(P["sky"])
    y = np.arange(H)[:, None]
    x = np.arange(W)[None, :]
    for k, (y0, th, col) in enumerate(((50, 22, "offwhite"), (100, 16, "mustard"), (150, 26, "offwhite"))):
        line = y0 + 5 * np.sin(x / W * TAU * (2 + k) + k)
        band = (y > line) & (y < line + th)
        bg[band] = bg[band] * 0.5 + rgb(P[col]) * 0.5
    bg[30:33] = rgb(P["offwhite"])                                                        # the ring plane, edge-on
    bg[36:42] = bg[36:42] * 0.85 + rgb(P["teal"]) * 0.15                                   # its shadow band
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
    review._label(head, "b-157 saturn flora designs (faceless, d-101; the proposed saturn palette): ringreed, heliumbell, frostfan, hexmoss, butterpuff", 6, 8)
    rows.append(head)
    widths, sheets = [], []
    scene, ground = saturn_strip(W, 300)
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
    review._label(scene, "1x on a saturn stand-in (butter haze, pale gold bands, the ring line edge-on, a floe band) beside the surveyor (2 m)", 6, 6)
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
    per = [v3.palette_hits(s_, "saturn") for s_ in sheets]
    hits, off = min(h for h, _o in per), [c for _h, o in per for c in o]
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; saturn palette hits >= {hits * 100:.1f}% per plant {off[:3]}; faces: none", 6, 8)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " preview (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b157_saturn_plants_preview.png")
    review.write(out, img)
    print("written", out, f"ink {min(w[1] for w in outer):.2f}-{max(w[2] for w in outer):.2f} / {min(w[1] for w in inner):.2f}-{max(w[2] for w in inner):.2f}",
          f"palette {hits * 100:.1f}% {off[:3]}")


if __name__ == "__main__":
    preview(sys.argv[1])
