# BLENDER STATUS
Updated: 2026-11-09 14:0x · Session: 12 (resumed 14:03 after the owner's restart; THIS SESSION = zuber-4d; LEAD = zuber-d1, UNITY = zuber-a0) · older: coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md, BLENDER_2026-11-07.md

## Current task
**14:3x — session 12 (LEAD = zuber-d1, UNITY = zuber-a0).** UNITY's U-194 chain holds the lock (PlayMode slices since 14:06) → files only, no want, no python; LEAD messages when the chain has released. Done files-only since 14:03 (all pushed): B-229 rev (the surveyor's hand on the D-grip, LEAD 14:1x; d593051c), B-233's source (build_site_icons_v3.py + manifest row icons/catalogue/sites; keys by label, RULED: meridian_beacon, solarite), B-232 rewritten to LEAD's 14:2x ruling (24 x 64 px, clips clod_1..4, one clod turning in place; 6970371f), the desk-check of all seven unrun sources by reading (B-230 / B-231 fixes in the commit after 6970371f; B-223 and B-225 read clean), and reports/blender/preview_notes_0.6.2.md (the run order, each sheet's command, what it must show, my 2x checks). Run order when the lock is mine: that report's table, top to bottom.
- B-231 crouch (to LEAD with the pose sheet): the 0.61 m helmet limits a drawable crouch to ~1.08 m over the 0.9 m crouch collider; proposal: a root squash of 0.92 in crouch or a 1.1 m crouch gap (U-199's "fits a 1 m gap").
**13:5x — RESUME HERE.** No lock and no want of mine; every source is committed. UNITY runs U-194 Build 0.6.1 (a multi-lock chain): NO want while it runs. When it has released (LEAD says so), in my lock (LEAD's order 13:5x), each item to LEAD before any export:
1. B-229 sheet (light; build_hints_v3.py preview, source daf89aad): ui/hints/dig_down's new picture (the shovel mid-scoop + flick) at 1x beside the SURFACE LINE card → export on ACCEPTED (0.6.2).
2. B-220 Neptune sheet (`python -I blender/scripts/gen_painted_bg.py --continue neptune blender/preview/review_b220_neptune_continue.png`, ~3 min), then Venus deck (`--continue venus`) in its own run; > 8 scenes = its own lock; <= 15 min per lock.
3. On ACCEPTED of both: export all five giants' bands + venus/deck together (tools/blender_render.ps1 on each planet's painted rows; the export logs "B-220 <key> layerN: continues | feathered"), then update coordination/reports/blender/b220_continue_rows.md for U-191 (Jupiter / Saturn / Uranus rows filled and ACCEPTED).
4. B-230 sheet (build_back_wall_v3.py, source 7b7f91b6; per planet: `python -I build_back_wall_v3.py <png> <planet>`; manifest kit row terrain/common/back_walls).
5. B-232 sheet (build_dig_debris_v3.py, source 88ab7c5b; kit row fx/dig_debris).
6. B-231 design sheet (build_surveyor_v5.py, source eb51b232; writes the bone JSON beside the review): PREVIEWS ONLY until the owner's look-over on the C5 page (D-185); interleave its source work whenever UNITY holds the lock.
Then the older previews: B-224 (veil serpent, f95c5461), B-223 (the bay + camp icon, 2f4a47f6), B-225 (the sea shallows, 6f107fa2).
B-228 (the 0.6.1 smoke read, read only, no lock) when U-194's smoke lands: prep in coordination/reports/blender/smoke_read_0.6.1.md.
7. After B-224 / B-223 / B-225's previews: B-233's sheet (`python -I blender/scripts/build_site_icons_v3.py blender/preview/review_b233_site_icons_preview.png`, light; only after B-223's camp icon is judged).
NOT YET RUN (expect first-run fixes): B-223, B-225, B-229, B-230, B-231, B-232, B-233. How I ran light sheets this session: list coordination/locks (abort on any other heavy_ / want_), read RAM in its own call, write heavy_blender.lock, run Blender's bundled `python.exe -I <script> <png>` with a working-set watchdog, delete the lock in `finally`.
- B-220 rule (LEAD-ruled 11:5x): continue_rows 64 only where a layer's bottom band is >= 25 % solid; a sparse layer fades out over its last 64 rows with no continue_rows. B-223's bay keeps DockingBay's keys backgrounds/waystation/layer0..2 at 1920x1080 (no code change). The owner's v5 direction (D-185): cards after 0.6.1; v4 keeps shipping.
- **Rule (LEAD 09:2x, after two slips):** the first line of ANY call that starts python lists coordination/locks (abort on another role's heavy_ / want_) and reads RAM.
- **Rule from LEAD 18:2x (D-087):** the Beam reads as a mining tool, never a gun. No pistol grip or trigger, nothing hanging under the body: a cable-fed, arm-mounted emitter with a cutting nozzle.
- Waiting on others: B-207 closes on PawsOnTheGround green; B-204 on UNITY's capture; B-172 on U-151. UNITY drops the three lance .meta files.

## Last completed
- 11-09 13:30: B-227 exported (3a46eb91, LEAD-accepted rev 2): icons/tools/{beam, grapple, survey, builder} 128 + json, 8 files, 0 .meta; for 0.6.1's HUD tool slot.
- 11-09 13:10-13:38: B-220 Jupiter, Saturn, Uranus sheets ACCEPTED (the sparse-layer rule; the U-191 list in reports/blender/b220_continue_rows.md); export after Neptune + Venus.
- 11-09 12:5x-13:5x (files only): B-228 prep, the D1 audit's new keys, credits upkeep (f8898839); sources B-229 / B-231 / B-230 / B-232 (daf89aad, eb51b232, 7b7f91b6, 88ab7c5b).
- 11-09 11:2x: B-222 exported (02462247, LEAD-accepted): icons/thruster_mk2/base, a steel bell with a brass collar; the other 49 item icons byte-identical. For 0.6.1.
- 11-09 11:2x: B-226 exported (ab1c524f, LEAD-accepted after the icon fix): props/rig/shovel 192x64 (pivot at the D-grip; json grip / blade_tip / muzzle), fx/shovel_flick/base (6 x 128, clip flick), icons/tools/shovel 128. For U-193 / 0.6.1.
- 11-09 11:10: B-221 exported (ea3f75fb, LEAD-accepted 10:5x): ui/title/background, the v3 title scene (Earth's camp at dusk), 1920x1080 + json. For 0.6.1.
- 11-09 06:0x-09:1x: B-201 (0.6.0 smoke read, all 75 shots; coordination/reports/blender/smoke_read_0.6.0.md, 517ae849 + 1008f40c): 17 defects routed by LEAD; mine fixed: terrain/earth/fill_decor_t2_1 (root_knot -> a pale root tangle) + fill_decor_t3_3 (mica_book -> a pale layered slab), b47759a4.
- 11-09 00:4x: props/dig/winch_post json stands_on = the drawn surface at the shaft's mouth (379b0b89; UNITY's U-176 question; json only).
- 11-09 00:35: B-219 (655fead8, LEAD-accepted after three fixes): the giants' floe nodes - props/jupiter/node_{ammonia_ice,metallic_hydrogen}, props/saturn/node_{ring_ice,ring_rock,helium3}, props/uranus/node_{methane_ice,superionic_ice}, props/neptune/node_{methane_ice,superionic_ice,deep_diamond}; B-176 format, json deck + item; for U-189.
- 11-08 12:10-22:5x: B-184 to B-217, the strip retirements, U-183's hand_socket (archived: coordination/status/archive/BLENDER_2026-11-09.md, BLENDER_2026-11-08.md).

## Ready for review
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
- (LEAD 13:4x) One lock <= 15 min; a painted planet with more than 8 scenes (Uranus: 16, 721 s) gets its own lock.
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
none held (last: 13:21:56-13:38:01, the B-227 export + B-220 Saturn / Uranus); no want on file: UNITY's U-194 chain runs, and LEAD's rule is no want of mine until it has released. No background waiters: I poll in the foreground.
