# C2 Mars design prep (B-139, BLENDER, 2026-11-07)

Basis: Bible 4.1 §7.2 Mars (Look: "butterscotch sky, long shadows, rust / umber / salmon; thin haze; sharp stars at dusk"),
§9.1 (muted, aged palette families; one 6-8 colour palette per planet), §9.3 (faces only on creatures, D-101; friendly or
neutral, D-087), contract v3.1 §11 (ink 2-3 / 1-1.5 px, mid + deep tones, PPU 64, caps). The C2 Earth pattern (cycle 245):
LEAD accepts these designs before any Mars card is written.

## 0. State (LEAD cycle 256, 2026-11-07 04:2x)

| Item | State | Commit / file | Card |
|---|---|---|---|
| Palette | ACCEPTED (D-125); in `meridian.v3.PALETTES["mars"]`; `ui/palettes/mars/strip` exported | cb88c5f, slot 03:06 | - |
| Ground strips (regolith, basalt) | preview; export row ready (`terrain/mars/ground_strip_set`) | 81d36d4, b0e3a53 | B-140 (after U-106) |
| Five plants | ACCEPTED (Puffpod D-101 fix cycle 255) | 8c69536, 9e9b06d | - |
| Rig set `flora/mars/rigset` | dry run ACCEPTED (504x216, 26 parts, json valid); export row ready | a4c9395, b0e3a53 | B-140 (after U-106) |
| Canyon + storm backdrops | sources written (`build_backdrop_v3.mars_canyon / mars_storm`); studies run in the next BLENDER slot; rows ready | 9cb766f, e6f74ae | B-141 |
| Dustskater | ACCEPTED (design) | 709a5bb | B-142 (after U-118) |
| Scree stalker | drawn, all 64 frames pass; review image in the next slot | a3b7222, fd9f5c8 | B-142 |
| Tube lurker + `props/mars/tube_mound` | D-126 split done: hole-less creature (40 frames pass) + the den prop (UNITY draws it in front) | c1d1377 | B-142 |
| Polar crawler | drawn, all 46 frames pass; review image in the next slot | e15fb30 | B-142 |
| Tharsis Worm rig set | not started (the Hadal Maw's pattern; B-136 accepted cycle 256) | - | - |

Rows for every export are in `blender/manifest.json` (dustskater + scree_stalker replace their v2 rows with `replaces_v2`).

## 1. Palette (ACCEPTED, D-125; checked by blender/scripts/build_c2_mars_palette.py)

Same slot names and order as Earth's strip, so gp_draw's mid / deep tones (70 / 45 % colour + the umber in the "brown" slot)
and the reviews' palette check work unchanged once LEAD accepts it into `meridian.v3.PALETTES["mars"]` and
`ui/palettes/mars/strip`.

| slot | hex | role | mid | deep | contrast vs ink | chroma |
|---|---|---|---|---|---|---|
| offwhite | #EEDCC2 | dust white: highlights, world-lit whites, frost | #C2AB95 | #9E836F | 12.9 | 15 |
| red | #B0502D | rust: the ground, boulders, the planet's signature | #97492C | #82442C | 3.3 | 53 |
| mustard | #D6A266 | butterscotch: the sky, sunlit dust, warm accents | #B18354 | #936946 | 7.6 | 40 |
| teal | #6E9C9A | ice teal: polar ice, cold plants, the one cool accent | #697F79 | #64665D | 5.7 | 16 |
| green | #8C8E55 | lichen olive: Mars plants (readable on rust and butterscotch) | #7E7548 | #72603E | 5.0 | 32 |
| sky | #D9907A | salmon haze: far ridges, the dust-storm wall, the horizon band | #B37662 | #94614F | 6.8 | 34 |
| brown | #5C3A2B | umber: the shadow colour every tone mixes toward | #5C3A2B | #5C3A2B | 1.7 | 20 |
| ink | #1E1A17 | shared | - | - | - | - |

Checks (all pass): every colour reads under the ink (contrast >= 2.0, the umber is a tone only); muted (no colour more
saturated than Earth's most saturated accepted colour: chroma <= 59, Mars max 53, the rust); distinct (closest pair
butterscotch / salmon at dE 20); the plants' lichen olive reads on the rust ground and the butterscotch sky (dE >= 20);
warm family (warm off-white, a butterscotch sky); the deep tones stay inside the family (L > 20, never black).

## 2. Five faceless Mars plants (ACCEPTED; rig parts + bones in build_c2_mars_rigs.py, drawn 1.5x for 0.38 g)

All faceless (D-101): personality through motion only; ink, mid + deep tones, interior detail; one Mars rig set
(`flora/mars/rigset`, <= 6 bones each, one texture), `biomes` per plant like Earth's.

| # | Plant | Look | Motion (idle on the 110 bpm beat; react within 3 m) | Biomes |
|---|---|---|---|---|
| 1 | Rustbell | a nodding bell flower on a hose stem, rust petals with a butterscotch lip, lichen leaves | sways; on react the bell swings shut like a lid and reopens (swap open / shut) | rust plains, canyon floor |
| 2 | Puffpod | a round lichen-olive puffball on a short neck, umber speckles | breathes (squash on the beat); react: deflates with a round dust puff, refills | dune seas, plains |
| 3 | Frostcurl | ice-teal fern fronds with off-white frost tips | uncurls by day, curls tight at night (swap cycle); react: shivers | polar margins, high ground |
| 4 | Pipereed | three stacked tube segments like organ pipes, butterscotch rings | segments bob out of phase (bone cascade) as if whistling in the wind; react: a quick telescoping squash | canyon walls, scree |
| 5 | Scree creeper | a low creeping vine with olive lichen pads hugging a rock | the pads ripple along the vine; react: pads lift and flatten | scree, lava-tube mouths |

## 3. Backdrop studies (B-141; painted, B-114 / B-133 manner; FFT washes, so they run in a BLENDER slot)

- Canyon (Valles Marineris): far = the opposite canyon wall in salmon haze with layered strata bands; mid = nearer
  stepped walls in rust with umber shadow ledges and long cast shadows; near = scree slopes and boulders. 2048 wide,
  tiling in x, the B-133 roll so the seam sits on a quiet column.
- Dust storm: the same far / mid layers washed toward salmon, and the storm as the NEAR layer (the near-layer rule: an
  overlay that must read through the stack goes on the nearest layer) with drawn wind streaks and rolling dust billows.
- Review per scene: a 1080p composite at 1x on the B-139 regolith strip beside the surveyor, and the 2x seam check
  (`review_b141_mars_<scene>_preview.png`). The Mars layers composite each wash as it is added (`Stack`): peak ~half.

## 4. Mars creature re-ink list (order, sizes, clips; contract §11.2: idle 8-12, walk / run 12-16, others <= 16)

| # | Creature (§7.2) | Role / habitat | Cartoon size at 1x | Clips | Interior detail | Notes |
|---|---|---|---|---|---|---|
| 1 | Dustskater | small scavenger; plains, dunes | ~0.8 m long (SpeciesSpec 0.8 x 0.45) | idle 10, walk 12 (a skating glide on splayed feet), react 8 (eye-pop, skid), bump 10, flee 12 | dust-crust plates, foot pads, specks | v2 model in Art: `replaces_v2` at export (D-119) |
| 2 | Scree stalker | canyon pack animal (no combat, D-087: curious, follows) | ~1.6 x 1.0 m | idle 10, walk 12, react 8, bump 10, follow 12, flee 12 | scale ridges, claw seams, a crest | v2 model in Art: `replaces_v2`; the wolf's follow pattern |
| 3 | Lava-tube lurker (`tube_lurker`) | ambusher in the dark tubes -> a shy peeker | ~1.2 m | idle 10 (peeks over its den), walk 12, react 8 (startle + duck), bump 10 | rock-like hide plates, eyes ringed by a mustard glow tone (no emission) | new key; D-126: the den is the static prop `props/mars/tube_mound`, drawn by UNITY in front on the same pivot |
| 4 | Polar crawler (`polar_crawler`) | slow, armoured; ice caps | ~1.4 x 0.8 m | idle 12 (plates breathe), walk 14 (slow), react 10 (curls into a ball), bump 10 | frost caps on the plates, plate seams, ice specks | new key; an olive pill-bug whose shell arc curls into a ball |
| 5 | Tharsis Worm (Grand creature, ex-apex) | surfaces in dust storms under Olympus Mons | ~60 m (Bible) | idle 12 (a surfaced arc sways), react 12 (a slow turn), scan-pose 8 (the Survey end state, D-087) | plate seams (Wormplate), sand pouring off | a §11.3 rig set like the Hadal Maw (B-136) |

## 5. Mars camp props that differ from Earth's

Shared with Earth (B-131 sheets as they are): the landing pad, shelter wall and door, storage crate, lamp, smelter.
Mars-only (v2 models in Art today, each `replaces_v2` at export): `props/mars/ice_drill_rig` (ice mining: a drill derrick,
a working loop), `props/mars/meridian_beacon` (the first-beacon story POI: a mast with a turning lamp, no face),
`props/mars/hauler_hull_a`, `hauler_hull_b`, `hauler_cargo` (the crashed Halcyon hauler: static wreck pieces, sand drifts),
`props/mars/warden_pylon` (the Warden outpost, combat-free since D-087: a humming pylon idle). Proposed new: an airlock
door for the pressurized base (Mars base building; Earth's door has no seal). Added by D-126: `props/mars/tube_mound`
(the lurker's den, `build_props_mars_v3.py`, the build_props_common_v3 API; render.py's prop rows import their generator).

## 6. Order of work (cards since cycle 256)

B-140 (Ready, after U-106): the rig set + the two strips, one short batch. B-141 (Ready): the canyon + storm studies in the
next slot, then the export. B-142 (Backlog until U-118): the four creatures + the den mound. Then the Mars-only props and
the Tharsis Worm rig set with the Hadal Maw's pattern.
