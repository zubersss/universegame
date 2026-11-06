"""Builds blender/sources/props/earth_flora.blend: Earth scenery for the near band and the play
plane (B-085): 3 trees (oak = forest, spruce = taiga, birch = both), 2 bushes, 3 rocks, grass
tufts, a cactus, a dead tree. One collection `flora_<name>` each, base at z = 0.

Every part is UV-projected into its material's tile of the shared atlas (gen_flora_atlas
TILES, 4x4 x 512 px): cylindrical for trunks/cactus, spherical for crowns/rocks (mirrored
angle, no wrap seam), planar for grass blades; UVs normalised to the part's bounds and inset
inside the tile. One shared material reads the atlas. Wind sway: a colour attribute `sway`
(R = sway weight: 0 at the base rising with height, crowns and blade tips high, rocks 0),
exported as COLOR_0. Low poly by construction (<= 2 k tris each); model.py adds LOD1.

  blender --background --factory-startup --python blender/scripts/build_flora.py
"""
import math
import zlib
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_flora_atlas as FA  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "earth_flora.blend")
ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art", "props", "earth_flora")


def atlas_material(art=ART, name="earth_flora_atlas"):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]
    pr.inputs["Roughness"].default_value = 0.8
    cpath = os.path.join(art, "atlas_color.png")
    if os.path.isfile(cpath):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(cpath, check_existing=True)
        nt.links.new(t.outputs["Color"], pr.inputs["Base Color"])
        npath = os.path.join(art, "atlas_normal.png")
        if os.path.isfile(npath):
            n = nt.nodes.new("ShaderNodeTexImage")
            n.image = bpy.data.images.load(npath, check_existing=True)
            n.image.colorspace_settings.name = "Non-Color"
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nt.links.new(n.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], pr.inputs["Normal"])
    return m


def _own(coll, ob):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob


def _apply(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    for md in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def finish(ob, tile, proj, sway_fn):
    """UVs into `tile` by projection; sway colour from sway_fn(local z fraction, world z)."""
    _apply(ob)
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    vs = [v.co for v in me.vertices]
    xs, ys, zs = [v.x for v in vs], [v.y for v in vs], [v.z for v in vs]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    z0, z1 = min(zs), max(zs)
    dz = max(z1 - z0, 1e-6)
    dx, dy = max(max(xs) - min(xs), 1e-6), max(max(ys) - min(ys), 1e-6)
    u0, v0, u1, v1 = FA.tile_rect(tile)
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = vs[me.loops[li].vertex_index]
            if proj == "blade":
                u, v = (co.x - min(xs)) / dx, (co.z - z0) / dz
            else:                                                    # cyl / sph: mirrored angle
                u = abs(math.atan2(co.y - cy, co.x - cx)) / math.pi
                v = (co.z - z0) / dz
            uv[li].uv = (u0 + u * (u1 - u0), v0 + v * (v1 - v0))
    ca = me.color_attributes.new("sway", "FLOAT_COLOR", "POINT")
    for i, co in enumerate(vs):
        s = max(0.0, min(1.0, sway_fn((co.z - z0) / dz, co.z)))
        ca.data[i].color = (s, 0.0, 0.0, 1.0)
    me.color_attributes.active_color = ca
    return ob


def cyl(coll, r1, r2, h, loc, sides=8, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=sides, radius1=r1, radius2=r2, depth=h, location=loc, rotation=rot)
    ob = _own(coll, bpy.context.active_object)
    bpy.ops.object.shade_smooth()
    return ob


def blob(coll, r, loc, scale=(1, 1, 1), subdiv=2, seed=0, rough=0.25):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=r, location=loc)
    ob = _own(coll, bpy.context.active_object)
    ob.scale = scale
    if rough > 0:                                    # a zero-strength displace counts as disabled (apply fails)
        tex = bpy.data.textures.new(f"blob{seed}", "CLOUDS")
        tex.noise_scale = r * 0.7
        d = ob.modifiers.new("disp", "DISPLACE")
        d.texture, d.strength, d.texture_coords = tex, r * rough, "GLOBAL"
    bpy.ops.object.shade_smooth()
    return ob


def branch(coll, base, length, r, yaw, pitch, sides=6):
    """A tapered branch from `base`, pointing (yaw, pitch) radians."""
    dx = math.cos(pitch) * math.cos(yaw)
    dy = math.cos(pitch) * math.sin(yaw)
    dz = math.sin(pitch)
    mid = (base[0] + dx * length / 2, base[1] + dy * length / 2, base[2] + dz * length / 2)
    rot = (0.0, math.acos(max(-1.0, min(1.0, dz))), math.atan2(dy, dx))
    return cyl(coll, r, r * 0.35, length, mid, sides, rot), (base[0] + dx * length, base[1] + dy * length, base[2] + dz * length)


def trunk_sway(f, z):
    return 0.35 * f * f


def crown_sway(f, z):
    return 0.6 + 0.4 * f


def join(coll, name, mat):
    obs = [o for o in coll.objects if o.type == "MESH"]
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    if len(obs) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = ob.data.name = name
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    ob.data.color_attributes.active_color = ob.data.color_attributes["sway"]
    return ob


# ---------------------------------------------------------------- species

def tree_oak(coll, rnd):
    t = finish(cyl(coll, 0.38, 0.2, 4.6, (0, 0, 2.3), 10), "bark_oak", "cyl", trunk_sway)
    for k, yaw in enumerate((0.4, 2.5, 4.4)):
        b, tip = branch(coll, (0, 0, 3.4 + 0.3 * k), 1.8, 0.12, yaw, 0.6)
        finish(b, "bark_oak", "cyl", lambda f, z: 0.4 + 0.2 * f)
    for k, (x, y, z, r) in enumerate(((0, 0, 6.2, 2.1), (1.3, 0.4, 5.4, 1.5), (-1.3, -0.3, 5.5, 1.5), (0.3, -1.2, 5.7, 1.4), (-0.4, 1.2, 5.9, 1.4))):
        finish(blob(coll, r, (x, y, z), (1, 1, 0.82), 3, seed=k), "leaf_oak", "sph", crown_sway)
    return t


def tree_spruce(coll, rnd):
    finish(cyl(coll, 0.26, 0.08, 9.0, (0, 0, 4.5), 8), "bark_spruce", "cyl", trunk_sway)
    layers = 10
    for k in range(layers):
        f = k / (layers - 1)
        r = 2.2 * (1 - f) + 0.35
        z = 1.6 + f * 7.6
        finish(cyl(coll, r, 0.0, 1.7 - 0.7 * f, (0, 0, z), 18, (0, 0, rnd.uniform(0, 1))), "needles", "sph",
               lambda ff, zz, f=f: 0.45 + 0.55 * f)
    return None


def tree_birch(coll, rnd):
    finish(cyl(coll, 0.17, 0.08, 7.2, (0, 0, 3.6), 8), "bark_birch", "cyl", trunk_sway)
    for k, (x, y, z, r) in enumerate(((0, 0, 7.0, 1.3), (0.7, 0.2, 6.0, 1.0), (-0.6, -0.2, 6.2, 1.0), (0.1, 0.6, 5.4, 0.9))):
        finish(blob(coll, r, (x, y, z), (0.8, 0.8, 1.25), 3, seed=10 + k), "leaf_birch", "sph", crown_sway)


def bush_a(coll, rnd):
    for k, (x, y, z, r) in enumerate(((0, 0, 0.55, 0.65), (0.5, 0.15, 0.45, 0.5), (-0.45, -0.1, 0.42, 0.5), (0.05, 0.4, 0.4, 0.45))):
        finish(blob(coll, r, (x, y, z), (1, 1, 0.85), 3, seed=20 + k), "leaf_bush", "sph", lambda f, z: 0.2 + 0.6 * f)


def bush_b(coll, rnd):
    for k, (x, y, z, r) in enumerate(((0, 0, 0.5, 0.55), (0.4, -0.1, 0.4, 0.42), (-0.38, 0.12, 0.38, 0.42))):
        finish(blob(coll, r, (x, y, z), (1, 1, 0.9), 3, seed=30 + k), "leaf_bush", "sph", lambda f, z: 0.2 + 0.6 * f)
    for k in range(14):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0.35, 0.55)
        finish(blob(coll, 0.05, (rr * math.cos(a), rr * math.sin(a), rnd.uniform(0.35, 0.85)), subdiv=1, seed=40 + k, rough=0.0),
               "berries", "sph", lambda f, z: 0.5)


def rock(coll, rnd, tile, size, seed):
    finish(blob(coll, 1.0, (0, 0, size[2] * 0.55), size, 4, seed=seed, rough=0.45), tile, "sph", lambda f, z: 0.0)


def grass(coll, rnd):
    blades = 30
    verts, faces = [], []
    for b in range(blades):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0, 0.25)
        bx, by = rr * math.cos(a), rr * math.sin(a)
        h = rnd.uniform(0.35, 0.7)
        w = rnd.uniform(0.02, 0.035)
        lean = rnd.uniform(-0.5, 0.5)
        yaw = rnd.uniform(0, math.pi)
        base = len(verts)
        for s in range(4):
            f = s / 3
            ox = math.sin(lean) * h * f * f
            cx, cy = bx + ox * math.cos(yaw), by + ox * math.sin(yaw)
            ww = w * (1 - 0.8 * f)
            verts.append((cx - ww * math.sin(yaw), cy + ww * math.cos(yaw), h * f))
            verts.append((cx + ww * math.sin(yaw), cy - ww * math.cos(yaw), h * f))
        for s in range(3):
            i = base + 2 * s
            faces.append((i, i + 1, i + 3, i + 2))
    me = bpy.data.meshes.new("grass")
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new("grass", me)
    coll.objects.link(ob)
    finish(ob, "grass", "blade", lambda f, z: f ** 1.5)


def cactus(coll, rnd):
    finish(cyl(coll, 0.3, 0.26, 3.4, (0, 0, 1.7), 12), "cactus", "cyl", lambda f, z: 0.05 * f)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.26, location=(0, 0, 3.4))
    finish(_own(coll, bpy.context.active_object), "cactus", "sph", lambda f, z: 0.05)
    for s, (zb, h) in ((1, (1.3, 1.1)), (-1, (1.8, 0.9))):
        finish(cyl(coll, 0.18, 0.18, 0.6, (s * 0.5, 0, zb), 10, (0, math.pi / 2, 0)), "cactus", "cyl", lambda f, z: 0.05)
        finish(cyl(coll, 0.18, 0.15, h, (s * 0.8, 0, zb + h / 2), 10), "cactus", "cyl", lambda f, z: 0.05)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=5, radius=0.15, location=(s * 0.8, 0, zb + h))
        finish(_own(coll, bpy.context.active_object), "cactus", "sph", lambda f, z: 0.05)


def dead_tree(coll, rnd):
    finish(cyl(coll, 0.3, 0.12, 5.0, (0, 0, 2.5), 8), "bark_dead", "cyl", trunk_sway)
    for k in range(6):
        b, tip = branch(coll, (0, 0, 2.6 + 0.35 * k), rnd.uniform(1.0, 1.9), 0.1, rnd.uniform(0, 2 * math.pi), rnd.uniform(0.3, 0.9))
        finish(b, "bark_dead", "cyl", lambda f, z: 0.3 + 0.3 * f)
        b2, _ = branch(coll, tip, rnd.uniform(0.5, 0.9), 0.045, rnd.uniform(0, 2 * math.pi), rnd.uniform(0.2, 1.0), sides=5)
        finish(b2, "bark_dead", "cyl", lambda f, z: 0.5)


FLORA = {
    "tree_oak": tree_oak, "tree_spruce": tree_spruce, "tree_birch": tree_birch,
    "bush_a": bush_a, "bush_b": bush_b,
    "rock_a": lambda c, r: rock(c, r, "rock_grey", (0.9, 0.75, 0.6), 50),
    "rock_b": lambda c, r: rock(c, r, "rock_brown", (1.6, 1.1, 0.9), 51),
    "rock_c": lambda c, r: rock(c, r, "rock_moss", (0.5, 0.45, 0.35), 52),
    "grass": grass, "cactus": cactus, "dead_tree": dead_tree,
}


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    mat = atlas_material()
    report = []
    for name, fn in FLORA.items():
        coll = bpy.data.collections.new(f"flora_{name}")
        scene.collection.children.link(coll)
        fn(coll, random.Random(zlib.crc32(name.encode())))   # deterministic (hash() is salted per process)
        ob = join(coll, name, mat)
        ob.data.calc_loop_triangles()
        report.append(f"{name} {len(ob.data.loop_triangles)}")
    print("MERIDIAN flora tris:", ", ".join(report))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


# ---------------------------------------------------------------- B-089 Mars set
MARS_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "mars_flora.blend")
MARS_ART = os.path.join(os.path.dirname(ART), "mars_flora")


def ice_chunk(coll, tile, size, seed):
    """v2: faceted ice (flat-shaded cleavage planes, as the B-059 ring ice v2)."""
    ob = finish(blob(coll, 1.0, (0, 0, size[2] * 0.5), size, 2, seed=seed, rough=0.45), tile, "sph", lambda f, z: 0.0)
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def dust_bush(coll, rnd):
    """Dead, wiry dust bush (fictional Mars xerophyte husk), v2: denser and thicker so it reads
    at 60 px/m: 14 main stems with forked tips over a low woody crown."""
    finish(blob(coll, 0.18, (0, 0, 0.08), (1.4, 1.4, 0.6), 1, seed=70, rough=0.3), "dust_bush", "sph", lambda f, z: 0.1)
    for k in range(14):
        b, tip = branch(coll, (rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), 0.08), rnd.uniform(0.45, 0.9), 0.05,
                        rnd.uniform(0, 2 * math.pi), rnd.uniform(0.3, 1.15), sides=5)
        finish(b, "dust_bush", "cyl", lambda f, z: 0.2 + 0.4 * f)
        for j in range(2):
            b2, _ = branch(coll, tip, rnd.uniform(0.2, 0.4), 0.025, rnd.uniform(0, 2 * math.pi), rnd.uniform(0.0, 0.9), sides=4)
            finish(b2, "dust_bush", "cyl", lambda f, z: 0.6)


def _drip_column(coll, rnd, z_sign, height, r0):
    """Lava-tube dripstone: 4 stacked, slightly offset, tapering lumpy tiers plus ring bulges,
    growing from the origin along z_sign (+1 floor, -1 ceiling)."""
    zc, r = 0.0, r0
    for k in range(4):
        h = height * (0.34 - 0.06 * k)
        dx, dy = rnd.uniform(-0.04, 0.04), rnd.uniform(-0.04, 0.04)
        ob = cyl(coll, r, r * 0.62, h, (dx, dy, z_sign * (zc + h / 2)), 12)
        if z_sign < 0:
            ob.rotation_euler = (math.pi, 0, 0)
        finish(ob, "lavatube", "cyl", lambda f, z: 0.0)
        finish(blob(coll, r * 0.95, (dx, dy, z_sign * (zc + h * 0.1)), (1, 1, 0.45), 1, seed=80 + k, rough=0.2),
               "lavatube", "sph", lambda f, z: 0.0)
        zc += h
        r *= 0.62
    tip = cyl(coll, r, 0.0, height * 0.12, (0, 0, z_sign * (zc + height * 0.06)), 8)
    if z_sign < 0:
        tip.rotation_euler = (math.pi, 0, 0)
    finish(tip, "lavatube", "cyl", lambda f, z: 0.0)


def stalactite(coll, rnd):
    """Hangs from its origin (the ceiling) down to about -1.6 m."""
    _drip_column(coll, rnd, -1, 1.6, 0.34)


def stalagmite(coll, rnd):
    _drip_column(coll, rnd, +1, 1.4, 0.42)


MARS_FLORA = {
    "boulder_a": lambda c, r: rock(c, r, "rock_rust", (1.2, 1.0, 0.85), 60),
    "boulder_b": lambda c, r: rock(c, r, "rock_basalt", (1.8, 1.3, 1.1), 61),
    "boulder_c": lambda c, r: rock(c, r, "rock_rust", (0.9, 0.85, 1.2), 62),
    "rock_a": lambda c, r: rock(c, r, "regolith", (0.5, 0.4, 0.25), 63),
    "rock_b": lambda c, r: rock(c, r, "hematite", (0.35, 0.3, 0.22), 64),
    "ice_a": lambda c, r: ice_chunk(c, "ice", (0.9, 0.7, 0.6), 65),
    "ice_b": lambda c, r: ice_chunk(c, "ice_dirty", (1.4, 1.0, 0.7), 66),
    "dust_bush": dust_bush, "stalactite": stalactite, "stalagmite": stalagmite,
}


def build_mars(out_path=MARS_OUT):
    FA.CURRENT = "mars"
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        mat = atlas_material(MARS_ART, "mars_flora_atlas")
        report = []
        for name, fn in MARS_FLORA.items():
            coll = bpy.data.collections.new(f"flora_{name}")
            scene.collection.children.link(coll)
            fn(coll, random.Random(zlib.crc32(name.encode())))
            ob = join(coll, name, mat)
            ob.data.calc_loop_triangles()
            report.append(f"{name} {len(ob.data.loop_triangles)}")
        print("MERIDIAN flora tris:", ", ".join(report))
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
        print("MERIDIAN built", out_path)
    finally:
        FA.CURRENT = "earth"


# ---------------------------------------------------------------- B-101 Mercury / Venus scenery
# Near-band and play-plane scenery as atlas models (the R3 counterpart of B-089): nothing grows on
# either planet, so every piece is rock, glass, ice, crust or a vent. Each <= 2 k tris with a LOD1
# <= 800 (manifest lod1_max), one shared 2048^2 atlas per planet (gen_flora_atlas TILE_SETS
# "mercury" / "venus"), emission through the atlas on the solarite and the vent mouth. Flat shading
# where the real thing cleaves (impact glass, ice), smooth elsewhere. sway = 0 (nothing moves).
MERCURY_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "mercury_scenery.blend")
MERCURY_ART = os.path.join(os.path.dirname(ART), "mercury_scenery")
VENUS_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "venus_scenery.blend")
VENUS_ART = os.path.join(os.path.dirname(ART), "venus_scenery")
_STILL = (lambda f, z: 0.0)


def _flat(ob):
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def shard(coll, rnd, tile, size, seed, lean=0.5):
    """Impact glass: an elongated, cleaved chunk standing on a corner (flat-shaded facets)."""
    ob = blob(coll, 1.0, (0, 0, 0), size, 2, seed=seed, rough=0.55)
    ob.rotation_euler = (rnd.uniform(-lean, lean), rnd.uniform(-lean, lean), rnd.uniform(0, 6.28))
    ob.location = (0, 0, size[2] * 0.62)
    return _flat(finish(ob, tile, "sph", _STILL))


def solarite_outcrop(coll, rnd):
    """A scorched host rock with 7 solarite spires (the B-095 cluster silhouette at scenery scale)."""
    finish(blob(coll, 1.0, (0, 0, 0.26), (1.5, 1.05, 0.5), 3, seed=90, rough=0.4), "solarite_rock", "sph", _STILL)
    for k in range(7):
        h = rnd.uniform(0.5, 1.25) if k else 1.3
        lean = rnd.uniform(-0.4, 0.4) if k else 0.05
        x, y = (rnd.uniform(-0.45, 0.45), rnd.uniform(-0.2, 0.2)) if k else (0.0, 0.0)
        ob = cyl(coll, 0.08 + 0.06 * h, 0.0, h, (x + math.sin(lean) * h / 2, y, 0.3 + math.cos(lean) * h / 2), 6,
                 rot=(rnd.uniform(-0.15, 0.15), lean, rnd.uniform(0, 6.28)))
        _flat(finish(ob, "solarite", "cyl", _STILL))


def ice_pocket(coll, rnd):
    """Polar/night-side ice: one faceted clean block in a skirt of dirty chunks."""
    _flat(finish(blob(coll, 1.0, (0, 0, 0.3), (0.8, 0.6, 0.55), 2, seed=91, rough=0.45), "ice", "sph", _STILL))
    for k in range(5):
        a = rnd.uniform(0, 6.28)
        r = rnd.uniform(0.14, 0.26)
        _flat(finish(blob(coll, r, (0.55 * math.cos(a), 0.42 * math.sin(a), r * 0.6), (1, 1, 0.7), 1, seed=92 + k, rough=0.4),
                     "ice_dirty", "sph", _STILL))


def basalt_columns(coll, rnd, n, hmax, seed):
    """Columnar basalt: a cluster of hexagonal prisms of stepped heights (Venus vent fields)."""
    rnd = random.Random(seed)
    cells = [(0, 0)] + [(0.46 * math.cos(a), 0.46 * math.sin(a)) for a in (0, 1.05, 2.09, 3.14, 4.19, 5.24)]
    for k, (x, y) in enumerate(cells[:n]):
        h = hmax * (1.0 if k == 0 else rnd.uniform(0.45, 0.85))
        ob = cyl(coll, 0.26, 0.24, h, (x, y, h / 2), 6, rot=(0, 0, rnd.uniform(-0.1, 0.1)))
        _flat(finish(ob, "basalt_column", "cyl", _STILL))


def tessera_slab(coll, rnd):
    """A tilted, deeply cracked highland slab (tesserae)."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    ob = _own(coll, bpy.context.active_object)
    ob.scale = (1.7, 0.95, 0.36)
    ob.rotation_euler = (0.08, 0.2, 0.35)
    ob.location = (0, 0, 0.3)
    bev = ob.modifiers.new("bev", "BEVEL")
    bev.width, bev.segments = 0.06, 2
    _flat(finish(ob, "tessera", "sph", _STILL))
    finish(blob(coll, 0.4, (0.55, -0.3, 0.14), (1.2, 1.0, 0.5), 2, seed=93, rough=0.4), "tessera", "sph", _STILL)


def sulfur_crust(coll, rnd):
    """Low sulfur crust mound with pyrite 'frost' lumps."""
    finish(blob(coll, 1.0, (0, 0, 0.1), (1.6, 1.25, 0.3), 3, seed=94, rough=0.5), "sulfur", "sph", _STILL)
    for k in range(6):
        a = rnd.uniform(0, 6.28)
        r = rnd.uniform(0.08, 0.16)
        finish(blob(coll, r, (0.6 * math.cos(a) * rnd.uniform(0.3, 1), 0.45 * math.sin(a), 0.18), (1, 1, 0.8), 1, seed=95 + k, rough=0.3),
               "sulfur", "sph", _STILL)


def vent_chimney(coll, rnd):
    """A 1.6 m cooled-lava chimney with an emissive vent mouth (the atlas vent_mouth tile glows)."""
    finish(cyl(coll, 0.6, 0.34, 1.3, (0, 0, 0.65), 12), "lava_crust", "cyl", _STILL)
    finish(blob(coll, 0.55, (0, 0, 0.16), (1.5, 1.4, 0.45), 2, seed=96, rough=0.45), "lava_crust", "sph", _STILL)
    finish(cyl(coll, 0.36, 0.22, 0.32, (0, 0, 1.42), 12), "vent_mouth", "cyl", _STILL)
    finish(cyl(coll, 0.2, 0.12, 0.1, (0, 0, 1.56), 10), "vent_mouth", "cyl", _STILL)


def lava_blister(coll, rnd):
    """A cooled lava blister: a cracked dome with a glassy sag at the crown."""
    finish(blob(coll, 1.0, (0, 0, 0.12), (1.35, 1.15, 0.5), 3, seed=97, rough=0.22), "lava_crust", "sph", _STILL)
    finish(blob(coll, 0.3, (0.2, 0.1, 0.5), (1.4, 1.0, 0.35), 1, seed=98, rough=0.35), "vent_glass", "sph", _STILL)


MERCURY_SCENERY = {
    "boulder_a": lambda c, r: rock(c, r, "regolith", (1.2, 1.0, 0.8), 100),
    "boulder_b": lambda c, r: rock(c, r, "basalt", (1.7, 1.25, 1.0), 101),
    "boulder_c": lambda c, r: rock(c, r, "regolith", (0.8, 0.75, 1.1), 102),
    "glass_shard_a": lambda c, r: shard(c, r, "impact_glass", (0.35, 0.22, 0.9), 103),
    "glass_shard_b": lambda c, r: shard(c, r, "impact_glass", (0.5, 0.3, 0.55), 104, lean=0.9),
    "solarite_outcrop": solarite_outcrop,
    "rim_rock": lambda c, r: rock(c, r, "rim_rock", (1.9, 0.8, 0.9), 105),
    "ice_pocket": ice_pocket,
}
VENUS_SCENERY = {
    "column_a": lambda c, r: basalt_columns(c, r, 7, 1.9, 110),
    "column_b": lambda c, r: basalt_columns(c, r, 4, 1.2, 111),
    "tessera_slab": tessera_slab,
    "sulfur_crust": sulfur_crust,
    "vent_chimney": vent_chimney,
    "lava_blister": lava_blister,
}


def _build_scenery(out_path, art, mat_name, table, set_name):
    FA.CURRENT = set_name
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        mat = atlas_material(art, mat_name)
        report = []
        for name, fn in table.items():
            coll = bpy.data.collections.new(f"scenery_{name}")
            scene.collection.children.link(coll)
            fn(coll, random.Random(zlib.crc32(name.encode())))
            ob = join(coll, name, mat)
            ob.data.calc_loop_triangles()
            report.append(f"{name} {len(ob.data.loop_triangles)}")
        print("MERIDIAN scenery tris:", ", ".join(report))
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
        print("MERIDIAN built", out_path)
    finally:
        FA.CURRENT = "earth"


def build_mercury_scenery(out_path=MERCURY_OUT):
    _build_scenery(out_path, MERCURY_ART, "mercury_scenery_atlas", MERCURY_SCENERY, "mercury")


def build_venus_scenery(out_path=VENUS_OUT):
    _build_scenery(out_path, VENUS_ART, "venus_scenery_atlas", VENUS_SCENERY, "venus")


SUNS = {   # review evidence (B-101 accept): 20 instances under that planet's Sun; sky ambient per planet
    "mercury": dict(sun=6.7, sun_col=(1.0, 0.98, 0.95), sun_dir=(-0.55, 0.35, -0.75), ambient=((0.08, 0.06, 0.12), 0.15)),
    "venus": dict(sun=0.1, sun_col=(1.0, 0.8, 0.55), sun_dir=(-0.4, 0.3, -0.85), ambient=((0.85, 0.55, 0.25), 0.9)),
    "mars": dict(sun=0.75, sun_col=(1.0, 0.9, 0.8), sun_dir=(-0.6, 0.4, -0.7), ambient=((0.7, 0.5, 0.4), 0.3)),
}


def field_preview(blend_path, planet, out_png, n=20, seed=7, width=1536, height=512):
    """Stamped field preview: `n` instances of the scenery models from `blend_path` scattered on a
    grey floor under the planet's Sun (SUNS), Eevee, camera side (-Y) at play-plane height."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    from meridian import pngio
    import review
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    scene = bpy.context.scene
    rnd = random.Random(seed)
    protos = [o for o in scene.objects if o.type == "MESH"]
    for o in protos:
        o.hide_render = True
    x0 = -float(n) * 0.9
    x = x0
    for i in range(n):
        src = protos[i % len(protos)] if i < len(protos) else rnd.choice(protos)
        ob = src.copy()
        ob.data = src.data
        ob.hide_render = False
        ob.location = (x, rnd.uniform(-0.6, 0.6), 0.0)
        ob.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
        scene.collection.objects.link(ob)
        x += rnd.uniform(1.3, 2.2)
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, -0.005))
    floor = bpy.context.active_object
    fm = bpy.data.materials.new("field_floor")
    fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.18, 0.18, 0.18, 1)
    floor.data.materials.append(fm)
    S = SUNS[planet]
    sd = bpy.data.lights.new("field_sun", "SUN")
    sd.energy, sd.color = S["sun"], S["sun_col"]
    sun = bpy.data.objects.new("field_sun", sd)
    scene.collection.objects.link(sun)
    sun.rotation_euler = Vector(S["sun_dir"]).to_track_quat("-Z", "Y").to_euler()
    scene.world = scene.world or bpy.data.worlds.new("field_world")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (*S["ambient"][0], 1)
        bg.inputs["Strength"].default_value = S["ambient"][1]
    for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = name
            break
        except TypeError:
            continue
    scene.eevee.taa_render_samples = 16
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.film_transparent = False
    cd = bpy.data.cameras.new("field_cam")
    cd.type = "ORTHO"
    cd.ortho_scale = (x - x0) * 1.05
    cam = bpy.data.objects.new("field_cam", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.location = ((x + x0) / 2, -30.0, 1.2)
    cam.rotation_euler = (math.radians(90), 0, 0)
    path = out_png + ".raw.png"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = pngio.read_png(path)[..., :3]
    os.remove(path)
    review.draw(img, review.stamp_text(blend_path) + " " + planet + " sun " + str(S["sun"]), 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
    pngio.write_png(out_png, np.dstack([pngio.to_u8(np.clip(img, 0, 1)), np.full(img.shape[:2], 255, np.uint8)]))
    print("MERIDIAN field preview", out_png)
    return out_png



if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
