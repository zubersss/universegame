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
    "forest": dict(ground=[(64, 92, 48), (82, 104, 56)], hill=6, rise=26, trees=220, conifer=0.6, tree_h=(14, 24),
                   needle=[(30, 58, 38), (40, 70, 44)], leaf=[(46, 78, 34), (62, 96, 40), (84, 112, 46)], seed=1),
    "plains": dict(ground=[(110, 134, 64), (132, 150, 76)], hill=3, rise=10, trees=22, conifer=0.2, tree_h=(9, 15),
                   needle=[(36, 64, 40)], leaf=[(62, 96, 40), (84, 112, 46)], seed=2),
    "desert": dict(ground=[(214, 182, 128), (196, 160, 108)], hill=4, rise=24, trees=0, conifer=0.0, tree_h=(0, 0),
                   strata=((232, 200, 150), 4.5), terrace=5.0, seed=3),
    "coast":  dict(ground=[(186, 174, 132), (140, 146, 92)], hill=2, rise=6, trees=45, conifer=0.9, tree_h=(8, 13),
                   needle=[(32, 60, 40), (44, 72, 46)], leaf=[(56, 92, 40)],
                   sea=dict(y=42.0, level=-1.5, shallow=(70, 176, 178), deep=(26, 70, 122)), seed=4),
    "taiga":  dict(ground=[(58, 80, 58), (72, 92, 64)], hill=7, rise=30, trees=260, conifer=0.95, tree_h=(16, 28),
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


def vc_material(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "col"
    nt.links.new(attr.outputs["Color"], pr.inputs["Base Color"])
    pr.inputs["Roughness"].default_value = 0.92
    return m


class Builder:
    def __init__(self):
        self.verts, self.faces, self.cols = [], [], []

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

    def tris(self):
        return sum(len(f) - 2 for f in self.faces)

    def mesh(self, name, coll):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        me.update()
        ca = me.color_attributes.new("col", "FLOAT_COLOR", "POINT")
        for i, c in enumerate(self.cols):
            ca.data[i].color = c
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        me.materials.append(vc_material(name + "_mat"))
        for p in me.polygons:
            p.use_smooth = False
        return ob


def ridge(region, R, coll):
    rng = random.Random(R["seed"])
    hill_t, rise_t, col_t = make_terms(rng, 5, 8), make_terms(rng, 4, 4), make_terms(rng, 4, 10)
    g0, g1 = R["ground"]
    xs = [-PERIOD / 2 + 2.0 * i for i in range(129)]                 # 2 m spacing, both ends on the period
    ys = [20.0 + 5.0 * j for j in range(9)]                          # 20..60 m depth
    sea = R.get("sea")

    def h(x, y):
        d = (y - 20.0) / 40.0                                        # 0 front .. 1 back
        z = periodic(rng, x, PERIOD, hill_t, R["hill"]) * (0.4 + 0.6 * d)
        z += R["rise"] * d * (0.6 + 0.4 * periodic(rng, x, PERIOD, rise_t, 1.0))
        if R.get("terrace"):                                         # desert mesas: stepped
            t = R["terrace"]
            z = t * math.floor(z / t) + min(t, max(0.0, (z % t) - 0.6 * t) * 2.5)
        if sea and y >= sea["y"]:
            z = min(z, sea["level"])
        return z

    def col(x, y, z):
        n = 0.5 + 0.5 * periodic(rng, x + 3 * y, PERIOD, col_t, 1.0) / 1.5
        c = [a + (b - a) * max(0.0, min(1.0, n)) for a, b in zip(g0, g1)]
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
    # Trees: cap by the budget. Conifer = two stacked 6-sided cones (12 tris); broadleaf = blob
    # (24 tris) on a 4-sided stem (4 tris).
    n = R["trees"]
    avg = 12 * R["conifer"] + 28 * (1 - R["conifer"]) if n else 1
    n = min(n, int((TRI_BUDGET - ground_tris) / (avg * 1.15))) if n else 0
    placed = []
    for i in range(n):
        x = rng.uniform(-PERIOD / 2, PERIOD / 2)
        y = rng.uniform(22.0, 58.0)
        z = h(x, y)
        if sea and (y >= sea["y"] - 2 or z <= sea["level"] + 0.5):
            continue
        th = rng.uniform(*R["tree_h"])
        conifer = rng.random() < R["conifer"]
        for dx in ([0.0] + ([PERIOD] if x < -PERIOD / 2 + 6 else []) + ([-PERIOD] if x > PERIOD / 2 - 6 else [])):
            if conifer:
                c = lin(rng.choice(R["needle"]))
                b.cone(x + dx, y, z - 0.3, th * 0.22, th * 0.62, 6, c)
                b.cone(x + dx, y, z + th * 0.38, th * 0.16, th * 0.62, 6, c)
            else:
                c = lin(rng.choice(R["leaf"]))
                b.cone(x + dx, y, z - 0.2, th * 0.06, th * 0.5, 4, lin((82, 68, 56)))
                b.blob(x + dx, y, z + th * 0.62, th * 0.32, c)
        placed.append((x, y))
    ob = b.mesh(f"ridge_{region}", coll)
    return ob, b.tris(), len(placed)


def skyline(coll):
    """v3 (LEAD cycle 183): a mountain range, not fins. Each depth row has its own profile (own
    seed; frequency and amplitude fall toward the back), lightly smoothed across rows so the
    range stays coherent; peaks ride on a broad massif instead of rising from the floor; an
    upper-envelope pass caps every slope near 45 deg (no vertical sheets); snow is a soft
    vertex-colour band at the v1 snow line (~0.74 of the peak height)."""
    P = 2 * PERIOD
    nx = 128                                                          # 4 m steps over 512 m
    xs = [-PERIOD + P / nx * i for i in range(nx + 1)]
    ys = [150.0 + 25.0 * j for j in range(11)]                        # 150..400 m
    rock0, rock1, snow = (112, 120, 132), (138, 146, 156), (232, 238, 246)
    base_rng = random.Random(77)
    massif_t = make_terms(base_rng, 3, 2)                             # broad base, 1-2 waves per 512 m
    Z = []
    for j, y in enumerate(ys):
        d = j / (len(ys) - 1)                                         # 0 front .. 1 back
        rr = random.Random(1000 + j)
        kmax = max(3, int(round(14 - 9 * d)))                         # lower frequency toward the back
        peaks_t = make_terms(rr, 6, kmax)
        amp = 46 - 18 * d                                             # lower amplitude toward the back
        rise = math.sin(math.pi / 2 * min(1.0, d * 2.2))              # the massif rises over the first rows
        row = []
        for x in xs:
            massif = 55 + periodic(None, x, P, massif_t, 18)
            pk = max(0.0, periodic(None, x, P, peaks_t, amp) + 0.35 * amp)
            row.append(rise * (massif + pk * (0.55 + 0.45 * massif / 73.0)))
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
    line = 0.74 * peak
    zmap = {(round(x, 3), y): Z[j][i] for j, y in enumerate(ys) for i, x in enumerate(xs)}

    def h(x, y):
        return zmap[(round(x, 3), y)]

    def col(x, y, z):
        k = max(0.0, min(1.0, (z - line) / 8.0))
        n = 0.5 + 0.5 * math.sin(2 * math.pi * x / P * 7 + y * 0.03)
        c = [a + (b2 - a) * n for a, b2 in zip(rock0, rock1)]
        return lin([a + (b2 - a) * k for a, b2 in zip(c, snow)])

    b = Builder()
    b.quad_grid(xs, ys, h, col)
    return b.mesh("skyline_far", coll), b.tris()


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


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
