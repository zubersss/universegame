"""B-085 grove preview: 20 flora instances on a grassy plane under the Earth Sun (v1 preset
sun dir (-0.75, 0.45, -0.55), strength 4.5), seen from the camera side (-Y), stamped."""
import math
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, r"C:/dev/universegame/blender/scripts")
sys.path.insert(0, r"C:/dev/universegame/blender")
import numpy as np  # noqa: E402
from meridian import pngio  # noqa: E402
import review  # noqa: E402

out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=r"C:/dev/universegame/blender/sources/props/mars_flora.blend")
scene = bpy.context.scene
src = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
for o in src.values():
    o.hide_render = True
layout = [("boulder_b", -9, 7), ("boulder_a", -4.5, 9), ("boulder_c", -1, 6), ("boulder_b", 4, 10), ("boulder_a", 8.5, 8),
          ("ice_b", 11, 6), ("ice_a", 13.5, 4), ("dust_bush", -7, 2.5), ("dust_bush", 2, 3), ("dust_bush", 6.5, 2.2),
          ("rock_a", -5, 1.2), ("rock_b", 0.5, 2.0), ("rock_a", 3.5, 1.0), ("rock_b", 10, 2.5), ("stalagmite", -8, 4),
          ("stalagmite", -2.8, 4.5), ("ice_a", 1.2, 5.5), ("rock_a", 7.5, 0.9), ("rock_b", 12, 1.2), ("stalagmite", 14.5, 7)]
rnd = random.Random(5)
for name, x, y in layout:
    o = bpy.data.objects.new(name + "_inst", src[name].data)
    scene.collection.objects.link(o)
    o.location = (x, y, 0)
    o.rotation_euler.z = rnd.uniform(0, 2 * math.pi)
bpy.ops.mesh.primitive_plane_add(size=80, location=(2, 10, 0))
g = bpy.context.active_object
gm = bpy.data.materials.new("ground")
gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.30, 0.12, 0.06, 1)
g.data.materials.append(gm)
sd = bpy.data.lights.new("sun", "SUN")
sd.energy, sd.angle = 4.5 * 0.75, math.radians(1.0)
sun = bpy.data.objects.new("sun", sd)
scene.collection.objects.link(sun)
sun.rotation_euler = Vector((-0.75, 0.45, -0.55)).to_track_quat("-Z", "Y").to_euler()
scene.world = bpy.data.worlds.new("sky") if scene.world is None else scene.world
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.55, 0.36, 0.24, 1)
bg.inputs["Strength"].default_value = 0.5
cd = bpy.data.cameras.new("cam")
cd.lens = 35
cam = bpy.data.objects.new("cam", cd)
scene.collection.objects.link(cam)
cam.location = (2.5, -16, 4.5)
cam.rotation_euler = (Vector((2.5, 5, 3.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scene.render.engine = name
        break
    except TypeError:
        pass
scene.render.resolution_x, scene.render.resolution_y = 1280, 560
scene.render.filepath = out + ".tmp.png"
bpy.ops.render.render(write_still=True)
img = pngio.read_png(out + ".tmp.png")[..., :3].copy()
review.draw(img, review.stamp_text(r"C:/dev/universegame/Assets/_Game/Art/props/mars_flora/boulder_a.glb"), 2, img.shape[0] - 16, (1.0, 1.0, 0.85))
pngio.write_png(out, np.dstack([pngio.to_u8(np.clip(img, 0, 1)), np.full(img.shape[:2], 255, np.uint8)]))
import os
os.remove(out + ".tmp.png")
print("GROVE ok", out)
