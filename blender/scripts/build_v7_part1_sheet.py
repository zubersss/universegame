"""B-258 part 1 (art v7, D-205): THE SHEET of the paint pass, from the files v7_paint_pass.py (paint) wrote into
blender/preview/b258/. numpy only (no bpy): python -I build_v7_part1_sheet.py <review png> [peak MB of the Blender run]

Per piece: the plain render | the painted materials | that plus the edge-softening filter at its three settings, at 2x and
at the game's 96 px per metre on a flat stage tone; the same over the old frame's background
(blender/preview/b251/forest_frame_96_plates.png); the normal map; a piece of the repainted texture at 1:1.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from meridian import pngio  # noqa: E402

D = os.path.normpath(os.path.join(HERE, "..", "preview", "b258"))
OLD = os.path.normpath(os.path.join(HERE, "..", "preview", "b251", "forest_frame_96_plates.png"))
STAGE = np.array([0.665, 0.725, 0.571], np.float32)
SPOT = {"calathea": (1500, 660), "rock": (1660, 668)}      # where a piece's foot stands in the old 96 px frame (px)


def rd(name):
    return pngio.read_png_np(os.path.join(D, name)).astype(np.float32) / 255.0


def on(bg, fg, x, y):
    """fg (straight alpha) over bg (opaque rgb), its top-left at (x, y)."""
    h, w = fg.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, bg.shape[1]), min(y + h, bg.shape[0])
    if x1 > x0 and y1 > y0:
        s = fg[y0 - y:y1 - y, x0 - x:x1 - x]
        bg[y0:y1, x0:x1] = s[..., :3] * s[..., 3:4] + bg[y0:y1, x0:x1] * (1 - s[..., 3:4])
    return bg


def sheet(out, peak=None):
    import review
    rep = json.load(open(os.path.join(D, "part1_report.json"), encoding="utf-8"))
    paper = np.array(review.PAPER, np.float32)
    Wd = 1920
    old = pngio.read_png_np(OLD).astype(np.float32)[..., :3] / 255.0 if os.path.isfile(OLD) else None

    def head(text, h=20):
        hd = np.tile(paper, (h, Wd, 1)).astype(np.float32)
        review._label(hd, text[:310], 6, 4, scale=1)
        return hd

    def cell(fg, label, pad=10):
        c = np.tile(STAGE, (fg.shape[0] + 2 * pad, fg.shape[1] + 2 * pad, 1)).astype(np.float32)
        on(c, fg, pad, pad)
        review._label(c, label, 3, 3, scale=1)
        return c

    def flow(cells, gap=8):
        rows_, cur, x = [], [], 0
        for c in cells:
            if cur and x + c.shape[1] > Wd:
                rows_.append(cur)
                cur, x = [], 0
            cur.append(c)
            x += c.shape[1] + gap
        rows_.append(cur)
        res = []
        for cs in rows_:
            H = max(c.shape[0] for c in cs)
            r = np.tile(paper, (H, Wd, 1)).astype(np.float32)
            x = 0
            for c in cs:
                w = min(c.shape[1], Wd - x)
                r[H - c.shape[0]:, x:x + w] = c[:, :w, :3]
                x += c.shape[1] + gap
            res.append(r)
        return res

    rows = [head("B-258 part 1 (ART v7, the living painting): THE PAINT PASS on real 3D - a CC0 scanned plant and rock (Poly Haven), one sun and sky, Cycles. "
                 "PREVIEW, nothing exported; the raw scans never ship", 26)]
    lines = []
    for pc in rep["pieces"]:
        nm, ks, how = pc["piece"], pc["filter_sizes"], pc["filter"]
        kname = lambda s, i: f"+ the filter, size {s:g}" + ("" if how[i] == "node" else " (numpy classic)")   # noqa: E731
        for sfx, what in (("2x", "at 2x (192 px per metre)"), ("1x", "AT THE GAME'S SIZE (96 px per metre)")):
            cells = [cell(rd(f"{nm}_plain_{sfx}.png"), "plain render"), cell(rd(f"{nm}_painted_{sfx}.png"), "painted materials")]
            cells += [cell(rd(f"{nm}_k{s:g}_{sfx}.png"), kname(s, i)) for i, s in enumerate(ks)]
            cells.append(cell(rd(f"{nm}_brushed_{sfx}.png"), f"filter {ks[0]:g} + BRUSHED EDGE"))
            rows.append(head(f"{nm} {what}: the plain lit render | strokes painted INTO its colour and normal textures | that, plus the edge-softening filter at three settings | the brushed edge"))
            rows += flow(cells)
        if old is not None:
            key = "calathea" if "calathea" in nm else "rock"
            fx, fy = SPOT[key]
            cells = []
            for sfx, k in (("1x", 1), ("2x", 2)):
                for tag, label in (("plain", "plain"), ("painted", "painted"), ("brushed", "painted + filter + brushed edge")):
                    fg = rd(f"{nm}_{tag}_{sfx}.png")
                    px, py = pc["pivot"][0] * fg.shape[1], (1 - pc["pivot"][1]) * fg.shape[0]
                    if key == "rock":                                           # the part of the rock under the ground line is in the ground
                        yy = np.arange(fg.shape[0], dtype=np.float32)[:, None]
                        fg[..., 3] *= np.clip((py + 2 * k - yy) / (3.0 * k), 0, 1)
                    cw, ch = 300, 260
                    bg = old[fy - 240:fy - 240 + ch, fx - cw // 2:fx - cw // 2 + cw].copy()
                    bg = np.repeat(np.repeat(bg, k, 0), k, 1)
                    on(bg, fg, int(round(cw // 2 * k - px)), int(round(240 * k - py)))
                    review._label(bg, f"{label}, {sfx}", 3, 3, scale=1)
                    cells.append(bg)
            rows.append(head(f"{nm} OVER THE OLD FRAME'S BACKGROUND (b251/forest_frame_96_plates.png): at the game's size, then at 2x (the background enlarged)"))
            rows += flow(cells)
        nrm = rd(f"{nm}_normal_2x.png")
        asset = pc["asset"]
        tex = pngio.read_png_np(os.path.join(D, "tex", asset + "_painted_diff.png")).astype(np.float32) / 255.0
        tnr = pngio.read_png_np(os.path.join(D, "tex", asset + "_painted_nor.png")).astype(np.float32) / 255.0
        y0, x0 = tex.shape[0] // 2 - 150, tex.shape[1] // 2 - 240
        rows.append(head(f"{nm}: THE NORMAL MAP at 2x (red = right, green = up, blue = toward the viewer) | the repainted COLOUR texture, a piece at 1:1 | the repainted NORMAL texture, the same piece"))
        rows += flow([cell(nrm, "normal map"), tex[y0:y0 + 300, x0:x0 + 480, :3], tnr[y0:y0 + 300, x0:x0 + 480, :3]])
        w4, h4 = pc["size_4x"]
        s = pc["seconds"]
        lines.append(f"{nm} (x{pc['scale']:g}, {pc['tris']} triangles): sprite {w4 // 4}x{h4 // 4} px at 96 px per metre = {w4 // 4 * (h4 // 4) * 4 / 1024:.0f} KB uncompressed "
                     f"(colour; the normal map the same again); at 2x {w4 // 2}x{h4 // 2} = {w4 // 2 * (h4 // 2) * 4 / 1024:.0f} KB.")
        lines.append(f"   TIME: plain render {s['plain']} s; repainting its two textures with {pc['strokes']} strokes {s['repaint_textures']} s (once per asset); "
                     f"painted render {s['painted']} s; normal map {s['normal']} s; the filter, three settings {s['filter_all']} s ({'/'.join(how)}); "
                     f"the brushed edge {s.get('edge_brush', 0)} s ({pc.get('edge_strokes', 0)} strokes along the contour).")
        sway = os.path.join(D, nm + "_sway.json")
        if os.path.isfile(sway):
            sw = json.load(open(sway, encoding="utf-8"))
            lines.append(f"   SWAY: {len(sw['pieces'])} pieces with a root (the pivot) and a tip each, in {nm}_sway.json; lengths "
                         + ", ".join(f"{p['length_m']:g}" for p in sw["pieces"][:10]) + " m")
    lines.append(f"{rep['blender']}; {rep['engine']}; rendered at 384 px per metre and only ever shrunk."
                 + (f" PEAK RAM of the Blender run that made all of this: {peak} MB." if peak else ""))
    foot = np.tile(paper, (24 + 16 * len(lines), Wd, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:310], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-258 part 1: the paint pass (Blender renders, numpy sheet; nothing exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    sheet(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
