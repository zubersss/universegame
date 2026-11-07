"""B-155 (C2 Jupiter design prep): Jupiter creature design previews on the B-132 kit (build_creatures_earth_v3: posed body,
pie eyes, dizzy stars), in the Jupiter palette (D-137). Faces kept, friendly or neutral, no teeth, no stings (D-087 /
D-101). Every Jupiter creature lives off the ground (the cloud column has none): pivots at the body centre, all four
frame edges checked, the travel clip at index 1 (B-135's rule, like the swimmers' swim).

  stormglider       176x96, a manta floater riding the deck winds: a rust back, a cream belly, rust-striped wings, two
                    rounded head lobes, a long whip tail; idle 10 (a glide-bob), glide 12, react 8 (a barrel roll away),
                    bump 10.
  lightning_eel     144x80, Deck 2, electric and curious: a festoon blue-grey eel with a cream zig-zag stripe and a rust
                    fin ribbon; idle 10 (an S-wave hover), swim 12, react 8 (sparks as cream tone stars, a flinch, never a
                    bite), bump 10.
  belt_wasp         64x64, Deck 1, a radiation-adapted swarm: rust-and-cream stripes, a blunt round cream tail (no sting),
                    festoon wings; idle 8 (a hover), fly 12, react 8 (a zig-zag scatter), bump 8.
  ballast_tortoise  288x176, huge and slow: a brick shell with cream-rimmed scutes and two cream ballast bladders, tan
                    flippers that paddle; idle 12 (a slow paddle), swim 14, react 10 (pulls its head in), bump 10. Its husk
                    is props/jupiter/husk_tortoise (the same shell, empty).

The Vortex Whale (apex) is a rig set: build_vortex_whale_v3.py. Design previews only; exports wait for Jupiter's cards.

  python -I build_creatures_jupiter_v3.py <preview dir> [names]      lock-free (meridian.fakegp; exact stroke ids)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_earth_v3 as K  # noqa: E402  (the kit; gp_draw real in Blender, fakegp outside)
from meridian import v3  # noqa: E402

G = K.G
P = v3.PALETTES["jupiter"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "jupiter")


def DP(h):
    return v3.deep_of(h, "jupiter")


def mats(gp, sp):
    def m(name, **kw):
        return G.mat(gp, f"{sp}_{name}", **kw)
    out = {"ink": m("ink", fill=None), "pupil": m("pupil", fill=G.INK, ink=False), "eye": m("eye_white", fill=P["offwhite"]),
           "mouth": m("mouth", fill=DP(P["red"])), "star": m("star", fill=P["mustard"]),
           "puff": m("puff", fill=P["offwhite"]), "puff_sh": m("puff_mid", fill=SH(P["offwhite"]), ink=False)}
    for key, slot in (("rust", "mustard"), ("brick", "red"), ("cream", "offwhite"), ("festoon", "teal"), ("sage", "green"),
                      ("tan", "sky"), ("umber", "brown")):
        h = P[slot]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=SH(h), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=DP(h), ink=False)
        out[key + "_b"] = m(key + "_behind", fill=h, behind=True)
    out["leg"], out["coat"] = m("leg", fill=SH(P["sky"])), m("coat", fill=SH(P["sky"]))
    out["leg_far"], out["far"] = m("leg_far", fill=DP(P["sky"])), m("far", fill=DP(P["sky"]))
    out["claw"] = m("claw", fill=P["offwhite"], behind=True)
    return out


def spark(d, M, x, z, r, rot=0.0):
    """A four-point spark (a tone: cream with a fine ink edge, no emission)."""
    pts = []
    for k in range(8):
        a = rot + k * math.pi / 4
        rr = r if k % 2 == 0 else r * 0.35
        pts.append((x + rr * math.cos(a), z + rr * math.sin(a)))
    G.stroke(d, pts, M["cream"], I, cyclic=True)


# ---------------------------------------------------------------- stormglider (a manta floater on the deck winds)
def glider_wing(d, M, f, up, near):
    """One wing from the shoulder: up (+1 far, above) / (-1 near, below); f = how far it is spread (0.3 .. 1)."""
    tip = (-0.30, up * 0.52 * f)
    shape = G.bezier((0.20, up * 0.05), (0.05, up * 0.40 * f), tip, n=9) + G.bezier(tip, (-0.18, up * 0.22 * f), (-0.32, up * 0.04), n=7)[1:]
    G.stroke(d, shape, M["rust_f" if near else "rust_sh"], 0.0, cyclic=True)
    if near:
        for t in (0.35, 0.6):                                                             # two cream stripes across the wing
            a = G.bezier((0.20, up * 0.05), (0.05, up * 0.40 * f), tip, n=9)[int(t * 8)]
            b = G.bezier(tip, (-0.18, up * 0.22 * f), (-0.32, up * 0.04), n=7)[int((1 - t) * 6)]
            G.stroke(d, G.hose_outline([a, b], 0.022), M["cream_f"], 0.0, cyclic=True)
        G.seam(d, [(0.12, up * 0.06), (-0.12, up * 0.28 * f)], M["ink"])
    G.stroke(d, shape, M["ink"], O if near else I, cyclic=True)


def draw_stormglider(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(flap=1.0, tail_w=0.0, roll=0.0))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.0))
    zf = math.cos(math.pi * p["roll"])                                                   # the barrel roll: z flips through 0
    R = G.Xf(G.Xf(d, B), lambda pts: [(x, z * zf) for x, z in pts])
    tail = [(-0.36 - 0.6 * t, 0.02 * math.sin(p["tail_w"] + 4 * t) * t + 0.03 * t) for t in [k / 10 for k in range(11)]]
    G.stroke(R, G.hose_outline(tail, 0.02), M["umber_f"], 0.0, cyclic=True)              # the whip tail
    G.stroke(R, G.hose_outline(tail, 0.02), M["ink"], I, cyclic=True)
    glider_wing(R, M, p["flap"], 1, False)                                                # the far wing, behind
    body = G.lumpy_ellipse(0.05, 0.0, 0.42, 0.15, n=34, lump=0.02, seed=seed + 1)
    G.stroke(R, body, M["rust_f"], 0.0, cyclic=True)
    G.stroke(R, [q for q in body if q[1] < -0.02] + [(0.05, -0.02)], M["cream_f"], 0.0, cyclic=True)   # the cream belly
    G.seam(R, [(-0.30, 0.02), (0.30, 0.04)], M["ink"])
    G.specks(R, [(-0.12, 0.08), (0.05, 0.10), (0.18, 0.08)], M["ink"])
    G.stroke(R, body, M["ink"], O, cyclic=True)
    for sg in (1, -1):                                                                    # two rounded head lobes (no horns)
        lobe = G.lumpy_ellipse(0.48, sg * 0.07, 0.06, 0.035, n=12, seed=seed + 5 + sg, rot=sg * 0.5)
        G.stroke(R, lobe, M["cream_sh"], I, cyclic=True)
    glider_wing(R, M, p["flap"], -1, True)                                                # the near wing, in front
    H = K.turn((0.30, 0.02), p["head_rot"], p["head"], B)
    dh = G.Xf(G.Xf(d, H), lambda pts: [(x, z * zf) for x, z in pts])
    K.eyes(dh, M, 0.30, 0.05, 0.03, 0.04, 0.07, p, seed)
    if p["mouth"] > 0.05:
        G.stroke(dh, G.lumpy_ellipse(0.40, -0.06, 0.02 + 0.01 * p["mouth"], 0.012 + 0.012 * p["mouth"], n=10, seed=seed + 4), M["mouth"], I, cyclic=True)
    else:
        G.seam(dh, G.bezier((0.33, -0.05), (0.38, -0.08), (0.44, -0.05), n=5), M["ink"])
    if p["stars"] is not None:
        K.stars(dh, M, 0.1, 0.32, 0.2, p["stars"])


def glider_poses():
    out = []
    for i in range(10):                                                                   # idle: a glide-bob, the wings breathe
        ph = TAU * i / 10
        out.append(dict(flap=0.8 + 0.2 * math.sin(ph), bob=0.04 * math.sin(ph), rock=0.04 * math.sin(ph - 0.8), tail_w=ph,
                        blink={6: 0.6, 7: 1.0}.get(i, 0.0), look=(0.6, 0.0)))
    for i in range(12):                                                                   # glide: nose down a touch, a slow beat
        ph = TAU * i / 12
        out.append(dict(flap=0.75 + 0.25 * math.sin(ph), bob=0.02 * math.sin(ph + 1), rock=-0.08, tail_w=2 * ph, look=(0.9, 0.0)))
    for i, r in enumerate((0.0, 0.12, 0.3, 0.5, 0.7, 0.88, 1.0, 1.0)):                   # react: a barrel roll away
        out.append(dict(roll=r, shift=-0.03 * i, rock=0.15 * math.sin(math.pi * r), eye_pop=1.4 if i < 3 else 1.1,
                        mouth=0.5 if i in (1, 2) else 0.0, flap=0.6 + 0.4 * abs(math.cos(math.pi * r)), tail_w=i))
    out += [dict(q, shift=0.5 * q.get("shift", 0.0)) for q in K.bump_clip()]
    return out


# ---------------------------------------------------------------- lightning eel (Deck 2; electric, curious)
def lightning_eel_body(d, M, spine, w0, w1, seed):
    """A tapered body along `spine` (head first): festoon blue-grey, a cream belly, a cream zig-zag stripe, a rust fin."""
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
    for i in range(1, n - 1, 3):                                                          # the rust fin ribbon (behind)
        q = up[i]
        G.stroke(d, G.lumpy_ellipse(q[0], q[1] + 0.02, 0.04, 0.03, n=8, lump=0.1, seed=seed + i), M["rust_b"], I, cyclic=True)
    shape = left + [spine[-1]] + right[::-1]
    G.stroke(d, shape, M["festoon_f"], 0.0, cyclic=True)
    mid = [((u[0] + 2 * v[0]) / 3, (u[1] + 2 * v[1]) / 3) for u, v in zip(up, down)]
    G.stroke(d, down + mid[::-1], M["cream_f"], 0.0, cyclic=True)                          # the belly
    zig = [((u[0] + v[0]) / 2 + 0.0, (u[1] + v[1]) / 2 + (0.022 if i % 2 else -0.022) * (1 - i / n)) for i, (u, v) in enumerate(zip(up, mid))]
    G.stroke(d, G.hose_outline(zig[1:-2], 0.012), M["cream_f"], 0.0, cyclic=True)          # the zig-zag stripe
    G.stroke(d, shape, M["ink"], O, cyclic=True)


def draw_lightning_eel(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(wave=0.0, amp=0.05, curl=0.0, sparks=None))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    spine = []
    for i in range(20):
        t = i / 19
        x = 0.46 - 1.05 * t
        z = p["amp"] * math.sin(p["wave"] - 6.0 * t) * t + 0.14 * p["curl"] * math.sin(math.pi * t)
        spine.append((x, z))
    lightning_eel_body(db, M, spine, 0.11, 0.028, seed)
    H = K.turn((0.46, 0.0), p["head_rot"], p["head"], B)
    hx, hz = 0.52, 0.01
    dh = G.Xf(G.Xf(d, H), K.scale_about((hx, hz), 1.3))
    head = G.lumpy_ellipse(hx, hz, 0.10, 0.08, n=24, lump=0.03, seed=seed + 2)
    G.stroke(dh, head, M["festoon_f"], 0.0, cyclic=True)
    G.stroke(dh, [q for q in head if q[1] < hz - 0.03] + [(hx, hz - 0.03)], M["cream_f"], 0.0, cyclic=True)
    G.stroke(dh, head, M["ink"], O, cyclic=True)
    K.eyes(dh, M, hx + 0.005, hz + 0.02, 0.024, 0.032, 0.048, p, seed)
    if p["mouth"] > 0.05:
        G.stroke(dh, G.lumpy_ellipse(hx + 0.07, hz - 0.04, 0.014 + 0.008 * p["mouth"], 0.01 + 0.01 * p["mouth"], n=10, seed=seed + 4), M["mouth"], I, cyclic=True)
    else:
        G.seam(dh, G.bezier((hx + 0.09, hz - 0.03), (hx + 0.05, hz - 0.05), (hx + 0.01, hz - 0.045), n=4), M["ink"])
    if p["sparks"] is not None:                                                           # sparks around the body (tones)
        for k in range(5):
            a = p["sparks"] + k * 1.3
            spark(db, M, -0.4 + 0.2 * k, 0.16 * math.sin(a) + (0.12 if k % 2 else -0.12), 0.05, rot=a)
    if p["stars"] is not None:
        K.stars(dh, M, hx, hz + 0.18, 0.12, p["stars"])


def lightning_eel_poses():
    out = []
    for i in range(10):                                                                   # idle: an S-wave hover
        ph = TAU * i / 10
        out.append(dict(wave=ph, amp=0.04, bob=0.02 * math.sin(ph), head_rot=0.05 * math.sin(ph), blink={6: 0.6, 7: 1.0}.get(i, 0.0), look=(0.7, 0.1)))
    for i in range(12):                                                                   # swim: a stronger wave
        ph = TAU * i / 12
        out.append(dict(wave=2 * ph, amp=0.07, head_rot=0.04 * math.sin(2 * ph), look=(0.9, 0.0)))
    for i in range(8):                                                                    # react: sparks, a flinch, a curl
        out.append(dict(sparks=0.8 * i if i < 5 else None, curl=(0.5, 0.9, 1.0, 0.8, 0.6, 0.4, 0.2, 0.0)[i], eye_pop=1.5 if i < 3 else 1.1,
                        mouth=0.5 if i in (1, 2) else 0.0, wave=0.5 * i, amp=0.03, shift=-0.02 * min(i, 4)))
    out += [dict(q, shift=0.5 * q.get("shift", 0.0), head=(q.get("head", (0.0, 0.0))[0], 0.3 * q.get("head", (0.0, 0.0))[1])) for q in K.bump_clip()]
    return out


# ---------------------------------------------------------------- belt wasp (Deck 1; a swarm; no sting)
def wasp_wing(d, M, root, theta, L, W, far):
    c, s = math.cos(theta), math.sin(theta)

    def at(t, w):
        return (root[0] + c * t * L - s * w, root[1] + s * t * L + c * w)
    shape = [at(0.0, 0.0)] + [at(0.5 + 0.5 * math.cos(a), W * math.sin(a)) for a in [k * math.pi / 8 for k in range(9)]]
    G.stroke(d, shape, M["festoon_sh" if far else "festoon_f"], 0.0, cyclic=True)
    G.seam(d, [at(0.05, 0.0), at(0.8, W * 0.3)], M["ink"])
    G.stroke(d, shape, M["ink"], I, cyclic=True)


def draw_belt_wasp(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(flap=0.0))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    th = math.radians(110 + 50 * math.sin(p["flap"]))
    wasp_wing(db, M, (0.0, 0.05), th + 0.35, 0.20, 0.07, True)                            # the far wing pair
    abd = G.lumpy_ellipse(-0.12, -0.01, 0.12, 0.08, n=22, lump=0.02, seed=seed + 1)       # the striped abdomen
    G.stroke(db, abd, M["rust_f"], 0.0, cyclic=True)
    for k in range(2):
        x = -0.16 + 0.07 * k
        G.stroke(db, [(x - 0.018, -0.085), (x + 0.018, -0.085), (x + 0.022, 0.07), (x - 0.014, 0.07)], M["cream_f"], 0.0, cyclic=True)
    G.stroke(db, abd, M["ink"], O, cyclic=True)
    G.stroke(db, G.lumpy_ellipse(-0.245, -0.02, 0.028, 0.026, n=10, seed=seed + 2), M["cream"], I, cyclic=True)   # a blunt round tail: no sting
    thor = G.lumpy_ellipse(0.03, 0.01, 0.055, 0.05, n=14, seed=seed + 3)
    G.stroke(db, thor, M["rust_sh"], I, cyclic=True)
    H = K.turn((0.07, 0.01), p["head_rot"], p["head"], B)
    hx, hz = 0.11, 0.03
    dh = G.Xf(G.Xf(d, H), K.scale_about((hx, hz), 1.35))
    for k in (0, 1):                                                                      # antennae with round knobs
        a = math.radians(70 - 25 * k) + p["ears"] * 0.6
        tip = (hx - 0.01 + 0.015 * k + 0.07 * math.cos(a), hz + 0.03 + 0.07 * math.sin(a))
        G.stroke(dh, [(hx - 0.01 + 0.015 * k, hz + 0.03), tip], M["ink"], I)
        G.stroke(dh, G.lumpy_ellipse(tip[0], tip[1], 0.012, 0.012, n=8, seed=seed + 6 + k), M["rust"], I, cyclic=True)
    G.stroke(dh, G.lumpy_ellipse(hx, hz, 0.044, 0.04, n=16, seed=seed + 4), M["cream"], I, cyclic=True)   # a cream face (reads at 1x)
    K.eyes(dh, M, hx - 0.002, hz + 0.004, 0.012, 0.016, 0.022, p, seed)
    wasp_wing(db, M, (0.0, 0.06), th, 0.22, 0.075, False)                                  # the near wing pair, in front
    if p["stars"] is not None:
        K.stars(dh, M, hx, hz + 0.1, 0.07, p["stars"])


def belt_wasp_poses():
    out = []
    for i in range(8):                                                                    # idle: a hover, quick flaps
        ph = TAU * i / 4
        out.append(dict(flap=ph, bob=0.015 * math.sin(TAU * i / 8), rock=0.05 * math.sin(TAU * i / 8), ears=0.2 * math.sin(ph),
                        look=(0.5, 0.3), blink={5: 1.0}.get(i, 0.0)))
    for i in range(12):                                                                   # fly: forward
        ph = TAU * i / 4
        out.append(dict(flap=ph, bob=0.02 * math.sin(ph + 1), rock=-0.12, ears=-0.3, look=(0.9, 0.0)))
    for i in range(8):                                                                    # react: a zig-zag scatter
        ph = TAU * i / 2
        out.append(dict(flap=ph, shift=0.06 * (1 if i % 2 else -1), bob=0.03 * (i % 3 - 1), rock=0.3 * (1 if i % 2 else -1),
                        eye_pop=1.4 if i < 4 else 1.1, mouth=0.4 if i in (1, 2) else 0.0, ears=-0.5))
    out += [dict(q, flap=0.5, shift=0.4 * q.get("shift", 0.0)) for q in K.bump_clip()[:8]]
    return out


# ---------------------------------------------------------------- ballast tortoise (huge, slow; a walkable husk when killed)
SHELL = (0.0, 0.10, 1.05, 0.62)                       # cx, cz, rx, rz of the dome (the husk prop shares it)


def tortoise_flipper(d, M, root, a, L, W, near):
    c, s = math.cos(a), math.sin(a)
    tip = (root[0] + c * L, root[1] + s * L)
    shape = G.bezier(root, (root[0] + c * L * 0.5 - s * W, root[1] + s * L * 0.5 + c * W), tip, n=8) + \
        G.bezier(tip, (root[0] + c * L * 0.5 + s * W * 0.6, root[1] + s * L * 0.5 - c * W * 0.6), root, n=8)[1:-1]
    G.stroke(d, shape, M["tan_f" if near else "tan_sh"], 0.0, cyclic=True)
    G.seam(d, [(root[0] + c * L * 0.3, root[1] + s * L * 0.3), (root[0] + c * L * 0.75, root[1] + s * L * 0.75)], M["ink"])
    G.stroke(d, shape, M["ink"], O if near else I, cyclic=True)


def draw_ballast_tortoise(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(paddle=0.0, tuck=0.0))
    p.update(pose or {})
    cx, cz, rx, rz = SHELL
    B = K.Body(p, (0.0, 0.0))
    db = G.Xf(d, B)
    sw = math.sin(p["paddle"])
    tortoise_flipper(db, M, (0.55, -0.25), math.radians(-140 - 25 * sw), 0.72, 0.26, False)    # the far front flipper (a broad paddle)
    tortoise_flipper(db, M, (-0.70, -0.25), math.radians(-165 + 20 * sw), 0.45, 0.20, False)   # the far rear flipper
    t = p["tuck"]
    H = K.turn((0.95, 0.0), p["head_rot"], (p["head"][0] - 0.35 * t, p["head"][1] - 0.04 * t), B)
    dh = G.Xf(d, H)
    neck = [(0.85, -0.05), (1.10, 0.0), (1.22, 0.06)]
    G.stroke(dh, G.hose_outline(neck, 0.14), M["tan_f"], 0.0, cyclic=True)                # the neck + head, behind the shell rim
    G.stroke(dh, G.hose_outline(neck, 0.14), M["ink"], O, cyclic=True)
    head = G.lumpy_ellipse(1.32, 0.08, 0.24, 0.18, n=26, lump=0.03, seed=seed + 2)
    G.stroke(dh, head, M["tan_f"], 0.0, cyclic=True)
    G.stroke(dh, [q for q in head if q[1] < 0.02] + [(1.32, 0.02)], M["tan_sh"], 0.0, cyclic=True)
    G.stroke(dh, head, M["ink"], O, cyclic=True)
    K.eyes(dh, M, 1.33, 0.13, 0.05, 0.065, 0.10, p, seed)
    if p["mouth"] > 0.05:
        G.stroke(dh, G.lumpy_ellipse(1.46, -0.03, 0.03 + 0.012 * p["mouth"], 0.015 + 0.018 * p["mouth"], n=10, seed=seed + 4), M["mouth"], I, cyclic=True)
    else:
        G.seam(dh, G.bezier((1.38, -0.02), (1.46, -0.06), (1.53, -0.02), n=5), M["ink"])
    plastron = G.lumpy_ellipse(cx, cz - rz * 0.62, rx * 0.95, rz * 0.28, n=30, lump=0.02, seed=seed + 7)
    G.stroke(db, plastron, M["tan_sh"], I, cyclic=True)                                    # the belly plate
    dome = [(x, max(z, cz - rz * 0.55)) for x, z in G.lumpy_ellipse(cx, cz, rx, rz, n=48, lump=0.015, seed=seed + 1)]
    G.stroke(db, dome, M["brick_f"], 0.0, cyclic=True)
    G.stroke(db, [q for q in dome if q[0] > rx * 0.35] + [(rx * 0.35, cz)], M["brick_sh"], 0.0, cyclic=True)
    for k, x in enumerate((-0.45, 0.0, 0.45)):                                             # the vertebral plates (deep brick hexagons)
        hexa = [(x + 0.2 * math.cos(a), cz + 0.26 + 0.14 * math.sin(a)) for a in [j * TAU / 6 for j in range(6)]]
        G.stroke(db, hexa, M["brick_dp"], 0.0, cyclic=True)
        G.stroke(db, hexa, M["ink"], I, cyclic=True)
    for x in (-0.68, -0.23, 0.23, 0.68):                                                   # the costal plates (seams)
        hexa = [(x + 0.2 * math.cos(a), cz - 0.06 + 0.13 * math.sin(a)) for a in [j * TAU / 6 for j in range(6)]]
        G.stroke(db, hexa, M["ink"], I, cyclic=True)
    band = G.bezier((-rx * 0.97, cz - rz * 0.40), (0.0, cz - rz * 0.62), (rx * 0.97, cz - rz * 0.40), n=16)
    G.stroke(db, G.hose_outline(band, 0.055), M["cream_f"], 0.0, cyclic=True)              # the cream marginal band + its ticks
    for j in range(1, 15, 2):
        q = band[j]
        G.seam(db, [(q[0], q[1] - 0.05), (q[0], q[1] + 0.05)], M["ink"])
    G.stroke(db, dome, M["ink"], O, cyclic=True)
    for bx, br in ((-0.40, 0.30), (0.32, 0.28)):                                           # the ballast bladders: flat, netted, tied
        base = cz + rz * 0.84
        bl = [(x, max(z, base)) for x, z in G.lumpy_ellipse(bx, base + br * 0.3, br, br * 0.55, n=22, lump=0.02, seed=seed + 30)]
        G.stroke(db, bl, M["cream_f"], 0.0, cyclic=True)
        G.stroke(db, [q for q in bl if q[0] > bx + br * 0.35] + [(bx + br * 0.35, base)], M["cream_sh"], 0.0, cyclic=True)
        for sg in (-1, 1):                                                                 # the net
            G.seam(db, G.bezier((bx - sg * br * 0.8, base + 0.02), (bx, base + br * 0.75), (bx + sg * br * 0.5, base + br * 0.62), n=6), M["ink"])
        G.seam(db, G.bezier((bx - br * 0.9, base + br * 0.35), (bx, base + br * 0.5), (bx + br * 0.9, base + br * 0.35), n=6), M["ink"])
        G.stroke(db, bl, M["ink"], O, cyclic=True)
        G.stroke(db, G.hose_outline([(bx - br * 0.75, base + 0.02), (bx + br * 0.75, base + 0.02)], 0.03), M["rust"], I, cyclic=True)   # the tie band
    tail = G.lumpy_ellipse(-1.12, -0.12, 0.10, 0.05, n=12, seed=seed + 8, rot=-0.3)
    G.stroke(db, tail, M["tan"], I, cyclic=True)
    tortoise_flipper(db, M, (0.62, -0.30), math.radians(-130 + 30 * sw), 0.80, 0.30, True)    # the near front flipper (a broad paddle)
    tortoise_flipper(db, M, (-0.62, -0.30), math.radians(-160 - 20 * sw), 0.50, 0.22, True)   # the near rear flipper
    if p["stars"] is not None:
        K.stars(dh, M, 1.25, 0.5, 0.24, p["stars"])


def tortoise_poses():
    out = []
    for i in range(12):                                                                   # idle: a slow paddle
        ph = TAU * i / 12
        out.append(dict(paddle=ph, bob=0.03 * math.sin(ph), rock=0.02 * math.sin(ph - 1.0), head_rot=0.04 * math.sin(ph),
                        blink={8: 0.6, 9: 1.0}.get(i, 0.0), look=(0.6, 0.0)))
    for i in range(14):                                                                   # swim: a stronger stroke, nose down
        ph = TAU * i / 14
        out.append(dict(paddle=2 * ph, bob=0.04 * math.sin(2 * ph), rock=-0.05, look=(0.9, 0.0)))
    for i, t in enumerate((0.0, 0.3, 0.7, 1.0, 1.0, 1.0, 0.8, 0.5, 0.25, 0.0)):         # react: pulls its head in, peeks out
        out.append(dict(tuck=t, eye_pop=1.4 if i < 3 else (1.0 if t < 1 else 0.9), mouth=0.5 if i == 1 else 0.0,
                        blink=1.0 if i in (4, 5) else 0.0, paddle=0.3 * i))
    out += [dict(q, shift=0.3 * q.get("shift", 0.0), head=(q.get("head", (0.0, 0.0))[0], 0.4 * q.get("head", (0.0, 0.0))[1])) for q in K.bump_clip()]
    return out


SPECIES = {
    "stormglider": dict(draw=draw_stormglider, poses=glider_poses, mats=mats, frame=(176, 96), seed=61, pivot=(0.5, 0.5),
                        clips=[("idle", 10, True), ("glide", 12, True), ("react", 8, False), ("bump", 10, False)],
                        self_check={"ink": "wing stripes and a seam, body specks, the belly line, the whip tail hose",
                                    "motion": "glides and bobs, the wings breathe; glide noses down; react: a barrel roll away",
                                    "original": "our own rust-and-cream manta with rounded head lobes (no horns); gentle, no teeth"},
                        ours="a rust-and-cream manta that rides Jupiter's winds in long glides and barrel-rolls away when startled"),
    "lightning_eel": dict(draw=draw_lightning_eel, poses=lightning_eel_poses, mats=mats, frame=(144, 80), seed=62, pivot=(0.5, 0.5),
                          clips=[("idle", 10, True), ("swim", 12, True), ("react", 8, False), ("bump", 10, False)],
                          self_check={"ink": "the zig-zag stripe, the belly line, the fin ribbon, a mouth seam",
                                      "motion": "an S-wave hover; swim waves harder; react: sparks (tones) and a flinching curl",
                                      "original": "our own festoon eel with a lightning stripe; curious, never biting (D-087), no teeth"},
                          ours="a blue-grey eel with a cream lightning stripe that crackles harmlessly when surprised"),
    "belt_wasp": dict(draw=draw_belt_wasp, poses=belt_wasp_poses, mats=mats, frame=(64, 64), seed=63, pivot=(0.5, 0.5),
                      clips=[("idle", 8, True), ("fly", 12, True), ("react", 8, False), ("bump", 8, False)],
                      self_check={"ink": "abdomen stripes, wing veins, antenna knobs",
                                  "motion": "quick flaps, the far pair a step behind; react: a zig-zag scatter",
                                  "original": "our own striped wasp with a blunt round tail: no sting (D-087), round knobbed antennae"},
                      ours="a fuzzy rust-and-cream wasp with a round blunt tail that buzzes in swarms through the radiation belts"),
    "ballast_tortoise": dict(draw=draw_ballast_tortoise, poses=tortoise_poses, mats=mats, frame=(288, 176), seed=64, pivot=(0.5, 0.5),
                             clips=[("idle", 12, True), ("swim", 14, True), ("react", 10, False), ("bump", 10, False)],
                             self_check={"ink": "cream-rimmed scutes, bladder seams, flipper seams, the belly plate",
                                         "motion": "a slow paddle; swim strokes harder; react: pulls its head in and peeks out",
                                         "original": "our own sky tortoise with ballast bladders on its shell; huge and gentle, no teeth"},
                             ours="a huge, gentle brick-shelled tortoise floating on two cream ballast bladders, paddling through the clouds"),
}
HABITAT = {"stormglider": "deck1", "lightning_eel": "deck2", "belt_wasp": "deck1", "ballast_tortoise": "deck3"}


SOURCES = os.path.join(os.path.dirname(HERE), "sources", "creatures")


def build(name, out=None):
    """The source .blend for one Jupiter creature (the export path, inside Blender): one GP object, one drawing
    per frame, clip markers; the same drawing functions the lock-free preview runs through fakegp (build_creatures_mars_v3's
    manner; the manifest rows name build_<name>)."""
    import bpy
    sp = SPECIES[name]
    out = out or os.path.join(SOURCES, f"jupiter_{name}_v3.blend")
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


def build_stormglider(out=None):          # manifest build_fn: render.py passes the source path
    return build("stormglider", out)


def build_lightning_eel(out=None):          # manifest build_fn: render.py passes the source path
    return build("lightning_eel", out)


def build_belt_wasp(out=None):          # manifest build_fn: render.py passes the source path
    return build("belt_wasp", out)


def build_ballast_tortoise(out=None):          # manifest build_fn: render.py passes the source path
    return build("ballast_tortoise", out)


def entry_for(name):
    sp = SPECIES[name]
    return {"key": f"creatures/jupiter/{name}", "style": "v3", "source": f"sources/creatures/jupiter_{name}_v3.blend",
            "build": "scripts/build_creatures_jupiter_v3.py", "build_fn": f"build_{name}", "collection": name,
            "frame": list(sp["frame"]), "pivot": list(sp.get("pivot", (0.5, 0.5))), "facing": "right", "squash_root": True,
            "planet": "jupiter", "seed": sp["seed"], "bg_scene": HABITAT[name], "beside": "characters/surveyor/side",
            "review_name": f"b155_jupiter_{name}", "clips": [{"name": c, "frames": n, "loop": lp} for c, n, lp in sp["clips"]],
            "self_check": dict(sp["self_check"], style="the B-132 kit (Gus's construction); LEAD judges"), "ours": sp["ours"],
            "replaces_v2": True, "note": "B-155 design (Jupiter creature re-ink); off the ground: pivot at the body centre, the travel clip at index 1"}


def preview(out_dir, name="stormglider"):
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
    meta = {"key": f"creatures/jupiter/{name}", "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": 4,
            "frames": len(frames), "fps": 12, "pivot": list(piv), "facing": "right", "ppu": 64, "animations": anims, "squash_root": True}
    problems = v3.validate_sheet(meta, sheet.shape)
    clipped = [i for i, im in enumerate(frames) if im[:2, :, 3].any() or im[-2:, :, 3].any() or im[:, :2, 3].any() or im[:, -2:, 3].any()]
    if clipped:
        problems.append(f"frames {clipped[:8]} touch the 2 px edge")
    dd = os.path.join(out_dir, "b155_jupiter")
    os.makedirs(dd, exist_ok=True)
    png = os.path.join(dd, f"{name}_color.png")
    nb = pngio.write_png(png, sheet)
    with open(os.path.join(dd, f"{name}.json"), "w", encoding="utf-8", newline="\n") as f_:
        json.dump(meta, f_, indent=2)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    stats = {"outer_px": (min(w[1] for w in outer), max(w[2] for w in outer)), "inner_px": (min(w[1] for w in inner), max(w[2] for w in inner)),
             "inner_n": len(inner), "palette": v3.palette_hits(sheet, "jupiter"), "problems": problems,
             "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": nb // 1024}
    out = os.path.join(out_dir, f"review_b155_jupiter_{name}_preview.png")
    boxes = review.v3_sheet_review(entry_for(name), meta, frames, png, out, stats)
    print(name, f"sheet {sheet.shape[1]}x{sheet.shape[0]} {nb // 1024} KB, ink {stats['outer_px'][0]:.2f}-{stats['outer_px'][1]:.2f} / "
          f"{stats['inner_px'][0]:.2f}-{stats['inner_px'][1]:.2f}, palette {stats['palette'][0] * 100:.1f}% {stats['palette'][1][:3]}, "
          f"problems {problems or '-'}, boxes not x: {','.join(k for k, (mk, _n) in boxes.items() if mk != 'x') or '-'}")


if __name__ == "__main__":
    for _n in (sys.argv[2:] or list(SPECIES)):
        preview(sys.argv[1], _n)
