"""B-233 (D-187; BLENDER's 12:2x proposal, accepted in cycle 297): the catalogue's site icons. CataloguePanel shows an entry's
icon at 64 px and, until it is scanned, as a dark silhouette ("a shape to look for"), so each icon is the site's own silhouette
taken from its props' art, in the style, size and ink weight of B-223's icons/catalogue/camp (B-199's item-icon contract:
128x128 @ PPU 128, pivot centre, inside the 2 px margin), in its own planet's palette. No faces: no single round window or dial
on a rounded body or a box (it is an eye: the 19:15 sheet's hauler, station pod, harvester box and beacon box), never two side by
side; hatches, slots and rows of three instead; the vault's hub is a plain nut. Nothing weapon-like (D-087: the Warden sites are
guarded survey posts).

  key = icons/catalogue/<PoiDef.label lowercased, spaces as _> (D-187). Two labels differ from the PoiDef ids the card lists:
  MERIDIAN BEACON (id mercury_beacon) -> meridian_beacon, SOLARITE (id solarite_field) -> solarite. NAMES holds them in one place.

  earth    survey_archive    the bunker front: a concrete face under a hazard-striped slab, the teal sign, the steel shutter in
                             its brown frame with a brass handle, a red lamp (props/earth/archive_door)
           launch_complex    the teal lattice gantry on its concrete pad: two red-striped service arms with their hoses, the
                             brass lift cab, the railed top deck and its red lamp; the red tower's bent stump beside it
                             (props/earth/launch_gantry, launch_tower_ruin)
  mars     halcyon_hauler    the crashed hull: a butterscotch barrel section nose-up in a regolith mound, its cream stripe, a
                             cargo hatch, rust patches, the torn end (props/mars/hauler_hull_a)
           warden_outpost    a Warden pylon (the cream taper, two teal panels, the brass signal cap with its arcs) and the small
                             tripod beacon on a levelled platform (props/mars/warden_pylon, meridian_beacon)
  mercury  flare_shelter     the low dome under three rows of gold heat shingles on its dark slab, the violet hatch, the T vent
                             (props/mercury/flare_shelter)
           warden_vault      the dark stone arch round the round teal vault door: six spokes, a brass hub nut, the brass bell on
                             the keystone (props/mercury/warden_vault_gate)
           meridian_beacon   the tripod beacon, big: the lantern under its cap, the banded mast, the brass instrument box with
                             its gauge slot, light ticks either side (props/mercury/meridian_beacon)
           solarite          the crystal field: three gold spires out of a dark rock, a small pair beside them, one glint
                             (props/mercury/solarite_cluster)
  venus    meridian_station  the aerostat: the apricot balloon over a cream hull pod (brass bands, three small portholes) on its
                             railed deck, a cloud under it (props/venus/aerostat_balloon, station_hull_a, aerostat_deck)
           vent_harvester    the tripod over a vent: the cream sampler box with its sight glass under a brass plate, the dark hood,
                             the teal hose, the vent's red mouth (props/venus/vent_harvester)

  python -I build_site_icons_v3.py <review png>    the lock-free sheet: the eleven site icons (B-223's camp included) at 128 / 48
                                                    / 40 per planet, a row at 64 as the catalogue shows them, the same row as
                                                    unscanned silhouettes, beside item icons as exported
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_rig_tools_v3 as RT  # noqa: E402  (installs fakegp; _ov)
import build_icons_items_v3 as IT  # noqa: E402  (mats per planet, lump / prism / glint, SIZE / PPU)
from meridian import v3  # noqa: E402

G = RT.G
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
GZ = -0.31                                         # the ground's top under a site (the one-strip ground of Mars / Mercury / Venus)
EZ = -0.28                                         # Earth's: the grass strip's top, as the camp icon's


# ---------------------------------------------------------------- helpers (metres, centre origin, x right, z up; 1 m = 128 px)
def R(x0, z0, x1, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


def arc(cx, cz, r, a0, a1, n=12, rz=None):
    """Points on an ellipse from a0 to a1 degrees, both ends included."""
    rz = r if rz is None else rz
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cz + rz * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def C(cx, cz, r, n=20, rz=None):
    rz = r if rz is None else rz
    return [(cx + r * math.cos(TAU * i / n), cz + rz * math.sin(TAU * i / n)) for i in range(n)]


def hose(pts, w):
    return G.hose_outline(pts, w)


def turned(deg, sx, sz):
    """Local coordinates -> the icon, turned `deg` about the local origin and moved to (sx, sz)."""
    a = math.radians(deg)
    ux, uz = math.cos(a), math.sin(a)
    return lambda pts: [(sx + x * ux - z * uz, sz + x * uz + z * ux) for x, z in pts]


def fill(d, M, pts, tone):
    G.stroke(d, pts, M[tone], 0.0, cyclic=True)


def inked(d, M, pts, tone, r=None):
    G.stroke(d, pts, M[tone + "_i"], O if r is None else r, cyclic=True)


def outline(d, M, pts, r=None):
    G.stroke(d, pts, M["ink"], O if r is None else r, cyclic=True)


def line(d, M, pts, r=None):
    G.stroke(d, pts, M["ink"], I if r is None else r)


def ground(d, M, tone, x=0.41):
    """One ground strip, its top on GZ."""
    inked(d, M, hose([(-x, GZ - 0.035), (x, GZ - 0.035)], 0.07), tone)


def earth_ground(d, M):
    """The camp icon's ground: soil with the grass strip on it (its top on EZ)."""
    inked(d, M, hose([(-0.40, -0.36), (0.40, -0.36)], 0.06), "brown_sh")
    inked(d, M, hose([(-0.42, -0.31), (0.42, -0.31)], 0.06), "green")


# ---------------------------------------------------------------- shared pieces
def beacon(d, M, cx, z0, h, rays=False, detail=True):
    """The Meridian tripod beacon, h tall from its feet at z0 (the icon's own chunky proportion)."""
    def P(pts):
        return [(cx + x * h, z0 + z * h) for x, z in pts]
    for fx in (-1.0, 1.0):
        inked(d, M, hose(P([(0.08 * fx, 0.40), (0.32 * fx, 0.02)]), 0.07 * h), "brown", I)             # the outer legs
        inked(d, M, hose(P([(0.26 * fx, 0.015), (0.38 * fx, 0.015)]), 0.045 * h), "brown", I)          # their feet
    inked(d, M, hose(P([(0.0, 0.34), (0.0, 0.03)]), 0.045 * h), "brown", I)                            # the middle leg
    mast = P(R(-0.045, 0.46, 0.045, 0.78))
    fill(d, M, mast, "off")
    for z in (0.52, 0.66):                                                                              # its teal bands
        fill(d, M, P(R(-0.045, z, 0.045, z + 0.065)), "teal")
    outline(d, M, mast, I)
    box = P(R(-0.15, 0.30, 0.15, 0.48))
    fill(d, M, box, "mustard")                                                                          # the instrument box
    fill(d, M, P(R(0.07, 0.30, 0.15, 0.48)), "mustard_sh")
    outline(d, M, box)
    if detail:                                                                                          # its gauge: a slot with two
        inked(d, M, P(R(-0.10, 0.355, 0.03, 0.425)), "off", I)                                          # ticks (the 19:15 sheet at 2x:
        for x in (-0.055, -0.015):                                                                      # a round dial in the box's
            line(d, M, P([(x, 0.355), (x, 0.39)]), I * 0.8)                                             # middle was one eye)
    inked(d, M, P(R(-0.08, 0.78, 0.08, 0.90)), "mustard", I)                                            # the lantern, lit
    if detail:
        for x in (-0.027, 0.027):
            line(d, M, P([(x, 0.78), (x, 0.90)]), I * 0.8)
    inked(d, M, P([(-0.11, 0.90), (0.11, 0.90), (0.08, 0.96), (0.0, 1.0), (-0.08, 0.96)]), "brown")    # its cap
    if rays:                                                                                            # light ticks either side
        for a in (30, 0, -30, 150, 180, 210):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            line(d, M, P([(0.15 * ca, 0.84 + 0.15 * sa), (0.30 * ca, 0.84 + 0.30 * sa)]), I * 1.2)


def pylon(d, M, cx, z0):
    """A Warden pylon standing on z0: the foot, the cream taper with two teal panels, the brass signal cap and its arcs."""
    inked(d, M, R(cx - 0.115, z0, cx + 0.115, z0 + 0.055), "brown")
    zb, zt, wb, wt = z0 + 0.055, z0 + 0.52, 0.085, 0.04

    def half(f):
        return wb + (wt - wb) * f

    def zf(f):
        return zb + (zt - zb) * f
    shaft = [(cx - wb, zb), (cx + wb, zb), (cx + wt, zt), (cx - wt, zt)]
    fill(d, M, shaft, "off")
    fill(d, M, [(cx + wb * 0.45, zb), (cx + wb, zb), (cx + wt, zt), (cx + wt * 0.45, zt)], "off_sh")    # the shade, right
    for f0, f1 in ((0.10, 0.48), (0.57, 0.87)):                                                         # the teal panels
        a, b = half(f0) - 0.024, half(f1) - 0.022
        inked(d, M, [(cx - a, zf(f0)), (cx + a, zf(f0)), (cx + b, zf(f1)), (cx - b, zf(f1))], "teal", I)
    outline(d, M, shaft)
    r = wt + 0.014
    inked(d, M, [(cx - r, zt)] + arc(cx, zt + 0.015, r, 180, 0, 10, rz=0.075) + [(cx + r, zt)], "mustard")   # the signal cap
    fill(d, M, R(cx - 0.012, zt + 0.022, cx + 0.012, zt + 0.058), "brown")                              # its slot
    for rr in (0.10, 0.135):                                                                            # the signal arcs
        line(d, M, arc(cx, zt + 0.04, rr, 25, 65, 6))
        line(d, M, arc(cx, zt + 0.04, rr, 115, 155, 6))


# ---------------------------------------------------------------- Earth
def survey_archive(d, M):
    earth_ground(d, M)
    wall = R(-0.35, EZ, 0.35, 0.20)
    fill(d, M, wall, "off_sh")                                                                          # the concrete face
    fill(d, M, R(0.23, EZ, 0.35, 0.20), "off_dp")                                                       # its shaded end
    line(d, M, [(-0.35, 0.05), (-0.24, 0.05)])                                                          # block seams
    line(d, M, [(0.24, -0.10), (0.35, -0.10)])
    line(d, M, [(-0.31, 0.16), (-0.28, 0.10), (-0.305, 0.06)], I * 0.8)                                 # a crack
    outline(d, M, wall)
    slab = [(-0.40, 0.20), (0.40, 0.20), (0.38, 0.30), (-0.38, 0.30)]
    fill(d, M, slab, "mustard")                                                                         # the hazard-striped slab
    for k in range(6):
        x0 = -0.37 + 0.125 * k
        fill(d, M, [(x0, 0.20), (x0 + 0.06, 0.20), (x0 + 0.10, 0.30), (x0 + 0.04, 0.30)], "off")
    outline(d, M, slab)
    inked(d, M, R(-0.13, 0.085, 0.13, 0.165), "teal", I)                                                # the sign
    fill(d, M, R(-0.03, 0.11, 0.09, 0.14), "off")
    fill(d, M, [(-0.10, 0.10), (-0.05, 0.10), (-0.075, 0.15)], "mustard")
    inked(d, M, R(-0.23, EZ, 0.23, 0.05), "brown")                                                      # the door frame
    door = R(-0.185, EZ, 0.185, 0.01)
    fill(d, M, door, "sky")                                                                             # the steel shutter
    fill(d, M, R(0.09, EZ, 0.185, 0.01), "sky_sh")
    fill(d, M, R(-0.185, EZ, 0.185, -0.225), "mustard")                                                 # its hazard foot
    for z in (-0.07, -0.15, -0.225):
        line(d, M, [(-0.185, z), (0.185, z)])
    line(d, M, [(0.0, 0.01), (0.0, -0.225)])
    outline(d, M, door, I)
    inked(d, M, R(0.03, -0.135, 0.075, -0.085), "mustard", I)                                           # the handle
    inked(d, M, C(0.295, 0.02, 0.028, 12), "red", I)                                                    # the lamp


def launch_complex(d, M):
    earth_ground(d, M)
    inked(d, M, R(-0.37, EZ, 0.40, -0.235), "off_sh")                                                   # the concrete pad
    pz = -0.235
    for a, b in (((-0.355, pz), (-0.235, -0.08)), ((-0.245, pz), (-0.345, -0.08))):                     # the red tower's stump
        inked(d, M, hose([a, b], 0.02), "red_sh", I * 0.8)
    inked(d, M, hose([(-0.35, -0.08), (-0.235, -0.08)], 0.024), "red", I)
    inked(d, M, hose([(-0.245, pz), (-0.23, -0.04)], 0.028), "red", I)
    inked(d, M, hose([(-0.355, pz), (-0.34, 0.01), (-0.285, 0.085)], 0.028), "red", I)                  # (one leg bent over)
    xl, xr, top = -0.13, 0.07, 0.31
    zs = [pz + (top - pz) * k / 3 for k in range(4)]
    for z0, z1 in zip(zs, zs[1:]):                                                                      # the gantry's braces
        inked(d, M, hose([(xl, z0), (xr, z1)], 0.022), "teal_sh", I * 0.8)
        inked(d, M, hose([(xr, z0), (xl, z1)], 0.022), "teal_sh", I * 0.8)
    for z in zs[1:3]:
        inked(d, M, hose([(xl, z), (xr, z)], 0.026), "teal", I)
    for x in (xl, xr):                                                                                  # its legs
        inked(d, M, hose([(x, pz), (x, top)], 0.034), "teal", I)
    cab = R(-0.105, -0.20, 0.045, -0.085)
    fill(d, M, cab, "mustard")                                                                          # the lift cab
    fill(d, M, R(-0.105, -0.19, 0.045, -0.172), "red")
    outline(d, M, cab)
    inked(d, M, R(-0.075, -0.155, -0.005, -0.11), "sky", I)
    for z0 in (0.165, -0.02):                                                                           # the service arms
        arm = R(xr + 0.017, z0, 0.35, z0 + 0.05)
        fill(d, M, arm, "off")
        for k in range(4):
            x0 = 0.10 + 0.062 * k
            fill(d, M, [(x0, z0), (x0 + 0.03, z0), (x0 + 0.055, z0 + 0.05), (x0 + 0.025, z0 + 0.05)], "red")
        outline(d, M, arm, I)
        inked(d, M, R(0.345, z0 - 0.01, 0.375, z0 + 0.06), "brown", I)
        line(d, M, [(0.30, z0), (0.305, z0 - 0.045), (0.29, z0 - 0.085), (0.27, z0 - 0.11)], I * 1.3)   # its hose
    inked(d, M, R(-0.18, top, 0.12, top + 0.035), "brown")                                              # the top deck
    for x in (-0.16, 0.10):                                                                             # its rail
        line(d, M, [(x, top + 0.035), (x, top + 0.09)])
    line(d, M, [(-0.16, top + 0.09), (0.10, top + 0.09)])
    inked(d, M, C(-0.03, top + 0.115, 0.022, 10), "red", I)                                             # the lamp


# ---------------------------------------------------------------- Mars
def halcyon_hauler(d, M):
    T = turned(12, 0.02, -0.02)
    torn = [(-0.36, -0.17), (-0.33, -0.10), (-0.37, -0.04), (-0.335, 0.03), (-0.375, 0.09)]            # the torn end, bottom to top
    body = [(-0.345, 0.17)] + arc(0.20, 0.0, 0.17, 90, -90, 12) + torn
    fill(d, M, T(body), "mustard")                                                                      # the hull section
    fill(d, M, T([(-0.335, -0.09), (0.344, -0.09)] + arc(0.20, 0.0, 0.17, -32, -90, 6) + [(-0.36, -0.17), (-0.33, -0.10)]), "mustard_sh")
    fill(d, M, T([(-0.335, 0.03), (0.367, 0.03), (0.359, 0.06), (0.344, 0.09), (-0.375, 0.09)]), "off")  # the cream stripe
    for cx, cz, rx, rz, seed in ((-0.22, 0.125, 0.05, 0.025, 41), (0.17, -0.06, 0.045, 0.03, 42), (0.10, 0.13, 0.025, 0.018, 43)):
        fill(d, M, T(IT.lump(cx, cz, rx, rz, seed, n=8)), "red")                                        # rust
    for x in (-0.14, 0.06):                                                                             # panel seams
        line(d, M, T([(x, 0.17), (x, -0.17)]))
    outline(d, M, T(body))
    inked(d, M, T(R(-0.105, -0.135, 0.015, -0.005)), "off", I)                                          # a cargo hatch between the seams
    line(d, M, T([(-0.01, -0.095), (-0.01, -0.045)]))                                                   # and its handle (the 19:15 sheet
    #                                                                                                     at 2x: one round porthole by
    #                                                                                                     the rounded nose was the eye of
    #                                                                                                     a grub lying on the mound)
    inked(d, M, [(-0.43, -0.33), (-0.41, -0.26), (-0.34, -0.19), (-0.26, -0.21), (-0.18, -0.17), (-0.08, -0.19), (0.02, -0.14),
                 (0.12, -0.145), (0.22, -0.11), (0.31, -0.15), (0.39, -0.24), (0.43, -0.33)], "red_sh")   # the regolith it ploughed up
    ground(d, M, "red_dp")


def warden_outpost(d, M):
    ground(d, M, "red_sh")
    inked(d, M, R(-0.37, GZ, 0.37, GZ + 0.055), "brown")                                                # the levelled platform
    z0 = GZ + 0.055
    pylon(d, M, -0.16, z0)
    beacon(d, M, 0.17, z0, 0.42, detail=False)                                                          # (its feet inside the platform)


# ---------------------------------------------------------------- Mercury
def flare_shelter(d, M):
    ground(d, M, "off_sh")
    zb = GZ + 0.055
    inked(d, M, hose([(0.09, zb + 0.39), (0.09, zb + 0.49)], 0.035), "brown", I)                        # the T vent (its foot
    inked(d, M, hose([(0.045, zb + 0.49), (0.135, zb + 0.49)], 0.035), "brown", I)                      # behind the dome)
    dome = arc(0.0, zb, 0.37, 0, 180, 24, rz=0.42)
    fill(d, M, dome, "teal")
    fill(d, M, [(0.20, zb)] + arc(0.0, zb, 0.37, 0, 57, 8, rz=0.42), "teal_sh")                         # the shade, right
    inked(d, M, C(-0.19, zb + 0.035, 0.05, 14, rz=0.022), "sky", I)                                     # the hatch
    w = 0.08
    for top, n in ((0.17, 8), (0.27, 7), (0.37, 4)):                                                    # the heat shingles, the
        for k in range(n):                                                                              # upper rows over the lower
            x = (k - (n - 1) / 2) * w
            sh = [(x - w / 2, zb + top), (x + w / 2, zb + top)] + arc(x, zb + top - 0.055, w / 2, 0, -180, 6)
            inked(d, M, sh, "mustard_sh" if x > 0.10 else "mustard", I)
    outline(d, M, dome)
    inked(d, M, R(-0.41, GZ, 0.41, zb), "brown")                                                        # the slab


def warden_vault(d, M):
    ground(d, M, "off_sh")
    cz = -0.03
    arch = [(0.40, GZ)] + arc(0.0, cz, 0.40, 0, 180, 20) + [(-0.40, GZ), (-0.28, GZ)] + arc(0.0, cz, 0.28, 180, 0, 16) + [(0.28, GZ)]
    inked(d, M, arch, "brown")                                                                          # the stone arch
    for a in (30, 60, 82, 98, 120, 150):                                                                # its stones
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        line(d, M, [(0.28 * ca, cz + 0.28 * sa), (0.40 * ca, cz + 0.40 * sa)])
    for fx in (-1, 1):
        line(d, M, [(0.28 * fx, -0.17), (0.40 * fx, -0.17)])
    dz, dr = -0.02, 0.285
    door = C(0.0, dz, dr, 40)
    fill(d, M, door, "teal")                                                                            # the round vault door
    fill(d, M, arc(0.0, dz, dr, -55, 55, 12), "teal_sh")
    outline(d, M, C(0.0, dz, 0.215, 32), I)
    for a in (20, 80, 140, 200, 260, 320):                                                              # six spokes
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        line(d, M, [(0.075 * ca, dz + 0.075 * sa), (0.205 * ca, dz + 0.205 * sa)], I * 1.2)
    outline(d, M, door)
    inked(d, M, C(0.0, dz, 0.07, 6), "mustard", I)                                                      # the hub nut (plain)
    inked(d, M, [(-0.04, 0.365), (0.04, 0.365), (0.028, 0.43), (0.0, 0.45), (-0.028, 0.43)], "mustard", I)   # the bell


def meridian_beacon(d, M):
    ground(d, M, "off_sh")
    beacon(d, M, 0.0, GZ, 0.72, rays=True)


def solarite(d, M):
    ground(d, M, "off_sh")
    IT.prism(d, M, -0.29, -0.11, -0.25, 0.08, "mustard", "mustard_sh", lean=-0.07)                      # the spires
    IT.prism(d, M, 0.01, 0.19, -0.25, 0.14, "mustard_sh", "mustard_dp", lean=0.06)
    IT.prism(d, M, -0.17, 0.07, -0.26, 0.36, "mustard", "mustard_sh", lean=0.015)
    inked(d, M, IT.lump(-0.05, -0.26, 0.30, 0.065, 77, n=11, jit=0.10), "brown")                        # the dark rock they grew on
    IT.prism(d, M, 0.25, 0.345, -0.27, -0.04, "mustard", "mustard_sh", lean=0.03)                       # a small pair beside
    IT.prism(d, M, 0.32, 0.40, -0.27, -0.13, "mustard_sh", "mustard_dp", lean=0.045)
    inked(d, M, IT.lump(0.33, -0.285, 0.10, 0.04, 78, n=8, jit=0.10), "brown")
    IT.glint(d, M, -0.035, 0.405, s=0.035)                                                              # one glint


# ---------------------------------------------------------------- Venus
def meridian_station(d, M):
    cloud = [(-0.37, -0.33)]
    for cx, r in ((-0.30, 0.07), (-0.15, 0.085), (0.0, 0.07), (0.15, 0.085), (0.30, 0.07)):
        cloud += arc(cx, -0.345, r, 180, 360, 6)
    inked(d, M, cloud + [(0.37, -0.33)], "off", I)                                                      # the cloud under it
    for fx in (-1, 1):                                                                                  # the balloon's lines
        line(d, M, [(0.055 * fx, -0.01), (0.12 * fx, -0.085)])
    bx, bz, rx, rz = 0.0, 0.21, 0.215, 0.205
    balloon = C(bx, bz, rx, 40, rz=rz)
    fill(d, M, balloon, "sky")                                                                          # the balloon
    fill(d, M, arc(bx, bz, rx, -70, 70, 12, rz=rz) + arc(bx, bz, rx * 0.5, 70, -70, 12, rz=rz), "sky_sh")
    for k in (-0.55, 0.0, 0.55):                                                                        # its gores
        line(d, M, [(bx + k * rx * math.cos(math.radians(t)), bz + rz * math.sin(math.radians(t))) for t in range(-80, 81, 20)], I * 0.8)
    outline(d, M, balloon)
    inked(d, M, C(bx, bz + rz - 0.003, 0.05, 14, rz=0.014), "mustard", I)                               # its cap and collar
    inked(d, M, C(bx, bz - rz - 0.005, 0.065, 14, rz=0.018), "mustard", I)
    dk = -0.275
    for fx in (-1, 1):                                                                                  # the deck's rail
        inked(d, M, hose([(0.36 * fx, dk), (0.36 * fx, dk + 0.085)], 0.022), "mustard", I)
        line(d, M, [(0.36 * fx, dk + 0.075), (0.26 * fx, dk + 0.075)])
    r = 0.06
    hull = (arc(0.25 - r, dk + r, r, -90, 0, 4) + arc(0.25 - r, -0.085 - r, r, 0, 90, 4)
            + arc(-0.25 + r, -0.085 - r, r, 90, 180, 4) + arc(-0.25 + r, dk + r, r, 180, 270, 4))
    fill(d, M, hull, "off")                                                                             # the hull pod
    fill(d, M, [(-0.19, dk), (0.19, dk), (0.24, dk + 0.04), (-0.24, dk + 0.04)], "off_sh")
    for x in (-0.135, 0.135):                                                                           # its brass bands
        fill(d, M, R(x - 0.02, dk, x + 0.02, -0.085), "mustard")
        for e in (-0.02, 0.02):
            line(d, M, [(x + e, dk), (x + e, -0.085)], I * 0.8)
    outline(d, M, hull)
    for x in (-0.068, 0.0, 0.068):                                                                      # three small portholes in a row:
        inked(d, M, C(x, -0.175, 0.026, 12), "teal", I)                                                 # a gondola's windows (one large
    #                                                                                                     ring in the pod's middle was a
    #                                                                                                     one-eyed head under the balloon)
    deck = R(-0.39, -0.335, 0.39, dk)
    inked(d, M, deck, "mustard_sh")                                                                     # the deck
    for x in (-0.26, -0.13, 0.0, 0.13, 0.26):
        line(d, M, [(x, -0.335), (x, dk)], I * 0.8)


def vent_harvester(d, M):
    ground(d, M, "brown")
    inked(d, M, C(0.0, GZ, 0.11, 16, rz=0.028), "red", I)                                               # the vent's mouth
    inked(d, M, hose([(0.12, 0.20), (0.22, 0.19), (0.285, 0.10), (0.30, -0.10), (0.27, GZ + 0.01)], 0.035), "teal", I)   # the hose
    for fx in (-1, 1):                                                                                  # the legs
        inked(d, M, hose([(0.10 * fx, 0.30), (0.33 * fx, GZ)], 0.04), "brown", I)
    line(d, M, [(0.0, -0.20), (0.0, GZ + 0.01)], I * 1.3)                                               # the probe
    inked(d, M, hose([(0.0, -0.05), (0.0, 0.11)], 0.035), "teal", I)                                    # the stem
    inked(d, M, [(-0.065, -0.05), (0.065, -0.05), (0.15, -0.21), (-0.15, -0.21)], "brown")              # the hood
    box = R(-0.13, 0.10, 0.13, 0.30)
    fill(d, M, box, "off")                                                                              # the sampler box
    fill(d, M, R(0.06, 0.10, 0.13, 0.30), "off_sh")
    outline(d, M, box)
    inked(d, M, R(-0.09, 0.135, -0.04, 0.265), "teal", I)                                               # its sight glass, two level
    for z in (0.18, 0.22):                                                                              # ticks (a round porthole made
        line(d, M, [(-0.09, z), (-0.065, z)], I * 0.8)                                                  # the box a one-eyed head on legs)
    inked(d, M, R(-0.17, 0.30, 0.17, 0.345), "mustard")                                                 # the brass plate
    inked(d, M, C(0.0, 0.37, 0.022, 10), "mustard", I)


# ---------------------------------------------------------------- kit / export
# (name = the PoiDef label lowercased with _ for spaces, D-187; planet = its palette; the drawing; the json note)
SITES = (
    ("survey_archive", "earth", survey_archive, "the Survey Archive (the bunker front: the striped slab, the sign, the steel shutter)"),
    ("launch_complex", "earth", launch_complex, "the Launch Complex (the teal gantry on its pad, the striped arms, the cab; the red stump)"),
    ("halcyon_hauler", "mars", halcyon_hauler, "the Halcyon Hauler (the crashed hull section in its regolith mound, a cargo hatch)"),
    ("warden_outpost", "mars", warden_outpost, "the Warden Outpost (a pylon with its signal cap and the tripod beacon on a platform)"),
    ("flare_shelter", "mercury", flare_shelter, "the Flare Shelter (the shingled dome on its slab, the hatch, the T vent)"),
    ("warden_vault", "mercury", warden_vault, "the Warden Vault (the stone arch, the round spoked door, the bell)"),
    ("meridian_beacon", "mercury", meridian_beacon, "the Meridian Beacon (PoiDef id mercury_beacon: the tripod beacon, lit)"),
    ("solarite", "mercury", solarite, "the Solarite field (PoiDef id solarite_field: gold spires out of dark rock)"),
    ("meridian_station", "venus", meridian_station, "the Meridian Station (the aerostat: the balloon, the hull pod, the deck, a cloud)"),
    ("vent_harvester", "venus", vent_harvester, "the Vent Harvester (the tripod sampler over a vent's red mouth, the hose)"),
)
NAMES = [s[0] for s in SITES]
PLANET = {s[0]: s[1] for s in SITES}


def render(fn, planet, seed=5):
    gp = IT.fakegp.FakeGP()
    M = IT.mats(gp, planet)
    d = IT.fakegp.FakeDrawing()
    fn(d, M)
    return IT.GR.render_frame(IT.fakegp.strokes_of(d, gp), IT.SIZE, IT.SIZE, IT.PPU, (0.5, 0.5), ss=4, seed=seed)[0]


def kit():
    return [(f"icons/catalogue/{n}", render(fn, planet), {"palette": planet, "ppu": IT.PPU, "pivot": [0.5, 0.5], "note": "B-233: the catalogue's " + note})
            for n, planet, fn, note in SITES]


def checks(key, img, planet):
    m = v3.EDGE_MARGIN
    out = []
    hit = v3.palette_hits(img, planet)[0]
    if hit < 0.995:
        out.append(f"{key}: palette {hit * 100:.1f}%")
    if img[:m, :, 3].any() or img[-m:, :, 3].any() or img[:, :m, 3].any() or img[:, -m:, 3].any():
        out.append(f"{key}: touches the {m} px edge")
    return out


def export(art):
    from meridian import pngio
    built, problems = [], []
    for key, img, extra in kit():
        problems += checks(key, img, extra["palette"])
        built.append((key, img, {"key": key, "style": "v3", "width": img.shape[1], "height": img.shape[0], **extra}))
    if problems:
        raise ValueError("B-233 checks: " + "; ".join(problems))
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
    return [f"icons/catalogue/{n}" for n in NAMES]


# ---------------------------------------------------------------- the review sheet
def silhouette(im):
    """An unscanned entry as CataloguePanel tints it (Color(0, 0, 0, 0.7)): black, 70 % of the icon's alpha."""
    s = im.copy()
    s[..., :3] = 0
    s[..., 3] = np.rint(s[..., 3].astype(np.float32) * 0.7).astype(np.uint8)
    return s


def preview(out, footnote=None):
    import time
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from build_tool_icons_v3 import shrink
    K = [(k, img, e["palette"]) for k, img, e in kit()]
    camp_note = ""
    try:                                                                                               # B-223's camp icon (its source,
        import build_bay_v3 as BB                                                                      # exported or not)
        K = [("icons/catalogue/camp", BB.camp(), "earth")] + K
    except Exception as ex:  # noqa: BLE001  (the sheet still shows the ten)
        camp_note = f" | camp NOT SHOWN ({type(ex).__name__}: {ex})"
    neigh = []
    for k in ("iron/base", "hematite/base", "solarite/base", "sulfur/base"):
        p = os.path.join(ART, "icons", *k.split("/")) + "_color.png"
        if os.path.isfile(p):
            neigh.append(("icons/" + k, pngio.read_png_np(p)))
    paper = np.array(review.PAPER, np.float32)
    W = 1300
    rows = []
    head = np.tile(paper, (28, W, 1)).astype(np.float32)
    review._label(head, "B-233 the catalogue's site icons (D-187: icons/catalogue/<label>) in the camp icon's style: each at 128 / 48 / 40" + camp_note, 6, 8)
    rows.append(head)

    def cell_row(items, label):
        r = np.tile(paper, (196, W, 1)).astype(np.float32)
        review._label(r, label, 6, 4, scale=1)
        x = 10
        for name, im in items:
            RT._ov(r, im, x, 24)
            RT._ov(r, shrink(im, 48), x + 136, 24)
            RT._ov(r, shrink(im, 40), x + 192, 24)
            review._label(r, name.replace("icons/", ""), x, 166, scale=1)
            x += 256
        return r
    for planet in ("earth", "mars", "mercury", "venus"):
        rows.append(cell_row([(k, im) for k, im, p in K if p == planet], f"{planet} (its own palette)"))
    rows.append(cell_row(neigh, "item icons as exported (the catalogue's mineral entries)"))
    both = [(k, im) for k, im, _p in K] + neigh
    for what, f in (("a row at 64 px as the catalogue shows them (the sites, then the item icons)", lambda im: im),
                    ("the same row unscanned: CataloguePanel's silhouette (black at 70 %), the shape to look for", silhouette)):
        r = np.tile(paper, (64 + 34, W, 1)).astype(np.float32)
        review._label(r, what, 6, 4, scale=1)
        x = 10
        for _n, im in both:
            RT._ov(r, f(shrink(im, 64)), x, 22)
            x += 64 + 16
        rows.append(r)
    lines = []
    for key, img, planet in K:
        bad = checks(key, img, planet)
        hit = v3.palette_hits(img, planet)[0] * 100
        lines.append(f"{key}: {img.shape[1]}x{img.shape[0]}, {planet} palette {hit:.1f}%" + ("; " + "; ".join(bad) if bad else ", inside the 2 px margin"))
    foot = np.tile(paper, (24 + 16 * ((len(lines) + 1) // 2), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6 + (i % 2) * 640, 6 + 16 * (i // 2), scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-233 design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_site_icons_v3.py <review png>
    preview(sys.argv[1])
    RT.fakegp.restore()
