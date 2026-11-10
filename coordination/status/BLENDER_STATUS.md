# BLENDER STATUS
Updated: 2026-11-10 12:2x · Session: 13 (resumed 11-10 00:52; THIS SESSION = zuber-e2; LEAD = zuber-36; UNITY = zuber-57) · older: coordination/status/archive/BLENDER_2026-11-09.md (session 12's closed entries), BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**12:2x — RESUME HERE: ART v6 IS A YES. The owner on USER-44 (11:4x): "I like it so far but find a painter's hand or you do it, AI is so capable nowadays, and continue doing the rest" -> D-202. B-231 and B-248 are DONE (the figure and the look accepted). THE CAMERA is ruled: 96 px per metre on foot at the surface, easing to 64 underground. NOW, in this order: (1) B-250 THE SURVEYOR'S FRAME SETS, slice 1 (`blender/scripts/build_surveyor_frames_v6.py <png>`; keys characters/surveyor_v6/side and /side_dig; drawn at 512 px per metre, exported at 128; every frame its own drawing from a pose): the strip sheet blender/preview/review_b250_frames_slice1_preview.png (run 5, 12:22, e2928939; strips in blender/preview/b231_frames/) is WITH LEAD, with two rulings asked: THE WALK (the game moves 4.0 / 6.5 m/s with clips at 12 fps, so "walk" is drawn as a lope and "run" as a sprint, the planted foot set by reach: leg_ik / plant / cycle; a true walk is kept as the extra strip "stroll") and THE FRAME BOX (288x320 at 128 px per metre, pivot [0.5, 0.0625]; side's 98 frames = 2.2 sheets of 2048). OWED with the export: slide_max per clip, carry and ready from the pose maths (today's are the v3 body's); then slice 2 (look_camera, bump, conk_out, dash). NOTHING EXPORTED. (2) B-251 THE PAINTER'S-HAND PILOT (AI-painted material made by LEAD under D-202: docs/art_sources/v6_painted/strokes_01.png and plant_01.png, 2048x2048): `blender/scripts/painted_v6.py` (strokes / stamp / brush with mips; plate / rekey / place: written UNRUN) and the forest frame's paint(hook=). The pilot sheet = (a) the plant specimen and the tree's bark painted with my oval dab and with the painted strokes; (b) plant_01 cut out as a plate, re-keyed, three times in the 96 px frame beside my plants; my read, incl. what a library should hold. NO scenery export, tiling or alpha until B-251 is judged. RHYTHM = True is the figure's default (b03f234d). EARTH'S KINDS: twelve painted or written (coordination/reports/blender/v6_earth_kinds.md; `build_forest_kinds_v6.py`, `build_plains_kinds_v6.py`, `build_coast_kinds_v6.py`), accepted as specimens except the tree fern and the tide line (not to be used yet). THE FRAME: `build_forest_frame_v6.py <png> [--only 96]` (run 9 accepted, 8d4efa4c; b248_forest/forest_frame_96.png, _64.png). DECIDED: figures ship as DRAWN FRAMES (no runtime rig), at twice the game's size, on twos. B-247's v3 repaints stay parked.**
- B-231 THE REDESIGN (`blender/scripts/build_surveyor_v6.py`, dca05ff0; the v5 file and its sheets are superseded, kept): a parametric DRAWN figure: skeleton(pose) -> Fig(pose, view).draw().render(); views side / three-quarter / front; 1.84 m to the skull, 5.26 heads (5.39 with the hair); head on a 100-unit grid in three hand-built views, eye 17 % of the head's width; trunk from cross-sections along the spine (T(u, v) puts the sash, badge, belt, straps on it); lower limbs' line open across the joint; rolled sleeves; hands open / grip; boots; pack + whip antenna ("ant"), no helmet on Earth; helmet_bust(); POSES idle, walk, crouch (0.90 m), jump, dig (arms by ik()). Sheet blender/preview/review_b231_surveyor_v6_model_preview.png (run 4); b231_v6/frame_idle_2x.png (78x243 px, 17.6 KB; 150 frames = 2.6 MB of PNG, 11 MB of texture). Three fixed heads, one expression.
- The study stills (docs/reference/v6_study/, git-ignored) are looked at only: never committed, never a texture, never traced; no character, design, composition or frame of the film.
- THE TWO MODULES. `blender/scripts/cel_v6.py` = the CEL (what acts): a charcoal pencil line (#2A2624, about 1.2 px at the game's zoom, pressure, tapers, gaps: `gap=`, `at=`) over FLAT paint, two layers until compose(key=); S() a stroke (rnd, keep= / clip=, under=, shade=), P() a paint patch, F() a flick, Canvas(W, H, K=4) in design px (128 per metre). `blender/scripts/paint_v6.py` = the PAINTING (the stage): Painting(W, H, seed, Q): an underpainting, then brush() lays dabs that take their colour from it (clip= keeps them on a form); blob(), stroke(), glaze(), tooth(); no line anywhere.
- SUPERSEDED BY D-200, kept (sources c2b7080e): the v5-proportioned cel surveyor (`build_surveyor_v5.py`) and the first style frame (`build_style_frame_v6.py`; it still supplies the crates, the smelter, the pit and the tints to the forest frame). The owner liked their COLOURS. My note on painted backgrounds (code holds the rules, it does not draw; scanned brush strokes would raise the ceiling) is with the owner.
- B-247: the five Grand icons EXPORTED 6329a93a (U-210 has the keys). The Tharsis field and boulder and the tessera pair are RULED but PARKED by LEAD until the owner rules on v6 (the tessera's blocks: `_seated(...)` in build_backdrop_v3.venus_tessera; no file changed).
- B-246 DONE (LEAD 11:1x). dig_up clears a 2.0 m ceiling, not a 1.8 m tunnel.
- B-245 DONE 11:2x (4653d243): coordination/reports/blender/smoke_read_0.6.3.md + 13 crops beside it: first hour GO; 0.6.3 is the owner's build (USER-45). Its findings H5-H8 and G5 are UNITY's (U-212).
- B-249 (from the read's H3) **EXPORTED 11:34 (15e15c74)**: the reticle's pip is a GROUND TICK (the cross in four brackets read as a gun sight): one png, fx/dig_reticle/base_color.png; the manifest row is `fx/dig_feel/kit` (a light kit: hand-held lock), NOT the sheet's key. In Review until UNITY's png-only re-import (U-212).
- Also waiting: U-151 (B-172's export, Blocked); B-242 / B-243 in Review.
RAM floor: nothing of mine under 0.3 GB free, nothing beside UNITY's lock or want.

How I run: locks listed, then RAM read, each in its own call; `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n>` for numpy sheets, proofs and crops (`blender/scripts/crop_png.py <src> x0 y0 x1 y1 k <dst>`; it refuses beside my OWN want: delete the want first); `tools/blender_render.ps1 <key or comma list>` for exports. UNITY and I take turns one job each while both have wants (D-037): on want_unity.lock finish the job I am on, yield, file mine (Write tool) only once UNITY HOLDS the lock, poll with the want refreshed. Beside a UNITY lock: file edits only (reading images is fine).
- A slot of several light steps beside UNITY = ONE hand-held heavy_blender.lock in ONE call, UNITY asked beforehand not to file while it is up and told the moment it is released. A heavy row (a v3 sheet) takes the wrapper's own lock.
- The giants: one table blender/scripts/giants_v3.py; after ANY change to it or build_discs_v3 both far-disc proofs must stay byte-identical (hashes in reports/blender/b239_belt_table.md).
- Rulings that stand: D-190 = ONE cream puff per planet tinted by the dug cell's fill tone. B-231: the shadow shape on each part's BACK edge, crouch <= 0.98 m, lit from above. B-233's keys by PoiDef label (D-187). continue_rows only at cover >= 0.90. The shovel's reach stays 2 m.
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun. Waiting on others: B-207 on PawsOnTheGround; B-204 on UNITY's capture.

## Last completed
- 11-10 12:22: B-250's slice 1 strip sheet sent (e2928939). 11:34: **B-249 EXPORTED** 15e15c74. 11:2x: B-245 the 0.6.3 smoke read (4653d243). 10:4x: the plains' and coast's sheets ACCEPTED (ad8de994). 09:5x: the frame's run 9 ACCEPTED (8d4efa4c).
- 11-10 06:32: B-247's five Grand icons EXPORTED 6329a93a. 06:08: B-246 sheet 2 b351f2d8. 01:28: B-243 3ff5e37e. 00:07: B-242 068a2918.

## Ready for review
- With LEAD: B-250's slice 1 strip sheet (review_b250_frames_slice1_preview.png, run 5, e2928939).
- In Review until UNITY's import and captures: B-224, B-223, B-225, B-233, B-242, B-243 (U-208), B-247's icons (U-210).

## Handoffs (unrouted only)
- -> UNITY (11:3x, 15e15c74): fx/dig_reticle/base, png only (the pip a ground tick), json unchanged; for U-212.
- -> UNITY (06:33, 6329a93a): icons/catalogue/{hadal_maw, vortex_whale, polar_hydra, diamondback_colossus, umbral_leviathan}; icon key = icons/catalogue/ + the last part of the creature's rig key; each json carries "creature".


## Blockers
none. Waiting on LEAD: B-250's two rulings (the walk, the frame box). If UNITY asks: a stow socket for the bump and hard-landing clips (side_dig.json, a direct data handoff).

## Proposals (undecided only)
none (the boil proposal is struck: moot under D-200, drawn frames boil by themselves).

## Rules I keep (from slips)
- One lock <= 15 min; a painted planet with more than 8 scenes gets its own lock.
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs, and every file change goes through the edit tools (a commit of edited files is fine). A lock listing is read in an EARLIER call than any write or run (11-10 07:46: I listed the locks and deleted seven stale preview files in ONE shell call; the listing showed UNITY's new lock. Harmless, told LEAD; a slip all the same).
- Never a bare `python` / `python3` in a shell line, not even for a version or an empty heredoc (11-10 06:58: it hung and had to be stopped): the only interpreter is Blender's bundled one, through blender_locked.ps1 or by its full path inside a hand-held lock. Never pipe the helper into `Select-Object -First n`.
- Before sending a sheet, look at every new shape at 2x-4x for faces and for what else it could be: two ringed dots side by side or in one outline; three dots in a triangle; a ring of an eye's size at an eye's height; ONE round window or dial on a rounded body or a box; a disc with one curved line (a mouth); a disc with one upright dark mark (a cat's eye) or a flick beside it (a lash); a dot over an arch; a chain of crisp blobs (a grub); ringed pits on jointed panels; identical dot trails; small three-cornered flakes; a bright accent on small ovals; a glove over a nose. Fix, re-run, look again.
- A first run is not a sheet: measure it against the card's numbers and look at it before sending. A noise added to a mask must be zero where the mask is (B-231 run 1: specks over the whole cel, a false height).
- A change to a builder whose art is exported is proven by rebuilding what it exports and comparing bytes (or strokes) with the exported files.
- A reach or a range is computed from the pose maths before it is promised. A re-export for one changed piece: `git status` must show only the intended files before the commit.
- A manifest row's key has three parts. No 2>&1 on the wrappers in PowerShell 5.1. A commit with nothing staged prints the whole tree's status: check `git status --short -- <my paths>` first.
- A want is filed only once the other role HOLDS the lock (D-039); refresh it each poll; never end a turn on a want. No background waiters.
- All three sessions share one working tree: a push can race another role's (fetch, never rebase, push again); commit by explicit file paths, check git show --stat, 0 .meta.

## For USER_ACTIONS
none of mine (LEAD's: USER-39 the C5 look-over, now in v6; USER-41 Build 0.6.2).

## HeavyJobLock
none held (last: 11-10 12:19:14-12:22:03, B-250's strip sheet, run 5). No want on file. No background waiters.
