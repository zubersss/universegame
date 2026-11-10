# UNITY STATUS
Updated: 2026-11-09 22:5x · Session: 12 (restarted ~14:02 on Fable 5.2, context rebuilt from the repo; earlier entries: coordination/status/archive/UNITY_2026-11-09.md, UNITY_2026-11-08.md)
## Current task
RESUME POINT (for a restarted window): BUILD 0.6.2 IS OUT to the owner (LEAD's page, USER-41; Build/MERIDIAN_0.6.2/, smoke in coordination/reports/unity/smoke_0.6.2/). The next build's work, in LEAD's order: U-206 (in Review) → U-205 (nearly done, below) → U-207 (NEXT: the backdrop's BC7 cost and the machine's two levels) → U-192 → U-197. No heavy job without a 1.5 GB free-RAM reading in its own call and an empty locks folder.

U-205 at 22:5x (commits 2d4ceeb5, 0405d4e1, 3b125219; every check green):
- (1) THE WALL'S COST, DONE AND RULED (D-192 amended): the back wall's extra ~2 ms was its paper grain IN BC7 ONLY. The same grained tile read 1.64 ÷ lit in BC7 and 1.43 in RGBA32 / DXT5 / DXT1 (the fill alone 1.38-1.41). The walls keep their grain and import as uncompressed RGBA32 (ArtKeys.IsBackWall, ArtImporter, CheckSetup's ReimportBackWalls; the twenty .meta files; BudgetGate's Textures row names the exception, accepted by LEAD). Re-read with the real walls: a walled T3 room 9.88 ms against the fill alone's 9.86, ratio 1.46, inside the bar of 1.52. +0.98 MB resident while a planet's five walls are loaded (by the formats' sizes; the player's row comes with the next dev build's probe). Tables: perf_2026-11-09.md, "Readings after 0.6.2".
- (2) B-225's SEA, DONE: sea_under's five layers wired from the json (layer3 2 m tall at the water line; layer4 the shallow seabed between layer2 and layer3, whole to 32 m from the shore, gone at 40: SceneLayout.DrawOrder, ParallaxLayers.SetLayerAlpha, CartoonStage.ShoreDistance / ShallowsWeight); SeaUnderPlayTests 4/4; captures u205/1_sea_1m, 2_sea_3m, 3_sea_10m, 4_sea_out. ASKED OF LEAD: at 10 m under, the shallow seabed's continued sand fills the frame behind the surveyor (a fade as the camera sinks under its ground line would be a few lines).
- (3) BLENDER's read of 0.6.2: G3 FIXED (the sky scan over a chunk stopped 12 cells up, so a deep chunk shaded an open shaft as shut: LitScan 512, and a dig that opens a column re-shades the chunks under it; DigFeelTests.ADeepOpenShaftsWallIsLitAllTheWayDown). G4 FIXED (GroundTiers' _RowShift: each 4 m wall row read 0.37 of a tile further along). G7 FIXED in the smoke's staging (the camp dig opens from the surface). G10 EXPLAINED and staged out (a dug piece's icon landing in the PACK readout). G11 FIXED at spawn (CreatureDirector.SpawnPack: a body and a half between a new creature and its kind, pack-mates 1.3 bodies apart; CreatureTests.TheSpawnerKeepsItsKindApart). G2 IS NOT A FAULT OF THE WALL: the V is the tier border's own wobble (U-182) with the wobble kept whole on level ground, a 0.9 m trough that sits in the smoke's shaft (numbers in 3b125219's message; captures u205/5_shaft_upper, 6_shaft_lower, 7_shaft_whole): LEAD rules whether the wobble changes. OPEN: G12 (soft dark shapes low in smoke_36 / 37 / 41 / 43: perhaps the same wobble), G5 (two soft Mars ground pieces in smoke_18), two of a kind walking onto one spot (not asked yet).

U-207 (LEAD's card, next): the surface view with the backdrop set's layers in BC7 / DXT5 / RGBA32, interleaved, no art or import rule changed; the resident memory each format would cost; a warm-up of at least 15 s and a level marker (the lit fill before and after each block) so every row names its level; one block read straight after a pause and one after the warm-up; which of BudgetGate's and the probe's frame rows are short enough to be bursts. Do NOT change any row's method before LEAD's ruling. Why: in the 22:36 capture the level flipped twice inside one process (the same room read lit 3.86 ms after a pause and 6.3-7.2 a few seconds of sustained rendering later): a sign that tonight's "slow machine" is the sustained level and the afternoon's fast figures were bursts. The laptop: on mains, 99 %, Balanced plan (19:1x and 22:49).

U-192 after it: the Pilgrim's rig on the bay's "ship_ground" (layer1.json); the catalogue's Site branch with B-233's ten icons (23524e72, verified; their .meta files, icons.asset and icons.spriteatlasv2 are IMPORTED IN THE TREE BUT NOT COMMITTED: they go with U-192) and the Camp entry's icon; the veil serpent at 1x of its v3 sheet (3.5 m, G6 ruled) with its gentle-drifter temper.

## Last completed
- U-206 (3f3ed7f8, 06edd642): the pale box on every non-Earth planet was the camp's gull, spawned on every planet's stage; CartoonStage.CampGullOn; TransitionTests.NoCreatureOfAnotherPlanetIsAliveOnArrival (direct load and the real route, both ways). In Review until the next build's smoke_21 Mars.
- BUILD 0.6.2 (b49a6305): sweep, gate, dev build, probe twice with 0.6.1's control in the same lock, release build, smoke 79 shots / 0 errors. U-195, U-196, U-200, U-204 are DONE on its smoke (LEAD).
- In git, parse-checked, not yet run (first at 0.6.3): tools/unity_profile.ps1 `-Control <version>` (the last build's dev player probed after this build's in the same lock; D-191 amended).

## Next up
U-207 → U-192 → U-197 → U-198 → U-199; U-177 (Mercury / Venus smooth ground: their ten walls wait for it), U-189 / U-191, U-179. In the gaps: name the AI's first-time frame (~86 frames after the spawn, Earth only) and warm it at load if it can be; make the gate's C0 draw-call row repeatable (a fixed creature set); U-202 part 2's four readings a build; one line for LEAD on the closest pixels-per-texel a giant reaches before the entry ring (B-237 / B-239).

## Ready for review
U-206; U-205 (1), (2) and (3)'s G3 / G4 / G7 / G10 / G11 (u205/1..7). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
(none open)
## Blockers
(none.) Free RAM sits at 1.3-2.3 GB with nothing of ours running; each heavy job waits for a 1.5 reading.
## Proposals
U-207 is my proposal, carded by LEAD.
## For USER_ACTIONS
USER-40 (LEAD): quit the Ollama app and the Xbox app for the build sessions. LEAD may ask the owner to try Windows' "Best performance" power mode once U-207 says the sustained limit is real.
## Housekeeping
Editor churn in the tree (Generated/Models *.mat, regenerated animator.controller files, link.xml deletions, UnderwaterTint.mat): never staged; commits list files explicitly. perf_2026-11-09.md: a BudgetGate run rewrites the whole file and a probe run replaces its last section ("Memory in the development player"): restore the readings sections from git under the gate's rows after a gate run, and save the last build's player rows before a probe. The perf capture's helper scripts are in the session's scratchpad (u205_perf.ps1, u205_both.ps1, u205_walls.ps1, u205_cap.ps1): each is one lock around tools/unity_check.ps1 and tools/unity_capture.ps1 -Name u182perf -Test CaptureU182Perf -NoPicture.
## HeavyJobLock
none held (U-205's capture lock released 22:55); no want. No background waiters.
