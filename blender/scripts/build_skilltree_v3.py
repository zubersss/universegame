"""B-204 (D-174; Bible 5.2 §8.1): the Skill Tree's art in UiKit's paper style (B-146 / B-151), Earth palette, no faces.

  ui/skilltree/panel             256x256  slice 72 72 72 72: aged chart paper (a darker foxed margin, a double brown rule,
                                          compass-arc corners)
  ui/skilltree/chart             960x960  the round chart: an inked double border with degree ticks and the six branches'
                                          colour bands, four dotted ring dividers, six dashed sector spokes, a ring round the hub
  ui/skilltree/hub               112x112  the centre (the start): a compass rose on a brass ring
  ui/skilltree/emblem_<branch>   96x96    the branch emblems on brass plaques: dig (the Beam), haul (a pack), ascent (a jetpack
                                          and a rope), survey (a lens), endurance (a helmet), voyage (the Pilgrim)
  ui/skilltree/node_<state>      64x64    node frames: locked (greyed ink, aged paper), available (inked, a warm mustard rim),
                                          bought (gold-filled)
  ui/skilltree/node_cap_<state>  72x72    ring 5's frames (a scalloped rim), the same three states
  ui/skilltree/select            96x96    a red pencil loop round the selected node
  ui/skilltree/link_<state>      64x16    tiling link lines (tile_x, the line on row 8): locked (grey dashes), open (ink),
                                          bought (ink with a gold thread)
  ui/skilltree/cost_tag          160x56   slice 48 16 20 16 (stretch it sideways): a paper tag, a brass eyelet and its string;
                                          lettered at runtime

The layout (LAYOUT, positions from the chart's centre) follows docs/D1_TABLES.md §5: the branches clockwise from the top
(Dig, Haul, Ascent, Survey, Endurance, Voyage), rings at RING_R, a sideways-linked node on the side of its neighbour.

  python -I build_skilltree_v3.py <preview dir>      the 1080p mock-up (lock-free numpy): review_b204_skilltree_mockup.png
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ui_v3 as U  # noqa: E402
from meridian import v3  # noqa: E402

G, GR, O, I = U.G, U.GR, U.O, U.I
TAU = 2 * math.pi
PAL = v3.PALETTES["earth"]


def SH(k):
    return v3.shadow_of(PAL[k], "earth")


def DP(k):
    return v3.deep_of(PAL[k], "earth")


NODE, CAP, HUB, EMB, SEL, CHART = 64, 72, 112, 96, 96, 960
RING_R = {1: 140, 2: 210, 3: 285, 4: 355, 5: 420}
DIVIDERS = (175, 247, 320, 387)
EMB_R = 408
BRANCHES = ("dig", "haul", "ascent", "survey", "endurance", "voyage")
BCOL = {"dig": "red", "haul": "brown", "ascent": "mustard", "survey": "teal", "endurance": "green", "voyage": "sky"}


# ---------------------------------------------------------------- the tree (docs/D1_TABLES.md §5)
TREE = {   # per ring, slot order counter-clockwise -> clockwise (a sideways-linked node on its neighbour's side)
    "dig": [["dig_power_1", "dig_brush_1"], ["dig_power_2", "dig_rhythm_1"], ["dig_power_3", "dig_heatsink", "dig_brush_2"],
            ["dig_power_4", "dig_rhythm_2"], ["dig_power_5", "dig_core_bit"]],
    "haul": [["haul_dirt_1", "haul_pack_1"], ["haul_light_1", "haul_pack_2"], ["haul_magnet_1", "haul_sorter", "haul_pack_3"],
             ["haul_light_2", "haul_pack_4"], ["haul_compact", "haul_pack_5"]],
    "ascent": [["asc_grapple_1", "asc_ladder_1"], ["asc_jet_1", "asc_climb_1"], ["asc_jet_2", "asc_grapple_2", "asc_ladder_2"],
               ["asc_jet_3", "asc_grapple_3"], ["asc_recall", "asc_winch"]],
    "survey": [["sur_scan_1", "sur_depth_1"], ["sur_scan_2", "sur_preview_1"], ["sur_scan_3", "sur_rare", "sur_preview_2"],
               ["sur_scan_4", "sur_vault"], ["sur_deep_eye", "sur_cartographer"]],
    "endurance": [["end_air_1", "end_fall_1"], ["end_air_2", "end_heat_1"], ["end_air_3", "end_heat_2", "end_fall_2"],
                  ["end_air_4", "end_deep_1"], ["end_suit_mk3", "end_deep_2"]],
    "voyage": [["voy_hold_1", "voy_price_1"], ["voy_thrust_2", "voy_price_2"], ["voy_hold_2", "voy_skip_1", "voy_price_3"],
               ["voy_thrust_3", "voy_trader"], ["voy_skip_2", "voy_dray"]],
}   # D1_TABLES §5 as revised 17:1x (5030aafd: the crossing-free links, 0 crossings)
LINKS = {   # node: the nodes it needs one of (outward); "centre" for ring 1
    "dig_power_2": ["dig_power_1"], "dig_rhythm_1": ["dig_power_1", "dig_brush_1"], "dig_power_3": ["dig_power_2"],
    "dig_heatsink": ["dig_rhythm_1"], "dig_brush_2": ["dig_rhythm_1"], "dig_power_4": ["dig_power_3"],
    "dig_rhythm_2": ["dig_heatsink", "dig_brush_2"], "dig_power_5": ["dig_power_4"], "dig_core_bit": ["dig_rhythm_2"],
    "haul_pack_2": ["haul_pack_1"], "haul_light_1": ["haul_pack_1", "haul_dirt_1"], "haul_pack_3": ["haul_pack_2"],
    "haul_magnet_1": ["haul_light_1"], "haul_sorter": ["haul_light_1"], "haul_pack_4": ["haul_pack_3"],
    "haul_light_2": ["haul_magnet_1", "haul_sorter"], "haul_pack_5": ["haul_pack_4"], "haul_compact": ["haul_light_2"],
    "asc_jet_1": ["asc_grapple_1", "asc_ladder_1"], "asc_climb_1": ["asc_ladder_1"], "asc_grapple_2": ["asc_jet_1"],
    "asc_jet_2": ["asc_jet_1"], "asc_ladder_2": ["asc_climb_1"], "asc_jet_3": ["asc_jet_2"],
    "asc_grapple_3": ["asc_grapple_2", "asc_ladder_2"], "asc_winch": ["asc_grapple_3"], "asc_recall": ["asc_jet_3"],
    "sur_scan_2": ["sur_scan_1"], "sur_preview_1": ["sur_depth_1"], "sur_scan_3": ["sur_scan_2"],
    "sur_rare": ["sur_scan_2", "sur_preview_1"], "sur_preview_2": ["sur_preview_1"], "sur_scan_4": ["sur_scan_3"],
    "sur_vault": ["sur_rare", "sur_preview_2"], "sur_deep_eye": ["sur_scan_4"], "sur_cartographer": ["sur_vault"],
    "end_air_2": ["end_air_1"], "end_heat_1": ["end_air_1", "end_fall_1"], "end_air_3": ["end_air_2"],
    "end_heat_2": ["end_heat_1"], "end_fall_2": ["end_fall_1"], "end_deep_1": ["end_heat_2", "end_fall_2"],
    "end_air_4": ["end_air_3"], "end_deep_2": ["end_deep_1"], "end_suit_mk3": ["end_air_4"],
    "voy_thrust_2": ["voy_price_1", "voy_hold_1"], "voy_price_2": ["voy_price_1"], "voy_hold_2": ["voy_thrust_2"],
    "voy_skip_1": ["voy_thrust_2"], "voy_price_3": ["voy_price_2"], "voy_thrust_3": ["voy_skip_1", "voy_hold_2"],
    "voy_trader": ["voy_price_3"], "voy_skip_2": ["voy_thrust_3"], "voy_dray": ["voy_trader"],
}
SIDEWAYS = [("dig_brush_2", "haul_magnet_1"), ("dig_power_5", "voy_dray"), ("haul_pack_5", "asc_recall"),
            ("asc_ladder_2", "sur_scan_2"), ("sur_cartographer", "end_suit_mk3"), ("end_fall_2", "voy_hold_2")]
OFFSET = {"end_air_2": -18, "end_heat_1": 4}     # degrees from the branch axis where the default slot would sit on a link


def axis_deg(b):
    return -90 + 60 * BRANCHES.index(b)           # screen degrees (y down): Dig at the top, then clockwise


def layout():
    """{id: (branch, ring, x, y)} in px from the chart's centre (y down)."""
    out = {}
    for b, rings in TREE.items():
        for r, ids in enumerate(rings, 1):
            slots = [-15, 15] if len(ids) == 2 else [-20, 0, 20]
            for sid, off in zip(ids, slots):
                a = math.radians(axis_deg(b) + OFFSET.get(sid, off))
                out[sid] = (b, r, RING_R[r] * math.cos(a), RING_R[r] * math.sin(a))
    return out


LAYOUT = layout()


def all_links():
    """[(a, b, sideways)] with "centre" at (0, 0)."""
    ls = []
    for b, rings in TREE.items():
        for sid in rings[0]:
            ls.append(("centre", sid, False))
    for n, req in LINKS.items():
        ls += [(q, n, False) for q in req]
    ls += [(a, b, True) for a, b in SIDEWAYS]
    return ls


def pos(n):
    return (0.0, 0.0) if n == "centre" else LAYOUT[n][2:]


def crossings():
    """Link pairs that cross (no shared node): the layout's honest count for LEAD."""
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])
    L, out = all_links(), []
    for i in range(len(L)):
        for j in range(i + 1, len(L)):
            a, b, c, d = L[i][0], L[i][1], L[j][0], L[j][1]
            if len({a, b, c, d}) < 4:
                continue
            p, q, r, s = pos(a), pos(b), pos(c), pos(d)
            if ccw(p, q, r) * ccw(p, q, s) < 0 and ccw(r, s, p) * ccw(r, s, q) < 0:
                out.append((f"{a}-{b}", f"{c}-{d}"))
    return out


# ---------------------------------------------------------------- drawing helpers (px, y down)
def extra(c):
    """Line materials (an open stroke draws in its material's ink colour) and the locked state's greyed fill."""
    M = c.M
    for name, hx in (("grey", SH("sky")), ("red", PAL["red"]), ("brown", PAL["brown"]), ("brown_sh", SH("brown")),
                     ("mustard", PAL["mustard"]), ("mustard_sh", SH("mustard")), ("offwhite", PAL["offwhite"])):
        M["ln_" + name] = G.mat(c.gp, f"st_ln_{name}", fill=None, ink_hex=hx)
    M["lock_paper"] = G.mat(c.gp, "st_lock_paper", fill=SH("offwhite"), ink_hex=SH("sky"))
    M["ink_f"] = G.mat(c.gp, "st_ink_f", fill=v3.INK, ink=False)
    return M


def circ(cx, cy, r, n=64, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(TAU * i / n), cy + ry * math.sin(TAU * i / n)) for i in range(n)]


def arc(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def scallop(cx, cy, r, k=12, depth=0.08, n=144):
    """Round bumps with sharp notches between them."""
    return [(cx + r * (1 - depth * (1 - abs(math.cos(k * TAU * i / n / 2)))) * math.cos(TAU * i / n),
             cy + r * (1 - depth * (1 - abs(math.cos(k * TAU * i / n / 2)))) * math.sin(TAU * i / n)) for i in range(n)]


def sector(cx, cy, r0, r1, a0, a1, n=32):
    return arc(cx, cy, r1, a0, a1, n) + arc(cx, cy, r0, a1, a0, n)


def rot(cx, cy, s, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    return lambda pts: [(cx + s * (u * ca - v * sa), cy + s * (u * sa + v * ca)) for u, v in pts]


def done(c, seed=3, grain=0.0):
    img, w = c.render(seed)
    return (U.paper_grain(img, seed, grain) if grain else img), w


# ---------------------------------------------------------------- the branch glyphs (unit: s = 1 fits radius ~28 px)
DIG_CABLE = True     # LEAD to rule (18:2x): the Beam on a cable, no pistol grip (as build_icons_nodes_v3.BEAM_CABLE); the
                     # exported ui/skilltree/emblem_dig keeps the grip until re-exported
def g_dig(d, M, cx, cy, s):
    """The Rig's Beam: the emitter (upper left) firing a teal beam down-right into chipped ground."""
    R = rot(cx, cy, s, 0.55)
    G.stroke(d, R([(4, -3.5), (26, -9), (26, 9), (4, 3.5)]), M["teal_f"], 0.0, cyclic=True)              # the beam
    G.stroke(d, R([(4, -3.5), (26, -9), (26, 9), (4, 3.5)]), M["ink"], I, cyclic=True)
    G.stroke(d, G.hose_outline(R([(6, 0), (24, 0)]), 2.6 * s), M["offwhite_f"], 0.0, cyclic=True)        # its core
    for a in (-0.7, 0.0, 0.7):                                                                           # sparks
        G.stroke(d, R([(28 + 2 * math.cos(a), 6 * math.sin(a)), (33 + 3 * math.cos(a), 11 * math.sin(a))]), M["ln_mustard"], I * 1.3 * s)
    if DIG_CABLE:                                                         # 18:2x flag (D-087): no pistol grip; a cable to the rig
        P = lambda pts: [(cx + s * u, cy + s * v) for u, v in pts]  # noqa: E731
        G.stroke(d, G.hose_outline(P([(-24, -14), (-28, -4), (-26, 9), (-18, 18), (-6, 23)]), 4.5 * s), M["brown_sh"], I, cyclic=True)
    else:
        G.stroke(d, G.hose_outline(R([(-17, 5), (-21, 19)]), 7 * s), M["brown"], I, cyclic=True)          # the grip
    G.stroke(d, R([(-28, -7), (-2, -7), (-2, 7), (-28, 7)]), M["teal"], O * s, cyclic=True)               # the body
    G.stroke(d, R([(-22, -7), (-22, 7)]), M["ink"], I)
    G.stroke(d, R([(-2, -6), (6, -3.5), (6, 3.5), (-2, 6)]), M["mustard"], I, cyclic=True)                # the nozzle


def g_haul(d, M, cx, cy, s):
    """A pack, front on: a brown body, a mustard flap with one buckle, a front pocket, a carry loop."""
    P = lambda pts: [(cx + s * u, cy + s * v) for u, v in pts]  # noqa: E731
    G.stroke(d, G.hose_outline(P(arc(0, -15, 7, math.pi, TAU, 10)), 3.5 * s), M["brown"], I, cyclic=True)
    G.stroke(d, P([(-17, -15), (17, -15), (18, 20), (14, 24), (-14, 24), (-18, 20)]), M["brown"], O * s, cyclic=True)
    G.stroke(d, P([(-11, 9), (11, 9), (11, 20), (-11, 20)]), M["brown_sh"], 0.0, cyclic=True)              # the pocket
    G.stroke(d, P([(-11, 9), (11, 9), (11, 20), (-11, 20)]), M["ink"], I, cyclic=True)
    G.stroke(d, P([(-18, -16), (18, -16), (18, -2)] + arc(0, -2, 18, 0, math.pi, 12)[1:] + [(-18, -2)]), M["mustard"], O * s, cyclic=True)
    G.stroke(d, P([(-3.5, 10), (3.5, 10), (3.5, 15), (-3.5, 15)]), M["offwhite"], I, cyclic=True)        # the buckle
    G.stroke(d, P([(0, 16), (0, 10)]), M["ink"], I)


def g_ascent(d, M, cx, cy, s):
    """A jetpack (two red tanks, a mustard harness band, two flames), a coil of rope hung at its right with a small hook
    (rev 16:5x: a coil round the whole pack read as a scribble)."""
    P = lambda pts: [(cx + s * u, cy + s * v) for u, v in pts]  # noqa: E731
    for k, x0 in enumerate((19, 15.5, 12)):                                                              # three laps, back to front
        lap = [(x0 + 6.5 * math.cos(a), 1 + 13 * math.sin(a)) for a in np.linspace(math.radians(-70), math.radians(255), 26)]
        G.stroke(d, G.hose_outline(P(lap), 3.4 * s), M["mustard_sh"], I, cyclic=True)
    G.stroke(d, G.hose_outline(P([(12, 14), (13, 20), (17, 24)]), 3.4 * s), M["mustard_sh"], I, cyclic=True)   # its free end
    G.stroke(d, G.hose_outline(P([(17, 24), (21, 25), (23, 22), (22, 19)]), 2.8 * s), M["sky"], I, cyclic=True)    # the hook
    for x in (-13, 1):
        G.stroke(d, P([(x - 4, 14), (x + 4, 14), (x, 27)]), M["mustard"], I, cyclic=True)                 # flames
        G.stroke(d, P([(x - 2, 14), (x + 2, 14), (x, 21)]), M["offwhite_f"], 0.0, cyclic=True)
        G.stroke(d, P([(x - 4, 9), (x + 4, 9), (x + 3, 14), (x - 3, 14)]), M["mustard_sh"], I, cyclic=True)   # nozzles
        G.stroke(d, G.hose_outline(P([(x, -15), (x, 6)]), 11 * s), M["red"], O * s, cyclic=True)           # the tanks
    G.stroke(d, P([(-20, -6), (8, -6), (8, -1), (-20, -1)]), M["mustard"], I, cyclic=True)               # the harness band


def g_survey(d, M, cx, cy, s):
    """A brass lens on a brown handle: one glint."""
    P = lambda pts: [(cx + s * u, cy + s * v) for u, v in pts]  # noqa: E731
    G.stroke(d, G.hose_outline(P([(7, 7), (21, 21)]), 7 * s), M["brown"], O * s, cyclic=True)
    G.stroke(d, P(circ(-5, -5, 18, 48)), M["mustard"], O * s, cyclic=True)
    G.stroke(d, P(circ(-5, -5, 13, 48)), M["sky"], I, cyclic=True)
    G.stroke(d, G.hose_outline(P(arc(-5, -5, 9, math.radians(195), math.radians(255), 10)), 2.6 * s), M["offwhite_f"], 0.0, cyclic=True)


def g_endurance(d, M, cx, cy, s):
    """The surveyor's helmet: a glass dome on a cream collar, the teal antenna; one glint, nothing inside."""
    P = lambda pts: [(cx + s * u, cy + s * v) for u, v in pts]  # noqa: E731
    G.stroke(d, P([(9, -18), (14, -28)]), M["ink"], I * 1.4)
    G.stroke(d, P(circ(14.5, -29, 3.2, 16)), M["teal"], I, cyclic=True)
    G.stroke(d, P(circ(0, -3, 20, 56)), M["sky"], O * s, cyclic=True)
    G.stroke(d, P(arc(0, -3, 20, math.radians(15), math.radians(165), 20)), M["sky_sh"], 0.0, cyclic=True)
    G.stroke(d, G.hose_outline(P(arc(0, -3, 14, math.radians(200), math.radians(262), 10)), 3.2 * s), M["offwhite_f"], 0.0, cyclic=True)
    G.stroke(d, P([(-22, 13), (22, 13), (22, 22), (-22, 22)]), M["offwhite"], O * s, cyclic=True)
    G.stroke(d, P([(-22, 17.5), (22, 17.5)]), M["ink"], I * 0.8)


def g_voyage(d, M, cx, cy, s):
    """The Pilgrim upright: a teal hull, the cream band, the mustard nose with its red tip, mustard fins, the bell, a flame."""
    P = lambda pts: [(cx + s * u, cy + s * v) for u, v in pts]  # noqa: E731
    G.stroke(d, P([(-5, 19), (5, 19), (0, 31)]), M["mustard"], I, cyclic=True)
    G.stroke(d, P([(-2.5, 19), (2.5, 19), (0, 25)]), M["offwhite_f"], 0.0, cyclic=True)
    for sx in (-1, 1):
        G.stroke(d, P([(sx * 8, 3), (sx * 18, 17), (sx * 17, 21), (sx * 8, 15)]), M["mustard"], I, cyclic=True)
        G.stroke(d, P(circ(sx * 17.5, 20, 2.4, 12)), M["red"], I, cyclic=True)
    G.stroke(d, P([(-6, 14), (6, 14), (8, 20), (-8, 20)]), M["brown"], I, cyclic=True)                     # the bell

    def hull(y0=-27.0, y1=15.0):
        L = [(-10 * math.sin(math.pi * min(1.0, (y - y0) / 26.0) / 2) ** 0.9, y) for y in np.linspace(y0, y1, 18)]
        return [(0.0, y0)] + L[1:] + [(-x, y) for x, y in reversed(L[1:])]
    G.stroke(d, P(hull()), M["teal"], O * s, cyclic=True)
    nose = [(x, y) for x, y in hull() if y <= -13.0]
    G.stroke(d, P(nose), M["mustard"], I, cyclic=True)
    w_band = 10 * math.sin(math.pi * min(1.0, 27.0 / 26.0) / 2) ** 0.9
    G.stroke(d, P([(-w_band, 0), (w_band, 0), (w_band, 5), (-w_band, 5)]), M["offwhite"], I, cyclic=True)
    G.stroke(d, P(circ(0, -7, 4.2, 20)), M["mustard"], I, cyclic=True)                                      # one porthole
    G.stroke(d, P(circ(0, -7, 2.5, 16)), M["sky"], I * 0.7, cyclic=True)
    G.stroke(d, P(circ(0, -27.5, 2.4, 12)), M["red"], I, cyclic=True)


GLYPHS = {"dig": g_dig, "haul": g_haul, "ascent": g_ascent, "survey": g_survey, "endurance": g_endurance, "voyage": g_voyage}


# ---------------------------------------------------------------- the pieces
def emblem(branch, seed=50):
    c = U.Canvas(EMB, EMB)
    d, M = c.dm, extra(c)
    cx = cy = EMB / 2
    G.stroke(d, circ(cx, cy, 43, 72), M["mustard"], O, cyclic=True)                                        # the brass plaque
    G.stroke(d, circ(cx, cy, 39, 72), M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, circ(cx, cy, 36, 72), M["offwhite"], I, cyclic=True)
    G.stroke(d, sector(cx, cy, 36.5, 38.5, math.radians(-150), math.radians(-30), 16), M[BCOL[branch] + "_f"], 0.0, cyclic=True)  # its colour
    GLYPHS[branch](d, M, cx, cy, 0.98)
    return done(c, seed + BRANCHES.index(branch))


def glyph_icon(branch, S=NODE, s=0.62):
    """The mock-up's stand-in node icon (the branch glyph small); the real node icons come in batches."""
    c = U.Canvas(S, S)
    d, M = c.dm, extra(c)
    GLYPHS[branch](d, M, S / 2, S / 2, s)
    return done(c, 7)


def node_frame(state, cap=False, seed=40):
    S = CAP if cap else NODE
    c = U.Canvas(S, S)
    d, M = c.dm, extra(c)
    cx = cy = S / 2
    R = S / 2 - 5

    def shape(r):
        return scallop(cx, cy, r, 12, 0.08) if cap else circ(cx, cy, r, 64)
    if state == "locked":
        G.stroke(d, shape(R), M["lock_paper"], O * 0.7, cyclic=True)                                         # greyed ink
        G.stroke(d, circ(cx, cy, R - 6, 56), M["ln_grey"], I * 0.8, cyclic=True)
    elif state == "available":
        G.stroke(d, shape(R), M["mustard"], O, cyclic=True)                                                  # the warm rim
        G.stroke(d, circ(cx, cy, R - 5.5, 56), M["offwhite"], I, cyclic=True)
        G.stroke(d, circ(cx, cy, R - 2.6, 56), M["ln_red"], I * 0.7, cyclic=True)
    else:
        G.stroke(d, shape(R), M["mustard"], O, cyclic=True)                                                  # gold-filled
        G.stroke(d, circ(cx, cy, R - 5, 56), M["mustard_sh"], 0.0, cyclic=True)
        G.stroke(d, circ(cx, cy, R - 7.5, 56), M["mustard_f"], 0.0, cyclic=True)
        G.stroke(d, circ(cx, cy, R - 5, 56), M["ink"], I * 0.8, cyclic=True)
        G.stroke(d, G.hose_outline(arc(cx, cy, R - 10, math.radians(200), math.radians(245), 10), 2.6), M["offwhite_f"], 0.0, cyclic=True)
    return done(c, seed)


def hub(seed=60):
    c = U.Canvas(HUB, HUB)
    d, M = c.dm, extra(c)
    cx = cy = HUB / 2
    G.stroke(d, circ(cx, cy, 50, 80), M["mustard"], O, cyclic=True)
    G.stroke(d, circ(cx, cy, 43, 80), M["offwhite"], I, cyclic=True)
    for k in range(32):
        a = TAU * k / 32
        r0 = 37 if k % 8 == 0 else 40
        G.stroke(d, [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + 43 * math.cos(a), cy + 43 * math.sin(a))], M["ink"], I * 0.7)
    for k in (1, 3, 5, 7, 0, 2, 4, 6):                                                                       # short points behind
        a = -TAU / 4 + TAU * k / 8
        L, w = (34, 7) if k % 2 == 0 else (21, 5)
        tip = (cx + L * math.cos(a), cy + L * math.sin(a))
        lf = (cx + w * math.cos(a - TAU / 4), cy + w * math.sin(a - TAU / 4))
        rt = (cx + w * math.cos(a + TAU / 4), cy + w * math.sin(a + TAU / 4))
        lite, dark = ("red_f", "red_sh") if k == 0 else ("mustard_f", "mustard_sh")
        G.stroke(d, [(cx, cy), lf, tip], M[dark], 0.0, cyclic=True)
        G.stroke(d, [(cx, cy), tip, rt], M[lite], 0.0, cyclic=True)
        G.stroke(d, [(cx, cy), lf, tip, rt], M["ink"], I, cyclic=True)
    G.stroke(d, circ(cx, cy, 4, 16), M["offwhite"], I, cyclic=True)
    return done(c, seed)


def select_ring(seed=70):
    c = U.Canvas(SEL, SEL)
    d, M = c.dm, extra(c)
    cx = cy = SEL / 2
    pts = [(cx + (39 + 1.5 * math.sin(3 * t)) * math.cos(t), cy + (37 + 1.5 * math.sin(2 * t + 1)) * math.sin(t))
           for t in np.linspace(math.radians(-110), math.radians(-110 + 395), 70)]
    G.stroke(d, pts, M["ln_red"], O * 0.85)
    return done(c, seed)


def link_tile(state, seed=80):
    c = U.Canvas(64, 16)
    d, M = c.dm, extra(c)
    y = 8
    if state == "locked":
        for i in range(-1, 5):
            x0 = i * 16 + 3
            G.stroke(d, G.hose_outline([(x0, y), (x0 + 9, y)], 2.6), M["sky_sh"], 0.0, cyclic=True)
    elif state == "open":
        G.stroke(d, G.hose_outline([(-8, y), (72, y)], 3.2), M["ink_f"], 0.0, cyclic=True)
    else:
        G.stroke(d, G.hose_outline([(-8, y), (72, y)], 7.0), M["ink_f"], 0.0, cyclic=True)
        G.stroke(d, G.hose_outline([(-8, y), (72, y)], 3.4), M["mustard_f"], 0.0, cyclic=True)
    return done(c, seed)


def cost_tag(seed=90):
    W, H = 160, 56
    c = U.Canvas(W, H)
    d, M = c.dm, extra(c)
    body = [(12, 28), (27, 8), (155, 8), (155, 48), (27, 48)]
    G.stroke(d, body, M["offwhite"], O, cyclic=True)
    G.stroke(d, [(20, 28), (31, 13), (150, 13), (150, 43), (31, 43)], M["ln_brown_sh"], I * 0.8, cyclic=True)
    G.stroke(d, circ(28, 28, 5.5, 24), M["mustard"], I, cyclic=True)                                         # the brass eyelet
    G.stroke(d, circ(28, 28, 2.6, 16), M["brown_dp"], 0.0, cyclic=True)
    G.stroke(d, G.bezier((28, 28), (14, 12), (6, 16), (4, 22), n=14), M["ln_brown"], I * 1.3)             # the string
    G.stroke(d, G.bezier((28, 28), (16, 36), (8, 44), (5, 50), n=14), M["ln_brown"], I * 1.3)
    return done(c, seed, 0.025)


def panel(seed=100):
    S, sl = 256, 72
    c = U.Canvas(S, S)
    d, M = c.dm, extra(c)
    G.stroke(d, U.wavy_rect(6, 6, S - 6, S - 6, 1.0, seed), M["offwhite_dp"], 0.0, cyclic=True)                # the foxed margin
    G.stroke(d, U.wavy_rect(14, 14, S - 14, S - 14, 0.8, seed + 1), M["offwhite_sh"], 0.0, cyclic=True)
    rnd = np.random.default_rng(seed)
    for (cx, cy) in ((20, 20), (S - 20, 20), (20, S - 20), (S - 20, S - 20)):                                # corner foxing
        for k in range(3):
            G.stroke(d, G.lumpy_ellipse(cx + rnd.uniform(-5, 5), cy + rnd.uniform(-5, 5), rnd.uniform(4, 8), rnd.uniform(3, 6), n=14,
                                        lump=0.15, seed=seed + k + int(cx)), M["offwhite_dp"], 0.0, cyclic=True)
    for inset, w in ((24, I * 1.1), (29, I * 0.7)):                                                         # the double rule
        G.stroke(d, U.wavy_rect(inset, inset, S - inset, S - inset, 0.4, seed + inset), M["ln_brown"], w, cyclic=True)
    for (cx, cy, fx, fy) in ((29, 29, 1, 1), (S - 29, 29, -1, 1), (29, S - 29, 1, -1), (S - 29, S - 29, -1, -1)):   # compass-arc corners
        a0 = 0.0 if fx > 0 else math.pi
        a1 = (math.pi / 2) * (1 if fy > 0 else -1)
        G.stroke(d, arc(cx, cy, 24, a0, a0 + (a1 if fx > 0 else -a1), 16), M["ln_brown"], I * 0.8)
        for k in range(1, 4):
            t = a0 + (a1 if fx > 0 else -a1) * k / 4
            G.stroke(d, [(cx + 20 * math.cos(t), cy + 20 * math.sin(t)), (cx + 24 * math.cos(t), cy + 24 * math.sin(t))], M["ln_brown"], I * 0.7)
    G.stroke(d, U.wavy_rect(6, 6, S - 6, S - 6, 1.0, seed), M["ink"], O, cyclic=True)
    img, w = done(c, seed)                                    # no grain: a 9-slice centre is stretched, and stretched grain blotches
    return img, w, [sl] * 4


def chart(seed=110):
    S = CHART
    c = U.Canvas(S, S, ss=2)
    d, M = c.dm, extra(c)
    cx = cy = S / 2
    G.stroke(d, circ(cx, cy, 474, 256), M["offwhite"], O, cyclic=True)                                       # the round sheet
    for b in BRANCHES:                                                                                      # the branch bands
        a = math.radians(axis_deg(b))
        G.stroke(d, sector(cx, cy, 446, 464, a - math.radians(30), a + math.radians(30), 40), M[BCOL[b] + "_f"], 0.0, cyclic=True)
    for r, w in ((446, I), (464, I), (474, O)):
        G.stroke(d, circ(cx, cy, r, 256), M["ink"], w, cyclic=True)
    for k in range(72):                                                                                     # degree ticks
        a = TAU * k / 72
        r0 = 432 if k % 6 == 0 else 438
        G.stroke(d, [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + 445 * math.cos(a), cy + 445 * math.sin(a))], M["ink"], I * 0.7)
    for b in BRANCHES:                                                                                      # band separators
        a = math.radians(axis_deg(b) + 30)
        G.stroke(d, [(cx + 446 * math.cos(a), cy + 446 * math.sin(a)), (cx + 464 * math.cos(a), cy + 464 * math.sin(a))], M["ink"], I)
    for r in DIVIDERS:                                                                                      # dotted ring dividers
        n = int(TAU * r / 11)
        for k in range(n):
            a = TAU * k / n
            G.stroke(d, arc(cx, cy, r, a, a + 4.0 / r, 2), M["ln_brown_sh"], I * 0.9)
    for b in BRANCHES:                                                                                      # dashed sector spokes
        a = math.radians(axis_deg(b) + 30)
        r = 100.0
        while r < 426:
            G.stroke(d, [(cx + r * math.cos(a), cy + r * math.sin(a)), (cx + (r + 9) * math.cos(a), cy + (r + 9) * math.sin(a))], M["ln_brown_sh"], I * 0.8)
            r += 17
    G.stroke(d, circ(cx, cy, 92, 96), M["ln_brown"], I, cyclic=True)                                        # round the hub
    G.stroke(d, circ(cx, cy, 97, 96), M["ln_brown_sh"], I * 0.7, cyclic=True)
    return done(c, seed, 0.025)


def links_layer(state_of, seed=120):
    """The mock-up's links, drawn as UNITY would lay the tiles (straight, centre to centre, under the frames)."""
    S = CHART
    c = U.Canvas(S, S, ss=2)
    d, M = c.dm, extra(c)
    cx = cy = S / 2
    for a, b, _side in all_links():
        pa, pb = pos(a), pos(b)
        sa, sb = state_of(a), state_of(b)
        st = "bought" if sa == sb == "bought" else "open" if "bought" in (sa, sb) else "locked"
        P = [(cx + pa[0], cy + pa[1]), (cx + pb[0], cy + pb[1])]
        if st == "locked":
            L = math.hypot(P[1][0] - P[0][0], P[1][1] - P[0][1])
            ux, uy = (P[1][0] - P[0][0]) / L, (P[1][1] - P[0][1]) / L
            t = 3.0
            while t < L - 3:
                e = min(t + 9, L - 3)
                G.stroke(d, G.hose_outline([(P[0][0] + ux * t, P[0][1] + uy * t), (P[0][0] + ux * e, P[0][1] + uy * e)], 2.6), M["sky_sh"], 0.0, cyclic=True)
                t += 16
        elif st == "open":
            G.stroke(d, G.hose_outline(P, 3.2), M["ink_f"], 0.0, cyclic=True)
        else:
            G.stroke(d, G.hose_outline(P, 7.0), M["ink_f"], 0.0, cyclic=True)
            G.stroke(d, G.hose_outline(P, 3.4), M["mustard_f"], 0.0, cyclic=True)
    return done(c, seed)


# ---------------------------------------------------------------- the 1080p mock-up
def ov(dst, fr, x, y, alpha=1.0):
    """Composite an RGBA uint8 sprite with its top-left at (x, y), clipped to dst."""
    h, w = fr.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    f = fr[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32) / 255.0
    a = f[..., 3:4] * alpha
    dst[y0:y1, x0:x1] = f[..., :3] * a + dst[y0:y1, x0:x1] * (1 - a)


def letter(dst, text, x, y, size, font=None, col=None, seed=0):
    m = U.text_mask(font or U.PATRICK, text, size, wobble=0.25, seed=seed)
    colv = np.array(v3.hex_rgb(col or v3.INK), np.float32) / 255.0
    h, w = m.shape
    h, w = min(h, dst.shape[0] - y), min(w, dst.shape[1] - x)
    sub = dst[y:y + h, x:x + w]
    sub[:] = colv * m[:h, :w, None] + sub * (1 - m[:h, :w, None])
    return m.shape[1]


BOUGHT = {"centre", "dig_power_1", "dig_brush_1", "dig_power_2", "haul_pack_1", "sur_depth_1", "voy_price_1"}
SELECTED = "dig_power_3"


def state_of(n):
    if n in BOUGHT:
        return "bought"
    req = ["centre"] if LAYOUT[n][1] == 1 else LINKS.get(n, [])
    side = [a if b == n else b for a, b in SIDEWAYS if n in (a, b)]
    return "available" if any(q in BOUGHT for q in req + side) else "locked"


def preview(out_dir, out=None, footnote=None):
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    pieces, widths = {}, []

    def keep(name, res):
        img, w = res[0], res[1]
        pieces[name] = img
        widths.extend(w)
        return img
    pan, _w, sl = panel()
    pieces["panel"] = pan
    ch = keep("chart", chart())
    hb = keep("hub", hub())
    emb = {b: keep(f"emblem_{b}", emblem(b)) for b in BRANCHES}
    fr = {(st, cap): keep(f"node_{'cap_' if cap else ''}{st}", node_frame(st, cap)) for st in ("locked", "available", "bought") for cap in (False, True)}
    sel = keep("select", select_ring())
    lk = {st: keep(f"link_{st}", link_tile(st)) for st in ("locked", "open", "bought")}
    tag = keep("cost_tag", cost_tag())
    icons = {b: glyph_icon(b)[0] for b in BRANCHES}
    lay = links_layer(state_of)[0]

    W, H = 1920, 1080
    img = np.empty((H, W, 3), np.float32)
    img[:] = np.array(v3.hex_rgb(DP("sky")), np.float32) / 255.0 * 0.55                                       # the game behind, dimmed
    ov(img, U.nine_slice(pan, sl, 1880, 1040), 20, 20)
    ox, oy = 60, 60
    ov(img, ch, ox, oy)
    ov(img, lay, ox, oy)
    ccx, ccy = ox + CHART // 2, oy + CHART // 2
    for n, (b, r, x, y) in LAYOUT.items():
        st = state_of(n)
        f = fr[(st, r == 5)]
        px, py = int(round(ccx + x)), int(round(ccy + y))
        ov(img, f, px - f.shape[1] // 2, py - f.shape[0] // 2)
        ov(img, icons[b], px - NODE // 2, py - NODE // 2, 0.4 if st == "locked" else 1.0)
        if n == SELECTED:
            ov(img, sel, px - SEL // 2, py - SEL // 2)
    for b in BRANCHES:
        a = math.radians(axis_deg(b))
        ov(img, emb[b], int(round(ccx + EMB_R * math.cos(a))) - EMB // 2, int(round(ccy + EMB_R * math.sin(a))) - EMB // 2)
    ov(img, hb, ccx - HUB // 2, ccy - HUB // 2)
    # the right column: the title, the purse, the selected node's card with its cost tag, the legend
    X = 1110
    letter(img, "Skill Tree", X, 52, 72, U.LIMELIGHT, seed=1)
    letter(img, "Scrip 1 240   -   Surveyor Rank 3", X + 4, 150, 34, seed=2)
    card = U.PANELS["inventory"][3](192, 192, [48, 48, 48, 48])[0]
    ov(img, U.nine_slice(card, [48, 48, 48, 48], 760, 360), X - 10, 210)
    ov(img, fr[("available", False)], X + 30, 250)
    ov(img, icons["dig"], X + 30, 250)
    letter(img, "Beam Power III", X + 112, 252, 44, seed=3)
    letter(img, "Dig  -  ring 3", X + 114, 304, 28, col=SH("brown"), seed=4)
    letter(img, "Beam power +1.5", X + 36, 350, 34, seed=5)
    letter(img, "needs: Beam Power II (bought)", X + 36, 396, 28, col=SH("brown"), seed=6)
    t = U.nine_slice(tag, [48, 16, 20, 16], 400, 56)
    ov(img, t, X + 30, 470)
    letter(img, "1 100 Scrip  +  hematite x6", X + 86, 478, 30, seed=7)
    ly = 640
    letter(img, "frames", X, ly, 30, seed=8)
    for k, st in enumerate(("locked", "available", "bought")):
        ov(img, fr[(st, False)], X + 10 + 120 * k, ly + 44)
        ov(img, icons["survey"], X + 10 + 120 * k, ly + 44, 0.4 if st == "locked" else 1.0)
        ov(img, fr[(st, True)], X + 380 + 100 * k, ly + 40)
        letter(img, st, X + 10 + 120 * k, ly + 112, 24, col=SH("brown"), seed=9 + k)
    letter(img, "ring 5", X + 470, ly + 112, 24, col=SH("brown"), seed=13)
    ly = 820
    letter(img, "links", X, ly, 30, seed=14)
    for k, st in enumerate(("locked", "open", "bought")):
        ov(img, np.tile(lk[st], (1, 3, 1)), X + 10 + 230 * k, ly + 50)
        letter(img, st, X + 10 + 230 * k, ly + 72, 24, col=SH("brown"), seed=15 + k)
    letter(img, "a sideways link: the same tiles across a sector's spoke", X, ly + 120, 24, col=SH("brown"), seed=19)

    # the sheet: the mock-up at 1x, then each sprite at 1x and 2x on paper, with its checks
    lines, row = [], []
    for name, p in pieces.items():
        hit = v3.palette_hits(p, "earth")[0] * 100
        m = v3.EDGE_MARGIN
        tiles = name.startswith("link_")
        edge = (p[:m, :, 3].any() or p[-m:, :, 3].any() or (not tiles and (p[:, :m, 3].any() or p[:, -m:, 3].any())))
        if name == "panel":
            edge = False                                                                                    # a 9-slice paper fills its frame
        lines.append(f"{name}: {p.shape[1]}x{p.shape[0]}, palette {hit:.1f}%" + ("; EDGE" if edge else ""))
    strips, cur, x = [], [], 10                                                                             # sprites packed into rows
    for name in [k for k in pieces if k not in ("chart", "panel")]:
        w2 = max(2 * pieces[name].shape[1], 90) + 14
        if x + w2 > W:
            strips.append(cur)
            cur, x = [], 10
        cur.append((name, x))
        x += w2
    strips.append(cur)
    rows_ = []
    for cur in strips:
        hm = max(pieces[n].shape[0] for n, _x in cur)
        r_ = np.empty((24 + 3 * hm + 18, W, 3), np.float32)
        r_[:] = review.PAPER
        for name, x in cur:
            p = pieces[name]
            ov(r_, p, x, 24)
            ov(r_, np.repeat(np.repeat(p, 2, axis=0), 2, axis=1), x, 24 + hm + 8)
            review._label(r_, name, x, 6, scale=1)
        rows_.append(r_)
    strip = np.vstack(rows_)
    cr = crossings()
    foot = np.empty((40 + 16 * ((len(lines) + 2) // 3), W, 3), np.float32)
    foot[:] = review.PAPER
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6 + (i % 3) * 620, 6 + 16 * (i // 3), scale=1)
    review._label(foot, f"links crossing in this layout: {len(cr)}; node icons here are the branch glyphs (the real icons come in batches)",
                  6, foot.shape[0] - 30, scale=1)
    head = np.empty((26, W, 3), np.float32)
    head[:] = review.PAPER
    review._label(head, "B-204 the Skill Tree panel mock-up at 1080p (1x), then its sprites at 1x and 2x", 6, 6)
    sheet = np.vstack([head, img, strip, foot])
    import time
    review.draw(sheet, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, sheet.shape[0] - 14, (1.0, 1.0, 0.85))
    out = out or os.path.join(out_dir, "review_b204_skilltree_mockup.png")
    review.write(out, sheet)
    print("written", out, sheet.shape[1], "x", sheet.shape[0])
    for ln in lines:
        print(ln)
    print("crossings:", len(cr))
    for a, b in cr:
        print("  ", a, "x", b)
    if widths:
        print(f"ink {min(w[1] for w in widths):.1f}-{max(w[2] for w in widths):.1f} px")


# ---------------------------------------------------------------- the export (LEAD 17:0x: the mock-up accepted; contract 11.6)
KIT = "ui/skilltree"


def kit():
    """[(name, rgba, meta extras)] for every sprite of the panel kit."""
    pan, _w, sl = panel()
    out = [("panel", pan, {"slice": list(sl), "slice_order": "[left, top, right, bottom] px in from each edge (contract 11.6); Unity's Sprite.border is (left, bottom, right, top)",
                           "note": "aged chart paper, no grain (it is stretched); the chart sits on it, the node card is UiKit's inventory panel"}),
           ("chart", chart()[0], {"ring_r_px": {str(k): v for k, v in RING_R.items()}, "dividers_r_px": list(DIVIDERS), "emblem_r_px": EMB_R,
                                  "branch_axis_deg": {b: axis_deg(b) for b in BRANCHES}, "slots_deg": {"2": [-15, 15], "3": [-20, 0, 20]},
                                  "angles": "screen degrees from +x, y down (Dig at the top, then clockwise); a node sits at its ring radius, its branch axis + its slot",
                                  "note": "the round chart: the six branches' colour bands, degree ticks, dotted ring dividers, dashed spokes at the sector borders; "
                                          "nodes, links, emblems and the hub are laid over it at runtime (D1_TABLES §5's slot order, counter-clockwise first)"}),
           ("hub", hub()[0], {"note": "the centre (the start): always bought; the ring-1 links run from it"})]
    for b in BRANCHES:
        out.append((f"emblem_{b}", emblem(b)[0], {"branch": b, "colour": BCOL[b], "note": f"the {b} branch's plaque, at emblem_r_px on its axis"}))
    for cap in (False, True):
        for st in ("locked", "available", "bought"):
            out.append((f"node_{'cap_' if cap else ''}{st}", node_frame(st, cap)[0],
                        {"state": st, "ring": "5" if cap else "1-4", "icon_display_px": 40, "icon_alpha": 0.4 if st == "locked" else 1.0,
                         "note": "a node's frame; its icon (icons/nodes/<id>) is drawn centred over it at icon_display_px, at icon_alpha"}))
    out.append(("select", select_ring()[0], {"note": "a red pencil loop centred on the selected node"}))
    for st in ("locked", "open", "bought"):
        out.append((f"link_{st}", link_tile(st)[0], {"state": st, "tile_x": True, "repeat_px": 64, "line_row": 8,
                                                      "mapping": "tiled along the link centre to centre (Tiled draw mode), rotated to it, drawn under the frames",
                                                      "note": "locked: neither end bought; open: one end bought; bought: both ends bought"}))
    out.append(("cost_tag", cost_tag()[0], {"slice": [48, 16, 20, 16], "stretch": "x only", "lettering": "runtime",
                                            "note": "the cost (Scrip + materials) lettered in Patrick Hand right of the eyelet"}))
    return out


def export(art, names=None):
    """Writes ui/skilltree/<name>_color.png + .json (names: only those, e.g. one re-drawn key); every check runs before
    anything is written. -> [(key, w, h, bytes)]"""
    import json
    from meridian import pngio
    built, problems = [], []
    for name, img, extra_meta in kit():
        if names and name not in names:
            continue
        h, w = img.shape[:2]
        meta = {"key": f"{KIT}/{name}", "style": "v3", "ppu": U.PPU, "pivot": [0.5, 0.5], "width": w, "height": h, "palette": "earth"}
        meta.update(extra_meta)
        hit = v3.palette_hits(img, "earth")[0]
        m = v3.EDGE_MARGIN
        tiles = name.startswith("link_")
        if w % 4 or h % 4:
            problems.append(f"{name}: {w}x{h} not a multiple of 4")
        if hit < 0.995:
            problems.append(f"{name}: palette {hit * 100:.1f}%")
        if name != "panel" and (img[:m, :, 3].any() or img[-m:, :, 3].any() or (not tiles and (img[:, :m, 3].any() or img[:, -m:, 3].any()))):
            problems.append(f"{name}: touches the {m} px edge")
        built.append((meta["key"], img, meta))
    if problems:
        raise ValueError("skill tree kit checks: " + "; ".join(problems))
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
    return [f"{KIT}/{n}" for n in (["panel", "chart", "hub"] + [f"emblem_{b}" for b in BRANCHES]
                                   + [f"node_{c}{s}" for c in ("", "cap_") for s in ("locked", "available", "bought")]
                                   + ["select"] + [f"link_{s}" for s in ("locked", "open", "bought")] + ["cost_tag"])]


if __name__ == "__main__":                       # <preview dir> [--check]: --check prints the crossings only
    if "--check" in sys.argv:
        _cr = crossings()
        print("crossings:", len(_cr), _cr)
    else:
        preview(sys.argv[1])
