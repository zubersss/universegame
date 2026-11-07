"""B-148 (C2 Mercury export readiness; the accepted B-145 designs): the Mercury ground strips on the accepted B-130 recipe
and contract (8 frames 64x152 per material, pivot on the ground line, the silhouette ON the line at both edges so any frame
joins any frame, paper grain), in the Mercury palette (D-130), palette colours and their own tones only (a mix would miss the
palette check): terrain/mercury/ground_strip (the blinding white regolith: Earth's soil recipe without the worm burrows)
and terrain/mercury/ground_strip_slate (the slate shadow side: the stone recipe in the twilight violet's mid / deep tones,
teal ice glints for lichen).

  python -I build_c2_mercury_ground.py <preview dir>
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_ground_strip as GS  # noqa: E402
from meridian import v3  # noqa: E402

G = GS.G
MP = v3.PALETTES["mercury"]
KEYS = {"regolith": "terrain/mercury/ground_strip", "basalt": "terrain/mercury/ground_strip_slate"}


def mats(gp):
    sh = lambda h: v3.shadow_of(h, "mercury")   # noqa: E731
    dp = lambda h: v3.deep_of(h, "mercury")     # noqa: E731
    return {
        "dirt": G.mat(gp, "me_regolith", fill=MP["offwhite"], ink=False),
        "dirt_sh": G.mat(gp, "me_regolith_mid", fill=sh(MP["offwhite"]), ink=False),
        "dirt_dp": G.mat(gp, "me_regolith_deep", fill=dp(MP["offwhite"]), ink=False),
        "stone": G.mat(gp, "me_slate", fill=sh(MP["sky"]), ink=False),
        "stone_sh": G.mat(gp, "me_slate_mid", fill=dp(MP["sky"]), ink=False),
        "stone_dp": G.mat(gp, "me_slate_deep", fill=MP["brown"], ink=False),
        "pebble": G.mat(gp, "me_pebble", fill=sh(MP["offwhite"])),
        "lichen": G.mat(gp, "me_ice", fill=MP["teal"]),
        "ink": G.mat(gp, "me_ink", fill=None, ink=True),
    }


def sheets():
    """{kind: [8 frames]} for regolith + the slate side and the measured ink widths (B-130's recipe, Mercury materials)."""
    return GS.sheets(tuple(KEYS), mats, grain={"regolith": 0.02})   # the white regolith: the sand's grain (its joins at 0.035 were 1.33/255)


def export(art, S=None):
    """B-148: terrain/mercury/ground_strip (+ _slate) colour + json in the B-130 contract; raises on a failed check."""
    return GS.export(art, S if S is not None else sheets()[0], keys=KEYS)


def main(out, S=None, allw=None, footnote="sources + preview"):
    """render.py's review hook: the B-139 layout written to `out`."""
    return preview(os.path.dirname(out), out=out, S=S, allw=allw, footnote=footnote)


def preview(out_dir, out=None, S=None, allw=None, footnote=None):
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_c2_mercury_plants as MPL
    import preview_c2_earth_rigs as PR
    if S is None:
        S, allw = sheets()
    within, across, problems = GS.checks(S)
    W = 1700
    rows = []
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, "b-148 mercury ground strips (the b-130 contract and recipe in the mercury palette): white regolith (no burrows) and the slate shadow side", 6, 8)
    rows.append(head)
    r = np.tile(np.array([0.62, 0.72, 0.72], np.float32), (GS.FH * 3 + 26, W, 1))
    x = 8
    for kind in KEYS:
        review._label(r, f"{KEYS[kind]} ({kind}) 8 frames at 3x", x, 4)
        for j, im in enumerate(S[kind][:4]):
            review._over(r, np.repeat(np.repeat(im, 3, 0), 3, 1), x + j * (GS.FW * 3 + 4), 22)
        x += 4 * (GS.FW * 3 + 4) + 40
    rows.append(r)
    scene, _g = MPL.mercury_strip(W, 420)
    base = 420 - 60                                                     # the ground line in the scene
    rnd = np.random.default_rng(5)
    kinds = ["regolith"] * (W // 64)
    for c in range(9, 13):
        kinds[c] = "basalt"
    for c, kind in enumerate(kinds):
        im = S[kind][int(rnd.integers(0, 8))]
        y0 = base - (GS.FH - int(round(GS.SURF * 64)))
        review._over(scene, im[:max(0, min(GS.FH, 420 - y0))], c * 64, y0)
    x = 40
    for name in MPL.PLANTS:
        img, _w = MPL.render(name, MPL.poses(name)[0][0])
        review._over(scene, img, x, base - MPL.FH)
        x += MPL.FW + 30
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, x + 20, base - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, "1x: the mercury strips (a slate run in the middle) under the five mercury plants and the surveyor", 6, 6)
    rows.append(scene)
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    foot = np.tile(review.PAPER, (50, W, 1)).astype(np.float32)
    review._label(foot, f"joins {', '.join(f'{k} {v:.2f}' for k, v in within.items())} /255; silhouette {across}; problems {problems or 'none'}", 6, 8)
    review._label(foot, f"ink outer {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} px, interior {min(w[1] for w in inner):.1f}-"
                        f"{max(w[2] for w in inner):.1f} px; keys {', '.join(KEYS.values())} (export after lead accepts)", 6, 28)
    rows.append(foot)
    img = np.vstack(rows)
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " " + (footnote or "preview (not exported)"), 2, img.shape[0] - 16)
    out = out or os.path.join(out_dir, "review_b148_mercury_ground_preview.png")
    review.write(out, img)
    print("written", out, "| joins", {k: round(v, 2) for k, v in within.items()}, "|", across, "| problems", problems or "-")


if __name__ == "__main__":
    preview(sys.argv[1])
