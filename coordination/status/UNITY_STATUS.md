# UNITY STATUS
Updated: 2026-11-09 15:2x · Session: 12 (restarted ~14:02 on Fable 5.2, context rebuilt from the repo; earlier entries: coordination/status/archive/UNITY_2026-11-09.md, UNITY_2026-11-08.md)
## Current task
15:3x: U-194 Build 0.6.1 READY FOR REVIEW: BUILD OK, SMOKE OK, the probe green on D-189's warm baseline. Build/MERIDIAN_0.6.1/MERIDIAN.exe (release, 519 MB, built 15:24-15:27 from 114ffba1), Build/MERIDIAN_0.6.1_dev (the probed development player, 586 MB, 15:12); the smoke 15:27-15:33: 79 shots, exit 0, 0 error lines (coordination/reports/unity/smoke_0.6.1/). Next: U-195 (dig feel).
- The probe: Return · Space after Mars read +10.4 % and +11.3 % against the first Space leg in the respin's lock (red on two readings, D-152; earlier today +12.8 % and an outlier -4.6 %; 0.6.0 +10.1 / +8.9 %), so the respin stopped before its release build and went to LEAD. Leg by leg every attributed counter in the Space legs equals 0.6.0's; the ~110 MB is the one-time warm-up after the first Space leg. RULED D-189: the row is judged against the warm Space leg (Space after Earth), the first Space → warm delta its own row (≤ 150 MB): +1.5 / -12.5 / +0.9 / +1.6 % and 123 / 102 / 106 / 106 MB on today's four 0.6.1 probe files, all green; the release built without a third probe. Every other row green in all four readings (Creep 3.5 / -1.5 / -5 / 9 MB, Earth again +1.1..+5.1 %, climb p99 16.7 ms); Film pass 0.337 / -0.171 / 0.469 / 0.631 ms (a watch row, D-180). All in perf_2026-11-09.md.
- Viewed by me: the first smoke's smoke_1 (B-221's title), 64 (Thruster Mk2), 65 (SHOVEL in the slot, mid-scoop), 67 (BEAM MK1, B-227's icon): right; the final smoke's smoke_18: both wall columns unbroken from the roof to the slope, no slit (each bottom wall meets the slope at its uphill corner, a small wedge of sky under the downhill one: U-200, 0.6.2). LEAD viewed the whole first smoke; only the wall footprint changed between the two.

## Last completed
- The sweep after the restart (11a86b34; one lock per slice 14:05-14:29): the restart cut slice C off (stale lock removed 14:05); C 33/34, D 28/28, E 33/33 (+ ShovelPlay / ShovelHollowPlay), F 22/24 (1 skipped). C's red is the AI worst-frame row (InnerCreatureTests 1.42 ms in the slice, 0.135 ms alone; CreatureTests 1.000 ms alone): passes for 0.6.1 under D-188. F's red fixed in the test's staging and ACCEPTED: TerrainStreamingTests holds the surveyor still for its 200 m camera flight (the camp's chunks unloaded under it and the solid rescue logged a 0.76 m lift; U-165's BudgetGate case).
- LeadQA 14:30-14:40: M1Loop 1/1, D1DigRun 1/1, M3Inner 7/7 on LEAD's 0b095662 (Step3 digs with the Beam: a new surveyor's shovel reaches 2 m).
- BudgetGate: reading 1 14:35 RED (Earth p99 18.75 ms, chunk gen p99 3.06 ms; the machine busy), reading 2 14:40 GREEN (Earth avg 5.71 / p99 12.31 ms, chunk gen p99 1.30 ms, Earth C0 5.22 / 8.22 ms, 153 draws): accepted under D-159.
- The first release chain 14:42-15:01: dev build OK, probe +12.8 % then -4.6 %, release build OK, smoke 79 shots / exit 0 / 0 error lines. Viewed: smoke_1, 64, 65, 67 right; smoke_18 a see-through slit between each bottom wall and the wall above.
- The wall fix (114ffba1; one lock 15:04-15:08): BaseBuilder.Spawn hands the sheet a footprint that includes the foot (SheetProp's own fit had replaced the stretched scale with the cell's size); BaseTests.TheShelterWallsStandOnTheDrawnGround now waits for the sheets and asserts each bottom wall's drawn top at its cells' top (+0.00 m both, feet 0.34 / 0.26). Compile 0 / 0, EditMode 493/493, PlayMode Base / ConkOut / U076Scene / DigPlace 9/9.
- The respin 15:09-15:33: dev build OK; the probe red twice on the old row (above), no release build from that lock; after D-189 the release build (15:24, its own lock) and the smoke (15:27, its own lock).

## Next up
U-195 (dig feel; B-232's clods are 24 frames at 64 px, four 6-frame clips clod_1..4, one clod per sprite, the arc in code) → U-196 → U-197 → U-198 → U-199; 0.6.2's small cards U-200 (FootOf on the lowest drawn surface under the piece's width) and U-201 (smoke_42's empty depth tag topside: runtime or staging); the giants (U-189 / U-191), U-177, U-192, U-179 after.

## Ready for review
U-194 (11a86b34 the sweep, 114ffba1 the wall fix, this commit the build's reports; smoke_0.6.1/ 79 shots). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
(none unrouted)
## Blockers
(none: LEAD ruled the row at 15:2x, D-189: judged against the warm Space leg; by hand from today's six probe files +0.2..+1.6 % and a 98-123 MB warm-up delta, all green, in perf_2026-11-09.md; U-202 moves it into the probe script and names the ~18 MB)
## Proposals
(none open)
## For USER_ACTIONS
(none)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat _MainTex fills, animator.controller files, link.xml deletions, AddressableAssetSettings line endings, UnderwaterTint.mat): never staged; my commits list files explicitly. MERIDIAN_SETUP.md at the repo root is untracked and not mine.
## HeavyJobLock
none held (the smoke's lock released 15:33:51, LEAD told at once for BLENDER's turn); no want. No background waiters.
