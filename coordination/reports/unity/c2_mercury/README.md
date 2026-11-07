# C2 Mercury — U-123 (Mercury on the cartoon stage) — UNITY hand-off (2026-11-07 14:5x: ready for review with U-131)

Decisions applied: D-146 (the camp on the plain; the band datum from the generator's surface), D-118 (the climb sky on the cartoon path), D-124 / D-133 (no 3D-path Mercury test left to retire), D-126 (den species), D-130 (the Mercury palette). Art: B-148 (the Mercury rig set, the regolith / slate strips), B-149 (the day / twilight / night sets), B-150 (the four creature sheets + `props/mercury/ice_burrow`) — exported after the code (D-119's order: the code binds by key the moment they land).

## What is in (commits 6aff1d38, 6aa8e018, 4d531e8b, 1e4c3915, 9a6e31d5, 228687c0, 9b213611; the Mars close 6227cc34 moved every planet's strips in front of the block faces)

| Piece | Rule | Where |
|---|---|---|
| The planet | `CartoonStage.Converted`: Earth, Mars, Mercury. The 3D stage, depth bands and backdrop (its Sun sprite with it) are off; the climb sky runs from the ink-black top (`PlanetBackdrop.SkyColor(Mercury)`). | CartoonStage |
| The set | `MercurySceneFor(x, clock, width)`: the terminator's zone at the camera column — `day`, `twilight`, `night` (`backgrounds/mercury/<scene>`); a cold trap paints the night set on either side (permanent shadow); the twilight set stands in for a set not exported yet. The band creeps 1 m per 6 s, so the set changes through U-128's FollowBand crossfade (1.5 s) as it passes the camera. The stage's clock is `MercuryClock` = the terminator's real seconds + the hazards' offset — the clock the creatures and the flares read, so the painted band is theirs. | CartoonStage |
| The strips | `GroundStrip.MercuryKeys`: `terrain/mercury/ground_strip` (the blinding regolith), `terrain/mercury/ground_strip_slate` (the shadow kind). `MercuryStripFor`: slate in the night zone and on a cold-trap floor, regolith in the sun — a clocked per-column rule (`materialRule`), laid out again whenever the dawn column moves (`Invalidate`; ~35 columns, no allocation). D-146: the fill tile under every strip (all planets) is one texel in from its frame's sides at a PPU that keeps it 1 m — the sheets' 4 px gutters are transparent and the full-width tile bled into them under bilinear filtering (the 13:08 night frame's 64 px seams; the art's bottom rows are clean). | GroundStrip |
| The plants | `FloraRigs.MercuryBiomeFor`: `day` / `twilight` / `night` by the zone when the plants are placed, `polar` in a cold trap (`biomeRule`); they stay where they grew as the band creeps. B-148's rigset lists: sunfan day, embercap day, glassreed twilight, shadebloom night + polar, coilwort polar. | FloraRigs |
| The ground and the datum | D-146: no seeded small crater reaches within ±40 columns of the pad (`MercuryLandforms.ReachesPad`; the 13:08 frames had the camp in a ~9 m bowl at 310 under the 320 ± 14 plain, the sets 10 m low behind the plain). `BandDatum` (Mercury) takes the generator's own surface without the small craters (`SolidWorldGenerator.BandSurfaceHeight`: the noise and the cold-trap bowls): the plain is one band at that surface by the spawn column (any bowl taken out, so an entry into a small crater or a trap keeps the plain's datum); a cold trap takes it per column, blended in from the rim over 48 columns, so the night set meets the trap's floor (it hung ~3 m over it on the nominal bowl). | BandDatum, MercuryLandforms, SolidWorldGenerator |
| The creatures | The Shadewyrm is a den species: `den = props/mercury/ice_burrow` (D-126) — it spawns at its burrow, `idle` is the peek behind it (the prop draws in front at order 6), `idle_open` in the open; its temper stays Hunts until a decision says otherwise (B-145 re-inks it shy). The Flarewing flies (`Habitat.Air`, fly at index 1); the Glassback and Cinderling take their sheets by key (`replaces_v2`). The Cinderhulk stays a model (its rig set is B-145 §4's last item). | CreatureSpecies |
| Before the art | Every Mercury key is probed, never loaded blind: until B-149 lands the backdrop is the placeholder tints, until B-148 no strip draws and no plant grows, until B-150 the burrow is an empty renderer — no error is logged (MercuryEntryTests' LogAssert holds). Build 0.4.3 (D-144) predates the conversion. | — |

## Tests
- EditMode: `MercuryStageTests` ×3 — the set by zone, by creep and in a cold trap on the day side; the strip rule, the biome names and the datum (the pad, the plain, the bowl, no step at the rim); the den species and the flier. `MarsStageTests`: Venus is the planet that waits now.
- PlayMode: `MercuryStagePlayTests` ×1 — a Mercury entry on the cartoon path, the set by the spawn's zone, the plain's datum, no placeholder / strip / plant assert until the art is on disk (then they bite), the clock moved to midnight (the night set after the crossfade, the slate rule) and to noon (the day set, the regolith), two crossfades, no unexpected log.
- EditMode (D-146): `MercuryStageTests.TheCampSitsOnThePlainAndTheBandsFollowTheGeneratorsSurface` (the pad clear for 60 seeds and the plain still pocked, the datum rules through a band surface, the real generator), `GroundStripTests.TheFillTileStaysInsideItsFrameAndSpansOneColumn`; PlayMode: MercuryStagePlay's datum is the ground at the pad (± 2 m).
- Capture: `CaptureU123Mercury` → `u123/1_day_1x` (the camp at noon with a Glassback — spawned on the band, its rule, before the clock turns; the plants grown again after the noon turn, the day kinds), `2_twilight_1x` (the dawn line at the camp, a Flarewing over the surveyor, the twilight kinds grown again), `3_night_burrow` (the first cold trap's floor, the Shadewyrm peeking from its burrow — the wait takes the director's Idle at the den with ≥ 0.8 s of its wander window left — six polar plants on its left).

## Check
- EditMode 356/356 (12:01, the code as committed; the 12:02 PlayMode leg ran the whole suite bare into the 20-minute cap: exit 124, no results — D-122 slices since).
- **Lock 1 (12:53:52–12:59:17, one `unity_check` call, 5.4 min): compile 0 errors / 0 warnings; CheckSetup imported B-148 / B-149 / B-150** (34 sheet animators and 5 rig sets rebuilt; the 47 Mercury `.meta` files and the v2 models' 16 orphans in 4d531e8b). The four creature sheets re-sliced from their json (Glassback 52, Cinderling 50, Flarewing 52, Shadewyrm 50 frames); the 48 "rect lies outside of texture" lines in the import log are each colour sheet's old v2 `.meta` (24 rects) on the first import, gone after the re-slice.
- **PlayMode slice 16/16** (`MercuryStagePlay|MercuryEntry|MarsStagePlay|InnerCreature|HazardV2Play|Solarite|WardenPlay|BudgetGate|Transition|BandFollowPlay`): the entry at x 64 is in the Twilight zone → `backgrounds/mercury/twilight` (no fallback, the set on disk), strips 2/2, the rig set 42 plants, datum 310.0; the creep leg 2 crossfades → `backgrounds/mercury/day`, the camp's strip regolith; MercuryEntry 0.81 s; 20 Mercury creatures' AI median 0.035 / p99 0.122 / max 0.207 ms; Warden p99 0.013 ms; the editor BudgetGate (Earth / Space / Mars) green; Transition ×2, BandFollow, MarsStage ×2, HazardV2 ×3, Solarite green.
- Lock 2 (13:04–13:09): compile 0 / 0; LeadQA M3Inner 5/7 with one red in LEAD's file (Step4's Venus deck from the pre-D-124 pixel rows; LEAD fixed it, e201d1e1); CaptureU123Mercury 13:08 drew all the Mercury art but missed B-145 (above) → D-146; the rest of lock 2 was stopped before it ran.
- Lock 3 (13:2x) was stopped for low memory at ~13:25 (EditMode 358/358 done, the PlayMode slice cut). The one re-run (D-046, the owner's yes at 13:3x) went as short foreground locks, each released between:
  1. **13:39–13:43 PlayMode 23/23** = the Mercury slice 16/16 + LeadQA M3Inner 7/7 (LEAD's Step4 fix): D-146 in play, the pad's ground 317.0 = the datum 317.0 (was the 310 crater floor); MercuryEntry 0.81 s; 20-creature AI p99 0.165 ms.
  2. CaptureU123Mercury 13:45–13:47 against BLENDER's D-147 straight-alpha sets: LEAD passed the three scenes (cycle 271), but the strip fill showed horizontal lines (at the 1 m PPU the fill tile left whole pixels and its bottom edge sampled the sheet's transparent top row) → 9a6e31d5 (rows 1–6); re-shot 13:49–13:51 and again 14:04–14:06 on B-165's first gutter export: the fill flat.
  3. CaptureU118Mars 13:54–13:56 on the B-162 straight Mars sets; CaptureU110Scenes 13:58–13:59 on the B-162 Earth sets + the B-165 strips, all at 16:9 (LEAD read them, cycle 271 14:1x).
  4. **BudgetGate 14:07–14:08 green** (every Editor row; perf_2026-11-07.md): Earth avg 6.42 / p99 14.44 ms, 131 draw calls; Space 3.10 / 5.72 ms; Mars 4.61 / 8.13; dust storm 4.60 / 7.82; FX peak 5.15 / 10.72; launch 0.89 s; chunk streaming p99 1.16 ms, 0/400 over 2 ms; Mars entry 1.35 s (Editor, info); GC 0 B per 300 frames everywhere.
  5. P-48 (LEAD yes): the strip sheets import Repeat in u, Clamp in v (228687c0; with Repeat in v each frame's bottom row sampled the sheet's transparent top row: a faint line 2 m under every ground line). B-165's RGBA gutter re-export (e0f476c7, 14:10) re-imported with it at the build; the nine metas at wrapV 1 in 9b213611.
  6. **Build/MERIDIAN_0.4.4 (development) BUILD OK 14:15, 550 MB, 75 s**: the Mercury code + D-146 + the fill fix + P-48 + the RGBA strips. A dev build; Build/MERIDIAN_0.4.3 stays the owner's (D-144).
  7. **One lock 14:51:06–14:55:25 (4.3 min, after BLENDER's Uranus slot): the 13-leg probe on 0.4.4 — BUILD MEMORY GREEN** (below) — and CaptureU123Mercury for U-131 (the three frames in u123/ re-shot 14:55 on the RGBA strips with P-48; the capture compiled the tree with U-102 in it: clean).

## The 13-leg probe (Build/MERIDIAN_0.4.4, development, 14:51–14:52; the 0.4.3 run of 11:40 in brackets)
| Row | Value |
|---|---|
| Planet load · Mercury | 0.75 s (tile sheets 221 ms; terrain settled 0.71 s; the rig set, strips and props done 0.04 s after) [0.75 s on the 3D path] — green |
| Memory · Mercury | working set 922 MB, private 1256 MB, textures 315 MB, meshes 4 MB [935 / 1260 / 319] — the cartoon path costs no more than the 3D one; handles 50 own, 155 held |
| Transition · Mercury entry | 1.01 s, worst iris-in frame 33.3 ms — green |
| Return · Space after Mercury | private 1203 MB vs the first Space 1092; planet_mercury handles 0 after 0.0 s — released |
| Planet load · Earth at boot / warm / again / again 2 | 1.51 s cold (tile sheets 1099 ms) / 0.75 / 0.76 / 0.64 s [1.37 cold] — green |
| Planet load · Mars / Mars again / Venus | 0.63 / 0.67 / 0.72 s — green |
| Memory, every leg | working set 772–954 MB, private 1092–1282 MB, textures ≤ 324 MB (Venus) — green |
| Return · Space after Mars / Earth again | private +8.9 % / +2.3 % [+8.6 / +2.6] — green |
| Boot → warm · Earth | working set +56 MB, private +60 MB (≤ 150) — green |
| First-visit cost per planet (D-143, info) | 7.2 MB per planet [8] |
| **Creep per visit (the second loop, ≤ 10 MB)** | **7 MB per visit (+1.1 %) [7.5] — green**. Per visit the Mono heap 0 MB (used 0), native allocated 0, native reserved 0, gfx driver 0, textures / meshes / shaders / handles 0: no Unity-side counter grows, so the 7 MB is process commit outside Unity's allocators and the Mono heap (the driver or the OS). A watch row: it held at 7–7.5 over 0.4.3 and 0.4.4. |
| Film pass GPU · Earth | on 11.04 ms, off 11.15 ms: the pass costs nothing measurable at 1080p — green |
| Mip streaming | active, 512 MB budget — green |

## U-131: the 64 px strip joins on the RGBA re-export (B-165 e0f476c7 + P-48)
The night frame's strip band (y 790–860, x 740–1430): each column's brightness against the mean of its ±2..4 neighbours, folded by x mod 64 (a join repeats at one phase, the drawing does not).
- 14:06 frame (B-165's first export, colour-only gutters at alpha 0): the join phase (x ≡ 12) dips **10.9 levels on average, 12.8 at most**, at 10 of its 11 columns (x 780, 844, 908 … 1356); every other phase averages −0.1.
- **14:55 frame (RGBA gutters + Clamp in v): no phase repeats a dip.** The worst phase (x ≡ 60) averages 1.8; its three 6.3 columns (x 764, 956, 1276) are the drawing itself (764 and 1276 are one strip period, 512 px, apart), the other eight read −1.3..2.0. The band reads continuous at 2× (scratch crop), and the fill below it is flat. → B-165's joins are gone.

## Captures (u123/, re-shot 14:55 on the RGBA strips; the 14:04–14:06 takes LEAD passed are in 9b213611; 1920×1080)
| Frame | What it shows | LEAD |
|---|---|---|
| 1_day_1x | The camp on the plain at noon under the huge low Sun, a Glassback, embercap ×24 + sunfan ×18; the regolith strip, the fill flat | passes (cycle 271) |
| 2_twilight_1x | The dawn line at the camp, the half-set Sun under the violet band, a Flarewing over the surveyor, glassreed ×42 | passes |
| 3_night_burrow | The first cold trap: the night set meeting the trap's floor at datum 279, the Shadewyrm peeking from its burrow, coilwort ×4 + shadebloom ×2; the slate strip, continuous (U-131) | passes; joins gone (U-131) |

## Open
- The Shadewyrm's temper (Hunts in the table, shy in B-145's re-ink list) — a decision if LEAD wants it changed.
- The Cinderling swarm "at dawn" is the spawner's rule already (local time 0.15–0.35); nothing changes on the cartoon path.
