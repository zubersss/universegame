# UNITY STATUS
Updated: 2026-11-10 07:02 · Session: 13 (restarted 11-10 00:5x on Fable 5.2, address zuber-57; every session paused 02:24-05:55; earlier entries: coordination/status/archive/UNITY_2026-11-10.md, UNITY_2026-11-09.md)
## Current task
U-209 (D-196 / D-196b, the owner's 0.6.2 playtest: the dig as one motion), the TOP CARD. Started 01:26. Parts 1-5 are in git and green: 8314a5c2, 1899e88d (+ B-246's sheet-1 import), 44a79f99 (D-196b: the reach from the shoulder, the first solid point on the aim line), 61bd3943, c9d5f102 (strips), 005a42ef (part 5), c978a70f (sheet 2's and B-247's import). Last green: EditMode DigStrokeTests 13/13; the PlayMode dig slice + LeadQA D1DigRunTests 30/30 at 06:56; compile 0 / 0.

LEAD ACCEPTED the rows (06:4x): press → change frame 0; the contact 5 frames after the press; the Beam's ray and glow in frame 0; the tap; the chain; the clamp and the whiff; the open times within one swing at every tier; 0 B a swing over an idle frame; the tip on the contact 8 of 12 with the 4 allowed buries.

LEAD's four asks (06:4x), all in 005a42ef:
1. The thrusts travel: a clip's slide and lunge are fixed ONCE from its CONTACT drawing's glove at the swing's start (swingSlide / swingLunge / swingDir) and carried by the other drawings; the wind-up holds the blade back 0.46-0.71 m (dig_fwd_near) and about 1.2 m (dig_fwd). DigResponseTests asserts ≥ 0.35 m on the thrusts.
2. The dig tool is drawn in front of the body (SurveyorOrder + 1), the fist over it (+ 2); stowed: behind (− 1).
3. The strips grab a frame at the end of its own LateUpdate (Tests/Unit/Play/LateFrameHook.cs, order 32000): the coroutine's grab showed the frame before's pose with this frame's debris.
4. dig_up's slide_max 0.75: BLENDER's to raise in side_dig.json; mine is a re-import (CheckSetup) when it lands. NOT YET IN: the last run still reads 0.55 and buries 0.15-0.22 m on a 2 m ceiling.

B-246's sheet 2 is wired in 005a42ef (my stand-ins draw only where a sheet is missing): fx/dig_reticle/base (four arcs on the brush's circle or four corners on a cell, a pip on the contact, a boil on twos; untinted and tight in reach, mustard + 0.09 m past the reach, red + 0.2 m and no pip for nothing; unlit; full strength with the button down or 1.5 s after the cursor moves, else 40 %; hidden in menus and transitions), fx/dig_chip/round and /cell (the stage's frame in the ground's tone, on the brush's centre), fx/beam_contact/base (up = back along the ray, the Beam's teal), fx/shovel_swish/base (dig_down and dig_up only, from the contact drawing).

IN THE TREE, NOT YET RUN (written 07:00 under BLENDER's lock, files only):
- RigToolView: the Beam's aim pose is shown BEFORE the glove is read (on the press' frame the body raised its arm and the tool stayed at the hip for that one frame: seen in the new beam strips' frame 0). DigResponseTests' Beam row asserts the glove on the press' frame is the aim pose's.
- The twelve strips re-shot 06:59 (coordination/reports/unity/u209/*.png): on disk, NOT committed; to shoot once more after the Beam fix, then commit and send LEAD (LEAD accepts shovel_near, shovel_fwd, shovel_down, beam_fwd and the past-reach in one look; shovel_past_reach_surface now clicks feet + (2, −6) and lands a real dig at the clamp).

RESUME POINT, in order:
1. RAM in its own call, the locks; `tools/unity_test.ps1 -Mode PlayMode -Filter 'DigResponseTests|DigFeelTests|RigModuleTests|ShovelPlayTests|ShovelHollowPlayTests|DigRunPlayTests|D1DigRunTests'` (30 rows).
2. `tools/unity_capture.ps1 -Name u209 -Test CaptureU209Strips`; look at beam_fwd's frame 0 (the tool in the raised hand); commit RigToolView.cs, DigResponseTests.cs, the strips, the day's test report; send LEAD the strips and two notes: the brackets and the crack stand on the brush's CENTRE and the pip on the CONTACT (BLENDER's preview centres the pip); dig_up waits for slide_max 0.75.
3. When BLENDER's side_dig.json change lands: `tools/unity_check.ps1 -ExecuteMethod Meridian.EditorTools.CheckSetup.Run -Graphics -SkipPlayMode`, the tip test again, commit the import by explicit list.
4. BudgetGate with Earth C0 within 0.3 ms (the gate rewrites perf_2026-11-10.md: restore the readings section from git under its rows); ONE EXTRA ROW for LEAD's cause hunt riding a capture lock (a BC7 copy made in CaptureU207Backdrop beside the imported BC7).
5. BUILD 0.6.3: the full sweep in slices, the gate, the dev build + probe with 0.6.2 as the control in the same lock, the release build, the smoke (three locks) → U-197 (collapse) → U-198 (audio) → U-210 (B-247's five Grand icons are imported: icons/catalogue/ + the last part of the creature's rig key) → U-208 (the giants' close view; B-243's handoff, b237_limb_band_design.md).

WHAT U-209 IS IN CODE, so nothing is re-derived:
- Player/DigStroke.cs (+ IDigWorld, DigPhase, DigContact): no Unity objects, no allocation. A press starts and commits a swing that frame; 0.15 s buffer; held swings chain; five drawings at 12 Hz, the contact on drawing 1; a contact's work = the swing's time over the D1 stroke time; four targets kept 1.5 s (SameTargetM 0.5); the Beam on ≥ 0.1 s, working by the second.
- Rig/RigTools.cs: reach 2 m (Beam 5) from the shoulder (DigOrigin, 0.95 m); DigTarget = the first solid point (workables, the drawn field, tiles) on the line from the shoulder through the cursor; DigPoint = the contact pushed 0.75 × the brush's radius into the ground.
- Player/RigToolView.cs: READY 1.5 s after a stroke then STOWED; the swing on the sheet's dig clips (side_dig: dig_down / dig_fwd / dig_fwd_near / dig_up; the forward pair picked by the smaller miss) with the tip on the contact (Player/DigPose.cs: slide up to the clip's slide_max, lunge up to 0.25 m); the Beam damped 0.06 s with its ray to the contact; the reticle, the crack, the contact flare, the swish (B-246), the fist.
- View2D/SpriteCharacterView.cs: HasClip, PlayStroke, ShowStroke (the body's drawing by the stroke's clock, shown the same frame), StrokeFacing, SetStrokePose. Mining/DigFeel: Throw, Chip, the debris from the contact. Audio: Sfx.Swish / Chip, the Beam's hum (SfxSynth placeholders until U-198).
- Tests: Tests/Unit/DigStrokeTests.cs (13); Tests/Unit/Play/DigResponseTests.cs (7); RigModuleTests; SceneCapture.CaptureU209Strips (12 strips).

## Last completed (this session, all pushed)
- U-192's captures (936dcf05): LEAD marked U-192, B-223, B-224, B-233 Done.
- B-243's import (2a32ccfe); B-242 wired and shot (568634e3, 70220e18, ca74b4c5): B-225, B-242, B-197 Done.
- D-194 (a) on Direct3D 11 (ca2d030c, perf_2026-11-10.md) → D-197; the pin (79bc423b).
- B-246's sheets 1 and 2 and B-247's icons imported (c978a70f).

## Next up
See the resume point. In the gaps, unchanged: name the AI's first-time frame (~86 frames after the spawn, Earth only); the gate's C0 draw-call row on a fixed creature set; U-202 part 2's four readings a build; the capture's UI pass draws panel text soft (the capture, not the game).

## Ready for review
U-209's rows (ACCEPTED) and its strips (to re-send after the Beam fix). U-206 (the next smoke's smoke_21 Mars); U-205's G5 objects and smoke_36's pocket (the next smoke). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
(none open; B-246's sheets 1 and 2 and B-247's icons are taken)
## Blockers
(none)
## Proposals
- P-U209-3 (the rhythm nodes): dig_rhythm_1 / _2's stats (rhythm_step, rhythm_max) are in SkillTree.json but no code reads them today. With per-target work it is one line (each consecutive contact on a target adds rhythm_step more work, up to rhythm_max): yes or no.
- P-U209-4 (0 B per swing): read as the swing adding nothing over an idle frame (the test's row: idle 0 B, swinging 0 B). The frame a cell OPENS allocates in the terrain edit as before U-209: not driven to 0 in this card.
- P-U209-5 (the carry pose's scope): the dig slot only (the shovel and the Beam). The Grapple, the Survey and the Builder keep pointing at the cursor with the button up.
- P-U209-6 (the reticle's marks): the brackets and the crack on the brush's centre (what opens), the pip on the contact (where the blade lands); BLENDER's preview puts the pip in the circle's middle. Mine is built; say if the preview's is wanted.
## For USER_ACTIONS
(none new)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat, regenerated animator.controller files, link.xml deletions, UnderwaterTint.mat, AddressableAssetSettings.asset's hash line, MERIDIAN_SETUP.md): never staged; commits list files explicitly. perf_2026-11-10.md: a BudgetGate run rewrites the whole file: restore the readings section from git under the gate's rows. The session's scratchpad holds capture_part.ps1 (one capture as a part of a chain under one lock); not needed to resume.
## HeavyJobLock
none held; no want. No background waiters. (BLENDER held heavy_blender.lock at 07:00.)
