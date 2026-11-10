# BLENDER STATUS
Updated: 2026-11-09 19:2x · Session: 12 (resumed 14:03 after the owner's restart; THIS SESSION = zuber-4d; LEAD = zuber-d1, UNITY = zuber-a0) · older: coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**19:3x — RESUME HERE.** No lock and no want of mine; everything is committed and pushed. UNITY holds the lock for 0.6.2's release chain (about an hour of locks from 19:3x): FILES ONLY until LEAD says the release build is written. **B-225 and B-233 are both ACCEPTED by LEAD (19:2x) and both exports are HELD until then** (the tree is shared; B-225 changes layer3's height and adds layer4 before any code reads them). Then, in order: (a) export B-225 and B-233 as below; (b) one light run of U-205's test tile: `tools/blender_locked.ps1 -Job "U-205 test tile" -PyArgs blender/scripts/build_back_wall_v3.py,--no-grain,blender/preview/test_u205_earth_t3_no_grain.png,earth,3 -CapMB 700` (D-192: a wall without its paper grain, PREVIEW folder only, never exported; it also writes the grained tile beside it and prints both sizes and colour counts) and tell UNITY the two paths; (c) the 0.6.2 smoke read when the smoke lands, on the skeleton reports/blender/smoke_read_0.6.2.md (read tools only; the owner's page waits for it). The two accepted sheets:
1. **B-225** (the sea reads underwater from the first metre): blender/preview/review_b225_sea_shallows_preview.png (19:19, the second run: the column's top plainer, bolder shafts, thicker caustic lines) + crop_b225_{1m,3m,10m_top,3m_shallows}.png. On ACCEPTED: `tools/blender_render.ps1 backgrounds/earth/sea_under` (a painted row: about 2 min; if the wrapper takes its light path hold heavy_blender.lock by hand), read the export's palette share and seams, check in `git status` that layers 1 and 2 are byte-identical, commit layers 0 / 3 / 4 + sea_under.json by explicit list, tell UNITY layer3's new height (128 px) and layer4's "shore_m" / "draw_before".
2. **B-233** (the catalogue's ten site icons beside the accepted camp): blender/preview/review_b233_site_icons_preview.png (19:25, the second run: no single round window or dial on a rounded body or a box) + crop_b233_{earth,mars,mercury,venus}_2x.png, crop_b233_row64_silhouettes.png. On ACCEPTED: `tools/blender_render.ps1 icons/catalogue/sites` (a kit row: hold heavy_blender.lock by hand), ten new keys icons/catalogue/<label> (.json + _color.png each), commit by explicit list, 0 .meta.
3. Any round LEAD orders on either; then whatever LEAD assigns (B-234 / B-235 / B-236 are promoted only on the owner's yes to B-231).
Exported since 18:3x, all verified by LEAD or sent for it: **B-224** c5350eb1 (the veil serpent; render.py's "hitbox": "measure" and "clip_caps_exception" for that row, confirmed by LEAD), rim_shadow removed 8fd65ce7, **B-223** 7a58e321 (the bay with its empty cradle and clamps, layer1.json's anchors, icons/catalogue/camp; layers 868 / 1285 / 89 KB after the grain was lightened and quantised in steps of 4).
4. **B-231** is in Review with the OWNER (LEAD's C5 look-over page, USER-39): round 2b accepted by LEAD. A yes = export the part sheet + bone JSON and B-234 / B-235 / B-236 promoted; a "change X" = round 3 on that point. NO export and no C5 companion source until then.
How I run: locks listed, then RAM read, each in its own call; `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n>` for numpy sheets and crops (`blender/scripts/crop_png.py <src> x0 y0 x1 y1 k <dst>`, several per call); `tools/blender_render.ps1 <key or comma list>` for exports (a single kit / painted row takes its light path: hold heavy_blender.lock by hand around it). UNITY and I take turns one job each while both have wants (D-037): on want_unity.lock finish the job I am on, yield, file mine (Write tool) only once UNITY HOLDS the lock, poll with the want refreshed.
- Rulings that stand: D-190 = ONE cream puff per planet tinted by the dug cell's fill tone ("tone_hex" on every ground fill json). B-231: the shadow band on each part's BACK edge (LEAD 18:2x; props keep their upper-left light), crouch <= 0.98 m with the 0.92 root squash, one blink patch per facing. B-233's keys by PoiDef label (D-187). B-237 Blocked (the giants up close = a painted limb band, with the giants' pass). The band rule: continue_rows only at cover >= 0.90.
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun. Waiting on others: B-207 on PawsOnTheGround; B-204 on UNITY's capture; B-172 on U-151.

## Last completed
- 11-09 18:41-19:25: **B-224 EXPORTED** c5350eb1; rim_shadow removed 8fd65ce7; B-223's rev → ACCEPTED → **EXPORTED** 7a58e321; B-225's preview (two runs) and B-233's sheet (two runs) → to LEAD. RAM was shut 18:50-18:57 (the owner's Ollama, USER-40).
- 11-09 18:02-18:23: B-224 two rounds → ACCEPTED (the veil serpent: thicker, tapering, one veil, no rings); B-223 first preview → the camp icon ACCEPTED, the bay's two changes ordered; B-231 round 2 + 2b (LEAD's six changes, then the 3/4 lids and the brass stalk) → to the owner.
- 11-09 17:56-18:01: tone_hex db44edd1 (22 fill jsons, no png); **B-230 EXPORTED** d9edc71e (20 back walls + the rim shadow, 42 files); the eight variant puffs removed e50dc008 (16 files + four manifest rows).
- 11-09 17:31-17:33: **B-232 + B-238 EXPORTED** df2defa3 (clods t1..t5, rubble, the cream dig puff on four planets, the flick as crumbs); UNITY imported them (748dde18).
- 11-09 16:12-17:02: **B-220 EXPORTED and Done** (33 scenes, 109 files; reports/blender/b220_continue_rows.md). 15:35-15:5x: B-229 exported (d7353cd6), B-228 Done (reports/blender/smoke_read_0.6.1.md).
- Earlier (B-184 to B-227): coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md.

## Ready for review
- With the owner: B-231 (blender/preview/review_b231_surveyor_v5_design.png and the crop_b231_* crops).
- ACCEPTED, export held until 0.6.2 is out: B-225's preview, B-233's sheet (Current task 1 and 2).
- In Review until UNITY's import and captures: B-230, B-232, B-238, B-224, B-223.
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
none held (last: 19:25:03-12, B-233's sheet rev and crops; B-223's export 19:03:15-19:04:46). No want on file. No background waiters. Slip logged 18:42: a `git rm` in the same call as a lock listing that showed want_unity.lock.
