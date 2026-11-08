# BLENDER STATUS
Updated: 2026-11-08 12:4x · Session: 10 (all three windows restarted ~09:30 after a ~3-hour break; context rebuilt from the repo) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-08.md, BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
B-185 exports, one planet per slot: Mercury (day / twilight / night) next, then Venus surface; then B-182's Earth audit (audit_g1.py), B-184's puffs (Mars / Mercury / Venus ground_set re-exports, only dig_puff changing), B-187's previews (mercury/coldtrap, venus/tessera: sources in, now 544 / y_m -3.0 too). Files only while UNITY holds the lock; my want beside its lock, withdrawn between the parts of a multi-lock job.

## Last completed
- 12:43-12:45: B-186 exported (60132bdb): mars/polar (rev 2, accepted) + mars/tharsis (rev 3: two unequal rises, varied flow bands, tongue fronts); stamped dip reviews incl. the camera-5-m frame.
- 12:37-12:41: B-185 Mars exported (4d86cbc3): plains / canyon layer2 480 (y_m -2.0, continue_rows 64), the storm a translucent veil 864 (no ground, LEAD 11:0x), layer0 tops feathered, layer1 byte-identical.
- 12:10-12:16: B-188 exported for Build 0.5.0 (e2ddb4cb; DONE in the game): every Earth layer0's top feathered; desert / taiga / tundra layer2 544 at y_m -3.0, plain ground below row 416, continue_rows 64. The forest valley's sky line is not art (UNITY's U-166).
- 10:38-10:52: D-169 / B-183 forest / coast / plains (7fc7eb06, 69aac68c, 83401c03) and the Earth puff (2c1d7a9a), all verified.
- 09:3x-10:34: B-179 tundra, B-178 Mars frost, B-180 lips, B-181 (all four planets): exported and verified.

## Ready for review
- B-186: review_b186_mars_{polar,tharsis}.png + _dip.png (60132bdb).
- B-185 Mars: review_b141_mars_{plains,canyon,storm}_dip.png (4d86cbc3).

## Handoffs (unrouted only)
- -> UNITY (U-164 / U-159): a layer2 json entry's "continue_rows": 64 = its bottom 64 rows tile vertically (repeat them under the layer's edge). Two depths: the B-133 / B-114 / B-185 sets 480 tall at y_m -2.0 (their line above the walking surface); the B-179 / B-186 / B-187 sets 544 tall at y_m -3.0 with "ground_row": 352 (the line on the walking surface). The Mars storm's layer2 is a translucent veil (864, y_m -2.0, continue_rows 64), no ground. New Mars sets: backgrounds/mars/polar (MarsFeature.PolarCap), backgrounds/mars/tharsis (Olympus).
- -> UNITY (U-159): Mars / Mercury / Venus variant keys: ground_band_{frost,basalt,talus} (Mars), ground_band_ice (Mercury), ground_band_{tessera,vent} (Venus); ground_fill_basalt for basalt (json "fill"); each band json's "biomes" names the code region (mars_tharsis, mars_canyon, mercury_cold_trap, venus_tessera, venus_vent_field); lips: terrain/earth/ground_lip_{sand,stone,snow}, terrain/mars/ground_lip_frost ("band" names the band).
- -> UNITY (U-150), B-171 placement: vapor_cone and shock_ring pivots = the ship's centre of mass (ship-local 0, 6.2 m, the tilt pivot); the cone draws IN FRONT of the hull, the ring BEHIND it. speed_lines: 128x360 tiles, 3 per 1080 px edge (tile i may show frame (f + i) % 4), drawn for the LEFT edge, flip x for the right; pivot (0, 0.5) = the edge. puff_boost: a drop-in for ships/pilgrim/puff (socket tail_exhaust, pivot 0.5 / 0.96, clip 'puff'), now 192x288 frames: no 1.6x y-scale needed.

## Blockers
none. Waiting on: U-151 (B-172's export), U-152 (B-174).

## Proposals (undecided only)
none (B-181's list accepted 09:4x).

## Rules I keep (from slips)
- preview_dip and any scene lookup: take the planet from the key (PLANET_OF is keyed by scene name: "plains" is Mars). The wrapper's light path takes no lock: hold heavy_blender.lock by hand around a light export (10:08 overlap; the wrapper now also refuses beside another role's lock or want).
- No 2>&1 on the render wrapper in PowerShell 5.1: a numpy warning on Blender's stderr becomes a terminating error under the wrapper's ErrorActionPreference Stop (09:41).
- A review grows with its rows: beside another role's lock, re-measure or cut it to the measured size.
- While another role holds the lock, run only jobs already measured <= 150 MB; a new job is first measured in a free gap, never estimated from its parts.
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073). The same for RAM: read it in its own call, then decide.
- A want is filed only when the queue says I am next after the running job; never while the other role's multi-lock job is between locks.
- Light work while another role's heavy job runs: <= ~150 MB; lock-free otherwise <= ~300 MB (D-109); under 0.3 GB free, code only.
- Measure every new export path's frames against the 2 px edge and the ground line before the export.
- Short jobs run in the foreground; no background waiters: check the locks folder each turn.
- All three sessions share one working tree: a push can race another role's; fetch + merge (never rebase) and push again.
- A stroke's line is drawn in its material's ink_hex: a coloured line needs its own line material; a fill-only material on an open stroke draws nothing.
- While a want is on file, poll the locks each turn; never end a turn waiting for a ping.
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs, not even a capped dry run; lock-free work is then files only.
- Commit by explicit file paths (never an Art directory), check git show --stat against the list.

## For USER_ACTIONS
none.

## HeavyJobLock
none held (released 12:45 after the B-186 export); my want beside UNITY's lock for B-185 Mercury. No background waiters.
