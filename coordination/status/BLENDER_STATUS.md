# BLENDER STATUS
Updated: 2026-11-07 04:17 · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
LEAD cycle 256 order (lock-free until my slot). Slot = #2 after UNITY's captures: file the want ONLY on UNITY's "captures done" (ETA 04:12; their wrapper yields to any older want), then <= 8 min: B-141 canyon + storm studies, the stalker / lurker review images, the stalker re-check (already passed lock-free 04:0x).
1. D-126 split: DONE 04:07 (c1d1377): props/mars/tube_mound (build_props_mars_v3, 104x32 static, den_for tube_lurker, drawn IN FRONT of the creature on the same pivot) + a hole-less tube_lurker (idle peeks, react startles + ducks to the eyes over the rim, paws on the mound's top line); render.py prop rows import their generator; manifest row (B-142). Checks: mound ink 2.14-2.91 / 1.01-1.48, palette 100 %, json valid; lurker 40/40 + stalker 64/64 frames json valid, no edge / ground hits, ink 2.00-3.00 / 1.00-1.50, palette 100 %. Den review: review_b142_tube_mound_preview.png.
2. Polar crawler DONE 04:17 (design only, new key creatures/mars/polar_crawler): an olive pill-bug of eight frost-capped plates, 144x64, idle 12 plates breathe / walk 14 leg ripple / react 10 curls into a ball and uncurls / bump 10; all 46 exact frames json valid, no edge / ground hits (after fixes), ink 2.00-3.00 / 1.00-1.50, palette 100 %, 43 MB. B-141 canyon + storm scene code DONE (9cb766f; the FFT run + reviews in the slot, script ready).
3. B-140 / B-141 / B-142 export readiness (rig set + strips rows, backdrop rows, creature rows with replaces_v2 on dustskater + scree_stalker, mound row done).
4. Mars report (c2_mars_designs.md) to the accepted state; 5. README.
Accepted cycle 256: B-136 Hadal Maw design (export in one slot after U-106, new key), Puffpod fix, Mars rig-set dry run, Dustskater. B-131 export after U-113 (after U-106). Under 0.3 GB free: code only.

## Last completed
- 03:3x-03:55 LEAD cycle 255 items 4-5: Mars rig-set sources + dry run (a4c9395, ACCEPTED 256), Dustskater (709a5bb, ACCEPTED 256), Scree stalker (a3b7222), Lava-tube lurker + the stalker tail-sign fix (fd9f5c8). A background all-frame check was killed for low memory at 03:55 (0.10 GB free during UNITY's PlayMode); re-run in the foreground 04:0x, passed.
- 03:06:23-03:09:39 SLOT (one heavy lock, 3.3 min, released; LEAD cycle 254 queue #1): squid re-exported 1940x1476 (155 s, peak 632 MB; flee stretch 1.12, inside the 2 px edge); B-137 planets/sun/disc_rig_color.png 1900x928 + disc_rig.json (36 s, peak 1009 MB; ink on screen 2.0-3.0 / 1.0-1.5; review_b137_sun_rig.png at the game's size); ui/palettes/mars/strip (D-125 (2)). Log: "OK creatures/earth/squid ... 155.4s | peak 632MB", "OK planets/sun/disc_rig | sheet 1900x928 944KB | parts body 928x928, tongue 216x148, prominence_a 128x140, prominence_b 100x104, corona 512x512 ... 36.3s | peak 1009MB", "OK ui/palettes/mars | strip 8x1".
- 02:41:14-02:45:04 SLOT: pike + shark + the sand strip exported (af83541, verified cycle 254); the squid failed the export's edge check (fakegp's stroke ids gave a different ink jitter than Blender's; fakegp.strokes_of(as_object=...) now matches the export pixel for pixel, 8c69536).
- 02:2x-02:4x B-138 edge audit (836f558, DONE cycle 254), B-137 parts preview (88ceb01, accepted), B-139 part 1 palette + report (cb88c5f; palette ACCEPTED D-125), part 2 plant designs (8c69536).
- 01:45:53-01:54:10 B-132 EXPORTED (0f9e0ab; log OK x3, peak 519 MB; eight stag / wolf v2 files removed as dry-run); verified cycle 252.
- 02:0x-02:1x B-133 / B-134 dry run (stub-layer export path; side_b row vs the sheet / socket path); coast sand strip (158484a).
- 00:5x-01:1x B-131 export wiring (5650912): see Ready for review.

## Ready for review
- B-131 export wiring (5650912): `props/common/camp_set` exports the six props (<= 512^2 each, colour + json, D-117) and removes their 24 v2 files; dry run passed. Waits for U-113 (after U-106). D-125's shelter-wall tile redraw comes first (Current task 2).
- B-136 design preview (1fb50b1): blender/preview/review_b136_hadal_maw_preview.png (parts, bones, swaps and the idle / react tables in build_hadal_maw_v3.RIG).
- B-139 Mars ground preview (81d36d4): blender/preview/review_b139_mars_ground_preview.png, terrain/mars/ground_strip (regolith) + _basalt in the B-130 contract; joins 0.55 / 0.58 per 255, silhouette identical on 32 edges.
- B-139 plants ACCEPTED cycle 255 (Puffpod fixed 9e9b06d); part 2 preview (8c69536): blender/preview/review_b139_mars_plants_preview.png, five faceless Mars plants at 1x on a Mars stand-in beside the surveyor, idle 8 + react 4 each at 2x; ink 2.0-3.0 / 1.0-1.5 px, Mars palette 100 % per plant; drawn 1.5x for 0.38 g.

## Handoffs (unrouted only)
-> UNITY (B-132, exported 0f9e0ab): delete the eight .meta files of the removed stag / wolf v2 files (stag.glb, stag_normal/_mask/_emission.png, same for wolf); creatures/earth/bear is a new key (no SpeciesSpec yet: Bible §7.1 "Brown bear (territorial)"; under D-087 its react is the rear-up + huff). The sheets are drawn about 1.5 m long x 2.0 m tall (stag), 1.2 x 1.0 m (wolf), 2.1 x 1.3 m (bear); the v2 SpeciesSpec sizes were 1.9x1.6 and 1.5x0.9.
-> UNITY (U-113, D-117, for the tests): B-131 jsons as they will export: frames pad 128x48 / wall 64x64 (D-125: a 1 x 1 m tile, tile x + y, ground_line_px 0) / door 88x176 / smelter 112x192 / crate 80x72 / lamp 64x160 at PPU 64; pivots [0.5, 0.208333], wall [0.5, 0.0], door [0.5, 0.056818], [0.5, 0.052083], [0.5, 0.138889], lamp [0.32, 0.0625]; door 3 cols x 2 rows, smelter 4 x 2, lamp 2 x 2, the rest 1 frame with "animations": []; extra fields tile, module_m (2.0 / 1.0), interactable, ground_line_px, squash_root false. The 24 .meta files beside the removed v2 files are yours.
-> UNITY (U-115, B-134 exported 27143e1): characters/surveyor/side_b plays by clip name (dig, build, surprise, jetpack, climb_in); climb_in: move the root up the fin-leg over frames 0-7, then put the `hatch` socket (1.0, 1.05 m from the pivot, every frame) on the Pilgrim door socket.
-> UNITY (B-133 exported 27143e1): backgrounds/earth/forest and /coast load by ConfigureFor("earth", "forest" / "coast"); CartoonStage still pins EarthScene = "plains", so biome selection is yours. Their .meta files are yours.
-> UNITY (B-135, after export): swimmers have pivot [0.5, 0.5]; the clip at index 1 is swim; keep the pivot >= 0.38 / 0.87 / 0.70 m (pike / shark / squid) above the sea floor; no Water habitat exists in SpeciesSpec yet.
-> UNITY (C2, routed to U-110): every Earth plant carries "biomes".
-> UNITY (B-128, on import): def.icon = "icons/<key>/base" for soil, grass, regolith, snow, mercury_regolith, mercury_basalt, sulfide, tessera.

## Blockers
none.

## Proposals (undecided only)
none (the Sun rig was ruled D-123).

## Rules I keep (from slips this session)
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073).
- A want is filed only after the other role takes the lock (D-039); a rank is live only while a want or lock is on file (D-112).
- Light work while another role's heavy job runs: <= 300 MB extra (D-109). fakegp sheet previews ~100-200 MB; FFT backdrops and full review rebuilds ~250-300 MB go in my slot.
- Measure every new export path's frames against the 2 px edge before the export (the B-131 lamp, B-134 dig/zip and B-135 pike/shark frames failed it).
- Measure a new preview's memory before running it beside the other role's job: disc / backdrop work at 2x supersampling is 250-350 MB, not the ~150 MB of a fakegp sheet.

## For USER_ACTIONS
none.

## HeavyJobLock
none held, no want on file (withdrawn 03:40 so UNITY's PlayMode B could start, heavy_unity.lock 03:39); re-file for the B-139 canyon + dust-storm studies (FFT ~300 MB, ~2 min, preview only) when UNITY says "captures done".
