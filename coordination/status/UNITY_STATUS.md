# UNITY STATUS
Updated: 2026-11-10 01:47 · Session: 13 (restarted 11-10 00:5x on Fable 5.2, address zuber-57; earlier entries: coordination/status/archive/UNITY_2026-11-09.md, UNITY_2026-11-08.md)
## Current task
U-209 (D-196, the owner's 0.6.2 playtest: the dig as one motion), the TOP CARD. Started 01:26, code only so far. One lock is owed first: U-192's three captures for LEAD (the capture test is not written yet).

RESUME POINT (for a restarted window), in order:
1. U-192's captures: write SceneCapture.CaptureU192 (add its name to tools/unity_capture.ps1's ValidateSet): (a) the bay docked at Earth's Waystation with the Pilgrim on its cradle (smoke_10's frame; CaptureU204Panels has the docking: director.SetView(Space), bay.Dock("earth")), (b) the catalogue page with the Site icons (CataloguePanel, the Site branch), (c) the veil serpent at 1x beside the Venus station (InnerCreatureTests has its staging). One lock, pictures to coordination/reports/unity/u192/, the list to LEAD.
2. U-209's code, in this order (the card: board line "### U-209"; LEAD's notes on what the old code does are in it):
   - DONE, compiled in the 01:35 check: Player/DigStroke.cs (the state machine: a press starts and commits a swing; a press in the last 0.15 s is buffered; held swings chain with no gap; the target fixed at the swing's start; five drawings at 12 Hz, the contact on drawing 2 at 0.083 s; work a contact = swing ÷ the D1 stroke time, kept 1.5 s per target in four slots; the Beam on from the press' frame for 0.1 s at least, work by the second); RigTools.DigTarget / Workable / DigOrigin / DigPoseReach / StrokeAxis / workables (probes added in BaseBuilder, SolariteCrystals, ResourceFinds).
   - NEXT: PlayerRigInput implements IDigWorld and steps the stroke in place of the hold timer (keep holdUse, AimAt, Use, StrokeProgress = the target's work; Using = held or a stroke under way; cancel the stroke when the module is not the dig slot; set rig.StrokeAxis before the Dig).
   - RigToolView: a carry pose at rest for the dig slot (no cursor tracking with the button up; the other modules keep the aim); in a swing the blade's tip AT the target on the contact drawing: the tool lies on the line hand → target, slid back through the hand for a target nearer than the blade (1.33 m), the squash root lunging up to 0.25 m for a farther one; the wind-up before and the follow-through after; the Beam's angle critically damped (~0.06 s), its ray on Stroke.Phase == Beam, a contact glow at the hit; the reticle (the brush ring at the target every frame; tint by state: in reach, clamped, nothing to dig) with a crack stage from Stroke.WorkAt.
   - SpriteCharacterView: the facing held on the target for the swing (the flip only between swings), a stroke pose on the squash root (lean ≤ 6°, recoil ≤ 0.06 m, the lunge), dig_down / dig_fwd / dig_up and the five aim poses played by name when the sheet has them (B-246).
   - DigFeel: a chip (one or two crumbs, a thud, a 1 px kick) on a contact that does not open; the debris along rig.StrokeAxis; SfxSynth: a whoosh at the swing's start, a chip by tier, the open's crunch.
   - Tests: Tests/Unit/DigStrokeTests.cs (EditMode, a fake world at a 1/60 step) and Tests/Unit/Play/DigResponseTests.cs (the card's rows); then the old tests that held the button for a timed stroke (ShovelPlayTests, ShovelHollowPlayTests, DigRunPlayTests, RigModuleTests' "turned to the aim", BuildSmokeD1's StrokeProgress wait, SceneCapture's u193 / u195 shots); LeadQA D1DigRunTests is LEAD's.
   - Captures: the frame strips (every frame from the press to the contact + 6, tiled) for the shovel down / forward / up and the Beam, on Topsoil and in Stone, a tap, a past-reach click; ONE EXTRA ROW in that lock for LEAD's cause hunt (a BC7 copy made in the capture beside the imported BC7 backdrop); BudgetGate with Earth C0 within 0.3 ms.
3. Then BUILD 0.6.3 (U-209 + what is green) → U-197 (collapse) → U-198 (audio) → U-208 (the giants' close view; BLENDER's B-243 handoff is in its 01:4x message and b237_limb_band_design.md).

## Last completed (this session, all pushed)
- D-194 (a): the two perf captures on Direct3D 11 (ca2d030c; perf_2026-11-10.md). The Editor's grainy-BC7 penalty is on Direct3D 11 too, so the API is not its cause; LEAD ruled D-197: the walls stay RGBA32, the backdrops BC7, the bars 1.52 (the fill alone 1.15, a walled room 1.24), nothing under 0.15 in a one-process ratio is a finding. U-207 closed.
- D-194's pin (79bc423b): ProjectSettings carries Direct3D 11 alone; compile 0 / 0, EditMode 506/506.
- B-242 wired (568634e3 code, 70220e18 import, ca74b4c5 pictures): back_wall_sand / back_wall_basalt behind a dug cell where the band's own fill is drawn; the hole's inner shadow now also shows in the desert (it lay under the overlay); DigFeelTests.ADugCellInTheDesertShowsTheSandsWall green; b242/1..3.
- The one check (01:35-01:41): compile 0 / 0, PlayMode SeaUnder|InnerCreature|Creature|Waystation|DigFeel 27 passed, 1 skipped, 0 failed: U-192's code and D-194's tooling have now met the compiler and their tests.
- U-205's set re-shot on Direct3D 11 (3b: no sand field 25 m out).
- B-233's import (the ten Site icons) committed with B-242's (70220e18).

## Next up
See the resume point. In the gaps, unchanged: name the AI's first-time frame (~86 frames after the spawn, Earth only); the gate's C0 draw-call row on a fixed creature set; U-202 part 2's four readings a build.

## Ready for review
B-242's wiring (b242/1..3); U-205's two sea re-shots (u205/3b, 2_sea_3m); U-206 (the next smoke's smoke_21 Mars). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
→ BLENDER (answered 01:1x): a json-only planets/<giant>/close.json is addressed by the importer as a TextAsset at planets/<giant>/close/json; JsonUtility wants fixed field names and no array of arrays. B-243's exports follow that (3ff5e37e).
## Blockers
(none)
## Proposals
- P-U209-1 (the body's clip until B-246): the card says "the existing side_b dig clip re-timed so its hit frame is the contact". That clip carries a baked pick and the held tool hides on its frames (U-203, BLENDER's read of 0.6.1's smoke_66): played again, every swing would swap the shovel for a pick. I build the body's part as the facing on the target, the lean and the recoil on the squash root; dig_down / dig_fwd / dig_up play by name the moment the sheet has them.
- P-U209-2 (the shovel's honest reach): the blade's tip lies 1.33 m from the grip (shovel.json) and the lunge adds 0.25 m: 1.58 m from the hand, which sits at the shoulder (0.95 m over the feet). D1_TABLES says 2 m from the feet. In code a click is clamped to 1.58 m from the SHOULDER (and still inside the tables' 2 m from the feet); a target nearer than the blade is met by sliding the shaft back through the hand. To amend in D1_TABLES §1 from this: "reach 1.6 m, measured from the shoulder"; with the 0.9 m brush the far edge of a scoop is 2.5 m from the shoulder, and straight down the contact lies 0.63 m under the feet (the scoop to 1.5 m under them). The measured rows follow with DigResponseTests.
- P-U209-3 (the rhythm nodes): dig_rhythm_1 / _2's stats (rhythm_step, rhythm_max) are in SkillTree.json but no code reads them today; "dig_rhythm's bonus as now" is therefore nothing. With per-target work it is one line (each consecutive contact on a target adds rhythm_step more work, up to rhythm_max): yes or no.
- P-U209-4 (0 B per swing): read as the swing's own machinery (the stroke, the tool, the reticle, the chips). The frame a cell opens allocates in the terrain edit as before U-209 (RigTools.BrushCells' list and sort, new density blocks, the chunk's mesh): measured apart and reported, not driven to 0 in this card.
- P-U209-5 (the carry pose's scope): the dig slot only (the shovel and the Beam). The Grapple, the Survey and the Builder keep pointing at the cursor with the button up: their aim is their feedback before a click.
## For USER_ACTIONS
USER-42 (LEAD): the laptop was not rebooted; free RAM has held 2.1-2.9 GB since 01:01 with the three fresh sessions.
## Housekeeping
Editor churn in the tree (Generated/Models *.mat, regenerated animator.controller files, link.xml deletions, UnderwaterTint.mat): never staged; commits list files explicitly. UNCOMMITTED IN THE TREE, mine: B-243's import (planets/common.meta, 24 metas under planets/, AssetGroups/space.asset) → with U-208's first check; U-209's code so far (DigStroke.cs + its meta, RigTools, BaseBuilder, SolariteCrystals, ResourceFinds). perf_2026-11-10.md: a BudgetGate run rewrites the whole file: restore the readings section from git under the gate's rows after a gate run. The session's scratchpad holds capture_part.ps1 (one capture as a part of a chain under one lock: -First takes it, -Last releases it) and d194_part1 / part2.ps1; none is needed to resume.
## HeavyJobLock
none held (the captures' lock released 01:45:39); no want. No background waiters.
