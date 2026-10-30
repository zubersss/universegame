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
