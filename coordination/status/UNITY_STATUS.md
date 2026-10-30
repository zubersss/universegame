# UNITY STATUS
Updated: 2026-10-30 12:30 · Session: 1
## Current task
U-016 Placeholder audio + AudioDirector — next (U-010 waits for U-009 Done; U-016 depends only on U-004).
## Last completed
U-011 Top-down space — d6831d4 — EditMode 88/88, PlayMode 15/15 (+3 tool skips). Layout per Bible §3 (8 planets, Sun R 300 / well 1200 / kill 360, 7 moons R 3–8 with 3R wells, belt 3200–4000 as one mesh); well pull at Earth 4R = 0.999 u/s², Earth ring 11.1, Jupiter ring 28.1; cruise 80 / boost 160 u/s (boost burns fuel); Earth waystation → Mars Atmosphere Ring in 8.04 s by simple autopilot, Mars well felt; Sun kills at 1.2R (hull 0). 16 draw calls measured with ProfilerRecorder on an explicitly rendered frame (capture_space_2026-10-30.png). Fixed: SceneDirector.SetView now hides the outgoing view first (two global 2D lights logged a URP error).
U-009 Player controller — 089657b — EditMode 75/75, PlayMode 13/13 (+2 skips = tool-only captures). Jump height Earth 2.497 m, Mars 6.586 m, Jupiter 0.988 m (all within 0.01% of v₀²/2g; jump starts at v₀ + g·dt/2 so the discrete arc matches the parabola). Walk 4.0 / sprint 6.5 m/s; terminal 50 (Earth) and 20 (Venus) within 1%; real drops 6 / 16.5 / 30 m → 10.6 / 17.9 / 24.1 m/s → health 100 / 51 / 0; Jetpack Mk1 net +4.19 m/s² on Earth, burns 3 s, refills in 2 s; coyote 0.10 s and buffer 0.12 s tested on exact steps. Input map per §6 in code (MeridianInput) and as Settings/Input/MERIDIAN.inputactions. In the game flow: player spawns on PlanetSide, frozen until the ground loads, then stands grounded (capture_earth_player_2026-10-30.png); camera follows, wheel zoom 6–14; mouse aim + left click uses Beam (1) / Builder (4).
U-007 seam fix — 562f0ff — capture at a fractional camera position showed thin lines between tile rows (bilinear sampling read the neighbor sheet cell). Fix: importer slices terrain cells 1 texel inset (126 px), each Tile scales back to 1 m. Lines gone; streaming unchanged (avg 0.30 ms, p99 0.92 ms, 0/400 frames over 2 ms, worst 2.08 ms, D-019 load "none"). A first try with runtime Sprite.Create sprites caused 100–186 ms hitches and was replaced.
U-008 Dig and place — f15f617. U-006 Lit preview — 5a75d90.
## Next up
U-016, U-010, U-019
## Ready for review
U-009 (089657b; plus 562f0ff terrain seam fix under U-007), U-011 (d6831d4)
## Handoffs
→ LEAD: Bible §3/§4.4 conflict: Mercury orbits at 1,150, inside the Sun's well (1,200). The Sun pulls 30.4 u/s² there, more than Mk1 thrust (30), so a Mk1 ship near Mercury can't climb away from the Sun; "a Mk1 ship always escapes any well from outside 1.6R" holds for planets, not the Sun. Needs a numbers decision before M3 (Mercury).
→ LEAD: Bible §4.2 jump table lists Saturn 2.4 m, but its formula v₀²/2g with g 10.44 gives 2.35 m (rounds to 2.3). Code follows the formula; my table test uses 2.35 with a comment. Please correct the table.
→ BLENDER: terrain sheets are sampled 1 texel inside each 128 px cell (the outer texel ring of every cell is never shown). Keep nothing important in that ring.
→ BLENDER: keys are always 3 segments; single-variant assets use `base`. Character sheets at 256 px with 4 px gutters fit 2048 only up to 7 columns.
## Blockers
(none)
## Proposals
P-10: Jetpack engages when jump is held 0.25 s into the air or pressed again while airborne; a tap is only a jump (Bible §6 says tap/hold without a time).
P-11: Boost burns 0.5 main-fuel units per second (Bible: "uses main fuel", no rate). Speed caps clamp total velocity, so wells can't push a ship past 80/160 u/s in M1.
P-12: PlanetDisc is a hand-written HLSL shader (Assets/_Game/Shaders/PlanetDisc.shader), not a .shadergraph: Shader Graph files can't be authored reliably as text by a session. Same features (equirect→sphere, rotation, terminator, rim, self-lit Sun).
P-13: Top-down positions: Earth and Mars share angle 0° so Earth → Mars matches the Bible's ≈ 7 s; other angles fixed in SpaceLayout.cs. Moon g = real surface g.
## For USER_ACTIONS
(none)
## HeavyJobLock
none
