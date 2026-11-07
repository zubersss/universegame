# C2 Mars — U-118 (Mars on the cartoon stage) + U-128 (the datum and the set follow the band) — UNITY hand-off (2026-11-07)

Decisions applied: D-124, D-126, D-135, D-139. Art: B-140 (the Mars rig set, the regolith / basalt strips), B-141 (plains / canyon / storm sets; the plains added 515d28bc), B-142 (the four Mars creature sheets + `props/mars/tube_mound`), B-144 (the six Mars prop sheets).

## What is in (commits 2fd23439, 9e0e4865, 3e66f118, this one)

| Card | What | Evidence |
|---|---|---|
| U-118 | `CartoonStage.Converted`: Earth or Mars. `SceneFor(planet, x)`: Mars by `StageRegions` — the canyon its own set, every other region the plains set; `ParallaxLayers.ConfigureFor` takes a fallback scene (plains → canyon while the plains set was missing; `UsedFallback` says so; it read false once 515d28bc landed). The B-141 storm set as the dust storm's veil: a second `ParallaxLayers` over the base set (`orderOffset` 5), alpha = `StormAlpha(DustStorm.Intensity)` (a smooth step), `scrollX` by the wind. `GroundStrip.KeysFor` / `MaterialFor(planet, tile)`: Mars draws the regolith strip, basalt where the top tile is basalt (hematite / ice / snow read regolith until their strips land). `FloraRigs.BiomeNameAt(Mars, x)`: plains / canyon / polar / highlands from the region (the B-140 vocabulary). D-126: `Species.TubeLurker` (den = `props/mars/tube_mound`: the director places the mound in front at order 6 at the spawn and reuses one within 6 m; `idle` is the peek at the den, `idle_open` away from it, walk / react / bump in the open) over the lava tubes; `Species.PolarCrawler` on the ice caps; the dustskater and scree stalker take their B-142 sheets by key. The hidden 3D stage stays off. | MarsStageTests ×3, MarsStagePlayTests ×2 (the Mars entry at x 64 = the polar cap: scene plains → `backgrounds/mars/plains`, 2/2 strips, the rig set with 42 plants, the veil at alpha 0 while clear; the lurker over the first tube at x 318 with its mound in front); u118/ frames |
| U-128 | `BandDatum`: each band its own datum — Earth's bands by mean surface (`EarthBiomes.MeanSurface`: plains +6, desert +8, taiga +18, tundra +22, the Ocean its water line +1), Mars's landforms by profile (`MarsLandforms.MeanSurface`: the canyon floor −160, the shield's mid slope +110, the cap +4), the spawn's band pinned to the stamped spawn surface (the camp frames do not move), borders blended over ±48 columns as the heights blend. `CartoonStage.FollowBand`: every layer slot and the sky's anchor follow the camera band's datum each frame; at a border the band's set fades in on a second `ParallaxLayers` (0 → 1 over 1.5 s above the base set), then takes the base orders and the old set releases its art. No allocation per frame. | LayerFollowTests (the datum per band, the monotonic border blend, the crossfade), BandFollowPlayTests (x 760: the plains set after one crossfade at datum 326.0; x 2096: the coast set at 322.8 — 16 columns into the band, still blending down from the desert; the water line 321 is reached 48 in); u128/ frames |

## Check (10:18–10:42, four locks; the EditMode re-run 10:43)
compile 0 errors · EditMode 351/353 → 353/353 after two stale asserts of mine (the Maw is no longer the last species; Mars names its regions) · PlayMode A 55/59 (MarsStagePlay ×2, BandFollowPlay's plains leg, HadalMawPlay, ClimbInPlay, HazardV2 on the cartoon path, BudgetGate green; the coast-leg assert fixed to the sampler's blended value; InnerCreature's worst frame 1.56 ms stays the one documented red, U-112's residual) · PlayMode B 62/63, 0 red · M1Loop 1/1. CheckSetup addressed B-142's four creature sheets + the mound and B-144's six prop sheets; the removed v2 models' orphan .meta files are deleted.

## Captures (10:45–10:48)
| Frame | What it shows |
|---|---|
| u128/1_camp | The camp at the datum (337.0), the forest set — unchanged. |
| u128/2_border_mid | The forest → plains border at x 712: the plains set fading in at alpha 0.35 over the forest; datum 329.5 mid-blend. |
| u128/3_plains | After the crossfade: the plains set, crossfades 1. |
| u128/4_shore_coast | The shore at column 2096 with the Maw come in to 14 m: the coast set (dunes, the sea, the stacks) painted at datum 322.2 behind the surveyor — the frame the Maw lacked at B2. **LEAD: passes; U-128 closes.** |
| u118/1_plains_1x | The Mars entry at x 65 — the polar cap region, so the plains set (no fallback), frostcurl ×42 (the polar list's one kind), the Pilgrim. The strip under the plain is the regolith sheet (the print: top tile Snow over Ice, strip material 0; pixel mean (105, 58, 43) on the plains = 0.68 of the sheet under the Mars day light, (52, 45, 42) at the cap — the extra dimming at the cap is open). No dustskater here: it needs regolith and the cap is frost; it stands beside the lurker in 3_lurker_den. Snow / ice take BLENDER.s frost strip (D-143) when it lands. |
| u118/2_canyon_1x | The canyon floor at x 1451 after the border crossfade: the canyon set at datum 160.0 (the floor), the terraces. |
| u118/3_lurker_den | Re-shot 11:19: the lurker peeks (clip idle) at its mound (props/mars/tube_mound in front at order 6) over the first lava tube at x 322, a dustskater beside it on the plains, the surveyor 12 m off (inside 6 m it flees). |
| u118/4_storm_1x | Re-shot 11:19 on the surface: the storm forced to intensity 0.95, the B-141 storm set as the veil at alpha 0.99 (scroll 14.4 m) over the plains set, the lurker in the open. |

## The 13-leg probe (Build/MERIDIAN_0.4.2 rebuilt 10:49, cold cache)
| Row | Value |
|---|---|
| Planet load · Earth at boot | 1.05 s cold (terrain settled at 1.00 s) |
| Planet load · Mars / Mars again | 0.65 s / 0.68 s (the plains set, the storm set, the rig set and the B-144 props still loading at the settle, done 0.02 s after) |
| Memory · Mars | working set 912 MB, private 1257 MB, textures 303 MB; gfx driver 278 MB; textures 332 (303 MB), meshes 133, shaders 57 — flat on Mars again |
| Resident sets · Mars | backgrounds/mars/plains ×7 + storm ×7 (the veil), the four Mars creature sheets, the Space scene's sets, the planets' discs |
| Return · Space after Mars / Earth again | private +8.6 % / +3.6 % — green |
| Creep per visit | 11.2 MB (the four first visits now load Mars's painted sets, the veil, the rig set and the sheets); the second loop 1 MB per visit (+0.2 %), driver / native / textures / shaders / handles flat: a first-visit cost, not a leak |
| Editor gate | green: Frame time · Mars avg 5.74 / p99 11.01 ms, dust storm 4.09 / 7.64, FX peak 6.51 / 11.85; Animated objects · Earth C0 39 |

## Open
- The two re-shoots (one short lock): the polar strip question (with the tile / material print), the lurker at its mound with a dustskater beside it, the storm on the surface.
- Creep per visit 11.2 MB against D-116's 10 from C2: the first-visit cost grew with Mars's art; the second loop says it is not a leak. LEAD's call whether the 10 MB row counts first visits.
