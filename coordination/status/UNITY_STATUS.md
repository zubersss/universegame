# UNITY STATUS
Updated: 2026-11-10 15:00 · Session: 14 (the laptop rebooted 14:18; this window's address zuber-30, LEAD zuber-4a; Fable 5.2; the 13:07 status in full and everything earlier today: coordination/status/archive/UNITY_2026-11-10.md)

## NOW (15:00): U-212's remainder and U-213's camera are written; their check waits on the RAM gate (want on file)
- Found at 14:22: nothing of mine cut mid-job. Last commit de36b4f1 (13:54, U-212 part 1), pushed; no lock, no want, no Unity process; free RAM 1.35 GB (under the gate while the windows settle; LEAD read 1.6 GB at 14:35).
- THE v6 IMPORT IS DISCARDED: BLENDER took the sheets out of Assets (c262d114); the tree holds no Art .meta for them, no Generated/Sheets/characters/surveyor_v6, no v6 entry in common.asset, the common atlas or ArtMaterials (`git grep surveyor_v6 -- Assets ProjectSettings` outside Art: nothing). Nothing to commit, nothing to undo.
- LEAD's order (14:2x message): (1) this status; (2) U-212's remainder; (3) U-213 part 3, the camera behind a flag, captured at the camp and in a 10 m shaft, plus ONE camp capture at 128 px per metre; (4) U-216 the living stage on today's art, sharing that capture; then BUILD 0.6.4 (its dev build prices U-216; every driven player takes -meridianSaveRoot; no control row, D-203a).

## Landed since the 13:07 status
- U-211 (b), 16bf8110 (13:36): the autosave is taken behind the iris (TransitionDirector.BeforeReveal; a failed save is logged and the iris still opens); gone from the first frame of play. U-211 (a): gate reading 5 (13:36) GREEN with the arrival row (frames 1-299, 16 KB) and frame 0 printed; the probe gained "worst frame in the first second after a transition" (50 ms): written, NOT run on a player yet. 17/17 PlayMode incl. the three LeadQA classes, EditMode 523/523.
- U-212 part 1, de36b4f1 (13:54): items (3) the marks under the drawn surveyor, (9) the pip only in a stroke, (6, H7) block-ground marks in front of the block mesh (BlockMarkZ), (5) the red state hidden over an animal, (10, H8) the stowed tool on BLENDER's props/rig/stow_socket table (82ca3266; imported). Compile 0/0, EditMode 523/523, PlayMode DigResponse | ShovelPlay | DigFeel 21/21. NOT yet seen in a capture or on a block planet.

## GATE READING 6 (13:53, after U-212 part 1): two Earth timing rows RED; every GC row green. CAUSE NOT ESTABLISHED
- Frame time · Earth p99 21.58 ms (limit 16.6), avg 6.50, max 22.8. Chunk generation p99 2.16 ms, 5/400 over 2 ms (limit 2 ms in 99 %).
- What the four readings of today say (u211/gate_reading3-6.md): Earth frame avg / p99 / max = 6.56 / 15.18 / 25.5 (12:59), 5.40 / 7.90 / 11.1 (13:02), 5.78 / 9.73 / 17.5 (13:35), 6.50 / 21.58 / 22.8 (13:53). Reading 3, an hour BEFORE U-212 part 1 existed, has the same average and a longer worst frame: the row is a handful of 17-25 ms frames in a 300-frame window, and three or four of them decide the p99. Earth C0 (the same scene's cartoon row) stayed green in all four (p99 5.5-8.3 ms). Chunk generation p99 read 1.74, 1.85, 1.93, 2.16 ms with 2, 2, 2, 5 frames over: it has sat within 0.3 ms of its limit all day and no reticle code runs inside it.
- So the data does not point at de36b4f1, and does not clear it either. OWED BEFORE 0.6.4: two more gate readings on a quiet machine (reading 6 began 0.6 min after a PlayMode run, the shader compiler and import workers' logs stamped inside its window); if a red stays, one reading with RigToolView.cs at 16bf8110 (the reticle changes off). Nothing waived.

## Current task
U-212 part 2 and U-213 (3): WRITTEN, NOT YET COMPILED OR RUN (in the tree, uncommitted). The check waits on the 1.5 GB gate: free RAM 1.0-1.3 GB since 14:49 with nothing of the team's running (the three windows hold 1.9 GB; Windows Update is working after the reboot; Copilot, Edge WebView, Chrome, the Xbox app and Settings are open). want_unity.lock on file since 14:50, refreshed at each poll; BLENDER holds off behind it.
- U-212 (1): BuildSmoke / BuildSmokeD1 keep the Rig's owner ON; each staging dig, mound or Bore takes it off for its own call (the Unreached scope); every shot logs the owner's state ("OWNER OFF" is the report's grep); on foot the smoke points the Rig at the ground 0.84 m ahead of the feet (a driven player's cursor was wherever the desktop left it: 0.6.3's red brackets in the air), a staging pins its own aim.
- U-212 (2): BuildSmoke.ShovelShots / BeamShot (one staging for the player's smoke and for the Editor capture): smoke_65_d1_shovel_contact (the first swing's contact drawing), smoke_66_d1_shovel_follow_through (the swing that opens the ground, drawing 3), NEW smoke_68_d1_beam_mid_dig (the cell's work between 0.35 and 0.9). The smoke is 80 shots now (tools/unity_smoke.ps1).
- U-212 (7), the Hadal Maw: KEPT OUT OF THE SHALLOWS, not sorted behind them. 0.6.3's smoke_43 viewed: behind the sand its head and lure would still stand over the sand flat. SpeciesSpec.shoreKeep = 67 m (the shallows' 40 + half a 20 m frame + half the 34 m rig): no spawn and no swim nearer the shore (CreatureDirector.TooNearShore / ShoreAt; a wanderer turns seaward). Its look out at sea is untouched. HadalMawTests +1, HadalMawPlayTests moved to the keep. NOT re-staged: the two old captures CaptureU119Maw and CaptureU128Shore spawn the Maw inside the keep and will stop at their spawn until re-staged (neither is in a sweep).
- U-212 (8): the smoke's G5 probe reads 8 m round the surveyor, pieces up to 4 m, with each drawing's px a metre.
- U-212's capture: SceneCapture.CaptureU212 -> coordination/reports/unity/u212/ (8 frames + a 2x cut of each: the shovel's contact and follow-through, the Beam mid-dig, the reticle at rest, the landing squash, Mercury's block ground at rest / contact / follow-through).
- U-213 (3), the close camera behind a flag: Camera/StageZoom.cs (off by default; a built player takes "-meridianCloseCamera" or "-meridianCloseCamera 128"); StageCamera eases the frame's share (SmoothDamp 0.34 s: within 2 % after about 1 s, 0.2 m of frame a frame at most); CameraFollow reads the world 10 times a second (underground = 3 m or more under the ground's own surface, out above 2.5 m, or ground within 6 m over the head); RigToolView's brackets and pip keep their screen size. StageCameraTests +3, StageZoomPlayTests (new). Its captures (the camp at 96 and at 128, a 10 m shaft) are not written yet.
- B-260 (a): BLENDER's v7 piece format answered (daa78ab9, coordination/reports/unity/v7_piece_format_answer.md); "play_front" agreed. LEAD ruled it 15:0x (contract v3.5 §12, D-206): my design stands; for U-216: THE STAGE NEVER COLLIDES; a rooted piece whose ground is dug away goes with the dig's puff (no save in the pilot; state what the check costs); no flip on middle, near or play_front (the normal's x flip is for foreground and far only); the reticle and a find always draw over play_front (at most 0.30 m tall).

NEXT, in order: the check (compile + EditMode + PlayMode HadalMaw | DigResponse | ShovelPlay | DigFeel | SeaUnder | ShoreCreature | StageZoom | StageCamera) and CaptureU212 under one lock -> commit -> U-213's captures -> U-216 (wind field, air, one vine chain, one lit sprite; priced on the built player) -> two gate readings -> BUILD 0.6.4 -> U-214 -> U-215 -> U-197 -> U-198 -> U-210 -> U-208. Open under U-211: the second arrival-row reading, the AI's first-time frame named, CreatureDirector.LastAiAllocBytes on the live counter, the cell-open frame re-read. U-213's surveyor and stage parts wait for the v7 pilot (D-205).

## What a new window must know (kept from today)
- THE OWNER'S SAVE SLOT (D-203): never write under AppData\LocalLow\Zubers\MERIDIAN\saves. Tests run on SaveSystem.FallbackRoot (PlayModeDefaults / EditModeDefaults); a driven player takes `-meridianSaveRoot <folder>`; unity_smoke / unity_profile pass one and REFUSE a player that predates the switch (0.6.3's two do).
- THE ALLOCATION COUNTER: `GC.GetAllocatedBytesForCurrentThread` reads 0 in Unity. Live: `ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC Allocated In Frame")` after a 64 KB control, less the Editor's floor (about 290 B a frame); or `Is.Not.AllocatingGCMemory()`.
- Gate readings: `tools/unity_profile.ps1` rewrites coordination/reports/unity/perf_2026-11-10.md (0.6.3's report). Copy the result to u211/gate_readingN.md, put the report back (`git checkout -- <the report>` restores the committed one) and check `git diff --quiet` on it.
- One Play run of one class: `tools/unity_test.ps1 PlayMode -Filter <Class>`; the bare unity_check runs the whole PlayMode (over the 20 min cap): pass -SkipPlayMode / -PlayFilter.
- Test faults that looked like regressions: Venus' deck wind pushes a grounded surveyor (disable Planet/Weather/VenusWind); warm-ups counted in frames move with the frame rate; a scripted dig at a fixed column can meet a workable.
- unity_test.ps1 leaves want_unity.lock when BLENDER's lock blocks it: remove it and poll.

## Last completed (all pushed)
U-212 part 1 (de36b4f1) · U-211 (b) and (a) (16bf8110) · U-211's table (87a556e0, 4cbd79fb, 1482880b) · D-203 (0ba0e5c7, 8eeaefcb) · BUILD 0.6.3 (6edc5562).

## Ready for review
U-212 part 1 (de36b4f1: tests only so far; captures with part 2). U-211 (a), (b) (accepted by LEAD 13:37; the second gate reading owed). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146; U-144.
## Handoffs
(none open)
## Blockers
(none)
## Proposals
- P-U213-1: under the close camera the frame's bottom stands FloorBelow x the share under the stage floor (2 m at 96 px a metre, 3 m at the shipped 64), so the ground keeps its 17.8 % of the frame: the shipped composition seen closer, not a taller slab of ground. Built that way; the captures will show it.
- P-U212-1: the Hadal Maw kept 67 m off the shore instead of sorted behind the shallow seabed (see Current task); say if the sorting is wanted as well.
## For USER_ACTIONS
(none new)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat, regenerated animator.controller files, common.asset's line endings, link.xml and its meta, UnderwaterTint.mat, MERIDIAN_SETUP.md): never staged; commits list files explicitly.
## HeavyJobLock
none held; no want. No background waiters.
