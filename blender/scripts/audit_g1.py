"""B-182: the G1 art audit (B-173's pattern for the smooth-ground art, D-161 / D-162). One stamped sheet per inner planet,
read back from Assets/_Game/Art/ at 1x with numpy only (no blender.exe, no export), with every G1 key of that planet:

  bands     terrain/<p>/ground_band*        B-175's band and each variant's (B-178, B-181): surface row, variant, fill
  fills     terrain/<p>/ground_fill*        the cross-section tiles (B-175, the variants' own fills)
  lips      terrain/<p>/ground_lip*         B-175's brink lip and the variants' (B-180)
  decor     terrain/<p>/ground_decor*       the upright decor, B-175's and each variant's
  dig       terrain/<p>/dig_rim, dig_puff (all 8 frames), fill_decor_<n> (D-165's spot features)
  finds     props/<p>/ the B-176 keys (U-158's list): each node full | harvested | glint 1, each pocket, the relics, scan_x

(every terrain json on contract "v3.2 11.9", every props json whose note names B-176). Each tile carries its measured ink
(the export log's line when it has one, else audit_c2's raster estimate), its palette hit (audit_c2.palette), its json fields
(surface row, pivot, clips) and, for frames that do not tile, a 2 px edge check (contract 11.9 / v3.EDGE_MARGIN). The foot
lists every key a json names that is missing on disk (a band's "fill", a lip's "band"), every node without its pocket (and
the reverse), a planet without scan_x, and the outliers (palette < 98 %, raster ink outside 1-4 px, an edge touched).

  python -I audit_g1.py <planet> [<planet> ...]   -> blender/preview/audit_g1_<planet>.png (stamped) + one line per planet
                                                     in coordination/reports/blender/audit_g1.md (replacing that planet's)
"""
import glob
import json
import os
import re
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import audit_c2 as A  # noqa: E402
from meridian import pngio, v3  # noqa: E402
import review  # noqa: E402

ART, PREVIEW, ROOT = A.ART, A.PREVIEW, A.ROOT
REPORT = os.path.join(ROOT, "coordination", "reports", "blender", "audit_g1.md")
W = 2100
LABEL = A.LABEL
SECTIONS = [("bands", "ground bands (b-175 + variants b-178 / b-181), 1x"), ("fills", "ground fills, 1x"), ("lips", "brink lips (b-175 + b-180), 1x"),
            ("decor", "upright decor, 1x"), ("dig", "dig rim, dig puff (8 frames), fill_decor, 1x"),
            ("nodes", "resource nodes (b-176): full | harvested | glint 1, 1x"), ("pockets", "buried pockets (b-176), 1x"),
            ("relics", "relics + scan_x (b-176), 1x")]


def g1_keys(p):
    """-> [(key, json path, meta)] for the planet's G1 keys, sorted by key."""
    out = []
    for js in sorted(glob.glob(os.path.join(ART, "terrain", p, "*.json"))):
        meta = json.load(open(js, encoding="utf-8"))
        if meta.get("style") == "v3" and str(meta.get("contract", "")).startswith("v3.2 11.9"):
            out.append((meta.get("key", A.rel(js)[:-5]), js, meta))
    for js in sorted(glob.glob(os.path.join(ART, "props", p, "*.json"))):
        meta = json.load(open(js, encoding="utf-8"))
        if meta.get("style") == "v3" and "B-176" in str(meta.get("note", "")):
            out.append((meta.get("key", A.rel(js)[:-5]), js, meta))
    return out


def section_of(name):
    for pre, sec in (("ground_band", "bands"), ("ground_fill", "fills"), ("ground_lip", "lips"), ("ground_decor", "decor"),
                     ("dig_", "dig"), ("fill_decor", "dig"), ("node_", "nodes"), ("pocket_", "pockets")):
        if name.startswith(pre):
            return sec
    return "relics"


def edge_touched(frames):
    m = v3.EDGE_MARGIN
    return [i for i, f in enumerate(frames) if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any()]


def tile_g1(key, js, meta, planet):
    """-> (section, rgba uint8, caption, edge frames)."""
    d, stem = os.path.dirname(js), os.path.basename(js)[:-5]
    name = key.rsplit("/", 1)[1]
    sheet = pngio.read_png_np(os.path.join(d, stem + "_color.png"))
    hit, off = A.palette(sheet, planet)
    pal = f"palette {hit * 100:.1f}%" + (f" off {' '.join(off[:3])}" if hit < 0.98 and off else "")
    ink = A.logged_ink().get(key) or A.raster_ink(sheet)
    frames = [A.frame_of(sheet, meta, i) for i in range(meta["frames"])]
    del sheet
    starts = {a["name"]: a["start"] for a in meta.get("animations", [])}
    fields = []
    if "surface_row" in meta:
        fields.append(f"surface row {meta['surface_row']}")
    fields.append(f"pivot {meta['pivot'][0]:g},{meta['pivot'][1]:.3g}")
    clips = ", ".join(f"{a['name']} {a['length']}" for a in meta.get("animations", []))
    if clips:
        fields.append("clips " + clips)
    for f in ("variant", "fill", "band"):
        if meta.get(f):
            fields.append(f"{f} {meta[f]}")
    sec = section_of(name)
    if sec == "nodes":
        img = A.hcat([frames[starts.get("full", 0)], frames[starts.get("harvested", 1)], frames[starts.get("glint", 2)]], 6)
    elif name == "vault_door" and "open" in starts:
        last = next(a for a in meta["animations"] if a["name"] == "open")
        img = A.hcat([frames[starts.get("closed", 0)], frames[last["start"] + last["length"] - 1]], 6)
        fields.append("closed | open (last)")
    elif name == "dig_puff":
        img = A.hcat(frames, 4)
    else:
        img = frames[0].copy()
    tiling = bool(meta.get("tile_x") or meta.get("tile_y")) or name == "dig_rim"
    edge = [] if tiling else edge_touched(frames)
    cap = f"{'; '.join(fields)}; ink {ink}; {pal}" + (f"; EDGE {edge}" if edge else "")
    return sec, img, cap, edge


def missing_names(p, keys):
    """Keys a json names that are not on disk, node / pocket pairs, scan_x."""
    names = {k.rsplit("/", 1)[1] for k, _j, _m in keys}
    miss = []
    for k, js, meta in keys:
        d = os.path.dirname(js)
        for f in ("fill", "band"):
            if meta.get(f) and not os.path.isfile(os.path.join(d, meta[f] + ".json")):
                miss.append(f"{k} names {f} {meta[f]} (no json)")
    items_n = {n[len("node_"):] for n in names if n.startswith("node_")}
    items_p = {n[len("pocket_"):] for n in names if n.startswith("pocket_")}
    miss += [f"node_{i} without pocket_{i}" for i in sorted(items_n - items_p)]
    miss += [f"pocket_{i} without node_{i}" for i in sorted(items_p - items_n)]
    if "scan_x" not in names:
        miss.append("no scan_x")
    return miss


def audit(planet):
    t0 = time.time()
    keys = g1_keys(planet)
    sky = np.array(v3.hex_rgb(v3.PALETTES[planet]["sky"]), np.uint8)
    tiles, outl = [], []
    for key, js, meta in keys:
        try:
            sec, img, cap, edge = tile_g1(key, js, meta, planet)
        except Exception as e:  # noqa: BLE001
            sec, img, cap, edge = "relics", np.zeros((24, 24, 4), np.uint8), f"UNREADABLE: {type(e).__name__}: {e}"[:120], []
            outl.append(f"{key} unreadable")
        m = re.search(r"palette ([\d.]+)%", cap)
        if m and float(m.group(1)) < 98.0:
            outl.append(f"{key} palette {m.group(1)}%")
        m = re.search(r"raster p25-p75 (\d+)-(\d+) px", cap)
        if m and (int(m.group(2)) > 4 or int(m.group(1)) < 1):
            outl.append(f"{key} ink {m.group(1)}-{m.group(2)} px")
        if edge:
            outl.append(f"{key} touches the {v3.EDGE_MARGIN} px edge (frames {edge})")
        tiles.append((sec, key, img, cap))
    miss = missing_names(planet, keys)
    counts = {s: sum(1 for t in tiles if t[0] == s) for s, _t in SECTIONS}
    rows, y = [], 40
    for sec, title in SECTIONS:
        st = [t for t in tiles if t[0] == sec]
        if not st:
            continue
        rows.append(("title", title, y))
        y += 26
        x, rh = 8, 0
        for _s, key, img, cap in st:
            h, w = img.shape[:2]
            cw = min(max(w, 8 * len(key.split("/", 1)[1]) + 8, 4 * min(len(cap), 120) + 8), W - 16)
            if x + cw > W - 8 and x > 8:
                x, y, rh = 8, y + rh, 0
            rows.append(("tile", (key, img, cap, x, y), 0))
            x += cw + 16
            rh = max(rh, h + 46)
        y += rh + 10
    foot = [f"g1 keys ({len(keys)}): " + ", ".join(f"{s} {counts[s]}" for s, _t in SECTIONS),
            "missing (" + str(len(miss)) + "): " + (", ".join(miss) if miss else "none"),
            "outliers (" + str(len(outl)) + "): " + (", ".join(outl) if outl else "none")]
    wrapped = []
    for ln in foot:
        while len(ln) > 250:
            cut = ln.rfind(", ", 0, 250)
            cut = cut if cut > 0 else 250
            wrapped.append(ln[:cut + 1])
            ln = "    " + ln[cut + 2:]
        wrapped.append(ln)
    H = y + 30 + 16 * len(wrapped) + 30
    canvas = np.empty((H, W, 3), np.uint8)
    canvas[:] = A.PAPER
    review.draw(canvas, f"b-182 g1 audit: {planet}  ({len(keys)} g1 keys, {len(miss)} missing, {len(outl)} outliers) read back from "
                        f"assets/_game/art at 1x", 6, 8, LABEL)
    for kind, a, b in rows:
        if kind == "title":
            review.draw(canvas, a, 6, b, LABEL)
            continue
        key, img, cap, x, yy = a
        h, w = img.shape[:2]
        canvas[yy + 16:yy + 16 + h, x:x + min(w, W - x)] = sky
        A.over_u8(canvas, img, x, yy + 16)
        review.draw(canvas, key.split("/", 1)[1], x, yy, LABEL, scale=2)
        review.draw(canvas, cap[:120], x, yy + 16 + h + 4, LABEL, scale=1)
    for i, ln in enumerate(wrapped):
        review.draw(canvas, ln, 6, y + 16 + 16 * i, LABEL, scale=1)
    newest = max((os.path.getmtime(js) for _k, js, _m in keys), default=0)
    review.draw(canvas, time.strftime("%m-%d %H:%M") + " audit; newest g1 json " + time.strftime("%m-%d %H:%M", time.localtime(newest)),
                2, H - 16, LABEL)
    out = os.path.join(PREVIEW, f"audit_g1_{planet}.png")
    rgba = np.empty((H, W, 4), np.uint8)
    rgba[..., :3] = canvas
    rgba[..., 3] = 255
    pngio.write_png(out, rgba)
    line = (f"- {planet} ({time.strftime('%m-%d %H:%M')}): {len(keys)} G1 keys ("
            + ", ".join(f"{s} {counts[s]}" for s, _t in SECTIONS) + f"); missing: {', '.join(miss) if miss else 'none'}; "
            f"outliers: {', '.join(outl) if outl else 'none'}; sheet blender/preview/audit_g1_{planet}.png")
    print(f"{planet}: {len(keys)} G1 keys, {len(miss)} missing, {len(outl)} outliers, {W}x{H}, {time.time() - t0:.1f}s")
    return line


def write_report(lines):
    head = ("# B-182: the G1 art audit (one line per planet; the sheets are blender/preview/audit_g1_<planet>.png, "
            "built by blender/scripts/audit_g1.py from Assets/_Game/Art)\n\n")
    old = {}
    if os.path.isfile(REPORT):
        for ln in open(REPORT, encoding="utf-8"):
            m = re.match(r"- (\w+) \(", ln)
            if m:
                old[m.group(1)] = ln.rstrip("\n")
    for ln in lines:
        old[re.match(r"- (\w+) \(", ln).group(1)] = ln
    order = ["earth", "mars", "mercury", "venus"]
    with open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write(head + "\n".join(old[p] for p in order if p in old) + "\n")


if __name__ == "__main__":
    write_report([audit(p) for p in sys.argv[1:]])
