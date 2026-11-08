# BLENDER STATUS
Updated: 2026-11-08 13:5x · Session: 10 (all three windows restarted ~09:30 after a ~3-hour break; context rebuilt from the repo) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-08.md, BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
B-191 + B-192 sheets with LEAD (13:5x): review_b191_dig_puffs_preview.png (Mercury ice, Venus tessera / vent puffs), review_b192_fill_decor_preview.png (fill_decor_sand_1..3: scallop, fulgurite, desert rose; fill_decor_basalt_1..3: lava tube, vesicles, amygdale); sources 9d52518a + b944b573 (own-review fixes: tessera shade, rose, lava tube - no teeth). On LEAD's OK all four rows export in one slot. Files only while UNITY holds or wants the lock.

## B-189 (DONE in Art): every inner set using terrace() / notch() or showing right-angle steps (sources 4876c415)
- mars/canyon + storm (layers 0-1 shared): rim, spur and three tiers -> _eroded / _soft_ledges (ledges, rounded corners). Exported 9e04de12.
- mars/plains: far mesas from trapezoids with flat block caps to eroded buttes (mesa2). Exported 9e04de12.
- venus/surface: layer1's tesserae ridge -> _soft_ledges. Exported with its B-185 baa7f1e0.
- mercury/coldtrap (B-187): rim and walls redrawn before its first preview.
- clean at 1x: mercury/day, twilight, night; venus/deck (viewed review_b152_venus_deck.png: towering clouds, an airship); venus/tessera; mars/polar, tharsis.

## Last completed
- 13:46-13:48: B-187 exported (3f486025): backgrounds/mercury/coldtrap, backgrounds/venus/tessera (D-169, 544 / y_m -3.0, ground_row 352, continue_rows 64); stamped dip reviews.
- 13:31: B-190 exported (d6eb5fb4): terrain/earth/dig_puffs (dig_puff_sand / _snow / _stone), terrain/mars/dig_puffs (dig_puff_frost / _basalt). B-182 audits Mars 37 / Mercury 25 / Venus 29 G1 keys, none missing, no outliers (after B-184).
- 13:16: B-184 exported (fe58e320): terrain/{mars,mercury,venus}/ground_set for the face-safe dig_puff; only the three dig_puff sheets changed.
- 13:12-13:13: B-182 Earth audit (44 G1 keys, none missing, no outliers; audit_g1_earth.png, reports/blender/audit_g1.md); B-190 preview (review_b190_dig_puffs_preview.png, sources 0c6deb8a), ACCEPTED.
- 13:08-13:09: B-185 + B-189 Venus surface exported (baa7f1e0). 13:00-13:04: B-189 Mars canyon / storm / plains exported (9e04de12).
- 12:47-12:51: B-185 Mercury exported (d7fbeace): day / twilight / night, layer2 480 at y_m -2.0, continue_rows 64, layer0 feathered.
- 12:43-12:45: B-186 exported (60132bdb): mars/polar + mars/tharsis. 12:37-12:41: B-185 Mars (4d86cbc3).
- 12:10-12:16: B-188 exported for Build 0.5.0 (e2ddb4cb); B-179 / B-183 / B-188 DONE (LEAD cycle 283).

## Ready for review
- B-184: review_b175_{mars,mercury,venus}_ground.png (fe58e320).
- B-189 / B-185: review_b141_mars_{canyon,storm,plains}(_dip).png (9e04de12), review_b152_venus_surface(_dip).png (baa7f1e0), review_b149_mercury_{day,twilight,night}_dip.png (d7fbeace).

## Handoffs (unrouted only)
- -> UNITY (B-190): terrain/<planet>/dig_puff_<variant> (earth: sand, snow, stone; mars: frost, basalt): drop-ins for dig_puff where the dig is in that variant's band - 8 frames 128x128, pivot (0.5, 0.25), clip 'puff'; json "variant" names the band.
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
