"""Lock-free review of the C2 Earth rig plants (build_c2_earth_rigs) for LEAD: each plant ASSEMBLED
from its parts through its bones with Unity's own idle maths (RigSetBuilder.SwayCurve / SquashCurve,
stepped at 12 Hz over two beats; the swap_cycle on the beat), its react state, all six Earth plants
at 1x beside the surveyor, and the whole Earth rig set (snoozle + the five) packed as ONE sheet and
validated against contract §11.3. meridian.fakegp + numpy, no Blender.

  python -I preview_c2_earth_rigs.py <out.png>
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from meridian import fakegp, v3  # noqa: E402

G = fakegp.install()
import build_c2_earth_rigs as R  # noqa: E402
import build_flora_earth_v3 as F  # noqa: E402
import gp_raster as GR  # noqa: E402
import review  # noqa: E402

ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
PPU, FPS = 64, 12
FW, FH, PIV = 160, 96, (0.4, 4 / 96)


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


def depth(plant, bone):
    d, b = 0, bone
    by = {x["name"]: x for x in plant["bones"]}
    while b.get("parent"):
        b = by[b["parent"]]
        d += 1
    return d


def idle_frames(plant):
    period = 120.0 / plant["idle"]["beat_bpm"]
    return max(1, round(period * FPS))


def unity_tracks(plant, t):
    """RigSetBuilder: share * sin(2 pi t / period - depth * 0.35) per bone; the root squashes once a beat."""
    idle = plant["idle"]
    period = 120.0 / idle["beat_bpm"]
    share = idle["amplitude_deg"] / max(1, len(plant["bones"]))
    out = {}
    for b in plant["bones"]:
        tr = {"rot_deg": share * math.sin(2 * math.pi * t / period - depth(plant, b) * 0.35)}
        if b.get("parent") is None and idle.get("squash", 0) > 0:
            s = idle["squash"] * math.sin(2 * math.pi * t / (period * 0.5))
            tr["scale"] = [1.0 / (1.0 + s), 1.0 + s]
        out[b["name"]] = tr
    return out


def cycle_state(plant, t):
    cyc = plant["idle"].get("swap_cycle")
    if not cyc:
        return {}
    total = sum(cyc["beats"])
    beat = (t * plant["idle"]["beat_bpm"] / 60.0) % total
    acc = 0
    for part, n in zip(cyc["sequence"], cyc["beats"]):
        acc += n
        if beat < acc:
            return {cyc["slot"]: part}
    return {cyc["slot"]: cyc["sequence"][-1]}


def react_state(plant):
    r = plant["react"]
    out = dict(r.get("also", {}))
    for slot, parts in plant["swaps"].items():
        if r.get("swap") in parts:
            out[slot] = r["swap"]
    return out


def draw_plant(d, plant, part_fns, mats_fn, M, tracks, states):
    by_bone_slot = {s["bone"]: s["slot"] for s in plant.get("slots", []) if s.get("replaces_part")}
    world = {}
    items = []
    lengths = {b["name"]: b.get("length", 0.5) for b in plant["bones"]}
    for i, b in enumerate(plant["bones"]):
        # contract §11.3: a bone without offset_m starts at its parent's tip (0, parent length)
        off = b.get("offset_m", [0.0, lengths[b["parent"]]] if b.get("parent") else [0.0, 0.0])
        tr = tracks.get(b["name"], {})
        local = trs(off[0], off[1], tr.get("rot_deg", 0.0), *(tr.get("scale", [1.0, 1.0])))
        world[b["name"]] = local if b.get("parent") is None else compose(world[b["parent"]], local)
        part = states.get(by_bone_slot.get(b["name"]), b["part"])
        items.append((b.get("order", i), i, part, world[b["name"]]))
    for _o, _i, part, m in sorted(items):
        part_fns[part](G.Xf(d, affine(m)), M)


def render_plant(plant, part_fns, mats_fn, tracks, states, fw=FW, fh=FH, piv=PIV, ss=2):
    gp = fakegp.FakeGP()
    M = mats_fn(gp)
    d = fakegp.FakeDrawing()
    draw_plant(d, plant, part_fns, mats_fn, M, tracks, states)
    return fakegp.render(d, gp, fw, fh, pivot=piv, ppu=PPU, ss=ss, seed=5)


def pack_all():
    """Every part of the Earth rig set (snoozle + C2) packed the way render.py's rig path does."""
    imgs, pivs, names = [], [], []
    pad = 4
    for name, fn, mfn in [(n, f, F.mats) for n, f in F.PARTS.items()] + [(n, f, R.mats) for n, f in R.PARTS.items()]:
        gp = fakegp.FakeGP()
        M = mfn(gp)
        d = fakegp.FakeDrawing()
        fn(d, M)
        st = fakegp.strokes_of(d, gp)
        allp = np.vstack([s["xz"] for s in st])
        rmax = max(float(s["radius"].max()) for s in st) * 1.25
        x0, x1 = allp[:, 0].min() - rmax, allp[:, 0].max() + rmax
        z0, z1 = allp[:, 1].min() - rmax, allp[:, 1].max() + rmax
        w_ = -(-(int(np.ceil((x1 - x0) * PPU)) + 2 * pad) // 4) * 4
        h_ = -(-(int(np.ceil((z1 - z0) * PPU)) + 2 * pad) // 4) * 4
        pv = ((0 - x0) * PPU + pad) / w_, ((0 - z0) * PPU + pad) / h_
        img, w = GR.render_frame(st, w_, h_, PPU, pv, ss=2, seed=1)
        imgs.append(img)
        pivs.append(pv)
        names.append(name)
    pos, SW, SH = v3.shelf_pack([(im.shape[1], im.shape[0]) for im in imgs])
    sheet = np.zeros((SH, SW, 4), np.uint8)
    parts = []
    for name, im, (px_, ytop), pv in zip(names, imgs, pos, pivs):
        h_, w_ = im.shape[:2]
        sheet[ytop:ytop + h_, px_:px_ + w_] = im
        parts.append({"name": name, "rect": [px_, SH - (ytop + h_), w_, h_], "pivot": [round(pv[0], 4), round(pv[1], 4)]})
    meta = {"key": "flora/earth/rigset", "style": "v3", "ppu": PPU, "rect_origin": "bottom_left", "parts": parts,
            "plants": R.all_plants()}
    return sheet, meta, v3.validate_rigset(meta, sheet.shape)


PLAINS_H, GROUND_UP = 236, 22          # the painted plains strip; the plants' ground line sits 22 px above its bottom


def plains_strip(W):
    """The B-114 painted plains layers (Art/backgrounds/earth/plains/layer0..2), bottom-aligned and tiled
    to W, read without bpy; a flat placeholder if they are missing."""
    from meridian import pngio
    bg = np.empty((PLAINS_H, W, 3), np.float32)
    bg[:] = np.array(v3.hex_rgb(v3.PALETTES["earth"]["sky"]), np.float32) / 255
    d = os.path.join(ART, "backgrounds", "earth", "plains")
    layers = sorted(f for f in os.listdir(d) if f.startswith("layer") and f.endswith("_color.png")) if os.path.isdir(d) else []
    if not layers:
        bg[PLAINS_H - GROUND_UP:] = np.array(v3.hex_rgb(v3.PALETTES["earth"]["green"]), np.float32) / 255
        return bg, "placeholder ground"
    for f in layers:
        img = pngio.read_png_np(os.path.join(d, f)).astype(np.float32) / 255
        lh, lw = img.shape[:2]
        img = np.tile(img, (1, -(-W // lw), 1))[:, :W]
        if lh > PLAINS_H:
            img = img[lh - PLAINS_H:]
        y = PLAINS_H - img.shape[0]
        a = img[..., 3:4]
        bg[y:] = img[..., :3] * a + bg[y:] * (1 - a)
    return bg, f"{len(layers)} painted plains layers"


def surveyor_frame():
    from meridian import pngio
    sm = json.load(open(os.path.join(ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
    sh = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))
    return sh[:sm["frame_height"], :sm["frame_width"]], sm.get("pivot", [0.5, 0.0])


def on_plains(can, x, plains, items, surveyor):
    """Paste a plains crop at x and stand the plant images (1x, pivot PIV) + the surveyor on one ground line."""
    pw = 40 + sum(FW - 30 for _ in items) + (surveyor[0].shape[1] if surveyor else 0)
    can[22:22 + PLAINS_H, x:x + pw] = plains[:, x:x + pw]
    ground = 22 + PLAINS_H - GROUND_UP
    cx = x + 20
    for img in items:
        review._over(can, img, cx, ground - FH + int(round(PIV[1] * FH)))
        cx += FW - 30
    if surveyor:
        fr, piv = surveyor
        review._over(can, fr, cx - 10, ground - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    return pw


def main(out):
    paper = review.PAPER
    sky = np.array([0.62, 0.72, 0.66], np.float32)
    allw = []
    plants = [(p, R.PARTS, R.mats) for p in R.PLANTS]
    nmax = max(idle_frames(p) for p, _f, _m in plants)
    ncyc = max(len(dict.fromkeys(p["idle"].get("swap_cycle", {}).get("sequence", []))) for p, _f, _m in plants)
    X_REST = 8 + 40 + (FW - 30) + 192 + 16
    X_IDLE = X_REST + 2 * (FW * 2 + 10) + 6
    X_CYC = X_IDLE + nmax * (FW + 4) + 16
    W = max(X_CYC + ncyc * (FW + 4) + 8, 8 + 40 + 6 * (FW - 30) + 200)
    plains, note = plains_strip(W)
    try:
        surveyor = surveyor_frame()
    except Exception as e:  # noqa: BLE001
        surveyor = None
        note += f"; surveyor unavailable ({type(e).__name__})"
    rows = []
    # (1) all six Earth plants at 1x on the painted plains beside the surveyor
    top = np.tile(paper, (PLAINS_H + 26, W, 1)).astype(np.float32)
    review._label(top, f"c2 earth rig plants: the five c2 plants + the snoozle at 1x on the b-114 plains ({note}), beside the surveyor (frame 0, 1x)", 6, 4)
    lineup = []
    for plant, fns, mfn in [(R.snoozle_plant(), F.PARTS, F.mats)] + plants:
        img, w = render_plant(plant, fns, mfn, {}, {})
        lineup.append(img)
    on_plains(top, 8, plains, lineup, surveyor)
    rows.append(top)
    # (2) per plant: 1x on the plains beside the surveyor, rest 2x, react 2x, the idle loop at 1x frame by
    # frame (Unity's maths), and the swap_cycle states at 1x
    for plant, fns, mfn in plants:
        n = idle_frames(plant)
        row = np.tile(sky, (PLAINS_H + 26, W, 1)).astype(np.float32)
        row[:, :X_REST - 8] = paper
        rest1, _w = render_plant(plant, fns, mfn, {}, {})
        on_plains(row, 8, plains, [rest1], surveyor)
        review._label(row, "1x on the plains", 10, 24, scale=1)
        idle = plant["idle"]
        cyc = idle.get("swap_cycle")
        review._label(row, (f"{plant['name']} ({', '.join(plant['biomes'])}): {len(plant['bones'])} bones, sway {idle['amplitude_deg']} deg at "
                            f"{idle['beat_bpm']} bpm, squash {idle['squash']}" + (f", swap_cycle {cyc['slot']} {cyc['beats']}" if cyc else "")
                            + f"; react: {plant['react']['swap']}" + (" + also " + ", ".join(plant["react"]["also"]) if plant["react"].get("also") else "")), 6, 4)
        rest, w = render_plant(plant, fns, mfn, {}, {})
        allw += w
        rea, w = render_plant(plant, fns, mfn, {}, react_state(plant))
        allw += w
        review._over(row, np.repeat(np.repeat(rest, 2, 0), 2, 1), X_REST, 22)
        review._label(row, "rest 2x", X_REST + 2, 24, scale=1)
        review._over(row, np.repeat(np.repeat(rea, 2, 0), 2, 1), X_REST + FW * 2 + 10, 22)
        review._label(row, "react 2x", X_REST + FW * 2 + 12, 24, scale=1)
        x0 = X_IDLE
        for i in range(n):
            t = i / FPS
            img, w = render_plant(plant, fns, mfn, unity_tracks(plant, t), cycle_state(plant, t))
            allw += w
            review._over(row, img, x0 + i * (FW + 4), 22 + FH)
            review._label(row, str(i), x0 + i * (FW + 4) + 2, 24 + FH, scale=1)
        review._label(row, f"idle loop, {n} frames at 12 hz = two beats (1x)", x0, 30, scale=1)
        if cyc:
            seen = list(dict.fromkeys(cyc["sequence"]))
            review._label(row, f"swap_cycle {cyc['slot']}: " + " > ".join(f"{p.split('_', 1)[1]} {b}" for p, b in zip(cyc["sequence"], cyc["beats"]))
                          + " beats (1x)", X_CYC, 30, scale=1)
            for j, part in enumerate(seen):
                img, w = render_plant(plant, fns, mfn, {}, {cyc["slot"]: part})
                allw += w
                review._over(row, img, X_CYC + j * (FW + 4), 22 + FH)
                review._label(row, part.split("_", 1)[1][:24], X_CYC + j * (FW + 4) + 2, 24 + FH, scale=1)
        rows.append(row)
    # (3) the whole Earth rig set as one sheet
    sheet, meta, problems = pack_all()
    SH, SW = sheet.shape[:2]
    prow = np.tile(paper, (SH + 70, W, 1)).astype(np.float32)
    review._over(prow, sheet, 8, 24)
    for p in meta["parts"]:
        x_, y_, w_, h_ = p["rect"]
        cx = 8 + int(x_ + p["pivot"][0] * w_)
        cy = 24 + int(SH - (y_ + h_) + (1 - p["pivot"][1]) * h_)
        prow[max(cy - 1, 0):cy + 2, max(cx - 3, 0):cx + 4] = (0.85, 0.1, 0.1)
        prow[max(cy - 3, 0):cy + 4, max(cx - 1, 0):cx + 2] = (0.85, 0.1, 0.1)
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    review._label(prow, f"flora/earth/rigset with all six plants: ONE sheet {SW}x{SH} at 1x (pivots red), {len(meta['parts'])} parts, "
                        f"bones {[len(p['bones']) for p in meta['plants']]} (cap 6); rig json "
                        f"{'valid (contract 11.3)' if not problems else 'INVALID: ' + '; '.join(problems)[:120]}", 6, 4)
    review._label(prow, f"measured ink: outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior "
                        f"{min(w[1] for w in inner):.1f}-{max(w[2] for w in inner):.1f} px; no faces (d-101); sources + previews only, no export (lead cycle 246)",
                  6, SH + 34)
    rows.append(prow)
    review.write(out, np.vstack(rows))
    fakegp.restore()
    print("written", out, "sheet", SW, SH, "parts", len(meta["parts"]), "problems", problems)
    return problems


if __name__ == "__main__":
    main(sys.argv[1])
