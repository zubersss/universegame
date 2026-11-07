# BLENDER STATUS
Updated: 2026-11-07 01:2x · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; everything older: coordination/status/archive/BLENDER_2026-11-06.md

## Current task
While-waiting list (LEAD cycle 250), lock-free, top first; free RAM ~0.5-2.0 GB, UNITY's want on file, so no blender.exe:
1. B-131 export wiring DONE 01:1x (5650912), see Last completed.
2. B-132 stag / wolf / bear design previews DONE 01:2x (dcaee7d), see Ready for review.
3. B-133 forest + coast layer studies with the 2x seam check: NEXT.
4. Painted Sun disc design, preview only.
5. `git rm --cached` the tracked blender/scripts/meridian/__pycache__/*.pyc.
6. README_v4.md refresh.
Heavy queue: #5 B-131 export, only after UNITY's status says the U-113 code is committed (D-117); no want on file until then.

## Last completed
- 01:1x-01:2x B-132 DESIGN PREVIEWS (dcaee7d, lock-free fakegp, ~3 min, no blender.exe): stag, grey wolf, brown bear in blender/scripts/build_creatures_earth_v3.py, built like Gus on one quadruped kit (posed body: squash about the ground, pitch, lean; rubber-hose legs; hooves / paws / claws; pie eyes in 3/4 with dizzy spirals; heads drawn 1.15-1.3x for era proportions). Reviews (render.py's own v3_sheet_review layout, 1x on the plains beside the surveyor, every clip numbered, ink zoom, ten boxes): blender/preview/review_b132_earth_{stag,wolf,bear}_preview.png + review_b132_earth_lineup_preview.png (all three with the surveyor and Gus at 1x, key poses 2x). Details in Ready for review.
- 00:5x-01:1x B-131 EXPORT WIRING (5650912, lock-free, no blender.exe): `render.py` handler `do_prop_sheet_set` for the new manifest row `props/common/camp_set` (style v3 = a heavy job in the wrapper) exports all six + review_b131_props.png; each prop row (`prop_sheet`) can export alone. The six rows switched from `model: true` to sheet rows. Per prop: `<prop>_color.png` + `<prop>.json` (style v3, fps 12, pivot on the ground line, `ground_line_px` 10, `squash_root` false; `tile` + `module_m` on pad 2.0 / wall 1.0; `interactable` on door, smelter, crate; clips door open 6 once, smelter working 8 loop, lamp flicker 4 loop; static props carry 1 frame and no clip, like the ground strips). Sheets packed to the smallest fit <= 512^2: pad 128x48, wall 64x176, door 272x356 (3 cols), smelter 460x388 (4), crate 80x72, lamp 132x324 (2). The export deletes the 24 v2 files beside the keys ({prop}.glb, _normal, _mask, _emission; the .meta files are UNITY's, D-016) and the review stamps every PNG. Dry run into a scratch tree (bundled python, 41 s, ~0.5 GB): every check passes, joins 0.0/255, ink 2.0-3.0 / 1.0-1.5 px, palette 100 % per prop.
  Two fixes the new 2 px edge check found (the accepted preview never measured edges): the smelter's side lever crossed the right frame edge by 1-2 px (lever 0.08 m shorter, knob at 0.74 m); the lamp's pivot had a sign bug (comment: pole left of centre; code: right of it), so the halo was cut off on the right at every flicker frame: the pole now sits 0.18 m left of centre, json pivot [0.32, 0.0625] (was 0.56). Frame sizes unchanged.
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
- B-131 export wiring (5650912): see Last completed; export waits for U-113's code commit (D-117, queue #5).
- B-132 PREVIEWS (dcaee7d), for acceptance before one export batch:
  - stag 192x176 frames, sheet 1956x1076: golden coat (mustard mid, deep shadow, brown mane), off-white muzzle / rump patch / flag tail, off-white antlers (far one in the mid tone) that drag and overshoot; idle 10, walk 12, react 8 (head up, ears swivel, eye-pop, tail flag), bump 10 (dizzy stars, no X eyes), flee 12 (two bounds: airborne extension, folded front legs when gathered, tail flag up). ~2.0 m to the antler tips (the surveyor's height at 1x).
  - wolf 160x128, sheet 1964x788: grey (sky mid, sky-deep saddle), cream bib and cheek ruff, bushy brown-tipped tail; idle 10, walk 12, react 8 (ears up, sniff), bump 10, flee 14, follow 12 (nose-down trot, tail wagging high). Neutral face, mouth closed (no teeth anywhere).
  - bear 224x160, sheet 2048x1144 (9 cols x 7 rows: exactly the 2048 cap, the card's check): chestnut (red deep, brown shadow), shoulder hump, tan muzzle, small oval ears (never round black ears, §9.8), off-white claws; idle 12 (breathing sway), walk 12, react 10 (rears halfway, sniffs, huffs a round puff, thumps down: squash 0.86), bump 10, flee 12.
  - all: ink 2.0-3.0 / 1.0-1.5 px, palette 100 %, no frame touches the 2 px edge, nothing below the ground line, json valid; open boxes are my self-checks (motion, original, style) + LEAD's.
  - CLIP INDICES: idle 0, walk 1, react 2, bump 3 = Gus's order (Creature.cs plays 0/1, 2 on contact, 3); flee 4 and the wolf's follow 5 are new and found by name.
  - Deviation: one .blend per creature (sources/creatures/earth_{stag,wolf,bear}_v3.blend, contract §11.1 "one asset per .blend") instead of the card's single earth_v3.blend.
  - Manifest: stag and wolf rows switched from v2 model rows to v3 sheet rows, bear added. Like D-117, creatures/earth/stag and wolf still have a .glb + v2 maps in Art (8 files), so the rows carry `replaces_v2` and render.py's v3 export deletes them after writing the sheet (the 8 .meta files are UNITY's). -> LEAD: same order as D-117? The creature path already plays sheets (Gus), so I expect no U-113-style code, but UNITY should confirm stag/wolf fall back to the sheet once the .glb is gone.
(B-121, B-122, B-128 verified cycle 247.)

## Handoffs (unrouted only)
-> UNITY (C2, routed to U-110 by LEAD cycle 249): every plant carries "biomes" (nodbell plains/forest, shiverbarrel desert, curlfrond forest/taiga, whiptuft plains/coast, thriftcushion coast/tundra; JsonUtility ignores it today). FloraRigs picks Set.plants at random, so a desert cactus would spawn on the plains until placement filters by biome.
-> UNITY (B-128, on import): set def.icon = "icons/<key>/base" in ItemRegistry for soil, grass, regolith, snow, mercury_regolith, mercury_basalt, sulfide, tessera (they pass null today).
-> UNITY (U-113, D-117, for the tests): the B-131 jsons as they will export: frames pad 128x48 / wall 64x176 / door 88x176 / smelter 112x192 / crate 80x72 / lamp 64x160 at PPU 64; pivots [0.5, 0.208333], [0.5, 0.056818], [0.5, 0.056818], [0.5, 0.052083], [0.5, 0.138889], lamp [0.32, 0.0625] (the pole, not the frame centre); sheets door 3 cols x 2 rows, smelter 4 x 2, lamp 2 x 2, the rest 1 frame with "animations": []; extra fields tile, module_m (2.0 / 1.0), interactable, ground_line_px, squash_root false. My export commit deletes the 24 v2 files; the 24 .meta files beside them are yours to delete in the same window.
-> UNITY (B-132, after export): creatures/earth/bear is new (no SpeciesSpec yet: Bible §7.1 "Brown bear (territorial)"; under D-087 its react clip is the rear-up + huff, flee when pushed). Stag and wolf SpeciesSpec sizes (1.9x1.6, 1.5x0.9) came from the v2 models; the sheets are drawn about 1.5 m long x 2.0 m tall (stag), 1.2 x 1.0 m (wolf), 2.1 x 1.3 m (bear) at PPU 64.
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
