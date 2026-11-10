"""B-240 (2) (LEAD 11-09 22:3x; the design: coordination/reports/blender/b237_limb_band_design.md): the giants' close view,
PREVIEWS ONLY. Nothing here exports; every file goes to blender/preview/b240/.

Above DiscSprite's near zoom a giant is not a magnified picture: it is drawn from planets/<giant>/close.json (the far
disc's own belts, wobble, rim, night crescent and storms: giants_v3) as flat tones, with narrow painted STRIPS laid along
the limb and along every edge at about one strip texel per screen pixel, whatever the zoom.

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

  python -I build_giant_close_v3.py <review png> [giant]     the sheet: the strips, then the close view at 6 / 7.7 / 12 screen
                                                             px per far texel, each over the far disc magnified the same
                                                             (as it draws today), and the night crescent's edge at 6
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
INK_ROW, EDGE_ROW = 16, 12        # the limb band's ink row; the edge strips' cut row
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
    """512x64, tiles in x: the outline's ink (2.5 px, +-20 % along its length, as the far disc's) on row INK_ROW, and below
    it (inside the planet) one flat faint shade with a ragged foot (brown at alpha 0.10: NEW against the far disc, which
    has none; LEAD to keep or drop). Transparent above."""
    W, H, S = 512, 64, 4
    n = W * S
    y = (np.arange(H * S) + 0.5)[:, None]
    c = ((INK_ROW + 0.5) + 0.45 * pnoise(n, 9, 11)) * S
    r = 1.25 * (1 + 0.2 * pnoise(n, 44, 12)) * S
    ink = (np.abs(y - c[None, :]) <= r[None, :]).astype(np.float32)
    foot = (31 + 3.5 * pnoise(n, 13, 13) + 1.2 * pnoise(n, 37, 14)) * S
    wash = ((y > c[None, :]) & (y < foot[None, :])).astype(np.float32) * 0.10 * (1 - ink)
    acc = np.zeros((H * S, n, 4), np.float32)
    acc[..., :3] = D.PAL["ink"] * ink[..., None] + D.PAL["brown"] * wash[..., None]
    acc[..., 3] = ink + wash
    return _down(acc, W, H, S)


def _edge(W, cells, amp, seed, ink=False, streaks=0):
    """An edge strip W x 24: RGB = the lower tone's share (0 above the ragged cut on row EDGE_ROW, 1 below), A = ink."""
    H, S = 24, 4
    n = W * S
    y = (np.arange(H * S) + 0.5)[:, None]
    b = (EDGE_ROW + amp * pnoise(n, cells, seed) + 0.8 * pnoise(n, cells * 3 - 7, seed + 1)) * S
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
        cl = (EDGE_ROW + 0.3 * pnoise(n, W // 60, seed + 4)) * S   # of it, laid where the far disc has its dash or hatch (the
        inkm = (np.abs(y - cl[None, :]) <= r[None, :]).astype(np.float32)   # first run's one dash per repeat sat on the
    #                                                              strip's own rhythm and crossed the Spot)
    sh = share.reshape(H, S, W, S).mean(axis=(1, 3))
    ia = inkm.reshape(H, S, W, S).mean(axis=(1, 3))
    return np.clip(np.rint(np.dstack([sh, sh, sh, ia]) * 255), 0, 255).astype(np.uint8)


def belt_edge(variant):
    return _edge(1024, 26, 2.2, 21, ink=True) if variant == 0 else _edge(1024, 22, 1.4, 31, ink=True, streaks=70)


def spot_rim():
    return _edge(512, 14, 1.8, 41)


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


def strip_scale(m):
    """A strip texel's size on screen at m px per far texel: the zoom in steps of root 2 from the swap, so the strip is
    re-laid only at a step and its ink stays 2.1-3.0 px (the design note, section 5)."""
    return (m / SWAP) / 2 ** (round(2 * math.log2(m / SWAP)) / 2)


def ribbon(ink_a, P, E, sc):
    """An ink mark: the edge strip's ink line (its A channel) laid along the polyline P (screen px, rows of (x, y)), flat
    ends, the strip's u running along the mark. Writes max alpha into ink_a."""
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
        sub[mk] = np.maximum(sub[mk], samp(E, S_[mk] / sc, EDGE_ROW - Dn[mk] / sc)[..., 3])


# ---------------------------------------------------------------- the close view, from the json
def close_view(J, T, m, centre, W=1920, H=540, frame=0, space=None):
    """J: a loaded close.json; T: the strips as float arrays; m: screen px per far texel; centre: the view's centre (u, v) in
    disc radii; space: the tone behind the planet. -> (RGB float (H, W, 3), the limb's ink alpha, the limb's distance
    field in px)."""
    space = SPACE if space is None else space
    Rs = J["radius_u"] * D.SPACE_PPU * m
    sc = strip_scale(m)
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
        for b in st["blobs"]:
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
        if near.any():
            sh = samp(T["spot_rim"], th[near] / sc, EDGE_ROW - dist[near] / sc)[..., :1]
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
            ribbon(ink_a, to_px(us, vb + ds["wave_amp"] * np.sin(ds["wave_freq"] * us + phase)), E, sc)
    for (u0, v0) in hz["groups"]:
        for j in range(hz["count"]):
            uc, vc, hl = u0 + hz["step"] * j, v0 + hz["step"] * j, hz["length"] / 2
            if uc * uc + vc * vc > hz["limit"]:
                continue
            ribbon(ink_a, to_px([uc - hl, uc + hl], [vc - hl, vc + hl]), E, sc)
    col = D.PAL["ink"] * ink_a[..., None] + col * (1 - ink_a[..., None])
    out = np.where((r <= rim)[..., None], col, space)
    dl = (r - rim) * Rs                                                      # the limb band: px, + outside
    L = T["limb_band"]
    reps = max(1, round(2 * math.pi * Rs / (L.shape[1] * sc)))               # a whole number of repeats round the limb
    nearl = (dl > -(L.shape[0] - INK_ROW) * sc) & (dl < INK_ROW * sc)
    la = np.zeros(vv.shape, np.float32)
    t = samp(L, (ang[nearl] / (2 * math.pi)) * reps * L.shape[1], (INK_ROW + 0.5) - dl[nearl] / sc)
    out[nearl] = t[..., :3] * t[..., 3:4] + out[nearl] * (1 - t[..., 3:4])
    la[nearl] = t[..., 3]
    return out.astype(np.float32), la, dl


def far_view(name, m, centre, W=1920, H=540):
    """The exported far disc's frame 0 magnified m times (bilinear, premultiplied), as the game draws a giant today."""
    meta = json.load(open(os.path.join(ART, "planets", name, "disc.json"), encoding="utf-8"))
    fw = meta["frame_width"]
    fr = pngio.read_png_np(os.path.join(ART, "planets", name, "disc_color.png"))[:fw, :fw].astype(np.float32) / 255.0
    fr[..., :3] *= fr[..., 3:4]
    Rf = meta["radius_px"]
    Rs = Rf * m
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5
    u = centre[0] + (xx - W / 2) / Rs
    v = centre[1] - (yy - H / 2) / Rs
    t = samp(fr, u * Rf + fw / 2, fw / 2 - v * Rf, wrap_x=False)
    inside = (np.abs(u * Rf) < fw / 2) & (np.abs(v * Rf) < fw / 2)
    t = np.where(inside[..., None], t, 0.0)
    return (t[..., :3] + SPACE * (1 - t[..., 3:4])).astype(np.float32)


def seam(img):
    """A tiling strip's wrap against its own neighbouring columns (<= 1.6 passes, as the backdrops' check)."""
    f = img.astype(np.float32)
    return float(np.abs(f[:, -1] - f[:, 0]).mean() / max(float(np.abs(np.diff(f, axis=1)).mean()), 0.5))


# ---------------------------------------------------------------- the sheet
VIEWS = {   # name -> [(label, m, centre)]: the swap, smoke_7's distance (0.6.1: 7.7), the closest (12 until UNITY's number)
    "jupiter": [("the swap: 6 px per far texel", 6.0, (0.72, -0.36)), ("smoke_7's distance: 7.7", 7.7, (0.76, -0.34)),
                ("the closest: 12 (until UNITY names the flight's limit)", 12.0, (0.80, -0.30)),
                ("the night crescent's edge, at 6", 6.0, (-0.45, -0.45))],
}


def preview(out, name="jupiter", footnote=None):
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    dd = os.path.join(os.path.dirname(out), "b240")
    os.makedirs(dd, exist_ok=True)
    jp = os.path.join(dd, f"{name}_close.json")
    with open(jp, "w", encoding="utf-8", newline="\n") as fh:                # the draft, then read back: the view is drawn
        json.dump(D.close_draft(name), fh, indent=2)                         # from the FILE, as UNITY would
        fh.write("\n")
    J = json.load(open(jp, encoding="utf-8"))
    variant = 0 if name in ("jupiter", "saturn") else 1
    pig, far_size = pigment(name)
    S = {"limb_band": limb_band(), "belt_edge_0": belt_edge(0), "belt_edge_1": belt_edge(1), "spot_rim": spot_rim(),
         "close_grain": close_grain(), f"{name}_pigment": pig}
    lines = []
    for k, im in S.items():
        n = pngio.write_png(os.path.join(dd, k + "_color.png"), im)
        tile = k not in (f"{name}_pigment",)
        lines.append(f"{k}: {im.shape[1]}x{im.shape[0]}, {n} bytes" + (f", seam {seam(im):.2f}" if tile else ""))
    lines[0] += f", palette {v3.palette_hits(S['limb_band'], 'earth')[0] * 100:.1f}% (its solid pixels: the ink)"
    f32 = {k: v.astype(np.float32) / 255.0 for k, v in S.items()}
    T = {"limb_band": f32["limb_band"], "belt_edge": f32[f"belt_edge_{variant}"], "spot_rim": f32["spot_rim"],
         "grain": f32["close_grain"] * 2.0, "pigment": f32[f"{name}_pigment"] * 2.0, "far_size": far_size}
    paper = np.array(review.PAPER, np.float32)
    W = 1920
    rows = [np.tile(paper, (30, W, 1)).astype(np.float32)]
    review._label(rows[0], f"B-240 {name}: the close view drawn from {name}_close.json + the strips (PREVIEW, nothing exported); each zoom over the far disc magnified the same", 6, 8)
    st = np.tile(paper, (64 * 2 + 24 * 2 * 3 + 256 + 70, W, 1)).astype(np.float32)   # the strips
    review._label(st, "the strips: limb_band 512x64 at 2x (ink on row 16, a faint inner shade below: new against the far disc) | belt_edge 0 and 1 and spot_rim at 2x (white = the lower tone's share, red = the ink line that marks are cut from) | close_grain and the pigment tile at 1x / 2x", 6, 4, scale=1)

    def put(im, x, y, k=2):
        f = np.repeat(np.repeat(im, k, 0), k, 1)
        st[y:y + f.shape[0], x:x + f.shape[1]] = f

    lb = f32["limb_band"]
    chk = (((np.arange(64)[:, None] // 8 + np.arange(512)[None, :] // 8) % 2) * 0.06 + 0.62)[..., None] * np.ones(3, np.float32)
    put(lb[..., :3] * lb[..., 3:4] + chk * (1 - lb[..., 3:4]), 10, 22)
    y = 22 + 128 + 6
    for k in ("belt_edge_0", "belt_edge_1"):
        e = f32[k]
        vis = e[..., :3] * (1 - e[..., 3:4]) + np.array([0.85, 0.15, 0.1], np.float32) * e[..., 3:4]
        put(vis[:, :520], 10, y)                                             # (its first 520 px: the dash sits at 400-510)
        y += 48 + 4
    put(np.repeat(f32["spot_rim"][..., :3], 1, 0), 10, y)
    put(f32["close_grain"][..., :3], 1100, 22, k=1)
    put(f32[f"{name}_pigment"][..., :3], 1380, 22, k=2)
    rows.append(st)
    for label, m, centre in VIEWS[name]:
        cv, la, dl = close_view(J, T, m, centre)
        fv = far_view(name, m, centre)
        ink = la > 0.5
        arc = int((np.abs(dl) < 0.5).sum())
        wpx = float(ink.sum()) / arc if arc else 0.0
        sc = strip_scale(m)
        msg = (f"{label}: strip texel {sc:.2f} px; limb ink measured {wpx:.2f} px over {arc} px of arc (the strip's own range "
               f"{2.5 * 0.8 * sc:.2f}-{2.5 * 1.2 * sc:.2f}); the planet's radius on screen {J['radius_u'] * D.SPACE_PPU * m:.0f} px")
        lines.append(msg)
        hd = np.tile(paper, (20, W, 1)).astype(np.float32)
        review._label(hd, "CLOSE VIEW, " + msg, 6, 4, scale=1)
        rows += [hd, cv]
        hd = np.tile(paper, (20, W, 1)).astype(np.float32)
        review._label(hd, f"TODAY: the far disc ({name}/disc frame 0) magnified {m:g}x, the same view", 6, 4, scale=1)
        rows += [hd, fv]
        tag = f"{m:g}".replace(".", "_") + ("_night" if "night" in label else "")
        pngio.write_png(os.path.join(dd, f"{name}_close_m{tag}.png"),
                        np.dstack([np.clip(np.rint(cv * 255), 0, 255).astype(np.uint8), np.full(cv.shape[:2], 255, np.uint8)]))
    ins = np.tile(paper, (20 + 300, W, 1)).astype(np.float32)                # the outline judged on paper (space is dark)
    review._label(ins, "the limb's ink on PAPER at 2x (a 320 x 150 px window on the limb at each zoom): the swap, 6 | smoke_7's distance, 7.7 | the closest, 12", 6, 4, scale=1)
    for i, (_label, m, centre) in enumerate(VIEWS[name][:3]):
        cv, _la, _dl = close_view(J, T, m, (math.sqrt(max(1 - centre[1] ** 2, 0.0)), centre[1]), W=320, H=150, space=paper)
        ins[20:320, i * 640:i * 640 + 640] = np.repeat(np.repeat(cv, 2, 0), 2, 1)
    rows.append(ins)
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-240 close-view preview (numpy; not exported)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_giant_close_v3.py <review png> [giant]
    preview(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "jupiter")
