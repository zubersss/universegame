"""A direct data handoff to UNITY for U-212 (from the 0.6.3 smoke read's H8; LEAD cleared it 11-10 11:3x and 13:2x):
props/rig/stow_socket.json - where a STOWED tool rides the v3 surveyor's BODY, per frame of characters/surveyor/side.

Today the stowed shovel rides the front GLOVE (props/rig/hand_socket.json) at side_dig.json's carry angle. In the bump
and the hard landing the glove flies up to the helmet and takes the tool with it: the blade stands on top of the helmet
(smoke_2c, smoke_3d: a horn, a feather). This table fixes the tool to the body instead: its grip end at the hip, where
the idle's glove holds it today, its direction the idle's (the blade up behind the helmet), both carried through each
drawing's own squash, bob, lean and shift. In the idle it is where the tool is today; it no longer swings with the arm.

Json only, no png, no change to any sheet: the sibling of hand_socket.json and read the same way.

  python -I build_stow_socket_v3.py <review png>     the check sheet: ten frames, today's rule above, the table below
"""
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

KEY = "props/rig/stow_socket"
ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
GRIP = {"side": (0.04, 0.57), "tq": (0.10, 0.57)}          # the tool's grip end on the body (its own metres, before the pose): the idle glove's place
ANGLE = {"side": 119.0, "tq": 108.0}                       # the tool's direction there (deg, counter-clockwise from +x): the carry's 125 with the idle arm's share
CARRY = (math.radians(125.0), 0.08)                        # today's rule, for the sheet: the direction on the glove, the arm's share


def poses():
    import build_rig_tools_v3 as RT
    return RT.side_poses()


def stow_of(pose):
    """[x, z, angle] for one drawing: the grip point and the direction carried through draw_surveyor's visual root (squash
    about the hips, bob, lean, shift). None in the front view (the tool is behind the body and its blade would stand over
    the head) and where the surveyor is hidden."""
    p = dict(view="side", bob=0.0, sz=1.0, lean=0.0, shift=0.0)
    p.update(pose)
    if p["view"] not in GRIP or p.get("hidden"):
        return None
    sx, pz = 1.0 / math.sqrt(p["sz"]), 0.55
    gx, gz = GRIP[p["view"]]
    a = math.radians(ANGLE[p["view"]])
    vx, vz = math.cos(a), math.sin(a)
    x, z = gx * sx + p["lean"] * (gz - pz) + p["shift"], pz + (gz - pz) * p["sz"] + p["bob"]
    return [round(x, 4), round(z, 4), round(math.atan2(vz * p["sz"], vx * sx + p["lean"] * vz), 4)]


def table():
    return [stow_of(p) for p in poses()]


def meta():
    return {"key": KEY, "style": "v3", "socket_sheet": "characters/surveyor/side", "stow_socket": table(),
            "units": "per frame of the socket sheet, in sheet order: [x, z] metres from the pivot to a stowed tool's grip end on the body "
                     "(x right, z up, facing right) and the tool's direction there (radians, counter-clockwise from +x); null where the tool "
                     "is not shown (the front view)",
            "note": "For U-212 (the 0.6.3 read's H8): a stowed tool fixed to the BODY, not to the front glove, so it stays behind the helmet "
                    "when the arms fly up (bump, land) and squashes, leans and bobs with each drawing. Draw it BEHIND the body, no fist over "
                    "it, as the carry is today. In the idle it stands where the glove-carried tool stands; it does not swing with the arm. "
                    "characters/surveyor/side only (side_b has no table yet)"}


def export(art):
    m = meta()
    if len(m["stow_socket"]) != 98:
        raise ValueError(f"{KEY}: {len(m['stow_socket'])} rows, the side sheet has 98 frames")
    base = os.path.join(art, *KEY.split("/"))
    os.makedirs(os.path.dirname(base), exist_ok=True)
    with open(base + ".json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(m, fh, indent=2)
        fh.write("\n")
    return [(KEY, 0, 0, os.path.getsize(base + ".json"))]


def keys():
    return [KEY]


def preview(out, footnote=None):
    """Ten drawings of the exported side sheet with the shovel sprite laid BEHIND the body: above by today's rule (on the
    glove), below by the table."""
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import pngio
    import build_dig_feel_v3 as DF
    paper = np.array(review.PAPER, np.float32)
    Wd = 1920
    side = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png")).astype(np.float32) / 255.0
    sj = json.load(open(os.path.join(ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
    hs = json.load(open(os.path.join(ART, "props", "rig", "hand_socket.json"), encoding="utf-8"))["hand_socket"]
    sh = pngio.read_png_np(os.path.join(ART, "props", "rig", "shovel_color.png")).astype(np.float32) / 255.0
    pm = np.dstack([sh[..., :3] * sh[..., 3:4], sh[..., 3:4]])
    pm = pm.reshape(pm.shape[0] // 2, 2, pm.shape[1] // 2, 2, 4).mean(axis=(1, 3))          # the sprite is ppu 128, the sheet 64
    a = pm[..., 3:4]
    shovel = np.clip(np.rint(np.dstack([np.where(a > 1e-4, pm[..., :3] / np.maximum(a, 1e-4), 0), a]) * 255), 0, 255).astype(np.uint8)
    piv = (0.0667 * shovel.shape[1], shovel.shape[0] * 0.5)
    fw, fh, cols, g = sj["frame_width"], sj["frame_height"], sj["columns"], sj.get("gutter", 4)
    ps, tb = poses(), table()

    def cell(i, sock, label):
        c = np.tile(paper * 0.92, (fh + 40, fw + 40, 1)).astype(np.float32)     # (run 1: 80 px of side padding pushed the fourth cell off the sheet)
        ox, oy = 20, 40
        c[oy + fh - 1:oy + fh] = paper * 0.6
        if sock is not None:
            DF._place(c, shovel, piv, math.degrees(sock[2]), (ox + fw / 2 + sock[0] * 64, oy + fh - sock[1] * 64))
        r, k = divmod(i, cols)
        fr = side[r * (fh + g):r * (fh + g) + fh, k * (fw + g):k * (fw + g) + fw]
        sub = c[oy:oy + fh, ox:ox + fw]
        sub[...] = fr[..., :3] * fr[..., 3:4] + sub * (1 - fr[..., 3:4])
        c = np.repeat(np.repeat(c, 2, 0), 2, 1)
        review._label(c, label, 4, 4, scale=1)
        return c

    def row(cells, gap=6):
        H = max(c.shape[0] for c in cells)
        r = np.tile(paper, (H, Wd, 1)).astype(np.float32)
        x = 0
        for c in cells:
            w = max(0, min(c.shape[1], Wd - x))
            r[:c.shape[0], x:x + w] = c[:, :w]
            x += c.shape[1] + gap
        return r

    def head(text, h=20):
        hd = np.tile(paper, (h, Wd, 1)).astype(np.float32)
        review._label(hd, text[:310], 6, 4, scale=1)
        return hd
    names = {}
    for an in sj["animations"]:
        for k in range(an["length"]):
            names[an["start"] + k] = f"{an['name']} {k}"
    rows = [head("props/rig/stow_socket (for U-212, the 0.6.3 read's H8): the STOWED shovel on the v3 surveyor, drawn behind the body, at 2x. PREVIEW of the table; the frames are the exported side sheet", 26)]
    for group in ((0, 13, 30, 31), (50, 51, 52, 75)):
        today = []
        for i in group:
            h = hs[i]
            p = dict(arms=(0.0, 0.0))
            p.update(ps[i])
            today.append(cell(i, None if h is None else [h[0], h[1], CARRY[0] + CARRY[1] * p["arms"][1]], f"{names[i]} (frame {i})"))
        rows += [head("TODAY: the tool rides the front glove: " + ", ".join(names[i] for i in group)), row(today)]
        rows += [head("THE TABLE: the tool rides the body: the same drawings"), row([cell(i, tb[i], f"{names[i]} (frame {i})") for i in group])]
    nulls = [i for i, t in enumerate(tb) if t is None]
    xs, zs = [t[0] for t in tb if t], [t[1] for t in tb if t]
    lines = [f"98 rows; null (the front view) on frames {nulls[0]}-{nulls[-1]} ({len(nulls)}); the grip point x {min(xs):+.3f}..{max(xs):+.3f}, z {min(zs):.3f}..{max(zs):.3f} m; "
             f"the direction {min(math.degrees(t[2]) for t in tb if t):.0f}..{max(math.degrees(t[2]) for t in tb if t):.0f} deg",
             "idle 0: " + str(tb[0]) + " (today's glove there: " + str(hs[0]) + ")"]
    foot = np.tile(paper, (24 + 16 * len(lines), Wd, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:310], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "props/rig/stow_socket check sheet (lock-free, numpy; not exported)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    preview(sys.argv[1])
