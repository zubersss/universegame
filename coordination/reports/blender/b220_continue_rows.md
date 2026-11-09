# B-220 · Which deck layers continue below their sheets (for U-191)

Rule (LEAD-ruled amendment, 2026-11-09 11:5x): a layer gets `continue_rows: 64` in its scene json only where its bottom 64 rows
are >= 25 % solid (alpha > 0.5): its bottom band is then tileable (D-169's cross-fade) and UNITY repeats it below the layer.
A sparse layer (wisps, rain, hail, lightning, the CRUSH band, the Great Red Spot, the storm ring, translucent ice pillars) has
its last 64 rows faded to transparent (its last row alpha 0) and NO `continue_rows`: UNITY draws nothing under it (and a
clamped bottom row is transparent, so no streaks).

Source: blender/scripts/gen_painted_bg.py (continue_layer, CONTINUE_MIN_COVER 0.25); export logs one line per layer
("B-220 <key> layer<n>: continues | feathered | own band"). Sheets: blender/preview/review_b220_<planet>_continue.png.

Status: Jupiter, Saturn, Uranus ACCEPTED (LEAD 13:2x / 13:4x); Neptune and Venus deck to render; all export together.

| Planet | Scenes | layer0 | layer1 | layer2 |
|--------|--------|--------|--------|--------|
| Jupiter | deck1, deck2, deck3, deep | continues | continues | fades |
| Jupiter | spot | continues | fades (the Great Red Spot alone) | fades |
| Saturn | deck1, deck2, deck3, deep | continues | continues | fades |
| Saturn | hexagon | continues | fades (translucent ice pillars, 4 % solid; LEAD: fade, not repeat) | fades |
| Uranus | deck1-3 and deep, each in sun_left / sun_right / night / survey (16 scenes) | continues | continues | fades |
| Neptune | deck1, deck2, deck3, deep, storm, spot | (pending sheet) | (expected: decks continue; storm / spot ring fades) | (expected: fades) |
| Venus | deck | (pending sheet) | | |

Watch item for U-191's in-game check (LEAD 13:2x): Jupiter deck3 layer0's faint horizontal lines, in case they repeat every
64 rows at 1x.

Measured on the sheets: the repeat seam (the band's last row into its first, vs its mean row step) 1.17-1.30 on every
continuing layer (< ~1.5 reads clean); the step from the row above into the band 1.0-3.2 / 255.
