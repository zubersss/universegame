"""Builds blender/sources/icons/icons.blend: item icons batch 1 (B-013) and batch 2 (B-042).

One collection per item (`icon_<item>`), each centred on the origin and fitting a ~0.8 m
box, plus a shared `icon_lights` rig (sun from the upper right, cool sky fill). render.py
renders them lit ("beauty") with the `icon` camera (3/4 view from front-right, above), so
every icon has the same lighting angle. Distinct silhouettes and colours keep each item
readable at 32 px. Deterministic; re-run any time:

  blender --background --factory-startup --python blender/scripts/build_icons.py
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_pilgrim import lin  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "icons", "icons.blend")

ITEMS = ["iron", "copper", "carbon", "silica", "water_ice", "oxygen", "launch_fuel", "hematite",
         "perchlorate", "clay", "aluminium", "living_seed", "wood", "stone", "sand", "nickel"]
# B-042 batch 2 (M3 resources and crafting). Appended after batch 1 so batch 1's shared random
# stream (and its icons) stay identical. `nickel` was already in batch 1.
ITEMS2 = ["solarite", "vitriol_glass", "sulfur", "basalt", "graphite", "polar_ice", "deep_core_sample",
          "launch_fuel_cell", "suit_patch", "cryo_pad", "thermal_pad", "radiation_liner",
          "smelter_bar_iron", "smelter_bar_copper", "circuit_board"]


# ---------------------------------------------------------------- materials

def mat(name, a, b=None, metallic=0.0, rough=0.6, noise=6.0, bump=0.3, emit=None, strength=1.0, alpha=1.0):
    """Principled: colour mottled between a and b by object-space noise, with matching bump."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    pr.inputs["Metallic"].default_value = metallic
    pr.inputs["Roughness"].default_value = rough
    if emit:
        pr.inputs["Emission Color"].default_value = lin(emit)
        pr.inputs["Emission Strength"].default_value = strength
    if b is None:
        pr.inputs["Base Color"].default_value = lin(a)
        return m
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = noise; nz.inputs["Detail"].default_value = 8.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.35; mr.inputs["From Max"].default_value = 0.7
    L.new(nz.outputs["Fac"], mr.inputs["Value"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
    L.new(mr.outputs["Result"], mx.inputs[0])
    mx.inputs[6].default_value = lin(a); mx.inputs[7].default_value = lin(b)
    L.new(mx.outputs[2], pr.inputs["Base Color"])
    if bump:
        bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        L.new(nz.outputs["Fac"], bp.inputs["Height"])
        L.new(bp.outputs["Normal"], pr.inputs["Normal"])
    return m


# ---------------------------------------------------------------- geometry helpers

def _link(ob, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob


def rock(coll, name, m, seed, size=(0.36, 0.3, 0.26), subdiv=3, strength=0.35, scale=0.9, flat=False, loc=(0, 0, 0)):
    """A displaced icosphere lump; flat=True gives a faceted (coal / ore) look."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=1.0, location=loc)
    ob = _link(bpy.context.active_object, coll)
    ob.name = name
    tex = bpy.data.textures.new(name + "_tex", "CLOUDS")
    tex.noise_scale = scale
    d = ob.modifiers.new("disp", "DISPLACE")
    d.texture, d.strength, d.texture_coords = tex, strength, "GLOBAL"
    ob.scale = size
    ob.rotation_euler = (seed * 0.7, seed * 1.3, seed * 0.4)
    if flat:
        bpy.ops.object.shade_flat()
    else:
        bpy.ops.object.shade_smooth()
    ob.data.materials.append(m)
    return ob


def prism(coll, name, m, base, height, radius, tilt, rot_z):
    """Hexagonal crystal with a pointed tip."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=radius, depth=height, location=(0, 0, height / 2))
    ob = _link(bpy.context.active_object, coll)
    ob.name = name
    me = ob.data
    top = max(v.co.z for v in me.vertices)
    for v in me.vertices:
        if v.co.z >= top - 1e-6:
            v.co.x *= 0.15
            v.co.y *= 0.15
            v.co.z += radius * 1.2
    ob.location = base
    ob.rotation_euler = (tilt[0], tilt[1], rot_z)
    bpy.ops.object.shade_flat()
    ob.data.materials.append(m)
    return ob


def cyl(coll, name, m, r, depth, loc, rot=(0, 0, 0), verts=40, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    ob = _link(bpy.context.active_object, coll)
    ob.name = name
    bev = ob.modifiers.new("bev", "BEVEL")
    bev.width, bev.segments = min(r, depth) * 0.12, 3
    if smooth:
        bpy.ops.object.shade_smooth()
    ob.data.materials.append(m)
    return ob


def ball(coll, name, m, r, loc, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=r, location=loc)
    ob = _link(bpy.context.active_object, coll)
    ob.name = name
    ob.scale = scale
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(m)
    return ob


def box(coll, name, m, size, loc, rot=(0, 0, 0), bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    ob = _link(bpy.context.active_object, coll)
    ob.name = name
    ob.scale = size
    bv = ob.modifiers.new("bev", "BEVEL")
    bv.width, bv.segments = bevel, 3
    ob.data.materials.append(m)
    return ob


# ---------------------------------------------------------------- items

def build_item(item, coll, rnd):
    if item == "iron":
        rock(coll, "ore", mat("iron_ore", (88, 80, 76), (150, 84, 54), 0.4, 0.55, 7), 1, flat=True, subdiv=2)
        for k in range(5):   # metallic flecks
            ball(coll, f"fleck{k}", mat(f"iron_fleck{k}", (176, 170, 168), metallic=1.0, rough=0.3), 0.035,
                 (rnd.uniform(-0.2, 0.2), rnd.uniform(-0.28, -0.18), rnd.uniform(-0.12, 0.16)))
    elif item == "copper":
        rock(coll, "ore", mat("copper_ore", (70, 132, 116), (54, 92, 84), 0.0, 0.7, 6), 2, flat=True, subdiv=2)
        for k in range(4):
            ball(coll, f"vein{k}", mat(f"copper_vein{k}", (214, 120, 70), metallic=1.0, rough=0.35), 0.05,
                 (rnd.uniform(-0.18, 0.18), rnd.uniform(-0.28, -0.2), rnd.uniform(-0.1, 0.14)), (1.4, 0.6, 0.8))
    elif item == "carbon":
        rock(coll, "coal", mat("coal", (30, 30, 32), (54, 54, 58), 0.0, 0.3, 9, 0.2), 3, flat=True, subdiv=1, strength=0.25)
    elif item == "silica":
        q = mat("quartz", (244, 246, 250), (214, 222, 232), 0.0, 0.15, 4, 0.0)
        # Crystals dominate (they are the item); the matrix rock is just a small foot.
        for k, (pos, h, r, tilt) in enumerate((((0, 0, -0.16), 0.42, 0.11, (0.0, 0.05)), ((0.15, 0.04, -0.16), 0.32, 0.09, (0.4, 0.2)),
                                               ((-0.15, 0.02, -0.16), 0.3, 0.085, (-0.35, -0.25)), ((0.04, 0.14, -0.16), 0.26, 0.08, (0.2, -0.5)))):
            prism(coll, f"crystal{k}", q, pos, h, r, tilt, rnd.uniform(0, 1))
        rock(coll, "base", mat("silica_base", (150, 140, 128), (120, 112, 102), 0, 0.8, 8), 4, (0.2, 0.15, 0.05), loc=(0, 0, -0.17))
    elif item == "water_ice":
        ice = mat("ice", (196, 226, 246), (150, 196, 228), 0.0, 0.08, 3, 0.15)
        rock(coll, "ice", ice, 5, (0.32, 0.28, 0.3), subdiv=1, strength=0.2, flat=True)
    elif item == "oxygen":
        cyl(coll, "tank", mat("o2_body", (232, 234, 238)), 0.15, 0.6, (0, 0, -0.02))
        cyl(coll, "band", mat("o2_band", (40, 110, 210)), 0.153, 0.12, (0, 0, 0.0))
        cyl(coll, "neck", mat("o2_neck", (150, 154, 160), metallic=1.0, rough=0.3), 0.05, 0.1, (0, 0, 0.32))
        cyl(coll, "valve", mat("o2_valve", (40, 110, 210)), 0.07, 0.035, (0, 0, 0.38))
    elif item == "launch_fuel":
        body = mat("fuel_body", (214, 74, 38), (176, 56, 30), 0.2, 0.45, 5, 0.05)
        box(coll, "can", body, (0.36, 0.2, 0.5), (0, 0, -0.04), bevel=0.04)
        box(coll, "stripe", mat("fuel_stripe", (232, 186, 40)), (0.365, 0.205, 0.08), (0, 0, 0.08), bevel=0.01)
        cyl(coll, "spout", mat("fuel_spout", (60, 62, 66), metallic=1.0, rough=0.4), 0.05, 0.12, (0.1, 0, 0.27))
        box(coll, "handle", mat("fuel_handle", (40, 40, 42)), (0.18, 0.05, 0.04), (-0.06, 0, 0.25), bevel=0.012)
    elif item == "hematite":
        hm = mat("hematite", (70, 52, 54), (112, 70, 64), 0.85, 0.35, 10, 0.1)
        for k, (p, r) in enumerate((((0, 0, -0.05), 0.15), ((0.2, 0.05, -0.12), 0.11), ((-0.17, 0.08, -0.13), 0.1),
                                    ((0.05, 0.18, -0.15), 0.09), ((-0.02, -0.12, 0.13), 0.1))):
            ball(coll, f"spherule{k}", hm, r, p)
    elif item == "perchlorate":
        salt = mat("perchlorate", (238, 234, 214), (214, 206, 170), 0.0, 0.5, 8, 0.15)
        for k in range(7):
            s = rnd.uniform(0.09, 0.17)
            box(coll, f"cube{k}", salt, (s, s, s), (rnd.uniform(-0.17, 0.17), rnd.uniform(-0.12, 0.12), rnd.uniform(-0.22, 0.1)),
                (rnd.uniform(0, 1), rnd.uniform(0, 1), rnd.uniform(0, 1)), bevel=0.008)
    elif item == "clay":
        rock(coll, "clay", mat("clay", (164, 92, 64), (134, 72, 50), 0.0, 0.75, 3, 0.25), 6, (0.36, 0.32, 0.22),
             subdiv=4, strength=0.12, scale=1.6)
    elif item == "aluminium":
        # Partly metallic: a fully metallic surface only mirrors the dim world and reads dark.
        al = mat("aluminium", (218, 222, 228), (196, 200, 208), 0.55, 0.3, 12, 0.05)
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        ob = _link(bpy.context.active_object, coll)
        ob.name = "ingot"
        for v in ob.data.vertices:              # trapezoid ingot: narrower on top
            if v.co.z > 0:
                v.co.x *= 0.78
                v.co.y *= 0.7
        ob.scale = (0.6, 0.3, 0.2)
        bv = ob.modifiers.new("bev", "BEVEL"); bv.width, bv.segments = 0.03, 3
        ob.data.materials.append(al)
    elif item == "living_seed":
        ball(coll, "pod", mat("seed_pod", (132, 92, 52), (104, 70, 40), 0.0, 0.6, 9, 0.25), 0.17, (0, 0, -0.14), (1.0, 0.85, 1.25))
        leaf = mat("seed_leaf", (78, 176, 72), (52, 132, 52), 0.0, 0.5, 5, 0.1, emit=(60, 200, 90), strength=0.15)
        cyl(coll, "stem", leaf, 0.018, 0.22, (0, 0, 0.14))
        for k, ang in enumerate((0.6, 2.4)):
            ball(coll, f"leaf{k}", leaf, 0.1, (0.09 * math.cos(ang), 0.09 * math.sin(ang), 0.27), (1.6, 0.6, 0.25))
            bpy.context.active_object.rotation_euler = (0.0, -0.45 if k == 0 else 0.45, ang)
    elif item == "wood":
        bark = mat("bark", (96, 66, 44), (70, 48, 32), 0.0, 0.85, 14, 0.5)
        cyl(coll, "log", bark, 0.2, 0.5, (0, 0, 0), rot=(0, math.pi / 2, 0.3), verts=48)
        grain = bpy.data.materials.new("end_grain")
        grain.use_nodes = True
        nt = grain.node_tree
        pr = nt.nodes["Principled BSDF"]
        wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = "RINGS"; wave.rings_direction = "SPHERICAL"
        wave.inputs["Scale"].default_value = 1.6; wave.inputs["Distortion"].default_value = 3.0
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
        nt.links.new(wave.outputs["Fac"], mx.inputs[0])
        mx.inputs[6].default_value = lin((214, 172, 120)); mx.inputs[7].default_value = lin((176, 128, 82))
        nt.links.new(mx.outputs[2], pr.inputs["Base Color"])
        cap = cyl(coll, "end", grain, 0.185, 0.02, (0, 0, 0), rot=(0, math.pi / 2, 0.3), verts=48)
        cap.location = (0.25 * math.cos(0.3), 0.25 * math.sin(0.3), 0.0)   # on the log's +x end
    elif item == "stone":
        rock(coll, "stone", mat("stone", (128, 126, 122), (96, 94, 92), 0.0, 0.8, 5, 0.4), 7, (0.36, 0.3, 0.24), subdiv=3, strength=0.3)
    elif item == "sand":
        bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.38, radius2=0.0, depth=0.32, location=(0, 0, -0.12))
        ob = _link(bpy.context.active_object, coll)
        ob.name = "pile"
        sub = ob.modifiers.new("sub", "SUBSURF"); sub.levels = sub.render_levels = 2
        bpy.ops.object.shade_smooth()
        ob.data.materials.append(mat("sand", (222, 196, 140), (196, 166, 112), 0.0, 0.9, 40, 0.6))
    elif item == "nickel":
        rock(coll, "meteorite", mat("nickel_iron", (184, 184, 178), (128, 122, 116), 0.55, 0.38, 11, 0.6), 8,
             (0.34, 0.28, 0.24), subdiv=3, strength=0.4, scale=0.5)


def ingot(coll, name, m):
    """Trapezoid ingot (narrower on top), as batch 1's aluminium."""
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = _link(bpy.context.active_object, coll)
    ob.name = name
    for v in ob.data.vertices:
        if v.co.z > 0:
            v.co.x *= 0.78
            v.co.y *= 0.7
    ob.scale = (0.6, 0.3, 0.2)
    bv = ob.modifiers.new("bev", "BEVEL"); bv.width, bv.segments = 0.03, 3
    ob.data.materials.append(m)
    return ob


def quilted_pad(coll, name, m, accent, accent_name):
    """A square quilted pad (2x2 puffy cells) with an emissive accent strip across it."""
    for i in range(2):
        for j in range(2):
            box(coll, f"{name}_cell{i}{j}", m, (0.27, 0.27, 0.1), ((i - 0.5) * 0.28, (j - 0.5) * 0.28, 0), bevel=0.05)
    box(coll, accent_name, accent, (0.58, 0.05, 0.03), (0, 0, 0.06), bevel=0.01)


def build_item2(item, coll, rnd):
    if item == "solarite":
        amber = mat("solarite", (255, 200, 110), (255, 160, 60), 0.0, 0.15, 4, 0.0, emit=(255, 196, 100), strength=1.2)
        for k, (pos, h, r, tilt) in enumerate((((0, 0, -0.16), 0.46, 0.1, (0.0, 0.05)), ((0.14, 0.05, -0.16), 0.34, 0.08, (0.45, 0.2)),
                                               ((-0.14, 0.03, -0.16), 0.3, 0.08, (-0.4, -0.2)), ((0.03, -0.13, -0.16), 0.26, 0.07, (0.2, -0.5)))):
            prism(coll, f"crystal{k}", amber, pos, h, r, tilt, rnd.uniform(0, 1))
        rock(coll, "base", mat("solarite_base", (60, 56, 58), (40, 38, 40), 0, 0.6, 8), 21, (0.22, 0.16, 0.05), loc=(0, 0, -0.17))
    elif item == "vitriol_glass":
        g = mat("vitriol", (176, 214, 70), (120, 168, 40), 0.0, 0.05, 3, 0.0, alpha=0.8)
        rock(coll, "shard", g, 22, (0.36, 0.22, 0.3), subdiv=1, strength=0.35, flat=True)
    elif item == "sulfur":
        sm = mat("sulfur", (236, 214, 60), (206, 176, 40), 0.0, 0.55, 6, 0.3)
        rock(coll, "lump", sm, 23, (0.34, 0.3, 0.26), subdiv=2, strength=0.3, flat=True)
        for k in range(4):
            box(coll, f"xtal{k}", sm, (0.08, 0.08, 0.08), (rnd.uniform(-0.18, 0.18), rnd.uniform(-0.25, -0.15), rnd.uniform(-0.05, 0.15)),
                (rnd.uniform(0, 1), rnd.uniform(0, 1), rnd.uniform(0, 1)), bevel=0.005)
    elif item == "basalt":
        bm_ = mat("basalt", (96, 96, 104), (70, 70, 78), 0.0, 0.55, 8, 0.4)   # lighter: read at 32 px on dark UI
        for k, (x, y, h) in enumerate(((0, 0, 0.5), (0.17, 0.05, 0.4), (-0.15, 0.06, 0.36), (0.02, 0.17, 0.3))):
            ob = cyl(coll, f"column{k}", bm_, 0.1, h, (x, y, -0.25 + h / 2), verts=6, smooth=False)
    elif item == "graphite":
        gm = mat("graphite", (120, 124, 132), (86, 90, 98), 0.8, 0.22, 10, 0.1)   # silvery sheen
        for k in range(5):
            box(coll, f"flake{k}", gm, (0.5 - 0.05 * k, 0.36 - 0.04 * k, 0.05), (0.02 * k, -0.01 * k, -0.12 + 0.06 * k),
                (0, 0, rnd.uniform(-0.25, 0.25)), bevel=0.01)
    elif item == "polar_ice":
        ice = mat("polar_ice", (226, 240, 252), (190, 216, 240), 0.0, 0.1, 3, 0.1)
        box(coll, "block", ice, (0.46, 0.38, 0.4), (0, 0, 0), bevel=0.05)
        for k, z in enumerate((-0.08, 0.06)):                          # dark dust bands in the ice
            box(coll, f"dust{k}", mat(f"dust{k}", (110, 108, 112)), (0.465, 0.385, 0.025), (0, 0, z), bevel=0.01)
    elif item == "deep_core_sample":
        for k, (col, h) in enumerate((((120, 96, 74), 0.12), ((70, 66, 70), 0.1), ((190, 172, 130), 0.08), ((96, 70, 56), 0.12))):
            z = -0.2 + sum(x[1] for x in (((0, 0), 0.12), ((0, 0), 0.1), ((0, 0), 0.08), ((0, 0), 0.12))[:k]) + h / 2
            cyl(coll, f"stratum{k}", mat(f"stratum{k}", col, None, 0.0, 0.8, 9, 0.4), 0.12, h, (0, 0, z))
        steel = mat("core_cap", (160, 164, 170), metallic=1.0, rough=0.3)
        cyl(coll, "cap_lo", steel, 0.13, 0.04, (0, 0, -0.22))
        cyl(coll, "cap_hi", steel, 0.13, 0.04, (0, 0, 0.24))
    elif item == "launch_fuel_cell":
        cyl(coll, "cell", mat("cell_body", (230, 232, 236), metallic=0.3, rough=0.35), 0.15, 0.5, (0, 0, -0.02))
        cyl(coll, "glow", mat("cell_glow", (120, 40, 20), emit=(255, 110, 40), strength=1.6), 0.153, 0.1, (0, 0, -0.02))
        cyl(coll, "term", mat("cell_term", (60, 62, 66), metallic=1.0, rough=0.4), 0.07, 0.06, (0, 0, 0.26))
        cyl(coll, "foot", mat("cell_foot", (60, 62, 66), metallic=1.0, rough=0.4), 0.155, 0.04, (0, 0, -0.27))
    elif item == "suit_patch":
        box(coll, "patch", mat("patch", (214, 112, 44), (176, 86, 32), 0.0, 0.85, 20, 0.3), (0.5, 0.5, 0.05), (0, 0, 0), bevel=0.04)
        st = mat("stitch", (240, 236, 220))
        for k in range(10):                                            # stitches round the edge
            t = k / 10
            box(coll, f"st{k}", st, (0.04, 0.012, 0.01), (-0.22 + 0.44 * t, -0.22, 0.03), bevel=0.002)
            box(coll, f"st2{k}", st, (0.04, 0.012, 0.01), (-0.22 + 0.44 * t, 0.22, 0.03), bevel=0.002)
    elif item == "cryo_pad":
        quilted_pad(coll, "cryo", mat("cryo_quilt", (150, 196, 236), (110, 160, 210), 0.0, 0.6, 14, 0.3),
                    mat("cryo_glow", (40, 90, 140), emit=(120, 210, 255), strength=1.4), "frost_strip")
    elif item == "thermal_pad":
        quilted_pad(coll, "thermal", mat("thermal_quilt", (214, 174, 92), (170, 130, 64), 0.4, 0.4, 14, 0.3),
                    mat("thermal_coil", (120, 40, 16), emit=(255, 130, 50), strength=1.4), "coil_strip")
    elif item == "radiation_liner":
        sheet = mat("liner", (96, 98, 104), (70, 72, 78), 0.5, 0.45, 12, 0.2)
        for k in range(3):                                             # folded sheet: stacked layers
            box(coll, f"fold{k}", sheet, (0.52, 0.42, 0.05), (0.02 * k, 0.015 * k, -0.08 + 0.06 * k), bevel=0.02)
        cyl(coll, "badge", mat("rad_yellow", (232, 196, 40)), 0.13, 0.02, (0.04, 0.03, 0.1))
        cyl(coll, "hub", mat("rad_black", (24, 24, 26)), 0.025, 0.025, (0.04, 0.03, 0.11))
        for k in range(3):                                             # trefoil blades
            a = math.pi / 2 + 2 * math.pi * k / 3
            box(coll, f"blade{k}", mat(f"rad_blade{k}", (24, 24, 26)), (0.07, 0.06, 0.012),
                (0.04 + 0.07 * math.cos(a), 0.03 + 0.07 * math.sin(a), 0.115), (0, 0, a), bevel=0.003)
    elif item == "smelter_bar_iron":
        ingot(coll, "ingot", mat("bar_iron", (130, 132, 138), (100, 102, 108), 0.6, 0.35, 12, 0.05))
    elif item == "smelter_bar_copper":
        ingot(coll, "ingot", mat("bar_copper", (214, 120, 70), (180, 96, 56), 0.6, 0.3, 12, 0.05))
    elif item == "circuit_board":
        box(coll, "pcb", mat("pcb", (40, 120, 70), (30, 96, 56), 0.0, 0.5, 20, 0.1), (0.56, 0.42, 0.04), (0, 0, 0), bevel=0.01)
        gold = mat("trace", (220, 180, 80), metallic=1.0, rough=0.3)
        for k in range(5):
            box(coll, f"trace{k}", gold, (0.44, 0.012, 0.006), (0, -0.16 + 0.08 * k, 0.024), bevel=0.0)
        chip = mat("chip", (30, 30, 34), (20, 20, 22), 0.2, 0.4)
        box(coll, "chip0", chip, (0.16, 0.16, 0.04), (-0.08, 0.02, 0.04), bevel=0.01)
        box(coll, "chip1", chip, (0.1, 0.08, 0.035), (0.15, -0.1, 0.04), bevel=0.008)
        ball(coll, "led", mat("pcb_led", (30, 80, 40), emit=(90, 255, 120), strength=1.4), 0.025, (0.18, 0.12, 0.04))


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    rnd = random.Random(13)
    for item in ITEMS:
        coll = bpy.data.collections.new(f"icon_{item}")
        scene.collection.children.link(coll)
        build_item(item, coll, rnd)
    for item in ITEMS2:
        coll = bpy.data.collections.new(f"icon_{item}")
        scene.collection.children.link(coll)
        build_item2(item, coll, rnd)
    lights = bpy.data.collections.new("icon_lights")
    scene.collection.children.link(lights)
    sd = bpy.data.lights.new("key", "SUN")
    sd.energy, sd.angle, sd.color = 3.4, math.radians(4), (1.0, 0.97, 0.92)
    sun = bpy.data.objects.new("key", sd)
    lights.objects.link(sun)
    sun.rotation_euler = Vector((-0.8, 0.35, -0.6)).to_track_quat("-Z", "Y").to_euler()   # from upper right
    world = bpy.data.worlds.new("icon_world")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.6, 0.7, 1.0)
    bg.inputs["Strength"].default_value = 0.45
    scene.world = world
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
