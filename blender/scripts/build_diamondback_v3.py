"""B-158 (C2 Uranus design prep): the Diamondback Colossus, Uranus' apex (Bible §7.8: armoured in diamond at the rain layer;
only its joints take damage, visible when it reaches to feed; drops Prism plates), as a Grand contract §11.3 rig set (D-140:
up to 8 bones, "grand": true). ~24 m across at 1x, a set piece in the deep. Friendly-neutral (D-087): pie eyes, a closed
smile, no teeth. The Uranus palette (D-142): a night-slate body under faceted ice-white diamond plates; the exposed joints
glow ember amber (a tone; the palette's one warm accent is the soft living tissue under the armour).

  bones  body (root) -> neck -> head; arm_l (upper) -> fore_l; arm_r (upper) -> fore_r    (7 bones)
  swaps  fore_l / fore_r: armoured / reach (the elbow plates part: the joint shows - the only target)
  idle   a slow sway, the arms drifting (cycle_beats 4)       reach  an arm extends up, its joint exposed (per arm)
  react  a flinch: the arms fold in, the joints armoured

  python -I build_diamondback_v3.py <preview dir>      lock-free design preview at 0.25x (meridian.fakegp)
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

P = v3.PALETTES["uranus"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "uranus")


def DP(h):
    return v3.deep_of(h, "uranus")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, "colossus_" + name, **kw)
    return {"hide_f": m("hide_f", fill=SH(P["teal"]), ink=False), "hide_dp": m("hide_deep", fill=P["brown"], ink=False),
            "plate": m("plate", fill=P["offwhite"], ink=False), "plate_sh": m("plate_mid", fill=SH(P["offwhite"]), ink=False),
            "plate_dp": m("plate_deep", fill=P["sky"], ink=False), "joint": m("joint", fill=P["red"], ink=False), "joint_sh": m("joint_mid", fill=SH(P["red"]), ink=False),
            "eye": m("eye", fill=P["offwhite"]), "pupil": m("pupil", fill=G.INK, ink=False), "ink": m("ink", fill=None)}


def facets(d, M, cx, cz, rx, rz, n, seed):
    """A cluster of faceted diamond plates (ice white, a shaded facet each) over an area."""
    import random
    rnd = random.Random(seed)
    for k in range(n):
        x, z = cx + rnd.uniform(-rx, rx), cz + rnd.uniform(-rz, rz)
        s = rnd.uniform(0.35, 0.7)
        pts = [(x + s * math.cos(a), z + s * 0.8 * math.sin(a)) for a in [rnd.uniform(0, 0.3) + j * TAU / 5 for j in range(5)]]
        G.stroke(d, pts, M["plate"], 0.0, cyclic=True)
        G.stroke(d, [pts[0], pts[1], pts[2], (x, z)], M["plate_dp"], 0.0, cyclic=True)
        G.stroke(d, pts, M["ink"], I, cyclic=True)


def part_body(d, M):
    body = G.lumpy_ellipse(0.0, 0.0, 6.0, 3.6, n=60, lump=0.04, seed=3)
    G.stroke(d, body, M["hide_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in body if q[1] < -1.6] + [(0.0, -1.6)], M["hide_dp"], 0.0, cyclic=True)
    facets(d, M, -0.6, 1.0, 4.6, 1.8, 22, 7)                                               # the diamond armour
    G.stroke(d, body, M["ink"], O, cyclic=True)


def part_neck(d, M):
    neck = [(-0.9, 0.0), (0.9, 0.0), (0.7, 2.2), (-0.7, 2.2)]
    G.stroke(d, neck, M["hide_f"], 0.0, cyclic=True)
    facets(d, M, 0.0, 1.1, 0.5, 0.8, 4, 11)
    G.stroke(d, neck, M["ink"], O, cyclic=True)


def part_head(d, M):
    head = G.lumpy_ellipse(0.4, 1.0, 2.0, 1.5, n=40, lump=0.03, seed=13)
    G.stroke(d, head, M["hide_f"], 0.0, cyclic=True)
    facets(d, M, 0.0, 2.0, 1.4, 0.35, 6, 17)                                                # the diamond brow
    G.stroke(d, head, M["ink"], O, cyclic=True)
    for dx in (0.2, 1.1):
        G.pie_eye(d, dx, 1.0, 0.32, 0.4, M["pupil"], M["eye"], look=(0.5, -0.1), seed=19 + int(dx * 10), m_lid=M["ink"])
    G.stroke(d, G.bezier((0.0, 0.2), (0.65, -0.05), (1.4, 0.2), n=8), M["ink"], I)          # a closed smile


def part_upper(d, M, side):
    """An upper arm from the shoulder (0, 0) out and up: an armoured segment."""
    seg = G.hose_outline([(0.0, 0.0), (side * 2.4, 2.6)], 0.75)
    G.stroke(d, seg, M["hide_f"], 0.0, cyclic=True)
    facets(d, M, side * 1.2, 1.3, 0.6, 0.9, 5, 23 + side)
    G.stroke(d, seg, M["ink"], O, cyclic=True)


def part_fore(d, M, side, reach=False):
    """The forearm from the elbow (0, 0) up to a three-fingered catching hand; reach: the elbow plates part, the joint shows."""
    seg = G.hose_outline([(0.0, 0.0), (side * 0.8, 3.4)], 0.6)
    G.stroke(d, seg, M["hide_f"], 0.0, cyclic=True)
    facets(d, M, side * 0.5, 2.0, 0.4, 1.0, 4, 29 + side)
    G.stroke(d, seg, M["ink"], O, cyclic=True)
    hx, hz = side * 0.8, 3.4
    for j in (-1, 0, 1):                                                                   # the cupped hand's fingers
        a = math.radians(90 + 25 * j)
        G.stroke(d, G.hose_outline([(hx, hz), (hx + 1.0 * math.cos(a), hz + 1.0 * math.sin(a))], 0.22), M["hide_f"], O, cyclic=True)
    if reach:
        G.stroke(d, G.lumpy_ellipse(0.0, 0.1, 0.75, 0.55, n=18, lump=0.06, seed=41), M["joint_sh"], 0.0, cyclic=True)   # the exposed joint (a tone)
        G.stroke(d, G.lumpy_ellipse(0.0, 0.1, 0.4, 0.3, n=14, seed=42), M["joint"], 0.0, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(0.0, 0.1, 0.75, 0.55, n=18, lump=0.06, seed=41), M["ink"], I, cyclic=True)
    else:
        facets(d, M, 0.0, 0.1, 0.4, 0.3, 3, 43 + side)                                     # the elbow armoured


PARTS = {"body": part_body, "neck": part_neck, "head": part_head,
         "arm_l": lambda d, M: part_upper(d, M, -1), "arm_r": lambda d, M: part_upper(d, M, 1),
         "fore_l": lambda d, M: part_fore(d, M, -1), "fore_l_reach": lambda d, M: part_fore(d, M, -1, True),
         "fore_r": lambda d, M: part_fore(d, M, 1), "fore_r_reach": lambda d, M: part_fore(d, M, 1, True)}

RIG = {
    "name": "diamondback_colossus", "grand": True, "scale_note": "about 24 m across at 1x: a set piece in the deep (D-140: a Grand rig, 7 bones)",
    "bones": [{"name": "body", "part": "body", "parent": None, "offset_m": [0.0, 0.0], "order": 1},
              {"name": "neck", "part": "neck", "parent": "body", "offset_m": [3.6, 2.4], "order": 2},
              {"name": "head", "part": "head", "parent": "neck", "offset_m": [0.0, 2.0], "order": 3},
              {"name": "arm_l", "part": "arm_l", "parent": "body", "offset_m": [-3.4, 1.8], "order": 0},
              {"name": "fore_l", "part": "fore_l", "parent": "arm_l", "offset_m": [-2.4, 2.6], "order": 0},
              {"name": "arm_r", "part": "arm_r", "parent": "body", "offset_m": [1.0, 2.6], "order": 4},
              {"name": "fore_r", "part": "fore_r", "parent": "arm_r", "offset_m": [2.4, 2.6], "order": 5}],
    "swaps": {"fore_l": ["fore_l", "fore_l_reach"], "fore_r": ["fore_r", "fore_r_reach"]},
    "slots": [{"slot": "fore_l", "bone": "fore_l", "offset_m": [0.0, 0.0], "order": 0, "replaces_part": True},
              {"slot": "fore_r", "bone": "fore_r", "offset_m": [0.0, 0.0], "order": 5, "replaces_part": True}],
    "idle": {"type": "sway", "beat_bpm": 110, "cycle_beats": 4, "amplitude_deg": {"body": 1, "neck": 2, "head": 3, "arm_l": 4, "fore_l": 5, "arm_r": 4, "fore_r": 5},
             "lag": 0.7},
    "react": {"radius_m": 30.0, "action": "flinch", "arm_deg": -18, "swap": {"fore_l": "fore_l", "fore_r": "fore_r"}},
    "actions": {"reach": {"per_arm": True, "arm_deg": 25, "fore_deg": 20, "swap_state": "reach", "note": "the exposed joint is the only target (UNITY)"}},
}


def pose_idle(i, n=8):
    ph = TAU * i / n
    return {"body": math.sin(ph), "neck": 2 * math.sin(ph - 0.4), "head": 3 * math.sin(ph - 0.8), "arm_l": 4 * math.sin(ph - 0.5),
            "fore_l": 5 * math.sin(ph - 1.0), "arm_r": 4 * math.sin(ph - 0.3), "fore_r": 5 * math.sin(ph - 0.9)}, {}


def pose_reach(i):
    k = (0.0, 0.4, 0.8, 1.0, 1.0, 0.8, 0.4, 0.0)[i]
    rot, _s = pose_idle(i)
    rot["arm_r"], rot["fore_r"] = -25 * k, -20 * k
    return rot, ({"fore_r": "fore_r_reach"} if k > 0.3 else {})


def pose_react(i):
    k = (0.0, 0.6, 1.0, 1.0, 0.8, 0.5, 0.25, 0.0)[i]
    return {"body": -2 * k, "neck": -4 * k, "head": -6 * k, "arm_l": -18 * k, "fore_l": -12 * k, "arm_r": 18 * k, "fore_r": 12 * k}, {}


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


SPAN_W, SPAN_H, PIV = 26.0, 20.0, (0.5, 5.0 / 20.0)


def render_pose(rot_deg, swaps, scale=0.25, ss=2, seed=3):
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    draw_pose(d, M, rot_deg, swaps)
    W_, H_ = int(SPAN_W * 64 * scale), int(SPAN_H * 64 * scale)
    W_ += (-W_) % 4
    H_ += (-H_) % 4
    return GR.render_frame(fakegp.strokes_of(d, gp, as_object=("diamondback_colossus", "art")), W_, H_, 64 * scale, PIV, ss=ss, seed=seed)


SRC = os.path.join(os.path.dirname(HERE), "sources", "creatures")


def build(out=os.path.join(SRC, "uranus_diamondback_rigset.blend")):
    """Blender (the Uranus card): one GP object per part around its pivot, the rig on scene["rig_plants"]."""
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
    """render.py review_script (the Uranus export): the assembled colossus and its loops, stamped."""
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
    gp = fakegp.FakeGP()                                                                   # ink + palette at 1x on the reaching forearm
    M = mats(gp)
    d = fakegp.FakeDrawing()
    PARTS["fore_r_reach"](d, M)
    part1x, widths = GR.render_frame(fakegp.strokes_of(d, gp, as_object=("diamondback_colossus", "art")), 192, 320, 64, (0.3, 0.12), ss=2, seed=3)
    W = img.shape[1] + 200
    rows = []
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "b-158 diamondback colossus (uranus apex, d-087, no teeth): a grand rig set (d-140), 7 bones; forearms armoured / reach "
                        "(the exposed joint, the only target)", 6, 8)
    rows.append(head)
    sky = np.empty((img.shape[0] + 40, W, 3), np.float32)
    t = (np.arange(sky.shape[0]) / sky.shape[0])[:, None, None]
    sky[:] = (np.array(v3.hex_rgb(P["teal"]), np.float32) / 255) * (1 - 0.5 * t) + (np.array(v3.hex_rgb(P["brown"]), np.float32) / 255) * 0.5 * t
    review._over(sky, img, 10, 30)
    try:
        fr, piv = PR.surveyor_frame()
        k = max(1, int(round(1 / scale)))
        review._over(sky, fr[::k, ::k], img.shape[1] + 40, sky.shape[0] - fr.shape[0] // k - 30)
    except Exception:  # noqa: BLE001
        pass
    review._label(sky, f"{scale:g}x in the deep beside the surveyor (2 m, also {scale:g}x): ~24 m across", 6, 6)
    rows.append(sky)
    for title, poses in (("idle 8 (a slow sway, once per 4 beats)", [pose_idle(i) for i in range(8)]),
                         ("reach 8 (the right arm reaches: its elbow plates part, the ember joint shows)", [pose_reach(i) for i in range(8)]),
                         ("react 8 (a flinch: the arms fold in)", [pose_react(i) for i in range(8)])):
        frames = [render_pose(r, s, scale=0.0625, ss=2, seed=9 + j)[0] for j, (r, s) in enumerate(poses)]
        fw, fh = frames[0].shape[1], frames[0].shape[0]
        per = max(1, (W - 16) // (fw + 8))
        for r0 in range(0, len(frames), per):
            row = np.tile(review.PAPER, (fh + 26, W, 1)).astype(np.float32)
            row[22:, :] = np.array(v3.hex_rgb(P["sky"]), np.float32) / 255
            for j, im in enumerate(frames[r0:r0 + per]):
                review._over(row, im, 8 + j * (fw + 8), 22)
            review._label(row, f"{title} at 0.0625x" if r0 == 0 else "", 6, 2)
            rows.append(row)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    hits, off = v3.palette_hits(part1x, "uranus")
    problems = v3.validate_rigset({"key": "creatures/uranus/diamondback_colossus", "style": "v3", "ppu": 64,
                                   "parts": [{"name": n, "rect": [0, 0, 1, 1], "pivot": [0.5, 0.5]} for n in PARTS], "plants": [RIG]})
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink at 1x outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; uranus palette {hits * 100:.1f}% {off[:3]}; rig json {'valid (grand: 7 bones)' if not problems else problems}", 6, 8)
    review._label(foot, "faces: pie eyes, a closed smile, no teeth (d-087); the exposed joints glow ember (a tone): the one warm accent is the living tissue", 6, 28)
    rows.append(foot)
    out = np.vstack(rows)
    review._label(out, __import__("time").strftime("%m-%d %H:%M") + " " + stamp, 2, out.shape[0] - 16)
    path = path or os.path.join(out_dir, "review_b158_diamondback_preview.png")
    review.write(path, out)
    print("written", path, f"{scale:g}x frame {img.shape[1]}x{img.shape[0]}", f"| palette {hits * 100:.1f}% {off[:3]} | rig {problems or 'valid'}")


if __name__ == "__main__":
    preview(sys.argv[1])
