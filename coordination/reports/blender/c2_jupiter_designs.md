# C2 Jupiter design prep (B-155, BLENDER, 2026-11-07)

Basis: Bible 4.1 §7.5 (the cloud-column world type: no ground; a 4096 x 2000 column; the Datum at y 1100; Deck 1
ammonia-ice clouds with floating ice floes that sublimate 30-90 s after the player disturbs them, buoyant derelicts,
creature husks; Deck 2 denser floes, stations, the beacon, lightning; Deck 3 water clouds, storms, the big creatures;
the Deep; the Crush Line at y 100 "drawn as a pulsing dark band with the label CRUSH"), §7.6 Jupiter (Radiation 3 above
Deck 2, lightning in Decks 2-3, 2.53 g, Cryo 2 in Deck 1, Thermal 2 in the Deep, the Great Red Spot a 600 m zone where
the wind pushes 12 m/s and floes spin; Metallic Hydrogen veins in hardened floe cores; Look: "cream, rust, and brick
bands rolling past; lightning under the floor; a sky that cycles every 8 minutes"), §9.1, §9.3 (faces only on
creatures, D-101; friendly or neutral, D-087), contract v3.1 §11 (+ v3.2 `cycle_beats`, D-127), the backdrop near-layer
rule (an overlay that must read through the cloud stack goes on layer2). The B-139 / B-145 / B-147 pattern: LEAD
accepts these designs before any Jupiter card is written. Nothing here is exported. The first giant sets the
cloud-column pattern Saturn, Uranus and Neptune reuse.

## 0. State

| Item | State | File |
|---|---|---|
| Palette | ACCEPTED (D-137): in `meridian.v3.PALETTES["jupiter"]` + the ui/palettes/jupiter row (exports with the first Jupiter slot) | blender/scripts/build_c2_jupiter_palette.py |
| Five flora (floe forms + float-cell forms) | source (f9205793, 1.6x since 7eee59fd): key poses checked, palette 100 %; the full preview waits for a free gap | build_c2_jupiter_plants.py |
| Floe strips | source + checks (a7c4c38a: 4 kinds x 10 frames per D-137, joins <= 0.86/255, caps the same, palette 100 %); review_b155_jupiter_floes_preview.png | build_c2_jupiter_floes.py |
| Cloud-deck backdrops | source (11169afd: deck1 / deck2 / deck3 / deep with the CRUSH band / spot = the Red Spot overlay); studies need slots | build_backdrop_v3.py (jupiter_scene) |
| Creatures 1-4 | source (a4a75e39): every frame in bounds; the reviews wait for a free gap | build_creatures_jupiter_v3.py |
| Vortex Whale | rig-set source (72753c0d, 6 bones); size (~48 m at 1x) asked | build_vortex_whale_v3.py |
| Aerostat kit (B-156) | source (fcf4c22e): deck, strut, cell, two packs, hook; the review waits for a free gap | build_props_aerostat_v3.py |
| Props that differ | later (section 6: the husk, derelict, vault) | - |

## 1. Palette (ACCEPTED, D-137; checked by blender/scripts/build_c2_jupiter_palette.py)

| slot | hex | role | mid | deep | contrast vs ink | chroma |
|---|---|---|---|---|---|---|
| offwhite | #EEE2CB | ammonia cream: the zones, floe-ice tops, cloud-deck highlights, the aerostat canvas | #BDB09E | #948678 | 13.5 | 13 |
| red | #A8503A | Red Spot brick: the Great Red Spot, phosphorus floes and blooms, warm accents | #8C4A38 | #754437 | 3.2 | 46 |
| mustard | #C48A4E | belt rust: the rust belts rolling past, rusted derelict plating, brass | #A07246 | #815F40 | 5.8 | 43 |
| teal | #6F8A97 | festoon blue-grey: lightning glow tones under the floor, the water decks, the one cool accent | #647279 | #5B5F61 | 4.7 | 12 |
| green | #8F9A6A | lichen sage: Jupiter flora (readable on the cream, the tan haze and the deep umber) | #7B7E5A | #6A664C | 5.8 | 27 |
| sky | #D8BC94 | zone tan: the deck sky between the bands, far cloud banks | #AE9577 | #8A755F | 9.5 | 24 |
| brown | #4B3B34 | deep umber: the dark under the floor; the shadow colour every mid / deep tone mixes toward | #4B3B34 | #4B3B34 | 1.6 | 9 |
| ink | #1E1A17 | ink, shared | - | - | 1.0 | 3 |

| check | result |
|---|---|
| every colour reads under the ink (contrast >= 2.0; the umber is exempt: it is only a tone and the dark under the floor) | pass |
| muted: no colour more saturated than Earth's most saturated accepted colour (chroma <= 59; Jupiter max 46) | pass |
| distinct (closest pair offwhite / sky at dE 17, >= 12) | pass |
| plants (lichen sage) read on the zone tan, the cream and the umber (dE >= 20; min 23) | pass |
| the bands stay apart: brick (hue 25-50 deg; 41) and rust (hue 50-75 deg; 69) at dE 28 (>= 15) | pass |
| a warm cream zone (L > 85, b* > 8; L 90, b* 13) and a tan sky darker than it (dL >= 8) | pass |
| one cool accent (festoon b* < 0; -10) and a deep umber (L < 30; 26) | pass |
| the shadow tones stay inside the family (deep tones never black: L > 20) | pass |

All checks pass (ALL PASS).

Slots keep the other planets' roles, so gp_draw's mid / deep tones and the reviews' palette check work unchanged once
LEAD accepts it into `meridian.v3.PALETTES["jupiter"]`. The giants that follow swap only the family rows of the check
(Saturn's pale gold bands, Uranus' and Neptune's methane cyans).

## 2. Five faceless Jupiter flora (floe forms and float-cell forms)

All faceless (D-101): personality through motion; ink, mid + deep tones, interior detail; one Jupiter rig set
(`flora/jupiter/rigset`, <= 6 bones each), `biomes` per plant (the column's decks, the Red Spot). At 2.53 g the floe
forms are low and broad (no tall stalks); the float-cell forms float, so gravity reads in their tethers, drawn taut
downward. Drawn 1.6x so they read beside the 2 m surveyor (like Venus; 1.4x read too small in the floe preview).

| # | Plant | Look | Motion (idle on the 110 bpm beat; react within 3 m) | Biomes |
|---|---|---|---|---|
| 1 | Driftbulb | a float-cell form: a cream gas bulb with one rust band and a ribbed seam, a sage tether tendril pulled taut down to its floe | bobs on the beat with a squash; react: deflates and dips (swap), then refills | deck 1, deck 2 |
| 2 | Bandstreamer | a squat sage holdfast on a floe edge trailing three long cream-and-rust striped streamers on the wind | the streamers wave (a bone cascade, like the Sulphurbell's chain); react: they wrap round the holdfast (swap) | deck 1 |
| 3 | Frostrosette | a low rosette of cream ammonia-ice crystal leaves on floe tops, festoon blue-grey facets | the crystals glint (swap) on the beat; react: they fold shut | deck 1 (Cryo 2) |
| 4 | Phosphor cup | brick-red cup blooms on a coiled sage stem, on the Red Spot floes (the phosphorus pigment resource) | the cups open / close on the beat; react: they close and the stem spins once (the Spot's wind) | the Great Red Spot |
| 5 | Stormreed | a clump of short stiff sage reeds tipped with festoon blue-grey bulbs | the tips flicker (a swap, a tone, no emission) as lightning walks under the floor; react: the reeds flatten | deck 2, deck 3 |

## 3. Floes (the ground of a giant): strips and caps

Floes are terrain tiles in the cloud column today (`terrain/jupiter/floe_ice`, `floe_core`, `floe_derelict`,
gen_terrain3d). In C2 they take the Earth / Mars ground-strip contract (B-130: 8 frames 64 x 152, pivot on the ground
line, `"tile": true`), one strip per floe kind:

- `terrain/jupiter/floe_strip_ice`: cream ammonia-ice top with frost lips, a tan-and-umber underside that thins into
  cloud wisps (a floe has no ground below it: the underside is drawn, then fades to the cloud through alpha).
- `terrain/jupiter/floe_strip_core`: a hardened brick-and-umber core floe with festoon blue-grey Metallic Hydrogen veins
  (the Deep only; drawn as tone veins, no emission).
- `terrain/jupiter/floe_strip_derelict`: rust plating with rivets and a torn edge (the *Meridian* expedition's derelicts).
- `terrain/jupiter/floe_strip_spot`: brick phosphorus ice with swirl marks (the Red Spot's floes).

**Ruled (D-137): caps yes.** A floe is finite, so each giant's floe strip has two extra frames (`cap_left`,
`cap_right`, the same 64 x 152 cell and pivot, after the 8 tile frames: 10 frames on the B-130 frame contract), drawn so
a floe of any length is cap + n tiles + cap. GroundStrip's cap placement is UNITY's card U-126 (with Jupiter's wiring);
the Earth and Mars strips stay 8 frames. The sublimation (30-90 s) re-inks `fx/floe_sublimate` in the v3 style: cream puffs
peeling off the floe's edge, 8 frames.

## 4. Cloud-deck backdrop studies (painted, the B-141 / B-145 / B-147 manner; FFT washes, so they run in a BLENDER slot)

Four scenes, one per band of the column, each layer0..2 at 2048 wide (tile x, the B-133 seam roll), `Stack` + `tint()`
for the translucent cloud, reviewed at 1x on a floe strip beside the surveyor. Jupiter's sky cycles every 8 minutes:
the scenes are drawn at noon and UNITY's day tint (the existing sky cycle) darkens them; nothing is baked per hour.

- **Deck 1 (ammonia, y 1100-900):** far = cream and rust bands rolling past (wide horizontal ribbons, the planet's own
  stripes seen edge-on), Io and Europa as small painted discs in the thin sky at the top; mid = cream ammonia cloud banks
  with frosted tops; near = wisps streaming in the wind.
- **Deck 2 (ammonium hydrosulfide, y 900-600):** far = tan-to-umber cloud walls; mid = denser banks and a distant
  station silhouette; near = umber billows with **lightning under the floor**: forked cream-and-festoon flashes drawn as
  tones low in layer2 (they read through the stack on the near layer).
- **Deck 3 (water, y 600-300):** far = warm umber towers lit from below; mid = storm anvils; near = rain curtains and
  the big creatures' shadows (silhouettes only, no faces).
- **Deep (y 300-100):** far = the umber dark; mid = slow brick-and-umber swirls (Thermal 2: heat shimmer dabs);
  near = **the Crush band** on layer2 (the near-layer rule): a dark pulsing band along the layer's bottom with the
  label "CRUSH" lettered in Limelight as drawn ink (the B-146 TrueType reader), so it reads through every cloud layer
  above it. The pulse is UNITY's (`fx/crush_pulse` re-inked as a 4-frame tone loop); the band itself is static art.
- **The Great Red Spot** (a 600 m zone): a layer1 overlay of brick swirl arms turning about the Spot's eye, for the Spot
  zone only (UNITY rotates it slowly; floes spin there).

## 5. Jupiter creature re-ink list (contract §11.2; faces kept, no teeth)

| # | Creature (§7.6) | Role / habitat | Cartoon size at 1x | Clips | Notes |
|---|---|---|---|---|---|
| 1 | Stormglider | a manta floater riding the deck winds | ~2.4 m wingspan | idle 10 (a slow glide-bob), glide 12 at index 1 (the travel clip, like the swimmers' swim), react 8 (a barrel roll away), bump 10 | `replaces_v2`; pivot at the body centre; a cream belly with rust bands across its wings, pie eyes |
| 2 | Lightning eel | Deck 2; electric, curious | ~1.8 m | idle 10 (an S-wave hover), swim 12 at index 1, react 8 (sparks: cream / festoon tone dabs, a flinch), bump 10 | `replaces_v2`; pivot at the body centre; sparks as tones, never a bite |
| 3 | Belt wasp | Deck 1; a radiation-adapted swarm | ~0.5 m | idle 8 (a hover), fly 12 at index 1, react 8 (a zig-zag scatter), bump 8 | `replaces_v2`; rust-and-cream stripes, a blunt round tail (no sting, D-087); swarms are UNITY's spawner |
| 4 | Ballast tortoise | huge and slow; a walkable husk when killed | ~4 x 2.5 m (a floater; its shell a platform) | idle 12 (a slow paddle), swim 14 at index 1, react 10 (pulls its head in), bump 10 | `replaces_v2`; pivot at the body centre; the husk is `props/jupiter/husk_tortoise` (the same shell, empty, a standable top line) |
| 5 | Vortex Whale (apex) | a 500 m floater in the Great Red Spot; its song stuns | a set piece over many screens | idle 12 (a rolling glide, `cycle_beats` 4), song 12 (the throat swells, rings ripple out as tones), react 12 (a slow turn), harpooned 8 | a §11.3 rig set like the Hadal Maw (D-127): body / head / flukes / fins on bones; the multi-stage hunt is UNITY's |

## 6. Jupiter props that differ

The v2 models in Art today, each `replaces_v2` at export: `props/jupiter/husk_tortoise` (the walkable husk: a prop sheet
with a standable top line like the dens, D-126's shared-top-line idea), `derelict_pod` (a buoyant *Meridian* pod: rust
plating, a cream gasbag patch, one round window), `beacon_vault` (the radiation-fried vault around the Jupiter beacon:
scorched plating, a hatch, a festoon-tinted interior glow drawn as a tone). The aerostat kit is shared by all four giants
and lives in `props/common` (`aerostat_deck`, `aerostat_strut`, `aerostat_cell`, `float_cell_pack_mk1` / `mk2`,
`grapple_hook`): RULED (D-137, B-156): re-inked once in the giants' style (it inherits each planet's paper only through
the backdrop, so one palette: Earth's, like the camp set), so Saturn -> Neptune need no aerostat work.

## 7. Order of work after LEAD's acceptance

Palette into v3 + the strip -> the floe strips (+ caps if ruled) -> the five flora (previews, one rig-set export) ->
the four deck backdrops + the Red Spot overlay (slots) -> creatures 1-4 -> the husk, derelict and vault props -> the
aerostat kit (props/common) -> the Vortex Whale rig set.

## 8. Self-check (contract §9.7 boxes, for the designs on paper)

The ten boxes are ticked on each preview at hand-off; on paper: faces only on creatures (D-101) - yes; no teeth, no
sting (D-087) - yes; one palette, muted (the check) - yes; ink weights v3.1 - at the previews; silhouettes readable at
1x - at the previews; motion on the 110 bpm beat - yes (every idle names its beat); the near-layer rule for the Crush
band and the lightning - yes; nothing exported - yes.
