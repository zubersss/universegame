# BLENDER STATUS
Updated: 2026-11-09 17:1x · Session: 12 (resumed 14:03 after the owner's restart; THIS SESSION = zuber-4d; LEAD = zuber-d1, UNITY = zuber-a0) · older: coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**17:1x — RESUME HERE.** No lock and no want of mine; everything is committed and pushed. Two sets of sheets are with LEAD, nothing of them exported:
1. **B-230** (the hole's back walls): blender/preview/review_b230_{earth,mars,mercury,venus}_back_walls_preview.png (17:12). LEAD accepted the direction on Earth's sheet (the wall = the tier fill's main tone mixed 0.35 toward ink; T5 stays ink; T4's glints on the seams). On ACCEPTED of the four: export `tools/blender_render.ps1 terrain/common/back_walls` (a kit row: 21 keys; hold heavy_blender.lock by hand if the wrapper takes its light path), read the jsons back, commit by explicit file list, 0 .meta.
2. **B-232 + B-238** (dig clods, rubble; the dig puff as low wide dust; the flick without its clod): blender/preview/review_b232_dig_debris_preview.png (17:14). On ACCEPTED: export fx/dig_debris/kit (clods t1..t5 + rubble), props/rig/shovel_kit (the flick; check the shovel prop and icon stay byte-identical), and the dig puff: terrain/{earth,mars,mercury,venus} ground rows' dig_puff + the variants' rows (dig_puffs) ONLY as LEAD rules on my two questions (the eight variant puffs under the tier tint; SideFx.OnMounded plays the puff untinted).
3. Then **B-231**'s design sheet (`tools/blender_locked.ps1 -Job "B-231" -PyArgs blender/scripts/build_surveyor_v5.py,blender/preview/review_b231_surveyor_v5_design.png`; PREVIEWS ONLY until the owner's C5 look-over, D-185; not yet run: expect first-run fixes), then B-224 → B-223 → B-225 previews → B-233's sheet (after B-223's camp icon is judged). B-230 / B-232 / B-238 outrank B-231 (0.6.2's path).
How I run: locks listed, then RAM read, each in its own call; `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n> [-MinFreeGB 1.5]` (lists the locks, takes heavy_blender.lock, Blender's bundled python -I, a working-set watchdog, the lock deleted in `finally`); `blender/scripts/crop_png.py` for crops; a sheet's command and my 2x checks: reports/blender/preview_notes_0.6.2.md. UNITY and I take turns one job each while both have wants (D-037): if want_unity.lock appears, finish the job I am on, release, file mine only once UNITY HOLDS the lock, poll.
- Rulings that stand: B-232 = 24 frames of 64 px, clips clod_1..4, UNITY throws them (U-195) and tints clods and puff by the dug cell's TIER tone (DigFeel.Tone = the tier's chip colour 35 % toward white). B-231: lit from above, crouch <= 0.98 m with a 0.92 root squash, one blink. B-233's keys by PoiDef label (D-187). B-237 Blocked (the giants up close = a painted limb band, with the giants' pass). The band rule: continue_rows only at cover >= 0.90.
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun. Waiting on others: B-207 on PawsOnTheGround; B-204 on UNITY's capture; B-172 on U-151.

## Last completed
- 11-09 17:12-17:15: B-230 four sheets (rev 3 + the T4 fix), B-232 + B-238 sheet (the dust measured 0.69 x 0.34 m) → to LEAD; sources committed.
- 11-09 16:12-17:02: **B-220 EXPORTED and Done** (33 scenes, 109 files, 0 .meta: Jupiter 1fb6b29b, Saturn 5d1da622, Neptune dadf2d6c with B-161's storm / spot wrap, Uranus 20c1af38 + 82ee7e7a, venus/deck 6dd385d0 with layer2 y_m -1.5); reports/blender/b220_continue_rows.md complete for U-191.
- 11-09 15:35-15:5x: B-229 sheet → ACCEPTED → EXPORTED (d7353cd6; Done). B-228 complete and Done (reports/blender/smoke_read_0.6.1.md: 79 shots, 21 findings; F1 the pickaxe swing in the shovel stroke → U-203 / Build 0.6.1b).
- 11-09 14:03-15:0x (files only): sources B-233, B-232's format, desk-check fixes B-230 / B-231 / B-224, B-231 to LEAD's rulings; reports preview_notes_0.6.2.md, c5_style_notes.md, b237_giants_close_view.md; tools/blender_locked.ps1, blender/scripts/crop_png.py.
- Earlier (B-184 to B-227): coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md.

## Ready for review
- B-230: the four sheets above. B-232 + B-238: the shared sheet above.
- B-189 / B-185 (waiting on U-159's captures): review_b141_mars_{canyon,storm,plains}(_dip).png, review_b152_venus_surface(_dip).png, review_b149_mercury_{day,twilight,night}_dip.png.

## Handoffs (unrouted only)
- -> UNITY (B-220, in reports/blender/b220_continue_rows.md): venus/deck layer2's y_m is -1.5 (was -0.5; the same drawing 64 rows higher in the layer); Neptune storm / spot layer0's core now sits under the rim at the tile's x 1024.
- -> UNITY (B-238, on its acceptance): the base dig_puff is cream + ink (multiply it by the tier's tone, also where a mound lands); it is 0.69 x 0.34 m at its peak with its foot on the pivot row, so it plays at scale 1; shovel_flick is crumbs only.
- -> UNITY (B-203 / B-204 / B-207, sent to LEAD 11-08 17:2x): ground_fill_t<n> json tier / depth_m / transition_m 1.0; surface_line row 40 = pivot; ui/skilltree chart json ring_r_px / branch_axis_deg / slots_deg, emblem_r_px 408; node icons at 40 px, 0.4 alpha when locked; vent_eel contact 0 px.
- -> UNITY (B-191 / B-192): dig_puff_{ice,tessera,vent} drop-ins; fill_decor_sand_1..3 / fill_decor_basalt_1..3 scattered by a position seed (upright, pivot centred).
- -> UNITY (U-164 / U-159): continue_rows 64 = a layer's bottom 64 rows tile vertically; the ground-set depths (480 at y_m -2.0; 544 at y_m -3.0 with ground_row 352); variant keys ground_band_{frost,basalt,talus,ice,tessera,vent}, ground_fill_basalt, the lips.
- -> UNITY (U-150): vapor_cone / shock_ring pivots = the ship's centre of mass; speed_lines 128x360 for the LEFT edge; puff_boost a drop-in for ships/pilgrim/puff.

## Blockers
none. Waiting on: U-151 (B-172's export), U-152 (B-174). B-237 Blocked by LEAD's ruling (see above).

## Proposals (undecided only)
- B-238 (to LEAD 17:1x): (a) the eight variant puffs under the tier tint: keep their material colours for mounds, re-export them in cream, or retire them; (b) SideFx.OnMounded plays the puff untinted: UNITY tints it, or the base puff keeps a tone. (c) the dust's ink at 1.5 px so it sits behind the clods.
- B-230 (to LEAD 17:1x): a planet-specific T1 for Mars / Mercury / Venus (the roots and worm holes read there as dry veins and pits).
- Offered, not drawn (UNITY's work if wanted): a contact shade under each v5 rig part.

## Rules I keep (from slips)
- One lock <= 15 min; a painted planet with more than 8 scenes gets its own lock (Uranus: two locks of 8, 398 s + 425 s).
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs, and every file change goes through the edit tools, appends included (a shell heredoc at 15:52 was the sixth slip of this kind). A lock listing is read in an EARLIER call than any write or run.
- Never pipe my lock helper into `Select-Object -First n`: it cut the script short after the release line and skipped the next step (17:04).
- Before sending a sheet, look at every new shape at 2x-3x for faces: dark marks on a ball, pale points under a dark arch, two ringed dots side by side (B-230's worm holes), two equal top lobes (B-184's puff).
- A first run is not a sheet: measure it against the card's numbers (B-238: 0.39 m against 0.35) and fix before sending.
- A manifest row's key has three parts. No 2>&1 on the wrappers in PowerShell 5.1. preview_dip and scene lookups: the planet from the key.
- A want is filed only once the other role HOLDS the lock (D-039); refresh it each poll; never end a turn on a want. No background waiters.
- All three sessions share one working tree: a push can race another role's (fetch, never rebase, push again); commit by explicit file paths, check git show --stat, 0 .meta.
- A stroke's line is drawn in its material's ink_hex; a fill-only material on an open stroke draws nothing; cream marks on a cream body draw nothing.
- A source that cannot run yet gets a desk-check by reading (extents, both soles level, sheet row sizes): session 12 found a crash or a wrong pose in five of eight; the first RUN still found what reading could not (hues, sizes, face reads).

## For USER_ACTIONS
none.

## HeavyJobLock
none held (last: 17:14:41-17:14:45, the B-232 + B-238 sheet; today's export locks are in the B-220 commits); no want on file. No background waiters.
