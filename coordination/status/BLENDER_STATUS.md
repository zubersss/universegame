# BLENDER STATUS
Updated: 2026-11-07 12:52 · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
12:23-12:49 the Mercury exports (D-119, U-123's keys; LEAD's order B-149 -> B-148 -> B-150), each wrapper log OK, colour + json only (.meta UNITY's): B-149 backgrounds/mercury/day|twilight|night 12:23:14-12:28:27 (313 s, peak 673 MB; layer0 1448 / 1525 / 1116 KB, seams 0.52-0.77; review_b149_mercury_{day,twilight,night}.png; 1e99fcc4). B-148 refused 12:29 at the old 1.5 GB gate (1359 MB free, no Unity running) -> LEAD's D-145, in the wrapper (2194f067: per-job gate = max(1200, the category's last own measured peak + 700), GATE / GATE-RESET log lines, the 25 % overshoot reset); B-148 flora/mercury/rigset (26 parts, 5 plants, biomes day/twilight/night/polar) + terrain/mercury/ground_strip + _slate (joins 0.78 / 0.71, 32 edges identical) 12:44:31-12:45:04 at gate 1200 (est 345, peak 347 MB), ui/palettes/mercury 12:45:14 (light, 193 MB); review_b148_mercury_rigset.png, review_b148_mercury_ground_strips.png; 70c40e1e. B-150 creatures/mercury/glassback|cinderling|flarewing|shadewyrm (replaces_v2; v2 glb/normal/mask/emission removed) + props/mercury/ice_burrow 12:45:47-12:49:08 at gate 1200 (est 446, peak 389 MB), ink 2.0-3.0 / 1.0-1.5, palette 100 %; review_b145_mercury_*.png; cca20f60. Lock-free 12:39-12:41: Uranus props review (frames raised to 192 for the canopy apex / beacon lamp; json valid, 97 MB), Uranus rig-set dry run (21 parts, problems none, 132 MB). Next: UNITY's want 12:49:57 (U-123 check chain) goes first (D-037); then the studies slot (<= 6 min: hexagon, sdeck1 / sdeck2 ring pass, Uranus deck1 x4).
11:34: flora/uranus/rigset source (f03ae08d: five plants, sunturner 2 bones with left / right sun heads UNITY picks by season, fogbell 4, hailcatch 2, embermoss 1, prismfern 1). LEAD's plan after UNITY's Mars close chain releases (~11:51), no UNITY want on file: lock-free first (the Uranus 16-set smoke test, measured in that gap; the props review; the rig-set dry run), then ONE lock <= 5 min: the hexagon curtains + Uranus deck1 in sun_left / sun_right / night / survey; LEAD judges the lighting before decks 2 / 3 / deep get slots.
11:24-11:32: D-143 terrain/mars/ground_strip_frost EXPORTED (7db366cf: wrapper log OK 11:24:21, joins 0.50, the regolith frame + ground line; UNITY binds it in its Mars close take). Saturn hexagon: the curtain re-run 11:25:14-11:26:50 read as tracks -> LEAD option B: upright cloud curtains at depths, code in (ebf8b783), its ~1 min re-run in a later gap. B-158 lock-free 11:27-11:30, one measured run each: the Colossus preview (64 MB, Grand rig valid), Uranus flora 300, floes 175 (joins 0.89 / 0.44), frostwisp 192, methane_ray 198, hailcrab 195, tiltbird 195 (problems none in all, palette 100 %); the tiltbird review started 2 s before UNITY's lock (11:29:44) and overlapped it ~40 s at 195 MB. Uranus props source (b398b3c4). UNITY's Mars close chain holds the lock from 11:29:44 (~22 min). Waiting: the Uranus 16-set smoke test + props review (lock-free), the hexagon re-run, the Uranus deck studies (16 sets: slots).
## Last completed
- 07:09:10-07:14:09 gated numpy runs under one lock (above).
- 05:44:51-05:45:52 SLOT (wrapper): B-131 props/common/camp_set exported, 24 v2 files removed (log OK, 60.8 s, peak 727 MB).
- 05:33:58-05:38:24 SLOT (wrapper): B-141 backgrounds/mars/canyon + storm exported (log OK x2, peaks 694 / 761 MB).
- 05:30:22-05:30:51 SLOT (wrapper): B-140 flora/mars/rigset + terrain/mars/ground_strip_set exported (log OK x2).
- 05:24:23-05:26:35 SLOT (wrapper): B-136 creatures/earth/hadal_maw exported (log OK, 115.6 s, peak 676 MB).

## Ready for review
- B-146 UI: review_b146_ui_preview.png (panels, switch, three title cards). B-147: plants, four creatures, vent_mouth den (previews in blender/preview/review_b147_*).

## Handoffs (unrouted only)
-> UNITY (B-132, exported 0f9e0ab): delete the eight .meta files of the removed stag / wolf v2 files; creatures/earth/bear is a new key (no SpeciesSpec yet; under D-087 its react is the rear-up + huff).
-> UNITY (B-133 exported 27143e1): backgrounds/earth/forest and /coast load by ConfigureFor("earth", "forest" / "coast"); CartoonStage pins EarthScene = "plains", so biome selection is yours.
-> UNITY (B-135): swimmers have pivot [0.5, 0.5]; the clip at index 1 is swim; keep the pivot >= 0.38 / 0.87 / 0.70 m (pike / shark / squid) above the sea floor.
-> UNITY (U-118, D-126): creatures/mars/tube_lurker idles and reacts behind props/mars/tube_mound on the same pivot (mound json den_for, the creature row den); dustskater + scree_stalker exports remove their v2 files (replaces_v2).
-> UNITY (B-128, on import): def.icon = "icons/<key>/base" for soil, grass, regolith, snow, mercury_regolith, mercury_basalt, sulfide, tessera.

## Blockers
none.

## Proposals (undecided only)
none (the lit variants ruled in D-142).

## Rules I keep (from slips this session)
- While another role holds the lock, run only jobs already measured <= 150 MB; a new job (or a new whole preview) is first measured in a free gap, never estimated from its parts.
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073). The same for RAM: read it in its own call, then decide.
- A want is filed only when the queue says I am next after the running job; never while the other role's multi-lock job is between locks.
- Light work while another role's heavy job runs: <= ~150 MB; lock-free otherwise <= ~300 MB (D-109); under 0.3 GB free, code only. Measure a new path on one part / a few frames first.
- Measure every new export path's frames against the 2 px edge and the ground line before the export.
- Short jobs run in the foreground; no background waiters (the harness reaps them under memory pressure): check the locks folder each turn.

## For USER_ACTIONS
none.

## HeavyJobLock
none held; no want of mine on file (UNITY's want 12:49:57 goes next, D-037; my studies slot after it).
