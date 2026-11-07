# BLENDER STATUS
Updated: 2026-11-07 02:2x · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
LEAD cycle 252 order (UNITY's Editor at ~0.1 GB free: nothing above ~100 MB until the lock frees):
1. Status: DONE (8e2761f landed 02:0x, before cycle 252; this update 02:1x).
2. B-133 / B-134 manifest rows (in 265ebc7) + dry run: DONE 02:1x. B-133: the export path with stub layers (manifest row -> export_background -> build_backdrop_v3 lookup -> six layers + two scene jsons written, sizes and seams checked); B-134: the side_b row against render.py's sheet path (build(out) default build_fn, 56 one-based socket frames, clip names unique vs side, the glass tint kept).
3. want_blender.lock filed 02:01:10 for queue #2: one batch `tools/blender_render.ps1 characters/surveyor/side_b,backgrounds/earth/forest,backgrounds/earth/coast` + the B-133 review rebuild (`build_backdrop_v3.py blender/preview forest,coast --from-png`) and a pixel compare of the exported layers with the rolled preview PNGs, <= 15 min.
4. B-135 pike / shark / squid: SOURCES WRITTEN 02:1x in build_creatures_earth_v3.py (fish kit: an undulating spine with a width profile, forked tail, dorsal / anal / pectoral fins; squid: mantle, fins, one big eye, eight hose arms + two club tentacles, a round ink cloud). Pivot [0.5, 0.5] (no ground); swim 12-16 at index 1 (v3.CAPS gains "swim", contract v3.1); the water-floor check = the deepest ink below the pivot per creature (reported) + the bottom 2 px edge; reviews 1x in the coast sea (B-133 layers 0-1) beside the surveyor. Preview runs once the lock frees (~150 MB).
5. Coast sand strip DONE 02:2x (158484a): terrain/earth/ground_strip_sand, a fourth B-130 kind (same contract; ripples, ripple marks, shells, weed, pebbles; grain 0.02 on the brighter sand); join 0.67/255, silhouette identical on all 64 edges, grass / soil / stone byte-identical to the accepted exports; the B-133 coast composite stands on sand. Exports with terrain/earth/ground_strip_set (four sheets) in a later slot.
6. Sun disc design (build_sun_v3.py, uncommitted until it runs).
Heavy queue: #2 my batch above (want on file); B-131 export after UNITY's U-113 code commit (D-117).

## Last completed
- 01:45:53-01:54:10 QUEUE #2 SLOT (one heavy lock, 8.3 min, released; UNITY's want was on file and yielded per D-112):
  - B-132 EXPORTED (0f9e0ab; log OK x3, peak 519 MB): creatures/earth/stag 1956x1076 (52 x 192x176, 140 s), wolf 1964x788 (66 x 160x128, 85 s), bear 2048x1144 (56 x 224x160, 165 s, new key); ink 2.0-3.0 / 1.0-1.5 px, palette 100 %; `replaces_v2` removed the eight stag / wolf v2 files (.glb, _normal, _mask, _emission) exactly as dry-run; sources sources/creatures/earth_{stag,wolf,bear}_v3.blend; reviews review_b132_earth_{stag,wolf,bear}.png stamped, the surveyor beside each.
  - B-133 PREVIEWS (numpy, the FFT washes): forest + coast at backgrounds/earth/{forest,coast}/ (LEAD cycle 251 accepted the paths). Layers: forest 2048x1024 2.3 MB / 2048x640 1.0 MB / 2048x384 0.6 MB; coast 2048x1024 2.3 MB / 2048x512 0.7 MB / 2048x384 0.6 MB (<= 4 MB each). Seam scores 0.80-1.03 except forest layer1 at 2.70 (limit 2.0): not a seam (alpha 252 -> 239 -> 200 -> 134 -> 70 across the wrap is one soft edge that sat on column 0). Fix in finish(): each periodic layer is rolled so the wrap sits on its quietest column (computed on the 8-bit image, so the export picks the same offset): every seam now 0.43-0.87, measured on the preview PNGs. Review images (review_b133_earth_{forest,coast}_preview.png) still show the unrolled layers until the --from-png rebuild.
- 01:3x-01:4x Wolf review fix (4dcf83d): the 1x panel grows to the beside frame's height (the 192 px surveyor beside the 128 px wolf raised a swallowed ValueError). v2 removal moved to meridian.v3.remove_v2 and dry-run on a scratch copy: 8 files out, bear none, every colour map / json / .meta kept.
- 01:1x-01:2x B-132 design previews (dcaee7d), accepted cycle 251 (D-119).
- 00:5x-01:1x B-131 export wiring (5650912): see Ready for review.

## Ready for review
- B-129 (558976a), B-130 (558976a): exported; Done on UNITY's import / U-111 capture per cycle 249.
- B-131 export wiring (5650912): `props/common/camp_set` exports the six props (<= 512^2 each, colour + json, D-117) and removes their 24 v2 files; dry run passed (joins 0.0/255, ink 2.0-3.0 / 1.0-1.5, palette 100 %). The new 2 px edge check fixed a smelter lever 1-2 px over the edge and a lamp pivot sign bug that cut the halo: lamp json pivot [0.32, 0.0625]. Waits for U-113.
- B-132 (0f9e0ab): exported, see Last completed. Clip indices idle 0, walk 1, react 2, bump 3 (Gus's order), flee 4, the wolf's follow 5 by name.
- B-133 previews (265ebc7) ACCEPTED cycle 252: forest (sky, two tree-fringed far ridges / the tree line: trunks, round crowns, tiered firs, shaded understorey, sun dapples / undergrowth: bushes, fern fronds, a stump and a log, bluebells) and coast (sea to the horizon, a pale headland, sparkle dabs / nearer sea with foam rows, a grassy cliff, two sea stacks / dunes with marram, pebbles, shells, driftwood). Scene jsons parallax 0.1 / 0.35 / 0.6, y_m -2 / -1 / -0.5 like the plains. Review images rebuilt in my next slot (see Current task).
- B-134 PREVIEW (265ebc7) ACCEPTED cycle 252: blender/preview/review_b134_surveyor_side_b_preview.png (the export's layout, side's idle frame at 1x beside): characters/surveyor/side_b 1956x1172, 56 frames 192x192, pivot [0.5, 0], PPU 64, seed 5. dig 10 loop (two-hand pick: wind-up, smear, the point bites, chips from the impact point), build 10 loop (hammer on a mustard plate that hangs askew and snaps flat, then a rivet driven), surprise 12 once (eye-pop 1.4x, the helmet lifts 0.11 m off the collar as the card's "hat lift"), jetpack 10 loop (red / mustard flame from a nozzle under the float pack, puffs rolling down and along the ground), climb_in 14 once (0-7 hand over hand in place: UNITY moves the root up the fin-leg; 8-9 lean to the hatch; 10-11 a stretched zip with speed lines; 12-13 only a puff: the surveyor is hidden). Every frame carries a `hatch` socket at (1.0, 1.05) m from the pivot (render.py's B-122 sockets path): put the Pilgrim's door socket there. Ink 2.0-3.0 / 1.0-1.5 px, palette 100 %, no clipped frame, nothing below ground, clip names unique vs side. Open boxes: motion / original / style self-checks + "idle" (the idle loop lives on side). Deviation: no scarf (the B-125 surveyor has none); the hose and plumb bob stream instead. draw_surveyor gained shift / helmet_dz / eye_pop; side's 98 drawings are stroke-identical (hash b3926709 before and after).

## Handoffs (unrouted only)
-> UNITY (B-132, exported 0f9e0ab): delete the eight .meta files of the removed stag / wolf v2 files (stag.glb, stag_normal/_mask/_emission.png, same for wolf); creatures/earth/bear is a new key (no SpeciesSpec yet: Bible §7.1 "Brown bear (territorial)"; under D-087 its react is the rear-up + huff). The sheets are drawn about 1.5 m long x 2.0 m tall (stag), 1.2 x 1.0 m (wolf), 2.1 x 1.3 m (bear); the v2 SpeciesSpec sizes were 1.9x1.6 and 1.5x0.9.
-> UNITY (U-113, D-117, for the tests): B-131 jsons as they will export: frames pad 128x48 / wall 64x176 / door 88x176 / smelter 112x192 / crate 80x72 / lamp 64x160 at PPU 64; pivots [0.5, 0.208333], [0.5, 0.056818], [0.5, 0.056818], [0.5, 0.052083], [0.5, 0.138889], lamp [0.32, 0.0625]; door 3 cols x 2 rows, smelter 4 x 2, lamp 2 x 2, the rest 1 frame with "animations": []; extra fields tile, module_m (2.0 / 1.0), interactable, ground_line_px, squash_root false. The 24 .meta files beside the removed v2 files are yours.
-> UNITY (U-115, B-134): side_b's clips by name (dig, build, surprise, jetpack, climb_in); the `hatch` socket per frame for climb_in's placement.
-> UNITY (C2, routed to U-110): every Earth plant carries "biomes".
-> UNITY (B-128, on import): def.icon = "icons/<key>/base" for soil, grass, regolith, snow, mercury_regolith, mercury_basalt, sulfide, tessera.

## Blockers
none.

## Proposals (undecided only)
- -> LEAD (Sun disc, C2 candidate): export as a rig, not a sheet (r 900 px in space); details in build_sun_v3.py's header, preview to follow.

## Rules I keep (from slips this session)
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073).
- A want is filed only after the other role takes the lock (D-039); a rank is live only while a want or lock is on file (D-112).
- Light work while another role's heavy job runs: <= 300 MB extra (D-109). fakegp sheet previews ~100-200 MB; FFT backdrops and full review rebuilds ~250-300 MB go in my slot.
- Measure every new export path's frames against the 2 px edge before the export (the B-131 lamp and B-134 dig/zip frames failed it).

## For USER_ACTIONS
none.

## HeavyJobLock
none held; want_blender.lock filed 02:01:10 (queue #2: B-134 + B-133 exports).
