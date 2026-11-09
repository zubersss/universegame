"""RETIRED 2026-11-08 (B-215, U-186 9694c4c8: a smooth planet loads only its first strip): the key was removed from Art/ and its
manifest row dropped; kept for reference only.

D-143 (LEAD): the Mars polar cap's top tile, terrain/mars/ground_strip_frost: CO2 frost over ice, on the accepted B-130
recipe and contract (8 frames 64x152, the same pivot and ground line as terrain/mars/ground_strip, the silhouette ON the line
at both edges, paper grain), in the Mars palette (D-125), palette colours and their own tones only. The recipe's mid-tone band
under the top becomes the white frost lip; the body is the cap's ice (the Mars teal), blocks and cracks, frost patches on
top. Its own module and row, so the exported regolith / basalt set stays byte-identical. UNITY draws it on snow and ice tops
the moment the key is addressed (it probes the key and uses the regolith until then).

  python -I build_c2_mars_frost.py <preview png>
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_c2_ground_strip as GS  # noqa: E402
from meridian import v3  # noqa: E402

G = GS.G
MP = v3.PALETTES["mars"]
KEYS = {"frost": "terrain/mars/ground_strip_frost"}


def mats(gp):
    sh = lambda h: v3.shadow_of(h, "mars")   # noqa: E731
    return {
        "dirt": G.mat(gp, "mf_ice", fill=MP["teal"], ink=False),                 # the frame recipe's body for an unknown kind
        "dirt_sh": G.mat(gp, "mf_frost_lip", fill=MP["offwhite"], ink=False),      # the band under the top: the frost lip
        "dirt_dp": G.mat(gp, "mf_ice_deep", fill=sh(MP["teal"]), ink=False),
        "stone_dp": G.mat(gp, "mf_pit", fill=sh(MP["teal"]), ink=False),
        "pebble": G.mat(gp, "mf_pebble", fill=sh(MP["offwhite"])),
        "lichen": G.mat(gp, "mf_frost", fill=MP["offwhite"]),                      # frost patches on the top
        "ink": G.mat(gp, "mf_ink", fill=None, ink=True),
    }


def sheets():
    return GS.sheets(tuple(KEYS), mats, grain={"frost": 0.02})   # a bright top: the sand's grain


def export(art, S=None):
    """terrain/mars/ground_strip_frost colour + json in the B-130 contract; raises on a failed check."""
    return GS.export(art, S if S is not None else sheets()[0], keys=KEYS)


def main(out, S=None, allw=None, footnote="preview (not exported)"):
    """The review: the frost frames at 3x, a 1x run of regolith | frost | regolith (the cap's edge) beside the surveyor."""
    import numpy as np
    sys.path.insert(0, os.path.dirname(HERE))
    import review
    import build_c2_mars_ground as MG
    import preview_c2_earth_rigs as PR
    if S is None:
        S, allw = sheets()
    within, across, problems = GS.checks(S)
    R, _w = MG.sheets()
    W = 1500
    head = np.tile(review.PAPER, (28, W, 1)).astype(np.float32)
    review._label(head, "d-143 terrain/mars/ground_strip_frost (the polar cap: co2 frost over ice; the b-130 contract, the regolith strip's frame + ground line)", 6, 8)
    bg = np.array(v3.hex_rgb(MP["sky"]), np.float32) / 255
    r = np.tile(bg, (GS.FH * 3 + 26, W, 1))
    for j, im in enumerate(S["frost"][:6]):
        review._over(r, np.repeat(np.repeat(im, 3, 0), 3, 1), 8 + j * (GS.FW * 3 + 4), 22)
    review._label(r, "frost frames 0-5 at 3x", 8, 4)
    scene = np.tile(bg, (300, W, 1))
    base = 240
    rnd = np.random.default_rng(5)
    for c in range(W // 64):
        kind, src = (("frost", S) if 7 <= c < 15 else ("regolith", R))
        im = src[kind][int(rnd.integers(0, 8))]
        y0 = base - (GS.FH - int(round(GS.SURF * 64)))
        review._over(scene, im[:max(0, min(GS.FH, 300 - y0))], c * 64, y0)
    try:
        fr, piv = PR.surveyor_frame()
        review._over(scene, fr, 10 * 64, base - fr.shape[0] + int(round(piv[1] * fr.shape[0])))
    except Exception:  # noqa: BLE001
        pass
    review._label(scene, "1x: regolith | the frost cap | regolith (the same ground line), the surveyor on the cap", 6, 6)
    hits, _o = v3.palette_hits(np.concatenate(S["frost"], axis=1), "mars")
    outer = [w for w in allw if w[0] >= v3.OUTER_SPLIT]
    inner = [w for w in allw if w[0] < v3.OUTER_SPLIT]
    foot = np.tile(review.PAPER, (40, W, 1)).astype(np.float32)
    review._label(foot, f"joins {', '.join(f'{k} {v:.2f}' for k, v in within.items())} /255; silhouette {across}; problems {problems or 'none'}; "
                        f"ink {min(w[1] for w in outer):.1f}-{max(w[2] for w in outer):.1f} / {min(w[1] for w in inner):.1f}-{max(w[2] for w in inner):.1f} px; "
                        f"mars palette {hits * 100:.1f}%", 6, 8)
    img = np.vstack([head, r, scene, foot])
    review._label(img, __import__("time").strftime("%m-%d %H:%M") + " " + footnote, 2, img.shape[0] - 16)
    review.write(out, img)
    print("written", out, "| joins", {k: round(v, 2) for k, v in within.items()}, "|", across, f"| palette {hits * 100:.1f}%", "| problems", problems or "-")


if __name__ == "__main__":
    main(sys.argv[1])
