# UNITY STATUS
Updated: 2026-11-10 08:31 · Session: 13 (restarted 11-10 00:5x on Fable 5.2, address zuber-57; every session paused 02:24-05:55; earlier entries: coordination/status/archive/UNITY_2026-11-10.md, UNITY_2026-11-09.md)
## Current task
U-209 (D-196 / D-196b, the owner's 0.6.2 playtest: the dig as one motion), the TOP CARD. Started 01:26. In git and green, parts 1-9: 8314a5c2, 1899e88d, 44a79f99, 61bd3943, c9d5f102, 005a42ef, c978a70f (sheet 2 + B-247 import), dad2b77f, 3743bc8a, 0b7bec7b, 78ad3014, 91ffdfc7 (the strips), afaf8fcb. Last green: EditMode DayNightTests + DigStrokeTests 24/24 at 08:19 (the whole EditMode 519/519 at 07:16); PlayMode dig slice + LeadQA D1DigRunTests 31/31 at 08:14; AllocBreakdownTests + TerrainStreamingTests + ClimbSkyPlayTests + RigModuleTests 9/9 at 08:26.

WHAT STANDS BETWEEN U-209 AND DONE (LEAD 08:1x): LEAD's one look at the re-shot strips (sent 08:3x: coordination/reports/unity/u209/, 91ffdfc7) and BudgetGate's Earth C0 within 0.3 ms.

THE DAY'S FINDING (07:45-08:30): THE ALLOCATION COUNTER WAS DEAD. `System.GC.GetAllocatedBytesForCurrentThread` reads 0 B for a known array in Unity's runtime. Every "0 B" row it gave proved nothing: U-209's swing row (which LEAD had accepted), U-195's clods, DayNightTests, ClimbSkyPlayTests, TerrainStreamingTests' Bible 11.1 row, AND BudgetGate's judged "GC per 300 frames" row (green on 0 B in every gate; the live counter printed beside it read 410 KB to 9.6 MB), and CreatureDirector.LastAiAllocBytes (CreatureTests' AI rows).
- The live measures: Unity's "GC Allocated In Frame" (ProfilerRecorder) after a 64 KB control; for a synchronous call the test framework's `Is.Not.AllocatingGCMemory()` after a control. Tests/Unit/Play/AllocBreakdownTests.cs reads a frame's bytes part by part (a reading, not a bar).
- Found and fixed with it: `TerrainStreamer.CurveAt` made two delegates a call (6 KB a frame in every slot, 54-115 KB a frame at rest in the dig slot: 78ad3014); `ArtMaterials.SocketFor` made a key string a call (88 B a frame from the Beam's cable: afaf8fcb). Earth as the game runs: 290 B a frame, the Editor's own floor. A swing adds 0 B over idle (live). The frame a cell opens: 116 862, 19 450, then about 1.1-1.3 KB (first-use growth). The rows: coordination/reports/unity/perf_2026-11-10.md, "Managed allocation a frame".
- All six tests are on the live measure and green (LEAD's ruling 08:1x for the three older ones).

IN THE TREE, NOT YET RUN (written 08:29 under BLENDER's lock, files only):
- Tests/Unit/Play/BudgetGateTests.cs: the GC rows are judged on the live counter less the Editor's floor (FloorThenGcRows: a 64 KB control, then every root object inactive for 300 frames, at the end of the gate's run; the rows' places are kept and filled in then). Code/Runtime/Perf/BudgetMonitor.cs: the dead main-thread figure (gcBytesLast300) is removed; gcProfilerBytes stays.
- EXPECT: Earth and Earth C0 near zero; Mars, Space, the dust storm and the FX peak RED (their allocators are not looked at). LEAD rules per red row: fix now or a named card, and whether 0.6.3 waits (told 08:3x; no answer yet).
- NOT TOUCHED: CreatureDirector.LastAiAllocBytes still reads the dead counter (CreatureTests lines 253, 299): LEAD's to rule.

RESUME POINT, in order:
1. RAM in its own call, the locks; compile + the gate: `tools/unity_profile.ps1` (BudgetGate with graphics; it REWRITES coordination/reports/unity/perf_2026-11-10.md: afterwards restore everything from "## Readings after 0.6.2" down from git (`git show HEAD:coordination/reports/unity/perf_2026-11-10.md`) under the gate's rows).
2. Send LEAD the gate's table: Earth C0's frame time against the last gate (within 0.3 ms), every GC row with its numbers; commit BudgetGateTests.cs, BudgetMonitor.cs, the report.
3. On LEAD's rulings: fix the red GC rows now or flip them to named cards; LEAD's verdict on the strips.
4. ONE EXTRA ROW for LEAD's cause hunt riding a capture lock: CaptureU207Backdrop now has a fourth set, BC7 compressed in the capture from the PNGs (3743bc8a): `tools/unity_capture.ps1 -Name u207 -Test CaptureU207Backdrop`; its rows go under the surface section of the perf report.
5. BUILD 0.6.3: the full sweep in slices, the gate, the dev build + probe with 0.6.2 as the control in the same lock, the release build, the smoke (three locks) → U-197 (collapse) → U-198 (audio) → U-210 (B-247's five Grand icons are imported: icons/catalogue/ + the last part of the creature's rig key) → U-208 (the giants' close view; B-243's handoff, b237_limb_band_design.md). D-200: U-199's v6 surveyor ships as drawn frame sheets on the side-sheet pipeline with U-209's sockets, slide and rest states: nothing to code until the owner accepts the figure.

WHAT U-209 IS IN CODE, so nothing is re-derived:
- Player/DigStroke.cs (+ IDigWorld, DigPhase, DigContact): no Unity objects, no allocation (proven live). A press starts and commits a swing that frame; 0.15 s buffer; held swings chain; five drawings at 12 Hz, the contact on drawing 1; a contact's work = the swing's time over the D1 stroke time; four targets kept 1.5 s (SameTargetM 0.5); the Beam on ≥ 0.1 s, working by the second. THE RHYTHM (P-U209-3, LEAD 07:1x): `Rhythm` counts the run's strokes (a shovel's working contact, a cell the Beam opens); a stroke's time is the tables' × (1 − min(strokes × rhythm_step, rhythm_max)); the run ends on a whiff, on a stroke 3 m from the last (SameFaceM), after 1.5 s of rest. SkillStats.RhythmStep / RhythmMax read dig_rhythm_1 / _2.
- Rig/RigTools.cs: reach 2 m (Beam 5) from the shoulder (DigOrigin, 0.95 m); DigTarget = the first solid point (workables, the drawn field, tiles) on the line from the shoulder through the cursor; DigPoint = the contact pushed 0.75 × the brush's radius into the ground.
- Player/RigToolView.cs: READY 1.5 s after a stroke then STOWED (behind the body; in the hand the tool is drawn in FRONT of the body, the fist over it); the swing on side_dig's clips (dig_down / dig_fwd / dig_fwd_near / dig_up; the forward pair picked by the smaller miss) with the tip on the contact (Player/DigPose.cs: slide up to the clip's slide_max, lunge up to 0.25 m; a clip's slide and lunge are fixed from its CONTACT glove at the swing's start, so the wind-up holds the blade back); the Beam damped 0.06 s, its aim pose shown before the glove is read, its ray to the contact. B-246's sheet 2: fx/dig_reticle (brackets on the brush's circle or the cell, the pip on the contact; white / mustard + 0.09 m / red + 0.2 m no pip; unlit; 40 % after 1.5 s of a still cursor; hidden in menus and transitions), fx/dig_chip (round: drawn FROM THE CONTACT and shown only on the ground's side of the face, a SpriteMask on the face's tangent from the field's slope; cell: on its cell), fx/beam_contact, fx/shovel_swish (dig_down / dig_up; pivoted on the contact drawing's TOOL origin so its end is on a slid tool's blade).
- View2D/SpriteCharacterView.cs: HasClip, PlayStroke, ShowStroke, StrokeFacing, SetStrokePose. Mining/DigFeel: Throw, Chip, the debris from the contact. Audio: Sfx.Swish / Chip, the Beam's hum (SfxSynth placeholders until U-198).
- Tests: Tests/Unit/DigStrokeTests.cs (16); Tests/Unit/Play/DigResponseTests.cs (8); RigModuleTests; SceneCapture.CaptureU209Strips (12 strips; a frame is grabbed at the end of its own LateUpdate: Tests/Unit/Play/LateFrameHook.cs).

## Last completed (this session, all pushed)
- U-192's captures (936dcf05): LEAD marked U-192, B-223, B-224, B-233 Done.
- B-243's import (2a32ccfe); B-242 wired and shot (568634e3, 70220e18, ca74b4c5): B-225, B-242, B-197 Done.
- D-194 (a) on Direct3D 11 (ca2d030c, perf_2026-11-10.md) → D-197; the pin (79bc423b).
- B-246's sheets 1 and 2 (dig_up's slide_max 0.75, d0899819, re-imported in 3743bc8a) and B-247's icons imported (c978a70f).

## Next up
See the resume point. In the gaps, unchanged: name the AI's first-time frame (~86 frames after the spawn, Earth only); the gate's C0 draw-call row on a fixed creature set; U-202 part 2's four readings a build; the capture's UI pass draws panel text soft (the capture, not the game).

## Ready for review
U-209: the rows (ACCEPTED 06:4x; the "0 B a swing" row re-measured live 08:02: idle 25 055 B, swinging 24 750 B in 75 frames) and the strips (sent 08:3x). U-206 (the next smoke's smoke_21 Mars); U-205's G5 objects and smoke_36's pocket (the next smoke). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
(none open; B-246's sheets 1 and 2 and B-247's icons are taken. BLENDER's note for LEAD: a 1.8 m tunnel still buries dig_up's tip 0.13-0.21 m; that needs a lower glove (a new low dig_up drawing), not more slide.)
## Blockers
(none; the gate's GC rows may turn red on Mars and Space: LEAD rules)
## Proposals
- P-U209-3 (the rhythm nodes): YES (LEAD 07:1x): built, 3743bc8a. Mine to flag: the node's holder has the Beam, which makes no contacts, so "a stroke" is a cell the Beam opens and the run carries from cell to cell on the same face (3 m); the shovel's is a working contact.
- P-U209-4 (0 B a swing = nothing over an idle frame; the opening frame allocates): ACCEPTED; the opening frame's bytes are in the perf report.
- P-U209-5 (the carry pose for the dig slot only): ACCEPTED.
- P-U209-6 (the reticle's marks): ACCEPTED; the crack from the contact, clipped to the ground's side: built with a half-plane mask (cheap), not the ground's exact outline.
- P-U209-7 (new): CreatureDirector.LastAiAllocBytes reads the dead counter: move CreatureTests' AI allocation rows to the live measure (the AI step called in a test under the AllocatingGCMemory constraint, or the frame counter with and without creatures): yes / a named card.
## For USER_ACTIONS
(none new)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat, regenerated animator.controller files, link.xml deletions, UnderwaterTint.mat, AddressableAssetSettings.asset's hash line, MERIDIAN_SETUP.md): never staged; commits list files explicitly. perf_2026-11-10.md: a BudgetGate run rewrites the whole file: restore the readings section from git under the gate's rows. The session's scratchpad holds capture_part.ps1 (one capture as a part of a chain under one lock); not needed to resume.
## HeavyJobLock
none held; no want. No background waiters. (BLENDER held heavy_blender.lock at 08:29.)
