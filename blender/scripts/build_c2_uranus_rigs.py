"""B-158 (C2 Uranus, the rig-set sources): the five Uranus flora (build_c2_uranus_plants) cut into contract §11.3 rig parts +
bones in the other planets' rig sets' manner: one flora/uranus/rigset, <= 6 bones per plant, swaps, slots, an idle on the
beat, a react within 3 m, biomes per plant. Parts at the plants' 1.6x. No faces (D-101). Nothing exports until Uranus's
card; build() makes the Blender source then. The flora take UNITY's season tint (D-142), not three drawings.

  sunturner  2 bones  stalk -> head (left / up / right / shut: the head faces the sun - UNITY picks left / right by the
                      season; the idle nods up / left on the beat; react shuts)
  fogbell    4 bones  stalk -> bell0 -> bell1 -> bell2 (a chain: the bells swing out of phase; open / shut)
  hailcatch  2 bones  base -> bowl (hail 0-4 settling on the beat; react tips and spills)
  embermoss  1 bone   the cushion (glow low / high on the beat; react curls)
  prismfern  1 bone   the fern (rest / glint on the beat; react flat)

  python -I build_c2_uranus_rigs.py <preview dir>      dry run (lock-free): pack, validate, the assembled idle + react
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_uranus_plants as JPL  # noqa: E402  (gp_draw real in Blender, fakegp outside)

G = JPL.G
S = JPL.SCALE
mats = JPL.mats
SRC = os.path.join(os.path.dirname(HERE), "sources", "flora")


def scaled(fn):
    def part(d, M):
        fn(G.Xf(d, lambda pts: [(x * S, z * S) for x, z in pts]), M)
    return part


def shifted(fn, dx, dz):
    def part(d, M):
        fn(G.Xf(d, lambda pts: [(x + dx, z + dz) for x, z in pts]), M)
    return part


def off(x, z):
    return [round(x * S, 4), round(z * S, 4)]


RAW = {
    "sunturner_stalk": JPL.sunturner_stalk,
    "sunturner_head_left": lambda d, M: JPL.sunturner_head(d, M, -1.0),
    "sunturner_head_up": lambda d, M: JPL.sunturner_head(d, M, 0.0),
    "sunturner_head_right": lambda d, M: JPL.sunturner_head(d, M, 1.0),
    "sunturner_head_shut": lambda d, M: JPL.sunturner_head(d, M, 0.0, 1.0),
    "fogbell_stalk": JPL.fogbell_stalk,
    "fogbell_bell_open": lambda d, M: (G.stroke(d, [(0.0, 0.0), (0.0, -0.04)], M["ink"], JPL.I),
                                       JPL.fogbell_bell(G.Xf(d, lambda pts: [(x, z - 0.04) for x, z in pts]), M, 0.0, 0.3)),
    "fogbell_bell_shut": lambda d, M: (G.stroke(d, [(0.0, 0.0), (0.0, -0.04)], M["ink"], JPL.I),
                                       JPL.fogbell_bell(G.Xf(d, lambda pts: [(x, z - 0.04) for x, z in pts]), M, 1.0, 0.0)),
    "hailcatch_base": JPL.hailcatch_base,
    "hailcatch_bowl_tip": lambda d, M: JPL.hailcatch_bowl(d, M, 4, 1.0),
    "embermoss_lo": lambda d, M: JPL.embermoss(d, M, {"glow": 0.4}),
    "embermoss_hi": lambda d, M: JPL.embermoss(d, M, {"glow": 1.0}),
    "embermoss_curl": lambda d, M: JPL.embermoss(d, M, {"curl": 1.0, "glow": 0.25}),
    "prismfern_rest": lambda d, M: JPL.prismfern(d, M, {}),
    "prismfern_glint": lambda d, M: JPL.prismfern(d, M, {"glint": 2}),
    "prismfern_flat": lambda d, M: JPL.prismfern(d, M, {"flat": 1.0}),
}
for _h in range(5):
    RAW[f"hailcatch_bowl_h{_h}"] = (lambda h: (lambda d, M: JPL.hailcatch_bowl(d, M, h, 0.0)))(_h)
PARTS = {k: scaled(f) for k, f in RAW.items()}


def sway(amp, squash=0.0, cycle=None):
    i = {"type": "sway", "amplitude_deg": amp, "beat_bpm": 110, "squash": squash}
    if cycle:
        i["swap_cycle"] = cycle
    return i


_FB = [JPL.FB_ARCH[int(t * (len(JPL.FB_ARCH) - 1))] for t in JPL.FB_T]
SUNTURNER = {"name": "sunturner", "biomes": ["deck1", "deck2"],
             "bones": [{"name": "root", "part": "sunturner_stalk", "parent": None, "length": round(0.62 * S, 4), "order": 0},
                       {"name": "head", "part": "sunturner_head_up", "parent": "root", "length": round(0.18 * S, 4), "offset_m": off(0.0, 0.62), "order": 1}],
             "swaps": {"head": ["sunturner_head_left", "sunturner_head_up", "sunturner_head_right", "sunturner_head_shut"]},
             "slots": [{"slot": "head", "bone": "head", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True}],
             "idle": sway(3, 0.02, {"slot": "head", "sequence": ["sunturner_head_up", "sunturner_head_left"], "beats": [2, 2]}),
             "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "sunturner_head_shut",
                       "note": "UNITY sets the head to sunturner_head_left / _right by the season (the sun's side)"}}
FOGBELL = {"name": "fogbell", "biomes": ["deck1", "deck2"],
           "bones": [{"name": "root", "part": "fogbell_stalk", "parent": None, "length": round(0.6 * S, 4), "order": 0}] + [
               {"name": f"bell{k}", "part": "fogbell_bell_open", "parent": "root" if k == 0 else f"bell{k - 1}", "length": round(0.17 * S, 4),
                "offset_m": off(*(_FB[0] if k == 0 else (_FB[k][0] - _FB[k - 1][0], _FB[k][1] - _FB[k - 1][1]))), "order": 1 + k}
               for k in range(3)],
           "swaps": {f"b{k}": ["fogbell_bell_open", "fogbell_bell_shut"] for k in range(3)},
           "slots": [{"slot": f"b{k}", "bone": f"bell{k}", "offset_m": [0.0, 0.0], "order": 1 + k, "replaces_part": True} for k in range(3)],
           "idle": sway(16, 0.0),
           "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "fogbell_bell_shut"}}
HAILCATCH = {"name": "hailcatch", "biomes": ["deck2"],
             "bones": [{"name": "root", "part": "hailcatch_base", "parent": None, "length": round(0.22 * S, 4), "order": 0},
                       {"name": "bowl", "part": "hailcatch_bowl_h2", "parent": "root", "length": round(0.18 * S, 4), "offset_m": off(0.0, 0.22), "order": 1}],
             "swaps": {"bowl": [f"hailcatch_bowl_h{h}" for h in range(5)] + ["hailcatch_bowl_tip"]},
             "slots": [{"slot": "bowl", "bone": "bowl", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True}],
             "idle": sway(3, 0.02, {"slot": "bowl", "sequence": [f"hailcatch_bowl_h{h}" for h in range(5)], "beats": [2, 2, 2, 2, 2]}),
             "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "hailcatch_bowl_tip"}}
EMBERMOSS = {"name": "embermoss", "biomes": ["dark_half"],
             "bones": [{"name": "root", "part": "embermoss_lo", "parent": None, "length": round(0.22 * S, 4), "order": 0}],
             "swaps": {"moss": ["embermoss_lo", "embermoss_hi", "embermoss_curl"]},
             "slots": [{"slot": "moss", "bone": "root", "offset_m": [0.0, 0.0], "order": 0, "replaces_part": True}],
             "idle": sway(1, 0.02, {"slot": "moss", "sequence": ["embermoss_lo", "embermoss_hi"], "beats": [2, 2]}),
             "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "embermoss_curl"}}
PRISMFERN = {"name": "prismfern", "biomes": ["deck3", "deep"],
             "bones": [{"name": "root", "part": "prismfern_rest", "parent": None, "length": round(0.56 * S, 4), "order": 0}],
             "swaps": {"fern": ["prismfern_rest", "prismfern_glint", "prismfern_flat"]},
             "slots": [{"slot": "fern", "bone": "root", "offset_m": [0.0, 0.0], "order": 0, "replaces_part": True}],
             "idle": sway(3, 0.02, {"slot": "fern", "sequence": ["prismfern_rest", "prismfern_glint"], "beats": [3, 1]}),
             "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "prismfern_flat"}}
PLANTS = [SUNTURNER, FOGBELL, HAILCATCH, EMBERMOSS, PRISMFERN]


def build(out=os.path.join(SRC, "uranus_rigset_c2.blend")):
    """Blender (the Uranus card): one GP object per part around its pivot, the plants on scene["rig_plants"]."""
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
        x0, x1 = min(allp[:, 0].min(), 0.0) - rmax, max(allp[:, 0].max(), 0.0) + rmax       # the bone origin always inside
        z0, z1 = min(allp[:, 1].min(), 0.0) - rmax, max(allp[:, 1].max(), 0.0) + rmax
        w_ = -(-(int(np.ceil((x1 - x0) * 64)) + 2 * pad) // 4) * 4
        h_ = -(-(int(np.ceil((z1 - z0) * 64)) + 2 * pad) // 4) * 4
        pv = ((0 - x0) * 64 + pad) / w_, ((0 - z0) * 64 + pad) / h_
        img, _w = GR.render_frame(st, w_, h_, 64, pv, ss=4, seed=1)
        imgs.append(img)
        pivs.append(pv)
        names.append(name)
    pos, SW, SH_ = v3.shelf_pack([(im.shape[1], im.shape[0]) for im in imgs])
    sheet = np.zeros((SH_, SW, 4), np.uint8)
    parts = []
    for name, im, (px_, ytop), pv in zip(names, imgs, pos, pivs):
        h_, w_ = im.shape[:2]
        sheet[ytop:ytop + h_, px_:px_ + w_] = im
        parts.append({"name": name, "rect": [px_, SH_ - (ytop + h_), w_, h_], "pivot": [round(pv[0], 4), round(pv[1], 4)]})
    meta = {"key": "flora/uranus/rigset", "style": "v3", "ppu": 64, "rect_origin": "bottom_left", "parts": parts, "plants": PLANTS}
    return sheet, meta, v3.validate_rigset(meta, sheet.shape)


def plant_rows(W):
    """Per plant: the first 6 idle frames with Unity's maths and its react, on a zone-tan panel."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    from meridian import v3
    rows = []
    fw, fh, piv = 200, 200, (0.5, 0.06)
    for plant in PLANTS:
        nfr = PR.idle_frames(plant)
        r = np.tile(np.array(v3.hex_rgb(JPL.P["sky"]), np.float32) / 255, (fh + 28, W, 1))
        r[:22] = review.PAPER
        frames = [PR.render_plant(plant, PARTS, mats, PR.unity_tracks(plant, k / 12.0), PR.cycle_state(plant, k / 12.0), fw, fh, piv)[0]
                  for k in range(min(nfr, 6))]
        frames.append(PR.render_plant(plant, PARTS, mats, {}, PR.react_state(plant), fw, fh, piv)[0])
        for j, im in enumerate(frames):
            review._over(r, im, 8 + j * (fw + 6), 24)
        review._label(r, f"{plant['name']}: {len(plant['bones'])} bones, idle (unity's maths, {nfr} frames on {plant['idle']['beat_bpm']} bpm; first 6) | react; "
                         f"biomes {', '.join(plant['biomes'])}", 6, 4)
        rows.append(r)
    return rows


def dry_run(out_dir):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import pngio, v3
    sheet, meta, problems = pack_all()
    d = os.path.join(out_dir, "b158_rigset")
    os.makedirs(d, exist_ok=True)
    n = pngio.write_png(os.path.join(d, "rigset_color.png"), sheet)
    with open(os.path.join(d, "rigset.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
    hits, off_ = v3.palette_hits(sheet, "uranus")
    W = 1900
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"b-158 flora/uranus/rigset dry run: {len(meta['parts'])} parts on {sheet.shape[1]}x{sheet.shape[0]} ({n // 1024} kb), "
                        f"{len(PLANTS)} plants, json {'valid' if not problems else 'INVALID ' + '; '.join(problems)[:80]}, uranus palette {hits * 100:.1f}%", 6, 8)
    sh = np.tile(np.array([0.36, 0.30, 0.28], np.float32), (sheet.shape[0] + 10, W, 1))
    review._over(sh, sheet, 8, 5)
    img = np.vstack([head, sh] + plant_rows(W))
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " dry run (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b158_uranus_rigset_dryrun.png")
    review.write(out, img)
    print("written", out, f"| sheet {sheet.shape[1]}x{sheet.shape[0]} {n // 1024} KB, {len(meta['parts'])} parts,",
          "bones", {p["name"]: len(p["bones"]) for p in PLANTS}, "| problems", problems or "-", f"| palette {hits * 100:.1f}% {off_[:3]}")


def main(out):
    """render.py review_script (a future flora/uranus/rigset row): the plants assembled with Unity's maths."""
    import numpy as np
    from meridian import fakegp
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    W = 1900
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"flora/uranus/rigset assembled: {len(PLANTS)} plants, idle (unity's maths) | react", 6, 8)
    fakegp.install()
    try:
        img = np.vstack([head] + plant_rows(W))
    finally:
        fakegp.restore()
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " export", 2, img.shape[0] - 16)
    review.write(out, img)
    return []


if __name__ == "__main__":
    dry_run(sys.argv[1])
