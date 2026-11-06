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
    ("spare",        {"recipe": "soil", "dark": [100, 100, 100], "light": [120, 120, 120], "pebble_thresh": 3.0}, 0.2),
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
    ("spare",        {"recipe": "soil", "dark": [100, 100, 100], "light": [120, 120, 120], "pebble_thresh": 3.0}, 0.2),
]
TILE_SETS = {"earth": TILES, "mars": MARS_TILES, "mercury": MERCURY_TILES, "venus": VENUS_TILES}
CURRENT = "earth"                                  # build_flora sets this while building a planet's set
INDEX = {name: i for i, (name, *_) in enumerate(TILES)}


def tile_rect(name, inset=12):
    """UV rect (u0, v0, u1, v1) of a tile with an inset in px; UV v=0 is the BOTTOM (Blender)."""
    i = [t[0] for t in TILE_SETS[CURRENT]].index(name)
    r, c = divmod(i, GRID)
    s = N * GRID
    u0 = (c * N + inset) / s
    u1 = ((c + 1) * N - inset) / s
    v1 = 1.0 - (r * N + inset) / s                    # image row 0 = top = v 1
    v0 = 1.0 - ((r + 1) * N - inset) / s
    return u0, v0, u1, v1


def build_atlas(seed=8501, tiles=TILES):
    S = N * GRID
    out = {m: np.zeros((S, S, 4), np.float32) for m in ("color", "normal", "mask", "emission")}
    out["emission"][..., 3] = 1
    for i, tile in enumerate(tiles):
        name, spec, smooth = tile[:3]
        emit = tile[3] if len(tile) > 3 else None
        face = G3.make_face(spec, seed + i, smooth, 0.4)
        r, c = divmod(i, GRID)
        ys, xs = slice(r * N, (r + 1) * N), slice(c * N, (c + 1) * N)
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
