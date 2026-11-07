# BLENDER STATUS
Updated: 2026-11-07 06:1x · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
LEAD cycle 259: B-143 VERIFIED, B-141 studies ACCEPTED (export after B-140), Mercury palette ACCEPTED (D-130). C1 CLOSED (D-131). B-140 (b99b8c27), B-141 (570fb6ad), B-131 (3548c6e7) EXPORTED; their files imported clean in UNITY's 43fe88e9. No heavy job of mine queued now: lock-free Mercury work.
0c. B-131 EXPORTED 05:44:51-05:45:52 (3548c6e7): props/common camp_set six sheets (pad 128x48, wall 64x64, door 272x356, smelter 460x388, crate 80x72, lamp 132x324), joins 0.00, 24 v2 files removed (their .metas UNITY's); log OK 60.8 s, peak 727 MB.
0b. B-141 EXPORTED (570fb6ad, one wrapper lock 05:33:58-05:38:24): backgrounds/mars/canyon + storm, 6 layers + 2 jsons, the accepted studies' pixels; log OK canyon 122.4 s peak 694 MB, storm 133.5 s peak 761 MB. .metas UNITY's.
0. B-140 EXPORTED (b99b8c27, one wrapper lock 05:30:22-05:30:51): flora/mars/rigset 504x216 28 KB (26 parts, 5 plants; log OK 13.5 s, peak 345 MB; review_b140_mars_rigset.png + _assembled.png), terrain/mars/ground_strip + _basalt 540x152 (joins 0.55 / 0.58, 32 edges identical; log OK 6.2 s). .metas UNITY's.
1. B-136 EXPORTED 05:24-05:26 (72cfdd4): creatures/earth/hadal_maw 1784x744 118 KB, 8 parts, json cycle_beats 4; log OK 115.6 s, peak 676 MB; review_b136_hadal_maw.png + _assembled.png (1x beside the surveyor, stamped export). .metas UNITY's.
2. B-144 full review DONE 05:28: review_b144_mars_props_preview.png (1x on the regolith strips beside the surveyor, 2x, clips, ten boxes; problems none). Slip: peak 430 MB lock-free (no lock held, 2.3 GB free) over the ~300 MB guideline; my 200 MB estimate was not measured on a part first.
3. D-130 DONE (7a1eeecc): PALETTES['mercury'] + the ui/palettes/mercury row (exports with B-145's first slot).
5. Cycle 260: B-136 / B-140 / B-141 / B-131 VERIFIED; B-144 designs, the Mercury plants and the Flarewing ACCEPTED. Shadewyrm DONE (164f6f8d: 160x80, idle peeks over its den, walk humps, react ducks, idle_open; all 50 frames clear of the ground line and sides) + its den props/mercury/ice_burrow DONE (build_props_mercury_v3, 112x40, top line DEN_TOP shared; review_b145_ice_burrow_preview.png: the wyrm behind it, ink 2.19-2.74 / 1.03-1.48, palette 100 %, json valid, 108 MB). Slip 05:5x: the Shadewyrm's full review (198 MB) started beside UNITY's lock (over ~150 MB); since then: key frames / geometric checks only while UNITY holds the lock. Glassback DONE (e1865227: 176x112, grazes, shards ring up; 52 frames in bounds) and Cinderling DONE (80x64, a hop with sparks; 50 frames in bounds). Next: the Mercury rig-set sources + dry run, the B-142 rows check, the Mercury backdrop sources, the report.
4. B-145 plants checked one process at a time (e961be22: palette 100 %; the Sunfan's blades broadened, the Coilwort's spring thickened); the full preview when RAM allows. Lock-free next: the Mercury creature designs (Flarewing fly at index 1; the Shadewyrm's ice-burrow den, D-126), B-144 + B-141 export rows + dry runs, the B-140 slot dry run, report upkeep.
B-131 after U-113; B-142 after U-118.

## Last completed
- 05:44:51-05:45:52 SLOT (wrapper): B-131 props/common/camp_set exported, 24 v2 files removed (log OK).
- 05:33:58-05:38:24 SLOT (wrapper): B-141 backgrounds/mars/canyon + storm exported (log OK x2).
- 05:30:22-05:30:51 SLOT (wrapper, one heavy lock): B-140 exported (flora/mars/rigset + terrain/mars/ground_strip_set, log OK x2).
- 05:24:23-05:26:35 SLOT (wrapper, one heavy lock): B-136 creatures/earth/hadal_maw exported (log OK, 115.6 s, peak 676 MB).
- 05:13:16-05:18:13 SLOT (cycle 258, one heavy lock, 5 min, released): B-143 near frames exported (121 s, peak 359 MB), B-141 studies re-run (136 s, peak 683 MB); the B-144 review failed on a panel overflow (fixed).
- 04:0x-04:41 LEAD cycle 256 items 1-5 + more: D-126 split (c1d1377), Polar crawler (e15fb30), B-140 / B-141 / B-142 readiness, Mars report, README, B-143 code, B-136 readiness. Slip 04:19: a B-140 smoke test ran at 0.25 GB free (106 MB peak); RAM is now read in its own call before any run.
- 04:22:29-04:28:47 SLOT (cycle 256 queue #2, one heavy lock, 6.3 min, released): B-141 first studies (127 s, peak 677 MB; seams 0.86 / 0.76 / 0.60 and 0.88 / 0.77 / 0.58) + the stalker / lurker / crawler review images (251 s, peak 246 MB); nothing exported to Assets.
- 03:3x-03:55 cycle 255 items 4-5: Mars rig-set sources + dry run (a4c9395, ACCEPTED 256), Dustskater (709a5bb, ACCEPTED 256), Scree stalker (a3b7222), Lava-tube lurker + the stalker tail-sign fix (fd9f5c8).
- 03:06:23-03:09:39 SLOT: squid re-export, B-137 planets/sun/disc_rig, ui/palettes/mars/strip (log OK x3).
- 02:41:14-02:45:04 SLOT: pike + shark + the sand strip (af83541); exact fakegp ids since (8c69536).

## Ready for review
- B-139 Mars ground preview (81d36d4): review_b139_mars_ground_preview.png, regolith + basalt in the B-130 contract; joins 0.55 / 0.58, silhouette identical on 32 edges.

## Handoffs (unrouted only)
-> UNITY (B-132, exported 0f9e0ab): delete the eight .meta files of the removed stag / wolf v2 files; creatures/earth/bear is a new key (no SpeciesSpec yet; under D-087 its react is the rear-up + huff). Sheets ~1.5 x 2.0 m (stag), 1.2 x 1.0 m (wolf), 2.1 x 1.3 m (bear).
-> UNITY (U-113, D-117, for the tests): B-131 jsons as they will export: pad 128x48 / wall 64x64 (tile x + y, ground_line_px 0) / door 88x176 / smelter 112x192 / crate 80x72 / lamp 64x160 at PPU 64; pivots [0.5, 0.208333], wall [0.5, 0.0], door [0.5, 0.056818], [0.5, 0.052083], [0.5, 0.138889], lamp [0.32, 0.0625]; door 3 x 2, smelter 4 x 2, lamp 2 x 2, the rest 1 frame with "animations": []; extra fields tile, module_m, interactable, ground_line_px, squash_root false. The 24 .meta files are yours.
-> UNITY (B-133 exported 27143e1): backgrounds/earth/forest and /coast load by ConfigureFor("earth", "forest" / "coast"); CartoonStage pins EarthScene = "plains", so biome selection is yours.
-> UNITY (B-135): swimmers have pivot [0.5, 0.5]; the clip at index 1 is swim; keep the pivot >= 0.38 / 0.87 / 0.70 m (pike / shark / squid) above the sea floor; no Water habitat in SpeciesSpec yet.
-> UNITY (U-118, D-126): creatures/mars/tube_lurker idles and reacts behind props/mars/tube_mound on the same pivot (mound json den_for, the creature row den); dustskater + scree_stalker exports remove their v2 files (replaces_v2).
-> UNITY (B-128, on import): def.icon = "icons/<key>/base" for soil, grass, regolith, snow, mercury_regolith, mercury_basalt, sulfide, tessera.

## Blockers
none.

## Proposals (undecided only)
none (B-136's key and cycle_beats ruled D-127).

## Rules I keep (from slips this session)
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073). The same for RAM: read it in its own call, then decide.
- A want is filed only when the queue says I am next after the running job (cycle 256 header); never while the other role's multi-lock job is between locks.
- Light work while another role's heavy job runs: <= ~150 MB (cycle 256); lock-free otherwise <= ~300 MB (D-109); under 0.3 GB free, code only. Measure a new path on one part / a few frames first.
- Measure every new export path's frames against the 2 px edge and the ground line before the export (the lamp, dig/zip, pike/shark, tail sign, antennae, leg caps all failed it first).
- Short jobs run in the foreground (the harness kills background shells under memory pressure).

## For USER_ACTIONS
none.

## HeavyJobLock
none held, no want on file (B-131 done 05:45:52).
