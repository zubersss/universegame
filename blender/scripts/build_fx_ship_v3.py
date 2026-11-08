"""B-171 (D-158 (4), the owner's 0.4.7 flight playtest): the flight effects in the cartoon style (Bible §9 v4: thin
detailed ink, 1930s rubber-hose, no faces), drawn in the Earth palette for UNITY's U-150. One source, four GP objects
(one collection each), one drawing per frame, clip markers; render.py's v3 sheet path exports each key.

  fx/ship/vapor_cone      336x252, form 10 (once)   the sound-barrier cloud: a cream skirt of puffy, ink-lined vapour
                          round the hull's waist, flaring down to a scalloped rim, then tearing away downward in puffs.
                          Pivot (0.5, 0.85) = the ship's centre of mass (ship-local 0, 6.2 m: UNITY's tilt pivot); drawn
                          IN FRONT of the hull (the nose, the porthole and the bell stay clear above and below it).
  fx/ship/shock_ring      504x248, burst 8 (once)   a cream flash at the waist, then a cream band between two ink rims
                          (a ring round the ship seen from a little below: ry = 0.32 rx) with cartoon boom spikes,
                          expanding to ~7.5 m wide and thinning to ink dashes. Pivot (0.5, 0.5) = the centre of mass;
                          drawn BEHIND the hull.
  fx/ship/speed_lines     128x360, streak 4 (loop)  frame-edge motion streaks for the climb (vertical: the world streams
                          down past an upward ship), ink on transparent, dense at the screen edge (x = 0) and thinning
                          inward; 3 x 360 px = one 1080 px edge, nothing touches the frame edge so the tiles stack
                          seamlessly (tile i may show frame (f + i) % 4). Drawn for the LEFT edge; flip x for the right.
                          Pivot (0.0, 0.5): the screen edge, mid-tile.
  ships/pilgrim/puff_boost 192x288, puff 8 (loop; 4 columns: the sheet 780x580)   the hard-acceleration flame (LEAD 02:2x:
                          it must read at 0.56x / 0.375x): a nozzle-wide flame tongue (red edge, gold core, a cream hot
                          spot, ink outline) ~2x the cruise puff's length, the cruise puff's round clouds trailing it.
                          Same socket (tail_exhaust), same pivot (0.5, 0.96) and the same clip name as the cruise puff.

  python -I build_fx_ship_v3.py <preview dir> [--sheet | --art]  lock-free (meridian.fakegp; exact stroke ids, ss 4): the four sheets
                                                   + their ten-box reviews (_preview) + review_b171_flight_fx_preview.png
                                                   (LEAD's acceptance sheet: the Pilgrim at 1x on the Earth sky with the
                                                   cruise vs boost puff, the cone and the ring at the hull, the lines along
                                                   both frame edges)
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp  # noqa: E402

try:                                    # inside Blender (the export build): the real gp_draw
    import bpy
    if not hasattr(bpy, "data"):
        raise ImportError
    import gp_draw as G
except ImportError:
    bpy = None
    G = fakegp.install()
import build_pilgrim_v3 as BP  # noqa: E402  (the hull profile, the cruise puff's look)

P = G.PALETTES["earth"]
O, I = G.OUTER, G.INNER
SOURCE = os.path.join(os.path.dirname(HERE), "sources", "fx", "ship_fx_v3.blend")
ZC = BP.UP_ZC                       # 6.2 m: the centre of mass, the cone's and the ring's pivot
TAU = 2 * math.pi


def materials(gp):
    off = P["offwhite"]
    return {
        "vapor": G.mat(gp, "fx_vapor", fill=off),
        "vapor_flat": G.mat(gp, "fx_vapor_flat", fill=off, ink=False),
        "vapor_sh": G.mat(gp, "fx_vapor_shadow", fill=G.shadow_of(off), ink=False),
        "vapor_dp": G.mat(gp, "fx_vapor_deep", fill=G.deep_of(off), ink=False),
        "ink": G.mat(gp, "fx_ink", fill=None, ink=True),
        "puff": G.mat(gp, "puff_offwhite", fill=off),
        "puff_hot": G.mat(gp, "puff_mustard", fill=P["mustard"]),
        "core": G.mat(gp, "fx_core_cream", fill=off, ink=False),
        "flame": G.mat(gp, "fx_flame_red", fill=P["red"]),
        "flame_mid": G.mat(gp, "fx_flame_mustard", fill=P["mustard"], ink=False),
    }


def hull_r(z_rel):
    """The upright hull's radius at a height relative to the centre of mass."""
    return BP.up_radius(ZC + z_rel)


# ---------------------------------------------------------------- fx/ship/vapor_cone (pivot = centre of mass)

Z_LEAD = 0.35                       # the cone's leading edge: just above the waist (the hull's widest is at 6.5 m)
CONE = [  # (length m, rim radius m, gap m (detached from the hull), rim puff radius, body?, drift m, spread)
    dict(L=0.70, r1=1.78, gap=0.00, pr=0.15, body=True, drift=0.0, spread=1.0),
    dict(L=1.50, r1=1.98, gap=0.00, pr=0.20, body=True, drift=0.0, spread=1.0),
    dict(L=2.20, r1=2.13, gap=0.00, pr=0.24, body=True, drift=0.0, spread=1.0),
    dict(L=2.50, r1=2.20, gap=0.00, pr=0.26, body=True, drift=0.0, spread=1.0),
    dict(L=2.50, r1=2.22, gap=0.00, pr=0.27, body=True, drift=0.0, spread=1.0),
    dict(L=2.25, r1=2.20, gap=0.40, pr=0.30, body=True, drift=0.10, spread=1.02),
    dict(L=1.75, r1=2.15, gap=0.85, pr=0.32, body=True, drift=0.20, spread=1.05),
    dict(L=0.00, r1=2.15, gap=1.00, pr=0.30, body=False, drift=0.25, spread=1.04),
    dict(L=0.00, r1=2.15, gap=1.00, pr=0.21, body=False, drift=0.40, spread=1.06),
    dict(L=0.00, r1=2.15, gap=1.00, pr=0.12, body=False, drift=0.52, spread=1.07),
]
CONE_RIM = -2.15                    # the full cone's rim height (Z_LEAD - 2.5)
B_RIM = 0.28                        # the rim's ellipse seen from a little below
B_TOP = 0.17                        # the leading ring's near arc


def _side(z_top, r_top, z_rim, r1, n=30):
    """The cone's left side from the leading ring down to the rim (a gentle outward bow)."""
    return G.bezier((-r_top, z_top), (-r_top - 0.12, z_top - (z_top - z_rim) * 0.35),
                    (-r1 + 0.05, z_rim + (z_top - z_rim) * 0.30), (-r1, z_rim), n=n)


def _scallop(path, amp, bumps, phase=0.0, outward=1.0):
    """Puff bumps along a polyline: each point pushed out along its normal by amp * |sin| (zero at both ends)."""
    out, n = [], len(path)
    for i, (x, z) in enumerate(path):
        a, b = path[max(i - 1, 0)], path[min(i + 1, n - 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz) or 1.0
        nx, nz = dz / L * outward, -dx / L * outward
        s = i / (n - 1)
        k = amp * abs(math.sin(math.pi * (bumps * s + phase))) ** 0.6 * math.sin(math.pi * s) ** 0.3
        out.append((x + nx * k, z + nz * k))
    return out


def _cone_outline(z_top, r_top, z_rim, r1, f=0):
    """Puffy silhouette: scalloped sides (independent bumps left and right), the rim's lower arc (its puffs drawn over
    it), the leading ring's near arc lightly lumpy where it wraps the hull."""
    side = _side(z_top, r_top, z_rim, r1)
    bumps = max(2, int(round((z_top - z_rim) / 0.55)))
    left = _scallop(side, 0.13, bumps, phase=0.08 * f)
    right = [(-x, z) for x, z in _scallop(side, 0.13, bumps, phase=0.5 + 0.06 * f)][::-1]
    bottom = [(r1 * math.cos(t), z_rim + B_RIM * math.sin(t)) for t in [math.pi + math.pi * i / 20 for i in range(1, 20)]]
    top = [(r_top * math.cos(t), z_top - B_TOP * math.sin(t) + 0.035 * abs(math.sin(5 * t + f))) for t in [math.pi * i / 16 for i in range(1, 16)]]
    return left, left + bottom + right + top


def draw_vapor_cone(d, M, f):
    c = CONE[f]
    rnd = random.Random(1710 + f)
    z_top = Z_LEAD - c["gap"]
    z_rim = (Z_LEAD - c["L"] - c["gap"]) if c["body"] else CONE_RIM - c["drift"]
    r_top = hull_r(z_top) + 0.10
    if c["body"]:
        r1 = c["r1"]
        left, out = _cone_outline(z_top, r_top, z_rim, r1, f)
        G.stroke(d, out, M["vapor_flat"], 0.0, cyclic=True)
        # the shadow side (light from the upper right): a band inside the scalloped left edge, deeper under the rim
        inner = [(x + 0.42 + 0.10 * (z - z_rim) / max(z_top - z_rim, 0.1), z) for x, z in left[::-1]]
        G.stroke(d, left + [(-r1 * 0.70, z_rim - B_RIM * 0.70)] + inner, M["vapor_sh"], 0.0, cyclic=True)
        G.stroke(d, [(-r1, z_rim), (-r1 * 0.97, z_rim + 0.32), (-r1 * 0.55, z_rim - B_RIM * 0.55),
                     (-r1 * 0.80, z_rim - B_RIM * 0.80)], M["vapor_dp"], 0.0, cyclic=True)
        G.stroke(d, out, M["ink"], O, cyclic=True)
        # interior: overlapping puff lobes (the lower edge of each lobe as a short ink smile, rows staggered, bigger
        # toward the rim), a hatch in the shadow, specks
        span = z_top - z_rim
        rows = [0.30, 0.56, 0.80] if span >= 1.2 else [0.55]
        for ri, fr in enumerate(rows):
            zz = z_top - span * fr - B_TOP * 0.4
            rr = r_top + (r1 - r_top) * (fr ** 0.8)
            a = 0.20 + 0.10 * fr                       # lobe half width (m)
            n = max(2, int(rr * 1.6 / (2 * a + 0.12)))
            for k in range(n):
                xc = -rr * 0.78 + (2 * rr * 0.78) * (k + 0.5 * (ri % 2) + 0.25) / (n + 0.5) + 0.05 * (rnd.random() - 0.5)
                if abs(xc) + a > rr * 0.92:
                    continue
                zl = zz - B_RIM * 0.5 * (1 - (xc / rr) ** 2) + 0.04 * (rnd.random() - 0.5)
                G.seam(d, G.bezier((xc - a, zl + a * 0.18), (xc - a * 0.3, zl - a * 0.42), (xc + a * 0.4, zl - a * 0.36),
                                   (xc + a, zl + a * 0.12), n=8), M["ink"])
        if span >= 1.2:
            G.hatch(d, -r1 * 0.80, z_rim + span * 0.40, M["ink"], n=3, length=0.28, spacing=0.10, angle_deg=62, seed=f + 4)
            G.specks(d, [(r1 * 0.30, z_rim + span * 0.25), (r1 * 0.48, z_rim + span * 0.38), (r1 * 0.12, z_rim + span * 0.62)], M["ink"])
    else:
        r1 = c["r1"] * c["spread"]
    # the rim's puffs (on the body; once torn away, drifting down and out on their own)
    n = 9 if c["body"] else (7 if f == 7 else (6 if f == 8 else 5))
    for k in range(n):
        t = math.pi + math.pi * (k + 0.5) / n
        x = r1 * math.cos(t)
        z = z_rim + B_RIM * math.sin(t)
        if not c["body"]:
            z -= 0.10 * abs(math.cos(t)) * (f - 6) + 0.04 * rnd.random()
        pr = c["pr"] * (0.82 + 0.36 * rnd.random()) * (1.12 if abs(math.cos(t)) > 0.8 else 1.0)
        lim = 2.52 - pr * 1.1
        x = max(-lim, min(lim, x))
        pts = G.lumpy_ellipse(x, z, pr, pr * 0.86, n=22, lump=0.08, seed=17 * k + f)
        G.stroke(d, pts, M["vapor"], O, cyclic=True)
        if pr > 0.2:
            G.seam(d, G.bezier((x - pr * 0.45, z - pr * 0.2), (x, z - pr * 0.5), (x + pr * 0.4, z - pr * 0.25), n=6), M["ink"])
    if not c["body"]:               # the body breaking up: big puffs where it was, fewer and smaller each frame
        cnt = {7: 4, 8: 3, 9: 2}[f]
        for k in range(cnt):
            x = (-0.85 + 1.7 * (k + 0.5) / cnt) * r1 * 0.62 + 0.06 * (rnd.random() - 0.5)
            z = CONE_RIM + 1.05 - 0.30 * (f - 7) + 0.16 * (k % 2)
            pr = c["pr"] * (1.45 if f == 7 else 1.25) * (0.9 + 0.2 * rnd.random())
            G.stroke(d, G.lumpy_ellipse(x, z, pr * 1.15, pr * 0.85, n=20, lump=0.08, seed=91 + 7 * k + f), M["vapor"], O, cyclic=True)
            G.stroke(d, G.lumpy_ellipse(x - pr * 0.45, z - pr * 0.05, pr * 0.42, pr * 0.55, n=12, lump=0.05, seed=5 + k + f),
                     M["vapor_sh"], 0.0, cyclic=True)
            G.seam(d, G.bezier((x - pr * 0.5, z - pr * 0.2), (x, z - pr * 0.55), (x + pr * 0.45, z - pr * 0.25), n=6), M["ink"])


# ---------------------------------------------------------------- fx/ship/shock_ring (pivot = centre of mass)

RING = [  # rx m, band width m, spike length m, kept arc fraction (1 = whole ring)
    dict(rx=1.75, w=0.34, spike=0.60, keep=1.0, flash=True),
    dict(rx=2.10, w=0.30, spike=0.55, keep=1.0, flash=False),
    dict(rx=2.50, w=0.27, spike=0.48, keep=1.0, flash=False),
    dict(rx=2.85, w=0.23, spike=0.38, keep=1.0, flash=False),
    dict(rx=3.15, w=0.19, spike=0.26, keep=0.86, flash=False),
    dict(rx=3.40, w=0.14, spike=0.14, keep=0.66, flash=False),
    dict(rx=3.60, w=0.00, spike=0.00, keep=0.46, flash=False),
    dict(rx=3.75, w=0.00, spike=0.00, keep=0.26, flash=False),
]
RY = 0.32                           # ry / rx: a ring round the hull seen from a little below
SPIKE_ANGLES = [0.0, 0.62, 1.25, 1.95, 2.55, 3.14, 3.75, 4.40, 5.02, 5.70]


def _ell(rx, ry, a0, a1, n):
    return [(rx * math.cos(t), ry * math.sin(t)) for t in [a0 + (a1 - a0) * i / (n - 1) for i in range(n)]]


def draw_shock_ring(d, M, f):
    c = RING[f]
    rnd = random.Random(1720 + f)
    rx = c["rx"]
    ry = rx * RY
    if c["flash"]:                  # the boom flash at the waist: a squashed cream star
        star = []
        for k in range(20):
            a = TAU * k / 20 + 0.1
            r = (1.95 if k % 2 == 0 else 1.25) * (0.92 + 0.16 * rnd.random())
            star.append((r * math.cos(a), r * 0.52 * math.sin(a)))
        G.stroke(d, star, M["vapor"], O, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(0.0, 0.0, 1.2, 0.52, n=30, lump=0.05, seed=f + 3), M["core"], 0.0, cyclic=True)
        for k in range(6):
            a = TAU * k / 6 + 0.35
            G.seam(d, G.bowed_line((1.3 * math.cos(a), 0.6 * math.sin(a)), (1.7 * math.cos(a), 0.86 * math.sin(a)), bow=0.08, n=4), M["ink"])
    if c["w"] > 0:
        # the band: fill-only annulus (outer arc one way, inner arc back), then both rims in ink, spikes on top
        if c["keep"] >= 1.0:
            arcs = [(0.0, TAU)]
        else:
            arcs, gaps = [], 5
            for k in range(gaps):
                a = TAU * k / gaps + 0.3
                span = TAU / gaps * c["keep"]
                arcs.append((a, a + span))
        ri_x, ri_y = rx - c["w"], ry - c["w"] * 0.55
        for a0, a1 in arcs:
            n = max(6, int(48 * (a1 - a0) / TAU))
            outer = _ell(rx, ry, a0, a1, n)
            inner = _ell(ri_x, ri_y, a1, a0, n)
            G.stroke(d, outer + inner, M["vapor_flat"], 0.0, cyclic=True)
            G.stroke(d, outer, M["ink"], O, cyclic=(c["keep"] >= 1.0))
            G.stroke(d, inner[::-1], M["ink"], O, cyclic=(c["keep"] >= 1.0))
            if c["keep"] < 1.0:     # close the broken ends of each arc
                G.stroke(d, [outer[0], inner[-1]], M["ink"], O)
                G.stroke(d, [outer[-1], inner[0]], M["ink"], O)
        # shading on the band's lower-left (the underside seen from below), a few speed ticks across the band
        G.stroke(d, _ell(rx - c["w"] * 0.15, ry - c["w"] * 0.1, math.pi * 1.05, math.pi * 1.45, 10) +
                 _ell(ri_x + c["w"] * 0.2, ri_y + c["w"] * 0.1, math.pi * 1.45, math.pi * 1.05, 10), M["vapor_sh"], 0.0, cyclic=True)
        for k in range(7):
            t = TAU * (k + 0.4 * rnd.random()) / 7
            if c["keep"] < 1.0 and not any(a0 < t % TAU < a1 or a0 < t % TAU + TAU < a1 for a0, a1 in arcs):
                continue
            G.seam(d, [((rx - c["w"] * 0.25) * math.cos(t), (ry - c["w"] * 0.15) * math.sin(t)),
                       ((ri_x + c["w"] * 0.25) * math.cos(t + 0.05), (ri_y + c["w"] * 0.15) * math.sin(t + 0.05))], M["ink"])
    else:
        # the fade: ink dashes on the ring's line, fewer each frame
        for k in range(9):
            a = TAU * k / 9 + 0.2 + 0.1 * rnd.random()
            span = TAU / 9 * c["keep"]
            G.stroke(d, _ell(rx, ry, a, a + span, 8), M["ink"], O if f == 6 else I)
            if f == 6:
                G.stroke(d, _ell(rx - 0.12, ry - 0.06, a + span * 0.2, a + span * 0.8, 6), M["ink"], I)
    if c["spike"] > 0:              # the boom spikes: cream wedges with ink, radiating from the outer rim
        for k, a in enumerate(SPIKE_ANGLES):
            a += 0.08 * math.sin(3 * k + f)
            L = c["spike"] * (0.8 + 0.4 * ((k * 37) % 7) / 6)
            bx, bz = rx * math.cos(a), ry * math.sin(a)
            ux, uz = math.cos(a), math.sin(a) * 0.75
            nrm = math.hypot(ux, uz)
            ux, uz = ux / nrm, uz / nrm
            px, pz = -uz, ux
            hw = 0.10 + 0.03 * (k % 2)
            wedge = [(bx + px * hw, bz + pz * hw), (bx + ux * L, bz + uz * L), (bx - px * hw, bz - pz * hw)]
            G.stroke(d, wedge, M["vapor"], O, cyclic=True)


# ---------------------------------------------------------------- fx/ship/speed_lines (pivot = the screen edge, mid-tile)

LINE_W, LINE_H = 2.0, 360 / 64     # metres at 64 ppu: 128 x 360 px (3 tiles = one 1080 px edge; 270 is not a BC7 multiple of 4)
LANES = [  # x m from the screen edge, streak length m, weight, phase, a second short dash?
    (0.07, 2.20, "o", 0, True), (0.14, 1.70, "o", 2, False), (0.23, 1.95, "o", 1, True), (0.33, 1.40, "o", 3, False),
    (0.44, 1.60, "o", 2, True), (0.57, 1.10, "i", 0, False), (0.72, 1.30, "i", 3, True), (0.90, 0.90, "i", 1, False),
    (1.10, 1.00, "i", 2, False), (1.35, 0.70, "i", 0, True), (1.62, 0.55, "i", 3, False),
]


def draw_speed_lines(d, M, f):
    top, bot = LINE_H / 2 - 0.08, -LINE_H / 2 + 0.08
    for i, (x, L, wt, ph, dash) in enumerate(LANES):
        k = (f + ph) % 4
        step = (top - bot - L) / 3.0
        z0 = top - k * step
        rad = O if wt == "o" else I
        xx = x + 0.015 * math.sin(i * 1.7 + f)
        G.stroke(d, G.bowed_line((xx, z0), (xx + 0.01, z0 - L), bow=0.006, n=8), M["ink"], rad)
        if dash:                    # a short dash trailing the streak (wraps to the top half of the lane)
            dl = 0.28 + 0.05 * (i % 3)
            dz = z0 - L - 0.22
            if dz - dl < bot:
                dz = top - (bot + 0.22 - (z0 - L)) % (top - bot - dl)
                dz = min(dz, top)
            if dz - dl >= bot and not (z0 >= dz - dl and z0 - L <= dz):
                G.stroke(d, [(xx + 0.004, dz), (xx + 0.008, dz - dl)], M["ink"], I)


# ---------------------------------------------------------------- ships/pilgrim/puff_boost (pivot = the bell, as the cruise puff)

BOOST_LEN = 3.05                    # the flame tongue's length (m): ~2x the cruise puff's ~1.55 m (LEAD 02:2x)
BOOST_HW = 0.86                     # its half width at the nozzle: the bell's mouth is 1.9 m wide


def _flame(hw, length, f, z0=0.05, wave=0.05, sway=0.10):
    """A candle-flame tongue hanging from the nozzle: full width at z0, a slight bulge, flicker waves running down the
    flanks (on twos), a pointed tip that sways. -> closed polygon (left flank down, right flank up)."""
    n = 24
    left, right = [], []
    for i in range(n + 1):
        s = i / n
        w = hw * (1.0 + 0.12 * math.sin(math.pi * min(s * 2.4, 1.0))) * (1 - s) ** 0.8
        ripple = wave * math.sin(TAU * (2.4 * s - f / 4.0)) * 4 * s * (1 - s)
        xc = sway * math.sin(TAU * f / 8 * 2 + 0.6) * s ** 2
        z = z0 - length * s
        left.append((xc - w - ripple, z))
        right.append((xc + w + ripple * 0.7, z))
    return left + right[::-1][1:]


def draw_puff_boost(d, M, f, n=8):
    """The hard-acceleration flame (LEAD 02:2x): a nozzle-wide flame tongue reaching ~2x the cruise puff's length - red edge,
    gold core, a small cream hot spot at the nozzle, ink outline, flicker on twos - with the cruise puff's round clouds
    trailing it, born at its flanks and drifting down past the tip."""
    L = BOOST_LEN * (0.94 + 0.08 * (0.5 + 0.5 * math.sin(TAU * f / 4)))    # the tip flickers on twos
    puffs = []
    for k in range(5):
        t = ((f / n) + k / 5) % 1.0
        side = -1 if k % 2 else 1
        r = 0.24 + 0.30 * math.sin(math.pi * min(t * 1.2, 1.0))
        z = -1.15 - 2.45 * t
        x = side * (0.40 + 0.36 * math.sin(math.pi * t)) + 0.05 * math.sin(6.28 * t + k)
        puffs.append((t, k, r, x, z))
    for t, k, r, x, z in sorted(puffs, reverse=True):         # far puffs first; the flame is drawn over the near ones
        hot = t < 0.18
        G.stroke(d, G.lumpy_ellipse(x, z, r, r * 1.06, n=24, lump=0.07, seed=31 * k + f), M["puff_hot"] if hot else M["puff"], O, cyclic=True)
        if r > 0.3:
            G.seam(d, G.bezier((x - r * 0.5, z - r * 0.18), (x, z - r * 0.5), (x + r * 0.45, z - r * 0.22), n=6), M["ink"])
    G.stroke(d, _flame(BOOST_HW, L, f), M["flame"], O, cyclic=True)                       # the red edge, inked
    G.stroke(d, _flame(BOOST_HW * 0.64, L * 0.76, f, z0=0.04, wave=0.035, sway=0.08), M["flame_mid"], 0.0, cyclic=True)   # gold core
    G.stroke(d, _flame(BOOST_HW * 0.30, L * 0.34, f, z0=0.03, wave=0.015, sway=0.03), M["core"], 0.0, cyclic=True)   # hot spot
    for side in (-1, 1):            # flow lines down the red band, and a lick that breaks off the tip on alternate twos
        G.seam(d, [(side * (BOOST_HW * 0.80 * (1 - s) ** 0.8 + 0.03 * math.sin(TAU * (2 * s - f / 4))), -L * s)
                   for s in [0.10 + 0.05 * i for i in range(9)]], M["ink"])
    if (f // 2) % 2 == 0:
        zl = -L - 0.22
        lick = [(0.0, zl + 0.16), (0.09, zl - 0.02), (0.0, zl - 0.20), (-0.09, zl - 0.02)]
        G.stroke(d, lick, M["flame"], O, cyclic=True)


# ---------------------------------------------------------------- the table render.py and the preview share

FX = {
    "vapor_cone": dict(key="fx/ship/vapor_cone", draw=draw_vapor_cone, n=10, clip="form", loop=False,
                       frame=(336, 252), pivot=(0.5, 0.85), columns=3, seed=17101,
                       self_check={"face": "a vapour cloud, no face",
                                   "motion": "forms in 4 frames (a collar growing into a flared skirt), holds with the puffs shifting, "
                                             "then detaches and tears away downward into puffs that spread and shrink",
                                   "original": "our own cartoon vapour skirt (round puffs, ink rims), drawn to the Pilgrim's hull",
                                   "style": "B-122's puff language (lumpy round puffs, seams), C1 / §9 v4; LEAD judges",
                                   "idle": "a one-shot (form): UNITY fires it once per upward crossing"},
                       ours="a cream vapour skirt that hugs the Pilgrim's waist and tears away in round cartoon puffs"),
    "shock_ring": dict(key="fx/ship/shock_ring", draw=draw_shock_ring, n=8, clip="burst", loop=False,
                       frame=(504, 248), pivot=(0.5, 0.5), columns=2, seed=17102,
                       self_check={"face": "a shock ring, no face",
                                   "motion": "a squashed star flash, then the ring overshoots outward fast and slows (ease-out), "
                                             "the band thinning and breaking into ink dashes as it fades",
                                   "original": "our own cartoon boom: a cream band between ink rims with wedge spikes",
                                   "style": "§9 v4 ink, Earth palette; LEAD judges",
                                   "idle": "a one-shot (burst): UNITY fires it once per upward crossing"},
                       ours="a cream boom ring with wedge spikes that thins to ink dashes"),
    "speed_lines": dict(key="fx/ship/speed_lines", draw=draw_speed_lines, n=4, clip="streak", loop=True,
                        frame=(128, 360), pivot=(0.0, 0.5), columns=4, seed=17103,
                        self_check={"face": "motion streaks, no face",
                                    "motion": "each lane's streak steps down the tile over 4 frames (phases staggered, so the "
                                              "edge always holds streaks), heavy at the screen edge, light inward",
                                    "original": "hand-ruled cartoon speed lines",
                                    "style": "§9 v4 ink weights (outer 2-3 px near the edge, interior inward)",
                                    "idle": "loops (streak 4); UNITY eases it off at a steady speed"},
                        ours="hand-ruled ink streaks, heavy at the screen edge"),
    "puff_boost": dict(key="ships/pilgrim/puff_boost", draw=draw_puff_boost, n=8, clip="puff", loop=True,
                       frame=(192, 288), pivot=(0.5, 0.96), columns=4, seed=17104,
                       self_check={"face": "a flame and puffs of exhaust, no face",
                                   "motion": "the tongue flickers on twos (length, waves down the flanks, the tip swaying, a lick "
                                             "breaking off); the cruise puff's clouds born at its flanks trail down past the tip",
                                   "original": "our own cartoon flame tongue with the B-122 round puffs",
                                   "style": "the cruise puff's clouds (ships/pilgrim/puff) + §9 v4 ink; LEAD judges",
                                   "idle": "loops (puff 8), swapped in for the cruise puff while accelerating"},
                       ours="a nozzle-wide red-and-gold flame tongue with the Pilgrim's own round puffs trailing it"),
}
ORDER = ["vapor_cone", "shock_ring", "speed_lines", "puff_boost"]


def first_frames():
    """Each object's first drawing (timeline frame) in the source: what render.py seeds its jitter with."""
    out, f = {}, 1
    for name in ORDER:
        out[name] = f
        f += FX[name]["n"]
    return out


def build(out=SOURCE):
    """The source .blend (inside Blender): one GP object per effect in its own collection, clip markers in ORDER."""
    scene = G.new_scene()
    starts = first_frames()
    for name in ORDER:
        fx = FX[name]
        coll = G.collection(name)
        ob, gp = G.gp_object(name, coll)
        M = materials(gp)
        layer = gp.layers.new("art")
        for i in range(fx["n"]):
            fx["draw"](G.drawing(layer, starts[name] + i), M, i)
    G.mark_clips(scene, [(FX[n]["clip"], FX[n]["n"]) for n in ORDER])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


def entry_for(name):
    fx = FX[name]
    e = {"key": fx["key"], "style": "v3", "source": "sources/fx/ship_fx_v3.blend", "build": "scripts/build_fx_ship_v3.py",
         "build_fn": "build", "collection": name, "frame": list(fx["frame"]), "pivot": list(fx["pivot"]),
         "columns": fx["columns"], "facing": "right", "squash_root": False, "planet": "earth", "seed": fx["seed"],
         "bg_scene": "", "bg_layers": [0], "review_name": f"b171_{name}", "clips": [{"name": fx["clip"], "frames": fx["n"], "loop": fx["loop"]}],
         "self_check": fx["self_check"], "ours": fx["ours"]}
    if name == "puff_boost":
        e["beside"] = "ships/pilgrim/puff"
    return e


# ---------------------------------------------------------------- lock-free preview (exact frames) + LEAD's sheet

def render_frames(name):
    import gp_raster as GR
    fx = FX[name]
    fw, fh = fx["frame"]
    f0 = first_frames()[name]
    frames, widths = [], []
    for i in range(fx["n"]):
        gp = fakegp.FakeGP()
        M = materials(gp)
        d = fakegp.FakeDrawing()
        fx["draw"](d, M, i)
        img, w = GR.render_frame(fakegp.strokes_of(d, gp, as_object=(name, "art")), fw, fh, 64, fx["pivot"], ss=4,
                                 seed=fx["seed"] * 1000 + f0 + i)
        frames.append(img)
        widths += w
    return frames, widths


def preview_one(out_dir, name):
    import json
    import numpy as np
    from meridian import pngio, v3
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    fx = FX[name]
    fw, fh = fx["frame"]
    frames, widths = render_frames(name)
    cols = fx["columns"]
    rows = -(-len(frames) // cols)
    c_ = min(cols, len(frames))
    sheet = np.zeros((rows * fh + (rows - 1) * 4, c_ * fw + (c_ - 1) * 4, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + 4):r * (fh + 4) + fh, c * (fw + 4):c * (fw + 4) + fw] = im
    anims = [{"name": fx["clip"], "start": 0, "length": fx["n"], "loop": fx["loop"], **({"loop_from": 0} if fx["loop"] else {})}]
    meta = {"key": fx["key"], "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": 4,
            "frames": len(frames), "fps": 12, "pivot": list(fx["pivot"]), "facing": "right", "ppu": 64, "animations": anims,
            "squash_root": False}
    problems = v3.validate_sheet(meta, sheet.shape)
    m = v3.EDGE_MARGIN
    clipped = [i for i, im in enumerate(frames) if im[:m, :, 3].any() or im[-m:, :, 3].any() or im[:, :m, 3].any() or im[:, -m:, 3].any()]
    if clipped:
        problems.append(f"frames {clipped[:8]} touch the {m} px edge")
    if sheet.shape[0] > 1024 or sheet.shape[1] > 1024:
        problems.append(f"sheet {sheet.shape[1]}x{sheet.shape[0]} over the card's 1024^2")
    dd = os.path.join(out_dir, "b171")
    os.makedirs(dd, exist_ok=True)
    variant = fx["key"].split("/")[2]
    png = os.path.join(dd, f"{variant}_color.png")
    nb = pngio.write_png(png, sheet)
    with open(os.path.join(dd, f"{variant}.json"), "w", encoding="utf-8", newline="\n") as f_:
        json.dump(meta, f_, indent=2)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    rng = lambda ws: (min(w[1] for w in ws), max(w[2] for w in ws)) if ws else (0, 0)  # noqa: E731
    stats = {"outer_px": rng(outer), "inner_px": rng(inner), "inner_n": len(inner), "palette": v3.palette_hits(sheet, "earth"),
             "problems": problems, "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": nb // 1024}
    out = os.path.join(out_dir, f"review_b171_{name}_preview.png")
    boxes = review.v3_sheet_review(entry_for(name), meta, frames, png, out, stats)
    line = (f"{name}: sheet {sheet.shape[1]}x{sheet.shape[0]} {nb // 1024} KB, ink {stats['outer_px'][0]:.2f}-{stats['outer_px'][1]:.2f} / "
            f"{stats['inner_px'][0]:.2f}-{stats['inner_px'][1]:.2f}, palette {stats['palette'][0] * 100:.1f}% {stats['palette'][1][:3]}, "
            f"problems {problems or '-'}, boxes not x: {','.join(k for k, (mk, _n) in boxes.items() if mk != 'x') or '-'}")
    print(line)
    return frames, stats, line


def preview(out_dir, names=None):
    """The sheets + their reviews (one process; then `--sheet` builds LEAD's page from the written sheets: under the
    300 MB lock-free cap, D-109)."""
    lines = [preview_one(out_dir, n)[2] for n in (names or ORDER)]
    if not names:
        with open(os.path.join(out_dir, "b171", "summary.txt"), "w", encoding="utf-8") as f_:
            f_.write("\n".join(lines) + "\n")
    fakegp.restore()




ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))


def sheet_path(out_dir, name, art=False):
    cat, nm, variant = FX[name]["key"].split("/")
    d = os.path.join(ART, cat, nm) if art else os.path.join(out_dir, "b171")
    return os.path.join(d, f"{variant}_color.png"), os.path.join(d, f"{variant}.json")


def read_back(out_dir, name, art=False):
    """(frames, sheet path, summary line) from a written sheet: the preview's (b171/) or the export's (Art/)."""
    import json
    from meridian import pngio
    png, js = sheet_path(out_dir, name, art)
    meta = json.load(open(js, encoding="utf-8"))
    sheet = pngio.read_png_np(png)
    fw, fh, cols = meta["frame_width"], meta["frame_height"], meta["columns"]
    frames = []
    for i in range(meta["frames"]):
        r, c = divmod(i, cols)
        frames.append(sheet[r * (fh + 4):r * (fh + 4) + fh, c * (fw + 4):c * (fw + 4) + fw].copy())
    if art:
        sys.path.insert(0, os.path.dirname(HERE))
        import review
        line = (f"{name}: {FX[name]['key']} sheet {sheet.shape[1]}x{sheet.shape[0]} {os.path.getsize(png) // 1024} KB, "
                f"{meta['frames']} frames {fw}x{fh}, pivot {meta['pivot']}, columns {cols}; exported {review.stamp_text(png)}")
    else:
        summary = open(os.path.join(out_dir, "b171", "summary.txt"), encoding="utf-8").read().splitlines()
        line = next((s for s in summary if s.startswith(name + ":")), name + ": (no summary)")
    return frames, png, line


def _area_matrix(n_in, s):
    """Exact area-average resampling along one axis (what a mip-mapped sprite at scale s shows): out = A @ in."""
    import numpy as np
    n_out = int(round(n_in * s))
    A = np.zeros((n_out, n_in), np.float32)
    for i in range(n_out):
        a, b = i / s, (i + 1) / s
        for j in range(int(math.floor(a)), min(n_in, int(math.ceil(b)))):
            A[i, j] = (min(b, j + 1) - max(a, j)) * s
    return A


def _scaled(img, s):
    import numpy as np
    Ay, Ax = _area_matrix(img.shape[0], s), _area_matrix(img.shape[1], s)
    return np.stack([Ay @ img[..., c] @ Ax.T for c in range(3)], -1)


def composite(out_dir, art=False):
    """LEAD's sheet: review_b171_flight_fx_preview.png from the preview sheets, or (art=True) review_b171_flight_fx.png
    from the exported sheets, stamped per file. Panel 1: the Pilgrim at 1x on the Earth sky - cruise | boost + lines |
    the boom | after - with the lines on both 1080 px edges. Panel 2 (LEAD 02:2x): cruise | boost | boom at the in-game
    ship scales, 0.5625x (the 30 m frame) and 0.375x (45 m), area-averaged like the mip-mapped sprites."""
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_pilgrim_rig as PR
    res = {n: read_back(out_dir, n, art) for n in ORDER}
    side = BP.PILGRIM_RIGS[0]
    sfw, sfh, spiv = 400, 816, (0.5, 12 / 816)
    ship, _w = PR.render(side, {}, sfw, sfh, spiv)
    cruise = pngio.read_png_np(os.path.join(ART, "ships", "pilgrim", "puff_color.png"))
    cruise_f = cruise[:128, 3 * 132:3 * 132 + 128]
    sock = BP.UP_SOCKETS["tail_exhaust"]

    def at(dst, img, piv, X, Y):     # place a frame so its pivot lands on panel pixel (X, Y)
        h, w = img.shape[:2]
        review._over(dst, img, int(round(X - piv[0] * w)), int(round(Y - (1 - piv[1]) * h)))

    def ship_xy(x0, ytop, xm, zm):  # ship-local metres -> panel px for a ship frame placed at (x0, ytop)
        return x0 + sfw * spiv[0] + xm * 64, ytop + sfh - sfh * spiv[1] - zm * 64

    def shot(dst, kind, x0, ytop):
        if kind in ("boom", "after"):   # the ring behind the hull
            at(dst, res["shock_ring"][0][2 if kind == "boom" else 5], FX["shock_ring"]["pivot"], *ship_xy(x0, ytop, 0.0, ZC))
        review._over(dst, ship, x0, ytop)
        if kind in ("boost", "boom"):
            at(dst, res["puff_boost"][0][3], FX["puff_boost"]["pivot"], *ship_xy(x0, ytop, *sock))
        else:
            at(dst, cruise_f, (0.5, 0.96), *ship_xy(x0, ytop, *sock))
        if kind in ("boom", "after"):   # the cone in front of the hull
            at(dst, res["vapor_cone"][0][3 if kind == "boom" else 7], FX["vapor_cone"]["pivot"], *ship_xy(x0, ytop, 0.0, ZC))

    W, H = 1900, 1080 + 60
    bg, note = review.planet_background("earth", "", W, H, only=[0])
    bg[:60] = review.PAPER
    shots = [("cruise: the B-122 puff (frame 3)", "cruise"), ("accelerating: puff_boost (frame 3) + speed lines", "boost"),
             ("the boom: boost + vapor_cone 3 + shock_ring 2", "boom"), ("after: vapor_cone 7 tearing + shock_ring 5", "after")]
    for (label, kind), xc in zip(shots, [370, 770, 1170, 1570]):
        shot(bg, kind, xc - sfw // 2, 60 + 40)
        review._label(bg, label, xc - sfw // 2 + 20, 70)
    lines = res["speed_lines"][0]
    for k in range(3):              # both 1080 px edges: tile k shows frame k % 4; the right edge mirrored
        review._over(bg, lines[k % 4], 0, 60 + k * 360)
        review._over(bg, lines[(k + 2) % 4][:, ::-1], W - 128, 60 + k * 360)
    review._label(bg, "b-171 flight fx (d-158) at 1x on the earth sky: the pilgrim (12 m = 768 px) as the rig assembles it; "
                      "speed lines on both 1080 px edges (3 tiles each, right edge mirrored)", 6, 6)
    review._label(bg, f"background: {note}; cone and ring pivots at the centre of mass (6.2 m), the puffs at tail_exhaust", 6, 26)
    review._label(bg, "every frame + the ten boxes per key: review_b171_{vapor_cone,shock_ring,speed_lines,puff_boost}"
                      f"{'' if art else '_preview'}.png", 140, H - 20)
    # panel 2: cruise | boost | boom at the in-game ship scales
    CW, CH = 560, 1060
    trio, _n = review.planet_background("earth", "", 3 * CW, CH, only=[0])
    for i, kind in enumerate(("cruise", "boost", "boom")):
        shot(trio, kind, i * CW + (CW - sfw) // 2, 20)
    s1, s2 = _scaled(trio, 0.5625), _scaled(trio, 0.375)
    row = np.tile(review.PAPER, (s1.shape[0] + 44, W, 1)).astype(np.float32)
    row[30:30 + s1.shape[0], 8:8 + s1.shape[1]] = s1
    x2 = 8 + s1.shape[1] + 30
    row[30:30 + s2.shape[0], x2:x2 + s2.shape[1]] = s2
    review._label(row, "in game: cruise | boost | boom at 0.5625x (the 30 m ship frame, 36 px/m)", 8, 8)
    review._label(row, "at 0.375x (the 45 m frame, 24 px/m); area-averaged", x2, 8)
    foot = np.tile(review.PAPER, (30 + 18 * len(ORDER), W, 1)).astype(np.float32)
    for i, name in enumerate(ORDER):
        review._label(foot, res[name][2][:160], 6, 6 + 18 * i)
    img = np.vstack([bg, row, foot])
    import time
    tag = "exported sheets read back from Art (stamps per file above)" if art else "preview (lock-free, fakegp, ss 4)"
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + tag, 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
    out = os.path.join(out_dir, f"review_b171_flight_fx{'' if art else '_preview'}.png")
    review.write(out, img)
    fakegp.restore()
    print("written", out, img.shape[1], "x", img.shape[0])


if __name__ == "__main__":
    if "--sheet" in sys.argv or "--art" in sys.argv:
        composite(sys.argv[1], art="--art" in sys.argv)
    else:
        preview(sys.argv[1], [a for a in sys.argv[2:] if a in FX] or None)
