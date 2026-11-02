# MERIDIAN — Task Board

Owner: LEAD (only LEAD edits this file). Workers mirror their task state in their status
files; LEAD moves cards. Statuses: Ready · In Progress · Review · Done · Blocked.
IDs: L-### LEAD, U-### UNITY, B-### BLENDER. Order within a role = priority.

Format:
```
### <ID> · <OWNER> · <Status> · <Milestone>
Goal: …
Accept: … (measurable)
Files: …
Depends: …
Lead notes: …
```

---

## LEAD

### L-001 · LEAD · Done · M0
Goal: Save every architect file at its exact path; add the "Clone the repo" step to the README.
Accept: `git log` shows `[lead] L-001 architect docs`; all paths from the architect output exist.
Files: all architect files
Depends: —
Lead notes: Done 4c10618.

### L-002 · LEAD · Done · M0
Goal: Audit `zubersss/universegame`; archive the old MERIDIAN build.
Accept: branch `archive/meridian-v1` and tag `meridian-v1-final` pushed; D-009 filled in with what the old build contained; old build files removed from `main` with `git rm -r`; nothing deleted from history.
Files: DECISIONS.md, repo root
Depends: L-001
Lead notes: Never `git checkout`/`git switch`; create the branch with `git branch archive/meridian-v1 main`. Done 21d0584; branch + tag at 4c10618; play/meridian/ and the old GPT automation kept by user choice (D-012).

### L-003 · LEAD · Done · M0
Goal: `.gitignore`, `.gitattributes` (LFS), `git lfs install`, tracked empty folders.
Accept: `git lfs track` lists png/blend/fbx/wav/ogg/mp3/exr/hdr/psd; `logs/`, `Build/`, `blender/preview/`, `coordination/locks/`, `Library/` ignored; `coordination/reports/unity/`, `coordination/reports/blender/` exist.
Files: .gitignore, .gitattributes, coordination/reports/*/.gitkeep
Depends: L-001
Lead notes: Done 4396dfa; `git lfs install --local` (repo hooks only).

### L-004 · LEAD · Done · M0
Goal: Verify `.claude/settings.json` against the current Claude Code docs.
Accept: file parses; every deny entry kept; `defaultMode` confirmed valid; a one-line note in REVIEW_LOG.
Files: .claude/settings.json
Depends: L-001
Lead notes: Done (see REVIEW_LOG cycle 1). PowerShell deny rules added; PowerShell allow rules await the user (USER-08).

### L-005 · LEAD · Done · M0
Goal: Pin exact versions (Unity, Blender, URP, Addressables, Claude Code) in Bible §12; write `tools/paths.json`.
Accept: §12 has no blanks; `tools/paths.json` has `unityExe` and `blenderExe` that exist on disk.
Files: docs/PROJECT_BIBLE.md, tools/paths.json
Depends: USER-01…04
Lead notes: Done (cycle 2). Unity 6000.6.5f1, Blender 5.2.2 LTS found on disk; D-013, D-014.

### L-006 · LEAD · Done · M0
Goal: Confirm USER-01…06, then release the workers.
Accept: "READY FOR WORKERS" appended to USER_ACTIONS.md with the date; both worker queues have ≥ 5 Ready tasks.
Files: coordination/USER_ACTIONS.md
Depends: L-002…L-005
Lead notes: Done (cycle 2). Queues: U-001 and B-001 unblocked; the rest unlock along each worker's own chain.

### L-007 · LEAD · Done · M0
Goal: LeadQA test assembly and smoke test.
Accept: `Assets/_Game/Tests/LeadQA/MERIDIAN.Tests.LeadQA.asmdef`; `SmokeTests.cs` loads `Core.unity`, asserts `LogAssert.NoUnexpectedReceived()`; passes via `tools/unity_test.ps1 PlayMode`.
Files: Assets/_Game/Tests/LeadQA/
Depends: U-004
Lead notes: Done (cycle 9): SmokeTests.cs passes via unity_test.ps1 PlayMode (LeadQA 1/1 at 12:42, 12:48, 12:55).

### L-008 · LEAD · Done · M0
Goal: M0 exit review and report.
Accept: every M0 exit criterion (Bible §12) checked with evidence in REVIEW_LOG; `coordination/reviews/M0_REPORT.md` under 200 words; `warnings_baseline.txt` created.
Files: coordination/REVIEW_LOG.md, coordination/reviews/
Depends: U-005, B-002, L-007
Lead notes: Done (cycle 9): M0 exit evidence in REVIEW_LOG cycle 9; coordination/reviews/M0_REPORT.md; warnings_baseline.txt = 0.

### L-009 · LEAD · In Progress · M1
Goal: Groom M1; draft M2 tasks in `## Backlog`.
Accept: ≥ 5 Ready per worker at all times during M1; M2 drafts cover every Bible §12 M2 item.
Files: coordination/TASK_BOARD.md
Depends: L-008
Lead notes: —

### L-010 · LEAD · Done · M1
Goal: M1 QA scenario and report.
Accept: LeadQA PlayMode test drives Earth → launch → Mars well → entry → landing → save → load; passes twice; `M1_REPORT.md` written; `Build/MERIDIAN_0.1.0/` plays.
Files: Assets/_Game/Tests/LeadQA/M1LoopTests.cs, coordination/reviews/M1_REPORT.md
Depends: U-017
Lead notes: Done (cycle 17): M1LoopTests passed twice (15:55, 16:42; touchdown 2.00 m/s); M1_REPORT.md; Build/MERIDIAN_0.1.1 plays (U-031 smoke). User playtest posted as USER-09.

### L-011 · LEAD · Done · M2
Goal: M2 QA: a LeadQA soak scenario that plays Earth (day → night, dig, creatures nearby) then flies to Mars through a dust storm, for ≥ 10 min of game time in one PlayMode run, with a clean console and BudgetGate rows recorded, plus the M2 screenshot set checked against §9.
Accept: Tests/LeadQA/M2SoakTests.cs passes twice; screenshots (Earth day/night with creatures and POIs, Mars canyon + storm, space with all planets) reviewed in REVIEW_LOG; M2_REPORT.md written.
Files: Assets/_Game/Tests/LeadQA/, coordination/reviews/M2_REPORT.md
Depends: U-033, U-034, U-037, U-039, B-015, B-016
Lead notes: Done (cycle 97): M2SoakTests passed twice (14:30, 14:33; touchdowns 2.68 and 4.80 m/s); screenshots reviewed; M2_REPORT.md written; owner playtest = USER-12.

### L-012 · LEAD · Done · M3
Goal: M3 QA: LeadQA M3InnerTests: Earth → launch → Mercury entry; survive a forced flare in a shelter; mine solarite in the window; fly to Venus; dock-free direct entry to the deck station; craft a radiation liner; sell at the Earth Waystation; ≤ 15 min game time per run; clean console; M3_REPORT.md + milestone page.
Accept: passes twice; screenshots checked vs §9; M3_REPORT written; owner playtest posted.
Files: Assets/_Game/Tests/LeadQA/M3InnerTests.cs, coordination/reviews/M3_REPORT.md
Depends: U-060
Lead notes: Done (cycle 168): M3InnerTests 738fd43 passed twice (UNITY checks 23:16 and 23:46, 7/7 each); 0.3.0 smoke shots checked; M3_REPORT.md written; milestone page published https://claude.ai/artifact/EfXnC1s4pys8zi3e5WDeQy; USER-16 playtest posted. M3 closes on the owner's playtest.

---

## UNITY

> **R1 (D-062).** 2D tasks U-061..U-071 are Superseded (their code and sources stay in the tree and
> get reused). R-tasks below rebuild Earth in 3D while keeping every system.

### U-072 · UNITY · Done · R1
Goal: 3D renderer and side-rail camera: switch the URP asset to the Universal (3D) Renderer with Forward+ (keep the 2D renderer asset in the project for the archive branch only); a perspective Cinemachine camera on a rail at z = −18 m, vertical FOV 35°, following the player on z = 0 with the current damping and look-ahead, giving ≈ 60 px/m at 1080p; Physics2D untouched; the HUD, panels and Space scene unchanged; `ArtMaterials` gains URP/Lit entries.
Accept: Core, Space and PlanetSide load with no errors; M1LoopTests + SmokeTests pass; an EditMode test asserts the on-plane density (60 ± 3 px/m); a capture shows the terrain with depth (placeholder blocks).
Files: Assets/_Game/Settings/, Code/Runtime/Camera/, Prefabs/
Depends: —
Lead notes: Done c70bfd8 + b395a26 + 308aac2 (cycle 174): Universal renderer Forward+, side rail per D-064, SideViewTests 60.0 px/m, EditMode 229/229, PlayMode 0 failed incl. M1LoopTests + SmokeTests; earth_perspective_rail.png checked. The "depth" and lighting parts of the Accept line belong to U-073/U-074 and move there.

### U-073 · UNITY · Done · R1
Goal: Chunk block mesher (Bible §10.4 v2): `TerrainChunk` builds one greedy-meshed block mesh of 1 m cubes (exposed faces only, 1 m deep) with UVs into a per-planet `Texture2DArray` (top/side layer per tile material; flat placeholder colours until B-080); a back-wall quad; dig/place rebuilds only that chunk within the frame; the Tilemap stays for collision and data with its renderer off; `TerrainBlocks` shader (array textures, height blend between layers).
Accept: EditMode: face count for a known chunk pattern; rebuild ≤ 2 ms per chunk (D-019); PlayMode: dig removes the block in the same frame and collision matches; streaming within budget; FootingTests green.
Files: Assets/_Game/Code/Runtime/Terrain/, Shaders/
Depends: U-072
Lead notes: Done 7d76dbf + 105bffa (cycle 184): greedy block mesher, TerrainBlocks shader with B-080 arrays, D-067 fringe, back wall; chain 5: dig same frame, FootingTests and streaming green; captures earth_blocks_b080(_depth). The core-loop regression found in chain 4 was the pad placeholder card (8810845), tracked in the log.

### U-074 · UNITY · In Progress · R1
Goal: 3D lighting from `TimeSystem` (Bible §10.5 v2): one directional Sun (angle, colour, intensity per planet per §9 and D-030), per-planet ambient gradient, soft shadows (one cascade, 30 m), bloom; lamps, thrusters, vents become point lights (≤ 8 visible); distance fog per planet replaces the haze gradient; Light2D components removed.
Accept: DayNightTests adapted (noon/midnight intensities per §9); night darkens the terrain; a lamp pools light on blocks and the back wall; BaseTests green; budgets.
Files: Assets/_Game/Code/Runtime/Planet/Lighting/, Building/
Depends: U-072
Lead notes: Cycle 171. R1.

### U-075 · UNITY · In Progress · R1
Goal: Model-based views: `CharacterView`/`CreatureView` drive an Animator with clips named exactly as the old sheet clips (contract §5 names), facing by a 180° yaw turn, hit flashes by material property; `ArtImporter` v5 imports `.glb` per contract §9 (materials from the four maps, clip names kept, address = key, placeholder retired); capsule/box placeholders until B-078/B-082; the hit/footing/interaction code unchanged.
Accept: ArtImporterTests for a sample glb (B-077's calibration model); every clip name used in code resolves on the placeholder Animator; FootingTests, creature tests green.
Files: Assets/_Game/Code/Runtime/Creatures/, Player/, Code/Editor/ArtImporter.cs, Tests/
Depends: U-072
Lead notes: Cycle 171. R1. Handshake with B-077 like B-002/U-005.

### U-076 · UNITY · Ready · R1
Goal: Ship, props and depth bands: the Pilgrim and props batch 1 as model prefabs (placeholders until B-079/B-081); the building system places 3D prefabs on the plane; the three parallax layers become depth bands (near props plane z 2–6 m, mid ridge mesh strip z 20–60 m, far skyline + sky dome ≥ 150 m) fed by the planet config; Space keeps its top-down view with planet spheres.
Accept: an Earth capture shows blocks, back wall, ridges, sky dome and the ship with depth; BuildTests, ShipSideTests, SpaceArtTests green.
Files: Assets/_Game/Code/Runtime/Ship/, Building/, Planet/Backdrop/, Prefabs/
Depends: U-073, U-074
Lead notes: Cycle 171. R1. Cycle 179: the landing pad is now a 2 m module (D-068): the camp spawns two modules (4 m) under the Pilgrim; landing-rule width = 4 m; shelter_door plays its `open` clip; lamps light from socket_light.

### U-077 · UNITY · Ready · R1
Goal: BudgetGate 3D rows (Bible §11.1 geometry row: ≤ 300 k triangles, ≤ 400 draw calls, ≤ 150 shadow casters) + `unity_profile` reads them; R1 build `Build/MERIDIAN_0.4.0/` with a smoke set (Earth day, night with a lamp, digging, the ship landed and flying, Space).
Accept: every BudgetGate row green on Earth in the dev build; smoke clean; GameInfo 0.4.0.
Files: Assets/_Game/Tests/Unit/BudgetGateTests.cs, tools/unity_profile.ps1, Build/
Depends: U-075, U-076
Lead notes: Cycle 171. R1 close, with the owner's playtest.


### U-001 · UNITY · Done · M0
Goal: Unity 6 project at repo root with URP 2D Renderer, Input System, Addressables, Test Framework, Cinemachine, TMP; folder tree and asmdefs; compile script.
Accept: `tools/unity_compile.ps1` exits 0 with zero `error CS`; asmdefs `MERIDIAN.Runtime`, `MERIDIAN.Editor`, `MERIDIAN.Tests.Unit`; packages pinned in `Packages/manifest.json`; URP asset uses the 2D Renderer.
Files: Assets/_Game/**, Packages/, ProjectSettings/, tools/unity_compile.ps1
Depends: L-005
Lead notes: Done add133b (cycle 4): latest unity_compile log 0 error CS / 0 warnings; 3 asmdefs; manifest pinned; MERIDIAN_URP uses MERIDIAN_Renderer2D.

### U-002 · UNITY · Done · M0
Goal: `PlanetConfig` ScriptableObjects for all 8 planets with Bible §4.1 and §5.1 values; tests.
Accept: EditMode tests assert every gravity ratio ±0.5%, launch fuel = round(1.5·v_esc), world width/height/datum/escape/crush per §5.1, all 8 configs present.
Files: Assets/_Game/Code/Runtime/Planets/PlanetConfig.cs, Assets/_Game/Settings/Planets/*.asset, Assets/_Game/Tests/Unit/PlanetConfigTests.cs
Depends: U-001
Lead notes: Done 886065c (cycle 4): PlanetConfigTests cover all 8 planets, ratios ±0.5%, fuel, §5.1 dimensions; EditMode 27/27.

### U-003 · UNITY · Done · M0
Goal: Batch test and build scripts.
Accept: `tools/unity_test.ps1 [EditMode|PlayMode]` writes `logs/tests_<date>.xml` and `coordination/reports/unity/tests_<date>.md` (pass/fail counts, failed names); `tools/unity_build.ps1` produces a dev build in `Build/`; both honor HeavyJobLock and exit non-zero on failure.
Files: tools/unity_test.ps1, tools/unity_build.ps1, Assets/_Game/Code/Editor/BuildTools.cs
Depends: U-001
Lead notes: Done b6aae59 (cycle 5): test reports written for both modes; Build/MERIDIAN_0.0.1/MERIDIAN.exe built; HeavyJobLock retry wrapper.

### U-004 · UNITY · Done · M0
Goal: `Core.unity` with `GameState`, `SceneDirector`, `TimeSystem` (72×), bootstrap; `Space.unity` and `PlanetSide.unity` stubs loaded additively.
Accept: Play from Core loads Space (inactive) and PlanetSide (Earth config); smoke test with `LogAssert.NoUnexpectedReceived()` passes.
Files: Assets/_Game/Scenes/, Assets/_Game/Code/Runtime/Core/
Depends: U-002
Lead notes: Done c5ba83a (cycle 5): PlayMode boot test 1/1 with LogAssert.NoUnexpectedReceived; Earth g = −9.81.

### U-005 · UNITY · Done · M0
Goal: `ArtImporter` + `ArtKeys` + M1 placeholder set.
Accept: Every rule in contract §6 implemented and covered by an EditMode test; placeholders exist for: characters/surveyor, ships/pilgrim/top+side, terrain/earth/{soil,grass,stone,sand,snow,water}, terrain/mars/{regolith,basalt,hematite,ice}, backgrounds/{earth,mars,space}/layer0..2, planets/{sun,mercury,venus,earth,mars,jupiter,saturn,uranus,neptune}/surface, planets/earth/clouds, fx/{thruster,dust,dig_sparks,escape_band,heat_shimmer}, props/common/calibration; importing B-002's calibration asset retires its placeholder with no manual step.
Files: Assets/_Game/Code/Editor/ArtImporter.cs, Assets/_Game/Code/Runtime/Art/ArtKeys.cs, Assets/_Game/Placeholders/**, Assets/_Game/Tests/Unit/ArtImporterTests.cs
Depends: U-001
Lead notes: Done bb0d201 (cycle 5): EditMode 45/45 incl. 17 importer tests; calibration imports clean and retires its placeholder (handshake import side OK).

### U-006 · UNITY · Done · M0
Goal: Lit art preview tool.
Accept: `tools/unity_art_preview.ps1 <key>` renders the sprite under a global light plus one upper-right point light to `logs/preview_<key>.png` in batch mode.
Files: tools/unity_art_preview.ps1, Assets/_Game/Code/Editor/ArtPreview.cs, Assets/_Game/Scenes/ArtPreview.unity
Depends: U-005
Lead notes: Done 5a75d90 (cycle 6): PlayMode capture works; calibration lit upper-right; previews in reports/unity/previews_2026-10-30.md.

### U-021 · UNITY · Done · M0
Goal: `tools/unity_test.ps1 PlayMode` also runs `MERIDIAN.Tests.LeadQA` (and EditMode runs it if it ever has EditMode tests).
Accept: `-assemblyNames "MERIDIAN.Tests.Play;MERIDIAN.Tests.LeadQA"` (or an `-Assembly` parameter defaulting to both); the report lists LeadQA results; commit the generated `Assets/_Game/Tests/LeadQA.meta` (folder meta in your Tests/ folder).
Files: tools/unity_test.ps1, Assets/_Game/Tests/LeadQA.meta
Depends: —
Lead notes: Done d185084 (cycle 7): PlayMode runs MERIDIAN.Tests.LeadQA by default with a per-assembly report; LeadQA.meta committed.

### U-023 · UNITY · Done · M1
Goal: HeavyJobLock fairness + memory gate in `tools/unity_common.ps1` (D-026).
Accept: Enter-HeavyJobLock writes `want_unity.lock` while waiting and deletes it on acquire; refuses to acquire if another role's `want_*.lock` < 30 min old exists and UNITY held the lock within the last 2 min; refuses below 1.5 GB free RAM (prints the number); Exit removes the lock. Run the full check set once per task hand-off, not after each edit.
Files: tools/unity_common.ps1
Depends: —
Lead notes: Done d692fdb + e2ca48d (cycle 11): want file, 2-min yield, 1.5 GB gate, 20-min cap; self-test 11/11.

### U-022 · UNITY · Done · M1
Goal: Top-down follow-ups from the U-011 review: apply the Sun's k_sun = 0.80 (D-022); draw `backgrounds/space/layer0..2` as parallax behind the system (layer0 slowest) and `planets/sun/glow` + `planets/*/glow` behind discs (B-003/B-005 handoffs: glow world width 2.56 × R planets, 3.2 × R Sun).
Accept: EditMode test: Sun pull at r = 1150 is 14.9 ± 0.1 u/s² and equals Mk1 thrust at r ≈ 810; PlayMode test: a Mk1 ship parked at Mercury's ring escapes to r > 1,300 with full thrust outward; capture_space shows stars + Milky Way band and planet glows; draw calls stay within §11.1.
Files: Assets/_Game/Code/Runtime/Space/, Assets/_Game/Scenes/Space.unity, Tests/
Depends: U-011
Lead notes: Done 4fded11 (cycle 9): k_sun 14.9 u/s² at 1150, Mk1 escapes Mercury ring in 4.0 s; capture_space shows stars, Milky Way, Earth glow; 24 draw calls.

### U-007 · UNITY · Done · M1
Goal: Terrain v1: 32×32 chunks, `IWorldGenerator`, `SolidWorldGenerator` (Earth, Mars), streaming, pooling, RuleTiles with normal maps, per-chunk collision.
Accept: Earth world streams at ≤ 12 ms frame on the dev laptop; chunk apply ≤ 2 ms per frame; only chunks within 2 of the camera resident (PlayMode test); seams invisible at ortho size 9.
Files: Assets/_Game/Code/Runtime/Terrain/, Assets/_Game/Prefabs/Terrain/
Depends: U-004, U-005
Lead notes: Done 2007876 + 015407a + 328c616 (cycle 7): tests per D-019; ortho-9 capture (reports/unity/capture_earth_surface_2026-10-30.png) shows no seams.

### U-008 · UNITY · Done · M1
Goal: Dig and place with diffs.
Accept: Beam removes a tile and spawns its item; Builder places a tile; diffs recorded per chunk; PlayMode test: dig → save → load → tile still absent.
Files: Assets/_Game/Code/Runtime/Terrain/TerrainEdits.cs, Code/Runtime/Rig/
Depends: U-007
Lead notes: Done f15f617 (cycle 7): EditMode 57/57, PlayMode 4/4; dig/place diffs survive save → load. Rig reach 5 m and no inventory check until M3 accepted (D-021).

### U-009 · UNITY · Done · M1
Goal: Player controller with real gravity.
Accept: walk 4.0 / sprint 6.5 m/s; v₀ 7.00 m/s; jump height within ±3% of Bible §4.2 on Earth, Mars, Jupiter (test scenes with each `PlanetConfig`); fall damage 12/24 m/s thresholds; terminal velocity per planet; coyote 0.10 s, buffer 0.12 s; Jetpack Mk1 14 m/s² for 3 s; Input System map per Bible §6.
Files: Assets/_Game/Code/Runtime/Player/, Assets/_Game/Settings/Input/, Tests/Unit/PlayerPhysicsTests.cs
Depends: U-004
Lead notes: Done 089657b (cycle 8): jump heights Earth 2.497 / Mars 6.586 / Jupiter 0.988 m, walk/sprint, terminal, fall damage, Jetpack Mk1; EditMode 75/75, PlayMode 13/13; capture_earth_player OK. Jetpack input per D-023.

### U-010 · UNITY · Done · M1
Goal: Side-view ship: board/exit, Mk1 thrust, launch fuel burn, landing rules, Escape Line band + HUD marker.
Accept: Launch from Earth costs 17 fuel over the first 3 s of thrust from rest; crossing the Escape Line with v_y > 0 raises `EscapeLineCrossed`; touchdown ≤ 6 m/s no damage, 6–15 proportional, > 15 crash to 30% hull; PlayMode test for each.
Files: Assets/_Game/Code/Runtime/Ship/, Prefabs/Ship/Pilgrim.prefab, Tests/Unit/ShipSideTests.cs
Depends: U-009
Lead notes: Done 98091e0 + 3707e5a (cycle 10): ShipSideTests cover 17-fuel launch, half burn, EscapeLineCrossed once, clean/proportional/crash touchdown, Mk1 can't lift on Jupiter; PlayMode 25/28 + LeadQA 1/1; landing floor per D-027.

### U-011 · UNITY · Done · M1
Goal: Top-down space: Sun, 8 planet discs (placeholder `PlanetDisc`), moons, belt, Gravity Wells, Atmosphere Rings, cruise/boost ship, HUD, camera.
Accept: positions and radii per Bible §3; well pull at Earth's 4R edge = 1.00 u/s² ±1% (EditMode test on the formula); cruise 80 / boost 160 u/s; Earth → Mars flight works; ≤ 80 draw calls.
Files: Assets/_Game/Code/Runtime/Space/, Assets/_Game/Shaders/PlanetDisc.shadergraph, Scenes/Space.unity
Depends: U-004
Lead notes: Done d6831d4 (cycle 8): layout §3, wells (Earth edge 1.00, Earth ring 11.1, Jupiter ring 28.1 u/s²), cruise/boost, Earth→Mars 8.0 s, 16 draw calls; EditMode 88/88, PlayMode 15/15. Mercury/Sun conflict resolved by D-022; background + glows + k_sun follow up in U-022.

### U-012 · UNITY · Done · M1
Goal: Both transitions per Bible §5.2–5.3.
Accept: launch ≤ 1.5 s total with state carried (hull, fuel, cargo), ship on the Atmosphere Ring at the longitude angle with 20 u/s outward; entry on inward ring crossing or F: ship at Escape Line + 20 m descending 15 m/s with planet gravity; PlayMode tests for both.
Files: Assets/_Game/Code/Runtime/Core/SceneDirector.cs, Code/Runtime/Transitions/
Depends: U-010, U-011
Lead notes: Done 5fecaeb (cycle 11): launch 1.05 s to Earth ring at longitude+rotation, 20 u/s out, state carried; entry at Escape Line + 20 m descending 15 m/s in 1.10 s; TransitionTests + TransitionMathTests; PlayMode clean 13:53.

### U-013 · UNITY · Done · M1
Goal: Save/load per Bible §10.7.
Accept: `state.json` + `terrain_<planet>.bin`; autosave on transitions and every 5 min; 3 rotating backups; version field; PlayMode test: save → load → identical state and terrain.
Files: Assets/_Game/Code/Runtime/Save/
Depends: U-008, U-012
Lead notes: Done e047727 (cycle 11): LocalLow/Zubers/MERIDIAN/saves/slotN, 3 rotating backups, atomic writes, version + migrations, autosave on transitions + 5 min; SaveLoadTests save → load identical; EditMode 108/108, PlayMode 28/28 at 13:53.

### U-014 · UNITY · Done · M1
Goal: BudgetGate v1, `BudgetMonitor`, profiling script.
Accept: tests for frame time, GC per 300 frames, light and particle caps, memory on Earth, Mars, Space; `tools/unity_profile.ps1` writes `coordination/reports/unity/perf_<date>.md` with every Bible §11.1 row.
Files: Assets/_Game/Tests/Unit/BudgetGateTests.cs, Code/Runtime/Perf/BudgetMonitor.cs, tools/unity_profile.ps1
Depends: U-007, U-011
Lead notes: Done a289721 (cycle 12): perf_2026-10-30.md all §11.1 rows green on Intel UHD at 1080p (Earth avg 5.1 ms, p99 7.8; Space 1.8/3.1; Mars 3.5/5.3; textures ≤ 342 MB; loads 1.1 s); first-frame stall → U-028; GC metric per D-029.

### U-015 · UNITY · Done · M1
Goal: HUD and menus v1.
Accept: main menu (New, Continue, Quit), pause, side HUD (health, oxygen placeholder, fuel, altitude bar with Escape Line marker), top HUD (speed, fuel, well indicator); OFL font logged in `docs/credits/unity.md`.
Files: Assets/_Game/UI/, Code/Runtime/UI/
Depends: U-010, U-011
Lead notes: Done 458709a (cycle 13): main menu, Esc pause, side/ship/top HUDs, JetBrains Mono (OFL) credited; EditMode 111/111, PlayMode 33/33. Visual check folded into L-010 M1 QA.

### U-016 · UNITY · Done · M1
Goal: Placeholder audio set and `AudioDirector`.
Accept: CC0 SFX for jump, land, dig, place, thrust, UI click; one ambient loop; every file's source and license in `docs/credits/unity.md`; Vorbis; ≤ 10 MB total.
Files: Assets/_Game/Audio/, Code/Runtime/Audio/, docs/credits/unity.md
Depends: U-004
Lead notes: Done 37f9ed9 (cycle 9): 7 synthesized CC0 clips (1.9 MB), AudioDirector with one listener; PlayMode clean incl. LeadQA; credits logged.

### U-028 · UNITY · Done · M1
Goal: Shader/pipeline warm-up during planet load (ShaderVariantCollection or a hidden pre-render) so the first visible frame doesn't stall (P-17).
Accept: BudgetGate first-visible-frame time ≤ 50 ms after Earth load, Mars entry, and launch into Space (was 215–800 ms); planet load stays ≤ 4 s.
Files: Assets/_Game/Code/Runtime/Core/, Assets/_Game/Settings/Rendering/
Depends: U-014
Lead notes: Done 58b1375 (cycle 14): first visible frame Earth 7.5 / Space 2.4 / Mars 1.5 ms (was 215–800); BudgetGate green.

### U-017 · UNITY · Done · M1
Goal: M1 integration and build.
Accept: PlayMode integration test Earth → launch → Mars → land → save → load passes twice with a clean console; `Build/MERIDIAN_0.1.0/` built by `tools/unity_build.ps1`; perf report green.
Files: Assets/_Game/Tests/Unit/M1IntegrationTests.cs, Build/
Depends: U-005…U-016
Lead notes: Done 72db6b1 + 7bc9e0d (cycle 15): M1IntegrationTests own-controls loop passed twice with clean consoles (touchdown 2.05 m/s); Build/MERIDIAN_0.1.0 + smoke screenshots. Gear look fixed in the rebuild (U-031).

### U-018 · UNITY · Done · M2
Goal: Swap Pilgrim's side sprite to `ships/pilgrim/side_legs` below 10 m altitude (Bible §4.3), back above it.
Accept: PlayMode test: descending through 10 m switches the sprite; climbing back through 10 m switches back; no pivot jump (same world position of the hull ±1 px).
Files: Assets/_Game/Code/Runtime/Ship/
Depends: U-010, B-019 (build against the placeholder until B-019 is Done)
Lead notes: Done 6aea64d (cycle 15): side_legs ≤ 10 m, side above; pivots within 1 px; ShipSideTests 7/7 at 16:00.


### U-019 · UNITY · Done · M1
Goal: `Sprite_LitEmissive` Shader Graph material (Bible §10.5): Sprite-Lit with `_NormalMap` and an additive `_EmissionMap` (+ intensity), used by ArtImporter for any asset with an `_emission` map.
Accept: lit preview of `props/common/calibration` shows the stripe at its emission color under zero point light; `ships/pilgrim/side` portholes and engine glow; `planets/sun/surface` self-lit; ArtImporter assigns the material automatically (EditMode test).
Files: Assets/_Game/Code/Runtime/Rendering/, Assets/_Game/Settings/Rendering/, Code/Editor/ArtImporter.cs, Tests/
Depends: U-005, U-006
Lead notes: Done 42988db (cycle 9): HLSL Sprite_LitEmissive; no-point-light previews show calibration stripe, Pilgrim ports/engine/vents, self-lit Sun; ArtMaterials registry auto-filled; EditMode 96/96.

### U-020 · UNITY · Done · M1
Goal: Terrain variants: when a sheet has tiles in slots 47–62, tile 46 picks one of them by a stable hash of (x, y) (D-020).
Accept: same world → same variants after save/load; no variant chosen for sheets without slots 47–62; chunk apply budget unchanged (D-019); EditMode test for hash stability.
Files: Assets/_Game/Code/Runtime/Terrain/
Depends: U-007, B-022
Lead notes: Done d455251 (cycle 14): slots 47–62 sliced, stable wrapped (x, y) hash; EditMode 116/116, PlayMode clean 15:36.

### U-031 · UNITY · Done · M1
Goal: Rebuild the M1 playtest build after U-018 as `Build/MERIDIAN_0.1.1/` and redo the build smoke screenshots.
Accept: on the ground the Pilgrim shows deployed skids touching the terrain (no floating hull, as seen in smoke_2_earth.png of 0.1.0, built before U-018); the menu hides the HUD behind it; smoke run clean; the 0.1.0 folder may stay.
Files: Build/ (ignored), coordination/reports/unity/smoke_<date>/
Depends: U-017, U-018
Lead notes: Done b327325 (cycle 17): Build/MERIDIAN_0.1.1; Pilgrim on deployed skids touching the ground; HUD hidden behind menus; smoke clean. This is the USER-09 playtest build.

### U-024 · UNITY · Done · M2
Goal: PlanetSide parallax: `backgrounds/<planet>/layer0..2` behind the terrain (layer0 slowest), plus a haze gradient per planet (Bible §9 Atmosphere).
Accept: capture at Earth and Mars shows three layers moving at different rates when the camera pans; no seams when wrapping; ≤ 3 extra draw calls; uses the B-010/B-011 rework files when present, placeholders otherwise.
Files: Assets/_Game/Code/Runtime/Planet/, Scenes/PlanetSide.unity
Depends: U-007
Lead notes: Done 92bd0d7 + b327325 (cycle 17): 3-layer parallax with haze, cave fade; BackdropTests; captures; smoke_2_earth shows the forest backdrop behind terrain.

### U-032 · UNITY · Done · M2
Goal: Surveyor animation: drive the `characters/surveyor/base` frame-sheet clips (idle, walk, run, jump, fall, land, dig, aim, hurt, death) from the player controller; face the aim direction.
Accept: PlayMode test steps the controller through walk → run → jump → fall → land → dig and asserts the clip at each state; capture strip of 6 states; ≤ 0.05 ms per frame; uses base.json clip ranges (no hard-coded indices).
Files: Assets/_Game/Code/Runtime/Player/
Depends: U-009
Lead notes: Done 2d0d0d0 (cycle 27): clips by name from base.json via the registry, state picker, aim facing; SurveyorAnim tests; states strip OK. Perf per D-035.

### U-033 · UNITY · Done · M2
Goal: FX hookup: `fx/thruster` on the Pilgrim (side: main engine + belly pods while thrusting; top-down: engine), `fx/dig_sparks` on Beam hits, `fx/dust` on hard landings and ship touchdown, `fx/escape_band` on the Escape Line, `fx/heat_shimmer` during entry.
Accept: captures for each effect; particles alive ≤ 600 at peak in BudgetGate; pooled, 0 B GC per frame; effects respect the emissive material.
Files: Assets/_Game/Code/Runtime/FX/
Depends: U-010, U-012
Lead notes: Done 38b9583 (cycle 30): flames, sparks, dust, Escape band, entry glow, top-down flame; pooled, 0 B GC; FX peak leg green (99 draw calls). The memory row is an Editor artifact (D-036 → U-041); the hole backdrop → U-040; heat_shimmer art → B-030.

### U-034 · UNITY · Done · M2
Goal: Space art pass with B-017/B-018: all eight planet discs + glows from real art, `planets/saturn/rings` at world width ≈ 446 units (BLENDER handoff: A-ring outer edge r = 500 px of 1024, Saturn R = 220.4 px), Luna disc from `planets/luna/surface`, asteroid belt drawn with `props/space/asteroid_01..06` (instanced, varied rotation/scale).
Accept: captures of Saturn with rings, Jupiter, Neptune, and a belt segment; Space draw calls ≤ 80 and frame p99 ≤ 16.6 ms in BudgetGate; no placeholder left for any planet key.
Files: Assets/_Game/Code/Runtime/Space/, Scenes/Space.unity
Depends: U-022
Lead notes: Done ef21e93 (cycle 30): Saturn rings at 446 u, Jupiter, Neptune, Luna, belt from six asteroid sprites. Belt reads sparse at the capture zoom (minor; revisit in M4 belt mining).

### U-035 · UNITY · Done · M2
Goal: Earth spawn camp with B-014 props: `landing_pad` under the Pilgrim at spawn, two `lamp`s, a `storage_crate` stack, the `smelter` (inert until M3), placed as a stamp like U-030 POIs.
Accept: capture at spawn by day and by night (lamps glow via emission); props have colliders where you can stand on them (pad, crates); the stamp survives dig/save/load.
Files: Assets/_Game/Code/Runtime/Planet/POI/, Prefabs/
Depends: U-030
Lead notes: Done 7fcb8b0 (cycle 33): levelled camp stamp, 12 m pad, lamps, crates, smelter; SpawnCampTests 3/3; day/night captures; TopSolidY placement. Follow-up (do with U-040): pad collider top = deck surface, not the studs, so the landed ship sits on the deck (now ~0.35 m high).

### U-036 · UNITY · Done · M2
Goal: ArtImporter honors a frame sheet's `"ppu"` field (D-031) for creature and character sheets.
Accept: EditMode test: a sheet with "ppu": 104 imports sprites at PPU 104 (world size = px / 104); sheets without it stay at 128; B-015 stag/wolf appear at true size (stag ~2.3 m) in a capture next to the surveyor.
Files: Assets/_Game/Code/Editor/ArtImporter.cs, Tests/Unit/
Depends: U-005
Lead notes: Done 30af54a (cycle 26): importer honors sheet ppu; capture_creatures shows the stag at true size (~2.3 m) next to the 1.8 m surveyor.

### U-037 · UNITY · Done · M2
Goal: Earth biomes v1 in SolidWorldGenerator (Bible §7.1): longitude bands for temperate forest (spawn), plains, desert, taiga, tundra, and ocean basins (water tiles to depth 250, D-010) with smooth transitions; surface material per biome (grass/soil, sand, snow, stone, water).
Accept: EditMode test: biome at x is deterministic per seed and every biome appears once in 4096 columns; spawn is in forest; ocean has water to sea level (Datum 320) and a trench ≥ 120 m deep; chunk apply stays within D-019; captures of each biome.
Files: Assets/_Game/Code/Runtime/Terrain/
Depends: U-007
Lead notes: Done fdc0885 (cycle 41): six longitude biomes with blended borders, ocean to 244 m, the water darkens with depth and hides the backdrop, the seabed is visible; unity_check one-lock hand-off: EditMode 142/142, PlayMode 56/56 + LeadQA 2/2.

### U-038 · UNITY · Done · M2
Goal: Backdrop switching by biome: PlanetBackdrop cross-fades to `backgrounds/earth_desert|earth_taiga|earth_coast` over ~20 m at biome borders (B-026; falls back to backgrounds/earth until those exist).
Accept: capture pair at a forest/desert border; no draw-call growth beyond +3 during a fade; no hitch > 33 ms at a border.
Files: Assets/_Game/Code/Runtime/Planet/
Depends: U-037, U-024
Lead notes: Done 1c2addc (cycle 91): biome cross-fade, border walk worst frame 9.0 ms, +1 quad; also fixed sea tint to apply only on water columns.

### U-039 · UNITY · Done · M2
Goal: Mars landforms (Bible §7.2): Valles Marineris canyon (wide, 180 m deep, layered walls), Olympus Mons shield (3 km wide, 300 m tall, caldera), polar ice caps (CO₂ over water ice at both ends of x), lava-tube caves (natural radiation shelters, flagged for M3 Radiation).
Accept: EditMode tests for each feature's position/size per seed; captures of canyon wall, Olympus flank, polar cap, and a lava tube; streaming within D-019.
Files: Assets/_Game/Code/Runtime/Terrain/
Depends: U-007
Lead notes: Done 0ff59d4 + 5e69dad (cycle 47): landforms per D-040; random caves suppressed inside landforms (small pockets only); backdrop hung from the Datum; entry 1.48 → 1.21 s (profile once per world, sheets preloaded). The remaining canyon-floor backdrop artifact goes to U-040.

### U-040 · UNITY · Done · M2
Goal: Background walls: a dug or natural underground cell shows a dark wall of the surrounding material (soil, stone, sand…) behind it instead of the sky/parallax backdrop; surface holes ≤ 3 m deep show the wall too.
Accept: capture of a fresh 1-tile hole and a cave (no forest visible through either); wall persists through save/load with the dig diffs; ≤ +2 draw calls; chunk apply within D-019.
Files: Assets/_Game/Code/Runtime/Terrain/
Depends: U-008, U-024
Lead notes: Done fb0c88a (cycle 90): background walls, canyon haze gradient (no hanging band), seabed tint, pad deck collider, shimmer behind the hull; EditMode 163/163, PlayMode 61/61.

### U-041 · UNITY · Done · M2
Goal: BudgetGate memory in a dev build (D-036): tools/unity_profile.ps1 runs the Earth/Space/Mars legs in a development build and reads system and texture memory there; Editor rows are kept as "upper bound".
Accept: perf report has build memory rows for every scene, all ≤ §11.1; the run fits the 20-min heavy cap.
Files: tools/unity_profile.ps1, Assets/_Game/Code/Runtime/Core/BudgetMonitor.cs
Depends: U-014, U-031
Lead notes: Done 4be13c8 (cycle 91): dev-player memory Earth 883/297/2, Space 780/292/2, Mars 888/354/2 MB (system/textures/audio), all within §11.1; profile -Build in 4 min.

### U-042 · UNITY · Done · M2
Goal: Fix the wolf drawing ~0.5 m below its feet in-game (creatures_v3.png). BLENDER verified the sheet: the lowest opaque pixel sits on the pivot [0.5, 0.03125] in every frame for both stag and wolf.
Accept: capture with the wolf's paws on the ground line in idle, walk, and death; a PlayMode test that a creature's lowest opaque sprite pixel is within 2 px of its feet/ground contact for every species.
Files: Assets/_Game/Code/Runtime/Creatures/, Code/Editor/ArtImporter.cs
Depends: U-036
Lead notes: Done fb0c88a (cycle 90): PawsOnTheGround passes for all four species (0 px); the sink was the pre-7c59ad7 metas.

### U-043 · UNITY · Done · M2
Goal: Strict turns in `tools/unity_common.ps1` (D-037): replace the 2-min yield window. After UNITY releases, Enter-HeavyJobLock refuses while another role's want file (< 30 min) exists, until that file is removed. Offer one wrapper call that runs compile + EditMode + PlayMode under a single lock.
Accept: self-test covering waiter present → refuse; waiter removed → acquire; stale want (> 30 min) → acquire; the batched call holds one lock throughout.
Files: tools/unity_common.ps1, tools/unity_test.ps1
Depends: U-023
Lead notes: Done 41f26e0 (cycle 37): strict turns (yield to any older want < 30 min until that role takes the lock; oldest request first), unity_check.ps1 batched check under one lock; self-test 17/17.

### U-044 · UNITY · Done · M2
Goal: M2 playtest build `Build/MERIDIAN_0.2.0/` with build smoke screenshots (menu, Earth camp by day and night, a desert/ocean border, Mars canyon in a dust storm, space with Saturn) and build memory rows (U-041).
Accept: build smoke clean; screenshots in coordination/reports/unity/smoke_<date>/; GameInfo.Version 0.2.0; every BudgetGate row green in the build.
Files: Build/ (ignored), coordination/reports/unity/smoke_<date>/
Depends: U-038, U-039, U-040, U-041, U-042
Lead notes: Done 3c1dbd1 (cycle 97): Build/MERIDIAN_0.2.0, smoke clean (7 shots), title art + logo + app icon, dev-player memory Earth 895/299, Space 785/294, Mars 888/357 MB; POI marker layout fixed. Menu overlap + canyon sky → U-047.

### U-045 · UNITY · Done · M3
Goal: Inventory v1 (M3 lookahead): item registry from `icons/*` (B-013), pickup of the pooled drops (U-008), a stack-based player inventory (40 slots, stack 999), Tab panel with icons and counts, Builder consumes the selected material (closes D-021's "no inventory check"), SaveData v2 with inventory + suit integrity (D-032) and a v1 → v2 migration.
Accept: EditMode tests for stacking/splitting/migration; PlayMode: dig → pickup → count rises → place → count falls → save → load identical; Tab panel capture; 0 B GC while the panel is closed.
Files: Assets/_Game/Code/Runtime/Items/, UI/, Save/
Depends: U-013, U-015
Lead notes: Done (cycle 99): registry, 40 × 999 inventory, pickup, Builder uses the selected slot, Tab panel (smoke_8_inventory), SaveData v2 with suit; InventoryTests 9 + InventoryPlayTests. Full check 14:37: EditMode 163/163, LeadQA 3/3.

### U-046 · UNITY · Done · M3
Goal: Rig modules v1 (Bible §6/§8; M3 needs all modules): Beam (dig/mine ray), Lance (projectile), Survey (scan ring that reveals and catalogues), Builder (placement with ghost), switched with 1–4 / Q/E; drawn in the surveyor's hand from B-037 art.
Accept: tool sprite at the hand with pivot [0.375, 0.5], rotating to the aim; muzzle offsets beam (0.47, 0.03), lance (0.52, 0.035), survey (0.30, 0.06), builder (0.44, 0.03) m; fx/beam_ray stretched from muzzle to hit (pivot [0, 0.5], tiles in x); fx/lance_bolt (pivot [0.75, 0.5]); fx/survey_scan 12-frame one-shot ring; fx/builder_ghost 8-frame pulse, tinted red when blocked; PlayMode tests per module; captures.
Files: Assets/_Game/Code/Runtime/Rig/, Player/
Depends: U-045, B-037
Lead notes: Done (cycle 106): Beam ray to terrain hit, Lance bolts (40 m/s, 30 m, 25 dmg) + creature HP, Survey ring with a Surveyed event, Builder ghost (red when blocked); grip pivot and muzzles per D-041; RigModuleTests 5 + table 2; captures OK. Save/load clock-window slack (+50 ms upper bound) noted as a test-timing tolerance, not an acceptance change.

### U-047 · UNITY · Done · M3
Goal: Polish from the M2 build review: (1) main menu: logo, tagline and buttons into the left third (the title art reserves it), so they don't overlap the Pilgrim; (2) Valles Marineris floor: show a sliver of sky above the far layer when the camera is deep in the canyon (it reads flat with haze only).
Accept: menu capture with no overlap at 1920×1080 and 1280×720; canyon-floor capture with visible sky; owner playtest feedback folded in.
Files: Assets/_Game/Code/Runtime/UI/, Planet/
Depends: U-044
Lead notes: Done (cycle 100): menu in the left third (Pilgrim clear); canyon-floor sky gradient below about 37 m under the datum; D-047 applied; border-test race fixed. The canyon floor still reads flat, so the real canyon backdrop art is B-049, and its hookup comes after.

### U-048 · UNITY · Done · M3
Goal: Mercury world (Bible §7.3): SolidWorldGenerator preset with terrain/mercury sets (B-027), a day side, a night side and a ~400 m twilight band that creeps 1 m per 6 real s, two polar cold-trap craters with water ice, backdrop from backgrounds/mercury with layer0_nosun + the Sun as its own sprite, and the Mercury POIs (B-033: flare shelter, Meridian beacon, Warden vault gate, solarite clusters).
Accept: EditMode tests for band position over time and cold-trap placement; captures of day, twilight, night and cold trap; entry ≤ 1.5 s; BudgetGate green.
Files: Assets/_Game/Code/Runtime/Terrain/, Planet/, POI/
Depends: U-039, U-030
Lead notes: Done (cycle 111): Mercury terrain, cold traps, saved terminator + flare clocks, nosun backdrop with a shader Sun, four POIs, entry 1.22 s, full check green. Visual follow-ups: U-057 (black holes, pad, violet twilight), B-050 (spiky far ridges).

### U-049 · UNITY · Done · M3
Goal: Hazards v2 + Envirosuit (Bible §7, D-032): Thermal, Radiation, Toxic and Pressure on the U-029 API; Mercury solar flares (45 s warning, then 20 s of Radiation 3; shelter in shadow, underground or a flare shelter); Mars lava tubes at Radiation 0; Envirosuit tiers Mk1–3 reduce levels (k) and swap the surveyor sheet (B-041 mk1/mk2/mk3).
Accept: EditMode tables per hazard and planet; PlayMode: a flare kills an unprotected surveyor in the open within 30 s and not inside a shelter; the Mk sheet swaps at equip; HUD shows the worst hazard.
Files: Assets/_Game/Code/Runtime/Hazards/, Player/
Depends: U-029, U-045
Lead notes: Done (cycle 109): HazardTable for Mars/Mercury/Venus per Bible §7; flares level 4 (D-048), cadence per D-049; Envirosuit tiers lower levels and swap mk1–3 sheets (saved); HUD shows the worst hazard; HazardTableTests 7 + HazardV2PlayTests 3; full check 15:44 green.

### U-050 · UNITY · Done · M3
Goal: Venus world (Bible §7.4): hybrid column with the surface (Datum 320; terrain/venus, B-028; Thermal 3, Pressure 3, Toxic 2) and the habitable cloud deck at y 770 ± 60 (backgrounds/venus_deck) where floating station props (B-045) sit; super-rotation wind (constant lateral push, 80-min cycle); acid haze ticks; backgrounds switch deck ↔ surface with altitude.
Accept: captures on the deck and on the surface by a vent; a timed surface dive is lethal without Mk2 Thermal + Pressure; wind test; budgets green.
Files: Assets/_Game/Code/Runtime/Terrain/, Planet/
Depends: U-049
Lead notes: Done (cycle 113): Venus surface (tessera, vent fields with Vitriol Glass), floating Meridian station walkway on the deck, super-rotation wind on the saved clock, surface↔deck backdrop cross-fade, dive lethal unprotected (29.6 s) and survivable with Mk2; full check green. POI pad block → U-057 (generalized).

### U-051 · UNITY · Done · M3
Goal: Crafting: Smelter (ore → bars), Refinery (fuel, glass, polymers), Blueprint Tree (story blueprints per Bible §2 table) with B-042 icons; recipes data-driven (ScriptableObjects).
Accept: EditMode recipe-graph tests (no unreachable item, no cycles); PlayMode: mine iron → smelt → craft a suit patch; UI capture of the Blueprint Tree.
Files: Assets/_Game/Code/Runtime/Crafting/, UI/
Depends: U-045
Lead notes: Done (cycle 118): RecipeBook asset (16 recipes, 10 blueprints, §2 story unlocks by beacon), Smelter at camp, Refinery + Fabricator on the Pilgrim, Blueprint Tree + recipes panel (B); CraftingGraphTests + CraftingPlayTests; full check green. UI polish (opaque panel, item icons in recipe rows, CRAFT buttons dimmed per availability) folded into U-058.

### U-052 · UNITY · Done · M3
Goal: Waystations and trading (Bible §3): dock at ships/waystation_earth|mars (B-038) in top-down; the docking-bay interior scene (backgrounds/waystation, B-039) with a Halcyon market (buy/sell in Scrip, prices per station), refuel and repair, and cargo contracts.
Accept: PlayMode: dock → sell 10 iron → Scrip rises → buy fuel → undock; prices differ Earth vs Mars; save/load keeps Scrip and contracts.
Files: Assets/_Game/Code/Runtime/Space/, Trade/, Scenes/
Depends: U-045, U-034
Lead notes: Done (cycle 124): Earth + Mars Waystations, docking (F, < 12 u, < 8 u/s), bay with Halcyon market (16 goods, per-station prices, sell 60%), refuel/repair, 2 cargo contracts each, Scrip 200 start, saved; B-051 icons wired; MarketTests 4 + WaystationPlayTests; full check green.

### U-053 · UNITY · Done · M3
Goal: Wardens basic (Bible §2): creatures/warden/sentinel (B-043, common atlas per D-043) patrol POIs and respond when the player over-mines a local area (threshold per chunk); fx/warden_bolt projectiles; the sentinel can be destroyed with the Lance.
Accept: PlayMode: digging past the threshold near a vault spawns a sentinel within 10 s; bolts damage the suit; Lance kills it; ≤ 0.3 ms AI with 6 sentinels.
Files: Assets/_Game/Code/Runtime/Creatures/Wardens/
Depends: U-046, U-027
Lead notes: Done 6c4deab (cycle 127): Warden meter, patrols at sites, hunters with bolts, Lance kills in 3, pooled; numbers per D-052; AI p99 0.06 ms; full check green. Bolt readability → B-052.

### U-054 · UNITY · Done · M3
Goal: Survey Catalogue + Datacores: the Survey module (U-046) scans creatures, minerals and POIs; first scans pay Datacores; Catalogue panel (N) lists entries with icons and per-planet completion.
Accept: PlayMode: scan a stag → entry + Datacores; rescans pay nothing; save/load keeps the catalogue; panel capture.
Files: Assets/_Game/Code/Runtime/Survey/, UI/
Depends: U-046
Lead notes: Done a7576ae (cycle 125): data-driven catalogue per planet, first-scan Datacores (D-051), N panel with % per planet, saved; tests green. Nits for the next UI touch: the catalogue panel lacks the U-058 scrim (world shows at full brightness at the sides), all planet buttons look selected, so highlight only the current one; unscanned entries could show a dark silhouette or icon instead of a blank tile.

### U-055 · UNITY · Done · M3
Goal: Inner-planet creatures + apexes: Mercury glassback, cinderling, flarewing, shadewyrm (B-029, B-035); Venus sulfur drifter, acidmoth (fliers, centred pivot), pressure crab, vent eel (B-032, B-036, B-034); apexes Cinderhulk (day/night sheets, vulnerable 2 min after crossing into night, B-040) and Veil Serpent (Cryo rounds, chilled flash on hurt frames, B-044).
Accept: each species spawns in its biome or zone with correct ground or flight placement; both apexes killable by their rule (PlayMode tests); AI ≤ 0.5 ms with 20 creatures.
Files: Assets/_Game/Code/Runtime/Creatures/
Depends: U-048, U-050, U-046
Lead notes: Done (cycle 132): 10 inner species with zone/time spawn rules, fliers, sheet animation everywhere; Cinderhulk night sheet tracks the terminator every frame (cracked dark shell when vulnerable); Veil Serpent at 3× art scale (9.8 × 2.3 m) and killable only with Cryo rounds; numbers D-053; tests 10/10.

### U-056 · UNITY · Done · M3
Goal: Bases v1: build shelter walls, doors, lamps and crates (B-014) with the Builder; a closed shelter counts as warmth and protection for hazards; Venus Aerostat platforms (B-045) with a buoyancy budget (lift ≥ load, HUD margin).
Accept: PlayMode: an enclosed shelter stops Cryo drain; an aerostat sinks when overloaded; save/load keeps the base.
Files: Assets/_Game/Code/Runtime/Building/
Depends: U-046, U-049, U-050
Lead notes: Done 4b34228 (cycle 141): wall/door/lamp/crate/deck pieces with recipes; shelter flood-fill counts as warmth; Venus aerostat buoyancy (sinks per missing lift, HUD margin); saved; BuoyancyTests + BaseTests; full check green. Sink anomaly + lamp light → U-064.

### U-057 · UNITY · Done · M3
Goal: Mercury polish from the U-048 review: (1) pure-black empty cells (right of the shelter block and under it in u048 day/night captures) should show the background wall / cold-trap shadow tone, not #000; (2) the solarite field pad lands on a crater rim and reads as a raised block, so seat it in a crater floor or on flat ground; (3) the twilight band should read violet (§7.3 "violet twilight"): add a low violet sky glow on the sunward side in the band.
Accept: re-captured day/twilight/night with no #000 holes, the pad flush, and a visible violet glow in twilight.
Files: Assets/_Game/Code/Runtime/Terrain/, Planet/, POI/
Depends: U-048
Lead notes: Done (cycle 116): PoiStamp general fix (median ground, rock fill, cleared air, ≤ 2 m shoulders; PoiShapingTests on 3 seeds), Earth-only sea clamp, seatLow for the Venus harvester (now flush), Mercury tint floor and violet twilight. Remaining nit: a pale band (the haze strip) shows under the pad deck line at the harvester; fold into the next Venus touch (U-055/U-056).

### U-058 · UNITY · Done · M3
Goal: UI readability pass (from the U-051 review): opaque or blurred panel backgrounds for the Blueprint/Recipes (B), Inventory (Tab) and future Catalogue/Market panels so the world doesn't bleed through; item icons (B-013/B-042) on every recipe input and output; CRAFT buttons clearly dimmed or disabled when you can't craft (the state must be visible, not only greyed text); the HUD hidden behind full-screen panels as on menus.
Accept: captures of the B and Tab panels over a busy forest scene; UI tests for the disabled state.
Files: Assets/_Game/Code/Runtime/UI/
Depends: U-051
Lead notes: Done (cycle 120): opaque modal panels with scrim, icon recipe rows, clear CRAFT on/off state, station tags lit in reach, shared icon cache. Two items lack icons (polymer, float cell): BLENDER B-051.

### U-059 · UNITY · Done · M3
Goal: Inner-planet "only here" resources (Bible §7, M3 exit): Solarite on Mercury's day side is harvestable only for 90 s after each flare (crystals glow, then crust over; Beam yields solarite); Venus Vitriol Glass (done) confirmed reachable; Mars Perchlorate (polar and plains deposits) and Wormplate placeholder (drop from the Tharsis Worm, M4+, stubbed); Earth Living Seed (forest/plains drop, plantable crop placeholder).
Accept: PlayMode: solarite mineable at +30 s after a flare and not at +120 s; each "only here" item obtainable on its planet in a seeded world (EditMode scan of the generators); catalogue entries exist.
Files: Assets/_Game/Code/Runtime/Terrain/, Hazards/, Items/
Depends: U-049, U-051
Lead notes: Done bac7e80 (cycle 137): solarite 90 s post-flare window (Beam cuts 3 per cluster, then crusts), Mars perchlorate deposits (plains + polar cap), Earth living seed drop, Venus vent glass confirmed, wormplate stub; OnlyHereTests 4 + SolariteTests; catalogue entries; full check green. Catalogue nits 2 and 3 fixed; scrim deepened to 78% for all panels (cycle 137).

### U-060 · UNITY · Done · M3
Goal: M3 playtest build `Build/MERIDIAN_0.3.0/` with build smoke screenshots (Mercury day + twilight + flare shelter, Venus deck station + surface vent, crafting panel, market, catalogue, a Warden, both apexes) and dev-build memory rows for all four inner planets.
Accept: build smoke clean; every BudgetGate row green in the build; GameInfo 0.3.0; the M2 UI nits (catalogue scrim, selected planet, unscanned silhouettes) folded in.
Files: Build/ (ignored), coordination/reports/unity/smoke_<date>/
Depends: U-053, U-055, U-056, U-059, U-064
Lead notes: Done 2e1f495 + 657f999 + a4fa60a (cycle 161): Build/MERIDIAN_0.3.0 (352 MB); check 22:46 compile 0/0, EditMode 224/224, PlayMode 91/110 + LeadQA 3/3, 0 failed; BudgetGate green (Earth p99 9.41 ms, Mars entry 1.34 s); dev-build textures Earth 187, Space 162, Mars 190, Mercury 258, Venus 308 MB (all ≤ 600); 18-shot smoke checked (Mercury day, Venus station read right).

### U-061 · UNITY · Superseded · M4
Goal: Cloud-column world generator (Bible §7.5, D-004): a 4096 × 2000 column with no ground; Escape Line, Datum (1-bar cloud tops), Decks 1–3, Deep and the Crush Line (y 100, lethal, pulsing "CRUSH" band); floating ice floes (solid, mineable platforms) seeded per deck with density by deck; floes sublimate 30–90 s after the player disturbs them; derelicts and creature husks as standable floes; the same chunk streaming as solid worlds. Start with Jupiter using terrain/jupiter floe_ice/floe_core and backgrounds/jupiter_deck1 (B-048).
Accept: EditMode tests for deck bands and floe density per seed; PlayMode: land on a floe from the ship, dig it, and it sublimates in the window; falling past the Crush Line respawns at the ship with a 20% Scrip fee; streaming within D-019; preload on approach (D-050).
Files: Assets/_Game/Code/Runtime/Terrain/CloudColumn/
Depends: U-007, U-048
Lead notes: Cycle 138. The first M4 task and the biggest technical unknown of the plan.

### U-062 · UNITY · Superseded · M4
Goal: Float cells + jetpack Mk2/Mk3 (Bible §4.2): Float cell Mk1 +6 m/s², Mk2 +12 buoyancy, usable only below the Datum, toggled with V; jetpack Mk2/Mk3 thrust/burn per the §4.2 table; Jupiter 2.53 g makes Mk3 the only climbing jetpack.
Accept: PlayMode on Jupiter: Mk1 jetpack slows a fall but can't climb; Mk3 climbs; Float Mk1 below the Datum arrests a fall; the HUD shows buoyancy margin.
Files: Assets/_Game/Code/Runtime/Player/
Depends: U-061
Lead notes: Cycle 138. M4.

### U-063 · UNITY · Superseded · M4
Goal: Skip Drive (Bible §3): hold J to spool 3 s, then travel at 1,200 u/s, consuming skip fuel per second; disabled inside any gravity well; skip-fuel item (Helium-3 Condensate, Saturn; deuterium from water at 1/3 efficiency) in the RecipeBook.
Accept: PlayMode: Earth → Neptune in ≈ 11 s at skip speed; refuses inside a well; fuel drains per second; the HUD shows the spool.
Files: Assets/_Game/Code/Runtime/Space/
Depends: U-034, U-051
Lead notes: Cycle 138. M4.

### U-064 · UNITY · Done · M3
Goal: (1) investigate the surveyor resting 2 m below TopSolidY ~30 m from the Mars camp (x 94), reported during U-056: the stamp's collider vs its drawn tiles, or a stale chunk collider (cf. the U-007 collider fix); (2) placed base lamps should cast a small warm Point Light 2D (radius ~5 m) so a shelter interior is lit at night (mars_shelter.png is dark inside).
Accept: a PlayMode test walks the surveyor across every POI stamp on Earth and Mars and asserts feet within 0.1 m of TopSolidY; the night shelter capture shows lamplight.
Files: Assets/_Game/Code/Runtime/Terrain/, Building/
Depends: U-056, U-057
Lead notes: Done 2182953 + 0cd743f (cycle 162): Mars frost tile set fix, FootingTests 86 columns 0 off (D-057), lamps carry a warm Point Light 2D; root cause of the dark lamp was unlit terrain (runtime tilemaps had no material), now ArtMaterials.lit + BaseTests assert; smoke_18 shows the lamp pool and smoke_3 shows night terrain darkening; check 23:16–23:35 green (EditMode 224/224, PlayMode 91/110 + LeadQA 10/10, BudgetGate green, Earth p99 13.67 ms).

### U-065 · UNITY · Done · M4
Goal: Thruster Mk2/Mk3 and Tank Mk2/Mk3 (Bible §4.3): 12 / 20 / 35 m/s² vertical, lateral 60%; launch allowed only where the table's "Can launch from" row says (Mk1: Mercury, Venus, Earth, Mars, Uranus; Mk2: + Saturn, Neptune; Mk3: + Jupiter); tanks 100/200/400; craftable ship upgrades in the RecipeBook; the HUD says "Thruster MkN can't lift off here" instead of a silent fail.
Accept: EditMode: launch permission table for all 8 planets × 3 marks; PlayMode: Mk1 refuses on Saturn with the HUD line, Mk2 lifts off Saturn; tank capacity follows the mark; save/load keeps the marks.
Files: Assets/_Game/Code/Runtime/Ship/, Items/, Tests/
Depends: U-010
Lead notes: Done 6e54f23 + e26a10b (cycle 153): check 20:58 compile 0/0, EditMode 223/223 (ShipMarksTests 5/5), ShipMarksPlayTests green (Mk1 refused on Saturn with the HUD line, Mk2 lifts off).

### U-066 · UNITY · Superseded · M4
Goal: Top-down ring and belt mining (Bible §3, §7.7): mining lanes in the asteroid Belt and Saturn's rings, density by distance with safe gaps; the ship's mining beam breaks ring ice / ring rock bodies (placeholder sprites until B-059) into water ice, silicates, iron; Ring Mites (placeholder) swarm a ship that mines for > 20 s and chew hull 1/s each until shot or outrun.
Accept: EditMode: lane density profile per seed with at least one gap; PlayMode: mine one ring body → cargo gains items; mites spawn after 20 s of mining and damage hull; Space scene budgets within §11.1.
Files: Assets/_Game/Code/Runtime/Space/Mining/, Tests/
Depends: U-034
Lead notes: Cycle 147. M4.

### U-067 · UNITY · Superseded · M4
Goal: Grapple Rig module (Bible §7.5 movement, §8 Rig table): fire at a floe/solid tile within 18 m, reel at 10 m/s, swing under gravity, release on jump; works on solid worlds too; no ammo; cooldown 0.5 s.
Accept: PlayMode on Earth: grapple to a ledge 12 m up and arrive; a shot at 25 m misses; under Jupiter gravity the reel still lifts the player; the HUD shows the reticle range.
Files: Assets/_Game/Code/Runtime/Player/Rig/, Tests/
Depends: U-049
Lead notes: Cycle 147. M4. Test on solid worlds now; the floe case joins once U-061 lands.

### U-068 · UNITY · Done · M4
Goal: Giant-world hazard bands (Bible §7.5–7.9) as data: per planet and per deck, hazard levels (Radiation, Cryo, Thermal, Pressure) read by the existing hazard system; Jupiter values from §7.6 (Radiation 3 above Deck 2, 1 below; Cryo 2 in Deck 1; Thermal 2 in Deep), Saturn/Uranus/Neptune from §7.7–7.9; a pure lookup HazardBands.For(planet, y) so it is testable before the column renders.
Accept: EditMode table tests for each giant at one y per band; suit meters show the band level when the player is placed at that y in a stub scene.
Files: Assets/_Game/Code/Runtime/Hazards/GiantBands.cs, Tests/
Depends: U-049
Lead notes: Done adb433e (cycle 153): GiantBandsTests 5 + GiantBandsPlayTests green in the 20:20 and 20:58 checks; numbers per D-055.

### U-069 · UNITY · Done · M4
Goal: Catalogue + recipes for M4 materials (Bible §7.6–7.9): metallic_hydrogen, ammonia_ice, phosphorus_pigment, ring_ice, ring_rock, methane_ice, deep_diamond, superionic_ice; float_cell_mk1/mk2 and jetpack_mk2/mk3 recipes (pick the numbers from §4.2 and the §7 gates; list them in your status for LEAD's D- entry); icons from B-061 (placeholders until it lands).
Accept: EditMode: every new item has a catalogue entry, an icon key, and at least one source (generator, drop, or recipe stub); RecipeBook loads with no duplicate ids.
Files: Assets/_Game/Code/Runtime/Items/, Data/, Tests/
Depends: U-051
Lead notes: Done adb06a3 + 7a413c1 (cycle 153): M4ItemsTests 5 green, RecipeBook reset; recipes per D-056; placeholder icons until B-061.

### U-070 · UNITY · Superseded · M4
Goal: Jupiter creatures v1 (Bible §7.6) on the U-055 creature framework, with placeholders until B-056: Stormglider (passive manta floater, drifts between floes), Lightning eel (Deck 2, charges 1.5 s then arcs 20 damage within 6 m), Belt wasp (Deck 1 swarm of 5–8, radiation-adapted, chases within 20 m), Ballast tortoise (huge slow floater; on death it becomes a standable floe for 120 s). Numbers you pick go in your status for LEAD's D- entry.
Accept: EditMode: spawn tables per deck; PlayMode in a stub column: eel arcs only after its tell; a killed tortoise is standable (feet within 0.1 m of its top); wasps give up past 40 m.
Files: Assets/_Game/Code/Runtime/Creatures/Jupiter/, Tests/
Depends: U-055
Lead notes: Cycle 153. M4. Build against a stub column now; switch to U-061's column when it lands.

### U-071 · UNITY · Superseded · M4
Goal: Aerostat platforms (Bible §7.5, Venus precedent in U-056): buildable on giants; each module lists mass and lift; the HUD shows the buoyancy margin; a platform with negative margin sinks 1 m/s until fixed; the respawn point after a Crush Line death is the last Aerostat (else the ship).
Accept: EditMode: margin = Σ lift − Σ mass per module set; PlayMode: overloading sinks, removing a module stops the sink; Crush respawn picks the Aerostat; save/load keeps the platform.
Files: Assets/_Game/Code/Runtime/Building/Aerostat/, Tests/
Depends: U-056
Lead notes: Cycle 153. M4. Reuse the Venus aerostat code; the Crush respawn hook joins once U-061 lands.

### U-078 · UNITY · Ready · R1
Goal: Planets as spheres in Space (Bible §10.5 v2): each planet disc becomes a sphere mesh with the equirect `planets/<name>/surface` texture, the atmosphere rim and cloud layer as a slightly larger translucent shell, the terminator from the real Sun direction, Saturn's rings as a flat ring mesh; the top-down orthographic camera, wells, belt and stations unchanged.
Accept: SpaceArtTests still resolve every planet key; a Space capture shows lit spheres with terminators and Saturn's rings; Space budgets within §11.1.
Files: Assets/_Game/Code/Runtime/Space/, Shaders/, Prefabs/Space/
Depends: U-072
Lead notes: Cycle 176. R1. Independent of the terrain work.

### U-079 · UNITY · Ready · R1
Goal: FX in 3D: thruster, landing dust, dig sparks, heat shimmer and the Escape band become camera-facing billboards or particle systems on the play plane using the existing `fx/*` sheets and keys; emissive FX feed bloom; nothing uses Light2D or sprite sorting layers.
Accept: FX keys resolve; a capture shows the thruster flame and dig sparks lit/emissive under the Universal renderer; 0 B GC per frame as before.
Files: Assets/_Game/Code/Runtime/FX/, Prefabs/FX/
Depends: U-072
Lead notes: Cycle 176. R1.

### U-080 · UNITY · Ready · R1
Goal: Review camera for depth: photo mode (`P`) gains an orbit of ±30° yaw and ±15° pitch around the player (mouse drag) and a "depth" preset used by `tools/unity_smoke.ps1` captures, so reviews can show the block relief, back wall and depth bands; gameplay camera unchanged.
Accept: a smoke capture named `*_depth.png` from the yaw preset; SideViewTests unaffected.
Files: Assets/_Game/Code/Runtime/Camera/, tools/unity_smoke.ps1
Depends: U-072
Lead notes: Cycle 176. R1. Small; it makes every later review honest about depth.

### U-025 · UNITY · Done · M2
Goal: Day/night lighting: sun Light2D angle and color follow TimeSystem (20 min Earth day, 20.5 min Mars), sunlight intensity from Bible §9 per planet, ambient night level, sky tint.
Accept: EditMode test: Earth noon/midnight intensities match §9; captures at dawn/noon/dusk/night on Earth; 0 B GC per frame.
Files: Assets/_Game/Code/Runtime/Planet/Lighting/
Depends: U-004
Lead notes: Done c56a516 (cycle 20): DayNightTests; dawn/noon/dusk/night captures (night: ship windows glow); values per D-030.

### U-026 · UNITY · Done · M2
Goal: Mars dust storm (Bible §7.2): 60 s warning, 2–6 min storm every 4–7 game days, visibility 15 m, Cryo +1, static discharges.
Accept: PlayMode test forces a storm: warning event 60 s before; fog shrinks visibility to 15 m; Cryo level rises by 1; storm ends inside 2–6 min; uses fx/dust when present.
Files: Assets/_Game/Code/Runtime/Planet/Weather/
Depends: U-025
Lead notes: Done 3b48dc7 + 4bbf8a0 (cycle 20): DustStorm tests; storm capture (15 m fog, dust puffs); BudgetGate storm leg avg 4.3 / p99 8.9 ms, first frame 2.8 ms.

### U-027 · UNITY · Done · M2
Goal: Creature AI v1: grazer (stag: wander, flee), pack hunter (wolf: night, chase), scavenger (dustskater), canyon hunter (scree stalker); spawns by biome and time; real gravity on bodies.
Accept: PlayMode tests: stag flees within 8 m, wolf packs spawn only at night, creatures never fall through streamed chunks; ≤ 0.5 ms AI per frame with 20 creatures; placeholders until B-015/B-016.
Files: Assets/_Game/Code/Runtime/Creatures/
Depends: U-009
Lead notes: Done 4bbf8a0 (cycle 20): stag/wolf/dustskater/scree stalker AI on placeholders, held on unloaded chunks, AI ≤ 0.13 ms with 20. Real art via B-015/B-016 + U-036.

### U-029 · UNITY · Done · M2
Goal: Hazard system v1 (Bible §7 0–3 scale) with Cryo first: per-planet/biome/time Cryo level (Earth tundra night 1; Mars day 1 / night 2; dust storm +1), suit integrity drain by level, HUD Cryo meter, warmth near a lit shelter or the ship.
Accept: EditMode tests for the level table; PlayMode: Mars night drains suit and the ship stops the drain; level 3 is lethal within 30 s unprotected (§7 definition); the HUD meter shows the level and drain.
Files: Assets/_Game/Code/Runtime/Hazards/, UI/
Depends: U-025
Lead notes: Done b1fb61e (cycle 26): numbers per D-032; clean profile perf_2026-10-31.md (load none) all green, Earth p99 10.5 ms, entry 1.30 s. The 18:51 RED was contention (D-033).

### U-030 · UNITY · Done · M2
Goal: POIs v1 on Earth and Mars: place the Survey Archive and the abandoned coastal launch complex (Earth), the crashed Halcyon hauler and the Warden outpost (Mars) as handmade stamps merged into the generated terrain at fixed longitudes; use B-020/B-021 props (placeholders until Done).
Accept: each POI appears at its longitude in every new world and survives dig/save/load (stamps write diffs once); a map marker for each; PlayMode test per planet.
Files: Assets/_Game/Code/Runtime/Planet/POI/, Assets/_Game/Prefabs/POI/
Depends: U-007, U-013
Lead notes: Done 3936ae1 (cycle 26): Archive at x 184 (buried room), launch complex, Halcyon hauler, Warden outpost as once-per-world stamps with B-020/B-021 props; PoiTests + PoiPlayTests. Visual check in the M2 playtest.

---

## BLENDER

> **R1 (D-062).** 2D tasks B-056..B-076 are Superseded; their `.blend` sources (rigs, props,
> terrain recipes) are the starting point for the models. Contract v2 §9 is the rule set.

### B-077 · BLENDER · Done · R1
Goal: Contract v2 pipeline test (the B-002 handshake again, in 3D): export the calibration figure as `characters/calibration/base.glb` with two clips (`idle`, `walk`), the four v2 maps, +X facing, feet at the origin; a stamped turntable contact sheet; a `render.py` export path for glb (`export_model(key)`); propose contract §9 changes you need in BLENDER_STATUS.
Accept: UNITY's ArtImporter v5 imports it with the clip names intact and the materials assigned (U-075 confirms); the turntable review is stamped.
Files: blender/scripts/build_calibration.py, blender/render.py, Assets/_Game/Art/characters/calibration/
Depends: —
Lead notes: Done 09c6f27 + f6108e4 (cycle 174): calibration glb imported by UNITY (e7dc190): clips and lengths kept, feet at y = 0, 984 tris, materials from the maps. Facing was mirrored by glTFast → D-065 (export facing glTF −X); re-export the calibration once under B-078's first turn.

### B-078 · BLENDER · Done · R1
Goal: The surveyor as a model: `characters/surveyor/base.glb`, ≤ 12 k triangles, 2048 textures, the full §5 clip set at 30 fps, a `float_pack` socket (empty) on the back and a `rig_tool` socket in the right hand; reuse the existing surveyor rig.
Accept: contract §9; clips loop where they should; stamped turntable; UNITY lit preview.
Files: blender/sources/characters/surveyor.blend, build_surveyor.py, Assets/_Game/Art/characters/surveyor/
Depends: B-077
Lead notes: Done 0f4193a + 929c588 (cycle 184): surveyor model, 9,228 tris, 10 clips, sockets; UNITY lit previews r1_models_2026-11-02 (chain 5) checked: lit PBR, faces screen right, emissive where expected.

### B-079 · BLENDER · Done · R1
Goal: The Pilgrim as a model: `ships/pilgrim/base.glb` (12 m long), ≤ 15 k triangles, emissive engines and windows, landing gear, a `cockpit` socket, `LOD1`; a top-down `top` is no longer separate (the same model is viewed from above in Space).
Accept: contract §9; stamped turntable; the landing-gear footprint matches the current landing_pad width.
Files: blender/sources/ships/pilgrim.blend, build_pilgrim.py, Assets/_Game/Art/ships/pilgrim/
Depends: B-077
Lead notes: Done 623b166 (cycle 184): Pilgrim 8,220 tris + LOD1, four legs; UNITY lit previews r1_models_2026-11-02 (chain 5) checked: lit PBR, faces screen right, emissive where expected.

### B-080 · BLENDER · Done · R1
Goal: Earth terrain block materials (contract §9 terrain row): for every Earth tile material in `EarthTileSet` (soil, grass-topped soil, stone, sand, clay, snow, ice, ores, wood…: list them from the tile set and log the list), a tileable `top` and `side` PBR set at 512², 2 m per repeat, plus `backwall`; derived from the v1 tile recipes.
Accept: tiles seamlessly (2× tiled preview); reads as the v1 materials under the Earth Sun in the UNITY lit preview; stamped contact sheet of all sets.
Files: blender/scripts/gen_terrain.py, Assets/_Game/Art/terrain/earth/
Depends: B-077
Lead notes: Done 2eb6213 (cycle 181): the six Earth block material sets + backwall; UNITY's lit captures earth_blocks_b080(_depth).png (105bffa) show soil, grass and stone textured with relief, grass tops, the D-067 fringe and the back wall.

### B-081 · BLENDER · Done · R1
Goal: Earth props batch 1 as models: `props/common/{landing_pad, shelter_wall, shelter_door, smelter, storage_crate, lamp}` (+ `fabricator`, `refinery` if they exist as sprites), each ≤ 6 k triangles, lamp with an emissive head and a `light` socket, door with an `open` clip.
Accept: contract §9; stamped turntable sheet; wall and pad tile at 1 m / 2 m pitches.
Files: blender/sources/props/common/, build_props_common.py, Assets/_Game/Art/props/common/
Depends: B-077
Lead notes: Done fbf6b7a (cycle 184): props batch 1 as models (2 m pad module, 1 m wall, door clip, lamp socket_light, smelter grate emissive); UNITY lit previews r1_models_2026-11-02 (chain 5) checked: lit PBR, faces screen right, emissive where expected.

### B-082 · BLENDER · Done · R1
Goal: Earth creatures as models: `creatures/earth/stag` and `creatures/earth/wolf`, medium class (≤ 8 k triangles), full walker clip set, reusing the v1 rigs.
Accept: contract §9; stamped turntables; UNITY lit preview at 60 px/m reads as the v1 silhouettes.
Files: blender/sources/creatures/earth/, build_creatures_earth.py, Assets/_Game/Art/creatures/earth/
Depends: B-077
Lead notes: Done e6abeef (cycle 184): stag + wolf 7,600 tris, 16-joint skins, 5 clips; UNITY lit previews r1_models_2026-11-02 (chain 5) checked: lit PBR, faces screen right, emissive where expected.


### B-024 · BLENDER · Done · M2
Goal: HeavyJobLock fairness + memory gate in `tools/blender_render.ps1` (D-026), mirroring U-023.
Accept: writes `want_blender.lock` while waiting, deletes it on acquire; yields to a fresh `want_unity.lock` after its own job; refuses below 1.5 GB free RAM; one job ≤ 20 min (split `all` exports by category).
Files: tools/blender_render.ps1
Depends: —
Lead notes: Done f7bffce (cycle 24): want_blender.lock while waiting, yield, memory gate.


### B-001 · BLENDER · Done · M0
Goal: Pipeline skeleton: `blender/` tree, `manifest.json` schema, `render.py` CLI (`--asset`, `--category`, `--all`, `--preview`), `tools/blender_render.ps1`, logging, memory settings per contract §3.
Accept: `tools/blender_render.ps1 all` on an empty manifest exits 0; an unknown key exits non-zero with a one-line reason; a line per asset in `logs/blender_<date>.log`.
Files: blender/render.py, blender/manifest.json, blender/scripts/, tools/blender_render.ps1
Depends: L-005
Lead notes: Done 4dd7922/5d630d4 (cycle 4): unknown key → FAIL line + non-zero; 11 assets logged one line each. Empty-manifest run not retained in logs; accepted on the populated-manifest runs.

### B-002 · BLENDER · Done · M0
Goal: Calibration asset `props/common/calibration`.
Accept: 1 m sphere on a 1 m cube with known flat colors; color, normal, emission, mask exported per contract §2; contact sheet shows the upper-right of the sphere lit when the light is upper-right; 8 px dilation visible; sizes logged.
Files: blender/sources/props/calibration.blend, Assets/_Game/Art/props/common/calibration_*.png
Depends: B-001
Lead notes: Done ead95f6 (cycle 6): calibration handshake complete (import clean, placeholder retired, lit preview upper-right). Emission display tracked in U-019.

### B-003 · BLENDER · Done · M2
Goal: Earth top-down: `planets/earth/surface` (2048×1024), `clouds` (1024×512), `glow` (512).
Accept: contract §4 sizes; public-domain source imagery logged in `docs/credits/blender.md`; preview wraps without a seam.
Files: blender/sources/planets/earth.blend, Assets/_Game/Art/planets/earth/
Depends: B-002
Lead notes: Done (cycle 6): contact sheets, contract sizes, LFS, credits OK; lit previews OK (U-006). Glow display depends on U-019, not on this art.

### B-004 · BLENDER · Done · M2
Goal: Mars top-down: `planets/mars/surface`, `glow`.
Accept: as B-003.
Files: Assets/_Game/Art/planets/mars/
Depends: B-002
Lead notes: Done (cycle 6): contact sheets, contract sizes, LFS, credits OK; lit previews OK (U-006). Glow display depends on U-019, not on this art.

### B-005 · BLENDER · Done · M2
Goal: Sun and space backgrounds: `planets/sun/surface` + `glow` (emission), `backgrounds/space/layer0..2`.
Accept: Sun emission map present; three 2048×1024 star layers tileable in x, with a Milky Way band on layer0.
Files: Assets/_Game/Art/planets/sun/, Assets/_Game/Art/backgrounds/space/
Depends: B-002
Lead notes: Done (cycle 6): contact sheets, contract sizes, LFS, credits OK; lit previews OK (U-006). Glow display depends on U-019, not on this art.

### B-006 · BLENDER · Done · M2
Goal: Starter ship **Pilgrim**: `ships/pilgrim/top` and `side`.
Accept: top ≤ 448×448 (see UNITY handoff), side ≤ 1536×512; color, normal, emission; thrusters and windows glow; industrial-worn look per Bible §9.
Files: blender/sources/ships/pilgrim.blend, Assets/_Game/Art/ships/pilgrim/
Depends: B-002
Lead notes: Done (cycle 6): contact sheets, contract sizes, LFS, credits OK; lit previews OK (U-006). Glow display depends on U-019, not on this art.

### B-007 · BLENDER · Done · M2
Goal: Earth terrain sets: `terrain/earth/{soil,grass,stone,sand,snow,water}`.
Accept: six 47-tile RuleTile sets, 128 px tiles, 8 columns, color + normal, 2× tile check passes.
Files: blender/sources/terrain/earth.blend, Assets/_Game/Art/terrain/earth/
Depends: B-002
Lead notes: Done (cycle 6): 47-blob sheets join seamlessly in the demos; LFS OK. Follow-ups (variants, grass on upward edges only) are B-022, not a reopen.

### B-008 · BLENDER · Done · M2
Goal: Mars terrain sets: `terrain/mars/{regolith,basalt,hematite,ice}`.
Accept: as B-007.
Files: Assets/_Game/Art/terrain/mars/
Depends: B-007
Lead notes: Done (cycle 6): 47-blob sheets join seamlessly in the demos; LFS OK. Follow-ups (variants, grass on upward edges only) are B-022, not a reopen.

### B-009 · BLENDER · Done · M2
Goal: Player character `characters/surveyor` frame sheet.
Accept: 256 px frames, standard character set ≤ 48 frames, color + normal + emission (visor, lamp), `.json` manifest, bottom-center pivot, right-facing.
Files: blender/sources/characters/surveyor.blend, Assets/_Game/Art/characters/surveyor/
Depends: B-002
Lead notes: Done 489a964 (cycle 7): key, 7-column sheet within 2048, 46 frames / 10 clips, color+normal+emission, LFS. Polish scheduled as B-023.

### B-010 · BLENDER · Done · M2
Goal: Earth parallax `backgrounds/earth/layer0..2` (temperate biome).
Accept: three 2048×1024 layers tileable in x; haze gradient readable; palette per Bible §9.
Files: Assets/_Game/Art/backgrounds/earth/
Depends: B-002
Lead notes: Done 6c6541d + 8efa54f (cycle 13): rendered 3D trees, ground clumps, sun-lit; passes the §9 cartoon rule. Polish items → B-025.

### B-011 · BLENDER · Done · M2
Goal: Mars parallax `backgrounds/mars/layer0..2`.
Accept: as B-010 with the Mars palette and butterscotch sky.
Files: Assets/_Game/Art/backgrounds/mars/
Depends: B-010
Lead notes: Done 8efa54f (cycle 13): rendered rocks, mesas, dunes, haze; split-half renders with no visible stitch. Mid-layer streak band → B-025.

### B-022 · BLENDER · Done · M2
Goal: Terrain sheet revision for all 10 materials: fill slots 47–62 with 16 variants of tile 46; grass rim only on upward-facing exposed edges (sides/underside show soil with a darker rim) (D-020).
Accept: contact sheets + demo patches show no visible 128 px repetition on a 16×8 interior block; grass demo shows no grass on cave ceilings or vertical walls; tiles 0–46 still join seamlessly; same file names, so no Unity change is needed beyond U-020.
Files: blender/scripts/gen_terrain.py, Assets/_Game/Art/terrain/
Depends: B-007, B-008
Lead notes: Done fb0c1dc (cycle 8): grass rim only on upward edges; 16 interior variants per sheet; joins seamless in demos.

### B-019 · BLENDER · Done · M2
Goal: Pilgrim landing legs: `ships/pilgrim/side_legs` (same framing, pivot, and size as `side`, with legs extended below the skids).
Accept: identical canvas and pivot to `side` so UNITY can swap without offset (diff of the two pivots = 0); legs read clearly at camera size 9; color, normal, emission.
Files: Assets/_Game/Art/ships/pilgrim/, blender/scripts/
Depends: B-006
Lead notes: Done f1eb426 (cycle 12): side = gear retracted into the pods, side_legs = skids deployed, identical canvas and pivot (D-025).

### B-023 · BLENDER · Done · M2
Goal: Surveyor v2 polish: replace primitive suit parts with a sculpted soft suit (fabric folds at joints, seams, chest unit, backpack straps), visor with reflection and emission readouts; fix the death end pose (legs grounded).
Accept: same key, sheet layout, frame count, clips, and pivot as v1 (UNITY needs no change); contact sheet reads as a real suited person at 60 px/m, not a mannequin (§9); lit preview via tools/unity_art_preview.ps1.
Files: blender/scripts/build_surveyor.py, blender/sources/characters/surveyor.blend, Assets/_Game/Art/characters/surveyor/
Depends: B-009
Lead notes: Done f095302 (cycle 15): soft suit, chest unit, harness, hard helmet, visor emission, mask map, flat death pose; same layout. Accepted as v2; no further polish unless the playtest asks.

### B-025 · BLENDER · Done · M2
Goal: Parallax polish from the cycle-13 review of the 3D backgrounds.
Accept: Earth: foliage reads as leaf masses, not stacked spheres (denser, smaller leaf-card clusters with silhouette breakup); clouds are soft volumetric or painted-haze shapes, not opaque white blobs, and never overlap the near tree line. Mars: no vertical spike/streak band in the mid layer (layer1 ground); at least 3 boulder shape families with varied scale. Same keys, sizes, tiling, and memory plan (D-028).
Files: blender/scripts/gen_backdrop3d.py, Assets/_Game/Art/backgrounds/{earth,mars}/
Depends: B-010, B-011
Lead notes: Done 4b09174 + layer2 re-export (cycle 28): leaf-card foliage, soft high clouds above a lowered tree line, Mars relief from a 2D field (no streaks), 4 boulder families. Distant peak slightly spiky (minor).

### B-026 · BLENDER · Done · M2
Goal: Earth biome parallax variants: `backgrounds/earth_desert/layer0..2`, `backgrounds/earth_taiga/layer0..2`, `backgrounds/earth_coast/layer0..2` (Bible §7.1 biomes), same rendered-3D approach as B-010 rework.
Accept: same sizes/tiling as backgrounds/earth; §9 (no flat fills, haze by distance); split-half renders within D-028 memory; stacked preview per biome.
Files: blender/scripts/gen_backdrop3d.py, Assets/_Game/Art/backgrounds/earth_*/
Depends: B-010
Lead notes: Done (cycle 53): desert (cb33653, circle-mapped noise), taiga (1b0178b), coast (shore skirt, 2D beach relief, turquoise-to-deep-blue sea with glitter and surf line). All stamped fresh; seams ≤ 1.26.

### B-027 · BLENDER · Done · M3
Goal: Mercury terrain sets `terrain/mercury/{regolith,basalt,sulfide,ice}` (47-blob + 16 variants, D-020) and parallax `backgrounds/mercury/layer0..2` (black sky, huge Sun glow, crater rims, violet twilight per §7.3).
Accept: contract §4 sizes; terrain joins seamlessly (demo patches); backdrop per §9 and Mercury palette (white/black/violet); split-half renders.
Files: blender/scripts/gen_terrain.py, gen_backdrop3d.py, Assets/_Game/Art/terrain/mercury/, backgrounds/mercury/
Depends: B-022
Lead notes: Done 2ee2cc4 + backdrop (cycle 57): Mercury terrain (regolith, basalt, sulfide, polar ice); backdrop with black sky, huge Sun + corona, violet twilight, cratered skyline. Integration note for M3: the Sun is baked into the tiling layer0, so two Suns could show if one tile is narrower than the view. Before Venus/Mercury integration, BLENDER provides a sun-less layer0 variant and UNITY draws the Sun as its own sprite (planets/sun/glow) at a fixed sky position.

### B-028 · BLENDER · Done · M3
Goal: Venus art: terrain sets `terrain/venus/{basalt,tessera,vent_glass,sulfur}` (47-blob + 16 variants) for the surface, and parallax `backgrounds/venus_deck/layer0..2` (habitable cloud deck: orange-cream haze, backlit cloud towers) plus `backgrounds/venus_surface/layer0..2` (black glassy plains lit by vents) per §7.4 and §9.
Accept: contract sizes; terrain joins seamlessly; backdrops rendered 3D (no flat fills), haze by distance; split-half renders at the 1.5 GB gate.
Files: blender/scripts/gen_terrain.py, gen_backdrop3d.py, Assets/_Game/Art/terrain/venus/, backgrounds/venus_*/
Depends: B-022
Lead notes: Done (cycle 56): 4 terrain sets (basalt, tessera, violet vent glass, ochre sulfur); venus_surface (haze, boulders, vents); venus_deck via painted 2D cumulus after 3 heightfield strikes. Polish (deck arcs, vent legibility) → B-034.

### B-029 · BLENDER · Done · M3
Goal: Mercury creatures `creatures/mercury/glassback` (silicate grazer, medium) and `creatures/mercury/cinderling` (small swarm), same clip set as B-015.
Accept: the B-015 rework method (one continuous armature-deformed mesh, real-feeling anatomy with one exaggeration: glassback's crystalline back plates, cinderling's glowing cracks with emission); 320 px / 6 columns for medium, 128–256 px for small; ppu ≥ 100.
Files: blender/scripts/build_creatures_mercury.py, Assets/_Game/Art/creatures/mercury/
Depends: B-015
Lead notes: Done f16d2ce (cycle 58): glassback (132.25 px/m, lilac glass-shard crest) and cinderling (150 px/m, glowing crack emission); metaball method.

### B-030 · BLENDER · Done · M2
Goal: Re-render `fx/heat_shimmer` as a visible heat-haze/entry-glow sheet (orange-white plasma streaks, additive), per UNITY's handoff (the current sheet is a near-transparent pale mask).
Accept: same key and frame layout; reads clearly over a dark sky at camera size 9; emission map present.
Files: blender/scripts/gen_fx.py, Assets/_Game/Art/fx/heat_shimmer/
Depends: B-012
Lead notes: Done (cycle 45): white-hot bow-shock arc + plasma streaks, 8-frame loop, new base_emission.png; reads clearly over a dark sky. UNITY to switch the entry glow from tinted-unlit to the emissive sheet.

### B-031 · BLENDER · Done · M2
Goal: Wolf silhouette polish (from the B-015 v3 review): heavy neck ruff and fur-clump outline along the back (§9 "one exaggeration" for the wolf), bushy tail (2–3× current thickness, tapering), larger upright ears, legs ~25% thicker at the upper leg, shorter snout.
Accept: same key, sheet layout, clips, and pivot as B-015 v3; full-size frames read as a wolf, not a hyena/rodent, next to the stag; ppu ≥ 100.
Files: blender/scripts/build_creatures_earth.py, Assets/_Game/Art/creatures/earth/
Depends: B-015
Lead notes: Done (cycle 43): brush tail, heavy ruff, back fur clumps, tapered upright ears (3-segment metaballs), thicker upper legs, shorter snout; 128.5 px/m; feet on pivot in every checked frame. Reads as a wolf.

### B-032 · BLENDER · Done · M3
Goal: Venus creatures (Bible §7.4): `creatures/venus/sulfur_drifter` (gasbag filter feeder, large, floats; 320–512 px class per D-034 rules) and `creatures/venus/acidmoth` (small swarm flyer, 128 px), standard clip set (fliers: idle/drift, move, attack, hurt, death).
Accept: metaball method (B-015 standard); one bold exaggeration each (drifter: translucent gas sacs with emission veins; acidmoth: acid-yellow wing eyespots with emission); Venus palette (orange-cream, sulfur yellow); ppu ≥ 100; full-size frames reviewed.
Files: blender/scripts/build_creatures_venus.py, Assets/_Game/Art/creatures/venus/
Depends: B-015
Lead notes: Done (cycle 59): sulfur drifter (117 px/m, translucent sac + emissive vein network, gondola, filter tendrils) and acidmoth (250 px/m, emissive eyespots); fliers use a centred pivot (0.5, 0.5); flier builder added.

### B-033 · BLENDER · Done · M3
Goal: Mercury POI props (Bible §7.3): `props/mercury/{flare_shelter,shelter_door,meridian_beacon,warden_vault_gate,solarite_cluster}`; solarite_cluster has emission (crystals fused by flares).
Accept: contract §4 prop rules; Mercury palette (white/black/violet), harsh light-ready normals; worn, flare-scorched metal.
Files: blender/scripts/build_props_mercury.py, Assets/_Game/Art/props/mercury/
Depends: B-014
Lead notes: Done (cycle 58): flare shelter, shelter door, Meridian beacon, Warden vault gate (violet emission strips), solarite cluster; all 4 maps. The dark bar across the shelter doorway → B-034.

### B-034 · BLENDER · Done · M3
Goal: Venus backdrop polish (from the B-028 review), for the M3 exit: remove the faint sphere-edge arcs inside the near deck bank; on venus_surface make the vents read (larger glowing vent mouths with soft emission halos and rising heat haze, 4–6 per tile) and add glassy sheen to the basalt plain (§7.4 "black glassy surface lit by vents").
Accept: stamped reviews show no arcs; vents are legible at camera size 9; same keys, sizes, seams.
Files: blender/scripts/gen_backdrop*.py, Assets/_Game/Art/backgrounds/venus_*/
Depends: B-028
Lead notes: Done (cycle 66): Venus deck arcs reduced, legible vents with halos, glassy basalt; mercury/layer0_nosun; flarewing body ×2 + gradient flare shell; pressure crab wide/flat with splayed legs (now 320 px frames, 114.25 px/m, so UNITY re-imports its metas). Heat shimmer over vents would be a Unity shader (M3, optional).

### B-035 · BLENDER · Done · M3
Goal: Mercury creatures 2 (Bible §7.3): `creatures/mercury/flarewing` (flyer that feeds on flares; emission on the wing membranes, brighter "flare" variant frames in attack) and `creatures/mercury/shadewyrm` (ice burrower of the polar craters; long segmented body, pale frost plates).
Accept: B-015 metaball standard (flier builder from B-032 for flarewing); one bold exaggeration each; ppu ≥ 100; stamped full-size review.
Files: blender/scripts/build_creatures_mercury.py, Assets/_Game/Art/creatures/mercury/
Depends: B-029, B-032
Lead notes: Done (cycle 62): flarewing (131.25 px/m, veined emissive membranes, flare shell on attack frames) and shadewyrm (110.75 px/m, 8-segment chain, frost plates, cyan eyes). Flarewing body thickness and flare-shell flatness → B-034.

### B-036 · BLENDER · Done · M3
Goal: Venus surface creatures (Bible §7.4): `creatures/venus/pressure_crab` (armored, slow; heavy plated carapace) and `creatures/venus/vent_eel` (heat-seeking surface eel; glowing heat pits with emission).
Accept: B-015 standard; Venus surface palette (black glass, orange glow); ppu ≥ 100; stamped review.
Files: blender/scripts/build_creatures_venus.py, Assets/_Game/Art/creatures/venus/
Depends: B-032
Lead notes: Done (cycle 63): pressure crab (102.25 px/m, black-glass plates with an emissive under-body, pincers, eye stalks) and vent eel (125.75 px/m, 10 segments, glowing heat pits). Crab silhouette reads beetle-like → B-034.

### B-037 · BLENDER · Done · M3
Goal: Rig modules (Bible §6/§8): held-tool sprites `items/rig/{beam,lance,survey,builder}` (drawn in the surveyor's hand, aim pivot at the grip) + FX sheets `fx/beam_ray`, `fx/lance_bolt`, `fx/survey_scan` (expanding ring), `fx/builder_ghost` (placement preview).
Accept: tools readable at 60 px/m at the surveyor's scale; grip pivot documented for UNITY; FX with emission; stamped review.
Files: blender/scripts/build_rig.py, gen_fx.py, Assets/_Game/Art/items/rig/, Assets/_Game/Art/fx/
Depends: B-012, B-023
Lead notes: Done (cycle 60): beam/lance/survey/builder tools (128×64, grip pivot [0.375, 0.5]), FX beam_ray, lance_bolt, survey_scan, builder_ghost; keys under props/rig (D-041). Integration → U-046.

### B-038 · BLENDER · Done · M3
Goal: Waystations (Bible §3): top-down `ships/waystation_earth/top` and `ships/waystation_mars/top` (orbital stations, large-ship class ≤ 768 px, docking ring with emission lights), plus a side-view docking-bay interior backdrop `backgrounds/waystation/layer0..2`.
Accept: Halcyon Freight industrial look (worn, hazard markings, lit windows); stamped review; contract sizes.
Files: blender/scripts/build_waystation.py, Assets/_Game/Art/ships/, backgrounds/waystation/
Depends: B-006
Lead notes: Done a9322d9 + bay (cycle 61): Earth and Mars Waystations top-down (768 px at PPU 36, lit ring windows, docking arms with guide lights). The painted 2D docking bay is a placeholder (too graphic for §9); the rendered pass → B-039.

### B-039 · BLENDER · Done · M3
Goal: Docking-bay backdrop, rendered 3D pass: replace the 2D-painted `backgrounds/waystation/layer0..2` (B-038) with rendered 3D (lit I-beams, truss, crane, worn plated deck, Halcyon crates with bevels, scuffs, and stencils; window onto stars with interior reflections), matching §9's rendered-realism style.
Accept: same keys, sizes, tiling; no flat-filled shapes; stamped review; split-half renders within the 1.5 GB gate.
Files: blender/scripts/gen_backdrop3d.py (bay preset), Assets/_Game/Art/backgrounds/waystation/
Depends: B-038
Lead notes: Done (cycle 64): rendered 3D bay with linked ±W copies (geometry, shadows, textures wrap); bevelled grimy panels, star window, I-beams, crane, Halcyon crates; replaces the painted placeholder.

### B-040 · BLENDER · Done · M3
Goal: Mercury apex `creatures/mercury/cinderhulk` (Bible §7.3): an armored colossus, large class (512 px frames per contract, sheet ≤ 2048), with a white-glowing shell on the day side and a "cooled & cracked" variant clip set (dark shell with glowing fracture lines) for the 2 min after it crosses into night, when it's vulnerable.
Accept: metaball standard; two shell states readable at 60 px/m; emission maps for both; stamped review.
Files: blender/scripts/build_creatures_mercury.py, Assets/_Game/Art/creatures/mercury/
Depends: B-029
Lead notes: Done v2 (cycle 70): irregular shingled dome edge, lower heavy stance, clawed jointed legs, tusked head below the dome; day + night sheets, 400 px × 5 (D-042), 102.25 px/m. Remaining polish (head and tail-mace readability at side view) is deferred to the M3 apex fight tuning, when the fight shows what needs to read.

### B-041 · BLENDER · Done · M3
Goal: Envirosuit tiers for the surveyor: `characters/surveyor/{mk1,mk2,mk3}` variants of the B-023 sheet (same layout, clips, pivot), with visible upgrades: Mk1 thermal/cryo pads, Mk2 armored plating + pressure collar, Mk3 full hard-shell with emissive visor bands.
Accept: identical frame layout to base (UNITY swaps the sheet); each tier distinct at 60 px/m; stamped review.
Files: blender/scripts/build_surveyor.py, Assets/_Game/Art/characters/surveyor/
Depends: B-023
Lead notes: Done (cycle 69): surveyor mk1 (gold foil pads), mk2 (gunmetal plates + pressure collar), mk3 (white hard shell, larger helmet); identical layout to base. Mk3 emissive bands faint at 60 px/m (acceptable; optional boost later).

### B-042 · BLENDER · Done · M3
Goal: Icons batch 2 (M3 resources and crafting, Bible §7/§8): solarite, vitriol_glass, sulfur, basalt, nickel, graphite, polar_ice, deep_core_sample, launch_fuel_cell, suit_patch, cryo_pad, thermal_pad, radiation_liner, smelter_bar_iron, smelter_bar_copper, circuit_board (16 icons, same icon camera and lights as B-013).
Accept: readable at 32 px; same style as batch 1 (the montage shows both batches side by side); stamped review.
Files: blender/scripts/build_icons.py, Assets/_Game/Art/icons/
Depends: B-013
Lead notes: Done (cycle 71): 15 icons (nickel already existed in batch 1, so no duplicate); readable at 32 px on a dark UI; consistent with batch 1.

### B-043 · BLENDER · Done · M3
Goal: Wardens basic tier (Bible §2, §8): `creatures/warden/sentinel` (hovering autonomous drone, centred pivot, flier clip set) and `creatures/warden/sentinel_shot` FX (fx/warden_bolt). Original design: an engineered-but-organic hybrid (Sowing era), a lens eye with emission, and no resemblance to any existing game's drones.
Accept: reads as a machine-guardian at 60 px/m; attack frames show the lens charging; emission maps; stamped review.
Files: blender/scripts/build_wardens.py, Assets/_Game/Art/creatures/warden/, fx/warden_bolt/
Depends: B-032
Lead notes: Done (cycle 72): sentinel (seed-pod ceramic hull, glowing verdigris seams, teal iris lens that charges white-hot in attack, root tendrils) + fx/warden_bolt; original design. Atlas → common (D-043). Seams still read slightly banded (minor; revisit with Warden tiers).

### B-044 · BLENDER · Done · M3
Goal: Venus apex `creatures/venus/veil_serpent` (Bible §7.4): a long ribbon serpent of the acid haze; 400 px × 5 frames (D-042); translucent fins with sulfur-yellow emission; a "chilled" hurt state (frost-white flash when hit by Cryo rounds).
Accept: reads as huge and graceful (S-curves in idle and move); a segmented chain rig like the shadewyrm; stamped review.
Files: blender/scripts/build_creatures_venus.py, Assets/_Game/Art/creatures/venus/
Depends: B-035
Lead notes: Done v2 (cycle 75): horned wedge head with glowing eyes and jaw, banded body with pale belly, veined dorsal sail + ventral fin, frost flash on hurt; 103 px/m. Thin rays and fin overlap deferred to M3 apex-fight tuning.

### B-045 · BLENDER · Done · M3
Goal: Venus Aerostat and station props (Bible §7.4): `props/venus/{aerostat_deck,aerostat_balloon,buoyancy_cell,station_hull_a,station_hull_b,meridian_station_door,vent_harvester}` with emission on lights; the balloon is translucent cream with rigging.
Accept: contract §4 prop rules (props ≤ 512; the balloon may use the large-ship 768 cap if needed, noted in the manifest); Venus palette; stamped review.
Files: blender/scripts/build_props_venus.py, Assets/_Game/Art/props/venus/
Depends: B-014
Lead notes: Done (cycle 76): aerostat deck, balloon (ppu 88, under the 512 cap), buoyancy cell, two station hulls, Meridian station door (Sowing-era arch matching the Wardens), vent harvester; all 4 maps.

### B-046 · BLENDER · Done · M2
Goal: Title-screen key art `ui/title/background` (1920×1080, color only): the Pilgrim lifting off the Earth spawn pad at dawn, the forest backdrop behind, Mars a small rust dot in the sky; leave the left third calm for the menu buttons. Also `ui/title/logo` (MERIDIAN wordmark, original, OFL font or hand-built letterforms, with transparency).
Accept: rendered in the game's own style from existing assets (B-006, B-010, B-014); no third-party logos or fonts outside OFL (credit in docs/credits/blender.md); stamped review at 1920 and 960 wide.
Files: blender/scripts/build_title.py, Assets/_Game/Art/ui/title/
Depends: B-006, B-010
Lead notes: Done v2 (cycle 80): dawn-graded forest, real landing pad on a soil strip, darkened left third, original hand-built MERIDIAN wordmark. build_title.py peaks ~1.03 GB, so it uses the 1.5 GB gate (not D-045).

### B-047 · BLENDER · Done · M6
Goal: Windows app icon `ui/app/icon` (256×256 with 16/32/48 px variants readable): the Pilgrim's silhouette over a rust-and-blue planet arc.
Accept: legible at 16 px; stamped review of all sizes.
Files: blender/scripts/build_title.py, Assets/_Game/Art/ui/app/
Depends: B-046
Lead notes: Done (cycle 80): Pilgrim silhouette over a rust-to-blue arc; 256/48/32/16 readable.

### B-048 · BLENDER · Done · M4
Goal: M4 risk-reduction look-dev, Jupiter cloud column only (Bible §7.5/§7.6): `backgrounds/jupiter_deck1/layer0..2` (ammonia-ice cloud tops: cream/rust/brick bands rolling past, thin sky above) and `terrain/jupiter/{floe_ice,floe_core}` (floating ice-floe tile sets, 47-blob + variants).
Accept: §9 look (no flat fills; band layers that read as moving cloud), tiling and contract sizes, stamped review. Only this one planet. The other giants wait until UNITY's cloud-column generator exists.
Files: blender/scripts/gen_backdrop*.py, gen_terrain.py, Assets/_Game/Art/backgrounds/jupiter_deck1/, terrain/jupiter/
Depends: B-028
Lead notes: Done (cycle 81): Jupiter deck-1 cloud tops (belts by absolute height, zonal streaks, thin starry sky) + floe_ice/floe_core terrain. Proves the cloud-column look. Further giant art waits for UNITY's cloud-column generator (M4).

### B-049 · BLENDER · Done · M3
Goal: Valles Marineris backdrop set `backgrounds/mars_canyon/layer0..2`: the view from the canyon floor, with the opposite canyon walls as terraced, layered cliffs (basalt with hematite bands, talus aprons) receding in dusty haze, butterscotch sky only in the top ~20%, and a near layer of fallen blocks and dune streaks on the floor.
Accept: same sizes and tiling as backgrounds/mars, rendered 3D (§9, no flat fills), haze by distance, stamped review; reads clearly as "inside a deep canyon".
Files: blender/scripts/gen_backdrop3d.py, Assets/_Game/Art/backgrounds/mars_canyon/
Depends: B-011
Lead notes: Done (cycle 101): continuous strata-banded canyon wall with talus, hazed far rim, near fallen blocks and dunes; sky ~27% (fine at in-game framing). UNITY hooks it to the canyon-floor trigger. (Cycle 104) Reopened for a layer0 fix: pinched spike and sliver at x ≈ 1550–1640 and stepped gaps read as hanging shapes in game; make the far rim one continuous wall. (Cycle 105) Far rim fixed: one continuous banded wall, no spikes; done.

### B-050 · BLENDER · Done · M3
Goal: Mercury far ridges: backgrounds/mercury layer0/layer0_nosun (and layer1 if affected) show a comb of vertical spikes along the crater skyline in game (coordination/reports/unity/u048_2026-10-31/capture_mercury_1_day.png, _2_twilight.png). Same cause as the canyon rim (terraced high-frequency ridge): use the ridge_lo approach so the rims are rounded crater walls, not spikes.
Accept: same keys, sizes, tiling; stamped review; no vertical spike combs.
Files: blender/scripts/gen_backdrop3d.py, Assets/_Game/Art/backgrounds/mercury/
Depends: B-027
Lead notes: Done (cycle 112): mercury layer0 + layer0_nosun re-rendered with ridge_lo=180, rounded crater rims, no spike comb; in-game confirmation via the U-057 re-capture.

### B-051 · BLENDER · Done · M3
Goal: Icons for crafted items still missing art: polymer, float_cell_mk1, solarite_capacitor (if absent), plus any other RecipeBook output without an icons/<key>/base (check UNITY's ItemRegistry/RecipeBook).
Accept: same icon camera and lights as B-013/B-042; readable at 32 px on a dark UI; stamped review.
Files: blender/scripts/build_icons.py, Assets/_Game/Art/icons/
Depends: B-042
Lead notes: Done (cycle 122): 7 icons (polymer, float cell, solarite capacitor, survey module, skip drive Mk2, deep-diamond tip, thruster Mk3), consistent with batches 1–2, readable at 32 px. 128 px icon renders count as below preview size (not heavy, CLAUDE.md rule 6).

### B-052 · BLENDER · Done · M3
Goal: (1) fx/warden_bolt reads too small at gameplay zoom: a bigger, brighter teal head (≈ 2× size) with a short glowing trail; same key and pivot rule. (2) backgrounds/mars layer0 far ridges show the same vertical spike comb as Mercury did (coordination/reports/unity/u053_2026-10-31/warden_outpost.png, top-left/right): re-render with the ridge_lo approach (rounded far rims). Check backgrounds/earth layer0's distant range for the same artifact and fix it if present.
Accept: stamped reviews; same keys, sizes, tiling; the bolt is readable at 60 px/m over a busy Mars backdrop.
Files: blender/scripts/gen_fx.py, gen_backdrop3d.py, Assets/_Game/Art/fx/warden_bolt/, backgrounds/mars/, backgrounds/earth/
Depends: B-043, B-050
Lead notes: Done (cycle 128): bigger and brighter warden bolt within 128×32 (enough, no resize); Mars layer0 rolling far hills (ridge_lo 200); Earth layer0 snowy peak without the comb (ridge_lo 80). UNITY re-imports.

### B-053 · BLENDER · Done · M3
Goal: Audit the far ridges of accepted backdrops for the spike comb (same generator as B-050/B-052): backgrounds/earth_desert, earth_taiga, earth_coast, venus_surface layer0 (and the jupiter_deck1 far layer if it uses ridges). Re-render only the layers that show it, with ridge_lo (keep peaks where the art needs them).
Accept: a stamped before/after review per changed layer; same keys, sizes, tiling; unchanged layers listed as "checked, no comb".
Files: blender/scripts/gen_backdrop3d.py, Assets/_Game/Art/backgrounds/
Depends: B-052
Lead notes: Cycle 129. BLENDER's offer, accepted; it reopens no accepted art except for this visible artifact. (Cycle 135) Desert, coast and venus_surface accepted. Taiga still shows a dense vertical streak curtain down the whole mountain face (review_b053 row 2, right). Smooth the face like the desert massif (raise ridge_lo or drop roughness below the snow line) and keep only the snow cap ridged. (Cycle 136) Taiga fixed (smooth massif with a soft snow cap); B-053 Done.

### B-054 · BLENDER · Done · M3
Goal: Icon `icons/cryo_round/base`: a frost-blue Lance round (an ammunition slug with a frosted cap and a cyan emissive band).
Accept: same icon camera and lights as B-013/B-042/B-051; readable at 32 px; stamped review.
Files: blender/scripts/build_icons.py, Assets/_Game/Art/icons/cryo_round/
Depends: B-051
Lead notes: Done (cycle 135): cryo round icon (brass casing, frost-blue slug, cyan band), readable at 32 px.

### B-055 · BLENDER · Done · M4
Goal: Jupiter column art completion (Bible §7.6): backgrounds/jupiter_deck2 (ammonium-hydrosulfide clouds, darker, lightning-lit), jupiter_deck3 (water clouds, warm storm towers), jupiter_deep (dark pressure haze with a glowing Crush band below); terrain/jupiter/floe_derelict (Meridian-expedition wreckage as standable floe material); props/jupiter/{husk_tortoise (Ballast tortoise husk platform), derelict_pod, beacon_vault}.
Accept: same pipeline rules (§9, tiling, painted cloud banks per B-048), stamped reviews; deck colours read as getting darker and warmer with depth.
Files: blender/scripts/gen_backdrop*.py, gen_terrain.py, build_props_jupiter.py, Assets/_Game/Art/backgrounds/jupiter_*/, terrain/jupiter/, props/jupiter/
Depends: B-048
Lead notes: Done (cycle 157): deck2/3 + deep backdrops, floe_derelict, derelict_pod, beacon_vault (cycle 156), husk_tortoise v2 af4ebdc (dead husk: slumped head with a hollow socket, cracked and missing plates, flat walk line, desaturated).

### B-056 · BLENDER · Superseded · M4
Goal: Jupiter creatures (Bible §7.6): `creatures/jupiter/stormglider` (manta floater, flier clip set), `lightning_eel` (electric, Deck 2, cyan-white emissive along the body), `belt_wasp` (small radiation-adapted swarm unit, 128 px), `ballast_tortoise` (huge slow floater; its dead pose must read as a standable platform; match B-055's husk_tortoise silhouette).
Accept: contract §4 sizes and the same clip names as the inner creatures; emission where glowing; cream/rust/brick palette (§9); stamped review contact sheet.
Files: blender/scripts/build_creatures_jupiter.py, Assets/_Game/Art/creatures/jupiter/
Depends: B-002
Lead notes: Cycle 147. M4.

### B-057 · BLENDER · Superseded · M4
Goal: Jupiter apex `creatures/jupiter/vortex_whale` (Bible §7.6): a 500 m floater built as segments (head, repeatable body, tail) that UNITY chains; per-segment size per the Venus apex precedent (D-042: 400 px × 5 frames); a "song" glow-pulse state; harpoon-anchor socket points in the JSON.
Accept: segments join without seams in a chained preview; stamped review; frames and sheets within contract §4.
Files: blender/scripts/build_creatures_jupiter.py, Assets/_Game/Art/creatures/jupiter/vortex_whale/
Depends: B-056
Lead notes: Cycle 147. M4.

### B-058 · BLENDER · Superseded · M4
Goal: Saturn column art (Bible §7.5, §7.7): backgrounds/saturn_deck1..3 and saturn_deep (pale gold and butter bands, soft low sun, the ring plane as a bright line across the upper sky in deck 1), terrain/saturn/floe_ice and floe_core; reuse the B-048/B-055 painted-cloud-bank pipeline.
Accept: same rules as B-055 (tiling, seams, stamped reviews, D-045 peak_mb measured before any numpy_only marker); decks darker and warmer with depth; clearly paler and golder than Jupiter.
Files: blender/scripts/gen_backdrop*.py, gen_terrain.py, Assets/_Game/Art/backgrounds/saturn_*/, terrain/saturn/
Depends: B-048
Lead notes: Cycle 147. M4. Start once B-055 is in review.

### B-059 · BLENDER · Superseded · M4
Goal: Ring and belt mining art (Bible §7.7): `props/space/ring_ice_01..04` (bright icy chunks), `props/space/ring_rock_01..04` (grey-brown silicate), `creatures/space/ringmite` (tiny top-down swarm unit, 64 px, chewing clip), `fx/ring_dust` (debris puff when a body breaks).
Accept: top-down camera and scale as the B-010 asteroids (64 px/m, D-018); sheets ≤ 1024²; stamped review.
Files: blender/scripts/build_asteroids.py, gen_fx.py, Assets/_Game/Art/props/space/, creatures/space/, fx/ring_dust/
Depends: B-010
Lead notes: Cycle 170 (bfbebbe): ring_rock_01..04, ringmite (ppu 54, idle/chew/hurt/death) and fx/ring_dust accepted. FAIL ring_ice_01..04, Art matches §9: they read as soft cotton puffs, not icy chunks. Fix: a hard irregular silhouette (faceted, a few flat cleavage planes), a bright specular highlight on the sun side and a cool blue shadow side, two or three dark cracks, no soft outer fuzz. Re-render the four ice bodies only, then mark Ready.

### B-060 · BLENDER · Superseded · M4
Goal: Saturn creatures (Bible §7.7): `creatures/saturn/helium_jelly` (translucent; add a "rise" clip for when it's hit), `hex_drake` (winged, flier clip set), `floe_moth` (small, 128 px).
Accept: contract §4 sizes and clips; pale gold palette, translucency where stated; stamped review.
Files: blender/scripts/build_creatures_saturn.py, Assets/_Game/Art/creatures/saturn/
Depends: B-002
Lead notes: Cycle 147. M4.

### B-061 · BLENDER · Done · M4
Goal: Icons batch M4 (keys match U-063 and U-069): helium3_condensate, deuterium, metallic_hydrogen, ammonia_ice, phosphorus_pigment, ring_ice, ring_rock, methane_ice, deep_diamond, superionic_ice, float_cell_mk1, float_cell_mk2, jetpack_mk2, jetpack_mk3.
Accept: same icon camera and lights as B-013/B-042/B-054; readable at 32 px; stamped review.
Files: blender/scripts/build_icons.py, Assets/_Game/Art/icons/<id>/
Depends: B-054
Lead notes: Done 37053f6 + 07335f6 (cycle 154): 13 icons, montage icons_b061_montage.png, all distinct at 32 px. Self-reported nits (helium3 glow pinkish, metallic_hydrogen beads small, ring_ice egg-like, jetpack_mk3 thin on dark UI) deferred to the M4 playtest; no polish pass now.

### B-062 · BLENDER · Done · M4
Goal: Uranus column art (Bible §7.5, §7.8): backgrounds/uranus_deck1..3 and uranus_deep (featureless cyan fog, dim light at sunlight 0.25, faint bands only hinted; crystalline sparkle below Deck 3 for the diamond rain; a dark-season variant tint for the unlit half as a second preset), terrain/uranus/floe_ice and floe_core (methane ice, pale cyan).
Accept: same rules as B-055/B-058 (tiling, seams, stamped reviews, D-045 peak_mb measured before any numpy_only marker); reads clearly as Uranus next to Saturn (cyan, dim, low contrast).
Files: blender/scripts/gen_backdrop*.py, gen_terrain.py, Assets/_Game/Art/backgrounds/uranus_*/, terrain/uranus/
Depends: B-048
Lead notes: Done 89e88b1 + 27d8a24 (cycle 158): day and dark-season decks + floes; reviews review_uranus_*/review_uranus_dark_* (stamped 21:47–21:54): dim cyan, low contrast, dark season reads as a colder blue; clearly distinct from Saturn. numpy_only peaks 681/683 MB.

### B-063 · BLENDER · Done · M4
Goal: Neptune column art (Bible §7.5, §7.9): backgrounds/neptune_deck1..3 and neptune_deep (deep indigo, white wisps streaking sideways to sell the wind, a dark storm mass that seems to breathe in deck 2–3), terrain/neptune/floe_ice and floe_core, plus terrain/neptune/superionic_ice (black "hot ice" with a faint inner glow, Deep only).
Accept: same pipeline rules; streaks tile horizontally; superionic ice readable against the deep backdrop; stamped reviews.
Files: blender/scripts/gen_backdrop*.py, gen_terrain.py, Assets/_Game/Art/backgrounds/neptune_*/, terrain/neptune/
Depends: B-048
Lead notes: Done (cycle 159): Neptune decks + floe_ice/floe_core/superionic_ice (27d8a24) and storm v4 on the near layer; review_neptune_deck2/3.png stamped 22:29–22:30: deep indigo, long white wind streaks, a soft dark storm mass.

### B-064 · BLENDER · Superseded · M4
Goal: Uranus creatures (Bible §7.8): `creatures/uranus/frostwisp` (small luminous floater, cyan-white emission, 128 px), `methane_ray` (glider, flier clip set), `hailcrab` (shelled walker whose shell catches diamonds; a "shell up" defend clip), `tiltbird` (migrating flier, small flock unit).
Accept: contract §4 sizes and clips as earlier creatures; dim-light readable (test the contact sheet at Uranus sunlight 0.25 in the lit preview); stamped review.
Files: blender/scripts/build_creatures_uranus.py, Assets/_Game/Art/creatures/uranus/
Depends: B-002
Lead notes: Cycle 158. M4.

### B-065 · BLENDER · Superseded · M4
Goal: Neptune creatures (Bible §7.9): `creatures/neptune/windrider` (sail-finned floater), `shadow_shoal` (dark fast fish-like swarm unit, 128 px, faint rim light so it reads on indigo), `pressure_phantom` (translucent, Deck 3), `anchor_worm` (holds floes; a coiled "anchored" pose and a free clip).
Accept: contract §4 sizes and clips; readable against the B-063 indigo decks; translucency where stated; stamped review.
Files: blender/scripts/build_creatures_neptune.py, Assets/_Game/Art/creatures/neptune/
Depends: B-002
Lead notes: Cycle 158. M4.

### B-066 · BLENDER · Superseded · M4
Goal: Saturn apex `creatures/saturn/polar_hydra` (Bible §7.7): a six-headed cloud serpent of the Hexagon's eye, built as a body segment set plus six head variants (each head a separate sprite with idle/strike/destroyed clips) so UNITY can remove heads one at a time; Venus apex precedent for size (D-042: 400 px × 5 frames per segment); pale gold with a cold inner glow.
Accept: heads and body join without seams in a chained preview; destroyed-head state reads at gameplay scale; frames and sheets within contract §4; stamped review.
Files: blender/scripts/build_creatures_saturn.py, Assets/_Game/Art/creatures/saturn/polar_hydra/
Depends: B-060
Lead notes: Cycle 164. M4.

### B-067 · BLENDER · Done · M4
Goal: Giant-world FX batch (Bible §7.5–7.9): `fx/lightning` (Deck 2–3 bolt + flash, 3 variants), `fx/diamond_rain` (falling 5–20 cm diamonds, sparkle), `fx/methane_hail`, `fx/wind_streaks` (Neptune lateral gusts, tileable), `fx/crush_pulse` (the pulsing dark band with the "CRUSH" label), `fx/skip_spool` + `fx/skip_streak` (Skip Drive spool-up glow and the travel streak, top-down), `fx/floe_sublimate` (a floe fading to vapour).
Accept: frames ≤ 256, sheets ≤ 1024², `.json` per sheet, emission where glowing; same rules as B-012; stamped contact sheet.
Files: blender/scripts/gen_fx.py, Assets/_Game/Art/fx/
Depends: B-012
Lead notes: Done 64f0265 + ba59ac8 (cycle 166): 10 FX sheets (3 lightning variants, diamond rain, methane hail, wind streaks, CRUSH band, skip spool + streak, floe sublimate); review_b067_fx.png stamped 00:01; numpy_only peak 327 MB.

### B-068 · BLENDER · Done · M4
Goal: Giant POI props (Bible §7.7–7.9): `props/saturn/{ring_rig, helium_trap, hexagon_wall_marker}` (the ring-mining rig with the Saturn beacon; a Deck 2–3 helium-rain trap; a wind-wall marker), `props/uranus/{tilted_derelict, umbrella_platform}` (the beacon derelict leaning at the axial tilt; a diamond-catching umbrella platform), `props/neptune/{wind_anchor, meridian_wreck_bow, meridian_wreck_mid, meridian_wreck_stern}` (the *Meridian* herself in three standable segments, alive with faint running lights).
Accept: contract §4 sizes (ppu per D-018 where a prop exceeds the margin); standable tops read flat; emission on beacons and running lights; stamped contact sheets.
Files: blender/scripts/build_props_saturn.py, build_props_uranus.py, build_props_neptune.py, Assets/_Game/Art/props/{saturn,uranus,neptune}/
Depends: B-055
Lead notes: Done 00abc78 (cycle 167): 9 props; Meridian wreck bow/mid/stern share the Jupiter hull recipe with lit portholes, torn ends, running lights and flat deck lines (512×400, ppu 108 per D-018); review_b068_props.png + review_b068_wreck.png stamped 00:08–00:09. Process gain: props are now grounded at z = 0 and framed from measured extents.

### B-069 · BLENDER · Done · M4
Goal: Aerostat and giant gear props (Bible §7.5, §4.2): `props/common/{aerostat_cell, aerostat_deck, aerostat_strut}` (the buildable platform modules: a gas cell, a deck plate, a strut, each tileable with the Venus aerostat look), `props/common/float_cell_pack` (the player's back-mounted float cell, two marks), `props/common/grapple_hook` + `fx/grapple_line` (the Rig grapple head and a tileable cable).
Accept: deck and strut tile seamlessly in a 3-wide preview; the float cell reads on the surveyor's back at 1:1; stamped contact sheet.
Files: blender/scripts/build_props_common.py, gen_fx.py, Assets/_Game/Art/props/common/, fx/grapple_line/
Depends: B-014
Lead notes: Done cfc0151 (cycle 169): aerostat_deck (2 m pitch), aerostat_strut (2 m, stacks with continuous braces), aerostat_cell, float_cell_pack mk1/mk2 at 1:1 on the surveyor, grapple_hook (pivot at the line point) + fx/grapple_line; b069_tiling_and_back.png and review_b069.png (stamped 00:14) checked.

### B-070 · BLENDER · Done · M4
Goal: Moon sky objects for the giants (Bible §7.6–7.9): `planets/io/surface`, `planets/europa/surface`, `planets/titan/surface`, `planets/enceladus/surface`, `planets/miranda/surface`, `planets/triton/surface` at 512×256 like Luna (B-010), with the geyser plumes of Enceladus and Triton as a `glow` layer; Io with volcanic hotspots.
Accept: same camera and lighting as Luna; real albedo/colour cues (Io yellow-sulfur, Europa cracked white, Titan orange haze, Triton pink-grey); stamped montage.
Files: blender/scripts/gen_planet.py, Assets/_Game/Art/planets/{io,europa,titan,enceladus,miranda,triton}/
Depends: B-010
Lead notes: Done c6b401b + ba59ac8 (cycle 166): Io (sulfur, hotspots), Europa (cracked white), Titan (orange haze), Enceladus, Miranda, Triton + two plume glows; review_b070_moons.png stamped 00:01. Short plumes (~40 px) accepted: moons are small sky objects.

### B-071 · BLENDER · Superseded · M4
Goal: Uranus apex `creatures/uranus/diamondback_colossus` (Bible §7.8): a huge armoured crawler of the diamond-rain layer, built as body + limb segments; joints are separate sprites with an "exposed" state (visible only while it reaches to feed) so UNITY can make only the joints take damage; diamond armour reads as faceted and sparkling in dim light; size per the Venus apex precedent (D-042: 400 px × 5 frames per segment).
Accept: a chained preview with the feed pose showing the exposed joints; stamped review; frames and sheets within contract §4.
Files: blender/scripts/build_creatures_uranus.py, Assets/_Game/Art/creatures/uranus/diamondback_colossus/
Depends: B-064
Lead notes: Cycle 169. M4.

### B-072 · BLENDER · Superseded · M4
Goal: Neptune apex `creatures/neptune/umbral_leviathan` (Bible §7.9): the final boss, a vast dark floater of the Great Dark Spot, built as head/body/tail segments plus a separate "maw" and two "anchor fin" sprites with their own clips; near-black with a faint indigo rim so it reads against the B-063 decks; a "roar" state with internal light.
Accept: chained preview reads at the gameplay scale against neptune_deck3; the rim light keeps the silhouette readable; stamped review; contract §4.
Files: blender/scripts/build_creatures_neptune.py, Assets/_Game/Art/creatures/neptune/umbral_leviathan/
Depends: B-065
Lead notes: Cycle 169. M4.

### B-073 · BLENDER · Superseded · M4
Goal: Giant zone overlays (Bible §7.6–7.9): side-view near-layer overlays that mark the four big zones: `backgrounds/jupiter_red_spot` (600 m of fast cream-and-brick wind bands, tileable, with spinning-floe debris wisps), `backgrounds/saturn_hexagon_wall` (a translucent rotating wind wall, 3 variants), `backgrounds/uranus_dark_season` tint overlay (already partly done in B-062; make it a separate alpha layer so UNITY can crossfade), `backgrounds/neptune_dark_storm` (a 400 m breathing storm mass with an inward pull suggested by streak direction, 2 frames for the breathing).
Accept: each is an alpha overlay that tiles horizontally; stamped reviews composited over the matching deck; D-045 peaks measured.
Files: blender/scripts/gen_backdrop*.py, Assets/_Game/Art/backgrounds/{jupiter_red_spot,saturn_hexagon_wall,uranus_dark_season,neptune_dark_storm}/
Depends: B-048
Lead notes: Cycle 169. M4. Numpy-only pipeline; good lock-free work.

### B-074 · BLENDER · Superseded · M4
Goal: M4 HUD and panel icons (ui/): buoyancy margin (up/down arrow in a cell), skip fuel, skip spool, wind (with direction), season (lit/dark half), Crush warning, float cell on/off, grapple ready, aerostat module slots (cell, deck, strut); plus item icons for the M4 recipes not covered by B-061: aerostat_cell, aerostat_deck, aerostat_strut, wind_anchor, grapple_hook, polymer.
Accept: same style and size as the existing ui/ HUD icons; readable at 24 px; item icons match B-013 camera and lights; stamped montage.
Files: blender/scripts/build_icons.py, blender/scripts/build_ui.py, Assets/_Game/Art/ui/, Assets/_Game/Art/icons/
Depends: B-061
Lead notes: Cycle 169. M4. Keys as written; UNITY will use them in U-062/U-067/U-071.

### B-075 · BLENDER · Superseded · M4
Goal: Saturn Waystation, Halcyon's largest market (Bible §7.7): `props/space/waystation_saturn` as a bigger top-down station sprite than the Earth/Mars waystation (B-0xx), with a ring-dock arm, lit hangars and a market canopy; plus `props/space/ring_rig_topdown` (the ring-mining rig as seen from space).
Accept: same top-down camera and scale as the existing waystation; sheets within contract §4; stamped review next to the Earth waystation for scale.
Files: blender/scripts/build_waystation.py, Assets/_Game/Art/props/space/
Depends: B-014
Lead notes: Cycle 169. M4. Feeds U-066 and the Saturn market.

### B-076 · BLENDER · Superseded · M4
Goal: Wardens, giant tier (Bible §2, §7.9 "the hardest Warden tier"): `creatures/warden/sentinel_mk2` and `creatures/warden/hunter_mk2` (heavier hulls, pressure-rated, indigo running lights, a visible shield emitter), `fx/warden_shield` (a hex-cell shield flash), `fx/warden_bolt_heavy`.
Accept: same clip set as the basic Wardens; mk2 reads as the same family but heavier at a glance; stamped review beside the mk1 sprites.
Files: blender/scripts/build_wardens.py, gen_fx.py, Assets/_Game/Art/creatures/warden/, fx/
Depends: B-002
Lead notes: Cycle 169. M4.

### B-083 · BLENDER · In Progress · R1
Goal: Earth depth bands (contract §9 depth-bands row): per Earth region (forest, plains, desert, ocean/coast, taiga, tundra) a `backgrounds/earth_<region>/ridge_mid.glb` (z 20–60 m strip, tileable every 256 m, ≤ 8 k tris, baked PBR from the v1 ridge recipes), a shared `skyline_far.glb` (≤ 4 k tris) and a `skydome` 2048×1024 equirect `color` per region derived from the v1 layer0 skies.
Accept: tiles seamlessly in x; reads as the v1 parallax from the side rail in UNITY's preview; stamped turntables; D-045/D-066 peaks measured.
Files: blender/scripts/gen_backdrop3d.py, Assets/_Game/Art/backgrounds/earth_*/
Depends: B-077
Lead notes: Cycle 186: art accepted in full. skyline_far v3 (11 seeded depth rows, broad massif, capped slopes, snow band; 2,560 tris; turntable stamped 02:22) reads as a snow-capped range; ridge_mid ×6 and skydomes ×6 accepted in cycle 183. Done on U-076's first capture with the depth bands in the scene.

### B-084 · BLENDER · In Progress · R1
Goal: Earth POI props as models: the Survey Archive, Launch Complex pieces, crashed Halcyon hauler, Warden outpost obelisk and the B-020/B-021 prop sets, each ≤ 6 k tris (hauler ≤ 15 k with LOD1), standable tops flat, emissive where lit.
Accept: contract §9; stamped turntables; UNITY lit preview for Done.
Files: blender/sources/props/earth/, build_props_earth.py, Assets/_Game/Art/props/earth/
Depends: B-077
Lead notes: Cycle 187 (b31f865): art accepted on the turntables (archive door + terminal, launch gantry + tower ruin, Earth beacon, hauler hull_a/hull_b/cargo with LOD1, Warden pylon, Meridian beacon; 188–1,404 tris). Rulings: the hauler stays as the three v1 pieces UNITY already places (no hero wreck now); the pylon stays the v1 obelisk. Done on UNITY's lit preview (fold into U-076's run).

### B-085 · BLENDER · In Progress · R1
Goal: Earth scenery for the near band and the play plane: 3 tree species (forest/taiga variants), 2 bushes, 3 rocks, grass tufts, a cactus and a dead tree, each ≤ 2 k tris with LOD1 at ≤ 800, sharing one 2048 atlas material; wind-sway via a vertex-colour mask (R = sway weight).
Accept: contract §9; a stamped grove preview (20 instances) reads under the Earth Sun; UNITY lit preview for Done.
Files: blender/sources/props/earth_flora/, build_props_earth.py, Assets/_Game/Art/props/earth_flora/
Depends: B-077
Lead notes: Cycle 188 (3a1ff4f): art accepted on review_b085_grove.png (11 models, shared 2048² atlas, sway in COLOR_0.r, LOD1 ≤ 800). Canopies are simple (blob oak, cone spruce); acceptable for R1, and a foliage-card pass is an M6 polish item, not now. Done on UNITY's lit preview; the shared atlas material is a one-off in ArtImporter (atlas_* maps, no per-model maps).

### B-086 · BLENDER · In Progress · R2
Goal: Mars terrain block materials (contract §9 terrain row), the R2 counterpart of B-080: every Mars tile material in `MarsTileSet` (regolith, basalt, hematite, clay, perchlorate, polar ice, CO₂ frost/snow, lava-tube rock…: list them from the tile set and log the list), top/side PBR sets at 512², 2 m per repeat, plus `terrain/mars/backwall`; from the v1 recipes, rust/salmon palette (§9).
Accept: tiles seamlessly; reads as the v1 Mars under the Mars Sun (0.75) in UNITY's lit preview; stamped contact sheet; peaks measured (D-045/D-066).
Files: blender/scripts/gen_terrain.py, Assets/_Game/Art/terrain/mars/
Depends: B-077
Lead notes: Cycle 189 (dc2b3c0): art accepted (regolith, basalt, hematite, ice, snow + basalt backwall; the board's clay/perchlorate/lava-tube examples are items or generator features, not tile materials, so none were due). Done on UNITY's first lit Mars block capture in R2.

### B-087 · BLENDER · In Progress · R2
Goal: Mars creatures as models: `creatures/mars/dustskater` (small class, ≤ 3 k tris) and `creatures/mars/scree_stalker` (medium, ≤ 8 k), full walker clip sets from the v1 rigs, materials matching Mars (silicate, dust).
Accept: contract §9; stamped turntables; UNITY lit preview at 60 px/m reads as the v1 silhouettes.
Files: blender/sources/creatures/mars/, build_creatures_mars.py, Assets/_Game/Art/creatures/mars/
Depends: B-077
Lead notes: Cycle 190: art accepted on the turntables (dustskater 2,850 tris on skate pads; scree_stalker 7,598 tris with back plates; 16-joint skins, 5 clips). Done on UNITY's lit preview in R2.

### B-088 · BLENDER · In Progress · R2
Goal: Mars depth bands (contract §9 depth-bands row), the R2 counterpart of B-083: `backgrounds/mars_<region>/ridge_mid.glb` for canyon, plains, polar and tharsis (Olympus Mons as the far hero), a shared `skyline_far.glb`, and skydomes per region (rust/salmon skies, the v1 dust haze; a `storm` skydome variant for the dust storm).
Accept: tiles seamlessly in x; reads as the v1 Mars parallax from the side rail; stamped turntables; peaks measured.
Files: blender/scripts/gen_backdrop3d.py, Assets/_Game/Art/backgrounds/mars_*/
Depends: B-077
Lead notes: Cycle 188. R2.

### B-089 · BLENDER · Ready · R2
Goal: Mars scenery and POI props as models: boulders ×3, regolith rocks ×2, ice chunks ×2, a dead shrub-like "dust bush", lava-tube stalactite/stalagmite pair (each ≤ 1.5 k tris, LOD1, one shared atlas); the Mars POI props from the v1 sources not already covered by B-084 (crash-site debris, the Mars Waystation surface beacon, ice-cap drill rig), ≤ 6 k tris each.
Accept: contract §9; a stamped field preview (20 instances) under the Mars Sun (0.75); UNITY lit preview for Done.
Files: blender/sources/props/mars/, build_props_mars.py, Assets/_Game/Art/props/mars_flora/, props/mars/
Depends: B-077
Lead notes: Cycle 188. R2.

### B-090 · BLENDER · Ready · R2
Goal: Space objects as models for U-078's lit top-down scene: `props/space/waystation` (the Earth/Mars Waystation as one model with a lit docking bay and running lights, LOD1), `props/space/asteroid_01..06` as low-poly rocks (≤ 600 tris each) from the v1 silhouettes, `planets/<name>/rings` for Saturn as a flat ring mesh with an alpha texture.
Accept: contract §9; top-down turntables at the Space camera scale; UNITY lit preview for Done.
Files: blender/scripts/build_waystation.py, build_asteroids.py, gen_planet.py, Assets/_Game/Art/props/space/, planets/saturn/
Depends: B-077
Lead notes: Cycle 188. R2. Feeds U-078.

### B-091 · BLENDER · Ready · R3
Goal: Mercury and Venus terrain block materials (R3 prep, as B-080/B-086): every tile material in `MercuryTileSet` (regolith, basalt, solarite crust, shadow ice, impact glass…) and `VenusTileSet` (basalt, sulfur crust, vent glass, station deck plates…), top/side PBR sets at 512², 2 m repeat, plus backwalls; palettes per §9.
Accept: tiles seamlessly; reads as the v1 materials under each planet's Sun in UNITY's lit preview; stamped contact sheets.
Files: blender/scripts/gen_terrain.py, Assets/_Game/Art/terrain/{mercury,venus}/
Depends: B-077
Lead notes: Cycle 188. R3 prep; numpy-light.

### B-012 · BLENDER · Done · M2
Goal: FX batch 1: `fx/thruster`, `fx/dust`, `fx/dig_sparks`, `fx/escape_band`, `fx/heat_shimmer`.
Accept: frames ≤ 256, sheets ≤ 1024², `.json` per sheet, emission where glowing.
Files: Assets/_Game/Art/fx/
Depends: B-002
Lead notes: Done 11828e9 + e450ab9 (cycle 12): five FX sheets; thruster contact sheet reads well (color/emission/alpha).

### B-013 · BLENDER · Done · M2
Goal: Icons batch 1 (16): iron, copper, carbon, silica, water_ice, oxygen, launch_fuel, hematite, perchlorate, clay, aluminium, living_seed, wood, stone, sand, nickel.
Accept: `icons/<item>/base` 128×128, consistent lighting angle, readable at 32 px.
Files: Assets/_Game/Art/icons/
Depends: B-002
Lead notes: Done 8ca8ba4 (cycle 17): 16 lit icons readable at 32 px (montage).

### B-014 · BLENDER · Done · M2
Goal: Props batch 1: `props/common/{landing_pad,shelter_wall,shelter_door,smelter,storage_crate,lamp}`.
Accept: ≤ 512², color + normal (+ emission for lamp and smelter), bottom-center pivots, mask R rim for interactables.
Files: Assets/_Game/Art/props/common/
Depends: B-002
Lead notes: Done 69b73e6 (cycle 19): landing pad, shelter wall/door, smelter, crate, lamp; worn industrial; emission for lights/windows.

### B-015 · BLENDER · Done · M2
Goal: Earth creatures `creatures/earth/stag`, `creatures/earth/wolf`.
Accept: medium class (256 px), standard creature set ≤ 30 frames, `.json`, color + normal.
Files: blender/sources/creatures/earth/, Assets/_Game/Art/creatures/earth/
Depends: B-009
Lead notes: Done 3f3e20e (cycle 31), v3 metaball method: continuous bodies, real stag proportions, 5-tine antlers, attached tail, soft underside; stag 101.75 / wolf 128 px/m, 320 px × 6 columns. Wolf silhouette polish → B-031. This method is the standard for B-016 and B-029.

### B-016 · BLENDER · Done · M2
Goal: Mars creatures `creatures/mars/dustskater` (small, 128 px), `creatures/mars/scree_stalker` (medium).
Accept: as B-015.
Files: Assets/_Game/Art/creatures/mars/
Depends: B-015
Lead notes: Done 0b105fb + b59f108 (cycle 39): scree stalker (116.75 px/m, 320 px, serrated stone-plate ridge, long hind legs) and dustskater (105 px/m, 128 px, broad skate pads); metaball method, Mars palette, no ears (thin air).

### B-017 · BLENDER · Done · M2
Goal: Asteroids `props/space/asteroid_01..06` and `planets/luna/surface` (512×256).
Accept: top-down, color + normal, six distinct silhouettes 1–6 m, sizes within contract §4.
Files: Assets/_Game/Art/props/space/, Assets/_Game/Art/planets/luna/
Depends: B-002
Lead notes: Done 087dcc9 (cycle 19): six asteroid silhouettes 1–6 m at 64 px/m (D-018 precedent), Luna 512×256 procedural.

### B-018 · BLENDER · Done · M2
Goal: Outer and inner planet discs for the space map: `planets/{mercury,venus,jupiter,saturn,uranus,neptune}/surface` (+ `glow` where an atmosphere exists: venus, jupiter, saturn, uranus, neptune) and `planets/saturn/rings` (top-down ring texture, transparent).
Accept: contract §4 sizes (surface 2048×1024 equirect, wraps in x; glow 512×512 with disc edge at r = 200 px as for Earth); public-domain sources (NASA/JPL/USGS global mosaics) logged in `docs/credits/blender.md`, or procedural bands where no mosaic exists; Venus shows the cloud tops, not the radar surface; contact sheets with a 2× wrap row.
Files: Assets/_Game/Art/planets/<planet>/, blender/sources/planets/<planet>/
Depends: B-002
Lead notes: Done 087dcc9 (cycle 19): Mercury (MESSENGER) and Jupiter (Cassini) PD sources, procedural Venus/Saturn/Uranus/Neptune, glows, Saturn rings (smooth at full size). Integration → U-034.

### B-020 · BLENDER · Done · M2
Goal: Earth POI props: `props/earth/{launch_gantry,launch_tower_ruin,archive_door,archive_terminal,beacon}` for the abandoned coastal launch complex and the Survey Archive (Bible §7.1).
Accept: contract §4 prop rules (≤ 512×512, bottom-center pivot, color + normal, emission where lit); weathered, documentary-naturalistic per §9; `beacon` has an emission pulse-ready map.
Files: Assets/_Game/Art/props/earth/
Depends: B-002
Lead notes: Done 554e14f (cycle 24): launch gantry/tower ruin, archive door/terminal, beacon; worn, emission on lights. Gantry stacking per BLENDER handoff.

### B-021 · BLENDER · Done · M2
Goal: Mars POI props: `props/mars/{hauler_hull_a,hauler_hull_b,hauler_cargo,warden_pylon,meridian_beacon}` for the crashed Halcyon hauler and the Warden outpost (Bible §7.2).
Accept: contract §4 prop rules; rust-dusted per Mars §9 palette; `warden_pylon` and `meridian_beacon` carry emission.
Files: Assets/_Game/Art/props/mars/
Depends: B-002
Lead notes: Done 554e14f (cycle 24): hauler hulls/cargo, Warden pylon, Meridian beacon. Hauler drift reads as a plain slab, so it goes into a later polish task (not a reopen).

---

## Backlog (not yet Ready; LEAD promotes)
M2: Earth/Mars POIs, day/night lighting pass (U), Mars dust storm (U), creature AI v1 (U),
Cryo meter (U), `PlanetDisc` shader with real textures (U). (POI prop sets promoted to B-020, B-021 in cycle 5.)
