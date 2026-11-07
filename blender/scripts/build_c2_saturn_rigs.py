"""B-157 (C2 Saturn, the rig-set sources): the five Saturn flora (build_c2_saturn_plants) cut into contract §11.3 rig parts +
bones in the Earth / Mars / Mercury / Venus / Jupiter rig sets' manner: one flora/saturn/rigset, <= 6 bones per plant, swaps,
slots, an idle on the beat, a react within 3 m, biomes per plant. Parts at the plants' 1.6x. No faces (D-101). Nothing
exports until Saturn's card; build() makes the Blender source then.

  ringreed    4 bones  tuft -> three reeds (each rest / tilt / drop: reed 1 tilts its ring on the beat; react drops all rings)
  heliumbell  2 bones  stem -> bell (rest / swell; react swells it - the rise on the stretched stem is UNITY's: the bell bone
                       lifts while the stem swaps to stem_long)
  frostfan    1 bone   the fan (open / mid / folded: it breathes open-mid on the beat; react folds it)
  hexmoss     1 bone   the cushion (six pulse states walk the cells on the beat; react hunkers)
  butterpuff  1 bone   the puffs (rest / spores: react)

  python -I build_c2_saturn_rigs.py <preview dir>      dry run (lock-free): pack, validate, the assembled idle + react
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_saturn_plants as JPL  # noqa: E402  (registers the proposed palette; gp_draw real in Blender, fakegp outside)

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
    "ringreed_tuft": JPL.ringreed_tuft,
    "heliumbell_stem": lambda d, M: JPL.heliumbell_stem(d, M, 1.0),
    "heliumbell_stem_long": lambda d, M: JPL.heliumbell_stem(d, M, 1.8),
    "heliumbell_bell": lambda d, M: JPL.heliumbell_bell(d, M, 0.0),
    "heliumbell_bell_swell": lambda d, M: JPL.heliumbell_bell(d, M, 1.0),
    "frostfan_open": lambda d, M: JPL.frostfan(d, M, {"open": 1.0}),
    "frostfan_mid": lambda d, M: JPL.frostfan(d, M, {"open": 0.7}),
    "frostfan_folded": lambda d, M: JPL.frostfan(d, M, {"open": 0.05}),
    "hexmoss_hunker": lambda d, M: JPL.hexmoss(d, M, {"hunker": 1.0}),
    "butterpuff_rest": lambda d, M: JPL.butterpuff(d, M, {}),
    "butterpuff_spores": lambda d, M: JPL.butterpuff(d, M, {"spores": 0.7}),
}
for _k in range(6):
    RAW[f"hexmoss_p{_k}"] = (lambda k: (lambda d, M: JPL.hexmoss(d, M, {"pulse": k})))(_k)
for _k, (_x, _L, _deg) in enumerate(JPL.REEDS):
    for _s, _t, _dr in (("rest", 0.0, 0.0), ("tilt", 1.0, 0.0), ("drop", 0.0, 1.0)):
        RAW[f"ringreed_r{_k}_{_s}"] = shifted((lambda k, t, dr: (lambda d, M: JPL.ringreed_reed(d, M, k, t, dr)))(_k, _t, _dr), -_x, -0.02)
PARTS = {k: scaled(f) for k, f in RAW.items()}


def sway(amp, squash=0.0, cycle=None):
    i = {"type": "sway", "amplitude_deg": amp, "beat_bpm": 110, "squash": squash}
    if cycle:
        i["swap_cycle"] = cycle
    return i


RINGREED = {"name": "ringreed", "biomes": ["deck1", "deck2"],
            "bones": [{"name": "root", "part": "ringreed_tuft", "parent": None, "length": round(0.03 * S, 4), "order": 0}] + [
                {"name": f"r{k}", "part": f"ringreed_r{k}_rest", "parent": "root", "length": round(L * S, 4), "offset_m": off(x, 0.02), "order": 1 + k}
                for k, (x, L, _deg) in enumerate(JPL.REEDS)],
            "swaps": {f"r{k}": [f"ringreed_r{k}_rest", f"ringreed_r{k}_tilt", f"ringreed_r{k}_drop"] for k in range(3)},
            "slots": [{"slot": f"r{k}", "bone": f"r{k}", "offset_m": [0.0, 0.0], "order": 1 + k, "replaces_part": True} for k in range(3)],
            "idle": sway(5, 0.02, {"slot": "r1", "sequence": ["ringreed_r1_rest", "ringreed_r1_tilt"], "beats": [1, 1]}),
            "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "ringreed_r1_drop", "also": {"r0": "ringreed_r0_drop", "r2": "ringreed_r2_drop"}}}
HELIUMBELL = {"name": "heliumbell", "biomes": ["deck2", "deck3"],
              "bones": [{"name": "root", "part": "heliumbell_stem", "parent": None, "length": round(0.38 * S, 4), "order": 0},
                        {"name": "bell", "part": "heliumbell_bell", "parent": "root", "length": round(0.2 * S, 4), "offset_m": off(0.0, 0.40), "order": 1}],
              "swaps": {"bell": ["heliumbell_bell", "heliumbell_bell_swell"], "stem": ["heliumbell_stem", "heliumbell_stem_long"]},
              "slots": [{"slot": "bell", "bone": "bell", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True},
                        {"slot": "stem", "bone": "root", "offset_m": [0.0, 0.0], "order": 0, "replaces_part": True}],
              "idle": sway(4, 0.03, {"slot": "bell", "sequence": ["heliumbell_bell", "heliumbell_bell_swell"], "beats": [2, 2]}),
              "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "heliumbell_bell_swell",
                        "note": "the rise is UNITY's: the bell bone lifts 0.29 m (1.6x) while the stem swaps to heliumbell_stem_long"}}
FROSTFAN = {"name": "frostfan", "biomes": ["deck1"],
            "bones": [{"name": "root", "part": "frostfan_open", "parent": None, "length": round(0.4 * S, 4), "order": 0}],
            "swaps": {"fan": ["frostfan_open", "frostfan_mid", "frostfan_folded"]},
            "slots": [{"slot": "fan", "bone": "root", "offset_m": [0.0, 0.0], "order": 0, "replaces_part": True}],
            "idle": sway(2, 0.02, {"slot": "fan", "sequence": ["frostfan_open", "frostfan_mid"], "beats": [2, 2]}),
            "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "frostfan_folded"}}
HEXMOSS = {"name": "hexmoss", "biomes": ["hexagon"],
           "bones": [{"name": "root", "part": "hexmoss_p0", "parent": None, "length": round(0.25 * S, 4), "order": 0}],
           "swaps": {"moss": [f"hexmoss_p{k}" for k in range(6)] + ["hexmoss_hunker"]},
           "slots": [{"slot": "moss", "bone": "root", "offset_m": [0.0, 0.0], "order": 0, "replaces_part": True}],
           "idle": sway(1, 0.02, {"slot": "moss", "sequence": [f"hexmoss_p{k}" for k in range(6)], "beats": [1] * 6}),
           "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "hexmoss_hunker"}}
BUTTERPUFF = {"name": "butterpuff", "biomes": ["deck1", "deck2"],
              "bones": [{"name": "root", "part": "butterpuff_rest", "parent": None, "length": round(0.35 * S, 4), "order": 0}],
              "swaps": {"puffs": ["butterpuff_rest", "butterpuff_spores"]},
              "slots": [{"slot": "puffs", "bone": "root", "offset_m": [0.0, 0.0], "order": 0, "replaces_part": True}],
              "idle": sway(3, 0.04),
              "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "butterpuff_spores"}}
PLANTS = [RINGREED, HELIUMBELL, FROSTFAN, HEXMOSS, BUTTERPUFF]


def build(out=os.path.join(SRC, "saturn_rigset_c2.blend")):
    """Blender (the Saturn card): one GP object per part around its pivot, the plants on scene["rig_plants"]."""
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
    meta = {"key": "flora/saturn/rigset", "style": "v3", "ppu": 64, "rect_origin": "bottom_left", "parts": parts, "plants": PLANTS}
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
    d = os.path.join(out_dir, "b157_rigset")
    os.makedirs(d, exist_ok=True)
    n = pngio.write_png(os.path.join(d, "rigset_color.png"), sheet)
    with open(os.path.join(d, "rigset.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
    hits, off_ = v3.palette_hits(sheet, "saturn")
    W = 1900
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"b-157 flora/saturn/rigset dry run: {len(meta['parts'])} parts on {sheet.shape[1]}x{sheet.shape[0]} ({n // 1024} kb), "
                        f"{len(PLANTS)} plants, json {'valid' if not problems else 'INVALID ' + '; '.join(problems)[:80]}, saturn palette {hits * 100:.1f}%", 6, 8)
    sh = np.tile(np.array([0.36, 0.30, 0.28], np.float32), (sheet.shape[0] + 10, W, 1))
    review._over(sh, sheet, 8, 5)
    img = np.vstack([head, sh] + plant_rows(W))
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " dry run (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b157_saturn_rigset_dryrun.png")
    review.write(out, img)
    print("written", out, f"| sheet {sheet.shape[1]}x{sheet.shape[0]} {n // 1024} KB, {len(meta['parts'])} parts,",
          "bones", {p["name"]: len(p["bones"]) for p in PLANTS}, "| problems", problems or "-", f"| palette {hits * 100:.1f}% {off_[:3]}")


def main(out):
    """render.py review_script (a future flora/saturn/rigset row): the plants assembled with Unity's maths."""
    import numpy as np
    from meridian import fakegp
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    W = 1900
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"flora/saturn/rigset assembled: {len(PLANTS)} plants, idle (unity's maths) | react", 6, 8)
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
