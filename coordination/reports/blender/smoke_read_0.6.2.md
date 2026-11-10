# Art read of 0.6.2's player smoke (BLENDER) — PREP, written 2026-11-09 19:3x before the smoke

Source (when it lands): `coordination/reports/unity/smoke_0.6.2/`. Read at 1:1 with the read tools only (no lock, no
interpreter; a 4x crop only when the lock is free and LEAD has no job waiting). Art defects only (wrong keys, v2 leftovers,
seams, floating or sunk art, palette breaks, weapon-like or face-like reads, illegible ink); HUD layout goes to UNITY via LEAD.
The owner's page waits for this read (LEAD 19:2x). Order: section 1 first, then section 2's rows on their shots, then every
other shot for regressions. One row per shot in section 3, written as each is read; a finding gets a number (G1, G2, ...)
only when I can name the shot, the place in px and what is wrong.

"Expected" below is what the commits and LEAD's rulings say should show. It is not an observation: every row is open until
its shot is read.

## 1. The shots LEAD lists as changed since 0.6.1b (read first)

| Shot | What should show in 0.6.2 | Art / code | Check |
|------|---------------------------|------------|-------|
| smoke_10 waystation | The v3 docking bay: riveted cream panels under a brown truss, the brass porthole open onto Earth and Luna, BAY 2 and HALCYON FREIGHT, the hazard-striped cradle with the bay's two clamps, the railing and lamp in front. The Pilgrim stands on the cradle as its own sprite (not baked in). The market list inside its panel (F10) | B-223 (7a58e321), `backgrounds/waystation/layer0..2`, layer1.json's anchors; U-192; U-204 F10 | no 3D grey bay left; the ship's feet on the deck plate at the cradle's centre (x 660 of 1920), drawn once, in front of the clamps and behind the railing; the clamps' jaws beside the fins, not through them; nothing important under the market panel; the lettering sharp; no banding in the dark sky through the porthole |
| smoke_18 Mars shelter | The shelter walls seated on the slope with no wedge of daylight under the downhill corner (F16) | U-200 | both stacks: the foot meets the drawn ground along its whole width; the wall not sunk past its base line uphill |
| smoke_20 settings | The space ship's key list without "Fire: LMB" (F12) | U-204 F12 (287203a2) | text only; the panel's art unchanged |
| smoke_42 Earth forest valley | Two changes (LEAD 19:3x): no empty depth tag at the top centre while topside; the pack reset before the shot, so PACK reads empty, not 30 / 30 in red. The shovel in hand as in 0.6.1b | U-201 (4588b3f0, 0.6.1b); the smoke script's staging (rides 0.6.2's check) | no empty paper bar at the top centre; PACK's readout not red and not full; the valley's art as in 0.6.1b ("ok") |
| smoke_47 D1 first dig | The DIG DOWN card with the shovel in the surveyor's glove (B-229), the card clear of the tool slot's name plate (F4); the first scoop with the new dust and clods if the frame catches a stroke | B-229 (d7353cd6); U-204 F4 (d8282916); B-238 / B-232 (df2defa3) | the card's picture is the shovel, not the Beam; SHOVEL readable in the slot beside the card; the scoop's bowl round; any dust low and pale, in the soil's tone |
| smoke_54 D1 pack full | In the shaft: B-230's back wall behind every dug cell (the tier's own wall, one step darker than its fill, darker with depth), the rim's ink gradient on the dug edges, the tier border a line that follows the slope with a 0.35 m crossfade (F7); the card clear of the slot's name (F4) | B-230 (d9edc71e) + U-196 (3bcd5956); U-204 F4 | the wall reads as a hole behind the surveyor, not an opaque block and not the fill's flat copy; T1's wall with roots and worm holes, T2's with pebbles; no tile seam every 4 m; no face in the wall's marks at 1x; no blurred stair-steps at the tier border |
| smoke_55 D1 jetpack | As 54; no shovel held up like a flag while flying (F18) | U-204 F18 (287203a2) | the hands empty or the tool hidden on the jetpack; the flame and puffs as before |
| smoke_56 D1 ladder | As 54: the wall behind the ladder, the surveyor on the rungs | B-230 + U-196 | the ladder and the surveyor read against the darker wall; the far limbs not lost in it |
| smoke_57 D1 winch | As 54: the wall behind the winch line | B-230 + U-196 | the line readable on the wall |
| smoke_60 D1 skill tree | The selected node's description wrapped inside the detail panel (F19) | U-204 F19 (78befa5f) | text only; the 66 node icons as before |
| smoke_63 system map | The planet labels clear of their plates' lines (F20) | U-204 F20 (78befa5f) | each label readable, not struck through; the paper map, the cartouche and the discs unchanged |
| smoke_64 crafting | A four-ingredient row with its last count clear of the station's name (F2); the Float cell Mk2 tile without the raw key, its icon off the text (F3) | U-204 F2, F3 (78befa5f) | text and layout; thruster Mk2's steel bell as in 0.6.1 |
| smoke_65 shovel mid-swing | The shovel in the glove, blade toward the dig point; under it the dug cell with its back wall if the scoop is deep enough | U-203 (0.6.1b); B-230 | a tool, nothing weapon-like; the grip in the hand |
| smoke_66 shovel flick | NO pickaxe in the stroke (F1). The flick as a short lift of crumbs at the dig point (not at the waist: F1b); clods thrown from the opened cell, turning, landing and gone; the dust a low pale cloud at the cell's mouth behind them; all tinted by the fill's tone (brown-tan on Earth's topsoil) | U-203; B-238 + B-232 (df2defa3); U-195; D-190 with "tone_hex" (db44edd1) | at 4x if the lock allows: the hand holds the shovel through the stroke; the clods read first, the dust behind; the dust under 0.35 m tall and not a two-lobed head; no cream (untinted) puff or clod anywhere |

## 2. B-228's findings (0.6.1): expected state in 0.6.2

| # | 0.6.1 finding | Expected in 0.6.2 | Where to look |
|---|---------------|-------------------|---------------|
| F1 | a pickaxe swing in the shovel's stroke | fixed in 0.6.1b (U-203) | smoke_66 |
| F1b | the flick drawn at the waist; the old puff's two lobes | fixed: the flick at the dig point (U-195), the puff redrawn as low dust (B-238) | smoke_66, 47 |
| F2 | a fourth ingredient's count into the station's name | fixed (U-204, accepted on u204 captures) | smoke_64 |
| F3 | a raw key on the Float cell Mk2 tile | fixed (U-204) | smoke_64, 9 |
| F4 | a hint card over the tool slot's name plate | fixed (U-204, d8282916) | smoke_2, 2b, 4, 47, 54 |
| F5 | an empty depth bar topside | fixed in 0.6.1b (U-201) | smoke_2, 3, 4 |
| F6 | "Earth night" in the day's light | ruled (LEAD 19:3x): the shot is renamed for what it shows, the camp by day; night on the cartoon stage is a Backlog line. Expected: a day shot under a day name | smoke_3 |
| F7 | the tier border as blurred stair-steps | fixed: a 0.35 m crossfade that follows the surface (U-196) | smoke_5, 31, 32, 36, 41, 54-57 |
| F8 | Saturn up close: a stepped edge, no bands | still open (B-237 Blocked: a painted limb band with the giants' pass) | smoke_7 |
| F9 | two item icons alike at inventory size | no art fault (LEAD 19:3x): the smoke staged one item, Stone, in two stacks; UNITY now stages two different materials. Expected: two different icons | smoke_8 |
| F10 | the market's list past the panel's bottom | fixed (U-204) | smoke_10 |
| F11 | a flat grey square as a mineral's silhouette | CLOSED, no fault (LEAD 19:3x): it is icons/snow/base, the Snow tile's drop (a pale cube), shown as its own silhouette while unscanned | smoke_11 |
| F12 | "Fire: LMB" in the ship's key list | fixed (U-204) | smoke_20 |
| F13 | a hint's arrow over a title card | fixed (U-204, d8282916) | smoke_21 Earth, Mars |
| F14 | a pale flat square behind the Pilgrim on Mars | unknown (LEAD 19:3x): UNITY's probe of a loaded Mars did not find it; it looks for it in the smoke's own landing shot. If I see it again: its pixel box and the shot's name, and it becomes a card | smoke_21 Mars (0.6.1: about 1350-1395, 660-695) |
| F15 | a soft upright band where two biome fills meet | unchanged (Backlog, low; not in 0.6.2) | smoke_41 |
| F16 | a wedge of daylight under the shelter walls' downhill corner | fixed (U-200, accepted) | smoke_18 |
| F17 | the Hadal Maw at the beach in 2 m of water | fixed (U-204 F17: a hunting swimmer holds where the water is too shallow) | smoke_43 |
| F18 | the shovel held up like a flag on the jetpack | fixed (U-204) | smoke_55 |
| F19 | the node's description off the panel | fixed (U-204) | smoke_60 |
| F20 | the map's labels struck through by their plates | fixed (U-204) | smoke_63 |

The 0.6.0 findings (B-201) that were still open in 0.6.1, for the same read:

| # | Finding | Expected in 0.6.2 | Where |
|---|---------|-------------------|-------|
| 1, 4 | Jupiter decks: streaks below the floes, a flat block under them | B-220's continue bands are exported (109 files); open until U-191 reads them: not known to be in 0.6.2 | smoke_21 Jupiter, 23-26 |
| 8 | Mercury / Venus stepped block terrain | still open (U-177) | smoke_13, 15, 17 |
| 11 | the unthemed 3D docking bay | FIXED IN 0.6.2 (B-223) | smoke_10 |
| 13, 14 | Mars canyon / Mercury twilight / venus deck continue rows not repeated | as 1, 4 (U-191) | smoke_5, 14, 16 |
| 15 | the sky serpent in the pre-v3 style | fixed if the import of c5350eb1 is in the build: the soft veiled serpent, flat-inked, 4 m frame | smoke_16 |
| 17 | the catalogue's Camp without an icon | fixed if U-192's Site branch is in: the camp icon (the pad, crates, a lantern post). The ten other sites still without icons (B-233 is accepted but held until after 0.6.2) | smoke_11 |

New art in 0.6.2 with no shot named above, to look for wherever it appears: the dug fill's tone on dust and clods on Mars
(smoke_61 if a stroke shows); B-230's walls on Mars (smoke_61: T4's wall with glints on its seams); the rubble (fx/rubble/base)
is imported but waits for U-197, so none should show.

## 3. Every shot read

(to be filled when the smoke lands: Shot | Read)

## 4. Findings

(G-numbered; Shot | What | Where | Owner | Confidence)

## 5. Summary

(does the art of 0.6.2 hold; the first minute; the hole; what is left)
