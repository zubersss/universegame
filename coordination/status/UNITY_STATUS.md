# UNITY STATUS
Updated: 2026-10-30 13:10 · Session: 1
## Current task
U-010 Side-view ship — next (U-009 is Done).
## Last completed
U-019 Sprite_LitEmissive — 42988db — EditMode 96/96, PlayMode 18/18 (+3 tool skips). Hand-written HLSL (D-023) based on URP 17.6 Sprite-Lit-Default: lit + normal map, plus additive _EmissionMap × intensity in the lit and unlit passes. ArtImporter keeps Settings/Resources/ArtMaterials.asset: every key whose addressed color file has an _emission sibling draws with Sprite_LitEmissive (EditMode tests on a sandbox registry and on the real one); AddressableSprite, PlayerView and the preview tool use it. Previews with the point light OFF (reports/unity/preview_*_nopoint_2026-10-30.png): calibration stripe brightest pixel 255,169,62 (emission 255,160,40 + albedo under the 0.25 global light); Pilgrim portholes, engine ring, lift vents and nav lights glow on a dim hull; Sun surface fully self-lit.
U-022 Top-down follow-ups — 4fded11 — Sun k_sun 0.80 (D-022): 14.9 u/s² at r 1150, 30 at r 810 (EditMode); Mk1 ship at Mercury's ring thrusting outward reaches r 1300 in 4.04 s (PlayMode); backgrounds/space/layer0..2 as parallax quads + planets/*/glow behind discs (2.56 R, Sun 3.2 R, only where art exists); 24 draw calls; capture_space_2026-10-30.png shows stars, Milky Way band and Earth's glow.
U-016 Placeholder audio — 37f9ed9 — EditMode 93/93, PlayMode 17/17 (+3 tool skips), LeadQA 1/1. Seven clips synthesized by AudioSynth.cs (original work, CC0 1.0, no downloads): jump, land, dig, place, thrust loop, ui_click, 20 s wind ambient loop; Vorbis, SFX compressed in memory, ambient streamed; 1.9 MB total; seamless loops. AudioDirector in Core: 8 pooled voices; plays jump/land (≥ 2 m/s)/dig/place from gameplay events, thrust loop while the top-down ship thrusts, ambient from boot. One AudioListener lives in Core (view cameras have none), which fixed a "no audio listeners" log during loading. Credits: docs/credits/unity.md.
U-011 Top-down space — d6831d4 — EditMode 88/88, PlayMode 15/15 (+3 tool skips). Layout per Bible §3 (8 planets, Sun R 300 / well 1200 / kill 360, 7 moons R 3–8 with 3R wells, belt 3200–4000 as one mesh); well pull at Earth 4R = 0.999 u/s², Earth ring 11.1, Jupiter ring 28.1; cruise 80 / boost 160 u/s (boost burns fuel); Earth waystation → Mars Atmosphere Ring in 8.04 s by simple autopilot, Mars well felt; Sun kills at 1.2R (hull 0). 16 draw calls measured with ProfilerRecorder on an explicitly rendered frame (capture_space_2026-10-30.png). Fixed: SceneDirector.SetView now hides the outgoing view first (two global 2D lights logged a URP error).
U-009 Player controller — 089657b — EditMode 75/75, PlayMode 13/13 (+2 skips = tool-only captures). Jump height Earth 2.497 m, Mars 6.586 m, Jupiter 0.988 m (all within 0.01% of v₀²/2g; jump starts at v₀ + g·dt/2 so the discrete arc matches the parabola). Walk 4.0 / sprint 6.5 m/s; terminal 50 (Earth) and 20 (Venus) within 1%; real drops 6 / 16.5 / 30 m → 10.6 / 17.9 / 24.1 m/s → health 100 / 51 / 0; Jetpack Mk1 net +4.19 m/s² on Earth, burns 3 s, refills in 2 s; coyote 0.10 s and buffer 0.12 s tested on exact steps. Input map per §6 in code (MeridianInput) and as Settings/Input/MERIDIAN.inputactions. In the game flow: player spawns on PlanetSide, frozen until the ground loads, then stands grounded (capture_earth_player_2026-10-30.png); camera follows, wheel zoom 6–14; mouse aim + left click uses Beam (1) / Builder (4).
U-007 seam fix — 562f0ff — capture at a fractional camera position showed thin lines between tile rows (bilinear sampling read the neighbor sheet cell). Fix: importer slices terrain cells 1 texel inset (126 px), each Tile scales back to 1 m. Lines gone; streaming unchanged (avg 0.30 ms, p99 0.92 ms, 0/400 frames over 2 ms, worst 2.08 ms, D-019 load "none"). A first try with runtime Sprite.Create sprites caused 100–186 ms hitches and was replaced.
U-008 Dig and place — f15f617. U-006 Lit preview — 5a75d90.
## Next up
U-010, U-020, U-012
## Ready for review
U-016 (37f9ed9), U-022 (4fded11), U-019 (42988db)
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
