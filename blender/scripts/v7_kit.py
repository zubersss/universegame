"""B-261 (art v7, D-205): THE KIT AND THE TOOLS AS 3D. Runs INSIDE Blender (bpy), through tools/blender_scene.ps1:
    ... --python v7_kit.py -- kit [shovel beam pack crate smelter]
WRITTEN 11-10 15:1x AS SOURCE, UNRUN (UNITY's want and the RAM gate). Its sheet is build_v7_kit_sheet.py's (to write).

Original designs, MODELLED BY SCRIPT from the measures the game already uses (no downloaded prop):
  shovel   build_surveyor_v6.Fig.tool (B-226's shovel): metres from the NEAR hand, +x toward the blade: the haft -0.42 .. 0.62,
           a brass D-grip behind -0.42, a brass collar at 0.60, a pointed steel blade 0.60 .. 0.93 (0.26 wide). The far hand
           holds it at x = -0.40; the tip is at 0.93 (1.33 m from the far hand). B-250's dig tables stand.
  beam     build_rig_tools_v3.beam_tool(1) (D-087: a MINING tool, never a gun: no grip, no trigger, NOTHING under the body):
           metres from the hand, +x the aim: an arm cuff round the origin, the emitter's body 0 .. 0.36 (radius 0.055), one
           cooling ring, a glow ring, a cutting nozzle to 0.47 (the muzzle: 0.47, 0.03), the cable leaving the back and
           rising toward the pack.
  pack     the red float pack (0.30 deep x 0.34 wide x 0.39 tall, a darker lower band, two belts), the whip antenna with its
           brass plumb bob at the back top corner, and the STOWED-TOOL MOUNT (two brass keepers on the back face).
  crate    the camp's crate: 1.15 x 0.80 x 0.80 m of planks, corner battens, a red band, a pale label plate.
  smelter  the camp's smelter: a squat pot on three legs, brass hoops, a hopper, a chimney with a cap, an arched fire door.
Painted materials (LEAD 13:3x: the paint is IN the materials): each material's colour is a small painted map (one colour
laid as strokes, a value up and a value down), box-projected in the object's own space, so the brushwork sits on the form
and holds still; matt. Each piece is rendered ALONE on alpha at 384 px per metre under the frame's light and finished by
v7_frame_pieces.finish (fewer values, the filter, the brush, a brushed edge). Nothing goes to Assets.
The json of each carries its points in metres from the pivot (grip, far grip, tip, muzzle, cable socket, the mount).
"""
import json
import math
import os
import sys
import time

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import v7_paint_pass as V  # noqa: E402
import v7_frame_pieces as FP  # noqa: E402

KDIR = os.path.join(V.REPO, "blender", "preview", "b261")
say = V.say
# the frame's palette for made things (sRGB): a few paints, each laid as strokes
PAINT = {"steel": (0.62, 0.66, 0.68), "brass": (0.80, 0.62, 0.24), "wood": (0.52, 0.36, 0.20), "haft": (0.62, 0.45, 0.26),
         "red": (0.72, 0.20, 0.14), "red_dark": (0.50, 0.14, 0.11), "belt": (0.30, 0.22, 0.15), "teal": (0.16, 0.52, 0.52),
         "teal_dark": (0.10, 0.36, 0.38), "leather": (0.42, 0.27, 0.16), "pale": (0.86, 0.82, 0.70), "iron": (0.34, 0.31, 0.30),
         "glow": (1.0, 0.62, 0.18), "cable": (0.22, 0.18, 0.16), "plank": (0.60, 0.44, 0.26)}
FP.POST["kit"] = dict(steps=4, amount=0.75, kuw=1.0, brush="leaf", size=(2.0, 4.5), density=1.0, accents=0.5, acc=(1.6, 3.6), edge="leaf")
_MATS = {}


def swatch(name, seed):
    """One paint laid as strokes on a 512 x 512 map (a value up and a value down among them). -> the file's path."""
    import numpy as np
    import paint_v6 as PT
    import painted_v6 as PV
    import v7_paint as VP
    path = os.path.join(KDIR, "tex", name + ".png")
    if os.path.isfile(path):
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    n = 512
    col = np.asarray(PAINT[name], np.float32)
    P = PT.Painting(n, n, seed, 1)
    P.img[:] = col
    one = np.ones((n, n), np.float32)
    for under, cnt, size in ((col, 900, (16.0, 40.0)), (np.clip(col * 1.14, 0, 1), 260, (12.0, 30.0)), (col * 0.84, 260, (12.0, 30.0)), (col, 500, (8.0, 18.0))):
        PV.brush(P, VP.bank(), under, one, cnt, size, angle=0.0, spread=0.35, alpha=(0.6, 0.95), jitter=0.05, hue=0.012, kind="leaf")
    V.write_png(path, np.concatenate([np.clip(P.img, 0, 1), np.ones((n, n, 1), np.float32)], axis=2))
    return path


def mat(name, emit=0.0):
    """A matt painted material: the swatch box-projected in object space (2 tiles a metre), a little relief from it."""
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new("kit_" + name)
    m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tex, tc, mp, bump = nt.nodes.new("ShaderNodeTexImage"), nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeMapping"), nt.nodes.new("ShaderNodeBump")
    tex.image = bpy.data.images.load(swatch(name, 3 + len(_MATS)), check_existing=True)
    tex.projection, tex.projection_blend = "BOX", 0.25
    mp.inputs["Scale"].default_value = (2.0, 2.0, 2.0)
    bump.inputs["Strength"].default_value = 0.12
    L = nt.links.new
    L(tc.outputs["Object"], mp.inputs["Vector"])
    L(mp.outputs["Vector"], tex.inputs["Vector"])
    L(tex.outputs["Color"], bs.inputs["Base Color"])
    L(tex.outputs["Color"], bump.inputs["Height"])
    L(bump.outputs["Normal"], bs.inputs["Normal"])
    if emit:
        for key in ("Emission Color", "Emission"):
            if bs.inputs.get(key) is not None:
                bs.inputs[key].default_value = PAINT[name] + (1.0,)
                break
        if bs.inputs.get("Emission Strength") is not None:
            bs.inputs["Emission Strength"].default_value = emit
    FP.matt([m])
    _MATS[name] = m
    return m


def obj(scene, name, bm, paint, smooth=True, emit=0.0):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = len(p.vertices) == 4
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(mat(paint, emit))
    scene.collection.objects.link(ob)
    return ob


def lathe(scene, name, prof, paint, axis="X", seg=28, at=(0.0, 0.0, 0.0), emit=0.0):
    """A solid of revolution: prof = [(t along the axis, radius)], capped at both ends."""
    bm = bmesh.new()
    rings = []
    for t, r in prof:
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            co = (t, r * math.cos(a), r * math.sin(a)) if axis == "X" else (r * math.cos(a), r * math.sin(a), t)
            ring.append(bm.verts.new(Vector(co) + Vector(at)))
        rings.append(ring)
    for a_, b_ in zip(rings, rings[1:]):
        for i in range(seg):
            bm.faces.new((a_[i], a_[(i + 1) % seg], b_[(i + 1) % seg], b_[i]))
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1])
    return obj(scene, name, bm, paint, emit=emit)


def tube(scene, name, pts, r, paint, seg=12):
    """A round tube along a path in the x-z plane (a cable, a strap's edge)."""
    bm = bmesh.new()
    rings = []
    for i, p in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        t = (Vector((b[0] - a[0], 0.0, b[1] - a[1]))).normalized()
        n = Vector((-t.z, 0.0, t.x))
        ring = [bm.verts.new(Vector((p[0], 0.0, p[1])) + r * (math.cos(2 * math.pi * k / seg) * n + math.sin(2 * math.pi * k / seg) * Vector((0, 1, 0)))) for k in range(seg)]
        rings.append(ring)
    for a_, b_ in zip(rings, rings[1:]):
        for i in range(seg):
            bm.faces.new((a_[i], a_[(i + 1) % seg], b_[(i + 1) % seg], b_[i]))
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1])
    return obj(scene, name, bm, paint)


def box(scene, name, lo, hi, paint, bevel=0.0, emit=0.0):
    """A box from corner lo to corner hi (x, y, z), its edges eased by `bevel` metres."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    lo, hi = Vector(lo), Vector(hi)
    M = Matrix.Translation((lo + hi) / 2) @ Matrix.Diagonal(Vector((hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, 1.0)))
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts[:])
    if bevel:
        try:
            bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, profile=0.5, affect="EDGES")
        except Exception as e:                                                             # noqa: BLE001  a plain box is still a box
            say(f"  bevel refused on {name}: {e!r}")
    return obj(scene, name, bm, paint, smooth=False, emit=emit)


def plate(scene, name, outline, paint, thick=0.006, dish=0.0, rib=0.0, nx=18, nz=9):
    """A plate in the x-z plane from its outline's HALF-WIDTH profile [(x, half width)], dished across its width and with
    a raised rib along its middle (a spade's blade)."""
    bm = bmesh.new()
    xs = [outline[0][0] + (outline[-1][0] - outline[0][0]) * i / (nx - 1) for i in range(nx)]

    def half(x):
        for (x0, w0), (x1, w1) in zip(outline, outline[1:]):
            if x0 <= x <= x1:
                return w0 + (w1 - w0) * (x - x0) / max(x1 - x0, 1e-6)
        return outline[-1][1]
    wmax = max(w for _, w in outline)
    layers = []
    for side in (1.0, -1.0):
        grid = []
        for x in xs:
            hw = max(half(x), 0.002)
            row = []
            for j in range(nz):
                u = -1.0 + 2.0 * j / (nz - 1)
                z = u * hw
                y = -dish * (z / wmax) ** 2 + rib * max(0.0, 1 - abs(u) * 4.0) - side * thick / 2
                row.append(bm.verts.new((x, y, z)))
            grid.append(row)
        layers.append(grid)
        for i in range(nx - 1):
            for j in range(nz - 1):
                bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    a, b = layers
    for i in range(nx - 1):                                                                # the two long edges
        for j in (0, nz - 1):
            bm.faces.new((a[i][j], a[i + 1][j], b[i + 1][j], b[i][j]))
    for j in range(nz - 1):                                                                # the two ends
        for i in (0, nx - 1):
            bm.faces.new((a[i][j], a[i][j + 1], b[i][j + 1], b[i][j]))
    return obj(scene, name, bm, paint)


# ---------------------------------------------------------------- the pieces (metres; x right, z up, the viewer at -y)
def shovel(scene):
    lathe(scene, "haft", [(-0.42, 0.018), (0.20, 0.018), (0.60, 0.016)], "haft")
    lathe(scene, "collar", [(0.56, 0.022), (0.64, 0.022)], "brass")
    for z in (-0.055, 0.055):                                                               # the D-grip: two cheeks and a cross bar
        lathe(scene, "grip_cheek", [(-0.50, 0.012), (-0.42, 0.014)], "brass", at=(0.0, 0.0, z))
    box(scene, "grip_bar", (-0.515, -0.014, -0.07), (-0.49, 0.014, 0.07), "brass", bevel=0.005)
    box(scene, "grip_yoke", (-0.43, -0.016, -0.07), (-0.41, 0.016, 0.07), "brass", bevel=0.004)
    plate(scene, "blade", [(0.60, 0.115), (0.66, 0.13), (0.75, 0.125), (0.85, 0.09), (0.93, 0.004)], "steel", dish=0.035, rib=0.008)
    return {"pivot": "the near hand on the haft", "grip_m": [0.0, 0.0], "far_grip_m": [-0.40, 0.0], "tip_m": [0.93, 0.0], "length_m": 1.445}


def beam(scene):
    r, x1 = 0.055, 0.36
    lathe(scene, "body", [(0.0, r), (x1, r * 0.9)], "teal")
    lathe(scene, "back_plug", [(-0.035, 0.035), (0.005, 0.035)], "iron")
    lathe(scene, "cooling_ring", [(x1 - 0.062, r + 0.010), (x1 - 0.038, r + 0.010)], "steel")
    lathe(scene, "glow_ring", [(x1 - 0.02, r * 0.82), (x1 + 0.01, r * 0.82)], "glow", emit=1.5)
    lathe(scene, "nozzle", [(x1 + 0.01, r * 0.75), (0.45, 0.025), (0.47, 0.020)], "brass")
    lathe(scene, "cuff", [(-0.06, r + 0.035), (0.06, r + 0.035)], "leather")
    for x in (-0.025, 0.025):
        lathe(scene, "cuff_strap", [(x - 0.008, r + 0.040), (x + 0.008, r + 0.040)], "brass")
    cable = [(-0.03, 0.0), (-0.09, 0.03), (-0.14, 0.08), (-0.17, 0.14)]                        # back and UP toward the pack: nothing hangs under the body
    tube(scene, "cable", cable, 0.015, "cable")
    return {"pivot": "the hand", "muzzle_m": [0.47, 0.03], "cable_socket_m": list(cable[-1]), "length_m": 0.47,
            "rule": "D-087: a mining tool, never a gun: no grip, no trigger, nothing under the body"}


def pack(scene):
    box(scene, "pack", (-0.15, -0.17, -0.19), (0.15, 0.17, 0.20), "red", bevel=0.03)
    box(scene, "pack_lower", (-0.156, -0.176, -0.20), (0.156, 0.176, -0.07), "red_dark", bevel=0.02)
    for z in (0.10, -0.10):
        box(scene, "belt", (-0.158, -0.178, z - 0.018), (0.158, 0.178, z + 0.018), "belt", bevel=0.004)
    top = (-0.11, 0.20)                                                                     # the back top corner (the back is -x)
    lathe(scene, "antenna", [(0.0, 0.004), (0.15, 0.003)], "iron", axis="Z", seg=8, at=(top[0], 0.0, top[1]))
    lathe(scene, "bob", [(0.0, 0.002), (0.045, 0.028), (0.062, 0.0015)], "brass", axis="Z", seg=16, at=(top[0], 0.0, top[1] + 0.15))
    mount = []
    for z in (0.12, -0.12):                                                                 # the stowed-tool mount: two brass keepers on the back face
        box(scene, "keeper", (-0.185, -0.03, z - 0.02), (-0.15, 0.03, z + 0.02), "brass", bevel=0.006)
        mount.append([-0.17, z])
    return {"pivot": "the pack's middle", "antenna_root_m": list(top), "antenna_tip_m": [top[0], top[1] + 0.21], "stow_mount_m": mount,
            "size_m": [0.30, 0.34, 0.39]}


def crate(scene):
    w, d, h = 1.15, 0.80, 0.80
    box(scene, "crate", (-w / 2, -d / 2, 0.0), (w / 2, d / 2, h), "plank", bevel=0.012)
    for x in (-w / 2, w / 2 - 0.07):                                                        # corner battens, proud of the planks
        for y in (-d / 2 - 0.012, d / 2 - 0.010):
            box(scene, "batten", (x, y, 0.0), (x + 0.07, y + 0.022, h), "wood", bevel=0.004)
    for z in (0.0, h - 0.07):
        box(scene, "rail", (-w / 2, -d / 2 - 0.012, z), (w / 2, -d / 2 + 0.010, z + 0.07), "wood", bevel=0.004)
    box(scene, "band", (-w / 2 - 0.006, -d / 2 - 0.016, 0.30), (w / 2 + 0.006, d / 2 + 0.006, 0.50), "red", bevel=0.004)
    box(scene, "label", (-0.12, -d / 2 - 0.022, 0.345), (0.12, -d / 2 - 0.014, 0.455), "pale", bevel=0.003)
    return {"pivot": "the middle of its base", "size_m": [w, d, h]}


def smelter(scene):
    lathe(scene, "pot", [(0.42, 0.30), (0.50, 0.52), (0.70, 0.70), (0.95, 0.74), (1.20, 0.66), (1.36, 0.46), (1.42, 0.22)], "wood", axis="Z", seg=36)
    for z, r in ((0.62, 0.665), (1.24, 0.640)):
        lathe(scene, "hoop", [(z - 0.03, r), (z + 0.03, r)], "brass", axis="Z", seg=36)
    for k in range(3):                                                                      # three legs, splayed
        a = math.radians(90 + 120 * k + 25)
        lathe(scene, "leg", [(0.0, 0.045), (0.55, 0.06)], "brass", axis="Z", seg=12, at=(0.50 * math.cos(a), 0.50 * math.sin(a), 0.0))
    lathe(scene, "hopper_neck", [(1.36, 0.10), (1.56, 0.10)], "brass", axis="Z", seg=16, at=(-0.40, 0.0, 0.0))
    lathe(scene, "hopper", [(1.56, 0.10), (1.82, 0.26), (1.86, 0.26)], "brass", axis="Z", seg=20, at=(-0.40, 0.0, 0.0))
    lathe(scene, "chimney", [(1.36, 0.075), (2.05, 0.075)], "teal", axis="Z", seg=16, at=(0.34, 0.0, 0.0))
    lathe(scene, "chimney_cap", [(2.05, 0.11), (2.12, 0.11)], "iron", axis="Z", seg=16, at=(0.34, 0.0, 0.0))
    # the fire door: an arched plate on the front, the fire a SQUARE-shouldered opening in it (one round glowing window on a
    # rounded body is on the face-catch list: no round window, no dial)
    box(scene, "door", (-0.20, -0.775, 0.66), (0.20, -0.70, 1.08), "iron", bevel=0.03)
    box(scene, "fire", (-0.12, -0.785, 0.72), (0.12, -0.77, 0.98), "glow", bevel=0.012, emit=2.5)
    return {"pivot": "the middle of its footprint", "size_m": [1.5, 1.5, 2.12]}


KIT = {"shovel": shovel, "beam": beam, "pack": pack, "crate": crate, "smelter": smelter}


def kit(ids):
    os.makedirs(KDIR, exist_ok=True)
    FP.PDIR = KDIR                                                                          # finish() writes beside the kit's own files
    for kid in ids or list(KIT):
        t0 = time.time()
        scene = V.fresh()
        _MATS.clear()
        points = KIT[kid](scene)
        bpy.context.view_layer.update()
        obs = [o for o in scene.objects if o.type == "MESH"]
        FP.painters_light(scene)
        V.render_setup(scene)
        lo, hi = V.bounds(obs)
        w, h, pivot = FP.camera(scene, lo, hi, 384)
        rp = os.path.join(KDIR, kid + "_render.png")
        scene.render.filepath = rp
        t1 = time.time()
        bpy.ops.render.render(write_still=True, scene=scene.name)
        t_r = time.time() - t1
        meta = {"id": kid, "style": "v7", "kind": "kit", "px_per_m": 384, "size_px": [w, h], "pivot": pivot, "width_m": round(hi.x - lo.x, 3),
                "height_m": round(hi.z - lo.z, 3), "tris": FP.tris(obs), "render_s": round(t_r, 1), "points": points}
        meta.update(FP.finish(kid, "kit", 384, rp))
        os.remove(rp)
        with open(os.path.join(KDIR, kid + ".json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(meta, fh, indent=1)
        say(f"{kid}: {meta['width_m']} x {meta['height_m']} m, {w}x{h} px, {meta['tris']} triangles; render {t_r:.1f} s; the brush {meta['strokes']} strokes "
            f"in {meta['paint_s']} s; {time.time() - t0:.1f} s in all -> blender/preview/b261/{kid}.png")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if argv and argv[0] == "kit":
        bad = [a for a in argv[1:] if a not in KIT]
        if bad:
            raise SystemExit(f"v7_kit: no piece {bad} (have: {', '.join(KIT)})")
        kit(argv[1:])
    else:
        raise SystemExit("v7_kit: kit [" + " ".join(KIT) + "]")
