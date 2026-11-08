"""B-175 (D-161 (1), D-162 (1)-(4); the owner: "even out the ground ... more cartoony"): ground art that bends. The ground
is one smoothed cartoon curve (UNITY's U-156 mesh band along it), digging carves round ink-rimmed scoops, and under the
surface is a drawn cross-section. Per planet (Earth first), drawn with gp_draw (fakegp + numpy outside Blender):

  terrain/<p>/ground_band   512x64, tiles in x (8 m)   the bendable top band: the turf (Earth) with its INK EDGE ON THE
                            SURFACE ROW (row 24 from the top), only low rounded scallops above it (they survive any bend),
                            the topsoil under it to a ragged edge with a few roots; transparent below (the fill shows)
  terrain/<p>/ground_fill   512x512, tiles both ways   the cartoon cross-section digging reveals: strata bands, pebbles,
                            stones, a water lens, a fossil, burrows; world-space, under the band
  terrain/<p>/ground_decor  64x64 x6, pivot at the base the things that must stay UPRIGHT on a slope (UNITY scatters them
                            along the curve, never rotated): three grass tufts, two stones, a flower
  terrain/<p>/ground_lip    128x96, pivot at the brink  a rounded grassy overhang for a cliff's lip (drawn for a drop to the
                            right; mirror x for the left)
  terrain/<p>/dig_rim       256x16, tiles in x (4 m)    the ink line round a carved scoop's wall: the ink on row 4, a deep-tone
                            band into the solid below it, transparent on the air side (map it along the hole's outline,
                            solid side down)
  terrain/<p>/dig_puff      128x128, puff 8 (once)      the dirt puff a dig throws: round dirt clouds and flying clods

  python -I build_ground_v3.py <preview dir> [planet]   lock-free curve preview: review_b175_<planet>_curve_preview.png
                                                        (the current strip on a test profile two ways, then the new band +
                                                        fill + upright decor + lip + a dug scoop, the surveyor at 1x, the
                                                        pieces) + the pieces' sheets in <preview dir>/b175/
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp, v3  # noqa: E402

try:                                    # inside Blender: the real gp_draw (not needed: every piece is numpy-only)
    import bpy
    if not hasattr(bpy, "data"):
        raise ImportError
    import gp_draw as G
except ImportError:
    bpy = None
    G = fakegp.install()
import gp_raster as GR  # noqa: E402

O, I = G.OUTER, G.INNER
PPU = 64
ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
TAU = 2 * math.pi

BAND_W, BAND_H, SURF_ROW = 512, 64, 24          # the band: 8 m repeat, the surface 24 px from the top
FILL = 512                                       # the fill tile: 8 m x 8 m
RIM_W, RIM_H, RIM_ROW = 256, 16, 4


def _mix(a, b, t):
    return v3.rgb_hex([x * (1 - t) + y * t for x, y in zip(v3.hex_rgb(a), v3.hex_rgb(b))])


def colours(planet):
    """Every role is ONE palette tone (a colour, its mid shadow or its deep shadow, §9 v4), so the cel box reads 100 %."""
    P = v3.PALETTES[planet]
    sh = lambda k: v3.shadow_of(P[k], planet)  # noqa: E731
    dp = lambda k: v3.deep_of(P[k], planet)  # noqa: E731
    if planet == "earth":
        return {"top": P["green"], "top_sh": sh("green"), "topsoil": P["brown"],
                "soil": dp("mustard"), "soil_sh": dp("red"), "soil_dp": P["brown"], "clay": sh("mustard"), "red": sh("red"),
                "stone": sh("sky"), "stone_sh": dp("sky"), "pebble": sh("offwhite"), "bone": P["offwhite"], "lens": P["teal"],
                "flower": P["mustard"], "petal": P["offwhite"], "dust": sh("mustard"), "dust_sh": dp("mustard"), "clod": P["brown"]}
    if planet == "mars":                        # D-163 cross-section (LEAD 04:1x): rust dust crust, Gale layering, hematite, basalt, ice
        return {"top": P["red"], "top_sh": sh("red"), "topsoil": dp("red"), "speck": P["offwhite"],
                "soil": sh("sky"), "soil_sh": dp("red"), "soil_dp": P["brown"], "ochre": sh("mustard"), "redbrown": dp("red"), "salmon": P["sky"],
                "basalt": dp("teal"), "basalt_sh": P["brown"], "hem": P["brown"], "hem_hi": sh("offwhite"), "ice": P["offwhite"], "ice_sh": sh("teal"),
                "rock": dp("sky"), "rock_sh": P["brown"], "pebble": sh("offwhite"), "frost": P["offwhite"], "frost_sh": P["teal"],
                "ripple": sh("mustard"), "ripple_sh": dp("mustard"), "dust": sh("red"), "dust_sh": dp("red"), "clod": P["brown"]}   # not the salmon sky
    if planet == "mercury":                     # LEAD 04:1x: cream regolith, impact breccia, a charcoal band, sulfide, solarite hints
        return {"top": P["offwhite"], "top_sh": sh("offwhite"), "topsoil": sh("offwhite"), "speck": dp("sky"),       # LEAD 04:2x: cream-dominant
                "soil": P["offwhite"], "pale": sh("offwhite"), "breccia": dp("offwhite"), "soil_sh": sh("sky"), "soil_dp": P["brown"],
                "charcoal": P["brown"],
                "frag_a": P["offwhite"], "frag_b": sh("offwhite"), "frag_c": sh("sky"), "frag_d": dp("sky"),
                "sulfide": sh("mustard"), "sulfide_hi": P["mustard"], "solar": P["mustard"], "rock": sh("sky"), "rock_sh": dp("sky"),
                "pebble": sh("offwhite"), "reed": P["teal"], "reed_tip": P["offwhite"], "dust": P["offwhite"], "dust_sh": sh("offwhite"),
                "clod": dp("sky")}
    if planet == "venus":                       # LEAD 04:1x: a glassy black crust, folded tessera basalt, sulfur veins, vitriol glass, an ember seam
        return {"top": P["brown"], "top_sh": dp("teal"), "topsoil": dp("red"), "speck": sh("teal"),
                "soil": dp("teal"), "soil_sh": dp("red"), "soil_dp": P["brown"], "fold_a": P["brown"], "fold_b": dp("red"), "fold_c": dp("mustard"),
                "glow": P["sky"], "ember": P["red"], "ember_core": P["mustard"], "vein_line": P["mustard"], "glass": P["green"],
                "rock": P["brown"], "rock_sh": dp("teal"), "pebble": sh("teal"), "sheen_line": sh("teal"), "sulfur": P["mustard"],
                "sulfur_sh": sh("mustard"), "dust": sh("sky"), "dust_sh": dp("sky"), "clod": P["brown"]}
    raise ValueError(f"B-175: {planet}'s ground colours come after Earth's preview is accepted")


def mats(gp, planet):
    """M[role] = the flat fill (no ink), M[role + '_i'] = the fill with its ink line; 'ink' a line only; 'tuft' inked behind."""
    C = colours(planet)

    def m(name, fill=None, ink=True, behind=False, ink_hex=v3.INK):
        return G.mat(gp, f"gr_{planet}_{name}", fill=fill, ink=ink, behind=behind, ink_hex=ink_hex)
    M = {"ink": m("ink", None, True)}
    for k, h in C.items():
        if k.endswith("_line"):                 # a coloured line (a vein, a sheen streak): its own line material
            M[k] = m(k, None, True, ink_hex=h)
            continue
        M[k] = m(k, h, ink=False)
        M[k + "_i"] = m(k + "_i", h)
    M["tuft"] = m("tuft", C["top"], behind=True)
    return M


def per(x, period, harmonics, seed, amp):
    """A smooth periodic wobble (whole cycles over `period`, so the ends match)."""
    rnd = random.Random(seed)
    ph = [(rnd.randint(1, 4 + 2 * h), rnd.uniform(0, TAU), rnd.uniform(0.5, 1.0)) for h in range(harmonics)]
    tot = sum(a for _n, _p, a in ph)
    return amp * sum(a * math.sin(TAU * n * x / period + p) for n, p, a in ph) / tot


_CUR = None                         # the drawing render_piece is filling: wrapped() records each element's copies in it
_GROUPS = []


def wrapped(fn, period_x, period_z=None):
    """Draw fn(dx, dz) at the tile's neighbouring offsets so anything crossing an edge wraps (seamless tiling); the
    stroke ranges of the copies are recorded so render_piece gives them the centre copy's ids (identical ink jitter)."""
    ranges, master = [], 0
    for dx in (-period_x, 0.0, period_x):
        for dz in ((-period_z, 0.0, period_z) if period_z else (0.0,)):
            n0 = len(_CUR.strokes) if _CUR is not None else 0
            fn(dx, dz)
            ranges.append((n0, len(_CUR.strokes) if _CUR is not None else 0))
            if dx == 0.0 and dz == 0.0:
                master = len(ranges) - 1
    if _CUR is not None:
        _GROUPS.append((master, ranges))


# ---------------------------------------------------------------- the band (x 0..8 m, the surface at z = 0)

def draw_band(d, M, planet="earth"):
    L = BAND_W / PPU
    n = 257
    xs = [L * i / (n - 1) for i in range(n)]
    top = [(x, max(0.0, 0.07 * math.sin(TAU * 16 * x / L) ** 2 * (0.6 + 0.4 * math.sin(TAU * 3 * x / L + 1.0)))) for x in xs]
    turf_b = [(x, -0.15 + per(x, L, 3, 11, 0.035)) for x in xs]
    soil_b = [(x, -0.46 + per(x, L, 4, 12, 0.07) + 0.03 * math.sin(TAU * 21 * x / L)) for x in xs]

    def body(dx, _dz):
        sh = lambda pts: [(x + dx, z) for x, z in pts]  # noqa: E731
        G.stroke(d, sh(turf_b + soil_b[::-1]), M["topsoil"], 0.0, cyclic=True)               # the topsoil to its ragged edge
        G.stroke(d, sh(top + turf_b[::-1]), M["top"], 0.0, cyclic=True)                 # the turf
        G.stroke(d, sh([(x, z - 0.05) for x, z in turf_b] + turf_b[::-1]), M["top_sh"], 0.0, cyclic=True)
        G.seam(d, sh(turf_b), M["ink"])                                                      # turf meets soil
        G.stroke(d, sh(top), M["ink"], O)                                                     # THE INK EDGE on the surface row
    wrapped(body, L)
    rnd = random.Random(175)
    for i in range(22):                                                                       # blade marks in the turf
        x = L * (i + rnd.random() * 0.6) / 22
        wrapped(lambda dx, _dz, x=x: G.seam(d, [(x + dx, -0.09), (x + dx + 0.012, -0.035)], M["ink"]), L)
    for i in range(7):                                                                        # roots below the topsoil
        x = L * (i + 0.3 + rnd.random() * 0.4) / 7
        z0 = -0.40

        def root(dx, _dz, x=x, z0=z0, s=rnd.random()):
            G.seam(d, G.bezier((x + dx, z0), (x + dx + 0.06 + 0.05 * s, z0 - 0.07), (x + dx - 0.03, z0 - 0.15), n=6), M["ink"])
        wrapped(root, L)
    for i in range(9):                                                                        # pebbles in the topsoil
        x, z, r = L * (i + rnd.random()) / 9, -0.27 - rnd.random() * 0.1, 0.028 + 0.018 * rnd.random()
        wrapped(lambda dx, _dz, x=x, z=z, r=r, s=i: G.stroke(d, G.lumpy_ellipse(x + dx, z, r * 1.3, r, n=12, lump=0.08, seed=s),
                                                                M["pebble_i"], I, cyclic=True), L)
    for i in range(6):
        x = L * (i + rnd.random()) / 6
        wrapped(lambda dx, _dz, x=x, s=i: G.hatch(d, x + dx, -0.30, M["ink"], n=3, length=0.07, spacing=0.03, angle_deg=160, seed=s), L)


# ---------------------------------------------------------------- the fill (x, z 0..8 m, tiles both ways)

def draw_fill(d, M, planet="earth"):
    L = FILL / PPU
    rnd = random.Random(1751)
    wrapped(lambda dx, dz: G.stroke(d, [(dx - 0.1, dz - 0.1), (dx + L + 0.1, dz - 0.1), (dx + L + 0.1, dz + L + 0.1), (dx - 0.1, dz + L + 0.1)],
                                    M["soil"], 0.0, cyclic=True), L, L)
    xs = [L * i / 128 for i in range(129)]
    strata = [(7.3, 0.55, "soil_sh", True), (6.1, 0.30, "clay", False), (4.9, 0.75, "soil_sh", True), (3.6, 0.22, "red", True),
              (2.6, 0.55, "stone", True), (1.3, 0.35, "soil_dp", False), (0.4, 0.28, "clay", True)]
    for j, (z0, th, mat, inked) in enumerate(strata):
        upper = [(x, z0 + th / 2 + per(x, L, 3, 30 + j, 0.12)) for x in xs]
        lower = [(x, z0 - th / 2 + per(x, L, 3, 50 + j, 0.10)) for x in xs]

        def band(dx, dz, upper=upper, lower=lower, mat=mat, inked=inked):
            sh = lambda pts: [(x + dx, z + dz) for x, z in pts]  # noqa: E731
            G.stroke(d, sh(upper + lower[::-1]), M[mat], 0.0, cyclic=True)
            if inked:
                G.seam(d, sh(upper), M["ink"])
        wrapped(band, L, L)
    for i in range(26):                                                                       # pebbles
        x, z, r = rnd.uniform(0, L), rnd.uniform(0, L), rnd.uniform(0.03, 0.07)

        def peb(dx, dz, x=x, z=z, r=r, s=i):
            G.stroke(d, G.lumpy_ellipse(x + dx, z + dz, r * 1.3, r, n=14, lump=0.08, seed=s), M["pebble_i"], I, cyclic=True)
            G.seam(d, [(x + dx - r * 0.6, z + dz - r * 0.2), (x + dx + r * 0.5, z + dz - r * 0.45)], M["ink"])
        wrapped(peb, L, L)
    for i in range(4):                                                                        # stones
        x, z, r = rnd.uniform(0, L), rnd.uniform(0, L), rnd.uniform(0.14, 0.24)

        def stone(dx, dz, x=x, z=z, r=r, s=i):
            pts = G.lumpy_ellipse(x + dx, z + dz, r * 1.35, r, n=18, lump=0.10, seed=40 + s)
            G.stroke(d, pts, M["stone"], I, cyclic=True)
            G.stroke(d, G.lumpy_ellipse(x + dx - r * 0.3, z + dz - r * 0.25, r * 0.7, r * 0.45, n=12, lump=0.06, seed=60 + s),
                     M["stone_sh"], 0.0, cyclic=True)
            G.stroke(d, pts, M["ink"], O, cyclic=True)
            G.seam(d, [(x + dx - r * 0.5, z + dz + r * 0.1), (x + dx + r * 0.3, z + dz - r * 0.3)], M["ink"])
        wrapped(stone, L, L)

    def lens(dx, dz, x=5.6, z=5.4):                                                           # a water lens
        pts = G.lumpy_ellipse(x + dx, z + dz, 0.45, 0.14, n=24, lump=0.05, seed=77)
        G.stroke(d, pts, M["lens_i"], O, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x + dx + 0.12, z + dz + 0.04, 0.22, 0.05, n=14, lump=0.03, seed=78), M["petal_i"], I, cyclic=True)
    wrapped(lens, L, L)

    def fossil(dx, dz, x=2.2, z=4.4):                                                         # an ammonite
        G.stroke(d, G.lumpy_ellipse(x + dx, z + dz, 0.28, 0.26, n=28, lump=0.02, seed=81), M["bone_i"], O, cyclic=True)
        spiral = [(x + dx + 0.25 * (1 - t) ** 1.2 * math.cos(TAU * 2.2 * t), z + dz + 0.23 * (1 - t) ** 1.2 * math.sin(TAU * 2.2 * t))
                  for t in [i / 40 for i in range(40)]]
        G.seam(d, spiral, M["ink"])
        for k in range(10):
            a = TAU * k / 10
            G.seam(d, [(x + dx + 0.14 * math.cos(a), z + dz + 0.13 * math.sin(a)), (x + dx + 0.25 * math.cos(a), z + dz + 0.23 * math.sin(a))], M["ink"])
    wrapped(fossil, L, L)

    def bone(dx, dz, x=6.6, z=1.9):                                                           # a little bone
        G.stroke(d, [(x + dx - 0.22, z + dz - 0.03), (x + dx + 0.22, z + dz - 0.03), (x + dx + 0.22, z + dz + 0.03), (x + dx - 0.22, z + dz + 0.03)],
                 M["bone_i"], I, cyclic=True)
        for sx in (-0.24, 0.24):
            for sz in (-0.045, 0.045):
                G.stroke(d, G.lumpy_ellipse(x + dx + sx, z + dz + sz, 0.05, 0.045, n=10, lump=0.0), M["bone_i"], I, cyclic=True)
    wrapped(bone, L, L)
    for i in range(5):                                                                        # burrows
        x, z = rnd.uniform(0, L), rnd.uniform(0, L)
        wrapped(lambda dx, dz, x=x, z=z, s=i: G.seam(d, [(x + dx + 0.05 * math.sin(k * 1.3 + s), z + dz - 0.06 * k) for k in range(7)], M["ink"]), L, L)
    for i in range(12):
        x, z = rnd.uniform(0, L), rnd.uniform(0, L)
        wrapped(lambda dx, dz, x=x, z=z, s=i: G.hatch(d, x + dx, z + dz, M["ink"], n=3, length=0.08, spacing=0.03,
                                                      angle_deg=15 if s % 2 else 165, seed=s), L, L)
    G.specks(d, [(rnd.uniform(0.05, L - 0.05), rnd.uniform(0.05, L - 0.05)) for _ in range(40)], M["ink"])


# ---------------------------------------------------------------- upright decor (pivot at the base, z = 0)

def draw_decor(d, M, k):
    rnd = random.Random(900 + k)
    if k < 3:                                                                                 # tufts
        for b in range(4 + k):
            a = math.radians(-34 + 68 * b / (3 + k) + rnd.uniform(-6, 6))
            h = rnd.uniform(0.26, 0.42) * (1.0 if k != 2 else 1.25)
            bx = rnd.uniform(-0.05, 0.05)
            G.stroke(d, [(bx - 0.03, 0.0), (bx + h * math.sin(a), h * math.cos(a)), (bx + 0.03, 0.0)], M["tuft"], I, cyclic=True)
    elif k < 5:                                                                               # stones half sunk
        r = 0.20 if k == 3 else 0.28
        pts = [(x, max(z, -0.02)) for x, z in G.lumpy_ellipse(0.0, 0.02, r * 1.3, r, n=22, lump=0.1, seed=k)]
        G.stroke(d, pts, M["stone"], 0.0, cyclic=True)
        G.stroke(d, [(x, z) for x, z in G.lumpy_ellipse(-r * 0.35, 0.0, r * 0.8, r * 0.5, n=14, lump=0.05, seed=k + 9) if z >= -0.02] or [(0, 0)],
                 M["stone_sh"], 0.0, cyclic=True)
        G.stroke(d, pts, M["ink"], O, cyclic=True)
        G.seam(d, [(-r * 0.4, r * 0.55), (r * 0.25, r * 0.2)], M["ink"])
    else:                                                                                     # a flower
        G.seam(d, G.bezier((0.0, 0.0), (0.05, 0.22), (-0.02, 0.42), n=8), M["ink"], radius=O)
        for j in range(5):
            a = TAU * j / 5 + 0.3
            G.stroke(d, G.lumpy_ellipse(-0.02 + 0.09 * math.cos(a), 0.46 + 0.09 * math.sin(a), 0.06, 0.05, n=12, lump=0.04, seed=j,
                                        rot=a), M["petal_i"], I, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(-0.02, 0.46, 0.05, 0.05, n=12, lump=0.02, seed=7), M["flower_i"], I, cyclic=True)
        G.stroke(d, [(0.0, 0.12), (0.12, 0.2), (0.02, 0.17)], M["tuft"], I, cyclic=True)


# ---------------------------------------------------------------- the cliff lip (pivot at the brink; a drop to the right)

def draw_lip(d, M):
    """A turf hood wrapping the brink's rounded corner (the band bends there too; this drapes over it): flat on top, then
    round the corner (radius 0.37 m) and down the face, long blades drooping over the drop, two roots dangling under it."""
    R, cz = 0.37, -0.35
    outer = [(-0.60 + 0.60 * i / 12, 0.03) for i in range(12)] + \
            [((R + 0.03) * math.sin(a), cz + (R + 0.03) * math.cos(a)) for a in [math.radians(6 * j) for j in range(15)]]
    inner = [((R - 0.10) * math.sin(a), cz + (R - 0.10) * math.cos(a)) for a in [math.radians(6 * j) for j in range(14, -1, -1)]] + \
            [(-0.60 + 0.60 * i / 12, 0.03 - 0.13) for i in range(11, -1, -1)]
    hood = outer + inner
    G.stroke(d, hood, M["top"], 0.0, cyclic=True)
    G.stroke(d, [((R - 0.03) * math.sin(a), cz + (R - 0.03) * math.cos(a)) for a in [math.radians(6 * j) for j in range(15)]] +
             inner[:15], M["top_sh"], 0.0, cyclic=True)
    G.stroke(d, outer, M["ink"], O)
    G.seam(d, inner, M["ink"])
    for j in range(6):                                                                        # blades drooping over the drop
        a = math.radians(18 + 13 * j)
        bx, bz = (R + 0.02) * math.sin(a), cz + (R + 0.02) * math.cos(a)
        ln = 0.16 + 0.05 * (j % 3)
        G.stroke(d, [(bx - 0.02, bz + 0.02), (bx + 0.07 + 0.02 * (j % 2), bz - ln), (bx + 0.03, bz + 0.01)], M["tuft"], I, cyclic=True)
    for j, (a_deg, ln) in enumerate(((60, 0.42), (82, 0.30))):                                # roots dangling down the face
        a = math.radians(a_deg)
        rx, rz = (R - 0.12) * math.sin(a), cz + (R - 0.12) * math.cos(a)
        G.seam(d, G.bezier((rx, rz), (rx + 0.08, rz - ln * 0.45), (rx - 0.02, rz - ln), n=8), M["ink"])
    for j in range(5):
        x = -0.52 + 0.11 * j
        G.seam(d, [(x, -0.07), (x + 0.012, -0.025)], M["ink"])


PUFF_BILLOWS = [(84, 0.00, 1.00), (48, 0.62, 0.66), (128, 0.46, 0.80), (24, 1.00, 0.46), (156, 0.86, 0.52), (104, 0.95, 0.50),
                (66, 1.18, 0.36)]                       # asymmetric: no pair of 'ears' over the central billow (no faces, D-101)


def draw_puff(d, M, k):
    """A billowing dust cluster: a big central billow and satellites drifting out and up, swelling then thinning and
    shrinking away; dark clods flying on their arcs. Drawn far satellites first, the central billow last."""
    t = k / 7.0
    grow = math.sin(math.pi * (0.15 + 0.80 * t)) ** 0.6           # swells to t 0.43, lingers, thins
    R = 0.30 * (0.35 + 0.65 * grow) * (1.0 if t < 0.72 else 1.0 - 1.4 * (t - 0.72))
    D = 0.15 + 0.45 * (1 - (1 - t) ** 2)
    rise = 0.12 + 0.28 * t
    for j, (a_deg, df, sf) in sorted(enumerate(PUFF_BILLOWS), key=lambda e: -e[1][1]):
        a = math.radians(a_deg)
        r = R * sf
        if r < 0.03:
            continue
        x, z = D * df * math.cos(a), rise + D * df * math.sin(a) * 0.75
        pts = G.lumpy_ellipse(x, z, r, r * 0.9, n=20, lump=0.07, seed=j + 10 * k)
        G.stroke(d, pts, M["dust_i"], O, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x - r * 0.28, z - r * 0.25, r * 0.55, r * 0.42, n=12, lump=0.05, seed=j + 3), M["dust_sh"], 0.0, cyclic=True)
        if r > 0.12:                                    # a short billow fold on the upper right (not a smile: no faces)
            G.seam(d, G.bezier((x + r * 0.15, z + r * 0.62), (x + r * 0.55, z + r * 0.55), (x + r * 0.68, z + r * 0.18), n=6), M["ink"])
    for j in range(5):                                                                        # flying clods on their arcs
        a = math.radians(40 + 100 * j / 4)
        v = 1.25 + 0.25 * (j % 3)
        x = v * t * math.cos(a) * 0.7
        z = 0.1 + v * t * math.sin(a) * 0.75 - 1.5 * t * t
        if z > -0.2 and t > 0.05:
            G.stroke(d, G.lumpy_ellipse(x, z, 0.045, 0.035, n=10, lump=0.15, seed=j), M["clod_i"], I, cyclic=True)


# ---------------------------------------------------------------- the dig rim (x 0..4 m; the ink at z = 0, the solid below)

def draw_rim(d, M):
    L = RIM_W / PPU
    xs = [L * i / 96 for i in range(97)]
    line = [(x, per(x, L, 3, 91, 0.012)) for x in xs]
    low = [(x, -0.13 + per(x, L, 4, 92, 0.025)) for x in xs]

    def body(dx, _dz):
        sh = lambda pts: [(x + dx, z) for x, z in pts]  # noqa: E731
        G.stroke(d, sh(line + low[::-1]), M["soil_dp"], 0.0, cyclic=True)
        G.stroke(d, sh(line), M["ink"], O)
    wrapped(body, L)
    rnd = random.Random(93)
    for i in range(8):
        x = L * (i + rnd.random()) / 8
        wrapped(lambda dx, _dz, x=x, s=i: G.stroke(d, G.lumpy_ellipse(x + dx, -0.075, 0.025, 0.018, n=10, lump=0.1, seed=s),
                                                   M["soil_sh"], 0.0, cyclic=True), L)
    for i in range(6):                                                                        # cracks in the wall (interior detail)
        x = L * (i + 0.2 + 0.6 * rnd.random()) / 6
        wrapped(lambda dx, _dz, x=x: G.seam(d, [(x + dx, -0.02), (x + dx + 0.03, -0.06), (x + dx + 0.01, -0.10)], M["ink"]), L)


# ---------------------------------------------------------------- the crust planets (Mars; Mercury and Venus to follow):
# their own band / fill / decor / lip; the rim and the puff are the shared role-based drawings above. Earth's functions above
# stay as exported (40a7e179).

def _bump_surface(xs, L, bumps):
    """The surface height at xs: flat, with low rounded pebble scallops (wrapping over the tile's period)."""
    out = []
    for x in xs:
        z = 0.0
        for c, r in bumps:
            for off in (-L, 0.0, L):
                u = (x - c - off) / r
                if abs(u) < 1:
                    z = max(z, r * 0.7 * math.sqrt(1 - u * u))
        out.append((x, z))
    return out


def band_crust(d, M, planet, k=0):
    """A crust band (no turf): the ink edge on the surface row with low pebble scallops, a thin crust over the topsoil,
    speckle in the crust, small rocks sitting in it, cracks and pebbles below; transparent under a ragged edge."""
    L = BAND_W / PPU
    rnd = random.Random({"mars": 2751, "mercury": 2752, "venus": 2753}[planet])
    xs = [L * i / 640 for i in range(641)]
    bumps = [(L * (i + rnd.random() * 0.6) / 15, rnd.uniform(0.022, 0.055)) for i in range(15)]
    top = _bump_surface(xs, L, bumps)
    depth = {"mercury": 0.30}.get(planet, 0.09)           # Mercury: a deep cream regolith over the grey breccia (LEAD 04:1x)
    crust_b = [(x, -depth + per(x, L, 3, 21, 0.02)) for x in xs[::4]]
    soil_b = [(x, -0.44 + per(x, L, 4, 22, 0.06) + 0.025 * math.sin(TAU * 19 * x / L)) for x in xs[::4]]

    def body(dx, _dz):
        sh = lambda pts: [(x + dx, z) for x, z in pts]  # noqa: E731
        G.stroke(d, sh(crust_b + soil_b[::-1]), M["topsoil"], 0.0, cyclic=True)
        G.stroke(d, sh(top + crust_b[::-1]), M["top"], 0.0, cyclic=True)
        G.stroke(d, sh([(x, z - 0.035) for x, z in crust_b] + crust_b[::-1]), M["top_sh"], 0.0, cyclic=True)
        G.seam(d, sh(crust_b), M["ink"])
        G.stroke(d, sh(top), M["ink"], O)
    wrapped(body, L)
    for i in range(46):                                                                       # the crust's speckle
        x, z, r = L * (i + rnd.random()) / 46, -0.02 - rnd.random() * 0.055, 0.010 + 0.008 * rnd.random()
        wrapped(lambda dx, _dz, x=x, z=z, r=r, s=i: G.stroke(d, G.lumpy_ellipse(x + dx, z, r * 1.4, r, n=8, lump=0.1, seed=s),
                                                             M["speck"], 0.0, cyclic=True), L)
    for i in range(4):                                                                        # the odd small rock in the crust
        x, r = L * (i + 0.3 + 0.4 * rnd.random()) / 4, 0.06 + 0.03 * rnd.random()

        def rock(dx, _dz, x=x, r=r, s=i):
            pts = [(px, max(pz, -0.06)) for px, pz in G.lumpy_ellipse(x + dx, 0.005, r * 1.35, r * 0.75, n=18, lump=0.1, seed=30 + s)]
            G.stroke(d, pts, M["rock"], 0.0, cyclic=True)
            G.stroke(d, G.lumpy_ellipse(x + dx - r * 0.35, -0.01, r * 0.6, r * 0.3, n=10, lump=0.05, seed=40 + s), M["rock_sh"], 0.0, cyclic=True)
            G.stroke(d, pts, M["ink"], I, cyclic=True)
        wrapped(rock, L)
    for i in range(9):                                                                        # cracks in the topsoil
        x = L * (i + 0.2 + 0.6 * rnd.random()) / 9
        wrapped(lambda dx, _dz, x=x: G.seam(d, [(x + dx, -0.12), (x + dx + 0.03, -0.20), (x + dx - 0.01, -0.27), (x + dx + 0.02, -0.33)],
                                            M["ink"]), L)
    for i in range(8):                                                                        # pebbles in the topsoil
        x, z, r = L * (i + rnd.random()) / 8, -0.22 - rnd.random() * 0.12, 0.024 + 0.016 * rnd.random()
        wrapped(lambda dx, _dz, x=x, z=z, r=r, s=i: G.stroke(d, G.lumpy_ellipse(x + dx, z, r * 1.3, r, n=12, lump=0.08, seed=60 + s),
                                                                M["pebble_i"], I, cyclic=True), L)
    for i in range(5):
        x = L * (i + rnd.random()) / 5
        wrapped(lambda dx, _dz, x=x, s=i: G.hatch(d, x + dx, -0.30, M["ink"], n=3, length=0.07, spacing=0.03, angle_deg=160, seed=s), L)


def _strata(d, M, L, strata, amp, seed):
    xs = [L * i / 128 for i in range(129)]
    for j, (z0, th, mat, inked) in enumerate(strata):
        upper = [(x, z0 + th / 2 + per(x, L, 3, seed + j, amp)) for x in xs]
        lower = [(x, z0 - th / 2 + per(x, L, 3, seed + 40 + j, amp * 0.85)) for x in xs]

        def band(dx, dz, upper=upper, lower=lower, mat=mat, inked=inked):
            sh = lambda pts: [(x + dx, z + dz) for x, z in pts]  # noqa: E731
            G.stroke(d, sh(upper + lower[::-1]), M[mat], 0.0, cyclic=True)
            if inked:
                G.seam(d, sh(upper), M["ink"])
        wrapped(band, L, L)


def _lens(d, M, L, x, z, rx, rz, seed):
    def lens(dx, dz):
        pts = G.lumpy_ellipse(x + dx, z + dz, rx, rz, n=24, lump=0.05, seed=seed)
        G.stroke(d, pts, M["ice_i"], O, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x + dx - rx * 0.25, z + dz - rz * 0.3, rx * 0.55, rz * 0.35, n=14, lump=0.04, seed=seed + 1),
                 M["ice_sh"], 0.0, cyclic=True)
        G.seam(d, [(x + dx + rx * 0.1, z + dz + rz * 0.45), (x + dx + rx * 0.55, z + dz + rz * 0.3)], M["ink"])
    wrapped(lens, L, L)


def _scatter(d, M, L, n, zr, rr, role, seed, glint=None):
    rnd = random.Random(seed)
    for i in range(n):
        x, z, r = rnd.uniform(0, L), rnd.uniform(*zr), rnd.uniform(*rr)

        def one(dx, dz, x=x, z=z, r=r, s=i):
            G.stroke(d, G.lumpy_ellipse(x + dx, z + dz, r * 1.1, r, n=12, lump=0.05, seed=s + seed), M[role], I, cyclic=True)
            if glint:
                G.stroke(d, G.lumpy_ellipse(x + dx + r * 0.3, z + dz + r * 0.3, r * 0.3, r * 0.3, n=8, lump=0.0), M[glint], 0.0, cyclic=True)
        wrapped(one, L, L)


def fill_mars(d, M, k=0):
    """Gale-crater layering: thin ochre / red-brown / salmon sandstone bands with cross-bedding, one band full of dark
    hematite spherules, a grey basalt layer with joints and vesicles deeper, white water-ice lenses at depth."""
    L = FILL / PPU
    rnd = random.Random(2761)
    wrapped(lambda dx, dz: G.stroke(d, [(dx - 0.1, dz - 0.1), (dx + L + 0.1, dz - 0.1), (dx + L + 0.1, dz + L + 0.1), (dx - 0.1, dz + L + 0.1)],
                                    M["soil"], 0.0, cyclic=True), L, L)
    _strata(d, M, L, [(7.62, 0.34, "ochre", True), (7.18, 0.22, "redbrown", False), (6.74, 0.42, "salmon", True), (6.26, 0.24, "ochre", False),
                      (5.80, 0.40, "redbrown", True), (5.20, 0.56, "ochre", True), (4.62, 0.30, "salmon", False), (4.12, 0.40, "redbrown", True),
                      (3.52, 0.50, "ochre", True), (2.98, 0.24, "salmon", False), (1.75, 1.10, "basalt", True), (0.45, 0.30, "redbrown", True)],
            0.05, 70)
    for i in range(14):                                                                       # cross-bedding in the sandstone
        x, z = rnd.uniform(0, L), rnd.choice((7.62, 6.74, 5.80, 4.12, 3.52)) + rnd.uniform(-0.08, 0.08)
        wrapped(lambda dx, dz, x=x, z=z: [G.seam(d, [(x + dx + 0.07 * j, z + dz + 0.10), (x + dx + 0.07 * j + 0.16, z + dz - 0.10)], M["ink"])
                                          for j in range(3)], L, L)
    _scatter(d, M, L, 40, (5.02, 5.40), (0.026, 0.042), "hem_i", 2771, glint="hem_hi")   # the 'blueberries'
    for i in range(7):                                                                        # basalt joints and vesicles
        x = L * (i + rnd.random() * 0.5) / 7
        wrapped(lambda dx, dz, x=x: G.seam(d, [(x + dx, 1.26 + dz), (x + dx + 0.03, 1.75 + dz), (x + dx - 0.01, 2.22 + dz)], M["ink"]), L, L)
    _scatter(d, M, L, 22, (1.3, 2.2), (0.012, 0.022), "basalt_sh", 2781)
    _lens(d, M, L, 2.4, 0.95, 0.55, 0.15, 2791)
    _lens(d, M, L, 6.1, 2.45, 0.38, 0.11, 2793)
    _scatter(d, M, L, 16, (0.0, L), (0.03, 0.06), "pebble_i", 2795)
    for i in range(3):                                                                        # stones
        x, z, r = rnd.uniform(0, L), rnd.uniform(3.0, 7.8), rnd.uniform(0.12, 0.2)

        def stone(dx, dz, x=x, z=z, r=r, s=i):
            pts = G.lumpy_ellipse(x + dx, z + dz, r * 1.35, r, n=18, lump=0.1, seed=80 + s)
            G.stroke(d, pts, M["rock"], 0.0, cyclic=True)
            G.stroke(d, G.lumpy_ellipse(x + dx - r * 0.3, z + dz - r * 0.25, r * 0.7, r * 0.45, n=12, lump=0.06, seed=90 + s), M["rock_sh"], 0.0, cyclic=True)
            G.stroke(d, pts, M["ink"], O, cyclic=True)
        wrapped(stone, L, L)
    for i in range(10):
        x, z = rnd.uniform(0, L), rnd.uniform(0, L)
        wrapped(lambda dx, dz, x=x, z=z, s=i: G.hatch(d, x + dx, z + dz, M["ink"], n=3, length=0.08, spacing=0.03,
                                                      angle_deg=15 if s % 2 else 165, seed=s), L, L)
    G.specks(d, [(rnd.uniform(0.05, L - 0.05), rnd.uniform(0.05, L - 0.05)) for _ in range(40)], M["ink"])


DECOR_NAMES = {"earth": ["tuft_a", "tuft_b", "tuft_c", "stone_a", "stone_b", "flower"],
               "mars": ["rock_a", "ventifact", "dust_ripple", "frost_patch", "pebbles", "rock_b"]}


def _rock(d, M, x, r, seed, flat=0.75, speck=False):
    pts = [(px, max(pz, -0.02)) for px, pz in G.lumpy_ellipse(x, 0.02, r * 1.3, r * flat, n=22, lump=0.1, seed=seed)]
    G.stroke(d, pts, M["rock"], 0.0, cyclic=True)
    G.stroke(d, [(px, pz) for px, pz in G.lumpy_ellipse(x - r * 0.35, 0.0, r * 0.8, r * 0.5 * flat, n=14, lump=0.05, seed=seed + 9) if pz >= -0.02]
             or [(0, 0)], M["rock_sh"], 0.0, cyclic=True)
    G.stroke(d, pts, M["ink"], O, cyclic=True)
    G.seam(d, [(x - r * 0.4, r * 0.5 * flat), (x + r * 0.25, r * 0.2 * flat)], M["ink"])
    if speck:
        G.specks(d, [(x + r * 0.3, r * 0.45 * flat), (x - r * 0.1, r * 0.6 * flat)], M["ink"])


def decor_mars(d, M, k=0):
    if k == 0:
        _rock(d, M, 0.0, 0.20, 301)
    elif k == 1:                                                                              # a ventifact: faceted, wind-grooved
        pts = [(-0.30, -0.02), (-0.24, 0.16), (-0.05, 0.30), (0.20, 0.24), (0.31, 0.06), (0.28, -0.02)]
        G.stroke(d, pts, M["rock"], 0.0, cyclic=True)
        G.stroke(d, [(-0.30, -0.02), (-0.24, 0.16), (-0.05, 0.30), (-0.02, 0.12), (0.0, -0.02)], M["rock_sh"], 0.0, cyclic=True)
        G.stroke(d, pts, M["ink"], O, cyclic=True)
        G.seam(d, [(-0.05, 0.30), (-0.02, 0.12), (0.0, -0.02)], M["ink"])
        for j in range(3):
            G.seam(d, [(0.04 + 0.07 * j, 0.22 - 0.03 * j), (0.12 + 0.07 * j, 0.05)], M["ink"])
    elif k == 2:                                                                              # a wind ripple of dust
        xs = [-0.42 + 0.84 * i / 30 for i in range(31)]
        top = [(x, 0.10 * math.exp(-((x + 0.05) / 0.22) ** 2) + 0.05 * math.exp(-((x - 0.25) / 0.12) ** 2)) for x in xs]
        G.stroke(d, top + [(0.42, -0.01), (-0.42, -0.01)], M["ripple"], 0.0, cyclic=True)
        G.stroke(d, [(x, z * 0.45) for x, z in top] + [(0.42, -0.01), (-0.42, -0.01)], M["ripple_sh"], 0.0, cyclic=True)
        G.stroke(d, top, M["ink"], O)
        for j in range(3):
            G.seam(d, [(-0.25 + 0.15 * j, 0.03), (-0.17 + 0.15 * j, 0.065), (-0.10 + 0.15 * j, 0.03)], M["ink"])
    elif k == 3:                                                                              # a frost patch, lying low
        pts = [(x, 0.035 * math.sin(math.pi * (x + 0.38) / 0.76) + 0.008 * math.sin(23 * x)) for x in [-0.38 + 0.76 * i / 24 for i in range(25)]]
        G.stroke(d, pts + [(0.38, -0.01), (-0.38, -0.01)], M["frost"], 0.0, cyclic=True)
        G.stroke(d, [(x, z * 0.4) for x, z in pts] + [(0.38, -0.01), (-0.38, -0.01)], M["frost_sh"], 0.0, cyclic=True)
        G.stroke(d, pts, M["ink"], O)
        for x in (-0.2, 0.05, 0.22):                                                           # a glint
            G.seam(d, [(x - 0.03, 0.07), (x + 0.03, 0.07)], M["ink"])
            G.seam(d, [(x, 0.04), (x, 0.10)], M["ink"])
    elif k == 4:
        for j, (x, r) in enumerate(((-0.22, 0.08), (0.02, 0.11), (0.24, 0.07))):
            _rock(d, M, x, r, 320 + j)
    else:
        _rock(d, M, 0.0, 0.26, 331, flat=0.85, speck=True)


def lip_crust(d, M, k=0):
    """The crust's hood over a rounded brink: the crust and its speckle round the corner, grit trickling over the drop."""
    R, cz = 0.37, -0.35
    outer = [(-0.60 + 0.60 * i / 12, 0.02) for i in range(12)] + \
            [((R + 0.02) * math.sin(a), cz + (R + 0.02) * math.cos(a)) for a in [math.radians(6 * j) for j in range(15)]]
    inner = [((R - 0.08) * math.sin(a), cz + (R - 0.08) * math.cos(a)) for a in [math.radians(6 * j) for j in range(14, -1, -1)]] + \
            [(-0.60 + 0.60 * i / 12, 0.02 - 0.10) for i in range(11, -1, -1)]
    G.stroke(d, outer + inner, M["top"], 0.0, cyclic=True)
    G.stroke(d, [((R - 0.04) * math.sin(a), cz + (R - 0.04) * math.cos(a)) for a in [math.radians(6 * j) for j in range(15)]] + inner[:15],
             M["top_sh"], 0.0, cyclic=True)
    G.stroke(d, outer, M["ink"], O)
    G.seam(d, inner, M["ink"])
    rnd = random.Random(341)
    for j in range(10):
        a = math.radians(rnd.uniform(5, 80))
        rr = R - 0.05 + rnd.uniform(-0.02, 0.02)
        G.stroke(d, G.lumpy_ellipse(rr * math.sin(a), cz + rr * math.cos(a), 0.012, 0.009, n=8, lump=0.1, seed=j), M["speck"], 0.0, cyclic=True)
    for j, (x, z, r) in enumerate(((0.47, -0.42, 0.030), (0.52, -0.58, 0.022), (0.46, -0.71, 0.018), (0.55, -0.30, 0.020))):
        G.stroke(d, G.lumpy_ellipse(x, z, r * 1.2, r, n=10, lump=0.1, seed=350 + j), M["pebble_i"], I, cyclic=True)
    G.seam(d, [(0.40, -0.36), (0.44, -0.47)], M["ink"])


PLANET_DRAW = {"mars": {"ground_band": lambda d, M, k: band_crust(d, M, "mars", k), "ground_fill": fill_mars,
                        "ground_decor": decor_mars, "ground_lip": lip_crust}}


def _shard(x, z, r, rnd, sides=5, flat=1.0):
    """An angular fragment: a polygon with irregular corners."""
    a0 = rnd.uniform(0, TAU)
    return [(x + r * rnd.uniform(0.65, 1.0) * math.cos(a0 + TAU * i / sides), z + r * flat * rnd.uniform(0.65, 1.0) * math.sin(a0 + TAU * i / sides))
            for i in range(sides)]


def _bg(d, M, L, role="soil"):
    wrapped(lambda dx, dz: G.stroke(d, [(dx - 0.1, dz - 0.1), (dx + L + 0.1, dz - 0.1), (dx + L + 0.1, dz + L + 0.1), (dx - 0.1, dz + L + 0.1)],
                                    M[role], 0.0, cyclic=True), L, L)


def _glint(d, M, x, z, s, role):
    """A tiny four-point star glint (a hint, never a find)."""
    G.stroke(d, [(x - s, z), (x - s * 0.25, z + s * 0.25), (x, z + s), (x + s * 0.25, z + s * 0.25), (x + s, z), (x + s * 0.25, z - s * 0.25),
                 (x, z - s), (x - s * 0.25, z - s * 0.25)], M[role], I, cyclic=True)


def fill_mercury(d, M, k=0):
    """Cream regolith (LEAD 04:2x: >= 60 % of the tile cream, the old strip's body): the cream body with pale-stone bands, the
    impact breccia as two grey bands packed with angular fragments, one dark charcoal (carbon-rich) band, small brassy
    sulfide nodules, a few tiny gold solarite glints as hints only (B-176 places the real pockets)."""
    L = FILL / PPU
    rnd = random.Random(2861)
    _bg(d, M, L)
    _strata(d, M, L, [(7.1, 0.40, "pale", True), (5.30, 1.05, "breccia", True), (4.05, 0.34, "charcoal", True), (2.95, 0.34, "pale", False),
                      (1.40, 0.85, "breccia", True)], 0.08, 170)
    tones = ("frag_a", "frag_b", "frag_c", "frag_d")
    for i in range(60):                                                                       # the angular fragments, most in the breccia
        zr = ((4.85, 5.75), (1.05, 1.75), (0.0, L))[0 if i % 5 < 2 else (1 if i % 5 < 4 else 2)]
        x, z, r = rnd.uniform(0, L), rnd.uniform(*zr), rnd.uniform(0.05, 0.20) if i % 5 < 4 else rnd.uniform(0.04, 0.09)
        pts = _shard(0.0, 0.0, r, rnd, sides=rnd.choice((4, 5, 6)), flat=rnd.uniform(0.6, 1.0))
        tone = tones[i % 4]

        def frag(dx, dz, x=x, z=z, pts=pts, tone=tone, r=r):
            sh_ = [(x + dx + px, z + dz + pz) for px, pz in pts]
            G.stroke(d, sh_, M[tone], 0.0, cyclic=True)
            G.stroke(d, sh_, M["ink"], I if r < 0.13 else O, cyclic=True)
        wrapped(frag, L, L)
    _scatter(d, M, L, 18, (0.0, L), (0.025, 0.045), "sulfide_i", 2871, glint="sulfide_hi")
    for i in range(5):                                                                        # solarite glints (hints)
        x, z = rnd.uniform(0, L), rnd.uniform(0, L)
        wrapped(lambda dx, dz, x=x, z=z: _glint(d, M, x + dx, z + dz, 0.05, "solar_i"), L, L)
    for i in range(10):
        x, z = rnd.uniform(0, L), rnd.uniform(0, L)
        wrapped(lambda dx, dz, x=x, z=z, s=i: G.hatch(d, x + dx, z + dz, M["ink"], n=3, length=0.08, spacing=0.03,
                                                      angle_deg=15 if s % 2 else 165, seed=s), L, L)
    G.specks(d, [(rnd.uniform(0.05, L - 0.05), rnd.uniform(0.05, L - 0.05)) for _ in range(40)], M["ink"])


def fill_venus(d, M, k=0):
    """Tessera: dark basalt bands strongly folded together, sulfur-yellow veins cutting them, green vitriol-glass shards,
    one deep ember-orange seam glowing in its halo."""
    L = FILL / PPU
    rnd = random.Random(2961)
    _bg(d, M, L)
    xs = [L * i / 160 for i in range(161)]

    def fold(x):
        return 0.75 * math.sin(TAU * x / L + 0.4) + 0.25 * math.sin(TAU * 3 * x / L + 1.1)
    bands = [(7.4, 0.50, "fold_a"), (6.55, 0.40, "fold_b"), (5.75, 0.55, "fold_c"), (3.65, 0.45, "fold_a"), (2.85, 0.50, "fold_b"),
             (2.05, 0.35, "fold_c"), (0.75, 0.55, "fold_a")]
    for j, (z0, th, mat) in enumerate(bands):
        upper = [(x, z0 + th / 2 + fold(x) + per(x, L, 2, 190 + j, 0.04)) for x in xs]
        lower = [(x, z0 - th / 2 + fold(x) + per(x, L, 2, 230 + j, 0.04)) for x in xs]

        def band(dx, dz, upper=upper, lower=lower, mat=mat):
            sh_ = lambda pts: [(x + dx, z + dz) for x, z in pts]  # noqa: E731
            G.stroke(d, sh_(upper + lower[::-1]), M[mat], 0.0, cyclic=True)
            G.seam(d, sh_(upper), M["ink"])
        wrapped(band, L, L)
    zc = 4.7                                                                                  # the ember seam and its glow
    up = [(x, zc + 0.24 + fold(x)) for x in xs]
    lo = [(x, zc - 0.24 + fold(x)) for x in xs]
    cu = [(x, zc + 0.11 + fold(x) + 0.02 * math.sin(TAU * 7 * x / L)) for x in xs]
    cl = [(x, zc - 0.11 + fold(x) + 0.02 * math.sin(TAU * 9 * x / L + 1)) for x in xs]
    hu = [(x, zc + 0.36 + fold(x)) for x in xs]
    hl = [(x, zc - 0.36 + fold(x)) for x in xs]

    def ember(dx, dz):
        sh_ = lambda pts: [(x + dx, z + dz) for x, z in pts]  # noqa: E731
        G.stroke(d, sh_(hu + hl[::-1]), M["glow"], 0.0, cyclic=True)
        G.stroke(d, sh_(up + lo[::-1]), M["ember"], 0.0, cyclic=True)
        G.stroke(d, sh_(cu + cl[::-1]), M["ember_core"], 0.0, cyclic=True)
        G.seam(d, sh_(up), M["ink"])
        G.seam(d, sh_(lo), M["ink"])
    wrapped(ember, L, L)
    for i in range(6):                                                                        # sulfur veins (coloured lines)
        x0, z0 = rnd.uniform(0, L), rnd.uniform(0, L)
        pts = [(x0 + 0.12 * t + 0.05 * math.sin(t * 1.7 + i), z0 + 0.09 * t * (1 if i % 2 else -1) + 0.04 * math.sin(t * 2.3)) for t in range(10)]
        wrapped(lambda dx, dz, pts=pts: G.stroke(d, [(x + dx, z + dz) for x, z in pts], M["vein_line"], I), L, L)
    for i in range(12):                                                                       # vitriol-glass shards
        x, z, r = rnd.uniform(0, L), rnd.uniform(0, L), rnd.uniform(0.06, 0.14)
        pts = _shard(0.0, 0.0, r, rnd, sides=rnd.choice((3, 4)), flat=rnd.uniform(0.5, 1.0))

        def shard(dx, dz, x=x, z=z, pts=pts, r=r):
            sh_ = [(x + dx + px, z + dz + pz) for px, pz in pts]
            G.stroke(d, sh_, M["glass_i"], I, cyclic=True)
            G.seam(d, [(x + dx - r * 0.3, z + dz + r * 0.1), (x + dx + r * 0.2, z + dz + r * 0.35)], M["ink"])
        wrapped(shard, L, L)
    _scatter(d, M, L, 20, (0.0, L), (0.012, 0.022), "fold_c", 2971)
    for i in range(8):
        x, z = rnd.uniform(0, L), rnd.uniform(0, L)
        wrapped(lambda dx, dz, x=x, z=z, s=i: G.hatch(d, x + dx, z + dz, M["ink"], n=3, length=0.08, spacing=0.03,
                                                      angle_deg=15 if s % 2 else 165, seed=s), L, L)
    G.specks(d, [(rnd.uniform(0.05, L - 0.05), rnd.uniform(0.05, L - 0.05)) for _ in range(30)], M["ink"])


def _angular_rock(d, M, x, r, seed, sides=6):
    rnd = random.Random(seed)
    pts = [(px, max(pz, -0.02)) for px, pz in _shard(x, r * 0.55, r, rnd, sides=sides, flat=0.75)]
    G.stroke(d, pts, M["rock"], 0.0, cyclic=True)
    lo = [p for p in pts if p[0] <= x + r * 0.1]
    if len(lo) >= 3:
        G.stroke(d, lo, M["rock_sh"], 0.0, cyclic=True)
    G.stroke(d, pts, M["ink"], O, cyclic=True)
    G.seam(d, [(x - r * 0.1, r * 0.95), (x + r * 0.05, r * 0.35)], M["ink"])


def _reeds(d, M, n, seed, tall=0.42):
    rnd = random.Random(seed)
    for j in range(n):
        bx = -0.12 + 0.24 * j / max(1, n - 1) + rnd.uniform(-0.02, 0.02)
        h = tall * rnd.uniform(0.75, 1.0)
        lean = rnd.uniform(-0.06, 0.06)
        G.stroke(d, [(bx - 0.018, 0.0), (bx + lean - 0.010, h), (bx + lean + 0.010, h), (bx + 0.018, 0.0)], M["reed_i"], I, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(bx + lean, h + 0.02, 0.03, 0.04, n=10, lump=0.05, seed=j), M["reed_tip_i"], I, cyclic=True)


def decor_mercury(d, M, k=0):
    if k in (0, 1, 4):
        _angular_rock(d, M, 0.0, (0.20, 0.28, 0.15)[(0, 1, 4).index(k)], 400 + k, sides=(6, 7, 5)[(0, 1, 4).index(k)])
    elif k in (2, 5):
        _reeds(d, M, 4 if k == 2 else 3, 410 + k, 0.42 if k == 2 else 0.34)
    else:                                                                                     # crater-rim pebbles
        for j, (x, r) in enumerate(((-0.24, 0.07), (-0.05, 0.10), (0.16, 0.08), (0.30, 0.05))):
            _angular_rock(d, M, x, r, 420 + j, sides=5)


def decor_venus(d, M, k=0):
    if k in (0, 1, 4):
        _angular_rock(d, M, 0.0, (0.22, 0.30, 0.16)[(0, 1, 4).index(k)], 500 + k, sides=(6, 7, 5)[(0, 1, 4).index(k)])
        G.seam(d, [(-0.05, 0.12), (0.05, 0.18)], M["sheen_line"])
    elif k == 2:                                                                              # a sulfur crust, lying low
        pts = [(x, 0.05 * math.sin(math.pi * (x + 0.36) / 0.72) + 0.012 * math.sin(29 * x)) for x in [-0.36 + 0.72 * i / 24 for i in range(25)]]
        G.stroke(d, pts + [(0.36, -0.01), (-0.36, -0.01)], M["sulfur"], 0.0, cyclic=True)
        G.stroke(d, [(x, z * 0.45) for x, z in pts] + [(0.36, -0.01), (-0.36, -0.01)], M["sulfur_sh"], 0.0, cyclic=True)
        G.stroke(d, pts, M["ink"], O)
        G.specks(d, [(-0.2, 0.03), (0.0, 0.04), (0.18, 0.03)], M["ink"])
    else:                                                                                     # glass shards standing
        rnd = random.Random(530 + k)
        for j in range(3 if k == 3 else 2):
            bx = -0.12 + 0.12 * j
            h = rnd.uniform(0.18, 0.32)
            pts = [(bx - 0.05, 0.0), (bx + rnd.uniform(-0.03, 0.03), h), (bx + 0.06, 0.0)]
            G.stroke(d, pts, M["glass_i"], I, cyclic=True)
            G.seam(d, [(bx - 0.01, 0.03), (bx + 0.0, h * 0.7)], M["ink"])


DECOR_NAMES.update({"mercury": ["angular_a", "angular_b", "glassreed", "rim_pebbles", "angular_c", "glassreed_b"],
                    "venus": ["basalt_a", "basalt_b", "sulfur_crust", "glass_shards", "basalt_c", "glass_pair"]})
PLANET_DRAW.update({
    "mercury": {"ground_band": lambda d, M, k: band_crust(d, M, "mercury", k), "ground_fill": fill_mercury,
                "ground_decor": decor_mercury, "ground_lip": lip_crust},
    "venus": {"ground_band": lambda d, M, k: band_crust(d, M, "venus", k), "ground_fill": fill_venus,
              "ground_decor": decor_venus, "ground_lip": lip_crust},
})


# ---------------------------------------------------------------- render the pieces

PIECES = {   # name -> (w, h, pivot, frames)
    "ground_band": (BAND_W, BAND_H, (0.0, (BAND_H - SURF_ROW) / BAND_H), 1),
    "ground_fill": (FILL, FILL, (0.0, 0.0), 1),
    "ground_decor": (64, 64, (0.5, 6 / 64), 6),
    "ground_lip": (128, 96, (0.55, 0.6), 1),
    "dig_rim": (RIM_W, RIM_H, (0.0, (RIM_H - RIM_ROW) / RIM_H), 1),
    "dig_puff": (128, 128, (0.5, 0.25), 8),
}


def render_piece(name, planet="earth", k=0, mx=1, mz=1, ss=None):
    """mx / mz: render the drawing mx x mz frames wide / tall (the periodicity check compares the copies)."""
    global _CUR
    w, h, piv, _n = PIECES[name]
    w, h = w * mx, h * mz
    gp = fakegp.FakeGP()
    M = mats(gp, planet)
    d = fakegp.FakeDrawing()
    _CUR = d
    _GROUPS.clear()
    own = PLANET_DRAW.get(planet, {}).get(name)
    if own:
        own(d, M, k)
    else:
        {"ground_band": lambda: draw_band(d, M, planet), "ground_fill": lambda: draw_fill(d, M, planet),
         "ground_decor": lambda: draw_decor(d, M, k), "ground_lip": lambda: draw_lip(d, M), "dig_rim": lambda: draw_rim(d, M),
         "dig_puff": lambda: draw_puff(d, M, k)}[name]()
    _CUR = None
    st = fakegp.strokes_of(d, gp)
    for master, ranges in _GROUPS:                      # a wrapped element's copies share the master's id: the same ink
        m0, m1 = ranges[master]                         # jitter along the same arc, so the tile's copies are identical
        for a, b in ranges:
            if (a, b) != (m0, m1) and b - a == m1 - m0:
                for i in range(m1 - m0):
                    st[a + i]["id"] = st[m0 + i]["id"]
    ss = ss or (2 if w * h > 200_000 else 4)              # the 512^2 fill at ss 4 holds a 2048^2 float buffer (> the 300 MB cap)
    img, wd = GR.render_frame(st, w, h, PPU, piv, ss=ss, seed=1750 + k)
    return img, wd


def render_all(planet="earth"):
    out = {}
    for name, (_w, _h, _p, n) in PIECES.items():
        frames, widths = [], []
        for k in range(n):
            img, wd = render_piece(name, planet, k)
            frames.append(img)
            widths += wd
        out[name] = (frames, widths)
    return out


# ---------------------------------------------------------------- the export (render.py's ground_strip_set API: KEYS, sheets,
# export, main; the row's "planet" picks the planet through use_planet)

DECOR = ["tuft_a", "tuft_b", "tuft_c", "stone_a", "stone_b", "flower"]
PLANET = "earth"
KEYS = {}


def use_planet(planet):
    global PLANET, KEYS, DECOR
    PLANET = planet
    DECOR = DECOR_NAMES.get(planet, DECOR_NAMES["earth"])
    KEYS = {n: f"terrain/{planet}/{n}" for n in ("ground_band", "ground_fill", "ground_lip", "dig_rim", "dig_puff")}
    KEYS.update({f"ground_decor_{i + 1}": f"terrain/{planet}/ground_decor_{i + 1}" for i in range(len(DECOR))})


use_planet(PLANET)


def sheets():
    """-> ({key name: (frames, widths)}, all widths): one entry per contract §11.9 key (the decor one key per piece)."""
    S, allw = {}, []
    for name, (_w, _h, _p, n) in PIECES.items():
        for k in range(n):
            img, wd = render_piece(name, PLANET, k)
            kn = f"ground_decor_{k + 1}" if name == "ground_decor" else name
            fr, ws = S.get(kn, ([], []))
            S[kn] = (fr + [img], ws + wd)
            allw += wd
    return S, allw


def pieces_of(S):
    """The preview's per-piece view of S (the decor as one 6-frame piece)."""
    out = {n: S[n] for n in ("ground_band", "ground_fill", "ground_lip", "dig_rim", "dig_puff")}
    out["ground_decor"] = ([S[f"ground_decor_{i + 1}"][0][0] for i in range(len(DECOR))],
                           sum((S[f"ground_decor_{i + 1}"][1] for i in range(len(DECOR))), []))
    return out


def copy_diff(name):
    """Contract §11.9: the drawing rendered two tiles wide (two tall for the fill); p99 of the copies' difference (must be 0)."""
    import numpy as np
    w0, h0 = PIECES[name][0], PIECES[name][1]
    two, _w = render_piece(name, PLANET, 0, mx=2, mz=2 if name == "ground_fill" else 1, ss=1)
    p = float(np.percentile(np.abs(two[:h0, :w0].astype(np.int32) - two[:h0, w0:2 * w0].astype(np.int32)), 99))
    if name == "ground_fill":
        p = max(p, float(np.percentile(np.abs(two[:h0, :w0].astype(np.int32) - two[h0:2 * h0, :w0].astype(np.int32)), 99)))
    return p


def sheet_meta(kn, frames):
    import numpy as np
    base = "ground_decor" if kn.startswith("ground_decor_") else kn
    w, h, piv, _n = PIECES[base]
    g = v3.GUTTER
    n = len(frames)
    sheet = np.zeros((h, n * w + (n - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        sheet[:, i * (w + g):i * (w + g) + w] = im
    meta = {"key": KEYS[kn], "style": "v3", "contract": "v3.2 11.9", "frame_width": w, "frame_height": h, "columns": n, "gutter": g,
            "frames": n, "fps": v3.FPS, "pivot": [round(piv[0], 6), round(piv[1], 6)], "facing": "right", "ppu": PPU, "animations": []}
    if kn == "ground_band":
        meta.update({"tile_x": True, "repeat_px": BAND_W, "surface_row": SURF_ROW, "above_px": SURF_ROW, "below_px": BAND_H - SURF_ROW,
                     "mapping": "u = world x x 64 mod 512 (continues across chunk seams; UNITY via LEAD 11-08 04:1x); v = 24 - (normal distance from the outline x 64), up = toward row 0; the sprite pivot is ON row 24 (40 px up from the bottom)",
                     "note": "low scallops only: the art stretches <= 22 % along the band on a 35 deg slope"})
    elif kn == "ground_fill":
        meta.update({"tile_x": True, "tile_y": True, "world_space": True, "standalone": True, "wrap": "repeat",
                     "mapping": "u = x x 64 mod 512, v = -y x 64 mod 512; a standalone texture (outside the atlases, Repeat wrap)"})
    elif kn == "dig_rim":
        meta.update({"tile_x": True, "repeat_px": RIM_W, "ink_row": RIM_ROW,
                     "mapping": "along each carved hole's outline; the rows below the ink lie in the solid (the normal points into the air); the sprite pivot is ON the ink row 4"})
    elif kn == "ground_lip":
        meta.update({"brink": True, "note": "drawn for a drop to the right; mirror x for a drop to the left"})
    elif kn == "dig_puff":
        meta["animations"] = [{"name": "puff", "start": 0, "length": n, "loop": False}]
    else:
        meta.update({"upright": True, "decor": DECOR[int(kn.rsplit("_", 1)[1]) - 1], "note": "scatter along the curve, never rotated"})
    problems = [p for p in v3.validate_sheet(meta, sheet.shape) if "sum of clip lengths" not in p]
    if kn not in ("ground_band", "ground_fill", "dig_rim"):
        m = v3.EDGE_MARGIN
        for i, im in enumerate(frames):
            if im[:m, :, 3].any() or im[-m:, :, 3].any() or im[:, :m, 3].any() or im[:, -m:, 3].any():
                problems.append(f"frame {i} touches the {m} px edge")
    hit, off = v3.palette_hits(sheet, PLANET)
    if hit < 0.98:
        problems.append(f"palette {hit * 100:.1f}% (off {' '.join(off[:3])})")
    return sheet, meta, problems


def export(art, S=None):
    """-> (out [(key, w, h, bytes)], within {name: p99 copy diff}, across): raises on any contract problem."""
    import json as _json
    from meridian import pngio
    if S is None:
        S, _w = sheets()
    built, problems, within = [], [], {}
    for kn, (frames, _ws) in S.items():
        sheet, meta, p = sheet_meta(kn, frames)
        problems += [f"{kn}: {x}" for x in p]
        built.append((kn, sheet, meta))
    for kn in ("ground_band", "ground_fill", "dig_rim"):
        within[kn] = copy_diff(kn)
        if within[kn] != 0:
            problems.append(f"{kn}: tiling copies differ (p99 {within[kn]:.0f}; contract 11.9: 0)")
    if problems:
        raise ValueError(f"{PLANET} ground set checks: " + "; ".join(problems))
    d = os.path.join(art, "terrain", PLANET)
    os.makedirs(d, exist_ok=True)
    out = []
    for kn, sheet, meta in built:
        n = pngio.write_png(os.path.join(d, kn + "_color.png"), sheet)
        with open(os.path.join(d, kn + ".json"), "w", encoding="utf-8", newline="\n") as f:
            _json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((meta["key"], sheet.shape[1], sheet.shape[0], n))
    return out, within, f"{len(out)} keys, contract v3.2 11.9"


def main(out, S=None, allw=None, footnote=None):
    """The stamped export review: the curve preview's three panels and pieces, from the exported frames."""
    if S is None:
        S, allw = sheets()
    preview(os.path.dirname(out), PLANET, pieces=pieces_of(S), out=out, footnote=footnote)


# ---------------------------------------------------------------- the curve preview

def profile(W_m=30.0):
    """The test profile (metres): flat, rolling hills, a 30 deg slope, a plateau, a rounded cliff lip, a valley, a rise.
    -> z(x) sampled at 1 px (64 per m), smoothed (a Gaussian, sigma 0.35 m) so every lip and foot is round."""
    import numpy as np
    pts = [(0, 0.0), (4, 0.0), (5.5, 0.45), (7, 0.0), (8.5, 0.55), (10, 0.2), (14, 0.2 + 4 * math.tan(math.radians(30))),
           (16.6, 2.5), (17.7, -0.4), (19.5, -0.85), (22.0, -0.45), (26, 0.35), (W_m + 1, 0.6)]
    xs = np.arange(int(W_m * PPU)) / PPU
    z = np.interp(xs, [p[0] for p in pts], [p[1] for p in pts])
    s = int(0.35 * PPU)
    k = np.exp(-0.5 * (np.arange(-3 * s, 3 * s + 1) / s) ** 2)
    k /= k.sum()
    zp = np.pad(z, 3 * s, mode="edge")
    return xs, np.convolve(zp, k, mode="valid")


def _bilinear(tex, u, v):
    """tex HxWx4 float premultiplied; u wraps in x, v clamps (outside rows -> transparent)."""
    import numpy as np
    H, Wt = tex.shape[:2]
    u = np.mod(u, Wt)
    u0 = np.floor(u).astype(np.int32)
    v0 = np.floor(v).astype(np.int32)
    fu, fv = (u - u0)[..., None], (v - v0)[..., None]
    u1 = (u0 + 1) % Wt
    out = np.zeros(u.shape + (4,), np.float32)
    for dv, wv in ((0, 1 - fv), (1, fv)):
        vv = v0 + dv
        ok = (vv >= 0) & (vv < H)
        vc = np.clip(vv, 0, H - 1)
        out += wv * ok[..., None] * ((1 - fu) * tex[vc, u0] + fu * tex[vc, u1])
    return out


def _premul(img):
    import numpy as np
    f = img.astype(np.float32) / 255.0
    f[..., :3] *= f[..., 3:4]
    return f


def bend(tex, surf_row, ys, X, Y, mode):
    """Sample a band texture along the curve for pixels (X, Y) (image coords, y down; ys = the surface row per column).
    mode 'normal': u = arc length at the nearest curve point, v = surf_row - the signed normal distance (a mesh band);
    mode 'shear': u = X, v = surf_row + (Y - ys[X]) (each column dropped vertically, today's GroundStrip)."""
    import numpy as np
    Wc = len(ys)
    if mode == "shear":
        return _bilinear(tex, X.astype(np.float32), (surf_row + (Y - ys[np.clip(X, 0, Wc - 1)])).astype(np.float32))
    dy = np.gradient(ys)
    S = np.concatenate([[0.0], np.cumsum(np.sqrt(1 + ((ys[1:] - ys[:-1]) ** 2)))])
    xc = X.astype(np.float64)
    for _ in range(5):                                  # project (X, Y) onto the curve (Newton on the tangent)
        yc = np.interp(xc, np.arange(Wc), ys)
        g = np.interp(xc, np.arange(Wc), dy)
        n = np.sqrt(1 + g * g)
        tx, ty = 1 / n, g / n
        xc = np.clip(xc + ((X - xc) * tx + (Y - yc) * ty) * tx, 0, Wc - 1)
    yc = np.interp(xc, np.arange(Wc), ys)
    g = np.interp(xc, np.arange(Wc), dy)
    n = np.sqrt(1 + g * g)
    h = ((X - xc) * (g / n) - (Y - yc) * (1 / n))      # + = above the surface (the normal pointing up-screen)
    u = np.interp(xc, np.arange(Wc), S)
    return _bilinear(tex, u.astype(np.float32), (surf_row - h).astype(np.float32))


def preview(out_dir, planet="earth", pieces=None, out=None, footnote=None):
    """The curve preview (out=None: lock-free design run, its pieces also written to <out_dir>/b175/) or, with out and
    footnote, the export's stamped review drawn from the exported frames (main)."""
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    design = pieces is None
    pieces = pieces or render_all(planet)
    dd = os.path.join(out_dir, "b175")
    os.makedirs(dd, exist_ok=True)
    for name, (frames, _w) in (pieces.items() if design else ()):
        pngio.write_png(os.path.join(dd, f"{planet}_{name}_color.png"), np.concatenate(frames, axis=1) if len(frames) > 1 else frames[0])
    xs, z = profile()
    Wp = len(xs)
    PH = 512                                             # 8 m: z from -3.0 (bottom) to +5.0 (top)
    ys = (PH - (z + 3.0) * PPU).astype(np.float64)       # the surface row per column
    Y, X = np.mgrid[0:PH, 0:Wp]
    sky = np.array(v3.hex_rgb(v3.PALETTES[planet]["sky"]), np.float32) / 255.0
    C = colours(planet)
    soil = np.array(v3.hex_rgb(C["soil"]), np.float32) / 255.0
    solid = Y > ys[X]

    def compose(band_tex, surf, mode, fill_tex=None, scoop=None):
        img = np.empty((PH, Wp, 3), np.float32)
        img[:] = sky
        if fill_tex is None:
            img[solid] = soil
        else:
            fv = _bilinear(fill_tex, X.astype(np.float32), np.mod(Y.astype(np.float32), fill_tex.shape[0]))
            img[solid] = fv[solid][:, :3] + (1 - fv[solid][:, 3:4]) * soil
        if scoop is not None:
            cx, cz, r = scoop
            hole = ((X - cx) ** 2 + (Y - cz) ** 2 <= r * r) & solid
            back = img[hole] * 0.55                       # the scoop shows the cross-section's back wall, darker
            img[hole] = back
        b = np.zeros((PH, Wp, 4), np.float32)
        for c0 in range(0, Wp, 480):                       # in column chunks (memory)
            sl = slice(c0, min(Wp, c0 + 480))
            b[:, sl] = bend(band_tex, surf, ys, X[:, sl], Y[:, sl], mode)
        if scoop is not None:
            b[hole] = 0
        img = b[..., :3] + (1 - b[..., 3:4]) * img
        return img
    strip = pngio.read_png_np(os.path.join(ART, "terrain", planet, "ground_strip_color.png"))
    strip_tex = _premul(np.concatenate([strip[:, i * 68:i * 68 + 64] for i in range(8)], axis=1))
    band_tex = _premul(pieces["ground_band"][0][0])
    fill_tex = _premul(pieces["ground_fill"][0][0])
    rows = []

    def surveyor_at(img, xm):
        try:
            sm = json.load(open(os.path.join(ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
            sh = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))
            fr = sh[:sm["frame_height"], :sm["frame_width"]]
            X0 = int(xm * PPU)
            gy = int(round(ys[X0]))
            review._over(img, fr, X0 - sm["frame_width"] // 2, gy - sm["frame_height"] + int(round(sm["pivot"][1] * sm["frame_height"])) + 2)
        except (OSError, KeyError, ValueError):
            pass
    A = compose(strip_tex, 24, "shear")
    surveyor_at(A, 2.0), surveyor_at(A, 12.0), surveyor_at(A, 20.5)
    rows.append((f"today's terrain/{planet}/ground_strip per column (vertical shear, as GroundStrip draws it): on the 30 deg slope and the "
                 "lip its top detail tilts and the ink edge thins", A))
    B = compose(strip_tex, 24, "normal")
    surveyor_at(B, 2.0), surveyor_at(B, 12.0), surveyor_at(B, 20.5)
    rows.append(("the same strip bent along the curve (a mesh band, u = arc length): its top detail leans with the slope and splays on the "
                 "lip; its 2 m body folds at the cliff", B))
    scoop = (int(8.6 * PPU), int(round(ys[int(8.6 * PPU)])) + 20, 62)
    Cimg = compose(band_tex, SURF_ROW, "normal", fill_tex, scoop)
    # the dig rim round the scoop's wall (the band's own mapping on a circle), the decor upright, the lip, a puff
    cx, cy, r = scoop
    ang = np.arctan2(Y - cy, X - cx)
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    near = (np.abs(dist - r) < RIM_H) & solid & (dist >= r - 1)
    rim_tex = _premul(pieces["dig_rim"][0][0])
    rv = _bilinear(rim_tex, ((ang + math.pi) * r).astype(np.float32), (RIM_ROW + (dist - r)).astype(np.float32))
    rv[~near] = 0
    Cimg = rv[..., :3] + (1 - rv[..., 3:4]) * Cimg
    slope = np.degrees(np.arctan(np.abs(np.gradient(ys))))
    brink = int(15 * PPU) + int(np.argmax(slope[int(15 * PPU):] > 25.0))     # the cliff's brink: where the drop passes 25 deg
    decor = pieces["ground_decor"][0]
    rnd = random.Random(5)
    xm = 0.6
    while xm < 29.5:
        X0 = int(xm * PPU)
        if slope[max(0, X0 - 20):X0 + 20].max() < 33.0 and abs(X0 - cx) > r + 20 and abs(X0 - brink) > 60:
            k = rnd.choice((0, 0, 1, 1, 2, 3, 4, 5))
            fr = decor[k]
            review._over(Cimg, fr, X0 - 32, int(round(ys[X0])) - 64 + 6 + 2)
        xm += rnd.uniform(0.7, 1.6)
    lip = pieces["ground_lip"][0][0]
    xl = brink - 10
    review._over(Cimg, lip, xl - int(0.55 * 128), int(round(ys[xl])) - int((1 - 0.6) * 96))
    puff = pieces["dig_puff"][0][3]
    review._over(Cimg, puff, cx - 64 + 40, int(round(ys[cx])) - 96 - 10)
    surveyor_at(Cimg, 2.0), surveyor_at(Cimg, 12.0), surveyor_at(Cimg, 20.5)
    rows.append(("NEW: ground_band bent along the curve (the ink edge on the surface row, only low scallops above it) over ground_fill "
                 "(world space), ground_decor upright, ground_lip on the brink, a dug scoop with dig_rim and dig_puff 3", Cimg))
    # the pieces
    PW = Wp
    piece_h = 512 + 60
    P = np.empty((piece_h, PW, 3), np.float32)
    P[:] = review.PAPER
    x = 8
    review._over(P, pieces["ground_band"][0][0], x, 40)
    review._label(P, "ground_band 512x64 (surface row 24)", x, 20)
    review._over(P, pieces["dig_rim"][0][0], x, 140)
    review._label(P, "dig_rim 256x16 (ink row 4)", x, 120)
    for j, fr in enumerate(pieces["ground_decor"][0]):
        P[200:264, x + j * 72:x + j * 72 + 64] = sky
        review._over(P, fr, x + j * 72, 200)
    review._label(P, "ground_decor x6 (upright)", x, 180)
    P[300:396, x:x + 128] = sky
    review._over(P, lip, x, 300)
    review._label(P, "ground_lip 128x96", x, 280)
    for j, fr in enumerate(pieces["dig_puff"][0]):
        P[430:558, x + j * 132:x + j * 132 + 128] = sky
        review._over(P, fr, x + j * 132, 430)
    review._label(P, "dig_puff 8 frames", x, 412)
    fx0 = 1100
    ft = pieces["ground_fill"][0][0]
    tiled = np.concatenate([np.concatenate([ft, ft], axis=1)] * 1, axis=0)[:, :768]
    review._over(P, tiled, fx0, 40)
    review._label(P, "ground_fill 512x512, tiled in x (the seam at 512)", fx0, 20)
    lines = []
    for name, (frames, widths) in pieces.items():
        o = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
        n_ = [w for w in widths if w[0] < v3.OUTER_SPLIT]
        rng = lambda q: f"{min(w[1] for w in q):.1f}-{max(w[2] for w in q):.1f}" if q else "-"  # noqa: E731
        pal = v3.palette_hits(frames[0], planet)[0] * 100
        m = v3.EDGE_MARGIN
        tiles = name in ("ground_band", "ground_fill", "dig_rim")
        edge = [i for i, f in enumerate(frames) if not tiles and (f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any())]
        seam = ""
        if tiles:                                         # periodicity: the drawing rendered 2 tiles wide (2 tall for the fill), the copies compared
            w0, h0 = PIECES[name][0], PIECES[name][1]
            two, _w2 = render_piece(name, planet, 0, mx=2, mz=2 if name == "ground_fill" else 1, ss=1)
            dx_ = np.abs(two[:h0, :w0].astype(np.int32) - two[:h0, w0:2 * w0].astype(np.int32))
            seam = f"; tiles: copy diff mean {dx_.mean():.2f} p99 {np.percentile(dx_, 99):.0f} (x)"
            if name == "ground_fill":
                dz_ = np.abs(two[:h0, :w0].astype(np.int32) - two[h0:2 * h0, :w0].astype(np.int32))
                seam += f", mean {dz_.mean():.2f} p99 {np.percentile(dz_, 99):.0f} (z)"
            del two
        lines.append(f"{name}: ink {rng(o)} / {rng(n_)} px, palette {pal:.1f}%{seam}{'; EDGE ' + str(edge) if edge else ''}")
    img_rows = []
    for title, im in rows:
        lab = np.empty((22, Wp, 3), np.float32)
        lab[:] = review.PAPER
        review._label(lab, title[:235], 6, 4)
        img_rows += [lab, im]
    foot = np.empty((30 + 16 * len(lines), Wp, 3), np.float32)
    foot[:] = review.PAPER
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack(img_rows + [P, foot])
    del img_rows, rows, A, B, Cimg, P, foot          # the panels live on only in img (a 2300 x 1920 float image is 53 MB)
    import time
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "curve preview (lock-free, fakegp + numpy; test profile 30 m at 1x)"), 2,
                img.shape[0] - 16, (1.0, 1.0, 0.85))
    out = out or os.path.join(out_dir, f"review_b175_{planet}_curve_preview.png")
    shape = img.shape                                 # review.write's to_u8 holds three float copies: convert in place
    np.clip(img, 0.0, 1.0, out=img)
    img *= 255.0
    np.rint(img, out=img)
    u8 = np.empty(shape[:2] + (4,), np.uint8)
    u8[..., :3] = img
    u8[..., 3] = 255
    del img
    pngio.write_png(out, u8)
    print("written", out, shape[1], "x", shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    import numpy as np  # noqa: F401
    preview(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "earth")
    fakegp.restore()
