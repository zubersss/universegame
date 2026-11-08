# UNITY STATUS
Updated: 2026-11-08 17:2x · Session: 10 (resumed 09:3x; earlier entries: coordination/status/archive/UNITY_2026-11-08.md)
## Current task
17:2x: U-173 Build 0.5.1 (the walk fix, Mars smooth, today's fixes). Version 0.5.1; smoke list 58 shots (+ the Survey Archive, the Launch Complex, a 4-frame downhill walk strip; smoke_12 shows B-196's Warden lantern). Part 1 (profile + dev build + probe) RED at 17:15: Earth frame time p99 22.6 ms / max 68 ms, chunk generation p99 2.06 ms, Return Space after Mars +11.7 % (D-152: run 2 decides), film pass 2.4 ms. Fixing the frame-time and chunk-generation causes (today's continuation readback and U-169's per-node fill top), then part 1 again, then part 2 (release + smoke).

## Last completed
- U-172 DONE (6a30e7e3): the outline's quarter-metre vertices kicked the walking capsule up; grounded feet never rise on flat ground + a 0.3 m ground snap; WalkDownhillPlayTests.
- The full PlayMode sweep (d77227b1): every class in 6 batches; fixes and stagings; D-176 (ShipMarks after the spool, green).
- U-169 DONE (07590dff): the grid fills to the drawn curve; CurveOverTilesTests. U-170 DONE (3fdad7f7): cryo_round retired.
- U-168 DONE (5fa45505). U-159 slice 2 (Mars) ACCEPTED: 6c11e281, 57d46b68, 8f96070f (the skylight funnel).
- Imports: e68fa896, 49775f73, 1f2924b7, f615b0d8 (tracked metas only from now on, D-016).

## Next up
U-173 Build 0.5.1 → D1: U-174 (the Surface Line, depth tiers, stroke time, pack weight, selling topside; data from docs/D1_TABLES.md, never constants) → U-175 (the Skill Tree, modifiers that take a global expedition multiplier) → U-178 (prestige, D-175) → U-176 (ways back up) → U-177 (the planet ladder, Mercury / Venus smooth). Parked: U-167 (fill_decor scatter), U-171 (the sea under-set, after B-202), U-162.

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
