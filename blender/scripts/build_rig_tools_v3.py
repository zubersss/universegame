"""B-205 (D-174; LEAD 18:2x rule, D-087): the tools you upgrade, visible, in v3 ink on the surveyor's existing sockets.

The Beam reads as a MINING tool, never a gun: no pistol grip, no trigger; an arm-mounted, cable-fed emitter with a cutting nozzle.
Mk1-5 grow the emitter (length, girth, cooling rings) and warm the beam from teal to gold.

  props/rig/beam_mk<1..5>    128x64 @ PPU 128, pivot [0.375, 0.5] = the hand (RigModules' tool contract); the nozzle tip stays at
                             MUZZLE (0.47, 0.03) m for every Mk; json "cable_socket" = where a cable line leaves its back
                             (props/rig/beam = Mk1 at export)
  fx/beam_ray_mk<1..5>       256x32 x 8 frames @ PPU 128 (0.25 m: RigToolView.BeamHeight), pivot [0, 0.5], tiles in x, clip 'flow'
  props/rig/grapple_mk<1..3> 128x64 @ PPU 128, pivot [0.375, 0.5]: a hand reel, the three-pronged hook seated forward (no barrel:
                             never a launcher gun); Mk3 twin anchors (props/rig/grapple = Mk1 at export)
  props/rig/jetpack_mk<2,3>  64x64 @ PPU 64, pivot [0.5, 0.5] = the float pack's centre: tanks, nozzles and fins strapped on;
                             Mk1 is the float pack as the surveyor sheet draws it. json "back_socket": per frame of
                             characters/surveyor/side, [x, z, angle_rad, sx, sz] from build_surveyor_v3's own pose math (null where the
                             pack is hidden: the front views)

  python -I build_rig_tools_v3.py <review png>     the lock-free sheet: each tool's looks on the surveyor at 1x
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp, v3  # noqa: E402
import build_icons_items_v3 as IT  # noqa: E402   (installs fakegp; the icon materials: <tone>[_sh|_dp][_i], ink)

G = IT.G
import gp_raster as GR  # noqa: E402

O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
TPPU, TW, TH, TPIV = 128, 128, 64, (0.375, 0.5)
MUZZLE = {"beam": (0.47, 0.03), "grapple": (0.52, 0.035), "survey": (0.30, 0.06), "builder": (0.44, 0.03)}   # B-217: survey /
                                                                                     # builder at RigModule.Muzzle's constants (no code change)
BEAM_TONES = {1: ("teal", "off"), 2: ("teal", "mustard"), 3: ("green", "off"), 4: ("mustard_sh", "off"), 5: ("mustard", "off")}


def render(fn, w, h, ppu, piv, seed=5):
    gp = fakegp.FakeGP()
    M = IT.mats(gp, "earth")
    d = fakegp.FakeDrawing()
    fn(d, M)
    return GR.render_frame(fakegp.strokes_of(d, gp), w, h, ppu, piv, ss=4, seed=seed)


def hose(pts, w):
    return G.hose_outline(pts, w)


def circ_pts(cx, cz, r, n=10):
    return [(cx + r * math.cos(TAU * i / n), cz + r * math.sin(TAU * i / n)) for i in range(n)]


# ---------------------------------------------------------------- the Beam, Mk1-5 (metres from the hand, +x the aim)
def cable_path(mk):
    """From the emitter's back end, backward and up in a soft curve toward the pack (its end: the json's cable_socket)."""
    x0 = 0.36 - (0.24 + 0.035 * (mk - 1)) - 0.12
    return [(x0 - 0.03, 0.0), (x0 - 0.09, 0.03), (x0 - 0.14, 0.08), (x0 - 0.17, 0.14)]


def beam_tool(mk):
    def fn(d, M):
        L = 0.24 + 0.035 * (mk - 1)                                                          # the body grows back from the nozzle
        r = 0.055 + 0.008 * (mk - 1)                                                         # and in girth
        x1 = 0.36                                                                            # the body's front (the nozzle beyond)
        x0 = x1 - L - 0.12
        G.stroke(d, hose(cable_path(mk), 0.03), M["brown_sh_i"], I, cyclic=True)            # the cable, trailing back and up to the
        G.stroke(d, [(x0 - 0.035, -0.035), (x0 + 0.005, -0.035), (x0 + 0.005, 0.035), (x0 - 0.035, 0.035)], M["sky_sh_i"], I, cyclic=True)  # pack
        # rev 19:2x (LEAD): nothing under the body (an L-shaped cable with a plug beneath read as a pistol grip)
        body = [(x0, -r), (x1, -r * 0.9), (x1, r * 0.9), (x0, r)]
        G.stroke(d, body, M["teal_sh_i" if mk < 5 else "mustard_sh_i"], O, cyclic=True)
        G.stroke(d, [(x0, r * 0.15), (x1, r * 0.1), (x1, r * 0.9), (x0, r)], M["teal" if mk < 5 else "mustard"], 0.0, cyclic=True)
        G.stroke(d, body, M["ink"], O, cyclic=True)
        for k in range(1 + mk // 2):                                                          # cooling rings: more with the Mk
            x = x1 - 0.05 - 0.045 * k
            G.stroke(d, [(x - 0.012, -r - 0.01), (x + 0.012, -r - 0.01), (x + 0.012, r + 0.01), (x - 0.012, r + 0.01)], M["sky_i"], I, cyclic=True)
        tone, core = BEAM_TONES[mk]                                                           # the glow ring: the Mk's beam tone
        G.stroke(d, [(x1 - 0.02, -r * 0.8), (x1 + 0.01, -r * 0.8), (x1 + 0.01, r * 0.8), (x1 - 0.02, r * 0.8)], M[tone + "_i"], I, cyclic=True)
        G.stroke(d, [(x1 + 0.01, -r * 0.75), (0.45, -0.025), (0.47, -0.02), (0.47, 0.02), (0.45, 0.025), (x1 + 0.01, r * 0.75)],
                 M["mustard_i" if mk < 5 else "red_sh_i"], I, cyclic=True)                   # the cutting nozzle
        G.seam(d, [(0.415, -0.03), (0.415, 0.03)], M["ink"])
        G.stroke(d, [(-0.06, -r - 0.035), (0.06, -r - 0.035), (0.06, r + 0.035), (-0.06, r + 0.035)], M["brown_i"], O, cyclic=True)   # the arm cuff
        for x in (-0.025, 0.025):
            G.stroke(d, [(x - 0.008, -r - 0.035), (x + 0.008, -r - 0.035), (x + 0.008, r + 0.035), (x - 0.008, r + 0.035)], M["mustard"], 0.0, cyclic=True)
    return fn


def beam_ray(mk, k):
    """One frame of the ray (256x32 at PPU 128 = 2 x 0.25 m), a band in the Mk's tone, a pale core, bright segments flowing +x."""
    tone, core = BEAM_TONES[mk]

    def fn(d, M):
        Lr = 2.0
        G.stroke(d, [(-0.01, -0.07), (Lr + 0.01, -0.07), (Lr + 0.01, 0.07), (-0.01, 0.07)], M[tone], 0.0, cyclic=True)
        G.stroke(d, [(-0.01, -0.025), (Lr + 0.01, -0.025), (Lr + 0.01, 0.025), (-0.01, 0.025)], M["off" if core == "off" else core], 0.0, cyclic=True)
        for j in range(8):                                                                    # flowing sparks, period 0.25 m
            x = (j * 0.25 + k * 0.25 / 8) % Lr
            G.stroke(d, [(x, 0.075), (x + 0.06, 0.09), (x + 0.12, 0.075), (x + 0.06, 0.062)], M[core if core != "off" else "off"], 0.0, cyclic=True)
            dark = tone[:-3] + "_dp" if tone.endswith("_sh") else tone + "_sh"
            G.stroke(d, [(x + 0.1, -0.075), (x + 0.16, -0.09), (x + 0.22, -0.075), (x + 0.16, -0.062)], M[dark], 0.0, cyclic=True)
    return fn


# ---------------------------------------------------------------- the Grapple, Mk1-3: a hand reel, the hook seated forward
def grapple_tool(mk):
    def fn(d, M):
        R = 0.09 + 0.015 * (mk - 1)
        G.stroke(d, hose([(0.0, 0.0), (0.24, 0.0)], 0.035), M["sky_sh_i"], I, cyclic=True)   # the arm to the hook seat
        G.stroke(d, IT.lump(0.0, 0.0, R, R, 11 + mk, n=12, jit=0.0), M["sky_sh_i"], O, cyclic=True)     # the reel drum (steel)
        for k in range(3):                                                                   # the coiled line, lap on lap (rev 19:1x:
            rr = R * (0.78 - 0.16 * k)                                                       # a dark drum hid it)
            G.stroke(d, hose([(rr * math.cos(a), rr * math.sin(a)) for a in [TAU * i / 20 for i in range(19)]], 0.022), M["mustard_sh_i"], I * 0.7, cyclic=True)
        G.stroke(d, hose([(-R * 0.4, R * 0.1), (R * 0.4, -R * 0.1)], 0.02), M["sky_i"], I, cyclic=True)   # the crank bar
        if mk < 3:                                                                           # the hook: shank + three prongs forward
            G.stroke(d, hose([(0.24, 0.0), (0.44, 0.0)], 0.03), M["sky_sh_i"], I, cyclic=True)
            for side in (-1, 1):
                G.stroke(d, hose([(0.46, 0.0), (0.47, side * 0.05), (0.44, side * 0.07)], 0.022), M["sky_i"], I, cyclic=True)
            G.stroke(d, hose([(0.46, 0.0), (0.5, 0.0)], 0.022), M["sky_i"], I, cyclic=True)
        else:                                                                                # Mk3: two separate anchors side by
            G.stroke(d, hose([(0.24, -0.075), (0.24, 0.075)], 0.03), M["sky_sh_i"], I, cyclic=True)   # side, flukes curving back (rev
            for dz in (0.075, -0.075):                                                       # 19:2x, LEAD: overlapped heads read
                G.stroke(d, hose([(0.24, dz), (0.44, dz)], 0.024), M["sky_sh_i"], I, cyclic=True)   # as a trident)
                for side in (-1, 1):
                    G.stroke(d, hose([(0.45, dz), (0.42, dz + side * 0.04), (0.37, dz + side * 0.045)], 0.018), M["sky_i"], I, cyclic=True)
                G.stroke(d, circ_pts(0.455, dz, 0.014), M["sky_i"], I, cyclic=True)
        if mk >= 2:                                                                          # Mk2+: brass fittings
            G.stroke(d, [(0.2, -0.03), (0.25, -0.03), (0.25, 0.03), (0.2, 0.03)], M["mustard_i"], I, cyclic=True)
    return fn


# ---------------------------------------------------------------- B-217: the Survey and the Builder (forearm-strapped, no grip)
def cuff(d, M, r):
    """The arm cuff at the hand, as the Beam's: brown, two brass straps."""
    G.stroke(d, [(-0.06, -r - 0.035), (0.06, -r - 0.035), (0.06, r + 0.035), (-0.06, r + 0.035)], M["brown_i"], O, cyclic=True)
    for x in (-0.025, 0.025):
        G.stroke(d, [(x - 0.008, -r - 0.035), (x + 0.008, -r - 0.035), (x + 0.008, r + 0.035), (x - 0.008, r + 0.035)], M["mustard"], 0.0, cyclic=True)


def tool_cable(x0, z0=0.0):
    """A cable from the case's back end, backward and up toward the pack (its end: the json's cable_socket)."""
    return [(x0 - 0.01, z0), (x0 - 0.07, z0 + 0.03), (x0 - 0.12, z0 + 0.08), (x0 - 0.15, z0 + 0.14)]


SURVEY_CABLE = tool_cable(-0.07, 0.01)
BUILDER_CABLE = tool_cable(-0.07, 0.0)


def survey_tool():
    """The Survey: a teal instrument case on the forearm, a brass compass dial on top, a short whip aerial with a red tip,
    a small brass dish at the front (its focus = the muzzle (0.30, 0.06)). Nothing under the body."""
    def fn(d, M):
        G.stroke(d, hose(SURVEY_CABLE, 0.028), M["brown_sh_i"], I, cyclic=True)
        G.stroke(d, hose([(0.03, 0.08), (0.0, 0.13), (-0.025, 0.17)], 0.012), M["sky_sh_i"], I, cyclic=True)    # the aerial (rev: its
        G.stroke(d, circ_pts(-0.027, 0.18, 0.017, 10), M["red_i"], I, cyclic=True)          # tip touched the frame's top)
        body = [(-0.06, -0.05), (0.19, -0.05), (0.215, -0.025), (0.215, 0.065), (0.19, 0.085), (-0.06, 0.085)]
        G.stroke(d, body, M["teal_sh_i"], O, cyclic=True)                                    # the case
        G.stroke(d, [(-0.06, 0.03), (0.215, 0.03), (0.215, 0.065), (0.19, 0.085), (-0.06, 0.085)], M["teal"], 0.0, cyclic=True)
        G.stroke(d, body, M["ink"], O, cyclic=True)
        cuff(d, M, 0.05)
        G.stroke(d, circ_pts(0.135, 0.095, 0.055, 22), M["mustard_i"], I, cyclic=True)      # the compass dial on top, clear of the
        G.stroke(d, circ_pts(0.135, 0.095, 0.04, 18), M["sky_i"], I, cyclic=True)           # cuff; a pale glass face and a long
        a_n = math.radians(50)                                                               # diagonal needle (rev: a white face with
        ux, uz = math.cos(a_n), math.sin(a_n)                                                # a dark centre read as an eye)
        G.stroke(d, [(0.135 + 0.034 * ux, 0.095 + 0.034 * uz), (0.135 - 0.006 * uz, 0.095 + 0.006 * ux),
                     (0.135 - 0.026 * ux, 0.095 - 0.026 * uz), (0.135 + 0.006 * uz, 0.095 - 0.006 * ux)], M["red_i"], I * 0.5, cyclic=True)
        G.stroke(d, hose([(0.215, 0.035), (0.262, 0.05)], 0.022), M["sky_sh_i"], I, cyclic=True)   # the dish's arm
        outer = [(0.37 + 0.105 * math.cos(a), 0.06 + 0.105 * math.sin(a)) for a in np.linspace(math.radians(128), math.radians(232), 13)]
        inner = [(0.37 + 0.088 * math.cos(a), 0.06 + 0.088 * math.sin(a)) for a in np.linspace(math.radians(232), math.radians(128), 13)]
        G.stroke(d, outer + inner, M["mustard_i"], I, cyclic=True)                          # the dish: a brass "(" open forward (rev: the
        G.stroke(d, hose([(0.283, 0.06), (0.3, 0.06)], 0.009), M["sky_sh_i"], I * 0.6, cyclic=True)   # crescent + rim read as a bow-tie)
        G.stroke(d, circ_pts(0.3, 0.06, 0.013, 10), M["teal_i"], I, cyclic=True)             # the pick-up at its focus = the muzzle
    return fn


def builder_tool():
    """The Builder: a wooden dirt hopper on the forearm, dirt heaped in its mouth, a steel scoop forward whose lip is the muzzle
    (0.44, 0.03); a dirt hose back to the pack (the dirt store). A scoop, not a barrel: nothing flares, nothing hangs below."""
    def fn(d, M):
        G.stroke(d, hose(BUILDER_CABLE, 0.034), M["brown_sh_i"], I, cyclic=True)           # the dirt hose
        for x, z, rr in ((0.0, 0.085, 0.045), (0.07, 0.1, 0.05), (0.15, 0.088, 0.042)):    # dirt heaped high in the crate's open top
            G.stroke(d, IT.lump(x, z, rr, rr * 0.75, int(x * 100) + 7, n=10, jit=0.12), M["brown_i"], I, cyclic=True)
        box = [(-0.07, -0.075), (0.2, -0.075), (0.2, 0.08), (-0.07, 0.08)]                   # rev: a taller plank crate (the long thin
        G.stroke(d, box, M["mustard_sh_i"], O, cyclic=True)                                  # pointed version read as a long gun)
        for x in (0.02, 0.11):
            G.seam(d, [(x, -0.07), (x, 0.075)], M["ink"])
        G.stroke(d, [(-0.07, -0.02), (0.2, -0.02), (0.2, 0.005), (-0.07, 0.005)], M["sky_sh_i"], I, cyclic=True)   # an iron band
        cuff(d, M, 0.065)
        bowl = [(0.2, 0.06), (0.2, -0.06)] + [(0.33 + 0.11 * math.cos(a), 0.0 + 0.075 * math.sin(a)) for a in np.linspace(-math.pi * 0.62, 0.32, 10)]
        G.stroke(d, bowl, M["sky_sh_i"], O, cyclic=True)                                     # the scoop: a deep round bowl, its lip
        for x, z, rr in ((0.27, 0.07, 0.04), (0.34, 0.075, 0.045), (0.405, 0.05, 0.032)):  # (0.44, 0.03) up front; dirt piled in it
            G.stroke(d, IT.lump(x, z, rr, rr * 0.75, int(x * 100) + 3, n=10, jit=0.12), M["brown_i"], I, cyclic=True)
    return fn


def survey_scan(k):
    """Frame k of 12 (240x240 @ PPU 128 = 1.875 m; PlayerRigInput plays it at scale 2 at the chest): an ink pulse ring in teal
    expanding with compass ticks, a fainter echo behind it, breaking into dashes as it fades. No glow."""
    def fn(d, M):
        t = k / 11.0
        R = 0.12 + 0.72 * math.sqrt(t)
        bw = 0.05 * (1 - t) + 0.014
        n = 96
        if k <= 1:                                                                           # the ping at the centre
            s = (0.11, 0.07)[k]
            st = [((s if j % 2 == 0 else s * 0.35) * math.cos(TAU * j / 8), (s if j % 2 == 0 else s * 0.35) * math.sin(TAU * j / 8)) for j in range(8)]
            G.stroke(d, st, M["teal_i"], I, cyclic=True)
        if k >= 3:                                                                           # the echo
            r2 = R * 0.62
            G.stroke(d, circ_pts(0, 0, r2, n), M["ink"], I * 0.6, cyclic=True)
        dashes = k >= 8
        seg = 24
        for j in range(seg):
            if dashes and j % 2:
                continue
            a0, a1 = TAU * j / seg, TAU * (j + 1) / seg - (0.06 if dashes else 0.0)
            outer = [((R + bw / 2) * math.cos(a), (R + bw / 2) * math.sin(a)) for a in np.linspace(a0, a1, 5)]
            inner = [((R - bw / 2) * math.cos(a), (R - bw / 2) * math.sin(a)) for a in np.linspace(a1, a0, 5)]
            G.stroke(d, outer + inner, M["teal"], 0.0, cyclic=True)
            if dashes:
                G.stroke(d, outer + inner, M["ink"], I * 0.7, cyclic=True)
        if not dashes:
            G.stroke(d, circ_pts(0, 0, R + bw / 2, n), M["ink"], I, cyclic=True)
            G.stroke(d, circ_pts(0, 0, R - bw / 2, n), M["ink"], I * 0.8, cyclic=True)
        if 2 <= k <= 8:                                                                      # compass ticks outside the ring
            for j in range(8):
                a = TAU * j / 8
                L = 0.05 if j % 2 == 0 else 0.03
                G.stroke(d, [((R + bw / 2 + 0.015) * math.cos(a), (R + bw / 2 + 0.015) * math.sin(a)),
                             ((R + bw / 2 + 0.015 + L) * math.cos(a), (R + bw / 2 + 0.015 + L) * math.sin(a))], M["ink"], I * 1.2)
    return fn


def builder_ghost(k):
    """Frame k of 8 (144x144 @ PPU 128; RigToolView scales the sprite to one tile): ink corner brackets and a dashed cream
    outline marching round the tile, a small plus at its centre. Cream + ink, so the Blocked tint (red) reads through."""
    def fn(d, M):
        h = 0.47                                                                             # the outline's half side (60 px)
        per = 0.12
        L = 8 * h
        ph = per * k / 8
        pts = [(-h, -h), (h, -h), (h, h), (-h, h)]

        def at(s):
            s %= L
            side = int(s // (2 * h))
            u = s - side * 2 * h
            (x0, z0), (x1, z1) = pts[side], pts[(side + 1) % 4]
            return (x0 + (x1 - x0) * u / (2 * h), z0 + (z1 - z0) * u / (2 * h))
        s = ph
        while s < L + ph - 1e-6:                                                             # marching dashes (cream, inked)
            seg = [at(s + per * 0.55 * i / 4) for i in range(5)]
            G.stroke(d, hose(seg, 0.022), M["off_i"], I * 0.8, cyclic=True)
            s += per
        c = 0.13
        for sx in (-1, 1):                                                                   # the corner brackets
            for sz in (-1, 1):
                G.stroke(d, hose([(sx * (h + 0.02), sz * (h + 0.02 - c)), (sx * (h + 0.02), sz * (h + 0.02)), (sx * (h + 0.02 - c), sz * (h + 0.02))], 0.03),
                         M["off_i"], I, cyclic=True)
        for a, b in (((-0.06, 0.0), (0.06, 0.0)), ((0.0, -0.06), (0.0, 0.06))):            # the centre plus
            G.stroke(d, hose([a, b], 0.022), M["off_i"], I * 0.8, cyclic=True)
    return fn


def fx_sheet(frames, cols):
    fh, fw = frames[0].shape[:2]
    rows = -(-len(frames) // cols)
    g = 4
    sheet = np.zeros((rows * fh + (rows - 1) * g, cols * fw + (cols - 1) * g, 4), np.uint8)
    for i, f in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw] = f
    return sheet


# ---------------------------------------------------------------- the jetpack overlays, Mk2-3 (metres from the pack's centre)
def jetpack(mk):
    def fn(d, M):
        if mk == 2:                                                                          # Mk2: one steel tank, a nozzle
            IT._tank(d, M, -0.2, 0.06, -0.2, 0.24, "sky_sh", "sky_dp", nozzle="sky_sh")
        else:                                                                                # Mk3: one fat teal fuel tank, gold
            IT._tank(d, M, -0.2, 0.085, -0.2, 0.26, "teal", "teal_sh", nozzle="mustard_sh")    # bands, steel side fins (rev 19:1x: two
            for z in (0.12, -0.08):                                                          # thin mustard tanks + red fins read as
                G.stroke(d, [(-0.29, z - 0.018), (-0.11, z - 0.018), (-0.11, z + 0.018), (-0.29, z + 0.018)], M["mustard_i"], I, cyclic=True)   # dynamite)
            for s in (-1, 1):
                G.stroke(d, [(-0.2 + s * 0.085, -0.06), (-0.2 + s * 0.15, -0.2), (-0.2 + s * 0.085, -0.16)], M["sky_i"], I, cyclic=True)
        for z in (0.16, -0.12):                                                              # the straps over the pack
            G.stroke(d, [(-0.3, z - 0.02), (0.12, z - 0.02), (0.12, z + 0.02), (-0.3, z + 0.02)], M["brown_i"], I, cyclic=True)
    return fn


def side_poses():
    """characters/surveyor/side's 98 poses in sheet order (build_surveyor_v3's clips)."""
    sys.path.insert(0, HERE)
    import build_surveyor_v3 as SV
    return [SV.idle_pose(i) for i in range(10)] + [SV.walk_pose(i) for i in range(12)] + SV.JUMP + SV.LAND + \
        [SV.look_pose(i) for i in range(12)] + SV.BUMP + SV.CONK + [SV.run_pose(i) for i in range(12)] + \
        [SV.fall_pose(i) for i in range(8)] + SV.DASH


def back_sockets():
    """Per frame of characters/surveyor/side: [x, z, angle, sx, sz] of the float pack's centre (build_surveyor_v3's X and PK)."""
    return [_socket(pose) for pose in side_poses()]


def _hand(pose):
    """UNITY's U-183 request: [x, z, angle_rad] of the FRONT glove's centre (draw_surveyor's arm(1): the hand point 0.04 m above
    the glove's centre) in metres from the sheet pivot (the feet; x right, z up, facing right), and the forearm's direction (the
    arm bezier's tangent at the hand, rad CCW from +x). None in the front view (no front hand) and where the surveyor is hidden."""
    p = dict(view="side", bob=0.0, sz=1.0, lean=0.0, shift=0.0, arms=(0.0, 0.0))
    p.update(pose)
    if p["view"] not in ("side", "tq") or p.get("hidden"):
        return None
    sz = p["sz"]
    sx = 1.0 / math.sqrt(sz)

    def X1(x, z, pivot_z=0.55):
        return ((x * sx) + p["lean"] * (z - pivot_z) + p["shift"], pivot_z + (z - pivot_z) * sz + p["bob"])
    ang = p["arms"][1]
    if p["view"] == "side":
        sh = X1(0.04, 1.00)
        h = (sh[0] + 0.42 * math.sin(ang), sh[1] - 0.42 * math.cos(ang))
        mid = ((sh[0] + h[0]) / 2 - 0.06, (sh[1] + h[1]) / 2 + 0.02)
    else:
        sh = X1(0.30, 1.00)
        h = (sh[0] + 0.16 + 0.10 * abs(math.sin(ang)), sh[1] - 0.42 * math.cos(ang * 0.6))
        mid = ((sh[0] + h[0]) / 2 + 0.07, (sh[1] + h[1]) / 2 + 0.03)
    return [round(h[0], 4), round(h[1] - 0.04, 4), round(math.atan2(h[1] - mid[1], h[0] - mid[0]), 4)]


def hand_sockets():
    return [_hand(pose) for pose in side_poses()]


def hand_sockets_b():
    """The same for characters/surveyor/side_b, plus per frame what the sheet already draws in or on that hand (None = nothing):
    the Beam strapped on (climb_ladder / reel_up), the reel, a pick, a hammer - UNITY skips its held tool there."""
    sys.path.insert(0, HERE)
    import build_surveyor_side_b as SB
    poses = SB.all_poses()
    held = []
    for pose in poses:
        h = [k for k in ("beam_arm", "reel", "pick", "hammer") if pose.get(k) not in (None, False)]
        held.append("+".join(h) if h else None)
    return [_hand(pose) for pose in poses], held


def back_sockets_b():
    """B-210: the same for characters/surveyor/side_b's frames (dig ... climb_in, climb_ladder, reel_up); null where the
    surveyor is hidden (climb_in's vanish)."""
    sys.path.insert(0, HERE)
    import build_surveyor_side_b as SB
    return [None if pose.get("hidden") else _socket(pose) for pose in SB.all_poses()]


def _socket(pose):
    """[x, z, swing, sx, sz] of the float pack's centre for one pose (build_surveyor_v3's X and PK), None in the front views."""
    p = dict(view="side", bob=0.0, sz=1.0, lean=0.0, shift=0.0, pack_swing=0.0, pack_dz=0.0)
    p.update(pose)
    if p["view"] not in ("side", "tq"):
        return None
    sz = p["sz"]
    sx = 1.0 / math.sqrt(sz)

    def X1(x, z, pivot_z=0.55):
        return ((x * sx) + p["lean"] * (z - pivot_z) + p["shift"], pivot_z + (z - pivot_z) * sz + p["bob"])
    px = -0.36 if p["view"] == "side" else -0.33
    strap = X1(px + 0.02, 1.14)
    sw, pdz = p["pack_swing"], p["pack_dz"]
    c = X1(px, 0.92)
    cs, sn = math.cos(sw), math.sin(sw)
    cx = strap[0] + (c[0] - strap[0]) * cs - (c[1] - strap[1]) * sn
    cz = strap[1] + (c[0] - strap[0]) * sn + (c[1] - strap[1]) * cs + pdz
    return [round(cx, 4), round(cz, 4), round(sw, 4), round(sx, 4), round(sz, 4)]


# ---------------------------------------------------------------- the export (on LEAD's OK)
def cable_socket(mk):
    return [round(v, 3) for v in cable_path(mk)[-1]]


def kit():
    """[(key, rgba, meta extras)]: the tools (props/rig/beam and props/rig/grapple are the Mk1 copies, the keys RigModules
    loads), the jetpack overlays with their back sockets, the beam ray sheets (2 columns x 4 rows, gutter 4)."""
    out = []
    for mk in range(1, 6):
        img = render(beam_tool(mk), TW, TH, TPPU, TPIV)[0]
        meta = {"ppu": TPPU, "pivot": list(TPIV), "muzzle": list(MUZZLE["beam"]), "cable_socket": cable_socket(mk), "mk": mk,
                "ray": f"fx/beam_ray/mk{mk}", "note": "B-205: the Beam, arm-mounted and cable-fed (no grip or trigger: a mining tool, D-087)"}
        out.append((f"props/rig/beam_mk{mk}", img, meta))
        if mk == 1:
            out.append(("props/rig/beam", img, dict(meta, note="B-205: = beam_mk1 (the key RigModules loads); replaces the v2 render")))
    for mk in range(1, 4):
        img = render(grapple_tool(mk), TW, TH, TPPU, TPIV)[0]
        meta = {"ppu": TPPU, "pivot": list(TPIV), "muzzle": list(MUZZLE["grapple"]), "mk": mk,
                "note": "B-205: the Grapple, a hand reel with the hook seated forward (no barrel)" + ("; twin anchors" if mk == 3 else "")}
        out.append((f"props/rig/grapple_mk{mk}", img, meta))
        if mk == 1:
            out.append(("props/rig/grapple", img, dict(meta, note="B-205: = grapple_mk1 (RigModules.ArtKey(Grapple)); replaces the Lance stand-in (U-183)")))
    for name, fn, cab, note in (("survey", survey_tool(), SURVEY_CABLE, "B-217: the Survey, a forearm-strapped instrument case: compass dial, "
                                 "whip aerial, a brass dish at the front (its focus = the muzzle); no grip; replaces the v2 render"),
                                ("builder", builder_tool(), BUILDER_CABLE, "B-217: the Builder, a forearm-strapped dirt hopper with a steel scoop "
                                 "forward (its lip = the muzzle) and a dirt hose to the pack; no grip, nothing flared; replaces the v2 render")):
        img = render(fn, TW, TH, TPPU, TPIV)[0]
        out.append((f"props/rig/{name}", img, {"ppu": TPPU, "pivot": list(TPIV), "muzzle": list(MUZZLE[name]),
                                                "cable_socket": [round(v, 3) for v in cab[-1]], "note": note}))
    scan = [render(survey_scan(k), 240, 240, TPPU, (0.5, 0.5))[0] for k in range(12)]
    out.append(("fx/survey_scan/base", fx_sheet(scan, 4), {"ppu": TPPU, "frame_width": 240, "frame_height": 240, "columns": 4, "gutter": 4,
                                                          "frames": 12, "fps": 12, "pivot": [0.5, 0.5], "facing": "right",
                                                          "animations": [{"name": "pulse", "start": 0, "length": 12, "loop": False}], "_frames": scan,
                                                          "note": "B-217: the Survey's scan - a teal ink pulse ring with compass ticks and an echo, "
                                                                  "breaking into dashes as it fades (no glow; v3 replaces B-037)"}))
    ghost = [render(builder_ghost(k), 144, 144, TPPU, (0.5, 0.5))[0] for k in range(8)]
    out.append(("fx/builder_ghost/base", fx_sheet(ghost, 4), {"ppu": TPPU, "frame_width": 144, "frame_height": 144, "columns": 4, "gutter": 4,
                                                             "frames": 8, "fps": 8, "pivot": [0.5, 0.5], "facing": "right",
                                                             "animations": [{"name": "idle", "start": 0, "length": 8, "loop": True}], "_frames": ghost,
                                                             "note": "B-217: the Builder's placement ghost (tile planets; RigToolView scales it to one tile) - "
                                                                     "cream dashes marching round the tile, ink-edged corner brackets; the Blocked tint reads through"}))
    socks = back_sockets()
    for mk in (2, 3):
        img = render(jetpack(mk), 64, 64, 64, (0.5, 0.5))[0]
        out.append((f"props/rig/jetpack_mk{mk}", img, {"ppu": 64, "pivot": [0.5, 0.5], "mk": mk, "socket_sheet": "characters/surveyor/side",
                                                       "back_socket": socks, "socket_sheet_b": "characters/surveyor/side_b",
                                                       "back_socket_b": back_sockets_b(),                       # B-210: side_b's frames too
                                                       "socket_units": "per sheet frame: [x, z] m from the sheet's pivot (the feet; x right, z up, facing right), the pack's swing (rad, CCW), the body's squash sx / sz; null = the pack hidden (front views)",
                                                       "note": "B-205: drawn over the surveyor at the frame's back socket (mirror x when facing left); Mk1 is the float pack as drawn"}))
    for mk in range(1, 6):
        frames = [render(beam_ray(mk, k), 256, 32, TPPU, (0.0, 0.5))[0] for k in range(8)]
        sheet = np.zeros((4 * 32 + 3 * 4, 2 * 256 + 4, 4), np.uint8)
        for k, f in enumerate(frames):
            r, c = divmod(k, 2)
            sheet[r * 36:r * 36 + 32, c * 260:c * 260 + 256] = f
        out.append((f"fx/beam_ray/mk{mk}", sheet, {"ppu": TPPU, "frame_width": 256, "frame_height": 32, "columns": 2, "gutter": 4, "frames": 8, "fps": 12,
                                                  "pivot": [0.0, 0.5], "facing": "right", "tile_x": True,
                                                  "animations": [{"name": "flow", "start": 0, "length": 8, "loop": True}],
                                                  "note": f"B-205: the Beam Mk{mk}'s ray (teal to gold with the Mk), tiled in x from the muzzle; 0.25 m tall"}))
    return out


V2_REMOVE = ["props/rig/beam_normal.png", "props/rig/beam_emission.png",          # the v2 maps (UNITY deletes the .meta files)
             "props/rig/survey_normal.png", "props/rig/survey_emission.png", "props/rig/builder_normal.png", "props/rig/builder_emission.png",
             "fx/survey_scan/base_emission.png", "fx/builder_ghost/base_emission.png"]                                  # (B-217)


def export(art):
    import json
    from meridian import pngio
    built, problems = [], []
    for key, img, extra_meta in kit():
        h, w = img.shape[:2]
        frames = extra_meta.pop("_frames", None)
        meta = {"key": key, "style": "v3", "width": w, "height": h, "palette": "earth", **extra_meta}
        hit = v3.palette_hits(img, "earth")[0]
        m = v3.EDGE_MARGIN
        for i, f in enumerate(frames or []):                                                 # B-217: framed fx, each frame clear
            if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any():
                problems.append(f"{key} frame {i}: touches the {m} px edge")
        if w % 4 or h % 4:
            problems.append(f"{key}: {w}x{h} not a multiple of 4")
        if hit < 0.995:
            problems.append(f"{key}: palette {hit * 100:.1f}%")
        if not key.startswith("fx/") and (img[:m, :, 3].any() or img[-m:, :, 3].any() or img[:, :m, 3].any() or img[:, -m:, 3].any()):
            problems.append(f"{key}: touches the {m} px edge")
        built.append((key, img, meta))
    if problems:
        raise ValueError("B-205 tool checks: " + "; ".join(problems))
    out = []
    for key, img, meta in built:
        base = os.path.join(art, *key.split("/"))
        os.makedirs(os.path.dirname(base), exist_ok=True)
        n = pngio.write_png(base + "_color.png", img)
        with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((key, img.shape[1], img.shape[0], n))
    for rel in V2_REMOVE:
        p = os.path.join(art, *rel.split("/"))
        if os.path.isfile(p):
            os.remove(p)
    hs, (hsb, held_b) = hand_sockets(), hand_sockets_b()                                      # U-183: the front hand, json only
    hmeta = {"key": HAND_KEY, "style": "v3", "socket_sheet": "characters/surveyor/side", "hand_socket": hs,
             "socket_sheet_b": "characters/surveyor/side_b", "hand_socket_b": hsb, "held_b": held_b,
             "socket_units": "per sheet frame: [x, z] m from the sheet's pivot (the feet; x right, z up, facing right) to the front glove's "
                             "centre, and the forearm's direction (rad, CCW from +x); null = no front hand drawn (front views, hidden)",
             "note": "U-183 (B-205's tools at the drawn hand): put the tool's pivot (its json pivot = the hand) here, mirrored in x when facing "
                     "left; held_b names what side_b already draws in that hand (beam_arm = the Beam strapped on, reel, pick, hammer): no held tool there"}
    p = os.path.join(art, *HAND_KEY.split("/")) + ".json"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(hmeta, f, indent=2)
        f.write("\n")
    out.append((HAND_KEY, 0, 0, os.path.getsize(p)))
    return out


HAND_KEY = "props/rig/hand_socket"


def keys():
    return [k for k, _i, _m in [(f"props/rig/beam_mk{m}", 0, 0) for m in range(1, 6)] + [("props/rig/beam", 0, 0)]
            + [(f"props/rig/grapple_mk{m}", 0, 0) for m in range(1, 4)] + [("props/rig/grapple", 0, 0)]
            + [(f"props/rig/jetpack_mk{m}", 0, 0) for m in (2, 3)] + [(f"fx/beam_ray/mk{m}", 0, 0) for m in range(1, 6)]
            + [("props/rig/survey", 0, 0), ("props/rig/builder", 0, 0), ("fx/survey_scan/base", 0, 0), ("fx/builder_ghost/base", 0, 0)]
            + [(HAND_KEY, 0, 0)]]


# ---------------------------------------------------------------- the review sheet (lock-free)
def preview(out, footnote=None):
    import time
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art")
    sheet = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))
    FW = FH = 192
    COLS, GUT = 10, 4

    def frame(i):
        r, c = divmod(i, COLS)
        return sheet[r * (FH + GUT):r * (FH + GUT) + FH, c * (FW + GUT):c * (FW + GUT) + FW]

    def scale_half(img):                                                                     # PPU 128 tool -> the surveyor's 64
        return np.rint(img.astype(np.float32).reshape(img.shape[0] // 2, 2, img.shape[1] // 2, 2, 4).mean(axis=(1, 3))).astype(np.uint8)

    def rotate(img, deg, piv):
        """Nearest-neighbour rotation about piv (px) into a larger canvas -> (img, new pivot)."""
        h, w = img.shape[:2]
        R = int(math.ceil(math.hypot(w, h)))
        outi = np.zeros((2 * R, 2 * R, 4), np.uint8)
        yy, xx = np.mgrid[0:2 * R, 0:2 * R]
        a = math.radians(deg)
        u = (xx - R) * math.cos(a) - (yy - R) * math.sin(a) + piv[0]                          # y down: a positive deg turns it up
        v = (xx - R) * math.sin(a) + (yy - R) * math.cos(a) + piv[1]
        ok = (u >= 0) & (u < w) & (v >= 0) & (v < h)
        outi[ok] = img[v[ok].astype(int), u[ok].astype(int)]
        return outi, (R, R)
    paper = np.array(review.PAPER, np.float32)
    bg = np.array(v3.hex_rgb(v3.PALETTES["earth"]["sky"]), np.float32) / 255.0

    class _R:                                                                                # review._over without the clip: wrap it
        @staticmethod
        def _over(dst, fr, x, y):
            h, w = fr.shape[:2]
            x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
            if x1 > x0 and y1 > y0:
                f = fr[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32) / 255.0
                a = f[..., 3:4]
                dst[y0:y1, x0:x1] = f[..., :3] * a + dst[y0:y1, x0:x1] * (1 - a)
    _over = _R._over
    W = 1500
    rows = []
    head = np.tile(paper, (28, W, 1)).astype(np.float32)
    review._label(head, "B-205 the tools by tier on the surveyor at 1x: Beam Mk1-5 (cable-fed, arm-mounted, no grip), Grapple Mk1-3 (a hand reel), jetpack Mk1-3", 6, 8)
    rows.append(head)
    HAND = (0.12, 0.95)                                                                      # RigToolView.Hand (m from the feet)

    def scene_row(label, items):
        r = np.empty((FH + 40, W, 3), np.float32)
        r[:] = bg
        review._label(r, label, 6, 4, scale=1)
        for k, (cap, fidx, tool, ray, aim, over, sock) in enumerate(items):
            x0 = 10 + k * 290
            f = frame(fidx)
            _over(r, f, x0, 24)
            fx, fz = x0 + FW // 2, 24 + FH                                                    # the feet (pivot 0.5, 0)
            if over is not None and sock is not None:                                         # a jetpack overlay on the back socket
                ox, oz, ang, _sx, _sz = sock
                oimg, opiv = rotate(over, math.degrees(ang), (32, 32))
                _over(r, oimg, int(fx + ox * 64 - opiv[0]), int(fz - oz * 64 - opiv[1]))
            if tool is not None:
                t = scale_half(tool)
                timg, tpiv = rotate(t, aim, (TW * TPIV[0] / 2, TH * TPIV[1] / 2))
                hx, hy = fx + HAND[0] * 64, fz - HAND[1] * 64
                _over(r, timg, int(hx - tpiv[0]), int(hy - tpiv[1]))
                if ray is not None:                                                           # the ray from the muzzle, 1.5 m
                    a = math.radians(aim)
                    mx, my = hx + 0.47 * 64 * math.cos(a), hy - 0.47 * 64 * math.sin(a)
                    rr = scale_half(np.tile(ray, (1, 1, 1)))[:, :96]
                    rimg, rpiv = rotate(rr, aim, (0, rr.shape[0] / 2))
                    _over(r, rimg, int(mx - rpiv[0]), int(my - rpiv[1]))
            review._label(r, cap, x0 + 4, FH + 26, scale=1)
        return r
    beams = [render(beam_tool(m), TW, TH, TPPU, TPIV)[0] for m in range(1, 6)]
    rays = [render(beam_ray(m, 0), 256, 32, TPPU, (0.0, 0.5))[0] for m in range(1, 6)]
    rows.append(scene_row("Beam Mk1-5 (the ray in the Mk's tone, aimed 10 degrees down)", [(f"beam_mk{m}", 0, beams[m - 1], rays[m - 1], -10, None, None) for m in range(1, 6)]))
    grs = [render(grapple_tool(m), TW, TH, TPPU, TPIV)[0] for m in range(1, 4)]
    socks = back_sockets()
    jets = {m: render(jetpack(m), 64, 64, 64, (0.5, 0.5))[0] for m in (2, 3)}
    rows.append(scene_row("Grapple Mk1-3 (aimed 25 degrees up) | jetpack Mk2 / Mk3 on the back socket (idle 0, walk 3)",
                          [(f"grapple_mk{m}", 0, grs[m - 1], None, 25, None, None) for m in range(1, 4)]
                          + [("jetpack_mk2 idle", 0, None, None, 0, jets[2], socks[0]), ("jetpack_mk3 walk", 13, None, None, 0, jets[3], socks[13])]))
    rows.append(scene_row("jetpack Mk3 through jump 1, run 4, dash 2, land 0 (the socket follows the pack's swing)",
                          [(f"frame {i}", i, None, None, 0, jets[3], socks[i]) for i in (23, 70, 94, 30)]))
    zoom = np.tile(paper, (2 * (TH * 2 + 40), W, 1)).astype(np.float32)                       # every sprite at 2x, two rows
    x, y = 8, 0
    for name, img in [(f"beam_mk{m}", beams[m - 1]) for m in range(1, 6)] + [(f"grapple_mk{m}", grs[m - 1]) for m in range(1, 4)] + \
                     [(f"jetpack_mk{m}", jets[m]) for m in (2, 3)]:
        im2 = np.repeat(np.repeat(img, 2, 0), 2, 1)
        if x + im2.shape[1] > W:
            x, y = 8, y + TH * 2 + 40
        _over(zoom, im2, x, y + 24)
        review._label(zoom, name, x, y + 6, scale=1)
        x += im2.shape[1] + 10
    rows.append(zoom)
    lines = []
    for name, img in [(f"props/rig/beam_mk{m}", beams[m - 1]) for m in range(1, 6)] + [(f"fx/beam_ray_mk{m}", rays[m - 1]) for m in range(1, 6)] + \
                     [(f"props/rig/grapple_mk{m}", grs[m - 1]) for m in range(1, 4)] + [(f"props/rig/jetpack_mk{m}", jets[m]) for m in (2, 3)]:
        hit = v3.palette_hits(img, "earth")[0] * 100
        m_ = v3.EDGE_MARGIN
        ray_ = "beam_ray" in name
        edge = img[:m_, :, 3].any() or img[-m_:, :, 3].any() or (not ray_ and (img[:, :m_, 3].any() or img[:, -m_:, 3].any()))
        lines.append(f"{name}: {img.shape[1]}x{img.shape[0]}, palette {hit:.1f}%" + ("; EDGE" if edge else ""))
    lines.append(f"back sockets: {sum(1 for s in socks if s)} of {len(socks)} frames (the front views hide the pack)")
    foot = np.tile(paper, (24 + 16 * ((len(lines) + 1) // 2), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6 + (i % 2) * 740, 6 + 16 * (i // 2), scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)
    if footnote:                                                                             # the export: B-217's sheet, stamped too
        preview_b217(os.path.join(os.path.dirname(out), "review_b217_survey_builder.png"), footnote)


def _half(img):
    """PPU 128 art -> the surveyor's 64 (2x2 means)."""
    h, w = img.shape[0] // 2 * 2, img.shape[1] // 2 * 2
    return np.rint(img[:h, :w].astype(np.float32).reshape(h // 2, 2, w // 2, 2, 4).mean(axis=(1, 3))).astype(np.uint8)


def _rot(img, deg, piv):
    h, w = img.shape[:2]
    R = int(math.ceil(math.hypot(w, h)))
    outi = np.zeros((2 * R, 2 * R, 4), np.uint8)
    yy, xx = np.mgrid[0:2 * R, 0:2 * R]
    a = math.radians(deg)
    u = (xx - R) * math.cos(a) - (yy - R) * math.sin(a) + piv[0]
    v = (xx - R) * math.sin(a) + (yy - R) * math.cos(a) + piv[1]
    ok = (u >= 0) & (u < w) & (v >= 0) & (v < h)
    outi[ok] = img[v[ok].astype(int), u[ok].astype(int)]
    return outi, (R, R)


def _ov(dst, fr, x, y, tint=None):
    h, w = fr.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 > x0 and y1 > y0:
        f = fr[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32) / 255.0
        rgb = f[..., :3] * (tint if tint is not None else 1.0)
        a = f[..., 3:4]
        dst[y0:y1, x0:x1] = rgb * a + dst[y0:y1, x0:x1] * (1 - a)


def preview_b217(out, footnote=None):
    """B-217's sheet: the Survey and the Builder on the surveyor (as RigToolView holds them), the scan at its in-game size over
    the surveyor's chest, the builder ghost at one tile (white and Blocked-red), everything at 2x."""
    import time
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art")
    side = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))
    FW = FH = 192
    surv = side[:FH, :FW]
    paper = np.array(review.PAPER, np.float32)
    pal = {k: np.array(v3.hex_rgb(v), np.float32) / 255.0 for k, v in v3.PALETTES["earth"].items()}
    K = {k: (img, m) for k, img, m in kit() if k in ("props/rig/survey", "props/rig/builder", "fx/survey_scan/base", "fx/builder_ghost/base")}
    scan, ghost = K["fx/survey_scan/base"][1]["_frames"], K["fx/builder_ghost/base"][1]["_frames"]
    W = 1560
    rows = []
    head = np.tile(paper, (28, W, 1)).astype(np.float32)
    review._label(head, "B-217 the Survey and the Builder (forearm-strapped, no grip), the scan pulse and the builder ghost, v3 ink; 1x = in game (64 px/m)", 6, 8)
    rows.append(head)
    HAND = (0.12, 0.95)
    r = np.empty((FH + 44, W, 3), np.float32)
    r[:] = pal["sky"]
    r[FH + 18:] = pal["green"]
    r[FH + 22:] = pal["brown"]
    review._label(r, "on the surveyor (RigToolView: the hand at (0.12, 0.95) m): Survey level / up 20; Builder level / down 30 (placing) - the muzzle dot in red", 6, 4, scale=1)
    for k, (name, aim) in enumerate((("survey", 0), ("survey", 20), ("builder", 0), ("builder", -30))):
        x0 = 10 + k * 300
        _ov(r, surv, x0, 24)
        fx, fz = x0 + FW // 2, 24 + FH
        t = _half(K[f"props/rig/{name}"][0])
        timg, tpiv = _rot(t, aim, (TW * TPIV[0] / 2, TH * TPIV[1] / 2))
        hx, hy = fx + HAND[0] * 64, fz - HAND[1] * 64
        _ov(r, timg, int(hx - tpiv[0]), int(hy - tpiv[1]))
        mx, mz = MUZZLE[name]
        a = math.radians(aim)
        px, py = hx + 64 * (mx * math.cos(a) - mz * math.sin(a)), hy - 64 * (mx * math.sin(a) + mz * math.cos(a))
        r[int(py) - 1:int(py) + 2, int(px) - 1:int(px) + 2] = pal["red"]
        review._label(r, f"{name} {aim:+d} deg", x0 + 4, FH + 26, scale=1)
    rows.append(r)
    per = 6
    for half in (0, 1):                                                                       # the scan, 1x, over the chest
        rr = np.empty((260, W, 3), np.float32)
        rr[:] = pal["sky"]
        rr[236:] = pal["green"]
        rr[240:] = pal["brown"]
        if half == 0:
            review._label(rr, "fx/survey_scan/base at 1x (scale 2: 3.75 m), centred 0.9 m up the surveyor, frames 0-11", 6, 4, scale=1)
        for i in range(per):
            k = half * per + i
            x0 = 10 + i * 252
            _ov(rr, surv, x0 + 120 - 96, 240 - FH)
            _ov(rr, scan[k], x0, 240 - int(0.9 * 64) - 120)
            review._label(rr, f"{k}", x0 + 4, 22, scale=1)
        rows.append(rr)
    g = np.tile(paper, (180, W, 1)).astype(np.float32)                                        # the ghost: native, then one tile
    review._label(g, "fx/builder_ghost/base: frames 0-7 at native 1x (144 px), then at one tile (64 px) white and Blocked (red tint) over a dug cell", 6, 4, scale=1)
    for k, f in enumerate(ghost):
        cell = np.empty((144, 144, 3), np.float32)
        cell[:] = pal["brown"] * 0.6
        _ov(cell, f, 0, 0)
        g[22:166, 10 + k * 150:154 + k * 150] = cell
    rows.append(g)
    g2 = np.tile(paper, (100, W, 1)).astype(np.float32)
    small = []
    for f in ghost:
        s = f.astype(np.float32)
        h2 = 64
        idx = (np.arange(h2) * 144 / h2).astype(int)
        small.append(np.rint(s[idx][:, idx]).astype(np.uint8))
    for k, f in enumerate(small[:4]):
        for j, tint in enumerate((None, np.array([0.95, 0.35, 0.3], np.float32))):
            x0 = 10 + (k * 2 + j) * 90
            cell = np.empty((64, 64, 3), np.float32)
            cell[:] = pal["brown"] * 0.6
            _ov(cell, f, 0, 0, tint)
            g2[20:84, x0:x0 + 64] = cell
    rows.append(g2)
    z = np.tile(paper, (TH * 2 + 40, W, 1)).astype(np.float32)
    x = 10
    for name in ("survey", "builder"):
        im2 = np.repeat(np.repeat(K[f"props/rig/{name}"][0], 2, 0), 2, 1)
        _ov(z, im2, x, 24)
        review._label(z, f"props/rig/{name} at 2x (native 128 ppu)", x, 6, scale=1)
        x += im2.shape[1] + 30
    rows.append(z)
    lines = []
    m_ = v3.EDGE_MARGIN
    for key, (img, meta) in K.items():
        hit = v3.palette_hits(img, "earth")[0] * 100
        frs = meta.get("_frames") or [img]
        bad = [i for i, f in enumerate(frs) if f[:m_, :, 3].any() or f[-m_:, :, 3].any() or f[:, :m_, 3].any() or f[:, -m_:, 3].any()]
        lines.append(f"{key}: {img.shape[1]}x{img.shape[0]}, palette {hit:.1f}%" + (f"; EDGE {bad}" if bad else ""))
    foot = np.tile(paper, (24 + 16 * 2, W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6 + (i % 2) * 760, 6 + 16 * (i // 2), scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_rig_tools_v3.py <review png> [--b217]
    if "--b217" in sys.argv:
        preview_b217(sys.argv[1])
    else:
        preview(sys.argv[1])
    fakegp.restore()
