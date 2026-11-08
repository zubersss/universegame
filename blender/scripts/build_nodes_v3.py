"""B-176 (D-161 (3), D-162 (5); LEAD D-164: Earth first, ahead of UNITY's U-158 key list; the keys are renamed at export):
mining by resource nodes and buried finds, drawn with gp_draw (fakegp + numpy), the planet's palette tones only, no faces.

  node_<item>      128x96, pivot at the base (upright on the curve): full 1, harvested 1 (chipped, smaller), glint 8 (a star
                   sparkle sweeping over the ore); Earth: iron, copper, carbon, silica, water_ice (the trade list)
  pocket_<item>    96x96, pivot at the centre: a rounded cavity set into ground_fill's cutaway holding the same ore; full 1,
                   glint 8 (the Survey scan's reveal)
  data_cache       96x80, pivot at the centre: a half-buried Meridian data cache (brass box, the meridian emblem); full 1,
                   glint 8 (its lamp blinking)
  vault_door       128x128, pivot at the centre: a round Warden vault door set into the cross-section (offwhite stone, teal
                   inset panels, a hum ring); closed 1, open 6 (it rolls aside, the dark doorway behind)
  scan_x           64x64, pivot at the base: the Survey scan's X painted on the ground above a find; pulse 8 (loop)

  python -I build_nodes_v3.py <preview dir> [planet]   lock-free design preview: review_b176_<planet>_nodes_preview.png
                                                       (the nodes on Earth's B-175 ground at 1x beside the surveyor, the
                                                       pockets / cache / vault door in the cutaway, the X over a pocket; every
                                                       clip as a strip; the per-key checks)
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp, v3  # noqa: E402

try:
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
TAU = 2 * math.pi
ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))


def colours(planet):
    P = v3.PALETTES[planet]
    sh = lambda k: v3.shadow_of(P[k], planet)  # noqa: E731
    dp = lambda k: v3.deep_of(P[k], planet)  # noqa: E731
    if planet == "earth":
        return {"rock": sh("sky"), "rock_sh": dp("sky"), "rock_hi": P["sky"], "iron": P["red"], "iron_sh": sh("red"),
                "malachite": P["teal"], "malachite_sh": sh("teal"), "copper": P["mustard"], "copper_sh": sh("mustard"),
                "coal": P["brown"], "coal_hi": dp("sky"), "sandrock": sh("mustard"), "sandrock_sh": dp("mustard"),
                "crystal": P["offwhite"], "crystal_sh": sh("offwhite"), "crystal_tint": P["sky"],
                "ice": P["offwhite"], "ice_sh": P["sky"], "ice_dp": P["teal"],
                "soil": dp("mustard"), "cavity": P["brown"], "cavity_sh": dp("red"),
                "brass": P["mustard"], "brass_sh": sh("mustard"), "panel": P["teal"], "stone": P["offwhite"], "stone_sh": sh("offwhite"),
                "lamp": P["red"], "lamp_on": P["offwhite"], "xred": P["red"], "xred_sh": sh("red"), "glint": P["offwhite"],
                "dark": P["brown"]}
    raise ValueError(f"B-176: {planet}'s nodes come after Earth's preview")


def mats(gp, planet):
    C = colours(planet)
    M = {"ink": G.mat(gp, f"nd_{planet}_ink", fill=None, ink=True)}
    for k, h in C.items():
        M[k] = G.mat(gp, f"nd_{planet}_{k}", fill=h, ink=False)
        M[k + "_i"] = G.mat(gp, f"nd_{planet}_{k}_i", fill=h)
    return M


def _poly(cx, cz, r, rnd, sides=7, flat=0.8, lift=0.0):
    a0 = rnd.uniform(0, TAU)
    return [(cx + r * rnd.uniform(0.75, 1.0) * math.cos(a0 + TAU * i / sides),
             max(cz + r * flat * rnd.uniform(0.75, 1.0) * math.sin(a0 + TAU * i / sides), lift)) for i in range(sides)]


def star(d, M, x, z, s):
    """A four-point sparkle (the glint)."""
    if s < 0.01:
        return
    pts = [(x - s, z), (x - s * 0.22, z + s * 0.22), (x, z + s), (x + s * 0.22, z + s * 0.22), (x + s, z), (x + s * 0.22, z - s * 0.22),
           (x, z - s), (x - s * 0.22, z - s * 0.22)]
    G.stroke(d, pts, M["glint_i"], I, cyclic=True)


def glint_at(k, spots):
    """Frame k of 8: the sparkle sweeps over the ore spots, one at a time, swelling and fading on twos."""
    if not spots:
        return None
    i = (k // 2) % len(spots)
    s = (0.05, 0.10, 0.10, 0.05)[k % 4] if k % 2 == 0 else (0.08, 0.12, 0.12, 0.08)[k % 4]
    return spots[i][0], spots[i][1], s


# ---------------------------------------------------------------- the rock mound every outcrop sits in

def mound(d, M, w, h, seed, mat="rock"):
    """A rounded half-buried rock mound (the base of an outcrop): lit from the upper right, the lower-left shaded."""
    xs = [-w + 2 * w * i / 30 for i in range(31)]
    top = [(x, h * (1 - (x / w) ** 2) ** 0.7 + 0.03 * math.sin(7 * x + seed)) for x in xs]
    outline = top + [(w, -0.02), (-w, -0.02)]
    G.stroke(d, outline, M[mat], 0.0, cyclic=True)
    G.stroke(d, [(x, z * 0.55) for x, z in top if x < 0.2 * w] + [(0.2 * w, -0.02), (-w, -0.02)], M[mat + "_sh"], 0.0, cyclic=True)
    G.stroke(d, top, M["ink"], O)
    G.seam(d, [(-w * 0.45, h * 0.55), (-w * 0.15, h * 0.3), (w * 0.05, h * 0.42)], M["ink"])
    G.hatch(d, -w * 0.6, h * 0.25, M["ink"], n=3, length=0.07, spacing=0.025, angle_deg=60, seed=seed)
    return top


def crag(d, M, w, h, seed, mat="rock"):
    """A tall craggy outcrop (B-176 revision, LEAD 04:5x: a node reads as harvestable, 1.2-1.5 m): steep sides, a lumpy
    crown, lit from the upper right, cracks; -> the crown's height function."""
    rnd = random.Random(seed)
    bumps = [(rnd.uniform(-0.6, 0.6) * w, rnd.uniform(0.04, 0.09) * h, rnd.uniform(0.18, 0.30) * w) for _ in range(3)]

    def top_z(x):
        base = h * max(0.0, 1 - (abs(x) / w) ** 2.4) ** 0.55
        return base + sum(a * math.exp(-((x - c) / s) ** 2) for c, a, s in bumps) * (base / h)
    xs = [-w + 2 * w * i / 40 for i in range(41)]
    top = [(x, top_z(x)) for x in xs]
    G.stroke(d, top + [(w, -0.02), (-w, -0.02)], M[mat], 0.0, cyclic=True)
    G.stroke(d, [(x, z * 0.8) for x, z in top if x < -0.05 * w] + [(-0.05 * w, -0.02), (-w, -0.02)], M[mat + "_sh"], 0.0, cyclic=True)
    G.stroke(d, top, M["ink"], O)
    for j in range(3):                                                                       # cracks down the face
        x0 = (-0.5 + 0.5 * j) * w + rnd.uniform(-0.05, 0.05)
        z0 = top_z(x0) * 0.9
        G.seam(d, [(x0, z0), (x0 + 0.04, z0 * 0.7), (x0 - 0.02, z0 * 0.45), (x0 + 0.03, z0 * 0.25)], M["ink"])
    G.hatch(d, -w * 0.6, h * 0.3, M["ink"], n=3, length=0.09, spacing=0.03, angle_deg=60, seed=seed)
    return top_z


def _chunk(d, M, x, z, r, rnd, fill, shade, hi):
    pts = _poly(x, z, r, rnd, sides=6, flat=0.85, lift=-9.0)
    G.stroke(d, pts, M[fill], 0.0, cyclic=True)
    G.stroke(d, [pts[2], pts[3], pts[4], (x, z)], M[shade], 0.0, cyclic=True)
    G.stroke(d, [pts[0], pts[1], (x + r * 0.15, z + r * 0.1)], M[hi], 0.0, cyclic=True)
    G.stroke(d, pts, M["ink"], I if r < 0.1 else O, cyclic=True)
    G.seam(d, [(x, z), pts[1]], M["ink"])


def node_iron(d, M, state, k=0):
    """Big rust ore faces on a tall grey crag; harvested: a stump with chip marks and one small lump."""
    rnd = random.Random(21)
    full = state != "harvested"
    w, h = (0.84, 1.10) if full else (0.70, 0.55)
    top_z = crag(d, M, w, h, 11)
    spots = []
    chunks = [(-0.42, 0.45, 0.20), (0.10, 0.80, 0.22), (0.45, 0.42, 0.18), (-0.15, 0.30, 0.16), (-0.30, 0.85, 0.15), (0.30, 0.95, 0.14)] \
        if full else [(-0.15, 0.22, 0.12)]
    for x, z, r in chunks:
        z = min(z, top_z(x) - r * 0.6)
        _chunk(d, M, x, z, r, rnd, "iron", "iron_sh", "rock_hi")
        spots.append((x + r * 0.35, z + r * 0.35))
    if not full:
        for x in (-0.4, 0.1, 0.4):
            G.seam(d, [(x - 0.07, top_z(x) - 0.04), (x, top_z(x) - 0.12), (x + 0.07, top_z(x) - 0.04)], M["ink"])
    return spots


def node_copper(d, M, state, k=0):
    """A tall crag with banded malachite patches and copper nuggets; harvested: a stump with one patch."""
    rnd = random.Random(22)
    full = state != "harvested"
    w, h = (0.82, 1.18) if full else (0.68, 0.52)
    top_z = crag(d, M, w, h, 12)
    spots = []
    patches = [(-0.38, 0.40, 0.22), (0.30, 0.55, 0.24), (-0.05, 0.88, 0.20), (0.05, 0.25, 0.16)] if full else [(0.0, 0.22, 0.16)]
    for j, (x, z, r) in enumerate(patches):
        z = min(z, top_z(x) - r * 0.55)
        G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.68, n=18, lump=0.12, seed=30 + j), M["malachite_i"], O, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x - r * 0.25, z - r * 0.2, r * 0.55, r * 0.35, n=12, lump=0.08, seed=40 + j), M["malachite_sh"], 0.0, cyclic=True)
        for b in range(4):                                                                   # the malachite's banding
            G.seam(d, G.bezier((x - r * 0.75, z - r * 0.25 + 0.035 * b), (x, z + r * 0.12 + 0.035 * b), (x + r * 0.75, z - r * 0.2 + 0.035 * b), n=7),
                   M["ink"])
        for n_ in range(2 if full else 1):                                                   # copper nuggets
            nx, nz = x + r * (0.55 - 1.1 * n_), z + r * (0.45 - 0.2 * n_)
            _chunk(d, M, nx, nz, r * 0.38, rnd, "copper", "copper_sh", "crystal")
            spots.append((nx + 0.03, nz + 0.03))
    return spots


def node_carbon(d, M, state, k=0):
    """A tall sandstone block with a thick black coal seam and black lumps on top; harvested: low, the seam cut back."""
    rnd = random.Random(23)
    full = state != "harvested"
    w, h = (0.86, 0.98) if full else (0.74, 0.50)
    top_z = crag(d, M, w, h, 13, mat="sandrock")
    zc, th = h * 0.48, (0.13 if full else 0.07)
    xs = [-w * 0.95 + 1.9 * w * i / 30 for i in range(31)]
    upper = [(x, min(zc + th + 0.03 * math.sin(5 * x), top_z(x) - 0.03)) for x in xs]
    lower = [(x, min(zc - th + 0.03 * math.sin(4 * x + 1), top_z(x) - 0.05)) for x in xs]
    G.stroke(d, upper + lower[::-1], M["coal"], 0.0, cyclic=True)
    G.stroke(d, upper, M["ink"], O)
    G.stroke(d, lower, M["ink"], O)
    spots = []
    for x in (-0.45, 0.0, 0.42):                                                             # the coal's sheen
        G.stroke(d, G.lumpy_ellipse(x, zc + th * 0.3, 0.06, 0.022, n=8, lump=0.0), M["coal_hi"], 0.0, cyclic=True)
        spots.append((x, zc + th * 0.3))
    if full:                                                                                 # black lumps on top
        for x, r in ((-0.18, 0.13), (0.22, 0.10)):
            z = top_z(x) + r * 0.45
            pts = _poly(x, z, r, rnd, sides=6, flat=0.8, lift=top_z(x) - 0.02)
            G.stroke(d, pts, M["coal"], 0.0, cyclic=True)
            G.stroke(d, [pts[0], pts[1], (x + r * 0.1, z + r * 0.05)], M["coal_hi"], 0.0, cyclic=True)
            G.stroke(d, pts, M["ink"], O, cyclic=True)
            spots.append((x + r * 0.3, z + r * 0.3))
    return spots


def node_silica(d, M, state, k=0):
    """A cluster of pale crystal prisms from a rock base."""
    mound(d, M, 0.62, 0.22, 14)
    spots = []
    prisms = [(-0.26, 0.55, -14, 0.09), (-0.05, 0.78, -4, 0.11), (0.18, 0.62, 10, 0.10), (0.36, 0.40, 22, 0.08), (-0.42, 0.34, -26, 0.07)]
    if state == "harvested":
        prisms = [(x, 0.18, a, w) for x, _l, a, w in prisms[1:4]]
    for j, (x, ln, a_deg, w) in enumerate(prisms):
        a = math.radians(a_deg)
        bx, bz = x, 0.12
        tx, tz = bx + ln * math.sin(a), bz + ln * math.cos(a)
        nx, nz = math.cos(a) * w, -math.sin(a) * w
        tip = (tx + 0.4 * w * math.sin(a), tz + 0.4 * w * math.cos(a))
        body = [(bx - nx, bz - nz), (tx - nx, tz - nz), tip, (tx + nx, tz + nz), (bx + nx, bz + nz)]
        G.stroke(d, body, M["crystal"], 0.0, cyclic=True)
        G.stroke(d, [(bx - nx, bz - nz), (tx - nx, tz - nz), tip, (tx, tz), (bx, bz)], M["crystal_sh"], 0.0, cyclic=True)
        G.stroke(d, body, M["ink"], O, cyclic=True)
        G.seam(d, [(bx, bz), (tx, tz), tip], M["ink"])
        if state != "harvested":
            spots.append((tx + nx * 0.5, tz + nz * 0.5))
    return spots


def node_water_ice(d, M, state, k=0):
    """A frozen spring's ice boulder on a rock: rounded ice with blue shading, an icicle lip, cracks."""
    mound(d, M, 0.66, 0.18, 15)
    h = 0.62 if state != "harvested" else 0.34
    xs = [-0.5 + i / 30 for i in range(31)]
    top = [(x, 0.12 + h * (1 - (x / 0.5) ** 2) ** 0.6 + 0.02 * math.sin(9 * x)) for x in xs]
    body = top + [(0.5, 0.10), (-0.5, 0.10)]
    G.stroke(d, body, M["ice"], 0.0, cyclic=True)
    G.stroke(d, [(x, 0.12 + (z - 0.12) * 0.5) for x, z in top if x < 0.05] + [(0.05, 0.10), (-0.5, 0.10)], M["ice_sh"], 0.0, cyclic=True)
    G.stroke(d, top, M["ink"], O)
    G.seam(d, [(-0.2, 0.12 + h * 0.8), (-0.05, 0.12 + h * 0.5), (-0.12, 0.12 + h * 0.25)], M["ink"])
    G.seam(d, [(0.18, 0.12 + h * 0.7), (0.24, 0.12 + h * 0.4)], M["ink"])
    for x in (-0.38, -0.25, 0.3):                                                           # icicles over the rock
        G.stroke(d, [(x - 0.03, 0.12), (x, 0.03), (x + 0.03, 0.12)], M["ice_dp_i"], I, cyclic=True)
    return [(0.12, 0.12 + h * 0.75), (-0.25, 0.12 + h * 0.55)] if state != "harvested" else []


NODES = {"iron": node_iron, "copper": node_copper, "carbon": node_carbon, "silica": node_silica, "water_ice": node_water_ice}


def draw_node(item):
    def fn(d, M, k):
        state = "full" if k == 0 else ("harvested" if k == 1 else "glint")
        spots = NODES[item](d, M, "harvested" if state == "harvested" else "full", k)
        if state == "glint":
            g = glint_at(k - 2, spots)
            if g:
                star(d, M, *g)
    return fn


# ---------------------------------------------------------------- buried pockets, the cache, the vault door, the X

def draw_pocket(item):
    def fn(d, M, k):
        """A rounded cavity in the cross-section (the Survey's find): a dark rim, the ore packed inside."""
        rnd = random.Random(50 + len(item))
        cav = G.lumpy_ellipse(0.0, 0.0, 0.62, 0.48, n=30, lump=0.06, seed=60 + len(item))
        G.stroke(d, cav, M["cavity"], 0.0, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(-0.08, -0.06, 0.52, 0.38, n=24, lump=0.05, seed=61), M["cavity_sh"], 0.0, cyclic=True)
        spots = []
        if item == "iron":
            for j in range(6):
                pts = _poly(rnd.uniform(-0.33, 0.33), rnd.uniform(-0.22, 0.18), rnd.uniform(0.10, 0.15), rnd, sides=6, lift=-9.0)
                G.stroke(d, pts, M["iron_i"], I, cyclic=True)
                spots.append(pts[1])
        elif item == "copper":
            for j in range(5):
                x, z = rnd.uniform(-0.32, 0.32), rnd.uniform(-0.22, 0.18)
                G.stroke(d, G.lumpy_ellipse(x, z, 0.12, 0.08, n=14, lump=0.12, seed=j), M["malachite_i"], I, cyclic=True)
                G.stroke(d, _poly(x + 0.06, z + 0.04, 0.05, rnd, sides=5, lift=-9.0), M["copper_i"], I, cyclic=True)
                spots.append((x + 0.06, z + 0.05))
        elif item == "carbon":
            for j in range(3):
                z = -0.2 + 0.18 * j
                G.stroke(d, G.lumpy_ellipse(0.0, z, 0.42 - 0.05 * abs(j - 1), 0.06, n=18, lump=0.08, seed=j), M["coal"], 0.0, cyclic=True)
                G.seam(d, [(-0.3, z + 0.02), (0.3, z + 0.03)], M["ink"])
                spots.append((0.15 * (j - 1), z + 0.03))
        elif item == "silica":
            for j, (x, a) in enumerate(((-0.25, -20), (0.0, 0), (0.22, 18), (0.38, 35))):
                a = math.radians(a)
                bx, bz, ln, w = x, -0.3, 0.34, 0.06
                tx, tz = bx + ln * math.sin(a), bz + ln * math.cos(a)
                nx, nz = math.cos(a) * w, -math.sin(a) * w
                body = [(bx - nx, bz - nz), (tx - nx, tz - nz), (tx + 0.3 * w * math.sin(a), tz + 0.3 * w * math.cos(a)), (tx + nx, tz + nz), (bx + nx, bz + nz)]
                G.stroke(d, body, M["crystal_i"], I, cyclic=True)
                spots.append((tx, tz))
        else:                                                                                # an ice lens filling the pocket
            G.stroke(d, G.lumpy_ellipse(0.0, -0.02, 0.46, 0.30, n=24, lump=0.05, seed=9), M["ice_i"], I, cyclic=True)
            G.stroke(d, G.lumpy_ellipse(-0.1, -0.08, 0.28, 0.14, n=16, lump=0.04, seed=10), M["ice_sh"], 0.0, cyclic=True)
            spots = [(0.12, 0.1)]
        G.stroke(d, cav, M["ink"], O, cyclic=True)
        if k > 0:
            g = glint_at(k - 1, spots)
            if g:
                star(d, M, *g)
    return fn


def draw_cache(d, M, k):
    """A half-buried Meridian data cache: a brass box tipped in the soil, the meridian emblem, a lamp that blinks."""
    box_ = [(-0.38, -0.20), (0.36, -0.26), (0.40, 0.18), (-0.34, 0.24)]
    G.stroke(d, box_, M["brass"], 0.0, cyclic=True)
    G.stroke(d, [(-0.38, -0.20), (-0.02, -0.23), (0.0, 0.21), (-0.34, 0.24)], M["brass_sh"], 0.0, cyclic=True)
    G.stroke(d, box_, M["ink"], O, cyclic=True)
    G.seam(d, [(-0.36, 0.0), (0.38, -0.04)], M["ink"])
    G.rivets(d, [(-0.3, -0.15), (0.3, -0.2), (0.33, 0.12), (-0.28, 0.18)], M["ink"], size=0.04)
    G.stroke(d, G.lumpy_ellipse(0.1, 0.09, 0.09, 0.09, n=18, lump=0.0), M["ink"], I, cyclic=True)     # the meridian emblem
    G.seam(d, [(0.1, 0.0), (0.1, 0.18)], M["ink"])
    lit = k > 0 and k % 2 == 1
    G.stroke(d, G.lumpy_ellipse(-0.2, 0.12, 0.05, 0.05, n=12, lump=0.0), M["lamp_on_i" if lit else "lamp_i"], I, cyclic=True)
    G.stroke(d, [(-0.5, -0.30), (0.5, -0.36), (0.5, -0.12), (-0.5, -0.05)], M["soil"], 0.0, cyclic=True)   # the soil it sits in
    G.seam(d, [(-0.5, -0.05), (0.5, -0.12)], M["ink"])


VAULT_OPEN = [0.0, 0.18, 0.40, 0.62, 0.82, 0.95]


def draw_vault(d, M, k):
    """A round Warden vault door in the cross-section: offwhite stone, teal inset panels, a hum ring; open rolls it aside."""
    t = 0.0 if k == 0 else VAULT_OPEN[k - 1]
    G.stroke(d, G.lumpy_ellipse(0.0, 0.0, 0.72, 0.72, n=40, lump=0.02, seed=3), M["dark_i"], O, cyclic=True)   # the doorway
    G.stroke(d, G.lumpy_ellipse(0.0, 0.0, 0.84, 0.84, n=40, lump=0.02, seed=4), M["ink"], O, cyclic=True)       # the frame's rim
    for j in range(8):
        a = TAU * j / 8
        G.seam(d, [(0.74 * math.cos(a), 0.74 * math.sin(a)), (0.84 * math.cos(a), 0.84 * math.sin(a))], M["ink"])
    r = 0.70                                         # it swings open on a hinge at its left edge: narrowing in place
    sx = max(0.08, 1.0 - 0.92 * t)
    cx = -r + r * sx
    door = G.lumpy_ellipse(cx, 0.0, r * sx, r, n=40, lump=0.015, seed=5)
    G.stroke(d, door, M["stone"], 0.0, cyclic=True)
    G.stroke(d, [(cx + r * sx * math.cos(a), r * math.sin(a)) for a in [math.pi * (0.55 + 0.9 * i / 20) for i in range(21)]] + [(cx - r * sx * 0.2, 0.0)],
             M["stone_sh"], 0.0, cyclic=True)
    for j in range(4):                                                                       # teal inset panels
        a0 = TAU * j / 4 + math.pi / 4
        pnl = [(cx + 0.28 * r * sx * math.cos(a0 + da) * s, 0.28 * r * math.sin(a0 + da) * s) for s, da in ((1, -0.3), (2.2, -0.2), (2.2, 0.2), (1, 0.3))]
        G.stroke(d, pnl, M["panel_i"], I, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(cx, 0.0, r * 0.18 * sx, r * 0.18, n=16, lump=0.0), M["panel_i"], I, cyclic=True)
    G.stroke(d, door, M["ink"], O, cyclic=True)
    if k == 0:                                                                               # the hum ring while closed
        G.stroke(d, [(0.95 * math.cos(a), 0.95 * math.sin(a)) for a in [math.pi * (0.1 + 0.3 * i / 10) for i in range(11)]], M["ink"], I)
        G.stroke(d, [(0.95 * math.cos(a), 0.95 * math.sin(a)) for a in [math.pi * (1.1 + 0.3 * i / 10) for i in range(11)]], M["ink"], I)


def draw_x(d, M, k):
    """The Survey scan's X painted on the ground: two crossed red brush strokes, pulsing on twos."""
    s = 1.0 + 0.10 * math.sin(TAU * k / 8)
    for sgn in (1, -1):
        a = math.radians(45 * sgn)
        L, w = 0.30 * s, 0.055 * s
        ux, uz = math.sin(a), math.cos(a)
        nx, nz = uz, -ux
        cz = 0.30
        stroke_ = [(-L * ux - w * nx, cz - L * uz - w * nz), (L * ux - w * nx * 0.7, cz + L * uz - w * nz * 0.7),
                   (L * ux + w * nx * 0.7, cz + L * uz + w * nz * 0.7), (-L * ux + w * nx, cz - L * uz + w * nz)]
        G.stroke(d, stroke_, M["xred"], 0.0, cyclic=True)
        G.stroke(d, [stroke_[0], stroke_[1], ((stroke_[0][0] + stroke_[1][0]) / 2, (stroke_[0][1] + stroke_[1][1]) / 2 - 0.01)], M["xred_sh"], 0.0, cyclic=True)
        G.stroke(d, stroke_, M["ink"], O, cyclic=True)
        G.seam(d, [(-L * ux * 0.6 + w * nx * 0.3, cz - L * uz * 0.6 + w * nz * 0.3), (L * ux * 0.5 + w * nx * 0.3, cz + L * uz * 0.5 + w * nz * 0.3)], M["ink"])   # a brush streak
    G.stroke(d, G.lumpy_ellipse(0.0, 0.02, 0.26 * s, 0.035, n=20, lump=0.02, seed=2), M["xred_sh"], 0.0, cyclic=True)   # its shadow on the ground


# ---------------------------------------------------------------- the table

PIECES = {}
for _it in NODES:
    PIECES[f"node_{_it}"] = (draw_node(_it), 128, 96, (0.5, 6 / 96), [("full", 1, False), ("harvested", 1, False), ("glint", 8, True)])
    PIECES[f"pocket_{_it}"] = (draw_pocket(_it), 96, 96, (0.5, 0.5), [("full", 1, False), ("glint", 8, True)])
PIECES["data_cache"] = (draw_cache, 96, 80, (0.5, 0.5), [("full", 1, False), ("glint", 8, True)])
PIECES["vault_door"] = (draw_vault, 128, 128, (0.5, 0.5), [("closed", 1, False), ("open", 6, False)])
PIECES["scan_x"] = (draw_x, 64, 64, (0.5, 6 / 64), [("pulse", 8, True)])


def render(name, planet="earth"):
    fn, fw, fh, piv, clips = PIECES[name]
    frames, widths = [], []
    n = sum(c[1] for c in clips)
    for k in range(n):
        gp = fakegp.FakeGP()
        M = mats(gp, planet)
        d = fakegp.FakeDrawing()
        fn(d, M, k)
        img, w = GR.render_frame(fakegp.strokes_of(d, gp), fw, fh, PPU, piv, ss=4, seed=1760 + k)
        frames.append(img)
        widths += w
    return frames, widths


def sheet_meta(name, frames, planet="earth"):
    import numpy as np
    _fn, fw, fh, piv, clips = PIECES[name]
    g = v3.GUTTER
    n = len(frames)
    cols = max(1, min(n, (512 + g) // (fw + g)))
    rows = -(-n // cols)
    sheet = np.zeros((rows * fh + (rows - 1) * g, min(cols, n) * fw + (min(cols, n) - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw] = im
    anims, s_ = [], 0
    for cn, cnt, lp in clips:
        anims.append({"name": cn, "start": s_, "length": cnt, "loop": lp, **({"loop_from": 0} if lp else {})})
        s_ += cnt
    meta = {"key": f"props/{planet}/{name}", "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": g,
            "frames": n, "fps": v3.FPS, "pivot": list(piv), "facing": "right", "ppu": PPU, "animations": anims, "squash_root": False,
            "provisional_key": True}
    problems = list(v3.validate_sheet(meta, sheet.shape))
    if sheet.shape[0] > 512 or sheet.shape[1] > 512:
        problems.append(f"sheet {sheet.shape[1]}x{sheet.shape[0]} over 512^2")
    m = v3.EDGE_MARGIN
    for i, im in enumerate(frames):
        a = im[..., 3]
        if a[:m].any() or a[-m:].any() or a[:, :m].any() or a[:, -m:].any():
            problems.append(f"frame {i} touches the {m} px edge")
    return sheet, meta, problems


def preview(out_dir, planet="earth"):
    """Earth's B-175 ground (band + fill from Art) flat at 1x: the five nodes on the surface beside the surveyor (full,
    harvested), the pockets, the cache and the vault door in the cutaway, the X above a pocket; every clip; the checks."""
    import json
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    res = {n: render(n, planet) for n in PIECES}
    W = 2000
    band = pngio.read_png_np(os.path.join(ART, "terrain", planet, "ground_band_color.png"))
    fill = pngio.read_png_np(os.path.join(ART, "terrain", planet, "ground_fill_color.png"))
    sky = np.array(v3.hex_rgb(v3.PALETTES[planet]["sky"]), np.float32) / 255.0
    SH = 720                                              # the scene: 4 m of sky, then the ground's cross-section
    surf = 300
    img = np.empty((SH, W, 3), np.float32)
    img[:surf] = sky
    ft = np.tile(fill, (2, 4, 1))[:SH - surf, :W].astype(np.float32) / 255.0
    img[surf:] = ft[..., :3]
    bt = np.tile(band, (1, 4, 1))[:, :W]
    review._over(img, bt, 0, surf - 24)

    def place(im, piv, x, y):
        h, w = im.shape[:2]
        review._over(img, im, int(x - piv[0] * w), int(y - (1 - piv[1]) * h))
    xs = [150, 420, 690, 960, 1230]
    for (name, x) in zip(NODES, xs):
        place(res[f"node_{name}"][0][0], (0.5, 6 / 96), x, surf + 2)
        place(res[f"node_{name}"][0][1], (0.5, 6 / 96), x + 140, surf + 2)
        review._label(img, f"{name}: full | harvested", x - 60, surf - 110)
    for j, name in enumerate(NODES):
        place(res[f"pocket_{name}"][0][0], (0.5, 0.5), 160 + 250 * j, surf + 230)
    place(res["data_cache"][0][0], (0.5, 0.5), 1450, surf + 120)
    place(res["vault_door"][0][0], (0.5, 0.5), 1700, surf + 250)
    place(res["scan_x"][0][0], (0.5, 6 / 64), 160 + 250 * 2, surf + 2)
    try:
        sm = json.load(open(os.path.join(ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
        shs = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))
        fr = shs[:sm["frame_height"], :sm["frame_width"]]
        review._over(img, fr, 1550, surf - sm["frame_height"] + int(round(sm["pivot"][1] * sm["frame_height"])) + 2)
    except (OSError, KeyError, ValueError):
        pass
    review._label(img, f"b-176 {planet} nodes at 1x on the b-175 ground (keys provisional, renamed at export): five nodes full | harvested; "
                       "the pockets, the data cache and the warden vault door in the cutaway; the scan's x above the carbon pocket", 6, 6)
    rows = [img]
    for name, (fn, fw, fh, piv, clips) in PIECES.items():
        frames = res[name][0]
        row = np.empty((fh + 34, W, 3), np.float32)
        row[:] = review.PAPER
        for i, im in enumerate(frames):
            xx = 8 + i * (fw + 6)
            if xx + fw > W:
                break
            row[24:24 + fh, xx:xx + fw] = sky
            review._over(row, im, xx, 24)
        review._label(row, f"{name} {fw}x{fh}: " + ", ".join(f"{c} {n_}" for c, n_, _l in clips), 6, 4)
        rows.append(row)
    lines = []
    for name in PIECES:
        frames, widths = res[name]
        sheet, meta, probs = sheet_meta(name, frames, planet)
        o = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
        n_ = [w for w in widths if w[0] < v3.OUTER_SPLIT]
        rng = lambda q: f"{min(w[1] for w in q):.1f}-{max(w[2] for w in q):.1f}" if q else "-"  # noqa: E731
        pal = v3.palette_hits(sheet, planet)[0] * 100
        lines.append(f"{name}: sheet {sheet.shape[1]}x{sheet.shape[0]}, ink {rng(o)} / {rng(n_)} px, palette {pal:.1f}%, "
                     f"json {'valid' if not probs else 'INVALID: ' + '; '.join(probs)[:70]}; no face")
    foot = np.empty((30 + 16 * len(lines), W, 3), np.float32)
    foot[:] = review.PAPER
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    out_img = np.vstack(rows + [foot])
    del rows, img
    import time
    review.draw(out_img, time.strftime("%m-%d %H:%M") + " design preview (lock-free, fakegp)", 2, out_img.shape[0] - 16, (1.0, 1.0, 0.85))
    shape = out_img.shape
    np.clip(out_img, 0.0, 1.0, out=out_img)
    out_img *= 255.0
    np.rint(out_img, out=out_img)
    u8 = np.empty(shape[:2] + (4,), np.uint8)
    u8[..., :3] = out_img
    u8[..., 3] = 255
    del out_img
    out = os.path.join(out_dir, f"review_b176_{planet}_nodes_preview.png")
    pngio.write_png(out, u8)
    print("written", out, shape[1], "x", shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    preview(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "earth")
    fakegp.restore()
