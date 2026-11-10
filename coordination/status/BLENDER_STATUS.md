# BLENDER STATUS
Updated: 2026-11-09 21:5x · Session: 12 (resumed 14:03 after the owner's restart; THIS SESSION = zuber-4d; LEAD = zuber-d1, UNITY = zuber-a0) · older: coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**22:3x — RESUME HERE: B-239 is COMPLETE and with LEAD (sent 22:3x); my queue is empty again until LEAD cards the close view's art or the owner answers USER-39 (B-231).** B-239: `blender/scripts/giants_v3.py` (the four giants' belts, storms and rings as one table) is read by `build_discs_v3` (paint_giant, BAND_EDGES, the night crescent, shade, saturn_rings); proof `build_discs_v3.py --b239 Assets/_Game/Art <out dir>`: BEFORE (22:13, a1935c8b) and AFTER (22:28) both byte-identical to the exported far discs and ring parts; the four close.json drafts are in blender/preview/b239/ (not exported); report coordination/reports/blender/b239_belt_table.md. A FINDING it made: build_disc / saturn_rings still defaulted to B-143's shelved soft limb (a re-export would have changed every far disc's limb); the default is off now. Nothing exported. The design: reports/blender/b237_limb_band_design.md (LEAD ruled: rings in the same card, the screen-space grain, the swap a cut on a tick; how close the player gets is asked of UNITY). For the record (LEAD 22:2x): the walls keep their grain; their cost was the BC7 format (UNITY changes the import format; U-207 tests the backdrops the same way; no redraw).
Before that, 21:5x: No lock and no want of mine; everything is committed and pushed. Build 0.6.2's release build is written (21:20) and its smoke read is DONE: reports/blender/smoke_read_0.6.2.md (79 shots at 1x, 12 findings G1-G12; "first hour: go" sent to LEAD 21:49, the summary 21:51). Every art card assigned to me is exported or with the owner. Open, in order:
**BUILD 0.6.2 IS OUT on that read (LEAD 21:5x, USER-41); B-230, B-232, B-238 are Done.** My queue is EMPTY until the owner answers USER-39 (B-231, the C5 surveyor). Open:
1. The smoke read is closed on my side: the four crops are cut and written into the report (blender/preview/crop_smoke062_*.png): G5 = two Mars surface decor pieces drawn soft (UNITY to name), G8 = the camp gull's plate (U-206), G9 = my own Mars fill decor "blueberries_a" (no fault; a lighter tone if LEAD wants), G6 = the serpent's line 5-6 px (ruled: drawn at 1x on U-192, no redraw). G4: no art change unless UNITY's offset leaves a landmark (then T2's pebbles smaller and more).
2. **B-237's design note is written for LEAD to card** (files only, no source): reports/blender/b237_limb_band_design.md: the giants up close as flat-toned belts with painted strips at screen scale (limb_band, belt_edge, spot_rim, ring_edge, close_grain, close.json), UNITY's half, the contract's 11.5.1, four points for LEAD to rule. Nothing to draw until it is carded.
3. Then whatever LEAD assigns (B-234 / B-235 / B-236 are promoted only on the owner's yes to B-231).
Exported today after 18:3x, each verified or sent for it: **B-224** c5350eb1 (the veil serpent), rim_shadow removed 8fd65ce7, **B-223** 7a58e321 (the bay with its empty cradle, layer1.json's anchors, icons/catalogue/camp), **B-225** 8eab2a30 (sea_under layers 0 / 3 / 4 + json; 1 and 2 byte-identical), **B-233** 23524e72 (ten catalogue site icons). U-205's test tile is in blender/preview/ (test_u205_earth_t3_no_grain.png + _with_grain.png; never exported).
4. **B-231** is in Review with the OWNER (LEAD's C5 look-over page, USER-39): round 2b accepted by LEAD. A yes = export the part sheet + bone JSON and B-234 / B-235 / B-236 promoted; a "change X" = round 3 on that point. NO export and no C5 companion source until then.
How I run: locks listed, then RAM read, each in its own call; `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n>` for numpy sheets and crops (`blender/scripts/crop_png.py <src> x0 y0 x1 y1 k <dst>`, several per call); `tools/blender_render.ps1 <key or comma list>` for exports (a single kit / painted row takes its light path: hold heavy_blender.lock by hand around it). UNITY and I take turns one job each while both have wants (D-037): on want_unity.lock finish the job I am on, yield, file mine (Write tool) only once UNITY HOLDS the lock, poll with the want refreshed.
- Rulings that stand: D-190 = ONE cream puff per planet tinted by the dug cell's fill tone ("tone_hex" on every ground fill json). B-231: the shadow band on each part's BACK edge (LEAD 18:2x; props keep their upper-left light), crouch <= 0.98 m with the 0.92 root squash, one blink patch per facing. B-233's keys by PoiDef label (D-187). B-237 Blocked (the giants up close = a painted limb band, with the giants' pass). The band rule: continue_rows only at cover >= 0.90.
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun. Waiting on others: B-207 on PawsOnTheGround; B-204 on UNITY's capture; B-172 on U-151.

## Last completed
- 11-09 22:03-22:33: **B-239 complete** (the giants' shared belt table; far discs byte-identical before and after; four close.json drafts; the soft-limb default fixed); B-237's design note (b237_limb_band_design.md) and the smoke read's four crops.
- 11-09 21:30-21:51: **B-225 EXPORTED** 8eab2a30, **B-233 EXPORTED** 23524e72 (both held until 0.6.2's release build was written), U-205's test tile run; **the 0.6.2 smoke read** (79 shots, G1-G12, first hour: go).
- 11-09 19:26-19:32 (files only): reports/blender/smoke_read_0.6.2.md's skeleton, build_back_wall_v3 --no-grain.
- 11-09 18:41-19:25: **B-224 EXPORTED** c5350eb1; rim_shadow removed 8fd65ce7; B-223's rev → ACCEPTED → **EXPORTED** 7a58e321; B-225's preview (two runs) and B-233's sheet (two runs) → to LEAD. RAM was shut 18:50-18:57 (the owner's Ollama, USER-40).
- 11-09 18:02-18:23: B-224 two rounds → ACCEPTED (the veil serpent: thicker, tapering, one veil, no rings); B-223 first preview → the camp icon ACCEPTED, the bay's two changes ordered; B-231 round 2 + 2b (LEAD's six changes, then the 3/4 lids and the brass stalk) → to the owner.
- 11-09 17:56-18:01: tone_hex db44edd1 (22 fill jsons, no png); **B-230 EXPORTED** d9edc71e (20 back walls + the rim shadow, 42 files); the eight variant puffs removed e50dc008 (16 files + four manifest rows).
- 11-09 17:31-17:33: **B-232 + B-238 EXPORTED** df2defa3 (clods t1..t5, rubble, the cream dig puff on four planets, the flick as crumbs); UNITY imported them (748dde18).
- 11-09 16:12-17:02: **B-220 EXPORTED and Done** (33 scenes, 109 files; reports/blender/b220_continue_rows.md). 15:35-15:5x: B-229 exported (d7353cd6), B-228 Done (reports/blender/smoke_read_0.6.1.md).
- Earlier (B-184 to B-227): coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md.

## Ready for review
- With the owner: B-231 (blender/preview/review_b231_surveyor_v5_design.png and the crop_b231_* crops).
- With LEAD: the 0.6.2 smoke read (reports/blender/smoke_read_0.6.2.md).
- In Review until UNITY's import and captures: B-230, B-232, B-238, B-224, B-223, B-225, B-233.
- B-189 / B-185 (waiting on U-159's captures): review_b141_mars_{canyon,storm,plains}(_dip).png, review_b152_venus_surface(_dip).png, review_b149_mercury_{day,twilight,night}_dip.png.

## Handoffs (unrouted only)
- -> UNITY (B-224 c5350eb1 and B-223 7a58e321, both sent to UNITY directly and to LEAD): the serpent's format change (256x256 at 64 px per metre, 7 columns, 12 fps, the hitbox as fractions with y from the bottom) and its two orphan .meta; the bay's layer1.json "cradle" / "ship_ground" anchors, the ship's sprite over layer1 and under layer2; rim_shadow's three orphan .meta.
- -> UNITY (B-220, in reports/blender/b220_continue_rows.md): venus/deck layer2's y_m is -1.5; Neptune storm / spot layer0's core under the rim at the tile's x 1024.
- -> UNITY (B-203 / B-204 / B-207, sent to LEAD 11-08 17:2x): ground_fill_t<n> json tier / depth_m / transition_m 1.0; surface_line row 40 = pivot; ui/skilltree chart json ring_r_px / branch_axis_deg / slots_deg, emblem_r_px 408; node icons at 40 px, 0.4 alpha when locked; vent_eel contact 0 px.
- -> UNITY (B-192): fill_decor_sand_1..3 / fill_decor_basalt_1..3 scattered by a position seed (upright, pivot centred).
- -> UNITY (U-164 / U-159): continue_rows 64 = a layer's bottom 64 rows tile vertically; the ground-set depths (480 at y_m -2.0; 544 at y_m -3.0 with ground_row 352); variant keys ground_band_{frost,basalt,talus,ice,tessera,vent}, ground_fill_basalt, the lips.
- -> UNITY (U-150): vapor_cone / shock_ring pivots = the ship's centre of mass; speed_lines 128x360 for the LEFT edge; puff_boost a drop-in for ships/pilgrim/puff.

## Blockers
none. Waiting on: the owner's word on B-231; U-151 (B-172's export), U-152 (B-174). B-237 Blocked by LEAD's ruling.

## Proposals (undecided only)
- B-231 (told to LEAD 18:1x): the blink's skin patch shows as a faint ring at 4x on the shaded face; LEAD: leave it, U-199 can match the patch's tone if it shows at 1x.
- none open beyond the blink patch.

## Rules I keep (from slips)
- One lock <= 15 min; a painted planet with more than 8 scenes gets its own lock.
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs, and every file change goes through the edit tools, appends and deletions included (a `git rm` waits for a clear folder; a commit of edited files is fine). A lock listing is read in an EARLIER call than any write or run.
- Never pipe my lock helper into `Select-Object -First n` (it cuts the script short); `-Last n` and `Where-Object` are safe.
- Before sending a sheet, look at every new shape at 2x-4x for faces. Session 12's catches: two ringed dots side by side, level or in one outline; a dark chip beside a pit; three dots in a triangle; a dot between two lines; a ring of an eye's size at an eye's height (the surveyor's ear); a hooked post with a pale dot and a wedge (a bird's head); two lit panes under a dark cap; ONE round window or dial on a rounded body or a box (B-233's hauler, station pod, harvester, beacon: use a hatch, a slot, or three in a row). Fix, re-run, look again: a rule that removes one read can make the next (B-230 took five runs).
- A first run is not a sheet: measure it against the card's numbers (B-238: 0.39 m against 0.35; B-231's crouch 0.98 after the heavier line) and fix before sending.
- Before deleting art on another role's word, read the code and tests that could ask for it (GroundArtTests counted the eight variant puffs on disk).
- A re-export for one changed piece or one json field: check `git status` shows only the intended files (every other png byte-identical) before committing.
- A manifest row's key has three parts. No 2>&1 on the wrappers in PowerShell 5.1.
- A want is filed only once the other role HOLDS the lock (D-039); refresh it each poll; never end a turn on a want. No background waiters.
- All three sessions share one working tree: a push can race another role's (fetch, never rebase, push again); commit by explicit file paths, check git show --stat, 0 .meta.
- A stroke's line is drawn in its material's ink_hex; a fill-only material on an open stroke draws nothing; cream marks on a cream body draw nothing.

## For USER_ACTIONS
none (the owner's look at B-231 is LEAD's USER-39).

## HeavyJobLock
none held (last: 22:28:30-22:31:23, B-239's AFTER proof run, peak 357 MB; before it 22:13:26-22:16:19 and 22:07:14-22:10:17). No want on file. Slip logged 22:32: a bare `python` at the end of a shell line hung in the background; stopped at once (never call a system python: only Blender's bundled one through blender_locked.ps1). No background waiters. Slip logged 18:42: a `git rm` in the same call as a lock listing that showed want_unity.lock.
