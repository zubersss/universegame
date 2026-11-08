"""B-178 (LEAD 11-08 05:0x, for 0.5.0): Earth's ground band variants on contract 11.9's format, so the desert, beaches,
rocky coast and taiga / tundra stop wearing the grass set (plains and forest keep it). Drawn with gp_draw (fakegp + numpy)
on build_ground_v3's machinery (its wrap, tiling check and curve bend); its verified grass set is untouched.

  terrain/earth/ground_band_sand    512x64, tiles in x (8 m), the ink edge on the surface row 24 = the pivot: desert / beach
                                    sand - low wind ripples, shell bits, a dry tuft, the damp sand under it to a ragged edge
  terrain/earth/ground_band_stone   the same format: coast cliffs and rocky shore - a grey rock crust in jointed slabs with
                                    lichen dots, the topsoil under it
  terrain/earth/ground_band_snow    the same format: taiga / tundra - a white drift crust with a shaded underside over dark soil
  terrain/earth/ground_fill_sand    512x512 world space (standalone, Repeat): pale sandstone strata, cross-bedding, pebbles,
                                    stones - no spot features (D-165); stone and snow keep Earth's ground_fill
  terrain/earth/ground_decor_<variant>_<n>   64x64 upright, pivot at the base (as ground_decor): three per variant

  python -I build_ground_variants_v3.py <preview dir>   lock-free preview: review_b178_earth_ground_variants_preview.png
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ground_v3 as B  # noqa: E402
from meridian import fakegp, v3  # noqa: E402

G, GR = B.G, B.GR
O, I = B.O, B.I
PPU, TAU, ART = B.PPU, B.TAU, B.ART
L = B.BAND_W / PPU
PLANET = "earth"
PLANET_VARIANTS = {"earth": ("sand", "stone", "snow"), "mars": ("frost",)}     # Mars's polar frost: LEAD 05:3x, for U-159
VARIANTS = PLANET_VARIANTS[PLANET]
BIOMES = {"sand": ["desert", "beach"], "stone": ["coast cliffs", "rocky shore"], "snow": ["taiga", "tundra"],
          "frost": ["polar cap", "polar layered terrain"],
          "basalt": ["mars_tharsis"], "talus": ["mars_canyon"],           # B-181: the code's region names (StageRegions / MarsLandforms)
          "ice": ["mercury_cold_trap"], "tessera": ["venus_tessera"], "vent": ["venus_vent_field"]}   # MercuryLandforms.InColdTrap, VenusFeature
DECOR = {"sand": ["dry_tuft", "shells", "sandstone_rock"], "stone": ["lichen_boulder", "shore_pebbles", "thrift"],
         "snow": ["snowy_shrub", "snow_rock", "dry_stalks"], "frost": ["frost_boulder", "ice_blocks", "frost_vent"],
         "basalt": ["vesicular_boulder", "spatter_cone", "tilted_slab"], "talus": ["fallen_block", "scree_fan", "buried_slab"],
         "ice": ["ice_glazed_rock", "ice_ridge", "frosted_pebbles"], "tessera": ["ridge_slab", "grooved_block", "fold_chips"],
         "vent": ["fumarole", "sulfur_rosettes", "vitriol_cluster"]}
FILL_OF = {"sand": "ground_fill_sand", "basalt": "ground_fill_basalt"}   # a variant's own fill (the rest lie over the planet's ground_fill)


def extra_colours():
    P = v3.PALETTES[PLANET]
    sh = lambda k: v3.shadow_of(P[k], PLANET)  # noqa: E731
    dp = lambda k: v3.deep_of(P[k], PLANET)  # noqa: E731
    if PLANET == "mars":
        return {"frost": P["offwhite"], "frost_sh": sh("teal"), "snow": P["offwhite"], "snow_sh": sh("teal"), "ice": P["teal"], "ice_sh": dp("teal"),
                "rock": dp("sky"), "rock_sh": P["brown"], "rock_lit": sh("sky"), "dust": dp("red"), "vent": P["brown"], "plume": P["offwhite"],
                "bas_lit": sh("teal"), "pale": sh("offwhite")}          # B-181 (appended: the frost set's materials keep their order)
    if PLANET == "mercury":                     # B-181: the cold traps' ice (cold-steel teal, an offwhite rim) over the dark shadowed floor
        return {"ice": P["teal"], "ice_sh": sh("teal"), "ice_lit": P["offwhite"], "floor": dp("sky"), "floor_sh": P["brown"],
                "rock": sh("sky"), "rock_sh": dp("sky"), "snow": P["offwhite"], "snow_sh": sh("teal")}
    if PLANET == "venus":                       # B-181: the tesserae's warm grey-brown crust; the vents' sulfur, basalt, embers, vitriol glass
        return {"tess": sh("offwhite"), "tess_sh": dp("sky"), "tess_lit": P["offwhite"], "tess_dp": P["brown"],   # LEAD 10:2x: a lighter warm grey
                "sulfur": P["mustard"], "sulfur_sh": sh("mustard"),
                "black": P["brown"], "ember": P["red"], "ember_core": P["mustard"], "glass": P["green"], "glass_sh": sh("green"),
                "glint": P["offwhite"], "fume": P["offwhite"], "dust": sh("sky")}
    return {"sand": P["mustard"], "sand_sh": sh("mustard"), "cream": P["offwhite"], "sandstone": sh("offwhite"), "rust": sh("red"),
            "shell": P["offwhite"], "shell_pink": sh("red"),
            "rock": sh("sky"), "rock_sh": dp("sky"), "rock_lit": sh("offwhite"), "lichen_y": P["mustard"], "lichen_g": P["green"],
            "lichen_w": P["offwhite"],
            "snow": P["offwhite"], "snow_sh": sh("sky"), "dsoil": P["brown"],
            "twig": P["brown"], "needle": dp("green"), "needle_lit": sh("green"), "thrift": P["red"], "cushion": P["green"],
            "dry": P["mustard"], "dry_sh": sh("mustard")}


def mats(gp):
    M = B.mats(gp, PLANET)
    for k, h in extra_colours().items():
        M[k] = G.mat(gp, f"gv_{k}", fill=h, ink=False)
        M[k + "_i"] = G.mat(gp, f"gv_{k}_i", fill=h)
    C = extra_colours()
    for k in [k for k in ("dry", "dry_sh", "cushion", "needle") if k in C]:
        M[k + "_tuft"] = G.mat(gp, f"gv_{k}_tuft", fill=C[k], ink=True, behind=True)
    return M


def W(fn):
    B.wrapped(fn, L)


def _ragged(seed, base=-0.45):
    return [(x, base + B.per(x, L, 4, seed, 0.06) + 0.025 * math.sin(TAU * 21 * x / L)) for x in [L * i / 160 for i in range(161)]]


def _blade(d, mat, bx, h, a, w=0.025, bend=0.0, z0=0.0):
    tip = (bx + h * math.sin(a) + bend, z0 + h * math.cos(a))
    mid = (bx + 0.5 * h * math.sin(a) + 0.35 * bend, z0 + 0.5 * h * math.cos(a))
    G.stroke(d, [(bx - w, z0), (mid[0] - w * 0.4, mid[1]), tip, (mid[0] + w * 0.4, mid[1]), (bx + w, z0)], mat, I, cyclic=True)
    return tip


def _pebbles(d, M, n, zr, seed, role="pebble_i"):
    rnd = random.Random(seed)
    for i in range(n):
        x, z, r = L * (i + rnd.random()) / n, rnd.uniform(*zr), 0.024 + 0.016 * rnd.random()
        W(lambda dx, _dz, x=x, z=z, r=r, s=seed + i: G.stroke(d, G.lumpy_ellipse(x + dx, z, r * 1.3, r, n=12, lump=0.08, seed=s),
                                                                M[role], I, cyclic=True))


def _hatches(d, M, n, z, seed):
    rnd = random.Random(seed)
    for i in range(n):
        x = L * (i + rnd.random()) / n
        W(lambda dx, _dz, x=x, s=seed + i: G.hatch(d, x + dx, z, M["ink"], n=3, length=0.07, spacing=0.03, angle_deg=160, seed=s))


# ---------------------------------------------------------------- the bands (x 0..8 m, the surface at z = 0)

def band_sand(d, M, k=0):
    """Low wind ripples on the surface (<= 0.035 m), the dry sand over the damp sand to a ragged edge, shell bits, a dry tuft."""
    xs = [L * i / 640 for i in range(641)]

    def surf(x):
        ph = TAU * 17 * x / L + 0.9 * math.sin(TAU * 2 * x / L + 0.4)
        return 0.034 * ((1 + math.sin(ph)) / 2) ** 1.6
    top = [(x, surf(x)) for x in xs]
    dry_b = [(x, -0.17 + B.per(x, L, 3, 31, 0.035)) for x in xs[::4]]
    damp_b = _ragged(32)

    def body(dx, _dz):
        sh = lambda pts: [(x + dx, z) for x, z in pts]  # noqa: E731
        G.stroke(d, sh(dry_b + damp_b[::-1]), M["sand_sh"], 0.0, cyclic=True)
        G.stroke(d, sh(top + dry_b[::-1]), M["sand"], 0.0, cyclic=True)
        G.seam(d, sh(dry_b), M["ink"])
        G.stroke(d, sh(top), M["ink"], O)
    W(body)
    crests = [x for i, (x, z) in enumerate(top[1:-1], 1) if z >= top[i - 1][1] and z > top[i + 1][1]]
    for j, xc in enumerate(crests):                                                           # ripple marks under the crests
        if j % 2:
            continue
        W(lambda dx, _dz, xc=xc: G.seam(d, G.bezier((xc + dx - 0.16, -0.055), (xc + dx - 0.02, -0.025), (xc + dx + 0.13, -0.06), n=6), M["ink"]))
    rnd = random.Random(1781)
    for i in range(8):                                                                        # shell bits
        x, z, r = L * (i + 0.2 + 0.6 * rnd.random()) / 8, rnd.uniform(-0.06, -0.13), rnd.uniform(0.026, 0.04)
        role = "shell_pink_i" if i % 3 == 1 else "shell_i"
        a = rnd.uniform(-0.5, 0.5)

        def bit(dx, _dz, x=x, z=z, r=r, role=role, a=a):
            fan = [(x + dx, z - r * 0.5)] + [(x + dx + r * math.cos(t + a), z - r * 0.5 + r * 0.9 * math.sin(t + a))
                                              for t in [math.radians(25 + 130 * q / 6) for q in range(7)]]
            G.stroke(d, fan, M[role], I, cyclic=True)
        W(bit)
    _pebbles(d, M, 6, (-0.26, -0.38), 1783, "sandstone_i")
    _hatches(d, M, 5, -0.30, 1784)
    for x0, n in ((2.35, 4), (6.05, 3)):                                                       # a dry tuft (low: it bends)
        for b in range(n):
            a = math.radians(-38 + 76 * b / (n - 1) + rnd.uniform(-6, 6))
            h = rnd.uniform(0.10, 0.15)
            W(lambda dx, _dz, x0=x0, a=a, h=h, s=b: _blade(d, M["dry_tuft" if s % 2 else "dry_sh_tuft"], x0 + dx + 0.02 * (s - 1), h, a,
                                                            w=0.014, z0=surf(x0) - 0.01))


def band_stone(d, M, k=0):
    """A grey rock crust in jointed slabs (rounded tops <= 0.05 m, V joints to the surface row), a lit top rim, shade under each
    slab, lichen dots; the topsoil under it to a ragged edge."""
    rnd = random.Random(1782)
    ws = []
    while sum(ws) < L - 0.3:
        ws.append(rnd.uniform(0.55, 1.3))
    ws = [w * L / sum(ws) for w in ws]
    edges = [sum(ws[:i]) for i in range(len(ws) + 1)]
    hs = [rnd.uniform(0.012, 0.05) for _ in ws]
    bs = [rnd.uniform(-0.34, -0.24) for _ in ws]
    bs2 = [rnd.uniform(-0.36, -0.22) for _ in ws]

    def blk(x):
        x %= L
        for i in range(len(ws)):
            if edges[i] <= x <= edges[i + 1]:
                return i, min(x - edges[i], edges[i + 1] - x)
        return len(ws) - 1, 0.0

    def ztop(x):
        i, t = blk(x)
        return hs[i] * min(1.0, t / 0.045) ** 0.5

    def zbot(x):
        i, t = blk(x)
        f = ((x % L) - edges[i]) / ws[i]
        return bs[i] * (1 - f) + bs2[i] * f + 0.05 * (1 - min(1.0, t / 0.06)) ** 2
    xs = [L * i / 640 for i in range(641)]
    top = [(x, ztop(x)) for x in xs]
    bot = [(x, zbot(x)) for x in xs[::2]]
    soil_b = _ragged(33, -0.47)

    def body(dx, _dz):
        sh = lambda pts: [(x + dx, z) for x, z in pts]  # noqa: E731
        G.stroke(d, sh(bot + soil_b[::-1]), M["topsoil"], 0.0, cyclic=True)
        G.stroke(d, sh(top + bot[::-1]), M["rock"], 0.0, cyclic=True)
        G.stroke(d, sh(top + [(x, z - 0.03) for x, z in top[::-1]]), M["rock_lit"], 0.0, cyclic=True)
        G.stroke(d, sh([(x, z + 0.035) for x, z in bot] + bot[::-1]), M["rock_sh"], 0.0, cyclic=True)
        G.seam(d, sh(bot), M["ink"])
        G.stroke(d, sh(top), M["ink"], O)
    W(body)
    for i, e in enumerate(edges[:-1]):                                                        # the joints
        zb = zbot(e + 0.001)
        W(lambda dx, _dz, e=e, zb=zb, s=i: G.seam(d, [(e + dx, 0.0), (e + dx + 0.015, -0.07), (e + dx - 0.01, -0.15), (e + dx + 0.008, zb + 0.02)],
                                                  M["ink"]))
    for c in range(16):                                                                       # lichen dot clusters
        x0, z0 = L * (c + rnd.random()) / 16, rnd.uniform(-0.04, -0.13)
        dots = [(x0 + rnd.uniform(-0.06, 0.06), z0 + rnd.uniform(-0.025, 0.025), rnd.uniform(0.008, 0.016),
                 rnd.choice(("lichen_y", "lichen_y", "lichen_g", "lichen_w"))) for _ in range(rnd.randint(3, 6))]
        W(lambda dx, _dz, dots=dots, s=c: [G.stroke(d, G.lumpy_ellipse(x + dx, z, r * 1.2, r, n=8, lump=0.1, seed=s * 7 + q), M[role], 0.0, cyclic=True)
                                           for q, (x, z, r, role) in enumerate(dots)])
    for i in range(7):                                                                        # hatching on the slabs
        x = L * (i + rnd.random()) / 7
        W(lambda dx, _dz, x=x, s=i: G.hatch(d, x + dx, -0.17, M["ink"], n=3, length=0.06, spacing=0.03, angle_deg=60, seed=s))
    _pebbles(d, M, 6, (-0.36, -0.42), 1785)


def band_snow(d, M, k=0):
    """A white drift crust (soft swells <= 0.065 m) with drips and a shaded underside, over dark soil to a ragged edge."""
    xs = [L * i / 640 for i in range(641)]
    top = [(x, 0.032 + 0.022 * math.sin(TAU * 2 * x / L + 0.7) + 0.010 * math.sin(TAU * 7 * x / L + 2.1)) for x in xs]
    sbot = [(x, -0.23 + B.per(x, L, 3, 41, 0.035) - 0.06 * max(0.0, math.sin(TAU * 13 * x / L + 0.5 * math.sin(TAU * 2 * x / L))) ** 3)
            for x in xs[::2]]
    soil_b = _ragged(42)

    def body(dx, _dz):
        sh = lambda pts: [(x + dx, z) for x, z in pts]  # noqa: E731
        G.stroke(d, sh(sbot + soil_b[::-1]), M["dsoil"], 0.0, cyclic=True)
        G.stroke(d, sh(top + sbot[::-1]), M["snow"], 0.0, cyclic=True)
        G.stroke(d, sh([(x, z + 0.045) for x, z in sbot] + sbot[::-1]), M["snow_sh"], 0.0, cyclic=True)
        G.seam(d, sh(sbot), M["ink"])
        G.stroke(d, sh(top), M["ink"], O)
    W(body)
    rnd = random.Random(1786)
    for i in range(7):                                                                        # wind lines in the drift
        x = L * (i + rnd.random()) / 7
        W(lambda dx, _dz, x=x: G.seam(d, G.bezier((x + dx - 0.18, -0.035), (x + dx, -0.015), (x + dx + 0.2, -0.045), n=6), M["ink"]))
    for i in range(10):                                                                       # frost glints (sky dots)
        x, z = L * (i + rnd.random()) / 10, rnd.uniform(-0.05, -0.09)
        W(lambda dx, _dz, x=x, z=z, s=i: G.stroke(d, G.lumpy_ellipse(x + dx, z, 0.018, 0.012, n=8, lump=0.1, seed=s), M["snow_sh"], 0.0, cyclic=True))
    for i in range(7):                                                                        # roots in the dark soil
        x = L * (i + 0.3 + rnd.random() * 0.4) / 7
        W(lambda dx, _dz, x=x, s=rnd.random(): G.seam(d, G.bezier((x + dx, -0.33), (x + dx + 0.05 + 0.05 * s, -0.39), (x + dx - 0.03, -0.46), n=6), M["ink"]))
    _pebbles(d, M, 7, (-0.32, -0.42), 1787)
    for i in range(6):                                                                        # frost specks in the soil
        x, z = L * (i + rnd.random()) / 6, rnd.uniform(-0.31, -0.40)
        W(lambda dx, _dz, x=x, z=z, s=i: G.stroke(d, G.lumpy_ellipse(x + dx, z, 0.014, 0.010, n=8, lump=0.1, seed=40 + s), M["snow"], 0.0, cyclic=True))


# ---------------------------------------------------------------- the sand fill (x, z 0..8 m, tiles both ways)

def fill_sand(d, M, k=0):
    """Pale sandstone: cream with golden, tan and two thin rust strata, cross-bedding in the thick bands, pebbles, a few stones."""
    Lf = B.FILL / PPU
    B.wrapped(lambda dx, dz: G.stroke(d, [(dx - 0.1, dz - 0.1), (dx + Lf + 0.1, dz - 0.1), (dx + Lf + 0.1, dz + Lf + 0.1), (dx - 0.1, dz + Lf + 0.1)],
                                      M["cream"], 0.0, cyclic=True), Lf, Lf)
    strata = [(7.20, 0.60, "sand", True), (6.15, 0.25, "sandstone", True), (5.10, 0.75, "sand", True), (4.05, 0.15, "rust", True),
              (3.10, 0.55, "sandstone", True), (2.00, 0.42, "sand", True), (0.95, 0.30, "sand_sh", False), (0.22, 0.14, "rust", True)]
    B._strata(d, M, Lf, strata, 0.10, 1788)
    rnd = random.Random(1789)
    for z0, th in ((7.20, 0.60), (5.10, 0.75), (2.00, 0.42)):                                   # cross-bedding
        for g in range(3):
            x0 = Lf * (g + rnd.uniform(0.1, 0.5)) / 3
            for q in range(4):
                xa = x0 + 0.13 * q
                B.wrapped(lambda dx, dz, xa=xa, z0=z0, th=th: G.seam(d, G.bezier((xa + dx, z0 + dz - th * 0.32), (xa + dx + 0.22, z0 + dz - th * 0.1),
                                                                                  (xa + dx + 0.42, z0 + dz + th * 0.28), n=6), M["ink"]), Lf, Lf)
    for i in range(22):                                                                       # pebbles
        x, z, r = rnd.uniform(0, Lf), rnd.uniform(0, Lf), rnd.uniform(0.03, 0.065)
        B.wrapped(lambda dx, dz, x=x, z=z, r=r, s=i: G.stroke(d, G.lumpy_ellipse(x + dx, z + dz, r * 1.3, r, n=14, lump=0.08, seed=s),
                                                              M["sandstone_i"], I, cyclic=True), Lf, Lf)
    for i in range(3):                                                                        # stones
        x, z, r = rnd.uniform(0, Lf), rnd.uniform(0, Lf), rnd.uniform(0.14, 0.22)

        def stone(dx, dz, x=x, z=z, r=r, s=i):
            pts = G.lumpy_ellipse(x + dx, z + dz, r * 1.35, r, n=18, lump=0.10, seed=140 + s)
            G.stroke(d, pts, M["stone"], 0.0, cyclic=True)
            G.stroke(d, G.lumpy_ellipse(x + dx - r * 0.3, z + dz - r * 0.25, r * 0.7, r * 0.45, n=12, lump=0.06, seed=160 + s), M["stone_sh"], 0.0, cyclic=True)
            G.stroke(d, pts, M["ink"], O, cyclic=True)
            G.seam(d, [(x + dx - r * 0.5, z + dz + r * 0.1), (x + dx + r * 0.3, z + dz - r * 0.3)], M["ink"])
        B.wrapped(stone, Lf, Lf)
    for i in range(10):
        x, z = rnd.uniform(0, Lf), rnd.uniform(0, Lf)
        B.wrapped(lambda dx, dz, x=x, z=z, s=i: G.hatch(d, x + dx, z + dz, M["ink"], n=3, length=0.08, spacing=0.03,
                                                        angle_deg=15 if s % 2 else 165, seed=s), Lf, Lf)
    G.specks(d, [(rnd.uniform(0.05, Lf - 0.05), rnd.uniform(0.05, Lf - 0.05)) for _ in range(30)], M["ink"])


# ---------------------------------------------------------------- upright decor (pivot at the base, z = 0)

def _boulder(d, M, x, r, seed, flat=0.8, fill="rock", shade="rock_sh", lit="rock_lit"):
    pts = [(px, max(pz, -0.02)) for px, pz in G.lumpy_ellipse(x, 0.02, r * 1.25, r * flat, n=22, lump=0.1, seed=seed)]
    G.stroke(d, pts, M[fill], 0.0, cyclic=True)
    if lit:
        G.stroke(d, [(px, pz) for px, pz in G.lumpy_ellipse(x + r * 0.15, r * flat * 0.62, r * 0.85, r * flat * 0.42, n=14, lump=0.05, seed=seed + 5)],
                 M[lit], 0.0, cyclic=True)
    G.stroke(d, [(px, pz) for px, pz in G.lumpy_ellipse(x - r * 0.4, 0.0, r * 0.75, r * 0.45 * flat, n=14, lump=0.05, seed=seed + 9) if pz >= -0.02]
             or [(0, 0)], M[shade], 0.0, cyclic=True)
    G.stroke(d, pts, M["ink"], O, cyclic=True)
    return pts


def decor_sand(d, M, k):
    rnd = random.Random(1790 + k)
    if k == 0:                                                                                # a dry tuft
        for b in range(8):
            a = math.radians(-40 + 80 * b / 7 + rnd.uniform(-7, 7))
            h = rnd.uniform(0.24, 0.42)
            tip = _blade(d, M["dry_tuft" if b % 2 else "dry_sh_tuft"], rnd.uniform(-0.05, 0.05), h, a, w=0.02, bend=0.05 * math.copysign(1, a))
            if b in (2, 5):
                G.stroke(d, G.lumpy_ellipse(tip[0], tip[1], 0.022, 0.035, n=10, lump=0.05, seed=b), M["dry_sh_i"], I, cyclic=True)
    elif k == 1:                                                                              # shells: a scallop and a spiral
        hx = 0.06
        fan = [(hx, -0.02)] + [(hx + 0.18 * math.cos(t), -0.02 + 0.17 * math.sin(t)) for t in [math.radians(18 + 144 * q / 14) for q in range(15)]]
        G.stroke(d, fan, M["shell"], 0.0, cyclic=True)
        G.stroke(d, [(hx, -0.02)] + fan[1:5], M["sandstone"], 0.0, cyclic=True)
        G.stroke(d, fan, M["ink"], O, cyclic=True)
        for q in range(1, 6):
            t = math.radians(18 + 144 * q / 6)
            G.seam(d, [(hx, 0.0), (hx + 0.16 * math.cos(t), -0.02 + 0.15 * math.sin(t))], M["ink"])
        G.stroke(d, [(hx - 0.05, -0.02), (hx - 0.045, 0.035), (hx + 0.045, 0.035), (hx + 0.05, -0.02)], M["shell_i"], I, cyclic=True)
        sp = G.lumpy_ellipse(-0.20, 0.06, 0.10, 0.07, n=18, lump=0.03, seed=11, rot=0.4)
        G.stroke(d, [(x, max(z, -0.02)) for x, z in sp], M["shell_pink_i"], O, cyclic=True)
        G.seam(d, [(-0.20 + 0.08 * (1 - t) * math.cos(TAU * 1.6 * t), 0.06 + 0.055 * (1 - t) * math.sin(TAU * 1.6 * t)) for t in [i / 24 for i in range(24)]],
               M["ink"])
    else:                                                                                     # a wind-carved sandstone rock
        _boulder(d, M, 0.0, 0.27, 1795, flat=0.85, fill="sand", shade="sand_sh", lit=None)
        for j, zz in enumerate((0.08, 0.16)):
            G.seam(d, [(-0.22 + 0.05 * j, zz), (-0.05, zz + 0.015), (0.12, zz - 0.01), (0.24 - 0.06 * j, zz + 0.01)], M["ink"])
        G.hatch(d, -0.18, 0.05, M["ink"], n=3, length=0.06, spacing=0.03, angle_deg=60, seed=4)


def _lichen(d, M, cx, cz, rnd, n=5, spread=0.06):
    for q in range(n):
        G.stroke(d, G.lumpy_ellipse(cx + rnd.uniform(-spread, spread), cz + rnd.uniform(-spread * 0.5, spread * 0.5), 0.016, 0.013, n=8, lump=0.1, seed=q),
                 M[rnd.choice(("lichen_y", "lichen_y", "lichen_g", "lichen_w"))], 0.0, cyclic=True)


def decor_stone(d, M, k):
    rnd = random.Random(1800 + k)
    if k == 0:                                                                                # a lichened boulder
        _boulder(d, M, 0.0, 0.30, 1801)
        G.seam(d, [(-0.12, 0.30), (-0.05, 0.18), (0.02, 0.12)], M["ink"])
        for cx, cz in ((0.10, 0.36), (-0.20, 0.25), (0.22, 0.20)):
            _lichen(d, M, cx, cz, rnd)
        G.hatch(d, -0.25, 0.08, M["ink"], n=3, length=0.06, spacing=0.03, angle_deg=60, seed=3)
    elif k == 1:                                                                              # rounded shore pebbles
        for j, (x, r, fill) in enumerate(((-0.26, 0.09, "rock_lit"), (-0.06, 0.13, "rock"), (0.17, 0.10, "sandstone"), (0.33, 0.06, "rock_sh"))):
            pts = [(px, max(pz, -0.02)) for px, pz in G.lumpy_ellipse(x, r * 0.62, r * 1.25, r * 0.72, n=18, lump=0.05, seed=1810 + j)]
            G.stroke(d, pts, M[fill], 0.0, cyclic=True)
            G.stroke(d, [(px, pz) for px, pz in G.lumpy_ellipse(x - r * 0.3, r * 0.4, r * 0.7, r * 0.35, n=12, lump=0.04, seed=1820 + j)],
                     M["rock_sh" if fill != "rock_sh" else "dsoil"], 0.0, cyclic=True)
            G.stroke(d, pts, M["ink"], O if r > 0.08 else I, cyclic=True)
    else:                                                                                     # thrift: a cushion with pink pompoms
        for b in range(12):
            a = math.radians(-70 + 140 * b / 11)
            _blade(d, M["cushion_tuft" if b % 3 else "needle_tuft"], 0.17 * math.sin(a) * 0.9, rnd.uniform(0.10, 0.15), a * 0.8, w=0.016)
        for j, (x, h) in enumerate(((-0.12, 0.30), (0.03, 0.38), (0.15, 0.27))):
            G.seam(d, G.bezier((x * 0.5, 0.05), (x * 0.8, h * 0.5), (x, h), n=6), M["ink"], radius=O)
            G.stroke(d, G.lumpy_ellipse(x, h + 0.04, 0.065, 0.058, n=16, lump=0.12, seed=j), M["thrift_i"], I, cyclic=True)
            G.specks(d, [(x + 0.02, h + 0.06), (x - 0.025, h + 0.03)], M["ink"])


def _snowcap(d, M, pts_top, thick=0.06, seed=0):
    """A snow cap along a top outline (left to right): thickened up by `thick`, a drip or two, the shaded underside."""
    up = [(x, z + thick * (0.6 + 0.4 * math.sin(math.pi * i / max(1, len(pts_top) - 1)))) for i, (x, z) in enumerate(pts_top)]
    low = [(x, z - 0.012 - (0.03 if i in (len(pts_top) // 3, 2 * len(pts_top) // 3) else 0.0)) for i, (x, z) in enumerate(pts_top)]
    G.stroke(d, up + low[::-1], M["snow"], 0.0, cyclic=True)
    G.stroke(d, [(x, z + 0.02) for x, z in low] + low[::-1], M["snow_sh"], 0.0, cyclic=True)
    G.stroke(d, up + low[::-1], M["ink"], O, cyclic=True)


def decor_snow(d, M, k):
    rnd = random.Random(1830 + k)
    if k == 0:                                                                                # a spruce sapling with snow on its tiers
        G.stroke(d, [(-0.028, -0.01), (0.028, -0.01), (0.022, 0.14), (-0.022, 0.14)], M["twig_i"], I, cyclic=True)
        for j, (zb, w, h) in enumerate(((0.10, 0.30, 0.28), (0.30, 0.23, 0.25), (0.48, 0.15, 0.26))):
            tier = [(0.0, zb + h), (-w, zb)] + [(-w + 2 * w * q / 6, zb + (0.035 if q % 2 else 0.0)) for q in range(1, 6)] + [(w, zb)]
            G.stroke(d, tier, M["needle"], 0.0, cyclic=True)
            G.stroke(d, [(0.0, zb + h), (w * 0.92, zb + 0.01), (w * 0.30, zb + 0.03)], M["needle_lit"], 0.0, cyclic=True)
            G.stroke(d, tier, M["ink"], O, cyclic=True)
            for sx, sz in ((-0.55, 0.30), (0.45, 0.42)):
                G.stroke(d, G.lumpy_ellipse(w * sx, zb + h * sz, 0.075, 0.03, n=12, lump=0.1, seed=j * 3 + int(sx * 10), rot=-0.5 * sx),
                         M["snow_i"], I, cyclic=True)
        _snowcap(d, M, [(-0.05 + 0.10 * q / 6, 0.70 + 0.04 * math.sin(math.pi * q / 6)) for q in range(7)], thick=0.04)
    elif k == 1:                                                                              # a snow-capped rock
        pts = _boulder(d, M, 0.0, 0.27, 1835, flat=0.8, lit=None)
        G.seam(d, [(0.10, 0.10), (0.04, 0.02)], M["ink"])
        topline = sorted([(x, z) for x, z in pts if z > 0.12 and abs(x) < 0.30], key=lambda p: p[0])
        _snowcap(d, M, topline, thick=0.07, seed=5)
    else:                                                                                     # dry stalks through a snow mound
        for b in range(7):
            a = math.radians(-28 + 56 * b / 6 + rnd.uniform(-6, 6))
            h = rnd.uniform(0.28, 0.48)
            tip = _blade(d, M["dry_tuft" if b % 2 else "dry_sh_tuft"], -0.05 + 0.017 * b, h, a, w=0.012, bend=0.04 * math.copysign(1, a), z0=0.03)
            if b % 3 == 0:
                G.stroke(d, G.lumpy_ellipse(tip[0], tip[1], 0.018, 0.04, n=10, lump=0.05, seed=b, rot=a), M["dry_sh_i"], I, cyclic=True)
        mound = [(-0.30 + 0.60 * q / 20, 0.085 * math.sin(math.pi * q / 20) ** 0.7) for q in range(21)]
        G.stroke(d, mound + [(0.30, -0.02), (-0.30, -0.02)], M["snow"], 0.0, cyclic=True)
        G.stroke(d, [(x, z * 0.35) for x, z in mound] + [(0.30, -0.02), (-0.30, -0.02)], M["snow_sh"], 0.0, cyclic=True)
        G.stroke(d, mound, M["ink"], O)


# ---------------------------------------------------------------- Mars's polar frost (LEAD 05:3x, for U-159): ground_band_frost over the Mars fill

def band_frost(d, M, k=0):
    """Mars's polar cap: a cream CO2-frost crust in polygon-patterned hummocks (soft troughs every ~1 m, cracks down from them),
    a grey-blue shaded underside, a layered teal water-ice deposit with dust lines, the rust regolith to a ragged edge."""
    rnd = random.Random(1840)
    ws = []
    while sum(ws) < L - 0.4:
        ws.append(rnd.uniform(0.8, 1.4))
    ws = [w * L / sum(ws) for w in ws]
    edges = [sum(ws[:i]) for i in range(len(ws) + 1)]
    hs = [rnd.uniform(0.035, 0.06) for _ in ws]

    def ztop(x):
        x %= L
        for i in range(len(ws)):
            if edges[i] <= x <= edges[i + 1]:
                t = min(x - edges[i], edges[i + 1] - x)
                return 0.004 + hs[i] * min(1.0, t / 0.22) ** 0.7
        return 0.004
    xs = [L * i / 640 for i in range(641)]
    top = [(x, ztop(x)) for x in xs]
    fbot = [(x, -0.12 + B.per(x, L, 3, 51, 0.025)) for x in xs[::2]]
    ibot = [(x, -0.31 + B.per(x, L, 3, 52, 0.035)) for x in xs[::2]]
    soil_b = _ragged(53, -0.47)

    def body(dx, _dz):
        sh = lambda pts: [(x + dx, z) for x, z in pts]  # noqa: E731
        G.stroke(d, sh(ibot + soil_b[::-1]), M["topsoil"], 0.0, cyclic=True)
        G.stroke(d, sh(fbot + ibot[::-1]), M["ice"], 0.0, cyclic=True)
        G.stroke(d, sh([(x, z + 0.04) for x, z in ibot] + ibot[::-1]), M["ice_sh"], 0.0, cyclic=True)
        G.stroke(d, sh(top + fbot[::-1]), M["frost"], 0.0, cyclic=True)
        G.stroke(d, sh([(x, z + 0.035) for x, z in fbot] + fbot[::-1]), M["frost_sh"], 0.0, cyclic=True)
        G.seam(d, sh(fbot), M["ink"])
        G.seam(d, sh(ibot), M["ink"])
        G.stroke(d, sh(top), M["ink"], O)
    W(body)
    for j in range(3):                                                                        # dust lines in the layered ice
        z0 = -0.165 - 0.045 * j
        line = [(x, z0 + B.per(x, L, 3, 60 + j, 0.012)) for x in xs[::8]]
        W(lambda dx, _dz, line=line: G.stroke(d, [(x + dx, z) for x, z in line] + [(x + dx, z - 0.012) for x, z in line[::-1]],
                                              M["dust"], 0.0, cyclic=True))
    for i, e in enumerate(edges[:-1]):                                                        # the polygon troughs' cracks
        W(lambda dx, _dz, e=e: G.seam(d, [(e + dx, 0.004), (e + dx + 0.012, -0.05), (e + dx - 0.008, -0.10)], M["ink"]))
    for i in range(12):                                                                       # frost sparkle
        x, z = L * (i + rnd.random()) / 12, rnd.uniform(-0.03, -0.07)
        W(lambda dx, _dz, x=x, z=z, s=i: G.stroke(d, G.lumpy_ellipse(x + dx, z, 0.016, 0.011, n=8, lump=0.1, seed=s), M["frost_sh"], 0.0, cyclic=True))
    _pebbles(d, M, 6, (-0.36, -0.42), 1841)


def _chipped(cx, cz, rx, rz, seed, rot=0.0, n=8, cuts=2):
    """A chipped, rounded lump: n corners at jittered angles and radii (the chips), corner-cut `cuts` times (Chaikin), so its
    facets stay flat-ish but every corner is soft: no flat top, no vertical side, nothing that reads as a cube."""
    rnd = random.Random(seed)
    poly = []
    for i in range(n):
        a = TAU * (i + rnd.uniform(-0.3, 0.3)) / n
        q = rnd.uniform(0.88, 1.06)
        poly.append((rx * q * math.cos(a), rz * q * math.sin(a)))
    for _ in range(cuts):
        nxt = []
        for i in range(len(poly)):
            (x0, z0), (x1, z1) = poly[i], poly[(i + 1) % len(poly)]
            nxt += [(0.75 * x0 + 0.25 * x1, 0.75 * z0 + 0.25 * z1), (0.25 * x0 + 0.75 * x1, 0.25 * z0 + 0.75 * z1)]
        poly = nxt
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + px * c - pz * s, cz + px * s + pz * c) for px, pz in poly]


def _arc(out, cx, cz, a0, a1):
    """The outline's points seen from (cx, cz) between a0 and a1 degrees (in outline order), closed by their chord: a facet
    chipped off the lump's rim, always inside the outline."""
    sel = [i for i, (px, pz) in enumerate(out) if a0 <= math.degrees(math.atan2(pz - cz, px - cx)) % 360 <= a1]
    if len(sel) < 3:
        return [(cx, cz)] * 3
    gaps = [(sel[(i + 1) % len(sel)] - sel[i]) % len(out) for i in range(len(sel))]
    start = (gaps.index(max(gaps)) + 1) % len(sel)                                            # begin after the one gap (the arc may wrap index 0)
    return [out[sel[(start + i) % len(sel)]] for i in range(len(sel))]


def decor_frost(d, M, k):
    rnd = random.Random(1850 + k)
    if k == 0:                                                                                # a frost-capped boulder
        pts = _boulder(d, M, 0.0, 0.26, 1851, flat=0.8, lit=None)
        G.seam(d, [(0.10, 0.10), (0.04, 0.02)], M["ink"])
        topline = sorted([(x, z) for x, z in pts if z > 0.12 and abs(x) < 0.30], key=lambda p: p[0])
        _snowcap(d, M, topline, thick=0.06)
    elif k == 1:                                                                              # chipped lumps of water ice (LEAD 09:4x: the blocks read as cubes)
        for j, (x, r, h, rot) in enumerate(((-0.22, 0.14, 0.17, -0.30), (0.05, 0.18, 0.25, 0.12), (0.29, 0.11, 0.13, 0.40))):
            cz = h * 0.47
            out = [(px, max(pz, -0.02)) for px, pz in _chipped(x, cz, r, h * 0.55, 1852 + j, rot)]
            G.stroke(d, out, M["ice"], 0.0, cyclic=True)
            G.stroke(d, _arc(out, x, cz, 150, 285), M["ice_sh"], 0.0, cyclic=True)              # the unlit chip on the lower left
            ox, oz = r * 0.30, h * 0.55 * 0.32                                               # the lit chip: a glassy facet up and right, inside the rim
            G.stroke(d, _chipped(x + ox * math.cos(rot) - oz * math.sin(rot), cz + ox * math.sin(rot) + oz * math.cos(rot),
                                 r * 0.36, h * 0.55 * 0.26, 1872 + j, rot + 0.35, n=5), M["frost"], 0.0, cyclic=True)
            G.stroke(d, out, M["ink"], O, cyclic=True)
    else:                                                                                     # a CO2 vent: a dark fan, a plume
        fan = [(-0.04, 0.0), (0.40, 0.035), (0.44, -0.01), (0.04, -0.015)]
        G.stroke(d, fan, M["vent"], 0.0, cyclic=True)
        G.stroke(d, fan, M["ink"], I, cyclic=True)
        mound = [(-0.12 + 0.24 * q / 10, 0.05 * math.sin(math.pi * q / 10)) for q in range(11)]
        G.stroke(d, mound + [(0.12, -0.02), (-0.12, -0.02)], M["frost"], 0.0, cyclic=True)
        G.stroke(d, mound, M["ink"], O)
        G.stroke(d, G.lumpy_ellipse(0.0, 0.05, 0.035, 0.012, n=10, lump=0.0), M["vent_i"], I, cyclic=True)
        for j, (x, z, r) in enumerate(((0.00, 0.17, 0.07), (0.04, 0.32, 0.085), (0.09, 0.49, 0.09), (0.15, 0.65, 0.07))):
            G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.85, n=14, lump=0.12, seed=j), M["plume_i"], I, cyclic=True)


# ---------------------------------------------------------------- B-180: a cliff lip per variant (B-175's lip format: 128x96, pivot (0.55, 0.6)
# at the brink, drawn for a drop to the right, mirror x for the left; the hood rounds the brink's corner, radius 0.37 m about (0, -0.35))

LIP_CZ = -0.35


def _hood(top, thick, a1, bulge=0.0, x0=-0.60):
    """A lip hood: the crust's flat top at `top` from x0 to the brink, round the corner (centre (0, LIP_CZ)) to a1 degrees, back
    along the inner edge `thick` deeper. bulge: the outer radius swells by bulge x sin^2 toward the face (a cornice overhang).
    -> (outer, inner) (outer: x0 -> the arc's end; inner: the arc's end -> x0), so outer + inner closes the hood."""
    r_o = top - LIP_CZ
    n = max(6, int(a1 / 6))
    angs = [math.radians(a1 * j / n) for j in range(n + 1)]
    outer = [(x0 * (1 - i / 12), top) for i in range(12)] + \
            [((r_o + bulge * math.sin(a) ** 2) * math.sin(a), LIP_CZ + (r_o + bulge * math.sin(a) ** 2) * math.cos(a)) for a in angs]
    ri = r_o - thick
    inner = [(ri * math.sin(a), LIP_CZ + ri * math.cos(a)) for a in angs[::-1]] + [(x0 * (1 - i / 12), top - thick) for i in range(11, -1, -1)]
    return outer, inner


def lip_sand(d, M, k=0):
    """The dry sand's hood over the brink (the band's dry layer), its damp underside, a ripple, a dry tuft leaning over the
    edge and a thin stream of sand pouring down the face with a few grains."""
    top = 0.03
    outer, inner = _hood(top, 0.15, 84)
    _o2, inner2 = _hood(top, 0.105, 84)
    G.stroke(d, outer + inner, M["sand"], 0.0, cyclic=True)
    G.stroke(d, inner2 + inner[::-1], M["sand_sh"], 0.0, cyclic=True)
    G.stroke(d, outer, M["ink"], O)
    G.seam(d, inner, M["ink"])
    G.seam(d, G.bezier((-0.52, -0.035), (-0.36, -0.008), (-0.20, -0.04), n=6), M["ink"])
    G.seam(d, G.bezier((0.05, -0.05), (0.16, -0.03), (0.24, -0.09), n=6), M["ink"])
    for b, a_deg in enumerate((20, 38, 56)):                                                  # a dry tuft at the brink, leaning out
        _blade(d, M["dry_tuft" if b % 2 else "dry_sh_tuft"], -0.10 + 0.025 * b, 0.13 + 0.02 * b, math.radians(a_deg), w=0.014, z0=top - 0.01)
    tongue = []                                                                               # a tongue of sand spilling down the face (>= 4 px wide)
    for i in range(13):
        t = i / 12
        z = -0.22 - 0.40 * t
        xf = math.sqrt(max(0.0, 0.37 ** 2 - (z - LIP_CZ) ** 2)) if z > LIP_CZ else 0.37 + 0.30 * (LIP_CZ - z)   # the face under the corner
        tongue.append((xf - 0.02, z, xf + 0.02 + 0.075 * (1 - t) ** 0.8 + 0.02))
    tip = tongue[-1]
    outline = [(a, z) for a, z, _b in tongue] + [(tip[0] + 0.03, tip[1] - 0.035)] + [(b, z) for _a, z, b in tongue[::-1]]
    G.stroke(d, outline, M["sand_i"], I, cyclic=True)
    G.seam(d, [((a + b) / 2 + 0.01, z) for a, z, b in tongue[2:10]], M["ink"])
    for j, (x, z, r) in enumerate(((0.62, -0.70, 0.026), (0.58, -0.80, 0.022), (0.66, -0.58, 0.020))):
        G.stroke(d, G.lumpy_ellipse(x, z, r * 1.2, r, n=10, lump=0.1, seed=1860 + j), M["sand_sh_i"], I, cyclic=True)


def lip_stone(d, M, k=0):
    """A capstone ledge (the first draw, the crust wrapped round the corner, read as a bent pipe at 1x): the rock crust's slab
    runs on flat past the brink and ends in a rounded, slightly chipped nose that juts over the rounded face, sky under it; a lit
    rim on top, the underside in shade, two joints, lichen, two chips falling."""
    top, th, nx = 0.04, 0.16, 0.40
    zb = top - th
    rise = [(-0.60 + (nx - 0.07 + 0.60) * i / 16, top + 0.004 * math.sin(2.3 * i)) for i in range(17)]
    nose = [(nx - 0.07 + 0.07 * math.sin(a), top - 0.07 + 0.07 * math.cos(a)) for a in [math.radians(15 * j) for j in range(1, 7)]]
    chin = [(nx - 0.065 + 0.065 * math.cos(a), zb + 0.065 - 0.065 * math.sin(a)) for a in [math.radians(15 * j) for j in range(0, 7)]]
    xface = math.sqrt(max(0.0, 0.37 ** 2 - (zb - LIP_CZ) ** 2))                               # where the underside meets the band's rounded face
    outer = rise + nose + chin + [(xface, zb)]
    inner = [(xface - 0.6 * (xface + 0.60) * i / 6 - 0.4 * (xface + 0.60) * (i / 6) ** 2, zb) for i in range(7)]
    G.stroke(d, outer + inner[1:], M["rock"], 0.0, cyclic=True)
    G.stroke(d, [(x, z) for x, z in rise] + [(x, z - 0.032) for x, z in rise[::-1]], M["rock_lit"], 0.0, cyclic=True)
    G.stroke(d, chin + [(xface, zb)] + [(xface - 0.02, zb + 0.045), (nx - 0.05, zb + 0.05)], M["rock_sh"], 0.0, cyclic=True)
    G.stroke(d, [(-0.60, zb + 0.04), (xface - 0.04, zb + 0.04), (xface, zb), (-0.60, zb)], M["rock_sh"], 0.0, cyclic=True)
    G.stroke(d, outer, M["ink"], O)
    G.seam(d, inner, M["ink"])
    for jx in (-0.30, 0.08):                                                                  # joints
        G.seam(d, [(jx, top), (jx + 0.015, top - 0.07), (jx - 0.01, zb + 0.01)], M["ink"])
    G.hatch(d, -0.16, -0.06, M["ink"], n=3, length=0.05, spacing=0.03, angle_deg=60, seed=7)
    rnd = random.Random(1870)
    for cx, cz in ((-0.46, -0.02), (0.22, -0.03)):
        _lichen(d, M, cx, cz, rnd, n=5, spread=0.05)
    for j, (x, z, r) in enumerate(((0.47, -0.40, 0.035), (0.50, -0.58, 0.028))):
        G.stroke(d, B._shard(x, z, r, random.Random(1875 + j), sides=5, flat=0.8), M["rock_i"], I, cyclic=True)


def lip_snow(d, M, k=0):
    """A snow cornice: the drift crust's hood swelling past the face and curling under, its blue underside, three rounded drips
    under the curl, a wind line on top, glints, two clumps falling."""
    top = 0.06
    outer, inner = _hood(top, 0.15, 118, bulge=0.07)
    _o2, inner2 = _hood(top, 0.10, 118)
    G.stroke(d, outer + inner, M["snow"], 0.0, cyclic=True)
    G.stroke(d, inner2 + inner[::-1], M["snow_sh"], 0.0, cyclic=True)
    end = [outer[-1], inner[0]]
    for j, t in enumerate((0.3, 0.75)):                                                       # two fat drips under the curl (>= 4 px: the colour shows)
        x = end[0][0] + (end[1][0] - end[0][0]) * t
        z = end[0][1] + (end[1][1] - end[0][1]) * t
        ln = (0.11, 0.075)[j]
        G.stroke(d, G.lumpy_ellipse(x, z - ln * 0.45, 0.036, ln * 0.6, n=14, lump=0.04, seed=1880 + j), M["snow_sh_i"], I, cyclic=True)
    G.stroke(d, outer + [inner[0]], M["ink"], O)                                               # the curl's underside is in the air: inked
    G.seam(d, inner, M["ink"])
    G.seam(d, G.bezier((-0.50, 0.0), (-0.32, 0.03), (-0.12, -0.01), n=6), M["ink"])
    rnd = random.Random(1881)
    for i in range(6):
        a = math.radians(rnd.uniform(5, 100))
        rr = top - LIP_CZ - 0.07
        G.stroke(d, G.lumpy_ellipse(rr * math.sin(a), LIP_CZ + rr * math.cos(a), 0.016, 0.011, n=8, lump=0.1, seed=i), M["snow_sh"], 0.0, cyclic=True)
    for j, (x, z, r) in enumerate(((0.58, -0.72, 0.045), (0.52, -0.82, 0.034))):
        G.stroke(d, G.lumpy_ellipse(x, z, r * 1.2, r, n=12, lump=0.1, seed=1885 + j), M["snow_i"], I, cyclic=True)


def lip_frost(d, M, k=0):
    """Mars's cap at a brink: the cream CO2-frost crust rounding the corner over the layered teal water ice (a dust line in it),
    both wrapping the edge as the band's layers do; a polygon trough's crack on top, frost flakes falling."""
    top = 0.04
    fo, fi = _hood(top, 0.12, 84)
    io, ii = _hood(top - 0.12, 0.17, 84)
    do_, di = _hood(top - 0.20, 0.014, 84)
    _o2, ish = _hood(top - 0.12, 0.13, 84)
    G.stroke(d, io + ii, M["ice"], 0.0, cyclic=True)
    G.stroke(d, ish + ii[::-1], M["ice_sh"], 0.0, cyclic=True)
    G.stroke(d, do_ + di, M["dust"], 0.0, cyclic=True)
    _o3, fsh = _hood(top, 0.085, 84)
    G.stroke(d, fo + fi, M["frost"], 0.0, cyclic=True)
    G.stroke(d, fsh + fi[::-1], M["frost_sh"], 0.0, cyclic=True)
    G.stroke(d, fo, M["ink"], O)
    G.seam(d, fi, M["ink"])
    G.seam(d, ii, M["ink"])
    G.seam(d, [(-0.35, top), (-0.338, top - 0.05), (-0.356, top - 0.10)], M["ink"])           # a polygon trough's crack
    for j, (x, z, r) in enumerate(((0.52, -0.52, 0.032), (0.47, -0.66, 0.027), (0.55, -0.79, 0.023))):   # >= 3 px so the cream shows
        G.stroke(d, G.lumpy_ellipse(x, z, r * 1.3, r, n=10, lump=0.12, seed=1890 + j), M["frost_i"], I, cyclic=True)


LIPS = {"sand": lip_sand, "stone": lip_stone, "snow": lip_snow, "frost": lip_frost}
LIP_PIV = (0.55, 0.6)


# ---------------------------------------------------------------- B-181 Mars (LEAD 09:5x, the variant list): Tharsis basalt, the canyon's talus

def _lobes(rnd, lo, hi, hmin, hmax, total=None):
    """Widths that sum to the band's 8 m, their start edges and a height each (a lobe / slab per span)."""
    total = total or L
    ws = []
    while sum(ws) < total - hi * 0.5:
        ws.append(rnd.uniform(lo, hi))
    ws = [w * total / sum(ws) for w in ws]
    return ws, [sum(ws[:i]) for i in range(len(ws) + 1)], [rnd.uniform(hmin, hmax) for _ in ws]


def _span_z(edges, ws, hs, x, shape=0.6, floor=0.004):
    """The top of a lobed surface at x: each span a rounded hump (sin^shape), the joins at `floor`."""
    x %= L
    for i in range(len(ws)):
        if edges[i] <= x <= edges[i + 1]:
            return floor + hs[i] * max(0.0, math.sin(math.pi * (x - edges[i]) / ws[i])) ** shape   # at an edge float error can dip below 0
    return floor


def band_basalt(d, M, k=0):
    """Tharsis / Olympus Mons: a dark basalt crust in pahoehoe lobes (rounded toes <= 0.05 m, ropy folds on the face, a lit rim,
    vesicles), rust dust lying in the hollows between lobes, then a rubbly red flow top (clinker) to a ragged edge."""
    rnd = random.Random(1910)
    ws, edges, hs = _lobes(rnd, 0.6, 1.3, 0.025, 0.05)
    xs = [L * i / 640 for i in range(641)]
    top = [(x, _span_z(edges, ws, hs, x)) for x in xs]
    cbot = [(x, -0.17 + B.per(x, L, 3, 1911, 0.025)) for x in xs[::2]]
    rag = _ragged(1912, -0.45)

    def body(dx, _dz):
        sh = lambda pts: [(x + dx, z) for x, z in pts]  # noqa: E731
        G.stroke(d, sh(cbot + rag[::-1]), M["redbrown"], 0.0, cyclic=True)
        G.stroke(d, sh(top + cbot[::-1]), M["basalt"], 0.0, cyclic=True)
        G.stroke(d, sh(top + [(x, z - 0.028) for x, z in top[::-1]]), M["bas_lit"], 0.0, cyclic=True)
        G.stroke(d, sh([(x, z + 0.035) for x, z in cbot] + cbot[::-1]), M["basalt_sh"], 0.0, cyclic=True)
        G.seam(d, sh(cbot), M["ink"])
    W(body)
    for i, e in enumerate(edges[:-1]):                                                        # each lobe's toe overlapping the one before it
        W(lambda dx, _dz, e=e: G.seam(d, G.bezier((e + dx, 0.0), (e + dx - 0.02, -0.07), (e + dx - 0.16, -0.11), n=8), M["ink"]))
    W(lambda dx, _dz: G.stroke(d, [(x + dx, z) for x, z in top], M["ink"], O))
    for i, e in enumerate(edges[:-1]):                                                        # rust dust drifted into each hollow, over the line
        W(lambda dx, _dz, e=e, s=i: G.stroke(d, [(px, max(pz, -0.012)) for px, pz in G.lumpy_ellipse(e + dx, 0.0, 0.14, 0.02, n=16, lump=0.06, seed=1913 + s)],
                                             M["top_i"], I, cyclic=True))
    for i in range(len(ws)):                                                                  # (the first draw's stacked rope arcs read as vent grilles: gone)
        rnd.uniform(0.35, 0.65)                                                               # keeps the rng sequence of the vesicles below
    for i in range(40):                                                                       # vesicles
        x, z, r = L * (i + rnd.random()) / 40, -0.035 - rnd.random() * 0.10, 0.007 + 0.007 * rnd.random()
        W(lambda dx, _dz, x=x, z=z, r=r, s=i: G.stroke(d, G.lumpy_ellipse(x + dx, z, r * 1.3, r, n=8, lump=0.1, seed=1920 + s), M["basalt_sh"], 0.0, cyclic=True))
    for i in range(11):                                                                       # clinker in the flow top
        x, z, r = L * (i + rnd.random()) / 11, -0.22 - rnd.random() * 0.08, 0.03 + 0.025 * rnd.random()   # above the ragged edge's highest point
        W(lambda dx, _dz, x=x, z=z, r=r, s=i: G.stroke(d, B._shard(x + dx, z, r, random.Random(1930 + s), sides=6, flat=0.7), M["rock_i"], I, cyclic=True))


def fill_basalt(d, M, k=0):
    """Under Tharsis: stacked lava-flow sheets (dark basalt and rose-grey flows, 1.2-1.8 m thick) with columnar joints and a
    vesicle zone under each top, parted by thin rubbly red flow tops (boles); strata, pebbles and stones only (D-165)."""
    Lf = B.FILL / PPU
    rnd = random.Random(1940)
    W2 = lambda fn: B.wrapped(fn, Lf, Lf)  # noqa: E731
    W2(lambda dx, dz: G.stroke(d, [(dx - 0.1, dz - 0.1), (dx + Lf + 0.1, dz - 0.1), (dx + Lf + 0.1, dz + Lf + 0.1), (dx - 0.1, dz + Lf + 0.1)],
                               M["basalt"], 0.0, cyclic=True))
    boles = [(6.50, 0.20), (4.51, 0.18), (2.89, 0.22), (1.31, 0.18)]
    B._strata(d, M, Lf, [(6.50, 0.20, "redbrown", True), (5.50, 1.80, "rock", True), (4.51, 0.18, "redbrown", True), (3.71, 1.42, "basalt", True),
                         (2.89, 0.22, "redbrown", True), (2.09, 1.38, "rock", True), (1.31, 0.18, "redbrown", True)], 0.06, 1941)
    flows = [(6.40, 4.60), (4.42, 3.00), (2.78, 1.40), (1.22, -1.40)]                         # (top, bottom) of the four flows (the last wraps)
    for j, (zt, zb) in enumerate(flows):
        for q in range(7):                                                                    # columnar joints in the core
            x = Lf * (q + 0.2 + 0.6 * rnd.random()) / 7
            W2(lambda dx, dz, x=x, zt=zt, zb=zb: G.seam(d, [(x + dx, zb + 0.15 + dz), (x + dx + 0.025, (zt + zb) / 2 + dz), (x + dx - 0.01, zt - 0.40 + dz)],
                                                        M["ink"]))
        B._scatter(d, M, Lf, 14, (zt - 0.34, zt - 0.06), (0.010, 0.020), "basalt_sh", 1950 + j)  # the vesicle zone
    for j, (z, t) in enumerate(boles):                                                        # clinker in the boles
        B._scatter(d, M, Lf, 9, (z - t * 0.3, z + t * 0.3), (0.025, 0.045), "rock_sh", 1960 + j)
    B._scatter(d, M, Lf, 12, (0.0, Lf), (0.03, 0.05), "pebble_i", 1970)
    for i in range(3):                                                                        # stones
        x, z, r = rnd.uniform(0, Lf), rnd.uniform(0.5, 7.5), rnd.uniform(0.12, 0.18)
        W2(lambda dx, dz, x=x, z=z, r=r, s=i: [G.stroke(d, B._shard(x + dx, z + dz, r, random.Random(1980 + s), sides=7, flat=0.75), M["bas_lit"], 0.0, cyclic=True),
                                              G.stroke(d, B._shard(x + dx, z + dz, r, random.Random(1980 + s), sides=7, flat=0.75), M["ink"], O, cyclic=True)])
    for i in range(10):
        x, z = rnd.uniform(0, Lf), rnd.uniform(0, Lf)
        W2(lambda dx, dz, x=x, z=z, s=i: G.hatch(d, x + dx, z + dz, M["ink"], n=3, length=0.08, spacing=0.03, angle_deg=15 if s % 2 else 165, seed=s))
    G.specks(d, [(rnd.uniform(0.05, Lf - 0.05), rnd.uniform(0.05, Lf - 0.05)) for _ in range(40)], M["ink"])


def decor_basalt(d, M, k):
    if k == 0:                                                                                # a vesicular boulder with dust on its back
        _boulder(d, M, 0.0, 0.25, 1990, flat=0.8, fill="basalt", shade="basalt_sh", lit="bas_lit")
        rnd = random.Random(1991)
        for q in range(9):
            G.stroke(d, G.lumpy_ellipse(rnd.uniform(-0.2, 0.22), rnd.uniform(0.04, 0.26), 0.014, 0.011, n=8, lump=0.1, seed=q), M["basalt_sh"], 0.0, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(-0.14, 0.17, 0.12, 0.035, n=14, lump=0.06, seed=1992, rot=0.5), M["top"], 0.0, cyclic=True)
    elif k == 1:                                                                              # a spatter cone stub: a low rim of welded clots
        rim = [(-0.34, -0.02), (-0.26, 0.08), (-0.16, 0.20), (-0.09, 0.27), (-0.04, 0.22), (0.04, 0.22), (0.10, 0.28), (0.18, 0.19),
               (0.27, 0.08), (0.34, -0.02)]
        G.stroke(d, rim, M["redbrown"], 0.0, cyclic=True)
        G.stroke(d, rim[:5] + [(-0.05, -0.02)], M["basalt_sh"], 0.0, cyclic=True)
        for j, (x, z, r) in enumerate(((-0.22, 0.12, 0.05), (-0.11, 0.23, 0.045), (0.12, 0.24, 0.045), (0.24, 0.11, 0.05))):
            G.stroke(d, G.lumpy_ellipse(x, z, r * 1.1, r, n=12, lump=0.12, seed=2000 + j), M["basalt_i"], I, cyclic=True)
        G.stroke(d, rim, M["ink"], O, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(0.0, 0.225, 0.04, 0.012, n=10, lump=0.0), M["basalt_sh"], 0.0, cyclic=True)   # the vent's dark mouth
    else:                                                                                     # a tilted crust slab (a tumulus plate)
        slab = _soften([(-0.40, -0.04), (-0.30, 0.07), (0.22, 0.31), (0.30, 0.28), (0.33, 0.20), (0.02, -0.04)])
        G.stroke(d, slab, M["basalt"], 0.0, cyclic=True)
        G.stroke(d, _soften([(-0.28, 0.06), (0.21, 0.28), (0.27, 0.25), (-0.24, 0.02)], 1), M["bas_lit"], 0.0, cyclic=True)
        G.stroke(d, _soften([(0.03, -0.02), (0.31, 0.19), (0.24, 0.19), (-0.02, 0.0)], 1), M["basalt_sh"], 0.0, cyclic=True)
        G.stroke(d, slab, M["ink"], O, cyclic=True)
        for j in range(3):
            t = 0.25 + 0.22 * j
            G.seam(d, G.bezier((-0.30 + 0.52 * t - 0.04, 0.06 + 0.24 * t - 0.06), (-0.30 + 0.52 * t, 0.06 + 0.24 * t - 0.02),
                               (-0.30 + 0.52 * t + 0.03, 0.06 + 0.24 * t - 0.07), n=6), M["ink"])


def band_talus(d, M, k=0):
    """Valles Marineris' floor: a dusty ochre scree crust packed with angular wall debris (salmon, rose-grey, rust and pale
    shards, the biggest poking <= 0.05 m above the surface), over a light-toned layered sediment, then the rust topsoil."""
    rnd = random.Random(2010)
    xs = [L * i / 640 for i in range(641)]
    top = [(x, 0.006 + B.per(x, L, 4, 2011, 0.008)) for x in xs]
    mbot = [(x, -0.12 + B.per(x, L, 3, 2012, 0.02)) for x in xs[::2]]
    pbot = [(x, -0.30 + B.per(x, L, 3, 2013, 0.03)) for x in xs[::2]]
    rag = _ragged(2014, -0.46)

    def body(dx, _dz):
        sh = lambda pts: [(x + dx, z) for x, z in pts]  # noqa: E731
        G.stroke(d, sh(pbot + rag[::-1]), M["topsoil"], 0.0, cyclic=True)
        G.stroke(d, sh(mbot + pbot[::-1]), M["pale"], 0.0, cyclic=True)
        G.stroke(d, sh(top + mbot[::-1]), M["ochre"], 0.0, cyclic=True)
        G.stroke(d, sh([(x, z + 0.03) for x, z in mbot] + mbot[::-1]), M["ripple_sh"], 0.0, cyclic=True)
        G.seam(d, sh(mbot), M["ink"])
        G.seam(d, sh(pbot), M["ink"])
        G.stroke(d, sh(top), M["ink"], O)
    W(body)
    for j, zl in enumerate((-0.17, -0.215, -0.255)):                                          # laminae in the light-toned sediment
        line = [(x, zl + B.per(x, L, 3, 2020 + j, 0.012)) for x in xs[::8]]
        if j == 1:
            W(lambda dx, _dz, line=line: G.stroke(d, [(x + dx, z) for x, z in line] + [(x + dx, z - 0.014) for x, z in line[::-1]], M["ochre"], 0.0, cyclic=True))
        else:
            W(lambda dx, _dz, line=line: G.seam(d, [(x + dx, z) for x, z in line], M["ink"]))
    roles = ("salmon_i", "rock_i", "top_i", "pale_i", "redbrown_i")
    for i in range(24):                                                                       # the scree: angular shards in the crust (>= 6 px: speckle at 1x otherwise)
        x = L * (i + rnd.random()) / 24
        r = rnd.uniform(0.06, 0.11)
        z = rnd.uniform(-0.08, -0.04) if i % 3 else rnd.uniform(-0.01, 0.01)                 # one in three pokes up through the surface
        role, sides = roles[i % len(roles)], rnd.choice((4, 5, 6))                            # drawn outside the lambda: every tiling copy alike
        W(lambda dx, _dz, x=x, z=z, r=r, s=i, role=role, sides=sides: G.stroke(d, B._shard(x + dx, z, r, random.Random(2030 + s), sides=sides, flat=0.7),
                                                                               M[role], I, cyclic=True))
    for i in range(8):                                                                        # grit specks
        x, z = L * (i + rnd.random()) / 8, rnd.uniform(-0.04, -0.10)
        W(lambda dx, _dz, x=x, z=z, s=i: G.specks(d, [(x + dx, z), (x + dx + 0.05, z - 0.02), (x + dx - 0.04, z + 0.01)], M["ink"]))
    _pebbles(d, M, 6, (-0.36, -0.42), 2040)


def _soften(poly, it=2):
    """Corner-cut a closed outline (Chaikin): straight-edged slabs keep their facets but lose every sharp corner."""
    for _ in range(it):
        nxt = []
        for i in range(len(poly)):
            (x0, z0), (x1, z1) = poly[i], poly[(i + 1) % len(poly)]
            nxt += [(0.75 * x0 + 0.25 * x1, 0.75 * z0 + 0.25 * z1), (0.25 * x0 + 0.75 * x1, 0.25 * z0 + 0.75 * z1)]
        poly = nxt
    return [(x, max(z, -0.02)) for x, z in poly]


def _span_x(poly, z):
    """The (left, right) x of a convex outline at height z."""
    xs = []
    for (x0, z0), (x1, z1) in zip(poly, poly[1:] + poly[:1]):
        if (z0 - z) * (z1 - z) <= 0 and z0 != z1:
            xs.append(x0 + (x1 - x0) * (z - z0) / (z1 - z0))
    return (min(xs), max(xs)) if xs else (0.0, 0.0)


def decor_talus(d, M, k):
    if k == 0:                                                                                # a broken piece of the layered canyon wall
        # LEAD 10:2x: the first draw (a pale oval, one stripe) read as an egg / a clam shell; now the wall's rose-grey rock with
        # rust and red-brown laminae along its tilt, two chipped corners, softened once (rounded enough, not a cube), its left
        # end buried, its right end resting on the ground
        tilt, lift = 0.18, -0.04
        c, s = math.cos(tilt), math.sin(tilt)
        R = lambda px, pz: (px * c - pz * s, lift + px * s + pz * c)  # noqa: E731
        local = [(-0.30, 0.0), (0.30, 0.0), (0.30, 0.19), (0.19, 0.30), (-0.23, 0.30), (-0.30, 0.24)]   # chipped top corners
        blk = _soften([R(*p) for p in local], 1)
        G.stroke(d, blk, M["rock"], 0.0, cyclic=True)
        for z0, t, role in ((0.10, 0.035, "top"), (0.16, 0.03, "redbrown"), (0.215, 0.03, "top")):    # laminae following the tilt
            xr = min(0.27, 0.30 - max(0.0, z0 + t - 0.19) - 0.03)                             # inside the softened outline and the chip
            G.stroke(d, [R(-0.24, z0), R(xr, z0), R(xr, z0 + t), R(-0.24, z0 + t)], M[role], 0.0, cyclic=True)
            G.seam(d, [R(-0.24, z0 + t), R(xr, z0 + t)], M["ink"])
        G.stroke(d, [R(-0.17, 0.268), R(0.12, 0.268), R(0.12, 0.288), R(-0.17, 0.288)], M["rock_lit"], 0.0, cyclic=True)   # the lit top edge
        G.stroke(d, blk, M["ink"], O, cyclic=True)
        G.seam(d, [R(0.19, 0.30), R(0.215, 0.235), R(0.30, 0.19)], M["ink"])                 # the fresh break at the chipped corner
    elif k == 1:                                                                              # a scree fan: shards heaped on a dust apron
        apron = [(-0.36 + 0.72 * i / 20, 0.05 * math.sin(math.pi * i / 20) ** 0.8) for i in range(21)]
        G.stroke(d, apron + [(0.36, -0.02), (-0.36, -0.02)], M["ochre"], 0.0, cyclic=True)
        G.stroke(d, apron, M["ink"], O)
        rnd = random.Random(2060)
        for j, (x, z, r, role) in enumerate(((-0.20, 0.06, 0.07, "rock_i"), (0.05, 0.07, 0.085, "salmon_i"), (0.24, 0.05, 0.06, "top_i"),
                                             (-0.08, 0.16, 0.07, "pale_i"), (0.13, 0.17, 0.06, "redbrown_i"), (0.02, 0.215, 0.055, "salmon_i"))):   # the top shard rests on the pile
            G.stroke(d, B._shard(x, z, r, rnd, sides=5, flat=0.75), M[role], O if r > 0.065 else I, cyclic=True)
    else:                                                                                     # a dust-buried slab, an ochre drift on its back
        slab = _soften([(-0.36, -0.04), (-0.30, 0.11), (0.18, 0.18), (0.33, 0.08), (0.36, -0.04)])
        G.stroke(d, slab, M["rock"], 0.0, cyclic=True)
        G.stroke(d, _soften([(-0.32, -0.02), (-0.28, 0.09), (-0.10, 0.12), (-0.14, -0.02)], 1), M["rock_sh"], 0.0, cyclic=True)
        drift = [(-0.36 + 0.40 * i / 12, 0.05 + 0.07 * math.sin(math.pi * i / 12) ** 1.2) for i in range(13)]
        G.stroke(d, slab, M["ink"], O, cyclic=True)
        G.stroke(d, drift + [(0.04, -0.02), (-0.36, -0.02)], M["ochre"], 0.0, cyclic=True)
        G.stroke(d, drift, M["ink"], O)
        G.seam(d, [(-0.02, 0.10), (0.10, 0.06), (0.18, 0.09)], M["ink"])


# ---------------------------------------------------------------- B-181 Mercury (the polar cold traps' ice) and Venus (tesserae, vent fields)

def band_ice(d, M, k=0):
    """Mercury's polar cold traps (MercuryLandforms.InColdTrap): a smooth water-ice skin in long low swells with a pale lit rim,
    star glints, hairline cracks and dark grains frozen in, over the dark shadowed crater-floor regolith to a ragged edge."""
    rnd = random.Random(2110)
    xs = [L * i / 640 for i in range(641)]
    top = [(x, 0.014 + 0.012 * math.sin(TAU * 3 * x / L + 0.4) + 0.006 * math.sin(TAU * 11 * x / L + 1.3)) for x in xs]
    ibot = [(x, -0.16 + B.per(x, L, 3, 2111, 0.03)) for x in xs[::2]]
    rag = _ragged(2112, -0.46)

    def body(dx, _dz):
        sh = lambda pts: [(x + dx, z) for x, z in pts]  # noqa: E731
        G.stroke(d, sh(ibot + rag[::-1]), M["floor"], 0.0, cyclic=True)
        G.stroke(d, sh(ibot + [(x, z - 0.05) for x, z in ibot[::-1]]), M["floor_sh"], 0.0, cyclic=True)
        G.stroke(d, sh(top + ibot[::-1]), M["ice"], 0.0, cyclic=True)
        G.stroke(d, sh(top + [(x, z - 0.03) for x, z in top[::-1]]), M["ice_lit"], 0.0, cyclic=True)
        G.stroke(d, sh([(x, z + 0.035) for x, z in ibot] + ibot[::-1]), M["ice_sh"], 0.0, cyclic=True)
        G.seam(d, sh(ibot), M["ink"])
        G.stroke(d, sh(top), M["ink"], O)
    W(body)
    for i in range(9):                                                                        # hairline cracks in the ice
        x = L * (i + 0.2 + 0.6 * rnd.random()) / 9
        W(lambda dx, _dz, x=x: G.seam(d, [(x + dx, -0.035), (x + dx + 0.02, -0.08), (x + dx - 0.005, -0.125)], M["ink"]))
    for i in range(20):                                                                       # dark grains frozen in
        x, z, r = L * (i + rnd.random()) / 20, -0.05 - rnd.random() * 0.08, 0.008 + 0.006 * rnd.random()
        W(lambda dx, _dz, x=x, z=z, r=r, s=i: G.stroke(d, G.lumpy_ellipse(x + dx, z, r * 1.3, r, n=8, lump=0.1, seed=2114 + s), M["floor_sh"], 0.0, cyclic=True))
    for i in range(7):                                                                        # four-point glints in the ice (>= 4 px)
        x, z, r = L * (i + rnd.random()) / 7, -0.075 - rnd.random() * 0.03, 0.032
        star = [(x + r * (1.0 if q % 2 == 0 else 0.3) * math.cos(TAU * q / 8 + 0.2), z + r * (1.0 if q % 2 == 0 else 0.3) * math.sin(TAU * q / 8 + 0.2))
                for q in range(8)]
        W(lambda dx, _dz, star=star: G.stroke(d, [(px + dx, pz) for px, pz in star], M["ice_lit"], 0.0, cyclic=True))
    _pebbles(d, M, 6, (-0.28, -0.38), 2113)


def decor_ice(d, M, k):
    if k == 0:                                                                                # a dark rock glazed with ice
        pts = _boulder(d, M, 0.0, 0.25, 2120, flat=0.8, fill="floor", shade="floor_sh", lit=None)
        topline = sorted([(x, z) for x, z in pts if z > 0.11 and abs(x) < 0.29], key=lambda p: p[0])
        _snowcap(d, {**M, "snow": M["ice"], "snow_sh": M["ice_sh"]}, topline, thick=0.05)
        G.stroke(d, G.lumpy_ellipse(0.10, 0.27, 0.035, 0.014, n=10, lump=0.05, seed=2121, rot=-0.3), M["ice_lit"], 0.0, cyclic=True)
    elif k == 1:                                                                              # a low ridge of ice, chipped and rounded
        out = [(px, max(pz, -0.02)) for px, pz in _chipped(0.0, 0.05, 0.36, 0.17, 2125, n=7)]
        G.stroke(d, out, M["ice"], 0.0, cyclic=True)
        G.stroke(d, _arc(out, 0.0, 0.05, 150, 285), M["ice_sh"], 0.0, cyclic=True)
        G.stroke(d, _chipped(0.11, 0.13, 0.12, 0.04, 2126, rot=-0.15, n=5), M["ice_lit"], 0.0, cyclic=True)
        G.stroke(d, out, M["ink"], O, cyclic=True)
        G.seam(d, [(-0.06, 0.18), (-0.03, 0.10), (-0.07, 0.03)], M["ink"])
    else:                                                                                     # dark pebbles with frost rims
        for j, (x, r) in enumerate(((-0.24, 0.08), (0.02, 0.11), (0.25, 0.075))):
            pts = [(px, max(pz, -0.02)) for px, pz in G.lumpy_ellipse(x, r * 0.55, r * 1.25, r * 0.7, n=18, lump=0.06, seed=2130 + j)]
            G.stroke(d, pts, M["floor"], 0.0, cyclic=True)
            G.stroke(d, pts, M["ink"], O if r > 0.08 else I, cyclic=True)
            topline = sorted([(px, pz) for px, pz in pts if pz > r * 0.85], key=lambda p: p[0])
            if len(topline) >= 3:
                _snowcap(d, {**M, "snow": M["ice_lit"], "snow_sh": M["ice"]}, topline, thick=0.03)


def band_tessera(d, M, k=0):
    """Venus's tesserae highlands: a crumpled crust of tight ridges and grooves (rounded crests <= 0.06 m, one every 0.25-0.5 m),
    a warm grey-brown lighter than the plains' black glass, one tilted fold line down each ridge, dust in the grooves, over the
    red-brown topsoil to a ragged edge."""
    rnd = random.Random(2210)
    ws, edges, hs = _lobes(rnd, 0.25, 0.5, 0.035, 0.07)
    xs = [L * i / 640 for i in range(641)]
    top = [(x, _span_z(edges, ws, hs, x, shape=1.4)) for x in xs]                            # narrow crests, wide grooves
    zt = lambda x: _span_z(edges, ws, hs, x, shape=1.4)  # noqa: E731
    cbot = [(x, -0.17 + B.per(x, L, 3, 2211, 0.025)) for x in xs[::2]]
    rag = _ragged(2212, -0.46)

    def body(dx, _dz):
        sh = lambda pts: [(x + dx, z) for x, z in pts]  # noqa: E731
        G.stroke(d, sh(cbot + rag[::-1]), M["topsoil"], 0.0, cyclic=True)
        G.stroke(d, sh(top + cbot[::-1]), M["tess"], 0.0, cyclic=True)
        G.stroke(d, sh([(x, z + 0.035) for x, z in cbot] + cbot[::-1]), M["tess_sh"], 0.0, cyclic=True)
    W(body)
    for i in range(len(ws)):                                                                  # LEAD 10:2x: lit crests, dark grooves
        e0, w = edges[i], ws[i]
        crest = [(e0 + w * t, zt(e0 + w * t)) for t in [0.2 + 0.6 * q / 12 for q in range(13)]]
        W(lambda dx, _dz, crest=crest: G.stroke(d, [(x + dx, z) for x, z in crest] + [(x + dx, z - 0.03) for x, z in crest[::-1]], M["tess_lit"], 0.0, cyclic=True))
        gx = e0                                                                               # the groove at this ridge's left foot: a dark wedge
        wedge = [(gx - 0.06, zt(gx - 0.06) - 0.004), (gx, -0.055), (gx + 0.06, zt(gx + 0.06) - 0.004)] + \
                [(gx + 0.06 * (1 - t), zt(gx + 0.06 * (1 - t)) - 0.002) for t in (0.33, 0.66)] + [(gx, zt(gx))] + \
                [(gx - 0.06 * t, zt(gx - 0.06 * t) - 0.002) for t in (0.33, 0.66)]
        W(lambda dx, _dz, wedge=wedge: G.stroke(d, [(x + dx, z) for x, z in wedge], M["tess_dp"], 0.0, cyclic=True))
    W(lambda dx, _dz: [G.seam(d, [(x + dx, z) for x, z in cbot], M["ink"]), G.stroke(d, [(x + dx, z) for x, z in top], M["ink"], O)])
    for i in range(len(ws)):                                                                  # one fold line per ridge, its tilt and length varied
        cx = edges[i] + ws[i] * rnd.uniform(0.35, 0.6)
        ln, lean = rnd.uniform(0.07, 0.13), rnd.uniform(0.05, 0.11)
        W(lambda dx, _dz, cx=cx, ln=ln, lean=lean: G.seam(d, G.bezier((cx + dx, -0.015), (cx + dx - lean * 0.4, -0.015 - ln * 0.6), (cx + dx - lean, -0.015 - ln), n=6),
                                                          M["ink"]))
    for i, e in enumerate(edges[:-1]):                                                        # dust lying in the grooves
        if i % 2:
            continue
        W(lambda dx, _dz, e=e, s=i: G.stroke(d, [(px, max(pz, -0.01)) for px, pz in G.lumpy_ellipse(e + dx, 0.004, 0.07, 0.016, n=12, lump=0.06, seed=2214 + s)],
                                             M["dust_i"], I, cyclic=True))
    _pebbles(d, M, 6, (-0.28, -0.38), 2213)


def band_vent(d, M, k=0):
    """Venus's active vent fields: a cracked yellow sulfur crust in low flat plates over black basalt, glowing ember seams running
    down through some of the cracks, green vitriol-glass shards poking through, over the red-brown topsoil to a ragged edge."""
    rnd = random.Random(2310)
    ws, edges, hs = _lobes(rnd, 0.5, 1.1, 0.012, 0.035)
    xs = [L * i / 640 for i in range(641)]
    top = [(x, _span_z(edges, ws, hs, x, shape=0.35)) for x in xs]                           # flat-topped plates
    sbot = [(x, -0.075 + B.per(x, L, 3, 2311, 0.015)) for x in xs[::2]]
    bbot = [(x, -0.26 + B.per(x, L, 3, 2312, 0.03)) for x in xs[::2]]
    rag = _ragged(2313, -0.46)

    def body(dx, _dz):
        sh = lambda pts: [(x + dx, z) for x, z in pts]  # noqa: E731
        G.stroke(d, sh(bbot + rag[::-1]), M["topsoil"], 0.0, cyclic=True)
        G.stroke(d, sh(sbot + bbot[::-1]), M["black"], 0.0, cyclic=True)
        G.stroke(d, sh(top + sbot[::-1]), M["sulfur"], 0.0, cyclic=True)
        G.stroke(d, sh([(x, z + 0.022) for x, z in sbot] + sbot[::-1]), M["sulfur_sh"], 0.0, cyclic=True)
        G.seam(d, sh(sbot), M["ink"])
        G.seam(d, sh(bbot), M["ink"])
        G.stroke(d, sh(top), M["ink"], O)
    W(body)
    for i, e in enumerate(edges[:-1]):                                                        # the cracks between plates; every other one glows
        if i % 2:
            W(lambda dx, _dz, e=e: G.seam(d, [(e + dx, 0.0), (e + dx + 0.012, -0.04), (e + dx - 0.005, -0.075)], M["ink"]))
            continue
        path = [(e + 0.03 * math.sin(2.1 * q + i), -0.01 - 0.21 * q / 6) for q in range(7)]
        wid = [0.042 * (1 - 0.5 * q / 6) for q in range(7)]                                  # LEAD 10:2x: ~5.4 px at the top, the red-orange 2-3 px inside the ink
        seam_ = [(x - w, z) for (x, z), w in zip(path, wid)] + [(x + w, z) for (x, z), w in zip(path[::-1], wid[::-1])]
        core = [(x - w * 0.22, z) for (x, z), w in zip(path[:4], wid[:4])] + [(x + w * 0.22, z) for (x, z), w in zip(path[3::-1], wid[3::-1])]
        W(lambda dx, _dz, seam_=seam_, core=core: [G.stroke(d, [(x + dx, z) for x, z in seam_], M["ember_i"], I, cyclic=True),
                                                    G.stroke(d, [(x + dx, z) for x, z in core], M["ember_core"], 0.0, cyclic=True)])
    for i in range(7):                                                                        # vitriol-glass shards through the crust
        x, r = L * (i + 0.25 + 0.5 * rnd.random()) / 7, rnd.uniform(0.045, 0.07)
        tilt = rnd.uniform(-0.35, 0.35)
        c, s = math.cos(tilt), math.sin(tilt)
        R = lambda px, pz, x=x, c=c, s=s: (x + px * c - pz * s, -0.03 + px * s + pz * c)  # noqa: E731
        shard = [R(-r * 0.5, 0.0), R(-r * 0.55, r * 1.1), R(-r * 0.05, r * 1.45), R(r * 0.5, r * 1.15), R(r * 0.5, 0.0)]
        lit = [R(r * 0.05, r * 1.25), R(r * 0.35, r * 1.05), R(r * 0.3, r * 0.6), R(r * 0.1, r * 0.75)]
        W(lambda dx, _dz, shard=shard, lit=lit: [G.stroke(d, [(px + dx, pz) for px, pz in shard], M["glass"], 0.0, cyclic=True),
                                                  G.stroke(d, [(px + dx, pz) for px, pz in lit], M["glint"], 0.0, cyclic=True),
                                                  G.stroke(d, [(px + dx, pz) for px, pz in shard], M["ink"], I, cyclic=True)])
    _pebbles(d, M, 6, (-0.32, -0.40), 2314)


def decor_tessera(d, M, k):
    if k == 0:                                                                                # a tilted ridge slab with its fold lines
        slab = _soften([(-0.38, -0.04), (-0.33, 0.06), (0.16, 0.27), (0.27, 0.26), (0.32, 0.17), (0.04, -0.04)])
        G.stroke(d, slab, M["tess"], 0.0, cyclic=True)
        G.stroke(d, _soften([(-0.30, 0.05), (0.15, 0.24), (0.24, 0.23), (-0.26, 0.01)], 1), M["tess_lit"], 0.0, cyclic=True)
        G.stroke(d, _soften([(0.05, -0.02), (0.30, 0.16), (0.22, 0.17), (0.0, 0.0)], 1), M["tess_sh"], 0.0, cyclic=True)
        G.stroke(d, slab, M["ink"], O, cyclic=True)
        for t, ln in ((0.35, 0.10), (0.65, 0.07)):
            x0, z0 = -0.33 + 0.49 * t, 0.06 + 0.21 * t
            G.seam(d, G.bezier((x0, z0 - 0.02), (x0 + 0.02, z0 - 0.02 - ln * 0.5), (x0 + 0.06, z0 - 0.02 - ln), n=6), M["ink"])
    elif k == 1:                                                                              # a grooved block, corner-cut once
        blk = [(px, max(pz, -0.02)) for px, pz in _chipped(0.0, 0.15, 0.27, 0.17, 2230, rot=-0.1, n=6, cuts=1)]
        G.stroke(d, blk, M["tess"], 0.0, cyclic=True)
        G.stroke(d, _arc(blk, 0.0, 0.15, 150, 290), M["tess_sh"], 0.0, cyclic=True)
        G.stroke(d, _arc(blk, 0.0, 0.15, 25, 95), M["tess_lit"], 0.0, cyclic=True)
        G.stroke(d, blk, M["ink"], O, cyclic=True)
        for j, (x0, ln) in enumerate(((-0.08, 0.16), (0.08, 0.12))):
            G.seam(d, G.bezier((x0, 0.27 - 0.03 * j), (x0 - 0.03, 0.18), (x0 + 0.01, 0.27 - 0.03 * j - ln), n=6), M["ink"])
    else:                                                                                     # a scree of folded chips on a dust apron
        apron = [(-0.34 + 0.68 * i / 18, 0.04 * math.sin(math.pi * i / 18) ** 0.8) for i in range(19)]
        G.stroke(d, apron + [(0.34, -0.02), (-0.34, -0.02)], M["dust"], 0.0, cyclic=True)
        G.stroke(d, apron, M["ink"], O)
        rnd = random.Random(2240)
        for j, (x, z, r, role) in enumerate(((-0.18, 0.06, 0.08, "tess_i"), (0.06, 0.07, 0.09, "tess_lit_i"), (0.24, 0.05, 0.065, "tess_sh_i"),
                                             (-0.04, 0.17, 0.07, "tess_i"))):
            G.stroke(d, B._shard(x, z, r, rnd, sides=5, flat=0.7), M[role], O if r > 0.075 else I, cyclic=True)


def decor_vent(d, M, k):
    if k == 0:                                                                                # a small fumarole cone breathing a fume
        cone = [(-0.30, -0.02), (-0.20, 0.06), (-0.08, 0.17), (-0.03, 0.15), (0.03, 0.15), (0.09, 0.18), (0.21, 0.07), (0.30, -0.02)]
        G.stroke(d, cone, M["sulfur"], 0.0, cyclic=True)
        G.stroke(d, cone[:4] + [(-0.06, -0.02)], M["sulfur_sh"], 0.0, cyclic=True)
        G.stroke(d, cone, M["ink"], O, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(0.0, 0.155, 0.035, 0.012, n=10, lump=0.0), M["black"], 0.0, cyclic=True)
        for j, (x, z, r) in enumerate(((0.02, 0.27, 0.06), (0.07, 0.41, 0.075), (0.13, 0.56, 0.08), (0.20, 0.69, 0.06))):
            G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.85, n=14, lump=0.12, seed=2250 + j), M["fume_i"], I, cyclic=True)
    elif k == 1:                                                                              # sulfur rosettes on a black stone
        _boulder(d, M, 0.0, 0.17, 2260, flat=0.6, fill="black", shade="tess_sh", lit=None)
        for j, (cx, cz, s) in enumerate(((-0.10, 0.16, 1.0), (0.12, 0.13, 0.8))):
            for q in range(7):
                a = math.radians(15 + 150 * q / 6)
                tip = (cx + 0.10 * s * math.cos(a), cz + 0.10 * s * math.sin(a))
                side = (0.022 * s * math.sin(a), -0.022 * s * math.cos(a))
                G.stroke(d, [(cx - side[0], cz - side[1]), tip, (cx + side[0], cz + side[1])], M["sulfur_i" if q % 2 else "sulfur_sh_i"], I, cyclic=True)
            G.stroke(d, G.lumpy_ellipse(cx, cz, 0.03 * s, 0.026 * s, n=10, lump=0.05, seed=2262 + j), M["sulfur_i"], I, cyclic=True)
    else:                                                                                     # a vitriol-glass cluster on basalt
        _boulder(d, M, 0.0, 0.19, 2270, flat=0.5, fill="black", shade="tess_sh", lit=None)
        for j, (x, w, h, tilt) in enumerate(((-0.12, 0.09, 0.30, 0.30), (0.03, 0.11, 0.42, -0.05), (0.16, 0.08, 0.26, -0.40))):
            c, s = math.cos(tilt), math.sin(tilt)
            R = lambda px, pz, x=x, c=c, s=s: (x + px * c - pz * s, 0.05 + px * s + pz * c)  # noqa: E731
            xt = [R(-w / 2, 0.0), R(-w / 2, h * 0.82), R(w * 0.15, h), R(w / 2, h * 0.86), R(w / 2, 0.0)]
            G.stroke(d, xt, M["glass"], 0.0, cyclic=True)
            G.stroke(d, [R(-w / 2, 0.0), R(-w / 2, h * 0.82), R(-w * 0.1, h * 0.8), R(-w * 0.1, 0.0)], M["glass_sh"], 0.0, cyclic=True)
            G.stroke(d, [R(w * 0.18, h * 0.9), R(w * 0.36, h * 0.8), R(w * 0.3, h * 0.55), R(w * 0.14, h * 0.62)], M["glint"], 0.0, cyclic=True)
            G.stroke(d, xt, M["ink"], O, cyclic=True)
            G.seam(d, [R(-w * 0.1, h * 0.8), R(w * 0.15, h)], M["ink"])


B181_VARIANTS = {"mars": ("basalt", "talus"), "mercury": ("ice",), "venus": ("tessera", "vent")}
B181_DRAW = {"basalt": (band_basalt, decor_basalt), "talus": (band_talus, decor_talus), "ice": (band_ice, decor_ice),
             "tessera": (band_tessera, decor_tessera), "vent": (band_vent, decor_vent)}
B181_FILLS = {"basalt": fill_basalt}


# ---------------------------------------------------------------- the pieces, the render, the export API (render.py ground_strip_set)

BAND_PIV = (0.0, (B.BAND_H - B.SURF_ROW) / B.BAND_H)
PART = "variants"

# B-190 (LEAD 13:0x): dig puffs in each ground's own material - B-175's draw_puff (the face-safe one: clods behind the billows,
# c8cf185b) with its three roles (the billow fill, its shade, the clods) taken from the variant's materials; 8 frames of 128x128,
# pivot (0.5, 0.25), clip 'puff', as terrain/<planet>/dig_puff
PUFF_VARIANTS = {"earth": ("sand", "snow", "stone"), "mars": ("frost", "basalt"),
                 "mercury": ("ice",), "venus": ("tessera", "vent")}                          # B-191 (LEAD cycle 284)
PUFF_ROLES = {"sand": ("sand_i", "sand_sh", "sand_sh_i"), "snow": ("snow_i", "sandstone", "snow_sh_i"),
              "stone": ("rock_lit_i", "rock", "rock_sh_i"), "frost": ("frost_i", "pale", "ice_i"),
              "basalt": ("bas_lit_i", "basalt", "basalt_sh_i"),
              "ice": ("ice_i", "ice_sh", "ice_lit_i"),                                     # B-191: teal ice spray, off-white ice chunks
              "tessera": ("tess_i", "tess_sh", "tess_dp_i"), "vent": ("sulfur_i", "sulfur_sh", "black_i")}


def _puff_fn(v):
    dust_i, dust_sh, clod_i = PUFF_ROLES[v]
    return lambda d, M, k: B.draw_puff(d, {**M, "dust_i": M[dust_i], "dust_sh": M[dust_sh], "clod_i": M[clod_i]}, k)


# B-192 (LEAD cycle 284): buried details for the newest fills on D-165's pattern (upright, pivot centred; UNITY's U-167 scatters
# them in that fill's cutaway by a position seed, never rotated): three for Earth's ground_fill_sand, three for Mars's
# ground_fill_basalt. Coordinates in metres from the frame centre (64 px = 1 m).

def _rot_ell(cx, cz, rx, rz, a, n=20, lump=0.04, seed=0):
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        t = TAU * i / n
        k = 1 + lump * (2 * rnd.random() - 1)
        x, z = rx * k * math.cos(t), rz * k * math.sin(t)
        pts.append((cx + x * math.cos(a) - z * math.sin(a), cz + x * math.sin(a) + z * math.cos(a)))
    return pts


def _tube(path, widths):
    """A closed outline round a centre path, widths[i] each side of point i."""
    left, right = [], []
    for i, (x, z) in enumerate(path):
        x0, z0 = path[max(i - 1, 0)]
        x1, z1 = path[min(i + 1, len(path) - 1)]
        ln = math.hypot(x1 - x0, z1 - z0) or 1.0
        nx, nz = -(z1 - z0) / ln, (x1 - x0) / ln
        left.append((x + nx * widths[i], z + nz * widths[i]))
        right.append((x - nx * widths[i], z - nz * widths[i]))
    return left + right[::-1]


def fs_scallop(d, M):
    """A pink scallop shell from the old sea floor: a ribbed fan with a scalloped rim and two ears at the hinge."""
    hz = -0.15
    arc = []
    for i in range(41):
        a = math.radians(32 + 116 * i / 40)
        r = 0.29 + 0.012 * abs(math.sin(9 * math.pi * i / 40))                               # one rim bump per rib
        arc.append((r * math.cos(a), hz + r * math.sin(a)))
    G.stroke(d, [(-0.08, hz - 0.03), (0.08, hz - 0.03), (0.09, hz + 0.03)] + arc + [(-0.09, hz + 0.03)], M["shell_pink_i"], O, cyclic=True)
    for j in range(9):
        a = math.radians(42 + 96 * j / 8)
        G.seam(d, [(0.05 * math.cos(a), hz + 0.05 + 0.03 * math.sin(a)), (0.26 * math.cos(a), hz + 0.26 * math.sin(a))], M["ink"])
    G.seam(d, [(-0.08, hz + 0.03), (0.08, hz + 0.03)], M["ink"])


def fs_fulgurite(d, M):
    """A fulgurite: a knobbly tube of sand fused by lightning, branching, broken off at one end to show its hollow core."""
    def branch(p0, p1, w0, w1, n, wob, seed):
        r = random.Random(seed)
        path = [(p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t + wob * math.sin(math.pi * 2.3 * t + seed)) for t in [i / n for i in range(n + 1)]]
        ws = [(w0 + (w1 - w0) * i / n) * (1 + 0.28 * (r.random() - 0.5)) for i in range(n + 1)]
        return path, _tube(path, ws)
    for p0, p1, seed in (((-0.06, 0.0), (0.12, -0.17), 3), ((0.14, 0.02), (0.30, 0.17), 5)):
        G.stroke(d, branch(p0, p1, 0.028, 0.012, 10, 0.015, seed)[1], M["sandstone_i"], I, cyclic=True)
    path, outline = branch((-0.40, 0.04), (0.40, -0.02), 0.046, 0.02, 24, 0.03, 1)
    G.stroke(d, outline, M["sandstone_i"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(path[0][0] + 0.004, path[0][1], 0.012, 0.028, n=10, lump=0.05, seed=7), M["rock_sh"], 0.0, cyclic=True)


def fs_desert_rose(d, M):
    """A desert rose: a rosette of rounded gypsum blades, rust behind, sand-coloured in front, each front blade's edge-on ridge."""
    back = [(-0.10, 0.02, 0.15, 0.045, 1.15), (0.09, 0.03, 0.15, 0.045, 0.45), (0.0, 0.08, 0.14, 0.04, 1.6),
            (-0.16, -0.06, 0.13, 0.04, 0.2), (0.16, -0.07, 0.13, 0.04, 2.9)]
    front = [(-0.05, -0.06, 0.13, 0.04, 0.75), (0.06, -0.05, 0.12, 0.04, 2.3), (0.0, -0.11, 0.12, 0.035, 0.05)]
    for i, (cx, cz, rx, rz, a) in enumerate(back):
        G.stroke(d, _rot_ell(cx, cz, rx, rz, a, seed=10 + i), M["rust_i"], I, cyclic=True)
    for i, (cx, cz, rx, rz, a) in enumerate(front):
        G.stroke(d, _rot_ell(cx, cz, rx, rz, a, seed=20 + i), M["sand_sh_i"], I, cyclic=True)
        G.seam(d, [(cx - 0.5 * rx * math.cos(a), cz - 0.5 * rx * math.sin(a)), (cx + 0.5 * rx * math.cos(a), cz + 0.5 * rx * math.sin(a))], M["ink"])


def fs_lava_tube(d, M):
    """A lava tube in section: a pale chilled rind round an empty dark tube, the last flow's flat floor, lava drips on the roof."""
    G.stroke(d, G.lumpy_ellipse(0.0, 0.0, 0.80, 0.34, n=40, lump=0.04, seed=1931), M["bas_lit_i"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, 0.03, 0.64, 0.24, n=36, lump=0.03, seed=1932), M["basalt_sh_i"], I, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.0, -0.13, 0.42, 0.045, n=24, lump=0.03, seed=1933), M["basalt_i"], I, cyclic=True)
    for x in (-0.38, -0.2, -0.05, 0.12, 0.3, 0.42):
        top = 0.03 + 0.24 * math.sqrt(max(0.0, 1 - (x / 0.64) ** 2)) - 0.015
        G.stroke(d, [(x - 0.022, top), (x + 0.022, top), (x + 0.004, top - 0.06), (x - 0.004, top - 0.06)], M["bas_lit_i"], I, cyclic=True)


def fs_vesicles(d, M):
    """Gas vesicles frozen in the flow: dark bubbles stretched sideways, each with a lit lower lip."""
    rnd = random.Random(1934)
    for i in range(8):
        a, dist = rnd.uniform(0, TAU), 0.2 * math.sqrt(rnd.random())
        x, z, r = dist * math.cos(a), dist * math.sin(a) * 0.6, rnd.uniform(0.028, 0.05)
        G.stroke(d, G.lumpy_ellipse(x, z, r * 1.5, r, n=14, lump=0.06, seed=1934 + i), M["basalt_sh_i"], I, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(x, z - r * 0.5, r * 0.9, r * 0.32, n=10, lump=0.0, seed=1940 + i), M["bas_lit"], 0.0, cyclic=True)


def fs_amygdale(d, M):
    """An amygdale: an old vesicle filled with pale zeolite, needles radiating from a teal core."""
    G.stroke(d, G.lumpy_ellipse(0.0, 0.0, 0.21, 0.15, n=24, lump=0.04, seed=1951), M["pale_i"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(0.02, 0.01, 0.09, 0.06, n=16, lump=0.05, seed=1952), M["ice_i"], I, cyclic=True)
    for k in range(12):
        a = TAU * k / 12 + 0.13
        G.seam(d, [(0.02 + 0.10 * math.cos(a), 0.01 + 0.068 * math.sin(a)), (0.17 * math.cos(a), 0.12 * math.sin(a))], M["ink"])


FILL_PIECES = {"earth": ("sand", [("scallop", fs_scallop, 64, 48), ("fulgurite", fs_fulgurite, 96, 48), ("desert_rose", fs_desert_rose, 64, 64)]),
               "mars": ("basalt", [("lava_tube", fs_lava_tube, 128, 64), ("vesicles", fs_vesicles, 64, 48), ("amygdale", fs_amygdale, 48, 48)])}


def _pieces(planet, part="variants"):
    """-> (the planet's pieces {name: (w, h, pivot, frames, draw)}, its tiling pieces). part "lips": B-180's ground_lip_<variant>
    only (their own manifest rows, so the accepted variant exports are not re-written)."""
    if part == "lips":
        return {f"ground_lip_{v}": (128, 96, LIP_PIV, 1, LIPS[v]) for v in PLANET_VARIANTS[planet]}, ()
    if part == "puffs":                                                                       # B-190: one 8-frame sheet per material
        return {f"dig_puff_{v}": (128, 128, (0.5, 0.25), 8, _puff_fn(v)) for v in PUFF_VARIANTS[planet]}, ()
    if part == "fills":                                                                       # B-192: the variant fill's buried details
        v, lst = FILL_PIECES[planet]
        return {f"fill_decor_{v}_{i + 1}": (w, h, (0.5, 0.5), 1, (lambda d, M, k, fn=fn: fn(d, M))) for i, (_n, fn, w, h) in enumerate(lst)}, ()
    if part == "b181":                                                                        # B-181: the planet's new biome variants, their own row
        P, T = {}, []
        for v in B181_VARIANTS[planet]:
            P[f"ground_band_{v}"] = (B.BAND_W, B.BAND_H, BAND_PIV, 1, B181_DRAW[v][0])
            T.append(f"ground_band_{v}")
            if v in B181_FILLS:
                P[FILL_OF[v]] = (B.FILL, B.FILL, (0.0, 0.0), 1, B181_FILLS[v])
                T.append(FILL_OF[v])
        for v in B181_VARIANTS[planet]:
            P[f"ground_decor_{v}"] = (64, 64, (0.5, 6 / 64), 3, B181_DRAW[v][1])
        return P, tuple(T)
    if planet == "mars":
        return ({"ground_band_frost": (B.BAND_W, B.BAND_H, BAND_PIV, 1, band_frost), "ground_decor_frost": (64, 64, (0.5, 6 / 64), 3, decor_frost)},
                ("ground_band_frost",))
    return ({"ground_band_sand": (B.BAND_W, B.BAND_H, BAND_PIV, 1, band_sand), "ground_band_stone": (B.BAND_W, B.BAND_H, BAND_PIV, 1, band_stone),
             "ground_band_snow": (B.BAND_W, B.BAND_H, BAND_PIV, 1, band_snow), "ground_fill_sand": (B.FILL, B.FILL, (0.0, 0.0), 1, fill_sand),
             "ground_decor_sand": (64, 64, (0.5, 6 / 64), 3, decor_sand), "ground_decor_stone": (64, 64, (0.5, 6 / 64), 3, decor_stone),
             "ground_decor_snow": (64, 64, (0.5, 6 / 64), 3, decor_snow)},
            ("ground_band_sand", "ground_band_stone", "ground_band_snow", "ground_fill_sand"))


PIECES, TILES = _pieces(PLANET)


def render_piece(name, k=0, mx=1, mz=1, ss=None):
    w, h, piv, _n, fn = PIECES[name]
    w, h = w * mx, h * mz
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    B._CUR = d
    B._GROUPS.clear()
    fn(d, M, k)
    B._CUR = None
    st = fakegp.strokes_of(d, gp)
    for master, ranges in B._GROUPS:
        m0, m1 = ranges[master]
        for a, b in ranges:
            if (a, b) != (m0, m1) and b - a == m1 - m0:
                for i in range(m1 - m0):
                    st[a + i]["id"] = st[m0 + i]["id"]
    ss = ss or (2 if w * h > 200_000 else 4)
    return GR.render_frame(st, w, h, PPU, piv, ss=ss, seed=1780 + k)


def _kn(name, k):
    return f"{name}_{k + 1}" if name.startswith("ground_decor_") else name


def _keys():
    return {_kn(n, k): f"terrain/{PLANET}/{_kn(n, k)}" for n, p in PIECES.items() for k in range(p[3])}


KEYS = _keys()


def use_planet(planet, part="variants"):
    """The row's planet: Earth's sand / stone / snow set (B-178) or Mars's polar frost (LEAD 05:3x); part "lips": B-180's lips."""
    global PLANET, VARIANTS, PIECES, TILES, KEYS, PART
    PLANET, PART = planet, part
    VARIANTS = (B181_VARIANTS[planet] if part == "b181" else PUFF_VARIANTS[planet] if part == "puffs"
                else (FILL_PIECES[planet][0],) if part == "fills" else PLANET_VARIANTS[planet])
    PIECES, TILES = _pieces(planet, part)
    KEYS = _keys()


def sheets():
    S, allw = {}, []
    for name, p in PIECES.items():
        if name.startswith("dig_puff_"):                                                      # B-190: the 8 frames are one key's sheet
            frames, wds = [], []
            for k in range(p[3]):
                img, wd = render_piece(name, k)
                frames.append(img)
                wds += wd
            S[name] = (frames, wds)
            allw += wds
            continue
        for k in range(p[3]):
            img, wd = render_piece(name, k)
            S[_kn(name, k)] = ([img], wd)
            allw += wd
    return S, allw


def pieces_of(S):
    if PART in ("lips", "puffs", "fills"):
        return dict(S)
    out = {n: S[n] for n in TILES}
    for v in VARIANTS:
        ks = [f"ground_decor_{v}_{i + 1}" for i in range(3)]
        out[f"ground_decor_{v}"] = ([S[k][0][0] for k in ks], sum((S[k][1] for k in ks), []))
    return out


def copy_diff(name):
    import numpy as np
    w0, h0 = PIECES[name][0], PIECES[name][1]
    fill = name.startswith("ground_fill_")
    two, _w = render_piece(name, 0, mx=2, mz=2 if fill else 1, ss=1)
    p = float(np.percentile(np.abs(two[:h0, :w0].astype(np.int32) - two[:h0, w0:2 * w0].astype(np.int32)), 99))
    if fill:
        p = max(p, float(np.percentile(np.abs(two[:h0, :w0].astype(np.int32) - two[h0:2 * h0, :w0].astype(np.int32)), 99)))
    return p


def sheet_meta(kn, frames):
    import numpy as np
    base = kn.rsplit("_", 1)[0] if kn.startswith("ground_decor_") else kn
    w, h, piv, _n, _fn = PIECES[base]
    n = len(frames)
    sheet = np.zeros((h, w * n + v3.GUTTER * (n - 1), 4), np.uint8)                          # one row of frames, gutters between (1 frame: as before)
    for i, f in enumerate(frames):
        sheet[:, i * (w + v3.GUTTER):i * (w + v3.GUTTER) + w] = f
    meta = {"key": KEYS[kn], "style": "v3", "contract": "v3.2 11.9", "frame_width": w, "frame_height": h, "columns": n, "gutter": v3.GUTTER,
            "frames": n, "fps": v3.FPS, "pivot": [round(piv[0], 6), round(piv[1], 6)], "facing": "right", "ppu": PPU, "animations": []}
    if kn.startswith("dig_puff_"):
        v = kn.rsplit("_", 1)[1]
        meta.update({"animations": [{"name": "puff", "start": 0, "length": n, "loop": False}], "variant": v,
                     "note": f"B-190: the dig puff in the {v} ground's material (as dig_puff: the clods behind the billows, no face)"})
    elif kn.startswith("fill_decor_"):
        v, i = kn.split("_")[2], int(kn.rsplit("_", 1)[1]) - 1
        meta.update({"upright": True, "variant": v, "fill": FILL_OF[v], "decor": FILL_PIECES[PLANET][1][i][0],
                     "note": f"B-192: a buried detail of {FILL_OF[v]} (D-165's pattern, for U-167): UNITY scatters it in that fill's cutaway by a position seed, never rotated; pivot centred"})
    elif kn.startswith("ground_band_"):
        v = kn.rsplit("_", 1)[1]
        meta.update({"tile_x": True, "repeat_px": B.BAND_W, "surface_row": B.SURF_ROW, "above_px": B.SURF_ROW, "below_px": B.BAND_H - B.SURF_ROW,
                     "variant": v, "biomes": BIOMES[v], "fill": FILL_OF.get(v, "ground_fill"),
                     "mapping": "as ground_band: u = world x x 64 mod 512; v = 24 - (normal distance from the outline x 64); the sprite pivot is ON row 24",
                     "note": f"{'B-181' if PART == 'b181' else 'B-178'}: {PLANET.capitalize()}'s {v} band ({', '.join(BIOMES[v])}); "
                             + ("plains and forest keep ground_band" if PLANET == "earth" else f"the rest of {PLANET.capitalize()} keeps ground_band (U-159)")
                             + "; crossfade the two bands at a biome border"})
    elif kn.startswith("ground_fill_"):
        v = kn.rsplit("_", 1)[1]
        meta.update({"tile_x": True, "tile_y": True, "world_space": True, "standalone": True, "wrap": "repeat", "variant": v,
                     "mapping": "as ground_fill: u = x x 64 mod 512, v = -y x 64 mod 512; a standalone texture (Repeat wrap); strata only (D-165)"})
    elif kn.startswith("ground_lip_"):
        v = kn.rsplit("_", 1)[1]
        meta.update({"brink": True, "variant": v, "biomes": BIOMES[v], "band": f"ground_band_{v}",
                     "note": f"B-180: the {v} band's cliff lip (as ground_lip): drawn for a drop to the right; mirror x for a drop to the left"})
    else:
        v, i = kn.split("_")[2], int(kn.rsplit("_", 1)[1]) - 1
        meta.update({"upright": True, "variant": v, "decor": DECOR[v][i], "note": f"B-178: {PLANET.capitalize()}'s {v} biomes' decor; scatter along the curve, never rotated"})
    problems = [p for p in v3.validate_sheet(meta, sheet.shape) if "sum of clip lengths" not in p]
    if kn not in TILES:
        m = v3.EDGE_MARGIN
        for i, im in enumerate(frames):
            if im[:m, :, 3].any() or im[-m:, :, 3].any() or im[:, :m, 3].any() or im[:, -m:, 3].any():
                problems.append(f"frame {i} touches the {m} px edge")
    hit, off = v3.palette_hits(sheet, PLANET)
    if hit < 0.98:
        problems.append(f"palette {hit * 100:.1f}% (off {' '.join(off[:3])})")
    return sheet, meta, problems


def export(art, S=None):
    import json as _json
    from meridian import pngio
    if S is None:
        S, _w = sheets()
    built, problems, within = [], [], {}
    for kn, (frames, _ws) in S.items():
        sheet, meta, p = sheet_meta(kn, frames)
        problems += [f"{kn}: {x}" for x in p]
        built.append((kn, sheet, meta))
    for kn in TILES:
        within[kn] = copy_diff(kn)
        if within[kn] != 0:
            problems.append(f"{kn}: tiling copies differ (p99 {within[kn]:.0f}; contract 11.9: 0)")
    if problems:
        raise ValueError("earth ground variants checks: " + "; ".join(problems))
    d = os.path.join(art, "terrain", PLANET)
    os.makedirs(d, exist_ok=True)
    out = []
    for kn, sheet, meta in built:
        n = pngio.write_png(os.path.join(d, kn + "_color.png"), sheet)
        with open(os.path.join(d, kn + ".json"), "w", encoding="utf-8", newline="\n") as f:
            _json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((meta["key"], sheet.shape[1], sheet.shape[0], n))
    return out, within, f"{len(out)} keys, contract v3.2 11.9 ({'B-180 lips' if PART == 'lips' else 'B-181 variants' if PART == 'b181' else 'B-190 puffs' if PART == 'puffs' else 'B-192 fill decor' if PART == 'fills' else 'B-178 variants'})"


def main(out, S=None, allw=None, footnote=None):
    if S is None:
        S, allw = sheets()
    if PART == "puffs":                                                                       # B-190: the export's review, this planet's rows
        preview_puffs(os.path.dirname(out), planets=(PLANET,), pieces=pieces_of(S), out=out, footnote=footnote)
        return
    if PART == "fills":                                                                       # B-192: the export's review, this planet's rows
        preview_fills(os.path.dirname(out), planets=(PLANET,), pieces=pieces_of(S), out=out, footnote=footnote)
        return
    (preview_lips if PART == "lips" else preview)(os.path.dirname(out), pieces=pieces_of(S), out=out, footnote=footnote)


# ---------------------------------------------------------------- the preview

def preview(out_dir, pieces=None, out=None, footnote=None):
    """Three 10 m panels side by side at 1x (sand / stone / snow on the same hills and 30 deg slope, each over its fill, its
    decor upright, the surveyor), then a 30 m grass -> sand border crossfade mock (bands, fills and decor blended over 3 m),
    then the pieces."""
    import json
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    if pieces is None:
        pieces = {}
        for n in PIECES:
            rs = [render_piece(n, k) for k in range(PIECES[n][3])]
            pieces[n] = ([r[0] for r in rs], sum((r[1] for r in rs), []))
    tex = lambda img: B._premul(img)  # noqa: E731
    E = os.path.join(ART, "terrain", PLANET)
    grass = {"band": tex(pngio.read_png_np(os.path.join(E, "ground_band_color.png"))),
             "fill": tex(pngio.read_png_np(os.path.join(E, "ground_fill_color.png"))),
             "decor": [pngio.read_png_np(os.path.join(E, f"ground_decor_{i + 1}_color.png")) for i in range(6)]}
    sets = {"grass": grass}
    for v in VARIANTS:
        sets[v] = {"band": tex(pieces[f"ground_band_{v}"][0][0]), "fill": tex(pieces[FILL_OF[v]][0][0]) if v in FILL_OF else grass["fill"],
                   "decor": pieces[f"ground_decor_{v}"][0]}
    xs_all, z_all = B.profile()
    PH = 448
    sky = np.array(v3.hex_rgb(v3.PALETTES[PLANET]["sky"]), np.float32) / 255.0
    try:
        sm = json.load(open(os.path.join(ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
        sv = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))[:sm["frame_height"], :sm["frame_width"]]
    except (OSError, KeyError, ValueError):
        sm = sv = None

    def panel(x0_m, x1_m, mix, seed):
        """mix(xm) -> {set name: weight} per column; returns the composed panel."""
        c0, c1 = int(x0_m * PPU), int(x1_m * PPU)
        ys = (PH - (z_all[c0:c1] + 2.5) * PPU).astype(np.float64)
        Wp = c1 - c0
        wts = [mix(c0 / PPU + i / PPU) for i in range(Wp)]
        names = sorted({n for w in wts for n in w})
        img = np.empty((PH, Wp, 3), np.float32)
        img[:] = sky
        for s0 in range(0, Wp, 480):
            sl = slice(s0, min(Wp, s0 + 480))
            Y, X = np.mgrid[0:PH, sl.start:sl.stop]
            solid = Y > ys[X]
            fl = np.zeros(Y.shape + (4,), np.float32)
            bd = np.zeros(Y.shape + (4,), np.float32)
            for n in names:
                wcol = np.array([w.get(n, 0.0) for w in wts[sl]], np.float32)[None, :, None]
                if not wcol.any():
                    continue
                ft = sets[n]["fill"]
                fl += wcol * B._bilinear(ft, (X + c0).astype(np.float32), np.mod(Y.astype(np.float32), ft.shape[0]))
                bd += wcol * B.bend(sets[n]["band"], B.SURF_ROW, ys, X, Y, "normal")
            sub = img[:, sl]
            sub[solid] = fl[solid][:, :3]
            img[:, sl] = bd[..., :3] + (1 - bd[..., 3:4]) * sub
        slope = np.degrees(np.arctan(np.abs(np.gradient(ys))))
        rnd = random.Random(seed)
        xm = 0.5
        while xm < (Wp / PPU) - 0.5:
            X0 = int(xm * PPU)
            if slope[max(0, X0 - 20):X0 + 20].max() < 33.0:
                w = wts[X0]
                n = max(w, key=w.get) if rnd.random() < max(w.values()) else min(w, key=w.get)
                fr = rnd.choice(sets[n]["decor"])
                review._over(img, fr, X0 - 32, int(round(ys[X0])) - 64 + 6 + 2)
            xm += rnd.uniform(0.6, 1.4)
        if sv is not None:
            for xm in (1.5, Wp / PPU * 0.62):
                X0 = int(xm * PPU)
                review._over(img, sv, X0 - sm["frame_width"] // 2, int(round(ys[X0])) - sm["frame_height"] + int(round(sm["pivot"][1] * sm["frame_height"])) + 2)
        return img
    side = [panel(4.0, 14.0, lambda xm, v=v: {v: 1.0}, 178 + i) for i, v in enumerate(VARIANTS)]
    gap = np.empty((PH, 0, 3), np.float32)
    row1 = np.concatenate(side, axis=1)

    def border(xm, c=9.0, half=1.5):
        t = min(1.0, max(0.0, (xm - (c - half)) / (2 * half)))
        t = t * t * (3 - 2 * t)
        v0 = VARIANTS[0]
        return {"grass": 1.0 - t, v0: t} if 0 < t < 1 else ({"grass": 1.0} if t == 0 else {v0: 1.0})
    row2 = panel(0.0, 30.0, border, 1782)
    Wt = row2.shape[1]
    row1 = np.concatenate([row1, np.full((PH, Wt - row1.shape[1], 3), review.PAPER, np.float32)], axis=1) if row1.shape[1] < Wt else row1[:, :Wt]
    P = np.empty((620, Wt, 3), np.float32)
    P[:] = review.PAPER
    for j, v in enumerate(VARIANTS):
        b = pieces[f"ground_band_{v}"][0][0]
        P[40 + 150 * j:40 + 150 * j + 128, 8:8 + 1024] = sky
        review._over(P, np.repeat(np.repeat(b, 2, 0), 2, 1), 8, 40 + 150 * j)
        review._label(P, f"ground_band_{v} 512x64 at 2x (surface row 24): {', '.join(BIOMES[v])}", 8, 20 + 150 * j)
    for fname in [n for n in pieces if n.startswith("ground_fill_")][:1]:
        ft = pieces[fname][0][0]
        review._over(P, np.concatenate([ft, ft], axis=1)[:, :768], 1100, 40)
        review._label(P, f"{fname} 512x512 tiled in x (the seam at 512)", 1100, 20)
    x = 8
    for v in VARIANTS:
        for j, fr in enumerate(pieces[f"ground_decor_{v}"][0]):
            P[490:554, x:x + 64] = sky
            review._over(P, fr, x, 490)
            x += 72
        review._label(P, f"decor_{v} x3", x - 216, 470)
        x += 24
    lines = []
    for name, (frames, widths) in pieces.items():
        o = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
        n_ = [w for w in widths if w[0] < v3.OUTER_SPLIT]
        rng = lambda q: f"{min(w[1] for w in q):.1f}-{max(w[2] for w in q):.1f}" if q else "-"  # noqa: E731
        pal = min(v3.palette_hits(f, PLANET)[0] for f in frames) * 100
        m = v3.EDGE_MARGIN
        edge = [i for i, f in enumerate(frames) if name not in TILES and (f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any())]
        seam = f"; tiles: copies p99 {copy_diff(name):.0f}" if name in TILES else ""
        lines.append(f"{name}: ink {rng(o)} / {rng(n_)} px, palette {pal:.1f}%{seam}{'; EDGE ' + str(edge) if edge else ''}")
    titles = ["sand | stone | snow: each band bent along the same 10 m (hills, a 30 deg slope) over its fill (sand: ground_fill_sand; stone, snow: "
              "ground_fill), its decor upright, the surveyor at 1x",
              "a grass -> sand biome border at 9 m: the two bands, fills and decor crossfaded over 3 m (smoothstep), as UNITY would blend them"] \
        if PLANET == "earth" else \
        [f"{PLANET}'s {' | '.join(VARIANTS)} band bent along 10 m (hills, a 30 deg slope), each over its fill "
         f"({', '.join(FILL_OF.get(v, 'ground_fill') for v in VARIANTS)}), its decor upright, the surveyor at 1x",
         f"the {PLANET} regolith band -> {VARIANTS[0]} border at 9 m: bands and decor crossfaded over 3 m (smoothstep), as UNITY would blend them"]
    rows = []
    for t, im in zip(titles, (row1, row2)):
        lab = np.empty((22, Wt, 3), np.float32)
        lab[:] = review.PAPER
        review._label(lab, t[:235], 6, 4)
        rows += [lab, im]
    foot = np.empty((30 + 16 * len(lines), Wt, 3), np.float32)
    foot[:] = review.PAPER
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [P, foot])
    del rows, row1, row2, side, P, foot
    import time
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
    out = out or os.path.join(out_dir, f"review_b181_{PLANET}_ground_preview.png" if PART == "b181" else f"review_b178_{PLANET}_ground_variants_preview.png")
    shape = img.shape
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


def preview_lips(out_dir, pieces=None, out=None, footnote=None):
    """B-180: each lip on a rounded cliff of its own band at 1x (B-175's test profile from 12.5 to 20.5 m: the 30 deg slope, the
    plateau, the cliff, the valley) over its fill, two of its decor upright, the surveyor on the plateau and in the valley; beside
    them the planet's B-175 band with its own lip; then each lip at 2x and the ink / palette / edge lines. The bands, fills and
    decor are read from the exports (byte-identical to the accepted renders); only the lips are drawn here."""
    import json
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    if pieces is None:
        pieces = {}
        for n in PIECES:
            img, wd = render_piece(n, 0)
            pieces[n] = ([img], wd)
    E = os.path.join(ART, "terrain", PLANET)
    rd = lambda name: pngio.read_png_np(os.path.join(E, name + "_color.png"))  # noqa: E731
    sets = [(f"{v}: ground_band_{v} + ground_lip_{v} (NEW) over {FILL_OF.get(v, 'ground_fill')}", rd(f"ground_band_{v}"),
             rd(FILL_OF.get(v, "ground_fill")), pieces[f"ground_lip_{v}"][0][0], [rd(f"ground_decor_{v}_{i + 1}") for i in range(3)])
            for v in VARIANTS]
    sets.append((f"for comparison: B-175's ground_band + ground_lip ({'grass' if PLANET == 'earth' else 'crust'})", rd("ground_band"), rd("ground_fill"),
                 rd("ground_lip"), [rd(f"ground_decor_{i + 1}") for i in (0, 3)]))
    _xs, z_all = B.profile()
    x0_m, x1_m, PH = 12.5, 20.5, 512                                                          # the plateau at row 224: the 192 px surveyor fits above it
    c0 = int(x0_m * PPU)
    Wp = int(x1_m * PPU) - c0
    ys = (PH - (z_all[c0:c0 + Wp] + 2.0) * PPU).astype(np.float64)
    Y, X = np.mgrid[0:PH, 0:Wp]
    solid = Y > ys[X]
    slope = np.degrees(np.arctan(np.abs(np.gradient(ys))))
    s0 = int((15.0 - x0_m) * PPU)
    brink = s0 + int(np.argmax(slope[s0:] > 25.0))                                            # where the drop passes 25 deg (B-175's rule)
    sky = np.array(v3.hex_rgb(v3.PALETTES[PLANET]["sky"]), np.float32) / 255.0
    try:
        sm = json.load(open(os.path.join(ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
        sv = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))[:sm["frame_height"], :sm["frame_width"]]
    except (OSError, KeyError, ValueError):
        sm = sv = None
    panels = []
    for title, band, fill, lip, decor in sets:
        bt, ft = B._premul(band), B._premul(fill)
        img = np.empty((PH, Wp, 3), np.float32)
        img[:] = sky
        fv = B._bilinear(ft, (X + c0).astype(np.float32), np.mod(Y.astype(np.float32), ft.shape[0]))
        img[solid] = fv[solid][:, :3]
        bd = B.bend(bt, B.SURF_ROW, ys, X, Y, "normal")
        img = bd[..., :3] + (1 - bd[..., 3:4]) * img
        del fv, bd
        for xm, k in ((13.9, 0), (19.7, 1)):
            X0 = int((xm - x0_m) * PPU)
            review._over(img, decor[k], X0 - 32, int(round(ys[X0])) - 64 + 6 + 2)
        xl = brink - 10
        review._over(img, lip, xl - int(LIP_PIV[0] * 128), int(round(ys[xl])) - int(round((1 - LIP_PIV[1]) * 96)))
        if sv is not None:
            for xm in (15.2, 18.9):
                X0 = int((xm - x0_m) * PPU)
                review._over(img, sv, X0 - sm["frame_width"] // 2, int(round(ys[X0])) - sm["frame_height"] + int(round(sm["pivot"][1] * sm["frame_height"])) + 2)
        lab = np.empty((22, Wp, 3), np.float32)
        lab[:] = review.PAPER
        review._label(lab, title[:84], 4, 6, scale=1)
        panels.append(np.vstack([lab, img]))
    gap = np.empty((PH + 22, 8, 3), np.float32)
    gap[:] = review.PAPER
    row = np.concatenate(sum(([p, gap] for p in panels), [])[:-1], axis=1)
    Wt = row.shape[1]
    P = np.empty((260, Wt, 3), np.float32)
    P[:] = review.PAPER
    x = 8
    for name in list(PIECES) + ["ground_lip"]:
        fr = pieces[name][0][0] if name in pieces else rd("ground_lip")
        P[40:232, x:x + 256] = sky
        review._over(P, np.repeat(np.repeat(fr, 2, 0), 2, 1), x, 40)
        review._label(P, f"{name} 128x96 at 2x", x, 20, scale=1)
        x += 280
    lines = []
    for name, (frames, widths) in pieces.items():
        o = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
        n_ = [w for w in widths if w[0] < v3.OUTER_SPLIT]
        rng = lambda q: f"{min(w[1] for w in q):.1f}-{max(w[2] for w in q):.1f}" if q else "-"  # noqa: E731
        pal = min(v3.palette_hits(f, PLANET)[0] for f in frames) * 100
        m = v3.EDGE_MARGIN
        edge = [i for i, f in enumerate(frames) if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any()]
        lines.append(f"{name}: ink {rng(o)} / {rng(n_)} px, palette {pal:.1f}%{'; EDGE ' + str(edge) if edge else ''}")
    head = np.empty((22, Wt, 3), np.float32)
    head[:] = review.PAPER
    review._label(head, f"B-180 {PLANET} cliff lips at 1x: each on a rounded cliff of its own band (B-175's profile 12.5-20.5 m), the surveyor"[:150], 6, 4)
    foot = np.empty((30 + 16 * len(lines), Wt, 3), np.float32)
    foot[:] = review.PAPER
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack([head, row, P, foot])
    import time
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
    out = out or os.path.join(out_dir, f"review_b180_{PLANET}_lips_preview.png")
    np.clip(img, 0.0, 1.0, out=img)
    u8 = np.empty(img.shape[:2] + (4,), np.uint8)
    u8[..., :3] = np.rint(img * 255.0)
    u8[..., 3] = 255
    pngio.write_png(out, u8)
    print("written", out, u8.shape[1], "x", u8.shape[0])
    for ln in lines:
        print(ln)


def preview_puffs(out_dir, planets=("earth", "mars"), pieces=None, out=None, footnote=None):
    """B-190: per planet, the exported soil dig_puff (read from Art) and then each material's new puff, every row its 8 frames at
    1x over the planet's sky with its own ground band under the pivot row (the dig's ground line), frame 2 (the old face frame)
    at 2x on the right; the palette / edge lines under. pieces: this planet's rendered sheets (main()'s export review)."""
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    keep = (PLANET, PART)
    FW, GAP, ROWH = 128, 4, 22 + 256
    rows, lines = [], []
    for p in planets:
        use_planet(p, "puffs")
        E = os.path.join(ART, "terrain", p)
        rd = lambda name: pngio.read_png_np(os.path.join(E, name + "_color.png"))  # noqa: E731
        soil = rd("dig_puff")
        sets = [(f"{p} soil: dig_puff (exported, for comparison)", [soil[:, i * (FW + GAP):i * (FW + GAP) + FW] for i in range(8)], rd("ground_band"))]
        for v in PUFF_VARIANTS[p]:
            name = f"dig_puff_{v}"
            if pieces is not None and name in pieces:
                frames = pieces[name][0]
            else:
                frames = [render_piece(name, k)[0] for k in range(8)]
            sets.append((f"{p} {v}: {name} (NEW)", frames, rd(f"ground_band_{v}")))
            pal = min(v3.palette_hits(f, p)[0] for f in frames) * 100
            m = v3.EDGE_MARGIN
            edge = [i for i, f in enumerate(frames) if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any()]
            lines.append(f"{name}: 8 frames 128x128, pivot (0.5, 0.25), palette {pal:.1f}%{'; EDGE ' + str(edge) if edge else '; inside the edge margin'}")
        sky = np.array(v3.hex_rgb(v3.PALETTES[p]["sky"]), np.float32) / 255.0
        for title, frames, band in sets:
            Wr = 8 * (FW + GAP) + 16 + 2 * FW
            img = np.empty((ROWH, Wr, 3), np.float32)
            img[:] = review.PAPER
            review._label(img, title, 4, 6, scale=1)
            strip = np.empty((FW, 8 * (FW + GAP), 3), np.float32)                             # sky, then the band's surface row on the pivot row 96
            strip[:] = sky
            bt = np.tile(band, (1, (strip.shape[1] + band.shape[1] - 1) // band.shape[1], 1))[:, :strip.shape[1]]
            y0 = FW - int(round(0.25 * FW)) - B.SURF_ROW
            review._over(strip, bt[:FW - y0], 0, y0)
            for i, f in enumerate(frames):
                review._over(strip, f, i * (FW + GAP), 0)
            img[22 + 64:22 + 64 + FW, :strip.shape[1]] = strip
            big = np.empty((2 * FW, 2 * FW, 3), np.float32)
            big[:] = sky
            review._over(big, np.repeat(np.repeat(bt[:FW - y0, :FW], 2, 0), 2, 1), 0, 2 * y0)
            review._over(big, np.repeat(np.repeat(frames[1], 2, 0), 2, 1), 0, 0)
            img[22:22 + 2 * FW, Wr - 2 * FW:] = big
            rows.append(img)
    use_planet(*keep)
    Wt = rows[0].shape[1]
    head = np.empty((22, Wt, 3), np.float32)
    head[:] = review.PAPER
    review._label(head, ("B-191" if planets[0] in ("mercury", "venus") else "B-190") + " dig puffs in each ground's material (draw_puff, the clods behind the billows): 8 frames at 1x over the band, frame 2 at 2x", 6, 4)
    foot = np.empty((30 + 16 * len(lines), Wt, 3), np.float32)
    foot[:] = review.PAPER
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack([head] + rows + [foot])
    import time
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
    out = out or os.path.join(out_dir, "review_b190_dig_puffs_preview.png" if planets[0] in ("earth", "mars") else "review_b191_dig_puffs_preview.png")
    np.clip(img, 0.0, 1.0, out=img)
    u8 = np.empty(img.shape[:2] + (4,), np.uint8)
    u8[..., :3] = np.rint(img * 255.0)
    u8[..., 3] = 255
    pngio.write_png(out, u8)
    print("written", out, u8.shape[1], "x", u8.shape[0])
    for ln in lines:
        print(ln)


def preview_fills(out_dir, planets=("earth", "mars"), pieces=None, out=None, footnote=None):
    """B-192: per planet, two tiles of the variant's fill (read from Art) with the new buried details scattered by a seed as
    U-167 will, each detail at 2x on the right; under it the planet's D-165 fill_decor on its ground_fill for comparison."""
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    keep = (PLANET, PART)
    rows, lines = [], []
    for p in planets:
        use_planet(p, "fills")
        v, lst = FILL_PIECES[p]
        E = os.path.join(ART, "terrain", p)
        rd = lambda name: pngio.read_png_np(os.path.join(E, name + "_color.png"))  # noqa: E731
        fill = rd(FILL_OF[v])[..., :3].astype(np.float32) / 255.0
        frames = []
        for i, (dn, _fn, w, h) in enumerate(lst):
            name = f"fill_decor_{v}_{i + 1}"
            fr = pieces[name][0][0] if pieces is not None and name in pieces else render_piece(name, 0)[0]
            frames.append((name, dn, fr))
            m = v3.EDGE_MARGIN
            edge = fr[:m, :, 3].any() or fr[-m:, :, 3].any() or fr[:, :m, 3].any() or fr[:, -m:, 3].any()
            lines.append(f"{name} ({dn}) {w}x{h}, pivot centred, palette {v3.palette_hits(fr, p)[0] * 100:.1f}%{'; EDGE' if edge else '; inside the edge margin'}")
        field = np.tile(fill, (1, 2, 1)).copy()                                                # two tiles: 16 m x 8 m of the cutaway
        rnd, boxes = random.Random(192), []
        for j in range(80):
            if len(boxes) >= 18:
                break
            _n, _dn, fr = frames[j % len(frames)]
            h, w = fr.shape[:2]
            X0, Y0 = rnd.randint(8, field.shape[1] - w - 8), rnd.randint(8, field.shape[0] - h - 8)
            if any(X0 < bx + bw + 24 and bx < X0 + w + 24 and Y0 < by + bh + 24 and by < Y0 + h + 24 for bx, by, bw, bh in boxes):
                continue
            boxes.append((X0, Y0, w, h))
            review._over(field, fr, X0, Y0)
        side = np.empty((field.shape[0], 2 * 128 + 16, 3), np.float32)
        side[:] = review.PAPER
        y = 0
        for _n, dn, fr in frames:
            h, w = fr.shape[:2]
            crop = np.repeat(np.repeat(fill[:h, :w], 2, 0), 2, 1).copy()
            review._over(crop, np.repeat(np.repeat(fr, 2, 0), 2, 1), 0, 0)
            review._label(side, f"{dn} at 2x", 8, y + 2, scale=1)
            side[y + 14:y + 14 + 2 * h, 8:8 + 2 * w] = crop
            y += 14 + 2 * h + 8
        top = np.hstack([field, side])
        gf = rd("ground_fill")[..., :3].astype(np.float32) / 255.0
        comp = np.tile(gf, (1, 3, 1))[:128, :top.shape[1]].copy()
        x = 24
        for i in range(len(B.FILL_DECOR.get(p, []))):
            fr = rd(f"fill_decor_{i + 1}")
            review._over(comp, fr, x, 64 - fr.shape[0] // 2)
            x += fr.shape[1] + 48
        for title, img in ((f"{p}: {FILL_OF[v]} (two tiles) with the NEW fill_decor_{v}_1..{len(lst)} scattered by a seed (as U-167), each at 2x", top),
                           (f"{p}: for comparison, D-165's fill_decor_1..{len(B.FILL_DECOR.get(p, []))} on ground_fill", comp)):
            lab = np.empty((22, top.shape[1], 3), np.float32)
            lab[:] = review.PAPER
            review._label(lab, title, 4, 6, scale=1)
            rows += [lab, img]
    use_planet(*keep)
    Wt = rows[0].shape[1]
    head = np.empty((22, Wt, 3), np.float32)
    head[:] = review.PAPER
    review._label(head, "B-192 buried details for the newest fills (D-165's pattern: upright, pivot centred, scattered in the cutaway, never rotated)", 6, 4)
    foot = np.empty((30 + 16 * len(lines), Wt, 3), np.float32)
    foot[:] = review.PAPER
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack([head] + rows + [foot])
    import time
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
    out = out or os.path.join(out_dir, "review_b192_fill_decor_preview.png")
    np.clip(img, 0.0, 1.0, out=img)
    u8 = np.empty(img.shape[:2] + (4,), np.uint8)
    u8[..., :3] = np.rint(img * 255.0)
    u8[..., 3] = 255
    pngio.write_png(out, u8)
    print("written", out, u8.shape[1], "x", u8.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_ground_variants_v3.py <preview dir> [planet] [lips | b181] | <dir> puffs|fills [planets]
    if len(sys.argv) > 2 and sys.argv[2] in ("puffs", "fills"):                            # [planets, comma-separated]
        (preview_puffs if sys.argv[2] == "puffs" else preview_fills)(sys.argv[1], tuple(sys.argv[3].split(",")) if len(sys.argv) > 3 else ("earth", "mars"))
        fakegp.restore()
        sys.exit(0)
    if len(sys.argv) > 2:
        use_planet(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "variants")
    (preview_lips if PART == "lips" else preview)(sys.argv[1])
    fakegp.restore()
