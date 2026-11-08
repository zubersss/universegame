"""B-204 (D-174; LEAD 17:0x): the Skill Tree's node icons, one per node of docs/D1_TABLES.md §5 (as revised 17:1x), in the
house style of B-199's item icons (128x128, 1 m = 128 px, ink 2-3 / 1-1.5 px, a colour lit top-left with its mid and deep
shadow, the Earth palette, no faces: never two round marks side by side). Drawn to read at the chart's 40 px (the node frame's
icon_display_px): one bold silhouette each, and a level meter at the bottom right (five bars, the node's level filled) on the
nodes that are a step of a chain (dig_power_3 = 3 of 5).

  batch 1  ring 1: dig_power_1, dig_brush_1, haul_pack_1, haul_dirt_1, asc_grapple_1, asc_ladder_1, sur_scan_1, sur_depth_1,
           end_air_1, end_fall_1, voy_price_1, voy_hold_1
  Only EXPORT_BATCHES (the accepted ones) export: icons/nodes/<id>_color.png + .json.

  python -I build_icons_nodes_v3.py <review png> [batch]    lock-free preview: each icon at 1x, at 40 px in the three
                                                            node frames (B-204's kit), and at 32 px
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp, v3  # noqa: E402
import build_icons_items_v3 as IT  # noqa: E402

G = IT.G
import gp_raster as GR  # noqa: E402

O, I = G.OUTER, G.INNER
SIZE, PPU = 128, 128
KEY = "icons/nodes/{}"
TAU = 2 * math.pi
CHAIN_LEN = {"dig_power": 5, "dig_brush": 2, "dig_rhythm": 2, "haul_pack": 5, "haul_dirt": 1, "haul_light": 2, "haul_magnet": 1,
             "asc_grapple": 3, "asc_ladder": 2, "asc_jet": 3, "asc_climb": 1, "sur_scan": 4, "sur_depth": 1, "sur_preview": 2,
             "end_air": 4, "end_fall": 2, "end_heat": 2, "end_deep": 2, "voy_price": 3, "voy_hold": 2, "voy_thrust": 3, "voy_skip": 2}


def level_of(nid):
    """(n, of) for a node that is a step of a chain (its id ends in _<n> and the chain has more than one step), else None."""
    head, _, tail = nid.rpartition("_")
    if tail.isdigit() and CHAIN_LEN.get(head, 1) > 1:
        return int(tail), CHAIN_LEN[head]
    return None


def meter(d, M, n, of):
    """The level meter, bottom right: `of` bars rising left to right, the first n filled mustard."""
    for i in range(of):
        x = 0.42 - 0.052 * (of - i)
        h = 0.05 + 0.022 * i
        G.stroke(d, [(x, -0.43), (x + 0.036, -0.43), (x + 0.036, -0.43 + h), (x, -0.43 + h)], M["mustard_i" if i < n else "off_sh_i"], I, cyclic=True)


def rot(cx, cz, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    return lambda pts: [(cx + u * ca - v * sa, cz + u * sa + v * ca) for u, v in pts]


def circ(cx, cz, r, n=40, rz=None):
    rz = r if rz is None else rz
    return [(cx + r * math.cos(TAU * i / n), cz + rz * math.sin(TAU * i / n)) for i in range(n)]


def arc(cx, cz, r, a0, a1, n=20):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cz + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def arrow(d, M, a, b, w, role, head=2.2):
    """A fat arrow from a to b (a hose shaft and a triangle head), inked."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    hb = (b[0] - ux * w * head, b[1] - uz * w * head)
    G.stroke(d, G.hose_outline([a, hb], w), M[role + "_i"], I, cyclic=True)
    G.stroke(d, [(hb[0] - uz * w * 1.2, hb[1] + ux * w * 1.2), b, (hb[0] + uz * w * 1.2, hb[1] - ux * w * 1.2)], M[role + "_i"], I, cyclic=True)


# ---------------------------------------------------------------- the motifs (each takes a level; the chain's steps share one)
def m_beam(d, M, lv=1):
    """The Rig's Beam firing right: a teal emitter, its grip, the beam with an offwhite core, sparks at the dig face."""
    R = rot(-0.08, 0.08, 0.22)
    G.stroke(d, R([(0.02, -0.05), (0.38, -0.12), (0.38, 0.12), (0.02, 0.05)]), M["teal_i"], I, cyclic=True)        # the beam
    G.stroke(d, G.hose_outline(R([(0.06, 0.0), (0.33, 0.0)]), 0.035), M["off"], 0.0, cyclic=True)
    G.stroke(d, G.hose_outline(R([(-0.22, -0.08), (-0.27, -0.27)]), 0.09), M["brown_i"], I, cyclic=True)           # the grip
    G.stroke(d, R([(-0.34, -0.1), (-0.05, -0.1), (-0.05, 0.1), (-0.34, 0.1)]), M["teal_sh_i"], O, cyclic=True)     # the body
    G.stroke(d, R([(-0.34, 0.02), (-0.05, 0.02), (-0.05, 0.1), (-0.34, 0.1)]), M["teal"], 0.0, cyclic=True)
    G.stroke(d, R([(-0.34, -0.1), (-0.05, -0.1), (-0.05, 0.1), (-0.34, 0.1)]), M["ink"], O, cyclic=True)
    G.seam(d, R([(-0.26, -0.1), (-0.26, 0.1)]), M["ink"])
    G.stroke(d, R([(-0.05, -0.085), (0.04, -0.055), (0.04, 0.055), (-0.05, 0.085)]), M["mustard_i"], I, cyclic=True)  # the nozzle
    for a in (-0.8, 0.0, 0.8):                                                                                          # sparks
        G.stroke(d, G.hose_outline(R([(0.41 + 0.02 * math.cos(a), 0.1 * math.sin(a)), (0.47 + 0.03 * math.cos(a), 0.17 * math.sin(a))]), 0.022),
                 M["mustard"], 0.0, cyclic=True)


def m_brush(d, M, lv=1):
    """The dig brush's reach: a scooped half-disc in the ground under a dashed teal circle, an arrow out along its radius."""
    G.stroke(d, [(-0.42, -0.3), (0.3, -0.3), (0.3, 0.0)] + [(x, 0.0 + 0.012 * math.sin(30 * x)) for x in (0.2, 0.0, -0.2, -0.42)], M["brown_i"], O, cyclic=True)
    cx, cz, r = -0.08, 0.0, 0.25 + 0.03 * (lv - 1)
    G.stroke(d, arc(cx, cz, r * 0.92, math.pi, TAU, 24), M["brown_dp"], 0.0, cyclic=True)                              # the scoop
    G.stroke(d, arc(cx, cz, r * 0.92, math.pi, TAU, 24), M["ink"], I, cyclic=False)
    for k in range(12):                                                                                                 # the reach
        a = TAU * k / 12
        G.stroke(d, G.hose_outline(arc(cx, cz, r, a, a + TAU / 24, 3), 0.03), M["teal_i"], I * 0.8, cyclic=True)
    arrow(d, M, (cx + 0.02, cz + 0.03), (cx + r + 0.08, cz + 0.03), 0.045, "mustard")


def m_pack(d, M, lv=1):
    """The pack, front on: a brown body, a mustard flap, one buckle, a front pocket, a carry loop."""
    G.stroke(d, G.hose_outline(arc(-0.06, 0.22, 0.09, 0.0, math.pi, 10), 0.04), M["brown_i"], I, cyclic=True)
    body = [(-0.3, 0.22), (0.18, 0.22), (0.2, -0.26), (0.15, -0.31), (-0.27, -0.31), (-0.32, -0.26)]
    G.stroke(d, body, M["brown_i"], O, cyclic=True)
    G.stroke(d, [(0.06, 0.22), (0.18, 0.22), (0.2, -0.26), (0.15, -0.31), (0.08, -0.31)], M["brown_sh"], 0.0, cyclic=True)
    G.stroke(d, body, M["ink"], O, cyclic=True)
    G.stroke(d, [(-0.22, -0.08), (0.1, -0.08), (0.1, -0.24), (-0.22, -0.24)], M["brown_dp_i"], I, cyclic=True)        # the pocket
    G.stroke(d, [(-0.32, 0.24), (0.2, 0.24), (0.2, 0.04)] + arc(-0.06, 0.04, 0.26, 0.0, -math.pi, 14)[1:] + [(-0.32, 0.04)], M["mustard_i"], O, cyclic=True)
    G.stroke(d, [(-0.04, 0.24), (0.2, 0.24), (0.2, 0.04)] + arc(-0.06, 0.04, 0.26, 0.0, -0.55, 6)[1:], M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, [(-0.32, 0.24), (0.2, 0.24), (0.2, 0.04)] + arc(-0.06, 0.04, 0.26, 0.0, -math.pi, 14)[1:] + [(-0.32, 0.04)], M["ink"], O, cyclic=True)
    G.stroke(d, [(-0.1, -0.24), (-0.02, -0.24), (-0.02, -0.15), (-0.1, -0.15)], M["off_i"], I, cyclic=True)           # the buckle (one)


def m_dirt(d, M, lv=1):
    """The dirt store: a canvas sack filled to a brown heap, a tie round its neck, two clods."""
    sack = [(-0.3, -0.32), (0.16, -0.32), (0.24, -0.18), (0.2, 0.06), (0.1, 0.12), (-0.24, 0.12), (-0.34, 0.06), (-0.38, -0.18)]
    G.stroke(d, sack, M["mustard_sh_i"], O, cyclic=True)
    G.stroke(d, [(0.0, -0.32), (0.16, -0.32), (0.24, -0.18), (0.2, 0.06), (0.1, 0.12), (0.04, 0.12)], M["mustard_dp"], 0.0, cyclic=True)
    G.stroke(d, sack, M["ink"], O, cyclic=True)
    for x in (-0.22, -0.06, 0.08):
        G.seam(d, [(x, -0.28), (x + 0.02, -0.08)], M["ink"])
    G.stroke(d, IT.lump(-0.07, 0.2, 0.25, 0.12, 31), M["brown_i"], O, cyclic=True)                                  # the heap
    G.stroke(d, G.hose_outline([(-0.3, 0.1), (0.16, 0.1)], 0.05), M["red_sh_i"], I, cyclic=True)                       # the tie
    for x, z, r in ((0.26, 0.3, 0.05), (-0.36, 0.3, 0.04)):
        G.stroke(d, IT.lump(x, z, r, r * 0.8, int(100 * x) + 40, n=6), M["brown_sh_i"], I, cyclic=True)


def m_grapple(d, M, lv=1):
    """The Grapple: a three-pronged steel hook on a ring, its rope rising up-left in a loop."""
    G.stroke(d, G.hose_outline([(-0.08, 0.12), (-0.2, 0.3), (-0.38, 0.32), (-0.4, 0.16), (-0.26, 0.12)], 0.05), M["mustard_sh_i"], I, cyclic=True)
    G.stroke(d, G.hose_outline([(0.0, 0.18), (0.02, -0.2)], 0.07), M["sky_sh_i"], O, cyclic=True)                      # the shank
    for s in (-1, 1):                                                                                                  # two side prongs
        G.stroke(d, G.hose_outline([(0.02, -0.18), (0.14 * s + 0.02, -0.26), (0.24 * s + 0.02, -0.18), (0.27 * s + 0.02, -0.04)], 0.055),
                 M["sky_sh_i"], O, cyclic=True)
        G.stroke(d, [(0.27 * s - 0.03 + 0.02, -0.04), (0.27 * s + 0.03 + 0.02, -0.04), (0.27 * s + 0.02, 0.04)], M["sky_i"], I, cyclic=True)
    G.stroke(d, G.hose_outline([(0.02, -0.18), (0.03, -0.32)], 0.06), M["sky_sh_i"], I, cyclic=True)                   # the front prong
    G.stroke(d, circ(-0.01, 0.24, 0.065, 20), M["sky_i"], O, cyclic=True)                                             # the eye ring
    G.stroke(d, circ(-0.01, 0.24, 0.03, 14), M["off_sh"], 0.0, cyclic=True)
    G.stroke(d, circ(-0.01, 0.24, 0.03, 14), M["ink"], I, cyclic=True)


def m_ladder(d, M, lv=1):
    """A Builder ladder: brown rails and rungs, its feet in a heap of the dirt it is made from."""
    R = rot(0.0, 0.0, -0.18)
    for u in (-0.15, 0.15):
        G.stroke(d, G.hose_outline(R([(u, -0.3), (u, 0.4)]), 0.06), M["brown_i"], O, cyclic=True)
    for k in range(5):
        v = -0.18 + 0.13 * k
        G.stroke(d, G.hose_outline(R([(-0.13, v), (0.13, v)]), 0.045), M["mustard_sh_i"], I, cyclic=True)
    G.stroke(d, IT.lump(-0.08, -0.33, 0.28, 0.1, 51), M["brown_sh_i"], O, cyclic=True)
    for x in (-0.24, 0.0, 0.12):
        G.stroke(d, IT.lump(x, -0.27, 0.05, 0.035, int(100 * x) + 60, n=6), M["brown_i"], I, cyclic=True)


def m_scan(d, M, lv=1):
    """The scan: pulse arcs spreading up-right from a teal emitter at the lower left, a mustard find at the outer arc."""
    cx, cz = -0.3, -0.24
    G.stroke(d, [(cx - 0.09, cz - 0.08), (cx + 0.09, cz - 0.08), (cx + 0.07, cz + 0.05), (cx - 0.07, cz + 0.05)], M["sky_sh_i"], I, cyclic=True)
    G.stroke(d, circ(cx, cz + 0.07, 0.06, 18), M["teal_i"], I, cyclic=True)
    for k, r in enumerate((0.22, 0.38, 0.54)):
        G.stroke(d, G.hose_outline(arc(cx, cz + 0.07, r, 0.12, 1.45, 18), 0.05 - 0.008 * k), M["teal_i" if k < 2 else "teal_sh_i"], I, cyclic=True)
    fx, fz = cx + 0.54 * math.cos(0.75), cz + 0.07 + 0.54 * math.sin(0.75)
    G.stroke(d, [(fx, fz + 0.08), (fx + 0.06, fz), (fx, fz - 0.08), (fx - 0.06, fz)], M["mustard_i"], I, cyclic=True)


def m_depth(d, M, lv=1):
    """The depth readout: two tiers' bands behind a ruler, a red marker on the tier border below."""
    G.stroke(d, [(-0.2, 0.36), (0.36, 0.36), (0.36, 0.0), (-0.2, 0.0)], M["brown_sh_i"], I, cyclic=True)
    G.stroke(d, [(-0.2, 0.0), (0.36, 0.0), (0.36, -0.36), (-0.2, -0.36)], M["sky_sh_i"], I, cyclic=True)
    for x in (-0.06, 0.14):
        G.seam(d, [(x, -0.06), (x + 0.03, -0.2)], M["ink"])
    G.stroke(d, [(-0.4, 0.4), (-0.26, 0.4), (-0.26, -0.4), (-0.4, -0.4)], M["off_i"], O, cyclic=True)                # the ruler
    for k in range(9):
        z = 0.32 - 0.08 * k
        G.stroke(d, [(-0.26, z), (-0.26 - (0.08 if k % 2 == 0 else 0.05), z)], M["ink"], I)
    G.stroke(d, G.hose_outline([(-0.2, 0.0), (0.36, 0.0)], 0.03), M["red"], 0.0, cyclic=True)                           # the next border
    arrow(d, M, (0.12, 0.3), (0.12, 0.05), 0.07, "red")


def m_air(d, M, lv=1):
    """An oxygen bottle: an offwhite cylinder, a teal band, a steel valve with a breath of air."""
    body = [(-0.2, -0.36), (0.12, -0.36), (0.12, 0.12)] + arc(-0.04, 0.12, 0.16, 0.0, math.pi, 14)[1:] + [(-0.2, 0.12)]
    G.stroke(d, body, M["off_i"], O, cyclic=True)
    G.stroke(d, [(0.04, -0.36), (0.12, -0.36), (0.12, 0.12)] + arc(-0.04, 0.12, 0.16, 0.0, 0.7, 6)[1:] + [(0.04, 0.2)], M["off_sh"], 0.0, cyclic=True)
    G.stroke(d, body, M["ink"], O, cyclic=True)
    G.stroke(d, [(-0.2, -0.08), (0.12, -0.08), (0.12, 0.04), (-0.2, 0.04)], M["teal_i"], I, cyclic=True)               # the band
    G.stroke(d, [(-0.09, 0.27), (0.01, 0.27), (0.01, 0.35), (-0.09, 0.35)], M["sky_sh_i"], I, cyclic=True)              # the valve
    G.stroke(d, G.hose_outline([(0.01, 0.31), (0.09, 0.31)], 0.035), M["sky_sh_i"], I, cyclic=True)
    for k, (x, z) in enumerate(((0.16, 0.36), (0.25, 0.3), (0.33, 0.37))):                                              # a breath
        G.stroke(d, G.hose_outline(arc(x, z, 0.04 + 0.01 * k, -0.3, 2.4, 8), 0.022), M["sky"], 0.0, cyclic=True)


def m_fall(d, M, lv=1):
    """A boot landing on a coil spring, motion lines above it."""
    for x in (-0.18, -0.06):
        G.stroke(d, G.hose_outline([(x, 0.42), (x, 0.3)], 0.025), M["sky_sh"], 0.0, cyclic=True)
    boot = [(-0.3, 0.02), (0.1, 0.02), (0.22, -0.02), (0.24, -0.1), (-0.3, -0.1)]
    G.stroke(d, [(-0.3, 0.02), (-0.3, 0.26), (-0.1, 0.26), (-0.1, 0.02)], M["brown_i"], O, cyclic=True)                # the shaft
    G.stroke(d, boot, M["brown_i"], O, cyclic=True)
    G.stroke(d, [(-0.3, -0.1), (0.24, -0.1), (0.24, -0.14), (-0.3, -0.14)], M["brown_dp_i"], I, cyclic=True)           # the sole
    pts = [(-0.24, -0.16)]                                                                                              # the spring
    for k in range(7):
        pts.append((0.16 if k % 2 == 0 else -0.24, -0.2 - 0.03 * k))
    G.stroke(d, G.hose_outline(pts, 0.04), M["sky_i"], I, cyclic=True)
    G.stroke(d, [(-0.32, -0.4), (0.24, -0.4), (0.24, -0.43), (-0.32, -0.43)], M["sky_sh_i"], I, cyclic=True)


def m_price(d, M, lv=1):
    """The Waystation's price: a Scrip coin (a star stamped in it) and a green arrow up."""
    G.stroke(d, circ(-0.1, -0.02, 0.27, 44), M["mustard_i"], O, cyclic=True)
    G.stroke(d, arc(-0.1, -0.02, 0.27, -1.2, 0.6, 12) + arc(-0.1, -0.02, 0.21, 0.6, -1.2, 12), M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, circ(-0.1, -0.02, 0.21, 40), M["ink"], I, cyclic=True)
    st = []
    for k in range(10):                                                                                                 # the stamp: a star
        a = TAU / 4 + TAU * k / 10
        r = 0.13 if k % 2 == 0 else 0.055
        st.append((-0.1 + r * math.cos(a), -0.02 + r * math.sin(a)))
    G.stroke(d, st, M["mustard_sh_i"], I, cyclic=True)
    arrow(d, M, (0.3, -0.12), (0.3, 0.4), 0.08, "green")


def m_hold(d, M, lv=1):
    """The rocket's hold: a strapped cargo crate, plank seams, a red stencil band."""
    G.stroke(d, [(-0.36, -0.32), (0.26, -0.32), (0.26, 0.24), (-0.36, 0.24)], M["mustard_sh_i"], O, cyclic=True)
    G.stroke(d, [(0.12, -0.32), (0.26, -0.32), (0.26, 0.24), (0.12, 0.24)], M["mustard_dp"], 0.0, cyclic=True)
    G.stroke(d, [(-0.36, -0.32), (0.26, -0.32), (0.26, 0.24), (-0.36, 0.24)], M["ink"], O, cyclic=True)
    for z in (-0.13, 0.05):
        G.seam(d, [(-0.34, z), (0.24, z)], M["ink"])
    G.stroke(d, [(-0.36, 0.24), (-0.28, 0.24), (0.26, -0.24), (0.26, -0.32), (0.18, -0.32), (-0.36, 0.16)], M["brown_i"], I, cyclic=True)   # the brace
    G.stroke(d, [(-0.12, -0.32), (-0.04, -0.32), (-0.04, 0.24), (-0.12, 0.24)], M["red_sh_i"], I, cyclic=True)          # the strap
    G.stroke(d, [(-0.15, -0.06), (-0.01, -0.06), (-0.01, 0.02), (-0.15, 0.02)], M["sky_sh_i"], I, cyclic=True)          # its buckle


MOTIF = {"dig_power": m_beam, "dig_brush": m_brush, "haul_pack": m_pack, "haul_dirt": m_dirt, "asc_grapple": m_grapple,
         "asc_ladder": m_ladder, "sur_scan": m_scan, "sur_depth": m_depth, "end_air": m_air, "end_fall": m_fall,
         "voy_price": m_price, "voy_hold": m_hold}


def draw_node(d, M, nid):
    head, _, tail = nid.rpartition("_")
    lv = level_of(nid)
    MOTIF[head if tail.isdigit() else nid](d, M, lv[0] if lv else 1)
    if lv:
        meter(d, M, *lv)


BATCHES = {1: ["dig_power_1", "dig_brush_1", "haul_pack_1", "haul_dirt_1", "asc_grapple_1", "asc_ladder_1", "sur_scan_1", "sur_depth_1",
               "end_air_1", "end_fall_1", "voy_price_1", "voy_hold_1"]}
EXPORT_BATCHES = ()                                                                             # only LEAD-accepted batches export


def render_node(nid):
    gp = fakegp.FakeGP()
    M = IT.mats(gp, "earth")
    d = fakegp.FakeDrawing()
    draw_node(d, M, nid)
    return GR.render_frame(fakegp.strokes_of(d, gp), SIZE, SIZE, PPU, (0.5, 0.5), ss=4, seed=11)


def checks(img):
    m = v3.EDGE_MARGIN
    a = img[..., 3]
    p = []
    if a[:m].any() or a[-m:].any() or a[:, :m].any() or a[:, -m:].any():
        p.append(f"touches the {m} px edge")
    hit, off = v3.palette_hits(img, "earth")
    if hit < 0.98:
        p.append(f"palette {hit * 100:.1f}% (off {' '.join(off[:3])})")
    return p, hit


def export(art, names=None):
    import json
    from meridian import pngio
    names = list(names or [n for b in EXPORT_BATCHES for n in BATCHES[b]])
    imgs = {n: render_node(n)[0] for n in names}
    problems = [f"{n}: {x}" for n in names for x in checks(imgs[n])[0]]
    if problems:
        raise ValueError("B-204 node icon checks: " + "; ".join(problems))
    out = []
    for n in names:
        base = os.path.join(art, *KEY.format(n).split("/"))
        os.makedirs(os.path.dirname(base), exist_ok=True)
        b = pngio.write_png(base + "_color.png", imgs[n])
        lv = level_of(n)
        with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
            json.dump({"key": KEY.format(n), "style": "v3", "ppu": PPU, "pivot": [0.5, 0.5], "icon": True, "node": n,
                       **({"level": lv[0], "of": lv[1]} if lv else {}),
                       "note": "B-204: the Skill Tree node's icon; drawn at the node frame's icon_display_px (40), 0.4 alpha when locked"}, f, indent=2)
            f.write("\n")
        out.append((KEY.format(n), SIZE, SIZE, b))
    return out


def preview(out, batch=1, footnote=None):
    import time
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_skilltree_v3 as ST
    names = BATCHES[batch]
    imgs = {n: render_node(n)[0] for n in names}
    frames = {st: ST.node_frame(st)[0] for st in ("locked", "available", "bought")}
    paper = np.array(review.PAPER, np.float32)

    def down(ic, s):
        """An area resample of the 128 px icon to s px (s = 40: x5 up, 16x16 boxes; s = 32: 4x4 boxes)."""
        f = ic.astype(np.float32)
        if 128 % s:
            f = np.repeat(np.repeat(f, 5, axis=0), 5, axis=1)
        k = f.shape[0] // s
        return np.rint(f.reshape(s, k, s, k, 4).mean(axis=(1, 3))).astype(np.uint8)
    TW = 214
    W = 8 + len(names) * TW
    r1 = np.empty((156, W, 3), np.float32)
    r1[:] = paper
    review._label(r1, f"B-204 node icons, batch {batch} (1x, 128 px)", 8, 4, scale=1)
    r2 = np.empty((150, W, 3), np.float32)
    r2[:] = paper
    review._label(r2, "at 40 px in the chart's frames: locked (0.4) / available / bought; below, at 32 px", 8, 4, scale=1)
    for i, n in enumerate(names):
        x = 8 + i * TW
        r1[20:148, x:x + 128] = paper * 0.9
        review._over(r1, imgs[n], x, 20)
        review._label(r1, n, x + 132, 24, scale=1)
        sm = down(imgs[n], 40)
        for k, st in enumerate(("locked", "available", "bought")):
            ST.ov(r2, frames[st], x + 68 * k, 18)
            ST.ov(r2, sm, x + 68 * k + 12, 30, 0.4 if st == "locked" else 1.0)
        review._over(r2, down(imgs[n], 32), x + 16, 90)
        review._label(r2, n, x + 56, 100, scale=1)
    lines = []
    for n in names:
        p, hit = checks(imgs[n])
        lines.append(f"{KEY.format(n)}: palette {hit * 100:.1f}%, problems: {'; '.join(p) or 'none'}")
    foot = np.empty((30 + 16 * ((len(lines) + 1) // 2), W, 3), np.float32)
    foot[:] = paper
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6 + (i % 2) * (W // 2), 6 + 16 * (i // 2), scale=1)
    img = np.vstack([r1, r2, foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_icons_nodes_v3.py <review png> [batch]
    preview(sys.argv[1], batch=int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    fakegp.restore()
