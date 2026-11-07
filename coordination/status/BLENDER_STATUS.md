# BLENDER STATUS
Updated: 2026-11-07 08:44 · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
08:40-08:44 B-155 Jupiter design prep, paper part DONE (67816d87): the palette proposal ALL PASS (build_c2_jupiter_palette.py, 11 MB) + c2_jupiter_designs.md (five faceless flora, floe strips, four deck backdrop notes + the Red Spot overlay, the CRUSH band and lightning on layer2, the creature re-ink list, props). Two proposals need a ruling (Proposals below). Next: the dry runs (Venus rigs, UI scratch, Mercury exports) and the deck re-run when RAM / a slot allows; then the Jupiter flora drawings.
08:35-08:40 code only (UNITY holds the lock, 0.25-0.42 GB free): B-153 Venus rig-set source DONE (7dd59765: 33 parts, bones 2/5/4/6/3, the bells a chain so they swing out of phase; the dry run waits for RAM); B-146 export readiness code DONE (56671818: build_ui_v3.export, render.py do_ui_set, row ui/c3_set; slice jsons, cards 1600x452 for BC7, switch parts off / on; the scratch dry run waits for RAM). Next: B-155 Jupiter design notes (writing), then the dry runs (Venus rigs, UI scratch, Mercury exports) and the deck re-run slot when free.
LEAD cycle 265: B-146 + B-147 DONE as designs; cards B-151 (UI export) / B-152 (Venus backdrops, studies in a free <= 5 min slot) / B-153 / B-154 in Backlog; B-155 Jupiter design prep Ready. 08:28:49-08:31:26 SLOT (numpy, B-152 Venus studies, released, 157 s, 559 MB): surface DONE (review_b147_venus_surface_preview.png: haze bands, terraced tesserae lit by vent glows, glassy glints, rain that stops mid-air); deck studied, then fixed in code (88ccee89: cumulus towers with a following cream lining, the airship station above the cloud tops) - its ~80 s re-run waits for a free slot (no want filed). 08:34: UNITY holds the lock, 0.25 GB free: code only (the Venus rig-set source, B-146 export readiness code, the Mercury export rows, B-155 notes).
08:19-08:28 lock-free (no lock held): B-147 the four Venus creature reviews DONE (6d5f7337: drifter, acidmoth, crab, eel; problems none, ink 2.00-3.00 / 1.00-1.50, palette 100 %, <= 198 MB; crab crust + rim + bigger claws, eel thicker, eel bump head drop damped) - ready for LEAD; props/venus/vent_mouth DONE (d8ac7e69: 96x40 den on VENT_TOP, den review json valid, palette 100 %, 108 MB) - ready for LEAD; the Venus backdrop stub smoke test DONE (deck + surface build, 233 MB). Next: the Mercury export dry runs, report upkeep.
08:0x-08:1x lock-free: B-146 full UI preview DONE (3715aa62: review_b146_ui_preview.png, the five 9-slice panels at 1x + stretched with Patrick Hand text, the switch, the Earth / Mars / Mercury title cards at 1x; 247 MB) - ready for LEAD; B-147 Venus plants preview DONE (review_b147_venus_plants_preview.png, drawn 1.6x, palette 100 %; 301 MB) - ready for LEAD. Next: the four Venus creature reviews (one measured run each), the Venus backdrop stub smoke test, the Mercury export dry runs.
LEAD cycle 264: the Glassback + the day / twilight studies ACCEPTED; every Mercury creature accepted; Mercury cards B-148 / B-149 / B-150 in Backlog (after U-118). 07:55:26-07:57:22 SLOT: the Mercury night study DONE (review_b145_mercury_night_preview.png, seams 0.68 / 0.66 / 0.63, 559 MB): B-145 can close. Lock-free order now: B-146 Earth + Mercury title cards + the full UI preview; B-147 plants preview, the four Venus creature reviews (one measured run each; key frames already in bounds); the Venus backdrop sources DONE (1d646544: deck + surface, code; the stub smoke test waits for RAM); the Mercury export dry runs; report upkeep. 07:59: UNITY holds the lock (batch B re-measure), 0.29 GB free: code only.
07:49:00-07:53:51 SLOT (numpy, the Mercury backdrop studies, released): day + twilight DONE (review_b145_mercury_day_preview.png, _twilight_: ink sky + stars, the huge Sun with a corona / half-set at the terminator, crater rims with hard slate shadows, Glassreed tufts at twilight); night cut by my 290 s guard (~2 min a scene): asked LEAD for a short slot. Next lock-free: the full UI preview, the Venus plants preview, the Venus creatures' key frames / reviews.
07:3x-07:5x lock-free (no lock held at the start): the Glassback full review DONE review_b145_mercury_glassback_preview.png (problems none, ink 2.00-3.00 / 1.00-1.50, palette 100 %, 220 MB, 268 s); Venus creatures source: Acidmoth, Pressure crab (83195e4d), Vent eel (all frames in bounds); B-146 Mars title card checked at ss 2 (181 MB). Slip 07:5x: the title-card run started in the same command as the lock listing, which showed UNITY had just taken the lock again: 181 MB beside UNITY's job (over ~150 MB). The rule stands: the lock / RAM check is its own call, then decide.
LEAD cycle 263: the Cinderling ACCEPTED, the Shadewyrm note closed (json valid), the Mercury rig-set dry run ACCEPTED. The optional Mercury backdrop slot comes after UNITY's commit 3 (its chain + the 0.4.1 profile hold the lock; 0.08 GB free at 07:28: code only). Lock-free when RAM allows, in order: the Glassback review (a longer limit), the B-146 title cards + full UI preview, the B-147 Venus plants preview, the Venus creatures (Sulfur drifter source c123f584; the Acidmoth, Pressure crab, Vent eel + its vent-mouth den next, code first).
1. Gated runs DONE 07:09:10-07:14:09 (one lock, numpy, released): Mercury rig dry run review_b145_mercury_rigset_dryrun.png (500x168 24 KB, 26 parts, bones 2/2/6/2/2, json valid, palette 100 %, 133 MB); the Mercury backdrop stub smoke test (day / twilight / night run, 217 MB); review_b145_mercury_cinderling_preview.png and review_b145_mercury_shadewyrm_preview.png (problems none: json valid, ink 2.00-3.00 / 1.00-1.50, palette 100 %, <= 198 MB). The Glassback review hit my 150 s timeout (52 frames at 176x112): re-run next gap.
2. B-146 UI designs, source DONE (a09e660d, b1626503): a TrueType reader (Limelight + Patrick Hand from Assets/_Game/Fonts), five 9-slice panels + the film switch checked (48 MB; corners kept, edges clean when stretched); the 1600x450 title cards + the full preview wait for RAM.
3. B-147: the Venus palette ACCEPTED (D-134; in PALETTES, 37828001, + the ui/palettes/venus row); c2_venus_designs.md (25afcafd); the five plants' source (fcec304a); the preview waits for RAM.
4. Accepted / done earlier today (cycles 258-261): B-145 Mercury palette (D-130), plants, Flarewing, Shadewyrm + props/mercury/ice_burrow (D-126); Glassback, Cinderling drawn; Mercury rig-set + backdrop sources; B-144 Mars prop designs (export after U-118 with B-142; rows + dry run done); B-142 rows complete. Exports verified: B-131, B-136, B-140, B-141, B-143.
B-142 export after U-118's code; Mars props with their card; Mercury / Venus exports wait for their cards.

## Last completed
- 07:09:10-07:14:09 gated numpy runs under one lock (above).
- 05:44:51-05:45:52 SLOT (wrapper): B-131 props/common/camp_set exported, 24 v2 files removed (log OK, 60.8 s, peak 727 MB).
- 05:33:58-05:38:24 SLOT (wrapper): B-141 backgrounds/mars/canyon + storm exported (log OK x2, peaks 694 / 761 MB).
- 05:30:22-05:30:51 SLOT (wrapper): B-140 flora/mars/rigset + terrain/mars/ground_strip_set exported (log OK x2).
- 05:24:23-05:26:35 SLOT (wrapper): B-136 creatures/earth/hadal_maw exported (log OK, 115.6 s, peak 676 MB).

## Ready for review
- B-146 UI: review_b146_ui_preview.png (panels, switch, three title cards). B-147: plants, four creatures, vent_mouth den (previews in blender/preview/review_b147_*).

## Handoffs (unrouted only)
-> UNITY (B-132, exported 0f9e0ab): delete the eight .meta files of the removed stag / wolf v2 files; creatures/earth/bear is a new key (no SpeciesSpec yet; under D-087 its react is the rear-up + huff).
-> UNITY (B-133 exported 27143e1): backgrounds/earth/forest and /coast load by ConfigureFor("earth", "forest" / "coast"); CartoonStage pins EarthScene = "plains", so biome selection is yours.
-> UNITY (B-135): swimmers have pivot [0.5, 0.5]; the clip at index 1 is swim; keep the pivot >= 0.38 / 0.87 / 0.70 m (pike / shark / squid) above the sea floor.
-> UNITY (U-118, D-126): creatures/mars/tube_lurker idles and reacts behind props/mars/tube_mound on the same pivot (mound json den_for, the creature row den); dustskater + scree_stalker exports remove their v2 files (replaces_v2).
-> UNITY (B-128, on import): def.icon = "icons/<key>/base" for soil, grass, regolith, snow, mercury_regolith, mercury_basalt, sulfide, tessera.

## Blockers
none.

## Proposals (undecided only)
- B-155 floe caps: two extra frames per floe strip (cap_left / cap_right after the 8 tiles, same 64x152 cell + pivot) so a finite floe is cap + n tiles + cap; GroundStrip.cs places tiles only today (a UNITY change).
- B-155 aerostat kit: re-ink props/common/aerostat_{deck,strut,cell}, float_cell_pack_mk1/2, grapple_hook once for all four giants (Earth palette like the camp set).

## Rules I keep (from slips this session)
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073). The same for RAM: read it in its own call, then decide.
- A want is filed only when the queue says I am next after the running job; never while the other role's multi-lock job is between locks.
- Light work while another role's heavy job runs: <= ~150 MB; lock-free otherwise <= ~300 MB (D-109); under 0.3 GB free, code only. Measure a new path on one part / a few frames first.
- Measure every new export path's frames against the 2 px edge and the ground line before the export.
- Short jobs run in the foreground; no background waiters (the harness reaps them under memory pressure): check the locks folder each turn.

## For USER_ACTIONS
none.

## HeavyJobLock
none held, no want on file (the Venus studies slot released 08:31:26; UNITY holds the lock at 08:34).
