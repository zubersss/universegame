"""B-158 (C2 Uranus design prep): the proposed Uranus palette strip and its check against Bible §9.1 (muted, slightly aged;
one 6-8 colour palette per planet) and §7.8 Uranus ("featureless cyan fog that reveals bands only with the Survey module;
dim; crystalline sparkle below"; the sideways winter). Same slot names and order as the other strips (v3.PALETTE_ORDER), so
gp_draw's tones and palette_hits work (ACCEPTED, D-142: in meridian.v3.PALETTES["uranus"]). The Mars checks
(build_c2_mars_palette) plus Uranus' family: a cyan fog sky, a cold white, exactly one warm accent, dimmer than Saturn
(D-141), a cold blue-slate shadow.

  python -I build_c2_uranus_palette.py           prints the check table (markdown); numpy only, no image
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import v3  # noqa: E402
from build_c2_mars_palette import chroma, contrast, lab  # noqa: E402

URANUS = {                     # slot: (hex, role)
    "offwhite": ("#E3ECE9", "ice white: floe tops, frost, the crystalline sparkle, highlights (cold, never cream)"),
    "red": ("#C27A4A", "ember amber: the one warm accent - the Frostwisp's warmth, suit heaters, the beacon lamp"),
    "mustard": ("#ABAF86", "methane sage: the faint methane bands (Survey only), pale lichen, old brass gone cold"),
    "teal": ("#5E9FA5", "methane cyan: the fog's dense banks, Methane rays, the dominant cool"),
    "green": ("#7E9A80", "frost mint: Uranus flora (readable on the fog, the ice white and the slate)"),
    "sky": ("#9CC2C2", "cyan fog: the deck sky, dim and featureless"),
    "brown": ("#2E3D47", "night slate: the dark half of the world and the shadow colour every mid / deep tone mixes toward"),
    "ink": (v3.INK, "ink, shared"),
}


def hue(h):
    L, a, b = lab(h)
    return float(np.degrees(np.arctan2(b, a)) % 360)


def check():
    pal = {k: h for k, (h, _r) in URANUS.items()}
    v3.PALETTES.setdefault("uranus", pal)
    sat = v3.PALETTES["saturn"]
    rows = ["| slot | hex | role | mid | deep | contrast vs ink | chroma |", "|---|---|---|---|---|---|---|"]
    for k in v3.PALETTE_ORDER:
        h, role = URANUS[k]
        mid = v3.shadow_of(h, "uranus") if k != "ink" else "-"
        deep = v3.deep_of(h, "uranus") if k != "ink" else "-"
        rows.append(f"| {k} | {h} | {role} | {mid} | {deep} | {contrast(h, v3.INK):.1f} | {chroma(h):.0f} |")
    names = [k for k in v3.PALETTE_ORDER if k != "ink"]
    lit = [k for k in names if k != "brown"]
    emax = max(chroma(v3.PALETTES["earth"][k]) for k in names)
    d = min((float(np.linalg.norm(lab(pal[a]) - lab(pal[b]))), a, b) for i, a in enumerate(names) for b in names[i + 1:])
    plant = min(float(np.linalg.norm(lab(pal["green"]) - lab(pal[k]))) for k in ("sky", "offwhite", "brown"))
    warm = [k for k in names if (hue(pal[k]) < 80 or hue(pal[k]) > 340) and chroma(pal[k]) > 20]
    l_ura, l_sat = np.mean([lab(pal[k])[0] for k in lit]), np.mean([lab(sat[k])[0] for k in lit])
    checks = [
        ("every colour reads under the ink (contrast >= 2.0; the slate is exempt: it is only a tone and the dark half)",
         all(contrast(pal[k], v3.INK) >= 2.0 for k in names if k != "brown")),
        (f"muted: no colour more saturated than Earth's most saturated accepted colour (chroma <= {emax:.0f}; Uranus max "
         f"{max(chroma(pal[k]) for k in names):.0f})", all(chroma(pal[k]) <= emax for k in names)),
        (f"distinct (closest pair {d[1]} / {d[2]} at dE {d[0]:.0f}, >= 12)", d[0] >= 12),
        (f"plants (frost mint) read on the cyan fog, the ice white and the slate (dE >= 20; min {plant:.0f})", plant >= 20),
        (f"a cyan fog (hue 180-230 deg, b* < 0; {hue(pal['sky']):.0f}, {lab(pal['sky'])[2]:.1f}) and a cold white (b* <= 2; {lab(pal['offwhite'])[2]:.1f})",
         180 <= hue(pal["sky"]) <= 230 and lab(pal["sky"])[2] < 0 and lab(pal["offwhite"])[2] <= 2),
        (f"exactly one warm accent (warm + chroma > 20: {warm})", warm == ["red"]),
        (f"dimmer than Saturn (mean L of the lit colours {l_ura:.0f} < Saturn's {l_sat:.0f}) and a cold slate (b* < 0; {lab(pal['brown'])[2]:.1f})",
         l_ura < l_sat and lab(pal["brown"])[2] < 0),
        ("the shadow tones stay inside the family (deep tones never black: L > 20)",
         all(lab(v3.deep_of(pal[k], "uranus"))[0] > 20 for k in names)),
    ]
    rows += ["", "| check | result |", "|---|---|"] + [f"| {t} | {'pass' if ok else 'FAIL'} |" for t, ok in checks]
    return "\n".join(rows), all(ok for _t, ok in checks)


if __name__ == "__main__":
    text, ok = check()
    print(text)
    print("ALL PASS" if ok else "SOME FAIL")
