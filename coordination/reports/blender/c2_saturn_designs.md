# C2 Saturn design prep (B-157, BLENDER, 2026-11-07)

Basis: Bible 4.1 §7.5 (the cloud-column world type, as Jupiter: the Datum, Decks 1-3, the Deep, the Crush Line drawn as a
dark band labelled CRUSH), §7.7 Saturn (gravity 1.06x, Cryo 2 in Deck 1, the North Polar Hexagon: a 900 m zone of six
rotating wind-walls with a calm eye; Helium-3 Condensate collected in Deck 2-3 traps; ring mining in space; Titan and
Enceladus in the sky; Look: "pale gold and butter bands, the ring plane as a bright line across the sky, soft low
sunlight"), §9.1, §9.3 (faces only on creatures, D-101; friendly or neutral, D-087), contract v3.1 §11 (+ v3.2
`cycle_beats`, D-127), the backdrop near-layer rule. The B-155 pattern (Jupiter, accepted cycle 267) is the base: the same
scene builder, the capped floe strips (D-137), the shared aerostat kit (B-156). Nothing here is exported.

## 0. State

| Item | State | File |
|---|---|---|
| Palette | proposed; the check (the Mars checks + Saturn's family, measured against Jupiter) passes, below | blender/scripts/build_c2_saturn_palette.py |
| Five flora | designed below; drawings + a 1x preview next (when RAM allows) | build_c2_saturn_plants.py (next) |
| Floe strips | designed below (D-137's 10-frame contract: 8 tiles + caps) | build_c2_saturn_floes.py (next) |
| Deck backdrops | study notes below (FFT washes: a BLENDER slot) | build_backdrop_v3.py (next) |
| Creatures | the re-ink list below (three v2 models: `replaces_v2`; the Ringmite is space; the apex a rig set) | - |
| Props | the ones that differ, below | - |

## 1. Palette (proposed; checked by blender/scripts/build_c2_saturn_palette.py)

| slot | hex | role | mid | deep | contrast vs ink | chroma |
|---|---|---|---|---|---|---|
| offwhite | #F1E9D2 | butter cream: the zones, floe-ice tops, the ring plane's bright line, highlights | #BFB8A7 | #958F83 | 14.3 | 12 |
| red | #B7735C | dusk salmon: warm accents, Helium-3 condensate tones, the Hex drake's crest | #966554 | #7B5A4E | 4.6 | 34 |
| mustard | #D4B46E | pale gold: the gold bands, brass on the ring-mining rig | #AB9361 | #887756 | 8.7 | 40 |
| teal | #7F98A4 | ring-ice blue-grey: the rings' shadowed edge, the Hexagon's wind-walls, the one cool accent | #6F7F87 | #626A6E | 5.7 | 11 |
| green | #97A27C | pale moss: Saturn flora (readable on the cream, the butter haze and the slate) | #80866B | #6D6F5C | 6.4 | 21 |
| sky | #E3CFA4 | butter haze: the deck sky in soft low sunlight, far cloud banks | #B5A687 | #8F836E | 11.3 | 24 |
| brown | #4A4542 | cold slate: the dark under the floor; the shadow colour every mid / deep tone mixes toward | #4A4542 | #4A4542 | 1.8 | 3 |
| ink | #1E1A17 | ink, shared | - | - | 1.0 | 3 |

| check | result |
|---|---|
| every colour reads under the ink (contrast >= 2.0; the slate is exempt: it is only a tone and the dark under the floor) | pass |
| muted: no colour more saturated than Earth's most saturated accepted colour (chroma <= 59; Saturn max 40) | pass |
| distinct (closest pair offwhite / sky at dE 15, >= 12) | pass |
| plants (pale moss) read on the butter haze, the cream and the slate (dE >= 20; min 23) | pass |
| paler than Jupiter (mean L of the lit colours 72 > Jupiter's 65) and colder (the shadow's b* 2.6 < Jupiter's 7.0) | pass |
| gold bands (pale gold hue 75-95 deg; 86) and soft banding (zone / gold / haze within dE 35; max 33) | pass |
| one cool ring-ice accent (b* < 0; -9) and a dark cold slate (L < 32; 30) | pass |
| the shadow tones stay inside the family (deep tones never black: L > 20) | pass |

All checks pass (ALL PASS).

Slots keep the other planets' roles, so gp_draw's mid / deep tones and the reviews' palette check work unchanged once
LEAD accepts it into `meridian.v3.PALETTES["saturn"]`.

## 2. Five faceless Saturn flora

All faceless (D-101): personality through motion; ink, mid + deep tones, interior detail; one Saturn rig set
(`flora/saturn/rigset`, <= 6 bones each), `biomes` per plant. At 1.06 g the forms can stand taller than Jupiter's (no
need to hug the floes); drawn 1.6x like Venus and Jupiter.

| # | Plant | Look | Motion (idle on the 110 bpm beat; react within 3 m) | Biomes |
|---|---|---|---|---|
| 1 | Ringreed | tall pale-moss reeds whose tips carry thin cream rings (little halos, like the planet's) | the rings tilt and catch the light (swap) on the beat; react: the rings drop down the stems | deck1, deck2 |
| 2 | Heliumbell | a pale-gold bell flower on a coiled stem that floats up on its stem when touched (helium inside) | bobs, the bell swells (swap); react: it rises on its stretched stem, then sinks back | deck2, deck3 (by the traps) |
| 3 | Frostfan | a fan of cream ice fronds edged ring-ice blue-grey, on floe tops | the fan opens / closes on the beat; react: it folds flat | deck1 (Cryo 2) |
| 4 | Hexmoss | a low cushion of moss in hexagon cells (the pole's pattern), dusk-salmon cell rims | the cells pulse (swap) in a ring; react: it hunkers down | the Hexagon's eye |
| 5 | Butterpuff | a cluster of butter-cream puffballs on short stalks that loose drifting spores (tones) | the puffs breathe; react: a spore puff (swap) | deck1, deck2 |

## 3. Floes (ring-mining floes) and ring chunks

The same contract as Jupiter's (D-137): `terrain/saturn/floe_strip_{ice,ring}` each 10 frames (8 tiles + cap_left +
cap_right, 64 x 152, pivot on the ground line):

- `floe_strip_ice`: butter-cream water-ice top with frost lips, a ring-ice blue-grey body, trapped bubbles.
- `floe_strip_ring`: a ring-rock floe (silicates and iron): slate and pale-gold speckled rock under a thin ice crust,
  the ring-mining floes that drift down into Deck 1.
- Ring chunks (props, one static frame each, `props/saturn/ring_chunk_{a,b,c}`): tumbling ice-and-rock pieces for the
  top-down ring-mining lanes (UNITY's space view), cream ice with slate rock inclusions, ring-ice edges.

## 4. Deck backdrop studies (the B-155 scene builder; FFT washes, so they run in a BLENDER slot)

Saturn's twist on the Jupiter column: the rings. From the equatorial decks (1-2) the ring plane is seen edge-on as a
bright cream line across the whole sky (Bible: "the ring plane as a bright line across the sky") with its shadow as a
darker band on the cloud tops below; from the high decks / the polar Hexagon the rings are tilted: a wide pale arc with
the Cassini gap as a darker gap line. Soft low sunlight: long warm highlights on the cloud tops, cool slate shadows.

- **deck1 (equatorial):** far = pale gold and butter bands, the ring line edge-on high in the sky with its shadow band,
  Titan (a small hazy orange-gold disc) and Enceladus (a tiny bright cream disc); mid = cream ammonia banks; near = wisps.
- **deck2:** the ring line still edge-on, butter banks, a distant helium trap rig silhouette; near = drifting
  Helium-3 condensate drops as cream tone dabs.
- **deck3:** warm deep banks, soft storm towers (no lightning: Saturn's storms are rarer; one far flash at most).
- **deep:** slate dark, slow swirls, and the CRUSH band on layer2 (the Jupiter set's band, the Saturn palette).
- **hexagon (the North Polar Hexagon overlay):** the rings tilted as a wide arc in the sky; layer1 = the six straight
  wind-walls of the Hexagon as tall translucent ring-ice blue-grey curtains converging in perspective; the calm eye
  between them (UNITY rotates the walls).

## 5. Saturn creature re-ink list (contract §11.2; faces kept, no teeth)

| # | Creature (§7.7) | Role / habitat | Cartoon size at 1x | Clips | Notes |
|---|---|---|---|---|---|
| 1 | Helium jelly | floats up when hit; Deck 2-3 | ~1.2 m | idle 10 (a pulse), drift 12 at index 1, react 8 (floats up fast, deflating), bump 10 | `replaces_v2`; pivot at the body centre; a pale-gold bell with cream frills and trailing tendrils |
| 2 | Hex drake | winged; rides the Hexagon's walls | ~2.6 m wingspan | idle 10 (a hover), fly 12 at index 1, react 8 (a wing-shielded turn), bump 10 | `replaces_v2`; pivot at the body centre; a slate-and-salmon drake with a hexagon-patterned crest, no teeth (a beak-less smiling snout) |
| 3 | Floe moth | Deck 1 floes | ~0.6 m | idle 8, fly 12 at index 1, react 8 (scatter), bump 8 | `replaces_v2`; cream wings with ring-ice edges; no eyespots |
| 4 | Ringmite | space (ring mining), swarms; chews hull | ~0.4 m | idle 8, fly 12 at index 1, react 8, bump 8 | new key (`creatures/saturn/ringmite`; space-view sheet); a round slate mite with stubby legs, never biting on screen (the hull damage is UNITY's) |
| 5 | Polar Hydra (apex) | the Hexagon's eye; six heads | a set piece | idle 12 (necks weave, `cycle_beats` 4), react 12 per head, head_lost 8 | a §11.3 rig set; six heads + a body is 7 bones (the plants' cap is 6): **a proposal below** |

## 6. Saturn props that differ

The v2 models in Art, each `replaces_v2` at export: `props/saturn/ring_rig` (the ring-mining rig with the Saturn beacon),
`helium_trap` (a Deck 2-3 condensate trap: a cream gasbag over a brass cone with a pale-gold drip), `hexagon_wall_marker`
(a ring-ice blue-grey buoy marking a wall). New: the ring chunks (section 3). The aerostat kit is B-156's (shared).

## 7. Proposals (need a ruling)

1. **The Polar Hydra's bones:** six heads + a body are 7 bones, over the rig sets' 6 (`validate_rigset`'s MAX_BONES is the
   plants' cap). I propose the apex as two rig sets on one body pivot (`polar_hydra_left`, `polar_hydra_right`, three
   necks + heads each, the body drawn once in the left set), so each stays within 6 bones and UNITY plays them together;
   or a ruling that apex rigs may use up to 8 bones.

## 8. Order of work after LEAD's acceptance

Palette into v3 + the strip -> the floe strips -> the five flora (previews, the rig set) -> the deck backdrops + the
Hexagon overlay (slots) -> creatures 1-4 -> the ring chunks + the props that differ -> the Polar Hydra.
