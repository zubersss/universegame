"""B-177 (D-161 (4), contract v3.3 11.10; LEAD D-164): the giants' floes as rounded cloud-ice islands. The floe strips'
tops and caps stay; these keys under terrain/<giant>/ draw the rest (gp_draw via fakegp + numpy; the giant's palette tones):

  island_belly        512x192 (D-166), tiles in x every 8 m, mapped along a floe's underside outline (u = world x x 64 mod
                      512, v = the signed normal distance); the OUTLINE ON ROW 72 = the sprite's pivot. It sorts ABOVE the floe
                      strip: its crown of lit cloud lobes rises ~1.06 m in front of the strip's lower half (only the ice cap
                      shows above it), and the belly hangs ~1.4 m below (lobes, icicles), transparent outside the cloud
  island_end_l / _r   160x256 (D-166), pivot on the outline row at the floe's end: a rounded cloud shoulder wrapping the strip's
                      end from the belly up to 1.8 m (just under its top edge), so no vertical slab side shows; above both
  under_haze_<deck>   512x512, its own texture (Repeat), world space below the floe line where the deck's set has no paint
                      (u = x / 8, v = y / 8): soft painted haze in the deck's palette, no ink, no hard edges; the tile is
                      periodic both ways (a gradient inside a repeating tile would band every 8 m), so "darker toward the
                      deck's floor" is UNITY's depth tint over it (proposed to LEAD with the preview)

  python -I build_islands_v3.py <preview dir> [giant]   lock-free design preview: review_b177_<giant>_islands_preview.png

05:19 preview: the belly's copies p99 0 (each lobe wrapped on its own), the ends' front lobe over the main lobe's overlap ink, no wisps.
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
BELLY_W, BELLY_H, OUT_ROW = 512, 192, 72               # D-166: the outline on row 72
DECKS = {g: ["deck1", "deck2", "deck3", "deep"] for g in ("jupiter", "saturn", "uranus", "neptune")}
BG_SCENE = {"uranus": "deck2_survey"}            # the preview's backdrop (Uranus's decks come in four lightings)


def colours(giant):
    P = v3.PALETTES[giant]
    sh = lambda k: v3.shadow_of(P[k], giant)  # noqa: E731
    dp = lambda k: v3.deep_of(P[k], giant)  # noqa: E731
    if giant == "jupiter":
        return {"cloud": P["offwhite"], "cloud_sh": sh("offwhite"), "cloud_dp": dp("offwhite"), "ice": P["teal"], "ice_hi": P["offwhite"],
                "wisp": P["sky"],
                "haze": {"deck1": (P["offwhite"], P["sky"]), "deck2": (P["sky"], sh("mustard")), "deck3": (sh("mustard"), sh("red")),
                         "deep": (dp("red"), P["brown"])}}
    # Saturn / Uranus / Neptune (LEAD 05:3x: their palettes, the same drawing): the cloud in the giant's offwhite, the ice in its
    # teal; each deck's haze pair = the palette tones nearest its painted backdrop's lower half (sampled 05:3x)
    common = {"cloud": P["offwhite"], "cloud_sh": sh("offwhite"), "cloud_dp": dp("offwhite"), "ice": P["teal"], "ice_hi": P["offwhite"],
              "wisp": P["sky"]}
    if giant == "saturn":
        return dict(common, haze={"deck1": (P["offwhite"], P["sky"]), "deck2": (P["sky"], P["offwhite"]), "deck3": (sh("sky"), dp("offwhite")),
                                  "deep": (P["brown"], dp("red"))})
    if giant == "uranus":
        return dict(common, haze={"deck1": (P["offwhite"], P["sky"]), "deck2": (P["sky"], sh("offwhite")), "deck3": (P["sky"], P["offwhite"]),
                                  "deep": (P["brown"], dp("teal"))})
    if giant == "neptune":
        return dict(common, haze={"deck1": (sh("offwhite"), P["sky"]), "deck2": (P["sky"], sh("teal")), "deck3": (sh("sky"), dp("teal")),
                                  "deep": (P["brown"], dp("sky"))})
    raise ValueError(f"B-177: no island tones for {giant}")


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
    """D-166: the cloud wraps the slab. Four rows of lobes per 8 m, each (c, zc, rx, rz), z up from the underside outline:
    the crown (lit, rising to <= 1.06 m in front of the strip's lower half), the middle row across the outline (lit, in front),
    the lower front lobes (lit) and the back hanging row (shade)."""
    rnd = random.Random(1771)
    top, mid, low, back = [], [], [], []
    for i in range(5):
        t, rx, rz = rnd.uniform(0.88, 1.06), rnd.uniform(0.92, 1.10), rnd.uniform(0.55, 0.65)
        top.append((L * (i + 0.5 + rnd.uniform(-0.12, 0.12)) / 5, t - rz, rx, rz))
    for i in range(4):
        mid.append((L * (i + rnd.uniform(-0.08, 0.08)) / 4, rnd.uniform(-0.20, 0.0), rnd.uniform(1.10, 1.25), rnd.uniform(0.55, 0.65)))
    for i in range(4):
        back.append((L * (i + 0.5 + rnd.uniform(-0.12, 0.12)) / 4, -0.60, rnd.uniform(1.15, 1.30), rnd.uniform(0.62, 0.72)))
    for i in range(5):
        low.append((L * (i + rnd.uniform(-0.08, 0.08)) / 5, rnd.uniform(-0.82, -0.70), rnd.uniform(0.80, 0.95), rnd.uniform(0.42, 0.50)))
    return top, mid, low, back


def _env(x, lobes, L, up, floor):
    """The lobes' upper (up) or lower envelope at x, wrapping over the period, never inside `floor`."""
    z = floor
    for c, zc, rx, rz in lobes:
        for off in (-L, 0.0, L):
            u = (x - c - off) / rx
            if abs(u) < 1:
                h = rz * math.sqrt(1 - u * u)
                z = max(z, zc + h) if up else min(z, zc - h)
    return z


def _crescent(c, zc, rx, rz, a0=math.pi * 1.02, a1=math.pi * 1.62):
    """The lobe's shaded lower-left crescent."""
    outer = _arc(c, zc, rx * 0.985, rz * 0.985, a0, a1, 14)
    inner = _arc(c + rx * 0.10, zc + rz * 0.12, rx * 0.86, rz * 0.80, a0, a1, 14)
    return outer + inner[::-1]


def _lit_lobe(d, M, c, zc, rx, rz, seed, arc=(0.08, 0.92)):
    """A lit lobe: its fill, the shaded lower-left crescent, and ink only along its exposed arc (in half-turns: the upper
    scallop (0.08, 0.92), or the lower one (1.08, 1.92) for a hanging lobe) so it merges into its neighbours."""
    G.stroke(d, _arc(c, zc, rx, rz, 0.0, TAU, 48), M["cloud"], 0.0, cyclic=True)
    G.stroke(d, _crescent(c, zc, rx, rz), M["cloud_sh"], 0.0, cyclic=True)
    G.stroke(d, _arc(c, zc, rx, rz, math.pi * arc[0], math.pi * arc[1], 28), M["ink"], I)
    G.hatch(d, c - rx * 0.45, zc - rz * 0.30, M["ink"], n=3, length=0.07, spacing=0.03, angle_deg=60, seed=seed)


def draw_belly(d, M, giant="jupiter", k=0):
    """Each lobe wraps on its own (all copies of lobe i before lobe i + 1), so the stacking is the same at both tile edges."""
    L = BELLY_W / PPU
    top, mid, low, back = _layout(L)
    rnd = random.Random(1772)
    xs = [L * i / 256 for i in range(257)]
    ztop = [(x, _env(x, top, L, True, 0.55)) for x in xs]
    zbot = [(x, _env(x, back + low, L, False, -0.5)) for x in xs]
    wrapped_x(lambda dx, _dz: G.stroke(d, [(x + dx, z) for x, z in ztop + zbot[::-1]], M["cloud_sh"], 0.0, cyclic=True), L)
    for c, zc, rx, rz in back:                                                                   # the back row: its lower arcs
        wrapped_x(lambda dx, _dz, c=c, zc=zc, rx=rx, rz=rz: G.stroke(d, _arc(c + dx, zc, rx, rz, math.pi * 1.05, math.pi * 1.95, 30),
                                                                    M["ink"], I), L)
    rows = [(lb, (1.08, 1.92)) for lb in low] + [(lb, (0.08, 0.92)) for lb in top + mid]
    for j, (lobe, arc) in enumerate(rows):                                                        # lit lobes, back to front
        wrapped_x(lambda dx, _dz, lobe=lobe, j=j, arc=arc: _lit_lobe(d, M, lobe[0] + dx, lobe[1], lobe[2], lobe[3], j, arc), L)

    def edges(dx, _dz):
        G.stroke(d, [(x + dx, z) for x, z in ztop], M["ink"], O)                                  # the crown in front of the strip
        G.stroke(d, [(x + dx, z) for x, z in zbot], M["ink"], O)                                  # the hanging silhouette
    wrapped_x(edges, L)
    for i in (0, 2, 3):                                                                           # icicles under the back row
        c = back[i][0] + rnd.uniform(-0.3, 0.3)
        z = _env(c, back + low, L, False, -0.5) + 0.03
        ln = rnd.uniform(0.22, 0.30)
        wrapped_x(lambda dx, _dz, c=c, z=z, ln=ln: G.stroke(d, [(c + dx - 0.05, z), (c + dx + 0.005, z - ln), (c + dx + 0.05, z)],
                                                           M["ice_i"], I, cyclic=True), L)


_CUR = None
_GROUPS = []
_COPIES = (-1, 0, 1)                    # the tile offsets drawn (render_piece widens it for the 2-tile check)


def wrapped_x(fn, L):
    """fn(dx, 0) at each offset in _COPIES x L; the copies share the centre copy's stroke ids (identical ink jitter, 11.9's check)."""
    ranges = []
    for m in _COPIES:
        n0 = len(_CUR.strokes) if _CUR is not None else 0
        fn(m * L, 0.0)
        ranges.append((n0, len(_CUR.strokes) if _CUR is not None else 0))
    if _CUR is not None:
        _GROUPS.append((_COPIES.index(0), ranges))


END_LOBES = [(0.80, 0.70, 0.55, 0.48), (0.85, -0.35, 0.55, 0.50), (0.05, 1.27, 0.55, 0.53), (-0.15, 0.45, 0.60, 0.60), (0.15, -0.60, 0.75, 0.78)]


def _inside(x, z, lobes):
    return any(((x - c) / rx) ** 2 + ((z - zc) / rz) ** 2 <= 1.0 for c, zc, rx, rz in lobes)


def draw_end(side):
    def fn(d, M, giant="jupiter", k=0):
        """D-166: a rounded cloud shoulder wrapping the floe's end (x = 0 at the floe's end on the outline, z = 0; x > 0 under
        the floe): five lobes from the hanging belly up to 1.8 m (just under the strip's top edge at 2 m), bulging ~0.75 m past
        the floe's side, so no vertical slab side shows; sorts above the strip and the belly. Drawn for the left end, mirrored."""
        s = 1 if side == "l" else -1
        X = lambda pts: [(s * x, z) for x, z in pts]  # noqa: E731
        for j, (c, zc, rx, rz) in enumerate(END_LOBES):                                            # back to front, the lower in front
            G.stroke(d, X(_arc(c, zc, rx, rz, 0.0, TAU, 48)), M["cloud"], 0.0, cyclic=True)
            G.stroke(d, X(_crescent(c, zc, rx, rz)), M["cloud_sh"], 0.0, cyclic=True)
            G.stroke(d, X(_arc(c, zc, rx, rz, math.pi * 0.10, math.pi * 0.90, 28)), M["ink"], I)
            G.hatch(d, s * (c - rx * 0.45), zc - rz * 0.30, M["ink"], n=3, length=0.07, spacing=0.03, angle_deg=60 if s > 0 else 120, seed=j)
        cx, cz = 0.15, 0.25                                                                         # the union's outline, by ray
        ring = []
        for i in range(180):
            t = TAU * i / 180
            lo, hi = 0.0, 2.6
            for _ in range(22):
                m = (lo + hi) / 2
                if _inside(cx + m * math.cos(t), cz + m * math.sin(t), END_LOBES):
                    lo = m
                else:
                    hi = m
            ring.append((cx + lo * math.cos(t), cz + lo * math.sin(t)))
        outer = [(x < 0.55 or z > 0.95) for x, z in ring]                                         # the silhouette, not the belly side
        start = next(i for i in range(len(ring)) if outer[i] and not outer[i - 1])
        run = []
        for q in range(len(ring) + 1):
            i = (start + q) % len(ring)
            if outer[i]:
                run.append(ring[i])
            elif run:
                G.stroke(d, X(run), M["ink"], O)
                run = []
        if run:
            G.stroke(d, X(run), M["ink"], O)
        bx = 0.25
        bz = -0.60 - 0.78 * math.sqrt(1 - ((bx - 0.15) / 0.75) ** 2) + 0.03
        G.stroke(d, X([(bx - 0.05, bz), (bx + 0.005, bz - 0.28), (bx + 0.05, bz)]), M["ice_i"], I, cyclic=True)
    return fn


END_W, END_H, END_PIV_X = 160, 256, 0.36
PIECES = {"island_belly": (draw_belly, BELLY_W, BELLY_H, (0.0, (BELLY_H - OUT_ROW) / BELLY_H)),
          "island_end_l": (draw_end("l"), END_W, END_H, (END_PIV_X, 0.5)), "island_end_r": (draw_end("r"), END_W, END_H, (1 - END_PIV_X, 0.5))}


def render_piece(name, giant="jupiter", mx=1, ss=4):
    global _CUR, _COPIES
    _COPIES = tuple(range(-1, mx + 1))
    fn, w, h, piv = PIECES[name]
    gp = fakegp.FakeGP()
    M = mats(gp, giant)
    d = fakegp.FakeDrawing()
    _CUR = d
    _GROUPS.clear()
    fn(d, M, giant)
    _CUR, _COPIES = None, (-1, 0, 1)
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


def preview(out_dir, giant="jupiter", S=None, out=None, footnote=None):
    """The design preview (S None), or with S / out / footnote the export's stamped review from the exported frames (main)."""
    import numpy as np
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    if S is None:
        S = {n: (lambda r: ([r[0]], r[1]))(render_piece(n, giant)) for n in PIECES}
        S.update({f"under_haze_{dk}": ([haze(giant, dk, seed=i)], []) for i, dk in enumerate(DECKS[giant])})
    (belly,), bw = S["island_belly"]
    (end_l,), wl = S["island_end_l"]
    (end_r,), wr = S["island_end_r"]
    hazes = {dk: S[f"under_haze_{dk}"][0][0] for dk in DECKS[giant]}
    copy_p99 = copy_diff(giant)
    W, H = 1920, 900
    img = np.empty((H, W, 3), np.float32)
    scene = BG_SCENE.get(giant, "deck2")
    sky_layers, _note = review.planet_background(giant, scene, W, H, os.path.join(ART, "backgrounds", giant, scene))
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
    review._over(img, end_l, x0 - int(END_PIV_X * END_W), floe_line - END_H // 2)
    review._over(img, end_r, x1 - int((1 - END_PIV_X) * END_W), floe_line - END_H // 2)
    try:
        import json
        sm = json.load(open(os.path.join(ART, "characters", "surveyor", "side.json"), encoding="utf-8"))
        shs = pngio.read_png_np(os.path.join(ART, "characters", "surveyor", "side_color.png"))
        f0 = shs[:sm["frame_height"], :sm["frame_width"]]
        review._over(img, f0, x0 + 300, ground - sm["frame_height"] + int(round(sm["pivot"][1] * sm["frame_height"])))
    except (OSError, KeyError, ValueError):
        pass
    review._label(img, f"b-177 {giant}: a 14 m ice floe (the floe strip + caps) at 1x on deck2 as an island: island_belly over its lower half (outline row 72), "
                       "island_end_l / _r shoulders at its ends, under_haze_deck2 below; the surveyor", 6, 6)
    rows = [img]
    P = np.empty((40 + 512 + 40, W, 3), np.float32)
    P[:] = review.PAPER
    x = 8
    for dk, hz in hazes.items():
        review._over(P, hz[::2, ::2], x, 40)
        review._label(P, f"under_haze_{dk} (0.5x)", x, 20)
        x += 256 + 16
    review._over(P, np.tile(belly, (1, 2, 1)), 8, 340)
    review._label(P, f"island_belly 512x192 tiled x2 (copies p99 {copy_p99:.0f})", 8, 320)
    review._over(P, end_l, x, 40)
    review._over(P, end_r, x + 180, 40)
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
    review.draw(out_img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, out_img.shape[0] - 16, (1.0, 1.0, 0.85))
    shape = out_img.shape
    np.clip(out_img, 0.0, 1.0, out=out_img)
    out_img *= 255.0
    np.rint(out_img, out=out_img)
    u8 = np.empty(shape[:2] + (4,), np.uint8)
    u8[..., :3] = out_img
    u8[..., 3] = 255
    del out_img
    out = out or os.path.join(out_dir, f"review_b177_{giant}_islands_preview.png")
    pngio.write_png(out, u8)
    print("written", out, shape[1], "x", shape[0])
    for ln in lines:
        print(ln)


# ---------------------------------------------------------------- the export (render.py's ground_strip_set API; the row's
# "planet" names the giant through use_planet)

GIANT = "jupiter"
KEYS = {}


def use_planet(giant):
    global GIANT, KEYS
    colours(giant)                                       # raises for a giant whose tones are not drawn yet
    GIANT = giant
    KEYS = {n: f"terrain/{giant}/{n}" for n in list(PIECES) + [f"under_haze_{dk}" for dk in DECKS[giant]]}


use_planet(GIANT)


def sheets():
    S, allw = {}, []
    for n in PIECES:
        img, wd = render_piece(n, GIANT)
        S[n] = ([img], wd)
        allw += wd
    for i, dk in enumerate(DECKS[GIANT]):
        S[f"under_haze_{dk}"] = ([haze(GIANT, dk, seed=i)], [])
    return S, allw


def copy_diff(giant=None):
    """Contract 11.9 / 11.10: the belly drawn two tiles wide; p99 of the copies' difference (must be 0)."""
    import numpy as np
    two, _w = render_piece("island_belly", giant or GIANT, mx=2, ss=1)
    return float(np.percentile(np.abs(two[:, :BELLY_W].astype(np.int32) - two[:, BELLY_W:].astype(np.int32)), 99))


def sheet_meta(kn, frames):
    im = frames[0]
    h, w = im.shape[:2]
    piv = PIECES[kn][3] if kn in PIECES else (0.0, 0.0)
    meta = {"key": KEYS[kn], "style": "v3", "contract": "v3.3 11.10", "frame_width": w, "frame_height": h, "columns": 1, "gutter": v3.GUTTER,
            "frames": 1, "fps": v3.FPS, "pivot": [round(piv[0], 6), round(piv[1], 6)], "facing": "right", "ppu": PPU, "animations": []}
    if kn == "island_belly":
        meta.update({"tile_x": True, "repeat_px": BELLY_W, "outline_row": OUT_ROW, "above_px": OUT_ROW, "below_px": BELLY_H - OUT_ROW,
                     "mapping": f"along each floe's underside outline: u = world x x 64 mod 512; v = {OUT_ROW} + (the signed distance below the outline along its normal x 64); the sprite pivot is ON row {OUT_ROW}",
                     "sort": "above the floe strip (its crown covers the strip's lower half; the ice cap's top line stays clear)",
                     "note": "B-177 / D-166: the cloud wraps the slab - a crown of lit lobes ~1.06 m above the outline, the belly and icicles hanging ~1.4-1.7 m below"})
    elif kn.startswith("island_end_"):
        side = "left" if kn.endswith("_l") else "right"
        meta.update({"end": side, "meets": "floe_strip cap_" + side, "sort": "above the floe strip and island_belly (it covers the band's cut at the floe's end)",
                     "note": "D-166: pivot on the outline row at the floe's end; the shoulder rises to 1.8 m (under the strip's top edge at 2 m) and bulges ~0.75 m past the floe's side"})
    else:
        meta.update({"tile_x": True, "tile_y": True, "world_space": True, "standalone": True, "wrap": "repeat", "painted": True,
                     "deck": kn[len("under_haze_"):],
                     "mapping": "u = x / 8, v = y / 8 (world metres) below the floe line where the deck's set has no paint; its own texture, Repeat",
                     "note": "soft, no ink, periodic both ways; the darkening toward the deck's floor is a depth tint over it (D-164 note)"})
    problems = [p for p in v3.validate_sheet(meta, im.shape) if "sum of clip lengths" not in p]
    if kn.startswith("island_end_"):
        m = v3.EDGE_MARGIN
        if im[:m, :, 3].any() or im[-m:, :, 3].any() or im[:, :m, 3].any() or im[:, -m:, 3].any():
            problems.append(f"touches the {m} px edge")
    if kn in PIECES:
        hit, off = v3.palette_hits(im, GIANT)
        if hit < 0.98:
            problems.append(f"palette {hit * 100:.1f}% (off {' '.join(off[:3])})")
    return im, meta, problems


def export(art, S=None):
    import json as _json
    from meridian import pngio
    if S is None:
        S, _w = sheets()
    built, problems = [], []
    for kn, (frames, _ws) in S.items():
        sheet, meta, p = sheet_meta(kn, frames)
        problems += [f"{kn}: {x}" for x in p]
        built.append((kn, sheet, meta))
    within = {"island_belly": copy_diff()}
    if within["island_belly"] != 0:
        problems.append(f"island_belly: tiling copies differ (p99 {within['island_belly']:.0f}; contract 11.9: 0)")
    if problems:
        raise ValueError(f"{GIANT} island set checks: " + "; ".join(problems))
    d = os.path.join(art, "terrain", GIANT)
    os.makedirs(d, exist_ok=True)
    out = []
    for kn, sheet, meta in built:
        n = pngio.write_png(os.path.join(d, kn + "_color.png"), sheet)
        with open(os.path.join(d, kn + ".json"), "w", encoding="utf-8", newline="\n") as f:
            _json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((meta["key"], sheet.shape[1], sheet.shape[0], n))
    return out, within, f"{len(out)} keys, contract v3.3 11.10"


def main(out, S=None, allw=None, footnote=None):
    if S is None:
        S, allw = sheets()
    preview(os.path.dirname(out), GIANT, S=S, out=out, footnote=footnote)


if __name__ == "__main__":
    preview(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "jupiter")
    fakegp.restore()
