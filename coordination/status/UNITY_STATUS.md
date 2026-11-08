# UNITY STATUS
Updated: 2026-11-08 18:0x · Session: 10 (resumed 09:3x; earlier entries: coordination/status/archive/UNITY_2026-11-08.md)
## Current task
18:0x: U-174 (D-174, Bible 5.2 §8.1, docs/D1_TABLES.md as data): the Surface Line, depth tiers and stroke time, pack weight, selling topside. Then U-179 (the first-2-s boot loads behind the title card) beside it.

## Last completed
- U-173 Build 0.5.1 (603fe1c3): BUILD OK release 515 MB, SMOKE OK 58 / 0, BUILD MEMORY GREEN, BudgetGate green with D-177 (Boot settle row). Import 3c9966bd (e72a24ff, B-207).
- U-172 DONE (6a30e7e3), the sweep (d77227b1), D-176 ShipMarks. U-169 / U-170 / U-168 DONE; U-159 slice 2 ACCEPTED.

## Next up
U-174 → U-175 (the Skill Tree; modifiers take a global expedition multiplier) → U-178 (prestige, D-175) → U-176 (ways back up) → U-177 (the planet ladder, Mercury / Venus smooth). U-179 beside U-174. Parked: U-167, U-171 (after B-202), U-162. PawsOnTheGround re-run with the next check (B-207 in).

## Ready for review
U-166 (b9d553de; smoke_42 with the next build). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (the survey scan pulse; UranusStageTests +1); U-144 (Neptune's -x zones, the drift, the anchor, the gust warning; NeptuneStageTests +3).
## Handoffs
(none unrouted)
## Blockers
(none)
## Proposals
(none open; P-57 ruled as D-172)
## Found (reported to LEAD 15:1x)
HazardV2PlayTests x3 + SurveyorAnimPlayTests red since U-156, NOT from today's changes (an experiment with today's PoiStamp change off fails the same): 30 m west of Earth's camp (x 37) the drawn curve stands 1.66 m above the tile top (332.66 vs 331.0); HazardV2's TopSolidY teleport is rescued, SurveyorAnim lands while running left. Either a curve/grid mismatch on the camp's west shoulder or stale teleports.
## For USER_ACTIONS
(none)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat _MainTex fills, TMP font asset, existing animator.controllers, UnderwaterTint.mat, link.xml.meta, two InitTestScene files): never staged; my commits list files explicitly. MERIDIAN_SETUP.md at the repo root is untracked and not mine.
## HeavyJobLock
none held, no want. No background waiters.
