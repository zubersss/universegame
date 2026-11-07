"""B-155 (C2 Jupiter design prep): the Vortex Whale, Jupiter's apex (Bible §7.6: a 500 m floater in the Great Red Spot whose
song stuns; a multi-stage hunt that is UNITY's), as a contract §11.3 rig set like the Hadal Maw (D-119 / D-127): parts on
one sheet + 6 bones. Drawn ~48 m long at 1x (the fiction's 500 m would be 32,000 px; like the Maw's 34 m for 40 m, it is
a set piece seen in passing: head, flank, flukes; the size needs LEAD's ruling). Friendly-neutral (D-087): one big pie
eye, a long closed smile, no teeth. Its hide mirrors the storm it lives in: a brick back with rust bands and cream swirl
marks, a cream pleated belly. The song's rings are drawn tones (no emission). Jupiter palette (D-137), v3.1 ink.

  bones  head (root) -> body1 -> body2 -> tail (the flukes); fin (pectoral, child of body1); throat (child of head)
  swaps  throat: throat_rest / throat_song (swollen, ripple rings); head: head / head_squint (the harpooned flinch)
  idle   a rolling glide: a sway travelling down the bones once per 4 beats at 110 bpm (cycle_beats 4), the fin rowing
  song   the throat swells and the rings ripple out (4 beats)          react  a slow turn: the head lifts, the body follows
  harpooned  a flinch: the eye squeezes shut, the flukes lift

  python -I build_vortex_whale_v3.py <preview dir>      lock-free design preview at 0.25x (meridian.fakegp)
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

P = v3.PALETTES["jupiter"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "jupiter")


def DP(h):
    return v3.deep_of(h, "jupiter")


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, "whale_" + name, **kw)
    return {
        "hide": m("hide", fill=P["red"]), "hide_f": m("hide_f", fill=P["red"], ink=False), "hide_sh": m("hide_mid", fill=SH(P["red"]), ink=False),
        "hide_dp": m("hide_deep", fill=DP(P["red"]), ink=False), "band": m("band", fill=P["mustard"], ink=False),
        "belly_f": m("belly_f", fill=P["offwhite"], ink=False), "belly_sh": m("belly_mid", fill=SH(P["offwhite"]), ink=False),
        "swirl": m("swirl", fill=P["offwhite"], ink=False), "fin": m("fin", fill=SH(P["red"])), "fin_sh": m("fin_mid", fill=DP(P["red"]), ink=False),
        "edge": m("edge", fill=P["teal"], ink=False), "knob": m("knob", fill=P["offwhite"]),
        "ring": m("ring", fill=P["offwhite"], ink=False, fill_alpha=0.35), "ring2": m("ring2", fill=P["teal"], ink=False, fill_alpha=0.25),
        "eye": m("eye", fill=P["offwhite"]), "pupil": m("pupil", fill=G.INK, ink=False), "ink": m("ink", fill=None),
    }


def H(xg):
    """The body's half-height along the whale (x from the head joint 0 back to the tail base -30 m): one smooth taper."""
    t = min(max(-xg / 30.0, 0.0), 1.0)
    return 1.0 + 3.6 * (0.5 + 0.5 * math.cos(math.pi * t ** 1.1))


def swirl_mark(d, M, cx, cz, r, seed):
    """A cream storm-swirl mark on the hide (a short log spiral as a tapering hose)."""
    pts = [(cx + r * (1 - t) * math.cos(4.5 * t + seed), cz + r * 0.6 * (1 - t) * math.sin(4.5 * t + seed)) for t in [k / 14 for k in range(15)]]
    G.stroke(d, G.hose_outline(pts[:11], r * 0.12), M["swirl"], 0.0, cyclic=True)


def segment(d, M, length, g0, seed, swirls=True):
    """A body segment from its joint (local x 0, global g0) back `length` m, reaching 0.8 m forward under the previous part;
    only the top and bottom edges are inked. A brick back with rust bands, a cream pleated belly, cream swirl marks."""
    n = 24
    xs = [0.8 - (length + 0.8) * i / (n - 1) for i in range(n)]
    hh = [H(g0 + x) for x in xs]
    top = [(x, h * (1.0 + 0.02 * math.sin(i * 1.1 + seed))) for i, (x, h) in enumerate(zip(xs, hh))]
    bot = [(x, -h * 0.9) for x, h in zip(xs, hh)]
    G.stroke(d, top + bot[::-1], M["hide_f"], 0.0, cyclic=True)
    G.stroke(d, top + [(x, h * 0.8) for x, h in zip(xs, hh)][::-1], M["hide_sh"], 0.0, cyclic=True)        # a back shadow
    for f0, f1 in ((0.45, 0.6), (0.15, 0.25)):                                                             # two rust bands (the planet's)
        G.stroke(d, [(x, h * f1) for x, h in zip(xs, hh)] + [(x, h * f0) for x, h in zip(xs, hh)][::-1], M["band"], 0.0, cyclic=True)
    G.stroke(d, [(x, -h * 0.3) for x, h in zip(xs, hh)] + bot[::-1], M["belly_f"], 0.0, cyclic=True)        # the cream belly
    G.stroke(d, [(x, -h * 0.75) for x, h in zip(xs, hh)] + bot[::-1], M["belly_sh"], 0.0, cyclic=True)
    for k in range(3):                                                                                       # the belly pleats
        G.seam(d, [(x, -h * (0.42 + 0.14 * k)) for x, h in zip(xs, hh)][2:-1], M["ink"])
    G.seam(d, [(x, -h * 0.3) for x, h in zip(xs, hh)][2:-1], M["ink"])
    if swirls:
        for i in range(3, n - 3, 6):
            swirl_mark(d, M, xs[i], hh[i] * 0.35, hh[i] * 0.45, seed + i)
    G.hatch(d, -length / 2, hh[n // 2] * 0.7, M["ink"], n=4, length=0.6, spacing=0.25, angle_deg=65, seed=seed)
    G.stroke(d, top[1:], M["ink"], O)
    G.stroke(d, bot[1:], M["ink"], O)


def part_body1(d, M):
    segment(d, M, 14.0, 0.0, 11)


def part_body2(d, M):
    segment(d, M, 12.0, -14.0, 23)


def part_tail(d, M):
    segment(d, M, 4.0, -26.0, 37, swirls=False)
    G.stroke(d, G.bezier((-4.0, 1.1), (-4.4, 0.0), (-4.0, -1.0), n=6), M["ink"], O)                       # the peduncle's end
    t = -4.0
    fluke = [(t + 0.4, 0.6), (t - 2.0, 4.6), (t - 4.6, 6.6), (t - 5.4, 6.0), (t - 3.6, 2.6), (t - 3.0, 0.0), (t - 3.6, -2.6),
             (t - 5.4, -6.0), (t - 4.6, -6.6), (t - 2.0, -4.6), (t + 0.4, -0.6)]
    G.stroke(d, fluke, M["fin"], O, cyclic=True)
    G.stroke(d, [(t - 4.6, 6.6), (t - 5.4, 6.0), (t - 3.6, 2.6), (t - 3.0, 0.0), (t - 3.6, -2.6), (t - 5.4, -6.0), (t - 4.6, -6.6),
                 (t - 4.4, -5.6), (t - 3.2, -2.4), (t - 2.6, 0.0), (t - 3.2, 2.4), (t - 4.4, 5.6)], M["edge"], 0.0, cyclic=True)   # festoon trailing edge
    G.stroke(d, [(t + 0.4, -0.6), (t - 2.0, -4.6), (t - 4.6, -6.6), (t - 3.6, -2.6), (t - 3.0, 0.0)], M["fin_sh"], 0.0, cyclic=True)
    for zz in (4.4, 2.0, -2.0, -4.4):
        G.seam(d, [(t - 0.4, zz * 0.12), (t - 3.4, zz)], M["ink"])
    G.stroke(d, fluke, M["ink"], O, cyclic=True)


def part_fin(d, M):
    """The long pectoral fin from its root (0, 0), sweeping down and back, knobbly cream leading edge."""
    fin = G.bezier((0.6, 0.3), (-2.0, -2.6), (-6.4, -4.4), n=12) + G.bezier((-6.4, -4.4), (-4.0, -2.2), (-0.8, -0.3), n=10)[1:]
    G.stroke(d, fin, M["fin"], O, cyclic=True)
    G.stroke(d, G.bezier((-6.4, -4.4), (-4.0, -2.2), (-0.8, -0.3), n=10) + [(-2.0, -1.8)], M["fin_sh"], 0.0, cyclic=True)
    for k, t in enumerate((0.2, 0.38, 0.56, 0.74)):                                                          # leading-edge knobs
        q = G.bezier((0.6, 0.3), (-2.0, -2.6), (-6.4, -4.4), n=12)[int(t * 11)]
        G.stroke(d, G.lumpy_ellipse(q[0] - 0.1, q[1] - 0.15, 0.32, 0.26, n=10, seed=70 + k), M["knob"], I, cyclic=True)
    G.seam(d, [(-0.6, -0.4), (-4.6, -3.4)], M["ink"])


def _head(d, M, squint=False):
    """The root: a blunt rounded head (neck joint x 0, snout ~ +12.5 m), one big pie eye, a long closed smile."""
    head = G.lumpy_ellipse(5.6, 0.0, 7.0, 4.8, n=60, lump=0.025, seed=5)
    head = [(x, z) for x, z in head if x > -0.8] + [(-0.8, 4.3), (-0.8, -4.2)]
    head.sort(key=lambda q: math.atan2(q[1], q[0] - 5.4))
    G.stroke(d, head, M["hide_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in head if q[1] > 3.6] + [(5.6, 3.6)], M["hide_sh"], 0.0, cyclic=True)
    G.stroke(d, [q for q in head if q[1] < -1.2] + [(12.0, -1.2), (0.0, -1.6)], M["belly_f"], 0.0, cyclic=True)   # the cream chin
    G.stroke(d, G.bezier((2.0, 2.3), (6.0, 2.7), (10.2, 2.2), n=10) + G.bezier((10.2, 1.4), (6.0, 1.9), (2.0, 1.6), n=10), M["band"], 0.0, cyclic=True)
    swirl_mark(d, M, 3.4, 0.4, 1.6, 7)
    G.stroke(d, G.bezier((5.4, -1.1), (9.4, -1.5), (12.4, -0.6), n=12), M["ink"], I)                         # the long closed smile
    G.seam(d, G.bezier((1.0, 3.2), (1.8, 0.4), (1.0, -2.8), n=8), M["ink"])                                   # a soft neck crease
    for k, (x, z) in enumerate(((7.4, 3.6), (8.8, 3.2), (6.2, 4.0))):                                           # cream knobs on the brow
        G.stroke(d, G.lumpy_ellipse(x, z, 0.28, 0.22, n=10, seed=40 + k), M["knob"], I, cyclic=True)
    G.hatch(d, 3.0, 2.8, M["ink"], n=4, length=0.7, spacing=0.25, angle_deg=70, seed=9)
    G.stroke(d, head, M["ink"], O, cyclic=True)
    if squint:                                                                                                  # harpooned: squeezed shut
        for dz in (0.0, -0.35):
            G.stroke(d, G.bezier((8.0, 0.9 + dz), (8.7, 1.25 + dz * 0.4), (9.4, 0.9 + dz), n=6), M["ink"], O)
    else:
        G.pie_eye(d, 8.7, 0.95, 0.75, 0.9, M["pupil"], M["eye"], look=(0.6, -0.1), seed=51, m_lid=M["ink"])     # one big friendly eye
    G.stroke(d, G.bezier((7.8, 2.2), (8.7, 2.5), (9.6, 2.2), n=6), M["ink"], I)                                  # a soft brow


def _throat(d, M, song=False):
    """The throat pouch under the head from (0, 0) forward; song: swollen, the pleats spread, rings ripple out (tones)."""
    k = 1.45 if song else 1.0
    pouch = G.bezier((0.0, 0.0), (3.0, -1.2 * k), (7.6, 0.2), n=12) + G.bezier((7.6, 0.2), (4.0, 0.7), (0.0, 0.6), n=10)[1:]
    if song:
        for r, mat in ((3.2, "ring"), (4.6, "ring2"), (6.0, "ring")):
            ring = G.lumpy_ellipse(4.0, -0.6, r * 1.3, r * 0.7, n=36, lump=0.02, seed=int(r * 10))
            inner = G.lumpy_ellipse(4.0, -0.6, r * 1.3 - 0.5, r * 0.7 - 0.3, n=36, lump=0.02, seed=int(r * 10) + 1)
            G.stroke(d, ring + inner[::-1], M[mat], 0.0, cyclic=True)
    G.stroke(d, pouch, M["belly_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in pouch if q[1] < -0.5 * k] + [(3.6, -0.5 * k)], M["belly_sh"], 0.0, cyclic=True)
    for j in range(4):                                                                                          # the pleats
        G.seam(d, G.bezier((0.6, 0.3 - 0.25 * j * k), (3.6, -0.35 * j * k), (7.0, 0.05 - 0.05 * j), n=8), M["ink"])
    G.stroke(d, pouch, M["ink"], O, cyclic=True)


PARTS = {"head": lambda d, M: _head(d, M), "head_squint": lambda d, M: _head(d, M, True), "body1": part_body1, "body2": part_body2,
         "tail": part_tail, "fin": part_fin, "throat_rest": lambda d, M: _throat(d, M), "throat_song": lambda d, M: _throat(d, M, True)}

RIG = {
    "name": "vortex_whale", "scale_note": "about 48 m long at 1x (the fiction's 500 m is a set piece seen in passing; needs LEAD's ruling)",
    "bones": [
        {"name": "head", "part": "head", "parent": None, "offset_m": [0.0, 0.0], "order": 3},
        {"name": "body1", "part": "body1", "parent": "head", "offset_m": [0.0, 0.0], "order": 2},
        {"name": "body2", "part": "body2", "parent": "body1", "offset_m": [-14.0, 0.0], "order": 1},
        {"name": "tail", "part": "tail", "parent": "body2", "offset_m": [-12.0, 0.0], "order": 0},
        {"name": "fin", "part": "fin", "parent": "body1", "offset_m": [-3.0, -2.6], "order": 5},
        {"name": "throat", "part": "throat_rest", "parent": "head", "offset_m": [4.4, -2.6], "order": 4},
    ],
    "swaps": {"throat": ["throat_rest", "throat_song"], "head": ["head", "head_squint"]},
    "slots": [{"slot": "throat", "bone": "throat", "offset_m": [0.0, 0.0], "order": 4, "replaces_part": True},
              {"slot": "head", "bone": "head", "offset_m": [0.0, 0.0], "order": 3, "replaces_part": True}],
    "idle": {"type": "sway", "beat_bpm": 110, "cycle_beats": 4, "amplitude_deg": {"head": 1.5, "body1": 3, "body2": 5, "tail": 8, "fin": 10},
             "lag": 0.8},
    "react": {"radius_m": 24.0, "action": "turn", "head_deg": 6},
    "actions": {"song": {"beats": 4, "swap": {"throat": "throat_song"}, "head_deg": 3},
                "harpooned": {"swap": {"head": "head_squint"}, "tail_deg": 14, "head_deg": -4}},
}


def pose_idle(i, n=8):
    ph = TAU * i / n
    return {"head": 1.5 * math.sin(ph + 0.5), "body1": 3 * math.sin(ph), "body2": 5 * math.sin(ph - 0.8), "tail": 8 * math.sin(ph - 1.6),
            "fin": 10 * math.sin(ph - 1.0), "throat": 0.0}, {}


def pose_song(i):
    sw = "throat_song" if 1 <= i <= 6 else "throat_rest"
    return {"head": 3 * math.sin(math.pi * i / 7), "body1": -1, "body2": 1, "tail": 2 * math.sin(i), "fin": 4, "throat": 0.0}, {"throat": sw}


def pose_react(i):
    h = 6 * math.sin(math.pi * min(i, 6) / 6)
    return {"head": h, "body1": -h * 0.4, "body2": -h * 0.3, "tail": -h * 0.5 + 2 * math.sin(i), "fin": 6 * math.sin(i), "throat": 0.0}, {}


def pose_harpooned(i):
    k = (0.0, 0.6, 1.0, 1.0, 0.8, 0.5, 0.25, 0.0)[i]
    return {"head": -4 * k, "body1": 1.5 * k, "body2": 3 * k, "tail": 14 * k, "fin": -8 * k, "throat": 0.0}, ({"head": "head_squint"} if k > 0.4 else {})


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
        part = swaps.get(b["name"], b["part"])
        PARTS[part](G.Xf(d, xf[b["name"]]), M)


SPAN_W, SPAN_H, PIV = 52.0, 16.0, (36.5 / 52.0, 7.6 / 16.0)     # the frame (m) and the head joint inside it


def render_pose(rot_deg, swaps, scale=0.25, ss=2, seed=3):
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    draw_pose(d, M, rot_deg, swaps)
    W_, H_ = int(SPAN_W * 64 * scale), int(SPAN_H * 64 * scale)
    W_ += (-W_) % 4
    H_ += (-H_) % 4
    return GR.render_frame(fakegp.strokes_of(d, gp, as_object=("vortex_whale", "art")), W_, H_, 64 * scale, PIV, ss=ss, seed=seed)


SRC = os.path.join(os.path.dirname(HERE), "sources", "creatures")


def build(out=os.path.join(SRC, "jupiter_vortex_whale_rigset.blend")):
    """Blender (the Jupiter card): one GP object per part around its pivot (the bone origin), the rig on scene["rig_plants"]."""
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
    """render.py review_script (the Jupiter export): the assembled whale and its loops, stamped. Inside Blender gp_draw is
    real: fakegp's mat goes in for the fake drawings and is restored after (the Hadal Maw's manner)."""
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
    gp = fakegp.FakeGP()                                                       # ink + palette measured at 1x on the head alone
    M = mats(gp)                                                               # (below ~0.5x the raster clamps every line to >= 1 px)
    d = fakegp.FakeDrawing()
    PARTS["head"](d, M)
    head1x, widths = GR.render_frame(fakegp.strokes_of(d, gp, as_object=("vortex_whale", "art")), 960, 704, 64, (0.08, 0.5), ss=2, seed=3)
    W = img.shape[1] + 200
    rows = []
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "b-155 vortex whale (jupiter apex, d-087 friendly-neutral, no teeth): a 3.11 rig set, 6 bones (head, body1, body2, tail, fin, "
                        "throat), swaps throat rest / song, head / squint; design preview", 6, 8)
    rows.append(head)
    sky = np.empty((img.shape[0] + 40, W, 3), np.float32)
    t = (np.arange(sky.shape[0]) / sky.shape[0])[:, None, None]
    sky[:] = (np.array(v3.hex_rgb(P["sky"]), np.float32) / 255) * (1 - 0.25 * t) + (np.array(v3.hex_rgb(P["red"]), np.float32) / 255) * 0.25 * t
    review._over(sky, img, 10, 30)
    try:
        fr, piv = PR.surveyor_frame()
        k = max(1, int(round(1 / scale)))
        fr = fr[::k, ::k]
        review._over(sky, fr, img.shape[1] + 40, sky.shape[0] - fr.shape[0] - 30)
    except Exception:  # noqa: BLE001
        pass
    review._label(sky, f"{scale:g}x in the red spot's haze beside the surveyor (2 m, also {scale:g}x): ~48 m long", 6, 6)
    rows.append(sky)
    for title, poses in (("idle 8 (a rolling glide: the sway travels down the bones, once per 4 beats; the fin rows)", [pose_idle(i) for i in range(8)]),
                         ("song 8 (the throat swells, rings ripple out as tones)", [pose_song(i) for i in range(8)]),
                         ("react 8 (a slow turn: the head lifts, the body follows)", [pose_react(i) for i in range(8)]),
                         ("harpooned 8 (a flinch: the eye squeezes shut, the flukes lift)", [pose_harpooned(i) for i in range(8)])):
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
    hits, off = v3.palette_hits(head1x, "jupiter")
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink at 1x outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; jupiter palette {hits * 100:.1f}% {off[:3]}; parts: {', '.join(PARTS)}", 6, 8)
    review._label(foot, "faces: one pie eye, a soft brow, a long closed smile; no teeth (d-087); the song's rings and the swirls are drawn tones", 6, 28)
    rows.append(foot)
    out = np.vstack(rows)
    review._label(out, __import__("time").strftime("%m-%d %H:%M") + " " + stamp, 2, out.shape[0] - 16)
    path = path or os.path.join(out_dir, "review_b155_vortex_whale_preview.png")
    review.write(path, out)
    print("written", path, f"{scale:g}x frame {img.shape[1]}x{img.shape[0]}", f"| palette {hits * 100:.1f}% {off[:3]}")


if __name__ == "__main__":
    preview(sys.argv[1])
