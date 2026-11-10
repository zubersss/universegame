"""B-258 part 1 (D-205, docs/STYLE_V7.md): THE PAINT PASS on real 3D. Runs INSIDE Blender (bpy), through
tools/blender_scene.ps1. Raw scans are read from blender/vendor_cc0/<asset>/<asset>.gltf (CC0, git-ignored; glTF only: it
carries no script); nothing is written to Assets.

  blender --background --factory-startup --python v7_paint_pass.py -- probe
      STAGE A: for each asset: what the scan IS (objects, triangles, bounds, materials, textures), a plain lit render on
      alpha at 384 px per metre (4x the game's 96; shrunk afterwards, never enlarged), and what this Blender's
      compositor offers for the paint filter (the Kuwahara node's sockets and properties, read before scripting it).

The light is the frame's ONE light: from the upper right, a little toward the viewer (build_specimens_v6.LIGHT), a warm
sun and a cool ambient sky. The camera is orthographic, from the side: image right = +X, up = +Z, the viewer at -Y.
Lines printed with "V7 " are the report the wrapper shows.
"""
import math
import os
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
VENDOR = os.path.join(REPO, "blender", "vendor_cc0")
OUT = os.path.join(REPO, "blender", "preview", "b258")
# What run 1 (11-10 13:43) found: each download is a SET laid out in a row - five calatheas 0.13-0.42 m tall, six rocks
# 2.1-2.7 m wide over 8 m. Rendering a whole set in one frame is not what the game needs (every piece is its own sprite)
# and the rock set at 3120 x 730 px took Blender past 1.3 GB (stopped by the watchdog at 1441 MB). So: ONE PIECE A RUN,
# named here, moved to stand on the origin; the plant is scaled up (a broad-leaved understorey plant a metre tall).
PIECES = {"calathea_orbifolia_01": ("calathea_orbifolia_01_a", 2.5), "rock_moss_set_01": ("rock_moss_set_01_rock03", 1.0)}   # asset: (object, scale)
ASSETS = tuple(PIECES)
PPM = 384                                         # render px per metre: 4x the surface camera's 96
TO_LIGHT = Vector((0.58, -0.53, 0.62)).normalized()   # the frame's light in Blender's axes (x right, -y to the viewer, z up)
SUN = ((1.0, 0.93, 0.80), 5.5)                    # colour, strength (W/m2) (run 1 at 4.0 / 0.55: the leaves near black)
SKY = ((0.62, 0.74, 0.90), 0.9)                   # the ambient: a cool, even sky


def say(*a):
    print("V7 " + " ".join(str(x) for x in a), flush=True)


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def bounds(obs):
    lo, hi = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    for o in obs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z)))
            hi = Vector((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
    return lo, hi


def load(asset):
    path = os.path.join(VENDOR, asset, asset + ".gltf")
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def isolate(obs, name, scale=1.0):
    """Keep one object of a set: the rest are removed; it is scaled and moved so its middle (x, y) stands on the origin
    (z is kept: the scan's own ground line is z = 0; a rock sits partly below it). -> [the object]."""
    from mathutils import Matrix
    keep = [o for o in obs if o.name == name]
    if not keep:
        raise SystemExit(f"v7_paint_pass: no object '{name}' among {[o.name for o in obs]}")
    for o in obs:
        if o.name != name:
            bpy.data.objects.remove(o, do_unlink=True)
    o = keep[0]
    bpy.context.view_layer.update()
    lo, hi = bounds([o])
    mid = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, 0.0))
    o.matrix_world = Matrix.Scale(scale, 4) @ Matrix.Translation(-mid) @ o.matrix_world
    bpy.context.view_layer.update()
    return [o]


def describe(asset, obs):
    lo, hi = bounds(obs)
    say(f"{asset}: {len(obs)} mesh object(s); bounds x {lo.x:+.3f}..{hi.x:+.3f}, y {lo.y:+.3f}..{hi.y:+.3f}, z {lo.z:+.3f}..{hi.z:+.3f} m "
        f"= {hi.x - lo.x:.2f} wide, {hi.y - lo.y:.2f} deep, {hi.z - lo.z:.2f} tall")
    mats = {}
    for o in obs:
        me = o.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        ol, oh = bounds([o])
        say(f"  object '{o.name}': {len(me.vertices)} verts, {tris} tris, z {ol.z:+.3f}..{oh.z:+.3f}, x {ol.x:+.3f}..{oh.x:+.3f}; materials: "
            + ", ".join(s.material.name for s in o.material_slots if s.material))
        for s in o.material_slots:
            if s.material:
                mats[s.material.name] = s.material
    for name, m in mats.items():
        tex = []
        alpha_linked = False
        if m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image:
                    tex.append(f"{os.path.basename(n.image.filepath)} {n.image.size[0]}x{n.image.size[1]}")
                if n.type == "BSDF_PRINCIPLED":
                    alpha_linked = n.inputs["Alpha"].is_linked
        say(f"  material '{name}': alpha linked {alpha_linked}; blend {getattr(m, 'blend_method', '?')}; textures: " + "; ".join(tex))
    return lo, hi


def light_and_world(scene):
    sun = bpy.data.lights.new("v7_sun", "SUN")
    sun.color, sun.energy = SUN
    sun.angle = math.radians(3.0)                                               # a slightly soft sun: painted shadows have a soft edge
    ob = bpy.data.objects.new("v7_sun", sun)
    ob.rotation_euler = TO_LIGHT.to_track_quat("Z", "Y").to_euler()             # a sun shines along its own -Z
    scene.collection.objects.link(ob)
    world = bpy.data.worlds.new("v7_sky")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg is not None:
        bg.inputs["Color"].default_value = SKY[0] + (1.0,)
        bg.inputs["Strength"].default_value = SKY[1]
    scene.world = world


def camera(scene, lo, hi, pad_m=0.06):
    """An orthographic side camera framing the bounds (plus a margin); the foot (z = 0, the bounds' middle x) is the
    sprite's pivot. -> (width px, height px, pivot [x, y] in the image, 0..1 from the bottom-left)."""
    x0, x1 = lo.x - pad_m, hi.x + pad_m
    z0, z1 = min(lo.z, 0.0) - pad_m, hi.z + pad_m
    w, h = int(math.ceil((x1 - x0) * PPM / 4.0)) * 4, int(math.ceil((z1 - z0) * PPM / 4.0)) * 4
    wm, hm = w / PPM, h / PPM
    cd = bpy.data.cameras.new("v7_cam")
    cd.type = "ORTHO"
    cd.ortho_scale = max(wm, hm)
    cd.sensor_fit = "AUTO"
    cd.clip_start, cd.clip_end = 0.01, 500.0
    cam = bpy.data.objects.new("v7_cam", cd)
    scene.collection.objects.link(cam)
    cam.location = Vector((x0 + wm / 2, -100.0, z0 + hm / 2))
    cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)                         # looks along +Y; image right = +X, up = +Z
    scene.camera = cam
    r = scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    return w, h, [round(((lo.x + hi.x) / 2 - x0) / wm, 4), round((0.0 - z0) / hm, 4)]


def render_setup(scene, samples=64):
    r = scene.render
    r.engine = "CYCLES"                                                         # D-033: on this machine EEVEE's buffers sit in shared RAM; Cycles CPU peaks lower
    cy = scene.cycles
    cy.device = "CPU"
    cy.samples = samples
    cy.use_denoising = True
    if hasattr(cy, "denoiser"):
        cy.denoiser = "OPENIMAGEDENOISE"
    cy.max_bounces, cy.transparent_max_bounces = 4, 12                          # leaves cut by alpha need the transparent bounces
    r.film_transparent = True
    r.dither_intensity = 0.0
    r.use_compositing = False
    r.use_sequencer = False
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    r.image_settings.color_depth = "8"
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"
    try:
        scene.view_settings.look = "None"
    except TypeError:
        pass


def render(scene, name):
    os.makedirs(OUT, exist_ok=True)
    scene.render.filepath = os.path.join(OUT, name)
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    return time.time() - t0


def compositor_facts(scene):
    """What this Blender offers for the paint filter: read, not assumed (the API moved between 4.x and 5.x)."""
    say("Blender", bpy.app.version_string, "; engines:",
        [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items])
    say("scene.compositing_node_group:", hasattr(scene, "compositing_node_group"), "; scene.node_tree:", hasattr(scene, "node_tree"),
        "; scene.use_nodes:", hasattr(scene, "use_nodes"))
    try:
        tree = bpy.data.node_groups.new("v7_probe", "CompositorNodeTree")
        n = tree.nodes.new("CompositorNodeKuwahara")
        for i in n.inputs:
            dv = getattr(i, "default_value", None)
            try:
                dv = list(dv)
            except TypeError:
                pass
            say(f"  Kuwahara input '{i.name}' ({i.type}) default {dv}" + (f"; enum {[e.identifier for e in i.bl_rna.properties['default_value'].enum_items]}"
                                                                               if i.type == "MENU" and "default_value" in i.bl_rna.properties else ""))
        say("  Kuwahara properties:", [p.identifier for p in n.bl_rna.properties if not p.is_readonly and p.identifier not in
                                       ("name", "label", "location", "width", "height", "color", "select", "hide", "mute", "parent",
                                        "show_options", "show_preview", "show_texture", "use_custom_color", "warning_propagation",
                                        "location_absolute", "width_hidden", "bl_idname", "bl_label", "bl_description", "bl_icon",
                                        "bl_static_type", "bl_width_default", "bl_width_min", "bl_width_max", "bl_height_default",
                                        "bl_height_min", "bl_height_max")])
        say("  Kuwahara outputs:", [o.name for o in n.outputs])
        kinds = sorted(k for k in dir(bpy.types) if k.startswith("CompositorNode") and any(t in k for t in ("Output", "Composite", "Viewer", "Image", "RLayers", "Group")))
        say("  compositor in / out node types:", kinds)
        say("  tree interface:", hasattr(tree, "interface"))
        bpy.data.node_groups.remove(tree)
    except Exception as e:                                                      # noqa: BLE001  a probe reports, it does not stop the run
        say("  Kuwahara probe FAILED:", repr(e))


def probe():
    compositor_facts(fresh())                                                   # first: a killed render must not lose the facts
    for asset in ASSETS:
        if not os.path.isfile(os.path.join(VENDOR, asset, asset + ".gltf")):
            say(f"{asset}: NOT DOWNLOADED (blender/vendor_cc0/{asset}/)")
            continue
        scene = fresh()
        t0 = time.time()
        name, scale = PIECES[asset]
        obs = isolate(load(asset), name, scale)
        lo, hi = bounds(obs)
        say(f"{name} x{scale}: {hi.x - lo.x:.2f} m wide, {hi.y - lo.y:.2f} deep, z {lo.z:+.2f}..{hi.z:+.2f} m; "
            f"{sum(len(p.vertices) - 2 for p in obs[0].data.polygons)} tris")
        light_and_world(scene)
        w, h, pivot = camera(scene, lo, hi)
        render_setup(scene)
        sec = render(scene, f"{name}_plain_4x.png")
        say(f"  plain render {w}x{h} px at {PPM} px per metre (the game's size x4), pivot {pivot}: {sec:.1f} s render, {time.time() - t0:.1f} s with the import; "
            f"blender/preview/b258/{name}_plain_4x.png")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    mode = argv[0] if argv else "probe"
    if mode == "probe":
        probe()
    else:
        raise SystemExit(f"v7_paint_pass: unknown mode {mode}")
