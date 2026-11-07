"""B-157 (C2 Saturn design prep): Saturn creature design previews on the B-132 kit (build_creatures_earth_v3: posed body,
pie eyes, dizzy stars), in the proposed Saturn palette (build_c2_saturn_palette; registered with setdefault until LEAD
accepts it). Faces kept, friendly or neutral, no teeth (D-087 / D-101). Every Saturn creature lives off the ground:
pivots at the body centre, all four frame edges checked, the travel clip at index 1.

  helium_jelly  96x112   floats up when hit (Decks 2-3): a pale-gold bell, a cream frill rim, a dusk-salmon inner glow
                         (a tone), trailing cream tendrils, pie eyes; idle 10 (a pulse), drift 12, react 8 (shoots up,
                         deflating), bump 10
  hex_drake     192x112  rides the Hexagon's walls: a slate body, a cream belly, dusk-salmon wing membranes on slate bones, a
                         hexagon-patterned crest, a rounded smiling snout (no beak, no teeth); idle 10 (a hover), fly 12,
                         react 8 (a wing-shielded turn), bump 10
  floe_moth     64x64    Deck 1 floes: cream wings edged ring-ice blue-grey (no eyespots), a butter body, feathery antennae;
                         idle 8, fly 12, react 8 (scatter), bump 8
  ringmite      48x48    space (ring mining), swarms: a round slate shell with pale-gold flecks, six stubby legs, pie eyes,
                         never biting on screen; idle 8 (legs wiggle), fly 12 (a drift), react 8 (curls into a ball), bump 8

The Polar Hydra (apex) is a Grand rig set (D-140): build_polar_hydra_v3.py. Design previews only.

  python -I build_creatures_saturn_v3.py <preview dir> [names]      lock-free (meridian.fakegp; exact stroke ids)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_earth_v3 as K  # noqa: E402  (the kit; gp_draw real in Blender, fakegp outside)
from meridian import v3  # noqa: E402

G = K.G
P = v3.PALETTES["saturn"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "saturn")


def DP(h):
    return v3.deep_of(h, "saturn")


def mats(gp, sp):
    def m(name, **kw):
        return G.mat(gp, f"{sp}_{name}", **kw)
    out = {"ink": m("ink", fill=None), "pupil": m("pupil", fill=G.INK, ink=False), "eye": m("eye_white", fill=P["offwhite"]),
           "mouth": m("mouth", fill=DP(P["red"])), "star": m("star", fill=P["mustard"]),
           "puff": m("puff", fill=P["offwhite"]), "puff_sh": m("puff_mid", fill=SH(P["offwhite"]), ink=False)}
    for key, slot in (("gold", "mustard"), ("salmon", "red"), ("cream", "offwhite"), ("ice", "teal"), ("moss", "green"),
                      ("butter", "sky"), ("slate", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
        out[key + "_b"] = m(key + "_behind", fill=h, behind=True)
    out["leg"], out["coat"] = m("leg", fill=SH(P["brown"])), m("coat", fill=SH(P["brown"]))
    out["leg_far"], out["far"] = m("leg_far", fill=DP(P["brown"])), m("far", fill=DP(P["brown"]))
    out["claw"] = m("claw", fill=P["offwhite"], behind=True)
    return out


# ---------------------------------------------------------------- helium jelly
def draw_helium_jelly(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(pulse=0.0, trail=0.0, deflate=0.0))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    k = 1.0 - 0.3 * p["deflate"]
    rx, rz, cz = 0.36 * k * (1 + 0.06 * math.sin(p["pulse"])), 0.30 * k * (1 - 0.05 * math.sin(p["pulse"])), 0.18
    for j in range(5):                                                                    # the tendrils, trailing
        x0 = -0.22 + 0.11 * j
        sw = 0.05 * math.sin(p["pulse"] * 1.2 + j) - 0.2 * p["trail"]
        tend = G.bezier((x0, cz - rz * 0.6), (x0 + sw * 0.5, cz - rz - 0.15), (x0 + sw, cz - rz - 0.42 + 0.03 * (j % 2)), n=8)
        G.stroke(db, G.hose_outline(tend, 0.022), M["cream_b"], I, cyclic=True)
    bell = [(x, max(z, cz - rz * 0.5)) for x, z in G.lumpy_ellipse(0.0, cz, rx, rz, n=40, lump=0.02, seed=seed + 1)]
    G.stroke(db, bell, M["gold_f"], 0.0, cyclic=True)
    G.stroke(db, G.lumpy_ellipse(0.0, cz - rz * 0.15, rx * 0.55, rz * 0.4, n=20, seed=seed + 2), M["salmon_sh"], 0.0, cyclic=True)   # the inner glow (a tone)
    G.stroke(db, [q for q in bell if q[0] > rx * 0.35] + [(rx * 0.35, cz)], M["gold_sh"], 0.0, cyclic=True)
    for j in range(3):
        x = -0.18 + 0.18 * j
        G.seam(db, G.bezier((x * 0.5, cz + rz * 0.9), (x * 1.1, cz + rz * 0.3), (x, cz - rz * 0.45), n=6), M["ink"])
    G.stroke(db, bell, M["ink"], O, cyclic=True)
    frill = [(x, z) for x, z in G.lumpy_ellipse(0.0, cz - rz * 0.5, rx * 1.02, 0.05, n=26, lump=0.15, seed=seed + 3)]
    G.stroke(db, frill, M["cream"], I, cyclic=True)
    H = K.turn((0.0, cz), p["head_rot"], p["head"], B)
    dh = G.Xf(d, H)
    K.eyes(dh, M, 0.08 * k, cz + 0.02, 0.04, 0.055, 0.08, p, seed)
    if p["mouth"] > 0.05:
        G.stroke(dh, G.lumpy_ellipse(0.14 * k, cz - 0.1, 0.02 + 0.01 * p["mouth"], 0.014 + 0.016 * p["mouth"], n=10, seed=seed + 4), M["mouth"], I, cyclic=True)
    else:
        G.seam(dh, G.bezier((0.09, cz - 0.09), (0.14, cz - 0.12), (0.19, cz - 0.09), n=5), M["ink"])
    if p["stars"] is not None:
        K.stars(dh, M, 0.0, cz + rz + 0.12, 0.18, p["stars"])


def jelly_poses():
    out = []
    for i in range(10):                                                                   # idle: a pulse, a slow bob
        ph = TAU * i / 10
        out.append(dict(pulse=ph, bob=0.03 * math.sin(ph), blink={6: 0.6, 7: 1.0}.get(i, 0.0), look=(0.6, -0.1)))
    for i in range(12):                                                                   # drift: tendrils trailing
        ph = TAU * i / 6
        out.append(dict(pulse=ph, bob=0.02 * math.sin(ph), trail=0.8, rock=-0.08, look=(0.9, 0.0)))
    for i, up in enumerate((0.0, 0.05, 0.12, 0.2, 0.26, 0.3, 0.32, 0.32)):               # react: shoots up, deflating (UNITY moves it)
        out.append(dict(bob=up, deflate=min(1.0, 0.3 * i), trail=-0.6 if i < 5 else -0.2, eye_pop=1.5 if i < 3 else 1.1,
                        mouth=0.6 if i in (1, 2) else 0.0, pulse=1.5 * i))
    out += [dict(q, shift=0.5 * q.get("shift", 0.0)) for q in K.bump_clip()]
    return out


# ---------------------------------------------------------------- hex drake (rides the Hexagon's walls)
def drake_wing(d, M, flap, up, near):
    tip = (-0.15, up * 0.62 * flap)
    root_a, root_b = (0.18, up * 0.06), (-0.30, up * 0.04)
    bones = [root_a, (0.02, up * 0.40 * flap), tip]
    shape = bones + [(-0.30, up * 0.42 * flap), (-0.42, up * 0.18 * flap), root_b]
    G.stroke(d, shape, M["salmon_f" if near else "salmon_sh"], 0.0, cyclic=True)
    for b in ((-0.30, up * 0.42 * flap), (-0.42, up * 0.18 * flap)):                       # the wing bones (slate)
        G.stroke(d, G.hose_outline([(0.02, up * 0.40 * flap), b], 0.012), M["slate"], I, cyclic=True)
    G.stroke(d, G.hose_outline(bones, 0.02), M["slate"], I, cyclic=True)
    G.stroke(d, shape, M["ink"], O if near else I, cyclic=True)


def draw_hex_drake(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(flap=1.0, shield=0.0, tail_w=0.0))
    p.update(pose or {})
    d = G.Xf(d, lambda pts: [(x * 1.25, z * 1.25) for x, z in pts])                         # drawn 1.25x: it fills its 192x112 frame
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    tail = [(-0.30 - 0.55 * t, 0.03 * math.sin(p["tail_w"] + 4 * t) * t - 0.02 * t) for t in [k / 10 for k in range(11)]]
    G.stroke(db, G.hose_outline(tail, 0.035), M["ice_dp"], 0.0, cyclic=True)
    G.stroke(db, G.hose_outline(tail, 0.035), M["ink"], I, cyclic=True)
    tip = tail[-1]
    G.stroke(db, [tip, (tip[0] - 0.06, tip[1] + 0.05), (tip[0] - 0.09, tip[1]), (tip[0] - 0.06, tip[1] - 0.05)], M["salmon"], I, cyclic=True)   # a tail fin
    f = p["flap"] * (1 - 0.6 * p["shield"])
    drake_wing(db, M, f, 1, False)
    body = G.lumpy_ellipse(0.0, 0.0, 0.34, 0.13, n=30, lump=0.02, seed=seed + 1)
    G.stroke(db, body, M["ice_dp"], 0.0, cyclic=True)                                    # a slate-blue hide (the slate itself read as black)
    G.stroke(db, [q for q in body if q[1] < -0.03] + [(0.0, -0.03)], M["cream_f"], 0.0, cyclic=True)        # the cream belly
    G.stroke(db, body, M["ink"], O, cyclic=True)
    H = K.turn((0.28, 0.04), p["head_rot"], p["head"], B)
    dh = G.Xf(d, H)
    hx, hz = 0.42, 0.10
    for j in range(3):                                                                    # the hexagon crest
        cx, cz = hx - 0.10 - 0.07 * j, hz + 0.11 - 0.01 * j
        hexa = [(cx + 0.06 * math.cos(a), cz + 0.052 * math.sin(a)) for a in [i * TAU / 6 for i in range(6)]]
        G.stroke(dh, hexa, M["salmon_f"], 0.0, cyclic=True)
        G.stroke(dh, [(cx + 0.03 * math.cos(a), cz + 0.026 * math.sin(a)) for a in [i * TAU / 6 for i in range(6)]], M["cream_f"], 0.0, cyclic=True)
        G.stroke(dh, hexa, M["ink"], I, cyclic=True)
    head = G.lumpy_ellipse(hx, hz, 0.13, 0.095, n=26, lump=0.02, seed=seed + 2)
    G.stroke(dh, head, M["ice_dp"], 0.0, cyclic=True)
    snout = G.lumpy_ellipse(hx + 0.1, hz - 0.03, 0.07, 0.05, n=18, seed=seed + 3)            # the rounded snout (no beak)
    G.stroke(dh, snout, M["cream_f"], 0.0, cyclic=True)
    G.stroke(dh, head, M["ink"], O, cyclic=True)
    G.stroke(dh, snout, M["ink"], I, cyclic=True)
    K.eyes(dh, M, hx + 0.01, hz + 0.03, 0.026, 0.034, 0.05, p, seed)
    if p["mouth"] > 0.05:
        G.stroke(dh, G.lumpy_ellipse(hx + 0.14, hz - 0.05, 0.016 + 0.008 * p["mouth"], 0.01 + 0.01 * p["mouth"], n=10, seed=seed + 4), M["mouth"], I, cyclic=True)
    else:
        G.seam(dh, G.bezier((hx + 0.09, hz - 0.05), (hx + 0.13, hz - 0.07), (hx + 0.17, hz - 0.045), n=5), M["ink"])
    drake_wing(db, M, f, -1, True)
    if p["shield"] > 0.3:                                                                 # the near wing swept forward as a shield
        G.seam(db, [(0.2, -0.02), (0.36, -0.2 * p["shield"])], M["ink"])
    if p["stars"] is not None:
        K.stars(dh, M, hx, hz + 0.28, 0.15, p["stars"])


def drake_poses():
    out = []
    for i in range(10):                                                                   # idle: a hover, slow wingbeats
        ph = TAU * i / 5
        out.append(dict(flap=0.65 + 0.35 * math.sin(ph), bob=0.03 * math.sin(ph + 1), tail_w=ph, blink={7: 1.0}.get(i, 0.0), look=(0.6, 0.0)))
    for i in range(12):                                                                   # fly: stronger beats, nose down
        ph = TAU * i / 6
        out.append(dict(flap=0.55 + 0.45 * math.sin(ph), bob=0.04 * math.sin(ph + 1), rock=-0.08, tail_w=2 * ph, look=(0.9, 0.0)))
    for i, sh in enumerate((0.2, 0.6, 1.0, 1.0, 0.9, 0.6, 0.3, 0.0)):                    # react: a wing-shielded turn
        out.append(dict(shield=sh, flap=0.7, rock=0.12 * sh, eye_pop=1.4 if i < 3 else 1.1, mouth=0.4 if i == 1 else 0.0, tail_w=i))
    out += [dict(q, shift=0.5 * q.get("shift", 0.0), sz=1 + 0.5 * (q.get("sz", 1.0) - 1)) for q in K.bump_clip()]   # half the stretch: the wings fit
    return out


# ---------------------------------------------------------------- floe moth (Deck 1)
def moth_wing(d, M, root, theta, L, W, far):
    c, s = math.cos(theta), math.sin(theta)
    n = (-s, c) if c < 0 else (s, -c)

    def at(t, w):
        return (root[0] + c * t * L + n[0] * w, root[1] + s * t * L + n[1] * w)
    shape = [at(0.0, -0.02), at(0.5, -0.05), at(0.95, 0.0)] + [at(1.0 - 0.1 * (1 - math.cos(a)), W * math.sin(a)) for a in [k * math.pi / 8 for k in range(1, 8)]] + \
        [at(0.4, W * 0.9), at(0.1, W * 0.5)]
    G.stroke(d, shape, M["cream_sh" if far else "cream_f"], 0.0, cyclic=True)
    G.stroke(d, [at(0.6, W * 0.75), at(0.95, W * 0.4), at(1.0, W * 0.2), at(0.98, W * 0.6), at(0.7, W * 0.95)], M["ice_f"], 0.0, cyclic=True)   # the ring-ice edge
    for t, w in ((0.7, 0.5), (0.45, 0.7)):
        G.seam(d, [at(0.05, 0.02), at(t * 0.7, w * W * 0.6), at(t, w * W)], M["ink"])
    G.stroke(d, shape, M["ink"], O if not far else I, cyclic=True)


def draw_floe_moth(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(flap=0.0))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    th = math.radians(115 + 55 * math.sin(p["flap"]))
    moth_wing(db, M, (0.0, 0.02), th + 0.3, 0.22, 0.11, True)
    body = G.lumpy_ellipse(-0.02, 0.0, 0.10, 0.045, n=20, lump=0.08, seed=seed + 1)
    G.stroke(db, body, M["butter_f"], 0.0, cyclic=True)
    for k in range(3):
        G.stroke(db, [(-0.09 + 0.05 * k, -0.04), (-0.07 + 0.05 * k, -0.04), (-0.065 + 0.05 * k, 0.04), (-0.085 + 0.05 * k, 0.04)], M["gold_f"], 0.0, cyclic=True)
    G.stroke(db, body, M["ink"], O, cyclic=True)
    H = K.turn((0.06, 0.0), p["head_rot"], p["head"], B)
    hx, hz = 0.10, 0.015
    dh = G.Xf(G.Xf(d, H), K.scale_about((hx, hz), 1.4))
    for k in (0, 1):
        a = math.radians(80 - 30 * k) + p["ears"] * 0.6
        tip = (hx - 0.01 + 0.015 * k + 0.08 * math.cos(a), hz + 0.03 + 0.08 * math.sin(a))
        G.stroke(dh, [(hx - 0.01 + 0.015 * k, hz + 0.03), tip], M["ink"], I)
        for t in (0.4, 0.7):
            q = (hx - 0.01 + 0.015 * k + t * (tip[0] - hx + 0.01 - 0.015 * k), hz + 0.03 + t * (tip[1] - hz - 0.03))
            G.stroke(dh, [(q[0] - 0.012, q[1] + 0.006), q, (q[0] + 0.012, q[1] + 0.006)], M["ink"], I)
    G.stroke(dh, G.lumpy_ellipse(hx, hz, 0.04, 0.036, n=16, seed=seed + 2), M["butter"], I, cyclic=True)
    K.eyes(dh, M, hx - 0.002, hz + 0.004, 0.012, 0.016, 0.022, p, seed)
    moth_wing(db, M, (-0.02, 0.02), th, 0.25, 0.12, False)
    if p["stars"] is not None:
        K.stars(dh, M, hx, hz + 0.1, 0.07, p["stars"])


def floe_moth_poses():
    out = []
    for i in range(8):
        ph = TAU * i / 4
        out.append(dict(flap=ph, bob=0.015 * math.sin(TAU * i / 8), rock=0.05 * math.sin(TAU * i / 8), ears=0.2 * math.sin(ph),
                        look=(0.4, 0.4), blink={5: 1.0}.get(i, 0.0)))
    for i in range(12):
        ph = TAU * i / 4
        out.append(dict(flap=ph, bob=0.02 * math.sin(ph + 1), rock=-0.12, ears=-0.3, look=(0.9, 0.0)))
    for i in range(8):
        ph = TAU * i / 2
        out.append(dict(flap=ph, shift=0.06 * (1 if i % 2 else -1), bob=0.03 * (i % 3 - 1), rock=0.3 * (1 if i % 2 else -1),
                        eye_pop=1.4 if i < 4 else 1.1, mouth=0.4 if i in (1, 2) else 0.0, ears=-0.5))
    out += [dict(q, flap=0.5, shift=0.4 * q.get("shift", 0.0)) for q in K.bump_clip()[:8]]
    return out


# ---------------------------------------------------------------- ringmite (space; swarms)
def draw_ringmite(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(wiggle=0.0, curl=0.0))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    c = p["curl"]
    r = 0.13 * (1 - 0.15 * c)
    for k in range(6):                                                                    # six stubby legs (tucked as it curls)
        a = math.radians(200 + 28 * k) + 0.15 * math.sin(p["wiggle"] + k * 1.7)
        L = 0.09 * (1 - 0.8 * c)
        base = (r * 0.8 * math.cos(a), r * 0.8 * math.sin(a))
        G.stroke(db, G.hose_outline([base, (base[0] + L * math.cos(a), base[1] + L * math.sin(a))], 0.018), M["slate_sh"], I, cyclic=True)
    shell = G.lumpy_ellipse(0.0, 0.0, r, r * (0.92 - 0.1 * c), n=24, lump=0.04, seed=seed + 1)
    G.stroke(db, shell, M["slate_f"], 0.0, cyclic=True)
    G.stroke(db, [q for q in shell if q[1] < -r * 0.3] + [(0.0, -r * 0.3)], M["slate_dp"], 0.0, cyclic=True)
    G.specks(db, [(-0.05, 0.06), (0.02, 0.08), (-0.08, -0.01)], M["gold"])
    for j in range(2):
        G.seam(db, G.bezier((-r * 0.7, r * (0.3 - 0.4 * j)), (0.0, r * (0.45 - 0.4 * j)), (r * 0.5, r * (0.35 - 0.4 * j)), n=5), M["ink"])
    G.stroke(db, shell, M["ink"], O, cyclic=True)
    if c < 0.85:
        H = K.turn((0.05, 0.0), p["head_rot"], p["head"], B)
        dh = G.Xf(d, H)
        K.eyes(dh, M, 0.06, 0.03, 0.022, 0.028, 0.04, p, seed)
        for k in (0, 1):                                                                  # antenna nubs
            G.stroke(dh, G.lumpy_ellipse(0.06 + 0.04 * k, r + 0.02, 0.012, 0.012, n=8, seed=seed + 5 + k), M["gold"], I, cyclic=True)
    if p["stars"] is not None:
        K.stars(db, M, 0.0, r + 0.05, 0.06, p["stars"])                                  # low enough for the 48 px frame


def ringmite_poses():
    out = []
    for i in range(8):                                                                    # idle: legs wiggle, a little spin
        ph = TAU * i / 8
        out.append(dict(wiggle=2 * ph, bob=0.01 * math.sin(ph), rock=0.1 * math.sin(ph), look=(0.6, 0.0), blink={5: 1.0}.get(i, 0.0)))
    for i in range(12):                                                                   # fly: a drift, legs paddling
        ph = TAU * i / 6
        out.append(dict(wiggle=3 * ph, bob=0.015 * math.sin(ph), rock=-0.15, look=(0.9, 0.0)))
    for i, c in enumerate((0.3, 0.7, 1.0, 1.0, 1.0, 0.7, 0.4, 0.1)):                     # react: curls into a ball
        out.append(dict(curl=c, rock=0.6 * c, eye_pop=1.4 if i == 0 else 1.0))
    out += [dict(q, shift=0.3 * q.get("shift", 0.0), head=(0.0, 0.0)) for q in K.bump_clip()[:8]]
    return out


SPECIES = {
    "helium_jelly": dict(draw=draw_helium_jelly, poses=jelly_poses, mats=mats, frame=(96, 112), seed=71, pivot=(0.5, 0.5),
                         clips=[("idle", 10, True), ("drift", 12, True), ("react", 8, False), ("bump", 10, False)],
                         self_check={"ink": "bell seams, the frill's lumpy rim, tendril hoses", "motion": "a pulse, tendrils trailing; react shoots up, deflating",
                                     "original": "our own pale-gold jelly with a frill and a soft glow; gentle, no teeth"},
                         ours="a pale-gold jelly that pulses through Saturn's warm decks and shoots upward, deflating, when bumped"),
    "hex_drake": dict(draw=draw_hex_drake, poses=drake_poses, mats=mats, frame=(192, 112), seed=72, pivot=(0.5, 0.5),
                      clips=[("idle", 10, True), ("fly", 12, True), ("react", 8, False), ("bump", 10, False)],
                      self_check={"ink": "wing bones, hexagon crest cells, the belly line, the snout", "motion": "a hover with slow beats; fly noses down; react: a wing-shielded turn",
                                  "original": "our own slate drake with a hexagon crest and a rounded smiling snout: no beak, no teeth (D-087)"},
                      ours="a slate-and-salmon drake with a hexagon crest that surfs the Hexagon's wind-walls"),
    "floe_moth": dict(draw=draw_floe_moth, poses=floe_moth_poses, mats=mats, frame=(64, 64), seed=73, pivot=(0.5, 0.5),
                      clips=[("idle", 8, True), ("fly", 12, True), ("react", 8, False), ("bump", 8, False)],
                      self_check={"ink": "wing veins, the ring-ice edge, body bands, feathery antennae", "motion": "quick flaps; react: a zig-zag scatter",
                                  "original": "our own cream floe moth with ring-ice wing edges; no eyespots"},
                      ours="a little cream moth that flutters over the ice floes, its wings edged like Saturn's rings"),
    "ringmite": dict(draw=draw_ringmite, poses=ringmite_poses, mats=mats, frame=(48, 48), seed=74, pivot=(0.5, 0.5),
                     clips=[("idle", 8, True), ("fly", 12, True), ("react", 8, False), ("bump", 8, False)],
                     self_check={"ink": "shell plate seams, gold flecks, leg stubs", "motion": "legs wiggle; react: curls into a ball",
                                 "original": "our own round ring mite; it never bites on screen (the hull damage is UNITY's)"},
                     ours="a round slate mite that swarms the ring lanes and curls into a ball when poked"),
}
HABITAT = {"helium_jelly": "deck2", "hex_drake": "hexagon", "floe_moth": "deck1", "ringmite": "-"}
SOURCES = os.path.join(os.path.dirname(HERE), "sources", "creatures")


def build(name, out=None):
    """The source .blend for one Saturn creature (inside Blender): one GP object, one drawing per frame, clip markers."""
    import bpy
    sp = SPECIES[name]
    out = out or os.path.join(SOURCES, f"saturn_{name}_v3.blend")
    scene = G.new_scene()
    coll = G.collection(name)
    ob, gp = G.gp_object(name, coll)
    M = sp["mats"](gp, name)
    layer = gp.layers.new("art")
    for f, pose in enumerate(sp["poses"]()):
        sp["draw"](G.drawing(layer, f + 1), M, pose, seed=5 * f)
    G.mark_clips(scene, [(c, n) for c, n, _l in sp["clips"]])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


def build_helium_jelly(out=None):          # manifest build_fn: render.py passes the source path
    return build("helium_jelly", out)


def build_hex_drake(out=None):
    return build("hex_drake", out)


def build_floe_moth(out=None):
    return build("floe_moth", out)


def build_ringmite(out=None):
    return build("ringmite", out)


def entry_for(name):
    sp = SPECIES[name]
    return {"key": f"creatures/saturn/{name}", "style": "v3", "source": f"sources/creatures/saturn_{name}_v3.blend",
            "build": "scripts/build_creatures_saturn_v3.py", "build_fn": f"build_{name}", "collection": name,
            "frame": list(sp["frame"]), "pivot": list(sp.get("pivot", (0.5, 0.5))), "facing": "right", "squash_root": True,
            "planet": "saturn", "seed": sp["seed"], "bg_scene": HABITAT[name], "beside": "characters/surveyor/side",
            "review_name": f"b157_saturn_{name}", "clips": [{"name": c, "frames": n, "loop": lp} for c, n, lp in sp["clips"]],
            "self_check": dict(sp["self_check"], style="the B-132 kit (Gus's construction); LEAD judges"), "ours": sp["ours"],
            "replaces_v2": name != "ringmite", "note": "B-157 design (Saturn creature re-ink); off the ground: pivot at the body centre, the travel clip at index 1"}


def preview(out_dir, name="helium_jelly"):
    """The export's review layout from exact frames (as_object ids, ss 4) on a placeholder background (centre pivots: all
    four edges checked)."""
    import json
    import numpy as np
    from meridian import fakegp, pngio
    import gp_raster as GR
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    sp = SPECIES[name]
    fw, fh = sp["frame"]
    piv = sp.get("pivot", (0.5, 0.5))
    frames, widths = [], []
    for f, pose in enumerate(sp["poses"]()):
        gp = fakegp.FakeGP()
        M = mats(gp, name)
        d = fakegp.FakeDrawing()
        sp["draw"](d, M, pose, seed=5 * f)
        img, w = GR.render_frame(fakegp.strokes_of(d, gp, as_object=(name, "art")), fw, fh, 64, piv, ss=4, seed=sp["seed"] * 1000 + f + 1)
        frames.append(img)
        widths += w
    cols = v3.columns_for(fw, len(frames))
    rows = -(-len(frames) // cols)
    sheet = np.zeros((rows * fh + (rows - 1) * 4, min(cols, len(frames)) * fw + (min(cols, len(frames)) - 1) * 4, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + 4):r * (fh + 4) + fh, c * (fw + 4):c * (fw + 4) + fw] = im
    anims, s_ = [], 0
    for c, n, lp in sp["clips"]:
        anims.append({"name": c, "start": s_, "length": n, "loop": lp, **({"loop_from": 0} if lp else {})})
        s_ += n
    meta = {"key": f"creatures/saturn/{name}", "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": 4,
            "frames": len(frames), "fps": 12, "pivot": list(piv), "facing": "right", "ppu": 64, "animations": anims, "squash_root": True}
    problems = v3.validate_sheet(meta, sheet.shape)
    clipped = [i for i, im in enumerate(frames) if im[:2, :, 3].any() or im[-2:, :, 3].any() or im[:, :2, 3].any() or im[:, -2:, 3].any()]
    if clipped:
        problems.append(f"frames {clipped[:8]} touch the 2 px edge")
    dd = os.path.join(out_dir, "b157_saturn")
    os.makedirs(dd, exist_ok=True)
    png = os.path.join(dd, f"{name}_color.png")
    nb = pngio.write_png(png, sheet)
    with open(os.path.join(dd, f"{name}.json"), "w", encoding="utf-8", newline="\n") as f_:
        json.dump(meta, f_, indent=2)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    stats = {"outer_px": (min(w[1] for w in outer), max(w[2] for w in outer)), "inner_px": (min(w[1] for w in inner), max(w[2] for w in inner)),
             "inner_n": len(inner), "palette": v3.palette_hits(sheet, "saturn"), "problems": problems,
             "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": nb // 1024}
    out = os.path.join(out_dir, f"review_b157_saturn_{name}_preview.png")
    boxes = review.v3_sheet_review(entry_for(name), meta, frames, png, out, stats)
    print(name, f"sheet {sheet.shape[1]}x{sheet.shape[0]} {nb // 1024} KB, ink {stats['outer_px'][0]:.2f}-{stats['outer_px'][1]:.2f} / "
          f"{stats['inner_px'][0]:.2f}-{stats['inner_px'][1]:.2f}, palette {stats['palette'][0] * 100:.1f}% {stats['palette'][1][:3]}, "
          f"problems {problems or '-'}, boxes not x: {','.join(k for k, (mk, _n) in boxes.items() if mk != 'x') or '-'}")


if __name__ == "__main__":
    for _n in (sys.argv[2:] or list(SPECIES)):
        preview(sys.argv[1], _n)
