# UNITY STATUS
Updated: 2026-10-30 11:00 · Session: 1
## Current task
U-007 Terrain v1 — starting (U-004/U-005 in review; building on them per "never wait"). Started 11:00.
## Last completed
U-006 WIP — 71c0b59 — `tools/unity_art_preview.ps1 <key>` writes logs/preview_<key>.png (calibration renders), but the upper-right point light doesn't contribute yet. 3 strikes, diagnosis below.
U-005 ArtImporter — bb0d201 — EditMode 45/45 (17 importer tests, one per contract §6 rule + key↔placeholder coverage). Calibration handshake: B-002's `props/common/calibration` holds the address in group `common`; placeholder entry retired automatically; no importer errors on BLENDER's real files.
U-004 Core scenes — c5ba83a — PlayMode 1/1 (Core loads Space inactive + PlanetSide Earth, g = −9.81, LogAssert.NoUnexpectedReceived).
U-003 scripts — b6aae59 — unity_test.ps1 proven both modes; unity_build.ps1 → Build/MERIDIAN_0.0.1/MERIDIAN.exe (177 MB dev build, 210 s).
U-002 PlanetConfig — 886065c. U-001 project — add133b.
## Next up
U-007, U-009, U-011, U-016
## Ready for review
U-001 (add133b), U-002 (886065c), U-003 (b6aae59), U-004 (c5ba83a), U-005 (bb0d201)
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
P-05: Give UNITY write access to `Assets/_Game/Art/**/*.meta` (+ `Assets/_Game/Art.meta`): the importer owns those settings and GUIDs; BLENDER keeps the PNG/JSON.
## For USER_ACTIONS
(none)
## HeavyJobLock
none
