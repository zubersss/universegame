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
sys.path.insert(0, HERE)                          # our own numpy modules (paint_v6, painted_v6, meridian.pngio); never a vendor folder
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
SUN = ((1.0, 0.93, 0.80), 6.5)                    # colour, strength (W/m2) (the probe at 4.0 / 0.55: the leaves near black)
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


# ---------------------------------------------------------------- STAGE B: the paint pass
# LEAD's ruling (13:4x) on my point: THE PAINT IS IN THE MATERIALS. The scan's colour texture is repainted with real
# brush strokes (LEAD's AI-painted stroke sheet as the brush: docs/art_sources/v6_painted/strokes_01.png; every stroke
# takes ONE colour from the scan under its middle and runs along the scan's own grain), and the same strokes, as small
# ridges of paint, are added to the normal map. So the brushwork sits ON the form: it turns with a leaf and holds still
# from frame to frame. The compositor's Kuwahara filter afterwards only softens edges.
STROKES = os.path.join(REPO, "docs", "art_sources", "v6_painted", "strokes_01.png")
KUWAHARA = (2.0, 4.0, 7.0)                        # the three settings of the edge-softening pass (the node's Size, px at 2x)
# (Run 1, 13:54: on the ROCK the strokes read at once as brushwork. On the PLANT, leaf dabs 30-60 texels long broke the
# leaf's fine vein stripes into camouflage blotches, and the scan's dark grey-green stood near black beside the old
# frame's plants; the filter at this size changed almost nothing. Now, for a leaf: thin LONG strokes along the veins,
# half the size; the scan's own fine detail laid back over the strokes (detail); the colour lifted toward a painter's
# green (gain, sat); and light let THROUGH the leaf (translucent). And for every piece a BRUSHED EDGE: edge_brush.)
PAINT = {"calathea_orbifolia_01": dict(kind="long", big=(9, 18, 7000), fine=(5, 9, 6000), ridge=1.2, detail=0.85, gain=1.6, sat=1.3, translucent=0.4),
         "rock_moss_set_01": dict(kind="dry", big=(14, 30, 4800), fine=(7, 14, 4200), ridge=2.0, detail=0.5, gain=1.15, sat=1.15, translucent=0.0)}
#        kind = which strokes of the sheet; big / fine = (half-length from, to, in texels; how many); ridge = the paint's relief in the normal map


def np_of(img):
    """A Blender image -> float32 H x W x 4, row 0 = top (a byte image's pixels are its stored display values, straight alpha)."""
    import numpy as np
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)[::-1].copy()


def read_png(path):
    img = bpy.data.images.load(path, check_existing=False)
    try:
        return np_of(img)
    finally:
        bpy.data.images.remove(img)


def write_png(path, arr):
    """float H x W x 4 (straight alpha, 0..1, row 0 = top) -> an 8-bit PNG by our own writer (fast to read back in numpy)."""
    import numpy as np
    from meridian import pngio
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return pngio.write_png(path, np.clip(np.rint(arr * 255.0), 0, 255).astype(np.uint8))


def image_from(name, arr, path, colorspace):
    """A numpy picture as a texture Blender can render from: written to `path` and loaded from it."""
    write_png(path, arr)
    img = bpy.data.images.load(path, check_existing=False)
    img.name = name
    img.colorspace_settings.name = colorspace
    return img


def shrink(arr, f, normal=False):
    """Block means of a straight-alpha picture (colour premultiplied for the mean; a normal map re-normalised)."""
    import numpy as np
    h, w = (arr.shape[0] // f) * f, (arr.shape[1] // f) * f
    a = arr[:h, :w]
    al = a[..., 3:4]
    pm = np.concatenate([a[..., :3] * al, al], axis=2).reshape(h // f, f, w // f, f, 4).mean(axis=(1, 3))
    al2 = pm[..., 3:4]
    rgb = np.where(al2 > 1e-4, pm[..., :3] / np.maximum(al2, 1e-4), 0.0)
    if normal:
        n = rgb * 2.0 - 1.0
        n /= np.maximum(np.sqrt((n * n).sum(axis=2, keepdims=True)), 1e-4)
        rgb = np.where(al2 > 1e-4, n * 0.5 + 0.5, 0.0)
    return np.concatenate([rgb, al2], axis=2).astype(np.float32)


def paint_textures(asset, mat, seed):
    """The material's colour and normal textures repainted (see above). -> seconds, strokes laid."""
    import numpy as np
    sys.path.insert(0, HERE)
    import paint_v6 as PT
    import painted_v6 as PV
    t0 = time.time()
    cfg = PAINT[asset]
    nodes = {}
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image:
            f = os.path.basename(n.image.filepath).lower()
            nodes["diff" if "_diff_" in f else "nor" if "_nor_" in f else "other"] = n
    diff, nor = np_of(nodes["diff"].image), np_of(nodes["nor"].image)
    h, w = diff.shape[:2]
    bank = PV.strokes(STROKES)
    rgb = diff[..., :3]
    base = np.dstack([PT.box(rgb[..., c], 3) for c in range(3)]).astype(np.float32)        # every stroke takes ONE colour: from a calmed copy of the scan
    lum = PT.box(rgb @ np.array([0.30, 0.59, 0.11], np.float32), 2)
    gy, gx = np.gradient(lum)
    j11, j22, j12 = PT.box(gx * gx, 6), PT.box(gy * gy, 6), PT.box(gx * gy, 6)
    along = (0.5 * np.arctan2(2 * j12, j11 - j22) + np.pi / 2).astype(np.float32)          # the scan's own grain: along its edges and veins
    ang = lambda x, y: float(along[min(max(int(y), 0), h - 1), min(max(int(x), 0), w - 1)])   # noqa: E731
    everywhere = np.ones((h, w), np.float32)
    noise = np.random.default_rng(seed + 7).uniform(0.25, 0.75, (h, w, 1)).astype(np.float32) * np.ones((1, 1, 3), np.float32)

    def lay(P, under):
        for a0, a1, n in (cfg["big"], cfg["fine"]):
            PV.brush(P, bank, under, everywhere, n, (a0, a1), angle=ang, spread=0.22, alpha=(0.8, 1.0), jitter=0.07, hue=0.014, kind=cfg["kind"])
    P = PT.Painting(w, h, seed, 1)                                                         # the colour: strokes over the calmed scan
    P.img[:] = base
    lay(P, base)
    H = PT.Painting(w, h, seed, 1)                                                         # the SAME strokes (the same seed) as heights: each a small ridge of paint
    H.img[:] = 0.5
    lay(H, noise)
    hgt = PT.box(H.img[..., 0], 1)
    gy, gx = np.gradient(hgt)
    n = nor[..., :3] * 2.0 - 1.0
    n[..., 0] -= cfg["ridge"] * gx
    n[..., 1] += cfg["ridge"] * gy                                                         # rows run down, the map's green runs up
    n /= np.maximum(np.sqrt((n * n).sum(axis=2, keepdims=True)), 1e-4)
    tex = os.path.join(OUT, "tex")
    one = np.ones((h, w, 1), np.float32)
    col = np.clip(P.img + cfg["detail"] * (rgb - base), 0, 1)                              # the scan's fine detail (veins, pores) back over the strokes
    lm = (col @ np.array([0.30, 0.59, 0.11], np.float32))[..., None]
    col = np.clip((lm + (col - lm) * cfg["sat"]) * cfg["gain"], 0, 1)                      # lifted toward a painter's colour
    nodes["diff"].image = image_from(asset + "_painted_diff", np.concatenate([col, one], axis=2), os.path.join(tex, asset + "_painted_diff.png"), "sRGB")
    nodes["nor"].image = image_from(asset + "_painted_nor", np.concatenate([n * 0.5 + 0.5, one], axis=2), os.path.join(tex, asset + "_painted_nor.png"), "Non-Color")
    for nd in mat.node_tree.nodes:                                                         # paint is matt: no plastic highlight
        if nd.type == "BSDF_PRINCIPLED":
            for key, val in (("Specular IOR Level", 0.12), ("Roughness", 0.9)):
                s = nd.inputs.get(key)
                if s is not None:
                    for lk in list(s.links):
                        mat.node_tree.links.remove(lk)
                    s.default_value = val
    if cfg.get("translucent"):                                                             # a leaf lets light through: lit from behind it glows
        nt = mat.node_tree
        outn = next((nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL"), None)
        bs = next((nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED"), None)
        if outn is not None and bs is not None:
            tr, mix = nt.nodes.new("ShaderNodeBsdfTranslucent"), nt.nodes.new("ShaderNodeMixShader")
            mix.inputs[0].default_value = cfg["translucent"]
            nt.links.new(nodes["diff"].outputs["Color"], tr.inputs["Color"])
            nt.links.new(bs.outputs[0], mix.inputs[1])
            nt.links.new(tr.outputs[0], mix.inputs[2])
            nt.links.new(mix.outputs[0], outn.inputs["Surface"])
    return time.time() - t0, P.count, nodes["nor"].image


def edge_brush(arr, kind="leaf", seed=23, per_px=0.14, size=(2.5, 5.5)):
    """THE BRUSHED EDGE (a still piece only: in screen space, so on a moving figure it would crawl): a render's silhouette
    is a perfect cut, a painting's is where the brush stopped. Strokes are laid ALONG the contour, each in the colour just
    inside it, a little over the edge; the alpha grows with them. arr: straight RGBA at the size it is laid (2x)."""
    import numpy as np
    import paint_v6 as PT
    import painted_v6 as PV
    h, w = arr.shape[:2]
    a = arr[..., 3]
    known = a > 0.5
    ext = arr[..., :3] * known[..., None]
    for r in (2, 4, 8, 14):                                                               # the colour bled outward, so a stroke over the edge has paint
        ba = PT.box(known.astype(np.float32), r)
        bc = np.dstack([PT.box(ext[..., c] * known, r) for c in range(3)])
        new = (~known) & (ba > 0.02)
        ext[new] = bc[new] / ba[new][:, None]
        known = known | new
    # (Run 2: 0.45 strokes a contour pixel, thin and long, fanned 0.3 rad off the contour: FUR. Stems two pixels wide were
    # all contour and swelled into fuzzy stalks. Now: a third as many, short blunt dabs lying ON the contour, and none
    # where the shape is thinner than a brush.)
    gy, gx = np.gradient(PT.box(a, 1))
    edge = (np.clip(np.hypot(gx, gy) * 4.0, 0, 1) * (PT.box(a, 3) > 0.42)).astype(np.float32)
    tang = (np.arctan2(gy, gx) + np.pi / 2).astype(np.float32)
    ang = lambda x, y: float(tang[min(max(int(y), 0), h - 1), min(max(int(x), 0), w - 1)])   # noqa: E731
    bank = PV.strokes(STROKES)
    n = int(float(edge.sum()) * per_px)
    P, A = PT.Painting(w, h, seed, 1), PT.Painting(w, h, seed, 1)                           # the same strokes twice: as colour, as coverage
    P.img[:] = ext
    A.img[:] = a[..., None]
    for canvas, under in ((P, ext.astype(np.float32)), (A, np.ones((h, w, 3), np.float32))):
        PV.brush(canvas, bank, under, edge, n, size, angle=ang, spread=0.07, alpha=(0.5, 0.85), jitter=0.05, hue=0.01, kind=kind)
    return np.concatenate([np.clip(P.img, 0, 1), np.clip(A.img[..., :1], 0, 1)], axis=2).astype(np.float32), n


def normal_material(src, nor_img):
    """A material that shows the surface's direction as the game's sprite normal map: red = to the right, green = up,
    blue = toward the viewer (the side camera: right +X, up +Z, the viewer at -Y), 0.5 = none; a back face is turned
    to the viewer."""
    m = bpy.data.materials.new(src.name + "_normals")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out, em = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeEmission")
    tex, nm = nt.nodes.new("ShaderNodeTexImage"), nt.nodes.new("ShaderNodeNormalMap")
    tex.image = nor_img
    sep, comb = nt.nodes.new("ShaderNodeSeparateXYZ"), nt.nodes.new("ShaderNodeCombineXYZ")
    absy = nt.nodes.new("ShaderNodeMath")
    absy.operation = "ABSOLUTE"
    enc = nt.nodes.new("ShaderNodeVectorMath")
    enc.operation = "MULTIPLY_ADD"
    enc.inputs[1].default_value = (0.5, 0.5, 0.5)
    enc.inputs[2].default_value = (0.5, 0.5, 0.5)
    L = nt.links.new
    L(tex.outputs["Color"], nm.inputs["Color"])
    L(nm.outputs["Normal"], sep.inputs[0])
    L(sep.outputs["X"], comb.inputs["X"])
    L(sep.outputs["Z"], comb.inputs["Y"])
    L(sep.outputs["Y"], absy.inputs[0])                                                    # |y|: toward the viewer, whichever way the face is wound
    L(absy.outputs[0], comb.inputs["Z"])
    L(comb.outputs[0], enc.inputs[0])
    L(enc.outputs[0], em.inputs["Color"])
    L(em.outputs[0], out.inputs["Surface"])
    return m


def kuwahara_np(arr, r):
    """The fallback, in numpy: the classic Kuwahara filter (of four windows round a pixel, the calmest one's mean)."""
    import numpy as np
    import paint_v6 as PT
    hgt = max(1, int(round(r / 2)))
    al = arr[..., 3:4]
    pm = np.concatenate([arr[..., :3] * al, al], axis=2)
    lum = pm[..., :3].sum(axis=2)
    mean = np.dstack([PT.box(pm[..., c], hgt) for c in range(4)])
    var = PT.box(lum * lum, hgt) - PT.box(lum, hgt) ** 2
    best, out = None, None
    for dy in (-hgt, hgt):
        for dx in (-hgt, hgt):
            v, mq = np.roll(var, (dy, dx), (0, 1)), np.roll(mean, (dy, dx), (0, 1))
            if best is None:
                best, out = v.copy(), mq.copy()
            else:
                pick = v < best
                best = np.where(pick, v, best)
                out = np.where(pick[..., None], mq, out)
    a2 = out[..., 3:4]
    return np.concatenate([np.where(a2 > 1e-4, out[..., :3] / np.maximum(a2, 1e-4), 0.0), a2], axis=2).astype(np.float32)


def kuwahara(src, dst, size):
    """The compositor's ANISOTROPIC Kuwahara on a picture file (no 3D is rendered): an Image node, the filter, the group's
    output. -> "node" or, if this Blender refuses, "numpy" (the classic filter, named as such on the sheet)."""
    try:
        img = bpy.data.images.load(src, check_existing=False)
        sc = bpy.data.scenes.new("v7_filter")
        cd = bpy.data.cameras.new("v7_filter_cam")
        cam = bpy.data.objects.new("v7_filter_cam", cd)
        sc.collection.objects.link(cam)
        sc.camera = cam
        render_setup(sc, samples=1)
        sc.cycles.use_denoising = False
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = img.size[0], img.size[1], 100
        tree = bpy.data.node_groups.new("v7_filter", "CompositorNodeTree")
        tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        src_n, kw, out = tree.nodes.new("CompositorNodeImage"), tree.nodes.new("CompositorNodeKuwahara"), tree.nodes.new("NodeGroupOutput")
        src_n.image = img
        kw.inputs["Size"].default_value = size
        tree.links.new(src_n.outputs["Image"], kw.inputs["Image"])
        tree.links.new(kw.outputs["Image"], out.inputs[0])
        sc.compositing_node_group = tree
        sc.render.use_compositing = True
        sc.render.filepath = dst
        bpy.ops.render.render(write_still=True, scene=sc.name)
        got = read_png(dst)
        if got.shape[:2] != (img.size[1], img.size[0]) or float(got[..., 3].max()) < 0.5:
            raise RuntimeError(f"the filter's picture is {got.shape}, alpha max {float(got[..., 3].max()):.2f}")
        write_png(dst, got)
        bpy.data.scenes.remove(sc)
        return "node"
    except Exception as e:                                                      # noqa: BLE001
        say(f"  the compositor's Kuwahara REFUSED ({e!r}): the numpy classic filter instead")
        write_png(dst, kuwahara_np(read_png(src), size))
        return "numpy"


def sway_pieces(ob, x0, z0, w, h):
    """The plant as pieces that can move: its mesh's separate parts, joined where one grows from another, each with its
    ROOT (its lowest point: the pivot it bends about) and its TIP. -> a dict for <name>_sway.json (px from the sprite's
    bottom-left at the render's size, and metres from the plant's foot)."""
    import numpy as np
    me = ob.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    mw = np.array(ob.matrix_world, np.float32)
    co = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
    parent = list(range(len(co)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    ed = np.empty(len(me.edges) * 2, np.int32)
    me.edges.foreach_get("vertices", ed)
    for a, b in ed.reshape(-1, 2):
        ra, rb = find(int(a)), find(int(b))
        if ra != rb:
            parent[ra] = rb
    roots = np.array([find(i) for i in range(len(co))])
    groups = [np.flatnonzero(roots == r) for r in np.unique(roots)]
    groups = [g for g in groups if len(g) >= 12]
    lows = [g[np.argmin(co[g, 2])] for g in groups]
    link = list(range(len(groups)))
    for i, lo in enumerate(lows):                                               # a part whose lowest point touches another part grows from it
        if co[lo, 2] < 0.06:
            continue
        best, bd = None, 0.03
        for j, g in enumerate(groups):
            if j != i:
                d = float(np.sqrt(((co[g] - co[lo]) ** 2).sum(axis=1)).min())
                if d < bd:
                    best, bd = j, d
        if best is not None:
            link[i] = best

    def top(i):
        seen = set()
        while link[i] != i and i not in seen:
            seen.add(i)
            i = link[i]
        return i
    pieces = {}
    for i, g in enumerate(groups):
        pieces.setdefault(top(i), []).append(g)
    out = []
    for k, gs in pieces.items():
        v = co[np.concatenate(gs)]
        root = v[np.argmin(v[:, 2])]
        tip = v[np.argmax(np.sqrt(((v - root) ** 2).sum(axis=1)))]
        px = lambda p: [round(float((p[0] - x0) * PPM), 1), round(float((p[2] - z0) * PPM), 1)]   # noqa: E731
        out.append({"root_m": [round(float(root[0]), 3), round(float(root[2]), 3)], "tip_m": [round(float(tip[0]), 3), round(float(tip[2]), 3)],
                    "root_px": px(root), "tip_px": px(tip), "length_m": round(float(np.sqrt(((tip - root) ** 2).sum())), 3),
                    "depth_m": round(float(v[:, 1].mean()), 3), "verts": int(len(v)),
                    "box_px": [round(float((v[:, 0].min() - x0) * PPM)), round(float((v[:, 2].min() - z0) * PPM)),
                               round(float((v[:, 0].max() - x0) * PPM)), round(float((v[:, 2].max() - z0) * PPM))]})
    out.sort(key=lambda p: -p["length_m"])
    return {"sprite_px": [w, h], "px_per_m": PPM, "units": "px from the sprite's bottom-left at this size; metres from the plant's foot (x right, z up)",
            "bend": "a piece bends about its root; the weight runs from 0 at the root to 1 at the tip (along root -> tip)", "pieces": out}


def paint():
    import json
    rows = []
    for asset in ASSETS:
        scene = fresh()
        name, scale = PIECES[asset]
        obs = isolate(load(asset), name, scale)
        ob = obs[0]
        lo, hi = bounds(obs)
        light_and_world(scene)
        w, h, pivot = camera(scene, lo, hi)
        render_setup(scene)
        t_plain = render(scene, f"{name}_plain_4x.png")
        mat = ob.material_slots[0].material
        t_tex, strokes, nor_img = paint_textures(asset, mat, 11)
        t_paint = render(scene, f"{name}_painted_4x.png")
        ob.material_slots[0].material = normal_material(mat, nor_img)          # the normal map of the PAINTED surface
        scene.view_settings.view_transform = "Raw"
        scene.cycles.use_denoising = False
        scene.cycles.samples = 24
        t_nor = render(scene, f"{name}_normal_4x.png")
        scene.view_settings.view_transform = "Standard"
        made = {}
        for tag in ("plain", "painted", "normal"):
            big = read_png(os.path.join(OUT, f"{name}_{tag}_4x.png"))
            for f, sfx in ((2, "2x"), (4, "1x")):
                write_png(os.path.join(OUT, f"{name}_{tag}_{sfx}.png"), shrink(big, f, normal=tag == "normal"))
            made[tag] = big.shape
        t0 = time.time()
        how = []
        for s in KUWAHARA:
            dst = os.path.join(OUT, f"{name}_k{s:g}_2x.png")
            how.append(kuwahara(os.path.join(OUT, f"{name}_painted_2x.png"), dst, s))
            write_png(os.path.join(OUT, f"{name}_k{s:g}_1x.png"), shrink(read_png(dst), 2))
        t_k = time.time() - t0
        t0 = time.time()
        br, n_edge = edge_brush(read_png(os.path.join(OUT, f"{name}_k{KUWAHARA[0]:g}_2x.png")))
        write_png(os.path.join(OUT, f"{name}_brushed_2x.png"), br)
        write_png(os.path.join(OUT, f"{name}_brushed_1x.png"), shrink(br, 2))
        t_edge = time.time() - t0
        x0, z0 = scene.camera.location.x - w / PPM / 2, scene.camera.location.z - h / PPM / 2
        extra = ""
        if asset.startswith("calathea"):
            sw = sway_pieces(ob, x0, z0, w, h)
            sw["pivot"] = pivot
            with open(os.path.join(OUT, f"{name}_sway.json"), "w", encoding="utf-8", newline="\n") as fh:
                json.dump(sw, fh, indent=1)
            extra = f"; {len(sw['pieces'])} sway pieces (the longest {sw['pieces'][0]['length_m']} m) -> {name}_sway.json"
        say(f"{name}: {w}x{h} px at {PPM} px per metre, pivot {pivot}; plain {t_plain:.1f} s; textures repainted with {strokes} strokes in {t_tex:.1f} s; "
            f"painted {t_paint:.1f} s; normal map {t_nor:.1f} s; the filter x{len(KUWAHARA)} ({'/'.join(how)}) {t_k:.1f} s{extra}")
        rows.append({"asset": asset, "piece": name, "scale": scale, "size_4x": [w, h], "px_per_m": PPM, "pivot": pivot,
                     "tris": sum(len(p.vertices) - 2 for p in ob.data.polygons), "strokes": strokes, "filter": how, "filter_sizes": list(KUWAHARA),
                     "edge_strokes": n_edge,
                     "seconds": {"plain": round(t_plain, 1), "repaint_textures": round(t_tex, 1), "painted": round(t_paint, 1),
                                 "normal": round(t_nor, 1), "filter_all": round(t_k, 1), "edge_brush": round(t_edge, 1)}})
    with open(os.path.join(OUT, "part1_report.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"blender": bpy.app.version_string, "engine": "Cycles CPU, 64 samples, denoised", "pieces": rows}, fh, indent=1)
    say("files in blender/preview/b258/: <piece>_{plain,painted,normal}_{4x,2x,1x}.png, <piece>_k<size>_{2x,1x}.png, tex/<asset>_painted_{diff,nor}.png, part1_report.json")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    mode = argv[0] if argv else "probe"
    if mode == "probe":
        probe()
    elif mode == "survey":                       # what every downloaded set holds (no render): to choose the frame's pieces
        for asset in sorted(os.listdir(VENDOR)):
            if not os.path.isfile(os.path.join(VENDOR, asset, asset + ".gltf")) or (len(argv) > 1 and asset not in argv[1:]):
                continue
            fresh()
            t0 = time.time()
            obs = load(asset)
            lo, hi = bounds(obs)
            parts = []
            for o in sorted(obs, key=lambda o: o.name):
                ol, oh = bounds([o])
                parts.append(f"{o.name.replace(asset, '~')} {oh.x - ol.x:.2f}x{oh.y - ol.y:.2f}x{oh.z - ol.z:.2f} m z{ol.z:+.2f} {sum(len(p.vertices) - 2 for p in o.data.polygons) // 1000}k")
            mats = sorted({s.material.name for o in obs for s in o.material_slots if s.material})
            say(f"{asset}: {len(obs)} objects over {hi.x - lo.x:.1f} m, {len(mats)} material(s), import {time.time() - t0:.1f} s: " + "; ".join(parts[:14])
                + (f"; ... {len(parts) - 14} more" if len(parts) > 14 else ""))
    elif mode == "paint":
        paint()
    elif mode == "edge":                         # only the brushed edge again, from the files a paint run left (no 3D render)
        import json
        rp = os.path.join(OUT, "part1_report.json")
        rep = json.load(open(rp, encoding="utf-8"))
        for pc in rep["pieces"]:
            t0 = time.time()
            br, n_edge = edge_brush(read_png(os.path.join(OUT, f"{pc['piece']}_k{KUWAHARA[0]:g}_2x.png")))
            write_png(os.path.join(OUT, f"{pc['piece']}_brushed_2x.png"), br)
            write_png(os.path.join(OUT, f"{pc['piece']}_brushed_1x.png"), shrink(br, 2))
            pc["edge_strokes"], pc["seconds"]["edge_brush"] = n_edge, round(time.time() - t0, 1)
            say(f"{pc['piece']}: the brushed edge again: {n_edge} strokes, {time.time() - t0:.1f} s")
        with open(rp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(rep, fh, indent=1)
    else:
        raise SystemExit(f"v7_paint_pass: unknown mode {mode}")
