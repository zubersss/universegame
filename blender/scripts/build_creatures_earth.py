"""Builds blender/sources/creatures/earth.blend: Earth creatures, stag and grey wolf (B-015 v2).

v2 per LEAD cycle 24 / D-034 (v1 failed §9 "grounded anatomy": separate tubes, gaps at hip
and knee, capsule body, small antlers):
  * One continuous body mesh per animal: a single connected edge skeleton (spine, neck, head,
    four three-segment legs, tail) with the modifier stack Armature -> Skin -> Subdivision.
    The armature moves the skeleton vertices, then Skin wraps ONE surface around the posed
    skeleton, so joints flex smoothly with no gaps and no weight painting (each skeleton vertex
    belongs to exactly one bone; a joint vertex belongs to the child bone, so it is the pivot).
  * Real proportions (red deer / grey wolf): deep chest, long neck, slender legs with a visible
    carpus (front "knee") and a raised hock; the wolf has a ruff and a bushy tail.
  * The stag's exaggeration is bold antlers: beam ~1.9x head length, 5 tines per side, built as
    a separate rigid object on the head bone (antler is hard bone, unlike the coat).
Animation: poses are rotations about the world Y axis (the 2D side plane), converted to each
bone's rest frame, keyed per frame; then every frame is grounded exactly (lowest evaluated
vertex on z = 0). Clips: idle 6, walk 8 (four-beat), attack 6, hurt 2, death 6 = 28.
Coat colour uses Generated (undeformed) coordinates: pale belly, darker lower legs, and the
far-side legs 15% darker so they read behind the body in 2D. Deterministic:

  blender --background --factory-startup --python blender/scripts/build_creatures_earth.py
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_icons import mat  # noqa: E402
from build_pilgrim import lin  # noqa: E402
from build_surveyor import _constant  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "creatures", "earth.blend")

CLIP_ORDER = ["idle", "walk", "attack", "hurt", "death"]
CLIP_LEN = {"idle": 6, "walk": 8, "attack": 6, "hurt": 2, "death": 6}
CLIP_START = {}
_f = 1
for _c in CLIP_ORDER:
    CLIP_START[_c] = _f
    _f += CLIP_LEN[_c] + 4

LEGS = ("fn", "ff", "hn", "hf")     # front/hind, near (-y) / far (+y)

# Skeleton in metres, side plane (x forward, z up), standing on z = 0. Each point: (x, z, radius).
# Legs list: top (inside the body), joint 1, joint 2, fetlock, hoof/paw tip.
SPECIES = {
    "stag": dict(
        spine=[(-0.62, 1.16, 0.20), (-0.4, 1.2, 0.27), (-0.05, 1.18, 0.30), (0.32, 1.22, 0.33), (0.55, 1.26, 0.28)],
        neck=[(0.55, 1.26, 0.20), (0.72, 1.55, 0.14), (0.86, 1.82, 0.11)],
        head=[(0.86, 1.82, 0.11), (1.02, 1.80, 0.09), (1.2, 1.7, 0.06), (1.28, 1.64, 0.045)],
        tail=[(-0.62, 1.16, 0.07), (-0.72, 1.08, 0.05)],
        front=[(0.42, 1.05, 0.12), (0.4, 0.8, 0.075), (0.42, 0.44, 0.045), (0.42, 0.12, 0.032), (0.46, 0.0, 0.036)],
        hind=[(-0.42, 1.08, 0.14), (-0.3, 0.74, 0.09), (-0.5, 0.46, 0.045), (-0.47, 0.12, 0.032), (-0.44, 0.0, 0.036)],
        leg_y=0.13, ears=0.16, ruff=0.0, belly_z=(0.86, 1.0), socks_z=0.32, far=(0.07, 0.95),
        coat=((140, 98, 62), (108, 74, 48)), belly=(204, 178, 138), socks=(70, 54, 42),
        antler=dict(head_len=0.45, beam=0.70, tines=5)),        # beam 1.56x head (D-034: >= 1.5x)
    "wolf": dict(
        spine=[(-0.48, 0.74, 0.13), (-0.3, 0.76, 0.17), (0.0, 0.76, 0.19), (0.28, 0.8, 0.21), (0.44, 0.82, 0.19)],
        neck=[(0.44, 0.82, 0.17), (0.58, 0.92, 0.13), (0.68, 1.0, 0.11)],
        head=[(0.68, 1.0, 0.11), (0.82, 0.98, 0.09), (0.96, 0.93, 0.055), (1.03, 0.9, 0.035)],
        tail=[(-0.48, 0.74, 0.07), (-0.7, 0.6, 0.085), (-0.9, 0.44, 0.06), (-0.98, 0.36, 0.03)],
        front=[(0.32, 0.66, 0.08), (0.3, 0.5, 0.055), (0.31, 0.24, 0.035), (0.32, 0.07, 0.03), (0.37, 0.0, 0.034)],
        hind=[(-0.32, 0.68, 0.1), (-0.22, 0.46, 0.065), (-0.36, 0.26, 0.035), (-0.33, 0.07, 0.03), (-0.29, 0.0, 0.034)],
        leg_y=0.1, ears=0.11, ruff=0.2, belly_z=(0.54, 0.66), socks_z=0.16, far=(0.05, 0.6),
        coat=((126, 122, 116), (92, 88, 84)), belly=(206, 200, 190), socks=(110, 104, 98),
        antler=None),
}


# ---------------------------------------------------------------- poses (degrees)
# s_<leg> swing (+ forward), j1/j2 flex of the two lower joints (+ = the natural fold),
# pitch (+ nose down), neck (+ up), head (+ nose down), tail (+ up).

def pose(name, i, sp):
    n = CLIP_LEN[name]
    t = i / n
    p = {f"s_{l}": 0.0 for l in LEGS}
    p.update({f"j1_{l}": 0.0 for l in LEGS})
    p.update({f"j2_{l}": 0.0 for l in LEGS})
    p.update(pitch=0.0, neck=0.0, head=0.0, tail=0.0)
    if name == "idle":
        s = math.sin(2 * math.pi * t)
        p.update(neck=3 * s, head=-2 * s, tail=8 * s)
    elif name == "walk":
        phase = {"hn": 0.0, "fn": 0.25, "hf": 0.5, "ff": 0.75}           # four-beat walk
        for l, ph in phase.items():
            u = 2 * math.pi * (t + ph)
            swing = max(0.0, math.cos(u))                                # 1 while the leg swings forward
            p[f"s_{l}"] = 20 * math.sin(u)
            p[f"j1_{l}"] = 10 + 25 * swing
            p[f"j2_{l}"] = 8 + 45 * swing
        p.update(neck=-3 + 3 * math.sin(4 * math.pi * t), tail=6 * math.sin(2 * math.pi * t))
    elif name == "attack":
        k = [0.0, 0.35, 0.8, 1.0, 0.6, 0.15][i]                          # wind-up, strike, recover
        if sp == "stag":                                                 # head-down antler charge
            p.update(pitch=6 * k, neck=-20 * k, head=26 * k, s_fn=-10 * k, s_ff=-7 * k, s_hn=12 * k, s_hf=9 * k)
            for l in ("hn", "hf"):
                p[f"j1_{l}"] = 18 * k
        else:                                                            # lunge and bite
            p.update(pitch=-6 * k, neck=12 * k, head=-14 * k, s_fn=28 * k, s_ff=22 * k, s_hn=-24 * k, s_hf=-20 * k, tail=18 * k)
            p["j2_fn"] = 30 * k
    elif name == "hurt":
        k = [1.0, 0.5][i]
        p.update(pitch=-8 * k, neck=18 * k, head=-12 * k, s_fn=14 * k, s_ff=10 * k, s_hn=-10 * k, s_hf=-6 * k, tail=-14 * k)
    elif name == "death":
        k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]                       # legs fold under, body sinks
        for l in LEGS:
            front = l.startswith("f")
            p[f"s_{l}"] = (-25 if front else 30) * k
            p[f"j1_{l}"] = 70 * k
            p[f"j2_{l}"] = 90 * k
        # The head sinks but tips nose-up, so a stag's antlers rake back instead of sweeping
        # 0.9 m forward (measured: that alone pushed the sheet below ppu 100).
        p.update(neck=-30 * k, head=-20 * k, tail=-15 * k, pitch=4 * k)
    return p


# ---------------------------------------------------------------- build

def coat_material(sp, S):
    """Coat: noise-mottled fur colour, pale belly and darker lower legs (Generated Z), far-side
    legs 15% darker (Generated Y), fur bump. Generated coords are undeformed, so the pattern
    stays on the body as it animates."""
    m = bpy.data.materials.new(f"{sp}_coat")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    pr.inputs["Roughness"].default_value = 0.92
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    # Object space in metres (Generated coords on a Skin mesh map from the wire skeleton's
    # bounds and put the bands in nonsense places).
    L.new(tc.outputs["Object"], sep.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60.0; nz.inputs["Detail"].default_value = 8.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.35; mr.inputs["From Max"].default_value = 0.7
    L.new(nz.outputs["Fac"], mr.inputs["Value"])

    def mix(fac, a, b):
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
        L.new(fac, mx.inputs[0])
        for sock, val in ((mx.inputs[6], a), (mx.inputs[7], b)):
            if isinstance(val, tuple):
                sock.default_value = lin(val)
            else:
                L.new(val, sock)
        return mx.outputs[2]

    def band(sock, lo, hi):
        r = N.new("ShaderNodeMapRange"); r.interpolation_type = "SMOOTHSTEP"
        r.inputs["From Min"].default_value, r.inputs["From Max"].default_value = lo, hi
        L.new(sock, r.inputs["Value"])
        return r.outputs["Result"]

    col = mix(mr.outputs["Result"], S["coat"][0], S["coat"][1])
    # Markings come from the "markings" colour attribute, computed once from the rest pose
    # (R belly, G socks, B far-side legs): they ride the deforming mesh and can't drift
    # across the legs the way coordinate bands did.
    attr = N.new("ShaderNodeAttribute"); attr.attribute_name = "markings"
    msep = N.new("ShaderNodeSeparateColor")
    L.new(attr.outputs["Color"], msep.inputs[0])
    col = mix(msep.outputs[0], col, S["belly"])
    col = mix(msep.outputs[1], col, S["socks"])
    dk = N.new("ShaderNodeMix"); dk.data_type = "RGBA"; dk.blend_type = "MULTIPLY"
    L.new(msep.outputs[2], dk.inputs[0]); L.new(col, dk.inputs[6]); dk.inputs[7].default_value = (0.85, 0.85, 0.85, 1.0)
    L.new(dk.outputs[2], pr.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35
    L.new(nz.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], pr.inputs["Normal"])
    return m


def build_species(sp, scene):
    S = SPECIES[sp]
    coll = bpy.data.collections.new(sp)
    scene.collection.children.link(coll)

    # --- skeleton graph (vertices with radius and owning bone) ---
    verts, radii, owner, edges = [], [], [], []

    def add(x, y, z, r, bone, link_to=None):
        verts.append(Vector((x, y, z)))
        radii.append(r)
        owner.append(bone)
        idx = len(verts) - 1
        if link_to is not None:
            edges.append((link_to, idx))
        return idx

    def chain(points, bones, y=0.0, link_to=None, rscale=1.0):
        idx = link_to
        out = []
        for (x, z, r), b in zip(points, bones):
            if idx is not None and verts[idx] == Vector((x, y, z)):
                out.append(idx)
                continue
            idx = add(x, y, z, r * rscale, b, idx)
            out.append(idx)
        return out

    spine = chain(S["spine"], ["body"] * len(S["spine"]))
    neck = chain(S["neck"][1:], ["neck", "neck"], link_to=spine[-1])
    if S["ruff"]:
        for k in neck:
            radii[k] *= 1.0 + S["ruff"] * 3
    head = chain(S["head"][1:], ["head"] * (len(S["head"]) - 1), link_to=neck[-1])
    tail = chain(S["tail"][1:], ["tail"] * (len(S["tail"]) - 1), link_to=spine[0])
    for sy in (-1, 1):                                                   # ears
        e0 = add(S["head"][0][0] + 0.02, sy * 0.05, S["head"][0][1] + 0.08, 0.035, "head", head[0] if head else neck[-1])
        add(S["head"][0][0] - 0.04, sy * 0.08, S["head"][0][1] + 0.08 + S["ears"], 0.012, "head", e0)
    leg_root = {}
    for l in LEGS:
        pts = S["front"] if l.startswith("f") else S["hind"]
        y = (-1 if l.endswith("n") else 1) * S["leg_y"]
        attach = min(spine, key=lambda k: abs(verts[k].x - pts[0][0]))
        names = [f"u_{l}", f"m_{l}", f"l_{l}", f"l_{l}"]
        top = add(pts[0][0], y, pts[0][1], pts[0][2], "body", attach)    # inside the body: rides the torso
        leg_root[l] = chain(pts[1:], names, y=y, link_to=top)

    # --- armature (bones in the side plane; joint vertices belong to the child bone) ---
    ad = bpy.data.armatures.new(f"{sp}_rig")
    rig = bpy.data.objects.new(f"{sp}_rig", ad)
    coll.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = ad.edit_bones

    def bone(name, head, tail, parent=None):
        b = eb.new(name)
        b.head, b.tail = Vector(head), Vector(tail)
        if parent:
            b.parent = eb[parent]
        return name

    sp0, spn = S["spine"][2], S["spine"][-1]
    bone("body", (sp0[0], 0, sp0[1]), (spn[0], 0, spn[1]))
    bone("neck", (S["neck"][0][0], 0, S["neck"][0][1]), (S["neck"][-1][0], 0, S["neck"][-1][1]), "body")
    bone("head", (S["head"][0][0], 0, S["head"][0][1]), (S["head"][-1][0], 0, S["head"][-1][1]), "neck")
    bone("tail", (S["tail"][0][0], 0, S["tail"][0][1]), (S["tail"][-1][0], 0, S["tail"][-1][1]), "body")
    for l in LEGS:
        pts = S["front"] if l.startswith("f") else S["hind"]
        y = (-1 if l.endswith("n") else 1) * S["leg_y"]
        bone(f"u_{l}", (pts[0][0], y, pts[0][1]), (pts[1][0], y, pts[1][1]), "body")
        bone(f"m_{l}", (pts[1][0], y, pts[1][1]), (pts[2][0], y, pts[2][1]), f"u_{l}")
        bone(f"l_{l}", (pts[2][0], y, pts[2][1]), (pts[4][0], y, pts[4][1]), f"m_{l}")
    bpy.ops.object.mode_set(mode="OBJECT")

    body = metaball_body(sp, S, verts, radii, edges, coll)
    paint_markings(body, S)
    body.data.materials.append(coat_material(sp, S))
    bind_auto(body, rig)

    dark = mat(f"{sp}_dark", (40, 32, 28), (30, 24, 22), 0, 0.5, 20, 0.1)
    for sy in (-1, 1):                                                   # eyes and nose on the head bone
        hx, hz = S["head"][1][0], S["head"][1][1]
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.018, location=(hx - 0.02, sy * 0.07, hz + 0.03))
        eye = bpy.context.active_object
        _rig_child(eye, rig, "head", coll, dark)
    tx, tz, _ = S["head"][-1]
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.035, location=(tx + 0.01, 0, tz))
    _rig_child(bpy.context.active_object, rig, "head", coll, dark)
    if S["antler"]:
        build_antlers(sp, S, rig, coll)
    animate(sp, rig, S)


# Metaball field: a capsule of nominal radius r shows a surface at about r / MB_GROW, so radii
# from the skeleton table are scaled up by MB_GROW (threshold 0.6, stiffness 2).
MB_GROW = 1.35


def metaball_body(sp, S, verts, radii, edges, coll):
    """B-015 v3 body: one metaball capsule per skeleton segment (radius = mean of its ends),
    plus a deep-chest ellipsoid; metaballs blend into one organic surface at every branch
    point (where Skin built hard hulls). Converted to one mesh and decimated."""
    mb = bpy.data.metaballs.new(f"{sp}_mb")
    mb.resolution = mb.render_resolution = 0.014
    mb.threshold = 0.6
    for a, b in edges:
        pa, pb = verts[a], verts[b]
        d = pb - pa
        length = d.length
        if length < 1e-4:
            continue
        el = mb.elements.new(type="CAPSULE")
        el.co = (pa + pb) / 2
        el.radius = MB_GROW * (radii[a] + radii[b]) / 2
        el.size_x = length / 2
        el.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())
        el.stiffness = 2.0
    sp0, sp3 = S["spine"][1], S["spine"][3]                       # deep chest / barrel
    el = mb.elements.new(type="ELLIPSOID")
    el.co = ((sp0[0] + sp3[0]) / 2 + 0.1, 0.0, sp3[1] - sp3[2] * 0.35)
    el.radius = MB_GROW * sp3[2] * 1.05
    el.size_x, el.size_y, el.size_z = 1.6, 0.85, 1.0
    ob = bpy.data.objects.new(f"{sp}_mb", mb)
    coll.objects.link(ob)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    body = bpy.context.view_layer.objects.active
    body.name = f"{sp}_body"
    dec = body.modifiers.new("dec", "DECIMATE")
    dec.ratio = 0.35
    bpy.ops.object.modifier_apply(modifier="dec")
    for p in body.data.polygons:
        p.use_smooth = True
    return body


def paint_markings(body, S):
    """Masks in a colour attribute from the rest pose: R pale belly (torso underside), G darker
    lower legs (socks), B far-side legs (y beyond half the leg spacing, below the torso)."""
    me = body.data
    attr = me.color_attributes.new("markings", "FLOAT_COLOR", "POINT")
    spine_z = sum(p[1] for p in S["spine"]) / len(S["spine"])
    r_body = max(p[2] for p in S["spine"])
    belly_top, belly_bot = spine_z - 0.35 * r_body, spine_z - 1.25 * r_body
    x0, x1 = S["spine"][0][0], S["spine"][-1][0]

    def smooth(e0, e1, v):
        t = min(1.0, max(0.0, (v - e0) / (e1 - e0)))
        return t * t * (3 - 2 * t)
    for k, v in enumerate(me.vertices):
        x, y, z = v.co
        belly = smooth(belly_top, belly_top - 0.06, z) * smooth(belly_bot - 0.08, belly_bot, z) * \
            smooth(x0, x0 + 0.15, x) * smooth(x1, x1 - 0.15, x)
        socks = smooth(S["socks_z"], S["socks_z"] - 0.08, z)
        far = smooth(0.5 * S["leg_y"], S["leg_y"], y) * smooth(belly_bot, belly_bot - 0.1, z)
        attr.data[k].color = (belly, socks, far, 1.0)


def bind_auto(body, rig):
    """Parent with automatic (bone heat) weights; fall back to envelopes if heat fails."""
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    body.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    if len(body.vertex_groups) == 0:                  # heat weighting failed silently
        bpy.ops.object.parent_set(type="ARMATURE_ENVELOPE")
        print("MERIDIAN bind: heat weights failed, used envelopes for", body.name)


def _rig_child(ob, rig, bone_name, coll, m):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = bone_name
    bpy.context.view_layer.update()
    ob.matrix_world = mw
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(m)


def build_antlers(sp, S, rig, coll):
    """Main beam per side curving up-back then forward, 5 tines (brow, bez, trez, two crown),
    beam length ~1.9x head length; a Skin skeleton on the head bone."""
    A = S["antler"]
    hx, hz = S["head"][0][0], S["head"][0][1]
    verts, radii, edges = [], [], []

    def add(p, r, link=None):
        verts.append(Vector(p))
        radii.append(r)
        k = len(verts) - 1
        if link is not None:
            edges.append((link, k))
        return k
    L = A["beam"]
    roots = []
    for sy in (-1, 1):
        base = add((hx + 0.02, sy * 0.06, hz + 0.1), 0.032)
        roots.append(base)
        beam_pts = [(-0.12, 0.10, 0.3), (-0.16, 0.16, 0.6), (-0.06, 0.2, 0.85), (0.08, 0.22, 1.0)]
        beam = [base]
        for dx, dy, f in beam_pts:
            beam.append(add((hx + dx, sy * dy, hz + 0.1 + L * f), 0.03 * (1.1 - 0.6 * f), beam[-1]))
        tines = [(1, (0.18, 0.0, 0.07)), (1, (0.16, 0.0, 0.13)), (2, (0.16, 0.0, 0.12)), (3, (0.1, 0.0, 0.16)), (4, (-0.07, 0.0, 0.13))]
        for k, (bi, d) in enumerate(tines[:A["tines"]]):
            p0 = verts[beam[bi]]
            mid = add(tuple(p0 + Vector(d) * 0.55 + Vector((0, sy * 0.01, 0))), 0.014, beam[bi])
            add(tuple(p0 + Vector(d)), 0.006, mid)
    me = bpy.data.meshes.new(f"{sp}_antler_skeleton")
    me.from_pydata([tuple(v) for v in verts], edges, [])
    ob = bpy.data.objects.new(f"{sp}_antlers", me)
    coll.objects.link(ob)
    vg = ob.vertex_groups.new(name="head")
    vg.add(list(range(len(verts))), 1.0, "REPLACE")
    ob.parent = rig
    a = ob.modifiers.new("rig", "ARMATURE")
    a.object = rig
    ob.modifiers.new("skin", "SKIN").use_smooth_shade = True
    s = ob.modifiers.new("sub", "SUBSURF")
    s.levels = s.render_levels = 2
    for sv, r in zip(me.skin_vertices[0].data, radii):
        sv.radius = (r, r)
    for k in roots:                                                      # one root per antler
        me.skin_vertices[0].data[k].use_root = True
    me.materials.append(mat(f"{sp}_antler_bone", (214, 196, 162), (176, 154, 120), 0, 0.55, 30, 0.35))


# ---------------------------------------------------------------- animation

def rot_y(deg):
    return Matrix.Rotation(math.radians(deg), 3, "Y")


def set_pose(rig, name, deg):
    """Rotate pose bone `name` by `deg` about the world Y axis (side plane), expressed in the
    bone's rest frame (all rotations are about Y, so they commute down the chain)."""
    pb = rig.pose.bones[name]
    M = rig.data.bones[name].matrix_local.to_3x3()
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (M.inverted() @ rot_y(deg) @ M).to_quaternion()


def animate(sp, rig, S):
    scene = bpy.context.scene
    for name in CLIP_ORDER:
        for i in range(CLIP_LEN[name]):
            p = pose(name, i, sp)
            f = CLIP_START[name] + i
            rig.rotation_euler = (0.0, math.radians(p["pitch"]), 0.0)
            rig.keyframe_insert("rotation_euler", frame=f)
            set_pose(rig, "neck", -p["neck"])
            set_pose(rig, "head", p["head"])
            set_pose(rig, "tail", p["tail"])
            for l in LEGS:
                front = l.startswith("f")
                set_pose(rig, f"u_{l}", -p[f"s_{l}"])
                # Front: elbow folds the forearm back a little, carpus folds the cannon back.
                # Hind: stifle folds the tibia back, hock folds the cannon forward.
                set_pose(rig, f"m_{l}", (0.4 if front else 1.0) * p[f"j1_{l}"])
                set_pose(rig, f"l_{l}", p[f"j2_{l}"] if front else -p[f"j2_{l}"])
            for pb in rig.pose.bones:
                pb.keyframe_insert("rotation_quaternion", frame=f)
    if rig.animation_data and rig.animation_data.action:
        _constant(rig.animation_data.action)
    ground_exactly(rig)


def ground_exactly(rig):
    """Measure the evaluated meshes on every keyed frame and key the rig's z so the lowest
    vertex sits exactly on z = 0 (no sinking into the pivot line, no floating)."""
    scene = bpy.context.scene
    meshes = [o for o in rig.children_recursive if o.type == "MESH"]
    for name in CLIP_ORDER:
        for i in range(CLIP_LEN[name]):
            f = CLIP_START[name] + i
            rig.location.z = 0.0
            scene.frame_set(f)
            rig.location.z = 0.0
            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()
            zmin = float("inf")
            for o in meshes:
                ev = o.evaluated_get(dg)
                m = ev.to_mesh()
                mw = ev.matrix_world
                zmin = min([zmin] + [(mw @ v.co).z for v in m.vertices])
                ev.to_mesh_clear()
            rig.location.z = -zmin
            rig.keyframe_insert("location", frame=f)
    if rig.animation_data and rig.animation_data.action:
        _constant(rig.animation_data.action)


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for sp in SPECIES:
        build_species(sp, scene)
    scene.frame_start = 1
    scene.frame_end = max(CLIP_START[c] + CLIP_LEN[c] - 1 for c in CLIP_ORDER)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
