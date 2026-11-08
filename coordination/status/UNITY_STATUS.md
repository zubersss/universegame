# UNITY STATUS
Updated: 2026-11-08 10:2x · Session: 10 (resumed 09:3x after the ~3-hour break; earlier entries: coordination/status/archive/UNITY_2026-11-08.md)
## Current task
U-163 Build 0.5.0 (started 10:2x): the smoke's new Earth shots written lock-free first, then one lock (part scripts): Earth slice + M1Loop + M3Inner + SaveLoad v2 on the build's code → release + dev players → the probe (two runs, D-152) → the smoke into reports/unity/smoke_0.5.0/.

## Last completed
U-157 (P-54, P-55) + U-158 + U-161 checked, 09:47-10:17 (six short locks: compile + EditMode, four PlayMode slices, three captures); commits c4d59ee4 (the 06:17 tree), b69d80c1 (code, tests, the import), and this status commit (frames).
- Compile 0 errors, 0 new warnings (two of mine fixed). EditMode 442/442 (LayerFollowTests +1). PlayMode green: DigPlace 2/2, Harvest 2/2, SaveLoad, SolidRescue, CraftingPlay, InventoryPlay, BandFollowPlay, Transition, LeadQA M1Loop.
- P-54: a fill level per brushed tile (TerrainEdits v2: a byte of density per tile, set by the stroke's distance with a 2 m ramp; stored beside the edits, not in the edit byte's spare bits, because the ramp also touches tiles that no edit flips; v1 files read as whole tiles). A stroke traces 0.9 m on the axes, 0.755 m on the diagonal (1 m ramp: 0.62, a rounded diamond). DugWallsAreRoundAtAnySize: a 7-stroke hole's outline 0.744..1.051 m from its strokes (band −0.22 / +0.20; the outward 0.15 is the rock tips between strokes rounded off). Frames: u157/1_scoop..4_bridge re-shot 10:11; u158/5_vault_open shows a dug shaft (scalloped, no tile faces). u157/2_tunnel is weakly framed (the tunnel at the frame's foot); the smoke frames it properly.
- P-55: CraftingPlay asserts the Locked paper tint 0.64 ± 0.05 and no gold band (D-167 (5)).
- U-158: ResourceFinds on smooth planets (Earth in 0.5.0): 42 nodes (every 50-90 m), 65 pockets (every 40 m, 2-10 m deep), a data cache every 400 m, the Warden vault doors (x 1223; 3620 if open). Node: 1 item per Beam stroke × 3, then harvested (glances off) until a game day later; state saved in GameState.nodeStates / SaveData.nodes (additive, no version bump; LEAD ok 09:5x); the Builder never harvests; Mercury's Solarite node only in the twilight window (ResourceFinds.Workable). Pocket: hidden until a Survey pulse, then drawn in the cutaway with scan_x above; dug → 3 of its item straight into the pack (three 0.9 m drops beside the tile's own did not fit a one-tile hollow), the rest drops if the pack is full. Relic: 1 Datacore + flag relic:<planet>:<x>. Vault: opens (6-frame clip) when dug to; flag vault_door:<planet>:<x>. B-176's sheets in frame order, the glint every 4 s, scan_x pulsing; placeholders only while a key loads. Item drops now park over unloaded ground (a drop left behind fell through the missing outline and the solid rescue lifted it: a real bug, seen in HarvestTests).
- U-158 yields per 100 m of Earth: node items 3.08, pocket items 4.76 (42 nodes, 65 pockets, width 4096). At walking pace (4 m/s, 240 m a minute) that is ~7.4 node items a minute plus at most ~11 pocket items a minute (an upper bound: each pocket costs a survey and a dig 2-10 m down). 0.4.8's comparable dig source (hematite seams and ice in the top 10 m) is being counted in the build's Harvest run (the 09:5x log counted the wrong item ids: raw iron / copper / carbon / silica had no dig source in 0.4.8).
- U-161: on a smooth planet the stage datum is the walking curve (CurveAt averaged ±4 columns, the sea held at its water line, interpolated between the camera's columns); the desert / taiga / tundra draw B-179's sets; the set's lowest layer continues below (fillFromSet), never a flat block. Worst set-to-surface gap 0.40 m over 3 seeds × 6 biomes (limit 1 m). Frames: u156/*_050 re-shot 10:16 incl. the new 10_tundra; 8_snow now shows the taiga set (spruces, the frozen lake) meeting the ground at the surveyor's feet.
- Captures: u158/1_node_full (iron, B-176's sheet), 2_node_harvested, 3_scan_x (a water-ice pocket 4 m down, the X above), 4_pocket_dug, 5_vault_closed, 5_vault_open, 6_data_cache. Mercury's Solarite node capture rides U-159 (Mercury keeps 0.4.8's ground in 0.5.0).
- Seen, not mine: the forest set's crisp log and stump (B-133's near layer) read as floating over a valley (u158/1_node_full, also in 0.4.8-era frames).

## Next up
U-163 (Build 0.5.0) → after the owner's look: U-159 + B-181, U-160, U-162.

## Ready for review
U-157 (P-54 / P-55 in, b69d80c1), U-158 (b69d80c1), U-161 (b69d80c1); frames in reports/unity/u157, u158, u156 (*_050, 10_tundra). Earlier, still unjudged: U-129 slice 1 (SaturnStageTests ×4); U-130 slice 1 (UranusStageTests ×7); U-133 slice 1 (NeptuneStageTests ×8); U-146 (the survey scan pulse; UranusStageTests +1); U-144 (Neptune's -x zones, the drift, the anchor, the gust warning; NeptuneStageTests +3).
## Handoffs
(none unrouted)
## Blockers
(none)
## Proposals
(none open: P-51 / P-53 / P-54 / P-55 decided in D-159..D-167)
## For USER_ACTIONS
(none)
## Housekeeping
Editor churn in the tree (Generated/Models *.mat _MainTex fills, TMP font asset, existing animator.controllers, UnderwaterTint.mat, link.xml.meta, two InitTestScene files): never staged; my commits list files explicitly. MERIDIAN_SETUP.md at the repo root is untracked and not mine.
## HeavyJobLock
none held, no want (the check's last capture released 10:17). No background waiters.
