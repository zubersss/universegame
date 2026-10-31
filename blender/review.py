"""Review composites for exported art, stamped so nobody reviews a stale image (LEAD, B-026).

Every panel gets a stamp in its corner: the source PNG's modification time and the first 8 hex
of its SHA-256, plus a red STALE banner when render.py listed the key in preview/STALE.txt
(the latest render failed, so the file on disk is from an earlier one).

  blender --background --factory-startup --python blender/review.py -- stack <art dir> <out.png>
      parallax layers layer0..2 composited, 2x wrap, half size (backgrounds)
  blender --background --factory-startup --python blender/review.py -- frames <art dir> <variant> <out.png> 0,8,17,27
      chosen sheet frames: flat albedo row + relit row (creatures, fx)
"""
import hashlib
import json
import os
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
import numpy as np  # noqa: E402

from meridian import pngio, post  # noqa: E402

STALE = os.path.join(HERE, "preview", "STALE.txt")
ART = os.path.normpath(os.path.join(HERE, "..", "Assets", "_Game", "Art"))

# 3x5 bitmap glyphs, rows top to bottom.
FONT = {
    "0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111",
    "4": "101101111001001", "5": "111100111001111", "6": "111100111101111", "7": "111001001001001",
    "8": "111101111101111", "9": "111101111001111", "a": "010101111101101", "b": "110101110101110",
    "c": "111100100100111", "d": "110101101101110", "e": "111100110100111", "f": "111100110100100",
    ":": "000010000010000", "-": "000000111000000", " ": "000000000000000", "S": "111100111001111",
    "T": "111010010010010", "A": "010101111101101", "L": "100100100100111", "E": "111100110100111",
}


def stale_keys():
    if not os.path.isfile(STALE):
        return set()
    with open(STALE, encoding="utf-8") as fh:
        return {ln.split(" | ")[0] for ln in fh.read().splitlines() if ln.strip()}


def key_of(path):
    """Art path -> manifest key (cat/name/variant)."""
    rel = os.path.relpath(path, ART).replace("\\", "/")
    cat, name, fname = rel.split("/")[:3]
    variant = fname.rsplit("_", 1)[0]
    return f"{cat}/{name}/{variant}"


def stamp_text(path):
    with open(path, "rb") as fh:
        h = hashlib.sha256(fh.read()).hexdigest()[:8]
    t = time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(path)))
    return f"{t} {h}"


def draw(img, text, x, y, color, scale=2):
    """Blit `text` into float RGB img at (x, y) top-left, on a dark backing box."""
    w = (len(text) * 4 + 1) * scale
    h = 7 * scale
    img[y:y + h, x:x + w] = img[y:y + h, x:x + w] * 0.25
    for i, ch in enumerate(text):
        g = FONT.get(ch, FONT[" "])
        for r in range(5):
            for c in range(3):
                if g[r * 3 + c] == "1":
                    yy, xx = y + (r + 1) * scale, x + (i * 4 + c + 1) * scale
                    img[yy:yy + scale, xx:xx + scale] = color


def stamp(img, path, stale):
    """Stamp time + hash bottom-left; STALE banner top-left when the latest render failed."""
    H = img.shape[0]
    draw(img, stamp_text(path), 2, H - 16, (1.0, 1.0, 0.85))
    if key_of(path) in stale:
        draw(img, "STALE", 2, 2, (1.0, 0.15, 0.1), scale=4)


def write(out, rgb):
    pngio.write_png(out, np.dstack([pngio.to_u8(np.clip(rgb, 0, 1)), np.full(rgb.shape[:2], 255, np.uint8)]))


def stack(d, out):
    stale = stale_keys()
    acc, panels = None, []
    for i in range(3):
        p = os.path.join(d, f"layer{i}_color.png")
        img = pngio.read_png(p)
        acc = img[..., :3].copy() if acc is None else acc * (1 - img[..., 3:4]) + img[..., :3] * img[..., 3:4]
        panels.append(p)
    acc = np.hstack([acc, acc])[::2, ::2].copy()              # 2x wrap, half size
    for i, p in enumerate(panels):                              # one stamp per layer, stacked up
        sub = acc[: acc.shape[0] - 18 * (2 - i)]
        stamp(sub, p, stale)
    write(out, acc)
    print("REVIEW stack ok", out)


def frames(d, v, out, pick):
    stale = stale_keys()
    cpath = os.path.join(d, f"{v}_color.png")
    meta = json.load(open(os.path.join(d, f"{v}.json"), encoding="utf-8"))
    c = pngio.to_u8(pngio.read_png(cpath))
    n = pngio.to_u8(pngio.read_png(os.path.join(d, f"{v}_normal.png")))
    ep = os.path.join(d, f"{v}_emission.png")
    e = pngio.to_u8(pngio.read_png(ep)) if os.path.exists(ep) else np.zeros_like(c)
    fw, cols, g = meta["frame_width"], meta["columns"], meta["gutter"]
    bg = np.array([0.55, 0.62, 0.70], np.float32)
    rows = []
    for lit in (False, True):
        row = []
        for i in pick:
            r, cc = divmod(i, cols)
            sl = (slice(r * (fw + g), r * (fw + g) + fw), slice(cc * (fw + g), cc * (fw + g) + fw))
            img = post.relight(c[sl], n[sl]) if lit else c[sl]
            f = img.astype(np.float32) / 255
            a = f[..., 3:4]
            row.append(np.clip(f[..., :3] * a + bg * (1 - a) + e[sl][..., :3].astype(np.float32) / 255 * 0.8, 0, 1))
        rows.append(np.hstack(row))
    out_img = np.vstack(rows)
    stamp(out_img, cpath, stale)
    write(out, out_img)
    print("REVIEW frames ok", out)


def tiles(out, dirs):
    """Terrain atlases side by side at half size (over a dark ground), one stamp each."""
    stale = stale_keys()
    panels = []
    for p in dirs:                                     # colour PNG paths (terrain/<planet>/<set>_color.png)
        img = pngio.read_png(p)
        rgb = (img[..., :3] * img[..., 3:4] + 0.1 * (1 - img[..., 3:4]))[::2, ::2].copy()
        stamp(rgb, p, stale)
        panels.append(rgb)
    write(out, np.hstack(panels))
    print("REVIEW tiles ok", out)


def sprites(out, paths):
    """Prop sprites over a neutral backdrop, bottom-aligned side by side; emission added on
    top when present; one stamp per sprite."""
    stale = stale_keys()
    imgs = [pngio.read_png(p) for p in paths]
    H = max(i.shape[0] for i in imgs)
    bg = np.array([0.55, 0.62, 0.70], np.float32)
    panels = []
    for p, img in zip(paths, imgs):
        h, w = img.shape[:2]
        rgb = img[..., :3] * img[..., 3:4] + bg * (1 - img[..., 3:4])
        ep = p.replace("_color.png", "_emission.png")
        if os.path.exists(ep):
            rgb = np.clip(rgb + pngio.read_png(ep)[..., :3] * 0.8, 0, 1)
        panel = np.tile(bg, (H, w + 8, 1)).astype(np.float32)
        panel[H - h:, 4:4 + w] = rgb
        stamp(panel, p, stale)
        panels.append(panel)
    write(out, np.hstack(panels))
    print("REVIEW sprites ok", out)


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if a[0] == "sprites":
        sprites(a[1], a[2:])
    elif a[0] == "tiles":
        tiles(a[1], a[2:])
    elif a[0] == "stack":
        stack(a[1], a[2])
    elif a[0] == "frames":
        frames(a[1], a[2], a[3], [int(x) for x in a[4].split(",")])
    else:
        raise SystemExit(__doc__)
