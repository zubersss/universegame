# U-104 · the drawn HUD (B-121 gauges, B-123 Escape Line + sign, D-090 faces) — captures 2026-11-07 04:17–04:19

`tools/unity_capture.ps1 -Test CaptureU104Hud -Name u104_hud` (unity_capture_20261107_041723.log), 1920×1080, graphics device on, the cartoon stage on Earth.

| File | What it shows | Evidence line |
|---|---|---|
| `hud_1080p.png` | on foot by the Pilgrim: the three dials (Suit power, Oxygen, Gravity) at DialScale 0.5 top-left with their numbers under them, the suit rows, the altitude rail with the ESCAPE mark, the POI list top-right; no ship rows on foot | `u104 art: gauges True, line True, sign True, ship True` · `suit 1.00, o2 1.00, g 0.33 (dials 160 px), sign y 720.0 lettered 'ESCAPE LINE', face PatrickHand-Regular, ship rows hidden (on foot)` |
| `hud_escape_line.png` | aboard, coasting to rest a few metres under the Escape Line: the painted dotted line tiled along y 720 with the lettered sign a third of the frame left of centre, the ship rows V/S · T/W · AGL · TILT (AGL reads `---` with no ground under the probe), the old U-018 band off | `ship rows V/S 4 T/W 1.2 AGL --- TILT 0` |

Notes. Every HUD / panel / menu string is Patrick Hand (synthetic bold on the one face), the title Limelight; the handwritten face draws at 1.35× its JetBrains Mono size (`UiKit.HudFaceScale`) so the labels read at 1080p. The gravity needle: g / 3 g = 0.33 on Earth. The old band's U-033 FxLoop re-enabled its renderer every frame; the painted branch now switches the loop off with the band (the MenuHud red of 03:48).

Known in this pass, fixed in the next commit: the suit rows (CRYO / SUIT) sit on the dial numbers (the Cryo value overprints the Suit power "100"), and the light labels wash out on Earth's bright sky (the rows move down 30 px, an ink shadow goes under the handwritten face).
