"""B-161 (C2 Neptune design prep): Neptune's floe strips on D-137's contract (64x152 cells, pivot on the ground line, 8 tiles
+ cap_left + cap_right = 10 frames, the silhouette on the line at the tile edges, paper grain), in the Neptune palette (D-148).
Built on build_c2_uranus_floes' frame / cap / check / export code, with Neptune's wind (+x, D-148):

  terrain/neptune/floe_strip_ice         methane ice carved by the wind: a wisp-white rime lip over wind cyan, ridges with a
                                         steep windward face and a long lee taper, wind-streak seams; cap_left (the windward
                                         end) rounded, cap_right (the lee end) ragged and broken - its own drawing, not a mirror
  terrain/neptune/floe_strip_superionic  the Deep's black hot ice: the deep indigo under a thin storm-violet crust, faceted,
                                         violet glints (the resource reads at a glance; no emission map); chamfered caps

A -x wind mirrors the whole floe at runtime (each frame flipped, the caps swapped; D-148 / §9.6), never a second drawing.

  python -I build_c2_neptune_floes.py <preview dir>      lock-free design preview (fakegp + numpy); nothing exported
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
NP = v3.PALETTES["neptune"]
O, I = G.OUTER, G.INNER
SURF, LIP, EDGE, FW, FH = GS.SURF, GS.LIP, GS.EDGE, GS.FW, GS.FH
KEYS = {"ice": "terrain/neptune/floe_strip_ice", "superionic": "terrain/neptune/floe_strip_superionic"}
_SH = lambda h: v3.shadow_of(h, "neptune")   # noqa: E731
_DP = lambda h: v3.deep_of(h, "neptune")     # noqa: E731
TONES = {   # kind: (body, the mid band, deep) - palette colours and their own tones only
    "ice": (NP["teal"], _SH(NP["teal"]), _DP(NP["teal"])),                         # wind cyan under a wisp-white rime lip
    "superionic": (NP["brown"], _SH(NP["mustard"]), _DP(NP["mustard"])),           # the deep indigo, storm-violet tones
}
TILES, CAP_LEFT, CAP_RIGHT = 8, 8, 9
SIDE_X = -0.5 + EDGE + 0.05          # a cap's side wall (cap_left; cap_right mirrors the x)
CORNER = 0.34                        # the radius of the ice's rounded windward corner
CHAMFER = 0.22                       # the superionic caps' cut corner


def mats(gp):
    out = {"ink": G.mat(gp, "n_ink", fill=None, ink=True), "wisp": G.mat(gp, "n_wisp", fill=NP["offwhite"], ink=False),
           "wisp_i": G.mat(gp, "n_wisp_inked", fill=NP["offwhite"]), "violet": G.mat(gp, "n_violet", fill=NP["mustard"], ink=False),
           "violet_i": G.mat(gp, "n_violet_inked", fill=NP["mustard"]),
           "violet_ln": G.mat(gp, "n_violet_line", fill=None, ink_hex=NP["mustard"]),
           "wisp_ln": G.mat(gp, "n_wisp_line", fill=None, ink_hex=NP["offwhite"]),
           "cyan_ln": G.mat(gp, "n_cyan_line", fill=None, ink_hex=_DP(NP["teal"]))}
    for kind, (body, mid, deep) in TONES.items():
        out[kind] = G.mat(gp, f"n_{kind}", fill=body, ink=False)
        out[kind + "_sh"] = G.mat(gp, f"n_{kind}_mid", fill=mid, ink=False)
        out[kind + "_dp"] = G.mat(gp, f"n_{kind}_deep", fill=deep, ink=False)
    return out


def win(x, L=-0.5, R=0.5):
    return GS.win(x, L, R)


def top_line(kind, k, L=-0.5, R=0.5, n=33):
    """The floe's top between L and R: on the ground line at both ends (windowed), a kind's own texture between."""
    rnd = random.Random(9300 + 13 * k + 7 * len(kind))
    xs = [L + (R - L) * i / (n - 1) for i in range(n)]
    if kind == "ice":                                                          # wind-carved: a steep face upwind, a long taper down
        ridges = [(rnd.uniform(L + 0.15, R - 0.35), rnd.uniform(0.055, 0.08)) for _ in range(2)]

        def h(x):
            v = 0.0
            for c, a in ridges:
                if c - 0.05 <= x <= c:
                    v = max(v, a * (x - (c - 0.05)) / 0.05)                    # the windward face (left of the crest)
                elif c < x <= c + 0.3:
                    v = max(v, a * (1 - (x - c) / 0.3) ** 1.5)                 # the lee taper (downwind, +x)
            return v
        return [(x, SURF + LIP + win(x, L, R) * (h(x) - 0.008)) for x in xs]
    facets = sorted(rnd.uniform(L + 0.12, R - 0.12) for _ in range(3))           # superionic: flat crystal facets
    def fz(x):
        j = sum(1 for f in facets if x > f)
        return [0.0, 0.022, 0.008, 0.028][j]
    return [(x, SURF + LIP + win(x, L, R) * (fz(x) - 0.006)) for x in xs]


def cap_silhouette(kind, k):
    """cap_left's line from the side wall's foot, up the wall, round (ice) or cut (superionic) the corner, along the top to
    the inner edge."""
    if kind == "ice":
        wall = [(SIDE_X, z) for z in (0.0, 0.5, 1.0, SURF - CORNER)]
        corner = [(SIDE_X + CORNER - CORNER * math.cos(a), SURF - CORNER + CORNER * math.sin(a)) for a in [math.pi / 2 * j / 8 for j in range(1, 9)]]
        top = top_line(kind, k, SIDE_X + CORNER, 0.5, n=24)[1:]
        return wall + corner + top
    wall = [(SIDE_X + 0.03, 0.0), (SIDE_X, 0.6), (SIDE_X + 0.02, SURF - CHAMFER)]
    top = top_line(kind, k, SIDE_X + CHAMFER, 0.5, n=24)
    return wall + top


def lee_silhouette(k):
    """The ice's lee end (drawn as a cap_left that gets mirrored): the top runs out to a broken, ragged wall - wind-snapped
    shards stepping down, nothing rounded."""
    rnd = random.Random(9500 + k)
    steps = [(SIDE_X + 0.10, SURF), (SIDE_X + 0.04, SURF - 0.10), (SIDE_X + 0.09, SURF - 0.18), (SIDE_X + 0.01, SURF - 0.33),
             (SIDE_X + 0.07, SURF - 0.47), (SIDE_X - 0.01, SURF - 0.66), (SIDE_X + 0.05, 0.9), (SIDE_X + 0.0, 0.55),
             (SIDE_X + 0.04, 0.25), (SIDE_X + 0.01, 0.0)]
    wall = [(x + rnd.uniform(-0.006, 0.006), z) for x, z in steps[::-1]]
    top = top_line("ice", k, SIDE_X + 0.10, 0.5, n=24)[1:]
    return wall + top


def detail(d, M, kind, k, top, L, R):
    """Interior detail between L and R (kept clear of the tile edges by EDGE), under the top line."""
    rnd = random.Random(2200 + 31 * k + 7 * len(kind))
    lo, hi = L + EDGE + 0.06, R - EDGE - 0.06
    if kind == "ice":
        lip = [(x, z - 0.13 - 0.04 * win(x, L, R) * (0.5 + 0.5 * math.sin(9 * x + k))) for x, z in top]
        G.stroke(d, top + lip[::-1], M["wisp"], 0.0, cyclic=True)                         # the rime lip
        G.seam(d, [p for p in lip if win(p[0], L, R) > 0.2], M["ink"])
        for c in range(3):                                                                 # wind-streak seams, lying along +x
            x0 = rnd.uniform(lo, hi - 0.2)
            z0 = rnd.uniform(0.7, SURF - 0.35)
            G.stroke(d, [(x0, z0), (min(hi, x0 + rnd.uniform(0.12, 0.22)), z0 - 0.01)], M["cyan_ln"], I)
        x0 = min(hi - 0.1, rnd.uniform(lo, hi))                                            # one facet in the deep tone
        z0 = rnd.uniform(0.9, SURF - 0.35)
        G.stroke(d, [(x0, z0), (x0 + 0.1, z0 - 0.04), (x0 + 0.08, z0 - 0.22), (x0 - 0.01, z0 - 0.18)], M["ice_dp"], 0.0, cyclic=True)
        G.seam(d, [(x0, z0), (x0 - 0.01, z0 - 0.18)], M["ink"])
    else:                                                                                  # superionic: a violet crust, facets, glints
        crust = [(x, z - 0.06 - 0.015 * win(x, L, R) * (0.5 + 0.5 * math.sin(13 * x + k))) for x, z in top]
        G.stroke(d, top + crust[::-1], M["violet"], 0.0, cyclic=True)
        G.seam(d, [p_ for p_ in crust if win(p_[0], L, R) > 0.2], M["ink"])
        x0, z0 = rnd.uniform(lo, hi - 0.22), rnd.uniform(1.0, SURF - 0.3)                 # one large shard plane in the violet deep tone
        shard = [(x0, z0), (x0 + 0.22, z0 - 0.06), (x0 + 0.16, z0 - 0.42), (x0 + 0.02, z0 - 0.3)]
        G.stroke(d, shard, M["superionic_dp"], 0.0, cyclic=True)
        G.stroke(d, shard[:2], M["violet_ln"], I)
        for c in range(2):                                                                 # angular crack lines (the faceting)
            cx, cz = rnd.uniform(lo, hi - 0.15), rnd.uniform(0.45, SURF - 0.35)
            G.stroke(d, [(cx, cz), (cx + 0.06, cz + 0.07), (cx + 0.11, cz + 0.02), (min(hi, cx + 0.16), cz + 0.09)], M["violet_ln"], I)
        for c in range(2 + k % 2):                                                         # four-point glints
            gx, gz = rnd.uniform(lo, hi), rnd.uniform(0.5, SURF - 0.3)
            for ang in (0.0, math.pi / 2):
                G.stroke(d, [(gx - 0.03 * math.cos(ang), gz - 0.03 * math.sin(ang)), (gx + 0.03 * math.cos(ang), gz + 0.03 * math.sin(ang))],
                         M["wisp_ln" if c % 2 == 0 else "violet_ln"], I)
    band = [(x, z - 0.32 - 0.04 * win(x, L, R) * math.sin(9 * x + k)) for x, z in top]       # the mid tone under the top
    G.stroke(d, [(x, z - 0.24) for x, z in top] + band[::-1], M[kind + "_sh"], 0.0, cyclic=True)
    hx, hz = rnd.uniform(lo, hi), rnd.uniform(0.55, 1.1)
    G.hatch(d, hx, hz, M["violet_ln" if kind == "superionic" else "ink"], n=3, length=0.09, spacing=0.03, angle_deg=rnd.choice((15, 165)), seed=k)
    G.specks(d, [(rnd.uniform(lo, hi), rnd.uniform(0.45, SURF - 0.4)) for _ in range(3)], M["ink"])


def cap_frame(d, M, kind, k, sil, inner_from):
    """A cap drawn as cap_left (the outer end on the left): fill, the shaded side wall, the detail, the silhouette ink."""
    G.stroke(d, sil + [(0.5, 0.0)], M[kind], 0.0, cyclic=True)
    wall_shade = [(sil[0][0], 0.0)] + [p for p in sil if p[1] < SURF - 0.1][:6] + [(min(p[0] for p in sil) + 0.08, 0.0)]
    G.stroke(d, wall_shade, M[kind + "_dp"], 0.0, cyclic=True)                              # the side wall in shadow
    top = [p for p in sil if p[1] >= SURF - 0.02 and p[0] > inner_from]
    detail(d, M, kind, k, top, inner_from, 0.5)
    G.stroke(d, sil, M["ink"], O)


def frame(d, M, kind, k):
    """Tile k (0-7), cap_left (8) or cap_right (9). The ice's cap_right is the ragged lee end, mirrored onto the right; the
    superionic's cap_right mirrors its cap_left. The silhouette is the last stroke."""
    mirror = lambda dd: G.Xf(dd, lambda pts: [(-x, z) for x, z in pts])   # noqa: E731
    if k == CAP_RIGHT and kind == "ice":
        cap_frame(mirror(d), M, kind, k, lee_silhouette(k), SIDE_X + 0.12)
        return
    if k == CAP_RIGHT:
        frame(mirror(d), M, kind, CAP_LEFT)
        return
    if k == CAP_LEFT:
        inner = SIDE_X + (CORNER * 0.6 if kind == "ice" else CHAMFER * 0.6)
        cap_frame(d, M, kind, k, cap_silhouette(kind, k), inner)
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
    """terrain/neptune/floe_strip_<kind>_color.png (10 frames 64x152 in one row, 4 px gutters) + .json (the B-130 json +
    "caps" + "wind"). Raises on a failed check. For the Neptune card (not before)."""
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
                "wind": "+x",
                "note": "D-137: frames 0-7 tile (x mod 8), 8 = cap_left (the floe's first column, the windward end), 9 = cap_right "
                        "(its last, the lee end); pivot = the ground line; below it the fill = the column's frame's bottom 8 px. "
                        "D-148: drawn for a +x wind; a -x wind flips every frame and swaps the caps at runtime"}
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
    return out, dict(within, **{f"{k} caps": v for k, v in caps.items()}), across   # render.py's ground-strip row unpacks three


def floe(S, kind, n, rnd):
    """One floe image: cap_left + n tiles + cap_right, the bottom 30 rows fading out (the preview's hint of its underside)."""
    import numpy as np
    cols = [S[kind][CAP_LEFT]] + [S[kind][int(rnd.integers(0, TILES))] for _ in range(n)] + [S[kind][CAP_RIGHT]]
    img = np.concatenate(cols, axis=1).astype(np.float32)
    img[-30:, :, 3] *= np.linspace(1.0, 0.0, 30)[:, None]
    return img.astype(np.uint8)


def main(out, S=None, allw=None, footnote="sources + preview"):
    """render.py's review hook (the ground-strip row): the preview layout written to `out`."""
    return preview(os.path.dirname(out), S=S, allw=allw, out=out, footnote=footnote)


def preview(out_dir, S=None, allw=None, out=None, footnote=None):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_c2_neptune_plants as NPL
    import preview_c2_earth_rigs as PR
    if S is None:
        S, allw = sheets()
    within, across, caps, problems = checks(S)
    W = 1960
    rows = []
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, "b-161 neptune floe strips (d-137: 8 tiles + cap_left + cap_right; d-148: a +x wind): wind-carved methane ice (rounded windward, ragged lee), superionic ice", 6, 8)
    rows.append(head)
    rh = FH * 2 + 30
    r = np.tile(np.array(v3.hex_rgb(NP["sky"]), np.float32) / 255, (rh, W, 1))
    for i, kind in enumerate(KEYS):                                                       # two kinds a row (5 frames at 2x = 650 px)
        x = 8 + i * 720
        review._label(r, f"{kind}: cap_l, tiles 0-2, cap_r at 2x", x, 4)
        for j, k in enumerate((CAP_LEFT, 0, 1, 2, CAP_RIGHT)):
            review._over(r, np.repeat(np.repeat(S[kind][k], 2, 0), 2, 1), x + j * (FW * 2 + 2), 24)
    rows.append(r)
    H = 460
    sky, _g = NPL.neptune_strip(W, H + 60)
    scene = sky[:H].copy()
    rnd = np.random.default_rng(5)
    layout = (("ice", 6, 40, 380), ("superionic", 4, 760, 290), ("ice", 3, 1300, 400))
    bases = {}
    for j, (kind, n, x0, base) in enumerate(layout):
        img = floe(S, kind, n, rnd)
        y0 = base - (FH - int(round(SURF * 64)))
        review._over(scene, img[:max(0, min(FH, H - y0))], x0, y0)
        bases[(kind, j)] = (x0, base, (n + 2) * FW)
    bases["ice"], bases["superionic"] = bases[("ice", 0)], bases[("superionic", 1)]
    for name, kind, dx in (("kitebloom", "ice", 30), ("gripweed", "ice", 150), ("pipereed", "ice", 250), ("stormlantern", "superionic", 50),
                           ("rimecomb", "superionic", 190)):
        x0, base, _w = bases[kind]
        img, _w = NPL.render(name, NPL.poses(name)[0][0])
        review._over(scene, img, x0 + dx, base - NPL.FH)
    try:
        fr, piv = PR.surveyor_frame()
        x0, base, wd = bases["ice"]
        review._over(scene, fr, x0 + wd - 110, base - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, "1x: three floes (cap + n tiles + cap) in the column, the wind blowing +x, the five neptune flora and the surveyor on them", 6, 6)
    rows.append(scene)
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    hits = {k: v3.palette_hits(np.concatenate(S[k], axis=1), "neptune")[0] for k in KEYS}
    foot = np.tile(review.PAPER, (70, W, 1)).astype(np.float32)
    review._label(foot, f"tile joins {', '.join(f'{k} {v:.2f}' for k, v in within.items())} /255; silhouette {across}", 6, 8)
    review._label(foot, f"cap joins {', '.join(f'{k} {v:.2f}' for k, v in caps.items())} /255; problems {problems or 'none'}", 6, 28)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; neptune palette {', '.join(f'{k} {v * 100:.1f}%' for k, v in hits.items())}; nothing exported", 6, 48)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " " + (footnote or "preview (not exported)"), 2, img.shape[0] - 16)
    out = out or os.path.join(out_dir, "review_b161_neptune_floes_preview.png")
    review.write(out, img)
    print("written", out, "| tile joins", {k: round(v, 2) for k, v in within.items()}, "| caps", {k: round(v, 2) for k, v in caps.items()},
          "|", across, "| palette", {k: round(v * 100, 1) for k, v in hits.items()}, "| problems", problems or "-")


if __name__ == "__main__":
    preview(sys.argv[1])
