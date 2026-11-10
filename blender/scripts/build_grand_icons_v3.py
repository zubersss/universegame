"""B-247 (G14; LEAD 11-10 06:1x): the catalogue's icons for the five Grand rig creatures. A rig set's sheet holds body
parts, so the catalogue's "first sprite of the creature's key" showed the Hadal maw's trunk as a cropped rectangle. Each
icon is the whole animal drawn small at the icon set's own ink weight (a rig assembled and shrunk to the row would lose
its ink: these animals are 1,400-1,900 px across), in the rig's own colours and marks.

  icons/catalogue/<the last part of the creature's art key>   128x128 @ PPU 128, pivot centre, as B-233's site icons:
      hadal_maw (earth)              the long trench fish: round head, pie eye, grey lower lip, brown back, teal ridge, the lure
      vortex_whale (jupiter)         the red whale: cream belly, mustard side stripe, cream swirls, blue-edged flukes
      polar_hydra (saturn)           the cream mound with its blue underside and six thin necks, each a small crested head
      diamondback_colossus (uranus)  the teal dome under its pale ice plates, two plated arms raised, the small head
      umbral_leviathan (neptune)     three storm-blue segments with violet bands, pale belly, round two-eyed head, forked tail
  Faces are the animals' own (D-101 allows them on animals); no teeth (D-087).

  python -I build_grand_icons_v3.py <review png>   the lock-free sheet: the five at 3x; then each at the catalogue's row
                                                   size beside two of its planet's catalogue neighbours and what the
                                                   catalogue shows for it today (the rig's first part)
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_icons_items_v3 as IT  # noqa: E402
import build_site_icons_v3 as SI  # noqa: E402
from meridian import v3  # noqa: E402

G, O, I = IT.G, IT.O, IT.I
TAU = 2 * math.pi
ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
C, arc, hose, fill, inked, outline, line = SI.C, SI.arc, SI.hose, SI.fill, SI.inked, SI.outline, SI.line


def eye(d, M, x, z, r, look=(0.35, 0.05)):
    """A small pie-less eye for a 128 px icon: a white disc with a thin ink ring and a round pupil."""
    inked(d, M, C(x, z, r, n=14), "off", I)
    G.stroke(d, [(x + look[0] * r - 0.002, z + look[1] * r), (x + look[0] * r + 0.002, z + look[1] * r)], M["ink"], r * 0.52)


def below(pts, z):
    """The part of a closed convex outline under height z (a chord polygon)."""
    return [p for p in pts if p[1] < z]


def above(pts, z):
    return [p for p in pts if p[1] > z]


def hadal_maw(d, M):
    inked(d, M, [(-0.30, 0.02), (-0.45, 0.20), (-0.40, 0.03), (-0.45, -0.15)], "teal_sh")                    # the tail fin
    top = [(-0.31, 0.045), (-0.15, 0.08), (0.0, 0.12), (0.12, 0.16)]
    bot = [(0.12, -0.15), (0.0, -0.11), (-0.15, -0.05), (-0.31, -0.005)]
    fill(d, M, top + bot, "teal_dp")                                                                        # the trunk
    fill(d, M, bot + [(-0.31, 0.012), (-0.15, -0.02), (0.0, -0.06), (0.12, -0.09)], "sky_sh")               # the grey belly
    fill(d, M, top + [(0.12, 0.125), (0.0, 0.09), (-0.15, 0.055), (-0.31, 0.03)], "brown")                  # the brown back
    for x0 in (-0.24, -0.12, 0.0):                                                                          # the dorsal ridge
        z0 = 0.045 + (x0 + 0.31) * (0.115 / 0.43)
        inked(d, M, [(x0 - 0.045, z0 - 0.012), (x0, z0 + 0.05), (x0 + 0.045, z0 + 0.012)], "teal_sh", I)
    outline(d, M, top + bot)
    inked(d, M, [(-0.02, -0.10), (0.05, -0.25), (0.10, -0.12)], "teal_sh")                                  # the pectoral fin
    for i, x in enumerate((-0.22, -0.14, -0.06, 0.02)):                                                     # the flank's lights
        fill(d, M, C(x, 0.02 + (x + 0.31) * 0.06, 0.012, n=8), "off" if i % 2 == 0 else "mustard")
    hd = C(0.22, 0.01, 0.21, n=28, rz=0.20)                                                                 # the head
    fill(d, M, hd, "teal_dp")
    fill(d, M, above(hd, 0.13), "brown")
    fill(d, M, [(0.20, -0.07), (0.425, -0.035), (0.40, -0.12), (0.26, -0.175)], "sky_sh")                   # the grey lower lip
    outline(d, M, hd)
    line(d, M, [(0.18, -0.065), (0.30, -0.055), (0.425, -0.03)])                                            # the closed smile
    eye(d, M, 0.31, 0.07, 0.042)
    inked(d, M, hose(G.bezier((0.16, 0.20), (0.20, 0.40), (0.35, 0.40), n=10), 0.022), "teal_sh", I)        # the lure's stalk
    inked(d, M, C(0.385, 0.385, 0.045, n=14), "mustard")                                                    # its bulb
    fill(d, M, C(0.375, 0.397, 0.014, n=8), "off")


def vortex_whale(d, M):
    inked(d, M, [(-0.30, 0.0), (-0.45, 0.17), (-0.40, 0.02), (-0.46, -0.12)], "red_dp")                     # the flukes
    fill(d, M, [(-0.45, 0.17), (-0.425, 0.165), (-0.385, 0.035), (-0.40, 0.02)], "teal")                    # their blue edge
    top = [(-0.31, 0.03), (-0.12, 0.13), (0.10, 0.17), (0.28, 0.15), (0.41, 0.07), (0.44, -0.01)]
    bot = [(0.42, -0.09), (0.30, -0.14), (0.08, -0.13), (-0.14, -0.07), (-0.31, -0.02)]
    fill(d, M, top + bot, "red")
    fill(d, M, [(0.44, -0.02)] + bot + [(-0.14, -0.035), (0.08, -0.075), (0.26, -0.07)], "off")             # the cream belly
    fill(d, M, hose([(-0.26, 0.035), (-0.05, 0.075), (0.16, 0.08)], 0.022), "mustard")                      # the side stripe
    for cx, cz, r in ((-0.10, 0.105, 0.028), (0.03, 0.125, 0.03), (0.16, 0.125, 0.026)):                    # three cream swirls
        fill(d, M, hose(arc(cx, cz, r, 60, 300, n=8), 0.012), "off")
    inked(d, M, [(0.02, -0.11), (-0.10, -0.25), (0.10, -0.14)], "red_dp")                                   # the flipper
    outline(d, M, top + bot)
    line(d, M, [(0.20, -0.06), (0.32, -0.075), (0.43, -0.03)])                                              # the long closed smile
    eye(d, M, 0.33, 0.05, 0.036)


def polar_hydra(d, M):
    # run 1 drew six straight pins with knobs in a dish (a pincushion): the necks WEAVE now, at uneven heights, and the heads
    # are bigger, each looking outward with its blue jaw and a crest
    heads = [(-0.33, 0.13), (-0.22, 0.30), (-0.08, 0.37), (0.07, 0.31), (0.21, 0.36), (0.33, 0.17)]
    for i, (hx, hz) in enumerate(heads):                                                                    # six weaving necks
        bx = -0.15 + 0.06 * i
        s = -1.0 if i % 2 == 0 else 1.0
        path = G.bezier((bx, -0.18), (bx + 0.09 * s, -0.02 + 0.15 * (hz - 0.1)), ((bx + hx) / 2 - 0.07 * s, hz * 0.62), (hx, hz - 0.03), n=14)
        inked(d, M, hose(path, 0.036), "sky", I)
    body = C(0.0, -0.25, 0.36, n=30, rz=0.13)                                                               # the mound
    fill(d, M, body, "sky")
    fill(d, M, below(body, -0.285), "teal")
    outline(d, M, body)
    for i, (hx, hz) in enumerate(heads):
        s = -1.0 if hx < 0 else 1.0                                                                         # the outer heads look outward
        hd = C(hx, hz, 0.068, n=18, rz=0.05)
        inked(d, M, [(hx - 0.035 * s, hz + 0.035), (hx - 0.075 * s, hz + 0.085), (hx - 0.03 * s, hz + 0.07), (hx - 0.005 * s, hz + 0.095),
                     (hx + 0.012 * s, hz + 0.045)], "red", I)                                               # the frill crest
        fill(d, M, hd, "off")
        fill(d, M, below(hd, hz - 0.012), "teal")                                                           # the blue jaw
        outline(d, M, hd, I)
        G.stroke(d, [(hx + 0.028 * s - 0.002, hz + 0.014), (hx + 0.028 * s + 0.002, hz + 0.014)], M["ink"], 0.011)            # the eye


def diamondback_colossus(d, M):
    for path, tip in (([(-0.20, -0.06), (-0.31, 0.12), (-0.30, 0.33)], (-0.30, 0.33)),                      # two raised arms
                      ([(0.08, -0.02), (0.10, 0.20), (0.15, 0.37)], (0.15, 0.37))):
        inked(d, M, hose(path, 0.07), "teal_sh")
        for a in (60, 90, 120):                                                                             # three claw tips
            line(d, M, [tip, (tip[0] + 0.06 * math.cos(math.radians(a)), tip[1] + 0.06 * math.sin(math.radians(a)))])
    body = arc(0.0, -0.24, 0.38, 0, 180, n=18, rz=0.27) + arc(0.0, -0.24, 0.38, 180, 360, n=12, rz=0.10)[1:-1]   # the dome
    fill(d, M, body, "teal")
    fill(d, M, below(body, -0.265), "brown")
    outline(d, M, body)
    hd = C(0.27, 0.10, 0.105, n=18)                                                                         # the head
    inked(d, M, hd, "teal")
    eye(d, M, 0.31, 0.125, 0.032)
    line(d, M, [(0.25, 0.05), (0.31, 0.04), (0.365, 0.065)])
    plates = [(-0.22, -0.13, 0.05, 0.3), (-0.06, -0.06, 0.06, 0.9), (0.10, -0.14, 0.05, 0.2), (-0.12, -0.22, 0.045, 0.6),
              (0.04, -0.24, 0.04, 1.1), (0.20, -0.20, 0.045, 0.5), (-0.30, 0.10, 0.04, 0.4), (-0.30, 0.24, 0.035, 1.0),
              (0.10, 0.14, 0.04, 0.7), (0.13, 0.28, 0.035, 0.2)]
    for x, z, r, t in plates:                                                                               # the ice plates
        inked(d, M, [(x + r * 1.15 * math.cos(t + TAU * q / 4), z + r * (0.75 if q % 2 else 1.0) * math.sin(t + TAU * q / 4)) for q in range(4)], "off", I)


def umbral_leviathan(d, M):
    inked(d, M, [(-0.33, 0.0), (-0.46, 0.10), (-0.41, 0.0), (-0.46, -0.09)], "sky_sh")                      # the forked tail
    inked(d, M, [(-0.05, -0.10), (-0.16, -0.21), (0.02, -0.12)], "sky_sh")                                  # two fins
    inked(d, M, [(0.14, -0.12), (0.03, -0.25), (0.22, -0.14)], "sky_sh")
    for cx, cz, rx, rz in ((-0.22, -0.01, 0.13, 0.085), (-0.03, -0.015, 0.155, 0.105), (0.16, -0.02, 0.17, 0.12)):   # three segments
        seg = C(cx, cz, rx, n=24, rz=rz)
        fill(d, M, seg, "sky")
        fill(d, M, below(seg, cz - 0.4 * rz), "off_sh")
        for bx in (cx - 0.3 * rx, cx + 0.2 * rx):                                                           # the violet bands
            h = rz * math.sqrt(max(0.0, 1 - ((bx - cx) / rx) ** 2))
            fill(d, M, [(bx - 0.016, cz + h * 0.9), (bx + 0.016, cz + h * 0.9), (bx + 0.02, cz - 0.4 * rz), (bx - 0.012, cz - 0.4 * rz)], "mustard")
        outline(d, M, seg)
    hd = C(0.33, 0.0, 0.12, n=22, rz=0.11)                                                                  # the head
    fill(d, M, hd, "sky")
    fill(d, M, below(hd, -0.045), "off_sh")
    outline(d, M, hd)
    eye(d, M, 0.355, 0.04, 0.027, look=(0.3, 0.0))
    eye(d, M, 0.412, 0.035, 0.025, look=(0.3, 0.0))


GRAND = [  # (the creature's art key, the palette, the drawing, the json note)
    ("creatures/earth/hadal_maw", "earth", hadal_maw, "the Hadal maw (the trench's long fish with its lure)"),
    ("creatures/jupiter/vortex_whale", "jupiter", vortex_whale, "the vortex whale (the Red Spot's red whale)"),
    ("creatures/saturn/polar_hydra", "saturn", polar_hydra, "the polar hydra (six necks on a cream mound)"),
    ("creatures/uranus/diamondback_colossus", "uranus", diamondback_colossus, "the Diamondback Colossus (a dome under ice plates, two arms raised)"),
    ("creatures/neptune/umbral_leviathan", "neptune", umbral_leviathan, "the Umbral Leviathan (a banded storm-blue whale-eel)"),
]
NEIGHBOURS = {"earth": ("creatures/earth/shark", "creatures/earth/stag"), "jupiter": ("creatures/jupiter/stormglider", "creatures/jupiter/ballast_tortoise"),
              "saturn": ("creatures/saturn/hex_drake", "creatures/saturn/helium_jelly"), "uranus": ("creatures/uranus/methane_ray", "creatures/uranus/hailcrab"),
              "neptune": ("creatures/neptune/windrider", "creatures/neptune/anchor_worm")}


def icon_key(creature_key):
    return "icons/catalogue/" + creature_key.split("/")[-1]


def keys():
    return [icon_key(k) for k, _p, _f, _n in GRAND]


def kit():
    return [(icon_key(k), SI.render(fn, planet), {"palette": planet, "ppu": IT.PPU, "pivot": [0.5, 0.5], "creature": k,
                                                   "note": "B-247 (G14): the catalogue's " + note + ": a rig set's first sprite is a body "
                                                           "part, so the catalogue shows this instead (U-210)"})
            for k, planet, fn, note in GRAND]


def export(art):
    from meridian import pngio
    built, problems = [], []
    for key, img, extra in kit():
        problems += SI.checks(key, img, extra["palette"])
        if not os.path.isfile(os.path.join(art, *extra["creature"].split("/")) + ".json"):
            problems.append(f"{key}: no rig {extra['creature']} on disk")
        built.append((key, img, {"key": key, "style": "v3", "width": img.shape[1], "height": img.shape[0], **extra}))
    if problems:
        raise ValueError("B-247 checks: " + "; ".join(problems))
    out = []
    for key, img, meta in built:
        base = os.path.join(art, *key.split("/"))
        os.makedirs(os.path.dirname(base), exist_ok=True)
        n = pngio.write_png(base + "_color.png", img)
        with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((key, img.shape[1], img.shape[0], n))
    return out


def preview(out, footnote=None):
    import time
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    paper = np.array(review.PAPER, np.float32)
    K = kit()
    problems = []
    for key, img, extra in K:
        problems += SI.checks(key, img, extra["palette"])

    def on_paper(img):
        f = img.astype(np.float32) / 255.0
        return f[..., :3] * f[..., 3:4] + paper * (1 - f[..., 3:4])

    def shrink(img, target=60):
        """A sprite at about the catalogue's row size: block means (premultiplied) by a whole factor."""
        h, w = img.shape[:2]
        k = max(1, int(math.ceil(max(h, w) / float(target))))
        H, W = -(-h // k) * k, -(-w // k) * k
        f = np.zeros((H, W, 4), np.float32)
        f[:h, :w] = img.astype(np.float32) / 255.0
        f[..., :3] *= f[..., 3:4]
        s = f.reshape(H // k, k, W // k, k, 4).mean(axis=(1, 3))
        return s[..., :3] + paper * (1 - s[..., 3:4])

    def first_sprite(key):
        """What the catalogue shows for a creature key today: its sheet's first frame, or a rig set's first part."""
        base = os.path.join(ART, *key.split("/"))
        if not os.path.isfile(base + ".json"):
            return None
        J = json.load(open(base + ".json", encoding="utf-8"))
        sh = pngio.read_png_np(base + "_color.png")
        if "parts" in J:
            x, y, w, h = J["parts"][0]["rect"]
            if J.get("rect_origin") == "bottom_left":
                y = sh.shape[0] - y - h
            return sh[y:y + h, x:x + w]
        return sh[:J["frame_height"], :J["frame_width"]]

    W = 1920
    rows = [np.tile(paper, (30, W, 1)).astype(np.float32)]
    review._label(rows[0], "B-247 (G14): the catalogue's icons for the five Grand rig creatures, icons/catalogue/<creature> 128x128 (PREVIEW, nothing exported) - at 3x", 6, 8)
    big = np.tile(paper, (384, W, 1)).astype(np.float32)
    for i, (key, img, _e) in enumerate(K):
        z = np.repeat(np.repeat(on_paper(img), 3, 0), 3, 1)
        big[:, i * 384:i * 384 + 384] = z
        review._label(big, key, i * 384 + 4, 4, scale=1)
    rows.append(big)
    hd = np.tile(paper, (20, W, 1)).astype(np.float32)
    review._label(hd, "at about the catalogue's row size, per planet: two catalogue neighbours (their first frames, as the catalogue shows them) | THE NEW ICON | what the catalogue shows for it today (the rig's first part)", 6, 4, scale=1)
    rows.append(hd)
    small = np.tile(paper, (90, W, 1)).astype(np.float32)
    x = 10
    for (ckey, planet, _fn, _n), (key, img, _e) in zip(GRAND, K):
        for nk in NEIGHBOURS[planet]:
            sp = first_sprite(nk)
            if sp is not None:
                s = shrink(sp)
                small[14:14 + s.shape[0], x:x + s.shape[1]] = s[:76]
                x += s.shape[1] + 8
        s = shrink(img)
        small[14:14 + s.shape[0], x:x + s.shape[1]] = s
        review._label(small, "new", x, 2, scale=1)
        x += s.shape[1] + 8
        sp = first_sprite(ckey)
        if sp is not None:
            s = shrink(sp)
            small[14:14 + min(76, s.shape[0]), x:x + s.shape[1]] = s[:76]
            review._label(small, "today", x, 2, scale=1)
            x += s.shape[1] + 8
        x += 36
    rows.append(small)
    lines = [f"{key}: {img.shape[1]}x{img.shape[0]}, palette {v3.palette_hits(img, e['palette'])[0] * 100:.1f}% ({e['palette']})" for key, img, e in K]
    lines.append("problems: " + ("; ".join(problems) if problems else "none"))
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-247 Grand creature icons preview (lock-free, fakegp + numpy; not exported)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    preview(sys.argv[1])
