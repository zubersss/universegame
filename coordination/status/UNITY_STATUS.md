# UNITY STATUS
Updated: 2026-11-09 12:0x · Session: 11 (restarted ~11:45, context rebuilt from the repo; earlier entries: coordination/status/archive/UNITY_2026-11-09.md, UNITY_2026-11-08.md)
## Current task
13:0x: slice 2 ran in my lock 12:51-13:06: compile 0 / 0, EditMode 493/493; PlayMode A 11/13 (D1DigRun: LeadQA's geometry, fixed by LEAD in cceb9e6d; the tool slot's icon never arrived: a load started inside a probe callback never reported done, now polled each frame, plus LEAD's few-frames real-sprite assert). Slice 3 (compile + EditMode, A + B, LeadQA D1DigRun, CaptureU193Shovel) queued behind BLENDER's B-220 lock (13:07); want filed 13:08. Code uncommitted until green.
- Slice 1 (11:40) was red, 6/18. Causes and fixes:
  (1) LeadQA D1DigRun's HeldStroke moved only Body.position of a body left unsimulated by StandAtDepth; it snapped back to its transform at the next physics step, so the aim fell in the hollow's own air (13:0x run: body = transform = 109.50, aim 110.5). LEAD added the transform line (cceb9e6d); my copy (ShovelHollowPlayTests) digs in 0.48 s against 0.50. The reach is now read from the body too (harmless; not the cause).
  (2) DigRunPlayTests / DigPlaceTests / RigModuleTests ×2 assume the Beam at the start. A test-only SkillStats.ToolOverride, set by PlayModeDefaults (as the hints are switched off), gives the Play suites the Beam. ShovelPlayTests / CaptureU193Shovel clear it. LeadQA (its own assembly) starts on the shovel. Null in the game (ShovelTests asserts it; LEAD's 11:5x condition). The look follows the tool (RigLooks.DigMk).
  (3) ShovelPlayTests sampled the arc over 40 frames (~0.06 s of a 0.5 s stroke); it now samples a whole stroke. Plus a reach-origin check (a body moved while not simulated).
- U-193 part 2: the HUD tool slot (HudToolSlot, LEAD's 11:3x ruling): a paper slot under the Rank medallion with the module's icon (icons/tools/shovel | beam | grapple | survey | builder, probed quietly; Skill Tree node icons stand in until B-227), its name in ink (SHOVEL, BEAM MK1..5, GRAPPLE, SURVEY, BUILDER), "< Q" / "E >" caps as bound; follows a switch and The Beam's purchase; hidden aboard; its tags go through SideHud.Tag so MenuHudTests' layout check covers them. ShovelPlayTests.TheToolSlotShowsTheHeldTool. The shovel's own scoop sound (SfxSynth.Shovel, Sfx.Shovel; credits line).
- U-194's code (so the release lock only builds): the shelter walls on the drawn ground (BaseBuilder.FootOf: a piece on its column's natural top reaches down to the highest drawn ground under its footprint, view + collider; stacked pieces keep the grid; BaseTests.TheShelterWallsStandOnTheDrawnGround at smoke_18's spot, base within 0.1 m); the smoke adds smoke_64 crafting with thruster_mk2, smoke_65 / 66 the held shovel mid-swing and its flick, smoke_67 the tool slot with The Beam (79 shots, unity_smoke.ps1); GameInfo 0.6.1.
- The check: compile + EditMode (one lock), then PlayMode `ShovelPlay|RigModule|DigPlace|HintPlay|DigRunPlay|Fx|MenuHud|Base|AudioDirector` + LeadQA D1DigRun, then CaptureU193Shovel (u193/1..4).

## Last completed
- U-193 part 1 (a0f489e1, 11:36): DigTool, the shovel's strokes / reach / looks / arc / flick, The Beam at 250 Scrip, hints, B-221 / B-222 / B-226 imported; EditMode 491 (SkillTreeTests' stale 80-Scrip asserts fixed).
- 0.6.0's post-build sweep green (f6765a66); U-188 Build 0.6.0 DONE (40a0b641).

## Next up
U-193 → U-194 Build 0.6.1 (its release lock) → U-189 + U-191 (the giants), U-177, U-192, U-179.

## Ready for review
U-166 (b9d553de; smoke_42 with the next build). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
(none unrouted; B-227's four tool icons are carded)
## Blockers
(none: my turn comes after BLENDER's B-220 job)
## Proposals
(none open)
## For USER_ACTIONS
(none from me; LEAD decides on the ChatGPT app's memory)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat _MainTex fills, link.xml deletions, InitTestScene files): never staged; my commits list files explicitly. MERIDIAN_SETUP.md at the repo root is untracked and not mine.
## HeavyJobLock
none held (released 13:06); want_unity.lock filed 13:08 behind heavy_blender.lock (D-039), refreshed on each poll. No background waiters.
