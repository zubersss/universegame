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
    pts = G.lumpy_ellipse(0.0, -0.02, 0.3, 0.33, n=24, lump=0.05, seed=111)
    G.stroke(d, pts, M["off"], 0.0, cyclic=True)
    G.stroke(d, [q for q in pts if q[0] + q[1] * 0.7 > 0.05] + [(0.06, -0.08)], M["sky"], 0.0, cyclic=True)
    G.specks(d, [(-0.1, -0.12), (0.06, 0.12), (0.14, -0.18), (-0.18, 0.06)], M["ink"])
    G.stroke(d, pts, M["ink"], O, cyclic=True)
    glint(d, M, -0.12, 0.14)


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
        prism(d, M, x0, x1, -0.24, tip, "off", "green_sh", lean)                              # frosty, faintly green shards fanning out
    glint(d, M, -0.12, 0.2, 0.025)


def helium3_condensate(d, M):
    body = [(-0.17, -0.26), (0.17, -0.26), (0.19, -0.2), (0.19, 0.18), (0.17, 0.24), (-0.17, 0.24), (-0.19, 0.18), (-0.19, -0.2)]
    G.stroke(d, body, M["red_sh"], 0.0, cyclic=True)                                          # the pink condensate behind glass
    G.stroke(d, [(0.06, -0.24), (0.17, -0.24), (0.17, 0.22), (0.06, 0.22)], M["red_dp"], 0.0, cyclic=True)
    G.stroke(d, [(-0.12, -0.18), (-0.07, -0.18), (-0.07, 0.16), (-0.12, 0.16)], M["red"], 0.0, cyclic=True)
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


ITEMS = {"iron": iron, "copper": copper, "nickel": nickel, "aluminium": aluminium, "carbon": carbon, "graphite": graphite,
         "hematite": hematite, "silica": silica, "solarite": solarite, "deep_diamond": deep_diamond,
         "water_ice": water_ice, "methane_ice": methane_ice, "polar_ice": polar_ice, "ring_ice": ring_ice,
         "superionic_ice": superionic_ice, "ammonia_ice": ammonia_ice, "helium3_condensate": helium3_condensate,
         "metallic_hydrogen": metallic_hydrogen, "oxygen": oxygen}
BATCHES = {1: ["iron", "copper", "nickel", "aluminium", "carbon", "graphite", "hematite", "silica", "solarite", "deep_diamond"],
           2: ["water_ice", "methane_ice", "polar_ice", "ring_ice", "superionic_ice", "ammonia_ice", "helium3_condensate",
               "metallic_hydrogen", "oxygen"]}
EXPORT_BATCHES = (1,)                                                                         # only LEAD-accepted batches export
ITEM_PLANET = {"superionic_ice": "neptune"}                                                   # its violet is Neptune's
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
