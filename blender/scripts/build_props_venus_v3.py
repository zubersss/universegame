"""B-147 (C2 Venus design prep; D-126, D-134): Venus props as v3.1 prop sheets (colour + json only), the build_props_common_v3
/ build_props_mercury_v3 API (PROPS, KEY, render_all, sheet_meta, export, main) so render.py's prop rows can export them.
One prop so far:

  vent_mouth  96x40, 1 static frame: the Vent eel's den, a squat black-basalt vent cone with glassy sheen dabs, a
              sulphur crust on its lee side and a vent-orange glow inside the lip, whose top line is
              build_creatures_venus_v3.VENT_TOP (the eel's peek rises behind it). Nothing is drawn above the top line, so the
              eel is never covered. UNITY draws it IN FRONT of creatures/venus/vent_eel on the same pivot (D-126).

  python -I build_props_venus_v3.py <review png>   lock-free den review: the vent at 3x, the eel's idle + react behind it
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_venus_v3 as CM  # noqa: E402  (gp_draw through fakegp outside Blender)
from meridian import fakegp, v3  # noqa: E402
import gp_raster as GR  # noqa: E402

G = CM.G
P = v3.PALETTES["venus"]
O, I = G.OUTER, G.INNER
PPU = 64
GROUND_PX = 10
KEY = "props/venus/{}"
SHEET_CAP = 512


def SH(h):
    return v3.shadow_of(h, "venus")


def DP(h):
    return v3.deep_of(h, "venus")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, f"venus_prop_{name}", **kw)
    return {"basalt": m("basalt", fill=P["brown"], ink=False), "basalt_sh": m("basalt_mid", fill=DP(P["brown"]), ink=False),
            "sheen": m("sheen", fill=SH(P["offwhite"]), ink=False), "sulphur": m("sulphur", fill=P["mustard"], ink=False),
            "glow": m("glow", fill=P["red"], ink=False), "glow_hot": m("glow_hot", fill=P["mustard"], ink=False),
            "pebble": m("pebble", fill=SH(P["brown"])), "ink": m("ink", fill=None)}


def vent_mouth(d, M, k=0):
    """The den: a basalt cone under the shared top line, the base sunk 0.06 m (no ink along it), the glow inside the lip."""
    top = CM.VENT_TOP
    base = -0.06
    G.stroke(d, top + [(top[-1][0], base), (top[0][0], base)], M["basalt"], 0.0, cyclic=True)
    G.stroke(d, [(0.26, 0.24), (0.42, 0.10), (0.56, 0.0), (0.56, base), (0.20, base), (0.18, 0.12)], M["basalt_sh"], 0.0, cyclic=True)   # the lee side
    G.stroke(d, [(0.30, 0.20), (0.40, 0.11), (0.46, 0.05), (0.36, 0.04), (0.30, 0.10)], M["sulphur"], 0.0, cyclic=True)   # the sulphur crust
    G.stroke(d, [(-0.13, 0.285), (0.13, 0.285), (0.10, 0.235), (-0.10, 0.235)], M["glow"], 0.0, cyclic=True)               # the glow in the lip
    G.stroke(d, [(-0.07, 0.28), (0.07, 0.28), (0.05, 0.255), (-0.05, 0.255)], M["glow_hot"], 0.0, cyclic=True)
    G.seam(d, [(-0.13, 0.235), (0.13, 0.235)], M["ink"])                                  # the lip's lower edge
    for x0, z0, x1, z1 in ((-0.36, 0.17, -0.28, 0.02), (-0.04, 0.22, 0.02, 0.03), (0.22, 0.20, 0.16, 0.02)):   # cooling cracks
        G.seam(d, [(x0, z0), ((x0 + x1) / 2 - 0.01, (z0 + z1) / 2), (x1, z1 + 0.01)], M["ink"])
    for cx, cz, rx, rz in ((-0.30, 0.13, 0.05, 0.012), (-0.12, 0.20, 0.04, 0.01)):        # glassy sheen dabs (the light side)
        G.stroke(d, G.lumpy_ellipse(cx, cz, rx, rz, n=10, lump=0.05, seed=int(abs(cx) * 100) + 50), M["sheen"], 0.0, cyclic=True)
    G.specks(d, [(-0.20, 0.08), (0.08, 0.12), (0.34, 0.06)], M["ink"])
    G.stroke(d, top, M["ink"], O)
    for cx, rx, rz, sd in ((-0.64, 0.04, 0.026, 3), (0.65, 0.035, 0.022, 4)):            # two cinders at the foot
        G.stroke(d, G.lumpy_ellipse(cx, rz * 0.6, rx, rz, n=10, lump=0.08, seed=sd), M["pebble"], I, cyclic=True)


PROPS = {"vent_mouth": (vent_mouth, 96, 40, None, 1, False)}
DEN_FOR = {"vent_mouth": "creatures/venus/vent_eel"}


def pivot_of(name):
    _fn, fw, fh, _c, _n, _t = PROPS[name]
    return (0.5, GROUND_PX / fh)


def render_prop(name, k=0, seed=7):
    fn, fw, fh, _c, _n, _t = PROPS[name]
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    fn(d, M, k)
    return GR.render_frame(fakegp.strokes_of(d, gp), fw, fh, PPU, pivot_of(name), ss=4, seed=seed)


def render_all():
    imgs, widths = {}, {}
    for name, (_fn, _fw, _fh, _c, n, _t) in PROPS.items():
        imgs[name], widths[name] = [], []
        for k in range(n):
            img, w = render_prop(name, k)
            imgs[name].append(img)
            widths[name] += w
    return imgs, widths


def sheet_meta(name, frames):
    _fn, fw, fh, clip, n, _t = PROPS[name]
    sheet = frames[0].copy()
    px, py = pivot_of(name)
    meta = {"key": KEY.format(name), "style": "v3", "frame_width": fw, "frame_height": fh, "columns": 1, "gutter": v3.GUTTER,
            "frames": 1, "fps": v3.FPS, "pivot": [round(px, 6), round(py, 6)], "facing": "right", "ppu": PPU, "animations": [],
            "squash_root": False, "ground_line_px": GROUND_PX,
            "note": "one static frame (no clip); the pivot sits on the ground line"}
    if name in DEN_FOR:
        meta["den_for"] = DEN_FOR[name]
        meta["note"] += f"; D-126: drawn in front of {DEN_FOR[name]} on the same pivot"
    problems = [p for p in v3.validate_sheet(meta, sheet.shape) if "sum of clip lengths" not in p]
    m = v3.EDGE_MARGIN
    a = sheet[..., 3]
    if a[:m].any() or a[-m:].any() or a[:, :m].any() or a[:, -m:].any():
        problems.append(f"touches the {m} px frame edge")
    return sheet, meta, problems


def v2_leftovers(art, names=None):
    d = os.path.join(art, "props", "venus")
    return [os.path.join(d, n + s) for n in (names or PROPS) for s in (".glb", "_normal.png", "_mask.png", "_emission.png")
            if os.path.isfile(os.path.join(d, n + s))]


def export(art, imgs=None, names=None):
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
        raise ValueError("Venus prop export checks: " + "; ".join(problems))
    d = os.path.join(art, "props", "venus")
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


def den_frames():
    """The eel's idle + react frames (exact ids) with the vent composited IN FRONT, as UNITY will draw them."""
    import numpy as np
    sp = CM.SPECIES["vent_eel"]
    fw, fh = sp["frame"]
    mound, _w = render_prop("vent_mouth")
    mh, mw = mound.shape[:2]
    poses = sp["poses"]()
    starts, s_ = {}, 0
    for c, n, _l in sp["clips"]:
        starts[c] = (s_, n)
        s_ += n
    out = []
    for clip in ("idle", "react"):
        a0, n = starts[clip]
        for f in range(a0, a0 + n):
            gp = fakegp.FakeGP()
            M = sp["mats"](gp, "vent_eel")
            d = fakegp.FakeDrawing()
            sp["draw"](d, M, poses[f], seed=5 * f)
            img, _w = GR.render_frame(fakegp.strokes_of(d, gp, as_object=("vent_eel", "art")), fw, fh, 64, (0.5, 0.0), ss=4,
                                      seed=sp["seed"] * 1000 + f + 1)
            H = fh + GROUND_PX
            c = np.zeros((H, fw, 4), np.float32)
            c[:fh] = img.astype(np.float32) / 255
            x0, y0 = fw // 2 - mw // 2, H - mh
            mf = mound.astype(np.float32) / 255
            reg = c[y0:y0 + mh, x0:x0 + mw]
            al = mf[..., 3:]
            reg[..., :3] = mf[..., :3] * al + reg[..., :3] * (1 - al)
            reg[..., 3:] = al + reg[..., 3:] * (1 - al)
            out.append((clip, c))
    return out


def main(out, imgs=None, widths=None, stamp_paths=()):
    """The den review: the vent at 3x (ink, palette, json), then the eel's idle + react behind it at 2x."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    if imgs is None:
        imgs, widths = render_all()
    sheet, meta, problems = sheet_meta("vent_mouth", imgs["vent_mouth"])
    hits, _off = v3.palette_hits(sheet, "venus")
    ws = widths["vent_mouth"]
    outer = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in ws if w[0] < v3.OUTER_SPLIT]
    W = 1700
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, f"review props/venus/vent_mouth (b-147, d-126)  96x40  pivot {meta['pivot']}  ink {min(w[1] for w in outer):.2f}-"
                        f"{max(w[2] for w in outer):.2f} / {min(w[1] for w in inner):.2f}-{max(w[2] for w in inner):.2f} px  "
                        f"venus palette {hits * 100:.1f}%  json {'valid' if not problems else '; '.join(problems)}", 6, 8)
    big = sheet.repeat(3, 0).repeat(3, 1)
    r1 = np.tile(review.PAPER, (big.shape[0] + 16, W, 1)).astype(np.float32)
    review._over(r1, big, 8, 8)
    review._label(r1, "3x: drawn in front of creatures/venus/vent_eel on the same pivot", big.shape[1] + 24, 10)
    rows = [head, r1]
    den = den_frames()
    for clip in ("idle", "react"):
        fr = [c for cl, c in den if cl == clip]
        h, w = fr[0].shape[:2]
        per = (W - 8) // (2 * w + 6)
        nr = -(-len(fr) // per)
        r = np.tile(review.PAPER, (nr * (2 * h + 6) + 26, W, 1)).astype(np.float32)
        for j, c in enumerate(fr):
            rr, cc = divmod(j, per)
            review._over(r, (np.clip(c, 0, 1) * 255).astype(np.uint8).repeat(2, 0).repeat(2, 1), 8 + cc * (2 * w + 6), 26 + rr * (2 * h + 6))
        review._label(r, f"den {clip} at 2x: the eel behind its vent ({len(fr)} frames)", 6, 6)
        rows.append(r)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + (" export" if stamp_paths else " preview"), 2, img.shape[0] - 16)
    review.write(out, img)
    return problems


if __name__ == "__main__":
    print("problems", main(sys.argv[1]) or "-")
