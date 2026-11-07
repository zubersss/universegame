"""B-139 part 5 (C2 Mars design prep, LEAD cycle 255): Mars creature design previews on the B-132 creature kit
(build_creatures_earth_v3: posed body, hose legs, pie eyes, dizzy stars), in the Mars palette (D-125). List order 1:

  dustskater  128x80  a small scavenger of the rust plains (~0.8 m): a domed butterscotch shell with rust plate bands,
              a dust-white underside, a short snout, two pie eyes, two knobbed antenna stalks that drag, four splayed
              hose legs on flat dust-white skate pads. Clips idle 10, walk 12 (a skating glide: pads slide, the body
              barely bobs), react 8 (eye-pop and a skid), bump 10, flee 12 (a low dash with dust puffs behind)

Faces kept, friendly or neutral, no teeth (D-087 / D-101). Design preview only: Mars exports wait for Mars cards.

  python -I build_creatures_mars_v3.py <preview dir>      lock-free (meridian.fakegp; exact stroke ids)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creatures_earth_v3 as K  # noqa: E402  (the kit; gp_draw real in Blender, fakegp outside)
from meridian import v3  # noqa: E402

G = K.G
P = v3.PALETTES["mars"]
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi


def SH(h):
    return v3.shadow_of(h, "mars")


def DP(h):
    return v3.deep_of(h, "mars")


def mats(gp, sp="dustskater"):
    def m(name, **kw):
        return G.mat(gp, f"{sp}_{name}", **kw)
    return {
        "shell": m("shell", fill=P["mustard"]), "shell_f": m("shell_f", fill=P["mustard"], ink=False),
        "shell_sh": m("shell_mid", fill=SH(P["mustard"]), ink=False), "shell_dp": m("shell_deep", fill=DP(P["mustard"]), ink=False),
        "band": m("band", fill=P["red"], ink=False), "band_sh": m("band_mid", fill=SH(P["red"]), ink=False),
        "under": m("under", fill=P["offwhite"], ink=False), "under_sh": m("under_mid", fill=SH(P["offwhite"]), ink=False),
        "head": m("head", fill=P["mustard"]), "snout": m("snout", fill=P["offwhite"]),
        "leg": m("leg", fill=SH(P["red"]), behind=True), "leg_far": m("leg_far", fill=DP(P["red"]), behind=True),
        "pad": m("pad", fill=P["offwhite"]), "pad_far": m("pad_far", fill=SH(P["offwhite"])),
        "knob": m("knob", fill=P["red"]), "nose": m("nose", fill=P["brown"]),
        "ink": m("ink", fill=None), "pupil": m("pupil", fill=G.INK, ink=False), "eye": m("eye_white", fill=P["offwhite"]),
        "mouth": m("mouth", fill=P["red"]), "star": m("star", fill=P["mustard"]),
        "puff": m("puff", fill=P["offwhite"]), "puff_sh": m("puff_mid", fill=SH(P["offwhite"]), ink=False),
    }


HIPS = [(-0.20, 0.20), (0.18, 0.20), (-0.24, 0.18), (0.14, 0.18)]       # far hind, far front, near hind, near front
FEET = [-0.36, 0.30, -0.40, 0.26]                                        # splayed: the feet reach past the shell


def skate_leg(d, M, hip, fx, lift, far, slide):
    """A splayed hose leg out to a flat skate pad (slide tilts the pad as it glides)."""
    fz = 0.035 + lift
    knee = ((hip[0] + fx) / 2, max(hip[1], fz) + 0.07)
    G.stroke(d, G.hose_outline(G.bezier(hip, knee, (fx, fz + 0.02), n=8), 0.045), M["leg_far" if far else "leg"], O, cyclic=True)
    pad = [(x * math.cos(slide) - z * math.sin(slide) + fx, x * math.sin(slide) + z * math.cos(slide) + fz)
           for x, z in G.lumpy_ellipse(0.025, 0.0, 0.09, 0.026, n=14, lump=0.04, seed=7)]
    G.stroke(d, pad, M["pad_far" if far else "pad"], O, cyclic=True)
    G.seam(d, [(fx - 0.03, fz - 0.002), (fx + 0.06, fz - 0.004)], M["ink"])


def draw_dustskater(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(slide=(0.0, 0.0, 0.0, 0.0), antenna=0.0, dust=None))
    p.update(pose or {})
    B = K.Body(p, (0.0, 0.27))
    J = (0.24, 0.30)
    H = K.turn(J, p["head_rot"], p["head"], B)
    dh, db = G.Xf(d, H), G.Xf(d, B)
    if p["dust"] is not None:                                             # dust puffs kicked up behind (flee)
        for k in range(2):
            t = (p["dust"] + 0.5 * k) % 1.0
            r = 0.035 + 0.04 * t
            blob = G.lumpy_ellipse(-0.42 - 0.35 * t, r + 0.03, r * 1.2, r, n=14, lump=0.12, seed=80 + k)
            G.stroke(d, blob, M["puff"], I, cyclic=True)
            G.stroke(d, [q for q in blob if q[1] < r * 0.8 + 0.03] + [(-0.42 - 0.35 * t, r * 0.8 + 0.03)], M["puff_sh"], 0.0, cyclic=True)
    for i in (0, 1):                                                      # far legs (behind)
        hip = B.pt(*HIPS[i])
        skate_leg(d, M, hip, FEET[i] * B.sx + p["shift"] + p["legs"][i][0], p["legs"][i][1], True, p["slide"][i])
    for k, side in enumerate((-1, 1)):                                    # antenna stalks (behind the head), drag by p['antenna']
        base = (0.31 + 0.06 * k, 0.43)
        a = math.radians(135 - 55 * k) + p["antenna"] * (1.0 if k == 0 else 0.6)    # splayed: one back, one forward
        tip = (base[0] + 0.15 * math.cos(a), base[1] + 0.15 * math.sin(a))
        G.stroke(dh, G.hose_outline(G.bezier(base, ((base[0] + tip[0]) / 2, base[1] + 0.10), tip, n=6), 0.018), M["leg"], I, cyclic=True)
        G.stroke(dh, G.lumpy_ellipse(tip[0], tip[1], 0.03, 0.03, n=10, seed=60 + k), M["knob"], I, cyclic=True)
    shell = K.body_shape(-0.04, 0.24, 0.30, 0.17, seed + 1, chest=0.0)
    shell = [(x, max(z, 0.12)) for x, z in shell]
    G.stroke(db, shell, M["shell_f"], 0.0, cyclic=True)
    under = [(x, z) for x, z in shell if z < 0.2]
    G.stroke(db, under + [(0.2, 0.16), (-0.3, 0.16)], M["under"], 0.0, cyclic=True)
    G.stroke(db, [q for q in shell if q[1] > 0.36 and q[0] < 0.0] + [(-0.02, 0.36)], M["shell_sh"], 0.0, cyclic=True)
    for k, x in enumerate((-0.20, -0.06, 0.08)):                          # rust plate bands with seams and rivet dots
        band = [(x - 0.035, 0.18), (x + 0.035, 0.18), (x + 0.045 - 0.02 * k, 0.40 - 0.02 * abs(k - 1)), (x - 0.025, 0.41 - 0.02 * abs(k - 1))]
        G.stroke(db, band, M["band"], 0.0, cyclic=True)
        G.seam(db, [(x - 0.035, 0.19), (x - 0.025, 0.40)], M["ink"])
        G.specks(db, [(x + 0.005, 0.30), (x + 0.01, 0.24)], M["ink"])
    G.hatch(db, -0.14, 0.33, M["ink"], n=3, length=0.05, spacing=0.02, angle_deg=65, seed=seed + 5)
    G.seam(db, [(x, z) for x, z in shell if 0.16 < z < 0.22][:8], M["ink"])
    G.stroke(db, shell, M["ink"], O, cyclic=True)
    for i in (2, 3):                                                      # near legs (in front)
        hip = B.pt(*HIPS[i])
        skate_leg(d, M, hip, FEET[i] * B.sx + p["shift"] + p["legs"][i][0], p["legs"][i][1], False, p["slide"][i])
    hx, hz = 0.33, 0.30                                                   # head, snout, nose, mouth, eyes
    G.stroke(dh, G.lumpy_ellipse(hx, hz, 0.11, 0.10, n=28, lump=0.03, seed=seed + 2), M["head"], O, cyclic=True)
    G.stroke(dh, G.lumpy_ellipse(hx + 0.11, hz - 0.035, 0.065, 0.045, n=18, seed=seed + 3, rot=-0.2), M["snout"], O, cyclic=True)
    G.stroke(dh, G.lumpy_ellipse(hx + 0.172, hz - 0.03, 0.022, 0.018, n=10, seed=seed + 4), M["nose"], I, cyclic=True)
    if p["mouth"] > 0.05:
        G.stroke(dh, G.lumpy_ellipse(hx + 0.12, hz - 0.07, 0.012 + 0.01 * p["mouth"], 0.008 + 0.012 * p["mouth"], n=10, seed=seed + 5), M["mouth"], I, cyclic=True)
    else:
        G.seam(dh, G.bezier((hx + 0.08, hz - 0.065), (hx + 0.115, hz - 0.075), (hx + 0.15, hz - 0.06), n=5), M["ink"])
    K.eyes(dh, M, hx + 0.005, hz + 0.035, 0.024, 0.033, 0.045, p, seed)
    if p["stars"] is not None:
        K.stars(dh, M, hx, hz + 0.24, 0.16, p["stars"])


def poses():
    out = []
    for i in range(10):                                                   # idle: breathe, antenna bob, a blink
        ph, q = K.idle_common(i, 10)
        q.update(head_rot=0.04 * math.sin(ph - 0.8), antenna=0.25 * math.sin(ph - 1.4), blink={6: 0.6, 7: 1.0}.get(i, 0.0))
        out.append(q)
    for i in range(12):                                                   # walk: a skating glide (pads slide, little lift)
        ph = TAU * i / 12
        legs = K.walk_legs(ph, 0.10, 0.02)
        out.append(dict(legs=legs, slide=tuple(0.18 * math.sin(ph + f) for f in (math.pi, 1.5 * math.pi, 0.0, 0.5 * math.pi)),
                        bob=0.004 * math.cos(2 * ph), sz=1 + 0.015 * math.cos(2 * ph), rock=0.03 * math.sin(ph), lean=0.03,
                        head_rot=0.03 * math.sin(2 * ph - 0.5), antenna=0.30 * math.sin(2 * ph - 1.4)))
    out += [dict(sz=0.92, bob=-0.01, antenna=0.3, look=(0.7, -0.1)),     # react: eye-pop and a skid
            dict(sz=0.86, bob=-0.015, antenna=0.4, blink=0.6),
            dict(sz=1.14, bob=0.02, head=(0.0, 0.03), eye_pop=1.6, mouth=0.7, antenna=-0.7, lean=-0.06, slide=(0.3, 0.3, 0.3, 0.3)),
            dict(sz=1.10, bob=0.015, head=(0.0, 0.03), eye_pop=1.7, mouth=0.6, antenna=-0.6, lean=-0.08, shift=-0.04, slide=(0.35,) * 4),
            dict(sz=1.04, eye_pop=1.4, mouth=0.3, antenna=-0.3, shift=-0.06, slide=(0.2,) * 4),
            dict(sz=0.98, eye_pop=1.2, antenna=0.2, shift=-0.05, look=(-0.6, 0.0)),
            dict(sz=1.0, eye_pop=1.05, antenna=-0.1, shift=-0.03, look=(0.8, 0.1)),
            dict(sz=1.0, antenna=0.05)]
    out += [dict(q, antenna=q.get("ears", 0.0)) for q in K.bump_clip()]
    for i in range(12):                                                   # flee: a low dash, legs streaming back, dust behind
        ph = TAU * i / 6
        legs = K.walk_legs(ph, 0.16, 0.04)
        out.append(dict(legs=legs, slide=tuple(0.25 * math.sin(ph + f) for f in (math.pi, 1.5 * math.pi, 0.0, 0.5 * math.pi)),
                        bob=0.01 * abs(math.sin(ph)), sz=0.94, lean=0.10, rock=-0.03, head_rot=-0.06, antenna=0.6,
                        look=(0.9, 0.0), dust=(i % 6) / 6.0))
    return out


# ---------------------------------------------------------------- scree stalker (list order 2)
# A canyon pack animal made curious (D-087): a low lizard-hound with a teal hide, scale-ridge rows, rust crest plates
# along the spine that rise when it is surprised, a cheek frill, a mustard belly, clawed hose legs and a long tail
# with a curled tip. It trots after the surveyor nose-down (the wolf's follow pattern). ~1.6 m long, ~0.9 m tall.

STALKER = dict(hips=[(-0.22, 0.40), (0.24, 0.42), (-0.28, 0.38), (0.18, 0.40)], feet=[-0.30, 0.34, -0.38, 0.28],
               ankle=0.06, leg_w=0.062, bend_hind=-0.34, bend_front=0.22, foot="paw", paw=(0.07, 0.035, 3, 2), dangle=0.30)
STALKER_HEAD = 1.2
SB = (0.0, 0.44, 0.40, 0.16)                                             # body centre x, z, radii
CREST = [(-0.26, 0.09), (-0.13, 0.13), (0.01, 0.15), (0.14, 0.13), (0.25, 0.09)]   # plate x, height


def mats_stalker(gp, sp="scree_stalker"):
    def m(name, **kw):
        return G.mat(gp, f"{sp}_{name}", **kw)
    T = P["teal"]
    return {
        "coat": m("coat", fill=T), "coat_i": m("coat_inner", fill=T), "far": m("far", fill=SH(T)),
        "leg": m("leg", fill=T), "leg_far": m("leg_far", fill=SH(T)),
        "sh": m("coat_mid", fill=SH(T), ink=False), "dp": m("coat_deep", fill=DP(T), ink=False),
        "belly": m("belly", fill=P["mustard"], ink=False), "belly_sh": m("belly_mid", fill=SH(P["mustard"]), ink=False),
        "crest": m("crest", fill=P["red"]), "crest_far": m("crest_far", fill=SH(P["red"])),
        "crest_sh": m("crest_mid", fill=SH(P["red"]), ink=False),
        "nose": m("nose", fill=P["brown"]), "claw": m("claw", fill=P["offwhite"], behind=True),
        "ink": m("ink", fill=None), "pupil": m("pupil", fill=G.INK, ink=False), "eye": m("eye_white", fill=P["offwhite"]),
        "mouth": m("mouth", fill=DP(P["red"])), "star": m("star", fill=P["mustard"]),
        "puff": m("puff", fill=P["offwhite"]), "puff_sh": m("puff_mid", fill=SH(P["offwhite"]), ink=False),
    }


def plate(base, ang, h, w):
    """A rounded fin standing on `base`, its axis at angle `ang` (rad; pi/2 = straight up)."""
    ca, sa = math.cos(ang), math.sin(ang)
    nx, nz = sa, -ca

    def at(u, v):
        return (base[0] + ca * u * h + nx * v * w, base[1] + sa * u * h + nz * v * w)
    return G.bezier(at(-0.2, -0.5), at(0.55, -0.55), at(0.95, -0.25), n=7) + \
        G.bezier(at(1.0, -0.1), at(1.05, 0.15), at(0.85, 0.35), n=5)[1:] + G.bezier(at(0.7, 0.45), at(0.3, 0.55), at(-0.2, 0.5), n=6)[1:]


def crest_plates(d, M, p, far=False):
    """Spine plates on the body top, leaning back; p['crest'] raises (react) or flattens (flee) them, crest_ph ripples."""
    cx, cz, rx, rz = SB
    for k, (x, h) in enumerate(CREST):
        top = cz + rz * math.sqrt(max(0.0, 1 - ((x - cx) / rx) ** 2))
        normal = math.atan2((top - cz) / rz ** 2, (x - cx) / rx ** 2)
        H = h * p["crest"] * (1 + 0.10 * math.sin(p["crest_ph"] - 0.9 * k))
        ang = normal + math.radians(14) + 0.25 * (1 - p["crest"])           # flattened plates lie further back
        shape = plate((x, top - 0.035), ang, H + 0.035, 0.115)
        G.stroke(d, shape, M["crest"], O, cyclic=True)
        n = len(shape)
        G.stroke(d, shape[-(n // 4):] + [(x - 0.02, top - 0.01)], M["crest_sh"], 0.0, cyclic=True)   # a sliver on the trailing edge
        tip = (x + math.cos(ang) * (H + 0.035) * 0.7, top - 0.035 + math.sin(ang) * (H + 0.035) * 0.7)
        if 0 < k < len(CREST) - 1:
            G.seam(d, [(x + 0.004, top - 0.01), tip], M["ink"])
        G.stroke(d, shape, M["ink"], O, cyclic=True)


def stalker_tail(d, M, p, seed):
    base = (-0.33, 0.48)
    up = p["tail"]
    c, s = math.cos(up), math.sin(up)
    curl = p["curl"]
    raw = G.bezier(base, (-0.62, 0.52), (-0.84, 0.12), (-1.0, 0.16 + 0.05 * curl), n=18)
    raw += [(-1.0 - 0.05 * math.cos(a), 0.16 + 0.05 * curl + 0.05 * math.sin(a)) for a in (0.9, 1.6, 2.2)][: 1 + int(2 * curl)]
    pts = []
    for i, (x, z) in enumerate(raw):
        t = i / (len(raw) - 1)
        z += p["wave"] * 0.05 * math.sin(math.pi * 1.5 * t) * t
        pts.append((base[0] + (x - base[0]) * c - (z - base[1]) * s, base[1] + (x - base[0]) * s + (z - base[1]) * c))
    left, right = [], []
    for i, (x, z) in enumerate(pts):
        t = i / (len(pts) - 1)
        w = 0.095 * (1 - t) + 0.02 * t
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / L, dx / L
        left.append((x + nx * w, z + nz * w))                                    # underside (the path runs leftwards)
        right.append((x - nx * w, z - nz * w))
    tip = pts[-1]
    shape = left + [(tip[0] - 0.012, tip[1])] + right[::-1]
    G.stroke(d, shape, M["coat"], O, cyclic=True)
    k = int(len(pts) * 0.7)
    mid = [((lx * 0.55 + x * 0.45), (lz * 0.55 + z * 0.45)) for (lx, lz), (x, z) in zip(left[:k], pts[:k])]
    G.stroke(d, left[:k] + mid[::-1], M["belly"], 0.0, cyclic=True)              # a mustard underside stripe
    G.stroke(d, mid, M["ink"], I)
    for j in range(3, len(pts) - 3, 3):                                          # scale bands
        G.seam(d, [right[j], ((right[j][0] + left[j][0]) / 2 + 0.01, (right[j][1] + left[j][1]) / 2)], M["ink"])
    G.stroke(d, shape, M["ink"], O, cyclic=True)


def draw_scree_stalker(d, M, pose=None, seed=0):
    p = K.base_pose()
    p.update(dict(crest=1.0, crest_ph=0.0, curl=0.5, wave=0.0))
    p.update(pose or {})
    cx, cz, rx, rz = SB
    B = K.Body(p, (cx, cz))
    J = (0.30, 0.54)
    hx, hz = 0.58, 0.66
    H = K.turn(J, p["head_rot"], p["head"], B)
    dh, db = G.Xf(d, H), G.Xf(d, B)
    dk = G.Xf(dh, K.scale_about((hx, hz), STALKER_HEAD))

    def R(dx, dz):
        return (hx + dx, hz + dz)
    if p["puff"] is not None:
        K.puff(d, M, -0.75 - 0.3 * p["puff"], 0.08 + 0.05 * p["puff"], 0.05 + 0.04 * p["puff"], seed + 40)
    K.legs_pass(d, M, B, STALKER, p, far=True)
    stalker_tail(db, M, p, seed)
    crest_plates(db, M, p)
    neck = G.bezier((0.16, 0.56), (0.32, 0.66), (0.48, 0.72), n=8) + G.bezier((0.60, 0.56), (0.50, 0.44), (0.30, 0.32), n=8)
    G.stroke(dh, neck, M["coat"], O, cyclic=True)
    G.stroke(dh, G.bezier((0.58, 0.55), (0.50, 0.44), (0.32, 0.33), n=8) + G.bezier((0.30, 0.40), (0.44, 0.48), (0.52, 0.60), n=8),
             M["belly"], 0.0, cyclic=True)                                       # throat
    for k in range(3):
        G.seam(dh, [(0.40 + 0.05 * k, 0.40 + 0.06 * k), (0.45 + 0.05 * k, 0.43 + 0.06 * k)], M["ink"])
    body = K.body_shape(cx, cz, rx, rz, seed + 1, chest=0.03)
    G.stroke(db, body, M["coat_i"], 0.0, cyclic=True)
    n = len(body)
    low = [body[i] for i in range(n) if math.sin(TAU * i / n) < -0.38]
    G.stroke(db, low + [(cx + (x - cx) * 0.88, cz + (z - cz) * 0.45) for x, z in low][::-1], M["belly"], 0.0, cyclic=True)
    deep = [body[i] for i in range(n) if math.sin(TAU * i / n) < -0.75]
    G.stroke(db, deep + [(cx + (x - cx) * 0.92, cz + (z - cz) * 0.8) for x, z in deep][::-1], M["belly_sh"], 0.0, cyclic=True)
    G.stroke(db, [(cx + (x - cx) * 0.88, cz + (z - cz) * 0.45) for x, z in low], M["ink"], I)
    for k in range(5):                                                           # belly plates
        x = -0.22 + 0.11 * k
        G.seam(db, [(x, cz - rz * 0.62), (x - 0.012, cz - rz * 0.92)], M["ink"])
    haunch = G.bezier((-0.10, 0.58), (-0.02, 0.46), (-0.14, 0.33), n=8)
    rear = [q for q in body if q[0] < -0.12 and q[1] > cz - rz * 0.4]
    G.stroke(db, rear + haunch[::-1][:4], M["sh"], 0.0, cyclic=True)
    G.stroke(db, [q for q in body if q[0] < -0.30 and q[1] > cz - rz * 0.3] + [(-0.30, cz + 0.02)], M["dp"], 0.0, cyclic=True)
    G.seam(db, haunch, M["ink"])
    for row, (z0, x0, nn) in enumerate(((0.52, -0.02, 3), (0.45, -0.07, 4))):  # scale-ridge rows
        for k in range(nn):
            x = x0 + 0.075 * k
            G.seam(db, G.bezier((x, z0), (x + 0.035, z0 - 0.03), (x + 0.07, z0), n=4), M["ink"])
    G.stroke(db, body, M["ink"], O, cyclic=True)
    K.legs_pass(d, M, B, STALKER, p, far=False)
    flare = 1.0 + 0.7 * max(0.0, -p["ears"])                                     # the cheek frill (ears in the kit's poses)
    for k, a in enumerate((2.55, 3.05, 3.55)):
        a2 = a + (a - 3.05) * 0.5 * (flare - 1) + 0.3 * p["ears"]
        G.stroke(dk, plate(R(-0.06, -0.02), a2, 0.085 * flare, 0.06), M["crest_far" if k != 1 else "crest"], O, cyclic=True)
    for k, (dx, dz, hh) in enumerate(((-0.07, 0.07, 0.06), (0.01, 0.095, 0.075))):   # head crest
        G.stroke(dk, plate(R(dx, dz), math.radians(115), hh * (0.6 + 0.4 * p["crest"]), 0.05), M["crest"], O, cyclic=True)
    G.stroke(dk, G.lumpy_ellipse(hx, hz, 0.13, 0.10, n=36, lump=0.03, seed=seed + 2, rot=-0.08), M["coat"], O, cyclic=True)
    sn = p["sniff"]
    snout = G.bezier(R(0.03, 0.06), R(0.14, 0.05), R(0.22, 0.015 + 0.008 * sn), n=8) + \
        G.bezier(R(0.245, -0.005 + 0.008 * sn), R(0.255, -0.045), R(0.215, -0.065), n=5) + \
        G.bezier(R(0.19, -0.07), R(0.10, -0.08), R(0.0, -0.06), n=8)
    G.stroke(dk, snout, M["coat"], O, cyclic=True)
    G.stroke(dk, G.bezier(R(0.20, -0.062), R(0.12, -0.074), R(0.03, -0.058), n=8) + G.bezier(R(0.04, -0.038), R(0.12, -0.046), R(0.20, -0.044), n=8),
             M["belly"], 0.0, cyclic=True)                                       # pale lower jaw
    G.stroke(dk, G.lumpy_ellipse(*R(0.215, 0.005 + 0.008 * sn), 0.016 + 0.004 * sn, 0.012, n=10, seed=seed + 6), M["nose"], I, cyclic=True)
    if p["mouth"] > 0.05:
        mo = p["mouth"]
        G.stroke(dk, G.lumpy_ellipse(*R(0.17, -0.05), 0.018 + 0.012 * mo, 0.008 + 0.014 * mo, n=12, seed=seed + 7), M["mouth"], I, cyclic=True)
    else:                                                                        # a long closed smile, curled up at the cheek
        G.seam(dk, G.bezier(R(0.22, -0.045), R(0.13, -0.05), R(0.05, -0.04), R(0.03, -0.018), n=8), M["ink"])
    G.specks(dk, [R(0.12, 0.02), R(0.15, 0.0), R(0.09, 0.0)], M["ink"])
    G.seam(dk, G.bezier(R(-0.02, 0.085), R(0.04, 0.10), R(0.10, 0.075), n=5), M["ink"])   # brow ridge
    K.eyes(dk, M, *R(0.02, 0.03), 0.03, 0.042, 0.058, p, seed)
    if p["stars"] is not None:
        K.stars(dk, M, *R(0.0, 0.25), 0.18, p["stars"])


def stalker_poses():
    out = []
    for i in range(10):                                                          # idle: breathe, crest ripple, tail sway, sniff, blink
        ph, q = K.idle_common(i, 10)
        q.update(head_rot=0.03 * math.sin(ph - 0.8), crest_ph=ph, tail=0.04 * math.sin(ph - 1.0), wave=0.6 * math.sin(ph - 0.5),
                 ears=0.06 * math.sin(ph), sniff=1.0 if i in (2, 3) else 0.0, blink={7: 0.6, 8: 1.0}.get(i, 0.0))
        out.append(q)
    for i in range(12):                                                          # walk: low and slinky, the tail swings
        ph = TAU * i / 12
        out.append(dict(legs=K.walk_legs(ph, 0.13, 0.05), bob=0.008 * math.cos(2 * ph), sz=1 + 0.02 * math.cos(2 * ph),
                        rock=0.025 * math.sin(ph), head_rot=0.035 * math.sin(2 * ph - 0.5), crest_ph=2 * ph,
                        tail=0.05 * math.sin(ph - 1.0), wave=math.sin(ph - 0.8), ears=0.08 * math.sin(2 * ph - 1.2), lean=0.02))
    out += [dict(sz=0.95, look=(0.7, 0.0), crest=1.1),                           # react: the crest shoots up, frill flares
            dict(sz=0.92, head_rot=0.05, sniff=1.0, crest=1.0),
            dict(sz=1.07, head_rot=0.15, head=(0.0, 0.03), eye_pop=1.45, crest=1.55, ears=-0.6, mouth=0.4, tail=0.15, curl=1.0),
            dict(sz=1.05, head_rot=0.17, head=(0.0, 0.03), eye_pop=1.5, crest=1.6, ears=-0.7, mouth=0.5, tail=0.18, curl=1.0),
            dict(sz=1.03, head_rot=0.14, eye_pop=1.3, crest=1.45, ears=-0.55, mouth=0.2, tail=0.15, crest_ph=1.5),
            dict(sz=1.0, head_rot=0.10, eye_pop=1.1, crest=1.3, ears=-0.35, sniff=1.0, tail=0.12, look=(0.9, 0.2), crest_ph=3.0),
            dict(sz=1.0, head_rot=0.06, crest=1.15, ears=-0.15, tail=0.08, look=(0.3, 0.0)),
            dict(sz=1.0, head_rot=0.02, crest=1.05, tail=0.04)]
    out += K.bump_clip(lambda f: dict(crest=1.0 + 1.2 * f.get("antler", 0.0), tail=0.4 * f.get("tail", 0.0), curl=0.5 + 0.5 * f.get("tail", 0.0)))
    for i in range(12):                                                          # flee: two bounds of 6, crest flat, tail streaming
        legs, bob, sz, rock = K.gallop(i / 6, A=0.7, lz=0.6)
        ph = TAU * i / 6
        out.append(dict(legs=legs, bob=bob, sz=sz, rock=rock, lean=0.06, head_rot=-0.05 + 0.04 * math.cos(ph), crest=0.55,
                        crest_ph=ph, ears=0.5, tail=0.06 + 0.04 * math.sin(ph - 1.0), wave=0.5 * math.sin(ph - 1.2), curl=0.0,
                        look=(0.8, 0.0), puff=(i % 6) / 6.0 if i % 3 == 0 else None))
    for i in range(12):                                                          # follow: a curious nose-down trot, tail up and swaying
        ph = TAU * i / 6
        trot = K.walk_legs(ph, 0.10, 0.06, order=(math.pi, 0.0, 0.0, math.pi))
        out.append(dict(legs=trot, bob=0.01 * abs(math.cos(ph)), sz=1 + 0.02 * math.cos(2 * ph), head_rot=-0.13 + 0.03 * math.sin(2 * ph),
                        head=(0.02, -0.02), sniff=1.0 if i % 4 < 2 else 0.0, crest=1.15, crest_ph=ph, ears=-0.15 + 0.08 * math.sin(2 * ph),
                        tail=0.16 + 0.06 * math.sin(TAU * i / 4), wave=0.9 * math.sin(TAU * i / 4), curl=1.0, lean=0.03, look=(0.8, -0.3)))
    return out


SPECIES = {
    "dustskater": dict(draw=draw_dustskater, poses=poses, mats=mats, frame=(128, 80), seed=31,
                       clips=[("idle", 10, True), ("walk", 12, True), ("react", 8, False), ("bump", 10, False), ("flee", 12, True)],
                       self_check={"ink": "shell plate seams, rivet dots, hatch, pad seams, antenna knobs",
                                   "motion": "squash on the beat, hose legs, the antennae drag and overshoot, skating pads slide; flee kicks dust",
                                   "original": "our own scavenger: a butterscotch dome with rust bands on skate pads; no teeth"},
                       ours="a little butterscotch dome on four skate pads that glides over the rust and kicks up dust when it bolts"),
    "scree_stalker": dict(draw=draw_scree_stalker, poses=stalker_poses, mats=mats_stalker, frame=(192, 96), seed=32,
                          clips=[("idle", 10, True), ("walk", 12, True), ("react", 8, False), ("bump", 10, False), ("flee", 12, True),
                                 ("follow", 12, True)],
                          self_check={"ink": "crest plate ribs, scale-ridge rows, belly plates, haunch seam, tail bands, toe seams, brow ridge",
                                      "motion": "squash on the beat, hose legs, the crest ripples and shoots up, the frill flares, the tail swings and curls",
                                      "original": "our own canyon lizard-hound: teal hide, rust spine plates, cheek frill; curious, never a fighter (D-087), no teeth"},
                          ours="a low teal lizard-hound whose rust crest shoots up when it is surprised and who trots after you nose-down, tail swinging"),
}


def preview(out_dir, name="dustskater"):
    """The export's own review layout (render.py v3_sheet_review) from exact frames, on a Mars stand-in (not the Earth plains)."""
    import json
    import numpy as np
    from meridian import fakegp, pngio
    import gp_raster as GR
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    sp = SPECIES[name]
    fw, fh = sp["frame"]
    frames, widths, below = [], [], []
    for f, pose in enumerate(sp["poses"]()):
        gp = fakegp.FakeGP()
        M = sp["mats"](gp, name)
        d = fakegp.FakeDrawing()
        sp["draw"](d, M, pose, seed=5 * f)
        st = fakegp.strokes_of(d, gp, as_object=(name, "art"))
        zmin = min(float((s["xz"][:, 1] - s["radius"] * 1.2).min()) for s in st)
        if zmin * 64 < -2.0:
            below.append(f)
        img, w = GR.render_frame(st, fw, fh, 64, (0.5, 0.0), ss=4, seed=sp["seed"] * 1000 + f + 1)
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
    meta = {"key": f"creatures/mars/{name}", "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols, "gutter": 4,
            "frames": len(frames), "fps": 12, "pivot": [0.5, 0.0], "facing": "right", "ppu": 64, "animations": anims, "squash_root": True}
    problems = v3.validate_sheet(meta, sheet.shape)
    clipped = [i for i, im in enumerate(frames) if im[:2, :, 3].any() or im[:, :2, 3].any() or im[:, -2:, 3].any()]
    if clipped:
        problems.append(f"frames {clipped[:8]} touch the 2 px edge")
    if below:
        problems.append(f"frames {below[:8]} below the ground line")
    dd = os.path.join(out_dir, "b139_mars")
    os.makedirs(dd, exist_ok=True)
    png = os.path.join(dd, f"{name}_color.png")
    nb = pngio.write_png(png, sheet)
    with open(os.path.join(dd, f"{name}.json"), "w", encoding="utf-8", newline="\n") as f_:
        json.dump(meta, f_, indent=2)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    stats = {"outer_px": (min(w[1] for w in outer), max(w[2] for w in outer)), "inner_px": (min(w[1] for w in inner), max(w[2] for w in inner)),
             "inner_n": len(inner), "palette": v3.palette_hits(sheet, "mars"), "problems": problems,
             "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": nb // 1024}
    entry = {"key": meta["key"], "planet": "mars", "bg_scene": "-", "beside": "characters/surveyor/side",
             "self_check": dict(sp["self_check"], style="the B-132 kit (Gus's construction); LEAD judges"), "ours": sp["ours"]}
    out = os.path.join(out_dir, f"review_b139_mars_{name}_preview.png")
    boxes = review.v3_sheet_review(entry, meta, frames, png, out, stats)
    print(name, f"sheet {sheet.shape[1]}x{sheet.shape[0]} {nb // 1024} KB, ink {stats['outer_px'][0]:.2f}-{stats['outer_px'][1]:.2f} / "
          f"{stats['inner_px'][0]:.2f}-{stats['inner_px'][1]:.2f}, palette {stats['palette'][0] * 100:.1f}% {stats['palette'][1][:3]}, "
          f"problems {problems or '-'}, boxes not x: {','.join(k for k, (mk, _n) in boxes.items() if mk != 'x') or '-'}")


if __name__ == "__main__":
    for _n in (sys.argv[2:] or ["dustskater"]):
        preview(sys.argv[1], _n)
