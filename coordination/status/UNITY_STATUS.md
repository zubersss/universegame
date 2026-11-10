# UNITY STATUS
Updated: 2026-11-10 17:18 · Session: 14 (the laptop rebooted 14:18; this window's address zuber-30, LEAD zuber-4a, BLENDER zuber-59; Fable 5.2; everything before 14:30 today: coordination/status/archive/UNITY_2026-11-10.md)

## PAUSED BY THE OWNER 17:18 (LEAD's relay of "Pause all work"). I take no further turns until the owner or LEAD says resume
- Stopped cleanly: no Unity job was running, no lock and no want of mine, no Unity process, no Assets/InitTestScene*. Nothing was cut mid-job.
- Everything checked is pushed: 426404c1 (U-216: the foreground clears round the surveyor and fades underground; the dev player's probe leg that prices the living stage, with its report rows) on top of 126df701 (U-212 part 2, U-213 (3), U-216's code).
- UNCOMMITTED, UNFINISHED, IN THE TREE (written 17:16-17:17, NOT compiled, NOT run): F1's flora half, two files:
  - Assets/_Game/Code/Runtime/Flora/FloraRigs.cs: HookDigs(rig) / OnDug / Uproot(at, reach) / Grounded(root) / Remove(plant), the counter Uprooted, RigPlant.groundChecked, and in LateUpdate's ranking pass a once-only ground look at each plant within 30 m of the camera on settled ground (a plant sown over an old hole after a reload goes); OnDestroy unhooks.
  - Assets/_Game/Code/Runtime/View2D/CartoonStage.cs: one line, `Flora.HookDigs(side.rig)` in ConfigureFor.
  No test for it is written yet. Editor churn also in the tree as always (AddressableAssetSettings.asset, common.asset, link.xml, UnderwaterTint.mat, MERIDIAN_SETUP.md, Generated/*): never staged.

## FIRST STEPS ON RESUME, in order
1. F1 (LEAD's three rules, 17:1x): (a) finish the flora half: a PlayMode row (at the camp nothing is uprooted on untouched ground for 3 s; a dig under one plant's root takes that plant and no other; `Uprooted` counts it) and the rule "no plant is placed over open ground when a chunk loads or streams in" (the ranking pass's once-only look does this as a plant comes within 30 m: say so, or move it to Populate if LEAD wants it at load); (b) a decorative POI prop settles onto the new ground under it or goes with a puff when none is within reach (PoiPlacer: props are SpriteRenderers under a POI root that the world wrap moves; solid ones own a BoxCollider2D laid from the art; some carry a model swap: NOT started; my estimate is over an hour); (c) NOTHING THE PLAYER USES GOES WITH A PUFF: for the Pilgrim and its pad, the camp's stations (sell, craft, the Skill Tree's place), a vault door, a placed ladder or winch, a Warden: read what the game does today under each (settles, or its footing cannot be dug), keep that, and write one test for the Pilgrim's pad and one for the sell point. NOT started.
2. The 128 camera's frame drop (LEAD: YES, before 0.6.4, behind the close camera's flag): StageInput gains the dig point's depth under the feet; the frame's bottom eases down to keep 1.2 m of ground under that point while the aim is down, back when the tool rests; an EditMode row for no cut. NOT started.
3. F2, the hole's right lip (the grass strip cut on a slant, a tan wedge, a triangle of the wall's shade above the ground line where a hole meets the surface on its right: u212/1, 2, 3 and the shaft's top right corner in u213/4): NOT looked at yet; it is in SmoothGround's rim. Fix if under an hour, else one line to LEAD on why not.
4. ONE check for 1-3 when the gate reads 1.5 GB in its own call (compile + EditMode, then PlayMode DigResponse | ShovelPlay | DigFeel | RigFlora | PoiPlay | StageZoom | StageCamera | LivingStage and the new rows), by the locks (BLENDER had a want at 17:15). Commit.
5. U-220 the ceiling probe ("-meridianCeilingProbe", dev player only), then U-218 (the importer slices by "cuts" and moves each pivot; ArtImporterTests on a synthetic sheet), then U-217's importer case and stage-file reader.
6. Two BudgetGate readings (reading 6 at 13:53 was red on Earth's frame p99 21.58 ms and chunk generation 5/400 over 2 ms, cause not established; if a red stays, one reading with RigToolView at 16bf8110). Then BUILD 0.6.4: dev build, the probe read twice (U-216's four prices and the ceiling probe ride it; no control row, D-203a), release build, the 80-shot smoke with -meridianSaveRoot.
7. After: U-214, U-215, U-197, U-198, U-210, U-208; open under U-211: the AI's first-time frame named, CreatureDirector.LastAiAllocBytes on the live counter, the cell-open frame re-read; the next shaft capture 3 m deeper (the Topsoil to Subsoil blend band, the "smear" in u213/4). U-219 is Blocked on BLENDER's rig.

## Where the cards stand
- U-212: ACCEPTED on the captures (LEAD 16:01), open until 0.6.4's smoke. P-U212-1 ruled yes (the Hadal Maw 67 m off the shore; re-stage CaptureU119Maw and CaptureU128Shore when next touched).
- U-213 (3) the close camera: ACCEPTED on the captures; the frame drop at 128 owed (step 2).
- U-216: its code, tests and captures are in; the clearing accepted (LEAD 17:1x); D-206b: play_front stays over the surveyor with the reticle under both; a find still draws over play_front (not checked in code yet). Its four prices are a probe leg that has NOT run on a player.
- v7 pages: the piece format (D-206), live-or-sheets (D-208: sheets, trimmed; U-218 mine; U-219 the impostor, Blocked).

## MEASURED PEAKS (D-209 / D-209a; the Editor WITH its workers, logs/unity_peaks.log; set MERIDIAN_WATCH_CAP_MB to log one, and NO free-RAM floor)
| Job | Peak | Free RAM at its lowest | Runs |
|---|---|---|---|
| compile | 2.06-2.75 GB (the larger after a reboot with new scripts and a shader) | 20-76 MB | 15:35, 17:11 |
| EditMode 536-537 tests | 2.44-3.16 GB | 9-32 MB | 15:36, 17:12 |
| PlayMode slice, 9 classes | 2.80 GB | 152 MB | 15:40 |
| PlayMode, 1-2 classes | 2.39-2.64 GB | 20-103 MB | 15:41, 15:53, 17:13 |
| a capture (one test, graphics on) | 2.40-2.96 GB | 11-102 MB | 15:43-17:15 |
My gate stays 1.5 GB at the START (LEAD, D-209a: 0.3 GB is a start condition, never a floor during a run; Editor jobs page by nature). ONE trial owed when free memory sits between 1.2 and 1.5 GB for ten minutes with my want on file: one compile + EditMode started there, timed against the same job started at 1.5 or more (2.3-2.4 min); within 1.3 times and not stopped: the gate becomes 1.2. The 15:32 compile was stopped by a 100 MB floor I had set myself; re-run once (D-046): clean. Not measured yet: BudgetGate, a build, the probe, the smoke.

## What a new window must know (kept)
- THE OWNER'S SAVE SLOT (D-203): never write under AppData\LocalLow\Zubers\MERIDIAN\saves; tests run on SaveSystem.FallbackRoot; a driven player takes "-meridianSaveRoot <folder>"; unity_smoke / unity_profile refuse a player without the switch (0.6.3's two).
- THE ALLOCATION COUNTER: GC.GetAllocatedBytesForCurrentThread reads 0 in Unity; use ProfilerRecorder "GC Allocated In Frame" after a 64 KB control, less the Editor's floor, or Is.Not.AllocatingGCMemory().
- THE GAME LOADS NO SPRITE ATLAS (EditorSettings m_SpritePackerMode 0; the probe's "atlases":0): a sheet ships as written, megabytes bind (D-208).
- One lock over several calls: a scratchpad wrapper (job_part.ps1: -First takes the lock, sets MERIDIAN_LOCK_HELD = 1 round each tool, -Last or a red part releases it). unity_check runs the whole PlayMode unless -SkipPlayMode / -PlayFilter. Captures: `tools/unity_capture.ps1 -Name u212 -Test CaptureU212` (u213 / CaptureU213Camera, u216 / CaptureU216Living), about 1.2 min each.
- A batch PlayMode run draws hundreds of frames a second: wait by Time.time, not by frame counts. Venus' deck wind pushes a grounded surveyor (disable Planet/Weather/VenusWind in such a test).
- The camp's whole flat ground counts as "pad" (TerrainStreamer.PadTop): a scatter that skips pad columns skips the camp.
- A gate run rewrites coordination/reports/unity/perf_2026-11-10.md (0.6.3's report): copy the result to u211/gate_readingN.md and `git checkout --` the report.
- A shell heredoc eats backticked words and breaks on an apostrophe: write status text and C# snippets with the Write tool.

## Last completed (all pushed)
426404c1 (U-216: the clearing, the probe leg) · 126df701 (U-212 part 2, U-213 (3), U-216's code) · 18cc9350 (the v7 live-or-sheets page → D-208) · daa78ab9 (the v7 piece format answered → D-206) · de36b4f1 (U-212 part 1) · 16bf8110 (U-211 (a), (b)).

## Ready for review
U-216's prices when 0.6.4's dev player exists. Earlier, still unjudged: U-129 slice 1, U-130 slice 1, U-133 slice 1, U-146, U-144.
## Handoffs
(none open)
## Blockers
The owner's pause (17:18).
## Proposals
(none open: P-U212-1, P-U213-1 and P-U216-1 are ruled)
## For USER_ACTIONS
(none new)
## Housekeeping
Editor churn in the tree (see the pause block): never staged; commits list files explicitly.
## HeavyJobLock
none held; no want. No background waiters.
