# UNITY STATUS
Updated: 2026-11-07 14:42 · Session: 8 (resumed 14:3x after a break; session 7's detail is in git log and coordination/status/archive/UNITY_2026-11-07.md)
## Current task
U-123 Mercury hand-off. Started 12:5x. Done in the chain since 13:58 (all foreground locks, each released):
- Captures 14:05–14:06: u123 Mercury day / twilight / night re-shot with the fill flat; u118 Mars + u110 Earth on the B-162 straight sets at 16:9 (LEAD read them, cycle 271 14:1x). Committed 9b213611 with the nine strip metas.
- P-48 (LEAD yes): strip sheets import Clamp in v (228687c0); the nine metas re-imported with wrapV 1 at 14:10 with B-165's RGBA re-export (e0f476c7), committed 9b213611. bundleVersion 0.4.4 in the same commit.
- BudgetGate 14:07–14:08: every Editor row green (Earth avg 6.42 / p99 14.44 ms, Space 3.10 / 5.72, Mars 4.61 / 8.13, storm 4.60 / 7.82, FX peak 5.15 / 10.72; launch 0.89 s; Mars entry 1.35 s Editor info). perf_2026-11-07.md holds the gate rows; the dev-build rows get appended by the probe.
- Build/MERIDIAN_0.4.4 (dev) BUILD OK 14:15, 550 MB, 75 s (includes P-48 + the B-165 RGBA strips). 0.4.3 stays the owner's build (D-144).
Still owed: (1) the 13-leg probe on 0.4.4 (`unity_profile.ps1 -Probe -SkipGate`, the player only, ~6 min): the Mercury legs + the Creep second loop with the Mono heap / native reserve per visit. (2) One short CaptureU123Mercury so the night frame shows whether B-165's RGBA gutters clear the 64 px dip (the 14:06 frames predate it; joins.ps1 measures it). (3) The hand-off commit: c2_mercury README + tests report + this file → U-123, B-148, B-149, B-150 to LEAD.
Blocked on memory: free RAM 0.65 GB at 14:37 with no Unity or Blender running (the gate is 1.5 GB). BLENDER's want (14:11, Uranus decks) is older, so it goes first when the gate opens (D-037 / D-039); I file my want once BLENDER takes the lock.
## Lock-free meanwhile (While waiting)
U-102 settings panel + U-124 title card / UiPaper drafts recovered from session 7's scratchpad; going in against HEAD (0.4.4 is already built, so they don't touch the Mercury build), committed ahead of their check.
## Last completed
U-118 Mars (Done cycle 269, 6227cc34, Build 0.4.3 = the owner's play build, D-144); U-128, U-112 (cycle 268).
## Next up
U-123 hand-off → C3 UI (U-124 + U-102 with B-151's panels) → Venus U-125 when promoted.
## Ready for review
(none until the U-123 hand-off)
## Handoffs
(none unrouted)
## Blockers
Memory gate (see Current task); not a code blocker.
## Proposals
(none open; P-48 yes, P-49 no, LEAD cycle 271)
## For USER_ACTIONS
(none)
## Housekeeping
Editor churn in the tree from the cut runs (TMP font asset, animator.controllers, UnderwaterTint.mat, link.xml.meta, two InitTestScene files): never staged; my commits list files explicitly.
## HeavyJobLock
none held; no want on file (BLENDER's 14:11 want goes first).
