"""Builds blender/sources/backgrounds/earth_bands.blend: Earth depth bands (B-083, contract §9
depth-bands row) as real-time meshes.

Per region a collection `ridge_<region>`: a terrain strip x -128..128 m (one 256 m period),
depth 20..60 m behind the play plane (Blender +Y = away from the camera), heights from sums
of sines with whole-number periods over 256 m (so the strip tiles exactly), colour as a
periodic vertex-colour field, and low-poly trees (cones for conifers, blobs on stems for
broadleaf) placed with wrap-around duplicates one period over, so tiled strips line up tree for
tree. One shared collection `skyline_far`: distant mountains x -256..256 (512 m period), depth
150..400 m, snow above a line. Colours and character from the v1 gen_backdrop3d presets
(earth = forest, earth_desert, earth_taiga, earth_coast) plus plains and tundra derived from
them. One material per mesh reading the colour attribute; meridian/model.py bakes it.

  blender --background --factory-startup --python blender/scripts/build_depthbands.py
"""
import math
import os
import random
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "backgrounds", "earth_bands.blend")
PERIOD = 256.0
TRI_BUDGET = 7600                 # contract 8 k, minus margin

REGIONS = {
    #          ground colours (sRGB)                hill  rise  trees conifer  tree h     extras
    "forest": dict(ground=[(64, 92, 48), (82, 104, 56)], hill=6, rise=12, trees=220, conifer=0.6, tree_h=(6, 12), haze=(184, 202, 214),
                   needle=[(30, 58, 38), (40, 70, 44)], leaf=[(46, 78, 34), (62, 96, 40), (84, 112, 46)], seed=1),
    "plains": dict(ground=[(110, 134, 64), (132, 150, 76)], hill=3, rise=10, trees=22, conifer=0.2, tree_h=(5, 9), haze=(190, 204, 214),
                   needle=[(36, 64, 40)], leaf=[(62, 96, 40), (84, 112, 46)], seed=2),
    "desert": dict(ground=[(214, 182, 128), (196, 160, 108)], hill=4, rise=24, trees=0, conifer=0.0, tree_h=(0, 0),
                   strata=((232, 200, 150), 4.5), terrace=5.0, seed=3),
    "coast":  dict(ground=[(186, 174, 132), (140, 146, 92)], hill=2, rise=4, trees=45, conifer=0.9, tree_h=(5, 9), haze=(190, 210, 222),
                   needle=[(32, 60, 40), (44, 72, 46)], leaf=[(56, 92, 40)],
                   sea=dict(y=42.0, level=-1.5, shallow=(70, 176, 178), deep=(26, 70, 122)), seed=4),
    "taiga":  dict(ground=[(58, 80, 58), (72, 92, 64)], hill=7, rise=14, trees=260, conifer=0.95, tree_h=(7, 14), haze=(186, 198, 210),
                   needle=[(24, 48, 36), (32, 58, 42), (40, 66, 46)], leaf=[(52, 80, 44)],
                   snow=((236, 240, 246), 24.0), seed=5),
    "tundra": dict(ground=[(150, 150, 128), (176, 170, 146)], hill=4, rise=12, trees=8, conifer=1.0, tree_h=(3, 6),
                   needle=[(48, 66, 50)], leaf=[(80, 92, 60)], snow=((240, 244, 248), 6.0), seed=6),
}


def lin(c):
    out = []
    for v in c:
        v = v / 255.0
        out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def periodic(rng, x, period, terms, amp):
    """Sum of sines with whole-number periods over `period` (tiles exactly)."""
    v = 0.0
    for k, ph, a in terms:
        v += a * math.sin(2 * math.pi * k * x / period + ph)
    return v * amp


def make_terms(rng, n, kmax):
    return [(rng.randint(1, kmax), rng.uniform(0, 2 * math.pi), rng.uniform(0.4, 1.0) / (1 + 0.3 * i)) for i in range(n)]


def vc_material(name, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "col"
    nt.links.new(attr.outputs["Color"], pr.inputs["Base Color"])
    pr.inputs["Roughness"].default_value = 0.92
    if emit:                                          # B-092 Venus vents: the colour attribute also glows
        nt.links.new(attr.outputs["Color"], pr.inputs["Emission Color"])
        pr.inputs["Emission Strength"].default_value = emit
    return m


class Builder:
    def __init__(self):
        self.verts, self.faces, self.cols = [], [], []
        self.islands = []                                  # B-102 round 2: (v0, v1) vertex ranges of the trees

    def quad_grid(self, xs, ys, hfun, cfun):
        base = len(self.verts)
        nx, ny = len(xs), len(ys)
        for y in ys:
            for x in xs:
                self.verts.append((x, y, hfun(x, y)))
                self.cols.append(cfun(x, y, self.verts[-1][2]))
        for j in range(ny - 1):
            for i in range(nx - 1):
                a = base + j * nx + i
                self.faces.append((a, a + 1, a + nx + 1, a + nx))

    def cone(self, cx, cy, z0, r, h, sides, col):
        base = len(self.verts)
        for s in range(sides):
            a = 2 * math.pi * s / sides
            self.verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z0))
            self.cols.append(col)
        self.verts.append((cx, cy, z0 + h))
        self.cols.append(col)
        tip = len(self.verts) - 1
        for s in range(sides):
            self.faces.append((base + s, base + (s + 1) % sides, tip))

    def blob(self, cx, cy, cz, r, col):
        """Octahedron-ish 12-sided blob (2 rings x 6), cheap broadleaf crown."""
        base = len(self.verts)
        ring = []
        for zz, rr in ((-0.45, 0.8), (0.35, 0.85)):
            for s in range(6):
                a = 2 * math.pi * s / 6 + (0.5 if zz > 0 else 0)
                ring.append(len(self.verts))
                self.verts.append((cx + r * rr * math.cos(a), cy + r * rr * math.sin(a), cz + r * zz))
                self.cols.append(col)
        self.verts.append((cx, cy, cz - r))
        self.cols.append(col)
        bot = len(self.verts) - 1
        self.verts.append((cx, cy, cz + r * 1.1))
        self.cols.append(col)
        top = len(self.verts) - 1
        lo, hi = ring[:6], ring[6:]
        for s in range(6):
            self.faces.append((lo[s], lo[(s + 1) % 6], bot)[::-1])
            self.faces.append((hi[s], hi[(s + 1) % 6], top))
            self.faces.append((lo[s], lo[(s + 1) % 6], hi[s]))
            self.faces.append((lo[(s + 1) % 6], hi[(s + 1) % 6], hi[s]))
        del base

    def author_uvs(self, me, ground_verts):
        """Authored UVs (B-102 round 2) so the glTF export never splits a vertex: the ground strip
        projected from the top into the upper half (one island, a heightfield never overlaps),
        every tree projected from the camera side into its own cell of a grid in the lower half
        (front and back faces share texels: per-tree colours are flat and the normals are smooth)."""
        uv = me.uv_layers.new(name="UVMap").data
        vs = self.verts
        xs = [v[0] for v in vs[:ground_verts]] or [0.0]
        ys = [v[1] for v in vs[:ground_verts]] or [0.0]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        n = len(self.islands)
        cols = max(1, int(math.ceil(math.sqrt(n * 2.0))))
        rows = max(1, int(math.ceil(n / cols)))
        cw, ch = 1.0 / cols, 0.5 / rows
        cell_of = {}
        for k, (a, b) in enumerate(self.islands):
            r, c = divmod(k, cols)
            px = [vs[i][0] for i in range(a, b)]
            pz = [vs[i][2] for i in range(a, b)]
            bx0, bx1, bz0, bz1 = min(px), max(px), min(pz), max(pz)
            for i in range(a, b):
                cell_of[i] = (c * cw + 0.08 * cw + 0.84 * cw * (vs[i][0] - bx0) / max(bx1 - bx0, 1e-6),
                              r * ch + 0.08 * ch + 0.84 * ch * (vs[i][2] - bz0) / max(bz1 - bz0, 1e-6))
        for poly in me.polygons:
            for li in poly.loop_indices:
                i = me.loops[li].vertex_index
                if i < ground_verts:
                    uv[li].uv = ((vs[i][0] - x0) / max(x1 - x0, 1e-6), 0.52 + 0.47 * (vs[i][1] - y0) / max(y1 - y0, 1e-6))
                else:
                    uv[li].uv = cell_of.get(i, (0.0, 0.0))

    def tris(self):
        return sum(len(f) - 2 for f in self.faces)

    def mesh(self, name, coll, emit=0.0, smooth_from=None, ground_verts=0):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        me.update()
        ca = me.color_attributes.new("col", "FLOAT_COLOR", "POINT")
        for i, c in enumerate(self.cols):
            ca.data[i].color = c
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        me.materials.append(vc_material(name + "_mat", emit))
        for p in me.polygons:                                      # B-102 round 2: everything smooth, no sharp split
            p.use_smooth = smooth_from is not None               # (the split and the smart-project islands doubled the
        if smooth_from is not None and self.islands:              # vertex count and read faceted in the game)
            self.author_uvs(me, ground_verts)
        return ob


def ridge(region, R, coll):
    rng = random.Random(R["seed"])
    hill_t, rise_t, col_t = make_terms(rng, 5, 8), make_terms(rng, 4, 4), make_terms(rng, 4, 10)
    g0, g1 = R["ground"]
    xs = [-PERIOD / 2 + 2.0 * i for i in range(129)]                 # 2 m spacing, both ends on the period
    ys = [20.0 + 5.0 * j for j in range(9)]                          # 20..60 m depth
    sea = R.get("sea")
    craters = [(rng.uniform(-PERIOD / 2, PERIOD / 2), rng.uniform(24.0, 56.0), rng.uniform(*R.get("crater_r", (4.0, 14.0))))
               for _ in range(R.get("craters", 0))]                   # B-092 Mercury: raised rims, shallow bowls
    if R.get("cloud"):                                               # B-092 Venus deck: long smooth heaps, no fine hills
        hill_t = make_terms(rng, 4, 3)

    def h(x, y):
        d = (y - 20.0) / 40.0                                        # 0 front .. 1 back
        z = periodic(rng, x, PERIOD, hill_t, R["hill"]) * (0.4 + 0.6 * d)
        z += R["rise"] * d * (0.6 + 0.4 * periodic(rng, x, PERIOD, rise_t, 1.0))
        for cx, cy, cr in craters:
            dx = ((x - cx + PERIOD / 2) % PERIOD) - PERIOD / 2
            dd = math.hypot(dx, y - cy)
            z += 0.22 * cr * math.exp(-((dd - cr) / (0.22 * cr)) ** 2) - 0.12 * cr * max(0.0, 1 - dd / cr)
        if R.get("terrace"):                                         # desert mesas: stepped
            t = R["terrace"]
            z = t * math.floor(z / t) + min(t, max(0.0, (z % t) - 0.6 * t) * 2.5)
        if sea and y >= sea["y"]:
            z = min(z, sea["level"])
        return z

    zr = [h(x, y) for y in ys for x in xs]
    zlo, zhi = min(zr), max(max(zr), min(zr) + 1e-3)

    def col(x, y, z):
        n = 0.5 + 0.5 * periodic(rng, x + 3 * y, PERIOD, col_t, 1.0) / 1.5
        c = [a + (b - a) * max(0.0, min(1.0, n)) for a, b in zip(g0, g1)]
        if R.get("cloud"):                                           # under-colour low, lit crown high
            k = (z - zlo) / (zhi - zlo)
            c = [a + (b - a) * k for a, b in zip(R["cloud"][0], R["cloud"][1])]
        if R.get("strata"):
            sc, per = R["strata"]
            k = 0.5 + 0.5 * math.sin(2 * math.pi * z / per)
            c = [a + (b - a) * 0.4 * k for a, b in zip(c, sc)]
        if R.get("snow"):
            sc, line = R["snow"]
            k = max(0.0, min(1.0, (z - line) / 4.0))
            c = [a + (b - a) * k for a, b in zip(c, sc)]
        if sea and z <= sea["level"] + 0.01:
            c = list(sea["deep"] if y > sea["y"] + 6 else sea["shallow"])
        return lin(c)

    b = Builder()
    b.quad_grid(xs, ys, h, col)
    ground_tris = b.tris()
    ground_faces = len(b.faces)
    ground_verts = len(b.verts)
    # Trees: cap by the budget. Conifer = two stacked 6-sided cones (12 tris); broadleaf = blob
    # (24 tris) on a 4-sided stem (4 tris).
    n = R["trees"]
    avg = 12 * R["conifer"] + 28 * (1 - R["conifer"]) if n else 1
    n = min(n, int((TRI_BUDGET - ground_tris) / (avg * 1.15))) if n else 0
    placed = []
    for i in range(n):
        x = rng.uniform(-PERIOD / 2, PERIOD / 2)
        y = rng.uniform(30.0, 58.0)                                  # B-102: no trees in the z 20 and 25 rows
        z = h(x, y)
        if sea and (y >= sea["y"] - 2 or z <= sea["level"] + 0.5):
            continue
        th = rng.uniform(*R["tree_h"])
        conifer = rng.random() < R["conifer"]
        y = max(y, 30.0 + th * (0.22 if conifer else 0.32))              # B-102: the whole crown stays at z >= 30
        for dx in ([0.0] + ([PERIOD] if x < -PERIOD / 2 + 6 else []) + ([-PERIOD] if x > PERIOD / 2 - 6 else [])):
            v0 = len(b.verts)
            if conifer:
                c = lin(rng.choice(R["needle"]))
                b.cone(x + dx, y, z - 0.3, th * 0.22, th * 0.62, 6, c)
                b.cone(x + dx, y, z + th * 0.38, th * 0.16, th * 0.62, 6, c)
            else:
                c = lin(rng.choice(R["leaf"]))
                b.cone(x + dx, y, z - 0.2, th * 0.06, th * 0.5, 4, lin((82, 68, 56)))
                b.blob(x + dx, y, z + th * 0.62, th * 0.32, c)
            b.islands.append((v0, len(b.verts)))
        placed.append((x, y))
    # B-088 boulders (Mars has no trees): 24-tri blobs from the region's rock palette, wrapped
    # at the seam like the trees, capped by the budget.
    nr = R.get("rocks", 0)
    if nr:
        nr = min(nr, int((TRI_BUDGET - b.tris()) / (24 * 1.15)))
        for i in range(nr):
            x = rng.uniform(-PERIOD / 2, PERIOD / 2)
            y = rng.uniform(21.0, 59.0)
            z = h(x, y)
            r = rng.uniform(*R.get("rock_r", (0.6, 2.4)))
            c = lin(rng.choice(R["rock_cols"]))
            for dx in ([0.0] + ([PERIOD] if x < -PERIOD / 2 + 4 else []) + ([-PERIOD] if x > PERIOD / 2 - 4 else [])):
                b.blob(x + dx, y, z + r * 0.35, r, c)
            placed.append((x, y))
    if R.get("haze"):                                                # B-102: atmospheric tint toward the sky haze,
        hz = lin(R["haze"])                                          # 20 % at z 20 -> 45 % at z 60
        for i, (v, c) in enumerate(zip(b.verts, b.cols)):
            k = 0.20 + 0.25 * max(0.0, min(1.0, (v[1] - 20.0) / 40.0))
            b.cols[i] = tuple(a + (hb - a) * k for a, hb in zip(c[:3], hz[:3])) + (c[3],)
    ob = b.mesh(f"ridge_{region}", coll, smooth_from=ground_faces if R["trees"] else None, ground_verts=ground_verts)
    nv = R.get("vents", 0)
    if nv:                                                           # B-092 Venus surface: lava vents, a second emissive mesh
        vb = Builder()
        for i in range(nv):
            x, y = rng.uniform(-PERIOD / 2, PERIOD / 2), rng.uniform(21.0, 59.0)
            r = rng.uniform(0.5, 1.3)
            c = lin(rng.choice([(255, 120, 40), (255, 90, 30), (255, 160, 70)]))
            for dx in ([0.0] + ([PERIOD] if x < -PERIOD / 2 + 3 else []) + ([-PERIOD] if x > PERIOD / 2 - 3 else [])):
                vb.blob(x + dx, y, h(x, y) + r * 0.15, r, c)
            placed.append((x, y))
        vb.mesh(f"vents_{region}", coll, emit=2.0)
    return ob, b.tris() + (nv * 24), len(placed)


def skyline(coll, name="skyline_far", period=2 * PERIOD, nx=128, rock0=(112, 120, 132), rock1=(138, 146, 156),
            snow=(232, 238, 246), seed=77, hero=None, snow_frac=0.74, amp0=46.0, massif0=55.0):
    """v3 (LEAD cycle 183): a mountain range, not fins. Each depth row has its own profile (own
    seed; frequency and amplitude fall toward the back), lightly smoothed across rows so the
    range stays coherent; peaks ride on a broad massif instead of rising from the floor; an
    upper-envelope pass caps every slope near 45 deg (no vertical sheets); snow is a soft
    vertex-colour band at the v1 snow line (~0.74 of the peak height)."""
    P = period                                                        # Earth: 512 m, 4 m steps
    xs = [-PERIOD + P / nx * i for i in range(nx + 1)]
    ys = [150.0 + 25.0 * j for j in range(11)]                        # 150..400 m
    base_rng = random.Random(seed)
    row_seed = 1000 if seed == 77 else seed * 100                     # Earth keeps its accepted seeds
    massif_t = make_terms(base_rng, 3, 2)                             # broad base, 1-2 waves per 512 m
    Z = []
    for j, y in enumerate(ys):
        d = j / (len(ys) - 1)                                         # 0 front .. 1 back
        rr = random.Random(row_seed + j)
        kmax = max(3, int(round(14 - 9 * d)))                         # lower frequency toward the back
        peaks_t = make_terms(rr, 6, kmax)
        amp = amp0 - 18 * d                                           # lower amplitude toward the back
        rise = math.sin(math.pi / 2 * min(1.0, d * 2.2))              # the massif rises over the first rows
        row = []
        for x in xs:
            massif = massif0 + periodic(None, x, P, massif_t, 18)
            pk = max(0.0, periodic(None, x, P, peaks_t, amp) + 0.35 * amp)
            z = rise * (massif + pk * (0.55 + 0.45 * massif / 73.0))
            if hero:                                                  # B-088 Olympus Mons: broad shield, caldera top
                hx, hr, hh = hero
                dx = ((x - hx + P / 2) % P) - P / 2
                if abs(dx) < hr:
                    sh = hh * (1 - (dx / hr) ** 2) ** 0.7 * min(1.0, 0.25 + 1.5 * d)   # v2: full height in the back rows (a sine faded it there)
                    sh = min(sh, 0.93 * hh) - 0.04 * hh * max(0.0, 1 - abs(dx) / (0.12 * hr))
                    z = max(z, sh)
            row.append(z)
        Z.append(row)
    for _ in range(2):                                                # light smoothing across depth rows
        Z = [Z[0]] + [[0.25 * a + 0.5 * b + 0.25 * c for a, b, c in zip(Z[j - 1], Z[j], Z[j + 1])]
                      for j in range(1, len(Z) - 1)] + [Z[-1]]
    sx, sy = P / nx, 25.0
    for _ in range(4):                                                # slope cap (upper envelope, ~45 deg)
        for row in Z:
            for i in range(nx + 1):
                l, r = row[(i - 1) % nx], row[(i + 1) % nx]            # wraps: keeps the 512 m period
                row[i] = min(row[i], l + sx * 1.0, r + sx * 1.0)
            row[nx] = row[0]
        for j in range(len(Z)):
            for i in range(nx + 1):
                nb = [Z[k][i] for k in (j - 1, j + 1) if 0 <= k < len(Z)]
                Z[j][i] = min([Z[j][i]] + [v + sy * 1.0 for v in nb])
    peak = max(max(r) for r in Z)
    line = snow_frac * peak
    zmap = {(round(x, 3), y): Z[j][i] for j, y in enumerate(ys) for i, x in enumerate(xs)}

    def h(x, y):
        return zmap[(round(x, 3), y)]

    def col(x, y, z):
        k = max(0.0, min(1.0, (z - line) / 8.0)) if snow else 0.0
        n = 0.5 + 0.5 * math.sin(2 * math.pi * x / P * 7 + y * 0.03)
        c = [a + (b2 - a) * n for a, b2 in zip(rock0, rock1)]
        return lin([a + (b2 - a) * k for a, b2 in zip(c, snow)] if snow else c)

    b = Builder()
    b.quad_grid(xs, ys, h, col)
    return b.mesh(name, coll), b.tris()


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    report = []
    for region, R in REGIONS.items():
        coll = bpy.data.collections.new(f"ridge_{region}")
        scene.collection.children.link(coll)
        ob, tris, trees = ridge(region, R, coll)
        report.append(f"{region}: {tris} tris, {trees} trees")
    coll = bpy.data.collections.new("skyline_far")
    scene.collection.children.link(coll)
    _, st = skyline(coll)
    report.append(f"skyline_far: {st} tris")
    print("MERIDIAN bands", "; ".join(report))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


# ---------------------------------------------------------------- B-088 Mars
MARS_OUT = os.path.join(os.path.dirname(HERE), "sources", "backgrounds", "mars_bands.blend")
MARS_ROCKS = [(96, 70, 58), (120, 86, 66), (80, 60, 52), (140, 96, 72)]
MARS_REGIONS = {   # colours from the v1 gen_backdrop3d mars / mars_canyon presets
    "canyon": dict(ground=[(126, 76, 54), (160, 100, 70)], hill=5, rise=34, terrace=6.0, strata=((86, 46, 36), 6.0),
                   trees=0, conifer=0.0, tree_h=(0, 0), rocks=150, rock_r=(0.8, 3.0), rock_cols=MARS_ROCKS, seed=21),
    "plains": dict(ground=[(150, 86, 56), (178, 110, 74)], hill=2.5, rise=8, trees=0, conifer=0.0, tree_h=(0, 0),
                   rocks=110, rock_r=(0.4, 2.0), rock_cols=MARS_ROCKS, seed=22),
    "polar":  dict(ground=[(214, 196, 188), (236, 224, 218)], hill=3, rise=14, terrace=2.5, strata=((178, 134, 112), 3.0),
                   trees=0, conifer=0.0, tree_h=(0, 0), rocks=14, rock_r=(0.4, 1.4), rock_cols=MARS_ROCKS, seed=23),
    "tharsis": dict(ground=[(84, 62, 54), (118, 84, 66)], hill=4, rise=20, trees=0, conifer=0.0, tree_h=(0, 0),
                    rocks=130, rock_r=(0.6, 2.6), rock_cols=[(62, 50, 46), (80, 62, 54), (104, 76, 62)], seed=24),
}


def build_mars(out_path=MARS_OUT):
    """Mars ridges per region, the shared Mars skyline (rust, no snow), and the Tharsis skyline
    with Olympus Mons as the far hero (1024 m period so the shield isn't stamped every 512 m)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    report = []
    for region, R in MARS_REGIONS.items():
        coll = bpy.data.collections.new(f"ridge_{region}")
        scene.collection.children.link(coll)
        ob, tris, n = ridge(region, R, coll)
        report.append(f"{region}: {tris} tris, {n} rocks")
    coll = bpy.data.collections.new("skyline_far")
    scene.collection.children.link(coll)
    _, st = skyline(coll, rock0=(150, 96, 70), rock1=(182, 126, 92), snow=None, seed=91, amp0=40.0, massif0=48.0)
    report.append(f"skyline_far: {st} tris")
    coll = bpy.data.collections.new("skyline_far_tharsis")
    scene.collection.children.link(coll)
    _, st2 = skyline(coll, name="skyline_far_tharsis", period=4 * PERIOD, nx=128, rock0=(138, 88, 66), rock1=(170, 116, 86),
                     snow=None, seed=92, hero=(0.0, 340.0, 260.0), amp0=30.0, massif0=40.0)
    report.append(f"skyline_far_tharsis: {st2} tris")
    print("MERIDIAN bands", "; ".join(report))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


# ---------------------------------------------------------------- B-092 Mercury + Venus
MERCURY_OUT = os.path.join(os.path.dirname(HERE), "sources", "backgrounds", "mercury_bands.blend")
VENUS_OUT = os.path.join(os.path.dirname(HERE), "sources", "backgrounds", "venus_bands.blend")
MERC_ROCKS = [(96, 94, 100), (70, 68, 74), (120, 118, 122)]
MERCURY_REGIONS = {   # v1 mercury preset: grey regolith, crater rims; night = the same ground in starlight (darker, bluer)
    "day":      dict(ground=[(128, 126, 130), (104, 102, 108)], hill=3, rise=10, craters=9, crater_r=(5.0, 16.0),
                     trees=0, conifer=0.0, tree_h=(0, 0), rocks=90, rock_r=(0.5, 2.2), rock_cols=MERC_ROCKS, seed=31),
    "twilight": dict(ground=[(104, 102, 112), (84, 82, 94)], hill=3, rise=12, craters=8, crater_r=(5.0, 16.0),
                     trees=0, conifer=0.0, tree_h=(0, 0), rocks=80, rock_r=(0.5, 2.2), rock_cols=MERC_ROCKS, seed=32),
    "night":    dict(ground=[(46, 46, 60), (34, 34, 46)], hill=3, rise=10, craters=9, crater_r=(5.0, 16.0),
                     trees=0, conifer=0.0, tree_h=(0, 0), rocks=70, rock_r=(0.5, 2.2),
                     rock_cols=[(40, 40, 52), (30, 30, 40), (52, 52, 64)], seed=33),
}
VENUS_REGIONS = {
    # deck: cloud-top masses, no ground. A translucent strip (manifest alpha) of long smooth heaps
    # coloured under -> crown by height, from the v1 venus_deck bank colours.
    "deck":    dict(ground=[(234, 212, 168), (216, 188, 142)], cloud=((206, 160, 112), (255, 244, 222)), hill=9, rise=14,
                    trees=0, conifer=0.0, tree_h=(0, 0), rocks=0, seed=41),
    # surface: black glassy basalt plains, dark boulders, lava vents (emissive second mesh).
    "surface": dict(ground=[(34, 30, 30), (52, 44, 40)], hill=3, rise=18, trees=0, conifer=0.0, tree_h=(0, 0),
                    rocks=110, rock_r=(0.6, 2.6), rock_cols=[(40, 34, 34), (58, 50, 46), (30, 28, 30)], vents=28, seed=42),
}


def _build_planet(out_path, regions, sky_kw):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    report = []
    for region, R in regions.items():
        coll = bpy.data.collections.new(f"ridge_{region}")
        scene.collection.children.link(coll)
        _, tris, n = ridge(region, R, coll)
        report.append(f"{region}: {tris} tris, {n} placed")
    coll = bpy.data.collections.new("skyline_far")
    scene.collection.children.link(coll)
    _, st = skyline(coll, snow=None, **sky_kw)
    report.append(f"skyline_far: {st} tris")
    print("MERIDIAN bands", "; ".join(report))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


def build_mercury(out_path=MERCURY_OUT):
    _build_planet(out_path, MERCURY_REGIONS, dict(rock0=(118, 116, 120), rock1=(150, 148, 152), seed=93, amp0=34.0, massif0=40.0))


def build_venus(out_path=VENUS_OUT):
    _build_planet(out_path, VENUS_REGIONS, dict(rock0=(40, 34, 32), rock1=(58, 48, 42), seed=94, amp0=36.0, massif0=44.0))


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
