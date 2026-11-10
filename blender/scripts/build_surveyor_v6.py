"""B-231 (D-200, milestone C5): THE SURVEYOR, REDESIGNED for ART v6 - a MODEL SHEET; previews only, nothing exported.

The owner on the first v6 test (D-200): "this still looks like a 1930s cartoon, big circle head and eyes ... the same
style and the same level of detail, from the proportions to everything". docs/STYLE_V6.md 4a: a person stands five to
five and a half heads tall, lean, BUILT (a skull and a jaw; shoulders, a rib cage, hips; elbows, wrists, knees, ankles;
hands with a palm, a thumb and fingers; boots on a foot), with small features, hair as a designed mass, a thin sure line.
OUR OWN character and costume (no character of any film): a lean young field surveyor, mustard hair swept back, an
off-white jumpsuit with rolled sleeves, the teal MERIDIAN sash and the brass compass badge, a brown belt with a pouch,
brown boots, the red float pack with its plumb-bob antenna - and NO bubble helmet: on Earth no helmet at all (a close helmet with a visor
stays in the ship and is worn on airless worlds: one small drawing).

Figures now ship as DRAWN FRAMES, not a runtime cut-out rig (STYLE_V6 4a.7): this file is a parametric FIGURE - a
skeleton posed by angles, turned to a view (side, three-quarter front, front), and every frame drawn fresh from it as a
cel (cel_v6.py: pencil line, flat paint): forms overlap, the silhouette changes with the pose.

  python -I build_surveyor_v6.py <review png>     the lock-free model sheet
"""
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio, v3  # noqa: E402
import cel_v6 as CEL  # noqa: E402

G = CEL.G
S, P_, F, C, hose = CEL.S, CEL.P, CEL.F, CEL.C, CEL.hose
LINE = CEL.LINE
PX, K = 128, 4                                    # design px per metre (twice the game's size); the master is PX * K = 512
PAL = v3.PALETTES["earth"]
HEAD_M = 0.35                                     # the head, chin to crown (m)
HU = HEAD_M / 100.0                               # a head unit: heads are drawn on a 100-unit-tall grid (y down)
VIEWS = {"side": 0.0, "three-quarter": math.radians(42), "front": math.radians(90)}   # the turn toward the viewer


def rgb(h):
    return np.array(v3.hex_rgb(h), np.float32) / 255.0


def mixh(a, b, t):
    return v3.rgb_hex(tuple(int(round(v)) for v in (rgb(a) * (1 - t) + rgb(b) * t) * 255))


TONES = {
    "suit": mixh(PAL["offwhite"], PAL["brown"], 0.05), "stripe": PAL["teal"], "skin": mixh(PAL["offwhite"], PAL["red"], 0.24),
    "hair": mixh(PAL["mustard"], PAL["brown"], 0.12), "eye": PAL["offwhite"], "iris": mixh(PAL["teal"], v3.INK, 0.4), "pupil": v3.INK,
    "pack": PAL["red"], "brass": PAL["mustard"], "boot": PAL["brown"], "sole": mixh(PAL["brown"], v3.INK, 0.45),
    "belt": mixh(PAL["brown"], PAL["mustard"], 0.25), "steel": mixh(PAL["sky"], PAL["offwhite"], 0.3), "haft": PAL["teal"],
    "visor": mixh(PAL["sky"], PAL["teal"], 0.45),
}
FAR = 0.82                                        # the far limbs' paint: a step darker (the pencil the same)


def mats(gp):
    """Per tone: paint under a pencil line; _f the paint alone (a patch); @f the far side's darker paint; ln the pencil."""
    M = {"ln": CEL.mat(gp, "s6_ln"), "glass": CEL.mat(gp, "s6_glass", fill=PAL["sky"], line=False, alpha=0.3),
         "glint": CEL.mat(gp, "s6_glint", fill=PAL["offwhite"], line=False, alpha=0.6)}
    for k, h in TONES.items():
        far = v3.rgb_hex(tuple(int(round(v)) for v in rgb(h) * FAR * 255))
        M[k], M[k + "_f"] = CEL.mat(gp, f"s6_{k}", fill=h), CEL.mat(gp, f"s6_{k}_f", fill=h, line=False)
        M[k + "@f"], M[k + "_f@f"] = CEL.mat(gp, f"s6_{k}@f", fill=far), CEL.mat(gp, f"s6_{k}_f@f", fill=far, line=False)
    return M


# ---------------------------------------------------------------- the skeleton (metres; f forward, z up, in the body's own plane)
def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(a, k):
    return (a[0] * k, a[1] * k)


def up(a):
    """A spine segment's direction, leaning forward by a."""
    return (math.sin(a), math.cos(a))


def dn(a):
    """A hanging limb's direction, swung forward by a."""
    return (math.sin(a), -math.cos(a))


def rot(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


L_TH, L_SH, L_UA, L_FA, ANKLE = 0.42, 0.41, 0.30, 0.27, 0.092
HEEL, TOE = (-0.078, -ANKLE), (0.20, -ANKLE)       # the boot's sole, from the ankle (the foot's own axes)
LAT = {"leg": 0.085, "arm": 0.205}                 # how far to the side the hips' and shoulders' joints sit

# THE RHYTHM RULES (LEAD 11-10 08:4x). WRITTEN AS SOURCE AND NOT YET RUN: RHYTHM stays False until a sheet drawn with
# them has been looked at, so the accepted model sheet's drawings do not change by a pixel meanwhile.
#   twist    pose["twist"] (deg): the shoulders turned against the hips about the spine. In profile the near shoulder
#            comes forward by LAT sin(twist) and the far one goes back, the hips counter-turn by 0.4 of it, and the
#            chest is seen wider as it turns toward us (trunk_levels gives each cross-section its share of the turn).
#   bow      every limb's centre line bows a little (seg(bow=), BOW): the thigh forward, the shin back, the upper arm
#            back, the forearm forward - the long S of a leg and of an arm instead of two straight tubes.
#   folds    Fig.folds(): cloth gathers on the INSIDE of a bend, one more flick for every 45 degrees of it (behind a
#            knee; across the waist's front when the chest leans over the pelvis, across its back when it leans away).
#   stretch  pose["len_arm_n"], ["len_arm_f"], ["len_leg_n"], ["len_leg_f"] (1.0 = as built): a reaching limb
#            lengthens and thins (its volume kept). pose["squash"] (1.0 = none): the whole figure pressed toward the
#            ground and widened by the same volume rule (a landing), or drawn out (a jump's take-off, above 1.0).
# Poses may already carry these keys; with RHYTHM False they are ignored.
RHYTHM = False
BOW = {"thigh": 0.035, "shin": -0.03, "upper_arm": -0.02, "forearm": 0.025}    # the bow, as a share of the segment's length


def skeleton(p):
    """The joints of a pose (degrees): pelvis, chest, neck, head = forward lean; th_ / ua_ = thigh / upper arm swung
    forward; kn_ / el_ = knee / elbow bent; ft_ = the foot's pitch (toe up +); _n the near side, _f the far. The lower
    sole stands on the ground (plus lift). With RHYTHM: twist and len_* (above)."""
    g = lambda k, d=0.0: math.radians(p.get(k, d))  # noqa: E731
    tw = g("twist") if RHYTHM else 0.0
    J = {"P": (0.0, 0.0)}
    pel, che = g("pelvis"), g("chest")
    J["W"] = mul(up(pel), 0.14)
    for k, t in (("R", 0.12), ("C", 0.24), ("SH", 0.34), ("N", 0.385)):
        J[k] = add(J["W"], mul(up(che), t))
    J["CR"] = mul(up(pel), -0.075)
    J["A"] = add(J["N"], mul(up(g("neck")), 0.05))
    lows = []
    for s in ("n", "f"):
        sg = 1 if s == "n" else -1
        ll = p.get("len_leg_" + s, 1.0) if RHYTHM else 1.0                      # a stretched leg, a stretched arm
        la = p.get("len_arm_" + s, 1.0) if RHYTHM else 1.0
        hip = add(mul(up(pel), -0.05), (-sg * LAT["leg"] * math.sin(0.4 * tw), 0.0))    # the hips counter-turn
        th, kn, ft = g("th_" + s), g("kn_" + s), g("ft_" + s)
        knee = add(hip, mul(dn(th), L_TH * ll))
        ank = add(knee, mul(dn(th - kn), L_SH * ll))
        sh = add(add(J["SH"], mul(up(che), -0.035)), (sg * LAT["arm"] * math.sin(tw), 0.0))   # the near shoulder forward
        ua, el = g("ua_" + s), g("el_" + s)
        elb = add(sh, mul(dn(ua), L_UA * la))
        J.update({"hip_" + s: hip, "knee_" + s: knee, "ank_" + s: ank, "sh_" + s: sh, "elb_" + s: elb,
                  "wr_" + s: add(elb, mul(dn(ua + el), L_FA * la))})
        lows += [add(ank, rot(q, ft))[1] for q in (HEEL, TOE)]
    dz = -min(lows) + p.get("lift", 0.0)
    return {k: (v[0], v[1] + dz) for k, v in J.items()}


def ik(root, target, l1, l2):
    """Two bones from root to target (the joint bending as an elbow does: behind the line): (first bone's swing, the bend), deg."""
    dx, dz = target[0] - root[0], target[1] - root[1]
    dist = min(math.hypot(dx, dz), l1 + l2 - 1e-4)
    a = math.atan2(dx, -dz)                                                     # the line's swing from hanging
    inner = math.acos(max(-1, min(1, (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist))))
    bend = math.pi - math.acos(max(-1, min(1, (l1 * l1 + l2 * l2 - dist * dist) / (2 * l1 * l2))))
    return math.degrees(a - inner), math.degrees(bend)


# ---------------------------------------------------------------- shapes (metres, z up)
def seg(a, b, wa, wb, bulge=0.0, n=8, cap0=0.0, peak=0.5, bow=0.0):
    """A limb segment a -> b as four runs of points: one side a -> b, the cap round b, the other side b -> a, the cap
    round a (its radius less cap0). bulge: how much fuller than a straight taper, fullest at `peak` of its length (a
    thigh, a calf, a forearm: fuller above, tapering to the joint below). bow: its centre line bowed to one side by
    this share of its length at the middle (nothing at the joints, so they stay where the skeleton put them)."""
    e = math.log(0.5) / math.log(peak)
    (x0, z0), (x1, z1) = a, b
    ln = math.hypot(x1 - x0, z1 - z0) or 1e-6
    ux, uz = (x1 - x0) / ln, (z1 - z0) / ln
    nx, nz = -uz, ux
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        w = (wa * (1 - t) + wb * t) / 2 + bulge * math.sin(math.pi * t ** e)
        k = bow * ln * math.sin(math.pi * t)
        cx, cz = x0 + (x1 - x0) * t + nx * k, z0 + (z1 - z0) * t + nz * k
        left.append((cx + nx * w, cz + nz * w))
        right.append((cx - nx * w, cz - nz * w))
    an = math.atan2(nz, nx)
    capb = [(x1 + wb / 2 * math.cos(an - math.pi * k / 8), z1 + wb / 2 * math.sin(an - math.pi * k / 8)) for k in range(1, 8)]
    r0 = wa / 2 - cap0
    capa = [(x0 + r0 * math.cos(an + math.pi - math.pi * k / 8), z0 + r0 * math.sin(an + math.pi - math.pi * k / 8)) for k in range(1, 8)]
    return left, capb, right[::-1], capa


class Fig:
    """One drawing of the figure: a pose turned to a view, on a cel canvas (design px), drawn in metres."""
    def __init__(self, pose, view="side", w=300, h=350, cx=140, tag="fig", prop=None, grip=("open", "open")):
        self.p, self.view, self.psi = pose, view, VIEWS[view]
        self.cs, self.sn = math.cos(self.psi), math.sin(self.psi)
        self.c = CEL.Canvas(w, h, K, tag=tag)
        self.M = mats(self.c.gp)
        gy = h - 20
        self.d = G.Xf(self.c.dm, lambda pts: [(cx + x * PX, gy - z * PX) for x, z in pts])
        self.J = skeleton(pose)
        self.far = "@f" if view != "front" else ""
        self.prop, self.grip = prop, grip

    # ---- projection
    def pr(self, q, lat=0.0):
        """A point of the body's plane, `lat` to the near side of it -> the drawing (metres). Seen from the front the
        idle's weight shows as a sway: the hips over the standing leg, the shoulders coming back toward the middle."""
        z = q[1]
        sway = 0.0
        if self.view == "front":
            sway = -0.045 * (min(z, 0.95) / 0.95 if z <= 0.95 else max(0.25, 1 - 0.75 * (z - 0.95) / 0.5))
        sq = self.squash()
        return ((q[0] * self.cs - lat * self.sn + sway) / math.sqrt(sq), z * sq)

    def squash(self):
        """RHYTHM: how far the whole figure is pressed toward the ground (below 1) or drawn out (above 1)."""
        return float(self.p.get("squash", 1.0)) if RHYTHM else 1.0

    def bow(self, k):
        """RHYTHM: a limb segment's bow (seen less as the figure turns to face us: it bows in its own plane)."""
        return BOW[k] * self.cs if RHYTHM else 0.0

    def thin(self, k):
        """RHYTHM: a stretched limb is thinner by the square root of its stretch (its volume kept)."""
        return 1.0 / math.sqrt(self.p.get(k, 1.0)) if RHYTHM else 1.0

    def folds(self, j, b, u, bend):
        """RHYTHM: cloth gathered on the inside of a bend at joint j: b = the unit direction into the bend's inside, u =
        the lower segment's direction; one more flick for every 45 degrees of bend (at most three)."""
        if not RHYTHM or abs(bend) < 20:
            return
        for i in range(min(3, 1 + int(abs(bend) / 45))):
            o = 0.022 * i
            F(self.d, self.M, [(j[0] + b[0] * 0.05 + u[0] * (o - 0.012), j[1] + b[1] * 0.05 + u[1] * (o - 0.012)),
                               (j[0] + b[0] * 0.024 + u[0] * (o + 0.004), j[1] + b[1] * 0.024 + u[1] * (o + 0.004)),
                               (j[0] - b[0] * 0.004 + u[0] * (o + 0.016), j[1] - b[1] * 0.004 + u[1] * (o + 0.016))], 0.75, ends=(1.5, 3))

    def aw(self, w, dep, turn=0.0):
        """A form w wide (side to side) and dep deep (front to back): how wide it is seen from this view (turn: its own
        extra turn toward the viewer, radians - a twisted chest). A squashed figure is wider by the volume rule."""
        ps = self.psi + turn
        return 2 * math.hypot(w / 2 * math.sin(ps), dep / 2 * math.cos(ps)) / math.sqrt(self.squash())

    def tone(self, k, far):
        return self.M[k + (self.far if far else "")]

    # ---- limbs
    def lower(self, a, b, wa, wb, bulge, tone, far, bow=0.0):
        """A lower limb: its paint runs up under the joint and its line is open across it (no line crosses the bend);
        fullest a third of the way down (a calf, a forearm)."""
        o = seg(a, b, wa, wb, bulge, cap0=0.004, peak=0.3, bow=bow)
        P_(self.d, o[0] + o[1] + o[2] + o[3], self.tone(tone + "_f", far), under=False)
        S(self.d, o[0] + o[1] + o[2], self.M["ln"], LINE, ends=(3, 3))

    def leg(self, s):
        far = s == "f"
        lat = LAT["leg"] * (-1 if far else 1)
        hip, knee, ank = (self.pr(self.J[k + s], lat) for k in ("hip_", "knee_", "ank_"))
        d, M = self.d, self.M
        tn = self.thin("len_leg_" + s)
        th = seg(hip, knee, self.aw(0.165, 0.19) * tn, self.aw(0.112, 0.12) * tn, 0.013, peak=0.3, bow=self.bow("thigh"))   # a thigh: full above, lean at the knee
        S(d, th[0] + th[1] + th[2] + th[3], self.tone("suit", far), LINE, cyclic=True)
        self.lower(knee, ank, self.aw(0.108, 0.116) * tn, self.aw(0.08, 0.085) * tn, 0.016, "suit", far, self.bow("shin"))   # a calf
        kn = self.p.get("kn_" + s, 0.0)
        ux, uz = (ank[0] - knee[0]), (ank[1] - knee[1])
        ln = math.hypot(ux, uz) or 1e-6
        ux, uz = ux / ln, uz / ln
        bx, bz = uz, -ux                                                        # across the shin: toward the back of the knee
        if RHYTHM and self.view != "front":
            self.folds(knee, (bx, bz), (ux, uz), kn)                            # the cloth behind a bent knee, by its bend
        elif kn > 25 and self.view != "front":                                  # the cloth gathers behind a bent knee
            F(d, M, [(knee[0] + bx * 0.045, knee[1] + bz * 0.045 + 0.02), (knee[0] + bx * 0.02, knee[1] + bz * 0.02), (knee[0] + bx * 0.04 + ux * 0.03, knee[1] + bz * 0.04 + uz * 0.03)], 0.8)
        F(d, M, [(knee[0] + bx * 0.035 + ux * 0.05, knee[1] + bz * 0.035 + uz * 0.05), (knee[0] + ux * 0.062, knee[1] + uz * 0.062), (knee[0] - bx * 0.03 + ux * 0.05, knee[1] - bz * 0.03 + uz * 0.05)], 0.8)
        self.boot(ank, math.radians(self.p.get("ft_" + s, 0.0)), far)

    def boot(self, ank, pitch, far):
        """A boot built on a foot: a shaft over the ankle, a heel, an instep, a rounded toe, a sole with a heel block."""
        d, M = self.d, self.M
        if self.view == "front":                                                # the foot points at the viewer
            f = lambda pts: [(ank[0] + x, ank[1] + z) for x, z in pts]         # noqa: E731
            S(d, f([(-0.052, 0.15), (0.052, 0.15), (0.056, 0.0), (0.064, -0.05), (0.052, -0.088), (-0.052, -0.088), (-0.064, -0.05), (-0.056, 0.0)]), self.tone("boot", far), LINE, cyclic=True, rnd=0.012)
            F(d, M, f([(-0.045, -0.035), (0.0, -0.022), (0.045, -0.035)]), 0.8)                      # the toe cap
            F(d, M, f([(-0.05, 0.118), (0.0, 0.11), (0.05, 0.118)]), 0.8)
            return
        k = self.cs + 0.3 * self.sn                                             # the foot foreshortened as it turns
        f = lambda pts: [add(ank, rot((x * k, z), pitch)) for x, z in pts]      # noqa: E731
        S(d, f([(-0.05, 0.15), (0.05, 0.15), (0.052, 0.035), (0.10, 0.0), (0.165, -0.028), (0.198, -0.052), (0.196, -0.072),
                (-0.074, -0.072), (-0.08, -0.03), (-0.058, 0.035)]), self.tone("boot", far), LINE, cyclic=True, rnd=0.016)
        S(d, f([(-0.08, -0.068), (0.2, -0.068), (0.198, -0.092), (0.03, -0.092), (0.022, -0.082), (-0.02, -0.082), (-0.026, -0.092), (-0.08, -0.092)]),
          self.tone("sole", far), LINE * 0.8, cyclic=True, rnd=0.004, gap=0)
        F(d, M, f([(-0.05, 0.118), (0.0, 0.11), (0.05, 0.12)]), 0.8)                                 # the shaft's top band
        F(d, M, f([(0.052, 0.04), (0.035, 0.012), (0.045, -0.015)]), 0.7)                            # the instep's crease

    def hand(self, wr, ang, kind, far, flip=1):
        """A hand: a palm, four fingers, a thumb (open), or a fist round a shaft (grip)."""
        d, sk = self.d, self.tone("skin", far)
        f = lambda pts: [add(wr, rot((x * flip, z), ang)) for x, z in pts]      # noqa: E731
        thin = LINE * 0.42                                                      # (run 1: four fingers each in a full line were a
        if kind == "grip":                                                      # dark glove; a hand is one shape and a few thin lines)
            S(d, f([(-0.032, 0.005), (0.03, 0.005), (0.042, -0.035), (0.038, -0.082), (-0.028, -0.088), (-0.04, -0.045)]), sk, LINE * 0.7, cyclic=True, rnd=0.014, gap=0)
            for z in (-0.032, -0.052, -0.07):                                   # the fingers wrapped round the shaft: three creases
                S(d, f([(0.006, z + 0.004), (0.022, z), (0.037, z + 0.003)]), self.M["ln"], thin, ends=(1, 1.5))
            S(d, f(hose([(-0.022, -0.012), (-0.004, -0.04), (0.02, -0.048)], 0.024)), sk, LINE * 0.55, cyclic=True, gap=0)
            return
        S(d, f([(-0.03, 0.006), (0.03, 0.006), (0.036, -0.05), (0.034, -0.1), (0.036, -0.15), (0.03, -0.168), (0.02, -0.165), (0.016, -0.178),
                (0.004, -0.181), (-0.004, -0.17), (-0.012, -0.172), (-0.02, -0.158), (-0.03, -0.15), (-0.036, -0.13), (-0.034, -0.09), (-0.037, -0.045)]),
          sk, LINE * 0.7, cyclic=True, rnd=0.006, gap=0)                        # the palm and the four fingers: one shape
        for x0, x1 in ((0.019, 0.021), (0.004, 0.003), (-0.012, -0.015)):       # the fingers parted by three thin lines
            S(d, f([(x0, -0.095), ((x0 + x1) / 2, -0.13), (x1, -0.16)]), self.M["ln"], thin, ends=(1.5, 1))
        S(d, f(hose([(0.026, -0.018), (0.05, -0.052), (0.052, -0.09)], 0.024)), sk, LINE * 0.6, cyclic=True, gap=0)   # the thumb
        S(d, f([(-0.026, -0.088), (0.0, -0.094), (0.028, -0.088)]), self.M["ln"], thin, ends=(1.5, 1.5))             # the knuckles

    def arm(self, s):
        far = s == "f"
        lat = LAT["arm"] * (-1 if far else 1)
        sh, elb, wr = (self.pr(self.J[k + s], lat * (1.0 if k == "sh_" else 1.06)) for k in ("sh_", "elb_", "wr_"))
        d, M = self.d, self.M
        tn = self.thin("len_arm_" + s)
        ua = seg(sh, elb, self.aw(0.105, 0.115) * tn, self.aw(0.086, 0.092) * tn, 0.004, bow=self.bow("upper_arm"))
        S(d, ua[0] + ua[1] + ua[2] + ua[3], self.tone("suit", far), LINE, cyclic=True)
        self.lower(elb, wr, self.aw(0.076, 0.082) * tn, self.aw(0.054, 0.058) * tn, 0.012, "skin", far, self.bow("forearm"))   # a forearm: full below the elbow
        ang = math.atan2(wr[0] - elb[0], -(wr[1] - elb[1])) + math.radians(self.p.get("wr_" + s, 0.0))
        self.hand(wr, ang, self.grip[1 if far else 0], far, -1 if (self.view == "front" and far) else 1)
        ux, uz = elb[0] - sh[0], elb[1] - sh[1]                                 # the rolled sleeve: a thick roll over the elbow
        ln = math.hypot(ux, uz) or 1e-6
        a, b = (sh[0] + ux * 0.7, sh[1] + uz * 0.7), (sh[0] + ux * 0.97, sh[1] + uz * 0.97)
        w = self.aw(0.098, 0.104) * 1.12
        r = seg(a, b, w, w, 0.0, n=3)
        S(d, r[0] + r[1][2:5] + r[2] + r[3][2:5], self.tone("suit", far), LINE * 0.9, cyclic=True, rnd=0.012, gap=0)
        nx, nz = -uz / ln, ux / ln
        m = (sh[0] + ux * 0.84, sh[1] + uz * 0.84)
        F(d, M, [(m[0] + nx * w * 0.42, m[1] + nz * w * 0.42), (m[0] + ux / ln * 0.008, m[1] + uz / ln * 0.008), (m[0] - nx * w * 0.42, m[1] - nz * w * 0.42)], 0.7, ends=(1.5, 1.5))

    # ---- the trunk
    def trunk_levels(self):
        """The trunk's cross-sections from the crotch to the neck's base: (centre, the 'front' normal, half the width seen)."""
        J, out = self.J, []
        lv = (("CR", 0.20, 0.17, 0.0), ("P", 0.345, 0.235, -0.008), ("W", 0.275, 0.195, 0.0), ("R", 0.335, 0.235, 0.01),
              ("C", 0.40, 0.25, 0.016), ("SH", 0.40, 0.19, 0.0), ("N", 0.15, 0.13, 0.0))
        pts = [self.pr(J[k]) for k, *_r in lv]
        tw = math.radians(self.p.get("twist", 0.0)) if RHYTHM else 0.0
        share = {"CR": -0.4, "P": -0.4, "W": 0.15, "R": 0.4, "C": 0.75, "SH": 1.0, "N": 1.0}   # each section's share of the twist
        for i, (k, w, dep, sh) in enumerate(lv):
            a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
            ln = math.hypot(b[0] - a[0], b[1] - a[1]) or 1e-6
            n = ((b[1] - a[1]) / ln, -(b[0] - a[0]) / ln)                         # to the spine's right: the front, in profile
            c = (pts[i][0] + n[0] * sh * self.cs, pts[i][1] + n[1] * sh * self.cs)
            out.append((c, n, self.aw(w, dep, tw * share[k]) / 2))
        return out

    def T(self, u, v):
        """A point ON the trunk: u from -1 (the back / the viewer's left) to +1 (the front / right), v from 0 (crotch) to 1."""
        lv = self.lv
        x = max(0.0, min(0.9999, v)) * (len(lv) - 1)
        i = int(x)
        t = x - i
        (c0, n0, h0), (c1, n1, h1) = lv[i], lv[i + 1]
        c, n, h = (c0[0] * (1 - t) + c1[0] * t, c0[1] * (1 - t) + c1[1] * t), (n0[0] * (1 - t) + n1[0] * t, n0[1] * (1 - t) + n1[1] * t), h0 * (1 - t) + h1 * t
        return (c[0] + n[0] * h * u, c[1] + n[1] * h * u)

    def trunk(self):
        d, M, T = self.d, self.M, self.T
        self.lv = lv = self.trunk_levels()
        front = [(c[0] + n[0] * h, c[1] + n[1] * h) for c, n, h in lv]
        back = [(c[0] - n[0] * h, c[1] - n[1] * h) for c, n, h in lv]
        S(d, front + back[::-1], M["suit"], LINE, cyclic=True, keep="trunk", at=0.02)              # the jumpsuit: ribs, waist, hips
        P_(d, [T(0.45, 1.0), T(0.98, 1.0), T(-0.55, 0.3), T(-1.1, 0.3)], M["stripe_f"], sharp=True, clip="trunk")   # the MERIDIAN sash
        P_(d, [T(-1.2, 0.04), T(-0.56, 0.04), T(-0.5, 0.5), T(-0.62, 0.99), T(-1.2, 0.99)], M["suit_f"], sharp=True, clip="trunk", shade=True)
        us = [-1.06 + 2.12 * i / 6 for i in range(7)]                                               # the belt
        P_(d, [T(u, 0.385) for u in us] + [T(u, 0.325) for u in us[::-1]], M["belt_f"], sharp=True, clip="trunk")
        for v in (0.385, 0.325):
            F(d, M, [T(u, v) for u in (-0.98, 0.0, 0.98)], 0.7, ends=(1, 1))
        uz = self.cs * 0.9                                                      # the suit's front seam: where the front faces
        if abs(uz) < 0.86:
            F(d, M, [T(uz, 0.93), T(uz, 0.66), T(uz, 0.42)], 0.7)
            P_(d, [T(uz - 0.1, 0.395), T(uz + 0.1, 0.395), T(uz + 0.1, 0.315), T(uz - 0.1, 0.315)], M["brass_f"], rnd=0.004, clip="trunk")
        else:                                                                   # in profile: the pouch on the near hip
            S(d, [T(-0.1, 0.33), T(0.42, 0.33), T(0.4, 0.2), T(-0.08, 0.2)], M["belt"], LINE * 0.8, cyclic=True, rnd=0.008, gap=0)
            F(d, M, [T(-0.08, 0.275), T(0.16, 0.262), T(0.4, 0.275)], 0.7)
        b = T({"side": 0.3, "three-quarter": uz - 0.5, "front": 0.42}[self.view], 0.72)   # the compass badge and its rose
        S(d, [(b[0] + 0.028 * math.cos(t), b[1] + 0.028 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 16, endpoint=False)], M["brass"], LINE * 0.6, cyclic=True, gap=0)
        P_(d, [(b[0], b[1] + 0.02), (b[0] + 0.005, b[1] + 0.005), (b[0] + 0.016, b[1]), (b[0] + 0.005, b[1] - 0.005), (b[0], b[1] - 0.02),
               (b[0] - 0.005, b[1] - 0.005), (b[0] - 0.016, b[1]), (b[0] - 0.005, b[1] + 0.005)], M["stripe_f"], sharp=True)
        if RHYTHM:                                                              # the waist folds on the side the chest leans to
            lean = self.p.get("chest", 0.0) - self.p.get("pelvis", 0.0)
            sgn = 1 if lean > 0 else -1
            for i in range(min(3, int(abs(lean) / 15))):
                F(d, M, [T(sgn * 0.98, 0.42 + 0.035 * i), T(sgn * 0.62, 0.40 + 0.035 * i), T(sgn * 0.3, 0.415 + 0.035 * i)], 0.7)
        F(d, M, [T(-0.2, 0.43), T(0.1, 0.455), T(0.45, 0.43)], 0.7)                                  # a crease over the belt
        if self.view != "side":                                                 # the pack's straps over the shoulders
            for u in (-0.55, 0.55):
                P_(d, [T(u - 0.09, 1.0), T(u + 0.09, 1.0), T(u * 1.25 + 0.09, 0.62), T(u * 1.25 - 0.09, 0.62)], M["belt_f"], sharp=True, clip="trunk")
        else:
            P_(d, [T(-0.3, 1.0), T(0.02, 1.0), T(0.5, 0.64), T(0.2, 0.62)], M["belt_f"], sharp=True, clip="trunk")
        if self.p.get("th_n", 0) > 25 and self.view != "front":                   # the cloth pulls at a raised thigh
            F(d, M, [T(0.1, 0.13), T(0.45, 0.1), T(0.8, 0.12)], 0.7)

    def neck(self):
        n, a = self.pr(self.J["N"]), self.pr(self.J["A"])
        o = seg((n[0], n[1] - 0.02), (a[0], a[1] + 0.03), self.aw(0.12, 0.125), self.aw(0.105, 0.115), n=3)
        P_(self.d, o[0] + o[2], self.M["skin_f"], rnd=0.004, under=False)
        S(self.d, o[0], self.M["ln"], LINE * 0.8, ends=(1, 1))
        S(self.d, o[2], self.M["ln"], LINE * 0.8, ends=(1, 1))
        ux, uz = a[0] - n[0], a[1] - n[1]                                       # the collar: a low stand-up ring round the neck's
        ln = math.hypot(ux, uz) or 1e-6                                         # base (run 1's thin closed sliver read as a beard)
        ux, uz = ux / ln, uz / ln
        w = self.aw(0.15, 0.15)
        c = seg((n[0] - ux * 0.03, n[1] - uz * 0.03), (n[0] + ux * 0.028, n[1] + uz * 0.028), w * 1.1, w * 0.92, n=2)
        S(self.d, c[0] + c[2], self.M["suit"], LINE * 0.85, cyclic=True, rnd=0.006, gap=0)

    def pack(self):
        """The float pack on the back and its plumb-bob antenna."""
        if self.view == "front":
            return
        d, M, J = self.d, self.M, self.J
        ch = math.radians(self.p.get("chest", 0.0))
        u, n = up(ch), (math.cos(ch), -math.sin(ch))
        c = add(J["C"], mul(n, -(0.125 + 0.07)))
        hw = self.aw(0.30, 0.17) / 2
        q = lambda a, b: self.pr(add(c, add(mul(n, a / max(self.cs, 0.35) * 1.0), mul(u, b))))   # noqa: E731
        k = hw
        box = [q(-k, -0.19), q(k, -0.19), q(k, 0.17), q(k * 0.6, 0.2), q(-k * 0.7, 0.2), q(-k, 0.15)]
        # (LEAD 08:2x: no helmet on the pack on Earth - hung there it read as a pale ball behind the hip; it stays in the
        # ship. The bust shows it worn.)
        top = q(-k * 0.75, 0.19)                                                # the antenna: a thin straight whip at the pack's
        aa = ch + math.radians(self.p.get("ant", 0.0))                          # back corner and the brass bob ("ant" bends it back:
        au, an_ = (math.sin(aa) * self.cs, math.cos(aa)), (math.cos(aa), -math.sin(aa) * self.cs)   # a crouch lays it along the pack).
        t = (top[0] + au[0] * 0.15, top[1] + au[1] * 0.15)                      # (Run 2's zigzag stalk beside the head read as a braid.)
        S(d, [top, (top[0] + au[0] * 0.08 - an_[0] * 0.004, top[1] + au[1] * 0.08 - an_[1] * 0.004), t], M["ln"], LINE * 0.6, ends=(0.5, 0.5))
        S(d, [(t[0] + au[0] * 0.062 + an_[0] * 0.03, t[1] + au[1] * 0.062 + an_[1] * 0.03), (t[0] + au[0] * 0.062 - an_[0] * 0.03, t[1] + au[1] * 0.062 - an_[1] * 0.03),
              (t[0] + au[0] * 0.004, t[1] + au[1] * 0.004)], M["brass"], LINE * 0.8, cyclic=True, rnd=0.004, gap=0)
        S(d, box, M["pack"], LINE, cyclic=True, rnd=0.03, keep="pack")
        P_(d, [q(-k * 1.2, -0.2), q(k * 1.2, -0.2), q(k * 1.2, -0.07), q(-k * 1.2, -0.07)], M["pack_f"], sharp=True, clip="pack", shade=True)
        for b in (0.1, -0.1):
            P_(d, [q(-k * 1.2, b + 0.018), q(k * 1.2, b + 0.018), q(k * 1.2, b - 0.018), q(-k * 1.2, b - 0.018)], M["belt_f"], sharp=True, clip="pack")

    # ---- the head: a skull and a jaw, small features, hair as a designed mass (head units: 100 = chin to crown, y down)
    def head(self):
        d, M = self.d, self.M
        a = self.pr(self.J["A"])
        tilt = -math.radians(self.p.get("head", 0.0)) * self.cs
        pv = {"side": (36, 84), "three-quarter": (-2, 88), "front": (0, 90)}[self.view]
        h = G.Xf(d, lambda pts: [add(a, rot(((x - pv[0]) * HU, (pv[1] - y) * HU), tilt)) for x, y in pts])
        W = LINE * 0.42                                                         # the face in a finer line than the body (run 2: at 8x the features were blobs)

        def eye(cx, cy, w, look=0.25):
            """An eye w wide: a white shape with no ring, a heavier upper lid, a flat iris, a pupil, one highlight; a brow."""
            k, name = w / 13.0, f"eye{cx}"
            P_(h, [(cx - 6.5 * k, cy + 0.6), (cx - 3 * k, cy - 3.1), (cx + 2.5 * k, cy - 3.5), (cx + 6.5 * k, cy - 0.4), (cx + 3 * k, cy + 2.8), (cx - 3 * k, cy + 3)], M["eye_f"], rnd=1.6, keep=name)
            P_(h, C(cx + look * 6 * k, cy - 0.3, 3.3 * min(k * 1.15, 1), 12, ry=3.5), M["iris_f"], clip=name)
            P_(h, C(cx + look * 6 * k + 0.2, cy - 0.3, 1.6, 10), M["pupil_f"], clip=name)
            P_(h, C(cx + look * 6 * k + 1.3, cy - 1.6, 0.75, 8), M["eye_f"])
            S(h, [(cx - 7.2 * k, cy + 1.0), (cx - 3.2 * k, cy - 3.3), (cx + 2.6 * k, cy - 3.8), (cx + 7.4 * k, cy - 0.2)], M["ln"], W * 1.25, ends=(1.5, 2))
            S(h, [(cx - 8 * k, cy - 9.5), (cx - 0.5 * k, cy - 12.2), (cx + 8.5 * k, cy - 10.2)], M["ln"], W * 1.7, ends=(1.5, 3.5))
        if self.view == "side":
            S(h, [(40, 82), (56, 92), (72, 98), (80, 97), (85, 91), (82.5, 85), (85, 81), (83, 78), (87, 74), (84.5, 69), (95, 64),
                  (86.5, 50), (88, 41), (86, 28), (80, 14), (58, 3), (32, 5), (11, 22), (5, 44), (10, 64), (22, 78)], M["skin"], LINE * 0.72, cyclic=True, at=0.02)
            # the hair: one swept mass, a forelock, tufts at the crown and the nape (run 2's hairline sat on the brow: raised)
            S(h, [(84, 19), (91, 9), (80, 6), (71, -1), (60, 4), (49, -3), (38, 3), (25, 2), (15, 7), (8, 19), (2, 41), (6, 62), (13, 59), (12, 72),
                  (22, 69), (30, 57), (33, 44), (43, 40), (47, 54), (53, 36), (63, 24), (74, 21)], M["hair"], LINE * 0.75, cyclic=True, rnd=2.4)
            for pts in ([(28, 12), (40, 9), (52, 12)], [(14, 30), (20, 44), (17, 56)], [(58, 12), (70, 11), (81, 13)]):
                S(h, pts, M["ln"], W, ends=(2, 3))
            S(h, C(41, 55, 6.5, 14, ry=10.5), M["skin"], W * 1.3, cyclic=True, gap=0)                    # the ear
            S(h, [(43, 50), (39.5, 55), (42.5, 60)], M["ln"], W, ends=(1, 1.5))
            eye(74, 46, 12.5)
            S(h, [(88.5, 66.8), (90.8, 65.4)], M["ln"], W, ends=(0.6, 0.6))                              # the nostril
            S(h, [(84.5, 77.8), (78, 78.6), (73.5, 76.6)], M["ln"], W * 1.1, ends=(1, 2.5))              # the mouth
            S(h, [(60, 86), (66, 90), (73, 92)], M["ln"], W, ends=(2, 2))                                # the jaw's line
        elif self.view == "front":
            half = [(0, 100), (12, 98.5), (24, 89), (31, 75), (35, 58), (37, 42), (35, 26), (26, 10), (0, 3)]
            for sx in (-1, 1):
                S(h, C(sx * 38.5, 55, 4.5, 12, ry=10), M["skin"], W * 1.2, cyclic=True, gap=0)           # the ears
            S(h, half + [(-x, y) for x, y in half[-2:0:-1]], M["skin"], LINE * 0.72, cyclic=True, at=0.02)
            S(h, [(-38, 45), (-39.5, 24), (-34, 8), (-24, -3), (-14, 2), (-4, -6), (8, 0), (20, -5), (28, 4), (36, 12), (39.5, 28), (38, 45),
                  (33, 33), (28, 24), (12, 29), (-8, 22), (-26, 29), (-33, 35)], M["hair"], LINE * 0.75, cyclic=True, rnd=2.4)   # a fringe swept to one side
            for pts in ([(-20, 8), (-10, 12), (2, 9)], [(12, 8), (22, 12), (30, 18)]):
                S(h, pts, M["ln"], W, ends=(2, 3))
            eye(-17, 50, 13, 0.0)
            eye(17, 50, 13, 0.0)
            S(h, [(3, 57), (5.5, 66), (2, 70), (-3.5, 69)], M["ln"], W, ends=(2.5, 1.5))                 # the nose
            S(h, [(-10, 80), (0, 83), (10, 80)], M["ln"], W * 1.1, ends=(2, 2))
            S(h, [(-3.5, 87.5), (3.5, 87.5)], M["ln"], W * 0.8, ends=(1, 1))
        else:
            S(h, [(18, 100), (30, 96.5), (38, 87), (42.5, 73), (44, 61), (41, 51), (43.5, 42), (41.5, 28), (34, 12), (8, 3), (-18, 7),
                  (-36, 22), (-42, 44), (-36, 64), (-24, 82), (-6, 94.5)], M["skin"], LINE * 0.72, cyclic=True, at=0.02)
            S(h, [(-40, 47), (-44.5, 26), (-38, 8), (-28, -3), (-16, 2), (-4, -6), (10, 0), (22, -4), (32, 6), (40, 16), (43.5, 30), (38, 27),
                  (30, 31), (22, 23), (10, 30), (0, 22), (-12, 28), (-22, 30), (-25, 45), (-32, 40)], M["hair"], LINE * 0.75, cyclic=True, rnd=2.4)
            for pts in ([(-24, 8), (-12, 12), (0, 9)], [(12, 8), (24, 12), (34, 18)]):
                S(h, pts, M["ln"], W, ends=(2, 3))
            S(h, C(-31, 56, 6, 14, ry=10.5), M["skin"], W * 1.2, cyclic=True, gap=0)                     # the near ear
            S(h, [(-29, 51), (-32.5, 56), (-29.5, 61)], M["ln"], W, ends=(1, 1.5))
            eye(3, 50, 13, 0.2)
            eye(31, 49.5, 9, 0.2)
            S(h, [(24.5, 50), (29.5, 60), (33.5, 65.5), (27, 69.6)], M["ln"], W, ends=(2.5, 1.5))        # the nose
            S(h, [(8, 80), (18, 83.5), (27.5, 80)], M["ln"], W * 1.1, ends=(2, 2))
            S(h, [(14, 88), (21, 88)], M["ln"], W * 0.8, ends=(1, 1))

    def tool(self):
        """The cel shovel through the hands (prop = (the grip's point, the tool's angle))."""
        if self.prop is None:
            return
        g, ang = self.prop
        f = G.Xf(self.d, lambda pts: [add(g, rot((x, z), ang)) for x, z in pts])
        M = self.M
        # the far hand holds the grip 0.4 m behind the near one; the blade's tip is 1.33 m from the grip (B-226's shovel)
        S(f, hose([(-0.42, 0.0), (0.62, 0.0)], 0.036), M["haft"], LINE * 0.8, cyclic=True, gap=0)
        S(f, [(-0.5, -0.07), (-0.42, -0.07), (-0.42, 0.07), (-0.5, 0.07)], M["brass"], LINE * 0.8, cyclic=True, rnd=0.02, gap=0)
        S(f, [(0.6, -0.115), (0.66, -0.13), (0.75, -0.125), (0.85, -0.09), (0.93, 0.0), (0.85, 0.09), (0.75, 0.125), (0.66, 0.13), (0.6, 0.115)], M["steel"], LINE, cyclic=True, rnd=0.03)
        P_(f, [(0.56, -0.03), (0.64, -0.03), (0.64, 0.03), (0.56, 0.03)], M["brass_f"], rnd=0.008, under=False)

    def draw(self):
        if self.view == "front":
            order = ("leg f", "leg n", "trunk", "neck", "head", "arm f", "arm n")
        else:
            order = ("arm f", "leg f", "pack", "leg n", "trunk", "neck", "head", "tool", "arm n")
        for step in order:
            name, *arg = step.split()
            getattr(self, name)(*arg)
        return self

    def render(self):
        """-> (premultiplied float RGBA at the master size, the pencil's stats, seconds)."""
        t0 = time.time()
        paint, line, st = self.c.render()
        img = CEL.premul(CEL.compose(paint, CEL.dry(line, 7)))
        return img, st, time.time() - t0


# ---------------------------------------------------------------- the poses (degrees; twist and len_* are RHYTHM keys, ignored while it is off)
POSES = {
    # the weight on the near leg, the far knee eased and its heel off the ground; the spine a little curved
    "idle": {"twist": 4, "pelvis": -3, "chest": 4, "neck": 6, "head": 2, "th_n": 1, "kn_n": 2, "th_f": 12, "kn_f": 26, "ft_f": -16,
             "ua_n": -7, "el_n": 14, "ua_f": 9, "el_f": 22},
    # a walk's contact: the near heel down ahead, the far foot pushing off its toes, the arms counter-swung
    "walk": {"twist": -14, "pelvis": 2, "chest": 6, "neck": 4, "th_n": 27, "kn_n": 6, "ft_n": 17, "th_f": -20, "kn_f": 26, "ft_f": -32,
             "ua_n": -28, "el_n": 16, "ua_f": 26, "el_f": 34},
    # a deep crouch under the 1 m line: folded at hips and knees, the back level, the head ducked, a hand to the ground
    # (the antenna laid back along the pack: "ant")
    "crouch": {"pelvis": 64, "chest": 82, "neck": 64, "head": 50, "th_n": 118, "kn_n": 152, "ft_n": 0, "th_f": 100, "kn_f": 154, "ft_f": -26,
               "ua_n": 40, "el_n": 62, "ua_f": 30, "el_f": 70, "ant": -150},
    # a jump's apex: the knees tucked unevenly, one arm thrown up and forward, the other back
    "jump": {"twist": 10, "len_arm_n": 1.06, "pelvis": 4, "chest": 8, "neck": -4, "th_n": 66, "kn_n": 98, "ft_n": -22, "th_f": 14, "kn_f": 72, "ft_f": -36,
             "ua_n": 128, "el_n": 26, "ua_f": -34, "el_f": 22, "lift": 0.32},
    # the dig's contact: a lunge, the weight over the front knee, both hands on the shovel (set by reach, below)
    "dig": {"twist": 12, "pelvis": 16, "chest": 30, "neck": 16, "head": 14, "th_n": 50, "kn_n": 62, "th_f": -30, "kn_f": 22, "ft_f": -34},
}
DIG_AIM = -47.0                                   # the shovel's angle at the dig's contact (deg from level)


def dig_pose():
    """The dig's contact with both hands ON the shaft: the near hand low, the far hand at the grip; the arms found by reach."""
    p = dict(POSES["dig"])
    J = skeleton(p)
    a = math.radians(DIG_AIM)
    near = add(J["sh_n"], (0.33, -0.36))                                         # the near hand: low and ahead of the knee
    grip = add(near, mul((math.cos(a), math.sin(a)), -0.40))                      # the far hand, 0.4 m up the shaft at the grip
    p["ua_n"], p["el_n"] = ik(J["sh_n"], near, L_UA, L_FA)
    p["ua_f"], p["el_f"] = ik(J["sh_f"], grip, L_UA, L_FA)
    p["wr_n"], p["wr_f"] = 20, 30
    J = skeleton(p)
    return p, (J["wr_n"], a)


def figure(name, view="side", **kw):
    if name == "dig":
        p, (wr, a) = dig_pose()
        f = Fig(p, view, tag=name + view, grip=("grip", "grip"), **kw)
        e, w_ = f.pr(f.J["elb_n"], LAT["arm"] * 1.06), f.pr(f.J["wr_n"], LAT["arm"] * 1.06)
        ln = math.hypot(w_[0] - e[0], w_[1] - e[1]) or 1e-6
        f.prop = ((w_[0] + (w_[0] - e[0]) / ln * 0.045, w_[1] + (w_[1] - e[1]) / ln * 0.045), a)   # the shaft through the near fist
        return f.draw()
    return Fig(POSES[name], view, tag=name + view, **kw).draw()


def helmet_bust():
    """The close helmet for airless worlds, worn: a shell round the skull, a visor over the face, a neck ring (one small drawing)."""
    f = Fig(dict(POSES["idle"], neck=2, head=0), "side", w=150, h=150, cx=64, tag="helmet")
    f.d = G.Xf(f.c.dm, lambda pts: [(64 + x * PX, 150 - 24 - (z - 1.38) * PX) for x, z in pts])   # the bust: from the chest up
    f.lv = f.trunk_levels()
    f.trunk()
    f.neck()
    f.head()
    a = f.pr(f.J["A"])
    h = G.Xf(f.d, lambda pts: [add(a, ((x - 36) * HU, (84 - y) * HU)) for x, y in pts])
    M = f.M
    P_(h, [(62, 24), (92, 26), (100, 62), (94, 90), (64, 92), (58, 58)], M["glass"], rnd=6)
    P_(h, CEL.crescent(80, 58, 22, math.radians(-150), math.radians(-95), 5), M["glint"], sharp=True)
    S(h, [(92, 20), (70, -6), (30, -8), (2, 14), (-6, 46), (2, 78), (20, 98), (56, 106), (88, 104), (98, 92), (64, 92), (58, 58), (62, 24)],
      M["steel"], LINE, cyclic=True, rnd=5)
    S(h, [(18, 100), (92, 104), (94, 114), (16, 110)], M["brass"], LINE * 0.9, cyclic=True, rnd=3, gap=0)
    S(h, [(92, 26), (100, 62), (94, 90)], M["ln"], LINE * 0.8, ends=(2, 2))
    return f


# ---------------------------------------------------------------- the model sheet
STAGE = np.array([0.665, 0.725, 0.571], np.float32)       # a flat sage ground: a cel is judged against a mid-value stage


def preview(out):
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    t0 = time.time()
    paper = np.array(review.PAPER, np.float32)
    Wd = 1920
    dd = os.path.join(os.path.dirname(out), "b231_v6")
    os.makedirs(dd, exist_ok=True)

    def head(text, h=20):
        hd = np.tile(paper, (h, Wd, 1)).astype(np.float32)
        review._label(hd, text, 6, 4, scale=1)
        return hd

    def over(dst, img, x, y):
        h, w = img.shape[:2]
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
        if x1 > x0 and y1 > y0:
            s = img[y0 - y:y1 - y, x0 - x:x1 - x]
            dst[y0:y1, x0:x1] = s[..., :3] + dst[y0:y1, x0:x1] * (1 - s[..., 3:4])
    stats, times, imgs = [], [], {}
    for name, view, kw in (("idle", "side", dict(w=200, cx=96, h=290)), ("idle", "three-quarter", dict(w=200, cx=104, h=290)), ("idle", "front", dict(w=200, cx=100, h=290)),
                           ("walk", "side", {}), ("crouch", "side", {}), ("jump", "side", {}), ("dig", "side", dict(w=340, cx=130))):
        img, st, sec = figure(name, view, **kw).render()
        imgs[(name, view)] = img
        stats.append(st)
        times.append(sec)
    hb, _st, _sec = helmet_bust().render()
    for view, cx in (("side", 96), ("three-quarter", 104), ("front", 100)):        # the three heads at the master size, as files
        c = imgs[("idle", view)][18 * K:94 * K, (cx - 38) * K:(cx + 46) * K]
        u8 = np.clip(np.rint(np.dstack([c[..., :3] + STAGE * (1 - c[..., 3:4]), np.ones(c.shape[:2], np.float32)]) * 255), 0, 255).astype(np.uint8)
        pngio.write_png(os.path.join(dd, f"head_{view}_8x.png"), u8)
    rows = [np.tile(paper, (30, Wd, 1)).astype(np.float32)]
    review._label(rows[0], "B-231 (D-200): THE SURVEYOR REDESIGNED - a model sheet. Our own character, drawn as a built figure: every drawing here is made fresh from a posed skeleton (no cut-out parts). PREVIEW, nothing exported", 6, 8)
    rows.append(head("THE TURN at 2x the game's size: side | three-quarter front | front ||| the side view at 4x ||| the close helmet for airless worlds, worn (at 4x); on Earth it stays in the ship"))
    r = np.tile(STAGE, (600, Wd, 1)).astype(np.float32)
    x = 10
    for view in ("side", "three-quarter", "front"):
        im = CEL.down(imgs[("idle", view)], 4)
        over(r, im, x, 600 - im.shape[0] - 10)
        x += im.shape[1] + 10
    im = CEL.down(imgs[("idle", "side")], 2)
    over(r, im, x + 20, 600 - im.shape[0] - 10)
    x += im.shape[1] + 50
    over(r, CEL.down(hb, 2), x, 600 - 300 - 10)
    rows.append(r)
    rows.append(head("FIVE POSES at 2x the game's size, each its own drawing: idle (the weight on one leg) | a walk's contact | a deep crouch under the 1 m line | a jump's apex | the dig's contact, both hands on the cel shovel"))
    RH = 370
    r = np.tile(STAGE, (RH, Wd, 1)).astype(np.float32)
    gy = RH - 10 - 20                                                           # the cells' ground row at 2x
    r[gy:gy + 2] = rgb(PAL["green"]) * 0.5 + rgb(PAL["brown"]) * 0.5
    x, tops = 10, {}
    for name in ("idle", "walk", "crouch", "jump", "dig"):
        img = imgs[(name, "side")]
        rows_on = np.where(img[..., 3].max(axis=1) > 0.02)[0]
        tops[name] = (img.shape[0] - 20 * K - rows_on[0]) / float(PX * K)
        im = CEL.down(img, 4)
        over(r, im, x, RH - im.shape[0] - 10)
        if name == "crouch":
            yc = gy - PX
            r[yc - 2:yc, x:x + im.shape[1]] = rgb(PAL["red"])
            review._label(r, f"1 m; the crouch stands {tops[name]:.2f} m", x + 6, yc - 14, scale=1)
        x += im.shape[1] + 16
    rows.append(r)
    rows.append(head("AT THE GAME'S SIZE (shrunk 8x from the master): the same seven drawings"))
    r = np.tile(STAGE, (190, Wd, 1)).astype(np.float32)
    x = 10
    for key in (("idle", "side"), ("idle", "three-quarter"), ("idle", "front"), ("walk", "side"), ("crouch", "side"), ("jump", "side"), ("dig", "side")):
        im = CEL.down(imgs[key], 8)
        over(r, im, x, 190 - im.shape[0] - 6)
        x += im.shape[1] + 8
    rows.append(r)
    idle2 = CEL.down(imgs[("idle", "side")], 4)
    u8 = np.clip(np.rint(np.dstack([idle2[..., :3] / np.maximum(idle2[..., 3:4], 1e-5), idle2[..., 3:4]]) * 255), 0, 255).astype(np.uint8)
    nb = pngio.write_png(os.path.join(dd, "frame_idle_2x.png"), u8)
    ys, xs = np.where(u8[..., 3] > 0)
    cw, chh = int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)
    mean_w, min_w, max_w, n_lines = CEL.line_stats(stats[0])
    eye_share = 12.5 / 74.0
    lines = [f"HEIGHT: {tops['idle']:.2f} m standing = {tops['idle'] / HEAD_M:.2f} heads (the head {HEAD_M:.2f} m, chin to crown). THE EYE: {eye_share * 100:.0f} % of the head's width (the limit: a fifth). The crouch stands {tops['crouch']:.2f} m.",
             f"THE LINE at the game's zoom on the side idle: mean {mean_w:.2f} px ({min_w:.2f}-{max_w:.2f}); {n_lines} pencil strokes in that one drawing (the dig: {CEL.line_stats(stats[-1])[3]}).",
             f"ONE FRAME COSTS: {min(times):.1f}-{max(times):.1f} s to render at the master size (512 px per metre), plus the pose's numbers. At twice the game's size the idle is {cw}x{chh} px, {nb / 1024:.1f} KB as a PNG.",
             f"A 150-FRAME SET at twice the game's size: about {150 * nb / 1024 / 1024:.1f} MB of PNG, {150 * cw * chh * 4 / 1024 / 1024:.0f} MB of texture uncompressed ({150 * cw * chh / (2048 * 2048):.1f} sheets of 2048x2048), about {150 * (min(times) + max(times)) / 2 / 60:.0f} min to render.",
             f"this run: {time.time() - t0:.0f} s"]
    foot = np.tile(paper, (24 + 16 * len(lines), Wd, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-231 surveyor model sheet, v6 redesign (lock-free, fakegp + numpy; not exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    preview(sys.argv[1])
