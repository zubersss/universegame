# BLENDER STATUS
Updated: 2026-11-07 15:31 · Session: 8 (resumed 14:3x after the ~14:17 machine restart; C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
Venus exports + B-161 reviews, each in my turns behind UNITY's wants (UNITY's U-124 lock since 15:29:26; my want filed 15:29:45). Order: (1) the B-161 stamped previews (plants, floes, rig dry run; <= 3 min, skipped at 15:29 when UNITY's want arrived mid-slot); (2) B-152 export (backgrounds/venus/deck + surface, straight); (3) B-153 export (flora/venus/rigset, terrain/venus/ground_strip_set, ui/palettes/venus). B-154 waits for U-125's code.
15:28:31-15:29:16 SLOT: B-152 Venus deck study re-run straight (40 s, 598 MB; seams 0.84 / 0.00 / 0.28; review_b147_venus_deck_preview.png 15:29, now on the B-153 deck planks). Released on UNITY's 15:29:07 want (D-037).
B-161 Neptune deck scenes in code (pushed with the re-run): build_backdrop_v3.neptune_scene deck1 / deck2 / deck3 / deep / storm / spot (preview names ndeck1..nspot, seeds 15101-15105); the storm's rim + companion clouds alone on layer1 with the D-148 pulse block (pivot_uv 0.5 / 0.5, roll=0); spot = storm + the Meridian (its own rng: layers 1-2 identical to storm's). The studies run in slots after the Venus exports.
B-153 readiness: build_c2_venus_ground.py (2a15f6c3) + the four Venus manifest rows; the rig dry run passed 09:03.
B-158 Uranus DONE as designs; B-151 exported (611c0c81); B-161 source: palette D-148, flora a1924873, floes 5de84381, rig set 994e266c.

## Last completed
- 15:3x B-161 Neptune deck scenes (code; registered, 31 MB import check) + the preview stands on the Venus / Neptune strips.
- 15:28:31-15:29:16 SLOT: B-152 Venus deck re-run straight (40 s, 598 MB).
- 15:2x B-153 / B-152 readiness: build_c2_venus_ground.py + four Venus manifest rows (2a15f6c3; 61 MB smoke).
- 15:18:20-15:22:50 SLOT: B-158 udeck1 x4 on the roll fix, check PASS (258 s, 673 MB). B-158 DONE.
- 15:07:55-15:09:03 SLOT (wrapper): B-151 C3 UI export (log OK, 942 MB; 611c0c81).

## Ready for review
- B-151: the 18 exports (611c0c81) + review_b151_ui.png (exported 15:08).
- B-152: review_b147_venus_deck_preview.png (15:29, straight; accepted on sight per the card).

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
none held (the Venus re-run slot released 15:29:16); want_blender filed 15:29:45 (the B-161 reviews, then B-152) behind UNITY's U-124 lock.
