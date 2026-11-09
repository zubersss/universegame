# UNITY STATUS
Updated: 2026-11-08 18:4x · Session: 10 (resumed 09:3x; earlier entries: coordination/status/archive/UNITY_2026-11-08.md)
## Current task
18:4x: U-175 (the Skill Tree: D1_TABLES §5 as data, 66 nodes, the panel on B-204's ui/skilltree art, every effect a stat modifier taking D-175's expedition multiplier; replaces the Blueprint Tree's unlocks).

## Last completed
- U-174 for review (the dig run, data-driven): the Surface Line, tiers and stroke time, dirt store and drops, the pack's weight and load, the Sell panel; DigRunTests +5, DigRunPlayTests +2, u174/ captures. Open: each tier's own fill (shader proposal sent), the giants' kg.
- U-173 Build 0.5.1 (603fe1c3). U-172, U-169, U-170, U-168 DONE; the sweep; D-176 / D-177.

## Next up
U-175 → U-178 (prestige) → U-176 (ways back up) → U-177 (the planet ladder). Beside: U-179 (boot loads), U-180 (POI pads / the Archive's chamber), U-181 (paper grain). Parked: U-167, U-171, U-162, U-174b (tier fills, on LEAD's ruling). The next check: WaystationPlay's restage, PawsOnTheGround.

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
