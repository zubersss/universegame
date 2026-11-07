"""C2 Earth plants as §11.3 rig plants (LEAD cycle 246, while-waiting #3): Nodbell, Shiverbarrel,
Curlfrond, Whiptuft, Thriftcushion. Sources + lock-free previews only; no export yet.

They join the snoozle in ONE rig set (flora/earth/rigset: one texture for every Earth plant, D-089),
and they use only what Unity's rig runtime animates today (RigSetBuilder / FloraRigs, U-108):
  * idle sway: each bone turns  (amplitude / bone count) * sin(2 pi t / period - depth * 0.35),
    period = two beats; deeper bones turn later (a whip), and a child adds its parents' turns;
  * a squash on the root (y 1 + s, x 1 / (1 + s)) once per beat;
  * one swap_cycle slot stepping on the beat; react = one swap plus `also` swaps on other slots.
Out-of-phase motion (Thriftcushion's poms, Whiptuft's seed stalks, Curlfrond's fronds) comes from
CASCADES: sibling stems chained parent -> child with their pivots side by side at the base, so each
lags the last by 0.35 rad. The pivots sit within 0.4 m, so a base drifts <= ~3 px at the full
swing, and the base part (cushion, clump, crown) is drawn on top to cover it.

Every part is drawn in its own frame with the PIVOT AT THE ORIGIN (metres, x right, z up). Part
names carry the plant's name (one namespace for the whole set); the snoozle's names are unchanged.

  python -I build_c2_earth_rigs.py <out.png>       lock-free review (meridian.fakegp, no Blender)
  build(out)                                       Blender: sources/flora/earth_rigset_c2.blend with
                                                   one GP object per part + scene["rig_plants"]
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_earth_plants as C  # noqa: E402  (picks the real gp_draw in Blender, the fake outside)

G = C.G
P, O, I = C.P, C.O, C.I
rot, hose_stem, leaf, mats = C.rot, C.hose_stem, C.leaf, C.mats
SRC = os.path.join(os.path.dirname(HERE), "sources", "flora")


def shift(pts, dx, dz):
    return [(x + dx, z + dz) for x, z in pts]


# ---------------------------------------------------------------- 1. Nodbell (4 bones)
NB_ARC = G.bezier((0.0, 0.0), (0.25, 0.12), (0.42, -0.05), n=10)        # the arch, in the arch bone's frame
NB_BELLS_AT = NB_ARC[4]                                                  # the bells bone's pivot on the arch


def nodbell_stem_lower(d, M):
    hose_stem(d, M, G.bezier((0.0, 0.0), (0.0, 0.25), (0.02, 0.49), n=8), 0.07, rib_every=0.14)
    leaf(d, M, (0.0, 0.16), math.radians(150), 0.34, 0.08)
    leaf(d, M, (0.0, 0.28), math.radians(25), 0.30, 0.07)


def nodbell_stem_upper(d, M):                       # pivot = world (0.02, 0.45); reaches the arch at (0.28, 0.60)
    hose_stem(d, M, G.bezier((0.0, -0.03), (0.03, 0.40), (0.28, 0.60), n=12), 0.07, rib_every=0.14)


def nodbell_arch(d, M):
    hose_stem(d, M, [(-0.03, -0.035)] + NB_ARC, 0.05, rib_every=0.2)


def _bells(d, M, nod):
    for k, idx in enumerate((2, 4, 8)):
        bx, bz = NB_ARC[idx][0] - NB_BELLS_AT[0], NB_ARC[idx][1] - NB_BELLS_AT[1]
        swing = math.radians(18 * nod * (1 + 0.25 * k))
        bell = G.bezier((-0.07, 0.0), (-0.09, -0.12), (-0.11, -0.17), n=6) + \
            [(-0.07, -0.20), (-0.02, -0.17), (0.02, -0.20), (0.07, -0.17)] + \
            G.bezier((0.11, -0.17), (0.09, -0.12), (0.07, 0.0), n=6)
        bell = [(bx + p[0], bz - 0.03 + p[1]) for p in rot(bell, swing)]
        G.stroke(d, [(bx, bz + 0.02), (bx, bz - 0.03)], M["ink"], I)                    # pedicel into the arch
        G.stroke(d, bell, M["bell"], 0.0, cyclic=True)
        G.stroke(d, [q for q in bell if q[0] < bx - 0.02] + [(bx - 0.02, bz - 0.15)], M["bell_sh"], 0.0, cyclic=True)
        mouth = [(bx + p[0], bz - 0.03 + p[1]) for p in rot([(-0.08, -0.17), (0.0, -0.13), (0.08, -0.17), (0.0, -0.19)], swing)]
        G.stroke(d, mouth, M["bell_in"], 0.0, cyclic=True)
        G.seam(d, [(bx + p[0], bz - 0.03 + p[1]) for p in rot([(0.0, -0.02), (0.01, -0.12)], swing)], M["ink"])
        G.stroke(d, bell, M["ink"], O, cyclic=True)


NODBELL = {
    "name": "nodbell", "biomes": ["plains", "forest"],
    "bones": [
        {"name": "root", "part": "nodbell_stem_lower", "parent": None, "length": 0.45, "order": 0},
        {"name": "stem2", "part": "nodbell_stem_upper", "parent": "root", "length": 0.65, "offset_m": [0.02, 0.45], "order": 1},
        {"name": "arch", "part": "nodbell_arch", "parent": "stem2", "length": 0.42, "offset_m": [0.28, 0.60], "order": 2},
        {"name": "bells", "part": "nodbell_bells_hang", "parent": "arch", "length": 0.2,
         "offset_m": [round(NB_BELLS_AT[0], 4), round(NB_BELLS_AT[1], 4)], "order": 3},
    ],
    "swaps": {"bells": ["nodbell_bells_hang", "nodbell_bells_nod"]},
    "slots": [{"slot": "bells", "bone": "bells", "offset_m": [0.0, 0.0], "order": 3, "replaces_part": True}],
    "idle": {"type": "sway", "amplitude_deg": 14, "beat_bpm": 100, "squash": 0.04,
             "swap_cycle": {"slot": "bells", "sequence": ["nodbell_bells_hang", "nodbell_bells_nod"], "beats": [7, 1]}},
    "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "nodbell_bells_nod"},
}


# ---------------------------------------------------------------- 2. Shiverbarrel (2 bones)
def _barrel(d, M, sh):
    sx, sz = 1 + 0.06 * abs(sh), 1 - 0.05 * abs(sh)
    body = G.lumpy_ellipse(0.0, 0.30, 0.30 * sx, 0.30 * sz, n=40, lump=0.04, seed=3)
    body = [(x + 0.022 * sh * math.sin(z * 40), max(z, 0.02)) for x, z in body]
    G.stroke(d, body, M["cactus_fill"], 0.0, cyclic=True)
    G.stroke(d, [q for q in body if q[0] < -0.10] + [(-0.10, 0.05)], M["cactus_sh"], 0.0, cyclic=True)
    G.stroke(d, [q for q in body if q[0] < -0.22] + [(-0.22, 0.10)], M["cactus_dp"], 0.0, cyclic=True)
    for k, xr in enumerate((-0.18, -0.06, 0.06, 0.18)):                 # ribs with spine ticks (they flick with the shiver)
        rib = [(xr * sx * (1 - 0.25 * ((z - 0.30) / 0.30) ** 2) + 0.012 * sh * math.sin(z * 40), z)
               for z in [0.06 + 0.48 * t / 8 for t in range(9)]]
        G.seam(d, rib, M["ink"])
        for x, z in rib[1:-1:2]:
            tick = 0.035 * (1 if k % 2 else -1)
            G.seam(d, [(x, z), (x + tick * (1 + 0.5 * abs(sh)), z + 0.025 + 0.012 * sh)], M["ink"])
    G.stroke(d, body, M["ink"], O, cyclic=True)


def _crown(d, M, open_):                             # pivot = world (0, 0.56): petals spring from (0, 0.02)
    n = 7
    for k in range(n):
        a = math.pi / 2 + (k - (n - 1) / 2) * (0.20 + 0.18 * open_)
        r = 0.5 + 0.5 * open_
        tip = (0.19 * math.cos(a) * r, 0.02 + 0.16 * math.sin(a) * (0.55 + 0.45 * open_))
        pet = G.bezier((0.0, 0.02), (tip[0] * 0.6 - 0.02, (0.02 + tip[1]) / 2 + 0.02), tip, n=6) + \
            G.bezier(tip, (tip[0] * 0.6 + 0.02, (0.02 + tip[1]) / 2 - 0.01), (0.0, 0.02), n=6)[1:-1]
        G.stroke(d, pet, M["mustard"], O, cyclic=True)
    if open_ > 0.3:
        G.stroke(d, G.lumpy_ellipse(0.0, 0.045, 0.03, 0.022, n=10, seed=4), M["brown"], I, cyclic=True)
    G.specks(d, [(-0.01, 0.04), (0.015, 0.05), (0.0, 0.065)], M["ink"])


SHIVERBARREL = {
    "name": "shiverbarrel", "biomes": ["desert"],
    "bones": [
        {"name": "root", "part": "shiverbarrel_body", "parent": None, "length": 0.56, "order": 0},
        {"name": "crown", "part": "shiverbarrel_crown_half", "parent": "root", "length": 0.18, "offset_m": [0.0, 0.56], "order": 1},
    ],
    "swaps": {"body": ["shiverbarrel_body", "shiverbarrel_body_shiver_a", "shiverbarrel_body_shiver_b"],
              "crown": ["shiverbarrel_crown_half", "shiverbarrel_crown_open"]},
    "slots": [{"slot": "body", "bone": "root", "offset_m": [0.0, 0.0], "order": 0, "replaces_part": True},
              {"slot": "crown", "bone": "crown", "offset_m": [0.0, 0.0], "order": 1, "replaces_part": True}],
    "idle": {"type": "sway", "amplitude_deg": 3, "beat_bpm": 120, "squash": 0.07,
             "swap_cycle": {"slot": "body", "beats": [6, 1, 1, 1, 1],
                            "sequence": ["shiverbarrel_body", "shiverbarrel_body_shiver_a", "shiverbarrel_body_shiver_b",
                                         "shiverbarrel_body_shiver_a", "shiverbarrel_body_shiver_b"]}},
    "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "shiverbarrel_crown_open"},
}


# ---------------------------------------------------------------- 3. Curlfrond (4 bones, cascade)
CF_LEAN = {"l": -0.5, "c": 0.05, "r": 0.55}
CF_BASE = {"l": -0.08, "c": 0.0, "r": 0.09}


def _frond(d, M, lean, curl, k):
    """One frond rooted at the origin (the design's curlfrond, per frond)."""
    pts = [(0.0, -0.02)]
    a, step = math.pi / 2 + lean * 0.6, 0.06
    L = 0.95 - 0.15 * abs(lean)
    n = int(L / step)
    for i in range(n):
        t = i / n
        a -= (0.04 + (2.6 * curl) * t ** 3) * (1 if lean >= 0 else -1) * (0.6 + 0.4 * (1 - curl))
        x, z = pts[-1]
        pts.append((x + step * math.cos(a), z + step * math.sin(a)))
    G.stroke(d, G.hose_outline(pts, 0.065), M["blade"], O, cyclic=True)        # ink-behind: the frond stays green
    for i in range(2, len(pts) - 3, 2):                                        # leaflets
        (x0, z0), (x1, z1) = pts[i], pts[i + 1]
        ta = math.atan2(z1 - z0, x1 - x0)
        size = 0.17 * (1 - i / len(pts)) * (1 - 0.55 * curl * (i / len(pts)))
        for s in (-1, 1):
            L_, W_ = max(0.05, size), max(0.022, size * 0.38)
            lf = G.bezier((0, 0), (L_ * 0.45, W_), (L_, 0.0), n=8) + G.bezier((L_, 0.0), (L_ * 0.45, -W_ * 0.8), (0, 0), n=8)[1:-1]
            G.stroke(d, [(x0 + q[0], z0 + q[1]) for q in rot(lf, ta + s * 1.1)], M["blade"], I, cyclic=True)
            G.seam(d, [(x0 + q[0], z0 + q[1]) for q in rot([(L_ * 0.1, 0.0), (L_ * 0.8, 0.0)], ta + s * 1.1)], M["ink"])
    G.hatch(d, pts[2][0] - 0.03, pts[2][1] + 0.03, M["ink"], n=2, length=0.04, spacing=0.018, angle_deg=70, seed=k)
    tx, tz = pts[-1]                                                           # the mustard fiddlehead tip (LEAD cycle 245)
    G.stroke(d, G.lumpy_ellipse(tx, tz, 0.058, 0.052, n=14, lump=0.08, seed=30 + k), M["mustard"], O, cyclic=True)
    G.seam(d, [(tx - 0.02, tz), (tx + 0.005, tz + 0.015), (tx + 0.02, tz - 0.005)], M["ink"])


def curlfrond_base(d, M):
    """The crown the fronds spring from: a low brown mound of old frond bases, drawn over the joints."""
    mound = [(x, max(z, 0.0)) for x, z in G.lumpy_ellipse(0.0, 0.025, 0.15, 0.06, n=24, lump=0.10, seed=17)]
    G.stroke(d, mound, M["brown"], 0.0, cyclic=True)
    G.stroke(d, [q for q in mound if q[0] < -0.05] + [(-0.05, 0.0)], M["brown_dp"], 0.0, cyclic=True)
    for x in (-0.09, -0.03, 0.04, 0.10):
        G.seam(d, [(x, 0.005), (x + 0.012, 0.055)], M["ink"])
    G.specks(d, [(-0.06, 0.03), (0.02, 0.045), (0.08, 0.02)], M["ink"])
    G.stroke(d, mound, M["ink"], O, cyclic=True)


def _cf(side, curl, k):
    return lambda d, M: _frond(d, M, CF_LEAN[side], curl, k)


CURLFROND = {
    "name": "curlfrond", "biomes": ["forest", "taiga"],
    "bones": [
        {"name": "root", "part": "curlfrond_base", "parent": None, "length": 0.06, "order": 3},
        {"name": "frond_l", "part": "curlfrond_l_open", "parent": "root", "length": 0.8, "offset_m": [CF_BASE["l"], 0.03], "order": 0},
        {"name": "frond_c", "part": "curlfrond_c_open", "parent": "frond_l", "length": 0.9,
         "offset_m": [CF_BASE["c"] - CF_BASE["l"], 0.0], "order": 1},
        {"name": "frond_r", "part": "curlfrond_r_open", "parent": "frond_c", "length": 0.8,
         "offset_m": [CF_BASE["r"] - CF_BASE["c"], 0.0], "order": 2},
    ],
    "swaps": {"frond_l": ["curlfrond_l_open", "curlfrond_l_curled"],
              "frond_c": ["curlfrond_c_open", "curlfrond_c_half", "curlfrond_c_curled"],
              "frond_r": ["curlfrond_r_open", "curlfrond_r_curled"]},
    "slots": [{"slot": s, "bone": s, "offset_m": [0.0, 0.0], "order": o, "replaces_part": True}
              for s, o in (("frond_l", 0), ("frond_c", 1), ("frond_r", 2))],
    "idle": {"type": "sway", "amplitude_deg": 10, "beat_bpm": 100, "squash": 0.03,
             "swap_cycle": {"slot": "frond_c", "beats": [4, 2, 4, 2],
                            "sequence": ["curlfrond_c_open", "curlfrond_c_half", "curlfrond_c_curled", "curlfrond_c_half"]}},
    "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "curlfrond_c_curled",
              "also": {"frond_l": "curlfrond_l_curled", "frond_r": "curlfrond_r_curled"}},
}


# ---------------------------------------------------------------- 4. Whiptuft (4 bones, cascade)
WT_BASE = {k: -0.12 + 0.03 * k for k in range(9)}
WT_WHIPS = {"a": 2, "b": 5, "c": 7}


def _blade(d, M, k, flat, x0=0.0, head=False):
    base = x0
    lean = (k - 4) * 0.10 * (1 + 1.2 * flat)
    L = 0.55 + 0.25 * math.sin(k * 1.7) ** 2
    tip = (base + L * math.sin(lean), L * math.cos(lean) * (1 - 0.3 * flat))
    mid = (base + 0.5 * L * math.sin(lean * 0.6), 0.55 * tip[1])
    blade = G.bezier((base - 0.026, -0.02), mid, tip, n=8) + G.bezier(tip, (mid[0] + 0.028, mid[1]), (base + 0.026, -0.02), n=8)[1:-1]
    G.stroke(d, blade, M["blade"] if k % 3 else M["blade_sh"], O, cyclic=True)
    if head:                                                                   # the seed head on its stalk
        hx, hz = tip
        cx, cz = hx + 0.06 * math.sin(lean), hz + 0.06 * math.cos(lean)
        G.stroke(d, G.lumpy_ellipse(cx, cz, 0.035, 0.08, n=16, lump=0.08, seed=k, rot=-lean), M["mustard"], O, cyclic=True)
        for j in range(3):
            G.seam(d, [(cx - 0.025, hz + 0.04 + 0.03 * j), (cx + 0.025, hz + 0.05 + 0.03 * j)], M["ink"])


def whiptuft_clump(flat):
    def draw(d, M):
        for k in range(9):
            if k not in WT_WHIPS.values():
                _blade(d, M, k, flat, x0=WT_BASE[k])
        G.specks(d, [(-0.10, 0.02), (0.05, 0.03), (0.15, 0.015)], M["ink"])
    return draw


def whiptuft_whip(name, flat):
    return lambda d, M: _blade(d, M, WT_WHIPS[name], flat, head=True)


WHIPTUFT = {
    "name": "whiptuft", "biomes": ["plains", "coast"],
    "bones": [
        {"name": "root", "part": "whiptuft_clump", "parent": None, "length": 0.6, "order": 3},
        {"name": "whip_a", "part": "whiptuft_whip_a", "parent": "root", "length": 0.8, "offset_m": [round(WT_BASE[2], 4), 0.0], "order": 0},
        {"name": "whip_b", "part": "whiptuft_whip_b", "parent": "whip_a", "length": 0.8,
         "offset_m": [round(WT_BASE[5] - WT_BASE[2], 4), 0.0], "order": 1},
        {"name": "whip_c", "part": "whiptuft_whip_c", "parent": "whip_b", "length": 0.8,
         "offset_m": [round(WT_BASE[7] - WT_BASE[5], 4), 0.0], "order": 2},
    ],
    "swaps": {"clump": ["whiptuft_clump", "whiptuft_clump_flat"], "whip_a": ["whiptuft_whip_a", "whiptuft_whip_a_flat"],
              "whip_b": ["whiptuft_whip_b", "whiptuft_whip_b_flat"], "whip_c": ["whiptuft_whip_c", "whiptuft_whip_c_flat"]},
    "slots": [{"slot": "clump", "bone": "root", "offset_m": [0.0, 0.0], "order": 3, "replaces_part": True}] +
             [{"slot": s, "bone": s, "offset_m": [0.0, 0.0], "order": o, "replaces_part": True}
              for s, o in (("whip_a", 0), ("whip_b", 1), ("whip_c", 2))],
    "idle": {"type": "sway", "amplitude_deg": 18, "beat_bpm": 100, "squash": 0.03},
    "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "whiptuft_clump_flat",
              "also": {"whip_a": "whiptuft_whip_a_flat", "whip_b": "whiptuft_whip_b_flat", "whip_c": "whiptuft_whip_c_flat"}},
}


# ---------------------------------------------------------------- 5. Thriftcushion (6 bones, cascade)
TC_POMS = [("a", -0.18, 0.42), ("b", -0.08, 0.55), ("c", 0.02, 0.48), ("d", 0.12, 0.58), ("e", 0.21, 0.40)]
TC_PIVOT_Z = 0.08


def thriftcushion_cushion(d, M):
    cushion = [(x, max(z, 0.0)) for x, z in G.lumpy_ellipse(0.0, 0.07, 0.30, 0.10, n=36, lump=0.06, seed=11)]
    G.stroke(d, cushion, M["stem_fill"], 0.0, cyclic=True)
    G.stroke(d, [q for q in cushion if q[1] < 0.05], M["stem_dp"], 0.0, cyclic=True)
    for k in range(9):
        x = -0.24 + 0.06 * k
        G.seam(d, [(x, 0.03), (x + 0.02 * math.sin(k), 0.13 + 0.02 * math.cos(k))], M["ink"])
    G.stroke(d, cushion, M["ink"], O, cyclic=True)


def thriftcushion_pom(k, up):
    _n, bx, h = TC_POMS[k]

    def draw(d, M):
        hz = h + 0.12 * up - TC_PIVOT_Z
        hx = 0.04 * math.sin(k * 2.1)
        G.stroke(d, G.bezier((0.0, -0.03), (0.03, (hz - 0.03) / 2), (hx, hz - 0.06), n=8), M["ink"], I)
        pom = G.lumpy_ellipse(hx, hz, 0.075, 0.07, n=24, lump=0.10, seed=20 + k)
        G.stroke(d, pom, M["red"], 0.0, cyclic=True)
        G.stroke(d, [q for q in pom if q[0] - hx + (q[1] - hz) < -0.04] + [(hx - 0.02, hz - 0.02)], M["red_sh"], 0.0, cyclic=True)
        G.specks(d, [(hx + 0.02, hz + 0.02), (hx - 0.01, hz + 0.035), (hx + 0.03, hz - 0.01), (hx - 0.03, hz)], M["ink"])
        G.stroke(d, pom, M["ink"], O, cyclic=True)
    return draw


def _tc_bones():
    out = [{"name": "root", "part": "thriftcushion_cushion", "parent": None, "length": 0.17, "order": 5}]
    prev, px = "root", 0.0
    for k, (n, bx, _h) in enumerate(TC_POMS):
        out.append({"name": f"pom_{n}", "part": f"thriftcushion_pom_{n}", "parent": prev, "length": 0.5,
                    "offset_m": [round(bx - px, 4), TC_PIVOT_Z if prev == "root" else 0.0], "order": k})
        prev, px = f"pom_{n}", bx
    return out


THRIFTCUSHION = {
    "name": "thriftcushion", "biomes": ["coast", "tundra"],
    "bones": _tc_bones(),
    "swaps": {f"pom_{n}": [f"thriftcushion_pom_{n}", f"thriftcushion_pom_{n}_up"] for n, _b, _h in TC_POMS},
    "slots": [{"slot": f"pom_{n}", "bone": f"pom_{n}", "offset_m": [0.0, 0.0], "order": k, "replaces_part": True}
              for k, (n, _b, _h) in enumerate(TC_POMS)],
    "idle": {"type": "sway", "amplitude_deg": 12, "beat_bpm": 110, "squash": 0.05},
    "react": {"radius_m": 3.0, "action": "turn_bounce", "swap": "thriftcushion_pom_c_up",
              "also": {f"pom_{n}": f"thriftcushion_pom_{n}_up" for n, _b, _h in TC_POMS if n != "c"}},
}


PARTS = {
    "nodbell_stem_lower": nodbell_stem_lower, "nodbell_stem_upper": nodbell_stem_upper, "nodbell_arch": nodbell_arch,
    "nodbell_bells_hang": lambda d, M: _bells(d, M, 0.0), "nodbell_bells_nod": lambda d, M: _bells(d, M, 1.0),
    "shiverbarrel_body": lambda d, M: _barrel(d, M, 0.0), "shiverbarrel_body_shiver_a": lambda d, M: _barrel(d, M, 1.0),
    "shiverbarrel_body_shiver_b": lambda d, M: _barrel(d, M, -1.0),
    "shiverbarrel_crown_half": lambda d, M: _crown(d, M, 0.5), "shiverbarrel_crown_open": lambda d, M: _crown(d, M, 1.0),
    "curlfrond_base": curlfrond_base,
    "curlfrond_l_open": _cf("l", 0.15, 0), "curlfrond_l_curled": _cf("l", 1.0, 0),
    "curlfrond_c_open": _cf("c", 0.15, 1), "curlfrond_c_half": _cf("c", 0.55, 1), "curlfrond_c_curled": _cf("c", 0.95, 1),
    "curlfrond_r_open": _cf("r", 0.15, 2), "curlfrond_r_curled": _cf("r", 1.0, 2),
    "whiptuft_clump": whiptuft_clump(0.0), "whiptuft_clump_flat": whiptuft_clump(1.0),
}
for _n in WT_WHIPS:
    PARTS[f"whiptuft_whip_{_n}"] = whiptuft_whip(_n, 0.0)
    PARTS[f"whiptuft_whip_{_n}_flat"] = whiptuft_whip(_n, 1.0)
PARTS["thriftcushion_cushion"] = thriftcushion_cushion
for _k, (_n, _b, _h) in enumerate(TC_POMS):
    PARTS[f"thriftcushion_pom_{_n}"] = thriftcushion_pom(_k, 0.0)
    PARTS[f"thriftcushion_pom_{_n}_up"] = thriftcushion_pom(_k, 1.0)

PLANTS = [NODBELL, SHIVERBARREL, CURLFROND, WHIPTUFT, THRIFTCUSHION]


def snoozle_plant():
    """The B-126 snoozle unchanged, plus its biomes (B-129: every plant names its biomes)."""
    import build_flora_earth_v3 as F
    return dict(F.PLANT, biomes=["plains"])


def all_plants():
    return [snoozle_plant()] + PLANTS


def build(out=os.path.join(SRC, "earth_rigset_c2.blend")):
    """Blender (C2 export, not run yet): the snoozle's parts + these, one GP object per part around its
    pivot, every plant on scene["rig_plants"]. Replaces earth_rigset.blend as flora/earth/rigset's source
    once LEAD opens the export."""
    import bpy
    import build_flora_earth_v3 as F
    scene = G.new_scene()
    scene["rig_plants"] = json.dumps(all_plants())
    coll = G.collection("parts")
    for name, fn in list(F.PARTS.items()) + list(PARTS.items()):
        ob, gp = G.gp_object("part_" + name, coll)
        layer = gp.layers.new("art")
        fn(G.drawing(layer, 1), (F.mats if name in F.PARTS else mats)(gp))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


if __name__ == "__main__":
    import preview_c2_earth_rigs
    preview_c2_earth_rigs.main(sys.argv[1])
