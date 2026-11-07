# C2 Neptune design prep (B-161, BLENDER, 2026-11-07)

Basis: Bible 4.1 §7.5 (the cloud-column world type: the Datum, Decks 1-3, the Deep, the Crush Line as a dark band labelled
CRUSH), §7.9 Neptune ("the endgame": wind 8-20 m/s with gusts to 35, wind anchors needed to build, Cryo 3, gravity 1.14x,
Dark Storms: 400 m zones that drift, pull inward at 10 m/s and host the apex; Pressure, lightning, Thermal in the Deep;
Superionic Ice, the black "hot ice" in the Deep; the *Meridian* herself in the Great Dark Spot; Triton in the sky with its
geysers; Look: "deep indigo, white wisps streaking, a storm you can see breathing"), §9.1, §9.3 (faces only on creatures,
D-101; friendly or neutral, D-087), §9.8 (a "what makes it ours" line per creature), contract v3.1 §11 (+ `cycle_beats`,
D-127; Grand rigs <= 8 bones, D-140). The B-155 / B-157 / B-158 pattern is the base: the column scene builder, the capped
floe strips (D-137), the shared aerostat kit (B-156), straight-alpha layers (D-147), the light-independent wrap roll
(fe6ace98). Nothing here is exported.

## 0. State

| Item | State | File |
|---|---|---|
| Palette | PROPOSED, every check passing (table below) | blender/scripts/build_c2_neptune_palette.py |
| Five flora | designed below; drawings after the palette | build_c2_neptune_plants.py (next) |
| Floe strips | designed below (D-137's 10-frame contract) | build_c2_neptune_floes.py (next) |
| Deck backdrops | study notes below (FFT washes: a BLENDER slot) | build_backdrop_v3.py (next) |
| Creatures | the list below (none in Art yet: all new, no `replaces_v2`); the apex a Grand rig set | - |
| Props | the ones that differ, below (four v2 sprites in Art: `replaces_v2`) | - |

## 1. Palette (PROPOSED; checked by blender/scripts/build_c2_neptune_palette.py)

| slot | hex | role | mid | deep | contrast vs ink | chroma |
|---|---|---|---|---|---|---|
| offwhite | #E4E8EE | wisp white: the streaking cirrus wisps, floe rime, highlights (cold, never cream; the brightest colour) | #ADB1C3 | #7F83A0 | 14.1 | 3 |
| red | #C06A55 | beacon coral: the one warm accent - the Meridian's hull paint and beacon lamp, suit heaters, the anchor hooks | #945958 | #6F4B5B | 4.5 | 42 |
| mustard | #9E88B8 | storm violet: the Dark Storm's breathing rim, Superionic Ice glints, the Pressure phantom's core | #7C6E9E | #5F5888 | 5.5 | 28 |
| teal | #5A98B0 | wind cyan: the wind streaks' tint, methane floes, Windrider sails, Triton's geyser plumes | #4C7998 | #415F84 | 5.4 | 23 |
| green | #7C9E86 | abyss sage: Neptune flora (readable on the blue sky, the wisp white and the indigo) | #647D7B | #506271 | 5.8 | 19 |
| sky | #5E74AE | Neptune blue: the deck sky, darker and bluer than Uranus's fog | #4F6097 | #424F83 | 3.8 | 34 |
| brown | #2C3160 | deep indigo: the Deep, the Great Dark Spot's core and the shadow colour every mid / deep tone mixes toward | #2C3160 | #2C3160 | 1.4 | 31 |
| ink | #1E1A17 | ink, shared | - | - | 1.0 | 3 |

| check | result |
|---|---|
| every colour reads under the ink (contrast >= 2.0; the indigo is exempt: it is only a tone and the Deep) | pass |
| muted: no colour more saturated than Earth's most saturated accepted colour (chroma <= 59; Neptune max 42) | pass |
| distinct (closest pair mustard / sky at dE 19, >= 12) | pass |
| plants (abyss sage) read on the blue sky, the wisp white and the indigo (dE >= 20; min 36) | pass |
| a deep indigo shadow (hue 270-310 deg, b* < -20, L < 30; 294, -28.7, 22) and a Neptune-blue sky (hue 260-300 deg, b* < -20; 283, -33.4) | pass |
| cold white wisps, the brightest colour (b* <= 2; -3.4; brightest: offwhite) | pass |
| exactly one warm accent (warm + chroma > 20: ['red']) | pass |
| dimmer than Uranus (mean L of the lit colours 63 < Uranus's 70) | pass |
| told apart from Uranus (sky vs Uranus's fog dE 44 >= 25; shadow vs Uranus's slate dE 26 >= 12) | pass |
| the shadow tones stay inside the family (deep tones never black: L > 20) | pass |

All checks pass (ALL PASS). The sky is the darkest deck sky of the eight (L 49; Uranus's fog is L 76), so the ink outline
still reads on it (contrast 3.8) and the characters' fills (wisp white, coral) pop hardest of any planet: the endgame is
the moodiest scene without going muddy.

## 2. The wind and the breathing storm (Neptune's two ideas)

Neptune has the fastest winds in the solar system, and its Great Dark Spot (seen by Voyager 2 in 1989) was a dark oval
vortex edged with bright white companion clouds. In the art:

- **Everything streams one way.** Wisps are long, thin horizontal dry-brush streaks, never puffs; cloud banks are sheared
  into leaning anvils; floes are wind-carved (streamlined on the windward end, ragged on the lee). All drawn with the wind
  blowing +x (left to right). When a zone's wind blows -x, UNITY mirrors the deck layers and the floe sprites at runtime
  (§9.6: mirror by flipping, never a second drawing).
- **High cirrus casting shadows.** The real Voyager view: bright cirrus streaks high above the deck cast long shadows on
  the cloud tops below. Layer1 carries the deck's banks; layer2 carries the bright streaks with their soft indigo shadow
  strip painted onto the bank tops under them (the B-158 `Stack.paint` way: colour only, the layer's alpha untouched).
- **Plants lean, the drawing stays neutral.** Flora are drawn upright; the wind is a lean of the root bone that UNITY sets
  from the wind value (stronger gusts, deeper lean, a stepped shiver at 12 Hz), plus each plant's own gust reaction. One
  drawing serves calm and gale and both directions. (Proposal 1.)
- **The storm breathes.** The Dark Storm set's vortex rim (storm violet, with the white companion clouds) sits on its own
  layer so UNITY can pulse it - a slow scale 0.97-1.03 and alpha 0.85-1.0 over 8 beats - instead of drawn frames.
  (Proposal 2.)
- **One warm light in the dark.** Beacon coral appears only on the *Meridian* (her hull paint gone dusty, the beacon
  lamp), suit heaters and the anchor hooks: the player's eye is pulled to the wreck from across the storm.

## 3. Five faceless Neptune flora

All faceless (D-101): personality through motion; one Neptune rig set (`flora/neptune/rigset`, <= 6 bones each), `biomes`
per plant. At 1.14 g and in a gale they are low, anchored and streamlined, or they fly on tethers. Drawn 1.6x.

| # | Plant | Look | Motion (idle on the 110 bpm beat; react within 3 m) | Biomes |
|---|---|---|---|---|
| 1 | Kitebloom | a wind-cyan kite of a leaf with wisp-white ribs, flying on a long abyss-sage tether from a clenched root knot | the kite bobs and loops on the beat (the tether a rubber-hose chain); react: it reels in and folds flat against the root | deck1, deck2 |
| 2 | Gripweed | a low tangle of abyss-sage tendrils hooked over the floe's lee edge | the tendril tips flutter downwind; react: they clench tight and the tips curl in | every deck (the common plant) |
| 3 | Pipereed | a clump of hollow wind-cyan reeds with wisp-white mouths, cut at angles like organ pipes | the reeds bow in a travelling wave (phase-shifted per reed); react: they duck flat in a row | deck2, deck3 |
| 4 | Stormlantern | a storm-violet bulb on a short curled stem that glows faintly (a tone, not an emission map) | the glow swells and fades with the storm's 8-beat breath (swap); react: it dims and draws its stem in | storm, deck3 |
| 5 | Rimecomb | a stiff fan of wisp-white ice combs growing on Superionic floes, its spines tipped storm violet | rime flakes tick off its edge on the beat (swap); react: the combs snap shut like a folding fan | deep |

## 4. Floes

D-137's contract (8 tiles + cap_left + cap_right, 64 x 152, pivot on the ground line):
- `terrain/neptune/floe_strip_ice`: methane ice: a wisp-white rime lip over wind cyan, wind-carved facets sloping downwind,
  the windward cap rounded and the lee cap ragged (the caps differ per end already, so nothing new in the contract).
- `terrain/neptune/floe_strip_superionic`: the Deep's black hot ice: the deep indigo under a thin storm-violet crust,
  faceted, with a few violet glints (the resource reads at a glance; its glow is painted, no emission map).

Anchor worms coil over floe tiles (a creature, §6), so the floes need no anchor art of their own.

## 5. Deck backdrop studies (the column scene builder; FFT washes, so they run in a BLENDER slot)

Every deck: one set (no seasons, no lit variants); straight alpha (D-147); the wrap roll taken from the light-independent
geometry (fe6ace98) so a mirrored or pulsed layer never slides against its neighbours.
- **deck1:** Neptune-blue sky, long wisp-white streaks on layer2 with their shadows on the bank tops, Triton high on layer0
  (a small wisp-white disc with a storm-violet terminator and two thin dark geyser plumes bent downwind).
- **deck2:** denser wind-cyan banks sheared into leaning anvils; lightning as one storm-violet branched flash on layer1
  (UNITY flashes it: the flash ships as its own small sprite, `fx/neptune/lightning`, if LEAD wants it animated).
- **deck3:** the banks darken toward the indigo; Pressure-phantom country; the first diamond-rain glints (sparser than
  Uranus's, violet-tinted, on layer2).
- **deep:** deep indigo, Superionic floe silhouettes far off on layer0, the CRUSH band (the Saturn / Jupiter band).
- **storm (the Dark Storm zone, 400 m wide):** layer0 the indigo vortex core spiralling inward (the inward pull drawn as
  curved streaks), layer1 the storm-violet rim with the bright white companion clouds along its edge (UNITY pulses this
  layer), layer2 the near wind streaks curving into the eye. The Great Dark Spot is the same set with the *Meridian*'s
  silhouette far off on layer0 (one extra layer0 variant, `storm_meridian`).

## 6. Neptune creature list (contract §11.2; faces kept, no teeth)

None are in Art yet (`creatures/neptune/` was never exported in v2), so each is a new key.

| # | Creature (§7.9) | Role / habitat | Cartoon size at 1x | Clips | Notes; what makes it ours (§9.8) |
|---|---|---|---|---|---|
| 1 | Windrider | a sail-finned floater that surfs the gusts | ~2.2 m | idle 10 (a hover, sail canting), glide 12 at index 1, react 8 (sail furls, it tumbles away), bump 10 | a wind-cyan body, a tall wisp-white sail fin with cyan veins, pie eyes; ours: a fish that tacks like a sailboat, the sail its whole personality |
| 2 | Shadow shoal | small dark fish that dart in storms | ~0.5 m each (one sprite, UNITY spawns 5-9) | idle 8, swim 12 at index 1, react 8 (scatter), bump 10 | indigo bodies with a wind-cyan rim stroke and big wisp-white eye whites (they read on the dark by their eyes); ours: a shoal that swirls around the surveyor's helmet light, curious, never biting (D-087) |
| 3 | Pressure phantom | a translucent drifter of Deck 3 | ~1.8 m | idle 10 (a slow pulse), drift 12 at index 1, react 8 (veils wrap round it), bump 10 | wisp-white veils at partial alpha (straight, D-147) round a storm-violet core with the pie eyes inside it; ours: a shy ghost-jelly that hides behind its own veils |
| 4 | Anchor worm | holds floes against the wind | ~3 m | idle 10, crawl 12, anchored 10 (coiled over a tile, hook set, shivering), react 8 (lets go, recoils), bump 10 | a segmented abyss-sage body with a beacon-coral hook tail, pie eyes on a round head; the ground-line pivot; ours: a worm that lassos floes and digs in its heels against the gale |
| 5 | Umbral Leviathan (apex) | the Great Dark Spot, circling the *Meridian*; the final encounter is a full Survey (D-087) | a set piece, ~40 m (drawn at 0.25x like the Diamondback) | idle 12 (`cycle_beats` 4), circle 12 (a slow turn round the wreck), survey 12 (it holds and lights its bands one by one: the Survey beats), react 12 | a Grand rig set (D-140, 8 bones, `"grand": true`): head, three body segments, two fin pairs, tail, the band layer; deep indigo with storm-violet bands that breathe with the storm, wisp-white pie eyes, long whiskers that trail downwind, no teeth; ours: a storm-coloured whale-eel whose markings are the Survey puzzle |

## 7. Neptune props that differ

The v2 sprites in Art, each `replaces_v2` at export (removes `_normal`, `_mask`, `_emission`; never a `.meta`, D-016):
- `props/neptune/wind_anchor`: a brass stake with a beacon-coral cap, three guy lines pegged into the floe, a little wind
  sock on top (it bends with the wind lean like the plants).
- `props/neptune/meridian_wreck_bow | _mid | _stern`: the *Meridian* in three segments: a dusty beacon-coral hull with
  rivet seams, round portholes, a brass name ring on the bow, the beacon lamp on the stern (the final beacon, the ending
  choice). At PPU 64 a 4.4 m segment is only 282 px; proposal 3 makes each ~7.5 m (480 px, inside the 512 cap) so the ship
  reads as the expedition vessel, ~22 m whole.
- New: Triton and its geysers are sky art (backdrop), not props; the Superionic Ice drill site reuses the Rig's drill.

## 8. Proposals (for LEAD)

1. **Wind lean on the root bone (UNITY).** Neptune flora and the wind anchor's sock are drawn upright; UNITY bends the root
   bone by the local wind (0 at calm to ~25 deg at 35 m/s, a stepped 12 Hz shiver in gusts) and mirrors for -x wind. No
   extra frames; the 300-plant loop keeps one controller (D-110). Cost: a per-planet wind input on RigSetBuilder's driver.
2. **The breathing storm as a pulsed layer.** The storm set's layer1 (the rim + companion clouds) ships alone so UNITY
   pulses it (scale 0.97-1.03 and alpha 0.85-1.0 over 8 beats at 110 bpm, ~4.4 s); the Stormlantern's glow swap follows
   the same clock. No animated backdrop frames.
3. **A bigger *Meridian*.** The three wreck segments at ~7.5 m each (480 x ~300 px, PPU 64), so the final beacon reads as
   a ship, not a shed; the keys and the three-part split unchanged.

## 9. Order of work after LEAD's acceptance

Palette into v3 + the strip -> the two floe strips -> the five flora (previews, the rig set) -> the deck backdrops and the
storm set (slots) -> creatures 1-4 -> the props -> the Umbral Leviathan.
