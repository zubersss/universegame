"""Terrain tile-set generator (contract §4 `terrain/<planet>/<material>`), called by render.py.

One 1024x1024 sheet per material: the 47 "blob" autotile variants, 128 px each, 8 columns,
no gutters; slots 47..62 hold 16 interior variants of tile 46 (D-020), slot 63 is empty. Variant order matches UNITY's BlobAutotile.cs exactly:
neighbour bits N=1 NE=2 E=4 SE=8 S=16 SW=32 W=64 NW=128 (N = the tile above), a corner only
counts when both adjacent edges connect, and the 47 reduced masks sorted ascending give the
sheet index (0 = isolated block, 46 = fully surrounded).

How tiles join: the material's albedo and height are periodic over 128 px, so any two tiles
line up. Edges that face air are carved with an irregular contour whose offset is a periodic
function of the position along the edge, so neighbouring tiles' contours meet exactly, inner
corners included. A bevel near exposed edges goes into the height field; the normal map is the
height gradient (OpenGL: +Y up). Writes a demo patch + relit view to blender/preview/.
"""
import os

import numpy as np

from meridian import post, pngio
from meridian.noise import fft_noise, fft_noise_1d

T = 128
COLS = 8
N_, NE, E_, SE, S_, SW, W_, NW = 1, 2, 4, 8, 16, 32, 64, 128


def reduce_mask(m):
    if not (m & N_ and m & E_):
        m &= ~NE
    if not (m & S_ and m & E_):
        m &= ~SE
    if not (m & S_ and m & W_):
        m &= ~SW
    if not (m & N_ and m & W_):
        m &= ~NW
    return m


MASKS = [m for m in range(256) if reduce_mask(m) == m]
assert len(MASKS) == 47
INDEX = {m: i for i, m in enumerate(MASKS)}


def srgb(c):
    return np.array(c, np.float32) / 255.0


# ---------------------------------------------------------------- materials
# Each recipe returns (albedo HxWx3 sRGB 0..1, height HxW in px, alpha_scale) — all periodic.

def _mix3(a, b, t):
    return a + (b - a) * np.clip(t, 0, 1)[..., None]


def _pebbles(rng, scale, thresh):
    n = fft_noise(rng, T, T, scale * 0.6, scale * 1.6, 0.2)
    return np.clip((n - thresh) / 0.6, 0, 1)


def mat_soil(rng, p):
    base = fft_noise(rng, T, T, 6, 60, 0.9)
    fine = fft_noise(rng, T, T, 1.5, 5, 0.2)
    peb = _pebbles(rng, p.get("pebble_size", 7), p.get("pebble_thresh", 1.6))
    peb_col = rng.random((T, T)) > 0.5
    col = _mix3(srgb(p.get("dark", (78, 58, 42))), srgb(p.get("light", (138, 104, 74))), 0.5 + 0.22 * base + 0.08 * fine)
    pl, pd = srgb(p.get("pebble_light", (150, 138, 120))), srgb(p.get("pebble_dark", (70, 62, 55)))
    col = np.where(peb[..., None] > 0, _mix3(col, np.where(peb_col[..., None], pl, pd), peb * 0.9), col)
    h = 1.2 * base + 0.5 * fine + 2.5 * peb
    return col, h


def mat_stone(rng, p):
    base = fft_noise(rng, T, T, 8, 90, 0.8)
    fine = fft_noise(rng, T, T, 1.5, 6, 0.2)
    ridge = 1 - np.abs(fft_noise(rng, T, T, 10, 60, 0.6))      # cracks where the noise crosses 0
    crack = np.clip((ridge - 0.86) / 0.1, 0, 1)
    col = _mix3(srgb(p.get("dark", (92, 90, 88))), srgb(p.get("light", (152, 149, 143))), 0.5 + 0.2 * base + 0.07 * fine)
    col = _mix3(col, srgb(p.get("crack_col", (60, 58, 56))), crack * p.get("crack_k", 0.45))
    h = 2.0 * base + 0.4 * fine - 1.5 * crack
    if p.get("pits"):
        # Vesicles (gas-bubble pits in basalt): small dark depressions.
        pit = _pebbles(rng, 4, 2.0)
        col = _mix3(col, srgb((30, 27, 26)), pit * 0.8)
        h = h - 2.0 * pit
    return col, h


def mat_sand(rng, p):
    base = fft_noise(rng, T, T, 10, 90, 0.8)
    grain = fft_noise(rng, T, T, 1.0, 2.5, 0.0)
    yy = np.mgrid[0:T, 0:T][0].astype(np.float32)
    ripple = np.sin(2 * np.pi * (yy / 16.0 + 0.15 * fft_noise(rng, T, T, 30, 128, 0.5)))
    col = _mix3(srgb(p.get("dark", (192, 164, 114))), srgb(p.get("light", (230, 208, 162))), 0.5 + 0.18 * base + 0.12 * grain)
    h = 0.6 * base + 0.25 * grain + 0.5 * ripple
    return col, h


def mat_snow(rng, p):
    base = fft_noise(rng, T, T, 8, 90, 0.9)
    fine = fft_noise(rng, T, T, 1.5, 6, 0.3)
    col = _mix3(srgb(p.get("dark", (206, 216, 230))), srgb(p.get("light", (248, 250, 253))), 0.6 + 0.2 * base + 0.06 * fine)
    h = 1.5 * base + 0.3 * fine
    return col, h


def mat_water(rng, p):
    base = fft_noise(rng, T, T, 10, 80, 0.8)
    wave = fft_noise(rng, T, T, 6, 24, 0.4)
    col = _mix3(srgb(p.get("dark", (22, 60, 90))), srgb(p.get("light", (44, 104, 138))), 0.5 + 0.2 * base)
    h = 0.5 * wave
    return col, h


RECIPES = {"soil": mat_soil, "grass": mat_soil, "stone": mat_stone, "sand": mat_sand,
           "snow": mat_snow, "water": mat_water}
# Other planets' materials pick a recipe and an edge style in the manifest
# ("recipe": "stone", "edge": "snow", colors and recipe parameters alongside).

# Edge style per material: inset base/amplitude (px), contour wavelength range, bevel depth and
# width (px), rim tint, top-band (grass/frost/foam).
EDGE = {
    "soil":  dict(inset=4, amp=2.2, lo=6, hi=40, depth=6, rim=10, rim_col=(64, 46, 32), rim_k=0.35),
    # Grass grows only on upward-facing exposed edges (D-020); sides/underside show soil + rim.
    "grass": dict(inset=4, amp=2.2, lo=6, hi=40, depth=6, rim=10, rim_col=(64, 46, 32), rim_k=0.35,
                  band=(22, 6), band_dark=(52, 92, 34), band_light=(112, 152, 58), blades=True,
                  top_only_band=True),
    "stone": dict(inset=3, amp=2.0, lo=10, hi=60, depth=9, rim=12, rim_col=(70, 68, 66), rim_k=0.3),
    "sand":  dict(inset=3, amp=1.2, lo=12, hi=64, depth=3, rim=10, rim_col=(176, 148, 100), rim_k=0.3),
    "snow":  dict(inset=3, amp=1.6, lo=10, hi=64, depth=7, rim=14, rim_col=(196, 210, 228), rim_k=0.4),
    "water": dict(inset=1, amp=0.0, lo=8, hi=64, depth=1, rim=4, rim_col=(30, 80, 110), rim_k=0.0,
                  band=(7, 1), band_dark=(150, 196, 214), band_light=(196, 228, 238), alpha=0.8, top_only_band=True),
}


# ---------------------------------------------------------------- tiles

def make_tile(mask, col, ins, st):
    """One 128x128 variant: color (float), edge height (px, non-periodic part), alpha."""
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    v, u = yy + 0.5, xx + 0.5
    xi, yi = xx.astype(int), yy.astype(int)
    eN = v - ins["N"][xi]
    eS = (T - v) - ins["S"][xi]
    eW = u - ins["W"][yi]
    eE = (T - u) - ins["E"][yi]
    big = np.full((T, T), 1e3, np.float32)
    exposed = {"N": not mask & N_, "S": not mask & S_, "W": not mask & W_, "E": not mask & E_}
    ed = {"N": eN, "S": eS, "W": eW, "E": eE}
    e = big.copy()
    for k, on in exposed.items():
        if on:
            e = np.minimum(e, ed[k])
    r = 12.0
    for a, b in (("N", "E"), ("S", "E"), ("S", "W"), ("N", "W")):
        if exposed[a] and exposed[b]:
            qa, qb = r - ed[a], r - ed[b]
            both = (qa > 0) & (qb > 0)
            e = np.where(both, np.minimum(e, r - np.hypot(qa, qb)), e)
    for a, b, bit in (("N", "E", NE), ("S", "E", SE), ("S", "W", SW), ("N", "W", NW)):
        if not exposed[a] and not exposed[b] and not mask & bit:
            e = np.minimum(e, np.maximum(ed[a], ed[b]))      # inner corner notch
    alpha = np.clip(e, 0, 1) * st.get("alpha", 1.0)

    t = np.clip(e / st["rim"], 0, 1)
    height = -st["depth"] * (1 - t) ** 2
    color = _mix3(col, srgb(st["rim_col"]), (1 - t) * st["rim_k"])

    if "band" in st:
        bw, bamp = st["band"]
        if st.get("top_only_band"):
            eb = eN if exposed["N"] else big
        else:
            eb = e
        width = bw + bamp * ins["band"][xi]
        g = np.clip((width - eb) / 2.0, 0, 1)
        shade = 0.5 + 0.5 * ins["band_tex"]
        band_col = _mix3(srgb(st["band_dark"]), srgb(st["band_light"]), shade)
        color = _mix3(color, band_col, g)
        height = height + 1.5 * g * ins["band_tex"]
        if st.get("alpha"):
            alpha = np.where(g > 0, np.maximum(alpha, np.clip(e, 0, 1) * 0.95 * g), alpha)
    return color, height, alpha


def normals_from_height(h_periodic, h_edge, strength=1.0):
    """Material height is periodic (wrapped gradient, seamless between tiles); the edge bevel
    is not (one-sided gradient at the tile border)."""
    gx = (np.roll(h_periodic, -1, axis=1) - np.roll(h_periodic, 1, axis=1)) * 0.5
    gy = (np.roll(h_periodic, -1, axis=0) - np.roll(h_periodic, 1, axis=0)) * 0.5   # +row = down
    ey, ex = np.gradient(h_edge)
    gx, gy = gx + ex, gy + ey
    n = np.dstack([-gx * strength, gy * strength, np.ones_like(gx)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n


def finish_tile(color, normal, alpha):
    """Per-tile dilation so nothing bleeds between sheet cells."""
    rgb, _ = post.dilate(color, alpha >= 0.5, 10)
    nrm, grown = post.dilate(normal * 0.5 + 0.5, alpha >= 0.5, 10)
    nrm[~grown] = np.array((128, 128, 255), np.float32) / 255.0
    c8 = np.dstack([pngio.to_u8(rgb), pngio.to_u8(alpha)])
    n8 = np.dstack([pngio.to_u8(nrm), np.full(alpha.shape, 255, np.uint8)])
    return c8, n8


def build_material(name, seed, overrides):
    rng = np.random.default_rng(seed)
    rname = overrides.get("recipe", name)
    recipe = RECIPES[rname]
    st = dict(EDGE[overrides.get("edge", rname)])
    st.update(overrides.get("edge_overrides", {}))
    col, h = recipe(rng, overrides)
    ins = {}
    for k in "NSWE":
        n1 = fft_noise_1d(rng, T, st["lo"], st["hi"], 0.8)
        ins[k] = np.maximum(st["inset"] + st["amp"] * n1, 0.5).astype(np.float32)
    if st.get("blades"):
        # Grass tufts: high-frequency jag on the exposed top edge only.
        ins["N"] = np.maximum(ins["N"] + 2.0 * np.abs(fft_noise_1d(rng, T, 2, 6, 0.0)) - 1.0, 0.5)
    ins["band"] = fft_noise_1d(rng, T, 8, 48, 0.8).astype(np.float32)
    ins["band_tex"] = fft_noise(rng, T, T, 1.5, 8, 0.3).astype(np.float32)
    strength = overrides.get("normal_strength", 0.35)
    tiles = []
    for m in MASKS:
        c, he, a = make_tile(m, col, ins, st)
        tiles.append(finish_tile(c, normals_from_height(h, he, strength), a))
    # Slots 47..62: interior variants of tile 46 (D-020). Each blends the base texture toward an
    # independently seeded texture of the same recipe through a window that is exactly 0 at
    # the tile border, so every variant joins every neighbour exactly like tile 46 does.
    # A linear 50/50 mix of two independent textures loses contrast (a faint grid at every tile
    # border), so blend by rotation about the mean: variance stays constant across the window.
    theta = interior_window() * (np.pi / 2)
    ca, sa = np.cos(theta), np.sin(theta)
    for v in range(VARIANTS):
        alt_col, alt_h = recipe(np.random.default_rng([seed, 1000 + v]), overrides)
        mc = 0.5 * (col.mean(axis=(0, 1)) + alt_col.mean(axis=(0, 1)))
        mh = 0.5 * (h.mean() + alt_h.mean())
        vc = mc + (col - mc) * ca[..., None] + (alt_col - mc) * sa[..., None]
        vh = mh + (h - mh) * ca + (alt_h - mh) * sa
        c, he, a = make_tile(255, vc, ins, st)
        tiles.append(finish_tile(c, normals_from_height(vh, he, strength), a))
    return tiles


VARIANTS = 16


def interior_window(lo=1.0, hi=6.0):
    """0 within `lo` px of the tile border, 1 beyond `hi` px, smooth in between."""
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32) + 0.5
    d = np.minimum(np.minimum(xx, T - xx), np.minimum(yy, T - yy))
    x = np.clip((d - lo) / (hi - lo), 0, 1)
    return x * x * (3 - 2 * x)


def pack(tiles, idx):
    sheet = np.zeros((T * COLS, T * COLS, 4), np.uint8)
    if idx == 1:
        sheet[..., :] = (128, 128, 255, 255)
    for i, t in enumerate(tiles):
        r, c = divmod(i, COLS)
        sheet[r * T:(r + 1) * T, c * T:(c + 1) * T] = t[idx]
    return sheet


# ---------------------------------------------------------------- demo patch

DEMO = [
    "................",
    ".........##.....",
    "........####....",
    "...##..######...",
    "..#####.#####..#",
    "###############.",
    "######...#######",
    "#####.....######",
    "######..########",
    "################",
]


DEMO_INTERIOR = ["#" * 16] * 8


def tile_for(m, r, c):
    """Sheet index for a cell: the blob variant, and for fully surrounded cells one of tile 46
    or the 16 interior variants (47..62) picked by a position hash (as U-020 does)."""
    i = INDEX[reduce_mask(m)]
    if i != 46:
        return i
    k = ((r * 73856093) ^ (c * 19349663)) % (VARIANTS + 1)
    return 46 if k == 0 else 46 + k


def demo_patch(tiles, path, grid=DEMO, outside_solid=False):
    """Assemble a demo map with the blob rule and save color-over-sky + a relit view."""
    rows, cols = len(grid), len(grid[0])
    if outside_solid:
        solid = lambda r, c: not (0 <= r < rows and 0 <= c < cols) or grid[r][c] == "#"
    else:
        solid = lambda r, c: 0 <= c < cols and (r >= rows or (r >= 0 and grid[r][c] == "#"))
    img_c = np.zeros((rows * T, cols * T, 4), np.uint8)
    img_n = np.zeros((rows * T, cols * T, 4), np.uint8)
    img_n[..., :] = (128, 128, 255, 255)
    for r in range(rows):
        for c in range(cols):
            if not solid(r, c):
                continue
            m = 0
            for bit, dr, dc in ((N_, -1, 0), (NE, -1, 1), (E_, 0, 1), (SE, 1, 1), (S_, 1, 0), (SW, 1, -1), (W_, 0, -1), (NW, -1, -1)):
                if solid(r + dr, c + dc):
                    m |= bit
            ci, ni = tiles[tile_for(m, r, c)]
            img_c[r * T:(r + 1) * T, c * T:(c + 1) * T] = ci
            img_n[r * T:(r + 1) * T, c * T:(c + 1) * T] = ni
    sky = np.array((0.55, 0.70, 0.86), np.float32)
    lit = post.relight(img_c, img_n).astype(np.float32) / 255.0
    a = img_c[..., 3:4].astype(np.float32) / 255.0
    flat = img_c[..., :3].astype(np.float32) / 255.0
    top = flat * a + sky * (1 - a)
    bottom = lit[..., :3] * a + sky * (1 - a)
    out = np.vstack([top, np.full((8, top.shape[1], 3), 0.12, np.float32), bottom])[::2, ::2]
    pngio.write_png(path, np.dstack([pngio.to_u8(out), np.full(out.shape[:2], 255, np.uint8)]))


def generate(entry, ctx):
    name = entry["key"].split("/")[2]
    tiles = build_material(name, int(entry.get("seed", 1)), entry)
    os.makedirs(os.path.join(ctx["blender_dir"], "preview"), exist_ok=True)
    stem = os.path.join(ctx["blender_dir"], "preview", entry["key"].replace("/", "__"))
    demo_patch(tiles, stem + "_demo.png")
    demo_patch(tiles, stem + "_demo_interior.png", DEMO_INTERIOR, outside_solid=True)
    maps = {"color": pack(tiles, 0), "normal": pack(tiles, 1)}
    if ctx["preview"]:
        maps = {k: v[::4, ::4].copy() for k, v in maps.items()}
    return maps
