# BLENDER STATUS
Updated: 2026-11-10 14:1x · Session: 13 (resumed 11-10 00:52; THIS SESSION = zuber-e2; LEAD = zuber-36; UNITY = zuber-57) · older: coordination/status/archive/BLENDER_2026-11-09.md (session 12's closed entries), BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**13:4x — RESUME HERE: ART v7, THE LIVING PAINTING (D-205; READ docs/STYLE_V7.md FIRST). The owner (13:3x): "You dont have to draw it, find another way ... a walking highly detailed living painting". v6 is history; nothing of it ships. THE METHOD (LEAD's ruling): REAL 3D (CC0 scans; a CC0 human base mesh with our own suit, boots and pack), lit by one sun and sky, rendered and PAINTED in Blender (THE PAINT IN THE MATERIALS; the compositor's anisotropic Kuwahara only softens), played as 2D sprites and layers; every near plant also alone with its pivot at the root; UNITY adds wind, physics, air and light (U-216). MY TASK: **B-258 THE PILOT**, each part sent to LEAD alone as it reads; NOTHING exported to Assets: part 1 (the paint pass) is JUDGED; NOW THE FRAME; THEN THE FIGURE (idle and walk keyed from B-250's pose tables in `build_surveyor_frames_v6.py`: keys, timings, ground speeds, sockets STAND; a strip of 12 twice: the pass must not crawl; the price of 12 and of 24 drawings a second). The next line has LEAD's ruling for the frame. RULES: ONE Blender at a time under my lock, never beside UNITY's lock or want; raw downloads under blender/vendor_cc0/ (git-ignored once LEAD adds `/blender/vendor_cc0/`; each asset in its own new folder; glTF, never an untrusted .blend; a generic User-Agent, nothing of the owner or the project in a request) + a committed manifest (name, URL, licence, sha256, size); CC0 only; raw scans never ship; original design, no likeness; if MPFB fights Blender 5.2, use Blender Studio's base meshes. THE MACHINE: i3-1215U, integrated Intel UHD, 7.75 GB; Blender 5.2.2; Cycles CPU. ON HOLD until the pilot's verdict: B-252 .. B-256. B-257 withdrawn. v6's work (B-250's sheets, B-251's pilot, the kinds, the forest frame) is in git and is not the look.**
- **B-258 PART 1 JUDGED 14:1x (15540e23)**: it proves real form, light and detail for almost nothing; it does NOT prove paint (the plant is a clean render); no more polishing of single pieces. **NOW: THE FRAME (part 3, ahead of the figure), LEAD's ruling 14:1x:** the camp's stage rebuilt from scans as PIECES COMPOSED (never one 2-megapixel render): far veils (a small far stand through the Kuwahara pass, scaled up: soft is right), a middle thicket, near plants, a trunk or two with roots, mossy rocks, a ground strip and dug earth from scanned forest-floor and soil textures, haze by depth, ONE colour key, a warm pool of light on the stage with cool shade round it; A PAINTER'S LIGHT (fewer, flatter values, a designed shadow shape, coloured bounce, matt: a glossy highlight is the 3D tell); VEINS AND GRAIN AS STROKES in two values instead of the restored photo detail (keep the scan where that loses the plant's character, and say so); a FOREGROUND layer in front of the play plane with pieces at 2-3x life size from the 384 px per metre source; the frame composed TWICE, the play plane at 96 and at 128 px per metre; plants may be scaled up to x3; a plain 1.84 m neutral-grey mannequin silhouette for scale (no v6 cel). Download what it needs from Poly Haven / ambientCG (fern, anthurium, pachira, an island tree or the jacaranda, grasses, moss, roots, a trunk, bark and forest-floor materials), each in the manifest. Gate: 1.9 GB free, watchdog 1.3 GB, peaks reported. THEN PART 2 (the figure): DATA ONLY: Blender Studio's CC0 human base meshes + Rigify; NO add-on on the owner's machine without the owner's word; one probe frame sets its gate. ALSO ASKED: the cost of a 3-4 s MOCK OF MOTION of the frame (near pieces swayed about their roots, motes, a breathing shaft): say the cost before doing it. Part 1's files: review_b258_part1_paint_pass_preview.png + blender/preview/b258/ (a calathea x2.5 and a mossy rock, Poly Haven CC0: blender/vendor_cc0/MANIFEST.md). HOW: `tools/blender_scene.ps1 -Job .. -Script blender/scripts/v7_paint_pass.py -ScriptArgs probe|paint|edge -CapMB 1300 -MinFreeGB 1.9` (a REAL Blender run under my lock; LEAD's gate for part 1: 1.9 GB free, watchdog 1.3 GB; part 2: 2.4 GB), then `blender_locked.ps1 .. build_v7_part1_sheet.py <png> <peak MB>`. MEASURED: one piece of about 0.4 megapixel peaks 0.63-0.90 GB, 150-180 s for both pieces; a 2.3 megapixel frame was killed at 1.44 GB (ONE PIECE A RENDER: a download is a set in a row). Blender 5.2.2: the compositor is scene.compositing_node_group with a group output; the Kuwahara node's settings are input sockets. MY READ (LEAD agreed): the rock reads painted; the plant is a clean detailed render, not yet paint.
- v6's sources stay for their POSE MATHS: `build_surveyor_v6.py` (skeleton, ik; 1.84 m to the skull), `build_surveyor_frames_v6.py` (the clips' keys; `--reach`, `--pages`); also cel_v6, paint_v6, painted_v6 (strokes as a brush), the forest frame and the kinds.
- The study stills (docs/reference/v6_study/, git-ignored) are looked at only: never committed, never a texture, never traced; no character, design, composition or frame of the film.
- B-250's six exported sheets were MOVED OUT of Assets to blender/archive/b250_surveyor_v6/ (c262d114; so 0.6.4 does not ship them). PROVEN 14:09: with REPACK off the frames builder rebuilds all six files byte-identical (`--pages`, 118 s, peak 359 MB).
- props/rig/stow_socket EXPORTED 13:27 (82ca3266), json only: the v3 body's stowed tool per frame of side; with UNITY (U-212).
- SUPERSEDED BY D-200, kept: `build_surveyor_v5.py` and the first style frame (`build_style_frame_v6.py`; it still supplies the crates, the smelter, the pit and the tints to the forest frame).
- B-247: the five Grand icons EXPORTED 6329a93a (U-210). The Tharsis field and boulder and the tessera pair are RULED but PARKED by LEAD (no file changed).
- B-246 DONE. The v3 dig_up clears a 2.0 m ceiling, not a 1.8 m tunnel.
- B-245 DONE (4653d243): smoke_read_0.6.3.md + 13 crops: first hour GO; its findings H5-H8 and G5 are UNITY's (U-212).
- B-249 EXPORTED (15e15c74): the reticle's pip is a ground tick; the row is `fx/dig_feel/kit`. In Review until U-212's re-import.
- Also waiting: U-151 (B-172's export, Blocked); B-242 / B-243 in Review.
RAM floor: nothing of mine under 0.3 GB free, nothing beside UNITY's lock or want.

How I run: locks listed, then RAM read, each in its own call; `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n>` for numpy sheets, proofs and crops (`blender/scripts/crop_png.py <src> x0 y0 x1 y1 k <dst>`; it refuses beside my OWN want: delete the want first); `tools/blender_render.ps1 <key or comma list>` for exports. UNITY and I take turns one job each while both have wants (D-037): on want_unity.lock finish the job I am on, yield, file mine (Write tool) only once UNITY HOLDS the lock, poll with the want refreshed. Beside a UNITY lock: file edits only (reading images is fine).
- A slot of several light steps beside UNITY = ONE hand-held heavy_blender.lock in ONE call, UNITY asked beforehand not to file while it is up and told the moment it is released. A heavy row (a v3 sheet) takes the wrapper's own lock.
- The giants: one table blender/scripts/giants_v3.py; after ANY change to it or build_discs_v3 both far-disc proofs must stay byte-identical (hashes in reports/blender/b239_belt_table.md).
- Rulings that stand: D-190 = ONE cream puff per planet tinted by the dug cell's fill tone. B-231: the shadow shape on each part's BACK edge, crouch <= 0.98 m, lit from above. B-233's keys by PoiDef label (D-187). continue_rows only at cover >= 0.90. The shovel's reach stays 2 m.
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun. Waiting on others: B-207 on PawsOnTheGround; B-204 on UNITY's capture.

## Last completed
- 11-10 13:2x: B-251 DONE (cf5c1c60). 12:54: **B-250 slice 1 EXPORTED** 2c151225. 11:34: **B-249 EXPORTED** 15e15c74. 11:2x: B-245 the 0.6.3 smoke read (4653d243). 10:4x: the plains' and coast's sheets ACCEPTED (ad8de994). 09:5x: the frame's run 9 ACCEPTED (8d4efa4c).
- 11-10 06:32: B-247's five Grand icons EXPORTED 6329a93a. 06:08: B-246 sheet 2 b351f2d8. 01:28: B-243 3ff5e37e. 00:07: B-242 068a2918.

## Ready for review
- Nothing waits on LEAD (B-258 part 1 judged; the frame is in work).
- In Review until UNITY's import and captures: B-224, B-223, B-225, B-233, B-242, B-243 (U-208), B-247's icons (U-210).

## Handoffs (unrouted only)
- -> UNITY (12:5x, 2c151225): characters/surveyor_v6/{side, side_air, side_dig}: keys, clips, sockets, the four points; received. OWED to UNITY: the v3 stow table (json only).
- -> UNITY (11:3x, 15e15c74): fx/dig_reticle/base, png only (the pip a ground tick); received, goes in with U-212.
- -> UNITY (06:33, 6329a93a): icons/catalogue/{hadal_maw, vortex_whale, polar_hydra, diamondback_colossus, umbral_leviathan}; icon key = icons/catalogue/ + the last part of the creature's rig key; each json carries "creature".


## Blockers
none.

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
none held (last: 11-10 14:07:28-14:09:26, B-250's byte-identical proof). No want on file. No background waiters.
