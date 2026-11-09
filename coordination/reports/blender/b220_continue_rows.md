# B-220 · Which deck layers continue below their sheets (for U-191)

Rule (LEAD, 2026-11-09 11:5x; the threshold raised 16:0x): a layer gets `continue_rows: 64` in its scene json only where its
bottom 64 rows are a FULL fill, >= 90 % solid (alpha > 0.5; it was 25 % until Venus's towers, 29 %, repeated as stacked slabs;
every accepted giant layer printed 1.00, 0.00 or 0.04, so none changed): its bottom band is then tileable (D-169's cross-fade)
and UNITY repeats it below the layer.
A sparse layer (wisps, rain, hail, lightning, the CRUSH band, the Great Red Spot, the storm ring, translucent ice pillars) has
its last 64 rows faded to transparent (its last row alpha 0) and NO `continue_rows`: UNITY draws nothing under it (and a
clamped bottom row is transparent, so no streaks).

Source: blender/scripts/gen_painted_bg.py (continue_layer, CONTINUE_MIN_COVER 0.25); export logs one line per layer
("B-220 <key> layer<n>: continues | feathered | own band"). Sheets: blender/preview/review_b220_<planet>_continue.png.

Status: every sheet ACCEPTED by LEAD (Jupiter, Saturn, Uranus 13:2x / 13:4x; Neptune 15:4x; the Venus deck's rev 16:1x).
**EXPORTED, all of it (2026-11-09 16:12-17:02, 33 scenes, 109 files, 0 .meta):** Jupiter 5 scenes (1fb6b29b), Saturn 5 (5d1da622),
Neptune 6 (dadf2d6c; its storm / spot layer0 on the fixed wrap), Uranus 16 (20c1af38 deck1 + deck2, 82ee7e7a deck3 + deep), venus/deck
(6dd385d0). Every exported scene json was read back against the table below: it holds exactly these `continue_rows`.
Unchanged pngs (not in the commits): the fading layers whose last 64 rows were already empty.

**For UNITY, venus/deck layer2 (changes with its export):** `y_m` goes from -0.5 to -1.5. The same drawing sits 64 rows
higher inside the layer (still 2048 x 384) and the layer sits 1 m lower, so the cloud tops land on the same screen rows and
the layer's bottom 128 rows are plain under-deck (its lobes' feet and the vent glows lay in the rows the repeat reuses).
The vent glows moved with it: they now sit in the floor's upper 84 rows (layer rows 166-250). Nothing to change in code if
the layer's place is read from its json; a hard-coded -0.5 for this layer would draw it 1 m too high.

Neptune's storm and spot, one more change that rode the export (LEAD 15:5x, B-161 reopened; accepted on
review_b220_neptune_storm_anchor.png 16:04): layer0 (the vortex core) keeps a fixed wrap like layer1 (the rim, the pulse
layer), so the core sits under the rim at the scene's anchor (the tile's x 1024; it sat at x 1939, half a tile away).
Vertically the core stays 170 px above the rim's centre, as B-161 was accepted (LEAD: it reads as looking into a funnel).

| Planet | Scenes | layer0 | layer1 | layer2 |
|--------|--------|--------|--------|--------|
| Jupiter | deck1, deck2, deck3, deep | continues | continues | fades |
| Jupiter | spot | continues | fades (the Great Red Spot alone) | fades |
| Saturn | deck1, deck2, deck3, deep | continues | continues | fades |
| Saturn | hexagon | continues | fades (translucent ice pillars, 4 % solid; LEAD: fade, not repeat) | fades |
| Uranus | deck1-3 and deep, each in sun_left / sun_right / night / survey (16 scenes) | continues | continues | fades |
| Neptune | deck1, deck2, deck3, deep | continues | continues | fades |
| Neptune | storm, spot | continues | fades (the violet rim alone, band cover 0.00) | fades |
| Venus | deck | continues | fades (the cloud towers, separate bodies: cover 0.29) | continues (plain under-deck; `y_m` -1.5, see above) |

Watch item for U-191's in-game check (LEAD 13:2x): Jupiter deck3 layer0's faint horizontal lines, in case they repeat every
64 rows at 1x.

Measured on the sheets: the repeat seam (the band's last row into its first, vs its mean row step) 1.17-1.30 on every
continuing layer (< ~1.5 reads clean); the step from the row above into the band 1.0-3.2 / 255. Neptune (15:42): seam
1.17-1.27, step 1.1-2.5 / 255 on its ten continuing layers.
