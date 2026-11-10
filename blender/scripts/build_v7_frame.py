"""B-258 part 3 (art v7, D-205; LEAD's ruling 11-10 14:1x): THE FRAME, COMPOSED FROM PIECES. numpy only:
    python -I build_v7_frame.py <review sheet png> [peak MB of the Blender runs]
Reads blender/preview/b258/pieces/<id>.png + .json (v7_frame_pieces.py: every piece rendered and painted alone) and the
painted ground maps (pieces/ground_<name>.png). Writes blender/preview/b258/frame_96.png, frame_128.png (the play plane at
96 and at 128 px per metre, 1920 x 1080 each), frame_<ppm>_2x_<what>.png (windows of the picture as it was composed, at
twice the frame's size: never an enlarged pixel), stage_camp.json (the layout, in B-260's stage format) and the sheet.

ONE layout (STAGE), two cameras: the camera only changes the px per metre; everything keeps its place in metres.
The layers, back to front: sky; two far veils (a small stand of trees through the filter, enlarged: soft is right) and
mist; the middle thicket on a receding floor; the near row on the ground strip, with cast shadows; the earth cut below
the ground line, the pit and the dug earth; a grey 1.84 m mannequin for scale; the light (a warm pool on the stage, cool
shade round it, shafts); the FOREGROUND (near pieces at 2-3x life size, in shade, in front of everything).
What the game would add (U-216) is NOT here: wind, motes, moving light. The camp's kit is B-261's (3D): not in this frame.
"""
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from meridian import pngio  # noqa: E402
import paint_v6 as PT  # noqa: E402
import painted_v6 as PV  # noqa: E402
import v7_paint as VP  # noqa: E402

D = os.path.normpath(os.path.join(HERE, "..", "preview", "b258"))
PD = os.path.join(D, "pieces")
OLD = os.path.normpath(os.path.join(HERE, "..", "preview", "b251", "forest_frame_96_plates.png"))
W, H, GY = 1920, 1080, 660                        # the frame; the ground line's row (as the old frame's)
CX = 10.0                                         # the camera's middle, metres from the stage's left edge
Q = 2                                             # composed at twice the frame's size
GROUND_PPM = 256.0                                # a painted ground map is laid at this many px per metre (1024 px = 4 m)

# ONE COLOUR KEY: a warm, yellow-green light; a cool blue-green shade; a pale green-grey air.
HAZE = np.array([0.80, 0.86, 0.76], np.float32)
SKY_TOP, SKY_LOW = np.array([0.56, 0.70, 0.74], np.float32), np.array([0.88, 0.91, 0.76], np.float32)
WARM, SHADE = np.array([1.14, 1.07, 0.86], np.float32), np.array([0.70, 0.83, 0.97], np.float32)
POOL = dict(x=8.8, y=0.9, rx=5.2, ry=3.4)         # the pool of light on the stage (metres)
GREY = np.array([0.50, 0.50, 0.50], np.float32)   # the mannequin: neutral, for scale only

# The stage: (piece, x_m, y_m, scale, flip). y_m = the foot's height above the ground line: on the strip a piece
# farther back stands higher (0 .. 0.28), in the middle higher still. D-206's rules (contract v3.5 section 12): NO flip
# on the middle, near or play_front layers (the painted light would come from the wrong side; the far veils and the
# foreground's silhouettes may flip); never two instances of one piece at one scale inside a screen width on one layer
# (check_stage() refuses a layout that breaks either).
STAGE = {
    "far_a": dict(haze=0.84, pieces=[("far_stand", -4.0, 1.05, 0.72, False)]),
    "far_b": dict(haze=0.66, pieces=[("far_stand", 27.0, 0.80, 1.00, True)]),
    "middle": dict(haze=0.36, pieces=[
        ("tree_bushy", 0.6, 0.62, 1.10, False), ("tree_small", 2.7, 0.50, 1.00, False), ("tree_tall", 4.3, 0.66, 1.00, False),
        ("tree_bushy", 7.4, 0.70, 0.95, False), ("tree_small", 9.9, 0.56, 1.10, False), ("tree_bushy", 12.3, 0.64, 1.00, False),
        ("tree_small", 13.9, 0.48, 0.90, False), ("tree_tall", 15.3, 0.70, 1.10, False), ("tree_bushy", 17.5, 0.58, 0.90, False),
        ("tree_tall", 19.5, 0.62, 0.92, False),
        ("fern_b", 1.7, 0.40, 0.80, False), ("anthurium_c", 5.7, 0.42, 0.85, False), ("fern_c", 8.7, 0.44, 0.80, False),
        ("calathea_b", 11.1, 0.40, 0.80, False), ("anthurium_a", 14.7, 0.42, 0.78, False), ("fern_b", 16.5, 0.38, 0.75, False),
        ("calathea_a", 18.7, 0.40, 0.80, False)]),
    "near": dict(haze=0.05, pieces=[
        ("snag", 1.9, 0.22, 1.00, False), ("stump", 1.95, 0.15, 1.00, False), ("calathea_a", 0.7, 0.05, 1.00, False),
        ("grass_wide", 2.9, 0.06, 1.00, False), ("fern_b", 3.7, 0.10, 1.00, False), ("grass_mid", 4.4, 0.04, 1.00, False),
        ("anthurium_b", 5.1, 0.19, 1.00, False), ("rock_low", 6.0, 0.11, 1.00, False), ("grass_seed", 5.6, 0.08, 1.00, False),
        ("grass_dry", 6.6, 0.21, 1.00, False), ("weed", 7.0, 0.24, 1.00, False), ("grass_wide", 7.5, 0.23, 0.90, False),
        ("grass_mid", 9.1, 0.24, 0.80, False), ("grass_seed", 9.5, 0.10, 0.90, False),
        ("fern_a", 11.2, 0.26, 0.90, False), ("grass_dry", 12.7, 0.26, 0.80, False), ("grass_wide", 13.6, 0.25, 0.80, False),
        ("calathea_b", 14.9, 0.23, 1.00, False), ("grass_mid", 16.3, 0.07, 0.88, False), ("fern_c", 16.0, 0.20, 1.00, False),
        ("rock_big", 16.9, 0.13, 1.00, False), ("weed", 17.8, 0.18, 0.84, False), ("log", 18.2, 0.07, 1.00, False),
        ("anthurium_a", 19.0, 0.02, 1.00, False), ("rock_flat", 19.5, 0.24, 1.00, False), ("grass_seed", 19.7, 0.05, 0.82, False)]),
    # in FRONT of the surveyor's feet, on the ground's lip: low tufts only, at most 0.30 m tall (D-206; UNITY: nothing here
    # may cover the hands or the reticle)
    "play_front": dict(haze=0.0, pieces=[("grass_mid", 3.3, -0.02, 0.42, False), ("grass_wide", 7.7, -0.03, 0.60, False),
                                         ("grass_seed", 9.25, -0.02, 0.40, False), ("grass_wide", 15.9, -0.02, 0.50, False)]),
    # the foreground: x from the VIEW's left edge (a negative x: from its right edge), so it frames both cameras
    "foreground": dict(pieces=[("calathea_a", 0.5, -2.05, 2.6, True), ("fern_b", 2.3, -3.3, 2.2, False),
                               ("anthurium_a", -0.6, -2.3, 2.5, True), ("fern_c", -2.6, -3.5, 2.4, True)]),
}
# The layers' own numbers (B-260's stage format: the composer and the game read the same table). parallax = the share of
# the camera's travel a layer keeps (a proposal: the game's numbers are UNITY's and LEAD's; a still frame does not use it).
LAYERS = {"far_a": dict(parallax=0.80, haze=0.84), "far_b": dict(parallax=0.65, haze=0.66), "middle": dict(parallax=0.40, haze=0.36),
          "near": dict(parallax=0.0, haze=0.05), "play_front": dict(parallax=0.0, haze=0.0),
          "foreground": dict(parallax=-0.35, haze=0.0, tint=[0.30, 0.40, 0.42])}
SPAWN_X = 8.2
PIT = dict(x0=9.6, x1=14.2, depth=2.95)           # the dug hole (as the old frame's)
MOUND = dict(x=15.15, w=1.7, h=0.42)              # the dug earth beside it
MAN = [(SPAWN_X, 0.0), (11.5, -2.93)]             # the mannequin: on the stage, in the pit

_PIECES = {}


def check_stage():
    """D-206's layout rules, checked before anything is painted. -> the number of placements."""
    bad, n = [], 0
    for layer, L in STAGE.items():
        seen = {}
        for pid, x_m, y_m, scale, flip in L["pieces"]:
            n += 1
            if flip and layer in ("middle", "near", "play_front"):
                bad.append(f"{layer}: {pid} at {x_m} is flipped")
            for x2 in seen.get((pid, round(scale, 3)), []):
                if abs(x2 - x_m) < W / 96.0 and layer != "foreground":
                    bad.append(f"{layer}: {pid} x{scale} at {x2} and at {x_m} (inside one screen width)")
            seen.setdefault((pid, round(scale, 3)), []).append(x_m)
            if layer == "play_front" and piece(pid)[1]["height_m"] * scale > 0.30:
                bad.append(f"play_front: {pid} x{scale} stands {piece(pid)[1]['height_m'] * scale:.2f} m (over 0.30)")
    if bad:
        raise SystemExit("build_v7_frame: the stage breaks D-206:\n  " + "\n  ".join(bad))
    return n


def piece(pid):
    if pid not in _PIECES:
        img = pngio.read_png_np(os.path.join(PD, pid + ".png")).astype(np.float32) / 255.0
        _PIECES[pid] = (img, json.load(open(os.path.join(PD, pid + ".json"), encoding="utf-8")))
    return _PIECES[pid]


def over(dst, fg, x, y):
    """fg (premultiplied RGBA) over dst (opaque RGB), its top-left at (x, y)."""
    h, w = fg.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 > x0 and y1 > y0:
        s = fg[y0 - y:y1 - y, x0 - x:x1 - x]
        d = dst[y0:y1, x0:x1]
        d *= 1 - s[..., 3:4]
        d += s[..., :3]


class Frame:
    def __init__(self, ppm, seed=7):
        self.P, self.k = ppm, float(ppm * Q)                  # the camera; the picture's px per metre
        self.x0 = CX - W / (2.0 * ppm)                        # the view's left edge, metres
        self.x1 = self.x0 + W / float(ppm)
        self.pw, self.ph, self.gy = W * Q, H * Q, GY * Q
        self.img = np.zeros((self.ph, self.pw, 3), np.float32)
        self.rng = np.random.default_rng(seed)
        self.cache = {}
        self.log = []

    def px(self, x_m, y_m):
        return (x_m - self.x0) * self.k, self.gy - y_m * self.k

    def metres(self, x0, y0, w, h):
        """The world coordinates of a window of the picture: (x_m 1 x w, y_m h x 1)."""
        return (self.x0 + (np.arange(x0, x0 + w, dtype=np.float32) + 0.5) / self.k)[None, :], ((self.gy - (np.arange(y0, y0 + h, dtype=np.float32) + 0.5)) / self.k)[:, None]

    def light(self, x0, y0, w, h, strength=1.0):
        """The stage's light over a window: WARM in the pool, SHADE round it. -> h x w x 3 (a multiplier)."""
        xm, ym = self.metres(x0, y0, w, h)
        t = np.exp(-((xm - POOL["x"]) / POOL["rx"]) ** 2 - ((ym - POOL["y"]) / POOL["ry"]) ** 2)
        m = SHADE[None, None, :] + (WARM - SHADE)[None, None, :] * t[..., None]
        return 1 + strength * (m - 1)

    def sprite(self, pid, scale=1.0, flip=False):
        """The piece at this picture's size. -> (straight RGBA, the pivot's column, the pivot's row)."""
        key = (pid, round(scale, 4), flip)
        if key not in self.cache:
            src, meta = piece(pid)
            im = VP.resize(src, self.k * scale / meta["px_per_m"])
            px, py = meta["pivot"][0] * im.shape[1], (1 - meta["pivot"][1]) * im.shape[0]
            if flip:
                im, px = im[:, ::-1], im.shape[1] - px
            self.cache[key] = (im, px, py)
        return self.cache[key]

    def put(self, pid, x_m, y_m, scale=1.0, flip=False, haze=0.0, lit=1.0, mul=None, opacity=1.0, cut=True, blur=0):
        im, px, py = self.sprite(pid, scale, flip)
        cx, cy = self.px(x_m, y_m)
        x, y = int(round(cx - px)), int(round(cy - py))
        h, w = im.shape[:2]
        if x >= self.pw or y >= self.ph or x + w <= 0 or y + h <= 0:
            return
        rgb, a = im[..., :3].copy(), im[..., 3] * opacity
        if blur:
            pm = np.dstack([PT.box(rgb[..., c] * a, blur) for c in range(3)])
            a = PT.box(a, blur)
            rgb = pm / np.maximum(a[..., None], 1e-3)
        if cut and piece(pid)[1].get("under_m", 0) > 0.03:    # what a rock has under the ground line is in the ground
            rows = np.arange(h, dtype=np.float32)[:, None]
            a = a * np.clip((py + 0.012 * self.k - rows) / (0.02 * self.k), 0, 1)
        if mul is not None:
            rgb = rgb * np.asarray(mul, np.float32)[None, None, :]
        if lit:
            rgb = rgb * self.light(x, y, w, h, lit)
        if haze:
            rgb = rgb * (1 - haze) + HAZE[None, None, :] * haze
        over(self.img, np.concatenate([np.clip(rgb, 0, 1) * a[..., None], a[..., None]], axis=2), x, y)

    # ---- the painted grounds
    def sky(self):
        yy = (np.arange(self.ph, dtype=np.float32) / self.gy)[:, None, None]
        t = np.clip(yy, 0, 1) ** 1.3
        base = SKY_TOP[None, None, :] * (1 - t) + SKY_LOW[None, None, :] * t
        xm, ym = self.metres(0, 0, self.pw, self.ph)
        glow = np.exp(-((xm - 13.5) / 6.5) ** 2 - ((ym - 4.6) / 2.6) ** 2)[..., None]         # where the light comes in
        self.img[:] = base * (1 - 0.35 * glow) + np.array([0.97, 0.95, 0.74], np.float32)[None, None, :] * 0.35 * glow
        P = PT.Painting(self.pw, self.ph, 3, 1)
        P.img = self.img
        under = self.img.copy()
        PV.brush(P, VP.bank(), under, np.ones((self.ph, self.pw), np.float32), 900, (40.0 * Q, 90.0 * Q), angle=0.0, spread=0.25, alpha=(0.5, 0.85),
                 jitter=0.03, hue=0.006, kind="dry")
        self.log.append(f"sky {P.count} strokes")

    def mist(self, y_m, thick_m, amount):
        """A band of the air lying on the far ground: densest at y_m, gone thick_m above and below."""
        ym = self.metres(0, 0, 1, self.ph)[1]
        noise = PT.fbm(self.ph // 8 + 1, self.pw // 8 + 1, 30.0, self.rng, 3)
        noise = PT.box(np.repeat(np.repeat(noise, 8, 0), 8, 1)[:self.ph, :self.pw], 6)
        m = np.clip(1 - np.abs(ym - y_m - 0.35 * noise) / thick_m, 0, 1) ** 1.5 * amount
        self.img *= 1 - m[..., None]
        self.img += HAZE[None, None, :] * m[..., None]

    def floor(self):
        """The forest floor going back from the strip (between the near row and the middle thicket): paint only, lighter
        and greyer with distance (it is seen at a low angle: no detail to tell)."""
        y_top, y_bot = self.px(0, 1.15)[1], self.px(0, 0.20)[1]
        r0, r1 = int(y_top), int(y_bot)
        h = r1 - r0
        tt = (np.arange(h, dtype=np.float32) / max(h - 1, 1))[:, None, None]                 # 0 far .. 1 near
        far, near = HAZE * np.array([0.86, 0.93, 0.80], np.float32), np.array([0.36, 0.42, 0.22], np.float32)
        band = far[None, None, :] * (1 - tt) + near[None, None, :] * tt
        n = PT.fbm(h, self.pw, 40.0 * Q, self.rng, 3, sx=5.0)[..., None]
        band = band * (1 + 0.16 * n) * self.light(0, r0, self.pw, h, 0.8)
        edge = np.clip(tt * 9.0, 0, 1)                                                       # its far edge melts into the mist
        self.img[r0:r1] = self.img[r0:r1] * (1 - edge) + np.clip(band, 0, 1) * edge
        P = PT.Painting(self.pw, h, 5, 1)
        P.img = self.img[r0:r1]
        under = self.img[r0:r1].copy()
        w = np.broadcast_to(np.clip(tt[..., 0] * 3.0, 0, 1), (h, self.pw))
        PV.brush(P, VP.bank(), under, w, int(2200 * self.pw / 3840), (9.0 * Q, 26.0 * Q), angle=0.0, spread=0.12, alpha=(0.6, 0.9), jitter=0.06, hue=0.012, kind="dry")
        self.log.append(f"floor {P.count} strokes")

    def tiles(self, name, x_px0, y_px0, w, h, squash=1.0, seed=0):
        """A painted ground map laid over the window (x_px0, y_px0, w, h) of the picture, fixed to the WORLD (not to the
        view): two copies of the map, offset and mirrored, cross-faded by a slow noise, so its 4 m period does not show.
        squash < 1 = the map seen at a low angle (its rows gathered by area means). -> h x w x 3."""
        key = (name, squash)
        if key not in self.cache:
            tex = pngio.read_png_np(os.path.join(PD, f"ground_{name}.png")).astype(np.float32)[..., :3] / 255.0
            s = self.k / GROUND_PPM
            if abs(s - 1.0) > 1e-3:
                tex = VP.resize(np.concatenate([tex, np.ones(tex.shape[:2] + (1,), np.float32)], axis=2), s)[..., :3]
            if squash != 1.0:
                tex = VP._axis(tex, max(2, int(tex.shape[0] * squash)), 0)
            self.cache[key] = tex
        tex = self.cache[key]
        th, tw = tex.shape[:2]
        xs = np.arange(x_px0, x_px0 + w) + int(self.x0 * self.k)
        ys = np.arange(h) + (y_px0 - self.gy)                                                 # rows from the ground line
        a = tex[np.ix_((ys + seed * 37) % th, xs % tw)]
        b = tex[np.ix_((ys + th // 2 + seed * 91) % th, (-xs + tw // 3 + seed * 53) % tw)]
        rng = np.random.default_rng(100 + seed)
        m = np.clip(PT.fbm(h, w, 150.0 * Q, rng, 2, sx=1.5) * 2.2 + 0.5, 0, 1)[..., None]
        return a * (1 - m) + b * m

    def ground(self):
        """The ground strip (the surface, seen at a low angle), the earth cut below it, the pit and the dug earth."""
        k, pw = self.k, self.pw
        # --- the cut: litter and topsoil, the soil wall, red laterite with stones
        r0 = self.gy
        h = self.ph - r0
        xm, ym = self.metres(0, r0, pw, h)
        depth = -ym                                                                           # h x 1, metres under the ground line
        wob = PT.fbm(1, pw, 260.0 * Q, self.rng, 3)[0][None, :] * 0.16
        wob2 = PT.fbm(1, pw, 180.0 * Q, self.rng, 3)[0][None, :] * 0.22
        top, wall, red = self.tiles("brown_mud_leaves_01", 0, r0, pw, h, seed=1), self.tiles("excavated_soil_wall", 0, r0, pw, h, seed=2), \
            self.tiles("red_laterite_soil_stones", 0, r0, pw, h, seed=3)
        t1 = np.clip((depth - (0.42 + wob)) / 0.16 + 0.5, 0, 1)[..., None]
        t2 = np.clip((depth - (2.15 + wob2)) / 0.30 + 0.5, 0, 1)[..., None]
        cut = (top * 0.62) * (1 - t1) + wall * 0.98 * t1
        cut = cut * (1 - t2) + red * 0.86 * t2
        cut *= (1 - 0.075 * depth)[..., None] * np.array([0.98, 0.96, 0.94], np.float32)[None, None, :]
        cut *= 1 - 0.30 * np.clip(1 - depth / 0.10, 0, 1)[..., None]                          # the lip's own shadow on the cut
        cut *= self.light(0, r0, pw, h, 0.35)
        # --- the pit: a bowl; its far wall the same earth in shade, lit a little where the light falls in
        x0, x1, dp = PIT["x0"], PIT["x1"], PIT["depth"]
        nb = PT.fbm(1, pw, 60.0 * Q, self.rng, 2)[0][None, :] * 0.05
        prof = dp * np.minimum(1.0, np.minimum(np.clip((xm - x0) / 1.15, 0, 1) ** 0.75, np.clip((x1 - xm) / 1.35, 0, 1) ** 0.75)) + nb
        inside = np.clip((prof - depth) * k / 2.5, 0, 1) * ((xm > x0) & (xm < x1))            # h x w
        back = self.tiles("excavated_soil_wall", 0, r0, pw, h, seed=5) * (1 - t2) + self.tiles("red_laterite_soil_stones", 0, r0, pw, h, seed=6) * t2
        sun_in = np.clip(1 - (xm - x0) / 2.6 - depth / 2.2, 0, 1)                             # the light falls in from the upper right: the left wall has it
        back = back * (0.36 + 0.42 * sun_in[..., None]) * np.array([0.86, 0.90, 1.0], np.float32)[None, None, :]
        back *= 1 - 0.35 * np.clip(1 - (prof - depth) / 0.35, 0, 1)[..., None]                # darker where the wall turns into the cut
        cut = cut * (1 - inside[..., None]) + back * inside[..., None]
        self.img[r0:] = np.clip(cut, 0, 1)
        # --- the strip: the forest floor at a low angle, its front edge the ground line
        s_top = 0.30
        r_top = int(self.px(0, s_top)[1])
        sh = r0 - r_top + int(0.05 * k)
        strip = self.tiles("forest_floor", 0, r_top, pw, sh, squash=0.30, seed=4)
        tt = (np.arange(sh, dtype=np.float32) / max(sh - 1, 1))[:, None, None]
        strip = strip * (0.86 + 0.34 * tt) * np.array([1.0, 1.02, 0.86], np.float32)[None, None, :] * self.light(0, r_top, pw, sh, 1.0)
        xm_s = self.metres(0, r_top, pw, sh)[0]
        edge = PT.fbm(1, pw, 18.0 * Q, self.rng, 2)[0][None, :] * 0.035 * k
        rows = np.arange(sh, dtype=np.float32)[:, None]
        a_top = np.clip((rows - 0.03 * k - edge) / (0.05 * k), 0, 1)                          # its far edge is soft and uneven
        a_bot = np.clip((sh - 0.035 * k + 0.5 * edge - rows) / 2.0, 0, 1)                     # its front lip hangs a little over the cut
        hole = ((xm_s > x0 + 0.05) & (xm_s < x1 - 0.05)).astype(np.float32)
        a_pit = 1 - hole * np.clip((rows - (r0 - r_top) + 0.03 * k) / 2.0, 0, 1)              # the pit's mouth cuts the lip
        a = (a_top * a_bot * a_pit)[..., None]
        self.img[r_top:r_top + sh] = self.img[r_top:r_top + sh] * (1 - a) + np.clip(strip, 0, 1) * a
        # --- the dug earth: a heap of the red subsoil beside the pit
        mx, mw, mh = MOUND["x"], MOUND["w"], MOUND["h"]
        bx0, by0 = int(self.px(mx - mw / 2 - 0.1, 0)[0]), int(self.px(0, mh + 0.25)[1])
        bw, bh = int((mw + 0.2) * k), int((mh + 0.30) * k)
        xm_m, ym_m = self.metres(bx0, by0, bw, bh)
        u = (xm_m - mx) / (mw / 2)
        nz = PT.fbm(bh, bw, 14.0 * Q, self.rng, 3)
        foot = 0.05                                                                           # where it stands on the strip
        top_m = foot + mh * np.clip(1 - np.abs(u) ** 2.2, 0, 1) * (1 + 0.10 * nz)                 # its outline
        am = np.clip((top_m - ym_m) * k / 2.0, 0, 1) * np.clip((ym_m - foot + 0.01) * k / 2.0, 0, 1) * (np.abs(u) < 1.0)
        earth = self.tiles("red_laterite_soil_stones", bx0, by0, bw, bh, seed=8)
        shade = np.clip(0.62 + 0.55 * (u * 0.5 + 0.5) + 0.25 * (ym_m - foot) / mh, 0.5, 1.25)[..., None]   # lit from the upper right
        earth = earth * shade * np.array([1.05, 0.98, 0.90], np.float32)[None, None, :] * self.light(bx0, by0, bw, bh, 1.0)
        self.mound = (np.concatenate([np.clip(earth, 0, 1) * am[..., None], am[..., None]], axis=2), bx0, by0)

    def shadows(self, pieces):
        """Each near piece's shadow on the strip: its own silhouette laid down flat (a sixth of its height) and thrown to
        the left and back, cool and soft: a SHAPE, as a painter puts it in, not a blur under the foot."""
        s_h = 0.17
        for pid, x_m, y_m, scale, flip in pieces:
            im, px, py = self.sprite(pid, scale, flip)
            a = im[:int(py) + 1, :, 3]
            if a.shape[0] < 4:
                continue
            hh = max(2, int(a.shape[0] * s_h))
            sm = VP._axis(a, hh, 0)
            shear = 0.55 * a.shape[0] / hh                                                    # px to the left per row up
            wid = a.shape[1] + int(shear * hh) + 2
            out = np.zeros((hh, wid), np.float32)
            for r in range(hh):
                off = int((hh - 1 - r) * shear)
                out[r, wid - a.shape[1] - off:wid - off] = sm[r]
            out = PT.box(out, max(1, int(0.012 * self.k)))
            cx, cy = self.px(x_m, y_m)
            x, y = int(round(cx - px)) - (wid - a.shape[1]), int(round(cy)) - hh
            x0, y0, x1, y1 = max(x, 0), max(y, int(self.px(0, 0.30)[1])), min(x + wid, self.pw), min(y + hh, self.gy)
            if x1 > x0 and y1 > y0:
                m = out[y0 - y:y1 - y, x0 - x:x1 - x, None] * 0.50
                self.img[y0:y1, x0:x1] *= 1 - m * (1 - np.array([0.42, 0.52, 0.66], np.float32))[None, None, :]

    def mannequin(self, x_m, y_m):
        """A plain neutral-grey figure 1.84 m tall, side view, for SCALE only (v7_paint.mannequin)."""
        fx, fy = self.px(x_m, y_m)
        VP.mannequin(self.img, self.k, fx, fy, GREY)

    def shafts(self, amount=0.13):
        """Light coming in through the canopy: a few soft beams from the upper right, ending on the stage."""
        f = 4
        h, w = self.ph // f, self.pw // f
        xm = (self.x0 + (np.arange(w, dtype=np.float32) + 0.5) * f / self.k)[None, :]
        ym = ((self.gy - (np.arange(h, dtype=np.float32) + 0.5) * f) / self.k)[:, None]
        beam = np.zeros((h, w), np.float32)
        for bx, wd, st in ((6.3, 0.55, 0.8), (8.4, 0.9, 1.0), (10.6, 0.45, 0.6), (12.7, 0.7, 0.75)):   # where each beam meets the ground, its width
            u = (xm - bx) - ym * 0.62                                                                  # it leans to the upper right
            beam += st * np.exp(-(u / wd) ** 2) * np.clip(ym / 0.6, 0, 1) * np.clip(1.15 - ym / 7.5, 0, 1)
        beam = PT.box(np.repeat(np.repeat(beam, f, 0), f, 1)[:self.ph, :self.pw], 3)
        self.img += (beam * amount)[..., None] * np.array([1.0, 0.96, 0.72], np.float32)[None, None, :] * (1 - self.img)

    def compose(self):
        t0 = time.time()
        self.sky()
        for name in ("far_a", "far_b"):
            L = STAGE[name]
            for pid, x_m, y_m, scale, flip in L["pieces"]:
                self.put(pid, x_m, y_m, scale, flip, haze=L["haze"], lit=0.0, cut=False)
            self.mist(1.0 if name == "far_a" else 0.75, 1.5, 0.55 if name == "far_a" else 0.42)
        self.floor()
        self.shafts(0.10)
        L = STAGE["middle"]
        for pid, x_m, y_m, scale, flip in sorted(L["pieces"], key=lambda p: -p[2]):
            self.put(pid, x_m, y_m, scale, flip, haze=L["haze"] + 0.25 * (y_m - 0.4), lit=0.55, cut=False)
        self.mist(0.42, 0.55, 0.26)
        self.shafts(0.09)
        self.ground()
        near = sorted(STAGE["near"]["pieces"], key=lambda p: -p[2])
        self.shadows(near)
        for pid, x_m, y_m, scale, flip in near:
            self.put(pid, x_m, y_m, scale, flip, haze=STAGE["near"]["haze"], lit=1.0)
        over(self.img, self.mound[0], self.mound[1], self.mound[2])
        for x_m, y_m in MAN:                                                                          # the figure: in front of the whole near layer
            self.mannequin(x_m, y_m)
        for pid, x_m, y_m, scale, flip in STAGE["play_front"]["pieces"]:
            self.put(pid, x_m, y_m, scale, flip, haze=0.0, lit=1.0, cut=False)
        for pid, x_m, y_m, scale, flip in STAGE["foreground"]["pieces"]:                              # in shade, a little out of focus
            xv = self.x0 + x_m if x_m >= 0 else self.x1 + x_m
            self.put(pid, xv, y_m, scale * (96.0 / self.P) ** 0.5, flip, lit=0.0, mul=LAYERS["foreground"]["tint"], cut=False, blur=max(1, int(0.004 * self.k)))
        self.img = PT.tooth(np.clip(self.img, 0, 1), 11)
        self.log.append(f"composed in {time.time() - t0:.1f} s")
        return self.img

    def window(self, x_m, y_m, w=960, h=540):
        """A window of the picture as composed (twice the frame's size), its middle at (x_m, y_m)."""
        cx, cy = self.px(x_m, y_m)
        x0, y0 = int(np.clip(cx - w / 2, 0, self.pw - w)), int(np.clip(cy - h / 2, 0, self.ph - h))
        return self.img[y0:y0 + h, x0:x0 + w]

    def shrunk(self):
        return self.img.reshape(H, Q, W, Q, 3).mean(axis=(1, 3))


def save(path, rgb):
    pngio.write_png(path, np.concatenate([pngio.to_u8(rgb), np.full(rgb.shape[:2] + (1,), 255, np.uint8)], axis=2))


def stage_json(path):
    out = {"stage": "camp", "ground_y_m": 0.0, "spawn_x_m": SPAWN_X, "haze_rgb": [round(float(v), 3) for v in HAZE], "layers": LAYERS,
           "light": {"pool_x_m": POOL["x"], "pool_y_m": POOL["y"], "pool_rx_m": POOL["rx"], "pool_ry_m": POOL["ry"],
                     "warm": [round(float(v), 3) for v in WARM], "shade": [round(float(v), 3) for v in SHADE]},
           "pit": PIT, "instances": []}
    for layer, L in STAGE.items():
        for pid, x_m, y_m, scale, flip in L["pieces"]:
            out["instances"].append({"piece": pid, "layer": layer, "x_m": x_m, "y_m": y_m, "scale": scale, "flip": flip,
                                     **({"x_from": "the view's edge (a negative x: its right edge)"} if layer == "foreground" else {})})
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1)
    return len(out["instances"])


def sheet(out, peak=None):
    import review
    paper = np.array(review.PAPER, np.float32)

    def head(text, h=20):
        hd = np.tile(paper, (h, W, 1)).astype(np.float32)
        review._label(hd, text[:310], 6, 4, scale=1)
        return hd
    rows = [head("B-258 part 3 (ART v7, the living painting): THE FRAME, composed from pieces - CC0 scans (Poly Haven) rendered and painted ONE PIECE AT A TIME in Blender, "
                 "laid out by numpy. PREVIEW, nothing exported; raw scans never ship", 26)]
    SPOTS = {96: (("stage", 8.3, 1.2), ("trunk", 2.6, 1.7), ("pit", 12.6, -1.3), ("right", 17.3, 1.0)), 128: (("stage", 8.3, 0.9), ("corner", 3.6, -1.6))}
    small, wins, lines = {}, {}, []
    for ppm in (96, 128):                                                                             # one picture in memory at a time
        F = Frame(ppm)
        F.compose()
        small[ppm] = F.shrunk()
        save(os.path.join(D, f"frame_{ppm}.png"), small[ppm])
        wins[ppm] = [F.window(x_m, y_m).copy() for _, x_m, y_m in SPOTS[ppm]]
        for (what, _, _), wn in zip(SPOTS[ppm], wins[ppm]):
            save(os.path.join(D, f"frame_{ppm}_2x_{what}.png"), wn)
        lines.append(f"frame at {ppm} px per metre: {'; '.join(F.log)}")
        print("frame", ppm, "; ".join(F.log), flush=True)
        del F
    rows += [head("THE NEW FRAME, the play plane at 96 px per metre (the grey figure is a 1.84 m mannequin for scale; the camp's kit is B-261's and is not in it)"), small[96]]
    if os.path.isfile(OLD):
        rows += [head("THE OLD FRAME beside it at the same size (b251/forest_frame_96_plates.png: art v6, drawn and painted by code, with LEAD's AI-painted plates)"),
                 pngio.read_png_np(OLD).astype(np.float32)[..., :3] / 255.0]
    rows += [head("THE SAME STAGE, the play plane at 128 px per metre (the camera closer: 15 x 8.4 m of the world instead of 20 x 11.25)"), small[128]]
    for ppm in (96, 128):
        rows.append(head(f"WINDOWS OF THE {ppm} FRAME AT TWICE ITS SIZE (the picture as it was composed: no pixel enlarged): " + ", ".join(s[0] for s in SPOTS[ppm])))
        for i in range(0, len(wins[ppm]), 2):
            pair = wins[ppm][i:i + 2]
            rows.append(np.hstack(pair + [np.tile(paper, (540, W - 960 * len(pair), 1)).astype(np.float32)] * (len(pair) < 2)))
    n_inst = stage_json(os.path.join(D, "stage_camp.json"))
    used = sorted({p[0] for L in STAGE.values() for p in L["pieces"]})
    tot_r = tot_p = tex = 0.0
    mem96 = 0
    for pid in used:
        m = piece(pid)[1]
        tot_r, tot_p, tex = tot_r + m.get("render_s", 0), tot_p + m.get("paint_s", 0), tex + m.get("texture_s", 0)
        w_, h_ = m["size_px"]
        mem96 += int(w_ * 192.0 / m["px_per_m"]) * int(h_ * 192.0 / m["px_per_m"]) * 4 if m["kind"] != "far" else w_ * h_ * 4
    lines.insert(0, f"{len(used)} pieces, {n_inst} placements (blender/preview/b258/stage_camp.json, B-260's stage format). Blender: render {tot_r:.0f} s, repainting the materials {tex:.0f} s, "
                    f"the brush {tot_p:.0f} s, all pieces together" + (f"; PEAK RAM of the Blender runs {peak} MB" if peak else "") + ".")
    lines.insert(1, f"Texture memory if these {len(used)} pieces shipped at 192 px per metre (the far stand at its own size), uncompressed RGBA: {mem96 / 1048576:.1f} MB colour, the same again for normal maps.")
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:310], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-258 part 3: the frame from pieces (Blender renders, numpy layout; nothing exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    print("stage:", check_stage(), "placements; D-206's rules hold", flush=True)
    if len(sys.argv) > 2 and sys.argv[1] == "one":                                                    # one frame only, to look at: one <ppm>
        F = Frame(int(sys.argv[2]))
        F.compose()
        save(os.path.join(D, f"frame_{F.P}.png"), F.shrunk())
        print("frame", F.P, "; ".join(F.log))
    else:
        sheet(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
