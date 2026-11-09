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

Second pass (the remaining shots: 1-7, 9-12, 14-16, 18-22, 24, 26, 28-33, 35-36, 39, 42, 44-46): appended below when read.
