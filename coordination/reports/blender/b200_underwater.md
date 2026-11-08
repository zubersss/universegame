# B-200: Earth's sets under the sea (3 / 8 / 15 m below the surface)

BLENDER, 2026-11-08 16:05. Sheets: `blender/preview/review_b200_earth_coast_underwater.png`, `review_b200_earth_plains_underwater.png`. They're built by `build_backdrop_v3.preview_underwater` from the exported layers (Art), numpy only.

## How the sheets are built

- **Camera.** The camera follows the swimmer (screen row 732, as in the dip reviews' camera frame). Each layer rises by its parallax × the camera's drop (ParallaxMath.LayerY). The near layer's `continue_rows` strip repeats below it (U-164), and the camera's sky colour shows wherever nothing covers.
- **Tint.** U-040's underwater tint is applied as `UnderwaterTint.shader` has it: everything below sea level, the swimmer included, multiplied by (0.55, 0.78, 0.95) × max(0.06, e^(−depth / 45 m)).
- **Assumption.** The sea surface is taken at the set's line. Over the Ocean the band's line follows the water line (BandDatum.cs 110-123); PlanetBackdrop's sea level is datumY + 1 m, so the surface may sit up to 1 m higher.
- **Not drawn.** The seabed and the shore's terrain depend on the terrain's depth, so the sheets show only what the backdrop puts behind the water.

## Read

| Set | Depth | What shows | Verdict |
|---|---|---|---|
| coast | 3 m | The near layer's beach (dunes, grass, the rock island) stands **above** the surface line, as a shore floating on the sea. Below the surface, the tinted sand body with dune shadows; its pebbles read as specks in murky water. | DEFECT 1 |
| coast | 8 m | Grass tips and the island's top poke above the surface. Below it, the tinted sand body and then the continue strip down to the frame's foot. | DEFECT 1, 2 |
| coast | 15 m | The surface is off-screen. A flat green-grey from top to bottom (layer2's strip), with faint vertical streaks. No depth cue: no light from above, no seabed, nothing far. | DEFECT 2, 3 |
| plains | 3 m | The meadow stands **above** the surface line. | DEFECT 1 |
| plains | 8 m | Below the surface, the tinted **meadow with its red and yellow flowers** fills the water: land, plainly. | DEFECT 1, 2 |
| plains | 15 m | Green-grey meadow texture with flower specks at the top, faint vertical streaks. | DEFECT 2, 3 |

**Clean:** the sky and far layers above the surface (coast layer0 / layer1 with the sea horizon's blue band; plains layer0) read correctly through the surface line at 3 and 8 m. No sky-colour gaps under water: the near layer's strip covers every row.

## Defects and proposed fixes

1. **The near land layer is still drawn when the camera is out at sea.** The coast set is the shore seen from the shore, and the plains are inland. From under the sea, their near layer (beach dunes, meadow) sits above the surface or fills the water.
   - *Fix (UNITY, no art):* below the sea surface on screen, stop drawing the land set's layers and their continue strip over sea columns (the wall map's sea flag, PlanetBackdrop.cs 608-610, already marks them). Fill that region with the water gradient the tint implies.
   - *Fix (BLENDER, art):* see 2.
2. **There is no underwater backdrop.** What shows is tinted land texture, and at 15 m nothing gives depth.
   - *Proposed card (BLENDER):* `backgrounds/earth/sea_under`, a D-169-style set drawn for below the surface. Its layers:
     - layer0: the water column, light near the surface (wavering light shafts) darkening down to the floor colour;
     - layer1: far seabed silhouettes (rock arches, kelp stands) in the haze;
     - layer2: the near seabed (sand ripples, rocks, kelp, shells), anchored on the seabed depth;
     - one optional strip: the surface seen from below, a bright wavy band.
   - Same palette, no faces. UNITY draws it where the screen is under the surface over sea columns, and the land set above.
3. **Vertical streaks from the continue strip.** When the 64-row strip fills most of the frame, the paper grain's variation along x tiles into faint vertical stripes. On land the ground fill covers it, so only deep valleys show it.
   - *Fix:* fixes 1 and 2 hide it under the sea.
   - *If it ever shows on land (BLENDER):* jitter the strip's grain per repeat, or blend 2 strips (the tile_bottom pass in gen_painted_bg).
