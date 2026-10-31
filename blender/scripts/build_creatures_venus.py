"""Builds blender/sources/creatures/venus.blend: Venus cloud-deck fliers (B-032, Bible §7.4).

Fliers, so no ground: each creature is centred on the origin and the sheet pivot is the
centre (render.py autofit checks the bottom extent too when the pivot is raised). Same clip
set and timing as the walkers (idle = drift/hover, walk = move, attack, hurt, death), so the
Unity loader needs nothing new. One bold exaggeration each, Venus palette (orange-cream,
sulfur yellow), readable at 60 px/m:
  * sulfur_drifter (~2.4 m gasbag filter feeder, 320 px): translucent sulfur-cream gas sac with
    glowing veins (emission), a smaller fore-sac, an opaque gondola body and four filter
    tendrils. Tendrils use the creature standard (metaball capsules -> one mesh -> armature
    with automatic weights); the sacs ride the root bone and are keyed for pulse and deflate.
  * acidmoth (~0.3 m body, 128 px): sulfur-orange moth, fore and hind wings per side with
    acid-yellow emissive eyespots. Wings flap about the body axis but never go flat: a flat
    wing is edge-on to the side camera and vanishes.

  blender --background --factory-startup --python blender/scripts/build_creatures_venus.py
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_creatures_earth import (CLIP_LEN, CLIP_ORDER, CLIP_START, _rig_child, bind_auto,  # noqa: E402
                                   ground_exactly, set_pose)
from build_pilgrim import flat_material, lin  # noqa: E402
from build_surveyor import _constant  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "creatures", "venus.blend")


def _link(coll, ob):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)


def _select_only(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)


def _frames():
    for name in CLIP_ORDER:
        for i in range(CLIP_LEN[name]):
            yield name, i, CLIP_START[name] + i


# ---------------------------------------------------------------- sulfur drifter

def sac_material(name, base, vein, alpha, vein_scale):
    """Translucent sac: sulfur-cream base, glowing vein network (Voronoi cell edges) in the
    albedo and the emission; Alpha < 1 so the colour pass keeps it see-through."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    pr.inputs["Roughness"].default_value = 0.35
    pr.inputs["Alpha"].default_value = alpha
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"
    vo.inputs["Scale"].default_value = vein_scale
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.06, 0.0
    L.new(vo.outputs["Distance"], mr.inputs["Value"])
    col = N.new("ShaderNodeMix"); col.data_type = "RGBA"
    L.new(mr.outputs["Result"], col.inputs[0])
    col.inputs[6].default_value = lin(base); col.inputs[7].default_value = lin(vein)
    L.new(col.outputs[2], pr.inputs["Base Color"])
    em = N.new("ShaderNodeMix"); em.data_type = "RGBA"
    L.new(mr.outputs["Result"], em.inputs[0])
    em.inputs[6].default_value = (0, 0, 0, 1); em.inputs[7].default_value = lin(vein)
    L.new(em.outputs[2], pr.inputs["Emission Color"])
    pr.inputs["Emission Strength"].default_value = 1.6
    return m


def build_drifter(scene):
    sp = "sulfur_drifter"
    coll = bpy.data.collections.new(sp)
    scene.collection.children.link(coll)
    # Armature: root at the sac centre, four two-segment tendrils hanging from the gondola.
    ad = bpy.data.armatures.new(f"{sp}_rig")
    rig = bpy.data.objects.new(f"{sp}_rig", ad)
    coll.objects.link(rig)
    _select_only(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = ad.edit_bones
    root = eb.new("root"); root.head, root.tail = Vector((0, 0, 0.2)), Vector((0, 0, 0.6))
    tend = [(-0.28, -0.12), (-0.08, 0.12), (0.12, -0.1), (0.3, 0.1)]
    for k, (x, y) in enumerate(tend):
        a = eb.new(f"tA_{k}"); a.head, a.tail = Vector((x, y, -0.38)), Vector((x - 0.04, y, -0.8))
        a.parent = root
        b = eb.new(f"tB_{k}"); b.head, b.tail = a.tail.copy(), Vector((x - 0.1, y, -1.18))
        b.parent = a
    bpy.ops.object.mode_set(mode="OBJECT")

    # Tendrils + gondola: metaball capsules -> one mesh -> automatic weights.
    mb = bpy.data.metaballs.new(f"{sp}_mb")
    mb.resolution = mb.render_resolution = 0.012
    mb.threshold = 0.6
    for k, (x, y) in enumerate(tend):
        pts = [(x, y, -0.36, 0.05), (x - 0.04, y, -0.8, 0.04), (x - 0.1, y, -1.18, 0.022)]
        for (x0, y0, z0, r0), (x1, y1, z1, r1) in zip(pts, pts[1:]):
            d = Vector((x1 - x0, y1 - y0, z1 - z0))
            c = mb.elements.new(type="CAPSULE")
            c.co = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
            c.radius = 1.35 * (r0 + r1) / 2
            c.size_x = d.length / 2
            c.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())
    mbo = bpy.data.objects.new(f"{sp}_mb", mb)
    coll.objects.link(mbo)
    _select_only(mbo)
    bpy.ops.object.convert(target="MESH")
    body = bpy.context.view_layer.objects.active
    body.name = f"{sp}_body"
    for p in body.data.polygons:
        p.use_smooth = True
    body.data.materials.append(flat_material(f"{sp}_skin", (176, 112, 62), rough=0.7))
    bind_auto(body, rig)

    # Sacs: rigid on the root bone (keyed scale = pulse / squash / deflate).
    sacm = sac_material(f"{sp}_sac", (236, 212, 146), (255, 196, 72), 0.85, 5.0)
    sacs = []
    # Sac overlaps the gondola top (first build: a gap made the sac float detached).
    for name, loc, rad, scl in (("sac", (0.0, 0.0, 0.46), 0.6, (1.3, 0.9, 1.05)),
                                ("foresac", (0.6, 0.0, 0.3), 0.3, (1.0, 0.85, 0.95))):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=rad, location=loc)
        s = bpy.context.active_object
        s.name = f"{sp}_{name}"
        for v in s.data.vertices:                      # origin at the sac's base: squash/deflate
            v.co.z += rad                              # keeps it seated on the gondola
        s.location.z -= rad * scl[2]
        s.scale = scl
        _link(coll, s)
        bpy.ops.object.shade_smooth()
        s.data.materials.append(sacm)
        mw = s.matrix_world.copy()
        s.parent = rig; s.parent_type = "BONE"; s.parent_bone = "root"
        bpy.context.view_layer.update()
        s.matrix_world = mw
        sacs.append((s, Vector(scl)))
    # Gondola (opaque body) and eye: rigid on the root bone like the sacs. As part of the
    # tendril mesh, automatic weights tied it to the tendril bones and it swung with them.
    rigid = []
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=(0.05, 0.0, -0.26))
    gon = bpy.context.active_object
    gon.name = f"{sp}_gondola"
    gon.scale = (0.42, 0.26, 0.22)
    _link(coll, gon)
    bpy.ops.object.shade_smooth()
    gon.data.materials.append(flat_material(f"{sp}_gondola", (176, 112, 62), rough=0.7))
    rigid.append(gon)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.045, location=(0.44, -0.08, -0.25))
    eye = bpy.context.active_object
    _link(coll, eye)
    eye.data.materials.append(flat_material(f"{sp}_eye", (36, 24, 20), rough=0.3))
    rigid.append(eye)
    for ob in rigid:
        mw = ob.matrix_world.copy()
        ob.parent = rig; ob.parent_type = "BONE"; ob.parent_bone = "root"
        bpy.context.view_layer.update()
        ob.matrix_world = mw

    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        s2 = math.sin(2 * math.pi * t)
        pitch, z, squash, tsw, tlag = 0.0, 0.0, 1.0, 0.0, 0.0
        if name == "idle":
            z, squash, tsw = 0.04 * s2, 1.0 + 0.03 * s2, 6 * s2
        elif name == "walk":
            pitch, tlag, tsw, squash = -6.0, -16.0, 8 * s2, 1.0 + 0.05 * math.sin(4 * math.pi * t)
        elif name == "attack":
            k = [0.0, 0.4, 1.0, 0.8, 0.4, 0.1][i]
            pitch, tlag = 4 * k, 38 * k                            # tendrils lash forward
        elif name == "hurt":
            k = [1.0, 0.5][i]
            pitch, squash, tsw = 8 * k, 1.0 - 0.15 * k, -10 * k
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            pitch, z, squash, tlag = 24 * k, -0.25 * k, 1.0 - 0.42 * k, 20 * k
        rig.rotation_euler = (0.0, math.radians(pitch), 0.0)
        rig.location = (0.0, 0.0, z)
        rig.keyframe_insert("rotation_euler", frame=f)
        rig.keyframe_insert("location", frame=f)
        for k in range(len(tend)):
            ph = 0.6 * k
            set_pose(rig, f"tA_{k}", tlag + tsw * math.cos(ph))
            set_pose(rig, f"tB_{k}", 0.6 * tlag + 1.4 * tsw * math.cos(ph + 0.8))
        for pb in rig.pose.bones:
            pb.keyframe_insert("rotation_quaternion", frame=f)
        for s, base in sacs:
            s.scale = (base.x * (2 - squash) ** 0.5, base.y, base.z * squash)   # squash widens a little
            s.keyframe_insert("scale", frame=f)
    for ob in [rig] + [s for s, _ in sacs]:
        if ob.animation_data and ob.animation_data.action:
            _constant(ob.animation_data.action)


# ---------------------------------------------------------------- acidmoth

def wing_material(name, base, edge, spot, spot_at, spot_r):
    """Wing: orange-cream membrane darkening to the edge, acid-yellow emissive eyespot with
    a dark ring (object space of the wing, origin at the wing root)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    pr.inputs["Roughness"].default_value = 0.6
    tc = N.new("ShaderNodeTexCoord")
    dist = N.new("ShaderNodeVectorMath"); dist.operation = "DISTANCE"
    L.new(tc.outputs["Object"], dist.inputs[0])
    dist.inputs[1].default_value = spot_at
    ring = N.new("ShaderNodeMapRange"); ring.interpolation_type = "SMOOTHSTEP"
    ring.inputs["From Min"].default_value, ring.inputs["From Max"].default_value = spot_r * 1.45, spot_r * 1.15
    L.new(dist.outputs["Value"], ring.inputs["Value"])
    eye = N.new("ShaderNodeMapRange"); eye.interpolation_type = "SMOOTHSTEP"
    eye.inputs["From Min"].default_value, eye.inputs["From Max"].default_value = spot_r, spot_r * 0.8
    L.new(dist.outputs["Value"], eye.inputs["Value"])
    rad = N.new("ShaderNodeVectorMath"); rad.operation = "LENGTH"
    L.new(tc.outputs["Object"], rad.inputs[0])
    edg = N.new("ShaderNodeMapRange")
    edg.inputs["From Min"].default_value, edg.inputs["From Max"].default_value = 0.08, 0.2
    L.new(rad.outputs["Value"], edg.inputs["Value"])
    c1 = N.new("ShaderNodeMix"); c1.data_type = "RGBA"
    L.new(edg.outputs["Result"], c1.inputs[0])
    c1.inputs[6].default_value = lin(base); c1.inputs[7].default_value = lin(edge)
    c2 = N.new("ShaderNodeMix"); c2.data_type = "RGBA"                  # dark ring
    L.new(ring.outputs["Result"], c2.inputs[0])
    L.new(c1.outputs[2], c2.inputs[6]); c2.inputs[7].default_value = lin((40, 26, 18))
    c3 = N.new("ShaderNodeMix"); c3.data_type = "RGBA"                  # acid-yellow eye
    L.new(eye.outputs["Result"], c3.inputs[0])
    L.new(c2.outputs[2], c3.inputs[6]); c3.inputs[7].default_value = lin(spot)
    L.new(c3.outputs[2], pr.inputs["Base Color"])
    em = N.new("ShaderNodeMix"); em.data_type = "RGBA"
    L.new(eye.outputs["Result"], em.inputs[0])
    em.inputs[6].default_value = (0, 0, 0, 1); em.inputs[7].default_value = lin(spot)
    L.new(em.outputs[2], pr.inputs["Emission Color"])
    pr.inputs["Emission Strength"].default_value = 2.0
    return m


def build_moth(scene):
    sp = "acidmoth"
    coll = bpy.data.collections.new(sp)
    scene.collection.children.link(coll)
    root = bpy.data.objects.new(f"{sp}_root", None)
    coll.objects.link(root)
    bodym = flat_material(f"{sp}_body", (196, 120, 52), rough=0.8)
    # Body: thorax + abdomen + head, as metaballs -> one mesh.
    mb = bpy.data.metaballs.new(f"{sp}_mb")
    mb.resolution = mb.render_resolution = 0.006
    for co, r, sx in (((0.02, 0, 0), 0.045, 1.2), ((-0.1, 0, -0.01), 0.04, 1.9), ((0.09, 0, 0.005), 0.032, 1.0)):
        e = mb.elements.new(type="ELLIPSOID"); e.co = co; e.radius = r * 1.35; e.size_x = sx
    mbo = bpy.data.objects.new(f"{sp}_mb", mb)
    coll.objects.link(mbo)
    _select_only(mbo)
    bpy.ops.object.convert(target="MESH")
    body = bpy.context.view_layer.objects.active
    body.name = f"{sp}_body"
    for p in body.data.polygons:
        p.use_smooth = True
    body.data.materials.append(bodym)
    body.parent = root
    # Antennae: two thin feathered curves forward-up.
    for sy in (-1, 1):
        bpy.ops.curve.primitive_bezier_curve_add(location=(0.11, sy * 0.012, 0.02))
        cu = bpy.context.active_object
        _link(coll, cu)
        cu.data.bevel_depth = 0.004
        pts = cu.data.splines[0].bezier_points
        pts[0].co, pts[1].co = Vector((0, 0, 0)), Vector((0.08, sy * 0.03, 0.07))
        for p in pts:
            p.handle_left_type = p.handle_right_type = "AUTO"
        cu.data.materials.append(bodym)
        cu.parent = root
    wings = []
    spec = [("fore", 0.035, 0.012, 0.19, 0.12, (0.0, 0.11, 0.0), 0.04),
            ("hind", -0.045, -0.005, 0.14, 0.1, (-0.01, 0.08, 0.0), 0.03)]
    for name, wx, wz, span, chord, spot_at, spot_r in spec:
        for sy in (-1, 1):
            # Ellipse in the XY plane, root at the object origin, extending to y = sy * span.
            n = 24
            verts = [(0.0, 0.0, 0.0)] + [(chord / 2 * math.cos(2 * math.pi * k / n) - chord * 0.1,
                                          sy * span / 2 * (1 + math.sin(2 * math.pi * k / n)), 0.0)
                                         for k in range(n)]
            faces = [(0, 1 + k, 1 + (k + 1) % n) for k in range(n)]
            me = bpy.data.meshes.new(f"{sp}_{name}_{sy}")
            me.from_pydata(verts, [], faces)
            w = bpy.data.objects.new(f"{sp}_wing_{name}_{'far' if sy > 0 else 'near'}", me)
            coll.objects.link(w)
            w.location = (wx, sy * 0.02, wz)
            sol = w.modifiers.new("solid", "SOLIDIFY"); sol.thickness = 0.003
            w.data.materials.append(wing_material(f"{sp}_wing_{name}_{sy}", (232, 176, 96), (150, 82, 36),
                                                  (226, 255, 60), (spot_at[0], sy * spot_at[1], 0.0), spot_r))
            w.parent = root
            wings.append((w, sy, name))

    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        flap = math.sin(2 * math.pi * t * (2 if name == "walk" else 1))
        pitch, roll, z, base, amp = 0.0, 0.0, 0.0, 55.0, 25.0
        if name == "idle":
            z = 0.012 * math.sin(2 * math.pi * t)
        elif name == "walk":
            pitch, amp = -12.0, 28.0
        elif name == "attack":
            k = [0.0, 0.5, 1.0, 1.0, 0.6, 0.2][i]
            pitch, base, amp = 32 * k, 55 + 25 * k, 25 * (1 - k)        # dive, wings swept back up
        elif name == "hurt":
            k = [1.0, 0.5][i]
            roll, base, amp = 18 * k, 40.0, 6.0
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            pitch, roll, z, base, amp = 60 * k, 25 * k, -0.08 * k, 55 + 25 * k, 6 * (1 - k)
        root.location = (0.0, 0.0, z)
        root.rotation_euler = (math.radians(roll), math.radians(pitch), 0.0)
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_euler", frame=f)
        for w, sy, wname in wings:
            ang = base + amp * flap * (0.85 if wname == "hind" else 1.0)
            ang = min(85.0, max(22.0, ang))                         # never flat (edge-on), never past vertical
            w.rotation_euler = (math.radians(ang) * sy, 0.0, 0.0)   # tips up on both sides
            w.keyframe_insert("rotation_euler", frame=f)
    for ob in [root] + [w for w, _, _ in wings]:
        if ob.animation_data and ob.animation_data.action:
            _constant(ob.animation_data.action)


# ---------------------------------------------------------------- B-036: surface walkers

def _glass(name):
    """Black volcanic glass: near-black, glossy (the harsh orange light glints off it)."""
    return flat_material(name, (26, 22, 26), metallic=0.1, rough=0.14)


def _rigid_on_bone(ob, rig, bone, coll):
    _link(coll, ob)
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = bone
    bpy.context.view_layer.update()
    ob.matrix_world = mw


def _ellipsoid(name, loc, scale, mat, coll, rig, bone, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat)
    _rigid_on_bone(ob, rig, bone, coll)
    return ob


def _capsules_mesh(name, coll, chains, res):
    """chains: lists of (x, y, z, r) points; consecutive points become metaball capsules."""
    mb = bpy.data.metaballs.new(f"{name}_mb")
    mb.resolution = mb.render_resolution = res
    mb.threshold = 0.6
    for pts in chains:
        for (x0, y0, z0, r0), (x1, y1, z1, r1) in zip(pts, pts[1:]):
            d = Vector((x1 - x0, y1 - y0, z1 - z0))
            e = mb.elements.new(type="CAPSULE")
            e.co = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
            e.radius = 1.35 * (r0 + r1) / 2
            e.size_x = d.length / 2
            e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())
    ob = bpy.data.objects.new(name, mb)
    coll.objects.link(ob)
    _select_only(ob)
    bpy.ops.object.convert(target="MESH")
    me = bpy.context.view_layer.objects.active
    me.name = name
    for p in me.data.polygons:
        p.use_smooth = True
    return me


def build_pressure_crab(scene):
    """Armored, slow surface crab (ground pivot). Exaggeration: a heavy carapace of three
    overlapping black-glass plates over an emissive orange under-body, so the glow shows only
    in the seams. Six legs (near/far, far ones darker) and two claws on an armature; legs are
    metaball capsules bound with automatic weights; plates, claws and eye stalks are rigid."""
    sp = "pressure_crab"
    coll = bpy.data.collections.new(sp)
    scene.collection.children.link(coll)
    zb = 0.34                                                               # B-034: lower, flatter
    ad = bpy.data.armatures.new(f"{sp}_rig")
    rig = bpy.data.objects.new(f"{sp}_rig", ad)
    coll.objects.link(rig)
    _select_only(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = ad.edit_bones
    body = eb.new("body"); body.head, body.tail = Vector((-0.2, 0, zb)), Vector((0.2, 0, zb))
    legs = {}
    for sy in (-1, 1):
        for k, (x, dx) in enumerate(((0.36, 0.34), (0.05, 0.12), (-0.3, -0.34))):   # B-034: splayed fore/aft
            tag = f"{k}{'n' if sy < 0 else 'f'}"
            p0 = Vector((x, sy * 0.3, zb - 0.05))
            p1 = Vector((x + dx, sy * 0.42, zb + 0.2))                      # knee arched high
            p2 = Vector((x + 2.4 * dx, sy * 0.48, 0.0))                     # foot far out
            a = eb.new(f"fem_{tag}"); a.head, a.tail = p0, p1; a.parent = body
            b = eb.new(f"tib_{tag}"); b.head, b.tail = p1, p2; b.parent = a
            legs[tag] = (p0, p1, p2)
    for sy in (-1, 1):
        tag = "n" if sy < 0 else "f"
        a = eb.new(f"arm_{tag}"); a.head, a.tail = Vector((0.5, sy * 0.24, zb)), Vector((0.78, sy * 0.28, zb + 0.04))   # held forward
        a.parent = body
    bpy.ops.object.mode_set(mode="OBJECT")
    # Legs: metaball capsules -> one mesh -> automatic weights.
    # Leg radii x1.5 after review: stick-thin legs vanished at 60 px/m.
    chains = [[(p.x, p.y, p.z, r) for p, r in zip(pts, (0.085, 0.07, 0.035))] for pts in legs.values()]
    chains += [[(0.46, sy * 0.24, zb, 0.08), (0.78, sy * 0.28, zb + 0.04, 0.07)] for sy in (-1, 1)]
    legm = _capsules_mesh(f"{sp}_legs", coll, chains, 0.012)
    legm.data.materials.append(_glass(f"{sp}_leg"))
    bind_auto(legm, rig)
    glass = _glass(f"{sp}_shell")
    glow = flat_material(f"{sp}_glow", (120, 40, 10), emit=(255, 120, 40), strength=1.6)
    _ellipsoid(f"{sp}_core", (0.0, 0, zb + 0.02), (0.82, 0.48, 0.17), glow, coll, rig, "body")
    for k, (x, z, s) in enumerate(((-0.42, zb + 0.04, 0.95), (0.0, zb + 0.07, 1.05), (0.42, zb + 0.05, 1.0))):
        _ellipsoid(f"{sp}_plate{k}", (x, 0, z), (0.42 * s, 0.54 * s, 0.18 * s), glass, coll, rig, "body")   # wide, flat
    for sy in (-1, 1):                                                       # claws: heavy pincers
        tag = "n" if sy < 0 else "f"
        _ellipsoid(f"{sp}_claw_{tag}", (0.96, sy * 0.28, zb + 0.06), (0.24, 0.11, 0.12), glass, coll, rig, f"arm_{tag}", 24)   # heavy pincer, forward
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.07, radius2=0.0, depth=0.22,
                                        location=(1.18, sy * 0.28, zb + 0.1), rotation=(0, math.pi / 2 - 0.15, 0))
        tip = bpy.context.active_object
        tip.data.materials.append(glass)
        _rigid_on_bone(tip, rig, f"arm_{tag}", coll)
    eye = flat_material(f"{sp}_eye", (80, 30, 10), emit=(255, 150, 60), strength=2.0)
    for sy in (-1, 1):                                                       # eyes on stalks
        _ellipsoid(f"{sp}_stalk{sy}", (0.5, sy * 0.1, zb + 0.18), (0.018, 0.018, 0.08), glass, coll, rig, "body", 12)
        _ellipsoid(f"{sp}_eye{sy}", (0.5, sy * 0.1, zb + 0.27), (0.03, 0.03, 0.03), eye, coll, rig, "body", 12)
    tags = list(legs)
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        pose = {b.name: 0.0 for b in rig.pose.bones}
        pitch = 0.0
        if name == "idle":
            for tg in tags:
                pose[f"fem_{tg}"] = 2 * math.sin(2 * math.pi * t)
        elif name == "walk":
            for j, tg in enumerate(tags):
                ph = 0.0 if (int(tg[0]) + (tg[1] == "f")) % 2 == 0 else 0.5    # alternating tripods
                u = 2 * math.pi * (t + ph)
                pose[f"fem_{tg}"] = 12 * math.sin(u)
                pose[f"tib_{tg}"] = -14 * max(0.0, math.cos(u))               # lift the swinging feet
        elif name == "attack":
            k = [0.2, 0.7, 1.0, 0.4, 0.1, 0.0][i]
            pitch = -5 * k
            for tag in ("n", "f"):
                pose[f"arm_{tag}"] = -38 * k if i < 3 else 25 * (1 - i / 6)   # raise, then snap down
        elif name == "hurt":
            pitch = 8 * (1.0 if i == 0 else 0.5)
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            pitch = 6 * k
            for tg in tags:
                pose[f"fem_{tg}"] = (-25 if tg[0] == "0" else 25 if tg[0] == "2" else 0) * k   # legs splay
                pose[f"tib_{tg}"] = 20 * k
            for tag in ("n", "f"):
                pose[f"arm_{tag}"] = 20 * k
        rig.rotation_euler = (0, math.radians(pitch), 0)
        rig.keyframe_insert("rotation_euler", frame=f)
        for bn, deg in pose.items():
            set_pose(rig, bn, deg)
            rig.pose.bones[bn].keyframe_insert("rotation_quaternion", frame=f)
    if rig.animation_data and rig.animation_data.action:
        _constant(rig.animation_data.action)
    ground_exactly(rig)


def build_vent_eel(scene):
    """Heat-seeking surface eel (ground pivot): sleek 10-segment black-glass body on a bone
    chain (metaball, automatic weights), a wedge head; exaggeration = a row of glowing orange
    heat pits along each side plus a glowing mouth (emission). Low undulation, head raised and
    sweeping for heat, lunge attack, limp death."""
    sp = "vent_eel"
    coll = bpy.data.collections.new(sp)
    scene.collection.children.link(coll)
    n = 10
    x0, x1 = -1.1, 1.1
    seg = (x1 - x0) / n
    zc = 0.15
    ad = bpy.data.armatures.new(f"{sp}_rig")
    rig = bpy.data.objects.new(f"{sp}_rig", ad)
    coll.objects.link(rig)
    _select_only(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    prev = None
    for k in range(n):
        b = ad.edit_bones.new(f"s{k}")
        b.head, b.tail = Vector((x0 + k * seg, 0, zc)), Vector((x0 + (k + 1) * seg, 0, zc))
        if prev:
            b.parent = prev
            b.use_connect = True
        prev = b
    bpy.ops.object.mode_set(mode="OBJECT")
    radius = [0.04, 0.065, 0.09, 0.105, 0.12, 0.13, 0.135, 0.135, 0.13, 0.12]   # x1.6: 6 px tall at 60 px/m was too thin
    pts = [(x0 + k * seg, 0, zc, radius[min(k, n - 1)]) for k in range(n)] + [(x1 + 0.05, 0, zc - 0.01, 0.04)]
    body = _capsules_mesh(f"{sp}_body", coll, [pts], 0.008)
    body.data.materials.append(_glass(f"{sp}_skin"))
    bind_auto(body, rig)
    pit = flat_material(f"{sp}_pit", (120, 40, 10), emit=(255, 130, 40), strength=2.0)
    for k in range(2, n):                                                    # heat pits along both sides
        for sy in (-1, 1):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.018,
                                                 location=(x0 + (k + 0.5) * seg, sy * radius[k] * 1.3, zc + 0.01))
            _rig_child(bpy.context.active_object, rig, f"s{k}", coll, pit)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.03, location=(x1 + 0.08, 0, zc - 0.02))
    _rig_child(bpy.context.active_object, rig, f"s{n - 1}", coll, pit)        # glowing mouth
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        A = 5.0
        lift = [0.0] * n
        sweep = 0.0
        if name == "idle":
            A, sweep = 2.0, 10 * math.sin(2 * math.pi * t)                   # head sweeps for heat
            lift[n - 2], lift[n - 1] = -10.0, -8.0
        elif name == "walk":
            lift[n - 1] = -6.0
        elif name == "attack":
            k = [0.3, 0.8, 1.0, 0.5, 0.2, 0.0][i]
            A = 1.5
            lift[n - 3], lift[n - 2], lift[n - 1] = -18 * k, -16 * k, (14 if i == 2 else -10) * k   # rear, lunge
        elif name == "hurt":
            lift[n - 1] = 12.0 * (1.0 if i == 0 else 0.5)
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            A = 5.0 * (1 - k)
        prev_abs = 0.0
        for j in range(n):
            ab = A * math.sin(2 * math.pi * (t - j * 0.2)) + lift[j] + (sweep if j == n - 1 else 0.0)
            set_pose(rig, f"s{j}", ab - prev_abs if j else ab)
            prev_abs = ab
        for pb in rig.pose.bones:
            pb.keyframe_insert("rotation_quaternion", frame=f)
    if rig.animation_data and rig.animation_data.action:
        _constant(rig.animation_data.action)
    ground_exactly(rig)


# ---------------------------------------------------------------- B-044: Veil Serpent (apex)

def membrane_material(name):
    """Translucent fin membrane (alpha 0.5): pale sulfur cream; the glow lives only in a vein
    network (Voronoi edges -> emission), not in an outline (B-044 v2 review)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    pr.inputs["Alpha"].default_value = 0.5
    pr.inputs["Roughness"].default_value = 0.4
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"
    vo.inputs["Scale"].default_value = 9.0
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    v = N.new("ShaderNodeMapRange"); v.interpolation_type = "SMOOTHSTEP"
    v.inputs["From Min"].default_value, v.inputs["From Max"].default_value = 0.04, 0.0
    L.new(vo.outputs["Distance"], v.inputs["Value"])
    col = N.new("ShaderNodeMix"); col.data_type = "RGBA"
    L.new(v.outputs["Result"], col.inputs[0])
    col.inputs[6].default_value = lin((214, 190, 120)); col.inputs[7].default_value = lin((255, 226, 110))
    L.new(col.outputs[2], pr.inputs["Base Color"])
    em = N.new("ShaderNodeMix"); em.data_type = "RGBA"
    L.new(v.outputs["Result"], em.inputs[0])
    em.inputs[6].default_value = (0, 0, 0, 1); em.inputs[7].default_value = lin((255, 214, 80))
    L.new(em.outputs[2], pr.inputs["Emission Color"])
    pr.inputs["Emission Strength"].default_value = 2.2
    return m


def serpent_skin(name):
    """Body: dark dorsal bands over sulfur-umber, pale belly; masks from the 'ser' colour
    attribute (R belly, G band), painted from the rest pose so they ride the deformation."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    pr.inputs["Roughness"].default_value = 0.35
    at = N.new("ShaderNodeAttribute"); at.attribute_name = "ser"
    sep = N.new("ShaderNodeSeparateColor")
    L.new(at.outputs["Color"], sep.inputs[0])
    a = N.new("ShaderNodeMix"); a.data_type = "RGBA"
    L.new(sep.outputs[1], a.inputs[0])
    a.inputs[6].default_value = lin((168, 128, 70)); a.inputs[7].default_value = lin((70, 50, 34))
    b = N.new("ShaderNodeMix"); b.data_type = "RGBA"
    L.new(sep.outputs[0], b.inputs[0])
    L.new(a.outputs[2], b.inputs[6]); b.inputs[7].default_value = lin((232, 214, 170))
    L.new(b.outputs[2], pr.inputs["Base Color"])
    return m


def build_veil_serpent(scene):
    """Venus apex (B-044 v2). 14-bone chain; metaball body thick in the front third tapering
    to a whip tail, banded back and pale belly; a wedge skull with jaw, glowing eyes and
    backswept horns; a tall dorsal sail (7 rays, translucent veined membrane, ragged edge)
    and a smaller ventral fin, both weighted to the chain; frost shell for the chilled hurt.
    Flier: centred pivot, no grounding."""
    import random as _r
    rnd = _r.Random(44002)
    sp = "veil_serpent"
    coll = bpy.data.collections.new(sp)
    scene.collection.children.link(coll)
    n = 14
    x0, x1 = -1.65, 1.45
    seg = (x1 - x0) / n
    ad = bpy.data.armatures.new(f"{sp}_rig")
    rig = bpy.data.objects.new(f"{sp}_rig", ad)
    coll.objects.link(rig)
    _select_only(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    prev = None
    for k in range(n):
        b = ad.edit_bones.new(f"s{k}")
        b.head, b.tail = Vector((x0 + k * seg, 0, 0)), Vector((x0 + (k + 1) * seg, 0, 0))
        if prev:
            b.parent = prev
            b.use_connect = True
        prev = b
    bpy.ops.object.mode_set(mode="OBJECT")

    def rad(t):                                       # thick front third, whip tail, slight neck
        return 0.03 + 0.17 * min(1.0, t / 0.68) ** 0.9 - 0.04 * max(0.0, (t - 0.85) / 0.15)
    radius = [rad(k / (n - 1)) for k in range(n)]
    pts = [(x0 + k * seg, 0, 0, radius[k]) for k in range(n)]
    body = _capsules_mesh(f"{sp}_body", coll, [pts], 0.009)
    me = body.data
    attr = me.color_attributes.new("ser", "FLOAT_COLOR", "POINT")
    for k, v in enumerate(me.vertices):
        x, y, z = v.co
        t = (x - x0) / (x1 - x0)
        r = max(rad(min(max(t, 0), 1)), 0.02)
        belly = min(1.0, max(0.0, (-z / r - 0.15) / 0.3))
        band = (1.0 if math.sin(x * 15.0) > 0.25 else 0.0) * min(1.0, max(0.0, (z / r + 0.1) / 0.3))
        attr.data[k].color = (belly, band, 0.0, 1.0)
    me.materials.append(serpent_skin(f"{sp}_skin"))
    bind_auto(body, rig)
    # Frost shell: a copy of the body; Displace keyed inside (-0.03) except the hurt frames.
    frost = body.copy()
    frost.data = body.data.copy()
    frost.name = f"{sp}_frost"
    coll.objects.link(frost)
    frost.data.materials.clear()
    fm = flat_material(f"{sp}_frost", (236, 246, 255), emit=(214, 236, 255), strength=1.6, rough=0.2)
    fm.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.85
    frost.data.materials.append(fm)
    dsp = frost.modifiers.new("inflate", "DISPLACE")
    dsp.mid_level = 0.0
    # Fins: membrane with a ragged top edge + rays (darker opaque spines past the edge).
    memb = membrane_material(f"{sp}_membrane")
    raym = flat_material(f"{sp}_ray", (90, 64, 40), rough=0.4)

    def fin(tag, t0, t1, sz, hmax, nrays):
        verts, faces = [], []
        m_ = 60
        top = []
        for i in range(m_ + 1):
            u = i / m_
            t = t0 + (t1 - t0) * u
            x = x0 + (x1 - x0) * t
            r = rad(t)
            h = hmax * math.sin(math.pi * u) ** 0.6 * (0.8 + 0.2 * math.sin(u * 7.3)) + rnd.uniform(-0.03, 0.02)
            h = max(h, 0.02)
            verts += [(x, 0, sz * r * 0.6), (x, 0, sz * (r + h))]
            top.append((x, r, h))
            if i:
                a = 2 * i
                faces.append((a - 2, a, a + 1, a - 1))
        mesh = bpy.data.meshes.new(f"{sp}_{tag}")
        mesh.from_pydata(verts, [], faces)
        ob = bpy.data.objects.new(f"{sp}_{tag}", mesh)
        coll.objects.link(ob)
        ob.modifiers.new("solid", "SOLIDIFY").thickness = 0.006
        ob.data.materials.append(memb)
        bind_auto(ob, rig)
        rv, rf = [], []
        for k in range(nrays):                          # rays: thin quads leaning back, past the edge
            i = int((k + 0.5) / nrays * m_)
            x, r, h = top[i]
            ext = h * 1.04 + 0.01                                   # just past the edge
            lean = -0.35 * ext
            b0 = len(rv)
            rv += [(x - 0.022, 0, sz * r * 0.6), (x + 0.022, 0, sz * r * 0.6),
                   (x + lean + 0.009, 0, sz * (r + ext)), (x + lean - 0.009, 0, sz * (r + ext))]
            rf.append((b0, b0 + 1, b0 + 2, b0 + 3))
        rmesh = bpy.data.meshes.new(f"{sp}_{tag}_rays")
        rmesh.from_pydata(rv, [], rf)
        ro = bpy.data.objects.new(f"{sp}_{tag}_rays", rmesh)
        coll.objects.link(ro)
        ro.modifiers.new("solid", "SOLIDIFY").thickness = 0.012
        ro.data.materials.append(raym)
        bind_auto(ro, rig)
    fin("sail", 0.3, 0.86, 1, 0.42, 7)                  # tall dorsal sail, front two-thirds
    fin("ventral", 0.16, 0.46, -1, 0.26, 4)             # smaller ventral fin, further back
    # Head: wedge skull, jaw, eyes, backswept horns (rigid on the last bone), ~2x body thickness.
    hb = f"s{n - 1}"
    hx = x1
    hide = flat_material(f"{sp}_skull", (92, 68, 44), rough=0.35)
    horn = flat_material(f"{sp}_horn", (214, 196, 160), rough=0.4)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=(0, 0, 0))
    sk = bpy.context.active_object
    sk.name = f"{sp}_skull"
    for v in sk.data.vertices:                          # wedge: tapers to the snout (+x)
        tt = min(1.0, max(0.0, (v.co.x + 1) / 2))
        v.co.y *= 1.0 - 0.55 * tt
        v.co.z *= 1.0 - 0.45 * tt
    sk.location = (hx + 0.14, 0, 0.06)
    sk.scale = (0.36, 0.22, 0.26)                                    # ~2x the neck thickness
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    _rig_child(sk, rig, hb, coll, hide)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=(hx + 0.16, 0, -0.13))
    jaw = bpy.context.active_object
    jaw.scale = (0.3, 0.16, 0.08)
    jaw.rotation_euler = (0, math.radians(8), 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    _rig_child(jaw, rig, hb, coll, flat_material(f"{sp}_jaw", (210, 190, 146), rough=0.4))
    eye = flat_material(f"{sp}_eye", (120, 60, 10), emit=(255, 200, 80), strength=2.6)
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.032, location=(hx + 0.24, sy * 0.13, 0.12))
        _rig_child(bpy.context.active_object, rig, hb, coll, eye)
        for j, (dz, ln) in enumerate(((0.12, 0.34), (0.05, 0.24))):   # backswept horns
            bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.035, radius2=0.0, depth=ln,
                                            location=(hx - 0.04 - ln * 0.4, sy * 0.1, dz + 0.06 + ln * 0.18),
                                            rotation=(0, math.radians(-112 + 14 * j), 0))
            _rig_child(bpy.context.active_object, rig, hb, coll, horn)
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        A, lam, lift, chill = 35.0, 0.07, 0.0, False
        head = [0.0] * n
        if name == "idle":
            A = 28.0
        elif name == "walk":
            A, lam = 38.0, 0.07
        elif name == "attack":
            k = [0.2, 0.6, 1.0, 0.7, 0.3, 0.1][i]
            A = 18.0
            head[n - 3], head[n - 2], head[n - 1] = -22 * k, -18 * k, (26 if i == 3 else -12) * k
        elif name == "hurt":
            A, chill = 6.0, True
            head[n - 1] = 18.0 * (1.0 if i == 0 else 0.5)
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            A, lift = 35.0 * (1 - k), 30 * k
        rig.rotation_euler = (0, math.radians(lift), 0)
        rig.keyframe_insert("rotation_euler", frame=f)
        prev_abs = 0.0
        for j in range(n):
            ab = A * math.sin(2 * math.pi * (t - j * lam)) + head[j]
            set_pose(rig, f"s{j}", ab - prev_abs if j else ab)
            prev_abs = ab
        for pb in rig.pose.bones:
            pb.keyframe_insert("rotation_quaternion", frame=f)
        dsp.strength = 0.018 if chill else -0.03
        dsp.keyframe_insert("strength", frame=f)
    for ob in (rig, frost):
        if ob.animation_data and ob.animation_data.action:
            _constant(ob.animation_data.action)


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    build_drifter(scene)
    build_moth(scene)
    build_pressure_crab(scene)
    build_vent_eel(scene)
    build_veil_serpent(scene)
    scene.frame_start = 1
    scene.frame_end = max(CLIP_START[c] + CLIP_LEN[c] - 1 for c in CLIP_ORDER)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
