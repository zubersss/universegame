# BLENDER STATUS
Updated: 2026-11-07 14:00 · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
13:57:17-13:57:53 B-165 STRIPS RE-EXPORTED (42cbd6f0 code: extrude_gutters, colour only, alpha 0): the nine strips (Earth x4, Mars x3 incl. frost, Mercury x2) in one wrapper job, log OK x4, joins unchanged, frame rects md5-identical in all nine, gutters now carry the edge columns (alpha 0), jsons unchanged. D-145's overshoot reset fired for the first time: 522 MB vs the 347 MB estimate (Mercury's 2-strip set; Earth renders 4) -> terrain:ground_strip_set on the default gate until re-measured. Next: Uranus decks 2 / 3 / deep x4 in budgeted slots (want filed while UNITY's lock is on).
13:51:50-13:54:26 B-162 MARS RE-EXPORT, straight alpha (D-147; bc0009b9): backgrounds/mars/plains | canyon | storm layer1 + layer2 re-written, layer0s byte-identical (md5), jsons unchanged; wrapper log OK x3, D-145 gate 1530 MB (free 2531), peak 768 MB (est 830), 157 s; review_b162_mars_{plains,canyon,storm}_before_after.png (13:55, one row each, 82 MB each: the storm's dust reads pale instead of murky grey, the dark rims along the mesa line gone). B-162 complete. Next: B-165 (LEAD): the strip exporter extrudes each frame's edge columns into its gutters (colour only, alpha 0), then the nine strips re-exported in one slot (frame rects md5-identical); then Uranus decks 2 / 3 / deep x4.
13:47:56-13:49:32 B-162 EARTH RE-EXPORT, straight alpha (D-147): backgrounds/earth/plains | forest | coast layer1 + layer2 re-written, layer0s byte-identical (md5), jsons unchanged; wrapper log OK x3, D-145 gate 1399 MB (free 2737), peak 830 MB (+19 %, within 25 %), 96 s; review_b162_earth_straight_before_after.png (13:49: the dark rims along the near ridges, canopies, dune line gone). Slip: that before / after review peaked at 207 MB while UNITY's lock was on (measured 144 MB with two rows; the third row grew it) - over my 150 MB beside-a-lock line. Next: B-162 Mars (plains, canyon, storm) in the next free gap, then Uranus decks 2 / 3 / deep.
13:43:22-13:45:46 B-149 RE-EXPORT, straight alpha (D-147; a9b61653): backgrounds/mercury/day | twilight | night layer1 + layer2 re-written, the three layer0s byte-identical (md5 vs the 12:28 export), jsons unchanged; wrapper log OK x3, D-145 gate 1373 MB (free 1421), peak 699 MB (within 25 %), 144 s; reviews review_b149_mercury_*.png + review_b149_straight_before_after.png (13:46, day + night: the dark rim lines along the near ridges gone). UNITY's captures (lock 13:45) shoot the corrected sets. Next: B-162 Earth sets in the next free gap (one slot per planet, before / after review), then Uranus decks 2 / 3 / deep.
13:25:54-13:31:21 studies slot 3 (327 s, peak 560 MB, released): sdeck2 (60 s, the inked ring like sdeck1 - closes B-157's studies; rendered before the D-147 default, so its fog is still the old grey: it re-renders straight before export), udeck1 sun_left / sun_right / night / survey (73 / 72 / 51 / 70 s) straight + the long shadows: fog reads pale, the long slate shadows run from each lobe's peak away from the sun, so left / right differ in the clouds themselves. Skipped by the budget: udeck2 / udeck3 / udeep x4 (the next gaps). The grey streaks were an exporter alpha bug (premultiplied colour read as straight) -> D-147 (LEAD): 96c21c80 makes straight alpha the default (BG.straighten, opaque pixels untouched so layer0s stay byte-identical; earth_plains too). Next (LEAD): UNITY's PlayMode slice + M3Inner, then my B-149 re-export straight (want filed when UNITY's lock is on; layer0 md5s recorded), then UNITY's captures, then B-162 Earth / Mars re-exports with before / after reviews.
13:10:12-13:15:48 studies slot 2 (after UNITY's 13:08 capture; 336 s, peak 560 MB, released): udeck1 sun_left / sun_right / night / survey (71 / 72 / 53 / 72 s) with the stronger light (a4a18ca1) + the long shadows (47f83d21); sdeck1 (66 s) with the inked ring. Reads: the ring is now an inked stroke at 1x (1 px ink / 4 px bright / 3 px underside); Uranus left / right tell apart at a glance (the sun + warm haze swap sides, every lobe's shaded face flips), night dark slate with the ember only as a low haze, survey with the methane bands; the long shadows are there but partly lost among the grey streaks inside the banks (the same in every light). Skipped: sdeck2 (9 s left) - the next gap.
## Last completed
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
none held (B-165 released 13:57:53); UNITY's want on file goes next; the Uranus decks want once its lock is on.
