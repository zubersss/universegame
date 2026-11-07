# C2 batch B — UNITY hand-off (2026-11-07)

Cards: U-120 (the cold first boot), U-110 (biome flora + scene sets), U-111 (four ground strips), U-116 (the Sun rig), U-119 (the Hadal Maw as a rig-set creature), U-122 (D-135: layer order, bump flash, suit tiers), the U-115 climb_in follow-up. Decisions applied: D-127, D-129, D-135, D-136.

## Hand-off B1 — the code and its check (commits c0dcc5ca, 5890f35a)

Check 08:33–08:57, four locks: compile 0 errors · EditMode 348/349 · PlayMode A 52/56 · PlayMode B 59/63 · M1Loop 1/1. Fix pass 09:03–09:07: compile 0 errors · EditMode 349/349 · BudgetGate | InnerCreature | SquashPlay | SpaceArt | WardenPlay 7/8 (tests_2026-11-07.md 08:34–09:07).

| Card | What is in | Evidence |
|---|---|---|
| U-120 | `TerrainStreamer.FirstFillPlanMs` 12 ms per frame from `Begin` to the first settle, then the 1 ms streaming budget (`PlanMs(firstFillDone)`); the 0.4.1 cold boot was one 4-row band per frame × 441 steps ≈ 5.7 s behind the cover. | FirstFillTests; **the 0.4.2 probe's boot leg: 1.20 s cold (terrain settled at 1.16 s), 0.53 s warm** (below) |
| U-110 | `RigSet.Plant.biomes` (B-129); `FloraRigs.PlantsFor` / `BiomeNameAt`: each column's kinds from its `EarthBiomes` band (one listed kind is a kind: the desert is all Shiverbarrel; a biome no plant lists takes the whole set); `CartoonStage.SceneFor`: forest / coast / plains from the spawn's band (the camp at x 64 sits in the forest band and now shows the B-133 forest set). D-136 (2): `FloraCount` 48 → 42, `Flora.Reserved` 4 + GullCount. | BiomeFloraTests 3/3; u110/ frames |
| U-111 | `GroundStrip` loads the four B-130 strips (`ground_strip`, `_soil`, `_stone`, `_sand`); a column's material from its top solid tile (grass / soil / stone / sand; snow and dug faces read soil); each sheet's frame-0 bottom 8 px is its fill; a sheet not in yet falls back to the grass strip. | GroundStripTests; the sand strips in u119/ and u122/ |
| U-116 | `SunView` draws `planets/sun/disc_rig` per its json: every part at draw_scale / space_ppu (the 928 px body spans 619 u: 2 × R plus its flame bases), 14 tongues at 0.97 R (291 u) spinning 2°/s with the 12 Hz stepped ± 8 % pulse at 110 bpm, alt scale 1.0 / 0.62, two prominences at 100° / 280° with a slow wobble, the corona at 1.42 R breathing 3 %; unlit. `SpaceWorld.ProbeSunRig` replaces the spheroid where the sheet exists (the glow and the light stay). | SpaceArtRulesTests `TheSunResolvesToItsRigWithPartsAndSockets`; SpaceArtTests (the rig, spheroid fallback); u116/ frames |
| U-119 | `Species.HadalMaw` (rig = true, Water, Hunts with `followDistance` 14 m → holds off and never bumps, `reactRadius` 12 m, 20 m of water needed); `Creature.EnsureRig` builds the RigSet under a flipping pivot centred on the body; the lure's swap cycle on the beat (lit 6 / dim 2); the `jaw_open` react eases the jaw to −24° and tilts the rig 4° with the lure flare. RigSet v3.2: `idle.cycle_beats` (a swing per N beats; the whole sway 2 N beats), `lag` (radians per bone depth, default 0.35 = the old whip), `amplitude_deg` as a bone → degrees object, the react `swap` object → `also`, `jaw_deg` / `head_deg`. RigSetBuilder: the sway clip over 2 × cycle_beats beats (the Maw: 4.36 s), per-bone amplitudes whole, a still bone gets no curve (the jaw is the react's). | HadalMawTests ×3; HadalMawPlayTests (rig at column 2124, jaw 24° open inside 12 m, 0 bumps); u119/ frames |
| U-122 | (a) `ParallaxLayers.FollowY`: the layers follow the camera from the anchor up and hold the datum pose below it — no crossing at any depth; (b) the 2-frame over-white flash on `SpriteCharacterView` (SquashPlayTests asserts it on both paths); (c) Envirosuit tiers as a tint + badge on the pack (`SetSuitTier` on `HazardSystem.SuitEquipped`; Mk1 faint cool / Mk2 steel / Mk3 gold), HazardV2PlayTests on the cartoon path. | LayerFollowTests; HazardV2PlayTests green on the cartoon path; u122/ frames |
| U-115 f/u | `ShipBoarding.TryBoard` climbs the drawn surveyor to the legs rig's `door` socket over the climb_in clip before the player object goes away; a lift-off or an exit cuts it short. | ClimbInPlayTests (door (74.5, 339.7), root rises, object away after) |
| Creatures | The first think is staggered by serial (a pack spawned in one frame never thinks in one frame again). | InnerCreature worst 2.86 → 1.45 / 3.23 ms (one frame; median 0.034, p99 0.084–0.118) |

The five reds of the first check and their fixes (fix pass, all green): BiomeFlora's one-kind rule; SpaceArtTests to the rig; the wolf knock read after a fixed step (vx −6.67); animated objects 42 → 39 (flora full rate 35, cheap idle 7, plants 42; the hidden 3D / sheet views' Animators off on the cartoon path); Warden worst 0.094 ms on the re-run. InnerCreature stays one frame over 1.0 ms (3.23 ms: 20 ticks under a GC pause, gen0 ~38/s) — U-112's hunt per D-136 (4).

## Hand-off B2 — the captures and the 0.4.2 probe (09:07–09:32)

### Captures (1080p, the side camera at 1x; the Space camera for the Sun)
| Folder | Frame | What it shows |
|---|---|---|
| u122/ | 1_datum, 2_pool_minus15, 3_minus40 | The camera at the datum, 15 m and 40 m under it over the pool west of the camp: layer tops 351.0 / 346.0 / 342.5 (sky over hills over near) at all three heights — the layers hold their datum pose under the anchor (the swimmers' frame at −9 m had the hills over the sky). Under the datum the frame is the pool bed in sand strips and the sky colour: the painting sits above the frame, as it should. |
| u110/ | 1_camp_forest, 2_plains, 3_coast | The camp as its band paints it: x 64 is the forest band → the B-133 forest set, curlfrond ×17 + nodbell ×25 (42 plants, every kind on the forest list); then the plains and coast sets on the same camp (3 layers each, no placeholders). |
| u116/ | 1_sun, 2_sun_earth_mars | The Sun rig close (R 300 u: body 619 u, 14 tongues at 291 u alternating 1.0 / 0.62, two prominences, the corona at scale 109.6 = 1.42 R, the glow behind, stepped at 12 Hz); then the Sun, Earth (R 25) and Mars (R 17) in one frame at one scale. |
| u119/ | 1_shore, 2_maw_1x, 3_react | The ocean band's shore (columns 2080+; shore 2096, 20 m of water at 2124): the surveyor on the sand, the Maw come in to hold 14 m off (state Chase, at x 2111), a shark beside it; the Maw at 1x (a set piece over two screens); the react with the surveyor inside 12 m: jaw 24° open, 0 bumps. **The lure read "none"** in this run: RigBuild makes no renderer for a `replaces_part` slot (the bone's part is the slot), so the swap cycle and the flare never found it — fixed in the tree (`Creature.RigSlotRenderer`), its check and the re-shoot of 3_react queued for the next lock. |

### The 0.4.2 build and the 11-leg probe (Build/MERIDIAN_0.4.2, built 09:16, probed on a cold cache right after)
| Row | 0.4.1 (07:42) | 0.4.2 (09:2x) |
|---|---|---|
| Planet load · Earth at boot | 5.69 s (terrain settled at 5.69 s) | **1.20 s** (scene load 124 ms, tile sheets 784 ms, terrain settled at 1.16 s) — green, U-120's acceptance (≤ 5 s cold) |
| Planet load · Earth (warm) | — | 0.53 s (terrain settled at 0.51 s) |
| Planet load · Mars / Mercury / Venus / Earth again | — | 0.73 / 0.70 / 0.75 / 0.77 s |
| Transition rows (dev build) | quoted per D-136 | Space 0.73, Earth (warm) 0.78, Mars 0.78, Mercury 1.00, Venus 1.03, Earth again 0.78 s — all green (≤ 1.5 s) |
| Return · Space after Mars / Earth again | +7 % / … | private +11.5 % / +10.6 % — red against 10 % (D-116) |
| Creep per visit | — | 31.8 MB per visit (private 1200 → 1327 MB); per visit mono 0.2 MB, native allocated 0.2 MB, reserved 0.5 MB, handles 0, objects 0 → the growth is outside Mono and the native allocator: U-112's remainder (the bundle / graphics side) |
| Boot → warm · Earth | — | working set +1 MB, private +14 MB — green |
| Film pass GPU · Earth | — | −0.3 ms at 1080p — green |

Editor gate of the same run: RED on `Transition · entry` 1.52 s (the Editor row D-136 (2) makes info — now an Info row in BudgetGateTests, in the tree) and `Frame time · Mars FX peak` avg 11.01 / p99 21.20 ms (the first Editor run after a fresh build: shader compilation lands in the FX peak; 05:1x read p99 13.08 — re-measured at the next gate). The 0.4.1 numbers in perf_2026-11-07.md's dev-build section were replaced by this run's (the section is rewritten per run; the 0.4.1 rows stay in the c1 README).

### Open after B2
- U-119: the lure swap check + the 3_react re-shoot (next lock, ~5 min).
- InnerCreature's worst frame (one GC pause in the tick, 1.45–3.23 ms) and the private creep 31.8 MB per visit → U-112.
- The Editor Mars FX peak p99 after a fresh build → the next gate.
