"""B-214 (D1): the dig run's reward moments - ink and paper, no glow, readable over the paper panels. Earth palette.

  fx/ui/scrip_shower     8 frames 192x192, pivot [0.5, 0.15] (the sell point): brass Scrip coins pop up, spinning, and arc off
                         toward the frame's top-left (the Scrip tag's corner); UNITY can slide the sprite toward the tag
  fx/ui/node_bought      8 frames 128x128, pivot centre (the node): an ink ring stamps down onto the 64 px node frame with a
                         splat, gold flecks burst off it and shrink away; the ring thins as the clip ends
  fx/ui/rank_up          10 frames 256x192, pivot [0.5, 0.542] (the insignia's centre): burst lines, two red paper ribbons
                         unfurl from behind the insignia, paper confetti tumbles; the insignia itself is UNITY's sprite
                         (ui/rank/insignia_<n>), drawn on top along json insignia_track (dy px, scale per frame)
  fx/ui/expedition_seal  10 frames 160x192, pivot [0.5, 0.354] (the seal's centre): a molten wax pool under the brass seal
                         stamp coming down, the press (the wax squashes, a splash of red wax flies), the stamp lifting off the
                         impressed seal; the last frames match the certificate's baked seal (ui/rank/certificate, its centre
                         58 px in from the right and bottom edges) so the hand-off is seamless

  python -I build_fx_ui_v3.py <review png>     the lock-free sheet (each over the HUD / the tree panel / the certificate)
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_ui_v3 as U  # noqa: E402
import build_skilltree_v3 as ST  # noqa: E402
import build_fx_rare_v3 as FR  # noqa: E402
from meridian import v3  # noqa: E402

G, O, I = U.G, U.O, U.I
TAU = 2 * math.pi
circ, extra, done = ST.circ, ST.extra, ST.done
ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Assets", "_Game", "Art")


def star(cx, cy, r, ri=None, n=5, a0=-TAU / 4, sy=1.0):
    ri = ri or r * 0.42
    return [(cx + (r if k % 2 == 0 else ri) * math.cos(a0 + TAU * k / (2 * n)), cy + sy * (r if k % 2 == 0 else ri) * math.sin(a0 + TAU * k / (2 * n)))
            for k in range(2 * n)]


# ---------------------------------------------------------------- scrip_shower
SW, SH_, S_PIV = 192, 192, (96, 163)
S_TARGET = (16, 16)
N_COINS = 9


def coin(d, M, x, y, r, tilt):
    """A brass coin turning: tilt 1 = face on (a stamped star), toward 0 = edge on (the milled side shows)."""
    ry = r * max(abs(tilt), 0.2)
    if ry < r * 0.95:
        G.stroke(d, circ(x, y + 1.6, r, 24, ry), M["mustard_sh"], I, cyclic=True)                        # the side, under the face
    G.stroke(d, circ(x, y, r, 24, ry), M["mustard"], I, cyclic=True)
    if abs(tilt) > 0.55:
        G.stroke(d, star(x, y, r * 0.5, sy=ry / r), M["mustard_sh"], 0.0, cyclic=True)


def shower_frame(k, seed=900):
    c = U.Canvas(SW, SH_)
    d, M = c.dm, extra(c)
    rng = np.random.default_rng(seed)
    x0, y0 = S_PIV
    if k <= 1:                                                                                   # the pop at the sell point
        for j in range(7):
            a = -math.pi + math.pi * (j + 0.5) / 7
            r0, r1 = 8 + 5 * k, 15 + 7 * k
            G.stroke(d, [(x0 + r0 * math.cos(a), y0 + r0 * math.sin(a)), (x0 + r1 * math.cos(a), y0 + r1 * math.sin(a))], M["ink"], I * 1.2)
    coins = []
    for i in range(N_COINS):
        a = math.radians(rng.uniform(-128, -62))
        s = rng.uniform(15, 21)
        start = i % 3
        ph = rng.uniform(0, TAU)
        t = k - start
        if t < 0:
            continue
        bx, by = x0 + s * t * math.cos(a), y0 + s * t * math.sin(a) + 1.9 * t * t
        w = min(1.0, (t / 7.0) ** 1.6)
        x, y = bx + (S_TARGET[0] + 6 * (i % 3) - bx) * w, by + (S_TARGET[1] + 5 * (i % 2) - by) * w
        r = 5.0 + 3.0 * min(1.0, t / 2.0)
        x, y = min(max(x, r + 4), SW - r - 4), min(max(y, r + 4), SH_ - r - 4)
        coins.append((y, x, r, math.cos(ph + 1.25 * t), t))
    for y, x, r, tilt, t in sorted(coins, key=lambda q: -q[0]):
        if 1 <= t <= 5:                                                                          # motion ticks behind it
            G.stroke(d, [(x + 1.2 * r, y + 1.4 * r), (x + 1.9 * r, y + 2.2 * r)], M["ink"], I)
        coin(d, M, x, y, r, tilt)
    return done(c, seed + k)[0]


# ---------------------------------------------------------------- node_bought
NW = 128
NODE_R = 35                                                # just outside the node frame's own rim (31 sat on it)


def node_frame_fx(k, seed=920):
    c = U.Canvas(NW, NW)
    d, M = c.dm, extra(c)
    cx = cy = NW / 2
    R = [50, 41, NODE_R + 1, NODE_R, NODE_R, NODE_R, NODE_R, NODE_R][k]
    wid = [0.9, 1.3, 2.4, 2.0, 1.7, 1.4, 1.1, 0.8][k]
    ring = [(cx + R * (1 + 0.02 * math.sin(7 * a + k)) * math.cos(a), cy + R * (1 + 0.02 * math.sin(7 * a + k)) * math.sin(a)) for a in np.linspace(0, TAU, 72, endpoint=False)]
    G.stroke(d, ring, M["ink"], I * wid, cyclic=True)                                            # the ink ring, stamping down
    if k == 2:                                                                                   # the splat where it lands
        for j in range(9):
            a = TAU * j / 9 + 0.3
            G.stroke(d, circ(cx + (R + 3.5) * math.cos(a), cy + (R + 3.5) * math.sin(a), 1.8 + (j % 3) * 0.6, 10), M["ink_f"], 0.0, cyclic=True)
    if 3 <= k <= 6:                                                                              # gold flecks burst off it
        t = (k - 3) / 3.0
        for j in range(8):
            a = TAU * j / 8 + 0.2 + 0.15 * (j % 2)
            rr = NODE_R + 5 + 17 * math.sqrt(t)
            sz = 6.5 * (1 - 0.75 * t)
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            if j % 2 == 0:
                G.stroke(d, FR.star4(x, y, sz, rot=0.3 * j), M["mustard"], I * 0.8, cyclic=True)
                G.stroke(d, FR.star4(x, y, sz * 0.45, rot=0.3 * j), M["offwhite_f"], 0.0, cyclic=True)
            else:
                G.stroke(d, FR.diamond(x, y, sz * 0.7), M["mustard"], I * 0.7, cyclic=True)
    return done(c, seed + k)[0]


# ---------------------------------------------------------------- rank_up
RW, RH, R_C = 256, 192, (128, 104)
INSIGNIA_TRACK = [(40, 0.70), (22, 0.86), (8, 1.0), (-4, 1.12), (-2, 1.05), (0, 1.0), (0, 1.0), (0, 1.0), (0, 1.0), (0, 1.0)]


def ribbon_side(d, M, s, L, seed):
    """One ribbon unfurling to length L from behind the insignia (s = -1 left, +1 right), its roll at the tip while it opens."""
    cx, cy = R_C
    x0 = cx + s * 18
    hw = 11
    n = 10
    mid = [(x0 + s * L * i / n, cy + 18 + 4 * math.sin(2.4 * i / n * math.pi + 0.5) * (i / n)) for i in range(n + 1)]
    top = [(x, y - hw) for x, y in mid]
    bot = [(x, y + hw) for x, y in mid]
    xe, ye = mid[-1]
    full = L >= 80
    if full:                                                                                     # the forked tail
        tail = [(xe + s * 14, ye - hw), (xe + s * 6, ye), (xe + s * 14, ye + hw)]
        G.stroke(d, top + tail + bot[::-1], M["red"], I, cyclic=True)
    else:
        G.stroke(d, top + bot[::-1], M["red"], I, cyclic=True)
    G.stroke(d, [(x, y - hw + 3.5) for x, y in mid[1:]], M["ln_mustard"], I * 0.9)                # its gold edge stripes
    G.stroke(d, [(x, y + hw - 3.5) for x, y in mid[1:]], M["ln_mustard"], I * 0.9)
    G.stroke(d, [(x0, cy + 18 - hw), (x0 + s * 8, cy + 18 - hw), (x0, cy + 18 + hw + 6)], M["red_sh"], I * 0.8, cyclic=True)   # the fold
    if not full and L > 2:                                                                       # the roll, still opening
        G.stroke(d, circ(xe, ye, 6.5, 16, hw + 1.5), M["red"], I, cyclic=True)
        G.stroke(d, circ(xe, ye, 2.5, 10, hw * 0.55), M["red_sh"], 0.0, cyclic=True)


def rank_frame(k, seed=940):
    c = U.Canvas(RW, RH)
    d, M = c.dm, extra(c)
    cx, cy = R_C
    rng = np.random.default_rng(seed)
    if 1 <= k <= 4:                                                                              # ink burst lines round it
        for j in range(12):
            a = TAU * j / 12 + 0.13
            r0, r1 = 46 + 6 * k, 58 + 9 * k
            if r1 + cy > RH - 6 or cy - r1 < 6:
                r1 = min(r1, min(cy - 6, RH - 6 - cy))
            if r1 > r0 + 3:
                G.stroke(d, G.hose_outline([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))], 2.0),
                         M["ink_f"], 0.0, cyclic=True)
    L = [0, 0, 10, 32, 56, 74, 84, 84, 84, 84][k]                                               # (96 put the tails on the edge)
    for s in (-1, 1):
        if L > 0:
            ribbon_side(d, M, s, L, seed + s)
    if k >= 3:                                                                                   # paper confetti tumbling down
        for j in range(14):
            px = rng.uniform(20, RW - 20)
            py0 = rng.uniform(8, 60)
            t = k - 3
            x = px + 6 * math.sin(1.3 * t + j)
            y = py0 + 13 * t + 2 * j % 9
            if y > RH - 12:
                continue
            ang = 0.7 * t + j
            w, h = 5.0, 3.0 * abs(math.cos(ang)) + 0.8
            q = [(x + w * math.cos(ang), y + h * math.sin(ang)), (x - h * math.sin(ang), y + w * 0.3 * math.cos(ang)),
                 (x - w * math.cos(ang), y - h * math.sin(ang)), (x + h * math.sin(ang), y - w * 0.3 * math.cos(ang))]
            G.stroke(d, q, M[("offwhite", "mustard", "teal", "red")[j % 4]], I * 0.6, cyclic=True)
    return done(c, seed + k)[0]


# ---------------------------------------------------------------- expedition_seal
EW, EH, E_C = 160, 192, (80, 124)
CERT_SEAL = (58, 58)                                       # the seal's centre in from the certificate's right / bottom edges


def stamp_top(d, M, cx, cy, s):
    """The brass seal stamp seen from above as it comes down (s = its scale: nearer is bigger): the flange, the neck,
    the turned wooden knob."""
    G.stroke(d, circ(cx, cy, 30 * s, 40), M["mustard"], O, cyclic=True)
    G.stroke(d, circ(cx, cy, 24 * s, 36), M["mustard_sh"], I, cyclic=True)
    G.stroke(d, circ(cx, cy, 15 * s, 28), M["mustard"], I, cyclic=True)
    G.stroke(d, circ(cx, cy, 11 * s, 24), M["brown"], I, cyclic=True)
    G.stroke(d, circ(cx - 3 * s, cy - 3 * s, 3.5 * s, 12), M["brown_sh"], 0.0, cyclic=True)


def wax(d, M, cx, cy, rx, ry, seed, impressed=False, lump=0.08):
    G.stroke(d, G.lumpy_ellipse(cx, cy, rx, ry, n=30, lump=lump, seed=seed), M["red"], O, cyclic=True)
    if impressed:
        G.stroke(d, circ(cx, cy, 18 * rx / 27, 36), M["ln_red"], I, cyclic=True)
        G.stroke(d, star(cx, cy, 12 * rx / 27, 5), M["red_sh"], 0.0, cyclic=True)
        G.stroke(d, star(cx, cy, 12 * rx / 27, 5), M["ink"], I * 0.7, cyclic=True)
    else:
        G.stroke(d, [(cx - rx * 0.45, cy - ry * 0.5), (cx - rx * 0.15, cy - ry * 0.62)], M["ln_offwhite"], I * 1.6)   # wet sheen (paint)


def seal_frame(k, seed=960):
    c = U.Canvas(EW, EH)
    d, M = c.dm, extra(c)
    cx, cy = E_C
    if k <= 2:                                                                                   # the molten pool, the stamp coming down
        wax(d, M, cx, cy, 30, 29, seed + 260, lump=0.1)
        s = (1.55, 1.3, 1.08)[k]
        stamp_top(d, M, cx, cy - (40, 18, 4)[k], s)
    elif k == 3:                                                                                 # the press: the wax squashes, splashes
        for j in range(9):
            a = TAU * j / 9 + 0.4
            rr = 40 + 4 * (j % 3)
            x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
            G.stroke(d, circ(x, y, 3.2 + (j % 2), 12), M["red"], I * 0.8, cyclic=True)
        wax(d, M, cx, cy, 37, 33, seed + 1, lump=0.14)
        stamp_top(d, M, cx, cy, 1.0)
    else:
        rx, ry = {4: (32, 30), 5: (29, 27.5), 6: (27.5, 26.5)}.get(k, (27, 26))
        if k <= 6:                                                                               # the splash flying out, shrinking
            t = (k - 3) / 3.0
            for j in range(9):
                a = TAU * j / 9 + 0.4
                rr = 44 + 4 * (j % 3) + 16 * t
                x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
                rad = (3.2 + (j % 2)) * (1 - 0.7 * t)
                if rad > 1.0:
                    G.stroke(d, circ(x, y, rad, 10), M["red"], I * 0.6, cyclic=True)
        if k <= 6:
            wax(d, M, cx, cy, rx, ry, seed + 2, impressed=True, lump=0.08 + 0.02 * (6 - k))
        else:                                                                                    # the certificate's own seal (B-206)
            G.stroke(d, G.lumpy_ellipse(cx, cy, 27, 26, n=30, lump=0.08, seed=260), M["red"], O, cyclic=True)
            G.stroke(d, circ(cx, cy, 18, 36), M["ln_red"], I, cyclic=True)
            G.stroke(d, star(cx, cy, 12, 5), M["red_sh"], 0.0, cyclic=True)
            G.stroke(d, star(cx, cy, 12, 5), M["ink"], I * 0.7, cyclic=True)
        if k in (4, 5):                                                                          # the stamp lifting away
            stamp_top(d, M, cx, cy - (34, 70)[k - 4], (1.15, 1.35)[k - 4])
    return done(c, seed + k)[0]


# ---------------------------------------------------------------- kit / export
FX = {   # name: (frame fn, n, w, h, pivot (from bottom-left), clip, note)
    "scrip_shower": (shower_frame, 8, SW, SH_, [S_PIV[0] / SW, 1 - S_PIV[1] / SH_], "shower",
                     "B-214: selling - brass Scrip coins pop up and arc off toward the frame's top-left; place the pivot at the sell point, "
                     "the tag up and to the left (UNITY may slide the sprite toward the tag over the clip)"),
    "node_bought": (node_frame_fx, 8, NW, NW, [0.5, 0.5], "stamp",
                    "B-214: buying a node - the ink ring stamps down round the 64 px node frame (ring r 35 px), gold flecks burst; pivot on the node"),
    "rank_up": (rank_frame, 10, RW, RH, [R_C[0] / RW, 1 - R_C[1] / RH], "rank_up",
                "B-214: a new Rank - draw ui/rank/insignia_<n> ON TOP at the pivot, offset / scaled per frame by insignia_track; the ribbons "
                "unfurl behind it, the confetti tumbles"),
    "expedition_seal": (seal_frame, 10, EW, EH, [E_C[0] / EW, 1 - E_C[1] / EH], "press",
                        "B-214: a New Expedition - play over ui/rank/certificate with the pivot on its seal (58 px in from its right and bottom "
                        "edges); frames 7-9 match the baked seal, so the hand-off at the end is seamless"),
}


def kit():
    out = []
    for name, (fn, n, w, h, piv, clip, note) in FX.items():
        frames = [fn(k) for k in range(n)]
        sheet, cols = FR.sheet_of(frames)
        meta = {"key": f"fx/ui/{name}", "style": "v3", "ppu": U.PPU, "gutter": v3.GUTTER, "fps": v3.FPS, "pivot": [round(piv[0], 4), round(piv[1], 4)],
                "frame_width": w, "frame_height": h, "columns": cols, "frames": n,
                "animations": [{"name": clip, "start": 0, "length": n, "loop": False}], "note": note}
        if name == "rank_up":
            meta["insignia_track"] = [{"dy_px": dy, "scale": sc} for dy, sc in INSIGNIA_TRACK]
            meta["insignia_track_note"] = "per frame: the insignia's offset from the pivot (px, + = down) and its scale (1 = its 96 px panel size)"
        if name == "expedition_seal":
            meta["seal_from_bottom_right_px"] = list(CERT_SEAL)
        out.append((meta["key"], frames, sheet, meta))
    return out


def export(art):
    from meridian import pngio
    built, problems = [], []
    for key, frames, sheet, meta in kit():
        m = v3.EDGE_MARGIN
        hit = v3.palette_hits(sheet, "earth")[0]
        if hit < 0.995:
            problems.append(f"{key}: palette {hit * 100:.1f}%")
        if sheet.shape[1] % 4 or sheet.shape[0] % 4:
            problems.append(f"{key}: sheet {sheet.shape[1]}x{sheet.shape[0]} not a multiple of 4")
        for i, f in enumerate(frames):
            if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any():
                problems.append(f"{key} frame {i}: touches the {m} px edge")
        built.append((key, sheet, meta))
    if problems:
        raise ValueError("B-214 fx checks: " + "; ".join(problems))
    out = []
    for key, sheet, meta in built:
        base = os.path.join(art, *key.split("/"))
        os.makedirs(os.path.dirname(base), exist_ok=True)
        n = pngio.write_png(base + "_color.png", sheet)
        with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((key, sheet.shape[1], sheet.shape[0], n))
    return out


def keys():
    return [f"fx/ui/{n}" for n in FX]


# ---------------------------------------------------------------- the review sheet
def _png(key):
    from meridian import pngio
    p = os.path.join(ART, *key.split("/")) + "_color.png"
    return pngio.read_png_np(p) if os.path.isfile(p) else None


def _scale(img, s):
    """Nearest resample of an RGBA uint8 sprite by s (the insignia track in the preview)."""
    h, w = img.shape[:2]
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    ys = np.clip((np.arange(nh) / s).astype(int), 0, h - 1)
    xs = np.clip((np.arange(nw) / s).astype(int), 0, w - 1)
    return img[ys][:, xs]


def backdrops():
    """Float RGB backgrounds per fx: the HUD (sky, turf, the Scrip tag), the tree panel's paper with a bought node, the certificate."""
    pal = {k: np.array(v3.hex_rgb(v), np.float32) / 255.0 for k, v in v3.PALETTES["earth"].items()}
    out = {}
    b = np.empty((SH_, SW, 3), np.float32)
    b[:] = pal["sky"]
    b[150:] = pal["green"]
    b[156:] = pal["brown"]
    tag = _png("ui/hud/scrip_tag")
    if tag is not None:
        ST.ov(b, tag, S_TARGET[0] - 30 + 6, S_TARGET[1] - 28 + 6)
    out["scrip_shower"] = b
    panel = _png("ui/skilltree/panel")
    b = np.empty((NW, NW, 3), np.float32)
    b[:] = pal["offwhite"]
    if panel is not None:
        ph, pw = panel.shape[:2]
        crop = panel[ph // 2 - NW // 2:ph // 2 + NW // 2, pw // 2 - NW // 2:pw // 2 + NW // 2]
        ST.ov(b, crop, 0, 0)
    node = _png("ui/skilltree/node_bought")
    if node is not None:
        ST.ov(b, node, NW // 2 - node.shape[1] // 2, NW // 2 - node.shape[0] // 2)
    out["node_bought"] = b
    b = np.empty((RH, RW, 3), np.float32)
    b[:] = pal["offwhite"]
    if panel is not None:
        ph, pw = panel.shape[:2]
        crop = panel[max(0, ph // 2 - RH // 2):ph // 2 + RH // 2, max(0, pw // 2 - RW // 2):pw // 2 + RW // 2]
        ST.ov(b, crop, 0, 0)
    out["rank_up"] = b
    cert = _png("ui/rank/certificate")
    b = np.empty((EH, EW, 3), np.float32)
    b[:] = pal["offwhite"]
    if cert is not None:
        ch, cw = cert.shape[:2]
        sx, sy = cw - CERT_SEAL[0], ch - CERT_SEAL[1]                                            # the seal's centre on the certificate
        ST.ov(b, cert, E_C[0] - sx, E_C[1] - sy)
    out["expedition_seal"] = b
    return out


def composite(name, frame, k, bg):
    img = bg.copy()
    ST.ov(img, frame, 0, 0)
    if name == "rank_up":
        ins = _png("ui/rank/insignia_3")
        if ins is not None:
            dy, sc = INSIGNIA_TRACK[k]
            s2 = _scale(ins, sc)
            ST.ov(img, s2, R_C[0] - s2.shape[1] // 2, R_C[1] + dy - s2.shape[0] // 2)
    return img


def preview(out, footnote=None):
    import time
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    K = kit()
    BG = backdrops()
    Wd = 1780
    paper = np.array(review.PAPER, np.float32)
    rows = []
    head = np.tile(paper, (28, Wd, 1))
    review._label(head, "B-214 the reward moments: each at 1x over the HUD / the tree panel / the certificate (rank_up with insignia_3 on its track), then frames at 2x", 6, 8)
    rows.append(head)
    for key, frames, _sheet, meta in K:
        name = key.split("/")[-1]
        comps = [composite(name, f, k, BG[name]) for k, f in enumerate(frames)]
        fw, fh = comps[0].shape[1], comps[0].shape[0]
        per = max(1, (Wd - 20) // (fw + 12))
        nrow = -(-len(comps) // per)
        r = np.tile(paper, (22 + nrow * (fh + 12), Wd, 1))
        review._label(r, f"{key} (1x, frames 0-{len(comps) - 1})", 6, 4, scale=1)
        for i, im in enumerate(comps):
            rr, cc = divmod(i, per)
            x, y = 10 + cc * (fw + 12), 20 + rr * (fh + 12)
            r[y:y + fh, x:x + fw] = im
        rows.append(r)
        pick = list(range(0, len(comps), 2)) if len(comps) > 4 else list(range(len(comps)))
        per2 = max(1, (Wd - 20) // (2 * fw + 12))
        nrow2 = -(-len(pick) // per2)
        r2 = np.tile(paper, (22 + nrow2 * (2 * fh + 12), Wd, 1))
        review._label(r2, f"{key} at 2x: frames {', '.join(map(str, pick))}", 6, 4, scale=1)
        for i, k in enumerate(pick):
            rr, cc = divmod(i, per2)
            x, y = 10 + cc * (2 * fw + 12), 20 + rr * (2 * fh + 12)
            r2[y:y + 2 * fh, x:x + 2 * fw] = np.repeat(np.repeat(comps[k], 2, 0), 2, 1)
        rows.append(r2)
    lines = []
    for key, frames, sheet, _m in K:
        hit = v3.palette_hits(sheet, "earth")[0] * 100
        m = v3.EDGE_MARGIN
        bad = [i for i, f in enumerate(frames) if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any()]
        lines.append(f"{key}: {sheet.shape[1]}x{sheet.shape[0]}, palette {hit:.1f}%" + (f"; EDGE {bad}" if bad else ""))
    foot = np.tile(paper, (24 + 16 * ((len(lines) + 1) // 2), Wd, 1))
    for i, ln in enumerate(lines):
        review._label(foot, ln, 6 + (i % 2) * 700, 6 + 16 * (i // 2), scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "design preview (lock-free, fakegp + numpy)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # python -I build_fx_ui_v3.py <review png>
    preview(sys.argv[1])
