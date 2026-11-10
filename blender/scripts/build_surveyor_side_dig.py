"""B-246 (D-196, the owner's 0.6.2 playtest: "the digging feels disconnected from clicks and the avatar"): the body's half of
the dig as ONE motion - characters/surveyor/side_dig, a third sheet of the shipped surveyor (B-125's draw_surveyor, 192x192
frames, pivot [0.5, 0], PPU 64, 12 fps). side and side_b are not rewritten: this is a sheet of its own.

  dig_down   5 once  the shovel planted in the ground ahead       0 wind-up (up on the toes, the blade swung up)
  dig_fwd    5 once  the shovel thrust at a wall                  1 CONTACT ("contact": 1 - the arm at full reach, the
  dig_up     5 once  the shovel driven up at a ceiling              body's weight in it: the frame the work lands)
                                                                  2 follow-through   3 settle (the recoil)   4 recover
  aim_up, aim_up45, aim_fwd, aim_down45, aim_down   2 loop each   the Beam's aim poses: a two-drawing hold, the arm along
                                                                  its direction (straight up it stops ~55 deg above level:
                                                                  a vertical arm would cover the face; the socket's angle
                                                                  is the full 90)

The FRONT HAND IS EMPTY on every frame: UNITY's tool sprite rides the glove. Per frame the sheet's json carries "hand":
[x, z, angle] - the front glove's centre in metres from the pivot (x right, z up, facing right) and the TOOL's direction on
that drawing (rad, CCW from +x): on a dig clip the shovel's own swing (on the contact drawing UNITY turns it so its blade
tip, 1.33 m from the grip, meets the target), on an aim pose the aim direction. carry_sockets() gives the same triple for
`side`'s idle, walk and run: the tool held low at the side, not aimed.

The front arm is drawn HERE (front_arm), not by draw_surveyor (pose key front_arm=False, B-246's one line there): it lies
over the collar and the helmet's rim like a near arm, it stretches on the contact ("reach", the shipped arm is 0.42 m) and
bends on the wind-up ("elbow"). With reach 0.42 and the default elbow it is the shipped arm's strokes.

  python -I build_surveyor_side_dig.py <review png>     the lock-free sheet 1 (meridian.fakegp + numpy): every clip as a
                                                        strip at 1x and 2x with the shovel on the socket and its blade on
                                                        marked contact points, the aim poses with the Beam and a ray, the
                                                        carry frames, and the pose maths (the blade's honest reach)
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

O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
PPU = 64
FW = FH = 192
SEED = 6
KEY = "characters/surveyor/side_dig"
DIG = ("dig_down", "dig_fwd", "dig_up", "dig_fwd_near")
AIM = (("aim_up", 90.0), ("aim_up45", 45.0), ("aim_fwd", 0.0), ("aim_down45", -45.0), ("aim_down", -90.0))
CLIPS = [(c, 5, False) for c in DIG] + [(c, 2, True) for c, _a in AIM]
CONTACT = 1                             # the drawing of a dig clip on which the work lands (D-196: 0.08 s after the press)
SHOVEL_LEN = 1.33                       # props/rig/shovel: the blade tip from the grip (its json "blade_tip")
# rev 2 (LEAD 02:0x): the glove may grip the SHAFT - the tool slid back through it by up to slide_max metres on that clip,
# its D-grip end going back along its own line - so UNITY can put the blade tip ON a contact nearer than the shovel's
# length. dig_fwd_near is the mid-shaft hold for a face at the nose; dig_fwd and dig_up take a slide too so the ranges
# meet (reach_lines prints them). dig_down has none: a spade driven in up to 0.24 m is right (LEAD).
SLIDE_MAX = {"dig_fwd": 0.70, "dig_up": 0.55, "dig_fwd_near": 0.95}
CHEST = (0.0, 0.9)                      # the body's middle, for the reach numbers
ROLES = ("wind-up", "CONTACT", "follow-through", "settle", "recover")
DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "characters", "surveyor_side_dig.blend")
EXTRA = ("reach", "elbow", "tool", "feet")


def base(pose):
    q = dict(view="side", expr="determined", bob=0.0, sz=1.0, lean=0.0, legs=((0.0, 0.0), (0.0, 0.0)), arms=(0.0, 0.0),
             pack_swing=0.0, pack_dz=0.0, shift=0.0, reach=0.42, elbow=0.06, tool=None, feet=None)
    q.update(pose)
    if q["feet"] is not None:           # feet given as absolute x (m from the pivot): they stay planted while the body moves
        sx = 1.0 / math.sqrt(q["sz"])
        q["legs"] = tuple((q["feet"][k] - ((-0.05 + 0.10 * k) * sx + q["lean"] * 0.05 + q["shift"]), 0.0) for k in range(2))
    return q


def X1(p, x, z, pivot_z=0.55):
    """draw_surveyor's visual root: squash about the hips, bob, lean, shift."""
    return (x / math.sqrt(p["sz"]) + p["lean"] * (z - pivot_z) + p["shift"], pivot_z + (z - pivot_z) * p["sz"] + p["bob"])


def rot(v, a):
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def arm_points(p):
    """The front arm: shoulder, elbow (the bezier's middle), hand point, glove centre, unit direction. Angle 0 = hanging,
    pi / 2 = forward, pi = up (draw_surveyor's convention); the elbow bows to the arm's back side (back for a hanging arm,
    down for a forward one, forward for a raised one)."""
    sh = X1(p, 0.04, 1.00)
    a, r = p["arms"][1], p["reach"]
    u = (math.sin(a), -math.cos(a))
    hand = (sh[0] + r * u[0], sh[1] + r * u[1])
    nb = (u[1], -u[0])
    mid = ((sh[0] + hand[0]) / 2 + p["elbow"] * nb[0], (sh[1] + hand[1]) / 2 + p["elbow"] * nb[1])
    fl = math.hypot(hand[0] - mid[0], hand[1] - mid[1]) or 1.0
    t = ((hand[0] - mid[0]) / fl, (hand[1] - mid[1]) / fl)      # the FOREARM's direction (the curve's tangent at the hand):
    glove = (hand[0] + 0.04 * t[0], hand[1] + 0.04 * t[1])      # with a bent elbow it is not the shoulder-to-hand line
    return sh, mid, hand, glove, t


def nose_of(p):
    """draw_surveyor's nose (side view): its centre; radius 0.055. The glove (radius ~0.115) must stay clear of it."""
    hc = X1(p, 0.0, 1.52 + p.get("helmet_dz", 0.0))
    return (hc[0] + 0.35, hc[1] - 0.06)


def hand_of(pose):
    """[x, z, angle]: the glove's centre (m from the pivot) and the tool's direction (rad, CCW from +x; the forearm's own
    direction where the pose names no tool angle)."""
    p = base(pose)
    _sh, _mid, _hand, g, t = arm_points(p)
    ang = math.radians(p["tool"]) if p["tool"] is not None else math.atan2(t[1], t[0])
    return [round(g[0], 4), round(g[1], 4), round(ang, 4)]


def front_arm(d, M, p, seed):
    """draw_surveyor's arm(1), stroke for stroke, turned with the arm: the sleeve, its fold, the mustard cuff with its
    stitches, the glove with its two finger lines. The hand is EMPTY."""
    sh, mid, hand, g, t = arm_points(p)
    a = math.atan2(t[0], -t[1])         # the forearm's angle in draw_surveyor's convention (0 = hanging)

    def L(c, dx, dz):                   # an offset drawn for the hanging arm, turned to this forearm's direction
        r = rot((dx, dz), a)
        return (c[0] + r[0], c[1] + r[1])
    G.stroke(d, G.hose_outline(G.bezier(sh, mid, hand, n=10), 0.11), M["suit"], O, cyclic=True)
    G.seam(d, G.bowed_line(L(mid, -0.03, 0.02), L(mid, 0.025, -0.01), bow=0.2, n=4), M["ink"])
    cc = L((mid[0] * 0.15 + hand[0] * 0.85, mid[1] * 0.15 + hand[1] * 0.85), 0.0, 0.01)
    G.stroke(d, G.lumpy_ellipse(cc[0], cc[1], 0.085, 0.06, n=20, lump=0.05, seed=seed + 42, rot=a), M["mustard"], O, cyclic=True)
    G.stitches(d, [L(cc, -0.06, 0.0), L(cc, 0.06, 0.0)], M["ink"], every=0.03, length=0.02)
    G.stroke(d, G.lumpy_ellipse(g[0], g[1], 0.115, 0.105, n=24, lump=0.06, seed=seed + 22, rot=a), M["glove"], O, cyclic=True)
    G.stroke(d, G.bezier(L(g, -0.02, -0.01), L(g, 0.03, -0.03), L(g, 0.07, 0.01), n=6), M["ink"], I)
    G.seam(d, G.bowed_line(L(g, 0.0, 0.035), L(g, -0.005, -0.02), bow=0.1, n=4), M["ink"])


def draw_dig(d, M, pose, seed=0):
    p = base(pose)
    body = {k: v for k, v in p.items() if k not in EXTRA}
    body["front_arm"] = False
    SV.draw_surveyor(d, M, body, seed=seed)
    front_arm(d, M, p, seed)


# ---------------------------------------------------------------- the clips
# arms (back, front) in rad; reach (m) and elbow (m) of the front arm; tool = the shovel's direction on that drawing (deg,
# CCW from +x); feet = the two feet's x (m), planted; the rest as draw_surveyor's keys.
DIG_KEYS = {
    "dig_down": [
        # 0 wind-up: up on the toes, the hand drawn back to the chest, the blade swung up ahead
        dict(arms=(-0.55, 1.75), reach=0.34, elbow=0.13, tool=55, sz=1.07, lean=-0.07, bob=0.015, shift=-0.02, feet=(-0.08, 0.10),
             bob_tip=0.07, pack_swing=-0.08, hose_lag=0.04, look=(0.75, -0.35)),
        # 1 CONTACT: the lunge - the arm at full reach ahead of the helmet (the glove clear of the nose), the blade planted
        # in the ground in front
        dict(arms=(-1.05, 1.95), reach=0.58, elbow=0.02, tool=-75, sz=0.88, lean=0.20, bob=-0.09, shift=0.06, feet=(-0.14, 0.20),
             bob_tip=-0.11, pack_swing=0.15, pack_dz=-0.03, hose_lag=-0.06, look=(0.6, -0.8)),
        # 2 follow-through, rev 2 (LEAD: the first one drove the blade straight down at the toes - a second stab at one's own
        # feet): the HEAVE - the handle levered down to the hip, the blade lifted out of the ground ahead with its load
        # (about 0.45 m up), the body rocking back onto the rear foot. The clods fly up and back on this drawing
        dict(arms=(0.55, 0.25), reach=0.44, elbow=0.10, tool=-3, sz=0.97, lean=-0.10, bob=-0.04, shift=-0.03, feet=(-0.14, 0.20),
             bob_tip=-0.07, pack_swing=-0.12, pack_dz=0.03, hose_lag=0.05, look=(0.75, -0.25)),
        # 3 settle: the recoil - the body springs back up, the blade lifts clear with its scoop
        dict(arms=(-0.30, 1.55), reach=0.44, elbow=0.10, tool=-45, sz=1.04, lean=0.05, bob=0.01, shift=0.02, feet=(-0.11, 0.14),
             bob_tip=0.05, pack_swing=-0.06, pack_dz=0.03, hose_lag=0.03, look=(0.7, -0.5)),
        # 4 recover: toward idle, the tool coming down to the carry
        dict(arms=(-0.08, 0.45), reach=0.42, elbow=0.07, tool=-18, sz=1.0, lean=0.01, feet=(-0.07, 0.07),
             pack_swing=0.03, look=(0.6, -0.2)),
    ],
    "dig_fwd": [
        # 0 wind-up, rev 2 (LEAD: more coil; the first was nearly idle with the shovel level): the body back on the rear
        # foot and a little down, the elbow well back, the grip behind the hip, the shaft across the body
        dict(arms=(1.10, -0.75), reach=0.34, elbow=0.14, tool=8, sz=0.97, lean=-0.22, bob=-0.02, shift=-0.10, feet=(-0.20, 0.06),
             bob_tip=0.12, pack_swing=-0.14, hose_lag=0.06, look=(0.8, 0.0)),
        # 1 CONTACT: the thrust - a lunge onto the front foot, the arm at full reach, the blade at the wall
        dict(arms=(-1.20, 1.50), reach=0.58, elbow=0.02, tool=-4, sz=0.90, lean=0.26, bob=-0.05, shift=0.10, feet=(-0.16, 0.30),
             bob_tip=-0.13, pack_swing=0.18, pack_dz=-0.02, hose_lag=-0.07, look=(0.8, -0.1)),
        # 2 follow-through: the push - the body keeps coming, the blade drives in and dips with its load
        dict(arms=(-1.00, 1.45), reach=0.60, elbow=0.03, tool=-10, sz=0.88, lean=0.30, bob=-0.06, shift=0.13, feet=(-0.16, 0.30),
             bob_tip=-0.07, pack_swing=0.12, pack_dz=-0.04, hose_lag=-0.05, look=(0.8, -0.1)),
        # 3 settle: the recoil - back off the front foot, the blade pulled out and lifted
        dict(arms=(-0.35, 1.10), reach=0.44, elbow=0.10, tool=10, sz=1.03, lean=0.04, shift=0.02, feet=(-0.12, 0.20),
             bob_tip=0.06, pack_swing=-0.07, pack_dz=0.03, hose_lag=0.03, look=(0.75, 0.0)),
        # 4 recover
        dict(arms=(-0.08, 0.45), reach=0.42, elbow=0.07, tool=-16, sz=1.0, lean=0.01, feet=(-0.07, 0.08),
             pack_swing=0.03, look=(0.6, -0.1)),
    ],
    "dig_up": [
        # 0 wind-up: the crouch - knees and back give, the hand low, the blade ahead
        dict(arms=(-0.40, 0.55), reach=0.38, elbow=0.12, tool=20, sz=0.88, lean=-0.04, bob=-0.08, feet=(-0.10, 0.10),
             bob_tip=-0.05, pack_swing=0.06, pack_dz=-0.04, hose_lag=-0.03, look=(0.55, 0.6)),
        # 1 CONTACT: the spring - the whole body stretches up, the arm at full reach, the blade into the ceiling
        dict(arms=(-0.95, 2.15), reach=0.60, elbow=0.02, tool=58, sz=1.10, lean=0.08, bob=0.04, shift=0.03, feet=(-0.10, 0.12),
             bob_tip=0.10, pack_swing=-0.12, pack_dz=0.05, hose_lag=0.06, look=(0.45, 0.9)),
        # 2 follow-through: the blade scrapes on up and over (the hand stays ahead of the helmet: 2.35 put the glove on the nose)
        dict(arms=(-0.80, 2.10), reach=0.60, elbow=0.03, tool=72, sz=1.12, lean=0.10, bob=0.05, shift=0.04, feet=(-0.10, 0.12),
             bob_tip=0.06, pack_swing=-0.08, pack_dz=0.06, hose_lag=0.04, look=(0.4, 0.9)),
        # 3 settle: the drop back onto the heels, the blade coming down with its load
        dict(arms=(-0.25, 1.60), reach=0.45, elbow=0.10, tool=30, sz=0.95, lean=0.03, bob=-0.03, shift=0.01, feet=(-0.09, 0.10),
             bob_tip=-0.06, pack_swing=0.08, pack_dz=-0.04, hose_lag=-0.04, look=(0.6, 0.4)),
        # 4 recover
        dict(arms=(-0.08, 0.45), reach=0.42, elbow=0.07, tool=-14, sz=1.0, lean=0.01, feet=(-0.07, 0.07),
             pack_swing=0.03, look=(0.6, 0.0)),
    ],
    # rev 2 (LEAD 02:0x: "the near case is not an edge case, it is the tunnel"): a face 0.6-1.5 m ahead. A MID-SHAFT hold:
    # the front glove low at the hip on the shaft, the D-grip end going back across the body to the back hand, a short jab
    # with the weight behind it. The tool slides through this glove (SLIDE_MAX) so the blade tip meets the face.
    "dig_fwd_near": [
        # 0 wind-up: the body rocks well back (a face at 0.6 m leaves no room to lunge: the weight has to come from here),
        # the glove drawn back past the hip
        dict(arms=(-0.60, -0.40), reach=0.40, elbow=0.08, tool=3, sz=1.02, lean=-0.18, shift=-0.08, feet=(-0.15, 0.08),
             bob_tip=0.10, pack_swing=-0.12, hose_lag=0.05, look=(0.8, -0.15)),
        # 1 CONTACT: the jab - the hips and the shoulder go in behind the shaft, the glove a hand's width ahead of the belly
        dict(arms=(-0.55, 0.0), reach=0.40, elbow=0.10, tool=3, sz=0.93, lean=0.12, bob=-0.04, shift=0.08, feet=(-0.16, 0.22),
             bob_tip=-0.11, pack_swing=0.15, pack_dz=-0.02, hose_lag=-0.06, look=(0.8, -0.2)),
        # 2 follow-through: the push - the weight keeps coming, the blade dips with its load
        dict(arms=(-0.50, 0.32), reach=0.41, elbow=0.09, tool=-4, sz=0.91, lean=0.16, bob=-0.05, shift=0.11, feet=(-0.16, 0.22),
             bob_tip=-0.06, pack_swing=0.10, pack_dz=-0.03, hose_lag=-0.04, look=(0.8, -0.2)),
        # 3 settle: the recoil, the blade drawn back out and lifted
        dict(arms=(-0.40, -0.05), reach=0.41, elbow=0.09, tool=7, sz=1.03, lean=0.0, shift=0.02, feet=(-0.12, 0.16),
             bob_tip=0.05, pack_swing=-0.06, pack_dz=0.03, hose_lag=0.03, look=(0.75, -0.1)),
        # 4 recover
        dict(arms=(-0.08, 0.30), reach=0.42, elbow=0.07, tool=-12, sz=1.0, lean=0.01, feet=(-0.07, 0.08),
             pack_swing=0.03, look=(0.6, -0.1)),
    ],
}

# the Beam's aim poses: arm angle, reach, elbow, lean, shift, sz, bob, feet, look. The Beam lies along the FOREARM, so the
# forearm is what points: at 45 deg and level the whole arm is straight; straight up and straight down the elbow bends (the
# upper arm reaches ahead, the forearm stands plumb) - up, the hand is ahead of the helmet with the glove clear of the nose
# (a straight vertical arm would cover the face); down, the hand is ahead of the toes so the Beam clears the boot.
AIM_KEYS = {
    "aim_up": dict(arms=(-0.35, 2.40), reach=0.537, elbow=0.24, lean=-0.28, sz=1.03, feet=(-0.10, 0.06), look=(0.3, 1.0)),
    "aim_up45": dict(arms=(-0.30, 2.356), reach=0.58, lean=-0.14, sz=1.02, feet=(-0.09, 0.07), look=(0.55, 0.7)),
    "aim_fwd": dict(arms=(-0.25, 1.571), reach=0.50, lean=0.03, sz=1.0, feet=(-0.08, 0.08), look=(0.8, 0.0)),
    "aim_down45": dict(arms=(-0.30, 1.00), reach=0.50, lean=0.10, sz=0.98, feet=(-0.09, 0.09), look=(0.65, -0.6)),
    "aim_down": dict(arms=(-0.45, 0.72), reach=0.50, elbow=-0.24, lean=0.20, shift=-0.06, sz=0.95, bob=-0.02, feet=(-0.10, 0.08),
                     look=(0.4, -1.0)),
}


def aim_pose(name, deg, j):
    """Drawing j (0, 1) of a hold: the same pose breathing (a hair taller, the pack and the plumb bob settling)."""
    q = dict({"elbow": 0.03}, **AIM_KEYS[name])
    q["tool"] = deg
    q["sz"] = q.get("sz", 1.0) + 0.012 * j
    q.update(bob_tip=0.03 * j - 0.01, pack_swing=0.03 * j, pack_dz=-0.01 * j, hose_lag=0.015 * j)
    return q


def all_poses():
    out = []
    for c in DIG:
        out += DIG_KEYS[c]
    for c, deg in AIM:
        out += [aim_pose(c, deg, 0), aim_pose(c, deg, 1)]
    return out


def clip_start(name):
    s = 0
    for c, n, _l in CLIPS:
        if c == name:
            return s
        s += n
    raise KeyError(name)


def hand_sockets():
    """Per frame of side_dig: [x, z, angle] (hand_of)."""
    return [hand_of(pose) for pose in all_poses()]


# ---------------------------------------------------------------- the carry (side's idle, walk, run)
# the tool at rest: its angle (rad from +x), how much of the arm's own swing it takes, and whether it is drawn BEHIND the
# body. Two candidates for LEAD's pick (rev 2): "low" = the blade ahead and a little down (sheet 1: it read as a lance, and
# a tip 0.04 m over the ground meets every rising slope); "shouldered" = the glove where it is, the shaft leaning back over
# the shoulder behind the body, the blade up behind the helmet. The Beam's carry (a short tool, low at the side) is UNITY's.
CARRY = {"low": (-0.25, 0.25, False), "shouldered": (math.radians(110.0), 0.08, True)}
SIDE_CLIPS = (("idle", 0, 10, SV.idle_pose), ("walk", 10, 12, SV.walk_pose), ("run", 72, 12, SV.run_pose))


def carry_sockets(kind="low"):
    """{clip: {"start": side's first frame, "glove": [[x, z, angle], ...]}}: the front glove's centre on `side`'s frames
    (build_rig_tools_v3._hand's own maths) and the carried tool's direction for that carry."""
    base_a, swing, _behind = CARRY[kind]
    out = {}
    for name, start, n, fn in SIDE_CLIPS:
        rows = []
        for i in range(n):
            p = dict(view="side", bob=0.0, sz=1.0, lean=0.0, shift=0.0, arms=(0.0, 0.0))
            p.update(fn(i))
            a = p["arms"][1]
            sh = X1(p, 0.04, 1.00)
            h = (sh[0] + 0.42 * math.sin(a), sh[1] - 0.42 * math.cos(a))
            rows.append([round(h[0], 4), round(h[1] - 0.04, 4), round(base_a + swing * a, 4)])
        out[name] = {"start": start, "glove": rows}
    return out


def tip_of(hand, deg=None, slide=0.0):
    """The shovel's blade tip for a socket triple (its own angle, or `deg`), the tool slid back through the glove by `slide`."""
    a = hand[2] if deg is None else math.radians(deg)
    return (hand[0] + (SHOVEL_LEN - slide) * math.cos(a), hand[1] + (SHOVEL_LEN - slide) * math.sin(a))


def face_hit(hand, x_face, deg=None):
    """A vertical face at x_face ahead, the tool at its drawn angle (or deg): -> (the slide that puts the blade tip on the
    face, the tip). A negative slide = the face is past the blade."""
    a = hand[2] if deg is None else math.radians(deg)
    along = (x_face - hand[0]) / math.cos(a)
    return SHOVEL_LEN - along, (x_face, hand[1] + along * math.sin(a))


# the marked contact points of the sheet, per direction: (label, the shovel's angle in deg on the contact drawing). Each
# lies on the circle of the shovel's length about the contact drawing's glove: where the blade tip CAN be with the hand as
# drawn. "far" is the reach's edge in that direction.
MARKS = {"dig_down": (("near: at the toes", -122.0), ("far: the ground ahead", -55.0)),
         "dig_fwd": (("low: the foot of a wall", -35.0), ("far: straight ahead", 0.0)),
         "dig_up": (("steep: overhead", 80.0), ("far: ahead and up", 35.0)),
         "dig_fwd_near": (("low", -20.0), ("level", 3.0))}
FACES = (0.6, 1.2)                      # rev 2's two marked faces for dig_fwd_near (m ahead of the feet's centre)


def reach_lines():
    """The pose maths LEAD asked for: per direction the contact drawing's glove, and for each marked point the blade tip
    and its distance from the body's middle (0, 0.9) and from the feet; with a slide, how near the tip can come."""
    out = []
    for c in DIG:
        h = hand_of(DIG_KEYS[c][CONTACT])
        sm = SLIDE_MAX.get(c, 0.0)
        out.append(f"{c}: contact glove ({h[0]:+.2f}, {h[1]:.2f}) m, the tool drawn at {math.degrees(h[2]):+.0f} deg, slide_max {sm:g} m; "
                   f"the blade tip can be {SHOVEL_LEN - sm:.2f}-{SHOVEL_LEN} m from that glove, in any direction UNITY turns the tool:")
        for label, deg in MARKS[c] + (("as drawn", math.degrees(h[2])),):
            t = tip_of(h, deg)
            ln = (f"    {label} ({deg:+.0f} deg): tip ({t[0]:+.2f}, {t[1]:+.2f}) m = {math.hypot(t[0] - CHEST[0], t[1] - CHEST[1]):.2f} m "
                  f"from the body's middle, {t[0]:.2f} m ahead of the feet, {t[1]:+.2f} m from the ground line")
            if sm:
                n = tip_of(h, deg, sm)
                ln += f"; at the full slide ({n[0]:+.2f}, {n[1]:+.2f}), {math.hypot(n[0] - CHEST[0], n[1] - CHEST[1]):.2f} m from the body's middle"
            out.append(ln)
    hn, hf = hand_of(DIG_KEYS["dig_fwd_near"][CONTACT]), hand_of(DIG_KEYS["dig_fwd"][CONTACT])
    lo, hi = tip_of(hn, None, SLIDE_MAX["dig_fwd_near"])[0], tip_of(hn)[0]
    lo2, hi2 = tip_of(hf, None, SLIDE_MAX["dig_fwd"])[0], tip_of(hf)[0]
    out.append(f"A FACE AHEAD, the blade tip ON it at the drawn angles: dig_fwd_near {lo:.2f}-{hi:.2f} m (slide {SLIDE_MAX['dig_fwd_near']:g}-0), "
               f"dig_fwd {lo2:.2f}-{hi2:.2f} m (slide {SLIDE_MAX['dig_fwd']:g}-0); nearer than {lo:.2f} m the blade goes into the face")
    for xf in FACES:
        s, t = face_hit(hn, xf)
        out.append(f"    a face at {xf:g} m with dig_fwd_near: slide {s:.2f} m, the tip at ({t[0]:.2f}, {t[1]:.2f})"
                   + ("" if 0 <= s <= SLIDE_MAX["dig_fwd_near"] else f" - OUT of its slide (0-{SLIDE_MAX['dig_fwd_near']:g}): the blade is {s - SLIDE_MAX['dig_fwd_near']:.2f} m into it"))
    return out


def sockets():
    """Per-frame sockets for render.py's B-122 path: {frame: {"hand": [x, z, angle]}}."""
    return {str(f + 1): {"hand": h} for f, h in enumerate(hand_sockets())}


# what UNITY's reader takes from side_dig.json (LEAD 02:0x, its four asks): "sockets": {"hand": [[x, z, angle], ...]} with
# the name "hand" ONCE in the file and the angle in radians CCW from +x; per clip "contact" (0-based inside the clip) and,
# where it has one, "slide_max" (m); a top-level "carry": {"angle": radians} (the carried tool rides the idle glove)
SOCKETS_UNITS = ("per frame in sheet order: [x, z] metres from the pivot to the front glove's centre (x right, z up, facing "
                 "right) and the tool's direction on that drawing (radians, counter-clockwise from +x)")
CARRY_PICK = "low"                      # until LEAD picks between rev 2's two carry rows


def clip_fields(c):
    out = {}
    if c in DIG:
        out["contact"] = CONTACT
        if SLIDE_MAX.get(c):
            out["slide_max"] = SLIDE_MAX[c]
    return out


def carry_json(kind):
    a, swing, behind = CARRY[kind]
    return {"angle": round(a, 4), "swing": swing, "behind": behind,
            "note": "the tool at rest on side's idle / walk / run glove: its direction (radians, CCW from +x) plus swing x the "
                    "front arm's own angle; behind = sorted behind the body"}


def build(out=DEFAULT_OUT):
    """The source .blend (export path, inside Blender)."""
    scene = G.new_scene()
    coll = G.collection("surveyor")
    _ob, gp = G.gp_object("surveyor", coll)
    M = SV.materials(gp)
    layer = gp.layers.new("art")
    for f, pose in enumerate(all_poses()):
        draw_dig(G.drawing(layer, f + 1), M, pose, seed=7 * f)
    G.mark_clips(scene, [(c, n) for c, n, _l in CLIPS])
    scene["sockets"] = json.dumps(sockets())
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


ENTRY = {"key": KEY, "style": "v3", "palette_tints": [["sky", 0.25]],
         "source": "sources/characters/surveyor_side_dig.blend", "build": "scripts/build_surveyor_side_dig.py", "collection": "surveyor",
         "frame": [FW, FH], "pivot": [0.5, 0.0], "facing": "right", "squash_root": True, "planet": "earth", "seed": SEED,
         "beside": "characters/surveyor/side", "review_name": "b246_surveyor_side_dig",
         "clips": [dict({"name": c, "frames": n, "loop": lp}, **clip_fields(c)) for c, n, lp in CLIPS],
         "sockets_units": SOCKETS_UNITS, "json_extra": {"carry": carry_json(CARRY_PICK)},
         "note": "B-246 (D-196): the dig as one motion - dig_down / dig_fwd / dig_up / dig_fwd_near (5 each, contact on drawing "
                 "1, slide_max where the glove may grip the shaft) and the Beam's five aim holds (2 each); the front hand empty, "
                 "a socket [x, z, angle] per frame; side and side_b untouched. NOT in the manifest until LEAD's ACCEPTED"}


# ---------------------------------------------------------------- lock-free preview (sheet 1)
def grip_frame():
    """A PROPOSAL (rev 2, not carded): the front glove alone as a fist round a shaft - 32x32 @ PPU 64, pivot centre, the
    shaft along +x. UNITY's tool sprite is drawn over the body, so it covers the glove that holds it; this one sprite laid
    OVER the tool at the hand socket, turned to the tool's angle, makes the hand visibly hold the shaft (the mid-shaft hold
    needs it most). The glove's own strokes (draw_surveyor's), three finger lines across the shaft."""
    gp = fakegp.FakeGP()
    M = SV.materials(gp)
    d = fakegp.FakeDrawing()
    G.stroke(d, G.lumpy_ellipse(0.0, 0.0, 0.115, 0.105, n=24, lump=0.06, seed=22), M["glove"], O, cyclic=True)
    for x in (-0.05, 0.0, 0.05):
        G.seam(d, G.bowed_line((x, 0.062), (x + 0.012, -0.055), bow=0.12, n=4), M["ink"])
    img, _w = GR.render_frame(fakegp.strokes_of(d, gp), 32, 32, PPU, (0.5, 0.5), ss=2, seed=SEED * 1000 + 900)
    return img


def _frame(pose, f, draw=None):
    gp = fakegp.FakeGP()
    M = SV.materials(gp)
    d = fakegp.FakeDrawing()
    (draw or draw_dig)(d, M, pose, seed=7 * f)
    st = fakegp.strokes_of(d, gp)
    zmin = min(float((s["xz"][:, 1] - s["radius"] * (1 + GR.JITTER)).min()) for s in st)
    img, w = GR.render_frame(st, FW, FH, PPU, (0.5, 0.0), ss=2, seed=SEED * 1000 + f + 1)
    return img, w, zmin


def preview(out, footnote=None, rev2=True):
    """rev2 (the default): only what LEAD asked of rev 2 - the new clip, dig_down, dig_fwd and the two carry rows; the
    whole sheet (dig_up and the aim holds too, accepted as drawn) with --full. (All of it at once passed 1 GB.)"""
    import time
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import pngio, v3
    paper = np.array(review.PAPER, np.float32)
    soil = paper * 0.86
    red = np.array([0.85, 0.15, 0.1], np.float32)
    teal = np.array(v3.hex_rgb(G.PALETTES["earth"]["teal"]), np.float32) / 255.0
    ink = np.array(v3.hex_rgb(G.INK), np.float32) / 255.0
    art = review.ART

    def sprite(key):
        p = os.path.join(art, *key.split("/"))
        return pngio.read_png_np(p + "_color.png"), json.load(open(p + ".json", encoding="utf-8"))

    def halve(img):                     # a PPU 128 tool at the game's 64 px a metre
        f = img.astype(np.float32) / 255.0
        f[..., :3] *= f[..., 3:4]
        h, w = f.shape[0] // 2 * 2, f.shape[1] // 2 * 2
        s = f[:h, :w].reshape(h // 2, 2, w // 2, 2, 4).mean(axis=(1, 3))
        a = s[..., 3:4]
        s[..., :3] = np.where(a > 1e-6, s[..., :3] / np.maximum(a, 1e-6), 0.0)
        return np.clip(np.rint(s * 255), 0, 255).astype(np.uint8)

    def place(dst, img, pivot, deg, at):
        """img (straight RGBA uint8) over dst (opaque float RGB), its pivot (px, y down) at `at`, turned deg CCW on screen."""
        h, w = img.shape[:2]
        f = img.astype(np.float32) / 255.0
        t = math.radians(deg)
        c, s = math.cos(t), math.sin(t)
        R = math.hypot(max(pivot[0], w - pivot[0]), max(pivot[1], h - pivot[1])) + 2
        x0, x1 = max(int(at[0] - R), 0), min(int(at[0] + R) + 1, dst.shape[1])
        y0, y1 = max(int(at[1] - R), 0), min(int(at[1] + R) + 1, dst.shape[0])
        if x1 <= x0 or y1 <= y0:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        u, v = xx + 0.5 - at[0], yy + 0.5 - at[1]
        sx = pivot[0] + u * c - v * s - 0.5
        sy = pivot[1] + u * s + v * c - 0.5
        ix, iy = np.floor(sx).astype(int), np.floor(sy).astype(int)
        fx, fy = (sx - ix)[..., None], (sy - iy)[..., None]

        def tap(ax, ay):
            ok = (ax >= 0) & (ax < w) & (ay >= 0) & (ay < h)
            o = np.zeros(ax.shape + (4,), np.float32)
            px = f[ay[ok], ax[ok]]
            o[ok] = np.concatenate([px[..., :3] * px[..., 3:4], px[..., 3:4]], axis=-1)
            return o
        smp = (tap(ix, iy) * (1 - fx) * (1 - fy) + tap(ix + 1, iy) * fx * (1 - fy) + tap(ix, iy + 1) * (1 - fx) * fy
               + tap(ix + 1, iy + 1) * fx * fy)
        sub = dst[y0:y1, x0:x1]
        sub[...] = smp[..., :3] + sub * (1 - smp[..., 3:4])

    def seg(dst, a, b, width, col):
        """A straight line a -> b (px) of `width` px."""
        x0, x1 = max(int(min(a[0], b[0]) - width - 1), 0), min(int(max(a[0], b[0]) + width + 2), dst.shape[1])
        y0, y1 = max(int(min(a[1], b[1]) - width - 1), 0), min(int(max(a[1], b[1]) + width + 2), dst.shape[0])
        if x1 <= x0 or y1 <= y0:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32) + 0.5
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = max(dx * dx + dy * dy, 1e-6)
        t = np.clip(((xx - a[0]) * dx + (yy - a[1]) * dy) / L2, 0, 1)
        dd = np.hypot(a[0] + t * dx - xx, a[1] + t * dy - yy)
        cov = np.clip(width / 2 + 0.5 - dd, 0, 1)[..., None]
        sub = dst[y0:y1, x0:x1]
        sub[...] = col * cov + sub * (1 - cov)

    shovel, sj = sprite("props/rig/shovel")
    beam, bj = sprite("props/rig/beam")
    tools = {2: (shovel, (sj["pivot"][0] * shovel.shape[1], shovel.shape[0] * 0.5)),
             1: (halve(shovel), (sj["pivot"][0] * shovel.shape[1] / 2, shovel.shape[0] * 0.25))}
    beams = {2: (beam, (bj["pivot"][0] * beam.shape[1], beam.shape[0] * 0.5)),
             1: (halve(beam), (bj["pivot"][0] * beam.shape[1] / 2, beam.shape[0] * 0.25))}

    fist = grip_frame()
    fists = {1: fist, 2: np.repeat(np.repeat(fist, 2, 0), 2, 1)}

    def cell(frame, k, wide_m, hand=None, deg=None, tool="shovel", marks=(), label=None, slide=0.0, under=False, wall=None,
             grip=False):
        """One drawing on paper at k x: the 192 px frame at the left, `wide_m` metres of room past it, 1 m of ground below;
        the tool on the socket (hand = [x, z, angle]; deg overrides the angle; slide = the tool slid back through the glove
        by that many metres; under = the tool behind the body), a solid face from x = wall on, red crosses at `marks`."""
        W, H = int((3.0 + wide_m) * PPU) * k, (FH + PPU) * k
        img = np.tile(paper, (H, W, 1)).astype(np.float32)
        img[FH * k:] = soil
        img[FH * k:FH * k + max(1, k)] = ink * 0.6 + paper * 0.4

        def px(x, z):
            return ((1.5 + x) * PPU * k, (3.0 - z) * PPU * k)
        if wall is not None:
            x0 = int(px(wall, 0.0)[0])
            img[:FH * k, x0:] = soil
            img[:FH * k, x0:x0 + max(1, k)] = ink * 0.6 + paper * 0.4

        def put_tool():
            a = math.degrees(hand[2]) if deg is None else deg
            ar = math.radians(a)
            at = px(hand[0] - slide * math.cos(ar), hand[1] - slide * math.sin(ar))
            if tool == "beam":
                mz = (hand[0] + bj["muzzle"][0] * math.cos(ar) - bj["muzzle"][1] * math.sin(ar),
                      hand[1] + bj["muzzle"][0] * math.sin(ar) + bj["muzzle"][1] * math.cos(ar))
                far = (mz[0] + 6.0 * math.cos(ar), mz[1] + 6.0 * math.sin(ar))
                seg(img, px(*mz), px(*far), 3.0 * k, teal)
                place(img, beams[k][0], beams[k][1], a, at)
            else:
                place(img, tools[k][0], tools[k][1], a, at)
        if hand is not None and under:
            put_tool()
        f = frame.astype(np.float32) / 255.0
        f = np.repeat(np.repeat(f, k, 0), k, 1)
        sub = img[:FH * k, :FW * k]
        sub[...] = f[..., :3] * f[..., 3:4] + sub * (1 - f[..., 3:4])
        if hand is not None and not under:
            put_tool()
        if hand is not None and grip:                                    # the proposed fist, over the tool
            place(img, fists[k], (16.0 * k, 16.0 * k), math.degrees(hand[2]) if deg is None else deg, px(hand[0], hand[1]))
        for (mx, mz_) in marks:
            cx, cy = px(mx, mz_)
            seg(img, (cx - 5 * k, cy - 5 * k), (cx + 5 * k, cy + 5 * k), 1.5 * k, red)
            seg(img, (cx - 5 * k, cy + 5 * k), (cx + 5 * k, cy - 5 * k), 1.5 * k, red)
        if label:
            review._label(img, label, 4, 4, scale=1)
        return img

    def row(cells, W=1920):
        H = max(c.shape[0] for c in cells)
        r = np.tile(paper, (H, W, 1)).astype(np.float32)
        x = 0
        for c in cells:
            r[:c.shape[0], x:x + c.shape[1]] = c[:, :max(0, min(c.shape[1], W - x))]
            x += c.shape[1]
        return r

    def head(text, h=20):
        hd = np.tile(paper, (h, 1920, 1)).astype(np.float32)
        review._label(hd, text, 6, 4, scale=1)
        return hd

    poses = all_poses()
    hands = hand_sockets()
    frames, widths, below, nose = [], [], [], []
    for f, pose in enumerate(poses):
        img, w, zmin = _frame(pose, f)
        frames.append(img)
        widths += w
        if zmin * PPU < -2.0:
            below.append(f)
        pb = base(pose)
        gl, ns = arm_points(pb)[3], nose_of(pb)
        nose.append(math.hypot(gl[0] - ns[0], gl[1] - ns[1]))   # the glove (r 0.115) and the nose (r 0.055): 0.17 = touching
    idle, _w, _z = _frame(SV.idle_pose(0), 0, draw=lambda d, M, pose, seed=0: SV.draw_surveyor(d, M, pose, seed=seed))
    carry, carry_b = carry_sockets("low"), carry_sockets("shouldered")

    rows = [np.tile(paper, (30, 1920, 1)).astype(np.float32)]
    review._label(rows[0], "B-246 sheet 1 REV 2 (PREVIEW, nothing exported): the dig as one motion - the body. The front hand is EMPTY in the art; the shovel and the Beam here are the game's own sprites laid on each frame's socket. Red crosses = marked contact points", 6, 8)
    s = clip_start("dig_fwd_near")                                       # rev 2's new clip first: a face at 1.2 m and at 0.6 m
    hc = hands[s + CONTACT]
    for xf in FACES[::-1]:
        sl, tip = face_hit(hc, xf)
        sl = max(0.0, min(SLIDE_MAX["dig_fwd_near"], sl))
        rows.append(head(f"dig_fwd_near (NEW, the mid-shaft hold) at 1x on a face {xf:g} m ahead: drawings 0-4, the tool slid {sl:.2f} m back through the glove (half that on the recover) | at 2x: wind-up, CONTACT, follow-through"))
        cells = [cell(frames[s + j], 1, 0.75, hands[s + j], slide=sl if j < 4 else sl / 2, wall=xf, marks=(tip,) if j == CONTACT else (),
                      label=f"{j} {ROLES[j]}") for j in range(5)]
        rows.append(row(cells))
        rows.append(row([cell(frames[s + j], 2, 0.75, hands[s + j], slide=sl, wall=xf, marks=(tip,) if j == CONTACT else (),
                              label=f"{j} {ROLES[j]}") for j in (0, 1, 2)]))
    rows.append(head("A PROPOSAL (not carded): one 32 px sprite, the glove as a fist, laid OVER the tool at the socket so the hand visibly holds the shaft. dig_fwd_near's CONTACT at 2x: a face at 0.6 m without / with it | a face at 1.2 m without / with it"))
    cells = []
    for xf in FACES:
        sl, tip = face_hit(hc, xf)
        sl = max(0.0, min(SLIDE_MAX["dig_fwd_near"], sl))
        cells += [cell(frames[s + CONTACT], 2, 0.75, hc, slide=sl, wall=xf, label=f"{xf:g} m, as the game draws it today"),
                  cell(frames[s + CONTACT], 2, 0.75, hc, slide=sl, wall=xf, grip=True, label=f"{xf:g} m, with the fist over the shaft")]
    rows.append(row(cells))
    for c in (("dig_down", "dig_fwd") if rev2 else ("dig_down", "dig_fwd", "dig_up")):
        s = clip_start(c)
        hc = hands[s + CONTACT]
        (nl, nd), (fl, fd) = MARKS[c]
        near, far = tip_of(hc, nd), tip_of(hc, fd)
        rows.append(head(f"{c} at 1x: drawings 0-4 (the contact drawing's blade on the FAR mark, {fl}) | the contact drawing again with the blade on the NEAR mark ({nl}) | idle 0 with the tool at the carry"))
        cells = []
        for j in range(5):
            cells.append(cell(frames[s + j], 1, 1.5, hands[s + j], deg=fd if j == CONTACT else None,
                              marks=(far, near) if j == CONTACT else (), label=f"{j} {ROLES[j]}"))
        cells.append(cell(frames[s + CONTACT], 1, 1.5, hc, deg=nd, marks=(far, near), label="1 CONTACT, near"))
        cells.append(cell(idle, 1, 0.0, carry["idle"]["glove"][0], label="idle 0"))
        rows.append(row(cells))
        rows.append(head(f"{c} at 2x: wind-up, CONTACT (far mark), follow-through"))
        rows.append(row([cell(frames[s + j], 2, 1.5, hands[s + j], deg=fd if j == CONTACT else None,
                              marks=(far, near) if j == CONTACT else (), label=f"{j} {ROLES[j]}") for j in (0, 1, 2)]))
        rows.append(head(f"{c} at 2x: settle, recover, and the CONTACT again on the near mark"))
        rows.append(row([cell(frames[s + 3], 2, 1.5, hands[s + 3], label=f"3 {ROLES[3]}"),
                         cell(frames[s + 4], 2, 1.5, hands[s + 4], label=f"4 {ROLES[4]}"),
                         cell(frames[s + CONTACT], 2, 1.5, hc, deg=nd, marks=(far, near), label="1 CONTACT, near")]))
    for j in (() if rev2 else (0, 1)):
        rows.append(head(f"the Beam's aim poses at 1x, drawing {j} of each two-drawing hold: " + ", ".join(c for c, _a in AIM) + " (the Beam on the socket, a ray from its muzzle)"))
        rows.append(row([cell(frames[clip_start(c) + j], 1, 3.0, hands[clip_start(c) + j], tool="beam", label=c) for c, _a in AIM]))
    if not rev2:
        rows.append(head("aim_up45, aim_fwd, aim_down45 at 2x (drawing 0)"))
        rows.append(row([cell(frames[clip_start(c)], 2, 1.5, hands[clip_start(c)], tool="beam", label=c) for c in ("aim_up45", "aim_fwd", "aim_down45")]))
        rows.append(head("aim_up, aim_down at 2x (drawing 0)"))
        rows.append(row([cell(frames[clip_start(c)], 2, 1.5, hands[clip_start(c)], tool="beam", label=c) for c in ("aim_up", "aim_down")]))

    side_png = pngio.read_png_np(os.path.join(art, "characters", "surveyor", "side_color.png"))
    sm = json.load(open(os.path.join(art, "characters", "surveyor", "side.json"), encoding="utf-8"))
    g, cols = sm.get("gutter", v3.GUTTER), sm["columns"]

    def side_frame(i):
        r, c = divmod(i, cols)
        return side_png[r * (FH + g):r * (FH + g) + FH, c * (FW + g):c * (FW + g) + FW]
    rows.append(head("THE CARRY, row A = LOW (as sheet 1: the blade ahead and a little down): side's own exported frames with the shovel on the glove - idle 0, 5 | walk 0, 3, 6, 9 | run 0, 3, 6, 9"))
    cells, low = [], []
    for name, start, n, _fn in SIDE_CLIPS:
        for i in ((0, 5) if name == "idle" else (0, 3, 6, 9)):
            cells.append(cell(side_frame(start + i), 1, 0.0, carry[name]["glove"][i], label=f"{name} {i}"))
        low.append(f"{name} {min(tip_of(h)[1] for h in carry[name]['glove']):+.2f}")
    rows.append(row(cells))
    rows.append(head("THE CARRY, row B = SHOULDERED (the glove where it is, the shaft leaning back at 110 deg BEHIND the body, the blade up behind the helmet): the same frames"))
    cells = []
    for name, start, n, _fn in SIDE_CLIPS:
        for i in ((0, 5) if name == "idle" else (0, 3, 6, 9)):
            cells.append(cell(side_frame(start + i), 1, 0.0, carry_b[name]["glove"][i], label=f"{name} {i}", under=True))
    rows.append(row(cells))
    rows.append(head("the two carries at 2x: idle 0 and walk 3, LOW then SHOULDERED"))
    rows.append(row([cell(side_frame(st + i), 2, 0.0, carry[nm]["glove"][i], label=f"{nm} {i} low") for nm, st, i in (("idle", 0, 0), ("walk", 10, 3))]
                    + [cell(side_frame(st + i), 2, 0.0, carry_b[nm]["glove"][i], label=f"{nm} {i} shouldered", under=True) for nm, st, i in (("idle", 0, 0), ("walk", 10, 3))]))

    sheet_cols = v3.columns_for(FW, len(frames))
    sheet_rows = -(-len(frames) // sheet_cols)
    gg = v3.GUTTER
    sheet = np.zeros((sheet_rows * FH + (sheet_rows - 1) * gg, sheet_cols * FW + (sheet_cols - 1) * gg, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, sheet_cols)
        sheet[r * (FH + gg):r * (FH + gg) + FH, c * (FW + gg):c * (FW + gg) + FW] = im
    anims, s = [], 0
    for c, n, lp in CLIPS:
        anims.append({"name": c, "start": s, "length": n, "loop": lp})
        if lp:
            anims[-1]["loop_from"] = 0
        anims[-1].update(clip_fields(c))
        s += n
    meta = {"key": KEY, "style": "v3", "frame_width": FW, "frame_height": FH, "columns": sheet_cols, "gutter": gg,
            "frames": len(frames), "fps": v3.FPS, "pivot": [0.5, 0.0], "facing": "right", "ppu": PPU, "animations": anims,
            "squash_root": True, "sockets": {"hand": hands}, "sockets_units": SOCKETS_UNITS, "carry": carry_json(CARRY_PICK)}
    problems = v3.validate_sheet(meta, sheet.shape)
    if json.dumps(meta).count('"hand"') != 1:
        problems.append('the json names "hand" more than once (UNITY\'s socket reader finds the array by that name)')
    m = v3.EDGE_MARGIN
    clipped = [i for i, im in enumerate(frames) if im[:m, :, 3].any() or im[:, :m, 3].any() or im[:, -m:, 3].any()]
    if clipped:
        problems.append(f"frames {clipped[:8]} touch the {m} px frame edge")
    if below:
        problems.append(f"frames {below[:8]} draw more than 2 px below the ground line")
    on_nose = [f for f, dn in enumerate(nose) if dn < 0.19]
    if on_nose:
        problems.append(f"the glove is on or against the nose in frames {on_nose} (centre distances {[round(nose[f], 2) for f in on_nose]}, 0.17 = touching)")
    names = {c for c, _n, _l in CLIPS}
    for other in ("side", "side_b"):
        oj = json.load(open(os.path.join(art, "characters", "surveyor", other + ".json"), encoding="utf-8"))
        clash = sorted({a["name"] for a in oj["animations"]} & names)
        if clash:
            problems.append(f"clip names also on {other}: {clash}")
    dd = os.path.join(os.path.dirname(out), "b246")
    os.makedirs(dd, exist_ok=True)
    nb = pngio.write_png(os.path.join(dd, "side_dig_color.png"), sheet)
    with open(os.path.join(dd, "side_dig.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=2)
        fh.write("\n")
    with open(os.path.join(dd, "carry_sockets.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"low": carry, "shouldered": carry_b}, fh, indent=2)
        fh.write("\n")
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    rng = lambda ws: (min(w[1] for w in ws), max(w[2] for w in ws)) if ws else (0, 0)   # noqa: E731
    pal = v3.palette_hits(sheet, "earth", tints=[("sky", 0.25)])
    lines = [f"the sheet as it would export: {sheet.shape[1]}x{sheet.shape[0]}, {len(frames)} frames, {nb // 1024} KB (blender/preview/b246/side_dig_color.png + side_dig.json); "
             f"ink outer {rng(outer)[0]:.2f}-{rng(outer)[1]:.2f} px, interior {rng(inner)[0]:.2f}-{rng(inner)[1]:.2f} px; palette {pal[0] * 100:.1f}% {pal[1] or ''}; problems: {problems or 'none'}",
             "clips: " + ", ".join(f"{a['name']} {a['start']}+{a['length']}" + (" (contact 1)" if "contact" in a else "") for a in anims),
             "THE POSE MATHS (metres; x ahead of the feet's centre, z up from the ground line; the shovel is 1.33 m from grip to blade tip):"]
    lines += reach_lines()
    lines.append("the carried blade's lowest tip over each clip (m above the ground line): " + ", ".join(low))
    lines.append(f"the glove's nearest approach to the nose (centre to centre, 0.17 m = touching): {min(nose):.2f} m at frame {nose.index(min(nose))}")
    foot = np.tile(paper, (24 + 16 * len(lines), 1920, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-246 sheet 1 preview (lock-free, fakegp + numpy; not exported)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    fakegp.restore()
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)
    print("hand sockets:")
    for (c, n, _l) in CLIPS:
        s0 = clip_start(c)
        print("  " + c + ": " + " | ".join(f"({h[0]:+.2f}, {h[1]:.2f}, {math.degrees(h[2]):+.0f})" for h in hands[s0:s0 + n]))


if __name__ == "__main__":                       # python -I build_surveyor_side_dig.py <review png> [--full]
    preview(sys.argv[1], rev2="--full" not in sys.argv)
