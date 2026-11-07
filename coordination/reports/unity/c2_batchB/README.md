# C2 batch B — UNITY hand-off (2026-11-07)

Cards: U-120 (the cold first boot), U-110 (biome flora + scene sets), U-111 (four ground strips), U-116 (the Sun rig), U-119 (the Hadal Maw as a rig-set creature), U-122 (D-135: layer order, bump flash, suit tiers), the U-115 climb_in follow-up. Decisions applied: D-127, D-129, D-135, D-136.

## Hand-off B1 — the code and its check (commit c0dcc5ca, 09:0x)

Check 08:33–08:57, four locks: compile 0 errors · EditMode 348/349 · PlayMode A 52/56 · PlayMode B 59/63 · M1Loop 1/1 (tests_2026-11-07.md 08:34–08:57).

| Card | What is in | Evidence |
|---|---|---|
| U-120 | `TerrainStreamer.FirstFillPlanMs` 12 ms per frame from `Begin` to the first settle, then the 1 ms streaming budget (`PlanMs(firstFillDone)`); the 0.4.1 cold boot was one 4-row band per frame × 441 steps ≈ 5.7 s behind the cover. | FirstFillTests; the boot row from the B2 probe (`terrain settled at … s`) |
| U-110 | `RigSet.Plant.biomes` (B-129); `FloraRigs.PlantsFor` / `BiomeNameAt`: each column's kinds from its `EarthBiomes` band (one listed kind is a kind: the desert is all Shiverbarrel; a biome no plant lists takes the whole set); `CartoonStage.SceneFor`: forest / coast / plains from the spawn's band (the camp at x 64 sits in the forest band and now shows the B-133 forest set). D-136 (2): `FloraCount` 48 → 42, `Flora.Reserved` 4 + GullCount. | BiomeFloraTests (one-kind rule in the fix pass); CaptureU110Scenes (B2) |
| U-111 | `GroundStrip` loads the four B-130 strips (`ground_strip`, `_soil`, `_stone`, `_sand`); a column's material from its top solid tile (grass / soil / stone / sand; snow and dug faces read soil); each sheet's frame-0 bottom 8 px is its fill; a sheet not in yet falls back to the grass strip. | GroundStripTests; the coast frames (B2) |
| U-116 | `SunView` draws `planets/sun/disc_rig` per its json: every part at draw_scale / space_ppu (the 928 px body spans 2 × R and its flame bases), 14 tongues at 0.97 R spinning 2°/s with the 12 Hz stepped ± 8 % pulse at 110 bpm, alt scale 1.0 / 0.62, two prominences at 100° / 280° with a slow wobble, the corona at 1.42 R breathing 3 %; unlit. `SpaceWorld.ProbeSunRig` replaces the spheroid where the sheet exists (the glow and the light stay). | SpaceArtRulesTests `TheSunResolvesToItsRigWithPartsAndSockets`; SpaceArtTests (rewritten to the rig, fix pass); CaptureU116Sun (B2) |
| U-119 | `Species.HadalMaw` (rig = true, Water, Hunts with `followDistance` 14 m → holds off and never bumps, `reactRadius` 12 m, 20 m of water needed); `Creature.EnsureRig` builds the RigSet under a flipping pivot centred on the body, the lure's swap cycle on the beat (lit 6 / dim 2), the `jaw_open` react eases the jaw to −24° and tilts the rig 4° with the lure flare. RigSet v3.2: `idle.cycle_beats` (a swing per N beats; the whole sway 2 N beats), `lag` (radians per bone depth, default 0.35 = the old whip), `amplitude_deg` as a bone → degrees object, the react `swap` object → `also`, `jaw_deg` / `head_deg`. RigSetBuilder: the sway clip over 2 × cycle_beats beats (the Maw: 4.36 s), per-bone amplitudes whole, a still bone gets no curve (the jaw is the react's). | HadalMawTests ×3; HadalMawPlayTests (rig at column 2124, jaw 24° open inside 12 m, 0 bumps); CaptureU119Maw (B2) |
| U-122 | (a) `ParallaxLayers.FollowY`: the layers follow the camera from the anchor up and hold the datum pose below it — no crossing at any depth; (b) the 2-frame over-white flash on `SpriteCharacterView` (SquashPlayTests asserts it on both paths); (c) Envirosuit tiers as a tint + badge on the pack (`SetSuitTier` on `HazardSystem.SuitEquipped`; Mk1 faint cool / Mk2 steel / Mk3 gold), HazardV2PlayTests on the cartoon path. | LayerFollowTests; HazardV2PlayTests green on the cartoon path; CaptureU122Pool (B2) |
| U-115 f/u | `ShipBoarding.TryBoard` climbs the drawn surveyor to the legs rig's `door` socket over the climb_in clip (0.75 s stand-in when the sheet has none) before the player object goes away; a lift-off or an exit cuts it short. | ClimbInPlayTests (door (74.5, 339.7), root rises, object away after) |
| Creatures | The first think is staggered by serial (a pack spawned in one frame never thinks in one frame again). | InnerCreature worst 2.86 → 1.45 ms; median 0.034, p99 0.084 |

### The five reds of the first check and their fixes (fix pass)
1. BiomeFlora desert picked Nodbell — my rule fell back to the whole set for a biome with one listed kind. Now one listed kind wins.
2. SpaceArtTests expected the Sun's spheroid — rewritten to the rig (14 tongues, 2 prominences, the corona), spheroid fallback when the sheet is missing.
3. The wolf knock read 0.00 one frame after the bump (flash true, clip bump): the knock velocity lands in the next fixed step; the assert now follows a `WaitForFixedUpdate`.
4. Animated objects 42 = 38 flora + 4 non-flora (the drawn surveyor, the ship legs rig, its puff sheet, one more): D-136 (2) — FloraCount 42, Reserved 4 + GullCount (35 full rate → 39), the hidden 3D / sheet views' Animators off on the cartoon path.
5. Warden worst 0.693 vs 0.6 ms: a single frame; re-run.

InnerCreature stays one frame over 1.0 ms (1.45 ms: 20 ticks, GC gen0 ~38/s) — U-112's hunt per D-136 (4).

## Hand-off B2 — the fix pass, the captures and the probe
(filled after the B2 lock)
