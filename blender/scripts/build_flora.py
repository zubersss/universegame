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
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_flora_atlas as FA  # noqa: E402
from meridian import model  # noqa: E402

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
        nt.links.new(t.outputs["Alpha"], pr.inputs["Alpha"])        # B-109 leaf cards (other tiles: alpha 1)
        for attr, val in (("surface_render_method", "DITHERED"), ("blend_method", "CLIP")):
            try:
                setattr(m, attr, val)
            except (AttributeError, TypeError):
                pass
        m.use_backface_culling = False
        npath = os.path.join(art, "atlas_normal.png")
        if os.path.isfile(npath):
            n = nt.nodes.new("ShaderNodeTexImage")
            n.image = bpy.data.images.load(npath, check_existing=True)
            n.image.colorspace_settings.name = "Non-Color"
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nt.links.new(n.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], pr.inputs["Normal"])
        epath = os.path.join(art, "atlas_emission.png")
        if os.path.isfile(epath):                        # B-101: emissive tiles glow in the previews too
            e = nt.nodes.new("ShaderNodeTexImage")
            e.image = bpy.data.images.load(epath, check_existing=True)
            nt.links.new(e.outputs["Color"], pr.inputs["Emission Color"])
            pr.inputs["Emission Strength"].default_value = 2.0
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

# ---------------------------------------------------------------- B-109 canopies (leaf-cluster cards)
# Crowns are clusters of alpha-cut leaf cards from the atlas 'leafcards' tile (gen_flora_atlas
# CARD_KINDS), each cluster a crossed pair of quads so no cluster vanishes edge-on to the side
# camera. Every card vertex stores a 'bend' normal pointing out of the crown volume (the crown
# centre for broadleaf, the trunk axis for conifers), applied as custom normals after the join, so
# the lighting reads as one rounded crown instead of many flat planes. 'card' = cluster index + 1
# (0 on wood) lets model.py build LOD1 by dropping clusters (manifest lod1_cards) instead of
# decimating cards into slivers. Wood is several tapered segments per limb, smooth-shaded.

def limb(coll, base, length, r0, r1, yaw, pitch, rnd, tile, sway, sides=8, segs=2, wander=0.25, gravity=0.0):
    """A tapered limb of `segs` chained segments from `base` toward (yaw, pitch); each joint turns
    by up to `wander` rad and sags by `gravity` rad. Returns (tip, last yaw, last pitch)."""
    p = Vector(base)
    for s in range(segs):
        ra = r0 + (r1 - r0) * s / segs
        rb = r0 + (r1 - r0) * (s + 1) / segs
        seg_len = length / segs
        d = Vector((math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)))
        mid = p + d * (seg_len / 2)
        rot = (0.0, math.acos(max(-1.0, min(1.0, d.z))), math.atan2(d.y, d.x))
        ob = cyl(coll, ra, rb, seg_len + ra * 0.6, tuple(mid), sides, rot)       # overlap hides the joint
        finish(ob, tile, "cyl", sway)
        p = p + d * seg_len
        yaw += rnd.uniform(-wander, wander)
        pitch += rnd.uniform(-wander, wander) * 0.6 - gravity
    return tuple(p), yaw, pitch


def cards(coll, kind, anchors, size, bend_fn, sway_fn, rnd, roll=0.6):
    """One mesh of crossed card pairs. anchors: [(pos, up)] with `up` the twig direction (card bottom
    at pos). size: card edge in m (x 0.8-1.2 per card). bend_fn(v) -> outward normal at vertex v."""
    u0, v0, u1, v1 = FA.tile_rect("leafcards", sub=kind)
    verts, faces, uvs, bends, ids = [], [], [], [], []
    for k, (pos, up) in enumerate(anchors):
        s = size * rnd.uniform(0.8, 1.2)
        up = Vector(up).normalized()
        ref = Vector((0, 0, 1)) if abs(up.z) < 0.9 else Vector((1, 0, 0))
        side = up.cross(ref).normalized()
        side = Matrix.Rotation(rnd.uniform(-roll, roll), 3, up) @ side
        base = Vector(pos) - up * (0.1 * s)                                       # the card's twig enters 10 % up
        for sd in (side, up.cross(side).normalized()):
            i = len(verts)
            for (a, b) in ((-0.5, 0.0), (0.5, 0.0), (0.5, 1.0), (-0.5, 1.0)):
                v = base + sd * (a * s) + up * (b * s)
                verts.append(tuple(v))
                uvs.append((u0 + (a + 0.5) * (u1 - u0), v0 + b * (v1 - v0)))
                bends.append(bend_fn(v))
                ids.append(k + 1)
            faces.append((i, i + 1, i + 2, i + 3))
    me = bpy.data.meshes.new(f"cards_{kind}")
    me.from_pydata(verts, [], faces)
    me.update()
    uvl = me.uv_layers.new(name="UVMap").data
    for poly in me.polygons:
        poly.use_smooth = True
        for li in poly.loop_indices:
            uvl[li].uv = uvs[me.loops[li].vertex_index]
    ca = me.color_attributes.new("sway", "FLOAT_COLOR", "POINT")
    ba = me.attributes.new("bend", "FLOAT_VECTOR", "POINT")
    ia = me.attributes.new("card", "INT", "POINT")
    for i, v in enumerate(verts):
        ca.data[i].color = (max(0.0, min(1.0, sway_fn(v[2]))), 0.0, 0.0, 1.0)
        ba.data[i].vector = bends[i]
        ia.data[i].value = ids[i]
    me.color_attributes.active_color = ca
    ob = bpy.data.objects.new(f"cards_{kind}", me)
    coll.objects.link(ob)
    return ob


def _shell_anchors(rnd, n, centre, radii, zmin=-0.45, shell=0.55, up_bias=0.45):
    """n points in an ellipsoid crown, biased to the outer shell; up = outward + some world up."""
    c, out = Vector(centre), []
    for _ in range(n):
        while True:
            d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1)))
            if d.length > 1e-3:
                d.normalize()
                if d.z >= zmin:
                    break
        rr = shell + (1 - shell) * rnd.random() ** 0.5
        p = c + Vector((d.x * radii[0], d.y * radii[1], d.z * radii[2])) * rr
        out.append((tuple(p), tuple((d + Vector((0, 0, up_bias))).normalized())))
    return out


def _crown_bend(centre, radii, toward=0.8):
    c = Vector(centre)

    def fn(v):
        o = Vector(v) - c
        o = Vector((o.x / radii[0], o.y / radii[1], o.z / radii[2]))
        return tuple((o.normalized() * toward + Vector((0, 0, 1 - toward))).normalized()) if o.length > 1e-4 else (0.0, 0.0, 1.0)
    return fn


def _height_sway(z0, z1, lo=0.5, hi=1.0):
    return lambda z: lo + (hi - lo) * max(0.0, min(1.0, (z - z0) / max(z1 - z0, 1e-3)))


def _wood_sway(h):
    return lambda f, z: 0.45 * min(1.0, max(0.0, z / h)) ** 2


def tree_oak(coll, rnd):
    """Oak (B-109): flared trunk in three leaning segments, five forked main limbs, a broad crown of
    ~120 crossed oak-leaf clusters around the limb ends."""
    ws = _wood_sway(8.0)
    finish(cyl(coll, 0.62, 0.4, 0.7, (0, 0, 0.35), 12), "bark_oak", "cyl", ws)                  # root flare
    top, _, _ = limb(coll, (0, 0, 0.3), 3.9, 0.42, 0.27, rnd.uniform(0, 6.28), math.radians(86), rnd, "bark_oak",
                     ws, sides=12, segs=3, wander=0.08)
    for k in range(4):                                                                            # surface roots
        limb(coll, (0, 0, 0.35), rnd.uniform(0.7, 1.0), 0.16, 0.05, k * 1.57 + rnd.uniform(-0.3, 0.3), -0.35, rnd,
             "bark_oak", ws, sides=6, segs=1)
    centre, radii = (0.0, 0.0, 6.0), (2.7, 2.5, 2.0)
    for k in range(5):
        yaw = k * 1.257 + rnd.uniform(-0.25, 0.25)
        b0 = (top[0] * 0.8, top[1] * 0.8, 3.0 + 0.25 * k)
        tip, y, p = limb(coll, b0, rnd.uniform(1.9, 2.5), 0.17, 0.08, yaw, rnd.uniform(0.45, 0.8), rnd, "bark_oak",
                         ws, sides=8, segs=2, wander=0.3)
        for j in range(2):
            limb(coll, tip, rnd.uniform(0.8, 1.3), 0.075, 0.03, y + (0.6 if j else -0.6), p + rnd.uniform(-0.2, 0.3), rnd,
                 "bark_oak", ws, sides=6, segs=1)
    an = _shell_anchors(rnd, 120, centre, radii)
    cards(coll, "oak", an, 1.55, _crown_bend(centre, radii), _height_sway(3.5, 8.2, 0.55, 1.0), rnd)


def tree_birch(coll, rnd):
    """Birch (B-109): a slim white trunk with a slight S lean, ascending limbs, a narrow tall crown of
    ~100 small drooping leaf clusters."""
    ws = _wood_sway(9.0)
    top, _, _ = limb(coll, (0, 0, 0.0), 8.0, 0.19, 0.06, rnd.uniform(0, 6.28), math.radians(87), rnd, "bark_birch",
                     ws, sides=10, segs=4, wander=0.07)
    centre, radii = (top[0] * 0.6, top[1] * 0.6, 6.3), (1.55, 1.45, 2.5)
    for k in range(6):
        z = 3.6 + 0.65 * k
        f = (z - 0.0) / 8.0
        base = (top[0] * f, top[1] * f, z)
        tip, y, p = limb(coll, base, rnd.uniform(1.2, 1.9), 0.07, 0.025, k * 2.4 + rnd.uniform(-0.3, 0.3),
                         rnd.uniform(0.75, 1.1), rnd, "bark_birch", ws, sides=6, segs=2, wander=0.25, gravity=0.35)
    an = [(p, tuple((Vector(u) + Vector((0, 0, -0.9))).normalized())) for p, u in _shell_anchors(rnd, 100, centre, radii, up_bias=0.0)]
    cards(coll, "birch", an, 1.15, _crown_bend(centre, radii), _height_sway(3.5, 8.8, 0.55, 1.0), rnd)


def tree_spruce(coll, rnd):
    """Spruce (B-109): a tapered trunk carrying 11 tiers of needle sprays (crossed needle cards along
    drooping branches), wide at the bottom, a spire of upturned sprays at the top."""
    ws = _wood_sway(10.0)
    finish(cyl(coll, 0.3, 0.05, 10.0, (0, 0, 5.0), 10), "bark_spruce", "cyl", ws)
    tiers, an, bend_axis = 11, [], 0.0
    for t in range(tiers):
        f = t / (tiers - 1)
        z = 1.3 + 8.0 * f
        R = 2.5 * (1 - f) ** 0.9 + 0.35
        n = max(4, int(round(10 * (1 - f))) + 3)
        off = rnd.uniform(0, 6.28)
        for k in range(n):
            yaw = off + k * 2 * math.pi / n + rnd.uniform(-0.2, 0.2)
            droop = -0.35 + 0.5 * f + rnd.uniform(-0.1, 0.1)
            d = Vector((math.cos(yaw), math.sin(yaw), droop)).normalized()
            if f < 0.85:
                limb(coll, (0, 0, z), R * 0.75, 0.05 * (1 - f) + 0.015, 0.012, yaw, math.asin(d.z), rnd, "bark_spruce",
                     ws, sides=4, segs=1)
            an.append((tuple(Vector((0, 0, z)) + d * 0.1), tuple(d)))
    an.append(((0.0, 0.0, 9.3), (0.0, 0.0, 1.0)))                                               # the leader

    def bend(v):
        o = Vector((v[0], v[1], 0.0))
        return tuple((o.normalized() * 0.7 + Vector((0, 0, 0.55))).normalized()) if o.length > 1e-4 else (0.0, 0.0, 1.0)
    cards(coll, "needle", an, 2.1, bend, _height_sway(1.0, 10.0, 0.45, 1.0), rnd, roll=0.25)


def _bush(coll, rnd, n, centre, radii, size, stems):
    ws = lambda f, z: 0.15 * f
    for k in range(stems):
        limb(coll, (rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), 0.0), rnd.uniform(0.6, 0.9), 0.04, 0.015,
             rnd.uniform(0, 6.28), rnd.uniform(0.9, 1.3), rnd, "bark_oak", ws, sides=5, segs=1)
    an = _shell_anchors(rnd, n, centre, radii, zmin=-0.2, shell=0.45, up_bias=0.6)
    cards(coll, "bush", an, size, _crown_bend(centre, radii, 0.75), _height_sway(0.0, centre[2] + radii[2], 0.15, 0.8), rnd)


def bush_a(coll, rnd):
    _bush(coll, rnd, 60, (0.0, 0.0, 0.55), (0.95, 0.8, 0.55), 0.8, 4)


def bush_b(coll, rnd):
    _bush(coll, rnd, 46, (0.0, 0.0, 0.5), (0.8, 0.7, 0.5), 0.72, 3)
    for k in range(12):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0.45, 0.7)
        finish(blob(coll, 0.05, (rr * math.cos(a), rr * math.sin(a) * 0.85, rnd.uniform(0.35, 0.85)), subdiv=1, seed=40 + k, rough=0.0),
               "berries", "sph", lambda f, z: 0.5)


def dead_tree(coll, rnd):
    """Dead tree (B-109): a leaning, gnarled trunk in segments, seven crooked two-segment limbs that fork
    twice, smooth bark (no cones)."""
    ws = _wood_sway(6.0)
    top, ty, tp = limb(coll, (0, 0, 0.0), 5.0, 0.32, 0.1, rnd.uniform(0, 6.28), math.radians(84), rnd, "bark_dead",
                       ws, sides=10, segs=4, wander=0.12)
    for k in range(7):
        f = 0.45 + 0.08 * k
        base = (top[0] * f, top[1] * f, 5.0 * f)
        tip, y, p = limb(coll, base, rnd.uniform(1.1, 1.9), 0.11 * (1.1 - f * 0.5), 0.04, k * 2.2 + rnd.uniform(-0.4, 0.4),
                         rnd.uniform(0.25, 0.85), rnd, "bark_dead", ws, sides=7, segs=2, wander=0.45)
        for j in range(2):
            t2, y2, p2 = limb(coll, tip, rnd.uniform(0.5, 0.9), 0.04, 0.015, y + (0.55 if j else -0.55), p + rnd.uniform(-0.3, 0.4),
                              rnd, "bark_dead", ws, sides=5, segs=1)
            limb(coll, t2, rnd.uniform(0.25, 0.45), 0.015, 0.006, y2 + rnd.uniform(-0.6, 0.6), p2 + 0.2, rnd, "bark_dead",
                 ws, sides=4, segs=1)


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
        model.bend_normals(ob)                          # B-109: crown-volume normals on the cards
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


def _hex_column(coll, x, y, r, h, tile, rnd, tilt=0.0, yaw=0.0, steps=3):
    """One basalt column as stacked hexagonal segments whose tops break at different heights
    (the stepped, broken crowns of a real colonnade); `tilt` leans the whole column."""
    z = 0.0
    hs = [h * f for f in (0.55, 0.28, 0.17)][:steps]
    for k, hk in enumerate(hs):
        rk = r * (1.0 - 0.06 * k)
        dx = (k * 0.35 * r) * math.cos(yaw) if k else 0.0            # upper segments sit off-axis: a broken step
        dy = (k * 0.35 * r) * math.sin(yaw) if k else 0.0
        ob = cyl(coll, rk, rk * rnd.uniform(0.9, 1.0), hk, (x + dx + math.sin(tilt) * (z + hk / 2), y + dy, (z + hk / 2) * math.cos(tilt)),
                 6, rot=(0, tilt, yaw))
        _flat(finish(ob, tile, "cyl", _STILL))
        z += hk
        if rnd.random() < 0.45:                                      # some columns stop early (sheared)
            break


def basalt_columns(coll, rnd, n, hmax, seed):
    """Columnar basalt (B-101 round 2): a cluster of 5-9 hexagonal prisms with broken stepped
    tops, one tilted outlier leaning out of the cluster, and a rubble skirt of fallen segments."""
    rnd = random.Random(seed)
    cells = [(0.0, 0.0)] + [(0.5 * math.cos(a), 0.5 * math.sin(a)) for a in (0.0, 1.05, 2.09, 3.14, 4.19, 5.24)]
    cells += [(1.0 * math.cos(a), 1.0 * math.sin(a)) for a in (0.5, 2.6, 4.7)]
    for k, (x, y) in enumerate(cells[:n]):
        h = hmax * (1.0 if k == 0 else rnd.uniform(0.4, 0.9))
        _hex_column(coll, x, y, rnd.uniform(0.2, 0.28), h, "basalt_column", rnd, yaw=rnd.uniform(0, 6.28), steps=3)
    ox, oy = 0.75 * math.cos(1.8), 0.75 * math.sin(1.8)              # the tilted outlier, leaning outward
    _hex_column(coll, ox, oy, 0.22, hmax * 0.7, "basalt_column", rnd, tilt=0.42, yaw=1.8, steps=2)
    for k in range(4):                                               # fallen segments at the foot
        a = rnd.uniform(0, 6.28)
        ob = cyl(coll, 0.18, 0.17, rnd.uniform(0.25, 0.5), (1.1 * math.cos(a), 0.9 * math.sin(a), 0.16), 6,
                 rot=(math.radians(90), 0, a))
        _flat(finish(ob, "basalt", "cyl", _STILL))


def tessera_slab(coll, rnd):
    """Tessera (B-101 round 2): a tilted highland slab with a ridged, cracked top (a displaced
    cap over the block) and a second slab leaning on it."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    ob = _own(coll, bpy.context.active_object)
    ob.scale = (1.7, 0.95, 0.3)
    ob.rotation_euler = (0.06, 0.16, 0.35)
    ob.location = (0, 0, 0.22)
    bev = ob.modifiers.new("bev", "BEVEL")
    bev.width, bev.segments = 0.05, 2
    _flat(finish(ob, "tessera", "sph", _STILL))
    cap = blob(coll, 1.0, (0.02, 0.0, 0.42), (0.86, 0.5, 0.16), 3, seed=93, rough=0.5)      # ridged cracked top
    cap.rotation_euler = (0.06, 0.16, 0.35)
    finish(cap, "tessera", "sph", _STILL)
    for k in range(5):                                               # parallel ridges across the top
        t = -0.6 + 0.3 * k
        ob = cyl(coll, 0.05, 0.03, 0.9, (t * math.cos(0.35), t * math.sin(0.35), 0.5 + 0.16 * t), 6,
                 rot=(math.radians(90), 0, 0.35 + math.radians(90)))
        _flat(finish(ob, "tessera", "cyl", _STILL))
    side = blob(coll, 0.45, (0.9, -0.5, 0.2), (1.3, 0.8, 0.45), 2, seed=94, rough=0.4)         # the leaning second slab
    side.rotation_euler = (0.3, 0.1, 0.9)
    finish(side, "tessera", "sph", _STILL)


def sulfur_crust(coll, rnd):
    """Sulfur crust (B-101 round 2): a low mound carrying raised, cracked crust plates (0.1-0.2 m
    relief) with brighter pyrite-flecked rims (the sulfur_rim tile), tilted every which way."""
    finish(blob(coll, 1.0, (0, 0, 0.08), (1.6, 1.25, 0.26), 2, seed=95, rough=0.4), "sulfur", "sph", _STILL)
    for k in range(9):
        a = k * 0.7 + rnd.uniform(-0.2, 0.2)
        rr = 0.0 if k == 0 else rnd.uniform(0.45, 1.05)
        x, y = rr * math.cos(a) * 1.2, rr * math.sin(a) * 0.9
        r, h = rnd.uniform(0.26, 0.42), rnd.uniform(0.1, 0.2)
        z = 0.2 - 0.12 * rr + h / 2
        rot = (rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), rnd.uniform(0, 6.28))
        rim = cyl(coll, r * 1.08, r * 1.02, h, (x, y, z), rnd.choice((5, 6, 7)), rot=rot)
        _flat(finish(rim, "sulfur_rim", "cyl", _STILL))
        top = cyl(coll, r * 0.82, r * 0.86, h * 0.5, (x, y, z + h * 0.42), 6, rot=rot)
        _flat(finish(top, "sulfur", "cyl", _STILL))


def vent_chimney(coll, rnd):
    """Vent chimney (B-101 round 2): a built-up cone of cooled lava with an irregular lumpy rim,
    a sag on one side where the wall slumped, and a recessed glowing mouth (vent_mouth tile,
    emissive) with glow spill over the lip."""
    finish(blob(coll, 0.6, (0, 0, 0.16), (1.6, 1.45, 0.5), 2, seed=96, rough=0.45), "lava_crust", "sph", _STILL)
    body = cyl(coll, 0.66, 0.5, 1.05, (0, 0, 0.52), 12)            # cycle 223: lower, wider throat
    finish(body, "lava_crust", "cyl", _STILL)
    for k in range(10):                                              # rim lumps at uneven heights; the sag side sits lower
        a = k * 0.628 + rnd.uniform(-0.15, 0.15)
        sag = 0.5 * max(0.0, math.cos(a - 2.2)) ** 2                 # the slumped side
        r = rnd.uniform(0.11, 0.18)
        lump = blob(coll, r, (0.47 * math.cos(a), 0.47 * math.sin(a), 1.0 + rnd.uniform(0.0, 0.12) - 0.24 * sag), (1.1, 1.0, 0.8), 1,
                    seed=100 + k, rough=0.35)
        finish(lump, "lava_crust", "sph", _STILL)
    slump = blob(coll, 0.3, (0.6 * math.cos(2.2), 0.6 * math.sin(2.2), 0.6), (1.3, 1.0, 1.4), 1, seed=111, rough=0.3)
    finish(slump, "lava_crust", "sph", _STILL)
    mouth = cyl(coll, 0.44, 0.22, 0.4, (0, 0, 0.86), 12)            # recessed glowing throat (cycle 223: wider, lower)
    finish(mouth, "vent_mouth", "cyl", _STILL)
    for k in range(4):                                               # glow spill over the lip
        a = rnd.uniform(0, 6.28)
        finish(blob(coll, 0.12, (0.44 * math.cos(a), 0.44 * math.sin(a), 1.02), (1.4, 1.2, 0.5), 1, seed=120 + k, rough=0.0),
               "vent_mouth", "sph", _STILL)


def lava_blister(coll, rnd):
    """Lava blister (B-101 round 2): a cracked, cooled dome whose seams still glow (vent_mouth
    tile, emissive) in a radial crack pattern, with a glassy sag at the crown."""
    finish(blob(coll, 1.0, (0, 0, 0.1), (1.35, 1.15, 0.52), 3, seed=97, rough=0.28), "lava_crust", "sph", _STILL)
    for k in range(7):                                               # glowing seams radiating from the crown
        a = k * 0.9 + rnd.uniform(-0.25, 0.25)
        ln = rnd.uniform(0.5, 0.95)
        mid = 0.5 * ln
        x, y = mid * 1.35 * math.cos(a) + 0.1, mid * 1.15 * math.sin(a) + 0.05
        z = 0.1 + 0.52 * math.sqrt(max(0.0, 1.0 - (mid * 1.0) ** 2)) * 0.95
        pitch = math.atan2(0.52 * mid, math.sqrt(max(1e-3, 1.0 - mid * mid)))     # follow the dome's slope
        ob = cyl(coll, 0.03, 0.025, ln * 1.25, (x, y, z), 4, rot=(0, math.radians(90) - 0.0, a))
        ob.rotation_euler = (0, math.radians(90) + pitch * 0.9, a)
        finish(ob, "vent_mouth", "cyl", _STILL)
    finish(blob(coll, 0.28, (0.1, 0.05, 0.58), (1.3, 1.0, 0.3), 1, seed=98, rough=0.3), "vent_glass", "sph", _STILL)


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
    "column_a": lambda c, r: basalt_columns(c, r, 9, 1.9, 110),
    "column_b": lambda c, r: basalt_columns(c, r, 5, 1.3, 111),
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
    "earth": dict(sun=3.5, sun_col=(1.0, 0.97, 0.92), sun_dir=(-0.6, 0.4, -0.7), ambient=((0.45, 0.58, 0.78), 0.7)),
    "mercury": dict(sun=6.7, sun_col=(1.0, 0.98, 0.95), sun_dir=(-0.55, 0.35, -0.75), ambient=((0.08, 0.06, 0.12), 0.15)),
    "venus": dict(sun=0.1, sun_col=(1.0, 0.8, 0.55), sun_dir=(-0.4, 0.3, -0.85), ambient=((0.85, 0.55, 0.25), 0.9)),
    "mars": dict(sun=0.75, sun_col=(1.0, 0.9, 0.8), sun_dir=(-0.6, 0.4, -0.7), ambient=((0.7, 0.5, 0.4), 0.3)),
}


def field_preview(blend_path, planet, out_png, n=20, seed=7, width=1536, height=512, names=None, camp=False):
    """Stamped field preview: `n` instances of the scenery models from `blend_path` scattered on a
    grey floor under the planet's Sun (SUNS), Eevee, camera side (-Y) at play-plane height."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    from meridian import pngio
    import review
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    scene = bpy.context.scene
    rnd = random.Random(seed)
    protos = [o for o in scene.objects if o.type == "MESH" and (names is None or o.name in names)]
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
        if camp:                                     # B-109: z 2-12 m behind the play plane, across the 1080p frame
            dpt = rnd.uniform(2.0, 12.0)
            half = (28.5 + dpt) * math.tan(math.radians(17.5)) * 16 / 9
            ob.location = (rnd.uniform(-half, half) * 0.92, dpt, 0.0)
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
    if camp:                                         # the game's side rail: 35 deg vertical FOV at 28.5 m = 60 px/m at 1080p
        cd.type, cd.sensor_fit, cd.angle = "PERSP", "VERTICAL", math.radians(35)
        scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    cam = bpy.data.objects.new("field_cam", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.location = (0.0, -28.5, 6.5) if camp else ((x + x0) / 2, -30.0, 1.2)
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
