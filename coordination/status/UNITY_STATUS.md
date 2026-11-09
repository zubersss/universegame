# UNITY STATUS
Updated: 2026-11-09 16:5x · Session: 12 (restarted ~14:02 on Fable 5.2, context rebuilt from the repo; earlier entries: coordination/status/archive/UNITY_2026-11-09.md, UNITY_2026-11-08.md)
## Current task
16:5x: 0.6.2's work. U-195 READY FOR REVIEW (d8282916 the code, 443868e0 the captures, 117118bd the re-shoot; u195/1..5): tests green, BudgetGate green on its second reading (Chunk generation p99 2.13 then 1.79 ms, D-159), the captures re-shot after the first set showed the clods as one clump in the bowl (now small, from the bowl's mouth, in the air at 0.2 s). LEAD's open call: the clods' speed (2-4 m/s lifts 0.2-0.8 m; 3-5 would clear the surface line every time). Lock-free now: U-200's sorting part (the surveyor against the rocket's fin and pad), then U-196's back wall.
- ACCEPTED by LEAD 16:4x on the captures: U-196's F7 (u200/2: the T1 / T2 border a smooth diagonal under a 33-degree slope; the cause was the border's wobble out-running the hill's slope, not the line texture) and U-200's wedge (u200/1: both wall columns into the ground at both corners).
- In d8282916, tests green, pictures not yet seen in a smoke: U-204 F4 (hint cards at -196, clear of the tool slot's name plate) and F13 (a hint and its arrow step aside under a planet's title card).
- LEAD's watch on u200/2: the T1 / T2 crossfade still reads a little like a shadow at its edge; judged again on U-196's captures.

## Last completed
- U-195's code (d8282916): Mining/DigFeel (4-8 clods a stroke by the cells opened, 2-4 m/s under the planet's gravity, resting where they land, gone at 0.6 s; B-232's fx/dig_clods/t<n> once exported, a drawn stand-in of the same shape until then; a pool of 48, drawn only, off in transitions, in the budget's particle count), CameraFollow.Kick (2 px along the stroke, one frame), UI/HudPackFlight + SideHud.BumpPack (the material's icon from its drop to the PACK readout in 0.35 s, a 10 % bump about the tag's centre, a tick), SfxSynth.ClodFall / PackTick (stand-ins until D-186's samples; credits). DigFeelTests ×4 (0 B allocated with clods flying), DigFeelSoundTests ×3.
- U-203 Build 0.6.1b DONE (LEAD 16:0x; the owner's build): the held tool stays in hand through a stroke (no baked pick), the depth tag draws only with a depth (U-201); 4588b3f0 + 2fce1044.
- U-194 Build 0.6.1 DONE (LEAD 15:4x): the sweep after the restart (11a86b34), the wall fix (114ffba1), the build's reports (17e6d96d); the probe's Return · Space row on the warm Space leg (D-189).

## Next up
U-196 → U-200 (the surveyor's order against the rocket's fin and pad, with a hatch climb-in and a launch capture) → U-204's other rows → U-202 → 0.6.2's release (the full sweep, BudgetGate, the probe with D-189's rows, the smoke; reset the pack before the valley shot in the smoke script) → U-197 → U-198 → U-199; the giants (U-189 / U-191: B-220's continue_rows arrive planet by planet), U-177, U-192, U-179 after.

## Ready for review
U-195 (d8282916 + 443868e0 + 117118bd; u195/1..5; DigFeelTests ×4, DigFeelSoundTests ×3). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
(none unrouted)
## Blockers
(none)
## Proposals
(none open: P-58, clods per stroke, RULED 16:2x as built). Asked 16:5x: with U-195 in, B-226's shovel_flick clod (F1b, as big as the torso) outweighs the new clods: lose the flick's clod or the flick for the shovel (LEAD / BLENDER).
## For USER_ACTIONS
(none)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat _MainTex fills, animator.controller files, link.xml deletions, AddressableAssetSettings line endings, UnderwaterTint.mat): never staged; my commits list files explicitly. MERIDIAN_SETUP.md at the repo root is untracked and not mine.
## HeavyJobLock
none held (the re-shoot's lock released 16:52:52); no want. No background waiters.
