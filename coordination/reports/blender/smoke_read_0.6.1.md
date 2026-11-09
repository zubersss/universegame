# B-228 · Art read of 0.6.1's player smoke (BLENDER) — PREP, written 2026-11-09 12:5x before the smoke

Source (when it lands): `coordination/reports/unity/smoke_0.6.1/` (U-194, ~79 shots). Read at 1:1 with the read tools only, no lock. Art defects only (wrong keys, v2 leftovers, seams, floating or sunk art, palette breaks, weapon-like or face-like reads, illegible ink); HUD layout goes to UNITY via LEAD. The 0.6.1 changes are read first, then every other shot for regressions.

## 1. The 0.6.1 changes (read first)

| Shot | What should show | Art | Check |
|------|------------------|-----|-------|
| smoke_1 | B-221's v3 title: Earth's camp at dusk, the Pilgrim on its pad, the smelter, crates and surveyor, the dug shaft with a ladder through the dashed Surface Line; the logo and four buttons over the calm left third | `ui/title/background` (ea3f75fb) | no v2 conifers / grey hull / pixel dirt; nothing busy behind the logo or buttons; the image unstretched (1920x1080) |
| smoke_18 | The built shelter walls seated on Mars's slope at night (was ~40 px afloat) | `props/common/shelter_wall`, `shelter_door` | each base on the drawn ground, no gap, no sinking past the foot |
| smoke_64 | Crafting with thruster Mk2's icon: a steel bell with a brass collar, before Mk3's red | `icons/thruster_mk2/base` (02462247) | not the flat teal square; reads at the panel's size beside mk1 / mk3 |
| smoke_65 / 66 | A new game digging with the shovel at camp: the shovel in the glove mid-swing, the flick tinted to the ground | `props/rig/shovel`, `fx/shovel_flick/base` (ab1c524f) | the D-grip in the hand (pivot), the blade toward the dig point, nothing weapon-like; the flick's clod arcs up and back, tinted brown on Earth |
| smoke_67 | The HUD tool slot: the shovel, then The Beam Mk1 after the buy | `icons/tools/shovel`; `icons/tools/beam` if B-227 exported before the build | reads at 48 px in the slot; the Beam a cutting emitter (D-087); a placeholder if B-227 missed the build (expected then, not a defect) |

## 2. The 0.6.0 findings (B-201): expected state in 0.6.1

| # | 0.6.0 finding | Expected in 0.6.1 | Why |
|---|---------------|-------------------|-----|
| 1 | Jupiter decks: vertical streaks below the floes | still open | B-220 / U-191 come after 0.6.1 |
| 2 | sea from below a flat grey-blue | fixed (0.6.0 release, U-188) | keep checking: no regression |
| 3 | a bear swimming in the sea | fixed (0.6.0 release) | no land animals or birds under water |
| 4 | a flat block under the floes, cap-to-cap gaps | still open | U-191 |
| 5 | the SURFACE LINE hint during the ship's climb | fixed (0.6.0 release: hints only on foot) | |
| 6 | mica_book read as a dark vent grate | fixed (b47759a4: a pale layered slab) | check T3 rooms |
| 7 | root_knot read as a spider | fixed (b47759a4: a pale root tangle) | check T2 rooms |
| 8 | Mercury / Venus stepped block terrain | still open | U-177 |
| 9 | "×1.00" into the skill tree's border | fixed (0.6.0 release) | |
| 10 | the v2 title scene | FIXED IN 0.6.1 (B-221) | smoke_1 |
| 11 | the unthemed 3D docking bay | still open | B-223 / U-192 after 0.6.1 (the v3 bay replaces the same keys) |
| 12 | thruster Mk2 a flat teal square | FIXED IN 0.6.1 (B-222) | smoke_64 |
| 13 | Mars canyon / Mercury twilight continue_rows not repeated | still open | U-191 |
| 14 | venus/deck without continue_rows | still open | B-220 (venus/deck included) / U-191 |
| 15 | the sky serpent in the pre-v3 style | still open | B-224 / U-192 |
| 16 | shelter walls floating on the slope | FIXED IN 0.6.1 (U-194) | smoke_18 |
| 17 | the catalogue's Camp without an icon | still open | B-223 (icons/catalogue/camp) / U-192 (IconOf has no Site branch) |

## 3. Every shot read

Read 2026-11-09 from 15:05, viewing only (no lock, no interpreter). "ok" = nothing wrong in the art at 1x.
**Which smoke each row is from.** UNITY respun the build for the shelter walls and its smoke overwrote the same folder
between 15:27 and 15:33. The "Smoke" column says: "first" = read before 15:07, certainly the first smoke (files 15:01-15:0x);
"first or respun" = read between 15:07 and 15:34, while the respin was writing, so I cannot say which file I saw (the two
builds differ only in BaseBuilder.Spawn, the shelter walls, so the art in these shots is the same); "respun" = read after
15:34. smoke_18 is read only from the respun smoke (LEAD 15:0x).
CORRECTION to the column: I wrote "first" on every row down to smoke_35 as I read them. That is certain only for smoke_1,
64-67 and 2 to 13; the rows smoke_14 to smoke_35 were read between 15:07 and about 15:30 and should read "first or respun".

| Shot | Smoke | Read |
|------|-------|------|
| smoke_1 menu | first | ok. B-221's title in the game, unstretched: the Pilgrim on its pad, the smelter, crates and surveyor, the shaft and ladder through the dashed Surface Line; the logo and four buttons over the calm left third |
| smoke_64 crafting | first | ok for the art: thruster Mk2 a pale steel bell, Mk3 a darker one, both in the tree and the recipe list. Two HUD text overlaps: F2, F3 |
| smoke_65 shovel mid-swing | first | ok. The slot shows the shovel's icon and SHOVEL; the shovel in the glove, blade low to the left of the surveyor in a round scoop; reads as a tool |
| smoke_66 shovel flick | first, then respun (the 4x crop, 15:36) | the flick's clod, tinted brown: ok. The raised tool beside the helmet IS a pickaxe: F1, settled at 4x |
| smoke_67 tool slot, the Beam | first | ok. B-227's Beam icon in the slot (a cutting emitter, no grip), BEAM MK1 under it; the Beam in hand; a round pocket dug below |
| smoke_2 earth day | first | ok for the art (the camp, the gull, the shovel at rest). The DIG DOWN card still draws the Beam (B-229, expected: 0.6.2) and covers the slot's name plate: F4. An empty bar at the top: F5 |
| smoke_2b depth | first | ok: strata, bones and an ammonite in the fill, no face read; the same card over the slot (F4) |
| smoke_2c bump | first | ok: the bump frame beside the wolf |
| smoke_3 earth night | first | reads as day (as 0.6.0's low-confidence note): F6 |
| smoke_3b earth dig | first | ok: the dug pocket with ore lumps at its top |
| smoke_3c ship airborne | first | ok |
| smoke_3d landing squash | first | ok |
| smoke_4 desert, the Launch Complex | first | ok: the teal gantry and the red ruin on the desert band; the SELL card over the slot's name plate (F4) |
| smoke_5 Mars canyon | first | the vertical streaks under the far ridge are 0.6.0's #13 (still open, U-191). New to my eye: a darker region with a stair-stepped edge across the canyon wall: F7 |
| smoke_6 Mars canyon, storm | first | as smoke_5; DUST STORM cue shown; no storm veil visible at this zoom |
| smoke_7 space, Saturn | first | Saturn's edge is stair-stepped and the disc has no bands or rings in view: F8 |
| smoke_8 inventory | first | ok; two neighbouring lumps read alike: F9 |
| smoke_9 crafting, page 1 | first | ok for the art (icons in the v3 set); the raw key again (F3) |
| smoke_10 waystation | first | the unthemed 3D bay: 0.6.0's #11, still open (B-223 / U-192). The market's list runs past the panel's bottom: F10 |
| smoke_11 catalogue | first | creature silhouettes read; Camp and two sites without icons: 0.6.0's #17, still open (B-223 / B-233 / U-192). One mineral's silhouette is a flat square: F11 |
| smoke_12 Warden outpost | first | ok: the pylon, the beacon, a Warden (a hovering lantern-bot, nothing weapon-like), all on the ground |
| smoke_13 Mercury day | first | ok for the art; the stepped terrain is 0.6.0's #8, still open (U-177) |
| smoke_14 Mercury twilight shelter | first | ok; the backdrop's hard edge with flat cream below (x 1445-1920, y 810) is 0.6.0's #13, still open (U-191) |
| smoke_15 shadewyrm burrow | first | ok; stepped terrain (#8) |
| smoke_16 Venus station | first | the sky serpent in the pre-v3 style: #15, still open (B-224 / U-192); the flat slab under the deck: #14, still open (B-220 / U-191); the rest ok |
| smoke_17 Venus vent | first | ok; stepped terrain (#8) |
| smoke_19 pause | first | ok |
| smoke_20 settings | first | ok for the art; a key named "Fire: LMB" in the space ship's list: F12 |
| smoke_21 title card, Earth | first | ok; a hint's arrow shows above the card: F13 |
| smoke_21 title card, Jupiter | first | ok; under it the flat block and the streaks (#1, #4, still open) |
| smoke_21 title card, Mars | first | ok; a hint's arrow sits on the tool slot's icon (F13); a pale flat square in the backdrop: F14 |
| smoke_21 title card, Mercury | first | ok |
| smoke_21 title card, Venus | first | ok |
| smoke_22 Mars hauler | first | ok: both hull halves sunk in the gouge, the cargo on its rim; the faint pale vertical streak in the mesa backdrop is 0.6.0's low-confidence note, unchanged |
| smoke_23 Jupiter floe kit | first | the flat block under the floes and the streaks below: #1 / #4, still open (U-191); the tortoise, the Pilgrim and the kit ok |
| smoke_24 Jupiter storm deck | first | as smoke_23 (#1 / #4); the painted storm deck ok |
| smoke_25 Jupiter deep, CRUSH | first | the CRUSH band reads; streaks below (#1) |
| smoke_26 Jupiter red spot, the whale | first | ok: the Vortex Whale overhead, the red floes; #1 / #4 below |
| smoke_27 climb boost | first | ok: the flame and the boost puffs |
| smoke_28 sound barrier | first | ok: the vapor cone in front, the shock ring behind, the speed lines |
| smoke_29 Earth camp curve | first | ok: the camp, the shovel held down to the ground, a dug pocket, bones and an ammonite in the fill |
| smoke_30 Earth hill | first | ok |
| smoke_31 Earth scoop | first | ok: the scoop's bowl, the dashed Surface Line and its pennants down the slope; a dark stepped smudge at the lower left (F7) |
| smoke_32 Earth tunnel | first | ok: the tunnel and its chamber inside the dig rim; the same smudge (F7) |
| smoke_33 Earth mound | first | ok: the built mound, the stag and the bear standing on the grass |
| smoke_34 Earth node, full | first | ok: the iron node's red crystals in its grey rock |
| smoke_35 Earth node, harvested | first | ok: the node worn down to rubble |
| smoke_36 Earth scan X | first or respun | ok: the red X on the ground, the buried pocket's marker, the copper node; a dark smudge at the lower right (F7) |
| smoke_37 Earth pocket dug | first or respun | ok: a U-bottomed shaft with crumbs on its floor, the red PACK FULL lettering under the readout |
| smoke_38 Earth desert | first or respun | ok: mesas, cacti, the sand fill, an iron node on the slope |
| smoke_39 Earth taiga | first or respun | ok |
| smoke_40 Earth tundra | first or respun | ok |
| smoke_18 Mars shelter, lamp | respun | the wall stacks now reach the ground at their uphill corner (0.6.0's #16: fixed as far as "floating" goes); a wedge of daylight stays under each stack's downhill corner: F16. The light is the day's (F6). The panels and the lamp ok |
| smoke_42 Earth forest valley | respun | ok |
| smoke_43 Earth sea | respun | the Hadal Maw at the beach in 2 m of water, its jaw drawn across the sand slope: F17. The water below the surface is a flat pale tint (B-225's shallows, coming) |
| smoke_44 Earth Survey Archive | respun | ok: the bunker door on the flat beside the funnel, the beacon, the rounded room below. The top bar reads "DEPTH 6 m · TOPSOIL" here, so F5's empty bar is this readout with nothing in it topside |
| smoke_45 Earth Launch Complex | respun | ok: the gantry and the ruin on their pads |
| smoke_41 Earth coast cliff | first or respun | ok for the art (the stone lip on the brink, shells in the sand). The sand fill and the soil fill meet in a soft upright band about 100 px wide where their strata do not line up: F15. Dark smudges at the lower left (F7) |

## 4. Findings

Owner = who would fix it. HUD layout items are listed for LEAD to route to UNITY; I do not judge them further.

| # | Shot | What | Where | Owner | Confidence |
|---|------|------|-------|-------|------------|
| F1 | smoke_66 | **The owner's first minute.** While the slot says SHOVEL, the surveyor swings a PICKAXE raised beside the helmet (4x crop: blender/preview/crop_b228_smoke66_4x.png, from the respun smoke): the v4 side_b sheet's dig frames have a pick baked into the hand (the frames props/rig/hand_socket.json flags held_b) and the shovel prop is hidden on them. Through each stroke the player sees the shovel low (smoke_65), then a pick swing. u193/2_shovel_flick caught a frame where the shovel shows | about (985, 790) | ROUTED by LEAD 15:4x as U-203 (Build 0.6.1b): no held_b frame during a shovel or Beam stroke. BLENDER's empty-handed dig clip only if UNITY finds no tool-free pose that reads | settled |
| F1b | smoke_66 (the same crop) | The flick's "ground lifting" ellipse and its clod draw at the surveyor's waist and knees, not at the dug cell under the feet; and the dig puff under the feet, tinted tan, is a round puff with two lobes on top that reads a little like a bear's head at 4x (B-184's puff, accepted; small at 1x) | (940-990, 800-860) | UNITY (the flick's anchor: its pivot is the dig point, [0.5, 0.25]); the puff: no action unless it reads so at 1x in play | medium / low |
| F2 | smoke_64 | Recipe rows with four ingredients: the fourth count runs into the station's name ("x 1BRICATOR", "x 4BRICATOR": Float cell Mk2, Jetpack Mk3, Thruster Mk3) | x 1500-1620 | UNITY | high |
| F3 | smoke_64 | The Float cell Mk2 blueprint tile prints a raw key ("after float_cell_mk1") and its icon sits on the text | (615, 425) | UNITY | high |
| F4 | smoke_2, 2b, 4 (any hint card) | The hint card covers the tool slot's name plate (SHOVEL hidden while a card shows); new with the slot | the card's top-left corner, (650-798, 163-187) | UNITY | high |
| F5 | smoke_2, 2b, 2c, 3, 3b, 3c, 3d, 4 | An empty paper bar with a small empty square at the top centre: it is the depth / tier readout (smoke_44 shows it filled: "DEPTH 6 m · TOPSOIL") drawn empty while topside. Reads as an unfilled placeholder | (790-1130, 17-48) | UNITY (hide it topside, or letter it "TOPSIDE") | medium |
| F6 | smoke_3 | "Earth night" has the day's sky and light | whole frame | UNITY (or the shot's staging) | medium |
| F7 | smoke_5, 6; also 31, 32 | A darker region of the fill ends in a stair-stepped edge: on Mars's canyon wall (steps about 180 px apart at that zoomed-out view), and as a dark smudge with stepped edges at the lower left of Earth's slope shots. It looks like the deeper tier's border following a stepped surface height instead of the slope | Mars: from (60, 380) to (1100, 1000); Earth: (0-350, 780-1080) | UNITY (the tier border on slopes) | medium |
| F8 | smoke_7 | Saturn's disc is the far disc scaled up: a stair-stepped ink edge, no bands; `planets/saturn` has no `disc_near` (Earth, Mars and Venus do) | the lower third | BLENDER (near discs for the giants: a card) | medium |
| F9 | smoke_8 | Two neighbouring item icons (slots 2 and 3, 999 and 210) read as the same pale blue-grey lump at inventory size | (637, 420), (729, 420) | BLENDER (tell me which items; one gets a clearer tone or mark) | low |
| F10 | smoke_10 | The market's goods list runs past the panel's bottom border: "Ring ice" straddles it, "Methane ice" is outside | y 1030-1080 | UNITY | high |
| F11 | smoke_11 | An unsurveyed Earth mineral shows a flat grey rounded square as its silhouette, where its neighbours show a cube or a pile: a missing or placeholder icon? | (610, 607) | UNITY to name the key; BLENDER if the icon is missing | medium |
| F12 | smoke_20 | The space ship's key list still names "Fire: LMB" (the lance is retired, D-087 / D-173) | the SHIP (SPACE) line | UNITY (text) | medium |
| F13 | smoke_21 Earth, Mars | A hint's pointing arrow shows over the title card's top edge (Earth, at 1245, 120) and sits on the tool slot's icon (Mars, at 723, 120) while its card is hidden | top centre | UNITY | medium |
| F16 | smoke_18 (respun) | Each shelter wall stack sits on the slope at its uphill corner; under the downhill corner a wedge of daylight shows, about 20 px (0.3 m) by eye at 1x on both stacks. A flat-footed wall on a slope would hide it if seated at the LOWEST ground under its foot (the uphill corner then sinks in) | left stack about (690-765, 715-740), right stack about (1155-1230, 635-657) | UNITY (BaseBuilder's foot); or BLENDER: a ragged skirt on the wall's bottom art that covers a 0.4 m wedge, if you prefer art | medium (not measured: no crop while UNITY holds the lock) |
| F17 | smoke_43 (respun) | The Hadal Maw, the deep-sea apex, floats at the beach in 2 m of water and its jaw is drawn across the sand slope (in front of the terrain where they overlap) | (1230-1500, 740-880) | UNITY (the smoke's staging, or its spawn depth and a keep-off-the-seabed rule) | medium |
| F15 | smoke_41 | Where two biome fills meet (sand / soil at the coast) the crossfade is a soft upright band about 100 px wide; the strata of the two fills do not line up, so it reads as a blurred vertical stripe through the cutaway | x 900-1000 and x 1380-1450 | UNITY (the crossfade's width or shape); BLENDER if a transition tile is wanted | low |
| F14 | smoke_21 Mars | A flat pale square floats in the backdrop behind the Pilgrim; it is in 0.6.0's shot too (I missed it there): an untextured sprite? | (1350-1395, 660-695) | UNITY to name the object; BLENDER if a key has no art | medium |
