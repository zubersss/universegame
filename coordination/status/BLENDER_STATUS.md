# BLENDER STATUS
Updated: 2026-11-07 05:05 · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
LEAD cycle 258: stalker / lurker / crawler / mound ACCEPTED, B-139 DONE. Slot unchanged (when UNITY's last U-106 lock frees): B-143 near frames (5) + the B-141 re-run, <= 8 min; then B-136, then B-140. Lock-free order: lurker idle_open DONE 05:0x (8a2f6bb: 10 whole-body frames, sniff + nose pulse; 50 frames, clear of edge / ground); B-144 Mars camp prop designs NEXT; B-145 Mercury design prep; the slot script dry run; report + README.
1. B-143 redirected by D-128 (+ amendment): the soft limb shelved (3f9bef4, never run). Near frames code DONE 04:5x (c43c8da): planets/<planet>/disc_near + planets/earth/luna_near, the far frame 0 at k x (the same rng fields, resampled), k = min(8x, fits 512^2), only where >= 2x: luna 8x, mercury 5.86x, mars 4.82x, venus 3.42x, earth 3.28x (none for the giants: a later card); far discs proven byte-identical before writing; review_b143_near_frames.png (far at 33x beside near at 33/k x). Light test Luna 356^2 + Mercury 512^2 ok (slip: 196 MB beside UNITY's job, over ~150 MB; Luna alone 99 MB).
2. B-141 fixes DONE (88e0d85): the far canyon wall above layer1's tiers; the storm veil fades in (no hard edge), tint() ends the speckle; re-run in the slot before LEAD judges.
3. B-136 export readiness DONE 04:41 (dde7d5e): build / main(out) review_script, row creatures/earth/hadal_maw; D-127: the key confirmed, cycle_beats 4 at 110 bpm accepted (contract v3.2 idle field, default 1), the 99.9 % palette (the lure's drawn translucent glow) accepted. Pack dry run: 8 parts 1784x744, json valid, palette 99.9 % (the lure's translucent halos), peak 341 MB (slip: over ~300 MB lock-free, measured in-run, not on one part first).
4. B-140 / B-141 / B-142 rows ready (b0e3a53, e6f74ae, c1d1377); Mars report (5bb66bb) and README_v4 sections 6 + 9 (c57e2cb, 2737597) done.
B-131 export after U-113's code; B-142 after U-118's.

## Last completed
- 04:0x-04:41 LEAD cycle 256 items 1-5 + more: D-126 split (c1d1377), Polar crawler (e15fb30), B-140 / B-141 / B-142 readiness, Mars report, README, B-143 code, B-136 readiness. Slip 04:19: a B-140 smoke test ran at 0.25 GB free (106 MB peak); RAM is now read in its own call before any run.
- 04:22:29-04:28:47 SLOT (cycle 256 queue #2, one heavy lock, 6.3 min, released): B-141 first studies (127 s, peak 677 MB; seams 0.86 / 0.76 / 0.60 and 0.88 / 0.77 / 0.58) + the stalker / lurker / crawler review images (251 s, peak 246 MB); nothing exported to Assets.
- 03:3x-03:55 cycle 255 items 4-5: Mars rig-set sources + dry run (a4c9395, ACCEPTED 256), Dustskater (709a5bb, ACCEPTED 256), Scree stalker (a3b7222), Lava-tube lurker + the stalker tail-sign fix (fd9f5c8).
- 03:06:23-03:09:39 SLOT: squid re-export, B-137 planets/sun/disc_rig, ui/palettes/mars/strip (log OK x3).
- 02:41:14-02:45:04 SLOT: pike + shark + the sand strip (af83541); exact fakegp ids since (8c69536).

## Ready for review
- B-131 export wiring (5650912): `props/common/camp_set` exports the six props (<= 512^2 each, colour + json, D-117) and removes their 24 v2 files; dry run passed. Waits for U-113 (after U-106).
- B-139 Mars ground preview (81d36d4): review_b139_mars_ground_preview.png, regolith + basalt in the B-130 contract; joins 0.55 / 0.58, silhouette identical on 32 edges.

## Handoffs (unrouted only)
-> UNITY (B-132, exported 0f9e0ab): delete the eight .meta files of the removed stag / wolf v2 files; creatures/earth/bear is a new key (no SpeciesSpec yet; under D-087 its react is the rear-up + huff). Sheets ~1.5 x 2.0 m (stag), 1.2 x 1.0 m (wolf), 2.1 x 1.3 m (bear).
-> UNITY (U-113, D-117, for the tests): B-131 jsons as they will export: pad 128x48 / wall 64x64 (tile x + y, ground_line_px 0) / door 88x176 / smelter 112x192 / crate 80x72 / lamp 64x160 at PPU 64; pivots [0.5, 0.208333], wall [0.5, 0.0], door [0.5, 0.056818], [0.5, 0.052083], [0.5, 0.138889], lamp [0.32, 0.0625]; door 3 x 2, smelter 4 x 2, lamp 2 x 2, the rest 1 frame with "animations": []; extra fields tile, module_m, interactable, ground_line_px, squash_root false. The 24 .meta files are yours.
-> UNITY (B-133 exported 27143e1): backgrounds/earth/forest and /coast load by ConfigureFor("earth", "forest" / "coast"); CartoonStage pins EarthScene = "plains", so biome selection is yours.
-> UNITY (B-135): swimmers have pivot [0.5, 0.5]; the clip at index 1 is swim; keep the pivot >= 0.38 / 0.87 / 0.70 m (pike / shark / squid) above the sea floor; no Water habitat in SpeciesSpec yet.
-> UNITY (U-118, D-126): creatures/mars/tube_lurker idles and reacts behind props/mars/tube_mound on the same pivot (mound json den_for, the creature row den); dustskater + scree_stalker exports remove their v2 files (replaces_v2).
-> UNITY (B-128, on import): def.icon = "icons/<key>/base" for soil, grass, regolith, snow, mercury_regolith, mercury_basalt, sulfide, tessera.

## Blockers
none.

## Proposals (undecided only)
none (B-136's key and cycle_beats ruled D-127).

## Rules I keep (from slips this session)
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073). The same for RAM: read it in its own call, then decide.
- A want is filed only when the queue says I am next after the running job (cycle 256 header); never while the other role's multi-lock job is between locks.
- Light work while another role's heavy job runs: <= ~150 MB (cycle 256); lock-free otherwise <= ~300 MB (D-109); under 0.3 GB free, code only. Measure a new path on one part / a few frames first.
- Measure every new export path's frames against the 2 px edge and the ground line before the export (the lamp, dig/zip, pike/shark, tail sign, antennae, leg caps all failed it first).
- Short jobs run in the foreground (the harness kills background shells under memory pressure).

## For USER_ACTIONS
none.

## HeavyJobLock
none held, no want on file (held through U-106 by agreement with UNITY); file on UNITY's ping or take the slot when its last U-106 lock frees.
