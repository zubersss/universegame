"""B-142 (D-126): Mars props as v3.1 prop sheets (colour + json only), drawn with gp_draw strokes through fakegp and the
numpy raster, the same API as build_props_common_v3 so render.py's do_prop_sheet_set exports a row that names this
generator. Props:

  tube_mound  104x32, 1 static frame: the lava-tube lurker's den, a low lumpy rust boulder (cracks, specks, pebbles)
              whose base sinks 0.06 m into the ground strip. UNITY draws it IN FRONT of creatures/mars/tube_lurker on the same
              pivot (the den's mouth is behind its top line; D-126: creature art never contains terrain or props). Its
              top line is build_creatures_mars_v3.mound_dome, the line the lurker's paws rest on.

  B-144 (designs; nothing exports until a Mars props export card, then each replaces its v2 model under the same key, D-117):
  ice_drill_rig    124x252, working 8: an A-frame ice derrick on a skid, the drill head pumps, the pulley turns, frost chips
                   puff from the collar; one status lamp (interactable). 1.9 x 3.7 m: narrower than the v2 model (3.2 x 4.4 m)
                   so the 8 frames fit one 512^2 sheet.
  meridian_beacon  136x224, pulse 4: the first beacon (story POI): a tripod, a brass base with the meridian emblem, a banded
                   mast, a caged lamp whose beam turns (interactable). 2.0 x 3.3 m.
  hauler_hull_a    232x168, static: the crashed Halcyon hauler's nose section, tilted in a sand drift, one cracked porthole.
  hauler_hull_b    248x208, static: its engine section, a bell nozzle, a torn front with ribs and hanging hoses.
  hauler_cargo     240x112, static: a cargo container with its door swung open, two Dray-part crates spilled (interactable).
  warden_pylon     80x248, hum 4: the Warden outpost's pylon (Bible: Wardens ring a bell, never shoot): an obelisk with a
                   brass bell that sways while hum rings spread; one lamp.

  python -I build_props_mars_v3.py <review png>     lock-free preview: every prop at 1x on the Mars strips beside the
                                                     surveyor, at 2x, the clips, the ten boxes, and the den (the lurker
                                                     behind the mound)
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_mars_v3 as CM  # noqa: E402  (gp_draw through fakegp outside Blender)
from meridian import fakegp, v3  # noqa: E402
import gp_raster as GR  # noqa: E402

G = CM.G
P = v3.PALETTES["mars"]
O, I = G.OUTER, G.INNER
PPU = 64
GROUND_PX = 10
KEY = "props/mars/{}"
SHEET_CAP = 512


def SH(h):
    return v3.shadow_of(h, "mars")


def DP(h):
    return v3.deep_of(h, "mars")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, f"mars_prop_{name}", **kw)
    M = {"rock": m("rock", fill=SH(P["red"]), ink=False), "rock_sh": m("rock_mid", fill=DP(P["red"]), ink=False),
         "rock_lit": m("rock_lit", fill=P["red"], ink=False), "pebble": m("pebble", fill=SH(P["sky"])),
         "ink": m("ink", fill=None)}
    for key, hx in (("off", P["offwhite"]), ("red", P["red"]), ("mustard", P["mustard"]), ("teal", P["teal"]),
                    ("olive", P["green"]), ("salmon", P["sky"]), ("umber", P["brown"])):
        M[key] = m(key, fill=hx)
        M[key + "_f"] = m(key + "_f", fill=hx, ink=False)
        M[key + "_sh"] = m(key + "_mid", fill=SH(hx), ink=False)
        M[key + "_dp"] = m(key + "_deep", fill=DP(hx), ink=False)
        M[key + "_b"] = m(key + "_behind", fill=hx, behind=True)          # thin parts: ink under the fill
    M["sand"] = m("sand", fill=SH(P["red"]), ink=False)
    M["sand_sh"] = m("sand_mid", fill=DP(P["red"]), ink=False)
    M["halo"] = m("halo", fill=P["offwhite"], ink=False, fill_alpha=0.30)
    M["halo2"] = m("halo2", fill=P["mustard"], ink=False, fill_alpha=0.25)
    M["puff"] = m("puff", fill=P["offwhite"])
    M["puff_sh"] = m("puff_mid", fill=SH(P["offwhite"]), ink=False)
    return M


def box(x0, z0, x1, z1, seed=0, wob=0.005, n=3):
    """A hand-drawn rectangle (build_props_common_v3's)."""
    rnd = random.Random(seed)
    pts = []
    for (ax, az), (bx, bz) in (((x0, z0), (x1, z0)), ((x1, z0), (x1, z1)), ((x1, z1), (x0, z1)), ((x0, z1), (x0, z0))):
        for i in range(n):
            t = i / n
            pts.append((ax + (bx - ax) * t + rnd.uniform(-wob, wob), az + (bz - az) * t + rnd.uniform(-wob, wob)))
    return pts


def rot(pts, deg, cx=0.0, cz=0.0, dx=0.0):
    """Rotate about (cx, cz), then shift dx (a tilted wreck kept inside its frame)."""
    a = math.radians(deg)
    c, s_ = math.cos(a), math.sin(a)
    return [(dx + cx + (x - cx) * c - (z - cz) * s_, cz + (x - cx) * s_ + (z - cz) * c) for x, z in pts]


def drift(d, M, x0, x1, humps, seed):
    """A regolith sand drift over a wreck's base: humps [(x, height, half width)]; ink along its top only."""
    xs = [x0 + (x1 - x0) * i / 40 for i in range(41)]
    top = [(x, 0.02 + max(h * math.exp(-((x - hx) / hw) ** 2) for hx, h, hw in humps) + 0.008 * math.sin(23 * x + seed)) for x in xs]
    G.stroke(d, top + [(x1, -0.04), (x0, -0.04)], M["sand"], 0.0, cyclic=True)
    G.stroke(d, [(x, z - 0.05) for x, z in top] + [(x1, -0.04), (x0, -0.04)], M["sand_sh"], 0.0, cyclic=True)
    G.stroke(d, top, M["ink"], O)
    rnd = random.Random(seed)
    G.specks(d, [(rnd.uniform(x0 + 0.1, x1 - 0.1), rnd.uniform(0.04, 0.12)) for _ in range(5)], M["ink"])


def lamp(d, M, x, z, lit, r=0.06):
    """The one light a prop may carry: a mustard bulb (lit: an off-white core and a drawn halo, no emission)."""
    if lit:
        G.stroke(d, G.lumpy_ellipse(x, z, r * 3.2, r * 3.0, n=16, lump=0.04, seed=71), M["halo2"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(x, z, r, r, n=12, seed=72), M["mustard"] if lit else M["mustard_dp"], I, cyclic=True)
    if lit:
        G.stroke(d, G.lumpy_ellipse(x - r * 0.3, z + r * 0.3, r * 0.35, r * 0.35, n=8, seed=73), M["off_f"], 0.0, cyclic=True)


# ---------------------------------------------------------------- ice drill rig (working 8)
def ice_drill_rig(d, M, k=0):
    ph = 2 * math.pi * k / 8
    bob = 0.12 * math.sin(ph)
    G.stroke(d, G.hose_outline([(0.0, 1.62 + bob), (0.0, 0.10)], 0.07), M["off_b"], O, cyclic=True)       # the drill string
    for z in (0.5, 0.9, 1.3):
        G.seam(d, [(-0.035, z + bob * (z > 1.0)), (0.035, z + bob * (z > 1.0))], M["ink"])
    xl = lambda z: 0.66 - 0.60 * (z - 0.16) / 3.2       # noqa: E731  (the legs' half span)
    for sx in (-1, 1):                                                                                     # A-frame legs
        G.stroke(d, G.hose_outline([(sx * 0.66, 0.16), (sx * 0.06, 3.36)], 0.10), M["teal"], O, cyclic=True)
        G.stroke(d, G.hose_outline([(sx * 0.66 + 0.02, 0.16), (sx * 0.06 + 0.02, 3.36)], 0.03), M["teal_sh"], 0.0, cyclic=True)
    for i, z in enumerate((0.85, 1.55, 2.25, 2.85)):                                                       # braces: rungs + X lattice
        G.stroke(d, box(-xl(z), z - 0.035, xl(z), z + 0.035, seed=10 + i), M["teal"], I, cyclic=True)
        if i < 3:
            z2 = (0.85, 1.55, 2.25, 2.85)[i + 1]
            G.stroke(d, [(-xl(z), z + 0.03), (xl(z2), z2 - 0.03)], M["ink"], I)
            G.stroke(d, [(xl(z), z + 0.03), (-xl(z2), z2 - 0.03)], M["ink"], I)
    G.stroke(d, box(-0.20, 3.30, 0.20, 3.48, seed=20), M["off"], O, cyclic=True)                            # crown block + pulley
    G.rivets(d, [(-0.12, 3.39), (0.12, 3.39)], M["ink"])
    G.stroke(d, G.lumpy_ellipse(0.0, 3.18, 0.15, 0.15, n=20, lump=0.01, seed=21), M["mustard"], O, cyclic=True)
    for j in range(3):                                                                                     # spokes turn
        a = ph * 0.5 + j * math.pi / 3
        G.stroke(d, [(0.11 * math.cos(a), 3.18 + 0.11 * math.sin(a)), (-0.11 * math.cos(a), 3.18 - 0.11 * math.sin(a))], M["ink"], I)
    G.stroke(d, [(0.15, 3.18), (0.16, 2.02 + bob)], M["ink"], I)                                           # the cable to the head
    hz = 1.62 + bob                                                                                       # drill head (motor)
    G.stroke(d, box(-0.24, hz, 0.24, hz + 0.40, seed=22), M["off"], O, cyclic=True)
    G.stroke(d, box(0.08, hz, 0.24, hz + 0.40, seed=22, wob=0.002), M["off_sh"], 0.0, cyclic=True)
    G.stroke(d, box(-0.24, hz + 0.16, 0.24, hz + 0.24, seed=23, wob=0.002), M["mustard_f"], 0.0, cyclic=True)
    G.seam(d, [(-0.24, hz + 0.16), (0.24, hz + 0.16)], M["ink"])
    G.seam(d, [(-0.24, hz + 0.24), (0.24, hz + 0.24)], M["ink"])
    G.stroke(d, box(-0.24, hz, 0.24, hz + 0.40, seed=22), M["ink"], O, cyclic=True)
    lamp(d, M, -0.13, hz + 0.32, lit=k % 4 < 2, r=0.045)                                                   # the one light: blinks
    G.stroke(d, box(-0.88, 0.0, 0.88, 0.18, seed=24), M["mustard"], O, cyclic=True)                        # skid base, hazard bands
    G.stroke(d, box(-0.88, 0.0, 0.88, 0.06, seed=24, wob=0.002), M["mustard_dp"], 0.0, cyclic=True)
    for i in range(6):
        x = -0.78 + 0.3 * i
        G.stroke(d, [(x, 0.07), (x + 0.08, 0.07), (x + 0.15, 0.17), (x + 0.07, 0.17)], M["umber_f"], 0.0, cyclic=True)
    G.stroke(d, box(-0.88, 0.0, 0.88, 0.18, seed=24), M["ink"], O, cyclic=True)
    G.stroke(d, box(-0.12, 0.18, 0.12, 0.30, seed=25), M["umber"], O, cyclic=True)                          # the collar
    G.stroke(d, box(0.30, 0.18, 0.84, 0.66, seed=26), M["off"], O, cyclic=True)                             # the pump box
    G.stroke(d, box(0.62, 0.18, 0.84, 0.66, seed=26, wob=0.002), M["off_sh"], 0.0, cyclic=True)
    G.hatch(d, 0.48, 0.44, M["ink"], n=3, length=0.12, spacing=0.035, angle_deg=90, seed=27)
    G.stroke(d, box(0.30, 0.18, 0.84, 0.66, seed=26), M["ink"], O, cyclic=True)
    G.stroke(d, box(-0.84, 0.18, -0.32, 0.30, seed=28), M["umber"], O, cyclic=True)                        # ice-core tray
    for i in range(3):
        G.stroke(d, G.lumpy_ellipse(-0.74 + 0.17 * i, 0.36, 0.075, 0.06, n=12, seed=29 + i), M["teal"], I, cyclic=True)
        G.seam(d, [(-0.78 + 0.17 * i, 0.38), (-0.72 + 0.17 * i, 0.34)], M["ink"])
    for j in range(2):                                                                                     # frost chips puff out
        t = ((k + 4 * j) % 8) / 8.0
        px, pz = (-0.18 if j else 0.2) * (0.5 + t), 0.34 + 0.32 * t
        r = 0.045 + 0.05 * t - 0.04 * max(0.0, t - 0.75) * 4
        if r > 0.02:
            puff = G.lumpy_ellipse(px, pz, r * 1.2, r, n=14, lump=0.12, seed=30 + j)
            G.stroke(d, puff, M["puff"], I, cyclic=True)
            G.stroke(d, [q for q in puff if q[1] < pz - r * 0.3] + [(px, pz - r * 0.3)], M["puff_sh"], 0.0, cyclic=True)


# ---------------------------------------------------------------- Meridian beacon (pulse 4)
def meridian_beacon(d, M, k=0):
    G.stroke(d, G.hose_outline([(0.10, 0.02), (0.02, 1.0)], 0.07), M["umber_dp"], I, cyclic=True)          # back strut
    for sx in (-1, 1):                                                                                     # tripod struts + feet
        G.stroke(d, G.hose_outline([(sx * 0.78, 0.05), (sx * 0.10, 1.0)], 0.08), M["umber_b"], O, cyclic=True)
        G.stroke(d, box(sx * 0.78 - 0.12, 0.0, sx * 0.78 + 0.12, 0.06, seed=40 + sx), M["umber"], I, cyclic=True)
    G.stroke(d, box(-0.36, 0.86, 0.36, 1.30, seed=42), M["mustard"], O, cyclic=True)                       # brass base
    G.stroke(d, box(0.14, 0.86, 0.36, 1.30, seed=42, wob=0.002), M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(-0.08, 1.08, 0.12, 0.12, n=20, lump=0.01, seed=43), M["ink"], I, cyclic=True)   # the meridian emblem
    G.seam(d, [(-0.08, 0.95), (-0.08, 1.21)], M["ink"])
    G.rivets(d, [(-0.3, 0.92), (0.3, 0.92), (-0.3, 1.24), (0.3, 1.24)], M["ink"])
    G.stroke(d, box(-0.36, 0.86, 0.36, 1.30, seed=42), M["ink"], O, cyclic=True)
    mast = [(-0.10, 1.30), (0.10, 1.30), (0.06, 2.72), (-0.06, 2.72)]                                      # the banded mast
    G.stroke(d, mast, M["off"], O, cyclic=True)
    G.stroke(d, [(0.03, 1.30), (0.10, 1.30), (0.06, 2.72), (0.02, 2.72)], M["off_sh"], 0.0, cyclic=True)
    for z in (1.6, 2.0, 2.4):
        w = 0.10 - 0.04 * (z - 1.3) / 1.42
        G.stroke(d, [(-w, z - 0.05), (w, z - 0.05), (w - 0.003, z + 0.05), (-w + 0.003, z + 0.05)], M["teal_f"], 0.0, cyclic=True)
        G.seam(d, [(-w, z - 0.05), (w, z - 0.05)], M["ink"])
        G.seam(d, [(-w, z + 0.05), (w, z + 0.05)], M["ink"])
    G.stroke(d, mast, M["ink"], O, cyclic=True)
    a = [0.0, 1.0, 0.0, -1.0][k % 4]                                                                       # the beam turns: right, out, left, away
    if abs(a) > 0.5:
        tip = 0.92 * a
        G.stroke(d, [(0.0, 2.92), (tip, 3.02), (tip, 2.72)], M["halo2"], 0.0, cyclic=True)
    halo = (0.34, 0.42, 0.34, 0.26)[k % 4]
    G.stroke(d, G.lumpy_ellipse(0.0, 2.9, halo, halo * 0.92, n=20, lump=0.04, seed=44), M["halo"], 0.0, cyclic=True)
    G.stroke(d, box(-0.17, 2.72, 0.17, 3.06, seed=45), M["mustard"], O, cyclic=True)                       # the lamp cage
    G.stroke(d, box(-0.11, 2.78, 0.11, 3.0, seed=46, wob=0.002), M["off_f"] if k % 4 == 1 else M["mustard_sh"], 0.0, cyclic=True)
    for x in (-0.06, 0.0, 0.06):
        G.stroke(d, [(x, 2.76), (x, 3.02)], M["ink"], I)
    G.stroke(d, box(-0.17, 2.72, 0.17, 3.06, seed=45), M["ink"], O, cyclic=True)
    cap = [q for q in G.lumpy_ellipse(0.0, 3.06, 0.2, 0.13, n=20, lump=0.02, seed=47) if q[1] >= 3.06]
    G.stroke(d, cap, M["umber"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, 3.2, 0.03, 0.03, n=8, seed=48), M["umber"], I, cyclic=True)


# ---------------------------------------------------------------- the crashed Halcyon hauler: hull a (nose), hull b (engine), cargo
def jag_edge(x, z0, z1, n, amp, seed):
    rnd = random.Random(seed)
    return [(x + (amp * (1 if i % 2 else -0.4) + rnd.uniform(-0.02, 0.02)), z1 - (z1 - z0) * i / n) for i in range(n + 1)]


def hauler_hull_a(d, M, k=0):
    T = 8.0
    torn = jag_edge(-1.55, 0.12, 1.92, 9, 0.07, 50)
    shell = [(-1.55, 0.12), (0.95, 0.12)] + G.bezier((0.95, 0.12), (1.72, 0.25), (1.66, 1.45), (0.90, 1.92), n=14)[1:] + [(-1.55, 1.92)] + torn[1:-1]
    sh = rot(shell, T, -1.55, 0.12, 0.12)
    G.stroke(d, rot([(-1.55, 0.12), (-1.40, 0.12), (-1.40, 1.92), (-1.55, 1.92)], T, -1.55, 0.12, 0.12), M["umber"], O, cyclic=True)   # the interior
    for z in (0.5, 0.95, 1.4):
        G.stroke(d, rot([(-1.52, z), (-1.42, z)], T, -1.55, 0.12, 0.12), M["ink"], I)                                          # rib stubs
    G.stroke(d, sh, M["mustard_f"], 0.0, cyclic=True)
    G.stroke(d, rot([(-1.55, 0.95), (1.47, 0.95), (1.44, 1.18), (-1.55, 1.18)], T, -1.55, 0.12, 0.12), M["off_f"], 0.0, cyclic=True)   # livery stripe (inside the nose)
    G.stroke(d, rot([(-1.55, 0.12), (0.95, 0.12), (1.21, 0.25), (1.39, 0.5), (-1.55, 0.5)], T, -1.55, 0.12, 0.12), M["mustard_sh"], 0.0, cyclic=True)
    for x, z, r in ((-1.1, 1.55, 0.16), (-0.9, 0.35, 0.12), (0.4, 1.65, 0.1)):                                           # rust weathering
        G.stroke(d, rot(G.lumpy_ellipse(x, z, r * 1.4, r, n=14, lump=0.15, seed=int(x * 10) + 60), T, -1.55, 0.12, 0.12), M["red_sh"], 0.0, cyclic=True)
    for x in (-0.75, 0.05):                                                                                                # panel seams + rivets
        G.seam(d, rot([(x, 0.14), (x, 1.9)], T, -1.55, 0.12, 0.12), M["ink"])
        G.rivets(d, rot([(x + 0.06, z) for z in (0.4, 0.8, 1.3, 1.7)], T, -1.55, 0.12, 0.12), M["ink"])
    G.seam(d, rot([(-1.25, 1.62), (-1.05, 1.48)], T, -1.55, 0.12, 0.12), M["ink"])                                          # straight creases by
    G.seam(d, rot([(-1.3, 0.78), (-1.08, 0.86)], T, -1.55, 0.12, 0.12), M["ink"])                                           # the torn edge (no curve: D-101)
    G.stroke(d, sh, M["ink"], O, cyclic=True)
    px, pz = rot([(0.95, 1.36)], T, -1.55, 0.12, 0.12)[0]                                                                       # the one porthole
    G.stroke(d, G.lumpy_ellipse(px, pz, 0.24, 0.24, n=24, lump=0.01, seed=61), M["off"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(px, pz, 0.16, 0.16, n=20, lump=0.01, seed=62), M["teal"], I, cyclic=True)
    G.seam(d, [(px - 0.10, pz + 0.08), (px - 0.01, pz - 0.01), (px + 0.03, pz - 0.11)], M["ink"])                         # crack
    G.rivets(d, [(px + 0.2 * math.cos(a), pz + 0.2 * math.sin(a)) for a in (0.4, 1.9, 3.4, 4.9)], M["ink"])
    drift(d, M, -1.70, 1.70, [(-1.2, 0.30, 0.45), (0.5, 0.42, 0.55), (1.45, 0.28, 0.3)], 63)


def hauler_hull_b(d, M, k=0):
    T = -6.0
    c = (0.0, 0.1)
    G.stroke(d, rot([(-1.25, 0.55), (-1.82, 0.22), (-1.82, 2.18), (-1.25, 1.85)], T, *c), M["red_sh"], O, cyclic=True)          # the bell nozzle
    G.stroke(d, rot([(-1.25, 0.55), (-1.82, 0.22), (-1.82, 0.62), (-1.25, 0.8)], T, *c), M["red_dp"], 0.0, cyclic=True)
    G.stroke(d, rot(G.lumpy_ellipse(-1.82, 1.2, 0.07, 0.96, n=24, lump=0.02, seed=70), T, *c), M["umber"], I, cyclic=True)
    for z in (0.7, 1.2, 1.7):
        G.seam(d, rot([(-1.3, 0.62 + (z - 0.62) * 0.95), (-1.78, 0.30 + (z - 0.3) * 1.0)], T, *c), M["ink"])
    torn = jag_edge(0.65, 0.12, 2.25, 10, 0.07, 71)
    body = [(-1.3, 0.12), (0.65, 0.12)] + torn[::-1][1:-1] + [(0.65, 2.25), (-1.3, 2.25)]
    G.stroke(d, rot([(0.48, 0.12), (0.65, 0.12), (0.65, 2.25), (0.48, 2.25)], T, *c), M["umber"], O, cyclic=True)
    G.stroke(d, rot(body, T, *c), M["mustard_f"], 0.0, cyclic=True)
    G.stroke(d, rot([(-1.3, 1.25), (0.65, 1.25), (0.65, 1.5), (-1.3, 1.5)], T, *c), M["off_f"], 0.0, cyclic=True)
    G.stroke(d, rot([(-1.3, 0.12), (0.65, 0.12), (0.65, 0.6), (-1.3, 0.6)], T, *c), M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, rot([(-1.3, 0.12), (-0.9, 0.12), (-0.9, 2.25), (-1.3, 2.25)], T, *c), M["mustard_dp"], 0.0, cyclic=True)
    for x in (-0.9, -0.2):
        G.seam(d, rot([(x, 0.14), (x, 2.23)], T, *c), M["ink"])
        G.rivets(d, rot([(x + 0.06, z) for z in (0.5, 1.0, 1.8)], T, *c), M["ink"])
    G.hatch(d, *rot([(-0.55, 0.45)], T, *c)[0], M["ink"], n=4, length=0.14, spacing=0.04, angle_deg=60, seed=72)
    for x, z, r in ((0.3, 1.9, 0.14), (-0.5, 0.4, 0.11)):
        G.stroke(d, rot(G.lumpy_ellipse(x, z, r * 1.4, r, n=14, lump=0.15, seed=73 + int(z * 10)), T, *c), M["red_sh"], 0.0, cyclic=True)
    G.stroke(d, rot(body, T, *c), M["ink"], O, cyclic=True)
    fin = [(-0.85, 2.25), (-0.15, 2.25), (-0.45, 2.92), (-0.75, 2.92)]                                                    # a stub fin
    G.stroke(d, rot(fin, T, *c), M["mustard"], O, cyclic=True)
    G.stroke(d, rot([(-0.85, 2.25), (-0.6, 2.25), (-0.68, 2.92), (-0.75, 2.92)], T, *c), M["mustard_dp"], 0.0, cyclic=True)
    for j, (z, col) in enumerate(((1.8, "teal"), (1.0, "red"))):                                                           # hanging hoses
        a0 = rot([(0.66, z)], T, *c)[0]
        G.stroke(d, G.hose_outline(G.bezier(a0, (a0[0] + 0.25, a0[1] - 0.2), (a0[0] + 0.2 + 0.1 * j, 0.32), n=8), 0.05), M[col + "_b"], I, cyclic=True)
    drift(d, M, -1.85, 1.2, [(-1.5, 0.34, 0.35), (-0.4, 0.44, 0.6), (0.85, 0.30, 0.35)], 74)


def hauler_cargo(d, M, k=0):
    G.stroke(d, box(-1.55, 0.04, 0.95, 1.38, seed=80), M["off_f"], 0.0, cyclic=True)                         # the container
    G.stroke(d, box(-1.55, 0.58, 0.95, 0.80, seed=81, wob=0.002), M["mustard_f"], 0.0, cyclic=True)          # Halcyon stripe
    G.stroke(d, box(-1.55, 0.04, 0.95, 0.30, seed=82, wob=0.002), M["off_sh"], 0.0, cyclic=True)
    for i in range(11):
        x = -1.45 + 0.22 * i
        G.seam(d, [(x, 0.08), (x, 1.34)], M["ink"])
    G.stroke(d, box(0.78, 0.06, 0.95, 1.36, seed=83, wob=0.002), M["umber_f"], 0.0, cyclic=True)            # the open end, dark
    G.stroke(d, box(-1.55, 0.04, 0.95, 1.38, seed=80), M["ink"], O, cyclic=True)
    door = [(0.95, 0.10), (1.38, -0.0 + 0.16), (1.38, 1.30), (0.95, 1.36)]                                   # the door swung open
    G.stroke(d, door, M["off"], O, cyclic=True)
    G.stroke(d, [(0.95, 0.58), (1.38, 0.62), (1.38, 0.82), (0.95, 0.80)], M["mustard_f"], 0.0, cyclic=True)
    G.seam(d, [(1.17, 0.18), (1.17, 1.30)], M["ink"])
    G.stroke(d, door, M["ink"], O, cyclic=True)
    for x0, w, h, sd in ((1.02, 0.42, 0.36, 84), (1.42, 0.36, 0.30, 85)):                                   # spilled crates
        G.stroke(d, box(x0, 0.0, x0 + w, h, seed=sd), M["red"], O, cyclic=True)
        G.stroke(d, box(x0 + w * 0.65, 0.0, x0 + w, h, seed=sd, wob=0.002), M["red_sh"], 0.0, cyclic=True)
        G.seam(d, [(x0 + 0.04, 0.04), (x0 + w - 0.04, h - 0.04)], M["ink"])
        G.seam(d, [(x0 + 0.04, h - 0.04), (x0 + w - 0.04, 0.04)], M["ink"])
        G.stroke(d, box(x0, 0.0, x0 + w, h, seed=sd), M["ink"], O, cyclic=True)
    gx, gz = 1.24, 0.42                                                                                    # a Dray-part gear on top
    gear = [(gx + (0.11 + 0.025 * (i % 2)) * math.cos(math.pi * i / 8), gz + (0.11 + 0.025 * (i % 2)) * math.sin(math.pi * i / 8)) for i in range(16)]
    G.stroke(d, gear, M["mustard"], I, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(gx, gz, 0.04, 0.04, n=8, seed=86), M["umber"], I, cyclic=True)
    drift(d, M, -1.80, -0.2, [(-1.62, 0.36, 0.35), (-0.9, 0.22, 0.45)], 87)


# ---------------------------------------------------------------- Warden pylon (hum 4)
def warden_pylon(d, M, k=0):
    ph = 2 * math.pi * k / 4
    G.stroke(d, box(-0.50, 0.0, 0.50, 0.24, seed=90), M["umber"], O, cyclic=True)                           # plinth
    G.stroke(d, box(-0.50, 0.0, 0.50, 0.08, seed=90, wob=0.002), M["umber_dp"], 0.0, cyclic=True)
    ob = [(-0.32, 0.24), (0.32, 0.24), (0.15, 2.92), (-0.15, 2.92)]                                         # the obelisk
    G.stroke(d, ob, M["off"], O, cyclic=True)
    G.stroke(d, [(0.12, 0.24), (0.32, 0.24), (0.15, 2.92), (0.05, 2.92)], M["off_sh"], 0.0, cyclic=True)
    for z0, z1 in ((0.5, 1.5), (1.75, 2.6)):                                                               # inset teal panels
        w0, w1 = 0.32 - 0.17 * (z0 - 0.24) / 2.68 - 0.08, 0.32 - 0.17 * (z1 - 0.24) / 2.68 - 0.08
        pnl = [(-w0, z0), (w0, z0), (w1, z1), (-w1, z1)]
        G.stroke(d, pnl, M["teal_f"], 0.0, cyclic=True)
        G.stroke(d, pnl, M["ink"], I, cyclic=True)
    G.rivets(d, [(-0.2, 0.36), (0.2, 0.36), (-0.12, 2.8), (0.12, 2.8)], M["ink"])
    G.stroke(d, ob, M["ink"], O, cyclic=True)
    for j in range(2):                                                                                     # hum rings spread from the bell
        r = 0.22 + 0.12 * ((k + 2 * j) % 4) / 4 + 0.08 * j
        for sx in (-1, 1):
            arc = [(sx * r * math.cos(a), 3.28 + r * math.sin(a)) for a in [(-0.6 + 1.2 * i / 8) for i in range(9)]]
            inner = [(sx * (r - 0.035) * math.cos(a), 3.28 + (r - 0.035) * math.sin(a)) for a in [(-0.6 + 1.2 * i / 8) for i in range(9)]]
            G.stroke(d, arc + inner[::-1], M["halo"], 0.0, cyclic=True)
    G.stroke(d, G.hose_outline(G.bezier((-0.17, 2.92), (-0.2, 3.62), (0.2, 3.62), (0.17, 2.92), n=12), 0.05), M["off_b"], I, cyclic=True)   # the arch
    sw = 5 * math.sin(ph)                                                                                  # the bell sways
    bell = G.bezier((-0.03, 3.48), (-0.10, 3.44), (-0.11, 3.24), (-0.16, 3.14), n=8) + [(0.0, 3.12)] +         G.bezier((0.16, 3.14), (0.11, 3.24), (0.10, 3.44), (0.03, 3.48), n=8)
    bell = rot(bell, sw, 0.0, 3.5)
    G.stroke(d, bell, M["mustard"], O, cyclic=True)
    G.stroke(d, [q for q in bell if q[0] > 0.02] + [rot([(0.02, 3.2)], sw, 0.0, 3.5)[0]], M["mustard_sh"], 0.0, cyclic=True)
    G.seam(d, rot([(-0.14, 3.18), (0.14, 3.18)], sw, 0.0, 3.5), M["ink"])
    lamp(d, M, *rot([(0.0, 3.08)], sw * 1.4, 0.0, 3.5)[0], lit=k % 2 == 0, r=0.035)                         # its one lamp, the clapper




def tube_mound(d, M, k=0):
    """The den: the shared top line, a base sunk 0.10 m into the ground (no ink along it), rust light on the upper left,
    mid tone low right, cracks + specks, two pebbles."""
    dome = CM.mound_dome()
    base = -0.06
    G.stroke(d, dome + [(dome[-1][0], base), (dome[0][0], base)], M["rock"], 0.0, cyclic=True)
    top_l = [q for q in dome if q[0] < CM.HOLE[0] - 0.05 and q[1] > 0.12]
    G.stroke(d, top_l + [(top_l[-1][0] + 0.06, top_l[-1][1] - 0.06), (top_l[0][0] + 0.10, 0.12)], M["rock_lit"], 0.0, cyclic=True)
    low_r = [q for q in dome if q[0] > CM.HOLE[0] + 0.12]
    G.stroke(d, low_r + [(low_r[-1][0], base), (low_r[0][0], base)], M["rock_sh"], 0.0, cyclic=True)
    for x, z, dx, dz in ((-0.32, 0.12, 0.06, -0.07), (0.24, 0.10, -0.04, -0.06), (-0.04, 0.05, 0.05, 0.04), (0.42, 0.04, 0.03, 0.05)):
        G.seam(d, [(x, z), (x + dx * 0.5 + 0.01, z + dz * 0.5), (x + dx, z + dz)], M["ink"])          # cracks
    G.specks(d, [(-0.42, 0.06), (0.36, 0.13), (0.06, 0.12), (-0.16, 0.17)], M["ink"])
    G.stroke(d, dome, M["ink"], O)
    for cx, rx, rz, sd in ((-0.66, 0.05, 0.03, 3), (0.70, 0.04, 0.025, 4)):                            # pebbles at the foot
        G.stroke(d, G.lumpy_ellipse(cx, rz * 0.6, rx, rz, n=12, lump=0.08, seed=sd), M["pebble"], I, cyclic=True)


PROPS = {"tube_mound": (tube_mound, 104, 32, None, 1, False),
         "ice_drill_rig": (ice_drill_rig, 124, 252, "working", 8, False),
         "meridian_beacon": (meridian_beacon, 136, 224, "pulse", 4, False),
         "hauler_hull_a": (hauler_hull_a, 232, 168, None, 1, False),
         "hauler_hull_b": (hauler_hull_b, 248, 208, None, 1, False),
         "hauler_cargo": (hauler_cargo, 240, 112, None, 1, False),
         "warden_pylon": (warden_pylon, 80, 248, "hum", 4, False)}
DEN_FOR = {"tube_mound": "creatures/mars/tube_lurker"}
INTERACTABLE = ("ice_drill_rig", "meridian_beacon", "hauler_cargo")         # ice mining, the story scan, salvage (Dray parts)
LOOPS = {"working": True, "pulse": True, "hum": True}
SELF = {   # BLENDER's self-checks per prop for the motion and idle boxes (the rest are measured)
    "tube_mound": ("static den (D-126); the lurker animates behind it", "static by D-126"),
    "ice_drill_rig": ("working 8: the drill head pumps 0.12 m, the pulley's spokes turn, frost chips puff from the collar, the lamp blinks",
                      "frame 0 at rest; working loops while mining"),
    "meridian_beacon": ("pulse 4: the lamp's beam turns (right, out, left, away), the halo breathes", "pulse loops always (a POI)"),
    "hauler_hull_a": ("static wreck (no clip on the card)", "static by the card"),
    "hauler_hull_b": ("static wreck (no clip on the card)", "static by the card"),
    "hauler_cargo": ("static wreck; interactable salvage", "static by the card"),
    "warden_pylon": ("hum 4: the bell sways 5 deg, hum rings spread, its lamp pulses", "hum loops always"),
}


def pivot_of(name):
    _fn, fw, fh, _clip, _n, _tiles = PROPS[name]
    return (0.5, GROUND_PX / fh)


def render_prop(name, k=0, seed=7):
    fn, fw, fh, _clip, _n, _tiles = PROPS[name]
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    fn(d, M, k)
    return GR.render_frame(fakegp.strokes_of(d, gp), fw, fh, PPU, pivot_of(name), ss=4, seed=seed)


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
    d = os.path.join(art, "props", "mars")
    return [os.path.join(d, n + s) for n in (names or PROPS) for s in (".glb", "_normal.png", "_mask.png", "_emission.png")
            if os.path.isfile(os.path.join(d, n + s))]


def columns_within(fw, fh, n, cap=SHEET_CAP, gutter=4):
    """The column count with the smallest sheet that fits cap x cap (ties: fewer rows)."""
    best = None
    for c in range(n, 0, -1):
        r = -(-n // c)
        w, h = c * fw + (c - 1) * gutter, r * fh + (r - 1) * gutter
        if w <= cap and h <= cap and (best is None or w * h < best[0]):
            best = (w * h, c)
    return best[1] if best else 1


def sheet_meta(name, frames):
    import numpy as np
    _fn, fw, fh, clip, n, _tiles = PROPS[name]
    g = v3.GUTTER
    cols = columns_within(fw, fh, n)
    rows = -(-n // cols)
    sheet = np.zeros((rows * fh + (rows - 1) * g, min(cols, n) * fw + (min(cols, n) - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw] = im
    px, py = pivot_of(name)
    anims = []
    if clip:
        anims.append({"name": clip, "start": 0, "length": n, "loop": LOOPS[clip], **({"loop_from": 0} if LOOPS[clip] else {})})
    meta = {"key": KEY.format(name), "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": g,
            "frames": n, "fps": v3.FPS, "pivot": [round(px, 6), round(py, 6)], "facing": "right", "ppu": PPU,
            "animations": anims, "squash_root": False, "ground_line_px": GROUND_PX,
            "note": "one static frame (no clip); the pivot sits on the ground line" if not clip else f"frame 0 = at rest; {clip} loops"}
    if name in INTERACTABLE:
        meta["interactable"] = True
    if name in DEN_FOR:
        meta["den_for"] = DEN_FOR[name]
        meta["note"] += f"; D-126: drawn in front of {DEN_FOR[name]} on the same pivot (the creature peeks over its top line)"
    problems = [p for p in v3.validate_sheet(meta, sheet.shape) if not (not clip and "sum of clip lengths" in p)]
    if sheet.shape[0] > SHEET_CAP or sheet.shape[1] > SHEET_CAP:
        problems.append(f"sheet {sheet.shape[1]}x{sheet.shape[0]} over {SHEET_CAP}^2")
    m = v3.EDGE_MARGIN
    for i, im in enumerate(frames):
        a = im[..., 3]
        if a[:m].any() or a[-m:].any() or a[:, :m].any() or a[:, -m:].any():
            problems.append(f"frame {i} touches the {m} px frame edge")
    return sheet, meta, problems


def export(art, imgs=None, names=None):
    """props/mars/<prop>_color.png + <prop>.json; raises before writing anything if a check fails."""
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
        raise ValueError("Mars prop export checks: " + "; ".join(problems))
    d = os.path.join(art, "props", "mars")
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


def den_frames(scale=2):
    """The lurker's idle + react frames (exact ids) with the mound composited IN FRONT, as UNITY will draw them."""
    import numpy as np
    sp = CM.SPECIES["tube_lurker"]
    fw, fh = sp["frame"]
    mound, _w = render_prop("tube_mound")
    mh, mw = mound.shape[:2]
    poses = sp["poses"]()
    out = []
    starts = {c: s for c, s in zip([c for c, _n, _l in sp["clips"]], np.cumsum([0] + [n for _c, n, _l in sp["clips"]]))}
    for clip in ("idle", "react"):
        n = dict((c, n) for c, n, _l in sp["clips"])[clip]
        for f in range(starts[clip], starts[clip] + n):
            gp = fakegp.FakeGP()
            M = sp["mats"](gp, "tube_lurker")
            d = fakegp.FakeDrawing()
            sp["draw"](d, M, poses[f], seed=5 * f)
            img, _w = GR.render_frame(fakegp.strokes_of(d, gp, as_object=("tube_lurker", "art")), fw, fh, 64, (0.5, 0.0), ss=4,
                                      seed=sp["seed"] * 1000 + f + 1)
            # the canvas: the creature frame with GROUND_PX of room below its pivot, the mound's pivot on the same point
            H = fh + GROUND_PX
            c = np.zeros((H, fw, 4), np.float32)
            c[:fh] = img.astype(np.float32) / 255
            x0, y0 = fw // 2 - mw // 2, H - mh
            mf = mound.astype(np.float32) / 255
            reg = c[y0:y0 + mh, x0:x0 + mw]
            a = mf[..., 3:]
            reg[..., :3] = mf[..., :3] * a + reg[..., :3] * (1 - a)
            reg[..., 3:] = a + reg[..., 3:] * (1 - a)
            out.append((clip, f - starts[clip], c))
    return out


def den_review(out, imgs=None, widths=None, stamp_paths=()):
    """Review: the mound at 3x with its measured ink + palette, then the den (lurker idle + react behind the mound) at 2x."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    if imgs is None:
        imgs, widths = render_all()
    sheet, meta, problems = sheet_meta("tube_mound", imgs["tube_mound"])
    hits, off = v3.palette_hits(sheet, "mars")
    ws = widths["tube_mound"]
    outer = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in ws if w[0] < v3.OUTER_SPLIT]
    W = 1700
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, f"review props/mars/tube_mound (b-142, d-126)  104x32  pivot {meta['pivot']}  ink {min(w[1] for w in outer):.2f}-"
                        f"{max(w[2] for w in outer):.2f} / {min(w[1] for w in inner):.2f}-{max(w[2] for w in inner):.2f} px  "
                        f"mars palette {hits * 100:.1f}%  json {'valid' if not problems else '; '.join(problems)}", 6, 8)
    big = sheet.repeat(3, 0).repeat(3, 1)
    r1 = np.tile(review.PAPER, (big.shape[0] + 16, W, 1)).astype(np.float32)
    review._over(r1, big, 8, 8)
    review._label(r1, "3x: drawn in front of creatures/mars/tube_lurker on the same pivot", big.shape[1] + 24, 10)
    rows = [head, r1]
    den = den_frames()
    for clip in ("idle", "react"):
        fr = [c for cl, _i, c in den if cl == clip]
        h, w = fr[0].shape[:2]
        per = (W - 8) // (2 * w + 6)
        nr = -(-len(fr) // per)
        r = np.tile(review.PAPER, (nr * (2 * h + 6) + 26, W, 1)).astype(np.float32)
        for j, c in enumerate(fr):
            rr, cc = divmod(j, per)
            review._over(r, (np.clip(c, 0, 1) * 255).astype(np.uint8).repeat(2, 0).repeat(2, 1), 8 + cc * (2 * w + 6), 26 + rr * (2 * h + 6))
        review._label(r, f"den {clip} at 2x: the lurker behind its mound ({len(fr)} frames)", 6, 6)
        rows.append(r)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + (" export" if stamp_paths else " preview"), 2, img.shape[0] - 16)
    review.write(out, img)
    return problems


def boxes_panel(imgs, widths, W, names):
    """The ten §9.7 boxes per prop: x measured, s BLENDER's self-check, blank = LEAD's to tick."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    lines = []
    for name in names:
        ws = widths[name]
        outer = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
        inner = [w for w in ws if w[0] < v3.OUTER_SPLIT]
        ow = (min(w[1] for w in outer), max(w[2] for w in outer)) if outer else (0, 0)
        iw = (min(w[1] for w in inner), max(w[2] for w in inner)) if inner else (0, 0)
        ink_ok = v3.OUTER_PX[0] - 0.05 <= ow[0] and ow[1] <= v3.OUTER_PX[1] + 0.05 and inner and \
            v3.INNER_PX[0] - 0.05 <= iw[0] and iw[1] <= v3.INNER_PX[1] + 0.05
        sh, meta, probs = sheet_meta(name, imgs[name])
        pal, _off = v3.palette_hits(sh, "mars", tints=[("offwhite", 0.30), ("mustard", 0.25)])
        mot, idl = SELF[name]
        marks = [("ink", "x" if ink_ok else "!", f"{ow[0]:.1f}-{ow[1]:.1f} / {iw[0]:.1f}-{iw[1]:.1f} px, {len(inner) // max(len(imgs[name]), 1)} interior strokes per frame"),
                 ("cel", "x" if pal >= 0.98 else "!", f"{pal * 100:.1f}% mars palette (+ mid, deep; drawn halo washes)"),
                 ("face", "s", "an object: no eyes, no mouth; one porthole or light at most"),
                 ("twos", "x" if not probs else "!", "fps 12, caps" if not probs else probs[0][:50]),
                 ("motion", "s", mot), ("idle", "s", idl), ("original", "s", "our mars kit (Halcyon livery, the Warden bell), no studio prop"),
                 ("sheet", "x" if not probs else "!", f"{sh.shape[1]}x{sh.shape[0]} <= 512^2{', interactable' if meta.get('interactable') else ''}"),
                 ("budget", "x", "one small sheet; UNITY confirms"), ("style", " ", "LEAD, against the C0 style test")]
        lines.append((name, marks))
    h = 24 + len(lines) * (18 + 11 * 15)
    p = np.tile(review.PAPER, (h, W, 1)).astype(np.float32)
    review._label(p, "bible 4.1 9.7 ten boxes per prop  (x measured  s self-check  ! fails  blank: lead's)", 6, 4)
    y = 24
    for name, marks in lines:
        review._label(p, name, 6, y, scale=1)
        y += 14
        for (k, mk, note), (_k, text) in zip(marks, review.BOXES):
            review._label(p, f"[{mk}] {text} - {note}"[:200], 18, y, scale=1)
            y += 15
        y += 4
    return p[:y + 4]


def main(out, imgs=None, widths=None, stamp_paths=()):
    """B-144 review: the Mars props at 1x on the B-139 regolith strips beside the surveyor, each prop at 2x, the clips at
    2x, the ten boxes per prop; then the den (den_review) written beside it."""
    import time
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_c2_ground_strip as GS
    import build_c2_mars_ground as MG
    import preview_c2_earth_rigs as PR
    if imgs is None:
        imgs, widths = render_all()
    names = [n for n in PROPS if n != "tube_mound"]
    W = 1936
    rows = []
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, "b-144 mars camp props v3.1 (designs, no faces): ice drill rig, meridian beacon, hauler hull a + b, hauler cargo, warden pylon; "
                        + ("exported" if stamp_paths else "lock-free fakegp preview, nothing exported"), 6, 8)
    rows.append(head)
    H = 420
    scene = np.empty((H, W, 3), np.float32)                                           # a butterscotch-to-salmon sky stand-in
    t = (np.arange(H) / H)[:, None, None]
    top = np.array(v3.hex_rgb(P["mustard"]), np.float32) / 255
    low = np.array(v3.hex_rgb(P["sky"]), np.float32) / 255
    scene[:] = top * (1 - t) + low * t
    S, _gw = MG.sheets()
    base = H - 70
    rnd = np.random.default_rng(3)
    for c in range(31):
        im = S["regolith"][int(rnd.integers(0, 8))]
        y0 = base - (GS.FH - int(round(GS.SURF * 64)))
        review._over(scene, im[:max(0, min(GS.FH, H - y0))], c * 64, y0)

    def stand(img, xc, fh):
        review._over(scene, img, int(xc - img.shape[1] / 2), base - (fh - GROUND_PX))
    x = 80
    for name in ("ice_drill_rig", "meridian_beacon", "warden_pylon", "hauler_hull_b", "hauler_hull_a", "hauler_cargo"):
        _fn, fw, fh, _c, _n, _t = PROPS[name]
        stand(imgs[name][0], x + fw / 2, fh)
        x += fw + 70
        if name == "warden_pylon":
            try:
                fr, piv = PR.surveyor_frame()
                review._over(scene, fr, x - 40, base - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
                x += 110
            except Exception:  # noqa: BLE001
                pass
    review._label(scene, "1x on the b-139 regolith strips (sky: a flat stand-in until b-141 exports) beside the surveyor (2 m)", 6, 6)
    rows.append(scene)
    big = np.tile(np.array([0.62, 0.72, 0.72], np.float32), (252 * 2 + 30, W, 1))
    x = 8
    for name in names:
        im = imgs[name][0]
        if x + im.shape[1] * 2 > W:
            break
        review._over(big, np.repeat(np.repeat(im, 2, 0), 2, 1), x, 22)
        review._label(big, name, x, 6, scale=1)
        x += im.shape[1] * 2 + 12
    rows.append(big)
    for name in ("ice_drill_rig", "meridian_beacon", "warden_pylon"):
        _fn, fw, fh, clip, n, _t = PROPS[name]
        r = np.tile(np.array([0.62, 0.72, 0.72], np.float32), (fh * 2 + 30, W, 1))
        review._label(r, f"{name} / {clip}: {n} frames at 12 fps (loop), 2x", 6, 4)
        for k, im in enumerate(imgs[name]):
            if 8 + k * (fw * 2 + 8) + fw * 2 > W:
                break
            review._over(r, np.repeat(np.repeat(im, 2, 0), 2, 1), 8 + k * (fw * 2 + 8), 22)
            review._label(r, str(k), 10 + k * (fw * 2 + 8), 24, scale=1)
        rows.append(r)
    allw = [w for n in names for w in widths[n]]
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; ground line 10 px above each frame's bottom; the drill rig drawn 1.9 x 3.7 m "
                        "(v2 3.2 x 4.4) so its 8 frames fit 512^2", 6, 8)
    review._label(foot, "sheets: " + ", ".join(f"{n} {sheet_meta(n, imgs[n])[0].shape[1]}x{sheet_meta(n, imgs[n])[0].shape[0]}" for n in names), 6, 28)
    rows.append(foot)
    rows.append(boxes_panel(imgs, widths, W, names))
    img = np.vstack(rows)
    review._label(img, time.strftime("%m-%d %H:%M") + (" export" if stamp_paths else " preview (not exported)"), 2, img.shape[0] - 16)
    review.write(out, img)
    return [p_ for n in names for p_ in sheet_meta(n, imgs[n])[2]]


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "--den":
        print("problems", den_review(sys.argv[1]) or "-")
    else:
        print("problems", main(sys.argv[1]) or "-")
