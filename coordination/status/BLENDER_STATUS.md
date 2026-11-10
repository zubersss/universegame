# BLENDER STATUS
Updated: 2026-11-10 14:5x · Session: 14 (all three windows restarted after the 14:18 reboot; THIS SESSION = zuber-59; LEAD = zuber-4a; UNITY = zuber-30) · older: coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**14:5x — RESUME HERE: B-258 PART 3, THE FRAME (art v7, the living painting, D-205; READ docs/STYLE_V7.md FIRST). LEAD's ruling 14:1x stands: the camp's stage from scans as PIECES COMPOSED (never one 2-megapixel render): far veils (a small stand through the filter, enlarged: soft is right), a middle thicket, near plants, a trunk with roots, mossy rocks, a ground strip and dug earth from scanned ground textures, haze by depth, ONE colour key, a warm pool of light with cool shade round it; A PAINTER'S LIGHT (fewer flatter values, a designed shadow shape, coloured bounce, matt); VEINS AND GRAIN AS STROKES in two values; a FOREGROUND layer at 2-3x life size from the 384 source; the frame TWICE (the play plane at 96 and at 128 px per metre); plants up to x3; a grey 1.84 m mannequin; ONE sheet, the pass that reads, my own read. Gate: 1.9 GB free, watchdog 1.3 GB, peaks reported. NOTHING exported to Assets. THEN part 2 (the figure: DATA ONLY, Blender Studio's CC0 base meshes + Rigify, no add-on on the owner's machine without the owner's word, ONE probe frame sets its gate; keyed from `build_surveyor_frames_v6.py`'s pose tables). THEN LEAD's new cards (14:3x, 2cccaa34): B-262 the pilot MOVING (Blocked until the frame is accepted; say its cost first); FILES ONLY at any time: B-260 (a) sent (below), B-263 the price list (v7_price_list.md), B-259's (the underground pilot) and B-261's (the kit and tools as 3D) sources. B-252 .. B-256 Blocked under D-205.**
- **WHERE THE FRAME STANDS (298c5928; build_v7_frame.py written after it, uncommitted):**
  - DONE: THE ALPHA MAPS (Poly Haven's glTF leaves out a plant's cut-out map: `tools/blender_fetch_cc0.ps1 -Alphas`; nine fetched, listed in MANIFEST.md; `wire_alpha()` puts them in the materials). THE LOOK PASS (`v7_frame_pieces.py look`: 126 s, peak 931 MB; blender/preview/b258/look_sheet.png, 64 pieces). THE CAST chosen from it: PIECES (23) and STANDS (far_stand) in v7_frame_pieces.py, with why the others are out.
  - WRITTEN, NOT YET RUN: `v7_frame_pieces.py piece <ids>` (one piece a render: the materials repainted with veins as two-value strokes, kept in preview/b258/tex3/; the painter's light: warm sun, cool sky, the ground's warm bounce; matt; then v7_paint.py: flatten_values, the filter, paint_over, a brushed edge -> preview/b258/pieces/<id>.png + .json), `plain <ids>` (the scan under the same light: the sheet's "before"), `stand far_stand`; `build_v7_frame.py <sheet> [peak MB]` (numpy: the STAGE layout; Frame(ppm).compose(): sky, far veils, mist, floor, shafts, the middle, the ground strip + the cut + the pit + the dug earth, cast shadows, the mannequin, the foreground; `one <ppm>` = one frame to look at).
  - STILL TO WRITE: a `ground` mode in v7_frame_pieces.py (the four ground maps are 16-bit PNG: read by bpy, painted as strokes, written 8-bit to pieces/ground_<name>.png: the composer reads those).
  - NEXT RUNS, each its own call under the gate: (1) `piece calathea_a fern_b rock_big` as a TEST: look at 1x and 2x, tune POST / TEXPAINT; (2) the rest in three or four runs by asset (each <= 9 min); (3) `ground`; (4) `plain` for the before/after; (5) `look island_tree_02` alone (a million triangles: if it does not fit, say so and leave it); (6) `tools/blender_locked.ps1 -Job .. -PyArgs blender/scripts/build_v7_frame.py,one,96 -CapMB 1500 -MinFreeGB 1.5`, look, fix the layout, then the sheet.
- **14:50: want_unity.lock is on file (UNITY waits at the RAM gate; free RAM 0.6-0.8 GB after the reboot, system tasks running): NOTHING of mine runs, file edits only. UNITY outranks me from its first want.**
- B-260 (a): coordination/reports/blender/v7_piece_format.md (the piece, the stage file, the figure sheet) sent to UNITY 14:4x with five questions (per-sprite ppu, vertex weights or constants, the lights' strength, the largest sprite, what else); UNITY's answer gets folded in, then LEAD lifts it.
- PART 1 (JUDGED 14:0x, 15540e23): real form, light and detail for almost nothing; NOT yet paint (the plant a clean render). Its files: review_b258_part1_paint_pass_preview.png + blender/preview/b258/. MEASURED: a piece of about 0.4 megapixel peaks 0.63-0.90 GB, 6-31 s; a 2.3 megapixel frame was killed at 1.44 GB (ONE PIECE A RENDER; a download is a SET in a row).
- HOW v7 RUNS: `tools/blender_scene.ps1 -Job .. -Script blender/scripts/<py> -ScriptArgs a,b -CapMB 1300 -MinFreeGB 1.9` (a REAL Blender under my lock; it refuses beside any lock or want); numpy sheets through `tools/blender_locked.ps1`. Blender 5.2.2: the compositor is scene.compositing_node_group with a group output; the Kuwahara node's settings are input sockets. Raw downloads under blender/vendor_cc0/<id>/ (git-ignored; glTF only; a generic client name) + MANIFEST.md (URL, licence, sha256, bytes); CC0 only; raw scans never ship. THE MACHINE: i3-1215U, Intel UHD, 7.75 GB; Cycles CPU.
- v6's sources stay for their POSE MATHS: `build_surveyor_v6.py` (skeleton, ik; 1.84 m to the skull), `build_surveyor_frames_v6.py` (the clips' keys; `--reach`, `--pages`). The study stills (docs/reference/v6_study/, git-ignored) are looked at only.
- B-250's six sheets are out of Assets (blender/archive/b250_surveyor_v6/, c262d114; rebuilt byte-identical 14:09). props/rig/stow_socket EXPORTED 82ca3266 (json only, U-212). B-249 EXPORTED 15e15c74 (`fx/dig_feel/kit`), in Review until U-212's re-import. B-247's icons 6329a93a. Waiting: U-151 (B-172's export, Blocked); B-242 / B-243 in Review.
RAM floor: nothing of mine under 0.3 GB free, nothing beside UNITY's lock or want.

How I run: locks listed, then RAM read, each in its own call; `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n>` for numpy sheets, proofs and crops (`blender/scripts/crop_png.py <src> x0 y0 x1 y1 k <dst>`; it refuses beside my OWN want: delete the want first); `tools/blender_render.ps1 <key or comma list>` for exports. UNITY and I take turns one job each while both have wants (D-037): on want_unity.lock finish the job I am on, yield, file mine (Write tool) only once UNITY HOLDS the lock, poll with the want refreshed. Beside a UNITY lock or want: file edits only (reading images is fine).
- The giants: one table blender/scripts/giants_v3.py; after ANY change to it or build_discs_v3 both far-disc proofs must stay byte-identical (hashes in reports/blender/b239_belt_table.md).
- Rulings that stand: D-190 = ONE cream puff per planet tinted by the dug cell's fill tone. B-231: the shadow shape on each part's BACK edge, crouch <= 0.98 m, lit from above. B-233's keys by PoiDef label (D-187). continue_rows only at cover >= 0.90. The shovel's reach stays 2 m.
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun. Waiting on others: B-207 on PawsOnTheGround; B-204 on UNITY's capture.

## Last completed
- 11-10 14:4x: B-258 part 3's first batch (298c5928): the alpha maps, the look pass, the piece and paint scripts; B-260 (a)'s draft. 14:15: the frame's CC0 pieces fetched (ac35497d). 14:0x: B-258 part 1 sent and judged (15540e23). 13:2x: B-251 DONE (cf5c1c60). 12:54: B-250 slice 1 EXPORTED 2c151225 (now out of Assets). 11:34: B-249 EXPORTED 15e15c74.

## Ready for review
- Nothing waits on LEAD (the frame is in work).
- In Review until UNITY's import and captures: B-224, B-223, B-225, B-233, B-242, B-243 (U-208), B-247's icons (U-210).

## Handoffs (unrouted only)
- -> UNITY (14:4x): the v7 piece format draft, coordination/reports/blender/v7_piece_format.md; five questions; its answer awaited.
- -> UNITY (11:3x, 15e15c74): fx/dig_reticle/base, png only (the pip a ground tick); received, goes in with U-212.
- -> UNITY (06:33, 6329a93a): icons/catalogue/{hadal_maw, vortex_whale, polar_hydra, diamondback_colossus, umbral_leviathan}; icon key = icons/catalogue/ + the last part of the creature's rig key; each json carries "creature".

## Blockers
none (the RAM gate after the reboot is a wait, not a block: files-only work meanwhile).

## Proposals (undecided only)
- v7_piece_format.md §A.2: a v7 colour map carries the PAINTED light (a contract exception to §2 "no baked lighting"); §A.3: "ppu" per piece (192 near, 128 middle, 32-48 a far strip) instead of the global 128. For LEAD with UNITY's answer.

## Rules I keep (from slips)
- One lock <= 15 min; one piece a render; a painted planet with more than 8 scenes gets its own lock.
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs, and every file change goes through the edit tools (a commit of edited files is fine). A lock listing is read in an EARLIER call than any write or run.
- Never a bare `python` / `python3` in a shell line: the only interpreter is Blender's bundled one, through blender_locked.ps1 or by its full path inside a hand-held lock. Never pipe the helper into `Select-Object -First n`.
- Before sending a sheet, look at every new shape at 2x-4x for faces and for what else it could be: two ringed dots side by side or in one outline; three dots in a triangle; a ring of an eye's size at an eye's height; ONE round window or dial on a rounded body or a box; a disc with one curved line (a mouth); a disc with one upright dark mark (a cat's eye) or a flick beside it (a lash); a dot over an arch; a chain of crisp blobs (a grub); ringed pits on jointed panels; identical dot trails; small three-cornered flakes; a bright accent on small ovals; a glove over a nose. Fix, re-run, look again.
- A first run is not a sheet: measure it against the card's numbers and look at it before sending. A noise added to a mask must be zero where the mask is.
- A change to a builder whose art is exported is proven by rebuilding what it exports and comparing bytes (or strokes) with the exported files.
- A reach or a range is computed from the pose maths before it is promised. A re-export for one changed piece: `git status` must show only the intended files before the commit.
- A manifest row's key has three parts. No 2>&1 on the wrappers in PowerShell 5.1. A commit with nothing staged prints the whole tree's status: check `git status --short -- <my paths>` first.
- A want is filed only once the other role HOLDS the lock (D-039); refresh it each poll; never end a turn on a want. No background waiters.
- All three sessions share one working tree: a push can race another role's (fetch, never rebase, push again); commit by explicit file paths, check git show --stat, 0 .meta.
- A scan's glTF may not list all its maps (the alpha): read the API's file list, not only the glTF's.

## For USER_ACTIONS
none of mine (LEAD's: the apps that auto-start at boot hold about 1.3 GB).

## HeavyJobLock
none held (last: 11-10 14:34:07-14:34:10, the look sheet's crops; before it 14:31:48-14:33:54, the look pass). No want on file. No background waiters.
