# BLENDER STATUS
Updated: 2026-11-07 15:17 · Session: 8 (resumed 14:3x after the ~14:17 machine restart; C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
B-158 Uranus: deck2 + deck3 ACCEPTED; 15:10:03-15:14:45 DEEP SLOT (lock free, no other want, D-112): udeep x4 in 277 s, peak 673 MB; review_b158_uranus_udeep_{sun_left,sun_right,night,survey}_preview.png 15:10-15:14; --uranus-check deep PASS; the CRUSH band lettered on layer2, the sun swaps sides over one geometry. Released 15:14:45; want_unity on file, so UNITY goes next; I re-file for deck1 x4 (its 13:2x renders predate the roll fix) once UNITY's lock appears (D-039). B-158 Done after deck1.
B-151 EXPORTED (LEAD moved it ahead of deep: UNITY's C3 code green): wrapper 15:07:55-15:09:03, log OK, 53.8 s, peak 942 MB; 611c0c81 (18 files, no .meta): five 9-slice panels with slice [l,t,r,b], the Earth / Mars / Mercury cards 1600x452, the film switch with parts off / on; review_b151_ui.png (exported 15:08). UNITY imports it next.
B-161 Neptune SOURCE COMPLETE (lock-free): palette D-148 (decf9ad0), flora a1924873, floes 5de84381 (ice: rounded windward cap, ragged lee cap, wind-carved crests; superionic: violet crust, shard, cracks, glints; joins 0.89 / 0.41, caps joined, silhouette identical, palette 100 %), rig set 994e266c (kitebloom 4 bones, gripweed 1, pipereed 5 with react.also, stormlantern 2 with the 8-beat glow, rimecomb 1; 24 parts 500x176, validate_rigset clean). Left on B-161: the three stamped reviews (plants, floes, rig dry run; ~300 MB each: a free gap, not beside UNITY's lock), then the deck studies in slots, creatures, props, the Leviathan.
Next lock-free / gaps: the B-161 reviews, the Venus deck re-run straight (B-152, ~80 s, in a gap), deck1 x4 in my next slot.

## Last completed
- 15:10:03-15:14:45 SLOT (bundled python, lock held): B-158 udeep x4 studies, --uranus-check deep PASS (277 s, peak 673 MB).
- 15:07:55-15:09:03 SLOT (wrapper): B-151 C3 UI export (log OK, 942 MB; 611c0c81).
- 15:0x B-161 floes (5de84381) + rig set (994e266c) sources, checked lock-free under a 150 MB kill cap (88 / 46 MB).
- 14:56:51-15:01:00 SLOT: B-158 udeck3 x4, --uranus-check deck3 PASS (244 s, 672 MB; ACCEPTED).
- 14:46:29-14:50:37 SLOT: B-158 udeck2 x4, --uranus-check deck2 PASS (231 s, 672 MB; ACCEPTED).
- 14:36-14:5x B-161 palette + report (ACCEPTED as D-148) + flora source.

## Ready for review
- B-151: the 18 exports (611c0c81) + review_b151_ui.png (exported 15:08).
- B-158 deep x4: review_b158_uranus_udeep_{sun_left,sun_right,night,survey}_preview.png (15:10-15:14) + the --uranus-check deep PASS lines.

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
none held (deep slot released 15:14:45); no want on file: UNITY's want goes next; I re-file for deck1 x4 only after UNITY takes the lock (D-039).
