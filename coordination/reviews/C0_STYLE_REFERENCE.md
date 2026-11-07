# C0 Style Reference (LEAD, cycle 241, 2026-11-06)

C0 is the style test for art direction v4 (Bible 4.0 §9, D-086): one Earth scene drawn and
animated as a 1930s rubber-hose cartoon. This file records LEAD's §9.7 pass on every C0 asset and
names the reference set that every later asset (C1 onward) is judged against (§9.7 box 9).

## The reference set

| what | files | commit |
|---|---|---|
| Surveyor (design + 10 clips, helmet glass) | `Assets/_Game/Art/characters/surveyor/side` · `blender/preview/review_b111_surveyor_side.png` | 7606528 |
| Snoozle (Earth face plant rig set) | `Assets/_Game/Art/flora/earth/rigset` · `blender/preview/review_b112_earth_rigset.png` | 2aa0303 |
| Gus the gull (Earth critter, 4 clips) | `Assets/_Game/Art/creatures/earth/gull` · `blender/preview/review_b113_earth_gull.png` | 27693eb |
| Earth plains (3 painted layers + palette strip) | `Assets/_Game/Art/backgrounds/earth/plains/`, `ui/palettes/earth` · `review_b114_earth_plains.png` | 27693eb |
| Film overlays (grain, dust, scratches) | `Assets/_Game/Art/fx/film/` · `review_b115_film.png` | af18479 |
| Pipeline proof (calibration blob) | `Assets/_Game/Art/characters/calibration_v3/side` · `review_b110_calibration_v3.png` | 3f0c1bd |
| The scene (nine stills, contact sheet, profile) | `coordination/reports/unity/c0_2026-11-06/u098/`, `strip/contact_sheet.png`, `perf_2026-11-06.md` | c114d7d |

## §9.7 nine boxes, per asset (x = pass on the review sheet and in the scene)

| box | surveyor | snoozle | gull | plains | film |
|---|---|---|---|---|---|
| 1 thick hand-inked outline, no perfect geometry | x (outer 4–6 px, interior 1.8–2.6, ±20 % jitter) | x | x (ink-behind on small parts) | n/a (no ink by rule) | n/a |
| 2 flat cel colour, one shadow tone, muted aged palette | x (100 % palette) | x | x | x (washes, paper grain) | x (greyscale) |
| 3 animated on twos (12 fps), within caps | x (10/12/8/8/12/10/12/12/8/6) | x (12-frame loop) | x (10/12/8/10) | n/a | n/a |
| 4 squash + stretch, rubber-hose limbs, secondary motion | x (0.70–1.28; pack swings, hose lags, bob drags) | x (8 % squash, sway) | x (waddle rock, crest drag) | n/a | n/a |
| 5 has an idle loop | x | x | x | n/a | n/a |
| 6 original design | x (plumb-bob antenna, meridian stripe, float pack) | x (dandelion clock face, mitten leaves) | x (three-feather crest, red-spotted beak) | x | x |
| 7 sheet + json per the contract | x | x (rig set, 5 bones) | x | x (layers + json) | x (512², sidecars) |
| 8 fits the atlas + RAM budget after import | x | x | x | x | x (Earth C0: 763 MB, 1 atlas, 38 animated, p99 9.62 ms) |
| 9 consistent with the approved style test | reference | reference | reference | reference | reference |

## Numbers every later asset matches

- PPU 64, 1x sheets, 12 fps; outer ink 4–6 px, interior 1.8–2.6 px, ±20 % thickness jitter; one shadow tone per colour; the planet palette strip (8 colours) + shadow tones; sheets ≤ 2048², 4 px gutters; rig sets ≤ 6 bones.
- Painted layers: watercolour washes, paper grain, soft bleed, no ink, tileable, ≤ 4 MB per PNG.
- Review sheet (§11.7): 1x row on the planet's painted layers, numbered strips per clip, 2× ink zoom, palette with hex, the nine boxes, the "what makes it ours" line; rig sets add the assembled 12-frame loop.
- Helmet glass: flat 25 % sky tone over the face (D-096). Dizzy = spirals and stars, never X eyes (D-087).

## Still placeholder in C0 (by design)

The ground strip and the flat silhouettes on the camp props and the Pilgrim (U-100) are UNITY placeholders; their cartoon art is C1 (Pilgrim, B-122) and C2 (Earth terrain and props). The gull flies without a fly clip (C2 Earth creature card).

## Verdict

C0 approved (D-099). The owner's look-over is USER-23; a rejection there reopens this file.
