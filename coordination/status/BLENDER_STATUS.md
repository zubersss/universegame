# BLENDER STATUS
Updated: 2026-11-10 17:1x · Session: 14 (THIS SESSION = zuber-59; LEAD = zuber-4a; UNITY = zuber-30) · older: coordination/status/archive/BLENDER_2026-11-10.md (session 13), BLENDER_2026-11-09.md, _08, _07

## PAUSED BY THE OWNER 17:2x ("Pause all work", relayed by LEAD). NOTHING RUNS UNTIL THE OWNER OR LEAD SAYS RESUME.
At the pause: no Blender process, no lock of mine, no want on file, every finished source and report committed and pushed. A piece run was about to start (locks empty, 2.38 GB free at 17:17) and was NOT started.

## Current task
**B-258 PART 3, THE FRAME (art v7, the living painting, D-205; docs/STYLE_V7.md; contract v3.5 §12). LEAD's ruling 14:1x stands: the camp's stage from CC0 scans as PIECES COMPOSED; a painter's light; veins and grain as strokes in two values; a foreground at 2-3x at the frame's SIDES (D-206b: never within 2.5 m of the surveyor); the frame at 96 AND 128 px per metre; a grey 1.84 m mannequin; ONE sheet to LEAD, the pass that reads, my own read. Nothing exported to Assets. AFTER IT, one turn each: part 2's probe frame, B-264's packer run, B-259's and B-261's sheets; one probe render of a near piece at 512 px per metre (old gate) after the frame is with LEAD.**

**WHERE I STOPPED**
- RENDERED AND PAINTED (run 1, 16:02:16-16:04:59), each alone at 384 px per metre, in blender/preview/b258/pieces/ (<id>.png painted, <id>_render.png the render before the brush, <id>.json): **calathea_a, calathea_b, fern_a, fern_b, fern_c, rock_big, rock_low, rock_flat** (8 of 23 + the far stand).
- LOOKED AT (17:1x, at the size rendered, 4x the game's): calathea_a beside its render, fern_b, rock_big beside its render, rock_low. WHAT I SAW: the calathea and the fern READ AS PAINT (dabs along the leaf, three or four values, a brushed edge); the calathea's stripes, its character, are mostly gone under the dabs (to weigh in the frame: more accent strokes or smaller base strokes on leaves); the rocks are dry strokes over real form. rock_big looked wrong in the viewer (a solid ground round it) but its alpha is right (pixels read: alpha 0 outside, the colour bled under it as intended). NOT YET LOOKED AT: any piece at 1x and 2x on the stage tone (that needs the composer or a numpy sheet), calathea_b, fern_a, fern_c, rock_flat.
- NOT RENDERED: anthurium_a / b / c (their material IS repainted and kept in preview/b258/tex3/), grass_mid / wide / seed, grass_dry, weed, stump, root, log, snag, tree_tall / bushy / small, far_stand; the four ground maps (`ground`); `plain` for the sheet's before; `look island_tree_02`. The composer has never run.
- MEASURED PEAKS (D-209: a job starts at its peak + 0.35 GB free, watchdog at peak + 0.2): one piece a render 0.63-0.90 GB (part 1, 13:47-14:02); the look pass, 64 pieces, 0.93 GB (14:31:48-14:33:54); pieces run 1: four sets in ONE process crept to 1136 MB and my watchdog (1130) stopped it inside the anthurium = MEMORY STOP 1 of that job (a second stop sends it back to the 1.5 GB gate). So: ONE OR TWO SETS A RUN.
- **THE NEXT RUN, one call (the anthurium alone; its peak is unmeasured, so the old gate):** `tools/blender_scene.ps1 -Job "B-258 part 3 pieces: the anthurium" -Script blender/scripts/v7_frame_pieces.py -ScriptArgs piece,anthurium_a,anthurium_b,anthurium_c -CapMB 1300 -MinFreeGB 1.9 -TimeoutSec 540`. THEN, each its own call at `-CapMB 1130 -MinFreeGB 1.28`: `piece,grass_mid,grass_wide,grass_seed,grass_dry,weed`; `piece,stump,root`; `piece,log,snag`; `piece,tree_tall,tree_bushy,tree_small,far_stand`; `ground`; `plain,calathea_a,fern_b,rock_big`. THEN the composer (numpy, unmeasured): `tools/blender_locked.ps1 -Job .. -PyArgs blender/scripts/build_v7_frame.py,one,96 -CapMB 1500 -MinFreeGB 1.5`: look, fix the layout, `refinish <ids>` if the paint needs tuning (no 3D render), then `build_v7_frame.py <sheet> <peak>` and the sheet to LEAD.
- **FIRST STEP ON RESUME: read coordination/locks, then RAM, each in its own call; if UNITY holds the lock, file want_blender.lock (Write tool) and poll; else run the anthurium call above.**

**RULED TODAY (LEAD; binds the pilot):** D-206 = contract v3.5 §12 from my v7_piece_format.md (the painted light in the colour map; ppu 192 near / 128 middle / 32-48 a far strip; the layers table with `play_front`, tufts <= 0.30 m; NO flip on middle / near / play_front; never one piece twice at one scale inside a screen width; each piece rendered alone; `"style": "v7"`): all in `build_v7_frame.check_stage()`. D-206a: 12 drawings a second; ONE ppu 192 set; NORMAL MAPS ONLY for figures and near / play_front pieces. D-207 / D-209: a v7 planet's texture line is the laptop's measured ceiling. D-208: the surveyor ships as frame sheets at ppu 192, 12 a second, TRIMMED with `"cuts"` (pack_cuts.py); keep the rig exportable as a skinned mesh. Rigify may be switched on per run (never saved); plain bones are what v7_figure.py builds. B-260 (b), the export to pilot_v7/, waits for the frame's verdict AND LEAD's word.

**SOURCES WRITTEN, UNRUN:** `build_v7_frame.py` (the composer, the stage json, the sheet); `v7_frame_pieces.py ground | stand | plain | refinish`; B-259 `build_v7_underground.py <sheet>`; B-261 `v7_kit.py kit [shovel beam pack crate smelter]` + `build_v7_kit_sheet.py <sheet>`; B-264 `pack_cuts.py prove blender/archive/b250_surveyor_v6 blender/preview/b264` (its report b264_trimmed_packer.md is owed after the run); PART 2: `v7_pose.py` (B-250's pose maths without the cel modules; `check()` against build_surveyor_v6 before any clip), `v7_figure.py inspect | probe <object> [idle|walk]`, and the fetch row: `tools/blender_fetch_cc0.ps1 -BundleName human_base_meshes -BundleUrl <the v1.4.1 zip on blender.org/download/demo-files> -BundlePage https://www.blender.org/download/demo-files/ -BundleLicence CC0` (49 MB; NOT fetched; the URL to be read from the page first). DONE on paper: B-263 + B-266 (v7_price_list.md), B-265 (v7_animal_sources.md), B-260 (a).

- HOW v7 RUNS: `tools/blender_scene.ps1 -Job .. -Script .. -ScriptArgs a,b -CapMB n -MinFreeGB n [-SmallestFit]` (a REAL Blender under my lock; refuses beside any lock or want; `-SmallestFit` = D-209's one turn beside UNITY's RAM-blocked want: announce the take to UNITY as an attempt, report the release); numpy through `tools/blender_locked.ps1`. Raw downloads under blender/vendor_cc0/<id>/ (git-ignored) + MANIFEST.md; CC0 only; raw scans never ship. Poly Haven's glTF leaves out a plant's alpha map: `-Alphas`. THE MACHINE: i3-1215U, Intel UHD, 7.75 GB; Blender 5.2.2; Cycles CPU.
- v6's sources stay for their POSE MATHS (`build_surveyor_v6.py`, `build_surveyor_frames_v6.py`). B-250's six sheets are out of Assets (blender/archive/b250_surveyor_v6/). In Review on UNITY: B-249, B-242, B-243, B-247's icons. v3-era rules that still hold and received handoffs: the archive. **D-087: the Beam reads as a mining tool, never a gun.**
RAM floor: nothing of mine under 0.3 GB free, nothing beside UNITY's lock or want (but D-209's smallest fit).

## Last completed
- 11-10 17:1x: part 2's source (v7_pose.py, v7_figure.py, the fetch tool's bundle row). 17:1x: pieces run 1 reported, D-206b in the composer (the commit before this one). 15:2x: B-265, B-266. 15:1x: B-261's, B-264's, B-259's sources. 15:0x: B-263 DONE. 14:5x: B-260 (a) ACCEPTED. 14:4x: the alpha maps, the look pass (298c5928).

## Ready for review
- Nothing waits on LEAD (the frame is in work, paused).

## Handoffs (unrouted only)
none unrouted.

## Blockers
none (paused by the owner).

## Proposals (undecided only)
none.

## Rules I keep (from slips)
- One lock <= 15 min; one piece a render; ONE OR TWO SETS a Blender process.
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs (but D-209's smallest fit), and every file change goes through the edit tools. A lock listing is read in an EARLIER call than any write or run.
- After a run ends, in error or not, go straight on: look at what it left, report it, start the next thing (16:04: a stopped run left me idle for an hour until LEAD asked).
- Never a bare `python` / `python3` in a shell line. Never pipe the helper into `Select-Object -First n`. No 2>&1 on the wrappers in PowerShell 5.1.
- Before sending a sheet, look at every new shape at 2x-4x for faces and for what else it could be (two ringed dots; three dots in a triangle; one round window or dial on a rounded body; a disc with one curved line; a dot over an arch; a chain of crisp blobs; a bright accent on small ovals). Fix, re-run, look again.
- A first run is not a sheet: measure it against the card's numbers and look at it before sending. Send LEAD only the pass that reads, the failed passes named, my own read.
- A change to a builder whose art is exported is proven by rebuilding what it exports and comparing bytes.
- A want is filed only once the other role HOLDS the lock (D-039); refresh it each poll; never end a turn on a want. No background waiters.
- All three sessions share one working tree: commit by explicit file paths, check git show --stat, 0 .meta; a push can race (fetch, never rebase, push again).
- A scan's glTF may not list all its maps: read the API's file list. A picture viewer may draw the colour bled under alpha 0: read the pixels before calling an alpha wrong.

## For USER_ACTIONS
none of mine.

## HeavyJobLock
none held (last: 11-10 16:02:16-16:04:59, pieces run 1, stopped by my watchdog at 1136 MB). No want on file. No background waiters.
