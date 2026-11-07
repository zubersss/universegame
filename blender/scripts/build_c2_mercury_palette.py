"""B-145 (C2 Mercury design prep): the proposed Mercury palette strip and its check against Bible §9.1 (muted, slightly
aged; one 6-8 colour palette per planet) and §7.3 Mercury ("pitch-black sky with a huge Sun, blinding regolith, violet
twilight"). Same slot names and order as Earth's and Mars' strips (v3.PALETTE_ORDER), so gp_draw's shadow_of / deep_of
(70 / 45 % colour + the planet's "brown" slot) and palette_hits work unchanged once LEAD accepts it into
meridian.v3.PALETTES. The Mars checks (build_c2_mars_palette) plus Mercury's family: a violet twilight, a cool night slate.

  python -I build_c2_mercury_palette.py         prints the check table (markdown); numpy only, no image
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import v3  # noqa: E402
from build_c2_mars_palette import chroma, contrast, lab  # noqa: E402

MERCURY = {                    # slot: (hex, role)
    "offwhite": ("#E9E2D4", "blinding regolith: the sunlit ground, glare highlights, frost in the cold traps"),
    "red": ("#A85A41", "ember: flare-scorched rock, heat-side plants, the Cinderhulk's hot seams"),
    "mustard": ("#D8B566", "sun gold: the huge Sun, Solarite crystals, glare on metal"),
    "teal": ("#5E8B91", "cold steel teal: polar-crater ice, shadow-side plants, the one cool accent"),
    "green": ("#8B9471", "dusty sage: Mercury plants (readable on the regolith, the twilight and the night)"),
    "sky": ("#8D7AA0", "violet twilight: the terminator band, far crater rims at dusk"),
    "brown": ("#3E3848", "night slate: the shadow colour every mid / deep tone mixes toward; the night side"),
    "ink": (v3.INK, "ink, shared (also the pitch-black day sky)"),
}


def hue(h):
    L, a, b = lab(h)
    return float(np.degrees(np.arctan2(b, a)) % 360)


def check():
    pal = {k: h for k, (h, _r) in MERCURY.items()}
    v3.PALETTES.setdefault("mercury", pal)                    # for shadow_of / deep_of with planet="mercury"
    rows = ["| slot | hex | role | mid | deep | contrast vs ink | chroma |", "|---|---|---|---|---|---|---|"]
    for k in v3.PALETTE_ORDER:
        h, role = MERCURY[k]
        mid = v3.shadow_of(h, "mercury") if k != "ink" else "-"
        deep = v3.deep_of(h, "mercury") if k != "ink" else "-"
        rows.append(f"| {k} | {h} | {role} | {mid} | {deep} | {contrast(h, v3.INK):.1f} | {chroma(h):.0f} |")
    names = [k for k in v3.PALETTE_ORDER if k != "ink"]
    emax = max(chroma(v3.PALETTES["earth"][k]) for k in names)
    d = min((float(np.linalg.norm(lab(pal[a]) - lab(pal[b]))), a, b) for i, a in enumerate(names) for b in names[i + 1:])
    plant = min(float(np.linalg.norm(lab(pal["green"]) - lab(pal[k]))) for k in ("offwhite", "sky", "brown"))
    checks = [
        ("every colour reads under the ink (contrast >= 2.0; the night slate is exempt: it is only a tone and the night side)",
         all(contrast(pal[k], v3.INK) >= 2.0 for k in names if k != "brown")),
        (f"muted: no colour more saturated than Earth's most saturated accepted colour (chroma <= {emax:.0f}; Mercury max "
         f"{max(chroma(pal[k]) for k in names):.0f})", all(chroma(pal[k]) <= emax for k in names)),
        (f"distinct (closest pair {d[1]} / {d[2]} at dE {d[0]:.0f}, >= 12)", d[0] >= 12),
        (f"plants (dusty sage) read on the blinding regolith, the violet twilight and the night slate (dE >= 20; min {plant:.0f})", plant >= 20),
        (f"the twilight is violet (hue 280-330 deg; {hue(pal['sky']):.0f}) and the regolith is near neutral (chroma <= 12; "
         f"{chroma(pal['offwhite']):.0f})", 280 <= hue(pal["sky"]) <= 330 and chroma(pal["offwhite"]) <= 12),
        ("cool family: the night slate is dark and cool (L < 30, hue 260-330 deg)",
         lab(pal["brown"])[0] < 30 and 260 <= hue(pal["brown"]) <= 330),
        ("the shadow tones stay inside the family (deep tones never black: L > 20)",
         all(lab(v3.deep_of(pal[k], "mercury"))[0] > 20 for k in names)),
    ]
    rows += ["", "| check | result |", "|---|---|"] + [f"| {t} | {'pass' if ok else 'FAIL'} |" for t, ok in checks]
    return "\n".join(rows), all(ok for _t, ok in checks)


if __name__ == "__main__":
    text, ok = check()
    print(text)
    print("ALL PASS" if ok else "SOME FAIL")
