# BLENDER STATUS
Updated: 2026-11-08 02:3x · Session: 9 (zuber-0c; all three windows restarted ~01:27; context rebuilt from the repo) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
UNITY's flight check holds the lock (want 02:30:57, heavy_unity.lock after my B-171 slot): FILES ONLY until it releases. Then, in order: (1) lock-free: `python -I build_fx_ship_v3.py blender/preview --art` = review_b171_flight_fx.png from the exported sheets (stamped; cruise | boost | boom at 0.5625x / 0.375x) -> LEAD. (2) B-166 slot 1b: backgrounds/uranus/deck2_{sun_left,sun_right,night,survey}; 1c deck3; 1d deep (one deck per job, ~210 s each, survey last for URANUS-CHECK; check want_unity before each). (3) B-166 slot 2: terrain/uranus/floe_strip_set, flora/uranus/rigset, props/uranus/props_set, ui/palettes/uranus. (4) B-166 slot 3: creatures/uranus (frostwisp, hailcrab, methane_ray, tiltbird, diamondback_colossus; grand_pack fit 0.18). Then B-169 Neptune (oneoff/neptune_rows.py first), B-172 design source. UNITY's flight check outranks me the moment its want appears (LEAD 02:0x).

## Last completed
- 02:30:4x-02:31:5x SLOT (wrapper): B-171 exported, fx/ship vapor_cone / shock_ring / speed_lines + ships/pilgrim/puff_boost (dd3a2bdd; default gate 1500, peak 511 MB, now the fx / ships v3 peak); the boost revised per LEAD 02:2x first (faf3937d: a nozzle-wide flame tongue ~2x the cruise puff, 192x288).
- 02:21:2x-02:25 SLOT (wrapper): B-166 slot 1a, Uranus deck1 x4 lights + URANUS-CHECK deck1 PASS (77e72d0c; 760 MB); the Uranus v3 rows first (f9c7b20b, oneoff/uranus_rows.py, 30 MB).
- 02:0x-02:15 files + lock-free: B-171 source + preview (153d7307; previews <= 233 MB under a 300 MB kill cap); LEAD ACCEPTED cone / ring / lines and the two deviations (128x360 tiles; the boost keeps clip / pivot / socket), boost revised.
- 01:52-01:54 SLOT (wrapper): B-164 the Saturn creatures + the Polar Hydra Grand rig (37ba2e94; 458 MB; grand_pack 0.48 first). VERIFIED by LEAD.
- 01:51 SLOT (wrapper): B-163 slot 2, Saturn floes / rig set / props / palette (f3d5d294; 387 MB). VERIFIED.
- 01:39:43-01:43:59 SLOT (wrapper): B-163 slot 1, Saturn deck1-3 / deep / hexagon straight (011b7de4; 803 MB). VERIFIED.
- 01:3x files: credits (Limelight / Patrick Hand lettering, D-090), renders_2026-11-08.md, the Jupiter design table (b3f24409).
- 01:13:0x-01:14:09 SLOT (wrapper): B-170 the five title cards (37c0a43f; 945 MB). VERIFIED.
- 01:02:41-01:03:37 SLOT (wrapper): B-160 the Vortex Whale at D-153 (92830c7f; 623 MB). VERIFIED.

## Ready for review
- B-171: the four exports (dd3a2bdd) + review_b171_{vapor_cone,shock_ring,speed_lines,puff_boost}.png (stamped 02:31); the set review review_b171_flight_fx.png (--art) follows after UNITY's check. The boost review's "beside ships/pilgrim/puff" panel errors (review.py's beside placement assumes a ground pivot; the puff hangs from the top); the set review shows cruise beside boost.
- B-166 slot 1a: deck1 x4 (77e72d0c) + review_b158_uranus_deck1_{sun_left,sun_right,night,survey}.png; URANUS-CHECK deck1 PASS in the log 02:25.

## Handoffs (unrouted only)
- -> UNITY (U-150), B-171 placement: vapor_cone and shock_ring pivots = the ship's centre of mass (ship-local 0, 6.2 m, the tilt pivot); the cone draws IN FRONT of the hull, the ring BEHIND it. speed_lines: 128x360 tiles, 3 per 1080 px edge (tile i may show frame (f + i) % 4), drawn for the LEFT edge, flip x for the right; pivot (0, 0.5) = the edge. puff_boost: a drop-in for ships/pilgrim/puff (socket tail_exhaust, pivot 0.5 / 0.96, clip 'puff'), now 192x288 frames: no 1.6x y-scale needed.

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
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs, not even a capped dry run (LEAD 18:1x; D-037: my idle time is what frees the memory); lock-free work is then files only (rows, sources, reports).

## For USER_ACTIONS
none (USER-28, closing ChatGPT + Edge for RAM, is LEAD's).

## HeavyJobLock
none held (released 02:31:5x after B-171); no want (UNITY took the lock after my job: D-039, re-filed only once it releases or per the queue). No background waiters.
