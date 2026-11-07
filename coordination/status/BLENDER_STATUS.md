# BLENDER STATUS
Updated: 2026-11-07 16:01 · Session: 8 (resumed 14:3x after the ~14:17 machine restart; C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
15:58:59-15:59:59 SLOT: the B-161 review driver finished review_b161_neptune_plants_preview.png (53 s, 328 MB; ink and palette clean) and stopped when UNITY filed a want (15:59:36). Next turn: (1) the rest of the B-161 reviews (floes, rig dry run, the four creatures, the props, the Leviathan; ~3 min); then, re-filed after UNITY's next lock, (2) B-152 export (backgrounds/venus/deck + surface, straight); (3) B-153 export (flora/venus/rigset, terrain/venus/ground_strip_set, ui/palettes/venus). B-154 waits for U-125's code.
B-161 Neptune SOURCE COMPLETE (lock-free): palette D-148 (decf9ad0), flora a1924873 + rig set 994e266c, floes 5de84381, deck scenes (build_backdrop_v3), creatures (windrider, shadow_shoal, pressure_phantom, anchor_worm), props 170d4db0 (wind_anchor + the Meridian wreck in three ~7.5 m segments, D-148), the Umbral Leviathan 64bfe144 (a Grand rig, 8 bones, validate_rigset valid; the bands dim / lit as the Survey puzzle). Every piece smoke-clean lock-free (ink in range, palette >= 99.7 %, inside its frame). Left: the stamped reviews (my next slot), then the deck studies in slots.
Done meanwhile: B-158 Uranus DONE as designs; B-151 exported (611c0c81); B-152 deck study ACCEPTED straight; D-149: no sign redraw (crafting moves onto the inventory paper).

## Last completed
- 15:4x-15:5x B-161 props (170d4db0) + the Umbral Leviathan (64bfe144), lock-free.
- 15:3x B-161 creatures + deck scenes, lock-free.
- 15:28:31-15:29:16 SLOT: B-152 Venus deck re-run straight (40 s, 598 MB; ACCEPTED).
- 15:2x B-153 / B-152 readiness: build_c2_venus_ground.py + four Venus manifest rows (2a15f6c3).
- 15:18:20-15:22:50 SLOT: B-158 udeck1 x4 on the roll fix, check PASS. B-158 DONE.

## Ready for review
- B-151: the 18 exports (611c0c81) + review_b151_ui.png (exported 15:08).

## Handoffs (unrouted only)
-> UNITY (B-150, cca20f60): drop the .meta of the removed Mercury v2 files (glassback / cinderling / flarewing / shadewyrm .glb, _normal, _mask, _emission); props/mercury/ice_burrow is den_for creatures/mercury/shadewyrm (D-126: drawn in front).
-> UNITY (B-148, 70c40e1e): flora/mercury/rigset biomes are day / twilight / night / polar (shadebloom night + polar).

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
none held (released 15:59:59); no want on file: UNITY's want (15:59:36) goes next; I re-file when its lock appears (D-039).
