"""Contract v2 model export (§9, B-077): source collection -> one skinned mesh -> baked maps ->
<variant>.glb + <variant>_{color,normal,mask,emission}.png + <variant>.json, and a stamped
Eevee turntable contact sheet (front, 3/4, back). Called by render.py for manifest entries with
"model": true.

Pipeline (generic, so the v1 sources become models without rewriting them):
  1. Duplicate the collection's meshes, apply modifiers, convert rigid parts to skinning: an
     object parented to a bone gets a vertex group of that bone (weight 1); then join into one
     mesh bound to the armature (or unskinned for props).
  2. Smart-UV-unwrap the joined mesh into one 0..1 atlas.
  3. Bake with Cycles CPU: base colour (DIFFUSE colour only), tangent-space normal, emission,
     roughness, AO, plus metallic and rim via a temporary emission route. Pack
     mask = (R metallic, G AO, B rim, A smoothness).
  4. Replace the materials with one export material (emissive parts keep a second slot) that
     uses the baked colour/normal/emission, so the glb is self-consistent; the PNGs beside it
     are what ArtImporter v5 reads.
  5. Export GLB: Y-up, metres, selected rig + mesh, actions as animations (names kept), 30 fps.
  6. Turntable: Eevee, the planet Sun from the upper right, neutral grey floor, three views.
Coordinates: Blender +X = screen right (the model faces +X), +Z up, Y = depth (the play plane
is y = 0). glTF export with export_yup maps Blender Z-up to glTF Y-up.
"""
import json
import math
import os
import re

import bpy
import numpy as np
from mathutils import Vector


def bend_normals(ob):
    """Custom normals: card loops take their stored 'bend' (crown-volume) normal, wood keeps its own."""
    me = ob.data
    if "bend" not in me.attributes:
        return
    bend = me.attributes["bend"].data
    cn = [Vector(c.vector) for c in me.corner_normals]
    out = []
    for li, loop in enumerate(me.loops):
        b = Vector(bend[loop.vertex_index].vector)
        out.append(b.normalized() if b.length > 1e-4 else cn[li])
    me.normals_split_custom_set(out)

from meridian import pngio

MAPS = ("color", "normal", "mask", "emission")


class ModelError(Exception):
    pass


# ---------------------------------------------------------------- 1. one skinned mesh

def _bone_of(ob):
    if ob.parent and ob.parent.type == "ARMATURE" and ob.parent_type == "BONE":
        return ob.parent, ob.parent_bone
    if ob.parent and ob.parent.type == "ARMATURE":
        return ob.parent, None
    return None, None


def merge_collection(objs):
    """Duplicate every visible mesh, bake its world transform + modifiers, tag it with its bone
    and join. Returns (joined mesh, armature or None)."""
    meshes = [o for o in objs if o.type == "MESH" and not o.hide_render]
    rigs = {o for o in objs if o.type == "ARMATURE"}
    if not meshes:
        raise ModelError("no meshes in the source collection")
    rig = next((a for a in (_bone_of(o)[0] for o in meshes) if a is not None), None) or (next(iter(rigs)) if rigs else None)
    # Bind at REST (fix 2026-11-02): the first exports merged at the current frame, so the
    # active clip's frame-1 pose was baked into the bind shape and then applied again by the
    # animation. Rest pose + the rig object's own (keyed) transform neutralised, meshes stored
    # in the rig's local space.
    saved = None
    if rig is not None:
        saved = (rig.data.pose_position, rig.animation_data.action if rig.animation_data else None, rig.matrix_basis.copy())
        rig.data.pose_position = "REST"
        if rig.animation_data:
            rig.animation_data.action = None
        rig.matrix_basis = rig.matrix_basis.__class__.Identity(4)
    skinned_mods = []
    for ob in meshes:                                 # skinned bodies: evaluate without the armature
        for md in ob.modifiers:
            if md.type == "ARMATURE" and md.show_viewport:
                md.show_viewport = False
                skinned_mods.append(md)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    to_local = rig.matrix_world.inverted() if rig is not None else None
    dups = []
    for ob in meshes:
        arm, bone = _bone_of(ob)
        skinned = any(md.type == "ARMATURE" for md in ob.modifiers)
        ev = ob.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
        orco = me.attributes.new("meridian_orco", "FLOAT_VECTOR", "POINT")   # original object space (B-093)
        orco.data.foreach_set("vector", [c for v in me.vertices for c in v.co])
        me.transform(to_local @ ob.matrix_world if to_local is not None else ob.matrix_world)
        d = bpy.data.objects.new(ob.name + "_x", me)
        bpy.context.scene.collection.objects.link(d)
        if skinned:                                   # keep its own bone weights
            for g in ob.vertex_groups:
                d.vertex_groups.new(name=g.name)
        elif rig is not None:                         # rigid part: weight 1 to its bone (or the first bone)
            vg = d.vertex_groups.new(name=bone or rig.data.bones[0].name)
            vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
        dups.append(d)
    for md in skinned_mods:
        md.show_viewport = True
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for d in dups:
        d.select_set(True)
    bpy.context.view_layer.objects.active = dups[0]
    if len(dups) > 1:
        bpy.ops.object.join()
    mesh = bpy.context.view_layer.objects.active
    mesh.name = "model"
    _orco_materials(mesh)
    mesh.data.name = "model"
    for o in meshes:                                 # originals stay out of the export
        o.hide_render, o.hide_viewport = True, True
    if rig is not None:
        for md in list(mesh.modifiers):
            mesh.modifiers.remove(md)
        mod = mesh.modifiers.new("Armature", "ARMATURE")
        mod.object = rig
        mesh.parent = rig
        mesh.matrix_parent_inverse.identity()
        mesh.matrix_basis.identity()                 # data is already in rig space
        rig.data.pose_position = "POSE"
        if saved[1] is not None:
            rig.animation_data.action = saved[1]
        bpy.context.view_layer.update()
    return mesh, rig


def bake_objects_to_bones(objs, frames):
    """B-093: v1 creatures that animate plain objects (wing meshes, a root empty, sacs) cannot be
    merged into one skinned mesh as-is. Give every animated object (and its animated ancestors)
    a bone whose rest = the object's world transform at frames[0], bake its world motion into
    the rig's action at every v1 frame, and re-parent the meshes to those bones. Returns the rig
    (the existing one, or a new `baked_rig`)."""
    from mathutils import Matrix
    scene = bpy.context.scene
    rig = next((o for o in objs if o.type == "ARMATURE"), None)
    anim = [o for o in objs if o.type in ("MESH", "EMPTY") and o.animation_data and o.animation_data.action]
    if not anim:
        return rig
    sel = set(anim)
    for o in list(anim):                                  # animated ancestors that are objects
        p = o.parent
        while p is not None and p.type != "ARMATURE":
            if p.animation_data and p.animation_data.action:
                sel.add(p)
            p = p.parent
    if rig is None:
        ad = bpy.data.armatures.new("baked_rig")
        rig = bpy.data.objects.new("baked_rig", ad)
        bpy.context.scene.collection.objects.link(rig)
        for c in objs[0].users_collection:
            c.objects.link(rig)
    scene.frame_set(frames[0])
    bpy.context.view_layer.update()
    rest = {o: o.matrix_world.copy() for o in sel}
    mesh_rest = {o: o.matrix_world.copy() for o in objs if o.type == "MESH"}   # before any clearing

    def depth(o):
        d, p = 0, o.parent
        while p is not None:
            d, p = d + 1, p.parent
        return d
    order = sorted(sel, key=depth)

    def parent_bone(o):
        p = o.parent
        while p is not None:
            if p in sel:
                return "b_" + p.name
            if p.type == "ARMATURE":
                return o.parent_bone if o.parent is p else None
            p = p.parent
        return None
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    inv = rig.matrix_world.inverted()
    for o in order:
        b = rig.data.edit_bones.new("b_" + o.name)
        m = inv @ rest[o]
        loc, rot, _ = m.decompose()
        b.head = loc
        b.tail = loc + rot @ Vector((0.0, 0.05, 0.0))
        b.align_roll(rot @ Vector((0.0, 0.0, 1.0)))
        pb = parent_bone(o)
        if pb:
            b.parent = rig.data.edit_bones[pb]
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.update()
    if rig.animation_data is None:
        rig.animation_data_create()
    if rig.animation_data.action is None:
        rig.animation_data.action = bpy.data.actions.new("baked")
    for f in frames:                                      # bake world motion (parents first)
        scene.frame_set(f)
        bpy.context.view_layer.update()
        mw = {o: o.matrix_world.copy() for o in order}
        for o in order:
            pbn = rig.pose.bones["b_" + o.name]
            pbn.rotation_mode = "QUATERNION"
            target = inv @ mw[o] @ rest[o].inverted() @ (rig.matrix_world @ rig.data.bones[pbn.name].matrix_local)
            pbn.matrix = target
            bpy.context.view_layer.update()
            pbn.keyframe_insert("location", frame=f)
            pbn.keyframe_insert("rotation_quaternion", frame=f)
            pbn.keyframe_insert("scale", frame=f)
    scene.frame_set(frames[0])
    for o in order:                                       # stop object animation, ride the bones
        o.animation_data_clear()
    bpy.context.view_layer.update()
    for o in objs:
        if o.type != "MESH":
            continue
        host, p = (o if o in sel else None), o.parent
        while host is None and p is not None:            # nearest animated ancestor
            if p in sel:
                host = p
            p = p.parent
        if host is None:                                 # not under any animated object: leave it
            continue
        o.parent, o.parent_type, o.parent_bone = rig, "BONE", "b_" + host.name
        bpy.context.view_layer.update()
        o.matrix_world = mesh_rest[o]
    return rig


def retime_clips(rig, clips):
    """v1 single-timeline animation -> one action per clip at 30 fps (contract §9).
    clips: [{name, start, length, fpp, loop}] in v1 frames. Samples every fcurve of the rig's
    current action at start+i, keys it at 1 + k*fpp (Bezier in-betweens), loops close on pose 0
    and one-shots hold the last pose; then removes the source action so it isn't exported.
    Returns the clip list for the json (name, frames, loop)."""
    src = rig.animation_data.action if rig.animation_data else None
    if src is None:
        raise ModelError("retime: rig has no action")
    fcs = getattr(src, "fcurves", None)
    if fcs is None:                                   # Blender 5 layered actions
        fcs = [fc for layer in src.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
    curves = [(fc.data_path, fc.array_index, fc) for fc in fcs]
    out = []
    for c in clips:
        act = bpy.data.actions.new(c["name"])
        act.use_fake_user = True
        rig.animation_data.action = act
        n, fpp = c["length"], c["fpp"]
        idx = list(range(n)) + ([0] if c.get("loop") else [n - 1])
        for k, i in enumerate(idx):
            f = 1 + k * fpp
            for path, ai, fc in curves:
                v = fc.evaluate(c["start"] + i)
                owner_path, prop = (path.rsplit(".", 1) if "." in path else ("", path))
                owner = rig.path_resolve(owner_path) if owner_path else rig
                vec = getattr(owner, prop)
                try:
                    vec[ai] = v
                except TypeError:
                    setattr(owner, prop, v)
                owner.keyframe_insert(prop, index=ai, frame=f)
        out.append({"name": c["name"], "frames": n * fpp, "loop": bool(c.get("loop"))})
    rig.animation_data.action = None
    bpy.data.actions.remove(src)
    rig.animation_data.action = bpy.data.actions[clips[0]["name"]]
    return out


def auto_decimate(mesh, budget):
    """Collapse-decimate to <= 95 % of the triangle budget (keeps UVs-to-be, vertex groups)."""
    tris = triangle_count(mesh)
    if tris <= budget:
        return tris
    dec = mesh.modifiers.new("budget", "DECIMATE")
    dec.ratio = 0.95 * budget / tris
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = mesh
    mesh.select_set(True)
    for md in list(mesh.modifiers):                  # decimate must run before the armature
        if md.type == "ARMATURE":
            bpy.ops.object.modifier_move_to_index(modifier=md.name, index=len(mesh.modifiers) - 1)
    bpy.ops.object.modifier_apply(modifier="budget")
    return triangle_count(mesh)


def _orco_materials(mesh):
    """Procedural v1 materials read Texture Coordinate > Object; after the merge every part sits
    in rig space, so patterns shifted (the acidmoth's eyespots fell off its wings). Re-route
    those links to the per-vertex original object coordinates stored before the merge."""
    done = set()
    for slot in mesh.material_slots:
        m = slot.material
        if m is None or not m.use_nodes or m.name in done:
            continue
        done.add(m.name)
        nt = m.node_tree
        for tc in [n for n in nt.nodes if n.type == "TEX_COORD"]:
            links = [l for l in nt.links if l.from_node == tc and l.from_socket.name == "Object"]
            if not links:
                continue
            at = nt.nodes.new("ShaderNodeAttribute")
            at.attribute_name = "meridian_orco"
            for l in links:
                to = l.to_socket
                nt.links.remove(l)
                nt.links.new(at.outputs["Vector"], to)


def triangle_count(mesh):
    mesh.data.calc_loop_triangles()
    return len(mesh.data.loop_triangles)


# ---------------------------------------------------------------- 2-3. unwrap and bake

def unwrap(mesh):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
    bpy.ops.object.mode_set(mode="OBJECT")


def _image(name, size, non_color):
    img = bpy.data.images.new(name, size, size, alpha=False, float_buffer=False)
    img.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
    return img


def _set_target(mesh, img):
    for slot in mesh.material_slots:
        m = slot.material
        if m is None or not m.use_nodes:
            continue
        nt = m.node_tree
        node = nt.nodes.get("meridian_bake")
        if node is None:
            node = nt.nodes.new("ShaderNodeTexImage")
            node.name = "meridian_bake"
        node.image = img
        nt.nodes.active = node


def _principled(m):
    if m is None or not m.use_nodes:
        return None
    return next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def _route_to_emission(mesh, which):
    """Temporarily feed `which` ('metallic' | 'rim') into Emission so EMIT bakes it as grey.
    Returns an undo list."""
    undo = []
    for slot in mesh.material_slots:
        m = slot.material
        pr = _principled(m)
        if pr is None:
            continue
        nt = m.node_tree
        ec, es = pr.inputs["Emission Color"], pr.inputs["Emission Strength"]
        saved = (tuple(ec.default_value), es.default_value, [l.from_socket for l in ec.links])
        for l in list(ec.links):
            nt.links.remove(l)
        if which == "metallic" and pr.inputs["Metallic"].links:
            nt.links.new(pr.inputs["Metallic"].links[0].from_socket, ec)
        else:
            v = pr.inputs["Metallic"].default_value if which == "metallic" else float(m.get("meridian_rim", 0.0))
            ec.default_value = (v, v, v, 1.0)
        es.default_value = 1.0
        undo.append((m, pr, saved))
    return undo


def _restore(undo):
    for m, pr, (col, strength, srcs) in undo:
        ec = pr.inputs["Emission Color"]
        for l in list(ec.links):
            m.node_tree.links.remove(l)
        ec.default_value = col
        pr.inputs["Emission Strength"].default_value = strength
        for s in srcs:
            m.node_tree.links.new(s, ec)


def _pixels(img):
    a = np.empty(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(img.size[1], img.size[0], 4)[::-1]          # top row first (PNG order)


def bake_maps(mesh, size, samples=16, alpha_map=False):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    bk = scene.render.bake
    bk.margin, bk.use_clear = 8, True
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    out = {}

    def bake(kind, non_color, **kw):
        img = _image(f"bake_{kind}", size, non_color)
        _set_target(mesh, img)
        bpy.ops.object.bake(**kw)
        return _pixels(img)

    alpha_saved = []                                      # B-094: Principled Alpha scales every pass; bake opaque
    for slot in mesh.material_slots:
        pr = _principled(slot.material)
        if pr is None:
            continue
        ai = pr.inputs["Alpha"]
        alpha_saved.append((slot.material, ai, ai.default_value, [l.from_socket for l in ai.links]))
        for l in list(ai.links):
            slot.material.node_tree.links.remove(l)
        ai.default_value = 1.0
    # Cycles' diffuse colour = base colour x (1 - metallic): a metallic part bakes black (the
    # calibration cube did). Metallic goes to the mask, so switch it off for the colour bake.
    undo = []
    for slot in mesh.material_slots:
        pr = _principled(slot.material)
        if pr is None:
            continue
        mi = pr.inputs["Metallic"]
        undo.append((slot.material, mi, mi.default_value, [l.from_socket for l in mi.links]))
        for l in list(mi.links):
            slot.material.node_tree.links.remove(l)
        mi.default_value = 0.0
    try:
        out["color"] = bake("color", False, type="DIFFUSE", pass_filter={"COLOR"})
    finally:
        for m, mi, v, srcs in undo:
            mi.default_value = v
            for s in srcs:
                m.node_tree.links.new(s, mi)
    out["normal"] = bake("normal", True, type="NORMAL", normal_space="TANGENT")
    out["emission"] = bake("emission", False, type="EMIT")
    out["rough"] = bake("rough", True, type="ROUGHNESS")
    out["ao"] = bake("ao", True, type="AO")
    for which in ("metallic", "rim"):
        undo = _route_to_emission(mesh, which)
        try:
            out[which] = bake(which, True, type="EMIT")
        finally:
            _restore(undo)
    color = out["color"][..., :3]
    if alpha_map:                                         # B-094: per-part alpha -> the colour map's A (fins)
        undo = []
        for m, ai, v, srcs in alpha_saved:
            pr, nt = _principled(m), m.node_tree
            ec, es = pr.inputs["Emission Color"], pr.inputs["Emission Strength"]
            saved = (tuple(ec.default_value), es.default_value, [l.from_socket for l in ec.links])
            for l in list(ec.links):
                nt.links.remove(l)
            if srcs:
                nt.links.new(srcs[0], ec)
            else:
                ec.default_value = (v, v, v, 1.0)
            es.default_value = 1.0
            undo.append((m, pr, saved))
        try:
            out["alpha"] = bake("alpha", True, type="EMIT")
        finally:
            _restore(undo)
        color = np.dstack([color, out["alpha"][..., 0]])
    for m, ai, v, srcs in alpha_saved:
        ai.default_value = v
        for src in srcs:
            m.node_tree.links.new(src, ai)
    mask = np.dstack([out["metallic"][..., 0], out["ao"][..., 0], out["rim"][..., 0], 1.0 - out["rough"][..., 0]])
    maps = {"color": color, "normal": out["normal"][..., :3], "mask": mask,
            "emission": out["emission"][..., :3]}
    return maps


# ---------------------------------------------------------------- 4. export material

def export_material(mesh, maps_paths, emissive, alpha=None):
    """One material using the baked maps (a second slot is not needed: emission is a map)."""
    m = bpy.data.materials.new("model_mat")
    m.use_nodes = True
    nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]

    def tex(path, non_color):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(path, check_existing=False)
        n.image.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
        return n
    ct = tex(maps_paths["color"], False)
    nt.links.new(ct.outputs["Color"], pr.inputs["Base Color"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex(maps_paths["normal"], True).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], pr.inputs["Normal"])
    if emissive:
        nt.links.new(tex(maps_paths["emission"], False).outputs["Color"], pr.inputs["Emission Color"])
        pr.inputs["Emission Strength"].default_value = 1.0
    if alpha is not None:                                 # B-092: translucent strips (glTF alphaMode BLEND)
        if alpha == "map":                               # B-094: alpha from the colour map's A
            nt.links.new(ct.outputs["Alpha"], pr.inputs["Alpha"])
        else:
            pr.inputs["Alpha"].default_value = float(alpha)
        for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            try:
                setattr(m, attr, val)
            except (AttributeError, TypeError):
                pass
        m.use_backface_culling = False
    mesh.data.materials.clear()
    mesh.data.materials.append(m)
    return m


# ---------------------------------------------------------------- 5. glb

def _drop_cards(lod, cap, tris):
    """B-109 LOD1 for card crowns: keep every step-th card cluster (step 2, 3, ...) until the mesh is
    within `cap` triangles and <= 50 % of LOD0; the wood is untouched; bent normals re-applied."""
    import bmesh
    step = 2
    while True:
        bm = bmesh.new()
        bm.from_mesh(lod.data)
        lay = bm.verts.layers.int.get("card")
        kill = [f for f in bm.faces if f.verts[0][lay] and (f.verts[0][lay] - 1) % step != 0]
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        me = bpy.data.meshes.new(lod.data.name + "_try")
        bm.to_mesh(me)
        bm.free()
        me.calc_loop_triangles()
        n = len(me.loop_triangles)
        if (n <= cap and n <= tris * 0.5) or step >= 8:
            old = lod.data
            lod.data = me
            me.name = old.name
            bpy.data.meshes.remove(old)
            bend_normals(lod)
            return n
        bpy.data.meshes.remove(me)
        step += 1


def export_glb(path, mesh, rig, extras=(), vertex_colors=False):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    mesh.select_set(True)
    for e in extras:                                 # socket_<name> empties (contract v2.1 §9.1)
        e.hide_viewport = e.hide_render = False
        e.select_set(True)
    if rig is not None:
        rig.select_set(True)
        rig.hide_render = False
        rig.hide_viewport = False
    bpy.context.view_layer.objects.active = rig or mesh
    kw = dict(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=False,
              export_animations=rig is not None, export_image_format="NONE")
    if vertex_colors:                                # B-085: COLOR_0 = sway mask (R)
        kw["export_vertex_color"] = "ACTIVE"
    if rig is not None:
        kw.update(export_animation_mode="ACTIONS", export_frame_range=False, export_force_sampling=True,
                  export_anim_slide_to_zero=True,                      # clips start at t = 0 (was +1 frame)
                  export_optimize_animation_size=False)
    # D-065 (contract v2.2): glTFast mirrors X on import, so the model is exported facing glTF -X
    # (a 180 deg turn about the vertical axis on the top node, not a mirror). After Unity's mirror
    # it faces +X, and the Blender camera side (-Y -> glTF +Z -> turned to -Z) lands on Unity's
    # camera side (-Z). The turn is undone after export (the turntable stays front = +X).
    # Every top-level selected object turns about the world origin (rig case: just the rig, the
    # mesh/LOD/sockets are its children; prop/ship case: mesh, LOD1 and sockets each).
    from mathutils import Matrix
    sel = [o for o in bpy.context.view_layer.objects if o.select_get()]
    tops = [o for o in sel if o.parent not in sel]
    saved = {o: o.matrix_world.copy() for o in tops}
    turn = Matrix.Rotation(math.pi, 4, "Z")
    for o in tops:
        o.matrix_world = turn @ saved[o]
    bpy.context.view_layer.update()
    try:
        bpy.ops.export_scene.gltf(**kw)
    finally:
        for o in tops:
            o.matrix_world = saved[o]
        bpy.context.view_layer.update()


# ---------------------------------------------------------------- 6. turntable

def turntable(mesh, rig, out_png, sun_dir=(-0.6, 0.4, -0.7), size=384, frame=1, angles=(0.0, -45.0, 180.0)):
    """Eevee, planet Sun from the upper right, neutral grey floor, views front (+X), 3/4, back."""
    scene = bpy.context.scene
    for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = name
            break
        except TypeError:
            continue
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.film_transparent = False
    scene.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    pts = [ev.matrix_world @ v.co for v in ev.data.vertices]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre = (lo + hi) / 2
    radius = max((hi - lo).length / 2, 0.2)
    bpy.ops.mesh.primitive_plane_add(size=radius * 8, location=(centre.x, centre.y, lo.z - 0.02 * radius))   # below flat models (rings z-fought the floor)
    floor = bpy.context.active_object
    fm = bpy.data.materials.new("tt_floor")
    fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.18, 0.18, 0.18, 1)
    floor.data.materials.append(fm)
    sd = bpy.data.lights.new("tt_sun", "SUN")
    sd.energy = 3.5
    sun = bpy.data.objects.new("tt_sun", sd)
    scene.collection.objects.link(sun)
    sun.rotation_euler = Vector(sun_dir).to_track_quat("-Z", "Y").to_euler()
    if scene.world is None:
        scene.world = bpy.data.worlds.new("tt_world")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.42, 0.45, 0.5, 1)
        bg.inputs["Strength"].default_value = 0.6
    cd = bpy.data.cameras.new("tt_cam")
    cd.lens = 50
    cam = bpy.data.objects.new("tt_cam", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam
    panels = []
    dist = radius * 4.2
    cd.clip_start, cd.clip_end = max(0.05, dist * 0.002), dist * 4.0     # large bands (skyline ~600 m) sat past the default far clip
    for ang in angles:                              # D-068: characters/creatures/ships +X, 3/4, back; props camera side (-Y), 3/4, far side
        if ang == "top":                            # B-090: space objects, the Space camera looks straight down
            cam.location = centre + Vector((0.0, -0.001, dist))
            ang = 999
        else:
            a = math.radians(ang)
            cam.location = centre + Vector((math.cos(a) * dist, math.sin(a) * dist, radius * 0.9))
        cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        path = out_png + f".tt{int(ang)}.png"
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        panels.append(pngio.read_png(path)[..., :3])
        os.remove(path)
    return np.hstack(panels)


# ---------------------------------------------------------------- entry point

def export_model(entry, art_dir, preview_dir, objs, stamp_fn):
    """Run the whole pipeline for one manifest entry; returns a dict for the log line."""
    key = entry["key"]
    cat, name, variant = key.split("/")
    out_dir = os.path.join(art_dir, cat, name)
    os.makedirs(out_dir, exist_ok=True)
    size = int(entry.get("texture", 1024))
    scene = bpy.context.scene
    scene.render.fps, scene.render.fps_base = 30, 1.0
    clips = entry.get("clips", [])
    if entry.get("bake_objects"):
        frames = sorted({c["start"] + i for c in entry["retime"] for i in range(c["length"])})
        rig_b = bake_objects_to_bones(objs, frames)
        if rig_b is not None and rig_b not in objs:
            objs = list(objs) + [rig_b]
    if entry.get("retime"):
        rig0 = next((o for o in objs if o.type == "ARMATURE"), None)
        if rig0 is None:
            raise ModelError("retime: no armature in the collection")
        clips = retime_clips(rig0, entry["retime"])
    mesh, rig = merge_collection(objs)
    if rig is not None and clips:
        # Export only the declared clips: ACTIONS mode also picks up any other action whose
        # channels match (the wolf's action rode along on the stag, same bone names).
        keep = {c["name"] for c in clips}
        prefix = entry.get("collection", "") + "|"
        own = {act.name[len(prefix):]: act for act in bpy.data.actions if act.name.startswith(prefix)}
        for act in list(bpy.data.actions):           # several species per blend: keep only this one's clips
            if act.name.startswith(prefix) and act.name[len(prefix):] in keep:
                continue
            if act.name in keep and act.name not in own:
                continue
            bpy.data.actions.remove(act)
        for clip, act in own.items():
            if clip in keep:
                act.name = clip                      # glTF animation name = clip name
        if rig.animation_data and "idle" in bpy.data.actions:
            rig.animation_data.action = bpy.data.actions["idle"]
    budget = int(entry.get("tri_budget", 1 << 30))
    if entry.get("auto_decimate"):
        auto_decimate(mesh, budget)
    tris = triangle_count(mesh)
    if tris > budget:
        raise ModelError(f"{tris} triangles > budget {budget}")
    atlas = entry.get("atlas")
    paths = {}
    if atlas:                                        # B-085: shared atlas, authored UVs, no bake
        maps = None
        emissive = False
    else:
        if not (entry.get("keep_uv") and mesh.data.uv_layers):   # B-102 round 2: bands author their UVs
            unwrap(mesh)
        maps = bake_maps(mesh, size, samples=int(entry.get("bake_samples", 16)), alpha_map=entry.get("alpha") == "map")
    for mname in (MAPS if not atlas else ()):
        a = maps[mname]
        if a.shape[2] == 3:
            a = np.dstack([a, np.ones(a.shape[:2], np.float32)])
        p = os.path.join(out_dir, f"{variant}_{mname}.png")
        pngio.write_png(p, pngio.to_u8(np.clip(a, 0, 1)))
        paths[mname] = p
    if not atlas:
        emissive = float(maps["emission"].max()) > 0.02
        export_material(mesh, paths, emissive, entry.get("alpha"))
    glb = os.path.join(out_dir, f"{variant}.glb")
    sockets = [o for o in objs if o.type == "EMPTY" and o.name.startswith("socket_")]
    for o in sockets:                                # B-094: several modules per blend share socket names; Blender
        base = re.sub(r"\.\d{3}$", "", o.name)       # suffixed the copies (socket_root.001): export the bare name
        if base != o.name:
            other = bpy.data.objects.get(base)
            if other is not None:
                other.name = base + ".swap"
            o.name = base
    extras = list(sockets)
    lod_tris = None
    if entry.get("lod1"):
        # Contract §9 LOD: `<variant>_LOD1` at <= 50 % triangles in the same glb, same UVs and
        # material (decimate keeps UVs, vertex groups and the armature binding).
        lod = mesh.copy()
        lod.data = mesh.data.copy()
        lod.name = lod.data.name = f"{variant}_LOD1"
        bpy.context.scene.collection.objects.link(lod)
        if rig is not None:
            lod.parent = rig
            lod.matrix_parent_inverse = mesh.matrix_parent_inverse.copy()
        if entry.get("lod1_cards") and "card" in lod.data.attributes:
            _drop_cards(lod, int(entry.get("lod1_max", 1 << 30)), tris)   # B-109: fewer card clusters, wood kept
        else:
            dec = lod.modifiers.new("lod", "DECIMATE")
            dec.ratio = min(0.48, float(entry.get("lod1_max", 1 << 30)) / max(1, tris))
            for o in bpy.context.view_layer.objects:
                o.select_set(False)
            bpy.context.view_layer.objects.active = lod
            lod.select_set(True)
            bpy.ops.object.modifier_apply(modifier="lod")
        lod_tris = triangle_count(lod)
        extras.append(lod)
    export_glb(glb, mesh, rig, extras, vertex_colors=bool(entry.get("vertex_colors")))
    meta = {"key": key, "format": "glb", "contract": "v2.2", "facing": "+X in Unity (exported facing glTF -X, D-065)", "up": "+Y", "units": "m",
            "origin": entry.get("origin_rule", "feet"), "triangles": tris, "lod1_triangles": lod_tris, "texture": size,
            "maps": list(MAPS), "fps": 30, "clips": clips, "atlas": atlas,
            "vertex_color": entry.get("vertex_colors"),
            "sockets": [o.name[len("socket_"):] for o in sockets] or entry.get("sockets", [])}
    if entry.get("alpha_clip"):                      # contract v2.6 ruling 10 (D-082): cut-out cards -> alpha clip + double-sided
        meta["alpha_clip"] = True
    with open(os.path.join(out_dir, f"{variant}.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    angles = ("top", -45.0, 0.0) if entry.get("origin_rule") == "space" else (-90.0, -45.0, 90.0) if entry.get("origin_rule") in ("base", "band") else (0.0, -45.0, 180.0)   # D-068 (bands as props: seen from the camera side)
    sheet = turntable(mesh, rig, os.path.join(preview_dir, f"review_{key.replace('/', '_')}"), angles=angles)
    out = os.path.join(preview_dir, f"review_{key.replace('/', '_')}.png")
    stamp_fn(sheet, glb)
    pngio.write_png(out, np.dstack([pngio.to_u8(np.clip(sheet, 0, 1)), np.full(sheet.shape[:2], 255, np.uint8)]))
    return {"glb": glb, "triangles": tris, "texture": size, "emissive": emissive, "review": out,
            "clips": [c["name"] for c in clips]}
