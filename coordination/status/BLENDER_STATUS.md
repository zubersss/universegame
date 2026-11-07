# BLENDER STATUS
Updated: 2026-11-06 23:5x · Session: 6 (C1, contract v3.1, Bible 4.1) · trimmed under D-113; everything older: coordination/status/archive/BLENDER_2026-11-06.md

## Current task
While-waiting list (LEAD cycle 247), in order; each logged here:
1. C2 Earth plant rig sources: DONE 23:5x (5cdca3b). build_c2_earth_rigs.py (+ preview_c2_earth_rigs.py): Nodbell 4 bones (bells nod on a 7+1 beat cycle and on react), Shiverbarrel 2 (shiver body cycle 6+1+1+1+1, crown pops open on react), Curlfrond 4 (centre fiddlehead curls open/half/curled/half on the beat, all three curl tight on react), Whiptuft 4 (seed stalks whip; the clump + stalks flatten on react), Thriftcushion 6 (poms bob out of phase, all rise on react). Out-of-phase motion = bone cascades with pivots side by side at the base (Unity's depth lag 0.35 rad); only today's runtime features. All six Earth plants in ONE rig set: 44 parts, sheet 500x212, rig json valid §11.3, ink 2.0-3.0 / 1.0-1.5 px. Review blender/preview/review_c2_earth_rigs_preview.png: each plant 1x on the B-114 plains beside the surveyor, rest + react 2x, the idle loop frame by frame with Unity's SwayCurve/SquashCurve maths, swap_cycle states. Beats kept inside Bible §9.2's 100-120 (the validator caught 150 and 90).
2. C2 Earth ground strip source (grass / soil / stone re-inked v3.1, paper fill, drawn 1 m grass lip, previewed on the plains): NEXT.
3. Disc review peak measure: want_blender.lock filed 23:51 (UNITY took heavy_unity.lock 23:49); runs build_discs_v3 export to a scratch dir + the review in bundled python under my own lock, logs the peak.
4. Painted Sun disc design, preview only.
5. README_v4.md refresh.

## Last completed
- 23:33-23:38 QUEUE #2 BATCH EXPORTED (f612225; one heavy lock, 4.9 min, log OK x4, peak 988 MB, lock released, UNITY told): B-121, B-128, B-122 (see Ready for review).
- 23:2x C2 Curlfrond fix (LEAD cycle 245): mustard fiddlehead tips + ink-behind fronds; review_c2_earth_plants_preview.png refreshed.
- 22:5x Disc review memory (673193b): build_discs_v3.preview turns each panel to uint8 as it finishes and writes the PNG directly (the 22:09 run peaked 2289 MB on the float canvas). Measure on the next disc run.
- 22:1x B-119 + B-120 exported (24f8fbb), accepted and verified cycle 246; live in UNITY's code (960af2f).
- 21:54 B-125 surveyor v3.1 exported (Done cycle 245). 21:13 B-124, B-126, B-127 exported.

## Ready for review
(B-121, B-122, B-128 verified by LEAD cycle 247; Done on UNITY's captures / import.)
- B-121 (f612225): ui/hud/gauges_color.png 1024² + gauges.json (three dials, needles as parts with pivots + min_deg / max_deg / danger_below), escape_line 512x64 ("tile": true, seam_x 0.00), escape_sign 192x224 BLANK (json "lettering": "runtime", pivot [0.5, 0]; UNITY letters it in Patrick Hand, U-104). Review blender/preview/review_b121_hud.png (1080p over the B-114 plains, stamped 23:34).
- B-128 (f612225): icons/{soil, grass, regolith, snow, mercury_regolith, mercury_basalt, sulfide, tessera}/base_color.png 64x64 (~1 KB each) + base.json (style v3, ppu 64, pivot centre). Review blender/preview/review_b128_icons.png (3x + 1x, ink 2.0-2.9 / 1.0-1.5 px).
- B-122 (f612225): ships/pilgrim/rig_color.png 920x912 (67 KB, 11 parts) + rig.json (pilgrim_side: 6 bones, bell/porthole slots, 7 sockets, fin_wobble 8 loop / leg_flex 8 / hatch_open 6 at 12 Hz; pilgrim_top: 3 bones, fin_wobble 8) + ships/pilgrim/puff 1052x128 (8-frame loop, 17 KB). Source sources/ships/pilgrim_v3_rig.blend. Reviews: review_b122_pilgrim_rig.png, review_b122_pilgrim_rig_assembled.png (rig built from parts + bones at 1x beside the surveyor, ±35 tilt, every clip, rig json valid §11.3), review_b122_pilgrim_puff.png. The puff review's "idle loop" box shows "!" because the clip is named puff (it IS a loop: FX, not a character idle); every other box passes or is self-checked. Done on U-103's capture.

## Handoffs (unrouted only)
-> UNITY (C2, when the Earth rig set re-exports): every plant now carries "biomes" (nodbell plains/forest, shiverbarrel desert, curlfrond forest/taiga, whiptuft plains/coast, thriftcushion coast/tundra; JsonUtility ignores it today). FloraRigs picks Set.plants at random, so a desert cactus would spawn on the plains until placement filters by biome.
-> UNITY (B-128, on import): set def.icon = "icons/<key>/base" in ItemRegistry for soil, grass, regolith, snow, mercury_regolith, mercury_basalt, sulfide, tessera (they pass null today).
-> UNITY (B-122, on import): ships/pilgrim/side_a..e and top_a..b were never exported (superseded by D-111; manifest preview_only). Sockets in rig.json, metres from the root: tail_exhaust, leg_l, leg_c, leg_r, door, attitude_l (-1.5, 2.6), attitude_r (1.5, 2.6). The ±35 flight tilt is the root transform.

## Blockers
none.

## Proposals (undecided only)
- -> LEAD (C2, from coordination/reports/blender/c2_earth_creature_reink.md): (1) a "swim" clip cap = walk/fly (12-16) in contract §11.2 + ArtRules.ClipCap; (2) Hadal Maw as a §11.3 rig set (too big for one sheet); (3) a shared Earth creature atlas, because the Earth scene with the ship landed is near the D-089 eight-texture budget.

## Rules I keep (from slips this session)
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073; two slips, 15:09 and 17:12).
- A want is filed only after the other role takes the lock (D-039); a rank is live only while a want or lock is on file (D-112): a free lock with no live rank ahead is mine to take.
- Light work while a heavy job runs: ≤ 300 MB extra (D-109). Lock-free previews use meridian.fakegp in Blender's bundled python (~100-200 MB).

## For USER_ACTIONS
none.

## HeavyJobLock
want_blender.lock filed 23:51 for the disc peak measure; UNITY holds heavy_unity.lock since 23:49.
