"""B-161 (C2 Neptune design prep): the Umbral Leviathan, Neptune's apex (Bible §7.9: lives in the Great Dark Spot around the
Meridian herself; the final encounter is a full Survey of the Grand creature, D-087), as a Grand contract §11.3 rig set
(D-140: up to 8 bones, "grand": true). ~30 m nose to tail at 1x (a full 1920 px screen: a set piece circling the wreck).
Friendly-neutral (D-087): wisp-white pie eyes, a closed smile, no teeth. The Neptune palette (D-148): a dark Neptune-blue
hide over a pale belly, storm-violet bands along the back that BREATHE with the storm (the bands are the Survey puzzle: each
body segment swaps dim / lit as the Survey reads it), long whiskers trailing downwind.

  bones  body0 (root) -> head -> whiskers; body0 -> body1 -> body2 -> tail; body0 -> fin_f; body1 -> fin_b    (8 bones)
  swaps  body0 / body1 / body2: dim / lit (the Survey lights them one by one; UNITY drives the order)
  idle   a slow travelling wave head to tail (cycle_beats 4), the whiskers lagging
  circle a wider wave (UNITY carries it round the wreck)      survey  it holds still and its bands light 0 -> 1 -> 2
  react  a curl: the body bends away, the fins fold

  python -I build_umbral_leviathan_v3.py <preview dir>      lock-free design preview at 0.25x (meridian.fakegp)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp, v3  # noqa: E402

try:
    import bpy
    if not hasattr(bpy, "data"):
        raise ImportError
    import gp_draw as G
except ImportError:
    G = fakegp.install()
import gp_raster as GR  # noqa: E402

P = v3.PALETTES["neptune"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "neptune")


def DP(h):
    return v3.deep_of(h, "neptune")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, "leviathan_" + name, **kw)
    return {"hide_f": m("hide_f", fill=SH(P["sky"]), ink=False), "hide_dp": m("hide_deep", fill=DP(P["sky"]), ink=False),
            "belly": m("belly", fill=SH(P["offwhite"]), ink=False), "belly_sh": m("belly_mid", fill=DP(P["offwhite"]), ink=False),
            "band_dim": m("band_dim", fill=DP(P["mustard"]), ink=False), "band": m("band", fill=P["mustard"], ink=False),
            "band_core": m("band_core", fill=P["offwhite"], ink=False), "fin": m("fin", fill=DP(P["sky"]), ink=False),
            "whisker": m("whisker", fill=None, ink_hex=SH(P["offwhite"])), "tip": m("tip", fill=P["offwhite"]),
            "eye": m("eye", fill=P["offwhite"]), "pupil": m("pupil", fill=G.INK, ink=False), "ink": m("ink", fill=None)}


SEGS = {"body0": (0.0, 4.6, 2.6), "body1": (-3.6, 4.3, 2.2), "body2": (-3.1, 3.8, 1.7)}   # cx, rx, rz in the bone's frame


def segment(d, M, name, lit):
    """A body segment: the blue hide, the pale belly, ring seams, and two storm-violet bands along the back (dim / lit)."""
    cx, rx, rz = SEGS[name]
    body = G.lumpy_ellipse(cx, 0.0, rx, rz, n=56, lump=0.03, seed=len(name) * 7 + int(cx))
    G.stroke(d, body, M["hide_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in body if q[1] < -rz * 0.25] + [(cx, -rz * 0.25)], M["belly"], 0.0, cyclic=True)
    G.stroke(d, [q for q in body if q[1] < -rz * 0.7] + [(cx, -rz * 0.7)], M["belly_sh"], 0.0, cyclic=True)
    G.stroke(d, [q for q in body if q[1] > rz * 0.55] + [(cx, rz * 0.55)], M["hide_dp"], 0.0, cyclic=True)
    for j, bx in enumerate((cx - rx * 0.35, cx + rx * 0.3)):                              # the two bands across the back
        band = [(bx - 0.45, rz * 0.98), (bx + 0.45, rz * 0.98), (bx + 0.75, -rz * 0.1), (bx - 0.15, -rz * 0.15)]
        band = [(x, z * (1 - 0.15 * abs(x - cx) / rx)) for x, z in band]
        G.stroke(d, band, M["band" if lit else "band_dim"], 0.0, cyclic=True)
        if lit:
            G.stroke(d, G.lumpy_ellipse(bx + 0.25, rz * 0.4, 0.22, 0.4, n=12, seed=60 + j), M["band_core"], 0.0, cyclic=True)
        G.stroke(d, band, M["ink"], I, cyclic=True)
    for k in range(4):                                                                    # ring seams on the belly
        x = cx - rx * 0.6 + rx * 0.4 * k
        G.seam(d, [(x, -rz * 0.3), (x + 0.15, -rz * 0.85)], M["ink"])
    G.hatch(d, cx - rx * 0.5, rz * 0.3, M["ink"], n=3, length=0.5, spacing=0.18, angle_deg=70, seed=len(name))
    G.stroke(d, body, M["ink"], O, cyclic=True)


def part_head(d, M):
    head = G.lumpy_ellipse(2.2, 0.2, 2.8, 2.15, n=48, lump=0.03, seed=13)
    G.stroke(d, head, M["hide_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in head if q[1] < -0.6] + [(2.2, -0.6)], M["belly"], 0.0, cyclic=True)
    G.stroke(d, [q for q in head if q[1] > 1.4] + [(2.2, 1.4)], M["hide_dp"], 0.0, cyclic=True)
    G.stroke(d, head, M["ink"], O, cyclic=True)
    for dx in (2.3, 3.3):
        G.pie_eye(d, dx, 0.75, 0.4, 0.5, M["pupil"], M["eye"], look=(0.6, -0.1), seed=19 + int(dx * 10), m_lid=M["ink"])
    G.stroke(d, G.bezier((2.9, -0.55), (3.8, -0.85), (4.7, -0.45), n=8), M["ink"], I)        # a closed smile, no teeth
    G.seam(d, [(4.8, 0.2), (4.9, 0.0)], M["ink"])                                         # a nostril


def part_whiskers(d, M):
    """Two long whiskers from the cheek (0, 0), trailing back and down with wisp-white tips (they drag downwind)."""
    for k, (dz, L) in enumerate(((0.0, 7.0), (-0.4, 5.5))):
        w = G.bezier((0.0, dz), (-L * 0.3, dz - 1.6), (-L * 0.7, dz - 0.6), (-L, dz - 1.4), n=16)
        G.stroke(d, w, M["ink"], I)
        G.stroke(d, G.lumpy_ellipse(w[-1][0], w[-1][1], 0.22, 0.18, n=10, seed=70 + k), M["tip"], I, cyclic=True)


def part_tail(d, M):
    tail = G.bezier((0.0, 1.5), (-2.5, 1.0), (-5.0, 0.5), n=10) + [(-5.6, 1.6), (-6.4, 1.2), (-5.6, -0.2), (-6.4, -1.0), (-5.4, -0.6)] + \
        G.bezier((-5.0, -0.3), (-2.5, -0.9), (0.0, -1.5), n=10)
    G.stroke(d, tail, M["hide_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in tail if q[1] < -0.3] + [(-2.5, -0.3)], M["belly"], 0.0, cyclic=True)
    G.stroke(d, [(-5.0, 0.5), (-5.6, 1.6), (-6.4, 1.2), (-5.6, -0.2), (-6.4, -1.0), (-5.4, -0.6), (-5.0, -0.3)], M["fin"], 0.0, cyclic=True)   # the fluke
    for z in (0.9, 0.0, -0.6):
        G.seam(d, [(-5.2, z * 0.4), (-6.0, z)], M["ink"])
    G.stroke(d, tail, M["ink"], O, cyclic=True)


def part_fin(d, M, L, seed):
    """A long flipper from its root (0, 0), sweeping back and down."""
    fin = [(0.6, 0.0), (-0.6, 0.1)] + G.bezier((-0.6, 0.1), (-L * 0.6, -L * 0.2), (-L, -L * 0.45), n=10)[1:] + \
        G.bezier((-L, -L * 0.45), (-L * 0.4, -L * 0.5), (0.6, 0.0), n=10)[1:-1]
    G.stroke(d, fin, M["fin"], 0.0, cyclic=True)
    for t in (0.35, 0.65):
        G.seam(d, [(0.0, 0.0), (-L * t, -L * (0.25 + 0.1 * t))], M["ink"])
    G.stroke(d, fin, M["ink"], O, cyclic=True)


PARTS = {"body0": lambda d, M: segment(d, M, "body0", False), "body0_lit": lambda d, M: segment(d, M, "body0", True),
         "body1": lambda d, M: segment(d, M, "body1", False), "body1_lit": lambda d, M: segment(d, M, "body1", True),
         "body2": lambda d, M: segment(d, M, "body2", False), "body2_lit": lambda d, M: segment(d, M, "body2", True),
         "head": part_head, "whiskers": part_whiskers, "tail": part_tail,
         "fin_f": lambda d, M: part_fin(d, M, 4.2, 81), "fin_b": lambda d, M: part_fin(d, M, 3.2, 82)}

RIG = {
    "name": "umbral_leviathan", "grand": True, "scale_note": "about 30 m nose to tail at 1x: a set piece circling the Meridian (D-140: a Grand rig, 8 bones)",
    "bones": [{"name": "body0", "part": "body0", "parent": None, "offset_m": [0.0, 0.0], "order": 3},
              {"name": "head", "part": "head", "parent": "body0", "offset_m": [3.9, 0.3], "order": 6},
              {"name": "whiskers", "part": "whiskers", "parent": "head", "offset_m": [3.9, -0.4], "order": 7},
              {"name": "body1", "part": "body1", "parent": "body0", "offset_m": [-3.6, -0.1], "order": 2},
              {"name": "body2", "part": "body2", "parent": "body1", "offset_m": [-6.8, -0.1], "order": 1},
              {"name": "tail", "part": "tail", "parent": "body2", "offset_m": [-6.3, 0.0], "order": 0},
              {"name": "fin_f", "part": "fin_f", "parent": "body0", "offset_m": [1.4, -1.9], "order": 5},
              {"name": "fin_b", "part": "fin_b", "parent": "body1", "offset_m": [-3.4, -1.6], "order": 4}],
    "swaps": {"body0": ["body0", "body0_lit"], "body1": ["body1", "body1_lit"], "body2": ["body2", "body2_lit"]},
    "slots": [{"slot": s, "bone": s, "offset_m": [0.0, 0.0], "order": o, "replaces_part": True} for s, o in (("body0", 3), ("body1", 2), ("body2", 1))],
    "idle": {"type": "sway", "beat_bpm": 110, "cycle_beats": 4,
             "amplitude_deg": {"body0": 1, "head": 2, "whiskers": 4, "body1": 2, "body2": 3, "tail": 5, "fin_f": 4, "fin_b": 4}, "lag": 0.8},
    "react": {"radius_m": 30.0, "action": "curl", "deg": {"head": -8, "body1": 6, "body2": 8, "tail": 10, "fin_f": -15, "fin_b": -15}},
    "actions": {"circle": {"amplitude_scale": 2.2, "note": "a wider wave; UNITY carries it round the wreck"},
                "survey": {"hold": True, "swap_sequence": [{"body0": "body0_lit"}, {"body1": "body1_lit"}, {"body2": "body2_lit"}],
                           "beats_each": 4, "note": "the bands light one by one as the Survey reads them (the final encounter, D-087)"}},
}


def pose_idle(i, n=8, amp=1.0):
    ph = TAU * i / n
    a = RIG["idle"]["amplitude_deg"]
    lag = {"body0": 0.0, "head": -0.5, "whiskers": 1.6, "body1": 0.8, "body2": 1.6, "tail": 2.4, "fin_f": 0.6, "fin_b": 1.4}
    return {b: amp * a[b] * math.sin(ph - lag[b]) for b in a}, {}


def pose_survey(i):
    rot, _s = pose_idle(i, amp=0.3)
    lit = {}
    for k, s in enumerate(("body0", "body1", "body2")):
        if i >= 2 + 2 * k:
            lit[s] = s + "_lit"
    return rot, lit


def pose_react(i):
    k = (0.0, 0.6, 1.0, 1.0, 0.8, 0.5, 0.25, 0.0)[i]
    return {b: k * v for b, v in RIG["react"]["deg"].items()}, {}


def world_xf(rot_deg):
    by = {b["name"]: b for b in RIG["bones"]}
    out = {}

    def get(name):
        if name in out:
            return out[name]
        b = by[name]
        a = math.radians(rot_deg.get(name, 0.0))
        ca, sa = math.cos(a), math.sin(a)
        ox, oz = b["offset_m"]
        if b["parent"] is None:
            f = (lambda ca=ca, sa=sa, ox=ox, oz=oz: (lambda pts: [(ox + x * ca - z * sa, oz + x * sa + z * ca) for x, z in pts]))()
        else:
            pf = get(b["parent"])
            f = (lambda pf=pf, ca=ca, sa=sa, ox=ox, oz=oz: (lambda pts: pf([(ox + x * ca - z * sa, oz + x * sa + z * ca) for x, z in pts])))()
        out[name] = f
        return f
    for b in RIG["bones"]:
        get(b["name"])
    return out


def draw_pose(d, M, rot_deg, swaps):
    xf = world_xf(rot_deg)
    for b in sorted(RIG["bones"], key=lambda b: b["order"]):
        PARTS[swaps.get(b["name"], b["part"])](G.Xf(d, xf[b["name"]]), M)


SPAN_W, SPAN_H = 36.0, 14.0
PIV = (24.0 / SPAN_W, 7.5 / SPAN_H)                                                       # body0's root inside the span


def render_pose(rot_deg, swaps, scale=0.25, ss=2, seed=3):
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    draw_pose(d, M, rot_deg, swaps)
    W_, H_ = int(SPAN_W * 64 * scale), int(SPAN_H * 64 * scale)
    W_ += (-W_) % 4
    H_ += (-H_) % 4
    return GR.render_frame(fakegp.strokes_of(d, gp, as_object=("umbral_leviathan", "art")), W_, H_, 64 * scale, PIV, ss=ss, seed=seed)


SRC = os.path.join(os.path.dirname(HERE), "sources", "creatures")


def build(out=os.path.join(SRC, "neptune_leviathan_rigset.blend")):
    """Blender (the Neptune card): one GP object per part around its pivot, the rig on scene["rig_plants"]."""
    import json as _json
    import bpy
    scene = G.new_scene()
    scene["rig_plants"] = _json.dumps([RIG])
    coll = G.collection("parts")
    for name, fn in PARTS.items():
        ob, gp = G.gp_object("part_" + name, coll)
        layer = gp.layers.new("art")
        fn(G.drawing(layer, 1), mats(gp))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


def main(out):
    """render.py review_script (the Neptune export): the assembled leviathan and its loops, stamped."""
    fakegp.install()
    try:
        preview(os.path.dirname(out), path=out, stamp="export")
    finally:
        fakegp.restore()
    return []


def preview(out_dir, scale=0.25, path=None, stamp="preview (not exported)"):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    img, _w = render_pose(*pose_idle(0), scale=scale)
    lit, _w2 = render_pose(*pose_survey(7), scale=scale)
    gp = fakegp.FakeGP()                                                                   # ink + palette at 1x on the lit front segment
    M = mats(gp)
    d = fakegp.FakeDrawing()
    PARTS["body0_lit"](d, M)
    part1x, widths = GR.render_frame(fakegp.strokes_of(d, gp, as_object=("umbral_leviathan", "art")), 640, 384, 64, (0.5, 0.5), ss=2, seed=3)
    W = img.shape[1] + 200
    rows = []
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "b-161 umbral leviathan (neptune apex, d-087, no teeth): a grand rig set (d-140), 8 bones; the bands dim / lit (the survey puzzle)", 6, 8)
    rows.append(head)
    for im, note in ((img, "idle"), (lit, "survey: all three segments lit")):
        sky = np.empty((im.shape[0] + 40, W, 3), np.float32)
        t = (np.arange(sky.shape[0]) / sky.shape[0])[:, None, None]
        sky[:] = (np.array(v3.hex_rgb(P["brown"]), np.float32) / 255) * (1 - 0.4 * t) + (np.array(v3.hex_rgb(P["sky"]), np.float32) / 255) * 0.4 * t
        review._over(sky, im, 10, 30)
        try:
            fr, piv = PR.surveyor_frame()
            k = max(1, int(round(1 / scale)))
            review._over(sky, fr[::k, ::k], im.shape[1] + 40, sky.shape[0] - fr.shape[0] // k - 30)
        except Exception:  # noqa: BLE001
            pass
        review._label(sky, f"{scale:g}x in the dark spot beside the surveyor (2 m, also {scale:g}x): ~30 m, {note}", 6, 6)
        rows.append(sky)
    for title, poses in (("idle 8 (a slow wave head to tail, once per 4 beats)", [pose_idle(i) for i in range(8)]),
                         ("survey 8 (it holds; the bands light 0 -> 1 -> 2)", [pose_survey(i) for i in range(8)]),
                         ("react 8 (a curl away, the fins fold)", [pose_react(i) for i in range(8)])):
        frames = [render_pose(r, s, scale=0.0625, ss=2, seed=9 + j)[0] for j, (r, s) in enumerate(poses)]
        fw, fh = frames[0].shape[1], frames[0].shape[0]
        per = max(1, (W - 16) // (fw + 8))
        for r0 in range(0, len(frames), per):
            row = np.tile(review.PAPER, (fh + 26, W, 1)).astype(np.float32)
            row[22:, :] = np.array(v3.hex_rgb(P["brown"]), np.float32) / 255
            for j, im in enumerate(frames[r0:r0 + per]):
                review._over(row, im, 8 + j * (fw + 8), 22)
            review._label(row, f"{title} at 0.0625x" if r0 == 0 else "", 6, 2)
            rows.append(row)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    hits, off = v3.palette_hits(part1x, "neptune")
    problems = v3.validate_rigset({"key": "creatures/neptune/umbral_leviathan", "style": "v3", "ppu": 64,
                                   "parts": [{"name": n, "rect": [0, 0, 1, 1], "pivot": [0.5, 0.5]} for n in PARTS], "plants": [RIG]})
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink at 1x outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; neptune palette {hits * 100:.1f}% {off[:3]}; rig json {'valid (grand: 8 bones)' if not problems else problems}", 6, 8)
    review._label(foot, "faces: wisp-white pie eyes, a closed smile, no teeth (d-087); ours: a storm-coloured whale-eel whose breathing bands are the survey puzzle", 6, 28)
    rows.append(foot)
    out = np.vstack(rows)
    review._label(out, __import__("time").strftime("%m-%d %H:%M") + " " + stamp, 2, out.shape[0] - 16)
    path = path or os.path.join(out_dir, "review_b161_leviathan_preview.png")
    review.write(path, out)
    print("written", path, f"{scale:g}x frame {img.shape[1]}x{img.shape[0]}", f"| palette {hits * 100:.1f}% {off[:3]} | rig {problems or 'valid'}")


if __name__ == "__main__":
    preview(sys.argv[1])
