"""B-227 (D1, LEAD 11:5x; for U-193's HUD tool slot and the tree): the other rig modules' tool icons in B-226's shovel-icon
proportion and ink weight (a chunky silhouette on a diagonal, heavy outer ink), so the slot reads at 48 px and the tree at 40.

  icons/tools/beam      128x128 @ PPU 128: the Beam - a cable-fed arm emitter (the brown cuff with brass straps, the teal body
                        with steel cooling rings, the teal glow ring, the brass cutting nozzle; its cable curls off the back
                        toward the pack), a short teal beam into a rock with chips flying. Never a gun (D-087): no grip, no
                        trigger, nothing hanging under the body
  icons/tools/grapple   the Grapple - the hand reel (a steel drum, the line coiled lap on lap, the crank) with its three-pronged
                        hook seated forward on the arm and a slack loop of line between them
  icons/tools/survey    the Survey - its scanner: the teal case on the cuff with the compass dial and the red-tipped aerial, the
                        big brass dish open forward with the pick-up at its focus, two teal scan arcs
  icons/tools/builder   the Builder - its placing tool: the plank hopper heaped with dirt, the steel scoop forward tipping a clod
                        into a placing ghost (B-217's cream dashes and corner brackets)

All four: Earth palette, 128x128 at PPU 128, pivot centre, inside the 2 px margin (B-199's item-icon contract, as
icons/tools/shovel); json key / style / size / ppu / pivot / note.

  python -I build_tool_icons_v3.py <review png>     the lock-free sheet: all five tool icons (the shovel included) at 128 / 48
                                                    (the HUD slot) / 40 (the tree), in a row at 48 and at 40, beside
                                                    icons/nodes/dig_power_1 (The Beam's node) and two item icons
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_rig_tools_v3 as RT  # noqa: E402  (installs fakegp; render + the icon materials)
import build_icons_items_v3 as IT  # noqa: E402
from meridian import v3  # noqa: E402

G = RT.G
O, I = G.OUTER, G.INNER
TAU = 2 * math.pi
ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
TOOLS = ("beam", "grapple", "survey", "builder")


def hose(pts, w):
    return G.hose_outline(pts, w)


def axis(deg, sx, sz):
    """Local tool coordinates (x along the tool, back to front; z across it) -> the icon, turned `deg` about (sx, sz)."""
    a = math.radians(deg)
    ux, uz = math.cos(a), math.sin(a)

    def T(pts):
        return [(sx + x * ux - z * uz, sz + x * uz + z * ux) for x, z in pts]
    return T


def rect(x0, z0, x1, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


def circle(cx, cz, r, n=20):
    return [(cx + r * math.cos(TAU * i / n), cz + r * math.sin(TAU * i / n)) for i in range(n)]


def arc(cx, cz, r, a0, a1, n=12):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cz + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def smooth(pts, n=6):
    """A Catmull-Rom curve through pts (n samples per span): a line that must not show its corners."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * p1[j] + (p2[j] - p0[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (3 * p1[j] - p0[j] - 3 * p2[j] + p3[j]) * t * t * t) for j in (0, 1)))
    out.append(pts[-1])
    return out


def cuff(d, M, T, x0, x1, h):
    """The forearm cuff every module straps on (B-205 / B-217): brown, two brass straps."""
    G.stroke(d, T(rect(x0, -h, x1, h)), M["brown_i"], O, cyclic=True)
    for k in (1, 2):
        x = x0 + (x1 - x0) * k / 3
        G.stroke(d, T(rect(x - 0.013, -h, x + 0.013, h)), M["mustard"], 0.0, cyclic=True)


# ---------------------------------------------------------------- the four icons (metres; the frame is 1 m, centre origin)
def beam_icon(d, M):
    T = axis(-35, -0.05, 0.035)
    r, x0, x1 = 0.11, -0.30, 0.12
    G.stroke(d, T(hose([(x0 - 0.02, 0.0), (x0 - 0.08, 0.03), (x0 - 0.11, 0.09), (x0 - 0.10, 0.15)], 0.045)), M["brown_sh_i"], I, cyclic=True)   # cable
    G.stroke(d, T(rect(x0 - 0.04, -0.065, x0 + 0.01, 0.065)), M["sky_sh_i"], I, cyclic=True)                       # the steel end cap
    rock = T([(0.45, 0.0)])[0]
    IT.faceted(d, M, IT.lump(rock[0], rock[1], 0.10, 0.11, 2271, n=8), "brown_sh", "brown", "brown_dp", rock[0], rock[1])   # the rock
    G.stroke(d, T(hose([(0.25, 0.0), (0.40, 0.0)], 0.075)), M["teal_i"], I, cyclic=True)                              # a short beam into it
    G.stroke(d, T(hose([(0.27, 0.0), (0.39, 0.0)], 0.028)), M["off"], 0.0, cyclic=True)
    for a0, a1 in (((0.37, 0.07), (0.31, 0.15)), ((0.39, 0.075), (0.42, 0.17)), ((0.37, -0.07), (0.32, -0.15))):    # chips off the dig face
        G.stroke(d, T(hose([a0, a1], 0.024)), M["mustard"], 0.0, cyclic=True)
    body = [(x0, -r), (x1, -r * 0.92), (x1, r * 0.92), (x0, r)]
    G.stroke(d, T(body), M["teal_sh_i"], O, cyclic=True)                                                              # the emitter body
    G.stroke(d, T([(x0, r * 0.2), (x1, r * 0.15), (x1, r * 0.92), (x0, r)]), M["teal"], 0.0, cyclic=True)
    G.stroke(d, T(body), M["ink"], O * 1.25, cyclic=True)
    G.stroke(d, T(rect(0.025, -r - 0.015, 0.07, r + 0.015)), M["sky_i"], I, cyclic=True)                             # one cooling ring (rev:
                                                                                                                        # two + the straps striped it at 40 px)
    G.stroke(d, T(rect(x1 - 0.025, -r * 0.85, x1 + 0.015, r * 0.85)), M["teal_i"], I, cyclic=True)                   # the glow ring
    G.stroke(d, T([(x1 + 0.015, -r * 0.8), (0.25, -0.04), (0.27, -0.035), (0.27, 0.035), (0.25, 0.04), (x1 + 0.015, r * 0.8)]),
             M["mustard_i"], O, cyclic=True)                                                                           # the cutting nozzle
    G.seam(d, T([(0.2, -0.058), (0.2, 0.058)]), M["ink"])
    cuff(d, M, T, -0.21, -0.09, r + 0.05)


def grapple_icon(d, M):
    C, R = (-0.17, -0.15), 0.19
    S0, S1 = (0.10, 0.10), (0.30, 0.30)
    u, p = (math.sqrt(0.5), math.sqrt(0.5)), (-math.sqrt(0.5), math.sqrt(0.5))

    def at(o, a, b):
        return (o[0] + a * u[0] + b * p[0], o[1] + a * u[1] + b * p[1])
    G.stroke(d, hose(smooth([(-0.21, 0.03), (-0.30, 0.16), (-0.24, 0.30), (-0.08, 0.33), (0.04, 0.24), (0.09, 0.13)]), 0.036),
             M["mustard_sh_i"], I * 0.7, cyclic=True)                                                                  # the slack line (rev:
                                                                                                                        # a smooth curve, not corners)
    G.stroke(d, hose([C, S0], 0.06), M["sky_sh_i"], I, cyclic=True)                                                   # the arm to the seat
    G.stroke(d, circle(C[0], C[1], R, 28), M["sky_sh_i"], O * 1.25, cyclic=True)                                       # the reel drum
    for k in range(3):                                                                                                  # the line, lap on lap
        rr = R * (0.8 - 0.17 * k)
        G.stroke(d, hose(circle(C[0], C[1], rr, 22)[:21], 0.034), M["mustard_sh_i"], I * 0.7, cyclic=True)
    G.stroke(d, hose([(C[0] - 0.09, C[1] + 0.025), (C[0] + 0.09, C[1] - 0.025)], 0.032), M["sky_i"], I, cyclic=True)  # the crank bar
    G.stroke(d, circle(C[0] + 0.09, C[1] - 0.025, 0.028, 12), M["mustard_i"], I, cyclic=True)                         # its knob
    G.stroke(d, hose([S0, S1], 0.055), M["sky_sh_i"], I, cyclic=True)                                                 # the hook's shank
    G.stroke(d, [at(S0, 0.015, -0.04), at(S0, 0.06, -0.04), at(S0, 0.06, 0.04), at(S0, 0.015, 0.04)], M["mustard_i"], I, cyclic=True)   # collar
    T0 = (0.31, 0.31)
    G.stroke(d, hose([T0, at(T0, 0.07, 0.0)], 0.04), M["sky_i"], I, cyclic=True)                                      # three prongs
    for s in (1, -1):
        G.stroke(d, hose([T0, at(T0, 0.01, 0.09 * s), at(T0, -0.06, 0.12 * s)], 0.04), M["sky_i"], I, cyclic=True)


def survey_icon(d, M):
    T = axis(20, -0.025, -0.02)
    G.stroke(d, T(hose([(-0.13, 0.12), (-0.16, 0.22), (-0.19, 0.30)], 0.024)), M["sky_sh_i"], I, cyclic=True)        # the aerial
    G.stroke(d, T(circle(-0.195, 0.315, 0.036, 12)), M["red_i"], I, cyclic=True)
    case = [(-0.34, -0.11), (0.04, -0.11), (0.08, -0.07), (0.08, 0.09), (0.04, 0.12), (-0.34, 0.12)]
    G.stroke(d, T(case), M["teal_sh_i"], O, cyclic=True)                                                              # the case
    G.stroke(d, T([(-0.34, 0.04), (0.08, 0.04), (0.08, 0.09), (0.04, 0.12), (-0.34, 0.12)]), M["teal"], 0.0, cyclic=True)
    G.stroke(d, T(case), M["ink"], O * 1.25, cyclic=True)
    cuff(d, M, T, -0.30, -0.19, 0.16)
    G.stroke(d, T(circle(-0.03, 0.12, 0.08, 24)), M["mustard_i"], I, cyclic=True)                                    # the compass dial
    G.stroke(d, T(circle(-0.03, 0.12, 0.058, 20)), M["sky_i"], I, cyclic=True)                                       # (a pale face, a long
    a_n = math.radians(50)                                                                                             # diagonal needle: no eye)
    ux, uz = math.cos(a_n), math.sin(a_n)
    G.stroke(d, T([(-0.03 + 0.05 * ux, 0.12 + 0.05 * uz), (-0.03 - 0.009 * uz, 0.12 + 0.009 * ux),
                   (-0.03 - 0.04 * ux, 0.12 - 0.04 * uz), (-0.03 + 0.009 * uz, 0.12 - 0.009 * ux)]), M["red_i"], I * 0.5, cyclic=True)
    G.stroke(d, T(hose([(0.08, 0.01), (0.19, 0.01)], 0.04)), M["sky_sh_i"], I, cyclic=True)                          # the dish's arm
    outer = arc(0.42, 0.01, 0.25, math.radians(125), math.radians(235), 14)
    inner = arc(0.42, 0.01, 0.20, math.radians(235), math.radians(125), 14)
    G.stroke(d, T(outer + inner), M["mustard_i"], O, cyclic=True)                                                     # the dish, open forward
    G.stroke(d, T(arc(0.42, 0.01, 0.235, math.radians(185), math.radians(232), 6) + arc(0.42, 0.01, 0.205, math.radians(232), math.radians(185), 6)),
             M["mustard_sh"], 0.0, cyclic=True)                                                                        # its shaded lower rim
    G.stroke(d, T(hose([(0.225, 0.01), (0.27, 0.01)], 0.016)), M["sky_sh_i"], I * 0.6, cyclic=True)                  # the feed
    G.stroke(d, T(circle(0.28, 0.01, 0.03, 12)), M["teal_i"], I, cyclic=True)                                        # the pick-up (focus)
    for rr in (0.10, 0.15):                                                                                            # two scan arcs
        G.stroke(d, T(hose(arc(0.28, 0.01, rr, math.radians(-38), math.radians(38), 8), 0.026)), M["teal_i"], I * 0.8, cyclic=True)


def dashed_square(d, M, cx, cz, h, per_side=3):
    """B-217's placing ghost at icon size: cream dashes round a square, bold corner brackets, a small plus."""
    pts = [(cx - h, cz - h), (cx + h, cz - h), (cx + h, cz + h), (cx - h, cz + h)]
    for side in range(4):
        (xa, za), (xb, zb) = pts[side], pts[(side + 1) % 4]
        for j in range(per_side):
            t0, t1 = (j + 0.25) / per_side, (j + 0.75) / per_side
            G.stroke(d, hose([(xa + (xb - xa) * t0, za + (zb - za) * t0), (xa + (xb - xa) * t1, za + (zb - za) * t1)], 0.026),
                     M["off_i"], I * 0.8, cyclic=True)
    c, e = 0.055, h + 0.02
    for sx in (-1, 1):
        for sz in (-1, 1):
            G.stroke(d, hose([(cx + sx * e, cz + sz * (e - c)), (cx + sx * e, cz + sz * e), (cx + sx * (e - c), cz + sz * e)], 0.032),
                     M["off_i"], I, cyclic=True)
    for a, b in (((cx - 0.035, cz), (cx + 0.035, cz)), ((cx, cz - 0.035), (cx, cz + 0.035))):
        G.stroke(d, hose([a, b], 0.024), M["off_i"], I * 0.8, cyclic=True)


def builder_icon(d, M):
    T = axis(-20, -0.05, 0.10)
    dashed_square(d, M, 0.25, -0.28, 0.12)                                                                             # where it lands
    G.stroke(d, IT.lump(0.29, -0.10, 0.036, 0.03, 2274, n=9, jit=0.15), M["brown_i"], I, cyclic=True)                 # a clod tipping out
    G.stroke(d, T(hose([(-0.37, 0.0), (-0.41, 0.05), (-0.42, 0.12)], 0.045)), M["brown_sh_i"], I, cyclic=True)        # the dirt hose
    for x, z, rr in ((-0.28, 0.15, 0.07), (-0.16, 0.17, 0.08), (-0.05, 0.15, 0.065)):                                # dirt heaped in the top
        c = T([(x, z)])[0]
        G.stroke(d, IT.lump(c[0], c[1], rr, rr * 0.75, int(abs(x) * 100) + 2277, n=10, jit=0.12), M["brown_i"], I, cyclic=True)
    box = rect(-0.36, -0.12, 0.02, 0.13)
    G.stroke(d, T(box), M["mustard_sh_i"], O, cyclic=True)                                                            # the plank hopper
    for x in (-0.23, -0.10):
        G.seam(d, T([(x, -0.115), (x, 0.125)]), M["ink"])
    G.stroke(d, T(rect(-0.36, -0.045, 0.02, -0.005)), M["sky_sh_i"], I, cyclic=True)                                  # an iron band
    G.stroke(d, T(box), M["ink"], O * 1.25, cyclic=True)
    cuff(d, M, T, -0.27, -0.17, 0.16)
    bowl = [(0.02, 0.10), (0.02, -0.10)] + [(0.20 + 0.18 * math.cos(a), 0.12 * math.sin(a)) for a in np.linspace(-math.pi * 0.62, 0.32, 10)]
    G.stroke(d, T(bowl), M["sky_sh_i"], O, cyclic=True)                                                               # the steel scoop
    G.stroke(d, T(bowl), M["ink"], O * 1.25, cyclic=True)
    for x, z, rr in ((0.11, 0.09, 0.055), (0.21, 0.08, 0.06), (0.30, 0.05, 0.042)):                                  # dirt in the scoop
        c = T([(x, z)])[0]
        G.stroke(d, IT.lump(c[0], c[1], rr, rr * 0.75, int(x * 100) + 2283, n=10, jit=0.12), M["brown_i"], I, cyclic=True)


ICONS = {"beam": beam_icon, "grapple": grapple_icon, "survey": survey_icon, "builder": builder_icon}
NOTES = {"beam": "B-227: The Beam's icon (a cable-fed arm emitter with a cutting nozzle firing into rock; never a gun, D-087)",
         "grapple": "B-227: the Grapple's icon (the hand reel with its coiled line, the three-pronged hook seated forward)",
         "survey": "B-227: the Survey's icon (the scanner: the case, the compass dial, the aerial, the brass dish and its scan arcs)",
         "builder": "B-227: the Builder's icon (the placing tool: the dirt hopper, the scoop tipping a clod into a placing ghost)"}


# ---------------------------------------------------------------- kit / export
def kit():
    return [(f"icons/tools/{t}", RT.render(ICONS[t], IT.SIZE, IT.SIZE, IT.PPU, (0.5, 0.5))[0],
             {"ppu": IT.PPU, "pivot": [0.5, 0.5], "note": NOTES[t]}) for t in TOOLS]


def checks(key, img):
    m = v3.EDGE_MARGIN
    out = []
    hit = v3.palette_hits(img, "earth")[0]
    if hit < 0.995:
        out.append(f"{key}: palette {hit * 100:.1f}%")
    if img[:m, :, 3].any() or img[-m:, :, 3].any() or img[:, :m, 3].any() or img[:, -m:, 3].any():
        out.append(f"{key}: touches the {m} px edge")
    return out


def export(art):
    from meridian import pngio
    built, problems = [], []
    for key, img, extra in kit():
        problems += checks(key, img)
        built.append((key, img, {"key": key, "style": "v3", "width": img.shape[1], "height": img.shape[0], "palette": "earth", **extra}))
    if problems:
        raise ValueError("B-227 checks: " + "; ".join(problems))
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


def keys():
    return [f"icons/tools/{t}" for t in TOOLS]


# ---------------------------------------------------------------- the review sheet
def shrink(im, s):
    """128 px RGBA (uint8, straight alpha) -> s px by an area mean on premultiplied colour (how a mip / bilinear UI scale
    blends it, closer than the nearest sampling of the B-226 sheet)."""
    n = im.shape[0]
    g = math.gcd(n, s)
    up, down = s // g, n // g
    f = im.astype(np.float32) / 255.0
    f[..., :3] *= f[..., 3:4]
    big = np.repeat(np.repeat(f, up, 0), up, 1)
    m = big.reshape(s, down, s, down, 4).mean(axis=(1, 3))
    a = m[..., 3:4]
    m[..., :3] = np.where(a > 1e-4, m[..., :3] / np.maximum(a, 1e-4), 0.0)
    return np.rint(np.clip(m, 0, 1) * 255).astype(np.uint8)


def preview(out, footnote=None):
    import time
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_shovel_v3 as BS
    K = [(k, img) for k, img, _e in kit()]
    shovel = RT.render(BS.shovel_icon, IT.SIZE, IT.SIZE, IT.PPU, (0.5, 0.5))[0]
    five = [("icons/tools/shovel", shovel)] + K
    neigh = []
    for k in ("nodes/dig_power_1", "iron/base", "copper/base"):
        p = os.path.join(ART, "icons", *k.split("/")) + "_color.png"
        if os.path.isfile(p):
            neigh.append(("icons/" + k, pngio.read_png_np(p)))
    paper = np.array(review.PAPER, np.float32)
    W = 1300
    rows = []
    head = np.tile(paper, (28, W, 1)).astype(np.float32)
    review._label(head, "B-227 the tool icons (the HUD tool slot, the tree) in B-226's shovel proportion: each at 128 / 48 (slot) / 40 (tree)", 6, 8)
    rows.append(head)

    def cell_row(items, label):
        r = np.tile(paper, (196, W, 1)).astype(np.float32)
        review._label(r, label, 6, 4, scale=1)
        x = 10
        for name, im in items:
            RT._ov(r, im, x, 24)
            RT._ov(r, shrink(im, 48), x + 136, 24)
            RT._ov(r, shrink(im, 40), x + 192, 24)
            review._label(r, name.replace("icons/", ""), x, 166, scale=1)
            x += 256
        return r
    rows.append(cell_row(five, "the five tool icons: the shovel (B-226, exported), the Beam, the Grapple, the Survey, the Builder"))
    rows.append(cell_row(neigh, "their neighbours as exported: The Beam's tree node, two item icons"))
    for s, what in ((48, "a row at 48 px as the HUD slot shows them"), (40, "a row at 40 px as the tree shows them")):
        r = np.tile(paper, (s + 34, W, 1)).astype(np.float32)
        review._label(r, what + " (the five, then the neighbours)", 6, 4, scale=1)
        x = 10
        for _n, im in five + neigh:
            RT._ov(r, shrink(im, s), x, 22)
            x += s + 16
        rows.append(r)
    lines = []
    for key, img in five:
        bad = checks(key, img)
        hit = v3.palette_hits(img, "earth")[0] * 100
        lines.append(f"{key}: {img.shape[1]}x{img.shape[0]}, palette {hit:.1f}%" + ("; " + "; ".join(bad) if bad else ", inside the 2 px margin"))
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-227 design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_tool_icons_v3.py <review png>
    preview(sys.argv[1])
    RT.fakegp.restore()
