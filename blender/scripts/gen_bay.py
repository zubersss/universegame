"""Waystation docking-bay interior backdrop (B-038), side view, painted in 2D (numpy), called
by render.py as a generator for backgrounds/waystation/layer0..2.

Architecture, not terrain, so it is drawn rather than rendered: every repeat unit divides the
2048 px width and every draw wraps in x, so each layer tiles by construction. Top-lit (bay
lights overhead): surfaces brighten toward their top edge; emission is baked into the colour
(backgrounds are colour only).
  layer0 (far, opaque): back wall of panels with seams, an observation window band onto space
         (stars, mullions), a row of ceiling lights, a hazard strip; hazed toward the bay air.
  layer1 (mid): I-beam columns every 512 px with work lights, an overhead gantry truss, a crane
         trolley with a hanging hook block.
  layer2 (near): deck floor plates with a hazard-striped edge, stacked Halcyon cargo crates.
"""
import numpy as np

from meridian import pngio, post
from meridian.noise import fft_noise

W, H = 2048, 1024
AIR = np.array([92, 98, 110], np.float32) / 255           # bay haze


def C(c):
    return np.array(c, np.float32) / 255


class Canvas:
    def __init__(self, opaque_rgb=None):
        self.rgb = np.zeros((H, W, 3), np.float32)
        self.a = np.zeros((H, W), np.float32)
        if opaque_rgb is not None:
            self.rgb[:] = opaque_rgb
            self.a[:] = 1.0

    def rect(self, x0, x1, y0, y1, col, lit=0.25, a=1.0):
        """Filled rect, x wraps; vertical light falloff: top edge `lit` brighter than bottom."""
        y0, y1 = int(max(0, y0)), int(min(H, y1))
        if y1 <= y0 or x1 <= x0:
            return
        ys = np.linspace(1 + lit, 1 - lit * 0.5, y1 - y0, dtype=np.float32)[:, None, None]
        block = np.clip(np.asarray(col, np.float32)[None, None, :] * ys, 0, 1)
        xs = np.arange(int(x0), int(x1)) % W
        self.rgb[y0:y1][:, xs] = self.rgb[y0:y1][:, xs] * (1 - a) + block * a
        self.a[y0:y1][:, xs] = np.maximum(self.a[y0:y1][:, xs], a)

    def line_h(self, x0, x1, y, th, col):
        self.rect(x0, x1, y, y + th, col, lit=0.0)

    def glow(self, cx, cy, r, col, k=0.8):
        """Soft additive light pool (x wraps)."""
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        dx = (xx - cx + W / 2) % W - W / 2
        g = np.exp(-(dx ** 2 + (yy - cy) ** 2) / (2 * r * r))[..., None] * k
        self.rgb = np.clip(self.rgb + g * np.asarray(col, np.float32) * (self.a[..., None] > 0), 0, 1)


def layer0(rng):
    cv = Canvas(C((70, 76, 86)))
    tex = fft_noise(rng, H, W, 6, 200, 1.2)
    cv.rgb *= (1 + 0.05 * tex)[..., None]
    for x in range(64, W, 128):                             # panel seams (off the tile edge)
        cv.rect(x, x + 3, 0, H, C((44, 48, 56)), lit=0.0)
    for y in range(96, H, 96):
        cv.line_h(0, W, y, 3, C((48, 52, 60)))
    # Observation window onto space: black, stars, faint blue glow low (a planet off-frame).
    cv.rect(0, W, 190, 360, C((6, 8, 14)), lit=0.0)
    n = 260
    sx, sy = rng.integers(0, W, n), rng.integers(196, 354, n)
    sb = rng.uniform(0.4, 1.0, n)
    cv.rgb[sy, sx] = np.clip(sb[:, None] * C((236, 240, 255)), 0, 1)
    yy = np.arange(190, 360, dtype=np.float32)[:, None, None]
    cv.rgb[190:360] = np.clip(cv.rgb[190:360] + C((40, 90, 160)) * np.exp(-(360 - yy) / 40) * 0.5, 0, 1)
    for x in range(0, W, 256):                              # mullions + frame
        cv.rect(x - 8, x + 8, 182, 368, C((58, 62, 70)), lit=0.1)
    cv.rect(0, W, 182, 194, C((58, 62, 70)), lit=0.1)
    cv.rect(0, W, 356, 368, C((58, 62, 70)), lit=0.1)
    for x in range(128, W, 256):                            # ceiling lights
        cv.rect(x - 40, x + 40, 52, 64, C((255, 240, 210)), lit=0.0)
        cv.glow(x, 64, 70, C((255, 236, 200)), 0.18)
    # Hazard strip along the wall base.
    yy0 = 700
    stripe = ((np.arange(W)[None, :] + np.arange(28)[:, None]) // 32) % 2      # period 64 divides W
    band = np.where(stripe[..., None] == 0, C((222, 176, 40)), C((30, 30, 32)))
    cv.rgb[yy0:yy0 + 28] = band
    cv.rgb = cv.rgb * 0.62 + AIR * 0.38                     # far: hazed into the bay air
    return cv


def i_beam(cv, x, w, col):
    cv.rect(x - w / 2, x + w / 2, 0, H, col, lit=0.15)
    cv.rect(x - w / 2, x - w / 2 + 8, 0, H, col * 0.7, lit=0.0)       # flange shadow
    cv.rect(x + w / 2 - 8, x + w / 2, 0, H, col * 1.15, lit=0.0)      # lit flange
    for y in range(140, H, 120):                                       # bolt plates
        cv.rect(x - w / 2 - 4, x + w / 2 + 4, y, y + 10, col * 0.85, lit=0.0)


def layer1(rng):
    cv = Canvas()
    steel = C((104, 108, 114))
    for x in range(256, W + 256, 512):
        i_beam(cv, x % W, 64, steel)
        cv.rect(x + 34, x + 50, 300, 316, C((255, 214, 120)), lit=0.0)  # work light
        cv.glow(x + 42, 308, 40, C((255, 214, 140)), 0.25)
    # Gantry truss across the top: chords + diagonal lattice (period 64 divides W).
    cv.rect(0, W, 96, 108, steel, lit=0.1)
    cv.rect(0, W, 156, 168, steel * 0.9, lit=0.1)
    for x in range(0, W, 64):
        for t in range(48):
            xx = (x + t) % W
            y = int(108 + t * (48 / 48))
            cv.rect(xx, xx + 5, y, y + 5, steel * 0.85, lit=0.0)
    # Crane trolley + cable + hook block, one per 1024 px.
    for x in (448, 1472):
        cv.rect(x - 40, x + 40, 168, 196, C((222, 176, 40)), lit=0.2)
        cv.rect(x - 2, x + 2, 196, 520, C((40, 40, 44)), lit=0.0)
        cv.rect(x - 22, x + 22, 520, 566, C((222, 176, 40)), lit=0.25)
        cv.rect(x - 6, x + 6, 566, 600, C((60, 60, 64)), lit=0.0)
    cv.rgb = cv.rgb * 0.85 + AIR * 0.15
    return cv


def crate(cv, x, y_floor, w, h, col, rng):
    cv.rect(x, x + w, y_floor - h, y_floor, col, lit=0.3)
    cv.rect(x, x + w, y_floor - h, y_floor - h + 6, col * 1.2, lit=0.0)     # lit top edge
    cv.rect(x + w - 6, x + w, y_floor - h, y_floor, col * 0.7, lit=0.0)     # shaded side
    cv.rect(x + w * 0.15, x + w * 0.85, y_floor - h * 0.55, y_floor - h * 0.45, col * 0.6, lit=0.0)  # label band


def layer2(rng):
    cv = Canvas()
    floor_y = 880
    cv.rect(0, W, floor_y, H, C((128, 132, 138)), lit=0.12)
    for x in range(64, W, 128):                               # plate seams (off the tile edge)
        cv.rect(x, x + 3, floor_y + 24, H, C((84, 88, 94)), lit=0.0)
    cv.line_h(0, W, floor_y + 60, 3, C((84, 88, 94)))
    stripe = ((np.arange(W)[None, :] + np.arange(24)[:, None]) // 16) % 2       # deck-edge hazard stripes, period 32
    cv.rgb[floor_y:floor_y + 24] = np.where(stripe[..., None] == 0, C((232, 184, 44)), C((28, 28, 30)))
    cv.a[floor_y:floor_y + 24] = 1.0
    orange, grey = C((214, 112, 40)), C((120, 126, 132))
    for x0 in (96, 760, 1340):                                 # crate stacks (well inside the tile)
        w1 = int(rng.integers(150, 200))
        crate(cv, x0, floor_y, w1, 130, orange, rng)
        crate(cv, x0 + w1 + 6, floor_y, 120, 100, grey, rng)
        crate(cv, x0 + 20, floor_y - 130, w1 - 40, 100, grey if x0 != 760 else orange, rng)
    for x in range(64, W, 256):                                # railing posts at the deck edge
        cv.rect(x - 4, x + 4, floor_y - 70, floor_y, C((180, 184, 188)), lit=0.2)
    cv.rect(0, W, floor_y - 72, floor_y - 64, C((180, 184, 188)), lit=0.0)
    return cv


def generate(entry, ctx):
    layer = entry["key"].split("/")[2]
    rng = np.random.default_rng(int(entry.get("seed", 1)))
    cv = {"layer0": layer0, "layer1": layer1, "layer2": layer2}[layer](rng)
    rgb, a = cv.rgb, cv.a
    if ctx["preview"]:
        rgb, a = rgb[::4, ::4], a[::4, ::4]
    if layer == "layer0":
        return {"color": np.dstack([pngio.to_u8(rgb), np.full(a.shape, 255, np.uint8)])}
    filled, _ = post.dilate(rgb, a >= 0.5, 10)                 # colour under alpha 0 = neighbours (no halos)
    return {"color": np.dstack([pngio.to_u8(filled), pngio.to_u8(a)])}
