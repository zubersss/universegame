"""B-204 (D-174; LEAD 17:0x): the Skill Tree's node icons, one per node of docs/D1_TABLES.md §5 (as revised 17:1x), in the
house style of B-199's item icons (128x128, 1 m = 128 px, ink 2-3 / 1-1.5 px, a colour lit top-left with its mid and deep
shadow, the Earth palette, no faces: never two round marks side by side). Drawn to read at the chart's 40 px (the node frame's
icon_display_px): one bold silhouette each. A chain's steps (dig_power_1..5) share a motif that changes with the step (the
Beam warms from teal to gold as B-205's Mk1-5); the json carries "level" / "of".

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
BEAM_CABLE = True             # LEAD to rule (18:1x flag): the Beam on a cable to the rig, no pistol grip (D-087); the exported
                              # dig_power_1 / _2 (and ui/skilltree/emblem_dig) still have the grip until re-exported
BEAM_TONE = {1: ("teal", "off"), 2: ("teal", "mustard"), 3: ("green", "off"), 4: ("mustard_sh", "off"), 5: ("mustard", "off")}   # B-205's
                                                                                               # Mk1-5: the beam warms from teal to gold


def m_beam(d, M, lv=1):
    """The Rig's Beam: the emitter (left) fires a straight beam into a rock (right), sparks at the dig face (rev 17:2x: a
    widening beam read as a megaphone). The beam's tone is the Beam Mk of the node's level."""
    beam, core = BEAM_TONE[lv]
    IT.faceted(d, M, IT.lump(0.3, 0.02, 0.15, 0.17, 71, n=8), "brown_sh", "brown", "brown_dp", 0.3, 0.02)            # the rock
    R = rot(-0.08, 0.04, 0.0)
    G.stroke(d, G.hose_outline(R([(0.03, 0.0), (0.25, 0.0)]), 0.085), M[beam + "_i"], I, cyclic=True)               # the beam
    G.stroke(d, G.hose_outline(R([(0.05, 0.0), (0.23, 0.0)]), 0.03), M[core], 0.0, cyclic=True)
    for a in (2.2, 2.75, 3.5, 4.05):                                                                                   # sparks
        G.stroke(d, G.hose_outline([(0.18 + 0.06 * math.cos(a), 0.04 + 0.06 * math.sin(a)), (0.18 + 0.14 * math.cos(a), 0.04 + 0.14 * math.sin(a))], 0.024),
                 M["mustard"], 0.0, cyclic=True)
    if not BEAM_CABLE:
        G.stroke(d, G.hose_outline(R([(-0.22, -0.08), (-0.27, -0.27)]), 0.09), M["brown_i"], I, cyclic=True)       # the grip
    else:                                                                    # rev 18:1x: no grip (a pistol grip read as a ray gun, a top
        G.stroke(d, G.hose_outline([(-0.42, -0.02), (-0.46, -0.16), (-0.38, -0.3), (-0.2, -0.36), (0.0, -0.4)], 0.05),   # handle as a
                 M["brown_sh_i"], I, cyclic=True)                            # padlock): a cable from its back to the rig, off below
    G.stroke(d, R([(-0.34, -0.1), (-0.05, -0.1), (-0.05, 0.1), (-0.34, 0.1)]), M["teal_sh_i"], O, cyclic=True)     # the body
    G.stroke(d, R([(-0.34, 0.02), (-0.05, 0.02), (-0.05, 0.1), (-0.34, 0.1)]), M["teal"], 0.0, cyclic=True)
    G.stroke(d, R([(-0.34, -0.1), (-0.05, -0.1), (-0.05, 0.1), (-0.34, 0.1)]), M["ink"], O, cyclic=True)
    G.seam(d, R([(-0.26, -0.1), (-0.26, 0.1)]), M["ink"])
    G.stroke(d, R([(-0.05, -0.085), (0.04, -0.055), (0.04, 0.055), (-0.05, 0.085)]), M["mustard_i"], I, cyclic=True)  # the nozzle


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
    """The pack, front on: a brown body, a mustard flap, one buckle, a front pocket, a carry loop; the steps add a steel frame
    behind (4), a bedroll on top (2), a side pouch (3) and a gold trim band (5)."""
    if lv >= 4:
        for x in (-0.36, 0.24):
            G.stroke(d, G.hose_outline([(x, -0.36), (x, 0.36)], 0.035), M["sky_sh_i"], I, cyclic=True)
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
    if lv >= 2:                                                                                                          # the bedroll
        G.stroke(d, G.hose_outline([(-0.26, 0.32), (0.14, 0.32)], 0.11), M["green_sh_i"], O, cyclic=True)
        for x in (-0.16, 0.04):
            G.stroke(d, [(x, 0.26), (x + 0.03, 0.26), (x + 0.03, 0.38), (x, 0.38)], M["brown_i"], I, cyclic=True)
    if lv >= 3:                                                                                                          # a side pouch
        G.stroke(d, [(0.2, -0.28), (0.32, -0.28), (0.32, -0.02), (0.2, -0.02)], M["brown_sh_i"], I, cyclic=True)
        G.seam(d, [(0.2, -0.08), (0.32, -0.08)], M["ink"])
    if lv >= 5:                                                                                                          # gold trim
        G.stroke(d, [(-0.31, -0.29), (0.18, -0.29), (0.17, -0.25), (-0.3, -0.25)], M["mustard_i"], I, cyclic=True)


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
    # rev 17:2x: no clods either side of the heap (a pair at the top read as ears)


def m_grapple(d, M, lv=1):
    """The Grapple: a three-pronged steel hook on a ring, its rope rising up-left in a loop; step 2: a longer line (a coil)."""
    if lv >= 2:
        G.stroke(d, G.hose_outline(arc(0.27, 0.3, 0.11, math.radians(-60), math.radians(250), 20), 0.045), M["mustard_sh_i"], I, cyclic=True)
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
    top, n, step = (0.4, 5, 0.13) if lv == 1 else (0.4, 6, 0.1)                                                       # step 2: sections
    for u in (-0.15, 0.15):                                                                                             # clamped, taller
        G.stroke(d, G.hose_outline(R([(u, -0.3), (u, top)]), 0.06), M["brown_i"], O, cyclic=True)
    for k in range(n):
        v = -0.18 + step * k
        G.stroke(d, G.hose_outline(R([(-0.13, v), (0.13, v)]), 0.045), M["mustard_sh_i"], I, cyclic=True)
    if lv >= 2:
        G.stroke(d, G.hose_outline(R([(-0.2, 0.09), (0.2, 0.09)]), 0.06), M["sky_sh_i"], I, cyclic=True)
    G.stroke(d, IT.lump(-0.08, -0.33, 0.28, 0.1, 51), M["brown_sh_i"], O, cyclic=True)
    for x in (-0.24, 0.0, 0.12):
        G.stroke(d, IT.lump(x, -0.27, 0.05, 0.035, int(100 * x) + 60, n=6), M["brown_i"], I, cyclic=True)


def m_scan(d, M, lv=1):
    """The scan: pulse arcs spreading up-right from a teal emitter at the lower left, a mustard find at the outer arc."""
    cx, cz = -0.3, -0.24
    G.stroke(d, [(cx - 0.09, cz - 0.08), (cx + 0.09, cz - 0.08), (cx + 0.07, cz + 0.05), (cx - 0.07, cz + 0.05)], M["sky_sh_i"], I, cyclic=True)
    G.stroke(d, circ(cx, cz + 0.07, 0.06, 18), M["teal_i"], I, cyclic=True)
    radii = (0.22, 0.38, 0.54) if lv == 1 else [0.2 + 0.36 * k / (lv + 1) for k in range(lv + 2)]                    # one more arc a step
    wd = 0.05 if lv == 1 else min(0.05, 0.36 / (lv + 1) * 0.45)
    for k, r in enumerate(radii):
        G.stroke(d, G.hose_outline(arc(cx, cz + 0.07, r, 0.12, 1.45, 18), (0.05 - 0.008 * k) if lv == 1 else wd),
                 M["teal_i" if k < len(radii) - 1 else "teal_sh_i"], I, cyclic=True)
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
    def bottle(dx, dz, band):
        S = lambda pts: [(x + dx, z + dz) for x, z in pts]  # noqa: E731
        body = S([(-0.2, -0.36), (0.12, -0.36), (0.12, 0.12)] + arc(-0.04, 0.12, 0.16, 0.0, math.pi, 14)[1:] + [(-0.2, 0.12)])
        G.stroke(d, body, M["off_i"], O, cyclic=True)
        G.stroke(d, S([(0.04, -0.36), (0.12, -0.36), (0.12, 0.12)] + arc(-0.04, 0.12, 0.16, 0.0, 0.7, 6)[1:] + [(0.04, 0.2)]), M["off_sh"], 0.0, cyclic=True)
        G.stroke(d, body, M["ink"], O, cyclic=True)
        G.stroke(d, S([(-0.2, -0.08), (0.12, -0.08), (0.12, 0.04), (-0.2, 0.04)]), M[band + "_i"], I, cyclic=True)        # the band
        G.stroke(d, S([(-0.09, 0.27), (0.01, 0.27), (0.01, 0.35), (-0.09, 0.35)]), M["sky_sh_i"], I, cyclic=True)        # the valve
        G.stroke(d, G.hose_outline(S([(0.01, 0.31), (0.09, 0.31)]), 0.035), M["sky_sh_i"], I, cyclic=True)
    for k in range(min(lv, 3) - 1, 0, -1):                                                                              # more bottles a step,
        bottle({1: 0.22, 2: -0.24}[k], 0.05, "teal")                                                                    # behind (step 4: gold bands)
    bottle(0.0, 0.0, "mustard" if lv >= 4 else "teal")
    for k, (x, z) in enumerate(((0.16, 0.36), (0.25, 0.3), (0.33, 0.37))):                                              # a breath
        G.stroke(d, G.hose_outline(arc(x, z, 0.04 + 0.01 * k, -0.3, 2.4, 8), 0.022), M["sky"], 0.0, cyclic=True)


def m_fall(d, M, lv=1):
    """A work boot landing on a coil spring, motion lines above it (rev 17:2x: a square shaft over a flat foot read as a
    toilet at 40 px: now a tapered shaft with a cuff and laces, a rounded toe, a heel)."""
    for x in (-0.22, -0.1):
        G.stroke(d, G.hose_outline([(x, 0.44), (x, 0.36)], 0.025), M["sky_sh"], 0.0, cyclic=True)
    toe = arc(0.13, -0.02, 0.1, -math.pi / 2, math.pi / 2, 10)
    boot = [(-0.3, -0.12), (0.13, -0.12)] + toe[1:] + [(-0.02, 0.08), (-0.06, 0.3), (-0.3, 0.3)]
    G.stroke(d, boot, M["brown_i"], O, cyclic=True)
    G.stroke(d, [(-0.3, 0.22), (-0.06, 0.22), (-0.06, 0.32), (-0.3, 0.32)], M["mustard_i"], I, cyclic=True)              # the cuff
    for k in range(3):                                                                                                  # laces
        z = 0.16 - 0.06 * k
        G.stroke(d, G.hose_outline([(-0.09 + 0.01 * k, z), (-0.01 + 0.025 * k, z - 0.03)], 0.02), M["off"], 0.0, cyclic=True)
    G.stroke(d, [(-0.3, -0.12), (0.18, -0.12), (0.2, -0.16), (-0.3, -0.16)], M["brown_dp_i"], I, cyclic=True)           # the sole
    G.stroke(d, [(-0.3, -0.16), (-0.16, -0.16), (-0.17, -0.2), (-0.29, -0.2)], M["brown_dp_i"], I, cyclic=True)        # the heel
    pts = [(-0.24, -0.16)]                                                                                              # the spring
    for k in range(7):
        pts.append((0.16 if k % 2 == 0 else -0.24, -0.2 - 0.03 * k))
    G.stroke(d, G.hose_outline(pts, 0.04), M["sky_i"], I, cyclic=True)
    if lv >= 2:                                                                                                          # step 2: an airbag
        G.stroke(d, G.lumpy_ellipse(-0.04, -0.4, 0.32, 0.06, n=20, lump=0.06, seed=91), M["mustard_i"], I, cyclic=True)
    else:
        G.stroke(d, [(-0.32, -0.4), (0.24, -0.4), (0.24, -0.43), (-0.32, -0.43)], M["sky_sh_i"], I, cyclic=True)


def m_price(d, M, lv=1):
    """The Waystation's price: a Scrip coin (a star stamped in it) and a green arrow up; one more coin behind a step."""
    for k in range(lv - 1, 0, -1):
        G.stroke(d, circ(-0.1 + 0.05 * k, -0.02 + 0.08 * k, 0.24, 40), M["mustard_sh_i"], O, cyclic=True)
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
    """The rocket's hold: a strapped cargo crate, plank seams, a red stencil band; step 2: a second crate stacked behind."""
    if lv >= 2:
        G.stroke(d, [(-0.02, 0.14), (0.4, 0.14), (0.4, 0.44), (-0.02, 0.44)], M["mustard_dp_i"], O, cyclic=True)
        G.seam(d, [(0.0, 0.3), (0.38, 0.3)], M["ink"])
    G.stroke(d, [(-0.36, -0.32), (0.26, -0.32), (0.26, 0.24), (-0.36, 0.24)], M["mustard_sh_i"], O, cyclic=True)
    G.stroke(d, [(0.12, -0.32), (0.26, -0.32), (0.26, 0.24), (0.12, 0.24)], M["mustard_dp"], 0.0, cyclic=True)
    G.stroke(d, [(-0.36, -0.32), (0.26, -0.32), (0.26, 0.24), (-0.36, 0.24)], M["ink"], O, cyclic=True)
    for z in (-0.13, 0.05):
        G.seam(d, [(-0.34, z), (0.24, z)], M["ink"])
    G.stroke(d, [(-0.36, 0.24), (-0.28, 0.24), (0.26, -0.24), (0.26, -0.32), (0.18, -0.32), (-0.36, 0.16)], M["brown_i"], I, cyclic=True)   # the brace
    G.stroke(d, [(-0.12, -0.32), (-0.04, -0.32), (-0.04, 0.24), (-0.12, 0.24)], M["red_sh_i"], I, cyclic=True)          # the strap
    G.stroke(d, [(-0.15, -0.06), (-0.01, -0.06), (-0.01, 0.02), (-0.15, 0.02)], M["sky_sh_i"], I, cyclic=True)          # its buckle


# ---------------------------------------------------------------- batch 2 (ring 2)
def m_rhythm(d, M, lv=1):
    """Rhythm: an hourglass inside a teal repeat arrow (each stroke on the same face comes quicker)."""
    G.stroke(d, G.hose_outline(arc(-0.04, 0.0, 0.34, math.radians(130), math.radians(385), 30), 0.06), M["teal_i"], I, cyclic=True)
    a = math.radians(385)                                                                                               # the head, along
    ex, ez = -0.04 + 0.34 * math.cos(a), 0.34 * math.sin(a)                                                             # the turn
    tx, tz, nx, nz = -math.sin(a), math.cos(a), math.cos(a), math.sin(a)
    G.stroke(d, [(ex + tx * 0.12, ez + tz * 0.12), (ex + nx * 0.08, ez + nz * 0.08), (ex - nx * 0.08, ez - nz * 0.08)], M["teal_i"], I, cyclic=True)
    glass = [(-0.16, 0.2), (0.08, 0.2), (-0.02, 0.0), (0.08, -0.2), (-0.16, -0.2), (-0.06, 0.0)]
    G.stroke(d, glass, M["off_i"], I, cyclic=True)
    G.stroke(d, [(-0.13, -0.18), (0.05, -0.18), (-0.04, -0.06)], M["brown"], 0.0, cyclic=True)                       # the sand
    G.stroke(d, [(-0.1, 0.14), (0.02, 0.14), (-0.04, 0.06)], M["brown"], 0.0, cyclic=True)
    G.stroke(d, glass, M["ink"], I, cyclic=True)
    for z in (0.2, -0.2):                                                                                               # the frame
        G.stroke(d, [(-0.22, z - 0.03), (0.14, z - 0.03), (0.14, z + 0.03), (-0.22, z + 0.03)], M["mustard_i"], I, cyclic=True)


def m_light(d, M, lv=1):
    """A lighter load: a steel weight with a ring handle, a feather floating above it."""
    G.stroke(d, circ(-0.06, -0.06, 0.07, 20), M["sky_sh_i"], I, cyclic=True)                                          # the ring
    G.stroke(d, circ(-0.06, -0.06, 0.035, 14), M["off_sh"], 0.0, cyclic=True)
    G.stroke(d, [(-0.3, -0.38), (0.18, -0.38), (0.1, -0.1), (-0.22, -0.1)], M["sky_sh_i"], O, cyclic=True)            # the weight
    G.stroke(d, [(0.0, -0.38), (0.18, -0.38), (0.1, -0.1), (0.04, -0.1)], M["sky_dp"], 0.0, cyclic=True)
    G.stroke(d, [(-0.3, -0.38), (0.18, -0.38), (0.1, -0.1), (-0.22, -0.1)], M["ink"], O, cyclic=True)
    R = rot(0.04, 0.22, 0.45)                                                                                          # the feather
    vane = [(-0.28, 0.0)] + [(u, 0.075 * math.sin(math.pi * (u + 0.28) / 0.6)) for u in (-0.2, -0.1, 0.0, 0.1, 0.2, 0.3)] + \
           [(u, -0.06 * math.sin(math.pi * (u + 0.28) / 0.6)) for u in (0.2, 0.1, 0.0, -0.1, -0.2)]
    G.stroke(d, R(vane), M["off_i"], O, cyclic=True)
    G.stroke(d, G.hose_outline(R([(-0.36, 0.0), (0.3, 0.0)]), 0.018), M["brown"], 0.0, cyclic=True)
    for u in (-0.12, 0.02, 0.14):
        G.seam(d, R([(u, 0.0), (u + 0.06, 0.05)]), M["ink"])


def m_jet(d, M, lv=1):
    """The jetpack: two red tanks on a mustard harness band, two nozzles and flames (bigger with the step)."""
    fl = 0.16 + 0.04 * (lv - 1)
    for x in (-0.13, 0.13):
        G.stroke(d, [(x - 0.07, -0.2), (x + 0.07, -0.2), (x, -0.2 - fl)], M["mustard_i"], I, cyclic=True)              # flames
        G.stroke(d, [(x - 0.035, -0.2), (x + 0.035, -0.2), (x, -0.2 - fl * 0.55)], M["off"], 0.0, cyclic=True)
        IT._tank(d, M, x, 0.1, -0.12, 0.36, "red", "red_sh", nozzle="sky_sh")                                         # (its own nozzle)
    G.stroke(d, [(-0.3, 0.06), (0.3, 0.06), (0.3, 0.14), (-0.3, 0.14)], M["mustard_i"], I, cyclic=True)


def m_climb(d, M, lv=1):
    """Climbing: a 40-degree slope, its angle marked, a green arrow running up it."""
    G.stroke(d, [(-0.42, -0.36), (0.4, -0.36), (0.4, 0.33)], M["brown_i"], O, cyclic=True)
    G.stroke(d, [(0.4, -0.36), (0.4, 0.33), (0.26, 0.21), (0.26, -0.36)], M["brown_sh"], 0.0, cyclic=True)
    G.stroke(d, [(-0.42, -0.36), (0.4, -0.36), (0.4, 0.33)], M["ink"], O, cyclic=True)
    G.stroke(d, G.hose_outline(arc(-0.42, -0.36, 0.2, 0.0, math.radians(40), 8), 0.03), M["mustard"], 0.0, cyclic=True)   # the angle
    arrow(d, M, (-0.2 + 0.0, -0.18 + 0.02), (0.18, 0.15), 0.07, "green")


def m_preview(d, M, lv=1):
    """The tier's materials listed: a clipboard, three swatch rows (one more row for the next tier at step 2)."""
    G.stroke(d, [(-0.3, -0.4), (0.26, -0.4), (0.26, 0.36), (-0.3, 0.36)], M["brown_i"], O, cyclic=True)
    G.stroke(d, [(-0.24, -0.34), (0.2, -0.34), (0.2, 0.28), (-0.24, 0.28)], M["off_i"], I, cyclic=True)
    G.stroke(d, [(-0.1, 0.3), (0.06, 0.3), (0.06, 0.4), (-0.1, 0.4)], M["sky_sh_i"], I, cyclic=True)                 # the clip
    rows = ["red_sh", "sky", "mustard"] + (["teal"] if lv >= 2 else [])
    for k, role in enumerate(rows):
        z = 0.16 - 0.14 * k
        G.stroke(d, [(-0.18, z - 0.05), (-0.08, z - 0.05), (-0.08, z + 0.05), (-0.18, z + 0.05)], M[role + "_i"], I, cyclic=True)
        G.stroke(d, G.hose_outline([(-0.02, z), (0.14, z)], 0.025), M["brown_sh"], 0.0, cyclic=True)


def m_heat(d, M, lv=1):
    """Heat and pressure kept off, as insulation (rev 18:0x: a kite shield is battle gear, D-087): the thermal pad's quilted
    panel (B-199's colours: mustard quilt, a red band) standing at the left, a flame on the right bending away from it; a
    second layer behind it at step 2."""
    G.stroke(d, [(-0.02, -0.4), (0.38, -0.4), (0.44, -0.16), (0.46, 0.1), (0.36, -0.04), (0.36, 0.26), (0.25, 0.04), (0.2, 0.2),
                 (0.11, -0.06), (0.0, -0.18)], M["red_i"], I, cyclic=True)                                            # the flame,
    G.stroke(d, [(0.06, -0.4), (0.32, -0.4), (0.37, -0.18), (0.36, 0.02), (0.28, -0.1), (0.24, 0.06), (0.17, -0.12), (0.08, -0.2)],
             M["mustard"], 0.0, cyclic=True)                                                                            # leaning away
    def blanket(dx, dz, fill, shade):                                                   # rev 18:1x: a soft silver blanket, diamond
        x0, x1, z0, z1, r = -0.42 + dx, -0.04 + dx, -0.38 + dz, 0.36 + dz, 0.07         # quilting (a gridded panel by a flame read
        pts = (arc(x1 - r, z1 - r, r, 0.0, math.pi / 2, 4) + arc(x0 + r, z1 - r, r, math.pi / 2, math.pi, 4)    # as a burning door)
               + arc(x0 + r, z0 + r, r, math.pi, 1.5 * math.pi, 4) + arc(x1 - r, z0 + r, r, 1.5 * math.pi, 2 * math.pi, 4))
        G.stroke(d, pts, M[fill + "_i"], O, cyclic=True)
        G.stroke(d, [(x1 - 0.1, z0 + 0.02), (x1 - 0.01, z0 + 0.06), (x1 - 0.01, z1 - 0.06), (x1 - 0.1, z1 - 0.02)], M[shade], 0.0, cyclic=True)
        G.stroke(d, pts, M["ink"], O, cyclic=True)
        return x0, x1, z0, z1
    if lv >= 2:                                                                                                         # a second layer
        blanket(0.06, 0.06, "sky_sh", "sky_dp")
    x0, x1, z0, z1 = blanket(0.0, 0.0, "off", "off_sh")
    xa, xb, za, zb = x0 + 0.03, x1 - 0.03, z0 + 0.05, z1 - 0.05                         # the diamond quilting: soft grey stitch
    xm = (xa + xb) / 2                                                                   # lines both ways, clipped to the blanket
    for s in (1, -1):
        for k in range(-6, 7):
            c = 0.14 * k
            xs = sorted([xm + (za - c) * s, xm + (zb - c) * s])
            lo, hi = max(xa, xs[0]), min(xb, xs[1])
            if hi - lo > 0.04:
                G.stroke(d, G.hose_outline([(lo, c + s * (lo - xm)), (hi, c + s * (hi - xm))], 0.014), M["sky_sh"], 0.0, cyclic=True)
    G.stroke(d, [(x0, -0.03), (x1, -0.03), (x1, 0.05), (x0, 0.05)], M["red_i"], I, cyclic=True)                        # the red band


def m_thrust(d, M, lv=2):
    """A thruster: a flared steel bell (rev 17:5x: a straight one read as a pen nib) under a short teal rocket tail with fins
    (rev 18:0x: without it the bell read as a spinning top); the flame grows with the Mk (2, 3)."""
    fl = 0.14 + 0.06 * (lv - 2)
    zb = -0.2                                                                                                           # the bell's mouth
    G.stroke(d, [(-0.16, zb + 0.02), (0.16, zb + 0.02), (0.0, zb - fl - 0.08)], M["mustard_i"], I, cyclic=True)
    G.stroke(d, [(-0.08, zb + 0.02), (0.08, zb + 0.02), (0.0, zb - fl)], M["red"], 0.0, cyclic=True)
    G.stroke(d, [(-0.04, zb + 0.02), (0.04, zb + 0.02), (0.0, zb - fl * 0.5)], M["off"], 0.0, cyclic=True)
    hw = lambda z: 0.07 + 0.19 * ((0.08 - z) / 0.28) ** 1.8  # noqa: E731
    zs = [0.08 - 0.28 * i / 10 for i in range(11)]
    bell = [(-hw(z), z) for z in zs] + [(hw(z), z) for z in reversed(zs)]
    G.stroke(d, bell, M["sky_sh_i"], O, cyclic=True)
    G.stroke(d, [(0.02, z) for z in zs] + [(hw(z), z) for z in reversed(zs)], M["sky_dp"], 0.0, cyclic=True)
    G.stroke(d, bell, M["ink"], O, cyclic=True)
    for z in (-0.02, -0.11):                                                                                            # bands round it
        G.seam(d, [(-hw(z) + 0.01, z), (hw(z) - 0.01, z)], M["ink"])
    if lv >= 3:                                                                                                          # Mk3: side vanes
        for s in (-1, 1):
            G.stroke(d, [(s * 0.15, 0.02), (s * 0.32, -0.1), (s * 0.32, -0.2), (s * 0.19, -0.14)], M["red_sh_i"], I, cyclic=True)
    for s in (-1, 1):                                                                                                    # the tail's fins
        G.stroke(d, [(s * 0.13, 0.3), (s * 0.3, 0.12), (s * 0.3, 0.06), (s * 0.13, 0.14)], M["mustard_i"], I, cyclic=True)
    tail = [(-0.14, 0.08), (0.14, 0.08), (0.14, 0.3)] + arc(0.0, 0.3, 0.14, 0.0, math.pi, 12)[1:] + [(-0.14, 0.3)]
    G.stroke(d, tail, M["teal_i"], O, cyclic=True)                                                                     # the rocket tail
    G.stroke(d, [(0.04, 0.08), (0.14, 0.08), (0.14, 0.3)] + arc(0.0, 0.3, 0.14, 0.0, 0.8, 5)[1:] + [(0.06, 0.4)], M["teal_sh"], 0.0, cyclic=True)
    G.stroke(d, tail, M["ink"], O, cyclic=True)
    G.stroke(d, [(-0.14, 0.12), (0.14, 0.12), (0.14, 0.18), (-0.14, 0.18)], M["off_i"], I, cyclic=True)              # its cream band


# ---------------------------------------------------------------- batch 3 (ring 3)
def m_heatsink(d, M, lv=1):
    """No Beam cool-down: a finned steel heat sink clamped on the teal emitter, cool teal waves rising off it."""
    G.stroke(d, [(-0.4, -0.3), (-0.04, -0.3), (-0.04, -0.06), (-0.4, -0.06)], M["teal_sh_i"], O, cyclic=True)        # the emitter
    G.stroke(d, [(-0.04, -0.27), (0.06, -0.24), (0.06, -0.12), (-0.04, -0.09)], M["mustard_i"], I, cyclic=True)
    G.stroke(d, [(-0.36, -0.06), (-0.08, -0.06), (-0.08, 0.02), (-0.36, 0.02)], M["sky_sh_i"], I, cyclic=True)       # the clamp
    for k in range(5):                                                                                                  # the fins
        x = -0.36 + 0.065 * k
        G.stroke(d, [(x, 0.02), (x + 0.035, 0.02), (x + 0.035, 0.26), (x, 0.26)], M["sky_i"], I, cyclic=True)
    for k, x in enumerate((-0.3, -0.18, -0.06)):                                                                        # cool waves
        G.stroke(d, G.hose_outline([(x + 0.03 * math.sin(i * 1.6), 0.3 + 0.035 * i) for i in range(4)], 0.03), M["teal"], 0.0, cyclic=True)
    G.stroke(d, [(0.12, -0.2), (0.4, -0.2), (0.4, -0.14), (0.12, -0.14)], M["teal_i"], I, cyclic=True)                 # a steady beam


def m_magnet(d, M, lv=1):
    """Drops fly into the pack: a red horseshoe magnet (offwhite poles) drawing two ore chunks in, motion lines behind them."""
    G.stroke(d, G.hose_outline(arc(-0.12, 0.0, 0.2, math.radians(90), math.radians(270), 16), 0.14), M["red_i"], O, cyclic=True)
    for z in (0.2, -0.2):
        G.stroke(d, [(-0.12, z - 0.07), (0.04, z - 0.07), (0.04, z + 0.07), (-0.12, z + 0.07)], M["off_i"], O, cyclic=True)   # the poles
    for (x, z, s) in ((0.2, 0.12, 81), (0.25, -0.14, 82)):                              # (pulled in: the lines ran past the edge)
        IT.faceted(d, M, IT.lump(x, z, 0.07, 0.06, s, n=7), "brown_sh", "brown", "brown_dp", x, z)
        for dz in (-0.03, 0.03):
            G.stroke(d, G.hose_outline([(x + 0.1, z + dz), (x + 0.18, z + dz)], 0.02), M["sky_sh"], 0.0, cyclic=True)


def m_sorter(d, M, lv=1):
    """The pack sorts itself: a gem dropping in (green arrow), a plain pebble thrown out (red arrow)."""
    G.stroke(d, [(-0.36, -0.38), (0.12, -0.38), (0.16, -0.06), (-0.4, -0.06)], M["brown_i"], O, cyclic=True)           # the bin
    G.stroke(d, [(-0.4, -0.06), (0.16, -0.06), (0.14, -0.12), (-0.38, -0.12)], M["brown_dp"], 0.0, cyclic=True)
    IT.faceted(d, M, [(-0.12, 0.42), (-0.02, 0.32), (-0.12, 0.2), (-0.22, 0.32)], "teal", "off", "teal_sh", -0.12, 0.31)   # the gem
    arrow(d, M, (-0.12, 0.17), (-0.12, -0.02), 0.06, "green")
    G.stroke(d, IT.lump(0.3, 0.08, 0.08, 0.065, 83, n=7), M["sky_sh_i"], O, cyclic=True)                             # the pebble
    arrow(d, M, (0.12, -0.1), (0.38, -0.1), 0.055, "red")


def m_rare(d, M, lv=1):
    """Rare finds glint through the ground: a gem in the soil, its glint rays crossing the surface."""
    G.stroke(d, [(-0.42, -0.4), (0.42, -0.4), (0.42, 0.06)] + [(x, 0.06 + 0.012 * math.sin(25 * x)) for x in (0.3, 0.1, -0.1, -0.3, -0.42)],
             M["brown_i"], O, cyclic=True)
    G.stroke(d, [(-0.42, -0.4), (0.42, -0.4), (0.42, -0.2), (-0.42, -0.2)], M["brown_sh"], 0.0, cyclic=True)
    G.seam(d, [(-0.42, -0.2), (0.42, -0.2)], M["ink"])
    G.stroke(d, [(-0.42, 0.04)] + [(x, 0.06 + 0.012 * math.sin(25 * x)) for x in (-0.3, -0.1, 0.1, 0.3)] + [(0.42, 0.04), (0.42, 0.11)]
             + [(x + 0.05 * (k % 2), 0.11 + 0.04 * (k % 2)) for k, x in enumerate((0.36, 0.28, 0.2, 0.12, 0.04, -0.04, -0.12, -0.2, -0.28, -0.36))]
             + [(-0.42, 0.11)], M["green_i"], I, cyclic=True)                                  # rev 18:1x: grass on top (it read as a chest)
    IT.faceted(d, M, [(0.0, -0.06), (0.1, -0.16), (0.0, -0.3), (-0.1, -0.16)], "mustard", "off", "mustard_sh", 0.0, -0.17)
    for a in (55, 75, 90, 105, 125):                                                                                    # glint rays
        t = math.radians(a)
        G.stroke(d, G.hose_outline([(0.15 * math.cos(t), -0.06 + 0.15 * math.sin(t)), (0.4 * math.cos(t), -0.06 + 0.4 * math.sin(t))],
                                   0.035 if a == 90 else 0.025), M["mustard_i"], I * 0.8, cyclic=True)


def m_skip(d, M, lv=1):
    """The Skip Drive: a dashed hop from a small teal world to a ringed one, its arrowhead landing (rev 18:1x: a teal oval in a
    brass ring read as an eye); one more dash-hop a step."""
    G.stroke(d, circ(-0.28, -0.24, 0.11, 28), M["teal_i"], O, cyclic=True)                                           # from
    G.stroke(d, arc(-0.28, -0.24, 0.11, -0.6, 1.2, 8) + arc(-0.28, -0.24, 0.07, 1.2, -0.6, 8), M["teal_sh"], 0.0, cyclic=True)
    G.stroke(d, circ(-0.28, -0.24, 0.11, 28), M["ink"], O, cyclic=True)
    G.stroke(d, circ(0.22, -0.16, 0.15, 32), M["mustard_i"], O, cyclic=True)                                         # to: a ringed world
    ring = [(0.22 + 0.21 * math.cos(t), -0.18 + 0.06 * math.sin(t)) for t in [math.pi * (1.02 + 0.96 * i / 13) for i in range(14)]]
    G.stroke(d, G.hose_outline(ring, 0.035), M["red_sh_i"], I, cyclic=True)
    hop = arc(-0.02, -0.08, 0.27, math.radians(150), math.radians(45), 24)                                             # the dashed hop
    for i in range(0, 20, 4):
        G.stroke(d, G.hose_outline(hop[i:i + 3], 0.04), M["off_i"], I * 0.8, cyclic=True)
    t = math.radians(45)
    ex, ez = hop[-1]
    tx, tz, nx, nz = math.sin(t), -math.cos(t), math.cos(t), math.sin(t)                                                # travel: clockwise
    G.stroke(d, [(ex + tx * 0.09, ez + tz * 0.09), (ex + nx * 0.06, ez + nz * 0.06), (ex - nx * 0.06, ez - nz * 0.06)], M["off_i"], I, cyclic=True)


MOTIF = {"dig_power": m_beam, "dig_brush": m_brush, "haul_pack": m_pack, "haul_dirt": m_dirt, "asc_grapple": m_grapple,
         "asc_ladder": m_ladder, "sur_scan": m_scan, "sur_depth": m_depth, "end_air": m_air, "end_fall": m_fall,
         "voy_price": m_price, "voy_hold": m_hold,
         "dig_rhythm": m_rhythm, "haul_light": m_light, "asc_jet": m_jet, "asc_climb": m_climb, "sur_preview": m_preview,
         "end_heat": m_heat, "voy_thrust": m_thrust,
         "dig_heatsink": m_heatsink, "haul_magnet": m_magnet, "haul_sorter": m_sorter, "sur_rare": m_rare, "voy_skip": m_skip}


def draw_node(d, M, nid):
    head, _, tail = nid.rpartition("_")
    lv = level_of(nid)
    MOTIF[head if tail.isdigit() else nid](d, M, lv[0] if lv else 1)   # rev 17:2x: no level meter (unreadable at 40 px; the
                                                                        # ring shows the step); a chain's steps vary in the motif


BATCHES = {1: ["dig_power_1", "dig_brush_1", "haul_pack_1", "haul_dirt_1", "asc_grapple_1", "asc_ladder_1", "sur_scan_1", "sur_depth_1",
               "end_air_1", "end_fall_1", "voy_price_1", "voy_hold_1"],
           2: ["dig_power_2", "dig_rhythm_1", "haul_pack_2", "haul_light_1", "asc_jet_1", "asc_climb_1", "sur_scan_2", "sur_preview_1",
               "end_air_2", "end_heat_1", "voy_thrust_2", "voy_price_2"],
           3: ["dig_power_3", "dig_heatsink", "dig_brush_2", "haul_magnet_1", "haul_sorter", "haul_pack_3", "asc_jet_2", "asc_grapple_2",
               "asc_ladder_2", "sur_scan_3", "sur_rare", "sur_preview_2", "end_air_3", "end_heat_2", "end_fall_2", "voy_hold_2", "voy_skip_1",
               "voy_price_3", "end_heat_1", "voy_thrust_2"]}                       # + batch 2's two redraws (LEAD 18:0x)
EXPORT_BATCHES = (1,)                                                                           # only LEAD-accepted batches export (1: 17:3x)


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
    TW, PER = 214, 10                                                                  # 10 icons a row (a 20-icon row was unreadable)
    W = 8 + min(len(names), PER) * TW
    blocks = []
    for c0 in range(0, len(names), PER):
        r1 = np.empty((156, W, 3), np.float32)
        r1[:] = paper
        review._label(r1, f"B-204 node icons, batch {batch} (1x, 128 px)", 8, 4, scale=1)
        r2 = np.empty((150, W, 3), np.float32)
        r2[:] = paper
        review._label(r2, "at 40 px in the chart's frames: locked (0.4) / available / bought; below, at 32 px", 8, 4, scale=1)
        for i, n in enumerate(names[c0:c0 + PER]):
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
        blocks += [r1, r2]
    lines = []
    for n in names:
        p, hit = checks(imgs[n])
        lines.append(f"{KEY.format(n)}: palette {hit * 100:.1f}%, problems: {'; '.join(p) or 'none'}")
    foot = np.empty((30 + 16 * ((len(lines) + 1) // 2), W, 3), np.float32)
    foot[:] = paper
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6 + (i % 2) * (W // 2), 6 + 16 * (i // 2), scale=1)
    img = np.vstack(blocks + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_icons_nodes_v3.py <review png> [batch]
    preview(sys.argv[1], batch=int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    fakegp.restore()
