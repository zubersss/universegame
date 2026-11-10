# BLENDER STATUS
Updated: 2026-11-10 07:4x · Session: 13 (resumed 11-10 00:52; every session stopped 02:24-05:55, the owner said "continue work"; THIS SESSION = zuber-e2; LEAD = zuber-36; UNITY = zuber-57) · older: coordination/status/archive/BLENDER_2026-11-09.md (session 12's closed entries), BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**08:1x — RESUME HERE: D-200. THE OWNER SAW THE FIRST v6 TEST (the v5-proportioned cel surveyor and the style frame): "I like the colours but the details I don't like ... still looks like a 1930s cartoon, big circle head and eyes ... the same style and the same level of detail, from the proportions to everything." Read docs/STYLE_V6.md section 4a. The cel-and-painting METHOD and the colours stay (cel_v6.py, paint_v6.py); HOW THINGS ARE DRAWN changes. LEAD's order, each to LEAD before the next: (1) the surveyor's MODEL SHEET: SENT 08:1x (below), waiting for LEAD's read; (2) a SPECIMEN SHEET of scenery (B-248): one tree (a trunk with weight, roots, tapering branches, bark strokes that WRAP the form), one rock (strokes following its planes), one broad-leaved plant leaf by leaf (two or three values a leaf, a midrib stroke), one grass clump of single blades, one square metre of covered ground (leaves, litter, a half-buried stone), ONE light direction, each at the game's size and at 2x; say how the brush follows form and what each cost: NOT STARTED; (3) only then ONE FRAME: Earth's forest edge with the camp, dense near and quiet behind the figures, at 64 and at 96 px per metre, the new surveyor in it. DECIDED: figures ship as DRAWN FRAMES (no runtime rig), exported at twice the game's size, on twos. B-247's v3 repaints (the Tharsis field, the boulder, the tessera pair) WAIT until the owner rules on v6. Be as honest with each sheet as with the last.**
- B-231 THE REDESIGN (`blender/scripts/build_surveyor_v6.py`, dca05ff0; the v5 file and its sheets are superseded, kept): a parametric DRAWN figure: skeleton(pose) -> Fig(pose, view).draw().render(); views side / three-quarter / front; 1.84 m to the skull, 5.26 heads (5.39 with the hair); head on a 100-unit grid in three hand-built views, eye 17 % of the head's width; trunk from cross-sections along the spine (T(u, v) puts the sash, badge, belt, straps on it); lower limbs' line open across the joint; rolled sleeves; hands open / grip; boots; pack + whip antenna ("ant") + the close helmet hung on it; helmet_bust(). POSES idle, walk, crouch (0.90 m), jump, dig (arms by ik()). Sheet blender/preview/review_b231_surveyor_v6_model_preview.png (run 3, 08:08; 10 s, peak 282-342 MB; a drawing renders in 0.7-1.5 s); blender/preview/b231_v6/ heads at the master size + frame_idle_2x.png (99x243 px, 18 KB; 150 frames = 2.7 MB of PNG, 14 MB of texture). My honest note to LEAD: it is a constructed mannequin (no twist, straight limbs, little cloth), three fixed heads and one expression, and at 64 px per metre the head is 22 px: the film's level of detail needs a closer camera. Offered: a twist, curved limbs, folds by joint bend, stretch (a day).
- Earlier today (superseded by D-200, files kept): LEAD's rulings 07:1x-07:4x on the v5-proportioned cel (line mean 1.2 px at the game's zoom, #2A2624, pressure 0.5-2.0, the dry edge halved; shadow shapes only where they model; no joint hardware; the boil = two full sheets A / B) and on the style frame (painted at 2x and shrunk; the earth quieter than the cels; one warm pool at the camp).
- The study stills (docs/reference/v6_study/, git-ignored) are looked at only: never committed, never a texture, never traced; no character, design, composition or frame of the film.
- TWO NEW MODULES. `blender/scripts/cel_v6.py` = the CEL (everything that acts): a charcoal pencil line (#3A3533; pressure +-40 %, tapered ends, a dry edge, outlines open at their first point: `gap=`, `at=`) over FLAT paint, kept as two layers until compose(); S() a stroke (rnd = corner rounding, keep= / clip= a paint mask, under= a patch under the form's lines), P() a paint patch with no line, F() a flick, shade() the ONE flat shadow shape, dry(), compose(key=) re-keys the paint only, Canvas(W, H, K=4) in design px (128 per metre; the game's zoom is half a design px). `blender/scripts/paint_v6.py` = the PAINTING (everything that is stage): an underpainting, then Painting.brush() lays thousands of dabs that take their colour from it; blob(), stroke(), glaze() (light pools, violet shadow), tooth(); no line anywhere.
- SUPERSEDED BY D-200, kept on disk (sources c2b7080e): the v5-proportioned cel surveyor (`build_surveyor_v5.py`; sheet review_b231_surveyor_v6_preview.png, blender/preview/b231/; its export path is written and unrun) and the first style frame (`build_style_frame_v6.py`: the Earth camp painted at 3840x2160 and shrunk, cels on it; blender/preview/b248/, sheet review_b248_style_frame_preview.png; 105 s, peak 650-766 MB, about 32,500 dabs). The owner liked their COLOURS. My honest note on painted backgrounds (07:21: code holds the rules; it does not draw, its brush has no intent, composition is numbers; scanned real brush strokes would raise the ceiling) stands and LEAD gave it to the owner.
- B-247: the five Grand icons EXPORTED 6329a93a (U-210 has the keys). The Tharsis field and boulder and the tessera pair are RULED but PARKED by LEAD until the owner rules on v6 (the tessera's blocks come from `_seated(...)` in build_backdrop_v3.venus_tessera, line 1223; no file changed).
- B-246: COMPLETE (body 56bbfa4d, sheet 2 b351f2d8); 07:01 dig_up slide_max 0.55 -> 0.75, json only (d0899819; it clears a 2.0 m ceiling, not a 1.8 m tunnel: that needs a lower glove, told UNITY).
- Also waiting: U-151 (B-172's export, Blocked); B-245 (the 0.6.3 smoke read); B-242 / B-243 in Review.
RAM: 2.2-2.9 GB free 06:30-07:10. My floor: nothing under 0.3 GB free. Nothing of mine beside UNITY's lock or want.

How I run: locks listed, then RAM read, each in its own call; `tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args> -CapMB <n>` for numpy sheets, proofs and crops (`blender/scripts/crop_png.py <src> x0 y0 x1 y1 k <dst>`; it refuses beside my OWN want: delete the want first); `tools/blender_render.ps1 <key or comma list>` for exports. UNITY and I take turns one job each while both have wants (D-037): on want_unity.lock finish the job I am on, yield, file mine (Write tool) only once UNITY HOLDS the lock, poll with the want refreshed. Beside a UNITY lock: file edits only (reading images is fine).
- A slot of several light steps beside UNITY = ONE hand-held heavy_blender.lock in ONE call, UNITY asked beforehand not to file while it is up and told the moment it is released. A heavy row (a v3 sheet) takes the wrapper's own lock.
- The giants: one table blender/scripts/giants_v3.py; after ANY change to it or build_discs_v3 both far-disc proofs must stay byte-identical (hashes in reports/blender/b239_belt_table.md).
- Rulings that stand: D-190 = ONE cream puff per planet tinted by the dug cell's fill tone. B-231: the shadow shape on each part's BACK edge, crouch <= 0.98 m, lit from above. B-233's keys by PoiDef label (D-187). continue_rows only at cover >= 0.90. The shovel's reach stays 2 m.
- **Rule (LEAD, D-087):** the Beam reads as a mining tool, never a gun. Waiting on others: B-207 on PawsOnTheGround; B-204 on UNITY's capture.

## Last completed
- 11-10 07:47: B-231 round 3 (v6 cel, run 8) and B-248 the style frame (run 5): FINAL, accepted by LEAD for the owner's page (c2b7080e).
- 11-10 07:01: side_dig.json dig_up slide_max 0.75 (d0899819, json only).
- 11-10 06:32: **B-247's five Grand icons EXPORTED** 6329a93a.
- 11-10 06:08: **B-246 sheet 2 EXPORTED** b351f2d8; 02:18-02:22 its body 56bbfa4d.
- 11-10 01:28-01:36: **B-243 EXPORTED** 3ff5e37e. 00:07: **B-242 EXPORTED** 068a2918. Earlier: the archive.

## Ready for review
- With the owner (through LEAD's page, being built): the v6 surveyor sheet and B-248's style frame, both final (c2b7080e); USER-39 the C5 look-over, now in v6.
- In Review until UNITY's import and captures: B-224, B-223, B-225, B-233, B-242, B-243 (U-208), B-246 (U-209), B-247's icons (U-210).

## Handoffs (unrouted only)
- -> UNITY (07:02, d0899819): dig_up slide_max 0.75, json only, the png byte-identical; what it clears and what it does not.
- -> UNITY (06:33, 6329a93a): icons/catalogue/{hadal_maw, vortex_whale, polar_hydra, diamondback_colossus, umbral_leviathan}; icon key = icons/catalogue/ + the last part of the creature's rig key; each json carries "creature".
- -> UNITY (B-246, 56bbfa4d / b351f2d8): side_dig's clips, contact, slide_max, sockets.hand, carry / ready, the fist; the five fx keys of sheet 2.

## Blockers
none. Waiting on: the owner's answer on v6 (LEAD's page); LEAD's answer on whether B-247's two v3 repaints still go ahead.

## Proposals (undecided only)
- The boil as two full part sheets (A / B) swapped by texture on the 12 Hz clock (in the 07:15 message to LEAD).

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
none held (last: 11-10 07:45:34-07:45:59, the surveyor sheet's run 8). No want on file. No background waiters.
