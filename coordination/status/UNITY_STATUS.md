# UNITY STATUS
Updated: 2026-11-08 01:50 · Session: 9 (all three windows restarted ~01:27; session 8's detail is in git log)
## Current task
U-148 (D-158, the owner's 0.4.7 flight: the climb's stutter and zoom), started 01:50; then U-149 (weight), U-150 (boost + sound barrier), all lock-free code ahead of every other card (LEAD 01:4x).
## Last completed
CaptureU127Jupiter 1-5, 01:37:32-01:39:14 (one lock, 102 s, CAPTURE OK, clean log; lock released, want gone): frames in reports/unity/u127/. They FAIL by eye (finding below). Before it: lock B's tests green 01:14-01:18 (MarsStageTests 3/3; the Jupiter PlayMode slice 20/20), the restart killed its captures, my stale lock removed 01:29; B-170's title-card metas + the ui group / atlas committed (a6361460); U-142's code ahead of lock C (6cd6bc7d: GameInfo 0.4.8, the smoke's four Jupiter shots + the Venus / Jupiter cards, 35 shots).
## Finding: the u127 frames (U-127 not ready; it also blocks 0.4.8's Jupiter smoke shots)
1. The deck sets are mostly out of frame: each is hung off its band's floor (deck2 datum 600, deck3 300, deep 100) but the floes stand up to ~260 m above it, so the camera (deck2 y 818, deck3 527) sees only the sky wash: 1_floe, 2_storm, 4_spot and 5_whale are flat tan; 3_deep (camera 165 over datum 100) shows just the set's top swirls at the frame's bottom, so a set paints only ~55 m above its datum. The log says the art loaded (fallback False, spot alpha 1.00 in 4 / 5), so the art is in; the placement is wrong. Fix idea: on the decked giants the set's datum follows the camera inside the band (clamped to the band's floor and its top minus the set's height), through the U-128 crossfade; a GiantBandsPlay assert that the set's painted band covers the frame at a floe 200 m up.
2. Only the ice floe draws its strip (1_floe: the capped ice strip). 3_deep, 4_spot and 5_whale show blurry block tiles where the core / spot / derelict strips belong (MaterialsLoaded 4, so the strip-per-floe-kind pick misses).
3. Two vertical ink lines run through every frame (x ~95 / 607 px on deck2, ~287 / 415 on deep): a layer's edge or a column rule; not yet traced.
4. 5_whale shows the flukes, not the head (the whale faces +x): D-138 holds (one end only), but the head should cross the frame: spawn it facing -x or at fx - 14.
Proposal P-52: a U-127 fix card (items 1-4) before lock C, or 0.4.8 ships without the Jupiter shots (smoke back to 31 shots: the two new cards only). The flight cards stay first; this waits for LEAD's order.
## Next up
U-148 → U-149 → U-150 (lock-free code) → my flight check after BLENDER's B-163 slot 1 → the U-127 fix if LEAD orders it (P-52) → lock C = 0.4.8 (flight + U-147 + Jupiter; release in Build/MERIDIAN_0.4.8/, the probed dev build in _dev/, the smoke with climb shots) → U-129 slice 2 (the Saturn creatures, B-164; the Polar Hydra Grand rig, D-140).
## Ready for review
U-126 floe caps (EditMode; u127/1_floe shows the capped ice strip, the other floe kinds miss their strips: the finding); U-129 slice 1 (code: Saturn on the decked-giant machinery, the Hexagon zone + overlay, the ice / ring strips, the biomes; SaturnStageTests ×4); U-130 slice 1 (code: UranusSeason, the deck sets by the season's light with the survey layer0, the ice / dark strips, the biomes; UranusStageTests ×7); U-143 (both builds in one call; tools/unity_build_selftest.ps1 green, no Editor); U-133 slice 1 (code: Neptune decks + the storm / spot zones, the pulsed rim layer, the wind lean, the ice / superionic strips, the biomes; NeptuneStageTests ×8); U-147 (HUD lettering on paper tags; MenuHudTests +1), U-146 (the survey scan pulse; UranusStageTests +1), U-144 (Neptune's -x zones mirrored, the drift, the anchor, the gust warning; NeptuneStageTests +3)
## Handoffs
→ BLENDER (via LEAD), U-125's keys for B-152 / B-153 / B-154: the sets backgrounds/venus/deck and /surface (deck hung off DeckY − 2 = 768, surface off the ground); the strips terrain/venus/ground_strip (the basalt crust, every ground column) and terrain/venus/ground_strip_deck (the deck planks, laid 1 m a frame along the station's deck top at 770.14, no fill); the rig set's biomes as in build_c2_venus_rigs.py (vent_fields, surface_plains; cloud_deck / station_rails grow nowhere until the station gets plants); the Vent eel's den props/venus/vent_mouth.
## Blockers
(none)
## Proposals
P-51: B-156's re-inked kit (props/common/aerostat_deck / _strut / _cell) is loaded only by CaptureU127Jupiter and the 0.4.8 smoke, which stage it as a sprite; in play the Deck piece still draws props/venus/aerostat_deck everywhere (PieceSpec has one artKey). Proposal: the Deck piece draws props/common/aerostat_deck on the four giants (a per-planet art key on PieceSpec, BaseBuilder picks it by PlanetKey), Venus unchanged; a small card after 0.4.8. Until then the owner's page should not promise a buildable kit on Jupiter.
## For USER_ACTIONS
(none)
## Housekeeping
Editor churn in the tree (the Generated/Models *.mat _MainTex fills, TMP font asset, animator.controllers, UnderwaterTint.mat, link.xml.meta, two InitTestScene files): never staged; my commits list files explicitly.
## HeavyJobLock
none held, no want (the capture job took and released the lock 01:37-01:39; BLENDER's B-163 slot 1 is next). My next want: the flight check, filed only after BLENDER takes the lock (D-039). No background waiters.
