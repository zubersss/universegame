"""B-264 (D-208, contract 12.9): THE TRIMMED PACKER. A frame sheet's drawings are packed CUT TO THEIR INK instead of in
their boxes, and the json says where each cut went and where it sat. numpy only:
    python -I pack_cuts.py prove <folder with <name>.json + <name>_color.png ...> <out folder> [name ...]
    python -I pack_cuts.py pack <sheet png> <sheet json> <out png> <out json>
WRITTEN 11-10 15:2x AS SOURCE, UNRUN (UNITY's want is on file: nothing of mine runs beside it).

A box sheet (contract section 5): frame i of frame_width x frame_height sits at column i % columns, row i // columns, with
`gutter` px between boxes and none round the page. The trimmed page: every drawing's CUT = the smallest rectangle that
holds every pixel of its box that is not wholly zero (so the colour bled under alpha 0 goes with it and nothing is lost),
laid by a shelf packer (tallest first, left to right, unrotated, 4 px gutter) on a page as narrow as packs smallest.
The json keeps the frame BOX (frame_width, frame_height, pivot, animations: as today) and gains
    "cuts": [[x, y, w, h, ox, oy], ...]   one per drawing, in frame order:
        x, y   the cut's top-left on the trimmed page, px from the page's top-left
        w, h   its size (0, 0 = an empty drawing)
        ox, oy where the cut's BOTTOM-LEFT sat inside the box, px from the box's bottom-left (y up, as a sprite's pivot is)
    "page": [width, height], "packed": "cuts"
A normal sheet takes the SAME cuts (pack_with(cuts)). prove: pack, unpack into boxes again, write with the same writer and
compare SHA-256 with the original file: the round trip must be byte for byte; prints the page before and after.
"""
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio  # noqa: E402

GUTTER = 4
WIDTHS = (256, 384, 512, 640, 768, 896, 1024, 1280, 1536, 1792, 2048)


def boxes(meta):
    fw, fh, cols, gut = meta["frame_width"], meta["frame_height"], meta["columns"], meta.get("gutter", 0)
    return [((i % cols) * (fw + gut), (i // cols) * (fh + gut), fw, fh) for i in range(meta["frames"])]


def ink(box):
    """The smallest rectangle holding every pixel that is not wholly zero. -> (x0, y0, w, h) in the box, or None."""
    on = box.any(axis=2)
    if not on.any():
        return None
    ys, xs = np.flatnonzero(on.any(axis=1)), np.flatnonzero(on.any(axis=0))
    return int(xs[0]), int(ys[0]), int(xs[-1] - xs[0] + 1), int(ys[-1] - ys[0] + 1)


def shelf(sizes, width, gutter=GUTTER):
    """Rectangles (w, h) laid tallest first on shelves `width` wide. -> ([(x, y)] in the order given, the height used)
    or None when one does not fit the width."""
    order = sorted(range(len(sizes)), key=lambda i: (-sizes[i][1], -sizes[i][0], i))
    at = [(0, 0)] * len(sizes)
    x = y = row_h = 0
    for i in order:
        w, h = sizes[i]
        if w > width:
            return None
        if w == 0 or h == 0:
            continue
        if x + w > width:
            x, y, row_h = 0, y + row_h + gutter, 0
        at[i] = (x, y)
        x, row_h = x + w + gutter, max(row_h, h)
    return at, y + row_h


def pack(sheet, meta):
    """-> (the trimmed page H x W x 4 uint8, cuts [[x, y, w, h, ox, oy]])."""
    fh = meta["frame_height"]
    rects = []
    for bx, by, bw, bh in boxes(meta):
        r = ink(sheet[by:by + bh, bx:bx + bw])
        rects.append((bx, by, r))
    sizes = [(r[2], r[3]) if r else (0, 0) for _, _, r in rects]
    best = None
    for width in WIDTHS:
        got = shelf(sizes, width)
        if got and (best is None or width * got[1] < best[0] * best[2]):
            best = (width, got[0], got[1])
    if best is None:
        raise SystemExit("pack_cuts: a drawing is wider than the widest page")
    width, at, used = best
    page = np.zeros((max(used, 1), width, 4), np.uint8)
    cuts = []
    for (bx, by, r), (x, y) in zip(rects, at):
        if r is None:
            cuts.append([0, 0, 0, 0, 0, 0])
            continue
        x0, y0, w, h = r
        page[y:y + h, x:x + w] = sheet[by + y0:by + y0 + h, bx + x0:bx + x0 + w]
        cuts.append([x, y, w, h, x0, fh - (y0 + h)])
    return page, cuts


def pack_with(sheet, meta, cuts, page_size):
    """Another map of the same sheet (its normal map) laid by the SAME cuts."""
    fh = meta["frame_height"]
    page = np.zeros((page_size[1], page_size[0], 4), np.uint8)
    for (bx, by, _, _), (x, y, w, h, ox, oy) in zip(boxes(meta), cuts):
        if w and h:
            y0 = fh - oy - h
            page[y:y + h, x:x + w] = sheet[by + y0:by + y0 + h, bx + ox:bx + ox + w]
    return page


def unpack(page, meta, cuts, sheet_size):
    """The box sheet again from a trimmed page and its cuts."""
    fh = meta["frame_height"]
    sheet = np.zeros((sheet_size[1], sheet_size[0], 4), np.uint8)
    for (bx, by, _, _), (x, y, w, h, ox, oy) in zip(boxes(meta), cuts):
        if w and h:
            y0 = fh - oy - h
            sheet[by + y0:by + y0 + h, bx + ox:bx + ox + w] = page[y:y + h, x:x + w]
    return sheet


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def trimmed_meta(meta, cuts, page):
    out = dict(meta)
    out.update({"cuts": cuts, "page": [int(page.shape[1]), int(page.shape[0])], "packed": "cuts"})
    return out


def prove(src, out, names):
    os.makedirs(out, exist_ok=True)
    names = names or sorted(f[:-5] for f in os.listdir(src) if f.endswith(".json") and os.path.isfile(os.path.join(src, f[:-5] + "_color.png")))
    tot0 = tot1 = 0
    ok_all = True
    for name in names:
        meta = json.load(open(os.path.join(src, name + ".json"), encoding="utf-8"))
        sp = os.path.join(src, name + "_color.png")
        sheet = pngio.read_png_np(sp)
        page, cuts = pack(sheet, meta)
        pngio.write_png(os.path.join(out, name + "_color.png"), page)
        with open(os.path.join(out, name + ".json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(trimmed_meta(meta, cuts, page), fh, indent=1)
        back = os.path.join(out, name + "_roundtrip.png")
        pngio.write_png(back, unpack(page, meta, cuts, (sheet.shape[1], sheet.shape[0])))
        same = sha(back) == sha(sp)
        ok_all &= same
        os.remove(back)
        a0, a1 = sheet.shape[0] * sheet.shape[1], page.shape[0] * page.shape[1]
        tot0, tot1 = tot0 + a0, tot1 + a1
        ws = [c[2] for c in cuts if c[2]]
        hs = [c[3] for c in cuts if c[3]]
        print(f"{name}: {meta['frames']} drawings in boxes of {meta['frame_width']} x {meta['frame_height']}: the box sheet {sheet.shape[1]} x {sheet.shape[0]} "
              f"({a0 / 1e6:.2f} Mpx, {a0 * 4 / 1048576:.1f} MB RGBA32) -> trimmed {page.shape[1]} x {page.shape[0]} ({a1 / 1e6:.2f} Mpx, {a1 * 4 / 1048576:.1f} MB) "
              f"= {100.0 * a1 / a0:.0f} % of it; cuts {min(ws)}-{max(ws)} px wide, {min(hs)}-{max(hs)} tall; round trip byte for byte: {'YES' if same else 'NO'}", flush=True)
    print(f"ALL {len(names)} SHEETS: {tot0 / 1e6:.2f} Mpx in boxes -> {tot1 / 1e6:.2f} Mpx trimmed = {100.0 * tot1 / tot0:.0f} %; every round trip identical: {'YES' if ok_all else 'NO'}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "prove":
        sys.exit(prove(sys.argv[2], sys.argv[3], sys.argv[4:]))
    if len(sys.argv) == 6 and sys.argv[1] == "pack":
        meta = json.load(open(sys.argv[3], encoding="utf-8"))
        page, cuts = pack(pngio.read_png_np(sys.argv[2]), meta)
        pngio.write_png(sys.argv[4], page)
        with open(sys.argv[5], "w", encoding="utf-8", newline="\n") as fh:
            json.dump(trimmed_meta(meta, cuts, page), fh, indent=1)
        print("packed", sys.argv[4], page.shape[1], "x", page.shape[0], len(cuts), "cuts")
    else:
        raise SystemExit(__doc__)
