"""B-213 (D1): the first hour's hint cards - six small paper cards in UiKit's style, each a baked pictogram + a key cap,
the words lettered at runtime by UNITY; plus a small pointing paper arrow.

  ui/hints/<name>   320x200, 9-slice, pivot centre, ppu 64, flat paper (ui/panels/grain overlays it, as B-208's panels):
      dig_down      B-229: the shovel mid-scoop in a fresh pit, a clod flicked up and back; the mouse (left button) on its corner
      surface_line  the dashed Surface Line with its pennant: sky and sun above, the dirt below
      sell          the pack -> brass Scrip coins, topside; a key cap (G)
      skill_tree    the chart: the hub, its rings and nodes; a key cap (K)
      climb_up      a ladder up a shaft, the jetpack, the grapple; a key cap (the climb binding)
      pack_full     the bulging pack, the red PACK FULL stamp pressed across it
  ui/hints/arrow    72x48, pivot at the tip: UNITY turns it about the tip to aim it at a HUD element

  The layout (px from the top-left): the title strip across the top (42..278 x 22..48, Limelight), the pictogram window
  bottom-left (22..138 x 58..174) with the key cap / mouse on its corner (100..146 x 132..178), the body text to its right
  (156..296 x 62..176, Patrick Hand). slice [l 152, t 52, r 44, b 144]: the pictogram, the key cap and the four corner curls
  sit in fixed corner slices; the stretched columns hold only the title / body paper and the horizontal rules, the stretched
  rows (52..56) only paper between the side rules.

  python -I build_hints_v3.py <review png>     the lock-free sheet (sample lettering, as UNITY will letter it)
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ui_v3 as U  # noqa: E402
import build_skilltree_v3 as ST  # noqa: E402
from meridian import v3  # noqa: E402

G, O, I = U.G, U.O, U.I
TAU = 2 * math.pi
circ, extra, done = ST.circ, ST.extra, ST.done

CW, CH = 320, 200
SLICE = [152, 52, 44, 144]                    # [left, top, right, bottom] px in from each edge (contract 11.6)
WIN = (22, 58, 138, 174)                      # the pictogram window
CAP = (100, 132, 146, 178)                    # the key cap / mouse on the window's corner
TITLE = (42, 22, 278, 48)
BODY = (156, 62, 296, 176)
CARDS = ("dig_down", "surface_line", "sell", "skill_tree", "climb_up", "pack_full")
KEY = {"dig_down": "mouse_left", "surface_line": None, "sell": "G", "skill_tree": "K", "climb_up": "climb", "pack_full": None}
SAMPLE = {"dig_down": ("DIG DOWN", "hold the left button: the shovel digs"),
          "surface_line": ("THE SURFACE LINE", "above it you're topside"),
          "sell": ("SELL", "topside, press G to sell your pack for Scrip"),
          "skill_tree": ("THE SKILL TREE", "press K to spend Scrip on new nodes"),
          "climb_up": ("CLIMB BACK UP", "a ladder, the jetpack or the grapple"),
          "pack_full": ("PACK FULL", "climb up and sell")}
AW, AH, ATIP = 72, 48, (66, 24)


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def rrect(x0, y0, x1, y1, r, n=5):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -math.pi / 2), (x1 - r, y1 - r, 0.0), (x0 + r, y1 - r, math.pi / 2), (x0 + r, y0 + r, math.pi)):
        pts += [(cx + r * math.cos(a0 + (math.pi / 2) * i / n), cy + r * math.sin(a0 + (math.pi / 2) * i / n)) for i in range(n + 1)]
    return pts


def wavy_band(x0, x1, y, amp, seed, n=12):
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, TAU)
    return [(x0 + (x1 - x0) * i / n, y + amp * math.sin(ph + 2.3 * i)) for i in range(n + 1)]


def band(d, M, mat, x0, x1, ytop, ybot, seed, amp=1.2):
    """A wavy-topped band in the window from ytop down to ybot (straight bottom)."""
    G.stroke(d, Ps(wavy_band(x0, x1, ytop, amp, seed) + [(x1, ybot), (x0, ybot)]), M[mat], 0.0, cyclic=True)


def arrow_pts(x0, y0, x1, y1, shaft=0.36, head=0.42, up=False):
    """A block arrow in the box, pointing right (or up)."""
    if up:
        w, h = x1 - x0, y1 - y0
        cx = (x0 + x1) / 2
        sw, hh = w * shaft / 2, h * head
        return [(cx - sw, y1), (cx - sw, y0 + hh), (x0, y0 + hh), (cx, y0), (x1, y0 + hh), (cx + sw, y0 + hh), (cx + sw, y1)]
    w, h = x1 - x0, y1 - y0
    cy = (y0 + y1) / 2
    sh, hw = h * shaft / 2, w * head
    return [(x0, cy - sh), (x1 - hw, cy - sh), (x1 - hw, y0), (x1, cy), (x1 - hw, y1), (x1 - hw, cy + sh), (x0, cy + sh)]


# ---------------------------------------------------------------- the card's paper (flat; the grain is UNITY's overlay)
def paper(d, M, seed):
    outer = U.wavy_rect(6, 6, CW - 6, CH - 6, 1.0, seed)
    G.stroke(d, outer, M["offwhite_f"], 0.0, cyclic=True)
    G.stroke(d, U.wavy_rect(16, 16, CW - 16, CH - 16, 0.5, seed + 2), M["mustard"], I, cyclic=True)      # the inner rule
    G.stroke(d, U.wavy_rect(20, 20, CW - 20, CH - 20, 0.4, seed + 3), M["offwhite_f"], 0.0, cyclic=True)
    G.stroke(d, [(24, 51), (CW - 24, 51)], M["ln_brown"], I)                                             # the title's rule
    for (cx, cy, fx, fy) in ((30, 30, 1, 1), (CW - 30, 30, -1, 1), (30, CH - 30, 1, -1), (CW - 30, CH - 30, -1, -1)):
        U.curl(d, M, cx, cy, 6, fx, fy)                                                                  # inside corner slices
    return outer


def window(d, M, seed):
    x0, y0, x1, y1 = WIN
    return U.wavy_rect(x0, y0, x1, y1, 0.5, seed + 5)


def P(u, v):
    return (WIN[0] + u, WIN[1] + v)


def Ps(pts):
    return [P(u, v) for u, v in pts]


def keycap(d, M, seed):
    x0, y0, x1, y1 = CAP
    G.stroke(d, rrect(x0, y0, x1, y1, 7), M["offwhite_sh"], 0.0, cyclic=True)                         # the cap's side
    G.stroke(d, rrect(x0 + 4, y0 + 2, x1 - 4, y1 - 9, 6), M["offwhite"], I, cyclic=True)              # its top face
    G.stroke(d, rrect(x0, y0, x1, y1, 7), M["ink"], O, cyclic=True)


def mouse(d, M, seed):
    cx, cy, rx, ry = (CAP[0] + CAP[2]) / 2, (CAP[1] + CAP[3]) / 2, 18, 22
    body = circ(cx, cy, rx, 48, ry)
    G.stroke(d, body, M["offwhite_f"], 0.0, cyclic=True)
    split = cy - 3
    left = [(cx - rx * math.cos(a), cy - ry * math.sin(a)) for a in np.linspace(math.asin(min(1, (cy - split) / ry)), math.pi / 2, 12)]
    G.stroke(d, [(cx, split)] + left + [(cx, cy - ry)], M["teal_f"], 0.0, cyclic=True)                 # the left button, pressed
    G.stroke(d, [(cx - rx + 1, split), (cx + rx - 1, split)], M["ink"], I)
    G.stroke(d, [(cx, cy - ry), (cx, split)], M["ink"], I)
    G.stroke(d, [(cx, cy - ry), (cx + 2, cy - ry - 4), (cx - 1, cy - ry - 8)], M["ink"], I)           # the lead
    G.stroke(d, body, M["ink"], O, cyclic=True)


# ---------------------------------------------------------------- the six pictograms (window units: u, v in 0..116)
def pic_dig_down(d, M, seed):
    G.stroke(d, Ps(rect(0, 0, 116, 36)), M["sky_f"], 0.0, cyclic=True)
    band(d, M, "brown_f", 0, 116, 34, 116, seed)
    band(d, M, "mustard_sh", 0, 116, 62, 72, seed + 1, 1.0)
    band(d, M, "brown_f", 0, 116, 71, 116, seed + 2, 1.0)
    band(d, M, "red_sh", 0, 116, 96, 104, seed + 3, 1.0)
    band(d, M, "brown_f", 0, 116, 103, 116, seed + 4, 1.0)
    G.stroke(d, Ps(wavy_band(0, 116, 33, 0.8, seed + 5) + [(116, 39), (0, 39)]), M["green"], I, cyclic=True)   # the turf
    # B-229 (D-182: the first tool is the shovel): B-226's shovel mid-scoop in a fresh pit, dirt on its blade, a clod flicked
    # up and back over the haft (the Beam drilling a shaft was here)
    pit = [(50, 36), (78, 36)] + [(64 + 14 * math.cos(a), 37 + 13 * math.sin(a)) for a in np.linspace(0, math.pi, 11)]
    G.stroke(d, Ps(pit), M["brown_dp"], 0.0, cyclic=True)                                                     # the scooped pit
    G.stroke(d, Ps(pit[1:]), M["ink"], I)                                                                     # (open at the turf)
    for x, y, r in ((44, 34, 3.5), (84, 34, 3.0), (89, 35, 2.2)):                                             # spoil on the turf
        G.stroke(d, Ps(circ(x, y, r, 10, r * 0.75)), M["brown"], I * 0.8, cyclic=True)
    g0, tip = (30.0, 11.0), (66.0, 47.0)                                                                      # the shovel: grip -> tip
    L = math.hypot(tip[0] - g0[0], tip[1] - g0[1])
    du, dv = (tip[0] - g0[0]) / L, (tip[1] - g0[1]) / L
    nu, nv = -dv, du                                                                                          # across the shovel

    def S(s, t=0.0):
        return (g0[0] + du * s + nu * t, g0[1] + dv * s + nv * t)
    dg = [S(-3.5, -5.5), S(-3.5, 5.5)] + [S(1.0 + 5.0 * math.cos(a), 5.5 * math.sin(a)) for a in np.linspace(math.pi / 2, -math.pi / 2, 9)]
    G.stroke(d, G.hose_outline(Ps(dg + [dg[0]]), 2.6), M["mustard"], I, cyclic=True)                          # the brass D-grip
    # the surveyor's hand on it (LEAD 14:1x: the card says "in the surveyor's hand"; no face): the off-white sleeve in from the
    # window's left edge, the mustard cuff, the white mitt closed over the D-grip's bar (the loop shows past the fingers)
    G.stroke(d, Ps([(0, 0.8), (16.0, 3.0), (14.6, 11.4), (0, 9.4)]), M["offwhite"], I, cyclic=True)           # the sleeve
    G.stroke(d, Ps([(15.0, 2.2), (22.5, 3.6), (21.3, 12.6), (13.8, 11.2)]), M["mustard"], I, cyclic=True)     # the cuff
    mc = S(-4.4)
    G.stroke(d, Ps(G.lumpy_ellipse(mc[0], mc[1], 5.4, 4.8, n=20, lump=0.05, seed=seed + 9)), M["offwhite"], I * 1.4, cyclic=True)   # the mitt
    for t in (-1.7, 1.7):                                                                                      # two finger seams
        G.stroke(d, Ps([S(-6.6, t), S(-2.4, t)]), M["ink"], I * 0.8)
    G.stroke(d, G.hose_outline(Ps([S(6), S(L * 0.58)]), 4.6), M["teal"], I, cyclic=True)                      # the teal haft
    G.stroke(d, Ps([S(L * 0.56, -3.2), S(L * 0.63, -3.2), S(L * 0.63, 3.2), S(L * 0.56, 3.2)]), M["mustard"], I, cyclic=True)   # ferrule
    blade = [S(L * 0.63, -6.5), S(L * 0.74, -7.5), S(L * 0.88, -6.0), S(L, 0.0), S(L * 0.88, 6.0), S(L * 0.74, 7.5), S(L * 0.63, 6.5)]
    G.stroke(d, Ps(blade), M["sky"], O, cyclic=True)                                                          # the steel blade
    G.stroke(d, Ps([S(L * 0.64, -6.0), S(L * 0.74, -6.8), S(L * 0.86, -5.4), S(L * 0.76, -3.5)]), M["offwhite_f"], 0.0, cyclic=True)   # lit edge
    G.stroke(d, Ps([S(L * 0.66, 0.0), S(L * 0.93, 0.0)]), M["ink"], I)                                        # the rib
    for s, t, r in ((0.72, -7.0, 4.2), (0.81, -6.5, 3.6), (0.66, -6.0, 3.0)):                                # dirt riding the blade
        cx, cy = S(L * s, t)
        G.stroke(d, Ps(circ(cx, cy, r, 10, r * 0.8)), M["brown"], I, cyclic=True)
    G.stroke(d, Ps(circ(50, 13, 5.0, 12, 4.2)), M["brown"], I, cyclic=True)                                  # the flicked clod, up
    for x, y, r in ((57, 22, 2.2), (59.5, 25.5, 1.8), (53, 19, 1.6)):                                         # and back, crumbs after it
        G.stroke(d, Ps(circ(x, y, r, 8, r * 0.85)), M["brown"], I * 0.8, cyclic=True)
    for k in range(2):                                                                                        # its motion arcs
        G.stroke(d, Ps([(58 + 4 * k, 9 + 3 * k), (63 + 4 * k, 13 + 3 * k), (66 + 4 * k, 19 + 3 * k)]), M["ink"], I)
    G.stroke(d, Ps([(88, 42), (100, 42), (100, 56), (106, 56), (94, 70), (82, 56), (88, 56)]), M["red"], I, cyclic=True)   # down


def pic_surface_line(d, M, seed):
    G.stroke(d, Ps(rect(0, 0, 116, 60)), M["sky_f"], 0.0, cyclic=True)
    G.stroke(d, Ps([(30 + 16 * math.cos(a), 58 - 16 * math.sin(a)) for a in np.linspace(0, math.pi, 16)]), M["mustard"], I, cyclic=True)  # the sun
    band(d, M, "brown_f", 0, 116, 58, 116, seed)
    band(d, M, "mustard_sh", 0, 116, 86, 94, seed + 1, 1.0)
    band(d, M, "brown_f", 0, 116, 93, 116, seed + 2, 1.0)
    G.stroke(d, Ps(wavy_band(0, 116, 56, 0.6, seed + 3) + [(116, 61), (0, 61)]), M["green"], I, cyclic=True)
    for k in range(6):                                                                                         # the dashed line
        x = 4 + 19 * k
        G.stroke(d, Ps(rrect(x, 55.5, x + 11, 61.5, 2, 3)), M["offwhite"], I, cyclic=True)
    G.stroke(d, G.hose_outline(Ps([(86, 58), (86, 16)]), 2.4), M["brown"], I, cyclic=True)                   # the pennant
    G.stroke(d, Ps([(87, 16), (87, 31), (106, 23)]), M["red"], I, cyclic=True)
    G.stroke(d, Ps([(56, 40), (64, 31), (72, 40), (68, 40), (64, 36), (60, 40)]), M["offwhite"], I, cyclic=True)   # up: topside
    G.stroke(d, Ps([(56, 72), (64, 81), (72, 72), (68, 72), (64, 76), (60, 72)]), M["offwhite"], I, cyclic=True)   # down: below


def pic_sell(d, M, seed):
    G.stroke(d, Ps(rect(0, 0, 116, 80)), M["sky_f"], 0.0, cyclic=True)
    band(d, M, "brown_f", 0, 116, 78, 116, seed)
    band(d, M, "mustard_sh", 0, 116, 100, 108, seed + 1, 1.0)
    G.stroke(d, Ps(wavy_band(0, 116, 76, 0.6, seed + 2) + [(116, 82), (0, 82)]), M["green"], I, cyclic=True)
    G.stroke(d, Ps([(14, 30), (16, 18), (30, 16), (32, 28)]), M["ink"], I * 1.4)                              # the pack's loop
    G.stroke(d, Ps(rrect(8, 26, 40, 72, 7)), M["red"], O, cyclic=True)                                        # the pack
    G.stroke(d, Ps(rrect(8, 26, 40, 44, 6)[:13] + [(40, 44), (8, 44)]), M["red_sh"], 0.0, cyclic=True)        # its flap
    G.stroke(d, Ps([(9, 44), (39, 44)]), M["ink"], I)
    G.stroke(d, Ps(rrect(20, 40, 28, 49, 1.5, 2)), M["mustard"], I, cyclic=True)                              # the buckle
    G.stroke(d, Ps(rrect(12, 54, 36, 66, 3)), M["red_sh"], 0.0, cyclic=True)                                  # a pocket
    G.stroke(d, Ps(rrect(12, 54, 36, 66, 3)), M["ink"], I, cyclic=True)
    G.stroke(d, Ps(arrow_pts(44, 38, 64, 56)), M["offwhite"], I, cyclic=True)                                 # ->
    for y in (60, 54, 48):                                                                                     # the coin stack
        side = [(99, y - 4)] + [(84 + 15 * math.cos(a), y + 5 * math.sin(a)) for a in np.linspace(0, math.pi, 13)] + [(69, y - 4)]
        G.stroke(d, Ps(side), M["mustard_sh"], I, cyclic=True)
        G.stroke(d, Ps(circ(84, y - 4, 15, 32, 5)), M["mustard"], I, cyclic=True)
    G.stroke(d, Ps([(84 + 7 * math.cos(-math.pi / 2 + TAU * k / 10) * (1 if k % 2 == 0 else 0.42),
                     44 + 2.4 * math.sin(-math.pi / 2 + TAU * k / 10) * (1 if k % 2 == 0 else 0.42)) for k in range(10)]), M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, Ps(circ(100, 22, 9, 24)), M["mustard"], I, cyclic=True)                                       # one coin flying
    G.stroke(d, Ps([(100 + 4.5 * math.cos(-math.pi / 2 + TAU * k / 10) * (1 if k % 2 == 0 else 0.45),
                     22 + 4.5 * math.sin(-math.pi / 2 + TAU * k / 10) * (1 if k % 2 == 0 else 0.45)) for k in range(10)]), M["mustard_sh"], 0.0, cyclic=True)
    for a in (2.4, 2.8):
        G.stroke(d, Ps([(100 + 12 * math.cos(a), 22 + 12 * math.sin(a)), (100 + 18 * math.cos(a), 22 + 18 * math.sin(a))]), M["ink"], I)


def pic_skill_tree(d, M, seed):
    G.stroke(d, Ps(rect(0, 0, 116, 116)), M["offwhite_sh"], 0.0, cyclic=True)
    cx, cy = 50, 50
    for r in (24, 40):
        G.stroke(d, Ps(circ(cx, cy, r, 64)), M["ln_brown"], I, cyclic=True)
    cols = ("red", "brown", "mustard", "teal", "green", "sky")
    inner = [(cx + 24 * math.cos(-math.pi / 2 + TAU * k / 6), cy + 24 * math.sin(-math.pi / 2 + TAU * k / 6)) for k in range(6)]
    outer_k = {0: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}                                                                 # clear of the key cap
    for k, (x, y) in enumerate(inner):
        G.stroke(d, Ps([(cx, cy), (x, y)]), M["ink"], I * 1.2)
        if k in outer_k:
            ang = -math.pi / 2 + TAU * k / 6
            ox, oy = cx + 40 * math.cos(ang), cy + 40 * math.sin(ang)
            G.stroke(d, Ps([(x, y), (ox, oy)]), M["ink"], I * 1.2)
            G.stroke(d, Ps(circ(ox, oy, 5.5, 20)), M[cols[k]], I, cyclic=True)
    for k, (x, y) in enumerate(inner):
        G.stroke(d, Ps(circ(x, y, 6.5, 24)), M[cols[k]], I, cyclic=True)
    G.stroke(d, Ps(circ(cx, cy, 11, 32)), M["mustard"], O, cyclic=True)                                       # the hub
    G.stroke(d, Ps([(cx + 6 * math.cos(-math.pi / 2 + TAU * k / 10) * (1 if k % 2 == 0 else 0.42),
                     cy + 6 * math.sin(-math.pi / 2 + TAU * k / 10) * (1 if k % 2 == 0 else 0.42)) for k in range(10)]), M["red"], 0.0, cyclic=True)


def pic_climb_up(d, M, seed):
    G.stroke(d, Ps(rect(0, 0, 116, 20)), M["sky_f"], 0.0, cyclic=True)
    band(d, M, "brown_f", 0, 116, 18, 116, seed)
    band(d, M, "mustard_sh", 0, 116, 60, 68, seed + 1, 1.0)
    band(d, M, "brown_f", 0, 116, 67, 116, seed + 2, 1.0)
    band(d, M, "red_sh", 0, 116, 98, 106, seed + 3, 1.0)
    band(d, M, "brown_f", 0, 116, 105, 116, seed + 4, 1.0)
    G.stroke(d, Ps(wavy_band(0, 116, 17, 0.6, seed + 5) + [(116, 22), (0, 22)]), M["green"], I, cyclic=True)
    G.stroke(d, Ps([(14, 21), (46, 21), (46, 116), (14, 116)]), M["brown_dp"], 0.0, cyclic=True)              # the shaft
    for x in (14, 46):
        G.stroke(d, Ps([(x, 21), (x, 116)]), M["ink"], I)
    for v in range(26, 116, 12):                                                                               # the rungs
        G.stroke(d, G.hose_outline(Ps([(21, v), (39, v)]), 2.2), M["mustard_sh"], I, cyclic=True)
    for x in (21, 39):                                                                                         # the rails
        G.stroke(d, G.hose_outline(Ps([(x, 6), (x, 116)]), 3.0), M["mustard"], I, cyclic=True)
    G.stroke(d, Ps(arrow_pts(52, 26, 70, 58, up=True)), M["offwhite"], I, cyclic=True)                       # up
    G.stroke(d, Ps([(88, 21), (100, 21), (100, 70), (88, 70)]), M["brown_dp"], 0.0, cyclic=True)              # the grapple's hole
    G.stroke(d, Ps([(88, 21), (88, 70), (100, 70), (100, 21)]), M["ink"], I)
    G.stroke(d, Ps([(94, 16), (94, 62)]), M["ln_offwhite"], I * 1.5)                                          # the line down it
    G.stroke(d, G.hose_outline(Ps([(103, 4), (103, 16)]), 2.6), M["mustard"], I, cyclic=True)                # the hook on the lip:
    G.stroke(d, G.hose_outline(Ps([(103 + 7 * math.sin(a), 13 + 5 * math.cos(a)) for a in np.linspace(-1.9, 1.9, 13)]), 2.4),
             M["mustard"], I, cyclic=True)                                                                     # its curved flukes bite
    G.stroke(d, Ps(circ(103, 3.5, 2.6, 12)), M["mustard"], I, cyclic=True)                                    # the turf; its eye
    G.stroke(d, Ps([(101, 4), (94, 9), (94, 16)]), M["ln_offwhite"], I * 1.5)                                 # (the line from the eye)
    G.stroke(d, Ps(circ(94, 64, 5, 16)), M["teal"], I, cyclic=True)                                           # the reel
    for k, (u, r) in enumerate(((60, 5.0), (68, 4.0))):                                                        # the jetpack's puffs (ink + paper)
        G.stroke(d, Ps(circ(u, 104 - 2 * k, r, 16)), M["offwhite"], I, cyclic=True)
    G.stroke(d, Ps(rrect(56, 68, 72, 94, 5)), M["teal"], I, cyclic=True)                                      # the jetpack tank
    G.stroke(d, Ps(rrect(58, 64, 70, 70, 2, 2)), M["mustard"], I, cyclic=True)
    G.stroke(d, Ps([(59, 94), (69, 94), (67, 99), (61, 99)]), M["brown"], I, cyclic=True)


def pic_pack_full(d, M, seed):
    G.stroke(d, Ps(rect(0, 0, 116, 116)), M["brown_f"], 0.0, cyclic=True)
    band(d, M, "mustard_sh", 0, 116, 20, 28, seed + 1, 1.0)
    band(d, M, "brown_f", 0, 116, 27, 116, seed + 2, 1.0)
    band(d, M, "red_sh", 0, 116, 92, 100, seed + 3, 1.0)
    band(d, M, "brown_f", 0, 116, 99, 116, seed + 4, 1.0)
    G.stroke(d, Ps(circ(58, 46, 46, 40, 34)), M["brown_dp"], 0.0, cyclic=True)                               # the dug pocket
    G.stroke(d, Ps(circ(58, 46, 46, 40, 34)), M["ink"], I, cyclic=True)
    G.stroke(d, Ps([(40, 28), (36, 12), (46, 4), (52, 16)]), M["teal"], I, cyclic=True)                      # ore over the top
    G.stroke(d, Ps(G.lumpy_ellipse(64, 14, 9, 7, n=14, seed=seed)), M["sky_sh"], 0.0, cyclic=True)
    G.stroke(d, Ps(G.lumpy_ellipse(64, 14, 9, 7, n=14, seed=seed)), M["ink"], I, cyclic=True)
    G.stroke(d, Ps(G.lumpy_ellipse(78, 20, 6, 5, n=12, seed=seed + 1)), M["mustard"], I, cyclic=True)
    pack =[(58 + 30 * math.cos(a) * (1 + 0.05 * math.sin(3 * a)), 50 + 32 * math.sin(a) * (1 + 0.04 * math.cos(5 * a))) for a in np.linspace(0, TAU, 40, endpoint=False)]
    G.stroke(d, Ps(pack), M["red"], O, cyclic=True)                                                           # the pack, bulging
    G.stroke(d, Ps([(30, 36), (44, 30), (58, 28), (72, 30), (86, 36), (86, 44), (30, 44)]), M["red_sh"], 0.0, cyclic=True)
    G.stroke(d, Ps([(30, 44), (86, 44)]), M["ink"], I)
    G.stroke(d, Ps(rrect(54, 40, 62, 50, 1.5, 2)), M["mustard"], I, cyclic=True)                              # the buckle, straining
    for u in (40, 76):                                                                                         # the seams, stretched
        G.stroke(d, Ps([(u, 56), (u + (2 if u > 58 else -2), 70)]), M["ink"], I)


PICS = {"dig_down": pic_dig_down, "surface_line": pic_surface_line, "sell": pic_sell, "skill_tree": pic_skill_tree,
        "climb_up": pic_climb_up, "pack_full": pic_pack_full}


def _stamp_small():
    """B-211's PACK FULL stamp at half size, opaque (its alpha 235 would tint what it covers off the palette)."""
    import build_hud_d1_v3 as HD
    s = HD.pack_full().astype(np.float32) / 255.0
    h, w = s.shape[0] // 2, s.shape[1] // 2
    a = s[:2 * h, :2 * w, 3].reshape(h, 2, w, 2).mean(axis=(1, 3))
    rgb = (s[:2 * h, :2 * w, :3] * s[:2 * h, :2 * w, 3:4]).reshape(h, 2, w, 2, 3).sum(axis=(1, 3)) / np.maximum(a * 4, 1e-6)[..., None]
    a = np.clip(a / 0.85, 0, 1)
    return np.dstack([rgb, a])


def _over(dst, fr, x, y):
    """Composite a float RGBA sprite over a uint8 RGBA image (both straight alpha)."""
    h, w = fr.shape[:2]
    sub = dst[y:y + h, x:x + w].astype(np.float32) / 255.0
    a = fr[..., 3:4]
    out_a = a + sub[..., 3:4] * (1 - a)
    out_rgb = (fr[..., :3] * a + sub[..., :3] * sub[..., 3:4] * (1 - a)) / np.maximum(out_a, 1e-6)
    dst[y:y + h, x:x + w] = np.rint(np.dstack([out_rgb, out_a]) * 255).astype(np.uint8)


def card(name, seed=700):
    seed = seed + 10 * CARDS.index(name)
    c = U.Canvas(CW, CH)
    d, M = c.dm, extra(c)
    outer = paper(d, M, seed)
    win = window(d, M, seed)
    G.stroke(d, win, M["offwhite_f"], 0.0, cyclic=True)
    PICS[name](d, M, seed)
    G.stroke(d, win, M["ink"], O * 0.8, cyclic=True)
    if KEY[name] == "mouse_left":
        mouse(d, M, seed)
    elif KEY[name]:
        keycap(d, M, seed)
    G.stroke(d, outer, M["ink"], O, cyclic=True)
    img = done(c, seed)[0]
    if name == "pack_full":                                                                                   # the stamp pressed across it
        st = _stamp_small()
        _over(img, st, 14, 118)
    return img


def arrow(seed=790):
    c = U.Canvas(AW, AH)
    d, M = c.dm, extra(c)
    body = [(8, 17), (40, 16.5), (39, 6), (ATIP[0], ATIP[1]), (39, 42), (40, 31.5), (8, 31)]
    G.stroke(d, body, M["offwhite_f"], 0.0, cyclic=True)
    G.stroke(d, [(8, 17), (15, 17), (15, 31), (8, 31)], M["mustard_f"], 0.0, cyclic=True)                    # the folded tail
    G.stroke(d, [(15, 17), (15, 31)], M["ink"], I)
    G.stroke(d, [(19, 21), (43, 21), (43, 14), (58, 24), (43, 34), (43, 27), (19, 27)], M["ln_mustard"], I, cyclic=True)   # the rule
    G.stroke(d, body, M["ink"], O, cyclic=True)
    return done(c, seed)[0]


# ---------------------------------------------------------------- checks + export
def _bl(rect_tl):
    """[x0, y0, x1, y1] from the top-left -> [x, y, w, h] from the bottom-left (Unity's sprite rects)."""
    x0, y0, x1, y1 = rect_tl
    return [x0, CH - y1, x1 - x0, y1 - y0]


def checks(name, img, w, h):
    p = []
    m = v3.EDGE_MARGIN
    hit = v3.palette_hits(img, "earth")[0]
    if img.shape[:2] != (h, w):
        p.append(f"{name}: {img.shape[1]}x{img.shape[0]} is not {w}x{h}")
    if w % 4 or h % 4:
        p.append(f"{name}: {w}x{h} not a multiple of 4")
    if hit < 0.995:
        p.append(f"{name}: palette {hit * 100:.1f}%")
    if img[:m, :, 3].any() or img[-m:, :, 3].any() or img[:, :m, 3].any() or img[:, -m:, 3].any():
        p.append(f"{name}: touches the {m} px edge")
    return p


def kit():
    out = []
    for n in CARDS:
        img = card(n)
        meta = {"key": f"ui/hints/{n}", "style": "v3", "ppu": U.PPU, "pivot": [0.5, 0.5], "width": CW, "height": CH,
                "slice": SLICE, "slice_order": "[left, top, right, bottom] px in from each edge (contract 11.6); Unity's Sprite.border is (left, bottom, right, top)",
                "rect_origin": "bottom_left", "title_rect": _bl(TITLE), "body_rect": _bl(BODY),
                "lettering": "runtime", "lettering_note": "the title in Limelight (ink), the body in Patrick Hand (ink); both rects grow with the card's width",
                "binding": KEY[n], "grain": U.GRAIN_KEY, "grain_note": "flat paper for the 9-slice; tile ui/panels/grain over it at 1 texel = 1 px, masked by alpha",
                "note": f"B-213: the first-hour hint card '{SAMPLE[n][0]}' (pictogram baked)"}
        if KEY[n] and KEY[n] != "mouse_left":
            meta["keycap_rect"] = _bl((CAP[0] + 4, CAP[1] + 2, CAP[2] - 4, CAP[3] - 9))
            meta["keycap_note"] = "a blank key cap: UNITY letters the current binding on its top face (Patrick Hand, ink)"
        out.append((meta["key"], img, meta, CW, CH))
    a = arrow()
    out.append(("ui/hints/arrow", a, {"key": "ui/hints/arrow", "style": "v3", "ppu": U.PPU, "pivot": [ATIP[0] / AW, 1 - ATIP[1] / AH],
                                      "width": AW, "height": AH, "facing": "right",
                                      "note": "B-213: the pointing paper arrow; the pivot is its tip: turn it about the tip so +x points at the HUD element"}, AW, AH))
    return out


def export(art):
    from meridian import pngio
    built, problems = [], []
    for key, img, meta, w, h in kit():
        problems += checks(key.split("/")[-1], img, w, h)
        l_, t_, r_, b_ = SLICE
        if "slice" in meta and (l_ + r_ >= w or t_ + b_ >= h):
            problems.append(f"{key}: slice {SLICE} leaves no stretchable centre")
        built.append((key, img, meta))
    if problems:
        raise ValueError("B-213 hint checks: " + "; ".join(problems))
    out = []
    for key, img, meta in built:
        base = os.path.join(art, *key.split("/"))
        os.makedirs(os.path.dirname(base), exist_ok=True)
        n = pngio.write_png(base + "_color.png", img)
        with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((key, img.shape[1], img.shape[0], n))
    return out


def keys():
    return [f"ui/hints/{n}" for n in CARDS] + ["ui/hints/arrow"]


# ---------------------------------------------------------------- the review sheet
def lettered(img, name):
    """The card with sample lettering, as UNITY will letter it (float RGB on the sheet's paper)."""
    title, body = SAMPLE[name]
    f = img.astype(np.float32) / 255.0
    paper_rgb = np.array(review_paper(), np.float32)
    rgb = f[..., :3] * f[..., 3:4] + paper_rgb * (1 - f[..., 3:4])
    size = 22
    while size > 12 and U.text_mask(U.LIMELIGHT, title, size).shape[1] > TITLE[2] - TITLE[0]:
        size -= 1
    m = U.text_mask(U.LIMELIGHT, title, size, wobble=0.3, seed=3)
    ST.letter(rgb, title, TITLE[0] + (TITLE[2] - TITLE[0] - m.shape[1]) // 2, TITLE[1] + 2, size, font=U.LIMELIGHT, seed=3)
    words, lines, cur = body.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if U.text_mask(U.PATRICK, t, 19).shape[1] > BODY[2] - BODY[0] and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    lines.append(cur)
    for i, ln in enumerate(lines):
        ST.letter(rgb, ln, BODY[0], BODY[1] + 4 + 24 * i, 19, seed=5 + i)
    k = KEY[name]
    if k and k != "mouse_left":
        glyph = {"climb": "W"}.get(k, k)
        x0, y0, x1, y1 = CAP[0] + 4, CAP[1] + 2, CAP[2] - 4, CAP[3] - 9
        gm = U.text_mask(U.PATRICK, glyph, 26)
        ST.letter(rgb, glyph, x0 + (x1 - x0 - gm.shape[1]) // 2, y0 + (y1 - y0 - gm.shape[0]) // 2, 26, seed=9)
    return rgb


def review_paper():
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    return review.PAPER


def preview(out, footnote=None):
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    K = kit()
    Wd = 1400
    bg = np.array(review.PAPER, np.float32)
    head = np.tile(bg, (28, Wd, 1))
    review._label(head, "B-213 the first-hour hint cards: six at 1x with sample lettering (UNITY letters them), the bare cards, a 9-slice stretch, the arrow", 6, 8)
    rows = [head]
    cards = [(k.split("/")[-1], img) for k, img, _m, _w, _h in K if k != "ui/hints/arrow"]
    hud = np.empty((2 * (CH + 40) + 20, Wd, 3), np.float32)
    hud[:] = np.array(v3.hex_rgb(v3.PALETTES["earth"]["sky"]), np.float32) / 255.0                        # over the topside sky
    for i, (n, img) in enumerate(cards):
        r, c = divmod(i, 3)
        x, y = 20 + c * (CW + 40), 26 + r * (CH + 40)
        rgb = lettered(img, n)
        a = img[..., 3:4].astype(np.float32) / 255.0
        hud[y:y + CH, x:x + CW] = rgb * a + hud[y:y + CH, x:x + CW] * (1 - a)
        review._label(hud, f"ui/hints/{n}", x, y - 14, scale=1)
    ax, ay = 20 + 3 * (CW + 40), 40                                                                         # the arrow, aimed
    arr = K[-1][1]
    for k, sc in enumerate((1, 2)):
        a2 = np.repeat(np.repeat(arr, sc, 0), sc, 1)
        ST.ov(hud, a2, ax + k * 90, ay + 20)
    review._label(hud, "ui/hints/arrow (1x, 2x)", ax, ay, scale=1)
    wx0, wy0, wx1, wy1 = WIN                                                                                # B-229: the shovel picture at 2x
    ST.ov(hud, np.repeat(np.repeat(cards[0][1][wy0:wy1, wx0:wx1], 2, 0), 2, 1), ax, 256)
    review._label(hud, "dig_down's picture at 2x (B-229: the shovel in the surveyor's hand)", ax, 242, scale=1)
    rows.append(hud)
    bare = np.tile(bg, (CH + 60, Wd, 1))
    x = 20
    for n, img in cards[:3]:
        ST.ov(bare, img, x, 30)
        x += CW + 30
    st = U.nine_slice(cards[2][1], [SLICE[0], SLICE[1], SLICE[2], SLICE[3]], 380, 236)
    review._label(bare, "bare (what UNITY gets) - and 'sell' 9-sliced to 380x236", 20, 8, scale=1)
    rows.append(bare)
    st_row = np.tile(bg, (236 + 40, Wd, 1))
    ST.ov(st_row, st, 20, 20)
    st2 = U.nine_slice(cards[5][1], [SLICE[0], SLICE[1], SLICE[2], SLICE[3]], 460, 200)
    ST.ov(st_row, st2, 440, 20)
    review._label(st_row, "9-slice: sell at 380x236, pack_full at 460x200", 440, 230, scale=1)
    rows.append(st_row)
    lines = []
    for key, img, _m, w, h in K:
        hit = v3.palette_hits(img, "earth")[0] * 100
        bad = checks(key, img, w, h)
        lines.append(f"{key}: {w}x{h}, palette {hit:.1f}%" + ("; " + "; ".join(b for b in bad if "palette" not in b) if any("palette" not in b for b in bad) else ""))
    foot = np.tile(bg, (24 + 16 * ((len(lines) + 2) // 3), Wd, 1))
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6 + (i % 3) * 460, 6 + 16 * (i // 3), scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_hints_v3.py <review png>
    preview(sys.argv[1])
