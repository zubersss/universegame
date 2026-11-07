"""B-158 (C2 Uranus design prep): the Uranus props that differ, as v3.1 prop sheets (colour + json only) in the Uranus palette
(D-142), on build_props_jupiter_v3's machinery (as build_props_saturn_v3 does). The v2 models are replaced under the same
keys when Uranus's card opens; they take UNITY's season tint (D-142), not three drawings.

  umbrella_platform  192x176  a diamond-rain catcher: a ribbed ice-white canopy on a mast over a float, caught diamonds
                              glinting on the canopy, a rim gutter
  tilted_derelict    224x160  the Uranus beacon on a Meridian hull lying tilted like the planet: slate plating, frost on the
                              upturned side, a round window, the ember beacon lamp (a tone: the one warm accent)

  python -I build_props_uranus_v3.py <review png>      lock-free design review (fakegp + numpy)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_uranus_v3 as CU  # noqa: E402  (gp_draw through fakegp outside Blender)
import build_props_jupiter_v3 as PJ  # noqa: E402  (the sheet / export / review machinery)
from meridian import v3  # noqa: E402

G = CU.G
P = v3.PALETTES["uranus"]
O, I = G.OUTER, G.INNER
PPU, GROUND_PX = 64, 10
KEY = "props/uranus/{}"
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "uranus")


def DP(h):
    return v3.deep_of(h, "uranus")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, f"uranus_prop_{name}", **kw)
    out = {"ink": m("ink", fill=None)}
    for key, slot in (("ice", "offwhite"), ("ember", "red"), ("sage", "mustard"), ("cyan", "teal"), ("fog", "sky"), ("slate", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
    return out


def umbrella_platform(d, M, k=0):
    G.stroke(d, [(-1.1, 0.0), (1.1, 0.0), (0.95, 0.3), (-0.95, 0.3)], M["cyan_sh"], O, cyclic=True)        # the float
    G.stroke(d, G.hose_outline([(0.0, 0.3), (0.0, 1.9)], 0.06), M["sage"], I, cyclic=True)                 # the mast
    canopy = G.bezier((-1.35, 1.75), (-0.7, 2.55), (0.0, 2.6), n=10) + G.bezier((0.0, 2.6), (0.7, 2.55), (1.35, 1.75), n=10)[1:] + \
        G.bezier((1.35, 1.75), (0.0, 1.95), (-1.35, 1.75), n=10)[1:-1]
    G.stroke(d, canopy, M["ice_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in canopy if q[0] > 0.45] + [(0.45, 2.2)], M["fog_sh"], 0.0, cyclic=True)
    for x in (-0.9, -0.45, 0.0, 0.45, 0.9):                                                # the ribs
        G.seam(d, [(0.0, 2.58), (x * 1.2, 1.85 + 0.05 * abs(x))], M["ink"])
    G.stroke(d, canopy, M["ink"], O, cyclic=True)
    G.stroke(d, G.hose_outline(G.bezier((-1.35, 1.75), (0.0, 1.95), (1.35, 1.75), n=10), 0.035), M["cyan"], I, cyclic=True)   # the rim gutter
    for j, (x, z) in enumerate(((-0.6, 2.3), (0.3, 2.42), (0.8, 2.15), (-0.2, 2.45))):     # caught diamonds
        pts = [(x, z + 0.06), (x + 0.05, z), (x, z - 0.06), (x - 0.05, z)]
        G.stroke(d, pts, M["ice"], I, cyclic=True)
    G.rivets(d, [(-0.7, 0.15), (0.0, 0.15), (0.7, 0.15)], M["ink"])


def tilted_derelict(d, M, k=0):
    a = math.radians(-24)                                                                   # the hull lies tilted, like the planet
    T = G.Xf(d, lambda pts: [(x * math.cos(a) - z * math.sin(a) + 0.2, x * math.sin(a) + z * math.cos(a) + 0.55) for x, z in pts])
    hull = G.lumpy_ellipse(0.0, 0.3, 1.5, 0.55, n=40, lump=0.01, seed=31)
    G.stroke(T, hull, M["slate_sh"], 0.0, cyclic=True)
    G.stroke(T, [q for q in hull if q[1] > 0.55] + [(0.0, 0.55)], M["ice_f"], 0.0, cyclic=True)           # frost on the upturned side
    for x in (-0.8, -0.2, 0.4, 1.0):
        G.seam(T, [(x, -0.2), (x + 0.03, 0.75)], M["ink"])
    G.stroke(T, G.lumpy_ellipse(0.55, 0.3, 0.17, 0.17, n=18, seed=33), M["cyan_f"], 0.0, cyclic=True)    # a round window
    G.stroke(T, G.lumpy_ellipse(0.55, 0.3, 0.19, 0.19, n=18, seed=34), M["ink"], O, cyclic=True)
    G.stroke(T, hull, M["ink"], O, cyclic=True)
    G.stroke(T, G.hose_outline([(-0.9, 0.8), (-0.9, 1.5)], 0.04), M["sage"], I, cyclic=True)             # the beacon mast
    G.stroke(T, G.lumpy_ellipse(-0.9, 1.62, 0.16, 0.16, n=14, seed=35), M["ember_sh"], 0.0, cyclic=True)  # its glow (a tone)
    G.stroke(T, G.lumpy_ellipse(-0.9, 1.62, 0.08, 0.08, n=10, seed=36), M["ember"], I, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, 0.0, 1.5, 0.08, n=20, seed=37), M["fog_sh"], I, cyclic=True)        # its resting frost drift


PROPS = {"umbrella_platform": (umbrella_platform, 192, 176), "tilted_derelict": (tilted_derelict, 224, 160)}


def pivot_of(name):
    _fn, fw, fh = PROPS[name]
    return (0.5, GROUND_PX / fh)


def _with_this(fn):
    def run(*a, **kw):
        keep = (PJ.PROPS, PJ.KEY, PJ.mats, PJ.pivot_of, PJ.P)
        PJ.PROPS, PJ.KEY, PJ.mats, PJ.pivot_of, PJ.P = PROPS, KEY, mats, pivot_of, P
        try:
            return fn(*a, **kw)
        finally:
            PJ.PROPS, PJ.KEY, PJ.mats, PJ.pivot_of, PJ.P = keep
    return run


render_prop = _with_this(PJ.render_prop)
render_all = _with_this(PJ.render_all)
sheet_meta = _with_this(PJ.sheet_meta)


def export(art, imgs=None, names=None):
    """For the Uranus card: props/uranus/<prop>_color.png + .json; the v2 model files removed (the .meta are UNITY's)."""
    from meridian import pngio
    names = list(names or PROPS)
    if imgs is None:
        imgs, _w = render_all()
    built, problems = [], []
    for name in names:
        sheet, meta, p = sheet_meta(name, imgs[name])
        problems += [f"{name}: {x}" for x in p]
        built.append((name, sheet, meta))
    if problems:
        raise ValueError("Uranus prop export checks: " + "; ".join(problems))
    d = os.path.join(art, "props", "uranus")
    os.makedirs(d, exist_ok=True)
    out = []
    for name, sheet, meta in built:
        n = pngio.write_png(os.path.join(d, name + "_color.png"), sheet)
        with open(os.path.join(d, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((meta["key"], sheet.shape[1], sheet.shape[0], n))
    removed = [os.path.join(d, n_ + s) for n_ in names for s in (".glb", "_normal.png", "_mask.png", "_emission.png")
               if os.path.isfile(os.path.join(d, n_ + s))]
    for p in removed:
        os.remove(p)
    return out, {}, removed


def main(out, imgs=None, widths=None, stamp_paths=()):
    """The design review: each prop at 2x with its checks, both at 1x on a Uranus ice floe beside the surveyor."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_c2_uranus_floes as UF
    import preview_c2_earth_rigs as PR
    if imgs is None:
        imgs, widths = render_all()
    W = 1500
    bg = np.array(v3.hex_rgb(P["sky"]), np.float32) / 255
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "b-158 uranus props that differ (the d-142 palette): the umbrella platform (a diamond-rain catcher), the tilted derelict (the beacon)", 6, 8)
    r = np.tile(bg, (2 * max(fh for _f, _w, fh in PROPS.values()) + 40, W, 1))
    x, notes, allw = 10, [], []
    for name in PROPS:
        sheet, meta, problems = sheet_meta(name, imgs[name])
        hits, _o = v3.palette_hits(sheet, "uranus")
        notes.append(f"{name} {meta['frame_width']}x{meta['frame_height']}: palette {hits * 100:.0f}%, json {'valid' if not problems else problems}")
        allw += widths[name]
        review._over(r, np.repeat(np.repeat(imgs[name][0], 2, 0), 2, 1), x, 30)
        review._label(r, name, x, 8, scale=1)
        x += PROPS[name][1] * 2 + 30
    S, _w = UF.sheets(("ice",))
    scene = np.tile(bg, (300, W, 1))
    base = 230
    img = UF.floe(S, "ice", 18, np.random.default_rng(3))
    review._over(scene, img[:300 - (base - 24)], 20, base - 24)
    xs = 120
    for name in PROPS:
        im = imgs[name][0]
        review._over(scene, im, xs, base - im.shape[0] + GROUND_PX)
        xs += im.shape[1] + 120
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, xs, base - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, "1x on a uranus ice floe beside the surveyor (2 m)", 6, 6)
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    foot = np.tile(review.PAPER, (30 + 18 * len(notes), W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px", 6, 6)
    for i, t in enumerate(notes):
        review._label(foot, t, 6, 24 + 18 * i, scale=1)
    img = np.vstack([head, r, scene, foot])
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + (" export" if stamp_paths else " preview (not exported)"), 2, img.shape[0] - 16)
    review.write(out, img)
    print("written", out, "|", "; ".join(notes))
    return []


if __name__ == "__main__":
    main(sys.argv[1])
