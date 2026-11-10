# BLENDER STATUS
Updated: 2026-11-10 13:4x · Session: 13 (resumed 11-10 00:52; THIS SESSION = zuber-e2; LEAD = zuber-36; UNITY = zuber-57) · older: coordination/status/archive/BLENDER_2026-11-09.md (session 12's closed entries), BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**13:4x — RESUME HERE: ART v7, THE LIVING PAINTING (D-205; READ docs/STYLE_V7.md FIRST). The owner, 13:2x-13:3x, withdrew v6 ("make it a lot more detailed") and then opened the method: "You dont have to draw it, find another way ... an animated movie or a book came to life ... a walking highly detailed living painting". v6 is history; nothing of it ships. THE METHOD (LEAD's ruling): REAL 3D (CC0 scans; a CC0 human base mesh with our own suit, boots and pack), lit by one sun and sky, rendered and PAINTED in Blender (the compositor's ANISOTROPIC Kuwahara + brush / canvas texture; my caution to LEAD: on a 180 px figure a screen filter does little and crawls, so the paint belongs in the materials too), played as 2D sprites and layers; every near plant also alone with its pivot at the root; UNITY adds wind, physics, air and light (U-216). MY TASK: **B-258 THE PILOT**, three parts, each sent to LEAD alone as it reads; NOTHING exported to Assets: (1) THE PAINT PASS on one scanned plant and one mossy rock or trunk (Poly Haven, 1k textures): three settings side by side at 96 px per metre and at 2x, the plain render beside them, a normal-map pass, render time and peak RAM; (2) THE FIGURE: a 3D human on a skeleton, idle and walk keyed from B-250's pose tables (`build_surveyor_frames_v6.py`: its keys, timings, ground speeds and sockets STAND), a strip of 12 and the same 12 again (the pass must not crawl); the price of 12 and of 24 drawings a second; (3) THE FRAME beside blender/preview/b251/forest_frame_96_plates.png. RULES: ONE Blender at a time under my lock, never beside UNITY's lock or want; raw downloads under blender/vendor_cc0/ (git-ignored once LEAD adds `/blender/vendor_cc0/`; each asset in its own new folder; glTF, never an untrusted .blend; a generic User-Agent, nothing of the owner or the project in a request) + a committed manifest (name, URL, licence, sha256, size); CC0 only; raw scans never ship; original design, no likeness; if MPFB fights Blender 5.2, use Blender Studio's base meshes. THE MACHINE: i3-1215U, integrated Intel UHD, 7.75 GB; Blender 5.2; EEVEE renders headless (10-30: 46 frames of 256 px, three maps, 118 s, peak 1.37 GB). ON HOLD until the pilot's verdict: B-252 .. B-256 (the v6 fist; the repack, written behind REPACK = False; slice 2; the stage layers; the ground; the kit; the library's intake). B-257 withdrawn. IN GIT, NOT THE LOOK: B-250 slice 1 (characters/surveyor_v6/*, 2c151225), B-251's pilot (cf5c1c60), Earth's twelve kinds, the forest frame.**
- v6's sources, kept as history and for their POSE MATHS (blender/scripts/): `build_surveyor_v6.py` (skeleton(pose), ik; the figure 1.84 m to the skull), `build_surveyor_frames_v6.py` (the clips' keys; `--reach`, `--pages`), `cel_v6.py`, `paint_v6.py`, `painted_v6.py`, `build_forest_frame_v6.py`, `build_*_kinds_v6.py`.
- The study stills (docs/reference/v6_study/, git-ignored) are looked at only: never committed, never a texture, never traced; no character, design, composition or frame of the film.
- OWED (small, in a gap): a dry run proving the frames builder still gives the pages as exported with REPACK off (`build_surveyor_frames_v6.py --pages <dir> <png>`, then compare with Assets/_Game/Art/characters/surveyor_v6/).
- **props/rig/stow_socket EXPORTED 13:27 (82ca3266)**, json only, for U-212: where a stowed tool rides the v3 body per frame of characters/surveyor/side (the blade off the helmet in bump and land); the row `props/rig/stow_socket`; with UNITY.
- SUPERSEDED BY D-200, kept: `build_surveyor_v5.py` and the first style frame (`build_style_frame_v6.py`; it still supplies the crates, the smelter, the pit and the tints to the forest frame).
- B-247: the five Grand icons EXPORTED 6329a93a (U-210). The Tharsis field and boulder and the tessera pair are RULED but PARKED by LEAD (no file changed).
- B-246 DONE. The v3 dig_up clears a 2.0 m ceiling, not a 1.8 m tunnel.
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
- 11-10 13:2x: B-251 DONE (cf5c1c60). 12:54: **B-250 slice 1 EXPORTED** 2c151225. 11:34: **B-249 EXPORTED** 15e15c74. 11:2x: B-245 the 0.6.3 smoke read (4653d243). 10:4x: the plains' and coast's sheets ACCEPTED (ad8de994). 09:5x: the frame's run 9 ACCEPTED (8d4efa4c).
- 11-10 06:32: B-247's five Grand icons EXPORTED 6329a93a. 06:08: B-246 sheet 2 b351f2d8. 01:28: B-243 3ff5e37e. 00:07: B-242 068a2918.

## Ready for review
- Nothing waits on LEAD. (B-250 slice 1 is in the tree; v6 is withdrawn, D-205.)
- In Review until UNITY's import and captures: B-224, B-223, B-225, B-233, B-242, B-243 (U-208), B-247's icons (U-210).

## Handoffs (unrouted only)
- -> UNITY (12:5x, 2c151225): characters/surveyor_v6/{side, side_air, side_dig}: keys, clips, sockets, the four points; received. OWED to UNITY: the v3 stow table (json only).
- -> UNITY (11:3x, 15e15c74): fx/dig_reticle/base, png only (the pip a ground tick); received, goes in with U-212.
- -> UNITY (06:33, 6329a93a): icons/catalogue/{hadal_maw, vortex_whale, polar_hydra, diamondback_colossus, umbral_leviathan}; icon key = icons/catalogue/ + the last part of the creature's rig key; each json carries "creature".


## Blockers
none. Asked of LEAD: the .gitignore line `/blender/vendor_cc0/` (its file).

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
none held (last: 11-10 13:27:27-13:27:33, the stow table's export). No want on file. No background waiters.
