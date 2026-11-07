# BLENDER STATUS
Updated: 2026-11-07 10:01 · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
10:01 code beside UNITY's U-112 lock: export readiness - build(name) + build_<name> added to the Mercury / Venus / Jupiter creature modules (b7ce2043; the rows named them, only Mars had them - my Mercury dry run checked layouts only and missed it); the Jupiter + B-156 rows (5e7e216e: four creature rows replace v2, the whale rig set, flora rig set, floe strip set, five decks, three Jupiter props + six aerostat-kit prop rows replace v2; floe + whale export hooks). B-157 Saturn palette proposal ALL PASS (231a59ff). Next: c2_saturn_designs.md; after UNITY's lock: the plains + deck3 slot (want filed), then lock-free the whale + aerostat reviews and a Jupiter scratch export dry run.
09:57: LEAD's catch (cycle 267): B-141's third Mars set backgrounds/mars/plains written (9ec15830: sky + wind streaks + far mesas / rolling plain + craters + a dust devil / near ground + ripples + dust; row seed 14103). WANT FILED 09:56:44 (D-039, while UNITY's U-112 lock is on): one slot <= 6 min = the plains study, the export by the wrapper if the 2x seams pass, the deck3 anvil re-run (LEAD: render the broad anvil). Then lock-free: the whale + aerostat reviews. Code meanwhile: the Jupiter export rows, B-157.
LEAD cycle 267: the five Jupiter decks + the Spot, the flora, the capped floes, the rig dry run ACCEPTED; B-157 Saturn design prep Ready. 09:44:33-09:47:20 SLOT (re-run deep / deck2 / deck3, 167 s, 699 MB, released): the CRUSH band clear, spiral swirls, lightning with a halo; deck3's anvil then broadened in code (18564d43: the thin wedge read as a beak). 09:48-09:53 lock-free, one measured run each: flora 301 MB, floes 176, rig dry run 132 (40 parts, valid), stormglider 198, lightning_eel 196, belt_wasp 192, ballast_tortoise 417 (problems none in all four), Jupiter props 102 (three valid); the whale and aerostat reviews hit preview bugs, fixed (f4a51fb9), re-run after UNITY's U-112 lock. Slip 09:53: the tortoise review peaked 417 MB lock-free (over ~300; no lock held, 2.2 GB free; its 288x176 frames were not measured first). Next code: the Jupiter export rows + a scratch dry run, then B-157.
09:42: the Jupiter rig-set source DONE (8041ee35: bones 2 / 4 / 1 / 4 / 6). LEAD slotted the ~3 min re-run of deep / deck2 / deck3 right after UNITY's Maw lure lock (a U-112 want, if filed, goes first). Then lock-free, one measured run each: flora, floes, the four creatures, the whale, the aerostat kit, the rig dry run, the Jupiter props. LEAD reviews at 09:49 / 10:49.
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
none (the whale's size ruled in D-138).

## Rules I keep (from slips this session)
- While another role holds the lock, run only jobs already measured <= 150 MB; a new job (or a new whole preview) is first measured in a free gap, never estimated from its parts.
- A lock check is its own call; Blender starts only in a later call after reading a clear result (D-073). The same for RAM: read it in its own call, then decide.
- A want is filed only when the queue says I am next after the running job; never while the other role's multi-lock job is between locks.
- Light work while another role's heavy job runs: <= ~150 MB; lock-free otherwise <= ~300 MB (D-109); under 0.3 GB free, code only. Measure a new path on one part / a few frames first.
- Measure every new export path's frames against the 2 px edge and the ground line before the export.
- Short jobs run in the foreground; no background waiters (the harness reaps them under memory pressure): check the locks folder each turn.

## For USER_ACTIONS
none.

## HeavyJobLock
want_blender.lock FILED 09:56:44 (LEAD cycle 267: the Mars plains study + export, the deck3 re-run; after UNITY's U-112 probe).
