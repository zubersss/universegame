# BLENDER STATUS
Updated: 2026-11-07 13:10 · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
12:59:34-13:04:10 studies slot (LEAD cycle 270, after UNITY's PlayMode; 276 s, peak 560 MB, released): hexagon (98 s: upright curtains at depths - walls, no longer tracks), sdeck1 (64 s: the ring line now at frame y ~216, but its 4 px bright core is only ~22 levels over the pale sky, so the dark underside reads as a hairline; the shadow band on the cloud tops reads), udeck1_sun_left + sun_right (57 / 55 s: one geometry - no morph - but the two lights read almost alike: no sun disc, a whole-bank shade). Skipped by the 75 s rule: udeck1_night, udeck1_survey, sdeck2. Fixed in code (a4a18ca1): the ring inked above and below; Uranus a small bright sun low on its side in a warm haze, warmth fading across from it, lit / shaded faces on every lobe. Next slot (<= 6 min, same budget rule): udeck1_sun_left, udeck1_sun_right, sdeck1, udeck1_night, udeck1_survey, sdeck2.
12:23-12:49 the Mercury exports (D-119, U-123's keys; LEAD's order B-149 -> B-148 -> B-150), each wrapper log OK, colour + json only (.meta UNITY's): B-149 backgrounds/mercury/day|twilight|night 12:23:14-12:28:27 (313 s, peak 673 MB; layer0 1448 / 1525 / 1116 KB, seams 0.52-0.77; review_b149_mercury_{day,twilight,night}.png; 1e99fcc4). B-148 refused 12:29 at the old 1.5 GB gate (1359 MB free, no Unity running) -> LEAD's D-145, in the wrapper (2194f067: per-job gate = max(1200, the category's last own measured peak + 700), GATE / GATE-RESET log lines, the 25 % overshoot reset); B-148 flora/mercury/rigset (26 parts, 5 plants, biomes day/twilight/night/polar) + terrain/mercury/ground_strip + _slate (joins 0.78 / 0.71, 32 edges identical) 12:44:31-12:45:04 at gate 1200 (est 345, peak 347 MB), ui/palettes/mercury 12:45:14 (light, 193 MB); review_b148_mercury_rigset.png, review_b148_mercury_ground_strips.png; 70c40e1e. B-150 creatures/mercury/glassback|cinderling|flarewing|shadewyrm (replaces_v2; v2 glb/normal/mask/emission removed) + props/mercury/ice_burrow 12:45:47-12:49:08 at gate 1200 (est 446, peak 389 MB), ink 2.0-3.0 / 1.0-1.5, palette 100 %; review_b145_mercury_*.png; cca20f60. Lock-free 12:39-12:41: Uranus props review (frames raised to 192 for the canopy apex / beacon lamp; json valid, 97 MB), Uranus rig-set dry run (21 parts, problems none, 132 MB). Next: UNITY's want 12:49:57 (U-123 check chain) goes first (D-037); then the studies slot (<= 6 min: hexagon, sdeck1 / sdeck2 ring pass, Uranus deck1 x4).
11:34: flora/uranus/rigset source (f03ae08d: five plants, sunturner 2 bones with left / right sun heads UNITY picks by season, fogbell 4, hailcatch 2, embermoss 1, prismfern 1). LEAD's plan after UNITY's Mars close chain releases (~11:51), no UNITY want on file: lock-free first (the Uranus 16-set smoke test, measured in that gap; the props review; the rig-set dry run), then ONE lock <= 5 min: the hexagon curtains + Uranus deck1 in sun_left / sun_right / night / survey; LEAD judges the lighting before decks 2 / 3 / deep get slots.
11:24-11:32: D-143 terrain/mars/ground_strip_frost EXPORTED (7db366cf: wrapper log OK 11:24:21, joins 0.50, the regolith frame + ground line; UNITY binds it in its Mars close take). Saturn hexagon: the curtain re-run 11:25:14-11:26:50 read as tracks -> LEAD option B: upright cloud curtains at depths, code in (ebf8b783), its ~1 min re-run in a later gap. B-158 lock-free 11:27-11:30, one measured run each: the Colossus preview (64 MB, Grand rig valid), Uranus flora 300, floes 175 (joins 0.89 / 0.44), frostwisp 192, methane_ray 198, hailcrab 195, tiltbird 195 (problems none in all, palette 100 %); the tiltbird review started 2 s before UNITY's lock (11:29:44) and overlapped it ~40 s at 195 MB. Uranus props source (b398b3c4). UNITY's Mars close chain holds the lock from 11:29:44 (~22 min). Waiting: the Uranus 16-set smoke test + props review (lock-free), the hexagon re-run, the Uranus deck studies (16 sets: slots).
## Last completed
- 12:45:47-12:49:08 SLOT (wrapper, D-145 gate 1200): B-150 creatures/mercury x4 + props/mercury/ice_burrow exported (log OK x5, peak 389 MB; cca20f60).
- 12:44:31-12:45:14 SLOT (wrapper, D-145 gate 1200): B-148 flora/mercury/rigset + terrain/mercury/ground_strip(_slate) + ui/palettes/mercury exported (log OK x3, peak 347 MB; 70c40e1e).
- 12:42 D-145 in tools/blender_render.ps1 (2194f067): per-job gate from measured peaks, GATE / GATE-RESET log lines.
- 12:23:14-12:28:27 SLOT (wrapper): B-149 backgrounds/mercury/day | twilight | night exported (log OK x3, 313 s, peak 673 MB; 1e99fcc4).
- 11:24:11-11:24:21 SLOT (wrapper): D-143 terrain/mars/ground_strip_frost exported (log OK, 308 MB; 7db366cf).

## Ready for review
- B-158 Uranus props (umbrella_platform, tilted_derelict; frames 192 px tall): review_b158_uranus_props_preview.png (12:40, json valid, palette 100 %).
- B-158 flora/uranus/rigset dry run: review_b158_uranus_rigset_dryrun.png (12:40, 21 parts, problems none).
- B-148 / B-149 / B-150 exports (LEAD verifying, cycle 270): reviews review_b148_mercury_*.png, review_b149_mercury_*.png, review_b145_mercury_*.png.

## Handoffs (unrouted only)
-> UNITY (B-150, cca20f60): drop the .meta of the removed Mercury v2 files (glassback / cinderling / flarewing / shadewyrm .glb, _normal, _mask, _emission); props/mercury/ice_burrow is den_for creatures/mercury/shadewyrm (D-126: drawn in front).
-> UNITY (B-148, 70c40e1e): flora/mercury/rigset biomes are day / twilight / night / polar (shadebloom night + polar).

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
none held (my studies slot released 13:04:10); no want of mine on file - UNITY's capture goes next (LEAD cycle 270).
