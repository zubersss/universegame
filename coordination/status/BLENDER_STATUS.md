# BLENDER STATUS
Updated: 2026-11-07 10:58 · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
10:58: B-158 Uranus paper part DONE: the palette ALL PASS (ef1553ae: cyan fog, cold white, one ember accent, dimmer than Saturn) + c2_uranus_designs.md (52c52ee5); one proposal (the lit variants sun_left / sun_right / night per deck). Still waiting for UNITY's chain to end for the Saturn gap plan.
LEAD cycle 268: the Vortex Whale ACCEPTED; the Saturn palette ACCEPTED (D-141: in PALETTES, setdefault dropped, ui/palettes/saturn row - c91d7c16); B-158 Uranus Ready after the Saturn previews; the Mercury rows export right after UNITY's U-123 commit, one slot each. 10:45 Mercury readiness: B-148's ground strips written (fae9b7e2: white regolith + slate side, joins 0.78 / 0.71, palette 100 %, scratch export OK) - B-148 / B-149 / B-150 rows complete. Next code: B-158 palette + notes; the Saturn gap plan when UNITY's chain ends.
10:36: the Saturn rig-set source (4423dc88) + dry run clean beside UNITY's lock (review_b157_saturn_rigset_dryrun.png: 26 parts 504x200 30 KB, json valid, palette 100 %, 136 MB). LEAD: when UNITY's chain ends with no want, lock-free one measured run each (the backdrop smoke test first, Saturn flora + floes, the four creatures, the Hydra, the aerostat review), then ONE lock <= 6 min for the five Saturn deck studies (no asking).
10:28-10:36 code + measured light checks under UNITY's chains: B-157 the Saturn creatures (f3fccc69: helium_jelly, hex_drake, floe_moth, ringmite; every frame in bounds), the Polar Hydra Grand rig (03ecb577), the props + ring chunks (review 113 MB, six valid); c2_saturn_designs.md state table. B-157 is all in source; waiting for a free gap (lock-free): the Saturn flora + floe previews, the four creature reviews, the Hydra preview, the backdrop smoke test, the aerostat review; the five Saturn deck studies need slots.
10:19-10:28 (UNITY's combined check + capture chains hold the lock from 10:19, ~55 min): the whale review DONE lock-free just before (267 MB, reads); the aerostat review waits. D-140 (Grand rigs <= 8 bones, "grand": true) in the validator + the whale / Maw rigs (c6a91ee0). B-157 sources: the Saturn flora (1c81b527, key poses <= 44 MB), floe strips ice + ring (3bf0b75b, checked 49 MB, joins <= 0.94), deck scenes with the rings edge-on / tilted + the Hexagon walls (code). Next: the Saturn creatures + the Polar Hydra (a Grand rig, 7 bones) + the props, code only until the lock frees.
10:02-10:18 SLOTS (one key or category per wrapper call, each lock released): (1) 10:02:04-10:03:50 + 10:04:44-10:05:40 numpy: the Mars plains study (re-run once: the mesas raised above layer1's skyline, the dust devil onto layer0) + the Jupiter deck3 broad-anvil re-run (reads as an anvil); (2) B-141 backgrounds/mars/plains EXPORTED 10:07:20 (515d28bc; log OK, seams 0.88 / 0.76 / 0.61, plains.json = the canyon's SceneLayout, review_b141_mars_plains.png stamped, 42.9 s, 700 MB); (3) B-142 EXPORTED 10:08:12-10:12:53 (74da5793; dustskater, scree_stalker, tube_lurker, polar_crawler + props/mars/tube_mound, all log OK, ink + palette in range, v2 removed on two; reviews review_b142_mars_*.png stamped); (4) B-144 EXPORTED 10:13:28-10:16:37 (644b9e74; the six Mars props, log OK, 24 v2 files removed; review_b144_mars_props.png stamped 10:17 lock-free). Slips: (a) my UI row key ui/c3_set (two parts) failed the wrapper's manifest check for every render 09:00-10:06 -> ui/c3/ui_set (629e892b; all 500+ keys checked); (b) the B-144 review peaked 430 MB lock-free (no lock, 2.1 GB free; I took the 291 MB export peak as its ceiling). Next lock-free: the whale + aerostat reviews, then B-157.
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
- B-158 lit variants: each Uranus deck as sun_left / sun_right / night sets (+ one survey layer0), cross-faded by UNITY with the season; or one set lined on both sides.

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
none held, no want on file (UNITY's combined Mars check + captures hold the lock from 10:19, ~55 min).
