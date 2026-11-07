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

## Heavy job queue (LEAD rewrites it every cycle; D-109)

When the lock frees, the highest pending job here goes next, even if the other role's want is
older (D-037 alternation applies only between equal ranks). A rank is live only while its role
has a want on file or holds the lock (D-112): if the top rank has no want when the lock frees,
the next live rank runs now and the skipped role goes next after it files. A role below the top
keeps its want filed and refreshed (D-075) and works its `## While waiting` list. Cycle 266 (09:0x; UNITY holds the lock since 08:34 for C2 batch B's check: EditMode 348/349 at 08:34 (one BiomeFlora red), PlayMode A 52/56 at 08:36 and B 59/63 at 08:46, a re-run on the lock since 08:55; its status file is stale since 08:0x; BLENDER on code only). A role files its want only when the queue says it is next after the running job:
1. UNITY · the batch B re-run → the fixes for its reds (the BiomeFlora desert pick, the Sun spheroid test vs the new SunView, the wolf knock distance, the animated-object count with the camp Animators idle-off, the Warden single-frame rule) → the captures (the coast pool with the layers in order, forest and coast scenes, the plains by biome, the Sun in Space, the coast deep with the Maw) → the hand-off with status current; a profile -Probe for the boot row and the Creep row.
2. BLENDER · the gap after UNITY's lock, one measured run each (≤ 5 min total): the Venus deck re-run (~80 s), the Venus rig dry run, the UI scratch dry run, the Mercury export dry runs; the Jupiter flora preview.
3. UNITY · U-118 Mars (promoted when batch B is in) → B-142 + B-144 exports after its code → the Mars captures; then the Mercury batch (U-123 + B-148..B-150), C3 UI (U-124 + U-102 + B-151), Venus (U-125 + B-152..B-154).
4. BLENDER · B-155 Jupiter previews lock-free; B-156 the aerostat kit re-ink (designs) after.



















## While waiting (lock-free work; CLAUDE.md rule 3, D-109)

Rules: nothing here needs the lock; it stays under ~300 MB of extra RAM; no Unity Editor and no
`blender.exe` while the other role holds the lock or a want; pull from the top; write what you
did in your status before the next poll. LEAD tops each list up to ≥ 3 items every cycle.

**UNITY**
- Batch B (one hand-off, after hand-off 3): U-120 first (the cartoon-path cold boot 8.35 s with tile sheets 2.9 s: prefetch the pending keys behind the boot cover or start the clock at the scene's first frame, per the 0.4.1 run's LastLoadPending list), U-110 biome placement + the scene set by biome, U-111 ground strips incl. sand, U-116 the Sun rig, U-119 the Hadal Maw as a RigSet creature with `cycle_beats`, U-122 (the layer order below the datum, the bump flash, suit tiers as tints), the U-115 climb_in root move + hatch socket. Drafts outside Assets until the batch applies; one check (D-122 split).
- U-112's remainder: the Creep row on the 0.4.1 run (28.2 MB private per visit with 0 handles / 0 objects now): name the native growth from the next probe's breakdown; Done at ≤ 10 MB or a ruled info row.
- The C2 Earth capture set for the batch B hand-off: the coast pool with the layers in order, forest and coast scenes, the plains with the biome plants, the Sun in Space, the coast deep with the Maw and a shark.
- `docs/credits/unity.md` upkeep; the icon-coverage assert stays.
Then one batched check per hand-off when your turn in the queue comes (compile + EditMode as one lock, PlayMode A / B as two, D-122).




**BLENDER** (numpy / scripts only while UNITY holds the lock or a want; bpy only under your own lock; under 0.3 GB free, code only; otherwise one item per measured run beside the other role's job, under ~150 MB; the lock / RAM check is its own call)
- B-155: the first deck study's source (the cloud decks with wisps, the storm, the CRUSH band on layer2 lettered in Limelight), the Red Spot overlay, the creature drawing functions (the Belt wasp without a sting, the Vortex Whale rig-set parts); previews in the gap.
- B-156 the aerostat kit re-ink designs (aerostat deck / strut / cell, the two float cell packs, the grapple hook; Earth palette, no faces; sizes per the manifest rows; `replaces_v2`), previews when RAM allows.
- The four pending dry runs' scripts ready as one call each (the Venus deck re-run, the Venus rig, the UI scratch, the Mercury exports) so the gap costs ≤ 5 min.
- `c2_jupiter_designs.md` and README upkeep (the floe-cap frame layout, the shared kit).
















**LEAD**
- The charter idle list, plus: the C1 LeadQA scenario draft (pad → Escape Line → space → entry → touchdown under scripted input), the C1_REPORT skeleton, the owner's v4.1 look-over page, Bible gap closure, credits audit, a status-size check each cycle (D-113).

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

> **C0 STYLE TEST (D-086, owner, 2026-11-06). Read Bible §9 v4 and contract v3.0 §11 first.**
> The game is now a 1930s rubber-hose cartoon; combat is cancelled (D-087). Every open 3D and S1
> card below is Superseded (its code stays; move what you retire to `Assets/_Game/Archive/`, never
> delete). R1 closed (D-088): U-077 and U-086 Done on the 11:17 profile. Work the cards in this
> order; build against v3 placeholder sheets until BLENDER's land. Memory: no heavy job below
> 1.5 GB free (11:2x read 0.46 GB); close the Editor after every batch (D-091).

### U-093 · UNITY · Done · C0
Goal: Remove combat (D-087): move Parry, HitStop/HitStopClock, the Lance module, creature bite/bolt attacks, fight zoom, kill shake, health/damage on the player and creatures, and their tests (FeelPlayTests parry cases, U-092 fight-zoom prep) to `Assets/_Game/Archive/Combat/` excluded from compilation (an `.asmdef` with no platforms, or `~` folder). Replace with: `Bump` (0.8 m knock over 0.12 s + `bump` clip + dizzy-stars hook, no damage) from creature contact and hazards; hazards drain Suit power; at 0 `ConkOut` (iris-out, respawn at the last base or the ship, cargo kept). Rig slots: Beam, Survey, Builder, Grapple. Keep the air dash, StageCamera follow (minus fight zoom) and SquashStretch.
Accept: compile 0 errors, warnings ≤ baseline; no type named Parry/HitStop/Lance compiled; EditMode + PlayMode green incl. new `BumpTests` (knock distance, no meter other than Suit power changes) and `ConkOutTests` (Suit power 0 → respawn at the base with cargo kept); M1LoopTests unchanged; the 13 check-#4b failures are either archived with their feature or fixed.
Files: Assets/_Game/Code/Runtime/Player/, Creatures/, Camera/, Assets/_Game/Archive/Combat/, Tests/
Depends: —
Lead notes: Cycle 230. Lock-free code first; one batched check at hand-off. Cycle 231: the tree is clean after 96112df (11:43, the S1 leftovers committed as U-091 work; U-091 is C1 and waits). C0 comes first now: do the archive move as its own commit (moves only, no edits) and the Bump/ConkOut code in the next, so the archive diff is reviewable. Cycle 232: 24faf9f read (one commit, not two, but acceptable): 6 renames into Archive/Combat~, 21 added, 35 modified, 0 deleted; no Parry/HitStop/HitStopClock/Lance class left under Code/. Review completes on the batched check (compile, EditMode, the PlayMode filter in your status); run it on your turn after BLENDER's B-110 export. Cycle 234: check 1 (2ce211d, 15:07–15:14) compile 0 errors / 0 warnings, EditMode 265/267 with both reds fixed in the same commit; PlayMode not reached. Owed: the PlayMode run (BumpTests, ConkOutTests and the rest of your filter). Done on that run green. Cycle 235: DONE (5b04177, check 7 16:05–16:08: compile 0/0, EditMode 268/268, PlayMode 26/26 incl. BumpTests + ConkOutTests, tests_2026-11-06.md). Camera teleport snap and the post-jump airborne step logged as D-092/D-093; P-38 is U-099; the WardenPlayTests flake (1 of 4) stays on the watch list.

### U-094 · UNITY · Done · C0
Goal: The v4 2D render path for one Earth surface scene: orthographic side camera 16.875 m tall (PPU 64) keeping §5.1 follow rules; `ArtImporter` v13 for `style: v3` assets (contract §11.8: Sprite import at the json PPU, no mips, BC7, Sprite Atlas per planet ≤ 8, Animator clips at 12 fps from sheets, caps enforced); `SpriteCharacterView` for the surveyor and creatures driving those clips with a runtime flip and a squash root; a `ParallaxLayers` component for 3–5 painted layers from `<scene>.json`; v3 placeholder sheets (flat-colour blobs with an ink outline) at the same keys so the scene runs before art lands. The 3D renderer stays in the project for the archive only.
Accept: EditMode: importer rejects a sheet > 2048, a clip over its cap, fps ≠ 12 (tests); the surveyor placeholder walks at 12 fps (Animator sample rate asserted); parallax offsets match the json factors; PlayMode smoke `smoke_c0_earth` with `LogAssert.NoUnexpectedReceived()`; capture `reports/unity/c0_<date>/earth_c0_placeholder.png`.
Files: Code/Runtime/Camera/, Code/Runtime/View2D/, Code/Editor/ArtImporter.cs, Settings/, Placeholders/, Scenes/
Depends: —
Lead notes: Cycle 233: part 1 noted (2518faf, uncompiled: importer v13, SheetAnimatorBuilder, View2D, CartoonImportTests). One batched check covers U-093 + U-094 part 1 together; the smoke_c0_earth PlayMode test and the capture can follow in a second check with part 2. B-115's film overlays (af18479) and B-110's calibration_v3 sheet are in the tree for the importer tests. Cycle 234: part 2 noted (875bcb7: smoke_c0_earth + CaptureC0Earth). The real surveyor sheet is in (b5b1d29, Art/characters/surveyor/side, clips idle/walk/jump/land/look_camera): import it in the owed check, run CartoonSmokeTests, and capture earth_c0 with it rather than the placeholder. Done on the capture + green PlayMode. Cycle 235: DONE (5b04177; earth_c0_placeholder.png + README 16:08: ortho 16.875 m, three placeholder parallax strips, the real surveyor at ≈ 130 px with 12 fps clips; CartoonSmokeTests green with a clean console; importer v13 caps tested incl. the 8-atlas refusal). Terrain, props and the Pilgrim stay 3D in C0 by design; their cartoon versions are C1+ cards.

### U-095 · UNITY · Done · C0
Goal: One full-screen film pass (single shader, single blit, URP renderer feature): grain, vignette, drifting dust specks and hairline scratches from the three 512² tiled overlays (`fx/film/*`), brightness flicker ≤ ±2 %, warm/sepia grade; no Bloom, no volumetrics, HDR off. Settings → "Film effects" toggle (default on), saved in settings.
Accept: GPU cost ≤ 0.6 ms at 1080p in the profile; the toggle removes the pass (test); overlays imported 512² (test); before/after capture pair in the C0 report.
Files: Assets/_Game/Shaders/FilmPass.shader, Code/Runtime/Rendering/, Code/Runtime/UI/Settings/
Depends: — (placeholder noise overlays until B-115)
Lead notes: Cycle 236: ART + BUDGET ACCEPTED (7b00dab): earth_c0_film_on/off pair (warm grade, vignette, grain and dust subtle at 1080p, flicker ≤ 2 %); perf row "Film pass GPU · Earth" on 11.24 / off 11.62 ms = inside the 0.6 ms line; profile 16:43 compile 0/0; the toggle test passed on a real device at 16:31. OWED for Done: one tests_<date>.md entry run on the final code showing FilmTests 4/4 in EditMode and FilmPlayTests green (the report's last entry is 16:31, 1/2 with the cost test that since moved into the probe). Batch it with U-096's check; no separate job. Rulings: the 16:43 entry-transition red is a contention run (D-094), the 16:37 1.46 s stands; HDR off project-wide and the film pass on every Game camera are per Bible §9.4 (the 3D planets are superseded, their bloom with them); P-39 accepted, the pause-panel FILM EFFECTS button is the toggle until the settings panel card (Backlog U-102). Cycle 237: DONE (tests_2026-11-06.md 16:52 EditMode 275/275 incl. FilmTests 4, 16:53 PlayMode 0 failed with FilmPlayTests green; the Editor GPU-cost test skipped by design, the probe row holds the number).

### U-096 · UNITY · Done · C0
Goal: Iris-out / iris-in circle wipe as a cheap shader cutout (one quad, no texture), 0.35 s each way, centred on the surveyor (or the ship), used by launch, entry and area entry; the load runs while the screen is black.
Accept: TransitionTests: launch and entry stay ≤ 1.5 s with the iris included; an EditMode test for the radius curve; a 6-frame capture strip in the C0 report.
Files: Assets/_Game/Shaders/IrisWipe.shader, Code/Runtime/Transitions/
Depends: —
Lead notes: Cycle 237: DONE (d577013; check 16:52–16:55: compile 0/0, EditMode 275/275 incl. IrisTests, PlayMode 0 failed; TransitionTests launch 1.00 s / entry 1.07 s with the iris, the v3 white fades retired; iris_strip.png: 6 frames closing on the surveyor, 4 px soft edge; ConkOut uses it).

### U-097 · UNITY · Done · C0
Goal: Rubber-hose rig path for flora and props (contract §11.3): build sprite bones + skinning (Unity 2D Animation) from `rigset.json`; one texture and one animator controller per planet's set; sway idle on the planet beat, sampled stepped at 12 Hz; staggered start phases; face swaps (blink, yawn, giggle); react within 3 m (turn to look); the 40-animated-object cap with distant flora falling back to a 3-frame idle or a static frame.
Accept: RigFloraTests: 300 plants share 1 texture + 1 controller; ≤ 40 animate at full rate; phases differ; the react fires within 3 m; CPU ≤ 1.0 ms for 300 plants in the profile.
Files: Code/Runtime/Flora/, Packages/manifest.json (com.unity.2d.animation, pinned, logged), Tests/
Depends: —
Lead notes: Cycle 238: DONE (b71d396; check 17:55–17:59 compile 0/0, EditMode 279/279 incl. RigSetTests 4, PlayMode 15/15; RigFloraTests: 300 plants on 1 sheet + 1 controller, 40 full / 160 cheap, phases differ, react within 3 m, loop p99 0.74 ms ≤ 1.0; the C0 capture shows 48 B-112 snoozles around the camp; com.unity.2d.animation 16.0.1 pinned and credited). Two importer fixes on the way (slicer wiped rig parts; typed sprite-list probe) noted.

### U-098 · UNITY · Done · C0
Goal: Assemble the C0 style-test scene with BLENDER's art (B-111..B-115): the surveyor, one face plant (several instances), one critter, the painted 3-layer Earth background, the film pass, the iris transition from space; a 20 s capture video-strip and stills; profile it.
Accept: `reports/unity/c0_<date>/` with stills (idle, walk, jump/land, plant react, critter idle, iris mid-wipe, film on/off) and the profile: working set < 2.0 GB, 60 fps p99 ≤ 16.6 ms; PlayMode smoke green. LEAD then runs the §9.7 checklist per asset.
Files: Scenes/, reports/unity/c0_<date>/
Depends: U-094, U-095, U-096, U-097, B-111, B-112, B-113, B-114, B-115
Lead notes: Cycle 241: DONE (c114d7d; reports/unity/c0_2026-11-06/u098/ nine stills with logged facts, strip/contact_sheet.png, README; profile = the 18:4x gate run, Earth C0 rows green (763 MB, p99 9.62 ms, 38 Animators, 1 atlas); 18:5x check compile 0/0, EditMode 279/279, PlayMode 3/3 incl. LeadQA SmokeTests after the B-118 controller rebuild). LEAD's §9.7 pass per asset is in coordination/reviews/C0_STYLE_REFERENCE.md → C0 approved (D-099).

### U-099 · UNITY · Done · C0
Goal: P-38 (U-093 check 3): a fleeing or chasing creature that meets a wall it cannot climb (camp props, a cliff face) stops dead with its legs still running. In `CreatureDirector.Tick`: Flee turns away along the wall or hops a 1-tile step (reuse the Wander cliff turn); Chase waits at the wall and never bumps through it; the legs stop when the body does.
Accept: PlayMode `CreatureWallTests`: a wolf fleeing into the camp's crate stack turns or hops within 0.5 s and keeps moving; a chasing wolf blocked by a 2-tile wall stays put with a still idle; CreatureTests + WardenPlayTests unchanged (one check; note the Warden flake count).
Files: Assets/_Game/Code/Runtime/Creatures/CreatureDirector.cs, Tests/Play/CreatureWallTests.cs
Depends: —
Lead notes: Cycle 235. Lock-free after U-095; small. Report the WardenPlayTests result of every check until it passes 5 in a row. Cycle 238: DONE (b71d396; CreatureWallTests 17:56 green: fleeing stag turns in 0.32 s at the smelter, blocked chasing wolf idles with no bump; the 17:52 red was the stuck timer read from velocity, fixed 63f7f1e to position-over-time). The Warden flake was a real bug (sentinels moved by MovePosition from Update), fixed 1120920 → D-095; keep the 5-in-a-row count going (2 so far).

### U-100 · UNITY · Done · C0
Goal: Cartoon ground placeholder for the C0 scene so the style test reads cartoon edge to edge: a flat Earth-palette dirt strip with a thick ink top line and a one-tone grass lip (`Placeholders/terrain/earth/ground_strip.png`, 512×128 tile, PPU 64) drawn over the 3D terrain blocks on Earth while `CartoonStage.Enabled` (the blocks stay for collision and dig; the strip follows the dug column heights at 1 m steps). The camp props and the Pilgrim get a flat ink-outlined silhouette tint (one material swap, `ArtMaterials.Cartoon`), no new art.
Accept: `earth_c0_ground.png` capture with no 3D texture visible on the ground line; CartoonSmokeTests unchanged and green; TerrainTests (dig/place) unchanged; frame time avg ≤ 12 ms on Earth in the next profile.
Files: Assets/_Game/Placeholders/terrain/, Code/Runtime/View2D/GroundStrip.cs, Code/Runtime/Art/ArtMaterials.cs
Depends: U-094
Lead notes: Cycle 237. Placeholder only (BLENDER's painted terrain is a C1 card); keep it under 150 lines. Cycle 239: BACK TO IN PROGRESS, one failing check. Passed: check 18:05–18:08 (compile 0/0, EditMode 279/279, PlayMode 5/5 incl. TerrainTests), GroundStrip 98 lines, the silhouette tint on the props and the Pilgrim (985c4c6). Failing: "no 3D texture visible on the ground line" was meant as no block texture visible anywhere in the frame; earth_c0_ground.png (18:13) still shows the 3D dirt texture across the bottom ≈ 200 px under the 1 m strip. Fix: below each column's strip slice, fill down to the frame bottom with the strip's flat dirt tone (one quad per visible column, or one full-width quad behind the strips at the lowest visible column top, whichever is fewer lines), including dug columns (their walls get the same flat tone with the ink edge). Re-shoot earth_c0_ground.png; TerrainTests unchanged. Stay under 150 lines. Cycle 240: DONE (f4ad816; earth_c0_ground.png 18:38: flat dirt fill to the frame bottom cut from the strip sheet, ink edges down each step, the dug column shows a shaded flat back wall, no block or water texture anywhere; GroundStrip 113 lines; check 18:31–18:32 compile 0/0, EditMode 279/279, PlayMode 11/11 incl. TerrainTests).

### U-101 · UNITY · Done · C0
Goal: U-098 capture tooling ahead of the art: `SceneCapture.CaptureC0Strip` records the C0 scene for 20 s at 2 stills per second into `reports/unity/c0_<date>/strip/` plus a contact sheet (6 × 7 at 320 px), driving the surveyor through idle → walk → jump/land → walk past a plant anchor → look_camera; the profile gains the rows U-098 asks for (working set, p99 frame time, animated-object count ≤ 40, sprite atlases per planet ≤ 8).
Accept: the contact sheet and a profile with the four rows in `reports/unity/`; runs on the placeholder plant/critter keys so U-098 only swaps art in.
Files: Assets/_Game/Code/Editor/SceneCapture.cs, tools/unity_profile.ps1, Code/Runtime/Perf/BudgetMonitor.cs
Depends: U-094
Lead notes: Cycle 237. Lock-free code; one capture + profile when the lock is free. Cycle 239: code in (8147bcf: CaptureC0Strip, the Earth C0 leg in BudgetGateTests with the four rows, Species.Gull with one gull over the camp); its check, the contact sheet and the gate run are owed and can share the U-100 re-shoot job. Cycle 240: DONE (f4ad816; strip/contact_sheet.png + 40 stills over 20 s; perf_2026-11-06.md Earth C0 rows all green: working set 763 MB < 2.0 GB, frame avg 5.23 / p99 9.62 ms, 38 Animators ≤ 40, planet_earth atlases 1 ≤ 8, draw calls 155, 17.8 k triangles; BUDGETGATE GREEN). The v3 no-mips counting (bf947d8) is now Bible §11.1 wording. Species.Gull last in the enum, noted.

> **C1 (D-097, D-099; owner C0 feedback D-100..D-104, cycle 242).** C0 is approved with changes: thinner detailed ink, faces only on people and animals, an upright faceless Pilgrim, fully manual fuel-free flight. Order: U-107 (manual flight, the gameplay change) → U-091 → U-103 → U-105 → U-104 → U-106.

### U-103 · UNITY · Done · C1
Goal: Ship and space on v3 sprites: the **upright, faceless** Pilgrim (D-101, D-102) side and top views from BLENDER's sheets (B-122; an upright placeholder rocket until then) with thrust = stretch along the ship's up axis, cut thrust = squash (SquashStretch on the ship root), round puff exhaust from the tail as a 12 fps sprite FX loop (no particles), fins that wobble with tilt; the eight planet discs (B-119) as sprites with their character idle clips (no faces); the painted starfield + nebula cards (B-120) as parallax layers in the Space scene; the camera untouched; the physics is U-107's.
Accept: SpaceArtTests: every planet key resolves to a disc sprite (placeholders count) at its D-098 size; the exhaust loop runs at 12 fps from the tail socket; thrust stretch 1.15 / cut squash 0.9 along the ship's up axis (EditMode); a Space capture with every disc visible and a side capture of the upright ship on the pad and tilted in flight.
Files: Code/Runtime/Ship/, Code/Runtime/Space/, Placeholders/space/, Placeholders/ships/, Tests/
Depends: U-094, U-107
Lead notes: Cycle 238. Code on placeholders now; art swaps by key. Cycle 240: BLENDER's keys (contract §11.5, D-098): `planets/<planet>/disc` (sheet + json with `space_ppu: 3`, `radius_u`, idle clip 9 or 12 frames), Luna at `planets/earth/luna`, Saturn's rings as two static parts `planets/saturn/rings_back` / `rings_front` drawn behind / in front of the body with the wobble from `planets/saturn/disc_rig.json`; the starfield at `space/starfield` + 3 cards under `space/nebula/` with `starfield.json` parallax factors. Size the disc sprite from `radius_u` × PlanetConfig.visualRadius so a wrong scale is a test failure, not a look. Cycle 243 (BLENDER review fixes, a89f057; D-108): the starfield is the scene `backgrounds/space/starfield` with `layer0` a 2048×1024 tile repeating in x and y and `layer1..3` the nebula cards, `starfield.json` in the SceneLayout schema; SpaceBackdrop loads that scene (today it loads `backgrounds/space/layer{i}`). Saturn's `rings_back` / `rings_front` carry v3 sidecars (`space_ppu: 3`, pivot centre) so they import at the disc scale, not PPU 128: assert it in SpaceArtTests. Cycle 245 (D-111): the Pilgrim arrives as a rig set `ships/pilgrim/rig` (parts + bones + sockets, §11.3 schema) and a `puff` loop, not frame sheets: build it with the RigSetBuilder path, play the fin-wobble / leg-flex / hatch clips at 12 Hz, and keep tilt, stretch and squash on the root as U-107 already does; the exhaust puffs spawn at the tail socket. Until it lands, the stand-in stays. Cycle 246 (scout answers): (1) drop the atmosphere / cloud shells outright wherever a disc exists (the painted disc carries its own clouds); keep the existing glow sprite behind it. (2) The Sun keeps its lit spheroid, glow and kill-zone through C1 (no `planets/sun/disc` asset exists; a painted Sun is a C2 candidate). B-119 / B-120 are exported (24f8fbb) and accepted; B-122 exports in BLENDER's next batch with the schema it posted 22:3x (11 parts, 6 + 3 bones, 7 sockets, clips at 12 Hz): build the real rig from it, the stand-in until then. Cycle 247: code green (960af2f; SpaceArtRulesTests + SpaceArtTests: 9 discs, Saturn's rings 444 u across, the belt's 286 rocks, 8 glows). B-122's rig and puff are exported (f612225): build the drawn ship now (RigSetBuilder path; fin_wobble / leg_flex / hatch_open at 12 Hz; puffs from the tail_exhaust socket; tilt, stretch and squash on the root), then the Space capture (CaptureSpaceArt) and the side captures on the pad and tilted in the climb with the drawn ship. DONE on those captures. Cycle 254: DONE (60bedcf + 636bb59 + captures 55f5aa1; compile 0/0 with CheckSetup, EditMode 316/316, PlayMode as A 49/54 / B 56/63 / C 12/17 under D-122, every U-103 fixture green: ShipSideTests ×7, SpaceArtTests, U076SceneTests, TransitionTests, FlightPlayTests, CartoonSmokeTests; the remaining reds are D-124's, none from this card). Captures viewed (reports/unity/u103, 02:50–02:53, README evidence lines): the drawn Pilgrim upright on the pad beside the six Earth plants on the B-130 strips (rig 6 bones, fin_wobble, fx on rig), tilted −35° at 28 m with the tail puff and both attitude puffs, at the Escape Line with the line and sign; Space: Saturn with its painted rings, Jupiter, Neptune, the belt (286 rocks), Earth + Luna, and the top-down Pilgrim thrusting (rig fit 0.299). Two Space findings go to U-117 (the starfield repeat at the far zoom; point-filtered disc pixels near a body); they are polish on the scene, not this card's Accept.

### U-104 · UNITY · Done · C1
Goal: Cartoon HUD: Suit power, oxygen and the gravity readout as BLENDER's gauge sprites (B-121; placeholder dials until then), needles stepped at 12 Hz, a wobble on change; the ship HUD shows altitude, vertical speed, tilt and thrust-to-weight (no fuel anywhere, D-103); the Escape Line as the hand-painted dotted line with its little sign (B-121) replacing the band; fonts per D-090 (Limelight titles, Patrick Hand HUD, OFL.txt beside each, credited).
Accept: MenuHudTests: the three gauges track their meters within 1 % at the 12 Hz step; no HUD element, panel or string mentions fuel (test greps the UI prefabs and strings); the Escape Line sign sits at the line's altitude; fonts load from the project (test); a HUD capture at 1080p.
Files: Code/Runtime/UI/HUD/, Assets/_Game/Fonts/, docs/credits/unity.md
Depends: U-094
Lead notes: Cycle 238. The current HUD stays until the swap is complete; one commit. Cycle 243 (BLENDER handoffs, a89f057): (a) ArtImporter ignores a single image's sidecar `pivot`; `ui/hud/escape_sign` needs `[0.5, 0]`, so honour the sidecar pivot for single sprites (importer test); (b) `ui/hud/gauges` is one sheet with `parts` (rects bottom-left + pivots, rig-set style) and `needles` `{min_deg, max_deg, hub, danger_below}`: slice it into its 6 sprites with the rig-set slicer and drive each needle from its json range; `escape_line.json` carries `"tile": true`. Cycle 246: the Escape Line sign arrives blank from B-121; UNITY draws ESCAPE LINE on it in Patrick Hand (TMP, the D-090 font) so the lettering is runtime text; the importer half (sidecar pivot, parts slicing) is already written per UNITY's 22:4x status. Cycle 247: importer half green (960af2f). B-121 is exported (f612225): do the swap now (the six gauge parts + needles from `ui/hud/gauges.json`, needles stepped at 12 Hz, the dotted `escape_line` tile at the line's altitude, the blank `escape_sign` lettered ESCAPE LINE in Patrick Hand, Limelight + Patrick Hand with OFL.txt and credits), the ship HUD rows (altitude, vertical speed, tilt, thrust-to-weight) with it, and the 1080p capture. DONE on that capture + MenuHudTests. Cycle 255: the C1 batch check is running: compile clean, EditMode 324/326 at 03:10 (HudGaugeTests needle settle, the U-117 FullRect assert) → 326/326 at 03:15; PlayMode A on the lock since 03:16 (0.4 GB free with the Editor at 1.16 GB). Done on the hand-off with the 1080p HUD capture and MenuHudTests green. Cycle 256: PlayMode A 50/54 (03:16; two batch reds: the BackdropTests layer check under the depth bands, the old Escape Line band left enabled by the painted branch), B 61/63 (03:40; one: the RigFlora react squash on its first frames), the focused re-runs 7/8 (03:48) then 6/6 (03:51): all three fixed in the tree; captures running from 03:53 (u104 HUD shot, u109 re-shoot on the lock 03:54). Done on the hand-off commit with the 1080p HUD capture. Cycle 257: HUD capture viewed from disk (reports/unity/u104/hud_1080p.png, 04:21, uncommitted): the three painted dials with needles top-left read as the B-121 art at 1x; the surveyor, plants and the Pilgrim rig beside the grey stand-in props. To confirm in the hand-off: the faint thin rows under the dials and at the top-right (readouts, item counts, a 1390 m marker) look like the legacy HUD at low alpha rather than Patrick Hand; if legacy, hide or restyle them in the U-106 batch (the Accept's font clause). Done on the hand-off commit with HudGaugeTests + MenuHudTests green and that answer. Cycle 257 (04:4x): DONE (0b4af5a, 174 files; EditMode 326/326 at 04:08 with HudGaugeTests (sheet parse, the 12 Hz needle, the no-fuel grep, the theme faces) and MenuHudTests; PlayMode A / B / re-runs green by 03:51 with the painted-line fix; captures reports/unity/u104/hud_1080p.png + hud_escape_line.png viewed: three painted dials with needles, the Escape Line tile and the sign lettered in Patrick Hand). The faint rows are Patrick Hand washed out on the bright sky, not legacy (the legacy bars are off once the gauges arm); an ink shadow under the face and the row positions are coded for the U-106 batch's re-shoot.

### U-105 · UNITY · Done · C1
Goal: Surveyor full Animator at 12 fps: every clip on `characters/surveyor/side` (incl. B-116's and the C1 dig, build, surprise, jetpack, climb_in once BLENDER adds them) wired to the controller states with stand-ins for the missing ones; eye-pop (surprise) and smear hooks (dash) as animation events; the SpriteCharacterView flip and squash root unchanged.
Accept: SurveyorAnimTests: each controller state resolves to a real clip or a named stand-in (listed in the report); events fire on the right frames (EditMode); CartoonSmokeTests green.
Files: Code/Runtime/View2D/SpriteCharacterView.cs, Code/Editor/SheetAnimatorBuilder.cs, Tests/
Depends: U-094
Lead notes: Cycle 238. Small; the builder already does most of it. Cycle 247: DONE (960af2f): SurveyorAnimTests in EditMode 307/307 (the C1 pick order, the stand-in table logged: 10 real, 10 stand-ins; events on surprise frame 0 and dash 0 / last); CartoonSmoke green 23:04 and 23:32; AnimationEventRelay feeds the EyePop / Smear hooks. The stand-ins resolve to real clips as BLENDER draws them (C2).

### U-106 · UNITY · Done · C1
Goal: C1 exit measurement: the Space scene and the Earth → Space → Mars loop on the new art profiled against D-089 (working set < 2.0 GB, warn 1.7; textures ≤ 512 MB; ≤ 8 atlases per planet; ≤ 40 animated objects); `M1LoopTests` pass with the v3 art and the manual, fuel-free flight (U-107); `reports/unity/c1_<date>/` with the Space capture set and a 20 s flight strip (pad → Escape Line → space → entry → touchdown, all under scripted player input).
Accept: perf rows green for Space, Earth, Mars; M1LoopTests 2 runs green; the report.
Files: reports/unity/c1_<date>/, tools/unity_profile.ps1
Depends: U-091, U-103, U-104, U-105, U-107, B-119, B-120, B-121, B-122, B-124, B-125, B-126, B-127
Lead notes: Cycle 238. Last C1 card; LEAD writes C1_REPORT.md on it. Cycle 242: depends on U-107 and the v4.1 re-inks too. Cycle 249 (D-114, D-116): the profile runs the 11-leg route with the Earth (warm) leg; the Return rows judge private commit within 10 % with working set as info; the `Creep per visit` row is info in this report (U-112 fixes it after); the atlas row prints the resident ≥ 1024² sheet count per planet (D-110 (2)); the worst iris-in frame per transition is listed and the 141–250 ms Earth-entry frames explained (hidden under the closed iris, or not); the boot load breakdown (4.80 s today) stays in. U-091 is Done, so the remaining dependencies are U-103, U-104, U-109 and the C1 art imports. Cycle 259 (05:4x): DONE (8e9eea0d, 94 files). Build/MERIDIAN_0.4.0 (556 MB, 103 s); perf_2026-11-07.md 158 rows: 104 green, 30 info, 6 n/a, 1 red; frame time p99 Earth 9.82 / Space 6.41 / Mars 7.20 / storm 10.75 / Mars FX 13.08 / Earth C0 13.01 ms; the 11-leg dev-build probe: working set peak 966 MB, private 1314 MB, textures 318 MB (all under 2.0 GB / 512 MB), Return · Space after Mars +8.8 % (re-run +9.8 %), Return · Earth again +8.6 % (+7.3 %) on private commit, Boot → warm +37 / +27 MB, Creep per visit 26 MB (info: 16 handles + 22 GameObjects per visit → U-112), transitions 0.72–1.05 s, planet loads 0.86–1.78 s warm; the red: Planet load · Earth at boot 5.53 s cold and 5.44 s on the D-129 warm re-run (the boot path, not the cache → U-120 first in C2 batch A); M1LoopTests 1/1 twice (04:53, 04:55); the 20 s flight strip (40 stills over 53.6 s, contact sheet viewed: pad → climb → Escape Line → launch iris → Space with the Earth disc → entry iris → descent → touchdown 2.55 m/s); the c1 README with items 1–7 and the near-range limit. C1 CLOSED on it (D-131).

### U-107 · UNITY · Done · C1
Goal: Manual, fuel-free flight (D-102, D-103; Bible §4.3, §5.2, §5.3, §6 v4.1). (1) `SideShip` becomes an upright rocket: thrust acts along the ship's up axis (W or Space held), A/D tilt up to ±35° with a spring back to upright on release, real planet gravity pulls it down, so it hovers where thrust = g, climbs above, sinks below; legs at the tail; the Mk class decides the thrust (12/20/35 m/s², §4.3), nothing else limits it. (2) All fuel is removed everywhere (D-103, D-105: launch fuel and skip fuel alike): `PlanetConfig` fuel fields, the launch burn, tanks, HUD fuel, refinery fuel recipes and any skip-fuel item, recipe, icon or string (move to `Assets/_Game/Archive/Fuel~`), the perchlorate "halves fuel" effect; the EditMode fuel-formula test becomes a thruster-class-per-planet test (§4.1 column); a test greps strings and prefab names for "fuel" and finds none outside the Archive. (3) Control never leaves the player: no input lock in §5.2/§5.3, no auto-launch; the iris is cosmetic; held inputs carry across the scene switch (a held thrust key keeps thrusting in space; the top-down controls are live on the first visible frame); the entry places the ship upright at Escape Line + 20 m descending 15 m/s with side controls live at once. (4) Landing rules §4.3 unchanged (≤ 6 m/s clean); the ship tips over if it touches down tilted more than 20° (no damage, it rights itself over 0.5 s with a wobble).
Accept: `FlightTests` (EditMode): hover at thrust = g on all 8 planets within 1 %; Mk1 cannot climb on Jupiter, Mk3 can; tilt clamps at 35° and springs back; no symbol named LaunchFuel/FuelTank/LaunchBurn compiled. `FlightPlayTests` (PlayMode): from rest on the Earth pad, holding thrust from frame 0 crosses the Escape Line with no input lock at any frame (an input probe asserts every frame accepted input through both transitions); the held key is still thrusting on the first Space frame; entry → manual touchdown ≤ 6 m/s under scripted input; `TransitionTests` still ≤ 1.5 s; `M1LoopTests` rewritten for no fuel and green twice; clean console.
Files: Code/Runtime/Ship/SideShip.cs, ShipLegsView.cs, ShipHud.cs, Code/Runtime/Transitions/, Code/Runtime/Planets/PlanetConfig.cs, Archive/Fuel~/, Tests/Unit/FlightTests.cs, Tests/Play/FlightPlayTests.cs, Tests/LeadQA/M1LoopTests.cs (LEAD's file: send the diff in your status; LEAD applies it)
Depends: U-096
Lead notes: Cycle 242. First C1 card: it is the owner's gameplay change. Keep the top-down flight model as is (§4.4). The side camera follows the ship with the §5.1 rules; look-ahead points along the velocity. One batched check at hand-off; a side capture of the ship on the pad, tilted mid-climb, and at the Escape Line. Cycle 245: LANDED, NOT YET READY (460d126, pairs with b930bcd): check 21:14–21:28 compile 0/0, EditMode 287/287 (FlightTests incl. six no-fuel sweeps), PlayMode 40/40 (M1LoopTests twice, M1Integration); input probe: W held from frame 0 over 39,286 frames with no input gap, thrust still on in the first Space frame, launch 0.70 s, entry 0.80 s, key-driven touchdown 2.55 m/s. Owed before review: the climb capture shows the camera staying on the pad (vehicle snap centres the hull, the per-frame step does not follow) → fix + re-shoot; a white quad where the gull spawns (goes with U-108's import of B-127). Batch both with U-108's check. Cycle 247: DONE (460d126 + 960af2f). The climb camera's root cause was CartoonStage switching the side camera's object off (PlanetBackdrop lives on it), so CameraFollow never ticked; fixed, and u107/2_tilted_climb + 3_escape_line re-shot 23:14 with the camera on the hull (35° lean, flames). The gull quad went with U-108's late-sheet fix. Tests: EditMode 307/307 (23:31), PlayMode green in every set 22:53–23:32 incl. M1LoopTests (23:17). Seen in the climb shots and carried to U-109: above the painted sky the frame is the camera's flat clear colour.

### U-108 · UNITY · Done · C1
Goal: Rig sets v3.1 and the re-inked C0 set in the scene: `RigSet` reads BLENDER's B-126 schema additions (`replaces_part` swap slots that substitute a part, and an idle `swap_cycle` that steps a swap on the beat) so the faceless snoozle opens and shuts its head and lifts its leaves; import the v3.1 re-inks as they land (surveyor B-125, gull B-127 with `fly` wired to the gull's airborne state, snoozle B-126, calibration); re-shoot the nine C0 stills into `reports/unity/c0_<date>/v41/` for the owner's second look-over.
Accept: RigSetTests cover `replaces_part` and `swap_cycle` (a swap steps once per beat, a replaced part is hidden); the snoozle v2 loads with no importer error and 48 instances run in the C0 scene; the gull plays `fly` while airborne (test); the nine v4.1 stills + README; CartoonSmokeTests green; the Earth C0 perf rows still green.
Files: Code/Runtime/Flora/RigSet.cs, FloraRigs.cs, Code/Editor/RigSetBuilder.cs, Creatures/, reports/unity/c0_<date>/v41/
Depends: U-107, B-126
Lead notes: Cycle 243. After U-107's check and before U-091: the owner is waiting on these pictures. The surveyor and gull sheets keep their indices, so only the rig schema needs code. Cycle 247: DONE (960af2f; the nine stills 23:15 in reports/unity/c0_2026-11-06/v41/ + README; tests_2026-11-06.md 22:45–23:33: EditMode 307/307, every PlayMode set green after the settle-race fix (CartoonSmoke walk → fall: IsSettled now needs the first streaming pass); RigSetTests + RigFloraTests (300-plant loop p99 0.195 ms) + CreatureTests.GullFliesWhileAirborne; animator addresses 13/13 after the delete-and-recreate fix; BudgetGate Earth p99 11.6 ms). The stills show thin ink, 48 faceless snoozles stepping head_open → half → closed on the beat, the gull in `fly`, the iris and film as before; the ship is the grey stand-in until the B-122 rig goes in (U-103). Owner look-over page updated (USER-24). Accepted leftovers (While-waiting): react `turn_bounce` gets its bounce (a root squash on react); `FloraRigs.CycleClockOffset` becomes internal.

### U-109 · UNITY · Done · C1
Goal: Climb sky. Above the painted plains sky the side camera shows its flat clear colour (u107/2 at 400 m, u107/3 at the Escape Line), which the player sees on every launch. Put a vertical gradient behind the parallax layers that starts at layer0's top-row sky colour and darkens to the Bible's space black by the Escape Line, with the B-120 starfield (`backgrounds/space/starfield/layer0` at low alpha) fading in over the last third of the climb; the reverse on entry; per planet from PlanetConfig's sky colour (Mars butterscotch; Mercury black from the ground).
Accept: side captures at 0 m, half-way and at the Escape Line show no flat band or seam between the painted sky and the gradient; stars visible at the Escape Line; FlightPlayTests and TransitionTests green; no new texture (a gradient built in code or a vertex-coloured quad); the Earth perf rows unchanged.
Files: Code/Runtime/Planet/PlanetBackdrop.cs, Code/Runtime/Planet/Backdrop/StageLayers.cs, Tests/
Depends: U-107
Lead notes: Cycle 247. Found in the U-107 climb re-shoot; it goes before U-106's flight strip because the owner flies this climb every launch. Code only, no BLENDER sheet; the C2 Earth backdrop pass may later paint the upper sky, and this gradient stays underneath it. Cycle 250: Files line amended on UNITY's scout (00:5x): the Earth climb runs on the cartoon path, so the gradient lives in View2D/CartoonStage + a new ClimbSky component behind ParallaxLayers (not PlanetBackdrop / StageLayers); layer0's top-row colour read once per scene load from the texture; no new asset. Accepted. Cycle 251: P-43 ruled D-118: the gradient is cartoon-path only; Mars and Mercury get it when they convert to the cartoon stage (C2), no `_Climb` uniform in SideParallax. Check running 01:06–; EditMode 316/316 at 01:16 on the third run (RigSetTests against the six-plant B-129 set). Cycle 254: LANDED, NOT YET READY (60bedcf; ClimbSkyTests ×3 + ClimbSkyPlayTests green; captures reports/unity/u109 02:54–02:55: half-way = the gradient, Escape Line = stars + the line). FAILS the Accept's seam clause: reports/unity/u103/2_tilted_climb.png (02:51, low altitude) shows a flat band of a different tone above the painted sky with a hard horizontal edge at layer0's top row, which the owner sees on every launch. Fix in the C1 wiring batch: take the sky tone from the top row's median with the cloud pixels excluded (or the top-left sky sample), and feather the gradient's bottom over layer0's top 2–3 m so no edge exists at any altitude; re-shoot u109/1_ground and a low-altitude climb shot. Done on that re-shoot. Cycle 257: re-shoot viewed from disk (reports/unity/u109/2_climb_28m.png, 04:21, uncommitted): the hard band is gone, the painting continues upward. New defect: the mirrored top metre repeats as rows of faint symmetric pale shapes across the upper 15 % of the frame at 28 m (a wallpaper read). One more short pass in the U-106 batch: blur the sampled band vertically over 2–3 m or sample a cloud-free stretch and jitter the mirror phase per strip so no repeat reads; re-shoot the 28 m frame. Done on that frame. Cycle 259 (05:5x): DONE (e6e515b5: both climb strips bind a white texel, ClimbSkyPlayTests asserts it; reports/unity/u109/2_climb_28m.png 05:31 viewed: the painting fades into the shade over its top 1.5 m with the flat sky above, no streak, lattice, band or line; 4_escape_line frame top #020205 with the stars at 0.60). Every C1 card is now Done except U-117 (2) and U-112, which ride C2 batch A.

### U-121 · UNITY · Done · C1
Goal: The cartoon path on by default (D-132, P-48): `CartoonStage.Enabled` defaults to true; tests that need the 3D path on Earth set it false and restore it, tests that set it true restore the previous value; a cartoon-path guard (no 3D scenery, region bands or depth bands configured while the cartoon stage runs) with a PlayMode assert; M1LoopTests ×2 on the cartoon path; one profile -Build re-run (the 11 legs with the D-116 rows, the pending-keys breakdown for the boot row) producing Build/MERIDIAN_0.4.1; the C1 Earth dev-build rows in `coordination/reports/unity/c1_2026-11-07/README.md` replaced by the re-run's.
Accept: the build boots Earth on the cartoon stage (a PlayMode assert and the build's first-frame log line); M1LoopTests 2 of 2 green on the cartoon path; the profile's Earth rows re-measured and green (the boot row's result reported either way, U-120 owns it if red); Build/MERIDIAN_0.4.1 plays; no capture changes needed.
Files: Code/Runtime/View2D/CartoonStage.cs, Code/Runtime/Planet/, Tests/, tools/unity_profile.ps1
Depends: U-106
Lead notes: Cycle 259 (05:5x, D-132). First in C2 batch A; the owner's playtest (USER-26) waits for 0.4.1. If the loop tests fail on the cartoon path, stop and report: C1 reopens in full. Cycle 261: step 1 EditMode 338/339 (the PropSpriteTests wall row, D-125), step 2 M1LoopTests 1/1 ×2 on the cartoon path (05:58, 06:01: C1 stands, D-132 (4)); step 3 the halves A 44/54 and B 53/63 with 17 reds, ruled D-133: five regressions to fix (the ResidencyTests planet_earth holder `terrain/earth/ground_strip`, the wolf's bump → idle, the two CreatureTests nulls on the sheet path, the ClimbSkyPlayTests edge assert), the InnerCreatureTests timing re-measured at good RAM, and the 3D-path tests set explicit, rewritten to the cartoon equivalent or retired per the D-133 table. Then the captures, the profile -Build, 0.4.1. Cycle 262 (07:1x): LANDED (ae7b8cfc: the default flip with test restores, the cartoon-path guard, the D-133 pass applied; M1LoopTests 1/1 ×2 on the cartoon path; EditMode 339/339; the GroundStrip handle leak fixed). Two reds stay open for hand-off 3: InnerCreatureTests' worst AI frame (7.6 / 4.2 / 4.7 ms in three runs against ≤ 1.0, median 0.04 ms: one outlier frame per 300 on the 3D-path Mercury creatures; a Profiler marker goes on it) and SurveyorAnimPlayTests' dig (the drawn surveyor dug the tile under its own foot and read `fall`; the test now digs a tile ahead). Done on hand-off 3: the profile -Build (the C1 Earth rows + the boot row on the cartoon path), Build/MERIDIAN_0.4.1, the two reds green or ruled. Cycle 263: the cartoon-path profile (07:14–07:24, 155 rows: 101 green, 30 info, 6 n/a, 1 red) read lower than the 3D path (working set peak 848 MB vs 966, private 1291 vs 1314, textures 322 MB; Return rows +7 % / +9.6 %; Boot → warm +32 / +46 MB; Creep per visit 28.2 MB private with 0 handles / 0 GameObjects now; Earth p99 9.39 ms, Space 7.42, Mars 9.31) with the red at Planet load · Earth at boot 8.35 s cold (tile sheets 2878 ms) → U-120's cartoon-path number; the probe now prints the pending keys when the terrain settles. The build was still named 0.4.0 (the bump is in the tree): the 0.4.1 rebuild runs after the re-shoots. Cycle 263 (07:5x): DONE (a2c5b4df; Build/MERIDIAN_0.4.1 at 07:45, 559 MB; the version now written from GameInfo.Version; M1LoopTests 1/1 ×2 on the cartoon path; the dev-build profile: working set peak 863 MB, private 1298, textures 322 MB, Return · Space after Mars +9.9 %, Return · Earth again +9.6 %, Boot → warm +2 / +37 MB, Creep 28.5 MB with 0 handles / 0 objects; Editor frame time Earth p99 10.5–10.8 / Space 4.6 / Mars 8.7 ms; the c1 README's row 6 replaced). The boot row 5.70 s (red; the cause settled: the terrain's first settle, not sheet loads → U-120 re-scoped, D-136). Two Editor rows red (transition entry, animated objects) ruled in D-136; two test reds (the surveyor's dig lookup, found; the InnerCreature p99 right after a build) go to batch B's first lock.

### U-112 · UNITY · Ready · C1
Goal: Per-visit memory creep (D-116): `MemoryProbe` prints per leg the Mono heap (`Profiler.GetMonoUsedSizeLong` / `GetMonoHeapSizeLong`), the native allocator totals (`Profiler.GetTotalAllocatedMemoryLong`, `GetTotalReservedMemoryLong`, `GetTotalUnusedReservedMemoryLong`) and the counts that can grow per visit (Addressable handles held, pooled chunks, live GameObjects, TMP objects, audio sources); `unity_profile.ps1` adds the `Creep per visit` row = (private at the last leg − private at Earth (warm)) / planet visits; then find and fix the top source of today's ≈ 15 MB per visit.
Accept: the 11-leg probe shows Creep per visit ≤ 10 MB and both Return rows within 5 % on private commit; the report names the source and the fix; no gameplay test changes.
Files: Code/Runtime/Perf/MemoryProbe.cs, Code/Runtime/Perf/BudgetMonitor.cs, tools/unity_profile.ps1, Tests/
Depends: U-106
Lead notes: Cycle 249. The instrumentation half is lock-free and sits on your While-waiting list so U-106's own profile already prints it; the hunt and the fix run after U-106 so the C1 build is not held for a 15 MB-per-visit creep that reaches the 1.7 GB warning only after dozens of planet visits. Cycle 263: the 0.4.1 run shows 28.5 MB private per visit with 0 Addressable handles and 0 GameObjects per visit (the region-band loads are gone, D-132); the remainder is native growth: the next probe's breakdown names it. The InnerCreatureTests p99 spike (GC gen0 at ~46/s; DiscSprite's per-frame camera search removed) joins this hunt if it holds at good RAM.


### U-115 · UNITY · Done · C1
Goal: Two-sheet surveyor (D-121): the surveyor's controller takes clips from `characters/surveyor/side` and `characters/surveyor/side_b` (B-134: dig, build, surprise, jetpack, climb_in; same frame size, pivot and PPU; clip names unique across the two); `SpriteCharacterView` swaps the texture with the clip; U-105's stand-ins for those five resolve to the real clips once `side_b` imports; both sheets in the Earth atlas count (D-110 (2)).
Accept: SurveyorAnimTests: with a stand-in `side_b` json every state resolves and the five clips play their own frames (EditMode); with B-134 imported, the stand-in table shows 0 stand-ins for dig / build / surprise / jetpack / climb_in; CartoonSmoke green; the Earth perf rows unchanged.
Files: Code/Editor/SheetAnimatorBuilder.cs, Code/Runtime/View2D/SpriteCharacterView.cs, Code/Runtime/Player/, Tests/
Depends: U-105
Lead notes: Cycle 251 (D-121). Code half lock-free (While-waiting #5) so B-134's export drops straight in; the check rides your next batch after U-104. Cycle 253: B-134 is exported (27143e1): `side_b` plays by clip name; climb_in moves the root up the fin-leg over frames 0–7, then the sheet's `hatch` socket (1.0, 1.05 m from the pivot, every frame) sits on the Pilgrim's door socket; the five stand-ins resolve on import. Cycle 257 (04:4x): DONE (0b4af5a; SheetAnimatorBuilder puts side_b's five clips on the `side` controller, the controller rebuilt with them at import; SurveyorAnimTests bind dig / build / surprise / jetpack / climb_in to side_b's drawings, EditMode 326/326; CartoonSmoke green in the batch). Owed in the C2 Earth batch (on the While-waiting list): the climb_in root move up the fin-leg and the `hatch` socket on the door socket.

### U-117 · UNITY · Done · C1
Goal: Space view polish from the U-103 captures: (1) the starfield repeats as a visible column pattern at the far zoom (`reports/unity/u103/space_1_saturn.png`): the starfield tile's world scale follows the camera zoom so one tile never covers less than half the frame (or the layer draws in screen space with its 0.05 parallax); (2) near a body the disc shows point-filtered pixel steps (`space_6_pilgrim.png`, Luna at ≈ 10×): planet disc sprites import with bilinear filtering (ArtImporter, `planets/*` only; frame sheets stay point), and the near-range disc size rule is noted for C2.
Accept: re-shot space_1 and space_6 with no visible repeat and no pixel steps on the disc; SpaceArtTests green; the Space perf rows unchanged.
Files: Code/Runtime/Space/SpaceBackdrop.cs, Code/Editor/ArtImporter.cs, Tests/
Depends: U-103
Lead notes: Cycle 254. Found on the U-103 Space captures; the owner sees both on every flight. Rides the C1 wiring batch with U-104. Cycle 255: fix amended on UNITY's scout: the disc textures already import bilinear (luna filterMode 1); the stairs at 10× are the Tight sprite mesh cut along the alpha at texel steps, so planets/* discs import on a FullRect mesh (sheets stay Tight) and the starfield tile period = max(native, frame / 2) (SpaceBackdrop.TilePeriod, pure, tested). SpaceArtRulesTests.PlanetDiscsImportBilinearOnAFullRectMesh red at 03:10, green at 03:15. Done on the two re-shoots. Cycle 257: re-shoots viewed from disk (04:00, uncommitted): (1) FIXED, space_1_saturn shows a smooth starfield at the far zoom; (2) NOT FIXED, space_6_pilgrim shows the same pixel stairs on Luna after the FullRect import: with bilinear sampling a hard-stepped alpha edge means the disc material clips alpha at a threshold (cutout) or the sprite is drawn through an alpha-test path; switch the disc material to alpha blend (or raise the near-range disc size) and re-shoot, in the U-106 batch. Done on the second re-shoot. Cycle 257 (04:4x): (1) DONE in 0b4af5a (SpaceBackdrop.TilePeriod; space_1 smooth). (2) open: UNITY is checking whether the 64 px source frame has a hard alpha edge (then bilinear at 10× gives 10 px steps and the fix is an edge-smoothing alpha in the disc material or a larger near-range frame) or a clip path; answer and re-shoot with the U-106 batch. Cycle 257 (04:5x): the art side is B-143 (a 2-texel soft alpha limb on the disc frames, BLENDER's next slot); UNITY's side stays the material (alpha blend, no cutoff). Re-shoot space_6 after both; Done on it. Cycle 257 (05:1x, D-128): (2) ruled: BLENDER exports `planets/<p>/disc_near` + `luna_near` ≤ 512² (B-143 redirected); DiscSprite swaps to the near frame above ~6× magnification and back below it, streamed with the planet's group; the Sprite_LitDisc iso-line material stays for the far view; no shader circle, no zoom clamp. This half rides the first C2 Earth batch (after U-106), not the U-106 window; C1 closes with the limit named in C1_REPORT.md. Done on the space_6 re-shoot after both halves. Cycle 262 (07:1x): the disc_near swap is in (ae7b8cfc, judged against the Space camera); space_6's near log read the far zoom between shots, so the capture now holds the ship-view zoom until the near frame is on; re-shot in hand-off 3. Done on it (B-143 with it). Cycle 263 (07:5x): DONE (a2c5b4df; reports/unity/u103/space_6_pilgrim.png re-shot on Earth's near frame: `13.3 px/texel, near frame disc_near_0, using near True`, a crisp inked limb where the 33× stairs were; space_1 smooth since 0b4af5a).

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

### U-074 · UNITY · Done · R1
Goal: 3D lighting from `TimeSystem` (Bible §10.5 v2): one directional Sun (angle, colour, intensity per planet per §9 and D-030), per-planet ambient gradient, soft shadows (one cascade, 30 m), bloom; lamps, thrusters, vents become point lights (≤ 8 visible); distance fog per planet replaces the haze gradient; Light2D components removed.
Accept: DayNightTests adapted (noon/midnight intensities per §9); night darkens the terrain; a lamp pools light on blocks and the back wall; BaseTests green; budgets.
Files: Assets/_Game/Code/Runtime/Planet/Lighting/, Building/
Depends: U-072
Lead notes: Done 4c439ca + 61f1a58 + 8405680 + 179d35d (cycle 193): Sun3D + ambient from DayNightMath, lamp point lights (1.6 m off the faces, 8 m), per-planet exp² fog, bloom; DayNightTests.The3DSunAndAmbientFollowTheClock; EditMode 237/237, compile 0/0; u074_2026-11-02/mars_shelter_night_lamp.png: night-dark terrain and backdrop, warm pool on the regolith blocks. Placeholder cards still full-bright until U-075/U-076 (expected).

### U-075 · UNITY · Done · R1
Goal: Model-based views: `CharacterView`/`CreatureView` drive an Animator with clips named exactly as the old sheet clips (contract §5 names), facing by a 180° yaw turn, hit flashes by material property; `ArtImporter` v5 imports `.glb` per contract §9 (materials from the four maps, clip names kept, address = key, placeholder retired); capsule/box placeholders until B-078/B-082; the hit/footing/interaction code unchanged.
Accept: ArtImporterTests for a sample glb (B-077's calibration model); every clip name used in code resolves on the placeholder Animator; FootingTests, creature tests green.
Files: Assets/_Game/Code/Runtime/Creatures/, Player/, Code/Editor/ArtImporter.cs, Tests/
Depends: U-072
Lead notes: Done cb1b3cb + a052069 + d50b5f6 (cycle 197): ModelView drives the surveyor, stag, wolf, dustskater and scree stalker by clip name (sheet species keep sprites); ArtImporter v5–v8 (glb → Mecanim, materials from the maps, loops/sockets from the json, generated placeholders, atlas rule); EditMode 239/239 incl. ModelImportTests; targeted PlayMode 03:29 + 03:36 green (ModelView, SurveyorAnim per D-070, CreatureTests 10/10 with feet measured on baked vertices, Footing, M1Integration, SpawnCamp); compile 0/0.

### U-076 · UNITY · Done · R1
Goal: Ship, props and depth bands: the Pilgrim and props batch 1 as model prefabs (placeholders until B-079/B-081); the building system places 3D prefabs on the plane; the three parallax layers become depth bands (near props plane z 2–6 m, mid ridge mesh strip z 20–60 m, far skyline + sky dome ≥ 150 m) fed by the planet config; Space keeps its top-down view with planet spheres.
Accept: an Earth capture shows blocks, back wall, ridges, sky dome and the ship with depth; BuildTests, ShipSideTests, SpaceArtTests green.
Files: Assets/_Game/Code/Runtime/Ship/, Building/, Planet/Backdrop/, Prefabs/
Depends: U-073, U-074
Lead notes: Cycle 171. R1. Cycle 179: the landing pad is now a 2 m module (D-068): the camp spawns two modules (4 m) under the Pilgrim; landing-rule width = 4 m; shelter_door plays its `open` clip; lamps light from socket_light. Cycle 202 review of u076_2026-11-02: mars_shelter_night.png PASSES (lamp model lit from socket_light, wall/door/crate models, boulders, ridge). earth_camp_day.png: ship on the pad modules, props, surveyor, ridge and skyline all read; FAIL on the flora, Art matches §9: the trees render flat-shaded and untextured (faceted crowns in solid greens), unlike BLENDER's review_b085_grove.png (smooth, textured). Likely the importer: mesh normals/smoothing lost on the atlas models, or the generated atlas material not using atlas_color/atlas_normal. Fix, then re-shoot. Also apply D-071 (P-33) in the same pass. Cycle 207 (2026-11-05, resume after USER-17): D-071 (77e5bf1) and D-072 (533cc5a, importer v10) are in; the 12:23 EditMode run was 242/243 with the one red (ModelMapsAreCappedByDimensionNotByFileSize) fixed in dfd7ce3 but never re-run; the re-check filed as want_unity 12:27 died with the restart. Left to Done: (1) commit the v10 reimport leftovers still untracked in the tree (Generated/Models/creatures/{mercury,venus}, props/{mercury,venus}, props/common/aerostat_*.mat and their .meta files, calibration/base.mat); (2) one check: compile + EditMode + PlayMode `U076SceneTests|ModelViewPlayTests`, expect 243/243 and atlas_normal.png.meta typed NormalMap/linear; (3) `unity_capture.ps1 -Params @{ Name='u076b'; Test='CaptureDepthBands' }`, copy earth_camp_day/depth over reports/unity/u076_2026-11-02/, trees textured and smooth behind the ridge → tell LEAD. Memory: free RAM was 0.37 GB at 23:3x; wait for the USER-18 gate (1.5 GB) before the check. Cycle 209 (2026-11-06): Done af8c985 + 490e08e: u076_2026-11-05/earth_camp_day.png (the Pilgrim on the pad modules, props, surveyor, the forest ridge and the snow skyline with depth), mars_shelter_night.png passes; compile 0/0, EditMode 243/243, PlayMode U076SceneTests|ModelViewPlayTests 3/3. The faceted 'trees' are B-083's earth_forest/ridge_mid (flat-shaded 14-24 m trees at z 17), not the flora: the near bush is smooth and textured. That is an art fail on B-083, reopened as B-102; no UNITY change (D-074).

### U-077 · UNITY · Done · R1
Goal: BudgetGate 3D rows (Bible §11.1 geometry row: ≤ 300 k triangles, ≤ 400 draw calls, ≤ 150 shadow casters) + `unity_profile` reads them; R1 build `Build/MERIDIAN_0.4.0/` with a smoke set (Earth day, night with a lamp, digging, the ship landed and flying, Space).
Accept: every BudgetGate row green on Earth in the dev build; smoke clean; GameInfo 0.4.0.
Files: Assets/_Game/Tests/Unit/BudgetGateTests.cs, tools/unity_profile.ps1, Build/
Depends: U-075, U-076
Lead notes: Cycle 171. R1 close, with the owner's playtest. Cycle 207: first slice (b5bf4bc: BudgetMonitor triangle/shadow-caster counters + caps, BudgetGate Geometry rows, GameInfo 0.4.0) and the smoke legs smoke_3b_earth_dig / smoke_3c_ship_airborne (490e08e) are committed uncompiled; left: unity_smoke.ps1 count 19 → 21, compile with the U-076 check (one wrapper call, not two), `unity_profile.ps1 -Build`, `unity_smoke.ps1`, perf + smoke reports, Build/MERIDIAN_0.4.0/. Start the moment U-076's capture is sent; don't wait for LEAD's Done. Cycle 209: order of work: (1) commit importer v11 (colour maps Default/sRGB + mips) and the flora-only CaptureDepthBands shot; (2) let BLENDER take the lock for B-102 + B-094 (one call, about 10 min); (3) then one wrapper call: compile + the v11 reimport + EditMode + unity_profile -Build + unity_smoke (21 shots) -> Build/MERIDIAN_0.4.0/. The Earth day smoke shot must show the B-102 ridge; if B-102 is not in within 60 min of your (2), build anyway and note it. Cycle 217: job 2 ran (8.8 min): Build/MERIDIAN_0.4.0/MERIDIAN.exe, smoke 21/0 errors, perf_2026-11-06.md all green except Transition entry 1.53 s vs 1.5 s (RED stays; first run after the full reimport; UNITY re-measures on its next turn, no loosening) and the Earth day shot fails on B-102 (BLENDER round 2). Venus dev-build textures 558/600 MB after the v11 mips: watch row, D-072 reopens at 600. Next turn, one release call after BLENDER's B-102 round 2 lands: unity_check with the U-078 tests folded in only if it fits the 20 min, else U-078 waits; rebuild 0.4.0, re-measure the transition, re-shoot smoke 2, 2b, 3c and 7. R1 closes on that build. Cycle 220 (01:3x): release call 4 (01:10-01:19, u077_release4_20261106.log) ran compile 0/0, EditMode 245/245, PlayMode 8/8, build 539 MB, smoke 21/0, every perf row green (transition entry 1.39 s) except the Venus dev-build texture row 630/600 MB and one normal map not BC5. Under budgets v3 (D-077, 2.0 GB) the Venus row is green; U-086 updates the gate and re-profiles; the call's outputs are still uncommitted in the tree (perf/tests reports, 21 shots, generated materials, metas, link.xml): commit them first. Closes on U-086's green profile; then the R1 report + owner playtest.


### U-086 · UNITY · Done · R1
Goal: BudgetGate v3 (Bible §11.1 v3, D-077): limits 4.5 GB working set (warn above 4.0), 2.0 GB textures, 600 MB meshes, 150 MB audio, 500 k triangles, 500 draw calls (250 side view), 1500 particles; a Residency row (the previous planet's groups released within 5 s of a transition, by Addressables handle count); a hit-stop row (≤ 90 ms; placeholder until U-089); per-planet dev-build memory rows kept; `unity_profile.ps1` prints the new rows. Before anything: commit the 01:19 release-call outputs as they stand (perf/tests reports, 21 smoke shots, generated materials, Art metas, link.xml).
Accept: `perf_<date>.md` from one profile-only run (no rebuild) all green incl. Venus textures (630 MB < 2.0 GB) and the one BC5 miss fixed (name the texture in the report); 0.4.0's smoke stays valid; EditMode green; U-077 then closes.
Files: Assets/_Game/Tests/Unit/BudgetGateTests.cs, Assets/_Game/Code/Runtime/Perf/BudgetMonitor.cs, tools/unity_profile.ps1
Depends: U-077
Lead notes: Cycle 220. First task, light: one profile under the lock (≤ 6 min), after BLENDER's B-101 export if its want is up. The thresholds are the owner's (D-077), not yours to tune. Cycle 223: BLENDER released the lock 10:18, no want filed: your turn now. Fold in (same call): (a) the rings_color mip fix and the u078 CaptureSpaceArt capture (U-078 note); (b) contract §9.1 ruling 10 (D-082): a model whose sidecar json says `"alpha_clip": true` gets its ArtImporter material set to alpha clip (cutoff 0.5) and double-sided; the B-109 Earth flora jsons will carry it and the Earth flora atlas_color already carries alpha (6550853). Keep mip streaming for U-091. Cycle 225 (10:5x): check OK 10:23-10:31 (617d01c; compile 0/0, EditMode 246/246, SpaceArtTests radial rings 1/1). Profile -Probe 10:40-10:42 (perf_2026-11-06.md 10:42): Earth rows green, Venus textures 630 MB green under v3, BC5 misses 0, dev-build memory rows green; THREE RED rows are contention candidates (run started with 0.27 GB free, two Unity processes; Earth warm-up 3386 ms vs 640 ms at 01:14): First visible frame Space 212.9 ms (01:14: 29.1), Mars 263.6 ms (1.4), Transition entry 1.87 s (1.39). Per D-083: one re-run of `unity_profile -Probe` when ≥ 1.5 GB is free, Blender not running and the u078 capture finished; the load line reports free RAM at start from now on. Residency row: 'pending U-091' (D-083); its measurement (planet_earth 7 handles after Mars entry) is the U-091 evidence, not a U-086 failure. No loosening. U-077 closes on the re-run if Earth and those three rows are green. Cycle 228 (11:2x): gate-clean re-run (2c50253, 2.7 GB free, one Editor): Space first frame 7.2 ms green, launch 1.43 s green, Earth green, dev-build memory green; still RED entry transition 1.54 s and Mars first frame 177.5 ms. It was the first Editor run after the v12 reimport of 335 textures, the pattern of cycle 217 (v11: 1.53 s, then 1.39 s). D-085: a first profile after a full Art reimport is a warm-up; ONE more `unity_profile -Probe` after the feel check, its own lock call, with mip streaming ON as now committed. That one is final: if either row stays red, it is a regression (bisect: ring fix vs v12 vs streaming) and R1 holds. Report the Mars warm-up and the transition breakdown (scene load / configure / tile sheets / warm-up) in that run.

### U-087 · UNITY · Superseded (D-086) · S1
Goal: Stage camera (Bible §5.1 v3): a pure C# `StageCamera` solver (inputs: player x/y/facing/speed, stage-floor height, hostile count and apex distance, dt; outputs: camera x/y and frame height) driving `CameraFollow`: ± 1.5 m dead zone, 0.25 s damped follow, 2 m look-ahead over 0.6 s, speed cap player + 2 m/s; vertical hold on the stage floor (frame bottom 3 m below the ground height smoothed over 0.8 s), vertical motion only outside the middle 60 % of the frame at ≤ 6 m/s, falls > 10 m use a 0.4 s follow; fight zoom 18 → 22 m (apex 26 m) in 1.0 s, back in 2.0 s after 3 s calm; impact shake 0.15 m / 0.10 s position-only; `SnapToTarget` and the photo orbit kept. The stage floor comes from `TerrainStreamer` (ground column under the player).
Accept: EditMode `StageCameraTests`: (a) a 2.5 m jump moves camera y by 0.00 m; (b) a 6.6 m jump (Mars) by 0.00 m; (c) a 15 m fall is followed within 0.4 s; (d) running right at 6.5 m/s holds the player 1.5–3.5 m left of centre after 1 s; (e) fight zoom reaches 22 m at 1.0 s ± 0.05 and is back at 18 m by 5.0 s after calm; (f) shake never rotates. PlayMode `StageCameraPlayTests` on Earth: a jump at the camp leaves camera y unchanged. Frame time Earth avg ≤ 12 ms / p99 ≤ 16.6 ms unchanged; 0 B GC per frame; `SideViewTests` and `M1LoopTests` unchanged; the smoke set re-shot with the new framing.
Files: Assets/_Game/Code/Runtime/Camera/StageCamera.cs, Assets/_Game/Code/Runtime/Player/CameraFollow.cs, Assets/_Game/Tests/Unit/StageCameraTests.cs, Assets/_Game/Tests/Play/StageCameraPlayTests.cs
Depends: U-086
Lead notes: Cycle 220. Lock-free coding; one check together with U-088 and U-089.

### U-088 · UNITY · Superseded (D-086) · S1
Goal: Feel v3 movement (Bible §4.2 Feel): `PlayerTuning` v3 (ground accel 60, braking 80, air accel 30, instant facing flip with velocity reversal ≤ 0.08 s, jump cut to 40 % on release), an `AirDash` solver (Shift tapped while airborne: 9 m/s facing for 0.18 s with vertical speed held at 0, then g resumes; one per airtime; refreshed by landing or a parry; 0.35 s cooldown), a `Parry` solver (C: 0.12 s window, 0.40 s whiff recovery, air and ground; a parried melee attack does 0 damage and staggers the attacker 1.2 s; a parried projectile reflects along the aim; refreshes the dash), input actions `Dash` and `Parry` in `MeridianInput`, an `IParryable` hook on `Creature` attacks, `LanceBolts`, Warden bolts and thrown projectiles; hit stop 50 ms (player hit) / 33 ms (Lance or parry hit) through a pooled `HitStop` (unscaled timers unaffected). Gravity, v₀ and heights untouched.
Accept: EditMode `FeelTests`: jump height per the §4.2 table on all 8 planets within ± 1 cm (same test before and after); dash distance 1.62 m ± 0.02 on all 8 planets; the dash ends with the planet's g; parry window and recovery timings; hit stop ≤ 90 ms across a 5-hit chain. PlayMode `FeelPlayTests` on Earth: one dash per airtime, a second only after landing; a parried wolf bite does 0 damage and staggers it 1.2 s; a parried Warden bolt travels back along the aim. `M1LoopTests` and `M2SoakTests` unchanged; 0 B GC per frame; frame time unchanged.
Files: Assets/_Game/Code/Runtime/Player/PlayerMotion.cs, PlayerController.cs, MeridianInput.cs, AirDash.cs, Parry.cs, Assets/_Game/Code/Runtime/Core/HitStop.cs, Creatures/Creature.cs, Creatures/Wardens/, Rig/LanceBolts.cs, Assets/_Game/Tests/Unit/FeelTests.cs, Assets/_Game/Tests/Play/FeelPlayTests.cs
Depends: U-086
Lead notes: Cycle 220. The dash is a velocity override like the jetpack's thrust, not a gravity change; the ± 1 cm test is the proof that the owner's hard rule holds. Cycle 224: UNITY's note accepted: no creature throws anything yet, so the parry reflects Warden bolts only (the projectile test case uses a Warden bolt); spit and shards join when a throwing creature exists. Hook: PlayerController.TryParryAttack(from) from CreatureDirector.Bite and WardenDirector.StepBolts (874f2cf, uncompiled).

### U-089 · UNITY · Superseded (D-086) · S1
Goal: Squash-and-stretch, anticipation and hit reactions (Bible §4.2 Feel): `SquashStretch` on the visual root only (volume-preserving; curves per §4.2: crouch 0.8 / 0.06 s, take-off 1.25 / 0.08 s, landing 0.7 at ≥ 6 m/s scaled from 1.0 at 2 m/s with a 1.05 overshoot in 0.18 s, dash 1.3, hit 0.85); `SurveyorAnim` plays `jump_anticipate`, `land_hard`, `dash`, `parry`, `parry_hit`, `hit_react` (scale-only stand-ins until B-103 lands); the player hit reaction (0.8 m knock over 0.12 s, a 2-frame white flash through a material float); creature reactions through `ModelView` (0.5 m knock, flash, squash, `hit_react` / `stagger` or stand-ins until B-106); the camera shake hook of U-087.
Accept: EditMode `SquashStretchTests`: sx·sy·sz = 1 ± 1 % along every curve; the `CapsuleCollider2D` and `Rigidbody2D` unchanged during a 0.7 squash. PlayMode: a 7 m/s landing reaches 0.7 within one frame and 1.0 ± 0.02 by 0.2 s; a wolf hit shows the player's knock and flash and the creature's squash in the same frame; 0 B GC; frame time unchanged; new smoke shots `smoke_3d_landing_squash` and `smoke_3e_parry` (23 shots).
Files: Assets/_Game/Code/Runtime/Player/SquashStretch.cs, SurveyorAnim.cs, Assets/_Game/Code/Runtime/Art/ModelView.cs, FX/HitFlash.cs, tools/unity_smoke.ps1, Assets/_Game/Tests/
Depends: U-088
Lead notes: Cycle 220. Visual root only, never the collider or the body. Cycle 226: P-37 accepted (D-084): the jump leaves the ground on the input frame; the 0.8 crouch is drawn over the first 0.06 s of the rise, then the 1.25 stretch; no input delay anywhere in the feel pass. Bible §4.2 reworded. Code in 518ce28 (uncompiled) matches.

### U-090 · UNITY · Superseded (D-086) · S1
Goal: Stage layers runtime (Bible §10.10, contract §10): `StageLayers` replaces `DepthBands` (keep its public API for the tests): layers 0–7 per region (foreground pieces 1 per 12 m from `props/<planet>_foreground/*`, never within 6 m of the spawn, a POI or a pad, shadows off; `rocks_near` 128 m; `ridge_mid`; `hills_far` 512 m; `skyline_far` 1024 m plus set-pieces from `stage.json`; the cloud strip at z 500 scrolling 0.5 m/s; the skydome), per-layer haze tint from `haze_rgb`, one Addressable label `stage_<planet>_<region>` per set, the adjacent region preloaded within 200 m of a border and unloaded 5 s after two regions away; flat tinted placeholder quads under `Placeholders/` for every missing layer so all 8 planets run before BLENDER's sets land; digging and building untouched (no layer has collision).
Accept: PlayMode `StageLayerTests`: every Earth region resolves ≥ 7 distinct layers (placeholders count) at their §10.10 depths; no foreground piece within 6 m of the spawn or a POI; crossing a region border at run speed: no hitch > 33 ms, the next set resident before arrival, the old set released within 5 s (handle count); a `*_depth.png` capture shows the stack. Earth dev build: frame time avg ≤ 12 / p99 ≤ 16.6 ms, triangles ≤ 500 k, draw calls ≤ 250, textures ≤ 2.0 GB, working set ≤ 4.5 GB. `TerrainTests` (dig/place) and `M1LoopTests` unchanged.
Files: Assets/_Game/Code/Runtime/Planet/Backdrop/StageLayers.cs, DepthBands.cs, Assets/AddressableAssetsData/, Assets/_Game/Placeholders/, Assets/_Game/Tests/Play/StageLayerTests.cs
Depends: U-087
Lead notes: Cycle 220. Build it on placeholders first; B-104/B-105 swap in through the importer with no code change. Foreground pieces are plain `ModelView`s at negative z.

### U-091 · UNITY · Done · C1
Goal: Residency and streaming for budgets v3: `TerrainStreamer` keeps chunks within 3 of the camera (was 2); per-planet Addressable groups verified exclusive (the current planet + `common` + `ui` + `space` only; the previous planet's groups and stage sets released within 5 s of a transition); texture mip streaming on with a 1.5 GB budget; `BudgetMonitor` Residency row from handle counts and the streaming budget; audio ≤ 150 MB with music streamed; `ArtImporter` rejects a planet's newest layer when the planet's layer textures exceed 700 MB stored (contract §10).
Accept: PlayMode `ResidencyTests`: Earth → Space → Mars → Space → Earth: after each hop the released planet's handles are 0 within 5 s and the working set returns to within 10 % of the first visit; perf rows for all five scenes per D-089: working set < 2.0 GB (warn 1.7), textures ≤ 512 MB, ≤ 8 atlases per planet; planet load ≤ 5 s; transition ≤ 1.5 s; no hitch > 33 ms while streaming at run speed with radius 3. (Rewritten cycle 238; the Goal's v3 numbers (1.5 GB mip budget, 700 MB stored) are superseded by D-089: mip streaming stays on with a 512 MB budget; the importer cap becomes 512 MB of textures per planet.)
Files: Assets/_Game/Code/Runtime/Terrain/TerrainStreamer.cs, Assets/_Game/Code/Runtime/Perf/BudgetMonitor.cs, Assets/_Game/Code/Editor/ArtImporter.cs, Assets/AddressableAssetsData/, Assets/_Game/Tests/Unit/Play/ResidencyTests.cs
Depends: U-086
Lead notes: Cycle 220. Lock-free coding; its measurement joins U-090's check. Cycle 225: first evidence from U-086's probe (perf_2026-11-06.md 10:42, Residency row): after Mars entry planet_earth still holds 7 handles at 5.0 s and the resident list is common, planet_earth, planet_mars, planet_mars_flora, planet_mars_plains, planet_space, planet_warden, planet_waystation, session, space, ui. Find the 7 holders first (ArtLoad wraps every load; log the keys); the fix is release on transition, not a longer timeout. Cycle 231: when this card is promoted for C1, its memory rows follow D-089 (working set < 2.0 GB, textures ≤ 512 MB), not the v3 numbers above; LEAD rewrites the Accept line at promotion. Cycle 245: design doc read (coordination/reports/unity/u091/design_2026-11-06.md); the seven open questions ruled (D-110): (1) YES: a terrain sheet used by more than one planet lives in `common`, unpacked (terrain/earth/snow, jupiter/floe_ice, floe_core); no BLENDER duplicates. (2) Sprite packing stays OFF through C1; the "≤ 8 atlases" row becomes "≤ 8 resident sheet textures of 1024² or larger per planet" counted from loaded textures, plus the 512 MB cap; revisit at C2 Earth. (3) YES: B-128 (icons for the seven icon-less tile items). (4) YES: review captures set `Texture.streamingTextureForceLoadAll = true` for the shot; smoke shots keep the real budget. (5) Keep the OnlyPlanet set (common, ui, space, planet_space, planet_warden, planet_waystation, planet_rig, icons, session) for U-091; Bible §11.1 worded to it; no tightening follow-up. (6) YES to the 9-leg probe route; it is one heavy job ≤ 20 min in its queue slot. (7) Docs done: Bible §11.1 planet-load definition, §10.10 and contract §10 700 MB lines marked superseded by D-089; the Files path below corrected; the stale "384 MB" is not on this card. Cycle 246: code written lock-free per UNITY's 22:3x status (ArtKeys.GroupOf as the one group table, Prefetch/ReleasePrefetch, LastPlanetLoadSeconds, BudgetMonitor v4 limits, the 512 MB importer cap); check is queue #3 after BLENDER's export batch. Add with it: ItemRegistry `def.icon = "icons/<key>/base"` for soil, grass (Turf), regolith, mercury_regolith, mercury_basalt, sulfide, tessera, snow (B-128 exports in that same BLENDER batch; the ItemIcons test lists none missing once both are in). Cycle 247: CHECK DONE (960af2f). Editor route: planet_earth 0 handles on Mars after 0.0 s, loads 0.68 / 0.71 s, transitions 0.70 / 0.89 s, returns within 10 %. Dev build, 9 legs (perf_2026-11-06.md 23:23–23:30): working set 819–956 MB, textures 261–319 MB, residency 0 handles after 0.0 s on every hop with the planet's own handles tracked, loads 1.66–1.72 s, transitions 0.72–1.00 s, bundles only the leg's own planet. One red row, Return · Earth again 956 vs 819 MB (+17 %) → D-114: the probe gains an `Earth (warm)` leg after the first launch + re-entry and the Return rows compare against it; the boot → warm delta becomes its own info row capped at 150 MB. Re-run in your #4 batch with the def.icon keys; DONE when every Return row is green. Cycle 249 (00:2x): DONE (e42a33a; perf_2026-11-07.md, 11 legs, dev build 134 s, probe 00:12–00:18): 50 rows green; Boot → warm +22 MB working set / +6 MB private; every hop 0 handles after 0.0 s; loads 1.5–1.8 s (boot 4.80 s); transitions 0.72–1.0 s; textures and meshes flat across the loop. The two Return rows were red on working set only (+11.6 % / +10.8 %) with private commit within 10 % (+6.9 % / +7.5 %) → D-116: the Return rows judge private commit, working set is info, and a `Creep per visit` info row (≈ 15 MB private per planet visit today) opens U-112 after U-106. Carried to U-106: the atlas row prints the resident ≥ 1024² sheet count per planet (D-110 (2)) instead of n/a; the worst iris-in frame per transition is listed (141–250 ms on the Earth entries); the boot load's 4.80 s breakdown stays in the report.

### U-092 · UNITY · Superseded (D-086) · S1
Goal: S1 build `Build/MERIDIAN_0.5.0/`: GameInfo 0.5.0; `unity_release.ps1` with the FULL PlayMode suite (no filter), profile -Build, the 23-shot smoke set re-framed by the stage camera plus `smoke_2c_earth_fight_zoom` (24); perf and smoke reports.
Accept: compile 0/0; EditMode and PlayMode all green with no filter; every §11.1 v3 row green on Earth, Space and Mars; smoke 24 shots, 0 errors; the Earth day and depth shots show ≥ 7 layers with the B-104/B-105 art and the surveyor's B-103 clips.
Files: Assets/_Game/Code/Runtime/GameInfo.cs, tools/unity_smoke.ps1, Build/
Depends: U-087, U-088, U-089, U-090, U-091, B-103, B-104, B-105
Lead notes: Cycle 220. Split the lock at 20 min (D-026): tests in one call, build + smoke in the next.

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

### U-078 · UNITY · Superseded (D-086) · R1
Goal: Planets as spheres in Space (Bible §10.5 v2): each planet disc becomes a sphere mesh with the equirect `planets/<name>/surface` texture, the atmosphere rim and cloud layer as a slightly larger translucent shell, the terminator from the real Sun direction, Saturn's rings as a flat ring mesh; the top-down orthographic camera, wells, belt and stations unchanged.
Accept: SpaceArtTests still resolve every planet key; a Space capture shows lit spheres with terminators and Saturn's rings; Space budgets within §11.1.
Files: Assets/_Game/Code/Runtime/Space/, Shaders/, Prefabs/Space/
Depends: U-072
Lead notes: Cycle 176. R1. Independent of the terrain work. Cycle 192: B-090 models are in: props/space/waystation (+ waystation_mars, LOD1), asteroid_01..06, planets/saturn/ring_mesh (alpha from rings_color.png, double-sided; handoff in BLENDER_STATUS). Use them in place of the sprites; the U-078 capture closes B-090. Cycle 220: its code compiled and SpaceArtTests passed 8/8 in release call 4 (01:11); smoke_7_space_saturn (01:19) is the capture: LEAD reviews it next cycle. Queue order now: U-086, then U-087–U-091, then U-078 polish if any, U-079, U-080, U-092. Cycle 221 (10:2x): smoke_7 FAILS Art matches: the ring sheet aliases into stair-stepped bands and moiré across the whole frame (the rings fill the shot at the ship's zoom), and nothing in the shot shows a lit sphere or terminator (only a cream edge of the planet at the bottom). Fix with U-086's call: rings_color imported with mips + trilinear + aniso 8 (or the ring material samples the sheet radially with a mip bias of −0.5), and the CaptureSpaceArt capture (`unity_capture.ps1 -Name u078`) framed on Saturn as a whole (sphere + rings + terminator) plus one on Earth with Luna. Accept unchanged; verdict on that capture. Cycle 227 (11:1x): capture u078_2026-11-06/ (123aa95, 10:47) PASSES Art matches: Saturn as a lit sphere with a terminator inside clean radial-sampled rings (no moiré), Jupiter and Neptune with terminators, the belt, Earth with the atmosphere rim, Luna and the waystation. The rings' baked shadow side averaged out is accepted (a real ring shadow is a later polish, not reopened). SpaceArtTests 8/8 (01:11) and 1/1 (10:31). Done together with U-077 on the profile re-run (Space rows green under the gate).

### U-079 · UNITY · Superseded (D-086) · R1
Goal: FX in 3D: thruster, landing dust, dig sparks, heat shimmer and the Escape band become camera-facing billboards or particle systems on the play plane using the existing `fx/*` sheets and keys; emissive FX feed bloom; nothing uses Light2D or sprite sorting layers.
Accept: FX keys resolve; a capture shows the thruster flame and dig sparks lit/emissive under the Universal renderer; 0 B GC per frame as before.
Files: Assets/_Game/Code/Runtime/FX/, Prefabs/FX/
Depends: U-072
Lead notes: Cycle 176. R1.

### U-080 · UNITY · Done · R1
Goal: Review camera for depth: photo mode (`P`) gains an orbit of ±30° yaw and ±15° pitch around the player (mouse drag) and a "depth" preset used by `tools/unity_smoke.ps1` captures, so reviews can show the block relief, back wall and depth bands; gameplay camera unchanged.
Accept: a smoke capture named `*_depth.png` from the yaw preset; SideViewTests unaffected.
Files: Assets/_Game/Code/Runtime/Camera/, tools/unity_smoke.ps1
Depends: U-072
Lead notes: Cycle 176. R1. Small; it makes every later review honest about depth. Cycle 229 (11:2x): Done (5f80da1): Camera/PhotoOrbit.cs (MaxYaw 30, MaxPitch 15, Depth preset 25/10 at the rail distance, CameraFollow paused only while the orbit is on); smoke_2b_earth_day_depth.png (01:18) shows block relief, back wall and the bands; SideViewTests in the 263/263 EditMode run (11:06). The flora in that shot predates B-109; the next smoke shows the new trees.

### U-081 · UNITY · Superseded (D-086) · R2
Goal: Mars in 3D, the R2 counterpart of U-076: Mars block arrays from B-086, Mars depth bands from B-088 (ridge_mid per region, Tharsis skyline, storm skydome crossfade during dust storms), Mars flora and POI props from B-089/B-084 placed by the existing POI/scenery rules, Mars creatures already through ModelView; dust storms as 3D particles + the ×4 fog; the M2 smoke set (canyon, storm, polar, Olympus, night) re-shot in 3D with the depth preset.
Accept: M2SoakTests + CreatureTests green; a Mars capture set matching §9 v2; §11.1 incl. the geometry row green on Mars in the dev build.
Files: Assets/_Game/Code/Runtime/Planet/, Terrain/, Prefabs/
Depends: U-073, U-074, U-075
Lead notes: Cycle 199. R2. Start after U-076; everything it needs from BLENDER is in.

### U-083 · UNITY · Superseded (D-086) · R2
Goal: Interactive rim glow (Bible §9 v2 Readability): props and creatures the player can interact with show a faint emissive rim driven by the mask's B channel when the player is within 3 m (material float set by the interaction system); pickups pulse; the HUD prompt unchanged.
Accept: PlayMode: the rim float is 1 within 3 m and 0 beyond; a capture shows the smelter rim-lit beside the surveyor; 0 B GC per frame.
Files: Assets/_Game/Code/Runtime/Interaction/, Shaders/
Depends: U-075
Lead notes: Cycle 199. R2.

### U-084 · UNITY · Superseded (D-086) · R2
Goal: Block mesher performance pass: greedy meshing in a Burst job off the main thread (apply on the main thread ≤ 2 ms per chunk per D-019), mesh and collider pooling, a per-planet `TerrainBlocks` material instance; measure the §11.1 geometry row (triangles, draw calls, shadow casters) on Earth and Mars with everything placed and record it in perf_<date>.md.
Accept: chunk apply ≤ 2 ms p99 while streaming at run speed; geometry row green; no visible pop at chunk edges in a depth capture.
Files: Assets/_Game/Code/Runtime/Terrain/, Tests/
Depends: U-073
Lead notes: Cycle 199. R2. Lock-free coding; the measurement joins a scheduled check.

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

> **C0 STYLE TEST (D-086, owner, 2026-11-06). Read Bible §9 v4 and contract v3.0 §11 first.**
> The game is now a 1930s rubber-hose cartoon. Every open 3D and S1 card below is Superseded
> (sources stay). Work the cards in this order. Grease Pencil drawing builds are light only below
> 512 px; sheet batches are heavy and run only while no Unity Editor is open (D-091), at
> ≥ 1.5 GB free. Originality (§9.8): era techniques, never a property; no cup/mug heads.

### B-110 · BLENDER · Done · C0
Goal: The v3 pipeline: `render.py --sheet` renders a Grease Pencil (or Line Art + two-tone toon) object to 1x frames at 12 fps, applies ±20 % ink-thickness jitter, packs a contract §11.2 sheet + json (4 px gutters, ≤ 2048), and writes the §11.7 review sheet (`review.py`); also packs §11.3 rig sets. Prove it on a 2-clip test blob (`characters/calibration_v3/side`).
Accept: the test sheet's json validates against §11.2 (fps 12, caps, ppu 64); review sheet stamped with the 2× ink zoom; log OK; peak RAM in the status.
Files: blender/render.py, blender/review.py, blender/scripts/gp_*.py, Assets/_Game/Art/characters/calibration_v3/
Depends: —
Lead notes: Cycle 230. First, it unblocks every C0 asset. Cycle 231: free RAM 0.13 GB at 11:4x, so start with what needs no Blender: the sheet packer, json writer and validator in Blender's bundled python (numpy only), then B-115's overlays the same way, then the B-111 step-1 design sheet below 512 px. The first real GP render waits for the gate (1.5 GB) and an Editor-free window (D-091). B-103's 11:35 export landed after D-086 and is not reviewed (Superseded; sources stay). Cycle 232: PREVIEW ACCEPTED (24b19cb, review_b110_calibration_v3_preview.png 11:53): sheet 1964×324, idle 8 + walk 12 at 12 fps, outer ink 4–6 px with visible jitter, interior 1.8–2.6 px, flat cel + one shadow tone, 100 % palette, squash on contact, json valid. The review-sheet layout is the §11.7 standard for every C0 asset. Done when the full export runs (log OK, peak RAM in status): the gate read 1.68 GB at 12:02 and your want is first in line. Cycle 234: DONE (3f0c1bd, log 15:06:53 OK, sheet 1964×324, peak 399 MB; v13 import of the sheet in UNITY's 2ce211d with no importer error).

### B-111 · BLENDER · Done · C0
Goal: The surveyor redesigned (§9.3): an original rubber-hose astronaut with a big round fishbowl helmet and an expressive face inside (pie-cut eyes), white gloves, boots, hose limbs, Earth palette. Step 1: a design sheet (front/side/3-4, 4 expressions, the "what makes it ours" line) at preview size for LEAD's review. Step 2 (after LEAD's OK in the board notes): `characters/surveyor/side` sheet with idle (10), walk (12, head bob, big arm swing), jump (8, stretch), land (8, squash + smoke puff), look_camera (≤ 12).
Accept: §9.7 nine boxes on the review sheet; clips within caps at 12 fps; ≈ 128 px tall at 1x; sheet ≤ 2048.
Files: blender/sources/characters/surveyor_v3.blend, Assets/_Game/Art/characters/surveyor/
Depends: B-110 (step 2 only)
Lead notes: Cycle 233: STEP 1 OK (7915b76, review_b111_surveyor_design_preview.png 12:02). §9.8 pass: fishbowl helmet + plumb-bob antenna + meridian stripe + compass badge + float pack with air hose is ours; pie-cut eyes, gloves and hose limbs are era conventions; nothing from the forbidden list. §9.7 pass on ink, cel, palette, sheet, json. Expressions read at 1x (eye-pop and dizzy stars best). Keep every design choice as drawn. Go to step 2 now: idle 10, walk 12, jump 8, land 8, look_camera ≤ 12 at 12 fps; body ≈ 128 px to the helmet top at 1x (the antenna may add up to 16 px); the float pack must swing behind every move and the air hose must lag it (the secondary motion the sheet promises). Step 2 is a heavy render: gate 1.5 GB, no Editor (D-091). Cycle 234: STEP 2 ART ACCEPTED (b5b1d29, review_b111_surveyor_side.png 15:27): idle 10 / walk 12 / jump 8 / land 8 / look_camera 12, all within caps at 12 fps; squash 0.70–1.28 with smoke puffs on land; float pack swings and the hose lags in every clip; ink 4–6 / 1.8–2.6 px; palette 100 %; sheet 1956×976. Done on UNITY's earth_c0 capture with this sheet, where LEAD checks the 128 px body height against the 16.875 m frame. Cycle 235: DONE (capture reports/unity/c0_2026-11-06/earth_c0_placeholder.png: body ≈ 128 px + antenna on the 1080 px frame, idle plays at 12 fps, imports clean under v13). The clips the sheet lacks (bump, conk_out, run, fall, dash) are B-116.

### B-112 · BLENDER · Done · C0
Goal: One Earth plant with a face (original design, e.g. a yawning meadow flower with leaf hands) as a simple rig: `flora/earth/rigset` per contract §11.3, ≤ 6 bones, swaps for blink / yawn / giggle, sway idle on a 110 bpm beat with 8 % squash, react = turn to look within 3 m. Plus a 12-frame preview loop of the rig in Blender for the review sheet.
Accept: §9.7 boxes; one texture ≤ 2048 holds every part; json validates.
Files: blender/sources/flora/earth_rigset.blend, Assets/_Game/Art/flora/earth/
Depends: B-110
Lead notes: Cycle 238: DONE (2aa0303; "snoozle": a dandelion clock with a face, hose stem, mitten leaves; 10 parts on a 236×76 sheet, 5 bones ≤ 6, blink/yawn/giggle swaps, sway 12° at 110 bpm with 8 % squash, react turn_look at 3 m; json valid with the offset_m/order/slots UNITY reads). Evidence: 48 instances in reports/unity/c0_2026-11-06/earth_c0_placeholder.png (17:59) read as one family, ink consistent with the surveyor. Pipeline note (no reopen): the rig-set review sheet shows parts only; from B-118 on, put the 12-frame assembled preview loop on the review sheet too (§11.7).

### B-113 · BLENDER · Done · C0
Goal: One small friendly Earth critter from §7.1's roster (BLENDER picks the smallest; redraw in the style): frame-by-frame sheet `creatures/earth/<name>` with idle (8–12, rhythmic bob), walk (12), react (eye-pop, ≤ 10), bump (dizzy stars, ≤ 10). Pie-cut eyes, rubber-hose legs, ears/tail with follow-through.
Accept: §9.7 boxes; caps; 12 fps; sheet ≤ 2048.
Files: blender/sources/creatures/earth_<name>_v3.blend, Assets/_Game/Art/creatures/earth/<name>/
Depends: B-110
Lead notes: Cycle 238: ART ACCEPTED (27693eb, review_b113_earth_gull.png 17:31): "Gus", a stout egg-bodied gull with a three-feather crest, red-spotted mustard beak, hose legs; original (§9.8 pass: not any studio bird). idle 10 / walk 12 / react 8 (eye-pop) / bump 10 (dizzy spirals + stars, no X eyes) within caps at 12 fps; 54 px tall at 1x, reads; ink-behind on the small parts keeps the colour. Done on UNITY's first capture with the gull in the scene (U-098 or U-101). Cycle 241: DONE (u098/6_critter_gull.png: Gus framed over the camp, reads at 1x with the crest and red-spotted beak). Note for C2 Earth: the gull flies in the game but the sheet has no fly clip (walk/idle frames play in the air); a `fly` loop (8–10 frames) joins the C2 Earth creature card.

### B-114 · BLENDER · Done · C0
Goal: The painted Earth plains background in 3 layers (`backgrounds/earth/plains/layer0..2`, contract §11.4: watercolour, paper texture, soft bleed, no ink, tileable, ≤ 2048×1024) + `plains.json` parallax factors, and the Earth palette strip `ui/palettes/earth/strip` (the 8 Bible §9.1 colours).
Accept: 2× tiled preview with no seam; the surveyor placeholder pops off it at 1x (review sheet); ≤ 4 MB per PNG.
Files: blender/sources/backgrounds/earth_plains_v3.blend (or a painted-texture script), Assets/_Game/Art/backgrounds/earth/plains/, Assets/_Game/Art/ui/palettes/earth/
Depends: —
Lead notes: Cycle 238: DONE (27693eb; review_b114_earth_plains.png 17:32: three watercolour layers with paper grain and soft bleed, no ink, 2× tiled with no visible seam at the centre, 2.3 / 0.6 / 0.5 MB ≤ 4 MB; the surveyor pops off the wash at 1x; plains.json + the 8-colour palette strip). In the game: the layers replaced UNITY's strips by key with no code change (earth_c0_placeholder.png 17:59). Helmet-reads-green note → D-096 / B-118.

### B-115 · BLENDER · Done · C0
Goal: Film overlays `fx/film/grain`, `dust`, `scratches`: 512×512, seamless tile, greyscale + alpha (contract §11.6), subtle (dust ≤ 8 specks per tile, 1–2 hairline scratches).
Accept: 2× tiled preview with no seam; each file 512²; UNITY's U-095 capture reads subtle at 1080p.
Files: blender/scripts/gen_film_overlays.py, Assets/_Game/Art/fx/film/
Depends: —
Lead notes: Cycle 232: ART ACCEPTED (af18479, review_b115_film.png stamped 11:55-11:56): three 512² tiles, no visible seam at the 2×2 crossings, grain fine and even, dust 7 specks + 1 fibre, 2 scratch hairlines with breaks; reads subtle at game strength. Done on UNITY's U-095 1080p capture. Cycle 236: DONE (earth_c0_film_on.png 16:32: the three overlays tile at 1:1 with no seam, grain and dust read faint at 1080p, as specified).

### B-116 · BLENDER · Done · C0
Goal: The surveyor's missing gameplay clips on `characters/surveyor/side` (same sheet key, re-export; UNITY handoff 16:1x): `bump` (≤ 10: 0.8 m knock-back pose, dizzy stars over the helmet, settle), `conk_out` (≤ 12: wobble, eyes to spirals, slump; the iris-out starts on its last frame), then `run` (12, bigger stride and lean than walk), `fall` (8 loop, arms up, hose streaming), `dash` (6, horizontal stretch with speed lines). Bump and conk_out first: they are the two calls the game makes now.
Accept: §9.7 boxes on the review sheet; every clip within its cap at 12 fps; sheet still ≤ 2048 (split to `side_b` with a second json if it overflows: tell UNITY in your status); json valid; peak RAM in the status.
Files: blender/scripts/build_surveyor_v3.py, Assets/_Game/Art/characters/surveyor/
Depends: B-111
Lead notes: Cycle 235. After B-112 and B-113 (the plant and the critter are what C0 proves); heavy export under the gate and D-091. Cycle 238: DONE (27693eb; review_b111_surveyor_side.png 17:35: bump 10 with stars, conk_out 12 ending slumped with spirals, run 12 with a wider stride and lean, fall 8 loop, dash 6 with stretch and speed lines; 98 frames on one 1956×1956 sheet, new clips at 50/60/72/84/92, first 50 indices unchanged; UNITY's 17:59 capture set plays them). The 1x row on the painted layers shows the helmet reading green → D-096, B-118.

### B-117 · BLENDER · Done · C0
Goal: The Pilgrim ship redesigned for the style (§9.3): a bendy vintage rocket with a face-like front (porthole eyes, a grille mouth), fins that wobble, round cartoon exhaust puffs; original, not any film or game rocket. Step 1 only: a design sheet (side, 3/4, front; thrust stretch and cut-thrust squash poses; one puff set) at preview size with the "what makes it ours" line, for LEAD's review. No sheet export until LEAD's OK in these notes.
Accept: §9.7 boxes that apply to a design sheet (ink, cel, palette, original); readable at 1x beside the surveyor (the ship is ≈ 12 m long = 768 px, so draw the sheet at 0.5x with a 1x detail crop).
Files: blender/scripts/build_pilgrim_v3.py, blender/sources/ships/pilgrim_v3_design.blend
Depends: —
Lead notes: Cycle 235. Light (preview only). Last in your queue; take it when the gate is shut and you are out of lock-free work. Cycle 240: STEP 1 OK (2bd84e0, review_b117_pilgrim_design_preview.png 18:24). §9.8 pass: a teal banana-cigar rocket with a mustard nose-face (porthole eyes, grille grin), red-tipped wobbling fins, hose landing legs, round puffs; not any film or game rocket. §9.7 ink/cel/palette pass; thrust stretch and cut-thrust squash poses read; the 7-frame design strip reads at 1x on the plains. Keep every choice as drawn; the hose legs are the landing gear (ShipLegsView drives them). B-122 is released (sources now, export after the C0 sign-off, D-097). DONE as a card.

### B-118 · BLENDER · Done · C0
Goal: Helmet glass readability (D-096): give the surveyor's fishbowl a faint flat glass fill (the Earth palette's sky tone at ≈ 25 % over the face layer, plus the existing highlight) so the helmet reads as glass against the green meadow and any later background; re-export `characters/surveyor/side` (all 98 frames, same indices) and refresh the design sheet. From this card on, every rig-set review sheet also shows the assembled 12-frame preview loop (§11.7).
Accept: the review sheet at 1x on the B-114 plains (not the flat placeholder) shows the helmet as glass with the face readable; ink and palette boxes unchanged; sheet ≤ 2048; json valid, clip indices unchanged (UNITY needs no change).
Files: blender/scripts/build_surveyor_v3.py, blender/review.py, Assets/_Game/Art/characters/surveyor/
Depends: B-116
Lead notes: Cycle 238. Before B-117. One heavy export under the gate and D-091. Cycle 239: DONE (7606528; review_b111_surveyor_side.png 18:12: the helmet reads as pale sky glass on the painted plains in every clip, face fully readable, ink and palette boxes unchanged, 98 frames at the same indices, sheet 1956×1956 ≤ 2048; review_b112_earth_rigset.png now carries the assembled 12-frame loop at 1x on the plains + 2×). UNITY picks the new sheet up on its next import; no code change.

> **C1 (D-097, D-099; owner C0 feedback D-100..D-104, cycle 242).** C0 is approved with changes: ink at half weight with interior detail and two shadow tones (contract v3.1 §11.1), faces only on people and animals, the Pilgrim upright and faceless, discs without expressions. Order: B-124 (pipeline v4.1) → B-126 (snoozle v2, no face) → B-125 (surveyor re-ink) → B-127 (gull re-ink) → B-123 (upright Pilgrim design) → B-119 → B-120 → B-121 → B-122. Every export is judged on the ten-box §9.7 list. UNITY handoff (U-107, D-105): drop the fuel and tank icons from `build_icons.py` (launch_fuel*, fuel_cell, deuterium); the next icons export has none.

### B-119 · BLENDER · Done · C1
Goal: The eight planet discs for the space view (§9.3, contract §11.5): painted watercolour discs with ink outlines that still read as the real planets (bands, rings, caps, Earth's Luna beside it), each with a subtle personality idle (≤ 12 frames at 12 fps, e.g. Jupiter's bands swirl, Saturn's rings wobble, Neptune frowns); one sheet per planet ≤ 2048, sizes per §3 at the space camera's PPU.
Accept: §9.7 per disc; a review sheet with all eight side by side at the space scale plus 2× detail; originality line per disc.
Files: blender/scripts/build_discs_v3.py, Assets/_Game/Art/planets/<planet>/ (contract §11.5: `disc_color.png` + json; Luna at `planets/earth/luna`; Saturn adds `rings_back`, `rings_front` + `disc_rig.json`)
Depends: B-110
Lead notes: Cycle 240: PREVIEW ACCEPTED (3bae88f, review_b119_discs_preview.png 19:0x): all eight read as the real planets (§9.3) in watercolour with paper grain, a night crescent and a 5 px jittered ink line; personality idles as listed (Neptune scowl + blink, Jupiter bands + spot, Earth clouds at two speeds). Rulings: (1) space scale 3 px per space unit from PlanetConfig.visualRadius → D-098 (json `space_ppu: 3`, `radius_u`); Jupiter and the Saturn body at 9-frame idles on 3×3 sheets ≤ 2048, the rest 12. (2) Paths follow the contract, not the card's shorthand (fixed above). Export after the C0 sign-off (D-097); Done on UNITY's Space capture (U-103). Cycle 242 (D-101): no faces or expressions on any disc: Neptune's scowl and blink go; its character is the dark storm wandering and the band drift. Ink per v3.1 (2–3 px at the disc scale, interior band lines 1–1.5 px). Re-preview before the export. Cycle 243: a89f057 noted (Neptune's face gone: dark storm + trailing bright cloud; v3.1 ink with night-side hatching and band-edge fragments; Saturn ring sidecars at space_ppu 3; the disc review shows every frame of every disc with a per-disc panel). Export on your turn; LEAD reviews the stamped disc sheet. Cycle 246: ART ACCEPTED + EXPORT VERIFIED (24f8fbb 22:10; review_b119_discs.png 22:09): eight discs + Luna + Saturn's two ring parts in LFS, every sheet ≤ 2048 (Jupiter 1976², Saturn 1796², Earth 1932×348) and ≤ 1.8 MB; json per §11.5 (space_ppu 3, radius_u, idle 12 or 9 at 12 fps; Earth radius_px 75 = D-098); no face or expression on any disc (Neptune = one dark storm with a trailing bright cloud); ink 2.0–3.0 / 1.0–1.5 px measured, night-side hatching, mid + deep tones; ten boxes ticked on the sheet. Budget note: the review build peaked at 2289 MB (float canvas), fixed to uint8 panels in 673193b, not yet measured; the next disc run logs the real peak. Done on UNITY's Space capture (U-103). Cycle 254: DONE (in the game: U-103's Space captures 55f5aa1 show Saturn with its rings, Jupiter, Neptune, Earth + Luna over the starfield, imported clean in 60bedcf with their controllers; SpaceArtTests green). The near-range pixel steps are UNITY's filter choice (U-117), not the art.

### B-120 · BLENDER · Done · C1
Goal: Painted starfield (2048² tileable, paper grain, soft ink stars of 3 sizes, no seam) + 3 nebula cards (≤ 1024², alpha, soft bleed) for the Space parallax (contract §11.4), Earth-palette night tones.
Accept: 2× tiled preview with no seam; ≤ 4 MB per PNG; json with parallax factors.
Files: blender/scripts/gen_painted_bg.py, Assets/_Game/Art/space/starfield/, Assets/_Game/Art/space/nebula/
Depends: B-110
Lead notes: Cycle 240: PREVIEW ACCEPTED (208eb1b, review_b120_starfield_preview.png): paper-grain night wash, inked cartoon stars in three sizes, three nebula cards (rust, slate, olive) with soft bleed; no seam at the marked crossing. Export after the C0 sign-off; Done on the Space capture (U-103) with the 2× seam check on the exported PNGs. Cycle 243 (D-108): the layer scheme from a89f057 is the contract now (§11.4 v3.1): `backgrounds/space/starfield/layer0` 2048×1024 tiling in x and y (seams 1.01 / 1.12 measured) + `layer1..3` nebula cards + `starfield.json`. Export on your turn. Cycle 246: ART ACCEPTED + EXPORT VERIFIED (24f8fbb 22:10; review_b120_starfield.png): layer0 2048×1024 (1.5 MB) + three 1024² nebula cards (rust, slate, olive; ≤ 0.15 MB each) + starfield.json in the SceneLayout schema (tile + tile_y on layer0; parallax 0.05 / 0.12 / 0.18 / 0.25); no seam at the marked crossing; inked stars in three sizes on paper grain. Done on UNITY's Space capture (U-103) with the 2× seam check on the imported PNGs. Cycle 254: DONE (in the game: the starfield + nebula layers behind every U-103 Space capture and at the Escape Line in u109/3; imported clean in 60bedcf). The repeat visible at the far zoom is the tile's world scale in UNITY (U-117), not the seams (1.01 / 1.12).

### B-121 · BLENDER · Done · C1
Goal: Cartoon HUD art (§9.3): three gauges (Suit power, oxygen, gravity readout) as dial faces + needles on one 1024² sheet with ink and paper, the Escape Line as a hand-painted dotted line tile (512×64) with its little sign (≤ 256²); Patrick Hand lettering on the sign only (D-090).
Accept: §9.7 (ink, cel, palette, original); the review sheet composes the HUD at 1080p over the B-114 plains.
Files: blender/scripts/build_hud_v3.py, Assets/_Game/Art/ui/hud/
Depends: B-110, B-124
Lead notes: Cycle 242: ink per contract v3.1 (B-124 first); no fuel gauge exists (D-103); the ship readouts are altitude, vertical speed, tilt, thrust-to-weight. Cycle 246: PREVIEW ACCEPTED (review_b121_hud_preview.png 21:58, 1080p over the B-114 plains): three brass-ringed dials with red danger arcs and drawn needles (bolt, bubbles, falling ball), paper and ink per v3.1; the Escape Line as a dotted mustard line with its little sign reads at 1x. Ruling: the sign ships BLANK; UNITY letters it in Patrick Hand at runtime (U-104), so no font is baked into art and the words can change. Export in your next lock batch with B-128 and B-122 (queue #2). Done on UNITY's HUD capture (U-104). Cycle 247: EXPORT VERIFIED (f612225; log 23:34:52 OK: gauges 1024² with parts + needles json, escape_line 512×64 seam 0.00, escape_sign 192×224 blank with `lettering: runtime` and pivot [0.5, 0]; peak 988 MB). Done on U-104's HUD capture. Cycle 257: DONE (in the game: U-104's captures 0b4af5a show the three gauges with their needles at 12 Hz, the Escape Line tile at the line and the blank sign lettered at runtime; imported clean, HudGaugeTests green).

### B-122 · BLENDER · Done · C1
Goal: B-123 step 2 as a **rig set, not frame sheets** (D-111): `ships/pilgrim/rig` = one sheet ≤ 2048² of parts at PPU 64 (hull, nose cone, the three fin-legs with pads, the exhaust bell, the hatch, the porthole; the top-view hull and fins as parts too) plus `rig.json` in the contract §11.3 schema with bones (fin_1..3, leg pads, hatch), per-part pivots and sockets (tail exhaust, legs, door), and bone clips sampled at 12 Hz: idle fin wobble (8), leg flex on land (8), hatch open (6); thrust stretch, cut squash and the ±35° tilt are UNITY's root transforms, never drawn. Plus `ships/pilgrim/puff` (8-frame exhaust loop ≤ 128²). No face (D-101); ink per v3.1; the parts carry the B-123 detail (rivets, seams, hatching).
Accept: ten §9.7 boxes; the rig review sheet shows the assembled ship at 1x = 768 px tall on the pad beside the surveyor and tilted in flight, plus the fin-wobble loop; one sheet + puff ≤ 2 textures; json validates against §11.3; sockets listed for UNITY.
Files: blender/scripts/build_pilgrim_v3.py, Assets/_Game/Art/ships/pilgrim/
Depends: B-123, B-124
Lead notes: Cycle 242: rewritten for D-101/D-102 (the 18:58 sources were the horizontal faced rocket; keep what transfers: fins, puffs, palette). Cycle 245: rewritten again as a rig set (D-111): your 21:48 split plan showed 5 side sheets + 2 top + puff = 8 textures for the ship alone, which breaks the per-planet texture count the moment the ship is on the pad; a 768 px rocket is a rigid body with a few moving parts, so it is parts + bones (pillar 4: shared rigs), one sheet. The poses you drew become the part drawings; UNITY's U-103 builds the rig with the same RigSetBuilder path as the flora. Cycle 246: PREVIEW ACCEPTED (review_b122_pilgrim_rig_assembled_preview.png 22:26): the rig assembled from 11 parts through the bone chain at 1x = 768 px on the pad beside the surveyor (the 12 m scale checks out), ±35° root tilt, fin_wobble 8 loop / leg_flex 8 / hatch_open 6 (dark doorway) / top fin_wobble; one 920×912 parts sheet + puff = 2 textures; ink 2.0–3.0 / 1.0–1.5 px; no face; the seven sockets listed for UNITY. Export in your next lock batch (queue #2). Done on UNITY's side capture of the real rig (U-103). Cycle 247: EXPORT VERIFIED (f612225; log 23:38:15 OK rig 920×912, 11 parts, 2 plants, json valid §11.3; 23:38:17 OK puff 1052×128, 8 frames 128² at 12 fps, ink and palette pass; the puff's unticked boxes (face, motion, idle, original, style) are not applicable to an FX loop, accepted). Done on U-103's captures of the drawn ship. Cycle 254: DONE (in the game: U-103's captures show the rig on the pad, tilted with puffs at the sockets, at the Escape Line and top-down in Space; RigSet / RigSetBuilder read the clips and sockets, controller 4 states, PilgrimRigTests + ShipSideTests ×7 green).

### B-123 · BLENDER · Done · C1
Goal: The Pilgrim redesigned upright and faceless (D-101, D-102; §9.3 v4.1): a bendy vintage rocket standing on its tail with three or four fins as legs, a porthole, panel seams and rivets as drawn detail, the teal/mustard/red palette kept, round puffs; no eyes, mouth or face-like arrangement. Step 1 only: a design sheet (standing on the pad, tilted ±35° in flight, thrust stretch, cut squash, top view) at preview size with the "what makes it ours" line, for LEAD's review.
Accept: the §9.7 boxes that apply to a design sheet (ink v3.1, two shadow tones, palette, original, no face); readable at 1x beside the surveyor (the ship is ≈ 12 m tall = 768 px, so draw the sheet at 0.5x with a 1x detail crop).
Files: blender/scripts/build_pilgrim_v3.py, blender/sources/ships/pilgrim_v3_design.blend
Depends: B-124
Lead notes: Cycle 242. Light (preview only). Supersedes B-117's design (Done, kept for history). Cycle 243: STEP 1 OK → DONE (36f33a0, review_b123_pilgrim_design_preview.png 20:43). §9.8 pass: a teal cigar hull on three mustard fin-legs with brown pads and red toes, mustard nose with a red knob, ONE off-centre brass porthole, off-white riveted band, panel seams, rivet rows, hatching on the shadow flank; nothing face-like (D-101 pass). Thrust stretch along the axis and cut squash read; the ±35° tilts carry the puffs along the ship's own axis. Keep as drawn. B-122 released; its review sheet must show the ship at 1x = 768 px tall beside the surveyor so the 12 m scale is checked there.

### B-124 · BLENDER · Done · C1
Goal: Pipeline v4.1 (D-100; contract v3.1 §11.1): `gp_raster` / `render.py` draw the outer silhouette at 2–3 px and interior lines at 1–1.5 px (±20 % jitter kept), support a second shadow tone per colour (mid + deep) in the palette check, and add an interior-detail layer per asset (seams, folds, veins, rivets, hatch and dot texture marks) that the review sheet shows in a 2× detail crop with measured widths. Prove it on `characters/calibration_v3/side` re-rendered: the blob gains seam lines, a few hatch marks and two shadow tones.
Accept: review sheet measures outer 2–3 px / interior 1–1.5 px; palette check passes with two shadow tones; json still validates (§11.2); the ten §9.7 boxes on the sheet; log OK; peak RAM in the status.
Files: blender/render.py, blender/review.py, blender/scripts/gp_*.py, Assets/_Game/Art/characters/calibration_v3/
Depends: —
Lead notes: Cycle 242. First: every re-ink and every C1 export runs through it. Light previews until the gate; one heavy export. Cycle 243: DONE (d9ace05 + the 20:59:35 export, log OK: calibration_v3/side 1964×324, ink outer 2.0–3.0 / interior 1.0–1.5 px measured, 40 interior strokes per frame, palette with mid + deep tones 100 %, ten-box sheet with the 2× detail crop; the blob still pops off the painted plains at 1x). The ten-box review sheet is the §11.7 standard from here.

### B-125 · BLENDER · Done · C1
Goal: Surveyor re-ink (D-100): `characters/surveyor/side` (all 98 frames, same indices) and the design sheet redrawn at v3.1 ink with interior detail (helmet ring seams and rivets, glove and boot seams, pack straps and buckle, hose ribs, stripe stitching, a few hatch marks on the pack) and two shadow tones; design, poses and clips unchanged.
Accept: ten §9.7 boxes; widths measured on the sheet; the face reads at 1x on the plains through the glass; json indices unchanged (UNITY needs no change); sheet ≤ 2048.
Files: blender/scripts/build_surveyor_v3.py, Assets/_Game/Art/characters/surveyor/
Depends: B-124
Lead notes: Cycle 242. One heavy export under the gate and D-091. Cycle 243: PREVIEW ACCEPTED (88a1764, review_b111_surveyor_design_preview.png 20:25: helmet-ring rivets and seams, glove and boot stitching, strap and buckle, hose ribs, hatch on the pack, mid + deep tones; 75 interior strokes per frame; the face reads through the glass at 1x). Done on the side export (98 frames, same indices, log OK). Cycle 244: the 21:11 export FAILED the new below-ground check (conk_out frames 68–71: the gloves sat under the ground line; the check did its job); BLENDER fixed the pose, re-export is #1 in the heavy job queue (short job) because U-108's stills need this sheet. Cycle 245: DONE (bd69423; log 21:54:57 OK: 98 frames, same indices, 2.0–3.0 / 1.0–1.5 px, 80 interior strokes per frame, palette 100 %, conk_out passes the below-ground check, peak 892 MB; the review sheet's STALE stamp predates that OK line by seconds and STALE.txt is empty). UNITY imports it in U-108.

### B-126 · BLENDER · Done · C1
Goal: Snoozle v2, no face (D-101, D-100): `flora/earth/rigset` redrawn as a dandelion clock with no eyes or mouth; personality through motion: sway idle on the beat, a head that opens and shuts (swaps `head_open` / `head_half` / `head_closed`), leaves that lift (`leaves_rest` / `leaves_up`), react = turn and bounce with the head opening; v3.1 ink with seed-head detail lines, stem ribs, leaf veins, two shadow tones; ≤ 6 bones, one texture.
Accept: ten §9.7 boxes; the assembled 12-frame loop on the review sheet at 1x on the plains; json validates against contract v3.1 §11.3 (no face parts); UNITY's RigSet reads it with no code change (same part/bone/swap schema).
Files: blender/sources/flora/earth_rigset.blend, Assets/_Game/Art/flora/earth/
Depends: B-124
Lead notes: Cycle 242. The biggest visible change for the owner; after B-124. Cycle 243: ART ACCEPTED (5fd7d91 + the 20:59:54 export, review_b126_earth_rigset.png: a dandelion clock with seed rays and no face, head open → half → bud → open again, leaves lift, stem ribs and leaf veins, mid + deep tones, 7 parts on 216×84, assembled loop at 1x on the plains reads as a plant with character). Schema note: the json adds `replaces_part` swap slots and an idle `swap_cycle`; UNITY reads them in U-108. Done on UNITY's earth_c0 re-shoot with it. Cycle 247: DONE: U-108's v41 re-shoot (23:15) runs 48 faceless snoozles with the head cycle and the leaf lift live; no importer error; RigFloraTests green.

### B-127 · BLENDER · Done · C1
Goal: Gus re-ink (D-100): `creatures/earth/gull` at v3.1 ink with feather marks on wings and tail, crest detail, foot webbing lines, two shadow tones; clips, frames and indices unchanged; add `fly` (8–10 frames loop, wings beating) since the game flies the gull.
Accept: ten §9.7 boxes; widths measured; json valid; indices of idle/walk/react/bump unchanged, fly appended.
Files: blender/sources/creatures/earth_gull_v3.blend, Assets/_Game/Art/creatures/earth/gull/
Depends: B-124
### B-128 · BLENDER · Done · C1
Goal: Icons for the seven tile items that have none (U-091 found they show nothing off their home planet once planet bundles unload): soil, turf, regolith, mercury_regolith, mercury_basalt, sulfide, tessera, as `icons/<item>` 64×64 in the v3.1 ink style (a drawn cube of the material with two shadow tones), on the existing icons sheet rules.
Accept: ten §9.7 boxes that apply (ink, tones, palette per planet, original); the seven files import with no error; UNITY's ItemIcons test lists none missing.
Files: blender/scripts/build_icons.py, Assets/_Game/Art/icons/
Depends: B-124
Lead notes: Cycle 245 (D-110 answer 3). Small; a while-waiting item (numpy previews first). Drop the fuel and tank icons in the same pass (D-105). Cycle 246: PREVIEW ACCEPTED (review_b128_icons_preview.png 22:30): eight drawn material cubes (snow included, accepted) with top colour + mid + deep tones and per-material marks, readable at 1x; ink 2.0–2.9 / 1.0–1.5 px; no fuel icons exist under Art/icons any more (U-107 archived them), nothing to drop. Export in your next lock batch (queue #2); UNITY sets `def.icon` for the eight keys (U-091 notes). Cycle 247: EXPORT VERIFIED (f612225; log 23:34:53 OK: eight icons/<item>/base 64×64, ~1 KB each). Done on UNITY's import with the def.icon keys (the ItemIcons test lists none missing). Cycle 257: DONE (the eight icons imported clean in e978700 / 60bedcf with `def.icon` set for the eight keys; EditMode 326/326). The Accept's "ItemIcons test" never existed as such; an icon-coverage assert is on UNITY's While-waiting list.

Lead notes: Cycle 243: PREVIEW ACCEPTED (1db52ef, review_b113_earth_gull_preview.png 20:27: feather shafts, web lines, chest specks, deep tone; fly = two wingbeats with the crest dragging; indices 0–39 unchanged, fly 40–51). Deviation accepted: fly is 12 frames, not the card's 8–10; the contract (§11.2: a flier's walk, 12–16) and ArtRules.ClipCap rule, the card was wrong. Done on the export. Cycle 244: DONE (2235cf6; log 21:13:13 OK: 1968×396, 52 frames, idle 0–9 / walk 10–21 / react 22–29 / bump 30–39 / fly 40–51, ink 2.0–3.0 / 1.0–1.5 px, peak 675 MB). UNITY wires `fly` in U-108.

### B-129 · BLENDER · Done · C2
Goal: Earth flora rig set export: `flora/earth/rigset` holding all six Earth plants (snoozle v2 + Nodbell, Shiverbarrel, Curlfrond, Whiptuft, Thriftcushion; 44 parts on one sheet ≤ 512², ≤ 6 bones each, no face parts, a `biomes` list per plant) from the approved sources (5cdca3b, review_c2_earth_rigs_preview.png); the snoozle's part names, swaps and clips unchanged so UNITY's scene keeps working the moment it re-imports.
Accept: log OK; json valid §11.3 with `biomes` on every plant; the ten §9.7 boxes per plant on the stamped review (assembled at 1x beside the surveyor on the plains, the sway and react loops); sheet ≤ 512², one texture; the snoozle's parts pixel-identical to B-126's export.
Files: blender/scripts/build_c2_earth_rigs.py, Assets/_Game/Art/flora/earth/
Depends: B-126
Lead notes: Cycle 249 (D-115): SOURCES ACCEPTED (5cdca3b; review_c2_earth_rigs_preview.png 23:59: five faceless plants, bone cascades for the out-of-phase motion, bones 4 / 2 / 4 / 4 / 6, 44 parts on 500×212, ink 2.0–3.0 / 1.0–1.5 px). Export in one batch with B-130 (≤ 10 min) in your queue slot between UNITY's C1 checks. UNITY's biome placement is U-110 (Backlog until U-106); until then any plant may spawn on the plains, which is fine for the C1 build. Cycle 249 (00:2x): EXPORT VERIFIED (558976a; log 00:22:23 OK: 504×212, 36 KB, 44 parts, 6 plants, peak 668 MB; `biomes` on all six; the snoozle's seven parts pixel-identical to B-126 per BLENDER's crop-by-crop compare; review_b129_earth_rigset(_assembled).png stamped 00:22). Done on UNITY's next clean import (CartoonSmoke green with this sheet; U-103's check will carry it). Cycle 254: DONE (in the game: all six plants at 1x beside the pad in u103/1_pad.png; the set imported clean in 60bedcf with its 6-state controller after UNITY's PlantSpan reader fix; CartoonSmoke + RigFloraTests green).

### B-130 · BLENDER · Ready · C2
Goal: Earth ground strips export: `terrain/earth/ground_strip` (grass), `ground_strip_soil`, `ground_strip_stone` in U-100's contract (8 frames of 64×128 per material = 1 × 2 m at PPU 64; the bottom 8 px of frame 0 is the fill tile), drawn 1 m grass lip, paper-grain fill, v3.1 ink; from the approved source (dde330d, review_c2_earth_ground_preview.png).
Accept: log OK; edge joins within a material ≤ 1/255 mean difference and the silhouette ink identical on all 48 frame edges (as measured on the preview); a json per sheet with `tile: true` in x; the ten boxes that apply; UNITY's U-111 swaps the placeholder by key.
Files: blender/scripts/build_c2_ground_strip.py, Assets/_Game/Art/terrain/earth/
Depends: —
Lead notes: Cycle 249 (D-115): SOURCE ACCEPTED (dde330d; review 23:59: grass / soil / stone with pebbles, roots and cracks; joins 0.6 / 0.6 / 0.8 per 255; the 1x composite on the plains with a stone outcrop and a dug hole reads as one drawn ground). Same export batch as B-129. Cycle 249 (00:2x): EXPORT VERIFIED (558976a; log 00:22:36 OK: three sheets 540×152, joins 0.63 / 0.62 / 0.81 per 255, silhouette identical on all 48 edges, `tile: true`; review_b130_ground_strips.png 00:22). Deviation ACCEPTED: frames are 64×152, not 64×128, with pivot [0.5, 0.842] on the ground line (`ground_line_px: 128`), so the sheet hangs 2 m below the line (what GroundStrip.cs draws today) plus 0.375 m of lip and tufts above it; no UNITY code change, the key swap only. Done on U-111's capture. Cycle 253: a fourth kind ACCEPTED, `terrain/earth/ground_strip_sand` (158484a sources; the same 8 × 64×152 contract, join 0.67/255, silhouette identical on all 64 edges; the rebuilt coast composite stands the surveyor on sand). Export as `terrain/earth/ground_strip_set` (four sheets, the three existing byte-identical) in BLENDER's next slot with B-135; U-111 maps coast columns to sand. Cycle 254: SAND EXPORTED AND VERIFIED (af83541; log 02:45:03 OK ground_strip_set: four sheets 540×152, grass / soil / stone byte-identical to 558976a, sand joins 0.67; LFS). Still Done on U-111's capture (grass, soil, stone, sand and a dug hole).

### B-131 · BLENDER · Done · C2
Goal: Earth camp props re-ink (the grey stand-ins in every still): `props/common/landing_pad`, `shelter_wall`, `shelter_door`, `smelter`, `storage_crate`, `lamp` redrawn as v3.1 cartoon sprites, no faces (D-101): ink 2–3 / 1–1.5 px, two shadow tones, drawn detail (planks, rivets, bolts, a smelter mouth with a drawn glow tone, a lamp with a drawn halo); sizes and pivots per the current manifest rows (ground line 10 px above the bottom; interactables keep mask R = 0.1); the door gets a 6-frame open clip, the smelter an 8-frame working loop, the lamp a 4-frame flicker.
Accept: the ten §9.7 boxes per prop on a stamped review (all six at 1x on the plains beside the surveyor and the Pilgrim rig); every file per the contract (color + json; emission only where the manifest has it); one sheet per prop ≤ 512²; UNITY imports with no key change.
Files: blender/scripts/build_props_common_v3.py, blender/sources/props/common_v3.blend, Assets/_Game/Art/props/common/
Depends: B-124
Lead notes: Cycle 249 (D-115). Previews first (lock-free), export in a later batch. These six sit in the owner's first frame every time; after the ship they are the most visible grey left. Cycle 250: PREVIEW ACCEPTED (09e1a63; review_b131_props_preview.png 00:3x: six props at 1x on the plains with the surveyor and the Pilgrim rig; ink 2.0–3.0 / 1.0–1.5 px, mid + deep tones, rivets, planks, bolts, a drawn smelter glow and lamp halo; no faces; door open 6 once, smelter working 8 loop, lamp flicker 4 loop; pad and wall joins 0.0/255; sizes pad 128×48, wall 64×176, door 88×176, smelter 112×192, crate 80×72, lamp 64×160, ground line 10 px up). Answers (D-117): (a) colour + json only; the card's mask / emission line is struck (it came from the v2 manifest rows); `"interactable": true` goes in the json and the glows stay drawn. (b) Yes, the type changes under the same keys, and ArtImporter un-addresses a colour map that sits beside a `.glb` (IsModelKey, U-075), so your export commit also removes the six `.glb` files and their v2 maps and switches the manifest rows; UNITY's U-113 (Backlog, its code half on the While-waiting list) makes ModelSwap keep the sprite + Animator when no model exists. Order: U-113 code committed → your export batch (≤ 10 min, queue #5) → UNITY's next check. Until then the wiring, lock-free (While-waiting #1). Cycle 254 (D-125, UNITY's P-45): the shelter wall becomes a stackable 1 × 1 m tile, 64×64, pivot bottom-centre, `tile` in x and y, no ground-line margin, so BaseBuilder's 1 × 1 wall cell shows it unsquashed and walls stack to any height; the door stays 88×176 (it scales uniformly into its 1 × 2 cell); pad, smelter, crate, lamp unchanged. Redraw the wall lock-free (While-waiting #2); the export still waits for U-113's code. Cycle 255: WALL TILE ACCEPTED (afcfa68; review_b131_props_preview.png 03:15: the 64×64 tile stacked 2 and 3 high round the door at 1x and a 3 × 3 stack at 2x reads as riveted corrugated panels with a strap at each joint, not as stripes; joins 0.0 in x and y; the other five props byte-identical). D-125's reopen condition is not met. Export still after U-113's code. Cycle 260: EXPORT VERIFIED (3548c6e7, 05:44:51–05:45:52 after UNITY's U-113 code commit 43fe88e9, D-117's order; log 05:45:51 OK props/common/camp_set: landing_pad 128×48, shelter_wall 64×64 (D-125), shelter_door 272×356, smelter 460×388, storage_crate 80×72, lamp 132×324, joins 0.00; the 24 v2 files removed, their metas deleted in UNITY's batch A commit 2; peak 727 MB; LFS). review_b131_props.png viewed: the camp at 1x on the plains with the walls stacked round the door, the clips and the 3 × 3 wall stack. Done on UNITY's batch A capture of the camp (U-113). Cycle 262: in the game on u113/camp_1x.png (pre-reviewed 07:0x); Done on UNITY's batch A hand-off commit. Cycle 262 (07:1x): DONE (in the game on u113/camp_1x.png, ae7b8cfc; the six sheets addressed and sliced, PropSpriteTests green).

### B-132 · BLENDER · Done · C2
Goal: Earth land creatures re-inked (your list coordination/reports/blender/c2_earth_creature_reink.md, order 1): stag, grey wolf, brown bear at v3.1 ink with faces kept (animals may have faces, D-101: pie-cut eyes, friendly or neutral, no bared teeth per D-087), interior detail and two shadow tones; clips per contract §11.2 (idle 8–12, walk 12–16, run / flee, react ≤ 16, bump ≤ 16; follow for the wolf); frames ≤ 192 px (bear ≤ 224 × 160); one sheet ≤ 2048² each; the below-ground check passing.
Accept: the ten §9.7 boxes per creature on a stamped review (1x on the plains beside the surveyor); json valid; where UNITY already binds a stag or wolf clip by index, the index is preserved or the change is in your status; one texture each.
Files: blender/scripts/build_creatures_earth_v3.py, blender/sources/creatures/earth_v3.blend, Assets/_Game/Art/creatures/earth/
Depends: B-124
Lead notes: Cycle 249 (D-115). Gus (B-127) is the reference. Design previews first, then one export batch for the three. The water creatures (pike, shark, squid) and the Hadal Maw rig follow as B-13x once these are in. Cycle 251: PREVIEWS ACCEPTED (dcaee7d; review_b132_earth_{stag,wolf,bear}_preview.png + the lineup, 01:15–01:17): stag 192×176 (idle 10, walk 12, react 8, bump 10, flee 12), wolf 160×128 (+ follow 12, flee 14), bear 224×160 on a 2048×1144 sheet (exactly the cap, accepted); ink 2.0–3.0 / 1.0–1.5 px, palette 100 %, faces kept with pie eyes, no teeth, dizzy stars not X eyes, nothing below the ground line; clip indices 0–3 = Gus's order, flee / follow by name. Deviations accepted: one .blend per creature (contract §11.1); the sheets' body sizes differ from the v2 SpeciesSpec (UNITY's U-114). Ruled D-119: no UNITY code gates the export (Creature.EnsureModel finds no GameObject under the key and the sheet path plays, as the gull does today), so export in your next slot (queue #2) with `replaces_v2` removing the eight stag / wolf v2 files (UNITY deletes the .meta files, D-016). Before it: fix the wolf review's surveyor placement (ValueError) so the stamped review carries the surveyor. Cycle 252: EXPORT VERIFIED (0f9e0ab, 01:45–01:52, one lock, peak 519 MB; logs/blender_2026-11-07.log 01:52:35 OK ×3: stag 1956×1076 / 52 frames, wolf 1964×788 / 66, bear 2048×1144 / 56, ink 2.0–3.0 / 1.0–1.5 px, palette 100 %; the eight stag / wolf v2 files deleted in the commit, the three .blend sources added, LFS; review_b132_earth_{stag,wolf,bear}.png stamped 01:48–01:52 with the surveyor beside each (the ValueError fixed in 4dcf83d)). UNITY's Editor generated the bear metas at 01:54 and dropped the orphan model metas; they go in UNITY's hand-off. Done on UNITY's clean import (CreatureTests green with the three sheets) and the U-114 capture. Cycle 262: in the game on u114/creatures_1x.png (the stag, wolf and bear at 1x; pre-reviewed 07:0x); Done on UNITY's batch A hand-off commit. Cycle 262 (07:1x): DONE (in the game on u114/creatures_1x.png, ae7b8cfc; EarthCreatureSheetTests green; the stag, wolf and bear at 1x beside the surveyor).

### B-133 · BLENDER · Ready · C2
Goal: Earth biome backdrops in the B-114 manner: painted watercolour layer sets for forest and coast (three layers each: far ridge, mid tree line or sea, near; 2048 × ≤ 1024 tiling in x; paper grain; Earth palette; nothing face-like), `backgrounds/earth_forest/layer0..2` and `backgrounds/earth_coast/layer0..2` with their scene jsons in the SceneLayout schema; the plains set stays as it is.
Accept: 2× tile check with no seam; ≤ 4 MB per PNG; a 1080p composite per biome at 1x with the surveyor; the ten boxes that apply; UNITY's StageLayers loads them by key with no code change.
Files: blender/scripts/build_backdrop_v3.py, Assets/_Game/Art/backgrounds/earth_forest/, Assets/_Game/Art/backgrounds/earth_coast/
Depends: B-114
Lead notes: Cycle 249 (D-115). After the B-131 and B-132 previews; previews lock-free, exports in one batch. Cycle 251: paths amended to `backgrounds/earth/forest/` and `backgrounds/earth/coast/` (contract §11.4 `backgrounds/<planet>/<scene>/`, the ParallaxLayers shape); the Goal's `earth_forest` / `earth_coast` names are struck. Sources written (1d83053); the previews (FFT washes, > 300 MB) run in your lock slot (queue #2), not lock-free. Cycle 252: PREVIEWS ACCEPTED (review_b133_earth_forest_preview.png + _coast_ 01:53–01:54): forest = sky + far ridge and treeline, mid tree line with trunks, near bushes with stumps and logs; coast = sky + open sea, a grassy sea stack with two rocks on the water, near sand with grass tufts and driftwood; watercolour, paper grain, no ink; the 2× tiled strips show no seam at the join line; the 1x composites with the surveyor read as one scene with the B-130 strips. Export in your next slot with B-134 (queue #2). Follow-up on the list: a sand ground strip for the coast (the composite stands the surveyor on soil). Cycle 253: EXPORT VERIFIED (27143e1; log 02:19:50 OK forest: layer0 2048×1024 2.3 MB seam 0.87, layer1 2048×640 seam 0.43, layer2 2048×384 seam 0.52 + forest.json; 02:20:21 OK coast: 2048×1024 seam 0.85, 2048×512 seam 0.63, 2048×384 seam 0.50 + coast.json; parallax 0.1 / 0.35 / 0.6; all six pixel-identical to the accepted previews rolled to their quiet column; LFS; review_b133_earth_{forest,coast}.png 02:20). UNITY's side: CartoonStage pins EarthScene = plains; the biome pick is U-110's (note added). Done on U-110's forest and coast captures.


### B-134 · BLENDER · Done · C1
Goal: The surveyor's five missing C1 clips (Bible §12 C1 "the surveyor's full clip set"; contract §11.2 surveyor list) on a second sheet `characters/surveyor/side_b` (D-121: `side` is 1960 px tall at 98 frames, the cap), same 192×192 frames, pivot, PPU 64, v3.1 ink and the B-125 character: dig (loop 8–12, the pick swings, dirt chips), build (loop 8–12, hammer + a part snapping in), surprise (eye-pop, once ≤ 16, hat lift), jetpack (loop 8–12, pack flame, scarf streams), climb_in (once ≤ 16, up the fin-leg and through the hatch; its last frame hides the surveyor). Clip names unique across the two sheets; `side` untouched.
Accept: the ten §9.7 boxes on a stamped review (each clip as a strip beside `side`'s idle at 1x, the 2× ink crop); json valid (`style: v3`, fps 12, the same pivot as `side`); sheet ≤ 2048²; log OK; UNITY's U-115 plays all five from the controller.
Files: blender/scripts/build_surveyor_v3.py (or the B-125 builder), blender/sources/characters/surveyor_side_b.blend, Assets/_Game/Art/characters/surveyor/side_b_color.png + side_b.json
Depends: B-125
Lead notes: Cycle 251 (D-121). C1 scope that sat in the Backlog note since cycle 238; it ranks above the C2 exports once its preview is accepted. Preview lock-free (While-waiting #2), export in one short batch. U-105's ResolveOn stand-ins (land_hard, jump_anticipate, …) are UNITY states, not contract clips: these five are the whole gap. Cycle 252: PREVIEW ACCEPTED (review_b134_surveyor_side_b_preview.png 01:54; sheet 1956×1172, 219 KB): dig 10 (pick wind-up, swing, chips), build 10 (hammer, the part snapping in), surprise 12 (eye-pop, antenna lift), jetpack 10 (pack flame, puff trail), climb_in 14 (a smear-line zip whose last frames hide the surveyor; UNITY plays it at the door socket so the smear ends at the hatch); ink 2.0–3.0 / 1.0–1.5 px, palette 100 %, json valid; no idle on this sheet by design (`side` keeps it). Export in your next slot (queue #2); UNITY's U-115 picks it up. Cycle 253: EXPORT VERIFIED (27143e1; log 02:19:16 OK characters/surveyor/side_b 1956×1172 396 KB, 56 frames 192×192, dig 10 / build 10 / surprise 12 / jetpack 10 / climb_in 14, ink 2.0–3.0 / 1.0–1.5 px, palette 100 %; pivot [0.5, 0], a `hatch` socket (1.0, 1.05 m from the pivot) on every frame; LFS; source surveyor_side_b.blend). Done on U-115's import (SurveyorAnimTests: 0 stand-ins for the five). Cycle 257: DONE (in the game: 0b4af5a imports side_b and rebuilds the surveyor controller with its five clips; SurveyorAnimTests bind them; U-115 Done).

### B-135 · BLENDER · Done · C2
Goal: Earth water creatures re-inked (your list coordination/reports/blender/c2_earth_creature_reink.md, order 2): pike, shark, squid at v3.1 with faces kept (pie-cut eyes, no bared teeth, D-087 / D-101), two shadow tones, interior detail; clips per §11.2 with `swim` 12–16 as the travel clip (D-119), idle 8–12, react ≤ 16, bump ≤ 16, flee ≤ 16; one sheet ≤ 2048² each; the below-ground check replaced by a below-water-floor check in your status.
Accept: the ten §9.7 boxes per creature on a stamped review (1x in the coast water beside the surveyor); json valid; clip indices 0–3 in Gus's order, the rest by name; one texture each.
Files: blender/scripts/build_creatures_earth_v3.py, blender/sources/creatures/earth_{pike,shark,squid}_v3.blend, Assets/_Game/Art/creatures/earth/
Depends: B-132
Lead notes: Cycle 251 (D-119). Design previews first (While-waiting #3), then one export batch. The Hadal Maw is B-136 (Backlog) as a §11.3 rig set. Cycle 253: PREVIEWS ACCEPTED (9c18daa; review_b135_earth_{pike,shark,squid}_preview.png 02:18–02:19, 1x in the coast sea with the surveyor): pike 128×80 (idle 8, swim 12, react 8 dart, bump 8, flee 12), shark 224×128 (idle 10, swim 14, react 8 turn-away, bump 10, flee 12), squid 320×144 (idle 12, swim 12 jet pulses, react 10 with an ink cloud, bump 10, flee 12); one pie eye each, closed mouths, no teeth; ink 2.0–3.0 / 1.0–1.5 px, palette 100 %; pivot [0.5, 0.5], swim at index 1; floor clearance 0.38 / 0.87 / 0.70 m (hand-off to UNITY on the card). Export in your next slot (queue #2) with the ground-strip set. Cycle 254: PIKE + SHARK EXPORTED AND VERIFIED (af83541; log 02:41:36 OK pike 1976×332, 48 frames 128×80; 02:42:13 OK shark 2048×788, 54 frames 224×128; ink 2.0–3.0 / 1.0–1.5 px, palette 100 %; LFS; the two .blend sources). SQUID FAILED (02:44:51: frame 54 touches the 2 px edge, nothing written): pull frame 54 inside the gutter and re-export in your next slot (queue #2). Done on all three imported clean (UNITY's U-114 batch). Cycle 255: SQUID EXPORTED AND VERIFIED (c4225fd; log 03:09:02 OK 1940×1476, 56 frames 320×144, idle 12 / swim 12 / react 10 / bump 10 / flee 12, inside the 2 px edge, ink 2.0–3.0 / 1.0–1.5 px, palette 100 %, peak 632 MB; LFS). All three swimmers exported; the preview-vs-export mismatch that cut frame 54 is fixed at the root (8c69536: fakegp uses Blender's stroke ids, previews now pixel-identical to exports). Done on UNITY's U-114 import + capture. Cycle 263: DONE (in the game on u114/swimmers_1x.png; SwimmerTests green).

### B-137 · BLENDER · Ready · C2
Goal: The painted Sun as a rig set (D-123; design accepted from review_sun_disc_design_preview.png, 43ba8f5): `planets/sun/disc_rig.json` in the Saturn-rings shape with parts on one sheet ≤ 2048²: the body drawn at 2x and exported at 0.5x (≤ 1024², the game's r 900 px), the flame-tongue ring as one part Unity rotates slowly and pulses, the corona as a 512² translucent wash scaled 4x, two prominence parts on limb sockets; no face (D-101); the drifting spots as a 12-frame idle on the body if it fits the sheet, else static.
Accept: the ten §9.7 boxes that apply on a stamped review at the game's size on the B-120 starfield with the Earth disc at true ratio; json valid; every part inside the 2 px edge; the sheet ≤ 2048²; log OK.
Files: blender/scripts/build_sun_v3.py, blender/sources/planets/sun_v3.blend, Assets/_Game/Art/planets/sun/
Depends: B-119
Lead notes: Cycle 253 (D-123). Parts preview lock-free (While-waiting #3), export in a later slot after B-135. The Sun stays a lit spheroid through C1; UNITY's U-116 (Backlog) swaps it in with U-110 / U-111. Cycle 254: PARTS PREVIEW ACCEPTED (88ceb01; review_b137_sun_parts_preview.png 02:38: the assembled Sun on the B-120 starfield with the Earth disc at true ratio, body 960², one flame tongue 260×180 instanced ×14 alternating 1.0 / 0.62, corona 512² breathing, two prominences; one sheet 2048×960 at 0.5x, no part on the 2 px edge). Deviations ACCEPTED under D-123: one tongue part instanced instead of a ring part (a 0.5x ring would be ~1220 px and cannot share the sheet), the body static (the spots drift as a UNITY tint drift or not at all; no 12-frame idle). Export in your next slot (queue #2); U-116 rotates the ring and pulses the corona. Cycle 255: EXPORT VERIFIED (c4225fd; log 03:09:39 OK planets/sun/disc_rig: sheet 1900×928 944 KB, parts body 928², tongue 216×148, prominence_a 128×140, prominence_b 100×104, corona 512²; ink on screen 2.0–3.0 / 1.0–1.5 px; peak 1009 MB; LFS; disc_rig.json with the orders, the 14-instance ring at 0.97 R with alt scale 1.0 / 0.62, spin 2°/s, pulse 0.08 at 110 bpm stepped 12 Hz, the corona breathe 0.03, the prominences at 100° / 280°). review_b137_sun_rig.png viewed at the game's size beside the Earth disc at true ratio: reads as the accepted design. Done on U-116's Space capture.

### B-138 · BLENDER · Done · C2
Goal: Edge audit of every committed v3 sheet exported before the 2 px edge check existed (B-119 discs + Luna + Saturn ring parts, B-120 layers, B-121 HUD parts, B-122 rig parts, B-124 calibration, B-125 surveyor `side`, B-126 / B-129 rig set, B-127 gull, B-128 icons, B-130 strips, B-132 creatures): frames or parts whose ink touches the 2 px gutter, the ink widths and the palette hit, measured lock-free from the committed PNGs and jsons.
Accept: `coordination/reports/blender/edge_audit_2026-11-07.md` with one row per key (frames checked, offenders by index, widths, palette %); every offender listed with its fix; the fixes exported in one later slot and the table re-run green.
Files: blender/scripts/edge_audit.py, coordination/reports/blender/edge_audit_2026-11-07.md
Depends: —
Lead notes: Cycle 253. Three of the last four export paths failed the edge check on first measure (B-131 lamp, B-134 zip, B-135 pike / shark); the older sheets were never measured. Read-only, ~100 MB, so it runs beside UNITY's Editor. Cycle 254: DONE (836f558; coordination/reports/blender/edge_audit_2026-11-07.md: 20 sheets, 0 offenders; rig parts flora 44 / Pilgrim 11 / gauges 6 none cut; 11 single images clear; tool blender/scripts/edge_audit.py read-only, 55 MB, 4 s). No re-export needed; the tool runs on every export from now on (render.py's edge check).

### B-139 · BLENDER · Done · C2
Goal: C2 Mars design prep (Bible §12 C2 order 2; §7.2 Mars): the Mars palette strip checked against §9; five faceless Mars plant designs as (d, M, pose) drawing functions in the Earth rig-set manner; the canyon and dust-storm backdrop studies (far / mid / near, the storm as a near layer with wind streaks); a Mars creature re-ink list like coordination/reports/blender/c2_earth_creature_reink.md (sizes, clips, order); the Mars camp props that differ from Earth's named.
Accept: one review per group (plants at 1x on a Mars ground strip beside the surveyor; the two backdrop composites at 1080p with the 2× seam check; the list as a report); the ten boxes self-checked; nothing exported.
Files: blender/scripts/build_c2_mars_*.py, coordination/reports/blender/c2_mars_designs.md
Depends: B-129
Lead notes: Cycle 253. Previews only when free RAM allows (fakegp ~150 MB; FFT backdrops in your slot). LEAD accepts the designs before any Mars card is written, like C2 Earth (cycle 245). Cycle 254: PALETTE ACCEPTED (cb88c5f, c2_mars_designs.md §1: dust white / rust / butterscotch sky / ice teal / lichen olive / salmon haze / umber, every check passing: contrast ≥ 2 under the ink, chroma ≤ Earth's max, closest pair dE 20, the olive reads on rust and butterscotch) → into `meridian.v3.PALETTES["mars"]` and `ui/palettes/mars/strip` (export in your next slot, D-125 (2)). The five plants' preview (02:47) is reviewed on your hand-off. Cycle 255: PLANTS ACCEPTED (8c69536; review_b139_mars_plants_preview.png: Rustbell, Puffpod, Frostcurl, Pipereed, Scree creeper at 1x on the Mars stand-in beside the surveyor, drawn 1.5× for 0.38 g, idle 8 + react 4, ink 2.0–3.0 / 1.0–1.5 px, Mars palette 100 %) with one change before the rig-set sources: the Puffpod's single curved seam with a dot each side reads as a closed eye at 1x (D-101), split or offset it. Ground strips ACCEPTED on the numbers (81d36d4: regolith + basalt in the B-130 contract, joins 0.55 / 0.58, silhouette identical on 32 edges; viewed with the Mars cards). `ui/palettes/mars/strip` EXPORTED (c4225fd; 8×1 + strip.json). The canyon + dust-storm studies run in your slot (queue #2). Cycle 256: Puffpod fix ACCEPTED (9e9b06d: two off-centre seams, irregular speckles, no face read). Mars rig-set dry run ACCEPTED (a4c9395: 26 parts on 504×216, bones 3 / 2 / 4 / 4 / 2, biomes per plant, idle with Unity's maths + react per plant; exports as B-140). Dustskater ACCEPTED (709a5bb: 128×80, idle 10 / walk 12 / react 8 / bump 10 / flee 12, a butterscotch dome with rust bands on skate pads, ink and palette measured). Scree stalker (a3b7222, tail sign fixed fd9f5c8) and tube lurker (fd9f5c8) are reviewed when their images render in your slot. D-126 rules the lurker's hole: a separate `props/mars/tube_mound` and a hole-less creature. The Mars work now has its own cards: B-140 (rig set + strips export), B-141 (backdrops), B-142 (creatures + the mound); B-139 goes Done when the backdrop studies and the two pending creature reviews are in. Cycle 258: DONE. Every part accepted: the palette (D-125), five plants (+ the Puffpod fix), the rig-set dry run, the regolith + basalt strips, four creature designs (dustskater cycle 256; scree stalker 192×96 with follow, tube lurker 160×64 hole-less, polar crawler 144×64 curling into a ball: cycle 258, review_b139_mars_{scree_stalker,tube_lurker,polar_crawler}_preview.png, ink 2.0–3.0 / 1.0–1.5 px, Mars palette 100 %, no edge or ground hits), the tube mound den (review_b142_tube_mound_preview.png: the lurker peeks over the rim and ducks to the eyes), the report (5bb66bb) and the README sections. The backdrop studies continue under B-141; the exports under B-140 / B-141 / B-142.

### B-140 · BLENDER · Ready · C2
Goal: C2 Mars flora and ground export (the accepted B-139 sources): `flora/mars/rigset` (the five Mars plants as one §11.3 rig set, 26 parts, bones ≤ 4, swaps, `biomes` per plant, the Puffpod D-101 fix in) and `terrain/mars/ground_strip` (regolith) + `ground_strip_basalt` in the B-130 contract (8 × 64×152, pivot on the ground line, `tile: true`).
Accept: log OK; rigset.json valid with `biomes` on every plant; the strips' joins ≤ 1/255 and the silhouette ink identical on all frame edges; the ten boxes per plant on the stamped assembled review at 1x beside the surveyor on the Mars strips; sheets ≤ 512² (rig set) and 540×152 (strips); UNITY's U-118 imports with no key change.
Files: blender/scripts/build_c2_mars_rigs.py, build_c2_mars_ground.py, Assets/_Game/Art/flora/mars/, Assets/_Game/Art/terrain/mars/
Depends: B-139
Lead notes: Cycle 256. New keys, nothing replaced: export in one BLENDER slot ≤ 10 min after U-106 (D-115: C2 exports below the C1 checks). The Mars 3D path keeps working until U-118 switches the planet. Cycle 257: export readiness done (b0e3a53: the rig-set row with its review script, the Mars strip set dry-run into a scratch dir 540×152 ×2, joins 0.55 / 0.58, 32 edges identical, the Earth strips byte-identical). Export in a slot after U-106. Cycle 260: EXPORT VERIFIED (b99b8c27; log 05:30:45 OK flora/mars/rigset 504×216 28 KB, 26 parts, 5 plants, peak 345 MB; 05:30:51 OK terrain/mars/ground_strip + _basalt 540×152, joins 0.55 / 0.58, silhouette identical on 32 edges; LFS; imported clean in 43fe88e9). review_b140_mars_rigset_assembled.png viewed: the five plants' idles with Unity's maths and their reacts. Done on U-118's Mars capture.

### B-141 · BLENDER · Ready · C2
Goal: Mars biome backdrops in the B-133 manner: `backgrounds/mars/plains`, `backgrounds/mars/canyon` and a `backgrounds/mars/storm` layer set (three layers each, 2048 × ≤ 1024 tiling in x; the dust-storm wall as a near layer with wind streaks and a salmon-haze far band; the Mars palette; paper grain; no ink outline; nothing face-like), scene jsons in the SceneLayout schema.
Accept: the 2× seam check with no seam; ≤ 4 MB per PNG; a 1080p composite per set at 1x with the surveyor on the Mars strips; the ten boxes that apply; UNITY's ParallaxLayers loads them by key with no code change.
Files: blender/scripts/build_backdrop_v3.py, Assets/_Game/Art/backgrounds/mars/
Depends: B-139
Lead notes: Cycle 256. Studies first in your next slot (FFT washes), LEAD accepts, then one export batch after U-106. Cycle 257: sources written (9cb766f: canyon layer0 butterscotch sky + far mesas, the storm set with the dust wall as the near layer) and the export rows + dry-run path in (e6f74ae); the FFT studies render in BLENDER's slot from 04:22 and are reviewed next tick. Cycle 259: STUDIES ACCEPTED (the 05:13 slot re-run; review_b141_mars_canyon_preview.png + _storm_: canyon = butterscotch sky with wind streaks, far mesa wall above the terraced tiers, near boulder field; storm = the same ground under a salmon dust veil that fades in from nothing with wind streaks, the far rims through the haze; seams 0.88 / 0.68 / 0.53 and 0.87 / 0.78 / 0.47, layers ≤ 2.2 MB, the 2× strips clean at the join). Export in one slot after B-140 (queue #2); U-118 loads them by biome. Cycle 260: EXPORT VERIFIED (570fb6ad; log 05:36:10 OK backgrounds/mars/canyon: 2048×1024 2.1 MB seam 0.88, 2048×640 seam 0.68, 2048×384 seam 0.53 + canyon.json; 05:38:24 OK backgrounds/mars/storm: 2048×1024 seam 0.87, 2048×640 seam 0.78, 2048×768 seam 0.47 + storm.json; the accepted studies' pixels; LFS; imported clean in 43fe88e9). Done on U-118's canyon and storm captures.

### B-142 · BLENDER · Backlog · C2
Goal: Mars creatures re-inked (c2_mars_designs.md order): dustskater (128×80), scree stalker (192×96, with follow), tube lurker (160×64, hole-less per D-126) with its den prop `props/mars/tube_mound`, polar crawler; faces kept (pie eyes, no teeth, D-087 / D-101); clips per §11.2; one sheet ≤ 2048² each; `replaces_v2` on the dustskater and scree stalker rows (their v2 models go in the export commit).
Accept: the ten boxes per creature on a stamped review (1x on the Mars strips beside the surveyor); json valid; clip indices 0–3 in Gus's order, the rest by name; the lurker draws behind the mound at its den in UNITY's capture.
Files: blender/scripts/build_creatures_mars_v3.py, Assets/_Game/Art/creatures/mars/, Assets/_Game/Art/props/mars/
Depends: B-139, U-118
Lead notes: Cycle 256. Previews lock-free as RAM allows (design only); the export waits for U-118's code because it replaces the two Mars models under live keys (D-119's order). Cycle 257: the D-126 split is done (c1d1377: `props/mars/tube_mound` 104×32 static with `den_for: tube_lurker`, drawn in front of the creature on the same pivot; the hole-less lurker idle peeks, react startles and ducks); the polar crawler designed (e15fb30: 144×64, idle 12 / walk 14 / react 10 curl / bump 10); export rows with `replaces_v2` on the dustskater and scree stalker (e6f74ae). The stalker, lurker, crawler and mound review images render in the 04:22 slot; reviewed next tick. Cycle 258: scree stalker, tube lurker, polar crawler and the mound ACCEPTED as designs. One addition before the export: the lurker's only idle is the den peek (head and neck), so a lurker that pauses in the open would show a bodiless pose; add a whole-body `idle_open` (8–10 frames) that Creature.cs plays away from the den (U-118 picks `idle` at the den, `idle_open` elsewhere).

### B-143 · BLENDER · Done · C1
Goal: Near-range planet discs (D-128, U-117 (2)): a static near frame per disc, `planets/<planet>/disc_near` ≤ 512² for the eight planets and `planets/earth/luna_near`, the same accepted drawing (frame 0 of the character idle) rendered at 8× the D-098 resolution with the ink at 2–3 / 1–1.5 px at that size; `build_discs_v3` only; the far discs, their clips and the Saturn ring parts untouched; `"style": "v3"` sidecars so the importer treats them as single sprites.
Accept: log OK for the nine near frames; each ≤ 512² and ≤ 1 MB; the stamped review shows each near frame beside its far disc at the ship-view zoom (~33×) with no pixel steps; UNITY's U-117 re-shoot of space_6 clean after the DiscSprite swap.
Files: blender/scripts/build_discs_v3.py, Assets/_Game/Art/planets/
Depends: B-119
Lead notes: Cycle 257. BLENDER's own proposal on UNITY's finding (a hard alpha edge in the 64 px source steps at 10× whatever the mesh). Pairs with UNITY's material side (alpha blend, no cutoff). One short slot (≤ 5 min) with the B-141 re-run, before U-117's re-shoot. Cycle 257 (05:1x, D-128): REDIRECTED. UNITY measured a 33× magnification in the ship view (Luna 21 px painted → ~700 px on screen), so the 2-texel soft limb cannot help and its run is dropped (keep the code; it is harmless). The near frames go in your next slot with the B-141 re-run (nine renders ≤ 512², ≤ 8 min together); U-117 (2) swaps to them above ~6×. Cycle 257 (05:2x, D-128 amended): five near frames only, where the gain is ≥ 2×: luna_near 8×, mercury 5.9×, mars 4.8×, venus 3.4×, earth 3.3× (the largest scale that fits 512²); none for Uranus, Neptune, Jupiter, Saturn (their close view is a named limit for a giants card); caps ≤ 512² and ≤ 1 MB stand. Cycle 259: EXPORT VERIFIED (d3af1e5; log 05:15:17 OK: five near frames, 121 s, peak 359 MB; mercury 512² at 5.86×, venus 512² at 3.42×, earth 512² at 3.28×, mars 512² at 4.82×, luna_near 356² at 8×, 124–257 KB each, LFS, `style: v3` + `near_of` sidecars; every far disc proven byte-identical before writing). review_b143_near_frames.png viewed: at the same screen size the far frame's blurry 33× stairs become a crisp inked limb on every near frame. Done on U-117's space_6 re-shoot with the DiscSprite swap. Cycle 263: DONE (in the game on the re-shot space_6: Luna's near frame at 13.3 px per texel, no steps).

### B-144 · BLENDER · Ready · C2
Goal: Mars camp prop designs (c2_mars_designs.md §5: the props that differ from Earth's camp): the ice drill rig, the hauler hull and cargo, the Meridian beacon and the warden pylon as v3.1 cartoon sprites in the Mars palette (no faces; one porthole or light at most per prop), with the clips that make sense (drill working 8, beacon pulse 4), sizes per the current manifest rows, the ground line 10 px above the bottom, `interactable` where used.
Accept: the ten §9.7 boxes per prop on a stamped preview at 1x on the Mars strips beside the surveyor; sheets ≤ 512² each; clips within caps; nothing exported until a Mars props export card.
Files: blender/scripts/build_props_mars_v3.py, blender/sources/props/mars_v3.blend
Depends: B-139
Lead notes: Cycle 258. Previews only, like B-131's first pass; the export replaces the v2 Mars prop models under the same keys (D-117's order) when U-118 opens. Cycle 259: six prop previews drawn and checked one per process (024462f, 172ae6e: ice drill rig 508², beacon 276×452, hull a 232×168, hull b 248×208, cargo 240×112, pylon 164×500; a dent on hull a that read as a smile straightened per D-101; the drill rig redrawn 1.9 × 3.7 m so its 8 frames fit 512²); the full review image renders in the 05:24 slot; reviewed next tick. Cycle 260: DESIGNS ACCEPTED (review_b144_mars_props_preview.png 05:28: the ice drill rig with its working loop, the Meridian beacon's pulse, the warden pylon's hum, the two hauler hulls and the cargo at 1x on the regolith beside the surveyor; no faces, one porthole on hull a; ink and palette measured). Export rows ready (544cbeab, `replaces_v2` on the six v2 models). Export after U-118's code, with B-142.

### B-145 · BLENDER · Done · C2
Goal: C2 Mercury design prep (Bible §12 C2 order 3; §7.3 "the twilight run"): a Mercury palette proposal with the Mars checks (contrast under the ink, muted, distinct, the plants readable on the ground and sky), five faceless Mercury plants as (d, M, pose) drawing functions (heat-side and shadow-side forms), the Mercury creature re-ink list (sizes, clips, order; faces kept, no teeth), the day / twilight / night backdrop study notes, the station and warden props that differ; `coordination/reports/blender/c2_mercury_designs.md`.
Accept: one review per group at 1x on a Mercury stand-in beside the surveyor; the ten boxes self-checked; nothing exported.
Files: blender/scripts/build_c2_mercury_*.py, coordination/reports/blender/c2_mercury_designs.md
Depends: B-139
Lead notes: Cycle 258. The same shape as B-139; LEAD accepts the designs before any Mercury card is written. Previews only when free RAM allows. Cycle 259: PALETTE ACCEPTED (37ed2ab, c2_mercury_designs.md §1: blinding regolith, ember, sun gold, cold steel teal, dusty sage, violet twilight, night slate; every check passing incl. the violet terminator hue and the near-neutral regolith) → D-130: into `meridian.v3.PALETTES["mercury"]`; the `ui/palettes/mercury/strip` export rides B-145's first export slot. Part 2 (the five plants) is previewed when RAM allows; reviewed on hand-off. Cycle 260: PLANTS ACCEPTED (18e602bd; review_b145_mercury_plants_preview.png: Sunfan, Embercap with its spore puff, Glassreed recoloured to cold teal so it reads on the violet twilight, Shadebloom, Coilwort; faceless; palette 100 %) and the FLAREWING ACCEPTED (4adf12ed; 124×124, idle 10 / fly 12 at index 1 / react 8 / bump 10 / flare_dance 12; a violet moth-bat with an ember belly and gold vanes, one eye, closed mouth). Next: the Shadewyrm + den, the Glassback, the Cinderling; the backdrop studies in a slot. Cycle 261: SHADEWYRM + ICE BURROW ACCEPTED (164f6f8d, 2b753f53; review_b145_mercury_shadewyrm_preview.png 05:58 and review_b145_ice_burrow_preview.png 06:00: a frost-capped teal wyrm with a round head, two eyes and a closed mouth, idle peek / walk hump / react duck / bump / `idle_open`; the 112×40 burrow drawn in front on the shared pivot; the 05:58 review listed six frames below the ground line and an invalid json, fixed per BLENDER's status by 06:22: the re-check line must say json valid). Glassback (e1865227) and Cinderling (9037f9b3) are reviewed when their full reviews render (the `review_glassback.png` / `review_cinderling.png` files are 10-31 model renders). Rig-set sources (c16565c5, bones 2 / 2 / 6 / 2 / 2) and backdrop sources (7c5cd276) noted; the report is at the accepted state (b25eedc7). Cycle 263: CINDERLING ACCEPTED (9037f9b3; review_b145_mercury_cinderling_preview.png 07:12: an 80×64 ember beetle with gold-glowing cracks and big eyes, idle 8 / walk 12 / react 8 hop with a spark puff / bump 10 / flee 12; json valid, ink and palette measured); the SHADEWYRM's re-check reads json valid (07:14; the earlier below-ground frames fixed). The Mercury rig-set dry run ACCEPTED (c16565c5; review_b145_mercury_rigset_dryrun.png: 26 parts on 500×168, bones 2 / 2 / 6 / 2 / 2, the idles with Unity's maths and the reacts, biomes per plant). The Glassback's review timed out at 150 s and re-runs. The backdrop stub smoke test ran (217 MB); the studies render in BLENDER's slot. Done when the Glassback is accepted and the studies are in; the exports go under the Mercury cards. Cycle 264: GLASSBACK ACCEPTED (e1865227; review_b145_mercury_glassback_preview.png 07:35: a pale grazer with cold-teal crystal shards that ring up on react, 176×112, idle 10 / walk 12 / react 8 / bump 10 / flee 12; ink and palette measured, json valid). DAY + TWILIGHT STUDIES ACCEPTED (07:49–07:53 slot; review_b145_mercury_day_preview.png: an ink sky with sharp stars, the huge painted Sun with its corona low on the left, blinding regolith with crater rims and hard slate shadows; _twilight_: the violet band under the ink, the Sun half-set at the terminator, Glassreed tufts near; the 2× strips seam-free; the Earth stone strip stands in under the surveyor until the Mercury strip exports). The night study renders in the 07:55 slot. B-145 is Done when the night study is accepted; the exports are B-148 / B-149 / B-150 (Backlog, promoted after U-118). Cycle 264 (08:1x): DONE. The night study ACCEPTED (07:55–07:57 slot; review_b145_mercury_night_preview.png: an ink sky dense with stars, slate crater rims with crisp shadows, teal ice glints; seams 0.68 / 0.66 / 0.63; layers 1.1 / 0.5 / 0.35 MB). Every part of the Mercury design prep is accepted: the palette (D-130), five plants, the rig-set dry run, four creatures + the ice-burrow den, three backdrop studies, the report. The exports are B-148 / B-149 / B-150 after U-118.

### B-146 · BLENDER · Done · C3
Goal: C3 UI art designs (Bible §12 C3; contract §11.6): paper panels as 9-slice sheets with `slice` in the json (the pause menu, the settings panel for U-102, the inventory, a hand-painted sign, a scroll), the planet title cards `ui/titlecards/<planet>` for Earth, Mars and Mercury (≤ 1920×540, the name lettered in Limelight as drawn ink, one painted vignette each, intertitle style), and the Film-effects toggle's switch; the Earth palette for the paper, each planet's palette for its card; previews only.
Accept: the ten §9.7 boxes that apply on a stamped preview (each panel at 1x with Patrick Hand sample text, each card at 1x); the 9-slice margins named in the json; nothing exported until a C3 export card.
Files: blender/scripts/build_ui_v3.py, blender/sources/ui/panels_v3.blend, titlecards_v3.blend
Depends: B-121
Lead notes: Cycle 261. Sideways work while UNITY wires C2 Earth: the menus and title cards are the owner's next visible layer after the planets. LEAD accepts the designs before the export card. Cycle 262: source in (a09e660d: a TrueType reader for Limelight + Patrick Hand so the lettering is drawn ink; five 9-slice panels and the Film switch checked at 48 MB, b1626503); the title cards and the full preview wait for a lock-free window; reviewed on hand-off. Cycle 264: the Mars title card checked at ss 2 (07:4x); the Earth and Mercury cards and the full UI preview next; reviewed on hand-off. Cycle 265: DONE as designs (3715aa62; review_b146_ui_preview.png 08:08: five 9-slice paper panels (pause, settings with a teal header band, inventory, a plank sign, a scroll) at 1x and stretched with Patrick Hand sample text, corners kept and edges clean; the Film switch off / on; the Earth, Mars and Mercury title cards 1600×450 with the name lettered in Limelight as drawn ink over an aged-paper card with a round painted vignette each; no faces). The export is B-151 (Backlog) when C3's UNITY card U-124 opens.

### B-147 · BLENDER · Done · C2
Goal: C2 Venus design prep (Bible §12 C2 order 4; §7.4 the dive world): the Venus palette proposal with the Mars checks, the cloud-layer backdrop study notes (the aerostat deck strip, the sulphur haze bands, the surface glow below), five faceless plants (deck and surface forms), the creature re-ink list (sizes, clips, order; faces kept, no teeth), the station and aerostat props that differ; `coordination/reports/blender/c2_venus_designs.md`.
Accept: one review per group at 1x on a Venus stand-in beside the surveyor; the ten boxes self-checked; nothing exported.
Files: blender/scripts/build_c2_venus_*.py, coordination/reports/blender/c2_venus_designs.md
Depends: B-145
Lead notes: Cycle 261. After B-146; previews only when free RAM allows. Cycle 262: PALETTE ACCEPTED (25afcafd, c2_venus_designs.md §1: cream haze, vent orange, sulphur yellow, sea-glass teal, dusty olive, apricot haze, glassy basalt; every check passing) → D-134: into `meridian.v3.PALETTES["venus"]`; the strip exports with B-147's first export slot. Next: the five plants (deck and surface forms), reviewed on hand-off. Cycle 263: the five plants' source (fcec304a) and the first creature, the Sulfur drifter (c123f584), are drawn; their previews wait for RAM and are reviewed on hand-off. Cycle 264: four creature sources are in (the Sulfur drifter c123f584 with drift at index 1, the Acidmoth 83195e4d with fly at index 1 and no eyespots, the Pressure crab whose claws wave and never pinch, the Vent eel 2d9484aa idling behind `props/venus/vent_mouth` per D-126); the plants' and creatures' previews are reviewed on hand-off. Cycle 265: DONE as designs. PLANTS ACCEPTED (ddbdcb32; review_b147_venus_plants_preview.png: Puffsail, Sulphurbell, Hazefern on the deck planks, Glasscoral and Ventcap with its steam puff on the surface; faceless; Venus palette 100 %). CREATURES ACCEPTED (6d5f7337; one measured run each): the Sulfur drifter (a sulphur-yellow gasbag with a cream frill and tendrils, drift at index 1), the Acidmoth (a sea-glass moth, fly at index 1, no eyespots), the Pressure crab (a basalt shell with vent-orange claws that wave and never pinch, ducks into its shell), the Vent eel (a dark basalt eel with a vent-glow belly peeking from `props/venus/vent_mouth`, D-126, with `idle_open`); ink 2.0–3.0 / 1.0–1.5 px, palette 100 %, json valid. The palette is D-134; the backdrop studies (deck + surface) run in a slot and are accepted under B-152. The exports are B-152 / B-153 / B-154 (Backlog) after U-123.

### B-148 · BLENDER · Backlog · C2
Goal: C2 Mercury flora and ground export (the accepted B-145 sources): `flora/mercury/rigset` (the five Mercury plants as one §11.3 rig set, 26 parts, bones ≤ 6, swaps, `biomes` per plant) and the Mercury ground strips in the B-130 contract (regolith white, and the slate shadow-side kind) plus `ui/palettes/mercury/strip` (D-130).
Accept: log OK; rigset.json valid with `biomes`; the strips' joins ≤ 1/255 and the silhouette ink identical on all edges; the ten boxes per plant on the stamped assembled review at 1x beside the surveyor; sheets ≤ 512² (rig set) and 540×152 (strips).
Files: blender/scripts/build_c2_mercury_rigs.py, build_c2_mercury_ground.py, Assets/_Game/Art/flora/mercury/, Assets/_Game/Art/terrain/mercury/, Assets/_Game/Art/ui/palettes/mercury/
Depends: B-145
Lead notes: Cycle 264. New keys; one slot ≤ 10 min when promoted (after U-118 Mars is in, per the Bible's C2 order).

### B-149 · BLENDER · Backlog · C2
Goal: Mercury backdrops from the accepted studies: `backgrounds/mercury/day`, `backgrounds/mercury/twilight` and `backgrounds/mercury/night` layer sets (three layers each, 2048 × ≤ 1024 tiling in x; the huge Sun on the far layer of day and half-set at twilight, the lit station on the night side), scene jsons in the SceneLayout schema.
Accept: the 2× seam check with no seam; ≤ 4 MB per PNG; a 1080p composite per set at 1x with the surveyor on the Mercury strips; UNITY's ParallaxLayers loads them by key.
Files: blender/scripts/build_backdrop_v3.py, Assets/_Game/Art/backgrounds/mercury/
Depends: B-145
Lead notes: Cycle 264. One export batch when promoted with B-148.

### B-150 · BLENDER · Backlog · C2
Goal: Mercury creatures re-inked from the accepted B-145 designs: the Flarewing (fly at index 1), the Shadewyrm with its den `props/mercury/ice_burrow` (D-126; `idle_open` away from the den), the Glassback, the Cinderling; faces kept (pie eyes, no teeth); one sheet ≤ 2048² each; `replaces_v2` on any Mercury model under the same key.
Accept: the ten boxes per creature on a stamped review (1x on the Mercury strips beside the surveyor); json valid; clip indices 0–3 in Gus's order, the rest by name; the Shadewyrm draws behind its burrow at the den in UNITY's capture.
Files: blender/scripts/build_creatures_mercury_v3.py, build_props_mercury_v3.py, Assets/_Game/Art/creatures/mercury/, Assets/_Game/Art/props/mercury/
Depends: B-145, U-123
Lead notes: Cycle 264. The export waits for U-123's code where it replaces Mercury models under live keys (D-119's order).

### B-151 · BLENDER · Backlog · C3
Goal: C3 UI export from the accepted B-146 designs: `ui/panels/{pause,settings,inventory,sign,scroll}` as 9-slice sheets with `slice` in the json (contract §11.6), `ui/titlecards/{earth,mars,mercury}` ≤ 1920×540, `ui/hud/film_switch` (two frames); the Venus and later cards follow their planets.
Accept: log OK; the slice margins in each json; UNITY's panels stretch with clean edges (U-124's capture); the cards at 1x in the intertitle slide.
Files: blender/scripts/build_ui_v3.py, Assets/_Game/Art/ui/
Depends: B-146, U-124
Lead notes: Cycle 265. One slot when U-124 opens (after U-118).

### B-152 · BLENDER · Backlog · C2
Goal: Venus backdrops: the cloud-deck set (`backgrounds/venus/deck`: the apricot haze, far cloud towers, the aerostat deck strip near) and the surface set (`backgrounds/venus/surface`: glassy basalt, vent glow, the sulphur crust), three layers each, 2048 × ≤ 1024 tiling in x, scene jsons; the studies first (one ≤ 5 min slot), LEAD accepts, then the export.
Accept: the 2× seam check with no seam; ≤ 4 MB per PNG; a 1080p composite per set at 1x with the surveyor; UNITY's ParallaxLayers loads them by key.
Files: blender/scripts/build_backdrop_v3.py, Assets/_Game/Art/backgrounds/venus/
Depends: B-147
Lead notes: Cycle 265. The studies may run now in a free slot; the export after U-123. Cycle 266: SURFACE STUDY ACCEPTED (the 08:28 slot; review_b147_venus_surface_preview.png: a banded apricot haze ceiling with acid-rain streaks that stop mid-air, terraced black tesserae ridges lit from below by vent glows, glassy glints; seams 0.89 / 0.56 / 0.56; layers ≤ 2.2 MB). The deck study's first pass had the towers as stacked lumps and the station hidden behind the near clouds; both fixed in code (88ccee89: cumulus towers with a following lining, the station as an airship above the cloud tops); its ~80 s re-run goes in the gap after UNITY's lock and is accepted on sight. Export after U-123.

### B-153 · BLENDER · Backlog · C2
Goal: Venus flora + ground export: `flora/venus/rigset` (the five accepted plants, deck and surface forms, ≤ 6 bones, swaps, `biomes`), the Venus ground strips (the deck planks, the basalt crust) in the B-130 contract, `ui/palettes/venus/strip` (D-134).
Accept: log OK; rigset.json valid with `biomes`; the strips' joins ≤ 1/255; the ten boxes per plant on the stamped assembled review at 1x beside the surveyor.
Files: blender/scripts/build_c2_venus_rigs.py, build_c2_venus_ground.py, Assets/_Game/Art/flora/venus/, terrain/venus/, ui/palettes/venus/
Depends: B-147
Lead notes: Cycle 265. One slot when promoted (after U-123).

### B-154 · BLENDER · Backlog · C2
Goal: Venus creatures re-inked from the accepted B-147 designs: the Sulfur drifter (drift at index 1), the Acidmoth (fly at index 1), the Pressure crab, the Vent eel with its den `props/venus/vent_mouth` (D-126; `idle_open`); faces kept (no teeth); one sheet ≤ 2048² each; `replaces_v2` on any Venus model under the same key.
Accept: the ten boxes per creature on a stamped review (1x on the Venus strips beside the surveyor); json valid; clip indices 0–3 in Gus's order, the rest by name; the eel draws behind its vent at the den in UNITY's capture.
Files: blender/scripts/build_creatures_venus_v3.py, build_props_venus_v3.py, Assets/_Game/Art/creatures/venus/, props/venus/
Depends: B-147, U-125
Lead notes: Cycle 265. The export waits for U-125's code where it replaces Venus models under live keys (D-119's order).

### B-155 · BLENDER · Ready · C2
Goal: C2 Jupiter design prep (Bible §12 C2 order 5; §7.5–7.6 the cloud-column world): the Jupiter palette proposal with the Mars checks, the cloud-deck layer study notes (decks, wisps, the storm and the Crush band on the near layer per the backdrop near-layer rule), floe and float-cell forms as faceless flora / props, the creature re-ink list (faces kept, no teeth), the aerostat and derelict props that differ; `coordination/reports/blender/c2_jupiter_designs.md`.
Accept: one review per group at 1x on a Jupiter stand-in beside the surveyor; the ten boxes self-checked; nothing exported.
Files: blender/scripts/build_c2_jupiter_*.py, coordination/reports/blender/c2_jupiter_designs.md
Depends: B-147
Lead notes: Cycle 265. The same shape as B-139 / B-145 / B-147; previews only when RAM allows. The first giant sets the cloud-column pattern for Saturn, Uranus and Neptune. Cycle 265 (08:5x, D-137): PALETTE ACCEPTED (67816d87; cream / brick / rust / festoon blue-grey / sage / tan / umber, every check passing) → PALETTES["jupiter"]; the report (five faceless flora, four floe strips, four deck backdrops + a Red Spot overlay with lightning and the CRUSH band on layer2, the creature list with the stingless Belt wasp and the Vortex Whale as a rig set, the props) noted. Rulings: floe strips export with cap_left + cap_right after the 8 tiles (U-126 places them); the aerostat kit (aerostat deck / strut / cell, float cell packs, grapple hook) is re-inked once in the Earth palette for all four giants (B-156, with the Jupiter cards). Previews of the flora, floes and the first deck study are reviewed on hand-off. Cycle 266: the flora drawing functions (f9205793) and the floe strips with cap_left + cap_right per D-137 (a7c4c38a) are in as source; their previews run in the gap after UNITY's lock.

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

### B-083 · BLENDER · Done · R1
Goal: Earth depth bands (contract §9 depth-bands row): per Earth region (forest, plains, desert, ocean/coast, taiga, tundra) a `backgrounds/earth_<region>/ridge_mid.glb` (z 20–60 m strip, tileable every 256 m, ≤ 8 k tris, baked PBR from the v1 ridge recipes), a shared `skyline_far.glb` (≤ 4 k tris) and a `skydome` 2048×1024 equirect `color` per region derived from the v1 layer0 skies.
Accept: tiles seamlessly in x; reads as the v1 parallax from the side rail in UNITY's preview; stamped turntables; D-045/D-066 peaks measured.
Files: blender/scripts/gen_backdrop3d.py, Assets/_Game/Art/backgrounds/earth_*/
Depends: B-077
Lead notes: Cycle 186: art accepted in full. skyline_far v3 (11 seeded depth rows, broad massif, capped slopes, snow band; 2,560 tris; turntable stamped 02:22) reads as a snow-capped range; ridge_mid ×6 and skydomes ×6 accepted in cycle 183. Done on U-076's first capture with the depth bands in the scene. Done (cycle 202): depth bands in the scene per u076 earth_camp_day.png (forest ridge + snow skyline) and mars_shelter_night.png (mars_plains ridge). Cycle 209: reopened for one failing check (works in the game, Bible section 9 v2 'no low-poly look'): the forest/taiga ridge trees are flat-shaded, vertex-colour-only, 14-24 m tall and start at z 17, so they fill the Earth frame as faceted blobs. Fix as B-102 (D-074); the desert/tundra/ocean bands and skyline_far stay accepted.

### B-084 · BLENDER · Done · R1
Goal: Earth POI props as models: the Survey Archive, Launch Complex pieces, crashed Halcyon hauler, Warden outpost obelisk and the B-020/B-021 prop sets, each ≤ 6 k tris (hauler ≤ 15 k with LOD1), standable tops flat, emissive where lit.
Accept: contract §9; stamped turntables; UNITY lit preview for Done.
Files: blender/sources/props/earth/, build_props_earth.py, Assets/_Game/Art/props/earth/
Depends: B-077
Lead notes: Cycle 187 (b31f865): art accepted on the turntables (archive door + terminal, launch gantry + tower ruin, Earth beacon, hauler hull_a/hull_b/cargo with LOD1, Warden pylon, Meridian beacon; 188–1,404 tris). Rulings: the hauler stays as the three v1 pieces UNITY already places (no hero wreck now); the pylon stays the v1 obelisk. Done on UNITY's lit preview (fold into U-076's run). Done (cycle 202): POI props in the scene per the u076 captures and UNITY's U-076 swaps (12 swaps, lit preview run r1_models).

### B-085 · BLENDER · Done · R1
Goal: Earth scenery for the near band and the play plane: 3 tree species (forest/taiga variants), 2 bushes, 3 rocks, grass tufts, a cactus and a dead tree, each ≤ 2 k tris with LOD1 at ≤ 800, sharing one 2048 atlas material; wind-sway via a vertex-colour mask (R = sway weight).
Accept: contract §9; a stamped grove preview (20 instances) reads under the Earth Sun; UNITY lit preview for Done.
Files: blender/sources/props/earth_flora/, build_props_earth.py, Assets/_Game/Art/props/earth_flora/
Depends: B-077
Lead notes: Cycle 188 (3a1ff4f): art accepted on review_b085_grove.png (11 models, shared 2048² atlas, sway in COLOR_0.r, LOD1 ≤ 800). Canopies are simple (blob oak, cone spruce); acceptable for R1, and a foliage-card pass is an M6 polish item, not now. Done on UNITY's lit preview; the shared atlas material is a one-off in ArtImporter (atlas_* maps, no per-model maps). Cycle 209: Done on u076_2026-11-05/earth_camp_day.png (UNITY's 4x crop: bush smooth, atlas-textured; tree_oak.glb smooth normals, atlas UVs, mask R0/G244/B0/A0.35, the generated URP/Lit material binds the atlas maps).

### B-086 · BLENDER · Superseded (D-086) · R2
Goal: Mars terrain block materials (contract §9 terrain row), the R2 counterpart of B-080: every Mars tile material in `MarsTileSet` (regolith, basalt, hematite, clay, perchlorate, polar ice, CO₂ frost/snow, lava-tube rock…: list them from the tile set and log the list), top/side PBR sets at 512², 2 m per repeat, plus `terrain/mars/backwall`; from the v1 recipes, rust/salmon palette (§9).
Accept: tiles seamlessly; reads as the v1 Mars under the Mars Sun (0.75) in UNITY's lit preview; stamped contact sheet; peaks measured (D-045/D-066).
Files: blender/scripts/gen_terrain.py, Assets/_Game/Art/terrain/mars/
Depends: B-077
Lead notes: Cycle 189 (dc2b3c0): art accepted (regolith, basalt, hematite, ice, snow + basalt backwall; the board's clay/perchlorate/lava-tube examples are items or generator features, not tile materials, so none were due). Done on UNITY's first lit Mars block capture in R2.

### B-087 · BLENDER · Superseded (D-086) · R2
Goal: Mars creatures as models: `creatures/mars/dustskater` (small class, ≤ 3 k tris) and `creatures/mars/scree_stalker` (medium, ≤ 8 k), full walker clip sets from the v1 rigs, materials matching Mars (silicate, dust).
Accept: contract §9; stamped turntables; UNITY lit preview at 60 px/m reads as the v1 silhouettes.
Files: blender/sources/creatures/mars/, build_creatures_mars.py, Assets/_Game/Art/creatures/mars/
Depends: B-077
Lead notes: Cycle 190: art accepted on the turntables (dustskater 2,850 tris on skate pads; scree_stalker 7,598 tris with back plates; 16-joint skins, 5 clips). Done on UNITY's lit preview in R2.

### B-088 · BLENDER · Superseded (D-086) · R2
Goal: Mars depth bands (contract §9 depth-bands row), the R2 counterpart of B-083: `backgrounds/mars_<region>/ridge_mid.glb` for canyon, plains, polar and tharsis (Olympus Mons as the far hero), a shared `skyline_far.glb`, and skydomes per region (rust/salmon skies, the v1 dust haze; a `storm` skydome variant for the dust storm).
Accept: tiles seamlessly in x; reads as the v1 Mars parallax from the side rail; stamped turntables; peaks measured.
Files: blender/scripts/gen_backdrop3d.py, Assets/_Game/Art/backgrounds/mars_*/
Depends: B-077
Lead notes: Cycle 191 (00f0a65): art accepted on the turntables (canyon terraces with strata and boulders; Olympus Mons as a broad shield on a 1024 m period; storm skydome). Done on R2's first Mars capture with the bands in the scene.

### B-089 · BLENDER · Superseded (D-086) · R2
Goal: Mars scenery and POI props as models: boulders ×3, regolith rocks ×2, ice chunks ×2, a dead shrub-like "dust bush", lava-tube stalactite/stalagmite pair (each ≤ 1.5 k tris, LOD1, one shared atlas); the Mars POI props from the v1 sources not already covered by B-084 (crash-site debris, the Mars Waystation surface beacon, ice-cap drill rig), ≤ 6 k tris each.
Accept: contract §9; a stamped field preview (20 instances) under the Mars Sun (0.75); UNITY lit preview for Done.
Files: blender/sources/props/mars/, build_props_mars.py, Assets/_Game/Art/props/mars_flora/, props/mars/
Depends: B-077
Lead notes: Cycle 194 (2eed996): art accepted on review_b089_field.png (boulders, rocks, ice chunks, dust bush, stalactite/stalagmite on one Mars atlas with LOD1; new POI prop ice_drill_rig; the other Mars POIs were already made in B-084). Done on R2's lit preview.

### B-090 · BLENDER · Done · R2
Goal: Space objects as models for U-078's lit top-down scene: `props/space/waystation` (the Earth/Mars Waystation as one model with a lit docking bay and running lights, LOD1), `props/space/asteroid_01..06` as low-poly rocks (≤ 600 tris each) from the v1 silhouettes, `planets/<name>/rings` for Saturn as a flat ring mesh with an alpha texture.
Accept: contract §9; top-down turntables at the Space camera scale; UNITY lit preview for Done.
Files: blender/scripts/build_waystation.py, build_asteroids.py, gen_planet.py, Assets/_Game/Art/props/space/, planets/saturn/
Depends: B-077
Lead notes: Cycle 192 (3e7fbc6): art accepted on the top-down turntables (ring station with solar panels, docking arms and guide lights, 14,250 tris + LOD1; waystation_mars; six asteroids 80–570 tris; planets/saturn/ring_mesh annulus at R = 96 m using rings_color.png alpha). Done on U-078's lit Space capture. Cycle 227: Done (3e7fbc6 art; U-078 capture 123aa95: station, ring mesh and belt rocks lit in the game).

### B-091 · BLENDER · Superseded (D-086) · R3
Goal: Mercury and Venus terrain block materials (R3 prep, as B-080/B-086): every tile material in `MercuryTileSet` (regolith, basalt, solarite crust, shadow ice, impact glass…) and `VenusTileSet` (basalt, sulfur crust, vent glass, station deck plates…), top/side PBR sets at 512², 2 m repeat, plus backwalls; palettes per §9.
Accept: tiles seamlessly; reads as the v1 materials under each planet's Sun in UNITY's lit preview; stamped contact sheets.
Files: blender/scripts/gen_terrain.py, Assets/_Game/Art/terrain/{mercury,venus}/
Depends: B-077
Lead notes: Cycle 196 (7c77065): art accepted (Mercury regolith/basalt/sulfide/ice; Venus basalt/tessera/vent glass/sulfur; basalt backwalls; the board's solarite crust, impact glass and deck plates are items/props, not tile materials, so none were due). Done on R3's first lit block captures.

### B-092 · BLENDER · Superseded (D-086) · R3
Goal: Mercury and Venus depth bands (as B-083/B-088): Mercury `ridge_mid` for day side, twilight band and night side (grey regolith crater rims, a violet-black sky skydome with the huge Sun on the day side; a night skydome with stars), Venus `ridge_mid` for the cloud deck (cloud-top masses as translucent planes, no ground) and the surface (black basalt plains with vent glows), skydomes orange-cream (deck) and dark orange (surface); shared `skyline_far` per planet.
Accept: tiles seamlessly; reads as the v1 parallax from the side rail; stamped turntables; peaks measured.
Files: blender/scripts/gen_backdrop3d.py, Assets/_Game/Art/backgrounds/{mercury,venus}_*/
Depends: B-077
Lead notes: Cycle 193. R3. Cycle 207 (2026-11-05): art accepted on the stamped turntables review_backgrounds_{mercury_day,mercury_twilight,mercury_night,venus_deck,venus_surface}_ridge_mid.png and the two skyline_far panels (12:28–12:30; log OK ×12, peak 1534 MB): grey cratered regolith strips with boulders, Venus deck cloud heaps, basalt plains with lava vents. The exports are NOT committed: Assets/_Game/Art/backgrounds/mercury*/, venus*/, sources/backgrounds/{mercury,venus}_bands.blend and the manifest sit untracked/modified in the tree since the 12:30 restart. First thing: commit them (`[blender] B-092 exports`), then this is Done on UNITY's R3 lit preview.

### B-093 · BLENDER · Superseded (D-086) · R3
Goal: Mercury and Venus creatures as models from the v1 sources (B-04x): every non-apex creature of `creatures/mercury/*` and `creatures/venus/*` (list them from the v1 manifest and log the list), size class per contract §9, full clip sets from the v1 rigs, emission where they glow.
Accept: contract §9; stamped turntables; UNITY lit preview for Done.
Files: blender/sources/creatures/{mercury,venus}/, build_creatures_mercury.py, build_creatures_venus.py, Assets/_Game/Art/creatures/{mercury,venus}/
Depends: B-077
Lead notes: Cycle 200: art accepted on the turntables (flarewing, acidmoth checked; 8 species: Mercury glassback/cinderling/flarewing/shadewyrm, Venus sulfur_drifter/acidmoth/pressure_crab/vent_eel). Pipeline fixes: object animation baked to bones; merge keeps original coordinates. Done on R3's lit preview.

### B-102 · BLENDER · Done · R1
Goal: Fix the Earth ridge bands (reopen of B-083, D-074): re-export `backgrounds/earth_{forest,taiga,coast,plains}/ridge_mid` from build_depthbands.py so the band reads as a distant tree line, not low-poly blobs: (1) tree crowns and trunks smooth-shaded (`use_smooth=True` on the tree meshes, auto-smooth about 60 deg; the ground/hill strip may stay faceted under its colours), (2) tree heights forest (6, 12), taiga (7, 14), coast (5, 9), plains (5, 9), (3) no trees in the two nearest rows (z 20 and 25 m); the tree line starts at z >= 30 m, (4) atmospheric tint: blend every vertex colour toward the region's sky haze colour by 20 % at z 20 -> 45 % at z 60 so the band sits behind the near flora, (5) tri and vertex counts <= B-083's. Desert, tundra, ocean and skyline_far are untouched.
Accept: stamped turntables; UNITY's next Earth day capture (U-077 smoke) shows the ridge tree line topping out below 45 % of frame height with no visible facet at 1080p and the B-085 flora reading in front of it; peaks measured; 4 assets in one wrapper call.
Files: blender/scripts/build_depthbands.py, Assets/_Game/Art/backgrounds/earth_{forest,taiga,coast,plains}/
Depends: B-083
Lead notes: Cycle 209. R1 blocker: do it before the B-094 export (same lock, one call if the wrapper allows); the 0.4.0 build waits up to 60 min for it. The flora (B-085) is fine; only the band changes. Cycle 212 (00:3x): art accepted on review_backgrounds_earth_forest_ridge_mid.png (stamped 00:24; log OK x4, peak 1746 MB, 5ecfb99): short hazed tree line behind a bare front strip, no facets at turntable size. Done on the U-077 Earth day smoke shot (the frame-height check is the real test). Cycle 217 (01:0x): FAILS that check in smoke_2026-11-06/smoke_2_earth_day.png: crowns still faceted (the 60-degree sharp-edge split kept every crown edge sharp: forest ridge_mid.glb 12,066 verts for 6,044 tris) and the tree line tops out at about 15 % from the top of the frame because the forest ground rises 26 m. Round 2, your very next call (4 assets, ~2 min): (a) tree crowns and trunks smooth with NO sharp-edge split (auto-smooth off or angle 180 deg; target verts <= 0.6 x tris + 50 per band), (b) rise forest 26 -> 12, taiga 30 -> 14, coast 6 -> 4, plains unchanged, (c) keep the cycle-209 heights, haze and z >= 30 tree line. Accept unchanged: in UNITY's next smoke_2_earth_day the highest crown sits below 45 % of frame height from the top and no facet is visible at 1080p. Cycle 218 (01:0x): round 2 exported 01:02-01:04 (d2020d6; log OK x4, peak 1709 MB): no sharp split, authored UVs (the split came mostly from the smart-UV islands; model.py keep_uv), rises forest 12 / taiga 14 / coast 4; glb verts = unique verts (forest 4757 / 6044 tris, taiga 5047 / 5496, coast 1395 / 2272, plains 1574 / 2648). The 0.6 x tris target was wrong for cone trees (7 verts per 6 tris); the criterion is 'no split vertices', met. Export accepted; Done on UNITY's next smoke_2_earth_day.

### B-094 · BLENDER · Superseded (D-086) · R3
Goal: Mercury and Venus apexes as models: `creatures/mercury/cinderhulk` (large class, lava-cracked back with emission that dims on the night side via a material float) and `creatures/venus/veil_serpent` (segmented ribbon: head, repeatable body, tail; translucent fins; a "chilled" white-flash state), LOD1 for both.
Accept: contract §9; chained preview for the serpent; stamped turntables; UNITY lit preview for Done.
Files: build_creatures_mercury.py, build_creatures_venus.py, Assets/_Game/Art/creatures/{mercury,venus}/
Depends: B-093
Lead notes: Cycle 193. R3. Cycle 212: cinderhulk exported (00:28, 19,000 tris, 2048^2, LOD1, 5 clips, peak 1952 MB); the serpent head/body export FAILED 00:29 with UnicodeDecodeError (byte 0xa7 at offset 46362 of a file read as UTF-8: a cp1252 section sign or degree sign in a script/note; open that file with the right encoding or replace the character). Fix is light work; export the three modules after UNITY's U-077 job 1. Cycle 213 (00:4x): encoding fixed; head (19,000 + LOD1) and body (11,400 + LOD1 5,472) exported 00:32-00:34 at 2048^2 (ea191ea head + cinderhulk). Art accepted on review_creatures_mercury_cinderhulk.png (00:28: cracked-plate carapace, dark body, claws) and review_b094_serpent_chain.png (continuous banded ribbon, veined translucent sail, no notch at the joins). Left: the tail export and a body re-export with the socket named socket_next (the glb carries socket_root.001), both on BLENDER's next turn; then Done on UNITY's R3 lit preview (U-085). Cycle 216 (00:5x): tail (15,200 + LOD1 7,296) and body re-export in one call 00:43-00:45 (5aa4b57; sockets root/next bare; chain tail + 2 bodies + head = 57,000 tris < 60 k); review_creatures_venus_veil_serpent_tail.png (00:43) reads. All B-094 art accepted; Done on U-085's lit preview. BLENDER → B-101. Cycle 207: started before the restart and left uncommitted: build_creatures_venus.py `build_serpent_modules` (+188 lines), model.py changes, manifest entries creatures/mercury/cinderhulk (one model, night dims the emission at runtime) and creatures/venus/veil_serpent_{head,body,tail} (chained by UNITY; a module with J bones behind it plays its clip delayed by J×0.07 cycles). Commit those sources as they stand before any export (they are reviewable work; an uncommitted tree is not). The three-module serpent and the single cinderhulk are approved as the design; the chaining rule goes to UNITY's R3 task (U-085, Backlog). Export 2048² bakes need ≥ 2.0 GB free (D-066): if the gate stays shut, bake at 1024² for the turntables and note it.

### B-095 · BLENDER · Superseded (D-086) · R3
Goal: Mercury and Venus props and stations as models: flare shelter (dome + door clip), Mercury equipment locker, solarite crystal cluster (3 states: glowing, crusted, cut), the Venus station modules (deck module, hab, airlock arch, balloon cell, railing, vent harvester), aerostat pieces already covered by B-069 are re-made as models here too (aerostat_cell/deck/strut), the Mars/Earth Waystation surface pads if any.
Accept: contract §9 (ppu/LOD rules); station modules tile at their v1 pitches; stamped turntables; UNITY lit preview for Done.
Files: build_props_mercury.py, build_props_venus.py, build_props_common.py, Assets/_Game/Art/props/{mercury,venus,common}/
Depends: B-077
Lead notes: Cycle 203 (3a33ba1 + 7968f97): art accepted on the turntables (flare shelter, Venus station hull checked; 19 models incl. solarite in three states, Venus hab/deck/balloon/cell/arch/harvester/railing, aerostat cell/deck/strut at 2 m). No Waystation surface pads exist in any source (fine). Done on R3's lit preview.

### B-096 · BLENDER · Superseded (D-086) · R3
Goal: Wardens as models: `creatures/warden/sentinel` and `creatures/warden/hunter` (hovering drones, centred pivot, flier clip set, indigo running lights, a shield emitter), plus `fx/warden_bolt` as a billboard sheet is kept (2D fx stay 2D).
Accept: contract §9; stamped turntables; UNITY lit preview for Done.
Files: build_wardens.py, Assets/_Game/Art/creatures/warden/
Depends: B-077
Lead notes: Cycle 198: art accepted on the turntables (sentinel 7,600 tris; hunter 7,440 tris as a slimmer dart pod with strike prongs; centred pivots; idle/walk/fly/attack/hurt/death; iris, core and prongs on bones; indigo lights and shield ring). Pipeline fix: species-prefixed actions. Done on R3's lit preview.

### B-097 · BLENDER · Superseded (D-086) · R4
Goal: Jupiter column in 3D: floe block materials (`terrain/jupiter/floe_ice`, `floe_core`, `floe_derelict` as top/side PBR sets at 512², 2 m repeat, from the v1 recipes) and the cloud decks as depth-band assets: `backgrounds/jupiter_deck1..3/` and `jupiter_deep/` each as three translucent cloud-bank planes (`deck_far.glb`, `deck_mid.glb`, `deck_near.glb`: alpha-textured strips from the B-048/B-055 painted banks, tileable every 256 m) plus a skydome per deck; the Crush band on the near plane of `deep` (as learned in B-055).
Accept: contract §9; tiles seamlessly; stamped turntables composited as a stack; peaks measured.
Files: blender/scripts/gen_terrain.py, gen_backdrop3d.py, Assets/_Game/Art/terrain/jupiter/, backgrounds/jupiter_*/
Depends: B-077
Lead notes: Cycle 199. R4 (M4 in 3D) prep; reuses the superseded B-048/B-055 work. Cycle 220: after B-108; add a `stage.json` per deck and `props/jupiter_foreground/wisp_*` pieces (contract §10 giants row).

### B-098 · BLENDER · Superseded (D-086) · R4
Goal: Jupiter creatures as models from the B-056 sources: stormglider (flier), lightning_eel (segmented, emissive stripe), belt_wasp (small), ballast_tortoise (large; its death pose matches the husk) and the husk_tortoise prop; size classes per contract §9; LOD1 for the tortoise.
Accept: contract §9; stamped turntables; UNITY lit preview for Done.
Files: build_creatures_jupiter.py, build_props_jupiter.py, Assets/_Game/Art/creatures/jupiter/, props/jupiter/
Depends: B-077
Lead notes: Cycle 199. R4 prep.

### B-099 · BLENDER · Superseded (D-086) · R4
Goal: Jupiter and Neptune POI props as models from the B-055/B-068 sources: derelict_pod, beacon_vault, the Meridian wreck bow/mid/stern (standable tops), wind_anchor; plus the aerostat modules (cell, deck, strut) as models if not already made under B-095.
Accept: contract §9 (ppu/LOD rules); standable tops flat; stamped turntables; UNITY lit preview for Done.
Files: build_props_jupiter.py, build_props_neptune.py, build_props_common.py, Assets/_Game/Art/props/{jupiter,neptune,common}/
Depends: B-077
Lead notes: Cycle 199. R4 prep.

### B-101 · BLENDER · Superseded (D-086) · R3
Goal: Mercury and Venus scenery props as models (the R3 counterpart of B-089): Mercury near-band and play-plane scenery (regolith boulders ×3, impact-glass shards ×2, solarite outcrop, crater-rim rock, ice pocket for the polar/night side) and Venus surface scenery (basalt columns ×2, tessera slab, sulfur crust, vent chimney, cooled lava blister), each ≤ 2 k tris with LOD1 ≤ 800, one shared 2048² atlas per planet (gen_flora_atlas TILE_SETS), emission on the solarite and vent chimney; no flora (nothing grows); the Venus deck gets no scenery (no ground).
Accept: contract §9; a stamped field preview per planet (20 instances under that planet's Sun: Mercury 6.7, Venus 0.1 diffuse) reads at 60 px/m; UNITY lit preview for Done.
Files: blender/sources/props/{mercury,venus}_scenery/, build_props_mercury.py, build_props_venus.py, Assets/_Game/Art/props/{mercury_scenery,venus_scenery}/
Depends: B-077
Lead notes: Cycle 207. R3. After B-094; before the R4 tasks. Cycle 219 (01:1x): Mercury half ACCEPTED on review_b101_field_mercury.png (00:57; 2e7fe21): lumpy regolith boulders, pale shards, solarite spires read under the 6.7 Sun. Venus half FAILS Art matches (Bible section 9 v2 'no low-poly look') on review_b101_field_venus.png (01:09; 5109dfd): the basalt columns are stacked boxes, the sulfur crust and lava blister are flat discs, the vent chimney a plain cone with a dull mouth; the set reads as placeholder silhouettes at 80-440 tris. Round 2 for the 6 Venus models, budget up to 1.5 k tris each (LOD1 <= 800 stays): basalt columns as clusters of 5-9 hexagonal prisms with broken, stepped tops and tilted outliers; tessera slab with ridged, cracked top faces; sulfur crust as raised cracked plates (0.1-0.2 m relief) with brighter rims; vent chimney with an irregular built-up rim, a glowing mouth (atlas emission wired in the preview material) and a sag on one side; lava blister as a cracked dome with emissive seams. Re-render both field sheets with emission; Mercury needs no model change. Cycle 220 (01:3x): still your first job (the Venus round 2 sources 42f0e6a are in; export when the gate opens), then B-109 (near flora v2, the most visible Earth failure) → B-103 → B-104 → B-105 → B-106 → B-107 → B-108 → B-097. Also in your next commit: `git rm --cached` the four tracked `blender/scripts/meridian/__pycache__/*.pyc` (already gitignored). Cycle 223 (10:2x): Venus round 2 ACCEPTED (ecf5e08; log OK x7 10:16-10:17, peak 1586 MB; review_props_venus_scenery_{column_a,vent_chimney}.png and review_b101_field_venus.png stamped 10:17): hex colonnades with fallen segments, ridged tessera, raised plates, lumpy chimney, blister seams, all textured. One touch-up, bundled into your next export call (the B-109 Earth flora call, not a lock of its own): vent_mouth emission about 3x stronger and the chimney mouth wider and lower so the glow reads as a pool from the level camera; lava_blister seams the same. Done on UNITY's lit preview (U-085).

### B-109 · BLENDER · Superseded (D-086) · S1
Goal: Earth near flora round 2 (reopen of B-085 for one check, Bible §9 v2/v3 'no low-poly faceted look'): the trees that stand at z 2–12 in every Earth frame (`props/earth_flora/tree_oak`, `tree_birch`, `tree_spruce`, `dead_tree`, `bush_a`, `bush_b`; `grass` and the rocks are fine) currently read as flat-shaded polyhedra crowns and plain cones. Rebuild each crown as a real canopy: 40–120 overlapping leaf-cluster cards from the flora atlas (alpha-clipped, two-sided, with normals bent toward the crown centre so the lighting reads as one volume), a modelled trunk and three to five main branches with bark detail, conifers as 8–12 tiers of needle cards on a tapered trunk; silhouettes must read as oak, birch, spruce at 60 px/m; 1.5–3 k tris each, LOD1 ≤ 1.2 k (fewer cards), sway through COLOR_0 as before; bushes and grass the same way at ≤ 800 tris. Atlas: add leaf-cluster and needle tiles to the existing 2048² Earth flora atlas (keep the colour tiles the other models use in place).
Accept: contract §9; a stamped field preview (20 instances at the camp distance, Earth Sun) with no visible facet, no polyhedral crown and no plain cone at 60 px/m; triangle counts in the json; peaks ≤ 2.0 GB (the 2048² atlas); UNITY's next Earth smoke shot (U-086 or U-092) for Done.
Files: blender/scripts/build_flora.py, gen_flora_atlas.py, blender/sources/props/earth_flora.blend, Assets/_Game/Art/props/earth_flora/
Depends: B-085
Lead notes: Cycle 221 (10:2x). Evidence: smoke_3c_ship_airborne.png and smoke_2_earth_day.png (01:18): every crown in the near band is a faceted polyhedron, every conifer a smooth cone. This is the B-085 flora itself (the B-102 ridge is fixed). No code change on UNITY's side; the importer swaps the models in. Before B-103: this failure is in every Earth frame, the clips are not. Cycle 224 (10:4x): art ACCEPTED on review_b109_field_earth.png (stamped 10:39; log OK atlas 10:32 + 6 models 10:33-10:39, peaks ≤ 1.69 GB; 2e6a775): layered needle spruces, white birches with soft crowns, broad oaks on forked limbs, gnarled dead trees, full bushes; no facet, polyhedron or cone at 60 px/m. Counts: oak 1216 (LOD1 796), birch 784 (436), spruce 1616 (1244), bush_a 304 (144), bush_b 472 (312), dead_tree 872 (418); the 1.5 k lower bound is waived (the crowns read full; the look is the criterion). Owed: tree_spruce LOD1 ≤ 1.2 k re-export (fix in; want filed 10:41, after UNITY's job). Done on UNITY's next Earth smoke shot with the alpha-clip materials (U-086's capture if it includes Earth, else U-092).

### B-103 · BLENDER · Superseded (D-086) · S1
Goal: Surveyor clips v2 at 60 fps (contract §9 Rig row v2.5): re-export `characters/surveyor/base` with every existing clip resampled to 60 fps and given anticipation (2–4 frames) and follow-through (one overshoot key) where it acts (jump, land, dig, aim, hurt), plus the new clips `jump_anticipate` (8 f: crouch and arm swing), `land_hard` (20 f: deep knee bend, arms forward, recover), `dash` (12 f: 30° lean, trailing arm), `parry` (20 f: 4 wind-up, 4 strike with the Rig arm, 12 hold and recover), `parry_hit` (12 f: braced pose with a recoil), `hit_react` (16 f: torso snaps away, head follows a frame later). Mesh, maps (2048²), rig and triangles (≤ 12 k) unchanged; sidecar `fps: 60`.
Accept: `base.json` lists 16 clips at fps 60 with the frame counts above; the glb's triangle count unchanged; a stamped clip strip `blender/preview/review_characters_surveyor_clips.png` (6 frames each of jump_anticipate, land_hard, dash, parry, hit_react) plus the turntable; peak measured (no map re-bake: 1.5 GB gate). Done on UNITY's U-089 capture.
Files: the surveyor builder in blender/scripts/, blender/sources/characters/surveyor.blend, Assets/_Game/Art/characters/surveyor/base.glb, base.json
Depends: B-077
Lead notes: Cycle 220. Original poses; exaggerate timing, not anatomy (Bible §9 v3 Animation row). Export the glb + json only, file-only pathspecs, no .meta.

### B-104 · BLENDER · Superseded (D-086) · S1
Goal: Earth stage layer sets (contract §10) for forest, taiga, coast, plains, desert, tundra: per region `rocks_near.glb` (z 8–14, period 128 m, ≤ 6 k, on the planet-shared `backgrounds/earth/rocks_atlas_*` 2048²), `hills_far.glb` (z 80–140, period 512 m, ≤ 4 k, 1024²), `stage.json` (set-piece slots for B-105, foreground pieces, haze_rgb); per planet `backgrounds/earth/clouds_color.png` (2048 × 512 RGBA strip) and six foreground pieces `props/earth_foreground/{tuft,fern,boulder,log,branch,reeds}.glb` (≤ 2 k each, one 1024² atlas, origin base, two with translucent edges). Haze baked by depth as B-102. `build_depthbands.py` gains the two bands, `build_flora.py` the foreground set, `render.py` a stage-sheet mode (`--stage <planet>_<region>`: the whole stack from the rail camera at 60 px/m, 1920 × 1080, stamped).
Accept: contract §10 caps per file; the planet's layer-texture sum reported ≤ 700 MB stored; six stamped stage sheets `blender/preview/stage_earth_<region>.png` that read as composed sets with no facet or seam; log OK per asset; peaks ≤ 1.5 GB (1024²) and ≤ 2.0 GB (the 2048² atlas); UNITY's Earth depth capture (U-090) for Done.
Files: blender/scripts/build_depthbands.py, build_flora.py, gen_flora_atlas.py, render.py, blender/sources/backgrounds/earth_bands.blend, Assets/_Game/Art/backgrounds/earth_*/, backgrounds/earth/, props/earth_foreground/
Depends: B-102
Lead notes: Cycle 220. The stage-sheet renderer is part of this task and is reused by every planet. Foreground pieces are seen from 1.5 m: real leaf and bark detail, no cards.

### B-105 · BLENDER · Superseded (D-086) · S1
Goal: Earth set-pieces and composed skylines (Bible §9 v3 Stage composition): three landmarks per region (18). Forest: split granite tor, waterfall cliff, dead giant oak. Taiga: granite dome, burnt-stand ridge, frozen lake shelf. Coast: sea-stack pair, headland arch, dune-backed cliff. Plains: lone crowned hill, river bluff, standing-stone ring. Desert: twin mesas, rock-spine dune crest, salt-flat ridge. Tundra: glacier snout, frost-shattered peaks, erratic field. Each `setpiece_<a|b|c>.glb` ≤ 10 k tris (LOD1 ≤ 4 k), 2048² own maps, origin base, haze by depth; `backgrounds/earth/skyline_far.glb` rebuilt as three composed peak silhouettes (period 1024 m) replacing the noise ridge; every `stage.json` `setpieces` filled (2–4 per region with `at`, `z`, `scale`, `mirror`; no two within 120 m).
Accept: contract §10; every stage sheet shows one dominant and one secondary landmark with at least a third open sky; no facet at 60 px/m; original forms (no real-world or fictional landmark replicated); log OK ×19; peaks ≤ 2.0 GB; UNITY's depth capture for Done.
Files: blender/scripts/build_setpieces.py, build_depthbands.py, blender/sources/backgrounds/earth_setpieces.blend, Assets/_Game/Art/backgrounds/earth_*/setpiece_*.glb, backgrounds/earth/skyline_far.glb
Depends: B-104
Lead notes: Cycle 220. Compose first: block out all 18 at ~500 tris and send one stage sheet per region for an early check, then detail and bake.

### B-106 · BLENDER · Superseded (D-086) · S1
Goal: Creature reaction clips (contract §9 Rig row v2.5): `hit_react` (6 f: snap away from the hit, head lags a frame) and `stagger` (24 f: lose footing, recover) at 30 fps for every creature with an attack or bite: Earth wolf; Mars scree_stalker; Mercury glassback, shadewyrm, cinderhulk; Venus pressure_crab, vent_eel, veil_serpent (head module; the body follows by chaining); Wardens sentinel and hunter (a flinch and a lights-flicker stagger). glb + json re-export only; meshes, maps and other clips unchanged.
Accept: each json lists the two clips; triangle counts unchanged; a stamped strip per species `review_creatures_<planet>_<name>_react.png` (4 frames each); log OK per export; peaks ≤ 1.5 GB (no re-bake). UNITY's U-089 capture for Done.
Files: blender/scripts/build_creatures_*.py, build_wardens.py, Assets/_Game/Art/creatures/*/<name>.glb, <name>.json
Depends: B-103
Lead notes: Cycle 220. One wrapper call per planet; 2048² maps are not re-baked.

### B-107 · BLENDER · Superseded (D-086) · S1
Goal: Mars stage layer sets and set-pieces (as B-104 + B-105) for canyon, plains, polar, tharsis: `rocks_near`, `hills_far`, `stage.json`, `backgrounds/mars/clouds_color.png` (thin dust veils), six foreground pieces `props/mars_foreground/` (regolith rock, slab, dust bush, ice chunk, drift, cairn), 12 set-pieces (canyon: layered wall tower, collapsed arch, scree fan; plains: crater rim, dust-devil scar field, lone butte; polar: ice scarp, layered cap edge, frost field; tharsis: lava channel, shield flank, caldera lip; Olympus stays the far hero), `skyline_far` as composed peaks; the storm skydome kept.
Accept: as B-104/B-105 (caps, ≤ 700 MB per planet, four stage sheets, peaks); UNITY's Mars depth capture (U-081) for Done.
Files: build_depthbands.py, build_setpieces.py, build_flora.py, blender/sources/backgrounds/mars_*.blend, Assets/_Game/Art/backgrounds/mars_*/, backgrounds/mars/, props/mars_foreground/
Depends: B-105
Lead notes: Cycle 220. The R2 counterpart; U-081 consumes it.

### B-108 · BLENDER · Superseded (D-086) · S1
Goal: Mercury and Venus stage layer sets and set-pieces (as B-104 + B-105). Mercury day/twilight/night: `rocks_near` crater-rim rubble, `hills_far` basin rims, set-pieces central-peak crater, scarp cliff, ejecta ray field; black sky, no cloud strip; foreground `props/mercury_foreground/` shards, boulders, solarite stubs. Venus surface: `rocks_near` basalt columns, `hills_far` tessera, set-pieces pancake dome, rift wall, collapsed lava tube; `clouds_color.png` as low sulfur haze; foreground vent rubble and glowing crust pieces. Venus deck (no ground): foreground cloud wisps `props/venus_foreground/wisp_*` plus `deck_near/mid/far` translucent planes as the layers, and a `stage.json`.
Accept: as B-104/B-105 (caps, ≤ 700 MB per planet, five stage sheets, peaks); UNITY's R3 depth captures (U-085) for Done.
Files: build_depthbands.py, build_setpieces.py, build_flora.py, gen_deckplane.py, blender/sources/backgrounds/{mercury,venus}_*.blend, Assets/_Game/Art/backgrounds/{mercury,venus}_*/, props/{mercury,venus}_foreground/
Depends: B-107
Lead notes: Cycle 220. The R3 counterpart. The giants' decks (B-097, B-100) already follow the layer rule; they add a `stage.json` and `wisp_*` foreground pieces.

### B-100 · BLENDER · Superseded (D-086) · R4
Goal: Saturn column in 3D (as B-097) from the B-058 sources: floe materials, deck planes for saturn_deck1..3 and saturn_deep (ring-plane line in the deck 1 skydome), plus the Saturn creatures as models from the B-060 sources (helium_jelly with its `rise` clip, hex_drake, floe_moth) and the ring-mining props from B-059/B-068 (ring_ice/ring_rock as low-poly bodies, ring_rig, helium_trap, hexagon_wall_marker).
Accept: contract §9; stamped turntables; UNITY lit preview for Done.
Files: gen_terrain.py, gen_backdrop3d.py, build_creatures_saturn.py, build_props_saturn.py, Assets/_Game/Art/{terrain,backgrounds,creatures,props}/saturn*/
Depends: B-077
Lead notes: Cycle 199. R4 prep.

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

> **C1 (Step 2, D-086): promoted when LEAD approves the C0 style test.** All Depends: C0 approval.
- Promoted cycle 238 (D-097) with fresh numbers: B-119 discs, B-120 starfield, B-121 HUD art, B-122 Pilgrim sheets; U-103 ship + space, U-104 HUD, U-105 surveyor Animator, U-106 C1 measurement; U-091 first. Still Backlog for C1: surveyor dig/build/surprise/jetpack/climb_in clips (B-12x after B-122).
- **C2 Earth flora, designs approved cycle 245** (review_c2_earth_plants_preview.png, df1121f): Nodbell (plains/forest), Shiverbarrel (desert), Curlfrond (forest/taiga; lighter frond tone or mustard tips owed), Whiptuft (plains/coast), Thriftcushion (coast/tundra) + snoozle v2 (plains): one `flora/earth/rigset` holding all six per contract §11.3, ≤ 6 bones each, swaps for the react states; the cartoon Earth ground strip (0191af7, in U-100's contract) and the creature re-ink list (coordination/reports/blender/c2_earth_creature_reink.md: swim cap 12–16 accepted into §11.2; Hadal Maw as a rig set accepted in principle) are the other C2 Earth cards. Cycle 249 (D-115): BLENDER's C2 Earth cards promoted on the approved sources (B-129 flora rig set export, B-130 ground strips, B-131 camp props, B-132 land creatures, B-133 forest + coast backdrops); UNITY's U-110 (biome placement) and U-111 (ground strips in) below stay Backlog until U-106.
M2: Earth/Mars POIs, day/night lighting pass (U), Mars dust storm (U), creature AI v1 (U),
Cryo meter (U), `PlanetDisc` shader with real textures (U). (POI prop sets promoted to B-020, B-021 in cycle 5.)
R3 (drafted cycle 207): U-085 Mercury and Venus in 3D (the R3 counterpart of U-081: B-091 block arrays, B-092 bands incl. the translucent Venus deck strip and the day/twilight/night Mercury skydomes, B-093/B-096 creatures and Wardens through ModelView, B-095 props and station modules via ModelSwap, B-101 scenery; the cinderhulk emission float driven by the day side; the veil serpent chained from veil_serpent_tail + n×body + head, each module's clip offset by J×0.07 cycles for J bones behind it; M3InnerTests + the M3 smoke set re-shot with the depth preset). Promote when U-081 is Done.
S1 → every planet (drafted cycle 220, D-076): the stage layer sets for the giants ride on B-097/B-100 (decks + wisps + stage.json); U-081 and U-085 gain 'stage layers resident and the §11.1 v3 rows green on that planet' as acceptance when promoted; S1 report `coordination/reviews/S1_REPORT.md` + milestone page after U-092 and the owner's playtest.

### U-102 · UNITY · Backlog · C1
Goal: Settings panel (P-39): one panel reachable from the pause menu and the title screen: Film effects (moves the FILM EFFECTS button here), master/music/SFX volume, key rebinding read-only list, language placeholder; saved through GameSettings; cartoon frame per contract §11 UI once B-1xx UI art exists (placeholder frame until then).
Accept: MenuHudTests cover open/close and the film toggle round trip; settings persist across a restart (test); clean console.
Files: Assets/_Game/Code/Runtime/UI/Settings/
Depends: U-095
Lead notes: Cycle 236. Promoted with the C1 cards.

### U-110 · UNITY · Ready · C2
Goal: Biome-aware flora placement: FloraRigs picks plants whose `biomes` list contains the spawn biome (JsonUtility reads the new field from B-129's rig set), weighted so every biome has at least two kinds; the C2 Earth rig set imports with no schema change; the 300-plant loop p99 unchanged.
Accept: RigFloraTests: a desert spawn never picks Nodbell; the plains pick among snoozle / Nodbell / Whiptuft; the perf row unchanged; a plains capture with every plains plant visible.
Files: Code/Runtime/Flora/FloraRigs.cs, Tests/
Depends: U-106, B-129
Lead notes: Cycle 249 (D-115). Promoted when U-106 is in. Cycle 253: B-133 is exported (27143e1): `backgrounds/earth/forest` and `/coast` load by ConfigureFor("earth", "forest" / "coast"), but CartoonStage pins EarthScene = plains, so this card also picks the scene set by the spawn biome (plains / forest / coast) and the Accept gains a forest and a coast capture at 1x. Cycle 259: promoted (C2 batch B).

### U-111 · UNITY · Ready · C2
Goal: Ground strips from art: U-100's placeholder strip replaced by `terrain/earth/ground_strip` (grass), `ground_strip_soil`, `ground_strip_stone` per column material (grass over soil, bare soil where dug, stone where the block is stone), the fill tile from each sheet's bottom 8 px; the strip follows dug heights as today.
Accept: an earth_c0_ground-style capture showing the three materials and a dug hole; TerrainTests unchanged; frame time unchanged.
Files: Code/Runtime/Planet/, Placeholders/terrain/earth/, Tests/
Depends: U-106, B-130
Lead notes: Cycle 249 (D-115). Promoted when U-106 is in. B-130 is exported (558976a): frames 64×152 with the pivot on the ground line at [0.5, 0.842] (`ground_line_px: 128`), 2 m of material below the line and 0.375 m of lip above it, `tile: true`, one frame per terrain column (x mod 8), the fill tile = frame 0's bottom 8 px; GroundStrip.cs needs the key swap only. Cycle 259: promoted (C2 batch B); the sand strip is in (af83541): coast columns map to sand.

### U-113 · UNITY · Done · C2
Goal: Camp props as sprites (D-117): when a `props/common/*` key resolves to a v3 sheet and no model (after B-131's export removes the glbs), `ModelSwap` keeps the SpriteRenderer and plays the sheet's clips through the §11.8 Animator (door `open` once on open, reversed on close; smelter `working` while a craft runs; lamp `flicker` at night and in the dark), pivot and px size from the json at PPU 64 (pad 128×48 tiling at 2 m, wall 64×176 at 1 m, door 88×176, smelter 112×192, crate 80×72, lamp 64×160; ground line 10 px above the bottom), the BaseBuilder fit rules kept; PoiCatalog sizes read from the sheet; the model path untouched for every other key.
Accept: PropSpriteTests: each of the six keys resolves to its sheet with the right frame size and clip set; the door clip plays once on use; the smelter loop runs only while crafting; a plains capture with the camp at 1x; CartoonSmoke and the BudgetGate Earth rows green; no importer error on the six keys.
Files: Code/Runtime/Art/ModelSwap.cs, ModelView.cs, Code/Runtime/Planet/POI/PoiPlacer.cs, Code/Runtime/Building/BaseBuilder.cs, Tests/
Depends: U-106, B-131
Lead notes: Cycle 250 (D-117). The code half is lock-free and sits last on the While-waiting list so B-131's export can land in BLENDER's first slot after it; the check rides your next batch. The B-131 preview is the size reference until the export: blender/preview/review_b131_props_preview.png. Cycle 254 (D-125, P-45): the wall keeps its 1 × 1 cell with the stretch rule; BLENDER redraws the wall as a 64×64 tile (1 × 1 m, tiling in x and y), so no BasePieces change; the door's 88×176 scales uniformly into its 1 × 2 cell (Fit.Height). The code half stays outside Assets until U-106 (D-115). Cycle 259: promoted (C2 batch A, D-131); BLENDER's B-131 export lands right after your code commit. Cycle 262: capture pre-reviewed from disk (reports/unity/u113/camp_1x.png 06:43, uncommitted): the painted crates, the smelter working with its puff, the lamp and the pad modules under the rocket at 1x beside the surveyor and the plants; the grey stand-ins are gone. Root cause found on the way (06:5x): the camp sidecars had no `<key>/json` address, so ModelSwap never took the sheet path; the importer now addresses props/* sidecars and PropSpriteTests asserts the six. Done on the batch A hand-off commit. Cycle 262 (07:1x): DONE (43fe88e9 + ae7b8cfc: SheetProp on the card's SpriteRenderer, the D-125 wall tile and 2 m pad tiling, the door's one-shot forward / backward sampled by hand (a negative Animator.speed warned), the smelter's `working` while crafting, the lamp's `flicker` by night; the props/* sidecar addressing fix; PropSpriteTests + U076SceneTests on the sheet path green, EditMode 339/339; reports/unity/u113/camp_1x.png viewed: the painted camp at 1x).


### U-114 · UNITY · Done · C2
Goal: Earth land creatures on v3 sheets (D-119): after B-132's export removes the stag / wolf models, both play their sheets through the existing creature sheet path (as the gull does) with SpeciesSpec sizes from the drawings (stag 1.5 × 2.0 m, wolf 1.2 × 1.0 m); the brown bear gets a SpeciesSpec (`creatures/earth/bear`, 2.1 × 1.3 m, territorial per Bible §7.1: react = rear-up + huff, flee when pushed, no chase); `flee` and the wolf's `follow` are found by name (indices 0–3 stay Gus's order); P-38: a fleeing creature that meets a wall it cannot climb turns along it or hops a 1-tile step, a chasing one waits.
Accept: CreatureTests: the three species resolve their sheets with no importer error and PawsOnTheGround passes for them; the bear spawns on the plains and rears on contact; a plains capture with stag, wolf and bear at 1x beside the surveyor; the 300-creature loop p99 unchanged.
Files: Code/Runtime/Creatures/CreatureSpecies.cs, Creature.cs, CreatureBrain.cs, Tests/
Depends: U-106, B-132
Lead notes: Cycle 251 (D-119). Code half on the While-waiting list (last); promoted with U-110 / U-111 when U-106 is in. If a stag or wolf still shows the grey model after the export, the Library kept the model address: reimport the two colour maps (D-117's reopen clause). Cycle 259: promoted (C2 batch A); the swimmers (pike / shark / squid, pivot centre, floor clearance 0.38 / 0.87 / 0.70 m, a Water habitat) join this card. Cycle 262: capture pre-reviewed from disk (reports/unity/u114/creatures_1x.png 06:37, uncommitted): the stag, the wolf and the bear on their sheets at 1x beside the surveyor and the camp. The swimmers' frame was empty (the pool's chunks not ready 150 columns out; the capture now walks the surveyor to the shore first): re-shot in the chain. Done on the hand-off with the swimmers' frame and EarthCreatureSheetTests + SwimmerTests green. Cycle 262 (07:1x): LANDED (ae7b8cfc: the land creatures and the swimmers with a Water habitat; EarthCreatureSheetTests + SwimmerTests green; creatures_1x viewed). The swimmers' frame (u114/swimmers_1x.png) has the three in the pool at column −96 but the follow camera kept the pool under the frame's edge: re-shot in hand-off 3 with the camera parked over the pool. Done on that frame (B-135 with it). Cycle 263 (07:5x): DONE (a2c5b4df; reports/unity/u114/swimmers_1x.png over the pool: the pike and the shark in frame, the squid right of it; the layer-order defect visible in that frame is U-122's).

### B-136 · BLENDER · Ready · C2
Goal: The Hadal Maw as a §11.3 rig set (`creatures/earth/hadal_maw/rigset`: body segments, jaw, fins, lure as parts + bones ≤ 6, idle sway and a jaw-open react; no teeth bared, D-087), too big for one frame sheet (your c2_earth_creature_reink.md proposal 2).
Accept: the ten boxes on a stamped assembled review at 1x beside the surveyor; rigset.json valid; sheet ≤ 2048².
Files: blender/scripts/build_creatures_earth_v3.py, Assets/_Game/Art/creatures/earth/hadal_maw/
Depends: B-135
Lead notes: Cycle 251 (D-119). Promoted when B-135's previews are accepted. Cycle 256: DESIGN ACCEPTED and promoted (1fb50b1; review_b136_hadal_maw_preview.png: ~34 m, six bones head / body1 / body2 / tail / jaw / lure, the lure swaps lit / dim / flare, one eye and a closed smile, the open jaw a dark cavern with a tongue and no teeth, bioluminescent dots, the idle a sway travelling down the bones with the lure bobbing, the react a 24° jaw open + head lift + lure flare; ink 2.0–3.0 / 1.0–1.5 px at 1x; parts ~1750×800 at 1x). Export in one BLENDER slot after U-106 (a new key, nothing to replace); UNITY's U-119 drives it as a rig-set creature. Cycle 257 (05:0x, D-127): key = `creatures/earth/hadal_maw` (three segments; the card's `…/rigset` struck); idle at 110 bpm with `cycle_beats: 4` (contract v3.2 field; no validator exception); the 99.9 % palette hit is accepted (the lure's translucent halos). Export-ready (dde7d5e: 8 parts on 1784×744, json valid); one slot after U-106. Cycle 259: export running (heavy_blender.lock 05:24:36, the rig set rebuilt 05:24:39); verified next tick against the log line, the 8-part sheet ≤ 2048², the json with `cycle_beats: 4` and the stamped review. Cycle 260: EXPORT VERIFIED (72cfdd4d; log 05:26:35 OK creatures/earth/hadal_maw: v3 rig set 1784×744 118 KB, 8 parts, 115.6 s, peak 676 MB; hadal_maw.json: six bones, the lure slot with lit / dim / flare, idle 110 bpm `cycle_beats: 4`, react jaw_open 24°; LFS; imported clean with its metas in UNITY's 43fe88e9). review_b136_hadal_maw_assembled.png viewed: the Maw at 1x spans two screens beside the surveyor; the idle sway travels down the bones and the lure bobs; the react opens the jaw on a cavern and tongue. Done on U-119's coast-deep capture.


### U-116 · UNITY · Ready · C2
Goal: The painted Sun in Space (D-123, B-137): `planets/sun/disc_rig.json` replaces the lit spheroid: the body sprite at the game's r 900 px, the flame ring rotating slowly (≈ 1°/s) with a 12 Hz stepped pulse, the corona wash scaled 4x behind it, the two prominence parts on their limb sockets with a slow wobble; the Space scene's light and the planet discs untouched.
Accept: SpaceArtTests: the Sun key resolves to the rig with its parts and sockets; a Space capture with the Sun, Earth and Mars discs at true ratio; the Space perf rows unchanged.
Files: Code/Runtime/Space/SunView.cs, Code/Runtime/Space/SpaceBackdrop.cs, Tests/
Depends: U-106, B-137
Lead notes: Cycle 253 (D-123). Promoted with U-110 / U-111 when U-106 is in and B-137 is exported. Cycle 259: promoted (C2 batch B); the Sun rig is exported (c4225fd): parts body / tongue ×14 / corona / two prominences, the json carries spin 2°/s, pulse 0.08 at 110 bpm, breathe 0.03. Cycle 266: batch B's check shows SpaceArtTests.SpaceUsesTheRealArt red on "the Sun's spheroid" (08:46): the test still expects the lit spheroid the SunView replaced; rewrite it to the rig (the body sprite, the ring parts, the corona) per this card's Accept.


### U-122 · UNITY · Ready · C2
Goal: Three C2 Earth findings from the batch A captures (D-135): (1) the painted layers stack wrongly when the camera is 10 m or more below the datum (the swimmers' frame: the hills layer rides above the sky layer) → the parallax layers keep their order and anchor at any camera height, with a PlayMode assert at −15 m; (2) the drawn surveyor gets the 2-frame bump flash that U-089 gave PlayerView, on SpriteCharacterView; (3) Envirosuit tiers on the drawn surveyor as tints and a badge per tier (D-135: no new sheets), with HazardV2PlayTests rewritten to the cartoon path.
Accept: a coast-pool capture at 1x with the layers in order below the datum; BumpTests sees the flash on the sheet path; HazardV2PlayTests green on the cartoon path; the Earth perf rows unchanged.
Files: Code/Runtime/View2D/ParallaxLayers.cs, SpriteCharacterView.cs, Code/Runtime/Hazards/, Tests/
Depends: U-114
Lead notes: Cycle 262. In batch B (it touches the coast scene U-110 / U-111 also set up). The layer-order bug is the one the owner would see first (any dig or pool below the datum).

### U-118 · UNITY · Backlog · C2
Goal: Mars on the cartoon stage: Mars runs the cartoon path like Earth (ParallaxLayers with the B-141 plains / canyon / storm sets picked by biome, the B-140 rig set and ground strips, the climb sky per D-118 with the butterscotch top, the dust storm as the near storm layer's alpha + wind), the Mars creatures on sheets (B-142; the two v2 models retired by the export), den creatures per D-126 (a `den` prop key in SpeciesSpec: the creature spawns at its mound, idles and reacts there drawing behind it, walks in the open); M1LoopTests and the Mars gameplay tests unchanged; the Mars perf rows green.
Accept: Mars captures at 1x (plains with plants and a dustskater, the canyon, the storm) matching the accepted B-139 composites; TransitionTests and M1LoopTests green; the BudgetGate Mars rows green; StageLayers' Mars tests retired per D-124.
Files: Code/Runtime/View2D/CartoonStage.cs, Code/Runtime/Planet/, Code/Runtime/Creatures/CreatureSpecies.cs, Tests/
Depends: U-110, U-111, U-114, B-140, B-141
Lead notes: Cycle 256. The first planet after Earth in C2 (Bible §12 order). Promoted when the C2 Earth batch is Done. Cycle 258: den species play `idle` (the peek) only at their mound and `idle_open` elsewhere (B-142).

### U-119 · UNITY · Ready · C2
Goal: Rig-set creatures: the Hadal Maw (B-136) as a creature whose view is a RigSet (head / body1 / body2 / tail / jaw / lure bones, the lure swaps lit / dim / flare, the idle sway down the bones, the react jaw open), spawning in the coast deep water (a Water habitat in SpeciesSpec from B-135's swimmers), no attack (D-087: it startles the player with its react and follows at a distance).
Accept: CreatureTests: the Maw resolves its rig set with six bones and plays idle and react; a coast-deep capture with the Maw, a shark and the surveyor at 1x; the Earth perf rows unchanged.
Files: Code/Runtime/Creatures/, Code/Runtime/Flora/RigSet.cs (shared), Tests/
Depends: U-114, B-136
Lead notes: Cycle 256. Promoted with the C2 Earth batch once B-136 is exported. Cycle 257 (D-127): RigSet honours `idle.cycle_beats` (one sway over N beats; default 1) and RigSetBuilder recognises a rig set by the json's `parts` array under the three-segment key `creatures/earth/hadal_maw`. Cycle 259: promoted (C2 batch B); B-136 exports in BLENDER's 05:24 slot under the key `creatures/earth/hadal_maw` with `cycle_beats: 4` (D-127).
### U-120 · UNITY · Ready · C2
Goal: Cold first boot under 5 s (D-129): the boot leg's tile-sheet reads (1067 ms on a cold disk cache in U-106's profile) move ahead of the entry clock with a boot-time sheet prefetch while the title card shows, or the Planet load clock starts at the scene's first rendered frame per Bible §11.1's definition; no change to warm loads.
Accept: the 11-leg probe's Planet load · Earth at boot ≤ 5 s on a cold cache (run right after a build) and on a warm one; TransitionTests and M1LoopTests unchanged.
Files: Code/Runtime/Boot/, Code/Runtime/Perf/MemoryProbe.cs, Tests/
Depends: U-106
Lead notes: Cycle 258 (D-129). Rides the C2 Earth batch; if U-106's warm re-run also reads ≥ 5 s, it moves to the front of that batch. Cycle 259 (05:4x): PROMOTED to the front of C2 batch A: the D-129 warm re-run read 5.44 s, so the boot path is the cause (tile sheets 889 ms warm, 1067 ms cold). Cycle 263: the cartoon-path number is 8.35 s cold (tile sheets 2.9 s; the 3D path read 5.5 s), so the owner's first launch of 0.4.1 takes about eight seconds: named on the page and in C1_REPORT.md; the fix leads batch B with the 0.4.1 run's LastLoadPending list as the prefetch set. Cycle 263 (07:5x, D-136): RE-SCOPED on the 0.4.1 evidence: `terrain settled at 5.69 s; still loading: none` on every leg, so the cold first boot is the terrain's first settle (chunk generation under the 2 ms frame budget behind the boot cover; the scene's own phases take 0.9 s), not sheet loads. The fix is a synchronous or widened first-fill window while the boot cover is up (the budget definition stands); first in batch B.


### U-123 · UNITY · Backlog · C2
Goal: Mercury on the cartoon stage (Bible §12 C2 order 3; §7.3): Mercury runs the cartoon path like Earth and Mars (ParallaxLayers with the B-149 day / twilight / night sets picked by the terminator position, the B-148 rig set and strips, the climb sky per D-118 from an ink-black top), the Mercury creatures on sheets (B-150; the Shadewyrm as a den species per D-126; the Flarewing a flier), the Mercury palette strip; M3InnerTests and the Mercury gameplay tests unchanged; the Mercury perf rows green.
Accept: Mercury captures at 1x (day plains with plants and a Glassback, the twilight band with a Flarewing, the night side with the Shadewyrm at its burrow) matching the accepted B-145 composites; TransitionTests green; the BudgetGate Mercury rows green; StageLayers' Mercury tests retired per D-124.
Files: Code/Runtime/View2D/CartoonStage.cs, Code/Runtime/Planet/, Code/Runtime/Creatures/CreatureSpecies.cs, Tests/
Depends: U-118, B-148, B-149
Lead notes: Cycle 264. Promoted when U-118 Mars is Done.


### U-124 · UNITY · Backlog · C3
Goal: C3 UI in: the paper panels (B-151) on the pause menu, the settings panel (U-102), the inventory and the sign / scroll frames with 9-slice; the planet title cards as the intertitle slide-in on entry (Bible C3), the Film-effects switch art on its toggle; Limelight + Patrick Hand throughout; every menu reachable by keyboard; the toggle persists in the save.
Accept: MenuHudTests cover each panel's open / close and the keyboard path; a title card capture per planet on entry; the settings round trip; clean console.
Files: Code/Runtime/UI/, Tests/
Depends: U-102, B-151
Lead notes: Cycle 265. Promoted after U-118 Mars; U-102 (the settings panel) rides with it.

### U-125 · UNITY · Backlog · C2
Goal: Venus on the cartoon stage (Bible §12 C2 order 4; §7.4 the dive world): the deck and surface scenes (B-152) picked by altitude, the B-153 rig set and strips (deck planks, basalt crust), the climb sky per D-118 from the apricot haze, the Venus creatures on sheets (B-154; the Vent eel a den species per D-126; the drifter and moth fliers); the M3 Venus gameplay tests unchanged; the Venus perf rows green (the 3D path's textures row was the red one, D-089).
Accept: Venus captures at 1x (the deck with the aerostat strip and a drifter, the surface with a crab at a vent) matching the accepted B-147 composites; TransitionTests green; the BudgetGate Venus rows green.
Files: Code/Runtime/View2D/CartoonStage.cs, Code/Runtime/Planet/, Code/Runtime/Creatures/CreatureSpecies.cs, Tests/
Depends: U-123, B-152, B-153
Lead notes: Cycle 265. Promoted when U-123 Mercury is Done.
