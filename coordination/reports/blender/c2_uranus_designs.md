# C2 Uranus design prep (B-158, BLENDER, 2026-11-07)

Basis: Bible 4.1 §7.5 (the cloud-column world type: the Datum, Decks 1-3, the Deep, the Crush Line as a dark band labelled
CRUSH), §7.8 Uranus ("the sideways winter": Cryo 3, gravity 0.89x, dim light at 0.25 of the clamp; seasons: the lit
hemisphere is one half of the world's x range and swaps every 6 game days, the dark half Cryo 3 even with Mk3; methane
hail; Diamond rain below Deck 3; Miranda's ice geysers in the sky; Look: "featureless cyan fog that reveals bands only with
the Survey module; dim; crystalline sparkle below"), §9.1, §9.3 (faces only on creatures, D-101; friendly or neutral,
D-087), contract v3.1 §11 (+ `cycle_beats`, D-127; Grand rigs <= 8 bones, D-140). The B-155 / B-157 pattern is the base: the
column scene builder, the capped floe strips (D-137), the shared aerostat kit (B-156). Nothing here is exported.

## 0. State

| Item | State | File |
|---|---|---|
| Palette | proposed; the check (the Mars checks + Uranus' family) passes, below | blender/scripts/build_c2_uranus_palette.py |
| Five flora | designed below; drawings next | build_c2_uranus_plants.py (next) |
| Floe strips | designed below (D-137's 10-frame contract) | build_c2_uranus_floes.py (next) |
| Deck backdrops | study notes below (FFT washes: a BLENDER slot) | build_backdrop_v3.py (next) |
| Creatures | the re-ink list below (four v2 models: `replaces_v2`; the apex a Grand rig set) | - |
| Props | the ones that differ, below | - |

## 1. Palette (proposed; checked by blender/scripts/build_c2_uranus_palette.py)

| slot | hex | role | mid | deep | contrast vs ink | chroma |
|---|---|---|---|---|---|---|
| offwhite | #E3ECE9 | ice white: floe tops, frost, the crystalline sparkle, highlights (cold, never cream) | #ADB8B8 | #7F8C90 | 14.4 | 4 |
| red | #C27A4A | ember amber: the one warm accent - the Frostwisp's warmth, suit heaters, the beacon lamp | #966849 | #715848 | 5.1 | 44 |
| mustard | #ABAF86 | methane sage: the faint methane bands (Survey only), pale lichen, old brass gone cold | #868D73 | #667063 | 7.6 | 22 |
| teal | #5E9FA5 | methane cyan: the fog's dense banks, Methane rays, the dominant cool | #508289 | #446971 | 5.7 | 21 |
| green | #7E9A80 | frost mint: Uranus flora (readable on the fog, the ice white and the slate) | #667E6F | #526761 | 5.6 | 18 |
| sky | #9CC2C2 | cyan fog: the deck sky, dim and featureless | #7B9A9D | #60797E | 9.0 | 13 |
| brown | #2E3D47 | night slate: the dark half of the world and the shadow colour every mid / deep tone mixes toward | #2E3D47 | #2E3D47 | 1.5 | 9 |
| ink | #1E1A17 | ink, shared | - | - | 1.0 | 3 |

| check | result |
|---|---|
| every colour reads under the ink (contrast >= 2.0; the slate is exempt: it is only a tone and the dark half) | pass |
| muted: no colour more saturated than Earth's most saturated accepted colour (chroma <= 59; Uranus max 44) | pass |
| distinct (closest pair mustard / green at dE 15, >= 12) | pass |
| plants (frost mint) read on the cyan fog, the ice white and the slate (dE >= 20; min 21) | pass |
| a cyan fog (hue 180-230 deg, b* < 0; 198, -4.2) and a cold white (b* <= 2; 0.4) | pass |
| exactly one warm accent (warm + chroma > 20: ['red']) | pass |
| dimmer than Saturn (mean L of the lit colours 70 < Saturn's 72) and a cold slate (b* < 0; -8.1) | pass |
| the shadow tones stay inside the family (deep tones never black: L > 20) | pass |

All checks pass (ALL PASS).

## 2. The sideways light (Uranus' one idea)

Uranus lies on its side, so its low sun wheels around the horizon instead of crossing the sky, and the shadows turn
slowly through the day. In the art:

- **One warm source, low and sideways.** The ember amber is used only for warmth (the Frostwisp, heaters, the beacon
  lamp, the low sun's rim light) - never as a band or a fill. Everything else is the cyan-white family.
- **Long shadows that point along x.** Lining (the backdrop helper) is drawn on the sun's side only - left in the lit
  half's morning, right in its evening - so the same scene ships as two lit variants (`sun_left`, `sun_right`); UNITY
  cross-fades them across the season's 6 game days. The dark half is a third variant (`night`): the night slate, no lining,
  only the crystalline sparkle.
- **Featureless fog.** The methane-sage bands exist in the art but at a very low opacity (a tint over the fog); UNITY lifts
  them when the Survey module is on (a second, banded layer0, `survey`, of the same scene).
- **Crystalline sparkle below.** Diamond rain under Deck 3: tiny four-point ice-white sparkles as tones on the near
  layer, denser deeper.

## 3. Five faceless Uranus flora

All faceless (D-101): personality through motion; one Uranus rig set (`flora/uranus/rigset`, <= 6 bones each), `biomes`
per plant. At 0.89 g and in the dim light they are tall and thin, with pale tips that catch what light there is. Drawn 1.6x.

| # | Plant | Look | Motion (idle on the 110 bpm beat; react within 3 m) | Biomes |
|---|---|---|---|---|
| 1 | Sunturner | a tall frost-mint stalk whose cupped ice-white head always faces the low sun | the head turns toward the light (swap: left / up / right) on the beat; react: it folds its cup shut | lit decks |
| 2 | Fogbell | a cluster of cyan bells that ring silently; condensed fog drips from their lips | the bells swing (a chain, like the Sulphurbell); react: they close | deck1, deck2 |
| 3 | Hailcatch | a low frost-mint basin plant with a cupped ice-white bowl that collects hail | idle: hail pebbles settle (swap); react: the bowl tips and spills | deck2 |
| 4 | Embermoss | a dark-half moss with a faint ember-amber glow at its heart (the one warm flora) | the glow breathes (swap, a tone); react: it dims and curls | the dark half |
| 5 | Prismfern | a stiff fern of faceted ice-white fronds below Deck 3, where the diamond rain falls | the fronds glint (swap); react: they clatter flat | deck3, deep |

## 4. Floes

D-137's contract (8 tiles + cap_left + cap_right, 64 x 152, pivot on the ground line): `terrain/uranus/floe_strip_ice`
(methane ice: an ice-white frost lip over methane cyan, facets) and `terrain/uranus/floe_strip_dark` (the dark half's floe:
night slate under a thin ice-white rime, a few sparkles).

## 5. Deck backdrop studies (the column scene builder; FFT washes, so they run in a BLENDER slot)

- **deck1 / deck2 (the lit half):** the cyan fog with barely-there methane bands, soft fog banks with lining on the sun's
  side only (`sun_left` / `sun_right`), the low ember sun as a rim glow at one edge of layer0, Miranda (a small cream-grey
  disc with a geyser plume) high in the sky.
- **deck3:** denser methane-cyan banks, hail streaks on layer2.
- **deep:** the night slate, the diamond-rain sparkle on layer2 above the CRUSH band (the Saturn / Jupiter band).
- **dark (the dark half):** night slate fog, no lining, sparkles and a faint ember glow from distant Embermoss.

## 6. Uranus creature re-ink list (contract §11.2; faces kept, no teeth)

| # | Creature (§7.8) | Role / habitat | Cartoon size at 1x | Clips | Notes |
|---|---|---|---|---|---|
| 1 | Frostwisp | luminous; leads you to warmth or danger | ~0.8 m | idle 10 (a hover with a flicker), drift 12 at index 1, react 8 (darts away), bump 10 | `replaces_v2`; pivot at the centre; an ice-white wisp with an ember heart (a tone), pie eyes |
| 2 | Methane ray | glides between floes | ~2.2 m wingspan | idle 10, glide 12 at index 1, react 8 (a dive), bump 10 | `replaces_v2`; methane-cyan back, ice-white belly |
| 3 | Hailcrab | its shell catches diamonds | ~1.0 x 0.6 m | idle 10, walk 12, react 8 (shell up as a shield), bump 10 | `replaces_v2`; a floe walker (the ground-line pivot); claws wave, never pinch (D-087); diamonds glinting on its shell |
| 4 | Tiltbird | migrates with the season | ~1.4 m wingspan | idle 10, fly 12 at index 1, react 8, bump 10 | `replaces_v2`; flies tilted (its body leans with the planet), a frost-mint crest |
| 5 | Diamondback Colossus (apex) | armoured in diamond at the rain layer; only its joints take damage | a set piece | idle 12 (`cycle_beats` 4), reach 12 (a joint shows), react 12 | a Grand rig set (D-140, up to 8 bones): body, neck, head, two arms with the joint parts that UNITY highlights |

## 7. Uranus props that differ

The v2 models in Art, each `replaces_v2` at export: `props/uranus/umbrella_platform` (a diamond-rain catcher: a ribbed
ice-white canopy on a brass mast over a float) and `tilted_derelict` (the Uranus beacon on a tilted *Meridian* hull, an
ember beacon lamp). New: ice geyser vents for the Miranda-facing decks are sky art (backdrop), not props.

## 8. Proposals (need a ruling)

1. **Lit variants per scene:** each Uranus deck exports as `sun_left`, `sun_right` and `night` sets (three times the
   backdrop files of a Jupiter deck; ~2 MB each), plus one `survey` layer0 per deck; UNITY cross-fades them with the
   season. The alternative is one set with the lining on both sides (cheaper, but the sideways light is the planet's
   whole idea).

## 9. Order of work after LEAD's acceptance

Palette into v3 + the strip -> the floe strips -> the five flora (previews, the rig set) -> the deck backdrops and their lit
variants (slots) -> creatures 1-4 -> the props -> the Diamondback Colossus.
