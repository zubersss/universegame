"""B-147 (C2 Venus design prep): Venus creature design previews on the B-132 kit (build_creatures_earth_v3: posed body, pie
eyes, dizzy stars), in the Venus palette (D-134). Faces kept, friendly or neutral, no teeth (D-087 / D-101).

  acidmoth        64x64, curious, swarms near lights: sea-glass wings with a cream edge (no eyespots), an apricot body,
                  feathery antennae; fly 12 at index 1; idle 8 (a hover), react 8 (a zig-zag scatter), bump 8.
  pressure_crab   128x80, the surface, armoured and slow: a basalt shell, vent-orange claws that wave (never pinch),
                  eye stalks; idle 10, walk 12 (a shuffle), react 8 (into its shell), bump 10.
  vent_eel        160x80, curious about warmth: a basalt eel with a vent-glow belly; idle peeks over its den
                  props/venus/vent_mouth (D-126), walk 12 (a slither), react 8 (ducks), bump 10, idle_open 10.
  sulfur_drifter  112x128, a gasbag filter feeder on the deck winds: a sulphur-yellow balloon with a cream filter frill
                  and swaying tendrils below, pie eyes, a small round mouth, two olive paddle fins. Pivot at the body
                  centre (creatures off the ground, B-135's rule); clips idle 10 (a bob), drift 12 at index 1 (the travel
                  clip, like the swimmers' swim / the Flarewing's fly), react 8 (puffs up), bump 10, flee 12.

Design previews only; Venus exports wait for their cards (B-147 is prep).

  python -I build_creatures_venus_v3.py <preview dir> [names]      lock-free (meridian.fakegp; exact stroke ids)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_earth_v3 as K  # noqa: E402  (the kit; gp_draw real in Blender, fakegp outside)
from meridian import v3  # noqa: E402

G = K.G
P = v3.PALETTES["venus"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "venus")


def DP(h):
    return v3.deep_of(h, "venus")


def mats(gp, sp):
    def m(name, **kw):
        return G.mat(gp, f"{sp}_{name}", **kw)
    out = {"ink": m("ink", fill=None), "pupil": m("pupil", fill=G.INK, ink=False), "eye": m("eye_white", fill=P["offwhite"]),
           "mouth": m("mouth", fill=DP(P["red"])), "star": m("star", fill=P["mustard"]),
           "puff": m("puff", fill=P["offwhite"]), "puff_sh": m("puff_mid", fill=SH(P["offwhite"]), ink=False)}
    for key, slot in (("sulphur", "mustard"), ("vent", "red"), ("cream", "offwhite"), ("glass", "teal"), ("olive", "green"),
                      ("haze", "sky"), ("basalt", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
        out[key + "_b"] = m(key + "_behind", fill=h, behind=True)
    legs = {"pressure_crab": "brown"}.get(sp, "sky")                                     # the kit's legs_pass / paw names
    out["leg"], out["coat"] = m("leg", fill=SH(P[legs])), m("coat", fill=SH(P[legs]))
    out["leg_far"], out["far"] = m("leg_far", fill=DP(P[legs])), m("far", fill=DP(P[legs]))
    out["claw"] = m("claw", fill=P["offwhite"], behind=True)
    return out


# ---------------------------------------------------------------- sulfur drifter
def draw_sulfur_drifter(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(inflate=0.0, paddle=0.0, trail=0.0, streak=None))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    k = 1.0 + 0.25 * p["inflate"]
    rx, rz, cz = 0.42 * k, 0.34 * k, 0.12
    for j in range(5):                                                                    # tendrils (behind the frill), trailing back
        x0 = -0.24 + 0.12 * j
        sw = 0.05 * math.sin(p["paddle"] * 1.3 + j) - 0.18 * p["trail"]
        tend = G.bezier((x0, cz - rz * 0.7), (x0 + sw * 0.5, cz - rz - 0.12), (x0 + sw, cz - rz - 0.30 + 0.02 * j % 3), n=8)
        G.stroke(db, G.hose_outline(tend, 0.025), M["cream_b"], I, cyclic=True)
    for side, sx in ((0, -1), (1, 1)):                                                     # paddle fins
        a = math.radians(-20 + 30 * math.sin(p["paddle"] + side * math.pi))
        root = (sx * rx * 0.9, cz - 0.02)
        fin = [root, (root[0] + sx * 0.16 * math.cos(a), root[1] + 0.16 * math.sin(a) + 0.04), (root[0] + sx * 0.18 * math.cos(a), root[1] + 0.18 * math.sin(a) - 0.05)]
        G.stroke(db, fin, M["olive"], I, cyclic=True)
    frill = [(x, z) for x, z in G.lumpy_ellipse(0.0, cz - rz * 0.62, rx * 0.86, 0.09, n=24, lump=0.12, seed=seed + 3)]
    G.stroke(db, frill, M["cream"], I, cyclic=True)                                       # the filter frill
    ball = G.lumpy_ellipse(0.0, cz, rx, rz, n=40, lump=0.025, seed=seed + 1)
    G.stroke(db, ball, M["sulphur_f"], 0.0, cyclic=True)
    G.stroke(db, [q for q in ball if q[1] < cz - 0.35 * rz] + [(0.0, cz - 0.35 * rz)], M["sulphur_sh"], 0.0, cyclic=True)
    for j in range(3):                                                                    # gasbag panel seams + sulphur specks
        x = -0.2 + 0.2 * j
        G.seam(db, G.bezier((x * 0.6, cz + rz * 0.92), (x * 1.1, cz + rz * 0.3), (x * 0.9, cz - rz * 0.3), n=6), M["ink"])
    G.specks(db, [(-0.25, cz + 0.12), (0.2, cz + 0.2), (0.08, cz - 0.05)], M["ink"])
    G.stroke(db, ball, M["ink"], O, cyclic=True)
    H = K.turn((0.0, cz - 0.05), p["head_rot"], p["head"], B)
    dh = G.Xf(d, H)
    ex, ez = 0.14 * k, cz - 0.04
    K.eyes(dh, M, ex, ez, 0.045, 0.06, 0.09, p, seed)
    if p["mouth"] > 0.05:
        G.stroke(dh, G.lumpy_ellipse(ex + 0.06, ez - 0.13, 0.02 + 0.012 * p["mouth"], 0.014 + 0.016 * p["mouth"], n=10, seed=seed + 4), M["mouth"], I, cyclic=True)
    else:
        G.stroke(dh, G.lumpy_ellipse(ex + 0.06, ez - 0.12, 0.022, 0.016, n=10, seed=seed + 4), M["sulphur_dp"], I, cyclic=True)   # the feeding funnel
    if p["streak"] is not None:                                                           # flee: wind streaks behind
        for j in range(3):
            y = cz - 0.2 + 0.18 * j
            x = -rx - 0.05 - 0.14 * ((p["streak"] + 0.3 * j) % 1.0)
            G.stroke(db, [(x, y), (x - 0.12, y + 0.01)], M["ink"], I)
    if p["stars"] is not None:
        K.stars(dh, M, 0.0, cz + rz + 0.12, 0.2, p["stars"])


def drifter_poses():
    out = []
    for i in range(10):                                                                   # idle: a bob, the frill and tendrils sway
        ph = TAU * i / 10
        out.append(dict(bob=0.035 * math.sin(ph), sz=1 + 0.03 * math.cos(ph), paddle=ph, rock=0.03 * math.sin(ph - 1.0),
                        blink={6: 0.6, 7: 1.0}.get(i, 0.0), look=(0.6, -0.2)))
    for i in range(12):                                                                   # drift: leaning into the wind, fins paddle
        ph = TAU * i / 6
        out.append(dict(bob=0.02 * math.sin(ph), rock=-0.10, paddle=ph * 1.5, trail=0.8, lean=0.04, look=(0.9, 0.0)))
    out += [dict(inflate=0.2, eye_pop=1.3, look=(0.7, 0.0)), dict(inflate=0.6, eye_pop=1.6, mouth=0.6),           # react: puffs up
            dict(inflate=1.0, eye_pop=1.5, mouth=0.7, sz=1.04), dict(inflate=0.95, eye_pop=1.4, mouth=0.5),
            dict(inflate=0.7, eye_pop=1.2, paddle=1.0), dict(inflate=0.4, paddle=2.0, look=(0.9, 0.2)), dict(inflate=0.2, paddle=3.0), dict(inflate=0.0)]
    out += [dict(q, shift=0.5 * q.get("shift", 0.0)) for q in K.bump_clip()]
    for i in range(12):                                                                   # flee: a little deflated, zipping off
        ph = TAU * i / 4
        out.append(dict(inflate=-0.12, rock=-0.18, lean=0.06, paddle=ph * 2, trail=1.0, streak=(i % 4) / 4.0, eye_pop=1.2, look=(0.9, 0.0)))
    return out


# ---------------------------------------------------------------- acidmoth (swarms near lights: curious)
def moth_wing(d, M, root, theta, L, W, far):
    c, s = math.cos(theta), math.sin(theta)
    n = (-s, c) if c < 0 else (s, -c)

    def at(t, w):
        return (root[0] + c * t * L + n[0] * w, root[1] + s * t * L + n[1] * w)
    shape = [at(0.0, -0.02), at(0.5, -0.05), at(0.95, 0.0)] + [at(1.0 - 0.1 * (1 - math.cos(a)), W * math.sin(a)) for a in [k * math.pi / 8 for k in range(1, 8)]] + \
        [at(0.4, W * 0.9), at(0.1, W * 0.5)]
    G.stroke(d, shape, M["glass_sh" if far else "glass_f"], 0.0, cyclic=True)
    G.stroke(d, [at(0.6, W * 0.75), at(0.95, W * 0.4), at(1.0, W * 0.2), at(0.98, W * 0.6), at(0.7, W * 0.95)], M["cream_f"], 0.0, cyclic=True)   # the cream edge
    for t, w in ((0.7, 0.5), (0.45, 0.7)):
        G.seam(d, [at(0.05, 0.02), at(t * 0.7, w * W * 0.6), at(t, w * W)], M["ink"])
    G.stroke(d, shape, M["ink"], O if not far else I, cyclic=True)


def draw_acidmoth(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(flap=0.0, zig=0.0))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    th = math.radians(115 + 55 * math.sin(p["flap"]))
    moth_wing(db, M, (0.0, 0.02), th + 0.3, 0.22, 0.11, True)                            # the far wing pair
    body = G.lumpy_ellipse(-0.02, 0.0, 0.10, 0.045, n=20, lump=0.08, seed=seed + 1)        # a fuzzy apricot body
    G.stroke(db, body, M["haze_f"], 0.0, cyclic=True)
    for k in range(3):
        G.stroke(db, [(-0.09 + 0.05 * k, -0.04), (-0.07 + 0.05 * k, -0.04), (-0.065 + 0.05 * k, 0.04), (-0.085 + 0.05 * k, 0.04)], M["olive_f"], 0.0, cyclic=True)
    G.stroke(db, body, M["ink"], O, cyclic=True)
    H = K.turn((0.06, 0.0), p["head_rot"], p["head"], B)
    hx, hz = 0.10, 0.015
    dh = G.Xf(G.Xf(d, H), K.scale_about((hx, hz), 1.4))
    for k in (0, 1):                                                                      # feathery antennae
        a = math.radians(80 - 30 * k) + p["ears"] * 0.6
        tip = (hx - 0.01 + 0.015 * k + 0.08 * math.cos(a), hz + 0.03 + 0.08 * math.sin(a))
        G.stroke(dh, [(hx - 0.01 + 0.015 * k, hz + 0.03), tip], M["ink"], I)
        for t in (0.4, 0.7):
            q = (hx - 0.01 + 0.015 * k + t * (tip[0] - hx + 0.01 - 0.015 * k), hz + 0.03 + t * (tip[1] - hz - 0.03))
            G.stroke(dh, [(q[0] - 0.012, q[1] + 0.006), q, (q[0] + 0.012, q[1] + 0.006)], M["ink"], I)
    G.stroke(dh, G.lumpy_ellipse(hx, hz, 0.04, 0.036, n=16, seed=seed + 2), M["haze"], O, cyclic=True)
    K.eyes(dh, M, hx - 0.002, hz + 0.004, 0.012, 0.016, 0.022, p, seed)
    moth_wing(db, M, (-0.02, 0.02), th, 0.25, 0.12, False)                                 # the near wing pair, in front
    if p["stars"] is not None:
        K.stars(dh, M, hx, hz + 0.1, 0.07, p["stars"])


def acidmoth_poses():
    out = []
    for i in range(8):                                                                    # idle: a hover near the light, quick flaps
        ph = TAU * i / 4
        out.append(dict(flap=ph, bob=0.015 * math.sin(TAU * i / 8), rock=0.05 * math.sin(TAU * i / 8), ears=0.2 * math.sin(ph),
                        look=(0.4, 0.4), blink={5: 1.0}.get(i, 0.0)))
    for i in range(12):                                                                   # fly: forward
        ph = TAU * i / 4
        out.append(dict(flap=ph, bob=0.02 * math.sin(ph + 1), rock=-0.12, ears=-0.3, look=(0.9, 0.0)))
    for i in range(8):                                                                    # react: a startled zig-zag scatter
        ph = TAU * i / 2
        out.append(dict(flap=ph, shift=0.06 * (1 if i % 2 else -1), bob=0.03 * (i % 3 - 1), rock=0.3 * (1 if i % 2 else -1),
                        eye_pop=1.4 if i < 4 else 1.1, mouth=0.4 if i in (1, 2) else 0.0, ears=-0.5))
    out += [dict(q, flap=0.5, shift=0.4 * q.get("shift", 0.0)) for q in K.bump_clip()[:8]]
    return out


# ---------------------------------------------------------------- pressure crab (the surface; armoured, slow)
CRAB = dict(hips=[(-0.22, 0.20), (0.18, 0.21), (-0.28, 0.19), (0.12, 0.20)], feet=[-0.44, 0.40, -0.48, 0.34],
            ankle=0.04, leg_w=0.06, bend_hind=0.30, bend_front=-0.30, foot="paw", paw=(0.03, 0.02, 0, 0), dangle=0.2)
CRAB_SHELL = (0.0, 0.30, 0.40, 0.20)


def draw_pressure_crab(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(tuck=0.0, wave=0.0))
    p.update(pose or {})
    cx, cz, rx, rz = CRAB_SHELL
    t = p["tuck"]
    B = K.Body(dict(p, bob=p["bob"] - 0.12 * t), (cx, cz))
    db = G.Xf(d, B)
    spec = dict(CRAB, feet=[f * (1 - 0.6 * t) for f in CRAB["feet"]])
    K.legs_pass(d, M, B, spec, p, far=True)
    for k, side in enumerate((-1, 1)):                                                    # the eye stalks (retract on tuck)
        base = (0.14 + 0.07 * k, cz + rz * 0.8)
        top = (base[0] + 0.03, base[1] + 0.16 * (1 - 0.85 * t))
        G.stroke(db, G.hose_outline([base, top], 0.03), M["basalt_b"], I, cyclic=True)
        if k == 0:
            stalk_top = top
    shell = [(x, max(z, 0.14)) for x, z in G.lumpy_ellipse(cx, cz, rx, rz, n=40, lump=0.03, seed=seed + 1)]
    G.stroke(db, shell, M["basalt_f"], 0.0, cyclic=True)
    G.stroke(db, [q for q in shell if q[0] > 0.12 and q[1] > cz] + [(0.12, cz)], M["basalt_sh"], 0.0, cyclic=True)
    for k in range(4):                                                                    # shell plate ridges + vent-orange flecks
        x = -0.28 + 0.18 * k
        G.seam(db, G.bezier((x, 0.16), (x + 0.04, cz + 0.06), (x + 0.02, cz + rz * 0.95 * math.sqrt(max(0.0, 1 - (x / rx) ** 2))), n=6), M["ink"])
    G.specks(db, [(-0.2, cz + 0.08), (0.05, cz + 0.12), (0.25, cz + 0.02)], M["ink"])
    G.stroke(db, [(-0.36, 0.16), (0.36, 0.16)], M["ink"], I)
    G.stroke(db, shell, M["ink"], O, cyclic=True)
    K.legs_pass(d, M, B, spec, p, far=False)
    for k in (0, 1):                                                                      # claws wave (never pinch: D-087)
        a = math.radians(30 + 25 * math.sin(p["wave"] + k * 1.7)) * (1 - t)
        root = (0.32 + 0.04 * k, 0.22 - 0.02 * k)
        el = (root[0] + 0.14 * math.cos(a), root[1] + 0.14 * math.sin(a) * (1 - t))
        G.stroke(db, G.hose_outline([root, el], 0.05), M["basalt_b"], I, cyclic=True)
        claw = G.lumpy_ellipse(el[0] + 0.04, el[1] + 0.02, 0.06, 0.04, n=14, lump=0.05, seed=seed + 10 + k, rot=a)
        G.stroke(db, claw, M["vent"], O, cyclic=True)
        G.seam(db, [(el[0] + 0.02, el[1] + 0.02), (el[0] + 0.09, el[1] + 0.03)], M["ink"])
    if t < 0.8:                                                                           # the eyes on the stalks
        K.eyes(db, M, stalk_top[0], stalk_top[1] + 0.015, 0.024, 0.03, 0.07, p, seed)
    if p["stars"] is not None:
        K.stars(db, M, 0.0, cz + rz + 0.25, 0.18, p["stars"])


def crab_poses():
    out = []
    for i in range(10):                                                                   # idle: the claws wave slowly, a blink
        ph, q = K.idle_common(i, 10)
        q.update(wave=ph, blink={6: 0.6, 7: 1.0}.get(i, 0.0), look=(0.7, 0.0))
        out.append(q)
    for i in range(12):                                                                   # walk: a slow shuffle
        ph = TAU * i / 12
        out.append(dict(legs=K.walk_legs(ph, 0.06, 0.03, order=(0.0, math.pi, math.pi, 0.0)), bob=0.008 * abs(math.sin(2 * ph)),
                        rock=0.02 * math.sin(2 * ph), wave=ph * 2, look=(0.9, 0.0)))
    out += [dict(eye_pop=1.4, wave=1.0, look=(0.8, 0.0)), dict(tuck=0.3, eye_pop=1.5), dict(tuck=0.7), dict(tuck=1.0, sz=0.95),   # react: into its shell
            dict(tuck=1.0, sz=0.97), dict(tuck=0.8), dict(tuck=0.4, look=(0.9, 0.2)), dict(tuck=0.1)]
    out += K.bump_clip()
    return out


# ---------------------------------------------------------------- vent eel (the surface vents; curious about warmth)
# A dark basalt eel with a vent-orange belly glow (a tone), a cream dorsal fin frill, a rounded head with pie eyes. Idle
# peeks over its den, props/venus/vent_mouth (a basalt vent cone, D-126: drawn by UNITY in front on the same pivot); walk
# slithers along the ground in an S-wave; react ducks; idle_open pauses in the open, curling.
VENT_TOP = [(-0.56, 0.0), (-0.42, 0.10), (-0.26, 0.24), (-0.14, 0.29), (0.14, 0.29), (0.26, 0.24), (0.42, 0.10), (0.56, 0.0)]


def eel_body(d, M, spine, w0, w1, seed):
    """A tapered body along `spine` (head first): basalt, the vent-glow belly band, a cream dorsal frill, bands."""
    n = len(spine)
    left, right = [], []
    for i, (x, z) in enumerate(spine):
        t = i / (n - 1)
        w = w0 * (1 - t) + w1 * t
        a, b = spine[max(i - 1, 0)], spine[min(i + 1, n - 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / L, dx / L
        left.append((x + nx * w, z + nz * w))
        right.append((x - nx * w, z - nz * w))
    up, down = (left, right) if sum(q[1] for q in left) > sum(q[1] for q in right) else (right, left)
    for i in range(1, n - 1, 3):                                                         # the dorsal frill (behind)
        q = up[i]
        G.stroke(d, G.lumpy_ellipse(q[0], q[1] + 0.02, 0.035, 0.03, n=8, lump=0.1, seed=seed + i), M["cream_sh"], I, cyclic=True)
    tip = spine[-1]
    shape = left + [tip] + right[::-1]
    G.stroke(d, shape, M["basalt_f"], 0.0, cyclic=True)
    mid = [((u[0] + 2 * v[0]) / 3, (u[1] + 2 * v[1]) / 3) for u, v in zip(up, down)]
    G.stroke(d, down + mid[::-1], M["vent_f"], 0.0, cyclic=True)                          # the belly glow
    for i in range(2, n - 2, 3):
        G.seam(d, [up[i], mid[i]], M["ink"])
    G.stroke(d, shape, M["ink"], O, cyclic=True)


def eel_head(d, M, hx, hz, p, seed):
    head = G.lumpy_ellipse(hx, hz, 0.11, 0.09, n=26, lump=0.03, seed=seed + 2)
    G.stroke(d, head, M["basalt_f"], 0.0, cyclic=True)
    G.stroke(d, [q for q in head if q[1] < hz - 0.03] + [(hx, hz - 0.03)], M["vent_f"], 0.0, cyclic=True)
    G.stroke(d, head, M["ink"], O, cyclic=True)
    if p["mouth"] > 0.05:
        G.stroke(d, G.lumpy_ellipse(hx + 0.07, hz - 0.04, 0.014 + 0.008 * p["mouth"], 0.01 + 0.01 * p["mouth"], n=10, seed=seed + 4), M["mouth"], I, cyclic=True)
    else:
        G.seam(d, G.bezier((hx + 0.10, hz - 0.03), (hx + 0.06, hz - 0.05), (hx + 0.02, hz - 0.045), n=4), M["ink"])
    K.eyes(d, M, hx + 0.005, hz + 0.02, 0.026, 0.034, 0.05, p, seed)
    if p["stars"] is not None:
        K.stars(d, M, hx, hz + 0.2, 0.13, p["stars"])


def draw_vent_eel(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(hole=None, wave=0.0, curl=0.0))
    p.update(pose or {})
    e = p["hole"]
    if e is not None:                                                                     # at the vent: rises behind its rim
        hx, hz = 0.08 + 0.03 * e, max(0.20 + 0.40 * e + p["bob"], 0.18)
        spine = G.bezier((hx - 0.02, hz - 0.04), (hx - 0.06, hz - 0.2), (0.0, 0.2), (-0.02, 0.10), n=12)
        eel_body(d, M, spine, 0.075, 0.07, seed)
        dk = G.Xf(d, K.turn((hx - 0.06, hz - 0.03), p["head_rot"], (0.0, 0.0), K.scale_about((hx, hz), 1.2)))
        eel_head(dk, M, hx, hz, p, seed)
        return
    B = K.Body(p, (0.0, 0.1))
    db = G.Xf(d, B)
    spine = []
    for i in range(20):                                                                   # an S-wave slither along the ground
        t = i / 19
        x = 0.62 - 1.45 * t
        z = 0.09 + 0.05 * max(0.0, math.sin(p["wave"] - 6.0 * t)) * t + 0.12 * p["curl"] * math.sin(math.pi * t)
        spine.append((x, z))
    eel_body(db, M, spine, 0.075, 0.025, seed)
    H = K.turn((0.62, 0.1), p["head_rot"], p["head"], B)
    hx, hz = 0.70, 0.13
    dk = G.Xf(G.Xf(d, H), K.scale_about((hx, hz), 1.2))
    eel_head(dk, M, hx, hz, p, seed)


def eel_poses():
    out = []
    for i in range(10):                                                                   # idle at the vent: peek, look about
        ph = TAU * i / 10
        out.append(dict(hole=1.0 + 0.04 * math.sin(ph), bob=0.01 * math.sin(ph), head_rot=0.07 * math.sin(ph - 0.6),
                        look=(0.8, 0.1) if i < 5 else (-0.5, 0.2), blink={6: 0.6, 7: 1.0}.get(i, 0.0)))
    for i in range(12):                                                                   # walk: a slither
        ph = TAU * i / 12
        out.append(dict(wave=ph * 2, head_rot=0.05 * math.sin(2 * ph), look=(0.9, 0.0)))
    out += [dict(hole=1.0, eye_pop=1.3), dict(hole=1.12, eye_pop=1.6, mouth=0.5), dict(hole=0.7, eye_pop=1.3, mouth=0.3),
            dict(hole=0.35, eye_pop=1.2), dict(hole=0.12, eye_pop=1.35, look=(0.6, 0.0)), dict(hole=0.12, look=(0.9, 0.0)),
            dict(hole=0.1, blink=1.0), dict(hole=0.15, look=(0.3, 0.0))]                  # react: duck behind the vent rim
    out += [dict(q, rock=0.4 * q.get("rock", 0.0), shift=0.5 * q.get("shift", 0.0)) for q in K.bump_clip()]
    for i in range(10):                                                                   # idle_open: a pause in the open, curling
        ph = TAU * i / 10
        _ph, q = K.idle_common(i, 10)
        q.update(wave=1.0 + 0.5 * math.sin(ph), curl=0.3 + 0.25 * math.sin(ph - 1.0), head_rot=0.06 * math.sin(ph), look=(0.7, 0.1))
        out.append(q)
    return out


SPECIES = {
    "sulfur_drifter": dict(draw=draw_sulfur_drifter, poses=drifter_poses, mats=mats, frame=(112, 128), seed=51, pivot=(0.5, 0.5),
                           clips=[("idle", 10, True), ("drift", 12, True), ("react", 8, False), ("bump", 10, False), ("flee", 12, True)],
                           self_check={"ink": "gasbag panel seams, sulphur specks, the frill's lumpy edge, tendril hoses, fin edges",
                                       "motion": "bobs and breathes, the tendrils sway and trail in the drift, fins paddle; react puffs up",
                                       "original": "our own sulphur gasbag: a balloon with a cream filter frill and tendrils; gentle, no teeth"},
                           ours="a sulphur-yellow gasbag that drifts on the deck winds, combing the haze with its frill, and puffs up when startled"),
    "acidmoth": dict(draw=draw_acidmoth, poses=acidmoth_poses, mats=mats, frame=(64, 64), seed=52, pivot=(0.5, 0.5),
                     clips=[("idle", 8, True), ("fly", 12, True), ("react", 8, False), ("bump", 8, False)],
                     self_check={"ink": "wing veins, the cream wing edge, body bands, feathery antennae",
                                 "motion": "quick flaps, the far pair a step behind; react: a zig-zag scatter",
                                 "original": "our own sea-glass moth: no eyespots (no extra eyes), curious near lights, never biting"},
                     ours="a little sea-glass moth that circles the station lamps and scatters in a zig-zag when startled"),
    "pressure_crab": dict(draw=draw_pressure_crab, poses=crab_poses, mats=mats, frame=(128, 80), seed=53,
                          clips=[("idle", 10, True), ("walk", 12, True), ("react", 8, False), ("bump", 10, False)],
                          self_check={"ink": "shell plate ridges, specks, the shell's rim line, claw seams, stalk hoses",
                                      "motion": "claws wave slowly, a shuffling walk, eye stalks bob; react: it pulls into its shell",
                                      "original": "our own basalt crab with vent-orange claws that wave, never pinch (D-087)"},
                          ours="a slow basalt-shelled crab with glowing orange claws that waves at you and ducks into its shell"),
    "vent_eel": dict(draw=draw_vent_eel, poses=eel_poses, mats=mats, frame=(160, 80), seed=54, den="props/venus/vent_mouth",
                     clips=[("idle", 10, True), ("walk", 12, True), ("react", 8, False), ("bump", 10, False), ("idle_open", 10, True)],
                     self_check={"ink": "body bands, the frill's lumpy edge, the belly glow line, a mouth seam",
                                 "motion": "idle peeks over its vent and looks about; walk slithers in an S-wave; react ducks; idle_open curls",
                                 "original": "our own basalt eel with a vent-glow belly; curious about warmth, never biting (D-087), no teeth"},
                     ours="a dark basalt eel with a glowing orange belly that peeks out of its vent and slithers off to sun itself by the warm rocks"),
}


def entry_for(name):
    sp = SPECIES[name]
    return {"key": f"creatures/venus/{name}", "style": "v3", "source": f"sources/creatures/venus_{name}_v3.blend",
            "build": "scripts/build_creatures_venus_v3.py", "build_fn": f"build_{name}", "collection": name,
            "frame": list(sp["frame"]), "pivot": list(sp.get("pivot", (0.5, 0.0))), "facing": "right", "squash_root": True,
            "planet": "venus", "seed": sp["seed"], "bg_scene": "-", "beside": "characters/surveyor/side",
            "review_name": f"b147_venus_{name}", "clips": [{"name": c, "frames": n, "loop": lp} for c, n, lp in sp["clips"]],
            "self_check": dict(sp["self_check"], style="the B-132 kit (Gus's construction); LEAD judges"), "ours": sp["ours"],
            "replaces_v2": True, "note": "B-147 design (Venus creature re-ink)"}


def preview(out_dir, name="sulfur_drifter"):
    """The export's review layout from exact frames (as_object ids, ss 4) on a placeholder background (centre-pivot
    creatures: all four edges checked)."""
    if True:
        import json
        import numpy as np
        from meridian import fakegp, pngio
        import gp_raster as GR
        sys.path.insert(0, os.path.dirname(HERE))
        import review
        sp = SPECIES[name]
        fw, fh = sp["frame"]
        piv = sp.get("pivot", (0.5, 0.0))
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
        meta = {"key": f"creatures/venus/{name}", "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": 4,
                "frames": len(frames), "fps": 12, "pivot": list(piv), "facing": "right", "ppu": 64, "animations": anims, "squash_root": True}
        problems = v3.validate_sheet(meta, sheet.shape)
        clipped = [i for i, im in enumerate(frames) if im[:2, :, 3].any() or im[-2:, :, 3].any() or im[:, :2, 3].any() or im[:, -2:, 3].any()]
        if clipped:
            problems.append(f"frames {clipped[:8]} touch the 2 px edge")
        dd = os.path.join(out_dir, "b147_venus")
        os.makedirs(dd, exist_ok=True)
        png = os.path.join(dd, f"{name}_color.png")
        nb = pngio.write_png(png, sheet)
        with open(os.path.join(dd, f"{name}.json"), "w", encoding="utf-8", newline="\n") as f_:
            json.dump(meta, f_, indent=2)
        outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
        inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
        stats = {"outer_px": (min(w[1] for w in outer), max(w[2] for w in outer)), "inner_px": (min(w[1] for w in inner), max(w[2] for w in inner)),
                 "inner_n": len(inner), "palette": v3.palette_hits(sheet, "venus"), "problems": problems,
                 "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": nb // 1024}
        out = os.path.join(out_dir, f"review_b147_venus_{name}_preview.png")
        boxes = review.v3_sheet_review(entry_for(name), meta, frames, png, out, stats)
        print(name, f"sheet {sheet.shape[1]}x{sheet.shape[0]} {nb // 1024} KB, ink {stats['outer_px'][0]:.2f}-{stats['outer_px'][1]:.2f} / "
              f"{stats['inner_px'][0]:.2f}-{stats['inner_px'][1]:.2f}, palette {stats['palette'][0] * 100:.1f}% {stats['palette'][1][:3]}, "
              f"problems {problems or '-'}, boxes not x: {','.join(k for k, (mk, _n) in boxes.items() if mk != 'x') or '-'}")


if __name__ == "__main__":
    for _n in (sys.argv[2:] or list(SPECIES)):
        preview(sys.argv[1], _n)
