"""B-134 (D-121): characters/surveyor/side_b, the surveyor's five missing C1 clips on a second sheet (side is at the
2048 cap with 98 frames). Same character (B-125, draw_surveyor), same 192x192 frames, pivot [0.5, 0], PPU 64, v3.1 ink;
held tools, the jetpack flame and the effects are drawn on top here. Clip names are unique across side and side_b.

  dig       10 loop  two-hand pick: wind-up overhead, smear down, the point bites the ground, dirt chips fly, recover
  build     10 loop  hammer on a mustard plate fitted against the work: it hangs askew, one blow snaps it flat
                     (snap lines), a second blow drives a rivet; the plate wobbles after each hit
  surprise  12 once  eye-pop: a crouch, then a big stretch with arms flung up while the helmet lifts off the collar
                     (the card's "hat lift"), drops back with a squash, settles
  jetpack   10 loop  the float pack fires: a red / mustard flame from a nozzle under the pack, smoke puffs rolling down
                     and spreading on the ground, legs dangling, arms out; hose and plumb bob stream (the B-125
                     surveyor has no scarf, so these carry the card's streaming)
  climb_in  14 once  frames 0-7 climb in place hand over hand (UNITY moves the root up the fin-leg), 8-9 lean toward
                     the hatch, 10-11 the cartoon zip into it with speed lines, 12-13 only a puff where it vanished.
                     Every frame carries a "hatch" socket (metres from the pivot) where the Pilgrim's door goes.

  python -I build_surveyor_side_b.py <preview dir>     lock-free preview (meridian.fakegp)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp  # noqa: E402

try:                                    # inside Blender (the export build): the real gp_draw
    import bpy
    if not hasattr(bpy, "data"):
        raise ImportError
    import gp_draw as G
except ImportError:
    bpy = None
    G = fakegp.install()
import gp_raster as GR  # noqa: E402
import build_surveyor_v3 as SV  # noqa: E402

P = G.PALETTES["earth"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
PPU = 64
CLIPS = [("dig", 10, True), ("build", 10, True), ("surprise", 12, False), ("jetpack", 10, True), ("climb_in", 14, False),
         ("climb_ladder", 8, True), ("reel_up", 8, True)]                                  # B-210 (D-174): the ways back up
SEED = 5
HATCH = (1.0, 1.05)                     # the hatch socket (m from the pivot): where the zip ends
DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "characters", "surveyor_side_b.blend")


def materials(gp):
    M = SV.materials(gp)
    M.update({
        "wood": G.mat(gp, "b_wood", fill=G.shadow_of(P["mustard"]), behind=True),
        "wood_dp": G.mat(gp, "b_wood_deep", fill=G.deep_of(P["mustard"]), ink=False),
        "steel": G.mat(gp, "b_steel", fill=P["sky"]),
        "steel_sh": G.mat(gp, "b_steel_mid", fill=G.shadow_of(P["sky"]), ink=False),
        "plate": G.mat(gp, "b_plate", fill=P["mustard"]),
        "plate_sh": G.mat(gp, "b_plate_mid", fill=G.shadow_of(P["mustard"]), ink=False),
        "chip": G.mat(gp, "b_chip", fill=P["brown"], behind=True),
        "chip2": G.mat(gp, "b_chip2", fill=G.deep_of(P["mustard"]), behind=True),
        "flame": G.mat(gp, "b_flame", fill=P["red"]),
        "flame_in": G.mat(gp, "b_flame_in", fill=P["mustard"], ink=False),
        "flame_core": G.mat(gp, "b_flame_core", fill=P["offwhite"], ink=False),
        "puff": G.mat(gp, "b_puff", fill=P["offwhite"]),
        "puff_sh": G.mat(gp, "b_puff_mid", fill=G.shadow_of(P["offwhite"]), ink=False),
        "rivet": G.mat(gp, "b_rivet", fill=P["red"], behind=True),
    })
    return M


# ---------------------------------------------------------------- the pose's visual root, the hands, the pack (as draw_surveyor)

def base(p):
    q = dict(view="side", expr="happy", bob=0.0, sz=1.0, lean=0.0, legs=((0.0, 0.0), (0.0, 0.0)), arms=(0.0, 0.0),
             pack_swing=0.0, pack_dz=0.0, shift=0.0)
    q.update(p)
    return q


def X1(p, x, z, pivot_z=0.55):
    sz = p["sz"]
    return (x / math.sqrt(sz) + p["lean"] * (z - pivot_z) + p["shift"], pivot_z + (z - pivot_z) * sz + p["bob"])


def hand(p, k):
    """draw_surveyor's hand centre for arm k (0 back, 1 front) and the arm's unit direction."""
    sh = X1(p, 0.04 * (-1 if k == 0 else 1), 1.00)
    ang = p["arms"][k]
    u = (math.sin(ang), -math.cos(ang))
    h = (sh[0] + 0.42 * u[0], sh[1] + 0.42 * u[1])
    return h, u


def front_glove(d, M, p, seed):
    """Redraw the front glove over a held tool (same strokes as draw_surveyor's arm(1))."""
    h, _u = hand(p, 1)
    G.stroke(d, G.lumpy_ellipse(h[0], h[1] - 0.04, 0.115, 0.105, n=24, lump=0.06, seed=seed + 22), M["glove"], O, cyclic=True)
    fx = h[0] + 0.03
    G.stroke(d, G.bezier((fx - 0.05, h[1] - 0.05), (fx, h[1] - 0.07), (fx + 0.04, h[1] - 0.03), n=6), M["ink"], I)
    G.seam(d, G.bowed_line((fx - 0.03, h[1] - 0.005), (fx - 0.035, h[1] - 0.06), bow=0.1, n=4), M["ink"])


def pack_point(p, x, z):
    """A point on the float pack, moved with its strap swing and bounce (draw_surveyor's PK)."""
    strap = X1(p, -0.34, 1.14)
    q = X1(p, x, z)
    cs, sn = math.cos(p["pack_swing"]), math.sin(p["pack_swing"])
    return (strap[0] + (q[0] - strap[0]) * cs - (q[1] - strap[1]) * sn,
            strap[1] + (q[0] - strap[0]) * sn + (q[1] - strap[1]) * cs + p["pack_dz"])


def rot(u, a):
    c, s = math.cos(a), math.sin(a)
    return (u[0] * c - u[1] * s, u[0] * s + u[1] * c)


def add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k)


# ---------------------------------------------------------------- props and effects

def pick_tip(p):
    """Where the pick's point is for pose p (the impact frame's tip is where the chips start)."""
    h, u = hand(p, 1)
    n = (-u[1], u[0])
    end = add((h[0], h[1] - 0.04), u, 0.62)
    return add(add(end, n, -0.22), u, -0.06)


def pick(d, M, grip, u, seed):
    n = (-u[1], u[0])
    end = add(grip, u, 0.62)
    G.stroke(d, G.hose_outline([add(grip, u, -0.12), add(grip, u, 0.3), end], 0.05), M["wood"], O, cyclic=True)
    G.seam(d, [add(grip, u, 0.05), add(grip, u, 0.40)], M["ink"])                          # wood grain
    A, B = add(add(end, n, 0.24), u, -0.06), add(add(end, n, -0.22), u, -0.06)
    outer = G.bezier(A, add(end, u, 0.10), B, n=10)
    inner = G.bezier(B, add(end, u, 0.0), A, n=10)[1:-1]
    head = outer + inner
    G.stroke(d, head, M["steel"], 0.0, cyclic=True)
    G.stroke(d, G.bezier(A, add(end, u, 0.035), B, n=10) + inner, M["steel_sh"], 0.0, cyclic=True)
    G.stroke(d, head, M["ink"], O, cyclic=True)
    G.rivets(d, [add(end, u, 0.04)], M["ink"])
    return B                                                                                   # the biting point


def hammer(d, M, grip, u):
    n = (-u[1], u[0])
    end = add(grip, u, 0.24)
    G.stroke(d, G.hose_outline([add(grip, u, -0.08), end], 0.045), M["wood"], O, cyclic=True)
    a, b = add(add(end, n, 0.085), u, -0.04), add(add(end, n, -0.085), u, -0.04)
    c, e = add(b, u, 0.09), add(a, u, 0.09)
    G.stroke(d, [a, b, c, e], M["steel"], O, cyclic=True)
    G.stroke(d, [add(a, u, 0.06), add(b, u, 0.06), c, e], M["steel_sh"], 0.0, cyclic=True)
    G.seam(d, [add(a, n, -0.03), add(b, n, 0.03)], M["ink"])
    return add(end, u, 0.05)                                                                   # the striking face


def plate(d, M, tilt, rivet_out):
    """The part being fitted: a mustard plate against the work, pivoting about its bottom-left corner."""
    x0, z0, w, h = 0.74, 0.70, 0.09, 0.52
    c, s = math.cos(-tilt), math.sin(-tilt)

    def R(x, z):
        return (x0 + (x - x0) * c - (z - z0) * s, z0 + (x - x0) * s + (z - z0) * c)
    body = [R(x0, z0), R(x0 + w, z0), R(x0 + w, z0 + h), R(x0, z0 + h)]
    G.stroke(d, body, M["plate"], O, cyclic=True)
    G.stroke(d, [R(x0 + w * 0.6, z0), R(x0 + w, z0), R(x0 + w, z0 + h), R(x0 + w * 0.6, z0 + h)], M["plate_sh"], 0.0, cyclic=True)
    G.rivets(d, [R(x0 + 0.03, z0 + 0.05), R(x0 + 0.03, z0 + h - 0.05)], M["ink"])
    G.hatch(d, *R(x0 + 0.05, z0 + 0.18), M["ink"], n=2, length=0.05, spacing=0.02, angle_deg=70, seed=3)
    if rivet_out is not None:                                                                  # a red rivet still proud of the plate
        rz = z0 + 0.30
        G.stroke(d, [R(x0 - rivet_out, rz - 0.022), R(x0 + 0.01, rz - 0.022), R(x0 + 0.01, rz + 0.022), R(x0 - rivet_out, rz + 0.022)],
                 M["rivet"], I, cyclic=True)
    G.stroke(d, body, M["ink"], O, cyclic=True)


def burst(d, M, c, r, n=6, a0=0.3):
    """Cartoon impact lines round c."""
    for k in range(n):
        a = a0 + TAU * k / n
        G.stroke(d, [(c[0] + r * math.cos(a), c[1] + r * math.sin(a)), (c[0] + 1.8 * r * math.cos(a), c[1] + 1.8 * r * math.sin(a))], M["ink"], I)


def chips(d, M, origin, t, seed):
    vel = [(0.9, 1.6), (1.4, 1.1), (0.4, 2.0), (1.8, 0.7), (0.2, 1.3)]
    for k, (vx, vz) in enumerate(vel):
        tt = 0.32 * t
        x, z = origin[0] + vx * tt, origin[1] + vz * tt - 3.0 * tt * tt
        r = 0.032 + 0.008 * (k % 3)
        if z < r + 0.03:
            continue
        G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.8, n=10, lump=0.12, seed=seed + k, rot=k), M["chip" if k % 2 else "chip2"], O, cyclic=True)


def puff(d, M, c, r, seed):
    blob = G.lumpy_ellipse(c[0], c[1], r * 1.15, r, n=18, lump=0.12, seed=seed)
    G.stroke(d, blob, M["puff"], O, cyclic=True)
    G.stroke(d, [q for q in blob if q[1] < c[1] - r * 0.25] + [(c[0], c[1] - r * 0.25)], M["puff_sh"], 0.0, cyclic=True)


def flame(d, M, nz, L, wob):
    """A downward teardrop flame from the nozzle point nz: red, mustard inside, an off-white core."""
    def shape(k, w):
        tip = (nz[0] + wob * k, nz[1] - L * k)
        return G.bezier((nz[0] - w, nz[1]), (nz[0] - w * 1.15, nz[1] - 0.45 * L * k), tip, n=10) + \
            G.bezier(tip, (nz[0] + w * 1.15, nz[1] - 0.45 * L * k), (nz[0] + w, nz[1]), n=10)[1:]
    G.stroke(d, shape(1.0, 0.085), M["flame"], O, cyclic=True)
    G.stroke(d, shape(0.68, 0.055), M["flame_in"], 0.0, cyclic=True)
    G.stroke(d, shape(0.36, 0.028), M["flame_core"], 0.0, cyclic=True)


def forearm(p):
    """draw_surveyor's front forearm (side view): the elbow (its bezier mid) and the hand."""
    sh = X1(p, 0.04, 1.00)
    h, _u = hand(p, 1)
    mid = ((sh[0] + h[0]) / 2 - 0.06, (sh[1] + h[1]) / 2 + 0.02)
    return mid, h


def beam_on_arm(d, M, p, seed):
    """B-210 (LEAD's Beam rule): the cable-fed Beam strapped along the front forearm, its nozzle toward the fingers, the cable
    from its back over the shoulder to the float pack - never in the hand, no grip."""
    e, h = forearm(p)
    L = math.hypot(h[0] - e[0], h[1] - e[1]) or 1.0
    u = ((h[0] - e[0]) / L, (h[1] - e[1]) / L)
    a, b = add(e, u, 0.18 * L), add(e, u, 0.74 * L)
    top = pack_point(p, -0.24, 1.10)
    sho = X1(p, -0.08, 1.16)
    G.stroke(d, G.hose_outline(G.bezier(a, ((a[0] + sho[0]) / 2 - 0.02, max(a[1], sho[1]) + 0.08), sho, n=8) + G.bezier(sho, (sho[0] - 0.08, sho[1] + 0.05), top, n=6)[1:],
                               0.03), M["boot_sh"], I, cyclic=True)                         # the cable, over the shoulder
    G.stroke(d, G.hose_outline([a, b], 0.085), M["teal"], O, cyclic=True)                  # the emitter
    n = (-u[1], u[0])
    for t in (0.35, 0.62):                                                                  # its straps round the arm
        c = add(a, (b[0] - a[0], b[1] - a[1]), t)
        G.stroke(d, G.hose_outline([add(c, n, -0.055), add(c, n, 0.055)], 0.022), M["mustard"], I * 0.8, cyclic=True)
    tip = add(b, u, 0.07)
    G.stroke(d, [add(b, n, -0.04), add(tip, n, -0.018), add(tip, n, 0.018), add(b, n, 0.04)], M["mustard"], I, cyclic=True)   # the nozzle


def reel(d, M, p, crank):
    """B-210: the grapple's hand reel at the front hand, its crank turning, the line leaving it upward (UNITY draws the line
    on from the 'reel' socket)."""
    h, _u = hand(p, 1)
    c = (h[0] + 0.02, h[1] + 0.04)
    G.stroke(d, G.hose_outline([(c[0] + 0.03, c[1] + 0.06), REEL_TOP(p)], 0.022), M["boot_sh"], I * 0.8, cyclic=True)   # the line stub
    G.stroke(d, G.lumpy_ellipse(c[0], c[1], 0.075, 0.075, n=20, lump=0.0, seed=3), M["steel"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(c[0], c[1], 0.045, 0.045, n=16, lump=0.0, seed=4), M["mustard"], I * 0.7, cyclic=True)   # the coil
    k = (math.cos(crank), math.sin(crank))
    G.stroke(d, G.hose_outline([c, add(c, k, 0.085)], 0.02), M["steel_sh"], I * 0.7, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(c[0] + 0.085 * k[0], c[1] + 0.085 * k[1], 0.02, 0.02, n=10, lump=0.0, seed=5), M["red"], I * 0.7, cyclic=True)


def REEL_TOP(p):
    h, _u = hand(p, 1)
    return (h[0] + 0.05, h[1] + 0.40)                                                       # the 'reel' socket: the line's start


# ---------------------------------------------------------------- one drawing

def draw_side_b(d, M, pose, seed=0):
    p = base(pose)
    hidden = p.get("hidden", False)
    if not hidden:
        SV.draw_surveyor(d, M, {k: v for k, v in pose.items() if k not in EXTRA}, seed=seed)
    if p.get("pick") is not None:
        h, u = hand(p, 1)
        tip = pick(d, M, (h[0], h[1] - 0.04), u, seed)
        front_glove(d, M, p, seed)
        if p.get("chips") is not None:                       # from the impact point, not from the lifting pick
            o = p.get("chips_at", tip)
            chips(d, M, (o[0] + 0.03, max(o[1], 0.06)), p["chips"], seed + 300)
        if p.get("impact"):
            burst(d, M, (tip[0], max(tip[1], 0.08) + 0.02), 0.07, n=5, a0=0.25)
            G.seam(d, G.bowed_line((tip[0] - 0.14, 0.03), (tip[0] + 0.12, 0.035), bow=0.08, n=6), M["ink"])   # the crack
    if p.get("plate") is not None:
        plate(d, M, p["plate"], p.get("rivet"))
        if p.get("snap"):
            for k in range(3):
                a = -0.6 + 0.6 * k
                G.stroke(d, [(0.86 + 0.06 * math.cos(a), 1.22 + 0.06 * math.sin(a)), (0.86 + 0.13 * math.cos(a), 1.22 + 0.13 * math.sin(a))], M["ink"], I)
    if p.get("hammer") is not None:
        h, u = hand(p, 1)
        face = hammer(d, M, (h[0], h[1] - 0.04), rot(u, p["hammer"]))
        front_glove(d, M, p, seed)
        if p.get("impact"):
            burst(d, M, face, 0.05, n=6)
    if p.get("flame") is not None:
        nz = pack_point(p, -0.36, 0.66)
        G.stroke(d, [(nz[0] - 0.06, nz[1] + 0.05), (nz[0] + 0.06, nz[1] + 0.05), (nz[0] + 0.045, nz[1]), (nz[0] - 0.045, nz[1])],
                 M["mustard"], I, cyclic=True)                                            # the nozzle
        L, wob = p["flame"]
        flame(d, M, (nz[0], nz[1] - 0.005), L, wob)
        for j, (t, r) in enumerate(p.get("puffs", [])):
            c = (nz[0] - 0.08 - 0.30 * t, nz[1] - L - 0.08 - 0.40 * t)
            c = (c[0] - 0.25 * max(0.0, r + 0.03 - c[1]), max(c[1], r + 0.03))       # rolls along the ground
            puff(d, M, c, r, seed + 400 + j)
    if p.get("beam_arm"):
        beam_on_arm(d, M, p, seed)
    if p.get("reel") is not None:
        reel(d, M, p, p["reel"])
        front_glove(d, M, p, seed)                                                         # the hand round the reel
    if p.get("vanish") is not None:
        t = p["vanish"]
        puff(d, M, (HATCH[0] - 0.05, HATCH[1] - 0.25 + 0.05 * t), 0.20 * (1 - 0.45 * t), seed + 500)
        if t < 0.5:
            puff(d, M, (HATCH[0] - 0.32, HATCH[1] - 0.55), 0.10, seed + 501)
        for k, z in enumerate((0.75, 1.05, 1.35)):
            G.stroke(d, G.bowed_line((HATCH[0] - 0.45 - 0.05 * k, z), (HATCH[0] - 0.75 - 0.10 * k - 0.2 * (1 - t), z + 0.02), bow=0.04, n=8), M["ink"], I)


EXTRA = ("pick", "chips", "chips_at", "impact", "plate", "rivet", "snap", "hammer", "flame", "puffs", "vanish", "hidden", "beam_arm", "reel")


# ---------------------------------------------------------------- the five clips

DIG_KEYS = [  # arms (back, front), sz, lean, bob, bob_tip, pack_swing, hose_lag, chips t, impact
    ((1.45, 1.60), 1.00, 0.00, 0.000, 0.00, 0.00, 0.00, None, 0),
    ((2.15, 2.35), 1.05, -0.04, 0.010, 0.05, -0.05, 0.03, None, 0),
    ((2.70, 2.90), 1.08, -0.08, 0.015, 0.08, -0.10, 0.05, None, 0),
    ((2.80, 3.00), 1.06, -0.09, 0.010, 0.09, -0.08, 0.05, None, 0),
    ((1.65, 1.80), 0.96, 0.08, -0.010, -0.02, 0.06, -0.03, None, 0),
    ((0.80, 0.78), 0.86, 0.12, -0.030, -0.10, 0.14, -0.06, 0.15, 1),
    ((0.82, 0.82), 0.90, 0.11, -0.020, -0.06, 0.10, -0.04, 0.45, 0),
    ((0.95, 1.00), 0.96, 0.08, 0.000, -0.02, 0.05, -0.02, 0.75, 0),
    ((1.15, 1.22), 1.00, 0.04, 0.000, 0.02, 0.00, 0.00, 1.00, 0),
    ((1.32, 1.45), 1.00, 0.02, 0.000, 0.00, 0.00, 0.00, None, 0),
]


def dig_poses():
    out = []
    for arms, sz, lean, bob, tip, sw, hl, ch, imp in DIG_KEYS:
        out.append(dict(expr="determined", arms=arms, sz=sz, lean=lean, bob=bob, bob_tip=tip, pack_swing=sw, hose_lag=hl,
                        legs=((-0.14, 0.0), (0.16, 0.0)), look=(0.7, -0.6), pick=True, chips=ch, impact=imp))
    hit = pick_tip(base(out[5]))
    for q in out:
        q["chips_at"] = hit
    return out


BUILD_KEYS = [  # front arm, hammer angle (+ = head raised back), sz, lean, plate tilt, rivet out, snap, impact
    (1.70, 0.25, 1.00, 0.02, 0.16, 0.06, 0, 0),
    (2.40, 0.95, 1.04, -0.03, 0.16, 0.06, 0, 0),
    (1.45, 0.00, 0.90, 0.08, 0.00, 0.06, 1, 1),
    (1.55, 0.10, 0.95, 0.06, -0.04, 0.06, 1, 0),
    (1.65, 0.20, 1.00, 0.03, 0.02, 0.06, 0, 0),
    (2.30, 0.90, 1.04, -0.02, 0.00, 0.06, 0, 0),
    (1.45, 0.00, 0.90, 0.08, 0.00, 0.00, 0, 1),
    (1.55, 0.10, 0.95, 0.06, -0.03, None, 0, 0),
    (1.65, 0.20, 1.00, 0.03, 0.015, None, 0, 0),
    (1.70, 0.25, 1.00, 0.02, 0.10, 0.06, 0, 0),
]


def build_poses():
    out = []
    for i, (fa, hm, sz, lean, tilt, rv, snap, imp) in enumerate(BUILD_KEYS):
        out.append(dict(expr="determined", arms=(0.35 + 0.1 * math.sin(TAU * i / 5), fa), sz=sz, lean=lean,
                        bob_tip=0.04 * math.sin(TAU * i / 5 - 1.2), pack_swing=0.05 * math.sin(TAU * i / 5 - 0.8),
                        hose_lag=0.03 * math.sin(TAU * i / 5 - 1.6), legs=((-0.10, 0.0), (0.10, 0.0)), look=(0.9, -0.1),
                        hammer=hm, plate=tilt, rivet=rv, snap=snap, impact=imp))
    return out


SURPRISE = [
    dict(sz=0.94, bob=-0.01, arms=(0.20, -0.10)),
    dict(expr="surprised", eye_pop=0.9, sz=0.86, bob=-0.03, arms=(0.60, 0.50), bob_tip=0.05),
    dict(expr="surprised", eye_pop=1.35, sz=1.24, bob=0.07, arms=(2.50, 2.30), helmet_dz=0.09, bob_tip=-0.14, pack_dz=0.06,
         pack_swing=0.10, hose_lag=0.06, legs=((-0.05, 0.05), (0.06, 0.06))),
    dict(expr="surprised", eye_pop=1.40, sz=1.18, bob=0.06, arms=(2.70, 2.50), helmet_dz=0.11, bob_tip=-0.10, pack_dz=0.04,
         pack_swing=0.06, legs=((-0.04, 0.04), (0.05, 0.05))),
    dict(expr="surprised", eye_pop=1.30, sz=1.08, bob=0.03, arms=(2.20, 2.00), helmet_dz=0.06, bob_tip=-0.02),
    dict(expr="surprised", eye_pop=1.20, sz=0.88, bob=-0.03, arms=(1.20, 1.00), bob_tip=0.08, pack_dz=-0.05),
    dict(expr="surprised", eye_pop=1.15, sz=1.05, arms=(0.90, 0.70), helmet_dz=0.025, bob_tip=-0.04),
    dict(expr="surprised", eye_pop=1.10, sz=0.98, arms=(0.60, 0.50), bob_tip=0.02),
    dict(expr="surprised", eye_pop=1.05, sz=1.01, arms=(0.40, 0.30)),
    dict(expr="surprised", sz=1.0, arms=(0.30, 0.20)),
    dict(sz=1.0, arms=(0.20, 0.10), blink=0.6),
    dict(sz=1.0, arms=(0.10, 0.0)),
]


def jetpack_poses():
    out = []
    for i in range(10):
        ph = TAU * i / 10
        puffs = []
        for j in range(2):
            t = ((i + 5 * j) % 10) / 10.0
            puffs.append((t, 0.05 + 0.07 * t))
        out.append(dict(arms=(1.25 + 0.15 * math.sin(ph), 1.70 - 0.15 * math.sin(ph)), legs=((-0.12, 0.20 + 0.03 * math.sin(ph)), (0.06, 0.14)),
                        bob=0.04 * math.sin(ph), sz=1.0 + 0.03 * math.cos(ph), lean=0.06, pack_swing=0.06 * math.sin(ph - 1.0),
                        bob_tip=0.10 + 0.05 * math.sin(ph - 1.4), hose_lag=0.06 * math.sin(ph - 1.8), look=(0.6, 0.2),
                        flame=(0.34 + 0.07 * math.sin(2 * ph) + 0.035 * math.sin(5 * ph), 0.03 * math.sin(3 * ph)), puffs=puffs))
    return out


def climb_poses():
    out = []
    for i in range(8):                                           # hand over hand, in place
        ph = TAU * i / 8
        out.append(dict(arms=(1.95 + 0.28 * math.sin(ph), 1.95 - 0.28 * math.sin(ph)), lean=0.05,   # hands beside the helmet, toward the fin-leg
                        legs=((-0.02, 0.10 + 0.10 * math.sin(ph)), (0.06, 0.10 - 0.10 * math.sin(ph))),
                        bob=0.05 + 0.03 * math.sin(2 * ph), sz=1.0 + 0.04 * math.cos(2 * ph), look=(0.3, 0.9),
                        bob_tip=0.04 * math.sin(ph - 1.0), pack_swing=0.05 * math.sin(ph - 0.8), hose_lag=0.04 * math.sin(ph - 1.5)))
    out += [dict(sz=0.86, lean=0.15, arms=(1.8, 1.6), legs=((-0.06, 0.05), (0.06, 0.04)), look=(0.9, 0.0), bob_tip=0.06),
            dict(sz=0.80, lean=0.25, shift=0.05, arms=(1.2, 1.0), legs=((-0.08, 0.02), (0.04, 0.02)), look=(1.0, 0.0), bob_tip=0.10, pack_swing=-0.08),
            dict(sz=0.66, lean=0.32, shift=0.40, arms=(1.6, 1.5), legs=((-0.20, 0.10), (-0.10, 0.12)), look=(1.0, 0.0), bob_tip=0.18,
                 pack_swing=-0.15, hose_lag=0.10, speed=1.0, expr="determined"),
            dict(sz=0.62, lean=0.36, shift=0.56, arms=(1.7, 1.6), legs=((-0.26, 0.14), (-0.18, 0.16)), look=(1.0, 0.0), bob_tip=0.22,
                 pack_swing=-0.20, hose_lag=0.14, speed=1.4, expr="determined"),
            dict(hidden=True, vanish=0.0),
            dict(hidden=True, vanish=1.0)]
    return out


RUNG = 0.25                     # B-210: the ladder's rung spacing (props/dig/ladder: four rungs a metre)
CLIMB = 0.5                     # metres climbed per climb_ladder cycle (UNITY lifts the root 0.5 m every 8 frames: 0.75 m/s)


def _arm_for(z, sh_z=1.0, reach=0.42):
    """The arm angle that puts draw_surveyor's hand at height z (the glove's centre 0.04 below it closes on the rung)."""
    c = -(z - sh_z) / reach
    return math.acos(max(-1.0, min(1.0, c)))


def ladder_poses():
    """B-210 climb_ladder (8, loop), rev (LEAD 20:0x): planted, not waved. In sprite space the rungs slide down 0.0625 m a
    frame (the root climbs 0.5 m a cycle); each hand grips a rung for four frames, riding down with it, then reaches two rungs
    up while the other grips; each foot stands on a rung the same way, half a cycle out of step with its hand. The ladder's
    centre line is the 'ladder' socket (0.38 m ahead): the hands close on rungs between its rails. No bob (the planted hands
    and feet set the body); looking up; the cable-fed Beam on the forearm, the pack on the back."""
    step = CLIMB / 8
    out = []
    for i in range(8):
        def planted(k, z0):                                                                   # gripping 4 frames, then 4 to reach
            if k < 4:                                                                         # two rungs up (lift on an arc)
                return z0 - step * k, 0.0
            t = (k - 4) / 4.0                                                                 # back to z0 at frame 8: +0.25 m in
            return z0 - step * 4 * (1 - t), math.sin(math.pi * t)                              # sprite space = +0.5 m (2 rungs) in world
        hz_a, arc_a = planted(i, 1.25 + 0.04)                                                 # the hands: rung 1.25 m at frame 0
        hz_b, arc_b = planted((i + 4) % 8, 1.25 + 0.04)
        fz_a, lift_a = planted((i + 4) % 8, RUNG)                                             # the feet: on the 0.25 m rung,
        fz_b, lift_b = planted(i, RUNG)                                                       # opposite their hands
        out.append(dict(arms=(_arm_for(hz_a) + 0.25 * arc_a, _arm_for(hz_b) + 0.25 * arc_b), lean=0.03,
                        legs=((0.16 + 0.04 * lift_a, fz_a + 0.02 + 0.06 * lift_a), (0.2 + 0.04 * lift_b, fz_b + 0.02 + 0.06 * lift_b)),   # soles on the rungs
                        bob=0.0, sz=1.0, look=(0.2, 0.9),
                        bob_tip=0.03 * math.sin(TAU * i / 8 - 1.0), pack_swing=0.03 * math.sin(TAU * i / 8 - 0.8),
                        hose_lag=0.03 * math.sin(TAU * i / 8 - 1.5), beam_arm=True))
    return out


def reel_poses():
    """B-210 reel_up (8, loop): hanging under the grapple line, the reel in the front hand winding (its crank turns), the back
    hand on the line, legs dangling and swaying, the plumb bob and hose trailing; the Beam on the forearm."""
    out = []
    for i in range(8):
        ph = TAU * i / 8
        out.append(dict(arms=(2.25 + 0.05 * math.sin(ph), 2.0 + 0.04 * math.sin(ph)), lean=0.05 * math.sin(ph),
                        legs=((-0.10 + 0.05 * math.sin(ph), 0.30 + 0.03 * math.sin(ph)), (0.05 + 0.05 * math.sin(ph + 1.0), 0.24 + 0.03 * math.cos(ph))),
                        bob=0.12, sz=1.04, look=(0.3, 0.8), expr="determined",
                        bob_tip=0.08 * math.sin(ph - 1.0), pack_swing=0.08 * math.sin(ph - 0.8), hose_lag=0.05 * math.sin(ph - 1.6),
                        beam_arm=True, reel=-TAU * i / 8))
    return out


def all_poses():
    return dig_poses() + build_poses() + SURPRISE + jetpack_poses() + climb_poses() + ladder_poses() + reel_poses()


def sockets():
    """Per-frame sockets in metres from the pivot (render.py's B-122 path): the hatch the zip ends at; B-210: on reel_up's
    frames the 'reel' socket, where UNITY's grapple line starts (it runs up from here to the hook)."""
    out = {}                                                     # every frame carries all three (render.py writes a socket only
    for f, pose in enumerate(all_poses()):                       # when it has one entry per frame); 'reel' matters on reel_up's,
        out[str(f + 1)] = {"hatch": list(HATCH), "reel": [round(v, 4) for v in REEL_TOP(base(pose))],   # 'ladder' on climb_ladder's
                           "ladder": list(LADDER)}
    return out


LADDER = (0.38, 0.0)                                             # B-210: the ladder's centre line under the reaching hands


def build(out=DEFAULT_OUT):
    """The source .blend (export path, inside Blender)."""
    scene = G.new_scene()
    coll = G.collection("surveyor")
    ob, gp = G.gp_object("surveyor", coll)
    M = materials(gp)
    layer = gp.layers.new("art")
    for f, pose in enumerate(all_poses()):
        draw_side_b(G.drawing(layer, f + 1), M, pose, seed=7 * f)
    G.mark_clips(scene, [(c, n) for c, n, _l in CLIPS])
    scene["sockets"] = json.dumps(sockets())
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


ENTRY = {"key": "characters/surveyor/side_b", "style": "v3", "palette_tints": [["sky", 0.25]],
         "source": "sources/characters/surveyor_side_b.blend", "build": "scripts/build_surveyor_side_b.py", "collection": "surveyor",
         "frame": [192, 192], "pivot": [0.5, 0.0], "facing": "right", "squash_root": True, "planet": "earth", "seed": SEED,
         "beside": "characters/surveyor/side", "review_name": "b134_surveyor_side_b",
         "clips": [{"name": c, "frames": n, "loop": lp} for c, n, lp in CLIPS],
         "self_check": {"ink": "the B-125 surveyor's line work + wood grain, steel shadow, plate rivets and hatch, chips, flame, puffs",
                        "motion": "pick and hammer swings with wind-up, smear and squash on the hit; helmet lifts on surprise; plumb bob, "
                                  "hose and pack drag on every move; the zip stretches 0.6 into the hatch",
                        "original": "the B-125 surveyor (accepted), our own tools and effects",
                        "style": "drawn with the side sheet's own function; LEAD judges"},
         "ours": "a surveyor with a plumb-bob antenna that swings behind every move, a teal meridian stripe and a float pack breathing through a rubber hose",
         "note": "B-134 (D-121): the five missing C1 clips; side untouched. B-210: + climb_ladder (8, loop) and reel_up (8, loop) with "
                 "the cable-fed Beam on the forearm; a 'reel' socket per frame (the grapple line's start on reel_up)"}


# ---------------------------------------------------------------- lock-free preview

def preview(out_dir):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import pngio, v3
    fw, fh = ENTRY["frame"]
    frames, widths, below = [], [], []
    for f, pose in enumerate(all_poses()):
        gp = fakegp.FakeGP()
        M = materials(gp)
        d = fakegp.FakeDrawing()
        draw_side_b(d, M, pose, seed=7 * f)
        st = fakegp.strokes_of(d, gp)
        zmin = min(float((s["xz"][:, 1] - s["radius"] * (1 + GR.JITTER)).min()) for s in st)
        if zmin * PPU < -2.0:
            below.append(f)
        img, w = GR.render_frame(st, fw, fh, PPU, (0.5, 0.0), ss=2, seed=SEED * 1000 + f + 1)
        frames.append(img)
        widths += w
    cols = v3.columns_for(fw, len(frames))
    rows = -(-len(frames) // cols)
    g = v3.GUTTER
    sheet = np.zeros((rows * fh + (rows - 1) * g, cols * fw + (cols - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw] = im
    anims, s = [], 0
    for c, n, lp in CLIPS:
        anims.append({"name": c, "start": s, "length": n, "loop": lp})
        if lp:
            anims[-1]["loop_from"] = 0
        s += n
    meta = {"key": ENTRY["key"], "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": g,
            "frames": len(frames), "fps": v3.FPS, "pivot": [0.5, 0.0], "facing": "right", "ppu": PPU, "animations": anims,
            "squash_root": True, "sockets": {"hatch": [list(HATCH)] * len(frames)},
            "sockets_units": "metres in sprite space from the pivot, one [x, y] per frame in sheet order"}
    problems = v3.validate_sheet(meta, sheet.shape)
    m = v3.EDGE_MARGIN
    clipped = [i for i, im in enumerate(frames) if im[:m, :, 3].any() or im[:, :m, 3].any() or im[:, -m:, 3].any()]
    if clipped:
        problems.append(f"frames {clipped[:8]} touch the {m} px frame edge")
    if below:
        problems.append(f"frames {below[:8]} draw more than 2 px below the ground line")
    side = json.load(open(os.path.join(review.ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
    clash = sorted({a["name"] for a in side["animations"]} & {c for c, _n, _l in CLIPS})
    if clash:
        problems.append(f"clip names also on side: {clash}")
    dd = os.path.join(out_dir, "b134")
    os.makedirs(dd, exist_ok=True)
    png = os.path.join(dd, "side_b_color.png")
    nb = pngio.write_png(png, sheet)
    with open(os.path.join(dd, "side_b.json"), "w", encoding="utf-8", newline="\n") as f_:
        json.dump(meta, f_, indent=2)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    rng = lambda ws: (min(w[1] for w in ws), max(w[2] for w in ws)) if ws else (0, 0)   # noqa: E731
    stats = {"outer_px": rng(outer), "inner_px": rng(inner), "inner_n": len(inner),
             "palette": v3.palette_hits(sheet, "earth", tints=[("sky", 0.25)]), "problems": problems,
             "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": nb // 1024}
    out = os.path.join(out_dir, "review_b134_surveyor_side_b_preview.png")
    boxes = review.v3_sheet_review(ENTRY, meta, frames, png, out, stats)
    fakegp.restore()
    print(f"side_b sheet {sheet.shape[1]}x{sheet.shape[0]} {nb // 1024} KB, {len(frames)} frames, ink {stats['outer_px'][0]:.2f}-"
          f"{stats['outer_px'][1]:.2f} / {stats['inner_px'][0]:.2f}-{stats['inner_px'][1]:.2f} px, palette {stats['palette'][0] * 100:.1f}% "
          f"{stats['palette'][1]}, problems {problems or '-'}, boxes not x: {','.join(k for k, (mk, _n) in boxes.items() if mk != 'x') or '-'}")


if __name__ == "__main__":
    preview(sys.argv[1])
