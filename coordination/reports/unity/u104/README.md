# U-104 · the drawn HUD (B-121 gauges, B-123 Escape Line + sign, D-090 faces) — captures 2026-11-07 05:21–05:23 (second pass)

`tools/unity_capture.ps1 -Test CaptureU104Hud -Name u104_hud` (unity_capture_20261107_052140.log), 1920×1080, graphics device on, the cartoon stage on Earth.

| File | What it shows | Evidence line |
|---|---|---|
| `hud_1080p.png` | on foot by the Pilgrim: the three dials (Suit power, Oxygen, Gravity) at DialScale 0.5 top-left with their captions and numbers under them, the suit rows (CRYO level, SUIT bar) under those, the altitude rail with the ESCAPE mark, the POI list top-right; no ship rows on foot | `u104 art: gauges True, line True, sign True, ship True` · `suit 1.00, o2 1.00, g 0.33 (dials 160 px), sign y 720.0 lettered 'ESCAPE LINE', face PatrickHand-Regular, ship rows hidden (on foot)` |
| `hud_escape_line.png` | aboard, coasting to rest a few metres under the Escape Line: the painted dotted line tiled along y 720 with the lettered sign a third of the frame left of centre, the ship rows V/S · T/W · AGL · TILT (AGL reads `---` with no ground under the probe), the old U-018 band and its FxLoop off | `ship rows V/S 4 T/W 1.2 AGL --- TILT 0` |

Notes. Every HUD / panel / menu string is Patrick Hand (synthetic bold on the one face) at 1.35× its JetBrains Mono size (`UiKit.HudFaceScale`), with a full-strength ink rim (`Outline`, 1.5 px) so the theme's light 0.6-alpha captions read on Earth's bright sky as well as on the dark one; the title is Limelight. The suit rows sit under the dial numbers (y −246 … −288) and the ship rows under those (−316 / −340 / −380), so nothing overprints. The gravity needle: g / 3 g = 0.33 on Earth. The first pass (04:17) had the Cryo value on the Suit power number and the captions washed out; both are in this pass.
