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
INDEX = {name: i for i, (name, _, _) in enumerate(TILES)}


def tile_rect(name, inset=12):
    """UV rect (u0, v0, u1, v1) of a tile with an inset in px; UV v=0 is the BOTTOM (Blender)."""
    i = INDEX[name]
    r, c = divmod(i, GRID)
    s = N * GRID
    u0 = (c * N + inset) / s
    u1 = ((c + 1) * N - inset) / s
    v1 = 1.0 - (r * N + inset) / s                    # image row 0 = top = v 1
    v0 = 1.0 - ((r + 1) * N - inset) / s
    return u0, v0, u1, v1


def build_atlas(seed=8501):
    S = N * GRID
    out = {m: np.zeros((S, S, 4), np.float32) for m in ("color", "normal", "mask", "emission")}
    out["emission"][..., 3] = 1
    for i, (name, spec, smooth) in enumerate(TILES):
        face = G3.make_face(spec, seed + i, smooth, 0.4)
        r, c = divmod(i, GRID)
        ys, xs = slice(r * N, (r + 1) * N), slice(c * N, (c + 1) * N)
        out["color"][ys, xs, :3] = face["color"]
        out["color"][ys, xs, 3] = 1
        out["normal"][ys, xs, :3] = face["normal"]
        out["normal"][ys, xs, 3] = 1
        out["mask"][ys, xs] = face["mask"]
    return out


def export_atlas(entry, art_dir):
    d = os.path.join(art_dir, "props", "earth_flora")
    os.makedirs(d, exist_ok=True)
    maps = build_atlas(int(entry.get("seed", 8501)))
    paths = {}
    for m, a in maps.items():
        p = os.path.join(d, f"atlas_{m}.png")
        pngio.write_png(p, pngio.to_u8(np.clip(a, 0, 1)))
        paths[m] = p
    return paths, maps
