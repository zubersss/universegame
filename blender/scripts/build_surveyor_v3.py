"""Builds blender/sources/characters/surveyor_v3.blend: the v4 surveyor (B-111), Grease Pencil.

Design (Bible §9.3, original, §9.8): a rubber-hose astronaut about 2.0 m tall (~128 px at 1x)
with a big round fishbowl helmet. Inside it is a round off-white face with pie-cut eyes, a soft
red bulb nose, cheeks and a mustard cowlick. Signature pieces that make it ours:
  - a surveyor's PLUMB BOB on a springy antenna on top of the helmet (drags and overshoots:
    the free secondary motion of every clip),
  - a teal MERIDIAN STRIPE running over the off-white suit, with a compass badge,
  - a soft-red float pack on the back, tied to the helmet by a rubber air hose.
White gloves with mustard cuffs, big brown boots, hose arms and legs. Earth palette only.

draw_surveyor(d, M, pose) draws one drawing; pose keys (all optional):
  view 'side' | 'front' | 'tq', expr 'happy' | 'surprised' | 'determined' | 'dizzy',
  bob, sz (squash on the visual root), lean, legs [(dx, lift), (dx, lift)] (back, front),
  arms [ang_back, ang_front] (rad, + = forward), look (pupil offset), blink 0..1,
  bob_tip (plumb-bob lag in m, + = backward).
Step 1 (design sheet) uses the views and expressions; step 2 (the side sheet) animates poses.
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gp_draw as G  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "characters", "surveyor_v3.blend")
P = G.PALETTES["earth"]
O, I = G.OUTER, G.INNER


def materials(gp):
    return {
        "suit": G.mat(gp, "suit", fill=P["offwhite"]),
        "suit_sh": G.mat(gp, "suit_shadow", fill=G.shadow_of(P["offwhite"]), ink=False),
        "stripe": G.mat(gp, "stripe_teal", fill=P["teal"]),
        "mustard": G.mat(gp, "mustard", fill=P["mustard"]),
        "red": G.mat(gp, "red", fill=P["red"]),
        "red_sh": G.mat(gp, "red_shadow", fill=G.shadow_of(P["red"]), ink=False),
        "red_flat": G.mat(gp, "cheek", fill=G.shadow_of(P["offwhite"]), ink=False),
        "teal": G.mat(gp, "hose_teal", fill=P["teal"]),
        "boot": G.mat(gp, "boot", fill=P["brown"]),
        "boot_sh": G.mat(gp, "boot_shadow", fill=G.shadow_of(P["brown"]), ink=False),
        "glove": G.mat(gp, "glove", fill=P["offwhite"]),
        "face": G.mat(gp, "face", fill=P["offwhite"]),
        "eye": G.mat(gp, "eye_white", fill=P["offwhite"]),
        "pupil": G.mat(gp, "pupil", fill=G.INK, ink=False),
        "ink": G.mat(gp, "ink_line", fill=None, ink=True),
        "glint": G.mat(gp, "glint", fill=None, ink=True, ink_hex=P["offwhite"]),
        "star": G.mat(gp, "star", fill=P["mustard"]),
    }


def star(cx, cz, r, rot=0.0, seed=0):
    pts = []
    for k in range(10):
        a = rot + math.pi / 2 + math.pi * k / 5
        rr = r * (1.0 if k % 2 == 0 else 0.45) * (1 + 0.05 * math.sin(seed + k * 1.7))
        pts.append((cx + rr * math.cos(a), cz + rr * math.sin(a)))
    return pts


def spiral(cx, cz, r, turns=2.2, n=40):
    return [(cx + r * (k / n) * math.cos(6.283 * turns * k / n), cz + r * (k / n) * math.sin(6.283 * turns * k / n))
            for k in range(n + 1)]


def draw_surveyor(d, M, pose=None, seed=0):
    p = dict(view="side", expr="happy", bob=0.0, sz=1.0, lean=0.0, legs=((0.0, 0.0), (0.0, 0.0)),
             arms=(0.0, 0.0), look=None, blink=0.0, bob_tip=0.0, pack_swing=0.0, pack_dz=0.0, hose_lag=0.0, puff=0.0, star_rot=0.6, speed=0.0)
    p.update(pose or {})
    view, expr = p["view"], p["expr"]
    face_dir = {"side": 1.0, "tq": 0.55, "front": 0.0}[view]
    sz = p["sz"]
    sx = 1.0 / math.sqrt(sz)

    def X(pts, pivot_z=0.55):                       # the visual root: squash about the hips, bob, lean
        return [((x * sx) + p["lean"] * (z - pivot_z), pivot_z + (z - pivot_z) * sz + p["bob"]) for x, z in pts]

    def X1(x, z):
        return X([(x, z)])[0]

    # ---- back limbs + float pack (behind the body)
    hip_z = 0.60
    def leg(k, dx, lift, back):
        hx = {"side": -0.05 + 0.10 * k, "tq": -0.12 + 0.22 * k, "front": -0.15 + 0.30 * k}[view]
        hip = X1(hx, hip_z)
        foot = (hip[0] + dx + (0.0 if view == "side" else (-0.04 if k == 0 else 0.04)), 0.10 + lift)
        knee = ((hip[0] + foot[0]) / 2 + (0.07 if view != "front" else (0.05 if k else -0.05)),
                (hip[1] + foot[1]) / 2)
        G.stroke(d, G.hose_outline(G.bezier(hip, knee, foot, n=10), 0.13), M["suit"], O, cyclic=True)
        toe = 1.0 if view != "front" else (0.55 if k else -0.55)
        bx = foot[0] + 0.08 * toe
        boot = G.lumpy_ellipse(bx, 0.0 + 0.10 * 1.04 + O * 1.25 - 0.10 + lift + 0.075, 0.13 + 0.06 * abs(toe), 0.10,
                               n=28, lump=0.04, seed=seed + 11 + k)
        G.stroke(d, boot, M["boot"], O, cyclic=True)
        sole = [(x, z) for x, z in boot if z < min(b[1] for b in boot) + 0.04]
        if len(sole) > 3:
            G.stroke(d, sole, M["boot_sh"], 0.0, cyclic=True)
            G.stroke(d, boot, M["ink"], O, cyclic=True)

    def arm(k, ang):
        side = (-1 if k == 0 else 1)
        if view == "side":
            sh = X1(0.0 + 0.04 * side, 1.00)
        else:
            sh = X1(side * 0.30, 1.00)
        reach = 0.42
        if view == "side":
            hand = (sh[0] + reach * math.sin(ang), sh[1] - reach * math.cos(ang))
            mid = ((sh[0] + hand[0]) / 2 - 0.06, (sh[1] + hand[1]) / 2 + 0.02)
        else:
            out = side * (0.16 + 0.10 * abs(math.sin(ang)))
            hand = (sh[0] + out, sh[1] - reach * math.cos(ang * 0.6))
            mid = ((sh[0] + hand[0]) / 2 + side * 0.07, (sh[1] + hand[1]) / 2 + 0.03)
        G.stroke(d, G.hose_outline(G.bezier(sh, mid, hand, n=10), 0.11), M["suit"], O, cyclic=True)
        cuff = G.lumpy_ellipse(mid[0] * 0.15 + hand[0] * 0.85, mid[1] * 0.15 + hand[1] * 0.85 + 0.01, 0.085, 0.06,
                               n=20, lump=0.05, seed=seed + 41 + k)
        G.stroke(d, cuff, M["mustard"], O, cyclic=True)
        g = G.lumpy_ellipse(hand[0], hand[1] - 0.04, 0.115, 0.105, n=24, lump=0.06, seed=seed + 21 + k)
        G.stroke(d, g, M["glove"], O, cyclic=True)
        fx = hand[0] + (0.03 if view == "side" else side * 0.02)
        G.stroke(d, G.bezier((fx - 0.05, hand[1] - 0.05), (fx, hand[1] - 0.07), (fx + 0.04, hand[1] - 0.03), n=6),
                 M["ink"], I)

    legs, arms = p["legs"], p["arms"]
    leg(0, legs[0][0], legs[0][1], True)
    if view == "side":
        arm(0, arms[0])
    # float pack: on the back (side: behind at -x; tq: peeks out left; front: hidden but straps)
    if view in ("side", "tq"):
        px = -0.36 if view == "side" else -0.33
        strap = X1(px + 0.02, 1.14)
        sw, pdz = p["pack_swing"], p["pack_dz"]

        def PK(pts):                                # the pack hangs from its strap: swing + bounce
            cs, sn = math.cos(sw), math.sin(sw)
            return [(strap[0] + (x - strap[0]) * cs - (z - strap[1]) * sn, strap[1] + (x - strap[0]) * sn + (z - strap[1]) * cs + pdz)
                    for x, z in pts]
        pack = PK(X(G.lumpy_ellipse(px, 0.92, 0.17, 0.25, n=32, lump=0.04, seed=seed + 51)))
        G.stroke(d, pack, M["red"], O, cyclic=True)
        lo = [q for q in pack if q[1] < PK([X1(px, 0.80)])[0][1]]
        if len(lo) > 3:
            G.stroke(d, lo, M["red_sh"], 0.0, cyclic=True)
            G.stroke(d, pack, M["ink"], O, cyclic=True)
        dial = PK([X1(px - 0.02, 1.00)])[0]
        G.stroke(d, G.lumpy_ellipse(dial[0], dial[1], 0.055, 0.055, n=18, seed=seed + 52), M["mustard"], I, cyclic=True)
        # rubber air hose from the pack top to the helmet back
        a, b = PK([strap])[0], X1(-0.28 if view == "side" else -0.22, 1.30)
        c = ((a[0] + b[0]) / 2 - 0.12 - p["hose_lag"], (a[1] + b[1]) / 2 + 0.02 - 0.5 * abs(p["hose_lag"]))
        G.stroke(d, G.hose_outline(G.bezier(a, c, b, n=10), 0.06), M["teal"], O, cyclic=True)
    leg(1, legs[1][0], legs[1][1], False)

    # ---- torso: a round bean with the meridian stripe, belt and badge
    body = X(G.lumpy_ellipse(0.0, 0.86, 0.33 if view != "side" else 0.29, 0.34, n=52, lump=0.03, seed=seed + 1))
    G.stroke(d, body, M["suit"], 0.0, cyclic=True)
    n = len(body)
    shadow_side = [body[i] for i in range(n) if math.cos(6.283 * i / n) < -0.35 or math.sin(6.283 * i / n) < -0.7]
    if len(shadow_side) > 3:
        cxz = X1(0.0, 0.86)
        inner = [(cxz[0] + (x - cxz[0]) * 0.78 + 0.03, cxz[1] + (z - cxz[1]) * 0.80 + 0.03) for x, z in shadow_side][::-1]
        G.stroke(d, shadow_side + inner, M["suit_sh"], 0.0, cyclic=True)
    so = {"side": 0.13, "tq": 0.10, "front": 0.0}[view]
    sw = {"side": 0.06, "tq": 0.09, "front": 0.10}[view]
    stripe = [(so - sw + 0.02 * math.sin(t * 3.0), 0.55 + 0.62 * t) for t in [k / 11 for k in range(12)]]
    stripe += [(so + sw + 0.02 * math.sin(t * 3.0), 0.55 + 0.62 * t) for t in [k / 11 for k in range(11, -1, -1)]]
    stripe = [(x * (1 - 0.35 * ((z - 0.86) / 0.34) ** 2 if view == "side" else 1), z) for x, z in stripe]
    stripe = [q for q in stripe if abs(q[1] - 0.86) < 0.31]
    G.stroke(d, X(stripe), M["stripe"], I, cyclic=True)
    belt = X(G.bowed_line((-0.30 if view != "side" else -0.27, 0.66), (0.30 if view != "side" else 0.27, 0.66), bow=-0.03))
    G.stroke(d, belt, M["ink"], I)
    if view != "side":
        bx = X1(so + 0.0, 0.93)
        G.stroke(d, G.lumpy_ellipse(bx[0], bx[1], 0.075, 0.075, n=24, seed=seed + 61), M["mustard"], I, cyclic=True)
        G.stroke(d, [(bx[0], bx[1] + 0.05), (bx[0] + 0.02, bx[1]), (bx[0], bx[1] - 0.05), (bx[0] - 0.02, bx[1])],
                 M["red"], I, cyclic=True)
    G.stroke(d, body, M["ink"], O, cyclic=True)

    # front arm (side), both arms (front / tq)
    if view == "side":
        arm(1, arms[1])
    else:
        arm(0, arms[0])
        arm(1, arms[1])

    # ---- collar + helmet + face
    collar = X(G.lumpy_ellipse(0.0, 1.13, 0.27, 0.07, n=32, lump=0.03, seed=seed + 71))
    G.stroke(d, collar, M["mustard"], O, cyclic=True)
    hc = X1(0.0, 1.52)
    hr = 0.42
    # head inside the glass
    fx = hc[0] + 0.10 * face_dir
    fz = hc[1] - 0.04
    face = G.lumpy_ellipse(fx, fz, 0.29 - 0.03 * face_dir, 0.30, n=40, lump=0.03, seed=seed + 81)
    G.stroke(d, face, M["face"], I, cyclic=True)
    tuft = G.bezier((fx - 0.10, fz + 0.27), (fx - 0.02 - 0.06 * face_dir, fz + 0.42), (fx + 0.08, fz + 0.30), n=10)
    tuft += G.bezier((fx + 0.08, fz + 0.30), (fx + 0.02, fz + 0.33), (fx - 0.02, fz + 0.28), n=6)[1:]
    G.stroke(d, tuft, M["mustard"], I, cyclic=True)
    # cheeks
    for k, cxo in enumerate((-0.17, 0.17)):
        if view == "side" and k == 0:
            continue
        cxx = fx + cxo * (1 - 0.45 * face_dir) + 0.05 * face_dir
        G.stroke(d, G.lumpy_ellipse(cxx, fz - 0.10, 0.05, 0.035, n=16, seed=seed + 91 + k), M["red_flat"], 0.0, cyclic=True)
    # eyes
    eye_x = [(-0.09, 0.09), (0.0, 0.16), (0.07, 0.19)][["front", "tq", "side"].index(view)]
    eyes = eye_x if view != "side" else (0.07, 0.19)
    look = p["look"] if p["look"] is not None else (0.5 * face_dir, 0.05)
    for k, ex in enumerate(eyes):
        exx = fx + ex - 0.02 * face_dir
        ez = fz + 0.06
        if expr == "dizzy":
            G.stroke(d, spiral(exx, ez, 0.075, turns=1.5), M["ink"], I)
            continue
        er = (0.055, 0.085)
        lid = p["blink"]
        if expr == "surprised":
            er = (0.08, 0.125)
            ez += 0.03
        if expr == "determined":
            lid = max(lid, 0.45)
        G.pie_eye(d, exx, ez, er[0], er[1], M["pupil"], M["eye"], look=look, seed=seed + 31 + k, closed=lid,
                  m_lid=M["ink"])
        if expr == "determined":         # a firm brow line
            G.stroke(d, G.bowed_line((exx - 0.06, ez + 0.06 + (0.02 if k == 0 else 0)),
                                     (exx + 0.06, ez + 0.06 + (0.0 if k == 0 else 0.02)), bow=0.1, n=6), M["ink"], I)
    # nose: a soft red bulb at the front of the face
    nx = fx + 0.21 * face_dir + (0.0 if face_dir else 0.0)
    G.stroke(d, G.lumpy_ellipse(nx + (0.04 if view == "side" else 0), fz - 0.02, 0.055, 0.045, n=18, seed=seed + 95),
             M["red"], I, cyclic=True)
    # mouth
    mx = fx + 0.12 * face_dir
    if expr == "happy":
        G.stroke(d, G.bezier((mx - 0.10 + 0.04 * face_dir, fz - 0.12), (mx + 0.02, fz - 0.21), (mx + 0.10, fz - 0.11), n=12),
                 M["ink"], I)
    elif expr == "surprised":
        G.stroke(d, G.lumpy_ellipse(mx + 0.01, fz - 0.15, 0.035, 0.05, n=18, seed=seed + 97), M["red"], I, cyclic=True)
    elif expr == "determined":
        G.stroke(d, G.bowed_line((mx - 0.07, fz - 0.15), (mx + 0.08, fz - 0.13), bow=-0.06, n=8), M["ink"], I)
    else:                                # dizzy: a wobbly mouth
        G.stroke(d, [(mx - 0.09 + 0.18 * t, fz - 0.15 + 0.015 * math.sin(t * 15)) for t in [k / 14 for k in range(15)]],
                 M["ink"], I)
    # the glass: ink ring (the silhouette), two glints
    ring = G.lumpy_ellipse(hc[0], hc[1], hr, hr * 0.98, n=64, lump=0.015, seed=seed + 5)
    G.stroke(d, ring, M["ink"], O, cyclic=True)
    gl = [(hc[0] + hr * 0.78 * math.cos(a), hc[1] + hr * 0.78 * math.sin(a)) for a in [2.0 + 0.09 * k for k in range(9)]]
    G.stroke(d, gl, M["glint"], I)
    G.stroke(d, [(hc[0] + hr * 0.78 * math.cos(2.95), hc[1] + hr * 0.78 * math.sin(2.95))], M["glint"], I)
    # antenna + plumb bob (drags behind by bob_tip)
    base = (hc[0] - 0.05 * face_dir, hc[1] + hr * 0.97)
    tip = (base[0] - p["bob_tip"] - 0.02, base[1] + 0.17)
    G.stroke(d, G.bezier(base, (base[0] + 0.04, base[1] + 0.09), tip, n=10), M["ink"], I)
    G.stroke(d, G.lumpy_ellipse(tip[0], tip[1] + 0.01, 0.10, 0.06, n=16, lump=0.03, seed=seed + 7)[:9] + [(tip[0] - 0.06, tip[1] - 0.05), (tip[0], tip[1] - 0.17), (tip[0] + 0.06, tip[1] - 0.05)], M["teal"], O, cyclic=True)
    if expr == "dizzy":
        for k in range(3):
            a = p["star_rot"] + 2.1 * k
            G.stroke(d, star(hc[0] + 0.52 * math.cos(a), hc[1] + 0.30 + 0.12 * math.sin(a), 0.08, rot=a, seed=k),
                     M["star"], I, cyclic=True)
    # dash speed lines: three bowed ink streaks trailing the body
    if p["speed"] > 0:
        for k, z in enumerate((0.62, 0.98, 1.42)):
            x0 = -0.48 - 0.06 * k
            G.stroke(d, G.bowed_line((x0, z + p["bob"]), (x0 - 0.30 * p["speed"] - 0.06 * k, z + p["bob"] + 0.02), bow=0.04, n=8),
                     M["ink"], I)
    # landing smoke puffs: round cartoon clouds rolling out from both boots
    if p["puff"] > 0:
        t = p["puff"]
        for k, side in enumerate((-1, 1)):
            for j in range(2):
                r = (0.07 + 0.05 * j) * (0.6 + 0.8 * t)
                cx = side * (0.30 + 0.28 * t + 0.14 * j)
                G.stroke(d, G.lumpy_ellipse(cx, r * 0.9 + O * 1.25 + 0.02 * t, r, r * 0.85, n=20, lump=0.06,
                                            seed=seed + 101 + 2 * k + j), M["glove"], O, cyclic=True)


DESIGN = [("side", "happy"), ("front", "happy"), ("tq", "happy"),
          ("front", "surprised"), ("front", "determined"), ("front", "dizzy"), ("side", "surprised")]
DESIGN_OUT = os.path.join(os.path.dirname(HERE), "sources", "characters", "surveyor_v3_design.blend")

# characters/surveyor/side clips (contract §11.2 caps; LEAD cycle 233 counts)
CLIPS = [("idle", 10), ("walk", 12), ("jump", 8), ("land", 8), ("look_camera", 12),
         ("bump", 10), ("conk_out", 12), ("run", 12), ("fall", 8), ("dash", 6)]          # B-116 appended
TAU = 2 * math.pi


def idle_pose(i):
    ph = TAU * i / 10
    return dict(sz=1.0 + 0.045 * math.cos(ph), bob=0.012 * math.cos(ph),
                arms=(0.10 * math.sin(ph), -0.10 * math.sin(ph)),
                pack_swing=0.05 * math.sin(ph - 1.2), pack_dz=-0.02 * math.cos(ph - 1.2),
                hose_lag=0.03 * math.sin(ph - 2.0), bob_tip=0.035 * math.sin(ph - 1.6),
                blink={7: 0.6, 8: 1.0}.get(i, 0.0))


def walk_pose(i):
    ph = TAU * i / 12
    legs = tuple((0.26 * math.sin(ph + math.pi * k), max(0.0, 0.15 * math.cos(ph + math.pi * k))) for k in range(2))
    return dict(legs=legs, bob=0.07 * abs(math.cos(ph)) - 0.02, sz=1.0 + 0.055 * math.cos(2 * ph), lean=0.08,
                arms=(0.75 * math.sin(ph), -0.75 * math.sin(ph)),
                pack_swing=0.12 * math.sin(2 * ph - 1.0) + 0.06, pack_dz=0.03 * math.cos(2 * ph - 1.0),
                hose_lag=0.05 * math.sin(2 * ph - 1.8), bob_tip=0.06 + 0.04 * math.sin(2 * ph - 1.4),
                look=(0.6, 0.0))


# jump: crouch, launch stretch, rise, tuck at the apex (the climb itself is physics)
JUMP = [dict(sz=0.78, bob=-0.06, legs=((-0.06, 0.0), (0.06, 0.0)), arms=(-0.6, -0.4), pack_swing=0.10, pack_dz=0.04, hose_lag=0.04, bob_tip=0.02),
        dict(sz=1.28, bob=0.04, legs=((-0.08, 0.10), (0.04, 0.05)), arms=(2.6, 2.4), pack_swing=-0.20, pack_dz=-0.08, hose_lag=-0.06, bob_tip=-0.06),
        dict(sz=1.20, bob=0.05, legs=((-0.06, 0.16), (0.06, 0.12)), arms=(2.5, 2.3), pack_swing=-0.16, pack_dz=-0.07, hose_lag=-0.07, bob_tip=-0.08),
        dict(sz=1.10, bob=0.06, legs=((-0.04, 0.22), (0.08, 0.20)), arms=(2.2, 2.0), pack_swing=-0.08, pack_dz=-0.04, hose_lag=-0.05, bob_tip=-0.05),
        dict(sz=1.02, bob=0.06, legs=((-0.10, 0.26), (0.12, 0.24)), arms=(1.6, 1.4), pack_swing=0.02, pack_dz=0.00, hose_lag=-0.01, bob_tip=0.0),
        dict(sz=0.98, bob=0.06, legs=((-0.12, 0.28), (0.14, 0.26)), arms=(1.3, 1.1), pack_swing=0.06, pack_dz=0.02, hose_lag=0.02, bob_tip=0.03),
        dict(sz=1.00, bob=0.06, legs=((-0.12, 0.28), (0.14, 0.26)), arms=(1.2, 1.0), pack_swing=0.04, pack_dz=0.01, hose_lag=0.03, bob_tip=0.02),
        dict(sz=1.00, bob=0.06, legs=((-0.11, 0.27), (0.13, 0.25)), arms=(1.25, 1.05), pack_swing=0.02, pack_dz=0.0, hose_lag=0.02, bob_tip=0.01)]

# land: contact squash with a smoke puff, overshoot, settle; pack keeps falling, then catches up
LAND = [dict(sz=0.70, bob=-0.08, legs=((-0.16, 0.0), (0.16, 0.0)), arms=(1.2, 1.0), pack_swing=0.05, pack_dz=-0.10, hose_lag=-0.08, bob_tip=-0.06, puff=0.15),
        dict(sz=0.76, bob=-0.07, legs=((-0.15, 0.0), (0.15, 0.0)), arms=(0.9, 0.7), pack_swing=0.14, pack_dz=-0.06, hose_lag=-0.05, bob_tip=0.06, puff=0.40),
        dict(sz=0.88, bob=-0.04, legs=((-0.12, 0.0), (0.12, 0.0)), arms=(0.5, 0.3), pack_swing=0.18, pack_dz=0.0, hose_lag=0.02, bob_tip=0.08, puff=0.65),
        dict(sz=1.06, bob=0.01, legs=((-0.08, 0.0), (0.08, 0.0)), arms=(0.2, 0.0), pack_swing=0.08, pack_dz=0.04, hose_lag=0.05, bob_tip=0.04, puff=0.85),
        dict(sz=0.98, bob=0.0, legs=((-0.06, 0.0), (0.06, 0.0)), arms=(0.05, -0.05), pack_swing=-0.03, pack_dz=0.01, hose_lag=0.02, bob_tip=-0.02, puff=1.0),
        dict(sz=1.01, bob=0.0, arms=(0.0, 0.0), pack_swing=0.02, pack_dz=0.0, hose_lag=-0.01, bob_tip=0.01),
        dict(sz=1.0, bob=0.0, pack_swing=-0.01, hose_lag=0.01),
        dict(sz=1.0, bob=0.0)]


def look_pose(i):
    """Stop, turn to the camera, a pleased blink and a little wave of the plumb bob, turn back."""
    view = ["side", "tq", "front", "front", "front", "front", "front", "front", "front", "front", "tq", "side"][i]
    sz = [1.0, 1.04, 1.06, 1.0, 1.0, 1.02, 1.0, 1.0, 1.0, 1.0, 1.03, 1.0][i]
    return dict(view=view, sz=sz, blink={6: 0.6, 7: 1.0}.get(i, 0.0), look=(0.0, 0.1) if view == "front" else None,
                bob_tip=[0.0, 0.05, 0.08, -0.04, 0.03, -0.02, 0.01, 0.0, 0.0, 0.0, -0.05, -0.02][i],
                pack_swing=[0.0, 0.06, 0.08, -0.03, 0.02, 0.0, 0.0, 0.0, 0.0, 0.0, -0.06, -0.02][i])


# ---- B-116: bump, conk_out, run, fall, dash (same sheet key; contract caps bump <= 10, conk_out <= 12)
BUMP = [dict(expr="surprised", sz=0.82, lean=-0.26, bob=-0.03, legs=((-0.14, 0.0), (-0.04, 0.06)), arms=(2.2, 1.8), pack_swing=0.25, pack_dz=0.05, hose_lag=0.08, bob_tip=-0.16),
        dict(expr="surprised", sz=1.10, lean=-0.30, legs=((-0.18, 0.0), (-0.10, 0.0)), arms=(2.0, 1.6), pack_swing=0.18, pack_dz=0.02, hose_lag=0.06, bob_tip=-0.12),
        dict(expr="dizzy", sz=0.92, lean=-0.14, star_rot=0.0, arms=(0.9, 0.6), pack_swing=0.05, hose_lag=0.03, bob_tip=0.08),
        dict(expr="dizzy", sz=1.03, lean=0.06, star_rot=0.7, arms=(0.4, 0.2), pack_swing=-0.08, hose_lag=-0.03, bob_tip=0.12),
        dict(expr="dizzy", sz=0.98, lean=-0.06, star_rot=1.4, arms=(0.2, 0.4), pack_swing=0.08, hose_lag=0.04, bob_tip=-0.08),
        dict(expr="dizzy", sz=1.02, lean=0.05, star_rot=2.1, arms=(0.3, 0.1), pack_swing=-0.06, hose_lag=-0.03, bob_tip=0.06),
        dict(expr="dizzy", sz=0.99, lean=-0.03, star_rot=2.8, arms=(0.1, 0.2), pack_swing=0.04, hose_lag=0.02, bob_tip=-0.04),
        dict(expr="dizzy", sz=1.0, lean=0.02, star_rot=3.5, pack_swing=-0.02, bob_tip=0.03),
        dict(sz=1.03, blink=1.0, pack_swing=0.02, bob_tip=-0.02),
        dict(sz=1.0)]

CONK = [dict(expr="dizzy", star_rot=0.0, lean=0.08, sz=1.02, arms=(0.3, -0.2), bob_tip=-0.06, pack_swing=-0.05),
        dict(expr="dizzy", star_rot=0.7, lean=-0.10, sz=0.98, arms=(-0.2, 0.4), bob_tip=0.08, pack_swing=0.08),
        dict(expr="dizzy", star_rot=1.4, lean=0.13, sz=1.03, arms=(0.4, -0.3), bob_tip=-0.10, pack_swing=-0.10),
        dict(expr="dizzy", star_rot=2.1, lean=-0.15, sz=0.97, arms=(-0.3, 0.5), bob_tip=0.12, pack_swing=0.12),
        dict(expr="dizzy", star_rot=2.8, lean=0.10, sz=1.06, bob=0.02, arms=(0.6, 0.5), bob_tip=-0.08, pack_swing=-0.06),
        dict(expr="dizzy", star_rot=3.5, sz=0.86, bob=-0.08, legs=((0.06, 0.0), (0.10, 0.0)), arms=(0.2, 0.1), bob_tip=0.06, pack_dz=0.04),
        dict(expr="dizzy", star_rot=4.2, sz=0.74, bob=-0.18, lean=-0.06, legs=((0.12, 0.0), (0.18, 0.0)), arms=(-0.2, -0.1), bob_tip=0.10, pack_dz=0.06, hose_lag=0.05),
        dict(expr="dizzy", star_rot=4.9, sz=0.64, bob=-0.28, lean=-0.14, legs=((0.20, 0.0), (0.26, 0.0)), arms=(-0.5, -0.3), bob_tip=0.12, pack_dz=0.03, hose_lag=0.06, puff=0.2),
        dict(expr="dizzy", star_rot=5.6, sz=0.60, bob=-0.33, lean=-0.18, legs=((0.24, 0.0), (0.30, 0.0)), arms=(-0.6, -0.4), bob_tip=0.06, pack_dz=-0.02, hose_lag=0.02, puff=0.5),
        dict(expr="dizzy", star_rot=6.3, sz=0.62, bob=-0.33, lean=-0.17, legs=((0.24, 0.0), (0.30, 0.0)), arms=(-0.6, -0.4), bob_tip=-0.03, puff=0.8),
        dict(expr="dizzy", star_rot=7.0, sz=0.61, bob=-0.33, lean=-0.18, legs=((0.24, 0.0), (0.30, 0.0)), arms=(-0.6, -0.4), bob_tip=0.01, puff=1.0),
        dict(expr="dizzy", star_rot=7.7, sz=0.61, bob=-0.33, lean=-0.18, legs=((0.24, 0.0), (0.30, 0.0)), arms=(-0.6, -0.4), blink=0.6)]


def run_pose(i):
    ph = TAU * i / 12
    legs = tuple((0.38 * math.sin(ph + math.pi * k), max(0.0, 0.24 * math.cos(ph + math.pi * k))) for k in range(2))
    return dict(legs=legs, bob=0.09 * abs(math.cos(ph)) - 0.03, sz=1.0 + 0.08 * math.cos(2 * ph), lean=0.22,
                arms=(1.1 * math.sin(ph), -1.1 * math.sin(ph)), expr="determined",
                pack_swing=0.20 * math.sin(2 * ph - 1.0) + 0.12, pack_dz=0.05 * math.cos(2 * ph - 1.0),
                hose_lag=0.08 * math.sin(2 * ph - 1.8), bob_tip=0.12 + 0.05 * math.sin(2 * ph - 1.4), look=(0.7, 0.0))


def fall_pose(i):
    ph = TAU * i / 8
    return dict(expr="surprised", sz=1.06 + 0.02 * math.sin(ph), bob=0.04,
                legs=((-0.08 + 0.05 * math.sin(ph), 0.22 + 0.04 * math.cos(ph)), (0.08 - 0.05 * math.sin(ph), 0.26 - 0.04 * math.cos(ph))),
                arms=(2.6 + 0.15 * math.sin(ph), 2.4 - 0.15 * math.sin(ph)), pack_swing=-0.10 + 0.05 * math.sin(ph - 0.8),
                pack_dz=0.06, hose_lag=-0.09 + 0.03 * math.sin(ph - 1.6), bob_tip=-0.10 + 0.04 * math.sin(ph - 1.2))


DASH = [dict(sz=0.86, lean=0.20, legs=((-0.10, 0.0), (0.04, 0.0)), arms=(-0.8, -0.6), expr="determined", pack_swing=-0.05, bob_tip=0.06),
        dict(sz=0.74, lean=0.38, bob=0.03, legs=((-0.30, 0.18), (-0.12, 0.12)), arms=(-1.3, -1.1), expr="determined", speed=0.6, pack_swing=-0.30, pack_dz=0.04, hose_lag=0.10, bob_tip=0.22),
        dict(sz=0.72, lean=0.40, bob=0.03, legs=((-0.32, 0.18), (-0.14, 0.12)), arms=(-1.35, -1.15), expr="determined", speed=1.0, pack_swing=-0.34, pack_dz=0.04, hose_lag=0.12, bob_tip=0.24),
        dict(sz=0.76, lean=0.36, bob=0.03, legs=((-0.28, 0.16), (-0.10, 0.10)), arms=(-1.2, -1.0), expr="determined", speed=0.8, pack_swing=-0.28, pack_dz=0.03, hose_lag=0.10, bob_tip=0.20),
        dict(sz=0.92, lean=0.22, legs=((-0.16, 0.04), (0.02, 0.0)), arms=(-0.6, -0.4), expr="determined", speed=0.3, pack_swing=-0.10, hose_lag=0.04, bob_tip=0.08),
        dict(sz=1.04, lean=0.10, arms=(-0.2, -0.1), pack_swing=0.06, hose_lag=-0.02, bob_tip=-0.04)]


def build(out=DEFAULT_OUT):
    """characters/surveyor/side: the step-2 clips, one drawing per frame at 12 fps."""
    scene = G.new_scene()
    coll = G.collection("surveyor")
    ob, gp = G.gp_object("surveyor", coll)
    M = materials(gp)
    layer = gp.layers.new("art")
    poses = [idle_pose(i) for i in range(10)] + [walk_pose(i) for i in range(12)] + JUMP + LAND + \
        [look_pose(i) for i in range(12)] + BUMP + CONK + [run_pose(i) for i in range(12)] + \
        [fall_pose(i) for i in range(8)] + DASH
    for f, pose in enumerate(poses):
        draw_surveyor(G.drawing(layer, f + 1), M, pose, seed=7 * f)
    G.mark_clips(scene, CLIPS)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


def build_design(out=DESIGN_OUT):
    scene = G.new_scene()
    coll = G.collection("surveyor")
    ob, gp = G.gp_object("surveyor", coll)
    M = materials(gp)
    layer = gp.layers.new("art")
    for i, (view, expr) in enumerate(DESIGN):
        draw_surveyor(G.drawing(layer, i + 1), M, {"view": view, "expr": expr}, seed=10 * i)
    G.mark_clips(scene, [("design", len(DESIGN))])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(argv[0] if argv else DEFAULT_OUT)
