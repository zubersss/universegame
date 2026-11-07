# BLENDER STATUS
Updated: 2026-11-07 03:4x · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
LEAD cycle 254 order (lock-free now; UNITY's C1 batch holds the queue):
1. Slot (queue #1): DONE 03:06:23-03:09:39 (c4225fd), see Last completed.
2. D-125 shelter wall DONE 03:2x (afcfa68): a 1 x 1 m tile 64x64, pivot [0.5, 0], tile x + y, ground_line_px 0; joins x 0.0 / y 0.0; review_b131_props_preview.png shows it stacked 2 and 3 high round the door fitted to its 1 x 2 cell; the other five props byte-identical.
3. B-139: plants preview handed off (8c69536, review_b139_mars_plants_preview.png, drawn 1.5x for 0.38 g); Mars ground strips DONE 03:2x (81d36d4, review_b139_mars_ground_preview.png: terrain/mars/ground_strip rust regolith + _basalt on the B-130 recipe; joins 0.55 / 0.58, silhouette identical on 32 edges); creature and prop notes in c2_mars_designs.md. Left: the canyon + dust-storm backdrop studies (FFT, so in a slot: want after UNITY's batch).
4. B-136 Hadal Maw design preview DONE 03:3x (1fb50b1): review_b136_hadal_maw_preview.png, a 6-bone rig set (head, body1, body2, tail, jaw, lure; lure swaps lit / dim / flare), ~34 m, one big eye + closed smile, the open jaw a cavern + tongue (no teeth), idle 8 travelling sway + react 8 jaw open. SLIP: its first run peaked 277 MB and the second 210 MB with UNITY's Editor up (~0.5-0.66 GB free, cap ~150 MB; nothing reaped); the large view is now 0.5x and further big renders wait for my slot.
B-131 export: after UNITY's U-113 code, which now follows U-106 (D-115 / D-117).

## Last completed
- 03:06:23-03:09:39 SLOT (one heavy lock, 3.3 min, released; LEAD cycle 254 queue #1): squid re-exported 1940x1476 (155 s, peak 632 MB; flee stretch 1.12, inside the 2 px edge); B-137 planets/sun/disc_rig_color.png 1900x928 + disc_rig.json (36 s, peak 1009 MB; ink on screen 2.0-3.0 / 1.0-1.5; review_b137_sun_rig.png at the game's size); ui/palettes/mars/strip (D-125 (2)). Log: "OK creatures/earth/squid ... 155.4s | peak 632MB", "OK planets/sun/disc_rig | sheet 1900x928 944KB | parts body 928x928, tongue 216x148, prominence_a 128x140, prominence_b 100x104, corona 512x512 ... 36.3s | peak 1009MB", "OK ui/palettes/mars | strip 8x1".
- 02:41:14-02:45:04 SLOT: pike + shark + the sand strip exported (af83541, verified cycle 254); the squid failed the export's edge check (fakegp's stroke ids gave a different ink jitter than Blender's; fakegp.strokes_of(as_object=...) now matches the export pixel for pixel, 8c69536).
- 02:2x-02:4x B-138 edge audit (836f558, DONE cycle 254), B-137 parts preview (88ceb01, accepted), B-139 part 1 palette + report (cb88c5f; palette ACCEPTED D-125), part 2 plant designs (8c69536).
- 01:45:53-01:54:10 B-132 EXPORTED (0f9e0ab; log OK x3, peak 519 MB; eight stag / wolf v2 files removed as dry-run); verified cycle 252.
- 02:0x-02:1x B-133 / B-134 dry run (stub-layer export path; side_b row vs the sheet / socket path); coast sand strip (158484a).
- 00:5x-01:1x B-131 export wiring (5650912): see Ready for review.

## Ready for review
- B-131 export wiring (5650912): `props/common/camp_set` exports the six props (<= 512^2 each, colour + json, D-117) and removes their 24 v2 files; dry run passed. Waits for U-113 (after U-106). D-125's shelter-wall tile redraw comes first (Current task 2).
- B-135 squid (c4225fd): re-exported, inside the 2 px edge (pike + shark verified cycle 254).
- B-137 (c4225fd): planets/sun/disc_rig_color.png 1900x928 + disc_rig.json; review blender/preview/review_b137_sun_rig.png at the game's size on the B-120 starfield with the Earth disc at true ratio; every part inside its 2 px edge; sheet <= 2048^2; log OK. Parts: corona (order 0, radius 1.42 R, breathe 0.03), tongue (order 1; ring: 14 instances, alt scale 1.0 / 0.62, base 0.97 R, spin 2 deg/s, pulse 0.08, 110 bpm, stepped 12 Hz), prominence_a / _b (order 2, at 100 / 280 deg on the rim), body (order 3); draw_scale 2.
- ui/palettes/mars/strip (c4225fd): the accepted Mars palette (D-125 (2)), also in meridian.v3.PALETTES["mars"].
- B-136 design preview (1fb50b1): blender/preview/review_b136_hadal_maw_preview.png (parts, bones, swaps and the idle / react tables in build_hadal_maw_v3.RIG).
- B-139 Mars ground preview (81d36d4): blender/preview/review_b139_mars_ground_preview.png, terrain/mars/ground_strip (regolith) + _basalt in the B-130 contract; joins 0.55 / 0.58 per 255, silhouette identical on 32 edges.
- B-139 part 2 preview (8c69536): blender/preview/review_b139_mars_plants_preview.png, five faceless Mars plants at 1x on a Mars stand-in beside the surveyor, idle 8 + react 4 each at 2x; ink 2.0-3.0 / 1.0-1.5 px, Mars palette 100 % per plant; drawn 1.5x for 0.38 g.

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
none held; want_blender.lock filed 03:20 for the B-139 canyon + dust-storm backdrop studies (FFT ~300 MB, ~2 min, preview only), rank per LEAD.
