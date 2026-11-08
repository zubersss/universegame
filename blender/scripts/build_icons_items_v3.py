"""B-199 (LEAD cycle 284): the item icons re-inked as v3 (49 of icons/<item>/base were v2 shaded renders: no ink, no json, seen
in every inventory and crafting panel). Same keys, same 128x128 size: the export replaces each base_color.png in place and
adds its json (B-128's: style v3, icon, pivot centre). Each item keeps its v2 identity (shape, colour) drawn in the house
style: ink 2-3 / 1-1.5 px, the material colour lit top-left, its mid and deep shadow tones (D-100), drawn marks, the Earth
palette's tones only; no faces (D-101: never two glints side by side). Batches (LEAD: ores and crystals first):

  batch 1  iron, copper, nickel, aluminium, carbon, graphite, hematite, silica, solarite, deep_diamond (ACCEPTED 15:2x)
  batch 2  water_ice, methane_ice, polar_ice, ring_ice, superionic_ice (Neptune's violet), ammonia_ice, helium3_condensate,
           metallic_hydrogen, oxygen
  Only EXPORT_BATCHES (the accepted ones) export; the preview takes a batch number.

  python -I build_icons_items_v3.py <review png>   lock-free preview: each new icon over its v2 render at 1x and at the
                                                    32 px slot, beside the v3 icons already in (B-128's cubes, wind_anchor)
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp, v3  # noqa: E402

G = fakegp.install()
import gp_raster as GR  # noqa: E402

P = v3.PALETTES["earth"]
O, I = G.OUTER, G.INNER
SIZE, PPU = 128, 128                              # 1 m = 128 px: the objects are ~0.8 m across
KEY = "icons/{}/base"
TONES = {"green": "green", "brown": "brown", "sky": "sky", "teal": "teal", "mustard": "mustard", "red": "red", "off": "offwhite"}


def mats(gp, planet="earth"):
    """The tones of `planet`'s palette under the Earth slot names (Neptune's 'mustard' slot is its violet)."""
    Pp = v3.PALETTES[planet]
    M = {"ink": G.mat(gp, "icon_ink", fill=None)}
    for k, slot in TONES.items():
        h = Pp[slot]
        for suf, hx in (("", h), ("_sh", v3.shadow_of(h, planet)), ("_dp", v3.deep_of(h, planet))):
            M[k + suf] = G.mat(gp, f"icon_{k}{suf}", fill=hx, ink=False)
            M[k + suf + "_i"] = G.mat(gp, f"icon_{k}{suf}_i", fill=hx)
    return M


def lump(cx, cz, rx, rz, seed, n=9, jit=0.12):
    """A faceted lump's outline in angular order (index i at about 360 i / n degrees)."""
    rnd = random.Random(seed)
    return [(cx + rx * (1 + rnd.uniform(-jit, jit * 0.6)) * math.cos(a), cz + rz * (1 + rnd.uniform(-jit, jit * 0.6)) * math.sin(a))
            for a in [2 * math.pi * i / n + rnd.uniform(-0.12, 0.12) for i in range(n)]]


def faceted(d, M, pts, base, lit, dark, cx, cz, seams=True):
    """Fill, a lit top-left facet, a dark lower-right facet (wedges to an inner point), facet seams, the ink outline."""
    n = len(pts)
    ang = [math.degrees(math.atan2(z - cz, x - cx)) % 360 for x, z in pts]
    G.stroke(d, pts, M[base], 0.0, cyclic=True)
    li = [p for p, a in zip(pts, ang) if 75 <= a <= 215]
    dk = [p for p, a in zip(pts, ang) if a >= 235 or a <= 10]
    rx = max(abs(x - cx) for x, _z in pts)
    rz = max(abs(z - cz) for _x, z in pts)
    pin_l, pin_d = (cx - rx * 0.12, cz + rz * 0.14), (cx + rx * 0.16, cz - rz * 0.12)
    if len(li) >= 2:
        G.stroke(d, li + [pin_l], M[lit], 0.0, cyclic=True)
    if len(dk) >= 2:
        G.stroke(d, sorted(dk, key=lambda p: (math.degrees(math.atan2(p[1] - cz, p[0] - cx)) - 200) % 360) + [pin_d], M[dark], 0.0, cyclic=True)
    if seams:
        for p in pts[1:n:2]:
            G.seam(d, [((p[0] + pin_l[0]) / 2, (p[1] + pin_l[1]) / 2), (p[0] * 0.8 + cx * 0.2, p[1] * 0.8 + cz * 0.2)], M["ink"])
    G.stroke(d, pts, M["ink"], O, cyclic=True)


def glint(d, M, x, z, s=0.03):
    """A highlight without ink (inked, the tiny diamond read as a dark mark at 1x)."""
    G.stroke(d, [(x, z + s), (x + s * 0.45, z), (x, z - s), (x - s * 0.45, z)], M["off"], 0.0, cyclic=True)


def prism(d, M, x0, x1, z0, tip, light, dark, lean=0.0):
    """A pointed crystal prism, light left half, dark right half, its middle edge."""
    xm = (x0 + x1) / 2
    top = (xm + lean, tip)
    sh = (x1 - x0) * 0.25
    left = [(x0, z0), (xm, z0 - sh * 0.3), (xm + lean * 0.7, tip - sh * 1.6), top, (x0 + lean * 0.8, tip - sh * 2.2)]
    right = [(xm, z0 - sh * 0.3), (x1, z0), (x1 + lean * 0.8, tip - sh * 2.2), top, (xm + lean * 0.7, tip - sh * 1.6)]
    G.stroke(d, left, M[light], 0.0, cyclic=True)
    G.stroke(d, right, M[dark], 0.0, cyclic=True)
    G.seam(d, [(xm, z0 - sh * 0.3), (xm + lean * 0.7, tip - sh * 1.6), top], M["ink"])
    G.stroke(d, [(x0, z0), (xm, z0 - sh * 0.3), (x1, z0), (x1 + lean * 0.8, tip - sh * 2.2), top, (x0 + lean * 0.8, tip - sh * 2.2)], M["ink"], O, cyclic=True)


# ---------------------------------------------------------------- batch 1: ores and crystals

def iron(d, M):
    pts = lump(0.0, -0.02, 0.37, 0.3, 11)
    faceted(d, M, pts, "red_sh", "red", "red_dp", 0.0, -0.02)
    for j, (x, z) in enumerate(((-0.12, 0.08), (0.1, -0.08), (0.18, 0.1), (-0.06, -0.14))):   # metal grains
        G.stroke(d, G.lumpy_ellipse(x, z, 0.03, 0.022, n=8, seed=20 + j), M["sky_i"], I, cyclic=True)
    G.specks(d, [(-0.22, -0.04), (0.02, 0.16), (0.24, -0.12)], M["ink"])
    glint(d, M, -0.17, 0.15)


def copper(d, M):
    pts = lump(0.0, -0.03, 0.38, 0.29, 12)
    faceted(d, M, pts, "teal_sh", "teal", "teal_dp", 0.0, -0.03)
    for j, (x, z, r) in enumerate(((-0.12, 0.04, 0.07), (0.14, -0.06, 0.06), (0.02, -0.16, 0.045))):   # copper nuggets
        nug = G.lumpy_ellipse(x, z, r * 1.2, r, n=12, lump=0.12, seed=30 + j)
        G.stroke(d, nug, M["mustard"], 0.0, cyclic=True)
        G.stroke(d, [q for q in nug if q[1] < z] + [(x, z)], M["red_sh"], 0.0, cyclic=True)
        G.stroke(d, nug, M["ink"], I, cyclic=True)
    glint(d, M, -0.15, 0.06, 0.025)


def nickel(d, M):
    pts = G.lumpy_ellipse(0.0, -0.02, 0.33, 0.29, n=24, lump=0.06, seed=41)
    G.stroke(d, pts, M["sky_sh"], 0.0, cyclic=True)
    G.stroke(d, [q for q in pts if q[0] - q[1] * 0.6 > 0.06] + [(0.08, -0.06)], M["sky_dp"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(-0.1, 0.08, 0.15, 0.12, n=16, lump=0.05, seed=42), M["sky"], 0.0, cyclic=True)
    for j, (x, z) in enumerate(((0.12, 0.08), (-0.04, -0.12), (0.16, -0.1))):                 # dimples
        G.stroke(d, G.lumpy_ellipse(x, z, 0.035, 0.025, n=8, seed=43 + j), M["sky_dp"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(-0.14, 0.12, 0.05, 0.03, n=10, seed=46), M["off"], 0.0, cyclic=True)
    G.stroke(d, pts, M["ink"], O, cyclic=True)


def aluminium(d, M):
    top = [(-0.3, 0.06), (0.22, 0.06), (0.36, 0.16), (-0.16, 0.16)]                          # an ingot in 3/4 view
    front = [(-0.36, -0.16), (0.24, -0.16), (0.22, 0.06), (-0.3, 0.06)]
    side = [(0.24, -0.16), (0.38, -0.06), (0.36, 0.16), (0.22, 0.06)]
    G.stroke(d, front, M["off_sh"], 0.0, cyclic=True)
    G.stroke(d, side, M["sky_sh"], 0.0, cyclic=True)
    G.stroke(d, top, M["off"], 0.0, cyclic=True)
    G.stroke(d, [(-0.2, -0.06), (0.1, -0.06), (0.09, 0.0), (-0.19, 0.0)], M["off_dp"], 0.0, cyclic=True)   # the stamped panel
    for poly in (top, side):
        G.seam(d, poly, M["ink"])
    G.stroke(d, [(-0.36, -0.16), (0.24, -0.16), (0.38, -0.06), (0.36, 0.16), (-0.16, 0.16), (-0.3, 0.06)], M["ink"], O, cyclic=True)
    G.seam(d, [(-0.3, 0.06), (0.22, 0.06), (0.24, -0.16)], M["ink"])
    G.stroke(d, [(-0.12, 0.13), (0.1, 0.13), (0.11, 0.115), (-0.11, 0.115)], M["off_i"], 0.0, cyclic=True)


def carbon(d, M):
    pts = lump(0.0, -0.01, 0.34, 0.31, 51, n=7, jit=0.1)
    faceted(d, M, pts, "sky_dp", "sky_sh", "brown_dp", 0.0, -0.01)
    glint(d, M, -0.12, 0.12, 0.028)
    G.specks(d, [(0.1, 0.05), (0.16, -0.12), (-0.08, -0.16)], M["ink"])


def graphite(d, M):
    for i, (dx, dz, w) in enumerate(((-0.02, -0.17, 0.36), (0.03, -0.05, 0.31), (-0.04, 0.07, 0.25))):   # stacked sheets
        topf = [(dx - w, dz + 0.04), (dx + w - 0.08, dz + 0.04), (dx + w, dz + 0.1), (dx - w + 0.08, dz + 0.1)]
        edge = [(dx - w, dz - 0.02), (dx + w - 0.08, dz - 0.02), (dx + w, dz + 0.04), (dx + w - 0.08, dz + 0.04), (dx - w, dz + 0.04)]
        G.stroke(d, edge, M["sky_dp"], 0.0, cyclic=True)
        G.stroke(d, topf, M["sky_sh"], 0.0, cyclic=True)
        G.seam(d, [(dx - w + 0.12, dz + 0.07), (dx + w - 0.15, dz + 0.07)], M["ink"])
        G.stroke(d, [(dx - w, dz - 0.02), (dx + w - 0.08, dz - 0.02), (dx + w, dz + 0.04), (dx + w, dz + 0.1), (dx - w + 0.08, dz + 0.1), (dx - w, dz + 0.04)],
                 M["ink"], O if i == 0 else I, cyclic=True)
        G.seam(d, [(dx - w, dz + 0.04), (dx + w - 0.08, dz + 0.04), (dx + w, dz + 0.1)], M["ink"])
    glint(d, M, -0.12, 0.15, 0.022)


def hematite(d, M):
    balls = [(-0.17, -0.1, 0.14), (0.16, -0.12, 0.15), (0.0, 0.02, 0.19), (0.12, 0.17, 0.1)]   # a cluster of 'blueberries'
    for j, (x, z, r) in enumerate(balls):
        b = G.lumpy_ellipse(x, z, r, r * 0.96, n=20, lump=0.03, seed=60 + j)
        G.stroke(d, b, M["red_dp"], 0.0, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x - r * 0.25, z + r * 0.25, r * 0.55, r * 0.45, n=14, lump=0.03, seed=65 + j), M["red_sh"], 0.0, cyclic=True)
        G.stroke(d, b, M["ink"], O if r > 0.12 else I, cyclic=True)
    glint(d, M, -0.06, 0.1, 0.035)                                                            # one glint only (no pair: D-101)


def silica(d, M):
    peb = G.lumpy_ellipse(0.02, -0.24, 0.3, 0.1, n=18, lump=0.08, seed=71)                  # a sandy pebble at the root
    G.stroke(d, peb, M["mustard_sh_i"], O, cyclic=True)
    for x0, x1, tip, lean in ((-0.24, -0.08, 0.2, -0.05), (0.08, 0.24, 0.16, 0.06), (-0.1, 0.1, 0.38, 0.0)):
        prism(d, M, x0, x1, -0.2, tip, "off", "sky_sh", lean)
    glint(d, M, -0.03, 0.22, 0.026)


def solarite(d, M):
    G.stroke(d, G.lumpy_ellipse(0.0, -0.16, 0.17, 0.12, n=16, lump=0.06, seed=81), M["brown_dp_i"], O, cyclic=True)   # the dark core
    for x0, x1, tip, lean in ((-0.3, -0.14, 0.12, -0.08), (0.14, 0.3, 0.1, 0.08), (-0.18, -0.02, 0.32, -0.03), (0.02, 0.18, 0.36, 0.04)):
        prism(d, M, x0, x1, -0.22, tip, "mustard", "mustard_sh", lean)
    glint(d, M, 0.08, 0.2, 0.026)


def deep_diamond(d, M):
    T, Bm, L, R, F = (0.0, 0.38), (0.0, -0.38), (-0.3, 0.02), (0.3, 0.02), (0.06, -0.02)
    for tri, mat in (((T, L, F), "off"), ((T, F, R), "sky"), ((L, F, Bm), "sky_sh"), ((F, R, Bm), "sky_dp")):
        G.stroke(d, list(tri), M[mat], 0.0, cyclic=True)
    for a, b in ((T, F), (L, F), (F, R), (F, Bm)):
        G.seam(d, [a, b], M["ink"])
    G.stroke(d, [T, R, Bm, L], M["ink"], O, cyclic=True)
    glint(d, M, -0.08, 0.16, 0.03)


# ---------------------------------------------------------------- batch 2: ices and gases

def _chunk(d, M, seed, base, lit, dark, cracks=True):
    pts = lump(0.0, -0.02, 0.35, 0.32, seed, n=7, jit=0.08)
    faceted(d, M, pts, base, lit, dark, 0.0, -0.02)
    if cracks:
        G.seam(d, [(-0.05, 0.12), (0.02, 0.02), (0.0, -0.1)], M["ink"])
    glint(d, M, -0.15, 0.14)


def water_ice(d, M):
    _chunk(d, M, 101, "sky", "off", "sky_sh")


def methane_ice(d, M):
    _chunk(d, M, 102, "teal_sh", "teal", "teal_dp")
    G.stroke(d, [(-0.2, 0.18), (-0.06, 0.24), (-0.02, 0.2), (-0.17, 0.14)], M["off"], 0.0, cyclic=True)   # a frost streak


def _box(d, M, top_m, front_m, side_m, w=0.3, h=0.28, dx=0.13, dz=0.1, cz=-0.06):
    """A block in 3/4 view: the front face, the side, the top; -> the corner points."""
    fl, fr, fb, ft = -w, w - dx, cz - h / 2, cz + h / 2
    front = [(fl, fb), (fr, fb), (fr, ft), (fl, ft)]
    side = [(fr, fb), (fr + dx, fb + dz), (fr + dx, ft + dz), (fr, ft)]
    top = [(fl, ft), (fr, ft), (fr + dx, ft + dz), (fl + dx, ft + dz)]
    for poly, m in ((front, front_m), (side, side_m), (top, top_m)):
        G.stroke(d, poly, M[m], 0.0, cyclic=True)
    return fl, fr, fb, ft, dx, dz


def _box_ink(d, M, fl, fr, fb, ft, dx, dz):
    G.stroke(d, [(fl, fb), (fr, fb), (fr + dx, fb + dz), (fr + dx, ft + dz), (fl + dx, ft + dz), (fl, ft)], M["ink"], O, cyclic=True)
    G.seam(d, [(fl, ft), (fr, ft), (fr + dx, ft + dz)], M["ink"])
    G.seam(d, [(fr, ft), (fr, fb)], M["ink"])


def polar_ice(d, M):
    fl, fr, fb, ft, dx, dz = _box(d, M, "off", "sky", "sky_sh", w=0.32, h=0.42)
    for z in (fb + 0.12, ft - 0.12):                                                         # two straps round it
        G.stroke(d, [(fl, z - 0.025), (fr, z - 0.025), (fr + dx, z - 0.025 + dz), (fr + dx, z + 0.025 + dz), (fr, z + 0.025), (fl, z + 0.025)],
                 M["brown_dp_i"], I, cyclic=True)
    _box_ink(d, M, fl, fr, fb, ft, dx, dz)
    glint(d, M, fl + 0.08, ft - 0.05, 0.025)


def ring_ice(d, M):
    """A lumpy, uneven chunk of ring ice (LEAD 15:3x: the smooth spotted oval read as an egg): white, cool shading, rime
    crystals on its top, specks of ring grit, one glint."""
    pts = lump(0.0, -0.03, 0.36, 0.3, 112, n=11, jit=0.18)
    faceted(d, M, pts, "off", "off", "sky", 0.0, -0.03)
    for j, (x, z, r) in enumerate(((-0.16, 0.2, 0.04), (-0.04, 0.24, 0.032), (0.1, 0.2, 0.036))):   # rime on the top
        G.stroke(d, B_shard(x, z, r, 210 + j), M["off_i"], I, cyclic=True)
    for j, (x, z) in enumerate(((0.12, -0.12), (-0.08, -0.16), (0.2, 0.02))):               # ring grit
        G.stroke(d, G.lumpy_ellipse(x, z, 0.018, 0.013, n=8, seed=215 + j), M["sky_dp"], 0.0, cyclic=True)
    glint(d, M, -0.17, 0.08)


def B_shard(x, z, r, seed, sides=5):
    rnd = random.Random(seed)
    return [(x + r * (1 + rnd.uniform(-0.25, 0.1)) * math.cos(2 * math.pi * i / sides + rnd.uniform(-0.2, 0.2)),
             z + r * (1 + rnd.uniform(-0.25, 0.1)) * math.sin(2 * math.pi * i / sides + rnd.uniform(-0.2, 0.2))) for i in range(sides)]


def superionic_ice(d, M):
    """Neptune's palette (its 'mustard' slot is the violet): a violet ice cube held in a dark cage frame."""
    fl, fr, fb, ft, dx, dz = _box(d, M, "mustard", "mustard_sh", "mustard_dp", w=0.24, h=0.3, dx=0.1, dz=0.08, cz=-0.04)
    _box_ink(d, M, fl, fr, fb, ft, dx, dz)
    cw = 0.035
    for a, b in (((fl - 0.08, fb - 0.08), (fr + 0.04, fb - 0.08)), ((fr + 0.04, fb - 0.08), (fr + dx + 0.06, fb + dz - 0.04)),
                 ((fl - 0.08, fb - 0.08), (fl - 0.08, ft + 0.06)), ((fr + 0.04, fb - 0.08), (fr + 0.04, ft + 0.06)),
                 ((fr + dx + 0.06, fb + dz - 0.04), (fr + dx + 0.06, ft + dz + 0.06)), ((fl - 0.08, ft + 0.06), (fr + 0.04, ft + 0.06)),
                 ((fr + 0.04, ft + 0.06), (fr + dx + 0.06, ft + dz + 0.06)), ((fl - 0.08, ft + 0.06), (fl - 0.08 + dx + 0.02, ft + dz + 0.06)),
                 ((fl - 0.08 + dx + 0.02, ft + dz + 0.06), (fr + dx + 0.06, ft + dz + 0.06))):
        G.stroke(d, G.hose_outline([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b], cw), M["brown_dp_i"], I, cyclic=True)
    glint(d, M, fl + 0.06, ft - 0.05, 0.025)


def ammonia_ice(d, M):
    G.stroke(d, G.lumpy_ellipse(0.02, -0.1, 0.16, 0.13, n=16, lump=0.08, seed=121), M["mustard_sh_i"], O, cyclic=True)   # the tan core
    for x0, x1, tip, lean in ((-0.32, -0.18, 0.06, -0.12), (0.2, 0.33, 0.08, 0.12), (-0.2, -0.06, 0.3, -0.06), (0.08, 0.2, 0.26, 0.07)):
        prism(d, M, x0, x1, -0.24, tip, "off", "off_sh", lean)                                # white shards fanning out (rev: green_sh read green)
    glint(d, M, -0.12, 0.2, 0.025)


def helium3_condensate(d, M):
    body = [(-0.17, -0.26), (0.17, -0.26), (0.19, -0.2), (0.19, 0.18), (0.17, 0.24), (-0.17, 0.24), (-0.19, 0.18), (-0.19, -0.2)]
    G.stroke(d, body, M["off"], 0.0, cyclic=True)                                             # the glass (rev: a solid red can)
    G.stroke(d, [(0.08, -0.24), (0.17, -0.24), (0.17, 0.22), (0.08, 0.22)], M["off_sh"], 0.0, cyclic=True)
    lvl = 0.06                                                                                # the pink condensate, two-thirds full
    G.stroke(d, [(-0.19, -0.2), (0.19, -0.2), (0.19, lvl), (0.05, lvl + 0.015), (-0.19, lvl)], M["red"], 0.0, cyclic=True)
    G.stroke(d, [(0.08, -0.2), (0.19, -0.2), (0.19, lvl), (0.08, lvl + 0.01)], M["red_sh"], 0.0, cyclic=True)
    G.seam(d, [(-0.19, lvl), (0.05, lvl + 0.015), (0.19, lvl)], M["ink"])
    G.stroke(d, [(-0.13, -0.14), (-0.09, -0.14), (-0.09, 0.18), (-0.13, 0.18)], M["off"], 0.0, cyclic=True)   # the glass's sheen
    for zc in (-0.27, 0.25):                                                                  # the caps
        G.stroke(d, [(-0.2, zc - 0.05), (0.2, zc - 0.05), (0.2, zc + 0.05), (-0.2, zc + 0.05)], M["sky_dp_i"], I, cyclic=True)
    G.stroke(d, [(-0.07, 0.3), (0.07, 0.3), (0.06, 0.38), (-0.06, 0.38)], M["sky_sh_i"], I, cyclic=True)   # the nozzle
    G.stroke(d, body, M["ink"], O, cyclic=True)
    glint(d, M, -0.1, 0.1, 0.025)


def metallic_hydrogen(d, M):
    base = G.lumpy_ellipse(0.0, -0.24, 0.34, 0.09, n=24, lump=0.02, seed=131)
    G.stroke(d, base, M["sky_dp_i"], O, cyclic=True)                                          # the containment pod's base
    dome = [(-0.3, -0.22)] + G.bezier((-0.3, -0.22), (-0.32, 0.3), (0.32, 0.3), (0.3, -0.22), n=16)[1:]
    G.stroke(d, dome, M["sky"], 0.0, cyclic=True)
    for j, (x, z, r) in enumerate(((-0.08, -0.08, 0.1), (0.1, -0.1, 0.09), (0.02, 0.06, 0.08))):   # three metal spheres (never a pair)
        s = G.lumpy_ellipse(x, z, r, r * 0.96, n=16, lump=0.02, seed=132 + j)
        G.stroke(d, s, M["sky_sh"], 0.0, cyclic=True)
        G.stroke(d, [q for q in s if q[0] - x + (q[1] - z) * 0.6 > 0.0] + [(x, z)], M["sky_dp"], 0.0, cyclic=True)
        G.stroke(d, s, M["ink"], I, cyclic=True)
    G.stroke(d, dome, M["ink"], O, cyclic=True)
    G.stroke(d, [(-0.2, 0.05), (-0.17, 0.16), (-0.12, 0.2), (-0.16, 0.09)], M["off"], 0.0, cyclic=True)   # the glass's sheen
    glint(d, M, 0.0, 0.1, 0.022)


def oxygen(d, M):
    body = [(-0.16, -0.32)] + G.bezier((-0.16, -0.32), (-0.18, 0.22), (-0.14, 0.26), (-0.06, 0.28), n=8)[1:] + \
        [(0.06, 0.28)] + G.bezier((0.06, 0.28), (0.14, 0.26), (0.18, 0.22), (0.16, -0.32), n=8)[1:]
    G.stroke(d, body, M["off"], 0.0, cyclic=True)                                             # a white tank, a blue band, its valve
    G.stroke(d, [(0.06, -0.31), (0.16, -0.32), (0.17, 0.2), (0.07, 0.24)], M["off_sh"], 0.0, cyclic=True)
    G.stroke(d, [(-0.17, -0.06), (0.17, -0.06), (0.17, 0.04), (-0.17, 0.04)], M["teal"], 0.0, cyclic=True)
    G.stroke(d, [(0.08, -0.06), (0.17, -0.06), (0.17, 0.04), (0.08, 0.04)], M["teal_sh"], 0.0, cyclic=True)
    G.seam(d, [(-0.17, -0.06), (0.17, -0.06)], M["ink"])
    G.seam(d, [(-0.17, 0.04), (0.17, 0.04)], M["ink"])
    G.stroke(d, body, M["ink"], O, cyclic=True)
    G.stroke(d, [(-0.07, 0.28), (0.07, 0.28), (0.07, 0.36), (-0.07, 0.36)], M["teal_dp_i"], I, cyclic=True)
    glint(d, M, -0.09, 0.16, 0.025)


# ---------------------------------------------------------------- batch 3: crafted items

def _top_pt(fl, fr, ft, dx, dz, u, v):
    """A point on a 3/4 block's top face: u along the front edge, v back."""
    return (fl + u * (fr - fl) + v * dx, ft + v * dz)


def _quad(fl, fr, ft, dx, dz, u0, u1, v0, v1):
    return [_top_pt(fl, fr, ft, dx, dz, u0, v0), _top_pt(fl, fr, ft, dx, dz, u1, v0),
            _top_pt(fl, fr, ft, dx, dz, u1, v1), _top_pt(fl, fr, ft, dx, dz, u0, v1)]


def _pad(d, M, top_m, front_m, side_m, strip, strip_sh, quilt=True):
    """A flat pad in 3/4 view, quilted 2 x 2, a band across it."""
    fl, fr, fb, ft, dx, dz = _box(d, M, top_m, front_m, side_m, w=0.34, h=0.08, dx=0.2, dz=0.3, cz=-0.12)
    G.stroke(d, _quad(fl, fr, ft, dx, dz, 0.0, 1.0, 0.44, 0.58), M[strip], 0.0, cyclic=True)
    G.stroke(d, _quad(fl, fr, ft, dx, dz, 0.6, 1.0, 0.44, 0.58), M[strip_sh], 0.0, cyclic=True)
    if quilt:
        G.seam(d, [_top_pt(fl, fr, ft, dx, dz, 0.5, 0.0), _top_pt(fl, fr, ft, dx, dz, 0.5, 0.44)], M["ink"])
        G.seam(d, [_top_pt(fl, fr, ft, dx, dz, 0.5, 0.58), _top_pt(fl, fr, ft, dx, dz, 0.5, 1.0)], M["ink"])
    G.seam(d, [_top_pt(fl, fr, ft, dx, dz, 0.0, 0.44), _top_pt(fl, fr, ft, dx, dz, 1.0, 0.44)], M["ink"])
    G.seam(d, [_top_pt(fl, fr, ft, dx, dz, 0.0, 0.58), _top_pt(fl, fr, ft, dx, dz, 1.0, 0.58)], M["ink"])
    _box_ink(d, M, fl, fr, fb, ft, dx, dz)
    return fl, fr, fb, ft, dx, dz


def _ingot(d, M, top_m, front_m, side_m, panel_m):
    top = [(-0.3, 0.06), (0.22, 0.06), (0.36, 0.16), (-0.16, 0.16)]
    front = [(-0.36, -0.16), (0.24, -0.16), (0.22, 0.06), (-0.3, 0.06)]
    side = [(0.24, -0.16), (0.38, -0.06), (0.36, 0.16), (0.22, 0.06)]
    for poly, m in ((front, front_m), (side, side_m), (top, top_m)):
        G.stroke(d, poly, M[m], 0.0, cyclic=True)
    G.stroke(d, [(-0.2, -0.06), (0.1, -0.06), (0.09, 0.0), (-0.19, 0.0)], M[panel_m], 0.0, cyclic=True)
    G.stroke(d, [(-0.36, -0.16), (0.24, -0.16), (0.38, -0.06), (0.36, 0.16), (-0.16, 0.16), (-0.3, 0.06)], M["ink"], O, cyclic=True)
    G.seam(d, [(-0.3, 0.06), (0.22, 0.06), (0.24, -0.16)], M["ink"])
    G.seam(d, [(0.22, 0.06), (0.36, 0.16)], M["ink"])
    glint(d, M, -0.2, 0.11, 0.022)


def _drum(d, M, body, body_sh, band, ring):
    """A cell lying on its side: a barrel with domed ends (rev: one open-looking cap read as a tube), its shaded underside,
    dark end rings, two coloured bands, a highlight along the top."""
    L, R, H, cap = -0.26, 0.22, 0.2, 0.1
    shell = ([(L + cap * math.cos(a), H * math.sin(a)) for a in [math.pi / 2 + math.pi * i / 12 for i in range(13)]] +     # left end, top -> bottom
             [(R + cap * math.cos(a), H * math.sin(a)) for a in [-math.pi / 2 + math.pi * i / 12 for i in range(13)]])     # right end, bottom -> top
    G.stroke(d, shell, M[body], 0.0, cyclic=True)
    G.stroke(d, [(x, z) for x, z in shell if z < -H * 0.3] + [(R, -H * 0.3), (L, -H * 0.3)], M[body_sh], 0.0, cyclic=True)
    for x0 in (L - 0.01, R - 0.03):                                                          # the end rings
        G.stroke(d, [(x0, -H), (x0 + 0.04, -H), (x0 + 0.04, H), (x0, H)], M[ring + "_i"], I, cyclic=True)
    for x0 in (-0.15, 0.06):                                                                  # the bands
        G.stroke(d, [(x0, -H), (x0 + 0.07, -H), (x0 + 0.07, H), (x0, H)], M[band], I, cyclic=True)
    G.stroke(d, [(L + 0.06, H * 0.55), (R - 0.06, H * 0.55), (R - 0.06, H * 0.72), (L + 0.06, H * 0.72)], M["off"], 0.0, cyclic=True)
    G.stroke(d, shell, M["ink"], O, cyclic=True)


def _cylinder(d, M, body, body_sh, top_m, x=0.0, w=0.2, zb=-0.24, zt=0.22):
    """An upright cylinder: body, its shaded right side, the top ellipse; -> the top ellipse."""
    G.stroke(d, G.lumpy_ellipse(x, zb, w, w * 0.32, n=20, lump=0.0, seed=160), M[body_sh], 0.0, cyclic=True)
    G.stroke(d, [(x - w, zb), (x + w, zb), (x + w, zt), (x - w, zt)], M[body], 0.0, cyclic=True)
    G.stroke(d, [(x + w * 0.45, zb), (x + w, zb), (x + w, zt), (x + w * 0.45, zt)], M[body_sh], 0.0, cyclic=True)
    top = G.lumpy_ellipse(x, zt, w, w * 0.32, n=20, lump=0.0, seed=161)
    G.stroke(d, top, M[top_m], 0.0, cyclic=True)
    outline = [(x - w, zt)] + [p for p in G.lumpy_ellipse(x, zb, w, w * 0.32, n=20, lump=0.0, seed=160) if p[1] <= zb] + [(x + w, zt)]
    G.stroke(d, sorted([p for p in outline], key=lambda p: p[0]), M["ink"], O)
    G.seam(d, [(x - w, zt), (x - w, zb)], M["ink"])
    G.seam(d, [(x + w, zt), (x + w, zb)], M["ink"])
    G.stroke(d, top, M["ink"], O, cyclic=True)
    return top


def circuit_board(d, M):
    fl, fr, fb, ft, dx, dz = _box(d, M, "green", "green_sh", "green_dp", w=0.36, h=0.05, dx=0.18, dz=0.3, cz=-0.1)
    for u0, u1, v0, v1 in ((0.12, 0.48, 0.35, 0.75), (0.56, 0.78, 0.12, 0.4)):              # two chips with their legs
        G.stroke(d, _quad(fl, fr, ft, dx, dz, u0, u1, v0, v1), M["sky_dp_i"], I, cyclic=True)
        for j in range(4):
            u = u0 + (u1 - u0) * (j + 0.5) / 4
            G.seam(d, [_top_pt(fl, fr, ft, dx, dz, u, v0), _top_pt(fl, fr, ft, dx, dz, u, v0 - 0.06)], M["ink"])
    for v in (0.2, 0.86):                                                                     # traces
        G.seam(d, [_top_pt(fl, fr, ft, dx, dz, 0.08, v), _top_pt(fl, fr, ft, dx, dz, 0.5, v), _top_pt(fl, fr, ft, dx, dz, 0.6, v + 0.05)], M["ink"])
    lx, lz = _top_pt(fl, fr, ft, dx, dz, 0.86, 0.78)
    G.stroke(d, G.lumpy_ellipse(lx, lz, 0.035, 0.028, n=12, seed=170), M["green_i"], I, cyclic=True)   # the LED
    glint(d, M, lx - 0.008, lz + 0.006, 0.014)
    _box_ink(d, M, fl, fr, fb, ft, dx, dz)


def cryo_pad(d, M):
    _pad(d, M, "sky", "sky_sh", "sky_dp", "teal", "teal_sh")


def thermal_pad(d, M):
    _pad(d, M, "mustard_sh", "mustard_dp", "brown_sh", "red", "red_sh")


def cryo_round(d, M):
    R = (lambda pts: [(x * math.cos(0.7) - z * math.sin(0.7), x * math.sin(0.7) + z * math.cos(0.7)) for x, z in pts])  # 40 deg up-right
    G.stroke(d, R([(-0.36, -0.09), (0.06, -0.09), (0.06, 0.09), (-0.36, 0.09)]), M["mustard"], 0.0, cyclic=True)   # the brass casing
    G.stroke(d, R([(-0.36, -0.09), (0.06, -0.09), (0.06, -0.03), (-0.36, -0.03)]), M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, R([(-0.36, -0.1), (-0.32, -0.1), (-0.32, 0.1), (-0.36, 0.1)]), M["mustard_dp_i"], I, cyclic=True)
    G.stroke(d, R([(0.06, -0.09), (0.12, -0.09), (0.12, 0.09), (0.06, 0.09)]), M["teal_i"], I, cyclic=True)        # the glowing ring
    nose = [(0.12, -0.09), (0.2, -0.09), (0.38, 0.0), (0.2, 0.09), (0.12, 0.09)]
    G.stroke(d, R(nose), M["sky"], 0.0, cyclic=True)
    G.stroke(d, R([(0.12, -0.09), (0.2, -0.09), (0.38, 0.0), (0.12, 0.0)]), M["sky_sh"], 0.0, cyclic=True)
    G.stroke(d, R([(0.2, 0.09), (0.38, 0.0), (0.24, 0.03)]), M["off"], 0.0, cyclic=True)
    G.stroke(d, R([(-0.36, -0.09), (0.12, -0.09), (0.2, -0.09), (0.38, 0.0), (0.2, 0.09), (0.12, 0.09), (-0.36, 0.09)]), M["ink"], O, cyclic=True)
    G.seam(d, R([(0.12, -0.09), (0.12, 0.09)]), M["ink"])
    glint(d, M, *R([(-0.18, 0.05)])[0], 0.02)


def float_cell_mk1(d, M):
    _drum(d, M, "off", "off_sh", "red", "sky_dp")


def float_cell_mk2(d, M):
    _drum(d, M, "sky", "sky_sh", "teal", "sky_dp")


def polymer(d, M):
    top = _cylinder(d, M, "off", "off_sh", "off", x=-0.04, w=0.22, zb=-0.18, zt=0.24)
    G.stroke(d, G.lumpy_ellipse(-0.04, 0.24, 0.07, 0.025, n=14, lump=0.0, seed=180), M["sky_sh_i"], I, cyclic=True)   # the core
    G.stroke(d, [(0.16, 0.02), (0.22, -0.16), (0.3, -0.26), (0.42, -0.3), (0.44, -0.25), (0.33, -0.2), (0.25, -0.1), (0.18, 0.08)],
             M["off_i"], I, cyclic=True)                                                      # the film draped down (rev: a diagonal flap
                                                                                              # read as a magnifier's handle)
    for j, (x, z) in enumerate(((-0.24, -0.3), (0.0, -0.33))):
        G.stroke(d, G.lumpy_ellipse(x, z, 0.05, 0.03, n=12, seed=181 + j), M["mustard_i"], I, cyclic=True)   # amber pellets
    glint(d, M, -0.18, 0.12, 0.024)
    _ = top


def radiation_liner(d, M):
    for i, (dz0, w) in enumerate(((-0.2, 0.36), (-0.1, 0.33), (0.0, 0.3))):                  # stacked lead sheets
        fl, fr, ft = -w, w - 0.12, dz0 + 0.04
        edge = [(fl, dz0), (fr, dz0), (fr + 0.12, dz0 + 0.1), (fr + 0.12, dz0 + 0.14), (fr, ft), (fl, ft)]
        G.stroke(d, edge, M["sky_dp"], 0.0, cyclic=True)
        G.stroke(d, [(fl, ft), (fr, ft), (fr + 0.12, dz0 + 0.14), (fl + 0.12, dz0 + 0.14)], M["sky_sh" if i == 2 else "sky_dp"], 0.0, cyclic=True)
        G.stroke(d, edge + [(fl + 0.12, dz0 + 0.14)], M["ink"], O if i == 0 else I, cyclic=True)
    cx, cz = 0.0, 0.11                                                                        # the trefoil disc on top
    G.stroke(d, G.lumpy_ellipse(cx, cz, 0.13, 0.05, n=20, lump=0.0, seed=190), M["mustard_i"], I, cyclic=True)
    for a in (90, 210, 330):
        t = math.radians(a)
        pts = [(cx, cz)] + [(cx + 0.11 * math.cos(t + s), cz + 0.042 * math.sin(t + s)) for s in (-0.5, -0.25, 0.0, 0.25, 0.5)]
        G.stroke(d, [(cx + 0.03 * math.cos(t - 0.5), cz + 0.012 * math.sin(t - 0.5))] + pts[1:] + [(cx + 0.03 * math.cos(t + 0.5), cz + 0.012 * math.sin(t + 0.5))],
                 M["brown_dp"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(cx, cz, 0.018, 0.008, n=8, lump=0.0, seed=191), M["brown_dp"], 0.0, cyclic=True)


def smelter_bar_copper(d, M):
    _ingot(d, M, "red", "red_sh", "red_dp", "red_dp")


def smelter_bar_iron(d, M):
    _ingot(d, M, "sky_sh", "sky_dp", "brown_dp", "brown_dp")


def solarite_capacitor(d, M):
    _cylinder(d, M, "brown_dp", "brown_dp", "sky_dp", w=0.17, zb=-0.24, zt=0.22)
    G.stroke(d, [(-0.12, -0.12), (0.12, -0.12), (0.12, 0.1), (-0.12, 0.1)], M["mustard"], 0.0, cyclic=True)   # the glowing window
    G.stroke(d, [(-0.06, -0.1), (0.04, -0.1), (0.04, 0.08), (-0.06, 0.08)], M["off"], 0.0, cyclic=True)
    G.stroke(d, [(-0.12, -0.12), (0.12, -0.12), (0.12, 0.1), (-0.12, 0.1)], M["ink"], I, cyclic=True)
    for zc in (-0.2, 0.18):                                                                   # the caps' bands
        G.stroke(d, [(-0.17, zc - 0.03), (0.17, zc - 0.03), (0.17, zc + 0.03), (-0.17, zc + 0.03)], M["sky_dp_i"], I, cyclic=True)
    for x in (-0.08, 0.08):                                                                   # terminals
        G.stroke(d, [(x - 0.025, 0.22), (x + 0.025, 0.22), (x + 0.025, 0.29), (x - 0.025, 0.29)], M["sky_sh_i"], I, cyclic=True)


def suit_patch(d, M):
    fl, fr, fb, ft, dx, dz = _box(d, M, "red", "red_sh", "red_dp", w=0.34, h=0.04, dx=0.2, dz=0.32, cz=-0.12)
    for k in range(14):                                                                       # stitches round the edge
        t = k / 14
        for (u, v) in ((t, 0.08), (t, 0.92), (0.06, t), (0.94, t)):
            if 0.05 < (u if v in (0.08, 0.92) else v) < 0.95 and k % 2 == 0:
                p0 = _top_pt(fl, fr, ft, dx, dz, u, v)
                p1 = _top_pt(fl, fr, ft, dx, dz, u + (0.035 if v in (0.08, 0.92) else 0.0), v + (0.035 if u in (0.06, 0.94) else 0.0))
                G.stroke(d, [p0, p1, (p1[0], p1[1] + 0.008), (p0[0], p0[1] + 0.008)], M["off"], 0.0, cyclic=True)
    _box_ink(d, M, fl, fr, fb, ft, dx, dz)


def survey_module(d, M):
    fl, fr, fb, ft, dx, dz = _box(d, M, "sky", "sky_sh", "sky_dp", w=0.3, h=0.32, dx=0.14, dz=0.1, cz=-0.08)
    G.stroke(d, [(fl + 0.06, fb + 0.06), (fr - 0.08, fb + 0.06), (fr - 0.08, ft - 0.06), (fl + 0.06, ft - 0.06)], M["teal_dp_i"], I, cyclic=True)   # the screen
    for i, w in enumerate((0.22, 0.14, 0.18)):
        z = ft - 0.12 - i * 0.06
        G.stroke(d, [(fl + 0.1, z - 0.012), (fl + 0.1 + w, z - 0.012), (fl + 0.1 + w, z + 0.012), (fl + 0.1, z + 0.012)], M["green"], 0.0, cyclic=True)
    lx, lz = fr + dx * 0.55, (fb + ft) / 2 + dz * 0.5                                         # one lens, on the side face
    G.stroke(d, G.lumpy_ellipse(lx, lz, 0.035, 0.08, n=16, lump=0.0, seed=200), M["brown_dp_i"], I, cyclic=True)
    _box_ink(d, M, fl, fr, fb, ft, dx, dz)
    G.stroke(d, G.hose_outline([(fl + 0.08, ft + 0.04), (fl + 0.08, ft + 0.18)], 0.014), M["sky_dp_i"], I, cyclic=True)   # the antenna
    G.stroke(d, G.lumpy_ellipse(fl + 0.08, ft + 0.2, 0.025, 0.025, n=10, seed=201), M["green_i"], I, cyclic=True)


# ---------------------------------------------------------------- batch 4: gear and the remaining materials

def _tank(d, M, x, w, zb, zt, body, sh, nozzle="sky_dp"):
    """An upright tank with a rounded top and a nozzle under it."""
    top = [(x - w, zt - w)] + [(x + w * math.cos(a), zt - w + w * math.sin(a)) for a in [math.pi - math.pi * i / 10 for i in range(11)]]
    tank = [(x - w, zb)] + top + [(x + w, zb)]
    G.stroke(d, tank, M[body], 0.0, cyclic=True)
    G.stroke(d, [(x + w * 0.35, zb), (x + w * 0.35, zt - w * 0.4), (x + w, zt - w), (x + w, zb)], M[sh], 0.0, cyclic=True)
    G.stroke(d, [(x - w * 0.55, zt - w * 0.9), (x - w * 0.3, zt - w * 0.9), (x - w * 0.3, zb + 0.04), (x - w * 0.55, zb + 0.04)], M["off"], 0.0, cyclic=True)
    G.stroke(d, tank, M["ink"], O, cyclic=True)
    G.stroke(d, [(x - w * 0.7, zb), (x + w * 0.7, zb), (x + w * 0.9, zb - 0.08), (x - w * 0.9, zb - 0.08)], M[nozzle + "_i"], I, cyclic=True)


def _heap(d, M, base, sh, cx, cz, w, h, seed):
    """A heap of powder: a lumpy cone, its shaded right flank, grains."""
    rnd = random.Random(seed)
    pts = [(cx - w, cz)] + [(cx + w * (2 * t - 1), cz + h * (1 - abs(2 * t - 1)) ** 0.8 * (1 + rnd.uniform(-0.06, 0.06))) for t in [i / 14 for i in range(1, 14)]] + [(cx + w, cz)]
    G.stroke(d, pts, M[base], 0.0, cyclic=True)
    G.stroke(d, [p for p in pts if p[0] >= cx] + [(cx + w * 0.1, cz)], M[sh], 0.0, cyclic=True)
    G.stroke(d, pts, M["ink"], O, cyclic=True)
    G.specks(d, [(cx - w * 0.4, cz + h * 0.3), (cx + w * 0.2, cz + h * 0.45), (cx - w * 0.1, cz + h * 0.15)], M["ink"])


def jetpack_mk2(d, M):
    G.stroke(d, [(-0.12, -0.2), (0.28, -0.14), (0.28, 0.24), (-0.12, 0.3)], M["sky_dp_i"], O, cyclic=True)   # the backplate
    for x in (-0.16, 0.06):
        _tank(d, M, x, 0.1, -0.22, 0.34, "red", "red_sh")
    for x in (-0.16, 0.06):                                                                   # a lick of blue under each
        G.stroke(d, [(x - 0.04, -0.31), (x + 0.04, -0.31), (x, -0.4)], M["teal"], 0.0, cyclic=True)


def jetpack_mk3(d, M):
    for x in (-0.2, 0.0, 0.2):
        _tank(d, M, x, 0.085, -0.22, 0.34, "sky_dp", "brown_dp", nozzle="brown_dp")
    for x in (-0.2, 0.0, 0.2):
        G.stroke(d, [(x - 0.045, -0.31), (x + 0.045, -0.31), (x, -0.42)], M["teal"], 0.0, cyclic=True)


def skip_drive_mk2(d, M):
    """Neptune's palette: the violet core (its 'mustard' slot) in a dark ring on four spokes."""
    outer = G.lumpy_ellipse(0.0, 0.0, 0.36, 0.36, n=36, lump=0.0, seed=220)
    inner = G.lumpy_ellipse(0.0, 0.0, 0.25, 0.25, n=36, lump=0.0, seed=221)
    G.stroke(d, outer, M["sky_dp"], 0.0, cyclic=True)
    G.stroke(d, [q for q in outer if q[0] + q[1] < 0.0] + [(-0.25, 0.25)], M["sky_sh"], 0.0, cyclic=True)
    G.stroke(d, inner, M["brown_dp"], 0.0, cyclic=True)
    for a in (45, 135, 225, 315):
        t = math.radians(a)
        G.stroke(d, G.hose_outline([(0.1 * math.cos(t), 0.1 * math.sin(t)), (0.25 * math.cos(t), 0.25 * math.sin(t))], 0.035), M["sky_sh_i"], I, cyclic=True)
    core = G.lumpy_ellipse(0.0, 0.0, 0.12, 0.12, n=20, lump=0.0, seed=222)
    G.stroke(d, core, M["mustard"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.025, -0.025, 0.08, 0.08, n=16, lump=0.0, seed=223), M["mustard_sh"], 0.0, cyclic=True)
    G.stroke(d, core, M["ink"], I, cyclic=True)
    G.stroke(d, outer, M["ink"], O, cyclic=True)
    G.stroke(d, inner, M["ink"], I, cyclic=True)
    glint(d, M, -0.04, 0.04, 0.025)


def thruster_mk3(d, M):
    cone = [(-0.12, 0.14), (0.12, 0.14), (0.3, -0.28), (-0.3, -0.28)]
    G.stroke(d, G.lumpy_ellipse(0.0, -0.28, 0.3, 0.07, n=24, lump=0.0, seed=230), M["brown_dp"], 0.0, cyclic=True)   # the bell's mouth
    G.stroke(d, cone, M["sky_dp"], 0.0, cyclic=True)
    G.stroke(d, [(0.03, 0.14), (0.12, 0.14), (0.3, -0.28), (0.1, -0.28)], M["brown_dp"], 0.0, cyclic=True)
    G.stroke(d, [(-0.07, 0.1), (-0.03, 0.1), (-0.14, -0.22), (-0.2, -0.22)], M["sky_sh"], 0.0, cyclic=True)
    G.stroke(d, cone, M["ink"], O, cyclic=True)
    G.stroke(d, [(-0.14, 0.14), (0.14, 0.14), (0.14, 0.19), (-0.14, 0.19)], M["red_i"], I, cyclic=True)   # the orange collar
    G.stroke(d, [(-0.11, 0.19), (0.11, 0.19), (0.09, 0.32), (-0.09, 0.32)], M["sky_dp_i"], O, cyclic=True)


def basalt(d, M):
    for x, zt, w in ((-0.14, 0.3, 0.12), (0.12, 0.18, 0.12), (-0.02, 0.06, 0.1)):            # hexagonal columns
        G.stroke(d, [(x - w, -0.3), (x + w, -0.3), (x + w, zt), (x - w, zt)], M["sky_dp"], 0.0, cyclic=True)
        G.stroke(d, [(x + w * 0.2, -0.3), (x + w, -0.3), (x + w, zt), (x + w * 0.2, zt)], M["brown_dp"], 0.0, cyclic=True)
        top = [(x - w, zt), (x - w * 0.5, zt + 0.04), (x + w * 0.5, zt + 0.04), (x + w, zt), (x + w * 0.5, zt - 0.03), (x - w * 0.5, zt - 0.03)]
        G.stroke(d, top, M["sky_sh"], 0.0, cyclic=True)
        G.seam(d, [(x + w * 0.2, -0.3), (x + w * 0.2, zt - 0.03)], M["ink"])
        G.stroke(d, [(x - w, -0.3), (x + w, -0.3), (x + w, zt), (x + w * 0.5, zt + 0.04), (x - w * 0.5, zt + 0.04), (x - w, zt)], M["ink"], O, cyclic=True)


def clay(d, M):
    pts = lump(0.0, -0.06, 0.34, 0.24, 240, n=10, jit=0.1)                                   # a squat, pinched ball (never an egg)
    pts = [(x, max(z, -0.26)) for x, z in pts]
    G.stroke(d, pts, M["red_sh"], 0.0, cyclic=True)
    G.stroke(d, [q for q in pts if q[0] - q[1] > 0.12] + [(0.1, -0.12)], M["red_dp"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.04, 0.04, 0.08, 0.05, n=14, lump=0.05, seed=241), M["red_dp"], 0.0, cyclic=True)   # a thumb dent
    G.seam(d, [(-0.04, 0.0), (0.04, 0.0), (0.12, 0.03)], M["ink"])
    G.stroke(d, pts, M["ink"], O, cyclic=True)
    glint(d, M, -0.18, 0.06, 0.022)


def perchlorate(d, M):
    for cx, cz, s in ((-0.1, -0.14, 0.15), (0.12, -0.08, 0.13), (0.0, 0.1, 0.12)):          # a cluster of pale cubes
        fl, fr, fb, ft = cx - s, cx + s * 0.6, cz - s, cz + s * 0.6
        dx, dz = s * 0.5, s * 0.4
        for poly, m in (([(fl, fb), (fr, fb), (fr, ft), (fl, ft)], "off_sh"), ([(fr, fb), (fr + dx, fb + dz), (fr + dx, ft + dz), (fr, ft)], "mustard_dp"),
                        ([(fl, ft), (fr, ft), (fr + dx, ft + dz), (fl + dx, ft + dz)], "off")):
            G.stroke(d, poly, M[m], 0.0, cyclic=True)
        _box_ink(d, M, fl, fr, fb, ft, dx, dz)
    glint(d, M, -0.02, 0.2, 0.022)


def phosphorus_pigment(d, M):
    dish = G.lumpy_ellipse(0.0, -0.22, 0.38, 0.1, n=28, lump=0.0, seed=250)
    G.stroke(d, dish, M["sky_dp_i"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, -0.2, 0.3, 0.07, n=24, lump=0.0, seed=251), M["sky_sh"], 0.0, cyclic=True)
    _heap(d, M, "red", "red_sh", 0.0, -0.21, 0.24, 0.26, 252)


def sand(d, M):
    _heap(d, M, "mustard", "mustard_sh", 0.0, -0.24, 0.36, 0.38, 260)


def stone(d, M):
    pts = lump(0.0, -0.08, 0.36, 0.22, 270, n=10, jit=0.08)                                  # a flat pebble (wider than tall: not an egg)
    faceted(d, M, pts, "sky_sh", "sky", "sky_dp", 0.0, -0.08, seams=False)
    G.seam(d, [(-0.12, 0.04), (-0.05, -0.04), (-0.08, -0.14)], M["ink"])
    G.specks(d, [(0.1, -0.02), (0.18, -0.12), (-0.2, -0.1)], M["ink"])
    glint(d, M, -0.16, 0.04, 0.022)


def sulfur(d, M):
    pts = lump(0.0, -0.02, 0.33, 0.33, 280, n=9, jit=0.14)
    faceted(d, M, pts, "mustard", "off", "mustard_sh", 0.0, -0.02)
    glint(d, M, -0.12, 0.15)


def vitriol_glass(d, M):
    T, Bm, L, R, F = (0.04, 0.36), (-0.02, -0.36), (-0.28, 0.06), (0.28, -0.04), (0.04, 0.0)  # a lime gem, tilted
    for tri, mat in (((T, L, F), "green"), ((T, F, R), "green_sh"), ((L, F, Bm), "green_sh"), ((F, R, Bm), "green_dp")):
        G.stroke(d, list(tri), M[mat], 0.0, cyclic=True)
    for a, b in ((T, F), (L, F), (F, R), (F, Bm)):
        G.seam(d, [a, b], M["ink"])
    G.stroke(d, [T, R, Bm, L], M["ink"], O, cyclic=True)
    glint(d, M, -0.08, 0.14, 0.028)


def deep_diamond_tip(d, M):
    shank = [(-0.08, -0.36), (0.08, -0.36), (0.08, -0.04), (-0.08, -0.04)]
    G.stroke(d, shank, M["sky_dp"], 0.0, cyclic=True)
    G.stroke(d, [(0.02, -0.36), (0.08, -0.36), (0.08, -0.04), (0.02, -0.04)], M["brown_dp"], 0.0, cyclic=True)
    G.stroke(d, shank, M["ink"], O, cyclic=True)
    G.stroke(d, [(-0.16, -0.06), (0.16, -0.06), (0.16, 0.0), (-0.16, 0.0)], M["sky_sh_i"], I, cyclic=True)   # the collar
    cone = [(-0.16, 0.0), (0.16, 0.0), (0.0, 0.38)]
    G.stroke(d, cone, M["sky"], 0.0, cyclic=True)
    G.stroke(d, [(0.0, 0.0), (0.16, 0.0), (0.0, 0.38)], M["sky_sh"], 0.0, cyclic=True)
    G.stroke(d, [(-0.1, 0.02), (-0.05, 0.02), (0.0, 0.3)], M["off"], 0.0, cyclic=True)
    G.stroke(d, cone, M["ink"], O, cyclic=True)


def deep_core_sample(d, M):
    w, zb, zt = 0.16, -0.32, 0.3
    bands = [(-0.32, -0.18, "brown_dp"), (-0.18, -0.06, "mustard_sh"), (-0.06, 0.04, "brown_sh"), (0.04, 0.16, "mustard_dp"), (0.16, 0.3, "brown_dp")]
    for z0, z1, m in bands:                                                                   # the strata in the core
        G.stroke(d, [(-w, z0), (w, z0), (w, z1), (-w, z1)], M[m], 0.0, cyclic=True)
        G.seam(d, [(-w, z0), (w, z0)], M["ink"])
    G.stroke(d, [(w * 0.4, zb), (w, zb), (w, zt), (w * 0.4, zt)], M["brown_dp"], 0.0, cyclic=True)
    top = G.lumpy_ellipse(0.0, zt, w, w * 0.32, n=20, lump=0.0, seed=290)
    G.stroke(d, top, M["sky_sh"], 0.0, cyclic=True)
    G.stroke(d, [(-w, zt), (-w, zb), (w, zb), (w, zt)], M["ink"], O)
    G.stroke(d, top, M["ink"], O, cyclic=True)


def ring_rock(d, M):
    pts = lump(0.0, -0.02, 0.33, 0.31, 300, n=13, jit=0.1)
    faceted(d, M, pts, "brown_sh", "mustard_sh", "brown_dp", 0.0, -0.02, seams=False)
    for j, (x, z, r) in enumerate(((-0.14, 0.1, 0.04), (0.06, -0.12, 0.05), (0.18, -0.02, 0.03), (-0.04, -0.2, 0.035))):   # pocks (one high:
                                                                                              # two side by side up top read as eyes)
        G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.8, n=10, seed=301 + j), M["brown_dp"], 0.0, cyclic=True)
        G.seam(d, [(x - r, z + r * 0.4), (x + r * 0.6, z + r * 0.8)], M["ink"])
    G.specks(d, [(0.0, 0.18), (-0.22, -0.04), (0.22, -0.02)], M["ink"])


def living_seed(d, M):
    seed = G.lumpy_ellipse(0.0, -0.1, 0.24, 0.2, n=24, lump=0.03, seed=310)
    G.stroke(d, seed, M["brown_sh"], 0.0, cyclic=True)
    G.stroke(d, [q for q in seed if q[0] - (q[1] + 0.1) > 0.08] + [(0.06, -0.14)], M["brown_dp"], 0.0, cyclic=True)
    G.seam(d, [(-0.04, 0.08), (0.0, -0.1), (-0.02, -0.26)], M["ink"])
    G.stroke(d, seed, M["ink"], O, cyclic=True)
    G.stroke(d, G.hose_outline(G.bezier((0.0, 0.09), (0.0, 0.2), (0.06, 0.28), (0.14, 0.3), n=8), 0.022), M["green_i"], I, cyclic=True)   # the sprout
    leaf = [(0.12, 0.3), (0.2, 0.38), (0.34, 0.36), (0.28, 0.28)]
    G.stroke(d, leaf, M["green_i"], I, cyclic=True)
    G.seam(d, [(0.14, 0.31), (0.3, 0.33)], M["ink"])
    glint(d, M, -0.12, -0.02, 0.022)


def wood(d, M):
    L, R, H = -0.32, 0.18, 0.2                                                                # a log lying on its side, its cut end right
    G.stroke(d, [(L, -H), (R, -H), (R, H), (L, H)], M["brown_sh"], 0.0, cyclic=True)
    G.stroke(d, [(L, -H), (R, -H), (R, -H * 0.3), (L, -H * 0.3)], M["brown_dp"], 0.0, cyclic=True)
    for z in (-0.1, 0.02, 0.12):                                                              # bark grain
        G.seam(d, [(L + 0.05, z), (L + 0.2, z + 0.01), (R - 0.12, z - 0.005)], M["ink"])
    end = G.lumpy_ellipse(R, 0.0, 0.1, H, n=24, lump=0.0, seed=320)
    G.stroke(d, end, M["mustard_sh"], 0.0, cyclic=True)
    for k in (0.65, 0.35):                                                                    # the rings
        G.stroke(d, G.lumpy_ellipse(R + 0.005, 0.0, 0.1 * k, H * k, n=20, lump=0.0, seed=321), M["ink"], I, cyclic=True)
    G.stroke(d, [(L, -H), (R, -H)], M["ink"], O)
    G.stroke(d, [(L, H), (R, H)], M["ink"], O)
    G.stroke(d, [(L, -H), (L - 0.03, 0.0), (L, H)], M["ink"], O)
    G.stroke(d, end, M["ink"], O, cyclic=True)


ITEMS = {"iron": iron, "copper": copper, "nickel": nickel, "aluminium": aluminium, "carbon": carbon, "graphite": graphite,
         "hematite": hematite, "silica": silica, "solarite": solarite, "deep_diamond": deep_diamond,
         "water_ice": water_ice, "methane_ice": methane_ice, "polar_ice": polar_ice, "ring_ice": ring_ice,
         "superionic_ice": superionic_ice, "ammonia_ice": ammonia_ice, "helium3_condensate": helium3_condensate,
         "metallic_hydrogen": metallic_hydrogen, "oxygen": oxygen,
         "circuit_board": circuit_board, "cryo_pad": cryo_pad, "thermal_pad": thermal_pad, "cryo_round": cryo_round,
         "float_cell_mk1": float_cell_mk1, "float_cell_mk2": float_cell_mk2, "polymer": polymer, "radiation_liner": radiation_liner,
         "smelter_bar_copper": smelter_bar_copper, "smelter_bar_iron": smelter_bar_iron, "solarite_capacitor": solarite_capacitor,
         "suit_patch": suit_patch, "survey_module": survey_module,
         "jetpack_mk2": jetpack_mk2, "jetpack_mk3": jetpack_mk3, "skip_drive_mk2": skip_drive_mk2, "thruster_mk3": thruster_mk3,
         "basalt": basalt, "clay": clay, "perchlorate": perchlorate, "phosphorus_pigment": phosphorus_pigment, "sand": sand,
         "stone": stone, "sulfur": sulfur, "vitriol_glass": vitriol_glass, "deep_diamond_tip": deep_diamond_tip,
         "deep_core_sample": deep_core_sample, "ring_rock": ring_rock, "living_seed": living_seed, "wood": wood}
BATCHES = {1: ["iron", "copper", "nickel", "aluminium", "carbon", "graphite", "hematite", "silica", "solarite", "deep_diamond"],
           2: ["water_ice", "methane_ice", "polar_ice", "ring_ice", "superionic_ice", "ammonia_ice", "helium3_condensate",
               "metallic_hydrogen", "oxygen"],
           3: ["circuit_board", "cryo_pad", "thermal_pad", "float_cell_mk1", "float_cell_mk2", "polymer",   # cryo_round retired
                                                                                              # (D-173: Veil Serpent ammo, combat cancelled D-087)
               "radiation_liner", "smelter_bar_copper", "smelter_bar_iron", "solarite_capacitor", "suit_patch", "survey_module"],
           4: ["jetpack_mk2", "jetpack_mk3", "skip_drive_mk2", "thruster_mk3", "basalt", "clay", "perchlorate", "phosphorus_pigment",
               "sand", "stone", "sulfur", "vitriol_glass", "deep_diamond_tip", "deep_core_sample", "ring_rock", "living_seed", "wood"]}
EXPORT_BATCHES = (1, 2, 3)                                                                    # only LEAD-accepted batches export
ITEM_PLANET = {"superionic_ice": "neptune", "skip_drive_mk2": "neptune",                      # the violet is Neptune's (its 'mustard' slot)
               "helium3_condensate": "saturn"}                                                # LEAD 15:3x: its source planet; Saturn's red is
                                                                                              # the dusty rose nearest the v2 pink (Earth's coral
                                                                                              # read as a fire extinguisher)
PROPS = {n: (ITEMS[n], SIZE, SIZE, None, 1, False) for b in EXPORT_BATCHES for n in BATCHES[b]}   # do_prop_sheet_set's API


def render_item(name):
    gp = fakegp.FakeGP()
    M = mats(gp, ITEM_PLANET.get(name, "earth"))
    d = fakegp.FakeDrawing()
    ITEMS[name](d, M)
    return GR.render_frame(fakegp.strokes_of(d, gp), SIZE, SIZE, PPU, (0.5, 0.5), ss=4, seed=7)


def render_all(names=None):
    imgs, widths = {}, {}
    for n in (names or list(PROPS)):
        img, w = render_item(n)
        imgs[n], widths[n] = [img], w
    return imgs, widths


def checks(img, name=""):
    m = v3.EDGE_MARGIN
    a = img[..., 3]
    p = []
    if a[:m].any() or a[-m:].any() or a[:, :m].any() or a[:, -m:].any():
        p.append(f"touches the {m} px edge")
    hit, off = v3.palette_hits(img, ITEM_PLANET.get(name, "earth"))
    if hit < 0.98:
        p.append(f"palette {hit * 100:.1f}% (off {' '.join(off[:3])})")
    return p, hit


def export(art, imgs=None, names=None):
    import json
    from meridian import pngio
    names = list(names or PROPS)                                                              # the accepted batches only
    if imgs is None:
        imgs, _w = render_all(names)
    problems = []
    for n in names:
        p, _h = checks(imgs[n][0], n)
        problems += [f"{n}: {x}" for x in p]
    if problems:
        raise ValueError("B-199 export checks: " + "; ".join(problems))
    out = []
    for n in names:
        dd = os.path.join(art, "icons", n)
        b = pngio.write_png(os.path.join(dd, "base_color.png"), imgs[n][0])
        with open(os.path.join(dd, "base.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"key": KEY.format(n), "style": "v3", "ppu": PPU, "pivot": [0.5, 0.5], "icon": True,
                       "note": "B-199: re-inked as v3 (replacing the v2 shaded render)"}, f, indent=2)
            f.write("\n")
        out.append((KEY.format(n), SIZE, SIZE, b))
    return out, {}, []


def main(out, imgs=None, widths=None, stamp_paths=(), batch=None):
    """Each new icon over its v2 render (read from Art before the export; after it, the exported one) at 1x, both again at
    the 32 px slot, and the v3 icons already in for the house look. batch: the design preview of that batch (default the
    last); the export passes its own imgs (the accepted batches)."""
    import time
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    if imgs is None:
        batch = batch or max(BATCHES)
        imgs, widths = render_all(BATCHES[batch])
    label = f"batch {batch}" if batch else "batches " + ", ".join(str(b) for b in EXPORT_BATCHES)
    ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art")
    paper = np.array(review.PAPER, np.float32)
    names = list(imgs)
    W = 8 + len(names) * 140
    old = {}
    for n in names:
        p = os.path.join(ART, "icons", n, "base_color.png")
        old[n] = pngio.read_png_np(p) if os.path.isfile(p) else None

    def small(ic):
        f = ic.shape[0] // 32
        return ic.reshape(32, f, 32, f, 4).astype(np.float32).mean(axis=(1, 3)).astype(np.uint8)

    def row(title, items, h):
        r = np.empty((h, W, 3), np.float32)
        r[:] = paper
        review._label(r, title, 8, 4, scale=1)
        for i, (lab, ic) in enumerate(items):
            x = 8 + i * 140
            if ic is None:
                continue
            r[20:20 + ic.shape[0], x:x + ic.shape[1]] = paper * 0.9
            review._over(r, ic, x, 20)
            if lab:
                review._label(r, lab, x, 20 + ic.shape[0] + 4, scale=1)
        return r
    rows = [row(f"B-199 {label}, NEW v3 (1x)", [(n, imgs[n][0]) for n in names], 168),
            row("the same at the 32 px slot", [("", small(imgs[n][0])) for n in names], 60),
            row("before: the v2 render in Art" + (" (now replaced)" if stamp_paths else "") + " (1x)", [(n, old[n] if not stamp_paths else None) for n in names], 168),
            row("before at 32 px", [("", small(old[n]) if old[n] is not None and not stamp_paths else None) for n in names], 60)]
    ref = []
    for n in ("soil", "tessera", "sulfide", "wind_anchor"):
        p = os.path.join(ART, "icons", n, "base_color.png")
        if os.path.isfile(p):
            ref.append((n, pngio.read_png_np(p)))
    rows.append(row("the v3 icons already in (B-128's cubes 64 px, B-197's wind_anchor), 1x", ref, 168))
    lines = []
    for n in names:
        p, hit = checks(imgs[n][0], n)
        lines.append(f"icons/{n}/base: palette {hit * 100:.1f}% ({ITEM_PLANET.get(n, 'earth')}), problems: {'; '.join(p) or 'none'}")
    for p in stamp_paths:
        lines.append("exported " + review.stamp_text(p))
    foot = np.empty((30 + 16 * len(lines), W, 3), np.float32)
    foot[:] = paper
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
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


if __name__ == "__main__":                       # python -I build_icons_items_v3.py <review png> [batch]
    main(sys.argv[1], batch=int(sys.argv[2]) if len(sys.argv) > 2 else None)
    fakegp.restore()
