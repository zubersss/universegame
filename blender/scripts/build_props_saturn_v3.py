"""B-157 (C2 Saturn design prep): the Saturn props that differ + the ring chunks, as v3.1 prop sheets (colour + json only) in
the proposed Saturn palette (registered with setdefault until LEAD accepts it), on build_props_jupiter_v3's API (PROPS, KEY,
render_all, sheet_meta, export, main). The v2 models (ring_rig, helium_trap, hexagon_wall_marker) are replaced under the
same keys when Saturn's card opens.

  ring_chunk_a / _b / _c  96x80 / 80x72 / 64x56  tumbling ice-and-rock pieces for the top-down ring-mining lanes (UNITY's
                                                 space view): cream ice, slate rock inclusions, ring-ice edges; pivot at
                                                 the centre (they float)
  ring_rig                192x192  the ring-mining rig with the Saturn beacon: a brass gantry on a float, a pale-gold dish, a
                                   salmon beacon lamp (a tone)
  helium_trap             96x128   a Deck 2-3 condensate trap: a cream gasbag over a brass funnel, a pale-gold drip, a tank
  hexagon_wall_marker     64x128   a ring-ice blue-grey buoy marking a wind-wall: a tall float with cream hoops, a pennant

  python -I build_props_saturn_v3.py <review png>      lock-free design review (fakegp + numpy)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_saturn_v3 as CS  # noqa: E402  (registers the proposed palette; gp_draw through fakegp outside Blender)
import build_props_jupiter_v3 as PJ  # noqa: E402  (the sheet / export / review machinery)
from meridian import fakegp, v3  # noqa: E402
import gp_raster as GR  # noqa: E402

G = CS.G
P = v3.PALETTES["saturn"]
O, I = G.OUTER, G.INNER
PPU, GROUND_PX = 64, 10
KEY = "props/saturn/{}"
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "saturn")


def DP(h):
    return v3.deep_of(h, "saturn")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, f"saturn_prop_{name}", **kw)
    out = {"ink": m("ink", fill=None)}
    for key, slot in (("gold", "mustard"), ("salmon", "red"), ("cream", "offwhite"), ("ice", "teal"), ("butter", "sky"), ("slate", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
    return out


def chunk(seed, rx, rz):
    def draw(d, M, k=0):
        body = G.lumpy_ellipse(0.0, 0.0, rx, rz, n=12, lump=0.18, seed=seed)                 # an angular lump of ice
        G.stroke(d, body, M["cream_f"], 0.0, cyclic=True)
        G.stroke(d, [q for q in body if q[1] < -rz * 0.2] + [(0.0, -rz * 0.2)], M["ice_f"], 0.0, cyclic=True)    # the ring-ice side
        for j in range(3):                                                                   # slate rock inclusions
            a = seed + j * 2.1
            G.stroke(d, G.lumpy_ellipse(rx * 0.45 * math.cos(a), rz * 0.4 * math.sin(a), rx * 0.18, rz * 0.16, n=10, lump=0.2, seed=seed + j), M["slate_f"], 0.0, cyclic=True)
        G.seam(d, [(-rx * 0.6, rz * 0.2), (rx * 0.1, rz * 0.35), (rx * 0.5, -rz * 0.1)], M["ink"])
        G.stroke(d, body, M["ink"], O, cyclic=True)
    return draw


def ring_rig(d, M, k=0):
    G.stroke(d, [(-1.2, 0.0), (1.2, 0.0), (1.0, 0.35), (-1.0, 0.35)], M["ice_sh"], O, cyclic=True)   # the float
    for x in (-0.8, 0.8):                                                                  # the gantry legs
        G.stroke(d, G.hose_outline([(x, 0.35), (x * 0.5, 1.9)], 0.06), M["gold"], I, cyclic=True)
    G.stroke(d, G.hose_outline([(-0.4, 1.9), (0.4, 1.9)], 0.06), M["gold"], I, cyclic=True)
    for z in (0.8, 1.35):
        G.stroke(d, G.hose_outline([(-0.7 + 0.1 * (z - 0.8) * 3, z), (0.7 - 0.1 * (z - 0.8) * 3, z)], 0.035), M["gold_sh"], I, cyclic=True)
    dish = G.bezier((-0.7, 2.25), (0.0, 1.85), (0.7, 2.25), n=10) + [(0.6, 2.32), (-0.6, 2.32)]
    G.stroke(d, dish, M["gold_f"], 0.0, cyclic=True)                                       # the dish
    G.stroke(d, dish, M["ink"], O, cyclic=True)
    G.stroke(d, [(0.0, 2.0), (0.0, 2.4)], M["ink"], I)
    G.stroke(d, G.lumpy_ellipse(0.0, 2.45, 0.11, 0.11, n=12, seed=61), M["salmon"], I, cyclic=True)   # the beacon lamp (a tone)
    G.rivets(d, [(-0.9, 0.18), (0.0, 0.18), (0.9, 0.18)], M["ink"])


def helium_trap(d, M, k=0):
    bag = G.lumpy_ellipse(0.0, 1.35, 0.55, 0.42, n=30, lump=0.02, seed=71)
    G.stroke(d, bag, M["cream_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in bag if q[0] > 0.18] + [(0.18, 1.35)], M["cream_sh"], 0.0, cyclic=True)
    for t in (-0.5, 0.0, 0.5):
        G.seam(d, G.bezier((t * 0.5, 0.98), (t * 0.9, 1.35), (t * 0.5, 1.74), n=6), M["ink"])
    G.stroke(d, bag, M["ink"], O, cyclic=True)
    G.stroke(d, [(-0.45, 0.95), (0.45, 0.95), (0.1, 0.45), (-0.1, 0.45)], M["gold"], O, cyclic=True)   # the brass funnel
    G.stroke(d, G.lumpy_ellipse(0.0, 0.36, 0.05, 0.07, n=10, seed=72), M["gold_f"], 0.0, cyclic=True)   # a pale-gold drip
    G.stroke(d, [(-0.3, 0.0), (0.3, 0.0), (0.3, 0.28), (-0.3, 0.28)], M["slate_sh"], O, cyclic=True)   # the tank
    G.rivets(d, [(-0.18, 0.14), (0.18, 0.14)], M["ink"])


def hexagon_wall_marker(d, M, k=0):
    body = [(-0.18, 0.0), (0.18, 0.0), (0.12, 1.25), (-0.12, 1.25)]
    G.stroke(d, body, M["ice_f"], 0.0, cyclic=True)
    G.stroke(d, [(0.04, 0.0), (0.18, 0.0), (0.12, 1.25), (0.03, 1.25)], M["ice_sh"], 0.0, cyclic=True)
    for z in (0.3, 0.7, 1.05):
        G.stroke(d, [(-0.17 + 0.05 * z, z - 0.04), (0.17 - 0.05 * z, z - 0.04), (0.17 - 0.05 * z, z + 0.04), (-0.17 + 0.05 * z, z + 0.04)], M["cream_f"], 0.0, cyclic=True)
    G.stroke(d, body, M["ink"], O, cyclic=True)
    G.stroke(d, [(0.0, 1.25), (0.0, 1.62)], M["ink"], I)
    G.stroke(d, [(0.0, 1.6), (0.32, 1.52), (0.0, 1.44)], M["salmon"], I, cyclic=True)        # the pennant
    G.stroke(d, G.lumpy_ellipse(0.0, 0.0, 0.3, 0.06, n=14, seed=81), M["slate_sh"], I, cyclic=True)   # the float's rim


PROPS = {"ring_chunk_a": (chunk(11, 0.62, 0.48), 96, 80), "ring_chunk_b": (chunk(23, 0.5, 0.42), 80, 72), "ring_chunk_c": (chunk(37, 0.38, 0.32), 64, 56),
         "ring_rig": (ring_rig, 192, 192), "helium_trap": (helium_trap, 96, 128), "hexagon_wall_marker": (hexagon_wall_marker, 64, 128)}
FLOAT = ("ring_chunk_a", "ring_chunk_b", "ring_chunk_c")


def pivot_of(name):
    _fn, fw, fh = PROPS[name]
    return (0.5, 0.5) if name in FLOAT else (0.5, GROUND_PX / fh)


def _with_this(fn):
    """Run one of build_props_jupiter_v3's machinery functions against this module's PROPS / KEY / mats / pivot / palette."""
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


def sheet_meta(name, frames):
    sheet, meta, problems = _with_this(PJ.sheet_meta)(name, frames)
    if name in FLOAT:
        meta["ground_line_px"] = 0
        meta["note"] = "one static frame; floats (space view / the ring lanes): the pivot at the centre"
    return sheet, meta, problems


def export(art, imgs=None, names=None):
    """For the Saturn card: props/saturn/<prop>_color.png + .json; the v2 model files removed (the .meta are UNITY's)."""
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
        raise ValueError("Saturn prop export checks: " + "; ".join(problems))
    d = os.path.join(art, "props", "saturn")
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
    """The design review: each prop at 2x with its checks (palette Saturn), all at 1x on a Saturn ice floe beside the surveyor."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_c2_saturn_floes as SF
    import preview_c2_earth_rigs as PR
    if imgs is None:
        imgs, widths = render_all()
    W = 1700
    bg = np.array(v3.hex_rgb(P["sky"]), np.float32) / 255
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "b-157 saturn props (the proposed palette): three ring chunks (floating), the ring rig, the helium trap, the hexagon wall marker", 6, 8)
    r = np.tile(bg, (2 * max(fh for _f, _w, fh in PROPS.values()) + 40, W, 1))
    x, notes, allw = 10, [], []
    for name in PROPS:
        sheet, meta, problems = sheet_meta(name, imgs[name])
        hits, _o = v3.palette_hits(sheet, "saturn")
        notes.append(f"{name} {meta['frame_width']}x{meta['frame_height']}: palette {hits * 100:.0f}%, json {'valid' if not problems else problems}")
        allw += widths[name]
        review._over(r, np.repeat(np.repeat(imgs[name][0], 2, 0), 2, 1), x, 30)
        review._label(r, name, x, 8, scale=1)
        x += PROPS[name][1] * 2 + 20
    S, _w = SF.sheets(("ice",))
    scene = np.tile(bg, (300, W, 1))
    base = 230
    img = SF.floe(S, "ice", 22, np.random.default_rng(3))
    review._over(scene, img[:300 - (base - 24)], 20, base - 24)
    xs = 80
    for name in PROPS:
        im = imgs[name][0]
        y = base - im.shape[0] + GROUND_PX if name not in FLOAT else base - 150 - im.shape[0] // 2
        review._over(scene, im, xs, y)
        xs += im.shape[1] + 70
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, xs, base - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, "1x on a saturn ice floe beside the surveyor (2 m); the ring chunks float", 6, 6)
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
