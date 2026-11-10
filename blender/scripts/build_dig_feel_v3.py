"""B-246 (D-196) sheet 2: the dig's small art - what marks the target, what shows the work, what the contact throws. All of
it cream + ink (v3), so UNITY tints it: the reticle by its state, the chips by the dug cell's tone_hex (as the clods,
D-190), the beam's contact by the Beam's own tone.

  fx/dig_reticle/base   6 frames x 48x48 @ PPU 64, pivot [0.5, 0.5], three two-drawing boils:
                          arc     a bracket that sits ON a circle (its own curve is the brush's 0.9 m; on a wider circle it is
                                  off by under a pixel): the frame's centre is on the circle's line, the circle's middle is
                                  straight below; UNITY lays four of them round the target
                          corner  a corner bracket for a 1 m cell: the frame's centre is the cell's top-left corner, its arms
                                  run right and down; turned for the other three
                          pip     a short ground tick on the contact point itself (B-249; B-246's was a small cross, which
                                  inside the four brackets read as a gun sight)
                        states are UNITY's, by tint and gap: in reach (as drawn, tight), clamped at the reach's edge
                        (mustard, the brackets pushed out), nothing to dig (red, wider still, no pip)
  fx/dig_chip/round     3 frames x 128x128, pivot centre: cracks from the contact point, three stages, for the brush
  fx/dig_chip/cell      3 frames x 64x64, pivot centre: the same for one 1 m cell (the cracks stay inside it)
                        a stage keeps the stage before it and grows it (the same cracks, longer, then branching and flaking)
  fx/beam_contact/base  6 frames x 64x64, pivot centre, loop: the ray's hit - a breathing glow and grit thrown clear of it;
                        the sprite's up is away from the surface. A mining tool's work, never a muzzle or a blast (D-087)
  fx/shovel_swish/base  3 frames x 104x96, once: a smear arc behind the blade - its pivot is the swing's centre (the grip),
                        it runs from level to 75 deg below, clockwise (the down stroke as drawn; mirrored or turned for the
                        others); full, breaking, wisps

  python -I build_dig_feel_v3.py <review png>   the lock-free sheet 2: the reticle's three states on tan soil and on grey
                                                stone at 1x (round and cell, a chip stage under each), the chip stages,
                                                the contact loop and the swish as strips, the swish on side_dig's contact
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
from meridian import v3  # noqa: E402

G, O, I = U.G, U.O, U.I
TAU = 2 * math.pi
ART = os.path.normpath(os.path.join(HERE, "..", "..", "Assets", "_Game", "Art"))
PPU = 64
RET = 48                                # the reticle's frame
R0 = 0.9 * PPU                          # the brush's radius: the arc bracket's own curve
SWW, SWH, SWC, SWR = 104, 96, (10.0, 10.0), 1.2 * PPU      # the swish: frame, the arc's centre in it (px, y down), its radius
SW_END = 75.0                           # the arc ends this many degrees below level
TIER_CHIP = {1: "#8C5A33", 3: "#7E7F86"}                    # D1Tables.json's chip colours (Topsoil, Stone), for the sheet


def keys():
    return ["fx/dig_reticle/base", "fx/dig_chip/round", "fx/dig_chip/cell", "fx/beam_contact/base", "fx/shovel_swish/base"]


def frame(W, H, fn, seed):
    c = U.Canvas(W, H)
    fn(c.dm, ST.extra(c))
    return ST.done(c, seed)[0]


def wob(pts, seed, amp):
    """The boil: every point nudged by a seeded fraction of a pixel."""
    rng = np.random.default_rng(seed)
    return [(x + float(rng.normal(0, amp)), y + float(rng.normal(0, amp))) for x, y in pts]


# ---------------------------------------------------------------- the reticle
def arc_piece(j):
    def fn(d, M):
        cx, cy = RET / 2, RET / 2 + R0                                   # the circle's middle, below the frame
        th = math.asin(15.0 / R0)
        pts = [(cx + R0 * math.sin(a), cy - R0 * math.cos(a)) for a in np.linspace(-th, th, 9)]

        def inward(p, k=5.0):                                            # a bracket's turned-in end, toward the middle
            L = math.hypot(cx - p[0], cy - p[1])
            return (p[0] + (cx - p[0]) / L * k, p[1] + (cy - p[1]) / L * k)
        path = wob([inward(pts[0])] + pts + [inward(pts[-1])], 900 + j, 0.45)
        G.stroke(d, G.hose_outline(path, 4.5), M["offwhite"], O * 0.8, cyclic=True)
    return frame(RET, RET, fn, 910 + j)


def corner_piece(j):
    def fn(d, M):
        c = RET / 2
        path = wob([(c + 13.0, c), (c, c), (c, c + 13.0)], 920 + j, 0.45)
        G.stroke(d, G.hose_outline(path, 4.5), M["offwhite"], O * 0.8, cyclic=True)
    return frame(RET, RET, fn, 930 + j)


PIP = "tick"    # B-249 (LEAD 11-10 11:0x, from the 0.6.3 smoke read, H3): B-246's pip was a small CROSS, and four arcs round
#                 a cross read as a GUN SIGHT with the Beam in hand (D-087). "tick" = a short hand-drawn ground tick;
#                 "diamond" = a small open diamond (the alternative shown on the preview); "cross" = the old one, kept
#                 only so the preview can show it beside the new. The key, the two frame slots and the json do not change.


def pip_piece(j, kind=None):
    kind = kind or PIP

    def fn(d, M):
        c = RET / 2
        if kind == "cross":                                              # B-246's, superseded
            a = wob([(c - 5.5, c), (c + 5.5, c)], 940 + j, 0.4)
            b = wob([(c, c - 5.5), (c, c + 5.5)], 945 + j, 0.4)
            G.stroke(d, G.hose_outline(a, 3.4), M["offwhite"], O * 0.7, cyclic=True)
            G.stroke(d, G.hose_outline(b, 3.4), M["offwhite"], O * 0.7, cyclic=True)
            G.stroke(d, [(c - 1.6, c - 1.6), (c + 1.6, c - 1.6), (c + 1.6, c + 1.6), (c - 1.6, c + 1.6)], M["offwhite_f"], 0.0, cyclic=True)
        elif kind == "tick":                                             # one short stroke, a little off level: a pencil tick on the ground
            a = wob([(c - 5.5, c + 0.9), (c - 1.8, c + 0.1), (c + 1.8, c - 0.2), (c + 5.5, c - 0.9)], 940 + j, 0.4)
            G.stroke(d, G.hose_outline(a, 3.4), M["offwhite"], O * 0.7, cyclic=True)
        else:                                                            # "diamond": four short strokes round an open middle
            r = 6.0
            p = wob([(c, c - r), (c + r, c), (c, c + r), (c - r, c)], 940 + j, 0.35)
            for i in range(4):
                G.stroke(d, G.hose_outline([p[i], p[(i + 1) % 4]], 2.4), M["offwhite"], O * 0.6, cyclic=True)
    return frame(RET, RET, fn, 950 + j)


# ---------------------------------------------------------------- the chip stages
def crack_set(seed, n, Lmax, R_lim):
    """n cracks from (0, 0): each a jagged run of points (stopped at R_lim) with two side branches off it."""
    rng = np.random.default_rng(seed)
    base = float(rng.uniform(0, TAU))
    out = []
    for i in range(n):
        a = base + TAU * i / n + float(rng.uniform(-0.3, 0.3))
        L = Lmax * float(rng.uniform(0.72, 1.0))
        pts, x, y, ang, run = [(0.0, 0.0)], 0.0, 0.0, a, 0.0
        while run < L:
            step = float(rng.uniform(4.5, 7.5))
            ang = a + max(-0.7, min(0.7, ang - a + float(rng.uniform(-0.45, 0.45))))
            x, y, run = x + step * math.cos(ang), y + step * math.sin(ang), run + step
            if math.hypot(x, y) > R_lim:
                break
            pts.append((x, y))
        branches = []
        for _b in range(2):
            if len(pts) < 3:
                break
            k = int(rng.integers(1, len(pts) - 1))
            ba = a + float(rng.choice([-1.0, 1.0])) * float(rng.uniform(0.6, 1.1))
            bl = L * float(rng.uniform(0.22, 0.38))
            bp, (bx, by), r2 = [pts[k]], pts[k], 0.0
            while r2 < bl:
                st = float(rng.uniform(4.0, 6.0))
                ba += float(rng.uniform(-0.3, 0.3))
                bx, by, r2 = bx + st * math.cos(ba), by + st * math.sin(ba), r2 + st
                if math.hypot(bx, by) > R_lim:
                    break
                bp.append((bx, by))
            branches.append((k, bp))
        out.append((pts, branches))
    return out


def chip_frame(size, stage, seed, n, Lmax):
    """Stage 1..3 of a chip decal size x size: stage s keeps what s - 1 drew and grows it."""
    c0 = size / 2
    R_lim = size / 2 - 5.0
    S = crack_set(seed, n, Lmax, R_lim)
    count = {1: max(3, n // 2), 2: max(4, n - 2), 3: n}[stage]
    frac = {1: 0.45, 2: 0.75, 3: 1.0}[stage]
    rng = np.random.default_rng(seed + 50)
    flakes = []
    for (pts, _br) in S:                                                 # each crack's two flakes, fixed for all stages: uneven
        for _f in range(2):                                              # four-cornered slivers, each its own length and turn
            k = int(rng.integers(1, max(2, len(pts))))                   # (run 1's three-cornered ones read as little arrowheads)
            px, py = pts[min(k, len(pts) - 1)]
            off, fa = float(rng.uniform(3.5, 6.0)), float(rng.uniform(0, TAU))
            L, w, turn = float(rng.uniform(2.6, 4.6)), float(rng.uniform(1.2, 2.0)), float(rng.uniform(0, TAU))
            quad = [(L * float(rng.uniform(0.8, 1.1)), 0.0), (0.2 * L, w * float(rng.uniform(0.7, 1.2))),
                    (-L * float(rng.uniform(0.6, 1.0)), 0.3 * w), (-0.1 * L, -w * float(rng.uniform(0.7, 1.2)))]
            ct, st_ = math.cos(turn), math.sin(turn)
            flakes.append((k, [(px + off * math.cos(fa) + x * ct - y * st_, py + off * math.sin(fa) + x * st_ + y * ct) for x, y in quad]))

    def fn(d, M):
        def at(pts):
            return [(c0 + x, c0 + y) for x, y in pts]

        def crack(pts, w0, w1):
            if len(pts) < 2:
                return
            G.stroke(d, at([(x - 1.0, y - 1.0) for x, y in pts]), M["ln_offwhite"], I * 0.9)                  # the lit lip
            G.stroke(d, at(pts), M["ink"], I, radii=[I * (w0 + (w1 - w0) * i / (len(pts) - 1)) for i in range(len(pts))])
        if stage == 3:                                                   # the loosened plate at the contact: a shard, not a disc
            pr = np.random.default_rng(seed + 90)
            plate = [((5.0 + 3.5 * float(pr.uniform())) * math.cos(TAU * q / 5 + 0.5) * 1.35,
                      (5.0 + 3.5 * float(pr.uniform())) * math.sin(TAU * q / 5 + 0.5) * 0.8) for q in range(5)]
            G.stroke(d, at(plate), M["offwhite_sh"], 0.0, cyclic=True)
            G.stroke(d, at(plate), M["ink"], I * 0.8, cyclic=True)
        fi = 0
        for ci, (pts, branches) in enumerate(S):
            mine = flakes[fi:fi + 2]
            fi += 2
            if ci >= count:
                continue
            keep = max(2, int(math.ceil(len(pts) * frac)))
            crack(pts[:keep], {1: 1.5, 2: 1.7, 3: 2.0}[stage], 0.7)      # heavier at the contact: the stage must read at 1x
            for bi, (k, bp) in enumerate(branches):
                if size < 128 and bi > 0:                                # the 1 m cell: one branch a crack (run 2's stage 3
                    continue                                             # was a scribble at 1x)
                if k < keep and (stage == 3 or (stage == 2 and bi == 0)):
                    crack(bp if stage == 3 else bp[:max(2, len(bp) // 2 + 1)], 1.0, 0.5)
            if stage == 3:                                               # flakes only on the last stage, one a crack
                for qi, (k, poly) in enumerate(mine):
                    if k < keep and qi == 0:
                        if all(math.hypot(x, y) < R_lim for x, y in poly):
                            G.stroke(d, at(poly), M["offwhite"], I * 0.7, cyclic=True)
    return frame(size, size, fn, seed + stage)


# ---------------------------------------------------------------- the beam's contact
def contact_frame(k):
    def fn(d, M):
        ph = TAU * k / 6
        cx, cy = 32.0, 33.0
        # the glow as a SPIKED FLARE with a five-cornered core (runs 1-4 drew a round halo with a round core and the grit
        # fanned along its rim: at 6x a lashed eye). No ink on it: a glowing part is drawn in its colour.
        halo = []
        for i in range(14):
            a = TAU * i / 14 + 0.22 * math.sin(ph + i)
            r = (14.5 + 2.2 * math.sin(ph + 1.7 * i)) if i % 2 == 0 else (8.0 + 1.0 * math.sin(ph + i))
            halo.append((cx + r * math.cos(a), cy + r * 0.9 * math.sin(a)))
        G.stroke(d, halo, M["offwhite_sh"], 0.0, cyclic=True)
        G.stroke(d, [(cx + (5.2 + 1.2 * math.sin(ph + 2 * i)) * math.cos(TAU * i / 5 + 0.3 + ph / 6),
                      cy + (4.4 + 1.0 * math.sin(ph + 2 * i)) * math.sin(TAU * i / 5 + 0.3 + ph / 6)) for i in range(5)], M["offwhite_f"], 0.0, cyclic=True)
        for j, deg in enumerate((-168.0, -128.0, -97.0, -66.0, -38.0, -10.0)):                # grit thrown clear, each on its own
            t = (k / 6 + j * 0.37) % 1.0                                                      # beat, well off the flare's edge
            a = math.radians(deg + 6 * math.sin(j * 2.3))
            dist = 16 + 11 * t
            x, y = cx + dist * math.cos(a), cy + dist * math.sin(a) + 5 * t * t
            L = 3.6 * (1 - 0.5 * t)                                                           # each a short ink dash along its own
            ux, uy = math.cos(a), math.sin(a) + 0.5 * t                                      # flight (runs 1-3 drew outlined chips:
            n = math.hypot(ux, uy)                                                           # two side by side over the round glow
            G.stroke(d, [(x - ux / n * L / 2, y - uy / n * L / 2), (x + ux / n * L / 2, y + uy / n * L / 2)], M["ink"], I * 0.9)   # read as eyes)
    return frame(64, 64, fn, 740 + k)


# ---------------------------------------------------------------- the shovel's swish
def swish_frame(j):
    """Drawing j of the smear behind the blade: 0 the full crescent, 1 thinned and breaking, 2 two wisps near the end."""
    spans = {0: [(4.0, 72.0, 9.0)], 1: [(26.0, 52.0, 5.0), (56.0, 74.0, 4.0)], 2: [(50.0, 62.0, 2.6), (66.0, 75.0, 2.2)]}[j]

    def fn(d, M):
        cx, cy = SWC
        for (a0, a1, wmax) in spans:
            n = 16
            outer, inner, mids = [], [], []
            for i in range(n + 1):
                s = i / n
                a = math.radians(a0 + (a1 - a0) * s)
                w = wmax * 1.75 * s * (1 - s) ** 0.3 + 0.6                # thin at the tail, fullest behind the blade
                outer.append((cx + (SWR + w / 2) * math.cos(a), cy + (SWR + w / 2) * math.sin(a)))
                inner.append((cx + (SWR - w / 2) * math.cos(a), cy + (SWR - w / 2) * math.sin(a)))
                mids.append((cx + SWR * math.cos(a), cy + SWR * math.sin(a)))
            G.stroke(d, outer + inner[::-1], M["offwhite"], I * 0.7, cyclic=True)
            if wmax > 4.5:                                               # a speed line along the smear's middle
                G.stroke(d, mids[n // 3:n - 2], M["ln_grey"], I * 0.6)
    return frame(SWW, SWH, fn, 780 + j)


# ---------------------------------------------------------------- the kit
def sheet_of(frames):
    fw, fh = frames[0].shape[1], frames[0].shape[0]
    cols = v3.columns_for(fw, len(frames))
    rows = -(-len(frames) // cols)
    g = v3.GUTTER
    sheet = np.zeros((rows * fh + (rows - 1) * g, cols * fw + (cols - 1) * g, 4), np.uint8)
    for i, im in enumerate(frames):
        r, c = divmod(i, cols)
        sheet[r * (fh + g):r * (fh + g) + fh, c * (fw + g):c * (fw + g) + fw] = im
    return sheet, cols


def kit():
    """[(key, sheet, json fields, frames)]."""
    out = []

    def add(key, frames, extra):
        sheet, cols = sheet_of(frames)
        out.append((key, sheet, dict({"ppu": PPU, "frame_width": frames[0].shape[1], "frame_height": frames[0].shape[0], "columns": cols,
                                      "gutter": v3.GUTTER, "frames": len(frames), "fps": 12}, **extra), frames))
    add("fx/dig_reticle/base", [arc_piece(0), arc_piece(1), corner_piece(0), corner_piece(1), pip_piece(0), pip_piece(1)],
        {"pivot": [0.5, 0.5], "ring_radius_m": 0.9,
         "animations": [{"name": "arc", "start": 0, "length": 2, "loop": True, "loop_from": 0},
                        {"name": "corner", "start": 2, "length": 2, "loop": True, "loop_from": 0},
                        {"name": "pip", "start": 4, "length": 2, "loop": True, "loop_from": 0}],
         "note": "B-246 (D-196): arc = a bracket ON a circle (the pivot on the circle's line, the circle's middle straight below the "
                 "frame: turn it about that middle, four round the target; its curve is 0.9 m, off by under a pixel on a wider "
                 "circle); corner = a 1 m cell's top-left corner at the pivot, arms right and down (turn for the other three); pip "
                 "= the contact point. States by tint and gap: in reach as drawn, clamped mustard and pushed out, nothing to dig "
                 "red and wider with no pip. Cream + ink"})
    add("fx/dig_chip/round", [chip_frame(128, s, 3100, 7, 52.0) for s in (1, 2, 3)],
        {"pivot": [0.5, 0.5], "stages": 3,
         "note": "B-246: three crack stages from the contact point for the brush (frame = stage - 1; a stage keeps the one before "
                 "and grows it); cream + ink: tint by the dug cell's tone_hex as the clods (D-190)"})
    add("fx/dig_chip/cell", [chip_frame(64, s, 3300, 5, 25.0) for s in (1, 2, 3)],
        {"pivot": [0.5, 0.5], "stages": 3,
         "note": "B-246: the same three stages inside one 1 m cell (nothing crosses its edge); cream + ink: tint by tone_hex"})
    add("fx/beam_contact/base", [contact_frame(k) for k in range(6)],
        {"pivot": [0.5, 0.5], "animations": [{"name": "glow", "start": 0, "length": 6, "loop": True, "loop_from": 0}],
         "note": "B-246: the Beam's ray on its target - a glow and thrown grit, a mining tool's work (D-087); the sprite's up is "
                 "away from the surface; cream: tint by the Beam's own tone (the ray's)"})
    add("fx/shovel_swish/base", [swish_frame(j) for j in range(3)],
        {"pivot": [round(SWC[0] / SWW, 4), round(1 - SWC[1] / SWH, 4)],
         "animations": [{"name": "swish", "start": 0, "length": 3, "loop": False}],
         "arc": {"radius_m": SWR / PPU, "from_deg": 0.0, "to_deg": -SW_END},
         "clips": ["dig_down", "dig_up"],        # LEAD 06:0x: the swings it is played on; the thrusts (dig_fwd, dig_fwd_near) have no arc
         "note": "B-246: a smear behind the blade; the pivot is the swing's centre (the grip); the arc runs clockwise from level "
                 "(0 deg) to to_deg (CCW from +x, so 75 below level), where the blade is on the contact drawing: turn it so that "
                 "end lies on the contact's direction, mirror it for a swing the other way; show drawing 0 on the contact frame"})
    return out


def checks(K):
    out = []
    m = v3.EDGE_MARGIN
    for key, img, _extra, frames in K:
        hit = v3.palette_hits(img, "earth")[0]
        if hit < 0.995:
            out.append(f"{key}: palette {hit * 100:.1f}%")
        if img.shape[1] % 4 or img.shape[0] % 4:
            out.append(f"{key}: {img.shape[1]}x{img.shape[0]} not a multiple of 4")
        for i, f in enumerate(frames):
            if f[:m, :, 3].any() or f[-m:, :, 3].any() or f[:, :m, 3].any() or f[:, -m:, 3].any():
                out.append(f"{key} frame {i}: touches the {m} px edge")
            if not f[..., 3].any():
                out.append(f"{key} frame {i}: empty")
    return out


def export(art):
    """After LEAD's ACCEPTED on sheet 2 (the manifest row is added then)."""
    from meridian import pngio
    K = kit()
    problems = checks(K)
    if problems:
        raise ValueError("B-246 checks: " + "; ".join(problems))
    out = []
    for key, img, extra, _frames in K:
        base = os.path.join(art, *key.split("/"))
        os.makedirs(os.path.dirname(base), exist_ok=True)
        n = pngio.write_png(base + "_color.png", img)
        with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
            json.dump({"key": key, "style": "v3", "width": img.shape[1], "height": img.shape[0], "palette": "earth", **extra}, f, indent=2)
            f.write("\n")
        out.append((key, img.shape[1], img.shape[0], n))
    return out


# ---------------------------------------------------------------- the sheet
def preview(out, footnote=None):
    import time
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    K = {key: (sheet, extra, frames) for key, sheet, extra, frames in kit()}
    problems = checks([(k,) + v for k, v in K.items()])
    paper = np.array(review.PAPER, np.float32)
    W = 1920

    def tone(tier):                     # UNITY's DigFeel.Tone: the tier's chip colour 35 % toward white
        return np.array(v3.hex_rgb(TIER_CHIP[tier]), np.float32) / 255.0 * 0.65 + 0.35
    pal = v3.PALETTES["earth"]
    TINT = {"in reach": np.ones(3, np.float32), "clamped": np.array(v3.hex_rgb(pal["mustard"]), np.float32) / 255.0,
            "nothing to dig": np.array(v3.hex_rgb(pal["red"]), np.float32) / 255.0}
    GAP = {"in reach": 0.0, "clamped": 6.0, "nothing to dig": 13.0}
    teal = np.array(v3.hex_rgb(pal["teal"]), np.float32) / 255.0 * 0.6 + 0.4

    fills = {}

    def ground(tier, h, w):
        if tier not in fills:
            fp = os.path.join(ART, "terrain", "earth", "ground_fill_color.png" if tier == 1 else f"ground_fill_t{tier}_color.png")
            fills[tier] = pngio.read_png_np(fp).astype(np.float32)[..., :3] / 255.0 if os.path.isfile(fp) else None
        f = fills[tier]
        if f is None:
            return np.full((h, w, 3), 0.5, np.float32)
        return np.tile(f, (-(-h // f.shape[0]), -(-w // f.shape[1]), 1))[:h, :w].copy()

    def place(dst, img, pivot, deg, at, tint=None, k=1):
        """img (straight RGBA uint8) over dst (opaque float RGB): its pivot (px, y down) at `at`, turned deg CCW on screen,
        drawn k times its size, its colour multiplied by tint."""
        h, w = img.shape[:2]
        f = img.astype(np.float32) / 255.0
        if tint is not None:
            f[..., :3] = f[..., :3] * tint
        t = math.radians(deg)
        c, s = math.cos(t), math.sin(t)
        R = (math.hypot(max(pivot[0], w - pivot[0]), max(pivot[1], h - pivot[1])) + 2) * k
        x0, x1 = max(int(at[0] - R), 0), min(int(at[0] + R) + 1, dst.shape[1])
        y0, y1 = max(int(at[1] - R), 0), min(int(at[1] + R) + 1, dst.shape[0])
        if x1 <= x0 or y1 <= y0:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        u, v = (xx + 0.5 - at[0]) / k, (yy + 0.5 - at[1]) / k
        sx = pivot[0] + u * c - v * s - 0.5
        sy = pivot[1] + u * s + v * c - 0.5
        ix, iy = np.floor(sx).astype(int), np.floor(sy).astype(int)
        fx, fy = (sx - ix)[..., None], (sy - iy)[..., None]

        def tap(ax, ay):
            ok = (ax >= 0) & (ax < w) & (ay >= 0) & (ay < h)
            o = np.zeros(ax.shape + (4,), np.float32)
            px = f[ay[ok], ax[ok]]
            o[ok] = np.concatenate([px[..., :3] * px[..., 3:4], px[..., 3:4]], axis=-1)
            return o
        smp = (tap(ix, iy) * (1 - fx) * (1 - fy) + tap(ix + 1, iy) * fx * (1 - fy) + tap(ix, iy + 1) * (1 - fx) * fy
               + tap(ix + 1, iy + 1) * fx * fy)
        sub = dst[y0:y1, x0:x1]
        sub[...] = smp[..., :3] + sub * (1 - smp[..., 3:4])

    def head(text, h=20):
        hd = np.tile(paper, (h, W, 1)).astype(np.float32)
        review._label(hd, text, 6, 4, scale=1)
        return hd

    ret = K["fx/dig_reticle/base"][2]
    chips_r, chips_c = K["fx/dig_chip/round"][2], K["fx/dig_chip/cell"][2]
    P = (RET / 2, RET / 2)

    def round_scene(tier, state, j, chip=None, radius=R0):
        S = 160
        g = ground(tier, S, S)
        c = S / 2
        if chip is not None:
            place(g, chips_r[chip], (64, 64), 0, (c, c), tint=tone(tier))
        for q in range(4):                                               # four brackets round the circle
            a = 45.0 + 90.0 * q
            rr = radius + GAP[state]
            at = (c + rr * math.cos(math.radians(a)), c - rr * math.sin(math.radians(a)))
            place(g, ret[j], P, a - 90.0, at, tint=TINT[state])
        if state != "nothing to dig":
            place(g, ret[4 + j], P, 0, (c, c), tint=TINT[state])
        review._label(g, f"{state}", 3, 3, scale=1)
        return g

    def cell_scene(tier, state, j, chip=None):
        S = 160
        g = ground(tier, S, S)
        c = S / 2
        if chip is not None:
            place(g, chips_c[chip], (32, 32), 0, (c, c), tint=tone(tier))
        h = 32.0 + GAP[state]
        for q, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, 1), (1, -1))):   # the cell's corners, turned 90 deg each (CCW)
            place(g, ret[2 + j], P, 90.0 * q, (c + sx * h, c + sy * h), tint=TINT[state])
        if state != "nothing to dig":
            place(g, ret[4 + j], P, 0, (c, c), tint=TINT[state])
        review._label(g, f"{state}", 3, 3, scale=1)
        return g

    def row(cells, gap=0):
        H = max(c.shape[0] for c in cells)
        r = np.tile(paper, (H, W, 1)).astype(np.float32)
        x = 0
        for c in cells:
            w = max(0, min(c.shape[1], W - x))
            r[:c.shape[0], x:x + w] = c[:, :w]
            x += c.shape[1] + gap
        return r

    def zoom(im, k):
        return np.repeat(np.repeat(im, k, 0), k, 1)

    rows = [np.tile(paper, (30, W, 1)).astype(np.float32)]
    review._label(rows[0], "B-246 sheet 2 (PREVIEW, nothing exported): the reticle, the chip stages, the beam's contact, the shovel's swish - cream + ink, tinted as the game would (the chips by the tier's tone, the reticle by its state)", 6, 8)
    states = ("in reach", "clamped", "nothing to dig")
    for j in (0, 1):
        rows.append(head(f"fx/dig_reticle at 1x, drawing {j} of the boil: on TAN SOIL the brush (0.9 m) in its three states, then a 1 m cell in its three | the same on GREY STONE. A chip stage lies under each in-reach reticle"))
        cells = []
        for tier in (1, 3):
            cells += [round_scene(tier, s, j, chip=1 if s == "in reach" else None) for s in states]
            cells += [cell_scene(tier, s, j, chip=1 if s == "in reach" else None) for s in states]
        rows.append(row(cells))
    rows.append(head("the brackets on a wider brush (1.5 m, in reach) on soil and stone at 1x | the three pieces at 4x, both drawings: arc, corner, pip"))
    cells = [round_scene(1, "in reach", 0, radius=1.5 * PPU * 0.5 + R0 * 0.5), round_scene(3, "in reach", 0, radius=1.5 * PPU * 0.5 + R0 * 0.5)]
    for im in ret:
        f = im.astype(np.float32) / 255.0
        on = np.tile(paper * 0.8, (RET, RET, 1)).astype(np.float32)
        on = f[..., :3] * f[..., 3:4] + on * (1 - f[..., 3:4])
        cells.append(zoom(on, 4)[:160])
    rows.append(row(cells, gap=6))
    for tier, name in ((1, "tan soil (Topsoil's tone)"), (3, "grey stone (Stone's tone)")):
        rows.append(head(f"fx/dig_chip on {name} at 1x: round stages 1-3 (128 px), cell stages 1-3 (64 px, the cell's edge drawn) | stage 3 of each at 3x (the face check)"))
        cells = []
        for s in range(3):
            g = ground(tier, 128, 128)
            place(g, chips_r[s], (64, 64), 0, (64, 64), tint=tone(tier))
            cells.append(g)
        for s in range(3):
            g = ground(tier, 128, 96)
            g[32 - 1:32, 16:80] *= 0.6
            g[96:97, 16:80] *= 0.6
            g[32:96, 15:16] *= 0.6
            g[32:96, 80:81] *= 0.6
            place(g, chips_c[s], (32, 32), 0, (48, 64), tint=tone(tier))
            cells.append(g)
        g = ground(tier, 128, 128)
        place(g, chips_r[2], (64, 64), 0, (64, 64), tint=tone(tier))
        cells.append(zoom(g, 3))
        g = ground(tier, 64, 64)
        place(g, chips_c[2], (32, 32), 0, (32, 32), tint=tone(tier))
        cells.append(zoom(g, 3))
        rows.append(row(cells, gap=4))
    rows.append(head("fx/beam_contact (tinted the Mk1 Beam's teal) at 1x: the six drawings on soil, on stone | all six at 3x on stone"))
    cells = []
    cf = K["fx/beam_contact/base"][2]
    for tier in (1, 3):
        g = ground(tier, 64, 6 * 64)
        for k in range(6):
            place(g, cf[k], (32, 32), 0, (32 + 64 * k, 32), tint=teal)
        cells.append(g)
    g = ground(3, 64, 6 * 64)
    for k in range(6):
        place(g, cf[k], (32, 32), 0, (32 + 64 * k, 32), tint=teal)
    cells.append(zoom(g, 3)[:, :1140])
    rows.append(row(cells, gap=6))
    rows.append(head("fx/shovel_swish at 1x and 2x on paper (the cross = its pivot, the swing's centre) | on side_dig's dig_down: the wind-up, then the CONTACT with swish drawing 0, the follow-through with drawing 1"))
    sw = K["fx/shovel_swish/base"][2]
    cells = []
    for k in (1, 2):
        for im in sw:
            f = im.astype(np.float32) / 255.0
            on = np.tile(paper * 0.8, (SWH, SWW, 1)).astype(np.float32)
            on = f[..., :3] * f[..., 3:4] + on * (1 - f[..., 3:4])
            on[int(SWC[1]) - 3:int(SWC[1]) + 4, int(SWC[0])] = (0.85, 0.15, 0.1)
            on[int(SWC[1]), int(SWC[0]) - 3:int(SWC[0]) + 4] = (0.85, 0.15, 0.1)
            cells.append(zoom(on, k))
    rows.append(row(cells, gap=6))                                       # (run 1: one row for both overflowed the sheet)
    cells = []
    b246 = os.path.join(os.path.dirname(out), "b246")
    dig_png, dig_js = os.path.join(b246, "side_dig_color.png"), os.path.join(b246, "side_dig.json")
    shovel_p = os.path.join(ART, "props", "rig", "shovel_color.png")
    if os.path.isfile(dig_png) and os.path.isfile(dig_js) and os.path.isfile(shovel_p):
        dj = json.load(open(dig_js, encoding="utf-8"))
        ds = pngio.read_png_np(dig_png)
        shovel = pngio.read_png_np(shovel_p)
        fw, fh, gg, cols = dj["frame_width"], dj["frame_height"], dj["gutter"], dj["columns"]
        for fi, sj in ((0, None), (1, 0), (2, 1)):
            r_, c_ = divmod(fi, cols)
            fr = ds[r_ * (fh + gg):r_ * (fh + gg) + fh, c_ * (fw + gg):c_ * (fw + gg) + fw].astype(np.float32) / 255.0
            cell = np.tile(paper, ((fh + 64) * 2, (fw + 96) * 2, 1)).astype(np.float32)
            cell[fh * 2:] = paper * 0.86
            f2 = zoom(fr, 2)
            sub = cell[:fh * 2, :fw * 2]
            sub[...] = f2[..., :3] * f2[..., 3:4] + sub * (1 - f2[..., 3:4])
            hx, hz, ha = dj["sockets"]["hand"][fi]
            at = ((1.5 + hx) * 128, (3.0 - hz) * 128)
            if sj is not None:                                           # the swish: its end on the contact's direction
                hc = dj["sockets"]["hand"][1]
                place(cell, sw[sj], SWC, math.degrees(hc[2]) + SW_END, ((1.5 + hc[0]) * 128, (3.0 - hc[1]) * 128), k=2)
            place(cell, shovel, (0.0667 * shovel.shape[1], shovel.shape[0] * 0.5), math.degrees(ha), at)
            cells.append(cell)
    if cells:
        rows.append(row(cells, gap=6))
    lines = [f"{key}: sheet {sheet.shape[1]}x{sheet.shape[0]}, {len(frames)} frames of {frames[0].shape[1]}x{frames[0].shape[0]}, palette {v3.palette_hits(sheet, 'earth')[0] * 100:.1f}%"
             for key, (sheet, _e, frames) in K.items()]
    lines.append("problems: " + ("; ".join(problems) if problems else "none"))
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " " + (footnote or "B-246 sheet 2 preview (lock-free, fakegp + numpy; not exported)"), 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


# ---------------------------------------------------------------- B-249: the pip, old beside new
def _place(dst, img, pivot, deg, at, tint=None):
    """img (straight RGBA uint8) over dst (opaque float RGB): its pivot (px, y down) at `at`, turned deg CCW on screen, its
    colour multiplied by tint. (preview()'s own place(), at 1x; that sheet's code is left as accepted.)"""
    h, w = img.shape[:2]
    f = img.astype(np.float32) / 255.0
    if tint is not None:
        f[..., :3] = f[..., :3] * tint
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    R = math.hypot(max(pivot[0], w - pivot[0]), max(pivot[1], h - pivot[1])) + 2
    x0, x1 = max(int(at[0] - R), 0), min(int(at[0] + R) + 1, dst.shape[1])
    y0, y1 = max(int(at[1] - R), 0), min(int(at[1] + R) + 1, dst.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    u, v = xx + 0.5 - at[0], yy + 0.5 - at[1]
    sx = pivot[0] + u * c - v * s - 0.5
    sy = pivot[1] + u * s + v * c - 0.5
    ix, iy = np.floor(sx).astype(int), np.floor(sy).astype(int)
    fx, fy = (sx - ix)[..., None], (sy - iy)[..., None]

    def tap(ax, ay):
        ok = (ax >= 0) & (ax < w) & (ay >= 0) & (ay < h)
        o = np.zeros(ax.shape + (4,), np.float32)
        px = f[ay[ok], ax[ok]]
        o[ok] = np.concatenate([px[..., :3] * px[..., 3:4], px[..., 3:4]], axis=-1)
        return o
    smp = (tap(ix, iy) * (1 - fx) * (1 - fy) + tap(ix + 1, iy) * fx * (1 - fy) + tap(ix, iy + 1) * (1 - fx) * fy
           + tap(ix + 1, iy + 1) * fx * fy)
    sub = dst[y0:y1, x0:x1]
    sub[...] = smp[..., :3] + sub * (1 - smp[..., 3:4])


def pip_preview(out):
    """B-249: the old cross beside the tick and the open diamond, inside the Beam's white brackets (0.9 m) on tan soil, on
    grey stone and on a dark back wall, at 1x and 4x; the pieces alone at 6x, both boil drawings; and the proof that
    nothing else of the five exported sheets moves (the reticle's frames 0-3 and the other four sheets, pixel for pixel)."""
    import time
    from meridian import pngio
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    paper = np.array(review.PAPER, np.float32)
    W, S = 1920, 160
    kinds = (("cross", "OLD: the cross (B-246)"), ("tick", "NEW: the ground tick"), ("diamond", "the alternative: an open diamond"))
    arcs = [arc_piece(0), arc_piece(1)]
    pips = {k: [pip_piece(0, k), pip_piece(1, k)] for k, _n in kinds}
    P = (RET / 2, RET / 2)

    def fill(tier):
        fp = os.path.join(ART, "terrain", "earth", "ground_fill_color.png" if tier == 1 else f"ground_fill_t{tier}_color.png")
        if not os.path.isfile(fp):
            return np.full((S, S, 3), 0.5, np.float32)
        f = pngio.read_png_np(fp).astype(np.float32)[..., :3] / 255.0
        return np.tile(f, (-(-S // f.shape[0]), -(-S // f.shape[1]), 1))[:S, :S].copy()
    grounds = (("tan soil", lambda: fill(1)), ("grey stone", lambda: fill(3)),
               ("a dark back wall", lambda: np.tile(np.array((0.33, 0.20, 0.16), np.float32), (S, S, 1))))

    def scene(gfn, kind, j=0):
        g = gfn()
        c = S / 2
        for q in range(4):
            a = 45.0 + 90.0 * q
            _place(g, arcs[j], P, a - 90.0, (c + R0 * math.cos(math.radians(a)), c - R0 * math.sin(math.radians(a))))
        _place(g, pips[kind][j], P, 0, (c, c))
        return g

    def head(text, h=20):
        hd = np.tile(paper, (h, W, 1)).astype(np.float32)
        review._label(hd, text[:300], 6, 4, scale=1)
        return hd

    def row(cells, gap=8):
        H = max(c.shape[0] for c in cells)
        r = np.tile(paper, (H, W, 1)).astype(np.float32)
        x = 0
        for c in cells:
            w = max(0, min(c.shape[1], W - x))
            r[:c.shape[0], x:x + w] = c[:, :w]
            x += c.shape[1] + gap
        return r

    def zoom(im, k):
        return np.repeat(np.repeat(im, k, 0), k, 1)
    rows = [head("B-249 (PREVIEW, nothing exported): the reticle's PIP, from the 0.6.3 smoke read (H3): four brackets round a cross read as a gun sight with the Beam. The Beam's white in-reach brackets (0.9 m) round each mark", 26)]
    for gname, gfn in grounds:
        rows.append(head(f"on {gname.upper()} at 1x: " + " | ".join(n for _k, n in kinds) + "     then the same three at 3x (the middle 96 px)"))
        cells = [scene(gfn, k) for k, _n in kinds]
        cells += [zoom(scene(gfn, k)[32:128, 32:128], 3) for k, _n in kinds]
        rows.append(row(cells))
    rows.append(head("the marks alone at 6x, both drawings of the boil: " + " | ".join(n for _k, n in kinds)))
    cells = []
    for k, _n in kinds:
        for im in pips[k]:
            f = im.astype(np.float32) / 255.0
            on = np.tile(paper * 0.8, (RET, RET, 1)).astype(np.float32)
            cells.append(zoom(f[..., :3] * f[..., 3:4] + on * (1 - f[..., 3:4]), 6)[60:228, 60:228])
    rows.append(row(cells))
    # the proof: with PIP as set, what an export would change
    lines = [f"PIP = \"{PIP}\" in the source: an export rewrites fx/dig_reticle/base (png only: its frames 4 and 5); the key, the slots and the json stay"]
    names = {"fx/dig_reticle/base": "fx/dig_reticle/base_color.png", "fx/dig_chip/round": "fx/dig_chip/round_color.png", "fx/dig_chip/cell": "fx/dig_chip/cell_color.png",
             "fx/beam_contact/base": "fx/beam_contact/base_color.png", "fx/shovel_swish/base": "fx/shovel_swish/base_color.png"}
    for key, sheet, extra, frames in kit():
        fp = os.path.join(ART, *names[key].split("/"))
        if not os.path.isfile(fp):
            lines.append(f"{key}: no exported png found")
            continue
        old = pngio.read_png_np(fp)
        if old.shape != sheet.shape:
            lines.append(f"{key}: SIZE DIFFERS {old.shape} against {sheet.shape}")
            continue
        if key == "fx/dig_reticle/base":
            wd = 4 * RET + 3 * v3.GUTTER
            same = bool((old[:, :wd] == sheet[:, :wd]).all())
            diff = int((old[:, wd:] != sheet[:, wd:]).any(axis=-1).sum())
            lines.append(f"{key}: frames 0-3 (two arcs, two corners) {'IDENTICAL' if same else 'DIFFER'} to the exported png; frames 4-5 (the pip) differ in {diff} px; "
                         f"palette {v3.palette_hits(sheet, 'earth')[0] * 100:.1f}%; the json's fields rebuilt equal: "
                         f"{json.load(open(fp.replace('_color.png', '.json'), encoding='utf-8')).get('animations') == extra.get('animations')}")
        else:
            lines.append(f"{key}: {'IDENTICAL' if bool((old == sheet).all()) else 'DIFFERS'} to the exported png, pixel for pixel")
    problems = checks(kit())
    lines.append("checks: " + ("; ".join(problems) if problems else "none failed"))
    foot = np.tile(paper, (24 + 16 * len(lines), W, 1)).astype(np.float32)
    for i, ln in enumerate(lines):
        review._label(foot, ln[:300], 6, 6 + 16 * i, scale=1)
    img = np.vstack(rows + [foot])
    review.draw(img, time.strftime("%m-%d %H:%M") + " B-249 the reticle's pip, old beside new (lock-free, fakegp + numpy; not exported)", 2, img.shape[0] - 14, (1.0, 1.0, 0.85))
    review.write(out, img)
    print("written", out, img.shape[1], "x", img.shape[0])
    for ln in lines:
        print(ln)


if __name__ == "__main__":                       # <review png>  |  --pip <review png>
    if len(sys.argv) > 2 and sys.argv[1] == "--pip":
        pip_preview(sys.argv[2])
    else:
        preview(sys.argv[1])
