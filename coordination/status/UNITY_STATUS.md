# UNITY STATUS
Updated: 2026-11-07 12:5x · Session: 7 (zuber-4e; D-113: session 6 is in coordination/status/archive/UNITY_2026-11-07.md)
## Current task
U-123 Mercury on the cartoon stage: the check against the real art. Started 12:5x. The code is in (6aff1d38, 6aa8e018); EditMode 356/356 at 12:01; the 12:02 PlayMode leg ran the whole suite bare into the 20-min cap (exit 124, no results), so it now runs as D-122 slices. All three Mercury exports landed by 12:49 (B-149 1e99fcc4, B-148 70c40e1e, B-150 cca20f60).
- Lock 1 (LEAD's order, 12:5x): one unity_check call: compile + CheckSetup (imports and addresses the Mercury sets, strips, rig set, sheets and burrow; builds their animators and the rig set) + the PlayMode slice MercuryStagePlay, MercuryEntry, MarsStagePlay, InnerCreature, HazardV2Play, Solarite, WardenPlay, BudgetGate, Transition, BandFollowPlay (~7 min). Numbers posted on release, then BLENDER's ≤ 6 min slot.
- Lock 2: M3Inner (LeadQA), CaptureU123Mercury (day with a Glassback, twilight at the terminator, night with the Shadewyrm at its burrow), the 16:9 re-shoots (u118/2_canyon, 3_lurker_den, 4_storm; u110's three) for the record, then the probe's Mercury legs + the Creep second-loop reading (≥ 7 MB again → add the Mono heap and the allocator reserve to the per-leg prints).
- Then the hand-off commit: reports/unity/c2_mercury/README.md (drafted 12:37), perf + tests reports, this file.
- 12:5x committed 2c9eac03: the frost strip's two .meta files (D-016; imported in the 11:29 chain, missed the Mars close commit).
## Last completed
U-118 Mars (Done cycle 269, 6227cc34, Build 0.4.3 = the owner's play build, D-144); U-128 (cycle 268); U-112 (cycle 268); batch B U-110 / U-111 / U-116 / U-119 / U-120 / U-122 (cycles 266–268).
## Next up
U-123 hand-off → C3 UI code lock-free (U-124 + U-102: 9-slice panels by their `slice` json, the settings panel, the intertitle title cards, the Film switch) → Venus U-125 when promoted.
## Ready for review
(none until the U-123 hand-off)
## Handoffs
(none open; LEAD 12:5x: lock 2 builds 0.4.4 as a dev build via a GameInfo bump; Build/MERIDIAN_0.4.3 stays the owner's, untouched, until LEAD rules otherwise under D-144's reopen clause)
## Blockers
(none)
## Proposals
(none open; P-47 0.4.4 = the Mercury dev build: LEAD agreed 12:5x)
## For USER_ACTIONS
(none)
## Housekeeping
The 12:02 cut run left editor churn in the tree (the TMP font material, eight space-prop .mat files, the surveyor animator.controller, AddressableAssetsData/link.xml deleted, one InitTestScene). Never staged; CheckSetup / the next batch run rewrite them; my commits list files explicitly.
## HeavyJobLock
want_unity.lock filed 12:49:57 (queue rank 4: U-123's check, after B-150); the lock is free since BLENDER's 12:49:08 release.
