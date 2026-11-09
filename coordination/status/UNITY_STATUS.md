# UNITY STATUS
Updated: 2026-11-09 17:5x · Session: 12 (restarted ~14:02 on Fable 5.2, context rebuilt from the repo; earlier entries: coordination/status/archive/UNITY_2026-11-09.md, UNITY_2026-11-08.md)
## Current task
17:5x: 0.6.2's work. B-232 + B-238 IMPORTED (748dde18); U-196's second set in (287203a2: the tiers' crossfade 0.35 m, the mound reframed, the T3 room's bar met, BudgetGate green); U-204 F12 and F18 in. Now, lock-free: U-204's layout rows (F2, F3, F10, F19, F20). One lock 17:40-17:51: compile 0 / 0, EditMode 499/499, PlayMode DigFeel / ShovelPlay / Fx / SmoothGroundPlay / RigModule / DigPlace / Harvest 25/25, CaptureU196Holes + CaptureU200Walls + CaptureU195DigFeel OK, BudgetGate GREEN on its first reading (Chunk generation p99 1.64 ms).
- U-196 as built (the back wall's own vertex colours and triangles: no texture sample, no draw call added): a quad a cell, each corner shaded DepthShade (full at the natural surface, 55 % from 6 m down) × AirShade (the way through air to the open sky beyond straight up: 1 down an open shaft, 80 % from 3 m of extra way and in a closed room); RimShadow, an ink gradient 0.5 → 0 over 0.3 m inside every dug edge (none in the open air). The open-air floor 0.8 and the rim's ink 0.5 RULED as built (LEAD 17:3x; looked at again with B-230's wall). The tiers' crossfade 0.35 m (LEAD 17:3x; the jsons keep transition_m 1.0). The full-screen T3 room with the tier shader: 4.59 then 4.86 ms avg (the bar 6.4). Still owed: B-230's wall behind the fill when its export lands.
- CaptureU182Perf saves no picture, so tools/unity_capture.ps1 prints CAPTURE FAILED and exits 1 for it though the test passes: read its figures from the capture xml's [MERIDIAN] u182 perf lines.
- D-190: clods lifted 35 % on T1-T3 and 60 % on T4-T5, the puff 60 %; DigFeel.PuffRedrawn = true (the dust at scale 1 and 0.85 alpha, the flick back, tinted as the clods). No code or test asks for the eight band-set puffs (SmoothGround.PuffKey takes the planet alone; GroundArtTests does not count the files): BLENDER told directly 17:54 to remove the 16 files; I drop their 16 metas and the generated dig_puff_* controller folders in my next commit after its removal. Known gap, D-190 (1): the tone is the tier's chip colour until the fills' jsons carry "tone_hex" (it comes with B-230's export).

## Last completed
- The import of df2defa3 (748dde18): fx/dig_clods/t1..t5, fx/rubble/base (for U-197), the redrawn dig_puff ×4 and shovel_flick; u195/1..5 re-shot on the real art. U-195 now waits only for 0.6.2's smoke_65 / 66 (ACCEPTED as built, LEAD 17:1x).
- U-204 F12 (287203a2): no Fire action in the ShipTop map, so no "Fire: LMB" in the key list (smoke_20). F18: the dig tool put away on the jetpack clip unless in use (smoke_55). F4 / F13 (d8282916). All to be seen in 0.6.2's smoke.
- U-200 ACCEPTED on both parts (LEAD 17:1x; in Review until 0.6.2's smoke_18 / 47).
- U-203 Build 0.6.1b DONE (the owner's build; 4588b3f0 + 2fce1044); U-194 Build 0.6.1 DONE (17e6d96d).

## Next up
U-204's layout rows (F2, F3, F10, F19, F20), then F6 / F17 (the smoke's staging), the three keys to name for BLENDER (F9, F11, F14) → U-202 (the probe script's warm-baseline rows, the ~18 MB) → B-230's import when LEAD says it has landed → 0.6.2's release (the full sweep, BudgetGate, the probe with D-189's rows, the smoke: reset the pack before the valley shot) → U-197 → U-198 → U-199; the giants (U-189 / U-191: B-220's continue_rows are arriving planet by planet), U-177, U-192, U-179 after.

## Ready for review
U-196's second set (287203a2; u196/1..4, u200/2 for the T1 / T2 border at 0.35 m). u195/1..5 on the real art (748dde18). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
→ BLENDER (direct, 17:54; LEAD told): the 16 variant puff files are free to remove; "tone_hex" on every ground_fill json expected with B-230.
## Blockers
(none)
## Proposals
(none open: P-58 ruled)
## For USER_ACTIONS
(none)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat _MainTex fills, regenerated animator.controller files, link.xml deletions, AddressableAssetSettings line endings, UnderwaterTint.mat): never staged; my commits list files explicitly. MERIDIAN_SETUP.md at the repo root is untracked and not mine. perf_2026-11-09.md: a BudgetGate run rewrites the whole file; the readings sections (0.6.2's, 0.6.1's, D-189's table, the 0.6.1 dev-player rows) must be restored under its rows after each run (they are in git at 748dde18: `git show HEAD:... | sed -n '89,$p' >>` the fresh file).
## HeavyJobLock
none held (released 17:51:45); no want. No background waiters.
