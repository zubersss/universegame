# BLENDER STATUS
Updated: 2026-11-09 14:4x · Session: 12 (resumed 14:03 after the owner's restart; THIS SESSION = zuber-4d; LEAD = zuber-d1, UNITY = zuber-a0) · older: coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**14:4x — RESUME HERE.** No lock and no want of mine; every source is committed and pushed. UNITY runs U-194 Build 0.6.1 (a multi-lock chain: the locks folder is empty between its locks, which is NOT a release): files only, no want, no python, until LEAD messages that the chain has released. Then, in my lock, each sheet to LEAD before any export, in this order (commands, what each must show and my 2x checks: coordination/reports/blender/preview_notes_0.6.2.md):
1. B-229 sheet (light): ui/hints/dig_down, the shovel in the surveyor's hand → export on ACCEPTED (0.6.2).
2. B-220 Neptune sheet (~3 min), then the Venus deck in its own run → on ACCEPTED of both, export all five giants' bands + venus/deck (> 8 scenes = its own lock; <= 15 min per lock), then fill reports/blender/b220_continue_rows.md for U-191.
3. B-230 sheets (one per planet) → B-232 sheet → B-231 design sheet (PREVIEWS ONLY until the owner's C5 look-over, D-185; it writes the bone JSON beside the review).
4. B-224 → B-223 → B-225 previews → B-233's sheet (only after B-223's camp icon is judged).
B-228 (the 0.6.1 smoke read, read only, no lock) when coordination/reports/unity/smoke_0.6.1/ lands: prep in reports/blender/smoke_read_0.6.1.md.
NOT YET RUN (all desk-checked by reading in session 12; expect first-run fixes): B-223, B-224, B-225, B-229, B-230, B-231, B-232, B-233. How I run a light sheet: list coordination/locks (abort on any other heavy_ / want_), read RAM in its own call, write heavy_blender.lock, Blender's bundled `python.exe -I <script> <png>` with a working-set watchdog, delete the lock in `finally`.
- Rulings this session: B-233's keys follow the PoiDef label (D-187: icons/catalogue/meridian_beacon, solarite). B-232 = 24 frames of 64 px in 4 rows of 6 (404x268), clips clod_1..4, one clod turning in place; U-195 throws them in code. B-231's crouch: the 1 m gap stays, the crouch stands <= 0.98 m (the forward tuck + root squash 0.92 in the crouch state); the sheet draws the 1 m line and prints the measured top; if it is over, say by how much and LEAD rules on the sheet. B-229: the surveyor's glove on the D-grip.
- B-220 rule (LEAD 11:5x): continue_rows 64 only where a layer's bottom band is >= 25 % solid; a sparse layer fades out over its last 64 rows. B-223's bay keeps DockingBay's keys backgrounds/waystation/layer0..2 at 1920x1080.
- **Rule (LEAD 09:2x):** the first line of ANY call that starts python lists coordination/locks (abort on another role's heavy_ / want_) and reads RAM.
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun: no pistol grip or trigger, a cable-fed, arm-mounted emitter with a cutting nozzle.
- Waiting on others: B-207 closes on PawsOnTheGround green; B-204 on UNITY's capture; B-172 on U-151. UNITY drops the three lance .meta files.

## Last completed
- 11-09 14:5x (files only): B-231 to LEAD's four rulings: the paint pass lit from above (no wrap-around, cast shadows under the helmet's ring and the belt, glints on the bubble's top), the blink swap parts blink / blink34 + the JSON's swaps, the sheet's new rows (the rig mirrored, a 1x row beside two v3 camp props, the face at 2x with the blink).
- 11-09 14:4x (files only, for the wait; LEAD's ask): coordination/reports/blender/c5_style_notes.md (v5 in plain words as the source draws it, kept / changed, the four rulings, the C5 pieces).
- 11-09 14:03-14:4x (session 12, files only): B-233 source + B-229 glove rev (d593051c); B-232 to the ruled format (6970371f); B-230 / B-231 / B-224 desk-check fixes (65e2b1db, 8e9058ce); B-231's crouch to LEAD's direction (734ae6a7); reports/blender/preview_notes_0.6.2.md.
- 11-09 13:10-13:38: B-220 Jupiter, Saturn, Uranus sheets ACCEPTED (the U-191 list in reports/blender/b220_continue_rows.md); export after Neptune + Venus.
- Earlier (B-184 to B-227, all Done on the board): coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md.

## Ready for review
- B-189 / B-185: review_b141_mars_{canyon,storm,plains}(_dip).png (9e04de12), review_b152_venus_surface(_dip).png (baa7f1e0), review_b149_mercury_{day,twilight,night}_dip.png (d7fbeace).

## Handoffs (unrouted only)
- -> UNITY (B-203 / B-204 / B-207, sent to LEAD 17:2x): ground_fill_t<n> json tier / depth_m / transition_m 1.0; surface_line row 40 = pivot, 2 m down the surface normal; ui/skilltree chart json ring_r_px / branch_axis_deg / slots_deg, emblem_r_px 408; node icons at 40 px, 0.4 alpha when locked; links tiled under the frames; vent_eel contact 0 px.
- -> UNITY (B-191): terrain/mercury/dig_puff_ice, terrain/venus/dig_puff_{tessera,vent}: drop-ins for dig_puff where the dig is in that variant's band, as B-190's (8 frames 128x128, pivot (0.5, 0.25), clip 'puff'; json "variant").
- -> UNITY (U-167, B-192): terrain/earth/fill_decor_sand_1..3 and terrain/mars/fill_decor_basalt_1..3: scatter in the ground_fill_sand / ground_fill_basalt cutaway by a position seed, as D-165's fill_decor (upright, never rotated, pivot centred; json "fill" names the fill).
- -> UNITY (U-164 / U-159): a layer2 json entry's "continue_rows": 64 = its bottom 64 rows tile vertically. Two depths: the B-133 / B-114 / B-185 sets 480 tall at y_m -2.0; the B-179 / B-186 / B-187 sets 544 tall at y_m -3.0 with "ground_row": 352. The Mars storm's layer2 is a translucent veil (864, y_m -2.0), no ground.
- -> UNITY (U-159): variant keys ground_band_{frost,basalt,talus} (Mars), ground_band_ice (Mercury), ground_band_{tessera,vent} (Venus); ground_fill_basalt (json "fill"); band json "biomes" names the code region; lips terrain/earth/ground_lip_{sand,stone,snow}, terrain/mars/ground_lip_frost.
- -> UNITY (U-150), B-171 placement: vapor_cone and shock_ring pivots = the ship's centre of mass (ship-local 0, 6.2 m); the cone IN FRONT of the hull, the ring BEHIND. speed_lines: 128x360 tiles, 3 per 1080 px edge, drawn for the LEFT edge (flip x for the right), pivot (0, 0.5). puff_boost: a drop-in for ships/pilgrim/puff (tail_exhaust, pivot 0.5 / 0.96, clip 'puff'), 192x288 frames.

## Blockers
none. Waiting on: U-151 (B-172's export), U-152 (B-174).

## Proposals (undecided only)
none open. Decided 14:5x by LEAD (reports/blender/c5_style_notes.md sections 3 and 4): v5 characters are lit FROM ABOVE (the rig mirrors; at most a slight lean to the upper left, the v3 props' side), the palette check on flats and 128 px per metre accepted, ONE blink swap part per facing now; the stag / the nodbell / the camp's near band accepted as B-234 / B-235 / B-236 in the Backlog (promoted when the owner accepts the surveyor; no drawing source before).
- Offered, not drawn (UNITY's work if wanted): a contact shade under each rig part (a darkened copy 2-3 px straight down), for moving shadows under the arms and the pack.

## Rules I keep (from slips)
- (LEAD 13:4x) One lock <= 15 min; a painted planet with more than 8 scenes (Uranus: 16, 721 s) gets its own lock.
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs: no capped dry run, no python / sed text patch, no json check; edit files with the edit tools only (five slips on 11-08 / 11-09). The shell is never the editor while a lock is out, and no interpreter runs before the locks folder is read.
- Before sending a sheet, look at every new shape at 2x for faces: dark marks on a ball (puff frame 2), pale points under a dark arch (teeth), a dark oval on a white ball (a hole).
- preview_dip and any scene lookup: take the planet from the key (PLANET_OF is keyed by scene name). Hold heavy_blender.lock by hand around a light run (the wrapper also refuses beside another role's lock or want).
- No 2>&1 on the render wrapper in PowerShell 5.1 (a numpy warning becomes a terminating error).
- A lock check and a RAM read are each their own call; Blender starts only in a later call after a clear result (D-073). Light work lock-free <= ~300 MB (D-109); under 0.3 GB free, code only.
- A want is filed only when I am next after the running job; withdraw it while the other role's multi-lock job is between locks. While a want is on file, poll the locks each turn; never end a turn waiting for a ping. No background waiters.
- Measure every new export path's frames against the 2 px edge and the ground line before the export.
- All three sessions share one working tree: a push can race another role's; fetch + merge (never rebase) and push again. Commit by explicit file paths (never an Art directory), check git show --stat against the list.
- A stroke's line is drawn in its material's ink_hex: a coloured line needs its own line material; a fill-only material on an open stroke draws nothing.
- A source that cannot run yet gets a desk-check by reading: canvas extents, both soles level by hand kinematics, sheet row sizes, tone-on-tone marks (session 12 found a crash or a wrong pose in five of eight).

## For USER_ACTIONS
none.

## HeavyJobLock
none held (last: 13:21:56-13:38:01, the B-227 export + B-220 Saturn / Uranus); no want on file: UNITY's U-194 chain runs, and LEAD's rule is no want of mine until it has released. No background waiters.
