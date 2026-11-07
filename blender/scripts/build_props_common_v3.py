"""B-131: the Earth camp props re-inked as v3.1 cartoon sprites (D-086/D-100, no faces D-101):
props/common/landing_pad, shelter_wall, shelter_door, smelter, storage_crate, lamp. Previews first
(lock-free, meridian.fakegp); the export (render.py, one sheet <= 512^2 per prop) comes in a later batch.

Each prop is drawn in metres with the ground line at z = 0 and x centred, ink 2-3 / 1-1.5 px, mid + deep
shadow tones, drawn detail (planks, grain, rivets, bolts, hazard stripes). Frames put the ground line
10 px above the bottom (the manifest rows' rule). The pad (2 m) and the wall (1 m) tile: every line that
crosses a module edge is straight there and its ink jitter is cancelled at the edges, so modules join.

  landing_pad    128x48   2 m module, plank deck on a mustard trestle, hazard stripes, one red light
  shelter_wall    64x176  1 m module, corrugated sky-steel panel, wood cap and sill, bolts
  shelter_door    88x176  posts + lintel, a red door with one porthole; clip open 6 (it swings in)
  smelter        112x192  pot-bellied iron stove: mouth with a drawn glow, hopper, chimney; clip working 8
  storage_crate   80x72   plank crate, mustard corner brackets, a red stripe with a this-way-up arrow
  lamp            64x160  post lamp, mustard shade, drawn halo; clip flicker 4

  python -I build_props_common_v3.py <out.png>      lock-free preview
"""
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp  # noqa: E402

try:                                    # inside Blender (a later export build): the real gp_draw
    import bpy  # noqa: F401
    if not hasattr(bpy, "data"):
        raise ImportError
    import gp_draw as G
except ImportError:
    G = fakegp.install()
import gp_raster as GR  # noqa: E402

P = G.PALETTES["earth"]
O, I = G.OUTER, G.INNER
PPU = 64
GROUND_PX = 10


def mats(gp):
    m = {}
    for name, hexc in (("wood", P["brown"]), ("steel", P["sky"]), ("teal", P["teal"]), ("mustard", P["mustard"]),
                       ("red", P["red"]), ("off", P["offwhite"]), ("green", P["green"])):
        m[name] = G.mat(gp, name, fill=hexc)
        m[name + "_f"] = G.mat(gp, name + "_f", fill=hexc, ink=False)
        m[name + "_sh"] = G.mat(gp, name + "_mid", fill=G.shadow_of(hexc), ink=False)
        m[name + "_dp"] = G.mat(gp, name + "_deep", fill=G.deep_of(hexc), ink=False)
    m["iron"] = G.mat(gp, "iron", fill=G.deep_of(P["brown"]))
    m["iron_f"] = G.mat(gp, "iron_f", fill=G.deep_of(P["brown"]), ink=False)
    m["iron_sh"] = G.mat(gp, "iron_mid", fill=G.deep_of(G.deep_of(P["brown"])), ink=False)
    m["hole"] = G.mat(gp, "hole", fill=G.deep_of(G.deep_of(P["brown"])), ink=False)
    m["glass"] = G.mat(gp, "glass", fill=P["sky"])
    m["halo"] = G.mat(gp, "halo", fill=P["offwhite"], ink=False, fill_alpha=0.30)
    m["halo2"] = G.mat(gp, "halo2", fill=P["mustard"], ink=False, fill_alpha=0.22)
    m["glow"] = G.mat(gp, "glow", fill=P["mustard"], ink=False)
    m["glow_hot"] = G.mat(gp, "glow_hot", fill=P["red"], ink=False)
    m["glow_core"] = G.mat(gp, "glow_core", fill=P["offwhite"], ink=False)
    m["puff"] = G.mat(gp, "puff", fill=P["offwhite"])
    m["puff_sh"] = G.mat(gp, "puff_mid", fill=G.shadow_of(P["offwhite"]), ink=False)
    m["ink"] = G.mat(gp, "ink", fill=None, ink=True)
    return m


def box(x0, z0, x1, z1, seed=0, wob=0.005, n=3):
    """A hand-drawn rectangle (corners and n points per side wobble a hair)."""
    rnd = random.Random(seed)
    pts = []
    for (ax, az), (bx, bz) in (((x0, z0), (x1, z0)), ((x1, z0), (x1, z1)), ((x1, z1), (x0, z1)), ((x0, z1), (x0, z0))):
        for i in range(n):
            t = i / n
            pts.append((ax + (bx - ax) * t + rnd.uniform(-wob, wob), az + (bz - az) * t + rnd.uniform(-wob, wob)))
    return pts


def hline(d, M, x0, x1, z, mat="ink", r=None):
    """A straight line across (for tiling edges: exactly straight, extended past the module edge)."""
    G.stroke(d, [(x0 + (x1 - x0) * i / 8, z) for i in range(9)], M[mat], O if r is None else r)


# ---------------------------------------------------------------- landing pad (2 m module, tiles)
PAD_W = 2.0


def landing_pad(d, M, k=0):
    L, R = -1.06, 1.06                                  # strokes run past the module edges (the frame cuts them)
    zt, zb = 0.38, 0.26                                 # deck top / bottom
    for x in (-0.5, 0.5):                               # trestle legs with an X brace between each pair
        G.stroke(d, box(x - 0.07, 0.0, x + 0.07, zb, seed=int(10 * x) + 3), M["mustard"], O, cyclic=True)
        G.stroke(d, box(x + 0.02, 0.0, x + 0.07, zb, seed=int(10 * x) + 4, wob=0.002), M["mustard_sh"], 0.0, cyclic=True)
        G.stroke(d, box(x - 0.1, 0.0, x + 0.1, 0.035, seed=int(10 * x) + 5), M["iron"], O, cyclic=True)       # foot plate
        G.rivets(d, [(x, 0.08), (x, 0.19)], M["ink"])
    G.stroke(d, [(-0.43, 0.04), (0.43, 0.22)], M["ink"], I)                                             # X brace
    G.stroke(d, [(-0.43, 0.22), (0.43, 0.04)], M["ink"], I)
    for x in (-0.5, 0.5):                                                                                # the deck's shadow on the legs
        G.stroke(d, [(x - 0.07, zb - 0.045), (x + 0.07, zb - 0.045), (x + 0.07, zb), (x - 0.07, zb)], M["mustard_dp"], 0.0, cyclic=True)
    G.stroke(d, [(L, zb), (R, zb), (R, zt), (L, zt)], M["wood_f"], 0.0, cyclic=True)                       # plank deck
    G.stroke(d, [(L, zb), (R, zb), (R, zb + 0.06), (L, zb + 0.06)], M["wood_dp"], 0.0, cyclic=True)
    G.stroke(d, [(L, zb + 0.06), (R, zb + 0.06), (R, zb + 0.085), (L, zb + 0.085)], M["wood_sh"], 0.0, cyclic=True)
    for i in range(16):                                                                                  # hazard band
        x = -1.0 + i * 0.125
        if i % 2 == 0:
            G.stroke(d, [(x, zb), (x + 0.0625, zb), (x + 0.125, zb + 0.06), (x + 0.0625, zb + 0.06)], M["mustard_f"], 0.0, cyclic=True)
    hline(d, M, L, R, zb + 0.06, r=I)
    for x in (-0.75, -0.25, 0.25, 0.75):                                                                 # plank ends + nails
        G.seam(d, [(x, zb + 0.065), (x + 0.004, zt - 0.005)], M["ink"])
        G.rivets(d, [(x - 0.04, zt - 0.025), (x + 0.04, zt - 0.025)], M["ink"])
    for x in (-0.62, 0.1, 0.55):                                                                         # wood grain
        G.seam(d, [(x, zt - 0.045), (x + 0.07, zt - 0.05), (x + 0.12, zt - 0.045)], M["ink"])
    G.specks(d, [(-0.9, zt - 0.03), (-0.1, zt - 0.06), (0.88, zt - 0.04)], M["ink"])
    hline(d, M, L, R, zt)                                                                                # deck outline
    hline(d, M, L, R, zb)
    lz = zt + 0.035                                                                                      # the red light (glow tone)
    G.stroke(d, G.lumpy_ellipse(0.0, lz + 0.01, 0.08, 0.07, n=16, seed=2), M["halo2"], 0.0, cyclic=True)
    G.stroke(d, [(-0.04, zt), (-0.035, lz + 0.02), (0.0, lz + 0.045), (0.035, lz + 0.02), (0.04, zt)], M["red"], I, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(-0.01, lz + 0.015, 0.012, 0.01, n=8, seed=3), M["glow_core"], 0.0, cyclic=True)


# ---------------------------------------------------------------- shelter wall (1 m module, tiles)
def shelter_wall(d, M, k=0):
    L, R = -0.53, 0.53
    G.stroke(d, [(L, 0.16), (R, 0.16), (R, 2.38), (L, 2.38)], M["steel_f"], 0.0, cyclic=True)              # panel
    for i in range(8):                                                                                   # corrugation
        x = -0.5 + i * 0.125
        G.stroke(d, [(x + 0.07, 0.16), (x + 0.11, 0.16), (x + 0.11, 2.38), (x + 0.07, 2.38)], M["steel_sh"], 0.0, cyclic=True)
        G.seam(d, [(x + 0.07, 0.2), (x + 0.07, 2.34)], M["ink"])
    G.stroke(d, [(L, 2.18), (R, 2.18), (R, 2.38), (L, 2.38)], M["steel_dp"], 0.0, cyclic=True)              # the cap's shadow
    hline(d, M, L, R, 1.27, r=I)                                                                         # the seam strap
    hline(d, M, L, R, 1.21, r=I)
    G.stroke(d, [(L, 1.21), (R, 1.21), (R, 1.27), (L, 1.27)], M["steel_sh"], 0.0, cyclic=True)
    G.rivets(d, [(x, 1.24) for x in (-0.31, -0.06, 0.19, 0.44)], M["ink"])
    G.rivets(d, [(-0.4, 2.12), (0.4, 2.12), (-0.4, 0.26), (0.4, 0.26)], M["ink"])
    G.stroke(d, [(0.22, 1.2), (0.25, 1.0), (0.21, 0.85), (0.235, 0.7)], M["wood_sh"], I)                   # a rust streak
    G.hatch(d, -0.25, 0.55, M["ink"], n=3, length=0.1, spacing=0.03, angle_deg=60, seed=4)
    G.specks(d, [(-0.12, 1.7), (0.33, 0.45), (-0.38, 1.0)], M["ink"])
    G.stroke(d, [(L, 0.0), (R, 0.0), (R, 0.16), (L, 0.16)], M["wood_f"], 0.0, cyclic=True)                  # sill plank
    G.stroke(d, [(L, 0.0), (R, 0.0), (R, 0.05), (L, 0.05)], M["wood_dp"], 0.0, cyclic=True)
    G.stroke(d, [(L, 2.38), (R, 2.38), (R, 2.52), (L, 2.52)], M["wood_f"], 0.0, cyclic=True)                # cap plank
    G.stroke(d, [(L, 2.38), (R, 2.38), (R, 2.42), (L, 2.42)], M["wood_sh"], 0.0, cyclic=True)
    G.seam(d, [(-0.3, 0.09), (-0.18, 0.1), (-0.05, 0.085)], M["ink"])                                   # grain
    G.seam(d, [(0.1, 2.46), (0.25, 2.47), (0.36, 2.455)], M["ink"])
    for z in (0.0, 0.16, 2.38, 2.52):
        hline(d, M, L, R, z)
    for x in (-0.5, 0.5):                                                                                # module edges: half a line each
        G.stroke(d, [(x, 0.16 + 2.22 * i / 40) for i in range(41)], M["ink"], I)   # dense: jitter is cancelled per point


# ---------------------------------------------------------------- shelter door (clip open 6)
DOOR_OPEN = [1.0, 0.82, 0.52, 0.24, 0.08, 0.14]        # the leaf's width as it swings in about the left hinge


def shelter_door(d, M, k=0):
    sx = DOOR_OPEN[k]
    G.stroke(d, box(-0.48, 0.0, 0.48, 2.3, seed=7, wob=0.002), M["hole"], 0.0, cyclic=True)                # the dark doorway
    G.stroke(d, box(-0.48, 1.9, 0.48, 2.3, seed=8, wob=0.002), M["iron_sh"], 0.0, cyclic=True)
    if k > 0:
        G.hatch(d, 0.2, 1.0, M["ink"], n=3, length=0.12, spacing=0.04, angle_deg=70, seed=9)
    hx = -0.48                                                                                           # the leaf, scaled in x about the hinge
    X = lambda x: hx + (x - hx) * sx  # noqa: E731
    leaf = [(X(x), z) for x, z in box(-0.48, 0.04, 0.48, 2.28, seed=11, wob=0.003)]
    G.stroke(d, leaf, M["red_f"], 0.0, cyclic=True)
    if sx < 0.9:                                                                                         # turning away: the far side darkens
        G.stroke(d, [(X(0.1), 0.04), (X(0.48), 0.04), (X(0.48), 2.28), (X(0.1), 2.28)], M["red_sh"], 0.0, cyclic=True)
    G.stroke(d, [(X(0.36), 0.04), (X(0.48), 0.04), (X(0.48), 2.28), (X(0.36), 2.28)], M["red_dp"], 0.0, cyclic=True)
    G.stroke(d, [(X(-0.42), 0.08), (X(0.42), 0.08), (X(0.42), 0.32), (X(-0.42), 0.32)], M["mustard_f"], 0.0, cyclic=True)   # kick plate
    for i in range(6):
        x0 = -0.42 + i * 0.14
        G.seam(d, [(X(x0 + 0.02), 0.09), (X(x0 + 0.1), 0.31)], M["ink"])
    G.seam(d, [(X(-0.42), 0.32), (X(0.42), 0.32)], M["ink"])
    G.seam(d, [(X(-0.36), 1.35), (X(0.36), 1.35)], M["ink"])                                               # panel seams
    G.seam(d, [(X(-0.36), 0.45), (X(-0.36), 1.25)], M["ink"])
    G.seam(d, [(X(0.36), 0.45), (X(0.36), 1.25)], M["ink"])
    G.rivets(d, [(X(x), z) for x in (-0.4, 0.4) for z in (0.5, 1.2, 2.18)], M["ink"])
    if sx > 0.3:                                                                                         # one porthole (no pair of marks)
        cx, cz = X(0.0), 1.78
        G.stroke(d, G.lumpy_ellipse(cx, cz, 0.17 * sx, 0.17, n=24, seed=12), M["off"], O, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(cx, cz, 0.12 * sx, 0.12, n=20, seed=13), M["glass"], I, cyclic=True)
        G.stroke(d, [(cx - 0.06 * sx, cz + 0.02), (cx - 0.02 * sx, cz + 0.07)], M["off"], I)                # glint
        G.rivets(d, [(cx + 0.145 * sx * math.cos(a), cz + 0.145 * math.sin(a)) for a in (0.5, 2.1, 3.7, 5.3)], M["ink"])
    G.stroke(d, [(X(0.3), 1.0), (X(0.3), 1.2)], M["off"], O)                                       # handle
    G.stroke(d, leaf, M["ink"], O, cyclic=True)
    for x0, x1 in ((-0.6, -0.48), (0.48, 0.6)):                                                          # wood posts + lintel
        G.stroke(d, box(x0, 0.0, x1, 2.38, seed=int(x0 * 10) + 20), M["wood"], O, cyclic=True)
        G.stroke(d, box(x1 - 0.035, 0.0, x1, 2.38, seed=int(x0 * 10) + 21, wob=0.002), M["wood_sh"], 0.0, cyclic=True)
        G.seam(d, [(x0 + 0.04, 0.3), (x0 + 0.05, 0.9), (x0 + 0.04, 1.5)], M["ink"])
    G.stroke(d, box(-0.62, 2.3, 0.62, 2.5, seed=24), M["wood"], O, cyclic=True)
    G.stroke(d, box(-0.62, 2.3, 0.62, 2.34, seed=25, wob=0.002), M["wood_sh"], 0.0, cyclic=True)
    G.seam(d, [(-0.4, 2.42), (-0.2, 2.43), (0.05, 2.415)], M["ink"])
    G.rivets(d, [(-0.54, 2.4), (0.54, 2.4)], M["ink"])
    lamp_c = M["green"] if k >= 4 else M["red"]                                                          # status light on the right post
    G.stroke(d, G.lumpy_ellipse(0.54, 1.62, 0.07, 0.07, n=14, seed=26), M["halo2"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.54, 1.62, 0.035, 0.035, n=12, seed=27), lamp_c, I, cyclic=True)


# ---------------------------------------------------------------- smelter (clip working 8)
def smelter(d, M, k=0):
    ph = 2 * math.pi * k / 8
    br = 1.0 + 0.018 * math.sin(ph)                                                                      # it breathes
    for x in (-0.42, 0.4):                                                                               # stubby feet, tucked under the belly
        G.stroke(d, [(x - 0.13, 0.0), (x + 0.13, 0.0), (x + 0.08, 0.42), (x - 0.08, 0.42)], M["mustard"], O, cyclic=True)
        G.stroke(d, [(x + 0.04, 0.0), (x + 0.13, 0.0), (x + 0.08, 0.42), (x + 0.03, 0.42)], M["mustard_sh"], 0.0, cyclic=True)
        G.stroke(d, [(x - 0.11, 0.0), (x + 0.11, 0.0), (x + 0.11, 0.04), (x - 0.11, 0.04)], M["mustard_dp"], 0.0, cyclic=True)
    hop = [(-0.5, 1.25), (-0.18, 1.25), (-0.02, 1.76), (-0.72, 1.76)]                                    # mustard hopper (into the belly)
    G.stroke(d, hop, M["mustard"], O, cyclic=True)
    G.stroke(d, [(-0.28, 1.25), (-0.18, 1.25), (-0.02, 1.76), (-0.18, 1.76)], M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, box(-0.76, 1.74, 0.02, 1.82, seed=39), M["mustard"], O, cyclic=True)
    G.stroke(d, box(-0.76, 1.74, 0.02, 1.765, seed=39, wob=0.002), M["mustard_dp"], 0.0, cyclic=True)
    G.rivets(d, [(-0.5, 1.6), (-0.25, 1.6)], M["ink"])
    G.stroke(d, box(0.3, 1.15, 0.46, 2.12, seed=40), M["teal"], O, cyclic=True)                           # chimney (out of the belly)
    G.stroke(d, box(0.4, 1.15, 0.46, 2.12, seed=41, wob=0.002), M["teal_sh"], 0.0, cyclic=True)
    G.ribs(d, [(0.38, 1.6), (0.38, 2.05)], 0.16, M["ink"], every=0.2, frac=0.9)
    G.stroke(d, box(0.24, 2.1, 0.52, 2.18, seed=42), M["iron"], O, cyclic=True)
    cx, cz = 0.0, 0.85                                                                                   # the pot belly
    belly = [(cx + x, 0.16 + (z - 0.16) * br) for x, z in G.lumpy_ellipse(0.0, cz, 0.72, 0.66, n=48, lump=0.02, seed=32)]
    belly = [(x, max(z, 0.16)) for x, z in belly]
    G.stroke(d, belly, M["iron_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in belly if q[0] > 0.32] + [(0.32, 0.4)], M["iron_sh"], 0.0, cyclic=True)        # deep side
    for z in (0.62, 1.12):                                                                               # riveted bands
        zz = 0.16 + (z - 0.16) * br
        w = 0.72 * math.sqrt(max(0.0, 1 - ((z - cz) / 0.66) ** 2)) - 0.02
        G.stroke(d, [(-w, zz - 0.035), (w, zz - 0.035), (w, zz + 0.035), (-w, zz + 0.035)], M["mustard_f"], 0.0, cyclic=True)
        G.seam(d, [(-w, zz - 0.035), (w, zz - 0.035)], M["ink"])
        G.seam(d, [(-w, zz + 0.035), (w, zz + 0.035)], M["ink"])
        G.rivets(d, [(x, zz) for x in [-w + 0.08 + i * (2 * w - 0.16) / 6 for i in range(7)]], M["ink"])
    G.hatch(d, 0.5, 0.9, M["ink"], n=4, length=0.14, spacing=0.035, angle_deg=65, seed=33)
    G.stroke(d, belly, M["ink"], O, cyclic=True)
    mx, mz = -0.2, 0.86                                                                                  # the furnace mouth, a drawn glow
    mouth = [(mx - 0.26, mz - 0.17), (mx + 0.26, mz - 0.17), (mx + 0.26, mz + 0.06)] + \
        G.bezier((mx + 0.26, mz + 0.06), (mx + 0.24, mz + 0.22), (mx - 0.24, mz + 0.22), (mx - 0.26, mz + 0.06), n=10)[1:]
    pulse = 0.5 + 0.5 * math.sin(ph)
    G.stroke(d, mouth, M["glow_hot"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(mx, mz - 0.02, 0.17 + 0.04 * pulse, 0.1 + 0.03 * pulse, n=18, lump=0.08, seed=34 + k % 2), M["glow"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(mx + 0.02, mz - 0.05, 0.07 + 0.02 * pulse, 0.035, n=12, lump=0.1, seed=36), M["glow_core"], 0.0, cyclic=True)
    for i in range(5):                                                                                   # grate bars
        x = mx - 0.2 + i * 0.1
        G.stroke(d, [(x, mz - 0.17), (x, mz + 0.16 - 0.04 * abs(i - 2))], M["ink"], I)
    G.stroke(d, mouth, M["ink"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(mx, mz + 0.3, 0.3, 0.05, n=16, seed=37), M["halo2"], 0.0, cyclic=True)    # glow on the iron above
    G.stroke(d, [(0.62, 0.95), (0.72, 1.08)], M["off"], O)                                         # a lever on the side (inside the 2 px margin)
    G.stroke(d, G.lumpy_ellipse(0.74, 1.10, 0.045, 0.045, n=12, seed=38), M["red"], I, cyclic=True)
    for j in range(2):                                                                                   # smoke puffs, born 4 frames apart
        t = ((k + 4 * j) % 8) / 8.0
        px, pz = 0.38 + 0.12 * t + 0.03 * math.sin(6 * t), 2.27 + 0.42 * t
        r = 0.06 + 0.07 * t - 0.05 * max(0.0, t - 0.75) * 4
        if r > 0.02:
            puff = G.lumpy_ellipse(px, pz, r * 1.2, r, n=16, lump=0.12, seed=43 + j)
            G.stroke(d, puff, M["puff"], I, cyclic=True)
            G.stroke(d, [q for q in puff if q[1] < pz - r * 0.3] + [(px, pz - r * 0.3)], M["puff_sh"], 0.0, cyclic=True)
    if k in (2, 3, 6):                                                                                   # sparks from the hopper
        G.specks(d, [(-0.35 + 0.05 * (k % 3), 1.9 + 0.04 * (k % 2)), (-0.45, 1.86 + 0.03 * k % 0.09)], M["ink"])


# ---------------------------------------------------------------- storage crate
def storage_crate(d, M, k=0):
    x0, x1, z0, z1 = -0.5, 0.5, 0.0, 0.8
    G.stroke(d, box(x0, z0, x1, z1, seed=50), M["wood_f"], 0.0, cyclic=True)
    for i, (za, zb) in enumerate(((0.0, 0.27), (0.27, 0.53), (0.53, 0.8))):                             # three boards
        if i == 0:
            G.stroke(d, box(x0, za, x1, zb, seed=51, wob=0.002), M["wood_sh"], 0.0, cyclic=True)
        G.seam(d, [(x0 + 0.02, zb), (x1 - 0.02, zb + 0.004)], M["ink"])
        G.seam(d, [(-0.25 + 0.17 * i, za + 0.1), (-0.1 + 0.17 * i, za + 0.11), (0.05 + 0.17 * i, za + 0.095)], M["ink"])  # grain
    G.stroke(d, box(0.36, z0, x1, z1, seed=52, wob=0.002), M["wood_dp"], 0.0, cyclic=True)                 # shaded side
    G.stroke(d, box(-0.28, 0.33, 0.28, 0.47, seed=53), M["red"], I, cyclic=True)                           # red stripe
    G.stroke(d, [(0.0, 0.35), (0.0, 0.44)], M["off"], I)                                            # this way up
    G.stroke(d, [(-0.035, 0.405), (0.0, 0.445), (0.035, 0.405)], M["off"], I)
    for cx, cz, sx_, sz in ((x0, z0, 1, 1), (x1, z0, -1, 1), (x0, z1, 1, -1), (x1, z1, -1, -1)):         # corner brackets
        br = [(cx, cz), (cx + 0.16 * sx_, cz), (cx + 0.16 * sx_, cz + 0.05 * sz), (cx + 0.05 * sx_, cz + 0.05 * sz),
              (cx + 0.05 * sx_, cz + 0.16 * sz), (cx, cz + 0.16 * sz)]
        G.stroke(d, br, M["mustard"], I, cyclic=True)
        G.rivets(d, [(cx + 0.1 * sx_, cz + 0.025 * sz), (cx + 0.025 * sx_, cz + 0.1 * sz)], M["ink"])
    G.hatch(d, 0.42, 0.62, M["ink"], n=3, length=0.08, spacing=0.03, angle_deg=70, seed=54)
    G.specks(d, [(-0.3, 0.68), (0.18, 0.15), (-0.4, 0.2)], M["ink"])
    G.stroke(d, box(x0, z0, x1, z1, seed=50), M["ink"], O, cyclic=True)


# ---------------------------------------------------------------- lamp (clip flicker 4)
FLICKER = [(1.0, 1.0), (0.9, 0.7), (1.04, 1.0), (0.84, 0.55)]   # (halo radius, bulb brightness)


def lamp(d, M, k=0):
    hr, bb = FLICKER[k]
    G.stroke(d, [(-0.17, 0.0), (0.17, 0.0), (0.12, 0.12), (-0.12, 0.12)], M["wood"], O, cyclic=True)       # plinth
    G.stroke(d, [(0.06, 0.0), (0.17, 0.0), (0.12, 0.12), (0.04, 0.12)], M["wood_dp"], 0.0, cyclic=True)
    G.rivets(d, [(-0.08, 0.06), (0.08, 0.06)], M["ink"])
    pole = G.hose_outline([(0.0, 0.1), (0.0, 1.0), (0.01, 1.95)], 0.07)                                  # teal pole
    G.stroke(d, pole, M["teal_f"], 0.0, cyclic=True)
    G.stroke(d, G.hose_outline([(0.018, 0.1), (0.018, 1.0), (0.028, 1.95)], 0.025), M["teal_sh"], 0.0, cyclic=True)
    for z in (0.5, 1.0, 1.5):                                                                            # bands
        G.stroke(d, box(-0.05, z - 0.03, 0.05, z + 0.03, seed=int(z * 10) + 60), M["mustard"], I, cyclic=True)
    G.stroke(d, pole, M["ink"], O, cyclic=True)
    arm = G.bezier((0.0, 1.95), (0.02, 2.12), (0.2, 2.12), (0.24, 2.04), n=10)                           # the curled arm
    G.stroke(d, G.hose_outline(arm, 0.045), M["teal"], O, cyclic=True)
    bx, bz = 0.24, 1.9                                                                                   # bulb under the shade
    G.stroke(d, G.lumpy_ellipse(bx, bz - 0.02, 0.3 * hr, 0.28 * hr, n=28, lump=0.03, seed=61), M["halo"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(bx, bz - 0.02, 0.18 * hr, 0.17 * hr, n=24, lump=0.03, seed=62), M["halo2"], 0.0, cyclic=True)
    for a in (-2.4, -1.57, -0.7):                                                                        # drawn rays (glow tone)
        r0, r1 = 0.12 * hr, 0.2 * hr
        G.stroke(d, [(bx + r0 * math.cos(a), bz - 0.02 + r0 * math.sin(a)), (bx + r1 * math.cos(a), bz - 0.02 + r1 * math.sin(a))], M["glow"], I)
    G.stroke(d, G.lumpy_ellipse(bx, bz, 0.055, 0.06, n=14, seed=63), M["off"] if bb > 0.8 else M["mustard"], I, cyclic=True)
    if bb > 0.8:
        G.stroke(d, G.lumpy_ellipse(bx - 0.012, bz + 0.012, 0.02, 0.02, n=8, seed=64), M["glow"], 0.0, cyclic=True)
    shade = [(bx - 0.15, 1.93), (bx + 0.15, 1.93), (bx + 0.06, 2.06), (bx - 0.06, 2.06)]
    G.stroke(d, shade, M["mustard"], O, cyclic=True)
    G.stroke(d, [(bx + 0.04, 1.93), (bx + 0.15, 1.93), (bx + 0.06, 2.06), (bx + 0.02, 2.06)], M["mustard_sh"], 0.0, cyclic=True)
    G.rivets(d, [(bx - 0.06, 1.99), (bx + 0.03, 1.99)], M["ink"])
    G.stroke(d, G.lumpy_ellipse(bx, 2.08, 0.03, 0.025, n=10, seed=65), M["red"], I, cyclic=True)           # finial knob
    G.specks(d, [(-0.01, 0.75), (0.015, 1.25)], M["ink"])


# name -> (fn, frame w, frame h, clip name, frame count, tiles)
PROPS = {
    "landing_pad": (landing_pad, 128, 48, None, 1, True),
    "shelter_wall": (shelter_wall, 64, 176, None, 1, True),
    "shelter_door": (shelter_door, 88, 176, "open", 6, False),
    "smelter": (smelter, 112, 192, "working", 8, False),
    "storage_crate": (storage_crate, 80, 72, None, 1, False),
    "lamp": (lamp, 64, 160, "flicker", 4, False),
}
LAMP_X = -0.18                       # the pole sits 0.18 m left of the frame centre so the halo (bulb 0.24 m right of it) fits


def steady_edges(strokes, xl, xr, seed, band=5 / 64.0):
    """Cancel gp_raster's width jitter within `band` of the module edges for every stroke (tiling props)."""
    import numpy as np
    for st in strokes:
        xz = st["xz"]
        s_ = np.cumsum(np.r_[0.0, np.hypot(*np.diff(xz, axis=0).T)])
        nz = GR._noise1d(s_, seed * 7919 + st["id"], 0.18)
        x = xz[:, 0]
        e = np.clip(1.0 - np.minimum(np.abs(x - xl), np.abs(xr - x)) / band, 0.0, 1.0)
        st["radius"] = (st["radius"] * (1.0 - e + e / (1.0 + GR.JITTER * nz))).astype(np.float32)


def pivot_of(name):
    """The drawing origin in the frame (x from the left, y from the bottom): the ground line 10 px up; the lamp's pole."""
    _fn, fw, fh, _clip, _n, _tiles = PROPS[name]
    return (0.5 + (LAMP_X * PPU / fw if name == "lamp" else 0.0), GROUND_PX / fh)


def render_prop(name, k=0, seed=7):
    fn, fw, fh, _clip, _n, tiles = PROPS[name]
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    fn(d, M, k)
    st = fakegp.strokes_of(d, gp)
    if tiles:
        half = fw / 2 / PPU
        steady_edges(st, -half, half, seed)
    img, w = GR.render_frame(st, fw, fh, PPU, pivot_of(name), ss=4, seed=seed)
    if tiles:                           # the module's right edge column = its left one: a module seam is always the same 2 px
        img[:, -1] = img[:, 0]
    return img, w


# ---------------------------------------------------------------- export (D-117: colour + json only, replaces the v2 models)

KEY = "props/common/{}"
INTERACTABLE = ("shelter_door", "smelter", "storage_crate")     # the props the player uses: open, craft, store
LOOPS = {"open": False, "working": True, "flicker": True}       # door open 6 once, smelter working 8 loop, lamp flicker 4 loop
SHEET_CAP = 512                                                 # B-131: one sheet per prop <= 512^2
V2_SUFFIXES = (".glb", "_normal.png", "_mask.png", "_emission.png")   # the v2 model + maps each key loses (D-117); .meta = UNITY's


def v2_leftovers(art, names=None):
    """The v2 model files beside the keys (ArtImporter un-addresses a colour map next to a .glb, IsModelKey)."""
    d = os.path.join(art, "props", "common")
    return [os.path.join(d, name + s) for name in (names or PROPS) for s in V2_SUFFIXES if os.path.isfile(os.path.join(d, name + s))]


def render_all():
    """Every frame of the six props (export quality, ss 4) -> {name: [RGBA]}, {name: [(nominal, lo, hi) px]}."""
    imgs, widths = {}, {}
    for name, (_fn, _fw, _fh, _clip, n, _tiles) in PROPS.items():
        imgs[name], widths[name] = [], []
        for k in range(n):
            img, w = render_prop(name, k)
            imgs[name].append(img)
            widths[name] += w
    return imgs, widths


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
    """One prop -> (sheet RGBA uint8, §11.2 json dict, problems)."""
    import numpy as np
    from meridian import v3
    _fn, fw, fh, clip, n, tiles = PROPS[name]
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
        anims.append({"name": clip, "start": 0, "length": n, "loop": LOOPS[clip]})
        if LOOPS[clip]:
            anims[-1]["loop_from"] = 0
    meta = {"key": KEY.format(name), "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": g,
            "frames": n, "fps": v3.FPS, "pivot": [round(px, 6), round(py, 6)], "facing": "right", "ppu": PPU,
            "animations": anims, "squash_root": False, "ground_line_px": GROUND_PX}
    if tiles:
        meta["tile"] = True
        meta["module_m"] = fw / PPU
    if name in INTERACTABLE:
        meta["interactable"] = True
    if not clip:
        meta["note"] = "one static frame (no clip); the pivot sits on the ground line"
    elif name == "shelter_door":
        meta["note"] = "frame 0 = shut; open plays once and holds its last frame"
    else:
        meta["note"] = f"frame 0 = at rest; {clip} loops while the prop is busy"
    problems = [p for p in v3.validate_sheet(meta, sheet.shape) if not (not clip and "sum of clip lengths" in p)]
    if sheet.shape[0] > SHEET_CAP or sheet.shape[1] > SHEET_CAP:
        problems.append(f"sheet {sheet.shape[1]}x{sheet.shape[0]} over {SHEET_CAP}^2")
    m = v3.EDGE_MARGIN
    for i, im in enumerate(frames):
        a = im[..., 3]
        if a[:m].any() or a[-m:].any() or (not tiles and (a[:, :m].any() or a[:, -m:].any())):
            problems.append(f"frame {i} touches the {m} px frame edge")
    return sheet, meta, problems


def joins(imgs):
    """Mean |right column - left column| per tiling module (B-131 preview: 0.0/255)."""
    import numpy as np
    return {nm: float(np.abs(imgs[nm][0][:, -1, :].astype(np.int32) - imgs[nm][0][:, 0, :].astype(np.int32)).mean())
            for nm, spec in PROPS.items() if spec[5]}


def export(art, imgs=None, names=None):
    """Writes props/common/<prop>_color.png + <prop>.json for the six (or `names`) and removes their v2 model
    files (.glb + normal/mask/emission). Raises before writing anything if a check fails.
    Returns [(key, w, h, bytes)], joins, removed paths."""
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
    jn = joins(imgs)
    problems += [f"{nm}: tiling join {v:.2f}/255 > 1" for nm, v in jn.items() if v > 1.0 and nm in names]
    if problems:
        raise ValueError("B-131 export checks: " + "; ".join(problems))
    d = os.path.join(art, "props", "common")
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
    return out, jn, removed


def main(out, imgs=None, widths=None, stamp_paths=()):
    """The B-131 review: the camp at 1x on the plains, each prop at 3x, the clips at 2x, the tiling joins, the
    ten §9.7 boxes per prop. stamp_paths (export): the written PNGs, stamped with file time + hash."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import v3
    import build_c2_ground_strip as GS
    import preview_c2_earth_rigs as PR
    import preview_pilgrim_rig as PP
    if imgs is None:
        imgs, widths = render_all()
    allw = [w for ws in widths.values() for w in ws]
    W = 1936
    rows = []
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, "b-131 earth camp props v3.1 (no faces): landing pad, shelter wall, shelter door, smelter, storage crate, lamp; "
                        + ("exported sheets (render.py props/common/camp_set)" if stamp_paths else "lock-free fakegp preview"), 6, 8)
    rows.append(head)
    # (1) the camp at 1x on the plains: ground strips, the Pilgrim rig on three pad modules, the shelter, the props, the surveyor
    MH = 1000
    keep, PR.PLAINS_H = PR.PLAINS_H, MH
    try:
        scene, note = PR.plains_strip(W)
    finally:
        PR.PLAINS_H = keep
    S, _gw = GS.sheets()
    base = MH - 150                                                     # the ground line
    rnd = np.random.default_rng(3)
    for c in range(30):
        im = S["grass"][int(rnd.integers(0, 8))]
        y0 = base - (GS.FH - int(round(GS.SURF * 64)))
        review._over(scene, im, 8 + c * 64, y0)
        scene[y0 + GS.FH:, 8 + c * 64:8 + c * 64 + 64] = np.array(S["grass"][0][-4, 30, :3], np.float32) / 255

    def stand(img, x_ground_center, fh, piv_x=0.5):
        review._over(scene, img, int(x_ground_center - piv_x * img.shape[1]), base - (fh - GROUND_PX))
    x = 8 + 64 * 1
    pad_x0 = x
    for m in range(3):                                                  # three 2 m pad modules (6 m under the Pilgrim)
        stand(imgs["landing_pad"][0], pad_x0 + 64 + m * 128, 48)
    side, _top = PP.BP.PILGRIM_RIGS
    ship, w = PP.render(side, {}, 400, 816, (0.5, 12 / 816))
    deck = int(round(0.38 * PPU))
    review._over(scene, ship, pad_x0 + 192 - 200, base - deck - (816 - 12))
    sx0 = pad_x0 + 384 + 160                                            # the shelter: wall, wall, door, wall, wall
    for i, nm in enumerate(["shelter_wall", "shelter_wall", "shelter_door", "shelter_wall", "shelter_wall"]):
        cx = sx0 + (32 if i == 0 else 0) + sum((64 if p != "shelter_door" else 77) for p in ["shelter_wall", "shelter_wall", "shelter_door", "shelter_wall"][:i]) + (38 if nm == "shelter_door" else 32)
        stand(imgs[nm][0], cx, 176)
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, sx0 + 330, base - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    except Exception:  # noqa: BLE001
        pass
    stand(imgs["smelter"][0], sx0 + 520, 192)
    stand(imgs["storage_crate"][0], sx0 + 650, 72)
    stand(imgs["storage_crate"][0], sx0 + 718, 72)
    review._over(scene, imgs["storage_crate"][0], int(sx0 + 684 - 40), base - (72 - GROUND_PX) - 51)
    stand(imgs["lamp"][0], sx0 + 820, 160, piv_x=pivot_of("lamp")[0])
    review._label(scene, f"1x on the b-114 plains over the b-130 ground strips ({note}): the pilgrim rig on three 2 m pad modules, "
                         "the shelter (wall x4 + door), the surveyor, smelter, crates, lamp", 6, 6)
    rows.append(scene)
    # (2) every prop at 3x (frame 0) and each clip at 2x
    big = np.tile(np.array([0.62, 0.72, 0.72], np.float32), (192 * 3 + 30, W, 1))
    x = 8
    for name in PROPS:
        im = imgs[name][0]
        if x + im.shape[1] * 3 > W:
            break
        review._over(big, np.repeat(np.repeat(im, 3, 0), 3, 1), x, 22)
        review._label(big, name, x, 6, scale=1)
        x += im.shape[1] * 3 + 12
    rows.append(big)
    for name in ("shelter_door", "smelter", "lamp"):
        fn, fw, fh, clip, n, tiles = PROPS[name]
        r = np.tile(np.array([0.62, 0.72, 0.72], np.float32), (fh * 2 + 30, W, 1))
        review._label(r, f"{name} / {clip}: {n} frames at 12 fps ({'once' if name == 'shelter_door' else 'loop'}), 2x", 6, 4)
        for k, im in enumerate(imgs[name]):
            review._over(r, np.repeat(np.repeat(im, 2, 0), 2, 1), 8 + k * (fw * 2 + 8), 22)
            review._label(r, str(k), 10 + k * (fw * 2 + 8), 24, scale=1)
        rows.append(r)
    # (3) tiling: pad and wall modules side by side at 2x (the joins)
    t = np.tile(np.array([0.62, 0.72, 0.72], np.float32), (176 * 2 + 40, W, 1))
    review._label(t, "tiling at 2x: three pad modules and three wall modules side by side (edges must join)", 6, 4)
    for m in range(3):
        review._over(t, np.repeat(np.repeat(imgs["landing_pad"][0], 2, 0), 2, 1), 8 + m * 256, 22 + 176 * 2 - 96)
        review._over(t, np.repeat(np.repeat(imgs["shelter_wall"][0], 2, 0), 2, 1), 900 + m * 128, 22)
    rows.append(t)

    def join(a, b):
        return float(np.abs(a[:, -1, :].astype(np.int32) - b[:, 0, :].astype(np.int32)).mean())
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; tiling joins (mean |right - left|): pad {join(imgs['landing_pad'][0], imgs['landing_pad'][0]):.1f}, "
                        f"wall {join(imgs['shelter_wall'][0], imgs['shelter_wall'][0]):.1f} /255; ground line 10 px above each frame's bottom", 6, 8)
    sizes = []
    for name in PROPS:
        sh, _m, _p = sheet_meta(name, imgs[name])
        sizes.append(f"{name} {sh.shape[1]}x{sh.shape[0]}")
    review._label(foot, "sheets (<= 512^2, colour + json only, D-117): " + ", ".join(sizes), 6, 28)
    rows.append(foot)
    rows.append(boxes_panel(imgs, widths, W))
    if stamp_paths:
        st = np.tile(review.PAPER, (20 + 16 * len(stamp_paths), W, 1)).astype(np.float32)
        review._label(st, "exported files (time + hash):", 6, 4, scale=1)
        for i, p in enumerate(stamp_paths):
            review._label(st, f"{review.stamp_text(p)}  {os.path.relpath(p, review.ART)}".replace("\\", "/"), 6, 18 + 16 * i, scale=1)
        rows.append(st)
    img = np.vstack(rows)
    if not stamp_paths:
        review._label(img, time.strftime("%m-%d %H:%M") + " preview (not exported)", 2, img.shape[0] - 16)
    review.write(out, img)
    fakegp.restore()
    print("written", out)


SELF = {   # BLENDER's self-checks per prop for the motion and idle boxes (the rest are measured)
    "landing_pad": ("static module (the card gives the pad no clip); the ship's land puff and UNITY's root bob carry it", "static by the card"),
    "shelter_wall": ("static module (no clip on the card); tiles at 1 m", "static by the card"),
    "shelter_door": ("open 6: a cartoon swing in about the hinge with an overshoot, status light red -> green", "frame 0 shut; open once on use"),
    "smelter": ("working 8: belly breathes (squash), mouth glow pulses, two chimney puffs, sparks", "working loops while crafting"),
    "storage_crate": ("static (no clip on the card); stacks", "static by the card"),
    "lamp": ("flicker 4: drawn halo grows and shrinks, bulb tone steps", "flicker loops at night"),
}


def boxes_panel(imgs, widths, W):
    """The ten §9.7 boxes per prop: x measured, s BLENDER's self-check, blank = LEAD's to tick."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import v3
    lines = []
    for name in PROPS:
        ws = widths[name]
        outer = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
        inner = [w for w in ws if w[0] < v3.OUTER_SPLIT]
        ow = (min(w[1] for w in outer), max(w[2] for w in outer)) if outer else (0, 0)
        iw = (min(w[1] for w in inner), max(w[2] for w in inner)) if inner else (0, 0)
        ink_ok = v3.OUTER_PX[0] - 0.05 <= ow[0] and ow[1] <= v3.OUTER_PX[1] + 0.05 and inner and \
            v3.INNER_PX[0] - 0.05 <= iw[0] and iw[1] <= v3.INNER_PX[1] + 0.05
        sh, _meta, probs = sheet_meta(name, imgs[name])
        pal, off = v3.palette_hits(sh, "earth", tints=[("offwhite", 0.30), ("mustard", 0.22)])
        mot, idl = SELF[name]
        marks = [("ink", "x" if ink_ok else "!", f"{ow[0]:.1f}-{ow[1]:.1f} / {iw[0]:.1f}-{iw[1]:.1f} px, {len(inner) // max(len(imgs[name]), 1)} interior strokes per frame"),
                 ("cel", "x" if pal >= 0.98 else "!", f"{pal * 100:.1f}% palette (+ mid, deep; halo washes)"),
                 ("face", "s", "an object: no eyes, no mouth"),
                 ("twos", "x" if not probs else "!", "fps 12, caps" if not probs else probs[0][:40]),
                 ("motion", "s", mot), ("idle", "s", idl), ("original", "s", "our camp kit, no studio prop"),
                 ("sheet", "x" if not probs else "!", "png + json, <= 512^2"), ("budget", "x", "one small sheet; UNITY confirms"),
                 ("style", " ", "LEAD, against the C0 style test")]
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


if __name__ == "__main__":
    main(sys.argv[1])
