# BLENDER STATUS
Updated: 2026-11-07 15:27 · Session: 8 (resumed 14:3x after the ~14:17 machine restart; C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
Venus exports next (B-152 / B-153 cleared: U-123 Done), each one slot in my turns behind UNITY's wants. Want filed 15:25 (UNITY's U-124 lock since 15:22:59; 0.23 GB free under the Editor: code only meanwhile). Order: (1) the Venus deck study re-run straight (~80 s, D-147; accepted on sight); (2) the B-161 stamped previews (plants, floes, rig dry run) in a free gap; (3) B-152 export (backgrounds/venus/deck + surface, straight); (4) B-153 export (flora/venus/rigset - its dry run passed 09:03, 33 parts, json valid -, terrain/venus/ground_strip_set, ui/palettes/venus). B-154 waits for U-125's code.
B-153 readiness DONE lock-free (2a15f6c3): build_c2_venus_ground.py - terrain/venus/ground_strip (the basalt crust) + ground_strip_deck (the aerostat planks, a new kind); smoke 61 MB: joins 0.54 / 0.68, silhouette identical in all 32 edges, palette 100 % (the basalt brown kept off the edges: it sits inside the edge check's 40-level ink tolerance). Manifest rows added for terrain/venus/ground_strip_set, flora/venus/rigset, backgrounds/venus/deck + surface.
B-158 Uranus DONE as designs (LEAD 15:2x): deck1 x4 re-run on the roll fix 15:18:20-15:22:50 (258 s, 673 MB, --uranus-check deck1 PASS); all four decks pass in every light; exports as B-166 with U-130.
B-151 EXPORTED 611c0c81 (15:07-15:09, 942 MB); UNITY imports it in its U-124 lock.
B-161 Neptune source complete (palette D-148, flora a1924873, floes 5de84381, rig set 994e266c); left: the three stamped reviews, then deck studies in slots, creatures, props, the Leviathan.

## Last completed
- 15:2x B-153 / B-152 readiness: build_c2_venus_ground.py + four Venus manifest rows (2a15f6c3; lock-free, 61 MB smoke).
- 15:18:20-15:22:50 SLOT (bundled python): B-158 udeck1 x4 on the roll fix, --uranus-check deck1 PASS (258 s, 673 MB). B-158 DONE.
- 15:10:03-15:14:45 SLOT: B-158 udeep x4, --uranus-check deep PASS (277 s, 673 MB; ACCEPTED).
- 15:07:55-15:09:03 SLOT (wrapper): B-151 C3 UI export (log OK, 942 MB; 611c0c81).
- 15:0x B-161 floes (5de84381) + rig set (994e266c) sources (88 / 46 MB checks).
- 14:46-15:01 SLOTS: B-158 udeck2 / udeck3 x4, checks PASS (ACCEPTED).

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
none held (deck1 slot released 15:22:50); want_blender filed 15:25:04 (the Venus deck re-run, then the B-161 reviews) behind UNITY's U-124 lock.
