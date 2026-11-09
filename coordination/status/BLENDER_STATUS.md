# BLENDER STATUS
Updated: 2026-11-09 15:5x · Session: 12 (resumed 14:03 after the owner's restart; THIS SESSION = zuber-4d; LEAD = zuber-d1, UNITY = zuber-a0) · older: coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**15:5x — RESUME HERE.** No lock and no want of mine; everything is committed and pushed. UNITY runs U-203 (Build 0.6.1b: the baked pick in the shovel stroke, B-228's F1), a multi-lock chain (an empty locks folder between its locks is NOT a release): files only, no want, no python, until LEAD messages that it has released. Then, in my lock, each sheet to LEAD before any export (commands and my 2x checks: coordination/reports/blender/preview_notes_0.6.2.md; the runner: `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n> [-MinFreeGB 1.5]`, which lists the locks, takes heavy_blender.lock, runs Blender's bundled python -I with a working-set watchdog and deletes the lock in `finally`; crops for a 4x look: blender/scripts/crop_png.py; both are this session's scratch tools copied into the repo, the repo copies not yet run in that form). **State 16:1x: B-220's EXPORT IS UNDER WAY (LEAD's GO 16:1x, every sheet accepted). Jupiter is exported (1fb6b29b). I yielded to UNITY's want (16:15:23, its U-195 check): nothing of mine runs until UNITY has run that one job (D-037); then, with the locks listed and RAM read in their own calls first:**
1. `tools/blender_render.ps1 backgrounds/saturn` (5 scenes; Jupiter's 5 took 240 s, peak 832 MB; the wrapper takes the lock itself).
2. `tools/blender_render.ps1 backgrounds/neptune` (6 scenes, with the storm / spot layer0 fixed wrap LEAD accepted on the anchor preview).
3. `tools/blender_render.ps1 backgrounds/venus/deck` (one key: the wrapper's LIGHT path, so I hold heavy_blender.lock by hand around it; NOT `backgrounds/venus`, which would re-export the surface).
4. Uranus in two locks of 8 scenes (comma lists: deck1_* + deck2_*, then deck3_* + deep_*; all 16 took 721 s as a preview).
5. After each: read the jsons back against reports/blender/b220_continue_rows.md, commit by explicit file list (git status → paths; 0 .meta), check git show --stat, push, one line to LEAD. Then complete that report (it already carries UNITY's line on venus/deck layer2's y_m -0.5 → -1.5).
6. B-230: its first Earth run (16:05) was wrong in three ways (Stone's wall teal behind grey stone, Subsoil's wall = its fill's tone, a false seam alarm 3.81); the rev is in the source, NOT RUN: the wall = the fill's own main tone mixed 0.35 toward ink, pebbles / strata / veins redrawn, the tile rolled to its quietest row and column. Run `build_back_wall_v3.py <png> earth`, look, send to LEAD only when Stone and Subsoil read apart from their fills; then mars / mercury / venus.
7. B-232 sheet → B-231 design sheet (PREVIEWS ONLY until the owner's C5 look-over, D-185) → B-224 → B-223 → B-225 previews → B-233's sheet (after B-223's camp icon is judged).
NOT YET RUN (desk-checked by reading; expect first-run fixes): B-223, B-224, B-225, B-230's rev, B-231, B-232, B-233. How I run a light sheet: list coordination/locks (abort on any other heavy_ / want_), read RAM in its own call, write heavy_blender.lock, Blender's bundled `python.exe -I <script> <png>` with a working-set watchdog, delete the lock in `finally`.
- Rulings this session: B-233's keys follow the PoiDef label (D-187: icons/catalogue/meridian_beacon, solarite). B-232 = 24 frames of 64 px in 4 rows of 6 (404x268), clips clod_1..4, one clod turning in place; U-195 throws them in code. B-231's crouch: the 1 m gap stays, the crouch stands <= 0.98 m (the forward tuck + root squash 0.92 in the crouch state); the sheet draws the 1 m line and prints the measured top; if it is over, say by how much and LEAD rules on the sheet. B-229: the surveyor's glove on the D-grip.
- B-220 rule (LEAD 11:5x): continue_rows 64 only where a layer's bottom band is >= 25 % solid; a sparse layer fades out over its last 64 rows. B-223's bay keeps DockingBay's keys backgrounds/waystation/layer0..2 at 1920x1080.
- **Rule (LEAD 09:2x):** the first line of ANY call that starts python lists coordination/locks (abort on another role's heavy_ / want_) and reads RAM.
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun: no pistol grip or trigger, a cable-fed, arm-mounted emitter with a cutting nozzle.
- Waiting on others: B-207 closes on PawsOnTheGround green; B-204 on UNITY's capture; B-172 on U-151. UNITY drops the three lance .meta files.

## Last completed
- 11-09 16:16: B-220 export part 1, Jupiter (1fb6b29b; 15 files, 0 .meta; lock 16:12:04-16:16:02, peak 832 MB).
- 11-09 16:02-16:10: the Venus deck sheet (not accepted: towers repeating as slabs, a ladder of crescents) → its rev ACCEPTED (the >= 0.90 rule; layer2 moved, y_m -1.5); the Neptune storm anchor preview ACCEPTED (the core inside the rim, seam 1.03 / 1.02).
- 11-09 15:5x: B-228 complete (reports/blender/smoke_read_0.6.1.md: 79 shots, 21 findings; F1 the pickaxe swing in the shovel stroke → U-203 / Build 0.6.1b).
- 11-09 15:44: B-229 EXPORTED (d7353cd6, LEAD-accepted; Done): ui/hints/dig_down_color.png only, 0 .meta; my lock 15:44:20-15:44:36, peak 335 MB.
- 11-09 15:42: B-220 Neptune sheet ACCEPTED (review_b220_neptune_continue.png; lock 15:37:22-15:42:53, 331 s, peak 455 MB).
- 11-09 15:35: B-229 sheet (lock 15:35:07-15:35:18, peak 82 MB) → ACCEPTED.
- 11-09 14:03-14:5x (session 12, files only): B-233 source (d593051c); B-232 to the ruled format (6970371f); B-230 / B-231 / B-224 desk-check fixes (65e2b1db, 8e9058ce); B-231 to LEAD's rulings (the crouch 734ae6a7; lit from above + the blink swap); reports/blender/preview_notes_0.6.2.md and c5_style_notes.md.
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
none. Waiting on: U-151 (B-172's export), U-152 (B-174). B-237 (the giants up close) is Blocked by LEAD's ruling 15:5x: option C of reports/blender/b237_giants_close_view.md (a painted limb band + a latitude fill on a ring mesh), carded with its UNITY half and a contract section when the giants' pass starts; nothing to draw before that (D-128's amendment rules out a disc_near for the giants).

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
- (15:52 slip) I appended a report section with a shell heredoc in a call whose own listing showed heavy_unity.lock: a lock listing is read BEFORE the call that writes, and beside a lock every write goes through the edit tools, appends included.
- A manifest row's key has three parts (fx/dig_debris stopped an export at the manifest check; now fx/dig_debris/kit): check new rows against `category/name/variant` when they are written.
- A source that cannot run yet gets a desk-check by reading: canvas extents, both soles level by hand kinematics, sheet row sizes, tone-on-tone marks (session 12 found a crash or a wrong pose in five of eight).

## For USER_ACTIONS
none.

## HeavyJobLock
none held (last: 15:44:20-15:44:36, the B-229 export; before it 15:37:22-15:42:53 Neptune, 15:36:23-26 crops, 15:35:07-18 the B-229 sheet); no want on file: UNITY's U-203 chain runs, and LEAD's rule is no want of mine until it has released. No background waiters.
