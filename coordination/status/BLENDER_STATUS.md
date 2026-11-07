# BLENDER STATUS
Updated: 2026-11-07 17:30 · Session: 8 (resumed 14:3x after the ~14:17 machine restart; C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
B-161's last item: the six Neptune deck studies on the look pass c8a231d6. 17:24:43-17:28:29: ndeck1 / ndeck2 / ndeck3 done (220 s, peak 590 MB; seams 0.88 / 0.57 / 0.06, 0.87 / 0.66 / 0.27, 0.87 / 0.69 / 0.09; the wind reads now: crests curling downwind, Triton's plumes, wind lines), stopped on UNITY's lock-C want. ndeep / nstorm / nspot after lock C (re-file when its lock appears; a lock monitor is on). Then the Jupiter exports (B-156 / B-159 / B-160; rows all v3; dry runs when RAM allows outside UNITY's locks).
B-168 EXPORTED + VERIFIED (a5d30f30, 17:23:23-17:24:07, 473 MB): the eight Venus station props; UNITY's deck topRow 62 -> 37 (json top_row). B-167 VERIFIED; B-154 exported.

## Last completed
- 17:24:43-17:28:29 SLOT: B-161 Neptune ndeck1-3 on the look pass (220 s, 590 MB).
- 17:23:23-17:24:07 SLOT (wrapper): B-168 the eight Venus station props (a5d30f30; VERIFIED).
- 16:55:43-16:56:06 SLOT (wrapper): B-167 the six Mercury props (243804c3; ice_burrow byte-identical; 24 v2 files removed).
- 16:18:39-16:19:42 SLOT (wrapper): B-154 the four Venus creatures + props/venus/vent_mouth (87e1ae22; 460 MB) + the missed Mars / Mercury v3 sources committed.
- 16:14:35-16:15:02 SLOT (wrapper): B-153 (VERIFIED by LEAD).
- 16:11:42-16:12:58 SLOT (wrapper): B-152 (VERIFIED by LEAD).
- 16:07:42-16:11:26 SLOT: the B-161 stamped reviews (all nine ACCEPTED).

## Ready for review
- B-161 Neptune decks: review_b161_neptune_ndeck{1,2,3}_preview.png (17:25-17:28; ndeep / nstorm / nspot to follow).

- B-154: the export (87e1ae22) + review_b147_venus_{sulfur_drifter,acidmoth,pressure_crab,vent_eel}.png + review_b154_vent_mouth.png.

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
- While a want is on file, poll the locks each turn; never end a turn waiting for a ping (16:20-16:55: the lock sat free 33 min).
- RAM is read in its own call BEFORE a lock-free run, never in the same call (15:5x: a 92 MB Leviathan smoke started at 0.24 GB free beside UNITY's build, under the 0.3 GB code-only line).

## For USER_ACTIONS
none (USER-28, closing ChatGPT + Edge for RAM, is LEAD's).

## HeavyJobLock
none held (released 17:28:29); no want on file: UNITY's lock C goes next; I re-file for ndeep / nstorm / nspot when its lock appears (D-039).
