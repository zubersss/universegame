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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_flora_atlas as FA  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "earth_flora.blend")
ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art", "props", "earth_flora")


def atlas_material():
    m = bpy.data.materials.new("earth_flora_atlas")
    m.use_nodes = True
    nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]
    pr.inputs["Roughness"].default_value = 0.8
    cpath = os.path.join(ART, "atlas_color.png")
    if os.path.isfile(cpath):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(cpath, check_existing=True)
        nt.links.new(t.outputs["Color"], pr.inputs["Base Color"])
        npath = os.path.join(ART, "atlas_normal.png")
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


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
