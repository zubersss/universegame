# C2 Mercury design prep (B-145, BLENDER, 2026-11-07)

Basis: Bible 4.1 §7.3 Mercury ("the twilight run": a day side at Thermal 3, a night side at Cryo 3, a ~400 m twilight band
creeping 1 m per 6 s, polar cold traps with ice, solar flares, Solarite; Look: "pitch-black sky with a huge Sun, blinding
regolith, violet twilight"), §9.1 (muted, aged; one 6-8 colour palette per planet), §9.3 (faces only on creatures, D-101;
friendly or neutral, D-087), contract v3.1 §11 (+ v3.2 `cycle_beats`, D-127). The B-139 Mars pattern: LEAD accepts these
designs before any Mercury card is written. Nothing here is exported.

## 0. State

| Item | State | File |
|---|---|---|
| Palette | proposed; the check passes (the Mars checks + Mercury's family: violet twilight, near-neutral regolith, a cool slate) | blender/scripts/build_c2_mercury_palette.py |
| Five plants | designed below; `(d, M, pose)` drawing functions + a 1x preview next | blender/scripts/build_c2_mercury_plants.py (next) |
| Creatures | the re-ink list below (all five have v2 models in Art: `replaces_v2`) | - |
| Backdrops | study notes below (FFT washes: a BLENDER slot) | - |
| Props | the ones that differ, below | - |

## 1. Palette (proposed; checked by blender/scripts/build_c2_mercury_palette.py)

Same slot names and order as Earth's and Mars' strips, so gp_draw's mid / deep tones (70 / 45 % colour + the "brown" slot)
and the reviews' palette check work unchanged once LEAD accepts it into `meridian.v3.PALETTES["mercury"]`.

| slot | hex | role | mid | deep | contrast vs ink | chroma |
|---|---|---|---|---|---|---|
| offwhite | #E9E2D4 | blinding regolith: the sunlit ground, glare highlights, frost in the cold traps | #B6AFAA | #8B8487 | 13.4 | 8 |
| red | #A85A41 | ember: flare-scorched rock, heat-side plants, the Cinderhulk's hot seams | #885043 | #6E4745 | 3.5 | 41 |
| mustard | #D8B566 | sun gold: the huge Sun, Solarite crystals, glare on metal | #AA905D | #837056 | 8.8 | 45 |
| teal | #5E8B91 | cold steel teal: polar-crater ice, shadow-side plants, the one cool accent | #54727B | #4C5D69 | 4.6 | 16 |
| green | #8B9471 | dusty sage: Mercury plants (readable on the regolith, the twilight and the night) | #747865 | #61615A | 5.4 | 20 |
| sky | #8D7AA0 | violet twilight: the terminator band, far crater rims at dusk | #756686 | #625670 | 4.5 | 23 |
| brown | #3E3848 | night slate: the shadow colour every mid / deep tone mixes toward; the night side | #3E3848 | #3E3848 | 1.5 | 11 |
| ink | #1E1A17 | ink, shared (also the pitch-black day sky) | - | - | 1.0 | 3 |

| check | result |
|---|---|
| every colour reads under the ink (contrast >= 2.0; the night slate is exempt: it is only a tone and the night side) | pass |
| muted: no colour more saturated than Earth's most saturated accepted colour (chroma <= 59; Mercury max 45) | pass |
| distinct (closest pair teal / green at dE 26, >= 12) | pass |
| plants (dusty sage) read on the blinding regolith, the violet twilight and the night slate (dE >= 20; min 33) | pass |
| the twilight is violet (hue 280-330 deg; 310) and the regolith is near neutral (chroma <= 12; 8) | pass |
| cool family: the night slate is dark and cool (L < 30, hue 260-330 deg) | pass |
| the shadow tones stay inside the family (deep tones never black: L > 20) | pass |

All checks pass (ALL PASS): `python -I blender/scripts/build_c2_mercury_palette.py`. The day sky is the ink itself (pitch black), not a wash.

## 2. Five faceless Mercury plants (heat side, twilight, shadow side)

All faceless (D-101): personality through motion; ink, mid + deep tones, interior detail; one Mercury rig set
(`flora/mercury/rigset`, <= 6 bones each), `biomes` per plant. Mercury's 0.38 g matches Mars: drawn 1.5x like Mars' plants.

| # | Plant | Look | Motion (idle on the 110 bpm beat; react within 3 m) | Biomes |
|---|---|---|---|---|
| 1 | Sunfan | a fan of stiff sun-gold blades on a short ember stem, seams down each blade | the fan tilts edge-on to the Sun on the beat (swap open / edge); react: snaps shut like a folding fan, reopens | day plains |
| 2 | Embercap | a squat ember cap with a cracked crust and a gold underside (a drawn tone), on a stubby sage foot | the crust breathes (squash); react: a little puff of spark dust, settles | day plains, flare fields |
| 3 | Glassreed | a cluster of tall violet-teal blades with off-white glints (drawn, no translucency) | blades sway out of phase (a bone cascade), glints swap; react: the blades clack together and ring still | the twilight band |
| 4 | Shadebloom | a violet bud on a coiled stem, frost-tipped petals | opens only in shadow: a slow open / close cycle (swap); react: shuts tight | night side, crater shadows |
| 5 | Coilwort | a sage coil-spring stem with a teal ice bead on top | bounces on the beat; react: compresses, then springs up with an overshoot | polar cold traps |

## 3. Backdrop studies (painted, B-114 / B-133 / B-141 manner; FFT washes, so they run in a BLENDER slot)

- Day: the sky is ink-black (a flat ink wash with a few sharp stars), the huge Sun low on one side (a gold disc with a drawn
  corona ring in the B-137 manner, no glow shader), the regolith blinding off-white with crisp crater rims and hard black
  shadows (the slate), heat shimmer drawn as a few wavy ink-free dabs near the horizon.
- Twilight: a violet band low across the sky, long shadows, Glassreed fields in the near layer; the layer the player
  mostly runs through (the band creeps 1 m per 6 s, so the backdrop stays put and UNITY moves the light).
- Night: black with stars, the slate ground, teal ice glints in the polar craters; a cold-trap scene for the ice runs.
- Each scene: layer0..2 at 2048 wide (tile x, the B-133 seam roll), `Stack` + `tint()` for translucent shapes; the review at
  1x on a Mercury ground strip beside the surveyor (Mercury terrain kinds exist as v2: regolith, basalt, sulfide, ice).

## 4. Mercury creature re-ink list (contract §11.2: idle 8-12, walk / run / fly / swim 12-16, others <= 16)

| # | Creature (§7.3) | Role / habitat | Cartoon size at 1x | Clips | Interior detail | Notes |
|---|---|---|---|---|---|---|
| 1 | Glassback | silicate grazer riding the twilight band | ~1.8 x 1.1 m | idle 10, walk 12 (an amble), react 8 (its crystal plates chime up), bump 10, flee 12 | crystal-plate facets and seams, hide specks | v2 model: `replaces_v2`; plates as drawn facets, no translucency |
| 2 | Cinderling | small, swarms at dawn | ~0.5 m | idle 8, walk 12 (a scurry), react 8 (a hop and a spark puff), bump 8, flee 12 | an ember shell with crust cracks | v2 model: `replaces_v2`; swarms are UNITY's spawner |
| 3 | Flarewing | a flyer that feeds on flares; "aggressive" becomes excited (D-087): it loops and flashes during a flare | ~1.4 m wingspan | idle 10 (hover), fly 12 (index 1, the travel clip, like the swimmers' swim), react 8 (a loop-de-loop), bump 10, flare_dance 12 | wing ribs, gold flare-catching vanes | v2 model: `replaces_v2`; pivot at the body centre like B-135's swimmers |
| 4 | Shadewyrm | an ice burrower in the polar craters -> shy | ~2.0 m long, segmented | idle 10 (peeks from its burrow), walk 12 (a slither), react 8 (dives), bump 10, idle_open 10 | segment seams, frost on the plates | v2 model: `replaces_v2`; D-126: the burrow is a separate den prop (`props/mercury/ice_burrow`, new) drawn in front |
| 5 | Cinderhulk (Grand creature, ex-apex) | an armoured colossus; the shell glows white on the day side, cools and cracks after crossing into night | ~18 m (proposal) | idle 12 (a slow sway, `cycle_beats` 4), react 12 (a slow turn), cooling 12 (day -> night: the shell's glow steps down, cracks open), scan-pose 8 (the Survey end state) | shell plate seams, drawn heat tones | a §11.3 rig set like the Hadal Maw (D-127), shell parts with day / night swaps (the v2 has cinderhulk_day / _night jsons) |

## 5. Mercury props that differ

Shared with Earth / Mars (B-131 / B-144 sheets as they are): the landing pad, shelter wall, crate, lamp. Mercury's v2 models
in Art today, each `replaces_v2` at export: `props/mercury/flare_shelter` (a squat dome bunker with a heavy door and one
lamp; the Mercury beacon sits inside), `props/mercury/meridian_beacon` (the Mars beacon's design in the Mercury palette,
inside the shelter), `props/mercury/warden_vault_gate` (the Warden-guarded Sowing vault: a round iron gate with the Warden
bell, a hum 4 like the Mars pylon), `props/mercury/solarite_cluster`, `solarite_crusted`, `solarite_cut` (the resource node in
three states: gold crystals, crusted in ember rock, cut facets; a glint 4 on the cluster), `props/mercury/equipment_locker`,
`props/mercury/shelter_door` (the heat-shielded door: the B-131 door's design with a gold heat shield). New by D-126:
`props/mercury/ice_burrow` (the Shadewyrm's den).

## 6. Order of work after LEAD's acceptance

Palette into v3 + the strip -> the Mercury ground strips -> the five plants (previews, one rig-set export) -> day /
twilight / night backdrops (slot) -> creatures 1-4 (+ the ice burrow) -> Mercury props -> the Cinderhulk rig set.
