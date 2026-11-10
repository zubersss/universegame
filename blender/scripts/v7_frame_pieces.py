"""B-258 part 3 (art v7, D-205; LEAD's ruling 11-10 14:1x): THE FRAME'S PIECES. Runs INSIDE Blender (bpy), through
tools/blender_scene.ps1. The camp's stage is PIECES COMPOSED, never one large render: every plant, rock, trunk and root is
rendered ALONE on alpha (one piece a render: a 2.3 megapixel frame was killed at 1.44 GB), and build_v7_frame.py (numpy)
composes them. Raw scans are read from blender/vendor_cc0/<asset>/ (CC0, git-ignored, glTF only); nothing goes to Assets.

  ... -- look [asset ...]     every piece of every downloaded set (or of the named ones), plain and small under the
                              painter's light, on one sheet: blender/preview/b258/look_sheet.png. To CHOOSE the pieces.
  ... -- piece <id> ...       the named pieces of PIECES as the frame uses them (see PIECES).

What part 1 did not have:
  * THE ALPHA MAPS. Poly Haven's glTF leaves out a plant's alpha map (the cut-out of its leaf cards), so a fern imports
    as solid cards. tools/blender_fetch_cc0.ps1 -Alphas fetches them; wire_alpha() puts each into its material.
  * A PAINTER'S LIGHT (LEAD): one warm sun, a cool sky from above and the lit ground's WARM BOUNCE from below (the world
    is two colours, mixed by the direction the light comes from); every material MATT (a glossy highlight is the 3D tell).
"""
import json
import math
import os
import sys
import time

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))         # blender/: review.py (labels on a sheet)
import v7_paint_pass as V  # noqa: E402  part 1's tools (fresh, load, bounds, read_png, write_png, shrink, kuwahara, edge_brush ...)

REPO, VENDOR = V.REPO, V.VENDOR
OUT = os.path.join(REPO, "blender", "preview", "b258")
LOOK = os.path.join(OUT, "look")
say = V.say

TO_LIGHT = Vector((0.58, -0.53, 0.62)).normalized()   # the frame's ONE light: from the upper right, a little toward the viewer
SUN = ((1.0, 0.90, 0.72), 6.0)                    # a warm sun (colour, W/m2)
SKY = ((0.55, 0.70, 0.92), 0.85)                  # the cool light of the sky, from above
BOUNCE = ((0.62, 0.50, 0.25), 0.55)               # the lit ground's light, from below: warm
SKIP = ("moss_01",)                               # pieces a centimetre across: nothing to place
HEAVY = ("island_tree_02",)                       # a million triangles: only when named, in a run of its own


def painters_light(scene):
    sun = bpy.data.lights.new("v7_sun", "SUN")
    sun.color, sun.energy = SUN
    sun.angle = math.radians(5.0)                                               # a soft-edged shadow, as a brush leaves it
    ob = bpy.data.objects.new("v7_sun", sun)
    ob.rotation_euler = TO_LIGHT.to_track_quat("Z", "Y").to_euler()
    scene.collection.objects.link(ob)
    world = bpy.data.worlds.new("v7_sky")
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out, mix = nt.nodes.new("ShaderNodeOutputWorld"), nt.nodes.new("ShaderNodeMixShader")
    sky, bounce = nt.nodes.new("ShaderNodeBackground"), nt.nodes.new("ShaderNodeBackground")
    sky.inputs["Color"].default_value, sky.inputs["Strength"].default_value = SKY[0] + (1.0,), SKY[1]
    bounce.inputs["Color"].default_value, bounce.inputs["Strength"].default_value = BOUNCE[0] + (1.0,), BOUNCE[1]
    tc, sep, mr = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeSeparateXYZ"), nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = -0.35, 0.25      # below the horizon: the ground's light
    L = nt.links.new
    L(tc.outputs["Generated"], sep.inputs[0])
    L(sep.outputs["Z"], mr.inputs["Value"])
    L(mr.outputs["Result"], mix.inputs[0])
    L(bounce.outputs[0], mix.inputs[1])
    L(sky.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs["Surface"])
    scene.world = world


def materials(obs):
    seen = {}
    for o in obs:
        for s in o.material_slots:
            if s.material:
                seen[s.material.name] = s.material
    return list(seen.values())


def wire_alpha(asset, mats):
    """<asset>/textures/<asset>[_part]_alpha_<res>.png into the Alpha of every material it belongs to (all of them, or
    those named for the part: a tree's "leaves"). -> the file names wired."""
    tdir = os.path.join(VENDOR, asset, "textures")
    done = []
    for fn in sorted(os.listdir(tdir)) if os.path.isdir(tdir) else ():
        low = fn.lower()
        if "alpha" not in low or not low.endswith(".png"):
            continue
        part = low[len(asset) + 1:].split("alpha")[0].strip("_")
        img = bpy.data.images.load(os.path.join(tdir, fn), check_existing=True)
        img.colorspace_settings.name = "Non-Color"
        for m in mats:
            if (part and part not in m.name.lower()) or not m.node_tree:
                continue
            nt = m.node_tree
            bs = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if bs is None:
                continue
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = img
            base = bs.inputs["Base Color"]
            if base.is_linked and base.links[0].from_node.type == "TEX_IMAGE" and base.links[0].from_node.inputs["Vector"].is_linked:
                nt.links.new(base.links[0].from_node.inputs["Vector"].links[0].from_socket, tex.inputs["Vector"])
            nt.links.new(tex.outputs["Color"], bs.inputs["Alpha"])
            done.append(f"{fn} -> {m.name}")
    return done


def matt(mats):
    """Paint is matt: no highlight, no sheen, no coat."""
    for m in mats:
        if not m.node_tree:
            continue
        for nd in m.node_tree.nodes:
            if nd.type == "BSDF_PRINCIPLED":
                for key, val in (("Specular IOR Level", 0.0), ("Roughness", 1.0), ("Metallic", 0.0), ("Sheen Weight", 0.0), ("Coat Weight", 0.0)):
                    s = nd.inputs.get(key)
                    if s is not None:
                        for lk in list(s.links):
                            m.node_tree.links.remove(lk)
                        s.default_value = val


def groups(obs):
    """A set's pieces: objects that share one origin (a pachira's bark and its leaves) are one piece. -> [[objects]]"""
    out = []
    for o in sorted(obs, key=lambda o: o.name):
        c = o.matrix_world.translation
        for g in out:
            if (g[0].matrix_world.translation - c).length < 0.02:
                g.append(o)
                break
        else:
            out.append([o])
    return out


def stand(obs, scale=1.0, yaw=0.0, roll=0.0):
    """The piece moved so its origin (a plant's root) stands on (0, 0); scaled; turned about the upright axis (yaw, degrees:
    another side of it toward the viewer); rolled about the viewing axis (roll: a lying log stood up), then set down on z = 0."""
    org = obs[0].matrix_world.translation.copy()
    M = Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Scale(scale, 4) @ Matrix.Translation(Vector((-org.x, -org.y, 0.0)))
    if roll:
        M = Matrix.Rotation(math.radians(roll), 4, "Y") @ M
    for o in obs:
        o.matrix_world = M @ o.matrix_world
    bpy.context.view_layer.update()
    if roll:
        lo, hi = V.bounds(obs)
        T = Matrix.Translation(Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)))
        for o in obs:
            o.matrix_world = T @ o.matrix_world
        bpy.context.view_layer.update()


def camera(scene, lo, hi, ppm, pad_m=0.04):
    """The orthographic side camera on the bounds at ppm px per metre. -> (w, h, pivot [x, y] 0..1 from the bottom-left:
    the piece's origin on the ground)."""
    x0, x1 = lo.x - pad_m, hi.x + pad_m
    z0, z1 = min(lo.z, 0.0) - pad_m, hi.z + pad_m
    w, h = int(math.ceil((x1 - x0) * ppm / 4.0)) * 4, int(math.ceil((z1 - z0) * ppm / 4.0)) * 4
    wm, hm = w / ppm, h / ppm
    cam = scene.camera
    if cam is None:
        cd = bpy.data.cameras.new("v7_cam")
        cd.type = "ORTHO"
        cd.sensor_fit = "AUTO"
        cd.clip_start, cd.clip_end = 0.01, 500.0
        cam = bpy.data.objects.new("v7_cam", cd)
        scene.collection.objects.link(cam)
        cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)
        scene.camera = cam
    cam.data.ortho_scale = max(wm, hm)
    cam.location = Vector((x0 + wm / 2, -100.0, z0 + hm / 2))
    r = scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    return w, h, [round((0.0 - x0) / wm, 4), round((0.0 - z0) / hm, 4)]


def tris(obs):
    return sum(len(p.vertices) - 2 for o in obs for p in o.data.polygons)


def look(only):
    """Every piece of every set, plain, about 300 px on its longer side. One import per asset; the others of the set are
    hidden from the render while one piece is taken."""
    os.makedirs(LOOK, exist_ok=True)
    rows = []
    assets = [a for a in sorted(os.listdir(VENDOR)) if os.path.isfile(os.path.join(VENDOR, a, a + ".gltf"))]
    assets = [a for a in assets if (a in only) or (not only and a not in SKIP and a not in HEAVY)]
    extra = {"dead_tree_trunk_02": [("upright", dict(roll=90.0))], "dead_tree_trunk": [("upright", dict(roll=90.0))],
             "single_root": [("turned", dict(yaw=90.0))], "tree_stump_01": [("turned", dict(yaw=90.0))]}
    for asset in assets:
        t0 = time.time()
        scene = V.fresh()
        obs = V.load(asset)
        mats = materials(obs)
        wired = wire_alpha(asset, mats)
        matt(mats)
        painters_light(scene)
        V.render_setup(scene, samples=24)
        say(f"{asset}: {len(obs)} objects, {tris(obs)} triangles, import {time.time() - t0:.1f} s; alpha: {', '.join(wired) or 'none'}")
        for g in groups(obs):
            if max(o.dimensions.length for o in g) < 0.09:
                continue
            for tag, kw in [("", {})] + extra.get(asset, []):
                keep = {o.name: o.matrix_world.copy() for o in g}
                for o in obs:
                    o.hide_render = o not in g
                stand(g, **kw)
                lo, hi = V.bounds(g)
                wm, hm = hi.x - lo.x, hi.z - min(lo.z, 0.0)
                ppm = min(1500.0, max(40.0, 300.0 / max(wm, hm)))
                w, h, pivot = camera(scene, lo, hi, ppm)
                name = g[0].name + ("_" + tag if tag else "")
                scene.render.filepath = os.path.join(LOOK, name + ".png")
                t1 = time.time()
                bpy.ops.render.render(write_still=True)
                rows.append({"name": name, "asset": asset, "w_m": round(wm, 2), "h_m": round(hi.z - lo.z, 2), "d_m": round(hi.y - lo.y, 2),
                             "under_m": round(-min(lo.z, 0.0), 2), "tris": tris(g), "px": [w, h], "sec": round(time.time() - t1, 1)})
                say(f"  {name}: {wm:.2f} m wide, {hi.z - lo.z:.2f} tall ({-min(lo.z, 0.0):.2f} under the ground line), {hi.y - lo.y:.2f} deep; "
                    f"{tris(g)} triangles; {w}x{h} px in {time.time() - t1:.1f} s")
                for o in g:
                    o.matrix_world = keep[o.name]
                bpy.context.view_layer.update()
    with open(os.path.join(LOOK, "look.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rows, fh, indent=1)
    look_sheet(rows)


def look_sheet(rows):
    import numpy as np
    import review
    paper, stage = np.array(review.PAPER, np.float32), np.array([0.665, 0.725, 0.571], np.float32)
    Wd, cells = 1920, []
    for r in rows:
        fg = V.read_png(os.path.join(LOOK, r["name"] + ".png"))
        c = np.tile(stage, (fg.shape[0] + 44, max(fg.shape[1] + 12, 300), 1)).astype(np.float32)
        y0, x0 = 38, (c.shape[1] - fg.shape[1]) // 2
        c[y0:y0 + fg.shape[0], x0:x0 + fg.shape[1]] = fg[..., :3] * fg[..., 3:4] + c[y0:y0 + fg.shape[0], x0:x0 + fg.shape[1]] * (1 - fg[..., 3:4])
        review._label(c, r["name"][:46], 3, 3, scale=1)
        review._label(c, f"{r['w_m']:g} x {r['h_m']:g} m, {r['d_m']:g} deep, {r['tris'] // 1000}k tris", 3, 19, scale=1)
        cells.append(c)
    out, cur, x = [], [], 0
    for c in cells:
        if cur and x + c.shape[1] > Wd:
            out.append(cur)
            cur, x = [], 0
        cur.append(c)
        x += c.shape[1] + 8
    out.append(cur)
    bands = []
    for cs in out:
        H = max(c.shape[0] for c in cs)
        band = np.tile(paper, (H + 8, Wd, 1)).astype(np.float32)
        x = 0
        for c in cs:
            band[H - c.shape[0]:H, x:x + c.shape[1]] = c
            x += c.shape[1] + 8
        bands.append(band)
    img = np.vstack(bands)
    V.write_png(os.path.join(OUT, "look_sheet.png"), np.concatenate([img, np.ones(img.shape[:2] + (1,), np.float32)], axis=2))
    say(f"look sheet: blender/preview/b258/look_sheet.png {img.shape[1]}x{img.shape[0]}, {len(rows)} pieces")


# ---------------------------------------------------------------- the pieces the frame uses
# Chosen from the look sheet (11-10 14:33, 64 pieces). A plant may be scaled up to x3 (LEAD): these are house-plant scans
# and the camp stands in a forest. ppm = the px per metre a piece is rendered and painted at: 384 for the play plane
# (the game's 96 x4, 128 x3; the foreground layer uses the same pictures at 2-3x life size), less for what stands back.
# NOT USED, and why: pachira_aquatica_01_bark_a (a braided trunk: a pot plant); anthurium d/e/f and calathea c/d/e (the
# same plants smaller); grass tiny_* (a blade or two); moss_01 (pieces a centimetre across); rock_moss_set_01 (ochre
# boulders: a second colour key beside set_02's grey and moss).
PDIR = os.path.join(OUT, "pieces")
TEX = os.path.join(OUT, "tex3")
PIECES = {
    "calathea_a": dict(asset="calathea_orbifolia_01", ob="calathea_orbifolia_01_a", scale=2.5, kind="leaf"),
    "calathea_b": dict(asset="calathea_orbifolia_01", ob="calathea_orbifolia_01_b", scale=2.5, kind="leaf"),
    "anthurium_a": dict(asset="anthurium_botany_01", ob="anthurium_botany_01_a", scale=2.5, kind="leaf"),
    "anthurium_b": dict(asset="anthurium_botany_01", ob="anthurium_botany_01_b", scale=2.5, kind="leaf"),
    "anthurium_c": dict(asset="anthurium_botany_01", ob="anthurium_botany_01_c", scale=2.5, kind="leaf"),
    "fern_a": dict(asset="fern_02", ob="fern_02_a", scale=2.5, kind="leaf"),
    "fern_b": dict(asset="fern_02", ob="fern_02_b", scale=2.5, kind="leaf"),
    "fern_c": dict(asset="fern_02", ob="fern_02_c", scale=2.2, kind="leaf"),
    "grass_mid": dict(asset="grass_medium_01", ob="grass_medium_01_mid_a_LOD0", scale=3.0, kind="grass"),
    "grass_wide": dict(asset="grass_medium_01", ob="grass_medium_01_large_a_LOD0", scale=3.0, kind="grass"),
    "grass_seed": dict(asset="grass_medium_01", ob="grass_medium_01_tall_c_LOD0", scale=3.0, kind="grass"),
    "grass_dry": dict(asset="grass_medium_02", ob="grass_medium_02_e", scale=3.0, kind="grass"),
    "weed": dict(asset="shrub_03", ob="shrub_03_a", scale=3.0, kind="grass"),
    "rock_big": dict(asset="rock_moss_set_02", ob="rock_moss_set_02_rock11", kind="rock"),
    "rock_low": dict(asset="rock_moss_set_02", ob="rock_moss_set_02_rock08", kind="rock"),
    "rock_flat": dict(asset="rock_moss_set_02", ob="rock_moss_set_02_rock12", kind="rock"),
    "stump": dict(asset="tree_stump_01", ob="tree_stump_01", scale=1.6, kind="bark"),
    "root": dict(asset="single_root", ob="single_root", scale=1.5, yaw=90.0, kind="bark"),
    "log": dict(asset="dead_tree_trunk_02", ob="dead_tree_trunk_02", ppm=256, kind="bark"),
    "snag": dict(asset="dead_tree_trunk_02", ob="dead_tree_trunk_02", scale=1.6, roll=90.0, ppm=192, kind="bark"),
    "tree_tall": dict(asset="pachira_aquatica_01", ob="pachira_aquatica_01_bark_d", scale=3.0, ppm=128, kind="tree"),
    "tree_bushy": dict(asset="pachira_aquatica_01", ob="pachira_aquatica_01_bark_c", scale=3.0, ppm=160, kind="tree"),
    "tree_small": dict(asset="pachira_aquatica_01", ob="pachira_aquatica_01_bark_b", scale=3.0, ppm=192, kind="tree"),
}
# A FAR STAND: several trees in one small picture (the far veils: through the filter, then enlarged: soft is right).
STANDS = {
    "far_stand": dict(asset="pachira_aquatica_01", ppm=32, kind="far", items=[
        ("pachira_aquatica_01_bark_d", 5.0, 0.0, 0.0), ("pachira_aquatica_01_bark_c", 6.0, 5.5, 40.0), ("pachira_aquatica_01_bark_d", 4.2, 10.5, 110.0),
        ("pachira_aquatica_01_bark_b", 7.0, 14.5, 200.0), ("pachira_aquatica_01_bark_c", 5.0, 19.0, 150.0), ("pachira_aquatica_01_bark_d", 5.6, 24.0, 250.0),
        ("pachira_aquatica_01_bark_b", 6.0, 28.5, 60.0), ("pachira_aquatica_01_bark_c", 6.5, 33.0, 300.0)]),
}
# How a material's textures are repainted (texels of the 1k map): kind = the stroke of the sheet; big / fine / vein =
# (half-length from, to; how many on a fully covered map); up / down = the two values of a vein or a crack; ridge = the
# paint's relief in the normal map; gain / sat = the colour lifted toward a painter's; translucent = light through a leaf.
TEXPAINT = {
    "leaf": dict(kind="leaf", big=(12, 26, 2600), fine=(6, 12, 3200), vein=(7, 18, 5000), up=1.30, down=0.72, ridge=1.2, gain=1.5, sat=1.25, translucent=0.35),
    "grass": dict(kind="long", big=(10, 22, 2600), fine=(5, 10, 2600), vein=(6, 14, 2500), up=1.25, down=0.75, ridge=0.8, gain=1.35, sat=1.2, translucent=0.3),
    "rock": dict(kind="dry", big=(14, 30, 4800), fine=(7, 14, 4200), vein=(8, 20, 3000), up=1.22, down=0.74, ridge=2.0, gain=1.15, sat=1.15, translucent=0.0),
    "bark": dict(kind="dry", big=(14, 30, 4200), fine=(7, 14, 4200), vein=(8, 22, 5000), up=1.25, down=0.70, ridge=2.0, gain=1.25, sat=1.1, translucent=0.0),
}
GAIN = {"anthurium_botany_01": 2.1}               # a scan far darker than its neighbours (asset: the gain instead of its kind's)
# What is done to the rendered piece (v7_paint): the brush's sizes are half-lengths in px AT THE GAME'S 96 px per metre
# (multiplied by ppm / 96 where the piece is painted), so a stroke is the same size on the screen whatever the source.
POST = {
    "leaf": dict(steps=4, amount=0.75, kuw=1.0, brush="leaf", size=(2.2, 5.0), density=1.0, accents=1.0, acc=(1.8, 4.0), edge="leaf"),
    "grass": dict(steps=3, amount=0.6, kuw=0.5, brush="long", size=(2.0, 4.5), density=0.7, accents=0.0, acc=(1.5, 3.0), edge=None),
    "rock": dict(steps=4, amount=0.8, kuw=1.25, brush="dry", size=(2.5, 6.0), density=1.0, accents=0.8, acc=(2.0, 5.0), edge="dry"),
    "bark": dict(steps=4, amount=0.8, kuw=1.0, brush="dry", size=(2.2, 5.5), density=1.0, accents=1.0, acc=(2.0, 5.5), edge="dry"),
    "tree": dict(steps=4, amount=0.75, kuw=1.25, brush="leaf", size=(2.6, 5.5), density=1.0, accents=0.6, acc=(2.0, 4.0), edge="leaf"),
    "far": dict(steps=3, amount=0.85, kuw=9.0, brush="leaf", size=(9.0, 18.0), density=1.0, accents=0.0, acc=(2.0, 4.0), edge=None),
}                                                 # far: the filter and the brush do the BROAD work (a crown is a few strokes); it is enlarged afterwards


def tex_nodes(mat):
    nodes = {}
    if mat.node_tree:
        for n in mat.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image:
                f = os.path.basename(n.image.filepath).lower()
                key = "alpha" if "alpha" in f else "diff" if "_diff_" in f else "nor" if "_nor_" in f else None
                if key:
                    nodes[key] = n
    return nodes


def repaint(asset, mat, kind, seed=11):
    """THE PAINT IN THE MATERIAL (LEAD 13:3x), and now VEINS AND GRAIN AS STROKES IN TWO VALUES (LEAD 14:1x): the colour
    texture is laid again as strokes, each ONE colour from the calmed scan under its middle, along the scan's own grain;
    then the scan's fine lines (veins, cracks: what stands out from its neighbourhood) come back as thin long strokes, a
    value lighter or a value darker than the paint under them. The scan's photographic detail is NOT laid back. The same
    strokes, as ridges of paint, go into the normal map. Painted maps are kept in blender/preview/b258/tex3/ by the
    material's name and the settings, and used again by the next piece of the set. -> (seconds, strokes, "painted" or "kept")."""
    import hashlib
    import numpy as np
    import paint_v6 as PT
    import painted_v6 as PV
    import v7_paint as VP
    t0 = time.time()
    cfg = dict(TEXPAINT[kind])
    cfg["gain"] = GAIN.get(asset, cfg["gain"])
    nodes = tex_nodes(mat)
    if "diff" not in nodes:
        return 0.0, 0, "no colour map"
    tag = hashlib.sha1(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:8]
    pd, pn = os.path.join(TEX, f"{mat.name}_{tag}_diff.png"), os.path.join(TEX, f"{mat.name}_{tag}_nor.png")
    strokes, how = 0, "kept"
    if not (os.path.isfile(pd) and (os.path.isfile(pn) or "nor" not in nodes)):
        how = "painted"
        rgb = V.np_of(nodes["diff"].image)[..., :3]
        h, w = rgb.shape[:2]
        cover = np.ones((h, w), np.float32)
        if "alpha" in nodes:
            al = V.np_of(nodes["alpha"].image)[..., 0]
            if al.shape == (h, w):
                cover = (PT.box(al, 3) > 0.03).astype(np.float32)                           # the leaf cards and a little round them
        frac = max(0.2, float(cover.mean()))
        base = np.dstack([PT.box(rgb[..., c], 3) for c in range(3)]).astype(np.float32)
        lum = rgb @ VP.LUM
        along = VP.grain(PT.box(lum, 2), 6)
        ang = lambda x, y: float(along[min(max(int(y), 0), h - 1), min(max(int(x), 0), w - 1)])   # noqa: E731
        hp = lum - PT.box(lum, 4)
        s = float(np.percentile(np.abs(hp[cover > 0.5]), 90)) + 1e-4
        light, dark = np.clip(hp / s - 0.45, 0, 1) * cover, np.clip(-hp / s - 0.45, 0, 1) * cover
        tot = float(light.sum() + dark.sum()) + 1e-3
        bank = VP.bank()

        def lay(P, under, under_up, under_dn):
            for a0, a1, n in (cfg["big"], cfg["fine"]):
                PV.brush(P, bank, under, cover, int(n * frac), (a0, a1), angle=ang, spread=0.22, alpha=(0.8, 1.0), jitter=0.07, hue=0.014, kind=cfg["kind"])
            a0, a1, n = cfg["vein"]
            for mask, und in ((dark, under_dn), (light, under_up)):
                PV.brush(P, bank, und, mask, int(n * frac * float(mask.sum()) / tot), (a0, a1), angle=ang, spread=0.07, alpha=(0.7, 0.95), jitter=0.02, hue=0.004, kind="long")
        P = PT.Painting(w, h, seed, 1)
        P.img[:] = base
        lay(P, base, np.clip(base * cfg["up"], 0, 1), base * cfg["down"])
        strokes = P.count
        lm = (P.img @ VP.LUM)[..., None]
        col = np.clip((lm + (P.img - lm) * cfg["sat"]) * cfg["gain"], 0, 1)
        one = np.ones((h, w, 1), np.float32)
        V.write_png(pd, np.concatenate([col, one], axis=2))
        if "nor" in nodes:
            nor = V.np_of(nodes["nor"].image)[..., :3]
            if nor.shape[:2] == (h, w):
                noise = np.random.default_rng(seed + 7).uniform(0.3, 0.7, (h, w, 1)).astype(np.float32) * np.ones((1, 1, 3), np.float32)
                H = PT.Painting(w, h, seed, 1)                                              # the SAME strokes (the same seed) as heights
                H.img[:] = 0.5
                lay(H, noise, np.clip(noise + 0.25, 0, 1), np.clip(noise - 0.25, 0, 1))
                gy, gx = np.gradient(PT.box(H.img[..., 0], 1))
                n = nor * 2.0 - 1.0
                n[..., 0] -= cfg["ridge"] * gx
                n[..., 1] += cfg["ridge"] * gy
                n /= np.maximum(np.sqrt((n * n).sum(axis=2, keepdims=True)), 1e-4)
                V.write_png(pn, np.concatenate([n * 0.5 + 0.5, one], axis=2))
    img = bpy.data.images.load(pd, check_existing=True)
    img.colorspace_settings.name = "sRGB"
    nodes["diff"].image = img
    if "nor" in nodes and os.path.isfile(pn):
        img = bpy.data.images.load(pn, check_existing=True)
        img.colorspace_settings.name = "Non-Color"
        nodes["nor"].image = img
    if cfg["translucent"]:
        leaf_shader(mat, nodes, cfg["translucent"])
    return time.time() - t0, strokes, how


def leaf_shader(mat, nodes, amount):
    """A leaf lets light through: its paint part translucent; the cut-out (the alpha map) applied to the whole of it."""
    nt = mat.node_tree
    outn = next((nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL"), None)
    bs = next((nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED"), None)
    if outn is None or bs is None or any(nd.type == "BSDF_TRANSLUCENT" for nd in nt.nodes):
        return
    tr, mix = nt.nodes.new("ShaderNodeBsdfTranslucent"), nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = amount
    nt.links.new(nodes["diff"].outputs["Color"], tr.inputs["Color"])
    nt.links.new(bs.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    last = mix.outputs[0]
    al = bs.inputs["Alpha"]
    if al.is_linked:
        src = al.links[0].from_socket
        nt.links.remove(al.links[0])
        al.default_value = 1.0
        clear, cut = nt.nodes.new("ShaderNodeBsdfTransparent"), nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(src, cut.inputs[0])
        nt.links.new(clear.outputs[0], cut.inputs[1])
        nt.links.new(last, cut.inputs[2])
        last = cut.outputs[0]
    nt.links.new(last, outn.inputs["Surface"])


def brushed_edge(arr, kind, k, seed=23):
    """Part 1's brushed edge (v7_paint_pass.edge_brush) at any size: k = this picture's px per metre / 192 (the size the
    first one was tuned at). Short blunt dabs lying ON the contour, each in the colour just inside it; none where the
    shape is thinner than a brush."""
    import numpy as np
    import paint_v6 as PT
    import painted_v6 as PV
    import v7_paint as VP
    h, w = arr.shape[:2]
    a = arr[..., 3]
    ext = VP.bleed(arr, radii=tuple(max(1, int(round(r * k))) for r in (2, 4, 8, 14)))
    gy, gx = np.gradient(PT.box(a, max(1, int(round(k)))))
    edge = (np.clip(np.hypot(gx, gy) * 4.0 * k, 0, 1) * (PT.box(a, max(1, int(round(3 * k)))) > 0.42)).astype(np.float32)
    tang = (np.arctan2(gy, gx) + np.pi / 2).astype(np.float32)
    ang = lambda x, y: float(tang[min(max(int(y), 0), h - 1), min(max(int(x), 0), w - 1)])   # noqa: E731
    n = int(float(edge.sum()) * 0.14 / (k * k))
    P, A = PT.Painting(w, h, seed, 1), PT.Painting(w, h, seed, 1)
    P.img[:] = ext
    A.img[:] = a[..., None]
    for canvas, under in ((P, ext), (A, np.ones((h, w, 3), np.float32))):
        PV.brush(canvas, VP.bank(), under, edge, n, (2.5 * k, 5.5 * k), angle=ang, spread=0.07, alpha=(0.5, 0.85), jitter=0.05, hue=0.01, kind=kind)
    return np.concatenate([np.clip(P.img, 0, 1), np.clip(A.img[..., :1], 0, 1)], axis=2).astype(np.float32), n


def finish(pid, kind, ppm, render_path):
    """The rendered piece painted (v7_paint: fewer flatter values, the filter, the brush, veins as strokes, a brushed edge)
    -> pieces/<id>.png at the size it was rendered. -> a dict of what was done."""
    import v7_paint as VP
    K, g = POST[kind], ppm / 96.0
    t0 = time.time()
    arr = V.read_png(render_path)
    flat = VP.flatten_values(arr, steps=K["steps"], amount=K["amount"])
    fp, kp = os.path.join(PDIR, pid + "_flat.png"), os.path.join(PDIR, pid + "_filter.png")
    V.write_png(fp, flat)
    how = V.kuwahara(fp, kp, max(1.0, K["kuw"] * g))
    soft = V.read_png(kp)
    out, n = VP.paint_over(soft, kind=K["brush"], size=(K["size"][0] * g, K["size"][1] * g), density=K["density"], accents=K["accents"],
                           acc_size=(K["acc"][0] * g, K["acc"][1] * g), detail=flat)
    n_edge = 0
    if K["edge"]:
        out, n_edge = brushed_edge(out, K["edge"], ppm / 192.0)
    V.write_png(os.path.join(PDIR, pid + ".png"), out)
    for p in (fp, kp):
        os.remove(p)
    return {"filter": how, "strokes": n, "edge_strokes": n_edge, "paint_s": round(time.time() - t0, 1)}


def piece(ids, plain=False):
    """The named pieces, one a render. plain = the scan as it is under the same light (pieces/<id>_plain.png): the
    'before' of the sheet; else painted materials, the render, then finish()."""
    os.makedirs(PDIR, exist_ok=True)
    os.makedirs(TEX, exist_ok=True)
    by_asset = {}
    for pid in ids:
        if pid not in PIECES:
            raise SystemExit(f"v7_frame_pieces: no piece '{pid}' (have: {', '.join(PIECES)})")
        by_asset.setdefault(PIECES[pid]["asset"], []).append(pid)
    for asset, pids in by_asset.items():
        scene = V.fresh()
        obs = V.load(asset)
        mats = materials(obs)
        wire_alpha(asset, mats)
        matt(mats)
        painters_light(scene)
        V.render_setup(scene)
        gs = groups(obs)
        painted = {}
        for pid in pids:
            cfg = PIECES[pid]
            g = next((x for x in gs if any(o.name == cfg["ob"] for o in x)), None)
            if g is None:
                raise SystemExit(f"v7_frame_pieces: {asset} has no object '{cfg['ob']}'")
            tex_s, tex_n = 0.0, 0
            if not plain:
                for m in materials(g):
                    if m.name not in painted:
                        mk = cfg["kind"] if cfg["kind"] != "tree" else ("bark" if "bark" in m.name.lower() else "leaf")
                        painted[m.name] = repaint(asset, m, mk)
                        say(f"  material {m.name}: {painted[m.name][2]} ({painted[m.name][1]} strokes, {painted[m.name][0]:.1f} s)")
                        tex_s, tex_n = tex_s + painted[m.name][0], tex_n + painted[m.name][1]
            keep = {o.name: o.matrix_world.copy() for o in g}
            for o in obs:
                o.hide_render = o not in g
            stand(g, cfg.get("scale", 1.0), cfg.get("yaw", 0.0), cfg.get("roll", 0.0))
            lo, hi = V.bounds(g)
            ppm = cfg.get("ppm", 384)
            w, h, pivot = camera(scene, lo, hi, ppm)
            rp = os.path.join(PDIR, pid + ("_plain.png" if plain else "_render.png"))
            scene.render.filepath = rp
            t1 = time.time()
            bpy.ops.render.render(write_still=True, scene=scene.name)
            t_r = time.time() - t1
            meta = {"id": pid, "asset": asset, "objects": [o.name for o in g], "scale": cfg.get("scale", 1.0), "yaw": cfg.get("yaw", 0.0),
                    "roll": cfg.get("roll", 0.0), "kind": cfg["kind"], "px_per_m": ppm, "size_px": [w, h], "pivot": pivot,
                    "width_m": round(hi.x - lo.x, 3), "height_m": round(hi.z, 3), "under_m": round(-min(lo.z, 0.0), 3), "depth_m": round(hi.y - lo.y, 3),
                    "tris": tris(g), "render_s": round(t_r, 1), "texture_s": round(tex_s, 1), "texture_strokes": tex_n}
            if plain:
                say(f"{pid} PLAIN: {w}x{h} px at {ppm} px per metre in {t_r:.1f} s")
            else:
                meta.update(finish(pid, cfg["kind"], ppm, rp))
                os.remove(rp)
                if cfg["kind"] in ("leaf", "grass") and len(g) == 1 and tris(g) < 20000:      # the parts that can sway: a root and a tip each
                    V.PPM = ppm
                    cam = scene.camera
                    sw = V.sway_pieces(g[0], cam.location.x - w / ppm / 2, cam.location.z - h / ppm / 2, w, h)
                    meta["sway"] = sw["pieces"]
                with open(os.path.join(PDIR, pid + ".json"), "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(meta, fh, indent=1)
                say(f"{pid}: {meta['width_m']} x {meta['height_m']} m, {w}x{h} px at {ppm} px per metre, pivot {pivot}; render {t_r:.1f} s; "
                    f"the brush {meta['strokes']} strokes + {meta['edge_strokes']} on the edge in {meta['paint_s']} s (filter: {meta['filter']})"
                    + (f"; {len(meta['sway'])} sway parts" if "sway" in meta else ""))
            for o in g:
                o.matrix_world = keep[o.name]
            bpy.context.view_layer.update()


def stand_piece(ids):
    """A far stand: copies of a set's trees (the mesh shared), each scaled, turned and set along x, in ONE small picture."""
    os.makedirs(PDIR, exist_ok=True)
    for sid in ids:
        cfg = STANDS[sid]
        scene = V.fresh()
        obs = V.load(cfg["asset"])
        mats = materials(obs)
        wire_alpha(cfg["asset"], mats)
        matt(mats)
        painters_light(scene)
        V.render_setup(scene)
        gs = groups(obs)
        copies = []
        for name, scale, x, yaw in cfg["items"]:
            g = next(x_ for x_ in gs if any(o.name == name for o in x_))
            org = g[0].matrix_world.translation.copy()
            M = Matrix.Translation(Vector((x, 0.0, 0.0))) @ Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Scale(scale, 4) @ Matrix.Translation(Vector((-org.x, -org.y, 0.0)))
            for o in g:
                c = o.copy()
                scene.collection.objects.link(c)
                c.matrix_world = M @ o.matrix_world
                copies.append(c)
        for o in obs:
            o.hide_render = True
        bpy.context.view_layer.update()
        lo, hi = V.bounds(copies)
        ppm = cfg["ppm"]
        w, h, pivot = camera(scene, lo, hi, ppm, pad_m=0.3)
        rp = os.path.join(PDIR, sid + "_render.png")
        scene.render.filepath = rp
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        t_r = time.time() - t1
        meta = {"id": sid, "asset": cfg["asset"], "kind": cfg["kind"], "px_per_m": ppm, "size_px": [w, h], "pivot": pivot,
                "width_m": round(hi.x - lo.x, 3), "height_m": round(hi.z, 3), "under_m": 0.0, "trees": len(cfg["items"]), "tris": tris(copies), "render_s": round(t_r, 1)}
        meta.update(finish(sid, cfg["kind"], ppm, rp))
        os.remove(rp)
        with open(os.path.join(PDIR, sid + ".json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(meta, fh, indent=1)
        say(f"{sid}: {len(cfg['items'])} trees over {meta['width_m']} m, {w}x{h} px at {ppm} px per metre; render {t_r:.1f} s; the brush {meta['strokes']} strokes in {meta['paint_s']} s")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    mode = argv[0] if argv else "look"
    if mode == "look":
        look(argv[1:])
    elif mode in ("piece", "plain"):
        unknown = [a for a in argv[1:] if a not in PIECES and a not in STANDS]
        if unknown:
            raise SystemExit(f"v7_frame_pieces: no piece {unknown} (have: {', '.join(list(PIECES) + list(STANDS))})")
        piece([a for a in argv[1:] if a in PIECES] if argv[1:] else list(PIECES), plain=mode == "plain")
        if mode == "piece":
            stand_piece([a for a in argv[1:] if a in STANDS])
    elif mode == "stand":
        stand_piece(argv[1:] or list(STANDS))
    else:
        raise SystemExit(f"v7_frame_pieces: unknown mode {mode}")
