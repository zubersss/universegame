"""B-157 (C2 Saturn design prep): the Polar Hydra, Saturn's apex (Bible §7.7: a six-headed cloud serpent in the North Polar
Hexagon's eye; each head is undone by crossing a different wind-wall with its lure; the body drops the Hexacore), as a
Grand contract §11.3 rig set (D-140: up to 8 bones, "grand": true): the body (root) and six necks, each neck part carrying
its head. ~18 m wide at 1x, a set piece seen in the eye. Friendly-neutral (D-087): rounded serpent heads with pie eyes and
soft closed smiles, no teeth; a lost head dissolves into a puff of cloud (no stump). The proposed Saturn palette.

  bones  body (root) -> neck0 .. neck5 (fanned across the body's top)
  swaps  per neck: rest / struck (the eyes squeezed, the frill flat) / lost (a cloud puff where the head was)
  idle   the necks weave: a sway per neck, each a little later (cycle_beats 4 at 110 bpm)
  react  the struck head recoils (per head; UNITY picks the head)      head_lost  the neck swaps to its cloud puff

  python -I build_polar_hydra_v3.py <preview dir>      lock-free design preview at 0.25x (meridian.fakegp)
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
import build_c2_saturn_palette as SPAL  # noqa: E402

v3.PALETTES.setdefault("saturn", {k: h for k, (h, _r) in SPAL.SATURN.items()})   # the proposal, until LEAD accepts it
P = v3.PALETTES["saturn"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "saturn")


def DP(h):
    return v3.deep_of(h, "saturn")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, "hydra_" + name, **kw)
    return {"hide_f": m("hide_f", fill=P["sky"], ink=False), "hide_sh": m("hide_mid", fill=SH(P["sky"]), ink=False),
            "lining": m("lining", fill=P["offwhite"], ink=False), "scale": m("scale", fill=P["teal"], ink=False),
            "scale_sh": m("scale_mid", fill=SH(P["teal"]), ink=False), "frill_a": m("frill_a", fill=P["red"]), "frill_b": m("frill_b", fill=P["mustard"]),
            "frill_sh": m("frill_mid", fill=SH(P["red"]), ink=False), "puff": m("puff", fill=P["offwhite"]), "puff_sh": m("puff_mid", fill=SH(P["offwhite"]), ink=False),
            "eye": m("eye", fill=P["offwhite"]), "pupil": m("pupil", fill=G.INK, ink=False), "ink": m("ink", fill=None)}


NECKS = [(-3.0, 1.9, 112, 6.2), (-1.8, 2.3, 101, 7.0), (-0.6, 2.5, 93, 7.6), (0.6, 2.5, 87, 7.6), (1.8, 2.3, 79, 7.0), (3.0, 1.9, 68, 6.2)]


def part_body(d, M):
    """The root: a coiled cloud-serpent body (lumpy cloud lining on top, ring-ice scales below), its coils resting in the eye."""
    body = G.lumpy_ellipse(0.0, 0.6, 4.6, 2.0, n=64, lump=0.05, seed=3)
    G.stroke(d, body, M["hide_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in body if q[1] < 0.0] + [(0.0, 0.0)], M["scale"], 0.0, cyclic=True)                  # the scaled belly
    for k in range(9):                                                                     # belly scale arcs
        x = -3.6 + 0.9 * k
        G.seam(d, G.bezier((x, -0.6), (x + 0.45, -0.95), (x + 0.9, -0.6), n=6), M["ink"])
    for k in range(5):                                                                     # coil lines
        x = -3.2 + 1.6 * k
        G.seam(d, G.bezier((x, 2.2), (x - 0.4, 0.9), (x + 0.2, -0.2), n=8), M["ink"])
    top = [q for q in body if q[1] > 1.6]
    for j, q in enumerate(top[::3]):                                                       # cloud lining lumps along the top
        G.stroke(d, G.lumpy_ellipse(q[0], q[1] - 0.05, 0.45, 0.22, n=12, lump=0.1, seed=10 + j), M["lining"], 0.0, cyclic=True)
    G.stroke(d, body, M["ink"], O, cyclic=True)


def _neck(d, M, k, state="rest"):
    """Neck k from its root (0, 0) up to the head; state rest / struck / lost (a cloud puff instead of the head)."""
    _x, _z, deg, L = NECKS[k]
    a = math.radians(deg)
    tip = (L * math.cos(a), L * math.sin(a))
    curve = G.bezier((0.0, 0.0), (0.5 * L * math.cos(a) + 0.6 * math.sin(a), 0.5 * L * math.sin(a)), tip, n=12)
    out = G.hose_outline(curve, 0.42)
    G.stroke(d, out, M["hide_f"], 0.0, cyclic=True)
    G.stroke(d, G.hose_outline([(x + 0.18, z) for x, z in curve], 0.16), M["scale_sh"], 0.0, cyclic=True)          # a scale stripe
    G.ribs(d, curve[1:-1], 0.42, M["ink"], every=0.9, frac=0.55)
    G.stroke(d, out, M["ink"], O, cyclic=True)
    hx, hz = tip
    if state == "lost":                                                                    # the head dissolved into a cloud puff
        for j in range(4):
            G.stroke(d, G.lumpy_ellipse(hx + 0.4 * math.cos(j * 1.6), hz + 0.5 + 0.3 * math.sin(j * 1.6), 0.55, 0.45, n=14, lump=0.12, seed=40 + 6 * k + j),
                     M["puff"], I, cyclic=True)
        return
    fr = "frill_a" if k % 2 == 0 else "frill_b"
    for j in range(5):                                                                     # the frill crest (flat when struck)
        ang = math.radians(60 + 22 * j) if state == "rest" else math.radians(140 + 8 * j)
        G.stroke(d, [(hx - 0.3, hz + 0.3), (hx - 0.3 + 0.9 * math.cos(ang), hz + 0.3 + 0.9 * math.sin(ang)),
                     (hx - 0.3 + 0.75 * math.cos(ang + 0.25), hz + 0.3 + 0.75 * math.sin(ang + 0.25))], M[fr], I, cyclic=True)
    head = G.lumpy_ellipse(hx + 0.3, hz + 0.1, 0.95, 0.7, n=30, lump=0.03, seed=20 + k)
    G.stroke(d, head, M["hide_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in head if q[1] < hz - 0.15] + [(hx + 0.3, hz - 0.15)], M["scale"], 0.0, cyclic=True)    # the scaled chin
    G.stroke(d, head, M["ink"], O, cyclic=True)
    if state == "struck":
        for dz in (0.0, -0.18):
            G.stroke(d, G.bezier((hx + 0.25, hz + 0.3 + dz), (hx + 0.5, hz + 0.45 + dz * 0.5), (hx + 0.75, hz + 0.3 + dz), n=5), M["ink"], I)
    else:
        G.pie_eye(d, hx + 0.5, hz + 0.3, 0.2, 0.26, M["pupil"], M["eye"], look=(0.6, -0.1), seed=30 + k, m_lid=M["ink"])
    G.stroke(d, G.bezier((hx + 0.6, hz - 0.2), (hx + 0.9, hz - 0.32), (hx + 1.15, hz - 0.15), n=6), M["ink"], I)   # a soft closed smile


PARTS = {"body": part_body}
for _k in range(6):
    for _s in ("rest", "struck", "lost"):
        PARTS[f"neck{_k}_{_s}"] = (lambda k, s: (lambda d, M: _neck(d, M, k, s)))(_k, _s)

RIG = {
    "name": "polar_hydra", "grand": True, "scale_note": "about 18 m wide at 1x: a set piece in the Hexagon's eye (D-140: a Grand rig, 7 bones)",
    "bones": [{"name": "body", "part": "body", "parent": None, "offset_m": [0.0, 0.0], "order": 0}] + [
        {"name": f"neck{k}", "part": f"neck{k}_rest", "parent": "body", "offset_m": [x, z], "order": 1 + (k if k < 3 else 5 - k)}
        for k, (x, z, _deg, _L) in enumerate(NECKS)],
    "swaps": {f"neck{k}": [f"neck{k}_rest", f"neck{k}_struck", f"neck{k}_lost"] for k in range(6)},
    "slots": [{"slot": f"neck{k}", "bone": f"neck{k}", "offset_m": [0.0, 0.0], "order": 1 + (k if k < 3 else 5 - k), "replaces_part": True} for k in range(6)],
    "idle": {"type": "sway", "beat_bpm": 110, "cycle_beats": 4, "amplitude_deg": dict({"body": 1}, **{f"neck{k}": 7 for k in range(6)}), "lag": 0.6},
    "react": {"radius_m": 30.0, "action": "recoil", "per_bone": True, "swap_state": "struck", "neck_deg": -10},
    "actions": {"head_lost": {"swap_state": "lost", "per_bone": True}},
}


def pose_idle(i, n=8):
    ph = TAU * i / n
    return dict({"body": math.sin(ph)}, **{f"neck{k}": 7 * math.sin(ph - 0.6 * k) for k in range(6)}), {}


def pose_react(i, head=2):
    k = (0.0, 0.6, 1.0, 1.0, 0.8, 0.5, 0.25, 0.0)[i]
    rot = dict({"body": 0.0}, **{f"neck{j}": 3 * math.sin(i - 0.6 * j) for j in range(6)})
    rot[f"neck{head}"] = -10 * k
    return rot, ({f"neck{head}": f"neck{head}_struck"} if k > 0.4 else {})


def pose_lost(i, lost=(0, 4)):
    rot, _s = pose_idle(i)
    return rot, {f"neck{k}": f"neck{k}_lost" for k in lost}


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


SPAN_W, SPAN_H, PIV = 20.0, 13.0, (0.5, 3.0 / 13.0)


def render_pose(rot_deg, swaps, scale=0.25, ss=2, seed=3):
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    draw_pose(d, M, rot_deg, swaps)
    W_, H_ = int(SPAN_W * 64 * scale), int(SPAN_H * 64 * scale)
    W_ += (-W_) % 4
    H_ += (-H_) % 4
    return GR.render_frame(fakegp.strokes_of(d, gp, as_object=("polar_hydra", "art")), W_, H_, 64 * scale, PIV, ss=ss, seed=seed)


SRC = os.path.join(os.path.dirname(HERE), "sources", "creatures")


def build(out=os.path.join(SRC, "saturn_polar_hydra_rigset.blend")):
    """Blender (the Saturn card): one GP object per part around its pivot, the rig on scene["rig_plants"]."""
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
    """render.py review_script (the Saturn export): the assembled hydra and its loops, stamped."""
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
    gp = fakegp.FakeGP()                                                                   # ink + palette measured at 1x on one neck
    M = mats(gp)
    d = fakegp.FakeDrawing()
    PARTS["neck2_rest"](d, M)
    neck1x, widths = GR.render_frame(fakegp.strokes_of(d, gp, as_object=("polar_hydra", "art")), 320, 640, 64, (0.5, 0.05), ss=2, seed=3)
    W = img.shape[1] + 200
    rows = []
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "b-157 polar hydra (saturn apex, d-087 friendly-neutral, no teeth): a grand rig set (d-140), 7 bones (body + six necks), "
                        "per neck rest / struck / lost (a cloud puff)", 6, 8)
    rows.append(head)
    sky = np.empty((img.shape[0] + 40, W, 3), np.float32)
    t = (np.arange(sky.shape[0]) / sky.shape[0])[:, None, None]
    sky[:] = (np.array(v3.hex_rgb(P["sky"]), np.float32) / 255) * (1 - 0.3 * t) + (np.array(v3.hex_rgb(P["teal"]), np.float32) / 255) * 0.3 * t
    review._over(sky, img, 10, 30)
    try:
        fr, piv = PR.surveyor_frame()
        k = max(1, int(round(1 / scale)))
        fr = fr[::k, ::k]
        review._over(sky, fr, img.shape[1] + 40, sky.shape[0] - fr.shape[0] - 30)
    except Exception:  # noqa: BLE001
        pass
    review._label(sky, f"{scale:g}x in the hexagon's eye beside the surveyor (2 m, also {scale:g}x): ~18 m wide", 6, 6)
    rows.append(sky)
    for title, poses in (("idle 8 (the necks weave, each a little later; once per 4 beats)", [pose_idle(i) for i in range(8)]),
                         ("react 8 (head 2 struck: it recoils, eyes squeezed, frill flat)", [pose_react(i) for i in range(8)]),
                         ("head_lost (heads 0 and 4 lost: cloud puffs)", [pose_lost(i) for i in range(4)])):
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
    hits, off = v3.palette_hits(neck1x, "saturn")
    problems = v3.validate_rigset({"key": "creatures/saturn/polar_hydra", "style": "v3", "ppu": 64, "parts": [{"name": n, "rect": [0, 0, 1, 1], "pivot": [0.5, 0.5]} for n in PARTS],
                                   "plants": [RIG]})
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink at 1x outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; saturn palette {hits * 100:.1f}% {off[:3]}; rig json {'valid (grand: 7 bones)' if not problems else problems}", 6, 8)
    review._label(foot, "faces: pie eyes, soft closed smiles, frill crests; no teeth (d-087); a lost head becomes a cloud puff (no stump)", 6, 28)
    rows.append(foot)
    out = np.vstack(rows)
    review._label(out, __import__("time").strftime("%m-%d %H:%M") + " " + stamp, 2, out.shape[0] - 16)
    path = path or os.path.join(out_dir, "review_b157_polar_hydra_preview.png")
    review.write(path, out)
    print("written", path, f"{scale:g}x frame {img.shape[1]}x{img.shape[0]}", f"| palette {hits * 100:.1f}% {off[:3]} | rig {problems or 'valid'}")


if __name__ == "__main__":
    preview(sys.argv[1])
