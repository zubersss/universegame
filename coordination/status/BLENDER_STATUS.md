# BLENDER STATUS
Updated: 2026-11-10 07:1x · Session: 13 (resumed 11-10 00:52; every session stopped 02:24-05:55, the owner said "continue work"; THIS SESSION = zuber-e2; LEAD = zuber-36; UNITY = zuber-57) · older: coordination/status/archive/BLENDER_2026-11-09.md (session 12's closed entries), BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**07:3x — RESUME HERE: ART v6 "cel on painted" (D-199, docs/STYLE_V6.md; the owner: the art style of a 1960s cel film, technique only). LEAD JUDGED both: the surveyor right in kind + eight points (done in run 5; run 6 = the hair again, my own read: even upright mustard tufts are a crown); the style frame "IS cel on painted, this goes to the owner" + five tweaks (done in run 3; run 4 carries the run-6 surveyor). BOTH RE-RUNS WAIT FOR THE LOCK (a want is on file); then send LEAD both sheets in one message: LEAD builds the owner's page from them. After that: the rest of B-247 (ask LEAD first whether v3 backdrops are still worth repainting under D-199).**
- LEAD's rulings 07:1x-07:2x: the line mean 1.2 px at the game's zoom, #2A2624, pressure 0.5-2.0, the dry edge halved; a shadow shape only where it models (under the helmet, the pack's underside; far limbs darker); slim ribbed joint bands on the figure, a no-hardware knee and elbow shown beside them; under ten accent flicks; the boil = two full sheets A / B with the same rects (to U-199 with the export); plates 1, 2, 4 kept, plate 3 at 2x and 4x only; the style frame's sheet = the frame, today's game at the SAME size, a 2x crop of the surveyor on the painting and of the pit's edge; no tiling or alpha work before the owner's yes.
- The study stills (docs/reference/v6_study/, git-ignored) are looked at only: never committed, never a texture, never traced; no character, design, composition or frame of the film.
- TWO NEW MODULES. `blender/scripts/cel_v6.py` = the CEL (everything that acts): a charcoal pencil line (#3A3533; pressure +-40 %, tapered ends, a dry edge, outlines open at their first point: `gap=`, `at=`) over FLAT paint, kept as two layers until compose(); S() a stroke (rnd = corner rounding, keep= / clip= a paint mask, under= a patch under the form's lines), P() a paint patch with no line, F() a flick, shade() the ONE flat shadow shape, dry(), compose(key=) re-keys the paint only, Canvas(W, H, K=4) in design px (128 per metre; the game's zoom is half a design px). `blender/scripts/paint_v6.py` = the PAINTING (everything that is stage): an underpainting, then Painting.brush() lays thousands of dabs that take their colour from it; blob(), stroke(), glaze() (light pools, violet shadow), tooth(); no line anywhere.
- B-231 ROUND 3 (source bc555e4d + the hair, `build_surveyor_v5.py`; nothing exported): sheet blender/preview/review_b231_surveyor_v6_preview.png (run 5, 07:30) + blender/preview/b231/ (rig_color.png pass A, rig_color_b.png pass B, rig.json, close_*_4x.png). 512 px per metre, sheet 2048x996, 25 parts, 282 KB; the line mean 1.20 px at the game's zoom (0.11-1.98), 76 pencil strokes on the side figure; crouch 0.959 m; 25 s a run, peak 465 MB. The boil: a second line pass over the same paint, 1 s, +282 KB and +7.8 MB of texture per pass as a second sheet. Bones, pivots unchanged; the idle pose has a curve through the spine (hips +3, torso -7, head +8). JOINT = "band" / "none"; all_parts(key=) re-keys the figure's paint for a place; shovel_cel(). Its export path is written and NOT run: only on the owner's yes + LEAD's word (the row's text is in the builder's docstring).
- B-248 (`build_style_frame_v6.py`, bc555e4d): ONE 1920x1080 frame of the Earth camp at 64 px per metre, made at TWICE that size (Painting Q = 2, 3840x2160) and shrunk -> blender/preview/b248/style_frame_v6.png, crop_surveyor_2x.png, crop_pit_2x.png and the sheet blender/preview/review_b248_style_frame_preview.png (1920x2790: the frame, UNITY's u195 camp capture at the same size (cached as .npy beside it), the two 2x windows). Painted: sky, two far ridges, a rise and the plain with trees and hedges, one warm pool at the camp, the earth's beds with angular stones and roots, the pit (darker, an inner shadow), grass on the surface edge, a near trunk + crown (left) and bush + grass (right). Cels: the surveyor idle and digging (re-keyed in the pit), three crates, the smelter, a cel shovel, clods, a flat shadow shape under each. Run 3: 105 s, peak 766 MB, 32,508 dabs. The HONEST note on painted backgrounds went to LEAD 07:21 (code holds the rules; it does not draw, its brush has no intent, composition is numbers; scanned real brush strokes would raise the ceiling) and LEAD is giving it to the owner in those terms.
- B-247: the five Grand icons EXPORTED 6329a93a (U-210 has the keys). Still to do, both RULED, previews first: (G13 a) repaint only backgrounds/mars/tharsis layer2 below its ground line (row 352) as a receding lava plain (soft flow bands, no ink), the last 192 rows tiling vertically, tharsis.json continue_rows 192, and move one of the two boulders side by side (tile x about 530 / 595): a slope view and the 5 m dip. (Tessera) keep one boulder of the pair, move the other at least 1.5 m along the ridge, three sizes; one layer file; 1x and 2x crop before / after. Both in blender/scripts/build_backdrop_v3.py (mars_tharsis line 761, venus_tessera line 1148). (Whether v3 backdrops are still worth repainting under D-199 is LEAD's call: ask before starting.)
- B-246: COMPLETE (body 56bbfa4d, sheet 2 b351f2d8); 07:01 dig_up slide_max 0.55 -> 0.75, json only (d0899819; it clears a 2.0 m ceiling, not a 1.8 m tunnel: that needs a lower glove, told UNITY).
- Also waiting: U-151 (B-172's export, Blocked); B-245 (the 0.6.3 smoke read); B-242 / B-243 in Review.
RAM: 2.2-2.9 GB free 06:30-07:10. My floor: nothing under 0.3 GB free. Nothing of mine beside UNITY's lock or want.

How I run: locks listed, then RAM read, each in its own call; `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n>` for numpy sheets, proofs and crops (`blender/scripts/crop_png.py <src> x0 y0 x1 y1 k <dst>`; it refuses beside my OWN want: delete the want first); `tools/blender_render.ps1 <key or comma list>` for exports. UNITY and I take turns one job each while both have wants (D-037): on want_unity.lock finish the job I am on, yield, file mine (Write tool) only once UNITY HOLDS the lock, poll with the want refreshed. Beside a UNITY lock: file edits only (reading images is fine).
- A slot of several light steps beside UNITY = ONE hand-held heavy_blender.lock in ONE call, UNITY asked beforehand not to file while it is up and told the moment it is released. A heavy row (a v3 sheet) takes the wrapper's own lock.
- The giants: one table blender/scripts/giants_v3.py; after ANY change to it or build_discs_v3 both far-disc proofs must stay byte-identical (hashes in reports/blender/b239_belt_table.md).
- Rulings that stand: D-190 = ONE cream puff per planet tinted by the dug cell's fill tone. B-231: the shadow shape on each part's BACK edge, crouch <= 0.98 m, lit from above. B-233's keys by PoiDef label (D-187). continue_rows only at cover >= 0.90. The shovel's reach stays 2 m.
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun. Waiting on others: B-207 on PawsOnTheGround; B-204 on UNITY's capture.

## Last completed
- 11-10 07:15: B-231 round 3 (v6 cel) sheet SENT to LEAD (d54e75d8).
- 11-10 07:01: side_dig.json dig_up slide_max 0.75 (d0899819, json only).
- 11-10 06:32: **B-247's five Grand icons EXPORTED** 6329a93a.
- 11-10 06:08: **B-246 sheet 2 EXPORTED** b351f2d8; 02:18-02:22 its body 56bbfa4d.
- 11-10 01:28-01:36: **B-243 EXPORTED** 3ff5e37e. 00:07: **B-242 EXPORTED** 068a2918. Earlier: the archive.

## Ready for review
- With LEAD: B-231 round 3 (the v6 cel sheet above). With the owner: USER-39 (the C5 look-over; LEAD re-pages it with the v6 sheet and B-248's frame).
- In Review until UNITY's import and captures: B-224, B-223, B-225, B-233, B-242, B-243 (U-208), B-246 (U-209), B-247's icons (U-210).

## Handoffs (unrouted only)
- -> UNITY (07:02, d0899819): dig_up slide_max 0.75, json only, the png byte-identical; what it clears and what it does not.
- -> UNITY (06:33, 6329a93a): icons/catalogue/{hadal_maw, vortex_whale, polar_hydra, diamondback_colossus, umbral_leviathan}; icon key = icons/catalogue/ + the last part of the creature's rig key; each json carries "creature".
- -> UNITY (B-246, 56bbfa4d / b351f2d8): side_dig's clips, contact, slide_max, sockets.hand, carry / ready, the fist; the five fx keys of sheet 2.

## Blockers
none. Waiting on: LEAD's read of the v6 surveyor sheet; the lock for B-248's run 2.

## Proposals (undecided only)
- The boil as two full part sheets (A / B) swapped by texture on the 12 Hz clock (in the 07:15 message to LEAD).

## Rules I keep (from slips)
- One lock <= 15 min; a painted planet with more than 8 scenes gets its own lock.
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs, and every file change goes through the edit tools (a commit of edited files is fine). A lock listing is read in an EARLIER call than any write or run.
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
none held (last: 11-10 07:11:13-07:11:57, B-248's run 1). A want is on file for B-248's run 2 while UNITY holds the lock. No background waiters.
