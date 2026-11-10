"""B-240 (2) / B-241 / B-243 (the design: coordination/reports/blender/b237_limb_band_design.md; contract 11.5.1, D-195):
the giants' close view. preview() and motion() write only to blender/preview/; export() (B-243, through the manifest row
planets/common/close_view and build_giant_close_export_v3) writes the strips, the pigment tiles and the four close.json.

Above DiscSprite's near zoom a giant is not a magnified picture: it is drawn from planets/<giant>/close.json (the far
disc's own belts, wobble, rim, night crescent and storms: giants_v3) as flat tones, with narrow painted STRIPS laid along
the limb and along every edge at ONE scale fixed to the planet (close.json's strips.texels_per_far_texel, 7.5: a strip
texel is 0.80 screen px at the flight's 6 px per far texel and 1.20 at its 9; B-240 / B-241's sheets stepped the scale).

  the strips (drafts)   limb_band 512x64      the outline: 2.5 px ink with its jitter on row 16, a faint inner shade below it
                        belt_edge 1024x24 x2  a mask: RGB = the lower tone's share across a ragged brushed cut on row 12,
                                              A = a thin ink line its whole length (the far disc's ink dashes and night
                                              hatches are short ribbons of it, placed by close.json's ink_marks);
                                              variant 0 firm, variant 1 faint and streaky
                        spot_rim 512x24       the storm's rim: the same kind of cut, rounder, no dash
                        close_grain 256x256   the paper's fine grain as a multiply tile (multiplier = value / 127.5), laid in
                                              SCREEN space so it never magnifies
                        pigment 128x128       the far disc's own slow tone variation (its coarse grain and pigment fields),
                                              over the far frame's square (multiplier = value / 127.5): without it the tones
                                              would shift by a few per cent at the swap
  close_view()          the software render of what UNITY would draw (the design note's section 5), from the JSON ONLY plus
                        the strips: belts by the far disc's own edge formula, the rim curve, the storm, the night crescent

  python -I build_giant_close_v3.py <review png> [giant]     the sheet: the strips, then the close view at 6 / 7.7 / 9 screen
                                                             px per far texel (VIEWS), each over the far disc magnified
                                                             the same (as it draws today), with the limb's and a dash's
                                                             measured ink width in each row's label
  export(art) / keys() / export_review(out)                  B-243: the files, and the stamped read-back of what was written
"""
import json
import math
import os
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_discs_v3 as D  # noqa: E402
from meridian import pngio, v3  # noqa: E402

ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
SWAP = 6.0                        # DiscSprite.NearAbove: screen px per far texel where the close view takes over
LIMB_H, LIMB_C = 16, 8.0          # the limb band: its height, and the ink's centre line (texel rows from its top)
EDGE_ROW, RING_ROW = 12, 8        # the cut row of the 24-row edge strips, and of the 16-row ring edge
SPACE = np.array([0.17, 0.20, 0.19], np.float32)       # the space behind the planet in the sheet: about the starfield's own
#                                                         tone (the first run's was as dark as the ink: the outline vanished)


def rgb(h):
    return np.array(v3.hex_rgb(h), np.float32) / 255.0


def pnoise(n, cells, seed):
    """Periodic value noise in [-1, 1] along n px: `cells` lattice values, cosine-interpolated (it tiles)."""
    lat = np.random.default_rng(seed).uniform(-1, 1, cells)
    k = np.arange(n) * cells / n
    i = np.floor(k).astype(int)
    w = (1 - np.cos(np.pi * (k - i))) / 2
    return lat[i % cells] * (1 - w) + lat[(i + 1) % cells] * w


def _down(acc, W, H, S):
    """Premultiplied float (H*S, W*S, 4) -> straight-alpha uint8 (H, W, 4)."""
    small = acc.reshape(H, S, W, S, 4).mean(axis=(1, 3))
    a = small[..., 3:4]
    return np.clip(np.rint(np.dstack([np.where(a > 1e-6, small[..., :3] / np.maximum(a, 1e-6), 0), a]) * 255), 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- the strips
def limb_band():
    """512x16, tiles in x: the outline's ink alone (2.5 px, +-20 % along its length, as the far disc's), its centre line on
    LIMB_C with a waver under half a px; transparent either side. (B-240's first band was 64 rows with a faint inner shade;
    LEAD 23:1x: dropped - the far disc has none, and nothing new should appear at the swap.)"""
    W, H, S = 512, LIMB_H, 4
    n = W * S
    y = (np.arange(H * S) + 0.5)[:, None]
    c = (LIMB_C + 0.45 * pnoise(n, 9, 11)) * S
    r = 1.25 * (1 + 0.2 * pnoise(n, 44, 12)) * S
    ink = (np.abs(y - c[None, :]) <= r[None, :]).astype(np.float32)
    acc = np.zeros((H * S, n, 4), np.float32)
    acc[..., :3] = D.PAL["ink"] * ink[..., None]
    acc[..., 3] = ink
    return _down(acc, W, H, S)


def _edge(W, cells, amp, seed, ink=False, streaks=0, H=24, row=EDGE_ROW, fine=0.8):
    """An edge strip W x H: RGB = the lower tone's share (0 above the ragged cut on `row`, 1 below), A = ink."""
    S = 4
    n = W * S
    y = (np.arange(H * S) + 0.5)[:, None]
    b = (row + amp * pnoise(n, cells, seed) + fine * pnoise(n, cells * 3 - 7, seed + 1)) * S
    share = (y > b[None, :]).astype(np.float32)
    rng = np.random.default_rng(seed + 2)
    for _ in range(streaks):                                     # dry-brush streaks: one tone reaching a little into the other
        x0, L, up = int(rng.integers(0, n)), int(rng.integers(24, 70)) * S, rng.uniform() < 0.5
        off = rng.uniform(1.0, 4.5) * S
        xs = np.arange(x0, x0 + L) % n
        yc = b[xs] + (-off if up else off)
        m = np.abs(y - yc[None, :]) <= 0.5 * S
        share[:, xs] = np.where(m, 1.0 if up else 0.0, share[:, xs])
    inkm = np.zeros((H * S, n), np.float32)
    if ink:                                                      # A: one thin ink LINE the strip's whole length, straight on
        r = 0.625 * (1 + 0.2 * pnoise(n, W // 12, seed + 3)) * S   # the cut row (1.25 px, +-20 %): an ink mark is a short ribbon
        cl = (row + 0.3 * pnoise(n, W // 60, seed + 4)) * S        # of it, laid where the far disc has its dash or hatch (the
        inkm = (np.abs(y - cl[None, :]) <= r[None, :]).astype(np.float32)   # first run's one dash per repeat sat on the
    #                                                              strip's own rhythm and crossed the Spot)
    sh = share.reshape(H, S, W, S).mean(axis=(1, 3))
    ia = inkm.reshape(H, S, W, S).mean(axis=(1, 3))
    return np.clip(np.rint(np.dstack([sh, sh, sh, ia]) * 255), 0, 255).astype(np.uint8)


def belt_edge(variant):
    return _edge(1024, 26, 2.2, 21, ink=True) if variant == 0 else _edge(1024, 22, 1.4, 31, ink=True, streaks=70)


def spot_rim():
    return _edge(512, 14, 1.8, 41)


def ring_edge():
    """512x16 (B-241): a ring's edge - a nearly clean cut on row RING_ROW (the rings are crisper than the belts) with the
    interior ink line (1.25 px) in A, for Saturn's inner edge; the outer edge takes the limb band's ink."""
    return _edge(512, 18, 0.7, 61, ink=True, H=16, row=RING_ROW, fine=0.3)


def close_grain():
    g = 1 + 0.03 * D.noise2(np.random.default_rng(51), 256, 0.8)
    v = np.clip(np.rint(g * 127.5), 0, 255).astype(np.uint8)
    return np.dstack([v, v, v, np.full_like(v, 255)])


def pigment(name):
    """128x128 over the far frame's square: (1 + 0.03 coarse) * (1 + 0.05 pigment), the far disc's own two slow fields (its
    0.8 px fibre is left out: that is the screen-space grain's job). The draws are Disc's, in its order."""
    R = D.RADIUS_U[name] * D.SPACE_PPU
    size = int(2 * (R + 10))
    size += (-size) % 4
    nb = size * D.SS
    rng = np.random.default_rng(zlib.crc32(name.encode()) % 1000)
    rng.uniform(0, 6), rng.uniform(0, 6)                         # the rim's two phases
    D.noise2(rng, nb, 0.8 * D.SS)                                # the fibre (drawn, not used)
    f = (1 + 0.03 * D.noise2(rng, nb, 30 * D.SS)) * (1 + 0.05 * D.noise2(rng, nb, 60 * D.SS))
    q = (np.arange(128) + 0.5) / 128 * nb - 0.5
    xx, yy = np.meshgrid(q, q)
    v = np.clip(np.rint(D._bilinear(f, xx, yy) * 127.5), 0, 255).astype(np.uint8)
    return np.dstack([v, v, v, np.full_like(v, 255)]), size


# ---------------------------------------------------------------- sampling
def samp(tex, x, y, wrap_x=True):
    """Bilinear: tex (H, W, C) float at float texel coords (x right, y down; a texel's centre is at +0.5); x wraps (or clamps),
    y clamps."""
    Ht, Wt = tex.shape[:2]
    x = np.asarray(x, np.float64) - 0.5
    y = np.clip(np.asarray(y, np.float64) - 0.5, 0, Ht - 1)
    if not wrap_x:
        x = np.clip(x, 0, Wt - 1)
    x0, y0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = (x - x0)[..., None].astype(np.float32), (y - y0)[..., None].astype(np.float32)
    x1 = (x0 + 1) % Wt if wrap_x else np.minimum(x0 + 1, Wt - 1)
    x0 = x0 % Wt if wrap_x else x0
    y1 = np.minimum(y0 + 1, Ht - 1)
    return (tex[y0, x0] * (1 - fx) + tex[y0, x1] * fx) * (1 - fy) + (tex[y1, x0] * (1 - fx) + tex[y1, x1] * fx) * fy


def strip_scale(m, k):
    """A strip texel's size on screen at m px per far texel: m / k, k = close.json's strips.texels_per_far_texel. ONE scale,
    fixed to the planet (D-195, contract 11.5.1; RULED 7.5 on B-243's desk-check): the flight shows a giant at 6 to 9 px
    per far texel, so a strip texel is 0.80 to 1.20 px and nothing is re-laid. (B-240 / B-241's accepted sheets stepped
    the scale by root 2 from the swap: 6 texels per far texel at zoom 6, 8.49 at 7.7, 12 at 12, i.e. about 1 px a texel.)"""
    return m / k


def ribbon(ink_a, P, E, sc, stats=None):
    """An ink mark: the edge strip's ink line (its A channel) laid along the polyline P (screen px, rows of (x, y)), flat
    ends, the strip's u running along the mark. Writes max alpha into ink_a. stats (a dict): adds the mark's inked pixels
    ("ink") and the pixels on its centre line ("arc"), so a sheet can print the line's mean width as it does the limb's."""
    H, W = ink_a.shape
    half = 3.0 * sc
    x0, x1 = int(max(P[:, 0].min() - half - 1, 0)), int(min(P[:, 0].max() + half + 2, W))
    y0, y1 = int(max(P[:, 1].min() - half - 1, 0)), int(min(P[:, 1].max() + half + 2, H))
    if x1 <= x0 or y1 <= y0:
        return
    X = (np.arange(x0, x1) + 0.5)[None, :]
    Y = (np.arange(y0, y1) + 0.5)[:, None]
    best = np.full((y1 - y0, x1 - x0), 1e9)
    S_, Dn = np.zeros_like(best), np.zeros_like(best)
    run = 0.0
    for (ax, ay), (bx, by) in zip(P[:-1], P[1:]):
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        t = ((X - ax) * dx + (Y - ay) * dy) / (L * L)
        tc = np.clip(t, 0, 1)
        dd = np.hypot(ax + tc * dx - X, ay + tc * dy - Y)
        ok = (t >= 0) & (t <= 1) & (dd < best)
        best = np.where(ok, dd, best)
        S_ = np.where(ok, run + tc * L, S_)
        Dn = np.where(ok, ((X - ax) * dy - (Y - ay) * dx) / L, Dn)
        run += L
    mk = best <= half
    if mk.any():
        sub = ink_a[y0:y1, x0:x1]
        a = samp(E, S_[mk] / sc, EDGE_ROW - Dn[mk] / sc)[..., 3]
        sub[mk] = np.maximum(sub[mk], a)
        if stats is not None:
            stats["ink"] = stats.get("ink", 0) + int((a > 0.5).sum())
            stats["arc"] = stats.get("arc", 0) + int((best < 0.5).sum())


# ---------------------------------------------------------------- the close view, from the json
def close_view(J, T, m, centre, W=1920, H=540, frame=0, space=None, stats=None):
    """J: a loaded close.json; T: the strips as float arrays; m: screen px per far texel; centre: the view's centre (u, v) in
    disc radii; space: the tone behind the planet; stats: a dict that collects the dashes' ink and arc (ribbon). -> (RGB
    float (H, W, 3), the limb's ink alpha, the limb's distance field in px)."""
    space = SPACE if space is None else space
    Rs = J["radius_u"] * D.SPACE_PPU * m
    sc = strip_scale(m, J["strips"]["texels_per_far_texel"])
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5
    u = centre[0] + (xx - W / 2) / Rs
    v = centre[1] - (yy - H / 2) / Rs
    ang, r = np.arctan2(v, u), np.hypot(u, v)
    rm = J["rim"]
    rim = 1 + rm["a3"] * np.sin(3 * ang + rm["ph3"]) + rm["a5"] * np.sin(5 * ang + rm["ph5"])
    amp, freq = J["edge_wobble"]["amp"], J["edge_wobble"]["freq"]
    phase = 2 * math.pi * frame / J["loop_frames"]
    vv = v + amp * np.sin(freq * math.pi * u + phase) * (1 - v ** 2)        # the far disc's bands(): a belt is vv in (lo, top]
    tops = [b["v_top"] for b in J["belts"]]
    tones = np.array([rgb(b["tone_hex"]) for b in J["belts"]])
    nights = np.array([rgb(b["night_hex"]) for b in J["belts"]])
    idx = np.zeros(vv.shape, np.int64)
    for i in range(1, len(tops)):
        idx[vv <= tops[i]] = i
    day, night = tones[idx], nights[idx]
    ink_a = np.zeros(vv.shape, np.float32)
    E = T["belt_edge"]
    ug = np.linspace(-1.25, 1.25, 8192)                                      # arc length along an edge, from the body's own
    for i in range(1, len(tops)):                                            # left: the strip is fixed to the planet
        vt = tops[i]
        dist = (vv - vt) * Rs / np.sqrt(1 + (amp * freq * math.pi * np.cos(freq * math.pi * u + phase) * (1 - vt ** 2)) ** 2)
        near = np.abs(dist) <= EDGE_ROW * sc                                 # px from the edge, + above it
        if not near.any():
            continue
        sl = amp * freq * math.pi * np.cos(freq * math.pi * ug + phase) * (1 - vt ** 2)
        sg = np.concatenate([[0.0], np.cumsum(np.sqrt(1 + sl[:-1] ** 2) * np.diff(ug))]) * Rs
        t = samp(E, (np.interp(u[near], ug, sg) + 137.0 * i) / sc, EDGE_ROW - dist[near] / sc)
        sh = t[..., :1]
        day[near] = tones[i - 1] * (1 - sh) + tones[i] * sh
        night[near] = nights[i - 1] * (1 - sh) + nights[i] * sh
    for st in J["storms"]:                                                   # a storm: the far disc's blobs(), with a rim
        shift = st["drift_turns_per_loop"] * frame / J["loop_frames"]
        cosl = np.sqrt(np.maximum(1 - v ** 2, 1e-6))
        su = (np.arcsin(np.clip(u / cosl, -1, 1)) / math.pi + shift) % 1.0
        f, th = None, None
        if "streak" in st:                                                   # a chain of blobs: one smooth streak (B-241: the
            p0, p1, rad = st["streak"]["from"], st["streak"]["to"], st["streak"]["radius"]   # scallops read as a grub up close)
            X = ((su - p0["lon_turns"] + 0.5) % 1.0 - 0.5) * math.pi * cosl
            Y = v - p0["v"]
            bx, by = (p1["lon_turns"] - p0["lon_turns"]) * math.pi * cosl, p1["v"] - p0["v"]
            tt = np.clip((X * bx + Y * by) / np.maximum(bx * bx + by * by, 1e-12), 0, 1)
            es = st["streak"].get("end_radius_share", 1.0)                   # tapered ends (LEAD 23:4x: a smooth-ended pill
            f = np.hypot(X - tt * bx, Y - tt * by) - rad * (es + (1 - es) * np.sin(np.pi * tt) ** 0.6)   # is not a cirrus streak)
            th = (tt * np.hypot(bx, by) + np.arctan2(Y - tt * by, X - tt * bx) * rad) * Rs
        for b in ([] if f is not None else st["blobs"]):
            dls = ((su - b["lon_turns"] + 0.5) % 1.0 - 0.5) * math.pi * cosl
            fb = np.hypot(dls, v - b["v"]) - b["radius"]
            if f is None:
                f, th = fb, np.arctan2(v - b["v"], dls) * b["radius"] * Rs
            else:
                f = np.minimum(f, fb)
        gy, gx = np.gradient(f)
        dist = f / np.maximum(np.hypot(gx, gy), 1e-9)                        # px, - inside
        near = (np.abs(dist) <= EDGE_ROW * sc) & (r < rim)
        ins = (f < 0) & ~near
        day[ins], night[ins] = rgb(st["tone_hex"]), rgb(st["night_hex"])
        if near.any():                                                       # (a streak's outline: belt_edge's ragged cut)
            sh = samp(E if "streak" in st else T["spot_rim"], th[near] / sc, EDGE_ROW - dist[near] / sc)[..., :1]
            day[near] = day[near] * (1 - sh) + rgb(st["tone_hex"]) * sh
            night[near] = night[near] * (1 - sh) + rgb(st["night_hex"]) * sh
    nc = J["night"]                                                          # the night crescent, its edge brushed
    hyp = np.hypot(u - nc["centre"][0], v - nc["centre"][1])
    dn = (hyp - nc["radius"]) * Rs                                           # px, + on the night side
    shn = (dn > 0).astype(np.float32)[..., None]
    near = np.abs(dn) <= EDGE_ROW * sc
    if near.any():
        sn = np.arctan2(v - nc["centre"][1], u - nc["centre"][0]) * nc["radius"] * Rs
        shn[near] = samp(E, sn[near] / sc, EDGE_ROW + dn[near] / sc)[..., :1]
    col = day * (1 - shn) + night * shn
    size = T["far_size"]                                                     # the slow tone variation, then the screen grain
    Rf = J["radius_u"] * D.SPACE_PPU
    col = col * samp(T["pigment"], (u * Rf + size / 2) / size * 128, (size / 2 - v * Rf) / size * 128, wrap_x=False)[..., :1]
    col = col * T["grain"][(yy.astype(np.int64)) % 256, (xx.astype(np.int64)) % 256][..., :1]
    col = np.clip(col, 0, 1)

    def to_px(pu, pv):
        return np.c_[W / 2 + (np.asarray(pu) - centre[0]) * Rs, H / 2 - (np.asarray(pv) - centre[1]) * Rs]
    mk = J["ink_marks"]                                                      # the far disc's marks, where it has them
    ds, hz = mk["dashes"], mk["night_hatches"]
    for vb in ds["edges"]:
        for u0 in ds["u0"]:
            uu = u0 + ds["drift"] * math.sin(phase + vb * ds["drift_per_v"])
            if (abs(uu) + ds["length"]) ** 2 + vb * vb > ds["limit"]:
                continue
            us = np.linspace(uu, uu + ds["length"], 25)
            ribbon(ink_a, to_px(us, vb + ds["wave_amp"] * np.sin(ds["wave_freq"] * us + phase)), E, sc, stats)
    for (u0, v0) in hz["groups"]:
        for j in range(hz["count"]):
            uc, vc, hl = u0 + hz["step"] * j, v0 + hz["step"] * j, hz["length"] / 2
            if uc * uc + vc * vc > hz["limit"]:
                continue
            ribbon(ink_a, to_px([uc - hl, uc + hl], [vc - hl, vc + hl]), E, sc)
    col = D.PAL["ink"] * ink_a[..., None] + col * (1 - ink_a[..., None])
    base = np.broadcast_to(np.asarray(space, np.float32), col.shape).copy()
    ring = ring_layer(J, T, u, v, Rs, sc) if "rings" in J else None          # Saturn: the back half (v > 0) goes under the
    back = (v > 0)[..., None]                                                # globe, the front half over it and its outline
    if ring is not None:
        base = np.where(back, ring[0] + base * (1 - ring[1][..., None]), base)
    out = np.where((r <= rim)[..., None], col, base)
    dl = (r - rim) * Rs                                                      # the limb band: px, + outside
    L = T["limb_band"]
    reps = max(1, round(2 * math.pi * Rs / (L.shape[1] * sc)))               # a whole number of repeats round the limb
    nearl = np.abs(dl) < (LIMB_H / 2) * sc
    la = np.zeros(vv.shape, np.float32)
    t = samp(L, (ang[nearl] / (2 * math.pi)) * reps * L.shape[1], LIMB_C - dl[nearl] / sc)
    out[nearl] = t[..., :3] * t[..., 3:4] + out[nearl] * (1 - t[..., 3:4])
    la[nearl] = t[..., 3]
    if ring is not None:
        out = np.where(back, out, ring[0] + out * (1 - ring[1][..., None]))
    return out.astype(np.float32), la, dl


def ring_layer(J, T, u, v, Rs, sc):
    """Saturn's rings from close.json's "rings", both halves: -> (premultiplied RGB, alpha). Flat-toned bands in the ring's
    own radius rr = hypot(u, v / tilt); ring_edge along every edge (a cut in tone where two bands touch, a cut in alpha at
    the inner edge, the gap's two edges and the outer edge); ink on the inner edge (the strip's line) and on the outer edge
    (the limb band's), as the far rings have. No grain: the far rings have none."""
    rg = J["rings"]
    rr = np.hypot(u, v / rg["tilt"])
    gy, gx = np.gradient(rr)
    gpx = np.maximum(np.hypot(gx, gy), 1e-9)                                 # ring radii per screen px
    phi = np.arctan2(v / rg["tilt"], u)
    bs = rg["bands"]
    col = np.empty(u.shape + (3,), np.float32)
    col[:] = rgb(bs[0]["tone_hex"])
    for b0, b1 in zip(bs[:-1], bs[1:]):                                      # (a band across the gap takes over at mid-gap)
        col[rr > (b0["r_out"] + b1["r_in"]) / 2] = rgb(b1["tone_hex"])
    a = ((rr >= rg["inner"]) & (rr <= rg["outer"]) & ~((rr > rg["gap"][0]) & (rr < rg["gap"][1]))).astype(np.float32)
    ink = np.zeros(u.shape, np.float32)
    RE, LB = T["ring_edge"], T["limb_band"]

    def edge(re):
        dist = (rr - re) / gpx                                               # px, + outward
        return dist, np.abs(dist) <= RING_ROW * sc, phi * re * Rs

    for b0, b1 in zip(bs[:-1], bs[1:]):
        if abs(b0["r_out"] - b1["r_in"]) < 1e-9:                             # two bands touching: a cut in tone
            dist, near, s = edge(b1["r_in"])
            if near.any():
                sh = samp(RE, s[near] / sc, RING_ROW + dist[near] / sc)[..., :1]
                col[near] = rgb(b0["tone_hex"]) * (1 - sh) + rgb(b1["tone_hex"]) * sh
    for re, ring_inside, line in ((rg["inner"], False, "thin"), (rg["gap"][0], True, None), (rg["gap"][1], False, None),
                                  (rg["outer"], True, "outline")):
        dist, near, s = edge(re)
        if not near.any():
            continue
        t = samp(RE, s[near] / sc, RING_ROW + dist[near] / sc)
        a[near] = 1 - t[..., 0] if ring_inside else t[..., 0]
        if line == "thin":
            ink[near] = np.maximum(ink[near], t[..., 3])
        elif line == "outline":
            ink[near] = np.maximum(ink[near], samp(LB, s[near] / sc, LIMB_C - dist[near] / sc)[..., 3])
    return D.PAL["ink"] * ink[..., None] + col * (a * (1 - ink))[..., None], np.maximum(a, ink)


def _far_frame(name, variant, frame=0):
    """One frame of an exported far sheet (premultiplied float) and its json."""
    meta = json.load(open(os.path.join(ART, "planets", name, f"{variant}.json"), encoding="utf-8"))
    sh = pngio.read_png_np(os.path.join(ART, "planets", name, f"{variant}_color.png")).astype(np.float32) / 255.0
    if "frame_width" in meta:
        fw, fh, g, c = meta["frame_width"], meta["frame_height"], meta.get("gutter", v3.GUTTER), meta["columns"]
        sh = sh[(frame // c) * (fh + g):(frame // c) * (fh + g) + fh, (frame % c) * (fw + g):(frame % c) * (fw + g) + fw]
    sh = sh.copy()
    sh[..., :3] *= sh[..., 3:4]
    return sh, meta


def far_view(name, m, centre, W=1920, H=540, frame=0):
    """The exported far disc's frame magnified m times (bilinear, premultiplied), as the game draws a giant today; Saturn
    with its two ring parts, the back one under the globe and the front one over it."""
    fr, meta = _far_frame(name, "disc", frame)
    Rf = meta["radius_px"]
    Rs = Rf * m
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5
    u = centre[0] + (xx - W / 2) / Rs
    v = centre[1] - (yy - H / 2) / Rs

    def layer(im):
        hh, ww = im.shape[:2]
        t = samp(im, u * Rf + ww / 2, hh / 2 - v * Rf, wrap_x=False)
        return np.where(((np.abs(u * Rf) < ww / 2) & (np.abs(v * Rf) < hh / 2))[..., None], t, 0.0)

    parts = [layer(fr)]
    if name == "saturn":
        parts = [layer(_far_frame(name, "rings_back")[0]), parts[0], layer(_far_frame(name, "rings_front")[0])]
    out = np.broadcast_to(SPACE, (H, W, 3)).astype(np.float32)
    for t in parts:
        out = t[..., :3] + out * (1 - t[..., 3:4])
    return out.astype(np.float32)


def seam(img):
    """A tiling strip's wrap against its own neighbouring columns (<= 1.6 passes, as the backdrops' check)."""
    f = img.astype(np.float32)
    return float(np.abs(f[:, -1] - f[:, 0]).mean() / max(float(np.abs(np.diff(f, axis=1)).mean()), 0.5))


# ---------------------------------------------------------------- the sheet
VIEWS = {   # name -> [(label, m, centre)]: the flight's own range (UNITY's reading, the design note's point 11): 6 px per far
    #         texel at the wheel's closest (= the swap), 9 at the end of the entry's push-in; smoke_7's distance (0.6.1: 7.7).
    #         (B-240 / B-241's accepted sheets showed 12 as "the closest"; the game never reaches it.) The first three rows
    #         feed the limb-on-paper insets; Jupiter's fourth is on a dash, for the thin line's measured width at 9.
    "jupiter": [("the wheel's closest (the swap): 6 px per far texel", 6.0, (0.72, -0.36)), ("smoke_7's distance: 7.7", 7.7, (0.76, -0.34)),
                ("the end of the entry's push-in: 9 (the limb)", 9.0, (0.80, -0.30)),
                ("9 again: a dash, two belt edges and the Spot's rim", 9.0, (0.50, -0.30)),
                ("the night crescent's edge, at 6", 6.0, (-0.45, -0.45))],
    "saturn": [("the swap, 6: the front ring over the globe and past its limb", 6.0, (0.72, -0.42)),
               ("the swap, 6: the back ring coming out from behind the globe", 6.0, (0.90, 0.40)),
               ("the push-in's end, 9: the ring's inner edge crossing the limb", 9.0, (0.93, -0.25))],
    "uranus": [("the swap, 6", 6.0, (0.55, 0.25)), ("the push-in's end, 9", 9.0, (0.72, 0.28))],
    "neptune": [("the swap, 6: the dark storm and its companion cloud", 6.0, (0.72, -0.20)),
                ("the push-in's end, 9", 9.0, (0.74, -0.19))],
}
CARD = {"jupiter": "b240"}                           # the preview folder and the sheet's tag per giant (the rest: b241)


def preview(out, name="jupiter", footnote=None):
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    card = CARD.get(name, "b241")
    dd = os.path.join(os.path.dirname(out), card)
    os.makedirs(dd, exist_ok=True)
    jp = os.path.join(dd, f"{name}_close.json")
    with open(jp, "w", encoding="utf-8", newline="\n") as fh:                # the draft, then read back: the view is drawn
        json.dump(D.close_draft(name), fh, indent=2)                         # from the FILE, as UNITY would
        fh.write("\n")
    J = json.load(open(jp, encoding="utf-8"))
    variant = 0 if name in ("jupiter", "saturn") else 1
    pig, far_size = pigment(name)
    S = {"limb_band": limb_band(), "belt_edge_0": belt_edge(0), "belt_edge_1": belt_edge(1), "spot_rim": spot_rim(),
         "ring_edge": ring_edge(), "close_grain": close_grain(), f"{name}_pigment": pig}
    lines = []
    for k, im in S.items():
        n = pngio.write_png(os.path.join(dd, k + "_color.png"), im)
        tile = k not in (f"{name}_pigment",)
        lines.append(f"{k}: {im.shape[1]}x{im.shape[0]}, {n} bytes" + (f", seam {seam(im):.2f}" if tile else ""))
    lines[0] += f", palette {v3.palette_hits(S['limb_band'], 'earth')[0] * 100:.1f}% (its solid pixels: the ink)"
    f32 = {k: v.astype(np.float32) / 255.0 for k, v in S.items()}
    T = {"limb_band": f32["limb_band"], "belt_edge": f32[f"belt_edge_{variant}"], "spot_rim": f32["spot_rim"],
         "ring_edge": f32["ring_edge"], "grain": f32["close_grain"] * 2.0, "pigment": f32[f"{name}_pigment"] * 2.0,
         "far_size": far_size}
    paper = np.array(review.PAPER, np.float32)
    W = 1920
    rows = [np.tile(paper, (30, W, 1)).astype(np.float32)]
    review._label(rows[0], f"{card.upper().replace('B', 'B-')} / B-243 {name}: the close view drawn from {name}_close.json + the strips at ONE scale ({J['strips']['texels_per_far_texel']:g} strip texels per far texel; PREVIEW, nothing exported); each zoom over the far disc magnified the same", 6, 8)
    st = np.tile(paper, (300, W, 1)).astype(np.float32)                      # the strips
    review._label(st, f"the strips at 2x: limb_band 512x16 (the ink alone) | belt_edge 0 and 1 (white = the lower tone's share, red = the ink line that marks are cut from; {name} uses variant {variant}) | spot_rim | ring_edge 512x16 | close_grain at 1x | the pigment tile at 2x", 6, 4, scale=1)

    def put(im, x, y, k=2):
        f = np.repeat(np.repeat(im, k, 0), k, 1)
        st[y:y + f.shape[0], x:x + f.shape[1]] = f

    def vis(e):
        return e[..., :3] * (1 - e[..., 3:4]) + np.array([0.85, 0.15, 0.1], np.float32) * e[..., 3:4]

    lb = f32["limb_band"]
    chk = (((np.arange(LIMB_H)[:, None] // 8 + np.arange(512)[None, :] // 8) % 2) * 0.06 + 0.62)[..., None] * np.ones(3, np.float32)
    put(lb[..., :3] * lb[..., 3:4] + chk * (1 - lb[..., 3:4]), 10, 22)
    y = 22 + 2 * LIMB_H + 6
    for k in ("belt_edge_0", "belt_edge_1", "spot_rim", "ring_edge"):
        put(vis(f32[k])[:, :520], 10, y)
        y += 2 * f32[k].shape[0] + 4
    put(f32["close_grain"][..., :3], 1100, 22, k=1)
    put(f32[f"{name}_pigment"][..., :3], 1380, 22, k=2)
    rows.append(st)
    for label, m, centre in VIEWS[name]:
        dash = {}
        cv, la, dl = close_view(J, T, m, centre, stats=dash)
        fv = far_view(name, m, centre)
        ink = la > 0.5
        arc = int((np.abs(dl) < 0.5).sum())
        kk = J["strips"]["texels_per_far_texel"]
        sc = strip_scale(m, kk)
        limb = (f"limb ink measured {float(ink.sum()) / arc:.2f} px over {arc} px of arc (the strip's own range "
                f"{2.5 * 0.8 * sc:.2f}-{2.5 * 1.2 * sc:.2f})") if arc else "no limb in this window"
        thin = (f"dash ink measured {dash['ink'] / dash['arc']:.2f} px over {dash['arc']} px (the line's own range "
                f"{1.25 * 0.8 * sc:.2f}-{1.25 * 1.2 * sc:.2f})") if dash.get("arc") else "no dash in this window"
        msg = (f"{label}: {kk:g} strip texels per far texel, a strip texel {sc:.2f} px; {limb}; {thin}; the planet's radius on "
               f"screen {J['radius_u'] * D.SPACE_PPU * m:.0f} px")
        lines.append(msg)
        hd = np.tile(paper, (20, W, 1)).astype(np.float32)
        review._label(hd, "CLOSE VIEW, " + msg, 6, 4, scale=1)
        rows += [hd, cv]
        hd = np.tile(paper, (20, W, 1)).astype(np.float32)
        review._label(hd, f"TODAY: the far disc ({name}/disc frame 0) magnified {m:g}x, the same view", 6, 4, scale=1)
        rows += [hd, fv]
        tag = f"{m:g}".replace(".", "_") + ("_night" if "night" in label else "") + f"_{len(rows)}"
        pngio.write_png(os.path.join(dd, f"{name}_close_m{tag}.png"),
                        np.dstack([np.clip(np.rint(cv * 255), 0, 255).astype(np.uint8), np.full(cv.shape[:2], 255, np.uint8)]))
    if name == "neptune":                                                    # B-241: the storm and its cloud are two shapes
        hd = np.tile(paper, (20, W, 1)).astype(np.float32)                   # side by side: the face check, at 2x
        review._label(hd, "the dark storm and its companion cloud at 2x (the face check: two shapes side by side): the close view | the far disc magnified, the same window", 6, 4, scale=1)
        two = np.tile(paper, (400, W, 1)).astype(np.float32)
        cv, _la, _dl = close_view(J, T, 6.0, (0.76, -0.19), W=480, H=200)
        two[:, :960] = np.repeat(np.repeat(cv, 2, 0), 2, 1)
        two[:, 960:] = np.repeat(np.repeat(far_view(name, 6.0, (0.76, -0.19), W=480, H=200), 2, 0), 2, 1)
        rows += [hd, two]
    zs = VIEWS[name][:3]
    ins = np.tile(paper, (20 + 300, W, 1)).astype(np.float32)                # the outline judged on paper (space is dark)
    review._label(ins, "the limb's ink on PAPER at 2x (a 320 x 150 px window on the limb), at: " + " | ".join(f"{z[1]:g} px per far texel" for z in zs), 6, 4, scale=1)
    for i, (_label, m, centre) in enumerate(zs):
        cv, _la, _dl = close_view(J, T, m, (math.sqrt(max(1 - centre[1] ** 2, 0.0)), centre[1]), W=320, H=150, space=paper)
        ins[20:320, i * 640:i * 640 + 640] = np.repeat(np.repeat(cv, 2, 0), 2, 1)
    rows.append(ins)
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "close-view preview (numpy; not exported)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


def motion(out, name="jupiter", frames=(0, 3), m=6.0, centre=(0.72, -0.36)):
    """B-241: the motion check B-240 left out - the close view at two frames of the idle loop, each over the far disc's OWN
    frame magnified the same: the belts' edges, the storm and the ink dashes must have moved the same way in both."""
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    J = D.close_draft(name)
    J = json.loads(json.dumps(J))                                            # (as read from a file: lists, rounded hexes)
    pig, far_size = pigment(name)
    f32 = {k: v.astype(np.float32) / 255.0 for k, v in (("limb_band", limb_band()), ("belt_edge", belt_edge(0 if name in ("jupiter", "saturn") else 1)),
                                                        ("spot_rim", spot_rim()), ("ring_edge", ring_edge()), ("grain", close_grain()), ("pigment", pig))}
    T = dict(f32, grain=f32["grain"] * 2.0, pigment=f32["pigment"] * 2.0, far_size=far_size)
    paper = np.array(review.PAPER, np.float32)
    W = 1920
    rows = [np.tile(paper, (30, W, 1)).astype(np.float32)]
    review._label(rows[0], f"B-241 {name} in motion: the close view at frames {frames[0]} and {frames[1]} of its {J['loop_frames']}-frame loop, each over the far disc's own frame, at {m:g} px per far texel", 6, 8)
    lines = []
    prev = None
    for f in frames:
        cv, _la, _dl = close_view(J, T, m, centre, frame=f)
        fv = far_view(name, m, centre, frame=f)
        for what, im in ((f"CLOSE VIEW, frame {f}", cv), (f"TODAY: the far disc's frame {f} magnified {m:g}x", fv)):
            hd = np.tile(paper, (20, W, 1)).astype(np.float32)
            review._label(hd, what, 6, 4, scale=1)
            rows += [hd, im]
        if prev is not None:                                                 # how far the picture moved between the frames
            for what, a, b in (("close view", prev[0], cv), ("far disc", prev[1], fv)):
                lines.append(f"{what}: {100.0 * float((np.abs(a - b).max(axis=-1) > 0.12).mean()):.1f} % of the window's pixels changed "
                             f"tone between frames {frames[0]} and {f}")
        prev = (cv, fv)
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-241 motion check (numpy; not exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


# ---------------------------------------------------------------- the export (B-243; contract 11.5.1, D-195)
NAMES = ("jupiter", "saturn", "uranus", "neptune")
SIZES = {"limb_band": (512, 16), "belt_edge_0": (1024, 24), "belt_edge_1": (1024, 24), "spot_rim": (512, 24),
         "ring_edge": (512, 16), "close_grain": (256, 256), "close_pigment": (128, 128)}
EXPORT_NOTE = ("B-243 (contract 11.5.1, D-195): the far disc's own facts for the giants' close view, from the table the far "
               "disc is painted from (giants_v3). u right, v up, in disc radii; tones are the far disc's flat tones (the "
               "Earth palette, as every disc)")


def keys():
    return (["planets/common/" + n for n in ("limb_band", "belt_edge_0", "belt_edge_1", "spot_rim", "close_grain")]
            + ["planets/saturn/ring_edge"] + [f"planets/{n}/close_pigment" for n in NAMES] + [f"planets/{n}/close" for n in NAMES])


def kit():
    """Every close-view texture, drawn by the same functions the accepted sheets used: [(key, RGBA uint8, json fields)]."""
    mask = "RGB = the lower tone's share across the cut (0 above it, 1 below), A = the thin ink line"
    out = [
        ("planets/common/limb_band", limb_band(), {"role": "the outline's ink alone", "tile_x": True, "centre_row": int(LIMB_C)}),
        ("planets/common/belt_edge_0", belt_edge(0), {"role": "a belt's edge, firm (Jupiter, Saturn): " + mask, "tile_x": True,
                                                      "cut_row": EDGE_ROW, "variant": 0}),
        ("planets/common/belt_edge_1", belt_edge(1), {"role": "a belt's edge, faint and streaky (Uranus, Neptune): " + mask,
                                                      "tile_x": True, "cut_row": EDGE_ROW, "variant": 1}),
        ("planets/common/spot_rim", spot_rim(), {"role": "a storm's rim: RGB = the storm tone's share, no ink", "tile_x": True,
                                                 "cut_row": EDGE_ROW}),
        ("planets/saturn/ring_edge", ring_edge(), {"role": "a ring's edge: " + mask, "tile_x": True, "cut_row": RING_ROW}),
        ("planets/common/close_grain", close_grain(), {"role": "the paper's fine grain, a multiply tile in screen space",
                                                       "tile_x": True, "tile_y": True, "multiply_unit": 127.5}),
    ]
    for name in NAMES:
        pig, size = pigment(name)
        out.append((f"planets/{name}/close_pigment", pig, {"role": "the far disc's slow tone variation, a multiply tile over the "
                                                           "far sheet's frame", "multiply_unit": 127.5, "far_frame_px": size}))
    return out


def close_export_json(name):
    """planets/<giant>/close.json as exported: the draft (giants_v3.close_json through build_discs_v3) without its draft
    flag, as a file holds it."""
    J = D.close_draft(name)
    J.pop("draft", None)
    J["note"] = EXPORT_NOTE
    return json.loads(json.dumps(J))


def export_checks(K, jsons):
    """What must hold before a file is written: one line per problem."""
    out = []
    for key, img, meta in K:
        short = key.split("/")[-1]
        if (img.shape[1], img.shape[0]) != SIZES[short]:
            out.append(f"{key}: {img.shape[1]}x{img.shape[0]}, not {SIZES[short][0]}x{SIZES[short][1]}")
        if meta.get("tile_x") and seam(img) > 1.6:
            out.append(f"{key}: seam {seam(img):.2f} in x")
        if meta.get("tile_y") and seam(np.swapaxes(img, 0, 1)) > 1.6:
            out.append(f"{key}: seam {seam(np.swapaxes(img, 0, 1)):.2f} in y")
    hit = v3.palette_hits(K[0][1], "earth")[0]
    if hit < 0.995:
        out.append(f"limb_band: palette {hit * 100:.1f}% (its solid pixels: the ink)")
    want = ("radius_u", "loop_frames", "fps", "belts", "edge_wobble", "rim", "night", "storms", "ink_marks", "swap", "strips")
    for name, J in jsons.items():
        missing = [k for k in want if k not in J]
        if missing:
            out.append(f"{name}/close.json: no {', '.join(missing)}")
        if "draft" in J:
            out.append(f"{name}/close.json: still flagged draft")
        if (name == "saturn") != ("rings" in J) or (name == "saturn") != ("ring_edge" in J.get("strips", {})):
            out.append(f"{name}/close.json: rings / ring_edge on the wrong body")
        if set(J.get("strips", {})) & {"limb_band", "belt_edge", "spot_rim", "pigment", "grain"} != {"limb_band", "belt_edge", "spot_rim", "pigment", "grain"}:
            out.append(f"{name}/close.json: strips lacks a texture")
        for part in ("limb_band", "belt_edge", "spot_rim", "ring_edge", "pigment", "grain"):
            k = J.get("strips", {}).get(part, {}).get("key")
            if k is not None and k not in keys():
                out.append(f"{name}/close.json: strips.{part} names {k}, which is not exported")
    return out


def export(art):
    """The accepted close view's files (LEAD's ACCEPTED on B-243's fixed-scale sheet first): ten textures with their json
    and the four close.json. No far-disc file is touched: every name here is new (limb_band, belt_edge_0 / _1, spot_rim,
    close_grain, ring_edge, close_pigment, close). The checks raise before anything is written."""
    K = kit()
    jsons = {n: close_export_json(n) for n in NAMES}
    problems = export_checks(K, jsons)
    if problems:
        raise ValueError("B-243 checks: " + "; ".join(problems))
    out = []
    for key, img, meta in K:
        base = os.path.join(art, *key.split("/"))
        os.makedirs(os.path.dirname(base), exist_ok=True)
        n = pngio.write_png(base + "_color.png", img)
        with open(base + ".json", "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"key": key, "style": "v3", "width": img.shape[1], "height": img.shape[0], **meta}, fh, indent=2)
            fh.write("\n")
        out.append((key, img.shape[1], img.shape[0], n))
    for name in NAMES:
        path = os.path.join(art, "planets", name, "close.json")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(jsons[name], fh, indent=2)
            fh.write("\n")
        out.append((f"planets/{name}/close", 0, 0, os.path.getsize(path)))
    return out


def export_review(out, art=ART, footnote=None):
    """The exported files read back from Art on one stamped sheet: the strips at 2x (a mask's ink line in red), the grain at
    1x, the four pigment tiles at 2x, and each file's size, seam and bytes."""
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    paper = np.array(review.PAPER, np.float32)
    W = 1920
    top = np.tile(paper, (570, W, 1)).astype(np.float32)
    review._label(top, "B-243: the giants' close-view textures AS EXPORTED, read back from Assets/_Game/Art (strips at 2x, their first 640 columns: white = the lower tone's share, red = the ink line; the grain at 1x; the four pigment tiles at 2x)", 6, 8, scale=1)
    lines = []

    def put(f, x, y, k=2):
        f = np.repeat(np.repeat(f, k, 0), k, 1)
        top[y:y + f.shape[0], x:x + f.shape[1]] = f

    y, px = 30, 10
    for key in keys():
        base = os.path.join(art, *key.split("/"))
        if key.endswith("/close"):
            J = json.load(open(base + ".json", encoding="utf-8"))
            lines.append(f"{key}.json: {os.path.getsize(base + '.json')} bytes, {len(J['belts'])} belts, {len(J['storms'])} storms, "
                         f"{J['strips']['texels_per_far_texel']:g} strip texels per far texel, belt edge {J['strips']['belt_edge']['key']}"
                         + (", rings" if "rings" in J else ""))
            continue
        im = pngio.read_png_np(base + "_color.png")
        meta = json.load(open(base + ".json", encoding="utf-8"))
        f = im.astype(np.float32) / 255.0
        ln = f"{key}: {im.shape[1]}x{im.shape[0]}, {os.path.getsize(base + '_color.png')} bytes"
        if meta.get("tile_x"):
            ln += f", seam {seam(im):.2f}"
        if meta.get("tile_y"):
            ln += f" (in y {seam(np.swapaxes(im, 0, 1)):.2f})"
        short = key.split("/")[-1]
        if short == "limb_band":
            ln += f", palette {v3.palette_hits(im, 'earth')[0] * 100:.1f}% (its solid pixels: the ink)"
            put((f[..., :3] * f[..., 3:4] + paper * (1 - f[..., 3:4]))[:, :640], 10, y)
            y += 2 * im.shape[0] + 6
        elif short == "close_grain":
            put(f[..., :3], 1320, 30, k=1)
        elif short == "close_pigment":
            put(f[..., :3], px, 300)
            px += 2 * im.shape[1] + 10
        else:
            put((f[..., :3] * (1 - f[..., 3:4]) + np.array([0.85, 0.15, 0.1], np.float32) * f[..., 3:4])[:, :640], 10, y)
            y += 2 * im.shape[0] + 6
        lines.append(ln)
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack([top, foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-243 export read-back (numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_giant_close_v3.py <review png> [giant] [--motion]
    if "--motion" in sys.argv:
        motion(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "jupiter")
    else:
        preview(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "jupiter")
