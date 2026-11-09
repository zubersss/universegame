# UNITY STATUS
Updated: 2026-11-09 14:0x · Session: 12 (restarted ~14:02 on Fable 5.2, context rebuilt from the repo; earlier entries: coordination/status/archive/UNITY_2026-11-09.md, UNITY_2026-11-08.md)
## Current task
14:0x: U-194 Build 0.6.1 RESUMED after the window restart. The chain so far (one lock per slice, as 0.6.0): compile 13:38 0 / 0, EditMode 493/493, the B-227 import (7a13536a), PlayMode slice 1 23/24 (1 skipped), slice 2 25/29 (3 skipped; the one fail is the ruled AI worst-frame note, 1.31 ms). Slice 3 (lock 13:56:50) was cut off by the restart at ~14:00 with no results: its lock stood stale until 14:05 (no Unity running), removed, the stray InitTestScene deleted.
14:3x: THE PLAYMODE SWEEP IS IN (one lock per slice, 14:05-14:29, RAM 1.5 -> 2.6 GB): C 33/34 (InnerCreatureTests' AI worst frame 1.42 ms in the slice; alone 0.135 ms), D 28/28, E 33/33 (ShovelPlay / ShovelHollowPlay added to 0.6.0's filter), F 22/24 (1 skipped) with ONE NEW RED, diagnosed and fixed in the test's staging: TerrainStreamingTests.EarthStreamsWithinRadiusBudgetAndFrameTime logged "solid rescue: Player buried ... lifted 0.76 m". Cause: the test flies the camera 200 m off with the follow disabled, the camp's chunks unload under the simulated surveyor, it falls through the missing outline and the rescue logs once the flight's last frames run past ~0.4 s (this run avg 2.16 ms a frame; earlier runs were quicker): U-165's BudgetGate case exactly. Fix: the surveyor held still for the flight, as BudgetGate does (no threshold touched, no runtime change). Re-run alone 14:28: TerrainStreaming 2/2 (avg 1.57 ms, p99 apply 1.84 ms, GC 0 B); the two AI timing tests alone: CreatureTests worst frame 1.000 ms (avg 0.030, p99 0.064), InnerCreatureTests max 0.135 ms. Next: LeadQA M1Loop, M3Inner + D1DigRun, then the release lock (BudgetGate, the dev build + probe, the release build), then the smoke (79 shots).

## Last completed
- U-193 part 2 (5c3f2d9b; slice 3 in one lock 13:10-13:21): compile 0 / 0, EditMode 493/493; PlayMode ShovelPlay / ShovelHollowPlay / RigModule / DigPlace / DigRunPlay green (ShovelPlay 2/2 after the slot fix), Base / MenuHud / AudioDirector / HintPlay / Fx 18/18; LeadQA D1DigRun 1/1 (the shovel 0.48 s at T1, 2.00 s at T3). CaptureU193Shovel: u193/1_shovel_midswing, 2_shovel_flick, 3_tree_the_beam, 4_tool_slot_beam (viewed).
  - The HUD tool slot (HudToolSlot): under the Rank medallion; the module's icon (icons/tools/*, preloaded at build, polled each frame: a load started inside a probe callback never reported done; the shovel's icon shows 1 frame after a switch), its name in ink, "< Q" / "E >" caps as bound; follows a switch and The Beam's purchase; hidden aboard; MenuHudTests' layout check covers its tags.
  - The shovel's scoop sound (SfxSynth.Shovel, seed 193, CC0; credits).
  - Slice 1's six: the Play suites get the Beam through the test-only SkillStats.ToolOverride (PlayModeDefaults; null in the game, ShovelTests asserts it); the look follows the tool (RigLooks.DigMk); the reach is read from the body; the arc test samples a whole stroke; LeadQA's hollow (a body moved while not simulated snaps back to its transform) fixed by LEAD (cceb9e6d), mirrored in ShovelHollowPlayTests.
- U-194 part 1 (4b0490ed, code only): BaseBuilder.FootOf (the shelter walls on the drawn ground; BaseTests: smoke_18's shelter, feet 0.34 / 0.26 m, lamp -0.30, every base +0.00 m); smoke_64 (crafting, thruster_mk2), smoke_65 / 66 (shovel mid-swing / flick), smoke_67 (the tool slot with The Beam): 79 shots; GameInfo 0.6.1.
- U-193 part 1 (a0f489e1, 11:36). 0.6.0's post-build sweep green (f6765a66); U-188 Build 0.6.0 DONE (40a0b641).

## Next up
U-194 Build 0.6.1 (the full PlayMode sweep in slices + LeadQA, BudgetGate, the release, its smoke, the dev probe) → U-189 + U-191 (the giants), U-177, U-192, U-179.

## Ready for review
U-193 (5c3f2d9b + a0f489e1; u193/1..4). U-166 (b9d553de; smoke_42 with the next build). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
→ LEAD (for a BLENDER card): ui/hints/dig_down's picture still shows the Beam drilling (B-213); its words now say the shovel (D-182).
## Blockers
(none)
## Proposals
(none open)
## For USER_ACTIONS
(none)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat _MainTex fills, the surveyor side animator.controller, link.xml deletions, AddressableAssetSettings line endings): never staged; my commits list files explicitly. MERIDIAN_SETUP.md at the repo root is untracked and not mine. BLENDER's B-227 icons/tools/*.png + json are in the tree uncommitted (theirs).
## HeavyJobLock
none held (released 13:21:47); no want (U-194's goes on file after B-227's export). No background waiters.
