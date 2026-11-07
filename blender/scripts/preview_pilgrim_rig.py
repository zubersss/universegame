"""Lock-free preview of the Pilgrim rig (B-122, D-111) for LEAD: the rig ASSEMBLED from its parts
through the bone chain exactly as Unity's RigSetBuilder will (part pivots at bone origins, bone
offsets, slots), with the 12 Hz bone clips applied. No Blender: meridian.fakegp + numpy.

  python -I preview_pilgrim_rig.py <out.png>

Panels: (1) the ship at 1x (12 m = 768 px) standing on the plains beside the surveyor (frame 0
of the exported surveyor sheet), (2) the +-35 deg in-flight tilt Unity applies to the root,
(3) every bone clip as a numbered strip (fin_wobble 8, leg_flex 8, hatch_open 6, top fin_wobble 8),
(4) the packed parts with pivots, the measured ink widths and the §11.3 validation.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from meridian import fakegp, v3  # noqa: E402

G = fakegp.install()
import build_pilgrim_v3 as BP  # noqa: E402
import gp_raster as GR  # noqa: E402
import review  # noqa: E402

ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))


def compose(m1, m2):
    a1, b1, c1, d1, x1, z1 = m1
    a2, b2, c2, d2, x2, z2 = m2
    return (a1 * a2 + b1 * c2, a1 * b2 + b1 * d2, c1 * a2 + d1 * c2, c1 * b2 + d1 * d2, a1 * x2 + b1 * z2 + x1, c1 * x2 + d1 * z2 + z1)


def affine(m):
    a, b, c, d, tx, tz = m
    return lambda pts: [(a * x + b * z + tx, c * x + d * z + tz) for x, z in pts]


def trs(tx, tz, deg=0.0, sx=1.0, sz=1.0):
    r = math.radians(deg)
    ca, sa = math.cos(r), math.sin(r)
    return (ca * sx, -sa * sz, sa * sx, ca * sz, tx, tz)


def pose_rig(rig, frame_tracks):
    """World matrices per bone for one clip frame: {bone: {'rot_deg': x, 'scale': [sx, sz]}}."""
    world = {}
    for b in rig["bones"]:
        off = b.get("offset_m", [0.0, 0.0])
        tr = frame_tracks.get(b["name"], {})
        local = trs(off[0], off[1], tr.get("rot_deg", 0.0), *(tr.get("scale", [1.0, 1.0])))
        world[b["name"]] = local if b["parent"] is None else compose(world[b["parent"]], local)
    return world


def draw_rig(d, M, rig, frame_tracks):
    W = pose_rig(rig, frame_tracks)
    items = [(b["order"], b["part"], W[b["name"]]) for b in rig["bones"]]
    for s in rig.get("slots", []):
        items.append((s["order"], rig["swaps"][s["slot"]][0], compose(W[s["bone"]], trs(*s["offset_m"]))))
    for _o, part, m in sorted(items, key=lambda t: t[0]):
        BP.draw_rig_part(G.Xf(d, affine(m)), M, part)


def tracks_at(clip, k):
    return {bone: {key: vals[k] for key, vals in tr.items()} for bone, tr in clip["tracks"].items()}


def render(rig, tracks, fw, fh, pivot, ppu=64):
    gp = fakegp.FakeGP()
    M = BP.materials_v2(gp)
    d = fakegp.FakeDrawing()
    draw_rig(d, M, rig, tracks)
    return fakegp.render(d, gp, fw, fh, pivot=pivot, ppu=ppu, ss=2, seed=5)


def main(out):
    side, top = BP.PILGRIM_RIGS
    fw, fh, piv = 400, 816, (0.5, 12 / 816)
    allw = []
    rest, w = render(side, {}, fw, fh, piv)
    allw += w
    paper = review.PAPER
    W = 1900
    # (1) on the plains at 1x beside the surveyor; (2) tilted +-35 about the centre of mass
    H1 = fh + 40
    sky = np.array([0.62, 0.72, 0.72], np.float32)
    bg = np.tile(sky, (H1, W, 1)).astype(np.float32)
    bg[H1 - 30:] = np.array(v3.hex_rgb(v3.PALETTES["earth"]["green"]), np.float32) / 255
    ground = H1 - 30
    review._over(bg, rest, 40, ground - fh + int(piv[1] * fh))
    try:
        import json
        from meridian import pngio
        sm = json.load(open(os.path.join(ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
        sh = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))
        sfr = sh[:sm["frame_height"], :sm["frame_width"]]
        review._over(bg, sfr, 40 + fw + 10, ground - sm["frame_height"])
        review._label(bg, "surveyor frame 0 at 1x", 40 + fw + 10, ground - sm["frame_height"] - 18)
    except Exception as e:  # noqa: BLE001
        review._label(bg, f"surveyor unavailable: {type(e).__name__}", 40 + fw + 10, 40)
    x = 40 + fw + 220
    for deg in (-35.0, 35.0):
        rot = review.rotate_about(rest, deg, (piv[0] * fw, fh - piv[1] * fh - 6.2 * 64))
        review._over(bg, rot, x, max(0, ground - rot.shape[0] - 60))
        review._label(bg, f"flight tilt {deg:+.0f} (unity root)", x, 30)
        x += rot.shape[1] + 30
    review._label(bg, "b-122 pilgrim rig assembled from parts + bones at 1x (12 m = 768 px) on the pad beside the surveyor; no face (d-101)", 6, 6)
    rows = [bg]
    # (3) every bone clip as a numbered strip (side at 0.5x, top at 0.5x)
    for rig, clip in [(side, c) for c in side["clips"]] + [(top, c) for c in top["clips"]]:
        tfw, tfh, tpiv = (fw, fh, piv) if rig is side else (900, 420, (0.5, 0.5))
        frames = []
        for k in range(clip["frames"]):
            img, w = render(rig, tracks_at(clip, k), tfw, tfh, tpiv)
            allw += w
            frames.append(img[::2, ::2])
        sw_, sh_ = frames[0].shape[1], frames[0].shape[0]
        row = np.tile(paper, (sh_ + 30, W, 1)).astype(np.float32)
        review._label(row, f"{rig['name']} / {clip['name']}  {clip['frames']} frames at {clip['fps']} hz  {'loop' if clip['loop'] else 'once'} (0.5x)", 6, 4)
        for k, im in enumerate(frames):
            if 8 + k * (sw_ + 6) + sw_ > W:
                break
            review._over(row, im, 8 + k * (sw_ + 6), 24)
            review._label(row, str(k), 10 + k * (sw_ + 6), 26)
        rows.append(row)
    # (4) parts with pivots + validation (pack exactly as render.py's rig path does)
    gp = fakegp.FakeGP()
    M = BP.materials_v2(gp)
    imgs, piv_list, names = [], [], []
    pad = 4
    for name, _fn, _pv in BP.RIG_PARTS:
        d = fakegp.FakeDrawing()
        BP.draw_rig_part(d, M, name)
        st = fakegp.strokes_of(d, gp)
        allp = np.vstack([s["xz"] for s in st])
        rmax = max(float(s["radius"].max()) for s in st) * 1.25
        x0, x1 = allp[:, 0].min() - rmax, allp[:, 0].max() + rmax
        z0, z1 = allp[:, 1].min() - rmax, allp[:, 1].max() + rmax
        w_ = -(-(int(np.ceil((x1 - x0) * 64)) + 2 * pad) // 4) * 4
        h_ = -(-(int(np.ceil((z1 - z0) * 64)) + 2 * pad) // 4) * 4
        pv = ((0 - x0) * 64 + pad) / w_, ((0 - z0) * 64 + pad) / h_
        img, _w = GR.render_frame(st, w_, h_, 64, pv, ss=2, seed=1)
        imgs.append(img)
        piv_list.append(pv)
        names.append(name)
    pos, SW, SH = v3.shelf_pack([(im.shape[1], im.shape[0]) for im in imgs])
    sheet = np.zeros((SH, SW, 4), np.uint8)
    parts = []
    for name, im, (px_, ytop), pv in zip(names, imgs, pos, piv_list):
        h_, w_ = im.shape[:2]
        sheet[ytop:ytop + h_, px_:px_ + w_] = im
        parts.append({"name": name, "rect": [px_, SH - (ytop + h_), w_, h_], "pivot": [round(pv[0], 4), round(pv[1], 4)]})
    meta = {"key": "ships/pilgrim/rig", "style": "v3", "ppu": 64, "rect_origin": "bottom_left", "parts": parts, "plants": BP.PILGRIM_RIGS}
    problems = v3.validate_rigset(meta, sheet.shape)
    prow = np.tile(paper, (SH // 2 + 140, W, 1)).astype(np.float32)
    review._over(prow, sheet[::2, ::2], 8, 24)
    for p in parts:
        x_, y_, w_, h_ = p["rect"]
        cx = 8 + int((x_ + p["pivot"][0] * w_) / 2)
        cy = 24 + int((SH - (y_ + h_) + (1 - p["pivot"][1]) * h_) / 2)
        prow[max(cy - 1, 0):cy + 2, max(cx - 4, 0):cx + 5] = (0.85, 0.1, 0.1)
        prow[max(cy - 4, 0):cy + 5, max(cx - 1, 0):cx + 2] = (0.85, 0.1, 0.1)
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    review._label(prow, f"parts sheet {SW}x{SH} (shown 0.5x, pivots red), {len(parts)} parts, one texture + puff = 2 textures; "
                        f"rig json {'valid (contract 11.3)' if not problems else 'INVALID: ' + '; '.join(problems)[:90]}", 6, 4)
    review._label(prow, f"measured ink: outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior "
                        f"{min(w[1] for w in inner):.1f}-{max(w[2] for w in inner):.1f} px; sockets {sorted(side['sockets'])}", 6, SH // 2 + 40)
    rows.append(prow)
    review.write(out, np.vstack(rows))
    fakegp.restore()
    print("written", out, "sheet", SW, SH, "problems", problems)
    return problems


if __name__ == "__main__":
    main(sys.argv[1])
