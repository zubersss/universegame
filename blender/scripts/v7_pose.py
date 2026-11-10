"""Art v7, B-258 part 2 (the figure): B-250's POSE MATHS WITHOUT THE CEL MODULES. Pure python (math only), so it runs
inside Blender and in the bundled python alike. WRITTEN 11-10 17:1x AS SOURCE, UNRUN.

A COPY of build_surveyor_v6.py's add / mul / up / dn / rot / skeleton / ik and its constants (L_TH, L_SH, L_UA, L_FA,
ANKLE, HEEL, TOE, LAT) with RHYTHM on: the tables that STAND (keys, timings, ground speeds, sockets). The copy exists
because build_surveyor_v6 pulls in the fake grease-pencil chain, which must not be imported beside the real bpy.
check(poses) (numpy side only) compares this copy with build_surveyor_v6.skeleton for every pose given: run it before
any clip is keyed from here.

A pose is a dict of degrees (pelvis, chest, neck, head = forward lean; th_ / ua_ = thigh / upper arm swung forward;
kn_ / el_ = knee / elbow bent; ft_ = the foot's pitch; _n the near side, _f the far; twist, arc, len_*, lift).
skeleton(p) -> the joints in the figure's own plane, metres: x forward, z up, the lower sole on z = 0.
bones(p)    -> THE BONE MAP for a 3D rig: name -> (head, tail) in 3D (x forward, y to the FAR side, z up; the viewer
               at -y sees the near side), each bone running along one segment of the 2D skeleton, the near and far limbs
               set apart by LAT. A rig is posed by aiming each bone along its (tail - head); lengths are the rig's own.
"""
import math

L_TH, L_SH, L_UA, L_FA, ANKLE = 0.42, 0.41, 0.30, 0.27, 0.092
HEEL, TOE = (-0.078, -ANKLE), (0.20, -ANKLE)
LAT = {"leg": 0.085, "arm": 0.205}
HEAD_UP = 0.20                                    # the head bone's length here (a direction is all a rig takes from it)
HAND = 0.09
# two poses of build_surveyor_v6.POSES, for the probe frame (the clips come from build_surveyor_frames_v6's tables)
IDLE = {"twist": 6, "arc": 6, "pelvis": -3, "chest": 4, "neck": 6, "head": 2, "th_n": 1, "kn_n": 2, "th_f": 12, "kn_f": 26, "ft_f": -16,
        "ua_n": -7, "el_n": 14, "ua_f": 9, "el_f": 22}
WALK = {"twist": -22, "arc": 8, "pelvis": 2, "chest": 6, "neck": 4, "th_n": 27, "kn_n": 6, "ft_n": 17, "th_f": -20, "kn_f": 26, "ft_f": -32,
        "ua_n": -28, "el_n": 16, "ua_f": 26, "el_f": 34}


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(a, k):
    return (a[0] * k, a[1] * k)


def up(a):
    return (math.sin(a), math.cos(a))


def dn(a):
    return (math.sin(a), -math.cos(a))


def rot(p, a):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def skeleton(p):
    """build_surveyor_v6.skeleton with RHYTHM on, line for line."""
    g = lambda k, d=0.0: math.radians(p.get(k, d))  # noqa: E731
    tw, arc = g("twist"), g("arc")
    J = {"P": (0.0, 0.0)}
    pel, che = g("pelvis"), g("chest")
    J["W"] = mul(up(pel), 0.14)

    def along(t):
        if arc == 0.0:
            return add(J["W"], mul(up(che), t))
        pos = J["W"]
        for i in range(8):
            pos = add(pos, mul(up(che + arc * ((i + 0.5) * t / 8 / 0.385 - 0.5)), t / 8))
        return pos
    for k, t in (("R", 0.12), ("C", 0.24), ("SH", 0.34), ("N", 0.385)):
        J[k] = along(t)
    J["CR"] = mul(up(pel), -0.075)
    J["A"] = add(J["N"], mul(up(g("neck") + 0.6 * arc), 0.05))
    lows = []
    for s in ("n", "f"):
        sg = 1 if s == "n" else -1
        ll, la = p.get("len_leg_" + s, 1.0), p.get("len_arm_" + s, 1.0)
        hip = add(mul(up(pel), -0.05), (-sg * LAT["leg"] * math.sin(0.4 * tw), 0.0))
        th, kn, ft = g("th_" + s), g("kn_" + s), g("ft_" + s)
        knee = add(hip, mul(dn(th), L_TH * ll))
        ank = add(knee, mul(dn(th - kn), L_SH * ll))
        sh = add(along(0.305) if arc else add(J["SH"], mul(up(che), -0.035)), (sg * LAT["arm"] * math.sin(tw), 0.0))
        ua, el = g("ua_" + s), g("el_" + s)
        elb = add(sh, mul(dn(ua), L_UA * la))
        J.update({"hip_" + s: hip, "knee_" + s: knee, "ank_" + s: ank, "sh_" + s: sh, "elb_" + s: elb,
                  "wr_" + s: add(elb, mul(dn(ua + el), L_FA * la))})
        lows += [add(ank, rot(q, ft))[1] for q in (HEEL, TOE)]
    dz = -min(lows) + p.get("lift", 0.0)
    return {k: (v[0], v[1] + dz) for k, v in J.items()}


def ik(root, target, l1, l2):
    dx, dz = target[0] - root[0], target[1] - root[1]
    dist = min(math.hypot(dx, dz), l1 + l2 - 1e-4)
    a = math.atan2(dx, -dz)
    inner = math.acos(max(-1, min(1, (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist))))
    bend = math.pi - math.acos(max(-1, min(1, (l1 * l1 + l2 * l2 - dist * dist) / (2 * l1 * l2))))
    return math.degrees(a - inner), math.degrees(bend)


def bones(p):
    """-> {bone: ((x, y, z) head, (x, y, z) tail)}: the 3D bone map (see the module's head). The near limbs at -y."""
    g = lambda k, d=0.0: math.radians(p.get(k, d))  # noqa: E731
    J = skeleton(p)
    tw, arc = g("twist"), g("arc")
    P3 = lambda q, y=0.0: (q[0], y, q[1])  # noqa: E731
    out = {"spine_lo": (P3(J["P"]), P3(J["W"])), "spine_mid": (P3(J["W"]), P3(J["C"])), "spine_hi": (P3(J["C"]), P3(J["N"])),
           "neck": (P3(J["N"]), P3(J["A"])),
           "head": (P3(J["A"]), P3(add(J["A"], mul(up(g("neck") + g("head") + arc), HEAD_UP))))}
    for s, sg in (("n", -1.0), ("f", 1.0)):
        yl, ya = sg * LAT["leg"] * math.cos(0.4 * tw), sg * LAT["arm"] * math.cos(tw)
        ft = g("ft_" + s)
        toe = add(J["ank_" + s], rot(TOE, ft))
        hand = add(J["wr_" + s], mul(dn(g("ua_" + s) + g("el_" + s) + g("wr_" + s)), HAND))
        out.update({"thigh_" + s: (P3(J["hip_" + s], yl), P3(J["knee_" + s], yl)), "shin_" + s: (P3(J["knee_" + s], yl), P3(J["ank_" + s], yl)),
                    "foot_" + s: (P3(J["ank_" + s], yl), P3(toe, yl)),
                    "upper_arm_" + s: (P3(J["sh_" + s], ya), P3(J["elb_" + s], ya)), "forearm_" + s: (P3(J["elb_" + s], ya), P3(J["wr_" + s], ya)),
                    "hand_" + s: (P3(J["wr_" + s], ya), P3(hand, ya))})
    return out


def check(poses):
    """This copy against build_surveyor_v6.skeleton (numpy side only: it imports the cel modules). -> the largest
    difference in metres over every joint of every pose given."""
    import build_surveyor_v6 as S
    worst = 0.0
    for p in poses:
        a, b = skeleton(p), S.skeleton(p)
        for k in b:
            worst = max(worst, abs(a[k][0] - b[k][0]), abs(a[k][1] - b[k][1]))
    return worst


if __name__ == "__main__":
    import sys
    sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
    import build_surveyor_v6 as S
    print("v7_pose against build_surveyor_v6.skeleton, every pose of POSES: largest difference", check(list(S.POSES.values()) + [S.dig_pose()[0]]), "m")
