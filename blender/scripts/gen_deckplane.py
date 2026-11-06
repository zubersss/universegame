"""B-097 deck planes (contract v2.4 section 9, depth bands: "Giants: deck<n>.glb translucent
cloud planes"). A giant's cloud column has no ground: each deck (jupiter_deck1..3, jupiter_deep)
is three translucent planes, deck_far / deck_mid / deck_near, that UNITY parks at the far,
mid and near depth-band distances. Each plane is a 256 m x 128 m quad (one period in x) whose
colour map is a painted cumulus bank from gen_backdrop3d.cloud_bank (the B-048/B-055 Jupiter
banks: belts and zones, streaks, lightning) with the bank silhouette in the alpha channel, so
the sky dome and the planes behind show through the gaps. The painter is periodic in x by
construction, so the plane tiles every 256 m.

Manifest entry: {"key": "backgrounds/jupiter_deck1/deck_far", "deck_plane": true,
"sky_preset": "jupiter_deck1", "bank": 0, "seed": 9601, ["crush": true]}. `bank` indexes the
preset's banks (0 = the far, haziest bank, 2 = the near one). `crush` (jupiter_deep near plane)
adds the Crush band: a dark-red glow across the bottom of the plane (colour + an emission map)
with alpha so it reads through the gaps (B-055).

Outputs beside the glb: <variant>_color.png (RGBA 2048x1024), <variant>_emission.png when the
crush band is on, <variant>.json ("alpha": "map", "unlit": true: the painter bakes the Sun; UNITY
renders these planes unlit, alpha-blended, double-sided). The glb holds a 2-triangle quad with
authored UVs, origin at the bottom centre of the plane (origin_rule "band"), exported facing
glTF -X like every model (D-065).
"""
import json
import math
import os

import numpy as np

import gen_backdrop3d as GB3
from meridian import pngio

WIDTH_M, HEIGHT_M = 256.0, 128.0


def paint(entry):
    """RGBA float HxWx4 (2048x1024) plus an optional emission HxWx3 for the crush band."""
    P = GB3.PRESETS[entry["sky_preset"]]
    spec = P["banks"][int(entry.get("bank", 0))]
    img = GB3.cloud_bank(P, spec, int(entry["seed"]), False)
    emission = None
    if entry.get("crush") and P.get("crush"):
        pos, width, col = P["crush"]
        H = img.shape[0]
        yy = (np.arange(H, dtype=np.float32) / H)[:, None]
        g = np.exp(-((yy - pos) / width) ** 2)                      # the band, soft above and below
        g = g * (0.85 + 0.15 * GB3.fft_noise(np.random.default_rng(int(entry["seed"]) + 1), H, img.shape[1], 40, 400, 1.2))
        c = np.array(col, np.float32) / 255.0
        img[..., :3] = np.clip(img[..., :3] * (1 - 0.6 * g[..., None]) + c * g[..., None] * 1.1, 0, 1)
        img[..., 3] = np.maximum(img[..., 3], np.clip(g * 0.85, 0, 1))
        emission = np.clip(g[..., None] * c * 0.9, 0, 1)
    return img, emission


def quad_glb(path, key):
    """A 256 x 128 m quad in the x-z plane (Blender z up), bottom centre at the origin, normal
    toward the camera side (-Y), UV (0,0)-(1,1), colour map with alpha, double-sided, unlit-ish."""
    import bpy
    from meridian import model
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    me = bpy.data.meshes.new("deck_plane")
    w, h = WIDTH_M / 2, HEIGHT_M
    me.from_pydata([(-w, 0, 0), (w, 0, 0), (w, 0, h), (-w, 0, h)], [], [(0, 3, 2, 1)])
    me.update()
    uv = me.uv_layers.new(name="UVMap").data
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = ((v.x + w) / WIDTH_M, v.z / HEIGHT_M)
    ob = bpy.data.objects.new("deck_plane", me)
    bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new("deck_plane")
    m.use_nodes = True
    m.use_backface_culling = False
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        try:
            setattr(m, attr, val)
        except (AttributeError, TypeError):
            pass
    pr = m.node_tree.nodes["Principled BSDF"]
    pr.inputs["Roughness"].default_value = 1.0
    me.materials.append(m)
    model.export_glb(path, ob, None)
    return ob


def export_deck_plane(entry, art_dir, preview_dir, stamp):
    cat, name, variant = entry["key"].split("/")
    out_dir = os.path.join(art_dir, cat, name)
    os.makedirs(out_dir, exist_ok=True)
    img, emission = paint(entry)
    cpath = os.path.join(out_dir, f"{variant}_color.png")
    pngio.write_png(cpath, pngio.to_u8(np.clip(img, 0, 1)))
    maps = ["color"]
    if emission is not None:
        pngio.write_png(os.path.join(out_dir, f"{variant}_emission.png"),
                        np.dstack([pngio.to_u8(emission), np.full(emission.shape[:2], 255, np.uint8)]))
        maps.append("emission")
    glb = os.path.join(out_dir, f"{variant}.glb")
    quad_glb(glb, entry["key"])
    meta = {"key": entry["key"], "format": "glb", "contract": "v2.4", "deck_plane": True,
            "facing": "+X in Unity (exported facing glTF -X, D-065)", "up": "+Y", "units": "m", "origin": "band",
            "width_m": WIDTH_M, "height_m": HEIGHT_M, "period_m": WIDTH_M, "triangles": 2, "lod1_triangles": None,
            "texture": [img.shape[1], img.shape[0]], "maps": maps, "alpha": "map", "unlit": True, "double_sided": True,
            "depth": variant.split("_")[-1], "bank": int(entry.get("bank", 0)), "crush": bool(entry.get("crush")),
            "fps": 30, "clips": [], "atlas": None, "vertex_color": None, "sockets": []}
    with open(os.path.join(out_dir, f"{variant}.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    # Review evidence: the plane over the deck's haze colour (what the sky dome shows behind it),
    # and, on the near plane, the three planes stacked (near over mid over far) as in the game.
    P = GB3.PRESETS[entry["sky_preset"]]
    hz = np.array(P["haze"], np.float32) / 255.0
    sheet = _over(np.broadcast_to(hz, img.shape[:2] + (3,)).copy(), img)[::2, ::2]
    stamp(sheet, cpath)
    out = os.path.join(preview_dir, f"review_{entry['key'].replace('/', '_')}.png")
    pngio.write_png(out, np.dstack([pngio.to_u8(np.clip(sheet, 0, 1)), np.full(sheet.shape[:2], 255, np.uint8)]))
    stack = None
    if variant.endswith("near"):
        layers = [os.path.join(out_dir, f"deck_{d}_color.png") for d in ("far", "mid")]
        if all(os.path.isfile(p) for p in layers):
            comp = np.broadcast_to(hz, img.shape[:2] + (3,)).copy()
            for p in layers:
                comp = _over(comp, pngio.read_png(p))
            comp = _over(comp, img)[::2, ::2]
            stamp(comp, cpath)
            stack = os.path.join(preview_dir, f"review_{cat}_{name}_stack.png")
            pngio.write_png(stack, np.dstack([pngio.to_u8(np.clip(comp, 0, 1)), np.full(comp.shape[:2], 255, np.uint8)]))
    return {"glb": glb, "review": out, "stack": stack, "maps": maps,
            "coverage": round(float(img[..., 3].mean()), 3), "seam": _seam(img)}


def _over(base_rgb, rgba):
    a = rgba[..., 3:4]
    return base_rgb * (1 - a) + rgba[..., :3] * a


def _seam(img):
    """Left/right edge mismatch (mean abs, /255 units) of the RGBA: 0 when the paint is periodic."""
    return round(float(np.abs(img[:, 0] - img[:, -1]).mean() * 255), 2)
