"""B-210 (D-174; Bible 5.2 §8.1, the ways back up): the climbing props in v3 ink, Earth palette, no glow, no faces.

  props/dig/ladder           48x64 @ PPU 64, pivot [0.5, 0]: a 1 m piece of the Builder ladder (wooden rails, rungs packed with
                             dirt at the joints), tiles in y (repeat_px 64)
  props/dig/ladder_top       48x32: the rails' rounded caps over a dirt plug (sits on the topmost piece)
  props/dig/ladder_bottom    64x32: the rails' feet driven into a dirt heap (under the lowest piece)
  props/dig/grapple_line     16x64: the grapple line, a twisted rope, tiles in y
  props/dig/grapple_hook     96x96, pivot [0.5, 0.5]: the three-pronged hook bitten into a rock; json "line_socket" (where the line
                             tile hangs from)
  props/dig/winch_post       96x160, pivot [0.5, 0.2] = its base on the Surface Line: a brass post staked down, a drum of line,
                             a crank, the Surface Line's red pennant on top; json "line_socket"
  props/dig/recall_beacon    64x192 frames, pivot [0.5, 0]: clips pulse (4, loop: the lamp and two ink rings, no glow) and
                             liftoff (6, once: a squash, then it shoots up trailing paper streamers)

  python -I build_dig_props_v3.py <review png>     the lock-free sheet: the props, and the surveyor's new clips on them
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp, v3  # noqa: E402
import build_icons_items_v3 as IT  # noqa: E402   (installs fakegp; materials <tone>[_sh|_dp][_i], ink)

G = IT.G
import gp_raster as GR  # noqa: E402

O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
PPU = 64


def render(fn, w, h, piv, seed=5):
    gp = fakegp.FakeGP()
    M = IT.mats(gp, "earth")
    d = fakegp.FakeDrawing()
    fn(d, M)
    return GR.render_frame(fakegp.strokes_of(d, gp), w, h, PPU, piv, ss=4, seed=seed)[0]


def hose(pts, w):
    return G.hose_outline(pts, w)


def circ(cx, cz, r, n=20):
    return [(cx + r * math.cos(TAU * i / n), cz + r * math.sin(TAU * i / n)) for i in range(n)]


# ---------------------------------------------------------------- the ladder
RX = 0.24


def rails(d, M, z0, z1):
    for x in (-RX, RX):
        G.stroke(d, hose([(x, z0), (x, z1)], 0.07), M["brown_i"], I * 1.3, cyclic=True)
        G.stroke(d, hose([(x + 0.012, z0), (x + 0.012, z1)], 0.018), M["brown_sh"], 0.0, cyclic=True)


def rung(d, M, z, seed):
    G.stroke(d, hose([(-RX, z), (RX, z)], 0.06), M["mustard_sh_i"], I, cyclic=True)
    rnd = np.random.default_rng(seed)
    for x in (-RX, RX):                                                                       # dirt packed round the joints
        G.stroke(d, IT.lump(x, z, 0.06, 0.05, int(rnd.integers(1, 99)), n=8), M["brown_sh_i"], I, cyclic=True)
    G.stroke(d, IT.lump(rnd.uniform(-0.06, 0.06), z + 0.035, 0.035, 0.02, int(rnd.integers(1, 99)), n=6), M["brown_sh"], 0.0, cyclic=True)


def ladder(d, M):
    rails(d, M, -0.2, 1.2)                                                                    # past both edges: tiles in y
    for z, s in ((0.25, 11), (0.75, 12)):
        rung(d, M, z, s)


def ladder_top(d, M):
    rails(d, M, -0.1, 0.3)
    for x in (-RX, RX):
        G.stroke(d, circ(x, 0.3, 0.045, 14), M["brown_i"], I * 1.3, cyclic=True)
    rung(d, M, 0.12, 13)


def ladder_bottom(d, M):
    rails(d, M, 0.1, 0.6)
    G.stroke(d, IT.lump(0.0, 0.06, 0.42, 0.13, 21, n=12), M["brown_sh_i"], O, cyclic=True)    # the dirt heap round the feet
    for x, z in ((-0.3, 0.12), (0.06, 0.16), (0.3, 0.1)):
        G.stroke(d, IT.lump(x, z, 0.05, 0.035, int(100 * x) + 50, n=6), M["brown_i"], I, cyclic=True)


# ---------------------------------------------------------------- the grapple line + hook, the winch post
def grapple_line(d, M):
    G.stroke(d, hose([(0.0, -0.2), (0.0, 1.2)], 0.07), M["mustard_sh_i"], I, cyclic=True)
    for k in range(10):                                                                       # the twist, period 0.1 m
        z = 0.05 + 0.1 * k
        G.seam(d, [(-0.03, z - 0.03), (0.03, z + 0.03)], M["ink"])


HOOK_LINE = (0.0, -0.42)                                                                      # the line hangs from the shank's eye


def grapple_hook(d, M):
    IT.faceted(d, M, IT.lump(0.0, 0.18, 0.62, 0.28, 31, n=10), "sky_sh", "sky", "sky_dp", 0.0, 0.18)   # the rock overhead
    for k, x in enumerate((-0.3, 0.1, 0.38)):
        G.seam(d, [(x, 0.05), (x + 0.06, 0.2)], M["ink"])
    G.stroke(d, hose([(0.0, -0.36), (0.0, 0.04)], 0.06), M["sky_sh_i"], O, cyclic=True)        # the shank
    for s in (-1, 1):                                                                         # the prongs, bitten into the rock
        G.stroke(d, hose([(0.0, 0.0), (s * 0.14, 0.04), (s * 0.2, 0.1)], 0.045), M["sky_i"], I, cyclic=True)
        G.seam(d, [(s * 0.17, 0.08), (s * 0.24, 0.12)], M["ink"])                              # cracks where they bite
    G.stroke(d, circ(0.0, -0.39, 0.05, 16), M["sky_i"], I, cyclic=True)                       # its eye
    G.stroke(d, hose([(0.0, -0.44), (0.0, -0.62)], 0.07), M["mustard_sh_i"], I, cyclic=True)    # the line leaving it


WINCH_LINE = (0.27, 0.62)


def winch_post(d, M):
    G.stroke(d, [(-0.36, 0.0), (0.36, 0.0), (0.32, 0.08), (-0.32, 0.08)], M["mustard_sh_i"], I, cyclic=True)   # the base plate
    for x in (-0.26, 0.26):                                                                   # its stakes into the ground
        G.stroke(d, [(x - 0.03, 0.0), (x + 0.03, 0.0), (x, -0.4)], M["sky_sh_i"], I, cyclic=True)
    G.stroke(d, [(-0.07, 0.08), (0.07, 0.08), (0.06, 1.55), (-0.06, 1.55)], M["mustard_i"], O, cyclic=True)    # the brass post
    G.stroke(d, [(0.02, 0.08), (0.07, 0.08), (0.06, 1.55), (0.02, 1.55)], M["mustard_sh"], 0.0, cyclic=True)
    for z in (0.35, 1.2):
        G.stroke(d, [(-0.085, z), (0.085, z), (0.085, z + 0.05), (-0.085, z + 0.05)], M["mustard_dp_i"], I, cyclic=True)
    G.stroke(d, [(-0.2, 0.62), (0.2, 0.62), (0.2, 0.98), (-0.2, 0.98)], M["sky_sh_i"], O, cyclic=True)      # the drum
    for k in range(5):
        z = 0.67 + 0.065 * k
        G.stroke(d, hose([(-0.18, z), (0.18, z + 0.01)], 0.03), M["mustard_sh"], I * 0.6, cyclic=True)    # the line on it
    G.stroke(d, hose([(-0.2, 0.8), (-0.32, 0.8), (-0.32, 0.92)], 0.035), M["red_sh_i"], I, cyclic=True)    # the crank
    G.stroke(d, hose([(0.2, 0.68), (0.27, 0.66), (0.27, 0.6)], 0.035), M["mustard_sh_i"], I, cyclic=True)   # the line leaving
    G.stroke(d, [(0.06, 1.55), (0.06, 1.88)], M["ink"], I * 1.4)                                   # the pennant
    G.stroke(d, [(0.06, 1.88), (0.06, 1.68), (0.3, 1.78)], M["red_i"], I, cyclic=True)


# ---------------------------------------------------------------- the recall beacon
def beacon(state, k):
    """state 'pulse' (k 0-3) or 'liftoff' (k 0-5)."""
    def fn(d, M):
        lift, sq, streamers = 0.0, 1.0, 0
        if state == "liftoff":
            lift = [0.0, 0.05, 0.3, 0.7, 1.1, 1.5][k]
            sq = [0.8, 1.25, 1.15, 1.08, 1.04, 1.0][k]
            streamers = [0, 0, 1, 2, 3, 3][k]
        S = lambda pts: [(x / math.sqrt(sq), z * sq + lift) for x, z in pts]  # noqa: E731
        if lift < 0.2:                                                                            # its foot spikes, in the ground
            for x in (-0.12, 0.12):
                G.stroke(d, [(x - 0.035, 0.12), (x + 0.035, 0.12), (x, -0.0)], M["brown_i"], I, cyclic=True)
        for j in range(streamers):                                                                 # paper streamers trailing
            col = ("red", "mustard", "off")[j]
            x0 = (-0.12, 0.0, 0.12)[j]
            pts = [(x0 + 0.06 * math.sin(2.5 * t + j + k), lift - 0.05 - 0.5 * t * (0.6 + 0.2 * j)) for t in [i / 8 for i in range(9)]]
            pts = [(x, max(z, 0.05)) for x, z in pts]
            G.stroke(d, hose(pts, 0.045), M[col + "_i"], I * 0.8, cyclic=True)
        G.stroke(d, S([(-0.16, 0.1), (0.16, 0.1), (0.12, 0.2), (-0.12, 0.2)]), M["brown_i"], I, cyclic=True)    # its foot
        G.stroke(d, S([(-0.04, 0.2), (0.04, 0.2), (0.035, 0.85), (-0.035, 0.85)]), M["sky_sh_i"], O, cyclic=True)  # the mast
        lamp_role = "red" if (state == "liftoff" or k % 2 == 0) else "mustard"
        G.stroke(d, S(circ(0.0, 0.95, 0.1, 22)), M[lamp_role + "_i"], O, cyclic=True)                      # the lamp
        G.stroke(d, S([(0.0 + 0.06 * math.cos(a), 0.95 + 0.06 * math.sin(a)) for a in (2.0, 2.3, 2.6, 2.9)]), M["off"], I * 1.2)
        if state == "pulse":                                                                       # two ink rings going out
            for j, r in enumerate((0.16 + 0.05 * k, 0.24 + 0.05 * k)):
                if r < 0.4:
                    G.stroke(d, G.hose_outline([(0.0 + r * math.cos(a), 0.95 + r * math.sin(a)) for a in [math.radians(30 + 120 * i / 12) for i in range(13)]], 0.02),
                             M["red_sh"], 0.0, cyclic=True)
    return fn


BEACON_W, BEACON_H = 64, 192


def beacon_sheet():
    frames = [render(beacon("pulse", k), BEACON_W, BEACON_H, (0.5, 0.0), seed=60 + k) for k in range(4)] + \
             [render(beacon("liftoff", k), BEACON_W, BEACON_H, (0.5, 0.0), seed=70 + k) for k in range(6)]
    cols = v3.columns_for(BEACON_W, len(frames))
    rows = -(-len(frames) // cols)
    g = v3.GUTTER
    sheet = np.zeros((rows * BEACON_H + (rows - 1) * g, cols * BEACON_W + (cols - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (BEACON_H + g):r * (BEACON_H + g) + BEACON_H, c * (BEACON_W + g):c * (BEACON_W + g) + BEACON_W] = im
    meta = {"frame_width": BEACON_W, "frame_height": BEACON_H, "columns": cols, "gutter": g, "frames": len(frames), "fps": v3.FPS,
            "pivot": [0.5, 0.0], "facing": "right", "animations": [{"name": "pulse", "start": 0, "length": 4, "loop": True, "loop_from": 0},
                                                                   {"name": "liftoff", "start": 4, "length": 6, "loop": False}]}
    return frames, sheet, meta


PIECES = {"ladder": (ladder, 48, 64, (0.5, 0.0), {"tile_y": True, "repeat_px": 64}),
          "ladder_top": (ladder_top, 48, 32, (0.5, 0.0), {}),
          "ladder_bottom": (ladder_bottom, 64, 48, (0.5, 0.25), {}),
          "grapple_line": (grapple_line, 16, 64, (0.5, 0.0), {"tile_y": True, "repeat_px": 64}),
          "grapple_hook": (grapple_hook, 96, 96, (0.5, 0.5), {"line_socket": list(HOOK_LINE)}),
          "winch_post": (winch_post, 96, 160, (0.5, 0.2), {"line_socket": list(WINCH_LINE), "stands_on": "the Surface Line (its base on the line)"})}


def pieces():
    return {n: render(fn, w, h, piv, seed=40 + i) for i, (n, (fn, w, h, piv, _m)) in enumerate(PIECES.items())}


# ---------------------------------------------------------------- the review sheet (lock-free)
def preview(out, footnote=None):
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_surveyor_side_b as SB
    P = pieces()
    bframes, _sheet, _meta = beacon_sheet()
    sb_frames = []
    poses = SB.all_poses()
    first = len(poses) - 16
    for f in range(first, len(poses)):                                                        # the two new clips, through fakegp
        gp = fakegp.FakeGP()
        M = SB.materials(gp)
        d = fakegp.FakeDrawing()
        SB.draw_side_b(d, M, poses[f], seed=7 * f)
        sb_frames.append(GR.render_frame(fakegp.strokes_of(d, gp), 192, 192, 64, (0.5, 0.0), ss=2, seed=SB.SEED * 1000 + f + 1)[0])
    socks = SB.sockets()

    def ov(dst, fr, x, y):
        h, w = fr.shape[:2]
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
        if x1 > x0 and y1 > y0:
            f = fr[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32) / 255.0
            a = f[..., 3:4]
            dst[y0:y1, x0:x1] = f[..., :3] * a + dst[y0:y1, x0:x1] * (1 - a)
    dirt = np.array(v3.hex_rgb(v3.deep_of(v3.PALETTES["earth"]["mustard"], "earth")), np.float32) / 255.0
    W = 1800
    rows = []
    head = np.tile(np.array(review.PAPER, np.float32), (26, W, 1))
    review._label(head, "B-210 the ways back up: climb_ladder on the ladder, reel_up under the grapple line, the winch post on the Surface Line, the recall beacon", 6, 6)
    rows.append(head)
    # climb_ladder over the ladder tiles (a dug shaft)
    r1 = np.empty((260, W, 3), np.float32)
    r1[:] = dirt
    review._label(r1, "climb_ladder (8, loop) on props/dig/ladder (tiled) + its caps", 6, 4, scale=1)
    for k in range(8):
        x0 = 10 + k * 220
        cx = x0 + 96 + int(round(SB.LADDER[0] * 64))                                          # the ladder under the hands (socket)
        for z in range(-1, 4):                                                                 # the ladder column behind
            ov(r1, P["ladder"], cx - 24, 250 - 64 * (z + 1))
        ov(r1, sb_frames[k], x0, 250 - 192 + 0)
    rows.append(r1)
    # reel_up under the line from a hook
    r2 = np.empty((330, W, 3), np.float32)
    r2[:] = dirt
    review._label(r2, "reel_up (8, loop): the line tile from the hook down to the frame's reel socket", 6, 4, scale=1)
    for k in range(8):
        x0 = 10 + k * 220
        fi = first + 8 + k
        sx, sz = socks[str(fi + 1)]["reel"]
        feet_x, feet_y = x0 + 96, 320
        rx, ry = int(feet_x + sx * 64), int(feet_y - sz * 64)
        hx, hy = rx, 70
        y = hy + 26
        while y + 64 <= ry + 4:                                                               # the line, tiled down
            ov(r2, P["grapple_line"], rx - 8, y)
            y += 64
        ov(r2, P["grapple_line"][:max(1, ry - y + 4)], rx - 8, y)
        ov(r2, P["grapple_hook"], hx - 48, hy - 48)
        ov(r2, sb_frames[8 + k], x0, feet_y - 192)
    rows.append(r2)
    # the winch post on the Surface Line, the props alone, the beacon
    r3 = np.empty((300, W, 3), np.float32)
    r3[:] = np.array(v3.hex_rgb(v3.PALETTES["earth"]["sky"]), np.float32) / 255.0
    r3[150:] = dirt
    import build_ground_variants_v3 as GV
    GV.use_planet("earth", "tiers")
    line = GV.render_piece("surface_line", 0)[0]
    ov(r3, np.tile(line, (1, 7, 1))[:, :W], 0, 228 - GV.SL_ROW)
    ov(r3, P["winch_post"], 60, 228 - 128)                                                    # its base (pivot 0.2 = row 128) on the line
    review._label(r3, "winch_post on the Surface Line | the ladder pieces, the line and the hook at 1x | recall_beacon: pulse 4 + liftoff 6", 6, 4, scale=1)
    x = 200
    for n in ("ladder_top", "ladder", "ladder_bottom", "grapple_line", "grapple_hook"):
        ov(r3, P[n], x, 40)
        review._label(r3, n, x, 24, scale=1)
        x += P[n].shape[1] + 24
    for k, fr in enumerate(bframes):
        ov(r3, fr, x + k * 70, 296 - 192)
    rows.append(r3)
    lines = []
    for n, img in list(P.items()) + [(f"recall_beacon {i}", f) for i, f in enumerate(bframes)]:
        hit = v3.palette_hits(img, "earth")[0] * 100
        m = v3.EDGE_MARGIN
        ty = n in ("ladder", "grapple_line")
        top_open = ty or n == "ladder_bottom"                                                 # the caps' joining edges, the beacon's
        bottom_open = ty or n == "ladder_top" or n.startswith("recall_beacon")                 # ground contact (pivot [0.5, 0])
        edge = (not top_open and img[:m, :, 3].any()) or (not bottom_open and img[-m:, :, 3].any()) or img[:, :m, 3].any() or img[:, -m:, 3].any()
        lines.append(f"{n}: {img.shape[1]}x{img.shape[0]}, palette {hit:.1f}%" + ("; EDGE" if edge else ""))
    for i, f in enumerate(sb_frames):
        m = v3.EDGE_MARGIN
        if f[:m, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any():
            lines.append(f"side_b frame {first + i}: EDGE")
    foot = np.tile(np.array(review.PAPER, np.float32), (24 + 16 * ((len(lines) + 2) // 3), W, 1))
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6 + (i % 3) * 600, 6 + 16 * (i // 3), scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_dig_props_v3.py <review png>
    preview(sys.argv[1])
    fakegp.restore()
