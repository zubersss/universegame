# C2 Mercury — U-123 (Mercury on the cartoon stage) — UNITY hand-off (2026-11-07, in progress)

Decisions applied: D-118 (the climb sky on the cartoon path), D-124 / D-133 (no 3D-path Mercury test left to retire), D-126 (den species), D-130 (the Mercury palette). Art: B-148 (the Mercury rig set, the regolith / slate strips), B-149 (the day / twilight / night sets), B-150 (the four creature sheets + `props/mercury/ice_burrow`) — exported after the code (D-119's order: the code binds by key the moment they land).

## What is in (commits 6aff1d38, 6aa8e018, 4d531e8b; the Mars close 6227cc34 moved every planet's strips in front of the block faces)

| Piece | Rule | Where |
|---|---|---|
| The planet | `CartoonStage.Converted`: Earth, Mars, Mercury. The 3D stage, depth bands and backdrop (its Sun sprite with it) are off; the climb sky runs from the ink-black top (`PlanetBackdrop.SkyColor(Mercury)`). | CartoonStage |
| The set | `MercurySceneFor(x, clock, width)`: the terminator's zone at the camera column — `day`, `twilight`, `night` (`backgrounds/mercury/<scene>`); a cold trap paints the night set on either side (permanent shadow); the twilight set stands in for a set not exported yet. The band creeps 1 m per 6 s, so the set changes through U-128's FollowBand crossfade (1.5 s) as it passes the camera. The stage's clock is `MercuryClock` = the terminator's real seconds + the hazards' offset — the clock the creatures and the flares read, so the painted band is theirs. | CartoonStage |
| The strips | `GroundStrip.MercuryKeys`: `terrain/mercury/ground_strip` (the blinding regolith), `terrain/mercury/ground_strip_slate` (the shadow kind). `MercuryStripFor`: slate in the night zone and on a cold-trap floor, regolith in the sun — a clocked per-column rule (`materialRule`), laid out again whenever the dawn column moves (`Invalidate`; ~35 columns, no allocation). | GroundStrip |
| The plants | `FloraRigs.MercuryBiomeFor`: `day` / `twilight` / `night` by the zone when the plants are placed, `polar` in a cold trap (`biomeRule`); they stay where they grew as the band creeps. B-148's rigset lists: sunfan day, embercap day, glassreed twilight, shadebloom night + polar, coilwort polar. | FloraRigs |
| The datum | `BandDatum` (Mercury): the plain is one band at the pad's measured surface; a cold trap follows its bowl (`MercuryLandforms.ColdTrapProfile`, datum − 36 at the centre) from the rim in, blended over 48 columns — the stage drops into the crater with the ground. | BandDatum, MercuryLandforms |
| The creatures | The Shadewyrm is a den species: `den = props/mercury/ice_burrow` (D-126) — it spawns at its burrow, `idle` is the peek behind it (the prop draws in front at order 6), `idle_open` in the open; its temper stays Hunts until a decision says otherwise (B-145 re-inks it shy). The Flarewing flies (`Habitat.Air`, fly at index 1); the Glassback and Cinderling take their sheets by key (`replaces_v2`). The Cinderhulk stays a model (its rig set is B-145 §4's last item). | CreatureSpecies |
| Before the art | Every Mercury key is probed, never loaded blind: until B-149 lands the backdrop is the placeholder tints, until B-148 no strip draws and no plant grows, until B-150 the burrow is an empty renderer — no error is logged (MercuryEntryTests' LogAssert holds). Build 0.4.3 (D-144) predates the conversion. | — |

## Tests
- EditMode: `MercuryStageTests` ×3 — the set by zone, by creep and in a cold trap on the day side; the strip rule, the biome names and the datum (the pad, the plain, the bowl, no step at the rim); the den species and the flier. `MarsStageTests`: Venus is the planet that waits now.
- PlayMode: `MercuryStagePlayTests` ×1 — a Mercury entry on the cartoon path, the set by the spawn's zone, the plain's datum, no placeholder / strip / plant assert until the art is on disk (then they bite), the clock moved to midnight (the night set after the crossfade, the slate rule) and to noon (the day set, the regolith), two crossfades, no unexpected log.
- Capture: `CaptureU123Mercury` → `u123/1_day_1x` (the camp at noon with the plants and a Glassback — spawned on the band, its rule, before the clock turns), `2_twilight_1x` (the dawn line at the camp, a Flarewing over the surveyor), `3_night_burrow` (the first cold trap's floor, the Shadewyrm peeking from its burrow).

## Check
- EditMode 356/356 (12:01, the code as committed; the 12:02 PlayMode leg ran the whole suite bare into the 20-minute cap: exit 124, no results — D-122 slices since).
- **Lock 1 (12:53:52–12:59:17, one `unity_check` call, 5.4 min): compile 0 errors / 0 warnings; CheckSetup imported B-148 / B-149 / B-150** (34 sheet animators and 5 rig sets rebuilt; the 47 Mercury `.meta` files and the v2 models' 16 orphans in 4d531e8b). The four creature sheets re-sliced from their json (Glassback 52, Cinderling 50, Flarewing 52, Shadewyrm 50 frames); the 48 "rect lies outside of texture" lines in the import log are each colour sheet's old v2 `.meta` (24 rects) on the first import, gone after the re-slice.
- **PlayMode slice 16/16** (`MercuryStagePlay|MercuryEntry|MarsStagePlay|InnerCreature|HazardV2Play|Solarite|WardenPlay|BudgetGate|Transition|BandFollowPlay`): the entry at x 64 is in the Twilight zone → `backgrounds/mercury/twilight` (no fallback, the set on disk), strips 2/2, the rig set 42 plants, datum 310.0; the creep leg 2 crossfades → `backgrounds/mercury/day`, the camp's strip regolith; MercuryEntry 0.81 s; 20 Mercury creatures' AI median 0.035 / p99 0.122 / max 0.207 ms; Warden p99 0.013 ms; the editor BudgetGate (Earth / Space / Mars) green; Transition ×2, BandFollow, MarsStage ×2, HazardV2 ×3, Solarite green.
- Lock 2: M3Inner, the captures, the 16:9 re-shoots, Build/MERIDIAN_0.4.4 (a dev build; 0.4.3 stays the owner's, D-144) + the 13-leg probe (the Mercury perf rows, the Creep second loop).

## Captures
pending B-148 / B-149 / B-150.

## Open
- The Shadewyrm's temper (Hunts in the table, shy in B-145's re-ink list) — a decision if LEAD wants it changed.
- The Cinderling swarm "at dawn" is the spawner's rule already (local time 0.15–0.35); nothing changes on the cartoon path.
