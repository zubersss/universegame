# UNITY STATUS
Updated: 2026-11-09 16:2x · Session: 12 (restarted ~14:02 on Fable 5.2, context rebuilt from the repo; earlier entries: coordination/status/archive/UNITY_2026-11-09.md, UNITY_2026-11-08.md)
## Current task
16:2x: 0.6.2's work, U-195 first. The first 0.6.2 check is GREEN (d8282916; one lock 16:16-16:24: compile 0 / 0, EditMode 496/496, PlayMode DigFeel / ShovelPlay / ShovelHollowPlay / MenuHud / AudioDirector / Fx / DigPlace / DigRunPlay / RigModule / InventoryPlay / Harvest / StageCameraPlay / FeelPlay / HintPlay / Base 45/45, LeadQA D1DigRun 1/1). Lock-free now, beside BLENDER's B-220 export locks: U-196 (the tier shader's two darkening terms, B-228's F7: the tier border from the drawn surface), then U-200's surveyor order, U-204's other rows, U-202.
- Still owed by U-195 before Review, in my next lock: CaptureU195DigFeel (u195/1..4, written, not run) and BudgetGate (Earth C0 within 0.3 ms).
- In d8282916, tests green, pictures not yet seen: U-204 F4 (hint cards at -196, clear of the tool slot's name plate) and F13 (a hint and its arrow step aside under a planet's title card); U-200's wall foot (the drawing reaches the lowest ground under its corners: smoke_18's walls view feet 0.50 / 0.48 m, the downhill corner -0.01 m, the collider still on the highest).

## Last completed
- U-195's code (d8282916): Mining/DigFeel (4-8 clods a stroke by the cells opened, 2-4 m/s under the planet's gravity, resting where they land, gone at 0.6 s; B-232's fx/dig_clods/t<n> once exported, a drawn stand-in of the same shape until then; a pool of 48, drawn only, off in transitions, in the budget's particle count), CameraFollow.Kick (2 px along the stroke, one frame), UI/HudPackFlight + SideHud.BumpPack (the material's icon from its drop to the PACK readout in 0.35 s, a 10 % bump about the tag's centre, a tick), SfxSynth.ClodFall / PackTick (stand-ins until D-186's samples; credits). DigFeelTests ×4 (0 B allocated with clods flying), DigFeelSoundTests ×3.
- U-203 Build 0.6.1b DONE (LEAD 16:0x; the owner's build): the held tool stays in hand through a stroke (no baked pick), the depth tag draws only with a depth (U-201); 4588b3f0 + 2fce1044.
- U-194 Build 0.6.1 DONE (LEAD 15:4x): the sweep after the restart (11a86b34), the wall fix (114ffba1), the build's reports (17e6d96d); the probe's Return · Space row on the warm Space leg (D-189).

## Next up
U-196 → U-200 (the surveyor's order against the rocket's fin and pad, with a hatch climb-in and a launch capture) → U-204's other rows → U-202 → 0.6.2's release (the full sweep, BudgetGate, the probe with D-189's rows, the smoke; reset the pack before the valley shot in the smoke script) → U-197 → U-198 → U-199; the giants (U-189 / U-191: B-220's continue_rows arrive planet by planet), U-177, U-192, U-179 after.

## Ready for review
(nothing new: U-195 after its captures and BudgetGate). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (UranusStageTests +1); U-144 (NeptuneStageTests +3).
## Handoffs
(none unrouted)
## Blockers
(none)
## Proposals
P-58: clods per stroke, not per opened cell: 4 for one cell, +2 a further cell, 8 at most (DigFeel.ClodsFor). A brush stroke opens 1-4 cells and the Beam lands a stroke every 0.17 s at T1: 4-8 per cell would put up to 115 clods in the air; the card's Goal and Accept say "per stroke", the 14:3x format note "per opened cell". Built per stroke; say if you want it per cell with a cap.
## For USER_ACTIONS
(none)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat _MainTex fills, animator.controller files, link.xml deletions, AddressableAssetSettings line endings, UnderwaterTint.mat): never staged; my commits list files explicitly. MERIDIAN_SETUP.md at the repo root is untracked and not mine.
## HeavyJobLock
none held (the check's lock released 16:24:12); no want (re-filed when the captures + BudgetGate are due, after BLENDER's export lock). No background waiters.
