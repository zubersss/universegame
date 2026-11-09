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
MUZZLE = {"beam": (0.47, 0.03), "grapple": (0.52, 0.035)}
BEAM_TONES = {1: ("teal", "off"), 2: ("teal", "mustard"), 3: ("green", "off"), 4: ("mustard_sh", "off"), 5: ("mustard", "off")}


def render(fn, w, h, ppu, piv, seed=5):
    gp = fakegp.FakeGP()
    M = IT.mats(gp, "earth")
    d = fakegp.FakeDrawing()
    fn(d, M)
    return GR.render_frame(fakegp.strokes_of(d, gp), w, h, ppu, piv, ss=4, seed=seed)


def hose(pts, w):
    return G.hose_outline(pts, w)


# ---------------------------------------------------------------- the Beam, Mk1-5 (metres from the hand, +x the aim)
def beam_tool(mk):
    def fn(d, M):
        L = 0.24 + 0.035 * (mk - 1)                                                          # the body grows back from the nozzle
        r = 0.055 + 0.008 * (mk - 1)                                                         # and in girth
        x1 = 0.36                                                                            # the body's front (the nozzle beyond)
        x0 = x1 - L - 0.12
        G.stroke(d, hose([(x0 - 0.02, -0.01), (x0 - 0.12, -0.06), (x0 - 0.1, -0.15), (x0 + 0.02, -0.17)], 0.03), M["brown_sh_i"], I, cyclic=True)   # the cable
        G.stroke(d, [(x0 + 0.0, -0.19), (x0 + 0.06, -0.19), (x0 + 0.06, -0.15), (x0 + 0.0, -0.15)], M["sky_sh_i"], I, cyclic=True)               # its plug
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
        hooks = [(0.0, 0.0)] if mk < 3 else [(0.0, 0.035), (0.0, -0.035)]
        for (dx, dz) in hooks:                                                               # the hook(s): shank + three prongs forward
            s = 1.0 if mk < 3 else 0.8
            G.stroke(d, hose([(0.24, dz), (0.36 * s + 0.08, dz)], 0.03 * s), M["sky_sh_i"], I, cyclic=True)
            for side in (-1, 1):
                G.stroke(d, hose([(0.42 * s + 0.04, dz), (0.47, dz + side * 0.05 * s), (0.42 * s + 0.02, dz + side * 0.07 * s)], 0.022 * s), M["sky_i"], I, cyclic=True)
            G.stroke(d, hose([(0.42 * s + 0.04, dz), (0.5, dz)], 0.022 * s), M["sky_i"], I, cyclic=True)
        if mk >= 2:                                                                          # Mk2+: brass fittings
            G.stroke(d, [(0.2, -0.03), (0.25, -0.03), (0.25, 0.03), (0.2, 0.03)], M["mustard_i"], I, cyclic=True)
    return fn


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


def back_sockets():
    """Per frame of characters/surveyor/side: [x, z, angle, sx, sz] of the float pack's centre (build_surveyor_v3's X and PK)."""
    sys.path.insert(0, HERE)
    import build_surveyor_v3 as SV
    poses = [SV.idle_pose(i) for i in range(10)] + [SV.walk_pose(i) for i in range(12)] + SV.JUMP + SV.LAND + \
        [SV.look_pose(i) for i in range(12)] + SV.BUMP + SV.CONK + [SV.run_pose(i) for i in range(12)] + \
        [SV.fall_pose(i) for i in range(8)] + SV.DASH
    out = []
    for pose in poses:
        p = dict(view="side", bob=0.0, sz=1.0, lean=0.0, shift=0.0, pack_swing=0.0, pack_dz=0.0)
        p.update(pose)
        if p["view"] not in ("side", "tq"):
            out.append(None)
            continue
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
        out.append([round(cx, 4), round(cz, 4), round(sw, 4), round(sx, 4), round(sz, 4)])
    return out


# ---------------------------------------------------------------- the export (on LEAD's OK)
def cable_socket(mk):
    x0 = 0.36 - (0.24 + 0.035 * (mk - 1)) - 0.12
    return [round(x0 + 0.03, 3), -0.17]


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
    socks = back_sockets()
    for mk in (2, 3):
        img = render(jetpack(mk), 64, 64, 64, (0.5, 0.5))[0]
        out.append((f"props/rig/jetpack_mk{mk}", img, {"ppu": 64, "pivot": [0.5, 0.5], "mk": mk, "socket_sheet": "characters/surveyor/side",
                                                       "back_socket": socks,
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


V2_REMOVE = ["props/rig/beam_normal.png", "props/rig/beam_emission.png"]          # the v2 beam's maps (UNITY deletes the .meta files)


def export(art):
    import json
    from meridian import pngio
    built, problems = [], []
    for key, img, extra_meta in kit():
        h, w = img.shape[:2]
        meta = {"key": key, "style": "v3", "width": w, "height": h, "palette": "earth", **extra_meta}
        hit = v3.palette_hits(img, "earth")[0]
        m = v3.EDGE_MARGIN
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
    return out


def keys():
    return [k for k, _i, _m in [(f"props/rig/beam_mk{m}", 0, 0) for m in range(1, 6)] + [("props/rig/beam", 0, 0)]
            + [(f"props/rig/grapple_mk{m}", 0, 0) for m in range(1, 4)] + [("props/rig/grapple", 0, 0)]
            + [(f"props/rig/jetpack_mk{m}", 0, 0) for m in (2, 3)] + [(f"fx/beam_ray/mk{m}", 0, 0) for m in range(1, 6)]]


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


if __name__ == "__main__":                       # python -I build_rig_tools_v3.py <review png>
    preview(sys.argv[1])
    fakegp.restore()
