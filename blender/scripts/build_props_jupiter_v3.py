"""B-155 (C2 Jupiter design prep): the Jupiter props that differ, as v3.1 prop sheets (colour + json only) in the Jupiter
palette (D-137), on the build_props_mercury_v3 / build_props_venus_v3 API (PROPS, KEY, render_all, sheet_meta, export,
main). Each replaces the v2 model under its key when Jupiter's card opens.

  husk_tortoise  176x112  the Ballast tortoise's empty shell (build_creatures_jupiter_v3.SHELL): dulled brick plates, a
                          chipped cream marginal band, the ballast bladders deflated and draped over the rim, the head
                          opening dark, frost crusts; its json carries the shell's top as "stand_line" (UNITY's walkable top)
  derelict_pod   128x112  a buoyant Meridian expedition pod: rust plating on a rounded capsule, a cream gasbag patch on top,
                          one round festoon window, rivets, a torn panel
  beacon_vault   192x160  the radiation-fried vault round the Jupiter beacon: scorched rust plating, cream / umber warning
                          stripes, a brass round hatch, a festoon interior glow through a slot (a tone, no emission)

  python -I build_props_jupiter_v3.py <review png>      lock-free design review (fakegp + numpy)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_jupiter_v3 as CJ  # noqa: E402  (gp_draw through fakegp outside Blender)
from meridian import fakegp, v3  # noqa: E402
import gp_raster as GR  # noqa: E402

G = CJ.G
P = v3.PALETTES["jupiter"]
O, I = G.OUTER, G.INNER
PPU = 64
GROUND_PX = 10
KEY = "props/jupiter/{}"
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "jupiter")


def DP(h):
    return v3.deep_of(h, "jupiter")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, f"jupiter_prop_{name}", **kw)
    out = {"ink": m("ink", fill=None)}
    for key, slot in (("rust", "mustard"), ("brick", "red"), ("cream", "offwhite"), ("festoon", "teal"), ("tan", "sky"), ("umber", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
    return out


def shell_top(n=24):
    """The husk's walkable top: the dome's upper edge (m, relative to the pivot on the shell's base)."""
    cx, cz, rx, rz = CJ.SHELL
    base = cz - rz * 0.55
    return [(round(cx + rx * math.cos(a), 3), round(cz + rz * math.sin(a) - base, 3)) for a in [math.pi * (1 - k / (n - 1)) for k in range(n)]]


def husk_tortoise(d, M, k=0):
    cx, cz, rx, rz = CJ.SHELL
    base = cz - rz * 0.55
    X = G.Xf(d, lambda pts: [(x, z - base) for x, z in pts])                              # the shell's base on the ground line
    dome = [(x, max(z, base)) for x, z in G.lumpy_ellipse(cx, cz, rx, rz, n=48, lump=0.015, seed=1)]
    G.stroke(X, dome, M["brick_sh"], 0.0, cyclic=True)                                    # dulled: the mid tone all over
    G.stroke(X, [q for q in dome if q[0] > rx * 0.35] + [(rx * 0.35, cz)], M["brick_dp"], 0.0, cyclic=True)
    for x in (-0.45, 0.0, 0.45):
        hexa = [(x + 0.2 * math.cos(a), cz + 0.26 + 0.14 * math.sin(a)) for a in [j * TAU / 6 for j in range(6)]]
        G.stroke(X, hexa, M["brick_dp"], 0.0, cyclic=True)
        G.stroke(X, hexa, M["ink"], I, cyclic=True)
    for x in (-0.68, -0.23, 0.23, 0.68):
        G.stroke(X, [(x + 0.2 * math.cos(a), cz - 0.06 + 0.13 * math.sin(a)) for a in [j * TAU / 6 for j in range(6)]], M["ink"], I, cyclic=True)
    band = G.bezier((-rx * 0.97, cz - rz * 0.40), (0.0, cz - rz * 0.62), (rx * 0.97, cz - rz * 0.40), n=16)
    for j in range(0, 15, 3):                                                              # the marginal band, chipped
        G.stroke(X, G.hose_outline(band[j:j + 3], 0.05), M["cream_sh"], 0.0, cyclic=True)
    G.stroke(X, G.lumpy_ellipse(rx * 0.92, cz - 0.12, 0.13, 0.18, n=14, seed=4), M["umber_dp"], 0.0, cyclic=True)   # the head opening
    G.hatch(X, -0.5, cz + 0.05, M["ink"], n=3, length=0.12, spacing=0.04, angle_deg=60, seed=5)
    G.stroke(X, dome, M["ink"], O, cyclic=True)
    for bx, sg in ((-0.42, -1), (0.36, 1)):                                                # the deflated bladders, draped over the rim
        sack = G.bezier((bx - 0.22, cz + rz * 0.86), (bx, cz + rz * 0.98), (bx + 0.24, cz + rz * 0.84), n=8) + \
            G.bezier((bx + 0.24, cz + rz * 0.84), (bx + sg * 0.42, cz + rz * 0.5), (bx + sg * 0.34, cz + rz * 0.18), n=8)[1:] + \
            G.bezier((bx + sg * 0.34, cz + rz * 0.18), (bx + sg * 0.2, cz + rz * 0.5), (bx - 0.22, cz + rz * 0.86), n=8)[1:-1]
        G.stroke(X, sack, M["cream_sh"], 0.0, cyclic=True)
        G.seam(X, [(bx, cz + rz * 0.9), (bx + sg * 0.22, cz + rz * 0.45)], M["ink"])
        G.stroke(X, sack, M["ink"], I, cyclic=True)
    for fx, fz in ((-0.8, 0.62), (0.1, 0.70), (0.7, 0.55)):                                # frost crusts on the plates
        G.stroke(X, G.lumpy_ellipse(fx, cz + fz * rz * 0.9, 0.08, 0.035, n=10, lump=0.15, seed=int(fx * 10) + 20), M["cream"], I, cyclic=True)


def derelict_pod(d, M, k=0):
    body = G.lumpy_ellipse(0.0, 0.62, 0.78, 0.5, n=40, lump=0.01, seed=31)
    body = [(x, max(z, 0.16)) for x, z in body]
    G.stroke(d, body, M["rust_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in body if q[0] > 0.3] + [(0.3, 0.62)], M["rust_sh"], 0.0, cyclic=True)
    patch = [(x, max(z, 0.98)) for x, z in G.lumpy_ellipse(-0.1, 1.06, 0.42, 0.2, n=20, lump=0.03, seed=32)]
    G.stroke(d, patch, M["cream_f"], 0.0, cyclic=True)                                    # the gasbag patch
    G.seam(d, [(-0.4, 1.06), (0.2, 1.08)], M["ink"])
    G.stroke(d, patch, M["ink"], I, cyclic=True)
    for x in (-0.4, 0.05, 0.45):                                                           # plate seams + rivets
        G.seam(d, G.bezier((x, 0.2), (x + 0.03, 0.62), (x, 1.0), n=6), M["ink"])
        G.rivets(d, [(x + 0.06, z) for z in (0.35, 0.6, 0.85)], M["ink"])
    G.stroke(d, G.lumpy_ellipse(0.32, 0.66, 0.15, 0.15, n=18, seed=33), M["festoon_f"], 0.0, cyclic=True)   # the round window
    G.stroke(d, G.lumpy_ellipse(0.28, 0.70, 0.05, 0.05, n=10, seed=34), M["cream"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.32, 0.66, 0.17, 0.17, n=18, seed=35), M["ink"], O, cyclic=True)
    torn = [(-0.62, 0.42), (-0.4, 0.36), (-0.44, 0.52), (-0.56, 0.6)]                       # a torn panel, dark behind
    G.stroke(d, torn, M["umber_dp"], 0.0, cyclic=True)
    G.stroke(d, torn, M["ink"], I, cyclic=True)
    G.stroke(d, [(-0.5, 0.16), (0.5, 0.16), (0.42, 0.04), (-0.42, 0.04)], M["umber_sh"], I, cyclic=True)    # the keel skid
    G.stroke(d, body, M["ink"], O, cyclic=True)


def beacon_vault(d, M, k=0):
    hull = [(-1.3, 0.0), (1.3, 0.0), (1.2, 1.3), (0.6, 1.75), (-0.6, 1.75), (-1.2, 1.3)]
    G.stroke(d, hull, M["rust_f"], 0.0, cyclic=True)
    G.stroke(d, [(0.6, 0.0), (1.3, 0.0), (1.2, 1.3), (0.6, 1.75)], M["rust_sh"], 0.0, cyclic=True)
    for j in range(7):                                                                     # warning stripes along the base
        x = -1.25 + 0.36 * j
        G.stroke(d, [(x, 0.05), (x + 0.18, 0.05), (x + 0.28, 0.25), (x + 0.1, 0.25)], M["cream_f" if j % 2 == 0 else "umber_f"], 0.0, cyclic=True)
    G.stroke(d, [(-1.28, 0.25), (1.28, 0.25)], M["ink"], I)
    for sx, sz, r in ((-0.8, 1.1, 0.22), (0.9, 0.7, 0.18), (-0.2, 1.5, 0.15)):              # radiation scorches
        G.stroke(d, G.lumpy_ellipse(sx, sz, r, r * 0.7, n=14, lump=0.2, seed=int(sx * 10) + 40), M["rust_dp"], 0.0, cyclic=True)
    G.stroke(d, [(-0.9, 0.5), (-0.3, 0.5), (-0.3, 0.62), (-0.9, 0.62)], M["festoon_f"], 0.0, cyclic=True)   # the glow slot (a tone)
    G.stroke(d, [(-0.9, 0.5), (-0.3, 0.5), (-0.3, 0.62), (-0.9, 0.62)], M["ink"], I, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.35, 0.82, 0.34, 0.34, n=28, seed=45), M["rust_dp"], 0.0, cyclic=True)    # the hatch
    G.stroke(d, G.lumpy_ellipse(0.35, 0.82, 0.28, 0.28, n=28, seed=46), M["rust"], O, cyclic=True)
    G.stroke(d, G.hose_outline([(0.15, 0.82), (0.55, 0.82)], 0.03), M["cream_sh"], I, cyclic=True)        # its wheel bar
    G.rivets(d, [(0.35 + 0.31 * math.cos(a), 0.82 + 0.31 * math.sin(a)) for a in [j * TAU / 8 for j in range(8)]], M["ink"])
    for x in (-0.6, 0.0, 0.6):
        G.seam(d, [(x, 0.3), (x, 1.7)], M["ink"])
    G.hatch(d, 0.9, 1.25, M["ink"], n=3, length=0.12, spacing=0.04, angle_deg=60, seed=47)
    G.stroke(d, hull, M["ink"], O, cyclic=True)


PROPS = {"husk_tortoise": (husk_tortoise, 176, 112), "derelict_pod": (derelict_pod, 128, 112), "beacon_vault": (beacon_vault, 192, 160)}


def pivot_of(name):
    _fn, fw, fh = PROPS[name]
    return (0.5, GROUND_PX / fh)


def render_prop(name, seed=7):
    fn, fw, fh = PROPS[name]
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    fn(d, M)
    return GR.render_frame(fakegp.strokes_of(d, gp), fw, fh, PPU, pivot_of(name), ss=4, seed=seed)


def render_all():
    imgs, widths = {}, {}
    for name in PROPS:
        img, w = render_prop(name)
        imgs[name], widths[name] = [img], w
    return imgs, widths


def sheet_meta(name, frames):
    _fn, fw, fh = PROPS[name]
    sheet = frames[0].copy()
    px, py = pivot_of(name)
    meta = {"key": KEY.format(name), "style": "v3", "frame_width": fw, "frame_height": fh, "columns": 1, "gutter": v3.GUTTER,
            "frames": 1, "fps": v3.FPS, "pivot": [round(px, 6), round(py, 6)], "facing": "right", "ppu": PPU, "animations": [],
            "squash_root": False, "ground_line_px": GROUND_PX, "note": "one static frame (no clip); the pivot sits on its base line"}
    if name == "husk_tortoise":
        meta["stand_line"] = shell_top()
        meta["note"] += "; stand_line = the shell's walkable top (m from the pivot), the husk of creatures/jupiter/ballast_tortoise"
    problems = [p for p in v3.validate_sheet(meta, sheet.shape) if "sum of clip lengths" not in p]
    m = v3.EDGE_MARGIN
    a = sheet[..., 3]
    if a[:m].any() or a[-m:].any() or a[:, :m].any() or a[:, -m:].any():
        problems.append(f"touches the {m} px frame edge")
    return sheet, meta, problems


def export(art, imgs=None, names=None):
    """For the Jupiter card: props/jupiter/<prop>_color.png + .json; the v2 model files removed (the .meta are UNITY's)."""
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
        raise ValueError("Jupiter prop export checks: " + "; ".join(problems))
    d = os.path.join(art, "props", "jupiter")
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
    """The design review: each prop at 2x with its checks, then all three at 1x on ice floes beside the surveyor."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_c2_jupiter_floes as JF
    import preview_c2_earth_rigs as PR
    if imgs is None:
        imgs, widths = render_all()
    W = 1700
    bg = np.array(v3.hex_rgb(P["sky"]), np.float32) / 255
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "b-155 jupiter props that differ (d-137 palette): the tortoise husk (a walkable stand_line), a derelict pod, the beacon vault", 6, 8)
    r = np.tile(bg, (2 * 160 + 40, W, 1))
    x, notes, allw = 10, [], []
    for name in PROPS:
        sheet, meta, problems = sheet_meta(name, imgs[name])
        hits, _o = v3.palette_hits(sheet, "jupiter")
        notes.append(f"{name} {meta['frame_width']}x{meta['frame_height']}: palette {hits * 100:.0f}%, json {'valid' if not problems else problems}")
        allw += widths[name]
        review._over(r, np.repeat(np.repeat(imgs[name][0], 2, 0), 2, 1), x, 30)
        review._label(r, name, x, 8, scale=1)
        x += PROPS[name][1] * 2 + 30
    S, _w = JF.sheets(("ice",))
    scene = np.tile(bg, (300, W, 1))
    base = 230
    rnd = np.random.default_rng(3)
    img = JF.floe(S, "ice", 22, rnd)
    review._over(scene, img[:300 - (base - 24)], 20, base - 24)
    xs = 80
    for name in PROPS:
        im = imgs[name][0]
        review._over(scene, im, xs, base - im.shape[0] + GROUND_PX)
        xs += im.shape[1] + 120
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, xs, base - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, "1x on an ice floe beside the surveyor (2 m)", 6, 6)
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
