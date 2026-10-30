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

### L-007 · LEAD · Ready · M0
Goal: LeadQA test assembly and smoke test.
Accept: `Assets/_Game/Tests/LeadQA/MERIDIAN.Tests.LeadQA.asmdef`; `SmokeTests.cs` loads `Core.unity`, asserts `LogAssert.NoUnexpectedReceived()`; passes via `tools/unity_test.ps1 PlayMode`.
Files: Assets/_Game/Tests/LeadQA/
Depends: U-004
Lead notes: —

### L-008 · LEAD · Ready · M0
Goal: M0 exit review and report.
Accept: every M0 exit criterion (Bible §12) checked with evidence in REVIEW_LOG; `coordination/reviews/M0_REPORT.md` under 200 words; `warnings_baseline.txt` created.
Files: coordination/REVIEW_LOG.md, coordination/reviews/
Depends: U-005, B-002, L-007
Lead notes: —

### L-009 · LEAD · Ready · M1
Goal: Groom M1; draft M2 tasks in `## Backlog`.
Accept: ≥ 5 Ready per worker at all times during M1; M2 drafts cover every Bible §12 M2 item.
Files: coordination/TASK_BOARD.md
Depends: L-008
Lead notes: —

### L-010 · LEAD · Ready · M1
Goal: M1 QA scenario and report.
Accept: LeadQA PlayMode test drives Earth → launch → Mars well → entry → landing → save → load; passes twice; `M1_REPORT.md` written; `Build/MERIDIAN_0.1.0/` plays.
Files: Assets/_Game/Tests/LeadQA/M1LoopTests.cs, coordination/reviews/M1_REPORT.md
Depends: U-017
Lead notes: —

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

### U-003 · UNITY · In Progress · M0
Goal: Batch test and build scripts.
Accept: `tools/unity_test.ps1 [EditMode|PlayMode]` writes `logs/tests_<date>.xml` and `coordination/reports/unity/tests_<date>.md` (pass/fail counts, failed names); `tools/unity_build.ps1` produces a dev build in `Build/`; both honor HeavyJobLock and exit non-zero on failure.
Files: tools/unity_test.ps1, tools/unity_build.ps1, Assets/_Game/Code/Editor/BuildTools.cs
Depends: U-001
Lead notes: —

### U-004 · UNITY · In Progress · M0
Goal: `Core.unity` with `GameState`, `SceneDirector`, `TimeSystem` (72×), bootstrap; `Space.unity` and `PlanetSide.unity` stubs loaded additively.
Accept: Play from Core loads Space (inactive) and PlanetSide (Earth config); smoke test with `LogAssert.NoUnexpectedReceived()` passes.
Files: Assets/_Game/Scenes/, Assets/_Game/Code/Runtime/Core/
Depends: U-002
Lead notes: —

### U-005 · UNITY · In Progress · M0
Goal: `ArtImporter` + `ArtKeys` + M1 placeholder set.
Accept: Every rule in contract §6 implemented and covered by an EditMode test; placeholders exist for: characters/surveyor, ships/pilgrim/top+side, terrain/earth/{soil,grass,stone,sand,snow,water}, terrain/mars/{regolith,basalt,hematite,ice}, backgrounds/{earth,mars,space}/layer0..2, planets/{sun,mercury,venus,earth,mars,jupiter,saturn,uranus,neptune}/surface, planets/earth/clouds, fx/{thruster,dust,dig_sparks,escape_band,heat_shimmer}, props/common/calibration; importing B-002's calibration asset retires its placeholder with no manual step.
Files: Assets/_Game/Code/Editor/ArtImporter.cs, Assets/_Game/Code/Runtime/Art/ArtKeys.cs, Assets/_Game/Placeholders/**, Assets/_Game/Tests/Unit/ArtImporterTests.cs
Depends: U-001
Lead notes: This is the M0 calibration handshake with B-002. (Cycle 4) Calibration handshake: when ArtImporter works, run tools/unity_art_preview.ps1 props/common/calibration and record the preview path in your status so LEAD can close B-002. Commit the Art .meta files (D-016).

### U-006 · UNITY · Ready · M0
Goal: Lit art preview tool.
Accept: `tools/unity_art_preview.ps1 <key>` renders the sprite under a global light plus one upper-right point light to `logs/preview_<key>.png` in batch mode.
Files: tools/unity_art_preview.ps1, Assets/_Game/Code/Editor/ArtPreview.cs, Assets/_Game/Scenes/ArtPreview.unity
Depends: U-005
Lead notes: —

### U-007 · UNITY · Ready · M1
Goal: Terrain v1: 32×32 chunks, `IWorldGenerator`, `SolidWorldGenerator` (Earth, Mars), streaming, pooling, RuleTiles with normal maps, per-chunk collision.
Accept: Earth world streams at ≤ 12 ms frame on the dev laptop; chunk apply ≤ 2 ms per frame; only chunks within 2 of the camera resident (PlayMode test); seams invisible at ortho size 9.
Files: Assets/_Game/Code/Runtime/Terrain/, Assets/_Game/Prefabs/Terrain/
Depends: U-004, U-005
Lead notes: Bible §10.4.

### U-008 · UNITY · Ready · M1
Goal: Dig and place with diffs.
Accept: Beam removes a tile and spawns its item; Builder places a tile; diffs recorded per chunk; PlayMode test: dig → save → load → tile still absent.
Files: Assets/_Game/Code/Runtime/Terrain/TerrainEdits.cs, Code/Runtime/Rig/
Depends: U-007
Lead notes: —

### U-009 · UNITY · Ready · M1
Goal: Player controller with real gravity.
Accept: walk 4.0 / sprint 6.5 m/s; v₀ 7.00 m/s; jump height within ±3% of Bible §4.2 on Earth, Mars, Jupiter (test scenes with each `PlanetConfig`); fall damage 12/24 m/s thresholds; terminal velocity per planet; coyote 0.10 s, buffer 0.12 s; Jetpack Mk1 14 m/s² for 3 s; Input System map per Bible §6.
Files: Assets/_Game/Code/Runtime/Player/, Assets/_Game/Settings/Input/, Tests/Unit/PlayerPhysicsTests.cs
Depends: U-004
Lead notes: —

### U-010 · UNITY · Ready · M1
Goal: Side-view ship: board/exit, Mk1 thrust, launch fuel burn, landing rules, Escape Line band + HUD marker.
Accept: Launch from Earth costs 17 fuel over the first 3 s of thrust from rest; crossing the Escape Line with v_y > 0 raises `EscapeLineCrossed`; touchdown ≤ 6 m/s no damage, 6–15 proportional, > 15 crash to 30% hull; PlayMode test for each.
Files: Assets/_Game/Code/Runtime/Ship/, Prefabs/Ship/Pilgrim.prefab, Tests/Unit/ShipSideTests.cs
Depends: U-009
Lead notes: —

### U-011 · UNITY · Ready · M1
Goal: Top-down space: Sun, 8 planet discs (placeholder `PlanetDisc`), moons, belt, Gravity Wells, Atmosphere Rings, cruise/boost ship, HUD, camera.
Accept: positions and radii per Bible §3; well pull at Earth's 4R edge = 1.00 u/s² ±1% (EditMode test on the formula); cruise 80 / boost 160 u/s; Earth → Mars flight works; ≤ 80 draw calls.
Files: Assets/_Game/Code/Runtime/Space/, Assets/_Game/Shaders/PlanetDisc.shadergraph, Scenes/Space.unity
Depends: U-004
Lead notes: —

### U-012 · UNITY · Ready · M1
Goal: Both transitions per Bible §5.2–5.3.
Accept: launch ≤ 1.5 s total with state carried (hull, fuel, cargo), ship on the Atmosphere Ring at the longitude angle with 20 u/s outward; entry on inward ring crossing or F: ship at Escape Line + 20 m descending 15 m/s with planet gravity; PlayMode tests for both.
Files: Assets/_Game/Code/Runtime/Core/SceneDirector.cs, Code/Runtime/Transitions/
Depends: U-010, U-011
Lead notes: —

### U-013 · UNITY · Ready · M1
Goal: Save/load per Bible §10.7.
Accept: `state.json` + `terrain_<planet>.bin`; autosave on transitions and every 5 min; 3 rotating backups; version field; PlayMode test: save → load → identical state and terrain.
Files: Assets/_Game/Code/Runtime/Save/
Depends: U-008, U-012
Lead notes: Company name for the save path: use "Zubers" unless D-011 says otherwise.

### U-014 · UNITY · Ready · M1
Goal: BudgetGate v1, `BudgetMonitor`, profiling script.
Accept: tests for frame time, GC per 300 frames, light and particle caps, memory on Earth, Mars, Space; `tools/unity_profile.ps1` writes `coordination/reports/unity/perf_<date>.md` with every Bible §11.1 row.
Files: Assets/_Game/Tests/Unit/BudgetGateTests.cs, Code/Runtime/Perf/BudgetMonitor.cs, tools/unity_profile.ps1
Depends: U-007, U-011
Lead notes: —

### U-015 · UNITY · Ready · M1
Goal: HUD and menus v1.
Accept: main menu (New, Continue, Quit), pause, side HUD (health, oxygen placeholder, fuel, altitude bar with Escape Line marker), top HUD (speed, fuel, well indicator); OFL font logged in `docs/credits/unity.md`.
Files: Assets/_Game/UI/, Code/Runtime/UI/
Depends: U-010, U-011
Lead notes: —

### U-016 · UNITY · Ready · M1
Goal: Placeholder audio set and `AudioDirector`.
Accept: CC0 SFX for jump, land, dig, place, thrust, UI click; one ambient loop; every file's source and license in `docs/credits/unity.md`; Vorbis; ≤ 10 MB total.
Files: Assets/_Game/Audio/, Code/Runtime/Audio/, docs/credits/unity.md
Depends: U-004
Lead notes: —

### U-017 · UNITY · Ready · M1
Goal: M1 integration and build.
Accept: PlayMode integration test Earth → launch → Mars → land → save → load passes twice with a clean console; `Build/MERIDIAN_0.1.0/` built by `tools/unity_build.ps1`; perf report green.
Files: Assets/_Game/Tests/Unit/M1IntegrationTests.cs, Build/
Depends: U-005…U-016
Lead notes: —

---

## BLENDER

### B-001 · BLENDER · Done · M0
Goal: Pipeline skeleton: `blender/` tree, `manifest.json` schema, `render.py` CLI (`--asset`, `--category`, `--all`, `--preview`), `tools/blender_render.ps1`, logging, memory settings per contract §3.
Accept: `tools/blender_render.ps1 all` on an empty manifest exits 0; an unknown key exits non-zero with a one-line reason; a line per asset in `logs/blender_<date>.log`.
Files: blender/render.py, blender/manifest.json, blender/scripts/, tools/blender_render.ps1
Depends: L-005
Lead notes: Done 4dd7922/5d630d4 (cycle 4): unknown key → FAIL line + non-zero; 11 assets logged one line each. Empty-manifest run not retained in logs; accepted on the populated-manifest runs.

### B-002 · BLENDER · Review · M0
Goal: Calibration asset `props/common/calibration`.
Accept: 1 m sphere on a 1 m cube with known flat colors; color, normal, emission, mask exported per contract §2; contact sheet shows the upper-right of the sphere lit when the light is upper-right; 8 px dilation visible; sizes logged.
Files: blender/sources/props/calibration.blend, Assets/_Game/Art/props/common/calibration_*.png
Depends: B-001
Lead notes: Review (cycle 4). Blender-side checks pass (contact sheet: sphere lit upper-right, OpenGL normals, 8 px dilation, exact flat colors). Waiting only on the U-005 lit preview via unity_art_preview.ps1. Dependents (B-003+) may proceed.

### B-003 · BLENDER · Review · M2
Goal: Earth top-down: `planets/earth/surface` (2048×1024), `clouds` (1024×512), `glow` (512).
Accept: contract §4 sizes; public-domain source imagery logged in `docs/credits/blender.md`; preview wraps without a seam.
Files: blender/sources/planets/earth.blend, Assets/_Game/Art/planets/earth/
Depends: B-002
Lead notes: Review (cycle 4). Contract sizes, LFS, credits, and wrap all pass on the contact sheets. Waiting on the in-Unity lit check after U-005 and the art preview tool; no BLENDER action needed.

### B-004 · BLENDER · Review · M2
Goal: Mars top-down: `planets/mars/surface`, `glow`.
Accept: as B-003.
Files: Assets/_Game/Art/planets/mars/
Depends: B-002
Lead notes: Review (cycle 4). Contract sizes, LFS, credits, and wrap all pass on the contact sheets. Waiting on the in-Unity lit check after U-005 and the art preview tool; no BLENDER action needed.

### B-005 · BLENDER · Review · M2
Goal: Sun and space backgrounds: `planets/sun/surface` + `glow` (emission), `backgrounds/space/layer0..2`.
Accept: Sun emission map present; three 2048×1024 star layers tileable in x, with a Milky Way band on layer0.
Files: Assets/_Game/Art/planets/sun/, Assets/_Game/Art/backgrounds/space/
Depends: B-002
Lead notes: Review (cycle 4). Contract sizes, LFS, credits, and wrap all pass on the contact sheets. Waiting on the in-Unity lit check after U-005 and the art preview tool; no BLENDER action needed.

### B-006 · BLENDER · In Progress · M2
Goal: Starter ship **Pilgrim**: `ships/pilgrim/top` and `side`.
Accept: top ≤ 448×448 (see UNITY handoff), side ≤ 1536×512; color, normal, emission; thrusters and windows glow; industrial-worn look per Bible §9.
Files: blender/sources/ships/pilgrim.blend, Assets/_Game/Art/ships/pilgrim/
Depends: B-002
Lead notes: —

### B-007 · BLENDER · Ready · M2
Goal: Earth terrain sets: `terrain/earth/{soil,grass,stone,sand,snow,water}`.
Accept: six 47-tile RuleTile sets, 128 px tiles, 8 columns, color + normal, 2× tile check passes.
Files: blender/sources/terrain/earth.blend, Assets/_Game/Art/terrain/earth/
Depends: B-002
Lead notes: Water as a tile set for M1/M2; a fluid system may replace it later (D-010).

### B-008 · BLENDER · Ready · M2
Goal: Mars terrain sets: `terrain/mars/{regolith,basalt,hematite,ice}`.
Accept: as B-007.
Files: Assets/_Game/Art/terrain/mars/
Depends: B-007
Lead notes: —

### B-009 · BLENDER · Ready · M2
Goal: Player character `characters/surveyor` frame sheet.
Accept: 256 px frames, standard character set ≤ 48 frames, color + normal + emission (visor, lamp), `.json` manifest, bottom-center pivot, right-facing.
Files: blender/sources/characters/surveyor.blend, Assets/_Game/Art/characters/surveyor/
Depends: B-002
Lead notes: —

### B-010 · BLENDER · Ready · M2
Goal: Earth parallax `backgrounds/earth/layer0..2` (temperate biome).
Accept: three 2048×1024 layers tileable in x; haze gradient readable; palette per Bible §9.
Files: Assets/_Game/Art/backgrounds/earth/
Depends: B-002
Lead notes: —

### B-011 · BLENDER · Ready · M2
Goal: Mars parallax `backgrounds/mars/layer0..2`.
Accept: as B-010 with the Mars palette and butterscotch sky.
Files: Assets/_Game/Art/backgrounds/mars/
Depends: B-010
Lead notes: —

### B-012 · BLENDER · Ready · M2
Goal: FX batch 1: `fx/thruster`, `fx/dust`, `fx/dig_sparks`, `fx/escape_band`, `fx/heat_shimmer`.
Accept: frames ≤ 256, sheets ≤ 1024², `.json` per sheet, emission where glowing.
Files: Assets/_Game/Art/fx/
Depends: B-002
Lead notes: —

### B-013 · BLENDER · Ready · M2
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

---

## Backlog (not yet Ready; LEAD promotes)
M2: Earth/Mars POIs, day/night lighting pass (U), Mars dust storm (U), creature AI v1 (U),
Cryo meter (U), `PlanetDisc` shader with real textures (U), 2 Earth and 2 Mars POI prop sets (B).
