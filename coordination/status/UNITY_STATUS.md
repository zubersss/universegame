# UNITY STATUS
Updated: 2026-11-07 13:0x · Session: 7 (zuber-4e; D-113: session 6 is in coordination/status/archive/UNITY_2026-11-07.md)
## Current task
U-123 Mercury on the cartoon stage: the check against the real art. Started 12:5x. The code is in (6aff1d38, 6aa8e018); EditMode 356/356 at 12:01; the 12:02 PlayMode leg ran the whole suite bare into the 20-min cap (exit 124, no results), so it now runs as D-122 slices. All three Mercury exports landed by 12:49 (B-149 1e99fcc4, B-148 70c40e1e, B-150 cca20f60).
- Lock 1 DONE (12:53:52–12:59:17, 5.4 min, released; posted to LEAD): compile 0 / 0; CheckSetup imported the three exports (34 sheet animators, 5 rig sets); PlayMode slice 16/16: entry x 64 Twilight → backgrounds/mercury/twilight, no fallback, strips 2/2, 42 plants, datum 310.0; creep 2 crossfades → day; MercuryEntry 0.81 s; 20-creature AI p99 0.122 ms, max 0.207. Import results + the capture peek fix + GameInfo 0.4.4 committed ahead of lock 2: 4d531e8b.
- Lock 2 (want filed 13:01:29 after BLENDER took its slot at 12:59:34; the chain waits through it): compile + M3Inner (LeadQA), CaptureU123Mercury (day with a Glassback, twilight at the terminator, night with the Shadewyrm at its burrow), CaptureU118Mars (the lurker den at 16:9; 2_canyon / 4_storm were re-shot 11:48 after both fixes), CaptureU110Scenes (16:9), then BudgetGate + Build/MERIDIAN_0.4.4 (dev) + the 13-leg probe: the Mercury rows and the Creep second loop (≥ 7 MB again → add the Mono heap and the allocator reserve to the per-leg prints).
- Lock-free meanwhile: U-102 (the settings panel) drafted outside the tree; it goes in after lock 2 so the 0.4.4 build is the Mercury code only.
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
lock 1 held 12:53:52–12:59:17 (released); want_unity.lock filed 13:01:29 for lock 2 (BLENDER holds its slot from 12:59:34).
