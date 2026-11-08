# BLENDER STATUS
Updated: 2026-11-08 11:0x · Session: 10 (all three windows restarted ~09:30 after a ~3-hour break; context rebuilt from the repo) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-08.md, BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
Waiting for U-163's build (it outranks everything, LEAD 10:5x); files only while UNITY holds the lock. Sources in for B-186 (bc8145f9: mars/polar, mars/tharsis), B-185 (60994988: D-169 on Mars plains / canyon / storm, Mercury day / twilight / night, Venus surface; the storm's dust overlay now over hazed canyon scree) and B-187 (7be57df1: mercury/coldtrap, venus/tessera). A painted-set preview peaks ~320 MB (polar killed at the 300 MB cap 11:03), so the previews need my own lock. After U-163, in order: B-186 previews -> LEAD -> exports; B-185 one planet per slot, Mars first; B-182 Earth audit (audit_g1.py, 01638ac1); B-184 puffs (Mars / Mercury / Venus); B-187 previews. B-178 / B-179 / B-180 / B-181 / B-183 + D-169 all exported (below).

## Last completed
- 10:38-10:52: D-169 / B-183: forest (7fc7eb06; the stump and log on scrub banks), coast (69aac68c; the driftwood gone) and plains (83401c03): layer2 2048x480 at y_m -2.0 (solid painted ground to 2 m under the line), the last 64 rows vertically tileable (gen_painted_bg.tile_bottom), "continue_rows": 64 in each layer2 json entry; layer0 / layer1 byte-identical. Stamped dip reviews review_b133_earth_forest_dip.png, review_b133_earth_coast_dip.png, review_b114_earth_plains_dip.png (1.5 m and 3 m valleys + a rise: no teal). Forest + coast VERIFIED. Two slips, both fixed: the first forest run failed in its new dip review (the 3 m frame overran); the plains dip review first showed MARS's plains (planet looked up by scene name).
- 10:52: B-182 Earth dig_puff re-exported for 0.5.0 (2c1d7a9a; source c8cf185b): the clods behind the billows, frames 1-2 no longer a face. Mars / Mercury / Venus puffs ride U-159.
- 10:1x-10:34: B-181 all four planets exported and VERIFIED: Mars 6b097cb4 (the talus block redrawn as a laminated wall piece), Mercury + Venus c2a2e298 (Venus with the hot embers and the warm-grey ridged tessera).
- 10:08-10:10: B-180 lips exported and VERIFIED (d9a1eb38, 6220a954). SLIP: the Earth run took the wrapper's light path into UNITY's 10:08:03 lock; the wrapper now refuses light jobs beside another role's lock or want.
- 09:3x-09:4x: B-179 tundra (d060f226) and B-178 Mars frost (2090cb3c) exported and VERIFIED.

## Ready for review
- D-169 plains: backgrounds/earth/plains (83401c03), review_b114_earth_plains_dip.png (rebuilt 10:52 from the export).
- B-182 Earth puff: terrain/earth/dig_puff (2c1d7a9a), review_b175_earth_ground.png.

## Handoffs (unrouted only)
- -> UNITY (U-164, D-169): backgrounds/earth/{forest,coast,plains}/<scene>.json: layer2 "y_m": -2.0, "height_px": 480, "continue_rows": 64 = its bottom 64 rows tile vertically (row 0 follows the painting above; repeat the strip under the layer's bottom edge, never a stretched row). B-179's desert / taiga / tundra keep their ground_row fields (no continue_rows).
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
none held (released 10:52:10 after the Earth puff re-export); no want. No background waiters.
