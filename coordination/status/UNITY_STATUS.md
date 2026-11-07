# UNITY STATUS
Updated: 2026-11-07 13:26 · Session: 7 (zuber-4e; D-113: session 6 is in coordination/status/archive/UNITY_2026-11-07.md)
## Current task
U-123 Mercury on the cartoon stage: the check against the real art. Started 12:5x. The code is in (6aff1d38, 6aa8e018); EditMode 356/356 at 12:01; the 12:02 PlayMode leg ran the whole suite bare into the 20-min cap (exit 124, no results), so it now runs as D-122 slices. All three Mercury exports landed by 12:49 (B-149 1e99fcc4, B-148 70c40e1e, B-150 cca20f60).
- Lock 1 DONE (12:53:52–12:59:17, 5.4 min, released; posted to LEAD): compile 0 / 0; CheckSetup imported the three exports (34 sheet animators, 5 rig sets); PlayMode slice 16/16: entry x 64 Twilight → backgrounds/mercury/twilight, no fallback, strips 2/2, 42 plants, datum 310.0; creep 2 crossfades → day; MercuryEntry 0.81 s; 20-creature AI p99 0.122 ms, max 0.207. Import results + the capture peek fix + GameInfo 0.4.4 committed ahead of lock 2: 4d531e8b.
- Lock 2 (13:04–13:09, two locks around BLENDER's slot): compile 0 / 0; LeadQA M3Inner 5/7, one red in LEAD's file (Step4's Venus deck from the pre-D-124 pixel rows: 770.63 vs 770.14 ± 0.3; LEAD fixed it, e201d1e1). CaptureU123Mercury 13:08: all the Mercury art draws, the Shadewyrm caught in a true peek (the 4d531e8b wait works), but the frames missed B-145: the camp sat in a seeded ~9 m impact crater (spawn surface 310 under a 320 ± 14 plain), so the sets stood 10 m low behind the plain; the trap's datum hung ~3 m over its floor (the nominal bowl had no noise); the camp's plants were all glassreed (grown in the twilight zone before the noon turn); the slate fill showed 64 px seams. → D-146 (LEAD 13:1x), written lock-free and committed 1e4c3915: no small crater within ±40 of the pad; Mercury's band datum = the generator's surface without small craters (the plain by the spawn, each trap per column); the strip fill tile one texel in from its frame's sides (the transparent gutters bled in under bilinear; the art's rows are clean); the capture re-grows the plants per clock turn. The rest of lock 2 (u118 / u110 / build) was stopped before it ran, so all of it runs on the D-146 code.
- Lock 3 STOPPED BY CLAUDE CODE FOR LOW MEMORY (13:22:06 to ~13:25, while my session sat idle): compile 0 / 0 and EditMode 358/358 done (D-146's two new tests green); the PlayMode slice was cut with no results; nothing after it ran. I removed my stale heavy_unity.lock at 13:25:39 (BLENDER's want of 13:22:11 goes now). Re-run waits for the owner's word in this window (the standing rule after a memory stop); asked. The chain as planned: compile + EditMode + the 10-class PlayMode slice + LeadQA M3Inner (one unity_check), CaptureU123Mercury, CaptureU118Mars (the lurker den), CaptureU110Scenes, BudgetGate + Build/MERIDIAN_0.4.4 (dev) + the 13-leg probe (the Mercury rows; the Creep row now prints the Mono heap and the native reserve per visit; on 0.4.3 both were flat, so the 7.5 MB/visit is outside Unity's allocators — a watch row, LEAD).
- Lock-free meanwhile: U-102 (the settings panel) drafted outside the tree; it goes in after the Mercury chain so 0.4.4 is the Mercury code only.
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
none held: lock 3 (from 13:22:06) was reaped for low memory ~13:25; my stale lock removed 13:25:39; no want filed until the owner says re-run.
