"""Contract v3.0 §11 constants and validators for cartoon assets (no bpy; B-110).

Change only when coordination/ASSET_CONTRACT.md §11 changes.
"""
import math
import os

import numpy as np

CONTRACT = "3.0"
PPU = 64
FPS = 12
GUTTER = 4
MAX_SHEET = 2048
MAX_FILE_BYTES = 4 * 1024 * 1024
INK = "#1E1A17"
OUTER_PX = (2.0, 3.0)          # outer silhouette width at 1x (v3.1, D-100; v3.0 was 4-6)
INNER_PX = (1.0, 1.5)          # interior lines (v3.1; v3.0 was 1.5-3)
OUTER_SPLIT = 1.9              # a stroke nominally >= this wide is silhouette ink (nominal 2.5 vs 1.25)
EDGE_MARGIN = 2                # px kept clear at each frame edge (nothing clipped)

# Bible §9.1 planet palettes (8 colours, strip order). ui/palettes/<planet>/strip is exported from these.
PALETTES = {
    "earth": {
        "offwhite": "#F2E6CF", "red": "#C8553D", "mustard": "#D9A93F", "teal": "#3E8A86",
        "green": "#7A9A5B", "sky": "#9FB7B9", "brown": "#5B4636", "ink": "#1E1A17",
    },
}
PALETTE_ORDER = ["offwhite", "red", "mustard", "teal", "green", "sky", "brown", "ink"]

# §11.2 frame caps per clip (min, max); anything else is a one-off special (<= 16).
CAPS = {"idle": (8, 12), "walk": (12, 16), "run": (12, 16), "fly": (12, 16), "swim": (12, 16),
        "jump": (8, 10), "land": (8, 10)}
SPECIAL_MAX = 16
MAX_BONES = 6


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(c):
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in c[:3])


def shadow_of(h, planet="earth"):
    """The mid shadow tone of a colour: 70 % colour + 30 % the planet's shadow brown (v3.0's one tone)."""
    a, b = hex_rgb(h), hex_rgb(PALETTES[planet]["brown"])
    return rgb_hex([0.7 * x + 0.3 * y for x, y in zip(a, b)])


def deep_of(h, planet="earth"):
    """The deep shadow tone (v3.1, D-100: up to two shadow tones per colour): 45 % colour + 55 % brown."""
    a, b = hex_rgb(h), hex_rgb(PALETTES[planet]["brown"])
    return rgb_hex([0.45 * x + 0.55 * y for x, y in zip(a, b)])


V2_SUFFIXES = (".glb", "_normal.png", "_mask.png", "_emission.png")


def remove_v2(dest, variant, dry_run=False):
    """D-117 / D-119: a v3 sheet replacing a v2 model under one key removes <variant>.glb + its normal/mask/emission
    maps (ArtImporter un-addresses a colour map beside a .glb, IsModelKey). Never touches the colour map, the json
    or any .meta (UNITY's, D-016). Returns the basenames removed (or that would be, with dry_run)."""
    out = []
    for suffix in V2_SUFFIXES:
        p = os.path.join(dest, variant + suffix)
        if os.path.isfile(p):
            if not dry_run:
                os.remove(p)
            out.append(os.path.basename(p))
    return out


def palette_with_shadows(planet="earth"):
    pal = PALETTES[planet]
    out = dict(pal)
    for k, v in pal.items():
        if k != "ink":
            out[k + "_shadow"] = shadow_of(v, planet)
            out[k + "_deep"] = deep_of(v, planet)
    return out


def cap_of(name):
    return CAPS.get(name, (1, SPECIAL_MAX))


def columns_for(fw, n):
    return max(1, min(n, (MAX_SHEET + GUTTER) // (fw + GUTTER)))


def sheet_size(meta):
    cols, n = meta["columns"], meta["frames"]
    rows = math.ceil(n / cols)
    c = min(cols, n)
    g = meta.get("gutter", GUTTER)
    return c * meta["frame_width"] + (c - 1) * g, rows * meta["frame_height"] + (rows - 1) * g


def validate_sheet(meta, png_shape=None, ppu=PPU):
    """Problems with a §11.2 sheet json (and the PNG's HxW if given); [] = valid."""
    p = []
    need = ["key", "style", "frame_width", "frame_height", "columns", "frames", "fps", "pivot",
            "facing", "ppu", "animations"]
    for k in need:
        if k not in meta:
            p.append(f"missing '{k}'")
    if p:
        return p
    if meta["style"] != "v3":
        p.append("style must be 'v3'")
    if meta["fps"] != FPS:
        p.append(f"fps {meta['fps']} (must be {FPS})")
    if meta["ppu"] != ppu:
        p.append(f"ppu {meta['ppu']} (must be {ppu})")
    if meta["facing"] not in ("right", "left"):
        p.append("facing must be right or left")
    fw, fh = meta["frame_width"], meta["frame_height"]
    if fw % 4 or fh % 4:
        p.append(f"frame {fw}x{fh} not a multiple of 4 (BC7 blocks)")
    pv = meta["pivot"]
    if len(pv) != 2 or not all(0.0 <= v <= 1.0 for v in pv):
        p.append(f"pivot {pv} outside 0..1")
    start = 0
    for a in meta["animations"]:
        lo, hi = cap_of(a["name"])
        if a["start"] != start:
            p.append(f"clip {a['name']} starts at {a['start']}, expected {start} (row-major, in order)")
        if not lo <= a["length"] <= hi:
            p.append(f"clip {a['name']} has {a['length']} frames (cap {lo}-{hi})")
        if not isinstance(a.get("loop"), bool):
            p.append(f"clip {a['name']} loop must be true/false")
        if a.get("loop") and not 0 <= a.get("loop_from", 0) < a["length"]:
            p.append(f"clip {a['name']} loop_from outside the clip")
        start += a["length"]
    if start != meta["frames"]:
        p.append(f"frames {meta['frames']} != sum of clip lengths {start}")
    w, h = sheet_size(meta)
    if w > MAX_SHEET or h > MAX_SHEET:
        p.append(f"sheet {w}x{h} over {MAX_SHEET}")
    if png_shape is not None and tuple(png_shape[:2]) != (h, w):
        p.append(f"png is {png_shape[1]}x{png_shape[0]}, json implies {w}x{h}")
    return p


def validate_rigset(meta, png_shape=None):
    """Problems with a §11.3 rig set json; [] = valid. Rects are [x, y, w, h] in px with the
    origin at the sheet's bottom-left (Unity sprite rects); pivots are 0..1 inside the rect."""
    p = []
    for k in ("key", "style", "ppu", "parts", "plants"):
        if k not in meta:
            p.append(f"missing '{k}'")
    if p:
        return p
    if meta["style"] != "v3" or meta["ppu"] != PPU:
        p.append("style v3 / ppu 64 required")
    names = set()
    H, W = (png_shape[:2] if png_shape is not None else (MAX_SHEET, MAX_SHEET))
    if W > MAX_SHEET or H > MAX_SHEET:
        p.append(f"rig sheet {W}x{H} over {MAX_SHEET}")
    for part in meta["parts"]:
        x, y, w, h = part["rect"]
        if x < 0 or y < 0 or x + w > W or y + h > H:
            p.append(f"part {part['name']} rect {part['rect']} outside the {W}x{H} sheet")
        if not all(0.0 <= v <= 1.0 for v in part["pivot"]):
            p.append(f"part {part['name']} pivot outside 0..1")
        if part["name"] in names:
            p.append(f"duplicate part {part['name']}")
        names.add(part["name"])
    for pl in meta["plants"]:
        bones = pl.get("bones", [])
        if not 1 <= len(bones) <= MAX_BONES:
            p.append(f"plant {pl['name']}: {len(bones)} bones (1-{MAX_BONES})")
        bn = [b["name"] for b in bones]
        roots = [b for b in bones if b.get("parent") is None]
        if len(roots) != 1:
            p.append(f"plant {pl['name']}: {len(roots)} root bones (need 1)")
        for b in bones:
            if b.get("parent") is not None and b["parent"] not in bn:
                p.append(f"plant {pl['name']}: bone {b['name']} parent {b['parent']} missing")
            if b.get("part") and b["part"] not in names:
                p.append(f"plant {pl['name']}: bone {b['name']} part {b['part']} missing")
        for slot, opts in pl.get("swaps", {}).items():
            for o in opts:
                if o not in names:
                    p.append(f"plant {pl['name']}: swap {slot}/{o} is not a part")
        idle = pl.get("idle", {})
        if idle and not 100 <= idle.get("beat_bpm", 0) <= 120:
            p.append(f"plant {pl['name']}: beat {idle.get('beat_bpm')} bpm outside 100-120 (Bible §9.2)")
    return p


def shelf_pack(sizes, gutter=GUTTER):
    """sizes [(w, h)] -> (positions [(x, y_top)], W, H): shelf packing, tallest first, in the
    smallest of 256/512/1024/2048 widths that fits, dimensions rounded up to multiples of 4."""
    order = sorted(range(len(sizes)), key=lambda i: -sizes[i][1])
    for W in (256, 512, 1024, 2048):
        if max(w for w, _ in sizes) > W:
            continue
        pos = [None] * len(sizes)
        x = y = shelf = 0
        for i in order:
            w, h = sizes[i]
            if x and x + w > W:
                x, y = 0, y + shelf + gutter
                shelf = 0
            pos[i] = (x, y)
            x += w + gutter
            shelf = max(shelf, h)
        H = y + shelf
        if H <= MAX_SHEET and (H <= W or W == MAX_SHEET):
            used_w = max(px + sizes[i][0] for i, (px, _) in enumerate(pos))
            return pos, -(-used_w // 4) * 4, -(-H // 4) * 4
    raise ValueError("rig parts do not fit one 2048 sheet")


def palette_hits(rgba, planet="earth", tol=6, tints=()):
    """Share of solid interior pixels (alpha 255, 3x3 uniform) that are palette colours or their
    one shadow tone, and the off-palette colours found (most common first)."""
    a = rgba[..., 3] == 255
    rgb = rgba[..., :3].astype(np.int32)
    same = a.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            sh = np.roll(np.roll(rgb, dy, 0), dx, 1)
            same &= (np.abs(sh - rgb).sum(-1) == 0) & np.roll(np.roll(a, dy, 0), dx, 1)
    px = rgb[same]
    if len(px) == 0:
        return 1.0, []
    pal = np.array([hex_rgb(v) for v in palette_with_shadows(planet).values()], np.int32)
    for name, alpha in tints:                 # flat translucent washes (D-096 glass): colour x (1-a) + tint x a
        t = np.array(hex_rgb(PALETTES[planet][name]), np.float64)
        pal = np.vstack([pal, np.rint(pal * (1 - alpha) + t * alpha).astype(np.int32)])
    d = np.abs(px[:, None, :] - pal[None, :, :]).max(-1).min(-1)
    bad = px[d > tol]
    off = []
    if len(bad):
        u, c = np.unique(bad, axis=0, return_counts=True)
        off = [rgb_hex(u[i]) for i in np.argsort(-c)[:5]]
    return float((d <= tol).mean()), off
