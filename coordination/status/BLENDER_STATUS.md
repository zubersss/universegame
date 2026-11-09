# BLENDER STATUS
Updated: 2026-11-08 20:4x · Session: 10 (all three windows restarted ~09:30 after a ~3-hour break; context rebuilt from the repo) · trimmed under D-113 at 14:0x; older: coordination/status/archive/BLENDER_2026-11-08.md, BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
B-219 (the giants' floe nodes): sources written files-only (build_nodes_v3 giant rows + manifest rows props/<giant>/nodes); the four previews render in my own lock once UNITY's lock and want clear and RAM is at the gate. Then B-201 on 0.6.0's smoke. Then B-201, the D1 build's smoke (an art read, frame by frame), when that build lands.
- **Rule from LEAD 18:2x (D-087):** the Beam reads as a mining tool, never a gun. No pistol grip or trigger, nothing hanging under the body: a cable-fed, arm-mounted emitter with a cutting nozzle.
- Waiting on others: B-207 closes on PawsOnTheGround green; B-204 on UNITY's capture; B-172 on U-151. UNITY drops the three lance .meta files.

## Last completed
- 22:5x: U-183 request (UNITY): props/rig/hand_socket.json (9934340b) - the front glove's grip per frame of side (98) and side_b (72), [x, z, forearm angle], null in front views / hidden; held_b flags side_b frames already holding a pick / hammer / Beam / reel. Json only; regenerated with props/rig/tools_v3.
- 22:47: Mars's old strips retired (9f035696, under my lock; U-186 9694c4c8): terrain/mars/ground_strip_basalt / _frost (2 png + 2 json, 0 .meta); the frost row dropped; build_c2_mars_ground RETIRED = basalt; the regolith strip kept.
- 22:1x: Earth's old strips retired (e5f972c5; U-186 1c58f11b): terrain/earth/ground_strip_soil / _stone / _sand (3 png + 3 json, 0 .meta); build_c2_ground_strip RETIRED (Earth's export skips them; the grass row stays).
- 22:0x: B-217 (320d45fa, LEAD-accepted as drawn): props/rig/survey + builder in v3 (json muzzle at RigModule's constants + cable_socket), fx/survey_scan/base + fx/builder_ghost/base; six v2 maps deleted (UNITY drops the .meta files).
- 21:4x: B-216 (59f3255e, LEAD-accepted as drawn): fx/dig_sparks/base + fx/dust/base in v3 ink under the v2 keys / clips (ppu 128); dig_sparks' v2 emission map deleted (UNITY drops the .meta).
- 21:35: B-215 the D1 key audit (b19effe0): coordination/reports/blender/d1_key_audit.md. 321 requested keys, 0 missing (29 decor probe slots empty by design); 8 v2 assets in the D1 loop (dig_sparks, dust, beam_ray/base, survey + builder tools without json, survey_scan, builder_ghost); 133 present keys unrequested (58 D1 deliveries awaiting wiring, 75 older ground pieces). Re-run: blender/scripts/audit_d1_keys.py.
- 20:5x: docs/credits/blender.md: the baked Limelight lettering rows + the B-193 to B-214 upkeep check (84a0c2e3).
- 20:5x: B-214 (2ccf8993, LEAD-accepted as drawn): fx/ui/{scrip_shower (8), node_bought (8, ring r 35), rank_up (10, insignia_track), expedition_seal (10, ends on the certificate's seal; seal 58,58 in from bottom-right)}.
- 20:4x: B-213 (36b60e46, LEAD-accepted as drawn): ui/hints/{dig_down, surface_line, sell, skill_tree, climb_up, pack_full} (320x200, 9-slice [152,52,44,144], title / body / keycap rects, binding) + ui/hints/arrow (pivot at the tip). For U-185.
- 20:0x-20:3x, all LEAD-accepted, reviews stamped:
  - B-210 (005782bc): characters/surveyor/side_b → 72 frames (+ climb_ladder 8, planted on rungs 0.25 m apart, root +0.5 m/cycle; reel_up 8); sockets hatch / reel / ladder on every frame. props/dig/{ladder, ladder_top, ladder_bottom, grapple_line, grapple_hook, winch_post, recall_beacon}. jetpack_mk2/mk3 json + back_socket_b.
  - B-211 (a3ee53f2): ui/hud/{gauge_pack (B-121's colours, LEAD's ruling; C4 palette audit in the Backlog), scrip_tag, rank_slot, pack_full, depth_marker}. Mock-up layout not binding (UNITY lays out).
  - B-212 (a3ee53f2): fx/rare/sparkle_t2..t5 (clip burst), fx/rare/pocket_pop (clip pop).
- 19:4x-19:5x:
  - B-209: ui/map/* (21 keys, b24977b9; for U-184).
  - props/rig/lance removed (4697c870: 3 PNGs + the manifest row, 0 .meta).
  - B-202: backgrounds/earth/sea_under (dc65eb88, for U-171). The 40 m edge was the far floor's flat top: now hillier, with a soft top.
- 18:2x-19:25, all LEAD-accepted, reviews stamped:
  - B-204 complete: node icons batches 3-5 (e09be9a4, 8d8fed62, acbc7ffd; all 66 in icons/nodes/) + emblem_dig cable-fed.
  - B-206: ui/rank/* (13 keys, d9f66b10).
  - B-205: props/rig/beam_mk1..5 + beam, grapple_mk1..3 + grapple, jetpack_mk2 / mk3 + back_socket, fx/beam_ray/mk1..5 (e5da8d0e).
- 12:10-18:0x: B-184 to B-208 (archived at 20:5x: coordination/status/archive/BLENDER_2026-11-08.md).

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
none.

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
none held (last: B-214's export 20:5x); no want on file. No background waiters: I poll in the foreground.
