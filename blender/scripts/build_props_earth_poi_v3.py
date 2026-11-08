"""B-195 (LEAD 14:2x; the owner saw them grey in 0.5.0): the five Earth POI props as v3.1 prop sheets in B-131's camp-props
style (build_props_common_v3's materials, ink weights, mid + deep shadow tones, drawn detail; no faces, D-101), the same API
(PROPS, KEY, render_all, export, main) so render.py's do_prop_sheet_set exports the set row. Each replaces its v2 model under
the same key: the export removes the .glb and its normal / mask / emission maps (the colour map and json are rewritten), so
ModelSwap finds no model and dresses the POI card with the sheet (U-113).

Frames are the PoiCatalog size's width x 64 px (PoiPlacer fits a sheet to the declared width, so these show 1:1 with the camp
props' ink), the ground line 10 px above the bottom (pivot (0.5, 10 / h)):

  archive_door       256x208  blink 4   the Survey Archive's entrance: a half-sunk concrete bunker, a ribbed steel door with
                                        hazard chevrons, a sign plate on the lintel, one red status lamp that blinks
  archive_terminal    96x144  scan 4    the archive's console (6 m down in its chamber): a cabinet, a key ledge, a slanted screen
                                        with drawn text lines and a scan band sweeping up, one status light
  beacon              52x208  blink 4   a radio beacon: a banded mast on a hazard-striped block, a horn antenna, a caged red lamp
  launch_gantry      320x912  static    the Launch Complex's gantry (14 m): a teal lattice tower, red service arms with drooping
                                        umbilicals, an elevator cage, a railed top with an aviation lamp (LEAD: one frame at full
                                        density, an exception to B-131's 512^2 rule, inside the contract's 2048)
  launch_tower_ruin  256x592  static    an older rust-red tower bent at 5 m and snapped, a dangling cable, vines, a fallen
                                        section and rubble at its foot

  python -I build_props_earth_poi_v3.py <review png>   lock-free preview: both POIs assembled at 1x on the plains strip,
                                                        every clip frame, the checks
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_props_common_v3 as PC  # noqa: E402  (gp_draw through fakegp outside Blender; the camp props' materials)
from meridian import fakegp, v3  # noqa: E402
import gp_raster as GR  # noqa: E402

G, P = PC.G, PC.P
O, I = PC.O, PC.I
PPU, GROUND_PX = PC.PPU, PC.GROUND_PX
KEY = "props/earth/{}"
box, mats = PC.box, PC.mats
SHEET_CAP = 2048                                       # LEAD 14:2x: the contract's cap (the gantry is 320x912)
BLINK = [1.0, 0.75, 0.3, 0.75]                         # a slow lamp pulse, never fully off
SCAN = [0.0, 0.3, 0.6, 0.9]                            # the terminal's scan band, bottom to top


def member(d, M, a, b, w, mat, weight=I, T=None):
    """A steel member from a to b, w wide (filled and inked); T maps the outline (a rotation for a leaning section)."""
    pts = G.hose_outline([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b], w)
    G.stroke(d, T(pts) if T else pts, M[mat], weight, cyclic=True)


def rot(deg, cx, cz):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return lambda pts: [(cx + (x - cx) * c - (z - cz) * s, cz + (x - cx) * s + (z - cz) * c) for x, z in pts]


def truss(d, M, xl, xr, z0, z1, bay, mat, w=0.11, seed=0, broken=(), T=None):
    """A lattice tower section: X braces and a strut in each bay, two chords (fill, shade on the right one, ink)."""
    n = max(1, int(round((z1 - z0) / bay)))
    bay = (z1 - z0) / n
    for i in range(n):
        za, zb = z0 + i * bay, z0 + (i + 1) * bay
        if i in broken:                                                        # a snapped brace: two stubs
            member(d, M, (xl, za), (xl + (xr - xl) * 0.3, za + bay * 0.3), w * 0.45, mat, T=T)
            member(d, M, (xr, zb), (xr - (xr - xl) * 0.25, zb - bay * 0.25), w * 0.45, mat, T=T)
        else:
            member(d, M, (xl, za), (xr, zb), w * 0.45, mat, T=T)
            member(d, M, (xr, za), (xl, zb), w * 0.45, mat, T=T)
        member(d, M, (xl, zb), (xr, zb), w * 0.55, mat, T=T)
    t = T or (lambda p: p)
    for x in (xl, xr):
        G.stroke(d, t(box(x - w / 2, z0, x + w / 2, z1, seed=seed + int(x * 10) + 3, wob=0.003)), M[mat + "_f"], 0.0, cyclic=True)
    G.stroke(d, t(box(xr + w * 0.05, z0, xr + w / 2, z1, seed=seed + 7, wob=0.002)), M[mat + "_dp"], 0.0, cyclic=True)
    for x in (xl, xr):
        G.stroke(d, t(box(x - w / 2, z0, x + w / 2, z1, seed=seed + int(x * 10) + 3, wob=0.003)), M["ink"], O, cyclic=True)


def lamp_glow(d, M, x, z, lvl, r=0.07, col="red", seed=91):
    G.stroke(d, G.lumpy_ellipse(x, z, r * 2.6 * lvl + 0.02, r * 2.4 * lvl + 0.02, n=20, lump=0.03, seed=seed), M["halo2"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.95, n=14, seed=seed + 1), M[col], I, cyclic=True)
    if lvl > 0.5:
        G.stroke(d, G.lumpy_ellipse(x - r * 0.25, z + r * 0.25, r * 0.35, r * 0.3, n=8, seed=seed + 2), M["glow_core"], 0.0, cyclic=True)


def tuft(d, M, x, n, h, seed):
    rnd = random.Random(seed)
    for _i in range(n):
        a, hh, bx = rnd.uniform(-0.45, 0.45), h * rnd.uniform(0.6, 1.0), x + rnd.uniform(-0.06, 0.06)
        G.stroke(d, [(bx - 0.018, 0.0), (bx + hh * math.sin(a), hh * math.cos(a)), (bx + 0.018, 0.0)], M["green"], I, cyclic=True)


def stripes(d, M, x0, x1, z0, z1, step, mat="mustard_f"):
    x = x0
    while x + step * 0.9 < x1:
        G.stroke(d, [(x, z0), (x + step * 0.5, z0), (x + step * 0.9, z1), (x + step * 0.4, z1)], M[mat], 0.0, cyclic=True)
        x += step


# ---------------------------------------------------------------- the Survey Archive

def archive_door(d, M, k=0):
    lvl = BLINK[k]
    body = box(-1.82, 0.0, 1.82, 2.55, seed=101, wob=0.01, n=4)                         # a concrete bunker half in the ground
    G.stroke(d, body, M["off_sh"], 0.0, cyclic=True)
    G.stroke(d, box(1.42, 0.0, 1.82, 2.55, seed=102, wob=0.005), M["off_dp"], 0.0, cyclic=True)
    for z in (0.85, 1.7):                                                               # pour lines, cracks, weathering
        G.seam(d, [(-1.78, z), (-0.9, z + 0.01), (0.0, z - 0.01), (1.78, z + 0.005)], M["ink"])
    G.seam(d, [(-1.5, 2.25), (-1.38, 2.05), (-1.42, 1.9), (-1.3, 1.72)], M["ink"])
    G.seam(d, [(1.58, 0.62), (1.5, 0.44), (1.56, 0.3)], M["ink"])
    G.specks(d, [(-1.6, 1.2), (-0.7, 2.35), (1.2, 2.32), (1.66, 1.4), (-1.68, 0.4)], M["ink"])
    G.hatch(d, 1.62, 1.9, M["ink"], n=4, length=0.18, spacing=0.05, angle_deg=65, seed=103)
    G.stroke(d, body, M["ink"], O, cyclic=True)
    roof = [(-1.93, 2.5), (1.93, 2.5), (1.86, 2.84), (-1.86, 2.84)]                   # the roof slab, a hazard band on its edge
    G.stroke(d, roof, M["off_f"], 0.0, cyclic=True)
    G.stroke(d, [(-1.93, 2.5), (1.93, 2.5), (1.92, 2.58), (-1.92, 2.58)], M["off_dp"], 0.0, cyclic=True)
    stripes(d, M, -1.82, 1.82, 2.61, 2.75, 0.24)
    G.seam(d, [(-1.88, 2.61), (1.88, 2.61)], M["ink"])
    G.seam(d, [(-1.87, 2.75), (1.87, 2.75)], M["ink"])
    G.stroke(d, roof, M["ink"], O, cyclic=True)
    dx0, dx1, dz1 = -1.15, 1.15, 2.02                                                   # the door in its dark recess
    recess = box(dx0 - 0.1, 0.0, dx1 + 0.1, dz1 + 0.1, seed=104)
    G.stroke(d, recess, M["iron_f"], 0.0, cyclic=True)
    door = box(dx0, 0.0, dx1, dz1, seed=105, wob=0.004)
    G.stroke(d, door, M["steel_f"], 0.0, cyclic=True)
    G.stroke(d, box(0.78, 0.0, dx1, dz1, seed=107, wob=0.002), M["steel_sh"], 0.0, cyclic=True)
    G.stroke(d, box(dx0, dz1 - 0.2, dx1, dz1, seed=106, wob=0.002), M["steel_dp"], 0.0, cyclic=True)   # the lintel's shadow
    for z in (0.62, 1.02, 1.42):                                                        # horizontal ribs, riveted
        G.stroke(d, box(dx0 + 0.03, z - 0.035, dx1 - 0.03, z + 0.035, seed=int(z * 10) + 110, wob=0.002), M["steel"], I, cyclic=True)
        G.rivets(d, [(dx0 + 0.15 + i * 0.37, z) for i in range(7)], M["ink"])
    stripes(d, M, dx0 + 0.04, dx1 - 0.02, 0.06, 0.3, 0.25)                             # chevrons at the foot
    G.seam(d, [(dx0, 0.32), (dx1, 0.32)], M["ink"])
    G.seam(d, [(-0.02, 0.34), (0.0, dz1 - 0.21)], M["ink"])                            # the two leaves meet
    G.stroke(d, box(0.36, 0.86, 0.52, 1.14, seed=108), M["mustard"], I, cyclic=True)  # one lever box, off centre
    G.stroke(d, [(0.44, 1.0), (0.6, 1.2)], M["red"], I)
    G.stroke(d, door, M["ink"], O, cyclic=True)
    G.stroke(d, recess, M["ink"], O, cyclic=True)
    plate = box(-0.62, 2.18, 0.62, 2.44, seed=109)                                      # the archive's plate: drawn lines, no letters
    G.stroke(d, plate, M["teal"], I, cyclic=True)
    G.stroke(d, [(-0.54, 2.23), (-0.44, 2.39), (-0.34, 2.23)], M["mustard"], I, cyclic=True)
    for i, w in enumerate((0.72, 0.5)):
        G.stroke(d, box(-0.24, 2.34 - i * 0.08 - 0.018, -0.24 + w, 2.34 - i * 0.08 + 0.018, seed=120 + i, wob=0.001, n=2), M["off_f"], 0.0, cyclic=True)
    G.stroke(d, box(1.44, 1.84, 1.66, 2.06, seed=112), M["iron"], I, cyclic=True)    # the status lamp, on one side
    lamp_glow(d, M, 1.55, 1.95, lvl, r=0.065)
    tuft(d, M, -1.62, 5, 0.22, 113)
    tuft(d, M, 1.66, 4, 0.18, 114)


def archive_terminal(d, M, k=0):
    G.stroke(d, G.hose_outline(G.bezier((-0.3, 0.9), (-0.62, 0.8), (-0.62, 0.2), (-0.5, 0.0), n=10), 0.035), M["iron"], I, cyclic=True)
    G.stroke(d, box(-0.42, 0.0, 0.42, 0.12, seed=201), M["iron"], O, cyclic=True)     # plinth
    body = box(-0.36, 0.12, 0.36, 1.2, seed=202)
    G.stroke(d, body, M["steel_f"], 0.0, cyclic=True)
    G.stroke(d, box(0.2, 0.12, 0.36, 1.2, seed=203, wob=0.002), M["steel_sh"], 0.0, cyclic=True)
    G.stroke(d, box(-0.27, 0.24, 0.14, 0.84, seed=204), M["teal"], I, cyclic=True)    # service panel
    G.rivets(d, [(-0.21, 0.3), (0.08, 0.3), (-0.21, 0.78), (0.08, 0.78)], M["ink"])
    for z in (0.94, 1.01, 1.08):                                                        # vents
        G.seam(d, [(-0.26, z), (0.06, z)], M["ink"])
    G.stroke(d, G.lumpy_ellipse(0.27, 0.55, 0.032, 0.032, n=10, seed=205), M["green"] if k in (0, 1) else M["mustard"], I, cyclic=True)
    G.stroke(d, body, M["ink"], O, cyclic=True)
    ledge = [(-0.42, 1.18), (0.54, 1.18), (0.58, 1.26), (-0.4, 1.26)]                  # the key ledge
    G.stroke(d, ledge, M["mustard"], I, cyclic=True)
    for x in (-0.26, -0.11, 0.04, 0.19, 0.34):
        G.seam(d, [(x, 1.2), (x + 0.04, 1.245)], M["ink"])
    head = [(-0.38, 1.26), (0.42, 1.26), (0.3, 1.9), (-0.4, 1.9)]                      # the slanted head
    G.stroke(d, head, M["steel_f"], 0.0, cyclic=True)
    G.stroke(d, [(0.22, 1.26), (0.42, 1.26), (0.3, 1.9), (0.16, 1.9)], M["steel_sh"], 0.0, cyclic=True)
    G.stroke(d, head, M["ink"], O, cyclic=True)
    zb, zt = 1.34, 1.82
    xr = lambda z: 0.29 - 0.09 * (z - zb) / (zt - zb)  # noqa: E731
    scr = [(-0.31, zb), (xr(zb), zb), (xr(zt), zt), (-0.32, zt)]
    G.stroke(d, scr, M["teal_dp"], 0.0, cyclic=True)
    for i, w in enumerate((0.36, 0.24, 0.3, 0.14)):                                    # drawn text lines (no letters)
        z = 1.72 - i * 0.1
        G.stroke(d, box(-0.25, z - 0.018, -0.25 + w, z + 0.018, seed=210 + i, wob=0.001, n=2), M["teal_f"], 0.0, cyclic=True)
    if k % 2 == 0:                                                                      # the cursor blinks
        G.stroke(d, box(-0.07, 1.402, -0.03, 1.438, seed=215, wob=0.0, n=2), M["glow_core"], 0.0, cyclic=True)
    sz = zb + 0.04 + (zt - zb - 0.08) * SCAN[k]                                        # the scan band sweeps up
    G.stroke(d, [(-0.31, sz - 0.03), (xr(sz - 0.03), sz - 0.03), (xr(sz + 0.03), sz + 0.03), (-0.31, sz + 0.03)], M["halo"], 0.0, cyclic=True)
    G.stroke(d, scr, M["ink"], I, cyclic=True)
    member(d, M, (0.18, 1.9), (0.22, 1.98), 0.02, "iron")                               # an antenna stub
    G.stroke(d, G.lumpy_ellipse(0.225, 2.0, 0.026, 0.024, n=8, seed=216), M["red"], I, cyclic=True)


def beacon(d, M, k=0):
    lvl = BLINK[k]
    base = box(-0.3, 0.0, 0.3, 0.26, seed=301)
    G.stroke(d, base, M["off_sh"], 0.0, cyclic=True)
    G.stroke(d, box(0.14, 0.0, 0.3, 0.26, seed=302, wob=0.002), M["off_dp"], 0.0, cyclic=True)
    stripes(d, M, -0.28, 0.28, 0.04, 0.14, 0.14)
    G.stroke(d, base, M["ink"], O, cyclic=True)
    for s in (-1, 1):                                                                   # braces from the block to the mast
        member(d, M, (0.24 * s, 0.26), (0.04 * s, 1.0), 0.018, "iron")
    mast = G.hose_outline([(0.0, 0.26), (0.0, 1.4), (0.0, 2.6)], 0.05)
    G.stroke(d, mast, M["teal_f"], 0.0, cyclic=True)
    G.stroke(d, G.hose_outline([(0.012, 0.26), (0.012, 2.6)], 0.018), M["teal_sh"], 0.0, cyclic=True)
    for z in (0.7, 1.3, 1.9):
        G.stroke(d, box(-0.045, z - 0.03, 0.045, z + 0.03, seed=int(z * 10) + 303), M["mustard"], I, cyclic=True)
    G.stroke(d, mast, M["ink"], O, cyclic=True)
    member(d, M, (0.0, 2.2), (0.15, 2.2), 0.02, "iron")                                 # a horn antenna, facing right
    G.stroke(d, [(0.14, 2.13), (0.2, 2.15), (0.32, 2.09), (0.32, 2.31), (0.2, 2.25), (0.14, 2.27)], M["mustard"], I, cyclic=True)
    G.stroke(d, box(-0.08, 2.6, 0.08, 2.66, seed=310), M["iron"], I, cyclic=True)    # the caged lamp
    lamp_glow(d, M, 0.0, 2.75, lvl, r=0.06, seed=95)
    for x in (-0.065, 0.0, 0.065):
        G.seam(d, [(x, 2.67), (x * 0.7, 2.84)], M["ink"])
    G.stroke(d, G.lumpy_ellipse(0.0, 2.86, 0.035, 0.022, n=8, seed=311), M["iron"], I, cyclic=True)
    tuft(d, M, -0.24, 3, 0.14, 312)


# ---------------------------------------------------------------- the Launch Complex

def service_arm(d, M, x0, x1, z, h=0.42, mat="red"):
    zt, zb = z + h / 2, z - h / 2
    for i in range(4):
        xa, xb = x0 + (x1 - x0) * i / 4, x0 + (x1 - x0) * (i + 1) / 4
        member(d, M, (xa, zb), (xb, zt), 0.035, mat)
    member(d, M, (x0, zt), (x1, zt), 0.06, mat)
    member(d, M, (x0, zb), (x1, zb), 0.06, mat)
    G.stroke(d, box(x1 - 0.06, zb - 0.04, x1 + 0.06, zt + 0.04, seed=int(z * 7)), M["iron"], I, cyclic=True)
    G.stroke(d, G.hose_outline(G.bezier((x1 - 0.04, zb), (x1 + 0.12, zb - 0.8), (x1 - 0.22, zb - 1.4), (x1 - 0.4, zb - 1.9), n=14), 0.04),
             M["iron"], I, cyclic=True)                                                 # the umbilical hanging off its tip


def launch_gantry(d, M, k=0):
    pad = box(-2.0, 0.0, 1.6, 0.35, seed=401, wob=0.008)
    G.stroke(d, pad, M["off_sh"], 0.0, cyclic=True)
    G.stroke(d, box(-2.0, 0.0, 1.6, 0.1, seed=402, wob=0.003), M["off_dp"], 0.0, cyclic=True)
    stripes(d, M, -1.95, 1.55, 0.2, 0.33, 0.3)
    G.stroke(d, pad, M["ink"], O, cyclic=True)
    for x in (-1.6, 0.9):
        G.seam(d, [(x, 0.35), (x + 0.06, 0.2), (x + 0.02, 0.1)], M["ink"])
    xl, xr = -1.2, 0.4
    truss(d, M, xl, xr, 0.35, 13.0, 1.1, "teal", seed=403)
    for z in (0.55, 0.8):                                                               # hazard collars on the legs
        for x in (xl, xr):
            G.stroke(d, box(x - 0.075, z - 0.06, x + 0.075, z + 0.06, seed=int(z * 20 + x * 10) + 404), M["mustard"], I, cyclic=True)
    cage = box(-1.06, 3.2, 0.26, 4.35, seed=405)                                        # the elevator cage
    G.stroke(d, cage, M["mustard_f"], 0.0, cyclic=True)
    G.stroke(d, box(0.06, 3.2, 0.26, 4.35, seed=406, wob=0.002), M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, box(-1.06, 3.55, 0.26, 3.68, seed=407, wob=0.002), M["red_f"], 0.0, cyclic=True)
    G.stroke(d, box(-0.8, 3.82, -0.2, 4.2, seed=408), M["glass"], I, cyclic=True)
    G.stroke(d, cage, M["ink"], O, cyclic=True)
    member(d, M, (-0.4, 4.35), (-0.4, 12.95), 0.025, "iron")                           # its cable
    service_arm(d, M, xr + 0.05, 2.25, 6.6)
    service_arm(d, M, xr + 0.05, 2.1, 10.4)
    deck = box(-1.45, 12.95, 0.75, 13.12, seed=409)                                     # the railed top, an aviation lamp
    G.stroke(d, deck, M["iron"], O, cyclic=True)
    for x in (-1.4, -0.7, 0.0, 0.7):
        member(d, M, (x, 13.12), (x, 13.48), 0.025, "teal")
    member(d, M, (-1.42, 13.48), (0.72, 13.48), 0.03, "teal")
    member(d, M, (-0.35, 13.12), (-0.35, 13.66), 0.035, "iron")
    lamp_glow(d, M, -0.35, 13.74, 1.0, r=0.06, seed=97)
    G.specks(d, [(xl + 0.02, 2.2), (xr - 0.01, 5.1), (xl - 0.01, 8.3), (xr + 0.02, 11.6), (1.2, 6.45), (-1.7, 0.27)], M["ink"])
    tuft(d, M, -1.85, 4, 0.2, 410)
    tuft(d, M, 1.45, 3, 0.16, 411)


def launch_tower_ruin(d, M, k=0):
    rnd = random.Random(501)
    pad = [(-1.7, 0.0), (1.5, 0.0), (1.5, 0.22), (1.1, 0.3), (0.6, 0.26), (0.2, 0.3), (-1.0, 0.3), (-1.3, 0.2), (-1.7, 0.26)]
    G.stroke(d, pad, M["off_sh"], 0.0, cyclic=True)                                     # cracked footing, a chunk gone
    G.stroke(d, pad, M["ink"], O, cyclic=True)
    G.seam(d, [(-0.4, 0.3), (-0.34, 0.16), (-0.42, 0.04)], M["ink"])
    xl, xr = -0.9, 0.5
    for x in (xl, xr):                                                                  # vines up the legs (behind)
        pts = [(x + 0.09 * math.sin(z * 4.0 + x * 3), z) for z in [0.3 + i * 0.12 for i in range(26)]]
        G.stroke(d, G.hose_outline(pts, 0.018), M["green"], I, cyclic=True)
    truss(d, M, xl, xr, 0.3, 5.2, 1.0, "red", seed=502, broken=(1, 3))
    T = rot(-24.0, xr, 5.2)                                                             # the upper section, bent over at 5.2 m
    truss(d, M, xl, xr, 5.2, 8.3, 1.0, "red", seed=503, broken=(2,), T=T)
    member(d, M, (xl, 5.2), T([(xl, 5.2)])[0], 0.1, "red", O)                           # the torn left chord
    for x in (xl, xr):                                                                  # snapped tops: jagged ends
        tx, tz = T([(x, 8.3)])[0]
        G.stroke(d, [(tx - 0.07, tz - 0.02), (tx - 0.02, tz + 0.12), (tx + 0.02, tz + 0.04), (tx + 0.06, tz + 0.1), (tx + 0.07, tz - 0.02)],
                 M["red"], I, cyclic=True)
    cx, cz = T([(xr, 7.6)])[0]                                                          # a cable dangling from the bend
    G.stroke(d, G.hose_outline(G.bezier((cx, cz), (cx + 0.2, cz - 1.2), (cx - 0.15, cz - 2.4), (cx - 0.05, 3.8), n=16), 0.03),
             M["iron"], I, cyclic=True)
    for i in range(10):                                                                 # leaves on the vines
        x = (xl if i % 2 else xr) + rnd.uniform(-0.12, 0.12)
        G.stroke(d, G.lumpy_ellipse(x, 0.5 + i * 0.3, 0.06, 0.035, n=10, lump=0.1, seed=510 + i), M["green"], I, cyclic=True)
    Tf = rot(4.0, 1.2, 0.3)                                                             # a fallen section at its foot
    for a, b in (((0.72, 0.36), (1.86, 0.36)), ((0.72, 0.74), (1.8, 0.74))):
        member(d, M, a, b, 0.08, "red", O, T=Tf)
    for xa in (0.75, 1.1, 1.45):
        member(d, M, (xa, 0.36), (xa + 0.33, 0.74), 0.035, "red", T=Tf)
    for i, (x, r) in enumerate(((-1.45, 0.14), (-1.15, 0.09), (1.3, 0.12), (-0.25, 0.08))):   # rubble
        G.stroke(d, G.lumpy_ellipse(x, r * 0.8, r * 1.3, r, n=12, lump=0.12, seed=520 + i), M["off"], I, cyclic=True)
    G.specks(d, [(xl, 1.7), (xr, 3.3), (xl + 0.05, 4.6), (-0.2, 0.15), (1.0, 0.2)], M["ink"])
    tuft(d, M, -1.55, 5, 0.22, 530)
    tuft(d, M, 0.3, 4, 0.18, 531)


# name -> (fn, frame w, frame h, clip name, frame count, tiles)
PROPS = {
    "archive_door": (archive_door, 256, 208, "blink", 4, False),
    "archive_terminal": (archive_terminal, 96, 144, "scan", 4, False),
    "beacon": (beacon, 52, 208, "blink", 4, False),
    "launch_gantry": (launch_gantry, 320, 912, None, 1, False),
    "launch_tower_ruin": (launch_tower_ruin, 256, 592, None, 1, False),
}
INTERACTABLE = ("archive_door", "archive_terminal")
LOOPS = {"blink": True, "scan": True}
V2_SUFFIXES = (".glb", "_normal.png", "_mask.png", "_emission.png")   # the v2 model + maps each key loses (D-117); .meta = UNITY's
POI = {   # PoiCatalog (dx, dy) per prop, for the review's assembly
    "survey_archive": [("beacon", 3.0, 0.0), ("archive_door", 10.0, 0.0), ("archive_terminal", 14.0, -6.0)],
    "coastal_launch_complex": [("launch_gantry", 10.0, 1.0), ("launch_tower_ruin", 24.0, 1.0)],
}


def pivot_of(name):
    _fn, _fw, fh, _clip, _n, _tiles = PROPS[name]
    return (0.5, GROUND_PX / fh)


def render_prop(name, k=0, seed=7):
    fn, fw, fh, _clip, _n, _tiles = PROPS[name]
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    fn(d, M, k)
    st = fakegp.strokes_of(d, gp)
    return GR.render_frame(st, fw, fh, PPU, pivot_of(name), ss=4, seed=seed)


def render_all():
    imgs, widths = {}, {}
    for name, (_fn, _fw, _fh, _clip, n, _tiles) in PROPS.items():
        imgs[name], widths[name] = [], []
        for k in range(n):
            img, w = render_prop(name, k)
            imgs[name].append(img)
            widths[name] += w
    return imgs, widths


def v2_leftovers(art, names=None):
    d = os.path.join(art, "props", "earth")
    return [os.path.join(d, n + s) for n in (names or PROPS) for s in V2_SUFFIXES if os.path.isfile(os.path.join(d, n + s))]


def sheet_meta(name, frames):
    import numpy as np
    _fn, fw, fh, clip, n, _tiles = PROPS[name]
    g = v3.GUTTER
    cols = PC.columns_within(fw, fh, n, cap=SHEET_CAP)
    rows = -(-n // cols)
    sheet = np.zeros((rows * fh + (rows - 1) * g, min(cols, n) * fw + (min(cols, n) - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw] = im
    px, py = pivot_of(name)
    anims = [{"name": clip, "start": 0, "length": n, "loop": True, "loop_from": 0}] if clip else []
    meta = {"key": KEY.format(name), "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": g,
            "frames": n, "fps": v3.FPS, "pivot": [round(px, 6), round(py, 6)], "facing": "right", "ppu": PPU,
            "animations": anims, "squash_root": False, "ground_line_px": GROUND_PX,
            "note": ("B-195: replaces the v2 model (D-117); " + ("one static frame; the pivot sits on the ground line" if not clip
                     else f"frame 0 = at rest; {clip} loops (idle)") + (" (LEAD 14:2x: full density, an exception to B-131's 512^2)"
                                                                         if fh > 512 else ""))}
    if name in INTERACTABLE:
        meta["interactable"] = True
    problems = [p for p in v3.validate_sheet(meta, sheet.shape) if not (not clip and "sum of clip lengths" in p)]
    m = v3.EDGE_MARGIN
    for i, im in enumerate(frames):
        a = im[..., 3]
        if a[:m].any() or a[-m:].any() or a[:, :m].any() or a[:, -m:].any():
            problems.append(f"frame {i} touches the {m} px frame edge")
    hit, off = v3.palette_hits(sheet, "earth")
    if hit < 0.98:
        problems.append(f"palette {hit * 100:.1f}% (off {' '.join(off[:3])})")
    return sheet, meta, problems


def export(art, imgs=None, names=None):
    """Writes props/earth/<prop>_color.png + <prop>.json and removes each key's v2 model files (.glb + normal / mask /
    emission) in the same run. Raises before writing anything if a check fails. -> [(key, w, h, bytes)], {}, removed."""
    import json
    from meridian import pngio
    names = list(names or PROPS)
    if imgs is None:
        imgs, _w = render_all()
    built, problems = [], []
    for name in names:
        sheet, meta, p = sheet_meta(name, imgs[name])
        problems += [f"{name}: {x}" for x in p]
        built.append((name, sheet, meta))
    if problems:
        raise ValueError("B-195 export checks: " + "; ".join(problems))
    d = os.path.join(art, "props", "earth")
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


# ---------------------------------------------------------------- the review

def main(out, imgs=None, widths=None, stamp_paths=()):
    """Both POIs assembled at 1x on the plains band (PoiCatalog's dx / dy; the terminal in a chamber 6 m down, as UNITY
    stamps it), the surveyor for scale, every clip frame at 1x, the checks."""
    import json
    import time
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    if imgs is None:
        imgs, widths = render_all()
    ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art")
    E = os.path.join(ART, "terrain", "earth")
    band = pngio.read_png_np(os.path.join(E, "ground_band_color.png"))
    fill = pngio.read_png_np(os.path.join(E, "ground_fill_color.png"))[..., :3].astype(np.float32) / 255.0
    sky = np.array(v3.hex_rgb(P["sky"]), np.float32) / 255.0
    try:
        sm = json.load(open(os.path.join(ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
        sv = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))[:sm["frame_height"], :sm["frame_width"]]
    except (OSError, KeyError, ValueError):
        sm = sv = None
    Wt = 1408

    def scene(width, ground, height):
        img = np.empty((height, width, 3), np.float32)
        img[:ground] = sky
        img[ground:] = np.tile(fill, (-(-(height - ground) // fill.shape[0]), -(-width // fill.shape[1]), 1))[:height - ground, :width]
        bt = np.tile(band, (1, -(-width // band.shape[1]), 1))[:, :width]
        review._over(img, bt, 0, ground - 24)
        return img

    def put(img, name, x, ground, k=0):
        fr = imgs[name][k]
        h, w = fr.shape[:2]
        review._over(img, fr, int(round(x - w / 2)), ground - (h - GROUND_PX))

    rows = []
    # the Survey Archive: origin 1 m in, the terminal 6 m down in a dug chamber
    ga, Ha, x0 = 260, 720, 64
    A = scene(Wt, ga, Ha)
    tx = x0 + 14 * PPU
    cf = ga + 6 * PPU
    A[cf - 150:cf + 6, tx - 110:tx + 110] = A[cf - 150:cf + 6, tx - 110:tx + 110] * 0.35 + np.array(v3.hex_rgb(P["brown"]), np.float32) / 255.0 * 0.25
    for name, dx, dy in POI["survey_archive"]:
        put(A, name, x0 + dx * PPU, ga - int(dy * PPU))
    if sv is not None:
        review._over(A, sv, x0 + 6 * PPU - sm["frame_width"] // 2, ga - sm["frame_height"] + int(round(sm["pivot"][1] * sm["frame_height"])) + 2)
    rows += [PC_lab(review, "SURVEY ARCHIVE at 1x (Earth x 184; PoiCatalog dx / dy): beacon dx 3, archive_door dx 10, archive_terminal dx 14 "
                    "6 m down in the archive's chamber (darkened here as UNITY's stamp cuts it); the surveyor for scale", Wt), A]
    # the Launch Complex: dx 5 .. 27 m shown; PoiCatalog's dy 1 m noted (drawn on the ground line here)
    gb, Hb, x0b = 950, 1060, -5 * PPU
    B = scene(Wt, gb, Hb)
    for name, dx, _dy in POI["coastal_launch_complex"]:
        put(B, name, x0b + dx * PPU, gb)
    if sv is not None:
        review._over(B, sv, x0b + 15 * PPU - sm["frame_width"] // 2, gb - sm["frame_height"] + int(round(sm["pivot"][1] * sm["frame_height"])) + 2)
    rows += [PC_lab(review, "LAUNCH COMPLEX at 1x (Earth x 2048): launch_gantry dx 10, launch_tower_ruin dx 24 (PoiCatalog dy 1 m: "
                    "UNITY's stamp; drawn on the ground line here); the surveyor for scale", Wt), B]
    # every clip frame at 1x
    C = np.empty((2 * 240, Wt, 3), np.float32)
    C[:] = review.PAPER
    x, y = 8, 0
    for name in ("archive_door", "archive_terminal", "beacon"):
        _fn, fw, fh, clip, n, _t = PROPS[name]
        if x + n * (fw + 6) > Wt - 8:                                                   # wrap to the second row
            x, y = 8, y + 240
        review._label(C, f"{name} {clip} {n} (1x)", x, y + 6, scale=1)
        for k in range(n):
            C[y + 24:y + 24 + fh, x:x + fw] = sky
            review._over(C, imgs[name][k], x, y + 24)
            x += fw + 6
        x += 24
    rows += [PC_lab(review, "the idle clips, every frame at 1x", Wt), C]
    lines = []
    for name, frames in imgs.items():
        _fn, fw, fh, clip, n, _t = PROPS[name]
        ws = widths.get(name, []) if widths else []
        o = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
        n_ = [w for w in ws if w[0] < v3.OUTER_SPLIT]
        rng = lambda q: f"{min(w[1] for w in q):.1f}-{max(w[2] for w in q):.1f}" if q else "-"  # noqa: E731
        m = v3.EDGE_MARGIN
        edge = [i for i, f in enumerate(frames) if f[..., 3][:m].any() or f[..., 3][-m:].any() or f[..., 3][:, :m].any() or f[..., 3][:, -m:].any()]
        pal = min(v3.palette_hits(f, "earth")[0] for f in frames) * 100
        lines.append(f"{name}: {fw}x{fh} x {n} ({clip or 'static'}), ink {rng(o)} / {rng(n_)} px, palette {pal:.1f}%"
                     + (f"; EDGE {edge}" if edge else "; inside the edge margin"))
    for p in stamp_paths:
        lines.append("exported " + review.stamp_text(p) + "  " + os.path.relpath(p, ART).replace(os.sep, "/"))
    foot = np.empty((30 + 16 * len(lines), Wt, 3), np.float32)
    foot[:] = review.PAPER
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack([PC_lab(review, "B-195: the five Earth POI props as v3 sheets (camp-props style, no faces), replacing the grey v2 models", Wt, 26)] + rows + [foot])
    del rows, A, B
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + ("exported" if stamp_paths else "design preview (lock-free, fakegp + numpy)"),
                2, img.shape[0] - 16, (1.0, 1.0, 0.85))
    np.clip(img, 0.0, 1.0, out=img)
    u8 = np.empty(img.shape[:2] + (4,), np.uint8)
    u8[..., :3] = np.rint(img * 255.0)
    u8[..., 3] = 255
    pngio.write_png(out, u8)
    print("written", out, u8.shape[1], "x", u8.shape[0])
    for ln in lines:
        print(ln)


def PC_lab(review, text, width, h=22):
    import numpy as np
    r = np.empty((h, width, 3), np.float32)
    r[:] = review.PAPER
    review._label(r, text[:int(width / 6)], 4, 6, scale=1)
    return r


if __name__ == "__main__":
    main(sys.argv[1])
    fakegp.restore()
