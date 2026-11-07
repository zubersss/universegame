"""B-155 (C2 Jupiter design prep): the proposed Jupiter palette strip and its check against Bible §9.1 (muted, slightly aged;
one 6-8 colour palette per planet) and §7.6 Jupiter ("cream, rust, and brick bands rolling past; lightning under the
floor; a sky that cycles every 8 minutes"). Same slot names and order as the other strips (v3.PALETTE_ORDER), so
gp_draw's tones and palette_hits work once LEAD accepts it into meridian.v3.PALETTES. The Mars checks
(build_c2_mars_palette) plus Jupiter's family: a cream zone, a rust belt and a brick Red Spot that stay apart, a cool
festoon blue-grey (the one cool accent: lightning glow tones, the deep water decks), a deep umber under the floor.
The first giant sets the cloud-column pattern Saturn, Uranus and Neptune reuse (their checks swap the family rows).

  python -I build_c2_jupiter_palette.py           prints the check table (markdown); numpy only, no image
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import v3  # noqa: E402
from build_c2_mars_palette import chroma, contrast, lab  # noqa: E402

JUPITER = {                    # slot: (hex, role)
    "offwhite": ("#EEE2CB", "ammonia cream: the zones, floe-ice tops, cloud-deck highlights, the aerostat canvas"),
    "red": ("#A8503A", "Red Spot brick: the Great Red Spot, phosphorus floes and blooms, warm accents"),
    "mustard": ("#C48A4E", "belt rust: the rust belts rolling past, rusted derelict plating, brass"),
    "teal": ("#6F8A97", "festoon blue-grey: lightning glow tones under the floor, the water decks, the one cool accent"),
    "green": ("#8F9A6A", "lichen sage: Jupiter flora (readable on the cream, the tan haze and the deep umber)"),
    "sky": ("#D8BC94", "zone tan: the deck sky between the bands, far cloud banks"),
    "brown": ("#4B3B34", "deep umber: the dark under the floor; the shadow colour every mid / deep tone mixes toward"),
    "ink": (v3.INK, "ink, shared"),
}


def hue(h):
    L, a, b = lab(h)
    return float(np.degrees(np.arctan2(b, a)) % 360)


def check():
    pal = {k: h for k, (h, _r) in JUPITER.items()}
    v3.PALETTES.setdefault("jupiter", pal)
    rows = ["| slot | hex | role | mid | deep | contrast vs ink | chroma |", "|---|---|---|---|---|---|---|"]
    for k in v3.PALETTE_ORDER:
        h, role = JUPITER[k]
        mid = v3.shadow_of(h, "jupiter") if k != "ink" else "-"
        deep = v3.deep_of(h, "jupiter") if k != "ink" else "-"
        rows.append(f"| {k} | {h} | {role} | {mid} | {deep} | {contrast(h, v3.INK):.1f} | {chroma(h):.0f} |")
    names = [k for k in v3.PALETTE_ORDER if k != "ink"]
    emax = max(chroma(v3.PALETTES["earth"][k]) for k in names)
    d = min((float(np.linalg.norm(lab(pal[a]) - lab(pal[b]))), a, b) for i, a in enumerate(names) for b in names[i + 1:])
    plant = min(float(np.linalg.norm(lab(pal["green"]) - lab(pal[k]))) for k in ("sky", "offwhite", "brown"))
    bands = float(np.linalg.norm(lab(pal["red"]) - lab(pal["mustard"])))
    checks = [
        ("every colour reads under the ink (contrast >= 2.0; the umber is exempt: it is only a tone and the dark under the floor)",
         all(contrast(pal[k], v3.INK) >= 2.0 for k in names if k != "brown")),
        (f"muted: no colour more saturated than Earth's most saturated accepted colour (chroma <= {emax:.0f}; Jupiter max "
         f"{max(chroma(pal[k]) for k in names):.0f})", all(chroma(pal[k]) <= emax for k in names)),
        (f"distinct (closest pair {d[1]} / {d[2]} at dE {d[0]:.0f}, >= 12)", d[0] >= 12),
        (f"plants (lichen sage) read on the zone tan, the cream and the umber (dE >= 20; min {plant:.0f})", plant >= 20),
        (f"the bands stay apart: brick (hue 25-50 deg; {hue(pal['red']):.0f}) and rust (hue 50-75 deg; {hue(pal['mustard']):.0f}) "
         f"at dE {bands:.0f} (>= 15)", 25 <= hue(pal["red"]) <= 50 and 50 <= hue(pal["mustard"]) <= 75 and bands >= 15),
        (f"a warm cream zone (L > 85, b* > 8; L {lab(pal['offwhite'])[0]:.0f}, b* {lab(pal['offwhite'])[2]:.0f}) and a tan sky darker "
         f"than it (dL >= 8)", lab(pal["offwhite"])[0] > 85 and lab(pal["offwhite"])[2] > 8
         and lab(pal["offwhite"])[0] - lab(pal["sky"])[0] >= 8),
        (f"one cool accent (festoon b* < 0; {lab(pal['teal'])[2]:.0f}) and a deep umber (L < 30; {lab(pal['brown'])[0]:.0f})",
         lab(pal["teal"])[2] < 0 and lab(pal["brown"])[0] < 30),
        ("the shadow tones stay inside the family (deep tones never black: L > 20)",
         all(lab(v3.deep_of(pal[k], "jupiter"))[0] > 20 for k in names)),
    ]
    rows += ["", "| check | result |", "|---|---|"] + [f"| {t} | {'pass' if ok else 'FAIL'} |" for t, ok in checks]
    return "\n".join(rows), all(ok for _t, ok in checks)


if __name__ == "__main__":
    text, ok = check()
    print(text)
    print("ALL PASS" if ok else "SOME FAIL")
