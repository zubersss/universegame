# C2 Venus design prep (B-147, BLENDER, 2026-11-07)

Basis: Bible 4.1 §7.4 Venus ("the dive world": the habitable cloud deck at y 770 +- 60 with floating stations and the
Aerostat base; the surface at y 320, volcanic plains, tesserae, active vents, Thermal 3 / Pressure 3 / Toxic 2 for 3-6 minute
dives; super-rotation winds; Vitriol Glass; Look: "orange-cream haze, backlit cloud towers, black glassy surface lit by
vents"), §9.1, §9.3 (faces only on creatures, D-101; friendly or neutral, D-087), contract v3.1 §11 (+ v3.2 `cycle_beats`,
D-127). The B-139 / B-145 pattern: LEAD accepts these designs before any Venus card is written. Nothing here is exported.

## 0. State

| Item | State | File |
|---|---|---|
| Palette | ACCEPTED (D-134): in `meridian.v3.PALETTES["venus"]` + the ui/palettes/venus row | blender/scripts/build_c2_venus_palette.py |
| Five plants | ACCEPTED (cycle 265; ddbdcb32, drawn 1.6x): review_b147_venus_plants_preview.png | build_c2_venus_plants.py |
| Rig set | source + dry run clean (7102e14d: 33 parts on 508x188, bones 2 / 5 / 4 / 6 / 3, json valid); export B-153 | build_c2_venus_rigs.py |
| Creatures 1-4 + the vent mouth | ACCEPTED (cycle 265; 6d5f7337, d8ac7e69): four reviews + the den review; export B-154 | build_creatures_venus_v3.py, build_props_venus_v3.py |
| Backdrops | surface ACCEPTED (cycle 266); deck re-run 09:00 (cumulus towers, the airship station; accepted on sight); export B-152 | build_backdrop_v3.py (venus_deck, venus_surface) |
| Veil Serpent, props | later (a rig set like the Maw; the props that differ, section 5) | - |

## 1. Palette (proposed; checked by blender/scripts/build_c2_venus_palette.py)

| slot | hex | role | mid | deep | contrast vs ink | chroma |
|---|---|---|---|---|---|---|
| offwhite | #F0E2C8 | cream haze: the backlit cloud-tower edges, highlights, the aerostat canvas | #BDAE9A | #928374 | 13.5 | 14 |
| red | #B8583A | vent orange: the glow of the surface vents, warm accents, the Vent eel | #954E37 | #794534 | 3.7 | 51 |
| mustard | #D8B04E | sulphur yellow: sulphur crust, Sulfur drifters, brass on the stations | #AC8B45 | #876C3D | 8.4 | 54 |
| teal | #6F9A88 | sea-glass teal: Vitriol Glass, acid-haze tints, the one cool accent | #627C6D | #586257 | 5.5 | 19 |
| green | #8E9A5E | dusty olive: Venus plants (readable on the haze, the cream and the basalt) | #787C50 | #666244 | 5.7 | 33 |
| sky | #E0A57A | apricot haze: the cloud deck's sky, far cloud towers | #B18363 | #8B6751 | 8.1 | 35 |
| brown | #45352F | glassy basalt: the dark surface; the shadow colour every mid / deep tone mixes toward | #45352F | #45352F | 1.5 | 9 |
| ink | #1E1A17 | ink, shared | - | - | 1.0 | 3 |

| check | result |
|---|---|
| every colour reads under the ink (contrast >= 2.0; the basalt is exempt: it is only a tone and the dark surface) | pass |
| muted: no colour more saturated than Earth's most saturated accepted colour (chroma <= 59; Venus max 54) | pass |
| distinct (closest pair teal / green at dE 26, >= 12) | pass |
| plants (dusty olive) read on the apricot haze, the cream and the basalt (dE >= 20; min 33) | pass |
| the haze is apricot-orange (hue 40-75 deg; 62) and the sulphur is yellow (hue 70-95 deg; 86) | pass |
| a dark glassy basalt (L < 30) and a warm cream (b* > 8) | pass |
| the shadow tones stay inside the family (deep tones never black: L > 20) | pass |

All checks pass (ALL PASS). Slots keep the other planets' roles, so gp_draw's mid / deep tones (70 / 45 % colour + the basalt) and the
reviews' palette check work unchanged once LEAD accepts it into `meridian.v3.PALETTES["venus"]`.

## 2. Five faceless Venus plants (deck forms and surface forms)

All faceless (D-101): personality through motion; ink, mid + deep tones, interior detail; one Venus rig set
(`flora/venus/rigset`, <= 6 bones each), `biomes` per plant. The super-rotation wind leans every deck plant the same way.

| # | Plant | Look | Motion (idle on the 110 bpm beat; react within 3 m) | Biomes |
|---|---|---|---|---|
| 1 | Puffsail | a cream gas bladder like a little sail on an olive stalk, tethered to a deck plank by root threads, ribbed seams | bobs and leans with the wind; react: the bladder sags and refills | cloud deck |
| 2 | Sulphurbell | a trailing olive vine hung with sulphur-yellow bells along a rail | the bells swing out of phase (a bone cascade); react: the bells close and ring still | cloud deck, station rails |
| 3 | Hazefern | an apricot-tinged olive frond that curls into the wind | uncurls and curls on the beat (swap); react: curls tight | cloud deck |
| 4 | Glasscoral | sea-glass teal coral spikes on a basalt foot, a vent-orange glow tone at their bases | the glow steps (swap) as the vent breathes; react: the spikes retract | surface vent fields |
| 5 | Ventcap | a squat basalt chimney plant with a vent-orange mouth and a hinged lid | puffs a cream steam ring on the beat; react: the lid snaps shut, reopens | surface plains, vents |

## 3. Backdrop studies (painted, the B-114 / B-133 / B-141 manner; FFT washes, so they run in a BLENDER slot)

- Cloud deck: far = sulphur-haze bands (apricot over cream, horizontal bands that drift with the super-rotation) with
  backlit cloud towers (cream edges, apricot bodies, the sun behind them); mid = nearer towers and a floating station
  silhouette; near = the haze thinning to show the dark surface far below with tiny vent glows (the promise of the dive).
- The aerostat deck strip: a ground-strip kind (the B-130 contract) of deck planks and rail posts for the deck scenes.
- Surface dive: an orange-cream haze ceiling, black glassy basalt plains and tesserae ridges lit from below by vent
  glows (vent orange drawn as tones, no emission), heat shimmer dabs, acid-rain streaks that stop mid-air (evaporating).
- Each scene: layer0..2 at 2048 wide (tile x, the B-133 seam roll), `Stack` + `tint()` for the translucent haze; the
  review at 1x on a Venus strip beside the surveyor.

## 4. Venus creature re-ink list (contract §11.2; faces kept, no teeth)

| # | Creature (§7.4) | Role / habitat | Cartoon size at 1x | Clips | Notes |
|---|---|---|---|---|---|
| 1 | Sulfur drifter | a gasbag filter feeder on the deck winds | ~1.4 m | idle 10 (a bob), drift 12 at index 1 (the travel clip, like the swimmers' swim / the Flarewing's fly), react 8 (puffs up), bump 10, flee 12 | `replaces_v2`; pivot at the body centre; a sulphur-yellow gasbag, frilly filter tendrils, pie eyes |
| 2 | Acidmoth | swarms near lights: curious, never biting | ~0.5 m wingspan | idle 8 (a hover near the light), fly 12 at index 1, react 8 (scatter), bump 8 | `replaces_v2`; sea-glass wings; swarms are UNITY's spawner |
| 3 | Pressure crab | the surface; armoured and slow | ~1.2 x 0.7 m | idle 10, walk 12 (a sideways shuffle), react 8 (pulls into its shell), bump 10 | `replaces_v2`; a basalt shell with vent-orange claw tips; claws wave, never pinch (D-087) |
| 4 | Vent eel | the surface vents; "heat-seeking" becomes curious about warmth | ~1.6 m | idle 10 (peeks from its vent), walk 12 (a slither), react 8 (ducks), bump 10, idle_open 10 | `replaces_v2`; D-126: the vent is a separate den prop (`props/venus/vent_mouth`, new) drawn in front |
| 5 | Veil Serpent (Grand creature, ex-apex) | a 300 m ribbon in the acid haze that wraps stations; flees from cold | a set piece over many screens | idle 12 (a slow ribbon wave, `cycle_beats` 4), react 12 (recoils from a Cryo lantern), scan-pose 8 | a §11.3 rig set like the Hadal Maw (D-127; the v2 has body / head / tail parts) |

## 5. Venus props that differ

The v2 models in Art today, each `replaces_v2` at export: `props/venus/aerostat_balloon` (the gasbag + rigging),
`aerostat_deck` (the deck module, tiles), `buoyancy_cell` (a float-cell canister), `railing` (tiles), `station_hull_a`,
`station_hull_b` (the floating station pieces), `meridian_station_door` (the Venus beacon station; the Warden origin),
`vent_harvester` (vent mining, a working loop). New by D-126: `props/venus/vent_mouth` (the Vent eel's den).

## 6. Order of work after LEAD's acceptance

Palette into v3 + the strip -> the deck strip + a basalt strip -> the five plants (previews, one rig-set export) -> the
cloud-deck and surface backdrops (slot) -> creatures 1-4 (+ the vent mouth) -> Venus props -> the Veil Serpent rig set.
