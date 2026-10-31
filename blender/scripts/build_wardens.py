"""Builds blender/sources/creatures/warden.blend: the Warden sentinel (B-043, Bible §2/§8).

Wardens are Sowing-era guardians: engineered but grown. Original design: an almond seed-pod
hull of pale ceramic-bone with carved ribs and faint verdigris-green seams (emission), a lens
eye at the front tip inside a thick bezel ringed by six iris petals, three root-like tendrils
trailing beneath (metaball chains on an armature, automatic weights). Flier: centred pivot,
the same clip names/timing as the walkers. Attack = the lens charging: the petals open and a
teal core swells over frames 1-4 (scaled geometry, since the emission pass reads material
strength once).

  blender --background --factory-startup --python blender/scripts/build_wardens.py
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

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "creatures", "warden.blend")


def _select_only(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)


def _link(coll, ob):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)


def _on_bone(ob, rig, bone, coll):
    _link(coll, ob)
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = bone
    bpy.context.view_layer.update()
    ob.matrix_world = mw


def hull_material(name):
    """Pale ceramic-bone with carved rib grooves (wave texture along x) whose seams glow a faint
    verdigris green (emission in the grooves only)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    pr.inputs["Roughness"].default_value = 0.4
    tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "X"
    wv.inputs["Scale"].default_value = 1.8; wv.inputs["Distortion"].default_value = 2.5
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    g = N.new("ShaderNodeMapRange"); g.interpolation_type = "SMOOTHSTEP"
    g.inputs["From Min"].default_value, g.inputs["From Max"].default_value = 0.05, 0.0   # fine seams (were zebra stripes)
    L.new(wv.outputs["Fac"], g.inputs["Value"])
    col = N.new("ShaderNodeMix"); col.data_type = "RGBA"
    L.new(g.outputs["Result"], col.inputs[0])
    col.inputs[6].default_value = lin((226, 218, 198)); col.inputs[7].default_value = lin((70, 150, 120))
    L.new(col.outputs[2], pr.inputs["Base Color"])
    em = N.new("ShaderNodeMix"); em.data_type = "RGBA"
    L.new(g.outputs["Result"], em.inputs[0])
    em.inputs[6].default_value = (0, 0, 0, 1); em.inputs[7].default_value = lin((110, 230, 170))
    L.new(em.outputs[2], pr.inputs["Emission Color"])
    pr.inputs["Emission Strength"].default_value = 0.5
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4
    L.new(wv.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], pr.inputs["Normal"])
    return m


def build_sentinel(scene):
    sp = "sentinel"
    coll = bpy.data.collections.new(sp)
    scene.collection.children.link(coll)
    ad = bpy.data.armatures.new(f"{sp}_rig")
    rig = bpy.data.objects.new(f"{sp}_rig", ad)
    coll.objects.link(rig)
    _select_only(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = ad.edit_bones
    root = eb.new("root"); root.head, root.tail = Vector((-0.2, 0, 0)), Vector((0.2, 0, 0))
    tend = [(-0.25, -0.12), (-0.1, 0.0), (-0.32, 0.12)]
    for k, (x, y) in enumerate(tend):
        a = eb.new(f"tA_{k}"); a.head, a.tail = Vector((x, y, -0.22)), Vector((x - 0.12, y, -0.5)); a.parent = root
        b = eb.new(f"tB_{k}"); b.head, b.tail = a.tail.copy(), Vector((x - 0.3, y, -0.74)); b.parent = a
    bpy.ops.object.mode_set(mode="OBJECT")
    # Tendrils: metaball capsules -> one mesh -> automatic weights.
    mb = bpy.data.metaballs.new(f"{sp}_mb")
    mb.resolution = mb.render_resolution = 0.01
    for x, y in tend:
        pts = [(x, y, -0.2, 0.045), (x - 0.12, y, -0.5, 0.032), (x - 0.3, y, -0.74, 0.016)]
        for (x0, y0, z0, r0), (x1, y1, z1, r1) in zip(pts, pts[1:]):
            d = Vector((x1 - x0, y1 - y0, z1 - z0))
            e = mb.elements.new(type="CAPSULE")
            e.co = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
            e.radius = 1.35 * (r0 + r1) / 2
            e.size_x = d.length / 2
            e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())
    mbo = bpy.data.objects.new(f"{sp}_mb", mb)
    coll.objects.link(mbo)
    _select_only(mbo)
    bpy.ops.object.convert(target="MESH")
    tendrils = bpy.context.view_layer.objects.active
    tendrils.name = f"{sp}_tendrils"
    for p in tendrils.data.polygons:
        p.use_smooth = True
    tendrils.data.materials.append(flat_material(f"{sp}_root", (120, 104, 84), rough=0.7))
    bind_auto(tendrils, rig)

    hull = hull_material(f"{sp}_hull")
    # Almond seed-pod hull: a sphere tapered to a point at the back.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=1.0, location=(0, 0, 0))
    pod = bpy.context.active_object
    pod.name = f"{sp}_pod"
    for v in pod.data.vertices:
        t = min(1.0, max(0.0, (1 - v.co.x) / 2))                      # 0 front .. 1 back
        k = 1.0 - 0.75 * t ** 1.6
        v.co.y *= k
        v.co.z *= k
    pod.scale = (0.48, 0.3, 0.3)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    pod.data.materials.append(hull)
    _on_bone(pod, rig, "root", coll)
    for sz in (-1, 1):                                                # stabiliser vanes
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.12, radius2=0.0, depth=0.34,
                                        location=(-0.3, 0, sz * 0.2), rotation=(0, math.radians(-90 + sz * 25), 0))
        vane = bpy.context.active_object
        vane.scale = (1.0, 0.25, 1.0)
        vane.data.materials.append(hull)
        _on_bone(vane, rig, "root", coll)
    # Lens eye: bezel ring, glass lens, six iris petals, charge core.
    bezel_m = flat_material(f"{sp}_bezel", (96, 92, 84), metallic=0.5, rough=0.4)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.05, location=(0.42, 0, 0), rotation=(0, math.pi / 2, 0))
    bez = bpy.context.active_object
    bez.data.materials.append(bezel_m)
    _on_bone(bez, rig, "root", coll)
    lens_m = flat_material(f"{sp}_lens", (20, 70, 70), metallic=0.2, emit=(90, 230, 210), strength=1.4, rough=0.08)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.17, location=(0.45, 0, 0))
    lens = bpy.context.active_object
    lens.scale = (0.85, 1.0, 1.0)                                   # bulges forward: reads in profile
    lens.data.materials.append(lens_m)
    _on_bone(lens, rig, "root", coll)
    core_m = flat_material(f"{sp}_core", (220, 255, 240), emit=(200, 255, 235), strength=3.0)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.1, location=(0.6, 0, 0))
    core = bpy.context.active_object
    core.data.materials.append(core_m)
    _on_bone(core, rig, "root", coll)
    petals = []
    for k in range(6):
        a = 2 * math.pi * k / 6
        piv = bpy.data.objects.new(f"{sp}_petalpiv{k}", None)
        piv.location = (0.46, 0.17 * math.cos(a), 0.17 * math.sin(a))
        piv.rotation_euler = (a, 0, 0)
        _on_bone(piv, rig, "root", coll)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
        pt = bpy.context.active_object
        pt.scale = (0.03, 0.08, 0.1)
        pt.location = (0.0, 0.0, -0.08)                               # hangs inward over the lens
        pt.data.materials.append(hull)
        _link(coll, pt)
        pt.parent = piv
        petals.append(piv)

    for name in CLIP_ORDER:
        for i in range(CLIP_LEN[name]):
            f = CLIP_START[name] + i
            t = i / CLIP_LEN[name]
            pitch, z, open_, charge, sway = 0.0, 0.0, 0.25, 0.0, 6 * math.sin(2 * math.pi * t)
            if name == "idle":
                z = 0.03 * math.sin(2 * math.pi * t)
            elif name == "walk":
                pitch, sway = -8.0, 12 * math.sin(2 * math.pi * t)
            elif name == "attack":
                k = [0.2, 0.5, 0.8, 1.0, 0.6, 0.2][i]
                pitch, open_, charge = -4 * k, 0.25 + 0.75 * k, (k if 1 <= i <= 4 else 0.0)
            elif name == "hurt":
                pitch, open_ = 12 * (1.0 if i == 0 else 0.5), 0.0
            elif name == "death":
                k = [0.15, 0.35, 0.55, 0.75, 0.92, 1.0][i]
                pitch, z, open_, sway = 50 * k, -0.25 * k, 0.0, 0.0
            rig.rotation_euler = (0, math.radians(pitch), 0)
            rig.location = (0, 0, z)
            rig.keyframe_insert("rotation_euler", frame=f)
            rig.keyframe_insert("location", frame=f)
            for k in range(len(tend)):
                set_pose(rig, f"tA_{k}", sway * math.cos(k) - (20 if name == "walk" else 0))
                set_pose(rig, f"tB_{k}", 1.4 * sway * math.cos(k + 0.7))
            for pb in rig.pose.bones:
                pb.keyframe_insert("rotation_quaternion", frame=f)
            for piv in petals:                                        # iris: closed 0 .. open 1
                piv.rotation_euler.y = math.radians(-70 * open_)
                piv.keyframe_insert("rotation_euler", frame=f)
            sc = max(0.001, charge * 1.3)
            core.scale = (sc, sc, sc)
            core.keyframe_insert("scale", frame=f)
    for ob in [rig, core] + petals:
        if ob.animation_data and ob.animation_data.action:
            _constant(ob.animation_data.action)


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    build_sentinel(scene)
    scene.frame_start = 1
    scene.frame_end = max(CLIP_START[c] + CLIP_LEN[c] - 1 for c in CLIP_ORDER)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
