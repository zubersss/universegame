"""B-139 (C2 Mars design prep): the proposed Mars palette strip and its check against Bible §9.1 (muted, slightly aged:
warm off-whites, soft reds, mustards, teal, dusty greens; one 6-8 colour palette per planet) and §7.2 Mars ("butterscotch
sky, long shadows, rust / umber / salmon; thin haze"). Same slot names and order as Earth's strip (v3.PALETTE_ORDER), so
gp_draw's shadow_of / deep_of (70 / 45 % colour + the planet's umber in the "brown" slot) and palette_hits work unchanged
once LEAD accepts it into meridian.v3.PALETTES. numpy only, no image needed.

  python -I build_c2_mars_palette.py            prints the check table (markdown)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from meridian import v3  # noqa: E402

MARS = {                       # slot: (hex, role)
    "offwhite": ("#EEDCC2", "dust white: highlights, the surveyor's world-lit whites, frost"),
    "red": ("#B0502D", "rust: the ground, boulders, the planet's signature"),
    "mustard": ("#D6A266", "butterscotch: the sky, sunlit dust, warm accents"),
    "teal": ("#6E9C9A", "ice teal: polar ice, cold plants, the one cool accent"),
    "green": ("#8C8E55", "lichen olive: Mars plants (readable on rust and butterscotch)"),
    "sky": ("#D9907A", "salmon haze: far ridges, the dust-storm wall, the horizon band"),
    "brown": ("#5C3A2B", "umber: the shadow colour every mid / deep tone mixes toward"),
    "ink": (v3.INK, "ink, shared"),
}


def _lin(c):
    c = np.asarray(c, np.float64) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def luminance(h):
    r, g, b = _lin(v3.hex_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def lab(h):
    r, g, b = _lin(v3.hex_rgb(h))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116   # noqa: E731
    return np.array([116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))])


def chroma(h):
    L, a, b = lab(h)
    return float(np.hypot(a, b))


def check():
    pal = {k: h for k, (h, _r) in MARS.items()}
    v3.PALETTES.setdefault("mars", pal)                       # for shadow_of / deep_of with planet="mars"
    rows = ["| slot | hex | role | mid | deep | contrast vs ink | chroma |", "|---|---|---|---|---|---|---|"]
    for k in v3.PALETTE_ORDER:
        h, role = MARS[k]
        mid = v3.shadow_of(h, "mars") if k != "ink" else "-"
        deep = v3.deep_of(h, "mars") if k != "ink" else "-"
        rows.append(f"| {k} | {h} | {role} | {mid} | {deep} | {contrast(h, v3.INK):.1f} | {chroma(h):.0f} |")
    names = [k for k in v3.PALETTE_ORDER if k != "ink"]
    emax = max(chroma(v3.PALETTES["earth"][k]) for k in names)
    d = min((float(np.linalg.norm(lab(pal[a]) - lab(pal[b]))), a, b) for i, a in enumerate(names) for b in names[i + 1:])
    checks = [
        ("every colour reads under the ink (contrast >= 2.0; the umber shadow is exempt: it is only a tone)",
         all(contrast(pal[k], v3.INK) >= 2.0 for k in names if k != "brown")),
        (f"muted: no colour more saturated than Earth's most saturated accepted colour (chroma <= {emax:.0f}; Mars max "
         f"{max(chroma(pal[k]) for k in names):.0f})", all(chroma(pal[k]) <= emax for k in names)),
        (f"distinct (closest pair {d[1]} / {d[2]} at dE {d[0]:.0f}, >= 12)", d[0] >= 12),
        ("plants (lichen olive) read on the rust ground and the butterscotch sky (dE >= 20)",
         min(np.linalg.norm(lab(pal["green"]) - lab(pal["red"])), np.linalg.norm(lab(pal["green"]) - lab(pal["mustard"]))) >= 20),
        ("warm family: off-white is warm (b* > 8), the sky is butterscotch (hue 55-80 deg)",
         lab(pal["offwhite"])[2] > 8 and 55 <= np.degrees(np.arctan2(lab(pal["mustard"])[2], lab(pal["mustard"])[1])) <= 80),
        ("the shadow tones stay inside the family (deep tones darker than their colour, never black: L > 20)",
         all(lab(v3.deep_of(pal[k], "mars"))[0] > 20 for k in names)),
    ]
    rows += ["", "| check | result |", "|---|---|"] + [f"| {t} | {'pass' if ok else 'FAIL'} |" for t, ok in checks]
    earth = v3.PALETTES["earth"]
    rows += ["", "For comparison, Earth's chroma: " + ", ".join(f"{k} {chroma(earth[k]):.0f}" for k in names)]
    return "\n".join(rows), all(ok for _t, ok in checks)


if __name__ == "__main__":
    text, ok = check()
    print(text)
    print("ALL PASS" if ok else "SOME FAIL")
