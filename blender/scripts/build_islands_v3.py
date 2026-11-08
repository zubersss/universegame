"""B-177 (D-161 (4), contract v3.3 11.10; LEAD D-164): the giants' floes as rounded cloud-ice islands. The floe strips'
tops and caps stay; these keys under terrain/<giant>/ draw the rest (gp_draw via fakegp + numpy; the giant's palette tones):

  island_belly        512x128, tiles in x every 8 m, mapped along a floe's underside outline (u = world x x 64 mod 512,
                      v = the signed normal distance); the INK EDGE ON ROW 8 = the sprite's pivot; above it a short tuck of fill
                      under the floe, below it the rounded belly - cream cloud-ice lobes, icicles, wisps - hanging up to
                      1.875 m, transparent below its ragged edge
  island_end_l / _r   128x128, pivot on the outline row at the floe's end: the belly's rounded end climbing to meet the
                      floe strip's cap_left / cap_right
  under_haze_<deck>   512x512, its own texture (Repeat), world space below the floe line where the deck's set has no paint
                      (u = x / 8, v = y / 8): soft painted haze in the deck's palette, no ink, no hard edges; the tile is
                      periodic both ways (a gradient inside a repeating tile would band every 8 m), so "darker toward the
                      deck's floor" is UNITY's depth tint over it (proposed to LEAD with the preview)

  python -I build_islands_v3.py <preview dir> [giant]   lock-free design preview: review_b177_<giant>_islands_preview.png

PAUSED for B-178 (LEAD 05:0x). The 05:07 preview reads right (two rows of cloud lobes, softer long haze). Still to do before it goes to LEAD:
  - the belly's tile copies p99 49: wrap each lobe on its own (wrapped_x per lobe, all copies of lobe i before lobe i+1) so the
    stacking is the same at both edges, and give the 2-tile check a copy at +2L
  - island_end: draw the main lobe's ink before the front lobe, move the front lobe lower-right (it reads as a bubble)
  - the wisps read as tan smiles: thinner or dropped
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp, v3  # noqa: E402

try:
    import bpy
    if not hasattr(bpy, "data"):
        raise ImportError
    import gp_draw as G
except ImportError:
    bpy = None
    G = fakegp.install()
import gp_raster as GR  # noqa: E402

O, I = G.OUTER, G.INNER
PPU = 64
TAU = 2 * math.pi
ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
BELLY_W, BELLY_H, OUT_ROW = 512, 128, 8
DECKS = {"jupiter": ["deck1", "deck2", "deck3", "deep"]}


def colours(giant):
    P = v3.PALETTES[giant]
    sh = lambda k: v3.shadow_of(P[k], giant)  # noqa: E731
    dp = lambda k: v3.deep_of(P[k], giant)  # noqa: E731
    if giant == "jupiter":
        return {"cloud": P["offwhite"], "cloud_sh": sh("offwhite"), "cloud_dp": dp("offwhite"), "ice": P["teal"], "ice_hi": P["offwhite"],
                "wisp": P["sky"],
                "haze": {"deck1": (P["offwhite"], P["sky"]), "deck2": (P["sky"], sh("mustard")), "deck3": (sh("mustard"), sh("red")),
                         "deep": (dp("red"), P["brown"])}}
    raise ValueError(f"B-177: {giant} comes after Jupiter's preview")


def mats(gp, giant):
    C = colours(giant)
    M = {"ink": G.mat(gp, f"is_{giant}_ink", fill=None, ink=True)}
    for k, h in C.items():
        if isinstance(h, str):
            M[k] = G.mat(gp, f"is_{giant}_{k}", fill=h, ink=False)
            M[k + "_i"] = G.mat(gp, f"is_{giant}_{k}_i", fill=h)
    return M


def _arc(c, zc, rx, rz, a0, a1, n=24):
    return [(c + rx * math.cos(a0 + (a1 - a0) * i / n), zc + rz * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _hung(c, zc, rx, rz, n=48):
    """A lobe's ellipse with its top clamped to the outline (z <= 0): (fill polygon, its arc below the outline)."""
    pts = [(x, min(z, 0.0)) for x, z in _arc(c, zc, rx, rz, 0.0, TAU, n)]
    if zc + rz <= 0:
        return pts, pts
    s = min(1.0, -zc / rz)
    a0, a1 = math.pi - math.asin(s), TAU + math.asin(s)
    return pts, _arc(c, zc, rx, rz, a0, a1, n)


def _layout(L):
    """Two rows of cloud-ice lobes per 8 m: a back row (deeper, in shade) and a front row (shallower, lit), each (c, zc, rx, rz)."""
    rnd = random.Random(1771)
    back, front = [], []
    for i in range(5):
        dep, rx = rnd.uniform(0.95, 1.20), rnd.uniform(0.95, 1.12)
        back.append((L * (i + 0.5 + rnd.uniform(-0.12, 0.12)) / 5, -dep * 0.38, rx, dep * 0.62))
    for i in range(6):
        dep, rx = rnd.uniform(0.55, 0.82), rnd.uniform(0.66, 0.84)
        front.append((L * (i + rnd.uniform(-0.08, 0.08)) / 6, -dep * 0.40, rx, dep * 0.60))
    return back, front


def _bottom(x, lobes, L):
    z = 0.0
    for c, zc, rx, rz in lobes:
        for off in (-L, 0.0, L):
            u = (x - c - off) / rx
            if abs(u) < 1:
                z = min(z, zc - rz * math.sqrt(1 - u * u))
    return z


def _crescent(c, zc, rx, rz, a0=math.pi * 1.02, a1=math.pi * 1.62):
    """The lobe's shaded lower-left crescent."""
    outer = _arc(c, zc, rx * 0.985, rz * 0.985, a0, a1, 14)
    inner = _arc(c + rx * 0.10, zc + rz * 0.12, rx * 0.86, rz * 0.80, a0, a1, 14)
    return [(x, min(z, 0.0)) for x, z in outer + inner[::-1]]


def draw_belly(d, M, giant="jupiter", k=0):
    L = BELLY_W / PPU
    back, front = _layout(L)
    allb = back + front
    rnd = random.Random(1772)
    icicles = [(i, rnd.uniform(-0.3, 0.3), rnd.uniform(0.22, 0.32)) for i in (0, 2, 3)]
    wisps = [1, 4]
    sil = [(L * i / 256, _bottom(L * i / 256, allb, L)) for i in range(257)]

    def body(dx, _dz):
        for c, zc, rx, rz in back:                                                               # the back row, in shade
            fill, arc = _hung(c + dx, zc, rx, rz)
            G.stroke(d, fill, M["cloud_sh"], 0.0, cyclic=True)
            G.stroke(d, arc, M["ink"], I)
        for j, (c, zc, rx, rz) in enumerate(front):                                               # the front row, lit
            fill, arc = _hung(c + dx, zc, rx, rz)
            G.stroke(d, fill, M["cloud"], 0.0, cyclic=True)
            G.stroke(d, _crescent(c + dx, zc, rx, rz), M["cloud_sh"], 0.0, cyclic=True)
            G.stroke(d, arc, M["ink"], I)
            G.hatch(d, c + dx - rx * 0.45, zc - rz * 0.30, M["ink"], n=3, length=0.07, spacing=0.03, angle_deg=60, seed=j)
        G.stroke(d, [(x + dx, z) for x, z in sil], M["ink"], O)                                   # the silhouette
        G.stroke(d, [(dx, 0.0), (L + dx, 0.0)], M["ink"], O)                                      # THE INK EDGE on row 8
        for i in wisps:                                                                           # wisps trailing the deep lobes
            c, zc, rx, rz = back[i]
            a0, a1 = math.pi * 1.30, math.pi * 1.78
            G.stroke(d, _arc(c + dx, zc, rx + 0.06, rz + 0.09, a0, a1, 16) + _arc(c + dx + 0.04, zc, rx * 0.97, rz * 0.985, a1, a0, 16),
                     M["wisp_i"], I, cyclic=True)
        for i, off, ln in icicles:                                                                # icicles under the back row
            c = back[i][0] + off
            z = _bottom(c, allb, L) + 0.03
            G.stroke(d, [(c + dx - 0.05, z), (c + dx + 0.005, z - ln), (c + dx + 0.05, z)], M["ice_i"], I, cyclic=True)
    wrapped_x(body, L)


_CUR = None
_GROUPS = []


def wrapped_x(fn, L):
    """fn(dx, 0) at -L, 0, +L; the copies share the centre copy's stroke ids (identical ink jitter, contract 11.9's check)."""
    ranges, master = [], 1
    for dx in (-L, 0.0, L):
        n0 = len(_CUR.strokes) if _CUR is not None else 0
        fn(dx, 0.0)
        ranges.append((n0, len(_CUR.strokes) if _CUR is not None else 0))
    if _CUR is not None:
        _GROUPS.append((master, ranges))


def draw_end(side):
    def fn(d, M, giant="jupiter", k=0):
        """The belly's rounded end, drawn over the belly: from the floe's end on the outline (x = 0, z = 0) a short drop, then a
        cloud lobe bulging out past the floe's side and rounding under it, deep enough to cover the belly's cut at x = 0; a lit
        front lobe overlapping it. Drawn for the left end, mirrored for the right."""
        s = 1 if side == "l" else -1
        X = lambda pts: [(s * x, z) for x, z in pts]  # noqa: E731
        c, zc, rx, rz = 0.36, -0.66, 0.72, 0.68
        top = math.asin(min(1.0, -zc / rz))
        a_in, a_out = 2.18, TAU + top
        arc = _arc(c, zc, rx, rz, a_in, a_out, 40)
        G.stroke(d, X([(0.0, 0.0)] + arc + [(arc[-1][0], 0.0)]), M["cloud"], 0.0, cyclic=True)
        G.stroke(d, X(_crescent(c, zc, rx, rz, math.pi * 0.85, math.pi * 1.62)), M["cloud_sh"], 0.0, cyclic=True)
        f_c, f_zc, f_rx, f_rz = 0.88, -0.30, 0.44, 0.36                                          # the lit front lobe
        fill, farc = _hung(f_c, f_zc, f_rx, f_rz)
        G.stroke(d, X(fill), M["cloud"], 0.0, cyclic=True)
        G.stroke(d, X(farc), M["ink"], I)
        split = 5.25                                                                              # silhouette ink, then the overlap
        G.stroke(d, X([(0.0, 0.0)] + _arc(c, zc, rx, rz, a_in, split, 30)), M["ink"], O)
        G.stroke(d, X(_arc(c, zc, rx, rz, split, a_out, 12)), M["ink"], I)
        bx = c + 0.10
        bz = zc - rz * math.sqrt(1 - (0.10 / rx) ** 2) + 0.03
        G.stroke(d, X([(bx - 0.05, bz), (bx + 0.005, bz - 0.28), (bx + 0.05, bz)]), M["ice_i"], I, cyclic=True)
        G.hatch(d, s * 0.02, -0.80, M["ink"], n=3, length=0.07, spacing=0.03, angle_deg=60 if s > 0 else 120, seed=3)
    return fn


PIECES = {"island_belly": (draw_belly, BELLY_W, BELLY_H, (0.0, (BELLY_H - OUT_ROW) / BELLY_H)),
          "island_end_l": (draw_end("l"), 128, 128, (0.3, 0.925)), "island_end_r": (draw_end("r"), 128, 128, (0.7, 0.925))}


def render_piece(name, giant="jupiter", mx=1, ss=4):
    global _CUR
    fn, w, h, piv = PIECES[name]
    gp = fakegp.FakeGP()
    M = mats(gp, giant)
    d = fakegp.FakeDrawing()
    _CUR = d
    _GROUPS.clear()
    fn(d, M, giant)
    _CUR = None
    st = fakegp.strokes_of(d, gp)
    for master, ranges in _GROUPS:
        m0, m1 = ranges[master]
        for a, b in ranges:
            if (a, b) != (m0, m1) and b - a == m1 - m0:
                for i in range(m1 - m0):
                    st[a + i]["id"] = st[m0 + i]["id"]
    return GR.render_frame(st, w * mx, h, PPU, piv, ss=ss, seed=1770)


def haze(giant, deck, size=512, seed=0):
    """A periodic soft haze tile: low-pass white noise (FFT, so it wraps both ways), two of the deck's tones blended softly."""
    import numpy as np
    rng = np.random.default_rng(1780 + seed)
    f = np.fft.fftfreq(size)
    fx, fy = np.meshgrid(f, f)
    spec = (rng.normal(size=(size, size)) + 1j * rng.normal(size=(size, size))) * np.exp(-((fx / 0.006) ** 2 + (fy / 0.022) ** 2))  # long in x
    n = np.real(np.fft.ifft2(spec))
    n = (n - n.min()) / (n.max() - n.min() + 1e-9)
    n = 0.5 + 0.34 * np.tanh((n - 0.5) * 2.0)                     # soft and low-contrast, no hard edges
    a, b = colours(giant)["haze"][deck]
    ca, cb = (np.array(v3.hex_rgb(h), np.float32) for h in (a, b))
    img = ca[None, None, :] * (1 - n[..., None]) + cb[None, None, :] * n[..., None]
    out = np.empty((size, size, 4), np.uint8)
    out[..., :3] = np.clip(np.rint(img), 0, 255).astype(np.uint8)
    out[..., 3] = 255
    return out


def preview(out_dir, giant="jupiter"):
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    belly, bw = render_piece("island_belly", giant)
    two, _w2 = render_piece("island_belly", giant, mx=2, ss=1)
    copy_p99 = float(np.percentile(np.abs(two[:, :BELLY_W].astype(np.int32) - two[:, BELLY_W:].astype(np.int32)), 99))
    del two
    end_l, wl = render_piece("island_end_l", giant)
    end_r, wr = render_piece("island_end_r", giant)
    hazes = {dk: haze(giant, dk, seed=i) for i, dk in enumerate(DECKS[giant])}
    W, H = 1920, 900
    img = np.empty((H, W, 3), np.float32)
    sky_layers, _note = review.planet_background(giant, "deck2", W, H, os.path.join(ART, "backgrounds", giant, "deck2"))
    img[:] = sky_layers
    floe_line = 430                                          # the floe's underside outline (panel px)
    hz = hazes["deck2"].astype(np.float32) / 255.0
    y0 = floe_line - 40                                      # UNITY fades the haze in over the backdrop's lower edge
    t = np.clip(np.arange(H - y0, dtype=np.float32) / 160.0, 0.0, 1.0)[:, None, None]
    img[y0:] = np.tile(hz, (2, 4, 1))[:H - y0, :W, :3] * t + img[y0:] * (1 - t)
    # the floe: the ice strip's cap + 12 tiles + cap at 1x, its ground line 2 m above the outline
    strip = pngio.read_png_np(os.path.join(ART, "terrain", giant, "floe_strip_ice_color.png"))
    fr = [strip[:, i * 68:i * 68 + 64] for i in range(10)]
    x0, ncol = 520, 14
    cols = [fr[8]] + [fr[i % 8] for i in range(ncol - 2)] + [fr[9]]
    ground = floe_line - 128
    for i, c in enumerate(cols):
        review._over(img, c, x0 + 64 * i, ground - 24)
    x1 = x0 + 64 * ncol
    bt = np.tile(belly, (1, 3, 1))[:, :x1 - x0]
    review._over(img, bt, x0, floe_line - OUT_ROW)
    review._over(img, end_l, x0 - int(0.3 * 128), floe_line - int((1 - 0.925) * 128))
    review._over(img, end_r, x1 - int(0.7 * 128), floe_line - int((1 - 0.925) * 128))
    try:
        import json
        sm = json.load(open(os.path.join(ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
        shs = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))
        f0 = shs[:sm["frame_height"], :sm["frame_width"]]
        review._over(img, f0, x0 + 300, ground - sm["frame_height"] + int(round(sm["pivot"][1] * sm["frame_height"])))
    except (OSError, KeyError, ValueError):
        pass
    review._label(img, f"b-177 {giant}: a 14 m ice floe (the floe strip + caps) at 1x on deck2 as an island: island_belly under it (ink on row 8), "
                       "island_end_l / _r at its ends, under_haze_deck2 below the floe line; the surveyor", 6, 6)
    rows = [img]
    P = np.empty((40 + 512 + 30, W, 3), np.float32)
    P[:] = review.PAPER
    x = 8
    for dk, hz in hazes.items():
        review._over(P, hz[::2, ::2], x, 40)
        review._label(P, f"under_haze_{dk} (0.5x)", x, 20)
        x += 256 + 16
    review._over(P, np.tile(belly, (1, 2, 1)), 8, 340)
    review._label(P, f"island_belly 512x128 tiled x2 (copies p99 {copy_p99:.0f})", 8, 320)
    review._over(P, end_l, x, 40)
    review._over(P, end_r, x + 150, 40)
    review._label(P, "island_end_l | island_end_r", x, 20)
    rows.append(P)
    lines = []
    for name, fr_, ws in (("island_belly", belly, bw), ("island_end_l", end_l, wl), ("island_end_r", end_r, wr)):
        o = [w for w in ws if w[0] >= v3.OUTER_SPLIT]
        n_ = [w for w in ws if w[0] < v3.OUTER_SPLIT]
        rng = lambda q: f"{min(w[1] for w in q):.1f}-{max(w[2] for w in q):.1f}" if q else "-"  # noqa: E731
        m = v3.EDGE_MARGIN
        edge = name != "island_belly" and (fr_[:m, :, 3].any() or fr_[-m:, :, 3].any() or fr_[:, :m, 3].any() or fr_[:, -m:, 3].any())
        lines.append(f"{name}: ink {rng(o)} / {rng(n_)} px, palette {v3.palette_hits(fr_, giant)[0] * 100:.1f}%{'; TOUCHES THE EDGE' if edge else ''}")
    lines.append("under_haze_<deck>: painted (no palette check), periodic both ways (FFT low-pass), no ink")
    foot = np.empty((30 + 16 * len(lines), W, 3), np.float32)
    foot[:] = review.PAPER
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6, 6 + 16 * i, scale=1)
    out_img = np.vstack(rows + [foot])
    del rows, img
    import time
    review.draw(out_img, time.strftime("%m-%d %H:%M") + " design preview (lock-free, fakegp + numpy)", 2, out_img.shape[0] - 16, (1.0, 1.0, 0.85))
    shape = out_img.shape
    np.clip(out_img, 0.0, 1.0, out=out_img)
    out_img *= 255.0
    np.rint(out_img, out=out_img)
    u8 = np.empty(shape[:2] + (4,), np.uint8)
    u8[..., :3] = out_img
    u8[..., 3] = 255
    del out_img
    out = os.path.join(out_dir, f"review_b177_{giant}_islands_preview.png")
    pngio.write_png(out, u8)
    print("written", out, shape[1], "x", shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":
    preview(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "jupiter")
    fakegp.restore()
