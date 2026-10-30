"""Builds blender/sources/ships/pilgrim.blend: the starter ship Pilgrim (B-006).

An 11.4 m industrial VTOL shuttle: lofted hull, belly lift pods, rear main engine, fixed
landing skids, dorsal fin, cockpit visor. Nose points +X; ground is z = 0; the centre of mass
used as the sprite pivot is (0, 0, 1.8). Worn paint, panel seams (bump), grime toward the
belly and scratched metal are procedural, so the color pass stays unlit albedo and the seams
reach the normal map through the Principled Normal input. Deterministic; re-run any time:

  blender --background --factory-startup --python blender/scripts/build_pilgrim.py
"""
import math
import os
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "ships", "pilgrim.blend")


def lin(c8):
    out = []
    for c in c8:
        c = c / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


# ---------------------------------------------------------------- materials

def _seam(nt, coord_socket, spacing, width=0.018):
    """1.0 on a seam line every `spacing` m along the given scalar, 0 elsewhere."""
    N = nt.nodes
    L = nt.links
    div = N.new("ShaderNodeMath"); div.operation = "DIVIDE"; div.inputs[1].default_value = spacing
    L.new(coord_socket, div.inputs[0])
    fr = N.new("ShaderNodeMath"); fr.operation = "FRACT"
    L.new(div.outputs[0], fr.inputs[0])
    inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    L.new(fr.outputs[0], inv.inputs[1])
    mn = N.new("ShaderNodeMath"); mn.operation = "MINIMUM"
    L.new(fr.outputs[0], mn.inputs[0]); L.new(inv.outputs[0], mn.inputs[1])
    m = N.new("ShaderNodeMath"); m.operation = "MULTIPLY"; m.inputs[1].default_value = spacing
    L.new(mn.outputs[0], m.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs["From Min"].default_value = width * 0.5
    mr.inputs["From Max"].default_value = width
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 0.0
    L.new(m.outputs[0], mr.inputs["Value"])
    return mr.outputs["Result"]


def _mix(nt, fac, a, b):
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
    nt.links.new(fac, mx.inputs["Factor"])
    for sock, val in ((mx.inputs[6], a), (mx.inputs[7], b)):
        if isinstance(val, tuple):
            sock.default_value = val
        else:
            nt.links.new(val, sock)
    return mx.outputs[2]


def _noise(nt, vec, scale, detail=4.0, lo=0.4, hi=0.6):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    nt.links.new(vec, n.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = lo
    mr.inputs["From Max"].default_value = hi
    nt.links.new(n.outputs["Fac"], mr.inputs["Value"])
    return mr.outputs["Result"]


def paint_material(name, paint, dirty, hazard=False, seams=True, grime=True, scratches=True):
    """Worn industrial paint: wear mottling, belly grime, scratches to bare metal, panel seams.
    grime/scratches off for small parts (the grime ramp is in object-space metres)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    pr = N["Principled BSDF"]
    pr.inputs["Roughness"].default_value = 0.55
    tc = N.new("ShaderNodeTexCoord")
    obj = tc.outputs["Object"]
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(obj, sep.inputs[0])

    wear = _noise(nt, obj, 0.7, 6.0, 0.35, 0.75)
    col = _mix(nt, wear, lin(paint), lin(dirty))
    if not grime:
        return _finish_paint(nt, pr, sep, obj, col, hazard, seams, scratches, m)

    # Grime toward the belly (object z below 1.6 m), broken up by noise.
    gz = N.new("ShaderNodeMapRange")
    gz.inputs["From Min"].default_value = 1.7
    gz.inputs["From Max"].default_value = 0.9
    L.new(sep.outputs["Z"], gz.inputs["Value"])
    gn = _noise(nt, obj, 3.0, 8.0, 0.35, 0.7)
    gm = N.new("ShaderNodeMath"); gm.operation = "MULTIPLY"; gm.inputs[2].default_value = 0
    L.new(gz.outputs["Result"], gm.inputs[0]); L.new(gn, gm.inputs[1])
    g7 = N.new("ShaderNodeMath"); g7.operation = "MULTIPLY"; g7.inputs[1].default_value = 0.7
    L.new(gm.outputs[0], g7.inputs[0])
    col = _mix(nt, g7.outputs[0], col, lin((72, 62, 52)))
    return _finish_paint(nt, pr, sep, obj, col, hazard, seams, scratches, m)


def _finish_paint(nt, pr, sep, obj, col, hazard, seams, scratches, m):
    N, L = nt.nodes, nt.links
    if hazard:
        # Yellow/black chevron band around the hull just aft of the cockpit (x 2.45..2.85 m).
        inb_lo = N.new("ShaderNodeMath"); inb_lo.operation = "GREATER_THAN"; inb_lo.inputs[1].default_value = 2.45
        inb_hi = N.new("ShaderNodeMath"); inb_hi.operation = "LESS_THAN"; inb_hi.inputs[1].default_value = 2.85
        L.new(sep.outputs["X"], inb_lo.inputs[0]); L.new(sep.outputs["X"], inb_hi.inputs[0])
        inb = N.new("ShaderNodeMath"); inb.operation = "MULTIPLY"
        L.new(inb_lo.outputs[0], inb.inputs[0]); L.new(inb_hi.outputs[0], inb.inputs[1])
        diag = N.new("ShaderNodeMath"); diag.operation = "ADD"
        L.new(sep.outputs["X"], diag.inputs[0]); L.new(sep.outputs["Z"], diag.inputs[1])
        d2 = N.new("ShaderNodeMath"); d2.operation = "MULTIPLY"; d2.inputs[1].default_value = 3.5
        L.new(diag.outputs[0], d2.inputs[0])
        fr = N.new("ShaderNodeMath"); fr.operation = "FRACT"
        L.new(d2.outputs[0], fr.inputs[0])
        st = N.new("ShaderNodeMath"); st.operation = "GREATER_THAN"; st.inputs[1].default_value = 0.5
        L.new(fr.outputs[0], st.inputs[0])
        stripe = _mix(nt, st.outputs[0], lin((222, 172, 40)), lin((38, 36, 33)))
        col = _mix(nt, inb.outputs[0], col, stripe)

    # Scratches / chipped paint: high-frequency noise exposes bare metal (also metallic).
    if scratches:
        sc = _noise(nt, obj, 14.0, 10.0, 0.66, 0.72)
        col = _mix(nt, sc, col, lin((150, 150, 154)))
        L.new(sc, pr.inputs["Metallic"])

    if seams:
        sx = _seam(nt, sep.outputs["X"], 1.15)
        sz1 = _seam(nt, sep.outputs["Z"], 0.75)
        mx = N.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
        L.new(sx, mx.inputs[0]); L.new(sz1, mx.inputs[1])
        seam = mx.outputs[0]
        dark = N.new("ShaderNodeMath"); dark.operation = "MULTIPLY"; dark.inputs[1].default_value = 0.45
        L.new(seam, dark.inputs[0])
        col = _mix(nt, dark.outputs[0], col, lin((30, 30, 30)))
        neg = N.new("ShaderNodeMath"); neg.operation = "MULTIPLY"; neg.inputs[1].default_value = -1.0
        L.new(seam, neg.inputs[0])
        bump = N.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.6
        bump.inputs["Distance"].default_value = 0.02
        L.new(neg.outputs[0], bump.inputs["Height"])
        L.new(bump.outputs["Normal"], pr.inputs["Normal"])

    L.new(col, pr.inputs["Base Color"])
    return m


def flat_material(name, base, metallic=0.0, emit=None, strength=1.0, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    pr = m.node_tree.nodes["Principled BSDF"]
    pr.inputs["Base Color"].default_value = lin(base)
    pr.inputs["Metallic"].default_value = metallic
    pr.inputs["Roughness"].default_value = rough
    if emit:
        pr.inputs["Emission Color"].default_value = lin(emit)
        pr.inputs["Emission Strength"].default_value = strength
    return m


# ---------------------------------------------------------------- geometry

def new_obj(name, mesh, coll, mat):
    ob = bpy.data.objects.new(name, mesh)
    coll.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def loft(name, sections, coll, mat, ring=40, n=4.0):
    """Hull from (x, half_width, z_bottom, z_top) sections; superellipse rings, capped."""
    bm = bmesh.new()
    rings = []
    for x, hw, zb, zt in sections:
        zc, hh = (zb + zt) / 2, (zt - zb) / 2
        verts = []
        for i in range(ring):
            t = 2 * math.pi * i / ring
            c, s = math.cos(t), math.sin(t)
            y = hw * math.copysign(abs(c) ** (2 / n), c)
            z = zc + hh * math.copysign(abs(s) ** (2 / n), s)
            verts.append(bm.verts.new((x, y, z)))
        rings.append(verts)
    for a, b in zip(rings, rings[1:]):
        for i in range(ring):
            j = (i + 1) % ring
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = new_obj(name, me, coll, mat)
    mod = ob.modifiers.new("subd", "SUBSURF")
    mod.levels = mod.render_levels = 1
    return ob


def prism(name, pts_xz, y0, y1, coll, mat):
    """Flat plate: polygon in XZ extruded from y0 to y1."""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in pts_xz]
    b = [bm.verts.new((x, y1, z)) for x, z in pts_xz]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    k = len(pts_xz)
    for i in range(k):
        j = (i + 1) % k
        bm.faces.new((a[i], b[i], b[j], a[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return new_obj(name, me, coll, mat)


def box(name, center, size, coll, mat, bevel=0.03, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=center, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        mod = ob.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    _move(ob, coll, mat)
    return ob


def cyl(name, center, radius, depth, coll, mat, rot=(0, 0, 0), verts=32, r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=center, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=radius, radius2=r2, depth=depth,
                                        location=center, rotation=rot, end_fill_type="NOTHING")
    ob = bpy.context.active_object
    ob.name = name
    bpy.ops.object.shade_smooth()
    _move(ob, coll, mat)
    return ob


def sphere(name, center, radius, coll, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=radius, location=center)
    ob = bpy.context.active_object
    ob.name = name
    bpy.ops.object.shade_smooth()
    _move(ob, coll, mat)
    return ob


def _move(ob, coll, mat):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    ob.data.materials.append(mat)


# ---------------------------------------------------------------- ship

HULL = [  # x, half width, z bottom, z top  (nose +X)
    (-5.30, 0.95, 1.25, 2.35),
    (-4.70, 1.35, 1.00, 2.70),
    (-3.80, 1.50, 0.92, 2.85),
    (-1.00, 1.52, 0.90, 2.88),
    (1.80, 1.48, 0.90, 2.84),
    (3.10, 1.32, 0.94, 2.62),
    (4.10, 1.02, 1.05, 2.18),
    (4.90, 0.66, 1.20, 1.82),
    (5.45, 0.28, 1.36, 1.58),
]


def hull_half_width(x):
    for (x0, w0, *_), (x1, w1, *_) in zip(HULL, HULL[1:]):
        if x0 <= x <= x1:
            return w0 + (w1 - w0) * (x - x0) / (x1 - x0)
    return HULL[0][1]


def build(out_path=DEFAULT_OUT):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    coll = bpy.data.collections.new("pilgrim")
    scene.collection.children.link(coll)

    paint = paint_material("pilgrim_paint", (196, 194, 184), (150, 146, 136), hazard=True)
    pods = paint_material("pilgrim_pods", (118, 120, 122), (88, 88, 86))
    metal = flat_material("pilgrim_metal", (74, 76, 82), metallic=1.0, rough=0.4)
    dark = flat_material("pilgrim_dark", (46, 47, 50), metallic=0.6, rough=0.6)
    glass = flat_material("pilgrim_glass", (22, 30, 40), emit=(110, 180, 255), strength=0.35, rough=0.1)
    port = flat_material("pilgrim_porthole", (30, 30, 30), emit=(255, 196, 120), strength=0.8)
    engine = flat_material("pilgrim_engine_glow", (60, 58, 56), emit=(255, 140, 50), strength=1.0)
    red = flat_material("pilgrim_nav_red", (120, 20, 15), emit=(255, 40, 30), strength=1.0)
    green = flat_material("pilgrim_nav_green", (15, 100, 30), emit=(40, 255, 90), strength=1.0)
    white = flat_material("pilgrim_strobe", (200, 200, 200), emit=(255, 255, 255), strength=1.0)

    loft("hull", HULL, coll, paint)

    # Cockpit visor on the upper nose slope, and side windows.
    slope = math.atan2(2.62 - 2.18, 4.10 - 3.10)
    box("visor", (3.62, 0, 2.43), (1.05, 1.9, 0.07), coll, glass, bevel=0.02, rot=(0, slope, 0))
    for sy in (-1, 1):
        x = 3.75
        box(f"side_window_{sy}", (x, sy * (hull_half_width(x) - 0.03), 1.95), (0.55, 0.06, 0.32), coll, glass, bevel=0.015)

    # Portholes along the cabin.
    for i, x in enumerate((-2.6, -1.7, -0.8)):
        for sy in (-1, 1):
            cyl(f"porthole_{i}_{sy}", (x, sy * 1.50, 2.05), 0.15, 0.08, coll, port, rot=(math.pi / 2, 0, 0), verts=24)

    # Cargo hatch frame and dorsal radiators.
    for sy in (-1, 1):
        box(f"hatch_{sy}", (0.9, sy * 1.51, 1.62), (1.3, 0.04, 1.0), coll, dark, bevel=0.02)
        box(f"radiator_{sy}", (-2.2, sy * 0.75, 2.90), (2.6, 0.7, 0.06), coll, dark, bevel=0.01)

    # Dorsal fin with a strobe.
    prism("fin", [(-5.15, 2.50), (-3.55, 2.80), (-4.35, 3.45), (-5.05, 3.45)], -0.06, 0.06, coll, paint)
    sphere("strobe", (-4.70, 0, 3.50), 0.06, coll, white)
    cyl("antenna", (1.2, 0.4, 3.12), 0.025, 0.55, coll, metal, verts=8)

    # Main engine: bell, throat glow, lip ring.
    cyl("engine_mount", (-5.35, 0, 1.80), 0.62, 0.30, coll, dark, rot=(0, math.pi / 2, 0))
    cyl("engine_bell", (-5.62, 0, 1.80), 0.42, 0.42, coll, metal, rot=(0, -math.pi / 2, 0), r2=0.62)
    cyl("engine_throat", (-5.50, 0, 1.80), 0.40, 0.04, coll, engine, rot=(0, math.pi / 2, 0))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.61, minor_radius=0.035, location=(-5.83, 0, 1.80),
                                     rotation=(0, math.pi / 2, 0), major_segments=48, minor_segments=8)
    lip = bpy.context.active_object
    lip.name = "engine_lip"
    _move(lip, coll, engine)

    # Belly lift pods with glowing side vents and an emitter plate underneath.
    for name, x in (("aft", -3.0), ("fore", 2.3)):
        box(f"pod_{name}", (x, 0, 0.74), (1.5, 2.2, 0.42), coll, pods, bevel=0.06)
        box(f"pod_{name}_emitter", (x, 0, 0.52), (1.2, 1.8, 0.04), coll, engine, bevel=0.01)
        for k in range(4):
            for sy in (-1, 1):
                box(f"pod_{name}_vent_{k}_{sy}", (x - 0.45 + k * 0.3, sy * 1.105, 0.74), (0.16, 0.02, 0.18), coll, engine, bevel=0)

    # Fixed landing skids: rails and struts.
    for sy in (-1, 1):
        cyl(f"skid_{sy}", (-0.3, sy * 1.30, 0.09), 0.08, 7.4, coll, metal, rot=(0, math.pi / 2, 0), verts=16)
        for x in (-4.0, -2.0, 1.4, 3.0):
            cyl(f"strut_{x}_{sy}", (x, sy * 1.18, 0.5), 0.06, 0.85, coll, metal, rot=(sy * 0.28, 0, 0), verts=12)
        sphere(f"skid_cap_{sy}", (3.4, sy * 1.30, 0.09), 0.08, coll, metal)

    # Nav lights: red port (+Y), green starboard (-Y) on the hull shoulders; nose and tail whites.
    sphere("nav_port", (0.2, 1.53, 2.55), 0.06, coll, red)
    sphere("nav_starboard", (0.2, -1.53, 2.55), 0.06, coll, green)
    sphere("nav_nose", (5.47, 0, 1.47), 0.05, coll, white)

    # Render sets (D-025): `pilgrim` keeps everything (top view, unchanged); `pilgrim_deployed`
    # = everything (side_legs); `pilgrim_retracted` = everything but the landing gear, which
    # folds into the pods in flight (side). Objects are linked, not copied.
    gear = {o for o in coll.objects if o.name.startswith(("skid_", "strut_"))}
    for name, members in (("pilgrim_deployed", list(coll.objects)),
                          ("pilgrim_retracted", [o for o in coll.objects if o not in gear])):
        c = bpy.data.collections.new(name)
        scene.collection.children.link(c)
        for o in members:
            c.objects.link(o)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=True)
    print("MERIDIAN built", out_path)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(args[0] if args else DEFAULT_OUT)
