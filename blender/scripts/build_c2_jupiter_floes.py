"""B-155 (C2 Jupiter design prep; D-137): the giant's floe strips on the B-130 frame contract (64x152 cells, pivot on the
ground line, the silhouette ON the line at both tile edges so any tile joins any tile, paper grain) in the Jupiter palette
(D-137), plus the two cap frames D-137 rules for a giant's floes: 8 tiles + cap_left + cap_right = 10 frames, so a floe of
any length is cap_left + n tiles + cap_right. A cap's inner edge joins the tiles exactly; its outer end rounds over into a
vertical side wall, so the column fill below it (GroundStrip's cap placement is UNITY's U-126) continues that wall.

  terrain/jupiter/floe_strip_ice       ammonia ice: a cream frost lip over blue-tinged ice, facet seams, trapped bubbles
  terrain/jupiter/floe_strip_core      a hardened brick-and-umber core with festoon Metallic Hydrogen veins (tones, no
                                       emission; the Deep only)
  terrain/jupiter/floe_strip_derelict  the Meridian expedition's rust plating: plate seams, rivets, a worn cream livery stripe
  terrain/jupiter/floe_strip_spot      the Great Red Spot's brick phosphorus ice with swirl marks and cream specks

  python -I build_c2_jupiter_floes.py <preview dir>      lock-free design preview (fakegp + numpy); nothing exported
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_ground_strip as GS  # noqa: E402  (installs fakegp; the B-130 constants, grain, joins)
from meridian import v3  # noqa: E402

G = GS.G
JP = v3.PALETTES["jupiter"]
O, I = G.OUTER, G.INNER
SURF, LIP, EDGE, FW, FH = GS.SURF, GS.LIP, GS.EDGE, GS.FW, GS.FH
KEYS = {"ice": "terrain/jupiter/floe_strip_ice", "core": "terrain/jupiter/floe_strip_core",
        "derelict": "terrain/jupiter/floe_strip_derelict", "spot": "terrain/jupiter/floe_strip_spot"}
_SH = lambda h: v3.shadow_of(h, "jupiter")   # noqa: E731
_DP = lambda h: v3.deep_of(h, "jupiter")     # noqa: E731
TONES = {   # kind: (body, the mid band, deep) - palette colours and their own tones only (a mix would miss the palette check)
    "ice": (JP["teal"], _SH(JP["teal"]), _DP(JP["teal"])),                  # festoon blue-grey ice under a cream frost lip
    "core": (_SH(JP["red"]), _DP(JP["red"]), JP["brown"]),                  # hardened brick-and-umber
    "derelict": (JP["mustard"], _SH(JP["mustard"]), _DP(JP["mustard"])),    # rust plating
    "spot": (JP["red"], _SH(JP["red"]), _DP(JP["red"])),                    # Red Spot brick
}
TILES, CAP_LEFT, CAP_RIGHT = 8, 8, 9
SIDE_X = -0.5 + EDGE + 0.05          # a cap's side wall (cap_left; cap_right is its mirror)
CORNER = 0.34                        # the radius of the cap's rounded top corner


def mats(gp):
    sh = lambda h: v3.shadow_of(h, "jupiter")   # noqa: E731
    dp = lambda h: v3.deep_of(h, "jupiter")     # noqa: E731
    out = {"ink": G.mat(gp, "j_ink", fill=None, ink=True), "cream": G.mat(gp, "j_cream", fill=JP["offwhite"], ink=False),
           "cream_i": G.mat(gp, "j_cream_inked", fill=JP["offwhite"]), "festoon": G.mat(gp, "j_festoon", fill=JP["teal"], ink=False),
           "festoon_sh": G.mat(gp, "j_festoon_mid", fill=sh(JP["teal"]), ink=False), "umber": G.mat(gp, "j_umber", fill=JP["brown"], ink=False),
           "brick_dp": G.mat(gp, "j_brick_deep", fill=dp(JP["red"]), ink=False)}
    for kind, (body, mid, deep) in TONES.items():
        out[kind] = G.mat(gp, f"j_{kind}", fill=body, ink=False)
        out[kind + "_sh"] = G.mat(gp, f"j_{kind}_mid", fill=mid, ink=False)
        out[kind + "_dp"] = G.mat(gp, f"j_{kind}_deep", fill=deep, ink=False)
    return out


def win(x, L=-0.5, R=0.5):
    return GS.win(x, L, R)


def top_line(kind, k, L=-0.5, R=0.5, n=33):
    """The floe's top between L and R: on the ground line at both ends (windowed), a kind's own texture between."""
    rnd = random.Random(9100 + 13 * k + 7 * len(kind))
    xs = [L + (R - L) * i / (n - 1) for i in range(n)]
    if kind == "ice":                                                                    # low faceted ridges (piecewise)
        knots = sorted(rnd.uniform(L + 0.1, R - 0.1) for _ in range(3))
        return [(x, SURF + LIP + win(x, L, R) * (0.035 * min(abs(x - c) for c in knots) * -1 + 0.02)) for x in xs]
    if kind == "derelict":                                                               # flat plating with a dent
        c = rnd.uniform(L + 0.2, R - 0.2)
        return [(x, SURF + LIP - win(x, L, R) * 0.018 * math.exp(-((x - c) / 0.08) ** 2)) for x in xs]
    if kind == "spot":                                                                   # a soft swell
        f = 2 + k % 2
        return [(x, SURF + LIP + 0.022 * win(x, L, R) * math.sin(math.pi * (x - L) / (R - L) * f + k)) for x in xs]
    knobs = [(rnd.uniform(L + 0.2, R - 0.2), rnd.uniform(0.03, 0.06), rnd.uniform(0.08, 0.15)) for _ in range(2)]   # core: hard knobs
    return [(x, SURF + LIP + win(x, L, R) * (sum(h * math.exp(-((x - c) / w) ** 2) for c, h, w in knobs) - 0.01)) for x in xs]


def cap_silhouette(kind, k):
    """cap_left's line from the side wall's foot, up the wall, round the corner, along the top to the inner edge."""
    wall = [(SIDE_X, z) for z in (0.0, 0.5, 1.0, SURF - CORNER)]
    corner = [(SIDE_X + CORNER - CORNER * math.cos(a), SURF - CORNER + CORNER * math.sin(a)) for a in [math.pi / 2 * j / 8 for j in range(1, 9)]]
    top = top_line(kind, k, SIDE_X + CORNER, 0.5, n=24)[1:]
    return wall + corner + top


def detail(d, M, kind, k, top, L, R):
    """Interior detail between L and R (kept clear of the tile edges by EDGE), under the top line."""
    rnd = random.Random(2000 + 31 * k + 7 * len(kind))
    lo, hi = L + EDGE + 0.06, R - EDGE - 0.06

    def ztop(x):
        return min(z for xx, z in top if abs(xx - x) < 0.05) if any(abs(xx - x) < 0.05 for xx, _z in top) else SURF
    if kind == "ice":
        lip = [(x, z - 0.15 - 0.03 * win(x, L, R) * (0.5 + 0.5 * math.sin(11 * x + k))) for x, z in top]
        G.stroke(d, top + lip[::-1], M["cream"], 0.0, cyclic=True)                       # the frost lip
        G.seam(d, [p for p in lip if win(p[0], L, R) > 0.2], M["ink"])
        for c in range(2):                                                               # facet seams + a festoon facet
            x0 = rnd.uniform(lo, hi)
            z0 = rnd.uniform(0.9, SURF - 0.3)
            x1 = min(hi - 0.08, max(lo, x0 + rnd.uniform(-0.15, 0.15)))                 # kept inside the edge margin
            x0 = min(hi - 0.08, x0)
            pts = [(x0, z0), (x1, z0 - rnd.uniform(0.25, 0.4))]
            G.seam(d, pts, M["ink"])
            G.stroke(d, [pts[0], pts[1], (pts[1][0] + 0.08, pts[1][1] + 0.05), (pts[0][0] + 0.07, pts[0][1] - 0.02)], M["ice_dp"], 0.0, cyclic=True)
        for c in range(2 + k % 2):                                                       # trapped bubbles
            bx, bz, r = rnd.uniform(lo, hi), rnd.uniform(0.5, SURF - 0.3), rnd.uniform(0.02, 0.035)
            G.stroke(d, G.lumpy_ellipse(bx, bz, r, r, n=10, seed=k * 5 + c), M["cream_i"], I, cyclic=True)
    elif kind == "core":
        for c in range(1 + k % 2):                                                       # Metallic Hydrogen veins (tones)
            x0 = rnd.uniform(lo, hi)
            vein = [(min(hi, max(lo, x0 + 0.12 * math.sin(i * 0.9 + c))), SURF - 0.25 - 0.16 * i) for i in range(8)]
            G.stroke(d, G.hose_outline(vein, 0.03), M["festoon"], 0.0, cyclic=True)
            G.stroke(d, G.hose_outline(vein, 0.012), M["festoon_sh"], 0.0, cyclic=True)
            G.specks(d, [vein[2], vein[5]], M["cream_i"])
        for c in range(2):
            G.stroke(d, G.lumpy_ellipse(rnd.uniform(lo, hi), rnd.uniform(0.5, SURF - 0.4), 0.05, 0.03, n=12, seed=k * 3 + c), M["core_dp"], 0.0, cyclic=True)
    elif kind == "derelict":
        band = [(x, z - 0.16) for x, z in top]
        stripe = [(x, z - 0.24) for x, z in top]
        G.stroke(d, band + stripe[::-1], M["cream"], 0.0, cyclic=True)                   # the worn livery stripe
        for c in range(2):                                                               # wear patches on the stripe
            wx = rnd.uniform(lo, hi)
            G.stroke(d, G.lumpy_ellipse(wx, ztop(wx) - 0.2, 0.04, 0.03, n=10, lump=0.2, seed=k + c), M["derelict"], 0.0, cyclic=True)
        jx = (L + R) / 2 if R - L > 0.8 else (lo + hi) / 2                              # one plate joint per 1 m column
        G.seam(d, [(jx, SURF - 0.34), (jx + 0.004, 1.1), (jx, 0.25)], M["ink"])           # (a seam can't cross a tile edge: the joins)
        G.stroke(d, [(jx + 0.01, SURF - 0.34), (jx + 0.05, SURF - 0.34), (jx + 0.05, 0.25), (jx + 0.01, 0.25)], M["derelict_sh"], 0.0, cyclic=True)
        for side in (-0.06, 0.09):                                                       # rivet rows beside the joint
            G.specks(d, [(jx + side, z) for z in (SURF - 0.45, SURF - 0.75, 1.0, 0.7, 0.4)], M["ink"])
        G.stroke(d, G.lumpy_ellipse(rnd.uniform(lo, hi), 1.1, 0.07, 0.04, n=12, lump=0.15, seed=k + 60), M["derelict_dp"], 0.0, cyclic=True)   # a scorch
    else:                                                                                # spot: swirls and phosphor specks
        for c in range(2):
            cx, cz = rnd.uniform(lo + 0.05, hi - 0.05), rnd.uniform(0.7, SURF - 0.45)
            sw = [(cx + 0.11 * (1 - t) * math.cos(5.5 * t + c), cz + 0.07 * (1 - t) * math.sin(5.5 * t + c)) for t in [j / 12 for j in range(13)]]
            G.seam(d, sw, M["ink"])
            G.stroke(d, G.hose_outline(sw[:7], 0.012), M["brick_dp"], 0.0, cyclic=True)
        G.specks(d, [(rnd.uniform(lo, hi), rnd.uniform(0.5, SURF - 0.25)) for _ in range(3)], M["cream_i"])
    band = [(x, z - 0.32 - 0.04 * win(x, L, R) * math.sin(9 * x + k)) for x, z in top]     # the mid tone under the top
    G.stroke(d, [(x, z - 0.26) for x, z in top] + band[::-1], M[kind + "_sh"], 0.0, cyclic=True)
    hx, hz = rnd.uniform(lo, hi), rnd.uniform(0.55, 1.1)
    G.hatch(d, hx, hz, M["ink"], n=3, length=0.09, spacing=0.03, angle_deg=rnd.choice((15, 165)), seed=k)
    G.specks(d, [(rnd.uniform(lo, hi), rnd.uniform(0.45, SURF - 0.4)) for _ in range(3)], M["ink"])


def frame(d, M, kind, k):
    """Tile k (0-7), cap_left (8) or cap_right (9; drawn as cap_left mirrored). The silhouette is the last stroke."""
    if k == CAP_RIGHT:
        frame(G.Xf(d, lambda pts: [(-x, z) for x, z in pts]), M, kind, CAP_LEFT)
        return
    if k == CAP_LEFT:
        sil = cap_silhouette(kind, k)
        G.stroke(d, sil + [(0.5, 0.0)], M[kind], 0.0, cyclic=True)
        wall_shade = [(SIDE_X, 0.0), (SIDE_X, SURF - CORNER), (SIDE_X + 0.07, SURF - CORNER + 0.02), (SIDE_X + 0.07, 0.0)]
        G.stroke(d, wall_shade, M[kind + "_dp"], 0.0, cyclic=True)                       # the side wall in shadow
        top = [p for p in sil if p[1] >= SURF - 0.02 and p[0] > SIDE_X + CORNER * 0.5]
        detail(d, M, kind, k, top, SIDE_X + CORNER * 0.6, 0.5)
        G.stroke(d, sil, M["ink"], O)
        return
    top = top_line(kind, k)
    G.stroke(d, [(-0.5, 0.0), (0.5, 0.0)] + top[::-1], M[kind], 0.0, cyclic=True)
    detail(d, M, kind, k, top, -0.5, 0.5)
    G.stroke(d, top, M["ink"], O)


def sheets(kinds=None):
    """{kind: [10 frames HxWx4 uint8: 8 tiles, cap_left, cap_right]} and the measured ink widths."""
    import numpy as np
    from meridian import fakegp
    import gp_raster as GR
    out, allw = {}, []
    for kind in (kinds or KEYS):
        gp = fakegp.FakeGP()
        M = mats(gp)
        frames = []
        for k in range(TILES + 2):
            d = fakegp.FakeDrawing()
            frame(d, M, kind, k)
            st = fakegp.strokes_of(d, gp)
            GS.steady_ends(st[-1], seed=k + 1)
            img, w = GR.render_frame(st, FW, FH, 64, (0.5, 0.0), ss=4, seed=k + 1)
            rgb = np.clip(img[..., :3].astype(np.float32) * GS.paper_grain(k)[..., None], 0, 255)
            frames.append(np.dstack([np.rint(rgb).astype(np.uint8), img[..., 3]]))
            allw += w
        out[kind] = frames
    return out, allw


def checks(S):
    """The B-130 checks on the tiles + D-137's caps: each cap's inner edge joins every tile (<= 1/255) and carries the same
    silhouette ink rows; the caps' outer columns are clear (the floe ends inside its frame)."""
    tiles = {k: v[:TILES] for k, v in S.items()}
    within, across, problems = GS.checks(tiles)
    caps = {}
    for kind, fr in S.items():
        a = GS.edge_join([fr[CAP_LEFT]], fr[:TILES])
        b = GS.edge_join(fr[:TILES], [fr[CAP_RIGHT]])
        caps[kind] = max(a, b)
        if caps[kind] > 1.0:
            problems.append(f"{kind}: cap join {caps[kind]:.2f}/255 > 1")
        rows = GS.ink_rows(fr[0], 0)
        if GS.ink_rows(fr[CAP_LEFT], FW - 1) != rows or GS.ink_rows(fr[CAP_RIGHT], 0) != rows:
            problems.append(f"{kind}: a cap's inner silhouette ink differs from the tiles'")
        if fr[CAP_LEFT][:, :2, 3].any() or fr[CAP_RIGHT][:, -2:, 3].any():
            problems.append(f"{kind}: a cap's outer end touches the frame edge")
    return within, across, caps, problems


def export(art, S=None):
    """terrain/jupiter/floe_strip_<kind>_color.png (10 frames 64x152 in one row, 4 px gutters) + .json (the B-130 json +
    "caps"). Raises on a failed check. For the Jupiter card (not before)."""
    import json
    import numpy as np
    from meridian import pngio
    if S is None:
        S, _w = sheets()
    within, across, caps, problems = checks(S)
    if problems:
        raise ValueError("floe strips fail the checks: " + "; ".join(problems))
    out = []
    n_ = TILES + 2
    for kind, key in KEYS.items():
        W = n_ * FW + (n_ - 1) * GS.GUTTER
        sheet = np.zeros((FH, W, 4), np.uint8)
        for j, im in enumerate(S[kind]):
            sheet[:, j * (FW + GS.GUTTER):j * (FW + GS.GUTTER) + FW] = im
        meta = {"key": key, "style": "v3", "frame_width": FW, "frame_height": FH, "columns": n_, "gutter": GS.GUTTER, "frames": n_,
                "fps": 12, "pivot": [0.5, round(SURF * 64 / FH, 6)], "facing": "right", "ppu": 64, "tile": True, "animations": [],
                "ground_line_px": int(round(SURF * 64)), "material": f"floe_{kind}", "caps": {"cap_left": CAP_LEFT, "cap_right": CAP_RIGHT},
                "note": "D-137: frames 0-7 tile (x mod 8), 8 = cap_left (the floe's first column), 9 = cap_right (its last); pivot = "
                        "the ground line; below it the fill = the column's frame's bottom 8 px (a cap's continues its side wall, U-126)"}
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
    return out, within, across, caps


def floe(S, kind, n, rnd):
    """One floe image: cap_left + n tiles + cap_right, the bottom 30 rows fading out (the preview's hint of its underside)."""
    import numpy as np
    cols = [S[kind][CAP_LEFT]] + [S[kind][int(rnd.integers(0, TILES))] for _ in range(n)] + [S[kind][CAP_RIGHT]]
    img = np.concatenate(cols, axis=1).astype(np.float32)
    img[-30:, :, 3] *= np.linspace(1.0, 0.0, 30)[:, None]
    return img.astype(np.uint8)


def preview(out_dir, S=None, allw=None):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_c2_jupiter_plants as JPL
    import preview_c2_earth_rigs as PR
    if S is None:
        S, allw = sheets()
    within, across, caps, problems = checks(S)
    W = 1960
    rows = []
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, "b-155 jupiter floe strips (d-137: the b-130 frame contract, 8 tiles + cap_left + cap_right): ice, core, derelict, spot", 6, 8)
    rows.append(head)
    rh = FH * 2 + 30
    r = np.tile(np.array(v3.hex_rgb(JP["sky"]), np.float32) / 255, (2 * rh, W, 1))
    for i, kind in enumerate(KEYS):                                                       # two kinds a row (5 frames at 2x = 650 px)
        x, y = 8 + (i % 2) * 720, (i // 2) * rh
        review._label(r, f"{kind}: cap_l, tiles 0-2, cap_r at 2x", x, y + 4)
        for j, k in enumerate((CAP_LEFT, 0, 1, 2, CAP_RIGHT)):
            review._over(r, np.repeat(np.repeat(S[kind][k], 2, 0), 2, 1), x + j * (FW * 2 + 2), y + 24)
    rows.append(r)
    H = 460
    sky, _g = JPL.jupiter_strip(W, H + 60)
    scene = sky[:H].copy()
    rnd = np.random.default_rng(5)
    layout = (("ice", 6, 40, 380), ("spot", 3, 720, 250), ("core", 3, 1060, 400), ("derelict", 4, 1480, 300))
    bases = {}
    for kind, n, x0, base in layout:
        img = floe(S, kind, n, rnd)
        y0 = base - (FH - int(round(SURF * 64)))
        review._over(scene, img[:max(0, min(FH, H - y0))], x0, y0)
        bases[kind] = (x0, base, (n + 2) * FW)
    for name, kind, dx in (("frostrosette", "ice", 30), ("driftbulb", "ice", 130), ("bandstreamer", "ice", 230), ("phosphorcup", "spot", 60), ("stormreed", "core", 70)):
        x0, base, _w = bases[kind]
        img, _w = JPL.render(name, JPL.poses(name)[0][0])
        review._over(scene, img, x0 + dx, base - JPL.FH)
    try:
        fr, piv = PR.surveyor_frame()
        x0, base, wd = bases["ice"]
        review._over(scene, fr, x0 + wd - 110, base - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, "1x: four floes (cap + n tiles + cap) in the column, the five jupiter flora and the surveyor on them", 6, 6)
    rows.append(scene)
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    hits = {k: v3.palette_hits(np.concatenate(S[k], axis=1), "jupiter")[0] for k in KEYS}
    foot = np.tile(review.PAPER, (70, W, 1)).astype(np.float32)
    review._label(foot, f"tile joins {', '.join(f'{k} {v:.2f}' for k, v in within.items())} /255; silhouette {across}", 6, 8)
    review._label(foot, f"cap joins {', '.join(f'{k} {v:.2f}' for k, v in caps.items())} /255; problems {problems or 'none'}", 6, 28)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; jupiter palette {', '.join(f'{k} {v * 100:.1f}%' for k, v in hits.items())}; nothing exported", 6, 48)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " preview (not exported)", 2, img.shape[0] - 16)
    out = os.path.join(out_dir, "review_b155_jupiter_floes_preview.png")
    review.write(out, img)
    print("written", out, "| tile joins", {k: round(v, 2) for k, v in within.items()}, "| caps", {k: round(v, 2) for k, v in caps.items()},
          "|", across, "| palette", {k: round(v * 100, 1) for k, v in hits.items()}, "| problems", problems or "-")


if __name__ == "__main__":
    preview(sys.argv[1])
