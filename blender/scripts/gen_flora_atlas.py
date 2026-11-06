"""Shared Earth flora atlas (B-085): 2048^2 color/normal/mask/emission, a 4x4 grid of 512 px
material tiles that every flora model UV-maps into (one shared material, contract §9).

Tile index = row * 4 + column, row 0 at the TOP of the image. build_flora.py uses the same
table (TILES) to place each part's UVs inside its tile (with an inset). Each tile is a v1
gen_terrain recipe run at 512 px (gen_terrain3d's scaled recipe), so it is detailed and soft at
its edges; tiles never need to wrap. Pure numpy.
"""
import os

import numpy as np

import gen_terrain3d as G3
from meridian import pngio

N, GRID = 512, 4
TILES = [
    # name           recipe spec                                                                          smooth
    ("bark_oak",     {"recipe": "stone", "dark": [62, 50, 40], "light": [104, 86, 68], "crack_col": [40, 32, 26], "crack_k": 0.7, "strata": [0.0, 64]}, 0.15),
    ("bark_spruce",  {"recipe": "stone", "dark": [70, 52, 40], "light": [112, 86, 64], "crack_col": [44, 32, 24], "crack_k": 0.6}, 0.15),
    ("bark_birch",   {"recipe": "stone", "dark": [190, 186, 176], "light": [236, 232, 222], "crack_col": [40, 38, 36], "crack_k": 0.9}, 0.3),
    ("bark_dead",    {"recipe": "stone", "dark": [104, 98, 90], "light": [150, 144, 134], "crack_col": [64, 60, 56], "crack_k": 0.8}, 0.2),
    ("leaf_oak",     {"recipe": "soil", "dark": [40, 72, 30], "light": [86, 124, 48], "pebble_thresh": 1.4, "pebble_light": [110, 146, 60], "pebble_dark": [30, 56, 26]}, 0.35),
    ("needles",      {"recipe": "soil", "dark": [22, 44, 32], "light": [42, 72, 46], "pebble_thresh": 1.6, "pebble_light": [56, 86, 54], "pebble_dark": [16, 34, 26]}, 0.3),
    ("leaf_birch",   {"recipe": "soil", "dark": [74, 112, 46], "light": [130, 166, 70], "pebble_thresh": 1.4, "pebble_light": [160, 186, 90], "pebble_dark": [60, 92, 40]}, 0.35),
    ("leaf_bush",    {"recipe": "soil", "dark": [52, 74, 34], "light": [94, 116, 56], "pebble_thresh": 1.5, "pebble_light": [118, 138, 66], "pebble_dark": [40, 58, 28]}, 0.3),
    ("rock_grey",    {"recipe": "stone", "dark": [92, 90, 88], "light": [152, 149, 143]}, 0.25),
    ("rock_brown",   {"recipe": "stone", "dark": [104, 86, 70], "light": [158, 134, 110], "pits": True}, 0.2),
    ("rock_moss",    {"recipe": "stone", "dark": [80, 88, 72], "light": [130, 136, 112], "crack_col": [52, 80, 40], "crack_k": 0.8}, 0.2),
    ("grass",        {"recipe": "soil", "dark": [56, 96, 36], "light": [118, 158, 62], "pebble_thresh": 3.0}, 0.3),
    ("cactus",       {"recipe": "sand", "dark": [58, 104, 62], "light": [92, 140, 84]}, 0.35),
    ("berries",      {"recipe": "soil", "dark": [120, 20, 24], "light": [196, 40, 42], "pebble_thresh": 3.0}, 0.6),
    ("grass_dry",    {"recipe": "soil", "dark": [150, 132, 82], "light": [196, 178, 112], "pebble_thresh": 3.0}, 0.2),
    ("leafcards",    {"cards": ["oak", "birch", "bush", "needle"]}, 0.35),     # B-109: 2x2 alpha leaf-cluster cards (was "spare")
]
MARS_TILES = [   # B-089 Mars set (v1 Mars recipes)
    ("rock_rust",   {"recipe": "stone", "dark": [120, 74, 54], "light": [172, 112, 80], "crack_col": [80, 46, 34], "crack_k": 0.5}, 0.2),
    ("rock_basalt", {"recipe": "stone", "dark": [52, 46, 44], "light": [96, 84, 78], "crack_col": [34, 30, 29], "crack_k": 0.5, "pits": True}, 0.25),
    ("regolith",    {"recipe": "soil", "dark": [128, 66, 42], "light": [190, 112, 76], "pebble_light": [176, 128, 98], "pebble_dark": [62, 50, 46], "pebble_thresh": 1.9}, 0.15),
    ("hematite",    {"recipe": "soil", "dark": [84, 44, 38], "light": [132, 70, 56], "pebble_light": [150, 140, 142], "pebble_size": 4, "pebble_thresh": 1.4}, 0.35),
    ("ice",         {"recipe": "stone", "dark": [196, 212, 226], "light": [238, 243, 248], "crack_col": [150, 180, 205], "crack_k": 0.6}, 0.6),
    ("ice_dirty",   {"recipe": "stone", "dark": [190, 170, 160], "light": [232, 222, 214], "crack_col": [150, 110, 90], "crack_k": 0.5}, 0.45),
    ("dust_bush",   {"recipe": "stone", "dark": [96, 66, 50], "light": [150, 110, 82], "crack_col": [60, 40, 30], "crack_k": 0.7}, 0.1),
    ("lavatube",    {"recipe": "stone", "dark": [36, 30, 30], "light": [72, 60, 58], "crack_col": [20, 18, 18], "crack_k": 0.6, "pits": True}, 0.45),
]
# B-101 Mercury scenery (Bible §7.3 look: blinding regolith, black sky; palettes from the B-091 block
# materials and the B-095 solarite). A 4th tuple element is an emission spec: colour (sRGB), which
# part of the tile glows ("light" = the bright areas, "dark" = the dark areas), strength.
MERCURY_TILES = [
    ("regolith",     {"recipe": "soil", "dark": [112, 110, 116], "light": [160, 158, 162], "pebble_light": [186, 184, 188], "pebble_dark": [64, 62, 68], "pebble_thresh": 1.7}, 0.12),
    ("basalt",       {"recipe": "stone", "dark": [52, 50, 56], "light": [86, 82, 90], "crack_col": [32, 30, 34], "crack_k": 0.5, "pits": True}, 0.25),
    ("rim_rock",     {"recipe": "stone", "dark": [124, 120, 126], "light": [178, 174, 178], "crack_col": [70, 66, 72], "crack_k": 0.7, "strata": [0.5, 96]}, 0.18),
    ("impact_glass", {"recipe": "stone", "dark": [18, 16, 24], "light": [72, 62, 84], "crack_col": [164, 150, 184], "crack_k": 0.55}, 0.8),
    ("solarite",     {"recipe": "stone", "dark": [222, 184, 118], "light": [255, 238, 196], "crack_col": [196, 146, 80], "crack_k": 0.4}, 0.65,
                     {"color": [255, 204, 120], "from": "light", "k": 1.0}),
    ("solarite_rock", {"recipe": "stone", "dark": [44, 40, 46], "light": [80, 74, 80], "crack_col": [120, 90, 60], "crack_k": 0.6, "pits": True}, 0.3),
    ("ice",          {"recipe": "stone", "dark": [196, 208, 226], "light": [234, 240, 248], "crack_col": [150, 170, 200], "crack_k": 0.55}, 0.6),
    ("ice_dirty",    {"recipe": "stone", "dark": [150, 156, 168], "light": [204, 208, 216], "crack_col": [110, 116, 130], "crack_k": 0.5}, 0.45),
]
# B-101 Venus surface scenery (§7.4: black glassy surface lit by vents; B-091 Venus palettes).
VENUS_TILES = [
    ("basalt",       {"recipe": "stone", "dark": [36, 32, 30], "light": [74, 64, 58], "crack_col": [20, 18, 18], "crack_k": 0.5, "pits": True}, 0.25),
    ("basalt_column", {"recipe": "stone", "dark": [30, 27, 26], "light": [68, 60, 54], "crack_col": [16, 14, 14], "crack_k": 0.85, "strata": [0.35, 128]}, 0.3),
    ("tessera",      {"recipe": "stone", "dark": [92, 80, 68], "light": [138, 120, 100], "crack_col": [58, 50, 44], "crack_k": 0.75}, 0.2),
    ("sulfur",       {"recipe": "soil", "dark": [168, 146, 70], "light": [212, 192, 110], "pebble_light": [230, 216, 150], "pebble_dark": [138, 108, 50], "pebble_size": 5, "pebble_thresh": 1.6}, 0.2),
    ("vent_glass",   {"recipe": "stone", "dark": [14, 12, 18], "light": [78, 64, 92], "crack_col": [150, 128, 168], "crack_k": 0.45}, 0.7),
    ("vent_mouth",   {"recipe": "stone", "dark": [38, 18, 14], "light": [84, 38, 24], "crack_col": [255, 126, 44], "crack_k": 0.95, "pits": True}, 0.35,
                     {"color": [255, 128, 46], "from": "light", "k": 1.0}),
    ("lava_crust",   {"recipe": "stone", "dark": [24, 21, 21], "light": [58, 49, 46], "crack_col": [92, 44, 26], "crack_k": 0.6, "pits": True}, 0.3),
    ("sulfur_rim",   {"recipe": "soil", "dark": [198, 178, 98], "light": [240, 228, 156], "pebble_light": [250, 244, 206], "pebble_dark": [160, 132, 60], "pebble_size": 4, "pebble_thresh": 1.3}, 0.35),
]
TILE_SETS = {"earth": TILES, "mars": MARS_TILES, "mercury": MERCURY_TILES, "venus": VENUS_TILES}
CURRENT = "earth"                                  # build_flora sets this while building a planet's set
INDEX = {name: i for i, (name, *_) in enumerate(TILES)}


def tile_rect(name, inset=12, sub=None):
    """UV rect (u0, v0, u1, v1) of a tile with an inset in px; UV v=0 is the BOTTOM (Blender).
    `sub` (B-109) picks one quarter of a 2x2 card tile (0 top-left, 1 top-right, 2 bottom-left,
    3 bottom-right, or a card name from the tile's "cards" list); cards map the whole quarter
    (inset 0) because their alpha is already 0 within 14 px of its edge."""
    tiles = TILE_SETS[CURRENT]
    i = [t[0] for t in tiles].index(name)
    r, c = divmod(i, GRID)
    s = N * GRID
    x0, y0, size = c * N, r * N, N
    if sub is not None:
        if isinstance(sub, str):
            sub = tiles[i][1]["cards"].index(sub)
        sr, sc = divmod(int(sub), 2)
        size = N // 2
        x0, y0, inset = x0 + sc * size, y0 + sr * size, 0
    u0 = (x0 + inset) / s
    u1 = (x0 + size - inset) / s
    v1 = 1.0 - (y0 + inset) / s                       # image row 0 = top = v 1
    v0 = 1.0 - (y0 + size - inset) / s
    return u0, v0, u1, v1


# ---------------------------------------------------------------- B-109 leaf-cluster cards

CARD_KINDS = {   # leaf palette (dark, light), leaf length range in px of a 256 card, width/length, count, rim lobes, twig colour
    "oak":    dict(dark=(34, 62, 26), light=(92, 130, 52), L=(30, 44), W=0.55, n=110, lobes=5, twig=(70, 56, 42)),
    "birch":  dict(dark=(66, 104, 42), light=(140, 172, 74), L=(18, 28), W=0.62, n=150, lobes=0, twig=(196, 190, 178)),
    "bush":   dict(dark=(42, 64, 30), light=(104, 126, 60), L=(14, 22), W=0.7, n=190, lobes=0, twig=(66, 52, 40)),
    "needle": dict(dark=(18, 40, 30), light=(48, 80, 52), L=(26, 40), W=0.08, n=260, lobes=0, twig=(78, 58, 44)),
}


def _card(kind, seed, size=256, ss=2):
    """One alpha-cut leaf-cluster card, painted leaf by leaf (back to front) at `ss` x supersample.
    Returns color RGBA, normal RGB (0..1) and mask RGBA, size x size float32. The cluster hangs on a
    twig that enters at the bottom centre (the card's attach point); leaves are ellipses (oak with
    lobed rims, needles as thin strokes along side twigs), each shaded from its own tilt so a card
    reads as many small lit surfaces; alpha is 0 within 14 px of the card edge."""
    K = CARD_KINDS[kind]
    rng = np.random.default_rng(seed)
    S = size * ss
    col = np.zeros((S, S, 3), np.float32)
    hgt = np.zeros((S, S), np.float32)
    nrm = np.zeros((S, S, 3), np.float32)
    nrm[..., 2] = 1.0
    cov = np.zeros((S, S), np.float32)
    dark, light = np.array(K["dark"], np.float32) / 255, np.array(K["light"], np.float32) / 255
    tw = np.array(K["twig"], np.float32) / 255
    up = np.array([0, 0, 1], np.float32)
    cx, cy, R = S * 0.5, S * 0.47, S * 0.36
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)

    def stroke(x0, y0, x1, y1, w, c):
        dx, dy = x1 - x0, y1 - y0
        ln2 = max(dx * dx + dy * dy, 1e-6)
        t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / ln2, 0, 1)
        d = np.hypot(xx - (x0 + t * dx), yy - (y0 + t * dy))
        m = np.clip(w - d + 0.5, 0, 1)[..., None]
        col[:] = col * (1 - m) + c * m
        nrm[:] = nrm * (1 - m) + up * m
        cov[:] = np.maximum(cov, m[..., 0])

    base_y = S * 0.9
    stem_top = (cx + rng.uniform(-0.05, 0.05) * S, cy - R * 0.55)
    stroke(cx, base_y, stem_top[0], stem_top[1], 1.6 * ss, tw)
    twigs = [(cx, base_y, stem_top[0], stem_top[1])]
    for k in range(int(rng.integers(3, 6))):
        f = rng.uniform(0.15, 0.85)
        bx, by = cx + (stem_top[0] - cx) * f, base_y + (stem_top[1] - base_y) * f
        a = rng.uniform(0.35, 1.1) * (1 if k % 2 else -1) - np.pi / 2
        ln = R * rng.uniform(0.45, 0.8)
        ex, ey = bx + np.cos(a) * ln, by + np.sin(a) * ln
        stroke(bx, by, ex, ey, 1.0 * ss, tw)
        twigs.append((bx, by, ex, ey))
    for _k in range(K["n"]):
        if kind == "needle":
            bx, by, ex, ey = twigs[int(rng.integers(len(twigs)))]
            f = rng.uniform(0.05, 1.0)
            px, py = bx + (ex - bx) * f, by + (ey - by) * f
            ang = np.arctan2(ey - by, ex - bx) + rng.choice((-1.0, 1.0)) * rng.uniform(0.5, 1.1)
        else:
            rr = R * np.sqrt(rng.uniform(0, 1)) * 0.95
            th = rng.uniform(0, 2 * np.pi)
            px, py = cx + rr * np.cos(th), cy + rr * np.sin(th) * 0.92
            ang = th + rng.uniform(-0.8, 0.8)                     # leaves point outward from the centre
        L = rng.uniform(*K["L"]) * ss
        W = L * K["W"] * 0.5
        ux, uy = np.cos(ang), np.sin(ang)
        x0, x1 = int(max(0, px - L - 2)), int(min(S, px + L + 2))
        y0, y1 = int(max(0, py - L - 2)), int(min(S, py + L + 2))
        if x1 <= x0 or y1 <= y0:
            continue
        X, Y = xx[y0:y1, x0:x1] - px, yy[y0:y1, x0:x1] - py
        a = X * ux + Y * uy                                        # along the leaf (0 at the petiole)
        b = -X * uy + Y * ux                                       # across it
        s = np.clip(a / L, 0, 1)
        if kind == "needle":
            half = np.maximum(W, 0.7 * ss) * (1 - 0.6 * s)
        else:
            half = W * np.sin(np.pi * s) ** (1.2 if kind == "birch" else 0.8)
            if K["lobes"]:
                half = half * (0.78 + 0.22 * np.abs(np.cos(K["lobes"] * np.pi * s)))
        inside = (a >= 0) & (a <= L)
        m = np.clip(half - np.abs(b) + 0.5, 0, 1) * inside
        if not m.any():
            continue
        tilt = rng.normal(0, 0.45, 2)                              # the leaf's own facing
        n = np.array([tilt[0], -tilt[1], 1.0], np.float32)
        n /= np.linalg.norm(n)
        lit = float(np.clip(0.55 + 0.45 * (0.5 * n[0] + 0.5 * n[1] + 0.7 * n[2]), 0, 1))
        depth = max(0.0, 1 - np.hypot(px - cx, py - cy) / (R * 1.3))   # inner leaves a little darker
        tone = float(np.clip(rng.uniform(0.15, 0.95) * (0.6 + 0.4 * lit) * (0.7 + 0.3 * (1 - depth)), 0, 1))
        c = dark + (light - dark) * tone
        rib = 0.0 if kind == "needle" else np.clip(1 - np.abs(b) / (0.12 * W + 0.6 * ss), 0, 1) * inside
        cc = c[None, None, :] * (1 - 0.25 * np.asarray(rib, np.float32)[..., None] if kind != "needle" else 1)
        mm = m[..., None]
        col[y0:y1, x0:x1] = col[y0:y1, x0:x1] * (1 - mm) + cc * mm
        nrm[y0:y1, x0:x1] = nrm[y0:y1, x0:x1] * (1 - mm) + n * mm
        hgt[y0:y1, x0:x1] = np.maximum(hgt[y0:y1, x0:x1], m * (0.4 + 0.6 * np.sin(np.pi * s)) * (0.5 + 0.5 * depth))
        cov[y0:y1, x0:x1] = np.maximum(cov[y0:y1, x0:x1], m)
    e = np.minimum(np.minimum(xx, S - 1 - xx), np.minimum(yy, S - 1 - yy)) / ss
    cov *= np.clip((e - 14) / 4, 0, 1)

    def down(arr):
        return arr.reshape(size, ss, size, ss, *arr.shape[2:]).mean(axis=(1, 3))
    cov_d = down(cov)
    col_d, nrm_d, hgt_d = down(col * cov[..., None]), down(nrm * cov[..., None]), down(hgt)
    w = np.maximum(cov_d[..., None], 1e-4)
    rgb = np.where(cov_d[..., None] > 1e-4, col_d / w, 0).astype(np.float32)
    nn = np.where(cov_d[..., None] > 1e-4, nrm_d / w, up).astype(np.float32)
    from meridian import post
    known = cov_d >= 0.5
    rgb, k2 = post.dilate(rgb, known, steps=12)                    # colour under the cut so mips never bleed black
    rgb[~k2] = rgb[k2].mean(axis=0) if k2.any() else dark
    nn = nn / np.maximum(np.linalg.norm(nn, axis=-1, keepdims=True), 1e-6)
    nn[cov_d < 0.5] = up
    color = np.dstack([np.clip(rgb, 0, 1), np.clip(cov_d, 0, 1)]).astype(np.float32)
    ao = np.clip(0.75 + 0.25 * hgt_d, 0.6, 1.0).astype(np.float32)
    mask = np.dstack([np.zeros_like(ao), ao, np.zeros_like(ao), np.full_like(ao, 0.35)])
    return color, (nn * 0.5 + 0.5).astype(np.float32), mask


def build_atlas(seed=8501, tiles=TILES):
    S = N * GRID
    out = {m: np.zeros((S, S, 4), np.float32) for m in ("color", "normal", "mask", "emission")}
    out["emission"][..., 3] = 1
    for i, tile in enumerate(tiles):
        name, spec, smooth = tile[:3]
        emit = tile[3] if len(tile) > 3 else None
        r, c = divmod(i, GRID)
        ys, xs = slice(r * N, (r + 1) * N), slice(c * N, (c + 1) * N)
        if "cards" in spec:                               # B-109: 2x2 alpha leaf-cluster cards
            h = N // 2
            for q, kind in enumerate(spec["cards"]):
                sr, sc = divmod(q, 2)
                qy = slice(r * N + sr * h, r * N + (sr + 1) * h)
                qx = slice(c * N + sc * h, c * N + (sc + 1) * h)
                cc, nn, mm = _card(kind, seed + 100 * i + q, size=h)
                out["color"][qy, qx] = cc
                out["normal"][qy, qx, :3] = nn
                out["normal"][qy, qx, 3] = 1
                out["mask"][qy, qx] = mm
            continue
        face = G3.make_face(spec, seed + i, smooth, 0.4)
        out["color"][ys, xs, :3] = face["color"]
        out["color"][ys, xs, 3] = 1
        out["normal"][ys, xs, :3] = face["normal"]
        out["normal"][ys, xs, 3] = 1
        out["mask"][ys, xs] = face["mask"]
        if emit:                                          # B-101: emissive tiles (solarite, vent mouths)
            lum = face["color"] @ np.array([0.30, 0.59, 0.11], np.float32)
            lo, hi = np.percentile(lum, 8), np.percentile(lum, 92)
            m = np.clip((lum - lo) / max(hi - lo, 1e-3), 0, 1)
            if emit.get("from", "light") == "dark":
                m = 1.0 - m
            m = m ** 1.5 * float(emit.get("k", 1.0))
            out["emission"][ys, xs, :3] = m[..., None] * (np.array(emit["color"], np.float32) / 255.0)
    return out


def export_atlas(entry, art_dir):
    _, name, _ = entry["key"].split("/")                 # props/earth_flora/atlas, props/mars_flora/atlas
    d = os.path.join(art_dir, "props", name)
    os.makedirs(d, exist_ok=True)
    maps = build_atlas(int(entry.get("seed", 8501)), TILE_SETS[entry.get("set", "earth")])
    paths = {}
    for m, a in maps.items():
        p = os.path.join(d, f"atlas_{m}.png")
        pngio.write_png(p, pngio.to_u8(np.clip(a, 0, 1)))
        paths[m] = p
    return paths, maps
