"""B-153 (C2 Venus export readiness; the accepted B-147 designs): the Venus ground strips on the accepted B-130 contract
(8 frames 64x152 per material, pivot on the ground line, the silhouette ON the line at both edges so any frame joins any
frame, paper grain), in the Venus palette (D-134), palette colours and their own tones only (a mix would miss the palette
check); the basalt brown never touches a frame edge (it is within B-139's 40-level ink tolerance, so the edge-row check would read it as ink):

  terrain/venus/ground_strip       the surface: the basalt crust (the B-130 stone recipe in Venus tones: a dark glassy
                                   basalt body, sulphur crust on the top, vent-orange pits, sea-glass glints)
  terrain/venus/ground_strip_deck  the cloud deck: the aerostat's planks seen edge-on (a plank band, a brass fascia beam with
                                   rivets, an X-braced truss under it, a short rail post every fourth frame) - a new kind
                                   drawn here; the silhouette is the flat deck line, so it joins the basalt's edge rows

  python -I build_c2_venus_ground.py <preview dir>
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_ground_strip as GS  # noqa: E402
from meridian import v3  # noqa: E402

G = GS.G
VP = v3.PALETTES["venus"]
O, I = G.OUTER, G.INNER
SURF, LIP, EDGE, FW, FH = GS.SURF, GS.LIP, GS.EDGE, GS.FW, GS.FH
KEYS = {"basalt": "terrain/venus/ground_strip", "planks": "terrain/venus/ground_strip_deck"}


def SH(h):
    return v3.shadow_of(h, "venus")


def DP(h):
    return v3.deep_of(h, "venus")


def mats(gp):
    return {
        "stone": G.mat(gp, "v_basalt", fill=DP(VP["teal"]), ink=False),           # glassy basalt with a sea-glass sheen
        "stone_sh": G.mat(gp, "v_basalt_mid", fill=DP(VP["red"]), ink=False),       # vent-lit from below (never the brown at an edge)
        "stone_dp": G.mat(gp, "v_basalt_pit", fill=VP["brown"], ink=False),           # interior pits only (the brown is ink-close)
        "pebble": G.mat(gp, "v_glass", fill=VP["teal"]),                           # Vitriol Glass glints
        "lichen": G.mat(gp, "v_sulphur", fill=VP["mustard"]),                      # the sulphur crust
        "deck": G.mat(gp, "v_deck", fill=DP(VP["mustard"]), ink=False),           # the under-deck
        "deck_sh": G.mat(gp, "v_deck_mid", fill=DP(VP["red"]), ink=False),
        "plank": G.mat(gp, "v_plank", fill=SH(VP["mustard"]), ink=False),
        "beam": G.mat(gp, "v_beam", fill=VP["mustard"], ink=False),
        "brace": G.mat(gp, "v_brace", fill=SH(VP["mustard"]), ink=False),
        "post": G.mat(gp, "v_post", fill=VP["mustard"]),
        "cap": G.mat(gp, "v_post_cap", fill=VP["teal"]),
        "ink": G.mat(gp, "v_ink", fill=None, ink=True),
    }


def deck_top(k, n=33):
    """The deck line: flat on the ground line, a hair of sag between the frame's edges (windowed to 0 at both)."""
    xs = [-0.5 + i / (n - 1) for i in range(n)]
    return [(x, SURF + LIP - 0.006 * GS.win(x)) for x in xs]


def planks_frame(d, M, k):
    """One deck frame: the body, the plank band, the brass fascia beam, the truss, a post on k % 4 == 0; the silhouette last."""
    rnd = random.Random(4000 + 31 * k)
    L, R = -0.5, 0.5
    lo, hi = L + EDGE + 0.04, R - EDGE - 0.04
    top = deck_top(k)
    G.stroke(d, [(L, 0.0), (R, 0.0)] + top[::-1], M["deck"], 0.0, cyclic=True)            # the under-deck up to the line
    plank_lo = [(x, z - 0.16) for x, z in top]
    G.stroke(d, top + plank_lo[::-1], M["plank"], 0.0, cyclic=True)                       # the plank band
    beam_lo = [(x, z - 0.48) for x, z in top]
    G.stroke(d, plank_lo + beam_lo[::-1], M["beam"], 0.0, cyclic=True)                    # the fascia beam
    shade = [(x, z - 0.62) for x, z in top]
    G.stroke(d, beam_lo + shade[::-1], M["deck_sh"], 0.0, cyclic=True)                   # its shadow on the truss
    G.seam(d, [p for p in plank_lo if lo - 0.02 <= p[0] <= hi + 0.02], M["ink"])
    G.seam(d, [p for p in beam_lo if lo - 0.02 <= p[0] <= hi + 0.02], M["ink"])
    jx = rnd.uniform(lo + 0.1, hi - 0.1)                                                  # a plank butt joint
    G.seam(d, [(jx, SURF - 0.015), (jx, SURF - 0.15)], M["ink"])
    for x in (lo + 0.05, hi - 0.05):                                                      # rivets on the beam
        for z in (SURF - 0.24, SURF - 0.40):
            G.stroke(d, G.lumpy_ellipse(x, z, 0.014, 0.014, n=8, lump=0.05, seed=k * 4 + int(z * 10)), M["ink"], I, cyclic=True)
    zt, zb = SURF - 0.66, SURF - 1.62                                                     # the truss: two struts and an X brace
    for x in (lo + 0.03, hi - 0.03):
        G.stroke(d, [(x - 0.025, zb), (x + 0.025, zb), (x + 0.025, zt), (x - 0.025, zt)], M["brace"], 0.0, cyclic=True)
        G.seam(d, [(x + 0.025, zb), (x + 0.025, zt)], M["ink"])
    for a, b in (((lo + 0.06, zt - 0.03), (hi - 0.06, zb + 0.03)), ((lo + 0.06, zb + 0.03), (hi - 0.06, zt - 0.03))):
        nx, nz = b[1] - a[1], a[0] - b[0]
        ln = (nx * nx + nz * nz) ** 0.5
        nx, nz = 0.02 * nx / ln, 0.02 * nz / ln
        G.stroke(d, [(a[0] - nx, a[1] - nz), (b[0] - nx, b[1] - nz), (b[0] + nx, b[1] + nz), (a[0] + nx, a[1] + nz)], M["brace"], 0.0, cyclic=True)
        G.seam(d, [(a[0] + nx, a[1] + nz), (b[0] + nx, b[1] + nz)], M["ink"])
    G.hatch(d, rnd.uniform(lo + 0.1, hi - 0.1), SURF - 1.8, M["ink"], n=3, length=0.09, spacing=0.03, angle_deg=rnd.choice((15, 165)), seed=k)
    G.specks(d, [(rnd.uniform(lo, hi), rnd.uniform(0.2, SURF - 0.7)) for _ in range(3)], M["ink"])
    if k % 4 == 0:                                                                        # a short rail post on the deck
        px = rnd.uniform(-0.12, 0.12)
        post = [(px - 0.03, SURF - 0.01), (px + 0.03, SURF - 0.01), (px + 0.028, SURF + 0.26), (px - 0.028, SURF + 0.26)]
        G.stroke(d, post, M["post"], O, cyclic=True)
        G.stroke(d, G.lumpy_ellipse(px, SURF + 0.28, 0.04, 0.025, n=10, lump=0.06, seed=k + 9), M["cap"], I, cyclic=True)
    G.stroke(d, top, M["ink"], O)                                                         # the silhouette, outer weight (last)


def frame(d, M, kind, k):
    if kind == "planks":
        planks_frame(d, M, k)
    else:
        GS.frame(d, M, kind, k)                                                           # basalt: the B-130 stone recipe


def sheets(kinds=None):
    """{kind: [8 frames]} and the measured ink widths (GS.sheets' loop with this module's frame for the planks)."""
    import numpy as np
    from meridian import fakegp
    out, allw = {}, []
    for kind in (kinds or KEYS):
        gp = fakegp.FakeGP()
        M = mats(gp)
        frames = []
        for k in range(8):
            d = fakegp.FakeDrawing()
            frame(d, M, kind, k)
            st = fakegp.strokes_of(d, gp)
            GS.steady_ends(st[-1], seed=k + 1)          # the silhouette is the last stroke
            img, w = GS.GR.render_frame(st, FW, FH, 64, (0.5, 0.0), ss=4, seed=k + 1)
            rgb = np.clip(img[..., :3].astype(np.float32) * GS.paper_grain(k, 0.035)[..., None], 0, 255)
            frames.append(np.dstack([np.rint(rgb).astype(np.uint8), img[..., 3]]))
            allw += w
        out[kind] = frames
    return out, allw


def export(art, S=None):
    """B-153: terrain/venus/ground_strip (+ _deck) colour + json in the B-130 contract; raises on a failed check."""
    return GS.export(art, S if S is not None else sheets()[0], keys=KEYS)


def main(out, S=None, allw=None, footnote="sources + preview"):
    """render.py's review hook: the B-139 layout written to `out`."""
    return preview(os.path.dirname(out), out=out, S=S, allw=allw, footnote=footnote)


def preview(out_dir, out=None, S=None, allw=None, footnote=None):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_c2_venus_plants as VPL
    import preview_c2_earth_rigs as PR
    if S is None:
        S, allw = sheets()
    within, across, problems = GS.checks(S)
    W = 1700
    rows = []
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, "b-153 venus ground strips (the b-130 contract in the venus palette): the basalt crust (the surface) and the aerostat deck planks (the cloud deck)", 6, 8)
    rows.append(head)
    r = np.tile(np.array(v3.hex_rgb(VP["sky"]), np.float32) / 255, (GS.FH * 3 + 26, W, 1))
    x = 8
    for kind in KEYS:
        review._label(r, f"{KEYS[kind]} ({kind}) frames 0-3 at 3x", x, 4)
        for j, im in enumerate(S[kind][:4]):
            review._over(r, np.repeat(np.repeat(im, 3, 0), 3, 1), x + j * (GS.FW * 3 + 4), 22)
        x += 4 * (GS.FW * 3 + 4) + 40
    rows.append(r)
    scene, _g = VPL.venus_strip(W, 420)
    base = 420 - 60                                                     # the ground line in the scene
    rnd = np.random.default_rng(5)
    kinds = ["planks"] * (W // 64 // 2) + ["basalt"] * (W // 64 - W // 64 // 2)
    for c, kind in enumerate(kinds):
        im = S[kind][c % 8 if kind == "planks" else int(rnd.integers(0, 8))]
        y0 = base - (GS.FH - int(round(GS.SURF * 64)))
        review._over(scene, im[:max(0, min(GS.FH, 420 - y0))], c * 64, y0)
    x = 40
    for name in VPL.PLANTS:
        img, _w = VPL.render(name, VPL.poses(name)[0][0])
        review._over(scene, img, x, base - VPL.FH)
        x += VPL.FW + 30
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, x + 20, base - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, "1x: the deck planks (left half; posts every 4 m) and the basalt crust (right half) under the five venus plants and the surveyor", 6, 6)
    rows.append(scene)
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    hits = {k: v3.palette_hits(np.concatenate(S[k], axis=1), "venus")[0] for k in KEYS}
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"joins {', '.join(f'{k} {v:.2f}' for k, v in within.items())} /255; silhouette {across}; problems {problems or 'none'}", 6, 8)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; venus palette {', '.join(f'{k} {v * 100:.1f}%' for k, v in hits.items())}; keys {', '.join(KEYS.values())}", 6, 28)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " " + (footnote or "preview (not exported)"), 2, img.shape[0] - 16)
    out = out or os.path.join(out_dir, "review_b153_venus_ground_preview.png")
    review.write(out, img)
    print("written", out, "| joins", {k: round(v, 2) for k, v in within.items()}, "|", across, "| palette",
          {k: round(v * 100, 1) for k, v in hits.items()}, "| problems", problems or "-")


if __name__ == "__main__":
    preview(sys.argv[1])
