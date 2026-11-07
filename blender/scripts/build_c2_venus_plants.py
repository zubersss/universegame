"""B-147 (C2 Venus design prep): five faceless Venus plant designs as (d, M, pose) drawing functions in the C2 manner
(build_c2_earth_plants' hose stems and leaves), in the Venus palette (D-134). No faces (D-101): personality through
motion only. Deck forms lean with the super-rotation wind (to +x); surface forms live by the vents. Each plant is built
from part functions (stem / head) so the rig set can cut it later. Drawn 1.6x (at 1.0x they read too small at 1x).

  puffsail     a cream gas bladder like a little sail on an olive stalk, root threads; bobs and leans; react: sags, refills
  sulphurbell  an arching olive vine hung with four sulphur bells; the bells swing out of phase; react: they close, still
  hazefern     an apricot-tinged olive frond curling into the wind; uncurls / curls on the beat; react: curls tight
  glasscoral   sea-glass teal spikes on a basalt foot over a vent-orange glow tone; the glow steps; react: they retract
  ventcap      a squat basalt chimney with a vent-orange mouth and a hinged brass lid; puffs a steam ring; react: lid shuts

  python -I build_c2_venus_plants.py <preview dir>      lock-free (meridian.fakegp)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_earth_plants as C  # noqa: E402  (the real gp_draw in Blender, the fake outside)
from meridian import v3  # noqa: E402

G = C.G
P = v3.PALETTES["venus"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
hose_stem, leaf, rot = C.hose_stem, C.leaf, C.rot
SCALE = 1.6                          # drawn 1.6x so they read beside the 2 m surveyor (Mars' are 1.5x; at 1.0x they were 0.5-0.8 m)
FW, FH = 160, 192


def SH(h):
    return v3.shadow_of(h, "venus")


def DP(h):
    return v3.deep_of(h, "venus")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, "venus_" + name, **kw)
    out = {"ink": m("ink", fill=None), "glow": m("glow", fill=P["red"], ink=False, fill_alpha=0.35)}
    for key, slot in (("olive", "green"), ("vent", "red"), ("sulphur", "mustard"), ("glass", "teal"), ("cream", "offwhite"),
                      ("haze", "sky"), ("basalt", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
    out["stem_fill"], out["stem_sh"] = out["olive_f"], out["olive_sh"]
    return out


def lean_xf(d, a, sq=1.0):
    """The wind's lean (a, radians, + to +x) about the root and a squash."""
    return G.Xf(d, lambda pts: [(x / math.sqrt(sq) + z * a, z * sq) for x, z in pts])


# ---------------------------------------------------------------- puffsail (deck)
def puffsail_stem(d, M):
    for k in (-1, 0, 1):                                                                 # root threads into the plank
        G.stroke(d, [(0.0, 0.02), (0.05 * k, -0.0), (0.09 * k, 0.015)], M["ink"], I)
    hose_stem(d, M, G.bezier((0.0, 0.0), (0.02, 0.18), (0.0, 0.36), n=7), 0.05, rib_every=0.12)
    leaf(d, M, (0.0, 0.10), math.radians(150), 0.16, 0.045, veins=1)


def puffsail_sail(d, M, fill=1.0):
    """The bladder above (0, 0): a teardrop sail, ribs, the mid tone on its lee side; fill 1 full .. 0.4 sagging."""
    w, h = 0.16 * (0.6 + 0.4 * fill), 0.42 * (0.7 + 0.3 * fill)
    droop = 0.06 * (1 - fill)
    sail = G.bezier((0.0, 0.0), (-w * 1.4, h * 0.35), (-w * 0.8, h * 0.95 - droop), (0.02, h - droop), n=10) + \
        G.bezier((0.02, h - droop), (w * 1.2, h * 0.9 - droop), (w * 1.5, h * 0.35), (0.0, 0.0), n=10)[1:]
    G.stroke(d, sail, M["cream_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in sail if q[0] > w * 0.3] + [(w * 0.3, h * 0.4)], M["cream_sh"], 0.0, cyclic=True)
    for k in (-1, 0, 1):
        G.seam(d, G.bezier((0.0, 0.03), (w * 0.6 * k, h * 0.5), (0.02 + w * 0.2 * k, h - droop - 0.02), n=6), M["ink"])
    G.stroke(d, sail, M["ink"], O, cyclic=True)


def puffsail(d, M, p):
    S = lean_xf(d, p.get("lean", 0.12) + p.get("sway", 0.0), p.get("squash", 1.0))
    puffsail_stem(S, M)
    puffsail_sail(G.Xf(S, lambda pts: [(x, z + 0.36) for x, z in pts]), M, p.get("fill", 1.0))


# ---------------------------------------------------------------- sulphurbell (deck rails)
SB_ARCH = G.bezier((0.0, 0.0), (-0.04, 0.55), (0.40, 0.72), (0.52, 0.40), n=24)


def sulphurbell_vine(d, M):
    leaf(d, M, (0.0, 0.12), math.radians(155), 0.16, 0.045, veins=1)
    hose_stem(d, M, SB_ARCH, 0.045, rib_every=0.14)
    for t in (0.45, 0.7):
        q = SB_ARCH[int(t * (len(SB_ARCH) - 1))]
        leaf(d, M, q, math.radians(60 + 40 * t), 0.12, 0.035, veins=1)


def sulphurbell_bell(d, M, shut=0.0):
    """One bell hanging from (0, 0): a sulphur cup with a cream lip; shut narrows it."""
    w = 0.07 * (1 - 0.45 * shut)
    bell = [(-0.012, 0.0), (0.012, 0.0)] + G.bezier((0.012, 0.0), (w, -0.04), (w * 1.1, -0.12), n=6)[1:] + \
        [(w * 0.4, -0.14), (-w * 0.4, -0.14)] + G.bezier((-w * 1.1, -0.12), (-w, -0.04), (-0.012, 0.0), n=6)
    G.stroke(d, bell, M["sulphur_f"], 0.0, cyclic=True)
    G.stroke(d, [(w * 1.1, -0.12), (w * 0.4, -0.14), (-w * 0.4, -0.14), (-w * 1.1, -0.12), (-w, -0.105), (w, -0.105)], M["cream_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in bell if q[0] > 0.01] + [(0.01, -0.06)], M["sulphur_sh"], 0.0, cyclic=True)
    G.stroke(d, bell, M["ink"], O, cyclic=True)


BELL_T = (0.32, 0.55, 0.75, 0.92)


def sulphurbell(d, M, p):
    S = lean_xf(d, p.get("lean", 0.06), p.get("squash", 1.0))
    sulphurbell_vine(S, M)
    for k, t in enumerate(BELL_T):
        q = SB_ARCH[int(t * (len(SB_ARCH) - 1))]
        a = 0.35 * math.sin(p.get("phase", 0.0) - 1.1 * k) * (1 - p.get("react", 0.0))
        G.stroke(S, [q, (q[0], q[1] - 0.04)], M["ink"], I)
        sulphurbell_bell(G.Xf(S, lambda pts, q=q, a=a: [(q[0] + x * math.cos(a) - z * math.sin(a), q[1] - 0.04 + x * math.sin(a) + z * math.cos(a))
                                                         for x, z in pts]), M, p.get("react", 0.0))       # swings about its stalk


# ---------------------------------------------------------------- hazefern (deck)
def leaflet(d, M, base, ang, L, W):
    """A small frond leaflet: olive with an apricot tip, a fine (interior-weight) ink edge so the colour reads at 1x."""
    c, s_ = math.cos(ang), math.sin(ang)

    def at(u, v):
        return (base[0] + c * u * L - s_ * v * W, base[1] + s_ * u * L + c * v * W)
    pts = [at(0, 0), at(0.35, 0.9), at(0.8, 0.6), at(1.0, 0.0), at(0.8, -0.6), at(0.35, -0.9)]
    G.stroke(d, pts, M["olive_f"], 0.0, cyclic=True)
    G.stroke(d, [at(0.7, 0.65), at(1.0, 0.0), at(0.7, -0.65)], M["haze_f"], 0.0, cyclic=True)
    G.stroke(d, pts, M["ink"], I, cyclic=True)


def hazefern_frond(d, M, curl, L=0.62, seed=5):
    """A frond from (0, 0) leaning up and into the wind (+x), its curvature growing toward the tip (curl 0 open .. 1 tight)."""
    pts, ang, x, z = [], math.radians(78), 0.0, 0.0
    n = 16
    for i in range(n + 1):
        pts.append((x, z))
        t = i / n
        ang -= (0.05 + 0.55 * curl * t * t) * (1 if i else 0)
        x += math.cos(ang) * L / n
        z += math.sin(ang) * L / n
    for i in range(2, n - 1, 2):                                                          # paired leaflets, apricot-tinged
        q, nxt = pts[i], pts[i + 1]
        a = math.atan2(nxt[1] - q[1], nxt[0] - q[0])
        for side in (-1, 1):
            leaflet(d, M, q, a + side * 1.1, 0.12 * (1 - 0.45 * i / n), 0.04)
    hose_stem(d, M, pts, 0.05, rib_every=0.2)
    G.stroke(d, G.lumpy_ellipse(pts[-1][0], pts[-1][1], 0.025, 0.025, n=8, seed=seed), M["haze"], I, cyclic=True)


def hazefern(d, M, p):
    S = lean_xf(d, p.get("sway", 0.0), p.get("squash", 1.0))
    G.stroke(S, G.lumpy_ellipse(0.0, 0.02, 0.08, 0.03, n=12, seed=3), M["olive_sh"], I, cyclic=True)
    for k, (dx, L, c0) in enumerate(((-0.03, 0.50, 0.0), (0.0, 0.66, 0.1), (0.03, 0.42, -0.05))):
        hazefern_frond(G.Xf(S, lambda pts, dx=dx: [(x + dx, z + 0.02) for x, z in pts]), M, min(1.0, p.get("curl", 0.3) + c0), L, seed=5 + k)


# ---------------------------------------------------------------- glasscoral (surface vents)
SPIKES = [(-0.10, 0.34, 100), (-0.04, 0.50, 94), (0.03, 0.42, 86), (0.09, 0.28, 74), (0.0, 0.22, 120)]


def glasscoral_foot(d, M, glow=0.5):
    G.stroke(d, G.lumpy_ellipse(0.0, 0.05, 0.22 + 0.04 * glow, 0.10 + 0.02 * glow, n=18, lump=0.06, seed=11), M["glow"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, 0.03, 0.15, 0.05, n=16, lump=0.05, seed=12), M["basalt"], O, cyclic=True)
    G.specks(d, [(-0.06, 0.03), (0.07, 0.04)], M["ink"])


def glasscoral_spike(d, M, x, L, deg, k):
    """One sea-glass spike from (x, 0.04): a narrow faceted shard, a light facet, the vent glow at its base."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    base = (x, 0.04)

    def at(u, v):
        return (base[0] + c * u * L - s * v * 0.06, base[1] + s * u * L + c * v * 0.06)          # wide enough for the glass to show
    sh = [at(0, -1), at(0.8, -0.8), at(1.0, 0.0), at(0.8, 0.8), at(0, 1)]
    G.stroke(d, sh, M["glass_f"], 0.0, cyclic=True)
    G.stroke(d, [at(0, 0.1), at(0.8, 0.1), at(1.0, 0.0), at(0.8, 0.8), at(0, 1)], M["glass_sh"], 0.0, cyclic=True)
    G.stroke(d, [at(0.0, -1), at(0.25, -0.95), at(0.25, 0.95), at(0.0, 1)], M["vent_f"], 0.0, cyclic=True)    # the glow at its base
    G.seam(d, [at(0.25, 0.0), at(0.85, 0.05)], M["ink"])
    G.stroke(d, sh, M["ink"], O, cyclic=True)


def glasscoral(d, M, p):
    S = lean_xf(d, 0.0, p.get("squash", 1.0))
    glasscoral_foot(S, M, p.get("glow", 0.5))
    shrink = 1.0 - 0.45 * p.get("react", 0.0)
    for k, (x, L, deg) in enumerate(SPIKES):
        glasscoral_spike(S, M, x, L * shrink, deg + 3 * math.sin(p.get("phase", 0.0) + k), k)


# ---------------------------------------------------------------- ventcap (surface)
def ventcap_chimney(d, M):
    ch = [(-0.16, 0.0), (0.16, 0.0), (0.10, 0.30), (-0.10, 0.30)]
    G.stroke(d, ch, M["basalt_f"], 0.0, cyclic=True)
    G.stroke(d, [(0.04, 0.0), (0.16, 0.0), (0.10, 0.30), (0.03, 0.30)], M["basalt_dp"], 0.0, cyclic=True)
    for z in (0.08, 0.18):
        G.seam(d, [(-0.15 + 0.2 * z, z), (0.15 - 0.2 * z, z)], M["ink"])
    G.stroke(d, G.lumpy_ellipse(0.0, 0.30, 0.10, 0.03, n=14, seed=21), M["vent"], I, cyclic=True)             # the glowing mouth
    G.stroke(d, G.lumpy_ellipse(0.0, 0.302, 0.06, 0.015, n=10, seed=22), M["sulphur_f"], 0.0, cyclic=True)
    G.stroke(d, ch, M["ink"], O, cyclic=True)


def ventcap_lid(d, M, open_=1.0):
    """The hinged brass lid on the mouth's left rim (0, 0 = the hinge): open 1 stands up, 0 shut flat."""
    a = math.radians(10 + 95 * open_)
    lid = [(0.0, 0.0), (0.2 * math.cos(a), 0.2 * math.sin(a)), (0.2 * math.cos(a) - 0.03 * math.sin(a), 0.2 * math.sin(a) + 0.03 * math.cos(a)),
           (-0.03 * math.sin(a), 0.03 * math.cos(a))]
    G.stroke(d, lid, M["sulphur"], I, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, 0.0, 0.018, 0.018, n=8, seed=23), M["basalt"], I, cyclic=True)


def ventcap(d, M, p):
    S = lean_xf(d, 0.0, p.get("squash", 1.0))
    ventcap_chimney(S, M)
    ventcap_lid(G.Xf(S, lambda pts: [(x - 0.10, z + 0.30) for x, z in pts]), M, 1.0 - p.get("react", 0.0))
    t = p.get("puff")
    if t is not None:                                                                     # a cream steam ring rising
        r = 0.05 + 0.06 * t
        ring = G.lumpy_ellipse(0.02 * t, 0.42 + 0.30 * t, r * 1.4, r * 0.6, n=16, lump=0.1, seed=24)
        G.stroke(S, ring, M["cream"], I, cyclic=True)
        G.stroke(S, G.lumpy_ellipse(0.02 * t, 0.42 + 0.30 * t, r * 0.7, r * 0.25, n=12, seed=25), M["cream_sh"], 0.0, cyclic=True)


PLANTS = {"puffsail": puffsail, "sulphurbell": sulphurbell, "hazefern": hazefern, "glasscoral": glasscoral, "ventcap": ventcap}


def poses(name):
    ph = [TAU * i / 8 for i in range(8)]
    idle = {"puffsail": [dict(sway=0.05 * math.sin(a), squash=1 + 0.03 * math.cos(a), fill=0.95 + 0.05 * math.cos(a)) for a in ph],
            "sulphurbell": [dict(phase=a) for a in ph],
            "hazefern": [dict(curl=0.3 + 0.25 * math.sin(a), sway=0.04 * math.sin(a)) for a in ph],
            "glasscoral": [dict(glow=0.5 + 0.5 * math.sin(a), phase=a) for a in ph],
            "ventcap": [dict(puff=(i % 4) / 4.0 if i < 8 else None, squash=1 + 0.02 * math.cos(a)) for i, a in enumerate(ph)]}[name]
    react = {"puffsail": [dict(fill=0.7, squash=0.95), dict(fill=0.45, squash=0.9), dict(fill=0.7), dict(fill=1.0, squash=1.04)],
             "sulphurbell": [dict(react=0.5, phase=0.5), dict(react=1.0), dict(react=1.0), dict(react=0.3, phase=1.0)],
             "hazefern": [dict(curl=0.7), dict(curl=1.0), dict(curl=1.0, sway=0.02), dict(curl=0.6)],
             "glasscoral": [dict(react=0.5, glow=1.0), dict(react=1.0, glow=0.8), dict(react=0.8, glow=0.5), dict(react=0.2, glow=0.5)],
             "ventcap": [dict(react=0.6, squash=0.95), dict(react=1.0, squash=0.9), dict(react=1.0), dict(react=0.3, puff=0.1)]}[name]
    return idle, react


def render(name, pose, scale=1, seed=7):
    from meridian import fakegp
    import gp_raster as GR
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    PLANTS[name](G.Xf(d, lambda pts: [(x * SCALE, z * SCALE) for x, z in pts]), M, pose)
    return GR.render_frame(fakegp.strokes_of(d, gp), FW * scale, FH * scale, 64 * scale, (0.5, 0.0), ss=2, seed=seed)


def venus_strip(W, H):
    """A Venus stand-in: an apricot haze over cream, a deck plank band (the cloud deck)."""
    import numpy as np
    rgb = lambda h: np.array(v3.hex_rgb(h), np.float32) / 255   # noqa: E731
    bg = np.empty((H, W, 3), np.float32)
    t = (np.arange(H) / H)[:, None, None]
    bg[:] = rgb(P["sky"]) * (1 - 0.45 * t) + rgb(P["offwhite"]) * 0.45 * t
    bg[H - 40:] = rgb(SH(P["mustard"]))
    for x in range(0, W, 48):
        bg[H - 40:, x:x + 2] = rgb(P["brown"])
    bg[H - 40:H - 36] = rgb(P["brown"])
    rng = np.random.default_rng(3)
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
    review._label(head, "b-147 venus plant designs (faceless, d-101; the venus palette d-134): puffsail, sulphurbell, hazefern (deck), glasscoral, ventcap (surface)", 6, 8)
    rows.append(head)
    widths, sheets = [], []
    scene, ground = venus_strip(W, 300)
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
    review._label(scene, "1x on a venus stand-in (apricot haze over cream, a deck plank band) beside the surveyor (2 m)", 6, 6)
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
    per = [v3.palette_hits(s_, "venus", tints=[("red", 0.35)]) for s_ in sheets]
    hits, off = min(h for h, _o in per), [c for _h, o in per for c in o]
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; venus palette hits >= {hits * 100:.1f}% per plant {off[:3]}; faces: none", 6, 8)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " preview (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b147_venus_plants_preview.png")
    review.write(out, img)
    print("written", out, f"ink {min(w[1] for w in outer):.2f}-{max(w[2] for w in outer):.2f} / {min(w[1] for w in inner):.2f}-{max(w[2] for w in inner):.2f}",
          f"palette {hits * 100:.1f}% {off[:3]}")


if __name__ == "__main__":
    preview(sys.argv[1])
