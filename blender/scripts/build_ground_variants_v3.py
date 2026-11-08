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
          "frost": ["polar cap", "polar layered terrain"]}
DECOR = {"sand": ["dry_tuft", "shells", "sandstone_rock"], "stone": ["lichen_boulder", "shore_pebbles", "thrift"],
         "snow": ["snowy_shrub", "snow_rock", "dry_stalks"], "frost": ["frost_boulder", "ice_blocks", "frost_vent"]}
FILL_OF = {"sand": "ground_fill_sand"}                   # a variant's own fill (the rest lie over the planet's ground_fill)


def extra_colours():
    P = v3.PALETTES[PLANET]
    sh = lambda k: v3.shadow_of(P[k], PLANET)  # noqa: E731
    dp = lambda k: v3.deep_of(P[k], PLANET)  # noqa: E731
    if PLANET == "mars":
        return {"frost": P["offwhite"], "frost_sh": sh("teal"), "snow": P["offwhite"], "snow_sh": sh("teal"), "ice": P["teal"], "ice_sh": dp("teal"),
                "rock": dp("sky"), "rock_sh": P["brown"], "rock_lit": sh("sky"), "dust": dp("red"), "vent": P["brown"], "plume": P["offwhite"]}
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


def _chipped(cx, cz, rx, rz, seed, rot=0.0, n=8):
    """A chipped, rounded lump: n corners at jittered angles and radii (the chips), corner-cut twice (Chaikin), so its
    facets stay flat-ish but every corner is soft: no flat top, no vertical side, nothing that reads as a cube."""
    rnd = random.Random(seed)
    poly = []
    for i in range(n):
        a = TAU * (i + rnd.uniform(-0.3, 0.3)) / n
        q = rnd.uniform(0.88, 1.06)
        poly.append((rx * q * math.cos(a), rz * q * math.sin(a)))
    for _ in range(2):
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
    r_o = top - LIP_CZ
    sx, sz = r_o * math.sin(math.radians(76)), LIP_CZ + r_o * math.cos(math.radians(76))
    left = [(sx - 0.018 + 0.05 * t * t, sz - 0.55 * t) for t in [i / 10 for i in range(11)]]
    right = [(sx + 0.018 + 0.042 * t * t - 0.012 * t, sz - 0.55 * t) for t in [i / 10 for i in range(11)]]
    G.stroke(d, left + right[::-1], M["sand_i"], I, cyclic=True)                             # the pour
    for j, (x, z, r) in enumerate(((0.50, -0.86 + 0.03, 0.016), (0.40, -0.70, 0.012), (0.47, -0.62, 0.010), (0.43, -0.80, 0.013))):
        G.stroke(d, G.lumpy_ellipse(x, z, r * 1.2, r, n=8, lump=0.1, seed=1860 + j), M["sand_sh_i"], I, cyclic=True)


def lip_stone(d, M, k=0):
    """The rock crust's slab rounding the brink and jutting a little past the face (a rounded ledge, no square corner): a lit
    rim along its top and corner, the shade along its inner edge, a joint, lichen on the top and the corner."""
    top = 0.04
    outer, inner = _hood(top, 0.17, 96)
    lit_o, lit_i = _hood(top, 0.035, 60)
    _o2, inner2 = _hood(top, 0.12, 96)
    G.stroke(d, outer + inner, M["rock"], 0.0, cyclic=True)
    G.stroke(d, lit_o + lit_i, M["rock_lit"], 0.0, cyclic=True)
    G.stroke(d, inner2 + inner[::-1], M["rock_sh"], 0.0, cyclic=True)
    G.stroke(d, outer, M["ink"], O)
    G.seam(d, inner, M["ink"])
    G.seam(d, [outer[-1], inner[0]], M["ink"])
    G.seam(d, [(-0.32, top), (-0.305, top - 0.07), (-0.325, top - 0.15)], M["ink"])           # a joint
    G.hatch(d, -0.20, -0.07, M["ink"], n=3, length=0.05, spacing=0.03, angle_deg=60, seed=7)
    rnd = random.Random(1870)
    for cx, cz in ((-0.46, -0.03), (0.10, -0.06), (0.27, -0.17)):
        _lichen(d, M, cx, cz, rnd, n=5, spread=0.05)


def lip_snow(d, M, k=0):
    """A snow cornice: the drift crust's hood swelling past the face and curling under, its blue underside, three rounded drips
    under the curl, a wind line on top, glints, two clumps falling."""
    top = 0.06
    outer, inner = _hood(top, 0.15, 118, bulge=0.07)
    _o2, inner2 = _hood(top, 0.10, 118)
    G.stroke(d, outer + inner, M["snow"], 0.0, cyclic=True)
    G.stroke(d, inner2 + inner[::-1], M["snow_sh"], 0.0, cyclic=True)
    end = [outer[-1], inner[0]]
    for j, t in enumerate((0.2, 0.5, 0.8)):                                                   # drips under the curl
        x = end[0][0] + (end[1][0] - end[0][0]) * t
        z = end[0][1] + (end[1][1] - end[0][1]) * t
        ln = (0.07, 0.11, 0.06)[j]
        G.stroke(d, G.lumpy_ellipse(x, z - ln * 0.45, 0.018, ln * 0.55, n=12, lump=0.04, seed=1880 + j), M["snow_sh_i"], I, cyclic=True)
    G.stroke(d, outer + [inner[0]], M["ink"], O)                                               # the curl's underside is in the air: inked
    G.seam(d, inner, M["ink"])
    G.seam(d, G.bezier((-0.50, 0.0), (-0.32, 0.03), (-0.12, -0.01), n=6), M["ink"])
    rnd = random.Random(1881)
    for i in range(6):
        a = math.radians(rnd.uniform(5, 100))
        rr = top - LIP_CZ - 0.07
        G.stroke(d, G.lumpy_ellipse(rr * math.sin(a), LIP_CZ + rr * math.cos(a), 0.016, 0.011, n=8, lump=0.1, seed=i), M["snow_sh"], 0.0, cyclic=True)
    for j, (x, z, r) in enumerate(((0.56, -0.70, 0.035), (0.50, -0.83, 0.025))):
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
    for j, (x, z, r) in enumerate(((0.50, -0.52, 0.020), (0.46, -0.66, 0.016), (0.53, -0.79, 0.013))):
        G.stroke(d, G.lumpy_ellipse(x, z, r * 1.3, r, n=10, lump=0.12, seed=1890 + j), M["frost_i"], I, cyclic=True)


LIPS = {"sand": lip_sand, "stone": lip_stone, "snow": lip_snow, "frost": lip_frost}
LIP_PIV = (0.55, 0.6)


# ---------------------------------------------------------------- the pieces, the render, the export API (render.py ground_strip_set)

BAND_PIV = (0.0, (B.BAND_H - B.SURF_ROW) / B.BAND_H)
PART = "variants"


def _pieces(planet, part="variants"):
    """-> (the planet's pieces {name: (w, h, pivot, frames, draw)}, its tiling pieces). part "lips": B-180's ground_lip_<variant>
    only (their own manifest rows, so the accepted variant exports are not re-written)."""
    if part == "lips":
        return {f"ground_lip_{v}": (128, 96, LIP_PIV, 1, LIPS[v]) for v in PLANET_VARIANTS[planet]}, ()
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
    VARIANTS = PLANET_VARIANTS[planet]
    PIECES, TILES = _pieces(planet, part)
    KEYS = _keys()


def sheets():
    S, allw = {}, []
    for name, p in PIECES.items():
        for k in range(p[3]):
            img, wd = render_piece(name, k)
            S[_kn(name, k)] = ([img], wd)
            allw += wd
    return S, allw


def pieces_of(S):
    if PART == "lips":
        return dict(S)
    out = {n: S[n] for n in TILES}
    for v in VARIANTS:
        ks = [f"ground_decor_{v}_{i + 1}" for i in range(3)]
        out[f"ground_decor_{v}"] = ([S[k][0][0] for k in ks], sum((S[k][1] for k in ks), []))
    return out


def copy_diff(name):
    import numpy as np
    w0, h0 = PIECES[name][0], PIECES[name][1]
    two, _w = render_piece(name, 0, mx=2, mz=2 if name == "ground_fill_sand" else 1, ss=1)
    p = float(np.percentile(np.abs(two[:h0, :w0].astype(np.int32) - two[:h0, w0:2 * w0].astype(np.int32)), 99))
    if name == "ground_fill_sand":
        p = max(p, float(np.percentile(np.abs(two[:h0, :w0].astype(np.int32) - two[h0:2 * h0, :w0].astype(np.int32)), 99)))
    return p


def sheet_meta(kn, frames):
    import numpy as np
    base = kn.rsplit("_", 1)[0] if kn.startswith("ground_decor_") else kn
    w, h, piv, _n, _fn = PIECES[base]
    sheet = np.zeros((h, w, 4), np.uint8)
    sheet[:] = frames[0]
    meta = {"key": KEYS[kn], "style": "v3", "contract": "v3.2 11.9", "frame_width": w, "frame_height": h, "columns": 1, "gutter": v3.GUTTER,
            "frames": 1, "fps": v3.FPS, "pivot": [round(piv[0], 6), round(piv[1], 6)], "facing": "right", "ppu": PPU, "animations": []}
    if kn.startswith("ground_band_"):
        v = kn.rsplit("_", 1)[1]
        meta.update({"tile_x": True, "repeat_px": B.BAND_W, "surface_row": B.SURF_ROW, "above_px": B.SURF_ROW, "below_px": B.BAND_H - B.SURF_ROW,
                     "variant": v, "biomes": BIOMES[v], "fill": FILL_OF.get(v, "ground_fill"),
                     "mapping": "as ground_band: u = world x x 64 mod 512; v = 24 - (normal distance from the outline x 64); the sprite pivot is ON row 24",
                     "note": f"B-178: {PLANET.capitalize()}'s {v} band ({', '.join(BIOMES[v])}); "
                             + ("plains and forest keep ground_band" if PLANET == "earth" else "the rest of Mars keeps ground_band (U-159)")
                             + "; crossfade the two bands at a biome border"})
    elif kn.startswith("ground_lip_"):
        v = kn.rsplit("_", 1)[1]
        meta.update({"brink": True, "variant": v, "biomes": BIOMES[v], "band": f"ground_band_{v}",
                     "note": f"B-180: the {v} band's cliff lip (as ground_lip): drawn for a drop to the right; mirror x for a drop to the left"})
    elif kn == "ground_fill_sand":
        meta.update({"tile_x": True, "tile_y": True, "world_space": True, "standalone": True, "wrap": "repeat", "variant": "sand",
                     "mapping": "as ground_fill: u = x x 64 mod 512, v = -y x 64 mod 512; a standalone texture (Repeat wrap); strata only (D-165)"})
    else:
        v, i = kn.split("_")[2], int(kn.rsplit("_", 1)[1]) - 1
        meta.update({"upright": True, "variant": v, "decor": DECOR[v][i], "note": f"B-178: {PLANET.capitalize()}'s {v} biomes' decor; scatter along the curve, never rotated"})
    problems = [p for p in v3.validate_sheet(meta, sheet.shape) if "sum of clip lengths" not in p]
    if kn not in TILES:
        m = v3.EDGE_MARGIN
        im = frames[0]
        if im[:m, :, 3].any() or im[-m:, :, 3].any() or im[:, :m, 3].any() or im[:, -m:, 3].any():
            problems.append(f"touches the {m} px edge")
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
    return out, within, f"{len(out)} keys, contract v3.2 11.9 ({'B-180 lips' if PART == 'lips' else 'B-178 variants'})"


def main(out, S=None, allw=None, footnote=None):
    if S is None:
        S, allw = sheets()
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
    if "ground_fill_sand" in pieces:
        ft = pieces["ground_fill_sand"][0][0]
        review._over(P, np.concatenate([ft, ft], axis=1)[:, :768], 1100, 40)
        review._label(P, "ground_fill_sand 512x512 tiled in x (the seam at 512)", 1100, 20)
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
        [f"{PLANET}'s {' | '.join(VARIANTS)} band bent along 10 m (hills, a 30 deg slope) over the {PLANET} ground_fill, its decor upright, the surveyor at 1x",
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
    out = out or os.path.join(out_dir, f"review_b178_{PLANET}_ground_variants_preview.png")
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


if __name__ == "__main__":                       # python -I build_ground_variants_v3.py <preview dir> [planet] [lips]
    if len(sys.argv) > 2:
        use_planet(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "variants")
    (preview_lips if PART == "lips" else preview)(sys.argv[1])
    fakegp.restore()
