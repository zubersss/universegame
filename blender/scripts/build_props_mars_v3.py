"""B-142 (D-126): Mars props as v3.1 prop sheets (colour + json only), drawn with gp_draw strokes through fakegp and the
numpy raster, the same API as build_props_common_v3 so render.py's do_prop_sheet_set exports a row that names this
generator. One prop so far:

  tube_mound  104x32, 1 static frame: the lava-tube lurker's den, a low lumpy rust boulder (cracks, specks, pebbles)
              whose base sinks 0.06 m into the ground strip. UNITY draws it IN FRONT of creatures/mars/tube_lurker on the same
              pivot (the den's mouth is behind its top line; D-126: creature art never contains terrain or props). Its
              top line is build_creatures_mars_v3.mound_dome, the line the lurker's paws rest on.

  python -I build_props_mars_v3.py <review png>     lock-free preview: the mound + the lurker's idle and react behind it
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_mars_v3 as CM  # noqa: E402  (gp_draw through fakegp outside Blender)
from meridian import fakegp, v3  # noqa: E402
import gp_raster as GR  # noqa: E402

G = CM.G
P = v3.PALETTES["mars"]
O, I = G.OUTER, G.INNER
PPU = 64
GROUND_PX = 10
KEY = "props/mars/{}"
SHEET_CAP = 512


def SH(h):
    return v3.shadow_of(h, "mars")


def DP(h):
    return v3.deep_of(h, "mars")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, f"mars_prop_{name}", **kw)
    return {"rock": m("rock", fill=SH(P["red"]), ink=False), "rock_sh": m("rock_mid", fill=DP(P["red"]), ink=False),
            "rock_lit": m("rock_lit", fill=P["red"], ink=False), "pebble": m("pebble", fill=SH(P["sky"])),
            "ink": m("ink", fill=None)}


def tube_mound(d, M, k=0):
    """The den: the shared top line, a base sunk 0.10 m into the ground (no ink along it), rust light on the upper left,
    mid tone low right, cracks + specks, two pebbles."""
    dome = CM.mound_dome()
    base = -0.06
    G.stroke(d, dome + [(dome[-1][0], base), (dome[0][0], base)], M["rock"], 0.0, cyclic=True)
    top_l = [q for q in dome if q[0] < CM.HOLE[0] - 0.05 and q[1] > 0.12]
    G.stroke(d, top_l + [(top_l[-1][0] + 0.06, top_l[-1][1] - 0.06), (top_l[0][0] + 0.10, 0.12)], M["rock_lit"], 0.0, cyclic=True)
    low_r = [q for q in dome if q[0] > CM.HOLE[0] + 0.12]
    G.stroke(d, low_r + [(low_r[-1][0], base), (low_r[0][0], base)], M["rock_sh"], 0.0, cyclic=True)
    for x, z, dx, dz in ((-0.32, 0.12, 0.06, -0.07), (0.24, 0.10, -0.04, -0.06), (-0.04, 0.05, 0.05, 0.04), (0.42, 0.04, 0.03, 0.05)):
        G.seam(d, [(x, z), (x + dx * 0.5 + 0.01, z + dz * 0.5), (x + dx, z + dz)], M["ink"])          # cracks
    G.specks(d, [(-0.42, 0.06), (0.36, 0.13), (0.06, 0.12), (-0.16, 0.17)], M["ink"])
    G.stroke(d, dome, M["ink"], O)
    for cx, rx, rz, sd in ((-0.66, 0.05, 0.03, 3), (0.70, 0.04, 0.025, 4)):                            # pebbles at the foot
        G.stroke(d, G.lumpy_ellipse(cx, rz * 0.6, rx, rz, n=12, lump=0.08, seed=sd), M["pebble"], I, cyclic=True)


PROPS = {"tube_mound": (tube_mound, 104, 32, None, 1, False)}
DEN_FOR = {"tube_mound": "creatures/mars/tube_lurker"}


def pivot_of(name):
    _fn, fw, fh, _clip, _n, _tiles = PROPS[name]
    return (0.5, GROUND_PX / fh)


def render_prop(name, k=0, seed=7):
    fn, fw, fh, _clip, _n, _tiles = PROPS[name]
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    fn(d, M, k)
    return GR.render_frame(fakegp.strokes_of(d, gp), fw, fh, PPU, pivot_of(name), ss=4, seed=seed)


def render_all():
    imgs, widths = {}, {}
    for name, (_fn, _fw, _fh, _clip, n, _tiles) in PROPS.items():
        imgs[name], widths[name] = [], []
        for k in range(n):
            img, w = render_prop(name, k)
            imgs[name].append(img)
            widths[name] += w
    return imgs, widths


def v2_leftovers(art, names=None):
    d = os.path.join(art, "props", "mars")
    return [os.path.join(d, n + s) for n in (names or PROPS) for s in (".glb", "_normal.png", "_mask.png", "_emission.png")
            if os.path.isfile(os.path.join(d, n + s))]


def sheet_meta(name, frames):
    import numpy as np
    _fn, fw, fh, clip, n, _tiles = PROPS[name]
    sheet = np.zeros((fh, fw, 4), np.uint8)
    sheet[:] = frames[0]
    px, py = pivot_of(name)
    meta = {"key": KEY.format(name), "style": "v3", "frame_width": fw, "frame_height": fh, "columns": 1, "gutter": v3.GUTTER,
            "frames": 1, "fps": v3.FPS, "pivot": [round(px, 6), round(py, 6)], "facing": "right", "ppu": PPU,
            "animations": [], "squash_root": False, "ground_line_px": GROUND_PX,
            "note": "one static frame (no clip); the pivot sits on the ground line"}
    if name in DEN_FOR:
        meta["den_for"] = DEN_FOR[name]
        meta["note"] += f"; D-126: drawn in front of {DEN_FOR[name]} on the same pivot (the creature peeks over its top line)"
    problems = [p for p in v3.validate_sheet(meta, sheet.shape) if "sum of clip lengths" not in p]
    m = v3.EDGE_MARGIN
    a = sheet[..., 3]
    if a[:m].any() or a[-m:].any() or a[:, :m].any() or a[:, -m:].any():
        problems.append(f"touches the {m} px frame edge")
    return sheet, meta, problems


def export(art, imgs=None, names=None):
    """props/mars/<prop>_color.png + <prop>.json; raises before writing anything if a check fails."""
    import json
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
        raise ValueError("Mars prop export checks: " + "; ".join(problems))
    d = os.path.join(art, "props", "mars")
    os.makedirs(d, exist_ok=True)
    out = []
    for name, sheet, meta in built:
        n = pngio.write_png(os.path.join(d, name + "_color.png"), sheet)
        with open(os.path.join(d, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((meta["key"], sheet.shape[1], sheet.shape[0], n))
    removed = v2_leftovers(art, names)
    for p in removed:
        os.remove(p)
    return out, {}, removed


def den_frames(scale=2):
    """The lurker's idle + react frames (exact ids) with the mound composited IN FRONT, as UNITY will draw them."""
    import numpy as np
    sp = CM.SPECIES["tube_lurker"]
    fw, fh = sp["frame"]
    mound, _w = render_prop("tube_mound")
    mh, mw = mound.shape[:2]
    poses = sp["poses"]()
    out = []
    starts = {c: s for c, s in zip([c for c, _n, _l in sp["clips"]], np.cumsum([0] + [n for _c, n, _l in sp["clips"]]))}
    for clip in ("idle", "react"):
        n = dict((c, n) for c, n, _l in sp["clips"])[clip]
        for f in range(starts[clip], starts[clip] + n):
            gp = fakegp.FakeGP()
            M = sp["mats"](gp, "tube_lurker")
            d = fakegp.FakeDrawing()
            sp["draw"](d, M, poses[f], seed=5 * f)
            img, _w = GR.render_frame(fakegp.strokes_of(d, gp, as_object=("tube_lurker", "art")), fw, fh, 64, (0.5, 0.0), ss=4,
                                      seed=sp["seed"] * 1000 + f + 1)
            # the canvas: the creature frame with GROUND_PX of room below its pivot, the mound's pivot on the same point
            H = fh + GROUND_PX
            c = np.zeros((H, fw, 4), np.float32)
            c[:fh] = img.astype(np.float32) / 255
            x0, y0 = fw // 2 - mw // 2, H - mh
            mf = mound.astype(np.float32) / 255
            reg = c[y0:y0 + mh, x0:x0 + mw]
            a = mf[..., 3:]
            reg[..., :3] = mf[..., :3] * a + reg[..., :3] * (1 - a)
            reg[..., 3:] = a + reg[..., 3:] * (1 - a)
            out.append((clip, f - starts[clip], c))
    return out


def main(out, imgs=None, widths=None, stamp_paths=()):
    """Review: the mound at 3x with its measured ink + palette, then the den (lurker idle + react behind the mound) at 2x."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    if imgs is None:
        imgs, widths = render_all()
    sheet, meta, problems = sheet_meta("tube_mound", imgs["tube_mound"])
    hits, off = v3.palette_hits(sheet, "mars")
    ws = widths["tube_mound"]
    outer = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in ws if w[0] < v3.OUTER_SPLIT]
    W = 1700
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, f"review props/mars/tube_mound (b-142, d-126)  104x32  pivot {meta['pivot']}  ink {min(w[1] for w in outer):.2f}-"
                        f"{max(w[2] for w in outer):.2f} / {min(w[1] for w in inner):.2f}-{max(w[2] for w in inner):.2f} px  "
                        f"mars palette {hits * 100:.1f}%  json {'valid' if not problems else '; '.join(problems)}", 6, 8)
    big = sheet.repeat(3, 0).repeat(3, 1)
    r1 = np.tile(review.PAPER, (big.shape[0] + 16, W, 1)).astype(np.float32)
    review._over(r1, big, 8, 8)
    review._label(r1, "3x: drawn in front of creatures/mars/tube_lurker on the same pivot", big.shape[1] + 24, 10)
    rows = [head, r1]
    den = den_frames()
    for clip in ("idle", "react"):
        fr = [c for cl, _i, c in den if cl == clip]
        h, w = fr[0].shape[:2]
        per = (W - 8) // (2 * w + 6)
        nr = -(-len(fr) // per)
        r = np.tile(review.PAPER, (nr * (2 * h + 6) + 26, W, 1)).astype(np.float32)
        for j, c in enumerate(fr):
            rr, cc = divmod(j, per)
            review._over(r, (np.clip(c, 0, 1) * 255).astype(np.uint8).repeat(2, 0).repeat(2, 1), 8 + cc * (2 * w + 6), 26 + rr * (2 * h + 6))
        review._label(r, f"den {clip} at 2x: the lurker behind its mound ({len(fr)} frames)", 6, 6)
        rows.append(r)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + (" export" if stamp_paths else " preview"), 2, img.shape[0] - 16)
    review.write(out, img)
    return problems


if __name__ == "__main__":
    print("problems", main(sys.argv[1]) or "-")
