# BLENDER STATUS
Updated: 2026-11-07 08:00 · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
LEAD cycle 264: the Glassback + the day / twilight studies ACCEPTED; every Mercury creature accepted; Mercury cards B-148 / B-149 / B-150 in Backlog (after U-118). 07:55:26-07:57:22 SLOT: the Mercury night study DONE (review_b145_mercury_night_preview.png, seams 0.68 / 0.66 / 0.63, 559 MB): B-145 can close. Lock-free order now: B-146 Earth + Mercury title cards + the full UI preview; B-147 plants preview, the four Venus creature reviews (one measured run each; key frames already in bounds), the Venus backdrop sources; the Mercury export dry runs; report upkeep.
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
- B-146 UI panels + switch (a09e660d, b1626503) once the title cards render; B-147 Venus plants once previewed.

## Handoffs (unrouted only)
-> UNITY (B-132, exported 0f9e0ab): delete the eight .meta files of the removed stag / wolf v2 files; creatures/earth/bear is a new key (no SpeciesSpec yet; under D-087 its react is the rear-up + huff).
-> UNITY (B-133 exported 27143e1): backgrounds/earth/forest and /coast load by ConfigureFor("earth", "forest" / "coast"); CartoonStage pins EarthScene = "plains", so biome selection is yours.
-> UNITY (B-135): swimmers have pivot [0.5, 0.5]; the clip at index 1 is swim; keep the pivot >= 0.38 / 0.87 / 0.70 m (pike / shark / squid) above the sea floor.
-> UNITY (U-118, D-126): creatures/mars/tube_lurker idles and reacts behind props/mars/tube_mound on the same pivot (mound json den_for, the creature row den); dustskater + scree_stalker exports remove their v2 files (replaces_v2).
-> UNITY (B-128, on import): def.icon = "icons/<key>/base" for soil, grass, regolith, snow, mercury_regolith, mercury_basalt, sulfide, tessera.

## Blockers
none.

## Proposals (undecided only)
none.

## Rules I keep (from slips this session)
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073). The same for RAM: read it in its own call, then decide.
- A want is filed only when the queue says I am next after the running job; never while the other role's multi-lock job is between locks.
- Light work while another role's heavy job runs: <= ~150 MB; lock-free otherwise <= ~300 MB (D-109); under 0.3 GB free, code only. Measure a new path on one part / a few frames first.
- Measure every new export path's frames against the 2 px edge and the ground line before the export.
- Short jobs run in the foreground; no background waiters (the harness reaps them under memory pressure): check the locks folder each turn.

## For USER_ACTIONS
none.

## HeavyJobLock
none held, no want on file (the night slot released 07:57:22).
