"""B-172 (C3; the 0.4.7 smoke_10 read: the Earth Waystation was still the grey v2 model): the space stations and the belt
re-inked for the top-down view as v3.1 prop sheets (colour + json, no maps), drawn with gp_draw (fakegp + numpy outside
Blender), the build_props_*_v3 API (PROPS, KEY, render_all, sheet_meta, export, main) so render.py's prop rows export them.
Top-down: x right, z up the screen; light from the upper right (shadow tones on the lower-left of every form); no faces.
Units are the space view's: 64 px per unit, the v2 footprints (Waystation.Size 14 u across, centre origin; belt rocks
drawn 4 u across, UNITY scales each instance to 2-12 u as it does the models).

  waystation       896x896, lamps 4 (loop)  Earth, Halcyon Freight, Earth palette in the camp-set look: a cream docking ring
                   with teal panels and a lamp chase, four teal spokes, a mustard hub with a red Halcyon band and a hatch,
                   the cargo deck (brown planks, crates) to the east with a lattice crane over it, two solar wings to the
                   west, the docking collar to the south (the ship docks at Size / 2 below the centre, DockingBay) with its
                   guide lamps, a beacon mast to the north.
  waystation_mars  896x896, lamps 4 (loop)  the same plan in the Mars palette with Mars parts: a rust hexagonal hub, three
                   spokes, a dish antenna to the north, dust-coloured crates.
  asteroid_01..06  256x256, idle 8 (loop)   a slow tumble about the screen's vertical axis: craters slide across the face and
                   foreshorten, the silhouette breathes between its long and short side; six shapes and stones (ochre,
                   pale stone, rust, a bitten ochre, salmon, ice-teal; 06 a contact binary). UNITY plays them slowly with a
                   random phase per instance (the json says 12 fps like every v3 sheet).

Every pivot is the centre (0.5, 0.5), as the v2 models' space origin. replaces_v2: the export removes each key's .glb /
_normal / _mask / _emission (never a .meta, D-016).

  python -I build_props_space_v3.py <review png>   lock-free design review: both stations at 1x with the Pilgrim docked
                                                   (its top rig at the space view's 4 u), the lamp chase, the six rocks'
                                                   tumbles, the per-prop checks
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_earth_v3 as CK  # noqa: E402  (gp_draw real in Blender, fakegp outside)
from meridian import fakegp, v3  # noqa: E402
import gp_raster as GR  # noqa: E402

G = CK.G
O, I = G.OUTER, G.INNER
PPU = 64
KEY = "props/space/{}"
TAU = 2 * math.pi
LIM = 6.88                          # the station's drawing stays inside +-LIM u (frame 7 u half, 2 px margin, ink)


def mats(gp, planet):
    P = v3.PALETTES[planet]

    def m(name, fill=None, ink=True):
        return G.mat(gp, f"sp_{planet}_{name}", fill=fill, ink=ink)
    M = {"ink": m("ink", None, True)}
    for k in ("offwhite", "red", "mustard", "teal", "green", "sky", "brown"):
        M[k] = m(k, P[k])
        M[k + "_flat"] = m(k + "_flat", P[k], ink=False)
        M[k + "_sh"] = m(k + "_sh", v3.shadow_of(P[k], planet), ink=False)
        M[k + "_dp"] = m(k + "_dp", v3.deep_of(P[k], planet), ink=False)
    return M


# ---------------------------------------------------------------- shape helpers (units, x right, z up)

def lin(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def circle(cx, cz, r, n=40, lump=0.012, seed=0):
    return G.lumpy_ellipse(cx, cz, r, r, n=n, lump=lump, seed=seed)


def arc(cx, cz, r, a0, a1, n=16):
    return [(cx + r * math.cos(a), cz + r * math.sin(a)) for a in lin(a0, a1, n)]


def band(cx, cz, r0, r1, a0, a1, n=24):
    """An annular sector (a closed polygon); a full band (a1 - a0 = TAU) has a zero-width slit, invisible with no ink."""
    return arc(cx, cz, r1, a0, a1, n) + arc(cx, cz, r0, a1, a0, n)


def box(x0, z0, x1, z1, bow=0.008):
    """A hand-drawn rectangle: four slightly bowed sides."""
    pts = []
    for a, b in (((x0, z0), (x1, z0)), ((x1, z0), (x1, z1)), ((x1, z1), (x0, z1)), ((x0, z1), (x0, z0))):
        pts += G.bowed_line(a, b, bow=bow, n=6)[:-1]
    return pts


def strip_shadow(d, M, tone, x0, z0, x1, z1, w=0.12):
    """The lower-left shadow of a box lit from the upper right: an L along its left and bottom sides."""
    G.stroke(d, [(x0, z0), (x1, z0), (x1, z0 + w), (x0 + w, z0 + w), (x0 + w, z1), (x0, z1)], M[tone], 0.0, cyclic=True)


def tube(d, M, p0, p1, w, fill, ribs=0):
    """A straight tube seen from above: a filled ink-lined band, its lower-left side shaded, rib seams across."""
    (x0, z0), (x1, z1) = p0, p1
    L = math.hypot(x1 - x0, z1 - z0)
    ux, uz = (x1 - x0) / L, (z1 - z0) / L
    nx, nz = -uz, ux
    if nx + nz > 0:                 # make n point to the lower-left (the shaded side)
        nx, nz = -nx, -nz
    h = w / 2
    poly = [(x0 + nx * h, z0 + nz * h), (x1 + nx * h, z1 + nz * h), (x1 - nx * h, z1 - nz * h), (x0 - nx * h, z0 - nz * h)]
    G.stroke(d, poly, M[fill + "_flat"], 0.0, cyclic=True)
    G.stroke(d, [(x0 + nx * h, z0 + nz * h), (x1 + nx * h, z1 + nz * h), (x1 + nx * h * 0.25, z1 + nz * h * 0.25),
                 (x0 + nx * h * 0.25, z0 + nz * h * 0.25)], M[fill + "_sh"], 0.0, cyclic=True)
    G.stroke(d, poly, M["ink"], O, cyclic=True)
    for i in range(ribs):
        t = (i + 1) / (ribs + 1)
        cx, cz = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t
        G.seam(d, [(cx + nx * h * 0.9, cz + nz * h * 0.9), (cx - nx * h * 0.9, cz - nz * h * 0.9)], M["ink"])


def lamp(d, M, x, z, lit, on="mustard", off="brown_sh", r=0.13):
    G.stroke(d, circle(x, z, r, n=14, lump=0.02, seed=int(97 * x + 31 * z) & 255), M[on if lit else off], I, cyclic=True)
    if lit:
        G.stroke(d, circle(x + 0.03, z + 0.03, r * 0.45, n=10, lump=0.0), M["offwhite_flat"], 0.0, cyclic=True)


# ---------------------------------------------------------------- the Waystations (frame 896^2 = 14 u, centre pivot)

STATIONS = {
    "waystation": dict(planet="earth", ring=(4.30, 5.10), hub="round", spokes=(45, 135, 225, 315), spoke="teal",
                       panel="teal", crates=("red", "mustard", "teal", "red", "offwhite"), north="mast", seed=11),
    "waystation_mars": dict(planet="mars", ring=(4.20, 5.00), hub="hex", spokes=(90 + 30, 90 + 150, 270), spoke="red",
                            panel="sky", crates=("mustard", "offwhite", "red", "mustard", "sky"), north="dish", seed=23),
}


def solar_wings(d, M, s, r1):
    G.stroke(d, box(-LIM + 0.12, -0.16, -r1 + 0.1, 0.16), M["mustard"], O, cyclic=True)        # the truss
    for i in range(7):
        x = -LIM + 0.35 + i * 0.22
        G.seam(d, [(x, -0.14), (x + 0.11, 0.14)], M["ink"])
    for sz in (1, -1):
        z0, z1 = (0.32, 2.55) if sz > 0 else (-2.55, -0.32)
        x0, x1 = -LIM + 0.08, -5.30
        G.stroke(d, box(x0, z0, x1, z1), M[s["panel"] + "_flat"], 0.0, cyclic=True)
        strip_shadow(d, M, s["panel"] + "_sh", x0, z0, x1, z1, w=0.14)
        G.stroke(d, box(x0, z0, x1, z1), M["ink"], O, cyclic=True)
        for gx in lin(x0, x1, 5)[1:-1]:
            G.seam(d, G.bowed_line((gx, z0 + 0.06), (gx, z1 - 0.06), bow=0.01, n=5), M["ink"])
        for gz in lin(z0, z1, 6)[1:-1]:
            G.seam(d, G.bowed_line((x0 + 0.06, gz), (x1 - 0.06, gz), bow=0.01, n=5), M["ink"])


def cargo_deck(d, M, s, r1):
    x0, x1, z0, z1 = r1 - 0.25, LIM - 0.05, -2.25, 2.25
    G.stroke(d, box(x0, z0, x1, z1), M["brown_flat"], 0.0, cyclic=True)
    strip_shadow(d, M, "brown_dp", x0, z0, x1, z1, w=0.14)
    G.stroke(d, box(x0, z0, x1, z1), M["ink"], O, cyclic=True)
    for gz in lin(z0, z1, 12)[1:-1]:                       # planks
        G.seam(d, G.bowed_line((x0 + 0.05, gz), (x1 - 0.05, gz), bow=0.006, n=5), M["ink"])
    G.specks(d, [(x0 + 0.4, 1.9), (x0 + 1.2, -1.7), (x1 - 0.3, 0.6), (x1 - 0.5, -1.1)], M["ink"])
    rnd = random.Random(s["seed"])
    spots = [(x0 + 0.55, 1.35), (x0 + 1.25, 1.45), (x0 + 0.60, -0.35), (x0 + 1.15, -1.45), (x0 + 0.55, -1.55)]
    for (cx, cz), col in zip(spots, s["crates"]):
        h = 0.30 + 0.04 * rnd.random()
        bx0, bz0, bx1, bz1 = cx - h, cz - h, cx + h, cz + h
        G.stroke(d, box(bx0, bz0, bx1, bz1), M[col + "_flat"], 0.0, cyclic=True)
        strip_shadow(d, M, col + "_sh", bx0, bz0, bx1, bz1, w=0.09)
        G.stroke(d, box(bx0, bz0, bx1, bz1), M["ink"], O, cyclic=True)
        G.seam(d, [(bx0 + 0.06, bz0 + 0.06), (bx1 - 0.06, bz1 - 0.06)], M["ink"])
        G.seam(d, [(bx0 + 0.06, bz1 - 0.06), (bx1 - 0.06, bz0 + 0.06)], M["ink"])


def ring(d, M, s, k, r0, r1):
    G.stroke(d, band(0, 0, r0, r1, 0.0, TAU, 72), M["offwhite_flat"], 0.0, cyclic=True)
    for i in range(8):                                     # teal panel segments
        a = TAU * i / 8 + 0.12
        G.stroke(d, band(0, 0, r0 + 0.08, r1 - 0.08, a, a + 0.32, 8), M[s["panel"] + "_flat"], 0.0, cyclic=True)
    G.stroke(d, band(0, 0, (r0 + r1) / 2 + 0.05, r1, math.radians(150), math.radians(300), 20), M["offwhite_sh"], 0.0, cyclic=True)
    G.stroke(d, band(0, 0, r1 - 0.12, r1, math.radians(175), math.radians(275), 14), M["offwhite_dp"], 0.0, cyclic=True)
    G.stroke(d, band(0, 0, r0, r0 + 0.1, math.radians(-15), math.radians(105), 14), M["offwhite_dp"], 0.0, cyclic=True)
    G.stroke(d, circle(0, 0, r1, n=72, lump=0.004, seed=s["seed"]), M["ink"], O, cyclic=True)
    G.stroke(d, circle(0, 0, r0, n=64, lump=0.004, seed=s["seed"] + 1), M["ink"], O, cyclic=True)
    for i in range(24):                                    # plate seams across the band, rivets
        a = TAU * i / 24
        G.seam(d, [(r0 * math.cos(a), r0 * math.sin(a)), (r1 * math.cos(a), r1 * math.sin(a))], M["ink"])
    G.rivets(d, [((r1 - 0.12) * math.cos(TAU * i / 48 + 0.07), (r1 - 0.12) * math.sin(TAU * i / 48 + 0.07)) for i in range(48)],
             M["ink"], size=0.05)
    rm = (r0 + r1) / 2
    for i in range(12):                                    # the lamp chase: every fourth lamp lit, stepping each frame
        a = TAU * i / 12 + TAU / 24
        lamp(d, M, rm * math.cos(a), rm * math.sin(a), i % 4 == k)


def hub(d, M, s):
    if s["hub"] == "round":
        G.stroke(d, circle(0, 0, 1.55, n=48, lump=0.01, seed=5), M["mustard_flat"], 0.0, cyclic=True)
        G.stroke(d, band(0, 0, 1.0, 1.55, math.radians(160), math.radians(290), 18), M["mustard_sh"], 0.0, cyclic=True)
        G.stroke(d, circle(0, 0, 1.55, n=48, lump=0.01, seed=5), M["ink"], O, cyclic=True)
        G.stroke(d, band(0, 0, 1.12, 1.30, 0.0, TAU, 48), M["red_flat"], 0.0, cyclic=True)     # the Halcyon band
        G.stroke(d, circle(0, 0, 1.30, n=48, lump=0.004, seed=6), M["ink"], I, cyclic=True)
        G.stroke(d, circle(0, 0, 1.12, n=48, lump=0.004, seed=7), M["ink"], I, cyclic=True)
        G.rivets(d, [(1.43 * math.cos(TAU * i / 20), 1.43 * math.sin(TAU * i / 20)) for i in range(20)], M["ink"], size=0.05)
        G.stroke(d, circle(0, 0, 0.78, n=36, lump=0.01, seed=8), M["offwhite"], O, cyclic=True)  # the hatch
        G.stroke(d, band(0, 0, 0.45, 0.78, math.radians(170), math.radians(280), 12), M["offwhite_sh"], 0.0, cyclic=True)
        G.seam(d, [(-0.55, 0.0), (0.55, 0.0)], M["ink"])
        G.seam(d, [(0.0, -0.55), (0.0, 0.55)], M["ink"])
        G.stroke(d, circle(0.0, 0.0, 0.16, n=14, lump=0.0), M["brown"], I, cyclic=True)
    else:
        hexa = [(1.65 * math.cos(TAU * i / 6 + TAU / 12), 1.65 * math.sin(TAU * i / 6 + TAU / 12)) for i in range(6)]
        inner = [(1.0 * math.cos(TAU * i / 6 + TAU / 12), 1.0 * math.sin(TAU * i / 6 + TAU / 12)) for i in range(6)]
        G.stroke(d, hexa, M["red_flat"], 0.0, cyclic=True)
        G.stroke(d, [hexa[2], hexa[3], hexa[4], inner[4], inner[3], inner[2]], M["red_sh"], 0.0, cyclic=True)
        G.stroke(d, hexa, M["ink"], O, cyclic=True)
        for a, b in zip(hexa, inner):
            G.seam(d, [a, b], M["ink"])
        G.stroke(d, inner, M["mustard"], O, cyclic=True)
        G.stroke(d, [inner[2], inner[3], inner[4], (0.0, -0.15)], M["mustard_sh"], 0.0, cyclic=True)
        G.rivets(d, [(1.45 * math.cos(TAU * i / 18), 1.45 * math.sin(TAU * i / 18)) for i in range(18)], M["ink"], size=0.05)
        G.stroke(d, circle(0, 0, 0.55, n=28, lump=0.01, seed=9), M["offwhite"], O, cyclic=True)
        G.seam(d, [(-0.38, 0.0), (0.38, 0.0)], M["ink"])
        G.stroke(d, circle(0.0, 0.0, 0.14, n=12, lump=0.0), M["brown"], I, cyclic=True)


def crane(d, M, s, r1):
    z = 0.95
    G.stroke(d, circle(0.95, z, 0.40, n=22, lump=0.02, seed=3), M["brown"], O, cyclic=True)      # the turret
    G.stroke(d, box(1.25, z - 0.15, 6.25, z + 0.15), M["mustard_flat"], 0.0, cyclic=True)        # the lattice boom
    G.stroke(d, box(1.25, z - 0.15, 6.25, z - 0.06), M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, box(1.25, z - 0.15, 6.25, z + 0.15), M["ink"], O, cyclic=True)
    xs = lin(1.35, 6.15, 19)
    for i, x in enumerate(xs[:-1]):
        G.seam(d, [(x, z - 0.12 if i % 2 else z + 0.12), (xs[i + 1], z + 0.12 if i % 2 else z - 0.12)], M["ink"])
    G.stroke(d, circle(6.25, z, 0.24, n=16, lump=0.02, seed=4), M["offwhite"], O, cyclic=True)    # the pulley
    G.stroke(d, circle(6.25, z, 0.08, n=10, lump=0.0), M["brown"], I, cyclic=True)
    G.seam(d, [(6.25, z - 0.24), (6.25, z - 0.62)], M["ink"])                                     # the cable to the hook
    G.stroke(d, circle(6.25, z - 0.70, 0.09, n=10, lump=0.0), M["mustard"], I, cyclic=True)


def dock_collar(d, M, s, k, r1):
    """The docking clamp on the ring's south edge: the docked ship's centre sits at (0, -Size / 2) = (0, -7 u) and its
    4 u hull reaches the ring, so the clamp is short and the guide lamps stand clear of the hull at +-1.25 u."""
    z0, z1 = -r1 + 0.15, -r1 - 0.42
    G.stroke(d, box(-0.70, z1, 0.70, z0), M["mustard_flat"], 0.0, cyclic=True)
    G.stroke(d, box(-0.70, z1, -0.40, z0), M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, box(-0.70, z1, 0.70, z0), M["ink"], O, cyclic=True)
    G.seam(d, [(-0.64, (z0 + z1) / 2), (0.64, (z0 + z1) / 2)], M["ink"])
    for sx in (-1, 1):                                     # the clamp's two jaws
        jaw = [(sx * 0.40, z1 + 0.02), (sx * 0.62, z1 + 0.02), (sx * 0.55, z1 - 0.30), (sx * 0.36, z1 - 0.22)]
        G.stroke(d, jaw, M["brown"], O, cyclic=True)
    for sx in (-1, 1):                                     # the guide lamps: red port, green starboard, alternating on twos
        G.seam(d, [(sx * 0.70, z1 + 0.2), (sx * 1.12, z1 + 0.05)], M["ink"])
        lamp(d, M, sx * 1.25, z1, (k % 2 == 0) == (sx < 0), on="red" if sx < 0 else "green", off="brown_sh", r=0.16)


def north(d, M, s, k, r1):
    if s["north"] == "mast":
        G.stroke(d, G.bowed_line((0.0, r1 - 0.05), (0.0, 6.35), bow=0.004, n=8), M["ink"], O)
        for zz in (5.55, 5.95):
            G.seam(d, [(-0.22, zz), (0.22, zz)], M["ink"])
        lamp(d, M, 0.0, 6.52, k in (0, 2), on="red", off="red_dp", r=0.2)
    else:
        G.stroke(d, box(-0.08, r1 - 0.05, 0.08, 5.35), M["brown"], I, cyclic=True)
        G.stroke(d, circle(0.0, 5.95, 0.78, n=36, lump=0.01, seed=12), M["offwhite"], O, cyclic=True)
        G.stroke(d, band(0.0, 5.95, 0.4, 0.78, math.radians(170), math.radians(290), 12), M["offwhite_sh"], 0.0, cyclic=True)
        G.stroke(d, circle(0.0, 5.95, 0.42, n=24, lump=0.01, seed=13), M["ink"], I, cyclic=True)
        for a in (90, 210, 330):
            G.seam(d, [(0.0, 5.95), (0.62 * math.cos(math.radians(a)), 5.95 + 0.62 * math.sin(math.radians(a)))], M["ink"])
        lamp(d, M, 0.0, 5.95, k in (0, 2), on="red", off="red_dp", r=0.12)


def draw_station(name):
    s = STATIONS[name]

    def fn(d, M, k=0):
        r0, r1 = s["ring"]
        solar_wings(d, M, s, r1)
        cargo_deck(d, M, s, r1)
        for a in s["spokes"]:
            ar = math.radians(a)
            tube(d, M, (1.2 * math.cos(ar), 1.2 * math.sin(ar)), ((r0 + 0.15) * math.cos(ar), (r0 + 0.15) * math.sin(ar)),
                 0.42, s["spoke"], ribs=4)
        ring(d, M, s, k, r0, r1)
        hub(d, M, s)
        crane(d, M, s, r1)
        dock_collar(d, M, s, k, r1)
        north(d, M, s, k, r1)
        G.hatch(d, -3.3, -3.2, M["ink"], n=3, length=0.32, spacing=0.12, angle_deg=40, seed=k + 2)
    return fn


# ---------------------------------------------------------------- the belt rocks (frame 256^2 = 4 u, centre pivot)

ROCKS = {  # rx, rz (u), lump, outline seed, colour, craters [(longitude rad, z u, radius u)], second lobe (dx, dz, rx, rz) or None
    "asteroid_01": dict(rx=1.62, rz=1.20, lump=0.07, seed=101, col="mustard",
                        craters=[(0.3, 0.35, 0.28), (2.0, -0.40, 0.22), (3.6, 0.10, 0.34), (5.0, -0.55, 0.18)], lobe=None),
    "asteroid_02": dict(rx=1.38, rz=1.32, lump=0.05, seed=102, col="offwhite",
                        craters=[(0.9, 0.50, 0.24), (2.6, -0.20, 0.30), (4.4, 0.45, 0.20), (5.6, -0.60, 0.16)], lobe=None),
    "asteroid_03": dict(rx=1.62, rz=0.86, lump=0.08, seed=103, col="red",
                        craters=[(0.2, 0.10, 0.20), (1.9, -0.25, 0.26), (3.3, 0.25, 0.18), (4.9, 0.0, 0.24)], lobe=None),
    "asteroid_04": dict(rx=1.48, rz=1.15, lump=0.12, seed=104, col="mustard",
                        craters=[(1.1, 0.30, 0.36), (3.0, -0.35, 0.20), (4.6, 0.40, 0.24)], lobe=None),
    "asteroid_05": dict(rx=1.20, rz=1.05, lump=0.10, seed=105, col="sky",
                        craters=[(0.6, -0.20, 0.20), (2.4, 0.35, 0.16), (4.0, -0.30, 0.22), (5.4, 0.30, 0.14)], lobe=None),
    "asteroid_06": dict(rx=1.00, rz=0.92, lump=0.06, seed=106, col="teal",
                        craters=[(0.8, 0.25, 0.18), (3.5, -0.20, 0.22)], lobe=(0.78, -0.18, 0.80, 0.74)),
}
ROCK_N = 8


def _rock_body(d, M, sp, k, dx=0.0, dz=0.0, rx=None, rz=None, seed_off=0):
    th = TAU * k / ROCK_N
    rx = (rx or sp["rx"]) * (0.90 + 0.10 * math.cos(2 * th + seed_off))     # the silhouette breathes as it turns
    rz = (rz or sp["rz"])
    rot = 0.10 * math.sin(th + seed_off)
    pts = G.lumpy_ellipse(dx, dz, rx, rz, n=40, lump=sp["lump"], seed=sp["seed"] + seed_off, rot=rot)
    col = sp["col"]
    G.stroke(d, pts, M[col + "_flat"], 0.0, cyclic=True)
    n = len(pts)                                            # the shaded lower-left: the outline's lower-left arc + an inner arc
    idx = [i for i in range(n) if math.radians(115) <= (TAU * i / n + rot) % TAU <= math.radians(305)]
    if idx:
        outer = [pts[i] for i in idx]
        inner = [(dx + (x - dx) * 0.58 + 0.10, dz + (z - dz) * 0.58 + 0.10) for x, z in outer[::-1]]
        G.stroke(d, outer + inner, M[col + "_sh"], 0.0, cyclic=True)
        deep = [(dx + (x - dx) * 0.86 + 0.02, dz + (z - dz) * 0.86 + 0.02) for x, z in outer[::-1][2:-2]]
        G.stroke(d, outer[2:-2] + deep, M[col + "_dp"], 0.0, cyclic=True)
    for lon, cz_, cr in sp["craters"]:                      # craters slide across the face and foreshorten
        if seed_off and cz_ > 0:
            continue
        a = lon + th
        vis = math.cos(a)
        if vis < 0.18:
            continue
        cx = dx + rx * 0.78 * math.sin(a)
        cz = dz + cz_ * (rz / sp["rz"])
        w = cr * max(0.35, vis)
        G.stroke(d, G.lumpy_ellipse(cx, cz, w, cr, n=16, lump=0.05, seed=int(lon * 10)), M[col + "_sh"], I, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(cx + w * 0.22, cz + cr * 0.22, w * 0.6, cr * 0.6, n=12, lump=0.05, seed=int(lon * 10) + 1),
                 M[col + "_dp"], 0.0, cyclic=True)
    G.stroke(d, pts, M["ink"], O, cyclic=True)
    rnd = random.Random(sp["seed"] * 7 + k)
    G.specks(d, [(dx + rx * (rnd.random() - 0.5) * 1.1, dz + rz * (rnd.random() - 0.5) * 1.1) for _ in range(5)], M["ink"])
    G.hatch(d, dx - rx * 0.45, dz - rz * 0.42, M["ink"], n=3, length=0.22 * min(rx, rz), spacing=0.08, angle_deg=35,
            seed=sp["seed"] + k)


def draw_rock(name):
    sp = ROCKS[name]

    def fn(d, M, k=0):
        if sp["lobe"]:                  # a contact binary: the far lobe first, the near one over it
            lx, lz, lrx, lrz = sp["lobe"]
            th = TAU * k / ROCK_N
            _rock_body(d, M, sp, k, dx=lx * math.cos(th) * 0.85, dz=lz, rx=lrx, rz=lrz, seed_off=3)
            _rock_body(d, M, sp, k, dx=-0.32 * math.cos(th), dz=0.12)
        else:
            _rock_body(d, M, sp, k)
    return fn


# ---------------------------------------------------------------- the prop table + the build_props_*_v3 API

# name -> (draw fn, frame w, frame h, clip, frames, planet)
PROPS = {n: (draw_station(n), 896, 896, "lamps", 4, STATIONS[n]["planet"]) for n in STATIONS}   # an idle needs 8-12 frames; 8 x 896^2 overflows 2048
PROPS.update({n: (draw_rock(n), 256, 256, "idle", ROCK_N, "mars") for n in ROCKS})
SELF = {
    "waystation": "lamps 4 (loop): the ring's lamps chase round (every fourth lit), the guide lamps alternate, the beacon blinks",
    "waystation_mars": "lamps 4 (loop): as the Earth station; the dish's lamp blinks",
}
SELF.update({n: "idle 8: a slow tumble (craters slide and foreshorten, the outline breathes); UNITY plays it slowly, random phase"
             for n in ROCKS})
SHEET_CAP = {n: 2048 for n in STATIONS}
SHEET_CAP.update({n: 1024 for n in ROCKS})


def pivot_of(name):
    return (0.5, 0.5)


def render_prop(name, k=0, seed=7):
    fn, fw, fh, _c, _n, planet = PROPS[name]
    gp = fakegp.FakeGP()
    M = mats(gp, planet)
    d = fakegp.FakeDrawing()
    fn(d, M, k)
    ss = 2 if fw > 512 else 4                          # a 896^2 station at ss 4 would hold 3584^2 buffers
    return GR.render_frame(fakegp.strokes_of(d, gp), fw, fh, PPU, pivot_of(name), ss=ss, seed=seed + 101 * k)


def render_all(names=None):
    imgs, widths = {}, {}
    for name in (names or PROPS):
        _fn, _fw, _fh, _c, n, _p = PROPS[name]
        imgs[name], widths[name] = [], []
        for k in range(n):
            img, w = render_prop(name, k)
            imgs[name].append(img)
            widths[name] += w
    return imgs, widths


def sheet_meta(name, frames):
    import numpy as np
    _fn, fw, fh, clip, n, planet = PROPS[name]
    g = v3.GUTTER
    cap = SHEET_CAP[name]
    cols = max(1, min(n, (cap + g) // (fw + g)))
    rows = -(-n // cols)
    sheet = np.zeros((rows * fh + (rows - 1) * g, min(cols, n) * fw + (min(cols, n) - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw] = im
    meta = {"key": KEY.format(name), "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": g,
            "frames": n, "fps": v3.FPS, "pivot": list(pivot_of(name)), "facing": "right", "ppu": PPU,
            "animations": [{"name": clip, "start": 0, "length": n, "loop": True, "loop_from": 0}], "squash_root": False,
            "view": "top", "units_across": round(fw / PPU, 3),
            "note": ("top-down; the pivot is the centre (the v2 model's space origin); " +
                     ("the station's 14 u across = Waystation.Size; the ship docks at (0, -Size / 2)" if name in STATIONS else
                      "drawn 4 u across; scale each instance to its belt size as the models were"))}
    problems = list(v3.validate_sheet(meta, sheet.shape))
    if sheet.shape[0] > cap or sheet.shape[1] > cap:
        problems.append(f"sheet {sheet.shape[1]}x{sheet.shape[0]} over {cap}^2")
    m = v3.EDGE_MARGIN
    for i, im in enumerate(frames):
        a = im[..., 3]
        if a[:m].any() or a[-m:].any() or a[:, :m].any() or a[:, -m:].any():
            problems.append(f"frame {i} touches the {m} px frame edge")
    return sheet, meta, problems


def v2_leftovers(art, names=None):
    d = os.path.join(art, "props", "space")
    return [os.path.join(d, n + s) for n in (names or PROPS) for s in (".glb", "_normal.png", "_mask.png", "_emission.png")
            if os.path.isfile(os.path.join(d, n + s))]


def export(art, imgs=None, names=None):
    import json
    from meridian import pngio
    names = list(names or PROPS)
    if imgs is None:
        imgs, _w = render_all(names)
    built, problems = [], []
    for name in names:
        sheet, meta, p = sheet_meta(name, imgs[name])
        problems += [f"{name}: {x}" for x in p]
        built.append((name, sheet, meta))
    if problems:
        raise ValueError("space prop export checks: " + "; ".join(problems))
    d = os.path.join(art, "props", "space")
    os.makedirs(d, exist_ok=True)
    out = []
    for name, sheet, meta in built:
        n = pngio.write_png(os.path.join(d, name + "_color.png"), sheet)
        with open(os.path.join(d, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((meta["key"], sheet.shape[1], sheet.shape[0], n))
    removed = v2_leftovers(art, names)
    for p in removed:
        os.remove(p)
    return out, {}, removed


# ---------------------------------------------------------------- the stamped review

SPACE_BG = "#1B1D27"                 # a review backdrop near the space view's dark (not exported)


def main(out, imgs=None, widths=None, stamp_paths=()):
    """Both stations at 1x side by side with the Pilgrim docked at (0, -7 u) (its top rig at the space view's 4 u, nose
    to the station), each station's idle 4 at 0.25x, the six rocks' tumbles at 1x, the per-prop checks."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_pilgrim_v3 as BP
    import preview_pilgrim_rig as PR
    if imgs is None:
        imgs, widths = render_all()
    bgc = np.array(v3.hex_rgb(SPACE_BG), np.float32) / 255.0
    W = 16 + ROCK_N * (256 + 8)                        # the eight rock frames at 1x (2128 px)
    # the docked Pilgrim: the top rig (12 m) drawn at 4 u = 256 px, nose up (+z)
    top = BP.PILGRIM_RIGS[1]
    ship, _w = PR.render(top, {}, 900, 420, (0.5, 0.5), ppu=64 * 4 / 12.0)
    ship = np.ascontiguousarray(np.rot90(ship, 1))         # the hull along x -> nose up
    ys, xs = np.nonzero(ship[..., 3])
    ship = ship[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    sh_, sw_ = ship.shape[:2]
    lines = []                       # the per-prop checks first (before the big image: under the 300 MB lock-free cap)
    for name in PROPS:
        sheet, meta, probs = sheet_meta(name, imgs[name])
        ws = widths[name] if widths else []
        o = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
        n_ = [w for w in ws if w[0] < v3.OUTER_SPLIT]
        rng = lambda q: f"{min(w[1] for w in q):.1f}-{max(w[2] for w in q):.1f}" if q else "-"  # noqa: E731
        pal = v3.palette_hits(imgs[name][0], PROPS[name][5])[0] * 100       # frame 0 (a 1796^2 sheet's check holds ~150 MB)
        lines.append(f"{name}: sheet {sheet.shape[1]}x{sheet.shape[0]}, ink {rng(o)} / {rng(n_)} px, palette {PROPS[name][5]} "
                     f"{pal:.1f}% (frame 0), json {'valid' if not probs else 'INVALID: ' + '; '.join(probs)[:60]}; no face")
        del sheet
    top_h = 896 + 60 + 140
    heights = [top_h, 224 + 40] + [256 + 36] * len(ROCKS) + [40 + 18 * len(PROPS)]
    img = np.empty((sum(heights), W, 3), np.float32)
    offs = [sum(heights[:i]) for i in range(len(heights))]
    rows = [img[o_:o_ + h_] for o_, h_ in zip(offs, heights)]
    panel = rows[0]
    panel[:] = bgc
    for i, name in enumerate(("waystation", "waystation_mars")):
        x0 = 30 + i * (896 + 40)
        review._over(panel, imgs[name][0], x0, 40)
        cx, cy = x0 + 448, 40 + 448 + 7 * 64               # (0, -7 u) below the centre
        review._over(panel, ship, cx - sw_ // 2, cy - sh_ // 2)
        review._label(panel, f"{KEY.format(name)} 896x896 (14 u) at 1x, lamps frame 0; the pilgrim docked at (0, -7 u)", x0, 12)
    strip = rows[1]
    strip[:] = review.PAPER
    x = 8
    for name in ("waystation", "waystation_mars"):
        for k, im in enumerate(imgs[name]):
            q = im[::4, ::4]
            strip[30:30 + q.shape[0], x:x + q.shape[1]] = bgc
            review._over(strip, q, x, 30)
            review._label(strip, str(k), x + 2, 32)
            x += q.shape[1] + 6
        x += 24
    review._label(strip, "lamps 4 at 0.25x: the lamp chase round the ring, the guide lamps, the beacon / dish lamp", 8, 8)
    for ri, name in enumerate(ROCKS):
        row = rows[2 + ri]
        row[:] = review.PAPER
        for k, im in enumerate(imgs[name]):
            xx = 8 + k * (256 + 8)
            row[28:28 + 256, xx:xx + 256] = bgc
            review._over(row, im, xx, 28)
            review._label(row, str(k), xx + 2, 30)
        review._label(row, f"{KEY.format(name)} 256x256 (4 u) idle 8 at 1x: {SELF[name][:90]}", 8, 6)
    foot = rows[-1]
    foot[:] = review.PAPER
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 8 + 18 * i)
    if stamp_paths:
        review.stamp(img, stamp_paths[0], review.stale_keys())
    else:
        import time
        review.draw(img, time.strftime("%m-%d %H:%M") + " design preview (lock-free, fakegp)", 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
    from meridian import pngio                        # review.write's to_u8 holds three float copies: convert in place
    shape = img.shape
    np.clip(img, 0.0, 1.0, out=img)
    img *= 255.0
    np.rint(img, out=img)
    u8 = np.empty(shape[:2] + (4,), np.uint8)
    u8[..., :3] = img
    u8[..., 3] = 255
    del img, rows, panel, strip, foot, row
    pngio.write_png(out, u8)
    print("written", out, shape[1], "x", shape[0])


if __name__ == "__main__":
    main(sys.argv[1])
    fakegp.restore()
