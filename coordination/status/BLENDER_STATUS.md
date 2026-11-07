# BLENDER STATUS
Updated: 2026-11-07 14:12 · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
14:09:59-14:10:35 B-165 REOPENED + RE-EXPORTED (UNITY measured a ~12.7 dip every 64 px: a colour-only gutter at alpha 0 still halves the edge pixel under straight-alpha bilinear): the gutters copy the edge columns in full RGBA (1c575843); the nine strips in one wrapper job (e0f476c7), default gate 1500 after the D-145 reset (re-measured: 525 MB), log OK x4, joins unchanged, frame rects md5-identical in all nine, jsons unchanged; UNITY re-measures. Uranus (697d5a40): Stack.paint keeps every layer's alpha the same in all four lights (the rim inside the bank, the faces / long shadows painted, night's extra glints on the opaque far layer); --uranus-check <deck> prints each layer's alpha md5 per light and FAILS on a difference, a missing or a stale render. Want filed 14:11 behind UNITY's 14:10:50 lock for the Uranus decks slot (deck2 first, the check after each full deck).
13:59:36-14:04:37 Uranus slot (301 s, peak 560 MB, released): udeck2 x4 + udeck3_sun_left. Found: deck2's sun_left / sun_right rolled differently (finish() chose each layer's wrap from the finished, light-dependent image) - the season crossfade would slide the clouds. Fixed in fe6ace98: Uranus layers roll from their light-independent geometry (far banks replayed on a copy of rng; replay == real checked), the sun pre-placed for the roll, the warm ramp wrapped; other planets unchanged. Those five renders are void; remaining: udeck2 x4, udeck3 x4, udeep x4 (~3 budgeted slots), deck1 again before export.
13:57:17-13:57:53 B-165 STRIPS RE-EXPORTED (42cbd6f0 code: extrude_gutters, colour only, alpha 0): the nine strips (Earth x4, Mars x3 incl. frost, Mercury x2) in one wrapper job, log OK x4, joins unchanged, frame rects md5-identical in all nine, gutters now carry the edge columns (alpha 0), jsons unchanged. D-145's overshoot reset fired for the first time: 522 MB vs the 347 MB estimate (Mercury's 2-strip set; Earth renders 4) -> terrain:ground_strip_set on the default gate until re-measured. Next: Uranus decks 2 / 3 / deep x4 in budgeted slots (want filed while UNITY's lock is on).
13:51:50-13:54:26 B-162 MARS RE-EXPORT, straight alpha (D-147; bc0009b9): backgrounds/mars/plains | canyon | storm layer1 + layer2 re-written, layer0s byte-identical (md5), jsons unchanged; wrapper log OK x3, D-145 gate 1530 MB (free 2531), peak 768 MB (est 830), 157 s; review_b162_mars_{plains,canyon,storm}_before_after.png (13:55, one row each, 82 MB each: the storm's dust reads pale instead of murky grey, the dark rims along the mesa line gone). B-162 complete. Next: B-165 (LEAD): the strip exporter extrudes each frame's edge columns into its gutters (colour only, alpha 0), then the nine strips re-exported in one slot (frame rects md5-identical); then Uranus decks 2 / 3 / deep x4.
## Last completed
- 14:09:59-14:10:35 SLOT (wrapper, gate 1500): B-165 reopened - the nine strips with RGBA gutters, frame rects identical (log OK x4, peak 525 MB).
- 13:57:17-13:57:53 SLOT (wrapper, D-145 gate 1200): B-165 nine strips re-exported, gutters extruded, frame rects identical (log OK x4, peak 522 MB, GATE-RESET).
- 13:51:50-13:54:26 SLOT (wrapper, D-145 gate 1530): B-162 Mars sets re-exported straight (D-147), layer0s byte-identical (log OK x3, peak 768 MB).
- 13:47:56-13:49:32 SLOT (wrapper, D-145 gate 1399): B-162 Earth sets re-exported straight (D-147), layer0s byte-identical (log OK x3, peak 830 MB).
- 13:43:22-13:45:46 SLOT (wrapper, D-145 gate 1373): B-149 re-exported straight (D-147), layer0s byte-identical (log OK x3, peak 699 MB; a9b61653).
- 12:45:47-12:49:08 SLOT (wrapper, D-145 gate 1200): B-150 creatures/mercury x4 + props/mercury/ice_burrow exported (log OK x5, peak 389 MB; cca20f60).
- 12:44:31-12:45:14 SLOT (wrapper, D-145 gate 1200): B-148 flora/mercury/rigset + terrain/mercury/ground_strip(_slate) + ui/palettes/mercury exported (log OK x3, peak 347 MB; 70c40e1e).
- 12:42 D-145 in tools/blender_render.ps1 (2194f067): per-job gate from measured peaks, GATE / GATE-RESET log lines.
- 12:23:14-12:28:27 SLOT (wrapper): B-149 backgrounds/mercury/day | twilight | night exported (log OK x3, 313 s, peak 673 MB; 1e99fcc4).
- 11:24:11-11:24:21 SLOT (wrapper): D-143 terrain/mars/ground_strip_frost exported (log OK, 308 MB; 7db366cf).

## Ready for review
- B-162 Mars re-export (straight alpha): review_b162_mars_{plains,canyon,storm}_before_after.png.

## Handoffs (unrouted only)
-> UNITY (B-150, cca20f60): drop the .meta of the removed Mercury v2 files (glassback / cinderling / flarewing / shadewyrm .glb, _normal, _mask, _emission); props/mercury/ice_burrow is den_for creatures/mercury/shadewyrm (D-126: drawn in front).
-> UNITY (B-148, 70c40e1e): flora/mercury/rigset biomes are day / twilight / night / polar (shadebloom night + polar).

## Blockers
none.

## Proposals (undecided only)
none (the lit variants ruled in D-142).

## Rules I keep (from slips this session)
- A review grows with its rows: beside another role's lock, re-measure or cut it to the measured size (13:50: the 3-row before / after hit 207 MB vs 144 MB measured for 2 rows).
- While another role holds the lock, run only jobs already measured <= 150 MB; a new job (or a new whole preview) is first measured in a free gap, never estimated from its parts.
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073). The same for RAM: read it in its own call, then decide.
- A want is filed only when the queue says I am next after the running job; never while the other role's multi-lock job is between locks.
- Light work while another role's heavy job runs: <= ~150 MB; lock-free otherwise <= ~300 MB (D-109); under 0.3 GB free, code only. Measure a new path on one part / a few frames first.
- Measure every new export path's frames against the 2 px edge and the ground line before the export.
- Short jobs run in the foreground; no background waiters (the harness reaps them under memory pressure): check the locks folder each turn.

## For USER_ACTIONS
none.

## HeavyJobLock
none held (B-165 released 14:10:35); want_blender filed 14:11 (Uranus decks) behind UNITY's 14:10:50 lock.
