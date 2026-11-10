"""B-231 (D-185, milestone C5): the v5 surveyor - a DESIGN for the owner's look-over; previews only, no export before it.

ROUND 3, in ART v6 "cel on painted" (D-198 + D-199, docs/STYLE_V6.md). The owner on round 2b: "Polish up the surveyor a
bit more than that. I want fine lines that don't render into pixels." (D-198), then: the art style of a 1960s cel film
(D-199): everything that acts is a CEL - a charcoal pencil line and flat paint. The design, the proportions, the face
and the bones STAND (no joint, pivot, length or pose changed). What changed:
  - every part is drawn at K = 4 times the round-2 size: 512 px per metre (2.0 m = 1024 px). In play it is only ever
    shrunk; every plate of the sheet is the large drawing shrunk by block means, none enlarges a pixel.
  - the LINE is a pencil line (cel_v6.py): dark charcoal everywhere, pressure in it (about 40 % thicker and thinner along
    a stroke), tapered ends, a slightly dry edge, outlines that may stop short of closing; mean 1.5 px at the game's
    zoom (round 2b: a 2.5 px ink outline). FEWER lines than round 2: a line where a form turns or overlaps, a few
    flicks for folds and hair; no stitching, no treads, no ticks.
  - the PAINT is flat: one colour an area, no texture, no grain, no gradient; at most ONE flat shadow shape per form
    (a step darker, a clean edge); colour patches meet their form with no line (the MERIDIAN stripe, the pack's straps
    and dial, the buckles, the blush); the glass is a flat tint with one flat highlight shape.
  - kept from LEAD's round-3 list: the joint cuffs (flat round shapes ON the elbow and knee pivots, so they hide the
    cut-out seam at every pose), clear gloves (fingers, thumb, a cuff line), the boots' sole line, the pack's straps
    and dial.
  - a second LINE pass over the same paint (boil = 1): the 12 Hz boil of STYLE_V6 2.6; the sheet prints what it costs.

v5 (D-185): KEPT from v4: an original character, faces only on people and animals, no combat. CHANGED: jointed limbs
(shoulder, elbow, wrist, hip, knee, ankle) and natural cartoon proportions instead of rubber hoses and pie-cut eyes; a
RIGGED CUT-OUT (parts + bones) so crouch, bent-knee jumps and head turns are cheap.

The surveyor keeps v4's identity marks so the player knows them: the big fishbowl helmet, the surveyor's PLUMB BOB on a
springy antenna, the teal MERIDIAN stripe with the compass badge on the off-white suit, the soft-red float pack, white
gloves with mustard cuffs, brown boots.

  The rig, per facing (side = profile facing right; front34 = three-quarter front):
    hips (root) -> torso -> head -> antenna;  torso -> pack;  torso -> upper_arm -> forearm -> hand (near f / far b);
    hips -> thigh -> shin -> boot (near f / far b).  Far limbs are the near parts with their paint re-keyed one step
    darker (the pencil line is the same).
  Part sheet: characters/surveyor_v5/rig_color.png (parts on pivots, 512 px per metre); rig.json: parts (name, rect [x, y,
  w, h] from the bottom-left, pivot), facings (bones: name, part, parent, offset_m from the parent's pivot at rest,
  rest_deg, length_m, order), ik chains (arm, leg) with the bend side, sockets (hand_f grip, helmet top). Angles are
  degrees counter-clockwise.

  python -I build_surveyor_v5.py <review png>     the lock-free design sheet (round 3's plates)
  export(art) / keys()                            (written and NOT YET RUN) render.py's kit path, for the owner's yes
                                                  only: the manifest row {"key": KEY, "kit_set": true, "generator":
                                                  "scripts/build_surveyor_v5.py", "numpy_only": true, "review_name":
                                                  "b231_surveyor_v5"} is added at that moment, not before
"""
import json
import math
import os
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import pngio, v3  # noqa: E402
import cel_v6 as CEL  # noqa: E402  (installs fakegp; design px canvases, y down)

G = CEL.G
S, P_, F, C, hose, taper = CEL.S, CEL.P, CEL.F, CEL.C, CEL.hose, CEL.taper
K = 4                                             # the parts are rendered K times the design size (512 px per metre)
OUT = CEL.LINE                                    # a contour's nominal radius (the pencil: cel_v6.py)
TAU = 2 * math.pi
PX = 128                                          # design px per metre (2.0 m = 256 px); the large drawing is PX * K
ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
KEY = "characters/surveyor_v5/rig"
PAL = v3.PALETTES["earth"]


def rgb(h):
    return np.array(v3.hex_rgb(h), np.float32) / 255.0


def mixh(a, b, t):
    ca, cb = rgb(a), rgb(b)
    return v3.rgb_hex(tuple(int(round(v)) for v in (ca * (1 - t) + cb * t) * 255))


# the cel's paints (all mixed from the Earth palette; STYLE_V6 2.5: mid-value and a little warm, so the figure reads as
# one clear shape against a painting)
TONES = {
    "suit": mixh(PAL["offwhite"], PAL["brown"], 0.05), "stripe": PAL["teal"],
    "skin": mixh(PAL["offwhite"], PAL["red"], 0.22), "skin_sh": mixh(PAL["offwhite"], PAL["red"], 0.40),
    "cheek": mixh(PAL["offwhite"], PAL["red"], 0.50), "hair": PAL["mustard"], "brow": mixh(PAL["brown"], v3.INK, 0.3),
    "eye": PAL["offwhite"], "iris": mixh(PAL["teal"], v3.INK, 0.35), "pupil": v3.INK,
    "pack": PAL["red"], "cuff": PAL["mustard"], "brass": PAL["mustard"],
    "glove": PAL["offwhite"], "boot": PAL["brown"], "sole": mixh(PAL["brown"], v3.INK, 0.45),
    "belt": mixh(PAL["brown"], PAL["mustard"], 0.25), "steel": mixh(PAL["sky"], PAL["offwhite"], 0.25),
    "hose": PAL["teal"], "joint": mixh(PAL["sky"], PAL["brown"], 0.30),
}
FAR_KEY = (0.8, (rgb(PAL["sky"]) * 0.55 + rgb(PAL["brown"]) * 0.25) * 0.08)     # the far limbs' paint: one step darker


def mats(gp):
    """Per tone: flat paint under a pencil line, and _f the paint alone (a patch: a paint edge, no line). ln = the
    pencil alone; glass = the bubble's flat tint; glint = its one flat highlight."""
    M = {"ln": CEL.mat(gp, "v6_ln"),
         "glass": CEL.mat(gp, "v6_glass", fill=PAL["sky"], line=False, alpha=0.22),
         "glint": CEL.mat(gp, "v6_glint", fill=PAL["offwhite"], line=False, alpha=0.62)}
    for k, h in TONES.items():
        M[k] = CEL.mat(gp, f"v6_{k}", fill=h)
        M[k + "_f"] = CEL.mat(gp, f"v6_{k}_f", fill=h, line=False)
    return M


# ---------------------------------------------------------------- the parts (design px, y down, in their own canvas)
PARTS = {}            # name -> (w, h, pivot (px), draw fn, band): design px; band = the flat shadow shape's depth (0: none)
BACK = 1              # the shadow shape lies on each part's lower end and on its BACK edge (+1), the side that turns under
#                       when a limb is raised forward. LEAD's ruling 11-09 14:5x: v5 characters are lit FROM ABOVE


def part(name, w, h, pivot, band=0):
    def reg(fn):
        PARTS[name] = (w, h, pivot, fn, band)
        return fn
    return reg


def m2p(v):
    return v * PX


# Round 2 (LEAD 11-09 18:0x (1), (2)): chunky, still jointed. The round-1 drawings stay in their own coordinates and are
# widened / enlarged in place by xf(), each on a canvas grown to hold it; the joints (pivots, bone lengths, the 2.0 m
# height, the 0.61 m bubble) do not move, so the poses and the crouch's height hold. Round 3 keeps all of it.
WIDE = 1.35           # torso, hips and limbs: 35 % wider
BIG = 1.25            # boots and gloves: 25 % larger
HK = 1.2              # the head: 20 % larger in the same bubble


def xf(d, cx=0.0, kx=1.0, cy=0.0, ky=1.0, dx=0.0, dy=0.0):
    """The drawing with every point scaled (kx, ky) about (cx, cy), then moved (dx, dy). Line widths are not scaled."""
    return G.Xf(d, lambda pts: [(cx + (x - cx) * kx + dx, cy + (y - cy) * ky + dy) for x, y in pts])


# limb lengths (metres) - the bones use the same numbers. 2.0 m to the helmet's top: legs 0.03 + 0.34 + 0.33 + the boot's
# 0.18, the torso 0.56, the head and helmet 0.55; the hands hang at ~0.64 m (mid thigh)
L_UA, L_FA, L_TH, L_SH = 0.28, 0.26, 0.34, 0.33


# Round 4 (LEAD 11-10 07:1x (5), (6), (7)). NO shadow band on the limbs and small parts (the same band on every part read
# as a bevel): a flat shadow shape only where it models something (the torso under the helmet, the pack's underside; the
# far limbs a step darker). THE JOINTS: a lower limb's paint runs up under the joint and its LINE is left open across it,
# so no line crosses the limb where it bends (how a drawn figure bends); JOINT = "band" lays a slim ribbed band over the
# elbow and the knee, "none" leaves the two shapes overlapping with one fold flick (the sheet shows both).
JOINT = "band"


def limb(d, M, p0, p1, w0, w1, bulge, tone="suit"):
    """A limb segment below a joint: its paint (the cap at the joint a little inside the upper segment's line), and its
    line down one side, round the far end and back up - open across the joint."""
    P_(d, taper(p0, p1, w0, w1, bulge=bulge, cap0=1.5), M[tone + "_f"], under=False)
    S(d, taper(p0, p1, w0, w1, bulge=bulge)[:15 + 9 + 15], M["ln"], OUT, ends=(3, 3))


@part("upper_arm", 48, 60, (24, 12))
def upper_arm(d, M):
    d = xf(d, 20, WIDE, dx=4, dy=3)
    y1 = 9 + m2p(L_UA)
    S(d, taper((20, 9), (20, y1), 15, 13, bulge=1.5), M["suit"], OUT, cyclic=True)
    F(d, M, [(14.6, y1 - 8.4), (18, y1 - 6.4), (22, y1 - 7)])                                        # one fold above the elbow


@part("forearm", 48, 58, (24, 11))
def forearm(d, M):
    d = xf(d, 20, WIDE, dx=4, dy=4)
    y1 = 7 + m2p(L_FA)
    limb(d, M, (20, 7), (20, y1), 13, 12, 1.0)
    if JOINT == "band":                                                                              # the elbow: a slim band,
        S(d, [(11.6, 4.2), (28.4, 4.2), (28.4, 10.8), (11.6, 10.8)], M["joint"], OUT * 0.85, cyclic=True, rnd=3, gap=0)   # two rib ticks
        for x in (17.4, 22.6):
            F(d, M, [(x, 5.6), (x, 9.4)], 0.7, ends=(1, 1))
    else:
        F(d, M, [(15.4, 9.6), (18.6, 11.4), (22.4, 11)])                                             # ... or one fold flick
    S(d, [(12.3, y1 - 8.5), (27.7, y1 - 8.5), (28.6, y1 + 2), (11.4, y1 + 2)], M["cuff"], OUT, cyclic=True, rnd=2.5)   # the wrist cuff


@part("hand", 46, 44, (19, 8))
def hand(d, M):
    d = xf(d, 16, BIG, 6, BIG, dx=3, dy=2)                                                           # 25 % larger about the wrist
    for x in (11.4, 16.3, 21.2):                                                                      # three fingers, a little curled
        S(d, hose([(x, 17), (x + 0.3, 24), (x - 0.5, 28.2)], 5.4), M["glove"], OUT * 0.8, cyclic=True, gap=0)
    S(d, [(10, 4), (22, 4), (25.4, 12), (25.6, 20.5), (17, 22.5), (8.4, 20.5), (8, 12)], M["glove"], OUT, cyclic=True, rnd=4)   # the back of the hand
    S(d, hose([(23.6, 13), (29.6, 18), (29, 24.2)], 6.2), M["glove"], OUT * 0.8, cyclic=True, gap=0)   # the thumb
    F(d, M, [(8.4, 8.4), (16, 9.4), (23.8, 8.4)])                                                    # the glove's cuff: one line
    F(d, M, [(10.4, 18.4), (14, 20), (18.6, 19.6)], 0.6, ends=(2.5, 3.5))                            # the knuckles: one light crease
    #                                                     (run 6's short tick read as a dot in the palm)


@part("thigh", 56, 72, (28, 15))
def thigh(d, M):
    d = xf(d, 24, WIDE, dx=4, dy=7)
    y1 = 8 + m2p(L_TH)
    S(d, taper((24, 8), (24, y1), 20, 16, bulge=2.0), M["suit"], OUT, cyclic=True)
    F(d, M, [(16.5, y1 - 8.5), (20.5, y1 - 6.6), (25, y1 - 7.4)])                                    # one fold above the knee


@part("shin", 52, 68, (26, 13))
def shin(d, M):
    d = xf(d, 22, WIDE, dx=4, dy=7)
    y1 = 6 + m2p(L_SH)
    limb(d, M, (22, 6), (22, y1), 16, 13, 1.2)
    if JOINT == "band":                                                                              # the knee: a slim band
        S(d, [(11.8, 3.0), (32.6, 3.0), (32.6, 10.4), (11.8, 10.4)], M["joint"], OUT * 0.85, cyclic=True, rnd=3.4, gap=0)
        for x in (19.0, 25.4):
            F(d, M, [(x, 4.6), (x, 8.8)], 0.7, ends=(1, 1))
    else:
        F(d, M, [(16.6, 9.4), (20.4, 11.4), (24.6, 10.8)])
    F(d, M, [(15.6, 19.4), (19.5, 21.4), (24, 20.6)])                                                # one fold below the knee


# the boot's sole, boot-local metres from the ankle: heel and toe (solve() stands the figure on them). Round 2 enlarges the
# boot 25 % about the point of the sole under the ankle, so the sole keeps its 0.18 m under the joint (the 2.0 m height holds)
SOLE = ((-0.117, -0.18), (0.283, -0.18))


@part("boot", 68, 40, (24, 13))
def boot(d, M):
    d = xf(d, 20, BIG, 27, BIG, dx=4, dy=9)
    S(d, [(12, 2), (28, 2), (30, 10), (40, 12.4), (47, 15), (50.4, 20), (49.4, 24), (8, 24), (8, 12)], M["boot"], OUT, cyclic=True, rnd=4)
    S(d, [(7, 22), (50.4, 22), (49.6, 27), (8, 27)], M["sole"], OUT * 0.9, cyclic=True, rnd=2)      # the sole; its top edge is the sole line
    F(d, M, [(10.8, 6.4), (20, 7.3), (29.4, 6.4)])                                                   # the turned cuff: one line


@part("hips", 76, 38, (38, 10))
def hips(d, M):
    d = xf(d, 30, WIDE, dx=8, dy=2)
    S(d, [(9, 4), (51, 4), (54, 18), (48, 30), (30, 31.5), (12, 30), (6, 18)], M["suit"], OUT, cyclic=True, rnd=8)   # the seat of the suit
    S(d, [(7, 3), (53, 3), (53, 11), (7, 11)], M["belt"], OUT, cyclic=True, rnd=1.5)                # the belt
    S(d, [(40, 10), (51, 10), (50.4, 23), (41, 23)], M["belt"], OUT * 0.85, cyclic=True, rnd=2, gap=0)   # a pouch
    F(d, M, [(40.6, 15.6), (45.6, 17.4), (50.6, 15.6)], 0.9)                                         # its flap
    P_(d, [(26.6, 1.6), (35.4, 1.6), (35.4, 12.4), (26.6, 12.4)], M["brass_f"], rnd=1.2, under=False)   # the buckle: a flat shape


def _torso(d, ds, M, body, stripe, zx, bx, by):
    """The chest, side and three-quarter: the suit, the MERIDIAN stripe as a paint patch (no line round it), the
    compass badge, the zip and two folds."""
    S(d, body, M["suit"], OUT, cyclic=True, rnd=9, keep="body")
    P_(d, stripe, M["stripe_f"], sharp=True, clip="body")
    x0, x1 = min(p[0] for p in body), max(p[0] for p in body)                                        # the ONE shadow shape: the
    P_(d, [(x0 - 2, 9), (x1 + 2, 9), (x1 + 1, 16), (x1 - 9, 20.5), ((x0 + x1) / 2, 22), (x0 + 9, 20.5), (x0 - 1, 16)],   # helmet's, across
       M["suit_f"], rnd=4, clip="body", shade=True)                                                  # the shoulders (flat, clean)
    F(d, M, [(zx, 50), (zx + 0.3, 60), (zx, 69)])                                                    # the zip
    F(d, M, [(17, 60), (21, 63), (25, 62.4)], 0.9)                                                   # a fold at the waist (run 3 had
    #                                                     one more under the arm: beside the badge it read as a lash on an eye)
    S(ds, C(bx, by, 8, 28), M["brass"], OUT * 0.8, cyclic=True, gap=0)                              # the compass badge
    # its compass rose: a flat four-pointed star (run 2's single upright needle on a brass disc read as a cat's eye)
    P_(ds, [(bx, by - 5.8), (bx + 1.3, by - 1.3), (bx + 4.4, by), (bx + 1.3, by + 1.3), (bx, by + 5.8), (bx - 1.3, by + 1.3),
            (bx - 4.4, by), (bx - 1.3, by - 1.3)], M["stripe_f"], sharp=True)


@part("torso", 92, 88, (44, 78))
def torso(d, M):
    ds = xf(d, dx=8 + (44 - 36) * (WIDE - 1), dy=2)                                                  # the badge: round, at its widened place
    d = xf(d, 36, WIDE, dx=8, dy=2)
    body = [(20, 76), (54, 76), (60, 52), (61, 26), (56, 12), (46, 6), (26, 6), (16, 12), (13, 28), (14, 54)]
    _torso(d, ds, M, body, [(46.6, 5.6), (56.4, 11.6), (22.6, 77), (13.2, 64.4), (13.6, 56.6)], 28, 44, 36)
    S(d, [(22, 4), (50, 4), (52, 10), (20, 10)], M["steel"], OUT, cyclic=True, rnd=2)               # the helmet's neck ring


@part("pack", 48, 74, (38, 18))
def pack(d, M):
    d = xf(d, 30, 1.25, dx=8, dy=2)                                                                  # 25 % deeper behind the wider back
    S(d, hose([(26, 14), (28, 7), (34, 5)], 5.5), M["hose"], OUT * 0.8, cyclic=True, gap=0)         # the air hose to the helmet
    S(d, [(8, 12), (30, 12), (34, 18), (34, 62), (30, 68), (10, 68), (5, 62), (5, 18)], M["pack"], OUT, cyclic=True, rnd=5, keep="pack")   # the float pack
    for y in (22, 58):                                                                                # two straps: flat shapes on it
        P_(d, [(3, y - 2.4), (36, y - 2.4), (36, y + 2.4), (3, y + 2.4)], M["belt_f"], sharp=True, clip="pack")
    P_(d, [(24, 18.4), (30, 18.4), (30, 25.6), (24, 25.6)], M["brass_f"], rnd=1)                     # the upper strap's buckle
    P_(d, C(14, 38, 6, 22), M["steel_f"])                                                            # the dial: a flat disc
    P_(d, [(13.0, 38.9), (18.3, 33.6), (15.0, 39.6)], M["pack_f"], sharp=True)                       # its hand: a flat red wedge (run
    #                                                     3's dark pencil needle on the disc read as a pupil)
    F(d, M, [(7, 47), (20, 48), (33, 47)])                                                           # the lid's seam
    P_(d, [(2, 48), (37, 48), (37, 70), (2, 70)], M["pack_f"], sharp=True, clip="pack", shade=True)   # its underside: one flat shadow


# The heads, round 2 (LEAD 11-09 18:0x (2), (3), (4)): each round-1 head drawn 20 % larger about its face's centre and 4 px
# lower, so it fills about 70 % of the same 0.61 m bubble with its hair inside the glass; the eye 14 px wide on the 256 px
# figure; clean skin, the blush. Round 3: the same face in pencil and flat paint; two strand flicks in the hair.
EYE = (48.0, 28.0, 6.0, 7.6)                      # the side head's eye in the round-1 drawing space: centre x, y, radii
EYE34 = ((31.0, 0.9), (47.0, 1.0))                # the front-3/4 head's eyes: centre x, scale (the far one narrower); y 28
E34 = (5.6, 7.4)                                  # ... their radii at scale 1


def _hs(x, y):
    """A point of the side head's round-1 drawing space -> its canvas px."""
    return 38 + (x - 38) * HK - 1, 32 + (y - 32) * HK + 10


def _h34(x, y):
    return 37 + (x - 37) * HK, 32 + (y - 32) * HK + 10


@part("head", 72, 80, (32, 70))
def head(d, M):
    dn = xf(d, dy=6)
    d = xf(d, 38, HK, 32, HK, dx=-1, dy=10)
    S(dn, [(30, 56), (46, 56), (44, 64), (32, 64)], M["skin_sh"], OUT * 0.8, cyclic=True, rnd=1.5, gap=0)   # the neck, in the flat shadow tone
    S(d, C(38, 32, 22, 40, ry=24), M["skin"], OUT, cyclic=True)                                     # the face, in profile
    S(d, C(60.5, 36, 4.6, 18, ry=4.0), M["skin"], OUT * 0.9, cyclic=True, gap=0)                    # a rounded nose,
    P_(d, C(57, 36, 5.4, 16, ry=3.0), M["skin_f"], under=False)                                      # open into the face
    # round 4 (LEAD 07:1x (2)): the hair as five pointed tufts and three loose flicks, not one rounded mass (all inside the glass)
    # (run 5's five even upright points in mustard read as a CROWN: the tufts are now uneven and swept back, with a
    # forelock curling forward)
    S(d, [(19.5, 23), (17.5, 15), (14.5, 8.5), (21, 10.5), (20, 3.5), (28, 7), (29.5, 1.5), (37, 5.5), (41, 1.8), (45, 6),
          (52, 4.5), (55.5, 9.5), (50, 10.5), (51, 14), (45, 13), (38, 12.2), (30, 14), (24.5, 18.5)], M["hair"], OUT * 0.9, cyclic=True, rnd=2.2)
    F(d, M, [(24, 14), (25, 10.5), (24, 7.4)], 0.8)
    F(d, M, [(33, 11.6), (34, 8), (33, 5)], 0.8)
    F(d, M, [(46, 11.6), (49, 9), (52, 8.2)], 0.8)
    # (3): the eye - a white shape with NO ring round it, a heavier upper lid line, open below; a flat iris, a pupil, one
    # small highlight; the brow a shaped pencil stroke. (4): no blush disc
    ex, ey, erx, ery = EYE
    P_(d, C(ex, ey, erx, 22, ry=ery), M["eye_f"], keep="eye")
    P_(d, C(ex + 1.6, ey + 0.8, 4.1, 16, ry=5.3), M["iris_f"], clip="eye")                           # a large iris: a soft gaze
    P_(d, C(ex + 2.4, ey + 0.6, 2.2, 12), M["pupil_f"], clip="eye")
    P_(d, C(ex + 3.8, ey - 1.6, 1.1, 10), M["eye_f"])                                                # the catch-light
    S(d, C(ex, ey, erx, 14, ry=ery, a0=math.radians(192), a1=math.radians(348)), M["ln"], OUT * 1.1, ends=(2, 3))   # the upper lid
    F(d, M, [(41.5, 18.2), (48, 15.2), (55, 17.4)], 1.4, ends=(2, 5))                                # the brow
    F(d, M, [(56.3, 46.4), (53.5, 47.9), (50, 47.3), (47.2, 44.8)], 0.9, ends=(1.5, 3))              # the smile: from the profile in
    F(d, M, C(28.5, 36.5, 3.6, 12, ry=5.0, a0=math.radians(55), a1=math.radians(305)), 0.8)          # the ear: a small plain C


@part("head34", 72, 80, (36, 70))
def head34(d, M):
    dn = xf(d, dy=6)
    d = xf(d, 37, HK, 32, HK, dy=10)
    S(dn, [(28, 55), (46, 55), (44, 64), (30, 64)], M["skin_sh"], OUT * 0.8, cyclic=True, rnd=1.5, gap=0)   # the neck
    S(d, C(14, 33, 4, 14, ry=5.5), M["skin"], OUT * 0.8, cyclic=True, gap=0)                        # the far ear (behind the face)
    S(d, C(37, 32, 23, 40, ry=24), M["skin"], OUT, cyclic=True, at=0.25)                            # the face, three-quarter (the
    S(d, [(14.5, 22), (14, 14), (14.5, 9), (19, 9.5), (20.5, 3.2), (28, 6.4), (31, 1.4), (39, 4.6), (44, 1.8), (49.5, 5.5),   # line opens under the chin)
          (55, 5), (58.5, 11), (59, 20), (55, 14), (50, 14.5), (45, 12), (38, 14), (31, 11.5), (24, 14.5), (18, 13),            # the hair: uneven tufts
          (17.5, 19)], M["hair"], OUT * 0.9, cyclic=True, rnd=2.2)                                                            # swept to one side
    F(d, M, [(23, 12.4), (24, 9), (23, 6.4)], 0.8)
    F(d, M, [(34, 10.4), (35, 7), (34, 4.4)], 0.8)
    F(d, M, [(47, 10.4), (50, 8), (53, 7.6)], 0.8)
    for i, (cx, sc) in enumerate(EYE34):                                                            # two eyes: white shapes, no ring
        rx, ry, lid = E34[0] * sc, E34[1], 0.42
        P_(d, C(cx, 28, rx, 22, ry=ry), M["eye_f"], keep=f"eye{i}")
        P_(d, C(cx + 0.9, 28.8, 3.5 * sc, 16, ry=4.6), M["iris_f"], clip=f"eye{i}")
        P_(d, C(cx + 1.2, 28.6, 2.0, 12), M["pupil_f"], clip=f"eye{i}")
        P_(d, C(cx + 2.4, 26.9, 1.1, 10), M["eye_f"], clip=f"eye{i}")
        # round 2b (LEAD 11-09 18:2x): an upper lid across the top of each iris (a relaxed look): skin over the eye above
        # the lid's line; round 4: that line is the eye's ONE line, heavier, the eye open below
        a = math.asin(lid)
        P_(d, C(cx, 28, rx + 0.7, 12, ry=ry + 0.7, a0=math.pi + a, a1=TAU - a), M["skin_f"], sharp=True)
        x0 = (rx + 0.5) * math.cos(a)
        S(d, [(cx - x0, 28 - lid * ry + 0.7), (cx, 28 - lid * ry - 0.7), (cx + x0, 28 - lid * ry + 0.7)], M["ln"], OUT * 1.1, ends=(2, 2.5))
        F(d, M, [(cx - 6 * sc, 18.8), (cx, 16.3), (cx + 6 * sc, 18.4)], 1.4, ends=(2, 4))            # the brow: a shaped stroke
    P_(d, hose([(40, 33), (43.5, 38), (40, 40.5)], 3.6), M["skin_sh_f"])                             # the nose: a flat shadow shape
    F(d, M, [(33, 45.5), (39, 48.5), (46, 45.5)], 0.9, ends=(2, 2))


# The blink (LEAD 11-09 14:5x: ONE closed-eye swap part per facing now; the rest of the face-swap set after acceptance): a
# skin patch the size of the open eye and its line, the closed lid's line on it; shown on the head bone at BLINK's offset
@part("blink", 24, 28, (12, 14))
def blink(d, M):
    P_(d, C(12, 14, EYE[2] * HK + 2.2, 24, ry=EYE[3] * HK + 2.1), M["skin_f"])
    F(d, M, C(12, 14.5, 6.4, 10, ry=3.6, a0=math.radians(15), a1=math.radians(165)), 0.9, ends=(2, 2))   # the lid, bowed down


_GAP34 = (EYE34[1][0] - EYE34[0][0]) * HK         # the two eyes' spacing on the enlarged head (px)


@part("blink34", 40, 28, (20, 14))
def blink34(d, M):
    for cx, sc in ((20 - _GAP34 / 2, EYE34[0][1]), (20 + _GAP34 / 2, EYE34[1][1])):
        P_(d, C(cx, 14, E34[0] * sc * HK + 2.1, 24, ry=E34[1] * HK + 2.0), M["skin_f"])
        F(d, M, C(cx, 14.5, 5.6 * sc, 10, ry=3.4, a0=math.radians(15), a1=math.radians(165)), 0.9, ends=(2, 2))


# the blink's part and its pivot's offset (m) from the head's pivot, per facing: the open eye's centre on the canvas against
# the head's pivot (side: (32, 70); front34: the midpoint of the two eyes against (36, 70))
BLINK = {"side": ("blink", ((_hs(EYE[0], EYE[1])[0] - 32) / PX, (70 - _hs(EYE[0], EYE[1])[1]) / PX)),
         "front34": ("blink34", ((_h34((EYE34[0][0] + EYE34[1][0]) / 2, 28)[0] - 36) / PX, (70 - _h34(0, 28)[1]) / PX))}


@part("helmet", 100, 100, (50, 92))
def helmet(d, M):
    P_(d, C(50, 52, 38.6, 72), M["glass"])                                                           # the glass: a flat tint
    P_(d, CEL.crescent(50, 52, 34, math.radians(-162), math.radians(-102), 6.5), M["glint"], sharp=True)   # its ONE flat highlight
    S(d, C(50, 52, 39, 72), M["ln"], OUT, cyclic=True, at=0.62, gap=7)                              # the bubble's rim: the line
    S(d, [(22, 86), (78, 86), (76, 94), (24, 94)], M["steel"], OUT, cyclic=True, rnd=2)             # opens by the highlight; the seal ring


@part("antenna", 34, 50, (17, 45))
def antenna(d, M):
    db = xf(d, 15, 1.3, 9, 1.3, dx=2, dy=5)                                                          # the bob 30 % larger
    d = xf(d, dx=2, dy=5)
    S(d, hose([(15, 40), (14, 34), (16, 28), (14, 22), (16, 16)], 4.4), M["brass"], OUT * 0.7, cyclic=True, gap=0)   # a springy stalk
    F(d, M, [(15, 16), (15, 13)], 0.9, ends=(1, 1))
    S(db, [(9, 4), (21, 4), (15, 14)], M["brass"], OUT * 0.9, cyclic=True, rnd=1.2, gap=0)          # the brass plumb bob on it


@part("torso34", 96, 88, (48, 78))
def torso34(d, M):
    ds = xf(d, dx=8 + (50 - 40) * (WIDE - 1), dy=2)
    d = xf(d, 40, WIDE, dx=8, dy=2)
    body = [(20, 76), (60, 76), (66, 52), (66, 26), (60, 12), (50, 6), (28, 6), (17, 12), (12, 28), (13, 54)]
    _torso(d, ds, M, body, [(49.6, 5.6), (61.4, 11.6), (28.6, 77), (17.4, 72.4), (15.4, 64.4)], 40, 50, 38)
    S(d, [(22, 4), (58, 4), (60, 10), (20, 10)], M["steel"], OUT, cyclic=True, rnd=2)


@part("hips34", 80, 38, (40, 10))
def hips34(d, M):
    d = xf(d, 32, WIDE, dx=8, dy=2)
    S(d, [(8, 4), (56, 4), (58, 18), (52, 30), (32, 31.5), (12, 30), (6, 18)], M["suit"], OUT, cyclic=True, rnd=8)
    S(d, [(6, 3), (58, 3), (58, 11), (6, 11)], M["belt"], OUT, cyclic=True, rnd=1.5)
    S(d, [(43, 10), (54, 10), (53.4, 23), (44, 23)], M["belt"], OUT * 0.85, cyclic=True, rnd=2, gap=0)
    F(d, M, [(43.6, 15.6), (48.6, 17.4), (53.6, 15.6)], 0.9)
    P_(d, [(27.6, 1.6), (36.4, 1.6), (36.4, 12.4), (27.6, 12.4)], M["brass_f"], rnd=1.2, under=False)


@part("boot34", 56, 42, (27, 13))
def boot34(d, M):
    d = xf(d, 22, BIG, 28, BIG, dx=5, dy=9)                                                          # as the boot: about its sole
    S(d, [(12, 2), (30, 2), (32, 10), (38, 16), (39, 22), (35, 25), (8, 25), (7, 14)], M["boot"], OUT, cyclic=True, rnd=4)
    S(d, [(6, 23), (40, 23), (39, 28), (7, 28)], M["sole"], OUT * 0.9, cyclic=True, rnd=2)
    F(d, M, [(10.8, 6.4), (21, 7.3), (31.4, 6.4)])


STATS = {}            # part -> its pencil strokes' stats (cel_v6.render), filled by layers(): the sheet's printed numbers


def layers(name, boil=0):
    """One part's two cel layers at the large size: (paint with its flat shadow shape, the dried pencil line)."""
    w, h, pivot, fn, band = PARTS[name]
    c = CEL.Canvas(w, h, K, tag=name)
    fn(c.dm, mats(c.gp))
    paint, line, st = c.render(boil=boil)
    if boil == 0:
        STATS[name] = st
    if band:
        paint = CEL.shade(paint, band, K, BACK)
    return paint, CEL.dry(line, (zlib.crc32(name.encode()) & 0xFFFF) + 977 * boil)


def shovel_cel():
    """B-226's shovel as a cel, on its own sprite's layout (192 x 64 design px, the grip at (12.8, 32), the blade's tip
    1.33 m on) -> (RGBA uint8 at the large size, its pivot in large px). For the sheets only; the shipped shovel is v3."""
    c = CEL.Canvas(192, 64, K, tag="shovel")
    M, d = mats(c.gp), c.dm
    S(d, hose([(18, 32), (124, 32)], 5.0), M["hose"], OUT * 0.8, cyclic=True, gap=0)                # the teal haft
    S(d, [(5, 22), (13, 22), (13, 42), (5, 42)], M["brass"], OUT * 0.8, cyclic=True, rnd=3, gap=0)  # the grip
    blade = [(12.8 + 128 * x, 32 + 128 * y) for x, y in ((0.97, -0.13), (1.04, -0.145), (1.14, -0.14), (1.25, -0.10), (1.33, 0.0),
                                                          (1.25, 0.10), (1.14, 0.14), (1.04, 0.145), (0.97, 0.13))]
    S(d, blade, M["steel"], OUT, cyclic=True, rnd=4)
    P_(d, [(118, 28), (130, 28), (130, 36), (118, 36)], M["brass_f"], rnd=1.5, under=False)          # the ferrule
    paint, line, _st = c.render()
    return CEL.compose(paint, CEL.dry(line, 77)), (12.8 * K, 32 * K)


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
        ("antenna", "antenna", "helmet", (-0.04, 0.615), 0.0, 0.3, 17),    # over the bubble (it lies back across it in crouch)
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
    # desk-check 11-09 14:3x (forward kinematics by hand): every pose has both soles level (a boot's world angle 0 = flat)
    # round 4 (LEAD 11-10 07:1x (8)): the idle with a little life - the pelvis tipped back 3, the chest forward 7 on it, the
    # head up 8 (a curve through the spine instead of a plumb line), the arms a little bent, the weight on the back leg.
    # Soles level: 3 + 2 - 7 + 2 = 0 (near), 3 - 8 + 1 + 4 = 0 (far)
    "idle": {"hips": 3, "torso": -7, "head": 8, "upper_arm_f": 12, "forearm_f": 22, "upper_arm_b": -10, "forearm_b": 16,
             "thigh_f": 2, "shin_f": -7, "boot_f": 2, "thigh_b": -8, "shin_b": 1, "boot_b": 4},
    # LEAD 11-09 14:4x: the 1 m gap stays (terrain cells are 1 m), so the crouch stands <= 0.98 m: a deep forward tuck, the
    # springy antenna pressed back along the helmet, and a root squash of 0.92 (root_scale_z: a per-state root scale about the
    # ground, in the bone JSON's "states" for U-199); the sheet measures the drawn top and draws the 1 m line
    "crouch": {"torso": -76, "head": 58, "antenna": 123, "upper_arm_f": 45, "forearm_f": 90, "upper_arm_b": 38, "forearm_b": 94,
               "thigh_f": 115, "shin_f": -142, "boot_f": 27, "thigh_b": 95, "shin_b": -152, "boot_b": 57, "root_scale_z": 0.92},
    # round 2 (LEAD 18:0x (5)): the counter-swing - the near arm forward and up, clear of the glass, the far arm back and down
    "jump": {"torso": -8, "head": 10, "upper_arm_f": 108, "forearm_f": 25, "upper_arm_b": -40, "forearm_b": 20,
             "thigh_f": 78, "shin_f": -96, "boot_f": 18, "thigh_b": 40, "shin_b": -104, "boot_b": 30, "lift": 0.42},
    # a lunge on the shovel: the near hand on the D-grip, the shovel 48 deg down (DIG_AIM), the back foot on its toe
    "dig": {"torso": -24, "head": 18, "upper_arm_f": -18.8, "forearm_f": 121.6, "upper_arm_b": 35.3, "forearm_b": 41.3,
            "thigh_f": 40, "shin_f": -52, "boot_f": 12, "thigh_b": -25, "shin_b": -27, "boot_b": 35.8},
    # round 2 (LEAD 18:0x (6)): one walk CONTACT pose - the near heel down ahead, the far foot behind on its toe
    "walk": {"torso": -4, "head": 4, "upper_arm_f": -24, "forearm_f": 16, "upper_arm_b": 26, "forearm_b": 24,
             "thigh_f": 27, "shin_f": -6, "boot_f": -7, "thigh_b": -20, "shin_b": -28, "boot_b": 26},
}
GRIP = (0.03 * BIG, -0.09 * BIG)                  # the near hand's grip socket (m from the wrist): with the glove, 25 % further
DIG_AIM = -126.8      # the shovel's turn from the near hand's angle (the hand's world angle 78.8 in "dig": 48 deg below level)


def rig_json(parts_rects):
    out = {"key": KEY, "style": "v6", "ppu": PX * K, "rect_origin": "bottom_left", "height_m": 2.0,
           "note": "B-231 DESIGN (C5): previews only until the owner's look-over (D-185); the contract's v4 rig schema follows it",
           "parts": [{"name": n, "rect": r, "pivot": p} for n, r, p in parts_rects], "facings": []}
    for facing in ("side", "front34"):
        out["facings"].append({
            "name": facing,
            "bones": [{"name": n, "part": p + ("_far" if n in FAR else ""), "parent": par, "offset_m": [round(o[0], 4), round(o[1], 4)], "rest_deg": r,
                       "length_m": L_, "order": order, "far": n in FAR} for n, p, par, o, r, L_, order in bones(facing)],
            "ik": [{"chain": ["upper_arm_f", "forearm_f"], "effector": "hand_f", "bend": "back"},
                   {"chain": ["upper_arm_b", "forearm_b"], "effector": "hand_b", "bend": "back"},
                   {"chain": ["thigh_f", "shin_f"], "effector": "boot_f", "bend": "forward"},
                   {"chain": ["thigh_b", "shin_b"], "effector": "boot_b", "bend": "forward"}],
            "sockets": {"hand_f_grip": {"bone": "hand_f", "offset_m": [round(GRIP[0], 4), round(GRIP[1], 4)]},
                        "helmet_top": {"bone": "antenna", "offset_m": [0.0, 0.3]}},
            "swaps": {"blink": {"part": BLINK[facing][0], "bone": "head", "offset_m": [round(v, 4) for v in BLINK[facing][1]], "order": 14.5,
                                "note": "shown over the head (under the helmet) while the eyes are closed; hidden otherwise"}}})
    # per state (LEAD 11-09 14:4x, for U-199 to read, not guess): the root's scale [x, z] about the ground point (the crouch's
    # 0.92 squash), the root's lift, and the design pose in degrees added to each bone's rest angle (side facing)
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
        n, p, par, off, rest, L_, order = B[name]
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
    """The posed figure's height (m) on a LARGE pose image: its top-most drawn row above the ground row (large px)."""
    rows = np.where(img[..., 3].max(axis=1) > 0.02)[0]
    return (ground - rows[0]) / float(PX * K) if len(rows) else 0.0


PW, PH, PG, PCX = 300, 380, 350, 150              # a pose cell in design px: width, height, the ground row, the feet's x


def pose_image(P, facing, pose, prop=None, blink=False):
    """One posed figure, LARGE (PW * K x PH * K, premultiplied float), the ground line at row PG * K; the pose's
    root_scale_z (the crouch's squash) applied about the ground. blink: the closed-eye swap shown on the head."""
    k = PX * K
    dst = np.zeros((PH * K, PW * K, 4), np.float32)
    world = solve(facing, pose)

    def at(x, z):
        return (PCX * K + x * k, PG * K - z * k)
    for n, p, par, off, rest, L_, order in sorted(bones(facing), key=lambda b: b[6]):
        if prop is not None and n == "upper_arm_f":                            # the held tool on the near hand's grip socket,
            pimg, ppiv, aim = prop                                             # over the body and the far hand, under the near arm
            x, z, a = world["hand_f"]
            t = math.radians(a)
            gx, gz = x + GRIP[0] * math.cos(t) - GRIP[1] * math.sin(t), z + GRIP[0] * math.sin(t) + GRIP[1] * math.cos(t)
            place(dst, pimg, ppiv, a + aim, at(gx, gz))
        img, pivot = P[p + ("_far" if n in FAR else "")]
        x, z, a = world[n]
        place(dst, img, pivot, a, at(x, z))
        if blink and n == "head":                                              # the swap, over the head and under the helmet
            bp, (bx, bz) = BLINK[facing]
            t = math.radians(a)
            place(dst, P[bp][0], P[bp][1], a, at(x + bx * math.cos(t) - bz * math.sin(t), z + bx * math.sin(t) + bz * math.cos(t)))
    return squash(dst, PG * K, pose.get("root_scale_z", 1.0))


FAR_PARTS = ("upper_arm", "forearm", "hand", "thigh", "shin", "boot", "boot34")


def all_parts(boil=0, paint_of=None, key=None):
    """Every part as a finished cel at the large size: name -> (RGBA uint8, pivot in large px). boil: the line pass (0 =
    the drawing; 1, 2 = alternate pencil passes for the 12 Hz boil). paint_of: pass 0's layers, so an alternate pass
    draws only its line over the SAME paint. key: (mul, add rgb) re-keys the whole figure's PAINT for a place or a time
    of day (STYLE_V6 2.5: in shadow, at night), the pencil unchanged. Returns (parts, layers)."""
    P, LAY = {}, {}
    far = FAR_KEY if key is None else (FAR_KEY[0] * key[0], FAR_KEY[1] * key[0] + np.array(key[1], np.float32))
    for name, (w, h, pivot, fn, band) in PARTS.items():
        paint, line = layers(name, boil)
        if paint_of is not None:
            paint = paint_of[name][0]
        LAY[name] = (paint, line)
        pv = (pivot[0] * K, pivot[1] * K)
        P[name] = (CEL.compose(paint, line, key), pv)
        if name in FAR_PARTS:                                                  # the far limbs: the paint re-keyed, the line kept
            P[name + "_far"] = (CEL.compose(paint, line, far), pv)
    return P, LAY


def sheet(P, g=v3.GUTTER):
    """Shelf-pack the LARGE parts onto one sheet (2048 wide) -> (RGBA, [(name, rect bottom-left, pivot normalised)]). g: the
    gutter between parts and around the sheet (the contract's 4 px)."""
    names = sorted(P, key=lambda n: -P[n][0].shape[0])
    W, x, y, row_h, placed = 2048, g, g, 0, []
    for n in names:
        img = P[n][0]
        h, w = img.shape[:2]
        if x + w + g > W:
            x, y, row_h = g, y + row_h + g, 0
        placed.append((n, x, y, w, h))
        x += w + g
        row_h = max(row_h, h)
    H = int(math.ceil((y + row_h + g) / 4.0) * 4)
    out = np.zeros((H, W, 4), np.uint8)
    rects = []
    for n, x, y, w, h in placed:
        out[y:y + h, x:x + w] = P[n][0]
        px, py = P[n][1]
        rects.append((n, [x, H - y - h, w, h], [round(px / w, 4), round(1 - py / h, 4)]))
    return out, rects


# ---------------------------------------------------------------- the design sheet (round 3's plates)
STAGE = np.array([0.665, 0.725, 0.571], np.float32)       # the plates' flat ground: a muted mid-value sage, about what a
#                                                           painted backdrop puts behind the figure (a cel is judged on it)


def preview(out, footnote=None):
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    t0 = time.time()
    P, LAY = all_parts()
    ST = dict(STATS)                                                             # the figure's own strokes (later passes refill STATS)
    t_parts = time.time() - t0
    t1 = time.time()
    PB, _lay = all_parts(boil=1, paint_of=LAY)                                   # the second pencil pass over the same paint
    t_boil = time.time() - t1
    sh, rects = sheet(P)
    shb, _r = sheet(PB)
    paper = np.array(review.PAPER, np.float32)
    ground_col = rgb(PAL["green"]) * 0.5 + rgb(PAL["brown"]) * 0.5
    W = 1920

    def sprite0(key):
        """An exported sprite's first frame (straight RGBA uint8) and its px per metre."""
        base = os.path.join(ART, *key.split("/"))
        if not os.path.isfile(base + "_color.png"):
            return None, 64
        im = pngio.read_png_np(base + "_color.png")
        J = json.load(open(base + ".json", encoding="utf-8")) if os.path.isfile(base + ".json") else {}
        if "frame_width" in J:
            im = im[:J["frame_height"], :J["frame_width"]]
        return im, J.get("ppu", 64)

    def over(dst, img, x, y):
        """A premultiplied float image over an opaque float canvas, its top-left at (x, y), clipped."""
        h, w = img.shape[:2]
        x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
        if x1 <= x0 or y1 <= y0:
            return
        s = img[y0 - y:y1 - y, x0 - x:x1 - x]
        dst[y0:y1, x0:x1] = s[..., :3] + dst[y0:y1, x0:x1] * (1 - s[..., 3:4])

    def head(text, h=20):
        hd = np.tile(paper, (h, W, 1)).astype(np.float32)
        review._label(hd, text, 6, 4, scale=1)
        return hd

    def stage(h):
        return np.tile(STAGE, (h, W, 1)).astype(np.float32)

    sh_u8, sh_piv = shovel_cel()                                                 # the shovel as a cel (LEAD 07:1x), on the grip
    prop = (sh_u8, sh_piv, DIG_AIM)
    global JOINT                                                                 # the other joint, for plate 3: no hardware
    JOINT = "none"
    try:
        PN, _lay = all_parts()
    finally:
        JOINT = "band"
    order = ("idle", "walk", "crouch", "jump", "dig")
    pimg = {k: pose_image(P, "side", POSES[k], prop=prop if k == "dig" else None) for k in order}
    front = pose_image(P, "front34", POSES["idle"])
    blinkp = pose_image(P, "side", POSES["idle"], blink=True)
    idle_b = pose_image(PB, "side", POSES["idle"])
    rows = [np.tile(paper, (30, W, 1)).astype(np.float32)]
    review._label(rows[0], "B-231 ROUND 3 in ART v6 (D-198 + D-199): the v5 surveyor as a CEL (a charcoal pencil line, flat paint), drawn at 512 px per metre. Every plate is that drawing SHRUNK; none enlarges a pixel. PREVIEW", 6, 8)

    # ---- plate 1: the game's zoom (shrunk 8 times: 64 px per metre), beside the camp props and the v4 surveyor
    rows.append(head("PLATE 1 - THE GAME'S ZOOM (1080p, 64 px per metre; the large drawing shrunk 8x): the v4 surveyor | v6 idle, walk, three-quarter, idle facing left, crouch, jump, dig | today's camp props (v3 art: the smelter, the lamp)"))
    r = stage(230)
    gy = 200
    r[gy:gy + 3] = ground_col
    x = 20
    v4, _p = sprite0("characters/surveyor/side")
    if v4 is not None:
        over(r, CEL.premul(v4), x, gy - v4.shape[0])
        x += v4.shape[1] + 10
    small = {k: CEL.down(pimg[k], 8) for k in order}
    sg = PG * K // 8                                                             # the ground row of a shrunk cell
    for im in (small["idle"], small["walk"], CEL.down(front, 8), small["idle"][:, ::-1], small["crouch"], small["jump"], small["dig"]):
        over(r, im, x, gy - sg)
        x += im.shape[1] - 10
    x += 30
    for key in ("props/common/smelter", "props/common/lamp"):
        im, ppu = sprite0(key)
        if im is not None and ppu == 64:
            over(r, CEL.premul(im), x, gy - im.shape[0])
            x += im.shape[1] + 10
    rows.append(r)

    # ---- plate 2: the pose row at twice the game's zoom (shrunk 4 times)
    rows.append(head("PLATE 2 - THE POSE ROW at 2x the game's zoom (shrunk 4x): idle | walk | crouch under the 1 m line | jump apex | dig (the shovel as a cel, on the grip) | three-quarter idle"))
    r = stage(PH + 20)
    r[PG:PG + 3] = ground_col
    crouch_top = top_m(pimg["crouch"], PG * K)
    for i, k in enumerate(order + ("front",)):
        im = CEL.down(front if k == "front" else pimg[k], 4)
        over(r, im, i * PW + 10, 0)
        review._label(r, k if k != "front" else "three-quarter", i * PW + 16, PG + 8, scale=1)
        if k == "crouch":
            yc = PG - int(round(1.0 * PX))
            r[yc - 2:yc, i * PW + 10:i * PW + 10 + PW] = rgb(PAL["red"])
            review._label(r, f"1 m ceiling; the crouch stands {crouch_top:.3f} m", i * PW + 30, yc - 16, scale=1)
    rows.append(r)

    # ---- plate 3: close-ups, each a window of the large drawing shrunk (4x zoom = shrunk 2x; 8x = the drawing itself)
    w_idle = solve("side", POSES["idle"])

    def crop(img, x0, z0, x1, z1):
        """The LARGE pose image between two world points (m): x0 < x1, z0 < z1."""
        k = PX * K
        X0, X1 = int(PCX * K + x0 * k), int(PCX * K + x1 * k)
        Y0, Y1 = int(PG * K - z1 * k), int(PG * K - z0 * k)
        return img[max(Y0, 0):Y1, max(X0, 0):X1]

    def on_stage(img):
        return img[..., :3] + STAGE * (1 - img[..., 3:4])
    hx, hz, _a = w_idle["hand_f"]
    kx, kz, _a = w_idle["shin_f"]
    bx, bz, _a = w_idle["boot_f"]
    face = (-0.36, 1.36, 0.44, 2.02)
    boxes = [("the face", face), ("a glove", (hx - 0.16, hz - 0.26, hx + 0.20, hz + 0.08)),
             ("a knee cuff", (kx - 0.20, kz - 0.20, kx + 0.20, kz + 0.16)), ("a boot", (bx - 0.20, bz - 0.22, bx + 0.42, bz + 0.12))]
    rows.append(head("PLATE 3 - CLOSE-UPS of the idle pose, each a window of the large drawing: at 2x the game's zoom (shrunk 4x), then at 4x (shrunk 2x) ||| THE JOINTS at 4x, the jump's bent knee and elbow: slim ribbed bands (the figure's) | no hardware (the shapes overlap, one fold flick)"))
    crops = [(name, crop(pimg["idle"], *b)) for name, b in boxes]
    w_jump = solve("side", POSES["jump"])
    jn = pose_image(PN, "side", POSES["jump"])
    joints = []
    for label, bone in (("the knee", "shin_f"), ("the elbow", "forearm_f")):
        jx, jz, _a = w_jump[bone]
        for kind, im in (("bands", pimg["jump"]), ("no hardware", jn)):
            joints.append((f"{label}: {kind}", crop(im, jx - 0.3, jz - 0.3, jx + 0.3, jz + 0.3)))
    for f, label in ((4, "2x"), (2, "4x")):
        hmax = max(c.shape[0] for _n, c in crops) // f + 24
        r = stage(hmax)
        x = 10
        for i, (name, c) in enumerate(crops + (joints if f == 2 else [])):
            im = on_stage(CEL.down(c, f))
            if x + im.shape[1] > W:
                break
            r[20:20 + im.shape[0], x:x + im.shape[1]] = im[:hmax - 20]
            review._label(r, f"{name} at {label}" if i < len(crops) else name, x, 4, scale=1)
            x += im.shape[1] + 24
        rows.append(r)

    # ---- plate 4: the boil's two line passes, the blink, and the part sheet shrunk 4 times
    rows.append(head("PLATE 4 - at 4x: the face in line pass A | in line pass B (the same paint, the pencil drawn again: the 12 Hz boil swaps them) | the blink swap ||| the part sheet, shrunk 4x"))
    fa, fb = (on_stage(CEL.down(crop(im, *face), 2)) for im in (pimg["idle"], idle_b))
    bl = on_stage(CEL.down(crop(blinkp, *face), 2))
    shs = CEL.down(CEL.premul(sh), 4)
    r = stage(max(fa.shape[0], shs.shape[0]) + 10)
    x = 10
    for im in (fa, fb, bl):
        r[4:4 + im.shape[0], x:x + im.shape[1]] = im[:, :max(0, W - x)]
        x += im.shape[1] + 12
    over(r, shs[:, :max(0, W - x - 10)], x + 10, 4)
    rows.append(r)

    def figure(facing):
        st = []
        for n, p, *_rest in bones(facing):
            st.extend(ST[p])
        return CEL.line_stats(st)
    mean_w, min_w, max_w, n_lines = figure("side")
    all_w = CEL.line_stats([s for st in ST.values() for s in st])
    dd = os.path.join(os.path.dirname(out), "b231")
    os.makedirs(dd, exist_ok=True)
    na = pngio.write_png(os.path.join(dd, "rig_color.png"), sh)                  # the large part sheet (pass A) and the bone
    nb = pngio.write_png(os.path.join(dd, "rig_color_b.png"), shb)               # JSON beside the review (not exported)
    shift = float(np.abs(pimg["idle"][..., 3] - idle_b[..., 3]).mean() / max(float(pimg["idle"][..., 3].mean()), 1e-6))
    lines = [f"THE LINE at the game's zoom, measured along every pencil stroke of the side figure: mean {mean_w:.2f} px, from {min_w:.2f} px (a tapered end) to {max_w:.2f} px (full pressure); "
             f"{n_lines} pencil strokes on the figure, charcoal {CEL.CHARCOAL}; all parts of both facings: mean {all_w[0]:.2f} px",
             f"the crouch stands {crouch_top:.3f} m (the limit 0.98 m under a 1 m gap); the idle {top_m(pimg['idle'], PG * K):.3f} m to the plumb bob",
             f"the part sheet: {sh.shape[1]}x{sh.shape[0]} px at {PX * K} px per metre, {len(rects)} parts on pivots (far limbs: the paint a step darker, the line the same), {na // 1024} KB; "
             "the bones, pivots and poses are round 2b's, unchanged",
             f"THE BOIL: a second pencil pass over the same paint took {t_boil:.0f} s more (the first pass with its paint {t_parts:.0f} s); as a second sheet of the same rects it is {nb // 1024} KB on disk "
             f"and {sh.shape[1] * sh.shape[0] * 4 // (1024 * 1024)} MB more texture uncompressed; the two passes differ on {shift * 100:.1f} % of the figure's coverage (under a pixel at the game's zoom)",
             f"this run: {time.time() - t0:.0f} s to draw, paint, pose and shrink everything"]
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-231 round 3 (v6 cel) design preview (lock-free, fakegp + numpy; not exported)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0], f"| sheet {sh.shape[1]}x{sh.shape[0]}, {len(rects)} parts")
    for ln in lines:
        print(ln)
    for k in order:
        w_ = solve("side", POSES[k])
        print(f"{k}: drawn top {top_m(pimg[k], PG * K):.3f} m, soles f / b {sole_z(w_, 'boot_f'):+.3f} / {sole_z(w_, 'boot_b'):+.3f} m")
    with open(os.path.join(dd, "rig.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rig_json(rects), fh, indent=1)
        fh.write("\n")
    for name, c in crops:                                                        # the 4x windows as files, for the owner's page
        c4 = CEL.down(c, 2)
        u8 = np.clip(np.rint(np.dstack([on_stage(c4), np.ones(c4.shape[:2], np.float32)]) * 255), 0, 255).astype(np.uint8)
        pngio.write_png(os.path.join(dd, "close_" + name.split()[-1] + "_4x.png"), u8)
    print("part sheets (pass A, pass B) + rig.json + the 4x windows ->", dd)


# ---------------------------------------------------------------- the export (written, NOT YET RUN)
def export_checks(P, sh, rects):
    """What must hold before a file is written (contract 2 / 11.1 / 11.3): one line per problem."""
    out = []
    if sh.shape[0] > v3.MAX_SHEET or sh.shape[1] > v3.MAX_SHEET:
        out.append(f"the sheet is {sh.shape[1]}x{sh.shape[0]} (cap {v3.MAX_SHEET})")
    on_sheet = {n for n, _rect, _pivot in rects}
    for n in sorted(P):
        a = P[n][0][..., 3]
        if a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any():
            out.append(f"part {n}: paint on its rect's outermost row or column (clipped by its canvas?)")
    for facing in ("side", "front34"):
        bl = bones(facing)
        names = [b[0] for b in bl]
        if len(set(names)) != len(names):
            out.append(f"{facing}: a bone name is used twice")
        roots = [b[0] for b in bl if b[2] is None]
        if len(roots) != 1:
            out.append(f"{facing}: {len(roots)} root bones ({', '.join(roots)})")
        for n, p, par, _o, _r, _length, _order in bl:
            part_name = p + ("_far" if n in FAR else "")
            if part_name not in on_sheet:
                out.append(f"{facing}/{n}: its part {part_name} is not on the sheet")
            if par is not None and par not in names:
                out.append(f"{facing}/{n}: its parent {par} is not a bone of this facing")
        if BLINK[facing][0] not in on_sheet:
            out.append(f"{facing}: the blink swap's part {BLINK[facing][0]} is not on the sheet")
    return out


def export(art):
    """ONLY after the owner's yes on the look-over (USER-39) and LEAD's word (B-231: no export before it): the part sheet
    and the bone JSON -> characters/surveyor_v5/rig_color.png + rig.json, through render.py's kit path (export / keys /
    preview). The manifest row is added at that moment and not before, so no batch run can ship the design early. (The
    boil's alternate line passes are a second sheet of the same rects; whether they ship is LEAD's call with U-199.)"""
    P, _lay = all_parts()
    sh, rects = sheet(P)
    problems = export_checks(P, sh, rects)
    if problems:
        raise ValueError("B-231 checks: " + "; ".join(problems))
    base = os.path.join(art, *KEY.split("/"))
    os.makedirs(os.path.dirname(base), exist_ok=True)
    n = pngio.write_png(base + "_color.png", sh)
    meta = rig_json(rects)
    meta["note"] = ("B-231 (C5, D-185): the v5 surveyor's part sheet and bones, exported after the owner's look-over; "
                    "the contract's v4 rig schema follows it")
    with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    return [(KEY, sh.shape[1], sh.shape[0], n)]


def keys():
    return [KEY]


if __name__ == "__main__":                       # python -I build_surveyor_v5.py <review png>
    preview(sys.argv[1])
