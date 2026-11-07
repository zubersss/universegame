# BLENDER STATUS
Updated: 2026-11-07 00:4x · Session: 6 (C1, contract v3.1, Bible 4.1) · trimmed under D-113; everything older: coordination/status/archive/BLENDER_2026-11-06.md

## Current task
While-waiting list (LEAD cycle 249), lock-free, top first; each logged here:
1. B-131 camp props PREVIEW DONE 00:4x (blender/scripts/build_props_common_v3.py, blender/preview/review_b131_props_preview.png): all six at 1x on the plains over the B-130 ground strips beside the surveyor and the assembled Pilgrim rig on three 2 m pad modules, each at 3x, the clips at 2x (door open 6: a cartoon swing in about the hinge, status light red -> green; smelter working 8: mouth glow pulse, two chimney puffs, breathing, sparks; lamp flicker 4: drawn halo), tiling at 2x (pad and wall joins 0.0/255). Ink 2.0-3.0 / 1.0-1.5 px, mid + deep tones, no faces (one porthole, one mouth, no eye pairs). Sizes: pad 128x48 (2 m module), wall 64x176 (1 m), door 88x176 (1.2 m like the model), smelter 112x192, crate 80x72, lamp 64x160; ground line 10 px above each frame bottom.
   Questions for LEAD before the export: (a) contract §11.1 says color only, the card says interactables keep mask R = 0.1 and emission where the manifest has it: I propose color + json only, with "interactable": true in the json and the glows drawn (smelter mouth, lamp halo, lights); (b) these keys are model (glb) rows today, so the export changes their TYPE (sprite sheet) under the same keys: UNITY's ModelView/ModelSwap path for props/common/* has to take sprites.
2. B-132 stag / wolf / bear design previews (faces kept, no bared teeth): NEXT.
3. B-133 forest + coast layer studies with the 2x seam check.
4. Painted Sun disc design, preview only.
5. README_v4.md refresh.
Heavy queue: nothing of mine queued; no want on file.

## Last completed
- 00:19-00:22 B-129 + B-130 EXPORTED (558976a; one heavy lock, log OK x2, peak 668 MB, lock released, UNITY told):
  - flora/earth/rigset: all six Earth plants, 504x212 (36 KB), 44 parts; the snoozle's 7 parts pixel-identical to B-126 (crops + pivots compared to the previous sheet), its plant json unchanged except biomes; biomes on every plant. Reviews review_b129_earth_rigset.png + review_b129_earth_rigset_assembled.png (each plant 1x on the plains, rest/react 2x, idle loop with Unity's maths, swap cycles).
  - terrain/earth/ground_strip (grass, the key GroundStrip loads), ground_strip_soil, ground_strip_stone: 540x152 each (8 frames 64x152, 4 px gutters, no clips), "tile": true, pivot [0.5, 0.842] = the ground line. FRAME SIZE vs U-100's 64x128: GroundStrip.cs puts the pivot on the ground line and hangs the fill StripHeight = 2 m below it, so the frame is 2 m below + 0.375 m above (lip, tufts); no code change needed. Silhouette ON the ground line at every edge (UNITY's wall-edge ink starts there). Joins 0.63 / 0.62 / 0.81 per 255, silhouette ink identical on all 48 edges (rows 23-24). Review review_b130_ground_strips.png.
- 00:01-00:06 DISC PEAK MEASURED under heavy_blender.lock (the B-119 job into a scratch tree, bundled python): 2545 MB with the uint8 panels alone; cause = pngio.write_png filtering the whole ~10k-wide review in int16. Chunked writer (57aef7f, byte-identical output): 415 MB. The 22 disc exports stay byte-identical.
- 23:33-23:38 QUEUE #2 BATCH EXPORTED (f612225; one heavy lock, 4.9 min, log OK x4, peak 988 MB, lock released, UNITY told): B-121, B-128, B-122 (see Ready for review).
- 23:2x C2 Curlfrond fix (LEAD cycle 245): mustard fiddlehead tips + ink-behind fronds; review_c2_earth_plants_preview.png refreshed.
- 22:5x Disc review memory (673193b): build_discs_v3.preview turns each panel to uint8 as it finishes and writes the PNG directly (the 22:09 run peaked 2289 MB on the float canvas). Measure on the next disc run.
- 22:1x B-119 + B-120 exported (24f8fbb), accepted and verified cycle 246; live in UNITY's code (960af2f).
- 21:54 B-125 surveyor v3.1 exported (Done cycle 245). 21:13 B-124, B-126, B-127 exported.

## Ready for review
- B-129 (558976a): Assets/_Game/Art/flora/earth/rigset_color.png 504x212 + rigset.json (6 plants, biomes on each; snoozle parts pixel-identical to B-126). Sources blender/scripts/build_c2_earth_rigs.py -> sources/flora/earth_rigset_c2.blend. Reviews blender/preview/review_b129_earth_rigset.png, review_b129_earth_rigset_assembled.png.
- B-130 (558976a): Assets/_Game/Art/terrain/earth/ground_strip{,_soil,_stone}_color.png 540x152 + .json (tile true, pivot on the ground line). Source blender/scripts/build_c2_ground_strip.py. Review blender/preview/review_b130_ground_strips.png.
(B-121, B-122, B-128 verified cycle 247.)

## Handoffs (unrouted only)
-> UNITY (C2, routed to U-110 by LEAD cycle 249): every plant carries "biomes" (nodbell plains/forest, shiverbarrel desert, curlfrond forest/taiga, whiptuft plains/coast, thriftcushion coast/tundra; JsonUtility ignores it today). FloraRigs picks Set.plants at random, so a desert cactus would spawn on the plains until placement filters by biome.
-> UNITY (B-128, on import): set def.icon = "icons/<key>/base" in ItemRegistry for soil, grass, regolith, snow, mercury_regolith, mercury_basalt, sulfide, tessera (they pass null today).
-> UNITY (B-122, on import): ships/pilgrim/side_a..e and top_a..b were never exported (superseded by D-111; manifest preview_only). Sockets in rig.json, metres from the root: tail_exhaust, leg_l, leg_c, leg_r, door, attitude_l (-1.5, 2.6), attitude_r (1.5, 2.6). The ±35 flight tilt is the root transform.

## Blockers
none.

## Proposals (undecided only)
- -> LEAD (C2, from coordination/reports/blender/c2_earth_creature_reink.md): (1) a "swim" clip cap = walk/fly (12-16) in contract §11.2 + ArtRules.ClipCap; (2) Hadal Maw as a §11.3 rig set (too big for one sheet); (3) a shared Earth creature atlas, because the Earth scene with the ship landed is near the D-089 eight-texture budget.

## Rules I keep (from slips this session)
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073; two slips, 15:09 and 17:12).
- A want is filed only after the other role takes the lock (D-039); a rank is live only while a want or lock is on file (D-112): a free lock with no live rank ahead is mine to take.
- Light work while a heavy job runs: ≤ 300 MB extra (D-109). Lock-free previews use meridian.fakegp in Blender's bundled python (~100-200 MB).

## For USER_ACTIONS
none.

## HeavyJobLock
none held, no want filed (B-129/B-130 batch done 00:22).
