# ART v6: the plant and rock kinds I would make for Earth (a plan for a yes on USER-44)

Written 2026-11-10 08:4x at LEAD's ask; one line each.

**State 11-10 10:0x** (previews only; nothing exported, no tiling or alpha):
- PAINTED and accepted as specimens or in the forest frame: 1 the canopy tree (one fork pattern), 2 the emergent tree
  (its buttresses read as boards: a later pass), 3 the feather palm and the fan palm, 4 the ground fern, 5 the broad
  leaf, the paddle and the heart leaf, 6 the bamboo clump, 7 the bough with leaf sprays and the liana, 8 the mossy
  boulder and the fallen log (a cut end, moss, a fern on it). Sources: `build_specimens_v6.py`,
  `build_forest_kinds_v6.py` (placeable `*_into(P, tf, s, pale)`), `build_forest_frame_v6.py` (the liana and the log
  are written inside the frame, not yet as placeable kinds).
- PAINTED AS SPECIMENS 10:14-10:35 (four runs each, with LEAD to judge): 9 the three grasses (`turf_into`,
  `clump_into`, `plume_grass_into`) and 10 the savanna tree and the thorn bush (`savanna_tree_into`,
  `thorn_bush_into`, the crown's `shelf`), in `blender/scripts/build_plains_kinds_v6.py`; 4's tree fern and a
  placeable ground fern (`tree_fern_into`, `fern_into`, `frond` in `build_forest_kinds_v6.py`, shown on the plains'
  sheet; `fern_into` itself is still unrun); 11 and 12, the coast (`coconut_palm_into`, `dune_grass_into`,
  `sea_rock_into` on `boulder`, `wrack_into`, `driftwood_into`, a generic `sheet()`), in
  `blender/scripts/build_coast_kinds_v6.py`. Sheets: blender/preview/review_b248_plains_kinds_preview.png and
  review_b248_coast_kinds_preview.png. None is in a frame yet.
- NOT WRITTEN: 1's two more fork patterns and the low spreading form; 8's shelf fungus and the boulder
  in three sizes; the liana and the log as placeable kinds; the plains' and the coast's ground palettes.
- What the first runs showed and what was changed is in renders_2026-11-10.md (10:14 on) and in the sources'
  comments (a weeping palm, a box tied with a ribbon, a snake, a row of teeth: each named and fixed).
Every kind is a rule in the manner of `blender/scripts/build_specimens_v6.py` (a form field steers the brush: TUBE =
a centre line with a radius, FACET = a plane with one value and one stroke direction, BALL = a lit cluster), under the
frame's one light, seeded so no two individuals are alike. "Cost" is my time to write and tune the rule; painting one
takes a second or two. Where it stands: N = near (dark, crisp, framing), M = middle, F = far (as a hazed silhouette).

## Forest
1. **Canopy tree** (DONE as the specimen; in the frame fourteen times): flared trunk, two roots, three boughs, a crown of ball-lit leaf clusters with leaves past its edge and sky holes. TUBE + BALL. N M F. To add: two more fork patterns and a low spreading form, so a thicket is not one tree repeated. 30 min.
2. **Emergent tree**: a tall pale trunk rising clear of the rest, buttress roots as thin planes at its foot, a small high crown. TUBE + FACET + BALL. M F. It gives the thicket its verticals and its height. 30 min.
3. **Feather palm** (DONE in the frame): a ringed, leaning trunk and eleven fronds, every leaflet its own dab. TUBE + fronds. M, and N as a single frond hanging into a corner. To add: a fan palm (pleated round leaves on stalks). 30 min.
4. **Ferns** (ground fern DONE in the frame): fronds from one base; a tree fern is the same crown on a short shaggy trunk. Fronds + TUBE. N M. 20 min.
5. **Broad-leaved understorey** (DONE as the specimen): leaf by leaf, a lit half, a shaded half, a midrib. To add two leaf shapes: a long paddle with torn edges, and a heart-shaped leaf on a stalk. TUBE per leaf. N M. 30 min.
6. **Bamboo clump**: jointed canes that taper, a node ring every 0.3 m as paint, sprays of small lance leaves at the nodes. TUBE with rings + leaf dabs. M, N at a frame's side. A strong upright rhythm against the round crowns. 40 min.
7. **Bough and liana**: a bough out of a near trunk with sprays of leaves (DONE in the frame), and a liana: a long sagging tube looped from trunk to trunk with a few leaves and aerial roots. TUBE. N, top corners. 20 min.
8. **Mossy boulder and fallen log**: the rock (DONE: jittered planes, a rounded corner, moss, earth over its foot) in three sizes; a log is a lying TUBE with bark rings, a cut end of growth rings, shelf fungus and ferns on it. FACET + TUBE. N M, the clearing's floor. 30 min.

## Plains
9. **Grasses in three heights**: turf blades along the surface (DONE), the clump (DONE as the specimen), and a tall plumed grass (arcing stems, a feathered seed head of small dabs). Strokes. Everywhere on the ground; the plumed grass is the plains' near layer. 20 min.
10. **Flat-topped savanna tree and thorn bush**: a short forked trunk under a wide, thin, layered crown (BALLs flattened into shelves); the bush is the same crown at knee height on many thin stems. TUBE + BALL. M F: the plains' skyline. 40 min.

## Coast
11. **Leaning coconut palm and dune grass**: a long trunk curving seaward, drooping fronds, a cluster of nuts; dune grass as long arcing blades in tufts on sand ripples. TUBE + fronds + strokes. N M. 30 min.
12. **Sea-worn rocks, the tide line and driftwood**: rounded dark boulders whose lower planes are wet (a darker, cooler value with a lit edge), weed and barnacle dabs, a line of wrack on the sand, a bleached log. FACET + TUBE. N M, the shore's ground. 40 min.

## Shared by all three (not counted above)
- **The covered ground**: litter in the frame's own ochres and olives (three leaf shapes), twigs, half-buried stones, roots breaking the surface, low rosettes; flowers only as a few paint accents inside a pool of light. DONE in the frame; per biome it needs its own palette (forest litter, plains dry grass and dust, coast sand and shell).

## What this buys and what it does not
- About six to seven hours of rule-writing for the twelve, then seconds to plant them. A thicket would then hold five or six kinds of tree and plant instead of one, which is most of what the forest frame lacks next to the stills.
- It does not buy draughtsmanship: each kind is still a rule's plant (measured, then painted), not a drawn one. The painter's-hand option (scanned strokes or painted plates that I place and light) stays open and would apply to any of these kinds.
- None of this needs the tiling and alpha work; that is separate (about two days) and waits for the owner's yes.
