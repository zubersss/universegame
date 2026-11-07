"""B-147 (C2 Venus design prep): the proposed Venus palette strip and its check against Bible §9.1 (muted, slightly aged;
one 6-8 colour palette per planet) and §7.4 Venus ("orange-cream haze, backlit cloud towers, black glassy surface lit by
vents"). Same slot names and order as the other strips (v3.PALETTE_ORDER), so gp_draw's tones and palette_hits work once
LEAD accepts it into meridian.v3.PALETTES. The Mars checks (build_c2_mars_palette) plus Venus' family: an apricot haze
sky, a dark glassy basalt, a sulphur yellow.

  python -I build_c2_venus_palette.py           prints the check table (markdown); numpy only, no image
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import v3  # noqa: E402
from build_c2_mars_palette import chroma, contrast, lab  # noqa: E402

VENUS = {                      # slot: (hex, role)
    "offwhite": ("#F0E2C8", "cream haze: the backlit cloud-tower edges, highlights, the aerostat canvas"),
    "red": ("#B8583A", "vent orange: the glow of the surface vents, warm accents, the Vent eel"),
    "mustard": ("#D8B04E", "sulphur yellow: sulphur crust, Sulfur drifters, brass on the stations"),
    "teal": ("#6F9A88", "sea-glass teal: Vitriol Glass, acid-haze tints, the one cool accent"),
    "green": ("#8E9A5E", "dusty olive: Venus plants (readable on the haze, the cream and the basalt)"),
    "sky": ("#E0A57A", "apricot haze: the cloud deck's sky, far cloud towers"),
    "brown": ("#45352F", "glassy basalt: the dark surface; the shadow colour every mid / deep tone mixes toward"),
    "ink": (v3.INK, "ink, shared"),
}


def hue(h):
    L, a, b = lab(h)
    return float(np.degrees(np.arctan2(b, a)) % 360)


def check():
    pal = {k: h for k, (h, _r) in VENUS.items()}
    v3.PALETTES.setdefault("venus", pal)
    rows = ["| slot | hex | role | mid | deep | contrast vs ink | chroma |", "|---|---|---|---|---|---|---|"]
    for k in v3.PALETTE_ORDER:
        h, role = VENUS[k]
        mid = v3.shadow_of(h, "venus") if k != "ink" else "-"
        deep = v3.deep_of(h, "venus") if k != "ink" else "-"
        rows.append(f"| {k} | {h} | {role} | {mid} | {deep} | {contrast(h, v3.INK):.1f} | {chroma(h):.0f} |")
    names = [k for k in v3.PALETTE_ORDER if k != "ink"]
    emax = max(chroma(v3.PALETTES["earth"][k]) for k in names)
    d = min((float(np.linalg.norm(lab(pal[a]) - lab(pal[b]))), a, b) for i, a in enumerate(names) for b in names[i + 1:])
    plant = min(float(np.linalg.norm(lab(pal["green"]) - lab(pal[k]))) for k in ("sky", "offwhite", "brown"))
    checks = [
        ("every colour reads under the ink (contrast >= 2.0; the basalt is exempt: it is only a tone and the dark surface)",
         all(contrast(pal[k], v3.INK) >= 2.0 for k in names if k != "brown")),
        (f"muted: no colour more saturated than Earth's most saturated accepted colour (chroma <= {emax:.0f}; Venus max "
         f"{max(chroma(pal[k]) for k in names):.0f})", all(chroma(pal[k]) <= emax for k in names)),
        (f"distinct (closest pair {d[1]} / {d[2]} at dE {d[0]:.0f}, >= 12)", d[0] >= 12),
        (f"plants (dusty olive) read on the apricot haze, the cream and the basalt (dE >= 20; min {plant:.0f})", plant >= 20),
        (f"the haze is apricot-orange (hue 40-75 deg; {hue(pal['sky']):.0f}) and the sulphur is yellow (hue 70-95 deg; {hue(pal['mustard']):.0f})",
         40 <= hue(pal["sky"]) <= 75 and 70 <= hue(pal["mustard"]) <= 95),
        ("a dark glassy basalt (L < 30) and a warm cream (b* > 8)", lab(pal["brown"])[0] < 30 and lab(pal["offwhite"])[2] > 8),
        ("the shadow tones stay inside the family (deep tones never black: L > 20)",
         all(lab(v3.deep_of(pal[k], "venus"))[0] > 20 for k in names)),
    ]
    rows += ["", "| check | result |", "|---|---|"] + [f"| {t} | {'pass' if ok else 'FAIL'} |" for t, ok in checks]
    return "\n".join(rows), all(ok for _t, ok in checks)


if __name__ == "__main__":
    text, ok = check()
    print(text)
    print("ALL PASS" if ok else "SOME FAIL")
