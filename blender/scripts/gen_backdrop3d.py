"""Rendered parallax backgrounds (B-010 rework, Bible §9): each layer is a real Blender scene,
lit by a sun from the upper-right and rendered with EEVEE, called by render.py as a generator.

  layer0 far : painted sky (gen_backdrop.sky_rgb) + a rendered 3D mountain heightfield
  layer1 mid : rendered forested hills (instanced tree prototypes), valley fog, transparent sky
  layer2 near: rendered forest edge: full trees, shrubs and grass tufts on a heightfield

Trees are built from scratch: broadleaf = branching skeleton through a Skin modifier (organic
trunk and limbs) carrying noise-displaced leaf clusters, each cluster tinted by Object Info
Random; conifer = trunk with stacked drooping, displaced whorls. Self-shadowing gives leaf
masses internal light and shadow; displacement breaks their edges.

Tiling: every scene repeats with period W along x. The ground mesh spans three periods and
every instance is placed at x, x - W and x + W, so the camera's [0, W] window is one exact
period. Haze: aerial perspective in every material (mix toward the haze colour by view depth,
plus low-lying fog on the mid layer). A volume box would also fill the transparent sky of
layers 1 and 2, so the haze lives in the shaders instead; the look is the same.
Deterministic: all randomness comes from the manifest seed.
"""
import math
import os
import random

import bpy
import numpy as np
from mathutils import Vector

import gen_backdrop as GB
from build_pilgrim import lin
from meridian import pngio, post
from meridian.noise import fft_noise, fft_noise_1d

PX_W, PX_H = 2048, 1024
# Rendered beyond the period on both sides, then cropped: the render's own border columns
# (filter / screen-space falloff) never reach the tile edge, so the crop is one exact period.
MARGIN = 32


# ---------------------------------------------------------------- presets (Bible §7.1, §9)

PRESETS = {
    "earth": dict(
        sun=dict(dir=(-0.75, 0.45, -0.55), strength=4.5, color=(1.0, 0.95, 0.86), angle=1.5),
        ambient=((0.50, 0.60, 0.76), 0.35),
        haze=(184, 202, 214),
        far=dict(W=9000.0, level=0.42, peak=0.82, rock=[(112, 108, 104), (138, 132, 124)], snow=(236, 240, 246),
                 snowline=0.74, haze=(0.40, 0.00004), tilt=6.0),
        mid=dict(W=700.0, level=0.42, amp=0.10, ground=[(64, 92, 48), (82, 104, 56)], trees=520, protos=8,
                 tree_h=(14, 26), conifer=0.6, depth=(20, 140), haze=(0.20, 0.0012), fog=(0.25, 0.22),
                 tilt=12.0, frame_up=-0.08),
        # B-025: near tree line kept below ~row 0.25 so the cloud band (rows ~0.04-0.2) never
        # sits behind it at any parallax offset.
        near=dict(W=64.0, level=0.28, amp=0.05, ground=[(70, 96, 44), (98, 118, 56), (86, 74, 50)], trees=18,
                  protos=6, tree_h=(8.5, 14), conifer=0.45, depth=(3, 14), haze=(0.06, 0.004),
                  tufts=3800, shrubs=140, tilt=18.0, frame_up=0.12),   # 6000 tufts peaked at 2.2 GB
        leaf=[(46, 78, 34), (62, 96, 40), (84, 112, 46), (54, 88, 50)],
        needle=[(30, 58, 38), (40, 70, 44), (52, 80, 46)],
        bark=(82, 68, 56),
    ),
    # B-026 Earth biomes (Bible §7.1): same rendered-3D layers, biome palettes and contents.
    "earth_desert": dict(
        sun=dict(dir=(-0.75, 0.4, -0.6), strength=5.0, color=(1.0, 0.95, 0.85), angle=3.0),   # soft: tiles cleanly
        ambient=((0.62, 0.62, 0.66), 0.35),
        haze=(226, 210, 182),
        far=dict(W=9000.0, level=0.38, peak=0.66, rock=[(196, 150, 104), (222, 182, 132)], snow=(0, 0, 0),
                 snowline=9.0, haze=(0.42, 0.00004), tilt=6.0, terrace=2),
        mid=dict(W=700.0, level=0.40, amp=0.12, cliff=0.5, bumps=0.004, depth=(20, 140), haze=(0.3, 0.0016),
                 ground=[(214, 182, 128), (196, 160, 108)], strata=(9.0, (232, 200, 150), 0.4),
                 rocks=30, rock_h=(2, 7), tilt=12.0, frame_up=-0.08, dune_rows=5, dune_h=0.8, seam_keepout=True),
        near=dict(W=64.0, level=0.26, amp=0.07, bumps=0.004, depth=(3, 14), haze=(0.05, 0.003),
                  ground=[(226, 196, 144), (208, 176, 124)], dune_rows=4, dune_h=0.9, dune_mesa=0.15,
                  rocks=14, rock_h=(0.3, 1.4), pebbles=120, tilt=18.0, frame_up=0.12, seam_keepout=True),
        rock=[(176, 132, 92), (150, 110, 78), (196, 156, 112), (132, 100, 74)],
    ),
    "earth_taiga": dict(
        sun=dict(dir=(-0.8, 0.45, -0.45), strength=3.6, color=(1.0, 0.95, 0.9), angle=2.0),
        ambient=((0.5, 0.58, 0.68), 0.4),
        haze=(186, 198, 210),
        far=dict(W=9000.0, level=0.42, peak=0.84, rock=[(108, 108, 112), (132, 132, 134)], snow=(240, 244, 248),
                 snowline=0.62, haze=(0.42, 0.00004), tilt=6.0),
        mid=dict(W=700.0, level=0.42, amp=0.12, ground=[(58, 80, 58), (72, 92, 64)], trees=640, protos=8,
                 tree_h=(16, 30), conifer=0.95, depth=(20, 140), haze=(0.24, 0.0012), fog=(0.3, 0.22),
                 tilt=12.0, frame_up=-0.08),
        near=dict(W=64.0, level=0.28, amp=0.05, ground=[(70, 88, 56), (88, 100, 66), (80, 72, 56)], trees=20,
                  protos=6, tree_h=(9, 14), conifer=0.95, depth=(3, 14), haze=(0.07, 0.004),
                  tufts=3000, shrubs=60, tilt=18.0, frame_up=0.12),
        leaf=[(52, 80, 44), (66, 92, 50)],
        needle=[(24, 48, 36), (32, 58, 42), (40, 66, 46)],
        bark=(72, 58, 48),
    ),
    "earth_coast": dict(
        sun=dict(dir=(-0.75, 0.45, -0.55), strength=4.5, color=(1.0, 0.96, 0.88), angle=1.5),
        ambient=((0.5, 0.62, 0.78), 0.38),
        haze=(190, 210, 222),
        # B-026 review: the first coast hid its sea behind a full-height forest (mid level 0.40 >
        # sea 0.34) and read as plain woodland. Now three clear steps: sea with low headlands
        # (far), a lowered sandy shore with sparse coastal pines leaving a band of sea above it
        # (mid), a sand beach with dune grass (near).
        far=dict(W=9000.0, level=0.18, peak=0.40, rock=[(112, 118, 104), (136, 140, 120)], snow=(0, 0, 0),
                 snowline=9.0, haze=(0.42, 0.00004), tilt=6.0, sea=dict(level=0.36, color=(46, 98, 140))),   # flooded: headlands only
        mid=dict(W=700.0, level=0.27, amp=0.07, ground=[(186, 174, 132), (140, 146, 92)], trees=0, protos=1,
                 tree_h=(8, 14), conifer=0.7, depth=(20, 140), haze=(0.22, 0.0012),
                 tilt=12.0, frame_up=-0.08, sea=dict(level=0.55, shore=30.0, shallow=(70, 176, 178), deep=(26, 70, 122))),
        near=dict(W=64.0, level=0.22, amp=0.03, relief2d=True, ground=[(226, 210, 168), (212, 192, 148), (196, 176, 132)], trees=0,
                  protos=1, tree_h=(7, 11), conifer=0.5, depth=(3, 14), haze=(0.06, 0.004),
                  tufts=1200, shrubs=6, tilt=18.0, frame_up=0.12),
        leaf=[(56, 92, 40), (74, 108, 46), (92, 120, 52)],
        needle=[(32, 60, 40), (44, 72, 46)],
        bark=(90, 74, 60),
    ),
    # B-039 Waystation docking bay (interior): front-top work lighting, bay air haze.
    "waystation": dict(
        sun=dict(dir=(-0.25, 0.7, -0.67), strength=3.2, color=(1.0, 0.96, 0.9), angle=8.0),
        ambient=((0.52, 0.56, 0.64), 0.45),
        haze=(92, 98, 110),
        bay=[dict(W=48.0, haze=(0.3, 0.0004), tilt=0.0),
             dict(W=36.0, haze=(0.12, 0.0004), tilt=0.0),
             dict(W=24.0, haze=(0.02, 0.0004), tilt=8.0, frame_up=0.12)],
    ),
    # B-027 Mercury (Bible §7.3): airless, so harsh small-angle sun, almost no ambient, little
    # haze; cratered relief; blinding grey regolith; violet twilight in the sky only.
    "mercury": dict(
        sun=dict(dir=(-0.85, 0.3, -0.42), strength=6.0, color=(1.0, 0.98, 0.94), angle=0.5),
        ambient=((0.3, 0.24, 0.42), 0.06),
        haze=(60, 44, 90),
        far=dict(W=9000.0, level=0.36, peak=0.56, rock=[(118, 116, 120), (150, 148, 152)], snow=(0, 0, 0),
                 snowline=9.0, haze=(0.3, 0.00003), tilt=6.0, rough=0.004),
        mid=dict(W=700.0, level=0.40, amp=0.10, bumps=0.02, depth=(20, 140), haze=(0.1, 0.0006),
                 ground=[(128, 126, 130), (104, 102, 108)], rocks=120, rock_h=(1, 5), craters=14,
                 tilt=12.0, frame_up=-0.08),
        near=dict(W=64.0, level=0.26, amp=0.04, depth=(3, 14), haze=(0.02, 0.001),
                  ground=[(150, 148, 152), (122, 120, 126)], rocks=90, rock_h=(0.2, 1.4), pebbles=900, craters=6,
                  tilt=18.0, frame_up=0.12),
        rock=[(96, 94, 100), (70, 68, 74), (120, 118, 122)],
    ),
    # B-028 Venus (Bible §7.4, §9 orange-cream/black). Deck: the habitable cloud layer, all
    # cloud (towers far, billowing deck tops mid/near), backlit warm haze. Surface: black glassy
    # plains under a dim orange murk, lit by lava vents.
    "venus_deck": dict(
        # B-028 review: the first deck read as rocky rubble (fine geometry bumps, isotropic dune
        # noise, spiky far ridge). Clouds = only the long smooth relief (rounded heaps), no
        # bumps, soft wide sun, high ambient, strong haze; far towers smooth (rough 0).
        sun=dict(dir=(-0.35, 0.45, -0.82), strength=3.6, color=(1.0, 0.92, 0.74), angle=14.0),   # high: lit tops
        ambient=((0.78, 0.62, 0.46), 0.55),
        haze=(232, 206, 160),
        far=dict(W=9000.0, level=0.36, peak=0.70, rock=[(240, 222, 182), (222, 196, 150)], snow=(0, 0, 0),
                 snowline=9.0, haze=(0.42, 0.00004), tilt=6.0, rough=0.0),
        mid=dict(W=700.0, level=0.40, amp=0.22, bumps=0.0, depth=(20, 140), haze=(0.32, 0.0014),
                 ground=[(234, 212, 168), (216, 188, 142)], rocks=0, rock_h=(1, 2), tilt=12.0, frame_up=-0.08),
        near=dict(W=64.0, level=0.26, amp=0.12, bumps=0.0, depth=(3, 14), haze=(0.1, 0.003),
                  ground=[(244, 228, 192), (224, 200, 156)], rocks=0, rock_h=(0.3, 1), tilt=18.0, frame_up=0.12),
        # Strike 4 / new approach: painted 2D cloud banks replace the heightfields above.
        banks=[dict(top=0.44, base_amp=26, r=(36, 110), billows=46, fall=260, haze=0.42,
                    crown=(255, 244, 222), under=(206, 160, 112)),
               dict(top=0.56, base_amp=34, r=(60, 170), billows=34, fall=320, haze=0.22,
                    crown=(255, 240, 214), under=(196, 148, 100)),
               dict(top=0.72, base_amp=40, r=(100, 260), billows=22, fall=380, haze=0.06,
                    crown=(255, 238, 208), under=(184, 134, 90))],
        rock=[(200, 180, 140)],
    ),
    "venus_surface": dict(
        sun=dict(dir=(-0.5, 0.5, -0.7), strength=1.2, color=(1.0, 0.7, 0.42), angle=20.0),    # diffuse light through the deck
        ambient=((0.56, 0.36, 0.2), 0.5),
        haze=(120, 70, 40),
        far=dict(W=9000.0, level=0.34, peak=0.52, rock=[(40, 34, 32), (58, 48, 42)], snow=(0, 0, 0),
                 snowline=9.0, haze=(0.5, 0.00004), tilt=6.0),
        mid=dict(W=700.0, level=0.40, amp=0.08, depth=(20, 140), haze=(0.3, 0.0012),
                 ground=[(34, 30, 30), (52, 44, 40)], rocks=140, rock_h=(1, 5), vents=60, tilt=12.0, frame_up=-0.08),
        near=dict(W=64.0, level=0.26, amp=0.04, depth=(3, 14), haze=(0.08, 0.003),
                  ground=[(30, 26, 28), (50, 42, 40)], rocks=90, rock_h=(0.2, 1.4), pebbles=600, vents=25,
                  tilt=18.0, frame_up=0.12),
        rock=[(40, 34, 34), (58, 50, 46), (30, 28, 30)],
    ),
    # Bible §7.2: butterscotch sky, long shadows, rust/umber/salmon, thin haze.
    "mars": dict(
        sun=dict(dir=(-0.85, 0.35, -0.38), strength=3.6, color=(1.0, 0.9, 0.78), angle=0.8),
        ambient=((0.66, 0.50, 0.38), 0.42),
        haze=(214, 170, 128),
        far=dict(W=9000.0, level=0.40, peak=0.70, rock=[(150, 92, 64), (184, 120, 84)], snow=(0, 0, 0),
                 snowline=9.0, haze=(0.42, 0.00004), tilt=6.0, terrace=3),
        mid=dict(W=700.0, level=0.40, amp=0.16, terrace=3, cliff=0.55, bumps=0.015, depth=(20, 140), haze=(0.22, 0.0012),
                 ground=[(150, 84, 54), (178, 108, 72)], strata=(10.0, (206, 142, 100), 0.65),
                 rocks=260, rock_h=(3, 10), tilt=12.0, frame_up=-0.08, fog=(0.18, 0.1)),
        near=dict(W=64.0, level=0.26, amp=0.04, depth=(3, 14), haze=(0.05, 0.003),
                  ground=[(146, 80, 50), (176, 108, 72)], dunes=True,
                  rocks=170, rock_h=(0.3, 2.4), pebbles=1400, tilt=18.0, frame_up=0.12),
        rock=[(96, 70, 58), (120, 86, 66), (80, 60, 52), (140, 96, 72)],   # basalt under rust dust
    ),
}


# ---------------------------------------------------------------- materials

def _haze(mat, haze_rgb, base, per_m, fog=None, front=0.0):
    """Mix the material's shader toward a flat haze colour: fac = base + per_m * (view depth
    - front), front = camera distance to the scene's front plane (+ fog that pools below a
    world height). Keeps alpha (no volume)."""
    base = base - per_m * front
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    out = next(n for n in N if n.bl_idname == "ShaderNodeOutputMaterial")
    src = out.inputs["Surface"].links[0].from_socket
    cam = N.new("ShaderNodeCameraData")
    d = N.new("ShaderNodeMath"); d.operation = "MULTIPLY_ADD"
    d.inputs[1].default_value = per_m
    d.inputs[2].default_value = base
    L.new(cam.outputs["View Z Depth"], d.inputs[0])
    fac = d.outputs[0]
    if fog:
        amount, z_top, z_bottom = fog                 # 0 at z_top, `amount` at z_bottom
        geo = N.new("ShaderNodeNewGeometry")
        sep = N.new("ShaderNodeSeparateXYZ")
        L.new(geo.outputs["Position"], sep.inputs[0])
        mr = N.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = z_top
        mr.inputs["From Max"].default_value = z_bottom
        mr.inputs["To Max"].default_value = amount
        L.new(sep.outputs["Z"], mr.inputs["Value"])
        add = N.new("ShaderNodeMath"); add.operation = "ADD"; add.use_clamp = True
        L.new(fac, add.inputs[0]); L.new(mr.outputs["Result"], add.inputs[1])
        fac = add.outputs[0]
    clamp = N.new("ShaderNodeClamp")
    L.new(fac, clamp.inputs["Value"])
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = lin(haze_rgb)
    mix = N.new("ShaderNodeMixShader")
    L.new(clamp.outputs[0], mix.inputs["Fac"])
    L.new(src, mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])


def _wrapped(nt, vec_socket, W):
    """(x mod W, y, z): periodic in x with the scene, continuous inside the [0, W) frame."""
    N, L = nt.nodes, nt.links
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(vec_socket, sep.inputs[0])
    md = N.new("ShaderNodeMath"); md.operation = "FLOORED_MODULO"; md.inputs[1].default_value = W
    L.new(sep.outputs["X"], md.inputs[0])
    cmb = N.new("ShaderNodeCombineXYZ")
    L.new(md.outputs[0], cmb.inputs["X"])
    L.new(sep.outputs["Y"], cmb.inputs["Y"])
    L.new(sep.outputs["Z"], cmb.inputs["Z"])
    return cmb.outputs[0]


def _periodic_noise(nt, pos_socket, W, nz):
    """Feed Noise node `nz` a position mapped onto a circle in x: vector (R cos t, R sin t, y),
    4th dimension z, with t = 2 pi x / W and R = W / 2 pi (arc length = x, so the noise scale is
    unchanged). Periodic AND continuous at the wrap: x mod W (_wrapped) repeats the texture but
    jumps at x = W, a seam smooth dunes made visible (B-026 desert)."""
    N, L = nt.nodes, nt.links
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(pos_socket, sep.inputs[0])
    t = N.new("ShaderNodeMath"); t.operation = "MULTIPLY"; t.inputs[1].default_value = 2 * math.pi / W
    L.new(sep.outputs["X"], t.inputs[0])
    R = W / (2 * math.pi)
    parts = []
    for op in ("COSINE", "SINE"):
        f = N.new("ShaderNodeMath"); f.operation = op
        L.new(t.outputs[0], f.inputs[0])
        r = N.new("ShaderNodeMath"); r.operation = "MULTIPLY"; r.inputs[1].default_value = R
        L.new(f.outputs[0], r.inputs[0])
        parts.append(r.outputs[0])
    cmb = N.new("ShaderNodeCombineXYZ")
    L.new(parts[0], cmb.inputs["X"]); L.new(parts[1], cmb.inputs["Y"]); L.new(sep.outputs["Y"], cmb.inputs["Z"])
    nz.noise_dimensions = "4D"
    L.new(cmb.outputs[0], nz.inputs["Vector"])
    L.new(sep.outputs["Z"], nz.inputs["W"])


def mat_varied(name, cols, rough=0.85, noise_scale=0.0, bump=0.0, W=None, world_noise=False):
    """Principled with base colour picked per object through a ramp of `cols`, plus optional
    noise variation and bump. The per-object pick is a white-noise hash of the object's
    location with x wrapped by W (Object Info Random differs between an instance and its
    x +/- W copy, which would break tiling). world_noise samples the noise at the wrapped
    world position (for ground spanning several periods); otherwise object space."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    pr.inputs["Roughness"].default_value = rough
    info = N.new("ShaderNodeObjectInfo")
    wn = N.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    L.new(_wrapped(nt, info.outputs["Location"], W) if W else info.outputs["Location"], wn.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "CONSTANT" if len(cols) > 2 else "LINEAR"
    els = cr.elements
    els[0].position, els[0].color = 0.0, lin(cols[0])
    els[1].position, els[1].color = 1.0, lin(cols[-1])
    for i, c in enumerate(cols[1:-1], start=1):     # new() returns the element; set it directly
        els.new(i / len(cols)).color = lin(c)
    if len(cols) > 2:                                # CONSTANT: last band starts at its slot
        els[len(els) - 1].position = (len(cols) - 1) / len(cols)
    L.new(wn.outputs["Value"], ramp.inputs["Fac"])
    col = ramp.outputs["Color"]
    if noise_scale:
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = noise_scale
        nz.inputs["Detail"].default_value = 6.0
        if world_noise:
            geo = N.new("ShaderNodeNewGeometry")
            _periodic_noise(nt, geo.outputs["Position"], W, nz)
        else:
            tc = N.new("ShaderNodeTexCoord")
            L.new(tc.outputs["Object"], nz.inputs["Vector"])
        mr = N.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.3
        mr.inputs["From Max"].default_value = 0.7
        mr.inputs["To Min"].default_value = 0.75
        mr.inputs["To Max"].default_value = 1.2
        L.new(nz.outputs["Fac"], mr.inputs["Value"])
        mul = N.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
        mul.inputs[0].default_value = 1.0
        L.new(col, mul.inputs[6])
        cm = N.new("ShaderNodeCombineColor")
        for k in range(3):
            L.new(mr.outputs["Result"], cm.inputs[k])
        L.new(cm.outputs[0], mul.inputs[7])
        col = mul.outputs[2]
        if bump:
            b = N.new("ShaderNodeBump")
            b.inputs["Strength"].default_value = bump
            L.new(nz.outputs["Fac"], b.inputs["Height"])
            L.new(b.outputs["Normal"], pr.inputs["Normal"])
    L.new(col, pr.inputs["Base Color"])
    return m


# ---------------------------------------------------------------- geometry helpers

def mesh_obj(name, verts, faces, coll, mat=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    if mat:
        me.materials.append(mat)
    return ob


def apply_modifiers(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    bpy.data.meshes.remove(old)


def _bake_mesh(ob, tex_scale, strength, seed):
    """Apply a noise Displace to a temporary object in the scene collection (excluded
    collections are not evaluated) and return just the mesh, with one empty material slot."""
    tex = bpy.data.textures.new(ob.name + "_tex", "CLOUDS")
    tex.noise_scale = tex_scale
    tex.noise_depth = 3
    mod = ob.modifiers.new("disp", "DISPLACE")
    mod.texture = tex
    mod.strength = strength
    mod.mid_level = 0.5
    mod.texture_coords = "GLOBAL"
    ob.location = (seed * 7.31, seed * 3.7, 0)      # different noise sample per variant
    bpy.context.view_layer.update()
    apply_modifiers(ob)
    me = ob.data
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(None)
    bpy.data.objects.remove(ob)
    return me


def leaf_cluster_mesh(name, seed, cards=160):
    """B-025 foliage: a leaf mass of small randomly oriented leaf cards scattered through a
    unit ball around a smaller, darker-shaded core, so the silhouette breaks up into leaves
    instead of reading as a smooth sphere. One empty material slot (set per object)."""
    import bmesh
    rnd = random.Random(seed)
    bm = bmesh.new()
    core = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.62)
    for _ in range(cards):
        # Points biased toward the surface of the unit ball (that's where leaves catch light).
        d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
        c = d * (0.55 + 0.45 * rnd.random() ** 0.5)
        n = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
        u = n.orthogonal().normalized()
        v = n.cross(u)
        w, h = rnd.uniform(0.09, 0.15), rnd.uniform(0.05, 0.09)
        verts = [bm.verts.new(c + u * sx * w + v * sy * h) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        bm.faces.new(verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    me.materials.append(None)
    return me


def blob_mesh(name, coll, seed, subdiv=3, strength=0.45, scale=0.9):
    """A leaf-cluster / shrub mesh: icosphere with displacement applied (broken edges)."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=1.0)
    ob = bpy.context.active_object
    ob.name = name
    return _bake_mesh(ob, scale, strength, seed)


def skin_tree_skeleton(rnd, h):
    """Broadleaf skeleton: trunk with a slight curve, 4-6 limbs with 2-3 segments each.
    Returns (verts, edges, radii, tips)."""
    verts, edges, radii = [(0.0, 0.0, 0.0)], [], [0.045 * h]
    lean = rnd.uniform(-0.06, 0.06)
    trunk_h = h * rnd.uniform(0.38, 0.5)
    for i in range(1, 4):
        t = i / 3
        verts.append((lean * h * t * t, 0.0, trunk_h * t))
        edges.append((i - 1, i))
        radii.append(0.045 * h * (1 - 0.35 * t))
    top = len(verts) - 1
    tips = []
    for b in range(rnd.randint(4, 6)):
        ang = rnd.uniform(0, 2 * math.pi)
        up = rnd.uniform(0.35, 0.8)
        prev, p = top, Vector(verts[top])
        r = radii[top] * 0.7
        seg = h * rnd.uniform(0.13, 0.2)
        for s in range(rnd.randint(2, 3)):
            d = Vector((math.cos(ang), math.sin(ang) * 0.6, up + 0.2 * s)).normalized()
            p = p + d * seg
            verts.append(tuple(p))
            edges.append((prev, len(verts) - 1))
            r *= 0.62
            radii.append(max(r, 0.01 * h))
            prev = len(verts) - 1
            ang += rnd.uniform(-0.4, 0.4)
        tips.append((Vector(verts[prev]), Vector(verts[top])))
    return verts, edges, radii, tips


def build_broadleaf(coll, rnd, h, bark, leaf, blobs):
    verts, edges, radii, tips = skin_tree_skeleton(rnd, h)
    me = bpy.data.meshes.new("trunk")
    me.from_pydata(verts, edges, [])
    ob = bpy.data.objects.new("trunk", me)
    coll.objects.link(ob)
    skin = ob.modifiers.new("skin", "SKIN")
    for sv, r in zip(me.skin_vertices[0].data, radii):
        sv.radius = (r, r)
    ob.modifiers.new("sub", "SUBSURF").levels = 1
    me.materials.append(bark)
    # Leaf clusters along each limb's outer half and around the crown.
    for tip, base in tips:
        for k in range(rnd.randint(7, 10)):
            t = rnd.uniform(0.4, 1.1)
            c = base.lerp(tip, t) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.5, 0.9))) * h * 0.08
            cl = bpy.data.objects.new("leaf", blobs[rnd.randrange(len(blobs))])
            coll.objects.link(cl)
            s = h * rnd.uniform(0.045, 0.08)
            cl.scale = (s * rnd.uniform(1.0, 1.4), s * rnd.uniform(0.9, 1.2), s * rnd.uniform(0.75, 1.0))
            cl.rotation_euler = (rnd.uniform(0, 6.3), rnd.uniform(0, 6.3), rnd.uniform(0, 6.3))
            cl.location = c
            cl.material_slots[0].link = "OBJECT"
            cl.material_slots[0].material = leaf


def build_conifer(coll, rnd, h, bark, needle, whorls):
    trunk_r = 0.025 * h
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=trunk_r, depth=h * 0.95, location=(0, 0, h * 0.475))
    tr = bpy.context.active_object
    for c in list(tr.users_collection):
        c.objects.unlink(tr)
    coll.objects.link(tr)
    tr.data.materials.append(bark)
    n = rnd.randint(9, 13)
    base_z = h * rnd.uniform(0.12, 0.2)
    for i in range(n):
        t = i / (n - 1)
        z = base_z + (h - base_z) * t ** 0.95
        r = h * 0.22 * (1 - t) ** 0.9 + h * 0.02
        w = bpy.data.objects.new("whorl", whorls[rnd.randrange(len(whorls))])
        coll.objects.link(w)
        w.scale = (r, r * rnd.uniform(0.85, 1.0), h * 0.12 * (0.6 + 0.4 * (1 - t)))
        w.rotation_euler = (rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), rnd.uniform(0, 6.3))
        w.location = (0, 0, z)
        w.material_slots[0].link = "OBJECT"
        w.material_slots[0].material = needle


def whorl_mesh(name, coll, seed):
    """A drooping skirt of branches: a cone (apex up, unit radius/height) displaced by noise."""
    bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=1.0, radius2=0.08, depth=1.0, end_fill_type="NOTHING")
    ob = bpy.context.active_object
    ob.name = name
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=8)
    bpy.ops.object.mode_set(mode="OBJECT")
    me = _bake_mesh(ob, 0.09, 0.2, seed + 11)
    rnd = random.Random(seed)
    phases = [rnd.uniform(0, 6.3) for _ in range(3)]
    for v in me.vertices:
        rr = math.hypot(v.co.x, v.co.y)
        a = math.atan2(v.co.y, v.co.x)
        # Ragged rim: branch tips stick out at irregular angles, more toward the skirt edge.
        spikes = (0.5 * math.sin(23 * a + phases[0]) + 0.3 * math.sin(37 * a + phases[1])
                  + 0.2 * math.sin(61 * a + phases[2]))
        k = 1 + 0.22 * spikes * rr ** 2
        v.co.x *= k
        v.co.y *= k
        v.co.z -= 0.25 * rr * rr + 0.06 * max(spikes, 0) * rr   # droop, tips sag a bit more
    return me


def tuft_mesh(name, coll, rnd):
    """A grass tuft: 14 curved, tapered blades (unit height)."""
    verts, faces = [], []
    for b in range(14):
        a = rnd.uniform(0, 2 * math.pi)
        lean = rnd.uniform(0.15, 0.55)
        hgt = rnd.uniform(0.6, 1.0)
        w = 0.035
        dx, dy = math.cos(a), math.sin(a)
        base = len(verts)
        for s in range(4):
            t = s / 3
            cx, cy = dx * lean * t * t * hgt, dy * lean * t * t * hgt
            ww = w * (1 - t) + 0.004
            verts += [(cx - dy * ww, cy + dx * ww, hgt * t), (cx + dy * ww, cy - dx * ww, hgt * t)]
        for s in range(3):
            i = base + 2 * s
            faces.append((i, i + 1, i + 3, i + 2))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    return me


def heightfield(name, coll, W, depth_m, nx, ny, zfun, mat, y0=0.0):
    """Ground over x in [-W, 2W] (three periods), y in [y0, depth_m]; zfun(ix, iy) on the
    one-period grid (periodic in ix)."""
    xs = np.linspace(-W, 2 * W, 3 * nx + 1)
    ys = np.linspace(y0, depth_m, ny + 1)
    verts = []
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            verts.append((float(x), float(y), float(zfun(i % nx, j))))
    row = len(xs)
    faces = [(j * row + i, j * row + i + 1, (j + 1) * row + i + 1, (j + 1) * row + i)
             for j in range(ny) for i in range(len(xs) - 1)]
    return mesh_obj(name, verts, faces, coll, mat)


def grid_rows(W, nx, y_front, y_back, cap=420):
    """Depth rows so ground cells are about square: noise on stretched cells reads as
    front-to-back streaks (vertical stripes on screen)."""
    return int(min(cap, max(64, round((y_back - y_front) / (W / nx)))))


def instance(coll_target, proto, loc, scale, rotz, W):
    for dx in (-W, 0.0, W):
        e = bpy.data.objects.new("inst", None)
        e.instance_type = "COLLECTION"
        e.instance_collection = proto
        e.location = (loc[0] + dx, loc[1], loc[2])
        e.scale = (scale, scale, scale)
        e.rotation_euler = (0, 0, rotz)
        coll_target.objects.link(e)


# ---------------------------------------------------------------- scene / render

def new_scene(P, W, preview, tilt_deg=0.0, target=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    r = scene.render
    items = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    r.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in items else "BLENDER_EEVEE"
    r.resolution_x, r.resolution_y = PX_W + 2 * MARGIN, PX_H
    r.resolution_percentage = 25 if preview else 100
    r.film_transparent = True
    r.dither_intensity = 0.0
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    scene.eevee.taa_render_samples = 8 if preview else 48
    if hasattr(scene.eevee, "use_shadows"):
        scene.eevee.use_shadows = True
    if hasattr(scene.eevee, "shadow_pool_size"):
        # Default pool reserves 512 MB; one sun on static scenery fits a smaller one (8 GB rule).
        items = [e.identifier for e in scene.eevee.bl_rna.properties["shadow_pool_size"].enum_items]
        if "128" in items:
            scene.eevee.shadow_pool_size = "128"
    # No EEVEE overscan: it rescales the projection slightly, so x = 0 and x = W no longer land
    # one period apart (measured: period error 3.1 -> 0.1 without it). MARGIN covers the borders.
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    world = bpy.data.worlds.new("w")
    if world.node_tree is None:
        world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    col, s = P["ambient"]
    bg.inputs["Color"].default_value = (*col, 1.0)
    bg.inputs["Strength"].default_value = s
    scene.world = world
    sd = bpy.data.lights.new("sun", "SUN")
    sd.energy = P["sun"]["strength"]
    sd.color = P["sun"]["color"]
    sd.angle = math.radians(P["sun"]["angle"])
    sun = bpy.data.objects.new("sun", sd)
    scene.collection.objects.link(sun)
    sun.rotation_euler = Vector(P["sun"]["dir"]).to_track_quat("-Z", "Y").to_euler()
    cd =bpy.data.cameras.new("cam")
    cd.type = "ORTHO"
    cd.ortho_scale = W * (PX_W + 2 * MARGIN) / PX_W     # width incl. margins; height stays W/2
    cd.sensor_fit = "HORIZONTAL"
    cd.clip_start, cd.clip_end = 0.1, W * 10
    cam = bpy.data.objects.new("cam", cd)
    scene.collection.objects.link(cam)
    # Looks along +Y tilted down by tilt_deg (a rotation about X keeps the x period intact);
    # the frame centre is `target`, the frame spans exactly x in [0, W].
    t = math.radians(tilt_deg)
    d = Vector((0.0, math.cos(t), -math.sin(t)))
    tgt = Vector(target if target is not None else (W / 2, 0.0, W / 4))
    cam.location = tgt - d * W
    cam.rotation_euler = (math.pi / 2 - t, 0, 0)
    scene.camera = cam
    return scene


def render(scene, work, tag, W):
    """Render in two halves (D-028: halves the frame buffers, peak ~1.45 GB): the camera shifts
    to W/4 and 3W/4, each half keeps MARGIN columns on both sides, and the cropped halves are
    joined. Logs two proofs: stitch (both halves agree at x = W/2) and period (x = 0 vs x = W)."""
    os.makedirs(work, exist_ok=True)
    cam = scene.camera
    half_px = PX_W // 2
    scene.render.resolution_x = half_px + 2 * MARGIN
    cam.data.ortho_scale = (W / 2) * (half_px + 2 * MARGIN) / half_px
    parts = []
    for k in (0, 1):
        cam.location.x = W / 4 + k * W / 2
        path = os.path.join(work, f"backdrop3d_{tag}_{k}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        parts.append(pngio.read_png(path))
    m = MARGIN * scene.render.resolution_percentage // 100
    hw = parts[0].shape[1] - 2 * m
    pm = [p[..., :3] * p[..., 3:4] for p in parts]
    stitch = float(np.abs(pm[0][:, m + hw] - pm[1][:, m]).mean() * 255)     # x = W/2 in both renders
    period = float(np.abs(pm[0][:, m] - pm[1][:, m + hw]).mean() * 255)     # x = 0 vs x = W
    step = float(np.abs(np.diff(pm[0][:, m:m + hw], axis=1)).mean() * 255)
    print(f"MERIDIAN period check {tag}: |col(0) - col(W)| = {period:.2f}, stitch |left(W/2) - right(W/2)| = "
          f"{stitch:.2f} (mean neighbour step {step:.2f})")
    if os.environ.get("MERIDIAN_KEEP_HALVES"):
        # Debug (B-026 desert seam): keep both halves, and a strip of x = W (end of half 1)
        # beside x = 0 (start of half 0) with the per-row difference, to see what isn't periodic.
        dbg = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "preview", "debug")
        os.makedirs(dbg, exist_ok=True)
        for k, p in enumerate(parts):
            pngio.write_png(os.path.join(dbg, f"{tag}_half{k}.png"), pngio.to_u8(p))
        a, b = pm[1][:, m + hw - 96:m + hw], pm[0][:, m:m + 96]
        diff = np.abs(pm[0][:, m:m + 1] - pm[1][:, m + hw:m + hw + 1]).repeat(32, 1) * 4
        strip = np.clip(np.hstack([a, b, diff]), 0, 1)
        pngio.write_png(os.path.join(dbg, f"{tag}_seam.png"),
                        pngio.to_u8(np.dstack([strip, np.ones(strip.shape[:2], np.float32)])))
        print(f"MERIDIAN debug halves written to {dbg}")
    return np.hstack([parts[0][:, m:m + hw], parts[1][:, m:m + hw]]).copy()


def proto_collection(name, scene):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    bpy.context.view_layer.layer_collection.children[name].exclude = True
    return c


def build_protos(P, scene, rnd, spec, mats):
    lib = proto_collection("lib", scene)
    blobs = [leaf_cluster_mesh(f"leaves{i}", seed=100 + i) for i in range(4)]       # B-025
    whorls = [whorl_mesh(f"whorl{i}", lib, i) for i in range(3)]
    protos = []
    for k in range(spec["protos"]):
        c = proto_collection(f"tree{k}", scene)
        h = 1.0                                       # unit tree; instances scale it
        if rnd.random() < spec["conifer"]:
            build_conifer(c, rnd, h, mats["bark"], mats["needle"], whorls)
        else:
            build_broadleaf(c, rnd, h, mats["bark"], mats["leaf"], blobs)
        protos.append(c)
    return protos, blobs


def forest_layer(P, spec, seed, preview, work, near):
    W = spec["W"]
    top0 = W / 2
    d0, d1 = spec["depth"]
    scene = new_scene(P, W, preview, spec["tilt"],
                      (W / 2, (d0 + d1) / 2, top0 * spec["level"] + top0 * spec["frame_up"]))
    rnd = random.Random(seed)
    rng = np.random.default_rng(seed)
    hz = P["haze"]
    mats = {
        "bark": mat_varied("bark", [P["bark"], tuple(int(c * 0.8) for c in P["bark"])], 0.9, 2.0, 0.3, W=W),
        "leaf": mat_varied("leaf", P["leaf"], 0.8, 1.5, 0.4, W=W),
        "needle": mat_varied("needle", P["needle"], 0.85, 2.5, 0.4, W=W),
        "ground": mat_varied("ground", spec["ground"][:2], 0.95, spec.get("ground_noise", 0.6), 0.5,
                             W=W, world_noise=True),
        "tuft": mat_varied("tuft", [(74, 108, 44), (96, 126, 52), (118, 132, 58)], 0.7, W=W),
    }
    top = W / 2
    base = top * spec["level"]
    amp = top * spec["amp"]
    fog = spec.get("fog")
    for m in mats.values():
        _haze(m, hz, spec["haze"][0], spec["haze"][1],
              (fog[0], base + amp * fog[1], base - amp) if fog else None, front=W)
    protos, blobs = build_protos(P, scene, rnd, spec, mats)
    # Ground runs from well in front of the camera's view (fills the frame bottom) to behind
    # the last trees; the tilted camera sees its surface, not its edge. The hill profile only
    # rises toward the back (it forms the silhouette); an extruded profile shades as stripes.
    y_front, y_back = -top, d1 + 4
    nx = 512
    ny = grid_rows(W, nx, y_front, y_back)
    prof = GB.ridge(rng, 0.5, 1.0, 40, 512, 1.2, 0.1)                  # periodic, in px of a 2048 width
    prof = (prof - prof.mean()) / (np.abs(prof - prof.mean()).max() + 1e-6)
    prof = np.interp(np.arange(nx) / nx * PX_W, np.arange(PX_W), prof)
    bumps = fft_noise(rng, ny + 1, nx, 3, 60, 0.8)
    rel2 = None
    if spec.get("relief2d"):
        # B-026 coast: the x-only profile extruded in depth shades as vertical streaks on a
        # bare beach; a 2D field (as rock_layer, B-025) varies along depth too. Opt-in, so the
        # accepted forest layers keep their exact relief.
        rel2 = fft_noise(rng, ny + 1, nx, 40, 260, 1.6)
        rel2 = (rel2 - rel2.mean()) / (np.abs(rel2 - rel2.mean()).max() + 1e-6)

    def shape(i, j):
        return rel2[min(j, ny), i] if rel2 is not None else prof[i]

    def zf(i, j):
        y = y_front + (y_back - y_front) * j / ny
        w = min(1.0, max(0.0, (y - d0 * 0.5) / max(y_back - d0 * 0.5, 1e-3)))
        w = w * w * (3 - 2 * w)
        return base - amp * shape(i, j) * w + amp * 0.06 * bumps[j % (ny + 1), i]
    heightfield("ground", scene.collection, W, y_back, nx, ny, zf, mats["ground"], y0=y_front)
    def ground_z(x, y):
        w = min(1.0, max(0.0, (y - d0 * 0.5) / max(y_back - d0 * 0.5, 1e-3)))
        w = w * w * (3 - 2 * w)
        row = prof if rel2 is None else rel2[min(ny, max(0, int(round(ny * (y - y_front) / (y_back - y_front)))))]
        return base - amp * w * float(np.interp((x % W) / W * nx, np.arange(nx + 1), np.r_[row, row[0]]))
    lo, hi = spec["tree_h"]
    for t in range(spec["trees"]):
        x = rnd.uniform(0, W)
        y = rnd.uniform(d0, d1)
        h = rnd.uniform(lo, hi)
        instance(scene.collection, protos[rnd.randrange(len(protos))], (x, y, ground_z(x, y) - 0.3), h,
                 rnd.uniform(0, 6.3), W)
    if near:
        lib = bpy.data.collections["lib"]
        tufts = [tuft_mesh(f"tuft{i}", lib, rnd) for i in range(4)]
        for k, me in enumerate(tufts):
            c = proto_collection(f"tuftp{k}", scene)
            ob = bpy.data.objects.new("tuft", me)
            c.objects.link(ob)
            me.materials.append(mats["tuft"])
            tufts[k] = c
        y_vis = -top * 0.45                           # nearest ground the tilted frame shows
        for t in range(spec["tufts"]):
            # Denser toward the front, where the ground is largest on screen.
            x, y = rnd.uniform(0, W), y_vis + (d1 - y_vis) * rnd.random() ** 1.8
            instance(scene.collection, tufts[rnd.randrange(4)], (x, y, ground_z(x, y) - 0.05),
                     rnd.uniform(0.35, 0.8), rnd.uniform(0, 6.3), W)
        shrubs = []
        for k in range(3):
            c = proto_collection(f"shrub{k}", scene)
            for j in range(rnd.randint(3, 5)):
                ob = bpy.data.objects.new("sb", blobs[rnd.randrange(len(blobs))])
                c.objects.link(ob)
                ob.location = (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.3, 0.3), rnd.uniform(0.2, 0.6))
                ob.scale = (rnd.uniform(0.4, 0.6),) * 3
                ob.material_slots[0].link = "OBJECT"
                ob.material_slots[0].material = mats["leaf"]
            shrubs.append(c)
        for t in range(spec["shrubs"]):
            x, y = rnd.uniform(0, W), rnd.uniform(y_vis, d1)
            instance(scene.collection, shrubs[rnd.randrange(3)], (x, y, ground_z(x, y) - 0.2),
                     rnd.uniform(0.7, 1.6), rnd.uniform(0, 6.3), W)
    if spec.get("sea"):
        # B-026 coast: the sea lives in the layer whose rows it fills (in the far layer it sat
        # behind this layer's skyline and never showed). Flat plane from the shore line out
        # past the back; ground beyond the shore floods, the rising back hills stay headlands.
        sea = spec["sea"]
        zs = base + amp * sea["level"]
        y0s = sea["shore"]
        wm = bpy.data.materials.new("sea")
        wm.use_nodes = True
        nt = wm.node_tree
        N, L = nt.nodes, nt.links
        pr = N["Principled BSDF"]
        pr.inputs["Roughness"].default_value = 0.25
        # Depth: turquoise shallows at the shore darkening to deep blue toward the back.
        geo = N.new("ShaderNodeNewGeometry")
        sep = N.new("ShaderNodeSeparateXYZ")
        L.new(geo.outputs["Position"], sep.inputs[0])
        dmr = N.new("ShaderNodeMapRange")
        dmr.inputs["From Min"].default_value, dmr.inputs["From Max"].default_value = y0s, y0s + (y_back - y0s) * 0.6
        L.new(sep.outputs["Y"], dmr.inputs["Value"])
        ramp = N.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = lin(sea["shallow"])
        ramp.color_ramp.elements[1].color = lin(sea["deep"])
        L.new(dmr.outputs["Result"], ramp.inputs["Fac"])
        # Soft sun glitter: sparse bright flecks from periodic noise (tiles with the layer).
        gn = N.new("ShaderNodeTexNoise"); gn.inputs["Scale"].default_value = 0.9; gn.inputs["Detail"].default_value = 2.0
        _periodic_noise(nt, geo.outputs["Position"], W, gn)
        gmr = N.new("ShaderNodeMapRange"); gmr.interpolation_type = "SMOOTHSTEP"
        gmr.inputs["From Min"].default_value, gmr.inputs["From Max"].default_value = 0.57, 0.63
        gmr.inputs["To Max"].default_value = 0.35
        L.new(gn.outputs["Fac"], gmr.inputs["Value"])
        gl = N.new("ShaderNodeMix"); gl.data_type = "RGBA"
        L.new(gmr.outputs["Result"], gl.inputs[0])
        L.new(ramp.outputs["Color"], gl.inputs[6]); gl.inputs[7].default_value = lin((236, 246, 250))
        L.new(gl.outputs[2], pr.inputs["Base Color"])
        _haze(wm, hz, spec["haze"][0] * 0.5, spec["haze"][1] * 0.5, None, front=W)
        # Surf: a vertical foam skirt at the shore line, from sea level down below the ground.
        # It closes the gap where the shore ground dips under the sea's front edge (the light
        # notches: the far layer showing through) and reads as the white surf line.
        fm = bpy.data.materials.new("surf")
        fm.use_nodes = True
        fnt = fm.node_tree
        fp = fnt.nodes["Principled BSDF"]
        fp.inputs["Roughness"].default_value = 0.6
        # Thin bright foam crest on top, shallow water below (the skirt must stay tall to fill
        # the gap, but a full-height white skirt read as a grey concrete strip).
        fgeo = fnt.nodes.new("ShaderNodeNewGeometry")
        fsep = fnt.nodes.new("ShaderNodeSeparateXYZ")
        fnt.links.new(fgeo.outputs["Position"], fsep.inputs[0])
        fmr = fnt.nodes.new("ShaderNodeMapRange"); fmr.interpolation_type = "SMOOTHSTEP"
        fmr.inputs["From Min"].default_value = zs - amp * 0.18
        fmr.inputs["From Max"].default_value = zs - amp * 0.04
        fnt.links.new(fsep.outputs["Z"], fmr.inputs["Value"])
        fmix = fnt.nodes.new("ShaderNodeMix"); fmix.data_type = "RGBA"
        fnt.links.new(fmr.outputs["Result"], fmix.inputs[0])
        fmix.inputs[6].default_value = lin(sea["shallow"]); fmix.inputs[7].default_value = lin((250, 252, 250))
        fnt.links.new(fmix.outputs[2], fp.inputs["Base Color"])
        _haze(fm, hz, spec["haze"][0] * 0.5, spec["haze"][1] * 0.5, None, front=W)
        zb = base - amp * 1.5
        mesh_obj("surf", [(-W, y0s, zb), (2 * W, y0s, zb), (2 * W, y0s, zs), (-W, y0s, zs)], [(0, 1, 2, 3)],
                 scene.collection, fm, smooth=False)
        # Ends with the ground: the tilted ortho camera has no horizon, so a plane running
        # further back rises up the frame as a wall (first try).
        mesh_obj("sea", [(-W, y0s, zs), (2 * W, y0s, zs), (2 * W, y_back, zs), (-W, y_back, zs)],
                 [(0, 1, 2, 3)], scene.collection, wm, smooth=False)
    return render(scene, work, ("near" if near else "mid") + str(seed), W)


def far_layer(P, spec, seed, preview, work):
    W = spec["W"]
    scene = new_scene(P, W, preview, spec.get("tilt", 0.0))
    rng = np.random.default_rng(seed)
    nx, ny = 640, 48
    top = W / 2
    ridge = fft_noise(rng, ny + 1, nx, 30, 640, 1.6)
    ridge = (ridge - ridge.min()) / (ridge.max() - ridge.min())
    if spec.get("terrace"):
        ridge = terrace01(ridge, spec["terrace"])
    rough = fft_noise(rng, ny + 1, nx, 3, 40, 0.6)
    depth_m = W * 0.5
    def zf(i, j):
        y = j / ny
        bell = math.sin(math.pi * min(1.0, y * 1.3)) ** 1.2
        return top * spec["level"] + top * (spec["peak"] - spec["level"]) * bell * ridge[j, i] + top * spec.get("rough", 0.012) * rough[j, i] - top * 0.15 * (1 - bell)
    m = bpy.data.materials.new("rock")
    m.use_nodes = True
    nt = m.node_tree
    pr = nt.nodes["Principled BSDF"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    nsep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], nsep.inputs[0])
    # Snow where high and not too steep.
    hmr = nt.nodes.new("ShaderNodeMapRange")
    hmr.inputs["From Min"].default_value = top * spec["snowline"] * 0.92
    hmr.inputs["From Max"].default_value = top * spec["snowline"]
    nt.links.new(sep.outputs["Z"], hmr.inputs["Value"])
    smr = nt.nodes.new("ShaderNodeMapRange")
    smr.inputs["From Min"].default_value = 0.45
    smr.inputs["From Max"].default_value = 0.7
    nt.links.new(nsep.outputs["Z"], smr.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    nt.links.new(hmr.outputs["Result"], mul.inputs[0]); nt.links.new(smr.outputs["Result"], mul.inputs[1])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.004
    _periodic_noise(nt, geo.outputs["Position"], W, nz)
    rock = nt.nodes.new("ShaderNodeMix"); rock.data_type = "RGBA"
    nt.links.new(nz.outputs["Fac"], rock.inputs[0])
    rock.inputs[6].default_value = lin(spec["rock"][0]); rock.inputs[7].default_value = lin(spec["rock"][1])
    snow = nt.nodes.new("ShaderNodeMix"); snow.data_type = "RGBA"
    nt.links.new(mul.outputs[0], snow.inputs[0])
    nt.links.new(rock.outputs[2], snow.inputs[6])
    snow.inputs[7].default_value = lin(spec["snow"])
    nt.links.new(snow.outputs[2], pr.inputs["Base Color"])
    pr.inputs["Roughness"].default_value = 0.9
    _haze(m, P["haze"], spec["haze"][0], spec["haze"][1], front=W)
    heightfield("range", scene.collection, W, depth_m, nx, ny, zf, m)
    if spec.get("sea"):                                   # B-026 coast: open sea in front of the range
        sea = spec["sea"]
        wm = bpy.data.materials.new("sea")
        wm.use_nodes = True
        pr = wm.node_tree.nodes["Principled BSDF"]
        pr.inputs["Base Color"].default_value = lin(sea["color"])
        pr.inputs["Roughness"].default_value = 0.12
        _haze(wm, P["haze"], spec["haze"][0], spec["haze"][1], front=W)
        zs = top * sea["level"]
        mesh_obj("sea", [(-W, -W, zs), (2 * W, -W, zs), (2 * W, depth_m, zs), (-W, depth_m, zs)], [(0, 1, 2, 3)],
                 scene.collection, wm, smooth=False)
    return render(scene, work, "far" + str(seed), W)


def terrace01(a, levels, cliff=0.3):
    """Mesa profile for values in [0, 1]: flat steps joined by steep (not vertical) cliffs."""
    t = a * levels
    k = np.floor(t)
    f = np.clip((t - k - (1 - cliff)) / cliff, 0, 1)
    return (k + f * f * (3 - 2 * f)) / levels


def mat_strata(name, cols, W, strata):
    """Ground/cliff rock: wrapped world-space noise variation plus horizontal strata bands
    (period m, band colour, strength), warped by noise so they don't read as ruled lines."""
    m = mat_varied(name, cols, 0.95, 0.35, 0.6, W=W, world_noise=True)
    if not strata:
        return m
    period, band_col, k = strata
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    src = pr.inputs["Base Color"].links[0].from_socket
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Position"], sep.inputs[0])
    warp = N.new("ShaderNodeTexNoise"); warp.inputs["Scale"].default_value = 0.05
    _periodic_noise(nt, geo.outputs["Position"], W, warp)
    wz = N.new("ShaderNodeMath"); wz.operation = "MULTIPLY_ADD"; wz.inputs[1].default_value = period * 0.8
    L.new(warp.outputs["Fac"], wz.inputs[0]); L.new(sep.outputs["Z"], wz.inputs[2])
    ph = N.new("ShaderNodeMath"); ph.operation = "MULTIPLY"; ph.inputs[1].default_value = 2 * math.pi / period
    L.new(wz.outputs[0], ph.inputs[0])
    sn = N.new("ShaderNodeMath"); sn.operation = "SINE"
    L.new(ph.outputs[0], sn.inputs[0])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = -1.0, 1.0
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.0, k
    L.new(sn.outputs[0], mr.inputs["Value"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
    L.new(mr.outputs["Result"], mx.inputs[0])
    L.new(src, mx.inputs[6])
    mx.inputs[7].default_value = lin(band_col)
    L.new(mx.outputs[2], pr.inputs["Base Color"])
    return m


def rock_layer(P, spec, seed, preview, work, near):
    """Mars-style layer: terraced or dune heightfield, strata, instanced basalt boulders
    (+ pebbles on the near layer). Same tiling, haze and margin rules as forest_layer."""
    W = spec["W"]
    top = W / 2
    d0, d1 = spec["depth"]
    scene = new_scene(P, W, preview, spec["tilt"], (W / 2, (d0 + d1) / 2, top * spec["level"] + top * spec["frame_up"]))
    rnd = random.Random(seed)
    rng = np.random.default_rng(seed)
    base, amp = top * spec["level"], top * spec["amp"]
    ground = mat_strata("ground", spec["ground"], W, spec.get("strata"))
    rockm = mat_varied("rock", P["rock"], 0.9, 1.2, 0.6, W=W)
    fog = spec.get("fog")
    for m in (ground, rockm):
        _haze(m, P["haze"], spec["haze"][0], spec["haze"][1],
              (fog[0], base + amp * fog[1], base - amp) if fog else None, front=W)
    y_front, y_back = -top, d1 + 4
    nx = 512
    ny = grid_rows(W, nx, y_front, y_back)
    terr = spec.get("terrace")
    prof = GB.ridge(rng, 0.5, 1.0, 160 if terr else 40, 1024, 1.6, 0.0 if terr else 0.1)
    prof = (prof - prof.mean()) / (np.abs(prof - prof.mean()).max() + 1e-6)          # -1..1, + = lower
    prof = np.interp(np.arange(nx) / nx * PX_W, np.arange(PX_W), prof)
    if terr:
        # B-025: wider talus (cliff fraction) — near-vertical heightfield cells streak.
        prof = 1 - 2 * terrace01((1 - prof) / 2, terr, spec.get("cliff", 0.3))          # plateaus up top
    bumps = fft_noise(rng, ny + 1, nx, 3, 60, 0.8)
    # B-025: relief from a 2D field, never an x-only profile extruded in depth (those slopes all
    # run straight back from the camera and read as vertical streaks). Terraced for mesas.
    f2 = fft_noise(rng, ny + 1, nx, 40, 260, 1.6)
    f2 = (f2 - f2.min()) / (f2.max() - f2.min() + 1e-6)
    if spec.get("craters"):
        # B-027: impact craters — raised rim ring + bowl; x distance wraps (layer tiles).
        gy, gx = np.mgrid[0:ny + 1, 0:nx].astype(np.float32)
        for _ in range(spec["craters"]):
            cx, cy = rnd.uniform(0, nx), rnd.uniform(ny * 0.35, ny * 0.95)
            R = rnd.uniform(8, 40)
            dx = (gx - cx + nx / 2) % nx - nx / 2
            d = np.hypot(dx, gy - cy) / R
            f2 = f2 + 0.35 * np.exp(-((d - 1) / 0.18) ** 2) - 0.45 * np.clip(1 - d, 0, 1) ** 1.5
        f2 = (f2 - f2.min()) / (f2.max() - f2.min() + 1e-6)
    mesa = 1 - 2 * (terrace01(f2, terr, spec.get("cliff", 0.3)) if terr else f2)        # -1..1, + = lower
    # Dunes: isotropic 2D undulation on the (now ~square) grid, not an x-only wave.
    dunes = 0.35 * fft_noise(rng, ny + 1, nx, 20, 90, 1.0) if spec.get("dunes") else np.zeros((ny + 1, nx))
    if spec.get("dune_rows"):
        # B-026 desert: rows of asymmetric dune ridges receding in depth (gentle windward rise,
        # steep slip face), warped so crests wander; each row is a smooth silhouette, the
        # opposite of the isotropic lumps above. Mesa noise and bumps are damped under them.
        warp = fft_noise(rng, ny + 1, nx, 60, 400, 1.6)
        ph = np.arange(ny + 1, dtype=np.float32)[:, None] / ny * spec["dune_rows"] + 0.22 * warp
        sd = ph % 1.0
        sl = spec.get("dune_slip", 0.42)            # slip-face share; steeper faces alias in EEVEE shadows (seam)
        hd = np.where(sd < 1 - sl, sd / (1 - sl), (1.0 - sd) / sl)
        dunes = dunes + amp * spec.get("dune_h", 0.9) * hd * hd * (3 - 2 * hd)
        mesa = mesa * spec.get("dune_mesa", 0.35) if mesa is not None else None
    dune = dunes[min(ny, int(ny * (0 - y_front) / (y_back - y_front)))]               # row at y = 0 for placement

    def wy(y):
        w = min(1.0, max(0.0, (y - d0 * 0.5) / max(y_back - d0 * 0.5, 1e-3)))
        return w * w * (3 - 2 * w)

    def zf(i, j):
        y = y_front + (y_back - y_front) * j / ny
        shape = mesa[j, i] if mesa is not None else prof[i]
        return base - amp * shape * wy(y) + dunes[j, i] + amp * spec.get("bumps", 0.06) * bumps[j % (ny + 1), i]
    heightfield("ground", scene.collection, W, y_back, nx, ny, zf, ground, y0=y_front)

    def ground_z(x, y):
        fi = (x % W) / W * nx
        j = min(ny, max(0, int(round(ny * (y - y_front) / (y_back - y_front)))))
        row = dunes[j]
        shp = mesa[j] if mesa is not None else prof
        return (base - amp * wy(y) * float(np.interp(fi, np.arange(nx + 1), np.r_[shp, shp[0]]))
                + float(np.interp(fi, np.arange(nx + 1), np.r_[row, row[0]])))

    # B-025: four boulder families — rounded, angular (faceted), flat slabs, tall pointed —
    # two variants each, so the field doesn't read as one repeated rock.
    families = [  # (subdiv, displacement, noise scale, flat shading, scale xyz)
        (3, 0.55, 0.7, False, (1.0, 0.85, 0.72)),     # rounded
        (1, 0.35, 1.2, True, (1.0, 0.9, 0.8)),        # angular
        (2, 0.3, 0.9, True, (1.35, 1.0, 0.34)),       # flat slab
        (2, 0.4, 0.8, True, (0.62, 0.6, 1.3)),        # tall pointed
    ]
    rocks = []
    for k, (sub, st, sc, flat, s) in enumerate(families):
        for v in range(2):
            c = proto_collection(f"rock{k}_{v}", scene)
            me = blob_mesh(f"rockmesh{k}_{v}", None, 40 + 10 * k + v, subdiv=sub, strength=st, scale=sc)
            if flat:
                for p in me.polygons:
                    p.use_smooth = False
            ob = bpy.data.objects.new("rock", me)
            c.objects.link(ob)
            ob.scale = (s[0], s[1] * rnd.uniform(0.85, 1.1), s[2] * rnd.uniform(0.85, 1.15))
            ob.material_slots[0].link = "OBJECT"
            ob.material_slots[0].material = rockm
            rocks.append(c)
    y_vis = -top * 0.45 if near else d0
    lo, hi = spec["rock_h"]

    def scatter(n, size_lo, size_hi, skew):
        for _ in range(n):
            x = rnd.uniform(0, W)
            y = y_vis + (d1 - y_vis) * rnd.random() ** (1.6 if near else 1.0)
            s = size_lo + (size_hi - size_lo) * rnd.random() ** skew
            if spec.get("seam_keepout") and min(x, W - x) < 1.5 * s:
                # B-026: a big rock straddling x = 0/W rendered differently in its two copies
                # (debug halves); slide it clear of the seam instead.
                x = 1.5 * s if x < W / 2 else W - 1.5 * s
            instance(scene.collection, rocks[rnd.randrange(len(rocks))], (x, y, ground_z(x, y) - 0.2 * s), s,
                     rnd.uniform(0, 6.3), W)
    scatter(spec["rocks"], lo, hi * 1.25, 2.8)          # B-025: wider size spread, few big ones
    if spec.get("pebbles"):
        scatter(spec["pebbles"], 0.05, 0.22, 1.5)
    if spec.get("vents"):                                # B-028 Venus surface: glowing lava vents
        vm = bpy.data.materials.new("vent")
        vm.use_nodes = True
        pr = vm.node_tree.nodes["Principled BSDF"]
        pr.inputs["Base Color"].default_value = lin((90, 30, 10))
        pr.inputs["Emission Color"].default_value = lin((255, 120, 40))
        pr.inputs["Emission Strength"].default_value = 1.6
        _haze(vm, P["haze"], spec["haze"][0], spec["haze"][1], front=W)
        vc = proto_collection("vent", scene)
        vo = bpy.data.objects.new("vent", blob_mesh("ventmesh", None, 77, subdiv=2, strength=0.3, scale=0.8))
        vc.objects.link(vo)
        vo.scale = (1.4, 1.0, 0.25)
        vo.material_slots[0].link = "OBJECT"
        vo.material_slots[0].material = vm
        for _ in range(spec["vents"]):
            x = rnd.uniform(0, W)
            y = y_vis + (d1 - y_vis) * rnd.random()
            s = lo * rnd.uniform(0.4, 1.0)
            instance(scene.collection, vc, (x, y, ground_z(x, y) - 0.05 * s), s, rnd.uniform(0, 6.3), W)
    return render(scene, work, ("near" if near else "mid") + str(seed), W)


# ---------------------------------------------------------------- 2D cloud banks (B-028)

def cloud_bank(P, spec, seed, preview):
    """A painted cumulus bank (B-028 venus_deck): every lit heightfield read as terrain, so the
    deck is drawn in 2D. Silhouette = fbm baseline + overlapping circular billows, drawn top
    first so lower billows overlap the bases of higher ones (cauliflower stacking). Each billow
    is shaded as a sphere lit from the upper front (bright crowns, shadowed undersides); the
    body darkens with depth below the crown line, with soft internal fbm; haze toward the
    preset colour. Periodic in x by construction (wrapped distances, FFT noise).
    Returns HxWx4 float (rgb, alpha)."""
    rng = np.random.default_rng(seed)
    rnd = random.Random(seed)
    W, H = PX_W, PX_H
    base = spec["top"] * H + spec["base_amp"] * fft_noise_1d(rng, W, 120, 1024, 1.4)
    top = base.copy()
    shade = np.zeros((H, W), np.float32)
    owner = np.zeros((H, W), bool)
    L = np.array([-0.35, -0.75, 0.56], np.float32)
    L /= np.linalg.norm(L)
    r0, r1 = spec["r"]
    circles = []
    for _ in range(spec["billows"]):
        cx = rnd.uniform(0, W)
        r = r0 + (r1 - r0) * rnd.random() ** 1.6
        cy = float(np.interp(cx, np.arange(W), base)) + r * rnd.uniform(0.15, 0.55)
        circles.append((cy, cx, r))
        for _k in range(rnd.randint(3, 5)):               # cauliflower: sub-billows on the crown
            a = rnd.uniform(-2.4, -0.7)                    # upper rim (y down)
            rs = r * rnd.uniform(0.22, 0.42)
            circles.append((cy + math.sin(a) * r * 0.82, cx + math.cos(a) * r * 0.82, rs))
    xs = np.arange(W, dtype=np.float32)
    for cy, cx, r in sorted(circles):                     # higher crowns first, lower overlap them
        dx = (xs - cx + W / 2) % W - W / 2
        cols = np.where(np.abs(dx) < r)[0]
        h = np.sqrt(np.maximum(r * r - dx[cols] ** 2, 0))
        top[cols] = np.minimum(top[cols], cy - h)
        y0, y1 = int(max(0, cy - r)), int(min(H, cy + r + 1))
        yy = np.arange(y0, y1, dtype=np.float32)[:, None]
        ddx, ddy = dx[cols][None, :], yy - cy
        inside = ddx ** 2 + ddy ** 2 < r * r
        nz = np.sqrt(np.clip(1 - (ddx ** 2 + ddy ** 2) / (r * r), 0, 1))
        lam = np.clip((ddx / r) * L[0] + (ddy / r) * L[1] + nz * L[2], 0, 1)
        sub = shade[y0:y1][:, cols]
        own = owner[y0:y1][:, cols]
        dist = np.sqrt(ddx ** 2 + ddy ** 2)
        e = np.clip((r - dist) / (0.18 * r), 0, 1)          # soft rim: melt into what's behind
        e = np.where(own, e, inside.astype(np.float32))
        sub[:] = np.where(inside, sub * (1 - e) + lam * e, sub)
        own[inside] = True
        shade[y0:y1, cols] = sub
        owner[y0:y1, cols] = own
    yy = np.arange(H, dtype=np.float32)[:, None]
    d = yy - top[None, :]                                  # depth below the crown line, px
    body = np.clip(1 - d / spec["fall"], 0.25, 1.0) * 0.75  # body away from billows: darker down
    lit = np.where(owner, 0.18 + 0.82 * shade, body)
    fb = fft_noise(rng, H, W, 20, 300, 1.4)
    lit = np.clip(lit + 0.06 * fb, 0, 1)
    crown, under = np.array(spec["crown"], np.float32) / 255, np.array(spec["under"], np.float32) / 255
    rgb = under + (crown - under) * lit[..., None]
    hz = np.array(P["haze"], np.float32) / 255
    rgb = rgb * (1 - spec["haze"]) + hz * spec["haze"]
    edge = 1.5 + 2.5 * fft_noise(rng, H, W, 3, 24, 0.8)    # soft, slightly ragged edge
    alpha = np.clip((d + edge * 0.5) / 2.0 + 0.5, 0, 1)
    out = np.dstack([rgb, alpha]).astype(np.float32)
    if preview:
        out = out[::4, ::4]
    return out


# ---------------------------------------------------------------- B-039: rendered docking bay

def _bay_obj(name, size, loc, mat, coll, W, bevel=0.04):
    """A bevelled box plus linked copies at x - W and x + W (shared mesh, same object space),
    so geometry, shadows and object-space textures all wrap with the period."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        bv = ob.modifiers.new("bevel", "BEVEL")
        bv.width, bv.segments = bevel, 2
    ob.data.materials.append(mat)
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    for dx in (-W, W):
        cp = ob.copy()
        cp.location.x += dx
        coll.objects.link(cp)
    return ob


def _bay_mat(name, col, dirt, rough=0.6, metal=0.4, W=None, stripes=None, emit=None, strength=1.0):
    """Worn industrial paint: periodic grime noise (continuous at the wrap), optional hazard
    stripes (period divides W) and emission."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    pr.inputs["Roughness"].default_value = rough
    pr.inputs["Metallic"].default_value = metal
    geo = N.new("ShaderNodeNewGeometry")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.8; nz.inputs["Detail"].default_value = 6.0
    _periodic_noise(nt, geo.outputs["Position"], W, nz)
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.45, 0.75
    L.new(nz.outputs["Fac"], mr.inputs["Value"])
    base = N.new("ShaderNodeMix"); base.data_type = "RGBA"
    L.new(mr.outputs["Result"], base.inputs[0])
    base.inputs[6].default_value = lin(col); base.inputs[7].default_value = lin(dirt)
    out = base.outputs[2]
    if stripes:
        # Diagonal hazard stripes: fract((x + z) / period) < 0.5; the period divides W.
        sep = N.new("ShaderNodeSeparateXYZ")
        L.new(geo.outputs["Position"], sep.inputs[0])
        add = N.new("ShaderNodeMath"); add.operation = "ADD"
        L.new(sep.outputs["X"], add.inputs[0]); L.new(sep.outputs["Z"], add.inputs[1])
        fr = N.new("ShaderNodeMath"); fr.operation = "FLOORED_MODULO"; fr.inputs[1].default_value = stripes
        L.new(add.outputs[0], fr.inputs[0])
        lt = N.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = stripes / 2
        L.new(fr.outputs[0], lt.inputs[0])
        sm = N.new("ShaderNodeMix"); sm.data_type = "RGBA"
        L.new(lt.outputs[0], sm.inputs[0])
        L.new(out, sm.inputs[6]); sm.inputs[7].default_value = lin((26, 26, 28))
        out = sm.outputs[2]
    L.new(out, pr.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25
    L.new(nz.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], pr.inputs["Normal"])
    if emit:
        pr.inputs["Emission Color"].default_value = lin(emit)
        pr.inputs["Emission Strength"].default_value = strength
    return m


def _stars_mat(name, W):
    """Black space with sparse emissive stars (periodic noise, so the window tiles)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    pr.inputs["Base Color"].default_value = (0.004, 0.005, 0.01, 1)
    geo = N.new("ShaderNodeNewGeometry")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 25.0; nz.inputs["Detail"].default_value = 0.0
    _periodic_noise(nt, geo.outputs["Position"], W, nz)
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.8, 0.83   # sparse pinpoints
    mr.inputs["To Max"].default_value = 3.0
    L.new(nz.outputs["Fac"], mr.inputs["Value"])
    L.new(mr.outputs["Result"], pr.inputs["Emission Strength"])
    pr.inputs["Emission Color"].default_value = (1, 1, 1, 1)
    return m


def bay_layer(P, spec, seed, preview, work, which):
    W = spec["W"]
    H = W / 2
    scene = new_scene(P, W, preview, spec.get("tilt", 0.0), (W / 2, 0.0, H / 2 + spec.get("frame_up", 0.0) * H))
    coll = scene.collection
    rnd = random.Random(seed)
    hz = P["haze"]

    def haze(m):
        _haze(m, hz, spec["haze"][0], spec["haze"][1], None, front=W)
        return m
    if which == 0:                                                         # back wall (opaque)
        panel = haze(_bay_mat("panel", (92, 98, 108), (54, 56, 62), W=W))
        seam = haze(_bay_mat("seam", (40, 42, 48), (30, 30, 34), W=W, metal=0.6))
        frame = haze(_bay_mat("frame", (70, 74, 82), (44, 46, 52), W=W, metal=0.7))
        haz = haze(_bay_mat("hazard", (222, 176, 40), (120, 96, 40), W=W, stripes=W / 80))
        lamp = _bay_mat("lamp", (255, 240, 210), (255, 240, 210), W=W, emit=(255, 238, 205), strength=4.0)
        y = 6.0
        # Backing above and below the window band only (full height hid the star plane).
        _bay_obj("backing_lo", (W, 0.2, 0.56 * H), (W / 2, y + 0.3, 0.28 * H), seam, coll, W, bevel=0)
        _bay_obj("backing_hi", (W, 0.2, 0.22 * H), (W / 2, y + 0.3, 0.89 * H), seam, coll, W, bevel=0)
        pw, ph = W / 16, 2.4
        for i in range(16):
            for j in range(int(H / ph)):
                z = (j + 0.5) * ph
                if 0.56 * H < z < 0.78 * H:                                  # window band
                    continue
                d = rnd.uniform(0.0, 0.08)
                _bay_obj(f"p{i}_{j}", (pw - 0.12, 0.2, ph - 0.12), ((i + 0.5) * pw, y - d, z), panel, coll, W, 0.05)
        # Observation window: frame, mullions, star plane behind.
        z0, z1 = 0.56 * H, 0.78 * H
        _bay_obj("stars", (W, 0.1, z1 - z0), (W / 2, y + 2.0, (z0 + z1) / 2), _stars_mat("stars", W), coll, W, 0)
        _bay_obj("sill", (W, 0.6, 0.35), (W / 2, y - 0.2, z0), frame, coll, W)
        _bay_obj("head", (W, 0.6, 0.35), (W / 2, y - 0.2, z1), frame, coll, W)
        for i in range(8):
            _bay_obj(f"mull{i}", (0.35, 0.5, z1 - z0), (i * W / 8, y - 0.15, (z0 + z1) / 2), frame, coll, W)
        for i in range(8):                                                   # ceiling light fixtures
            _bay_obj(f"lamp{i}", (2.2, 0.3, 0.25), ((i + 0.5) * W / 8, y - 0.4, H - 1.2), lamp, coll, W, 0.03)
        _bay_obj("hazard", (W, 0.25, 0.8), (W / 2, y - 0.3, 0.2 * H), haz, coll, W, 0.02)
    elif which == 1:                                                       # structure
        steel = haze(_bay_mat("steel", (112, 116, 124), (60, 62, 68), W=W, metal=0.8, rough=0.45))
        yellow = haze(_bay_mat("crane", (222, 176, 40), (110, 90, 40), W=W, metal=0.3))
        light = _bay_mat("work", (255, 214, 140), (255, 214, 140), W=W, emit=(255, 214, 140), strength=5.0)
        dark = haze(_bay_mat("cable", (30, 30, 32), (20, 20, 22), W=W, metal=0.5))
        for x in (W / 4, 3 * W / 4):                                         # I-beam columns
            _bay_obj(f"web{x}", (0.25, 0.6, H), (x, 0, H / 2), steel, coll, W, 0.02)
            for s in (-1, 1):
                _bay_obj(f"fl{x}{s}", (0.9, 0.12, H), (x, s * 0.36, H / 2), steel, coll, W, 0.02)
            for z in range(2, int(H), 3):
                _bay_obj(f"bolt{x}{z}", (1.1, 0.8, 0.18), (x, 0, z), steel, coll, W, 0.02)
            _bay_obj(f"wl{x}", (0.4, 0.3, 0.3), (x + 0.75, -0.4, 0.45 * H), light, coll, W, 0.02)
        ztop = H - 1.6
        _bay_obj("chordA", (W, 0.3, 0.35), (W / 2, 0, ztop + 0.9), steel, coll, W, 0.02)
        _bay_obj("chordB", (W, 0.3, 0.35), (W / 2, 0, ztop - 0.9), steel, coll, W, 0.02)
        n = int(W / 2)
        for i in range(n):                                                   # lattice: one diagonal per 2 m
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(i * 2 + 1, 0, ztop))
            d = bpy.context.active_object
            d.scale = (2.6, 0.18, 0.18)
            d.rotation_euler = (0, math.radians(40 if i % 2 else -40), 0)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            d.data.materials.append(steel)
            for c in list(d.users_collection):
                c.objects.unlink(d)
            coll.objects.link(d)
            for dx in (-W, W):
                cp = d.copy(); cp.location.x += dx; coll.objects.link(cp)
        for x in (0.3 * W, 0.8 * W):                                         # crane trolley, cable, hook block
            _bay_obj(f"trolley{x}", (2.2, 1.0, 0.9), (x, 0, ztop - 1.5), yellow, coll, W, 0.06)
            _bay_obj(f"cable{x}", (0.08, 0.08, 6.0), (x, 0, ztop - 5.0), dark, coll, W, 0)
            _bay_obj(f"hook{x}", (1.0, 0.7, 1.2), (x, 0, ztop - 8.5), yellow, coll, W, 0.08)
    else:                                                                  # deck
        deck = haze(_bay_mat("deck", (134, 138, 144), (70, 72, 76), W=W, metal=0.6, rough=0.5))
        seam = haze(_bay_mat("dseam", (60, 62, 68), (40, 40, 44), W=W))
        haz = haze(_bay_mat("dhaz", (232, 184, 44), (120, 96, 40), W=W, stripes=W / 48))
        orange = haze(_bay_mat("crateO", (214, 112, 40), (90, 60, 40), W=W, metal=0.2))
        grey = haze(_bay_mat("crateG", (120, 126, 132), (70, 72, 76), W=W, metal=0.3))
        band = haze(_bay_mat("stencil", (30, 30, 32), (20, 20, 22), W=W))
        rail = haze(_bay_mat("rail", (186, 190, 194), (110, 112, 116), W=W, metal=0.8, rough=0.35))
        top = 1.0
        _bay_obj("slab", (W, 14.0, top), (W / 2, 2.0, top / 2), seam, coll, W, 0)
        for i in range(12):                                                  # plates with seams
            for j in range(3):
                _bay_obj(f"pl{i}{j}", (W / 12 - 0.08, 4.4, 0.06), ((i + 0.5) * W / 12, -3.0 + j * 4.5, top + 0.03),
                         deck, coll, W, 0.02)
        _bay_obj("edge", (W, 0.6, 0.12), (W / 2, -5.4, top + 0.06), haz, coll, W, 0.01)
        for k in range(int(W / 4)):                                          # railing posts, 4 m spacing
            _bay_obj(f"post{k}", (0.08, 0.08, 1.1), (k * 4 + 2, 3.5, top + 0.55), rail, coll, W, 0)
        _bay_obj("rail", (W, 0.08, 0.08), (W / 2, 3.5, top + 1.1), rail, coll, W, 0)
        for cx, stack in ((3.0, ("O", "G")), (11.0, ("G",)), (17.5, ("O", "O"))):   # crate stacks
            z = top
            for k, c in enumerate(stack):
                w, h = (2.4, 1.8) if k == 0 else (2.0, 1.5)
                m = orange if c == "O" else grey
                _bay_obj(f"cr{cx}{k}", (w, 2.2, h), (cx + 0.2 * k, 1.0, z + h / 2), m, coll, W, 0.06)
                _bay_obj(f"st{cx}{k}", (w * 0.7, 0.02, 0.22), (cx + 0.2 * k, -0.11, z + h * 0.55), band, coll, W, 0)
                z += h
    return render(scene, work, f"bay{which}_{seed}", W)


# ---------------------------------------------------------------- entry

def _finish_transparent(px):
    a = px[..., 3]
    rgb, _ = post.dilate(px[..., :3], a >= 0.5, 10)
    return np.dstack([pngio.to_u8(rgb), pngio.to_u8(a)])


def generate(entry, ctx):
    _, planet, layer = entry["key"].split("/")
    P = PRESETS[entry.get("preset", planet)]
    seed = int(entry.get("seed", 1))
    preview, work = ctx["preview"], ctx["work"]
    if P.get("bay"):                                     # B-039: rendered 3D docking bay
        k = int(layer[-1])
        px = bay_layer(P, P["bay"][k], seed, preview, work, k)
        if layer == "layer0":
            rgb = px[..., :3] * px[..., 3:4] + np.array([0.03, 0.03, 0.04]) * (1 - px[..., 3:4])
            return {"color": np.dstack([pngio.to_u8(rgb), np.full(rgb.shape[:2], 255, np.uint8)])}
        return {"color": _finish_transparent(px)}
    if P.get("banks"):                                   # B-028: painted 2D cloud deck
        bank = cloud_bank(P, P["banks"][int(layer[-1])], seed, preview)
        if layer == "layer0":
            sky = GB.sky_rgb(GB.PRESETS[planet], np.random.default_rng(seed))
            if preview:
                sky = sky[::4, ::4]
            a = bank[..., 3:4]
            rgb = sky * (1 - a) + bank[..., :3] * a
            return {"color": np.dstack([pngio.to_u8(rgb), np.full(rgb.shape[:2], 255, np.uint8)])}
        return {"color": _finish_transparent(bank)}
    if layer == "layer0":
        sky = GB.sky_rgb(GB.PRESETS[planet], np.random.default_rng(seed))
        if preview:
            sky = sky[::4, ::4]
        rng_px = far_layer(P, P["far"], seed, preview, work)
        a = rng_px[..., 3:4]
        rgb = sky * (1 - a) + rng_px[..., :3] * a
        return {"color": np.dstack([pngio.to_u8(rgb), np.full(rgb.shape[:2], 255, np.uint8)])}
    spec = P["mid"] if layer == "layer1" else P["near"]
    build = forest_layer if "trees" in spec else rock_layer
    px = build(P, spec, seed, preview, work, near=(layer == "layer2"))
    return {"color": _finish_transparent(px)}
