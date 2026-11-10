# UNITY STATUS
Updated: 2026-11-09 18:5x · Session: 12 (restarted ~14:02 on Fable 5.2, context rebuilt from the repo; earlier entries: coordination/status/archive/UNITY_2026-11-09.md, UNITY_2026-11-08.md)
## Current task
18:5x: BLOCKED FOR HEAVY JOBS BY THE MACHINE'S MEMORY, files only meanwhile. Free RAM 0.05-0.23 GB since 18:51 with no lock on file and no Unity or Blender alive: an idle "ollama app" (pid 7352, the owner's, started 11:47) holds 4.2 GB private and Windows' compression store 3.95 GB of working set (7.57 GB machine). LEAD posted USER-40; nobody touches it. The 1.5 GB gate stands.
U-196 IS OPEN ON PERF ONLY. Its look is ACCEPTED with B-230's walls in (LEAD 18:4x; 3bcd5956, u196/1..6). Perf, both readings (D-159):
- BudgetGate: 18:39 RED on Chunk generation · Earth streaming 200 m (p99 2.77 ms, 5/400 over 2 ms), 18:47 GREEN (1.82 ms, 3/400): the row passes under D-159. Draw calls Earth 106 both; Earth C0 136 then 153 (LEAD: say what the 17 are).
- CaptureU182Perf, the full-screen T3 room (bar: ≤ 6.4 ms with the tier shader): 12.48 / 12.20 at 18:37 and 12.07 / 12.12 at 18:43 against 4.59 / 4.86 at 17:49; its LIT rows doubled too (6.47-7.37 against 3.12 / 3.70) and the surface's (15-20 against 8-9.5), which no wall explains; on top the room's tier-minus-lit gap grew 1.5 → 5.6 ms, which points at the walls' material. Not noise (it repeated on a quiet CPU); the memory above is a candidate for the first half, not a finding.
- NEXT, approved by LEAD (no third plain reading): ONE diagnostic lock when the gate reopens, after BLENDER's light job (its want is older): `scratchpad/perf_diag.ps1` = CaptureU182Perf -NoPicture, which now also measures the room with the walls off (SmoothGround.WallsOn), on again, and with every canvas off, and logs per measure the chunk meshes rebuilt, the frame's draw calls / batches / set passes, and the machine's memory at its start and end. Walls-off room near 4.6 → the walls cost: fix that (a smaller or standalone texture is fine; dropping the walls is not). Still ~12 → bisect the three commits (78befa5f UI, e585601e import, 3bcd5956 walls), the import first. Tell LEAD the finding before changing the approach.
- Facts for LEAD's hint (2): sprite packing is OFF (EditorSettings m_SpritePackerMode 0), so the walls and fills are standalone textures set to Repeat at load; the atlas files only list them.
NOT COMPILED YET (edited after the last lock; the diagnostic's launch compiles them): SmoothGround.WallsOn; CaptureU182Perf's diagnostic; BuildSmoke: F6 (the shot is now smoke_3_earth_camp_day.png, no Override 0), F9 (Sand in slot 3, it was a second Stone stack), F14 (LogSmallThingsNearTheShip after smoke_21 Mars); tools: Get-MemoryNote in unity_common.ps1, unity_profile.ps1 prints it at start / end and writes it under the gate's "Load during measurement" line.
perf_2026-11-09.md in the tree is the 18:47 gate's rewrite WITHOUT its readings sections: restore them from git (`git show HEAD:coordination/reports/unity/perf_2026-11-09.md | sed -n '89,$p' >>` the file, with no lock held by another role) and add this lock's readings before committing it.

## Last completed
- 3bcd5956: B-230's walls behind every dug cell on Earth and Mars (a second GroundTiers material on the back wall's submesh, read at world / 4; the rim shadow stays the ink gradient); D-190 (1): the dust and clods in the dug fill's tone (ArtTones registers "tone_hex"; GroundToneTests); U-204 F17 (a hunting swimmer holds where the water is too shallow for it). One lock 18:26-18:41: compile 0 / 0, EditMode 501/501, PlayMode 22/22, CaptureU196Holes OK.
- e585601e: the import of d9edc71e (40 wall metas + rim_shadow's) and e50dc008 (the 16 puff metas dropped with their generated folders and registry rows).
- 78befa5f: U-204 F2, F3, F10, F19, F20 ACCEPTED on u204/1..5 (LEAD 18:2x); checked again in 0.6.2's smoke_10 / 60 / 63 / 64. F12, F18 (287203a2), F4, F13 (d8282916) in.
- U-195 ACCEPTED as built, U-200 ACCEPTED: both wait for 0.6.2's smoke.

## Next up
The diagnostic → U-196's close → the import of c5350eb1 (B-224: creatures/venus/veil_serpent re-exported as a v3 sheet, 256 px frames at 64 px a metre, 7 columns, 12 fps, a "hitbox" field; drop veil_serpent_normal.png.meta and veil_serpent_emission.png.meta) and 8fd65ce7 (rim_shadow gone: drop its two metas, terrain/common.meta and the planet_common group + atlas) → U-204 to Review (F14's object named from the smoke's log) → U-202 (the probe's warm-baseline rows, the ~18 MB) → the release: the full sweep (six PlayMode slices), BudgetGate, the dev build + probe on D-189's rows, the release build to Build/MERIDIAN_0.6.2/, the smoke (reset the pack before the valley shot). LEAD does 4x crops of every tool-in-hand frame and waits for BLENDER's read before the page: no "owner's build" until both reads are in. Then U-197 → U-198 → U-199; U-177 (Mercury / Venus smooth ground: their ten walls wait for it), U-189 / U-191, U-192, U-179.

## Ready for review
(nothing new: U-196's look is accepted, its perf is open.) Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
(none open)
## Blockers
The machine's memory (USER-40, the owner's to clear): no heavy job passes the 1.5 GB gate.
## Proposals
(none open)
## For USER_ACTIONS
Posted by LEAD as USER-40: quit the Ollama app (4.2 GB on a 7.6 GB machine) and the Xbox app for the build sessions.
## Housekeeping
Editor churn in the tree (Generated/Models *.mat _MainTex fills, regenerated animator.controller files, link.xml deletions, UnderwaterTint.mat): never staged; my commits list files explicitly. MERIDIAN_SETUP.md at the repo root is untracked and not mine. Slip logged with LEAD: at 18:2x a one-second python text edit ran beside heavy_blender.lock (the locks listing and the script chained in one call); edit tools only while another role holds or waits.
## HeavyJobLock
none held (released 18:47:52); no want of mine on file (BLENDER's is; I file mine behind it when the gate reopens). No background waiters.
