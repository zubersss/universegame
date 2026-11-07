"""B-139 (C2 Mars, sources for the rig set; LEAD cycle 255): the five accepted Mars plant designs (build_c2_mars_plants)
cut into contract §11.3 rig parts + bones in the Earth rig set's manner (build_c2_earth_rigs): one flora/mars/rigset,
<= 6 bones per plant, swaps, slots, an idle on the beat, a react within 3 m, biomes per plant. Parts are drawn at the
accepted 1.5x (Mars' 0.38 g), bone offsets with them. No faces (D-101). Nothing exports until the Mars cards exist;
build() makes the Blender source when they do.

  rustbell       3 bones  stem_lower -> stem_upper -> bell (bell_open / bell_shut)
  puffpod        2 bones  neck -> pod (pod / pod_big / pod_flat with its dust puff)
  frostcurl      4 bones  crown -> fronds l, c, r (open / curled)
  pipereed       4 bones  mound -> pipes a, b, c (rest / squash)
  scree_creeper  2 bones  rock + vine -> pads (pads_a / pads_b / pads_flat)

  python -I build_c2_mars_rigs.py <preview dir>      dry run (lock-free): pack, validate, assembled idle + react loops
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_mars_plants as MPL  # noqa: E402  (gp_draw real in Blender, fakegp outside)

G = MPL.G
O, I = MPL.O, MPL.I
S = MPL.MARS_SCALE
mats, hose_stem, leaf, rot = MPL.mats, MPL.hose_stem, MPL.leaf, MPL.rot
SRC = os.path.join(os.path.dirname(HERE), "sources", "flora")


def scaled(fn):
    """A part drawn at the Mars scale about its own pivot (the origin)."""
    def part(d, M):
        fn(G.Xf(d, lambda pts: [(x * S, z * S) for x, z in pts]), M)
    return part


def off(x, z):
    return [round(x * S, 4), round(z * S, 4)]


# ---------------------------------------------------------------- rustbell
def rb_stem_lower(d, M):
    leaf(d, M, (0.0, 0.14), math.radians(155), 0.30, 0.07)
    leaf(d, M, (0.0, 0.30), math.radians(28), 0.28, 0.065)
    hose_stem(d, M, G.bezier((0.0, 0.0), (-0.01, 0.22), (-0.01, 0.47), n=8), 0.06, rib_every=0.16)


def rb_stem_upper(d, M):                       # pivot = world (-0.01, 0.45); the bell hangs at local (0.31, 0.41)
    hose_stem(d, M, G.bezier((0.0, -0.03), (0.03, 0.25), (0.11, 0.35), n=8) + G.bezier((0.11, 0.35), (0.21, 0.53), (0.31, 0.41), n=6)[1:],
              0.06, rib_every=0.16)


def rb_bell(shut):
    def fn(d, M):
        swing = math.radians(-12 + 70 * shut)
        bell = G.bezier((-0.10, 0.0), (-0.13, -0.15), (-0.17, -0.24), n=8) + [(-0.10, -0.28), (0.0, -0.25), (0.10, -0.28)] + \
            G.bezier((0.17, -0.24), (0.13, -0.15), (0.10, 0.0), n=8)
        B = [(x, z - 0.02) for x, z in rot(bell, swing)]
        G.stroke(d, [(0.0, 0.02), (0.0, -0.04)], M["ink"], I)
        G.stroke(d, B, M["rust_f"], 0.0, cyclic=True)
        G.stroke(d, [q for q in B if q[0] < -0.03] + [(-0.03, -0.20)], M["rust_sh"], 0.0, cyclic=True)
        lip = [(x, z - 0.02) for x, z in rot([(-0.17, -0.24), (-0.10, -0.28), (0.0, -0.25), (0.10, -0.28), (0.17, -0.24),
                                               (0.15, -0.20), (0.0, -0.21), (-0.15, -0.20)], swing)]
        G.stroke(d, lip, M["butter_f"], 0.0, cyclic=True)
        for x0 in (-0.06, 0.0, 0.06):
            G.seam(d, [(x, z - 0.02) for x, z in rot([(x0 * 0.5, -0.03), (x0, -0.19)], swing)], M["ink"])
        G.stroke(d, B, M["ink"], O, cyclic=True)
        if shut > 0.5:
            G.seam(d, [(x, z - 0.02) for x, z in rot([(-0.16, -0.22), (0.16, -0.22)], swing)], M["ink"])
    return fn


RUSTBELL = {
    "name": "rustbell", "biomes": ["plains", "canyon"],
    "bones": [
        {"name": "root", "part": "rustbell_stem_lower", "parent": None, "length": round(0.45 * S, 4), "order": 0},
        {"name": "stem2", "part": "rustbell_stem_upper", "parent": "root", "length": round(0.45 * S, 4), "offset_m": off(-0.01, 0.45), "order": 1},
        {"name": "bell", "part": "rustbell_bell_open", "parent": "stem2", "length": round(0.25 * S, 4), "offset_m": off(0.31, 0.41), "order": 2},
    ],
    "swaps": {"bell": ["rustbell_bell_open", "rustbell_bell_shut"]},
    "slots": [{"slot": "bell", "bone": "bell", "offset_m": [0.0, 0.0], "order": 2, "replaces_part": True}],
    "idle": {"type": "sway", "amplitude_deg": 12, "beat_bpm": 110, "squash": 0.03},
    "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "rustbell_bell_shut"},
}


# ---------------------------------------------------------------- puffpod
def pp_neck(d, M):
    leaf(d, M, (0.0, 0.05), math.radians(165), 0.20, 0.06, veins=1)
    leaf(d, M, (0.0, 0.07), math.radians(15), 0.18, 0.055, veins=1)
    hose_stem(d, M, G.bezier((0.0, 0.0), (0.02, 0.12), (0.0, 0.24), n=6), 0.07, rib_every=0.1)


def pp_pod(breathe, deflate, puff_t=None):
    def fn(d, M):                              # pivot = the neck top, world (0, 0.22)
        p = {"breathe": breathe, "react": deflate, "squash": 1.0, "sway": 0.0}
        if puff_t is not None:
            p["puff"] = puff_t
        MPL.puffpod_pod(d, M, p, base=0.0)
    return fn


PUFFPOD = {
    "name": "puffpod", "biomes": ["dunes", "plains"],
    "bones": [
        {"name": "root", "part": "puffpod_neck", "parent": None, "length": round(0.22 * S, 4), "order": 0},
        {"name": "pod", "part": "puffpod_pod", "parent": "root", "length": round(0.42 * S, 4), "offset_m": off(0.0, 0.22), "order": 1},
    ],
    "swaps": {"pod": ["puffpod_pod", "puffpod_pod_big", "puffpod_pod_flat"]},
    "slots": [{"slot": "pod", "bone": "pod", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True}],
    "idle": {"type": "sway", "amplitude_deg": 4, "beat_bpm": 110, "squash": 0.05,
             "swap_cycle": {"slot": "pod", "sequence": ["puffpod_pod", "puffpod_pod_big"], "beats": [1, 1]}},
    "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "puffpod_pod_flat"},
}


# ---------------------------------------------------------------- frostcurl
FC_LEAN = {"l": (118, 0.62), "c": (92, 0.80), "r": (64, 0.62)}
FC_BASE = {"l": -0.05, "c": 0.0, "r": 0.05}


def fc_crown(d, M):
    G.stroke(d, G.lumpy_ellipse(0.0, 0.03, 0.12, 0.05, n=18, seed=3), M["umber"], O, cyclic=True)
    G.specks(d, [(-0.05, 0.03), (0.04, 0.04)], M["ink"])


def fc_frond(side, curl):
    def fn(d, M):                              # pivot = the frond's base
        lean, L = FC_LEAN[side]
        MPL._frond(d, M, (0.0, 0.0), math.radians(lean), curl, L, 10 + "lcr".index(side))
    return fn


FROSTCURL = {
    "name": "frostcurl", "biomes": ["polar", "highlands"],
    "bones": [{"name": "root", "part": "frostcurl_crown", "parent": None, "length": round(0.05 * S, 4), "order": 0}] + [
        {"name": f"frond_{s}", "part": f"frostcurl_{s}_open", "parent": "root", "length": round(FC_LEAN[s][1] * S, 4),
         "offset_m": off(FC_BASE[s], 0.05), "order": 1 + k} for k, s in enumerate("lcr")],
    "swaps": {f"f{s}": [f"frostcurl_{s}_open", f"frostcurl_{s}_curled"] for s in "lcr"},
    "slots": [{"slot": f"f{s}", "bone": f"frond_{s}", "offset_m": [0.0, 0.0], "order": 1 + k, "replaces_part": True} for k, s in enumerate("lcr")],
    "idle": {"type": "sway", "amplitude_deg": 10, "beat_bpm": 110, "squash": 0.02,
             "swap_cycle": {"slot": "fc", "sequence": ["frostcurl_c_open", "frostcurl_c_curled"], "beats": [7, 1]}},
    "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "frostcurl_c_curled",
              "also": {"fl": "frostcurl_l_curled", "fr": "frostcurl_r_curled"}},
}


# ---------------------------------------------------------------- pipereed
PR_PIPES = {"a": (-0.11, 0.62, 0.09, 0.44), "b": (0.0, 0.92, 0.10, 0.62), "c": (0.11, 0.48, 0.08, 0.28)}


def pr_mound(d, M):
    G.stroke(d, G.lumpy_ellipse(0.0, 0.03, 0.16, 0.05, n=16, seed=5), M["umber"], O, cyclic=True)
    G.specks(d, [(-0.07, 0.03), (0.08, 0.04)], M["ink"])


def pr_pipe(name, sq):
    def fn(d, M):                              # pivot = the pipe's base centre
        _x, h, w, slit = PR_PIPES[name]
        MPL.pipe(d, M, 0.0, h * sq, w, slit, 20 + "abc".index(name), z0=0.0)
    return fn


PIPEREED = {
    "name": "pipereed", "biomes": ["canyon", "scree"],
    "bones": [{"name": "root", "part": "pipereed_mound", "parent": None, "length": round(0.04 * S, 4), "order": 0}] + [
        {"name": f"pipe_{n}", "part": f"pipereed_pipe_{n}", "parent": "root", "length": round(PR_PIPES[n][1] * S, 4),
         "offset_m": off(PR_PIPES[n][0], 0.04), "order": 1 + k} for k, n in enumerate("abc")],
    "swaps": {f"p{n}": [f"pipereed_pipe_{n}", f"pipereed_pipe_{n}_squash"] for n in "abc"},
    "slots": [{"slot": f"p{n}", "bone": f"pipe_{n}", "offset_m": [0.0, 0.0], "order": 1 + k, "replaces_part": True} for k, n in enumerate("abc")],
    "idle": {"type": "sway", "amplitude_deg": 8, "beat_bpm": 110, "squash": 0.03},
    "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "pipereed_pipe_b_squash",
              "also": {"pa": "pipereed_pipe_a_squash", "pc": "pipereed_pipe_c_squash"}},
}


# ---------------------------------------------------------------- scree creeper
def sc_rock(d, M):
    MPL.scree_rock_vine(d, M)


SC_PADS_AT = 0.30                          # the pads' pivot sits on the vine, inside the pad set (rig parts need it in their rect)


def sc_pads(phase, lift):
    def fn(d, M):
        MPL.scree_pads(G.Xf(d, lambda pts: [(x, z - SC_PADS_AT) for x, z in pts]), M, phase, lift)
    return fn


SCREE_CREEPER = {
    "name": "scree_creeper", "biomes": ["scree", "lava_tubes"],
    "bones": [
        {"name": "root", "part": "scree_creeper_rock", "parent": None, "length": round(0.36 * S, 4), "order": 0},
        {"name": "pads", "part": "scree_creeper_pads_a", "parent": "root", "length": round(0.1 * S, 4), "offset_m": off(0.0, SC_PADS_AT), "order": 1},
    ],
    "swaps": {"pads": ["scree_creeper_pads_a", "scree_creeper_pads_b", "scree_creeper_pads_flat"]},
    "slots": [{"slot": "pads", "bone": "pads", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True}],
    "idle": {"type": "sway", "amplitude_deg": 0, "beat_bpm": 110, "squash": 0.0,
             "swap_cycle": {"slot": "pads", "sequence": ["scree_creeper_pads_a", "scree_creeper_pads_b"], "beats": [1, 1]}},
    "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "scree_creeper_pads_flat"},
}


RAW = {
    "rustbell_stem_lower": rb_stem_lower, "rustbell_stem_upper": rb_stem_upper,
    "rustbell_bell_open": rb_bell(0.0), "rustbell_bell_shut": rb_bell(1.0),
    "puffpod_neck": pp_neck, "puffpod_pod": pp_pod(0.0, 0.0), "puffpod_pod_big": pp_pod(1.0, 0.0), "puffpod_pod_flat": pp_pod(0.0, 1.0, 0.7),
    "frostcurl_crown": fc_crown, "pipereed_mound": pr_mound, "scree_creeper_rock": sc_rock,
    "scree_creeper_pads_a": sc_pads(0.0, 0.0), "scree_creeper_pads_b": sc_pads(math.pi, 0.0), "scree_creeper_pads_flat": sc_pads(0.5, 1.0),
}
for _s in "lcr":
    RAW[f"frostcurl_{_s}_open"] = fc_frond(_s, 0.2)
    RAW[f"frostcurl_{_s}_curled"] = fc_frond(_s, 0.85)
for _n in "abc":
    RAW[f"pipereed_pipe_{_n}"] = pr_pipe(_n, 1.0)
    RAW[f"pipereed_pipe_{_n}_squash"] = pr_pipe(_n, 0.78)
PARTS = {k: scaled(f) for k, f in RAW.items()}
PLANTS = [RUSTBELL, PUFFPOD, FROSTCURL, PIPEREED, SCREE_CREEPER]


def build(out=os.path.join(SRC, "mars_rigset_c2.blend")):
    """Blender (when the Mars cards open): one GP object per part around its pivot, the plants on scene["rig_plants"]."""
    import bpy
    scene = G.new_scene()
    scene["rig_plants"] = json.dumps(PLANTS)
    coll = G.collection("parts")
    for name, fn in PARTS.items():
        ob, gp = G.gp_object("part_" + name, coll)
        layer = gp.layers.new("art")
        fn(G.drawing(layer, 1), mats(gp))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


def pack_all():
    """Every part packed as render.py's rig path does (exact ids: part_<name> / art), the json and its problems."""
    import numpy as np
    from meridian import fakegp, v3
    import gp_raster as GR
    imgs, pivs, names = [], [], []
    pad = 4
    for name, fn in PARTS.items():
        gp = fakegp.FakeGP()
        M = mats(gp)
        d = fakegp.FakeDrawing()
        fn(d, M)
        st = fakegp.strokes_of(d, gp, as_object=("part_" + name, "art"))
        allp = np.vstack([s_["xz"] for s_ in st])
        rmax = max(float(s_["radius"].max()) for s_ in st) * 1.25
        x0, x1 = allp[:, 0].min() - rmax, allp[:, 0].max() + rmax
        z0, z1 = allp[:, 1].min() - rmax, allp[:, 1].max() + rmax
        w_ = -(-(int(np.ceil((x1 - x0) * 64)) + 2 * pad) // 4) * 4
        h_ = -(-(int(np.ceil((z1 - z0) * 64)) + 2 * pad) // 4) * 4
        pv = ((0 - x0) * 64 + pad) / w_, ((0 - z0) * 64 + pad) / h_
        img, _w = GR.render_frame(st, w_, h_, 64, pv, ss=4, seed=1)
        imgs.append(img)
        pivs.append(pv)
        names.append(name)
    pos, SW, SH = v3.shelf_pack([(im.shape[1], im.shape[0]) for im in imgs])
    sheet = np.zeros((SH, SW, 4), np.uint8)
    parts = []
    for name, im, (px_, ytop), pv in zip(names, imgs, pos, pivs):
        h_, w_ = im.shape[:2]
        sheet[ytop:ytop + h_, px_:px_ + w_] = im
        parts.append({"name": name, "rect": [px_, SH - (ytop + h_), w_, h_], "pivot": [round(pv[0], 4), round(pv[1], 4)]})
    meta = {"key": "flora/mars/rigset", "style": "v3", "ppu": 64, "rect_origin": "bottom_left", "parts": parts, "plants": PLANTS}
    return sheet, meta, v3.validate_rigset(meta, sheet.shape)


def dry_run(out_dir):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    from meridian import pngio, v3
    sheet, meta, problems = pack_all()
    d = os.path.join(out_dir, "b139_rigset")
    os.makedirs(d, exist_ok=True)
    n = pngio.write_png(os.path.join(d, "rigset_color.png"), sheet)
    with open(os.path.join(d, "rigset.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
    hits, off_ = v3.palette_hits(sheet, "mars")
    W = 1900
    rows = []
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"b-139 flora/mars/rigset dry run: {len(meta['parts'])} parts on {sheet.shape[1]}x{sheet.shape[0]} ({n // 1024} kb), "
                        f"{len(PLANTS)} plants, json {'valid' if not problems else 'INVALID ' + '; '.join(problems)[:80]}, mars palette {hits * 100:.1f}%", 6, 8)
    rows.append(head)
    sh = np.tile(np.array([0.62, 0.72, 0.72], np.float32), (sheet.shape[0] + 10, W, 1))
    review._over(sh, sheet, 8, 5)
    rows.append(sh)
    rows += plant_rows(W)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " dry run (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b139_mars_rigset_dryrun.png")
    review.write(out, img)
    print("written", out, f"| sheet {sheet.shape[1]}x{sheet.shape[0]} {n // 1024} KB, {len(meta['parts'])} parts,",
          "bones", {p["name"]: len(p["bones"]) for p in PLANTS}, "| problems", problems or "-", f"| palette {hits * 100:.1f}% {off_[:3]}")


def plant_rows(W):
    """Per plant: the first 6 idle frames with Unity's maths (RigSetBuilder tracks + swap cycle) and its react."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    rows = []
    fw, fh, piv = 200, 200, (0.5, 0.06)
    for plant in PLANTS:
        nfr = PR.idle_frames(plant)
        r = np.tile(review.PAPER, (fh + 28, W, 1)).astype(np.float32)
        frames = [PR.render_plant(plant, PARTS, mats, PR.unity_tracks(plant, k / 12.0), PR.cycle_state(plant, k / 12.0), fw, fh, piv)[0]
                  for k in range(min(nfr, 6))]
        frames.append(PR.render_plant(plant, PARTS, mats, {}, PR.react_state(plant), fw, fh, piv)[0])
        for j, im in enumerate(frames):
            review._over(r, im, 8 + j * (fw + 6), 24)
        review._label(r, f"{plant['name']}: {len(plant['bones'])} bones, idle (unity's maths, {nfr} frames on {plant['idle']['beat_bpm']} bpm; first 6) | react; "
                         f"biomes {', '.join(plant['biomes'])}", 6, 4)
        rows.append(r)
    return rows


def main(out):
    """render.py review_script (B-140, flora/mars/rigset): every Mars plant assembled with Unity's maths at 1x."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    W = 1900
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"b-140 flora/mars/rigset assembled: {len(PLANTS)} plants, idle (unity's maths) | react, drawn 1.5x for 0.38 g", 6, 8)
    img = np.vstack([head] + plant_rows(W))
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " export", 2, img.shape[0] - 16)
    review.write(out, img)
    return []


if __name__ == "__main__":
    dry_run(sys.argv[1])
