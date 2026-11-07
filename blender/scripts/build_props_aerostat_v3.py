"""B-156 (D-137): the giants' aerostat kit re-inked once as v3.1 prop sheets (colour + json only) in the Earth palette, the
camp set's look (build_props_common_v3: its materials, hand-drawn boxes, edge-steadied tiling), shared by Jupiter, Saturn,
Uranus and Neptune; each replaces the v2 model under the same key when Jupiter opens (.glb + normal / mask / emission
removed on export; the .meta files are UNITY's). Sizes follow the build grid (1 m cells) and the v2 sprites' frames.

  props/common/aerostat_deck        128x64   a 2 m deck module: wooden planks on a steel truss; tiles in x
  props/common/aerostat_strut       64x128   a 1 x 2 m riveted lattice strut; tiles in y (stacked struts)
  props/common/aerostat_cell        72x152   a lift cell: a cream gasbag in a brass cage with netting and a teal valve;
                                             breathe 4 (a gentle swell, loops)
  props/common/float_cell_pack_mk1  72x88    a backpack float cell: one cream canister on a brass frame (v2 frame + pivot)
  props/common/float_cell_pack_mk2  72x88    two canisters, teal trim
  props/common/grapple_hook         76x52    three rounded prongs and a rope eye; the pivot at the eye (v2 pivot)

  python -I build_props_aerostat_v3.py <review png>      lock-free design review (fakegp + numpy)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_props_common_v3 as PC  # noqa: E402  (installs fakegp outside Blender; the camp set's helpers)
from meridian import fakegp, v3  # noqa: E402
import gp_raster as GR  # noqa: E402

G = PC.G
P = PC.P
O, I = G.OUTER, G.INNER
PPU, GROUND_PX = PC.PPU, PC.GROUND_PX
mats, box, hline = PC.mats, PC.box, PC.hline
KEY = "props/common/{}"


def aerostat_deck(d, M, k=0):
    """A 2 m module: three plank rows on top (the walkable line at 0.62 m), a steel truss below; tiles in x."""
    L, R = -1.0, 1.0
    G.stroke(d, [(L - 0.02, 0.44), (R + 0.02, 0.44), (R + 0.02, 0.62), (L - 0.02, 0.62)], M["wood_f"], 0.0, cyclic=True)   # the planks
    G.stroke(d, [(L - 0.02, 0.44), (R + 0.02, 0.44), (R + 0.02, 0.5), (L - 0.02, 0.5)], M["wood_sh"], 0.0, cyclic=True)
    for x in (-0.75, -0.25, 0.25, 0.75):                                                   # plank butt joints (inside the module)
        G.seam(d, [(x, 0.46), (x + 0.005, 0.6)], M["ink"])
    G.seam(d, [(-0.9, 0.55), (-0.5, 0.56), (-0.1, 0.55)], M["ink"])                         # grain
    G.seam(d, [(0.35, 0.53), (0.7, 0.535)], M["ink"])
    G.stroke(d, [(L - 0.02, 0.06), (R + 0.02, 0.06), (R + 0.02, 0.14), (L - 0.02, 0.14)], M["steel_f"], 0.0, cyclic=True)   # the bottom chord
    for i in range(4):                                                                     # the truss: diagonals between the chords
        x0 = -1.0 + 0.5 * i
        G.stroke(d, G.hose_outline([(x0 + 0.04, 0.14), (x0 + 0.46, 0.44)], 0.025), M["steel"], I, cyclic=True)
    G.rivets(d, [(x, 0.10) for x in (-0.74, -0.24, 0.26, 0.76)], M["ink"])
    G.hatch(d, 0.55, 0.3, M["ink"], n=3, length=0.08, spacing=0.03, angle_deg=60, seed=3)
    for z in (0.06, 0.14, 0.44, 0.62):                                                     # straight edge lines (tiling)
        hline(d, M, L - 0.02, R + 0.02, z, r=I if z != 0.62 else O)


def aerostat_strut(d, M, k=0):
    """A 1 x 2 m lattice strut: two steel uprights, cross braces, rivets; tiles in y (half a brace at each end)."""
    B, T = 0.0, 2.0
    for x in (-0.32, 0.32):
        G.stroke(d, [(x - 0.06, B - 0.02), (x + 0.06, B - 0.02), (x + 0.06, T + 0.02), (x - 0.06, T + 0.02)], M["steel_f"], 0.0, cyclic=True)
        G.stroke(d, [(x + 0.02, B - 0.02), (x + 0.06, B - 0.02), (x + 0.06, T + 0.02), (x + 0.02, T + 0.02)], M["steel_sh"], 0.0, cyclic=True)
        for xx in (x - 0.06, x + 0.06):
            G.stroke(d, [(xx, B - 0.02 + (T - B + 0.04) * i / 24) for i in range(25)], M["ink"], I)
    for i in range(4):                                                                     # the braces, a full X per half metre
        z0 = 0.5 * i
        G.stroke(d, G.hose_outline([(-0.26, z0 + 0.04), (0.26, z0 + 0.46)], 0.022), M["steel"], I, cyclic=True)
        G.stroke(d, G.hose_outline([(0.26, z0 + 0.04), (-0.26, z0 + 0.46)], 0.022), M["steel"], I, cyclic=True)
    for z in (0.0, 0.5, 1.0, 1.5, 2.0):                                                    # gusset bands, the ends split half / half
        G.stroke(d, [(-0.38, z - 0.03), (0.38, z - 0.03), (0.38, z + 0.03), (-0.38, z + 0.03)], M["steel_dp"], 0.0, cyclic=True)
    G.rivets(d, [(x, z) for x in (-0.32, 0.32) for z in (0.5, 1.0, 1.5)], M["ink"])
    G.stroke(d, [(0.2, 1.3), (0.23, 1.18), (0.19, 1.06)], M["wood_sh"], I)                  # a rust streak


BREATHE = [1.0, 1.03, 1.05, 1.03]


def aerostat_cell(d, M, k=0):
    """A lift cell: a cream gasbag (it breathes) in a brass cage on a base plate, netting, a teal valve on top."""
    s = BREATHE[k % len(BREATHE)]
    G.stroke(d, box(-0.42, 0.0, 0.42, 0.12, seed=60), M["mustard_sh"], O, cyclic=True)       # the base plate
    bag = G.lumpy_ellipse(0.0, 1.05, 0.40 * s, 0.82 * s, n=40, lump=0.015, seed=61)
    G.stroke(d, bag, M["off_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in bag if q[0] > 0.14 * s] + [(0.14 * s, 1.05)], M["off_sh"], 0.0, cyclic=True)
    for t in (-0.6, 0.0, 0.6):                                                              # the netting
        G.seam(d, G.bezier((t * 0.4 * s, 0.26), (t * 0.75 * s, 1.05), (t * 0.4 * s, 1.84), n=8), M["ink"])
    for z in (0.65, 1.05, 1.45):
        w = 0.40 * s * math.sqrt(max(0.0, 1 - ((z - 1.05) / (0.82 * s)) ** 2))
        G.seam(d, G.bezier((-w, z), (0.0, z - 0.04), (w, z), n=7), M["ink"])
    G.stroke(d, bag, M["ink"], O, cyclic=True)
    for x in (-0.46, 0.46):                                                                 # the brass cage uprights
        G.stroke(d, G.hose_outline([(x * 0.92, 0.12), (x, 1.05), (x * 0.4, 1.95)], 0.03), M["mustard"], I, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, 1.97, 0.12, 0.06, n=12, seed=62), M["teal"], I, cyclic=True)   # the valve
    G.stroke(d, [(0.0, 2.03), (0.0, 2.1)], M["ink"], I)
    G.rivets(d, [(-0.3, 0.06), (0.0, 0.06), (0.3, 0.06)], M["ink"])


def float_pack(d, M, mk):
    """A backpack float cell on a brass frame: one cream canister (mk1) or two with teal trim (mk2); faces right."""
    G.stroke(d, box(-0.22, 0.02, 0.06, 0.92, seed=70), M["mustard"], O, cyclic=True)        # the pack frame
    G.stroke(d, box(0.0, 0.02, 0.06, 0.92, seed=71, wob=0.002), M["mustard_sh"], 0.0, cyclic=True)
    for z in (0.2, 0.7):                                                                    # two shoulder straps
        G.stroke(d, G.hose_outline([(0.06, z), (0.2, z + 0.06)], 0.025), M["wood"], I, cyclic=True)
    cells = ((-0.2, 0.62, 0.17, 0.30),) if mk == 1 else ((-0.24, 0.66, 0.14, 0.26), (-0.06, 0.58, 0.13, 0.24))
    for j, (cx, cz, rx, rz) in enumerate(cells):
        can = G.lumpy_ellipse(cx, cz, rx, rz, n=24, lump=0.015, seed=72 + j)
        G.stroke(d, can, M["off_f"], 0.0, cyclic=True)
        G.stroke(d, [q for q in can if q[0] > cx + rx * 0.3] + [(cx + rx * 0.3, cz)], M["off_sh"], 0.0, cyclic=True)
        G.seam(d, [(cx - rx * 0.8, cz), (cx + rx * 0.8, cz + 0.01)], M["ink"])
        G.stroke(d, can, M["ink"], O, cyclic=True)
        G.stroke(d, box(cx - 0.04, cz + rz - 0.02, cx + 0.04, cz + rz + 0.05, seed=74 + j), M["teal" if mk == 2 else "mustard"], I, cyclic=True)   # the valve cap
    if mk == 2:
        G.stroke(d, box(-0.22, 0.30, 0.06, 0.36, seed=76), M["teal"], I, cyclic=True)           # the teal trim band
    G.rivets(d, [(-0.18, 0.08), (0.02, 0.08), (-0.18, 0.86)], M["ink"])


def grapple_hook(d, M, k=0):
    """Three rounded prongs (no points) on a steel shank, a rope eye on the left at the origin; drawn 0.9x so it fits its
    76x52 frame at the v2 pivot, the prongs wide enough for the steel to show at 1x."""
    d = G.Xf(d, lambda pts: [(x * 0.9, z * 0.9) for x, z in pts])
    G.stroke(d, G.lumpy_ellipse(0.0, 0.0, 0.07, 0.06, n=14, seed=80), M["steel"], O, cyclic=True)        # the eye
    G.stroke(d, G.lumpy_ellipse(0.0, 0.0, 0.03, 0.025, n=10, seed=81), M["hole"], 0.0, cyclic=True)
    G.stroke(d, G.hose_outline([(0.06, 0.0), (0.62, 0.0)], 0.06), M["steel"], O, cyclic=True)            # the shank
    G.stroke(d, G.hose_outline([(0.08, -0.02), (0.6, -0.02)], 0.015), M["steel_sh"], 0.0, cyclic=True)
    for sg, a0 in ((1, 0.0), (-1, 0.0), (0, 0.0)):                                                       # the prongs, curling back
        if sg == 0:
            pts = [(0.62, 0.0), (0.84, 0.0), (0.9, 0.0)]
        else:
            pts = G.bezier((0.6, 0.0), (0.78, sg * 0.30), (0.62, sg * 0.30), n=8)
        G.stroke(d, G.hose_outline(pts, 0.05), M["steel"], O, cyclic=True)
        tip = pts[-1]
        G.stroke(d, G.lumpy_ellipse(tip[0], tip[1], 0.04, 0.04, n=10, seed=82 + sg), M["steel"], I, cyclic=True)   # a round tip
    G.stroke(d, G.hose_outline([(-0.06, 0.0), (-0.10, -0.01)], 0.02), M["wood"], I, cyclic=True)        # a stub of rope
    G.rivets(d, [(0.4, 0.0)], M["ink"])


PROPS = {   # name: (fn, fw, fh, clip, frames, tiles, pivot)
    "aerostat_deck": (aerostat_deck, 128, 64, None, 1, True, (0.5, 0.0)),
    "aerostat_strut": (aerostat_strut, 64, 128, None, 1, False, (0.5, 0.0)),
    "aerostat_cell": (aerostat_cell, 72, 152, "breathe", 4, False, (0.5, 0.0)),
    "float_cell_pack_mk1": (lambda d, M, k=0: float_pack(d, M, 1), 72, 88, None, 1, False, (0.5, 0.113636)),
    "float_cell_pack_mk2": (lambda d, M, k=0: float_pack(d, M, 2), 72, 88, None, 1, False, (0.5, 0.113636)),
    "grapple_hook": (grapple_hook, 76, 52, None, 1, False, (0.157895, 0.5)),
}
TILE_Y = ("aerostat_strut",)


def render_prop(name, k=0, seed=7):
    fn, fw, fh, _clip, _n, tiles, piv = PROPS[name]
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    fn(d, M, k)
    st = fakegp.strokes_of(d, gp)
    if tiles:
        PC.steady_edges(st, -fw / 2 / PPU, fw / 2 / PPU, seed)
    if name in TILE_Y:
        PC.steady_edges(st, -9.0, 9.0, seed, zl=0.0, zr=fh / PPU)
    img, w = GR.render_frame(st, fw, fh, PPU, piv, ss=4, seed=seed)
    if tiles:
        img[:, -1] = img[:, 0]
    if name in TILE_Y:
        img[0] = img[-1]
    return img, w


def render_all():
    imgs, widths = {}, {}
    for name, spec in PROPS.items():
        imgs[name], widths[name] = [], []
        for k in range(spec[4]):
            img, w = render_prop(name, k)
            imgs[name].append(img)
            widths[name] += w
    return imgs, widths


def sheet_meta(name, frames):
    import numpy as np
    _fn, fw, fh, clip, n, tiles, piv = PROPS[name]
    g = v3.GUTTER
    cols = PC.columns_within(fw, fh, n)
    rows = -(-n // cols)
    sheet = np.zeros((rows * fh + (rows - 1) * g, min(cols, n) * fw + (min(cols, n) - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw] = im
    anims = [{"name": clip, "start": 0, "length": n, "loop": True, "loop_from": 0}] if clip else []
    meta = {"key": KEY.format(name), "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": g, "frames": n,
            "fps": v3.FPS, "pivot": [round(piv[0], 6), round(piv[1], 6)], "facing": "right", "ppu": PPU, "animations": anims,
            "squash_root": False, "ground_line_px": 0 if piv[1] == 0.0 else GROUND_PX,
            "note": "B-156: the giants' aerostat kit (Earth palette, the camp set's look); replaces the v2 model under this key"}
    if tiles:
        meta["tile"], meta["module_m"] = True, fw / PPU
    if name in TILE_Y:
        meta["tile_y"] = True
    problems = [p for p in v3.validate_sheet(meta, sheet.shape) if not (not clip and "sum of clip lengths" in p)]
    m = v3.EDGE_MARGIN
    for i, im in enumerate(frames):
        a = im[..., 3]
        if (name not in TILE_Y and a[:m].any()) or (not tiles and (a[:, :m].any() or a[:, -m:].any())):
            problems.append(f"frame {i} touches the {m} px frame edge")
    return sheet, meta, problems


def export(art, imgs=None, names=None):
    """For the Jupiter card (B-156): props/common/<prop>_color.png + .json, the v2 model files removed. Raises first."""
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
        raise ValueError("aerostat kit checks: " + "; ".join(problems))
    d = os.path.join(art, "props", "common")
    os.makedirs(d, exist_ok=True)
    out = []
    for name, sheet, meta in built:
        n = pngio.write_png(os.path.join(d, name + "_color.png"), sheet)
        with open(os.path.join(d, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((meta["key"], sheet.shape[1], sheet.shape[0], n))
    removed = [os.path.join(d, n_ + s) for n_ in names for s in PC.V2_SUFFIXES if os.path.isfile(os.path.join(d, n_ + s))]
    for p in removed:
        os.remove(p)
    return out, {}, removed


def main(out, imgs=None, widths=None, stamp_paths=()):
    """The design review: each prop at 2x with its checks, then a 1x aerostat built from the kit beside the surveyor."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    if imgs is None:
        imgs, widths = render_all()
    W = 1700
    rows = []
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "b-156 the giants' aerostat kit (d-137): earth palette, the camp set's look; replaces the v2 models under the same keys", 6, 8)
    rows.append(head)
    bg = np.array(v3.hex_rgb(v3.PALETTES["jupiter"]["sky"]), np.float32) / 255
    r = np.tile(bg, (2 * max(spec[2] for spec in PROPS.values()) + 50, W, 1))
    x = 10
    allw, notes = [], []
    for name in PROPS:
        sheet, meta, problems = sheet_meta(name, imgs[name])
        allw += widths[name]
        hits, _o = v3.palette_hits(sheet, "earth")
        big = np.repeat(np.repeat(imgs[name][0], 2, 0), 2, 1)
        review._over(r, big, x, 30)
        review._label(r, f"{name} {meta['frame_width']}x{meta['frame_height']}", x, 8, scale=1)
        notes.append(f"{name}: palette {hits * 100:.0f}%, json {'valid' if not problems else problems}")
        x += big.shape[1] + 24
    rows.append(r)
    scene = np.tile(bg, (520, W, 1))                                                       # room for the 128 px strut under the deck
    base_y = 330
    deck = imgs["aerostat_deck"][0]
    for c in range(4):                                                                     # a 4-module deck (8 m)
        review._over(scene, deck, 300 + c * 128, base_y - 64)
    for c in (0, 3):                                                                        # two struts under it
        review._over(scene, imgs["aerostat_strut"][0], 330 + c * 128, base_y)
    for c, k in ((0, 0), (3, 2)):                                                           # two lift cells on the deck
        review._over(scene, imgs["aerostat_cell"][k], 330 + c * 128, base_y - 64 - 136 + 40)
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, 520, base_y - 24 - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    except Exception:  # noqa: BLE001
        pass
    review._over(scene, imgs["float_cell_pack_mk1"][0], 900, base_y - 140)
    review._over(scene, imgs["float_cell_pack_mk2"][0], 990, base_y - 140)
    review._over(scene, imgs["grapple_hook"][0], 1090, base_y - 120)
    review._label(scene, "1x: an aerostat from the kit (four deck modules, two struts, two lift cells) with the surveyor on it; the packs and the hook", 6, 6)
    rows.append(scene)
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    j = float(np.abs(imgs["aerostat_deck"][0][:, -1].astype(np.int32) - imgs["aerostat_deck"][0][:, 0].astype(np.int32)).mean())
    jy = float(np.abs(imgs["aerostat_strut"][0][-1].astype(np.int32) - imgs["aerostat_strut"][0][0].astype(np.int32)).mean())
    foot = np.tile(review.PAPER, (30 + 18 * len(notes), W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; deck join {j:.2f}/255, strut join (y) {jy:.2f}/255", 6, 6)
    for i, t in enumerate(notes):
        review._label(foot, t, 6, 24 + 18 * i, scale=1)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + (" export" if stamp_paths else " preview (not exported)"), 2, img.shape[0] - 16)
    review.write(out, img)
    print("written", out, "|", "; ".join(notes), f"| deck join {j:.2f}, strut join {jy:.2f}")
    return []


if __name__ == "__main__":
    main(sys.argv[1])
