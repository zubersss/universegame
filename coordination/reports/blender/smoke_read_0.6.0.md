# B-201 · Art read of 0.6.0's dev-player smoke (BLENDER, 2026-11-09 00:5x)

Source: `coordination/reports/unity/smoke_0.6.0/` (75 shots). Read at 1:1 with the read tools only (UNITY held the lock for the release). Art defects only: wrong keys, v2 leftovers, seams, floating or sunk art, palette breaks, weapon-like or face-like reads, illegible ink. HUD layout is with UNITY already (the pack readout, the PACK FULL cue under the medallion, the hint arrow over the card text) and is not repeated here. smoke_58 (grapple) re-shoots.

## Defects

| # | Shot | Defect | Owner |
|---|------|--------|-------|
| 1 | smoke_23, smoke_25 (Jupiter decks) | Vertical streaks fill the view below the floes (a layer's bottom row stretched down). The giants' deck backdrops carry no `continue_rows` (e.g. `backgrounds/jupiter/deep/deep.json`), so there is nothing to tile below them: D-169 gave the surface sets a tileable bottom band, never the decks. | BLENDER + UNITY: I add D-169-style tileable bottom bands (`continue_rows` 64) to the giants' deck layers; UNITY repeats them below. LEAD to route. |
| 2 | smoke_43 (the sea from below) | At −2 m the water is a flat grey-blue: no sign of B-202's `backgrounds/earth/sea_under` (light under the surface, the wavy surface band, rock arches, kelp). | UNITY (U-171: the underwater set not shown, or tinted flat) |
| 3 | smoke_43 | A brown bear swims underwater beside the shark and the squid (a land creature in the sea). | UNITY (creature placement) |
| 4 | smoke_23, smoke_25 | Under the floe a flat rectangular block stands where B-177's rounded `island_belly` belongs; the floe segments show cap-to-cap gaps. | UNITY (floe assembly) |
| 5 | smoke_27 (climb boost) | THE SURFACE LINE hint card shows during the ship's climb at 54 m AGL. | UNITY (hint trigger) |
| 6 | smoke_51 (T3 Stone) | `fill_decor_t3` "mica_book" reads as a dark vent grate at 1x (about 1490,408 and 15,925). | BLENDER (lighten it to silvery layered sheets) |
| 7 | smoke_50, 54, 56, 58 (T2 Subsoil) | `fill_decor_t2` "root_knot" (a small dark knot with radiating roots) can read as a spider at 1x (e.g. smoke_50 at 760,775). | BLENDER (a paler, looser root tangle) |
| 8 | smoke_13, smoke_17 (Mercury, Venus) | Stepped block terrain with the old strip crust, not smooth ground. Possibly intended for those scenes; noting it in case. | UNITY (terrain mode), if not intended |
| 9 | smoke_60 (skill tree) | "×1.00" runs into the panel's right border. | UNITY (layout; minor) |

## Every shot read (first pass)

| Shot | My art in frame | Read |
|------|-----------------|------|
| 47 first dig | hints/dig_down (+ mouse), gauges, Earth ground, the dug pit | OK |
| 48 surface line | hints/surface_line, hints/arrow aimed at the depth tag, shaft | OK |
| 49 T1 room | Earth T1 fill, fill decor (shell, bone, water lenses), the Surface Line with pennants | OK |
| 50 T2 room | ground_fill_t2, clay concretions, rusty nodules, root_knot | #7 |
| 51 T3 room | ground_fill_t3, geodes, crystal sprays, mica_book | #6 |
| 52 T4 room | ground_fill_t4, graphite lenses, glow nodule, obsidian shard, gold seams | OK |
| 53 T5 room | ground_fill_t5, kimberlite diamonds, magma pockets, ember cracks | OK |
| 54 pack full | hints/pack_full (the stamp), T2 | HUD layout only (UNITY's) + #7 |
| 55 jetpack | the jetpack's flame and puffs, the tool at the hand | OK |
| 56 ladder | props/dig/ladder + ladder_bottom, climb_ladder | OK + #7 |
| 57 winch | reel_up on the line in the shaft | OK |
| 58 grapple | (re-shoots) | - |
| 59 sell | ui/panels/scroll, item icons | OK |
| 60 skill tree | the chart, hub, node icons, emblems, rank pin, expedition rosette, cost tag | #9 (layout) |
| 61 Mars T4 | Mars ground_fill_t4 and its decor | OK |
| 62 minimap | ui/map frame, discs, tags, rim arrows, ship | OK |
| 63 system map | system panel, cartouche, discs, tags, suns, compass rose | OK |
| 43 sea | coast sand strata, shells | #2, #3 |
| 34 node full | node_iron on the turf | OK |
| 37 pocket dug | node_copper, the dug pocket, the Surface Line | OK |
| 38 desert | ground_band_sand, sand fill, node_iron, the B-179 desert | OK |
| 40 tundra | ground_band_snow, the tundra backdrop | OK |
| 41 coast cliff | the stone lip band, sand / soil fills, shells, the Surface Line | OK |
| 13 Mercury day | solarite nodes, the day backdrop | #8 (terrain mode) |
| 17 Venus vent | vent harvester, the surface backdrop | #8 (terrain mode) |
| 23 Jupiter floe kit | floe_strip_ice, the storm deck backdrop | #1, #4 |
| 25 Jupiter deep | the CRUSH band, floes | #1, #4 |
| 8 inventory | ui/panels/inventory, item icons | OK |
| 27 climb boost | the Pilgrim, puff_boost | #5 |

## Second pass (09:1x): the remaining 42 shots

A first read by a helper agent, then every flagged shot re-read by me at 1:1 (1, 5, 9, 10, 14, 16). Verified defects:

| # | Shot | Defect | Owner |
|---|------|--------|-------|
| 10 | smoke_1 (the title menu) | The whole scene is B-046's v2 render (`ui/title/background`, MenuController.cs:243): 3D-rendered conifers, a glowing violet peak, a grey placeholder hull with a black window, pixel-noise dirt with hard edges at x≈558 / 1898. The first thing a player sees. | BLENDER (a v3 title scene: the Pilgrim on its pad, painted backdrop; card) |
| 11 | smoke_10 (Earth waystation) | The docking bay interior is unthemed 3D (grey cloudy panels, a photographic starfield, flat grey / orange / yellow blocks); DockingBay.cs requests no art key. | UNITY + BLENDER (a v3 painted bay interior would need a card and its wiring) |
| 12 | smoke_9 (crafting) | Thruster Mk2's icon is a flat teal square: `icons/thruster_mk2/base` does not exist (Mk3 does). | BLENDER (draw it in B-199's item-icon style) |
| 13 | smoke_5, smoke_6 (Mars canyon), smoke_14 (Mercury twilight) | Below layer2 the view smears into vertical streaks (Mars) or stops at a hard edge with flat cream below (Mercury, x 1445-1920, y≈810). Both sets DO declare `continue_rows` 64 (D-169), so the band is not being repeated below the layer. | UNITY (repeat continue_rows; the same code serves B-220 / U-191) |
| 14 | smoke_16 (Venus station) | Flat bands with ruler-straight edges under the aerostat deck (a pale strip y 900-945, a dark slab below): `backgrounds/venus/deck` has no `continue_rows`. | BLENDER + UNITY: add venus/deck to B-220's tileable bands |
| 15 | smoke_16 | The sky serpent is shaded in soft gradients with a glowing mesh halo behind its spines and little ink: reads as the pre-v3 creature style. | BLENDER (check its key; a v3 redraw if it is v2) |
| 16 | smoke_18 (Mars shelter, night) | The built shelter wall stacks float ~40 px above the slope (bases at y≈692 / 615 over ground at ≈740 / 655). | UNITY (base-piece placement on a slope) |
| 17 | smoke_11 (catalogue) | The "Camp" entry has no icon. | UNITY / BLENDER (which key it wants) |

Possible, low confidence (the helper's flags, not confirmed by me): smoke_3 / 18 "night" shots look like day (lighting); smoke_7 Saturn has no rings or bands at that distance; smoke_24 the Pilgrim's base below the floe top; smoke_4 strata above the sloping shore line; smoke_22 a pale vertical seam in the mesa backdrop; smoke_31 / 32 / 36 soft dark smudges on the strata (UNITY's depth shading, as on smoke_41); smoke_3b / 3d a hairline seam in the ground band at x≈922; smoke_2c / 15 the held tool or scan beam reading weapon-like at a glance (the v3 tools landed in B-217; worth a look on the next smoke).

Clean in the second pass: 2, 2b, 3c, 12, 19, 20, the five title cards, 26, 28, 29, 30, 33, 35, 39, 42, 44, 45, 46a-d.
