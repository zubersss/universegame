"""Builds blender/sources/props/calibration.blend: a 1 m sphere on a 1 m cube with known flat
colors (contract calibration asset, B-002). Re-run any time; the result is deterministic.

  blender --background --factory-startup --python blender/scripts/build_calibration.py

Known values (sRGB 8-bit, what the color map must contain):
  cube   (60, 120, 200)  metallic 1.0, rim 0.0
  sphere (200, 60, 50)   metallic 0.0, rim 0.5
  stripe (90, 90, 90) albedo, emission (255, 160, 40) on the cube's camera face
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "props", "calibration.blend")

CUBE_SRGB = (60, 120, 200)
SPHERE_SRGB = (200, 60, 50)
STRIPE_SRGB = (90, 90, 90)
STRIPE_EMIT_SRGB = (255, 160, 40)


def srgb_to_linear(c8):
    out = []
    for c in c8:
        c = c / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def material(name, base, metallic=0.0, rim=0.0, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    pr = m.node_tree.nodes["Principled BSDF"]
    pr.inputs["Base Color"].default_value = srgb_to_linear(base)
    pr.inputs["Metallic"].default_value = metallic
    pr.inputs["Roughness"].default_value = 0.5
    if emit:
        pr.inputs["Emission Color"].default_value = srgb_to_linear(emit)
        pr.inputs["Emission Strength"].default_value = 1.0
    m["meridian_rim"] = rim
    return m


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    coll = bpy.data.collections.new("calibration")
    scene.collection.children.link(coll)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.5))
    cube = bpy.context.active_object
    cube.name = "cal_cube"
    cube.data.materials.append(material("cal_cube", CUBE_SRGB, metallic=1.0))

    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=0.5, location=(0, 0, 1.5))
    sphere = bpy.context.active_object
    sphere.name = "cal_sphere"
    bpy.ops.object.shade_smooth()
    sphere.data.materials.append(material("cal_sphere", SPHERE_SRGB, rim=0.5))

    # Emissive stripe 0.6 x 0.1 m on the camera-facing (-Y) face of the cube.
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.505, 0.3))
    stripe = bpy.context.active_object
    stripe.name = "cal_stripe"
    stripe.scale = (0.6, 0.01, 0.1)
    stripe.data.materials.append(material("cal_stripe", STRIPE_SRGB, emit=STRIPE_EMIT_SRGB))

    for ob in (cube, sphere, stripe):
        for c in ob.users_collection:
            c.objects.unlink(ob)
        coll.objects.link(ob)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
