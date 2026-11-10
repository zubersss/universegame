"""B-231 / U-199 (D-200; the owner's YES on USER-44, LEAD 11-10 11:4x): THE SURVEYOR'S FRAME SETS in ART v6.

Drop-ins for today's sheets: the same clip names, frame counts and fps, so UNITY swaps by key.
  characters/surveyor_v6/side       idle 10, walk 12, jump 8, land 8, run 12, fall 8 (slice 1; look_camera, bump,
                                    conk_out and dash are a later slice)
  characters/surveyor_v6/side_dig   dig_down 5, dig_fwd 5, dig_up 5, dig_fwd_near 5 (the contact on drawing 1), and
                                    the five aim holds, two drawings each; sockets.hand per frame as today
Every frame is its own DRAWING: a pose -> build_surveyor_v6.Fig -> the cel at 512 px per metre, shrunk to 128 (twice
the game's size, ppu 128). There is no cut-out part and no tween of pictures: where a frame is an in-between, it is
the POSE that is interpolated (the joint angles), and the figure is drawn fresh from it. The rhythm rules are on.

A clip is a short list of KEY POSES (hand-set numbers) and a rule for the frames between them:
  loop(keys, n)   keys evenly round the cycle, a smooth curve through them (walk, run: four keys a step, mirrored)
  once(keys, n)   keys at their phases, eased between (jump, land)
  the dig clips   five keys, no in-betweens; the hands are put ON the tool's line by reach (ik), from the tool's angle
                  and the near glove's place; the front glove's centre and that angle are the frame's socket

  python -I build_surveyor_frames_v6.py <review png>     slice 1 as ONE strip sheet (lock-free, numpy); nothing exported
"""
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio  # noqa: E402
import cel_v6 as CEL  # noqa: E402
import build_surveyor_v6 as SV  # noqa: E402

BOX_W, BOX_H, CX = 288, 320, 144                  # the frame box at 128 px per metre: 2.25 x 2.5 m, the pivot's column
GROUND = 20                                       # px of the box under the ground line (Fig's own): the pivot is [0.5, 20 / 320]
ONE = ("len_arm_n", "len_arm_f", "len_leg_n", "len_leg_f", "squash")      # keys whose rest value is 1, not 0
IDLE = SV.POSES["idle"]
SV.RHYTHM = True                                  # the figure's default since the owner's yes; set here too so the key poses below are measured with it
STAND = SV.skeleton(IDLE)["P"][1]                 # the pelvis's height standing (m)
SPEED = {"walk": 4.0, "run": 6.5, "stroll": 1.632}   # ground speeds (m/s): PlayerMotion.WalkSpeed and SprintSpeed (read 11-10); the stroll's own (0.136 m a frame)
ONLY_CLIPS = None                                 # the clips to draw (names), or all


# ---------------------------------------------------------------- poses between poses
def lerp_pose(a, b, t):
    return {k: a.get(k, 1.0 if k in ONE else 0.0) * (1 - t) + b.get(k, 1.0 if k in ONE else 0.0) * t for k in set(a) | set(b)}


def curve_pose(p0, p1, p2, p3, t):
    """A smooth curve through p1 .. p2 (Catmull-Rom), every joint by itself."""
    out = {}
    for k in set(p0) | set(p1) | set(p2) | set(p3):
        d = 1.0 if k in ONE else 0.0
        a, b, c, e = (q.get(k, d) for q in (p0, p1, p2, p3))
        out[k] = 0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - e) * t * t + (3 * b - a - 3 * c + e) * t ** 3)
    return out


def tidy(p):
    p["lift"] = max(0.0, p.get("lift", 0.0))
    p["squash"] = min(1.08, max(0.88, p.get("squash", 1.0)))
    return p


def loop(keys, n):
    m, out = len(keys), []
    for i in range(n):
        x = i / n * m
        j = int(x)
        out.append(tidy(curve_pose(keys[(j - 1) % m], keys[j % m], keys[(j + 1) % m], keys[(j + 2) % m], x - j)))
    return out


def once(keys, n):
    out = []
    for i in range(n):
        ph = i / (n - 1)
        for (p0, a), (p1, b) in zip(keys, keys[1:]):
            if ph <= p1 + 1e-9:
                t = min(1.0, max(0.0, (ph - p0) / (p1 - p0)))
                out.append(tidy(lerp_pose(a, b, t * t * (3 - 2 * t))))
                break
    return out


def mirror(p):
    """The other step: near and far change places, the twist turns the other way."""
    q = {}
    for k, v in p.items():
        if k.endswith("_n"):
            q[k[:-2] + "_f"] = v
        elif k.endswith("_f"):
            q[k[:-2] + "_n"] = v
        else:
            q[k] = -v if k == "twist" else v
    return q


def air(p, k=0.97):
    """Off the ground: the sprite's pivot is the body's foot point, so the pelvis keeps (k of) its standing height and
    the legs tuck up under it, instead of the lowest sole dropping to the ground line."""
    q = dict(p, lift=0.0)
    q["lift"] = max(0.0, STAND * k - SV.skeleton(q)["P"][1])
    return q


def leg_ik(hip, target, l1, l2):
    """The thigh's swing and the knee's bend (deg) that put the ankle on `target`: a knee bends ahead of the hip-ankle
    line (an elbow bends behind it: SV.ik)."""
    dx, dz = target[0] - hip[0], target[1] - hip[1]
    dist = min(math.hypot(dx, dz), l1 + l2 - 1e-4)
    a = math.atan2(dx, -dz)
    inner = math.acos(max(-1, min(1, (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist))))
    bend = math.pi - math.acos(max(-1, min(1, (l1 * l1 + l2 * l2 - dist * dist) / (2 * l1 * l2))))
    return math.degrees(a + inner), math.degrees(bend)


def roll(ft):
    """How far the ankle stands ahead of its flat-foot place when the foot (pitch ft, deg, toe up +) rolls on the
    ground: about the heel when the toe is up, about the toe when the heel is up."""
    q = SV.HEEL if ft > 0 else SV.TOE
    return -(SV.rot(q, math.radians(ft))[0] - q[0])


def plant(p, s, x, H=None):
    """The pose with leg `s` set by reach so that its foot's ground point is x metres ahead of the pivot. H: the
    pelvis's height over the ground (m) on that foot; None keeps the ankle's height under the hip as posed."""
    q = dict(p, lift=0.0)
    J = SV.skeleton(q)
    ll = q.get("len_leg_" + s, 1.0)
    ft = q.get("ft_" + s, 0.0)
    z = J["ank_" + s][1]
    if H is not None:                                                           # the ankle stands this high on its rolled foot
        az = -min(SV.rot(c, math.radians(ft))[1] for c in (SV.HEEL, SV.TOE))
        z = J["P"][1] - (H - az)
    q["th_" + s], q["kn_" + s] = leg_ik(J["hip_" + s], (x + roll(ft), z), SV.L_TH * ll, SV.L_SH * ll)
    return q


def cycle(step, n, stance=(), v=0.0, x0=0.0, tail=0, heights=None):
    """A two-step loop of n frames from ONE step's keys [(frame, pose)]: the other step is their mirror, n / 2 later; a
    smooth curve through the keys, every joint by itself. On the step's `stance` frames its foot is on the ground and
    is put there BY REACH: its ground point travels back exactly v metres a frame from x0, so at a ground speed of
    v x 12 m/s the foot does not slide. tail: for that many frames the foot of the step before is still down too.
    heights: the pelvis's height on each frame of a step, as a share of its standing height (the bob: lowest on the
    planted foot, highest in the air). (Run 2 left the height to the leg's own bend: 25 cm between two frames.)"""
    h = n // 2
    keys = list(step) + [(f + h, mirror(p)) for f, p in step]
    m, out = len(keys), []
    for i in range(n):
        j = max(k for k in range(m) if keys[k][0] <= i + 1e-9)
        f0 = keys[j][0]
        f1 = keys[j + 1][0] if j + 1 < m else keys[0][0] + n
        p = tidy(curve_pose(keys[(j - 1) % m][1], keys[j][1], keys[(j + 1) % m][1], keys[(j + 2) % m][1], (i - f0) / (f1 - f0)))
        k, s, o = i % h, "n" if i < h else "f", "f" if i < h else "n"
        H = heights[k] * STAND if heights else None
        if k in stance:
            p = plant(p, s, x0 - v * k, H)
            if k < tail:
                p = plant(p, o, x0 - v * (k + h))
        elif heights:
            p = air(p, heights[k])
        out.append(p)
    return out


def hold(body, hand, ang, two=True, far=None, gap=0.40, world=False):
    """A pose with the tool in the hands: `hand` = the near glove's place from the near shoulder (m; with world=True
    from the pivot, so a blade can be kept on its mark), `ang` = the tool's direction (deg, counter-clockwise from +x).
    The near arm reaches the glove; with two hands the far one takes the grip `gap` m back along the tool (0.4 = the
    shovel as carried; more when the front hand has slid down the shaft toward the blade, as a spade is held to cut)."""
    p = dict(body)
    J = SV.skeleton(p)
    a = math.radians(ang)
    near = hand if world else SV.add(J["sh_n"], hand)
    p["ua_n"], p["el_n"] = SV.ik(J["sh_n"], near, SV.L_UA, SV.L_FA)
    if two:
        p["ua_f"], p["el_f"] = SV.ik(J["sh_f"], SV.add(near, SV.mul((math.cos(a), math.sin(a)), -gap)), SV.L_UA, SV.L_FA)
    else:
        p.update(far or {"ua_f": 8, "el_f": 24})
    p["wr_n"], p["wr_f"], p["_tool"], p["_two"] = 20, 30, ang, 1.0 if two else 0.0
    return p


# ---------------------------------------------------------------- the key poses (degrees; see build_surveyor_v6.skeleton)
W_C = dict(SV.POSES["walk"])                                                     # the contact: the near heel down ahead
W_D = {"twist": -14, "arc": 9, "pelvis": 3, "chest": 7, "neck": 4, "th_n": 20, "kn_n": 24, "ft_n": 0, "th_f": -26, "kn_f": 52, "ft_f": -44,
       "ua_n": -20, "el_n": 16, "ua_f": 18, "el_f": 30}                          # down: the weight onto the near leg, its knee giving
W_P = {"twist": 0, "arc": 7, "pelvis": 2, "chest": 5, "neck": 4, "th_n": 2, "kn_n": 4, "ft_n": 0, "th_f": 18, "kn_f": 64, "ft_f": -12,
       "ua_n": -2, "el_n": 12, "ua_f": 2, "el_f": 22}                            # passing: the far leg folded through, the arms hanging
W_U = {"twist": 14, "arc": 8, "pelvis": 2, "chest": 6, "neck": 4, "th_n": -14, "kn_n": 8, "ft_n": -20, "th_f": 32, "kn_f": 30, "ft_f": 4,
       "ua_n": 18, "el_n": 26, "ua_f": -18, "el_f": 14}                          # up: off the near toes, the far leg reaching
# THE GAME MOVES AT 4.0 m/s ON FOOT AND 6.5 m/s SPRINTING (PlayerMotion.WalkSpeed, SprintSpeed), the clips play at 12 fps
# and nothing scales them by speed. The v3 surveyor's short legs shuffled under that; a figure of real proportions at
# 4 m/s cannot WALK (a walk's step is 0.8 m: 1.6 m/s; its feet would slide 2.4 times their stride). So the clip named
# "walk" is drawn as a LOPE (a foot down for three frames, a flight of three) and "run" as a SPRINT (two down, four in
# the air), each with its foot travelling back at exactly the game's speed. The true walk (W_*) is the clip "stroll"
# (LEAD 12:2x: a full pack slows the surveyor; UNITY takes it below about 2.2 m/s and plays each clip at a rate tied to
# the ground speed, 0.75 to 1.25 of its own: every clip's json carries "ground_speed").
# LEAD's revision (12:2x) of runs 2-5, where a step had three or four keys and the frames between were a curve through
# them: THE FLIGHT FRAMES READ AS ONE HELD SPLIT, and the lope and the sprint as one run. Now EVERY FRAME OF A STEP IS A
# KEY (six a step, the other step their mirror): through the flight the rear leg folds and swings under, the lead leg
# reaches down for the ground, the arms cross over; no two neighbours alike.
#   the LOPE: upright and easy - a low knee, the hands low and loose (open), a small bounce;
#   the SPRINT: a strong forward lean, a long stride (four frames in the air), the knee high, the arms pumping to the chin.
# legs, a frame: ((near thigh, knee, foot), (far thigh, knee, foot)); the near leg is the step's standing leg and is
# then set by reach on its ground frames (cycle), so its first rows are what the reach starts from.
LOPE = (((30, 14, 8), (-4, 84, -36)),             # 0 CONTACT: the near leg reaching, the far one folded behind, swinging under
        ((10, 34, 0), (16, 82, -28)),             # 1 DOWN: the near knee takes the weight, the far knee coming through, low
        ((-22, 14, -30), (34, 70, -14)),          # 2 PUSH-OFF: off the near toes
        ((-32, 26, -44), (40, 62, -6)),           # 3 in the air: the near leg trailing, the far knee at its (low) highest
        ((-24, 62, -40), (38, 38, 2)),            # 4 the near leg folding, the far shin swinging out
        ((-14, 80, -34), (32, 18, 8)))            # 5 the near leg under the body, the far foot reaching down for the ground
LOPE_BODY = {"arc": 6, "pelvis": 3, "chest": 6, "neck": 4, "head": 0}
LOPE_H = (0.93, 0.925, 0.945, 0.96, 0.97, 0.955)  # the pelvis's height a frame, of standing: a bounce of 4.5 cm
SPRINT = (((22, 44, 0), (36, 124, -40)),          # 0 MID-STANCE: the weight on the near foot, the far heel up to the seat
          ((-28, 16, -40), (64, 112, -24)),       # 1 PUSH-OFF: the near leg driven out behind, the far knee driving up
          ((-40, 34, -50), (78, 100, -10)),       # 2 in the air: the near leg at full stretch behind, the far knee at its highest
          ((-30, 80, -48), (72, 70, 0)),          # 3 the near leg folding, the far shin swinging out
          ((-8, 112, -44), (56, 40, 6)),          # 4 the near heel to the seat, the far leg reaching
          ((16, 126, -40), (38, 26, 4)))          # 5 the near knee coming through, the far foot coming down under the body
SPRINT_BODY = {"arc": 10, "pelvis": 16, "chest": 30, "neck": -4, "head": -14}
SPRINT_H = (0.93, 0.95, 0.97, 0.985, 0.975, 0.955)


def gait(legs, body, amp, lead, elbow, twist, extra=None):
    """One step's keys, a drawing a frame: the legs as tabled; the arms a sine against the legs (amp deg; the near arm
    is forward-most `lead` frames after frame 3, the far arm its opposite); the elbow elbow[0] +- elbow[1], more bent
    as the arm comes forward; the shoulders turned with the arms (twist a degree of arm); extra: {frame: more keys}."""
    keys = []
    for k, (n, f) in enumerate(legs):
        sw = math.sin(2 * math.pi * (k - lead) / 12.0)
        p = dict(body)
        p.update({"th_n": n[0], "kn_n": n[1], "ft_n": n[2], "th_f": f[0], "kn_f": f[1], "ft_f": f[2],
                  "ua_n": amp * sw, "el_n": elbow[0] + elbow[1] * sw, "ua_f": -amp * sw, "el_f": elbow[0] - elbow[1] * sw, "twist": twist * amp * sw})
        p.update((extra or {}).get(k, {}))
        keys.append((k, p))
    return keys
I_B = dict(IDLE, chest=2.5, arc=8, head=4, th_f=11, ua_n=-5, el_n=16, ua_f=8, el_f=24)       # the idle's breath, in
J_0 = {"arc": 18, "pelvis": 22, "chest": 38, "neck": 10, "head": 4, "th_n": 72, "kn_n": 104, "th_f": 66, "kn_f": 100, "ft_f": -12,
       "ua_n": -52, "el_n": 20, "ua_f": -40, "el_f": 26, "squash": 0.95}         # the jump's anticipation: down, the arms back
# (Runs 1-5: in the jump's take-off both arms stood out level, a sleepwalker. LEAD 12:2x: the arms SWING from behind the
# hips up through the take-off, the far arm a beat behind the near one, and are relaxed at the apex.)
J_1 = {"twist": 4, "arc": 4, "pelvis": 10, "chest": 16, "th_n": 30, "kn_n": 44, "ft_n": -8, "th_f": 24, "kn_f": 40, "ft_f": -14,
       "ua_n": 8, "el_n": 26, "ua_f": -26, "el_f": 24}                           # the launch: the legs opening, the near arm swinging down through, the far one still behind
J_2 = {"twist": 10, "arc": -10, "chest": 2, "neck": -6, "th_n": 6, "kn_n": 6, "ft_n": -44, "th_f": -8, "kn_f": 10, "ft_f": -50,
       "ua_n": 104, "el_n": 34, "ua_f": 20, "el_f": 30, "squash": 1.05, "len_leg_n": 1.04, "len_leg_f": 1.04}   # off the toes, drawn out: the near arm up ahead, the far one coming through below it
J_2B = air({"twist": 12, "arc": -12, "chest": 0, "neck": -8, "th_n": 14, "kn_n": 30, "ft_n": -46, "th_f": -4, "kn_f": 26, "ft_f": -50,
            "ua_n": 138, "el_n": 28, "ua_f": 84, "el_f": 40}, 1.0)               # just off the ground: the near arm at the top of its swing, the far one a beat behind
J_3 = air(dict({k: v for k, v in SV.POSES["jump"].items() if k not in ("lift", "len_arm_n")},
               ua_n=28, el_n=34, ua_f=-14, el_f=30), 0.98)                        # the apex (the model sheet's legs), tucked up under the pelvis; the arms have come down, one a little ahead and one behind (run 6: both level ahead again)
F_0 = air({"twist": -6, "arc": -8, "pelvis": -2, "chest": -4, "neck": 6, "head": 8, "th_n": 26, "kn_n": 44, "ft_n": -24, "th_f": -6, "kn_f": 52,
           "ft_f": -34, "ua_n": 116, "el_n": 30, "ua_f": 56, "el_f": 48})        # falling: one arm up, one out, the legs loose
F_1 = air({"twist": 6, "arc": -6, "pelvis": -1, "chest": -2, "neck": 6, "head": 8, "th_n": 14, "kn_n": 34, "ft_n": -28, "th_f": 6, "kn_f": 62,
           "ft_f": -30, "ua_n": 100, "el_n": 44, "ua_f": 74, "el_f": 36})
L_0 = {"arc": 2, "pelvis": 4, "chest": 8, "neck": 2, "th_n": 16, "kn_n": 22, "ft_n": -14, "th_f": 6, "kn_f": 26, "ft_f": -22,
       "ua_n": 34, "el_n": 26, "ua_f": -10, "el_f": 34}                          # the landing's touch: the toes reaching, one arm a little ahead and one behind (runs 1-3: both level ahead, a sleepwalker)
L_1 = {"arc": 20, "pelvis": 26, "chest": 44, "neck": 14, "head": 8, "th_n": 82, "kn_n": 112, "th_f": 70, "kn_f": 106, "ft_f": -14,
       "ua_n": 34, "el_n": 40, "ua_f": 22, "el_f": 48, "squash": 0.92}           # the squash: folded, pressed down
L_2 = {"twist": 2, "arc": 10, "pelvis": 8, "chest": 14, "neck": 6, "th_n": 30, "kn_n": 44, "th_f": 26, "kn_f": 46, "ft_f": -10,
       "ua_n": 2, "el_n": 22, "ua_f": 12, "el_f": 28, "squash": 1.02}            # the rebound
# the dig's bodies (no arms: the hands are set by hold())
B_LUNGE = {k: v for k, v in SV.POSES["dig"].items()}
B_DEEP = dict(B_LUNGE, chest=36, arc=28, th_n=54, kn_n=70)
B_HALF = {"twist": 8, "arc": 12, "pelvis": 8, "chest": 14, "neck": 8, "head": 6, "th_n": 34, "kn_n": 38, "th_f": -20, "kn_f": 14, "ft_f": -20}
B_READY = {"twist": 4, "arc": 6, "chest": 6, "neck": 4, "th_n": 10, "kn_n": 10, "th_f": -4, "kn_f": 8, "ft_f": -6}
B_BACK = {"twist": -10, "arc": 4, "pelvis": 2, "chest": 4, "head": -4, "th_n": 24, "kn_n": 20, "th_f": -14, "kn_f": 10, "ft_f": -14}
B_CUT = {"twist": 14, "arc": 16, "pelvis": 10, "chest": 20, "neck": 10, "head": 8, "th_n": 44, "kn_n": 50, "th_f": -28, "kn_f": 16, "ft_f": -32}   # the cut: a step in, the weight over the front knee, the eyes on the blade
B_JAB = {"twist": 12, "arc": 10, "pelvis": 6, "chest": 14, "neck": 6, "th_n": 26, "kn_n": 28, "th_f": -14, "kn_f": 10, "ft_f": -14}
B_LOW = {"twist": -8, "arc": 14, "pelvis": 10, "chest": 20, "neck": 2, "head": -10, "th_n": 40, "kn_n": 56, "th_f": -10, "kn_f": 30, "ft_f": -16}
B_HIGH = {"twist": 16, "arc": -12, "pelvis": -2, "chest": -6, "neck": -14, "head": -22, "th_n": 16, "kn_n": 8, "ft_n": -8, "th_f": -16, "kn_f": 6, "ft_f": -30, "len_arm_n": 1.06}
B_EASE = {"twist": 6, "chest": 2, "neck": -4, "head": -8, "th_n": 12, "kn_n": 10, "th_f": -8, "kn_f": 8, "ft_f": -10}
B_AIM = {"twist": 8, "arc": 4, "chest": 4, "neck": 4, "th_n": 6, "kn_n": 6, "th_f": -6, "kn_f": 8, "ft_f": -6}
READY = (B_READY, (0.20, -0.42), -14)             # the drawing every dig clip ends on: the tool low in front (the ready pose)
DIG = {                                           # five drawings a clip: wind-up, CONTACT, follow-through, settle, recover
    "dig_down": [(B_BACK, (0.10, -0.10), 62), (B_LUNGE, (0.33, -0.36), -62), (B_DEEP, (0.30, -0.44), -40), (B_HALF, (0.26, -0.30), -30), READY],
    # (Runs 1-5: dig_fwd and dig_fwd_near were a LEVEL two-handed drive: on this figure, with a long shaft, a spear lunge.
    # LEAD 12:2x, D-087 (a tool, never a weapon): a spade CUT - the rear hand high at the shoulder on the grip, the front
    # hand low on the shaft, the blade driven DOWN and forward into the face; then the handle is levered down so the
    # blade prises out; then the load is lifted. A fourth number = how far apart the hands are on the tool.)
    # (Run 6: the lever drawing held the spade LEVEL at the hip in a lunge, its blade half a metre up and on from the
    # cut: a thrust again. A lever turns ABOUT THE BLADE: the tip stays at the cut, the handle comes down, the body
    # bends over it. Those drawings give the glove's place from the pivot - a fifth entry, True - worked back from the tip.)
    "dig_fwd": [(B_BACK, (0.18, -0.16), -16, 0.55), (B_CUT, (0.42, -0.44), -32, 0.55),
                (dict(B_CUT, chest=34, arc=22, th_n=50, kn_n=62), (0.45, 0.64), -12, 0.45, True),       # the tip about (1.36, 0.45): 7 cm up from the cut at (1.38, 0.39)
                (B_HALF, (0.34, -0.40), 12, 0.5), READY],
    "dig_up": [(B_LOW, (0.16, -0.50), 20), (B_HIGH, (0.26, 0.38), 60), (B_HIGH, (0.30, 0.36), 72), (B_EASE, (0.30, -0.10), 30), READY],
    "dig_fwd_near": [(dict(B_BACK, twist=-6), (0.08, -0.20), -24, 0.6), (B_JAB, (0.26, -0.46), -40, 0.6),
                     (dict(B_JAB, chest=26, arc=16, th_n=36, kn_n=46), (0.23, 0.67), -18, 0.45, True),     # the tip about (1.11, 0.38); the cut at (1.13, 0.32)
                     (B_READY, (0.22, -0.42), 12, 0.5), READY],
}
AIM = {                                           # the Beam in the near hand: the arm along its direction; two drawings each (a held boil)
    "aim_up": (dict(B_AIM, arc=-10, chest=-6, neck=-16, head=-26), (0.06, 0.50), 90),
    "aim_up45": (dict(B_AIM, arc=-6, chest=-2, neck=-8, head=-14), (0.36, 0.36), 45),
    "aim_fwd": (B_AIM, (0.52, -0.02), 0),
    "aim_down45": (dict(B_AIM, arc=10, chest=12, neck=10, head=10), (0.38, -0.36), -45),
    "aim_down": (dict(B_AIM, arc=14, chest=16, neck=14, head=18), (0.10, -0.52), -90),
}


def fists(poses):
    """The hands closed (run 2: a runner with open flat hands carried two trays)."""
    return [dict(p, _fist=1.0) for p in poses]


def clips():
    """[(sheet, clip, [pose, ...], what the keys are)] for slice 1, in the shipped sheets' order."""
    wv, sv = SPEED["walk"] / 12.0, SPEED["run"] / 12.0                           # metres a frame at 12 fps
    lope = gait(LOPE, LOPE_BODY, 30, 0.5, (30, 8), 0.45, {0: {"len_leg_n": 1.03}, 1: {"squash": 0.985}})   # (run 6: elbows at 52 and open palms held both hands out in front, a tray again: the arms hang and swing past the hips, loose fists)
    sprint = gait(SPRINT, SPRINT_BODY, 62, -0.5, (91, 9), 0.48, {1: {"len_leg_n": 1.04}})
    # PAGES (LEAD 12:2x), each one sheet of at most 2048 x 2048: at this box and a 4 px gutter a sheet holds 7 x 6 = 42
    # frames. side with the stroll would be 46, so the stroll rides side_air (36); side is 34.
    side = [("side", "idle", loop([IDLE, I_B], 10), "2 keys (the breath out, in), 8 in-betweens"),
            ("side", "walk", fists(cycle(lope, 12, (0, 1, 2), wv, wv, heights=LOPE_H)),
             f"a LOPE for the game's {SPEED['walk']:.1f} m/s: EVERY FRAME A KEY (6 a step, the other step their mirror); a foot down on frames 0-2 / 6-8 (set by reach), in the air 3-5 / 9-11; upright, the arms hanging and swinging past the hips"),
            ("side", "run", fists(cycle(sprint, 12, (0, 1), sv, 0.06, heights=SPRINT_H)),
             f"a SPRINT for the game's {SPEED['run']:.1f} m/s: EVERY FRAME A KEY (6 a step, mirrored); a foot down on frames 0-1 / 6-7 (by reach), in the air 2-5 / 8-11; a strong lean, the knee high, the fists to the chin"),
            ("side_air", "jump", once([(0.0, J_0), (0.2, J_1), (0.42, J_2), (0.6, J_2B), (1.0, J_3)], 8), "5 keys (anticipation, launch, off the toes, just off the ground, the apex), 3 in-betweens"),
            ("side_air", "fall", loop([F_0, F_1], 8), "2 keys, 6 in-betweens"),
            ("side_air", "land", once([(0.0, L_0), (0.3, L_1), (0.62, L_2), (1.0, IDLE)], 8), "4 keys (touch, squash, rebound, the idle), 4 in-betweens"),
            ("side_air", "stroll", cycle([(0, W_C), (1.5, W_D), (3, W_P), (4.5, W_U)], 12, (0, 1, 2, 3, 4, 5), SPEED["stroll"] / 12.0, 0.35, tail=1),
             f"a true WALK at {SPEED['stroll']:.2f} m/s for a loaded pack (4 keys a step: contact, down, passing, up; 4 in-betweens a step), a foot always down, set by reach")]
    far = {"ua_f": -6, "el_f": 26}                                              # (run 1: both hands on a tool held low put the far elbow out behind the pack, a loop)
    dig = []
    for name, ks in DIG.items():
        poses = [hold(k[0], k[1], k[2], two=i < 3 or (len(k) > 3 and i < 4), far=far, gap=k[3] if len(k) > 3 else 0.40, world=len(k) > 4 and k[4])
                 for i, k in enumerate(ks)]
        dig.append(("side_dig", name, poses, "5 keys, every drawing a key (no in-betweens); the contact is drawing 1; both hands on the tool until the ready pose"
                    + (" (a spade CUT: the rear hand high, the blade driven down into the face, the handle levered down, the load lifted)" if len(ks[0]) > 3 else "")))
    for name, (b, h, a) in AIM.items():
        dig.append(("side_dig", name, [hold(b, h, a, two=False), hold(dict(b, chest=b.get("chest", 0) + 1.0), (h[0], h[1] - 0.006), a, two=False)], "1 key drawn twice (the hold's boil)"))
    return side + dig


def planted(p):
    """Which foot carries the pose (the one whose sole is lowest; "air" when both are off the ground) and its ground
    point's x from the pivot (m): a planted foot must travel back at the game's ground speed, or it slides."""
    if p.get("lift", 0.0) > 0.004:
        return "air", 0.0
    J, low = SV.skeleton(p), {}
    for s in ("n", "f"):
        low[s] = min(SV.add(J["ank_" + s], SV.rot(q, math.radians(p.get("ft_" + s, 0.0))))[1] for q in (SV.HEEL, SV.TOE))
    s = min(low, key=low.get)
    return s, J["ank_" + s][0] - roll(p.get("ft_" + s, 0.0))


# ---------------------------------------------------------------- a frame
def draw(pose, tag, tool=False, big=False):
    """-> (the frame at 128 px per metre, premultiplied float RGBA BOX_H x BOX_W; the socket [x, z, rad] or None; the
    pencil's stats; seconds; the drawing at 256 px per metre if `big`)."""
    held = "_tool" in pose
    f = SV.Fig(pose, "side", w=BOX_W + (176 if tool else 0), h=BOX_H + (96 if tool else 0), cx=CX, tag=tag,   # (run 1: the box cut the blade off; the tool is UNITY's sprite, shown here on a wider cel)
               grip=("grip", "grip" if pose.get("_two") else "open") if held else ("grip", "grip") if pose.get("_fist") else ("open", "open"))
    sock = None
    if held:
        e, w_ = f.pr(f.J["elb_n"], SV.LAT["arm"] * 1.06), f.pr(f.J["wr_n"], SV.LAT["arm"] * 1.06)
        ln = math.hypot(w_[0] - e[0], w_[1] - e[1]) or 1e-6
        g = (w_[0] + (w_[0] - e[0]) / ln * 0.045, w_[1] + (w_[1] - e[1]) / ln * 0.045)     # the fist's middle, on the forearm's line
        a = math.radians(pose["_tool"])
        sock = (round(g[0], 4), round(g[1], 4), round(a, 4))
        if tool:
            f.prop = (g, a)
    f.draw()
    img, st, sec = f.render()
    return CEL.down(img, SV.K), sock, st, sec, (CEL.down(img, SV.K // 2) if big else None)


def bbox(frames, pad=6):
    a = np.max([f[..., 3] for f in frames], axis=0) > 0.02
    ys, xs = np.where(a)
    return max(int(xs.min()) - pad, 0), max(int(ys.min()) - pad, 0), min(int(xs.max()) + 1 + pad, a.shape[1]), a.shape[0]


def preview(out):
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    t0 = time.time()
    SV.RHYTHM = True
    paper = np.array(review.PAPER, np.float32)
    Wd = 1920
    dd = os.path.join(os.path.dirname(out), "b231_frames")
    os.makedirs(dd, exist_ok=True)
    line = SV.rgb(SV.PAL["green"]) * 0.5 + SV.rgb(SV.PAL["brown"]) * 0.5

    def head(text, h=20):
        hd = np.tile(paper, (h, Wd, 1)).astype(np.float32)
        review._label(hd, text[:310], 6, 4, scale=1)
        return hd

    def cell(fr, box, k=1, label=None, g=None):
        x0, y0, x1, y1 = (v * k for v in box)
        c = np.tile(SV.STAGE, (y1 - y0, x1 - x0, 1)).astype(np.float32)
        gy = fr.shape[0] - (GROUND * k if g is None else g) - y0
        c[gy:gy + k] = line
        s = fr[y0:y1, x0:x1]
        c[...] = s[..., :3] + c * (1 - s[..., 3:4])
        if label:
            review._label(c, label, 3, 3, scale=1)
        return c

    def flow(cells, gap=6):
        """Cells laid left to right, wrapped at the sheet's width -> a list of rows."""
        rows_, cur, x = [], [], 0
        for c in cells:
            if cur and x + c.shape[1] > Wd:
                rows_.append(cur)
                cur, x = [], 0
            cur.append(c)
            x += c.shape[1] + gap
        rows_.append(cur)
        outp = []
        for cs in rows_:
            H = max(c.shape[0] for c in cs)
            r = np.tile(paper, (H, Wd, 1)).astype(np.float32)
            x = 0
            for c in cs:
                w = min(c.shape[1], Wd - x)
                r[H - c.shape[0]:, x:x + w] = c[:, :w]
                x += c.shape[1] + gap
            outp.append(r)
        return outp

    def strip_png(name, cells):
        H, Wt = max(c.shape[0] for c in cells), sum(c.shape[1] for c in cells) + 4 * (len(cells) - 1)
        s = np.tile(paper, (H, Wt, 1)).astype(np.float32)
        x = 0
        for c in cells:
            s[H - c.shape[0]:, x:x + c.shape[1]] = c
            x += c.shape[1] + 4
        pngio.write_png(os.path.join(dd, name), np.dstack([pngio.to_u8(np.clip(s, 0, 1)), np.full(s.shape[:2], 255, np.uint8)]))

    rows = [head("B-231 / U-199 (D-200, the owner's YES): THE SURVEYOR'S FRAME SETS, SLICE 1 - every frame its own drawing from a pose, the rhythm rules on, at the EXPORT size (128 px per metre = twice the game's). PREVIEW, nothing exported", 26)]
    lines, socks, clipped, secs, nfr, boxes = [], {}, [], [], 0, {}
    for sheet, name, poses, what in clips():
        if ONLY_CLIPS and name not in ONLY_CLIPS:
            continue
        big = name in ("walk", "run", "dig_down", "dig_fwd")
        got = [draw(p, f"{name}{i}", big=big) for i, p in enumerate(poses)]
        frames = [g[0] for g in got]
        secs += [g[3] for g in got]
        nfr += len(frames)
        for i, fr in enumerate(frames):
            a = fr[..., 3] > 0.02
            if a[:2].any() or a[:, :2].any() or a[:, -2:].any():
                clipped.append(f"{name} {i}")
        bx = bbox(frames)
        boxes[name] = bx
        ys, xs = np.where(np.max([f[..., 3] for f in frames], axis=0) > 0.02)
        ext = f"{(CX - xs.min()) / 128.0:.2f} m back, {(xs.max() - CX) / 128.0:.2f} m ahead, {(BOX_H - GROUND - ys.min()) / 128.0:.2f} m tall"
        rows.append(head(f"{sheet} / {name}: {len(frames)} frames - {what}. Reaches {ext}"))
        cells = [cell(fr, bx, label=str(i)) for i, fr in enumerate(frames)]
        strip_png(f"{name}.png", cells)
        if name in DIG:                                                          # the same five with the cel shovel laid on the socket
            tooled = [draw(p, f"{name}{i}", tool=True)[0] for i, p in enumerate(poses)]
            tb = bbox(tooled)
            tc = [cell(fr, tb, label=f"{i} + shovel") for i, fr in enumerate(tooled)]
            strip_png(f"{name}_with_shovel.png", tc)
            cells += tc
            nfr += 5
        rows += flow(cells)
        if held := [g[1] for g in got if g[1] is not None]:
            socks[name] = held
        if big:
            b2 = [cell(g[4], bx, k=2, label=str(i)) for i, g in enumerate(got)]
            strip_png(f"{name}_2x.png", b2)
            rows.append(head(f"{name} at TWICE the export size (the same drawings shrunk less: 256 px per metre)"))
            rows += flow(b2)
            f96 = [CEL.down(np.repeat(np.repeat(g[4], 3, 0), 3, 1), 8) for g in got]      # 256 x 3 / 8 = 96 px per metre
            f64 = [CEL.down(fr, 2) for fr in frames]
            c96 = [cell(fr, bbox(f96, 4), label=str(i), g=GROUND * 3 // 4) for i, fr in enumerate(f96)]
            c64 = [cell(fr, bbox(f64, 3), label=str(i), g=GROUND // 2) for i, fr in enumerate(f64)]
            strip_png(f"{name}_96.png", c96)
            strip_png(f"{name}_64.png", c64)
            rows.append(head(f"{name} AS THE GAME SHOWS IT: at 96 px per metre (the camera on the surface), then at 64 px per metre (underground)"))
            rows += flow(c96 + c64)
    x0 = min(b[0] for b in boxes.values())
    x1 = max(b[2] for b in boxes.values())
    y0 = min(b[1] for b in boxes.values())
    pages = {}
    for sheet, _n, ps, _w in clips():
        pages[sheet] = pages.get(sheet, 0) + len(ps)
    cols, rws = (2048 + 4) // (BOX_W + 4), (2048 + 4) // (BOX_H + 4)
    lines += [f"{nfr} drawings this run in {time.time() - t0:.0f} s ({min(secs):.1f}-{max(secs):.1f} s each)" + (f" (ONLY {', '.join(sorted(ONLY_CLIPS))})" if ONLY_CLIPS else "")
              + ". Slice 1 = 70 frames on side and side_air + 30 on side_dig, from 50 key poses (28 + 22); 29 of the 100 frames are in-betweens of POSES (each drawn fresh), none of pictures.",
              f"THE FRAME BOX: {BOX_W}x{BOX_H} px at 128 px per metre, pivot [0.5, {GROUND / BOX_H:.4f}]. What the drawings here use: x {x0}..{x1} of {BOX_W}, the top at row {y0} (6 px pad). Frames touching the box's edge: {', '.join(clipped) if clipped else 'none'}.",
              f"THE PAGES (a 2048x2048 sheet holds {cols} x {rws} = {cols * rws} frames of this box with a 4 px gutter): " + ", ".join(f"{k} {v} frames" for k, v in pages.items())
              + f". The stroll rides side_air: side with it would be {pages.get('side', 0) + 12}, over a sheet.",
              "SOCKETS (side_dig, per frame: the front glove's centre x, z in metres from the pivot, the tool's direction in rad):"]
    for cname in ("stroll", "run", "walk"):
        feet = [planted(p) for _s, n, ps, _w in clips() if n == cname for p in ps]
        steps = [feet[i][1] - feet[i + 1][1] for i in range(len(feet) - 1) if feet[i][0] == feet[i + 1][0] != "air"]
        want = SPEED.get(cname)
        hs = [SV.skeleton(p)["P"][1] for _s, n, ps, _w in clips() if n == cname for p in ps]
        lines.insert(3, f"   the pelvis's height per frame (m; standing {STAND:.3f}): " + " ".join(f"{z:.3f}" for z in hs) + f": a bob of {(max(hs) - min(hs)) * 100:.1f} cm")
        lines.insert(3, f"{cname.upper()}: the foot on the ground and its ground point's x (m) per frame (n = near, f = far): " + " ".join("air" if s == "air" else f"{s}{x:+.3f}" for s, x in feet)
                     + (f". While a foot is down it travels back {min(steps):.3f}-{max(steps):.3f} m a frame = {sum(steps) / len(steps) * 12:.2f} m/s at 12 fps"
                        + (f" (its ground_speed: {want:.2f} m/s)" if want else "") if steps else ""))
    for name, ss in socks.items():
        lines.append(f"  {name}: " + " ".join(f"[{s[0]:.3f}, {s[1]:.3f}, {s[2]:.3f}]" for s in ss))
    foot = np.tile(paper, (24 + 16 * len(lines), Wd, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:310], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-231 the surveyor's frame sets, slice 1 (lock-free, fakegp + numpy; not exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # <review png> [--only <clip> ...]
    if len(sys.argv) > 3 and sys.argv[2] == "--only":
        ONLY_CLIPS = set(sys.argv[3:])
    preview(sys.argv[1])
