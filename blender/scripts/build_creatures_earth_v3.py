"""B-132: the Earth land creatures re-inked at v3.1 (D-086, D-100; faces kept, D-101; friendly or neutral,
no bared teeth, D-087): the stag, the grey wolf and the brown bear, Grease Pencil, in the manner of Gus
(B-113/B-127): one draw_<name>(d, M, pose) per creature, pose tables per clip, ink-behind on thin parts.

  stag  192x176  ~2.0 m to the antler tips; golden-tan coat, brown neck mane, off-white muzzle, rump patch and
                 flag tail, off-white antlers that wobble behind every stop; clips idle 10, walk 12, react 8
                 (head up, ears swivel, eye-pop, tail flag), bump 10, flee 12 (two bounds, tail flag up)
  wolf  160x128  ~1.0 m to the ear tips; grey coat with a darker saddle, off-white cheek ruff and bib, bushy
                 brown-tipped tail; clips idle 10, walk 12, react 8 (ears up, sniff), bump 10, flee 14,
                 follow 12 (a nose-down trot, tail wagging high: curious, never menacing)
  bear  224x160  ~1.3 m at the hump on all fours; chestnut coat, tan muzzle and inner ears, off-white claws;
                 clips idle 12 (breathing sway), walk 12, react 10 (rears up halfway, sniffs, huffs a round
                 cartoon puff, drops with a thump), bump 10, flee 12

Clip order idle, walk, react, bump, flee (+ follow) keeps Gus's indices: Creature.cs plays 0 idle, 1 walk, 2 on
contact (react) and 3 (bump); flee / follow are found by name.

Sources: one asset per .blend, sources/creatures/earth_<name>_v3.blend (build(name)). Lock-free previews:
  python -I build_creatures_earth_v3.py <preview dir>      (meridian.fakegp, no blender.exe)
"""
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

P = G.PALETTES["earth"]
O, I = G.OUTER, G.INNER
SH, DP = G.shadow_of, G.deep_of
TAU = 2 * math.pi
PPU = 64
SOURCES = os.path.join(os.path.dirname(HERE), "sources", "creatures")

COLOURS = {
    "stag": dict(coat=SH(P["mustard"]), coat_sh=DP(P["mustard"]), coat_dp=P["brown"], light=P["offwhite"],
                 light_sh=SH(P["offwhite"]), dark=P["brown"]),
    "wolf": dict(coat=SH(P["sky"]), coat_sh=DP(P["sky"]), coat_dp=P["brown"], light=P["offwhite"],
                 light_sh=SH(P["offwhite"]), dark=P["brown"]),
    "bear": dict(coat=DP(P["red"]), coat_sh=P["brown"], coat_dp=P["brown"], light=SH(P["mustard"]),
                 light_sh=DP(P["mustard"]), dark=G.INK),
}


def mats(gp, sp):
    C = COLOURS[sp]
    thin = sp != "bear"                 # stag and wolf legs are thin: ink-behind keeps their colour

    def m(name, **kw):
        return G.mat(gp, f"{sp}_{name}", **kw)
    return {
        "coat": m("coat", fill=C["coat"]),
        "coat_i": m("coat_inner", fill=C["coat"]),
        "far": m("far", fill=C["coat_sh"]),
        "leg": m("leg", fill=C["coat"], behind=thin),
        "leg_far": m("leg_far", fill=C["coat_sh"], behind=thin),
        "sh": m("coat_mid", fill=C["coat_sh"], ink=False),
        "dp": m("coat_deep", fill=C["coat_dp"], ink=False),
        "light": m("light", fill=C["light"]),
        "light_f": m("light_f", fill=C["light"], ink=False),
        "light_sh": m("light_mid", fill=C["light_sh"], ink=False),
        "dark": m("dark", fill=C["dark"]),
        "dark_b": m("dark_behind", fill=C["dark"], behind=True),
        "dark_f": m("dark_f", fill=C["dark"], ink=False),
        "horn": m("horn", fill=P["offwhite"], behind=True),
        "horn_far": m("horn_far", fill=SH(P["offwhite"]), behind=True),
        "claw": m("claw", fill=P["offwhite"], behind=True),
        "ink": m("ink", fill=None),
        "pupil": m("pupil", fill=G.INK, ink=False),
        "eye": m("eye_white", fill=P["offwhite"]),
        "mouth": m("mouth_red", fill=P["red"]),
        "star": m("star", fill=P["mustard"]),
        "puff": m("puff", fill=P["offwhite"]),
        "puff_sh": m("puff_mid", fill=SH(P["offwhite"]), ink=False),
    }


# ---------------------------------------------------------------- shared quadruped toolkit (metres, XZ, ground z = 0)

def base_pose():
    return dict(bob=0.0, sz=1.0, lean=0.0, rock=0.0, rock_at=None, shift=0.0, head=(0.0, 0.0), head_rot=0.0,
                ears=0.0, tail=0.0, legs=((0.0, 0.0),) * 4, eye_pop=1.0, blink=0.0, look=(0.5, 0.0), stars=None,
                mouth=0.0, antler=0.0, front_up=0.0, puff=None, sniff=0.0)


class Body:
    """Rest-pose coordinates -> the posed drawing: pitch `rock` (+ = nose up) about rock_at, squash sz about the
    ground (x by 1/sqrt(sz), volume kept), lean (shear by height), bob and shift."""
    def __init__(self, p, rock_at):
        self.p = p
        self.sz, self.sx = p["sz"], 1.0 / math.sqrt(p["sz"])
        self.c, self.s = math.cos(p["rock"]), math.sin(p["rock"])
        self.ax, self.az = p["rock_at"] or rock_at

    def __call__(self, pts):
        p, out = self.p, []
        for x, z in pts:
            dx, dz = x - self.ax, z - self.az
            x, z = self.ax + dx * self.c - dz * self.s, self.az + dx * self.s + dz * self.c
            out.append((x * self.sx + p["lean"] * z + p["shift"], z * self.sz + p["bob"]))
        return out

    def pt(self, x, z):
        return self([(x, z)])[0]


def turn(J, rot, off, then):
    """Rotate about J (+ = counter-clockwise: nose up for a right-facing head), offset, then `then`."""
    c, s = math.cos(rot), math.sin(rot)

    def f(pts):
        return then([(J[0] + (x - J[0]) * c - (z - J[1]) * s + off[0], J[1] + (x - J[0]) * s + (z - J[1]) * c + off[1])
                     for x, z in pts])
    return f


def feather(base, ang, length, width, bulge=0.45):
    """A pointed leaf (ears, tail flags) from base along angle ang (rad)."""
    ca, sa = math.cos(ang), math.sin(ang)
    nx, nz = -sa, ca
    tip = (base[0] + ca * length, base[1] + sa * length)
    mid = (base[0] + ca * length * bulge, base[1] + sa * length * bulge)
    a = G.bezier(base, (mid[0] + nx * width, mid[1] + nz * width), tip, n=8)
    b = G.bezier(tip, (mid[0] - nx * width, mid[1] - nz * width), base, n=8)[1:-1]
    return a + b


def star(cx, cz, r, rot=0.0):
    return [(cx + r * (1.0 if k % 2 == 0 else 0.45) * math.cos(rot + math.pi / 2 + math.pi * k / 5),
             cz + r * (1.0 if k % 2 == 0 else 0.45) * math.sin(rot + math.pi / 2 + math.pi * k / 5)) for k in range(10)]


def leg(d, mat, hip, foot_x, ankle_z, width, bend):
    """A rubber-hose leg from the hip (posed) to the ankle (world). bend > 0 bows the knee forward, < 0 back
    (a hind leg's hock). Returns the centre line."""
    hx, hz = hip
    L = max(hz - ankle_z, 0.1)
    c1 = (hx + bend * 0.6 * L, hz - 0.35 * L)
    c2 = (foot_x - bend * L, ankle_z + 0.40 * L)
    center = G.bezier((hx, hz), c1, c2, (foot_x, ankle_z), n=10)
    G.stroke(d, G.hose_outline(center, width), mat, O, cyclic=True)
    return center


def hoof(d, M, ax, az):
    """A cloven hoof hanging under the ankle (az = its top); split seam + a fetlock tick."""
    pts = [(ax - 0.048, az + 0.012), (ax + 0.044, az + 0.012), (ax + 0.068, az - 0.072), (ax - 0.054, az - 0.072)]
    G.stroke(d, pts, M["dark"], O, cyclic=True)
    G.seam(d, [(ax + 0.008, az - 0.072), (ax + 0.004, az - 0.028)], M["ink"])
    G.seam(d, [(ax - 0.04, az + 0.04), (ax + 0.035, az + 0.045)], M["ink"])


def paw(d, M, mat, ax, az, rx, rz, toes=2, claws=0, seed=0):
    """A round paw under the ankle: toe seams at the front, optional claws poking out."""
    cx, cz = ax + rx * 0.35, az
    G.stroke(d, G.lumpy_ellipse(cx, cz, rx, rz, n=20, lump=0.04, seed=seed), mat, O, cyclic=True)
    for k in range(toes):
        tx = cx + rx * (0.2 + 0.35 * k)
        G.seam(d, [(tx, cz - rz * 0.95), (tx - rx * 0.08, cz - rz * 0.2)], M["ink"])
    for k in range(claws):
        tx = cx + rx * (0.45 + 0.22 * k)
        tz = cz - rz * (0.55 - 0.05 * k)
        G.stroke(d, [(tx, tz + 0.02), (tx + 0.05, tz - 0.012), (tx + 0.008, tz - 0.02)], M["claw"], I, cyclic=True)


def eyes(d, M, x, z, rx, rz, gap, p, seed):
    """Two pie-cut eyes in three-quarter profile (Gus's arrangement); dizzy spirals while stars circle."""
    ep = p["eye_pop"]
    for k, ex in enumerate((0.0, gap)):
        ey = z + 0.02 * (ep - 1)
        if p["stars"] is not None:
            G.stroke(d, [(x + ex + rx * 1.2 * (j / 24) * math.cos(9.4 * j / 24), ey + rx * 1.2 * (j / 24) * math.sin(9.4 * j / 24))
                         for j in range(25)], M["ink"], I)                     # dizzy spiral, never X eyes (D-087)
            continue
        G.pie_eye(d, x + ex, ey, rx * ep, rz * ep, M["pupil"], M["eye"], look=p["look"], seed=seed + 31 + k,
                  closed=p["blink"], m_lid=M["ink"])


def stars(d, M, cx, cz, rad, a0):
    for k in range(3):
        a = a0 + TAU * k / 3
        G.stroke(d, star(cx + rad * math.cos(a), cz + 0.07 * math.sin(a), 0.055, rot=a), M["star"], I, cyclic=True)


def puff(d, M, cx, cz, r, seed):
    """A round cartoon huff cloud (no fx sheet)."""
    blob = G.lumpy_ellipse(cx, cz, r * 1.15, r, n=18, lump=0.12, seed=seed)
    G.stroke(d, blob, M["puff"], I, cyclic=True)
    G.stroke(d, [q for q in blob if q[1] < cz - r * 0.25] + [(cx, cz - r * 0.25)], M["puff_sh"], 0.0, cyclic=True)


def body_shape(cx, cz, rx, rz, seed, chest=0.0, hump=None, lump=0.03):
    """A lumpy bean: the chest hangs a little lower in front; an optional shoulder hump (x, height, width)."""
    pts = []
    for x, z in G.lumpy_ellipse(cx, cz, rx, rz, n=56, lump=lump, seed=seed):
        if z < cz and x > cx + 0.2 * rx:
            z -= chest * (x - cx - 0.2 * rx) / (0.8 * rx)
        if hump and z > cz:
            hx, hh, hw = hump
            z += hh * math.exp(-((x - hx) / hw) ** 2)
        pts.append((x, z))
    return pts


def shade(d, M, body, cx, cz, lo=-0.3, deep=-0.65, deep_x=None):
    """Gus's tones: a lower crescent in the mid shadow, a sliver of the deep tone (optionally only behind deep_x)."""
    n = len(body)
    sl = [body[i] for i in range(n) if math.sin(TAU * i / n) < lo]
    G.stroke(d, sl + [(cx + (x - cx) * 0.8 + 0.02, cz + (z - cz) * 0.5 + 0.02) for x, z in sl][::-1], M["sh"], 0.0, cyclic=True)
    dl = [body[i] for i in range(n) if math.sin(TAU * i / n) < deep and (deep_x is None or body[i][0] < deep_x)]
    if len(dl) > 3:
        G.stroke(d, dl + [(cx + (x - cx) * 0.9 + 0.01, cz + (z - cz) * 0.8 + 0.01) for x, z in dl][::-1], M["dp"], 0.0, cyclic=True)


def jag(pts, amp, seed=0):
    """Push every other point outward along the local normal: a fur edge."""
    out = []
    for i, (x, z) in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz) or 1.0
        k = amp if (i + seed) % 2 else -amp * 0.3
        out.append((x - dz / L * k, z + dx / L * k))
    return out


def legs_pass(d, M, B, spec, p, far):
    """Far pair (shadow tone) or near pair: hose legs + hooves / paws. Order in p['legs']: far hind, far front,
    near hind, near front."""
    for j, kind in enumerate(("hind", "front")):
        i = j if far else 2 + j
        hx, hz = spec["hips"][i]
        dx, lift = p["legs"][i][:2]
        fold = p["legs"][i][2] if len(p["legs"][i]) > 2 else 0.0      # extra knee bend (gallop tuck)
        hip = B.pt(hx, hz)
        fx = spec["feet"][i] * B.sx + p["shift"] + dx
        az = spec["ankle"] + lift
        if kind == "front" and p["front_up"] > 0:             # rearing: the front feet hang from the shoulders
            t = p["front_up"]
            fx = fx * (1 - t) + (hip[0] + 0.06) * t
            az = az * (1 - t) + (hip[1] - spec["dangle"]) * t
        bend = (spec["bend_hind"] if kind == "hind" else spec["bend_front"]) + fold
        leg(d, M["leg_far"] if far else M["leg"], hip, fx, az, spec["leg_w"], bend)
        if spec["foot"] == "hoof":
            hoof(d, M, fx, az)
        else:
            rx, rz, toes, claws = spec["paw"]
            paw(d, M, M["far"] if far else M["coat"], fx, az - rz * 0.35, rx, rz, toes, claws, seed=17 + i)


# ---------------------------------------------------------------- stag

STAG = dict(hips=[(-0.20, 0.86), (0.36, 0.86), (-0.28, 0.84), (0.28, 0.84)], feet=[-0.22, 0.38, -0.30, 0.30],
            ankle=0.085, leg_w=0.085, bend_hind=-0.14, bend_front=0.05, foot="hoof", dangle=0.6)
STAG_HEAD = 1.3                          # the head and its parts drawn 1.3x about the skull centre (era proportions)


def scale_about(c, k):
    def f(pts):
        return [(c[0] + (x - c[0]) * k, c[1] + (z - c[1]) * k) for x, z in pts]
    return f


def draw_stag(d, M, pose=None, seed=0):
    p = base_pose()
    p.update(pose or {})
    B = Body(p, (0.0, 0.92))
    J = (0.30, 1.02)
    hx, hz = 0.60, 1.48
    H = turn(J, p["head_rot"], p["head"], B)
    dh, db = G.Xf(d, H), G.Xf(d, B)
    dk = G.Xf(dh, scale_about((hx, hz), STAG_HEAD))                              # head parts, drawn big

    def R(dx, dz):
        return (hx + dx, hz + dz)

    def antler(bx, bz, mat, spread):
        A = G.Xf(dk, turn((bx, bz), p["antler"] + spread, (0.0, 0.0), lambda q: q))
        beam = G.bezier((bx, bz), (bx - 0.15, bz + 0.07), (bx - 0.20, bz + 0.25), (bx - 0.09, bz + 0.36), n=12)
        for t, ang, L in ((0.16, 0.30, 0.12), (0.50, 0.70, 0.12), (0.84, 1.35, 0.07)):   # brow, trez, crown tines
            k = int(round(t * (len(beam) - 1)))
            px, pz = beam[k]
            tip = (px + L * math.cos(ang), pz + L * math.sin(ang) + 0.02)
            G.stroke(A, G.hose_outline(G.bezier((px, pz), (px + 0.6 * L * math.cos(ang), pz + 0.6 * L * math.sin(ang) - 0.01),
                                                 tip, n=6), 0.034), mat, O, cyclic=True)
        G.stroke(A, G.hose_outline(beam, 0.042), mat, O, cyclic=True)
        G.ribs(A, beam[:3], 0.06, M["ink"], every=0.022, frac=0.9)              # the burr at the base
        G.seam(A, beam[5:9], M["ink"])

    antler(*R(-0.05, 0.11), M["horn_far"], 0.35)                                 # far antler + far ear (behind)
    G.stroke(dk, feather(R(-0.09, 0.07), 2.80 + p["ears"], 0.20, 0.07), M["far"], O, cyclic=True)
    legs_pass(d, M, B, STAG, p, far=True)
    tb = (-0.43, 1.04)                                                           # the flag tail
    G.stroke(db, feather(tb, 2.55 - p["tail"], 0.17, 0.065), M["light"], O, cyclic=True)
    ta = 2.55 - p["tail"]
    G.seam(db, [(tb[0] + 0.03 * math.cos(ta), tb[1] + 0.03 * math.sin(ta)), (tb[0] + 0.11 * math.cos(ta), tb[1] + 0.11 * math.sin(ta))], M["ink"])
    legs_pass(d, M, B, STAG, p, far=False)
    # neck + brown mane (they turn with the head)
    back = G.bezier((0.08, 1.06), (0.26, 1.32), (0.47, 1.50), n=10)
    front = G.bezier((0.68, 1.36), (0.56, 1.10), (0.44, 0.84), n=12)
    G.stroke(dh, back + front, M["coat"], O, cyclic=True)
    mane_out = jag(front[1:10], 0.03, seed=1)
    mane_in = [(x - 0.075, z + 0.01) for x, z in front[1:10]]
    G.stroke(dh, mane_out + mane_in[::-1], M["dark_f"], 0.0, cyclic=True)
    G.stroke(dh, mane_out, M["ink"], I)
    for k in (2, 4, 6):
        x, z = front[k]
        G.seam(dh, [(x - 0.06, z + 0.02), (x - 0.02, z - 0.02)], M["ink"])
    # body
    body = body_shape(0.0, 0.92, 0.46, 0.25, seed + 1, chest=0.04)
    G.stroke(db, body, M["coat_i"], 0.0, cyclic=True)
    shade(db, M, body, 0.0, 0.92, deep_x=-0.12)
    G.stroke(db, G.lumpy_ellipse(-0.35, 0.98, 0.065, 0.11, n=20, seed=seed + 4), M["light"], I, cyclic=True)   # rump patch
    G.stroke(db, [(-0.41, 0.94), (-0.29, 0.94), (-0.30, 0.89), (-0.35, 0.875), (-0.40, 0.89)], M["light_sh"], 0.0, cyclic=True)
    G.seam(db, G.bezier((-0.16, 1.13), (-0.07, 0.97), (-0.18, 0.78), n=8), M["ink"])           # haunch
    G.seam(db, G.bezier((0.20, 1.13), (0.28, 0.98), (0.19, 0.82), n=8), M["ink"])              # shoulder
    G.hatch(db, 0.02, 0.82, M["ink"], n=3, length=0.07, spacing=0.03, angle_deg=60, seed=seed + 5)
    G.specks(db, [(0.30, 1.05), (0.34, 1.0), (0.27, 0.99), (-0.05, 1.07)], M["ink"])
    for k in range(3):                                                           # chest fur tufts
        cx, cz = 0.43 - 0.02 * k, 0.92 - 0.06 * k
        G.stroke(db, [(cx - 0.03, cz + 0.02), (cx, cz - 0.01), (cx - 0.02, cz - 0.03)], M["ink"], I)
    G.stroke(db, body, M["ink"], O, cyclic=True)
    # head (1.3x): skull, off-white muzzle, nose, mouth, eyes, near ear, near antler
    G.stroke(dk, G.lumpy_ellipse(hx, hz, 0.15, 0.12, n=36, lump=0.03, seed=seed + 2, rot=-0.3), M["coat"], O, cyclic=True)
    G.stroke(dk, [R(-0.13, -0.05), R(-0.02, -0.11), R(0.05, -0.11), R(-0.05, -0.06)], M["sh"], 0.0, cyclic=True)
    G.stroke(dk, G.lumpy_ellipse(*R(0.15, -0.10), 0.10, 0.07, n=24, lump=0.03, seed=seed + 3, rot=-0.4), M["light"], O, cyclic=True)
    G.stroke(dk, G.lumpy_ellipse(*R(0.232, -0.112), 0.036, 0.03, n=14, seed=seed + 6), M["dark"], I, cyclic=True)
    if p["mouth"] > 0.05:
        mo = p["mouth"]
        G.stroke(dk, G.lumpy_ellipse(*R(0.165, -0.14), 0.02 + 0.016 * mo, 0.01 + 0.018 * mo, n=12, seed=seed + 7), M["mouth"], I, cyclic=True)
    else:
        G.seam(dk, G.bezier(R(0.12, -0.128), R(0.16, -0.143), R(0.195, -0.13), n=5), M["ink"])
    G.specks(dk, [R(0.18, -0.08), R(0.195, -0.095)], M["ink"])                   # whisker pores
    eyes(dk, M, *R(-0.005, 0.035), 0.034, 0.048, 0.07, p, seed)
    G.stroke(dk, feather(R(-0.065, 0.075), 2.70 + p["ears"], 0.21, 0.08), M["coat"], O, cyclic=True)
    G.stroke(dk, feather(R(-0.075, 0.08), 2.70 + p["ears"], 0.14, 0.04), M["light_sh"], 0.0, cyclic=True)
    antler(*R(-0.02, 0.10), M["horn"], 0.0)
    if p["stars"] is not None:
        stars(dk, M, *R(-0.04, 0.24), 0.20, p["stars"])


# ---------------------------------------------------------------- grey wolf

WOLF = dict(hips=[(-0.16, 0.53), (0.29, 0.53), (-0.23, 0.51), (0.23, 0.51)], feet=[-0.18, 0.31, -0.25, 0.25],
            ankle=0.07, leg_w=0.075, bend_hind=-0.16, bend_front=0.05, foot="paw", paw=(0.06, 0.035, 2, 0), dangle=0.35)
WOLF_HEAD = 1.25


def wolf_tail(d, M, p, seed):
    base = (-0.31, 0.64)
    up = p["tail"]
    c, s = math.cos(-up), math.sin(-up)
    rot = [(base[0] + (x - base[0]) * c - (z - base[1]) * s, base[1] + (x - base[0]) * s + (z - base[1]) * c)
           for x, z in G.bezier(base, (-0.55, 0.69), (-0.67, 0.47), n=14)]
    left, right = [], []
    for i, (x, z) in enumerate(rot):
        t = i / (len(rot) - 1)
        w = 0.045 + 0.06 * math.sin(math.pi * min(t * 1.25, 1.0)) * (1 - 0.6 * max(0.0, t - 0.8) / 0.2)
        a, b = rot[max(i - 1, 0)], rot[min(i + 1, len(rot) - 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / L, dx / L
        left.append((x + nx * w, z + nz * w))
        right.append((x - nx * w, z - nz * w))
    tip = rot[-1]
    shape = jag(left, 0.014, seed) + [(tip[0] - 0.03, tip[1] - 0.03)] + jag(right, 0.014, seed + 1)[::-1]
    G.stroke(d, shape, M["coat"], O, cyclic=True)
    k = int(len(rot) * 0.72)
    G.stroke(d, left[k:] + [(tip[0] - 0.03, tip[1] - 0.03)] + right[k:][::-1], M["dark_f"], 0.0, cyclic=True)
    G.stroke(d, [right[k - 1], right[k], ((left[k][0] + right[k][0]) / 2, (left[k][1] + right[k][1]) / 2), left[k]], M["ink"], I)
    for off in (-0.25, 0.25):
        G.seam(d, [((1 + off) * left[j][0] / 2 + (1 - off) * right[j][0] / 2, (1 + off) * left[j][1] / 2 + (1 - off) * right[j][1] / 2)
                   for j in range(3, k - 1, 2)], M["ink"])
    G.stroke(d, shape, M["ink"], O, cyclic=True)


def draw_wolf(d, M, pose=None, seed=0):
    p = base_pose()
    p.update(pose or {})
    B = Body(p, (0.0, 0.57))
    J = (0.22, 0.62)
    hx, hz = 0.44, 0.80
    H = turn(J, p["head_rot"], p["head"], B)
    dh, db = G.Xf(d, H), G.Xf(d, B)
    dk = G.Xf(dh, scale_about((hx, hz), WOLF_HEAD))

    def R(dx, dz):
        return (hx + dx, hz + dz)
    G.stroke(dk, feather(R(-0.075, 0.085), 1.70 + p["ears"], 0.15, 0.06, bulge=0.3), M["far"], O, cyclic=True)   # far ear
    legs_pass(d, M, B, WOLF, p, far=True)
    wolf_tail(db, M, p, seed)
    legs_pass(d, M, B, WOLF, p, far=False)
    back = G.bezier((0.06, 0.68), (0.24, 0.84), (0.40, 0.90), n=10)                                   # neck
    front = G.bezier((0.52, 0.72), (0.45, 0.56), (0.32, 0.43), n=12)
    G.stroke(dh, back + front, M["coat"], O, cyclic=True)
    bib_out = jag(front[0:11], 0.02, seed=0)
    bib_in = [(x - 0.07, z + 0.02) for x, z in front[0:11]]
    G.stroke(dh, bib_out + bib_in[::-1], M["light_f"], 0.0, cyclic=True)                              # off-white bib
    G.stroke(dh, bib_in, M["ink"], I)
    G.stroke(dh, bib_out, M["ink"], I)
    body = body_shape(0.0, 0.57, 0.36, 0.19, seed + 1, chest=0.035)
    G.stroke(db, body, M["coat_i"], 0.0, cyclic=True)
    n = len(body)
    top = [body[i] for i in range(n) if math.sin(TAU * i / n) > 0.42]                                  # the darker saddle
    G.stroke(db, top + jag([(x, z - 0.06) for x, z in top], 0.015, seed)[::-1], M["sh"], 0.0, cyclic=True)
    shade(db, M, body, 0.0, 0.57, deep_x=-0.10)
    G.seam(db, G.bezier((-0.13, 0.72), (-0.05, 0.59), (-0.15, 0.44), n=8), M["ink"])                  # haunch
    for k in range(4):                                                                               # fur ticks
        x = -0.22 + 0.12 * k
        G.stroke(db, [(x, 0.68), (x + 0.025, 0.655), (x + 0.045, 0.675)], M["ink"], I)
    G.hatch(db, 0.08, 0.47, M["ink"], n=3, length=0.06, spacing=0.025, angle_deg=65, seed=seed + 5)
    G.stroke(db, body, M["ink"], O, cyclic=True)
    G.stroke(dk, G.lumpy_ellipse(hx, hz, 0.14, 0.12, n=36, lump=0.03, seed=seed + 2, rot=-0.1), M["coat"], O, cyclic=True)
    sn = p["sniff"]
    snout = G.bezier(R(0.04, 0.055), R(0.13, 0.03), R(0.21, -0.005 + 0.01 * sn), n=8) + \
        G.bezier(R(0.235, -0.025 + 0.01 * sn), R(0.24, -0.055), R(0.20, -0.068), n=5) + \
        G.bezier(R(0.18, -0.07), R(0.10, -0.078), R(0.02, -0.065), n=8)
    G.stroke(dk, snout, M["coat"], O, cyclic=True)
    G.stroke(dk, G.bezier(R(0.20, -0.06), R(0.12, -0.072), R(0.04, -0.06), n=8) + G.bezier(R(0.04, -0.035), R(0.12, -0.042), R(0.20, -0.042), n=8),
             M["light_f"], 0.0, cyclic=True)                                                         # pale lower jaw
    G.stroke(dk, G.lumpy_ellipse(*R(0.228, -0.017 + 0.01 * sn), 0.032, 0.026, n=14, seed=seed + 6), M["dark"], I, cyclic=True)
    G.seam(dk, [R(0.08, 0.035), R(0.16, 0.008)], M["ink"])                                            # muzzle seam
    if p["mouth"] > 0.05:
        mo = p["mouth"]
        G.stroke(dk, G.lumpy_ellipse(*R(0.16, -0.06), 0.02 + 0.014 * mo, 0.01 + 0.016 * mo, n=12, seed=seed + 7), M["mouth"], I, cyclic=True)
    else:
        G.seam(dk, G.bezier(R(0.205, -0.052), R(0.13, -0.058), R(0.075, -0.045), n=6), M["ink"])
    G.specks(dk, [R(0.16, -0.02), R(0.175, -0.03), R(0.145, -0.032)], M["ink"])
    ruff = jag(G.lumpy_ellipse(*R(-0.07, -0.06), 0.06, 0.055, n=16, lump=0.05, seed=seed + 8), 0.012, seed)
    G.stroke(dk, ruff, M["light"], I, cyclic=True)                                                   # cheek ruff
    eyes(dk, M, *R(0.02, 0.035), 0.03, 0.042, 0.06, p, seed)
    G.stroke(dk, feather(R(-0.03, 0.095), 1.78 + p["ears"], 0.16, 0.065, bulge=0.3), M["coat"], O, cyclic=True)
    G.stroke(dk, feather(R(-0.025, 0.10), 1.78 + p["ears"], 0.10, 0.032, bulge=0.3), M["light_sh"], 0.0, cyclic=True)
    if p["stars"] is not None:
        stars(dk, M, *R(0.0, 0.25), 0.18, p["stars"])


# ---------------------------------------------------------------- brown bear

BEAR = dict(hips=[(-0.32, 0.68), (0.38, 0.68), (-0.40, 0.66), (0.30, 0.66)], feet=[-0.32, 0.40, -0.40, 0.32],
            ankle=0.11, leg_w=0.19, bend_hind=-0.06, bend_front=0.03, foot="paw", paw=(0.13, 0.065, 3, 3), dangle=0.42)
BEAR_HEAD = 1.15


def draw_bear(d, M, pose=None, seed=0):
    p = base_pose()
    p.update(pose or {})
    B = Body(p, (-0.40, 0.55))
    J = (0.40, 0.92)
    hx, hz = 0.68, 0.92
    H = turn(J, p["head_rot"], p["head"], B)
    dh, db = G.Xf(d, H), G.Xf(d, B)
    dk = G.Xf(dh, scale_about((hx, hz), BEAR_HEAD))

    def R(dx, dz):
        return (hx + dx, hz + dz)
    legs_pass(d, M, B, BEAR, p, far=True)
    G.stroke(db, G.lumpy_ellipse(-0.64, 0.99 + 0.02 * p["tail"], 0.06, 0.05, n=14, seed=seed + 9), M["coat"], O, cyclic=True)
    legs_pass(d, M, B, BEAR, p, far=False)
    body = body_shape(-0.05, 0.84, 0.60, 0.34, seed + 1, chest=0.03, hump=(0.22, 0.11, 0.22), lump=0.025)
    G.stroke(db, body, M["coat_i"], 0.0, cyclic=True)
    shade(db, M, body, -0.05, 0.84, lo=-0.35, deep=-0.9)
    G.hatch(db, 0.16, 1.17, M["ink"], n=4, length=0.09, spacing=0.035, angle_deg=70, seed=seed + 5)    # hump fur
    G.hatch(db, -0.44, 1.02, M["ink"], n=3, length=0.08, spacing=0.035, angle_deg=110, seed=seed + 6)  # haunch fur
    G.seam(db, G.bezier((-0.22, 1.12), (-0.12, 0.90), (-0.24, 0.66), n=8), M["ink"])                   # haunch
    G.seam(db, G.bezier((0.30, 1.10), (0.40, 0.92), (0.30, 0.70), n=8), M["ink"])                      # shoulder
    for k in range(5):                                                                               # shaggy belly fringe
        x = -0.36 + 0.14 * k
        G.stroke(db, [(x, 0.57), (x + 0.03, 0.535), (x + 0.06, 0.565)], M["ink"], I)
    G.stroke(db, body, M["ink"], O, cyclic=True)
    for k, (ex, ez) in enumerate(((-0.12, 0.16), (-0.035, 0.18))):                                    # ears (behind the head)
        e = G.lumpy_ellipse(*R(ex, ez), 0.068, 0.062, n=18, lump=0.04, seed=seed + 10 + k, rot=0.5)
        G.stroke(dk, e, M["far"] if k == 0 else M["coat"], O, cyclic=True)
        if k == 1:
            G.stroke(dk, G.lumpy_ellipse(*R(ex + 0.005, ez + 0.002), 0.034, 0.03, n=12, seed=seed + 12, rot=0.5), M["light"], I, cyclic=True)
    G.stroke(dk, G.lumpy_ellipse(hx, hz, 0.22, 0.19, n=40, lump=0.025, seed=seed + 2, rot=-0.1), M["coat"], O, cyclic=True)
    G.hatch(dk, *R(-0.13, -0.06), M["ink"], n=3, length=0.06, spacing=0.03, angle_deg=100, seed=seed + 13)   # cheek fur
    sn = p["sniff"]
    muz = G.lumpy_ellipse(*R(0.20, -0.07 + 0.01 * sn), 0.13, 0.10, n=28, lump=0.03, seed=seed + 3, rot=-0.15)
    G.stroke(dk, muz, M["light"], O, cyclic=True)
    G.stroke(dk, [q for q in muz if q[1] < hz - 0.09] + [R(0.12, -0.12)], M["light_sh"], 0.0, cyclic=True)
    G.stroke(dk, G.lumpy_ellipse(*R(0.315, -0.025 + 0.015 * sn), 0.05, 0.038, n=16, seed=seed + 6), M["dark"], I, cyclic=True)
    G.seam(dk, [R(0.29, -0.062), R(0.27, -0.09)], M["ink"])                                           # philtrum
    if p["mouth"] > 0.05:
        mo = p["mouth"]
        G.stroke(dk, G.lumpy_ellipse(*R(0.25, -0.12), 0.025 + 0.02 * mo, 0.012 + 0.025 * mo, n=12, seed=seed + 7), M["mouth"], I, cyclic=True)
    else:
        G.seam(dk, G.bezier(R(0.27, -0.105), R(0.22, -0.125), R(0.16, -0.11), n=6), M["ink"])
    G.specks(dk, [R(0.22, -0.05), R(0.235, -0.065), R(0.205, -0.07)], M["ink"])
    eyes(dk, M, *R(0.035, 0.07), 0.030, 0.042, 0.064, p, seed)
    if p["puff"] is not None:
        t = p["puff"]
        puff(d, M, *H([(1.14 + 0.20 * t, 0.86 + 0.05 * t)])[0], 0.06 + 0.06 * min(t, 1.0), seed + 20)
    if p["stars"] is not None:
        stars(dk, M, *R(0.0, 0.33), 0.25, p["stars"])


# ---------------------------------------------------------------- clips (12 fps, on twos)

def idle_common(i, n, amp=1.0):
    ph = TAU * i / n
    return ph, dict(sz=1 + 0.025 * amp * math.cos(ph), bob=0.006 * amp * math.cos(ph))


def walk_legs(ph, A, B_, order=(math.pi, 1.5 * math.pi, 0.0, 0.5 * math.pi)):
    """Lateral-sequence walk (far hind, far front, near hind, near front phases): a foot swings forward
    (and lifts) while cos > 0."""
    return tuple((A * math.sin(ph + f), B_ * max(0.0, math.cos(ph + f))) for f in order)


# One bounding stride in six keys: bob, squash, pitch, hind (dx, lift, fold), front (dx, lift, fold). fold adds knee bend:
# + bows a front knee forward (the hoof tucks back), - flexes a hind hock.
GALLOP = [
    (0.10, 0.92, 0.04, (-0.30, 0.10, 0.00), (0.34, 0.10, 0.00)),     # extension, airborne
    (0.03, 0.96, -0.03, (-0.18, 0.13, -0.25), (0.20, 0.00, 0.00)),   # the front feet land
    (-0.01, 1.03, -0.06, (0.04, 0.12, -0.30), (0.00, 0.00, 0.00)),   # front push, the hind legs swing under
    (0.00, 1.06, 0.00, (0.22, 0.00, -0.05), (-0.16, 0.12, 0.45)),    # gathered: hind lands, the front legs fold
    (0.04, 1.00, 0.05, (0.02, 0.00, 0.00), (0.06, 0.15, 0.35)),      # hind push
    (0.08, 0.95, 0.05, (-0.18, 0.04, 0.00), (0.26, 0.12, 0.12)),     # launch
]


def gallop(t, A=1.0, lz=1.0, lag=0.8):
    """Bounding flee at stride phase t (0..1): legs (far hind, far front, near hind, near front), bob, sz, rock.
    Keys interpolate cyclically; the far pair lags `lag` keys (a rotary gallop's offset)."""
    def at(u):
        u = (u % 1.0) * len(GALLOP)
        a, b = GALLOP[int(u) % len(GALLOP)], GALLOP[(int(u) + 1) % len(GALLOP)]
        f = u - int(u)
        mix = lambda x, y: x + (y - x) * f   # noqa: E731
        return (mix(a[0], b[0]), mix(a[1], b[1]), mix(a[2], b[2]), tuple(mix(x, y) for x, y in zip(a[3], b[3])),
                tuple(mix(x, y) for x, y in zip(a[4], b[4])))
    bob, sz, rock, h, fr = at(t)
    _b, _s, _r, hf, ff = at(t - lag / len(GALLOP))
    leg_ = lambda q: (q[0] * A, q[1] * lz, q[2])   # noqa: E731
    return (leg_(hf), leg_(ff), leg_(h), leg_(fr)), bob * lz, sz, rock


def bump_clip(extra=None):
    """Gus's bump: knocked back with a squash, dizzy stars, a wobble, settle (10 frames)."""
    fr = [dict(sz=0.80, shift=-0.10, lean=-0.10, head=(-0.04, -0.03), eye_pop=1.4, ears=0.7, tail=0.5, mouth=0.5, antler=0.30,
               legs=((0.06, 0.0), (0.10, 0.0), (0.04, 0.0), (0.12, 0.05))),
          dict(sz=0.86, shift=-0.08, lean=-0.07, head=(-0.03, -0.02), ears=0.5, tail=0.4, mouth=0.3, antler=-0.15, stars=0.0),
          dict(sz=1.08, shift=-0.05, head_rot=0.05, ears=-0.2, tail=-0.1, antler=0.12, stars=0.6),
          dict(sz=0.98, shift=-0.03, rock=0.04, head_rot=-0.06, ears=0.3, tail=0.2, antler=-0.08, stars=1.2),
          dict(sz=1.02, shift=-0.02, rock=-0.04, head_rot=0.06, ears=-0.2, tail=-0.2, antler=0.06, stars=1.8),
          dict(sz=0.99, shift=-0.01, rock=0.03, head_rot=-0.05, ears=0.2, tail=0.15, antler=-0.04, stars=2.4),
          dict(sz=1.01, rock=-0.02, head_rot=0.04, ears=-0.15, tail=-0.1, stars=3.0),
          dict(sz=1.0, rock=0.01, head_rot=-0.02, ears=0.1, stars=3.6),
          dict(sz=1.0, blink=1.0, ears=-0.05),
          dict(sz=1.0)]
    if extra:
        for f in fr:
            f.update(extra(f))
    return fr


def stag_poses():
    out = []
    for i in range(10):                                                          # idle: breathe, ears flick, blink
        ph, p = idle_common(i, 10)
        p.update(head_rot=0.03 * math.sin(ph - 0.8), antler=-0.05 * math.sin(ph - 1.6), tail=0.15 * math.sin(ph - 1.0),
                 ears=0.10 * math.sin(ph - 1.2) - (0.35 if i in (3, 4) else 0.0), blink={6: 0.6, 7: 1.0}.get(i, 0.0))
        out.append(p)
    for i in range(12):                                                          # walk
        ph = TAU * i / 12
        out.append(dict(legs=walk_legs(ph, 0.14, 0.08), bob=0.012 * math.cos(2 * ph), sz=1 + 0.02 * math.cos(2 * ph),
                        rock=0.02 * math.sin(ph), head_rot=0.05 * math.sin(2 * ph - 0.5), antler=-0.08 * math.sin(2 * ph - 1.6),
                        ears=0.15 * math.sin(2 * ph - 1.2), tail=0.2 * math.sin(ph), lean=0.02))
    out += [dict(sz=0.95, bob=-0.01, ears=0.2, look=(0.6, -0.2)),                # react: head up, ears swivel, eye-pop
            dict(sz=0.92, bob=-0.02, blink=0.6, ears=0.3),
            dict(sz=1.08, bob=0.02, head_rot=0.18, head=(0.0, 0.04), eye_pop=1.6, mouth=0.6, ears=-0.6, tail=0.9, antler=-0.15),
            dict(sz=1.06, bob=0.015, head_rot=0.20, head=(0.0, 0.04), eye_pop=1.7, mouth=0.7, ears=-0.7, tail=1.0, antler=0.10),
            dict(sz=1.03, head_rot=0.16, head=(0.0, 0.02), eye_pop=1.4, mouth=0.4, ears=-0.5, tail=0.9, antler=-0.05),
            dict(sz=1.0, head_rot=0.12, eye_pop=1.2, ears=-0.4, tail=0.7, look=(0.9, 0.1)),
            dict(sz=1.0, head_rot=0.10, eye_pop=1.05, ears=-0.3, tail=0.5, look=(-0.6, 0.1)),
            dict(sz=1.0, head_rot=0.06, ears=-0.1, tail=0.2)]
    out += bump_clip()
    for i in range(12):                                                          # flee: two bounds, the white flag up
        legs, bob, sz, rock = gallop(i / 6)
        ph = TAU * i / 6
        out.append(dict(legs=legs, bob=bob, sz=sz, rock=rock, lean=0.05, head_rot=-0.10 + 0.05 * math.cos(ph),
                        antler=0.12 * math.sin(ph - 1.2), ears=0.6 + 0.1 * math.sin(TAU * i / 12),
                        tail=1.0 + 0.15 * math.sin(ph - 1.0), look=(0.8, 0.0)))
    return out


def wolf_poses():
    out = []
    for i in range(10):                                                          # idle: breathe, slow tail wag, ear twitch
        ph, p = idle_common(i, 10)
        p.update(head_rot=0.03 * math.sin(ph - 0.8), tail=0.12 + 0.12 * math.sin(ph - 1.0),
                 ears=-0.25 if i in (4, 5) else 0.05 * math.sin(ph), blink={7: 0.6, 8: 1.0}.get(i, 0.0), sniff=1.0 if i in (1, 2) else 0.0)
        out.append(p)
    for i in range(12):
        ph = TAU * i / 12
        out.append(dict(legs=walk_legs(ph, 0.12, 0.06), bob=0.01 * math.cos(2 * ph), sz=1 + 0.02 * math.cos(2 * ph),
                        rock=0.02 * math.sin(ph), head_rot=0.04 * math.sin(2 * ph - 0.5), ears=0.1 * math.sin(2 * ph - 1.2),
                        tail=0.15 + 0.2 * math.sin(ph - 1.0), lean=0.02))
    out += [dict(sz=0.95, ears=0.15, look=(0.7, 0.0)),                           # react: ears up, sniff, a little pop
            dict(sz=0.93, ears=-0.2, head_rot=0.06, sniff=1.0),
            dict(sz=1.06, ears=-0.45, head_rot=0.16, head=(0.0, 0.03), sniff=0.0, eye_pop=1.45, tail=0.45),
            dict(sz=1.05, ears=-0.5, head_rot=0.18, head=(0.0, 0.03), sniff=1.0, eye_pop=1.5, tail=0.55),
            dict(sz=1.03, ears=-0.45, head_rot=0.16, sniff=0.0, eye_pop=1.3, tail=0.5, mouth=0.3),
            dict(sz=1.0, ears=-0.35, head_rot=0.12, sniff=1.0, eye_pop=1.1, tail=0.45, look=(0.9, 0.2)),
            dict(sz=1.0, ears=-0.2, head_rot=0.08, tail=0.4, look=(0.3, 0.0)),
            dict(sz=1.0, ears=0.0, head_rot=0.03, tail=0.3)]
    out += bump_clip()
    for i in range(14):                                                          # flee: two bounds of 7
        legs, bob, sz, rock = gallop(i / 7, A=0.75, lz=0.7)
        ph = TAU * i / 7
        out.append(dict(legs=legs, bob=bob, sz=sz, rock=rock, lean=0.06, head_rot=-0.06 + 0.04 * math.cos(ph), ears=0.55,
                        tail=-0.15 + 0.1 * math.sin(ph - 1.0), look=(0.8, 0.0)))
    for i in range(12):                                                          # follow: a curious nose-down trot, tail wagging high
        ph = TAU * i / 6
        trot = walk_legs(ph, 0.10, 0.07, order=(math.pi, 0.0, 0.0, math.pi))
        out.append(dict(legs=trot, bob=0.012 * abs(math.cos(ph)), sz=1 + 0.02 * math.cos(2 * ph), head_rot=-0.14 + 0.03 * math.sin(2 * ph),
                        head=(0.02, -0.02), sniff=1.0 if i % 4 < 2 else 0.0, ears=-0.15 + 0.08 * math.sin(2 * ph),
                        tail=0.55 + 0.25 * math.sin(TAU * i / 4), lean=0.03, look=(0.8, -0.3)))
    return out


def bear_poses():
    out = []
    for i in range(12):                                                          # idle: breathing sway, head swing, blink
        ph, p = idle_common(i, 12, amp=1.2)
        p.update(shift=0.02 * math.sin(ph), head_rot=0.05 * math.sin(ph - 0.8), head=(0.0, -0.01 + 0.01 * math.cos(ph)),
                 ears=0.0, tail=0.3 * math.sin(ph - 1.0), blink={8: 0.6, 9: 1.0}.get(i, 0.0), sniff=1.0 if i in (3, 4) else 0.0)
        out.append(p)
    for i in range(12):                                                          # walk: a heavy amble, shoulders roll
        ph = TAU * i / 12
        out.append(dict(legs=walk_legs(ph, 0.15, 0.07), bob=0.015 * math.cos(2 * ph), sz=1 + 0.025 * math.cos(2 * ph),
                        rock=0.03 * math.sin(2 * ph), head_rot=-0.04 + 0.04 * math.sin(2 * ph - 0.5), head=(0.0, -0.02),
                        tail=0.3 * math.sin(ph), lean=0.01))
    out += [dict(sz=0.94, bob=-0.02, head_rot=-0.05, look=(0.7, 0.0)),          # react: rear up halfway, sniff, huff, thump
            dict(rock=0.18, front_up=0.6, head_rot=0.04, eye_pop=1.1),
            dict(rock=0.36, front_up=1.0, head_rot=0.12, eye_pop=1.35, sniff=1.0),
            dict(rock=0.40, front_up=1.0, head_rot=0.14, eye_pop=1.3, sniff=0.0),
            dict(rock=0.40, front_up=1.0, head_rot=0.10, eye_pop=1.2, mouth=0.5, puff=0.3, sniff=1.0),
            dict(rock=0.36, front_up=1.0, head_rot=0.08, mouth=0.35, puff=0.8),
            dict(rock=0.16, front_up=0.5, head_rot=0.0, puff=1.3),
            dict(sz=0.86, bob=-0.025, head_rot=-0.06, blink=0.6),
            dict(sz=1.06, bob=0.01, head_rot=0.02),
            dict(sz=1.0)]
    out += bump_clip()
    for i in range(12):                                                          # flee: a bounding lope
        legs, bob, sz, rock = gallop(i / 6, A=0.85, lz=0.7)
        ph = TAU * i / 6
        out.append(dict(legs=legs, bob=bob, sz=1.0 + (sz - 1.0) * 0.8, rock=rock * 0.8, lean=0.04,
                        head_rot=-0.06 + 0.04 * math.cos(ph), tail=0.4, look=(0.8, 0.0)))
    return out


SPECIES = {
    "stag": dict(draw=draw_stag, poses=stag_poses, frame=(192, 176), seed=11,
                 clips=[("idle", 10, True), ("walk", 12, True), ("react", 8, False), ("bump", 10, False), ("flee", 12, True)]),
    "wolf": dict(draw=draw_wolf, poses=wolf_poses, frame=(160, 128), seed=12,
                 clips=[("idle", 10, True), ("walk", 12, True), ("react", 8, False), ("bump", 10, False), ("flee", 14, True),
                        ("follow", 12, True)]),
    "bear": dict(draw=draw_bear, poses=bear_poses, frame=(224, 160), seed=13,
                 clips=[("idle", 12, True), ("walk", 12, True), ("react", 10, False), ("bump", 10, False), ("flee", 12, True)]),
}


def build(name, out=None):
    """The source .blend for one creature (export path, inside Blender)."""
    sp = SPECIES[name]
    out = out or os.path.join(SOURCES, f"earth_{name}_v3.blend")
    scene = G.new_scene()
    coll = G.collection(name)
    ob, gp = G.gp_object(name, coll)
    M = mats(gp, name)
    layer = gp.layers.new("art")
    for f, pose in enumerate(sp["poses"]()):
        sp["draw"](G.drawing(layer, f + 1), M, pose, seed=5 * f)
    G.mark_clips(scene, [(c, n) for c, n, _l in sp["clips"]])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


def build_stag(out=None):                # manifest build_fn: render.py passes the source path
    return build("stag", out)


def build_wolf(out=None):
    return build("wolf", out)


def build_bear(out=None):
    return build("bear", out)


SELF_CHECK = {
    "stag": {"ink": "lumpy bean body, bowed haunch and shoulder seams, chest tufts, flank hatch, hoof splits, antler burrs",
             "motion": "squash 0.92-1.08 on the beat, hose legs, antlers / ears / flag tail drag and overshoot; flee stretches and gathers",
             "original": "our own stag: golden coat, brown mane, off-white flag tail and muzzle; no studio deer, no teeth",
             "style": "built like Gus (B-127): pie eyes in 3/4, hose limbs, mid + deep tones; LEAD judges"},
    "wolf": {"ink": "lumpy body, saddle edge, fur ticks, haunch seam, tail fur strokes, toe seams, muzzle seam",
             "motion": "squash on the beat, hose legs, bushy tail wags and lags, ears flick; follow trots nose-down with the tail high",
             "original": "our own wolf: round grey body, cream bib and ruff, brown tail tip; neutral face, no teeth (D-087)",
             "style": "built like Gus (B-127); LEAD judges"},
    "bear": {"ink": "hump and haunch fur hatch, belly fringe, shoulder seam, toe seams and claws, cheek fur",
             "motion": "breathing sway, heavy hose legs, rear-up with a thump squash 0.86 and a round huff puff; ears and stub tail follow",
             "original": "our own bear: chestnut with a hump, tan muzzle, small oval ears (not round black ears, §9.8), no teeth",
             "style": "built like Gus (B-127); LEAD judges"},
}
OURS = {
    "stag": "a golden stag with a shaggy brown mane, a white flag tail that pops up on alarm and swept antlers that wobble behind every stop",
    "wolf": "a round grey wolf with a cream bib, a cheek ruff and a brown-tipped bushy tail that wags while it trots after you, nose down",
    "bear": "a chestnut bear with a shoulder hump and white claws that rears up halfway to sniff and huffs a round cloud",
}


def entry_for(name):
    """The manifest row of one creature (the preview uses the same dict the export reads)."""
    sp = SPECIES[name]
    return {"key": f"creatures/earth/{name}", "style": "v3", "source": f"sources/creatures/earth_{name}_v3.blend",
            "build": "scripts/build_creatures_earth_v3.py", "build_fn": f"build_{name}", "collection": name,
            "frame": list(sp["frame"]), "pivot": [0.5, 0.0], "facing": "right", "squash_root": True, "planet": "earth",
            "seed": sp["seed"], "beside": "characters/surveyor/side", "review_name": f"b132_earth_{name}",
            "clips": [{"name": c, "frames": n, "loop": lp} for c, n, lp in sp["clips"]],
            "self_check": SELF_CHECK[name], "ours": OURS[name],
            "note": "B-132: v3.1 sheet (D-086/D-100), faces kept (D-101), no bared teeth (D-087)"}


# ---------------------------------------------------------------- lock-free preview (fakegp; same strokes, same rasterizer)

def render_frames(name, ss=2, scale=1):
    """Every frame in sheet order -> (frames RGBA uint8, widths, frames drawing > 2 px below the ground)."""
    sp = SPECIES[name]
    fw, fh = sp["frame"]
    frames, widths, below = [], [], []
    for f, pose in enumerate(sp["poses"]()):
        gp = fakegp.FakeGP()
        M = mats(gp, name)
        d = fakegp.FakeDrawing()
        sp["draw"](d, M, pose, seed=5 * f)
        st = fakegp.strokes_of(d, gp)
        zmin = min(float((s["xz"][:, 1] - s["radius"] * (1 + GR.JITTER)).min()) for s in st)
        if zmin * PPU < -2.0:
            below.append(f)
        img, w = GR.render_frame(st, fw * scale, fh * scale, PPU * scale, (0.5, 0.0), ss=ss, seed=sp["seed"] * 1000 + f + 1)
        frames.append(img)
        widths += [(a / scale, b / scale, c / scale) for a, b, c in w]
    return frames, widths, below


def sheet_of(name, frames):
    """Frames -> the §11.2 sheet + json exactly as render.py's do_v3_sheet packs them, and its problems."""
    import numpy as np
    from meridian import v3
    sp = SPECIES[name]
    fw, fh = sp["frame"]
    cols = v3.columns_for(fw, len(frames))
    rows = -(-len(frames) // cols)
    g = v3.GUTTER
    sheet = np.zeros((rows * fh + (rows - 1) * g, min(cols, len(frames)) * fw + (min(cols, len(frames)) - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw] = im
    clips, s = [], 0
    for c, n, lp in sp["clips"]:
        clips.append({"name": c, "start": s, "length": n, "loop": lp})
        if lp:
            clips[-1]["loop_from"] = 0
        s += n
    meta = {"key": f"creatures/earth/{name}", "style": "v3", "frame_width": fw, "frame_height": fh, "columns": cols,
            "gutter": g, "frames": len(frames), "fps": v3.FPS, "pivot": [0.5, 0.0], "facing": "right", "ppu": PPU,
            "animations": clips, "squash_root": True}
    problems = v3.validate_sheet(meta, sheet.shape)
    m = v3.EDGE_MARGIN
    clipped = [i for i, im in enumerate(frames) if im[:m, :, 3].any() or im[:, :m, 3].any() or im[:, -m:, 3].any()]
    if clipped:
        problems.append(f"frames {clipped[:8]} touch the {m} px frame edge (drawing clipped)")
    return sheet, meta, problems


def preview(out_dir, names=None):
    """Lock-free design previews (D-109): per creature the stamped §11.7 review (review.v3_sheet_review, the export's
    own layout: 1x on the plains beside the surveyor, every clip as a strip, ink zoom, palette, ten boxes) from a
    preview sheet written under <out_dir>/b132/, and review_b132_earth_lineup_preview.png (all three + Gus + the
    surveyor at 1x, key poses at 2x)."""
    import json
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import pngio, v3
    names = names or list(SPECIES)
    firsts = {}
    for name in names:
        frames, widths, below = render_frames(name)
        sheet, meta, problems = sheet_of(name, frames)
        if below:
            problems.append(f"frames {below[:8]} draw more than 2 px below the ground line")
        d = os.path.join(out_dir, "b132")
        os.makedirs(d, exist_ok=True)
        png = os.path.join(d, f"{name}_color.png")
        n = pngio.write_png(png, sheet)
        with open(os.path.join(d, f"{name}.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
        outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
        inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
        rng = lambda ws: (min(w[1] for w in ws), max(w[2] for w in ws)) if ws else (0, 0)   # noqa: E731
        stats = {"outer_px": rng(outer), "inner_px": rng(inner), "inner_n": len(inner), "palette": v3.palette_hits(sheet, "earth"),
                 "problems": problems, "sheet_wh": (sheet.shape[1], sheet.shape[0]), "png_kb": n // 1024}
        out = os.path.join(out_dir, f"review_b132_earth_{name}_preview.png")
        boxes = review.v3_sheet_review(entry_for(name), meta, frames, png, out, stats)
        print(name, f"sheet {sheet.shape[1]}x{sheet.shape[0]} {n // 1024} KB, {len(frames)} frames,",
              f"ink {stats['outer_px'][0]:.2f}-{stats['outer_px'][1]:.2f} / {stats['inner_px'][0]:.2f}-{stats['inner_px'][1]:.2f} px,",
              f"palette {stats['palette'][0] * 100:.1f}% {stats['palette'][1]}, problems {problems or '-'},",
              "boxes not x:", ",".join(k for k, (mk, _n) in boxes.items() if mk != "x") or "-")
        firsts[name] = (frames, meta)
    if len(firsts) == len(SPECIES):
        lineup(out_dir, firsts)
    fakegp.restore()


def lineup(out_dir, firsts):
    """All three at 1x on the plains with Gus and the surveyor (the scale check), then key poses at 2x."""
    import json
    import numpy as np
    import review
    from meridian import pngio
    import preview_c2_earth_rigs as PR
    W = 1600
    rows = []
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, "b-132 earth land creatures v3.1 (faces kept, no teeth): stag, grey wolf, brown bear; lock-free fakegp preview", 6, 8)
    rows.append(head)
    H = 300
    keep, PR.PLAINS_H = PR.PLAINS_H, H
    try:
        scene, note = PR.plains_strip(W)
    finally:
        PR.PLAINS_H = keep
    ground = H - 22
    x = 30
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, x, ground - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
        x += fr.shape[1] - 20
    except Exception:  # noqa: BLE001
        pass
    try:
        gm = json.load(open(os.path.join(PR.ART, "creatures", "earth", "gull.json"), encoding="utf-8"))
        gs = pngio.read_png_np(os.path.join(PR.ART, "creatures", "earth", "gull_color.png"))
        review._over(scene, gs[:gm["frame_height"], :gm["frame_width"]], x, ground - gm["frame_height"])
        x += gm["frame_width"] + 10
    except Exception:  # noqa: BLE001
        pass
    for name in ("wolf", "stag", "bear"):
        frames, meta = firsts[name]
        im = frames[0]
        review._over(scene, im, x, ground - im.shape[0])
        x += im.shape[1] - 20
    review._label(scene, f"1x on the b-114 plains ({note}): the surveyor (2 m), gus, wolf, stag, bear; idle frame 0", 6, 6)
    rows.append(scene)
    for name in ("stag", "wolf", "bear"):
        frames, meta = firsts[name]
        fw, fh = meta["frame_width"], meta["frame_height"]
        picks = []
        for c in meta["animations"]:
            picks += [(c["name"], c["start"]), (c["name"], c["start"] + c["length"] // 2)]
        per = max(1, (W - 16) // (fw * 2 + 8))
        for r0 in range(0, len(picks), per):
            r = np.tile(review.PAPER, (fh * 2 + 24, W, 1)).astype(np.float32)
            for j, (cn, i) in enumerate(picks[r0:r0 + per]):
                xx = 8 + j * (fw * 2 + 8)
                r[20:20 + fh * 2, xx:xx + fw * 2] = review.PAPER * 0.95
                review._over(r, np.repeat(np.repeat(frames[i], 2, 0), 2, 1), xx, 20)
                review._label(r, f"{name} {cn} {i - [a['start'] for a in meta['animations'] if a['name'] == cn][0]} (2x)", xx, 2, scale=1)
            rows.append(r)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " preview (not exported)", 2, img.shape[0] - 16)
    review.write(os.path.join(out_dir, "review_b132_earth_lineup_preview.png"), img)


if __name__ == "__main__":
    preview(sys.argv[1], sys.argv[2].split(",") if len(sys.argv) > 2 else None)
