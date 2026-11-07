"""B-155 (C2 Jupiter, the rig-set sources): the five Jupiter flora (build_c2_jupiter_plants) cut into contract §11.3 rig
parts + bones in the Earth / Mars / Mercury / Venus rig sets' manner: one flora/jupiter/rigset, <= 6 bones per plant,
swaps, slots, an idle on the beat, a react within 3 m, biomes per plant. Parts drawn at the plants' 1.6x. No faces (D-101).
Nothing exports until Jupiter's card; build() makes the Blender source then.

  driftbulb     2 bones  tether -> bulb (full / sag; the idle bobs with a squash)
  bandstreamer  4 bones  holdfast -> three streamers (streamer 0 swaps two wave phases on the beat; react wraps all three)
  frostrosette  1 bone   the rosette (open / glint / folded: the glint on the beat, react folds)
  phosphorcup   4 bones  stem -> three cups (open / half / closed; cup 1 breathes on the beat; react closes all; the
                         react's one spin is UNITY's, a flip of the plant's root)
  stormreed     6 bones  tuft -> five reeds (normal / lit / flat; reed 1 flickers on the beat; react flattens all)

  python -I build_c2_jupiter_rigs.py <preview dir>      dry run (lock-free): pack, validate, the assembled idle + react
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_jupiter_plants as JPL  # noqa: E402  (gp_draw real in Blender, fakegp outside)

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


def rotated(fn, a):
    c, s = math.cos(a), math.sin(a)

    def part(d, M):
        fn(G.Xf(d, lambda pts: [(x * c - z * s, x * s + z * c) for x, z in pts]), M)
    return part


def off(x, z):
    return [round(x * S, 4), round(z * S, 4)]


RAW = {
    "driftbulb_tether": JPL.driftbulb_tether,
    "driftbulb_bulb_full": lambda d, M: JPL.driftbulb_bulb(d, M, 1.0),
    "driftbulb_bulb_sag": lambda d, M: JPL.driftbulb_bulb(d, M, 0.45),
    "bandstreamer_holdfast": JPL.bandstreamer_holdfast,
    "frostrosette_open": lambda d, M: JPL.frostrosette(d, M, {}),
    "frostrosette_glint": lambda d, M: JPL.frostrosette(d, M, {"glint": 2}),
    "frostrosette_fold": lambda d, M: JPL.frostrosette(d, M, {"fold": 1.0}),
    "phosphorcup_stem": JPL.phosphorcup_stem,
    "stormreed_tuft": JPL.stormreed_tuft,
}
for _k, (_x0, _z0, _L, _ph) in enumerate(JPL.STREAMERS):                                  # streamers about their own roots
    for _s, _phase, _wrap in (("a", 0.0, 0.0), ("b", math.pi, 0.0), ("wrap", 0.0, 1.0)):
        if _s == "b" and _k:
            continue
        RAW[f"bandstreamer_s{_k}_{_s}"] = shifted((lambda k, ph, w: (lambda d, M: JPL.bandstreamer_streamer(d, M, k, ph, w)))(_k, _phase, _wrap), -_x0, -_z0)
for _k, (_x, _z, _deg) in enumerate(JPL.CUP_TIPS):
    for _s, _o in (("open", 1.0), ("half", 0.5), ("closed", 0.0)):
        RAW[f"phosphorcup_c{_k}_{_s}"] = rotated((lambda o, k: (lambda d, M: JPL.phosphorcup_cup(d, M, o, seed=61 + k)))(_o, _k), math.radians(_deg) * 0.25)
for _k, (_x, _L, _deg) in enumerate(JPL.REEDS):
    _side = 1 if _deg >= 88 else -1
    for _s, _dd, _lit in (("rest", _deg, False), ("lit", _deg, True), ("flat", _deg + _side * 62, False)):
        RAW[f"stormreed_r{_k}_{_s}"] = shifted((lambda dd, lit, L: (lambda d, M: JPL.stormreed_reed(d, M, 0.0, L, dd, lit)))(_dd, _lit, _L * (0.9 if _s == "flat" else 1.0)), 0.0, -0.02)
PARTS = {k: scaled(f) for k, f in RAW.items()}


def sway(amp, squash=0.0, cycle=None):
    i = {"type": "sway", "amplitude_deg": amp, "beat_bpm": 110, "squash": squash}
    if cycle:
        i["swap_cycle"] = cycle
    return i


DRIFTBULB = {"name": "driftbulb", "biomes": ["deck1", "deck2"],
             "bones": [{"name": "root", "part": "driftbulb_tether", "parent": None, "length": round(0.40 * S, 4), "order": 0},
                       {"name": "bulb", "part": "driftbulb_bulb_full", "parent": "root", "length": round(0.34 * S, 4), "offset_m": off(0.02, 0.40), "order": 1}],
             "swaps": {"bulb": ["driftbulb_bulb_full", "driftbulb_bulb_sag"]},
             "slots": [{"slot": "bulb", "bone": "bulb", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True}],
             "idle": sway(6, 0.04),
             "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "driftbulb_bulb_sag"}}
BANDSTREAMER = {"name": "bandstreamer", "biomes": ["deck1"],
                "bones": [{"name": "root", "part": "bandstreamer_holdfast", "parent": None, "length": round(0.12 * S, 4), "order": 2}] + [
                    {"name": f"s{k}", "part": f"bandstreamer_s{k}_a", "parent": "root", "length": round(L * S, 4), "offset_m": off(x0, z0),
                     "order": 3 if k == 0 else 1} for k, (x0, z0, L, _ph) in enumerate(JPL.STREAMERS)],
                "swaps": dict({"s0": ["bandstreamer_s0_a", "bandstreamer_s0_b", "bandstreamer_s0_wrap"]},
                              **{f"s{k}": [f"bandstreamer_s{k}_a", f"bandstreamer_s{k}_wrap"] for k in (1, 2)}),
                "slots": [{"slot": f"s{k}", "bone": f"s{k}", "offset_m": [0.0, 0.0], "order": 3 if k == 0 else 1, "replaces_part": True} for k in range(3)],
                "idle": sway(10, 0.0, {"slot": "s0", "sequence": ["bandstreamer_s0_a", "bandstreamer_s0_b"], "beats": [1, 1]}),
                "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "bandstreamer_s0_wrap",
                          "also": {"s1": "bandstreamer_s1_wrap", "s2": "bandstreamer_s2_wrap"}}}
FROSTROSETTE = {"name": "frostrosette", "biomes": ["deck1"],
                "bones": [{"name": "root", "part": "frostrosette_open", "parent": None, "length": round(0.3 * S, 4), "order": 0}],
                "swaps": {"rosette": ["frostrosette_open", "frostrosette_glint", "frostrosette_fold"]},
                "slots": [{"slot": "rosette", "bone": "root", "offset_m": [0.0, 0.0], "order": 0, "replaces_part": True}],
                "idle": sway(2, 0.02, {"slot": "rosette", "sequence": ["frostrosette_open", "frostrosette_glint"], "beats": [3, 1]}),
                "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "frostrosette_fold"}}
PHOSPHORCUP = {"name": "phosphorcup", "biomes": ["red_spot"],
               "bones": [{"name": "root", "part": "phosphorcup_stem", "parent": None, "length": round(0.33 * S, 4), "order": 0}] + [
                   {"name": f"c{k}", "part": f"phosphorcup_c{k}_open", "parent": "root", "length": round(0.1 * S, 4), "offset_m": off(x, z), "order": 1 + k}
                   for k, (x, z, _deg) in enumerate(JPL.CUP_TIPS)],
               "swaps": {f"c{k}": [f"phosphorcup_c{k}_open", f"phosphorcup_c{k}_half", f"phosphorcup_c{k}_closed"] for k in range(3)},
               "slots": [{"slot": f"c{k}", "bone": f"c{k}", "offset_m": [0.0, 0.0], "order": 1 + k, "replaces_part": True} for k in range(3)],
               "idle": sway(4, 0.02, {"slot": "c1", "sequence": ["phosphorcup_c1_open", "phosphorcup_c1_half"], "beats": [2, 2]}),
               "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "phosphorcup_c0_closed",
                         "also": {"c1": "phosphorcup_c1_closed", "c2": "phosphorcup_c2_closed"}, "note": "the one spin is UNITY's (a flip of the root)"}}
STORMREED = {"name": "stormreed", "biomes": ["deck2", "deck3"],
             "bones": [{"name": "root", "part": "stormreed_tuft", "parent": None, "length": round(0.03 * S, 4), "order": 0}] + [
                 {"name": f"r{k}", "part": f"stormreed_r{k}_rest", "parent": "root", "length": round(L * S, 4), "offset_m": off(x, 0.02), "order": 1 + k}
                 for k, (x, L, _deg) in enumerate(JPL.REEDS)],
             "swaps": {f"r{k}": [f"stormreed_r{k}_rest", f"stormreed_r{k}_lit", f"stormreed_r{k}_flat"] for k in range(5)},
             "slots": [{"slot": f"r{k}", "bone": f"r{k}", "offset_m": [0.0, 0.0], "order": 1 + k, "replaces_part": True} for k in range(5)],
             "idle": sway(5, 0.0, {"slot": "r1", "sequence": ["stormreed_r1_rest", "stormreed_r1_lit"], "beats": [3, 1]}),
             "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "stormreed_r0_flat",
                       "also": {f"r{k}": f"stormreed_r{k}_flat" for k in range(1, 5)}}}
PLANTS = [DRIFTBULB, BANDSTREAMER, FROSTROSETTE, PHOSPHORCUP, STORMREED]


def build(out=os.path.join(SRC, "jupiter_rigset_c2.blend")):
    """Blender (the Jupiter card): one GP object per part around its pivot, the plants on scene["rig_plants"]."""
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
    meta = {"key": "flora/jupiter/rigset", "style": "v3", "ppu": 64, "rect_origin": "bottom_left", "parts": parts, "plants": PLANTS}
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
    d = os.path.join(out_dir, "b155_rigset")
    os.makedirs(d, exist_ok=True)
    n = pngio.write_png(os.path.join(d, "rigset_color.png"), sheet)
    with open(os.path.join(d, "rigset.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
    hits, off_ = v3.palette_hits(sheet, "jupiter")
    W = 1900
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"b-155 flora/jupiter/rigset dry run: {len(meta['parts'])} parts on {sheet.shape[1]}x{sheet.shape[0]} ({n // 1024} kb), "
                        f"{len(PLANTS)} plants, json {'valid' if not problems else 'INVALID ' + '; '.join(problems)[:80]}, jupiter palette {hits * 100:.1f}%", 6, 8)
    sh = np.tile(np.array([0.36, 0.30, 0.28], np.float32), (sheet.shape[0] + 10, W, 1))
    review._over(sh, sheet, 8, 5)
    img = np.vstack([head, sh] + plant_rows(W))
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " dry run (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b155_jupiter_rigset_dryrun.png")
    review.write(out, img)
    print("written", out, f"| sheet {sheet.shape[1]}x{sheet.shape[0]} {n // 1024} KB, {len(meta['parts'])} parts,",
          "bones", {p["name"]: len(p["bones"]) for p in PLANTS}, "| problems", problems or "-", f"| palette {hits * 100:.1f}% {off_[:3]}")


def main(out):
    """render.py review_script (a future flora/jupiter/rigset row): the plants assembled with Unity's maths."""
    import numpy as np
    from meridian import fakegp
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    W = 1900
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"flora/jupiter/rigset assembled: {len(PLANTS)} plants, idle (unity's maths) | react", 6, 8)
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
