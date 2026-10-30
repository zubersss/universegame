# UNITY STATUS
Updated: 2026-10-30 12:20 · Session: 1
## Current task
U-011 Top-down space — next (U-010 needs the ship prefab; U-011 is independent).
## Last completed
U-009 Player controller — 089657b — EditMode 75/75, PlayMode 13/13 (+2 skips = tool-only captures). Jump height Earth 2.497 m, Mars 6.586 m, Jupiter 0.988 m (all within 0.01% of v₀²/2g; jump starts at v₀ + g·dt/2 so the discrete arc matches the parabola). Walk 4.0 / sprint 6.5 m/s; terminal 50 (Earth) and 20 (Venus) within 1%; real drops 6 / 16.5 / 30 m → 10.6 / 17.9 / 24.1 m/s → health 100 / 51 / 0; Jetpack Mk1 net +4.19 m/s² on Earth, burns 3 s, refills in 2 s; coyote 0.10 s and buffer 0.12 s tested on exact steps. Input map per §6 in code (MeridianInput) and as Settings/Input/MERIDIAN.inputactions. In the game flow: player spawns on PlanetSide, frozen until the ground loads, then stands grounded (capture_earth_player_2026-10-30.png); camera follows, wheel zoom 6–14; mouse aim + left click uses Beam (1) / Builder (4).
U-007 seam fix — 562f0ff — capture at a fractional camera position showed thin lines between tile rows (bilinear sampling read the neighbor sheet cell). Fix: importer slices terrain cells 1 texel inset (126 px), each Tile scales back to 1 m. Lines gone; streaming unchanged (avg 0.30 ms, p99 0.92 ms, 0/400 frames over 2 ms, worst 2.08 ms, D-019 load "none"). A first try with runtime Sprite.Create sprites caused 100–186 ms hitches and was replaced.
U-021 — d185084 — unity_test.ps1 runs MERIDIAN.Tests.LeadQA by default (SmokeTests 1/1), per-assembly lines in the report; Tests/LeadQA.meta committed.
U-008 Dig and place — f15f617. U-006 Lit preview — 5a75d90.
## Next up
U-011, U-016, U-010
## Ready for review
U-007 (2007876 + 015407a D-019 logging + 328c616/562f0ff seam evidence and fix), U-008 (f15f617), U-009 (089657b), U-021 (d185084)
## Handoffs
→ LEAD: Bible §4.2 jump table lists Saturn 2.4 m, but its formula v₀²/2g with g 10.44 gives 2.35 m (rounds to 2.3). Code follows the formula; my table test uses 2.35 with a comment. Please correct the table.
→ LEAD: `Assets/_Game/Tests/LeadQA/*.meta` (inner files) are still untracked; they're yours to commit.
→ BLENDER: terrain sheets are sampled 1 texel inside each 128 px cell (the outer texel ring of every cell is never shown). Keep nothing important in that ring.
→ BLENDER: keys are always 3 segments; single-variant assets use `base`. Character sheets at 256 px with 4 px gutters fit 2048 only up to 7 columns.
## Blockers
(none)
## Proposals
P-09: Rig reach 5 m (Bible silent). Builder places the selected material without an inventory check until inventory exists (M3); drops are pooled physics bodies, max 64 live.
P-10: Jetpack engages when jump is held 0.25 s into the air or pressed again while airborne; a tap is only a jump (Bible §6 says tap/hold without a time).
## For USER_ACTIONS
(none)
## HeavyJobLock
none
