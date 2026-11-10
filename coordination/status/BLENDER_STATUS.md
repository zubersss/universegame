# BLENDER STATUS
Updated: 2026-11-10 01:1x · Session: 13 (resumed 11-10 00:52 after the windows' restart; THIS SESSION = zuber-e2; LEAD = zuber-36; UNITY = zuber-57 by elimination, not yet heard from; the laptop itself was not rebooted) · older: coordination/status/archive/BLENDER_2026-11-09.md (session 12's closed entries), BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**01:1x — RESUME HERE: B-246 (the art of the dig as one motion, D-196, from the owner's 0.6.2 playtest) IS THE TOP CARD, started 01:1x; SHEET 1 (the body) FIRST, to LEAD, before any time goes into the fx. B-243 (the giants' close-view export) is behind it: its source is written and NOT RUN, its one Jupiter sheet goes in a spare slot. Nothing is exported for either.**
- B-246 sheet 1 = (a) dig_down / dig_fwd / dig_up, five drawings each at 12 fps: wind-up, CONTACT on drawing 2 (index 1; the arm at full reach, the body's weight in it), follow-through, settle, a recover that meets idle; the front hand EMPTY, hand_socket per frame, json "contact": 1; (b) the Beam's aim_up / aim_up45 / aim_fwd / aim_down45 / aim_down, two drawings each, the arm along its direction, hand_socket per frame; (c) a carry socket for idle, walk and run (the tool low at the side). The sheet: the clips as strips at 1x and 2x with the shovel on the socket and its blade tip (1.33 m from the grip) on a marked contact point, a near and a far target a direction, beside idle; the aim poses with the Beam on the socket and a ray. Tell LEAD from the pose maths how far the blade honestly reaches in each direction (LEAD expects about 1.6 m). My call to state: a new sheet key (characters/surveyor/side_dig) or side_b rewritten.
- B-246 sheet 2 (after sheet 1 is judged): fx/dig_reticle (brackets on a circle of any radius and on a 1 m cell, a two-drawing boil; in reach / clamped / nothing to dig), fx/dig_chip (three crack stages, a round and a cell decal, cream + ink, tone_hex), fx/beam_contact (six drawings, glow and grit; a mining tool, never a gun), fx/shovel_swish (three drawings). Previews only until ACCEPTED.
- B-243 as it stands: LEAD RULED 7.5 strip texels per far texel on my desk-check (the previewer had stepped the scale by root 2: the accepted sheets drew 6 / 8.49 / 12). In source, NOT RUN: giants_v3.STRIP_SCALE 7.5 + strips_json (close.json gains "strips"); build_giant_close_v3: strip_scale(m, k) = m / k from the json, a dash's ink collected (stats), VIEWS at 6 / 7.7 / 9, kit / export_checks / export / keys / export_review; build_giant_close_export_v3.py (the kit wrapper); the manifest row planets/common/close_view. ITS STEPS, each under my own lock and only when UNITY has no lock and no want: (1) ONE sheet `tools/blender_locked.ps1 -Job "B-243 Jupiter fixed-scale sheet" -PyArgs blender/scripts/build_giant_close_v3.py,blender/preview/review_b243_jupiter_close_preview.png,jupiter -CapMB 900`: the printed limb and dash widths at 6 and 9 against 2.00-3.00 and 1.00-1.50, a look at 2x, to LEAD; WAIT for ACCEPTED. (2) both far-disc proofs (`build_discs_v3.py --b239 Assets/_Game/Art blender/preview/b239 giants`, then `... blender/preview/b239_inner inner`: 16 pngs + 9 jsons byte-identical). (3) `tools/blender_render.ps1 planets/common/close_view`, heavy_blender.lock held by hand (a kit row = the light path); a failed check writes nothing. (4) the proofs again; hashes into reports/blender/b239_belt_table.md. (5) `git status`: ONLY new files (10 pngs + 10 jsons + 4 close.json), 0 .meta; explicit list; git show --stat; LFS. (6) one message to UNITY (keys, close.json's fields, "strips"), LEAD the hash, credits; Review "waits for: U-208's captures".
- Open with UNITY (asked 01:0x): how a json-only key (planets/<giant>/close.json) passes ArtImporter and any field name it would rather read. Precedents on disk: props/rig/hand_socket.json (ArtSockets.cs), planets/saturn/disc_rig.json.
- B-231's export path WRITTEN, NOT RUN (4d4293b2; no manifest row): build_surveyor_v5.py has export / keys / export_checks; sheet() packs with the contract's 4 px gutter (it drew 2 px): layout and rects change on the next run, no part's pixels. ON THE OWNER'S YES (USER-39) + LEAD's word: add the manifest row (its text is in the script's docstring), `tools/blender_render.ps1 characters/surveyor_v5/rig` under a hand-held lock, look at the part-sheet row at 2x, commit rig_color.png + rig.json by explicit list, tell UNITY (U-199) the key, bottom-left rects, the 4 px gutter.
- Also waiting: U-151 (B-172's export, Blocked); B-245 (the 0.6.3 smoke read: Blocked on that smoke; its skeleton may be written any time); B-242 (exported 068a2918, in Review on UNITY's wiring; a change would need a new sheet and LEAD's ACCEPTED: build_back_wall_v3.py's "sand" / "basalt" branches, then its --proof).
RAM: 1.01 GB at 00:54 while the sessions started, 1.90 GB at 01:01 (LEAD); UNITY's Direct3D 11 capture lock since 01:02. My floor: nothing under 0.3 GB free. UNITY's captures need a quiet machine: nothing of mine beside its lock; yield on its want.

How I run: locks listed, then RAM read, each in its own call; `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n>` for numpy sheets, proofs and crops (`blender/scripts/crop_png.py <src> x0 y0 x1 y1 k <dst>`, several per call; it refuses beside my OWN want: delete the want first); `tools/blender_render.ps1 <key or comma list>` for exports. UNITY and I take turns one job each while both have wants (D-037): on want_unity.lock finish the job I am on, yield, file mine (Write tool) only once UNITY HOLDS the lock, poll with the want refreshed. Beside a UNITY lock: file edits only.
- The giants: one table blender/scripts/giants_v3.py; after ANY change to it or build_discs_v3 the two far-disc proofs must stay byte-identical (last 11-09 23:53 / 23:56; OWED again before B-243's export: giants_v3 changed 01:0x). The design note: reports/blender/b237_limb_band_design.md (sections 10-11; contract 11.5.1 is now LEAD's text, v3.4).
- Rulings that stand: D-190 = ONE cream puff per planet tinted by the dug cell's fill tone ("tone_hex"). A variant wall takes the fill's MAIN TONES, a tier wall its largest one. The soft limb stays shelved. B-231: the shadow band on each part's BACK edge, crouch <= 0.98 m. B-233's keys by PoiDef label (D-187). continue_rows only at cover >= 0.90.
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun. Waiting on others: B-207 on PawsOnTheGround; B-204 on UNITY's capture.

## Last completed
- 11-10 01:0x-01:1x: B-243's desk-check (LEAD ruled 7.5) and its source (not run); B-231's export path in source (4d4293b2, not run).
- 11-10 00:5x (session 13's resume): the Ready-card ledger for L-015 (reports/blender/ready_cards_l015.md, d893569e): LEAD closed 5 cards, 13 to Review, B-172 Blocked.
- 11-10 00:07-00:09: **B-242 EXPORTED** 068a2918 (terrain/earth/back_wall_sand, terrain/mars/back_wall_basalt: 4 files, 0 .meta).
- 11-09 22:03-23:56: B-239 Done, B-240 Done, B-241 Done (the shared belt table; far discs byte-identical; all four giants' close-view previews).
- Earlier on 11-09: coordination/status/archive/BLENDER_2026-11-09.md.

## Ready for review
- With the owner: B-231 (blender/preview/review_b231_surveyor_v5_design.png and the crop_b231_* crops; LEAD's C5 page, USER-39).
- In Review until UNITY's import and captures: B-224, B-223, B-225, B-233, B-242.
- B-189 / B-185 (waiting on U-159's captures): review_b141_mars_{canyon,storm,plains}(_dip).png, review_b152_venus_surface(_dip).png, review_b149_mercury_{day,twilight,night}_dip.png.

## Handoffs (unrouted only)
- -> UNITY (B-242, 068a2918; sent 00:09): terrain/earth/back_wall_sand goes behind ground_fill_sand, terrain/mars/back_wall_basalt behind ground_fill_basalt; json "variant" and "fill" name them; mapped as the tiers' walls.
- -> UNITY (B-220, in reports/blender/b220_continue_rows.md): venus/deck layer2's y_m is -1.5; Neptune storm / spot layer0's core under the rim at the tile's x 1024.
- -> UNITY (U-164 / U-159): continue_rows 64 = a layer's bottom 64 rows tile vertically; the ground-set depths (480 at y_m -2.0; 544 at y_m -3.0 with ground_row 352); the variant band, fill and lip keys.
- -> UNITY (U-150): vapor_cone / shock_ring pivots = the ship's centre of mass; speed_lines 128x360 for the LEFT edge; puff_boost a drop-in for ships/pilgrim/puff.

## Blockers
none. Waiting on: UNITY's capture lock (01:02) before any run; the owner's word on B-231 (USER-39); U-151 (B-172's export).

## Proposals (undecided only)
- none open.

## Rules I keep (from slips)
- One lock <= 15 min; a painted planet with more than 8 scenes gets its own lock.
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs, and every file change goes through the edit tools, appends and deletions included (a `git rm` waits for a clear folder; a commit of edited files is fine). A lock listing is read in an EARLIER call than any write or run.
- Never a bare `python` in a shell line (it hung in the background): the only interpreter is Blender's bundled one through blender_locked.ps1. Never pipe the helper into `Select-Object -First n`.
- Before sending a sheet, look at every new shape at 2x-4x for faces and for what else it could be: two ringed dots side by side or in one outline; three dots in a triangle; a ring of an eye's size at an eye's height; ONE round window or dial on a rounded body or a box; a chain of crisp blobs (a grub); ringed pits on jointed panels (riveted plates); identical dot trails (a stamped glyph); a bright accent on small ovals (gold beads). Fix, re-run, look again.
- A first run is not a sheet: measure it against the card's numbers and look at it before sending.
- A change to a builder whose art is exported is proven by rebuilding what it exports and comparing bytes with the exported files, before and after.
- Before deleting art on another role's word, read the code and tests that could ask for it. A re-export for one changed piece: `git status` must show only the intended files before the commit.
- A manifest row's key has three parts. No 2>&1 on the wrappers in PowerShell 5.1.
- A want is filed only once the other role HOLDS the lock (D-039); refresh it each poll; never end a turn on a want. No background waiters.
- All three sessions share one working tree: a push can race another role's (fetch, never rebase, push again); commit by explicit file paths, check git show --stat, 0 .meta.
- A previewer is checked against a ruled number BEFORE its export is planned (B-243: the sheets had been accepted on a stepped scale the ruling had removed).

## For USER_ACTIONS
none of mine (LEAD's: USER-39 the C5 surveyor look-over, USER-41 Build 0.6.2).

## HeavyJobLock
none held (last: 11-10 00:07:42-00:08:13, B-242's export). No want on file. No background waiters. Nothing has run in session 13.
