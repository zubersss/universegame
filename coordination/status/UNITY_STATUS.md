# UNITY STATUS
Updated: 2026-11-08 21:4x · Session: 10 (resumed 09:3x; earlier entries: coordination/status/archive/UNITY_2026-11-08.md)
## Current task
21:4x: U-182 for review → next U-186 (brink lips, surface decor, the dig puff by band; before the D1 build), then U-178, U-183, U-176, U-177.

## Last completed
- U-182 for review (the fill by depth tier): Shaders/GroundTiers (2D lit; the Surface Line per column in an R16 texture, 2 mm from DigRun.LineAt; ground_fill + t2..t5 smoothstepped over 1 m at D1_TABLES depths; at most two samples a pixel), GroundTiersSetup (material in the registry), SmoothGround (tier materials for the fill and the desert sand; the fill_decor scatter by tier, U-167 folded in: 4 m cells, 22 %, off tier borders, wholly under the surface, gone with a dug tile; its rebuild spread 3 chunks a frame); GroundTierTests x2; u182/1..5 Earth T1..T5, 6 the T1/T2 border on a 0.6 slope, 7 Mars T4 (Mercury / Venus wait for U-177 smooth ground). BudgetGate green twice (rows within run noise); an A/B probe (CaptureU182Perf) shows +1.5 ms render in a full-screen T3 room on this iGPU (7.5 → 9 ms): proposal to LEAD, the back wall only behind dug cells (halves the fill overdraw).
- U-184 for review (D-178, the space minimap + the system map on M): Space/SpaceMap + MapLines on B-209 ui/map; marks at true positions (minimap; system map = whole system + inner-planets inset, each linear), rim arrows (nearest 3 tagged with distance; lined-up bodies share the nearer arrow), zoom by the 2nd-nearest planet + 5 s of speed, landed ticks (landed:<planet> flag on entry; Earth, beacons), hidden during transitions and menus; M toggles, Esc closes (MenuController asks first); built at boot behind the cover. SpaceMapTests x5, MapLinesTests x2; BudgetGate green (Space avg 3.70 ms, p99 8.04 ms, first frame 8.2 ms, GC 0 B); u184/1_minimap, 2_minimap_far, 3_system_map. Also: CreatureDirector skips a body destroyed before its sheet arrived (a MissingReference race).
- U-175 review fixes (LEAD 19:4x): the header (Skill Tree in Limelight, Scrip, Surveyor Rank from D1_TABLES §7 now in D1Tables.rankScrip), the node card on the kit inventory paper (frame + icon, name, branch / ring, effect, needs:, the cost tag owned / needed, BUY greyed with the reason), BLENDER crossing-free slots and angles in SkillTree.json (+ node names) with sideways links as arcs (SkillTreeTests.TheChartHasNoCrossingLinks: 0 crossings, no link over a node); u175/1_skill_tree.png + 2_skill_tree_ready.png. U-183 step 1: the Grapple slot off props/rig/lance (5a528c84); B-205 imported (31ddf15e).
- U-175 for review (the Skill Tree): Settings/Resources/D1/SkillTree.json (66 nodes from D1_TABLES §5; links any-one-of with the sideways; costs Scrip / items / Datacores; typed mods add / mul / set / min / flag); Progress/SkillTree (buy rules, topside), SkillStats (LEAD 19:0x stacking: + adds, best × never compounded, sets the best, then the expedition factor D-175 on the multiplied stats); wired: Beam power, brush radius, pack kg, dirt store, load k, jet thrust / power use, scan radius, fall damage / safe fall, Waystation bonus, thruster mark, suit tier (grapple / reel / climb / oxygen / hold exposed for U-176 / later cards); save v4 (skillNodes, expedition; a v3 file maps its earned blueprints, the fitted thruster and the Mk3 suit to nodes); SkillTreePanel (K, B-204 art); SkillTreeTests ×5; u175/1_skill_tree.png.
- U-174 for review (the dig run, data-driven): the Surface Line, tiers and stroke time, dirt store and drops, the pack's weight and load, the Sell panel; DigRunTests +5, DigRunPlayTests +2, u174/ captures. Open: each tier's own fill (shader proposal sent), the giants' kg.
- U-173 Build 0.5.1 (603fe1c3). U-172, U-169, U-170, U-168 DONE; the sweep; D-176 / D-177.

## Next up
U-184 (minimap) → U-182 → U-178 (prestige; B-206 rank art in) → U-183 (tool looks; the Grapple slot off the v2 lance once B-205 lands) → U-176 → U-177. Beside: U-179, U-180, U-181. Parked: U-167, U-171, U-162. A full sweep before the D1 build.

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
