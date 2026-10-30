# MERIDIAN — Review Log

Owner: LEAD. One entry per review cycle. Format:

```
## Cycle <n> · <date time>
Checked: <files/logs/previews opened>
Moved: <task → status (commit)>
Decided: <D-### or none>
Signals: <loop/stall signals and responses, or none>
User: <USER_ACTIONS changes, or none>
```

## Cycle 0 · (M0 start)
Checked: —
Moved: —
Decided: D-001…D-008, D-010 adopted from the architect draft.
Signals: none
User: USER-01…06 posted.

## Cycle 1 · 2026-10-30
Checked: MERIDIAN_SETUP.md (all 18 files extracted, line counts match); `git lfs track`; `git check-ignore` on logs/, Build/, blender/preview/, coordination/locks/*.lock, Library/; `.claude/settings.json` vs code.claude.com/docs/en/permissions; installed tools on the laptop.
Moved: L-001 → Done (4c10618); L-002 → Done (21d0584); L-003 → Done (4396dfa); L-004 → Done.
Decided: D-009 filled; D-012 (play/meridian/ and the old GPT automation stay on main, user choice).
Signals: none (workers not started).
User: USER-01, 02, 05, 06 verified done; USER-03 (Unity), USER-04 (Blender) open; USER-08 (optional PowerShell allow rules) posted.
L-004 note: settings.json parses; `Bash(x:*)` and `acceptEdits` valid per current docs; all 40 deny rules kept; 42 `PowerShell(...)` deny equivalents added because Bash rules don't cover the PowerShell tool on Windows.

## Cycle 2 · 2026-10-30
Checked: `C:\Program Files\Unity\Hub\Editor\6000.6.5f1\Editor\Unity.exe` (6000.6.5f1; Hub cache labels it SUPPORTED, recommended); bundled packages in the editor's PackageManager folder (URP 17.6.0, Addressables 2.11.2, Input System 1.20.0, Test Framework 1.8.0); Windows player variations (Mono only, no IL2CPP); `blender.exe --version` (5.2.2 LTS); `claude --version` (2.1.314).
Moved: L-005 → Done; L-006 → Done; USER-03, USER-04 → Done.
Decided: D-011 (company "Zubers"); D-013 (Unity 6000.6.5f1, not LTS); D-014 (Mono backend). Bible → v1.1.
Signals: none.
User: READY FOR WORKERS posted; USER-07 open (start UNITY and BLENDER sessions); USER-08 optional.

## Cycle 3 · 2026-10-30
Checked: `git log` (no worker commits yet); UNITY_STATUS (U-001 In Progress), BLENDER_STATUS (B-001 In Progress); `coordination/locks/` (empty); running processes.
Moved: none.
Decided: D-015 (HeavyJobLock process check by path; CLAUDE.md rule 6 updated). PID 2828 `Unity Hub\resources\unity.exe serve` is the Hub service, not the Editor.
Signals: none (both workers started this cycle; uncommitted U-001/B-001 work in the tree).
User: none.
Queue: U-001 and B-001 unblocked; downstream tasks unlock on each worker's own chain.

## Cycle 4 · 2026-10-30 10:50
Checked: git log (10 worker commits since 10:23); UNITY_STATUS, BLENDER_STATUS; logs/unity_compile_*.log (latest 0 error CS, 0 warnings); PlanetConfigTests.cs; Packages/manifest.json; asmdefs; Rendering assets; reports/unity/tests_2026-10-30.md; reports/blender/renders_2026-10-30.md; `git lfs ls-files` (18/18 PNG in LFS); contact sheets calibration, earth/surface, space/layer0, sun/surface; docs/credits/blender.md; logs/blender_2026-10-30.log.
Moved: U-001 → Done (add133b); U-002 → Done (886065c); B-001 → Done (4dd7922, 5d630d4); B-002…B-005 → Review (awaiting in-Unity lit check after U-005); U-003/U-004/U-005/B-006 → In Progress.
Decided: D-016 (Art .meta owned by UNITY); D-017 (mask override, topo+bathy, test asmdef split, settings path, Cinemachine 6.6.0). Contract → v1.1; Bible → v1.2. `tools/paths.json` rewritten with forward slashes (was invalid JSON, LEAD error; both workers had worked around it). `.gitignore` += `__pycache__/`. `warnings_baseline.txt` = 0.
Signals: none. Open EditMode failure ArtImporterTests.FrameSheetSlicedFromJson belongs to in-progress U-005, not a regression in accepted work. Note: DoD names `logs/compile_<date>.log`; actual is `logs/unity_compile_<timestamp>.log`, accepted.
User: none.
Queue: UNITY 12 Ready; BLENDER 11 Ready (fast pace, ~5 tasks/20 min: draft more art tasks next cycle if < 8).

## Cycle 5 · 2026-10-30 11:15
Checked: git log 10:52–10:55 (U-003…U-006, B-006); UNITY_STATUS, BLENDER_STATUS; reports/unity/tests_2026-10-30.md (EditMode 45/45, PlayMode 1/1); Build/MERIDIAN_0.0.1; ships__pilgrim__side_contact.png; `git lfs ls-files` (pilgrim 6/6 in LFS).
Moved: U-003 → Done (b6aae59); U-004 → Done (c5ba83a); U-005 → Done (bb0d201); B-006 → Review; U-006, U-007, B-007 → In Progress.
Decided: D-018 (Addressables path/groups, atlases, ship top size). B-002 handshake: import side passes; lit preview blocked on U-006.
Signals: U-006 three strikes (point Light2D not rendering in batch). Response: concrete approach in U-006 Lead notes (render via PlayMode test after 3 frames, no -nographics) and priority raised above U-007, since it gates closing B-002…B-006.
User: none.
Queue: added B-018 (six planet discs + Saturn rings), B-019 (Pilgrim landing legs), B-020/B-021 (Earth/Mars POI props), U-018 (legs swap). Ready: UNITY 11, BLENDER 14. Answered BLENDER proposals: paths.json fixed and __pycache__ ignored (cycle 4); legs → B-019.

## Cycle 6 · 2026-10-30 11:45
Checked: git log 11:13–11:32 (U-006, U-007, D-016 metas, B-007, B-008); UNITY_STATUS, BLENDER_STATUS; reports/unity/previews_2026-10-30.md; logs/preview_props_common_calibration.png and preview_ships_pilgrim_side.png (lit upper-right, OK); blender/preview/terrain__earth__grass_demo.png and terrain__mars__regolith_demo.png; tests_2026-10-30.md (EditMode 57/57; PlayMode 3/3 ×2 after two 2.3 ms / 20.4 ms failures under Blender load); tools/unity_test.ps1.
Moved: U-006 → Done (5a75d90); B-002 → Done (handshake complete); B-003…B-006 → Done; B-007, B-008 → Done; U-007 → Review (ortho-9 seam capture outstanding); U-008, B-009 → In Progress; L-007 → In Progress.
Decided: D-019 (chunk-apply measurement; UNITY had loosened its own test, now ratified with conditions); D-020 (blob index over RuleTile; 16 tile-46 variants; grass rim only on upward edges). Contract → v1.2.
Signals: worker changed an acceptance threshold without LEAD approval (U-007 test). Response: ratified as D-019 with a no-load condition; reminder that acceptance criteria change only through LEAD.
User: none.
Queue: added U-019 (Sprite_LitEmissive, P-08), U-020 (terrain variants), U-021 (test script runs LeadQA), B-022 (terrain revision). Ready: UNITY 13, BLENDER 13. Heavy lock held by BLENDER since 11:39 (fresh).

## Cycle 7 · 2026-10-30 12:15
Checked: git log 11:43–11:56 (U-007 evidence, U-008, U-021, B-009, B-010); UNITY_STATUS, BLENDER_STATUS; reports/unity/capture_earth_surface_2026-10-30.png (no seams at ortho 9); blender/preview/surveyor_frames.png; backgrounds__earth__layer2_contact.png; Bible §9.
Moved: U-007 → Done; U-008 → Done (f15f617); U-021 → Done (d185084); B-009 → Done (489a964); B-010 → In Progress (FAILED: cartoon-like flat tree silhouettes, §9 Forbidden; concrete 3D-tree approach in Lead notes); U-009, B-011 → In Progress.
Decided: D-021 (rig reach 5 m, no inventory check until M3, 64 pooled drops).
Signals: none. BLENDER queue reordered: B-022 (terrain revision), B-019 (legs) ahead of icons/props; B-023 (surveyor polish) added.
User: none.
L-007: tests written; run attempted 12:12, blocked by heavy_blender.lock (backgrounds/mars) — retry next cycle. Note: unity_test.ps1 takes the lock itself; LEAD must not pre-create heavy_lead.lock before calling it.
Queue: UNITY 12 Ready; BLENDER 13 Ready.

## Cycle 8 · 2026-10-30 12:45
Checked: git log 12:12–12:39 (U-007 seam fix, U-009, U-011, B-011 v1, B-022); UNITY_STATUS, BLENDER_STATUS; reports/unity/capture_space_2026-10-30.png, capture_earth_player_2026-10-30.png; blender/preview/terrain__earth__grass_demo.png (grass on upward edges only); tests_2026-10-30.md (EditMode 93/93; latest PlayMode run fails 5 tests on "no audio listeners" log from in-progress U-016, not from accepted commits).
Moved: U-009 → Done (089657b); U-011 → Done (d6831d4); B-022 → Done (fb0c1dc); U-016 → In Progress. B-011 v1 (flat silhouettes) stays in rework with B-010.
Decided: D-022 (Sun k_sun = 0.80; Mercury reachable with Mk1; Bible §4.4 → v1.3); D-023 (P-10…P-13: jetpack input, boost burn, HLSL shaders, fixed angles).
Signals: watch the "no audio listeners" PlayMode failures. If they persist in U-016's ready-for-review commit, it fails the console-clean check.
User: none.
L-007: not run; heavy_unity.lock active at 12:40. Retry next cycle.
Queue: added U-022 (k_sun, space background + glows). Ready: UNITY 10, BLENDER 11.

## Cycle 9 · 2026-10-30 13:15 · M0 exit review (L-008)
Checked: git log 12:44–13:04 (U-016, U-022, U-019); tests_2026-10-30.md (PlayMode 18/21 + 3 tool skips, LeadQA 1/1 ×4; EditMode 96/96); preview_ships_pilgrim_side_nopoint and calibration/sun nopoint previews (emission visible); capture_space_2026-10-30.png (stars, Milky Way, Earth glow).
Moved: U-016 → Done (37f9ed9); U-019 → Done (42988db); U-022 → Done (4fded11); L-007 → Done; L-008 → Done; U-010, L-009 → In Progress. USER-07 → Done.
M0 exit criteria (Bible §12), each with evidence:
- Repo verified, old build archived: `archive/meridian-v1` + tag `meridian-v1-final` pushed (cycle 1, D-009).
- Versions pinned: Bible §12 (L-005, D-013, D-014; Cinemachine cycle 4).
- Unity URP-2D project at root compiles clean: logs/unity_compile_20261030_130842.log 0 `error CS`, 0 warnings ≤ baseline 0; MERIDIAN_URP uses MERIDIAN_Renderer2D (cycle 4).
- render.py renders the calibration asset: B-002 (ead95f6), byte-identical re-render (renders_2026-10-30.md).
- ArtImporter imports it: U-005 (bb0d201), placeholder retired; lit preview OK (U-006, cycle 6).
- .claude/settings.json verified: L-004 (cycle 1).
- ≥ 5 Ready tasks per worker: UNITY 7, BLENDER 11 (this cycle). UNITY completes ~4 tasks/hour: L-009 drafts M2 UNITY tasks next cycle.
- USER_ACTIONS complete: USER-01…07 Done; USER-08 optional.
Decided: D-024 (M0 closed; Saturn jump 2.3 m, Bible v1.4).
Signals: BLENDER has no commit since 12:39 on the B-010 rework while In Progress (31 min, under the 90-min threshold; Blender is rendering).
User: none. M0_REPORT.md written (no playtest for M0).

## Cycle 10 · 2026-10-30 13:45
Checked: git log 13:11–13:31 (B-010/B-011 rework sources and first exports, B-012 generator, U-010, U-007 collider fix); UNITY_STATUS, BLENDER_STATUS; ShipSideTests.cs (6 tests + 1 rule test); tests_2026-10-30.md (EditMode 103/103, PlayMode 25/28 + 3 tool skips, LeadQA 1/1); free RAM 0.8 / 7.6 GB with two Unity processes (643 + 509 MB); 18 unity_compile logs since 10:35.
Moved: U-010 → Done (98091e0, 3707e5a); U-012, B-012 → In Progress.
Decided: D-025 (Pilgrim gear option b); D-026 (lock fairness + 1.5 GB memory gate; CLAUDE.md rule 6); D-027 (P-14/P-15).
Signals: resource starvation. UNITY held the heavy lock every 5–10 min; BLENDER's full exports deferred > 25 min; low-memory incident killed BLENDER's lock-watcher. Response: D-026, priority tasks U-023 and B-024.
User: none.
L-009: started. M2 UNITY drafts U-024…U-027 promoted to Ready to keep the queue ≥ 5. Remaining M2 drafts (Cryo meter, M2 POI placement, PlanetDisc real textures check) next cycle.
Queue: UNITY 11 Ready, BLENDER 11 Ready.

## Cycle 11 · 2026-10-30 14:15
Checked: git log 13:42–14:09 (U-012, U-023, U-013, B-012 partial, B-019 sources); UNITY_STATUS, BLENDER_STATUS; tests_2026-10-30.md (13:53 PlayMode 28/31 + LeadQA 1/1 clean; 14:08 BudgetGate failure belongs to in-progress U-014); memory: free 0.3 GB with UNITY's batch job (unity ×3 666 MB, Unity.DataStore 265 MB, Burst/compiler dotnet 318 MB), claude ×11 1.05 GB, Memory Compression 1.08 GB; Hub itself ~60 MB.
Moved: U-012 → Done (5fecaeb); U-013 → Done (e047727); U-023 → Done (d692fdb, e2ca48d); U-014, B-019 → In Progress.
Decided: scheduling action: LEAD filed `want_blender.lock` (14:11) for BLENDER's queued exports so UNITY yields after its current job. B-010/B-011 render jobs split per layer with ≤ 1.0 GB peak each (Lead notes).
Signals: BLENDER starved of the lock and memory for ~55 min (exports queued since 13:18). B-024 not yet done, so no want file had been written. Response above. If BLENDER still hasn't exported by cycle 12, LEAD will ask UNITY to pause heavy jobs for 30 min.
User: none (the Hub is ~60 MB; closing apps wouldn't free enough to matter).
Queue: UNITY 8 Ready, BLENDER 10 Ready.

## Cycle 12 · 2026-10-30 14:45
Checked: git log 14:09–14:32 (U-014, B-012 thruster/dig_sparks, B-019); UNITY_STATUS, BLENDER_STATUS (blocker + self-reported incident); perf_2026-10-30.md; contact sheets ships__pilgrim__side, side_legs, fx__thruster__base; free RAM 0.7 GB with UNITY's job.
Moved: U-014 → Done (a289721); B-012 → Done; B-019 → Done (f1eb426); U-015 → In Progress.
Decided: D-028 (split-half background renders, one-off 0.5 GB headroom in a scheduled window); D-029 (P-16 GC metric; P-17 → U-028).
Signals: the scheduler window worked (BLENDER exported FX + Pilgrim at 14:28–14:31). BLENDER self-reported a HeavyJobLock bypass at ~13:03 (36 s direct render while UNITY held the lock); UNITY's 13:02 and 13:09 runs both passed, so no impact. Acknowledged, no further action. `want_blender.lock` re-filed (the 14:11 one was older than 30 min).
User: none.
Queue: UNITY 8 Ready, BLENDER 10 Ready.

## Cycle 13 · 2026-10-30 15:15
Checked: git log 14:45–14:54 (U-015, B-010 re-export, B-011); UNITY_STATUS (U-028/U-020 written, verification waiting on memory), BLENDER_STATUS; blender/preview/backgrounds_earth_stack.png, backgrounds_mars_stack_full.png; locks (want_blender.lock 14:41 from LEAD, window used; want_unity.lock 15:09); free RAM 2.0 GB.
Moved: U-015 → Done (458709a); B-010 → Done; B-011 → Done; U-020, U-028, B-023 → In Progress.
Decided: B-010/B-011 accepted (§9 cartoon rule now passes); remaining polish split to B-025 rather than a second bounce (anti-loop).
Signals: none. LEAD deleted its own want_blender.lock (window finished) so UNITY gets the next turn.
User: none.
Queue: UNITY 6 Ready, BLENDER 10 Ready.

## Cycle 14 · 2026-10-30 15:45
Checked: git log 15:11–15:35 (U-020, U-028, Art metas, B-023 sources + self-rejected first render); tests_2026-10-30.md (15:36 EditMode 116/116, PlayMode 35/38 + LeadQA 1/1); perf_2026-10-30.md first-visible-frame rows; locks (heavy_unity 15:40 for U-017); free RAM 0.5 GB.
Moved: U-020 → Done (d455251); U-028 → Done (58b1375); U-017, L-010 → In Progress.
Decided: none.
Signals: none. BLENDER self-rejected its first B-023 render (bandage-like wrinkles, helmet shared the fabric) and fixed it before review. B-024 is partial (memory gate in the wrapper; want-file logic not yet marked done).
User: none.
L-010: M1LoopTests.cs written (no teleports after boot). Run deferred: UNITY holds the lock for U-017 and free RAM is 0.5 GB.
Queue: UNITY 7 Ready, BLENDER 10 Ready.

## Cycle 15 · 2026-10-30 16:15
Checked: git log 15:47–16:02 (U-017 M1 integration + build, U-018, B-023, surveyor metas); UNITY_STATUS (U-017 details), BLENDER_STATUS; tests_2026-10-30.md (15:55 PlayMode LeadQA 2/2 = SmokeTests + M1LoopTests first pass; 16:00 ShipSideTests 7/7 after a ±0.01 pivot fix); Build/MERIDIAN_0.1.0 contents; smoke_2026-10-30 screenshots (menu, Earth, ship, space); blender/preview/surveyor_v2_frames.png.
Moved: U-017 → Done; U-018 → Done; B-023 → Done; U-024, B-013 → In Progress.
Decided: B-023 accepted as v2 (no further polish without playtest evidence).
Signals: Build 0.1.0 predates U-018: on the ground the ship shows retracted gear and appears to float. Response: U-031 rebuild 0.1.1, priority.
User: none yet. M1 playtest request goes out after U-031 and the second M1LoopTests pass.
L-010: M1LoopTests 1 pass (15:55). Second run at 16:12 refused ("Unity Editor is running"). Retry next cycle.
Queue: UNITY 6 Ready, BLENDER 9 Ready.

## Cycle 16 · 2026-10-30 16:45
Checked: git log 16:16–16:30 (U-024 WIP, B-013/B-014 sources); UNITY_STATUS (U-024 hand-off interrupted by low memory), BLENDER_STATUS (exports gated on memory); Build/MERIDIAN_0.1.1 exists (16:38, U-031 not yet reported); input bindings in MERIDIAN.inputactions match Bible §6.
Moved: U-031 → In Progress.
Decided: none.
Signals: low memory again stopped a UNITY PlayMode batch (16:23). Free RAM swings 0.45–1.8 GB, and both workers are gated much of the time. Not a stall yet (both committed this cycle). Watch it.
L-010: M1LoopTests second pass 16:42 (LEAD ran it in a free window): touchdown 2.00 m/s, 55 s, clean console. Two passes now. M1_REPORT.md drafted (controls, what to try).
User: playtest request (USER-09) goes out after U-031's smoke check.
Queue: UNITY 5 Ready, BLENDER 9 Ready.
