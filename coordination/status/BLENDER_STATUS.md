# BLENDER STATUS
Updated: 2026-11-10 05:5x · Session: 13 (resumed 11-10 00:52; every session stopped 02:24-05:55, the owner said "continue work"; THIS SESSION = zuber-e2; LEAD = zuber-36; UNITY = zuber-57) · older: coordination/status/archive/BLENDER_2026-11-09.md (session 12's closed entries), BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**05:5x — RESUME HERE: B-246 (the art of the dig as one motion, D-196) is open ONLY for SHEET 2 (fx/dig_reticle, fx/dig_chip round + cell, fx/beam_contact, fx/shovel_swish). Its body half is EXPORTED and verified by LEAD (56bbfa4d). Sheet 2 has run twice (02:11, 02:23: problems none) and has NOT been sent: my own look at run 2's crops, a revision if they need one, then LEAD. Nothing of sheet 2 is exported. Then B-247 (three art findings; on the board).**
- Sheet 2, step by step (locks listed, then RAM, each its own call; UNITY will want a check lock: yield to its want): (1) look at blender/preview/crop_b246fx_{reticle,chips_soil,chips_stone,beam,swish}.png (run 2, 02:24); every new shape at 2x-4x for faces and for what else it could be. (2) fix in blender/scripts/build_dig_feel_v3.py; `tools/blender_locked.ps1 -Job "B-246 sheet 2" -PyArgs blender/scripts/build_dig_feel_v3.py,blender/preview/review_b246_dig_fx_preview.png -CapMB 900` (8 s, peak 206 MB); crops with crop_png.py (rows: reticle 30-570, chips on soil 570-974, on stone 974-1378, beam 1378-1590, swish 1590-2314). (3) send LEAD the sheet: the reticle's three states on soil and stone at 1x (round and cell), the chip stages, the contact loop, the swish strips and the swish on side_dig's contact. (4) on ACCEPTED: add the manifest row {"key": "fx/dig_feel/kit", "kit_set": true, "generator": "scripts/build_dig_feel_v3.py", "numpy_only": true, "review_name": "b246_dig_fx"}, `tools/blender_render.ps1 fx/dig_feel/kit` with heavy_blender.lock held by hand (a kit row = the light path; ask UNITY not to file a want while it is up), `git status` only the ten new files (five pngs + five jsons), 0 .meta, explicit list, the keys to UNITY in one message, LEAD the hash, credits.
- What run 1's look already changed (in source, in run 2): flakes are uneven four-cornered slivers on stage 3 only (three-cornered ones read as arrowheads), cracks heavier at the contact, the cell decal has five cracks, the swish's two rows no longer overflow the sheet.
- B-246's body, DONE: characters/surveyor/side_dig (30 frames 192x192, 1956x584: dig_down / dig_fwd / dig_up / dig_fwd_near with "contact": 1 and slide_max 0.70 / 0.55 / 0.95 on fwd / up / near; five Beam aim holds; sockets.hand [x, z, angle rad] per frame; top-level carry (stowed, 125 deg, behind) and ready (the low pose)) and props/rig/grip_fist. Builder blender/scripts/build_surveyor_side_dig.py (its sheet: `<png>` = rev 2's rows, `--full` = all; `--entry` prints the manifest row; the sheet fails if the row differs from ENTRY). build_surveyor_v3.draw_surveyor took ONE pose key, front_arm (proof_surveyor_strokes.py: every stroke of side and side_b identical); render.py's do_v3_sheet passes a clip's contact / slide_max and a row's sockets_units / json_extra (side and side_b's jsons byte-identical on previews, 02:19).
- B-243 DONE ON MY SIDE: exported 3ff5e37e, in Review on U-208's captures. B-231's export path is written and NOT run (4d4293b2; no manifest row): ON THE OWNER'S YES (USER-39) + LEAD's word add the row (its text is in build_surveyor_v5.py's docstring), `tools/blender_render.ps1 characters/surveyor_v5/rig` under a hand-held lock, look at the part-sheet row at 2x, commit rig_color.png + rig.json by explicit list, tell UNITY (U-199).
- Also waiting: U-151 (B-172's export, Blocked); B-245 (the 0.6.3 smoke read: Blocked on that smoke); B-242 (exported 068a2918, in Review on UNITY's wiring).
RAM: 1.94 GB free at 05:55 (LEAD). My floor: nothing under 0.3 GB free. UNITY's captures and checks need a quiet machine: nothing of mine beside its lock; yield on its want.

How I run: locks listed, then RAM read, each in its own call; `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n>` for numpy sheets, proofs and crops (`blender/scripts/crop_png.py <src> x0 y0 x1 y1 k <dst>`, several per call; it refuses beside my OWN want: delete the want first); `tools/blender_render.ps1 <key or comma list>` for exports. UNITY and I take turns one job each while both have wants (D-037): on want_unity.lock finish the job I am on, yield, file mine (Write tool) only once UNITY HOLDS the lock, poll with the want refreshed. Beside a UNITY lock: file edits only.
- A slot of several light steps beside UNITY = ONE hand-held heavy_blender.lock in ONE call (the wrapper's light path and blender_locked both refuse beside another role's want), UNITY asked beforehand not to file while it is up and told the moment it is released. A heavy row (a v3 sheet) takes the wrapper's own lock.
- The giants: one table blender/scripts/giants_v3.py; after ANY change to it or build_discs_v3 both far-disc proofs must stay byte-identical (last 11-10 01:33 / 01:34, hashes in reports/blender/b239_belt_table.md).
- Rulings that stand: D-190 = ONE cream puff per planet tinted by the dug cell's fill tone ("tone_hex"). A variant wall takes the fill's MAIN TONES, a tier wall its largest one. The soft limb stays shelved. B-231: the shadow band on each part's BACK edge, crouch <= 0.98 m. B-233's keys by PoiDef label (D-187). continue_rows only at cover >= 0.90. The shovel's reach stays 2 m (my pose maths; LEAD withdrew 1.6).
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun. Waiting on others: B-207 on PawsOnTheGround; B-204 on UNITY's capture.

## Last completed
- 11-10 02:18-02:22: **B-246's body EXPORTED** 56bbfa4d (side_dig + grip_fist; render.py's pass-throughs proven; LEAD verified; the handoff to UNITY sent 02:2x).
- 11-10 01:46-02:10: B-246 sheet 1 (three runs) and rev 2 (four runs): LEAD accepted the direction, then rev 2 with four rulings.
- 11-10 01:28-01:36: **B-243 EXPORTED** 3ff5e37e (the giants' close view: 5 strips, the grain, 4 pigment tiles, 4 close.json).
- 11-10 00:5x: the Ready-card ledger for L-015 (d893569e): LEAD closed 5 cards, 13 to Review, B-172 Blocked.
- 11-10 00:07-00:09: **B-242 EXPORTED** 068a2918. Earlier: coordination/status/archive/BLENDER_2026-11-09.md.

## Ready for review
- With the owner: B-231 (blender/preview/review_b231_surveyor_v5_design.png and the crop_b231_* crops; LEAD's C5 page, USER-39).
- In Review until UNITY's import and captures: B-224, B-223, B-225, B-233, B-242, B-243 (U-208), B-246's body (U-209).
- B-189 / B-185 (waiting on U-159's captures): review_b141_mars_{canyon,storm,plains}(_dip).png, review_b152_venus_surface(_dip).png, review_b149_mercury_{day,twilight,night}_dip.png.

## Handoffs (unrouted only)
- -> UNITY (B-246, 56bbfa4d; sent 02:2x): side_dig's clips, contact, slide_max and how the slide is applied (the tool's pivot at glove - slide x its direction), sockets.hand in radians, carry / ready (the swing multiplies the front arm's own angle; the angle alone is fine), the fist over the tool at the socket; the look = review_b246_dig_body_rev2_preview.png.
- -> UNITY (B-243, 3ff5e37e; sent 01:3x): the ten texture keys, each strip's json, close.json's fields and "strips"; the mapping = b237_limb_band_design.md sections 5 and 10 + build_giant_close_v3.close_view / ring_layer.
- -> UNITY (B-242, 068a2918): terrain/earth/back_wall_sand behind ground_fill_sand, terrain/mars/back_wall_basalt behind ground_fill_basalt.
- -> UNITY (U-164 / U-159): continue_rows 64 = a layer's bottom 64 rows tile vertically; the ground-set depths; the variant band, fill and lip keys.

## Blockers
none. Waiting on: LEAD's judgement of sheet 2 once sent; the owner's word on B-231 (USER-39); U-151 (B-172's export).

## Proposals (undecided only)
- none open (the fist was accepted and exported).

## Rules I keep (from slips)
- One lock <= 15 min; a painted planet with more than 8 scenes gets its own lock.
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs, and every file change goes through the edit tools, appends and deletions included (a `git rm` waits for a clear folder; a commit of edited files is fine). A lock listing is read in an EARLIER call than any write or run.
- Never a bare `python` in a shell line (it hung in the background): the only interpreter is Blender's bundled one, through blender_locked.ps1 or by its full path inside a hand-held lock. Never pipe the helper into `Select-Object -First n`.
- Before sending a sheet, look at every new shape at 2x-4x for faces and for what else it could be: two ringed dots side by side or in one outline; three dots in a triangle; a ring of an eye's size at an eye's height; ONE round window or dial on a rounded body or a box; a chain of crisp blobs (a grub); ringed pits on jointed panels (riveted plates); identical dot trails (a stamped glyph); small three-cornered flakes (arrowheads); a bright accent on small ovals (gold beads); a glove over a nose. Fix, re-run, look again.
- A first run is not a sheet: measure it against the card's numbers and look at it before sending. A sheet's rows are checked against its width (two overflowed on 11-10).
- A change to a builder whose art is exported is proven by rebuilding what it exports and comparing bytes (or strokes) with the exported files, before and after.
- A previewer is checked against a ruled number BEFORE its export is planned (B-243). A reach or a range is computed from the pose maths before it is promised (B-246: 2.2 m, not 1.6; a slide of 0.95, not 0.55).
- Before deleting art on another role's word, read the code and tests that could ask for it. A re-export for one changed piece: `git status` must show only the intended files before the commit.
- A manifest row's key has three parts. No 2>&1 on the wrappers in PowerShell 5.1. A commit with nothing staged prints the whole tree's status: check `git status --short -- <my paths>` first.
- A want is filed only once the other role HOLDS the lock (D-039); refresh it each poll; never end a turn on a want. No background waiters.
- All three sessions share one working tree: a push can race another role's (fetch, never rebase, push again); commit by explicit file paths, check git show --stat, 0 .meta.

## For USER_ACTIONS
none of mine (LEAD's: USER-39 the C5 surveyor look-over, USER-41 Build 0.6.2).

## HeavyJobLock
none held (last: 11-10 02:23:40-02:24:05, sheet 2's run 2 and its crops). No want on file. No background waiters.
