# Preview notes: what each pending sheet must show (BLENDER, 2026-11-09 14:3x)

Written files-only beside UNITY's U-194 chain, so each sheet is one run when the lock is mine. Every run: list
`coordination/locks` first (abort on another role's heavy_ / want_), read RAM in its own call, hold `heavy_blender.lock` by
hand around it, Blender's bundled `python.exe -I`, a working-set watchdog, the lock deleted in `finally`. Every sheet goes to
LEAD; no export before ACCEPTED. All sources below were desk-checked by reading in session 12 (none has run yet).

| Order | Card | Command (from the repo root) | The sheet must show (the card's Accept) | I check at 2x before sending | Desk-check, session 12 |
|-------|------|------------------------------|------------------------------------------|------------------------------|------------------------|
| 1 | B-229 the DIG DOWN hint | `python -I blender/scripts/build_hints_v3.py blender/preview/review_b229_hints_preview.png` | dig_down at 1x beside the SURFACE LINE card (row 1, cards 1 and 2), its picture at 2x; the 9-slice, rects and binding unchanged; palette 100 % | the mitt reads as a hand, not a blob; the D-grip's loop shows past the fingers; the clod and crumbs clear of the haft; no face in the pit / spoil / mouse | glove added (LEAD 14:1x); the grip moved to (30, 11) so the mitt clears the window's top |
| 2 | B-220 Neptune | `python -I blender/scripts/gen_painted_bg.py --continue neptune blender/preview/review_b220_neptune_continue.png` (~3 min) | each deck layer repeated 3x below its sheet: no seam, no streak; which layers continue (>= 25 % solid bottom band) and which fade; deck2's flash lifted out of the band | seam scores (<= 1.6), step <= 3/255; no 64-row period visible at 1x | run in session 11 before the sparse-layer rule; this is the re-run |
| 3 | B-220 Venus deck | the same with `--continue venus`, its own run | as Neptune, for backgrounds/venus/deck | as Neptune | not run |
| 4 | B-220 export | `tools/blender_render.ps1` on each giant's painted rows + venus/deck (> 8 scenes = its own lock; <= 15 min per lock) | the log line "B-220 <key> layerN: continues / feathered" per layer; then reports/blender/b220_continue_rows.md filled for Neptune / Venus | json continue_rows only on the continuing layers | waits for ACCEPTED of 2 and 3 |
| 5 | B-230 back walls | `python -I blender/scripts/build_back_wall_v3.py blender/preview/review_b230_<planet>_back_walls_preview.png <planet>` x 4 | per planet: each tier's wall tiled 2x2 beside its fill at 1x (seamless), a dug cell, the 10 m shaft with U-196's darkening and the rim shadow | the footer: "back" is never the fill's main tone (flagged in capitals if no darker palette tone exists); seam x / y <= 1.6; the wall reads darker than the fill at the shaft's mouth | the snap-to-self guard, the 55 % at 6 m mock-up |
| 6 | B-232 dig debris | `python -I blender/scripts/build_dig_debris_v3.py blender/preview/review_b232_dig_debris_preview.png` | LEAD's 14:2x format: each tier's four clips clod_1..4 as rows (one clod turning in place), a mock burst built from the clips, the rubble 2x2, on T1 and T3 ground; sheets 404x268 | each clod stays inside its 64 px frame (2 px) at every angle; a clip is ONE shape turning, not morphing; T2's pebble, T4's glint, T5's lit edge visible after the tint; no face (two marks on a ball) | rewritten to the ruling; three cream-on-cream marks and a preview crash fixed |
| 7 | B-231 v5 surveyor (previews only, D-185) | `python -I blender/scripts/build_surveyor_v5.py blender/preview/review_b231_surveyor_v5_design.png` (also writes `..._rig.json` beside it) | the turnaround (side, front 3/4) beside the v4 surveyor at 1x and v5 at half size; the pose sheet idle / crouch / jump apex / dig from the rig, knees and elbows bending; the part sheet | the printed pose table: both soles at +0.000 in idle / crouch / dig; the crouch's helmet top ~1.08 m; the shovel's D-grip under the near mitt and its tip in the ground; no part cut by its canvas; the face reads in the helmet | poses re-derived by hand kinematics (see below) |
| 8 | B-224 veil serpent | (its builder in build_creatures_venus_v3.py, source f95c5461) | the redrawn serpent beside the Venus deck at 1x: flat fills, the ink line, no glow, closed mouth, no fangs / spines / barbs | reads passive at 1x; the 25 frames keep their sockets | read 14:3x: helper signatures and materials agree; one fix: death's first frame drew its last wisp past the frame's left edge (the wisps now trail 0.15 + 0.14 j m) |
| 9 | B-223 the bay + camp icon | `python -I blender/scripts/build_bay_v3.py blender/preview/review_b223_bay_preview.png` | the bay at 1080p with the Pilgrim docked and the market panel's frame outlined; the three layers at 1/4; the camp icon at 128 / 64 beside its neighbours | the porthole open onto layer0; nothing important under the market panel; the icon inside the 2 px margin | read end to end: inputs exist (starfield, disc_near, luna, crate, the Pilgrim rig) |
| 10 | B-225 sea shallows | `preview_sea_under` in build_backdrop_v3.py (source 6f107fa2) -> review_b225_sea_shallows_preview.png | the swimmer at 1 / 3 / 10 (and 40) m beside the beach slope at 1x: the light ceiling, the bold shafts, the shallow seabed fading out 40 m off the shore; palette 100 %; continue_rows kept | the surface band reads at 1 m; the shallows' strip tiles; layers 1 and 2 unchanged from the accepted set | the diff read: helper signatures and sizes agree |
| 11 | B-233 site icons (after B-223's camp is judged) | `python -I blender/scripts/build_site_icons_v3.py blender/preview/review_b233_site_icons_preview.png` | the eleven site icons at 128 / 48 / 40 per planet, a row at 64 and the same as unscanned silhouettes, beside item icons | each silhouette distinct at 64 and as a black shape; one porthole per hull; nothing weapon-like on the Warden sites; inside the 2 px margin, each planet's palette 100 % | new this session |

## B-231: what the desk-check changed, and one question it raises

The first pose set (eb51b232) was drawn by eye. Forward kinematics by hand showed: in crouch the front foot hung 7 px over the
ground and the helmet's top stood at ~1.67 m; in dig one foot hung 10 px and neither hand could reach the haft; idle's back
boot tipped 5 degrees. The poses are now solved so both soles are level:

- **crouch**: a deep tuck, hips 0.36 m, the thighs drawn up past level, the torso 70 degrees forward, hands to the ground;
  the helmet's top ~1.08 m. PlayerTuning.Height is 1.8 m for the 2.0 m figure, so the crouch collider (0.9 m) carries a
  1.08 m figure with the same 0.2 m of helmet over it. **Question for LEAD / U-199**: the fishbowl helmet is 0.61 m across,
  so a crouch much under 1.1 m is not drawable without squashing it; "fits a 1 m gap" will show ~0.1 m of helmet in the
  ceiling line unless UNITY squashes the root ~8 % in the crouch state or the crouch gap is 1.1 m. Proposal: a root squash
  of 0.92 in crouch (a cartoon squash, the rig's `squash_root`), decided on the pose sheet.
- **dig**: a lunge; the near hand holds the shovel's D-grip (the tool's pivot, as U-183's socket on the front glove), the
  far hand the haft 0.3 m down it; the shovel 48 degrees below level, its tip ~0.1 m in the ground 1.25 m ahead; the back
  foot on its toe.
- **draw order**: the torso under the near leg (a raised thigh crosses it in crouch and jump), the belt over both; the
  held tool under the near arm so the mitt closes over the grip.
