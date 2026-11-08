# BLENDER STATUS
Updated: 2026-11-08 14:0x · Session: 10 (all three windows restarted ~09:30 after a ~3-hour break; context rebuilt from the repo) · trimmed under D-113 at 14:0x; older: coordination/status/archive/BLENDER_2026-11-08.md, BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
IDLE (14:0x). Every card on my list is exported; B-172 / B-174 wait on UNITY's U-151 / U-152. Credits upkeep done (57432a73). Ready for LEAD's next cards.

## Last completed
- 14:06: B-191 + B-192 exported (591164e9): terrain/mercury/dig_puff_ice, terrain/venus/dig_puff_tessera / _vent; terrain/earth/fill_decor_sand_1..3 (scallop, fulgurite, desert rose), terrain/mars/fill_decor_basalt_1..3 (lava tube, vesicles, amygdale).
- 13:46-13:48: B-187 exported (3f486025): backgrounds/mercury/coldtrap, backgrounds/venus/tessera (D-169, 544 / y_m -3.0, ground_row 352, continue_rows 64).
- 13:31: B-190 exported (d6eb5fb4): terrain/earth/dig_puff_{sand,snow,stone}, terrain/mars/dig_puff_{frost,basalt}. B-182 audits: Earth 44 / Mars 37 / Mercury 25 / Venus 29 G1 keys, none missing, no outliers.
- 12:10-13:16: B-188, B-185 (Mars / Mercury / Venus), B-186, B-189, B-184 exported (archived lines).

## Ready for review
- B-191 / B-192: review_b191_{mercury,venus}_puffs.png, review_b192_{earth,mars}_fill_decor.png (591164e9).
- B-189 / B-185: review_b141_mars_{canyon,storm,plains}(_dip).png (9e04de12), review_b152_venus_surface(_dip).png (baa7f1e0), review_b149_mercury_{day,twilight,night}_dip.png (d7fbeace).

## Handoffs (unrouted only)
- -> UNITY (B-191): terrain/mercury/dig_puff_ice, terrain/venus/dig_puff_{tessera,vent}: drop-ins for dig_puff where the dig is in that variant's band, as B-190's (8 frames 128x128, pivot (0.5, 0.25), clip 'puff'; json "variant").
- -> UNITY (U-167, B-192): terrain/earth/fill_decor_sand_1..3 and terrain/mars/fill_decor_basalt_1..3: scatter in the ground_fill_sand / ground_fill_basalt cutaway by a position seed, as D-165's fill_decor (upright, never rotated, pivot centred; json "fill" names the fill).
- -> UNITY (U-164 / U-159): a layer2 json entry's "continue_rows": 64 = its bottom 64 rows tile vertically. Two depths: the B-133 / B-114 / B-185 sets 480 tall at y_m -2.0; the B-179 / B-186 / B-187 sets 544 tall at y_m -3.0 with "ground_row": 352. The Mars storm's layer2 is a translucent veil (864, y_m -2.0), no ground.
- -> UNITY (U-159): variant keys ground_band_{frost,basalt,talus} (Mars), ground_band_ice (Mercury), ground_band_{tessera,vent} (Venus); ground_fill_basalt (json "fill"); band json "biomes" names the code region; lips terrain/earth/ground_lip_{sand,stone,snow}, terrain/mars/ground_lip_frost.
- -> UNITY (U-150), B-171 placement: vapor_cone and shock_ring pivots = the ship's centre of mass (ship-local 0, 6.2 m); the cone IN FRONT of the hull, the ring BEHIND. speed_lines: 128x360 tiles, 3 per 1080 px edge, drawn for the LEFT edge (flip x for the right), pivot (0, 0.5). puff_boost: a drop-in for ships/pilgrim/puff (tail_exhaust, pivot 0.5 / 0.96, clip 'puff'), 192x288 frames.

## Blockers
none. Waiting on: U-151 (B-172's export), U-152 (B-174).

## Proposals (undecided only)
none.

## Rules I keep (from slips)
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs: no capped dry run, no python / sed text patch, no json check. Edit files with the edit tools only (13:1x and 13:5x slips: two one-off python patches beside UNITY's lock).
- Before sending a sheet, look at every new shape at 2x for faces: dark marks on a ball (puff frame 2), pale points under a dark arch (teeth), a dark oval on a white ball (a hole).
- preview_dip and any scene lookup: take the planet from the key (PLANET_OF is keyed by scene name). Hold heavy_blender.lock by hand around a light run (the wrapper also refuses beside another role's lock or want).
- No 2>&1 on the render wrapper in PowerShell 5.1 (a numpy warning becomes a terminating error).
- A lock check and a RAM read are each their own call; Blender starts only in a later call after a clear result (D-073). Light work lock-free <= ~300 MB (D-109); under 0.3 GB free, code only.
- A want is filed only when I am next after the running job; withdraw it while the other role's multi-lock job is between locks. While a want is on file, poll the locks each turn; never end a turn waiting for a ping. No background waiters.
- Measure every new export path's frames against the 2 px edge and the ground line before the export.
- All three sessions share one working tree: a push can race another role's; fetch + merge (never rebase) and push again. Commit by explicit file paths (never an Art directory), check git show --stat against the list.
- A stroke's line is drawn in its material's ink_hex: a coloured line needs its own line material; a fill-only material on an open stroke draws nothing.

## For USER_ACTIONS
none.

## HeavyJobLock
none held (released 14:06 after the B-191 + B-192 export); no want on file. No background waiters.
