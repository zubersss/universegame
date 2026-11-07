"""B-161 (C2 Neptune design prep): the proposed Neptune palette strip and its check against Bible §9.1 (muted, slightly aged;
one 6-8 colour palette per planet) and §7.9 Neptune ("deep indigo, white wisps streaking, a storm you can see breathing"; the
endgame, the wind world). Same slot names and order as the other strips (v3.PALETTE_ORDER), so gp_draw's tones and
palette_hits work once LEAD accepts it into meridian.v3.PALETTES["neptune"]. The Mars checks (build_c2_mars_palette) plus
Neptune's family: a deep indigo shadow, a Neptune-blue sky, a cold white for the wisps (the brightest colour), exactly one
warm accent (the Meridian's beacon coral), dimmer than Uranus (Neptune gets 0.4x Uranus's sunlight), and told apart from
Uranus at a glance (the two ice giants sit side by side in space).

  python -I build_c2_neptune_palette.py           prints the check table (markdown); numpy only, no image
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import v3  # noqa: E402
from build_c2_mars_palette import chroma, contrast, lab  # noqa: E402

NEPTUNE = {                    # slot: (hex, role)
    "offwhite": ("#E4E8EE", "wisp white: the streaking cirrus wisps, floe rime, highlights (cold, never cream; the brightest colour)"),
    "red": ("#C06A55", "beacon coral: the one warm accent - the Meridian's hull paint and beacon lamp, suit heaters, the anchor hooks"),
    "mustard": ("#9E88B8", "storm violet: the Dark Storm's breathing rim, Superionic Ice glints, the Pressure phantom's core"),
    "teal": ("#5A98B0", "wind cyan: the wind streaks' tint, methane floes, Windrider sails, Triton's geyser plumes"),
    "green": ("#7C9E86", "abyss sage: Neptune flora (readable on the blue sky, the wisp white and the indigo)"),
    "sky": ("#5E74AE", "Neptune blue: the deck sky, darker and bluer than Uranus's fog"),
    "brown": ("#2C3160", "deep indigo: the Deep, the Great Dark Spot's core and the shadow colour every mid / deep tone mixes toward"),
    "ink": (v3.INK, "ink, shared"),
}


def hue(h):
    L, a, b = lab(h)
    return float(np.degrees(np.arctan2(b, a)) % 360)


def de(a, b):
    return float(np.linalg.norm(lab(a) - lab(b)))


def check():
    pal = {k: h for k, (h, _r) in NEPTUNE.items()}
    v3.PALETTES.setdefault("neptune", pal)
    ura = v3.PALETTES["uranus"]
    rows = ["| slot | hex | role | mid | deep | contrast vs ink | chroma |", "|---|---|---|---|---|---|---|"]
    for k in v3.PALETTE_ORDER:
        h, role = NEPTUNE[k]
        mid = v3.shadow_of(h, "neptune") if k != "ink" else "-"
        deep = v3.deep_of(h, "neptune") if k != "ink" else "-"
        rows.append(f"| {k} | {h} | {role} | {mid} | {deep} | {contrast(h, v3.INK):.1f} | {chroma(h):.0f} |")
    names = [k for k in v3.PALETTE_ORDER if k != "ink"]
    lit = [k for k in names if k != "brown"]
    emax = max(chroma(v3.PALETTES["earth"][k]) for k in names)
    d = min((de(pal[a], pal[b]), a, b) for i, a in enumerate(names) for b in names[i + 1:])
    plant = min(de(pal["green"], pal[k]) for k in ("sky", "offwhite", "brown"))
    warm = [k for k in names if (hue(pal[k]) < 80 or hue(pal[k]) > 340) and chroma(pal[k]) > 20]
    l_nep, l_ura = np.mean([lab(pal[k])[0] for k in lit]), np.mean([lab(ura[k])[0] for k in lit])
    ind = lab(pal["brown"])
    sky = lab(pal["sky"])
    wisp = lab(pal["offwhite"])
    brightest = max(names, key=lambda k: lab(pal[k])[0])
    checks = [
        ("every colour reads under the ink (contrast >= 2.0; the indigo is exempt: it is only a tone and the Deep)",
         all(contrast(pal[k], v3.INK) >= 2.0 for k in names if k != "brown")),
        (f"muted: no colour more saturated than Earth's most saturated accepted colour (chroma <= {emax:.0f}; Neptune max "
         f"{max(chroma(pal[k]) for k in names):.0f})", all(chroma(pal[k]) <= emax for k in names)),
        (f"distinct (closest pair {d[1]} / {d[2]} at dE {d[0]:.0f}, >= 12)", d[0] >= 12),
        (f"plants (abyss sage) read on the blue sky, the wisp white and the indigo (dE >= 20; min {plant:.0f})", plant >= 20),
        (f"a deep indigo shadow (hue 270-310 deg, b* < -20, L < 30; {hue(pal['brown']):.0f}, {ind[2]:.1f}, {ind[0]:.0f}) and a "
         f"Neptune-blue sky (hue 260-300 deg, b* < -20; {hue(pal['sky']):.0f}, {sky[2]:.1f})",
         270 <= hue(pal["brown"]) <= 310 and ind[2] < -20 and ind[0] < 30 and 260 <= hue(pal["sky"]) <= 300 and sky[2] < -20),
        (f"cold white wisps, the brightest colour (b* <= 2; {wisp[2]:.1f}; brightest: {brightest})",
         wisp[2] <= 2 and brightest == "offwhite"),
        (f"exactly one warm accent (warm + chroma > 20: {warm})", warm == ["red"]),
        (f"dimmer than Uranus (mean L of the lit colours {l_nep:.0f} < Uranus's {l_ura:.0f})", l_nep < l_ura),
        (f"told apart from Uranus (sky vs Uranus's fog dE {de(pal['sky'], ura['sky']):.0f} >= 25; shadow vs Uranus's slate "
         f"dE {de(pal['brown'], ura['brown']):.0f} >= 12)",
         de(pal["sky"], ura["sky"]) >= 25 and de(pal["brown"], ura["brown"]) >= 12),
        ("the shadow tones stay inside the family (deep tones never black: L > 20)",
         all(lab(v3.deep_of(pal[k], "neptune"))[0] > 20 for k in names)),
    ]
    rows += ["", "| check | result |", "|---|---|"] + [f"| {t} | {'pass' if ok else 'FAIL'} |" for t, ok in checks]
    return "\n".join(rows), all(ok for _t, ok in checks)


if __name__ == "__main__":
    text, ok = check()
    print(text)
    print("ALL PASS" if ok else "SOME FAIL")
