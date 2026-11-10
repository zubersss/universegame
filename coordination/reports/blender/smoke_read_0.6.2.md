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

Read 2026-11-09 from 21:37 (the smoke's files 21:22-21:28, Build/MERIDIAN_0.6.2 written 21:20:51), with the read tool only,
at 1x. "ok" = nothing wrong in the art at 1x. Crops are named where one was cut; until then "not checked at 4x" stands.

| Shot | Read |
|------|------|
| smoke_66 shovel flick | ok, the first minute holds. No pickaxe (F1 fixed): the shovel in the hand, blade down at the scoop (1010, 895). Two tan clods in the air (1035, 855) and a small one (1058, 872), in the topsoil's tone; a small pale shape low in the scoop's mouth (1043, 912): the dust. The scoop shows B-230's Topsoil wall (a pale root line, two worm holes) inside a dark rim: a hole. Not checked at 4x |
| smoke_65 shovel mid-swing | ok: the shovel in the glove, blade at the scoop's rim; the wall in the bowl |
| smoke_47 first dig, DIG DOWN | ok: the card's picture is the shovel in the glove (B-229); SHOVEL's name plate readable above the card (F4 fixed); the first scoop's bowl with its wall |
| smoke_42 forest valley | ok: no empty depth tag (F5 / U-201); PACK 0 / 30 kg, not red; the shovel in hand; the valley's art as in 0.6.1b |
| smoke_10 waystation | The v3 bay is in and reads: panels, truss, the porthole with Earth and Luna, BAY 2, HALCYON FREIGHT, the railing and lamp; the market list inside its panel with PREV / NEXT (F10 fixed). **The cradle is empty: no Pilgrim anywhere (G1)** |
| smoke_54 pack full | ok: the back wall behind every dug cell (Topsoil's lighter wall with roots at the top, Subsoil's dark wall with pebbles), the surveyor reads against it; the tier border in the fill a clean line that follows the slope (F7 fixed); the card clear of the slot's name (F4). G2, G3 |
| smoke_55 jetpack | ok: no shovel held up (F18 fixed), the flame and a puff under the pack. G2, G3, G4 |
| smoke_56 ladder | ok: the ladder and the surveyor read on the wall. G2, G3 |
| smoke_57 winch | ok: the line reads down the shaft; Topsoil's wall with roots and worm holes at the top. G2 (clearest here), G3 |
| smoke_18 Mars shelter | Both stacks meet the ground along their feet, no wedge (F16 fixed at 1x). The day's light under the name "night_lamp". A dark spiky shape at the Beam's tip beside the surveyor (925-1000, 635-685): not identified at 1x (G5) |
| smoke_20 settings | ok: no "Fire: LMB" (F12 fixed) |
| smoke_60 skill tree | ok: the description wraps inside its panel (F19 fixed); the node icons as before |
| smoke_63 system map | ok: the labels clear in their plates (F20 fixed) |
| smoke_64 crafting | ok: the four-ingredient rows clear of FABRICATOR (F2 fixed); "after Float cell Mk1" on the tile (F3 fixed); thruster Mk2's steel bell |
| smoke_2 earth day | ok: the DIG DOWN card with the shovel picture, SHOVEL's plate readable above it (F4 fixed); no empty bar at the top centre (F5 fixed); the camp, the gull, the shovel at rest |
| smoke_2b depth | ok: the same card; bones and ammonites in the fill |
| smoke_2c bump | ok: the bump frame beside the wolf |
| smoke_3 camp by day | ok: the shot is named for what it shows (F6 as ruled) |
| smoke_3c ship airborne | ok |
| smoke_3d landing squash | ok for the squash. Under the surveyor a round scoop with its Topsoil wall whose mouth is closed by the grass band: G7 (low) |
| smoke_4 desert, Launch Complex | ok: the gantry and the ruin; the SELL card clear of the slot's name; PACK 30 / 30 in red (staged for the card) |
| smoke_5 Mars canyon | The tier border is a clean straight edge parallel to the slope (F7 fixed). The vertical streaks under the far ridge (x 1500-1700, y 640-1080): 0.6.0's #13, still open (U-191) |
| smoke_6 Mars canyon, storm | as smoke_5; the DUST STORM cue |
| smoke_7 space, Saturn | unchanged: the stepped edge, no bands (F8; B-237 Blocked) |
| smoke_8 inventory | ok: six different items, six different icons (F9: the staging fixed) |
| smoke_9 crafting, page 1 | ok |
| smoke_12 Warden outpost | ok |
| smoke_13 Mercury day | ok; stepped terrain (#8, U-177) |
| smoke_14 Mercury twilight shelter | ok; the backdrop's hard edge over flat cream at (1445-1920, 810): #13, still open |
| smoke_15 shadewyrm burrow | ok; stepped terrain (#8) |
| smoke_16 Venus station | **The new veil serpent is in** (#15 fixed): flat-inked, the veil along its back, a calm eye pair, a closed smile; it reads as a gentle drifter. It is drawn about 2.7x its art size (600 px long for 224): its ink line is about three times heavier than the station's and soft-edged: G6. The flat grey-green slab under the deck (y 950-1080): #14, still open (U-191) |
| smoke_17 Venus vent | ok; stepped terrain (#8) |
| smoke_19 pause | ok |
| smoke_21 title card, Earth | ok: no hint arrow over the card (F13 fixed) |
| smoke_21 title card, Mars | No hint arrow (F13 fixed). **The pale flat square is still there** behind the Pilgrim: (1342-1386, 660-692): G8 (was F14). A cluster of dark round blobs in the fill at (1815-1860, 965-1010): G9 (low) |
| smoke_21 title card, Jupiter | ok; under it the flat block and the streaks (#1, #4, still open: U-191) |
| smoke_21 title card, Mercury | ok |
| smoke_21 title card, Venus | ok |
| smoke_22 Mars hauler | ok |
| smoke_23 Jupiter floe kit | ok for the kit, the tortoise and the Pilgrim; #1 / #4 below |
| smoke_24 Jupiter storm deck | ok for the painted deck; the flat block under the floes and the streaks (#1 / #4) |
| smoke_25 Jupiter deep, CRUSH | ok: the CRUSH band reads; streaks below (#1) |
| smoke_26 Jupiter red spot, the whale | ok: the Vortex Whale overhead, the red floes; #1 / #4 below |
| smoke_27 climb boost | ok |
| smoke_28 sound barrier | ok: the vapor cone, the shock ring, the speed lines |
| smoke_29 Earth camp curve | ok for the camp. A closed round pocket under the grass with its Topsoil wall at (540-630, 700-785): G7 |
| smoke_30 Earth hill | ok |
| smoke_31 Earth scoop | ok: the scoop's bowl with its wall; the Surface Line and pennants; the tier border at the lower left a clean diagonal (F7 fixed) |
| smoke_32 Earth tunnel | ok: the tunnel and its chamber with the Topsoil wall (roots); the dashed Surface Line and a pennant drawn across the chamber; a small grey lump on its floor (1475, 828) |
| smoke_33 Earth mound | ok for the tunnel, the mound. Two bears stand in one spot and read as one two-headed animal at (1525-1655, 598-680): G11 (staging, low) |
| smoke_34 Earth node, full | ok |
| smoke_35 Earth node, harvested | ok |
| smoke_36 Earth scan X | ok: the red X, the buried pocket's marker, the copper node. A soft dark smudge with a reddish upper edge at the lower right (1500-1920, 980-1080): G12 |
| smoke_37 Earth pocket dug | ok: a U-bottomed shaft with its wall, three grey crumbs on its floor, PACK FULL in red. The same smudge (G12) |
| smoke_38 Earth desert | ok |
| smoke_39 Earth taiga | ok |
| smoke_40 Earth tundra | ok |
| smoke_41 Earth coast cliff | ok for the lip and the shells. The two fills still meet in soft upright bands at x 880-1000 and x 1380-1460 (F15, unchanged as expected). A dark brown soft-edged shape with peaks along the bottom left (0-1000, 930-1080): G12 |
| smoke_43 Earth sea | The Hadal Maw now holds off the shallows, half out of frame at the right (1810-1920, 580-900), no longer across the sand slope (F17 fixed). Its lure's glow sits at the water line (1720, 405). A red squid mid-water. The water under the surface is still a flat pale tint (B-225 was exported after this build). A dark soft-edged region at the lower left (0-330, 850-1080): G12 |
| smoke_44 Survey Archive | ok: the bunker, the beacon; the funnel and the room below show the Topsoil wall with roots throughout; "DEPTH 6 m · TOPSOIL" |
| smoke_45 Launch Complex | ok |
| smoke_46a-d downhill walk | ok: four walk frames, the feet on the ground line in each, the shovel carried |
| smoke_58 grapple reel | ok: the hook in a rock at the shaft's lip, the line to the hand, GRAPPLE in the slot; the fill's tier border a clean diagonal at the right (F7 fixed). G2 at the shaft's top (830-1090, 60-150), G3 at y 525 |
| smoke_59 sell | ok: the scroll, five item icons at list size. The closed round pocket under the grass (750-880, 905-1030): G7 |
| smoke_62 space, minimap | ok; the minimap's labels crowd each other as before (HUD, low) |
| smoke_67 tool slot, the Beam | ok: BEAM MK1 with its icon, the Beam in hand. The same closed pocket (750-880, 895-1030): G7 |
| smoke_11 catalogue | The creature and mineral silhouettes read. **Camp is surveyed ("Camp · SITE · 50 DC") and its icon slot is empty** at (1325-1375, 580-630), and the two unsurveyed sites show no silhouette: 0.6.0's #17 is still open in this build (icons/catalogue/camp is imported; the panel's Site branch is U-192). The grey rounded square at (585-635, 588-628) is icons/snow/base (F11, closed) |
| smoke_3b Earth dig | ok for the camp, the gull, the shovel raised. The pocket under the surveyor is a closed round disc under unbroken grass (790-910, 905-1025): G7 |
| smoke_1 menu | ok: the v3 title, the logo and four buttons over the calm left third |
| smoke_48 Surface Line | ok: the card, its arrow up at "DEPTH 2 m · TOPSOIL"; the shaft and the small scoop both show the Topsoil wall (roots, worm holes) inside a dark rim: holes |
| smoke_49 T1 room | ok: the room's Topsoil wall; the dashed Surface Line with its pennants; a dug tunnel at the upper left with its wall |
| smoke_50 T2 room | ok: the Subsoil wall, dark with pebbles; the twig mark at (760, 775) |
| smoke_51 T3 room | ok: the Stone wall, dark grey with strata lines and cracks |
| smoke_52 T4 room | ok: the Deep wall, dark teal with gold seams |
| smoke_53 T5 room | ok: the Core wall, black with dark-teal glass veins |
| smoke_61 Mars T4 room | ok: Mars's Deep wall (dark brown, pale angular seams). A small red mark sits on the PACK bar at (1265-1285, 33-43) with the pack at 0 / 30: G10 (HUD, low) |

## 4. Findings

Owner = who would fix it. Boxes are px at 1x as (x0-x1, y0-y1). None was checked at 4x: UNITY held the lock through the
read (21:37 on); the crops I owe are listed under the table.

| # | Shot | What | Where | Owner | Confidence |
|---|------|------|-------|-------|------------|
| G1 | smoke_10 | **The bay's cradle is empty.** The v3 bay is in, but no Pilgrim stands on the cradle: B-223 took the ship out of layer1 (LEAD's ruling) and the game does not yet place its sprite on layer1.json's "ship_ground". The player has just docked and their ship is not in its bay | the cradle and clamps (440-880, 690-940) | RULED by LEAD 21:4x: the page says so; U-192 places the ship next build. layer1 stays as exported | settled |
| G2 | smoke_54-58 | Inside a shaft the back wall's Topsoil / Subsoil border dips in a V about 1 m deep at the shaft's centre, while the fill's border outside follows the slope as a straight line | smoke_57: (850, 255) down to (975, 315) and up to (1100, 270); smoke_58: (830-1090, 60-150); the same at the top of 54-56 | UNITY (U-205 part 3, LEAD 21:4x): the wall's tier depth is taken from the dug surface (the shaft's own floor line) instead of the Surface Line the fill uses | high that it is there; the cause is my guess |
| G3 | smoke_54-58 | A hard horizontal step in the wall's darkening crosses the shaft at one depth: lighter above, darker below, a straight edge the width of the shaft | smoke_54 / 55 / 56 / 58: y 525; smoke_57: y 690 | UNITY (U-205 part 3): the depth darkening or the ambient changes in one step there (a chunk border or a clamp) | medium |
| G4 | smoke_55 (any tall shaft) | The wall tile's 4 m repeat shows down a tall shaft: the same grey pebble sits at x 883 every 256 px | smoke_55: (883, 270), (883, 527), (883, 783) | UNITY (U-205 part 3) for a cheap answer: offset the wall's u by a per-column or per-4 m-row hash, or mirror every other repeat. In the ART it would take a second variant tile a tier (20 more tiles, about 800 KB) or an 8 m tile (4x the pixels): I do not recommend either for a low finding; the T2 pebbles could instead be drawn smaller and more of them, so no single one is a landmark (one re-export of four tiles) | medium that a player notices it |
| G5 | smoke_18 | A dark spiky shape stands at the Beam's tip beside the surveyor; LEAD saw it in 0.6.1's smoke_18 too. Not identified at 1x: a Mars plant, a spark burst or the dust | (925-1000, 635-685) | BLENDER: a 4x crop when the lock is free, then a name | open |
| G6 | smoke_16 | The new veil serpent is drawn about 2.7 times its art size (about 600 px long on screen; the sheet draws it 224 px long at 64 px per metre), so its ink line is about three times heavier than the station's beside it and its edges are soft. It reads as a gentle drifter, which is the card; the line weight does not match | the serpent (790-1400, 410-580) | UNITY / LEAD: the creature's scale (the manifest row's note says "artScale 3 as before": the v2 sheet was 400 px at 103 px per metre). Either the game draws it at 1x (a 3.5 m serpent) or, if a 10 m serpent is wanted, BLENDER redraws the sheet at that size with the line at 1x (a 640 px frame; a card) | high that the line is heavy; which answer is LEAD's |
| G7 | smoke_3b, 3d, 29, 59, 67 | At the camp the staged "dug pocket" is a closed round disc under unbroken grass: with B-230's wall and the rim shadow inside it, it reads as a buried cracked boulder, not a hole (in 0.6.1 it was a flat darker patch). A player's own dig opens the surface (smoke_31, 37, 47, 65), so this is the smoke's staging, or a pocket carved under the grass band without opening it | smoke_3b: (790-910, 905-1025); smoke_29: (540-630, 700-785); smoke_67: (750-880, 895-1030) | UNITY: the staging (dig from the surface), or draw no wall where a carved cell has no opening above it | medium |
| G8 | smoke_21 Mars | The pale flat square is still behind the Pilgrim (0.6.1's F14; UNITY's probe of a loaded Mars did not find it) | (1342-1386, 660-692) | UNITY to name the object (LEAD 19:3x: with its box and shot it becomes a card); BLENDER if a key has no art | high that it is there |
| G9 | smoke_21 Mars | A cluster of dark round blobs in the fill at the lower right, like a bunch of berries; not in my notes for 0.6.1 | (1815-1860, 965-1010) | not identified at 1x: a buried detail of Mars's fill (mine: then it wants a lighter tone) or a debris cluster. A 4x crop when the lock is free | low |
| G10 | smoke_61 | A small red mark sits on the PACK bar's right end while the pack reads 0 / 30 kg | (1265-1285, 33-43) | UNITY (HUD) | low |
| G11 | smoke_33 | Two bears stand in one spot and read as one two-headed animal | (1525-1655, 598-680) | UNITY (spawn spacing or the smoke's staging) | low |
| G12 | smoke_36, 37, 41, 43 | A dark soft-edged region low in the frame: in 36 / 37 a smudge with a reddish upper edge at the lower right, in 41 a brown shape with peaks along the bottom left, in 43 a dark wedge at the lower left. It is F7's old look (soft, stepped); F7 itself is fixed where the tier border shows as a clean line (smoke_5, 31, 54-58) | smoke_36 / 37: (1500-1920, 980-1080); smoke_41: (0-1000, 930-1080); smoke_43: (0-330, 850-1080) | UNITY: a second darkening that still follows a stepped surface height (my guess: the depth ambient or the next tier's border under a steep or carved surface) | medium that it is one cause |

### The four crops (cut 21:51 when the lock was free; viewed 21:5x) and LEAD's routing (21:5x)

Build 0.6.2 went out on this read (LEAD 21:5x, USER-41). Routing: G1 on the page; G2, G3, G4, G7, G9, G10, G11, G12 →
U-205 part 3 (G4: UNITY breaks the repeat; no art change unless a landmark is left); G6 ruled: the serpent is drawn at 1x of
its sheet (a 3.5 m serpent), on U-192, no redraw; G8 = U-206; #17 = U-192's Site branch with the eleven icons.

| # | Crop | What it shows |
|---|------|---------------|
| G5 | blender/preview/crop_smoke062_18_shape_4x.png (smoke_18, 860-1060 x 600-720, 4x) | Two small ground objects side by side behind the Beam's tip: a dark brown rounded lump (about 42 px wide at 1x) and a tan mound with a pointed top and dark zigzag grooves (about 62 px wide). Both are drawn SOFT: their edges step in blocks of 4-5 px at 1x, while the surveyor, the Beam and the lamp post beside them are crisp. They are not a plant, a spark or the dust (the new dust is a pale scalloped cloud, and LEAD saw the shape in 0.6.1). My reading: two of Mars's surface decor pieces (the set is rock_a, ventifact, dust_ripple, frost_patch, pebbles, rock_b: a rock and the grooved ventifact fit) drawn from a low-resolution copy of their texture (a low mip, or a small sprite scaled up). The same decor is crisp in smoke_21 Mars. Nothing weapon-like, no face. Owner: UNITY to name the two objects at that spot and why they draw soft. Confidence: high that they are soft; medium on which pieces they are |
| G8 | crop_smoke062_21mars_square_4x.png (smoke_21 Mars, 1300-1430 x 630-720, 4x) | A plain cream rectangle, 44 x 32 px at 1x, hard-edged, with paper grain, no ink and nothing on it, over the far ridge. LEAD 21:5x: cause found (U-206: the camp gull spawned on every planet's stage), fixed for the next build |
| G9 | crop_smoke062_21mars_blobs_4x.png (smoke_21 Mars, 1790-1880 x 940-1030, 4x) | Seven dark round balls in a cluster with one loose beside it, each with a small grey highlight. NAMED: it is my own buried detail, terrain/mars/fill_decor_3 ("blueberries_a": hematite spherules, 7 in a cluster with a glint each; build_ground_v3.FILL_DECOR), where the fill's scatter put it. No fault in the key. Two art notes on it: at 1x it reads as a bunch of dark grapes more than as mineral beads, and it is soft at 4x where the fill's own pebbles are crisp. If LEAD wants it clearer: a lighter hematite tone and a firmer ink ring (one re-export of two 64 / 48 px pieces). Low |
| G6 | crop_smoke062_16_serpent_2x.png (smoke_16, 780-1420 x 400-590, 2x) | The serpent's outline is 5-6 px wide at 1x and soft-edged; the station's rigging lines crossing behind it are about 1 px and crisp. The head reads well (the eye pair, the closed smile, the cream belly). Confirms G6: the sheet is being scaled up about 2.7x. Ruled: 1x on U-192 |

## 5. Summary (21:5x, all 79 shots read at 1x)

**Does the art of 0.6.2 hold? Yes. First hour: go.**

- **The first minute holds.** No pickaxe: the shovel is in the glove through the stroke (smoke_65, 66; LEAD's 4x crops agree).
  Clods fly in the topsoil's tone with a pale low dust at the bowl; the DIG DOWN card shows the shovel and no longer covers the
  slot's name; no empty depth bar topside.
- **The hole reads as a hole.** B-230's walls are behind every dug cell at every tier (smoke_47-58, 31, 32, 37, 44, 61 on
  Mars): Topsoil's roots and worm holes, Subsoil's pebbles, Stone's strata, Deep's seams, Core's glass veins, each darker than
  its fill inside a dark rim. No face read in any wall at 1x.
- **B-228's findings:** fixed and seen fixed: F1, F1b, F2, F3, F4, F5, F6 (renamed), F7 (where the border is a line), F9
  (staging), F10, F12, F13, F16, F17, F18, F19, F20. Closed: F11. Unchanged as expected: F8 (Saturn up close), F15. Still
  there: F14 (now G8, with its box).
- **The 0.6.0 list:** #11 fixed (the v3 bay; its cradle empty: G1, ruled for the page), #15 fixed (the veil serpent; its scale:
  G6). #17 still open in this build (Camp without its icon: the panel's Site branch is U-192). #1, #4, #8, #13, #14 open as
  expected (U-191, U-177).
- **12 findings (G1-G12).** For the page: G1. For UNITY's next build: G2, G3, G4 (the walls inside a shaft: U-205 part 3), G7
  (the staged closed pocket), G12 (F7's residue), G6 (the serpent's scale), G8, G10, G11. For BLENDER: the crops for G5, G8,
  G9, G6 when the lock is free; G4's art answer only if LEAD wants it (smaller, more numerous T2 pebbles).
- **Not checked:** nothing at 4x by me (the lock was UNITY's throughout); motion (stills only); the sea from below (no shot
  under the surface; B-225 is not in this build).
