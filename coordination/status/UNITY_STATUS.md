# UNITY STATUS
Updated: 2026-11-09 16:0x · Session: 12 (restarted ~14:02 on Fable 5.2, context rebuilt from the repo; earlier entries: coordination/status/archive/UNITY_2026-11-09.md, UNITY_2026-11-08.md)
## Current task
16:0x: U-203 Build 0.6.1b (the first-minute fixes) READY FOR REVIEW: BUILD OK, SMOKE OK. Build/MERIDIAN_0.6.1b/MERIDIAN.exe (release, 519 MB, 15:55; Build/MERIDIAN_0.6.1 untouched); the smoke 15:55-16:02: 79 shots, exit 0, 0 error lines (coordination/reports/unity/smoke_0.6.1b/). No BudgetGate or probe (HUD and animation code only, LEAD's card). Next, lock-free: U-195's DigFeel code.
- Viewed in the final smoke: 65 / 66 the shovel in hand through the stroke, no pick; 47 the DIG DOWN card with B-229's shovel picture; 42 the top bar clean topside (no outline, no box).
- Seen and not touched, sent to LEAD: smoke_47's card covers the tool slot's name tag (a stub of the empty tag at the card's left edge); the surveyor half behind the rocket's fin and foot pad in 47 / 65 / 66 (the ordering default, on U-200's list); smoke_42's PACK 30 / 30 kg in red is the smoke's staging.

## Last completed
- U-203 (4588b3f0; check 15:44-15:50 one lock: compile 0 / 0, EditMode 493/493, PlayMode ShovelPlay / ShovelHollowPlay / MenuHud / Base / DigRunPlay / SurveyorAnimPlay 20/20, LeadQA D1DigRun 1/1; HintPlay 3/3 at 15:52 on B-229's picture):
  - The pick: since U-121 the drawn surveyor played side_b's dig clip after every dig; its frames 0-9 carry a baked pick (hand_socket held_b) and the held tool hides on them, so every shovel or Beam stroke ended in a pick swing (in 0.6.0 too). SpriteCharacterView no longer hooks the dig: the body keeps its stand / walk pose, the tool in the hand carries the stroke. ShovelPlayTests +1: 2 shovel strokes over 1675 frames, 2 Beam strokes over 591: tool off 0, baked-tool body frames 0.
  - U-201: SideHud.Awake switched off the depth tag's and chip's fills only; their eight ink-edge Images drew from every boot until the first dig below the Surface Line and back. ShowDepthTag(on) over a parts list cached in Awake. MenuHudTests +1 (fresh boot, board / exit, Tab open / close: 10 Images off; 4.5 m under the line: on with "DEPTH 4 m"; back up: off).
  - GameInfo 0.6.1b (a plain string everywhere it is read).
- U-194 Build 0.6.1 DONE (LEAD 15:4x; out to the owner): the sweep after the restart (11a86b34), the wall fix (114ffba1), the build's reports (17e6d96d); the probe's Return · Space row re-based on the warm Space leg (D-189; the readings and the table in perf_2026-11-09.md).

## Next up
U-195 (dig feel; B-232's clods: 24 frames at 64 px, four 6-frame clips clod_1..4, one clod per sprite, the arc in code) → U-196 → U-197 → U-198 → U-199; 0.6.2's small cards with U-195's check: U-200 (FootOf on the lowest drawn surface under the piece's width; the surveyor's order against the rocket's fin), U-202 (the probe script's warm-baseline rows, the ~18 MB named); the giants (U-189 / U-191), U-177, U-192, U-179 after.

## Ready for review
U-203 (4588b3f0 + this commit's reports; smoke_0.6.1b/ 79 shots). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
(none unrouted)
## Blockers
(none)
## Proposals
(none open)
## For USER_ACTIONS
(none)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat _MainTex fills, animator.controller files, link.xml deletions, AddressableAssetSettings line endings, UnderwaterTint.mat): never staged; my commits list files explicitly. MERIDIAN_SETUP.md at the repo root is untracked and not mine. ProjectSettings.asset's bundleVersion (0.6.0 → 0.6.1b, written by the builds) goes in with this commit.
## HeavyJobLock
none held (the 0.6.1b smoke's lock released 16:02:08, LEAD told at once); no want. No background waiters.
