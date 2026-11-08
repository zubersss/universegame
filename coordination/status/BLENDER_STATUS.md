# BLENDER STATUS
Updated: 2026-11-08 09:5x · Session: 10 (all three windows restarted ~09:30 after a ~3-hour break; context rebuilt from the repo) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-08.md, BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
B-181: the variant list below is posted for LEAD's ruling. While it waits: B-180's lips (sand / stone / snow / frost) in source + the curve preview, lock-free. Then B-182 Earth's audit sheet in a free gap with no want on file. UNITY's batched check (queue rank 1) outranks every BLENDER job; bpy only under my own lock.

## B-181 variant list (Mars / Mercury / Venus per-biome ground; for LEAD, then U-159)
Keyed by the regions the code already has (MarsLandforms / StageRegions, MercuryLandforms.InColdTrap, VenusLandforms.At), so U-159 needs no new region. A variant only where the ground reads clearly different at 1x.
- Mars plains (mars_plains) -> ground_band + ground_fill (B-175, in). No new key.
- Mars polar cap (mars_polar) -> ground_band_frost + ground_fill (B-178, in, 2090cb3c). No new key.
- Mars Olympus / Tharsis (mars_tharsis) -> NEW ground_band_basalt (dark grey-brown lava crust: ropy pahoehoe folds, vesicles, rust dust in the hollows) + NEW ground_fill_basalt (stacked lava-flow sheets with vesicle rows and rubbly flow tops instead of the Gale sandstone) + ground_decor_basalt_1..3 (a vesicular boulder, a spatter cone stub, a lava-tube skylight rim stone).
- Mars Valles Marineris floor (mars_canyon) -> NEW ground_band_talus (a scree crust of angular ochre / rust wall debris over light-toned layered sediment) + ground_fill (B-175's layered sandstone fill already reads as canyon strata) + ground_decor_talus_1..3 (a fallen wall block with strata, a scree fan, a dust-buried slab).
- Mars dune seas: the code has no dune span (MarsFeature: Plains / Canyon / Olympus / PolarCap), so none drawn. If U-159 adds one: ground_band_dune (dark basaltic sand ripples) + decor.
- Mercury day / twilight / night -> ground_band + ground_fill (B-175, in): one set, because the terminator moves the light, not the ground (the zones change with the clock, so a band per zone would slide under the player).
- Mercury polar cold traps (InColdTrap) -> NEW ground_band_ice (a pale blue-white water-ice skin, frost sparkle, over the dark crater-floor regolith) + ground_fill (B-175) + ground_decor_ice_1..3 (an ice-glazed rock, an ice ridge, frost-rimmed pebbles).
- Venus plains (VenusFeature.Plains) -> ground_band + ground_fill (B-175, in: the glassy black crust over the folded basalt fill).
- Venus tesserae (Tessera) -> NEW ground_band_tessera (crumpled ridge-and-groove crust, lighter grey-brown than the plains' black glass) + ground_fill (B-175's folded basalt fits tessera) + ground_decor_tessera_1..3 (a tilted ridge slab, a grooved block, a scree of folded chips).
- Venus vent fields (VentField) -> NEW ground_band_vent (a cracked sulfur crust, yellow over black, ember-glow seams, green vitriol-glass shards) + ground_fill (B-175's fill has sulfur veins and an ember seam) + ground_decor_vent_1..3 (a small fumarole cone, sulfur rosettes, a vitriol-glass cluster).
New keys: 5 bands, 1 fill, 15 decor. Each band json's "biomes" names the code region (e.g. ["mars_tharsis"]) and its "fill". Lips for the new variants would be a follow-up to B-180, not in this card. Mars first: its preview after LEAD rules on this list.

## Last completed
- 09:4x: B-178 Mars frost: ground_decor_frost_2 redrawn as rounded, chipped ice lumps (source f0b6e35b); export 2090cb3c (log OK 09:42:15, 4 keys, peak 346 MB, join 0.00/255, palette 100 %). VERIFIED by LEAD. The first wrapper run (09:41) wrote the files, then stopped in the review step on a numpy NaN warning: the Mars preview padded with np.empty * 0. Fixed with np.full and re-ran clean.
- 09:3x: B-179 tundra: layer1's lee shading redrawn as soft, curved, feathered crescents on each hill's unlit (left-facing) slope (build_backdrop_v3.tundra_lee; the rng order kept); export d060f226 (log OK 09:36:52, 42.7 s, peak 850 MB, seams 0.87 / 0.65 / 0.37). VERIFIED by LEAD. All three B-179 sets are in for 0.5.0.

## Ready for review
none (B-179 and B-178 Mars frost verified 09:4x-09:5x).

## Handoffs (unrouted only)
- -> UNITY (U-159): terrain/mars/ground_band_frost is in (2090cb3c): pivot on surface row 24, json "fill": "ground_fill", "biomes": ["polar cap", "polar layered terrain"] (the region in code is mars_polar). backgrounds/earth/tundra is in (d060f226) for U-161.
- -> UNITY (U-150), B-171 placement: vapor_cone and shock_ring pivots = the ship's centre of mass (ship-local 0, 6.2 m, the tilt pivot); the cone draws IN FRONT of the hull, the ring BEHIND it. speed_lines: 128x360 tiles, 3 per 1080 px edge (tile i may show frame (f + i) % 4), drawn for the LEFT edge, flip x for the right; pivot (0, 0.5) = the edge. puff_boost: a drop-in for ships/pilgrim/puff (socket tail_exhaust, pivot 0.5 / 0.96, clip 'puff'), now 192x288 frames: no 1.6x y-scale needed.

## Blockers
none. Waiting on: U-151 (B-172's export), U-152 (B-174).

## Proposals (undecided only)
- B-181's variant list above.

## Rules I keep (from slips)
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
none held (released 09:42:15 after the Mars frost export); no want. No background waiters.
