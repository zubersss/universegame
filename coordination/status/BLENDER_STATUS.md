# BLENDER STATUS
Updated: 2026-11-09 12:2x · Session: 11 (resumed ~11:45 after a restart; context rebuilt from the repo; LEAD = zuber-67, UNITY = zuber-15, me = zuber-61) · trimmed under D-113 at 14:0x; older: coordination/status/archive/BLENDER_2026-11-08.md, BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
**12:2x: every source in my queue is committed; all renders wait for the gate.** UNITY's want (U-193 slice 2) is on file and goes first (RAM 0.51 GB at 12:17; USER-37 asks the owner to close the ChatGPT app). Files only until UNITY has run. Then, in my lock (LEAD's order 12:1x):
1. B-227 rev 2 sheet (light; all five tool icons) → LEAD → export the four on ACCEPTED (0.6.1 if before U-194's build). Beam + survey ACCEPTED 12:0x; the builder redrawn (a plank bucket tipped to pour onto a ghost block on a ground line: no plus, no brackets, D-087), the grapple inked heavier (rev 2 source b506e10d).
2. B-220's five sheets (jupiter, saturn, uranus, neptune, venus; LEAD's 1.5 GB gate, <= 15 min, yield if want_unity appears) → LEAD with the per-layer list (continues / fades) for U-191 → export on ACCEPTED. The sparse-layer rule is LEAD-ruled (11:5x): continue_rows 64 only where the bottom band is >= 25 % solid; a sparse layer fades out over its last 64 rows with no continue_rows; Neptune deck2's flash lifted (4604620b). The first sheets (11:27-11:40) showed why: wisps / rain / lightning as dashes, the CRUSH band ghosted into stripes, Neptune's storm ring as slats.
3. B-224 preview (veil serpent sources f95c5461).
4. B-223 preview (sources 2f4a47f6: build_bay_v3.py - the bay in v3 under DockingBay's existing keys backgrounds/waystation/layer0..2 at 1920x1080, no code change; + icons/catalogue/camp).
5. B-225 preview (sources 6f107fa2: sea_under's bolder shafts, a 2 m rippled light ceiling, + layer4 shallow_seabed for the shore's first 40 m; the review at 1 / 3 / 10 / 40 m beside a 1:8 beach slope).
- **Rule (LEAD 09:2x, after two slips):** the first line of ANY call that starts python lists coordination/locks (abort on another role's heavy_ / want_) and reads RAM.
- **Rule from LEAD 18:2x (D-087):** the Beam reads as a mining tool, never a gun. No pistol grip or trigger, nothing hanging under the body: a cable-fed, arm-mounted emitter with a cutting nozzle.
- Waiting on others: B-207 closes on PawsOnTheGround green; B-204 on UNITY's capture; B-172 on U-151. UNITY drops the three lance .meta files.

## Last completed
- 11-09 11:2x: B-222 exported (02462247, LEAD-accepted): icons/thruster_mk2/base, a steel bell with a brass collar; the other 49 item icons byte-identical. For 0.6.1.
- 11-09 11:2x: B-226 exported (ab1c524f, LEAD-accepted after the icon fix): props/rig/shovel 192x64 (pivot at the D-grip; json grip / blade_tip / muzzle), fx/shovel_flick/base (6 x 128, clip flick), icons/tools/shovel 128. For U-193 / 0.6.1.
- 11-09 11:10: B-221 exported (ea3f75fb, LEAD-accepted 10:5x): ui/title/background, the v3 title scene (Earth's camp at dusk), 1920x1080 + json. For 0.6.1.
- 11-09 06:0x-09:1x: B-201 (0.6.0 smoke read, all 75 shots; coordination/reports/blender/smoke_read_0.6.0.md, 517ae849 + 1008f40c): 17 defects routed by LEAD; mine fixed: terrain/earth/fill_decor_t2_1 (root_knot -> a pale root tangle) + fill_decor_t3_3 (mica_book -> a pale layered slab), b47759a4.
- 11-09 00:4x: props/dig/winch_post json stands_on = the drawn surface at the shaft's mouth (379b0b89; UNITY's U-176 question; json only).
- 11-09 00:35: B-219 (655fead8, LEAD-accepted after three fixes): the giants' floe nodes - props/jupiter/node_{ammonia_ice,metallic_hydrogen}, props/saturn/node_{ring_ice,ring_rock,helium3}, props/uranus/node_{methane_ice,superionic_ice}, props/neptune/node_{methane_ice,superionic_ice,deep_diamond}; B-176 format, json deck + item; for U-189.
- 11-08 12:10-22:5x: B-184 to B-217, the strip retirements, U-183's hand_socket (archived: coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md).

## Ready for review
- B-191 / B-192: review_b191_{mercury,venus}_puffs.png, review_b192_{earth,mars}_fill_decor.png (591164e9).
- B-189 / B-185: review_b141_mars_{canyon,storm,plains}(_dip).png (9e04de12), review_b152_venus_surface(_dip).png (baa7f1e0), review_b149_mercury_{day,twilight,night}_dip.png (d7fbeace).

## Handoffs (unrouted only)
- -> UNITY (B-203 / B-204 / B-207, sent to LEAD 17:2x): ground_fill_t<n> json tier / depth_m / transition_m 1.0; surface_line row 40 = pivot, 2 m down the surface normal; ui/skilltree chart json ring_r_px / branch_axis_deg / slots_deg, emblem_r_px 408; node icons at 40 px, 0.4 alpha when locked; links tiled under the frames; vent_eel contact 0 px.
- -> UNITY (B-191): terrain/mercury/dig_puff_ice, terrain/venus/dig_puff_{tessera,vent}: drop-ins for dig_puff where the dig is in that variant's band, as B-190's (8 frames 128x128, pivot (0.5, 0.25), clip 'puff'; json "variant").
- -> UNITY (U-167, B-192): terrain/earth/fill_decor_sand_1..3 and terrain/mars/fill_decor_basalt_1..3: scatter in the ground_fill_sand / ground_fill_basalt cutaway by a position seed, as D-165's fill_decor (upright, never rotated, pivot centred; json "fill" names the fill).
- -> UNITY (U-164 / U-159): a layer2 json entry's "continue_rows": 64 = its bottom 64 rows tile vertically. Two depths: the B-133 / B-114 / B-185 sets 480 tall at y_m -2.0; the B-179 / B-186 / B-187 sets 544 tall at y_m -3.0 with "ground_row": 352. The Mars storm's layer2 is a translucent veil (864, y_m -2.0), no ground.
- -> UNITY (U-159): variant keys ground_band_{frost,basalt,talus} (Mars), ground_band_ice (Mercury), ground_band_{tessera,vent} (Venus); ground_fill_basalt (json "fill"); band json "biomes" names the code region; lips terrain/earth/ground_lip_{sand,stone,snow}, terrain/mars/ground_lip_frost.
- -> UNITY (U-150), B-171 placement: vapor_cone and shock_ring pivots = the ship's centre of mass (ship-local 0, 6.2 m); the cone IN FRONT of the hull, the ring BEHIND. speed_lines: 128x360 tiles, 3 per 1080 px edge, drawn for the LEFT edge (flip x for the right), pivot (0, 0.5). puff_boost: a drop-in for ships/pilgrim/puff (tail_exhaust, pivot 0.5 / 0.96, clip 'puff'), 192x288 frames.

## Blockers
none. Waiting on: U-151 (B-172's export), U-152 (B-174).

## Proposals (undecided only)
- P (12:2x, from B-223's read of CataloguePanel.IconOf): every catalogue Site entry has no icon, not only Camp. IconOf returns null for EntryKind.Site, so U-192 needs a Site branch for any site icon. Proposal: key sites as icons/catalogue/<label lowercased, spaces as _> (camp, survey_archive, launch_complex, halcyon_hauler, warden_outpost, flare_shelter, warden_vault, mercury_beacon, solarite_field, meridian_station, vent_harvester), and a BLENDER card for the other ten in the camp icon's style once LEAD wants them.

## Rules I keep (from slips)
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs: no capped dry run, no python / sed text patch, no json check. Edit files with the edit tools only (13:1x and 13:5x slips: two one-off python patches beside UNITY's lock; 16:4x: one `sed -i` swapping two characters in my own script; 18:2x: one `sed -i` on this status line; 11-09 00:3x: one python palette lookup (died at import, no numpy) run without first listing the locks while UNITY compiled. The shell is never the editor while a lock is out, and no interpreter runs before the locks folder is read.)
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
none held (last: the B-220 sheets 11:2x-11:40); no want on file: UNITY's want (U-193 slice 2, 11:43) goes first and mine is filed only once heavy_unity.lock appears (D-039). No background waiters: I poll in the foreground.
