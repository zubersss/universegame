"""B-153 (C2 Venus, the rig-set sources; LEAD cycle 265): the five Venus plant designs (build_c2_venus_plants) cut into
contract §11.3 rig parts + bones in the Earth / Mars / Mercury rig sets' manner: one flora/venus/rigset, <= 6 bones per
plant, swaps, slots, an idle on the beat, a react within 3 m, biomes per plant. Parts drawn at the plants' 1.6x. No faces
(D-101). The deck plants' wind lean is baked into each part about its own origin (and into the bone offsets), so the
assembled plant matches the drawn design. Nothing exports until B-153 is promoted; build() makes the Blender source then.

  puffsail     2 bones  stem -> sail (full / sag; the idle bobs with a squash)
  sulphurbell  5 bones  vine -> bell0 -> bell1 -> bell2 -> bell3 (a chain, so the sway reaches each bell a step later:
                        the bells swing out of phase; each bell open / shut)
  hazefern     4 bones  tuft -> three fronds (each frond open / mid / tight; the idle curls the tall one on the beat)
  glasscoral   6 bones  foot -> five spikes (the foot dim / bright steps on the beat; each spike full / short)
  ventcap      3 bones  chimney -> lid (open / shut) + steam ring (low / high on the beat)

  python -I build_c2_venus_rigs.py <preview dir>      dry run (lock-free): pack, validate, the assembled idle + react
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_venus_plants as VPL  # noqa: E402  (gp_draw real in Blender, fakegp outside)

G = VPL.G
S = VPL.SCALE
mats = VPL.mats
SRC = os.path.join(os.path.dirname(HERE), "sources", "flora")
PS_LEAN, SB_LEAN = 0.12, 0.06                    # the drawn plants' default wind lean (lean_xf: x += z * a)


def scaled(fn):
    def part(d, M):
        fn(G.Xf(d, lambda pts: [(x * S, z * S) for x, z in pts]), M)
    return part


def shifted(fn, dx, dz):
    def part(d, M):
        fn(G.Xf(d, lambda pts: [(x + dx, z + dz) for x, z in pts]), M)
    return part


def leaned(fn, a):
    """The wind's shear about the part's own origin (x += z * a), as lean_xf does about the plant's root."""
    def part(d, M):
        fn(G.Xf(d, lambda pts: [(x + z * a, z) for x, z in pts]), M)
    return part


def off(x, z):
    return [round(x * S, 4), round(z * S, 4)]


def bell_point(t):
    q = VPL.SB_ARCH[int(t * (len(VPL.SB_ARCH) - 1))]
    return (q[0] + q[1] * SB_LEAN, q[1])                                                  # the leaned stalk tip on the vine


def bell(shut):
    def draw(d, M):
        G.stroke(d, [(0.0, 0.0), (0.0, -0.04)], M["ink"], I)                               # the stalk, from the vine down
        VPL.sulphurbell_bell(G.Xf(d, lambda pts: [(x, z - 0.04) for x, z in pts]), M, shut)
    return draw


I = VPL.I
FRONDS = ((-0.03, 0.50, 0.0), (0.0, 0.66, 0.1), (0.03, 0.42, -0.05))                     # hazefern (dx, L, curl offset)
CURL = {"open": 0.1, "mid": 0.45, "tight": 1.0}
RAW = {
    "puffsail_stem": leaned(VPL.puffsail_stem, PS_LEAN),
    "puffsail_sail_full": leaned(lambda d, M: VPL.puffsail_sail(d, M, 1.0), PS_LEAN),
    "puffsail_sail_sag": leaned(lambda d, M: VPL.puffsail_sail(d, M, 0.45), PS_LEAN),
    "sulphurbell_vine": leaned(VPL.sulphurbell_vine, SB_LEAN),
    "sulphurbell_bell_open": leaned(bell(0.0), SB_LEAN),
    "sulphurbell_bell_shut": leaned(bell(1.0), SB_LEAN),
    "hazefern_tuft": lambda d, M: G.stroke(d, G.lumpy_ellipse(0.0, 0.02, 0.08, 0.03, n=12, seed=3), M["olive_sh"], I, cyclic=True),
    "glasscoral_foot_dim": lambda d, M: VPL.glasscoral_foot(d, M, 0.1),
    "glasscoral_foot_bright": lambda d, M: VPL.glasscoral_foot(d, M, 0.9),
    "ventcap_chimney": VPL.ventcap_chimney,
    "ventcap_lid_open": lambda d, M: VPL.ventcap_lid(d, M, 1.0),
    "ventcap_lid_shut": lambda d, M: VPL.ventcap_lid(d, M, 0.0),
}
for _k, (_dx, _L, _c0) in enumerate(FRONDS):
    for _s, _c in CURL.items():
        RAW[f"hazefern_frond{_k}_{_s}"] = (lambda k, L, c: (lambda d, M: VPL.hazefern_frond(d, M, c, L, seed=5 + k)))(_k, _L, min(1.0, _c + _c0))
for _k, (_x, _L, _deg) in enumerate(VPL.SPIKES):
    for _s, _f in (("full", 1.0), ("short", 0.55)):
        RAW[f"glasscoral_spike{_k}_{_s}"] = shifted((lambda k, L, deg: (lambda d, M: VPL.glasscoral_spike(d, M, 0.0, L, deg, k)))(_k, _L * _f, _deg), 0.0, -0.04)


def puff(t):
    """The cream steam ring at t (0 low .. 1 high), relative to the chimney mouth (0, 0.30)."""
    def draw(d, M):
        r = 0.05 + 0.06 * t
        zb = 0.12 + 0.30 * t - r * 0.5                                                    # a faint steam trail from the mouth to the
        G.stroke(d, [(-0.014, 0.0), (0.014, 0.0), (0.02 * t + 0.03, zb), (0.02 * t - 0.03, zb)], M["cream_sh"], 0.0, cyclic=True)   # ring (keeps the
        G.stroke(d, G.lumpy_ellipse(0.02 * t, 0.12 + 0.30 * t, r * 1.4, r * 0.6, n=16, lump=0.1, seed=24), M["cream"], I, cyclic=True)  # pivot in the rect)
        G.stroke(d, G.lumpy_ellipse(0.02 * t, 0.12 + 0.30 * t, r * 0.7, r * 0.25, n=12, seed=25), M["cream_sh"], 0.0, cyclic=True)
    return draw


RAW["ventcap_puff_low"] = puff(0.15)
RAW["ventcap_puff_high"] = puff(0.75)
PARTS = {k: scaled(f) for k, f in RAW.items()}


def sway(amp, squash=0.0, cycle=None):
    i = {"type": "sway", "amplitude_deg": amp, "beat_bpm": 110, "squash": squash}
    if cycle:
        i["swap_cycle"] = cycle
    return i


PUFFSAIL = {"name": "puffsail", "biomes": ["cloud_deck"],
            "bones": [{"name": "root", "part": "puffsail_stem", "parent": None, "length": round(0.36 * S, 4), "order": 0},
                      {"name": "sail", "part": "puffsail_sail_full", "parent": "root", "length": round(0.42 * S, 4),
                       "offset_m": off(0.36 * PS_LEAN, 0.36), "order": 1}],
            "swaps": {"sail": ["puffsail_sail_full", "puffsail_sail_sag"]},
            "slots": [{"slot": "sail", "bone": "sail", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True}],
            "idle": sway(6, 0.04),
            "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "puffsail_sail_sag"}}
_BP = [bell_point(t) for t in VPL.BELL_T]
SULPHURBELL = {"name": "sulphurbell", "biomes": ["cloud_deck", "station_rails"],
               "bones": [{"name": "root", "part": "sulphurbell_vine", "parent": None, "length": round(0.40 * S, 4), "order": 0}] + [
                   {"name": f"bell{k}", "part": "sulphurbell_bell_open", "parent": "root" if k == 0 else f"bell{k - 1}", "length": round(0.18 * S, 4),
                    "offset_m": off(*(_BP[0] if k == 0 else (_BP[k][0] - _BP[k - 1][0], _BP[k][1] - _BP[k - 1][1]))), "order": 1 + k}
                   for k in range(len(_BP))],
               "swaps": {f"b{k}": ["sulphurbell_bell_open", "sulphurbell_bell_shut"] for k in range(len(_BP))},
               "slots": [{"slot": f"b{k}", "bone": f"bell{k}", "offset_m": [0.0, 0.0], "order": 1 + k, "replaces_part": True} for k in range(len(_BP))],
               "idle": sway(20, 0.0),
               "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "sulphurbell_bell_shut"}}
HAZEFERN = {"name": "hazefern", "biomes": ["cloud_deck"],
            "bones": [{"name": "root", "part": "hazefern_tuft", "parent": None, "length": round(0.04 * S, 4), "order": 0}] + [
                {"name": f"frond{k}", "part": f"hazefern_frond{k}_mid", "parent": "root", "length": round(L * S, 4), "offset_m": off(dx, 0.02), "order": 1 + k}
                for k, (dx, L, _c) in enumerate(FRONDS)],
            "swaps": {f"f{k}": [f"hazefern_frond{k}_{s}" for s in CURL] for k in range(len(FRONDS))},
            "slots": [{"slot": f"f{k}", "bone": f"frond{k}", "offset_m": [0.0, 0.0], "order": 1 + k, "replaces_part": True} for k in range(len(FRONDS))],
            "idle": sway(8, 0.02, {"slot": "f1", "sequence": ["hazefern_frond1_mid", "hazefern_frond1_open"], "beats": [2, 2]}),
            "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "hazefern_frond1_tight",
                      "also": {"f0": "hazefern_frond0_tight", "f2": "hazefern_frond2_tight"}}}
GLASSCORAL = {"name": "glasscoral", "biomes": ["vent_fields"],
              "bones": [{"name": "root", "part": "glasscoral_foot_dim", "parent": None, "length": round(0.04 * S, 4), "order": 0}] + [
                  {"name": f"spike{k}", "part": f"glasscoral_spike{k}_full", "parent": "root", "length": round(L * S, 4), "offset_m": off(x, 0.04), "order": 1 + k}
                  for k, (x, L, _deg) in enumerate(VPL.SPIKES)],
              "swaps": dict({"foot": ["glasscoral_foot_dim", "glasscoral_foot_bright"]},
                            **{f"s{k}": [f"glasscoral_spike{k}_full", f"glasscoral_spike{k}_short"] for k in range(len(VPL.SPIKES))}),
              "slots": [{"slot": "foot", "bone": "root", "offset_m": [0.0, 0.0], "order": 0, "replaces_part": True}] + [
                  {"slot": f"s{k}", "bone": f"spike{k}", "offset_m": [0.0, 0.0], "order": 1 + k, "replaces_part": True} for k in range(len(VPL.SPIKES))],
              "idle": sway(4, 0.0, {"slot": "foot", "sequence": ["glasscoral_foot_dim", "glasscoral_foot_bright"], "beats": [1, 1]}),
              "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "glasscoral_spike0_short",
                        "also": {f"s{k}": f"glasscoral_spike{k}_short" for k in range(1, len(VPL.SPIKES))}}}
VENTCAP = {"name": "ventcap", "biomes": ["surface_plains", "vent_fields"],
           "bones": [{"name": "root", "part": "ventcap_chimney", "parent": None, "length": round(0.30 * S, 4), "order": 0},
                     {"name": "lid", "part": "ventcap_lid_open", "parent": "root", "length": round(0.20 * S, 4), "offset_m": off(-0.10, 0.30), "order": 1},
                     {"name": "puff", "part": "ventcap_puff_low", "parent": "root", "length": round(0.30 * S, 4), "offset_m": off(0.0, 0.30), "order": 2}],
           "swaps": {"lid": ["ventcap_lid_open", "ventcap_lid_shut"], "puff": ["ventcap_puff_low", "ventcap_puff_high"]},
           "slots": [{"slot": "lid", "bone": "lid", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True},
                     {"slot": "puff", "bone": "puff", "offset_m": [0.0, 0.0], "order": 2, "replaces_part": True}],
           "idle": sway(3, 0.03, {"slot": "puff", "sequence": ["ventcap_puff_low", "ventcap_puff_high"], "beats": [1, 1]}),
           "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "ventcap_lid_shut"}}
PLANTS = [PUFFSAIL, SULPHURBELL, HAZEFERN, GLASSCORAL, VENTCAP]


def build(out=os.path.join(SRC, "venus_rigset_c2.blend")):
    """Blender (when B-153 is promoted): one GP object per part around its pivot, the plants on scene["rig_plants"]."""
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
    meta = {"key": "flora/venus/rigset", "style": "v3", "ppu": 64, "rect_origin": "bottom_left", "parts": parts, "plants": PLANTS}
    return sheet, meta, v3.validate_rigset(meta, sheet.shape)


def plant_rows(W):
    """Per plant: the first 6 idle frames with Unity's maths and its react, on an apricot panel (the deck's sky)."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import preview_c2_earth_rigs as PR
    from meridian import v3
    rows = []
    fw, fh, piv = 200, 200, (0.5, 0.06)
    for plant in PLANTS:
        nfr = PR.idle_frames(plant)
        r = np.tile(np.array(v3.hex_rgb(VPL.P["sky"]), np.float32) / 255, (fh + 28, W, 1))
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
    d = os.path.join(out_dir, "b153_rigset")
    os.makedirs(d, exist_ok=True)
    n = pngio.write_png(os.path.join(d, "rigset_color.png"), sheet)
    with open(os.path.join(d, "rigset.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
    hits, off_ = v3.palette_hits(sheet, "venus")
    W = 1900
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"b-153 flora/venus/rigset dry run: {len(meta['parts'])} parts on {sheet.shape[1]}x{sheet.shape[0]} ({n // 1024} kb), "
                        f"{len(PLANTS)} plants, json {'valid' if not problems else 'INVALID ' + '; '.join(problems)[:80]}, venus palette {hits * 100:.1f}%", 6, 8)
    sh = np.tile(np.array([0.36, 0.30, 0.28], np.float32), (sheet.shape[0] + 10, W, 1))
    review._over(sh, sheet, 8, 5)
    img = np.vstack([head, sh] + plant_rows(W))
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " dry run (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b153_venus_rigset_dryrun.png")
    review.write(out, img)
    print("written", out, f"| sheet {sheet.shape[1]}x{sheet.shape[0]} {n // 1024} KB, {len(meta['parts'])} parts,",
          "bones", {p["name"]: len(p["bones"]) for p in PLANTS}, "| problems", problems or "-", f"| palette {hits * 100:.1f}% {off_[:3]}")


def main(out):
    """render.py review_script (a future flora/venus/rigset row): the plants assembled with Unity's maths."""
    import numpy as np
    from meridian import fakegp
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    W = 1900
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, f"flora/venus/rigset assembled: {len(PLANTS)} plants, idle (unity's maths) | react", 6, 8)
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
