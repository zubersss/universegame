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

### L-010 · LEAD · In Progress · M1
Goal: M1 QA scenario and report.
Accept: LeadQA PlayMode test drives Earth → launch → Mars well → entry → landing → save → load; passes twice; `M1_REPORT.md` written; `Build/MERIDIAN_0.1.0/` plays.
Files: Assets/_Game/Tests/LeadQA/M1LoopTests.cs, coordination/reviews/M1_REPORT.md
Depends: U-017
Lead notes: In Progress (cycle 16): M1LoopTests passed twice (15:55; 16:42 touchdown 2.00 m/s, 55 s). M1_REPORT.md drafted. Waiting on U-031 (0.1.1 smoke) before posting the playtest (USER-09).

---

## UNITY

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

### U-031 · UNITY · In Progress · M1
Goal: Rebuild the M1 playtest build after U-018 as `Build/MERIDIAN_0.1.1/` and redo the build smoke screenshots.
Accept: on the ground the Pilgrim shows deployed skids touching the terrain (no floating hull, as seen in smoke_2_earth.png of 0.1.0, built before U-018); the menu hides the HUD behind it; smoke run clean; the 0.1.0 folder may stay.
Files: Build/ (ignored), coordination/reports/unity/smoke_<date>/
Depends: U-017, U-018
Lead notes: PRIORITY: next, before more M2 work (cycle 15). This is the build the user will playtest.

### U-024 · UNITY · In Progress · M2
Goal: PlanetSide parallax: `backgrounds/<planet>/layer0..2` behind the terrain (layer0 slowest), plus a haze gradient per planet (Bible §9 Atmosphere).
Accept: capture at Earth and Mars shows three layers moving at different rates when the camera pans; no seams when wrapping; ≤ 3 extra draw calls; uses the B-010/B-011 rework files when present, placeholders otherwise.
Files: Assets/_Game/Code/Runtime/Planet/, Scenes/PlanetSide.unity
Depends: U-007
Lead notes: M2 draft promoted early (cycle 10) to keep the queue ≥ 5; M1 tasks still come first.

### U-025 · UNITY · Ready · M2
Goal: Day/night lighting: sun Light2D angle and color follow TimeSystem (20 min Earth day, 20.5 min Mars), sunlight intensity from Bible §9 per planet, ambient night level, sky tint.
Accept: EditMode test: Earth noon/midnight intensities match §9; captures at dawn/noon/dusk/night on Earth; 0 B GC per frame.
Files: Assets/_Game/Code/Runtime/Planet/Lighting/
Depends: U-004
Lead notes: M2 draft (cycle 10).

### U-026 · UNITY · Ready · M2
Goal: Mars dust storm (Bible §7.2): 60 s warning, 2–6 min storm every 4–7 game days, visibility 15 m, Cryo +1, static discharges.
Accept: PlayMode test forces a storm: warning event 60 s before; fog shrinks visibility to 15 m; Cryo level rises by 1; storm ends inside 2–6 min; uses fx/dust when present.
Files: Assets/_Game/Code/Runtime/Planet/Weather/
Depends: U-025
Lead notes: M2 draft (cycle 10).

### U-027 · UNITY · Ready · M2
Goal: Creature AI v1: grazer (stag: wander, flee), pack hunter (wolf: night, chase), scavenger (dustskater), canyon hunter (scree stalker); spawns by biome and time; real gravity on bodies.
Accept: PlayMode tests: stag flees within 8 m, wolf packs spawn only at night, creatures never fall through streamed chunks; ≤ 0.5 ms AI per frame with 20 creatures; placeholders until B-015/B-016.
Files: Assets/_Game/Code/Runtime/Creatures/
Depends: U-009
Lead notes: M2 draft (cycle 10).

### U-029 · UNITY · Ready · M2
Goal: Hazard system v1 (Bible §7 0–3 scale) with Cryo first: per-planet/biome/time Cryo level (Earth tundra night 1; Mars day 1 / night 2; dust storm +1), suit integrity drain by level, HUD Cryo meter, warmth near a lit shelter or the ship.
Accept: EditMode tests for the level table; PlayMode: Mars night drains suit and the ship stops the drain; level 3 is lethal within 30 s unprotected (§7 definition); the HUD meter shows the level and drain.
Files: Assets/_Game/Code/Runtime/Hazards/, UI/
Depends: U-025
Lead notes: M2 draft (cycle 13). Build the API so Thermal/Radiation/Toxic/Pressure plug in later (M3).

### U-030 · UNITY · Ready · M2
Goal: POIs v1 on Earth and Mars: place the Survey Archive and the abandoned coastal launch complex (Earth), the crashed Halcyon hauler and the Warden outpost (Mars) as handmade stamps merged into the generated terrain at fixed longitudes; use B-020/B-021 props (placeholders until Done).
Accept: each POI appears at its longitude in every new world and survives dig/save/load (stamps write diffs once); a map marker for each; PlayMode test per planet.
Files: Assets/_Game/Code/Runtime/Planet/POI/, Assets/_Game/Prefabs/POI/
Depends: U-007, U-013
Lead notes: M2 draft (cycle 13). The Archive is the story start (Bible §2). Put it within 200 m of spawn.

---

## BLENDER

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

### B-024 · BLENDER · Ready · M2
Goal: HeavyJobLock fairness + memory gate in `tools/blender_render.ps1` (D-026), mirroring U-023.
Accept: writes `want_blender.lock` while waiting, deletes it on acquire; yields to a fresh `want_unity.lock` after its own job; refuses below 1.5 GB free RAM; one job ≤ 20 min (split `all` exports by category).
Files: tools/blender_render.ps1
Depends: —
Lead notes: PRIORITY: do this before the next full export (cycle 10).

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

### B-025 · BLENDER · Ready · M2
Goal: Parallax polish from the cycle-13 review of the 3D backgrounds.
Accept: Earth: foliage reads as leaf masses, not stacked spheres (denser, smaller leaf-card clusters with silhouette breakup); clouds are soft volumetric or painted-haze shapes, not opaque white blobs, and never overlap the near tree line. Mars: no vertical spike/streak band in the mid layer (layer1 ground); at least 3 boulder shape families with varied scale. Same keys, sizes, tiling, and memory plan (D-028).
Files: blender/scripts/gen_backdrop3d.py, Assets/_Game/Art/backgrounds/{earth,mars}/
Depends: B-010, B-011
Lead notes: M2 exit polish, not a reopen. Schedule after B-023.

### B-012 · BLENDER · Done · M2
Goal: FX batch 1: `fx/thruster`, `fx/dust`, `fx/dig_sparks`, `fx/escape_band`, `fx/heat_shimmer`.
Accept: frames ≤ 256, sheets ≤ 1024², `.json` per sheet, emission where glowing.
Files: Assets/_Game/Art/fx/
Depends: B-002
Lead notes: Done 11828e9 + e450ab9 (cycle 12): five FX sheets; thruster contact sheet reads well (color/emission/alpha).

### B-013 · BLENDER · In Progress · M2
Goal: Icons batch 1 (16): iron, copper, carbon, silica, water_ice, oxygen, launch_fuel, hematite, perchlorate, clay, aluminium, living_seed, wood, stone, sand, nickel.
Accept: `icons/<item>/base` 128×128, consistent lighting angle, readable at 32 px.
Files: Assets/_Game/Art/icons/
Depends: B-002
Lead notes: —

### B-014 · BLENDER · Ready · M2
Goal: Props batch 1: `props/common/{landing_pad,shelter_wall,shelter_door,smelter,storage_crate,lamp}`.
Accept: ≤ 512², color + normal (+ emission for lamp and smelter), bottom-center pivots, mask R rim for interactables.
Files: Assets/_Game/Art/props/common/
Depends: B-002
Lead notes: —

### B-015 · BLENDER · Ready · M2
Goal: Earth creatures `creatures/earth/stag`, `creatures/earth/wolf`.
Accept: medium class (256 px), standard creature set ≤ 30 frames, `.json`, color + normal.
Files: blender/sources/creatures/earth/, Assets/_Game/Art/creatures/earth/
Depends: B-009
Lead notes: —

### B-016 · BLENDER · Ready · M2
Goal: Mars creatures `creatures/mars/dustskater` (small, 128 px), `creatures/mars/scree_stalker` (medium).
Accept: as B-015.
Files: Assets/_Game/Art/creatures/mars/
Depends: B-015
Lead notes: —

### B-017 · BLENDER · Ready · M2
Goal: Asteroids `props/space/asteroid_01..06` and `planets/luna/surface` (512×256).
Accept: top-down, color + normal, six distinct silhouettes 1–6 m, sizes within contract §4.
Files: Assets/_Game/Art/props/space/, Assets/_Game/Art/planets/luna/
Depends: B-002
Lead notes: —

### B-018 · BLENDER · Ready · M2
Goal: Outer and inner planet discs for the space map: `planets/{mercury,venus,jupiter,saturn,uranus,neptune}/surface` (+ `glow` where an atmosphere exists: venus, jupiter, saturn, uranus, neptune) and `planets/saturn/rings` (top-down ring texture, transparent).
Accept: contract §4 sizes (surface 2048×1024 equirect, wraps in x; glow 512×512 with disc edge at r = 200 px as for Earth); public-domain sources (NASA/JPL/USGS global mosaics) logged in `docs/credits/blender.md`, or procedural bands where no mosaic exists; Venus shows the cloud tops, not the radar surface; contact sheets with a 2× wrap row.
Files: Assets/_Game/Art/planets/<planet>/, blender/sources/planets/<planet>/
Depends: B-002
Lead notes: Replaces UNITY's placeholders for the six remaining planets (U-005 list). Rings: propose the size and ring-inner/outer radii in px in your status; UNITY draws them at Saturn's ring radius 220 units (Bible §3).

### B-020 · BLENDER · Ready · M2
Goal: Earth POI props: `props/earth/{launch_gantry,launch_tower_ruin,archive_door,archive_terminal,beacon}` for the abandoned coastal launch complex and the Survey Archive (Bible §7.1).
Accept: contract §4 prop rules (≤ 512×512, bottom-center pivot, color + normal, emission where lit); weathered, documentary-naturalistic per §9; `beacon` has an emission pulse-ready map.
Files: Assets/_Game/Art/props/earth/
Depends: B-002
Lead notes: Promoted from Backlog ("2 Earth and 2 Mars POI prop sets").

### B-021 · BLENDER · Ready · M2
Goal: Mars POI props: `props/mars/{hauler_hull_a,hauler_hull_b,hauler_cargo,warden_pylon,meridian_beacon}` for the crashed Halcyon hauler and the Warden outpost (Bible §7.2).
Accept: contract §4 prop rules; rust-dusted per Mars §9 palette; `warden_pylon` and `meridian_beacon` carry emission.
Files: Assets/_Game/Art/props/mars/
Depends: B-002
Lead notes: Promoted from Backlog.

---

## Backlog (not yet Ready; LEAD promotes)
M2: Earth/Mars POIs, day/night lighting pass (U), Mars dust storm (U), creature AI v1 (U),
Cryo meter (U), `PlanetDisc` shader with real textures (U). (POI prop sets promoted to B-020, B-021 in cycle 5.)
