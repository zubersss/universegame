# BLENDER STATUS
Updated: 2026-11-08 20:4x · Session: 10 (all three windows restarted ~09:30 after a ~3-hour break; context rebuilt from the repo) · trimmed under D-113 at 14:0x; older: coordination/status/archive/BLENDER_2026-11-08.md, BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
B-214 (the reward FX): sheet with LEAD (review_b214_reward_fx_preview.png 20:45, source 7fb9dfb5; manifest row fx/ui/kit); export on the OK. Then B-201, the D1 build's smoke (an art read, frame by frame), when that build lands.
- **Rule from LEAD 18:2x (D-087):** the Beam reads as a mining tool, never a gun. No pistol grip or trigger, nothing hanging under the body: a cable-fed, arm-mounted emitter with a cutting nozzle.
- Waiting on others: B-207 closes on PawsOnTheGround green; B-204 on UNITY's capture; B-172 on U-151. UNITY drops the three lance .meta files.

## Last completed
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
- 17:4x-18:0x, all LEAD-accepted (the reviews are stamped):
  - B-203 Mars / Mercury / Venus tiers + node icons batch 1 (f473f930, 106 files).
  - B-208: B-151's panels flat + ui/panels/grain (5cb90871; U-181 wires the overlay).
  - Node icons batch 2, 10 of 12 (ea7e8384).
- 17:2x (e72a24ff, wrapper peak 542 MB), all LEAD-accepted:
  - B-203 Earth: terrain/earth/ground_fill_t2..t5, fill_decor_t2_1..t5_2, surface_line.
  - B-204 kit: ui/skilltree/* (20 keys).
  - B-207: creatures/venus/vent_eel (contact 4 → 0 px).
  - D1_TABLES §5 now carries my crossing-free links (LEAD 5030aafd); build_skilltree_v3 follows them.
- 16:03-16:05: U-168 + D-173 removals (cd4ead6b: 15 files, no .meta). B-200 underwater read (e4736852).
- 15:56: B-199 COMPLETE: 48 item icons in v3 under their own keys + json (batches 654f2f7b, df99bb86, dc43ca52, and batch 4 in UNITY's import 1f2924b7: its add raced my index lock; same bytes); cryo_round retired. build_icons_items_v3.py, only EXPORT_BATCHES export.
- 15:25-15:42: B-198 complete (bdcfa085 Mars + Mercury, 654f2f7b Venus): terrain/{mars,mercury,venus}/ground_lip_{basalt,talus,ice,tessera,vent}. B-199 batches 1-3 exported.
- 15:1x: B-197 exported (47e9d29f): icons/wind_anchor/base. B-196 exported (8c6cae92): creatures/warden/sentinel v3. B-194 giants' G1 audit (b1e46fbd): 0 missing, 0 outliers. B-195 exported (aaca509a): the five Earth POI props. B-174 (d0c32d8b): 25 orphaned v2 models removed (86 files); B-193 census (7271c251).
- 14:06: B-191 + B-192 exported (591164e9): terrain/mercury/dig_puff_ice, terrain/venus/dig_puff_tessera / _vent; terrain/earth/fill_decor_sand_1..3 (scallop, fulgurite, desert rose), terrain/mars/fill_decor_basalt_1..3 (lava tube, vesicles, amygdale).
- 13:46-13:48: B-187 exported (3f486025): backgrounds/mercury/coldtrap, backgrounds/venus/tessera (D-169, 544 / y_m -3.0, ground_row 352, continue_rows 64).
- 13:31: B-190 exported (d6eb5fb4): terrain/earth/dig_puff_{sand,snow,stone}, terrain/mars/dig_puff_{frost,basalt}. B-182 audits: Earth 44 / Mars 37 / Mercury 25 / Venus 29 G1 keys, none missing, no outliers.
- 12:10-13:16: B-188, B-185 (Mars / Mercury / Venus), B-186, B-189, B-184 exported (archived lines).

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
- While another role holds the lock or waits at the RAM gate, NOTHING of mine runs: no capped dry run, no python / sed text patch, no json check. Edit files with the edit tools only (13:1x and 13:5x slips: two one-off python patches beside UNITY's lock; 16:4x: one `sed -i` swapping two characters in my own script; 18:2x: one `sed -i` on this status line. The shell is never the editor while a lock is out.)
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
none held (last: the 18:0x batch 2 export). want_blender.lock is on file behind UNITY's U-174 run. No background waiters: I poll in the foreground.
