# BLENDER STATUS
Updated: 2026-11-10 00:5x · Session: 13 (resumed 11-10 00:52 after the windows' restart; THIS SESSION = zuber-e2; LEAD = zuber-36 (its message 00:5x); the third window, zuber-57, is UNITY by elimination; the laptop itself was not rebooted) · older: coordination/status/archive/BLENDER_2026-11-09.md (session 12's closed entries), BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**00:5x — RESUME HERE (session 13): NOTHING IS ASSIGNED AND NOTHING IS HALF-DONE. The tree holds no uncommitted file of mine; no lock, no want. LEAD (zuber-36) has my check-in and sends the queue and any new card next.** Next work comes from: the owner's answer to USER-39 (B-231, the v5 surveyor: a yes = export the part sheet + bone JSON and B-234 / B-235 / B-236 promoted; a "change X" = round 3 on that point), LEAD carding the giants' close view's UNITY half (then my strips export), U-151 landing (then B-172's export), or a new card. On resume: read LEAD's messages and the board's top queue lines first.
- Done at this resume (files only, RAM 1.01 GB at 00:54, under the gate): the 19 cards that still read Ready checked against git and the disk for LEAD's L-015 → coordination/reports/blender/ready_cards_l015.md (18 exported or reported; B-172 alone still owes an export, on U-151; B-190's puffs removed by D-190, B-184's redrawn by B-238).
- B-231's export path WRITTEN, NOT RUN (01:0x, files only; nothing exported, no manifest row): build_surveyor_v5.py gained export(art) / keys() (the kit path) and export_checks (sheet <= 2048; no part's paint on its rect's outermost row or column; per facing one root, every bone's part and parent present, the blink part on the sheet). sheet() now packs with the contract's 4 px gutter (it drew 2 px; ships/pilgrim/rig packs 4): the part sheet's LAYOUT and the json rects change on the next run, no part's pixels do. ON THE OWNER'S YES + LEAD's word: (1) add the manifest row {"key": "characters/surveyor_v5/rig", "kit_set": true, "generator": "scripts/build_surveyor_v5.py", "numpy_only": true, "review_name": "b231_surveyor_v5"}; (2) locks, RAM, then `tools/blender_render.ps1 characters/surveyor_v5/rig` with heavy_blender.lock held by hand (a kit row takes the light path); a check failure writes nothing: fix the part's canvas and re-run; (3) look at the stamped review's part-sheet row at 2x; (4) commit rig_color.png + rig.json by explicit list, 0 .meta; (5) tell UNITY (U-199) the key and that rects are bottom-left with a 4 px gutter. The untested risk is a first-run error in the new functions (they only add to the file; preview() is untouched apart from the gutter).
- B-242 (EXPORTED 068a2918, in Review until UNITY's wiring; LEAD approved the import 00:1x) = terrain/earth/back_wall_sand and terrain/mars/back_wall_basalt; sheet blender/preview/review_b242_back_wall_variants_preview.png + crop_b242_{sand,basalt}_{row,3x,shaft}.png. Only if a capture asks for a change: edit blender/scripts/build_back_wall_v3.py (draw_tier's "sand" / "basalt" branches, tier_colours' VARIANT_BASE), then `tools/blender_locked.ps1 -Job .. -PyArgs blender/scripts/build_back_wall_v3.py,--proof,Assets/_Game/Art,blender/preview/b242_proof -CapMB 900` (the tiers' 20 exported tiles must stay byte-identical: last run 00:04, all identical), then `... --variants,blender/preview/review_b242_back_wall_variants_preview.png`, then the crops (crop_png.py boxes: rows 0 28 1600 576 and 0 1378 1600 1926; 3x tiles 10 600 778 1368 and 10 1950 778 2718; shafts 788 600 1600 1368 and 788 1950 1600 2718).; a re-export needs LEAD's ACCEPTED on the new sheet first.
RAM: 0.9-1.2 GB free before the restart with nothing running; 1.01 GB at 00:54 while the three new sessions start (gate 1.5). My floor: nothing under 0.3 GB free; a light numpy run is fine above it. UNITY's 8.5-minute capture needs a quiet machine and its own gate: it gets the first quiet slot; yield on its want; nothing of mine beside its lock.

The giants' close view (B-239, B-240, B-241: Done or complete on my side; previews only, NOTHING exported):
- One table: blender/scripts/giants_v3.py (GIANTS, NIGHT, SHADE, RIM, MARKS, close_json). build_discs_v3 paints the far discs from it. After ANY change to either: `build_discs_v3.py --b239 Assets/_Game/Art blender/preview/b239 giants` (3 min) and `... blender/preview/b239_inner inner` (40 s): 16 pngs and 9 jsons must stay byte-identical to the exported files (last 23:53 / 23:56: all identical). Report: reports/blender/b239_belt_table.md.
- The previewer: blender/scripts/build_giant_close_v3.py (`<sheet png> <giant>`, or `<png> jupiter --motion`). Accepted sheets: blender/preview/review_b240_jupiter_close_preview.png, review_b241_{saturn,uranus,neptune}_close_preview.png, review_b241_jupiter_motion_preview.png; strips and close.json drafts in blender/preview/b240/ and b241/.
- The design note LEAD cards UNITY's half from: reports/blender/b237_limb_band_design.md, sections 10 (rulings, the key list, the flight's closest zoom 6-9: no zoom stepping) and 11 (the contract's 11.5.1).
How I run: locks listed, then RAM read, each in its own call; `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n>` for numpy sheets, proofs and crops (`blender/scripts/crop_png.py <src> x0 y0 x1 y1 k <dst>`, several per call; it refuses beside my OWN want: delete the want first); `tools/blender_render.ps1 <key or comma list>` for exports. UNITY and I take turns one job each while both have wants (D-037): on want_unity.lock finish the job I am on, yield, file mine (Write tool) only once UNITY HOLDS the lock, poll with the want refreshed. Beside a UNITY probe or capture lock: file edits only.
- Rulings that stand: D-190 = ONE cream puff per planet tinted by the dug cell's fill tone ("tone_hex"). A variant wall takes the fill's MAIN TONES, a tier wall its largest one. The soft limb stays shelved (build_disc's default is off). B-231: the shadow band on each part's BACK edge, crouch <= 0.98 m. B-233's keys by PoiDef label (D-187). continue_rows only at cover >= 0.90. The walls keep their grain (no format change came of U-207: the cost was the Editor's Direct3D 12).
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun. Waiting on others: B-207 on PawsOnTheGround; B-204 on UNITY's capture; B-172 on U-151.

## Last completed
- 11-10 00:5x (session 13's resume): the Ready-card check for L-015 (reports/blender/ready_cards_l015.md; nothing run, nothing exported).
- 11-10 00:07-00:09: **B-242 EXPORTED** 068a2918 (terrain/earth/back_wall_sand, terrain/mars/back_wall_basalt: 4 files, 0 .meta; the tiers' tiles not rewritten).
- 11-10 00:03-00:05: B-242 rev 3 (the warm sand wall, the basalt's stacked segments), the 20-tile proof again → ACCEPTED.
- 11-09 23:57 to 11-10 00:01: B-242's source, proof and first three runs (187dc733).
- 11-09 23:26-23:56: B-241 (Saturn with rings, Uranus, Neptune's tapered streak, Jupiter's motion check: all accepted as previews), the design note's sections 10-11, both far-disc proofs again (b11032ac, 187dc733).
- 11-09 22:03-23:13: B-239 Done, B-240 Done (the shared belt table; far discs byte-identical; Jupiter's close view).
- Earlier on 11-09 (B-220, B-223, B-224, B-225, B-228, B-229, B-230, B-232, B-233, B-238 exported or Done; the 0.6.2 smoke read; B-231 rounds 2 / 2b): coordination/status/archive/BLENDER_2026-11-09.md.

## Ready for review
- With the owner: B-231 (blender/preview/review_b231_surveyor_v5_design.png and the crop_b231_* crops; LEAD's C5 page, USER-39).
- In Review until UNITY's import and captures: B-224, B-223, B-225, B-233, B-242.
- B-189 / B-185 (waiting on U-159's captures): review_b141_mars_{canyon,storm,plains}(_dip).png, review_b152_venus_surface(_dip).png, review_b149_mercury_{day,twilight,night}_dip.png.

## Handoffs (unrouted only)
- -> UNITY (B-242, 068a2918; sent to UNITY and LEAD 00:09): terrain/earth/back_wall_sand goes behind ground_fill_sand, terrain/mars/back_wall_basalt behind ground_fill_basalt; json "variant" and "fill" name them; mapped as the tiers' walls.
- -> UNITY (the giants' close view, when carded): blender/preview/b240/jupiter_close.json and b241/*_close.json are the drafts of what it reads; the mapping is the design note's sections 5 and 10 and build_giant_close_v3.close_view / ring_layer.
- -> UNITY (B-220, in reports/blender/b220_continue_rows.md): venus/deck layer2's y_m is -1.5; Neptune storm / spot layer0's core under the rim at the tile's x 1024.
- -> UNITY (U-164 / U-159): continue_rows 64 = a layer's bottom 64 rows tile vertically; the ground-set depths (480 at y_m -2.0; 544 at y_m -3.0 with ground_row 352); the variant band, fill and lip keys.
- -> UNITY (U-150): vapor_cone / shock_ring pivots = the ship's centre of mass; speed_lines 128x360 for the LEFT edge; puff_boost a drop-in for ships/pilgrim/puff.

## Blockers
none. Waiting on: the owner's word on B-231 (USER-39) and the restart (USER-42); U-151 (B-172's export), U-152 (B-174).

## Proposals (undecided only)
- none open.

## Rules I keep (from slips)
- One lock <= 15 min; a painted planet with more than 8 scenes gets its own lock.
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs, and every file change goes through the edit tools, appends and deletions included (a `git rm` waits for a clear folder; a commit of edited files is fine). A lock listing is read in an EARLIER call than any write or run.
- Never a bare `python` in a shell line (it hung in the background): the only interpreter is Blender's bundled one through blender_locked.ps1. Never pipe the helper into `Select-Object -First n`.
- Before sending a sheet, look at every new shape at 2x-4x for faces and for what else it could be: two ringed dots side by side or in one outline; three dots in a triangle; a ring of an eye's size at an eye's height; ONE round window or dial on a rounded body or a box; a chain of crisp blobs (a grub); ringed pits on jointed panels (riveted plates); identical dot trails (a stamped glyph); a bright accent on small ovals (gold beads). Fix, re-run, look again.
- A first run is not a sheet: measure it against the card's numbers and look at it before sending.
- A change to a builder whose art is exported is proven by rebuilding what it exports and comparing bytes with the exported files, before and after (B-239 found the shelved soft limb still on by default; B-242's proof ran twice).
- Before deleting art on another role's word, read the code and tests that could ask for it. A re-export for one changed piece: `git status` must show only the intended files before the commit.
- A manifest row's key has three parts. No 2>&1 on the wrappers in PowerShell 5.1.
- A want is filed only once the other role HOLDS the lock (D-039); refresh it each poll; never end a turn on a want. No background waiters.
- All three sessions share one working tree: a push can race another role's (fetch, never rebase, push again); commit by explicit file paths, check git show --stat, 0 .meta.

## For USER_ACTIONS
none of mine (LEAD's: USER-39 the C5 surveyor look-over, USER-41 Build 0.6.2, USER-42 the restart).

## HeavyJobLock
none held (last: 00:07:42-00:08:13, B-242's export; 00:04:11-00:05:06 its proof, sheet rev 3 and crops). No want on file. No background waiters.
