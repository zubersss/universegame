# BLENDER STATUS
Updated: 2026-11-07 16:20 · Session: 8 (resumed 14:3x after the ~14:17 machine restart; C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
The owner-build work (0.4.6 waits for B-167, D-150), in my turns behind UNITY's locks; want filed 16:15:54 behind UNITY's check lock. Next slots: (1) B-154 export (creatures/venus sulfur_drifter / acidmoth / pressure_crab / vent_eel + props/venus/vent_mouth; the rows switched to v3 in 856f5ab4); (2) B-167 export through props/mercury/b167_set (its stamped review b167_mercury_props.png comes from the export run); (3) the six Neptune deck studies (B-161 Done on them) in budgeted slots.
B-167 SOURCE DONE (3257db89): the six Mercury props re-inked, sized to PoiCatalog (shelter 3.88 x 2.13, door 1.75 x 2.69 open 6, beacon 2.0 x 3.3, solarite 1.81 x 1.63, vault gate 3.94 x 3.56, locker 1.0 x 1.98 m), static except the door; smoke 139 MB clean (palette >= 99.9 %, ink in range); ice_burrow unchanged.
B-153 EXPORTED (9dd3798d, 16:14:35-16:15:02, 348 MB): flora/venus/rigset 508x184 (33 parts), terrain/venus/ground_strip + _deck (joins 0.54 / 0.68), ui/palettes/venus.
B-152 EXPORTED 657bb2ae + VERIFIED (LEAD). B-161: all nine previews ACCEPTED (16:1x); only the six deck studies left.

## Last completed
- 16:1x B-167 source + the set row; B-154 readiness (the Venus creature rows to v3, the vent_mouth den row).
- 16:14:35-16:15:02 SLOT (wrapper): B-153 export (log OK x3).
- 16:11:42-16:12:58 SLOT (wrapper): B-152 export (log OK x2, 713 MB).
- 16:07:42-16:11:26 SLOT: the B-161 stamped reviews (216 s, 302 MB; all ACCEPTED).
- 15:58:59-15:59:59 SLOT: review_b161_neptune_plants_preview.png.

## Ready for review
- B-153: the 9 files (9dd3798d) + review_b153_venus_rigset.png + the ground strip review.
- B-151: the 18 exports (611c0c81) + review_b151_ui.png (exported 15:08).

## Handoffs (unrouted only)
-> UNITY (B-150, cca20f60): drop the .meta of the removed Mercury v2 files (glassback / cinderling / flarewing / shadewyrm .glb, _normal, _mask, _emission); props/mercury/ice_burrow is den_for creatures/mercury/shadewyrm (D-126: drawn in front).
-> UNITY (B-148, 70c40e1e): flora/mercury/rigset biomes are day / twilight / night / polar (shadebloom night + polar).
-> UNITY (B-153): VenusKeys = terrain/venus/ground_strip (the basalt crust) + ground_strip_deck (the aerostat planks); routed by LEAD to U-125.

## Blockers
none.

## Proposals (undecided only)
none (B-161's three ruled in D-148).

## Rules I keep (from slips this session)
- A review grows with its rows: beside another role's lock, re-measure or cut it to the measured size (13:50: the 3-row before / after hit 207 MB vs 144 MB measured for 2 rows).
- While another role holds the lock, run only jobs already measured <= 150 MB; a new job (or a new whole preview) is first measured in a free gap, never estimated from its parts.
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073). The same for RAM: read it in its own call, then decide.
- A want is filed only when the queue says I am next after the running job; never while the other role's multi-lock job is between locks.
- Light work while another role's heavy job runs: <= ~150 MB; lock-free otherwise <= ~300 MB (D-109); under 0.3 GB free, code only. Measure a new path on one part / a few frames first.
- Measure every new export path's frames against the 2 px edge and the ground line before the export.
- Short jobs run in the foreground; no background waiters (the harness reaps them under memory pressure): check the locks folder each turn.
- All three sessions share one working tree: a push can race another role's; fetch + merge (never rebase) and push again.
- A stroke's line is drawn in its material's ink_hex: a coloured line needs its own line material (fill=None, ink_hex=colour); a fill-only material on an open stroke draws nothing.
- RAM is read in its own call BEFORE a lock-free run, never in the same call (15:5x: a 92 MB Leviathan smoke started at 0.24 GB free beside UNITY's build, under the 0.3 GB code-only line).

## For USER_ACTIONS
none (USER-28, closing ChatGPT + Edge for RAM, is LEAD's).

## HeavyJobLock
none held; want_blender filed 16:15:54 (B-154, then B-167) behind UNITY's check lock.
