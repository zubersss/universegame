"""Builds blender/sources/creatures/mercury.blend: Mercury creatures, glassback and cinderling (B-029).

The creature standard (B-015 v3): skeleton -> metaball body -> one mesh bound to the armature
with automatic weights, rest-pose marking masks, same clip set. Bible §7.3 / §9: grounded
anatomy, ONE bold exaggeration each, readable at 60 px/m; materials match Mercury (silicate
glass, basalt). Airless, so no external ears.
  * glassback (1.7 m silicate grazer riding the twilight band): stocky, low-carried grazing
    head; exaggeration = clusters of crystalline glass shards along the back.
  * cinderling (0.5 m, swarms at dawn): small, round, short-legged, basalt-dark hide;
    exaggeration = glowing orange cracks (emission map).

  blender --background --factory-startup --python blender/scripts/build_creatures_mercury.py
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_creatures_earth import (CLIP_LEN, CLIP_ORDER, CLIP_START, _rig_child, bind_auto,  # noqa: E402
                                   build as build_species_set, ground_exactly, set_pose)
from build_pilgrim import flat_material, lin  # noqa: E402
from build_surveyor import _constant  # noqa: E402
from build_icons import mat  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "creatures", "mercury.blend")


def glass_shards(sp, S, rig, coll):
    """Clusters of 3-4 faceted glass shards along the back, leaning tail-ward and outward so
    the ridge reads as crystal (tall, sharp, pale) against black sky and grey regolith."""
    m = mat(f"{sp}_glass", (226, 222, 242), (182, 176, 214), 0, 0.12, 10, 0.15)
    rnd = random.Random(29001)
    spine = S["spine"]
    xs = [0.42, 0.22, 0.0, -0.22, -0.42]
    k = 0
    for ci, x in enumerate(xs):
        _, zc, r = min(spine, key=lambda p: abs(p[0] - x))
        tall = 0.42 - 0.08 * abs(ci - 2)                  # tallest mid-back
        for j in range(4 if ci in (1, 2, 3) else 3):
            h = tall * rnd.uniform(0.55, 1.0)
            dx = rnd.uniform(-0.07, 0.07)
            dy = rnd.uniform(-0.06, 0.06)
            bpy.ops.mesh.primitive_cone_add(vertices=5, radius1=h * 0.2, radius2=0.0, depth=h,
                                            location=(x + dx, dy, zc + r * 0.75 + h * 0.42))
            ob = bpy.context.active_object
            ob.name = f"{sp}_shard{k}"
            ob.rotation_euler = (math.radians(rnd.uniform(-14, 14) + 12 * math.copysign(1, dy)),
                                 math.radians(-rnd.uniform(8, 30)), rnd.uniform(0, 6.28))
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            _rig_child(ob, rig, "body", coll, m)
            bpy.ops.object.shade_flat()                    # crisp facets
            k += 1


def cinder_plate_material(name, state):
    """Cinderhulk shell (B-040). day: white-hot plates (strong white emission). night: cooled
    charcoal plates cracked with glowing orange fracture lines (Voronoi edges -> emission)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    pr.inputs["Roughness"].default_value = 0.5
    tc = N.new("ShaderNodeTexCoord")
    if state == "day":
        # White-hot plates, each a slightly different tone (white -> pale gold by cell), with
        # thin amber seams between them: a plain white albedo read as a flat blob (review).
        cells = N.new("ShaderNodeTexVoronoi"); cells.inputs["Scale"].default_value = 5.0
        L.new(tc.outputs["Object"], cells.inputs["Vector"])
        tone = N.new("ShaderNodeValToRGB")
        tone.color_ramp.elements[0].color = lin((255, 250, 236))
        tone.color_ramp.elements[1].color = lin((246, 214, 150))
        L.new(cells.outputs["Color"], tone.inputs["Fac"])
        edge = N.new("ShaderNodeTexVoronoi"); edge.feature = "DISTANCE_TO_EDGE"
        edge.inputs["Scale"].default_value = 5.0
        L.new(tc.outputs["Object"], edge.inputs["Vector"])
        sm = N.new("ShaderNodeMapRange"); sm.interpolation_type = "SMOOTHSTEP"
        sm.inputs["From Min"].default_value, sm.inputs["From Max"].default_value = 0.08, 0.02
        L.new(edge.outputs["Distance"], sm.inputs["Value"])
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
        L.new(sm.outputs["Result"], mx.inputs[0])
        L.new(tone.outputs["Color"], mx.inputs[6]); mx.inputs[7].default_value = lin((120, 56, 24))
        L.new(mx.outputs[2], pr.inputs["Base Color"])
        L.new(tone.outputs["Color"], pr.inputs["Emission Color"])
        inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
        L.new(sm.outputs["Result"], inv.inputs[1])
        st = N.new("ShaderNodeMath"); st.operation = "MULTIPLY"; st.inputs[1].default_value = 0.8
        L.new(inv.outputs[0], st.inputs[0])
        L.new(st.outputs[0], pr.inputs["Emission Strength"])               # seams stay dark
        return m
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"
    vo.inputs["Scale"].default_value = 5.0
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.05, 0.0
    L.new(vo.outputs["Distance"], mr.inputs["Value"])
    col = N.new("ShaderNodeMix"); col.data_type = "RGBA"
    L.new(mr.outputs["Result"], col.inputs[0])
    col.inputs[6].default_value = lin((44, 40, 42)); col.inputs[7].default_value = lin((255, 120, 40))
    L.new(col.outputs[2], pr.inputs["Base Color"])
    em = N.new("ShaderNodeMix"); em.data_type = "RGBA"
    L.new(mr.outputs["Result"], em.inputs[0])
    em.inputs[6].default_value = (0, 0, 0, 1); em.inputs[7].default_value = lin((255, 120, 40))
    L.new(em.outputs[2], pr.inputs["Emission Color"])
    pr.inputs["Emission Strength"].default_value = 2.4
    return m


def cinder_plates(sp, S, rig, coll):
    """Cinderhulk armour and anatomy (B-040 v2, LEAD review): domed carapace whose lower edge
    is a ring of irregular overhanging plates (no straight cut line), crest plates; a heavy
    head with jaw, brow ridge and tusks (dark hide, not shell); splayed claws on every foot;
    a bony mace with spikes on the tapering tail (its own bone material)."""
    import random as _r
    rnd = _r.Random(40002)
    m = cinder_plate_material(f"{sp}_shell", S["state"])
    hide = flat_material(f"{sp}_hide", (52, 46, 46), rough=0.6)
    bone = flat_material(f"{sp}_bone", (196, 180, 156), rough=0.45)
    spine = S["spine"]

    def blob(name, loc, scale, rot, bone_name, mat, seg=24):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=1.0, location=loc)
        ob = bpy.context.active_object
        ob.name = name
        ob.scale = scale
        ob.rotation_euler = rot
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        _rig_child(ob, rig, bone_name, coll, mat)
        return ob

    def spike(name, loc, rot, r, depth, bone_name, mat):
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=r, radius2=0.0, depth=depth, location=loc, rotation=rot)
        ob = bpy.context.active_object
        ob.name = name
        _rig_child(ob, rig, bone_name, coll, mat)
        bpy.ops.object.shade_flat()

    # Carapace dome (cut below), then a ring of overhanging rim plates hides the cut.
    x0, x1 = spine[0][0], spine[-1][0]
    rmax = max(q[2] for q in spine) * 1.35
    zc = max(q[1] for q in spine)
    cx, ax, ay = (x0 + x1) / 2, (x1 - x0) / 2 + rmax * 0.55, rmax * 1.1
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0, location=(0, 0, 0))
    dome = bpy.context.active_object
    dome.name = f"{sp}_dome"
    bm = bmesh.new()
    bm.from_mesh(dome.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.2], context="VERTS")
    bm.to_mesh(dome.data)
    bm.free()
    zb = zc - rmax * 0.08                                        # seat on the back: legs stay visible
    dome.location = (cx, 0, zb)
    dome.scale = (ax, ay, rmax * 0.8)                                 # lower, wider (read as a tortoise)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    _rig_child(dome, rig, "body", coll, m)
    n = 16
    for k in range(n):
        a = 2 * math.pi * (k + rnd.uniform(-0.2, 0.2)) / n
        rx, ry = math.cos(a) * ax * 1.02, math.sin(a) * ay * 1.02
        drop = rnd.uniform(0.12, 0.3)                               # irregular overhang depth
        # Thin shingle: tangent x, radial y (thin), vertical z; leaning out over the flank.
        blob(f"{sp}_rim{k}", (cx + rx, ry, zb - rmax * 0.12 - drop * 0.4),
             (rnd.uniform(0.24, 0.34), 0.05, 0.16 + drop * 0.6),
             (math.radians(-22 + rnd.uniform(-6, 6)), 0, a + math.pi / 2), "body", m, seg=16)
    top = zb + rmax * 0.8
    xs = [x0 + 0.15 + (x1 - x0 - 0.3) * k / 4 for k in range(5)]
    for k, x in enumerate(xs):                                      # crest plates
        blob(f"{sp}_crest{k}", (x, 0, top - 0.06), (0.3, 0.34, 0.17), (0, math.radians(-14), 0), "body", m)
    # Head: heavy lower jaw, brow ridge over the eyes, two tusks (hide/bone, not shell).
    h = S["head"]
    hx0, hz0 = h[0][0], h[0][1]
    hx1, hz1 = h[-1][0], h[-1][1]
    # Outside the grown metaball surface (head radius ~0.36 at the back, 0.2 at the snout).
    blob(f"{sp}_jaw", (hx1 - 0.16, 0, (hz0 + hz1) / 2 - 0.3), (0.42, 0.26, 0.14),
         (0, math.radians(10), 0), "head", hide)
    blob(f"{sp}_brow", (hx0 + 0.24, 0, hz0 + 0.3), (0.26, 0.32, 0.1), (0, math.radians(-12), 0), "head", m)
    for sy in (-1, 1):
        spike(f"{sp}_tusk{sy}", (hx1 + 0.02, sy * 0.15, hz1 - 0.24), (0, math.radians(-25), 0), 0.05, 0.3, "head", bone)
    # Claws: three splayed per foot on the lower leg bone.
    for leg in ("fn", "ff", "hn", "hf"):
        pts = S["front"] if leg[0] == "f" else S["hind"]
        fx = pts[-1][0]
        y = (-1 if leg[1] == "n" else 1) * S["leg_y"]
        for j, (dx, dy) in enumerate(((0.32, 0.0), (0.26, 0.13), (0.26, -0.13))):
            spike(f"{sp}_claw_{leg}{j}", (fx + dx, y + dy, 0.05), (0, math.radians(100), math.atan2(dy, dx)),
                  0.055, 0.26, f"l_{leg}", bone)
    # Tail mace: bony ball with spikes on the tapering tail tip.
    tx, tz, _ = S["tail"][-1]
    blob(f"{sp}_mace", (tx - 0.05, 0, tz), (0.2, 0.18, 0.18), (0, 0, 0), "tail", bone)
    for j, (a, e) in enumerate(((0, 0.6), (1.6, 0.4), (3.1, 0.8), (4.7, 0.3), (2.2, -0.5), (5.3, -0.4))):
        d = (math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e))
        loc = (tx - 0.05 + d[0] * 0.2, d[1] * 0.18, tz + d[2] * 0.18)
        rot = Vector((0, 0, 1)).rotation_difference(Vector(d)).to_euler()
        spike(f"{sp}_macespike{j}", loc, rot, 0.04, 0.14, "tail", bone)

SPECIES = {
    "glassback": dict(
        spine=[(-0.6, 0.74, 0.2), (-0.35, 0.78, 0.26), (0.0, 0.8, 0.28), (0.3, 0.78, 0.26), (0.5, 0.74, 0.21)],
        neck=[(0.5, 0.74, 0.18), (0.64, 0.7, 0.14), (0.76, 0.66, 0.12)],             # head carried low: grazer
        head=[(0.76, 0.66, 0.12), (0.9, 0.6, 0.1), (1.02, 0.52, 0.07), (1.08, 0.48, 0.05)],
        tail=[(-0.6, 0.74, 0.1), (-0.78, 0.66, 0.07), (-0.9, 0.58, 0.045), (-0.96, 0.54, 0.025)],
        front=[(0.36, 0.6, 0.12), (0.36, 0.42, 0.09), (0.37, 0.22, 0.06), (0.37, 0.07, 0.05), (0.41, 0.0, 0.055)],
        hind=[(-0.4, 0.62, 0.14), (-0.3, 0.4, 0.1), (-0.44, 0.22, 0.06), (-0.42, 0.07, 0.05), (-0.38, 0.0, 0.055)],
        leg_y=0.14, ears=0.0, ruff=0.0, socks_z=0.16,
        belly_z=(0.5, 0.6), far=(0.07, 0.55),
        coat=((150, 146, 150), (116, 112, 118)), belly=(184, 180, 184), socks=(78, 74, 80),
        antler=None, extras=glass_shards),
    "cinderling": dict(
        spine=[(-0.16, 0.2, 0.07), (-0.08, 0.21, 0.085), (0.0, 0.21, 0.09), (0.08, 0.21, 0.085), (0.14, 0.2, 0.07)],
        neck=[(0.14, 0.2, 0.06), (0.18, 0.22, 0.055), (0.21, 0.23, 0.05)],
        head=[(0.21, 0.23, 0.055), (0.26, 0.22, 0.045), (0.3, 0.2, 0.032), (0.32, 0.19, 0.022)],
        tail=[(-0.16, 0.2, 0.04), (-0.22, 0.18, 0.03), (-0.27, 0.15, 0.02), (-0.3, 0.13, 0.014)],
        front=[(0.09, 0.16, 0.04), (0.09, 0.1, 0.03), (0.1, 0.05, 0.024), (0.1, 0.02, 0.02), (0.12, 0.0, 0.022)],
        hind=[(-0.09, 0.16, 0.045), (-0.06, 0.1, 0.032), (-0.1, 0.05, 0.024), (-0.1, 0.02, 0.02), (-0.08, 0.0, 0.022)],
        leg_y=0.05, ears=0.0, ruff=0.0, socks_z=0.04, mb_res=0.007, eye_scale=0.45,
        belly_z=(0.12, 0.16), far=(0.03, 0.14),
        coat=((58, 52, 52), (36, 32, 34)), belly=(74, 64, 60), socks=(30, 26, 28),
        cracks=dict(scale=14.0, width=0.07, color=(255, 128, 36), strength=3.0),
        antler=None),
}


def _cinderhulk(state):
    """Armored colossus (B-040 v2): low, wide stance; heavy head (>= 1/4 body length) carried
    below the dome line; thick legs with a visible elbow/stifle bend; tapering tail."""
    return dict(
        spine=[(-0.95, 1.0, 0.44), (-0.5, 1.08, 0.56), (0.0, 1.1, 0.6), (0.5, 1.05, 0.56), (0.82, 0.95, 0.46)],
        neck=[(0.82, 0.95, 0.4), (1.0, 0.82, 0.36), (1.12, 0.74, 0.34)],
        head=[(1.12, 0.74, 0.36), (1.32, 0.68, 0.32), (1.5, 0.62, 0.26), (1.62, 0.58, 0.2)],
        tail=[(-0.95, 1.0, 0.26), (-1.15, 0.86, 0.19), (-1.24, 0.76, 0.13), (-1.32, 0.71, 0.09)],
        front=[(0.5, 0.8, 0.3), (0.74, 0.5, 0.21), (0.52, 0.22, 0.16), (0.58, 0.07, 0.17), (0.66, 0.0, 0.18)],   # slimmer joints: bends read
        hind=[(-0.58, 0.82, 0.32), (-0.3, 0.5, 0.22), (-0.64, 0.22, 0.16), (-0.58, 0.07, 0.17), (-0.5, 0.0, 0.18)],
        leg_y=0.5, ears=0.0, ruff=0.0, socks_z=0.2, eye_scale=1.4,
        belly_z=(0.6, 0.75), far=(0.25, 0.7),
        coat=((62, 58, 60), (44, 40, 42)), belly=(74, 68, 66), socks=(36, 32, 34),
        antler=None, extras=cinder_plates, state=state)

SPECIES["cinderhulk_day"] = _cinderhulk("day")
SPECIES["cinderhulk_night"] = _cinderhulk("night")


# ---------------------------------------------------------------- B-035: flarewing, shadewyrm

def _select_only(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)


def _relink(ob, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)


def _mb_to_mesh(mb, name, coll):
    ob = bpy.data.objects.new(name, mb)
    coll.objects.link(ob)
    _select_only(ob)
    bpy.ops.object.convert(target="MESH")
    me_ob = bpy.context.view_layer.objects.active
    me_ob.name = name
    for p in me_ob.data.polygons:
        p.use_smooth = True
    return me_ob


def membrane_material(name, base, vein, glow, alpha):
    """Leathery membrane: dark base, Voronoi vein network glowing (emission)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    pr.inputs["Roughness"].default_value = 0.6
    pr.inputs["Alpha"].default_value = alpha
    tc = N.new("ShaderNodeTexCoord")
    vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"
    vo.inputs["Scale"].default_value = 9.0
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.07, 0.0
    L.new(vo.outputs["Distance"], mr.inputs["Value"])
    col = N.new("ShaderNodeMix"); col.data_type = "RGBA"
    L.new(mr.outputs["Result"], col.inputs[0])
    col.inputs[6].default_value = lin(base); col.inputs[7].default_value = lin(vein)
    L.new(col.outputs[2], pr.inputs["Base Color"])
    em = N.new("ShaderNodeMix"); em.data_type = "RGBA"
    L.new(mr.outputs["Result"], em.inputs[0])
    em.inputs[6].default_value = (0, 0, 0, 1); em.inputs[7].default_value = lin(vein)
    L.new(em.outputs[2], pr.inputs["Emission Color"])
    pr.inputs["Emission Strength"].default_value = glow
    return m


def _frames():
    for name in CLIP_ORDER:
        for i in range(CLIP_LEN[name]):
            yield name, i, CLIP_START[name] + i


def flare_material(name):
    """B-034 flare shell: white-hot at the wing root fading to orange and transparent toward
    the tip and edges (a uniform shell read as a flat white cut-out). Driven by the distance
    from the wing root in object space; the emission pass keeps linked strength sockets."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    ln = N.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    L.new(tc.outputs["Object"], ln.inputs[0])
    t = N.new("ShaderNodeMapRange"); t.interpolation_type = "SMOOTHSTEP"
    t.inputs["From Min"].default_value, t.inputs["From Max"].default_value = 0.05, 0.85
    L.new(ln.outputs["Value"], t.inputs["Value"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = lin((255, 248, 226))
    ramp.color_ramp.elements[1].color = lin((255, 140, 50))
    L.new(t.outputs["Result"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], pr.inputs["Base Color"])
    L.new(ramp.outputs["Color"], pr.inputs["Emission Color"])
    inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    L.new(t.outputs["Result"], inv.inputs[1])
    al = N.new("ShaderNodeMath"); al.operation = "MULTIPLY"; al.inputs[1].default_value = 0.8
    L.new(inv.outputs[0], al.inputs[0])
    L.new(al.outputs[0], pr.inputs["Alpha"])
    st = N.new("ShaderNodeMath"); st.operation = "MULTIPLY"; st.inputs[1].default_value = 3.0
    L.new(inv.outputs[0], st.inputs[0])
    L.new(st.outputs[0], pr.inputs["Emission Strength"])
    return m


def build_flarewing(scene):
    """Flier that feeds on flares (centred pivot). Dark light-absorbing body with a forked
    tail; two bat-like membranes with glowing veins (emission). The attack is the 'flare': a
    white-hot overlay copy of each wing is scaled in only on the attack frames (a keyed
    material strength would not survive the emission pass, which reads it once)."""
    sp = "flarewing"
    coll = bpy.data.collections.new(sp)
    scene.collection.children.link(coll)
    root = bpy.data.objects.new(f"{sp}_root", None)
    coll.objects.link(root)
    mb = bpy.data.metaballs.new(f"{sp}_mb")
    mb.resolution = mb.render_resolution = 0.01
    # B-034: body ~2x thicker with a distinct thorax hump (it read stick-thin).
    for typ, co, r, size in (("ELLIPSOID", (0.02, 0, 0.0), 0.22, (1.35, 0.9, 0.85)),     # thorax
                             ("ELLIPSOID", (-0.18, 0, -0.01), 0.15, (1.3, 0.85, 0.8)),  # abdomen
                             ("ELLIPSOID", (0.26, 0, 0.03), 0.12, (1.2, 0.9, 0.9)),     # head
                             ("CAPSULE", (-0.38, 0, -0.01), 0.07, (0.16, 1, 1)),        # tail: capsules overlap
                             ("CAPSULE", (-0.6, 0, 0.0), 0.045, (0.14, 1, 1))):         # (short ones read as dashes)
        e = mb.elements.new(type=typ)
        e.co, e.radius = co, r * 1.35
        e.size_x, e.size_y, e.size_z = size
    body = _mb_to_mesh(mb, f"{sp}_body", coll)
    skin = flat_material(f"{sp}_skin", (30, 26, 28), rough=0.45)
    body.data.materials.append(skin)
    body.parent = root
    for ang in (0.45, -0.45):                                               # forked tail tips
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.035, radius2=0.0, depth=0.2,
                                        location=(-0.74, 0, 0.05 * (1 if ang > 0 else -1)),
                                        rotation=(0, -math.pi / 2 - ang, 0))
        t = bpy.context.active_object
        _relink(t, coll)
        t.data.materials.append(skin)
        t.parent = root
    for sy in (-1, 1):                                                       # eyes: hot points
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.02, location=(0.29, sy * 0.05, 0.05))
        ey = bpy.context.active_object
        _relink(ey, coll)
        ey.data.materials.append(flat_material(f"{sp}_eye", (80, 40, 20), emit=(255, 170, 70), strength=2.0))
        ey.parent = root
    memb = membrane_material(f"{sp}_membrane", (70, 30, 22), (255, 150, 60), 1.5, 0.92)
    hot = flare_material(f"{sp}_flare")
    wings = []
    for sy in (-1, 1):
        # Bat-like membrane in the XY plane: root at the origin, leading edge out to the tip,
        # scalloped trailing edge between finger spars.
        pts = [(0.08, 0.0), (0.16, sy * 0.3), (0.12, sy * 0.85), (-0.05, sy * 0.72), (-0.02, sy * 0.55),
               (-0.2, sy * 0.52), (-0.16, sy * 0.36), (-0.3, sy * 0.24), (-0.18, 0.0)]
        verts = [(0.0, 0.0, 0.0)] + [(x, y, 0.0) for x, y in pts]
        faces = [(0, 1 + k, 2 + k) for k in range(len(pts) - 1)]
        wing = None
        for kind, m, off in (("wing", memb, 0.0), ("hot", hot, 0.0)):
            me = bpy.data.meshes.new(f"{sp}_{kind}_{sy}")
            me.from_pydata([(x, y, z + off) for x, y, z in verts], [], faces)
            w = bpy.data.objects.new(f"{sp}_{kind}_{'far' if sy > 0 else 'near'}", me)
            coll.objects.link(w)
            sol = w.modifiers.new("solid", "SOLIDIFY")
            sol.thickness, sol.offset = (0.004, -1.0) if kind == "wing" else (0.014, 0.0)   # flare shell wraps both faces
            w.data.materials.append(m)
            if kind == "wing":
                w.location = (0.02, sy * 0.06, 0.03)
                w.parent = root
                wing = w
            else:
                w.parent = wing                                              # rides its wing
            wings.append((w, sy, kind))
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        flap = math.sin(2 * math.pi * t * (2 if name == "walk" else 1))
        pitch, z, base, amp, flare = 0.0, 0.0, 50.0, 28.0, False
        if name == "idle":
            z = 0.02 * math.sin(2 * math.pi * t)
        elif name == "walk":
            pitch, amp = -10.0, 32.0
        elif name == "attack":
            k = [0.2, 0.6, 1.0, 1.0, 0.7, 0.3][i]
            pitch, base, amp, flare = -18 * k, 70.0, 12.0, 1 <= i <= 4      # wings flared wide, white-hot
        elif name == "hurt":
            k = [1.0, 0.5][i]
            pitch, base, amp = 14 * k, 35.0, 6.0
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            pitch, z, base, amp = 55 * k, -0.15 * k, 50 + 30 * k, 4.0
        root.location = (0, 0, z)
        root.rotation_euler = (0, math.radians(pitch), 0)
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_euler", frame=f)
        for w, sy, kind in wings:
            if kind == "wing":
                ang = min(85.0, max(22.0, base + amp * flap))                # never edge-on
                w.rotation_euler = (math.radians(ang) * sy, 0, 0)
                w.keyframe_insert("rotation_euler", frame=f)
            else:
                sc = 1.0 if flare else 0.001
                w.scale = (sc, sc, sc)
                w.keyframe_insert("scale", frame=f)
    for ob in [root] + [w for w, _, _ in wings]:
        if ob.animation_data and ob.animation_data.action:
            _constant(ob.animation_data.action)


def build_shadewyrm(scene):
    """Ice burrower of the polar craters (ground pivot): long segmented body on an 8-bone
    chain (metaball capsules -> one mesh -> automatic weights), a pale faintly lit frost
    plate on every segment (the exaggeration; reads in dark craters), cyan eyes. Moves with a
    vertical travelling wave, rears and strikes to attack, goes slack on death."""
    sp = "shadewyrm"
    coll = bpy.data.collections.new(sp)
    scene.collection.children.link(coll)
    n = 8
    x0, x1 = -1.25, 1.25
    seg = (x1 - x0) / n
    zc = 0.17
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
    radius = [0.06, 0.09, 0.12, 0.14, 0.15, 0.15, 0.14, 0.16]              # tail -> head (head bulb)
    mb = bpy.data.metaballs.new(f"{sp}_mb")
    mb.resolution = mb.render_resolution = 0.012
    for k in range(n):
        e = mb.elements.new(type="CAPSULE")
        e.co = (x0 + (k + 0.5) * seg, 0, zc)
        e.radius = 1.35 * radius[k]
        e.size_x = seg / 2
    body = _mb_to_mesh(mb, f"{sp}_body", coll)
    body.data.materials.append(flat_material(f"{sp}_skin", (54, 60, 72), rough=0.55))
    bind_auto(body, rig)
    frost = flat_material(f"{sp}_frost", (214, 228, 242), emit=(150, 190, 255), strength=0.35, rough=0.3)
    for k in range(1, n):                                                    # one plate per segment
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0,
                                              location=(x0 + (k + 0.5) * seg, 0, zc + radius[k] * 0.85))
        pl = bpy.context.active_object
        pl.scale = (seg * 0.62, radius[k] * 1.1, radius[k] * 0.42)
        pl.rotation_euler = (0, math.radians(-18), 0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        _rig_child(pl, rig, f"s{k}", coll, frost)
        bpy.ops.object.shade_flat()
    eye_m = flat_material(f"{sp}_eye", (20, 60, 70), emit=(120, 240, 255), strength=1.6)
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=0.022,
                                             location=(x1 - 0.06, sy * 0.1, zc + 0.06))
        _rig_child(bpy.context.active_object, rig, f"s{n - 1}", coll, eye_m)
    for name, i, f in _frames():
        t = i / CLIP_LEN[name]
        A = 9.0
        rear = [0.0] * n
        if name == "idle":
            A = 3.0
        elif name == "attack":
            k = [0.3, 0.7, 1.0, 0.6, 0.2, 0.0][i]
            A = 2.0
            for j, a in zip(range(n - 3, n), (-14, -22, -18)):               # rear the head up
                rear[j] = a * k if i < 3 else a * 0.4 * k
            if i == 3:                                                       # strike forward-down
                rear[n - 1], rear[n - 2] = 20.0, 6.0
        elif name == "hurt":
            A = 4.0
            rear[n - 1] = 14.0 * (1.0 if i == 0 else 0.5)
        elif name == "death":
            k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
            A = 9.0 * (1 - k)
            rear[0], rear[1] = -16 * k, -10 * k                              # tail curls, body slack
        prev_abs = 0.0
        for j in range(n):
            ab = A * math.sin(2 * math.pi * (t - j * 0.275)) + rear[j]
            set_pose(rig, f"s{j}", ab - prev_abs if j else ab)
            prev_abs = ab
        for pb in rig.pose.bones:
            pb.keyframe_insert("rotation_quaternion", frame=f)
    if rig.animation_data and rig.animation_data.action:
        _constant(rig.animation_data.action)
    ground_exactly(rig)


def build(out_path=DEFAULT_OUT):
    """render.py's stale-source guard calls build(out) with no species: pin the Mercury table,
    then reopen the file and add the non-quadrupeds (B-035)."""
    build_species_set(out_path, SPECIES)
    bpy.ops.wm.open_mainfile(filepath=out_path)
    scene = bpy.context.scene
    build_flarewing(scene)
    build_shadewyrm(scene)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built (+flarewing, shadewyrm)", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
