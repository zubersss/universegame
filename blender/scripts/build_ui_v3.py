"""B-146 (C3 UI art designs; contract v3.1 §11.6): paper panels as 9-slice sheets ("slice": [l, t, r, b] in the json), the
planet title cards ui/titlecards/<planet> (<= 1920x540, the name lettered in Limelight as drawn ink, one painted vignette,
intertitle style) and the Film-effects toggle's switch. Earth palette for the paper, each planet's palette for its card.
export() writes them for B-151 (render.py's ui_set row); nothing exports until that card opens.

  ui/panels/pause      192x192  slice 48 48 48 48  cream paper, a mustard rule inside the ink edge, corner curls
  ui/panels/settings   192x224  slice 48 80 48 48  the same paper with a teal header band (U-102's settings)
  ui/panels/inventory  192x192  slice 48 48 48 48  a darker card paper with an umber rule and stitched corners
  ui/panels/sign       192x128  slice 40 40 40 40  a hand-painted wooden sign: mustard boards, umber grain, four nails
  ui/panels/scroll     256x160  slice 64 28 64 28  a parchment with rolled ends (the rolls live in the l / r slices)
  ui/titlecards/<earth|mars|mercury>  1600x450 (exported 1600x452: one transparent row top + bottom for BC7) an ornate
                                      double ink border, a painted oval vignette, the name in Limelight
  ui/hud/film_switch   64x96 x2  the Film-effects toggle: a brass lever on a round plate; one 132x96 sheet, parts off / on

Lettering: Limelight and Patrick Hand are read straight from their TTFs (a minimal TrueType reader: cmap 4, loca, glyf,
hmtx; quadratic curves flattened; contours filled even-odd), then drawn as ink with a slight hand wobble.

  python -I build_ui_v3.py <preview png>                    lock-free preview
  python -I build_ui_v3.py --export <art dir> [--ss N]      the export into a scratch tree (the dry run)
"""
import math
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp, v3  # noqa: E402

try:
    import bpy
    if not hasattr(bpy, "data"):
        raise ImportError
    import gp_draw as G
except ImportError:
    G = fakegp.install()
import gp_raster as GR  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
FONTS = os.path.join(ROOT, "Assets", "_Game", "Fonts")
LIMELIGHT = os.path.join(FONTS, "Limelight", "Limelight-Regular.ttf")
PATRICK = os.path.join(FONTS, "PatrickHand", "PatrickHand-Regular.ttf")
O, I = G.OUTER, G.INNER
PPU = 64


# ---------------------------------------------------------------- a minimal TrueType reader
class TTF:
    def __init__(self, path):
        self.b = open(path, "rb").read()
        n = struct.unpack(">H", self.b[4:6])[0]
        self.t = {}
        for i in range(n):
            tag, _cs, off, ln = struct.unpack(">4sIII", self.b[12 + 16 * i:28 + 16 * i])
            self.t[tag.decode("latin-1")] = (off, ln)
        h = self.t["head"][0]
        self.upem = struct.unpack(">H", self.b[h + 18:h + 20])[0]
        self.loc_long = struct.unpack(">h", self.b[h + 50:h + 52])[0] == 1
        self.nglyphs = struct.unpack(">H", self.b[self.t["maxp"][0] + 4:self.t["maxp"][0] + 6])[0]
        self.nhm = struct.unpack(">H", self.b[self.t["hhea"][0] + 34:self.t["hhea"][0] + 36])[0]
        self.cmap = self._cmap()

    def _cmap(self):
        c = self.t["cmap"][0]
        n = struct.unpack(">H", self.b[c + 2:c + 4])[0]
        for i in range(n):
            pid, eid, off = struct.unpack(">HHI", self.b[c + 4 + 8 * i:c + 12 + 8 * i])
            s = c + off
            if struct.unpack(">H", self.b[s:s + 2])[0] == 4 and pid in (0, 3):
                segx2 = struct.unpack(">H", self.b[s + 6:s + 8])[0]
                seg = segx2 // 2
                ends = struct.unpack(f">{seg}H", self.b[s + 14:s + 14 + segx2])
                starts = struct.unpack(f">{seg}H", self.b[s + 16 + segx2:s + 16 + 2 * segx2])
                deltas = struct.unpack(f">{seg}h", self.b[s + 16 + 2 * segx2:s + 16 + 3 * segx2])
                ro_at = s + 16 + 3 * segx2
                ros = struct.unpack(f">{seg}H", self.b[ro_at:ro_at + segx2])
                m = {}
                for k in range(seg):
                    for ch in range(starts[k], ends[k] + 1):
                        if ch == 0xFFFF:
                            continue
                        if ros[k] == 0:
                            g = (ch + deltas[k]) & 0xFFFF
                        else:
                            a = ro_at + 2 * k + ros[k] + 2 * (ch - starts[k])
                            g = struct.unpack(">H", self.b[a:a + 2])[0]
                            g = (g + deltas[k]) & 0xFFFF if g else 0
                        m[ch] = g
                return m
        raise ValueError("no cmap format 4")

    def advance(self, g):
        h = self.t["hmtx"][0]
        i = min(g, self.nhm - 1)
        return struct.unpack(">H", self.b[h + 4 * i:h + 4 * i + 2])[0]

    def _loca(self, g):
        lo = self.t["loca"][0]
        if self.loc_long:
            a, b = struct.unpack(">II", self.b[lo + 4 * g:lo + 4 * g + 8])
        else:
            a, b = (2 * x for x in struct.unpack(">HH", self.b[lo + 2 * g:lo + 2 * g + 4]))
        return a, b

    def contours(self, g, steps=6):
        """[[(x, y) font units, curves flattened]]"""
        a, b = self._loca(g)
        if a == b:
            return []
        s = self.t["glyf"][0] + a
        nc = struct.unpack(">h", self.b[s:s + 2])[0]
        if nc < 0:                                                   # composite: offsets only (enough for Latin capitals)
            out, p = [], s + 10
            while True:
                flags, gi = struct.unpack(">HH", self.b[p:p + 4])
                p += 4
                if flags & 1:
                    dx, dy = struct.unpack(">hh", self.b[p:p + 4])
                    p += 4
                else:
                    dx, dy = struct.unpack(">bb", self.b[p:p + 2])
                    p += 2
                if flags & 8:
                    p += 2
                elif flags & 0x40:
                    p += 4
                elif flags & 0x80:
                    p += 8
                out += [[(x + dx, y + dy) for x, y in c] for c in self.contours(gi, steps)]
                if not flags & 0x20:
                    return out
        ends = struct.unpack(f">{nc}H", self.b[s + 10:s + 10 + 2 * nc])
        npts = ends[-1] + 1
        p = s + 10 + 2 * nc
        ilen = struct.unpack(">H", self.b[p:p + 2])[0]
        p += 2 + ilen
        flags = []
        while len(flags) < npts:
            f = self.b[p]
            p += 1
            flags.append(f)
            if f & 8:
                r = self.b[p]
                p += 1
                flags += [f] * r
        xs, ys = [], []
        for coords, short, same in ((xs, 2, 16), (ys, 4, 32)):
            v = 0
            for f in flags:
                if f & short:
                    d = self.b[p]
                    p += 1
                    v += d if f & same else -d
                elif not f & same:
                    v += struct.unpack(">h", self.b[p:p + 2])[0]
                    p += 2
                coords.append(v)
        out, st = [], 0
        for e in ends:
            pts = [(xs[i], ys[i], bool(flags[i] & 1)) for i in range(st, e + 1)]
            st = e + 1
            if not pts:
                continue
            if not pts[0][2]:                                         # start on an on-curve point
                k = next((i for i, q in enumerate(pts) if q[2]), None)
                if k is None:
                    a0 = pts[0]
                    pts.insert(0, ((a0[0] + pts[-1][0]) / 2, (a0[1] + pts[-1][1]) / 2, True))
                else:
                    pts = pts[k:] + pts[:k]
            poly = [(pts[0][0], pts[0][1])]
            n = len(pts)
            i = 1
            while i <= n:
                q = pts[i % n]
                if q[2]:
                    poly.append((q[0], q[1]))
                    i += 1
                    continue
                nxt = pts[(i + 1) % n]
                end = (nxt[0], nxt[1]) if nxt[2] else ((q[0] + nxt[0]) / 2, (q[1] + nxt[1]) / 2)
                p0 = poly[-1]
                for t in [j / steps for j in range(1, steps + 1)]:
                    poly.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * q[0] + t * t * end[0],
                                 (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * q[1] + t * t * end[1]))
                i += 2 if nxt[2] else 1
            out.append(poly)
        return out


_FONTS = {}


def font(path):
    if path not in _FONTS:
        _FONTS[path] = TTF(path)
    return _FONTS[path]


def text_mask(path, text, size_px, tracking=0.0, wobble=0.6, seed=0, ss=4):
    """The text's coverage (h x w float32, 0..1) at an em size of size_px: contours XOR-filled (even-odd), the outline
    points nudged by a smooth noise (a drawn hand), box-filtered from ss x."""
    f = font(path)
    k = size_px * ss / f.upem
    rng = np.random.default_rng(seed)
    polys, x = [], 0.0
    for ch in text:
        g = f.cmap.get(ord(ch), 0)
        for c in f.contours(g):
            polys.append([(x + px * k, -py * k) for px, py in c])
        x += f.advance(g) * k + tracking * size_px * ss
    if not polys:
        return np.zeros((1, 1), np.float32)
    allx = [p[0] for c in polys for p in c]
    ally = [p[1] for c in polys for p in c]
    pad = 4 * ss
    x0, y0 = min(allx) - pad, min(ally) - pad
    W_ = int(math.ceil((max(allx) - x0 + pad) / ss)) * ss
    H_ = int(math.ceil((max(ally) - y0 + pad) / ss)) * ss
    m = np.zeros((H_, W_), bool)
    ph = rng.uniform(0, TAU_, 4)
    for c in polys:
        px = np.array([p[0] - x0 for p in c])
        py = np.array([p[1] - y0 for p in c])
        jx = wobble * ss * np.sin(px / (23.0 * ss) + ph[0]) * np.cos(py / (31.0 * ss) + ph[1])
        jy = wobble * ss * np.sin(py / (19.0 * ss) + ph[2]) * np.cos(px / (29.0 * ss) + ph[3])
        m ^= GR._poly_mask(px + jx, py + jy, H_, W_)
    return m.reshape(H_ // ss, ss, W_ // ss, ss).mean(axis=(1, 3)).astype(np.float32)


TAU_ = 2 * math.pi


# ---------------------------------------------------------------- the painting helpers (gp strokes in px / 64 m)
def _pal(planet):
    return {k: h for k, h in v3.PALETTES[planet].items()}


def mats(gp, planet="earth"):
    pal = _pal(planet)

    def m(name, **kw):
        return G.mat(gp, f"ui_{planet}_{name}", **kw)
    out = {"ink": m("ink", fill=None)}
    for key in ("offwhite", "red", "mustard", "teal", "green", "sky", "brown"):
        h = pal[key]
        out[key] = m(key, fill=h)
        out[key + "_f"] = m(key + "_f", fill=h, ink=False)
        out[key + "_sh"] = m(key + "_mid", fill=v3.shadow_of(h, planet), ink=False)
        out[key + "_dp"] = m(key + "_deep", fill=v3.deep_of(h, planet), ink=False)
    return out


def wavy_rect(x0, y0, x1, y1, amp, seed, n=10):
    """A hand-drawn rectangle in px (y down), the long sides gently wavy."""
    rnd = np.random.default_rng(seed)
    pts = []
    for (ax, ay), (bx, by) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        L = math.hypot(bx - ax, by - ay)
        k = max(2, int(L / 24))
        for i in range(k):
            t = i / k
            nx, ny = -(by - ay) / L, (bx - ax) / L
            w = amp * math.sin(t * math.pi * (2 + rnd.integers(0, 2))) * (0 < t)
            pts.append((ax + (bx - ax) * t + nx * w, ay + (by - ay) * t + ny * w))
    return pts


def to_m(pts):
    """px (x right, y down) -> the raster's metres (x right, z up); the frame's pivot is its bottom-left corner."""
    return [(x / PPU, -y / PPU) for x, y in pts]


class Canvas:
    """Strokes in pixel coordinates (y down) for one frame of W x H px."""
    def __init__(self, W, H, planet="earth", ss=4):
        self.W, self.H, self.ss = W, H, ss
        self.gp = fakegp.FakeGP()
        self.M = mats(self.gp, planet)
        self.d = fakegp.FakeDrawing()
        self.dm = G.Xf(self.d, lambda pts: [(x / PPU, (self.H - y) / PPU) for x, y in pts])

    def render(self, seed=3):
        st = fakegp.strokes_of(self.d, self.gp, as_object=("ui", "art"))
        return GR.render_frame(st, self.W, self.H, PPU, (0.0, 0.0), ss=self.ss, seed=seed)


def paper_grain(img, seed, strength=0.035):
    """Paper grain multiplied into the colour where opaque (periodic noise, like the backdrops)."""
    rng = np.random.default_rng(seed)
    H, W = img.shape[:2]
    n = rng.standard_normal((H, W)).astype(np.float32)
    k = np.array([1, 4, 6, 4, 1], np.float32) / 16
    for ax in (0, 1):
        n = np.apply_along_axis(lambda r: np.convolve(np.concatenate([r[-2:], r, r[:2]]), k, mode="valid"), ax, n)
    out = img.astype(np.float32)
    out[..., :3] *= (1 + strength * n / max(float(n.std()), 1e-3))[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- the panels (9-slice)
def curl(d, M, cx, cy, s, flip_x=1, flip_y=1):
    """A small ink corner curl in a slice corner (never crosses into the stretched edges)."""
    pts = [(cx + flip_x * s * (0.2 + 0.8 * t) * math.cos(TAU_ * 0.8 * t), cy + flip_y * s * (0.2 + 0.8 * t) * math.sin(TAU_ * 0.8 * t)) for t in [i / 16 for i in range(17)]]
    G.stroke(d, pts, M["ink"], I)


GRAIN_KEY, GRAIN_PX = "ui/panels/grain", 128


def grain_tile(size=GRAIN_PX, seed=5, strength=0.035):
    """B-208: paper_grain's noise as a tileable overlay (the same blur, wrapped, so the tile is periodic), ink at a low alpha:
    UNITY tiles it at 1 texel = 1 screen px over a flat panel, masked by the panel's alpha; mean darkening ~ strength."""
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((size, size)).astype(np.float32)
    k = np.array([1, 4, 6, 4, 1], np.float32) / 16
    for ax in (0, 1):
        n = np.apply_along_axis(lambda r: np.convolve(np.concatenate([r[-2:], r, r[:2]]), k, mode="valid"), ax, n)
    n /= max(float(n.std()), 1e-3)
    out = np.zeros((size, size, 4), np.uint8)
    out[..., :3] = v3.hex_rgb(v3.INK)
    out[..., 3] = np.rint(np.clip(strength * (n + 1.5), 0.0, 0.16) * 255)
    return out


def panel_paper(W, H, sl, paper="offwhite", rule="mustard", header=None, stitch=False, seed=1, grain=True):
    c = Canvas(W, H)
    d, M = c.dm, c.M
    l_, t_, r_, b_ = sl
    outer = wavy_rect(6, 6, W - 6, H - 6, 1.2, seed)
    G.stroke(d, outer, M[paper + "_f"], 0.0, cyclic=True)
    if header:
        G.stroke(d, wavy_rect(6, 6, W - 6, t_ - 14, 0.8, seed + 1), M[header + "_f"], 0.0, cyclic=True)
        G.stroke(d, [(8, t_ - 14), (W - 8, t_ - 14)], M["ink"], I)
    G.stroke(d, wavy_rect(16, 16, W - 16, H - 16, 0.6, seed + 2), M[rule], I, cyclic=True)      # the inner rule (ink-edged)
    G.stroke(d, wavy_rect(20, 20, W - 20, H - 20, 0.5, seed + 3), M[paper + "_f"], 0.0, cyclic=True)
    if header:
        G.stroke(d, wavy_rect(20, 20, W - 20, t_ - 18, 0.5, seed + 4), M[header + "_f"], 0.0, cyclic=True)
    for (cx, cy, fx, fy) in ((28, 28, 1, 1), (W - 28, 28, -1, 1), (28, H - 28, 1, -1), (W - 28, H - 28, -1, -1)):
        if stitch:
            for k in range(3):
                G.stroke(d, [(cx + fx * (2 + 6 * k), cy + fy * 2), (cx + fx * (6 + 6 * k), cy + fy * 6)], M["ink"], I)
        else:
            curl(d, M, cx + fx * 6, cy + fy * 6, 8, fx, fy)
    G.stroke(d, outer, M["ink"], O, cyclic=True)
    img, w = c.render(seed)
    return (paper_grain(img, seed) if grain else img), w            # B-208: flat for the 9-slice, the grain an overlay


def panel_sign(W, H, sl, seed=11, grain=True):
    c = Canvas(W, H)
    d, M = c.dm, c.M
    board = wavy_rect(6, 6, W - 6, H - 6, 0.8, seed)
    G.stroke(d, board, M["mustard_f"], 0.0, cyclic=True)
    for k in range(1, 3):                                                                # board seams + grain (horizontal: stretches clean)
        y = 6 + (H - 12) * k / 3
        G.stroke(d, [(8, y), (W - 8, y)], M["ink"], I)
        G.stroke(d, [(8, y - 3), (W - 8, y - 3)], M["mustard_sh"], I)
    for k in range(5):
        y = 14 + (H - 28) * (k + 0.5) / 5
        G.stroke(d, [(sl[0], y), (W - sl[2], y + 0.5)], M["mustard_sh"], I)
    G.stroke(d, wavy_rect(6, H - 18, W - 6, H - 6, 0.5, seed + 1), M["mustard_dp"], 0.0, cyclic=True)
    for (x, y) in ((18, 18), (W - 18, 18), (18, H - 18), (W - 18, H - 18)):                # four nails
        G.stroke(d, G.lumpy_ellipse(x, y, 4, 4, n=10, seed=seed + int(x)), M["brown"], I, cyclic=True)
    G.stroke(d, board, M["ink"], O, cyclic=True)
    img, w = c.render(seed)
    return (paper_grain(img, seed, 0.03) if grain else img), w


def panel_scroll(W, H, sl, seed=21, grain=True):
    c = Canvas(W, H)
    d, M = c.dm, c.M
    l_, t_, r_, b_ = sl
    sheet = wavy_rect(l_ - 14, 16, W - r_ + 14, H - 16, 1.0, seed)
    G.stroke(d, sheet, M["offwhite_f"], 0.0, cyclic=True)
    G.stroke(d, wavy_rect(l_ - 14, H - 30, W - r_ + 14, H - 16, 0.6, seed + 1), M["offwhite_sh"], 0.0, cyclic=True)
    G.stroke(d, sheet, M["ink"], O, cyclic=True)
    for side in (0, 1):                                                                  # the rolled ends, in the l / r slices
        x0 = 8 if side == 0 else W - r_ + 6
        x1 = l_ - 6 if side == 0 else W - 8
        roll = wavy_rect(x0, 8, x1, H - 8, 0.4, seed + 2 + side)
        G.stroke(d, roll, M["mustard_f"], 0.0, cyclic=True)
        G.stroke(d, wavy_rect(x0 + (x1 - x0) * 0.62, 10, x1 - 2, H - 10, 0.3, seed + 4 + side), M["mustard_sh"], 0.0, cyclic=True)
        for k in range(3):
            xx = x0 + (x1 - x0) * (0.25 + 0.25 * k)
            G.stroke(d, [(xx, 12), (xx, H - 12)], M["ink"], I)
        for yy in (8, H - 8):                                                            # the roll's knobs
            G.stroke(d, G.lumpy_ellipse((x0 + x1) / 2, yy, (x1 - x0) * 0.32, 5, n=12, seed=seed + 7 + side), M["brown"], I, cyclic=True)
        G.stroke(d, roll, M["ink"], O, cyclic=True)
    img, w = c.render(seed)
    return (paper_grain(img, seed, 0.03) if grain else img), w


PANELS = {   # name: (W, H, slice [l, t, r, b], builder(W, H, sl, grain=True))
    "pause": (192, 192, [48, 48, 48, 48], lambda W, H, sl, **kw: panel_paper(W, H, sl, seed=1, **kw)),
    "settings": (192, 224, [48, 80, 48, 48], lambda W, H, sl, **kw: panel_paper(W, H, sl, header="teal", seed=2, **kw)),
    "inventory": (192, 192, [48, 48, 48, 48], lambda W, H, sl, **kw: panel_paper(W, H, sl, paper="offwhite", rule="brown", stitch=True, seed=3, **kw)),
    "sign": (192, 128, [40, 40, 40, 40], panel_sign),
    "scroll": (256, 160, [64, 28, 64, 28], panel_scroll),
}


def nine_slice(img, sl, W, H):
    """Stretch a 9-slice image to W x H (the corners kept, the edges and the centre stretched): the preview's test."""
    l_, t_, r_, b_ = sl
    h, w = img.shape[:2]
    xs = np.concatenate([np.arange(l_), l_ + (np.arange(W - l_ - r_) * (w - l_ - r_) / max(W - l_ - r_, 1)).astype(int), w - r_ + np.arange(r_)])
    ys = np.concatenate([np.arange(t_), t_ + (np.arange(H - t_ - b_) * (h - t_ - b_) / max(H - t_ - b_, 1)).astype(int), h - b_ + np.arange(b_)])
    return img[ys][:, xs]


# ---------------------------------------------------------------- the title cards
CARD_W, CARD_H = 1600, 450
SUBTITLE = {"earth": "home, and the first launch", "mars": "the first off-world base", "mercury": "the twilight run"}


def vignette(planet, w, h, seed):
    """The painted oval vignette (numpy washes in the planet's palette): Earth hills under a sky, Mars a butte in a
    canyon under butterscotch, Mercury the huge Sun over crater rims under an ink sky."""
    if planet in VIGNETTES_C2:                                                             # B-170: the five later cards
        return VIGNETTES_C2[planet](w, h, np.random.default_rng(seed))
    pal = {k: np.array(v3.hex_rgb(h_), np.float32) / 255 for k, h_ in v3.PALETTES[planet].items()}
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.float32)
    t = yy / h
    if planet == "earth":
        img[:] = pal["sky"] * (1 - 0.3 * t[..., None]) + pal["offwhite"] * 0.3 * t[..., None]
        for k, (base, amp, col) in enumerate(((0.55, 0.08, v3.shadow_of(v3.PALETTES["earth"]["teal"], "earth")), (0.7, 0.07, v3.PALETTES["earth"]["green"]))):
            line = h * (base + amp * np.sin(xx[0] / w * 6.0 + rng.uniform(0, 6)) + 0.03 * np.sin(xx[0] / w * 17 + k))
            img[yy > line[None, :]] = np.array(v3.hex_rgb(col), np.float32) / 255
    elif planet == "mars":
        img[:] = pal["mustard"] * (1 - 0.35 * t[..., None]) + pal["sky"] * 0.35 * t[..., None]
        butte = (yy > h * 0.42) & (np.abs(xx - w * 0.55) < w * (0.16 + 0.25 * np.clip((yy - h * 0.42) / h, 0, 1)))
        img[butte] = pal["red"]
        img[butte & (xx > w * 0.6)] = np.array(v3.hex_rgb(v3.shadow_of(v3.PALETTES["mars"]["red"], "mars")), np.float32) / 255
        img[yy > h * 0.8] = np.array(v3.hex_rgb(v3.shadow_of(v3.PALETTES["mars"]["red"], "mars")), np.float32) / 255
    else:
        img[:] = np.array(v3.hex_rgb(v3.INK), np.float32) / 255
        sun = (xx - w * 0.35) ** 2 + (yy - h * 0.55) ** 2 < (h * 0.42) ** 2
        img[sun] = pal["mustard"]
        img[((xx - w * 0.33) ** 2 + (yy - h * 0.5) ** 2 < (h * 0.2) ** 2)] = pal["offwhite"]
        line = h * (0.72 + 0.04 * np.sin(xx[0] / w * 9.0))
        img[yy > line[None, :]] = pal["offwhite"]
        img[(yy > line[None, :]) & ((xx - w * 0.7) ** 2 / (w * 0.12) ** 2 + (yy - h * 0.82) ** 2 / (h * 0.05) ** 2 < 1)] = pal["brown"]
    img *= (1 + 0.03 * rng.standard_normal((h, w, 1))).astype(np.float32)
    return np.clip(img, 0, 1)


def title_card(planet, seed=31, ss=2):
    """An intertitle card: the planet's paper, an ornate double ink border with corner flourishes, the painted oval
    vignette left, the name in Limelight (drawn ink, a small wobble), a Patrick Hand subtitle. -> RGBA uint8, widths."""
    W, H = CARD_W, CARD_H
    c = Canvas(W, H, planet, ss=ss)                        # ss 2 for the lock-free preview (a 1600 card at ss 4 is ~0.2 GB)
    d, M = c.dm, c.M
    paper = wavy_rect(10, 10, W - 10, H - 10, 1.5, seed)
    G.stroke(d, paper, M["offwhite_f"], 0.0, cyclic=True)
    G.stroke(d, wavy_rect(28, 28, W - 28, H - 28, 0.8, seed + 1), M["ink"], I, cyclic=True)        # the inner border
    for (cx, cy, fx, fy) in ((44, 44, 1, 1), (W - 44, 44, -1, 1), (44, H - 44, 1, -1), (W - 44, H - 44, -1, -1)):
        curl(d, M, cx, cy, 14, fx, fy)
        G.stroke(d, [(cx - fx * 16, cy), (cx + fx * 60, cy)], M["ink"], I)
        G.stroke(d, [(cx, cy - fy * 16), (cx, cy + fy * 40)], M["ink"], I)
    ox, oy, orx, ory = 260, H / 2, 190, 150                                               # the vignette's oval frame
    oval = [(ox + orx * math.cos(a), oy + ory * math.sin(a)) for a in np.linspace(0, TAU_, 72, endpoint=False)]
    G.stroke(d, [(ox + (orx + 12) * math.cos(a), oy + (ory + 12) * math.sin(a)) for a in np.linspace(0, TAU_, 72, endpoint=False)], M["mustard_f"], 0.0, cyclic=True)
    G.stroke(d, paper, M["ink"], O, cyclic=True)
    img, w = c.render(seed)
    img = paper_grain(img, seed, 0.03).astype(np.float32) / 255
    vg = vignette(planet, int(2 * orx), int(2 * ory), seed)                              # the painting inside the oval
    yy, xx = np.mgrid[0:vg.shape[0], 0:vg.shape[1]]
    inside = ((xx + 0.5 - orx) / orx) ** 2 + ((yy + 0.5 - ory) / ory) ** 2 <= 1.0
    y0, x0 = int(oy - ory), int(ox - orx)
    reg = img[y0:y0 + vg.shape[0], x0:x0 + vg.shape[1]]
    reg[..., :3] = np.where(inside[..., None], vg, reg[..., :3])
    c2 = Canvas(W, H, planet, ss=ss)                                                      # the oval's ink ring over the painting
    G.stroke(c2.dm, oval, c2.M["ink"], O, cyclic=True)
    ring, w2 = c2.render(seed + 1)
    rf = ring.astype(np.float32) / 255
    img[..., :3] = rf[..., :3] * rf[..., 3:] + img[..., :3] * (1 - rf[..., 3:])
    ink = np.array(v3.hex_rgb(v3.INK), np.float32) / 255
    name = planet.upper()
    tm = text_mask(LIMELIGHT, name, 190, tracking=0.04, wobble=0.7, seed=seed)            # the name, drawn ink
    tx = int(ox + orx + 60 + (W - (ox + orx + 60) - 60 - tm.shape[1]) / 2)
    ty = int(H * 0.47 - tm.shape[0] / 2)
    sub = img[ty:ty + tm.shape[0], tx:tx + tm.shape[1]]
    sub[..., :3] = ink * tm[..., None] + sub[..., :3] * (1 - tm[..., None])
    sm = text_mask(PATRICK, SUBTITLE[planet], 52, wobble=0.3, seed=seed + 2)
    sx = int(tx + (tm.shape[1] - sm.shape[1]) / 2)
    sy = ty + tm.shape[0] + 10
    sub = img[sy:sy + sm.shape[0], sx:sx + sm.shape[1]]
    sub[..., :3] = ink * sm[..., None] + sub[..., :3] * (1 - sm[..., None])
    return (np.clip(img, 0, 1) * 255).astype(np.uint8), w + w2


# ---------------------------------------------------------------- B-170: the five later title cards (B-151's style)
SUBTITLE.update({"venus": "the station above the acid clouds", "jupiter": "the floating belts and the great spot",
                 "saturn": "the rings and the hexagon", "uranus": "the sideways seasons", "neptune": "the dark winds at the edge"})
CARDS_C2 = ("venus", "jupiter", "saturn", "uranus", "neptune")


def _col(planet, key, tone=None):
    """A palette colour (or "ink") as float rgb, optionally its mid ("sh") or deep ("dp") shadow tone."""
    h_ = v3.INK if key == "ink" else v3.PALETTES[planet][key]
    if tone == "sh":
        h_ = v3.shadow_of(h_, planet)
    elif tone == "dp":
        h_ = v3.deep_of(h_, planet)
    return np.array(v3.hex_rgb(h_), np.float32) / 255


def _grid(w, h):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return yy + 0.5, xx + 0.5


def _space(planet, w, h, rng, density=0.0022):
    """The night sky in the planet's deep brown with a sprinkle of offwhite specks (1-2 px)."""
    img = np.empty((h, w, 3), np.float32)
    img[:] = _col(planet, "brown", "dp")
    s = rng.random((h, w)) < density
    img[s] = _col(planet, "offwhite")
    img[np.roll(s, 1, axis=1) & (rng.random((h, w)) < 0.35)] = _col(planet, "offwhite")
    return img


def _ellipse(xx, yy, cx, cy, rx, ry, rot=0.0):
    """The normalised radius of an (optionally rotated) ellipse: < 1 inside; and its px scale for ink rings."""
    ca, sa = math.cos(rot), math.sin(rot)
    u = (xx - cx) * ca + (yy - cy) * sa
    v = -(xx - cx) * sa + (yy - cy) * ca
    return np.sqrt((u / rx) ** 2 + (v / ry) ** 2), u, v


def _ink(img, e, scale, px=2.0, where=None):
    """A cartoon ink line px wide just inside the edge e == 1 (scale: the px per unit of e at the thinnest side)."""
    m = (e < 1.0) & (e >= 1.0 - px / scale)
    if where is not None:
        m &= where
    img[m] = _col("earth", "ink")


def _banded_disc(img, planet, xx, yy, cx, cy, r, bands, wobble, light=(-0.3, -0.15), lit_r=1.12, seed_ph=1.3):
    """A planet disc: latitude bands (palette keys / tones, top to bottom) with a wavy edge, a two-tone terminator
    (the lit circle offset toward the light; outside it the band's mid shadow), an ink rim. -> the disc mask."""
    e = np.hypot(xx - cx, yy - cy) / r
    disc = e < 1.0
    lat = (yy - cy) / r + wobble * np.sin((xx - cx) / r * 5.0 + seed_ph)
    idx = np.clip(((lat + 1) / 2 * len(bands)).astype(int), 0, len(bands) - 1)
    lit = np.hypot(xx - (cx + light[0] * r), yy - (cy + light[1] * r)) < lit_r * r
    for k, (key, tone) in enumerate(bands):
        m = disc & (idx == k)
        img[m & lit] = _col(planet, key, tone)
        img[m & ~lit] = _col(planet, key, "dp" if tone == "sh" else "sh")
    _ink(img, e, r)
    return disc


def _vig_venus(w, h, rng):
    """The apricot deck: an apricot sky over two scalloped cloud banks, the Sun's disc in the haze, a red aerostat balloon
    with its gondola, the station's plank deck and rail across the bottom."""
    P = "venus"
    yy, xx = _grid(w, h)
    # B-170 reopened (D-164): the sky in three flat palette bands with hand-drawn wavy edges (it was a sky-to-mustard
    # gradient, 76.9 % palette in the B-173 audit): apricot sky, mustard, then mustard's mid shadow toward the banks
    img = np.empty((h, w, 3), np.float32)
    img[:] = _col(P, "sky")
    for frac, key, tone, k in ((0.26, "mustard", None, 5.0), (0.44, "mustard", "sh", 7.0)):
        edge = h * (frac + 0.012 * np.sin(xx[0] / w * k * math.pi + frac * 9) + 0.006 * np.sin(xx[0] / w * 23 + frac * 5))
        img[yy > edge[None, :]] = _col(P, key, tone)
    es, _u, _v = _ellipse(xx, yy, w * 0.2, h * 0.28, h * 0.1, h * 0.1)
    img[es < 1] = _col(P, "offwhite")
    for base, amp, key, tone, k in ((0.6, 0.05, "offwhite", "sh", 7.0), (0.7, 0.05, "offwhite", None, 11.0)):
        ph = rng.uniform(0, 6)
        line = h * (base - amp * np.abs(np.sin(xx[0] / w * k + ph)) + 0.01 * np.sin(xx[0] / w * 31 + ph))
        img[yy > line[None, :]] = _col(P, key, tone)
        top = (yy > line[None, :]) & (yy < line[None, :] + 2.0)
        img[top] = _col(P, key, "sh" if tone is None else "dp")
    cx, cy, rx, ry = w * 0.66, h * 0.3, w * 0.13, h * 0.19                                      # the balloon
    eb, u, _v = _ellipse(xx, yy, cx, cy, rx, ry)
    ball = eb < 1
    img[ball] = _col(P, "red")
    img[ball & (np.abs(np.sin(u / rx * math.pi * 1.5)) < 0.1)] = _col(P, "red", "sh")             # the gores
    img[ball & (u > rx * 0.45)] = _col(P, "red", "sh")
    eh, _u, _v = _ellipse(xx, yy, cx - rx * 0.4, cy - ry * 0.45, rx * 0.16, ry * 0.12)
    img[eh < 1] = _col(P, "offwhite")
    _ink(img, eb, min(rx, ry))
    gy = cy + ry + 14
    for sx in (-1, 1):                                                                         # the cables
        x0, x1 = cx + sx * rx * 0.45, cx + sx * 9
        for j in range(16):
            f = j / 15
            px_, py_ = int(x0 + (x1 - x0) * f), int(cy + ry * 0.88 + (gy - cy - ry * 0.88) * f)
            img[py_:py_ + 2, px_:px_ + 1] = _col(P, "brown")
    gond = (np.abs(xx - cx) < 13) & (yy > gy) & (yy < gy + 11)
    img[gond] = _col(P, "brown")
    img[gond & (yy < gy + 3)] = _col(P, "mustard", "sh")
    deck_y, rail_y = h * 0.84, h * 0.75                                                         # the deck and its rail
    img[(yy > rail_y) & (yy < rail_y + 4)] = _col(P, "brown")
    for x0 in np.arange(6, w, 34):
        img[(yy > rail_y) & (yy < deck_y) & (np.abs(xx - x0) < 2)] = _col(P, "brown")
    deck = yy > deck_y
    img[deck] = _col(P, "mustard", "sh")
    img[deck & (yy < deck_y + 3)] = _col(P, "ink")
    img[deck & ((xx % 28) < 1.6)] = _col(P, "brown")
    img[deck & (yy > deck_y + 3) & (yy < deck_y + 6)] = _col(P, "mustard")
    return img


def _vig_jupiter(w, h, rng):
    """The banded giant with the Spot: the disc filling the medallion's lower half, ten wavy belts, the Great Red Spot
    ringed in offwhite, the terminator crescent, Io in the dark."""
    P = "jupiter"
    yy, xx = _grid(w, h)
    img = _space(P, w, h, rng)
    cx, cy, r = w * 0.54, h * 0.62, h * 0.55
    bands = [("offwhite", None), ("mustard", None), ("sky", None), ("red", None), ("offwhite", None), ("mustard", "sh"),
             ("sky", None), ("red", "sh"), ("offwhite", None), ("mustard", None)]
    disc = _banded_disc(img, P, xx, yy, cx, cy, r, bands, 0.03)
    es, _u, _v = _ellipse(xx, yy, cx - r * 0.05, cy + r * 0.3, r * 0.26, r * 0.13)              # the Spot, ringed
    img[disc & (es < 1.32) & (es >= 1.0)] = _col(P, "offwhite")
    img[disc & (es < 1.0)] = _col(P, "red")
    img[disc & (es < 0.55)] = _col(P, "red", "sh")
    _ink(img, es, r * 0.13, 1.5, disc)
    ei, _u, _v = _ellipse(xx, yy, w * 0.13, h * 0.2, 11, 11)                                    # Io
    img[ei < 1] = _col(P, "mustard")
    img[(ei < 1) & (xx > w * 0.13 + 3)] = _col(P, "mustard", "sh")
    _ink(img, ei, 11, 1.5)
    return img


def _vig_saturn(w, h, rng):
    """The ringed world: a soft-banded disc behind and in front of a tilted ring (sky inner ring, a dark gap, an offwhite
    outer ring), the Hexagon's outline at the north pole."""
    P = "saturn"
    yy, xx = _grid(w, h)
    img = _space(P, w, h, rng)
    cx, cy, r, tilt = w * 0.5, h * 0.52, h * 0.3, -0.3
    er, _u, v = _ellipse(xx, yy, cx, cy, r * 2.15, r * 0.52, tilt)

    def ring(where):
        img[where & (er >= 0.62) & (er < 0.78)] = _col(P, "sky", "sh")
        img[where & (er >= 0.83) & (er < 1.0)] = _col(P, "offwhite")
        img[where & (er >= 0.83) & (er < 0.88)] = _col(P, "mustard")
        _ink(img, er, r * 0.52, 1.5, where)
        img[where & (er >= 0.62) & (er < 0.62 + 1.5 / (r * 0.52))] = _col(P, "ink")
    ring(v < 0)                                                                                # the far half, behind
    bands = [("mustard", None), ("offwhite", None), ("sky", None), ("mustard", None), ("offwhite", None), ("sky", None),
             ("mustard", "sh"), ("offwhite", None)]
    disc = _banded_disc(img, P, xx, yy, cx, cy, r, bands, 0.015, light=(-0.35, -0.2))
    hx, hy, s = cx + r * 0.08, cy - r * 0.8, r * 0.2                                             # the Hexagon (flattened)
    ax, ay = np.abs(xx - hx), np.abs(yy - hy) / 0.45

    def hexm(sz):
        return (ay <= sz * 0.866) & (0.866 * ax + 0.5 * ay <= sz * 0.866)
    img[disc & hexm(s) & ~hexm(s - 2.2)] = _col(P, "brown")
    ring(v >= 0)                                                                               # the near half, over the disc
    return img


def _vig_uranus(w, h, rng):
    """The sideways-lit ice giant: the pole turned to the Sun (left), its offwhite cap and ring-shaped seasons around it,
    the terminator down the disc's right, the thin rings standing near edge-on and upright."""
    P = "uranus"
    yy, xx = _grid(w, h)
    img = _space(P, w, h, rng)
    cx, cy, r = w * 0.5, h * 0.5, h * 0.36
    er, u, _v = _ellipse(xx, yy, cx, cy, r * 0.4, r * 1.62)

    def ring(where):
        for a, b in ((0.9, 0.94), (0.97, 1.0)):
            img[where & (er >= a) & (er < b)] = _col(P, "offwhite", "sh")
    ring(u >= 0)
    e = np.hypot(xx - cx, yy - cy) / r
    disc = e < 1.0
    pole = np.hypot(xx - (cx - r * 0.72), yy - cy)
    img[disc] = np.where(((pole / (r * 0.3)).astype(int) % 2 == 0)[disc][:, None], _col(P, "sky"), _col(P, "teal"))
    img[disc & (pole < r * 0.36)] = _col(P, "offwhite")
    term = (xx - cx) / r > 0.25 * np.sqrt(np.clip(1 - ((yy - cy) / r) ** 2, 0, 1))              # a curved terminator
    img[disc & term] = _col(P, "teal", "sh")
    img[disc & term & ((xx - cx) / r > 0.7)] = _col(P, "teal", "dp")
    _ink(img, e, r)
    ring(u < 0)
    return img


def _vig_neptune(w, h, rng):
    """The dark storm world: the deep-blue disc with two thin teal belts, the Great Dark Spot and its offwhite cirrus
    streaks swept downwind, the night side's crescent, Triton small and pink."""
    P = "neptune"
    yy, xx = _grid(w, h)
    img = _space(P, w, h, rng)
    cx, cy, r = w * 0.47, h * 0.54, h * 0.42
    bands = [("sky", None), ("teal", "sh"), ("sky", None), ("sky", None), ("teal", None), ("sky", None), ("sky", None),
             ("teal", "sh"), ("sky", None)]
    disc = _banded_disc(img, P, xx, yy, cx, cy, r, bands, 0.02, light=(-0.32, -0.18), lit_r=1.1, seed_ph=2.1)
    es, _u, _v = _ellipse(xx, yy, cx - r * 0.15, cy + r * 0.12, r * 0.3, r * 0.15, 0.08)          # the Great Dark Spot
    img[disc & (es < 1.2) & (es >= 1.0)] = _col(P, "sky", "sh")
    img[disc & (es < 1.0)] = _col(P, "brown")
    lat = (yy - cy) / r
    for L, x0, x1 in ((0.32, -0.45, 0.25), (0.36, -0.3, 0.05), (-0.25, -0.55, 0.0), (-0.21, -0.2, 0.35)):   # the cirrus
        k = (xx - cx) / r
        bow = L - 0.05 * (k - x0) * (k - x1)
        img[disc & (np.abs(lat - bow) < 0.022) & (k > x0) & (k < x1)] = _col(P, "offwhite")
    et, _u, _v = _ellipse(xx, yy, w * 0.85, h * 0.2, 9, 9)                                      # Triton
    img[et < 1] = _col(P, "red")
    img[(et < 1) & (yy < h * 0.2 - 3)] = _col(P, "offwhite")
    _ink(img, et, 9, 1.5)
    return img


VIGNETTES_C2 = {"venus": _vig_venus, "jupiter": _vig_jupiter, "saturn": _vig_saturn, "uranus": _vig_uranus, "neptune": _vig_neptune}


def preview_cards(out, art=None, cards=CARDS_C2, note="preview (not exported)"):
    """B-170's review: all eight cards at 1x on one sheet, two columns (Earth / Mars / Mercury from B-151 first). With
    `art` the cards are read back from the export (what UNITY imports); otherwise rendered here at ss 2 (lock-free)."""
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import pngio
    names = list(CARDS) + list(cards)
    cw, ch, g = CARD_W, CARD_H + 2, 12
    W = 2 * cw + 3 * g
    rows = [np.tile(review.PAPER, (28, W, 1)).astype(np.float32)]
    review._label(rows[0], "b-170 the planet title cards at 1x (b-151's style: limelight as drawn ink, the painted medallion, a patrick hand "
                           "subtitle; no faces): earth / mars / mercury (b-151) beside venus / jupiter / saturn / uranus / neptune", 6, 8)
    for r0 in range(0, len(names), 2):
        rr = np.tile(review.PAPER, (ch + 30, W, 1)).astype(np.float32)
        for j, planet in enumerate(names[r0:r0 + 2]):
            path = os.path.join(art, "ui", "titlecards", f"{planet}_color.png") if art else None
            if path and os.path.isfile(path):
                card, src = pngio.read_png_np(path), "exported png"
            else:
                card, src = pad4(title_card(planet)[0]), "rendered ss 2"
            x = g + j * (cw + g)
            review._over(rr, card, x, 26)
            review._label(rr, f"ui/titlecards/{planet} {card.shape[1]}x{card.shape[0]} at 1x ({planet} palette; {src})", x, 6)
        rows.append(rr)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " " + note, 2, img.shape[0] - 16)
    review.write(out, img)
    print("written", out, img.shape)


# ---------------------------------------------------------------- the Film-effects switch (2 frames)
def film_switch(on):
    c = Canvas(64, 96)
    d, M = c.dm, c.M
    plate = G.lumpy_ellipse(32, 60, 26, 26, n=28, lump=0.01, seed=41)
    G.stroke(d, plate, M["mustard"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(36, 64, 18, 18, n=24, lump=0.01, seed=42), M["mustard_sh"], 0.0, cyclic=True)
    for a in (0.3, 2.4, 4.5):                                                            # three screws
        G.stroke(d, G.lumpy_ellipse(32 + 20 * math.cos(a), 60 + 20 * math.sin(a), 2.5, 2.5, n=8, seed=43), M["brown"], I, cyclic=True)
    a = math.radians(35)                                                                  # the lever: up-right (on) / down-left (off)
    tip = (32 + 34 * math.sin(math.radians(28)), 60 - 34 * math.cos(math.radians(28))) if on else (32 - 30 * math.sin(a), 60 + 30 * math.cos(a))
    G.stroke(d, G.hose_outline([(32, 60), tip], 8), M["offwhite"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(tip[0], tip[1], 8, 8, n=14, seed=44), M["red"] if on else M["brown"], O, cyclic=True)
    G.stroke(d, G.lumpy_ellipse(32, 60, 7, 7, n=12, seed=45), M["brown"], I, cyclic=True)
    return c.render(47 + int(on))


# ---------------------------------------------------------------- the export (B-151; contract §11.6)
CARDS = ("earth", "mars", "mercury")
SWITCH_KEY = "ui/hud/film_switch"
SWITCH_PIVOT = [0.5, 0.375]          # the lever's hub on the plate (32, 60 px from the top of 64x96)


def keys(cards=CARDS, panels=True, flat=False):
    """panels False (B-170): the cards alone; B-151's panels and switch are not rewritten. flat (B-208): + the grain overlay."""
    return (([f"ui/panels/{n}" for n in PANELS] if panels else []) + [f"ui/titlecards/{p}" for p in cards] + ([SWITCH_KEY] if panels else [])
            + ([GRAIN_KEY] if flat else []))


def pad4(img):
    """Transparent rows / columns split around the image so both sides are multiples of 4 (BC7 blocks)."""
    h, w = img.shape[:2]
    ph, pw = -h % 4, -w % 4
    return np.pad(img, ((ph // 2, ph - ph // 2), (pw // 2, pw - pw // 2), (0, 0)))


def panel_meta(name, img):
    pw, ph, sl, _fn = PANELS[name]
    meta = {"key": f"ui/panels/{name}", "style": "v3", "ppu": PPU, "pivot": [0.5, 0.5], "width": pw, "height": ph, "slice": list(sl),
            "slice_order": "[left, top, right, bottom] px in from each edge (contract 11.6); Unity's Sprite.border is (left, bottom, right, top)",
            "lettering": "runtime", "lettering_note": "blank panel; UNITY letters it in Patrick Hand"}
    p = []
    l_, t_, r_, b_ = sl
    if img.shape[:2] != (ph, pw):
        p.append(f"png {img.shape[1]}x{img.shape[0]} is not {pw}x{ph}")
    if pw % 4 or ph % 4:
        p.append(f"{pw}x{ph} not a multiple of 4")
    if l_ + r_ >= pw or t_ + b_ >= ph:
        p.append(f"slice {sl} leaves no stretchable centre in {pw}x{ph}")
    return meta, p


def card_meta(planet, img):
    h, w = img.shape[:2]
    meta = {"key": f"ui/titlecards/{planet}", "style": "v3", "ppu": PPU, "pivot": [0.5, 0.5], "width": w, "height": h, "palette": planet,
            "lettering": "baked", "lettering_note": f"{planet.upper()} in Limelight + the subtitle in Patrick Hand, drawn as ink (B-146)",
            "note": f"designed {CARD_W}x{CARD_H}; padded with transparent rows to {w}x{h} (BC7 blocks)"}
    p = []
    if w > 1920 or h > 540:
        p.append(f"{w}x{h} over 1920x540")
    if w % 4 or h % 4:
        p.append(f"{w}x{h} not a multiple of 4")
    return meta, p


def switch_sheet():
    """The two switch frames side by side (gutter 4) + a parts json in the gauges.json manner (rects bottom-left)."""
    frames = [film_switch(on)[0] for on in (False, True)]
    fh, fw = frames[0].shape[:2]
    g = v3.GUTTER
    sheet = np.zeros((fh, 2 * fw + g, 4), np.uint8)
    sheet[:, :fw] = frames[0]
    sheet[:, fw + g:] = frames[1]
    meta = {"key": SWITCH_KEY, "style": "v3", "ppu": PPU, "rect_origin": "bottom_left",
            "parts": [{"name": "off", "rect": [0, 0, fw, fh], "pivot": SWITCH_PIVOT}, {"name": "on", "rect": [fw + g, 0, fw, fh], "pivot": SWITCH_PIVOT}],
            "note": "the Film-effects toggle: off = the lever down-left with an umber knob, on = up-right with a red knob; swap the part on toggle"}
    p = [] if sheet.shape[1] % 4 == 0 and fh % 4 == 0 else [f"switch sheet {sheet.shape[1]}x{fh} not a multiple of 4"]
    return sheet, meta, p


def export(art, ss_card=4, cards=CARDS, panels=True, flat=False):
    """Writes ui/panels/<name>, ui/titlecards/<planet>, ui/hud/film_switch (_color.png + .json) under `art`; raises on any
    check before writing anything. flat (B-208): the panels without baked grain + ui/panels/grain, the tiling overlay.
    -> [(key, w, h, bytes)]"""
    import json
    from meridian import pngio
    built, problems = [], []
    for name, (pw, ph, sl, fn) in (PANELS.items() if panels else ()):
        img, _w = fn(pw, ph, sl, grain=not flat)
        meta, p = panel_meta(name, img)
        if flat:
            meta.update({"grain": GRAIN_KEY, "grain_note": "B-208: flat paper for the 9-slice; tile ui/panels/grain over it at 1 texel = 1 px, masked by this panel's alpha"})
        if v3.palette_hits(img, "earth")[0] < 0.995:
            p.append(f"palette {v3.palette_hits(img, 'earth')[0] * 100:.1f}%")
        built.append((meta["key"], img, meta))
        problems += [f"{name}: {x}" for x in p]
    if flat:
        g = grain_tile()
        built.append((GRAIN_KEY, g, {"key": GRAIN_KEY, "style": "v3", "ppu": PPU, "pivot": [0.5, 0.5], "width": GRAIN_PX, "height": GRAIN_PX,
                                     "tile_x": True, "tile_y": True, "repeat_px": GRAIN_PX, "texel_px": 1, "wrap": "repeat",
                                     "blend": "alpha over the panel (ink at alpha 0-0.16, mean ~0.05), masked by the panel's alpha (a UGUI Mask)",
                                     "note": "B-208: B-151's paper grain, no longer baked into the stretched panels; tiled, never stretched"}))
    for planet in cards:
        img, _w = title_card(planet, ss=ss_card)
        img = pad4(img)
        meta, p = card_meta(planet, img)
        built.append((meta["key"], img, meta))
        problems += [f"{planet} card: {x}" for x in p]
    if panels:
        sheet, meta, p = switch_sheet()
        built.append((SWITCH_KEY, sheet, meta))
        problems += [f"film_switch: {x}" for x in p]
    if problems:
        raise ValueError("UI export checks: " + "; ".join(problems))
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


# ---------------------------------------------------------------- the lock-free preview
def preview(out, note="preview (not exported)"):
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    widths = []
    W = 1960
    rows = []
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, "b-146 c3 ui art designs (previews only): 9-slice paper panels, the planet title cards (limelight as drawn ink), the film-effects switch", 6, 8)
    rows.append(head)
    mh = max(ph for _pw, ph, _sl, _fn in PANELS.values())
    r = np.tile(np.array([0.36, 0.36, 0.40], np.float32), (30 + 2 * mh + 64 + 30, W, 1))  # the panels at 1x + stretched + sample text
    x = 12
    for name, (pw, ph, sl, fn) in PANELS.items():
        img, w = fn(pw, ph, sl)
        widths += w
        review._over(r, img, x, 30)
        big = nine_slice(img, sl, pw + 96, ph + 64)
        review._over(r, big, x, 30 + ph + 12)
        tm = text_mask(PATRICK, {"pause": "Paused", "settings": "Settings", "inventory": "Inventory", "sign": "Base camp",
                                  "scroll": "A message"}[name], 30, wobble=0.2, seed=5)
        tx, ty = x + (pw + 96 - tm.shape[1]) // 2, 30 + ph + 12 + (ph + 64 - tm.shape[0]) // 2
        sub = r[ty:ty + tm.shape[0], tx:tx + tm.shape[1]]
        sub[:] = np.array(v3.hex_rgb(v3.INK), np.float32) / 255 * tm[..., None] + sub * (1 - tm[..., None])
        review._label(r, f"{name} {pw}x{ph} slice {sl}", x, 8, scale=1)
        x += pw + 96 + 30
    for k, on in enumerate((False, True)):
        img, w = film_switch(on)
        widths += w
        review._over(r, img, x + k * 80, 30)
    review._label(r, "film switch off | on", x, 8, scale=1)
    rows.append(r)
    for planet in ("earth", "mars", "mercury"):
        card, w = title_card(planet)
        widths += w
        rr = np.tile(review.PAPER, (CARD_H + 30, W, 1)).astype(np.float32)
        review._over(rr, card, 12, 24)
        review._label(rr, f"ui/titlecards/{planet} {CARD_W}x{CARD_H} at 1x ({planet} palette)", 6, 4)
        rows.append(rr)
    outer = [w for w in widths if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in widths if w[0] < v3.OUTER_SPLIT]
    foot = np.tile(review.PAPER, (30, W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; lettering read from the ttfs (limelight, patrick hand); no faces", 6, 8)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " " + note, 2, img.shape[0] - 16)
    review.write(out, img)
    print("written", out, img.shape)


def preview_flat(out, note="design preview (lock-free, fakegp + numpy)"):
    """B-208: each panel flat with the grain overlay tiled over it (masked by the panel's alpha) at 1x, 4x and an 8:1 strip,
    and the inventory panel's old baked grain stretched 4x for the comparison."""
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    g = grain_tile().astype(np.float32) / 255.0
    ink = g[0, 0, :3]

    def grained(img):
        """The panel composited the way UNITY draws it: the flat 9-sliced panel, the grain tiled at 1 texel = 1 px on top,
        inside the panel's alpha."""
        h, w = img.shape[:2]
        t = np.tile(g, (h // GRAIN_PX + 1, w // GRAIN_PX + 1, 1))[:h, :w]
        f = img.astype(np.float32) / 255.0
        a = t[..., 3:4] * (f[..., 3:4] > 0)
        f[..., :3] = f[..., :3] * (1 - a) + ink * a
        return np.rint(f * 255).astype(np.uint8)
    bg = np.array([0.36, 0.36, 0.40], np.float32)
    rows, W = [], 2480
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, "B-208 B-151's panels flat for the 9-slice + the grain as a tiled overlay (1 texel = 1 px): 1x | 4x | an 8:1 strip", 6, 8)
    rows.append(head)
    for name, (pw, ph, sl, fn) in PANELS.items():
        flat, _w = fn(pw, ph, sl, grain=False)
        tiles = [("1x", grained(flat)), ("4x", grained(nine_slice(flat, sl, 4 * pw, 4 * ph))),
                 ("8:1 strip", grained(nine_slice(flat, sl, 1024, 128)))]
        h = max(t.shape[0] for _l, t in tiles) + 40
        r = np.tile(bg, (h, W, 1)).astype(np.float32)
        x = 12
        for lab, t in tiles:
            review._over(r, t, x, 28)
            review._label(r, f"{name} {lab} ({t.shape[1]}x{t.shape[0]})", x, 8, scale=1)
            x += t.shape[1] + 30
        rows.append(r)
    old, _w = PANELS["inventory"][3](192, 192, [48, 48, 48, 48])
    r = np.tile(bg, (4 * 192 + 40, W, 1)).astype(np.float32)
    review._over(r, nine_slice(old, [48, 48, 48, 48], 768, 768), 12, 28)
    review._over(r, grained(nine_slice(PANELS["inventory"][3](192, 192, [48, 48, 48, 48], grain=False)[0], [48, 48, 48, 48], 768, 768)), 810, 28)
    review._label(r, "inventory at 4x: BEFORE (B-151's baked grain stretched) | AFTER (flat + the tiled overlay)", 12, 8, scale=1)
    rows.append(r)
    gr = np.tile(review.PAPER, (4 * GRAIN_PX + 40, W, 1)).astype(np.float32)
    gt = np.tile(g, (2, 4, 1))
    gp = np.array(review.PAPER, np.float32) * (1 - gt[..., 3:4]) + ink * gt[..., 3:4]
    gr[28:28 + gp.shape[0], 12:12 + gp.shape[1]] = gp
    review._label(gr, f"{GRAIN_KEY} {GRAIN_PX}x{GRAIN_PX} tiled 4x2 over paper (seams must not show)", 12, 8, scale=1)
    rows.append(gr)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " " + note, 2, img.shape[0] - 16)
    review.write(out, img)
    print("written", out, img.shape)


if __name__ == "__main__":
    if sys.argv[1] == "--flat":                                                      # B-208: the lock-free flat-panel preview
        preview_flat(sys.argv[2])
    elif sys.argv[1] == "--cards":                                                   # B-170: the lock-free card preview
        preview_cards(sys.argv[2])
    elif sys.argv[1] == "--export":
        _ss = int(sys.argv[sys.argv.index("--ss") + 1]) if "--ss" in sys.argv else 4
        for _k, _w, _h, _n in export(sys.argv[2], ss_card=_ss):
            print(f"{_k} {_w}x{_h} {_n // 1024} KB")
    else:
        preview(sys.argv[1])
