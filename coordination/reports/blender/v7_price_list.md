# What a v7 Earth costs (B-263)

BLENDER, 2026-11-10 15:0x. Files only: sums from rows already measured and from the game's own lists. Every figure is
marked **M** (measured on this machine or read from a file) or **E** (estimated; what would replace it is named).
Nothing here is promised; it feeds the owner's page (STYLE_V7 §5) and the 96 or 128 camera choice.

**Units.** 1 megapixel (Mpx) = 4 MB as RGBA32 (uncompressed, what D-197 keeps for walls) = 1 MB as BC7 (colour) or
BC5 (normal). A 2048 x 2048 atlas page = 4.19 Mpx = 16 MB RGBA32 = 4 MB BC7. Mips add a third.
**The budget** (Bible §11.1): <= 512 MB of textures loaded, <= 8 sprite atlases (<= 2048 a side) per planet, < 2.0 GB
working set. Gate reading 6 already reads 520 MB on Earth in the Editor (LEAD's card).

**Measured rows this is built on (M):** one scanned piece of about 0.4 Mpx in Cycles CPU, 64 samples: peak 0.63-0.90 GB,
6-31 s a render; repainting a material's two 1k maps 25-32 s, once per asset; a normal-map pass 4-10 s; the filter and
the brushed edge 6-15 s; a 2.3 Mpx frame was killed at 1.44 GB (part 1, 13:43-14:03). The look pass: 64 pieces, plain,
about 300 px each, 24 samples: 126 s, peak 931 MB (14:31). Sprites at 96 px per metre: 69-99 KB uncompressed (part 1).

## 1. The surveyor's clip set as frame sheets (colour + normal)

Drawings (M, from B-250's json and today's v3 sheets): slice 1 = **100** at 12 a second (side 34: idle 10, walk 12, run
12; side_air 36: jump, fall, land 8 each, stroll 12; side_dig 30: four digs of 5, five aims of 2). The whole set as v3
ships it today = **200** (side 98, side_b 72, side_dig 30). At 24 a second the moving clips double and the held ones
(idle, the aims) need not: slice 1 = 180, the whole set about **370** (E).
The frame box (M, B-250): 2.25 x 2.5 m. At ppu 128 it is 288 x 320 px (42 on a page); at 192, 432 x 480 (16 on a
page); at 256, 576 x 640 (9 on a page). 4 px gutters.

| Sheet ppu | Serves | Drawings | Pages | Colour + normal, RGBA32 | Colour + normal, BC7 + BC5 |
|---|---|---|---|---|---|
| 128 | the 96 camera (x1.33 over it) | 100 (slice 1, 12/s) | 3 | 96 MB | 24 MB |
| 128 | | 200 (whole set, 12/s) | 5 | 160 MB | 40 MB |
| 128 | | 370 (whole set, 24/s) | 9 | 288 MB | 72 MB |
| 192 | BOTH cameras (x2 over 96, x1.5 over 128) | 100 | 7 | 224 MB | 56 MB |
| 192 | | 200 | 13 | 416 MB | 104 MB |
| 192 | | 370 | 24 | 768 MB | 192 MB |
| 256 | the 128 camera (x2 over it) | 100 | 12 | 384 MB | 96 MB |
| 256 | | 200 | 23 | 736 MB | 184 MB |
| 256 | | 370 | 42 | 1 344 MB | 336 MB |

Sums: pages = drawings / (frames a page), rounded up; MB = pages x 16 (RGBA32) or x 4 (BC), twice (colour and normal).
- **Trimmed frames halve every row (E).** The figure's ink covers about 28 % of the box standing and about 70 % in a
  dig; if each frame is packed by its own rectangle the sheets shrink to roughly half. UNITY's importer decides.
- **Render time (E, until part 2's probe frame):** each drawing rendered in the figure's own bounds (about 0.25 Mpx at
  384 px per metre, so the peak stays near a piece's 0.7-0.9 GB): 8-15 s colour + 4 s normal = 12-19 s. 100 drawings:
  20-32 min, 2-3 locks; 200: 40-63 min, 3-5 locks; 370: 74-117 min, 5-8 locks (one lock <= 15 min). The sheet's ppu
  does not change the render (it is rendered at 384 and shrunk). NOT in this: building the figure, its suit and rig,
  and baking cloth and straps (STYLE_V7 §3.2), which is work, not render time.
- **12 against 24 drawings a second:** 24 costs 1.85x the memory and render of 12 for the whole set. The middle way:
  24 only for walk and run (+24 drawings: +12 % at ppu 192).

## 2. The camp's stage, and a biome

A SCREEN (M, B-258 part 3's layout, `build_v7_frame.py`): **24 pieces** (20 near, 3 middle trees, 1 far stand) in
**53 placements** over a 20 m view (UNITY's ceiling: about 80 in view). Cropped to their content, at the format's ppu
(near 192, middle 128, the far stand 32):

| Layer | Pieces | Mpx | What it is |
|---|---|---|---|
| near (ppu 192) | 20 | 1.66 | the largest: a 6.5 m snag 0.43, a 4 m log 0.17, a 2.25 m anthurium 0.12; a grass clump 0.02 |
| middle (ppu 128) | 3 | 0.55 | trees of 2.2, 3.5 and 5.7 m |
| far (ppu 32) | 1 strip | 0.37 | eight trees in one 1152 x 320 picture, enlarged by the game |
| ground maps (256 px per metre) | 4 | 4.19 | forest floor, litter, soil wall, red subsoil: 1024 x 1024 each, tiling |

Sum: near + middle = 2.21 Mpx = **one atlas page** at 53 % fill; the far strip and the ground maps beside it.
Colour: 16 MB (page) + 1.5 (strip) + 16 (ground) = 33.5 MB RGBA32, 8.4 MB BC7. Normal maps for the page only (a far veil
is in haze, the ground is unlit): +16 MB RGBA32, +4 MB BC5. **The camp: about 50 MB RGBA32, 12 MB compressed.**

A BIOME (E): a screen's 24 kinds repeated would show within two screens; three times the kinds (about 65 pieces: 3 near
pages, 1 middle page, 3 far strips of 2048 x 512) = colour 76 MB RGBA32 (19 BC7) + normals 64 MB (16 BC5) + ground
16 MB (4): **about 156 MB RGBA32, 39 MB compressed, per region**, with one region resident at a time. Earth has six
(forest, plains, coast, desert, taiga, tundra); they share grasses and rocks.
Render (E from the measured rows; the frame's own runs will replace it): about 1-1.5 min a piece with its normal map
(render 6-31 s, the material's repaint 25-32 s once per asset, the brush and edge 6-15 s): 65 pieces = 65-100 min of
Blender, 6-8 locks; about 100-150 MB of scans downloaded per region (M: the camp's nineteen assets are 105 MB).

## 3. Earth's creatures by the same sum

Today (M): seven frame sheets at ppu 64 (bear, gull, pike, shark, squid, stag, wolf: 384 drawings at 12 a second) and
the Hadal Maw as a rig: 13.2 Mpx on disk (50 MB RGBA32).

| v7 sheet ppu | All seven, Mpx | Pages | Colour + normal, RGBA32 | Colour + normal, BC7 + BC5 |
|---|---|---|---|---|
| 128 (x1.33 over the 96 camera) | 41.2 | 10 | 330 MB | 82 MB |
| 192 (x2 over the 96 camera) | 92.7 | 23 | 742 MB | 185 MB |

Sums: today's frame boxes x (ppu / 64) squared x the frame counts (bear 224 x 160 x 56, gull 112 x 96 x 52, pike
128 x 80 x 48, shark 224 x 128 x 54, squid 320 x 144 x 56, stag 192 x 176 x 52, wolf 160 x 128 x 66). A region holds
two to four of the seven: about 3/7 of a row resident. 24 drawings a second: about x1.8.
**What this table does not price, and it is the larger cost:** each creature needs a 3D animal (a CC0 mesh or one
modelled by script), a skeleton and its clips keyed; today's are cut-out rubber-hose sheets. That is days of work per
creature, and no CC0 animal is in hand yet.

## 4. The total against 512 MB

One region resident: the surveyor's whole set, the region's stage, its ground, three creatures.

| Case | Surveyor | Stage + ground | Creatures (3 of 7, ppu 128) | TOTAL | Against 512 MB |
|---|---|---|---|---|---|
| A. ppu 192 sheets, 12/s, RGBA32, boxes | 416 | 156 | 141 | **713 MB** | OVER by 201 |
| B. A with trimmed frames | 208 | 156 | 141 | **505 MB** | at the line, nothing left for anything else |
| C. A in BC7 + BC5 | 104 | 39 | 35 | **178 MB** | inside |
| D. C with trimmed frames | 52 | 39 | 35 | **126 MB** | inside |
| E. the 128 camera with everything x2 over it (ppu 256), BC, trimmed | 92 | 69 | 62 (ppu 192) | **223 MB** | inside; 1.8x case D |
| F. D at 24 drawings a second | 96 | 39 | 63 | **198 MB** | inside |

- **D-207 (the owner on this list, 11-10 15:0x; Bible 5.4): for an art v7 planet the texture line is 1 024 MB loaded**,
  bounded by the unchanged working set (2.0 GB, warning 1.7; 0.6.3's built player reads 0.89-0.99 GB today). Against
  1 024 MB ALL SIX cases fit by the line alone (A 713, B 505, C 178, D 126, E 223, F 198); what case A leaves is 311 MB
  for everything else on the planet, and the working set becomes the real bound. Where the allowance is spent is
  UNITY's A/B (U-217): compressed wherever the paint survives, uncompressed only where it does not. The lines below
  were written against 512 MB and stand as the reasoning for that order.
- **Against the old 512 MB line, v7 fits only compressed.** Uncompressed it is over the budget before any UI, effect or space texture. Whether
  painted pictures survive BC7 without blocks is UNITY's A/B on one real piece (as U-207 did for walls, where D-197 kept
  RGBA32): the first thing to measure when the pilot's pieces are exported (B-260 b).
- **The atlas count breaks first:** the surveyor alone is 13 pages at ppu 192 (7 trimmed) against "<= 8 sprite atlases
  per planet". Either the rule counts pages resident at once and the sheets load by clip group, or the figure runs LIVE
  as a skinned mesh (LEAD's (ii), 13:3x), which removes the largest row of this whole list.
- **The 128 camera costs no memory if it uses the ppu 192 art** (x1.5 over it instead of x2). Kept at x2 it costs 1.8x.
  What it always costs is screen: every piece covers 78 % more pixels, and covered pixels per overlapping layer are what
  the Intel chip pays for (UNITY's Q4 answer); that is U-216's measure on the built player, not mine.

**The three largest costs:** (1) the surveyor's frame sheets, colour and normal (416 MB RGBA32 at ppu 192, 12/s);
(2) the creatures' sheets, and before their memory the work of making seven 3D animals; (3) normal maps, which are half
of every figure and near piece.

**What I would cut first, in this order:** (a) FRAMES before sizes: stay at 12 drawings a second, 24 only for walk and
run; (b) trim the frames (pack the ink, not the box); (c) BC7 / BC5 for every v7 sheet and piece, once UNITY's A/B says
the paint survives; (d) normal maps only where a light of the game's can reach (figures and near pieces; not the middle,
the far veils, the ground or the foreground in shade): a third off the stage; (e) the middle layer at 96 instead of 128;
(f) one ppu 192 set for both cameras instead of a ppu 256 set for the 128 camera.

## 5. What leaves memory when v7 replaces v3 for a region (M: the files' own sizes; which are resident is UNITY's gate)

Today's Earth and surveyor art on disk: 210 Mpx (803 MB as RGBA32, 201 MB at one byte a pixel): the surveyor's fifteen
files 47.6 Mpx (182 MB RGBA32), the shared Earth backgrounds 41.8 Mpx (159), terrain 25.3 (97), props/earth_flora's
atlases 16.8 (64), the creatures 13.2 (50), each region's painted layers 6.3-12.6 (24-48). A region going over to v7
retires its painted layers (24-48 MB), the flora atlases (64), the v3 surveyor sheets in use (side, side_b, side_dig:
7.4 Mpx, 30 MB) and its creatures' sheets (about 20 of the 50): **about 140-160 MB RGBA32 leaves**; case A brings in
713, case D 126.

## 6. The quality ladder (B-266, D-209: what to SPEND memory on, in the order the eye gains most)

D-209 (the owner, 15:1x): use this laptop to its measured limit. So from case D (126 MB: everything compressed, trimmed,
ppu 192, 12 a second, normals only on figures and near pieces) upward, each rung is something the eye would see, its
cost, and the running total of one region resident. All **E** (sums from sections 1-4; one near "page" = about 20 kinds
of piece = 16 MB RGBA32 or 4 MB BC at ppu 192, x1.78 at ppu 256; the figure trimmed = 6.5 pages at ppu 192).
The marks are texture megabytes; on this Intel chip texture memory IS the machine's RAM, so the real bound is the
working set U-220's probe measures on the built player.

| Rung | What the eye gains | Cost | Running total |
|---|---|---|---|
| D | the base (section 4) | | 126 MB |
| 1 | THE FIGURE's colour uncompressed (the thing looked at all the time: no block in a face or a fold); its normals stay BC5 | +78 | 204 |
| 2 | the NEAR pieces' colour uncompressed (3 pages) | +36 | 240 |
| 3 | ppu 256 UNDER THE 128 CAMERA (only if that camera is chosen: x2 over it instead of x1.5): the figure +101, the near pieces +46 | +147 | 387 |
| 4 | 24 drawings a second for WALK AND RUN (+24 drawings) | +28 | 415 |
| 5 | 24 a second for EVERY moving clip (370 drawings in all) | +168 | 583 |
| 6 | normal maps on the MIDDLE layer (the game's lights reach the thicket) | +4 | 587 |
| 7 | MORE KINDS a screen: 40 more near pieces (two more pages at this quality) | +71 | 658 |
| 8 | A SECOND LIT VARIANT of the near plants (rendered with the light from the other side, so a plant may be mirrored without the painted light going wrong: D-206's rule 1 lifted for them) | +107 | 765 |
| 9 | LARGER FAR VEILS (ppu 64 instead of 32, uncompressed: the far forest stops being soft) | +36 | 801 |
| 10 | the three resident CREATURES' colour uncompressed (at ppu 128) | +53 | 854 |
| 11 | the creatures at ppu 192 (x2 over the 96 camera, as the figure) | +110 | 964 |
| | **---- 1 024 MB (D-207's line) ----** | | |
| 12 | the creatures at 24 a second for their moving clips | +159 | 1 123 |
| 13 | the figure's NORMAL maps uncompressed too (only if BC5 shows in a lit face) | +256 | 1 379 |
| 14 | the ground maps at 512 px per metre, uncompressed (the earth cut holds a 2x look) | +60 | 1 439 |
| 15 | the middle layer at ppu 192, colour uncompressed | +37 | 1 476 |
| | **---- 1 500 MB ----** | | |
| 16 | A SECOND REGION RESIDENT at this quality (no load when the surveyor crosses from forest to plains) | +440 | 1 916 |
| | **---- 2 000 MB ----** | | |

- Rungs 1, 2 and 4 are the cheap ones the eye gains most from: **240 MB with 1 and 2, 268 with 4 as well** (at ppu 192).
- Rung 3 is a camera decision, not a quality one: without the 128 camera it is not spent and every total below it is 147
  less (and rungs 4-8 cost about 0.56 of what is written, being priced at ppu 256).
- Rung 5 is the first costly one (168 MB for motion the paint-in-materials look may not show at 12 against 24): look at
  rung 4 in the game before buying it.
- Rungs 8 and 16 cost RENDER TIME as well as memory (a second render of every near plant; a second region's pieces).
- What none of this buys: more DETAIL in a piece than the 384 px per metre source holds. Past ppu 256 the next gain is
  rendering at 512, which is a change to B-258's method (one piece of about 0.7 megapixel a render: its peak is not
  measured yet), not a rung.
