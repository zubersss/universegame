"""B-161 (C2 Neptune design prep): the Neptune props that differ, as v3.1 prop sheets (colour + json only) in the Neptune
palette (D-148), on build_props_jupiter_v3's machinery (as the Saturn / Uranus prop modules do). The v2 sprites are replaced
under the same keys when Neptune's card opens (their _normal / _mask / _emission removed; the .meta are UNITY's, D-016).

  wind_anchor          128x192  the build anchor: a steel-indigo stake with a beacon-coral cap, three guy lines pegged into
                                the floe, a wind sock hanging limp at the top (drawn upright, D-148: UNITY leans it)
  meridian_wreck_bow   512x320  the Meridian in three ~7.5 m segments (D-148: the ship reads ~22 m whole), each lying a little
  meridian_wreck_mid   512x320  askew on the floe: a dusty beacon-coral hull with rivet seams, round wind-cyan portholes,
  meridian_wreck_stern 512x320  torn ends with storm-violet rime; the bow with its wisp-white name ring, the mid with the
                                deckhouse, the stern with the beacon mast and its coral lamp (the final beacon, a tone)

The palette has no brass (D-148): the stake and the name ring take the palette's own tones.

  python -I build_props_neptune_v3.py <review png>      lock-free design review (fakegp + numpy)
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_neptune_v3 as CN  # noqa: E402  (gp_draw through fakegp outside Blender)
import build_props_jupiter_v3 as PJ  # noqa: E402  (the sheet / export / review machinery)
from meridian import v3  # noqa: E402

G = CN.G
P = v3.PALETTES["neptune"]
O, I = G.OUTER, G.INNER
PPU, GROUND_PX = 64, 10
KEY = "props/neptune/{}"
TAU = 2 * math.pi
SEG = 3.75                                     # half a wreck segment (m): 7.5 m = 480 px inside the 512 frame


def SH(h):
    return v3.shadow_of(h, "neptune")


def DP(h):
    return v3.deep_of(h, "neptune")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, f"neptune_prop_{name}", **kw)
    out = {"ink": m("ink", fill=None)}
    for key, slot in (("wisp", "offwhite"), ("coral", "red"), ("violet", "mustard"), ("cyan", "teal"), ("sage", "green"),
                      ("blue", "sky"), ("indigo", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
        out[key + "_ln"] = m(key + "_line", fill=None, ink_hex=h)
    return out


# ---------------------------------------------------------------- the wind anchor (the Aerostat build anchor, Bible §7.9)
def wind_anchor(d, M, k=0):
    for x0 in (-0.75, 0.68):                                                              # guy lines to two pegs (a third behind)
        G.stroke(d, G.bowed_line((0.0, 1.35), (x0, 0.06), bow=0.02, n=8), M["ink"], I)
        G.stroke(d, [(x0 - 0.06, 0.0), (x0 + 0.06, 0.0), (x0 + 0.02, 0.14), (x0 - 0.02, 0.14)], M["coral"], I, cyclic=True)
    G.stroke(d, G.bowed_line((0.0, 1.35), (0.2, 0.06), bow=0.01, n=6), M["blue_ln"], I)
    G.stroke(d, G.hose_outline([(0.0, 0.0), (0.01, 0.9), (0.0, 1.8)], 0.075), M["blue_dp"], 0.0, cyclic=True)   # the stake
    G.stroke(d, G.hose_outline([(0.02, 0.05), (0.03, 0.9), (0.02, 1.75)], 0.02), M["blue_sh"], 0.0, cyclic=True)
    G.stroke(d, G.hose_outline([(0.0, 0.0), (0.01, 0.9), (0.0, 1.8)], 0.075), M["ink"], O, cyclic=True)
    for z in (0.35, 0.8, 1.25):                                                           # bands
        G.seam(d, [(-0.05, z), (0.06, z + 0.01)], M["ink"])
    G.stroke(d, [(-0.12, 0.0), (0.12, 0.0), (0.06, 0.12), (-0.06, 0.12)], M["indigo_sh"], I, cyclic=True)   # the foot plate
    cap = G.lumpy_ellipse(0.0, 1.86, 0.1, 0.09, n=16, seed=41)
    G.stroke(d, cap, M["coral_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in cap if q[0] > 0.03] + [(0.03, 1.86)], M["coral_sh"], 0.0, cyclic=True)
    G.stroke(d, cap, M["ink"], O, cyclic=True)
    sock = [(0.06, 1.8), (0.19, 1.86), (0.34, 1.0), (0.2, 0.96)]                       # the sock hanging limp (UNITY leans it)
    G.stroke(d, sock, M["wisp_f"], 0.0, cyclic=True)
    for t in (0.33, 0.66):                                                                # two coral stripes
        a = (0.05 + 0.11 * t, 1.8 - 0.65 * t)
        b = (0.12 + 0.12 * t, 1.84 - 0.66 * t)
        c = (b[0] + 0.03, b[1] - 0.1)
        e = (a[0] + 0.03, a[1] - 0.1)
        G.stroke(d, [a, b, c, e], M["coral_f"], 0.0, cyclic=True)
    G.stroke(d, sock, M["ink"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.2, 1.165, 0.045, 0.02, n=10, seed=42, rot=0.3), M["ink"], I, cyclic=True)   # its open mouth


# ---------------------------------------------------------------- the Meridian wreck (the final beacon)
def hull_profile(left, right, z_keel=0.15, z_deck=1.85):
    """A hull section's outline from x=left to x=right: `left` / `right` are 'torn', 'bow' or 'stern'."""
    rnd = random.Random(int((left == "torn") * 3 + (right == "torn") * 5 + (right == "bow") * 7))
    pts = []
    if left == "stern":                                                                   # a rounded counter stern
        pts += [(-SEG + 0.5, z_keel), (-SEG + 0.1, 0.5)] + G.bezier((-SEG + 0.1, 0.5), (-SEG - 0.15, 1.3), (-SEG + 0.05, z_deck + 0.15), n=8)[1:]
    else:                                                                                 # torn: a jagged break
        zs = [z_keel + (z_deck - z_keel) * j / 7 for j in range(8)]
        pts += [(-SEG + 0.12 + rnd.uniform(-0.12, 0.14) * (0 < j < 7), z) for j, z in enumerate(zs)]
    if right == "bow":                                                                    # the deck rising to the stem, a raked bow
        pts += G.bezier((-SEG + 0.3, z_deck), (1.6, z_deck), (2.9, z_deck + 0.25), (SEG - 0.1, z_deck + 0.55), n=14)[1:]
        pts += G.bezier((SEG - 0.1, z_deck + 0.55), (SEG - 0.05, 1.2), (SEG - 0.5, 0.5), (SEG - 1.1, z_keel), n=12)[1:]
    elif right == "torn":
        pts += [(SEG - 0.15, z_deck)]
        zs = [z_deck - (z_deck - z_keel) * j / 7 for j in range(1, 8)]
        pts += [(SEG - 0.15 + rnd.uniform(-0.14, 0.12) * (j < 7), z) for j, z in enumerate(zs, 1)]
    return pts


def hull(d, M, left, right, seed):
    """The coral hull section (the tones, the rivet seams, portholes, rime on the breaks); returns the outline."""
    out = hull_profile(left, right)
    G.stroke(d, out, M["coral_sh"], 0.0, cyclic=True)                                    # the body in the dusty mid tone
    G.stroke(d, [(x, max(z, 1.25)) for x, z in out], M["coral_f"], 0.0, cyclic=True)    # the sunlit top strake (the outline clamped)
    G.stroke(d, [(x, min(z, 0.55)) for x, z in out], M["coral_dp"], 0.0, cyclic=True)   # the bilge in shadow
    G.seam(d, [(-SEG + 0.35, 1.25), (SEG - 0.35, 1.25)], M["ink"])
    G.seam(d, [(-SEG + 0.4, 0.6), (SEG - 1.2, 0.6)], M["ink"])
    G.rivets(d, [(-SEG + 0.5 + 0.55 * j, 1.12) for j in range(13)], M["ink"])
    for j, x in enumerate((-2.2, -0.9, 0.4, 1.7)):                                      # portholes
        if (right == "bow" and x > 2.0) or (left == "stern" and x < -2.9):
            continue
        G.stroke(d, G.lumpy_ellipse(x, 0.9, 0.17, 0.17, n=16, seed=seed + j), M["cyan_f"], 0.0, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x - 0.04, 0.95, 0.06, 0.05, n=10, seed=seed + 10 + j), M["wisp_f"], 0.0, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x, 0.9, 0.2, 0.2, n=16, seed=seed + 20 + j), M["ink"], O, cyclic=True)
    for side, on in ((-1, left == "torn"), (1, right == "torn")):                         # storm-violet rime on the torn breaks
        if on:
            x = side * (SEG - 0.3)
            for z in (0.5, 1.0, 1.5):
                G.stroke(d, G.lumpy_ellipse(x, z, 0.12, 0.07, n=10, lump=0.15, seed=seed + 30 + int(z * 10)), M["violet"], I, cyclic=True)
    G.hatch(d, 0.6, 0.35, M["ink"], n=4, length=0.12, spacing=0.04, angle_deg=60, seed=seed)
    G.stroke(d, out, M["ink"], O, cyclic=True)
    return out


def tilted(d, deg, lift):
    a = math.radians(deg)
    return G.Xf(d, lambda pts: [(x * math.cos(a) - z * math.sin(a), x * math.sin(a) + z * math.cos(a) + lift) for x, z in pts])


def meridian_wreck_bow(d, M, k=0):
    T = tilted(d, 4.0, 0.22)
    hull(T, M, "torn", "bow", 61)
    G.stroke(T, G.lumpy_ellipse(2.75, 1.55, 0.32, 0.32, n=20, seed=65), M["wisp_f"], 0.0, cyclic=True)   # the name ring
    G.stroke(T, G.lumpy_ellipse(2.75, 1.55, 0.22, 0.22, n=18, seed=66), M["coral_sh"], 0.0, cyclic=True)
    for j in range(6):                                                                    # its letters, worn to dashes
        a = math.pi * (0.15 + 0.7 * j / 5)
        G.seam(T, [(2.75 + 0.27 * math.cos(a), 1.55 + 0.27 * math.sin(a)), (2.75 + 0.27 * math.cos(a + 0.12), 1.55 + 0.27 * math.sin(a + 0.12))], M["ink"])
    G.stroke(T, G.lumpy_ellipse(2.75, 1.55, 0.32, 0.32, n=20, seed=65), M["ink"], O, cyclic=True)
    G.stroke(T, G.hose_outline([(1.2, 1.85), (1.2, 2.35), (2.6, 2.3)], 0.025), M["indigo_sh"], I, cyclic=True)   # a bent rail
    G.stroke(d, G.lumpy_ellipse(0.0, 0.05, 3.4, 0.07, n=24, seed=67), M["wisp_sh"], I, cyclic=True)        # rime drift at its foot


def meridian_wreck_mid(d, M, k=0):
    T = tilted(d, -1.5, 0.2)
    hull(T, M, "torn", "torn", 71)
    house = [(-1.6, 1.82), (1.7, 1.82), (1.55, 3.0), (-1.45, 3.0)]                       # the deckhouse
    G.stroke(T, house, M["blue_sh"], 0.0, cyclic=True)
    G.stroke(T, [(-1.6, 1.82), (1.7, 1.82), (1.65, 2.2), (-1.55, 2.2)], M["blue_dp"], 0.0, cyclic=True)
    for j, x in enumerate((-0.9, 0.0, 0.9)):
        G.stroke(T, G.lumpy_ellipse(x, 2.55, 0.18, 0.18, n=16, seed=74 + j), M["cyan_f"], 0.0, cyclic=True)
        G.stroke(T, G.lumpy_ellipse(x - 0.05, 2.6, 0.06, 0.05, n=10, seed=77 + j), M["wisp_f"], 0.0, cyclic=True)
        G.stroke(T, G.lumpy_ellipse(x, 2.55, 0.21, 0.21, n=16, seed=80 + j), M["ink"], I, cyclic=True)
    G.stroke(T, [(-1.7, 3.0), (1.8, 3.0), (1.7, 3.12), (-1.6, 3.12)], M["coral_dp"], I, cyclic=True)   # the roof lip
    G.stroke(T, house, M["ink"], O, cyclic=True)
    for x in (-1.0, 0.2, 1.3):                                                            # rime on the roof
        G.stroke(T, G.lumpy_ellipse(x, 3.14, 0.22, 0.05, n=12, lump=0.12, seed=int(90 + 10 * x)), M["wisp"], I, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, 0.05, 3.5, 0.07, n=24, seed=77), M["wisp_sh"], I, cyclic=True)


def meridian_wreck_stern(d, M, k=0):
    T = tilted(d, -3.5, 0.25)
    hull(T, M, "stern", "torn", 81)
    G.stroke(T, [(-SEG + 0.6, 0.15), (-SEG + 0.9, -0.05), (-SEG + 1.3, -0.05), (-SEG + 1.2, 0.2)], M["indigo_sh"], I, cyclic=True)   # the rudder stub
    mx = -2.1
    G.stroke(T, G.hose_outline([(mx, 1.85), (mx + 0.02, 3.0), (mx, 3.85)], 0.075), M["blue_dp"], 0.0, cyclic=True)   # the beacon mast
    G.stroke(T, G.hose_outline([(mx, 1.85), (mx + 0.02, 3.0), (mx, 3.85)], 0.075), M["ink"], O, cyclic=True)
    for z in (2.4, 3.1):
        G.stroke(T, [(mx - 0.25, z), (mx + 0.25, z), (mx + 0.22, z + 0.06), (mx - 0.22, z + 0.06)], M["indigo_sh"], I, cyclic=True)   # yards
    G.stroke(T, G.lumpy_ellipse(mx, 4.08, 0.34, 0.3, n=20, seed=85), M["coral_sh"], 0.0, cyclic=True)   # the lamp's glow (a tone)
    lamp = G.lumpy_ellipse(mx, 4.08, 0.17, 0.2, n=16, seed=86)
    G.stroke(T, lamp, M["coral_f"], 0.0, cyclic=True)
    G.stroke(T, G.lumpy_ellipse(mx - 0.04, 4.13, 0.06, 0.08, n=10, seed=87), M["wisp_f"], 0.0, cyclic=True)
    G.stroke(T, [(mx - 0.2, 4.3), (mx + 0.2, 4.3), (mx + 0.12, 4.38), (mx - 0.12, 4.38)], M["indigo_sh"], I, cyclic=True)   # its cap
    G.stroke(T, lamp, M["ink"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, 0.05, 3.5, 0.07, n=24, seed=88), M["wisp_sh"], I, cyclic=True)


PROPS = {"wind_anchor": (wind_anchor, 128, 192), "meridian_wreck_bow": (meridian_wreck_bow, 512, 320),
         "meridian_wreck_mid": (meridian_wreck_mid, 512, 320), "meridian_wreck_stern": (meridian_wreck_stern, 512, 320)}


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
    """For the Neptune card: props/neptune/<prop>_color.png + .json; the v2 sprite maps removed (the .meta are UNITY's)."""
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
        raise ValueError("Neptune prop export checks: " + "; ".join(problems))
    d = os.path.join(art, "props", "neptune")
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
    """The design review: each prop at 1x with its checks, the wreck laid end to end on a Neptune floe beside the surveyor."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_c2_neptune_floes as NF
    import preview_c2_earth_rigs as PR
    if imgs is None:
        imgs, widths = render_all()
    W = 1900
    bg = np.array(v3.hex_rgb(P["sky"]), np.float32) / 255
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "b-161 neptune props that differ (the d-148 palette): the wind anchor (the sock drawn upright), the meridian wreck in three ~7.5 m segments", 6, 8)
    notes, allw = [], []
    for name in PROPS:
        sheet, meta, problems = sheet_meta(name, imgs[name])
        hits, _o = v3.palette_hits(sheet, "neptune")
        notes.append(f"{name} {meta['frame_width']}x{meta['frame_height']}: palette {hits * 100:.0f}%, json {'valid' if not problems else problems}")
        allw += widths[name]
    S, _w = NF.sheets(("ice",))
    scene = np.tile(bg, (420, W, 1))
    base = 360
    img = NF.floe(S, "ice", 27, np.random.default_rng(3))
    review._over(scene, img[:420 - (base - 24)], 10, base - 24)
    xs = 30
    for name in ("meridian_wreck_stern", "meridian_wreck_mid", "meridian_wreck_bow", "wind_anchor"):
        im = imgs[name][0]
        review._over(scene, im, xs, base - im.shape[0] + GROUND_PX)
        xs += im.shape[1] - 30 if name != "wind_anchor" else im.shape[1] + 20
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, xs, base - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, "1x on a neptune ice floe: the meridian (stern | mid | bow, ~22 m), the wind anchor, the surveyor (2 m)", 6, 6)
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    foot = np.tile(review.PAPER, (30 + 18 * len(notes), W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px", 6, 6)
    for i, t in enumerate(notes):
        review._label(foot, t, 6, 24 + 18 * i, scale=1)
    img = np.vstack([head, scene, foot])
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + (" export" if stamp_paths else " preview (not exported)"), 2, img.shape[0] - 16)
    review.write(out, img)
    print("written", out, "|", "; ".join(notes))
    return []


if __name__ == "__main__":
    main(sys.argv[1])
