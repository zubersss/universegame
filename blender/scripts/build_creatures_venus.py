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
from build_creatures_earth import CLIP_LEN, CLIP_ORDER, CLIP_START, bind_auto, set_pose  # noqa: E402
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


def frames():
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

    for name, i, f in frames():
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

    for name, i, f in frames():
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


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    build_drifter(scene)
    build_moth(scene)
    scene.frame_start = 1
    scene.frame_end = max(CLIP_START[c] + CLIP_LEN[c] - 1 for c in CLIP_ORDER)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
