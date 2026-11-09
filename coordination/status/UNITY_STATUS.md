# UNITY STATUS
Updated: 2026-11-09 17:3x · Session: 12 (restarted ~14:02 on Fable 5.2, context rebuilt from the repo; earlier entries: coordination/status/archive/UNITY_2026-11-09.md, UNITY_2026-11-08.md)
## Current task
17:3x: 0.6.2's work, U-196 (holes read as holes). Its darkening and rim shadow are in with a first capture set (05b10762; u196/1..4), waiting for LEAD's look. Still owed by U-196: the mound shot reframed (u196/4 cuts the pit off), CaptureU182Perf (the full-screen T3 room ≤ 6.4 ms) and BudgetGate, and B-230's detail layer behind the fill when its export lands (the wall draws the fill shaded until then). One lock 17:23-17:30: compile 0 / 0, EditMode 499/499, PlayMode DigFeel / ShovelPlay / Fx / SmoothGroundPlay / DigPlace / DigRunPlay / Harvest 21/21, CaptureU196Holes + CaptureU195DigFeel OK.
- U-196 as built (the back wall's own vertex colours and triangles: no texture sample, no draw call added): a quad a cell, each corner shaded DepthShade (full at the natural surface, 55 % from 6 m down) × AirShade (the way through air to the open sky beyond straight up: 1 down an open shaft, 80 % from 3 m of extra way and in a closed room); RimShadow, an ink gradient 0.5 → 0 over 0.3 m inside every dug edge (none in the open air). My two numbers for LEAD's ruling: the open-air floor 0.8, the rim's ink 0.5. F7 (a tier border under a slope: the wobble kept by the line's slope) ACCEPTED 16:4x.
- D-190 in (05b10762): clods lifted 35 % on T1-T3 and 60 % on T4-T5, the puff 60 %; the one dust puff (no code asks for the eight band-set puff keys: BLENDER can remove them, told LEAD); a mound's puff tinted. DigFeel.PuffRedrawn = false until B-238's dust is imported (then scale 1, 0.85 alpha, and the shovel's flick back, tinted): set it in B-238's import commit. Known gap, D-190 (1): the tone is the tier's chip colour, not the fill drawn at the cell (snow and sand puff Topsoil-brown).

## Last completed
- U-195 ACCEPTED AS BUILT (LEAD 17:1x; in Review until B-232's sheet and B-238's dust are imported and seen in 0.6.2's smoke_65 / 66): d8282916, 443868e0, 117118bd, 60696ed5; the icon-flight staging compiled and green (05b10762). P-58 (clods per stroke) ruled as built; 3-4.5 m/s ruled.
- U-200 ACCEPTED on both parts (LEAD 17:1x; in Review until 0.6.2's smoke_18 / 47): the wall's drawing down to the lowest ground under its corners (u200/1), the surveyor, tool, cable and grapple line at 18-19 in front of the rocket (u200/3..5); the surveyor in front of all ground flora is RULED: keep.
- U-204 F4 / F13 (d8282916; tests green, not yet seen in a smoke): hint cards at -196, clear of the tool slot's name plate; a hint and its arrow step aside under a planet's title card.
- U-203 Build 0.6.1b DONE (the owner's build; 4588b3f0 + 2fce1044); U-194 Build 0.6.1 DONE (17e6d96d).

## Next up
U-196's remaining captures and perf → U-204's other rows (F1b is B-238's; F2, F3, F10, F19, F20, F12, F18, F17, F6; the three keys to name for BLENDER) → U-202 (the probe script's warm-baseline rows, the ~18 MB) → the imports of B-230 / B-232 / B-238 when LEAD says they have landed → 0.6.2's release (the full sweep, BudgetGate, the probe with D-189's rows, the smoke: reset the pack before the valley shot) → U-197 → U-198 → U-199; the giants (U-189 / U-191: B-220's continue_rows are arriving planet by planet), U-177, U-192, U-179 after.

## Ready for review
U-196's first set (05b10762; u196/1..4, u200/2 for the T1 / T2 border). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
→ LEAD (for BLENDER): a per-fill tone field in the fills' json would close D-190 (1); the eight variant puff keys are free to remove.
## Blockers
(none)
## Proposals
(none open: P-58 ruled)
## For USER_ACTIONS
(none)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat _MainTex fills, animator.controller files, link.xml deletions, AddressableAssetSettings line endings, UnderwaterTint.mat): never staged; my commits list files explicitly. MERIDIAN_SETUP.md at the repo root is untracked and not mine. perf_2026-11-09.md: a BudgetGate run rewrites the whole file; the readings sections (0.6.2's, 0.6.1's, D-189's table, the 0.6.1 dev-player rows) must be restored under its rows after each run (they are in git at 117118bd).
## HeavyJobLock
none held (released 17:30:18; BLENDER's want was on file); no want. No background waiters.
