# UNITY STATUS
Updated: 2026-11-10 11:19 · Session: 13 (restarted 11-10 00:5x on Fable 5.2, address zuber-57; every session paused 02:24-05:55; earlier entries of today and the 08:31-09:57 status in full: coordination/status/archive/UNITY_2026-11-10.md)
## NOW (11:19): BUILD 0.6.3 IS THE OWNER'S BUILD (LEAD 11:1x; U-209, U-205, U-206 Done). U-211 in work, LOCK-FREE until LEAD says
- LEAD is editing Assets/_Game/Tests/LeadQA/*.cs (its tests' isolation): NO Unity run until LEAD's message; then LEAD wants ONE PlayMode run of the three LeadQA classes in one process (`tools/unity_test.ps1 -Mode PlayMode -Filter 'D1DigRunTests|M1LoopTests|M3InnerTests'`).
- LEAD's question on the smoke (the reticle on the cursor in smoke_31, 32, 49-53) is answered and closed: the smoke takes rig.owner away round its scripted digs (BuildSmoke.cs:456, BuildSmokeD1.cs:95 and 326); in play the reticle at rest sits on the next contact (asserted: DigResponseTests.PastReachDigsAtTheClampAndNothingInReachWhiffs' last block, b4ad405c).
- U-212 (the NEXT build, small, not now; read its card): the smoke keeps the owner on in every shot with a reticle or a stroke, 65 as a contact frame on fresh ground, a Beam shot mid-dig; the brackets and pip under the surveyor; BLENDER's new pip (B-249); the red empty brackets fade or hide when a creature is inside them; ON BLOCK GROUND THE RETICLE SHOWS AS TWO OR THREE DASHES BY THE FEET, NOT CORNERS ON A CELL (Mercury, Venus, the floes: mine, RigToolView.UpdateReticle's corner branch); the Hadal Maw in front of the shallow seabed's sand (smoke_43); G5's two soft Mars pieces (smoke_18) named from the smoke's log.
- The cause hunt's extra row is done and in the perf report (53f45a31): the BC7 made in the capture costs what the imported BC7 costs: the format, not the import; D-197's reopening clause answered (no).
- U-211 SO FAR (11:04-11:16, two diagnostics, uncommitted files Tests/Unit/Play/AllocByTypeTests.cs (run once, 11:16) and AllocByMarkerTests.cs (written, NOT yet compiled or run); both run only with MERIDIAN_ALLOC_DIAG set):
  - AllocByTypeTests (every script type switched off in turn, 40 frames each; base 300 frames): SPACE parked: 456 B a frame, constant (floor 290): Meridian.Space.SpaceMap is the one allocator (-161 B a frame without it). MARS settled (120 frames after the entry): median 290 = the floor, 5 burst frames in 300 (the most 4 486 B): no steady allocator; MARS DUST STORM: 290, the floor. So the gate's red Mars and Space figures (79-620 KB per 300 frames) are the seconds straight after a transition, which is also why two readings differed 2-3 times. Switching DustStorm, HazardSystem, SolarFlares or CameraFollow off and on allocates by itself (OnEnable): not a steady cost.
  - NEXT: SpaceMap's 160 B a frame (read its Update); the gate's GC window to begin on a settled scene (quiet frames after the transition), with the transition's own tail printed as its own figure; AllocByMarkerTests (the Editor profiler's frames read back by sample path) for the bursts, the cell-open frame's buffer and the creature AI's first-time frame.
## Earlier (11:03): BUILD 0.6.3 written, probed and smoked
- Build/MERIDIAN_0.6.3/MERIDIAN.exe (release, 520 MB) and Build/MERIDIAN_0.6.3_dev (587 MB); tree eee8e5b2 (GameInfo 0.6.3); the reports' commit 6edc5562.
- One lock 10:36:30-10:50:48, three calls (scratchpad job_part.ps1: -First takes the lock, -Last releases it): `unity_build.ps1`; `unity_profile.ps1 -Probe -SkipGate -Control 0.6.2` (BUILD MEMORY GREEN; every frame and transition row within -3.8 to +4.1 % of 0.6.2's dev player probed in the same lock); `unity_build.ps1 -Release`.
- Smoke 10:51-10:57 (its own lock): player exit 0, done marker, 79 screenshots, 0 error lines: coordination/reports/unity/smoke_0.6.3/.
- The sweep (tests_2026-11-10.md, "Notes on 0.6.3's sweep"): EditMode 522/522; PlayMode slices 1-7 green after three TEST faults were fixed (the serpent row slid on Venus' deck wind and passed by luck; D-193a: the AI rows' warm-up is 150 frames AND 1.0 s; M1LoopRun1 dug a fixed column a workable can stand on). LeadQA M1Loop: green alone (space leg 7.5 s), red once in one process after D1DigRunTests (space leg 90 s): LEAD's row, LEAD's to fix; I told LEAD what a Core load resets and what it does not (11:0x message).
- BudgetGate GREEN on its second reading 08:53 (13c76d1f) with the LIVE GC rows (D-201): Earth 166 B, Earth C0 166 B per 300 frames; RED and not gating (U-211): Space 208 577-619 985 B, Mars 79 163-131 818 B, Mars dust storm 1 300-7 284 B, Mars FX peak 822-1 084 B.
- U-209: in Review; Done on LEAD's 4x crops of the smoke's tool-in-hand frames and BLENDER's read (B-245).

## Current task
None in work. Waiting on LEAD's and BLENDER's read of 0.6.3 (a fault they find comes first). LEAD's order after 0.6.3: U-211 → U-199 (on the owner's yes; D-200: drawn frame sheets on the side-sheet pipeline, nothing to code until the figure is accepted) → U-197 → U-198 → U-210 → U-208.

RESUME POINT, in order:
1. If LEAD or BLENDER names a fault in 0.6.3's smoke: that first (a fix, the dig slice, a rebuild by the three-call chain above, the smoke).
2. The cause hunt's extra row (owed since 07:09, never run): `tools/unity_capture.ps1 -Name u207 -Test CaptureU207Backdrop` (it now measures a fourth set: BC7 compressed in the capture from the PNGs, beside the imported BC7; SceneCapture.cs, 3743bc8a). Its rows go under "The surface" in perf_2026-11-10.md; the pictures u207/1_bc7.png … are re-shot by the run (commit them or restore them, say which).
3. U-211 (read its card on the board first; LEAD's notes for it so far): (a) make the gate's GC row repeatable before chasing causes (Space and Mars read 2-3 times apart in two readings 17 minutes apart: a fixed scene state); (b) Mars', Space's and the storm's allocators; (c) the frame a cell opens (116 862 B the first time, then 19 450, then about 1.1-1.3 KB: which buffer, by a Profiler capture of that one frame); (d) name the creature AI's first-time frame (the spike note gains the slowest creature: species, state, ms; two timestamps a creature in the director) and why this test's frames are shorter than on 11-09; (e) CreatureDirector.LastAiAllocBytes off the dead counter (CreatureTests.MeasureAi prints the live figure beside it already and still asserts the dead one).

WHAT TODAY ADDED THAT A NEW WINDOW MUST KNOW:
- THE ALLOCATION COUNTER: `System.GC.GetAllocatedBytesForCurrentThread` reads 0 B for any allocation in Unity's runtime. Never measure with it. Live: `Unity.Profiling.ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC Allocated In Frame")` (LastValue = the last whole frame; every thread; the Editor's own floor is about 290-330 B a frame: read it with every root object inactive and take it off) after a control (a 64 KB array must show); for a synchronous call `Assert.That(() => …, Is.Not.AllocatingGCMemory())` with `using UnityEngine.TestTools.Constraints; using Is = UnityEngine.TestTools.Constraints.Is;`. Tests/Unit/Play/AllocBreakdownTests.cs reads a frame's bytes part by part.
- Found and fixed with it: TerrainStreamer.CurveAt (two delegates a call: 6 KB a frame everywhere, 54-115 KB at rest in the dig slot), ArtMaterials.SocketFor (a key string a call: 88 B a frame from the Beam's cable). Earth as the game runs: the Editor's floor.
- The dig slot's cost at rest (SceneCapture.CaptureU209Cost, one process, interleaved): +0.39 to +0.45 ms a frame before, +0.10 to +0.13 after TerrainStreamer.CurveAt keeps a column's curve; RigTools.DigTargetKept (the reticle's: the last walk while the cursor, the shoulder and the ground stand, 6 frames at most; TerrainStreamer.EditVersion) came after that capture and is not measured apart.
- U-209 in code: the archive's 08:31-09:57 block ("WHAT U-209 IS IN CODE"); since then only the swish's pivot (the contact drawing's tool origin) and the above.
- Test faults that looked like regressions and were not: a test that stands the surveyor on Venus' cloud deck must disable Planet/Weather/VenusWind (it pushes a grounded surveyor 0.875 m/s, always); a warm-up counted in frames moves with the frame rate; a scripted dig at a fixed column beside a landing spot can meet a workable.
- unity_test.ps1 leaves `want_unity.lock` when it is BLOCKED by BLENDER's lock: remove it and poll (BLENDER's ask); BLENDER chains 10-20 s jobs, so read RAM and call at once.

## Last completed (this session, all pushed)
- BUILD 0.6.3: the sweep, the gate, the builds, the probe, the smoke (6edc5562).
- U-209 parts 1-9 and the reticle's cost (8314a5c2 … 13c76d1f); B-246's sheets 1 and 2 and B-247's icons imported.
- The dead allocation counter found; six tests and BudgetGate moved to the live measure (78ad3014, afaf8fcb, 13c76d1f); D-201.
- Earlier today: U-192's captures; B-243's import; B-242 wired; D-194 (a) on Direct3D 11 → D-197; the pin.

## Next up
See the resume point. In the gaps, unchanged: the gate's C0 draw-call row on a fixed creature set; U-202 part 2's four readings a build; the capture's UI pass draws panel text soft (the capture, not the game).

## Ready for review
BUILD 0.6.3 (smoke_0.6.3: 79 shots; LEAD's crops: 65, 66, 67, 3b, 31, 32, 47, 49-53, 61). U-209 (Review). U-206 (smoke_21 Mars, this smoke); U-205's G5 objects and smoke_36's pocket (this smoke). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
(none open. BLENDER's note for LEAD stands: a 1.8 m tunnel still buries dig_up's tip 0.13-0.21 m; that needs a lower glove (a new low dig_up drawing), not more slide.)
## Blockers
(none)
## Proposals
- P-U209-7: CreatureDirector.LastAiAllocBytes off the dead counter: LEAD put it into U-211 (the director's runtime code stays out of the release tree).
- (P-U209-3 … 6: ruled and built; in the archive.)
## For USER_ACTIONS
(none new)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat, regenerated animator.controller files, link.xml and its meta, UnderwaterTint.mat, AddressableAssetSettings.asset's hash line, MERIDIAN_SETUP.md): never staged; commits list files explicitly. perf_2026-11-10.md: a BudgetGate run rewrites the whole file: save everything from "## The gate's two readings today" down first and put it back under the gate's rows (the probe appends its own sections at the end).
## HeavyJobLock
none held; no want. No background waiters.
