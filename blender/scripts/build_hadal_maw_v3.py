"""B-136 (D-119): the Hadal Maw, Earth's Grand creature (ex-apex, Bible §7.1: a 40 m trench ambusher that lights its lure),
as a contract §11.3 rig set: parts on one sheet + bones (6) instead of a frame sheet (one frame would be ~2200 px wide).
Friendly-neutral (D-087): one big pie eye, a wide closed smile; the jaw opens on a dark cavern with a tongue, never teeth.
The lure's glow and the flank dots are drawn tones (no emission, contract §11.1). Earth palette, v3.1 ink.

  bones  head (root) -> body1 -> body2 -> tail; jaw (child of head, hinge); lure (child of head, forehead)
  swaps  lure: lure_lit / lure_dim / lure_flare
  idle   a travelling sway down the body (head 2, body1 4, body2 6, tail 9 deg, each later), the lure bobs and pulses
  react  the jaw opens to 24 deg and holds, the head lifts, the lure flares, then all settle (once)

Design preview (this file): the parts, the assembled creature at 1x beside the surveyor, the idle and react loops at 0.5x.

  python -I build_hadal_maw_v3.py <preview dir>      lock-free (meridian.fakegp)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp  # noqa: E402

try:
    import bpy
    if not hasattr(bpy, "data"):
        raise ImportError
    import gp_draw as G
except ImportError:
    G = fakegp.install()
import gp_raster as GR  # noqa: E402

P = G.PALETTES["earth"]
O, I = G.OUTER, G.INNER
SH, DP = G.shadow_of, G.deep_of
TAU = 2 * math.pi
BODY = DP(P["teal"])                     # the deep-water hide: teal's deep tone, its shadow the brown
BELLY = SH(P["sky"])


def mats(gp):
    def m(name, **kw):
        return G.mat(gp, "maw_" + name, **kw)
    return {
        "hide": m("hide", fill=BODY), "hide_f": m("hide_f", fill=BODY, ink=False), "hide_sh": m("hide_mid", fill=P["brown"], ink=False),
        "belly": m("belly", fill=BELLY), "belly_f": m("belly_f", fill=BELLY, ink=False), "belly_sh": m("belly_mid", fill=DP(P["sky"]), ink=False),
        "fin": m("fin", fill=SH(P["teal"])), "fin_sh": m("fin_mid", fill=DP(P["teal"]), ink=False),
        "dot": m("dot", fill=P["offwhite"], ink=False), "dot_y": m("dot_y", fill=P["mustard"], ink=False),
        "cavern": m("cavern", fill=P["brown"], ink=False), "tongue": m("tongue", fill=P["red"]), "tongue_sh": m("tongue_mid", fill=SH(P["red"]), ink=False),
        "lip": m("lip", fill=SH(P["sky"])),
        "bulb": m("bulb", fill=P["mustard"]), "bulb_dim": m("bulb_dim", fill=SH(P["mustard"])), "core": m("core", fill=P["offwhite"], ink=False),
        "halo": m("halo", fill=P["offwhite"], ink=False, fill_alpha=0.28), "halo2": m("halo2", fill=P["mustard"], ink=False, fill_alpha=0.22),
        "stalk": m("stalk", fill=SH(P["teal"]), behind=True),
        "eye": m("eye", fill=P["offwhite"]), "pupil": m("pupil", fill=G.INK, ink=False), "ink": m("ink", fill=None),
    }


def H(xg):
    """The body's half-height along the whole fish (x from the head joint 0 back to the tail base -22 m): one smooth
    taper, so the segments' silhouettes continue across every joint."""
    t = min(max(-xg / 22.0, 0.0), 1.0)
    return 0.75 + 2.1 * (0.5 + 0.5 * math.cos(math.pi * t ** 0.9))


def segment(d, M, length, g0, seed, dorsal=True, dots=True):
    """A body segment from its joint (local x 0, global g0) back `length` m; it reaches 0.6 m forward under the previous
    part so the joint never opens. Only the top and bottom edges are inked (no vertical joint lines)."""
    n = 22
    xs = [0.6 - (length + 0.6) * i / (n - 1) for i in range(n)]
    hh = [H(g0 + x) for x in xs]
    top = [(x, h * (1.0 + 0.025 * math.sin(i * 1.3 + seed))) for i, (x, h) in enumerate(zip(xs, hh))]
    bot = [(x, -h * 0.92) for x, h in zip(xs, hh)]
    shape = top + bot[::-1]
    if dorsal:                                                       # a soft scalloped dorsal ridge behind the body
        ridge = [(x, h + 0.35 + 0.18 * math.sin(i * 1.4 + seed)) for i, (x, h) in enumerate(zip(xs, hh))]
        G.stroke(d, ridge + top[::-1], M["fin"], 0.0, cyclic=True)
        G.stroke(d, ridge[1:-1], M["ink"], O)
        for i in range(2, n - 2, 3):
            G.seam(d, [(xs[i], hh[i] + 0.05), (xs[i] - 0.12, hh[i] + 0.38)], M["ink"])
    G.stroke(d, shape, M["hide_f"], 0.0, cyclic=True)
    G.stroke(d, top + [(x, h * 0.78) for x, h in zip(xs, hh)][::-1], M["hide_sh"], 0.0, cyclic=True)          # a thin back shadow
    G.stroke(d, [(x, -h * 0.25) for x, h in zip(xs, hh)] + bot[::-1], M["belly_f"], 0.0, cyclic=True)        # pale underside
    G.stroke(d, [(x, -h * 0.72) for x, h in zip(xs, hh)] + bot[::-1], M["belly_sh"], 0.0, cyclic=True)
    G.seam(d, [(x, -h * 0.25) for x, h in zip(xs, hh)][2:-1], M["ink"])
    for i in range(3, n - 2, 3):                                     # scale arcs
        x, h = xs[i], hh[i]
        G.seam(d, G.bezier((x, h * 0.55), (x - 0.45, h * 0.2), (x, -h * 0.15), n=6), M["ink"])
    if dots:                                                         # a row of drawn glow dots along the flank
        for i in range(1, n - 1, 2):
            G.stroke(d, G.lumpy_ellipse(xs[i], hh[i] * 0.1, 0.12, 0.10, n=10, seed=seed + i), M["dot_y" if i % 4 == 1 else "dot"], 0.0, cyclic=True)
    G.hatch(d, -length / 2, hh[n // 2] * 0.55, M["ink"], n=4, length=0.5, spacing=0.2, angle_deg=65, seed=seed)
    G.stroke(d, top[1:], M["ink"], O)                                # top and bottom edges only
    G.stroke(d, bot[1:], M["ink"], O)


def part_body1(d, M):
    segment(d, M, 9.0, 0.0, 11)
    fan = [(-1.2, -1.6)] + [(-1.2 - 2.4 * math.cos(a), -1.6 - 1.9 * math.sin(a)) for a in [0.2 + 0.2 * k for k in range(8)]]   # pectoral fan
    G.stroke(d, fan, M["fin"], O, cyclic=True)
    for k in range(1, 7, 2):
        a = 0.2 + 0.2 * k
        G.seam(d, [(-1.2, -1.6), (-1.2 - 2.2 * math.cos(a), -1.6 - 1.75 * math.sin(a))], M["ink"])


def part_body2(d, M):
    segment(d, M, 8.0, -9.0, 23)


def part_tail(d, M):
    segment(d, M, 5.0, -17.0, 37, dots=False)
    G.stroke(d, G.bezier((-5.0, 0.78), (-5.35, 0.0), (-5.0, -0.72), n=6), M["ink"], O)                # the peduncle's end
    t = (-5.0, 0.0)
    fin = [(t[0] + 0.4, 0.5), (t[0] - 2.2, 3.2), (t[0] - 3.4, 3.4), (t[0] - 2.4, 0.8), (t[0] - 2.0, 0.0), (t[0] - 2.4, -0.8),
           (t[0] - 3.4, -3.0), (t[0] - 2.2, -2.9), (t[0] + 0.4, -0.5)]
    G.stroke(d, fin, M["fin"], O, cyclic=True)
    G.stroke(d, [(t[0] + 0.4, -0.5), (t[0] - 2.2, -2.9), (t[0] - 3.4, -3.0), (t[0] - 2.4, -0.8), (t[0] - 2.0, 0.0)], M["fin_sh"], 0.0, cyclic=True)
    for zz in (2.6, 1.4, -1.4, -2.4):
        G.seam(d, [(t[0] - 0.2, zz * 0.15), (t[0] - 2.6, zz)], M["ink"])


def part_head(d, M):
    """The root: a bulbous head (neck joint at x 0, snout at ~ +8 m); the mouth cavern sits under the jaw."""
    head = G.lumpy_ellipse(3.6, 0.2, 4.4, 3.2, n=56, lump=0.03, seed=5)
    head = [(x, z) for x, z in head if x > -0.6] + [(-0.6, 2.6), (-0.6, -2.5)]
    head.sort(key=lambda q: math.atan2(q[1] - 0.2, q[0] - 3.4))
    G.stroke(d, G.bezier((3.4, -1.0), (6.0, -0.9), (7.6, -0.7), n=10) + G.bezier((7.6, -0.7), (6.6, -2.1), (3.6, -2.0), n=10), M["cavern"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(5.6, -1.6, 1.0, 0.32, n=18, seed=7), M["tongue"], I, cyclic=True)            # the tongue, inside
    G.stroke(d, head, M["hide_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in head if q[1] > 2.5] + [(3.6, 2.5)], M["hide_sh"], 0.0, cyclic=True)
    G.stroke(d, G.bezier((3.2, -1.0), (6.0, -0.85), (7.95, -0.6), n=10) + [(7.6, -1.4), (3.4, -1.6)], M["belly_f"], 0.0, cyclic=True)   # pale upper lip area
    G.stroke(d, G.bezier((3.2, -1.0), (6.0, -0.85), (7.95, -0.6), n=10), M["ink"], I)                       # the closed smile line
    G.seam(d, G.bezier((0.6, 2.2), (1.2, 0.2), (0.5, -1.9), n=8), M["ink"])                                  # gill arc
    G.seam(d, G.bezier((1.1, 1.8), (1.6, 0.2), (1.0, -1.5), n=8), M["ink"])
    for k, (x, z) in enumerate(((2.4, 2.4), (3.6, 2.9), (4.9, 2.7), (2.8, -0.3), (4.4, -0.2))):
        G.stroke(d, G.lumpy_ellipse(x, z, 0.12, 0.1, n=10, seed=40 + k), M["dot"], 0.0, cyclic=True)
    G.hatch(d, 2.2, 1.4, M["ink"], n=4, length=0.6, spacing=0.2, angle_deg=70, seed=9)
    G.stroke(d, head, M["ink"], O, cyclic=True)
    G.pie_eye(d, 5.7, 1.1, 0.55, 0.68, M["pupil"], M["eye"], look=(0.6, -0.1), seed=51, m_lid=M["ink"])     # one big friendly eye
    G.stroke(d, G.bezier((5.0, 2.0), (5.7, 2.25), (6.4, 2.0), n=6), M["ink"], I)                             # a soft brow, not a frown


def part_jaw(d, M):
    """The lower jaw from its hinge (0, 0) forward: a lip crescent; it rotates down (bone) to show the cavern. No teeth."""
    jaw = G.bezier((0.0, 0.0), (2.6, 0.15), (4.6, 0.35), n=10) + G.bezier((4.6, 0.35), (4.4, -1.6), (1.2, -1.7), n=12) + [(0.0, -0.9)]
    G.stroke(d, jaw, M["belly_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in jaw if q[1] < -0.8] + [(1.0, -0.8)], M["belly_sh"], 0.0, cyclic=True)
    G.stroke(d, G.bezier((0.2, -0.05), (2.6, 0.08), (4.6, 0.32), n=10) + G.bezier((4.6, 0.32), (2.6, -0.1), (0.2, -0.25), n=8), M["lip"], 0.0, cyclic=True)
    for k in range(3):
        G.seam(d, [(1.2 + 1.0 * k, -0.5), (1.4 + 1.0 * k, -1.0)], M["ink"])
    G.stroke(d, jaw, M["ink"], O, cyclic=True)


def _lure(d, M, lit, flare=False):
    stalk = G.bezier((0.0, 0.0), (0.6, 2.4), (2.8, 2.6), n=12)
    G.stroke(d, G.hose_outline(stalk, 0.16), M["stalk"], O, cyclic=True)
    G.ribs(d, stalk[1:-1], 0.16, M["ink"], every=0.45, frac=0.7)
    bx, bz = 3.1, 2.3
    if lit:
        k = 1.35 if flare else 1.0
        G.stroke(d, G.lumpy_ellipse(bx, bz, 1.05 * k, 1.0 * k, n=28, lump=0.03, seed=61), M["halo"], 0.0, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(bx, bz, 0.65 * k, 0.62 * k, n=24, lump=0.03, seed=62), M["halo2"], 0.0, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(bx, bz, 0.36, 0.40, n=20, lump=0.04, seed=63), M["bulb"] if lit else M["bulb_dim"], O, cyclic=True)
    if lit:
        G.stroke(d, G.lumpy_ellipse(bx - 0.08, bz + 0.08, 0.14, 0.15, n=12, seed=64), M["core"], 0.0, cyclic=True)
    G.seam(d, [(bx - 0.2, bz - 0.25), (bx + 0.15, bz - 0.3)], M["ink"])


PARTS = {"head": part_head, "jaw": part_jaw, "body1": part_body1, "body2": part_body2, "tail": part_tail,
         "lure_lit": lambda d, M: _lure(d, M, True), "lure_dim": lambda d, M: _lure(d, M, False),
         "lure_flare": lambda d, M: _lure(d, M, True, True)}

RIG = {
    "name": "hadal_maw", "grand": True, "scale_note": "about 34 m long at 1x (Bible 40 m: a set piece over two screens)",
    "bones": [
        {"name": "head", "part": "head", "parent": None, "offset_m": [0.0, 0.0], "order": 3},
        {"name": "body1", "part": "body1", "parent": "head", "offset_m": [0.0, 0.0], "order": 2},
        {"name": "body2", "part": "body2", "parent": "body1", "offset_m": [-9.0, 0.0], "order": 1},
        {"name": "tail", "part": "tail", "parent": "body2", "offset_m": [-8.0, 0.0], "order": 0},
        {"name": "jaw", "part": "jaw", "parent": "head", "offset_m": [3.3, -1.0], "order": 4},
        {"name": "lure", "part": "lure_lit", "parent": "head", "offset_m": [6.0, 2.6], "order": 5},
    ],
    "swaps": {"lure": ["lure_lit", "lure_dim", "lure_flare"]},
    "slots": [{"slot": "lure", "bone": "lure", "offset_m": [0.0, 0.0], "order": 5, "replaces_part": True}],
    # Bible §9.2 beats are 100-120 bpm (validate_rigset): the giant sways once per 4 beats at 110 bpm (2.18 s, the accepted
    # design's slow 2 s sway); cycle_beats is new for U-119 (plants sway once per 2 beats).
    "idle": {"type": "sway", "beat_bpm": 110, "cycle_beats": 4, "amplitude_deg": {"head": 2, "body1": 4, "body2": 6, "tail": 9, "lure": 8},
             "lag": 0.8, "swap_cycle": {"slot": "lure", "sequence": ["lure_lit", "lure_dim"], "beats": [6, 2]}},
    "react": {"radius_m": 12.0, "action": "jaw_open", "jaw_deg": -24, "head_deg": 4, "swap": {"lure": "lure_flare"}},
}


def pose_idle(i, n=8):
    ph = TAU * i / n
    return {"head": 2 * math.sin(ph + 0.5), "body1": 4 * math.sin(ph), "body2": 6 * math.sin(ph - 0.8), "tail": 9 * math.sin(ph - 1.6),
            "jaw": 0.0, "lure": 8 * math.sin(ph - 1.0)}, {"lure": "lure_lit" if i % 8 < 6 else "lure_dim"}


REACT = [(0, 0, "lure_lit"), (-8, 1, "lure_lit"), (-18, 3, "lure_flare"), (-24, 4, "lure_flare"), (-24, 4, "lure_flare"), (-22, 3, "lure_flare"),
         (-12, 2, "lure_lit"), (-3, 0.5, "lure_lit")]


def pose_react(i):
    jaw, head, lure = REACT[i]
    return {"head": head, "body1": -head * 0.5, "body2": -head * 0.4, "tail": 3 * math.sin(i), "jaw": jaw, "lure": -6 + 2 * i}, {"lure": lure}


def world_xf(rot_deg):
    """Bone world transforms (2D affine: rotate about the bone origin, then the parent's)."""
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


def render_pose(rot_deg, swaps, scale=1.0, ss=1, seed=3):
    gp = fakegp.FakeGP()
    M = mats(gp)
    d = fakegp.FakeDrawing()
    draw_pose(d, M, rot_deg, swaps)
    W_, H_ = int(39.0 * 64 * scale), int(11.0 * 64 * scale)
    W_ += (-W_) % 4
    H_ += (-H_) % 4
    piv = (27.5 / 39.0, 4.6 / 11.0)                 # the head's joint: 27.5 m from the left (the tail fin), 4.6 m up
    return GR.render_frame(fakegp.strokes_of(d, gp, as_object=("hadal_maw", "art")), W_, H_, 64 * scale, piv, ss=ss, seed=seed)


SRC = os.path.join(os.path.dirname(HERE), "sources", "creatures")


def build(out=os.path.join(SRC, "earth_hadal_maw_rigset.blend")):
    """Blender (B-136 export): one GP object per part around its pivot (the bone origin), the rig on scene["rig_plants"]
    (render.py's do_v3_rigset packs the parts and writes the json's plants from it)."""
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
    """render.py review_script (B-136 accept): the assembled creature at 1x beside the surveyor (1x), the loops, stamped.
    Inside Blender gp_draw is real: fakegp's mat goes in for the fake drawings and is restored after (a later job in the
    same batch gets the real one back)."""
    fakegp.install()
    try:
        preview(os.path.dirname(out), scale=1.0, path=out, stamp="export")
    finally:
        fakegp.restore()
    return []


def preview(out_dir, scale=0.5, path=None, stamp="preview (not exported)"):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    from meridian import v3
    img, widths = render_pose(*pose_idle(0), scale=scale, ss=2)    # 0.5x for the lock-free design look; 1x (ss 2) in the export slot
    widths = [(a / scale, b / scale, c / scale) for a, b, c in widths]   # reported at 1x
    W = img.shape[1] + 260
    rows = []
    head = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(head, "b-136 hadal maw (grand creature, d-087 friendly-neutral, no teeth): a 3.11 rig set, 6 bones (head, body1, body2, tail, jaw, lure), "
                        f"lure swaps lit / dim / flare; {'the exported rig set' if stamp == 'export' else 'design preview'}", 6, 8)
    rows.append(head)
    deep = np.empty((img.shape[0] + 40, W, 3), np.float32)
    t = (np.arange(deep.shape[0]) / deep.shape[0])[:, None, None]
    deep[:] = (np.array(v3.hex_rgb(G.deep_of(P["teal"])), np.float32) / 255) * (1 - 0.45 * t)          # trench water, darker below
    review._over(deep, img, 10, 30)
    try:
        fr, piv = PR.surveyor_frame()
        fr = fr[::2, ::2] if scale == 0.5 else fr
        review._over(deep, fr, img.shape[1] + 40, deep.shape[0] - fr.shape[0] - 30)
    except Exception:  # noqa: BLE001
        pass
    review._label(deep, f"{scale:g}x in trench water beside the surveyor (2 m, also {scale:g}x): ~34 m long, over two screens wide at 1x", 6, 6)
    rows.append(deep)
    for title, poses in (("idle 8 (a sway travelling down the bones, once per 4 beats at 110 bpm; the lure bobs, dims on 6-7)", [pose_idle(i) for i in range(8)]),
                         ("react 8 (the jaw opens to 24 deg on a cavern + tongue, the head lifts, the lure flares, settle)", [pose_react(i) for i in range(8)])):
        frames = [render_pose(r, s, scale=0.25, ss=2, seed=9 + k)[0] for k, (r, s) in enumerate(poses)]
        fw, fh = frames[0].shape[1], frames[0].shape[0]
        per = max(1, (W - 16) // (fw + 8))
        for r0 in range(0, len(frames), per):
            row = np.tile(review.PAPER, (fh + 26, W, 1)).astype(np.float32)
            row[22:, :] = np.array(v3.hex_rgb(G.deep_of(P["teal"])), np.float32) / 255
            for j, im in enumerate(frames[r0:r0 + per]):
                review._over(row, im, 8 + j * (fw + 8), 22)
            review._label(row, f"{title} at 0.25x" if r0 == 0 else "", 6, 2)
            rows.append(row)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"ink at 1x outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; parts: {', '.join(PARTS)}; one sheet at export (parts at 1x pack ~1750 x 800)", 6, 8)
    review._label(foot, "faces: one pie eye, a soft brow, a closed smile; open jaw = a dark cavern with a tongue, no teeth (d-087); glow = drawn tones", 6, 28)
    rows.append(foot)
    out = np.vstack(rows)
    review._label(out, __import__("time").strftime("%m-%d %H:%M") + " " + stamp, 2, out.shape[0] - 16)
    path = path or os.path.join(out_dir, "review_b136_hadal_maw_preview.png")
    review.write(path, out)
    print("written", path, f"1x frame {img.shape[1]}x{img.shape[0]}")


if __name__ == "__main__":
    preview(sys.argv[1])
