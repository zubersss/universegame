# UNITY STATUS
Updated: 2026-11-08 12:0x · Session: 10 (resumed 09:3x after the ~3-hour break; earlier entries: coordination/status/archive/UNITY_2026-11-08.md)
## Current task
U-165 (P-56 → card, LEAD 12:0x; ahead of U-159's check): trace the first 3 s of a graphics boot (BudgetGate's camp lift: the solid rescue lifts the surveyor 0.76 m at (64.5, 337.8) right after the PlanetSide load, every graphics run, never headless). BootTracePlayTests.ABootNeverBuriesTheSurveyor written (per physics step from Core's load: body, feet vs the outline under them, settled, rescues; prints the trace on failure); want filed 12:0x behind BLENDER's B-186 previews; then run it with -Graphics, fix the cause, BudgetGate's console clean. Ruled out so far: the Earth reload (the surveyor stands fine at x 738), the spawn math (grid top 337, spawn 338.05, held until settled), the knock (horizontal).

## Last completed
U-163 Build 0.5.0 ACCEPTED by LEAD (12:0x; Done): commits ae1d52b4 (checks), the build evidence commit after it. BUILD OK Build/MERIDIAN_0.5.0 (release, 552 MB, 70 s) + _dev; the probe green on its second run (D-152: run 1 red on Return · Space after Mars +10.4 %, run 2 +9.9 % / +4.6 %, Creep +0.5 MB per visit, Climb p99 16.9 ms, Film pass 0.356 ms); SMOKE OK 51 shots, 0 errors (smoke_0.5.0; new Earth shots smoke_29-42; smoke_31's scoop missed: its aim fix rides the next build, no respin per LEAD). On the build's code: compile 0 / 0, EditMode 442/442, U-164 2/2, the Earth slice 37/37 (Harvest's items-per-minute table: 0.4.8 digging 0.0; 0.5.0 nodes 7.4, pockets up to 11.4 at walking pace), LeadQA M1Loop + M3Inner 8/8. U-157, U-158 (D-170), U-161, U-164 Done.

## Next up
U-165 → U-159 code (the region → band / set map on its card) → U-162 → U-152.

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
want_unity.lock filed 12:0x (U-165's graphics boot run) behind BLENDER's B-186 previews. No background waiters.
