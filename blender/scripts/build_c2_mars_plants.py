"""B-139 (C2 Mars design prep): five faceless Mars plant designs as (d, M, pose) drawing functions, Grease Pencil strokes
in the Earth C2 manner (build_c2_earth_plants' hose stems and leaves), in the proposed Mars palette
(build_c2_mars_palette.MARS). No faces (D-101): personality through motion only. Design previews only; the rig parts and
bones follow after LEAD accepts the designs (the Earth rig set's pattern, one Mars rig set).

  rustbell       a nodding rust bell with a butterscotch lip on an olive hose stem; react: the bell swings shut like a lid
  puffpod        an olive puffball on a short neck with umber speckles; breathes; react: deflates with a dust puff
  frostcurl      ice-teal fern fronds with frost tips; uncurl by day, curl at night; react: shiver
  pipereed       three stacked olive pipes with butterscotch rings, one sound slit each at different heights (never a
                 pair: no face); segments bob out of phase as if whistling; react: a telescoping squash
  scree_creeper  an olive vine with round lichen pads hugging a salmon rock; pads ripple; react: they lift and flatten

  python -I build_c2_mars_plants.py <preview dir>      lock-free (meridian.fakegp)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_earth_plants as C  # noqa: E402  (the real gp_draw in Blender, the fake outside)
import build_c2_mars_palette as MP  # noqa: E402
from meridian import v3  # noqa: E402

G = C.G
v3.PALETTES.setdefault("mars", {k: h for k, (h, _r) in MP.MARS.items()})
P = v3.PALETTES["mars"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
hose_stem, leaf, rot = C.hose_stem, C.leaf, C.rot


def SH(h):
    return v3.shadow_of(h, "mars")


def DP(h):
    return v3.deep_of(h, "mars")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, "mars_" + name, **kw)
    out = {"ink": m("ink", fill=None)}
    for key, slot in (("olive", "green"), ("rust", "red"), ("butter", "mustard"), ("ice", "teal"), ("dust", "offwhite"),
                      ("rock", "sky"), ("umber", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
    out["stem_fill"], out["stem_sh"] = out["olive_f"], out["olive_sh"]       # build_c2_earth_plants' hose_stem / leaf keys
    out["ice_b"] = m("ice_behind", fill=P["teal"], behind=True)
    return out


def _sway(pts, a, pivot=(0.0, 0.0)):
    return rot(pts, a, pivot[0], pivot[1])


def rustbell(d, M, p):
    a, shut, sq = p.get("sway", 0.0), p.get("react", 0.0), p.get("squash", 1.0)
    S = G.Xf(d, lambda pts: [(x / math.sqrt(sq), z * sq) for x, z in _sway(pts, a)])
    stem = G.bezier((0.0, 0.0), (-0.02, 0.45), (0.10, 0.80), n=10) + G.bezier((0.10, 0.80), (0.20, 0.98), (0.30, 0.86), n=6)[1:]
    leaf(S, M, (0.0, 0.14), math.radians(155), 0.30, 0.07)
    leaf(S, M, (0.0, 0.30), math.radians(28), 0.28, 0.065)
    hose_stem(S, M, stem, 0.06, rib_every=0.16)
    tip = stem[-1]
    swing = math.radians(-12 + 70 * shut)
    bell = G.bezier((-0.10, 0.0), (-0.13, -0.15), (-0.17, -0.24), n=8) + [(-0.10, -0.28), (0.0, -0.25), (0.10, -0.28)] + \
        G.bezier((0.17, -0.24), (0.13, -0.15), (0.10, 0.0), n=8)
    B = [(tip[0] + x, tip[1] - 0.02 + z) for x, z in rot(bell, swing)]
    G.stroke(S, [(tip[0], tip[1] + 0.02), (tip[0], tip[1] - 0.04)], M["ink"], I)
    G.stroke(S, B, M["rust_f"], 0.0, cyclic=True)
    G.stroke(S, [q for q in B if q[0] < tip[0] - 0.03] + [(tip[0] - 0.03, tip[1] - 0.20)], M["rust_sh"], 0.0, cyclic=True)
    lip = [(tip[0] + x, tip[1] - 0.02 + z) for x, z in rot([(-0.17, -0.24), (-0.10, -0.28), (0.0, -0.25), (0.10, -0.28), (0.17, -0.24),
                                                             (0.15, -0.20), (0.0, -0.21), (-0.15, -0.20)], swing)]
    G.stroke(S, lip, M["butter_f"], 0.0, cyclic=True)
    for x0 in (-0.06, 0.0, 0.06):
        G.seam(S, [(tip[0] + x, tip[1] - 0.02 + z) for x, z in rot([(x0 * 0.5, -0.03), (x0, -0.19)], swing)], M["ink"])
    G.stroke(S, B, M["ink"], O, cyclic=True)
    if shut > 0.5:                                                   # shut: a drawn lid line across the mouth
        G.seam(S, [(tip[0] + x, tip[1] - 0.02 + z) for x, z in rot([(-0.16, -0.22), (0.16, -0.22)], swing)], M["ink"])


def puffpod(d, M, p):
    b, df, sq = p.get("breathe", 0.0), p.get("react", 0.0), p.get("squash", 1.0)
    a = p.get("sway", 0.0) * 0.4
    S = G.Xf(d, lambda pts: _sway(pts, a))
    hose_stem(S, M, G.bezier((0.0, 0.0), (0.02, 0.12), (0.0, 0.22), n=6), 0.07, rib_every=0.1)
    leaf(S, M, (0.0, 0.05), math.radians(165), 0.20, 0.06, veins=1)
    leaf(S, M, (0.0, 0.07), math.radians(15), 0.18, 0.055, veins=1)
    rx = 0.22 * (1 + 0.04 * b) * (1 + 0.12 * df)
    rz = 0.21 * (1 + 0.04 * b) * (1 - 0.40 * df) * sq
    cz = 0.22 + rz
    ball = G.lumpy_ellipse(0.0, cz, rx, rz, n=40, lump=0.04 + 0.05 * df, seed=81)
    G.stroke(S, ball, M["olive_f"], 0.0, cyclic=True)
    lo = [q for q in ball if q[1] < cz - 0.25 * rz]
    G.stroke(S, lo + [(0.0, cz - 0.25 * rz)], M["olive_sh"], 0.0, cyclic=True)
    G.stroke(S, [q for q in ball if q[1] < cz - 0.75 * rz and q[0] > -0.05] + [(0.05, cz - 0.75 * rz)], M["olive_dp"], 0.0, cyclic=True)
    for k, (x, z) in enumerate(((-0.13, -0.03), (0.11, -0.09), (-0.03, -0.13), (0.15, 0.07), (-0.07, 0.03), (0.04, -0.03))):   # irregular, mostly low: no flanking pair (D-101)
        G.stroke(S, G.lumpy_ellipse(x * rx / 0.22, cz + z * rz / 0.21, 0.016, 0.013, n=8, seed=90 + k), M["umber_f"], 0.0, cyclic=True)
    if df > 0.2:                                                     # wrinkles while deflated
        for k in range(3):
            x = -0.10 + 0.10 * k
            G.seam(S, [(x - 0.02, cz + 0.05), (x + 0.01, cz), (x - 0.01, cz - 0.05)], M["ink"])
    G.seam(S, G.bezier((-0.19, cz - 0.01), (-0.15, cz + 0.08), (-0.07, cz + 0.13), n=6), M["ink"])        # two short pod seams, off-centre and offset
    G.seam(S, G.bezier((0.09, cz - 0.12), (0.15, cz - 0.07), (0.18, cz + 0.01), n=6), M["ink"])        # (one centred arc between two dots read as an eye, D-101)
    G.stroke(S, ball, M["ink"], O, cyclic=True)
    t = p.get("puff")
    if t is not None:                                                # a round dust puff out of the top
        r = 0.06 + 0.07 * t
        blob = G.lumpy_ellipse(0.04 * t, cz + rz + 0.06 + 0.25 * t, r * 1.15, r, n=16, lump=0.12, seed=95)
        G.stroke(S, blob, M["dust"], I, cyclic=True)
        G.stroke(S, [q for q in blob if q[1] < cz + rz + 0.06 + 0.25 * t - 0.3 * r], M["dust_sh"], 0.0, cyclic=True)


def _frond(d, M, base, lean, curl, L, seed):
    """An ice-teal frond: a hose whose curvature grows toward the tip (curl 0 open .. 1 a tight spiral), leaflets, frost tips."""
    pts, ang, x, z = [], lean, base[0], base[1]
    n = 14
    for i in range(n):
        pts.append((x, z))
        t = i / (n - 1)
        ang -= (0.05 + 0.55 * curl * t * t) * (1 if lean > math.pi / 2 else -1)
        x, z = x + math.cos(ang) * L / n, z + math.sin(ang) * L / n
    for i in range(3, n - 2, 3):                                     # leaflets first (the frond covers their bases)
        x, z = pts[i]
        a = math.atan2(pts[i + 1][1] - z, pts[i + 1][0] - x)
        for s in (-1, 1):
            ll = 0.12 * (1 - 0.6 * i / n)
            lf = G.bezier((x, z), (x + ll * 0.55 * math.cos(a + s * 0.8) - 0.012, z + ll * 0.55 * math.sin(a + s * 0.8) + 0.02),
                          (x + ll * math.cos(a + s * 1.0), z + ll * math.sin(a + s * 1.0)), n=6)
            blade = lf + [(q[0] + 0.012 * math.cos(a), q[1] + 0.012 * math.sin(a)) for q in lf[::-1][1:-1]]
            G.stroke(d, blade, M["ice"], I, cyclic=True)
            G.stroke(d, [lf[-1], (lf[-1][0] + 0.006, lf[-1][1] + 0.004)], M["dust"], I)      # a frost tip
    out = G.hose_outline(pts, 0.05)
    G.stroke(d, out, M["ice_f"], 0.0, cyclic=True)
    G.stroke(d, G.hose_outline([(x + 0.012, z) for x, z in pts], 0.018), M["ice_sh"], 0.0, cyclic=True)
    G.seam(d, pts[2:-2], M["ink"])
    G.stroke(d, out, M["ink"], O, cyclic=True)


def frostcurl(d, M, p):
    curl, sh = p.get("curl", 0.2), p.get("react", 0.0)
    a = p.get("sway", 0.0) * 0.6 + 0.04 * sh * math.sin(p.get("k", 0) * 2.5)
    S = G.Xf(d, lambda pts: _sway(pts, a))
    G.stroke(S, G.lumpy_ellipse(0.0, 0.03, 0.12, 0.05, n=18, seed=3), M["umber"], O, cyclic=True)      # the root crown
    for k, (lean, L) in enumerate(((math.radians(118), 0.62), (math.radians(92), 0.80), (math.radians(64), 0.62))):
        _frond(S, M, (-0.05 + 0.05 * k, 0.05), lean, min(1.0, curl + 0.1 * k * curl), L, 10 + k)


def pipereed(d, M, p):
    sq, ph = p.get("squash", 1.0), p.get("phase", 0.0)
    a = p.get("sway", 0.0) * 0.5
    S = G.Xf(d, lambda pts: _sway(pts, a))
    G.stroke(S, G.lumpy_ellipse(0.0, 0.03, 0.16, 0.05, n=16, seed=5), M["umber"], O, cyclic=True)
    for k, (x, h, w, slit) in enumerate(((-0.11, 0.62, 0.09, 0.44), (0.0, 0.92, 0.10, 0.62), (0.11, 0.48, 0.08, 0.28))):
        top = 0.04 + h * sq + 0.03 * math.sin(ph + 2.1 * k)
        body = G.bezier((x - w / 2, 0.04), (x - w / 2 - 0.006, top * 0.5), (x - w / 2, top), n=6) + \
            G.lumpy_ellipse(x, top, w / 2, 0.025, n=16, seed=20 + k)[8:16] + G.bezier((x + w / 2, top), (x + w / 2 + 0.006, top * 0.5), (x + w / 2, 0.04), n=6)
        G.stroke(S, body, M["olive_f"], 0.0, cyclic=True)
        G.stroke(S, [(x + w * 0.15, 0.04), (x + w / 2, 0.04), (x + w / 2, top), (x + w * 0.15, top)], M["olive_sh"], 0.0, cyclic=True)
        for rz in (0.25, 0.55, 0.85):                                 # butterscotch rings
            zz = 0.04 + (top - 0.04) * rz
            G.stroke(S, [(x - w / 2, zz - 0.018), (x + w / 2, zz - 0.018), (x + w / 2, zz + 0.018), (x - w / 2, zz + 0.018)], M["butter"], I, cyclic=True)
        sz_ = 0.04 + (top - 0.04) * slit                              # ONE sound slit per pipe (never paired)
        G.stroke(S, [(x - w * 0.28, sz_), (x + w * 0.28, sz_ - 0.01), (x + w * 0.24, sz_ - 0.035), (x - w * 0.24, sz_ - 0.03)], M["umber_f"], 0.0, cyclic=True)
        G.seam(S, [(x - w * 0.28, sz_), (x + w * 0.28, sz_ - 0.01)], M["ink"])
        G.stroke(S, G.lumpy_ellipse(x, top, w / 2, 0.025, n=16, seed=20 + k), M["umber_f"], I, cyclic=True)   # the open top
        G.stroke(S, body, M["ink"], O, cyclic=True)


def scree_creeper(d, M, p):
    rip, lift = p.get("phase", 0.0), p.get("react", 0.0)
    rock = G.lumpy_ellipse(0.0, 0.16, 0.34, 0.18, n=36, lump=0.06, seed=31)
    rock = [(x, max(z, 0.0)) for x, z in rock]
    G.stroke(d, rock, M["rock_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in rock if q[0] > 0.05] + [(0.05, 0.0)], M["rock_sh"], 0.0, cyclic=True)
    G.hatch(d, 0.18, 0.12, M["ink"], n=3, length=0.06, spacing=0.025, angle_deg=70, seed=33)
    G.seam(d, [(-0.33, 0.12), (-0.22, 0.09), (-0.16, 0.12), (-0.10, 0.06)], M["ink"])               # cracks run in from the edge
    G.seam(d, [(0.30, 0.22), (0.24, 0.18), (0.25, 0.12)], M["ink"])
    G.stroke(d, rock, M["ink"], O, cyclic=True)
    vine = G.bezier((-0.40, 0.02), (-0.30, 0.38), (0.10, 0.36), (0.40, 0.04), n=16)
    G.stroke(d, G.hose_outline(vine, 0.03), M["olive"], O, cyclic=True)
    for k in range(7):
        x, z = vine[2 + 2 * k]
        r = 0.045 * (1 + 0.15 * math.sin(rip + 0.9 * k)) * (1 - 0.3 * lift)
        zz = z + 0.03 + 0.05 * lift * math.sin(0.9 * k)
        pad = G.lumpy_ellipse(x, zz, r * 1.2, r, n=14, lump=0.08, seed=40 + k)
        G.stroke(d, pad, M["olive_f"], 0.0, cyclic=True)
        G.stroke(d, [q for q in pad if q[1] < zz - 0.3 * r] + [(x, zz - 0.3 * r)], M["olive_dp"], 0.0, cyclic=True)
        G.seam(d, [(x - r * 0.5, zz), (x + r * 0.5, zz + 0.005)], M["ink"])
        G.stroke(d, pad, M["ink"], O, cyclic=True)


PLANTS = {"rustbell": rustbell, "puffpod": puffpod, "frostcurl": frostcurl, "pipereed": pipereed, "scree_creeper": scree_creeper}
FW, FH = 128, 192
MARS_SCALE = 1.5                     # 0.38 g: Mars flora grows taller and spindlier than Earth's (drawn 1.5x)


def poses(name):
    """The idle (8 frames on the beat) and the react (4) for one plant."""
    idle = [dict(sway=0.06 * math.sin(TAU * i / 8), squash=1 + 0.03 * math.cos(TAU * i / 8), breathe=math.cos(TAU * i / 8),
                 phase=TAU * i / 8, curl=0.25 + 0.05 * math.sin(TAU * i / 8), k=i) for i in range(8)]
    react = {"rustbell": [dict(react=0.3), dict(react=1.0, squash=0.94), dict(react=0.8), dict(react=0.2)],
             "puffpod": [dict(react=0.5, puff=0.1), dict(react=1.0, puff=0.5), dict(react=0.7, puff=0.9), dict(react=0.2, puff=1.2)],
             "frostcurl": [dict(react=1.0, k=1, curl=0.5), dict(react=1.0, k=2, curl=0.6), dict(react=1.0, k=3, curl=0.5), dict(react=0.3, k=4, curl=0.3)],
             "pipereed": [dict(squash=0.85), dict(squash=0.72, phase=1.0), dict(squash=1.08, phase=2.0), dict(squash=0.98, phase=3.0)],
             "scree_creeper": [dict(react=0.5, phase=0.5), dict(react=1.0, phase=1.0), dict(react=0.6, phase=1.5), dict(react=0.1, phase=2.0)]}[name]
    return idle, react


def render(name, pose, scale=1, seed=7):
    from meridian import fakegp
    import gp_raster as GR
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    PLANTS[name](G.Xf(d, lambda pts: [(x * MARS_SCALE, z * MARS_SCALE) for x, z in pts]), M, pose)
    return GR.render_frame(fakegp.strokes_of(d, gp), FW * scale, FH * scale, 64 * scale, (0.5, 0.0), ss=2, seed=seed)


def mars_strip(W, H):
    """A painted Mars stand-in for the design review: butterscotch sky, a salmon haze ridge, a rust ground band."""
    import numpy as np
    rgb = lambda k: np.array(v3.hex_rgb(P[k]), np.float32) / 255   # noqa: E731
    bg = np.empty((H, W, 3), np.float32)
    t = (np.arange(H) / H)[:, None, None]
    bg[:] = rgb("mustard") * (1 - 0.25 * t) + rgb("offwhite") * 0.25 * t
    x = np.arange(W)
    ridge = (H * 0.55 + 18 * np.sin(x / 140.0) + 9 * np.sin(x / 47.0 + 1)).astype(int)
    for c in range(W):
        bg[ridge[c]:, c] = rgb("sky")
    bg[H - 40:] = rgb("red")
    bg[H - 40:H - 36] = np.array(v3.hex_rgb(SH(P["red"])), np.float32) / 255
    rng = np.random.default_rng(3)
    bg *= (1 + 0.025 * rng.standard_normal((H, W, 1))).astype(np.float32)
    return bg, H - 40


def preview_one(out_dir, name):
    """One plant only (a D-101 fix re-preview): 1x on the Mars stand-in beside the surveyor, idle + react at 2x."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    W = 1960
    scene, ground = mars_strip(W, 300)
    img, w = render(name, poses(name)[0][0])
    review._over(scene, img, 40, ground - FH + 8)
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, 220, ground - fr.shape[0] + int(round(piv[1] * fr.shape[0])) + 8)
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, f"{name} at 1x beside the surveyor (re-preview after the d-101 change)", 6, 6)
    idle, react = poses(name)
    r = np.tile(review.PAPER, (FH * 2 + 30, W, 1)).astype(np.float32)
    for j, pz in enumerate(idle + react):
        im, _w = render(name, pz, scale=2, seed=11 + j)
        xx = 8 + j * (FW * 2 - 100) + (24 if j >= 8 else 0)
        if xx + FW * 2 <= W:
            review._over(r, im, xx, 24)
    review._label(r, f"{name}: idle 8 | react 4 at 2x", 6, 4)
    out = np.vstack([scene, r])
    review._label(out, __import__("time").strftime("%m-%d %H:%M") + " preview (not exported)", 2, out.shape[0] - 16)
    path = os.path.join(out_dir, f"review_b139_mars_{name}_preview.png")
    review.write(path, out)
    hits, off = v3.palette_hits(img, "mars")
    print("written", path, f"palette {hits * 100:.1f}%")


def preview(out_dir):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    W = 1960
    rows = []
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, "b-139 mars plant designs (faceless, d-101; proposed mars palette): rustbell, puffpod, frostcurl, pipereed, scree creeper; lock-free fakegp", 6, 8)
    rows.append(head)
    widths, sheets = [], []
    scene, ground = mars_strip(W, 300)
    x = 30
    for name in PLANTS:
        img, w = render(name, poses(name)[0][0])
        widths += w
        sheets.append(img)
        ph, po = v3.palette_hits(img, "mars")
        print(f"  {name}: palette {ph * 100:.1f}% {po[:3]}")
        review._over(scene, img, x, ground - FH + 8)
        review._label(scene, name, x + 10, ground + 14, scale=1)
        x += FW + 40
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, x + 20, ground - fr.shape[0] + int(round(piv[1] * fr.shape[0])) + 8)
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, "1x on a painted mars stand-in (butterscotch sky, salmon haze, rust ground) beside the surveyor (2 m)", 6, 6)
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
    per = [v3.palette_hits(s_, "mars") for s_ in sheets]                 # per plant (a flattened strip mixes neighbours)
    hits, off = min(h for h, _o in per), [c for _h, o in per for c in o]
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; mars palette hits >= {hits * 100:.1f}% per plant {off[:3]}; faces: none (one slit per pipe, never paired)", 6, 8)
    review._label(foot, "designs only: rig parts + bones (<= 6) and one mars rig set after lead accepts; biomes per plant in c2_mars_designs.md", 6, 28)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " preview (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b139_mars_plants_preview.png")
    review.write(out, img)
    print("written", out, f"ink {min(w[1] for w in outer):.2f}-{max(w[2] for w in outer):.2f} / {min(w[1] for w in inner):.2f}-{max(w[2] for w in inner):.2f}",
          f"palette {hits * 100:.1f}% {off[:3]}")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        preview_one(sys.argv[1], sys.argv[2])
    else:
        preview(sys.argv[1])
