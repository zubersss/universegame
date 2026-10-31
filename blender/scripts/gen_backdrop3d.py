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
from meridian.noise import fft_noise

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
                 rocks=30, rock_h=(2, 7), tilt=12.0, frame_up=-0.08, dune_rows=5, dune_h=0.8),
        near=dict(W=64.0, level=0.26, amp=0.07, bumps=0.004, depth=(3, 14), haze=(0.05, 0.003),
                  ground=[(226, 196, 144), (208, 176, 124)], dune_rows=4, dune_h=0.9, dune_mesa=0.15,
                  rocks=14, rock_h=(0.3, 1.4), pebbles=120, tilt=18.0, frame_up=0.12),
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
        far=dict(W=9000.0, level=0.30, peak=0.52, rock=[(112, 118, 104), (136, 140, 120)], snow=(0, 0, 0),
                 snowline=9.0, haze=(0.42, 0.00004), tilt=6.0, sea=dict(level=0.34, color=(46, 98, 140))),
        mid=dict(W=700.0, level=0.40, amp=0.10, ground=[(84, 116, 62), (100, 124, 70)], trees=160, protos=6,
                 tree_h=(10, 20), conifer=0.25, depth=(20, 140), haze=(0.22, 0.0012), fog=(0.2, 0.22),
                 tilt=12.0, frame_up=-0.08),
        near=dict(W=64.0, level=0.28, amp=0.04, ground=[(96, 124, 64), (120, 136, 76), (176, 160, 120)], trees=6,
                  protos=4, tree_h=(7, 11), conifer=0.2, depth=(3, 14), haze=(0.06, 0.004),
                  tufts=4000, shrubs=50, tilt=18.0, frame_up=0.12),
        leaf=[(56, 92, 40), (74, 108, 46), (92, 120, 52)],
        needle=[(32, 60, 40), (44, 72, 46)],
        bark=(90, 74, 60),
    ),
    # B-027 Mercury (Bible §7.3): airless, so harsh small-angle sun, almost no ambient, little
    # haze; cratered relief; blinding grey regolith; violet twilight in the sky only.
    "mercury": dict(
        sun=dict(dir=(-0.85, 0.3, -0.42), strength=6.0, color=(1.0, 0.98, 0.94), angle=0.5),
        ambient=((0.3, 0.24, 0.42), 0.06),
        haze=(60, 44, 90),
        far=dict(W=9000.0, level=0.36, peak=0.56, rock=[(118, 116, 120), (150, 148, 152)], snow=(0, 0, 0),
                 snowline=9.0, haze=(0.3, 0.00003), tilt=6.0),
        mid=dict(W=700.0, level=0.40, amp=0.10, depth=(20, 140), haze=(0.1, 0.0006),
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
        sun=dict(dir=(-0.4, 0.8, -0.2), strength=3.0, color=(1.0, 0.86, 0.62), angle=6.0),   # low, from behind: backlit
        ambient=((0.86, 0.72, 0.52), 0.6),
        haze=(232, 206, 160),
        far=dict(W=9000.0, level=0.36, peak=0.86, rock=[(236, 214, 170), (214, 184, 136)], snow=(0, 0, 0),
                 snowline=9.0, haze=(0.36, 0.00004), tilt=6.0),
        mid=dict(W=700.0, level=0.40, amp=0.10, depth=(20, 140), haze=(0.26, 0.0012),
                 ground=[(228, 204, 158), (206, 176, 128)], rocks=0, rock_h=(1, 2), tilt=12.0, frame_up=-0.08, dunes=True),
        near=dict(W=64.0, level=0.26, amp=0.06, depth=(3, 14), haze=(0.08, 0.003),
                  ground=[(238, 220, 180), (214, 188, 140)], dunes=True, rocks=0, rock_h=(0.3, 1), tilt=18.0, frame_up=0.12),
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
            L.new(_wrapped(nt, geo.outputs["Position"], W), nz.inputs["Vector"])
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
    def zf(i, j):
        y = y_front + (y_back - y_front) * j / ny
        w = min(1.0, max(0.0, (y - d0 * 0.5) / max(y_back - d0 * 0.5, 1e-3)))
        w = w * w * (3 - 2 * w)
        return base - amp * prof[i] * w + amp * 0.06 * bumps[j % (ny + 1), i]
    heightfield("ground", scene.collection, W, y_back, nx, ny, zf, mats["ground"], y0=y_front)
    def ground_z(x, y):
        w = min(1.0, max(0.0, (y - d0 * 0.5) / max(y_back - d0 * 0.5, 1e-3)))
        w = w * w * (3 - 2 * w)
        return base - amp * w * float(np.interp((x % W) / W * nx, np.arange(nx + 1), np.r_[prof, prof[0]]))
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
        return top * spec["level"] + top * (spec["peak"] - spec["level"]) * bell * ridge[j, i] + top * 0.012 * rough[j, i] - top * 0.15 * (1 - bell)
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
    nt.links.new(_wrapped(nt, geo.outputs["Position"], W), nz.inputs["Vector"])
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
    L.new(_wrapped(nt, geo.outputs["Position"], W), warp.inputs["Vector"])
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
