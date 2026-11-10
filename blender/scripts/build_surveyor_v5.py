"""B-231 (D-185, milestone C5): the v5 surveyor - a DESIGN for the owner's look-over; previews only, no export before it.

v5 (D-185): a modern hand-drawn cartoon. KEPT from v4: hand-drawn / painted (ink + gouache texture, no digital gradients or
3D look), an original character, faces only on people and animals, no combat. CHANGED: jointed limbs (shoulder, elbow, wrist,
hip, knee, ankle) and natural cartoon proportions instead of rubber hoses and pie-cut eyes; painted shading and fabric texture
on the suit; cleaner but still hand-wobbly ink; a RIGGED CUT-OUT (parts + bones) so crouch, bent-knee jumps and head turns
are cheap.

The surveyor keeps v4's identity marks so the player knows them: the big fishbowl helmet, the surveyor's PLUMB BOB on a
springy antenna, the teal MERIDIAN stripe with the compass badge on the off-white suit, the soft-red float pack, white gloves
with mustard cuffs, brown boots. New: an oval-eyed, eyebrowed face (a warm, curious grown-up, not a baby), a mustard hair
tuft, a stitched suit with knee and elbow pads, a belt with a pouch, boot soles with treads.

  Height 2.0 m = 256 px (PPU 128). The rig, per facing (side = profile facing right; front34 = three-quarter front):
    hips (root) -> torso -> head -> antenna;  torso -> pack;  torso -> upper_arm -> forearm -> hand (near f / far b);
    hips -> thigh -> shin -> boot (near f / far b).  Far limbs are the near parts painted one step darker.
  Part sheet: characters/surveyor_v5/rig_color.png (parts on pivots); rig.json: parts (name, rect [x, y, w, h] from the
  bottom-left, pivot), facings (bones: name, part, parent, offset_m from the parent's pivot at rest, rest_deg, length_m,
  order), ik chains (arm, leg) with the bend side, sockets (hand_f grip, helmet top). Angles are degrees counter-clockwise.

  python -I build_surveyor_v5.py <review png>     the lock-free design sheet: turnaround (side, front 3/4), the pose sheet
                                                  (idle, crouch, jump apex with bent knees, dig with the shovel) posed from
                                                  the rig, the part sheet, beside the v4 surveyor at 1x
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio, v3  # noqa: E402
import build_ui_v3 as U  # noqa: E402  (installs fakegp; px canvases, y down)

G = U.G
OUT, INN = G.OUTER * 2.0, G.INNER * 2.0          # round 2 (LEAD 18:0x (1)): the v3 props' weight at the game's zoom, 2.5 px outer /
#                                                   1.25 px inner at 1x = 5 / 2.5 px on the 256 px figure (round 1: 3.5 / 1.75, a
#                                                   line finer than everything around it)
TAU = 2 * math.pi
PX = 128                                          # px per metre (2.0 m = 256 px)
ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
KEY = "characters/surveyor_v5/rig"
PAL = v3.PALETTES["earth"]


def rgb(h):
    return np.array(v3.hex_rgb(h), np.float32) / 255.0


def mixh(a, b, t):
    ca, cb = rgb(a), rgb(b)
    return v3.rgb_hex(tuple(int(round(v)) for v in (ca * (1 - t) + cb * t) * 255))


# the suit's tones (all mixed from the Earth palette)
TONES = {
    "suit": PAL["offwhite"], "suit_sh": mixh(PAL["offwhite"], PAL["sky"], 0.35), "stripe": PAL["teal"],
    "skin": mixh(PAL["offwhite"], PAL["red"], 0.22), "skin_sh": mixh(PAL["offwhite"], PAL["red"], 0.42),
    "cheek": mixh(PAL["offwhite"], PAL["red"], 0.55), "hair": PAL["mustard"], "brow": mixh(PAL["brown"], v3.INK, 0.3),
    "eye": PAL["offwhite"], "iris": mixh(PAL["teal"], v3.INK, 0.35), "pupil": v3.INK, "mouth": mixh(PAL["red"], v3.INK, 0.35),
    "pack": PAL["red"], "pack_sh": mixh(PAL["red"], PAL["brown"], 0.45), "cuff": PAL["mustard"], "brass": PAL["mustard"],
    "glove": PAL["offwhite"], "boot": PAL["brown"], "sole": mixh(PAL["brown"], v3.INK, 0.45), "pad": mixh(PAL["offwhite"], PAL["sky"], 0.55),
    "belt": mixh(PAL["brown"], PAL["mustard"], 0.25), "steel": mixh(PAL["sky"], PAL["offwhite"], 0.25), "glass": PAL["sky"],
    "hose": PAL["teal"], "lead": mixh(PAL["sky"], v3.INK, 0.4),
}


def mats(gp):
    M = {"ink": G.mat(gp, "v5_ink", fill=None)}
    for k, h in TONES.items():
        M[k] = G.mat(gp, f"v5_{k}", fill=h)                      # fill + ink
        M[k + "_f"] = G.mat(gp, f"v5_{k}_f", fill=h, ink=False)   # fill only
    return M


def C(cx, cy, r, n=28, ry=None, a0=0.0, a1=TAU):
    ry = r if ry is None else ry
    closed = abs(a1 - a0 - TAU) < 1e-6
    k = n if closed else n + 1
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(k)]


def hose(pts, w):
    return G.hose_outline(pts, w)


def taper(p0, p1, w0, w1, n=8, bulge=0.0):
    """A limb segment's outline from p0 (width w0) to p1 (width w1), its sides gently bulged (a muscle / padded suit)."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        w = (w0 * (1 - t) + w1 * t) / 2 + bulge * math.sin(math.pi * t)
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        left.append((cx + nx * w, cy + ny * w))
        right.append((cx - nx * w, cy - ny * w))
    capb = C(x1, y1, w1 / 2, 8, a0=math.atan2(ny, nx), a1=math.atan2(ny, nx) - math.pi)
    capa = C(x0, y0, w0 / 2, 8, a0=math.atan2(-ny, -nx), a1=math.atan2(-ny, -nx) - math.pi)
    return left + capb[1:-1] + right[::-1] + capa[1:-1]


# ---------------------------------------------------------------- painted shading (numpy, after the ink render)
def _blur(a, r):
    if r < 1:
        return a
    k = np.ones(2 * r + 1, np.float32) / (2 * r + 1)
    a = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 0, a)
    return np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, a)


LEAN = 0.15           # LEAD's ruling 14:5x: v5 characters are lit FROM ABOVE (the rig mirrors for left / right, so a side light
#                       would swap sides at every turn), leaning at most slightly to the upper LEFT, the side the v3 props and
#                       icons are lit from (they shade right / lower-right). LEAN = the sideways share of the shadow's offset


def _shift(a, dy, dx):
    """a moved dy rows down and dx columns right, zero-filled (np.roll would wrap the far edge back in)."""
    out = np.zeros_like(a)
    h, w = a.shape
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


BACK = 1              # round 2 (LEAD 18:0x (3)): the shadow band lies on each part's lower end and on its BACK edge (+1), the side
#                       that turns under when a limb is raised forward (the jump's thigh, the dig's arms, a walk's swing), so the
#                       band is a true underside in the poses. -1 puts it on the lower RIGHT as the v3 props shade (facing right);
#                       then a raised limb carries its shadow on top. The sheet shows both (the last-but-one row); the rig
#                       mirrors either way
COOL_SHADE = (0.70, 0.77, 0.84)                   # the band's tint (a multiply): a clear cool step on suit, pack and boots
SKIN_SHADE = (0.90, 0.76, 0.72)                   # on skin: one soft warm step


def paint(u8, seed, band=6, glow=0.10, cast=None, soft=False, streak=0.012, grain=0.03, tint=COOL_SHADE, strength=0.8):
    """Gouache shading on a rendered part, lit from above: ONE shadow band on the form's underside, `band` px deep (about
    30 % of the part's width: LEAD 18:0x, visible at the game's zoom), a brushed edge (soft: a soft edge, for skin), a lit
    rim along the top edges, the brush streaks (round 2: a third of round 1's contrast on the suit, none on skin - at 2x
    they read as wood grain) and the paper grain. cast = (row0, row1): a shadow cast across the part there (under the
    helmet's ring, under the belt)."""
    rng = np.random.default_rng(seed)
    f = u8.astype(np.float32) / 255.0
    a = f[..., 3]
    h, w = a.shape
    d = max(2, int(round(band)))
    shade = np.clip(a - _shift(a, -d, BACK * d), 0, 1)                          # the lower end and the back (BACK -1: right) edge
    if cast is not None:
        shade[cast[0]:cast[1]] = np.maximum(shade[cast[0]:cast[1]], a[cast[0]:cast[1]])
    if soft:
        shade = np.clip(_blur(shade, max(2, d // 2)) * 1.3, 0, 1) * a
    else:
        noise = _blur(rng.standard_normal((h, w)).astype(np.float32), 2)
        noise /= max(float(noise.std()), 1e-3)
        shade = np.clip((_blur(shade, 1) - 0.35 + 0.08 * noise) * 3.0, 0, 1) * a   # a brushed edge, one clear shape
    dl = max(1, d // 3)
    lit = np.clip(a - _shift(a, dl, -BACK * max(1, dl // 2)), 0, 1)             # the rim along the top (and front) edges
    lit = np.clip(_blur(lit, 1) * 1.6 - 0.2, 0, 1) * a
    ink = (f[..., :3].max(axis=2) < 0.22)                                       # leave the ink lines dark
    out = f[..., :3].copy()
    k = (strength * shade)[..., None]
    out = out * (1 - k) + out * np.array(tint, np.float32) * k
    out = out + (rgb(PAL["offwhite"]) - out) * (glow * lit)[..., None]
    if streak > 0:
        st = rng.standard_normal((h, w)).astype(np.float32)                     # brush texture: streaks along the rows
        st = np.apply_along_axis(lambda v: np.convolve(v, np.ones(7, np.float32) / 7, mode="same"), 1, st)
        st = (st - st.mean()) / max(float(st.std()), 1e-3)
        out *= (1 + streak * st)[..., None]
    out = np.where(ink[..., None], f[..., :3], out)
    res = np.dstack([np.clip(out, 0, 1), a])
    img = np.clip(np.rint(res * 255), 0, 255).astype(np.uint8)
    return U.paper_grain(img, seed, grain)


# ---------------------------------------------------------------- the parts (px, y down, in their own canvas)
PARTS = {}            # name -> (w, h, pivot (px), draw fn, paint kwargs)


def part(name, w, h, pivot, **kw):
    def reg(fn):
        PARTS[name] = (w, h, pivot, fn, kw)
        return fn
    return reg


def m2p(v):
    return v * PX


# Round 2 (LEAD 18:0x (1), (2)): chunky, still jointed. The round-1 drawings stay in their own coordinates and are widened /
# enlarged in place by xf(), each on a canvas grown to hold it and the heavier line; the joints (pivots, bone lengths, the
# 2.0 m height, the 0.61 m bubble) do not move, so the poses and the crouch's height hold
WIDE = 1.35           # torso, hips and limbs: 35 % wider
BIG = 1.25            # boots and gloves: 25 % larger
HK = 1.2              # the head: 20 % larger in the same bubble (it filled 56 % of the glass; now about 70 %)


def xf(d, cx=0.0, kx=1.0, cy=0.0, ky=1.0, dx=0.0, dy=0.0):
    """The drawing with every point scaled (kx, ky) about (cx, cy), then moved (dx, dy). Line widths are not scaled."""
    return G.Xf(d, lambda pts: [(cx + (x - cx) * kx + dx, cy + (y - cy) * ky + dy) for x, y in pts])


# limb lengths (metres) - the bones use the same numbers. 2.0 m to the helmet's top: legs 0.03 + 0.34 + 0.33 + the boot's
# 0.18, the torso 0.56, the head and helmet 0.55; the hands hang at ~0.64 m (mid thigh)
L_UA, L_FA, L_TH, L_SH = 0.28, 0.26, 0.34, 0.33


@part("upper_arm", 48, 60, (24, 12), band=6)
def upper_arm(d, M):
    d = xf(d, 20, WIDE, dx=4, dy=3)
    G.stroke(d, taper((20, 9), (20, 9 + m2p(L_UA)), 15, 13, bulge=1.5), M["suit"], OUT, cyclic=True)
    G.stroke(d, [(13, 18), (27, 16)], M["ink"], INN)                                               # a seam at the shoulder


@part("forearm", 48, 58, (24, 11), band=5.5)
def forearm(d, M):
    d = xf(d, 20, WIDE, dx=4, dy=4)
    y1 = 7 + m2p(L_FA)
    G.stroke(d, taper((20, 7), (20, y1), 13, 12, bulge=1.0), M["suit"], OUT, cyclic=True)
    G.stroke(d, C(20, 9, 8.5, 14, ry=6.5), M["pad"], INN, cyclic=True)                              # the elbow pad
    G.stroke(d, [(12.5, y1 - 8), (27.5, y1 - 8), (28.5, y1 + 2), (11.5, y1 + 2)], M["cuff"], OUT, cyclic=True)   # mustard cuff


@part("hand", 46, 44, (19, 8), band=5)
def hand(d, M):
    d = xf(d, 16, BIG, 6, BIG, dx=3, dy=2)                                                           # 25 % larger about the wrist
    G.stroke(d, [(10, 4), (22, 4), (25, 14), (26, 23), (21, 29), (12, 29), (8, 22), (8, 12)], M["glove"], OUT, cyclic=True)   # a mitt
    G.stroke(d, hose([(24, 14), (30, 19), (29, 24)], 6.5), M["glove"], INN, cyclic=True)           # the thumb
    for x in (13, 17.5):                                                                              # finger creases
        G.stroke(d, [(x, 21), (x + 0.5, 28)], M["ink"], INN)


@part("thigh", 56, 72, (28, 15), band=8)
def thigh(d, M):
    d = xf(d, 24, WIDE, dx=4, dy=7)
    G.stroke(d, taper((24, 8), (24, 8 + m2p(L_TH)), 20, 16, bulge=2.0), M["suit"], OUT, cyclic=True)
    G.stroke(d, [(31, 18), (32, 40)], M["ink"], INN)                                                 # the side seam


@part("shin", 52, 68, (26, 13), band=6.5)
def shin(d, M):
    d = xf(d, 22, WIDE, dx=4, dy=7)
    y1 = 6 + m2p(L_SH)
    G.stroke(d, taper((22, 6), (22, y1), 16, 13, bulge=1.2), M["suit"], OUT, cyclic=True)
    G.stroke(d, C(24, 9, 9.5, 14, ry=7.5), M["pad"], INN, cyclic=True)                              # the knee pad


# the boot's sole, boot-local metres from the ankle: heel and toe (solve() stands the figure on them). Round 2 enlarges the
# boot 25 % about the point of the sole under the ankle, so the sole keeps its 0.18 m under the joint (the 2.0 m height
# holds), the shaft climbs the shin and the boot grows to heel and toe
SOLE = ((-0.117, -0.18), (0.283, -0.18))


@part("boot", 68, 40, (24, 13), band=6)
def boot(d, M):
    d = xf(d, 20, BIG, 27, BIG, dx=4, dy=9)
    G.stroke(d, [(12, 2), (28, 2), (30, 10), (46, 14), (50, 20), (49, 24), (8, 24), (8, 12)], M["boot"], OUT, cyclic=True)   # the boot
    G.stroke(d, [(7, 22), (50, 22), (49, 27), (8, 27)], M["sole"], INN, cyclic=True)                # the sole
    for x in (14, 22, 30, 38):                                                                       # treads
        G.stroke(d, [(x, 27), (x + 2, 24.5)], M["ink"], INN)
    G.stroke(d, [(11, 4), (29, 4)], M["ink"], INN)                                                   # the cuff line
    G.stroke(d, [(31, 12), (36, 9)], M["ink"], INN)                                                  # a lace


@part("hips", 76, 38, (38, 10), band=8, cast=(14, 19))                                              # (the belt's shadow)
def hips(d, M):
    d = xf(d, 30, WIDE, dx=8, dy=2)
    G.stroke(d, [(9, 4), (51, 4), (54, 18), (48, 30), (12, 30), (6, 18)], M["suit"], OUT, cyclic=True)   # the seat of the suit
    G.stroke(d, [(7, 3), (53, 3), (53, 11), (7, 11)], M["belt"], OUT, cyclic=True)                 # the belt
    G.stroke(d, [(27, 2), (35, 2), (35, 12), (27, 12)], M["brass"], INN, cyclic=True)              # its buckle
    G.stroke(d, [(40, 11), (51, 11), (50, 23), (41, 23)], M["belt"], INN, cyclic=True)            # a pouch


@part("torso", 92, 88, (44, 78), band=16, cast=(13, 21))                                            # (the helmet's shadow on the shoulders)
def torso(d, M):
    ds = xf(d, dx=8 + (44 - 36) * (WIDE - 1), dy=2)                                                  # the badge: round, at its widened place
    d = xf(d, 36, WIDE, dx=8, dy=2)
    body = [(20, 76), (54, 76), (60, 52), (61, 26), (56, 12), (46, 6), (26, 6), (16, 12), (13, 28), (14, 54)]
    G.stroke(d, body, M["suit"], OUT, cyclic=True)                                                   # the chest (pivot: the hips)
    G.stroke(d, [(47, 7), (55, 12), (22, 76), (13, 64), (14, 56)], M["stripe_f"], 0.0, cyclic=True)   # the MERIDIAN stripe
    G.stroke(d, [(47, 7), (14, 56)], M["ink"], INN)
    G.stroke(d, [(55, 12), (22, 76)], M["ink"], INN)
    G.stroke(d, body, M["ink"], OUT, cyclic=True)
    G.stroke(ds, C(44, 36, 8, 16), M["brass"], INN, cyclic=True)                                    # the compass badge
    G.stroke(ds, [(44, 30.5), (45.8, 36), (44, 41.5), (42.2, 36)], M["stripe"], INN * 0.6, cyclic=True)
    G.stroke(d, [(22, 4), (50, 4), (52, 10), (20, 10)], M["steel"], OUT, cyclic=True)              # the helmet's neck ring
    G.stroke(d, [(28, 50), (28, 70)], M["ink"], INN)                                                 # a zip seam


@part("pack", 48, 74, (38, 18), band=8)
def pack(d, M):
    d = xf(d, 30, 1.25, dx=8, dy=2)                                                                  # 25 % deeper behind the wider back
    G.stroke(d, hose([(26, 14), (28, 7), (34, 5)], 5.5), M["hose"], INN, cyclic=True)              # the air hose to the helmet (desk-check: its end was cut by the canvas top)
    G.stroke(d, [(8, 12), (30, 12), (34, 18), (34, 62), (30, 68), (10, 68), (5, 62), (5, 18)], M["pack"], OUT, cyclic=True)   # the float pack
    G.stroke(d, [(7, 46), (33, 46)], M["ink"], INN)                                                  # its lid
    G.stroke(d, [(12, 20), (18, 20), (18, 40), (12, 40)], M["pack_sh"], INN, cyclic=True)        # a vent


# The heads, round 2 (LEAD 18:0x (2), (3), (4)): each round-1 head drawn 20 % larger about its face's centre and 4 px lower, so
# it fills about 70 % of the same 0.61 m bubble with its hair inside the glass; the eye 14 px wide on the 256 px figure
# (7 px at the game's zoom; round 1: 5); clean skin (no streaks), one soft shadow shape, the blush. The side face - what the
# player sees nearly all the time - has a rounded nose, a smile line from the profile, a bold eyebrow, and the ear as a
# small plain C with one fold. The neck stays unscaled on the pivot.
EYE = (48.0, 28.0, 6.0, 7.6)                      # the side head's eye in the round-1 drawing space: centre x, y, radii
EYE34 = ((31.0, 0.9), (47.0, 1.0))                # the front-3/4 head's eyes: centre x, scale (the far one narrower); y 28
E34 = (5.6, 7.4)                                  # ... their radii at scale 1


def _hs(x, y):
    """A point of the side head's round-1 drawing space -> its canvas px."""
    return 38 + (x - 38) * HK - 1, 32 + (y - 32) * HK + 10


def _h34(x, y):
    return 37 + (x - 37) * HK, 32 + (y - 32) * HK + 10


@part("head", 72, 80, (32, 70), band=12, soft=True, streak=0.0, grain=0.012, tint=SKIN_SHADE, strength=0.7)
def head(d, M):
    dn = xf(d, dy=6)
    d = xf(d, 38, HK, 32, HK, dx=-1, dy=10)
    G.stroke(dn, [(30, 56), (46, 56), (44, 64), (32, 64)], M["skin"], INN, cyclic=True)            # the neck (under the chin)
    G.stroke(d, C(38, 32, 22, 32, ry=24), M["skin"], OUT, cyclic=True)                              # the face, in profile
    G.stroke(d, C(60.5, 36, 4.6, 14, ry=4.0), M["skin"], OUT, cyclic=True)                          # a rounded nose (round 1: a
    G.stroke(d, C(57, 36, 5.4, 12, ry=3.0), M["skin_f"], 0.0, cyclic=True)                          # pointed triangle), open into the face
    G.stroke(d, hose([(24, 12), (32, 4), (44, 6), (50, 12)], 9), M["hair"], INN, cyclic=True)      # the hair tuft
    G.stroke(d, hose([(44, 6), (49, 3.5), (53, 6.5)], 5), M["hair"], INN, cyclic=True)              # its cowlick (inside the glass)
    ex, ey, erx, ery = EYE
    G.stroke(d, C(ex, ey, erx, 16, ry=ery), M["eye"], INN, cyclic=True)                             # an oval eye
    G.stroke(d, C(ex + 1.6, ey + 0.8, 4.1, 12, ry=5.3), M["iris_f"], 0.0, cyclic=True)              # a large iris: a soft gaze (at
    G.stroke(d, C(ex + 2.4, ey + 0.6, 2.2, 8), M["pupil_f"], 0.0, cyclic=True)                      # 3.4 px in so much white it stared)
    G.stroke(d, C(ex + 3.8, ey - 1.6, 1.1, 6), M["eye_f"], 0.0, cyclic=True)                        # the catch-light
    G.stroke(d, hose([(41.5, 18), (48, 15.5), (55, 18)], 3.0), M["brow"], 0.0, cyclic=True)         # the eyebrow
    G.stroke(d, C(45.5, 41.5, 4.8, 12, ry=3), M["cheek_f"], 0.0, cyclic=True)                       # the blush
    G.stroke(d, [(56.3, 46.4), (53.5, 47.9), (50, 47.3), (47.2, 44.8)], M["ink"], INN)               # the smile: from the profile
    #                                                                                                 in, its corner turned up
    G.stroke(d, C(28.5, 36.5, 3.6, 10, ry=5.0, a0=math.radians(55), a1=math.radians(305)), M["ink"], INN)   # the ear: a small
    G.stroke(d, [(29.2, 34.8), (28.0, 36.6), (29.4, 38.2)], M["ink"], INN * 0.8)                     # plain C and one fold (round 1's
    #                                                                                                 ring of the eye's size at the eye's
    #                                                                                                 height read as a second, blank eye)


@part("head34", 72, 80, (36, 70), band=12, soft=True, streak=0.0, grain=0.012, tint=SKIN_SHADE, strength=0.7)
def head34(d, M):
    dn = xf(d, dy=6)
    d = xf(d, 37, HK, 32, HK, dy=10)
    G.stroke(dn, [(28, 55), (46, 55), (44, 64), (30, 64)], M["skin"], INN, cyclic=True)            # the neck
    G.stroke(d, C(14, 33, 4, 12, ry=5.5), M["skin"], INN, cyclic=True)                              # the far ear (behind the face)
    G.stroke(d, C(37, 32, 23, 32, ry=24), M["skin"], OUT, cyclic=True)                              # the face, three-quarter
    G.stroke(d, hose([(18, 14), (28, 4), (44, 4), (54, 12)], 10), M["hair"], INN, cyclic=True)
    G.stroke(d, hose([(40, 4), (45.5, 2), (50, 4.5)], 5), M["hair"], INN, cyclic=True)
    for cx, sc in EYE34:                                                                            # two oval eyes
        G.stroke(d, C(cx, 28, E34[0] * sc, 16, ry=E34[1]), M["eye"], INN, cyclic=True)
        G.stroke(d, C(cx + 0.9, 28.8, 3.9 * sc, 12, ry=5.1), M["iris_f"], 0.0, cyclic=True)
        G.stroke(d, C(cx + 1.2, 28.6, 2.0, 8), M["pupil_f"], 0.0, cyclic=True)
        G.stroke(d, C(cx + 2.4, 26.6, 1.1, 6), M["eye_f"], 0.0, cyclic=True)
        G.stroke(d, hose([(cx - 6 * sc, 18.6), (cx, 16.2), (cx + 6 * sc, 18.6)], 3.0), M["brow"], 0.0, cyclic=True)
    G.stroke(d, hose([(40, 33), (43.5, 38), (40, 40.5)], 3.6), M["skin_sh_f"], 0.0, cyclic=True)    # the nose
    G.stroke(d, C(26.5, 40.5, 4.2, 12, ry=2.8), M["cheek_f"], 0.0, cyclic=True)
    G.stroke(d, C(51.5, 40.5, 4.8, 12, ry=3.0), M["cheek_f"], 0.0, cyclic=True)
    G.stroke(d, [(33, 45.5), (39, 48.5), (46, 45.5)], M["ink"], INN)


# The blink (LEAD 14:5x: ONE closed-eye swap part per facing now; the rest of the face-swap set after acceptance): a skin
# patch the size of the open eye and its ink, the closed lid's line on it; shown on the head bone at BLINK's offset
@part("blink", 24, 28, (12, 14))
def blink(d, M):
    G.stroke(d, C(12, 14, EYE[2] * HK + 2.2, 18, ry=EYE[3] * HK + 2.1), M["skin_f"], 0.0, cyclic=True)
    G.stroke(d, C(12, 14.5, 6.4, 8, ry=3.6, a0=math.radians(15), a1=math.radians(165)), M["ink"], INN)   # the lid, bowed down


_GAP34 = (EYE34[1][0] - EYE34[0][0]) * HK         # the two eyes' spacing on the enlarged head (px)


@part("blink34", 40, 28, (20, 14))
def blink34(d, M):
    for cx, sc in ((20 - _GAP34 / 2, EYE34[0][1]), (20 + _GAP34 / 2, EYE34[1][1])):
        G.stroke(d, C(cx, 14, E34[0] * sc * HK + 2.1, 18, ry=E34[1] * HK + 2.0), M["skin_f"], 0.0, cyclic=True)
        G.stroke(d, C(cx, 14.5, 5.6 * sc, 8, ry=3.4, a0=math.radians(15), a1=math.radians(165)), M["ink"], INN)


# the blink's part and its pivot's offset (m) from the head's pivot, per facing: the open eye's centre on the canvas against
# the head's pivot (side: (32, 70); front34: the midpoint of the two eyes against (36, 70))
BLINK = {"side": ("blink", ((_hs(EYE[0], EYE[1])[0] - 32) / PX, (70 - _hs(EYE[0], EYE[1])[1]) / PX)),
         "front34": ("blink34", ((_h34((EYE34[0][0] + EYE34[1][0]) / 2, 28)[0] - 36) / PX, (70 - _h34(0, 28)[1]) / PX))}


@part("helmet", 100, 100, (50, 92), depth=0.0, glow=0.0)
def helmet(d, M):
    G.stroke(d, C(50, 52, 39, 48), M["ink"], OUT, cyclic=True)                                      # the bubble's rim (ink only; the glass
    G.stroke(d, hose(C(50, 52, 37, 20, a0=math.radians(-128), a1=math.radians(-72)), 4.5), M["eye_f"], 0.0, cyclic=True)   # tint is numpy)
    G.stroke(d, hose(C(50, 52, 32, 8, a0=math.radians(-112), a1=math.radians(-92)), 2.5), M["eye_f"], 0.0, cyclic=True)    # glints: on
    #                                                               top of the bubble, a touch to its left (lit from above, LEAD 14:5x)
    G.stroke(d, [(22, 86), (78, 86), (76, 94), (24, 94)], M["steel"], OUT, cyclic=True)            # the seal ring


@part("antenna", 34, 50, (17, 45), band=2)
def antenna(d, M):
    db = xf(d, 15, 1.3, 9, 1.3, dx=2, dy=5)                                                          # the bob 30 % larger (it carries
    d = xf(d, dx=2, dy=5)                                                                            # the heavier line)
    G.stroke(d, hose([(15, 40), (14, 34), (16, 28), (14, 22), (16, 16)], 3.6), M["lead"], INN, cyclic=True)   # a coiled spring stalk
    G.stroke(d, [(15, 16), (15, 13)], M["ink"], INN)
    G.stroke(db, [(9, 4), (21, 4), (15, 14)], M["brass"], OUT, cyclic=True)                         # the brass plumb bob on the spring
    G.stroke(db, C(15, 4, 2.2, 8), M["brass"], INN, cyclic=True)


@part("torso34", 96, 88, (48, 78), band=16, cast=(13, 21))
def torso34(d, M):
    ds = xf(d, dx=8 + (50 - 40) * (WIDE - 1), dy=2)
    d = xf(d, 40, WIDE, dx=8, dy=2)
    body = [(20, 76), (60, 76), (66, 52), (66, 26), (60, 12), (50, 6), (28, 6), (17, 12), (12, 28), (13, 54)]
    G.stroke(d, body, M["suit"], OUT, cyclic=True)
    G.stroke(d, [(50, 6), (60, 12), (28, 76), (18, 72), (16, 64)], M["stripe_f"], 0.0, cyclic=True)
    G.stroke(d, [(50, 6), (16, 64)], M["ink"], INN)
    G.stroke(d, [(60, 12), (28, 76)], M["ink"], INN)
    G.stroke(d, body, M["ink"], OUT, cyclic=True)
    G.stroke(ds, C(50, 38, 8, 16), M["brass"], INN, cyclic=True)
    G.stroke(ds, [(50, 32.5), (51.8, 38), (50, 43.5), (48.2, 38)], M["stripe"], INN * 0.6, cyclic=True)
    G.stroke(d, [(22, 4), (58, 4), (60, 10), (20, 10)], M["steel"], OUT, cyclic=True)
    G.stroke(d, [(40, 46), (40, 72)], M["ink"], INN)


@part("hips34", 80, 38, (40, 10), band=8, cast=(14, 19))
def hips34(d, M):
    d = xf(d, 32, WIDE, dx=8, dy=2)
    G.stroke(d, [(8, 4), (56, 4), (58, 18), (52, 30), (12, 30), (6, 18)], M["suit"], OUT, cyclic=True)
    G.stroke(d, [(6, 3), (58, 3), (58, 11), (6, 11)], M["belt"], OUT, cyclic=True)
    G.stroke(d, [(28, 2), (36, 2), (36, 12), (28, 12)], M["brass"], INN, cyclic=True)
    G.stroke(d, [(43, 11), (54, 11), (53, 23), (44, 23)], M["belt"], INN, cyclic=True)


@part("boot34", 56, 42, (27, 13), band=6)
def boot34(d, M):
    d = xf(d, 22, BIG, 28, BIG, dx=5, dy=9)                                                          # as the boot: about its sole
    G.stroke(d, [(12, 2), (30, 2), (32, 10), (38, 16), (39, 22), (35, 25), (8, 25), (7, 14)], M["boot"], OUT, cyclic=True)
    G.stroke(d, [(6, 23), (40, 23), (39, 28), (7, 28)], M["sole"], INN, cyclic=True)
    G.stroke(d, [(11, 4), (31, 4)], M["ink"], INN)


def render_part(name):
    w, h, pivot, fn, kw = PARTS[name]
    c = U.Canvas(w, h)
    c.M.update(mats(c.gp))
    fn(c.dm, c.M)
    img = c.render(seed=31 + len(name))[0]
    if name == "helmet":                                                       # the glass: a pale sky tint under the rim
        a = np.zeros((h, w), np.float32)
        yy, xx = np.mgrid[0:h, 0:w]
        a[(xx + 0.5 - 50) ** 2 + (yy + 0.5 - 52) ** 2 < 38 ** 2] = 0.16
        f = img.astype(np.float32) / 255.0
        g = np.dstack([np.broadcast_to(rgb(TONES["glass"]), (h, w, 3)), a])
        ia = f[..., 3:4]
        out_a = ia + g[..., 3:4] * (1 - ia)
        out = (f[..., :3] * ia + g[..., :3] * g[..., 3:4] * (1 - ia)) / np.maximum(out_a, 1e-4)
        img = np.clip(np.rint(np.dstack([out, out_a]) * 255), 0, 255).astype(np.uint8)
        return img
    if name.startswith("blink"):                                               # a swap overlay: no form shading (a rim or a
        return U.paper_grain(img, 101 + len(name), 0.012)                      # shade would outline the patch on the face)
    return paint(img, 101 + len(name), **kw)


# ---------------------------------------------------------------- the rig (metres; offsets from the parent's pivot at rest)
def bones(facing):
    """(name, part, parent, offset_m (x, z), rest_deg, length_m, order). Side: facing right; near limbs _f, far _b."""
    if facing == "side":
        T, Hd, Hp, Bt = "torso", "head", "hips", "boot"
        sh_f, sh_b, hp_f, hp_b = (0.0, 0.42), (0.01, 0.42), (0.01, -0.03), (-0.02, -0.03)
        pack_off, head_off = (-0.22, 0.36), (0.02, 0.56)                       # round 2: the pack 0.06 m further back (the wider back)
    else:
        T, Hd, Hp, Bt = "torso34", "head34", "hips34", "boot34"
        sh_f, sh_b, hp_f, hp_b = (0.23, 0.42), (-0.2, 0.43), (0.12, -0.03), (-0.108, -0.03)   # round 2: x 1.35 with the body
        pack_off, head_off = (-0.18, 0.38), (0.0, 0.56)
    return [
        ("hips", Hp, None, (0.0, 0.92), 0.0, 0.0, 12),
        ("torso", T, "hips", (0.0, 0.0), 0.0, 0.56, 8),      # under the near leg (a raised thigh crosses it), the belt over both
        ("pack", "pack", "torso", pack_off, 0.0, 0.0, 4),
        ("head", Hd, "torso", head_off, 0.0, 0.0, 14),
        ("helmet", "helmet", "head", (0.02, -0.06), 0.0, 0.0, 16),
        ("antenna", "antenna", "helmet", (-0.04, 0.615), 0.0, 0.3, 17),    # over the bubble (it lies back across it in crouch);
        #                                                                    round 2: its foot ON the rim's line (0.63 stood it
        #                                                                    above the rim, and the heavier stalk took the crouch
        #                                                                    from 0.97 to 0.98 m)
        ("upper_arm_b", "upper_arm", "torso", sh_b, 0.0, L_UA, 1),
        ("forearm_b", "forearm", "upper_arm_b", (0.0, -L_UA), 0.0, L_FA, 2),
        ("hand_b", "hand", "forearm_b", (0.0, -L_FA), 0.0, 0.12, 3),
        ("thigh_b", "thigh", "hips", hp_b, 0.0, L_TH, 5),
        ("shin_b", "shin", "thigh_b", (0.0, -L_TH), 0.0, L_SH, 6),
        ("boot_b", Bt, "shin_b", (0.0, -L_SH), 0.0, 0.1, 7),
        ("thigh_f", "thigh", "hips", hp_f, 0.0, L_TH, 9),
        ("shin_f", "shin", "thigh_f", (0.0, -L_TH), 0.0, L_SH, 10),
        ("boot_f", Bt, "shin_f", (0.0, -L_SH), 0.0, 0.1, 11),
        ("upper_arm_f", "upper_arm", "torso", sh_f, 0.0, L_UA, 18),
        ("forearm_f", "forearm", "upper_arm_f", (0.0, -L_UA), 0.0, L_FA, 19),
        ("hand_f", "hand", "forearm_f", (0.0, -L_FA), 0.0, 0.12, 20),
    ]


FAR = {"upper_arm_b", "forearm_b", "hand_b", "thigh_b", "shin_b", "boot_b"}

POSES = {   # degrees counter-clockwise, added to rest; "lift" raises the root above the ground solve (m)
    # desk-check 14:3x (forward kinematics by hand; the first set left a foot 6-10 px off the ground in crouch and dig, and the
    # shovel out of both hands' reach): every pose has both soles level (a boot's world angle 0 = flat)
    "idle": {"torso": -2, "head": 3, "upper_arm_f": 8, "forearm_f": 14, "upper_arm_b": -6, "forearm_b": 10,
             "thigh_f": 3, "shin_f": -3, "thigh_b": -3, "shin_b": -2, "boot_b": 5},
    # LEAD 14:4x: the 1 m gap stays (terrain cells are 1 m), so the crouch stands <= 0.98 m: a deep forward tuck (hips 0.36 m,
    # both ankles 0.18 m under the hip joints, the torso 76 deg forward, the helmet leading and tilted with the spine, hands to
    # the ground), the springy antenna pressed back along the helmet, and a root squash of 0.92 (root_scale_z: a per-state root
    # scale about the ground, in the bone JSON's "states" for U-199). By hand: the bubble's top 1.03 m and the antenna's foot
    # 1.04 m unsquashed (the plumb bob 15 deg below level behind it) -> ~0.95 / ~0.96 m; the sheet measures the drawn top and
    # draws the 1 m line
    "crouch": {"torso": -76, "head": 58, "antenna": 123, "upper_arm_f": 45, "forearm_f": 90, "upper_arm_b": 38, "forearm_b": 94,
               "thigh_f": 115, "shin_f": -142, "boot_f": 27, "thigh_b": 95, "shin_b": -152, "boot_b": 57, "root_scale_z": 0.92},
    # the 17:17 sheet: the near arm at 150 crossed the bubble and hid the face (the arms cannot reach over a 0.6 m bubble).
    # Round 2 (LEAD 18:0x (5)): the counter-swing - the near arm forward and up, clear of the glass, the far arm back and down
    "jump": {"torso": -8, "head": 10, "upper_arm_f": 108, "forearm_f": 25, "upper_arm_b": -40, "forearm_b": 20,
             "thigh_f": 78, "shin_f": -96, "boot_f": 18, "thigh_b": 40, "shin_b": -104, "boot_b": 30, "lift": 0.42},
    # a lunge on the shovel: the near hand on the D-grip at (0.33, 0.93) m from the hips' ground point, the shovel 48 deg
    # down (DIG_AIM), its tip ~0.1 m in the ground 1.25 m ahead; the far hand on the haft 0.3 m down it; the back foot on its
    # toe (round 2: 35.8 for 32, the longer boot's toe 0.283 m ahead of the ankle)
    "dig": {"torso": -24, "head": 18, "upper_arm_f": -18.8, "forearm_f": 121.6, "upper_arm_b": 35.3, "forearm_b": 41.3,
            "thigh_f": 40, "shin_f": -52, "boot_f": 12, "thigh_b": -25, "shin_b": -27, "boot_b": 35.8},
    # round 2 (LEAD 18:0x (6)): one walk CONTACT pose - the near heel down ahead (its toe up 14 deg), the far foot behind on
    # its toe (the heel up 22 deg), the arms swung against the legs. By hand: the heel at -0.844 m and the toe at -0.843 m
    # under the hips' pivot
    "walk": {"torso": -4, "head": 4, "upper_arm_f": -24, "forearm_f": 16, "upper_arm_b": 26, "forearm_b": 24,
             "thigh_f": 27, "shin_f": -6, "boot_f": -7, "thigh_b": -20, "shin_b": -28, "boot_b": 26},
}
GRIP = (0.03 * BIG, -0.09 * BIG)                  # the near hand's grip socket (m from the wrist): with the glove, 25 % further
DIG_AIM = -126.8      # the shovel's turn from the near hand's angle (the hand's world angle 78.8 in "dig": 48 deg below level)


def rig_json(parts_rects):
    out = {"key": KEY, "style": "v5", "ppu": PX, "rect_origin": "bottom_left", "height_m": 2.0,
           "note": "B-231 DESIGN (C5): previews only until the owner's look-over (D-185); the contract's v4 rig schema follows it",
           "parts": [{"name": n, "rect": r, "pivot": p} for n, r, p in parts_rects], "facings": []}
    for facing in ("side", "front34"):
        out["facings"].append({
            "name": facing,
            "bones": [{"name": n, "part": p + ("_far" if n in FAR else ""), "parent": par, "offset_m": [round(o[0], 4), round(o[1], 4)], "rest_deg": r,
                       "length_m": L, "order": order, "far": n in FAR} for n, p, par, o, r, L, order in bones(facing)],
            "ik": [{"chain": ["upper_arm_f", "forearm_f"], "effector": "hand_f", "bend": "back"},
                   {"chain": ["upper_arm_b", "forearm_b"], "effector": "hand_b", "bend": "back"},
                   {"chain": ["thigh_f", "shin_f"], "effector": "boot_f", "bend": "forward"},
                   {"chain": ["thigh_b", "shin_b"], "effector": "boot_b", "bend": "forward"}],
            "sockets": {"hand_f_grip": {"bone": "hand_f", "offset_m": [round(GRIP[0], 4), round(GRIP[1], 4)]},
                        "helmet_top": {"bone": "antenna", "offset_m": [0.0, 0.3]}},
            "swaps": {"blink": {"part": BLINK[facing][0], "bone": "head", "offset_m": [round(v, 4) for v in BLINK[facing][1]], "order": 14.5,
                                "note": "shown over the head (under the helmet) while the eyes are closed; hidden otherwise"}}})
    # per state (LEAD 14:4x, for U-199 to read, not guess): the root's scale [x, z] about the ground point (the crouch's 0.92
    # squash), the root's lift, and the design pose in degrees added to each bone's rest angle (side facing)
    out["states"] = {k: {"root_scale": [1.0, v.get("root_scale_z", 1.0)], "lift_m": v.get("lift", 0.0),
                         "pose_deg": {b: a for b, a in v.items() if b not in ("lift", "root_scale_z")}} for k, v in POSES.items()}
    out["states_note"] = ("root_scale is applied to the rig's root about the ground point (z only: a cartoon squash); crouch must stand "
                          "<= 0.98 m under a 1 m gap (the crouch collider is 0.9 m)")
    return out


# ---------------------------------------------------------------- posing (forward kinematics, bilinear placement)
def place(dst, img, pivot, deg, at):
    """Premultiplied float dst; img uint8 straight RGBA drawn with its pivot (px, y down) at `at` (px), turned `deg` CCW."""
    h, w = img.shape[:2]
    f = img.astype(np.float32) / 255.0
    f[..., :3] *= f[..., 3:4]
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
        out = np.zeros(ax.shape + (4,), np.float32)
        out[ok] = f[ay[ok], ax[ok]]
        return out
    smp = (tap(ix, iy) * (1 - fx) * (1 - fy) + tap(ix + 1, iy) * fx * (1 - fy) + tap(ix, iy + 1) * (1 - fx) * fy
           + tap(ix + 1, iy + 1) * fx * fy)
    dst[y0:y1, x0:x1] = smp + dst[y0:y1, x0:x1] * (1 - smp[..., 3:4])


def solve(facing, pose):
    """World (x, z) metres and angle (deg) of every bone, the root dropped so the lower sole touches the ground."""
    B = {b[0]: b for b in bones(facing)}
    world = {}

    def go(name):
        if name in world:
            return world[name]
        n, p, par, off, rest, L, order = B[name]
        a_local = rest + pose.get(name, 0.0)
        if par is None:
            world[name] = (off[0], off[1], a_local)
        else:
            px, pz, pa = go(par)
            t = math.radians(pa)
            world[name] = (px + off[0] * math.cos(t) - off[1] * math.sin(t), pz + off[0] * math.sin(t) + off[1] * math.cos(t), pa + a_local)
        return world[name]
    for n in B:
        go(n)
    soles = []
    for bt in ("boot_f", "boot_b"):
        x, z, a = world[bt]
        t = math.radians(a)
        for ox, oz in SOLE:                                                    # heel and toe of the sole, boot-local
            soles.append(z + ox * math.sin(t) + oz * math.cos(t))
    dz = -min(soles) + pose.get("lift", 0.0)
    return {n: (x, z + dz, a) for n, (x, z, a) in world.items()}


def sole_z(world, boot):
    """The lowest point of a boot's sole (m above the ground) in a solved pose: 0 = standing on it."""
    x, z, a = world[boot]
    t = math.radians(a)
    return min(z + ox * math.sin(t) + oz * math.cos(t) for ox, oz in SOLE)


def squash(img, ground, sz):
    """The state's root scale (z only) about the ground row: the canvas resampled along y (linear), as UNITY's root transform
    will scale the whole rig."""
    if abs(sz - 1.0) < 1e-6:
        return img
    H = img.shape[0]
    ys = ground - (ground - (np.arange(H, dtype=np.float32) + 0.5)) / sz - 0.5      # the source row of each output row
    i0 = np.floor(ys).astype(int)
    f = (ys - i0)[:, None, None]
    a = np.where(((i0 >= 0) & (i0 < H))[:, None, None], img[np.clip(i0, 0, H - 1)], 0.0)
    b = np.where(((i0 + 1 >= 0) & (i0 + 1 < H))[:, None, None], img[np.clip(i0 + 1, 0, H - 1)], 0.0)
    return (a * (1 - f) + b * f).astype(np.float32)


def top_m(img, ground):
    """The posed figure's height (m): its top-most drawn row above the ground row."""
    rows = np.where(img[..., 3].max(axis=1) > 0.02)[0]
    return (ground - rows[0]) / PX if len(rows) else 0.0


def pose_image(P, facing, pose, W=300, H=380, ground=350, cx=150, prop=None, blink=False):
    """One posed figure on a transparent canvas (premultiplied float), the ground line at row `ground`; the pose's
    root_scale_z (the crouch's squash) applied about the ground. blink: the closed-eye swap shown on the head."""
    dst = np.zeros((H, W, 4), np.float32)
    world = solve(facing, pose)
    for n, p, par, off, rest, L, order in sorted(bones(facing), key=lambda b: b[6]):
        if prop is not None and n == "upper_arm_f":                            # the held tool on the near hand's grip socket,
            pimg, ppiv, aim = prop                                             # drawn over the body and the far hand, under the
            x, z, a = world["hand_f"]                                          # near arm (its mitt closes over the D-grip)
            t = math.radians(a)
            gx, gz = x + GRIP[0] * math.cos(t) - GRIP[1] * math.sin(t), z + GRIP[0] * math.sin(t) + GRIP[1] * math.cos(t)
            place(dst, pimg, ppiv, a + aim, (cx + gx * PX, ground - gz * PX))
        img, pivot = P[p + ("_far" if n in FAR else "")]
        x, z, a = world[n]
        place(dst, img, pivot, a, (cx + x * PX, ground - z * PX))
        if blink and n == "head":                                              # the swap, over the head and under the helmet
            bp, (bx, bz) = BLINK[facing]
            t = math.radians(a)
            place(dst, P[bp][0], P[bp][1], a, (cx + (x + bx * math.cos(t) - bz * math.sin(t)) * PX,
                                               ground - (z + bx * math.sin(t) + bz * math.cos(t)) * PX))
    return squash(dst, ground, pose.get("root_scale_z", 1.0))


def all_parts(back=1):
    """Every part rendered and painted. back: paint()'s BACK (the shadow band on the back edge, or -1: on the right)."""
    global BACK
    P = {}
    keep, BACK = BACK, back
    try:
        for name, (w, h, pivot, fn, kw) in PARTS.items():
            img = render_part(name)
            P[name] = (img, pivot)
    finally:
        BACK = keep
    for name in ("upper_arm", "forearm", "hand", "thigh", "shin", "boot", "boot34"):  # the far limbs: one step darker
        img = P[name][0].astype(np.float32) / 255.0
        img[..., :3] = img[..., :3] * 0.8 + (rgb(PAL["sky"]) * 0.55 + rgb(PAL["brown"]) * 0.25) * 0.08
        P[name + "_far"] = (np.clip(np.rint(img * 255), 0, 255).astype(np.uint8), P[name][1])
    return P


def sheet(P):
    """Shelf-pack the parts onto one sheet (2 px gutters) -> (RGBA, [(name, rect bottom-left, pivot normalised)])."""
    names = sorted(P, key=lambda n: -P[n][0].shape[0])
    W, x, y, row_h, placed = 512, 2, 2, 0, []
    for n in names:
        img = P[n][0]
        h, w = img.shape[:2]
        if x + w + 2 > W:
            x, y, row_h = 2, y + row_h + 2, 0
        placed.append((n, x, y, w, h))
        x += w + 2
        row_h = max(row_h, h)
    H = int(math.ceil((y + row_h + 2) / 4.0) * 4)
    out = np.zeros((H, W, 4), np.uint8)
    rects = []
    for n, x, y, w, h in placed:
        out[y:y + h, x:x + w] = P[n][0]
        px, py = P[n][1]
        rects.append((n, [x, H - y - h, w, h], [round(px / w, 4), round(1 - py / h, 4)]))
    return out, rects


# ---------------------------------------------------------------- the design sheet
def preview(out, footnote=None):
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    P = all_parts()
    sh, rects = sheet(P)
    paper = np.array(review.PAPER, np.float32)
    ground_col = rgb(PAL["green"]) * 0.5 + rgb(PAL["brown"]) * 0.5
    shovel = os.path.join(ART, "props", "rig", "shovel_color.png")
    prop = None
    if os.path.isfile(shovel):
        simg = pngio.read_png_np(shovel)
        prop = (simg, (simg.shape[1] * 0.0667, simg.shape[0] * 0.5), DIG_AIM)   # B-226's shovel, pivot at the D-grip (PPU 128, as v5)
    W = 1760                                                                     # (round 2: five poses in the pose row)
    GROUND = 350                                                                 # pose_image's ground row

    def tex(name):
        p = os.path.join(ART, "terrain", "earth", name + "_color.png")
        return pngio.read_png_np(p)[..., :3].astype(np.float32) / 255.0 if os.path.isfile(p) else None

    def tiled(t, hh, ww):
        return np.tile(t, (-(-hh // t.shape[0]), -(-ww // t.shape[1]), 1))[:hh, :ww]

    def strip(cells, label, h=430, bg=None):
        """cells: (name, premultiplied float image, its ground row[, a ceiling in m]): each stands on the strip's ground line; a
        ceiling draws a red line that far above the ground across the cell (the crouch's 1 m gap, LEAD 14:4x). bg = (wall,
        floor) textures: the strip is a dug cell at 1x - the tier's back wall behind the figures, its fill under their feet."""
        r = np.tile(paper, (h, W, 1)).astype(np.float32)
        r[h - 40:h - 36] = ground_col
        if bg is not None and bg[0] is not None:
            r[18:h - 40] = tiled(bg[0], h - 58, W)
            if bg[1] is not None:
                r[h - 40:h] = tiled(bg[1], 40, W)
        review._label(r, label, 6, 4, scale=1)
        x = 10
        for name, img, g, *rest in cells:
            ih, iw = img.shape[:2]
            y = h - 40 - g                                                       # desk-check: the figures floated 28 px over the line
            y0, y1 = max(y, 0), min(y + ih, h)
            a = img[y0 - y:y1 - y, :, 3:4]
            r[y0:y1, x:x + iw] = img[y0 - y:y1 - y, :, :3] + r[y0:y1, x:x + iw] * (1 - a)
            if rest and rest[0]:
                yc = h - 40 - int(round(rest[0] * PX))                           # the line's lower edge = the ceiling
                r[yc - 2:yc, x:x + iw] = rgb(PAL["red"])
                review._label(r, f"{rest[0]:g} m ceiling", x + iw - 96, yc - 16, scale=1)
            review._label(r, name, x + 4, h - 30, scale=1)
            x += iw + 12
        return r
    side = pose_image(P, "side", POSES["idle"])
    turn = [("side, facing right (idle)", side, GROUND), ("the rig mirrored: facing left", side[:, ::-1].copy(), GROUND),
            ("front 3/4 (idle)", pose_image(P, "front34", POSES["idle"]), GROUND)]
    rows = [np.tile(paper, (28, W, 1)).astype(np.float32)]
    review._label(rows[0], "B-231 the v5 surveyor (C5 design, D-185), ROUND 2: a rigged cut-out, jointed limbs, the props' line weight, one cool shadow band a part; 2.0 m = 256 px", 6, 8)
    rows.append(strip(turn, "turnaround (posed from the rig): lit from above, the shadow band on each part's lower end and back edge, so the mirrored rig reads the same"))

    def half(im):
        """The game's zoom: the 256 px drawing at 1/2."""
        return im[:im.shape[0] // 2 * 2, :im.shape[1] // 2 * 2].reshape(im.shape[0] // 2, 2, im.shape[1] // 2, 2, 4).mean(axis=(1, 3))

    def prop1x(name):
        """A v3 camp prop's first frame at 1x (premultiplied float), or None."""
        try:
            import build_title_v3 as TT
            p = TT.prop_frame(name).astype(np.float32).copy()
            p[..., :3] *= p[..., 3:4]
            return p
        except Exception:  # noqa: BLE001  (the row still shows the surveyors)
            return None
    one = []
    v4 = os.path.join(ART, "characters", "surveyor", "side_color.png")
    if os.path.isfile(v4):
        s4 = pngio.read_png_np(v4).astype(np.float32) / 255.0
        f4 = s4[:192, :192].copy()
        f4[..., :3] *= f4[..., 3:4]
        one.append(("v4 surveyor", f4, 192))                                     # its pivot: the frame's bottom row
    one.append(("v5 facing right", half(side), GROUND // 2))
    for pn, label in (("storage_crate", "crate (v3)"), ("smelter", "smelter (v3)")):
        pr = prop1x(pn)
        if pr is not None:
            one.append((label, pr, pr.shape[0]))
    one.append(("v5 facing left", half(side)[:, ::-1].copy(), GROUND // 2))
    rows.append(strip(one, "at the game's zoom (1x): the v4 surveyor, v5 facing right, v3 camp props (lit from the upper left: they shade right / lower-right), v5 facing left", h=290))

    def face(facing, closed):
        """The head at 2x (a 112 px window on the bubble's centre), eyes open or with the blink swap."""
        im = pose_image(P, facing, POSES["idle"], blink=closed)
        hx, hz, ha = solve(facing, POSES["idle"])["helmet"]
        t = math.radians(ha)
        px_ = int(round(150 + (hx - 0.3125 * math.sin(t)) * PX))
        py_ = int(round(GROUND - (hz + 0.3125 * math.cos(t)) * PX))
        return np.repeat(np.repeat(im[max(py_ - 56, 0):py_ + 56, max(px_ - 56, 0):px_ + 56], 2, 0), 2, 1)
    faces = [(f"{fc}: {'the blink swap' if cl else 'eyes open'}", face(fc, cl), None) for fc in ("side", "front34") for cl in (False, True)]
    rows.append(strip([(n, im, im.shape[0]) for n, im, _g in faces], "the face at 2x: eyes open and the ONE blink swap part per facing (the rest of the face set after acceptance)", h=300))
    pimg = {k: pose_image(P, "side", POSES[k]) for k in ("idle", "crouch", "jump")}
    pimg["walk"] = pose_image(P, "side", POSES["walk"], W=340, cx=160)
    pimg["dig"] = pose_image(P, "side", POSES["dig"], W=400, cx=120, prop=prop)                    # (wider: the shovel reaches 1.25 m)
    csz, ctop = POSES["crouch"].get("root_scale_z", 1.0), top_m(pimg["crouch"], GROUND)
    over = f", {100 * (ctop - 1.0):.0f} cm INTO THE 1 m LINE" if ctop > 1.0 else ""
    poses = [("idle", pimg["idle"], GROUND), ("walk (contact)", pimg["walk"], GROUND),
             (f"crouch x{csz:g}: top {ctop:.3f} m{over}", pimg["crouch"], GROUND, 1.0), ("jump", pimg["jump"], GROUND), ("dig", pimg["dig"], GROUND)]
    rows.append(strip(poses, f"pose sheet (side): idle, a walk contact, crouch (a deep tuck under a 1 m gap, root squash {csz:g}, measured top {ctop:.3f} m), jump apex (knees tucked, the counter-swing), dig with B-226's shovel"))
    order = ("idle", "walk", "crouch", "jump", "dig")
    rows.append(strip([(k, half(pimg[k]), GROUND // 2) for k in order],
                      "the same poses at the game's zoom (1x): the shading is baked on each part at rest; the band on the back edge turns under on the jump's raised thigh and the dig's arms", h=260))
    # LEAD 18:0x (6): the surveyor lives in holes - the 1x row inside a dug cell of Subsoil and of Stone (B-230's back wall
    # behind, the tier's fill underfoot); here the far limbs' one-step-darker tone is judged too
    for tname, t in (("Subsoil", 2), ("Stone", 3)):
        cells = [("idle", half(side), GROUND // 2), ("facing left", half(side)[:, ::-1].copy(), GROUND // 2)]
        cells += [(k, half(pimg[k]), GROUND // 2) for k in order[1:]]
        rows.append(strip(cells, f"at the game's zoom (1x) in a dug cell of {tname}: terrain/earth/back_wall_t{t} behind (as exported; the game darkens it further with depth), ground_fill_t{t} underfoot",
                          h=250, bg=(tex(f"back_wall_t{t}"), tex(f"ground_fill_t{t}"))))
    # the band's side, both ways (see BACK): A as drawn in every other row, B on the lower right as the v3 props shade
    PB = all_parts(back=-1)
    alt = [("A idle: the band on the back edge", side, GROUND), ("A jump: it lies under the raised thigh and arm", pimg["jump"], GROUND),
           ("B idle: the band on the lower right", pose_image(PB, "side", POSES["idle"]), GROUND),
           ("B jump: it lies on top of them", pose_image(PB, "side", POSES["jump"]), GROUND)]
    rows.append(strip(alt, "the shadow band's side: A (this sheet) on each part's back edge, B on the lower right as the v3 props are shaded; either mirrors with the rig"))
    for k in order:                                                              # the measured heights, for the sheet's reader
        w_ = solve("side", POSES[k])
        hx, hz, ha = w_["helmet"]
        top = hz + 0.3125 * math.cos(math.radians(ha)) + 0.305
        print(f"{k}: hips {w_['hips'][1]:.2f} m, the bubble's top {top:.2f} m unscaled, drawn top {top_m(pimg[k], GROUND):.3f} m (root scale z "
              f"{POSES[k].get('root_scale_z', 1.0):g}), soles f / b {sole_z(w_, 'boot_f'):+.3f} / {sole_z(w_, 'boot_b'):+.3f} m")
    ps = np.tile(paper, (sh.shape[0] + 30, W, 1)).astype(np.float32)
    review._label(ps, f"the part sheet characters/surveyor_v5/rig_color.png ({sh.shape[1]}x{sh.shape[0]}, {len(rects)} parts on pivots; far limbs a step darker)", 6, 4, scale=1)
    f = sh.astype(np.float32) / 255.0
    ps[24:24 + sh.shape[0], 10:10 + sh.shape[1]] = f[..., :3] * f[..., 3:4] + ps[24:24 + sh.shape[0], 10:10 + sh.shape[1]] * (1 - f[..., 3:4])
    rows.append(ps)
    img = np.vstack(rows)
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-231 design preview (lock-free, fakegp + numpy; not exported)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0], f"| sheet {sh.shape[1]}x{sh.shape[0]}, {len(rects)} parts")
    js = os.path.splitext(out)[0] + "_rig.json"                                  # the bone JSON beside the review (not exported)
    with open(js, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rig_json(rects), fh, indent=1)
        fh.write("\n")
    print("rig json ->", js)


if __name__ == "__main__":                       # python -I build_surveyor_v5.py <review png>
    preview(sys.argv[1])
