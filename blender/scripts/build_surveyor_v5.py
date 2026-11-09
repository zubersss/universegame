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
OUT, INN = G.OUTER * 1.4, G.INNER * 1.4          # v5 ink: ~3.5 px outer / ~1.75 px inner on a 256 px figure
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


def paint(u8, seed, depth=0.2, cool=0.35, glow=0.10, far=False):
    """Gouache shading on a rendered part (light from the upper right): a shadow shape on the lower-left side of the form
    with a ragged brushed edge (no smooth digital ramp), a cool shadow tint, a lit rim on the upper right, a streaky brush
    texture and the paper grain. far: the far-side limb, one step darker and cooler."""
    rng = np.random.default_rng(seed)
    f = u8.astype(np.float32) / 255.0
    a = f[..., 3]
    h, w = a.shape
    d = max(2, int(round(depth * min(h, w))))
    shifted = np.roll(np.roll(a, -d, 0), d, 1)                                  # the shape seen from down-left
    shade = np.clip(a - shifted, 0, 1)
    noise = _blur(rng.standard_normal((h, w)).astype(np.float32), 2)
    noise /= max(float(noise.std()), 1e-3)
    shade = np.clip((_blur(shade, max(1, d // 3)) - 0.35 + 0.18 * noise) * 3.0, 0, 1) * a   # a ragged painted edge
    dl = max(1, d // 3)
    lit = np.clip(a - np.roll(np.roll(a, dl, 0), -dl, 1), 0, 1)                # the rim toward the light
    lit = np.clip(_blur(lit, 1) * 1.6 - 0.2, 0, 1) * a
    ink = (f[..., :3].max(axis=2) < 0.22)                                       # leave the ink lines dark
    sh_col = rgb(PAL["sky"]) * 0.55 + rgb(PAL["brown"]) * 0.25
    out = f[..., :3].copy()
    k = (0.30 * shade)[..., None]
    out = out * (1 - k) + (out * (1 - cool) + sh_col * cool) * k
    out = out + (rgb(PAL["offwhite"]) - out) * (glow * lit)[..., None]
    streak = rng.standard_normal((h, w)).astype(np.float32)                     # brush texture: streaks along a diagonal
    streak = np.apply_along_axis(lambda v: np.convolve(v, np.ones(7, np.float32) / 7, mode="same"), 1, streak)
    streak = (streak - streak.mean()) / max(float(streak.std()), 1e-3)
    out *= (1 + 0.035 * streak)[..., None]
    if far:
        out = out * 0.80 + sh_col * 0.08
    out = np.where(ink[..., None], f[..., :3], out)
    res = np.dstack([np.clip(out, 0, 1), a])
    img = np.clip(np.rint(res * 255), 0, 255).astype(np.uint8)
    return U.paper_grain(img, seed, 0.03)


# ---------------------------------------------------------------- the parts (px, y down, in their own canvas)
PARTS = {}            # name -> (w, h, pivot (px), draw fn, paint kwargs)


def part(name, w, h, pivot, **kw):
    def reg(fn):
        PARTS[name] = (w, h, pivot, fn, kw)
        return fn
    return reg


def m2p(v):
    return v * PX


# limb lengths (metres) - the bones use the same numbers. 2.0 m to the helmet's top: legs 0.03 + 0.34 + 0.33 + the boot's
# 0.18, the torso 0.56, the head and helmet 0.55; the hands hang at ~0.64 m (mid thigh)
L_UA, L_FA, L_TH, L_SH = 0.28, 0.26, 0.34, 0.33


@part("upper_arm", 40, 54, (20, 9), depth=0.25)
def upper_arm(d, M):
    G.stroke(d, taper((20, 9), (20, 9 + m2p(L_UA)), 15, 13, bulge=1.5), M["suit"], OUT, cyclic=True)
    G.stroke(d, [(13, 18), (27, 16)], M["ink"], INN)                                               # a seam at the shoulder


@part("forearm", 40, 50, (20, 7), depth=0.25)
def forearm(d, M):
    y1 = 7 + m2p(L_FA)
    G.stroke(d, taper((20, 7), (20, y1), 13, 12, bulge=1.0), M["suit"], OUT, cyclic=True)
    G.stroke(d, C(20, 9, 8.5, 14, ry=6.5), M["pad"], INN, cyclic=True)                              # the elbow pad
    G.stroke(d, [(12.5, y1 - 8), (27.5, y1 - 8), (28.5, y1 + 2), (11.5, y1 + 2)], M["cuff"], OUT, cyclic=True)   # mustard cuff


@part("hand", 36, 36, (16, 6), depth=0.2)
def hand(d, M):
    G.stroke(d, [(10, 4), (22, 4), (25, 14), (26, 23), (21, 29), (12, 29), (8, 22), (8, 12)], M["glove"], OUT, cyclic=True)   # a mitt
    G.stroke(d, hose([(24, 14), (30, 19), (29, 24)], 6.5), M["glove"], INN, cyclic=True)           # the thumb
    for x in (13, 17.5):                                                                              # finger creases
        G.stroke(d, [(x, 21), (x + 0.5, 28)], M["ink"], INN)


@part("thigh", 48, 62, (24, 8), depth=0.25)
def thigh(d, M):
    G.stroke(d, taper((24, 8), (24, 8 + m2p(L_TH)), 20, 16, bulge=2.0), M["suit"], OUT, cyclic=True)
    G.stroke(d, [(31, 18), (32, 40)], M["ink"], INN)                                                 # the side seam


@part("shin", 44, 58, (22, 6), depth=0.25)
def shin(d, M):
    y1 = 6 + m2p(L_SH)
    G.stroke(d, taper((22, 6), (22, y1), 16, 13, bulge=1.2), M["suit"], OUT, cyclic=True)
    G.stroke(d, C(24, 9, 9.5, 14, ry=7.5), M["pad"], INN, cyclic=True)                              # the knee pad


@part("boot", 52, 30, (20, 4), depth=0.22)
def boot(d, M):
    G.stroke(d, [(12, 2), (28, 2), (30, 10), (46, 14), (50, 20), (49, 24), (8, 24), (8, 12)], M["boot"], OUT, cyclic=True)   # the boot
    G.stroke(d, [(7, 22), (50, 22), (49, 27), (8, 27)], M["sole"], INN, cyclic=True)                # the sole
    for x in (14, 22, 30, 38):                                                                       # treads
        G.stroke(d, [(x, 27), (x + 2, 24.5)], M["ink"], INN)
    G.stroke(d, [(11, 4), (29, 4)], M["ink"], INN)                                                   # the cuff line
    G.stroke(d, [(31, 12), (36, 9)], M["ink"], INN)                                                  # a lace


@part("hips", 60, 34, (30, 8), depth=0.22)
def hips(d, M):
    G.stroke(d, [(9, 4), (51, 4), (54, 18), (48, 30), (12, 30), (6, 18)], M["suit"], OUT, cyclic=True)   # the seat of the suit
    G.stroke(d, [(7, 3), (53, 3), (53, 11), (7, 11)], M["belt"], OUT, cyclic=True)                 # the belt
    G.stroke(d, [(27, 2), (35, 2), (35, 12), (27, 12)], M["brass"], INN, cyclic=True)              # its buckle
    G.stroke(d, [(40, 11), (51, 11), (50, 23), (41, 23)], M["belt"], INN, cyclic=True)            # a pouch


@part("torso", 76, 84, (36, 76), depth=0.2)
def torso(d, M):
    body = [(20, 76), (54, 76), (60, 52), (61, 26), (56, 12), (46, 6), (26, 6), (16, 12), (13, 28), (14, 54)]
    G.stroke(d, body, M["suit"], OUT, cyclic=True)                                                   # the chest (pivot: the hips)
    G.stroke(d, [(47, 7), (55, 12), (22, 76), (13, 64), (14, 56)], M["stripe_f"], 0.0, cyclic=True)   # the MERIDIAN stripe
    G.stroke(d, [(47, 7), (14, 56)], M["ink"], INN)
    G.stroke(d, [(55, 12), (22, 76)], M["ink"], INN)
    G.stroke(d, body, M["ink"], OUT, cyclic=True)
    G.stroke(d, C(44, 36, 7, 16), M["brass"], INN, cyclic=True)                                     # the compass badge
    G.stroke(d, [(44, 31), (45.5, 36), (44, 41), (42.5, 36)], M["stripe"], INN * 0.6, cyclic=True)
    G.stroke(d, [(22, 4), (50, 4), (52, 10), (20, 10)], M["steel"], OUT, cyclic=True)              # the helmet's neck ring
    G.stroke(d, [(28, 50), (28, 70)], M["ink"], INN)                                                 # a zip seam


@part("pack", 40, 72, (30, 16), depth=0.25)
def pack(d, M):
    G.stroke(d, hose([(26, 14), (28, 7), (34, 5)], 5.5), M["hose"], INN, cyclic=True)              # the air hose to the helmet (desk-check: its end was cut by the canvas top)
    G.stroke(d, [(8, 12), (30, 12), (34, 18), (34, 62), (30, 68), (10, 68), (5, 62), (5, 18)], M["pack"], OUT, cyclic=True)   # the float pack
    G.stroke(d, [(7, 46), (33, 46)], M["ink"], INN)                                                  # its lid
    G.stroke(d, [(12, 20), (18, 20), (18, 40), (12, 40)], M["pack_sh"], INN, cyclic=True)        # a vent


@part("head", 72, 76, (32, 68), depth=0.18)
def head(d, M):
    d = G.Xf(d, lambda pts: [(x, y + 4) for x, y in pts])                                           # desk-check: 4 px more headroom (the
    G.stroke(d, C(38, 32, 22, 32, ry=24), M["skin"], OUT, cyclic=True)                              # tuft was cut); the face, in profile
    G.stroke(d, [(55, 30), (63, 35.5), (57, 40)], M["skin"], INN, cyclic=True)                      # the nose
    G.stroke(d, hose([(24, 12), (32, 4), (44, 6), (50, 12)], 9), M["hair"], INN, cyclic=True)      # the hair tuft
    G.stroke(d, hose([(44, 6), (50, 1), (54, 4)], 5), M["hair"], INN, cyclic=True)                  # its cowlick
    G.stroke(d, C(48, 28, 5, 14, ry=6.5), M["eye"], INN, cyclic=True)                               # an oval eye
    G.stroke(d, C(50, 29, 2.8, 10, ry=3.6), M["iris_f"], 0.0, cyclic=True)
    G.stroke(d, C(51, 28, 1.3, 8), M["pupil_f"], 0.0, cyclic=True)
    G.stroke(d, C(52, 26.5, 0.8, 6), M["eye_f"], 0.0, cyclic=True)                                  # the catch-light
    G.stroke(d, hose([(43, 19), (48, 17), (54, 19)], 2.2), M["brow"], 0.0, cyclic=True)             # the eyebrow
    G.stroke(d, C(46, 40, 4.5, 12, ry=3), M["cheek_f"], 0.0, cyclic=True)                           # the cheek
    G.stroke(d, [(50, 45), (54, 47), (58, 45)], M["ink"], INN)                                       # a small smile
    G.stroke(d, C(26, 32, 4.5, 12, ry=6), M["skin"], INN, cyclic=True)                              # the ear
    G.stroke(d, [(30, 56), (46, 56), (44, 64), (32, 64)], M["skin"], INN, cyclic=True)             # the neck


@part("head34", 72, 78, (36, 70), depth=0.18)
def head34(d, M):
    d = G.Xf(d, lambda pts: [(x, y + 6) for x, y in pts])                                           # (6 px more headroom, as head)
    G.stroke(d, C(37, 32, 23, 32, ry=24), M["skin"], OUT, cyclic=True)                              # the face, three-quarter
    G.stroke(d, hose([(18, 14), (28, 4), (44, 4), (54, 12)], 10), M["hair"], INN, cyclic=True)
    G.stroke(d, hose([(40, 4), (46, -1), (51, 2)], 5), M["hair"], INN, cyclic=True)
    for cx, sc in ((31, 0.9), (47, 1.0)):                                                          # two oval eyes (the far one narrower)
        G.stroke(d, C(cx, 28, 4.6 * sc, 14, ry=6.3), M["eye"], INN, cyclic=True)
        G.stroke(d, C(cx + 1.2, 29, 2.6 * sc, 10, ry=3.4), M["iris_f"], 0.0, cyclic=True)
        G.stroke(d, C(cx + 1.4, 28.5, 1.2, 8), M["pupil_f"], 0.0, cyclic=True)
        G.stroke(d, C(cx + 2.2, 27, 0.8, 6), M["eye_f"], 0.0, cyclic=True)
        G.stroke(d, hose([(cx - 5 * sc, 19.5), (cx, 17.5), (cx + 5 * sc, 19.5)], 2.2), M["brow"], 0.0, cyclic=True)
    G.stroke(d, hose([(40, 32), (43, 37), (40, 39)], 3.2), M["skin_sh_f"], 0.0, cyclic=True)        # the nose
    G.stroke(d, C(27, 39, 4, 12, ry=2.6), M["cheek_f"], 0.0, cyclic=True)
    G.stroke(d, C(51, 39, 4.5, 12, ry=2.8), M["cheek_f"], 0.0, cyclic=True)
    G.stroke(d, [(33, 45), (39, 48), (46, 45)], M["ink"], INN)
    G.stroke(d, C(14, 33, 4, 12, ry=5.5), M["skin"], INN, cyclic=True)
    G.stroke(d, [(28, 55), (46, 55), (44, 64), (30, 64)], M["skin"], INN, cyclic=True)


@part("helmet", 100, 100, (50, 92), depth=0.0, glow=0.0)
def helmet(d, M):
    G.stroke(d, C(50, 52, 39, 48), M["ink"], OUT, cyclic=True)                                      # the bubble's rim (ink only; the glass
    G.stroke(d, hose(C(50, 52, 37, 20, a0=math.radians(-75), a1=math.radians(-15)), 4.5), M["eye_f"], 0.0, cyclic=True)   # tint is numpy)
    G.stroke(d, hose(C(50, 52, 32, 8, a0=math.radians(-60), a1=math.radians(-40)), 2.5), M["eye_f"], 0.0, cyclic=True)    # glints
    G.stroke(d, [(22, 86), (78, 86), (76, 94), (24, 94)], M["steel"], OUT, cyclic=True)            # the seal ring


@part("antenna", 30, 44, (15, 40), depth=0.2)
def antenna(d, M):
    G.stroke(d, hose([(15, 40), (14, 34), (16, 28), (14, 22), (16, 16)], 2.6), M["lead"], INN, cyclic=True)   # a coiled spring stalk
    G.stroke(d, [(15, 16), (15, 12)], M["ink"], INN)
    G.stroke(d, [(9, 4), (21, 4), (15, 14)], M["brass"], OUT, cyclic=True)                          # the brass plumb bob on the spring
    G.stroke(d, C(15, 4, 2.2, 8), M["brass"], INN, cyclic=True)


@part("torso34", 80, 84, (40, 76), depth=0.2)
def torso34(d, M):
    body = [(20, 76), (60, 76), (66, 52), (66, 26), (60, 12), (50, 6), (28, 6), (17, 12), (12, 28), (13, 54)]
    G.stroke(d, body, M["suit"], OUT, cyclic=True)
    G.stroke(d, [(50, 6), (60, 12), (28, 76), (18, 72), (16, 64)], M["stripe_f"], 0.0, cyclic=True)
    G.stroke(d, [(50, 6), (16, 64)], M["ink"], INN)
    G.stroke(d, [(60, 12), (28, 76)], M["ink"], INN)
    G.stroke(d, body, M["ink"], OUT, cyclic=True)
    G.stroke(d, C(50, 38, 7, 16), M["brass"], INN, cyclic=True)
    G.stroke(d, [(50, 33), (51.5, 38), (50, 43), (48.5, 38)], M["stripe"], INN * 0.6, cyclic=True)
    G.stroke(d, [(22, 4), (58, 4), (60, 10), (20, 10)], M["steel"], OUT, cyclic=True)
    G.stroke(d, [(40, 46), (40, 72)], M["ink"], INN)


@part("hips34", 64, 34, (32, 8), depth=0.22)
def hips34(d, M):
    G.stroke(d, [(8, 4), (56, 4), (58, 18), (52, 30), (12, 30), (6, 18)], M["suit"], OUT, cyclic=True)
    G.stroke(d, [(6, 3), (58, 3), (58, 11), (6, 11)], M["belt"], OUT, cyclic=True)
    G.stroke(d, [(28, 2), (36, 2), (36, 12), (28, 12)], M["brass"], INN, cyclic=True)
    G.stroke(d, [(43, 11), (54, 11), (53, 23), (44, 23)], M["belt"], INN, cyclic=True)


@part("boot34", 44, 30, (22, 4), depth=0.22)
def boot34(d, M):
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
    return paint(img, 101 + len(name), **{k: v for k, v in kw.items() if k in ("depth", "cool", "glow")})


# ---------------------------------------------------------------- the rig (metres; offsets from the parent's pivot at rest)
def bones(facing):
    """(name, part, parent, offset_m (x, z), rest_deg, length_m, order). Side: facing right; near limbs _f, far _b."""
    if facing == "side":
        T, Hd, Hp, Bt = "torso", "head", "hips", "boot"
        sh_f, sh_b, hp_f, hp_b = (0.0, 0.42), (0.01, 0.42), (0.01, -0.03), (-0.02, -0.03)
        pack_off, head_off = (-0.16, 0.36), (0.02, 0.56)
    else:
        T, Hd, Hp, Bt = "torso34", "head34", "hips34", "boot34"
        sh_f, sh_b, hp_f, hp_b = (0.17, 0.42), (-0.15, 0.43), (0.09, -0.03), (-0.08, -0.03)
        pack_off, head_off = (-0.13, 0.38), (0.0, 0.56)
    return [
        ("hips", Hp, None, (0.0, 0.92), 0.0, 0.0, 12),
        ("torso", T, "hips", (0.0, 0.0), 0.0, 0.56, 8),      # under the near leg (a raised thigh crosses it), the belt over both
        ("pack", "pack", "torso", pack_off, 0.0, 0.0, 4),
        ("head", Hd, "torso", head_off, 0.0, 0.0, 14),
        ("helmet", "helmet", "head", (0.02, -0.06), 0.0, 0.0, 16),
        ("antenna", "antenna", "helmet", (-0.04, 0.63), 0.0, 0.3, 17),     # over the bubble (it lies back across it in crouch)
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
    "jump": {"torso": -8, "head": 10, "upper_arm_f": 150, "forearm_f": 30, "upper_arm_b": 125, "forearm_b": 40,
             "thigh_f": 78, "shin_f": -96, "boot_f": 18, "thigh_b": 40, "shin_b": -104, "boot_b": 30, "lift": 0.42},
    # a lunge on the shovel: the near hand on the D-grip at (0.33, 0.93) m from the hips' ground point, the shovel 48 deg
    # down (DIG_AIM), its tip ~0.1 m in the ground 1.25 m ahead; the far hand on the haft 0.3 m down it; the back foot on its toe
    "dig": {"torso": -24, "head": 18, "upper_arm_f": -18.8, "forearm_f": 121.6, "upper_arm_b": 35.3, "forearm_b": 41.3,
            "thigh_f": 40, "shin_f": -52, "boot_f": 12, "thigh_b": -25, "shin_b": -27, "boot_b": 32},
}
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
            "sockets": {"hand_f_grip": {"bone": "hand_f", "offset_m": [0.03, -0.09]},
                        "helmet_top": {"bone": "antenna", "offset_m": [0.0, 0.3]}}})
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
        for ox, oz in ((-0.09, -0.18), (0.24, -0.18)):                         # heel and toe of the sole, boot-local
            soles.append(z + ox * math.sin(t) + oz * math.cos(t))
    dz = -min(soles) + pose.get("lift", 0.0)
    return {n: (x, z + dz, a) for n, (x, z, a) in world.items()}


def sole_z(world, boot):
    """The lowest point of a boot's sole (m above the ground) in a solved pose: 0 = standing on it."""
    x, z, a = world[boot]
    t = math.radians(a)
    return min(z + ox * math.sin(t) + oz * math.cos(t) for ox, oz in ((-0.09, -0.18), (0.24, -0.18)))


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


def pose_image(P, facing, pose, W=300, H=380, ground=350, cx=150, prop=None):
    """One posed figure on a transparent canvas (premultiplied float), the ground line at row `ground`; the pose's
    root_scale_z (the crouch's squash) applied about the ground."""
    dst = np.zeros((H, W, 4), np.float32)
    world = solve(facing, pose)
    for n, p, par, off, rest, L, order in sorted(bones(facing), key=lambda b: b[6]):
        if prop is not None and n == "upper_arm_f":                            # the held tool on the near hand's grip socket,
            pimg, ppiv, aim = prop                                             # drawn over the body and the far hand, under the
            x, z, a = world["hand_f"]                                          # near arm (its mitt closes over the D-grip)
            t = math.radians(a)
            gx, gz = x + 0.03 * math.cos(t) + 0.09 * math.sin(t), z + 0.03 * math.sin(t) - 0.09 * math.cos(t)
            place(dst, pimg, ppiv, a + aim, (cx + gx * PX, ground - gz * PX))
        img, pivot = P[p + ("_far" if n in FAR else "")]
        x, z, a = world[n]
        place(dst, img, pivot, a, (cx + x * PX, ground - z * PX))
    return squash(dst, ground, pose.get("root_scale_z", 1.0))


def all_parts():
    P = {}
    for name, (w, h, pivot, fn, kw) in PARTS.items():
        img = render_part(name)
        P[name] = (img, pivot)
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
    W = 1560
    GROUND = 350                                                                 # pose_image's ground row

    def strip(cells, label, h=430):
        """cells: (name, premultiplied float image, its ground row[, a ceiling in m]): each stands on the strip's ground line; a
        ceiling draws a red line that far above the ground across the cell (the crouch's 1 m gap, LEAD 14:4x)."""
        r = np.tile(paper, (h, W, 1)).astype(np.float32)
        r[h - 40:h - 36] = ground_col
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
    turn = [("side (idle)", pose_image(P, "side", POSES["idle"]), GROUND), ("front 3/4 (idle)", pose_image(P, "front34", POSES["idle"]), GROUND)]
    v4 = os.path.join(ART, "characters", "surveyor", "side_color.png")
    if os.path.isfile(v4):
        s4 = pngio.read_png_np(v4).astype(np.float32) / 255.0
        f4 = s4[:192, :192].copy()
        f4[..., :3] *= f4[..., 3:4]
        turn.append(("v4 surveyor at 1x (128 px tall)", f4, 192))                # its pivot: the frame's bottom row
        side = pose_image(P, "side", POSES["idle"])
        half = side[:side.shape[0] // 2 * 2, :side.shape[1] // 2 * 2].reshape(side.shape[0] // 2, 2, side.shape[1] // 2, 2, 4).mean(axis=(1, 3))
        turn.append(("v5 at the v4's height (1/2)", half, GROUND // 2))
    rows = [np.tile(paper, (28, W, 1)).astype(np.float32)]
    review._label(rows[0], "B-231 the v5 surveyor (C5 design, D-185): a rigged cut-out, jointed limbs, painted shading; 2.0 m = 256 px", 6, 8)
    rows.append(strip(turn, "turnaround (posed from the rig) beside the v4 surveyor"))
    pimg = {k: pose_image(P, "side", POSES[k]) for k in ("idle", "crouch", "jump")}
    pimg["dig"] = pose_image(P, "side", POSES["dig"], W=400, cx=120, prop=prop)                    # (wider: the shovel reaches 1.25 m)
    csz, ctop = POSES["crouch"].get("root_scale_z", 1.0), top_m(pimg["crouch"], GROUND)
    over = f", {100 * (ctop - 1.0):.0f} cm INTO THE 1 m LINE" if ctop > 1.0 else ""
    poses = [("idle", pimg["idle"], GROUND), (f"crouch x{csz:g}: top {ctop:.2f} m{over}", pimg["crouch"], GROUND, 1.0),
             ("jump", pimg["jump"], GROUND), ("dig", pimg["dig"], GROUND)]
    rows.append(strip(poses, f"pose sheet (side): idle, crouch (a deep tuck under a 1 m gap, root squash {csz:g}, measured top {ctop:.2f} m), jump apex (knees tucked, arms up), dig with B-226's shovel"))
    for k in ("idle", "crouch", "jump", "dig"):                                  # the measured heights, for the sheet's reader
        w_ = solve("side", POSES[k])
        hx, hz, ha = w_["helmet"]
        top = hz + 0.3125 * math.cos(math.radians(ha)) + 0.305
        print(f"{k}: hips {w_['hips'][1]:.2f} m, the bubble's top {top:.2f} m unscaled, drawn top {top_m(pimg[k], GROUND):.2f} m (root scale z "
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
