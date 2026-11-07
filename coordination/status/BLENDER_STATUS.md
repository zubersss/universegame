# BLENDER STATUS
Updated: 2026-11-07 14:53 · Session: 8 (resumed 14:3x after the ~14:17 machine restart; C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
14:46:29-14:50:37 URANUS DECK2 SLOT (D-112: UNITY rank 1 had no want when the gate cleared at 1.76 GB): udeck2 sun_left / sun_right / night / survey in 231 s, peak 672 MB (560 before the Stack.paint path: the next deck slots budget 672); review_b158_uranus_udeck2_{sun_left,sun_right,night,survey}_preview.png 14:47-14:50; --uranus-check deck2 PASS (layer0 / 1 / 2 alpha md5 SAME in all four lights); one geometry across the lit sets (the roll fix holds), the sun + haze and the shaded faces swap sides. Deck3 x4 (~4 min) skipped rather than overrun; it goes in my next slot after UNITY's probe (want_unity 14:50:04; I re-file only after UNITY takes the lock, D-039). Left on B-158: deck3 x4, deep x4, deck1 again before export.
14:4x D-148 (LEAD): the Neptune palette in meridian.v3.PALETTES["neptune"] + the ui/palettes/neptune manifest row (decf9ad0); the check script raises if its table and v3 differ; the report's proposals are rulings now (flora + wind sock upright; the storm rim on its own layer with a `pulse` block; the Meridian's segments ~7.5 m). Next in B-161 source: the two floe strips, the five flora (previews + the rig dry run); then B-151's dry run, the Venus rows.
14:36-14:45 B-161 Neptune design prep (lock-free; Ready since cycle 272): build_c2_neptune_palette.py (e4ef46b2, 05a4e3a4): wisp white #E4E8EE, beacon coral #C06A55, storm violet #9E88B8, wind cyan #5A98B0, abyss sage #7C9E86, Neptune blue #5E74AE, deep indigo #2C3160; the Mars checks + Neptune's (deep indigo + blue sky, cold white wisps the brightest, the card's one pale accent, exactly one warm accent, dimmer than Uranus 63 < 70, told apart from Uranus: sky dE 44): ALL PASS (11). c2_neptune_designs.md: the wind (+x, mirrored at runtime) and the breathing storm; Kitebloom / Gripweed / Pipereed / Stormlantern / Rimecomb; floe_strip_ice + floe_strip_superionic; deck1-3 / deep / storm (+ storm_meridian) notes, diamond rain on layer2; Windrider, Shadow shoal, Pressure phantom, Anchor worm (all new keys) + the Umbral Leviathan as an 8-bone Grand rig; props wind_anchor + meridian_wreck x3 (replaces_v2). Left on B-161: the previews (one review per group at 1x beside the surveyor) when RAM allows, after the Uranus decks.
Waiting: the Uranus decks slot (deck2 x4 first, --uranus-check after each deck, <= 6 min a slot) behind UNITY's 0.4.4 probe lock (rank 1); free RAM 0.58-0.72 GB since the restart (USER-28: close ChatGPT + Edge). Next lock-free: B-151's dry run, then the Venus rows (B-152 deck re-run straight ~80 s in a free gap).
14:09:59-14:10:35 B-165 reopened + re-exported (RGBA gutters, e0f476c7; peak 525 MB); UNITY measures the dip in its probe lock (U-131); Done on a flat reading.

## Last completed
- 14:46:29-14:50:37 SLOT (bundled python, lock held): B-158 udeck2 x4 studies, --uranus-check deck2 PASS (231 s, peak 672 MB).
- 14:4x B-161 D-148 palette into v3 + the manifest row (decf9ad0).
- 14:36-14:45 B-161 palette + design report (e4ef46b2, 05a4e3a4; lock-free, numpy only).
- 14:09:59-14:10:35 SLOT (wrapper, gate 1500): B-165 reopened - the nine strips with RGBA gutters, frame rects identical (log OK x4, peak 525 MB).
- 13:57:17-13:57:53 SLOT (wrapper, D-145 gate 1200): B-165 nine strips re-exported, gutters extruded, frame rects identical (log OK x4, peak 522 MB, GATE-RESET).
- 13:51:50-13:54:26 SLOT (wrapper, D-145 gate 1530): B-162 Mars sets re-exported straight (D-147), layer0s byte-identical (log OK x3, peak 768 MB).
- 13:47:56-13:49:32 SLOT (wrapper, D-145 gate 1399): B-162 Earth sets re-exported straight (D-147), layer0s byte-identical (log OK x3, peak 830 MB).
- 13:43:22-13:45:46 SLOT (wrapper, D-145 gate 1373): B-149 re-exported straight (D-147), layer0s byte-identical (log OK x3, peak 699 MB; a9b61653).

## Ready for review
- B-158 deck2 x4: review_b158_uranus_udeck2_{sun_left,sun_right,night,survey}_preview.png (14:47-14:50) + the --uranus-check deck2 PASS lines.

## Handoffs (unrouted only)
-> UNITY (B-150, cca20f60): drop the .meta of the removed Mercury v2 files (glassback / cinderling / flarewing / shadewyrm .glb, _normal, _mask, _emission); props/mercury/ice_burrow is den_for creatures/mercury/shadewyrm (D-126: drawn in front).
-> UNITY (B-148, 70c40e1e): flora/mercury/rigset biomes are day / twilight / night / polar (shadebloom night + polar).

## Blockers
none (the decks wait on the RAM gate, logged above).

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

## For USER_ACTIONS
none (USER-28, closing ChatGPT + Edge for RAM, is LEAD's).

## HeavyJobLock
none held (deck2 slot released 14:50:37); no want on file: UNITY's want (14:50:04, the 0.4.4 probe) goes next, and I re-file for deck3 only after UNITY takes the lock (D-039).
