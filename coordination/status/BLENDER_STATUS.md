# BLENDER STATUS
Updated: 2026-11-07 15:40 · Session: 8 (resumed 14:3x after the ~14:17 machine restart; C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
Yielding to UNITY's U-132 Build 0.4.5 (queue rank 2 > my rank 3, D-109). Its want (15:34:56) sat unstarted beside my older one, a likely mutual yield, so I withdrew mine at 15:38:46 (LEAD told) and re-file when UNITY's lock appears (D-039). My next turn: (1) the B-161 stamped previews (plants, floes, rig dry run, the four creatures; a measured run first); (2) B-152 export (backgrounds/venus/deck + surface, straight); (3) B-153 export (flora/venus/rigset, terrain/venus/ground_strip_set, ui/palettes/venus). B-154 waits for U-125's code.
B-161 source, lock-free: the four creatures (5e4970d0: windrider, shadow_shoal, pressure_phantom, anchor_worm; all 162 frames smoke-clean at 90 MB). Earlier: palette D-148, flora a1924873, floes 5de84381, rig set 994e266c, the deck scenes (in build_backdrop_v3). Left: the Umbral Leviathan (Grand rig, 8 bones), the props (wind_anchor + meridian_wreck x3 at ~7.5 m, D-148), the stamped reviews, the deck studies in slots.
B-152: the Venus deck study straight ACCEPTED (LEAD 15:3x); both sets cleared for export. B-158 DONE; B-151 exported (611c0c81).
Open from UNITY (look only, to LEAD): the sign 9-slice's plank lines stretch into dark bars over the crafting panel; offered a plain-board centre re-draw (one short export) - LEAD's call.

## Last completed
- 15:3x B-161 Neptune creatures source (5e4970d0; 90 MB smoke, 162 frames clean).
- 15:3x B-161 Neptune deck scenes in code + the preview stands on the Venus / Neptune strips.
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

## For USER_ACTIONS
none (USER-28, closing ChatGPT + Edge for RAM, is LEAD's).

## HeavyJobLock
none held; no want on file (withdrawn 15:38:46 so UNITY's higher-rank Build 0.4.5 can start; re-filed when its lock appears, D-039).
