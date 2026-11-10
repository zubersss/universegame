# UNITY STATUS
Updated: 2026-11-10 15:58 · Session: 14 (the laptop rebooted 14:18; this window's address zuber-30, LEAD zuber-4a, BLENDER zuber-59; Fable 5.2; everything before 14:30 today: coordination/status/archive/UNITY_2026-11-10.md)

## NOW (15:58): U-212 part 2, U-213 (3) and U-216's code are checked, captured and pushed (126df701); with LEAD for its 4x look. Nothing of mine is uncommitted. No lock, no want
- CHECK 15:35-15:53: compile 0 errors / 0 warnings; EditMode 536/536 (+13); PlayMode HadalMaw | DigResponse | ShovelPlay | DigFeel | SeaUnder | ShoreCreature | StageZoom | StageCamera | LivingStage 28/30 at 15:40 (both reds faults of my NEW tests: the first water tile is a column from the world's own sea columns; a wait counted in frames where a batch run draws hundreds a second), the two classes re-run 2/2 (15:41), LivingStage 1/1 after a scatter change (15:53). NOT run: the smoke (it rides 0.6.4), any built-player price of U-216.
- CAPTURES in coordination/reports/unity/: u212/ (8 frames, each with a _cut2x), u213/ (camp at 64 / 96 / 128, the shaft's floor at 64, its mouth at 96), u216/ (1_on_96, 2_off_96, 3_strip_10s, 4_bend_pair_2x, 5_push_2x, 0_placeholder_page). Run again with `tools/unity_capture.ps1 -Name u212 -Test CaptureU212` (u213 / CaptureU213Camera, u216 / CaptureU216Living): about 1.2 min each.
- ASKED OF LEAD 15:57: (1) play_front (order 19, over the surveyor) against "the reticle always over play_front" (the reticle sorts under the surveyor since U-212 (3)): which gives; (2) my reading of D-209's "nothing runs with less than 0.3 GB free" as a START condition (see the peaks).

## What is in 126df701
- U-212 part 2: BuildSmoke / BuildSmokeD1 keep the Rig's owner ON (the Unreached scope takes it off for one staging call); every shot logs the owner's state ("OWNER OFF" is the report's grep); on foot the smoke points the Rig at the ground 0.84 m ahead of the feet, a staging pins its own aim; BuildSmoke.ShovelShots / BeamShot stage smoke_65_d1_shovel_contact, smoke_66_d1_shovel_follow_through and the new smoke_68_d1_beam_mid_dig for the player's smoke AND for CaptureU212 (the smoke is 80 shots: tools/unity_smoke.ps1); the G5 probe reads 8 m.
- The Hadal Maw (P-U212-1, LEAD: yes): SpeciesSpec.shoreKeep 67 m; no spawn, no swim nearer the shore (CreatureDirector.TooNearShore / ShoreAt). Its first legal column at the coast: 68 m out (the first deep column is 34.5 m out). CaptureU119Maw and CaptureU128Shore still spawn it inside the keep: re-stage when next touched.
- U-213 (3): Camera/StageZoom.cs (off; "-meridianCloseCamera" or "-meridianCloseCamera 128"); StageCamera.Zoom eases (within 2 % after 0.99 s in and 1.00 s out, measured in the test; the largest step 0.03 m of frame a frame); underground = 3 m under the ground's own surface (out above 2.5 m) or ground within 6 m over the head, asked 10 times a second; the frame's bottom keeps the ground's share (P-U213-1, accepted as built); RigToolView.MarkScale keeps the brackets' and the pip's screen size.
- U-216: Code/Runtime/View2D/Living/ (LivingWind: the field and the shader's constants; LivingMesh: one mesh a layer, a 0.2 m grid a swaying piece, uv1 = root + weight + give, uv2 = phase + the normal's x sign; VineChain: a 60 Hz position chain; LivingPlaceholders: a code-painted 1024 x 512 page + normals; LivingStage: the flag "-meridianLivingStage", the four switches WindOn / AirOn / VineOn / LightOn, near / play / play_front / foreground at orders -1 / 0 / 19 / 60, the dig removal), Shaders/LivingStage.shader + LivingWind.hlsl (the wind in the vertex stage; lit only with LIVING_LIT), Settings/Resources/LivingStage.mat + LivingStageLit.mat. At the camp: 144 pieces, about 11 000 vertices, 8 draw calls added. The lamp's normal-map quality has no setter in URP 17.6: set by reflection (LampUsesNormals says whether it took). A dig asks every piece its distance and reads the ground for the near ones (LastDigAsked / LastDigRead).

## MEASURED PEAKS (D-209; the Editor WITH its workers, logs/unity_peaks.log; set MERIDIAN_WATCH_CAP_MB to log one)
| Job | Peak | Free RAM at its lowest | Run |
|---|---|---|---|
| compile (after a reboot, new scripts and a shader) | 2.75 GB (the Editor 0.73) | 20 MB | 15:35 |
| EditMode 536 tests | 3.16 GB (the Editor 1.52) | 32 MB | 15:36 |
| PlayMode slice, 9 classes | 2.80 GB | 152 MB | 15:40 |
| PlayMode, 1-2 classes | 2.58-2.64 GB | 20-103 MB | 15:41, 15:53 |
| a capture (one test, graphics on) | 2.75-2.96 GB | 11-102 MB | 15:43-15:57 |
Every one is over 1.15 GB, so each keeps the 1.5 GB gate; each takes the machine to the page file while it runs (as before today: 0.14-0.17 GB under my locks). The 15:32 compile was STOPPED by a 100 MB free-RAM floor I had set on the watchdog myself (99 MB at 76 s); re-run once with no floor (D-046): clean. Not measured yet: BudgetGate, a build, the probe, the smoke.

## NEXT, in order
1. LEAD's rulings on the captures and the two questions; a fault it finds comes first.
2. U-216's four prices: probe rows in unity_profile for the dev player (the stage on, then each of wind / air / vine / light off: ms a frame and draw calls) with the pilot's density; a short clip only if a tool for it is already on the machine.
3. U-220 the ceiling probe ("-meridianCeilingProbe", dev player only; rides 0.6.4), then U-218 (the importer slices by "cuts" and moves each pivot; ArtImporterTests on a synthetic sheet), then U-217's importer case and stage-file reader (contract §12).
4. Two BudgetGate readings (reading 6 at 13:53 was red on Earth's frame p99 21.58 ms and chunk generation 5/400 over 2 ms, cause not established: readings 3-5 of the same timing code read p99 15.2 / 7.9 / 9.7 ms; if a red stays, one reading with RigToolView at 16bf8110). Then BUILD 0.6.4: dev build, probe (no control row, D-203a; absolute limits, read twice), release build, the 80-shot smoke with -meridianSaveRoot.
5. After: U-214, U-215, U-197, U-198, U-210, U-208. Open under U-211: the AI's first-time frame named, CreatureDirector.LastAiAllocBytes on the live counter, the cell-open frame re-read. U-219 (the live impostor) is Blocked on BLENDER's rig.

## What a new window must know (kept)
- THE OWNER'S SAVE SLOT (D-203): never write under AppData\LocalLow\Zubers\MERIDIAN\saves; tests run on SaveSystem.FallbackRoot; a driven player takes "-meridianSaveRoot <folder>"; unity_smoke / unity_profile refuse a player without the switch (0.6.3's two).
- THE ALLOCATION COUNTER: GC.GetAllocatedBytesForCurrentThread reads 0 in Unity; use ProfilerRecorder "GC Allocated In Frame" after a 64 KB control, less the Editor's floor, or Is.Not.AllocatingGCMemory().
- THE GAME LOADS NO SPRITE ATLAS (EditorSettings m_SpritePackerMode 0; the probe's "atlases":0): a sheet ships as written, megabytes bind (D-208).
- One lock over several calls: a scratchpad wrapper takes the lock on the first part, sets MERIDIAN_LOCK_HELD = 1 round each tool, releases on the last or on a red part. unity_check runs the whole PlayMode unless -SkipPlayMode / -PlayFilter.
- A batch PlayMode run draws hundreds of frames a second: wait by Time.time, not by frame counts. Venus' deck wind pushes a grounded surveyor (disable Planet/Weather/VenusWind in such a test).
- A gate run rewrites coordination/reports/unity/perf_2026-11-10.md (0.6.3's report): copy the result to u211/gate_readingN.md and `git checkout --` the report.
- A shell heredoc eats backticked words: write status text with the Write tool.

## Last completed (all pushed)
126df701 (U-212 part 2, U-213 (3), U-216's code) · 18cc9350 (the v7 live-or-sheets page → D-208) · daa78ab9 (the v7 piece format answered → D-206) · de36b4f1 (U-212 part 1) · 16bf8110 (U-211 (a), (b)).

## Ready for review
U-212 (parts 1 and 2: captures u212/; the smoke itself with 0.6.4). U-213 (3) (captures u213/; the 128 frame is the closer trial). U-216 (code and captures u216/; its built-player prices owed). Earlier, still unjudged: U-129 slice 1, U-130 slice 1, U-133 slice 1, U-146, U-144.
## Handoffs
(none open)
## Blockers
(none)
## Proposals
- P-U216-1: play_front draws over the surveyor (19) and the reticle under both (16); "the reticle always over play_front" would put the marks over the surveyor again. Built the first way; LEAD to rule.
## For USER_ACTIONS
(none new)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat, regenerated animator.controller files, common.asset's line endings, link.xml and its meta, UnderwaterTint.mat, MERIDIAN_SETUP.md): never staged; commits list files explicitly.
## HeavyJobLock
none held; no want. No background waiters.
