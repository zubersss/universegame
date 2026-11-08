# UNITY STATUS
Updated: 2026-11-08 12:4x · Session: 10 (resumed 09:3x after the ~3-hour break; earlier entries: coordination/status/archive/UNITY_2026-11-08.md)
## Current task
12:4x, lock-free: U-166 + U-159 code (its check after BLENDER's B-185 Mars export), then U-162.
- U-166 (smoke_42's straight line): it is the liquid tilemap's water, not a datum overlay. Crop at x 960: at y 300 the frame goes from sky / trees (~188,191,178) to a blue-green multiply (~85,109,93) under a 2-3 px bright surface row, over the layers behind. PlanetBackdrop's UnderwaterTint can't show on the cartoon path (backdrop.ConfigureFor never runs there, its sea level stays unset); U-156 turned off only the solid tilemap renderer. The forest valley at 4506 (410) lies under Earth's sea level, so the generator fills it to the datum: a lake drawn as faint tiles (u156/3_valley's teal block is a pond). Sent to LEAD with two fixes (draw smooth-ground water as a body with an inked surface where it stands over the outline, or drain inland lakes); a PlayMode probe at 4506 confirms first.
- U-159 slice 1 checked (82cba57d + meta): SmoothGround's slots per planet (VariantKeys, AltFillKey, VariantFor), GroundRegionTests; EditMode 443/443. Next: slice 2 (Mars smooth: GroundField.Smooth, the backdrop sets by region, the storm veil's strip), slice 3 Mercury, slice 4 Venus (the station deck keeps its plank strip: on smooth ground a deck top would draw as earth fill).

## Last completed
0.5.0 respin + U-165, one lock 12:17-12:26 on B-188 (e2ddb4cb): call 1 BudgetGate + BootTracePlayTests with graphics 3/3 (BudgetGate's console clean; both first-launch boots: no sink, no rescue); call 2 BUILD OK Build/MERIDIAN_0.5.0 (release, 552 MB, 54 s), SMOKE OK 51 shots, 0 errors (scoop True at 108; forest valley fill layer 2). The dev build stays the probed run-2 build (no probe re-run, per LEAD).
U-165's cause (486e55a5): BudgetGate's "Earth streaming 200 m" row moved the side camera 200 m (streaming follows the camera); the camp's chunks unloaded under the surveyor, it fell, and the solid rescue lifted it 0.76 m when the camera returned. BudgetGate now holds the surveyor during the excursion (test staging only). Normal play: BootTracePlayTests holds it.
U-163 Build 0.5.0 (first spin 11:2x-12:0x, accepted by LEAD on its checks): probe green on run 2 (D-152: Return +9.9 % / +4.6 %, Creep +0.5 MB per visit, Climb p99 16.9 ms, Film pass 0.356 ms); compile 0 / 0, EditMode 442/442, U-164 2/2, the Earth slice 37/37 (Harvest: 0.4.8 digging 0.0; 0.5.0 nodes 7.4 / pockets up to 11.4 items a minute), LeadQA M1Loop + M3Inner 8/8.

## Next up
U-159 code (the region → band / set map on its card) → U-162 → U-152.

## Ready for review
Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (the survey scan pulse; UranusStageTests +1); U-144 (Neptune's -x zones, the drift, the anchor, the gust warning; NeptuneStageTests +3).
## Handoffs
(none unrouted)
## Blockers
(none)
## Proposals
(none open: P-51 / P-53 / P-54 / P-55 decided in D-159..D-167)
## For USER_ACTIONS
(none)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat _MainTex fills, TMP font asset, existing animator.controllers, UnderwaterTint.mat, link.xml.meta, two InitTestScene files): never staged; my commits list files explicitly. MERIDIAN_SETUP.md at the repo root is untracked and not mine.
## HeavyJobLock
none held, no want. No background waiters.
