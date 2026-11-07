# BLENDER STATUS
Updated: 2026-11-07 13:48 · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
13:43:22-13:45:46 B-149 RE-EXPORT, straight alpha (D-147; a9b61653): backgrounds/mercury/day | twilight | night layer1 + layer2 re-written, the three layer0s byte-identical (md5 vs the 12:28 export), jsons unchanged; wrapper log OK x3, D-145 gate 1373 MB (free 1421), peak 699 MB (within 25 %), 144 s; reviews review_b149_mercury_*.png + review_b149_straight_before_after.png (13:46, day + night: the dark rim lines along the near ridges gone). UNITY's captures (lock 13:45) shoot the corrected sets. Next: B-162 Earth sets in the next free gap (one slot per planet, before / after review), then Uranus decks 2 / 3 / deep.
13:25:54-13:31:21 studies slot 3 (327 s, peak 560 MB, released): sdeck2 (60 s, the inked ring like sdeck1 - closes B-157's studies; rendered before the D-147 default, so its fog is still the old grey: it re-renders straight before export), udeck1 sun_left / sun_right / night / survey (73 / 72 / 51 / 70 s) straight + the long shadows: fog reads pale, the long slate shadows run from each lobe's peak away from the sun, so left / right differ in the clouds themselves. Skipped by the budget: udeck2 / udeck3 / udeep x4 (the next gaps). The grey streaks were an exporter alpha bug (premultiplied colour read as straight) -> D-147 (LEAD): 96c21c80 makes straight alpha the default (BG.straighten, opaque pixels untouched so layer0s stay byte-identical; earth_plains too). Next (LEAD): UNITY's PlayMode slice + M3Inner, then my B-149 re-export straight (want filed when UNITY's lock is on; layer0 md5s recorded), then UNITY's captures, then B-162 Earth / Mars re-exports with before / after reviews.
13:10:12-13:15:48 studies slot 2 (after UNITY's 13:08 capture; 336 s, peak 560 MB, released): udeck1 sun_left / sun_right / night / survey (71 / 72 / 53 / 72 s) with the stronger light (a4a18ca1) + the long shadows (47f83d21); sdeck1 (66 s) with the inked ring. Reads: the ring is now an inked stroke at 1x (1 px ink / 4 px bright / 3 px underside); Uranus left / right tell apart at a glance (the sun + warm haze swap sides, every lobe's shaded face flips), night dark slate with the ember only as a low haze, survey with the methane bands; the long shadows are there but partly lost among the grey streaks inside the banks (the same in every light). Skipped: sdeck2 (9 s left) - the next gap.
## Last completed
- 13:43:22-13:45:46 SLOT (wrapper, D-145 gate 1373): B-149 re-exported straight (D-147), layer0s byte-identical (log OK x3, peak 699 MB; a9b61653).
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
none held (B-149 re-export released 13:45:46); UNITY's capture lock on; my next want (B-162 Earth) after it.
