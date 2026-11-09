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

  B-219 (LEAD 00:2x): the giants' floes get nodes only (no pockets / relics / scan X), json "deck" (where U-189 places it; deeper
  rarer) and "item" (what it drops): Jupiter ammonia_ice (deck1), metallic_hydrogen (deep); Saturn ring_ice (deck1), ring_rock
  (deck2), helium3 (deep, drops helium3_condensate); Uranus methane_ice (deck1), superionic_ice (deep); Neptune methane_ice (deck1),
  superionic_ice (deck3), deep_diamond (deep). Preview: review_b219_<giant>_nodes_preview.png (the nodes on floe_strip_ice).

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
    if planet == "mars":                        # LEAD 05:3x: hematite, perchlorate crust, water ice; an old lander beacon
        return {"rock": dp("sky"), "rock_sh": P["brown"], "rock_hi": sh("sky"), "hem": dp("teal"), "hem_hi": sh("offwhite"),
                "salt": P["offwhite"], "salt_sh": sh("offwhite"), "ice": P["offwhite"], "ice_sh": sh("teal"), "ice_dp": P["teal"],
                "dust": P["red"], "dust_sh": sh("red"), "soil": dp("red"), "cavity": P["brown"], "cavity_sh": dp("red"),
                "capsule": P["offwhite"], "capsule_sh": sh("offwhite"), "stripe": P["red"], "dish": P["teal"],
                "lamp": P["red"], "lamp_on": P["mustard"], "glint": P["offwhite"], "dark": P["brown"],
                "xpale": P["offwhite"], "xpale_sh": sh("offwhite")}
    if planet == "mercury":                     # LEAD 05:3x: solarite (nodes and pockets), nickel; an old sunshade probe
        return {"rock": sh("sky"), "rock_sh": dp("sky"), "rock_hi": P["sky"], "solar": P["mustard"], "solar_sh": sh("mustard"),
                "solar_hi": P["offwhite"], "nickel": sh("offwhite"), "nickel_sh": dp("offwhite"), "nickel_hi": P["offwhite"],
                "dust": P["offwhite"], "dust_sh": sh("offwhite"), "soil": sh("offwhite"), "cavity": P["brown"], "cavity_sh": dp("red"),
                "capsule": P["offwhite"], "capsule_sh": sh("offwhite"), "panel": P["teal"], "lamp": P["red"], "lamp_on": P["mustard"],
                "glint": P["offwhite"], "dark": P["brown"], "ice": P["offwhite"], "ice_sh": P["sky"],
                "xpale": P["offwhite"], "xpale_sh": sh("offwhite"), "xred": P["red"], "xred_sh": sh("red")}
    if planet == "venus":                       # LEAD 05:3x: vitriol glass, sulfur; an old pressure capsule
        return {"rock": dp("teal"), "rock_sh": P["brown"], "rock_hi": sh("teal"), "glass": P["green"], "glass_sh": sh("green"),
                "glass_hi": P["offwhite"], "sulfur": P["mustard"], "sulfur_sh": sh("mustard"), "salt_sh": sh("mustard"),
                "fume": P["offwhite"], "vent": P["brown"], "soil": dp("red"), "cavity": P["brown"], "cavity_sh": dp("red"),
                "capsule": P["mustard"], "capsule_sh": sh("mustard"), "stripe": P["red"], "petal": sh("mustard"),
                "lamp": P["red"], "lamp_on": P["offwhite"], "glint": P["offwhite"], "dark": P["brown"], "ice": P["offwhite"],
                "ice_sh": P["sky"], "xred": P["red"], "xred_sh": sh("red"), "xpale": P["offwhite"], "xpale_sh": sh("offwhite")}
    # B-219 (LEAD 00:2x): the giants' harvestable nodes on their floes, each giant's own palette and tones only
    if planet == "jupiter":                     # ammonia ice (deck 1), metallic hydrogen (the deep)
        return {"rock": sh("sky"), "rock_sh": dp("sky"), "rock_hi": P["offwhite"], "crystal": P["offwhite"], "crystal_sh": sh("offwhite"),
                "crystal_tint": P["teal"], "metal": P["teal"], "metal_sh": dp("teal"), "metal_hi": P["offwhite"],
                "shell": P["brown"], "shell_sh": dp("brown"), "band": P["mustard"], "band2": P["red"],
                "glint": P["offwhite"], "dark": P["brown"]}
    if planet == "saturn":                      # ring ice (deck 1), ring rock (deck 2), helium-3 (the deep)
        return {"rock": sh("offwhite"), "rock_sh": dp("offwhite"), "rock_hi": P["offwhite"], "ice": P["offwhite"], "ice_sh": P["teal"],
                "ice_dp": sh("teal"), "rrock": dp("sky"), "rrock_sh": P["brown"], "rrock_hi": P["sky"], "vent": sh("sky"), "vent_sh": dp("sky"),
                "mouth": P["brown"], "frost": P["offwhite"], "frost_sh": sh("offwhite"), "rose": P["red"], "rose_sh": sh("red"),
                "rose_hi": P["offwhite"], "glint": P["offwhite"], "dark": P["brown"]}
    if planet == "uranus":                      # methane ice (deck 1), superionic ice (the deep: ice-cyan; Uranus has no violet)
        return {"rock": sh("sky"), "rock_sh": dp("sky"), "rock_hi": P["offwhite"], "meth": P["sky"], "meth_sh": P["teal"],
                "meth_hi": P["offwhite"], "super": P["teal"], "super_sh": sh("teal"), "super_hi": P["offwhite"], "glint": P["offwhite"],
                "dark": P["brown"]}
    if planet == "neptune":                     # methane ice (deck 1), superionic ice (deck 3, violet), deep diamond (the deep)
        return {"rock": sh("offwhite"), "rock_sh": dp("offwhite"), "rock_hi": P["offwhite"], "meth": P["teal"], "meth_sh": sh("teal"),
                "meth_hi": P["offwhite"], "super": P["mustard"], "super_sh": sh("mustard"), "super_hi": P["offwhite"],
                "diamond": P["offwhite"], "diamond_sh": P["teal"], "diamond_dp": P["sky"], "pit": sh("offwhite"), "glint": P["offwhite"],
                "dark": P["brown"]}
    raise ValueError(f"B-176: no node tones for {planet}")


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


# ---------------------------------------------------------------- Mars (LEAD 05:3x: hematite, perchlorate crust, water ice; a relic)

def node_hematite(d, M, state, k=0):
    """A tall dusty crag studded with kidney-ore hematite (grey botryoidal clusters with bright highlights) and loose
    'blueberries' at its foot; harvested: a stump with one cluster and chip marks."""
    rnd = random.Random(31)
    full = state != "harvested"
    w, h = (0.84, 1.08) if full else (0.70, 0.52)
    top_z = crag(d, M, w, h, 21)
    spots = []
    clusters = [(-0.38, 0.45, 0.17), (0.12, 0.78, 0.18), (0.42, 0.40, 0.15), (-0.10, 0.28, 0.14), (-0.28, 0.86, 0.13)] if full \
        else [(-0.10, 0.22, 0.13)]
    for j, (x, z, r) in enumerate(clusters):
        z = min(z, top_z(x) - r * 0.75)
        for q in range(4):
            a = TAU * q / 4 + j
            bx, bz, rr = x + r * 0.5 * math.cos(a), z + r * 0.42 * math.sin(a), r * 0.56
            G.stroke(d, G.lumpy_ellipse(bx, bz, rr, rr * 0.92, n=14, lump=0.04, seed=j * 5 + q), M["hem_i"], I, cyclic=True)
            G.stroke(d, G.lumpy_ellipse(bx + rr * 0.32, bz + rr * 0.36, rr * 0.24, rr * 0.18, n=8, lump=0.0), M["hem_hi"], 0.0, cyclic=True)
        spots.append((x + r * 0.3, z + r * 0.4))
    for q in range(7 if full else 3):                                                        # loose blueberries at the foot
        x = -0.7 + 1.4 * (q + 0.5) / (7 if full else 3) + rnd.uniform(-0.05, 0.05)
        G.stroke(d, G.lumpy_ellipse(x, 0.035, 0.04, 0.036, n=10, lump=0.03, seed=40 + q), M["hem_i"], I, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x + 0.012, 0.05, 0.012, 0.01, n=6, lump=0.0), M["hem_hi"], 0.0, cyclic=True)
    if not full:
        for x in (-0.4, 0.15, 0.42):
            G.seam(d, [(x - 0.07, top_z(x) - 0.04), (x, top_z(x) - 0.12), (x + 0.07, top_z(x) - 0.04)], M["ink"])
    return spots


def _rosette(d, M, x, z, s, seed, role="salt_i"):
    rnd = random.Random(seed)
    tips = []
    for b in range(4):                                                                       # chunky white crystal prisms
        a = math.radians(-48 + 32 * b + rnd.uniform(-6, 6))
        ln = s * rnd.uniform(0.85, 1.15)
        ux, uz, w = math.sin(a), math.cos(a), 0.042
        tx, tz = x + ln * ux, z + ln * uz
        body = [(x - w * uz, z + w * ux), (tx - w * uz, tz + w * ux), (tx + 0.6 * w * ux, tz + 0.6 * w * uz), (tx + w * uz, tz - w * ux), (x + w * uz, z - w * ux)]
        G.stroke(d, body, M[role], I, cyclic=True)
        G.stroke(d, [body[0], body[1], body[2], (x, z)], M['salt_sh'], 0.0, cyclic=True)
        G.seam(d, [(x, z), (tx, tz), body[2]], M['ink'])
        tips.append((tx, tz))
    return tips


def node_perchlorate(d, M, state, k=0):
    """A dusty crag under a thick white perchlorate salt crust (a lumpy, cauliflower underside), salt crystal rosettes on
    top, salt patches weeping down the face; harvested: a stump with a thin crust remnant."""
    full = state != "harvested"
    w, h = (0.82, 0.94) if full else (0.70, 0.50)
    top_z = crag(d, M, w, h, 22)
    th = 0.20 if full else 0.08
    xs = [-w * 0.93 + 1.86 * w * i / 40 for i in range(41)]
    upper = [(x, top_z(x) + 0.035) for x in xs]
    lower = [(x, top_z(x) - th - 0.05 * max(0.0, math.sin(11 * x + 0.5)) ** 2) for x in xs]
    G.stroke(d, upper + lower[::-1], M["salt"], 0.0, cyclic=True)
    G.stroke(d, [(x, z + 0.045) for x, z in lower] + lower[::-1], M["salt_sh"], 0.0, cyclic=True)
    G.stroke(d, upper, M["ink"], O)
    G.stroke(d, lower, M["ink"], I)
    spots = []
    if full:
        for j, x in enumerate((-0.30, 0.05, 0.36)):
            tips = _rosette(d, M, x, top_z(x) + 0.01, 0.16 if j == 1 else 0.12, 60 + j)
            spots.append(tips[2])
        rnd = random.Random(62)
        for q in range(6):                                                                   # salt weeping down the face
            x = rnd.uniform(-0.55, 0.55)
            z = rnd.uniform(0.18, max(0.2, top_z(x) - th - 0.12))
            G.stroke(d, G.lumpy_ellipse(x, z, 0.05, 0.03, n=10, lump=0.15, seed=q), M["salt_i"], I, cyclic=True)
    return spots


def node_mars_ice(d, M, state, k=0):
    """An exposed block of buried water ice in a scarp: a tall rounded block, layered with dust bands, under a rust dust cap,
    teal-shaded, cracked; harvested: a low stub of ice under the dust."""
    full = state != "harvested"
    w, h = (0.74, 1.12) if full else (0.66, 0.48)
    xs = [-w + 2 * w * i / 40 for i in range(41)]
    top = [(x, h * max(0.0, 1 - (abs(x) / w) ** 3.0) ** 0.45 + 0.02 * math.sin(6 * x)) for x in xs]
    G.stroke(d, top + [(w, -0.02), (-w, -0.02)], M["ice"], 0.0, cyclic=True)
    G.stroke(d, [(x, z * 0.85) for x, z in top if x < -0.1] + [(-0.1, -0.02), (-w, -0.02)], M["ice_sh"], 0.0, cyclic=True)
    for j, f in enumerate((0.30, 0.55, 0.78) if full else (0.45,)):                         # the dust layers in the ice
        band = [(x, z * f + 0.015 * math.sin(9 * x + j)) for x, z in top[3:-3]]
        G.stroke(d, band + [(x, z - 0.03) for x, z in band[::-1]], M["dust_sh"], 0.0, cyclic=True)
    cap = [(x, z + 0.04) for x, z in top[2:-2]]                                               # the rust dust cap
    G.stroke(d, cap + [(x, z - 0.10 - 0.03 * math.sin(13 * x)) for x, z in top[2:-2][::-1]], M["dust"], 0.0, cyclic=True)
    G.stroke(d, top, M["ink"], O)
    G.seam(d, [(x, z - 0.10 - 0.03 * math.sin(13 * x)) for x, z in top[3:-3]], M["ink"])
    G.seam(d, [(-0.25, h * 0.7), (-0.12, h * 0.48), (-0.2, h * 0.25)], M["ink"])
    G.seam(d, [(0.22, h * 0.62), (0.3, h * 0.35)], M["ink"])
    for x in (-0.5, 0.45):                                                                    # meltwater icicles at the foot
        G.stroke(d, [(x - 0.03, 0.12), (x, 0.02), (x + 0.03, 0.12)], M["ice_dp_i"], I, cyclic=True)
    return [(0.15, h * 0.7), (-0.3, h * 0.5), (0.35, h * 0.35)] if full else []


def draw_beacon(d, M, k):
    """A half-buried old lander beacon (Mars's relic): a domed capsule with a red stripe, a dish antenna on a bent strut,
    its lamp blinking on the glint clip."""
    body = G.lumpy_ellipse(0.0, 0.02, 0.40, 0.33, n=30, lump=0.01, seed=7, rot=-0.25)
    body = [(x, max(z, -0.18)) for x, z in body]
    G.stroke(d, body, M["capsule"], 0.0, cyclic=True)
    G.stroke(d, [(x, z) for x, z in body if x < 0.0] + [(0.0, -0.18)], M["capsule_sh"], 0.0, cyclic=True)
    G.stroke(d, [(-0.33, 0.02), (0.30, -0.14), (0.31, -0.08), (-0.31, 0.09)], M["stripe"], 0.0, cyclic=True)
    G.stroke(d, body, M["ink"], O, cyclic=True)
    G.seam(d, [(-0.33, 0.02), (0.30, -0.14)], M["ink"])
    G.stroke(d, [(-0.30, 0.10), (-0.10, 0.07), (-0.08, 0.25), (-0.26, 0.29)], M["ink"], I, cyclic=True)   # a hatch outline, off-centre
    G.seam(d, [(-0.28, 0.20), (-0.24, 0.19)], M["ink"])
    G.seam(d, [(0.08, 0.24), (0.16, 0.36), (0.26, 0.38)], M["ink"], radius=O)                # the bent strut
    dish = [(0.16, 0.50), (0.36, 0.30), (0.42, 0.40), (0.26, 0.56)]
    G.stroke(d, dish, M["dish_i"], O, cyclic=True)
    G.seam(d, [(0.22, 0.44), (0.35, 0.33)], M["ink"])
    lit = k > 0 and k % 2 == 1
    G.stroke(d, G.lumpy_ellipse(0.43, 0.57, 0.035, 0.035, n=12, lump=0.0), M["lamp_on_i" if lit else "lamp_i"], I, cyclic=True)   # on the dish's tip
    G.stroke(d, [(-0.5, -0.32), (0.5, -0.36), (0.5, -0.16), (-0.5, -0.10)], M["soil"], 0.0, cyclic=True)
    G.seam(d, [(-0.5, -0.10), (0.5, -0.16)], M["ink"])
    if k > 0 and k % 4 == 2:
        star(d, M, 0.30, 0.42, 0.07)


# ---------------------------------------------------------------- Mercury (LEAD 05:3x: solarite as nodes and pockets - the Beam cuts it in
# the twilight window - and nickel; a relic)

def _prism(d, M, bx, bz, ln, a_deg, w, fill, shade, cut=False):
    """A crystal prism from (bx, bz): a lit right face, a shaded left face, the facet seam; cut = a flat beam-cut top."""
    a = math.radians(a_deg)
    tx, tz = bx + ln * math.sin(a), bz + ln * math.cos(a)
    nx, nz = math.cos(a) * w, -math.sin(a) * w
    tip = (tx + (0.05 if cut else 0.45) * w * math.sin(a), tz + (0.05 if cut else 0.45) * w * math.cos(a))
    body = [(bx - nx, bz - nz), (tx - nx, tz - nz), tip, (tx + nx, tz + nz), (bx + nx, bz + nz)]
    G.stroke(d, body, M[fill], 0.0, cyclic=True)
    G.stroke(d, [(bx - nx, bz - nz), (tx - nx, tz - nz), tip, (tx, tz), (bx, bz)], M[shade], 0.0, cyclic=True)
    G.stroke(d, body, M["ink"], O, cyclic=True)
    G.seam(d, [(bx, bz), (tx, tz), tip], M["ink"])
    if cut:                                                                                  # the beam's glowing cut face
        G.stroke(d, G.lumpy_ellipse(tx, tz, w * 0.95, w * 0.35, n=12, lump=0.0, rot=-a), M["solar_hi_i"], I, cyclic=True)
    return tx, tz


def node_solarite(d, M, state, k=0):
    """A cluster of golden solarite prisms from a breccia base (the B-148 solarite look, bolder); harvested: beam-cut stumps."""
    mound(d, M, 0.68, 0.24, 16)
    prisms = [(-0.48, 0.42, -30, 0.09), (0.47, 0.46, 28, 0.09), (-0.27, 0.74, -16, 0.12), (0.27, 0.82, 13, 0.12), (0.0, 1.02, -3, 0.15)]
    spots = []
    for j, (x, ln, a_deg, w) in enumerate(prisms):
        if state == "harvested":
            _prism(d, M, x, 0.14, 0.16 + 0.03 * (j % 2), a_deg * 0.5, w, "solar", "solar_sh", cut=True)
        else:
            tx, tz = _prism(d, M, x, 0.14, ln, a_deg, w, "solar", "solar_sh")
            spots.append((tx, tz - 0.06))
    return spots


def node_nickel(d, M, state, k=0):
    """A nickel-iron meteorite half-sunk in its crater rim: a rounded silver-grey lump with thumbprint dimples and a lit
    sheen, the cream regolith rim heaped in front; harvested: a smaller chunk with chip marks."""
    full = state != "harvested"
    cx, cz, rx, rz = (0.0, 0.55, 0.56, 0.52) if full else (0.05, 0.30, 0.36, 0.28)
    blob = [(x, max(z, 0.10)) for x, z in G.lumpy_ellipse(cx, cz, rx, rz, n=34, lump=0.07, seed=81)]
    G.stroke(d, blob, M["nickel"], 0.0, cyclic=True)
    G.stroke(d, [(x, z) for x, z in G.lumpy_ellipse(cx - rx * 0.30, cz - rz * 0.25, rx * 0.62, rz * 0.62, n=20, lump=0.05, seed=82)
                 if z >= 0.10] or [(0, 0.1)], M["nickel_sh"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(cx + rx * 0.35, cz + rz * 0.5, rx * 0.28, rz * 0.12, n=12, lump=0.05, seed=83, rot=-0.5), M["nickel_hi"], 0.0,
             cyclic=True)
    rnd = random.Random(84)
    for q in range(7 if full else 3):                                                        # thumbprint dimples
        x, z = cx + rnd.uniform(-0.6, 0.6) * rx, cz + rnd.uniform(-0.45, 0.55) * rz
        r = rnd.uniform(0.05, 0.08) * (1.0 if full else 0.8)
        G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.8, n=12, lump=0.06, seed=q), M["nickel_sh_i"], I, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x + r * 0.3, z + r * 0.3, r * 0.35, r * 0.25, n=8, lump=0.0), M["nickel_hi"], 0.0, cyclic=True)
    G.stroke(d, blob, M["ink"], O, cyclic=True)
    if not full:
        for x in (-0.15, 0.2):
            G.seam(d, [(x - 0.06, cz + rz * 0.6), (x, cz + rz * 0.35), (x + 0.06, cz + rz * 0.6)], M["ink"])
    xs = [-0.86 + 1.72 * i / 30 for i in range(31)]                                            # the crater rim in front
    rim = [(x, 0.20 * max(0.0, 1 - (x / 0.86) ** 2) ** 0.5 * (0.75 + 0.25 * math.cos(2.4 * x))) for x in xs]
    G.stroke(d, rim + [(0.86, -0.02), (-0.86, -0.02)], M["dust"], 0.0, cyclic=True)
    G.stroke(d, [(x, z * 0.45) for x, z in rim] + [(0.86, -0.02), (-0.86, -0.02)], M["dust_sh"], 0.0, cyclic=True)
    G.stroke(d, rim, M["ink"], O)
    return [(cx + rx * 0.4, cz + rz * 0.55), (cx - rx * 0.2, cz + rz * 0.7)] if full else [(cx + rx * 0.3, cz + rz * 0.5)]


def draw_sunprobe(d, M, k):
    """Mercury's relic: an old probe half-buried in the regolith, its curved cloth sunshade still raised, a teal solar
    panel, its lamp blinking on the glint clip."""
    box_ = [(-0.30, -0.16), (0.22, -0.22), (0.26, 0.16), (-0.26, 0.22)]
    G.stroke(d, box_, M["capsule"], 0.0, cyclic=True)
    G.stroke(d, [(-0.30, -0.16), (-0.04, -0.19), (-0.02, 0.19), (-0.26, 0.22)], M["capsule_sh"], 0.0, cyclic=True)
    G.stroke(d, box_, M["ink"], O, cyclic=True)
    G.seam(d, [(-0.28, 0.03), (0.24, -0.03)], M["ink"])
    pnl = [(0.24, 0.02), (0.58, 0.14), (0.54, 0.30), (0.22, 0.16)]                             # the solar panel
    G.stroke(d, pnl, M["panel_i"], O, cyclic=True)
    for t in (0.33, 0.66):
        G.seam(d, [(0.24 + 0.34 * t, 0.02 + 0.12 * t), (0.22 + 0.32 * t, 0.16 + 0.14 * t)], M["ink"])
    shade = [(-0.42 + 0.84 * i / 16, 0.40 + 0.12 * math.sin(math.pi * i / 16)) for i in range(17)]   # the curved sunshade
    G.stroke(d, shade + [(x, z - 0.07) for x, z in shade[::-1]], M["capsule_i"], O, cyclic=True)
    G.seam(d, [(-0.25, 0.22), (-0.30, 0.38)], M["ink"], radius=O)
    G.seam(d, [(0.10, 0.20), (0.12, 0.44)], M["ink"], radius=O)
    lit = k > 0 and k % 2 == 1
    G.stroke(d, G.lumpy_ellipse(0.56, 0.31, 0.035, 0.035, n=12, lump=0.0), M["lamp_on_i" if lit else "lamp_i"], I, cyclic=True)   # on the panel's corner
    G.stroke(d, [(-0.5, -0.34), (0.5, -0.38), (0.5, -0.14), (-0.5, -0.08)], M["soil"], 0.0, cyclic=True)
    G.seam(d, [(-0.5, -0.08), (0.5, -0.14)], M["ink"])
    if k > 0 and k % 4 == 2:
        star(d, M, 0.50, 0.26, 0.07)


# ---------------------------------------------------------------- Venus (LEAD 05:3x: vitriol glass, sulfur; a relic)

def _shard_poly(bx, bz, ln, a_deg, w):
    """An angular glass blade from (bx, bz): two base corners, a kinked side, the tip."""
    a = math.radians(a_deg)
    ux, uz = math.sin(a), math.cos(a)
    nx, nz = uz * w, -ux * w
    s1 = (bx + 0.82 * ln * ux - 0.85 * nx, bz + 0.82 * ln * uz - 0.85 * nz)                 # chisel-tipped: shoulders, then
    tip = (bx + ln * ux + 0.25 * nx, bz + ln * uz + 0.25 * nz)                                 # an off-centre point
    s2 = (bx + 0.66 * ln * ux + 0.95 * nx, bz + 0.66 * ln * uz + 0.95 * nz)
    return [(bx - nx, bz - nz), s1, tip, s2, (bx + nx, bz + nz)], tip


def _glass(d, M, bx, bz, ln, a_deg, w, ink=O):
    pts, tip = _shard_poly(bx, bz, ln, a_deg, w)
    G.stroke(d, pts, M["glass"], 0.0, cyclic=True)
    G.stroke(d, [pts[0], pts[1], pts[2], (bx + 0.1 * (pts[4][0] - bx), bz + 0.1 * (pts[4][1] - bz))], M["glass_sh"], 0.0, cyclic=True)   # the shaded facet
    a = math.radians(a_deg)
    G.stroke(d, [(bx + 0.30 * ln * math.sin(a) + 0.25 * w * math.cos(a), bz + 0.30 * ln * math.cos(a) - 0.25 * w * math.sin(a)),
                 (bx + 0.75 * ln * math.sin(a) + 0.12 * w * math.cos(a), bz + 0.75 * ln * math.cos(a) - 0.12 * w * math.sin(a)),
                 (bx + 0.72 * ln * math.sin(a) + 0.30 * w * math.cos(a), bz + 0.72 * ln * math.cos(a) - 0.30 * w * math.sin(a))],
             M["glass_hi"], 0.0, cyclic=True)                                                 # a sheen streak
    G.stroke(d, pts, M["ink"], ink, cyclic=True)
    G.seam(d, [(bx + 0.1 * (pts[4][0] - bx), bz + 0.1 * (pts[4][1] - bz)), tip], M["ink"])      # the facet edge
    return tip


def node_vitriol(d, M, state, k=0):
    """Big green vitriol-glass shards jutting from a low basalt crag; harvested: snapped stubs."""
    full = state != "harvested"
    top_z = crag(d, M, 0.80, 0.50 if full else 0.40, 31)
    shards = [(-0.42, 0.46, -32, 0.13), (0.44, 0.42, 34, 0.12), (-0.15, 0.80, -9, 0.19), (0.18, 0.64, 14, 0.17), (0.02, 0.38, 2, 0.14)]
    spots = []
    for x, ln, a_deg, w in shards:
        bz = top_z(x) - 0.08
        if full:
            tip = _glass(d, M, x, bz, ln, a_deg, w)
            spots.append((tip[0] * 0.92 + x * 0.08, tip[1] - 0.08))
        else:
            _glass(d, M, x, bz, 0.13, a_deg, w)
    return spots


def node_sulfur(d, M, state, k=0):
    """A fumarole crag under a thick sulfur crust (lumpy underside), yellow sulfur crystal rosettes, a vent breathing a
    curl of fume; harvested: a stump with a thin crust."""
    full = state != "harvested"
    w, h = (0.80, 0.88) if full else (0.68, 0.45)
    top_z = crag(d, M, w, h, 32)
    th = 0.20 if full else 0.08
    xs = [-w * 0.93 + 1.86 * w * i / 40 for i in range(41)]
    upper = [(x, top_z(x) + 0.035) for x in xs]
    lower = [(x, top_z(x) - th - 0.05 * max(0.0, math.sin(10 * x + 1.2)) ** 2) for x in xs]
    G.stroke(d, upper + lower[::-1], M["sulfur"], 0.0, cyclic=True)
    G.stroke(d, [(x, z + 0.045) for x, z in lower] + lower[::-1], M["sulfur_sh"], 0.0, cyclic=True)
    G.stroke(d, upper, M["ink"], O)
    G.stroke(d, lower, M["ink"], I)
    spots = []
    if full:
        for j, x in enumerate((-0.38, 0.33)):
            spots.append(_rosette(d, M, x, top_z(x) + 0.01, 0.13, 90 + j, role="sulfur_i")[2])
        vz = top_z(0.0) + 0.03                                                               # the vent and its fume
        G.stroke(d, G.lumpy_ellipse(0.0, vz, 0.09, 0.035, n=14, lump=0.0), M["vent_i"], I, cyclic=True)
        for j, (x, z, r) in enumerate(((0.03, vz + 0.11, 0.065), (0.10, vz + 0.22, 0.05), (0.05, vz + 0.31, 0.035))):
            G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.85, n=12, lump=0.12, seed=j), M["fume_i"], I, cyclic=True)
    return spots


def draw_capsule(d, M, k):
    """Venus's relic: an old brass pressure capsule half-buried in the crust, a red band, a flared petal skirt, one hatch
    outline off-centre (no portholes: no face, D-101), the lamp on its antenna's tip."""
    for a in (-0.9, -0.3, 0.3, 0.9):                                                          # the petal skirt behind
        px, pz = 0.38 * math.sin(a), -0.10 - 0.06 * math.cos(a)
        G.stroke(d, [(0.12 * math.sin(a), -0.04), (px - 0.07, pz), (px + 0.06, pz - 0.04)], M["petal_i"], I, cyclic=True)
    ball = G.lumpy_ellipse(0.0, 0.06, 0.30, 0.29, n=32, lump=0.01, seed=11)
    G.stroke(d, ball, M["capsule"], 0.0, cyclic=True)
    G.stroke(d, _arc_pts(0.0, 0.06, 0.29, 0.28, math.pi * 0.95, math.pi * 1.6) + [(-0.02, 0.02)], M["capsule_sh"], 0.0, cyclic=True)
    G.stroke(d, [(-0.30, 0.02), (0.30, 0.02), (0.30, 0.08), (-0.30, 0.08)], M["stripe"], 0.0, cyclic=True)
    G.stroke(d, ball, M["ink"], O, cyclic=True)
    G.seam(d, [(-0.29, 0.02), (0.29, 0.02)], M["ink"])
    G.seam(d, [(-0.29, 0.08), (0.29, 0.08)], M["ink"])
    G.stroke(d, [(0.08, 0.14), (0.22, 0.13), (0.21, 0.27), (0.09, 0.27)], M["ink"], I, cyclic=True)   # a hatch outline
    G.seam(d, [(-0.05, 0.33), (-0.10, 0.48)], M["ink"], radius=O)                             # the antenna
    lit = k > 0 and k % 2 == 1
    G.stroke(d, G.lumpy_ellipse(-0.105, 0.51, 0.035, 0.035, n=12, lump=0.0), M["lamp_on_i" if lit else "lamp_i"], I, cyclic=True)
    G.stroke(d, [(-0.5, -0.34), (0.5, -0.38), (0.5, -0.14), (-0.5, -0.08)], M["soil"], 0.0, cyclic=True)
    G.seam(d, [(-0.5, -0.08), (0.5, -0.14)], M["ink"])
    if k > 0 and k % 4 == 2:
        star(d, M, 0.20, 0.30, 0.07)


def _arc_pts(c, zc, rx, rz, a0, a1, n=16):
    return [(c + rx * math.cos(a0 + (a1 - a0) * i / n), zc + rz * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


# ---------------------------------------------------------------- B-219: the giants' nodes on their floes (LEAD 00:2x)
# Each sits on the floe's top (pivot 0.5, 6/96); a low floe-ice mound under it ("rock" = the giant's pale floe tone); no faces:
# bubbles and pits are many and irregular, never a pair of dark dots.

def _prisms(d, M, prisms, base_z, fill, shade, ink=O):
    """Crystal prisms from a base line: [(x, length, angle_deg, half_width)] -> their tip spots."""
    spots = []
    for x, ln, a_deg, w in prisms:
        a = math.radians(a_deg)
        bx, bz = x, base_z
        tx, tz = bx + ln * math.sin(a), bz + ln * math.cos(a)
        nx, nz = math.cos(a) * w, -math.sin(a) * w
        tip = (tx + 0.45 * w * math.sin(a), tz + 0.45 * w * math.cos(a))
        body = [(bx - nx, bz - nz), (tx - nx, tz - nz), tip, (tx + nx, tz + nz), (bx + nx, bz + nz)]
        G.stroke(d, body, M[fill], 0.0, cyclic=True)
        G.stroke(d, [(bx - nx, bz - nz), (tx - nx, tz - nz), tip, (tx, tz), (bx, bz)], M[shade], 0.0, cyclic=True)
        G.stroke(d, body, M["ink"], ink, cyclic=True)
        G.seam(d, [(bx, bz), (tx, tz), tip], M["ink"])
        spots.append((tx + nx * 0.5, tz + nz * 0.5))
    return spots


def node_ammonia_ice(d, M, state, k=0):
    """Jupiter, deck 1: a cluster of pale, chunky ammonia-ice crystals with slate-blue inner faces and frosted tips."""
    mound(d, M, 0.66, 0.20, 31)
    full = state != "harvested"
    prisms = [(-0.34, 0.50, -18, 0.10), (-0.10, 0.80, -6, 0.13), (0.14, 0.64, 9, 0.12), (0.36, 0.44, 24, 0.10), (-0.50, 0.30, -30, 0.08),
              (0.50, 0.26, 34, 0.07)]
    if not full:
        prisms = [(x, 0.16, a, w) for x, _l, a, w in prisms[1:4]]
    spots = _prisms(d, M, prisms, 0.12, "crystal", "crystal_tint")
    if full:
        for x, z in ((-0.12, 0.98), (0.17, 0.82), (-0.38, 0.66)):                          # frost on the tips
            G.stroke(d, G.lumpy_ellipse(x, z, 0.05, 0.025, n=10, lump=0.15, seed=int(x * 100) + 5), M["crystal"], 0.0, cyclic=True)
    return spots if full else []


def node_metallic_hydrogen(d, M, state, k=0):
    """Jupiter, the deep: a dark pressure shell banded red and gold, split open, silver liquid-metal beads bulging from the
    split and a few run down onto the floe; harvested: the cracked shell, empty but for one bead."""
    full = state != "harvested"
    w, h = (0.80, 1.00) if full else (0.72, 0.62)
    top_z = crag(d, M, w, h, 33, mat="shell")
    for j, (zf, mat) in enumerate(((0.62, "band"), (0.40, "band2"))):                       # the pressure bands across the shell
        xs = [-w * 0.92 + 1.84 * w * i / 24 for i in range(25)]
        up = [(x, min(top_z(x) - 0.03, h * zf + 0.05 + 0.04 * math.sin(3 * x + j))) for x in xs]
        lo = [(x, min(top_z(x) - 0.06, h * zf - 0.03 + 0.04 * math.sin(3 * x + j))) for x in xs]
        G.stroke(d, up + lo[::-1], M[mat], 0.0, cyclic=True)
        G.stroke(d, up, M["ink"], I)
        G.stroke(d, lo, M["ink"], I)
    split = [(-0.10, 0.10), (-0.18, h * 0.45), (-0.04, h * 0.78), (0.14, h * 0.50), (0.08, 0.10)]       # the split
    G.stroke(d, split, M["shell_sh"], 0.0, cyclic=True)
    G.stroke(d, split, M["ink"], O, cyclic=True)
    beads = [(-0.04, h * 0.55, 0.12), (0.06, h * 0.34, 0.10), (-0.10, h * 0.30, 0.08), (0.02, h * 0.18, 0.07), (0.30, 0.06, 0.06),
             (0.42, 0.045, 0.045), (-0.36, 0.05, 0.05)] if full else [(-0.02, h * 0.3, 0.07)]
    spots = []
    for x, z, r in beads:                                                                    # silver beads: round, a bright cap
        G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.94, n=18, lump=0.02, seed=int(x * 100) + 9), M["metal"], 0.0, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x - r * 0.2, z - r * 0.25, r * 0.65, r * 0.5, n=12, lump=0.0), M["metal_sh"], 0.0, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x + r * 0.3, z + r * 0.38, r * 0.32, r * 0.2, n=8, lump=0.0), M["metal_hi"], 0.0, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.94, n=18, lump=0.02, seed=int(x * 100) + 9), M["ink"], I, cyclic=True)
        spots.append((x + r * 0.3, z + r * 0.38))
    if not full:
        for x in (-0.45, 0.35):
            G.seam(d, [(x - 0.07, top_z(x) - 0.04), (x, top_z(x) - 0.12), (x + 0.07, top_z(x) - 0.04)], M["ink"])
    return spots


def _slab(d, M, cx, cz, w, h, tilt, fill, shade, hi, seed, ink=O):
    """An angular chunk (a ring fragment): a skewed box with a lit top and a shaded side."""
    rnd = random.Random(seed)
    ca, sa = math.cos(tilt), math.sin(tilt)
    R = lambda u, v: (cx + u * ca - v * sa, cz + u * sa + v * ca)  # noqa: E731
    j = lambda: rnd.uniform(-0.15, 0.15)  # noqa: E731
    body = [R(-w * (1 + j() * 0.3), -h), R(w * (1 + j() * 0.3), -h), R(w * (0.9 + j() * 0.3), h), R(-w * (0.85 + j() * 0.3), h * (1 + j() * 0.2))]
    G.stroke(d, body, M[fill], 0.0, cyclic=True)
    G.stroke(d, [body[0], body[1], R(w * 0.9, -h * 0.2), R(-w * 0.9, -h * 0.35)], M[shade], 0.0, cyclic=True)
    G.stroke(d, [body[3], body[2], R(w * 0.7, h * 0.65), R(-w * 0.6, h * 0.7)], M[hi], 0.0, cyclic=True)
    G.stroke(d, body, M["ink"], ink, cyclic=True)
    return R(w * 0.4, h * 0.6)


def node_ring_ice(d, M, state, k=0):
    """Saturn, deck 1: a heap of angular ring-ice fragments, offwhite with blue shading and cracks."""
    mound(d, M, 0.66, 0.16, 41)
    full = state != "harvested"
    chunks = [(-0.36, 0.30, 0.20, 0.15, 0.25), (0.20, 0.28, 0.24, 0.16, -0.18), (-0.06, 0.62, 0.22, 0.17, 0.10), (0.42, 0.62, 0.14, 0.12, -0.4),
              (-0.42, 0.66, 0.12, 0.10, 0.5)] if full else [(-0.10, 0.22, 0.16, 0.10, 0.2), (0.24, 0.18, 0.12, 0.08, -0.3)]
    spots = []
    for j, (x, z, w, h, t) in enumerate(chunks):
        spots.append(_slab(d, M, x, z, w, h, t, "ice", "ice_sh", "ice", 50 + j))
        G.seam(d, [(x - w * 0.3, z + h * 0.4), (x, z), (x + w * 0.2, z - h * 0.3)], M["ink"])
    return spots


def node_ring_rock(d, M, state, k=0):
    """Saturn, deck 2: ring-rubble boulders, dusty tan-grey, their tops crusted with ice."""
    mound(d, M, 0.68, 0.16, 43)
    full = state != "harvested"
    rocks = [(-0.34, 0.30, 0.24), (0.22, 0.30, 0.26), (-0.04, 0.70, 0.22), (0.46, 0.18, 0.13), (-0.56, 0.16, 0.11)] if full else [(0.0, 0.24, 0.18)]
    spots = []
    for j, (x, z, r) in enumerate(rocks):
        rnd = random.Random(60 + j)
        pts = _poly(x, z, r, rnd, sides=7, flat=0.82, lift=0.10)
        G.stroke(d, pts, M["rrock"], 0.0, cyclic=True)
        G.stroke(d, [p for p in pts if p[0] < x] + [(x, z - r * 0.5)], M["rrock_sh"], 0.0, cyclic=True)
        crust = [(x - r * 0.75, z + r * 0.35), (x - r * 0.3, z + r * 0.72), (x + r * 0.35, z + r * 0.7), (x + r * 0.8, z + r * 0.3),
                 (x + r * 0.4, z + r * 0.42), (x - r * 0.2, z + r * 0.5)]
        G.stroke(d, crust, M["rrock_hi"], 0.0, cyclic=True)                                  # the ice crust on top
        G.stroke(d, pts, M["ink"], O, cyclic=True)
        G.seam(d, [(x - r * 0.2, z - r * 0.1), (x + r * 0.15, z + r * 0.2)], M["ink"])
        spots.append((x + r * 0.3, z + r * 0.55))
    return spots


def node_helium3(d, M, state, k=0):
    """Saturn, the deep: a low vent cone, its rim crusted with frost, pale rose helium-3 condensate pooled round the mouth and
    a soft rose puff over it; harvested: the frost rim, the mouth dry, no puff."""
    full = state != "harvested"
    w, h = 0.78, 0.46
    xs = [-w + 2 * w * i / 30 for i in range(31)]
    cone = [(x, h * (1 - (abs(x) / w) ** 1.6)) for x in xs]
    cone = [(x, min(z, h * 0.86)) for x, z in cone]
    G.stroke(d, cone + [(w, -0.02), (-w, -0.02)], M["vent"], 0.0, cyclic=True)
    G.stroke(d, [(x, z * 0.7) for x, z in cone if x < -0.1] + [(-0.1, -0.02), (-w, -0.02)], M["vent_sh"], 0.0, cyclic=True)
    G.stroke(d, cone, M["ink"], O)
    mz = h * 0.86
    G.stroke(d, G.lumpy_ellipse(0.0, mz, 0.24, 0.06, n=20, lump=0.03, seed=3), M["mouth"], 0.0, cyclic=True)         # the mouth
    rim = [(0.30 * math.cos(a) * (1 + 0.12 * math.sin(7 * a)), mz + 0.085 * math.sin(a)) for a in [TAU * i / 28 for i in range(28)]]
    inner = [(0.22 * math.cos(a), mz + 0.05 * math.sin(a)) for a in [TAU * i / 28 for i in range(28)]]
    G.stroke(d, rim + [rim[0]] + [inner[0]] + inner[::-1], M["frost"], 0.0, cyclic=True)                              # frost rim
    G.stroke(d, rim, M["ink"], I, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, mz, 0.24, 0.06, n=20, lump=0.03, seed=3), M["ink"], I, cyclic=True)
    spots = [(0.18, mz + 0.06)]
    if full:
        for x, z, r in ((-0.42, 0.10, 0.08), (0.38, 0.14, 0.07), (-0.2, 0.32, 0.06)):           # condensate pooled on the cone
            G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.55, n=12, lump=0.1, seed=int(x * 50) + 7), M["rose"], I, cyclic=True)
            spots.append((x + r * 0.3, z + r * 0.2))
        puff = [(-0.12, mz + 0.22, 0.13), (0.06, mz + 0.30, 0.15), (0.20, mz + 0.20, 0.11), (-0.02, mz + 0.48, 0.10)]   # the rose puff
        for x, z, r in puff:
            G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.85, n=16, lump=0.05, seed=int(z * 40)), M["rose"], O * 0.8, cyclic=True)
        for x, z, r in puff:
            G.stroke(d, G.lumpy_ellipse(x, z, r - 0.02, (r - 0.02) * 0.85, n=16, lump=0.05, seed=int(z * 40)), M["rose"], 0.0, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(0.10, mz + 0.36, 0.05, 0.025, n=8, lump=0.0), M["rose_hi"], 0.0, cyclic=True)
        spots.append((0.08, mz + 0.40))
    return spots


def node_methane_ice(d, M, state, k=0):
    """Uranus / Neptune, deck 1: a rounded mound of methane clathrate, frosted on top, pocked with many small pale bubbles."""
    mound(d, M, 0.66, 0.16, 47)
    full = state != "harvested"
    h = 0.66 if full else 0.34
    xs = [-0.56 + 1.12 * i / 30 for i in range(31)]
    top = [(x, 0.10 + h * (1 - (x / 0.56) ** 2) ** 0.55 + 0.025 * math.sin(8 * x)) for x in xs]
    G.stroke(d, top + [(0.56, 0.08), (-0.56, 0.08)], M["meth"], 0.0, cyclic=True)
    G.stroke(d, [(x, 0.10 + (z - 0.10) * 0.5) for x, z in top if x < 0.0] + [(0.0, 0.08), (-0.56, 0.08)], M["meth_sh"], 0.0, cyclic=True)
    cap = [(x, z) for x, z in top if abs(x) < 0.42]                                          # the frosted cap, scalloped
    G.stroke(d, cap + [(cap[-1][0], cap[-1][1] - 0.08)] + [(x, z - 0.07 - 0.03 * math.sin(14 * x)) for x, z in cap[::-1]], M["meth_hi"], 0.0, cyclic=True)
    G.stroke(d, top, M["ink"], O)
    rnd = random.Random(77)
    spots = []
    for j in range(9 if full else 4):                                                        # many pale bubbles (never a pair)
        x = rnd.uniform(-0.40, 0.40)
        zt = 0.10 + h * (1 - (x / 0.56) ** 2) ** 0.55
        z = rnd.uniform(0.16, max(0.18, zt - 0.14))
        r = rnd.uniform(0.022, 0.045)
        G.stroke(d, G.lumpy_ellipse(x, z, r, r, n=10, lump=0.0), M["meth_hi"], I * 0.7, cyclic=True)
        if j < 3:
            spots.append((x, z))
    return spots if full else []


def _cube(d, M, cx, cz, s, tilt, fill, shade, hi):
    """A cubic crystal in a three-quarter view: the top face lit, the left face the body tone, the right face shaded; nested ink
    squares on the faces stand for the inner glow (ink only, no glow)."""
    ca, sa = math.cos(tilt), math.sin(tilt)
    R = lambda u, v: (cx + u * ca - v * sa, cz + u * sa + v * ca)  # noqa: E731
    a, b, c = s, s * 0.55, s * 0.95                                                          # half width, depth skew, height
    top = [R(-a, c), R(-a + b, c + b * 0.6), R(a + b, c + b * 0.6), R(a, c)]
    left = [R(-a, 0), R(a, 0), R(a, c), R(-a, c)]
    right = [R(a, 0), R(a + b, b * 0.6), R(a + b, c + b * 0.6), R(a, c)]
    G.stroke(d, left, M[fill], 0.0, cyclic=True)
    G.stroke(d, right, M[shade], 0.0, cyclic=True)
    G.stroke(d, top, M[hi], 0.0, cyclic=True)
    for face in (left, right, top):
        G.stroke(d, face, M["ink"], O * 0.8, cyclic=True)
    fx, fz = (left[0][0] + left[2][0]) / 2, (left[0][1] + left[2][1]) / 2                      # the inner squares on the front face
    for q in (0.55, 0.28):
        G.stroke(d, [(fx + (p[0] - fx) * q, fz + (p[1] - fz) * q) for p in left], M["ink"], I * 0.6, cyclic=True)
    return R(a * 0.3, c + b * 0.3)


def node_superionic_ice(d, M, state, k=0):
    """Uranus (the deep) / Neptune (deck 3): a cluster of cubic superionic crystals, inked heavily, inner squares for the glow."""
    mound(d, M, 0.62, 0.16, 49)
    full = state != "harvested"
    cubes = [(-0.30, 0.12, 0.17, 0.12), (0.12, 0.12, 0.22, -0.06), (-0.06, 0.48, 0.15, 0.22), (0.40, 0.12, 0.12, -0.25), (0.26, 0.48, 0.10, -0.3)] \
        if full else [(-0.06, 0.10, 0.12, 0.1)]
    return [_cube(d, M, x, z, s, t, "super", "super_sh", "super_hi") for x, z, s, t in cubes]


def _octa(d, M, cx, cz, s, buried, fill, shade, deep):
    """A diamond (an octahedron's silhouette) half-buried in the floe: only the part above `buried` (0..1 of its height) shows."""
    top, mid_l, mid_r, bot = (cx, cz + s), (cx - s * 0.7, cz), (cx + s * 0.7, cz), (cx, cz - s)
    cut = cz - s + 2 * s * buried
    def clip(poly):
        return [(x, max(z, cut)) for x, z in poly]
    G.stroke(d, clip([top, mid_l, bot, mid_r]), M[fill], 0.0, cyclic=True)
    G.stroke(d, clip([top, (cx, cz), bot, mid_r]), M[shade], 0.0, cyclic=True)
    G.stroke(d, clip([(cx, cz), mid_r, bot]), M[deep], 0.0, cyclic=True)
    G.stroke(d, clip([top, mid_l, bot, mid_r]), M["ink"], O * 0.8, cyclic=True)
    G.seam(d, clip([mid_l, (cx, cz), mid_r]), M["ink"])
    G.seam(d, clip([top, (cx, cz)]), M["ink"])
    return (cx - s * 0.2, cz + s * 0.55)


def node_deep_diamond(d, M, state, k=0):
    """Neptune, the deep: diamond hail half-buried in a patch of floe crust: a big stone and a scatter of small ones."""
    full = state != "harvested"
    mound(d, M, 0.74, 0.14, 51)
    stones = [(0.0, 0.28, 0.26, 0.42), (-0.40, 0.17, 0.13, 0.4), (0.38, 0.16, 0.12, 0.35), (-0.18, 0.12, 0.08, 0.3), (0.56, 0.08, 0.07, 0.3),
              (-0.58, 0.08, 0.06, 0.3), (0.20, 0.10, 0.07, 0.35)] if full else [(0.30, 0.10, 0.08, 0.35)]
    spots = []
    for x, z, s, b in stones:
        spots.append(_octa(d, M, x, z, s, b, "diamond", "diamond_sh", "diamond_dp"))
    if not full:                                                                             # the pits the hail left
        for x in (-0.32, 0.02, -0.55):
            G.stroke(d, G.lumpy_ellipse(x, 0.12, 0.09, 0.03, n=12, lump=0.08, seed=int(x * 100) + 3), M["pit"], I, cyclic=True)
    return spots


GIANTS = ("jupiter", "saturn", "uranus", "neptune")
GIANT_DECK = {"jupiter": {"ammonia_ice": "deck1", "metallic_hydrogen": "deep"},           # where U-189 places each (deeper = rarer)
              "saturn": {"ring_ice": "deck1", "ring_rock": "deck2", "helium3": "deep"},
              "uranus": {"methane_ice": "deck1", "superionic_ice": "deep"},
              "neptune": {"methane_ice": "deck1", "superionic_ice": "deck3", "deep_diamond": "deep"}}
ITEM_OF = {"helium3": "helium3_condensate"}                                                # the node's name -> the item it drops


PLANET_NODES = {"earth": {"iron": node_iron, "copper": node_copper, "carbon": node_carbon, "silica": node_silica, "water_ice": node_water_ice},
                "mars": {"hematite": node_hematite, "perchlorate": node_perchlorate, "water_ice": node_mars_ice},
                "mercury": {"solarite": node_solarite, "nickel": node_nickel},
                "venus": {"vitriol_glass": node_vitriol, "sulfur": node_sulfur},
                "jupiter": {"ammonia_ice": node_ammonia_ice, "metallic_hydrogen": node_metallic_hydrogen},
                "saturn": {"ring_ice": node_ring_ice, "ring_rock": node_ring_rock, "helium3": node_helium3},
                "uranus": {"methane_ice": node_methane_ice, "superionic_ice": node_superionic_ice},
                "neptune": {"methane_ice": node_methane_ice, "superionic_ice": node_superionic_ice, "deep_diamond": node_deep_diamond}}
NODES = PLANET_NODES["earth"]


def draw_node(item, planet="earth"):
    def fn(d, M, k):
        state = "full" if k == 0 else ("harvested" if k == 1 else "glint")
        spots = PLANET_NODES[planet][item](d, M, "harvested" if state == "harvested" else "full", k)
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
        elif item == "hematite":                                                             # a nest of hematite spherules
            for j in range(9):
                x, z, r = rnd.uniform(-0.34, 0.34), rnd.uniform(-0.24, 0.20), rnd.uniform(0.06, 0.09)
                G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.92, n=12, lump=0.04, seed=j), M["hem_i"], I, cyclic=True)
                G.stroke(d, G.lumpy_ellipse(x + r * 0.3, z + r * 0.35, r * 0.25, r * 0.2, n=8, lump=0.0), M["hem_hi"], 0.0, cyclic=True)
                spots.append((x + r * 0.3, z + r * 0.35))
        elif item == "perchlorate":                                                          # salt crystal rosettes
            for j, (x, z) in enumerate(((-0.25, -0.22), (0.05, -0.26), (0.30, -0.16), (-0.05, 0.04))):
                spots.append(_rosette(d, M, x, z, 0.16, 70 + j)[2])
        elif item == "solarite":                                                             # golden prisms packed in the pocket
            for j, (x, a_deg) in enumerate(((-0.26, -22), (-0.02, -4), (0.20, 14), (0.36, 32))):
                spots.append(_prism(d, M, x, -0.30, 0.32 if j % 2 else 0.40, a_deg, 0.065, "solar", "solar_sh"))
        elif item == "nickel":                                                               # nickel-iron nuggets
            for j in range(6):
                x, z, r = rnd.uniform(-0.32, 0.32), rnd.uniform(-0.22, 0.18), rnd.uniform(0.08, 0.12)
                G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.8, n=14, lump=0.08, seed=j), M["nickel_i"], I, cyclic=True)
                G.stroke(d, G.lumpy_ellipse(x + r * 0.3, z + r * 0.3, r * 0.3, r * 0.2, n=8, lump=0.0), M["nickel_hi"], 0.0, cyclic=True)
                spots.append((x + r * 0.3, z + r * 0.3))
        elif item == "vitriol_glass":                                                        # glass shards packed in the pocket
            for j, (x, a_deg, ln) in enumerate(((-0.26, -24, 0.36), (-0.02, -6, 0.46), (0.22, 16, 0.38), (0.38, 34, 0.26))):
                spots.append(_glass(d, M, x, -0.32, ln, a_deg, 0.09, ink=I))
        elif item == "sulfur":                                                               # sulfur crystal rosettes
            for j, (x, z) in enumerate(((-0.25, -0.22), (0.05, -0.26), (0.30, -0.16), (-0.05, 0.04))):
                spots.append(_rosette(d, M, x, z, 0.16, 95 + j, role="sulfur_i")[2])
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


def draw_x_pale(d, M, k):
    """scan_x_pale (LEAD 05:4x): the same X in cream with dark ink edges, for grounds where the red one vanishes (Mars...)."""
    draw_x(d, M, k, fill="xpale", shade="xpale_sh")


def draw_x(d, M, k, fill="xred", shade="xred_sh"):
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
        G.stroke(d, stroke_, M[fill], 0.0, cyclic=True)
        G.stroke(d, [stroke_[0], stroke_[1], ((stroke_[0][0] + stroke_[1][0]) / 2, (stroke_[0][1] + stroke_[1][1]) / 2 - 0.01)], M[shade], 0.0, cyclic=True)
        G.stroke(d, stroke_, M["ink"], O, cyclic=True)
        G.seam(d, [(-L * ux * 0.6 + w * nx * 0.3, cz - L * uz * 0.6 + w * nz * 0.3), (L * ux * 0.5 + w * nx * 0.3, cz + L * uz * 0.5 + w * nz * 0.3)], M["ink"])   # a brush streak
    G.stroke(d, G.lumpy_ellipse(0.0, 0.02, 0.26 * s, 0.035, n=20, lump=0.02, seed=2), M[shade], 0.0, cyclic=True)   # its shadow on the ground


# ---------------------------------------------------------------- the table

RELICS = {"earth": {"data_cache": (draw_cache, 96, 80, (0.5, 0.5), [("full", 1, False), ("glint", 8, True)]),
                    "vault_door": (draw_vault, 128, 128, (0.5, 0.5), [("closed", 1, False), ("open", 6, False)]),
                    "scan_x": (draw_x, 64, 64, (0.5, 6 / 64), [("pulse", 8, True)])},
          "mars": {"lander_beacon": (draw_beacon, 96, 96, (0.5, 0.5), [("full", 1, False), ("glint", 8, True)]),
                   "scan_x_pale": (draw_x_pale, 64, 64, (0.5, 6 / 64), [("pulse", 8, True)])},
          "mercury": {"sunshade_probe": (draw_sunprobe, 96, 96, (0.5, 0.5), [("full", 1, False), ("glint", 8, True)])},
          "venus": {"pressure_capsule": (draw_capsule, 96, 96, (0.5, 0.5), [("full", 1, False), ("glint", 8, True)]),
                    "scan_x": (draw_x, 64, 64, (0.5, 6 / 64), [("pulse", 8, True)]),
                    "scan_x_pale": (draw_x_pale, 64, 64, (0.5, 6 / 64), [("pulse", 8, True)])}}
RELIC_AT = {"earth": {"data_cache": (1450, 120), "vault_door": (1700, 250), "scan_x": (660, 2)}, "mars": {"lander_beacon": (1450, 150), "scan_x_pale": (1000, 2)},
            "mercury": {"sunshade_probe": (1450, 150), "scan_x": (1000, 2)},
            "venus": {"pressure_capsule": (1450, 150), "scan_x": (1000, 2), "scan_x_pale": (1150, 2)}}
_PC = {}


def pieces_for(planet):
    """The planet's keys: node_<item> and pocket_<item> per node, then its relics."""
    if planet not in _PC:
        P = {}
        for it in PLANET_NODES[planet]:
            P[f"node_{it}"] = (draw_node(it, planet), 128, 96, (0.5, 6 / 96), [("full", 1, False), ("harvested", 1, False), ("glint", 8, True)])
            if planet not in GIANTS:                                                         # B-219: the giants' floes have nodes only
                P[f"pocket_{it}"] = (draw_pocket(it), 96, 96, (0.5, 0.5), [("full", 1, False), ("glint", 8, True)])
        P.update(RELICS.get(planet, {}))
        _PC[planet] = P
    return _PC[planet]


PIECES = pieces_for("earth")


def render(name, planet="earth", piece=None):
    fn, fw, fh, piv, clips = piece or pieces_for(planet)[name]
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


def sheet_meta(name, frames, planet="earth", piece=None):
    import numpy as np
    _fn, fw, fh, piv, clips = piece or pieces_for(planet)[name]
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


def preview(out_dir, planet="earth", S=None, out=None, footnote=None):
    """Earth's B-175 ground (band + fill from Art) flat at 1x: the five nodes on the surface beside the surveyor (full,
    harvested), the pockets, the cache and the vault door in the cutaway, the X above a pocket; every clip; the checks."""
    if planet in GIANTS:
        return preview_giant(out_dir, planet, S=S, out=out, footnote=footnote)
    import json
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    PC = pieces_export(planet) if S is not None else pieces_for(planet)
    res = S if S is not None else {n: render(n, planet) for n in PC}
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
    nodes = list(PLANET_NODES[planet])
    xs = [150 + 270 * i for i in range(len(nodes))]
    for (name, x) in zip(nodes, xs):
        place(res[f"node_{name}"][0][0], (0.5, 6 / 96), x, surf + 2)
        place(res[f"node_{name}"][0][1], (0.5, 6 / 96), x + 140, surf + 2)
        review._label(img, f"{name}: full | harvested", x - 60, surf - 120)
    for j, name in enumerate(nodes):
        place(res[f"pocket_{name}"][0][0], (0.5, 0.5), 160 + 250 * j, surf + 230)
    placed = set()
    for name, (x, y) in RELIC_AT[planet].items():
        nm = name if name in PC else ("scan_x" if name.startswith("scan_x") else None)
        if nm is None or nm in placed:
            continue
        placed.add(nm)
        place(res[nm][0][0], PC[nm][3], x, surf + y)
    try:
        sm = json.load(open(os.path.join(ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
        shs = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))
        fr = shs[:sm["frame_height"], :sm["frame_width"]]
        review._over(img, fr, 1550, surf - sm["frame_height"] + int(round(sm["pivot"][1] * sm["frame_height"])) + 2)
    except (OSError, KeyError, ValueError):
        pass
    review._label(img, f"b-176 {planet} nodes at 1x on its b-175 ground ({'exported, U-158 keys' if S is not None else 'keys provisional, renamed at export'}): {len(nodes)} nodes full | harvested; "
                       f"their pockets and {', '.join(RELIC_AT[planet])} in the cutaway", 6, 6)
    rows = [img]
    for name, (fn, fw, fh, piv, clips) in PC.items():
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
    for name in PC:
        frames, widths = res[name]
        sheet, meta, probs = sheet_meta(name, frames, planet, PC[name])
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
    review.draw(out_img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp)"), 2, out_img.shape[0] - 16, (1.0, 1.0, 0.85))
    shape = out_img.shape
    np.clip(out_img, 0.0, 1.0, out=out_img)
    out_img *= 255.0
    np.rint(out_img, out=out_img)
    u8 = np.empty(shape[:2] + (4,), np.uint8)
    u8[..., :3] = out_img
    u8[..., 3] = 255
    del out_img
    out = out or os.path.join(out_dir, f"review_b176_{planet}_nodes_preview.png")
    pngio.write_png(out, u8)
    print("written", out, shape[1], "x", shape[0])
    for ln in lines:
        print(ln)




def preview_giant(out_dir, planet, S=None, out=None, footnote=None):
    """B-219: the giant's nodes on its floe (terrain/<giant>/floe_strip_ice, caps at both ends, the fill continued below) at 1x
    beside the surveyor, full | harvested, labelled with their deck; every clip as a strip; the per-key checks."""
    import json
    import time
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    PC = pieces_export(planet) if S is not None else pieces_for(planet)
    res = S if S is not None else {n: render(n, planet) for n in PC}
    W, SH, surf = 1900, 520, 300
    sky = np.array(v3.hex_rgb(v3.PALETTES[planet]["sky"]), np.float32) / 255.0
    img = np.empty((SH, W, 3), np.float32)
    img[:] = sky
    fj = json.load(open(os.path.join(ART, "terrain", planet, "floe_strip_ice.json"), encoding="utf-8"))
    fs = pngio.read_png_np(os.path.join(ART, "terrain", planet, "floe_strip_ice_color.png"))
    fw, fh, cols, g = fj["frame_width"], fj["frame_height"], fj["columns"], fj.get("gutter", 4)
    fr = []
    for i in range(fj["frames"]):
        r, c = divmod(i, cols)
        fr.append(fs[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw])
    gl = fj.get("ground_line_px", int(round(fh * (1 - fj["pivot"][1]))))
    caps = fj.get("caps", {})
    ncol = (W - 40) // fw
    for c in range(ncol):
        f = fr[caps.get("cap_left", 8)] if c == 0 else fr[caps.get("cap_right", 9)] if c == ncol - 1 else fr[(c - 1) % 8]
        review._over(img, f, 20 + c * fw, surf - gl)
        for q in range(4):                                                                   # the floe's fill below (the bottom 8 px)
            review._over(img, f[-8:], 20 + c * fw, surf - gl + fh + 8 * q)

    def place(im, piv, x, y):
        h, w = im.shape[:2]
        review._over(img, im, int(x - piv[0] * w), int(y - (1 - piv[1]) * h))
    nodes = list(PLANET_NODES[planet])
    for i, name in enumerate(nodes):
        x = 140 + 430 * i
        place(res[f"node_{name}"][0][0], (0.5, 6 / 96), x, surf + 2)
        place(res[f"node_{name}"][0][1], (0.5, 6 / 96), x + 150, surf + 2)
        review._label(img, f"{name} ({GIANT_DECK[planet][name]}): full | harvested", x - 60, surf - 130, scale=1)
    try:
        sm = json.load(open(os.path.join(ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
        shs = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))
        review._over(img, shs[:sm["frame_height"], :sm["frame_width"]], W - 260,
                     surf - sm["frame_height"] + int(round(sm["pivot"][1] * sm["frame_height"])) + 2)
    except (OSError, KeyError, ValueError):
        pass
    review._label(img, f"b-219 {planet}'s nodes at 1x on its floe (floe_strip_ice), full | harvested, beside the surveyor; deeper decks rarer (u-189 places them)", 6, 6)
    rows = [img]
    for name, (fn, fw_, fh_, piv, clips) in PC.items():
        frames = res[name][0]
        row = np.empty((fh_ + 34, W, 3), np.float32)
        row[:] = review.PAPER
        for i, im in enumerate(frames):
            xx = 8 + i * (fw_ + 6)
            if xx + fw_ > W:
                break
            row[24:24 + fh_, xx:xx + fw_] = sky
            review._over(row, im, xx, 24)
        review._label(row, f"{name} {fw_}x{fh_}: " + ", ".join(f"{c} {n_}" for c, n_, _l in clips), 6, 4)
        rows.append(row)
    lines = []
    for name in PC:
        frames, widths = res[name]
        sheet, meta, probs = sheet_meta(name, frames, planet, PC[name])
        o = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
        n_ = [w for w in widths if w[0] < v3.OUTER_SPLIT]
        rng = lambda q: f"{min(w[1] for w in q):.1f}-{max(w[2] for w in q):.1f}" if q else "-"  # noqa: E731
        pal = v3.palette_hits(sheet, planet)[0] * 100
        lines.append(f"{name}: sheet {sheet.shape[1]}x{sheet.shape[0]}, ink {rng(o)} / {rng(n_)} px, palette {pal:.1f}%, "
                     f"json {'valid' if not probs else 'INVALID: ' + '; '.join(probs)[:70]}")
    foot = np.empty((30 + 16 * len(lines), W, 3), np.float32)
    foot[:] = review.PAPER
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    out_img = np.vstack(rows + [foot])
    review.draw(out_img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp)"), 2, out_img.shape[0] - 16, (1.0, 1.0, 0.85))
    out = out or os.path.join(out_dir, f"review_b219_{planet}_nodes_preview.png")
    review.write(out, out_img)
    print("written", out, out_img.shape[1], "x", out_img.shape[0])
    for ln in lines:
        print(ln)


# ---------------------------------------------------------------- the export (render.py's ground_strip_set API; U-158's key list,
# UNITY_STATUS 24eab036: props/<planet>/node_<item>, pocket_<item>, the relics, ONE scan_x per planet)

SCAN_PALE = {"mars", "venus"}           # LEAD 05:5x: the pale X where the red one vanishes on the ground


def pieces_export(planet):
    """U-158's keys for the planet: its nodes, pockets and relics, and ONE scan_x (the pale X for Mars and Venus)."""
    P = {n: v for n, v in pieces_for(planet).items() if n not in ("scan_x", "scan_x_pale")}
    if planet not in GIANTS:                                                                 # B-219: no scan X on the floes
        P["scan_x"] = (draw_x_pale if planet in SCAN_PALE else draw_x, 64, 64, (0.5, 6 / 64), [("pulse", 8, True)])
    return P


PLANET = "earth"
KEYS = {}
PE = {}


def use_planet(planet):
    global PLANET, KEYS, PE
    PLANET = planet
    PE = pieces_export(planet)
    KEYS = {n: f"props/{planet}/{n}" for n in PE}


use_planet(PLANET)


def sheets():
    S, allw = {}, []
    for n, piece in PE.items():
        fr, wd = render(n, PLANET, piece)
        S[n] = (fr, wd)
        allw += wd
    return S, allw


def export(art, S=None):
    """-> (out [(key, w, h, bytes)], {}, summary): raises on any contract problem before writing."""
    import json as _json
    from meridian import pngio
    if S is None:
        S, _w = sheets()
    built, problems = [], []
    for n, (frames, _w) in S.items():
        sheet, meta, p = sheet_meta(n, frames, PLANET, PE[n])
        meta.pop("provisional_key", None)
        meta["note"] = ("B-176 / U-158: " + ("a resource node, upright on the curve" if n.startswith("node_") else
                        "a buried find set into the cutaway" if n.startswith("pocket_") else
                        "the Survey scan's X above a find (pale where red vanishes)" if n == "scan_x" else "a relic in the cutaway") + "; no faces")
        if PLANET in GIANTS and n.startswith("node_"):                                       # B-219: where it grows, what it drops
            it = n[len("node_"):]
            meta["note"] = "B-219: a harvestable node on the floe's top (pivot on the floe's surface); deeper decks rarer; no faces"
            meta["deck"] = GIANT_DECK[PLANET][it]
            meta["item"] = ITEM_OF.get(it, it)
        hit, off = v3.palette_hits(sheet, PLANET)
        if hit < 0.98:
            p.append(f"palette {hit * 100:.1f}% (off {' '.join(off[:3])})")
        problems += [f"{n}: {x}" for x in p]
        built.append((n, sheet, meta))
    if problems:
        raise ValueError(f"{PLANET} nodes checks: " + "; ".join(problems))
    d = os.path.join(art, "props", PLANET)
    os.makedirs(d, exist_ok=True)
    out = []
    for n, sheet, meta in built:
        nbytes = pngio.write_png(os.path.join(d, n + "_color.png"), sheet)
        with open(os.path.join(d, n + ".json"), "w", encoding="utf-8", newline="\n") as f:
            _json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((meta["key"], sheet.shape[1], sheet.shape[0], nbytes))
    return out, {}, f"{len(out)} keys (U-158)"


def main(out, S=None, allw=None, footnote=None):
    if S is None:
        S, allw = sheets()
    preview(os.path.dirname(out), PLANET, S=S, out=out, footnote=footnote)


if __name__ == "__main__":
    preview(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "earth")
    fakegp.restore()
