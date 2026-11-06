"""Stamped clip strip from an EXPORTED model glb (B-103): N evenly spaced frames per clip,
side view from the game's camera side, one row per clip, stamped with the glb's time + hash.

Reads the shipped glb (not the .blend), so the strip shows what Unity imports. The colour map
beside the glb is wired onto the imported mesh for readability (the glb carries no images).

  blender --background --factory-startup --python blender/scripts/clip_strip.py -- \
      <glb> <out.png> <fps> <clip,clip,...> [frames_per_clip=6]
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import review  # noqa: E402
from meridian import pngio  # noqa: E402

PW, PH = 240, 300            # panel size (px)
ORTHO = 2.6                  # metres across the panel's longer side


def setup(fps):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps, sc.render.fps_base = fps, 1.0
    for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = name
            break
        except TypeError:
            continue
    sc.render.resolution_x, sc.render.resolution_y = PW, PH
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("strip_world")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.32, 0.36, 0.42, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(50), 0, math.radians(150))
    sc.collection.objects.link(sun)
    return sc


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    glb, out, fps, names = a[0], a[1], int(a[2]), a[3].split(",")
    per = int(a[4]) if len(a) > 4 else 6
    sc = setup(fps)
    bpy.ops.import_scene.gltf(filepath=glb)
    rig = next(o for o in sc.objects if o.type == "ARMATURE")
    meshes = [o for o in sc.objects if o.type == "MESH" and not o.name.endswith("_LOD1")]
    for o in sc.objects:
        if o.type == "MESH" and o.name.endswith("_LOD1"):
            o.hide_render = True
    col = glb[:-4] + "_color.png"
    if os.path.isfile(col):
        m = bpy.data.materials.new("strip_mat")
        m.use_nodes = True
        tex = m.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(col)
        pr = m.node_tree.nodes["Principled BSDF"]
        m.node_tree.links.new(tex.outputs["Color"], pr.inputs["Base Color"])
        pr.inputs["Roughness"].default_value = 0.8
        for o in meshes:
            o.data.materials.clear()
            o.data.materials.append(m)
    # Ground line at the feet (y = 0 in glTF -> z = 0 here).
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    g = bpy.context.active_object
    gm = bpy.data.materials.new("ground")
    gm.diffuse_color = (0.12, 0.11, 0.1, 1)
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.12, 0.11, 0.1, 1)
    g.data.materials.append(gm)
    # Camera on the game's camera side. Export turned the model 180 deg (D-065): it faces -X here and
    # its camera side is +Y, so look from +Y toward -Y; -X then points right on screen.
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = ORTHO
    cam.location = (0, 8, 0.95)
    cam.rotation_euler = (math.radians(90), 0, math.radians(180))
    sc.collection.objects.link(cam)
    sc.camera = cam
    rig.animation_data_create()
    rows, tmp = [], os.path.join(os.path.dirname(out), "_strip_tmp.png")
    found = []
    for name in names:
        act = bpy.data.actions.get(name) or next((x for x in bpy.data.actions if x.name.startswith(name + "_") or x.name.split("|")[-1] == name), None)
        if act is None:
            raise SystemExit(f"FAIL clip {name} not in {glb}")
        rig.animation_data.action = act
        if hasattr(rig.animation_data, "action_suggested_slot") and act.slots:
            rig.animation_data.action_slot = act.slots[0]
        f0, f1 = act.frame_range
        found.append(f"{name} {f0:.0f}-{f1:.0f}")
        panels = []
        for i in range(per):
            f = f0 + (f1 - f0) * i / (per - 1)
            sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
            sc.render.filepath = tmp
            bpy.ops.render.render(write_still=True)
            img = pngio.read_png(tmp)[..., :3].copy()
            review.draw(img, f"{f - f0:.0f}".replace(".", ""), 2, 2, (1.0, 1.0, 0.85))
            panels.append(img)
        row = np.hstack(panels)
        label = np.full((PH, 120, 3), 0.08, np.float32)
        rows.append(np.hstack([label, row]))
    os.remove(tmp)
    sheet = np.vstack(rows)
    review.stamp(sheet, glb, review.stale_keys())
    review.write(out, sheet)
    print("REVIEW clips ok", out, "|", "; ".join(found))


if __name__ == "__main__":
    main()
