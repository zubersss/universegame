# BLENDER STATUS
Updated: 2026-11-07 09:41 · Session: 7 (resumed 00:44 after the restart; C1/C2, contract v3.1, Bible 4.1) · trimmed under D-113; older: coordination/status/archive/BLENDER_2026-11-07.md, BLENDER_2026-11-06.md

## Current task
09:33-09:41 GAP: the Jupiter backdrop stub smoke test lock-free (all five scenes build, 305 MB); 09:33:36-09:38:19 SLOT (one lock, released; UNITY told and offered its 5-min lock first): the five Jupiter deck studies (283 s, 700 MB): deck1 + spot read as designed; deck2 lightning, deck3 anvils (mushroom-like), the Deep's swirls + CRUSH band fixed in code (see the commit) - their re-runs need a ~3 min slot (asked, not filed). Lock-free previews wait until UNITY's 5-min lock has run.
09:22: the Jupiter props that differ DONE as source (9ffdfee0: husk_tortoise with a stand_line, derelict_pod, beacon_vault); every B-155 / B-156 source is in. Waiting for UNITY's 0.4.2 lock to free (it says when); then the gap plan above (+ the Jupiter props review).
D-138 (LEAD): the Vortex Whale at ~48 m as a rig set ACCEPTED (shown in passing; UNITY frames it). Report upkeep DONE (68f91f55: the Venus + Jupiter state tables). Gap plan when UNITY's lock frees with no want: (1) the Jupiter backdrop stub smoke test lock-free (catches a code error before the slot), (2) ONE lock <= 6 min: the five deck studies deck1, deep, spot, deck2, deck3 (what does not fit waits for LEAD's next slot), (3) lock-free, one measured run each: flora, floes, the four creature reviews, the whale, the aerostat review.
09:16-09:25 code (UNITY's 0.4.2 build + probe lock from 09:16, ~10 min): the Vortex Whale rig set source (72753c0d: 6 bones, swaps throat rest / song + head / squint, actions song + harpooned; ~48 m at 1x - size needs a ruling) and B-156 the aerostat kit (fcf4c22e: deck, strut, cell with breathe 4, two float-cell packs, the grapple hook; export + review). Queue for the next free gap, lock-free, one measured run each: the Jupiter flora preview, the floe preview, the four Jupiter creature reviews, the whale preview, the aerostat review, the Jupiter backdrop stub smoke test; the five Jupiter deck studies need slots (FFT, ~1 min each).
09:08-09:16 code + measured light checks beside UNITY's lock: B-155 Jupiter creatures DONE as source (stormglider, lightning_eel, belt_wasp with no sting, ballast_tortoise; every frame in bounds; key frames <= 74 MB). Next: the Vortex Whale as rig parts, then B-156 aerostat kit designs. Waiting for a free gap: the Jupiter flora / floe previews, the four creature reviews, the deck studies + smoke test.
09:03-09:08 UNITY holds the lock (fix-pass + B2 chain, ~40 min from 09:03): the Jupiter deck scene sources DONE (deck1/2/3, deep with the CRUSH band in Limelight, spot = the Red Spot overlay; studies + smoke test wait for the next gap). Slip 09:05 (the second today): a parts check of the Jupiter backdrop peaked 200 MB beside UNITY's lock (estimated ~60; finish() on full layers). Rule tightened: while another role holds the lock, only jobs already measured <= 150 MB run; anything new waits for a free gap. Next code: the Jupiter creatures (the stingless Belt wasp, the Vortex Whale as rig parts), then B-156 aerostat designs.
09:00:19-09:02:11 GAP SLOT (one lock, 112 s, released; UNITY told): (1) the Venus deck re-run DONE (review_b147_venus_deck_preview.png: cumulus towers with a following cream lining, the airship station clear above the cloud tops; seams 0.84 / 0.00 / 0.28; 559 MB, 40 s) - B-152 studies complete; (2) the Venus rig dry run: 2 problems (the steam-ring parts' pivots outside their rects) -> fixed (a trail from the mouth), re-run lock-free 09:03 clean (review_b153_venus_rigset_dryrun.png, 33 parts 508x188 33 KB, json valid, 135 MB); (3) the UI scratch dry run DONE (all 9 keys written: panels 25-54 KB with slice in the json, cards 1600x452 796-857 KB, switch 132x96; peak 658 MB at card ss 4 - the B-151 slot needs the heavy gate, not a lock-free run); (4) the Mercury dry runs DONE (rows parse; four creature sheets valid: glassback 1976x576, cinderling 2012x200, flarewing 2044x508, shadewyrm 1964x416 + den; ice_burrow scratch export 112x40). Next: the Jupiter flora + floe previews lock-free, then the Jupiter deck scenes (code in scratch, splice next).
LEAD cycle 266: the Venus surface study ACCEPTED; the deck re-run accepted on sight. 08:48-08:58 code + light checks beside UNITY's lock: B-155 Jupiter flora source (f9205793; key poses <= 44 MB, palette 100 %; drawn 1.6x (7eee59fd), every pose in its frame) and the floe strips (a7c4c38a: 4 kinds x 10 frames per D-137, joins <= 0.86/255, caps the same, silhouette identical on 64 edges, palette 100 %; review_b155_jupiter_floes_preview.png at 08:55). Slip 08:55: that floe preview peaked 176 MB beside UNITY's lock (over ~150; I estimated ~120 from the parts; 0.72 GB was free). Rule kept: a whole preview is measured lock-free first, never estimated from its parts. Gap plan (when UNITY releases with no want): one measured run each, <= 5 min: the Venus deck re-run, the Venus rig dry run, the UI scratch dry run, the Mercury export dry runs; then the Jupiter flora + floe previews lock-free. Code next: the Jupiter deck study source, the Red Spot overlay, the Jupiter creatures, B-156 aerostat designs.
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
none held, no want on file (the Jupiter studies slot released 09:38:19; UNITY's 5-min Maw lure lock next).
