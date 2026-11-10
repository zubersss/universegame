# BLENDER STATUS
Updated: 2026-11-09 23:1x · Session: 12 (resumed 14:03 after the owner's restart; THIS SESSION = zuber-4d; LEAD = zuber-d1, UNITY = zuber-a0) · older: coordination/status/archive/BLENDER_2026-11-09.md (session 12's closed entries are there), BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**00:0x (11-10) — RESUME HERE: B-242's sheet is WITH LEAD (sent 00:02; source 187dc733).** B-242 = back walls for the two surface-variant fills, terrain/earth/back_wall_sand and terrain/mars/back_wall_basalt, as B-230's tiles: blender/preview/review_b242_back_wall_variants_preview.png (the third run) and crop_b242_*.png. The tiers' 20 exported tiles still rebuild byte-identical (`build_back_wall_v3.py --proof Assets/_Game/Art blender/preview/b242_proof`: run it again after ANY change to that builder). On LEAD's ACCEPTED: `tools/blender_render.ps1 terrain/common/back_walls_variants` (a kit row: list the folder and read RAM first, hold heavy_blender.lock by hand around it), then `git status` must show only the 4 new files under Assets/_Game/Art/terrain/{earth,mars}/ (back_wall_sand / back_wall_basalt .json + _color.png); commit by explicit list, 0 .meta; tell UNITY the two keys (json "variant" and "fill") and LEAD the hash. On a round instead: fix, re-run `--variants`, re-cut the crops (crop_png.py: the rows 0 28 1600 576 and 0 1378 1600 1926; the 3x tiles 10 600 778 1368 and 10 1950 778 2718; the shafts 788 600 1600 1368 and 788 1950 1600 2718), look at 3x, send.
B-241 is complete on my side (all four giants' close views accepted as previews; both far-disc proofs re-run 23:53 / 23:56: all byte-identical; LEAD has the line). UNITY's quiet-machine probes are over (23:58); it still wants one capture lock of about 8.5 min and a short check tonight: one light job a turn, yield on its want.
The close view's state, for reference (nothing of it is exported until its UNITY half is carded, after U-207 / U-197): sheets blender/preview/review_b240_jupiter_close_preview.png, review_b241_{saturn,uranus,neptune}_close_preview.png, review_b241_jupiter_motion_preview.png; the design note reports/blender/b237_limb_band_design.md sections 10-11 are what LEAD cards UNITY's half from. B-241's card as it was given:
B-240 is DONE (Jupiter's close view ACCEPTED: blender/preview/review_b240_jupiter_close_preview.png). B-241, one sheet a giant, each to LEAD as it lands:
- **Saturn**: five belts, the three ring bands with a `ring_edge` strip, the back half behind the globe and the front half over it (close.json "rings"); **Uranus**: belt_edge's variant 1 (NOTE for LEAD: the far disc draws Uranus's belts LEVEL, there is no tilt in build_discs_v3: the close view follows the far disc); **Neptune**: the dark storm and its companion cloud: two shapes side by side, so look at them at 2x for a face. Each at the swap (6 px per far texel) and at the closest zoom (12) over the far disc magnified the same.
- **The motion check B-240 left out**: two frames of Jupiter a few ticks apart (frames 0 and 3), the close view over the far disc's own frames.
- **The design note** (reports/blender/b237_limb_band_design.md) updated with LEAD's rulings and the 11.5.1 text: the close view follows the far limb's lumpy "rim"; a 128x128 pigment tile per giant; limb_band WITHOUT its inner shade (512x16); the ink's 2-3 px is the line's MEAN across root-2 steps with the far disc's hand jitter on top; the outline's jump at the swap (15 soft px to 2.5) accepted; the ink marks placed by close.json's ink_marks.
- Source: blender/scripts/build_giant_close_v3.py (`tools/blender_locked.ps1 -Job .. -PyArgs blender/scripts/build_giant_close_v3.py,blender/preview/review_b241_<giant>_close_preview.png,<giant> -CapMB 1200`, about 1 min a sheet). Nothing is exported until the UNITY half is carded (after U-207 / U-197). One light job a turn; yield on UNITY's want (its U-205 check and U-207 trial want about 15 minutes of locks tonight).
- The shared table: blender/scripts/giants_v3.py (GIANTS, NIGHT, SHADE, RIM, MARKS, close_json). build_discs_v3 reads it. After ANY change to either, re-run both proofs: `build_discs_v3.py --b239 Assets/_Game/Art blender/preview/b239 giants` (3 min) and `... blender/preview/b239_inner inner` (40 s): 16 pngs and 9 jsons must stay byte-identical to the exported files (last run 23:06 / 23:09: all identical). Report: reports/blender/b239_belt_table.md.
Also open:
1. **A look step from LEAD (not a card):** UNITY will capture each planet's backdrop set in BC7 beside DXT5 with a 4x crop of its smoothest gradient; I look for banding or blocky grain (Venus's haze, the giants' deep decks, the starfield, Mercury's night) and tell LEAD which set and by how much. No art change is planned. Wait for the captures' paths.
2. **B-231** (the v5 surveyor) is in Review with the OWNER (LEAD's C5 page, USER-39). A yes = export the part sheet + bone JSON and B-234 / B-235 / B-236 promoted; a "change X" = round 3. NO export and no C5 companion source until then.
3. Build 0.6.2 is out (USER-41). The smoke read is closed (reports/blender/smoke_read_0.6.2.md); LEAD routed G1-G12; nothing of it is mine to draw unless LEAD cards it (G4's T2 pebbles, G9's hematite tone).
How I run: locks listed, then RAM read, each in its own call (RAM sat at 1.3-2.4 GB tonight; nothing under 0.3 GB); `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n>` for numpy sheets and crops (`blender/scripts/crop_png.py <src> x0 y0 x1 y1 k <dst>`, several per call; it refuses beside my OWN want: delete the want first, in the same call as the run once a listing has shown the folder clear); `tools/blender_render.ps1 <key or comma list>` for exports (a single kit / painted row may take its light path: hold heavy_blender.lock by hand). UNITY and I take turns one job each while both have wants (D-037): on want_unity.lock finish the job I am on, yield, file mine (Write tool) only once UNITY HOLDS the lock, poll with the want refreshed.
- Rulings that stand: D-190 = ONE cream puff per planet tinted by the dug cell's fill tone ("tone_hex" on every ground fill json). The giants' close view (B-237 option C): rings in the same card, the grain a screen-space tile, the far / close swap a cut on a 12 Hz tick; the soft limb stays shelved (build_disc's default is off). B-231: the shadow band on each part's BACK edge, crouch <= 0.98 m with the 0.92 root squash. B-233's keys by PoiDef label (D-187). The band rule: continue_rows only at cover >= 0.90. The walls keep their grain (their cost was the BC7 format).
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun. Waiting on others: B-207 on PawsOnTheGround; B-204 on UNITY's capture; B-172 on U-151.

## Last completed
- 11-09 23:57 to 11-10 00:01: B-242's source, the tiers' 20-tile byte proof, the sheet (three runs: shells larger and pebbles grey-tan; the basalt's rivet read and stamped trails removed) → to LEAD (187dc733).
- 11-09 23:45-23:56: Neptune's tapered streak (accepted on the 1:1 frame); both far-disc proofs again, all byte-identical; the design note's point 11 (the flight's closest zoom 6-9).
- 11-09 23:26-23:39: B-241's four sheets (Saturn with rings: accepted; Uranus; Neptune, its cloud as one streak after the 2x face look; Jupiter's two-frame motion check: 40.4 % / 41.2 % of pixels changed, close / far) and the design note's sections 10-11 (b11032ac) → to LEAD.
- 11-09 22:39-23:13: B-240 (1) the inner set byte-identical (3633d54d); B-240 (2) Jupiter's strips and close-view preview, two runs, the ink marks lifted into the shared table and both proofs re-run (5e4d8010) → to LEAD.
- 11-09 22:03-22:33: B-239 Done (the shared belt table; far discs byte-identical before and after; the soft-limb default fixed).
- Earlier today (B-220, B-223, B-224, B-225, B-228, B-229, B-230, B-232, B-233, B-238 exported or Done; the 0.6.2 smoke read; B-231 rounds 2 / 2b): coordination/status/archive/BLENDER_2026-11-09.md.

## Ready for review
- With LEAD: B-242's sheet (the sand and basalt back walls).
- Accepted as previews (LEAD 23:3x-23:4x): all four giants' close views and Jupiter's motion check; the two proofs done.
- With the owner: B-231 (blender/preview/review_b231_surveyor_v5_design.png and the crop_b231_* crops).
- In Review until UNITY's import and captures: B-224, B-223, B-225, B-233.
- B-189 / B-185 (waiting on U-159's captures): review_b141_mars_{canyon,storm,plains}(_dip).png, review_b152_venus_surface(_dip).png, review_b149_mercury_{day,twilight,night}_dip.png.

## Handoffs (unrouted only)
- -> UNITY (the giants' close view, when carded): blender/preview/b240/jupiter_close.json is the draft of what it would read (belts, edge_wobble, rim, night, storms, ink_marks, swap); the mapping is the design note's section 5 and build_giant_close_v3.close_view.
- -> UNITY (B-220, in reports/blender/b220_continue_rows.md): venus/deck layer2's y_m is -1.5; Neptune storm / spot layer0's core under the rim at the tile's x 1024.
- -> UNITY (B-203 / B-204 / B-207, sent to LEAD 11-08): ground_fill_t<n> json tier / depth_m / transition_m 1.0; surface_line row 40 = pivot; ui/skilltree chart json ring_r_px / branch_axis_deg / slots_deg, emblem_r_px 408; node icons at 40 px, 0.4 alpha when locked; vent_eel contact 0 px.
- -> UNITY (U-164 / U-159): continue_rows 64 = a layer's bottom 64 rows tile vertically; the ground-set depths (480 at y_m -2.0; 544 at y_m -3.0 with ground_row 352); variant keys ground_band_{frost,basalt,talus,ice,tessera,vent}, ground_fill_basalt, the lips.
- -> UNITY (U-150): vapor_cone / shock_ring pivots = the ship's centre of mass; speed_lines 128x360 for the LEFT edge; puff_boost a drop-in for ships/pilgrim/puff.

## Blockers
none. Waiting on: LEAD's judgement of B-240 (2); the owner's word on B-231; U-151 (B-172's export), U-152 (B-174).

## Proposals (undecided only)
- none open (LEAD ruled B-241's two: Neptune's cloud a tapered streak in the close view; Uranus level, no tilt asked).
- B-231: the blink's skin patch shows as a faint ring at 4x on the shaded face; LEAD: leave it unless it shows at 1x.

## Rules I keep (from slips)
- One lock <= 15 min; a painted planet with more than 8 scenes gets its own lock.
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs, and every file change goes through the edit tools, appends and deletions included (a `git rm` waits for a clear folder; a commit of edited files is fine). A lock listing is read in an EARLIER call than any write or run.
- Never a bare `python` in a shell line (it hung in the background, 22:32): the only interpreter is Blender's bundled one through blender_locked.ps1. Never pipe the helper into `Select-Object -First n`.
- Before sending a sheet, look at every new shape at 2x-4x for faces: two ringed dots side by side or in one outline; a dark chip beside a pit; three dots in a triangle; a dot between two lines; a ring of an eye's size at an eye's height; a hooked post with a pale dot and a wedge; two lit panes under a dark cap; ONE round window or dial on a rounded body or a box. Fix, re-run, look again.
- A first run is not a sheet: measure it against the card's numbers and look at it before sending (B-238's 0.39 m; B-231's crouch; B-225's lost light; B-240's dashes on the strip's rhythm and an outline invisible on a dark ground).
- A refactor of a builder is proven by rebuilding what it exports and comparing bytes with the exported files, BEFORE and AFTER (B-239: the before run found the shelved soft limb still on by default).
- Before deleting art on another role's word, read the code and tests that could ask for it. A re-export for one changed piece: `git status` must show only the intended files before the commit.
- A manifest row's key has three parts. No 2>&1 on the wrappers in PowerShell 5.1.
- A want is filed only once the other role HOLDS the lock (D-039); refresh it each poll; never end a turn on a want. No background waiters.
- All three sessions share one working tree: a push can race another role's (fetch, never rebase, push again); commit by explicit file paths, check git show --stat, 0 .meta.
- A stroke's line is drawn in its material's ink_hex; a fill-only material on an open stroke draws nothing; cream marks on a cream body draw nothing.

## For USER_ACTIONS
none (the owner's look at B-231 is LEAD's USER-39; 0.6.2 is USER-41).

## HeavyJobLock
none held (last: 00:00:59-00:01:10, B-242's sheet rev 2 and crops; 23:57:31-23:58:01 the walls' proof; 23:53:04-23:56:53 the two far-disc proofs). No want on file. No background waiters. Nothing of mine ran beside UNITY's probe lock (23:46:32-23:52).
