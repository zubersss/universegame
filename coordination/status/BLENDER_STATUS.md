# BLENDER STATUS
Updated: 2026-11-07 17:20 · Session: 8 (resumed 14:3x after the ~14:17 machine restart; C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
B-168 (D-151, ahead of the Neptune decks; the owner's 0.4.7 waits for it): the eight Venus station props re-inked, source 6d685baa (frames at the catalog widths so PoiPlacer's scale stays 1; the deck top_row 37 at 64 px/m, UNITY's topRow 62 -> 37; per-prop smoke clean). Next slot: its export (props/venus/b168_set + review_b168_venus_station.png), then the six Neptune decks on the look pass. Want rewritten 17:11:15 to that order; a lock monitor watches for UNITY's lock B to release.
B-161's last item, the six Neptune deck studies. 17:07:45-17:09:20 (the gap between UNITY's 0.4.6 locks A and B, caught by a lock monitor): ndeck1 + ndeck2 (48 / 41 s, peak 590 MB), the driver stopped on UNITY's lock-B want. My read: the wind did not read (layer2's 1 px dabs nearly invisible, the banks barely leaning, faint plumes and cirrus shadows) -> one look pass c8a231d6 (bolder wind + speed lines, crests sheared downwind, darker plumes and shadows); LEAD told not to judge the first two. Next slot: all six on the pass (~4.5 min). Want filed 17:09:56 behind lock B.
Then: the Jupiter exports (B-156 with B-159's first slot, B-159, B-160; the rows are all v3; scratch dry runs when RAM allows outside UNITY's build chain).
B-167 VERIFIED (LEAD 16:5x); B-154 exported; B-152 / B-153 verified.

## Last completed
- 16:55:43-16:56:06 SLOT (wrapper): B-167 the six Mercury props (243804c3; ice_burrow byte-identical; 24 v2 files removed).
- 16:18:39-16:19:42 SLOT (wrapper): B-154 the four Venus creatures + props/venus/vent_mouth (87e1ae22; 460 MB) + the missed Mars / Mercury v3 sources committed.
- 16:14:35-16:15:02 SLOT (wrapper): B-153 (VERIFIED by LEAD).
- 16:11:42-16:12:58 SLOT (wrapper): B-152 (VERIFIED by LEAD).
- 16:07:42-16:11:26 SLOT: the B-161 stamped reviews (all nine ACCEPTED).

## Ready for review

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
none held (released 17:09:20); want_blender rewritten 17:11:15 (B-168 export first, then the six Neptune decks) behind UNITY's 0.4.6 lock B.
