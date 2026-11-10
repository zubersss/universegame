# BLENDER STATUS
Updated: 2026-11-09 18:3x · Session: 12 (resumed 14:03 after the owner's restart; THIS SESSION = zuber-4d; LEAD = zuber-d1, UNITY = zuber-a0) · older: coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**18:3x — RESUME HERE.** My want is on file behind UNITY's lock (18:26:48; RAM 0.08 GB under it); poll, delete my own want (blender_locked.ps1 refuses beside it), then in order:
1. **B-224 EXPORT** (LEAD ACCEPTED round 2, 18:2x): `tools/blender_render.ps1 creatures/venus/veil_serpent` (a v3 sheet from a .blend built in Blender: the wrapper takes the lock; gate ~1.5 GB free). New for this row, UNCOMMITTED and not yet run: render.py measures the "hitbox" (manifest `"hitbox": "measure"`) and waives the two clip-length caps (`"clip_caps_exception"`: the v2 counts idle 5 / walk 8 kept, the card's ruling); the row's bg_scene is the Venus deck. The export removes the v2 maps veil_serpent_normal.png and veil_serpent_emission.png (replaces_v2): commit color.png + json + the two deletions + render.py + manifest.json by explicit list, 0 .meta, and name to UNITY the two orphan .meta and the format change for U-192 (256x256 at 64 px per metre, was 400 at 103; 7 columns, 12 fps, the hitbox's convention: fractions, y from the bottom).
2. **B-223 rev** (LEAD 18:2x; the camp icon is ACCEPTED): build_bay_v3.py is edited, UNCOMMITTED, not yet run: the two umbilicals (they read as the rocket's arms) replaced by the bay's two docking clamps on the cradle's ends; the Pilgrim NOT baked into layer1 (the preview composes it; layer1.json carries the cradle's anchor for U-192); the preview writes the three layers to blender/preview/b223_layers/ and prints their png sizes. Run `tools/blender_locked.ps1 -Job .. -PyArgs blender/scripts/build_bay_v3.py,blender/preview/review_b223_bay_preview.png -CapMB 1300`, look at the clamps for face / arm reads, re-cut the crops (crop_b223_camp_icon_3x: 1480 1100 1900 1270 x3; crop_b223_pilgrim_docked: 380 100 960 960), report the sizes to LEAD (quantise the grain if a layer passes about 1.5 MB), export on ACCEPTED (a Limelight credits row for BAY 2 / HALCYON FREIGHT).
3. **rim_shadow's removal** (LEAD 18:2x: UNITY draws its own rim gradient): build_back_wall_v3.py no longer exports it and the manifest row's note says so (both edited, UNCOMMITTED). Still to do with no lock or want on file: `git rm` Assets/_Game/Art/terrain/common/rim_shadow.json and rim_shadow_color.png, commit with the two sources, name the two .meta (and the folder's) to UNITY.
4. **B-225**'s preview (`preview_sea_under` in build_backdrop_v3.py → review_b225_sea_shallows_preview.png), then **B-233**'s sheet (`build_site_icons_v3.py blender/preview/review_b233_site_icons_preview.png`; its ten follow the accepted camp icon).
5. **B-231** is in Review with the OWNER (LEAD's C5 look-over page, USER-39): round 2b accepted by LEAD. A yes = export the part sheet + bone JSON and B-234 / B-235 / B-236 promoted; a "change X" = round 3 on that point. NO export and no C5 companion source until then.
How I run: locks listed, then RAM read, each in its own call; `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n>` for numpy sheets and crops (`blender/scripts/crop_png.py <src> x0 y0 x1 y1 k <dst>`, several per call); `tools/blender_render.ps1 <key or comma list>` for exports (a single kit / painted row takes its light path: hold heavy_blender.lock by hand around it). UNITY and I take turns one job each while both have wants (D-037): on want_unity.lock finish the job I am on, yield, file mine (Write tool) only once UNITY HOLDS the lock, poll with the want refreshed.
- Rulings that stand: D-190 = ONE cream puff per planet tinted by the dug cell's fill tone ("tone_hex" on every ground fill json). B-231: the shadow band on each part's BACK edge (LEAD 18:2x; props keep their upper-left light), crouch <= 0.98 m with the 0.92 root squash, one blink patch per facing. B-233's keys by PoiDef label (D-187). B-237 Blocked (the giants up close = a painted limb band, with the giants' pass). The band rule: continue_rows only at cover >= 0.90.
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun. Waiting on others: B-207 on PawsOnTheGround; B-204 on UNITY's capture; B-172 on U-151.

## Last completed
- 11-09 18:02-18:23: B-224 two rounds → ACCEPTED (the veil serpent: thicker, tapering, one veil, no rings); B-223 first preview → the camp icon ACCEPTED, the bay's two changes ordered; B-231 round 2 + 2b (LEAD's six changes, then the 3/4 lids and the brass stalk) → to the owner.
- 11-09 17:56-18:01: tone_hex db44edd1 (22 fill jsons, no png); **B-230 EXPORTED** d9edc71e (20 back walls + the rim shadow, 42 files); the eight variant puffs removed e50dc008 (16 files + four manifest rows).
- 11-09 17:31-17:33: **B-232 + B-238 EXPORTED** df2defa3 (clods t1..t5, rubble, the cream dig puff on four planets, the flick as crumbs); UNITY imported them (748dde18).
- 11-09 16:12-17:02: **B-220 EXPORTED and Done** (33 scenes, 109 files; reports/blender/b220_continue_rows.md). 15:35-15:5x: B-229 exported (d7353cd6), B-228 Done (reports/blender/smoke_read_0.6.1.md).
- Earlier (B-184 to B-227): coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md.

## Ready for review
- With the owner: B-231 (blender/preview/review_b231_surveyor_v5_design.png and the crop_b231_* crops).
- In Review until UNITY's import and captures: B-230, B-232, B-238.
- B-189 / B-185 (waiting on U-159's captures): review_b141_mars_{canyon,storm,plains}(_dip).png, review_b152_venus_surface(_dip).png, review_b149_mercury_{day,twilight,night}_dip.png.

## Handoffs (unrouted only)
- -> UNITY (B-224, at its export): the format change and the two orphan .meta, as in Current task 1.
- -> UNITY (B-223, at its export): layer1.json's "cradle" / "ship_ground" anchors (px from the top-left and bottom-left, metres from the layer's centre at 64 px per metre); the ship's sprite goes over layer1 and under layer2.
- -> UNITY (B-220, in reports/blender/b220_continue_rows.md): venus/deck layer2's y_m is -1.5; Neptune storm / spot layer0's core under the rim at the tile's x 1024.
- -> UNITY (B-203 / B-204 / B-207, sent to LEAD 11-08 17:2x): ground_fill_t<n> json tier / depth_m / transition_m 1.0; surface_line row 40 = pivot; ui/skilltree chart json ring_r_px / branch_axis_deg / slots_deg, emblem_r_px 408; node icons at 40 px, 0.4 alpha when locked; vent_eel contact 0 px.
- -> UNITY (B-192): fill_decor_sand_1..3 / fill_decor_basalt_1..3 scattered by a position seed (upright, pivot centred).
- -> UNITY (U-164 / U-159): continue_rows 64 = a layer's bottom 64 rows tile vertically; the ground-set depths (480 at y_m -2.0; 544 at y_m -3.0 with ground_row 352); variant keys ground_band_{frost,basalt,talus,ice,tessera,vent}, ground_fill_basalt, the lips.
- -> UNITY (U-150): vapor_cone / shock_ring pivots = the ship's centre of mass; speed_lines 128x360 for the LEFT edge; puff_boost a drop-in for ships/pilgrim/puff.

## Blockers
none. Waiting on: the owner's word on B-231; U-151 (B-172's export), U-152 (B-174). B-237 Blocked by LEAD's ruling.

## Proposals (undecided only)
- B-231 (told to LEAD 18:1x): the blink's skin patch shows as a faint ring at 4x on the shaded face; LEAD: leave it, U-199 can match the patch's tone if it shows at 1x.
- B-223: the three 1920x1080 layers' png sizes are not measured yet; quantising the paper grain is the lever if one passes about 1.5 MB.

## Rules I keep (from slips)
- One lock <= 15 min; a painted planet with more than 8 scenes gets its own lock.
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs, and every file change goes through the edit tools, appends and deletions included (a `git rm` waits for a clear folder; a commit of edited files is fine). A lock listing is read in an EARLIER call than any write or run.
- Never pipe my lock helper into `Select-Object -First n` (it cuts the script short); `-Last n` and `Where-Object` are safe.
- Before sending a sheet, look at every new shape at 2x-4x for faces. Session 12's catches: two ringed dots side by side, level or in one outline; a dark chip beside a pit; three dots in a triangle; a dot between two lines; a ring of an eye's size at an eye's height (the surveyor's ear); a hooked post with a pale dot and a wedge (a bird's head); two lit panes under a dark cap. Fix, re-run, look again: a rule that removes one read can make the next (B-230 took five runs).
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
none held (last: 18:23:17-33, B-223's preview rev 2). want_blender.lock on file since 18:26:53 behind heavy_unity.lock (18:26:48). No background waiters.
