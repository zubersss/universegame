"""Builds blender/sources/creatures/earth_gull_v3.blend: "Gus" the gull (B-113), Grease Pencil.

Original design (Bible §9.3 creatures, §9.8): a stout round gull, friendly (D-087). Off-white
egg body with one shadow tone, sky-grey wing and tail feathers, a wobbly crest tuft that drags
behind every move, a mustard beak with the red gull spot, mustard rubber-hose legs on webbed
feet, pie-cut eyes. Drawn at a cartoon 0.85 m (~54 px at 1x) so it reads beside the surveyor.

Clips (contract §11.2, 12 fps): idle 10 (bob on the 110 bpm beat, head bob, tuft drags),
walk 12 (waddle: body rocks, tail wags), react 8 (eye-pop: crouch, stretch, eyes pop, feathers
up, settle), bump 10 (knocked back, squash, dizzy stars, wobble, settle).
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gp_draw as G  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(HERE), "sources", "creatures", "earth_gull_v3.blend")
P = G.PALETTES["earth"]
O, I = G.OUTER, G.INNER
CLIPS = [("idle", 10), ("walk", 12), ("react", 8), ("bump", 10)]
TAU = 2 * math.pi


def materials(gp):
    return {
        "body": G.mat(gp, "gull_body", fill=P["offwhite"]),
        "body_sh": G.mat(gp, "gull_body_shadow", fill=G.shadow_of(P["offwhite"]), ink=False),
        "wing": G.mat(gp, "gull_wing", fill=P["sky"], behind=True),
        "wing_sh": G.mat(gp, "gull_wing_shadow", fill=G.shadow_of(P["sky"]), behind=True),
        "beak": G.mat(gp, "gull_beak", fill=P["mustard"], behind=True),
        "leg": G.mat(gp, "gull_leg", fill=P["mustard"], behind=True),
        "spot": G.mat(gp, "gull_spot", fill=P["red"], ink=False),
        "ink": G.mat(gp, "ink_line", fill=None, ink=True),
        "pupil": G.mat(gp, "pupil", fill=G.INK, ink=False),
        "eye": G.mat(gp, "eye_white", fill=P["offwhite"]),
        "star": G.mat(gp, "star", fill=P["mustard"]),
        "mouth": G.mat(gp, "mouth_red", fill=P["red"]),
    }


def star(cx, cz, r, rot=0.0):
    return [(cx + r * (1.0 if k % 2 == 0 else 0.45) * math.cos(rot + math.pi / 2 + math.pi * k / 5),
             cz + r * (1.0 if k % 2 == 0 else 0.45) * math.sin(rot + math.pi / 2 + math.pi * k / 5)) for k in range(10)]


def feather(base, ang, length, width):
    """A pointed feather leaf from base along angle ang (rad)."""
    ca, sa = math.cos(ang), math.sin(ang)
    nx, nz = -sa, ca
    tip = (base[0] + ca * length, base[1] + sa * length)
    mid = (base[0] + ca * length * 0.45, base[1] + sa * length * 0.45)
    a = G.bezier(base, (mid[0] + nx * width, mid[1] + nz * width), tip, n=8)
    b = G.bezier(tip, (mid[0] - nx * width, mid[1] - nz * width), base, n=8)[1:-1]
    return a + b


def draw_gull(d, M, pose=None, seed=0):
    p = dict(bob=0.0, sz=1.0, lean=0.0, head=(0.0, 0.0), legs=((0.0, 0.0), (0.0, 0.0)), wing=0.0, tail=0.0,
             tuft=0.0, eye_pop=1.0, blink=0.0, beak_open=0.0, stars=None, look=(0.5, 0.0), rock=0.0)
    p.update(pose or {})
    sz = p["sz"]
    sx = 1 / math.sqrt(sz)
    hip_z = 0.26

    def X(pts, pz=hip_z):
        cr, sr = math.cos(p["rock"]), math.sin(p["rock"])
        out = []
        for x, z in pts:
            x, z = x * sx + p["lean"] * (z - pz), pz + (z - pz) * sz + p["bob"]
            x, z = x * cr - (z - pz) * sr, pz + x * sr + (z - pz) * cr     # waddle rock about the hips
            out.append((x, z))
        return out

    def X1(x, z):
        return X([(x, z)])[0]

    # legs + webbed feet (back leg first)
    def leg(k):
        dx, lift = p["legs"][k]
        hip = X1(-0.04 + 0.10 * k, hip_z + 0.04)
        foot = (hip[0] + dx, 0.05 + lift)
        knee = ((hip[0] + foot[0]) / 2 + 0.05, (hip[1] + foot[1]) / 2)
        G.stroke(d, G.hose_outline(G.bezier(hip, knee, foot, n=8), 0.11), M["leg"], O, cyclic=True)
        fx, fz = foot
        web = [(fx - 0.07, fz + 0.01), (fx + 0.02, fz + 0.05), (fx + 0.22, fz + 0.0), (fx + 0.17, fz - 0.05),
               (fx + 0.11, fz - 0.025), (fx + 0.05, fz - 0.06), (fx, fz - 0.035), (fx - 0.07, fz - 0.05)]
        web = [(x, z + O * 1.25 + 0.06) for x, z in web]
        G.stroke(d, web, M["leg"], O, cyclic=True)
    leg(0)
    # tail feathers (behind the body), wag by p['tail']
    tb = X1(-0.24, 0.47)
    for k, (a, L) in enumerate(((2.70, 0.30), (2.95, 0.34), (3.20, 0.28))):
        G.stroke(d, feather(tb, a + p["tail"], L, 0.085), M["wing"] if k != 1 else M["wing_sh"], O, cyclic=True)
    leg(1)
    # body: an egg with one shadow tone
    body = X(G.lumpy_ellipse(0.0, 0.47, 0.28, 0.23, n=48, lump=0.03, seed=seed + 1))
    G.stroke(d, body, M["body"], 0.0, cyclic=True)
    n = len(body)
    lo = [body[i] for i in range(n) if math.sin(TAU * i / n) < -0.3]
    cx, cz = X1(0.0, 0.47)
    G.stroke(d, lo + [(cx + (x - cx) * 0.78 + 0.02, cz + (z - cz) * 0.55 + 0.02) for x, z in lo][::-1], M["body_sh"], 0.0, cyclic=True)
    G.stroke(d, body, M["ink"], O, cyclic=True)
    # wing on the body side, lifts by p['wing']
    wb = X1(0.10, 0.56)
    G.stroke(d, feather(wb, math.pi + 0.35 - p["wing"], 0.34, 0.12), M["wing"], I, cyclic=True)   # inside the body: interior ink
    # head + crest tuft
    hx, hz = X1(0.17 + p["head"][0], 0.76 + p["head"][1])
    for k in range(3):
        G.stroke(d, feather((hx - 0.03 + 0.04 * k, hz + 0.11), 1.9 + 0.30 * k + p["tuft"], 0.17 - 0.02 * k, 0.055),
                 M["wing"], O, cyclic=True)
    head = G.lumpy_ellipse(hx, hz, 0.16, 0.15, n=36, lump=0.03, seed=seed + 2)
    G.stroke(d, head, M["body"], O, cyclic=True)
    # beak: upper and lower bill, red spot on the lower; opens by p['beak_open']
    bo = p["beak_open"]
    bx, bz = hx + 0.12, hz - 0.03
    up = [(bx - 0.03, bz + 0.06), (bx + 0.11, bz + 0.05), (bx + 0.25, bz + 0.0 + 0.03 * bo), (bx + 0.11, bz - 0.01), (bx - 0.03, bz - 0.01)]
    lo_b = [(bx - 0.03, bz - 0.01), (bx + 0.11, bz - 0.02 - 0.08 * bo), (bx + 0.20, bz - 0.03 - 0.11 * bo), (bx + 0.10, bz - 0.07 - 0.07 * bo), (bx - 0.03, bz - 0.05)]
    if bo > 0.05:
        G.stroke(d, [(bx, bz - 0.01), (bx + 0.17, bz - 0.02 - 0.07 * bo), (bx + 0.14, bz - 0.03)], M["mouth"], I, cyclic=True)
    G.stroke(d, lo_b, M["beak"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(bx + 0.13, bz - 0.035 - 0.08 * bo, 0.025, 0.02, n=10, seed=seed + 3), M["spot"], 0.0, cyclic=True)
    G.stroke(d, up, M["beak"], O, cyclic=True)
    # eyes: two pie-cut eyes in three-quarter profile; pop by p['eye_pop']
    ep = p["eye_pop"]
    for k, ex in enumerate((0.0, 0.075)):
        ey = hz + 0.035 + 0.02 * (ep - 1)
        if p["stars"] is not None:
            G.stroke(d, [(hx + ex + 0.04 * (j / 24) * math.cos(9.4 * j / 24), ey + 0.04 * (j / 24) * math.sin(9.4 * j / 24))
                         for j in range(25)], M["ink"], I)          # dizzy spiral, never X eyes (D-087)
            continue
        G.pie_eye(d, hx + ex, ey, 0.032 * ep, 0.048 * ep, M["pupil"], M["eye"], look=p["look"], seed=seed + 31 + k,
                  closed=p["blink"], m_lid=M["ink"])
    if p["stars"] is not None:
        for k in range(3):
            a = p["stars"] + TAU * k / 3
            G.stroke(d, star(hx + 0.24 * math.cos(a), hz + 0.26 + 0.07 * math.sin(a), 0.055, rot=a), M["star"], I, cyclic=True)


def idle_pose(i):
    ph = TAU * i / 10
    return dict(sz=1 + 0.05 * math.cos(ph), bob=0.01 * math.cos(ph), head=(0.0, 0.02 * math.cos(ph - 0.8)),
                tuft=0.25 * math.sin(ph - 1.4), tail=0.10 * math.sin(ph - 1.0), wing=0.05 * math.sin(ph - 0.6),
                blink={6: 0.6, 7: 1.0}.get(i, 0.0))


def walk_pose(i):
    ph = TAU * i / 12
    legs = tuple((0.10 * math.sin(ph + math.pi * k), max(0.0, 0.07 * math.cos(ph + math.pi * k))) for k in range(2))
    return dict(legs=legs, rock=0.10 * math.sin(ph), bob=0.03 * abs(math.cos(ph)) - 0.01, sz=1 + 0.04 * math.cos(2 * ph),
                head=(0.03 * math.sin(2 * ph - 0.5), 0.015 * math.cos(2 * ph)), tuft=0.35 * math.sin(2 * ph - 1.4),
                tail=0.25 * math.sin(ph - 1.0), wing=0.10 * math.sin(2 * ph - 0.6), lean=0.05)


REACT = [dict(sz=0.85, bob=-0.03, tuft=0.2, tail=-0.1, look=(0.6, -0.2)),
         dict(sz=0.80, bob=-0.04, tuft=0.3, tail=-0.15, blink=0.6),
         dict(sz=1.22, bob=0.03, head=(0.0, 0.08), eye_pop=1.7, beak_open=0.8, tuft=-0.6, tail=0.4, wing=0.7),
         dict(sz=1.18, bob=0.03, head=(0.0, 0.07), eye_pop=1.8, beak_open=0.9, tuft=-0.4, tail=0.3, wing=0.9),
         dict(sz=1.08, bob=0.02, head=(0.0, 0.04), eye_pop=1.5, beak_open=0.6, tuft=0.1, tail=0.1, wing=0.5),
         dict(sz=0.95, bob=0.0, head=(0.0, 0.01), eye_pop=1.2, beak_open=0.2, tuft=0.3, tail=-0.1, wing=0.2),
         dict(sz=1.02, eye_pop=1.05, tuft=-0.1, tail=0.05),
         dict(sz=1.0, tuft=0.05)]

BUMP = [dict(sz=0.75, lean=-0.18, bob=-0.03, head=(-0.06, -0.04), eye_pop=1.4, tuft=0.8, tail=0.5, wing=0.8, beak_open=0.5, legs=((-0.06, 0.04), (0.04, 0.06))),
        dict(sz=0.82, lean=-0.14, head=(-0.05, -0.02), tuft=0.6, tail=0.4, wing=0.6, stars=0.0, beak_open=0.3),
        dict(sz=1.10, lean=-0.10, head=(-0.02, 0.03), tuft=-0.3, tail=-0.2, wing=0.2, stars=0.6),
        dict(sz=0.96, rock=0.10, tuft=0.3, tail=0.2, stars=1.2),
        dict(sz=1.02, rock=-0.10, tuft=-0.2, tail=-0.2, stars=1.8),
        dict(sz=0.98, rock=0.08, tuft=0.2, tail=0.15, stars=2.4),
        dict(sz=1.01, rock=-0.06, tuft=-0.15, tail=-0.1, stars=3.0),
        dict(sz=1.0, rock=0.03, tuft=0.1, stars=3.6),
        dict(sz=1.0, rock=-0.01, blink=1.0, tuft=-0.05),
        dict(sz=1.0, tuft=0.02)]


def build(out=DEFAULT_OUT):
    scene = G.new_scene()
    coll = G.collection("gull")
    ob, gp = G.gp_object("gull", coll)
    M = materials(gp)
    layer = gp.layers.new("art")
    poses = [idle_pose(i) for i in range(10)] + [walk_pose(i) for i in range(12)] + REACT + BUMP
    for f, pose in enumerate(poses):
        draw_gull(G.drawing(layer, f + 1), M, pose, seed=5 * f)
    G.mark_clips(scene, CLIPS)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    build(argv[0] if argv else DEFAULT_OUT)
