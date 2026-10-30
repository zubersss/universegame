# UNITY STATUS
Updated: 2026-10-30 11:45 · Session: 1
## Current task
U-008 Dig and place with diffs — starting 11:45.
## Last completed
U-007 Terrain v1 — 2007876 — EditMode 54/54, PlayMode 3/3 (twice). Earth from Core: 25 chunks resident (5×5), never one beyond radius 2 while flying 200 m; avg frame 0.28 ms (batch, no rendering), chunk apply p99 0.88–0.91 ms, 1/400 frames over 2 ms (max 2.26–2.53 ms), worst frame 3.1–3.6 ms; 0 bytes GC over 300 settled frames. Real B-007/B-008 sheets in use. Seam check at ortho 9 still needs a rendered look (batch runs have no graphics): "visual check pending".
U-006 WIP — 71c0b59 — `tools/unity_art_preview.ps1 <key>` writes logs/preview_<key>.png (calibration renders), but the upper-right point light doesn't contribute yet. 3 strikes, diagnosis below.
U-005 ArtImporter — bb0d201 — EditMode 45/45 (17 importer tests, one per contract §6 rule + key↔placeholder coverage). Calibration handshake: B-002's `props/common/calibration` holds the address in group `common`; placeholder entry retired automatically; no importer errors on BLENDER's real files.
U-004 Core scenes — c5ba83a — PlayMode 1/1 (Core loads Space inactive + PlanetSide Earth, g = −9.81, LogAssert.NoUnexpectedReceived).
U-003 scripts — b6aae59 — unity_test.ps1 proven both modes; unity_build.ps1 → Build/MERIDIAN_0.0.1/MERIDIAN.exe (177 MB dev build, 210 s).
U-002 PlanetConfig — 886065c. U-001 project — add133b.
## Next up
U-009, U-011, U-016
## Ready for review
U-001 (add133b), U-002 (886065c), U-003 (b6aae59), U-004 (c5ba83a), U-005 (bb0d201), U-007 (2007876; seam visual check pending)
→ LEAD: U-005 ready for the calibration handshake (B-002 imports clean, address + placeholder retirement verified).
## Handoffs
→ LEAD: tools/paths.json has unescaped backslashes (invalid JSON); my scripts regex-read it. Please store `\\` or `/`.
→ LEAD: Cinemachine is bundled with 6000.6.5f1 as core package `6.6.0` (not 3.x); pinned that.
→ LEAD: Unity writes a `.meta` beside every file under `Assets/_Game/Art/` (it holds the GUID and the importer's settings). Nobody commits them yet. Proposal P-05 below.
→ BLENDER: keys are always 3 segments (contract §1). Single-variant assets use `base`, as icons do: `fx/thruster/base_color.png`, `characters/surveyor/base_color.png` + `base.json`. Creatures: key `creatures/earth/stag` → `Art/creatures/earth/stag_color.png` + `stag.json`.
→ BLENDER: character sheets at 256 px frames with 4 px gutters fit 2048 only up to 7 columns (8 × 256 + 7 × 4 = 2076). My placeholder uses 7 columns, 48 frames.
→ BLENDER: pivots from your manifest are read and applied (calibration y = 0.0555556 confirmed).
## Blockers
U-006 3 strikes — tried: (1) move/resize Light2D before Camera.Render, (2) render twice, (3) light fixed in the saved scene, sprite scaled to fit. Happened: global light (0.25) applies; the point light adds nothing; both target sorting layer Default. Best guess: in batch editor mode Light2D's mesh/culling is updated only in the editor player loop, so a manual Camera.Render sees no local lights. Next try (later cycle): render from a PlayMode test (real player loop), or EditorApplication.QueuePlayerLoopUpdate + a few frames before capture.
## Proposals
P-01: Tests are two asmdefs: `MERIDIAN.Tests.Unit` (Editor-only, EditMode) and `MERIDIAN.Tests.Play` (PlayMode) in Tests/Unit/Play/; Unity runs EditMode tests only from Editor-only assemblies.
P-02: URP global settings + default volume profile live in `Assets/_Game/Settings/Rendering/`.
P-03: Addressables config stays at its package-fixed path `Assets/AddressableAssetsData/` (DefaultObject location can't move); UNITY owns it. Groups: `common`, `space` (planets/*, backgrounds/space), `planet_<name>`, `icons`, `ui`.
P-04: Atlases are Sprite Atlas v2 files in `Assets/_Game/Settings/Atlases/`; placeholders join atlases and leave when retired.
P-06: U-007 asserts §11.1 "chunk apply ≤ 2 ms per frame" as ≥ 99% of streaming frames ≤ 2 ms plus "no hitch > 33 ms". Code plans bands against 1 ms; single OS stalls on the shared laptop (one 20 ms band seen once while Blender ran) can't be engineered away. LEAD: confirm, or name the measurement you want.
P-07: Autotiling uses plain Tiles + a precomputed 47-blob index (BlobAutotile.cs, computed on the worker thread) instead of RuleTile assets: RuleTile neighbor evaluation on the main thread doesn't fit the 2 ms budget. Same 47-tile sheets; layout in coordination/reports/unity/terrain_blob_layout.md (BLENDER already matches it).
P-05: Give UNITY write access to `Assets/_Game/Art/**/*.meta` (+ `Assets/_Game/Art.meta`): the importer owns those settings and GUIDs; BLENDER keeps the PNG/JSON.
## For USER_ACTIONS
(none)
## HeavyJobLock
none
