# UNITY STATUS
Updated: 2026-11-10 00:0x · Session: 12 (restarted 11-09 ~14:02 on Fable 5.2; earlier entries: coordination/status/archive/UNITY_2026-11-09.md, UNITY_2026-11-08.md)
## Current task
RESUME POINT (for a restarted window; LEAD posted USER-42: restart the three windows and the laptop). BUILD 0.6.2 IS OUT (USER-41). THE RAM GATE HAS BEEN SHUT SINCE 11-09 23:58 (0.9-1.2 GB free with nothing of ours running: the three sessions hold about 1 GB private each): files only until a 1.5 GB reading with an empty locks folder. Poll every few minutes, not every minute.

LEAD'S ORDER AFTER THE RESTART (11-10 00:0x), each step its own lock after a RAM reading in its own call:
1. D-194 (a): `scratchpad/u207_d3d11.ps1` if the scratchpad survives, else by hand in one lock: `tools/unity_capture.ps1 -Name u182perf -Test CaptureU182Perf -NoPicture` then `tools/unity_capture.ps1 -Name u207 -Test CaptureU207Backdrop` (the tool now forces Direct3D 11 on every capture; ~8.5 min for both). Report to LEAD: the rooms (lit, the fill alone, the walls as imported RGBA32, the BC7 control tiles: with grain, without, flat; the grained tile as RGBA32 / DXT5 / DXT1) and the surface (the backdrop as BC7, DXT5, RGBA32, the marker), the machine note beside each; say what the walled room's ratio is on Direct3D 11, and whether tonight's slow level and the two-level behaviour show on Direct3D 11 too.
2. LEAD then rules the walls' format (D-192's amendment is SUSPENDED): if BC7 walls read within 0.05 of RGBA32 on Direct3D 11 the walls go BACK to BC7 (ArtImporter's rule for ArtKeys.IsBackWall, CheckSetup.ReimportBackWalls, BudgetGate's Textures row, ArtImporterTests.ABackWallImportsUncompressedAndAFillStaysBc7, the twenty back_wall_t*_color.png.meta files: 0405d4e1's import part reverted).
3. The pin's check: `tools/unity_check.ps1 -ExecuteMethod Meridian.EditorTools.CheckSetup.Run -Graphics -SkipPlayMode` (CheckSetup.PinDirect3D11 writes ProjectSettings.asset: commit it). BuildFolderTests.ThePlayerAndTheEditorDrawOnDirect3D11 FAILS until this has run.
4. One check for what is written and NOT YET COMPILED (78396568 D-194's tooling; 9e3bc26e U-192's Site icons and the veil serpent; fc209fbe the docked Pilgrim): compile (expect a slip or two: none of it has met the compiler); EditMode (CatalogueTests.EverySiteHasItsIconByItsLabel, PilgrimRigTests.TheBindPoseStandsOnTheBaysShipGround, BuildFolderTests); PlayMode `SeaUnderPlayTests|InnerCreatureTests|CreatureTests|WaystationPlayTests`; then `tools/unity_capture.ps1 -Name u205 -Test CaptureU205` for the two re-shots LEAD judges B-225 on (u205/3b with the layer gone at its ground line; 2_sea_3m untouched). Then commit B-233's import with U-192: the twenty icons/catalogue/*.meta files, AssetGroups/icons.asset, Settings/Atlases/icons.spriteatlasv2 (in the tree, uncommitted).
5. U-192's captures for LEAD: the bay with the docked ship (smoke_10's frame) and the catalogue page with the Site icons (CaptureU204Panels has the panels' staging). All of U-192's code is written: Catalogue.SiteIconKey + CataloguePanel; the serpent at 1x as Temper.Drifts (CreatureDirector.PartedAround); RigBuild.BindPose + DockingBay's BayShip on ShipGroundPx (660, 186).
6. BLENDER's B-242 (068a2918, two new back walls: terrain/earth/back_wall_sand behind a dug cell whose fill is ground_fill_sand, terrain/mars/back_wall_basalt for ground_fill_basalt; 256 px, 4 m, json "variant" / "fill", no tier): LEAD SAID YES (11-10 00:1x): import it (the two png .meta and json .meta files only) and wire it, a wall by the fill's name where one exists, IN STEP 4's CHECK, after LEAD's ruling on the walls' format (step 2). SmoothGround draws the band's shaded fill there today (SubBackSand, the sandBack colour); the new key is terrain/<planet>/back_wall_<the alt fill's name without "ground_fill_"> (AltFillKey gives the fill).
7. U-197 → U-198 → U-199; U-177, U-189 / U-191, U-179.

WHAT 11-09's LAST HOURS FOUND, in one place (perf_2026-11-09.md, top of "Readings after 0.6.2"):
- U-207's first reading (cc2cf200) said the painted backdrop costs 9-14 ms a frame in BC7 and 1.4-2.5 ms as DXT5 / RGBA32. THE TRIAL IN THE BUILT PLAYER (6a5d9135) SAID NO: the same dev binary probed as built and with `-meridianBackdropTrial rgba32` read GPU frame 11.07 / 11.25 ms against 12.87 / 13.20, climb p99 17.3 both, memory +59 to +174 MB uncompressed. CAUSE: the Editor runs on Direct3D 12 and the built player on Direct3D 11 (all 56 saved player logs: 11.0; every Editor capture log of 11-09: 12); the grainy-BC7 penalty is the driver's Direct3D 12 path.
- D-194 (LEAD): Editor perf captures run on the player's API; the Windows player's API pinned to Direct3D 11; every Editor frame figure and ratio of 11-09 is void as evidence about the game (the rules D-191 / D-192 stand and are re-read on Direct3D 11); no texture format changes on an Editor reading alone. The second probe lock and the per-planet DXT5 look capture (CaptureU207Sets, in git, never run) are DROPPED. The build folders are back: Build/MERIDIAN_0.6.2_dev is the released dev player (11-09 20:57), the trial build is Build/MERIDIAN_0.6.2_dev_u207trial.
- The trial flag stays in the code, development builds only, off unless given (GroundTierTests holds it).
- U-205 (2d4ceeb5, 0405d4e1, 3b125219, 7e679a8d, 807e51c5): ACCEPTED by LEAD: G2 / G12 (the tier border's long roll: 0.4 m over 12-30 m waves), G3 (an open shaft lit all the way down), G4 (the wall's rows shifted), G7, G10, G11, the sea's 2_sea_3m. OPEN: the seabed's fade re-shots (step 4), G5's two objects and smoke_36's pocket frame (the next smoke: "[MERIDIAN] smoke G5 near the surveyor" lines).
- For LEAD's B-237 / B-239 question, answered: a giant's far disc draws at 6.0 screen px a texel at the wheel's closest zoom and 9.0 at the end of the entry's push-in; never 12.

## Last completed
- U-206 (3f3ed7f8, 06edd642): the pale box on every non-Earth planet was the camp's gull spawned on every planet's stage; in Review until the next build's smoke_21 Mars.
- BUILD 0.6.2 (b49a6305); U-195, U-196, U-200, U-204 DONE on its smoke.
- tools/unity_profile.ps1 `-Control <version>` (D-191 amended): in git, parse-checked, first run at 0.6.3; the probe now also prints the player's graphics API and is red off Direct3D 11.

## Next up
See the order above. In the gaps: name the AI's first-time frame (~86 frames after the spawn, Earth only) and warm it at load if it can be; make the gate's C0 draw-call row repeatable (a fixed creature set); U-202 part 2's four readings a build.

## Ready for review
U-206; U-205 (but the two sea re-shots). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
(none open)
## Blockers
THE RAM GATE (above): USER-42.
## Proposals
(none open)
## For USER_ACTIONS
USER-42 (LEAD): restart the three windows and the laptop. USER-40: quit the Ollama app and the Xbox app (the Xbox app held 0.3 GB private at 00:04).
## Housekeeping
Editor churn in the tree (Generated/Models *.mat, regenerated animator.controller files, link.xml deletions, UnderwaterTint.mat): never staged; commits list files explicitly. perf_2026-11-09.md: a BudgetGate run rewrites the whole file and a probe run replaces its last section: restore the readings sections from git under the gate's rows after a gate run, and save the last build's player rows before a probe. The helper scripts in the session's scratchpad (u205_*.ps1, u207_*.ps1) are each one lock around tools/unity_check.ps1 / unity_capture.ps1 / unity_build.ps1 and are not needed to resume.
## HeavyJobLock
none held (the first probe lock released 11-09 23:52); no want. No background waiters.
