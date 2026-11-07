"""C2 Earth ground strips (LEAD cycle 247 while-waiting #2; replaces U-100's placeholder dirt): the grass,
soil and stone ground re-inked at v3.1 in U-100's contract, so GroundStrip.cs can load them unchanged:

  terrain/earth/ground_strip         grass: a drawn 1 m grass lip over soil (the key U-100 loads today)
  terrain/earth/ground_strip_soil    bare soil (dug or trodden columns)
  terrain/earth/ground_strip_stone   stone outcrop

Each is 8 frames of 64x152 px, one frame per terrain column (B-130 export: one 540x152 sheet per
material, 4 px gutters, "tile": true, no clips). GroundStrip.cs puts a frame's PIVOT on the ground line
and hangs the fill StripHeight = 2 m below it, so a frame is 2 m below the ground line (128 px) plus
0.375 m above it (24 px) for the lip and tufts: pivot [0.5, 128/152].

Frame anatomy (metres, x -0.5..0.5, z 0..2.375, ground line z = SURF = 2): the inked SILHOUETTE (outer
weight, 2-3 px) runs ON the ground line at both frame edges in every material (flat for the outer 5 px;
UNITY's wall-edge ink starts there), so any frame joins
any frame of any material; between the edges it bumps (grass waves, soil clods, stone knobs). Under it
a band in the material's mid tone, then the body; interior detail (pebbles, roots, worm burrows,
cracks, lichen, strata hatch, specks) stays >= 5 px from the edges and above the bottom 24 px. The
bottom 8 px of frame 0 is the fill tile U-100 cuts for the depth below. "Paper fill": a faint
aged-paper grain (x-periodic at 64 px, identical at the frame edges, fading out over the bottom
24 px so the fill tile repeats cleanly) on the flat cel colour. v3.1 ink, no faces.

  python -I build_c2_ground_strip.py <out.png>     (lock-free: meridian.fakegp, no Blender)
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import fakegp  # noqa: E402

G = fakegp.install()
import gp_raster as GR  # noqa: E402
P = G.PALETTES["earth"]
O, I = G.OUTER, G.INNER
SURF = 2.0                         # the ground line (the tile top) inside the frame: GroundStrip.StripHeight below it
LIP = 0.0                          # the silhouette's height above the ground line at the frame edges (every material)
EDGE = 5 / 64.0                    # detail and bumps keep this far from the column edges
FW, FH = 64, 152
GUTTER = 4


def _mix(a, b, t):
    return G.rgb_hex([x * (1 - t) + y * t for x, y in zip(G.hex_rgb(a), G.hex_rgb(b))])


DIRT = _mix(P["brown"], P["mustard"], 0.38)
STONE = _mix(P["sky"], P["brown"], 0.40)
SAND = _mix(P["mustard"], P["offwhite"], 0.55)       # the B-133 coast dunes' sand
KEYS = {"grass": "terrain/earth/ground_strip", "soil": "terrain/earth/ground_strip_soil", "stone": "terrain/earth/ground_strip_stone",
        "sand": "terrain/earth/ground_strip_sand"}  # sand: the coast (LEAD cycle 252), the same frame contract
KINDS = tuple(KEYS)


def mats(gp):
    return {
        "dirt": G.mat(gp, "dirt", fill=DIRT, ink=False),
        "dirt_sh": G.mat(gp, "dirt_mid", fill=G.shadow_of(DIRT), ink=False),
        "dirt_dp": G.mat(gp, "dirt_deep", fill=G.deep_of(DIRT), ink=False),
        "stone": G.mat(gp, "stone", fill=STONE, ink=False),
        "stone_sh": G.mat(gp, "stone_mid", fill=G.shadow_of(STONE), ink=False),
        "stone_dp": G.mat(gp, "stone_deep", fill=G.deep_of(STONE), ink=False),
        "grass": G.mat(gp, "grass", fill=P["green"], ink=False),
        "grass_sh": G.mat(gp, "grass_mid", fill=G.shadow_of(P["green"]), ink=False),
        "tuft": G.mat(gp, "tuft", fill=P["green"], behind=True),
        "sand": G.mat(gp, "sand", fill=SAND, ink=False),
        "sand_sh": G.mat(gp, "sand_mid", fill=G.shadow_of(SAND), ink=False),
        "sand_dp": G.mat(gp, "sand_deep", fill=G.deep_of(SAND), ink=False),
        "shell": G.mat(gp, "shell", fill=P["offwhite"]),
        "weed": G.mat(gp, "weed", fill=_mix(P["green"], P["teal"], 0.4), behind=True),
        "pebble": G.mat(gp, "pebble", fill=G.shadow_of(P["offwhite"])),
        "lichen": G.mat(gp, "lichen", fill=P["mustard"]),
        "ink": G.mat(gp, "ink", fill=None, ink=True),
    }


def win(x, L=-0.5, R=0.5):
    """0 within EDGE of either edge, rising smoothly to 1 in the middle (so edges match exactly)."""
    u = (x - L - EDGE) / (R - L - 2 * EDGE)
    return 0.0 if u <= 0 or u >= 1 else math.sin(math.pi * u) ** 0.6


def silhouette(kind, k, n=33):
    rnd = random.Random(7000 + k * 13 + len(kind))
    xs = [-0.5 + i / (n - 1) for i in range(n)]
    if kind == "grass":                      # a soft wave
        f = 2 + k % 3
        return [(x, SURF + LIP + 0.03 * win(x) * math.sin(math.pi * (x + 0.5) * f + k)) for x in xs]
    if kind == "soil":                       # crumbly clods
        ph = [rnd.uniform(0, 6.28) for _ in range(2)]
        return [(x, SURF + LIP + win(x) * (0.012 * math.sin(23 * x + ph[0]) + 0.010 * math.sin(41 * x + ph[1]) - 0.006)) for x in xs]
    if kind == "sand":                       # low wind ripples
        return [(x, SURF + LIP + win(x) * (0.011 * math.sin(math.pi * (x + 0.5) * (5 + k % 2) + k) - 0.003)) for x in xs]
    knobs = [(rnd.uniform(-0.3, 0.3), rnd.uniform(0.04, 0.07), rnd.uniform(0.10, 0.18)) for _ in range(2)]
    return [(x, SURF + LIP + win(x) * (sum(h * math.exp(-((x - c) / w) ** 2) for c, h, w in knobs) - 0.01)) for x in xs]


def _top_z(top, x, r=0.04):
    return min(z for xx, z in top if abs(xx - x) < r)


def frame(d, M, kind, k):
    rnd = random.Random(1000 + 31 * k + 7 * len(kind))
    L, R = -0.5, 0.5
    body = {"stone": "stone", "sand": "sand", "basalt": "stone"}.get(kind, "dirt")      # B-139 Mars: regolith = dirt, basalt = stone
    top = silhouette(kind, k)
    G.stroke(d, [(L, 0.0), (R, 0.0)] + top[::-1], M[body], 0.0, cyclic=True)            # the body up to the silhouette
    band = [(x, z - 0.18 - 0.03 * win(x) * math.sin(9 * x + k)) for x, z in top]        # mid-tone band under the top
    G.stroke(d, top + band[::-1], M[body + "_sh"], 0.0, cyclic=True)
    if kind == "grass":                                                                  # the drawn 1 m grass lip
        under = [(x, z - 0.12 - 0.035 * win(x) * (0.5 + 0.5 * math.sin(7 * x + 2 * k))) for x, z in top]
        G.stroke(d, top + under[::-1], M["grass"], 0.0, cyclic=True)
        G.stroke(d, [(x, z - 0.075) for x, z in top] + under[::-1], M["grass_sh"], 0.0, cyclic=True)
        G.seam(d, [p for p in under if win(p[0]) > 0.15], M["ink"])                     # grass meets soil
        for t in range(2 + k % 3):                                                       # tufts, never across an edge
            cx = rnd.uniform(L + EDGE + 0.09, R - EDGE - 0.09)
            base = _top_z(top, cx, 0.05) - 0.01
            for b in range(3):
                a = math.radians(-25 + 25 * b + rnd.uniform(-8, 8))
                h = rnd.uniform(0.11, 0.19)
                G.stroke(d, [(cx - 0.018, base), (cx + h * math.sin(a), base + h * math.cos(a)), (cx + 0.018, base)], M["tuft"], I, cyclic=True)
        for x in [rnd.uniform(L + EDGE + 0.05, R - EDGE - 0.05) for _ in range(5)]:      # blade strokes in the lip
            z = _top_z(top, x)
            G.seam(d, [(x, z - 0.09), (x + 0.01, z - 0.04)], M["ink"])
        if k % 2 == 0:                                                                   # a root curling down from the lip
            rx = rnd.uniform(L + EDGE + 0.15, R - EDGE - 0.15)
            G.seam(d, G.bezier((rx, SURF - 0.10), (rx + 0.10, SURF - 0.32), (rx - 0.05, SURF - 0.52), n=8), M["ink"])
            G.seam(d, G.bezier((rx + 0.04, SURF - 0.30), (rx + 0.10, SURF - 0.35), (rx + 0.13, SURF - 0.43), n=5), M["ink"])
    elif kind in ("soil", "regolith"):
        for c in range(3 + k % 2):                                                       # crumbs on the topsoil
            cx = rnd.uniform(L + EDGE + 0.06, R - EDGE - 0.06)
            cz = SURF + LIP - rnd.uniform(0.05, 0.11)
            G.stroke(d, G.lumpy_ellipse(cx, cz, 0.03, 0.02, n=10, lump=0.12, seed=k * 7 + c), M["dirt_dp"], 0.0, cyclic=True)
        if kind == "soil" and k % 2 == 1:                                                # a worm burrow (Earth only)
            wx = rnd.uniform(L + EDGE + 0.15, R - EDGE - 0.15)
            G.seam(d, [(wx + 0.05 * math.sin(i * 1.3), SURF - 0.30 - 0.06 * i) for i in range(7)], M["ink"])
            G.stroke(d, G.lumpy_ellipse(wx + 0.05 * math.sin(7.8), SURF - 0.72, 0.035, 0.03, n=10, seed=k), M["dirt_dp"], 0.0, cyclic=True)
    elif kind == "sand":                                                                 # ripple marks, shells, a strand of weed
        for c in range(3):
            zz = SURF - 0.16 - 0.13 * c - rnd.uniform(0.0, 0.04)
            x0 = rnd.uniform(L + EDGE + 0.04, -0.15)
            G.seam(d, [(x0 + 0.05 * i, zz + 0.012 * math.sin(i * 1.7 + c)) for i in range(int((rnd.uniform(0.25, 0.45)) / 0.05))], M["ink"])
        for c in range(1 + k % 2):
            sx, sz = rnd.uniform(L + EDGE + 0.08, R - EDGE - 0.08), rnd.uniform(0.55, SURF - 0.45)
            fan = [(sx, sz)] + [(sx + 0.055 * math.cos(a), sz + 0.045 * math.sin(a)) for a in [0.25 + 0.33 * j for j in range(9)]]
            G.stroke(d, fan, M["shell"], I, cyclic=True)
            for a in (1.0, 1.6, 2.2):
                G.seam(d, [(sx, sz), (sx + 0.045 * math.cos(a), sz + 0.037 * math.sin(a))], M["ink"])
        if k % 3 == 0:
            wx = rnd.uniform(L + EDGE + 0.15, R - EDGE - 0.25)
            G.stroke(d, G.hose_outline(G.bezier((wx, _top_z(top, wx) - 0.035), (wx + 0.08, _top_z(top, wx) - 0.0), (wx + 0.18, _top_z(top, wx) - 0.04), n=8), 0.025),
                     M["weed"], I, cyclic=True)
    else:                                                                                # stone: blocks, cracks, lichen
        for c in range(2):
            y0 = rnd.uniform(0.55, SURF - 0.35)
            pts = [(L + EDGE + 0.02, y0)]
            while pts[-1][0] < R - EDGE - 0.12:
                pts.append((pts[-1][0] + rnd.uniform(0.08, 0.16), pts[-1][1] + rnd.uniform(-0.05, 0.05)))
            G.seam(d, pts, M["ink"])
            bx = rnd.uniform(L + EDGE + 0.15, R - EDGE - 0.15)
            G.seam(d, [(bx, y0 + 0.01), (bx + rnd.uniform(-0.03, 0.03), y0 + rnd.uniform(0.18, 0.28))], M["ink"])
        for c in range(2):                                                               # deep-tone pits
            G.stroke(d, G.lumpy_ellipse(rnd.uniform(L + EDGE + 0.1, R - EDGE - 0.1), rnd.uniform(0.6, SURF - 0.4), 0.05, 0.03, n=12, seed=k * 3 + c),
                     M["stone_dp"], 0.0, cyclic=True)
        for c in range(1 + k % 2):                                                       # mustard lichen on the top
            lx = rnd.uniform(L + EDGE + 0.08, R - EDGE - 0.08)
            lz = _top_z(top, lx) - 0.035
            G.stroke(d, G.lumpy_ellipse(lx, lz, 0.035, 0.018, n=10, lump=0.15, seed=40 + k + c), M["lichen"], I, cyclic=True)
    if kind != "stone":
        for p in range(rnd.randint(1, 3)):                                               # pebbles
            px, pz = rnd.uniform(L + EDGE + 0.06, R - EDGE - 0.06), rnd.uniform(0.55, SURF - 0.40)
            r = rnd.uniform(0.035, 0.06)
            G.stroke(d, G.lumpy_ellipse(px, pz, r * 1.3, r, n=14, lump=0.08, seed=k * 10 + p), M["pebble"], I, cyclic=True)
            G.seam(d, [(px - r * 0.6, pz - r * 0.2), (px + r * 0.5, pz - r * 0.45)], M["ink"])
        G.stroke(d, G.lumpy_ellipse(rnd.uniform(L + EDGE + 0.1, R - EDGE - 0.1), rnd.uniform(0.7, 1.2), 0.06, 0.035, n=12, seed=k + 50),
                 M[body + "_dp"], 0.0, cyclic=True)                                      # a darker clod
    hx, hz = rnd.uniform(L + EDGE + 0.12, R - EDGE - 0.12), rnd.uniform(0.6, 1.15)
    G.hatch(d, hx, hz, M["ink"], n=3, length=0.09, spacing=0.03, angle_deg=rnd.choice((15, 165)), seed=k)
    G.specks(d, [(rnd.uniform(L + EDGE, R - EDGE), rnd.uniform(0.45, SURF - 0.25)) for _ in range(4)], M["ink"])
    G.stroke(d, top, M["ink"], O)                                                        # the silhouette, outer weight


def paper_grain(k, amp=0.035):
    """A faint aged-paper grain for one frame (row 0 = top): x-periodic at 64 px and the same at both
    edges for every frame (the per-frame part is windowed to 0 there), fading to 0 over the bottom 24 rows."""
    import numpy as np

    def smooth(seed):
        r = np.random.default_rng(seed).standard_normal((FH, FW))
        for _ in range(2):
            r = (r + np.roll(r, 1, 1) + np.roll(r, -1, 1) + np.roll(r, 1, 0) + np.roll(r, -1, 0)) / 5
        return r / max(1e-6, r.std())
    w = np.sin(np.pi * (np.arange(FW) + 0.5) / FW) ** 2
    g = smooth(91) + w[None, :] * smooth(100 + k)
    fade = np.clip((FH - 1 - np.arange(FH)) / 24.0, 0, 1)[:, None]
    return 1.0 + amp * np.tanh(g / 2) * fade


def steady_ends(sil, seed):
    """Cancel gp_raster's +-20 % width jitter on the silhouette's outer EDGE at both frame edges, so the
    line is exactly the nominal outer width where columns meet (every frame, every material) and still
    hand-jittered in between. Mirrors gp_raster.render_frame's per-stroke seed (seed * 7919 + id)."""
    import numpy as np
    xz = sil["xz"]
    s_ = np.cumsum(np.r_[0.0, np.hypot(*np.diff(xz, axis=0).T)])
    nz = GR._noise1d(s_, seed * 7919 + sil["id"], 0.18)
    x = xz[:, 0]
    e = np.clip(1.0 - np.minimum(x + 0.5, 0.5 - x) / EDGE, 0.0, 1.0)
    sil["radius"] = (sil["radius"] * (1.0 - e + e / (1.0 + GR.JITTER * nz))).astype(np.float32)


def sheets(kinds=None, mats_fn=None):
    """{kind: [8 frames HxWx4 uint8]} and the measured ink widths."""
    import numpy as np
    out, allw = {}, []
    for kind in (kinds or KINDS):
        gp = fakegp.FakeGP()
        M = (mats_fn or mats)(gp)
        frames = []
        for k in range(8):
            d = fakegp.FakeDrawing()
            frame(d, M, kind, k)
            st = fakegp.strokes_of(d, gp)
            steady_ends(st[-1], seed=k + 1)          # the silhouette is the last stroke
            img, w = GR.render_frame(st, FW, FH, 64, (0.5, 0.0), ss=4, seed=k + 1)
            rgb = np.clip(img[..., :3].astype(np.float32) * paper_grain(k, 0.02 if kind == "sand" else 0.035)[..., None], 0, 255)   # sand is brighter: the same grain contrast
            frames.append(np.dstack([np.rint(rgb).astype(np.uint8), img[..., 3]]))
            allw += w
        out[kind] = frames
    return out, allw


def ink_rows(img, col):
    """Rows where a frame's edge column is the ink colour (within 40 of #1E1A17 per channel; B-139: a darker material
    such as Mars basalt made the anti-aliased row under the line pass a plain darkness test on some edges)."""
    import numpy as np
    ink = np.array(G.hex_rgb(G.INK), np.int32)
    near = np.abs(img[:, col, :3].astype(np.int32) - ink).max(axis=1) < 40
    return tuple(int(r) for r in np.nonzero(near & (img[:, col, 3] > 128))[0])


def checks(S):
    """B-130 accept: joins <= 1/255 within a material; identical silhouette ink rows on all 48 edges."""
    within = {k: edge_join(S[k], S[k]) for k in S}
    edge_sets = {ink_rows(im, c) for k in S for im in S[k] for c in (0, FW - 1)}
    same = len(edge_sets) == 1 and bool(min(edge_sets))
    across = (f"identical in all {sum(len(v) for v in S.values()) * 2} edges, rows {min(edge_sets)[0]}-{min(edge_sets)[-1]}" if same
              else f"MISMATCH {sorted(edge_sets)[:3]}")
    problems = [f"{k}: edge join {v:.2f}/255 > 1" for k, v in within.items() if v > 1.0] + ([] if same else [f"silhouette ink {across}"])
    return within, across, problems


def export(art, S=None):
    """B-130: terrain/earth/ground_strip{,_soil,_stone}_color.png (8 frames 64x152 in one row, 4 px
    gutters) + <name>.json (style v3, pivot on the ground line, "tile": true, no clips). Raises on a
    failed accept check. Returns [(key, w, h, bytes)], within, across."""
    import json
    import numpy as np
    from meridian import pngio, v3
    if S is None:
        S, _w = sheets()
    within, across, problems = checks(S)
    if problems:
        raise ValueError("ground strips fail the B-130 checks: " + "; ".join(problems))
    out = []
    for kind in KINDS:
        key = KEYS[kind]
        W = 8 * FW + 7 * GUTTER
        sheet = np.zeros((FH, W, 4), np.uint8)
        for j, im in enumerate(S[kind]):
            sheet[:, j * (FW + GUTTER):j * (FW + GUTTER) + FW] = im
        meta = {"key": key, "style": "v3", "frame_width": FW, "frame_height": FH, "columns": 8, "gutter": GUTTER, "frames": 8,
                "fps": 12, "pivot": [0.5, round(SURF * 64 / FH, 6)], "facing": "right", "ppu": 64, "tile": True, "animations": [],
                "ground_line_px": int(round(SURF * 64)), "material": kind,
                "note": "one frame per terrain column (x mod 8); pivot = the ground line; 2 m below it, the fill = frame 0's bottom 8 px"}
        bad = [m for m in v3.validate_sheet(meta, sheet.shape) if "sum of clip lengths" not in m]
        if bad:
            raise ValueError(f"{key}: " + "; ".join(bad))
        d = os.path.join(art, *key.split("/")[:2])
        os.makedirs(d, exist_ok=True)
        name = key.split("/")[2]
        n = pngio.write_png(os.path.join(d, name + "_color.png"), sheet)
        with open(os.path.join(d, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
        out.append((key, W, FH, n))
    return out, within, across


def edge_join(frames_a, frames_b, rows=None):
    import numpy as np
    worst = 0.0
    for a in frames_a:
        for b in frames_b:
            ra, rb = a[:, -1, :].astype(np.int32), b[:, 0, :].astype(np.int32)
            if rows is not None:
                ra, rb = ra[rows], rb[rows]
            worst = max(worst, float(np.abs(ra - rb).mean()))
    return worst


def main(out, S=None, allw=None, footnote="sources + preview"):
    import json
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    from meridian import v3
    import preview_c2_earth_rigs as PR
    if S is None:
        S, allw = sheets()
    paper = review.PAPER
    W = 1920 + 16
    rows = []
    head = np.tile(paper, (28, W, 1)).astype(np.float32)
    review._label(head, "b-130 earth ground strips v3.1 (groundstrip.cs: 8 frames 64x152 per material, pivot on the ground line, 2 m below + 0.375 m above; grass / soil / stone / sand (the coast); drawn grass lip; paper grain fill)", 6, 8)
    rows.append(head)
    # (1) every frame at 3x per material
    for kind in KINDS:
        r = np.tile(np.array([0.62, 0.72, 0.72], np.float32), (FH * 3 + 26, W, 1))
        review._label(r, f"{KEYS[kind]}  ({kind})", 6, 4)
        for j, im in enumerate(S[kind]):
            review._over(r, np.repeat(np.repeat(im, 3, 0), 3, 1), 8 + j * (FW * 3 + 6), 22)
        rows.append(r)
    # (2) assembled at 1x across a 1080p width on the B-114 plains: a hill with a stone outcrop, a bare
    # soil patch, a dug hole (soil at its bottom), the fill below, the surveyor and some C2 plants
    MH = 560
    keep, PR.PLAINS_H = PR.PLAINS_H, MH                 # the painted plains at the mock's full height
    try:
        mock, note = PR.plains_strip(W)
    finally:
        PR.PLAINS_H = keep
    base_y = MH - 196                                     # the ground line of the flat columns (a dug column still fits)
    heights = [0] * 30
    for c in (11, 12, 13, 14, 15, 16):
        heights[c] = 1
    for c in (13, 14):
        heights[c] = 2
    heights[24] = -1
    kinds = ["grass"] * 30
    for c in (13, 14, 15):
        kinds[c] = "stone"
    for c in (20, 21, 24):
        kinds[c] = "soil"
    rnd = np.random.default_rng(4)
    fill = {k: np.array(S[k][0][-4, 30, :3], np.float32) / 255 for k in S}
    tops = []
    for c in range(30):
        x = 8 + c * 64
        gy = base_y - heights[c] * 64
        im = S[kinds[c]][int(rnd.integers(0, 8))]
        y0 = gy - (FH - int(round(SURF * 64)))           # the frame's ground row (its pivot) sits 24 px below its top
        review._over(mock, im, x, y0)
        mock[y0 + FH:, x:x + 64] = fill[kinds[c]]
        tops.append(gy - int(round(LIP * 64)))
    back = np.array(v3.hex_rgb(DIRT), np.float32) / 255 * np.array([0.62, 0.62, 0.66], np.float32)
    for c in range(1, 29):                                 # a dug column shows U-100's shaded back wall above it
        if heights[c] < 0:
            x = 8 + c * 64
            mock[min(tops[c - 1], tops[c + 1]):tops[c] - 1, x:x + 64] = back
    ink = np.array(v3.hex_rgb(P["ink"]), np.float32) / 255
    for c in range(29):                                    # the ink edge where neighbours differ (as U-100 draws it)
        a, b = tops[c], tops[c + 1]
        if a != b:
            x = 8 + (c + 1) * 64
            mock[min(a, b):max(a, b) + 2, x - 1:x + 2] = ink
    try:
        fr, piv = PR.surveyor_frame()
        review._over(mock, fr, 8 + 6 * 64, base_y - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    except Exception:  # noqa: BLE001
        pass
    for plant, col in ((PR.R.NODBELL, 3), (PR.R.WHIPTUFT, 9), (PR.R.THRIFTCUSHION, 18), (PR.R.CURLFROND, 27)):
        img, _w = PR.render_plant(plant, PR.R.PARTS, PR.R.mats, {}, {})
        gy = base_y - heights[col] * 64
        review._over(mock, img, 8 + col * 64 + 32 - int(PR.PIV[0] * PR.FW), gy - PR.FH + int(round(PR.PIV[1] * PR.FH)))
    sn, _w = PR.render_plant(PR.R.snoozle_plant(), PR.F.PARTS, PR.F.mats, {}, {})
    review._over(mock, sn, 8 + 22 * 64 + 32 - int(PR.PIV[0] * PR.FW), base_y - PR.FH + int(round(PR.PIV[1] * PR.FH)))
    review._label(mock, f"1x across 1920 px on the b-114 plains ({note}): grass hill with a stone outcrop, bare soil at 20-21, a dug hole at 24, "
                        "the 8 px fill below; surveyor, nodbell, whiptuft, thriftcushion, snoozle, curlfrond", 6, 6)
    rows.append(mock)
    # (3) checks
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    within, across, _problems = checks(S)
    foot = np.tile(paper, (52, W, 1)).astype(np.float32)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; edge join within a material (mean |right - left| over all frame pairs): "
                        + ", ".join(f"{k} {v:.1f}" for k, v in within.items()) + f"/255; silhouette ink at the frame edges across materials: {across}", 6, 8)
    review._label(foot, f"body {DIRT} (grass, soil) / {STONE} (stone); fill tile = frame 0's bottom 8 px (groundstrip cuts it); {footnote}", 6, 28)
    rows.append(foot)
    review.write(out, np.vstack(rows))
    fakegp.restore()
    print("written", out, "within", {k: round(v, 2) for k, v in within.items()}, "across", across, json.dumps(KEYS))


if __name__ == "__main__":
    main(sys.argv[1])
