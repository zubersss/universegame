# UNITY STATUS
Updated: 2026-11-09 21:1x · Session: 12 (restarted ~14:02 on Fable 5.2, context rebuilt from the repo; earlier entries: coordination/status/archive/UNITY_2026-11-09.md, UNITY_2026-11-08.md)
## Current task
21:1x: BUILD 0.6.2, the release path. Everything up to the release build is green; LEAD's GO for the release build and the smoke is given (D-191 amended). WAITING ON THE RAM GATE: free RAM read 1.41-1.47 GB at 21:12-21:13 (gate 1.5; the three sessions hold ~1.3 GB of working set, Ollama is down at 58 MB); no lock held, none on file. Next, in order: `scratchpad/rel062_release.ps1` (the release player to Build/MERIDIAN_0.6.2/, ~3 min, its own lock) → `tools/unity_smoke.ps1` (79 shots, ~6.3 min, its own lock) → tell LEAD AT ONCE that the build is written (BLENDER's held exports wait on that word) → my own view of the smoke (10, 18, 20, 42, 47, 54-57, 60, 63, 64, 65, 66; F14's object from the player log's "[MERIDIAN] smoke F14" lines) → smoke report + tests/perf reports + this file. NOT the owner's build until LEAD's 4x crops and BLENDER's read are in.
What is green (GameInfo 0.6.2; code 2f08ebb9, no code commit since):
- The sweep 19:38-20:46: slice A 26/26; B 28 + 3 skipped (the stag's own Ignore; FilmPlay's two, on a graphics device 1 passed, the 1080p row the player's) with its AI row green under D-193; C 36/37, M1LoopRun2 then green alone and with its class (the tile 7 → 0, 0 after the reload; the test now asserts the tile is air BEFORE the save); D 28/28; E 36/36; F 24 + 1 skipped; LeadQA M1Loop 1/1, M3Inner + D1DigRun 8/8. The end on the committed tree: compile 0 / 0, EditMode 502/502.
- BudgetGate 20:48: GREEN on its first reading (chunk generation p99 1.72 ms).
- Dev build 20:53-20:58: Build/MERIDIAN_0.6.2_dev (587 MB). Its probe twice (20:58, 21:03): BUILD MEMORY GREEN; D-189's rows scripted (U-202 part 1): Return · Space after Mars -0.2 / +0.4 % against the warm leg, Space first → warm +101 / +103 MB, creep -0.5 / +1 MB.
- D-191 (2) with a control: 0.6.1's own dev player probed in the same lock at 21:06 reads ABOVE 0.6.2 on every frame and transition row (transitions 1.00-1.16 s against 0.6.2's 0.91-1.00; its own afternoon figure was 0.78). The build is not slower than 0.6.1; tonight's machine reads 28-48 % slower than this afternoon's, cause not found (memory clean, up 9.4 h). D-192's condition met: B-230's walls ship.
Rulings of this evening that changed tests or tools (all in git): D-191 (the Editor capture's shader bar is the ratio tier ÷ lit ≤ 1.52 in one process; the player's rows judged against the last build's control run in the same lock), D-192 (a room with a back wall: ≤ 1.85, reads 1.80), D-193 (the AI rows: 150 warm frames whose worst ≤ 2.0 ms, 300 measured with D-047's limits, 0 B and no collection a frame).
UNCOMMITTED, parse-checked, not yet run: tools/unity_profile.ps1 `-Control <version>` (the last build's dev player probed after this build's, the frame and transition rows judged at 20 % against it, a table in the report); commit with the release's reports.

## Last completed
- U-196 → REVIEW (LEAD 19:3x): look accepted with B-230's walls (3bcd5956), perf closed under D-191 / D-192; waits for 0.6.2's smoke_54-57. U-195, U-200: accepted, wait for the smoke.
- U-204: F2, F3, F10, F19, F20 accepted on u204/1..5; F12, F18, F4, F13, F17 in; F6 (the shot renamed smoke_3_earth_camp_day.png), F9 (Sand in slot 3) in the smoke script; F11 answered (icons/snow/base's own silhouette); F14's object to be named from the smoke's log. To Review after the smoke.
- U-202 part 1 (fd767362): the probe's Return rows against "Space after Earth", "Space first → warm" ≤ 150 MB, the cold figure as info through 0.6.4. Part 2 (the ~18 MB): the nine probe files of 11-09 read Space after Mars at 1216-1243 MB private in both builds (one outlier 1075), handles 150, every counter equal: inside the run-to-run swing; four readings each still owed for the card's wording.
- Imports: e585601e (B-230's walls, the puffs removed), 72976545 (the veil serpent v3, rim_shadow and planet_common gone, B-223's bay and camp icon).

## Next up
After 0.6.2 is out: U-205 (LEAD: a grain-free and a flat wall tile in the interleaved capture; B-225's shallows), name the AI's first-time frame (~86 frames after the spawn, Earth only) and warm it at load if it can be, make the gate's C0 draw-call row repeatable (a fixed creature set), U-192 (the Pilgrim's rig in the bay on layer1.json's ship_ground, the catalogue's Camp icon, the veil serpent's gentle-drifter temper, B-233's ten site icons), U-197 → U-198 → U-199, U-177 (Mercury / Venus smooth ground: their ten walls wait for it), U-189 / U-191, U-179.

## Ready for review
U-196, U-195, U-200 (on 0.6.2's smoke). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
(none open)
## Blockers
The RAM gate, on and off tonight: 0.05 GB at 18:51 under an idle 4.2 GB Ollama app (USER-40, cleared by 18:59), 1.41-1.47 GB at 21:12.
## Proposals
(none open)
## For USER_ACTIONS
USER-40 (LEAD): quit the Ollama app and the Xbox app for the build sessions.
## Housekeeping
Editor churn in the tree (Generated/Models *.mat, regenerated animator.controller files, link.xml deletions, UnderwaterTint.mat): never staged; commits list files explicitly. perf_2026-11-09.md: a BudgetGate run rewrites the whole file and a probe run replaces its last section ("Memory in the development player"): restore the readings sections from git under the gate's rows after a gate run (`git show HEAD:<file> | sed -n '<the line before "## Readings for 0.6.2">,$p' >>`), and save the last build's player rows before a probe. Slip logged with LEAD: at 18:2x a one-second python text edit ran beside heavy_blender.lock; edit tools only while another role holds or waits.
## HeavyJobLock
none held (released 21:09:52); no want. No background waiters.
