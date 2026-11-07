"""B-138: read-only edge audit of every committed v3 sheet (contract §11.2 sheets with frames) against the 2 px
frame-edge rule that render.py's do_v3_sheet applies today (v3.EDGE_MARGIN): no alpha in the top 2 rows, the left
and right 2 columns (unless the sheet tiles in x), and the bottom 2 rows when the pivot sits above the frame bottom
(a pivot at the feet stands on the ground line, so the bottom edge is the ground's business). Rig sets (parts + rects)
have no frames and are listed as n/a. numpy only, one sheet in memory at a time (< 100 MB).

  python -I edge_audit.py <report.md>
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio, v3  # noqa: E402

ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))


def frames_of(meta, sheet):
    fw, fh, cols, g = meta["frame_width"], meta["frame_height"], meta["columns"], meta.get("gutter", v3.GUTTER)
    for i in range(meta["frames"]):
        r, c = divmod(i, cols)
        yield i, sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw]


def clip_of(meta, i):
    for a in meta.get("animations", []):
        if a["start"] <= i < a["start"] + a["length"]:
            return f"{a['name']} {i - a['start']}"
    return str(i)


def audit_sheet(js):
    meta = json.load(open(js, encoding="utf-8"))
    png = js[:-5] + "_color.png"
    if not os.path.isfile(png):
        return meta, None, "no colour sheet"
    sheet = pngio.read_png_np(png)
    m = v3.EDGE_MARGIN
    tiles = bool(meta.get("tile") or meta.get("tile_x"))
    low = float(meta.get("pivot", [0.5, 0.0])[1]) > 0 and not tiles
    bad = []
    for i, f in frames_of(meta, sheet):
        a = f[..., 3]
        edges = {"top": int(a[:m].max())}
        if not tiles:
            edges["left"], edges["right"] = int(a[:, :m].max()), int(a[:, -m:].max())
        if low:
            edges["bottom"] = int(a[-m:].max())
        hit = {k: v for k, v in edges.items() if v > 0}
        if hit:
            bad.append((i, hit))
    return meta, bad, None


def audit_parts(meta, png):
    """Rig-set parts (rect [x, y, w, h], origin bottom-left): alpha on a rect's outermost row / column means the part
    was cut at its rect (0 px margin: parts are packed tight, so touching inside is fine, ink AT the border is a cut)."""
    sheet = pngio.read_png_np(png)
    H = sheet.shape[0]
    bad = []
    for p in meta.get("parts", []):
        if "rect" not in p:
            continue
        x, y, w, h = p["rect"]
        a = sheet[H - y - h:H - y, x:x + w, 3]
        if a.size == 0:
            continue
        hit = {k: int(v) for k, v in (("top", a[0].max()), ("bottom", a[-1].max()), ("left", a[:, 0].max()), ("right", a[:, -1].max())) if v > 128}
        if hit:
            bad.append((p["name"], hit))
    return bad


def audit_single(png, pivot_y=0.5, margin=v3.EDGE_MARGIN):
    """A pivot at the base (pivot_y 0) stands on its line, so the bottom edge is not checked (the sheets' rule)."""
    a = pngio.read_png_np(png)[..., 3]
    edges = (("top", a[:margin].max()), ("left", a[:, :margin].max()), ("right", a[:, -margin:].max()))
    if pivot_y > 0:
        edges += (("bottom", a[-margin:].max()),)
    return {k: int(v) for k, v in edges if v > 0}


SINGLE = ("icons/", "planets/saturn/rings_", "ui/hud/escape_sign")   # free-standing images (not tiles, washes or panels)


def main(out):
    rows, na = [], []
    for root, _dirs, files in os.walk(ART):
        for fn in sorted(files):
            if not fn.endswith(".json") or fn.endswith(".meta"):
                continue
            js = os.path.join(root, fn)
            try:
                meta = json.load(open(js, encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if meta.get("style") != "v3":
                continue
            key = os.path.relpath(js, ART).replace("\\", "/")[:-5]
            if "frame_width" not in meta or "frames" not in meta:
                na.append(key + (" (rig set)" if "parts" in meta else " (no frames)"))
                continue
            meta, bad, err = audit_sheet(js)
            rows.append((key, meta, bad, err))
    off = [r for r in rows if r[2]]
    lines = ["# Edge audit 2026-11-07 (B-138)", "",
             "Read-only, from the committed PNGs under Assets/_Game/Art (blender/scripts/edge_audit.py). Rule: v3.EDGE_MARGIN = 2 px "
             "with no alpha at the top, left and right of every frame (left / right skipped for sheets that tile in x), and at the "
             "bottom when the pivot is above the frame bottom; a pivot at the feet leaves the bottom to the ground line.", "",
             f"{len(rows)} sheets audited, {len(off)} with frames touching an edge; {len(na)} v3 files without frames (n/a).", "",
             "| key | frame | frames | pivot | edges checked | offending frames | max alpha per edge |",
             "|---|---|---|---|---|---|---|"]
    for key, meta, bad, err in sorted(rows):
        tiles = bool(meta.get("tile") or meta.get("tile_x"))
        low = float(meta.get("pivot", [0.5, 0.0])[1]) > 0 and not tiles
        checked = "top" + ("" if tiles else ", sides") + (", bottom" if low else "")
        if err:
            lines.append(f"| {key} | {meta.get('frame_width')}x{meta.get('frame_height')} | {meta.get('frames')} | {meta.get('pivot')} | - | {err} | - |")
            continue
        if not bad:
            lines.append(f"| {key} | {meta['frame_width']}x{meta['frame_height']} | {meta['frames']} | {meta.get('pivot')} | {checked} | none | - |")
            continue
        worst = {}
        for _i, hit in bad:
            for k, v in hit.items():
                worst[k] = max(worst.get(k, 0), v)
        names = ", ".join(clip_of(meta, i) for i, _h in bad[:12]) + (f" (+{len(bad) - 12})" if len(bad) > 12 else "")
        lines.append(f"| **{key}** | {meta['frame_width']}x{meta['frame_height']} | {meta['frames']} | {meta.get('pivot')} | {checked} | "
                     f"{len(bad)}: {names} | {', '.join(f'{k} {v}' for k, v in sorted(worst.items()))} |")
    lines += ["", "## Parts and single images", "",
              "Rig-set parts: alpha > 128 on a part rect's outermost row or column (a cut part). Single images (icons, Saturn's ring "
              "parts, the escape sign): any alpha in the 2 px border (the bottom skipped when the pivot is at the base: the sign's post stands on its line). Backgrounds, film overlays, the escape-line tile and the "
              "palette strip are full-bleed by design and not checked.", "",
              "| key | kind | result |", "|---|---|---|"]
    for key in sorted(na):
        k = key.split(" (")[0]
        js = os.path.join(ART, *k.split("/")) + ".json"
        png = js[:-5] + "_color.png"
        if "(rig set)" in key:
            meta = json.load(open(js, encoding="utf-8"))
            if not os.path.isfile(png) or not any("rect" in p for p in meta.get("parts", [])):
                lines.append(f"| {k} | rig set | no packed sheet (parts are separate images) |")
                continue
            bad = audit_parts(meta, png)
            res = "none of {} parts cut".format(len(meta["parts"])) if not bad else "**{} cut**: ".format(len(bad)) + ", ".join(
                f"{n} ({', '.join(f'{e} {v}' for e, v in h.items())})" for n, h in bad[:10])
            lines.append(f"| {k} | rig set | {res} |")
        elif k.startswith(SINGLE) and os.path.isfile(png):
            pv = json.load(open(js, encoding="utf-8")).get("pivot", [0.5, 0.5])
            hit = audit_single(png, float(pv[1]))
            lines.append(f"| {k} | single image | {'clear' if not hit else '**touches** ' + ', '.join(f'{e} {v}' for e, v in hit.items())} |")
    lines += ["", "Full-bleed by design (not checked): " + ", ".join(sorted(x.split(" (")[0] for x in na
                                                                        if "(rig set)" not in x and not x.split(" (")[0].startswith(SINGLE))), ""]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"{len(rows)} sheets, {len(off)} offenders:", [r[0] for r in off])


if __name__ == "__main__":
    main(sys.argv[1])
