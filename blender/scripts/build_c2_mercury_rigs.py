"""B-145 (C2 Mercury, the rig-set sources; LEAD cycle 260): the five Mercury plant designs (build_c2_mercury_plants) cut into
contract §11.3 rig parts + bones in the Earth / Mars rig sets' manner: one flora/mercury/rigset, <= 6 bones per plant,
swaps, slots, an idle on the beat, a react within 3 m, biomes per plant. Parts drawn at the plants' 1.5x. No faces
(D-101). Nothing exports until a Mercury card exists; build() makes the Blender source then.

  sunfan      2 bones  stem -> fan (fan_open / fan_edge / fan_shut; the idle tilts it edge-on on the beat)
  embercap    2 bones  foot -> cap (cap / cap_puff)
  glassreed   6 bones  base -> five reeds (each reed: glint a / b)
  shadebloom  2 bones  stem -> bloom (bud / half / open)
  coilwort    2 bones  knob -> spring (rest / short / tall, the ice bead on top)

  python -I build_c2_mercury_rigs.py <preview dir>      dry run (lock-free): pack, validate, the assembled idle + react
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_mercury_plants as MPL  # noqa: E402  (gp_draw real in Blender, fakegp outside)

G = MPL.G
S = MPL.SCALE
mats = MPL.mats
SRC = os.path.join(os.path.dirname(HERE), "sources", "flora")


def scaled(fn):
    def part(d, M):
        fn(G.Xf(d, lambda pts: [(x * S, z * S) for x, z in pts]), M)
    return part


def shifted(fn, dz):
    def part(d, M):
        fn(G.Xf(d, lambda pts: [(x, z + dz) for x, z in pts]), M)
    return part


def off(x, z):
    return [round(x * S, 4), round(z * S, 4)]


REEDS = sorted(MPL.REEDS, key=lambda r: -r[1])          # the drawing order of the plant (tallest first)
RAW = {
    "sunfan_stem": MPL.sunfan_stem,
    "sunfan_fan_open": lambda d, M: MPL.sunfan_fan(d, M, 0.0, 0.0, hub=(0.0, 0.0)),
    "sunfan_fan_edge": lambda d, M: MPL.sunfan_fan(d, M, 1.0, 0.0, hub=(0.0, 0.0)),
    "sunfan_fan_shut": lambda d, M: MPL.sunfan_fan(d, M, 0.0, 1.0, hub=(0.0, 0.0)),
    "embercap_foot": MPL.embercap_foot,
    "embercap_cap": shifted(lambda d, M: MPL.embercap_cap(d, M, None), -0.15),
    "embercap_cap_puff": shifted(lambda d, M: MPL.embercap_cap(d, M, 0.6), -0.15),
    "glassreed_base": MPL.glassreed_base,
    "shadebloom_stem": MPL.shadebloom_stem,
    "shadebloom_bloom_bud": lambda d, M: MPL.shadebloom_bloom(d, M, 0.0, (0.0, 0.0)),
    "shadebloom_bloom_half": lambda d, M: MPL.shadebloom_bloom(d, M, 0.5, (0.0, 0.0)),
    "shadebloom_bloom_open": lambda d, M: MPL.shadebloom_bloom(d, M, 1.0, (0.0, 0.0)),
    "coilwort_knob": MPL.coilwort_knob,
    "coilwort_spring_rest": lambda d, M: MPL.coilwort_spring(d, M, 0.36),
    "coilwort_spring_short": lambda d, M: MPL.coilwort_spring(d, M, 0.22),
    "coilwort_spring_tall": lambda d, M: MPL.coilwort_spring(d, M, 0.48),
}
for _j, (_x, _L, _deg) in enumerate(REEDS):
    for _g, _k in (("a", 0), ("b", 1)):
        RAW[f"glassreed_reed{_j}_{_g}"] = (lambda j, L, deg, k: (lambda d, M: MPL.glassreed_reed(d, M, j, 0.0, L, math.radians(deg), k, z0=0.0)))(_j, _L, _deg, _k)
PARTS = {k: scaled(f) for k, f in RAW.items()}


def sway(amp, squash=0.0, cycle=None):
    i = {"type": "sway", "amplitude_deg": amp, "beat_bpm": 110, "squash": squash}
    if cycle:
        i["swap_cycle"] = cycle
    return i


SUNFAN = {"name": "sunfan", "biomes": ["day"],
          "bones": [{"name": "root", "part": "sunfan_stem", "parent": None, "length": round(0.32 * S, 4), "order": 0},
                    {"name": "fan", "part": "sunfan_fan_open", "parent": "root", "length": round(0.30 * S, 4), "offset_m": off(0.0, 0.34), "order": 1}],
          "swaps": {"fan": ["sunfan_fan_open", "sunfan_fan_edge", "sunfan_fan_shut"]},
          "slots": [{"slot": "fan", "bone": "fan", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True}],
          "idle": sway(6, 0.02, {"slot": "fan", "sequence": ["sunfan_fan_open", "sunfan_fan_edge"], "beats": [1, 1]}),
          "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "sunfan_fan_shut"}}
EMBERCAP = {"name": "embercap", "biomes": ["day"],
            "bones": [{"name": "root", "part": "embercap_foot", "parent": None, "length": round(0.15 * S, 4), "order": 0},
                      {"name": "cap", "part": "embercap_cap", "parent": "root", "length": round(0.16 * S, 4), "offset_m": off(0.0, 0.15), "order": 1}],
            "swaps": {"cap": ["embercap_cap", "embercap_cap_puff"]},
            "slots": [{"slot": "cap", "bone": "cap", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True}],
            "idle": sway(2, 0.05),
            "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "embercap_cap_puff"}}
GLASSREED = {"name": "glassreed", "biomes": ["twilight"],
             "bones": [{"name": "root", "part": "glassreed_base", "parent": None, "length": round(0.04 * S, 4), "order": 0}] + [
                 {"name": f"reed{j}", "part": f"glassreed_reed{j}_a", "parent": "root", "length": round(L * S, 4), "offset_m": off(x, 0.04), "order": 1 + j}
                 for j, (x, L, _deg) in enumerate(REEDS)],
             "swaps": {f"r{j}": [f"glassreed_reed{j}_a", f"glassreed_reed{j}_b"] for j in range(len(REEDS))},
             "slots": [{"slot": f"r{j}", "bone": f"reed{j}", "offset_m": [0.0, 0.0], "order": 1 + j, "replaces_part": True} for j in range(len(REEDS))],
             "idle": sway(9, 0.0, {"slot": "r0", "sequence": ["glassreed_reed0_a", "glassreed_reed0_b"], "beats": [3, 1]}),
             "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "glassreed_reed0_b",
                       "also": {f"r{j}": f"glassreed_reed{j}_b" for j in range(1, len(REEDS))}}}
SHADEBLOOM = {"name": "shadebloom", "biomes": ["night", "polar"],
              "bones": [{"name": "root", "part": "shadebloom_stem", "parent": None, "length": round(0.48 * S, 4), "order": 0},
                        {"name": "bloom", "part": "shadebloom_bloom_half", "parent": "root", "length": round(0.18 * S, 4),
                         "offset_m": off(*MPL.SB_TOP), "order": 1}],
              "swaps": {"bloom": ["shadebloom_bloom_bud", "shadebloom_bloom_half", "shadebloom_bloom_open"]},
              "slots": [{"slot": "bloom", "bone": "bloom", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True}],
              "idle": sway(5, 0.02, {"slot": "bloom", "sequence": ["shadebloom_bloom_bud", "shadebloom_bloom_half", "shadebloom_bloom_open",
                                                                    "shadebloom_bloom_half"], "beats": [2, 1, 4, 1]}),
              "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "shadebloom_bloom_bud"}}
COILWORT = {"name": "coilwort", "biomes": ["polar"],
            "bones": [{"name": "root", "part": "coilwort_knob", "parent": None, "length": round(0.03 * S, 4), "order": 0},
                      {"name": "spring", "part": "coilwort_spring_rest", "parent": "root", "length": round(0.36 * S, 4), "offset_m": [0.0, 0.0], "order": 1}],
            "swaps": {"spring": ["coilwort_spring_rest", "coilwort_spring_short", "coilwort_spring_tall"]},
            "slots": [{"slot": "spring", "bone": "spring", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True}],
            "idle": sway(4, 0.0, {"slot": "spring", "sequence": ["coilwort_spring_rest", "coilwort_spring_tall"], "beats": [1, 1]}),
            "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "coilwort_spring_short"}}
PLANTS = [SUNFAN, EMBERCAP, GLASSREED, SHADEBLOOM, COILWORT]


def build(out=os.path.join(SRC, "mercury_rigset_c2.blend")):
    """Blender (when a Mercury card opens): one GP object per part around its pivot, the plants on scene["rig_plants"]."""
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
    pos, SW, SH_ = v3.shelf_pack([(im.shape[1], im.shape[0]) for im in imgs])
    sheet = np.zeros((SH_, SW, 4), np.uint8)
    parts = []
    for name, im, (px_, ytop), pv in zip(names, imgs, pos, pivs):
        h_, w_ = im.shape[:2]
        sheet[ytop:ytop + h_, px_:px_ + w_] = im
        parts.append({"name": name, "rect": [px_, SH_ - (ytop + h_), w_, h_], "pivot": [round(pv[0], 4), round(pv[1], 4)]})
    meta = {"key": "flora/mercury/rigset", "style": "v3", "ppu": 64, "rect_origin": "bottom_left", "parts": parts, "plants": PLANTS}
    return sheet, meta, v3.validate_rigset(meta, sheet.shape)


def plant_rows(W):
    """Per plant: the first 6 idle frames with Unity's maths and its react, on a slate panel (night-side contrast)."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    from meridian import v3
    rows = []
    fw, fh, piv = 200, 200, (0.5, 0.06)
    for plant in PLANTS:
        nfr = PR.idle_frames(plant)
        r = np.tile(np.array(v3.hex_rgb(MPL.P["sky"]), np.float32) / 255, (fh + 28, W, 1))
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
    d = os.path.join(out_dir, "b145_rigset")
    os.makedirs(d, exist_ok=True)
    n = pngio.write_png(os.path.join(d, "rigset_color.png"), sheet)
    with open(os.path.join(d, "rigset.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
    hits, off_ = v3.palette_hits(sheet, "mercury")
    W = 1900
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"b-145 flora/mercury/rigset dry run: {len(meta['parts'])} parts on {sheet.shape[1]}x{sheet.shape[0]} ({n // 1024} kb), "
                        f"{len(PLANTS)} plants, json {'valid' if not problems else 'INVALID ' + '; '.join(problems)[:80]}, mercury palette {hits * 100:.1f}%", 6, 8)
    sh = np.tile(np.array([0.62, 0.72, 0.72], np.float32), (sheet.shape[0] + 10, W, 1))
    review._over(sh, sheet, 8, 5)
    img = np.vstack([head, sh] + plant_rows(W))
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " dry run (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b145_mercury_rigset_dryrun.png")
    review.write(out, img)
    print("written", out, f"| sheet {sheet.shape[1]}x{sheet.shape[0]} {n // 1024} KB, {len(meta['parts'])} parts,",
          "bones", {p["name"]: len(p["bones"]) for p in PLANTS}, "| problems", problems or "-", f"| palette {hits * 100:.1f}% {off_[:3]}")


def main(out):
    """render.py review_script (a future flora/mercury/rigset row): the plants assembled with Unity's maths."""
    import numpy as np
    from meridian import fakegp
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    W = 1900
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"flora/mercury/rigset assembled: {len(PLANTS)} plants, idle (unity's maths) | react", 6, 8)
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
