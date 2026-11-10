"""B-258 part 2 (art v7, D-205): THE FIGURE. Runs INSIDE Blender (bpy), through tools/blender_scene.ps1.
WRITTEN 11-10 17:1x AS SOURCE, UNRUN. DATA ONLY (LEAD): the body is one of Blender Studio's CC0 Human Base Meshes
(a .blend from blender.org, fetched by tools/blender_fetch_cc0.ps1 -BundleName human_base_meshes ...; opened with
--disable-autoexec and only APPENDED from: no script in it runs); the suit, boots, belt, pack and antenna are made here
by script; the skeleton is plain bones made here (Rigify is allowed per run by LEAD's ruling, and not needed for this).

  ... -- inspect                  what the bundle holds: every .blend under blender/vendor_cc0/human_base_meshes/, every
                                  object in it (type, size, vertices, modifiers, parent). To CHOOSE the body. No render.
  ... -- probe <object> [pose]    THE PROBE FRAME (LEAD: one frame sets part 2's gate): the named body, set to 1.84 m and
                                  turned to face +x; landmarks found on it; bones laid on them; skinned; dressed; posed
                                  from B-250's pose maths (v7_pose: idle by default, or walk); rendered alone at 384 px per
                                  metre under the frame's light -> blender/preview/b258/figure/probe_<pose>.png + .json.

HOW A POSE GETS ON THE RIG (the bone map): v7_pose.bones(pose) gives every bone's head and tail from B-250's 2D skeleton
(the tables that STAND). Each rig bone is AIMED along its segment's direction, parent first; the rig keeps its own bone
lengths (the body's real proportions), so angles carry over exactly and the sockets (wrists, the tool's grip) are read
back from the posed rig and written to the json, to be compared with the 2D table's.
THE PAINT HOLDS STILL: every material's painted map is projected from the mesh's REST positions (the rest_position
attribute), not from where the surface is in a pose, so a stroke stays on its fold of cloth from drawing to drawing.
A figure gets NO strokes laid in the picture and no brushed edge (they would crawl): finish() only gathers the values
and softens the edge with the filter (LEAD 13:3x).
FOLLOW-THROUGH (the antenna, strap ends): follow_through() below: a damped spring per bone driven by its root's motion
through the clip, run twice round a looping clip so the loop closes; baked as plain keys. Not used by a single frame.
THE EXPORT (D-208, contract 12.9): frames rendered in the frame BOX's own camera, laid in boxes, then pack_cuts.pack()
trims them and writes "cuts"; the normal sheet goes through pack_cuts.pack_with() with the same cuts.
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
import v7_kit as KIT  # noqa: E402
import v7_pose as POSE  # noqa: E402

BUNDLE = os.path.join(V.VENDOR, "human_base_meshes")
FDIR = os.path.join(V.REPO, "blender", "preview", "b258", "figure")
HEIGHT = 1.84
say = V.say
KIT.PAINT.update({"suit": (0.86, 0.82, 0.72), "suit_dark": (0.66, 0.62, 0.54), "skin": (0.84, 0.64, 0.52), "hair": (0.62, 0.47, 0.25),
                  "boot": (0.40, 0.26, 0.16), "glove": (0.34, 0.24, 0.17)})
FP.POST["figure"] = dict(steps=4, amount=0.6, kuw=0.75, brush="leaf", size=(2.0, 4.0), density=0.0, accents=0.0, acc=(1.5, 3.0), edge=None)
# the bones: name -> (parent, joined to the parent's tail)
RIG = [("spine_lo", None, False), ("spine_mid", "spine_lo", True), ("spine_hi", "spine_mid", True), ("neck", "spine_hi", True), ("head", "neck", True)] + \
      [(b + s, p if p.startswith("spine") else p + s, c) for s in ("_n", "_f") for b, p, c in
       (("thigh", "spine_lo", False), ("shin", "thigh", True), ("foot", "shin", True), ("upper_arm", "spine_hi", False), ("forearm", "upper_arm", True), ("hand", "forearm", True))]


def blends():
    out = []
    for root, _, files in os.walk(BUNDLE):
        out += [os.path.join(root, f) for f in files if f.lower().endswith(".blend")]
    return sorted(out)


def inspect():
    files = blends()
    if not files:
        say(f"NO .blend under blender/vendor_cc0/human_base_meshes/ (fetch it first: tools/blender_fetch_cc0.ps1 -BundleName human_base_meshes -BundleUrl <the zip on blender.org>)")
        return
    for path in files:
        scene = V.fresh()
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            names = list(src.objects)
            say(f"{os.path.relpath(path, V.REPO)}: {len(names)} objects, {len(src.collections)} collections, {len(src.armatures)} armatures, {len(src.materials)} materials")
            dst.objects = names
        for ob in dst.objects:
            if ob is None:
                continue
            scene.collection.objects.link(ob)
        bpy.context.view_layer.update()
        for ob in sorted((o for o in dst.objects if o is not None), key=lambda o: o.name):
            if ob.type == "MESH":
                d = ob.dimensions
                say(f"  MESH '{ob.name}': {d.x:.2f} x {d.y:.2f} x {d.z:.2f} m, {len(ob.data.vertices)} verts, {sum(len(p.vertices) - 2 for p in ob.data.polygons)} tris; "
                    f"modifiers {[m.type for m in ob.modifiers]}; parent {ob.parent.name if ob.parent else None}; vertex groups {len(ob.vertex_groups)}; "
                    f"materials {[s.material.name for s in ob.material_slots if s.material]}")
            else:
                say(f"  {ob.type} '{ob.name}'")


def verts(ob, evaluated=False):
    import numpy as np
    if evaluated:
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
    else:
        me = ob.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    mw = np.array(ob.matrix_world, np.float32)
    co = co @ mw[:3, :3].T + mw[:3, 3]
    if evaluated:
        ev.to_mesh_clear()
    return co


def take_body(scene, name):
    """The named object appended from the bundle, set to 1.84 m, its feet on z = 0 over the origin, FACING +x (the base
    meshes face -y: a quarter turn about z). Its mesh is transformed, the object left at the identity."""
    for path in blends():
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            if name in src.objects:
                dst.objects = [name]
        if dst.objects and dst.objects[0] is not None:
            body = dst.objects[0]
            break
    else:
        raise SystemExit(f"v7_figure: no object '{name}' in the bundle (run inspect)")
    scene.collection.objects.link(body)
    for m in list(body.modifiers):
        body.modifiers.remove(m)
    body.parent = None
    bpy.context.view_layer.update()
    body.data.transform(Matrix.Rotation(math.radians(90.0), 4, "Z") @ body.matrix_world)
    body.matrix_world = Matrix.Identity(4)
    co = verts(body)
    s = HEIGHT / float(co[:, 2].max() - co[:, 2].min())
    body.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(Vector((-float(co[:, 0].mean()), -float(co[:, 1].mean()), -float(co[:, 2].min())))))
    body.data.update()
    return body


def landmarks(co):
    """Where the joints are on a standing body that faces +x with its arms held away from it (an A or a T pose):
    name -> (x, y, z). Read from the mesh: slices for the trunk and the legs, a line through each arm's vertices."""
    import numpy as np
    H = HEIGHT

    def mid(z, sel=None, band=0.02):
        m = np.abs(co[:, 2] - z) < band * H
        if sel is not None:
            m &= sel
        return co[m].mean(axis=0) if m.any() else np.array([0.0, 0.0, z], np.float32)
    L = {}
    half = float(np.percentile(np.abs(co[np.abs(co[:, 2] - 0.60 * H) < 0.02 * H][:, 1]), 95))      # the waist's half width
    trunk = np.abs(co[:, 1]) < half * 1.05
    for k, z in (("P", 0.53), ("W", 0.60), ("C", 0.70), ("N", 0.845), ("A", 0.875), ("TOP", 1.0)):
        c = mid(z * H, trunk)
        L[k] = (float(c[0]), 0.0, z * H)
    for s, sg in (("n", -1.0), ("f", 1.0)):
        side = (co[:, 1] * sg > 0.01)
        leg = side & (co[:, 2] < 0.47 * H) & (np.abs(co[:, 1]) < half * 1.4)
        hip, knee, ank = mid(0.44 * H, leg), mid(0.285 * H, leg), mid(0.05 * H, leg)
        L["hip_" + s] = (float(hip[0]), float(hip[1]), 0.50 * H)
        L["knee_" + s] = (float(knee[0]), float(knee[1]), 0.285 * H)
        L["ank_" + s] = (float(ank[0]) - 0.02, float(ank[1]), 0.05 * H)
        foot = side & (co[:, 2] < 0.04 * H)
        L["toe_" + s] = (float(co[foot][:, 0].max()) if foot.any() else L["ank_" + s][0] + 0.2, L["ank_" + s][1], 0.012 * H)
        arm = side & (np.abs(co[:, 1]) > half * 1.25) & (co[:, 2] > 0.30 * H)
        a = co[arm]
        c = a.mean(axis=0)
        _, _, vt = np.linalg.svd(a - c, full_matrices=False)
        d = vt[0] * (1.0 if vt[0][1] * sg > 0 else -1.0)                                         # along the arm, outward
        t = (a - c) @ d
        t0, t1 = float(np.percentile(t, 1)), float(np.percentile(t, 99))
        sh, tip = c + d * t0, c + d * t1
        L["sh_" + s] = tuple(float(v) for v in sh)
        L["elb_" + s] = tuple(float(v) for v in sh + (tip - sh) * 0.43)
        L["wr_" + s] = tuple(float(v) for v in sh + (tip - sh) * 0.80)
        L["tip_" + s] = tuple(float(v) for v in tip)
    return L, half


def build_rig(scene, L):
    arm = bpy.data.armatures.new("v7_rig")
    ob = bpy.data.objects.new("v7_rig", arm)
    scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    ends = {"spine_lo": ("P", "W"), "spine_mid": ("W", "C"), "spine_hi": ("C", "N"), "neck": ("N", "A"), "head": ("A", "TOP")}
    for s in ("n", "f"):
        ends.update({"thigh_" + s: ("hip_" + s, "knee_" + s), "shin_" + s: ("knee_" + s, "ank_" + s), "foot_" + s: ("ank_" + s, "toe_" + s),
                     "upper_arm_" + s: ("sh_" + s, "elb_" + s), "forearm_" + s: ("elb_" + s, "wr_" + s), "hand_" + s: ("wr_" + s, "tip_" + s)})
    for name, parent, joined in RIG:
        eb = arm.edit_bones.new(name)
        eb.head, eb.tail = Vector(L[ends[name][0]]), Vector(L[ends[name][1]])
        if parent:
            eb.parent = arm.edit_bones[parent]
            eb.use_connect = joined
    bpy.ops.object.mode_set(mode="OBJECT")
    return ob


def skin(body, rig):
    """Automatic weights; envelopes if the solver refuses. -> which."""
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    how = "automatic weights"
    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    except Exception as e:                                                                    # noqa: BLE001
        say(f"  automatic weights refused ({e!r}): envelopes")
        how = "envelopes"
        bpy.ops.object.parent_set(type="ARMATURE_ENVELOPE")
    if not any(len(v.groups) for v in body.data.vertices):
        how = "envelopes (the automatic solve left no weights)"
        bpy.ops.object.parent_set(type="ARMATURE_ENVELOPE")
    return how


def rest_mat(name):
    """A painted material whose map is projected from the REST positions (see the module's head)."""
    key = "rest_" + name
    if key in KIT._MATS:
        return KIT._MATS[key]
    m = bpy.data.materials.new("fig_" + name)
    m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tex, at, mp, bump = nt.nodes.new("ShaderNodeTexImage"), nt.nodes.new("ShaderNodeAttribute"), nt.nodes.new("ShaderNodeMapping"), nt.nodes.new("ShaderNodeBump")
    at.attribute_name = "rest_position"
    tex.image = bpy.data.images.load(KIT.swatch(name, 31 + len(KIT._MATS)), check_existing=True)
    tex.projection, tex.projection_blend = "BOX", 0.25
    mp.inputs["Scale"].default_value = (2.0, 2.0, 2.0)
    bump.inputs["Strength"].default_value = 0.10
    L = nt.links.new
    L(at.outputs["Vector"], mp.inputs["Vector"])
    L(mp.outputs["Vector"], tex.inputs["Vector"])
    L(tex.outputs["Color"], bs.inputs["Base Color"])
    L(tex.outputs["Color"], bump.inputs["Height"])
    L(bump.outputs["Normal"], bs.inputs["Normal"])
    FP.matt([m])
    KIT._MATS[key] = m
    return m


def dress(scene, body, rig, L, half):
    """THE FIRST SUIT, by script on the body: the coverall is the body's own surface pushed out a little and painted as
    cloth (everything but the head and the hands); boots are the feet and lower shins pushed out further; gloves the
    hands; hair the skull's top and back; a belt round the waist; the float pack with its antenna on the back."""
    import numpy as np
    co = verts(body)
    H = HEIGHT
    me = body.data
    body.add_rest_position_attribute = True
    for name in ("suit", "skin", "boot", "glove", "hair"):
        me.materials.append(rest_mat(name))
    slot = {"suit": 0, "skin": 1, "boot": 2, "glove": 3, "hair": 4}
    arm_out = np.abs(co[:, 1]) > half * 1.25
    wr_n, wr_f = np.array(L["wr_n"]), np.array(L["wr_f"])
    hand = arm_out & (np.minimum(np.linalg.norm(co - wr_n, axis=1), np.linalg.norm(co - wr_f, axis=1)) < 0.24) & \
        ((co - wr_n) @ (np.array(L["tip_n"]) - wr_n) > 0) | arm_out & ((co - wr_f) @ (np.array(L["tip_f"]) - wr_f) > 0)
    head = (co[:, 2] > 0.865 * H) & ~arm_out
    hair = head & ((co[:, 2] > 0.955 * H) | ((co[:, 2] > 0.905 * H) & (co[:, 0] < L["A"][0] - 0.01)))
    boot = (co[:, 2] < 0.17 * H) & ~arm_out
    region = np.zeros(len(co), np.int32)                                                        # per vertex: the slot
    region[head] = slot["skin"]
    region[hair] = slot["hair"]
    region[boot] = slot["boot"]
    region[hand] = slot["glove"]
    push = {"suit": 0.012, "boot": 0.020, "glove": 0.006, "hair": 0.012, "skin": 0.0}
    for nm in push:
        vg = body.vertex_groups.new(name="dress_" + nm)
        idx = [int(i) for i in np.flatnonzero(region == slot[nm])]
        if idx and push[nm] > 0:
            vg.add(idx, 1.0, "REPLACE")
            md = body.modifiers.new("dress_" + nm, "DISPLACE")
            md.vertex_group, md.strength, md.mid_level = vg.name, push[nm], 0.0
    for p in me.polygons:                                                                        # a face takes the slot most of its corners have
        r = [int(region[v]) for v in p.vertices]
        p.material_index = max(set(r), key=r.count)
    # the belt: a band round the waist, read from the body's own section there
    w = co[(np.abs(co[:, 2] - 0.60 * H) < 0.015 * H) & ~arm_out]
    cx, hx, hy = float(w[:, 0].mean()), float(np.ptp(w[:, 0])) / 2 + 0.02, float(np.ptp(w[:, 1])) / 2 + 0.02
    bm = bmesh.new()
    rings = [[bm.verts.new((cx + hx * math.cos(2 * math.pi * i / 32), hy * math.sin(2 * math.pi * i / 32), z)) for i in range(32)] for z in (0.585 * H, 0.615 * H)]
    for i in range(32):
        bm.faces.new((rings[0][i], rings[0][(i + 1) % 32], rings[1][(i + 1) % 32], rings[1][i]))
    belt = KIT.obj(scene, "belt", bm, "belt")
    pieces = [(belt, "spine_lo")]
    # the pack: v7_kit's own, set on the back (the back is -x), its middle at the chest's height
    before = set(scene.objects)
    KIT.pack(scene)
    back = float(co[(np.abs(co[:, 2] - 0.72 * H) < 0.03 * H) & ~arm_out][:, 0].min())
    T = Matrix.Translation(Vector((back - 0.15, 0.0, 0.72 * H)))
    for ob in set(scene.objects) - before:
        ob.matrix_world = T @ ob.matrix_world
        pieces.append((ob, "spine_hi"))
    bpy.context.view_layer.update()
    for ob, bone in pieces:                                                                      # rigid on a bone, kept where it stands
        keep = ob.matrix_world.copy()
        ob.parent, ob.parent_type, ob.parent_bone = rig, "BONE", bone
        ob.matrix_world = keep
    return [ob for ob, _ in pieces]


def pose(rig, p):
    """Every bone aimed along its segment of B-250's skeleton (v7_pose.bones), parent first; the root set at the 2D
    pelvis's height scaled by this rig's leg length; then the whole rig lowered so the lowest point stands on z = 0."""
    target = POSE.bones(p)
    arm = rig.data
    leg_rig = (arm.bones["thigh_n"].length + arm.bones["shin_n"].length)
    k = leg_rig / (POSE.L_TH + POSE.L_SH)
    for name, parent, joined in RIG:
        pb, b = rig.pose.bones[name], arm.bones[name]
        h, t = Vector(target[name][0]), Vector(target[name][1])
        d = (t - h).normalized()
        rest = b.matrix_local.to_3x3()
        q = (rest @ Vector((0.0, 1.0, 0.0))).rotation_difference(d)                               # the shortest turn from rest to the pose
        R = q.to_matrix() @ rest
        if parent is None:
            head = Vector((h.x * k, 0.0, h.z * k))
        else:
            pp, pbone = rig.pose.bones[parent], arm.bones[parent]
            head = pp.matrix @ (pbone.matrix_local.inverted() @ b.head_local)                     # where the parent carries this bone's head
        pb.matrix = Matrix.Translation(head) @ R.to_4x4()
        bpy.context.view_layer.update()


def sockets(rig):
    """The posed rig's own points (metres, x forward, z up), to compare with the 2D table's."""
    out = {}
    for name in ("hand_n", "hand_f", "foot_n", "foot_f", "head"):
        pb = rig.pose.bones[name]
        out[name] = [round(v, 3) for v in (rig.matrix_world @ pb.head)]
    return out


def follow_through(root_xz, fps, stiffness=60.0, damping=7.0, loop=True, sub=4):
    """The lag of something springy on a moving root (an antenna, a strap's end): root_xz = its root's (x, z) per frame.
    -> the bend in radians per frame (+ = swung forward). A damped spring driven by the root's sideways acceleration,
    integrated at `sub` steps a frame; a looping clip is run twice and the second round kept, so the loop closes."""
    n = len(root_xz)
    seq = list(root_xz) * (2 if loop else 1)
    dt = 1.0 / (fps * sub)
    th, om, out = 0.0, 0.0, []
    for i in range(len(seq)):
        a, b, c = seq[i - 1][0], seq[i][0], seq[(i + 1) % len(seq)][0]
        acc = (a - 2 * b + c) * fps * fps                                                        # the root's acceleration along x
        for _ in range(sub):
            om += (-stiffness * th - damping * om - 6.0 * acc) * dt
            th += om * dt
        out.append(th)
    return out[-n:]


def probe(name, which="idle"):
    os.makedirs(FDIR, exist_ok=True)
    FP.PDIR = FDIR
    t0 = time.time()
    scene = V.fresh()
    KIT._MATS.clear()
    body = take_body(scene, name)
    co = verts(body)
    L, half = landmarks(co)
    rig = build_rig(scene, L)
    how = skin(body, rig)
    extra = dress(scene, body, rig, L, half)
    p = dict(POSE.IDLE if which == "idle" else POSE.WALK)
    pose(rig, p)
    bpy.context.view_layer.update()
    ev = verts(body, evaluated=True)
    rig.location.z -= float(ev[:, 2].min())                                                       # the soles on the ground
    bpy.context.view_layer.update()
    ev = verts(body, evaluated=True)
    lo, hi = Vector([float(v) for v in ev.min(axis=0)]), Vector([float(v) for v in ev.max(axis=0)])
    for ob in extra:
        ol, oh = V.bounds([ob])
        lo, hi = Vector((min(lo.x, ol.x), min(lo.y, ol.y), min(lo.z, ol.z))), Vector((max(hi.x, oh.x), max(hi.y, oh.y), max(hi.z, oh.z)))
    FP.painters_light(scene)
    V.render_setup(scene)
    w, h, pivot = FP.camera(scene, lo, hi, 384)
    rp = os.path.join(FDIR, f"probe_{which}_render.png")
    scene.render.filepath = rp
    t1 = time.time()
    bpy.ops.render.render(write_still=True, scene=scene.name)
    t_r = time.time() - t1
    meta = {"id": f"probe_{which}", "style": "v7", "kind": "figure", "body": name, "skin": how, "px_per_m": 384, "size_px": [w, h], "pivot": pivot,
            "height_m": round(hi.z, 3), "tris": FP.tris([body] + extra), "verts": len(body.data.vertices), "render_s": round(t_r, 1),
            "sockets_rig": sockets(rig), "sockets_table": {k: [round(v[0], 3), round(v[1], 3)] for k, v in POSE.skeleton(p).items() if k[:3] in ("wr_", "ank")}}
    meta.update(FP.finish(f"probe_{which}", "figure", 384, rp))
    with open(os.path.join(FDIR, f"probe_{which}.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=1)
    say(f"probe {which}: body '{name}' ({meta['verts']} verts), skinned by {how}; {w}x{h} px at 384 px per metre (the figure's own bounds), {hi.z:.2f} m tall; "
        f"render {t_r:.1f} s, the values and the filter {meta['paint_s']} s, {time.time() - t0:.1f} s in all -> blender/preview/b258/figure/probe_{which}.png")
    say(f"  the price of the clip set from this frame: 100 drawings {100 * (t_r + meta['paint_s']) / 60:.0f} min, 200 drawings {200 * (t_r + meta['paint_s']) / 60:.0f} min (colour; a normal pass about a third more)")


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if argv and argv[0] == "inspect":
        inspect()
    elif len(argv) >= 2 and argv[0] == "probe":
        probe(argv[1], argv[2] if len(argv) > 2 else "idle")
    else:
        raise SystemExit("v7_figure: inspect | probe <object> [idle|walk]")
