"""B-128: v3.1 icons for the tile items that have none (U-091: off their home planet they show
nothing once planet bundles unload). Each is `icons/<item key>/base` (the ItemRegistry key, the same
rule as every other icon): a 64x64 drawn cube of the material, ink 2-3 / 1-1.5 px, top face in the
material colour, left face its mid shadow, right face its deep shadow (two tones, D-100), and
material marks on the faces. No faces (D-101). numpy only via meridian.fakegp (no Blender):

  python -I build_icons_v3.py <out_preview.png>          lock-free preview
  render.py "icons/tile_items/v3" (icon_set)             export: icons/<item>/base_color.png + base.json
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp, pngio, v3  # noqa: E402

G = fakegp.install()
P = G.PALETTES["earth"]
O, I = G.OUTER, G.INNER
SIZE = 64
PPU = 64
S = 0.36                                   # half the cube's top-face width (m); the icon is 1 m = 64 px


def mixh(a, b, t):
    return G.rgb_hex([x * (1 - t) + y * t for x, y in zip(G.hex_rgb(a), G.hex_rgb(b))])


# item key -> (top colour, mark style, planet note). Colours from the Earth palette family (Mercury and
# Venus get their own strips in their planet tasks; these mixes stay inside the muted family).
ITEMS = {
    "soil": (mixh(P["brown"], P["mustard"], 0.38), "pebbles", "Earth"),
    "grass": (P["green"], "turf", "Earth (shown as Turf)"),
    "regolith": (mixh(P["red"], P["mustard"], 0.3), "dust", "Mars"),
    "mercury_regolith": (mixh(P["brown"], P["offwhite"], 0.55), "craters", "Mercury"),
    "mercury_basalt": (mixh(P["brown"], P["ink"], 0.35), "vesicles", "Mercury"),
    "sulfide": (mixh(P["mustard"], P["brown"], 0.25), "facets", "Mercury"),
    "tessera": (mixh(P["red"], P["brown"], 0.45), "ridges", "Venus"),
    "snow": (P["offwhite"], "sparkle", "Earth / Mars (not on the card: also icon-less)"),
}


def cube(d, M, style, seed):
    rnd = random.Random(seed)
    cz = 0.06                               # the cube sits a little above the icon's bottom
    h = 0.40                                # side height
    top = [(0.0, cz + h + S * 0.5), (S, cz + h + S * 0.25), (0.0, cz + h), (-S, cz + h + S * 0.25)]
    top = [(x, z - 0.0) for x, z in top]
    t_l, t_b, t_r = top[3], top[2], top[1]
    left = [t_l, t_b, (t_b[0], t_b[1] - h), (t_l[0], t_l[1] - h)]
    right = [t_b, t_r, (t_r[0], t_r[1] - h), (t_b[0], t_b[1] - h)]
    # wobble the corners a hair (no perfect geometry)
    jit = lambda pts: [(x + rnd.uniform(-0.008, 0.008), z + rnd.uniform(-0.008, 0.008)) for x, z in pts]  # noqa: E731
    top, left, right = jit(top), jit(left), jit(right)
    G.stroke(d, left, M["mid"], 0.0, cyclic=True)
    G.stroke(d, right, M["deep"], 0.0, cyclic=True)
    G.stroke(d, top, M["top"], 0.0, cyclic=True)
    if style == "turf":                     # a green top over soil sides, blades poking up
        dirt_l = [left[0], left[1], (left[1][0], left[1][1] - 0.08), (left[0][0], left[0][1] - 0.08)]
        dirt_r = [right[0], right[1], (right[1][0], right[1][1] - 0.08), (right[0][0], right[0][1] - 0.08)]
        G.stroke(d, dirt_l, M["top"], 0.0, cyclic=True)
        G.stroke(d, dirt_r, M["mid"], 0.0, cyclic=True)
    marks(d, M, style, top, left, right, rnd)
    G.seam(d, [t_l, t_b, t_r], M["ink"])                          # the top face's front edges
    G.seam(d, [t_b, (t_b[0], t_b[1] - h)], M["ink"])              # the front vertical edge
    outline = [top[3], top[0], top[1], right[2], right[3], left[3]]
    G.stroke(d, outline, M["ink"], O, cyclic=True)


def _in(face, u, v):
    """A point inside a quad face by bilinear (u, v) in 0..1."""
    (x0, z0), (x1, z1), (x2, z2), (x3, z3) = face
    a = (x0 + (x1 - x0) * u, z0 + (z1 - z0) * u)
    b = (x3 + (x2 - x3) * u, z3 + (z2 - z3) * u)
    return (a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v)


def marks(d, M, style, top, left, right, rnd):
    if style == "pebbles":
        for f, u, v in ((top, 0.3, 0.4), (top, 0.65, 0.6), (left, 0.5, 0.55), (right, 0.4, 0.4)):
            x, z = _in(f, u, v)
            G.stroke(d, G.lumpy_ellipse(x, z, 0.045, 0.03, n=10, seed=rnd.randint(0, 99)), M["peb"], I, cyclic=True)
        G.specks(d, [_in(right, 0.7, 0.7), _in(left, 0.25, 0.3)], M["ink"])
    elif style == "turf":
        for k in range(5):
            x, z = _in(top, 0.15 + 0.17 * k, 0.5 + 0.2 * math.sin(k))
            G.stroke(d, [(x - 0.02, z), (x + 0.01, z + 0.10 + 0.03 * (k % 2)), (x + 0.025, z)], M["blade"], I, cyclic=True)
        G.specks(d, [_in(left, 0.5, 0.7), _in(right, 0.4, 0.75)], M["ink"])
    elif style == "dust":
        G.specks(d, [_in(f, rnd.uniform(0.15, 0.85), rnd.uniform(0.15, 0.85)) for f in (top, top, top, left, left, right, right)], M["ink"])
        x, z = _in(left, 0.5, 0.5)
        G.hatch(d, x, z, M["ink"], n=2, length=0.07, spacing=0.03, angle_deg=20, seed=1)
    elif style == "craters":
        for f, u, v, r in ((top, 0.4, 0.45, 0.07), (top, 0.75, 0.55, 0.04), (right, 0.5, 0.4, 0.05)):
            x, z = _in(f, u, v)
            G.stroke(d, G.lumpy_ellipse(x, z, r, r * 0.55, n=14, seed=rnd.randint(0, 99)), M["deep_f"], I, cyclic=True)
    elif style == "vesicles":
        for f in (top, top, left, right, right):
            x, z = _in(f, rnd.uniform(0.2, 0.8), rnd.uniform(0.2, 0.8))
            G.stroke(d, G.lumpy_ellipse(x, z, 0.022, 0.018, n=8, seed=rnd.randint(0, 99)), M["hole"], I, cyclic=True)
    elif style == "facets":
        for f in (top, left, right):
            a, b = _in(f, 0.2, 0.3), _in(f, 0.8, 0.7)
            c = _in(f, 0.75, 0.2)
            G.seam(d, [a, c, b], M["ink"])
        x, z = _in(top, 0.35, 0.6)
        G.stroke(d, [(x - 0.03, z), (x, z + 0.03), (x + 0.03, z), (x, z - 0.03)], M["glint"], I, cyclic=True)
    elif style == "ridges":
        for k in range(3):
            G.seam(d, [_in(top, 0.1, 0.25 + 0.25 * k), _in(top, 0.5, 0.2 + 0.25 * k), _in(top, 0.9, 0.25 + 0.25 * k)], M["ink"])
        for f in (left, right):
            G.seam(d, [_in(f, 0.15, 0.45), _in(f, 0.85, 0.5)], M["ink"])
    elif style == "sparkle":
        for f, u, v in ((top, 0.35, 0.4), (right, 0.5, 0.35)):
            x, z = _in(f, u, v)
            G.seam(d, [(x - 0.035, z), (x + 0.035, z)], M["ink"])
            G.seam(d, [(x, z - 0.035), (x, z + 0.035)], M["ink"])
        G.specks(d, [_in(left, 0.5, 0.6)], M["ink"])


def mats(gp, top):
    return {"top": G.mat(gp, "top", fill=top, ink=False), "mid": G.mat(gp, "mid", fill=G.shadow_of(top), ink=False),
            "deep": G.mat(gp, "deep", fill=G.deep_of(top), ink=False), "deep_f": G.mat(gp, "deep_f", fill=G.deep_of(top)),
            "peb": G.mat(gp, "peb", fill=G.shadow_of(P["offwhite"])), "blade": G.mat(gp, "blade", fill=P["green"], behind=True),
            "hole": G.mat(gp, "hole", fill=G.deep_of(top)), "glint": G.mat(gp, "glint", fill=P["offwhite"]),
            "ink": G.mat(gp, "ink", fill=None, ink=True)}


def render_icon(key, seed=0):
    top, style, _note = ITEMS[key]
    gp = fakegp.FakeGP()
    M = mats(gp, top)
    d = fakegp.FakeDrawing()
    cube(d, M, style, seed=seed + 7)
    return fakegp.render(d, gp, SIZE, SIZE, pivot=(0.5, 0.0), ppu=PPU, ss=4, seed=seed + 3)


def export(art, keys=None):
    """Write icons/<key>/base_color.png + base.json (style v3 single image, pivot centre)."""
    out = []
    for k in keys or ITEMS:
        img, w = render_icon(k, seed=len(k))
        a = img[..., 3]
        if a[:2].any() or a[-1:].any() or a[:, :2].any() or a[:, -2:].any():
            raise ValueError(f"icons/{k}/base touches the 2 px edge")
        d = os.path.join(art, "icons", k)
        os.makedirs(d, exist_ok=True)
        n = pngio.write_png(os.path.join(d, "base_color.png"), img)
        with open(os.path.join(d, "base.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"key": f"icons/{k}/base", "style": "v3", "ppu": PPU, "pivot": [0.5, 0.5], "icon": True}, f, indent=2)
            f.write("\n")
        out.append((k, n, w))
    return out


def preview(path):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    keys = list(ITEMS)
    W = 16 + len(keys) * (SIZE * 3 + 16)
    can = np.tile(review.PAPER, (SIZE * 3 + 120, W, 1)).astype(np.float32)
    review._label(can, "b-128 tile item icons v3.1 (64x64, two shadow tones, no faces); 3x and 1x; lock-free fakegp", 6, 6)
    allw = []
    for j, k in enumerate(keys):
        img, w = render_icon(k, seed=len(k))
        allw += w
        x = 8 + j * (SIZE * 3 + 16)
        review._over(can, np.repeat(np.repeat(img, 3, 0), 3, 1), x, 26)
        review._over(can, img, x + SIZE, 26 + SIZE * 3 + 6)
        review._label(can, f"icons/{k}", x, SIZE * 3 + 100, scale=1)
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    review._label(can, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior "
                       f"{min(w[1] for w in inner):.1f}-{max(w[2] for w in inner):.1f} px", 6, SIZE * 3 + 106)
    review.write(path, can)
    print("written", path)


if __name__ == "__main__":
    preview(sys.argv[1])
