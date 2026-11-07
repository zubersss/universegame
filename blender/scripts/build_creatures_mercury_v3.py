"""B-145 (C2 Mercury design prep): Mercury creature design previews on the B-132 kit (build_creatures_earth_v3: posed body,
pie eyes, dizzy stars), in the Mercury palette (D-130). Faces kept, friendly or neutral, no teeth (D-087 / D-101).

  shadewyrm  160x80, a shy ice burrower of the polar craters (see its section): idle peeks over its den
             props/mercury/ice_burrow (D-126, drawn by UNITY in front on the same pivot), walk 12, react 8 (ducks), bump 10,
             idle_open 10.
  glassback  176x112, the silicate grazer riding the twilight band (see its section): idle 10 (grazing), walk 12,
             react 8 (the shards ring up), bump 10, flee 12.
  cinderling 80x64, small, swarms at dawn (see its section): idle 8, walk 12 (a scurry), react 8 (a hop with a spark
             puff), bump 10, flee 12.
  flarewing  124x124, a flyer that feeds on flares ("aggressive" becomes excited, D-087): a violet moth-bat with ember
             belly, membrane wings on drawn ribs, gold flare-catching vanes at the wing tips and a forked gold-tipped
             tail. Pivot at the body centre (the B-135 swimmers' rule for creatures that leave the ground); clips idle 10
             (a hover), fly 12 (index 1: the travel clip, like the swimmers' swim), react 8 (a loop-de-loop), bump 10,
             flare_dance 12 (during a flare: fast flaps, the vanes glow, sparks spiral).

Design previews only; Mercury exports wait for their cards (B-145 is prep).

  python -I build_creatures_mercury_v3.py <preview dir> [names]      lock-free (meridian.fakegp; exact stroke ids)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_earth_v3 as K  # noqa: E402  (the kit; gp_draw real in Blender, fakegp outside)
from meridian import v3  # noqa: E402

G = K.G
P = v3.PALETTES["mercury"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "mercury")


def DP(h):
    return v3.deep_of(h, "mercury")


def mats(gp, sp):
    def m(name, **kw):
        return G.mat(gp, f"{sp}_{name}", **kw)
    out = {"ink": m("ink", fill=None), "pupil": m("pupil", fill=G.INK, ink=False), "eye": m("eye_white", fill=P["offwhite"]),
           "mouth": m("mouth", fill=DP(P["red"])), "star": m("star", fill=P["mustard"]),
           "puff": m("puff", fill=P["offwhite"]), "puff_sh": m("puff_mid", fill=SH(P["offwhite"]), ink=False),
           "glow": m("glow", fill=P["mustard"], ink=False, fill_alpha=0.30)}
    for key, slot in (("violet", "sky"), ("ember", "red"), ("gold", "mustard"), ("ice", "teal"), ("white", "offwhite"),
                      ("sage", "green"), ("slate", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
        out[key + "_b"] = m(key + "_behind", fill=h, behind=True)
    legs = {"glassback": "offwhite", "cinderling": "red"}.get(sp, "sky")              # the kit's legs_pass / paw names
    out["leg"], out["coat"] = m("leg", fill=SH(P[legs])), m("coat", fill=SH(P[legs]))
    out["leg_far"], out["far"] = m("leg_far", fill=DP(P[legs])), m("far", fill=DP(P[legs]))
    out["claw"] = m("claw", fill=P["offwhite"], behind=True)
    return out


# ---------------------------------------------------------------- flarewing
def wing(d, M, root, theta, L, far, vane, seed):
    """A membrane wing from `root` toward angle theta (radians from +x): a bowed leading edge, a scalloped trailing
    edge between three ribs, the mid tone at the root, a gold vane at the tip (it glows during a flare)."""
    c, s = math.cos(theta), math.sin(theta)
    n = (-s, c) if c < 0 else (s, -c)                                # the trailing side: away from the body's front

    def at(t, w):
        return (root[0] + c * t * L + n[0] * w + 0.03 * math.sin(math.pi * t) * -n[0],
                root[1] + s * t * L + n[1] * w + 0.03 * math.sin(math.pi * t) * -n[1])
    tip = at(1.0, 0.0)
    trail = []
    for t, w in ((0.90, 0.12), (0.70, 0.19), (0.52, 0.17), (0.32, 0.21), (0.12, 0.17), (0.0, 0.08)):   # a soft scallop
        trail.append(at(t, w))
    lead = [at(t, 0.0) for t in (0.0, 0.25, 0.5, 0.75)]
    shape = lead + [tip] + trail
    G.stroke(d, shape, M["violet_sh"] if far else M["violet_f"], 0.0, cyclic=True)
    G.stroke(d, lead[:2] + [at(0.3, 0.17), at(0.12, 0.18), at(0.0, 0.08)], M["violet_dp"] if far else M["violet_sh"], 0.0, cyclic=True)
    for t, w in ((0.70, 0.18), (0.32, 0.20)):                                           # two ribs
        G.seam(d, [at(0.05, 0.01), at(t * 0.8, w * 0.5), at(t, w - 0.015)], M["ink"])
    G.stroke(d, shape, M["ink"], O, cyclic=True)
    vt = (tip[0] + c * 0.05, tip[1] + s * 0.05)
    if vane > 0.05:
        G.stroke(d, G.lumpy_ellipse(vt[0], vt[1], 0.07 + 0.04 * vane, 0.07 + 0.04 * vane, n=14, lump=0.04, seed=seed + 9), M["glow"], 0.0, cyclic=True)
    vpts = [(vt[0] + 0.07 * math.cos(theta + a), vt[1] + 0.07 * math.sin(theta + a)) for a in (-0.7, -0.25, 0.2, 0.7)]
    G.stroke(d, [tip] + vpts, M["gold" if not far else "gold_sh"], I, cyclic=True)        # the flare-catching vane


def draw_flarewing(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(flap=0.0, vane=0.0, sparks=None, tail2=0.0))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    theta = math.radians(147.5 + 52.5 * math.sin(p["flap"]))                              # 95 deg (up) .. 200 deg (down, back)
    wing(db, M, (0.02, 0.06), theta + 0.25, 0.58, True, p["vane"], seed)                  # the far wing, a step behind
    for k in (0, 1):                                                                      # the forked tail, gold tips
        a = math.pi + 0.25 * (k - 0.5) + p["tail"] + 0.15 * math.sin(p["tail2"] + k)
        base = (-0.20, 0.0)
        tip = (base[0] + 0.36 * math.cos(a), base[1] + 0.36 * math.sin(a))
        G.stroke(db, G.hose_outline(G.bezier(base, ((base[0] + tip[0]) / 2, base[1] + 0.05 * (k - 0.5)), tip, n=6), 0.03), M["violet_b"], I, cyclic=True)
        G.stroke(db, G.lumpy_ellipse(tip[0], tip[1], 0.035, 0.025, n=10, seed=seed + 20 + k, rot=a), M["gold"], I, cyclic=True)
    body = G.lumpy_ellipse(-0.02, 0.0, 0.22, 0.10, n=30, lump=0.03, seed=seed + 1)
    G.stroke(db, body, M["violet_f"], 0.0, cyclic=True)
    G.stroke(db, [q for q in body if q[1] < -0.02] + [(0.18, -0.02), (-0.2, -0.02)], M["ember_f"], 0.0, cyclic=True)   # ember belly
    for k in range(3):
        G.seam(db, [(-0.12 + 0.08 * k, -0.075), (-0.10 + 0.08 * k, -0.035)], M["ink"])   # belly bands
    G.specks(db, [(-0.08, 0.05), (0.04, 0.06)], M["ink"])
    G.stroke(db, body, M["ink"], O, cyclic=True)
    H = K.turn((0.16, 0.02), p["head_rot"], p["head"], B)
    hx, hz = 0.25, 0.04
    dh = G.Xf(G.Xf(d, H), K.scale_about((hx, hz), 1.3))                                   # the head 1.3x (era proportions)
    for k in (0, 1):                                                                      # two little gold feelers
        a = math.radians(70 - 35 * k) + p["ears"] * 0.6
        G.stroke(dh, G.hose_outline(G.bezier((hx - 0.02 + 0.03 * k, hz + 0.07), (hx + 0.0 + 0.03 * k, hz + 0.13), (hx + 0.1 * math.cos(a) + 0.03 * k, hz + 0.07 + 0.12 * math.sin(a)), n=5), 0.014), M["gold_b"], I, cyclic=True)
    G.stroke(dh, G.lumpy_ellipse(hx, hz, 0.095, 0.085, n=24, lump=0.03, seed=seed + 2), M["violet"], O, cyclic=True)
    G.stroke(dh, G.lumpy_ellipse(hx + 0.075, hz - 0.02, 0.03, 0.025, n=10, seed=seed + 3), M["ember"], I, cyclic=True)   # a round snout
    if p["mouth"] > 0.05:
        G.stroke(dh, G.lumpy_ellipse(hx + 0.05, hz - 0.055, 0.012 + 0.008 * p["mouth"], 0.008 + 0.01 * p["mouth"], n=10, seed=seed + 4), M["mouth"], I, cyclic=True)
    else:
        G.seam(dh, G.bezier((hx + 0.07, hz - 0.05), (hx + 0.04, hz - 0.06), (hx + 0.01, hz - 0.05), n=4), M["ink"])
    K.eyes(dh, M, hx - 0.01, hz + 0.02, 0.022, 0.03, 0.042, p, seed)
    wing(db, M, (-0.02, 0.05), theta, 0.62, False, p["vane"], seed + 5)                   # the near wing, in front
    if p["sparks"] is not None:                                                           # flare sparks spiral round it
        G.specks(db, [(0.45 * math.cos(p["sparks"] + k * 2.1), 0.35 * math.sin(p["sparks"] + k * 2.1)) for k in range(3)], M["ink"])
        for k in range(2):
            a = p["sparks"] + 1.0 + k * math.pi
            G.stroke(db, K.star(0.4 * math.cos(a), 0.3 * math.sin(a), 0.035, rot=a), M["gold"], I, cyclic=True)
    if p["stars"] is not None:
        K.stars(dh, M, hx, hz + 0.2, 0.14, p["stars"])


def flarewing_poses():
    out = []
    for i in range(10):                                                                   # idle: a hover, two slow flaps
        ph = TAU * i / 5
        out.append(dict(flap=ph, bob=0.03 * math.sin(ph + math.pi / 2), rock=0.05 * math.sin(ph), tail=0.1 * math.sin(ph - 1.0),
                        tail2=ph, ears=0.2 * math.sin(ph), blink={7: 0.6, 8: 1.0}.get(i, 0.0), look=(0.7, -0.1)))
    for i in range(12):                                                                   # fly: forward, nose a touch down
        ph = TAU * i / 6
        out.append(dict(flap=ph, bob=0.025 * math.sin(ph + math.pi / 2), rock=-0.10 + 0.04 * math.sin(ph), tail=-0.12, tail2=ph,
                        ears=-0.3, look=(0.9, 0.0)))
    for i in range(8):                                                                    # react: a loop-de-loop
        out.append(dict(flap=TAU * i / 4, rock=TAU * i / 8, eye_pop=1.3 if i < 3 else 1.1, mouth=0.4 if 1 <= i <= 4 else 0.0,
                        tail=0.2, tail2=i, ears=-0.4))
    out += [dict(q, flap=0.0, shift=0.5 * q.get("shift", 0.0), ears=q.get("ears", 0.0)) for q in K.bump_clip()]   # wings held up-back, half the knock
    for i in range(12):                                                                   # flare_dance: fast flaps, glowing vanes
        ph = TAU * i / 4
        out.append(dict(flap=ph, bob=0.04 * math.sin(TAU * i / 6), rock=0.12 * math.sin(TAU * i / 12), vane=0.6 + 0.4 * math.sin(TAU * i / 3),
                        sparks=TAU * i / 12, tail=0.15 * math.sin(ph), tail2=ph, eye_pop=1.2, mouth=0.5, ears=0.4 * math.sin(ph), look=(0.6, 0.3)))
    return out


# ---------------------------------------------------------------- shadewyrm (ice burrower, polar craters; D-126 den)
# A shy segmented ice wyrm: frost-capped teal segments tapering to the tail, a slate underside, a big round head with
# pie eyes, a frost brow plate and two frost nubs; no legs: it humps along like a caterpillar. Idle peeks over its den,
# props/mercury/ice_burrow (a faceted ice-block mound, build_props_mercury_v3), which UNITY draws IN FRONT on the same
# pivot (D-126: creature art never contains terrain or props); react ducks; idle_open is the whole-body pause in the open.

WYRM_N = 6
DEN_TOP = [(-0.62, 0.0), (-0.52, 0.16), (-0.30, 0.24), (-0.16, 0.20), (0.02, 0.31), (0.22, 0.27), (0.36, 0.18), (0.54, 0.12), (0.62, 0.0)]


def den_top(x):
    """The ice burrow's top line above x (piecewise linear through DEN_TOP; 0 outside)."""
    for (x0, z0), (x1, z1) in zip(DEN_TOP, DEN_TOP[1:]):
        if x0 <= x <= x1:
            return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    return 0.0


def wyrm_segment(d, M, cx, cz, r, k, seed):
    seg = G.lumpy_ellipse(cx, cz, r, r * 0.92, n=20, lump=0.03, seed=seed + k)
    G.stroke(d, seg, M["ice_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in seg if q[1] < cz - 0.35 * r] + [(cx, cz - 0.35 * r)], M["slate_sh"], 0.0, cyclic=True)     # slate underside
    cap = [q for q in seg if q[1] > cz + 0.25 * r]
    if len(cap) > 2:                                                                     # the frost cap, a scalloped edge
        edge = [(cx + r * 0.8 * math.cos(a), cz + 0.25 * r + 0.04 * r * math.sin(5 * a + k)) for a in [math.pi * (1 - t / 8) for t in range(9)]]
        G.stroke(d, cap + edge[::-1], M["white_f"], 0.0, cyclic=True)
        G.seam(d, edge, M["ink"])
    G.specks(d, [(cx - 0.3 * r, cz - 0.05 * r), (cx + 0.25 * r, cz + 0.05 * r)], M["ink"])
    G.stroke(d, seg, M["ink"], O, cyclic=True)


def wyrm_head(d, M, hx, hz, p, seed):
    def R(dx, dz):
        return (hx + dx, hz + dz)
    for k in (0, 1):                                                                     # frost nubs
        G.stroke(d, G.lumpy_ellipse(*R(-0.06 + 0.08 * k, 0.17), 0.03, 0.045, n=10, seed=seed + 60 + k, rot=0.3 - 0.6 * k), M["white"], I, cyclic=True)
    head = G.lumpy_ellipse(hx, hz, 0.19, 0.17, n=32, lump=0.03, seed=seed + 2)
    G.stroke(d, head, M["ice_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in head if q[1] < hz - 0.07] + [R(0.0, -0.07)], M["slate_sh"], 0.0, cyclic=True)
    brow = [q for q in G.lumpy_ellipse(hx - 0.01, hz + 0.02, 0.19, 0.16, n=32, lump=0.04, seed=seed + 3) if q[1] > hz + 0.08]
    G.stroke(d, brow + [R(0.12, 0.08), R(-0.15, 0.08)], M["white_f"], 0.0, cyclic=True)               # the frost brow plate
    G.seam(d, [R(-0.15, 0.08), R(0.12, 0.08)], M["ink"])
    G.stroke(d, head, M["ink"], O, cyclic=True)
    if p["mouth"] > 0.05:
        G.stroke(d, G.lumpy_ellipse(*R(0.10, -0.08), 0.015 + 0.01 * p["mouth"], 0.01 + 0.012 * p["mouth"], n=10, seed=seed + 4), M["mouth"], I, cyclic=True)
    else:
        G.seam(d, G.bezier(R(0.15, -0.06), R(0.10, -0.085), R(0.04, -0.075), n=5), M["ink"])
    K.eyes(d, M, *R(0.02, 0.0), 0.04, 0.052, 0.075, p, seed)
    if p["stars"] is not None:
        K.stars(d, M, hx, hz + 0.3, 0.16, p["stars"])


def draw_shadewyrm(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(hole=None, hump=0.0, curl=0.0))
    p.update(pose or {})
    e = p["hole"]
    if e is not None:                                                                    # at the den: segments rise behind its top
        hx, hz = 0.10 + 0.04 * e, 0.22 + 0.42 * e + p["bob"]
        spine = G.bezier((-0.06, 0.17), (-0.04, 0.20 + 0.15 * e), (hx - 0.06, max(hz - 0.18, 0.17)), n=5)     # its base and its end stay above the ground
        for k, (x, z) in enumerate(spine[:-1]):
            wyrm_segment(d, M, x, z, 0.15 + 0.01 * k, k, seed)
        dk = G.Xf(d, K.turn((hx - 0.1, hz - 0.08), p["head_rot"], (0.0, 0.0), K.scale_about((hx, hz), 1.15)))
        wyrm_head(dk, M, hx, hz, p, seed)
        return
    B = K.Body(p, (0.0, 0.2))
    db = G.Xf(d, B)
    xs = [-0.86 + 0.27 * k for k in range(WYRM_N)]
    for k, x in enumerate(xs):                                                           # tail first, so each overlaps the one behind
        r = 0.09 + 0.09 * k / (WYRM_N - 1)
        z = r + 0.015 + 0.07 * max(0.0, math.sin(p["hump"] - 0.9 * k)) + 0.08 * p["curl"] * (WYRM_N - k) / WYRM_N
        wyrm_segment(db, M, x, z, r, k, seed)
    hx, hz = 0.74, 0.24 + 0.05 * max(0.0, math.sin(p["hump"] - 0.9 * WYRM_N))
    H = K.turn((0.58, 0.2), p["head_rot"], p["head"], B)
    dk = G.Xf(G.Xf(d, H), K.scale_about((hx, hz), 1.15))
    wyrm_head(dk, M, hx, hz, p, seed)


def shadewyrm_poses():
    out = []
    for i in range(10):                                                                  # idle at the den: peek, look about, blink
        ph = TAU * i / 10
        out.append(dict(hole=1.0 + 0.03 * math.sin(ph), bob=0.01 * math.sin(ph), head_rot=0.06 * math.sin(ph - 0.6),
                        look=(0.8, 0.0) if i < 4 else ((-0.6, 0.1) if i in (6, 7, 8) else (0.2, 0.0)), blink={4: 0.6, 5: 1.0}.get(i, 0.0)))
    for i in range(12):                                                                  # walk: a hump travels tail to head
        ph = TAU * i / 12
        out.append(dict(hump=ph * 1.0 + 1.5, bob=0.0, sz=1 + 0.015 * math.cos(2 * ph), head_rot=0.05 * math.sin(ph), look=(0.9, -0.1)))
    out += [dict(hole=1.0, eye_pop=1.3, look=(0.9, 0.0)),                              # react: startle, then duck behind the burrow
            dict(hole=1.1, eye_pop=1.6, mouth=0.5, head_rot=0.06),
            dict(hole=0.7, eye_pop=1.3, mouth=0.3),
            dict(hole=0.35, eye_pop=1.2),
            dict(hole=0.12, eye_pop=1.35, look=(0.6, 0.0)),
            dict(hole=0.12, look=(0.9, 0.0)),
            dict(hole=0.1, blink=1.0),
            dict(hole=0.15, look=(0.3, 0.0))]
    out += [dict(q, curl=0.4 * q.get("tail", 0.0), rock=0.4 * q.get("rock", 0.0)) for q in K.bump_clip()]   # a long body: a softer pitch
    for i in range(10):                                                                  # idle_open: a whole-body pause in the open
        ph = TAU * i / 10
        _ph, q = K.idle_common(i, 10)
        q.update(hump=1.5 + 0.4 * math.sin(ph), curl=0.3 + 0.2 * math.sin(ph - 1.0), head_rot=0.05 * math.sin(ph - 0.6),
                 look=(0.8, 0.0) if i < 5 else (-0.5, 0.1), blink={7: 0.6, 8: 1.0}.get(i, 0.0))
        out.append(q)
    return out


# ---------------------------------------------------------------- glassback (silicate grazer of the twilight band)
# A slow stocky grazer: a pale regolith-grey hide with a slate underside, thick hose legs on round feet, a long soft
# snout it nibbles the regolith with, pie eyes; five cold-teal crystal shards along its back (drawn facets and an
# off-white glint, no translucency) that ring and lift when it is startled. ~1.8 x 1.1 m (the shards to ~1.4 m).

GLASS = dict(hips=[(-0.30, 0.42), (0.34, 0.44), (-0.38, 0.40), (0.26, 0.42)], feet=[-0.34, 0.40, -0.44, 0.32],
             ankle=0.06, leg_w=0.12, bend_hind=-0.10, bend_front=0.06, foot="paw", paw=(0.08, 0.04, 2, 0), dangle=0.3)
GB = (0.0, 0.52, 0.55, 0.26)
SHARDS = [(-0.40, 0.20, 0.10), (-0.20, 0.30, 0.12), (0.02, 0.36, 0.13), (0.22, 0.30, 0.12), (0.40, 0.20, 0.09)]   # x, height, half width


def shard(d, M, base, h, w, ang, glint, seed):
    """An angular crystal: a hexagonal prism tip on `base` toward ang; a light facet, a mid facet, the glint."""
    c, s = math.cos(ang), math.sin(ang)

    def at(u, v):
        return (base[0] + c * u * h - s * v * w, base[1] + s * u * h + c * v * w)
    shape = [at(-0.15, -1.0), at(0.75, -1.0), at(1.0, -0.25), at(1.0, 0.2), at(0.75, 1.0), at(-0.15, 1.0)]
    G.stroke(d, shape, M["ice_f"], 0.0, cyclic=True)
    G.stroke(d, [at(-0.15, 0.1), at(0.75, 0.1), at(1.0, 0.2), at(0.75, 1.0), at(-0.15, 1.0)], M["ice_sh"], 0.0, cyclic=True)   # the far facet
    G.seam(d, [at(0.0, 0.1), at(0.75, 0.1), at(1.0, -0.05)], M["ink"])
    t = 0.3 + 0.4 * glint
    G.stroke(d, [at(t, -0.75), at(t + 0.18, -0.75), at(t + 0.12, -0.45), at(t - 0.04, -0.45)], M["white_f"], 0.0, cyclic=True)
    G.stroke(d, shape, M["ink"], O, cyclic=True)


def draw_glassback(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(chime=0.0, glint=0.0, graze=0.0))
    p.update(pose or {})
    cx, cz, rx, rz = GB
    B = K.Body(p, (cx, cz))
    db = G.Xf(d, B)
    K.legs_pass(d, M, B, GLASS, p, far=True)
    for k, (x, h, w) in enumerate(SHARDS):                                                # shards behind the hide's top line
        top = cz + rz * math.sqrt(max(0.0, 1 - (x / rx) ** 2))
        normal = math.atan2((top - cz) / rz ** 2, x / rx ** 2)
        hh = h * (1 + 0.35 * p["chime"]) * (1 + 0.04 * math.sin(p["glint"] * 6 + k))
        shard(db, M, (x, top - 0.06), hh + 0.06, w, normal + math.radians(8), (p["glint"] + 0.3 * k) % 1.0, seed + k)
        if p["chime"] > 0.3:                                                               # ring marks (a chime, never a zap)
            tip = (x + math.cos(normal) * (hh + 0.12), top + math.sin(normal) * (hh + 0.12))
            G.stroke(db, [(tip[0] - 0.05, tip[1]), (tip[0] - 0.03, tip[1] + 0.03)], M["ink"], I)
            G.stroke(db, [(tip[0] + 0.05, tip[1]), (tip[0] + 0.03, tip[1] + 0.03)], M["ink"], I)
    body = [(x, max(z, 0.30)) for x, z in K.body_shape(cx, cz, rx, rz, seed + 1, chest=0.03)]
    G.stroke(db, body, M["white_sh"], 0.0, cyclic=True)                                    # the pale regolith-grey hide
    n = len(body)
    low = [body[i] for i in range(n) if math.sin(TAU * i / n) < -0.40]
    G.stroke(db, low + [(cx + (x - cx) * 0.9, cz + (z - cz) * 0.4) for x, z in low][::-1], M["slate_sh"], 0.0, cyclic=True)
    G.stroke(db, [q for q in body if q[0] < -0.35] + [(-0.35, cz)], M["white_dp"], 0.0, cyclic=True)
    for k in range(4):                                                                    # hide folds + specks
        x = -0.30 + 0.18 * k
        G.seam(db, [(x, cz + 0.12), (x + 0.03, cz - 0.02), (x - 0.01, cz - 0.14)], M["ink"])
    G.specks(db, [(-0.2, 0.6), (0.1, 0.62), (0.3, 0.55), (-0.4, 0.5)], M["ink"])
    G.stroke(db, body, M["ink"], O, cyclic=True)
    K.legs_pass(d, M, B, GLASS, p, far=False)
    J = (0.46, 0.56)
    hx, hz = 0.66, 0.56 - 0.18 * p["graze"]
    H = K.turn(J, p["head_rot"] - 0.35 * p["graze"], p["head"], B)
    dk = G.Xf(G.Xf(d, H), K.scale_about((hx, hz), 1.2))

    def R(dx, dz):
        return (hx + dx, hz + dz)
    G.stroke(dk, G.lumpy_ellipse(hx, hz, 0.15, 0.13, n=28, lump=0.03, seed=seed + 2), M["white_sh"], O, cyclic=True)
    snout = G.bezier(R(0.06, 0.06), R(0.18, 0.04), R(0.27, -0.02 + 0.01 * p["sniff"]), n=8) + \
        G.bezier(R(0.29, -0.06), R(0.25, -0.11), R(0.17, -0.11), n=5) + G.bezier(R(0.12, -0.11), R(0.05, -0.10), R(0.0, -0.08), n=5)
    G.stroke(dk, snout, M["white_sh"], O, cyclic=True)
    G.stroke(dk, G.lumpy_ellipse(*R(0.265, -0.035), 0.03, 0.025, n=10, seed=seed + 5), M["slate"], I, cyclic=True)   # the nose pad
    G.seam(dk, [R(0.12, 0.03), R(0.20, 0.01)], M["ink"])
    if p["mouth"] > 0.05:
        G.stroke(dk, G.lumpy_ellipse(*R(0.18, -0.10), 0.016 + 0.01 * p["mouth"], 0.01 + 0.012 * p["mouth"], n=10, seed=seed + 6), M["mouth"], I, cyclic=True)
    else:
        G.seam(dk, G.bezier(R(0.25, -0.085), R(0.18, -0.095), R(0.10, -0.085), n=5), M["ink"])
    K.eyes(dk, M, *R(0.02, 0.03), 0.032, 0.042, 0.06, p, seed)
    for k in (0, 1):                                                                      # two small round ears
        G.stroke(dk, G.lumpy_ellipse(*R(-0.09 + 0.06 * k, 0.12), 0.04, 0.03, n=10, seed=seed + 7 + k, rot=0.4 + p["ears"]), M["white_dp" if k == 0 else "white_sh"], I, cyclic=True)
    if p["stars"] is not None:
        K.stars(dk, M, hx, hz + 0.25, 0.16, p["stars"])


def glassback_poses():
    out = []
    for i in range(10):                                                                   # idle: grazing, nibbles twice, glints walk
        ph, q = K.idle_common(i, 10)
        q.update(graze=0.5 + 0.5 * math.sin(ph - 1.0), sniff=1.0 if i in (2, 3, 7) else 0.0, glint=i / 10, ears=0.1 * math.sin(ph),
                 blink={5: 0.6, 6: 1.0}.get(i, 0.0), look=(0.6, -0.3))
        out.append(q)
    for i in range(12):                                                                   # walk: a slow amble
        ph = TAU * i / 12
        out.append(dict(legs=K.walk_legs(ph, 0.11, 0.05), bob=0.012 * math.cos(2 * ph), sz=1 + 0.02 * math.cos(2 * ph),
                        rock=0.02 * math.sin(ph), head_rot=0.04 * math.sin(2 * ph - 0.5), glint=i / 12, graze=0.15, look=(0.9, -0.1)))
    out += [dict(sz=0.95, look=(0.7, 0.0), chime=0.2), dict(sz=0.92, chime=0.5, eye_pop=1.2),           # react: the shards ring up
            dict(sz=1.06, chime=1.0, eye_pop=1.5, mouth=0.4, head_rot=0.12, glint=0.3), dict(sz=1.04, chime=0.9, eye_pop=1.4, glint=0.6, head_rot=0.12),
            dict(sz=1.02, chime=0.6, eye_pop=1.2, glint=0.9), dict(chime=0.35, glint=0.2, look=(0.9, 0.2)), dict(chime=0.15, glint=0.5), dict(chime=0.0)]
    out += K.bump_clip(lambda f: dict(chime=0.3 if f.get("stars") is not None else 0.0))
    for i in range(12):                                                                   # flee: a lumbering trot
        legs, bob, sz, rock = K.gallop(i / 6, A=0.5, lz=0.45)
        out.append(dict(legs=legs, bob=bob, sz=sz, rock=0.6 * rock, lean=0.04, head_rot=-0.05, chime=0.2, glint=i / 12, ears=0.4, look=(0.9, 0.0)))
    return out


# ---------------------------------------------------------------- cinderling (small, swarms at dawn)
# A small ember beetle: a domed ember shell with crust plates and cracks that show a gold glow tone (no emission), a round
# head with big pie eyes, two gold spark feelers, stubby hose legs; it scurries, hops with a spark puff when startled.
# ~0.5 m. Swarms are UNITY's spawner.

CINDER = dict(hips=[(-0.08, 0.13), (0.08, 0.14), (-0.11, 0.12), (0.05, 0.13)], feet=[-0.13, 0.12, -0.16, 0.09],
              ankle=0.035, leg_w=0.07, bend_hind=-0.10, bend_front=0.05, foot="paw", paw=(0.04, 0.02, 1, 0), dangle=0.1)   # wide enough for the fill to show
CB = (0.0, 0.19, 0.17, 0.11)


def draw_cinderling(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(spark=None))
    p.update(pose or {})
    cx, cz, rx, rz = CB
    B = K.Body(p, (cx, cz))
    db = G.Xf(d, B)
    if p["spark"] is not None:                                                             # a spark puff behind (react, flee)
        t = p["spark"]
        r = 0.035 + 0.04 * t
        blob = G.lumpy_ellipse(-0.18 - 0.12 * t, 0.06 + 0.10 * t, r * 1.2, r, n=12, lump=0.12, seed=seed + 30)
        G.stroke(d, blob, M["white"], I, cyclic=True)
        G.specks(d, [(-0.22 - 0.1 * t, 0.16 + 0.08 * t), (-0.10 - 0.08 * t, 0.12 + 0.12 * t)], M["ink"])
    K.legs_pass(d, M, B, CINDER, p, far=True)
    shell = [(x, max(z, 0.12)) for x, z in G.lumpy_ellipse(cx, cz, rx, rz, n=28, lump=0.04, seed=seed + 1)]
    G.stroke(db, shell, M["ember_f"], 0.0, cyclic=True)
    G.stroke(db, [q for q in shell if q[0] < -0.06] + [(-0.06, 0.13)], M["ember_sh"], 0.0, cyclic=True)
    for k, (x, z) in enumerate(((-0.08, 0.24), (0.03, 0.27), (0.10, 0.21))):              # crust plates
        G.stroke(db, G.lumpy_ellipse(x, z, 0.04, 0.03, n=10, lump=0.1, seed=seed + 40 + k), M["ember_dp"], 0.0, cyclic=True)
    for pts in (((-0.12, 0.18), (-0.05, 0.22), (0.02, 0.20)), ((0.0, 0.16), (0.06, 0.18), (0.12, 0.15))):
        G.stroke(db, G.hose_outline(list(pts), 0.012), M["gold_f"], 0.0, cyclic=True)    # the glow in the cracks (a tone)
        G.seam(db, list(pts), M["ink"])
    G.stroke(db, [(-0.16, 0.13), (0.16, 0.13)], M["ink"], I)
    G.stroke(db, shell, M["ink"], O, cyclic=True)
    K.legs_pass(d, M, B, CINDER, p, far=False)
    hx, hz = 0.18, 0.18
    H = K.turn((0.12, 0.17), p["head_rot"], p["head"], B)
    dk = G.Xf(G.Xf(d, H), K.scale_about((hx, hz), 1.55))                                  # a big head for a small beetle
    for k in (0, 1):                                                                      # gold spark feelers
        a = math.radians(75 - 30 * k) + p["ears"] * 0.6
        tip = (hx - 0.01 + 0.025 * k + 0.08 * math.cos(a), hz + 0.05 + 0.08 * math.sin(a))
        G.stroke(dk, G.hose_outline(G.bezier((hx - 0.01 + 0.025 * k, hz + 0.05), (hx + 0.01 * k, hz + 0.1), tip, n=5), 0.01), M["gold_b"], I, cyclic=True)
        G.stroke(dk, K.star(tip[0], tip[1], 0.018, rot=a), M["gold"], I, cyclic=True)
    G.stroke(dk, G.lumpy_ellipse(hx, hz, 0.065, 0.06, n=20, lump=0.03, seed=seed + 2), M["ember"], O, cyclic=True)
    if p["mouth"] > 0.05:
        G.stroke(dk, G.lumpy_ellipse(hx + 0.035, hz - 0.035, 0.01 + 0.006 * p["mouth"], 0.006 + 0.008 * p["mouth"], n=8, seed=seed + 3), M["mouth"], I, cyclic=True)
    else:
        G.seam(dk, G.bezier((hx + 0.05, hz - 0.03), (hx + 0.03, hz - 0.042), (hx + 0.01, hz - 0.035), n=4), M["ink"])
    K.eyes(dk, M, hx - 0.005, hz + 0.01, 0.016, 0.022, 0.03, p, seed)
    if p["stars"] is not None:
        K.stars(dk, M, hx, hz + 0.13, 0.09, p["stars"])


def cinderling_poses():
    out = []
    for i in range(8):                                                                    # idle: breathe, feelers twitch, a blink
        ph, q = K.idle_common(i, 8)
        q.update(ears=0.3 * math.sin(2 * ph), head_rot=0.04 * math.sin(ph), blink={5: 0.6, 6: 1.0}.get(i, 0.0), look=(0.7, 0.0))
        out.append(q)
    for i in range(12):                                                                   # walk: a scurry
        ph = TAU * i / 6
        out.append(dict(legs=K.walk_legs(ph, 0.05, 0.03), bob=0.008 * abs(math.sin(ph)), sz=1 + 0.03 * math.cos(2 * ph),
                        rock=0.04 * math.sin(ph), ears=0.3 * math.sin(2 * ph), look=(0.9, -0.1)))
    for i, (bob, sz, sp) in enumerate(((0.0, 0.85, None), (0.06, 1.12, 0.0), (0.16, 1.06, 0.3), (0.20, 1.0, 0.55),
                                       (0.14, 1.0, 0.8), (0.05, 1.04, None), (0.0, 0.88, None), (0.0, 1.0, None))):
        out.append(dict(bob=bob, sz=sz, spark=sp, eye_pop=1.4 if 1 <= i <= 4 else 1.0, mouth=0.5 if 1 <= i <= 3 else 0.0,
                        ears=-0.5 if i < 5 else 0.0, legs=((0.0, bob),) * 4))                       # the feet leave the ground with it
    out += K.bump_clip()
    for i in range(12):                                                                   # flee: a fast scurry, sparks behind
        ph = TAU * i / 4
        out.append(dict(legs=K.walk_legs(ph, 0.07, 0.04), bob=0.01 * abs(math.sin(ph)), sz=0.95, lean=0.08, rock=-0.05,
                        spark=(i % 4) / 4.0 if i % 2 == 0 else None, ears=0.6, look=(0.9, 0.0)))
    return out


SPECIES = {
    "flarewing": dict(draw=draw_flarewing, poses=flarewing_poses, mats=mats, frame=(124, 124), seed=41, pivot=(0.5, 0.5), flyer=True,
                      clips=[("idle", 10, True), ("fly", 12, True), ("react", 8, False), ("bump", 10, False), ("flare_dance", 12, True)],
                      self_check={"ink": "wing ribs, belly bands, specks, vane edges, feeler hoses",
                                  "motion": "flaps on the beat, the far wing a step behind, the forked tail streams, feelers drag; react loops; flare_dance glows",
                                  "original": "our own flare-feeder: a violet moth-bat with an ember belly and gold vanes; excited, never aggressive (D-087), no teeth"},
                      ours="a violet moth-bat that hovers on gold-vaned wings and loops for joy when a flare lights its vanes"),
    "shadewyrm": dict(draw=draw_shadewyrm, poses=shadewyrm_poses, mats=mats, frame=(160, 80), seed=42, den="props/mercury/ice_burrow",
                      clips=[("idle", 10, True), ("walk", 12, True), ("react", 8, False), ("bump", 10, False), ("idle_open", 10, True)],
                      self_check={"ink": "frost caps with scalloped seams, segment specks, the brow seam, a mouth seam",
                                  "motion": "idle peeks over its ice burrow and looks about; walk humps tail to head; react ducks; idle_open breathes and curls",
                                  "original": "our own ice wyrm: frost-capped teal segments, a big round head; shy, never an ambusher (D-087), no teeth"},
                      ours="a shy frost-capped wyrm that peeks over its ice burrow and humps along the crater floor like a caterpillar"),
    "glassback": dict(draw=draw_glassback, poses=glassback_poses, mats=mats, frame=(176, 112), seed=43,
                      clips=[("idle", 10, True), ("walk", 12, True), ("react", 8, False), ("bump", 10, False), ("flee", 12, True)],
                      self_check={"ink": "crystal facet seams + glints, hide folds, specks, toe seams, a muzzle seam",
                                  "motion": "grazes with the head dipping, glints walk along the shards, an amble; react: the shards ring up and lift",
                                  "original": "our own silicate grazer: a pale hide with cold-teal crystal shards; gentle, no teeth"},
                      ours="a gentle pale grazer whose cold-teal crystal shards ring and lift when it is startled"),
    "cinderling": dict(draw=draw_cinderling, poses=cinderling_poses, mats=mats, frame=(80, 64), seed=44,
                       clips=[("idle", 8, True), ("walk", 12, True), ("react", 8, False), ("bump", 10, False), ("flee", 12, True)],
                       self_check={"ink": "crust plates, crack seams with a gold glow tone, the shell's rim, toe seams, a mouth seam",
                                   "motion": "breathes, feelers twitch, scurries; react hops with a spark puff; flee leaves sparks",
                                   "original": "our own ember beetle: a cracked ember shell with gold glow, big eyes; harmless, no teeth"},
                       ours="a little ember beetle with gold glowing cracks that hops in a puff of sparks when startled"),
}


def entry_for(name):
    sp = SPECIES[name]
    return {"key": f"creatures/mercury/{name}", "style": "v3", "source": f"sources/creatures/mercury_{name}_v3.blend",
            "build": "scripts/build_creatures_mercury_v3.py", "build_fn": f"build_{name}", "collection": name,
            "frame": list(sp["frame"]), "pivot": list(sp.get("pivot", (0.5, 0.0))), "facing": "right", "squash_root": True,
            "planet": "mercury", "seed": sp["seed"], "bg_scene": "-", "beside": "characters/surveyor/side",
            "review_name": f"b145_mercury_{name}", "clips": [{"name": c, "frames": n, "loop": lp} for c, n, lp in sp["clips"]],
            "self_check": dict(sp["self_check"], style="the B-132 kit (Gus's construction); LEAD judges"), "ours": sp["ours"],
            "replaces_v2": True, "note": "B-145 design (Mercury creature re-ink); a flyer's travel clip sits at index 1 like the swimmers' swim"}


def preview(out_dir, name="flarewing"):
    """The export's review layout from exact frames (as_object ids, ss 4), a Mercury placeholder background."""
    import json
    import numpy as np
    from meridian import fakegp, pngio
    import gp_raster as GR
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    sp = SPECIES[name]
    fw, fh = sp["frame"]
    piv = sp.get("pivot", (0.5, 0.0))
    frames, widths, below = [], [], []
    for f, pose in enumerate(sp["poses"]()):
        gp = fakegp.FakeGP()
        M = mats(gp, name)
        d = fakegp.FakeDrawing()
        sp["draw"](d, M, pose, seed=5 * f)
        st = fakegp.strokes_of(d, gp, as_object=(name, "art"))
        if piv[1] == 0.0 and min(float((s_["xz"][:, 1] - s_["radius"] * 1.2).min()) for s_ in st) * 64 < -2.0:
            below.append(f)                                                            # feet-pivot creatures: the ground-line check
        img, w = GR.render_frame(st, fw, fh, 64, piv, ss=4, seed=sp["seed"] * 1000 + f + 1)
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
    meta = {"key": f"creatures/mercury/{name}", "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": 4,
            "frames": len(frames), "fps": 12, "pivot": list(piv), "facing": "right", "ppu": 64, "animations": anims, "squash_root": True}
    problems = v3.validate_sheet(meta, sheet.shape)
    bottom = piv[1] != 0.0                                                             # flyers: all four edges; walkers: sides + top
    clipped = [i for i, im in enumerate(frames) if im[:2, :, 3].any() or (bottom and im[-2:, :, 3].any()) or im[:, :2, 3].any() or im[:, -2:, 3].any()]
    if clipped:
        problems.append(f"frames {clipped[:8]} touch the 2 px edge")
    if below:
        problems.append(f"frames {below[:8]} below the ground line")
    dd = os.path.join(out_dir, "b145_mercury")
    os.makedirs(dd, exist_ok=True)
    png = os.path.join(dd, f"{name}_color.png")
    nb = pngio.write_png(png, sheet)
    with open(os.path.join(dd, f"{name}.json"), "w", encoding="utf-8", newline="\n") as f_:
        json.dump(meta, f_, indent=2)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    stats = {"outer_px": (min(w[1] for w in outer), max(w[2] for w in outer)), "inner_px": (min(w[1] for w in inner), max(w[2] for w in inner)),
             "inner_n": len(inner), "palette": v3.palette_hits(sheet, "mercury", tints=[("mustard", 0.30)]), "problems": problems,
             "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": nb // 1024}
    out = os.path.join(out_dir, f"review_b145_mercury_{name}_preview.png")
    boxes = review.v3_sheet_review(entry_for(name), meta, frames, png, out, stats)
    print(name, f"sheet {sheet.shape[1]}x{sheet.shape[0]} {nb // 1024} KB, ink {stats['outer_px'][0]:.2f}-{stats['outer_px'][1]:.2f} / "
          f"{stats['inner_px'][0]:.2f}-{stats['inner_px'][1]:.2f}, palette {stats['palette'][0] * 100:.1f}% {stats['palette'][1][:3]}, "
          f"problems {problems or '-'}, boxes not x: {','.join(k for k, (mk, _n) in boxes.items() if mk != 'x') or '-'}")


if __name__ == "__main__":
    for _n in (sys.argv[2:] or list(SPECIES)):
        preview(sys.argv[1], _n)
