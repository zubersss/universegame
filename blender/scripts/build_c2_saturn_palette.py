"""B-157 (C2 Saturn design prep): the proposed Saturn palette strip and its check against Bible §9.1 (muted, slightly aged;
one 6-8 colour palette per planet) and §7.7 Saturn ("pale gold and butter bands, the ring plane as a bright line across
the sky, soft low sunlight"). Same slot names and order as the other strips (v3.PALETTE_ORDER), so gp_draw's tones and
palette_hits work (ACCEPTED, D-141: in meridian.v3.PALETTES["saturn"]). The Mars checks (build_c2_mars_palette) plus Saturn's
family, measured against the accepted Jupiter palette (D-137): paler (a higher mean lightness) and colder (a cooler
shadow), gold bands, soft banding (the zone / gold / haze colours close together), a cool ring-ice accent.

  python -I build_c2_saturn_palette.py           prints the check table (markdown); numpy only, no image
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import v3  # noqa: E402
from build_c2_mars_palette import chroma, contrast, lab  # noqa: E402

SATURN = {                     # slot: (hex, role)
    "offwhite": ("#F1E9D2", "butter cream: the zones, floe-ice tops, the ring plane's bright line, highlights"),
    "red": ("#B7735C", "dusk salmon: warm accents, Helium-3 condensate tones, the Hex drake's crest"),
    "mustard": ("#D4B46E", "pale gold: the gold bands, brass on the ring-mining rig"),
    "teal": ("#7F98A4", "ring-ice blue-grey: the rings' shadowed edge, the Hexagon's wind-walls, the one cool accent"),
    "green": ("#97A27C", "pale moss: Saturn flora (readable on the cream, the butter haze and the slate)"),
    "sky": ("#E3CFA4", "butter haze: the deck sky in soft low sunlight, far cloud banks"),
    "brown": ("#4A4542", "cold slate: the dark under the floor; the shadow colour every mid / deep tone mixes toward"),
    "ink": (v3.INK, "ink, shared"),
}


def hue(h):
    L, a, b = lab(h)
    return float(np.degrees(np.arctan2(b, a)) % 360)


def check():
    pal = {k: h for k, (h, _r) in SATURN.items()}
    if v3.PALETTES.get("saturn") != pal:                         # D-141: the palette lives in meridian.v3, no setdefault
        raise ValueError("SATURN here and meridian.v3.PALETTES['saturn'] (D-141) differ: " + str(v3.PALETTES.get("saturn")))
    jp = v3.PALETTES["jupiter"]
    rows = ["| slot | hex | role | mid | deep | contrast vs ink | chroma |", "|---|---|---|---|---|---|---|"]
    for k in v3.PALETTE_ORDER:
        h, role = SATURN[k]
        mid = v3.shadow_of(h, "saturn") if k != "ink" else "-"
        deep = v3.deep_of(h, "saturn") if k != "ink" else "-"
        rows.append(f"| {k} | {h} | {role} | {mid} | {deep} | {contrast(h, v3.INK):.1f} | {chroma(h):.0f} |")
    names = [k for k in v3.PALETTE_ORDER if k != "ink"]
    lit = [k for k in names if k != "brown"]
    emax = max(chroma(v3.PALETTES["earth"][k]) for k in names)
    d = min((float(np.linalg.norm(lab(pal[a]) - lab(pal[b]))), a, b) for i, a in enumerate(names) for b in names[i + 1:])
    plant = min(float(np.linalg.norm(lab(pal["green"]) - lab(pal[k]))) for k in ("sky", "offwhite", "brown"))
    l_sat, l_jup = np.mean([lab(pal[k])[0] for k in lit]), np.mean([lab(jp[k])[0] for k in lit])
    bands = max(float(np.linalg.norm(lab(pal[a]) - lab(pal[b]))) for a, b in (("offwhite", "mustard"), ("offwhite", "sky"), ("mustard", "sky")))
    checks = [
        ("every colour reads under the ink (contrast >= 2.0; the slate is exempt: it is only a tone and the dark under the floor)",
         all(contrast(pal[k], v3.INK) >= 2.0 for k in names if k != "brown")),
        (f"muted: no colour more saturated than Earth's most saturated accepted colour (chroma <= {emax:.0f}; Saturn max "
         f"{max(chroma(pal[k]) for k in names):.0f})", all(chroma(pal[k]) <= emax for k in names)),
        (f"distinct (closest pair {d[1]} / {d[2]} at dE {d[0]:.0f}, >= 12)", d[0] >= 12),
        (f"plants (pale moss) read on the butter haze, the cream and the slate (dE >= 20; min {plant:.0f})", plant >= 20),
        (f"paler than Jupiter (mean L of the lit colours {l_sat:.0f} > Jupiter's {l_jup:.0f}) and colder (the shadow's b* "
         f"{lab(pal['brown'])[2]:.1f} < Jupiter's {lab(jp['brown'])[2]:.1f})", l_sat > l_jup and lab(pal["brown"])[2] < lab(jp["brown"])[2]),
        (f"gold bands (pale gold hue 75-95 deg; {hue(pal['mustard']):.0f}) and soft banding (zone / gold / haze within dE 35; max {bands:.0f})",
         75 <= hue(pal["mustard"]) <= 95 and bands <= 35),
        (f"one cool ring-ice accent (b* < 0; {lab(pal['teal'])[2]:.0f}) and a dark cold slate (L < 32; {lab(pal['brown'])[0]:.0f})",
         lab(pal["teal"])[2] < 0 and lab(pal["brown"])[0] < 32),
        ("the shadow tones stay inside the family (deep tones never black: L > 20)",
         all(lab(v3.deep_of(pal[k], "saturn"))[0] > 20 for k in names)),
    ]
    rows += ["", "| check | result |", "|---|---|"] + [f"| {t} | {'pass' if ok else 'FAIL'} |" for t, ok in checks]
    return "\n".join(rows), all(ok for _t, ok in checks)


if __name__ == "__main__":
    text, ok = check()
    print(text)
    print("ALL PASS" if ok else "SOME FAIL")
