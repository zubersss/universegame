"""B-261 (art v7): THE SHEET of the kit and the tools as 3D, from the files v7_kit.py (kit) wrote into
blender/preview/b261/. numpy only:  python -I build_v7_kit_sheet.py <review sheet png> [peak MB of the Blender run]
WRITTEN 11-10 15:1x AS SOURCE, UNRUN.

Each piece alone at the game's 96 and 128 px per metre and at twice 96; the shovel held by the grey mannequin at dig_down's
contact pose and the Beam on its forearm in an aim hold. The mannequin's joints are B-250's own pose maths
(build_surveyor_v6.skeleton / dig_pose: the tables that STAND), drawn as plain grey capsules: so the sheet shows whether
the 3D tools sit where the dig clips' sockets expect them (the near hand on the haft, the far hand 0.40 m up it, the
tip 0.93 m ahead; the Beam's muzzle 0.47 m beyond the hand).
"""
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from meridian import pngio  # noqa: E402
import painted_v6 as PV  # noqa: E402
import v7_paint as VP  # noqa: E402

D = os.path.normpath(os.path.join(HERE, "..", "preview", "b261"))
STAGE = np.array([0.665, 0.725, 0.571], np.float32)
KIT = ("shovel", "beam", "pack", "crate", "smelter")
FARG = np.array([0.42, 0.42, 0.42], np.float32)   # the far limbs a step darker, so a pose reads


def load(kid):
    return pngio.read_png_np(os.path.join(D, kid + ".png")).astype(np.float32) / 255.0, json.load(open(os.path.join(D, kid + ".json"), encoding="utf-8"))


def on(bg, fg, x, y):
    h, w = fg.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, bg.shape[1]), min(y + h, bg.shape[0])
    if x1 > x0 and y1 > y0:
        s = fg[y0 - y:y1 - y, x0 - x:x1 - x]
        bg[y0:y1, x0:x1] = s[..., :3] * s[..., 3:4] + bg[y0:y1, x0:x1] * (1 - s[..., 3:4])


def turned(img, deg):
    """A straight-alpha picture turned counter-clockwise by deg about its middle (colour premultiplied for the turn)."""
    a = PV._turn(img[..., 3], deg)
    rgb = np.dstack([PV._turn(img[..., c] * img[..., 3], deg) for c in range(3)])
    return np.concatenate([np.where(a[..., None] > 1e-3, rgb / np.maximum(a[..., None], 1e-3), 0.0), np.clip(a, 0, 1)[..., None]], axis=2).astype(np.float32)


def place_tool(bg, kid, k, hx, hy, deg):
    """The tool laid into bg at k px per metre, its pivot (the hand) at the pixel (hx, hy), turned by deg from level."""
    img, meta = load(kid)
    im = VP.resize(img, k / meta["px_per_m"])
    px, py = meta["pivot"][0] * im.shape[1], (1 - meta["pivot"][1]) * im.shape[0]
    t = turned(im, deg)
    dx, dy = px - im.shape[1] / 2.0, py - im.shape[0] / 2.0                                  # the pivot from the picture's middle (y down)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    ox, oy = dx * c + dy * s, -dx * s + dy * c                                               # ... after the turn
    on(bg, t, int(round(hx - (t.shape[1] / 2.0 + ox))), int(round(hy - (t.shape[0] / 2.0 + oy))))


def posed(bg, k, fx, fy, J, tool=None):
    """The grey mannequin in a pose of B-250's skeleton (J: metres, x forward, z up, the soles on z = 0), the far limbs
    first, then the trunk and head, the near leg, the tool, the near arm over it."""
    import build_surveyor_v6 as S
    def limb(a, b, c, r0, r1, r2):                                                           # noqa: E306
        return [(J[a][0], J[a][1], J[b][0], J[b][1], r0, r1), (J[b][0], J[b][1], J[c][0], J[c][1], r1, r2)]

    def foot(s, p):
        ft = math.radians(p.get("ft_" + s, 0.0))
        h_, t_ = S.add(J["ank_" + s], S.rot(S.HEEL, ft)), S.add(J["ank_" + s], S.rot(S.TOE, ft))
        return [(h_[0], h_[1] + 0.035, t_[0], t_[1] + 0.035, 0.035, 0.035)]
    p = J["pose"]
    VP.capsules(bg, k, fx, fy, limb("sh_f", "elb_f", "wr_f", 0.052, 0.042, 0.036) + limb("hip_f", "knee_f", "ank_f", 0.085, 0.060, 0.042) + foot("f", p), FARG)
    trunk = [(J["P"][0], J["P"][1], J["W"][0], J["W"][1], 0.125, 0.12), (J["W"][0], J["W"][1], J["C"][0], J["C"][1], 0.12, 0.135),
             (J["C"][0], J["C"][1], J["SH"][0], J["SH"][1], 0.135, 0.12), (J["SH"][0], J["SH"][1], J["A"][0], J["A"][1], 0.06, 0.055)]
    hd = S.add(J["A"], S.mul(S.up(math.radians(p.get("neck", 0.0) + p.get("head", 0.0))), 0.115))
    VP.capsules(bg, k, fx, fy, trunk + limb("hip_n", "knee_n", "ank_n", 0.085, 0.060, 0.042) + foot("n", p), VP.GREY, ovals=((hd[0] + 0.02, hd[1], 0.098, 0.115),))
    if tool:
        kid, at, deg = tool
        place_tool(bg, kid, k, fx + at[0] * k, fy - at[1] * k, deg)
    VP.capsules(bg, k, fx, fy, limb("sh_n", "elb_n", "wr_n", 0.052, 0.042, 0.036), VP.GREY)


def poses():
    """-> {"dig": (J, tool), "aim": (J, tool)}: dig_down's contact with the shovel (B-250's dig_pose) and an aim hold
    with the Beam on the near forearm (the idle with the near arm raised level; the Beam's pivot is the hand, its aim
    the forearm's line)."""
    import build_surveyor_v6 as S
    p, (wr, a) = S.dig_pose()
    Jd = S.skeleton(p)
    Jd["pose"] = p
    q = dict(S.POSES["idle"])
    q["ua_n"], q["el_n"] = 78.0, 14.0
    Ja = S.skeleton(q)
    Ja["pose"] = q
    fa = math.degrees(math.atan2(Ja["wr_n"][1] - Ja["elb_n"][1], Ja["wr_n"][0] - Ja["elb_n"][0]))
    return {"dig": (Jd, ("shovel", wr, math.degrees(a))), "aim": (Ja, ("beam", Ja["wr_n"], fa))}


def sheet(out, peak=None):
    import review
    paper = np.array(review.PAPER, np.float32)
    Wd = 1920

    def head(text, h=20):
        hd = np.tile(paper, (h, Wd, 1)).astype(np.float32)
        review._label(hd, text[:310], 6, 4, scale=1)
        return hd

    def row(cells, gap=10):
        Hh = max(c.shape[0] for c in cells)
        r = np.tile(paper, (Hh, Wd, 1)).astype(np.float32)
        x = 0
        for c in cells:
            w = min(c.shape[1], Wd - x)
            if w <= 0:
                break
            r[Hh - c.shape[0]:, x:x + w] = c[:, :w]
            x += c.shape[1] + gap
        return r

    def cell(fg, label, pad=10):
        c = np.tile(STAGE, (fg.shape[0] + 2 * pad + 14, fg.shape[1] + 2 * pad, 1)).astype(np.float32)
        on(c, fg, pad, pad + 14)
        review._label(c, label, 3, 3, scale=1)
        return c
    rows = [head("B-261 (ART v7): THE KIT AND THE TOOLS AS 3D - original designs modelled by script from the game's own measures, painted materials, the frame's light. PREVIEW, nothing exported", 26)]
    lines = []
    have = [kid for kid in KIT if os.path.isfile(os.path.join(D, kid + ".png"))]
    for ppm, what in ((96, "AT THE GAME'S 96 px per metre"), (128, "at 128 px per metre"), (192, "at twice 96 (the size they would ship at: ppu 192)")):
        rows.append(head(f"each piece alone, {what}"))
        rows.append(row([cell(VP.resize(load(kid)[0], ppm / load(kid)[1]["px_per_m"]), kid) for kid in have]))
    if "shovel" in have and "beam" in have:
        P = poses()
        for ppm in (96, 192):
            k = float(ppm)
            bg = np.tile(STAGE, (int(2.3 * k), Wd, 1)).astype(np.float32)
            gy = bg.shape[0] - int(0.12 * k)
            bg[gy:] *= 0.86
            posed(bg, k, 2.0 * k, gy, P["dig"][0], P["dig"][1])
            posed(bg, k, 6.0 * k, gy, P["aim"][0], P["aim"][1])
            rows += [head(f"HELD, at {ppm} px per metre: the shovel at dig_down's contact (B-250's pose: the near hand on the haft, the far hand 0.40 m up it) | the Beam on the forearm in an aim hold"), bg]
    for kid in have:
        m = load(kid)[1]
        lines.append(f"{kid}: {m['width_m']} x {m['height_m']} m, {m['tris']} triangles; render {m['render_s']} s, the brush {m['strokes']} + {m['edge_strokes']} strokes in {m['paint_s']} s; "
                     f"at ppu 192: {int(m['size_px'][0] / 2)} x {int(m['size_px'][1] / 2)} px; points: " + json.dumps(m["points"])[:150])
    if peak:
        lines.append(f"PEAK RAM of the Blender run: {peak} MB.")
    foot = np.tile(paper, (24 + 16 * len(lines), Wd, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:310], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-261: the kit and the tools as 3D (Blender renders, numpy sheet; nothing exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    sheet(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
