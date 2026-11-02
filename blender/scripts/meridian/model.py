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

import bpy
import numpy as np
from mathutils import Vector

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
    dg = bpy.context.evaluated_depsgraph_get()
    dups = []
    rig = None
    for ob in meshes:
        arm, bone = _bone_of(ob)
        if arm is not None:
            rig = arm
        ev = ob.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
        me.transform(ob.matrix_world)
        d = bpy.data.objects.new(ob.name + "_x", me)
        bpy.context.scene.collection.objects.link(d)
        if arm is not None:
            vg = d.vertex_groups.new(name=bone or arm.data.bones[0].name)
            vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
        dups.append(d)
    if rig is None and rigs:
        rig = next(iter(rigs))
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for d in dups:
        d.select_set(True)
    bpy.context.view_layer.objects.active = dups[0]
    if len(dups) > 1:
        bpy.ops.object.join()
    mesh = bpy.context.view_layer.objects.active
    mesh.name = "model"
    mesh.data.name = "model"
    for o in meshes:                                 # originals stay out of the export
        o.hide_render, o.hide_viewport = True, True
    if rig is not None:
        mod = mesh.modifiers.new("Armature", "ARMATURE")
        mod.object = rig
        mesh.parent = rig
        mesh.matrix_parent_inverse = rig.matrix_world.inverted()
    return mesh, rig


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


def bake_maps(mesh, size, samples=16):
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
    mask = np.dstack([out["metallic"][..., 0], out["ao"][..., 0], out["rim"][..., 0], 1.0 - out["rough"][..., 0]])
    maps = {"color": out["color"][..., :3], "normal": out["normal"][..., :3], "mask": mask,
            "emission": out["emission"][..., :3]}
    return maps


# ---------------------------------------------------------------- 4. export material

def export_material(mesh, maps_paths, emissive):
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
    nt.links.new(tex(maps_paths["color"], False).outputs["Color"], pr.inputs["Base Color"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex(maps_paths["normal"], True).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], pr.inputs["Normal"])
    if emissive:
        nt.links.new(tex(maps_paths["emission"], False).outputs["Color"], pr.inputs["Emission Color"])
        pr.inputs["Emission Strength"].default_value = 1.0
    mesh.data.materials.clear()
    mesh.data.materials.append(m)
    return m


# ---------------------------------------------------------------- 5. glb

def export_glb(path, mesh, rig, extras=()):
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
    if rig is not None:
        kw.update(export_animation_mode="ACTIONS", export_frame_range=False, export_force_sampling=True,
                  export_anim_slide_to_zero=True,                      # clips start at t = 0 (was +1 frame)
                  export_optimize_animation_size=False)
    bpy.ops.export_scene.gltf(**kw)


# ---------------------------------------------------------------- 6. turntable

def turntable(mesh, rig, out_png, sun_dir=(-0.6, 0.4, -0.7), size=384, frame=1):
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
    bpy.ops.mesh.primitive_plane_add(size=radius * 8, location=(centre.x, centre.y, lo.z))
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
    for ang in (0.0, -45.0, 180.0):                 # front (+X), 3/4 (front-left toward the camera side), back
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
    mesh, rig = merge_collection(objs)
    tris = triangle_count(mesh)
    budget = int(entry.get("tri_budget", 1 << 30))
    if tris > budget:
        raise ModelError(f"{tris} triangles > budget {budget}")
    unwrap(mesh)
    maps = bake_maps(mesh, size, samples=int(entry.get("bake_samples", 16)))
    paths = {}
    for mname in MAPS:
        a = maps[mname]
        if a.shape[2] == 3:
            a = np.dstack([a, np.ones(a.shape[:2], np.float32)])
        p = os.path.join(out_dir, f"{variant}_{mname}.png")
        pngio.write_png(p, pngio.to_u8(np.clip(a, 0, 1)))
        paths[mname] = p
    emissive = float(maps["emission"].max()) > 0.02
    export_material(mesh, paths, emissive)
    glb = os.path.join(out_dir, f"{variant}.glb")
    sockets = [o for o in objs if o.type == "EMPTY" and o.name.startswith("socket_")]
    export_glb(glb, mesh, rig, sockets)
    clips = entry.get("clips", [])
    meta = {"key": key, "format": "glb", "contract": "v2", "facing": "+X", "up": "+Y", "units": "m",
            "origin": entry.get("origin_rule", "feet"), "triangles": tris, "texture": size,
            "maps": list(MAPS), "fps": 30, "clips": clips,
            "sockets": [o.name[len("socket_"):] for o in sockets] or entry.get("sockets", [])}
    with open(os.path.join(out_dir, f"{variant}.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    sheet = turntable(mesh, rig, os.path.join(preview_dir, f"review_{key.replace('/', '_')}"))
    out = os.path.join(preview_dir, f"review_{key.replace('/', '_')}.png")
    stamp_fn(sheet, glb)
    pngio.write_png(out, np.dstack([pngio.to_u8(np.clip(sheet, 0, 1)), np.full(sheet.shape[:2], 255, np.uint8)]))
    return {"glb": glb, "triangles": tris, "texture": size, "emissive": emissive, "review": out,
            "clips": [c["name"] for c in clips]}
