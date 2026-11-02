"""Builds blender/sources/planets/saturn_rings.blend: Saturn's rings as a flat mesh (B-090).

An annulus in the XY plane (seen from the top-down Space camera), from the C-ring inner edge
(1.239 R) to the A-ring outer edge (2.269 R), R = 96 m (Saturn's radius in the Space scene,
UNITY handoff B-018). UVs are planar and match planets/saturn/rings_color.png (B-018: the
A-ring outer edge at 500 px of 1024, so the texture spans +-2.323 R), whose alpha carries the
ring structure (Cassini Division, Encke Gap). One material reads that texture (colour + alpha);
no bake (model.py atlas branch).

  blender --background --factory-startup --python blender/scripts/build_rings.py
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "planets", "saturn_rings.blend")
TEX = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art", "planets", "saturn", "rings_color.png")
R = 96.0
R_IN, R_OUT = 1.239, 2.269
TEX_HALF = 512.0 / (500.0 / R_OUT)            # texture half-width in Saturn radii (2.323)


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    coll = bpy.data.collections.new("saturn_rings")
    scene.collection.children.link(coll)
    seg, rings = 96, 6                             # radial rows keep the alpha structure on vertices too
    verts, faces = [], []
    radii = [R_IN + (R_OUT - R_IN) * k / rings for k in range(rings + 1)]
    for r in radii:
        for s in range(seg):
            a = 2 * math.pi * s / seg
            verts.append((r * R * math.cos(a), r * R * math.sin(a), 0.0))
    for k in range(rings):
        for s in range(seg):
            a0, a1 = k * seg + s, k * seg + (s + 1) % seg
            faces.append((a0, a1, a1 + seg, a0 + seg))
    me = bpy.data.meshes.new("rings")
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            x, y, _ = verts[me.loops[li].vertex_index]
            uv.data[li].uv = (0.5 + x / (2 * TEX_HALF * R), 0.5 + y / (2 * TEX_HALF * R))
    ob = bpy.data.objects.new("rings", me)
    coll.objects.link(ob)
    m = bpy.data.materials.new("saturn_rings")
    m.use_nodes = True
    nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]
    pr.inputs["Roughness"].default_value = 0.9
    if os.path.isfile(TEX):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(TEX, check_existing=True)
        nt.links.new(t.outputs["Color"], pr.inputs["Base Color"])
        nt.links.new(t.outputs["Alpha"], pr.inputs["Alpha"])
    me.materials.append(m)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
