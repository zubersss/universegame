"""B-161 (C2 Neptune, the rig-set sources): the five Neptune flora (build_c2_neptune_plants) cut into contract §11.3 rig parts
+ bones in the other planets' rig sets' manner: one flora/neptune/rigset, <= 6 bones per plant, swaps, slots, an idle on the
110 bpm beat, a react within 3 m, biomes per plant. Parts at the plants' 1.6x. No faces (D-101). Drawn upright for a +x wind:
UNITY leans each plant's root bone by the local wind and mirrors for a -x wind (D-148). Nothing exports until Neptune's card;
build() makes the Blender source then.

  kitebloom     4 bones  root (the knot) -> tether0 -> tether1 -> kite (a chain: the kite bobs and loops on the beat; react
                         folds the kite)
  gripweed      1 bone   the tangle (flutter a / b on the beat; react clenches)
  pipereed      5 bones  root (the clump) + reed0..reed3 (the reeds bow; react ducks every reed: react.also, as glassreed)
  stormlantern  2 bones  stem -> bulb (the glow low / high over the storm's 8-beat breath, D-148; react dims)
  rimecomb      1 bone   the combs (rest / a flake ticking off on the beat; react snaps shut)

  python -I build_c2_neptune_rigs.py <preview dir>      dry run (lock-free): pack, validate, the assembled idle + react
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_neptune_plants as NPL  # noqa: E402  (gp_draw real in Blender, fakegp outside)

G = NPL.G
S = NPL.SCALE
mats = NPL.mats
SRC = os.path.join(os.path.dirname(HERE), "sources", "flora")
KITE_TILT = 0.35                       # the kite leans downwind (+x) at rest
T0 = (0.04, 0.36)                      # tether0's vector from the knot's top (0, 0.08)
T1 = (0.26, 0.22)                      # tether1's vector; the kite's tail sits at its end


def scaled(fn):
    def part(d, M):
        fn(G.Xf(d, lambda pts: [(x * S, z * S) for x, z in pts]), M)
    return part


def off(x, z):
    return [round(x * S, 4), round(z * S, 4)]


def tether(v):
    def part(d, M):
        G.stroke(d, G.bowed_line((0.0, 0.0), v, bow=0.015, n=8), M["ink"], NPL.I)
    return part


def kite(fold):
    """The kite with its tail point at the bone origin, leaning downwind, two ribbons hanging from the tail."""
    def part(d, M):
        NPL.kitebloom_kite(G.Xf(d, lambda pts: NPL.rot([(x, z + 0.14) for x, z in pts], -KITE_TILT)), M, fold)
        for k in range(2):
            G.stroke(d, G.bezier((0.0, 0.0), (-0.04 - 0.02 * k, -0.05), (0.01 - 0.03 * k, -0.12), n=8), M["ink"], NPL.I)
    return part


def reed(k, ducked):
    bx, h, w = NPL.REEDS[k]

    def part(d, M):
        NPL.pipereed_reed(G.Xf(d, lambda pts: NPL.rot(pts, -NPL.DUCK)) if ducked else d, M, h, w)
    return part


RAW = {
    "kitebloom_root": NPL.kitebloom_root,
    "kitebloom_tether0": tether(T0),
    "kitebloom_tether1": tether(T1),
    "kitebloom_kite_open": kite(0.0),
    "kitebloom_kite_folded": kite(1.0),
    "gripweed_a": lambda d, M: NPL.gripweed(d, M, {"flutter": 0.0}),
    "gripweed_b": lambda d, M: NPL.gripweed(d, M, {"flutter": math.pi}),
    "gripweed_clench": lambda d, M: NPL.gripweed(d, M, {"clench": 1.0}),
    "pipereed_base": NPL.pipereed_base,
    "stormlantern_stem": NPL.stormlantern_stem,
    "stormlantern_bulb_lo": lambda d, M: NPL.stormlantern_bulb(d, M, 0.25),
    "stormlantern_bulb_hi": lambda d, M: NPL.stormlantern_bulb(d, M, 1.0),
    "stormlantern_bulb_dim": lambda d, M: NPL.stormlantern_bulb(d, M, 0.0),
    "rimecomb_rest": lambda d, M: NPL.rimecomb(d, M, {}),
    "rimecomb_flake": lambda d, M: NPL.rimecomb(d, M, {"flake": 4}),
    "rimecomb_shut": lambda d, M: NPL.rimecomb(d, M, {"shut": 1.0}),
}
for _k in range(len(NPL.REEDS)):
    RAW[f"pipereed_reed{_k}_a"] = reed(_k, False)
    RAW[f"pipereed_reed{_k}_b"] = reed(_k, True)
PARTS = {k: scaled(f) for k, f in RAW.items()}


def sway(amp, squash=0.0, cycle=None):
    i = {"type": "sway", "amplitude_deg": amp, "beat_bpm": 110, "squash": squash}
    if cycle:
        i["swap_cycle"] = cycle
    return i


WIND = "UNITY leans the root bone by the local wind and mirrors for a -x wind (D-148)"
KITEBLOOM = {"name": "kitebloom", "biomes": ["deck1", "deck2"],
             "bones": [{"name": "root", "part": "kitebloom_root", "parent": None, "length": round(0.08 * S, 4), "order": 0},
                       {"name": "tether0", "part": "kitebloom_tether0", "parent": "root", "length": round(math.hypot(*T0) * S, 4), "offset_m": off(0.0, 0.08), "order": 1},
                       {"name": "tether1", "part": "kitebloom_tether1", "parent": "tether0", "length": round(math.hypot(*T1) * S, 4), "offset_m": off(*T0), "order": 2},
                       {"name": "kite", "part": "kitebloom_kite_open", "parent": "tether1", "length": round(0.28 * S, 4), "offset_m": off(*T1), "order": 3}],
             "swaps": {"kite": ["kitebloom_kite_open", "kitebloom_kite_folded"]},
             "slots": [{"slot": "kite", "bone": "kite", "offset_m": [0.0, 0.0], "order": 3, "replaces_part": True}],
             "idle": sway(16, 0.02),
             "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "kitebloom_kite_folded", "note": WIND}}
GRIPWEED = {"name": "gripweed", "biomes": ["deck1", "deck2", "deck3", "deep", "storm"],
            "bones": [{"name": "root", "part": "gripweed_a", "parent": None, "length": round(0.2 * S, 4), "order": 0}],
            "swaps": {"tangle": ["gripweed_a", "gripweed_b", "gripweed_clench"]},
            "slots": [{"slot": "tangle", "bone": "root", "offset_m": [0.0, 0.0], "order": 0, "replaces_part": True}],
            "idle": sway(2, 0.03, {"slot": "tangle", "sequence": ["gripweed_a", "gripweed_b"], "beats": [1, 1]}),
            "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "gripweed_clench", "note": WIND}}
PIPEREED = {"name": "pipereed", "biomes": ["deck2", "deck3"],
            "bones": [{"name": "root", "part": "pipereed_base", "parent": None, "length": round(0.05 * S, 4), "order": 0}] + [
                {"name": f"reed{j}", "part": f"pipereed_reed{j}_a", "parent": "root", "length": round(h * S, 4), "offset_m": off(bx, 0.0), "order": 1 + j}
                for j, (bx, h, _w) in enumerate(NPL.REEDS)],
            "swaps": {f"r{j}": [f"pipereed_reed{j}_a", f"pipereed_reed{j}_b"] for j in range(len(NPL.REEDS))},
            "slots": [{"slot": f"r{j}", "bone": f"reed{j}", "offset_m": [0.0, 0.0], "order": 1 + j, "replaces_part": True} for j in range(len(NPL.REEDS))],
            "idle": sway(9, 0.0),
            "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "pipereed_reed0_b",
                      "also": {f"r{j}": f"pipereed_reed{j}_b" for j in range(1, len(NPL.REEDS))}, "note": WIND}}
STORMLANTERN = {"name": "stormlantern", "biomes": ["storm", "deck3"],
                "bones": [{"name": "root", "part": "stormlantern_stem", "parent": None, "length": round(NPL.LANTERN_H * S, 4), "order": 0},
                          {"name": "bulb", "part": "stormlantern_bulb_lo", "parent": "root", "length": round(0.25 * S, 4), "offset_m": off(0.0, NPL.LANTERN_H), "order": 1}],
                "swaps": {"bulb": ["stormlantern_bulb_lo", "stormlantern_bulb_hi", "stormlantern_bulb_dim"]},
                "slots": [{"slot": "bulb", "bone": "bulb", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True}],
                "idle": sway(4, 0.02, {"slot": "bulb", "sequence": ["stormlantern_bulb_lo", "stormlantern_bulb_hi"], "beats": [4, 4]}),
                "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "stormlantern_bulb_dim",
                          "note": "the glow cycle is the storm's 8-beat breath (the storm rim's pulse, D-148); " + WIND}}
RIMECOMB = {"name": "rimecomb", "biomes": ["deep"],
            "bones": [{"name": "root", "part": "rimecomb_rest", "parent": None, "length": round(0.42 * S, 4), "order": 0}],
            "swaps": {"combs": ["rimecomb_rest", "rimecomb_flake", "rimecomb_shut"]},
            "slots": [{"slot": "combs", "bone": "root", "offset_m": [0.0, 0.0], "order": 0, "replaces_part": True}],
            "idle": sway(2, 0.02, {"slot": "combs", "sequence": ["rimecomb_rest", "rimecomb_flake"], "beats": [3, 1]}),
            "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "rimecomb_shut", "note": WIND}}
PLANTS = [KITEBLOOM, GRIPWEED, PIPEREED, STORMLANTERN, RIMECOMB]


def build(out=os.path.join(SRC, "neptune_rigset_c2.blend")):
    """Blender (the Neptune card): one GP object per part around its pivot, the plants on scene["rig_plants"]."""
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
    meta = {"key": "flora/neptune/rigset", "style": "v3", "ppu": 64, "rect_origin": "bottom_left", "parts": parts, "plants": PLANTS}
    return sheet, meta, v3.validate_rigset(meta, sheet.shape)


def plant_rows(W):
    """Per plant: the first 6 idle frames with Unity's maths and its react, on the Neptune blue."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    from meridian import v3
    rows = []
    fw, fh, piv = 200, 200, (0.5, 0.06)
    for plant in PLANTS:
        nfr = PR.idle_frames(plant)
        r = np.tile(np.array(v3.hex_rgb(NPL.P["sky"]), np.float32) / 255, (fh + 28, W, 1))
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
    d = os.path.join(out_dir, "b161_rigset")
    os.makedirs(d, exist_ok=True)
    n = pngio.write_png(os.path.join(d, "rigset_color.png"), sheet)
    with open(os.path.join(d, "rigset.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
    hits, off_ = v3.palette_hits(sheet, "neptune")
    W = 1900
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"b-161 flora/neptune/rigset dry run: {len(meta['parts'])} parts on {sheet.shape[1]}x{sheet.shape[0]} ({n // 1024} kb), "
                        f"{len(PLANTS)} plants, json {'valid' if not problems else 'INVALID ' + '; '.join(problems)[:80]}, neptune palette {hits * 100:.1f}%", 6, 8)
    sh = np.tile(np.array([0.36, 0.30, 0.28], np.float32), (sheet.shape[0] + 10, W, 1))
    review._over(sh, sheet, 8, 5)
    img = np.vstack([head, sh] + plant_rows(W))
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " dry run (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b161_neptune_rigset_dryrun.png")
    review.write(out, img)
    print("written", out, f"| sheet {sheet.shape[1]}x{sheet.shape[0]} {n // 1024} KB, {len(meta['parts'])} parts,",
          "bones", {p["name"]: len(p["bones"]) for p in PLANTS}, "| problems", problems or "-", f"| palette {hits * 100:.1f}% {off_[:3]}")


def main(out):
    """render.py review_script (a future flora/neptune/rigset row): the plants assembled with Unity's maths."""
    import numpy as np
    from meridian import fakegp
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    W = 1900
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"flora/neptune/rigset assembled: {len(PLANTS)} plants, idle (unity's maths) | react", 6, 8)
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
