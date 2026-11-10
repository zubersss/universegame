# UNITY STATUS
Updated: 2026-11-10 05:58 · Session: 13 (restarted 11-10 00:5x on Fable 5.2, address zuber-57; every session paused 02:24-05:55; earlier entries: coordination/status/archive/UNITY_2026-11-10.md, UNITY_2026-11-09.md)
## Current task
U-209 (D-196, the owner's 0.6.2 playtest: the dig as one motion), the TOP CARD. Started 01:26. Part 1 is in git and compiled (8314a5c2: compile 0 / 0, EditMode 518/518 at 02:18); DigResponseTests (PlayMode) are written and have NOT run. Part 2 (B-246's side_dig sheet, the two rest states, the fist) is half written in the tree and does NOT compile as it stands.

RESUME POINT (for a restarted window), in order:
1. Finish part 2 in the tree, files only (uncommitted: Editor/ArtImporter, ArtSockets, SheetAnimatorBuilder; Rendering/ArtMaterials; Player/RigToolView; Tests/Unit/Play/SceneCapture; tools/unity_capture.ps1):
   - WRITTEN: ArtClip / SheetClip carry "contact" and "slide_max"; ArtSockets reads "blade_tip", side_dig's "hand" rows and its "carry" / "ready" objects ([angle, swing, behind]); SheetAnimatorBuilder puts side_dig's clips in the side sheet's controller as side_b's (SideSiblings); RigToolView reads the dig sheet's hand table for frames named side_dig_<i>, the clip's slide_max at a swing's start, the rest poses (CarryAngle / StowAngle are now INSTANCE methods: angle + swing x the arm's own angle); SceneCapture.CaptureU209Strips (ten strips; its name is in unity_capture.ps1).
   - TO WRITE: DigResponseTests still calls RigToolView.CarryAngle / StowAngle statically (make it view.CarryAngle(false), and compare the rest angle through view.ArmDegrees: the tool takes a share of the idle arm's swing); the fist overlay (props/rig/grip_fist: a child renderer over the tool at the glove, turned to the tool's angle, on the dig clips, the aim holds and the ready pose; not stowed); dig_fwd against dig_fwd_near picked by which clip's contact glove meets the target with the smaller miss (DigPose.Contact from each clip's contact frame's socket); on a dig clip the slide held over drawings 0-3 and halved on the recover (BLENDER's easing; SwingReach is the idle glove's); JetpackOverlay: a side_dig frame reads the side sheet's back socket of frame 0 (the dig sheet has none); a "near" strip in CaptureU209Strips (LEAD wants: a tap, the shovel down / forward / near / up, the Beam, a past-reach click).
2. ONE check, RAM read in its own call first: `tools/unity_check.ps1 -ExecuteMethod Meridian.EditorTools.CheckSetup.Run -Graphics -SkipPlayMode` (imports side_dig and grip_fist, registers the sockets and poses, rebuilds the side controller; compile + EditMode), then `tools/unity_test.ps1 -Mode PlayMode -Filter 'DigResponseTests|DigFeelTests|RigModuleTests|ShovelPlayTests|ShovelHollowPlayTests|DigRunPlayTests'` and LeadQA D1DigRunTests; then `tools/unity_capture.ps1 -Name u209 -Test CaptureU209Strips`. Commit the import by explicit list (the two art keys' metas, Generated/Sheets/characters/surveyor/side* controllers and clips, the registry asset, the groups).
3. Send LEAD DigResponseTests' rows and the strips (LEAD judges in that order, then the reach). The reticle, the chips and the contact glow stay on placeholders until BLENDER's sheet 2.
4. Then: ONE EXTRA ROW for LEAD's cause hunt riding a capture lock (a BC7 copy made in CaptureU207Backdrop beside the imported BC7); BudgetGate with Earth C0 within 0.3 ms; BUILD 0.6.3 (U-209 + what is green) → U-197 (collapse) → U-198 (audio) → U-208 (the giants' close view; B-243's handoff is in BLENDER's 01:4x message and b237_limb_band_design.md).

WHAT U-209 IS IN CODE (8314a5c2), so nothing is re-derived:
- Player/DigStroke.cs: no Unity objects, no allocation. A press starts a swing that frame and commits it; a press in the last 0.15 s is buffered; held swings chain with no gap; the target is fixed for the swing; five drawings at 12 Hz, the contact on the second (5 frames after the press at 60 fps); a contact's work = the swing's 0.4167 s over the D1 stroke time; kept 1.5 s a target in four slots, a cursor drifting under 0.5 m keeps its target; the Beam is on from the press' frame for 0.1 s at least and works by the second. PlayerRigInput steps it (IDigWorld) in place of the hold timer; holdUse, AimAt, Use and StrokeProgress stay.
- RigTools.DigTarget / Workable / DigOrigin (the shoulder, 0.95 m over the feet) / workables (probes from BaseBuilder, SolariteCrystals, ResourceFinds): inside the tables' reach the aim itself; past it the last point inside the reach on the aim line from the shoulder, or the nearest back along it with something to dig; nothing there: a whiff.
- Player/DigPose.cs: the blade's tip on the contact point: the tool along the line glove → target, slid back through the glove for a near target (up to the clip's slide_max), the body's lunge for a far one (up to 0.25 m); the miss named where neither reaches.
- RigToolView: at rest the dig tool is READY for 1.5 s after a swing, then STOWED behind the body (no cursor tracking; the other modules keep the aim); the swing's five drawings; the Beam's angle damped 0.06 s, its ray from the muzzle to the target and a glow at its end; the reticle (ring or cell; white in reach, amber pulled in, pale for nothing) and a three-stage crack mark; the surveyor faces the target for the swing (SpriteCharacterView.StrokeFacing / SetStrokePose / PlayStroke) and keeps that side (PlayerController.Face).
- DigFeel: a chip (1-2 crumbs, a 1 px kick, a knock pitched by tier) on a contact that leaves the cell shut, a whoosh at the swing's start; AudioDirector: Sfx.Swish / Chip and the Beam's hum (SfxSynth placeholders).
- Tests: Tests/Unit/DigStrokeTests.cs (12, green in the 518); Tests/Unit/Play/DigResponseTests.cs (7, not yet run); RigModuleTests' two rows updated for the carried dig tool and the tap's 0.1 s ray.

## Last completed (this session, all pushed)
- U-192's captures (936dcf05): LEAD marked U-192, B-223, B-224, B-233 Done.
- B-243's import (2a32ccfe); B-242 wired and shot (568634e3, 70220e18, ca74b4c5): B-225, B-242, B-197 Done.
- D-194 (a) on Direct3D 11 (ca2d030c, perf_2026-11-10.md) → D-197; the pin (79bc423b); the one check 01:35-01:41 (27 passed, 1 skipped).

## Next up
See the resume point. In the gaps, unchanged: name the AI's first-time frame (~86 frames after the spawn, Earth only); the gate's C0 draw-call row on a fixed creature set; U-202 part 2's four readings a build; the capture's UI pass draws panel text soft (LEAD: the capture, not the game; fix when a UI capture next matters).

## Ready for review
U-206 (the next smoke's smoke_21 Mars); U-205's G5 objects and smoke_36's pocket (the next smoke). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
(none open; B-246's handoff from BLENDER is taken: commit 56bbfa4d, its 02:2x message)
## Blockers
(none)
## Proposals
- P-U209-1 (the body's clip until B-246): ACCEPTED by LEAD 01:5x and now moot: side_dig is exported.
- P-U209-2 (the shovel's reach): WITHDRAWN on LEAD's ruling 02:0x: the reach stays the tables' 2 m from the body; near targets by the slide.
- P-U209-3 (the rhythm nodes): dig_rhythm_1 / _2's stats (rhythm_step, rhythm_max) are in SkillTree.json but no code reads them today; "dig_rhythm's bonus as now" is therefore nothing. With per-target work it is one line (each consecutive contact on a target adds rhythm_step more work, up to rhythm_max): yes or no.
- P-U209-4 (0 B per swing): read as the swing adding nothing over an idle frame (the test's row). The frame a cell OPENS allocates in the terrain edit as before U-209 (RigTools.BrushCells' list and sort, new density blocks, the chunk's mesh): not driven to 0 in this card.
- P-U209-5 (the carry pose's scope): the dig slot only (the shovel and the Beam). The Grapple, the Survey and the Builder keep pointing at the cursor with the button up: their aim is their feedback before a click.
## For USER_ACTIONS
(none new)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat, regenerated animator.controller files, link.xml deletions, UnderwaterTint.mat, AddressableAssetSettings.asset's hash line): never staged; commits list files explicitly. perf_2026-11-10.md: a BudgetGate run rewrites the whole file: restore the readings section from git under the gate's rows after a gate run. The session's scratchpad holds capture_part.ps1 (one capture as a part of a chain under one lock: -First takes it, -Last releases it); not needed to resume.
## HeavyJobLock
none held; no want. No background waiters.
