# LEAD M2 plan (L6–L10)

Produced 2026-10-30 by LEAD's planning pass over overhaul/integration + L5c (d2f4ed8). Living document: steps are marked in STATUS.md as they land.

Base: `lead/it-m1` at d2f4ed8. The five analyses disagreed on some points; this plan settles them as follows:

- **Sol play set.** The charter's 10 bodies, in `SOL_TRAVEL_ORDER` order. Europa and Titan arrive with W9. Digits 1–0 cover every nav row (Moon is 5).
- **Landable.** Earth, Moon and Mars only, listed in `config.SURFACE_READY`. Mercury and Venus are approach-only, so there is no Cairn-fallback placeholder (B.7).
- **Sun.**
  - The cruise envelope is 5R (1,000 km), outside the gravity taper.
  - While piloting there is a heat hazard: a caution at 3R, a 15 s danger countdown at 2R, and a recall at 1.75R.
  - Giants get a keep-out wall until L12.
- **Activation.** Only surface-ready bodies activate. While CRUISING, only the nav target can.
- **Saves.**
  - `MAX_COORD = SYSTEM_EXTENT`, enforced by a system edge for both cruise and piloting.
  - Velocity is at most 20 km/s, or at most `cruiseMaxSpeed(2·SYSTEM_EXTENT)` while CRUISING.
  - The landing pose and the player must be within 4R of the body centre.
- **Progress** lives in `Expedition`. SaveData writes `unlocked` and `discoveries` at the top level.
- **Sol stays behind `?system=sol`** until step 10.
- **No `placeLandedOn` hook.** The test-hook rule forbids it, so the light is checked inside journeys instead.

## 1. Steps

1. **L7a cruise core** (start now).
   - `Cruise.ts` changes:
     - `begin(…, hop=0)` sets maxSpeed to `cruiseMaxSpeed(hop)` and accel to max(5,000, vmax ÷ 3 s). Add `retarget(hop)`.
     - `safetyRadius(star)` = 5R.
     - Add the system edge.
     - Move `planPath(a, b, inflate, ids = BODY_IDS)` here from autopilot.ts:61-87.
   - Tests: `cruise.test` stays unchanged. A new `travel-route.test` checks:
     - the three M2 legs keep the Sun at 5R or more and every other body beyond 3.3R;
     - each leg takes at most 60 s of simulated time with 0 safety stops;
     - the Earth→Moon cap is about 21 km/s;
     - the edge stop holds;
     - the origin round trip at 1.5e8 m is under 1e-6 m;
     - a 90,000 km integration stays within 1 m.
2. **L6a Sun light** (start now).
   - `Lighting.ts` changes:
     - Pure functions `starOf`, `starLight` and `lightScale`.
     - `sunDir` slews with τ 0.4 s; `snap()` sets it at once.
     - Lighting becomes the single writer of `atmoUniforms.uSunDir`.
     - Fix the env `uSun` and the env key.
     - Intensity becomes 5.2 × `lightScale`.
   - Tests in `lighting.test`:
     - Quiet gets exactly `SUN_DIR` at scale 1.
     - Sol bodies get `sunDirFor`.
     - The Sun's angular radius from Earth is about 3.89°.
     - Flux falls outward.
   - The smoke test confirms the Quiet System is unchanged.
3. **L8 schema 2 and the title history line** (start now). The schema bump and the history line go in one commit, per charter N.
   - `SaveSystem`: `SAVE_SCHEMA = 2` with:
     - `bodyId` and `system`;
     - `discoveries`;
     - `unlocked` (catalog powers except 'walk');
     - `abilityState`, null-only for now.
   - `Expedition`: `SURVEY_BODIES = SYSTEM_BODY_IDS.quiet`, plus idempotent `arrive()` and `powerFor()`.
   - Game: call `noteArrival()` at land (:626), placeShipLanded (:976) and restore (:1599), never inside setMode.
   - Title screen: `#title-legacy`, `Menus.setLegacy` and `legacyText`.
   - Tests:
     - `save.test`:
       - a frozen schema-1 fixture is treated as legacy;
       - it accepts CRUISING at Neptune distance at 2e6 m/s;
       - it rejects 9e9 m and a PILOTING speed of 1e5 m/s.
     - `expedition.test`: arrive and powerFor.
     - `saves.spec`: literals change to 2, plus a short "earlier-version save" test.
4. **L7b/L6b Sol boot** (needs WORLDS A).
   - Boot calls `setPlaySystem` before `new Game`.
   - An Earth start replaces the Ilex literals at Game :109, 206, 215, 217-219, 1117 and 1137. newExpedition sets `lastSafeLanding` to the start pose.
   - MissionObjects is built only for `SURVEY_BODIES`, which avoids the throw at MissionObjects.ts:191.
   - Activation and the speed limit follow the policy above. Cruise receives the hop.
   - Panel: digits 1–0 and Star/Planet/Moon labels.
   - `bgCamera.far` is at least 33,000.
   - Lighting runs per body, with `snap()` on teleports.
   - Telemetry adds the light, the cruise cap and a bounded handoff log.
   - Test: `travel.spec` A, "Earth → Moon hop" (about 10–15 min): Tab+5 selects the Moon. It asserts:
     - cruise peak speed is at most the cap;
     - the handoff log is release Earth, then activate/show Moon;
     - landing slope is at most 12°;
     - the light is within 0.5° of `sunDirFor`;
     - there are 0 errors.
   - What the player sees: a start on Earth in real sunlight, then a hop of about 48 s to the Moon.
5. **L7c/L6c Sun bypass and hazards.**
   - The nav marker points at `planPath()[0]` while the direct line is blocked, labelled "bypass Sun".
   - `Heat.ts`: zone, timer, HUD warnings, and a recall after `stepper.advance`.
   - The giant keep-out wall.
   - Autopilot changes:
     - it uses `Cruise.planPath`;
     - a non-surface "arrived" phase;
     - `cruise.accel` at :257;
     - terrain-following descent below 3 km;
     - `release()` clears KeyQ, MouseRight and KeyC.
   - Tests: `heat.test`, and the Earth→Mars bypass is under 1.6× the direct line.
6. **L9a First Light state** (after step 3).
   - Add `FIRST_LIGHT` and the id grammar `${body}:route:${i}` / `${body}:poi:${i}`.
   - Add `reachRoute`, `chapter()` and `objective()`. The survey objective stays until Earth, Moon and Mars are in play.
   - `OnFootContext.power = powerFor(body)`.
   - Add `#journal-powers` and the "route" and "scan" markers.
   - Tests:
     - progression, out-of-order arrival and idempotence;
     - `ctx.power`;
     - the setMode regex at :96.
7. **L6d Sun disc** (needs WORLDS C). Pass the light's direction, angular radius and distance to `space.update`. A screenshot shows the disc agrees with the shadows.
8. **L9b routes and scans** (needs WORLDS E and F).
   - Add `updateRoute`.
   - Make the target kinds explicit (:793, :881, :1478).
   - A chapter advance sets the next nav target.
   - Test: a short First Light `expedition.spec` on Earth.
9. **L8b ability saves** (needs PLAYER A and B).
   - `unlocked` becomes `AbilityId[]`.
   - Add `parseAbilityState` and `saveState`/`restored`.
   - No schema bump is needed.
10. **L10a default flip** (after steps 3, 4 and 6 and the spec notices).
    - The start system comes from `?system=`, else the latest save's system, else Sol.
    - Port the smoke, flight, saves, expedition and profile specs to the Earth start.
11. **L10b M2 gate** (needs W3 unblocked, W5–W8 and P4–P8).
    - Add test hooks `photo('body')` and `geoProbe`.
    - `travel.spec` B, "First Light loop", covers:
      - four reloads: on foot mid-flight, LANDED on the Moon, CRUISING and PILOTING;
      - each power used once, plus the rule that a power works only on its own body;
      - Earth geography checks;
      - a revisit fingerprint and the counters.
    - A serial gate run of 5–7 h.

## 2. IFACE requests

**WORLDS** (one packet):
- **A** (blocks step 4): `bodies.ts:20-21`, declared after `SYSTEM_BODY_IDS`.
  - `export let PLAY_SYSTEM: SystemId = 'quiet'; export let BODY_IDS: readonly BodyId[] = SYSTEM_BODY_IDS.quiet; export function setPlaySystem(ids: readonly BodyId[]): void`. It throws unless the ids are non-empty, are catalog ids, and all belong to one system.
  - `environment.ts:48`: the default becomes `BODY_IDS[0]`.
  - Delete `SAVE_SCHEMA_VERSION` after step 3.
  - After P2: `BodyDef.power: AbilityId | null`, with the same strings.
- **B** (W7): `BodyProxies`.
  - A per-proxy constant `uSunDir = sunDirFor(def)` (:49).
  - Skip kind 'star' (:300/:307).
  - A smooth giant globe for viewing at R + 30 km.
  - A minimum on-screen size.
  - `update`, `readyCount` and `dispose` stay unchanged.
- **C**: `Space.update(q, pixelRatio, starFade, sun: {dir: Vector3; angularRadius: number | null; distance: number})`.
  - The billboard sits along `dir` at min(distance·BG_SCALE, 2600), and its core subtends `angularRadius`.
  - `null` keeps today's look.
  - Add limb darkening and a capped corona.
- **D** (notice): Lighting is the only writer of `uSunDir`. For M3, scale `sunIntensity` and cloud light by `lightScale`.
- **E**: `sites.ts`.
  - A Sol `prefsFor` that picks sunlit sites, Earth on dry land, and the Moon and Mars in flat basins with no relief within 3 km.
  - `computeSites` throws for explore 'none'.
  - `route: {id, dir, radius, label}[]` and `scans: {id, dir, label, note, tag}[]`, exactly 3 each for Earth, Moon and Mars and empty elsewhere. Ids follow the grammar above and are built without importing `src/game`.
- **F**: `MissionObjects`.
  - Relays and samples only in the Quiet System.
  - Kinds 'route' and 'scan', with a `label`.
  - `sync(reached)`.
- **G**: `Journal` iterates `SURVEY_BODIES` and adds First Light entries from `route` and `scanned`.
- **H** (W5): Earth geography support.
  - `geoToDir`, `dirToGeo` and `earthElevationM`.
  - The infill amplitude.
  - `SurfaceInfo.liquidLevel`.
  - A dataset-ready signal on the main thread and in the worker.
  - The subsolar lat/lon at EPOCH.
- **I** (questions and notices):
  - Does the Sun keep its real 274 m/s² gravity?
  - Can `BeltDef` gain `halfThickness`?
  - `planet.spec` should pass `&system=quiet` before step 10.

**PLAYER** (one packet, for P2):
- **A**: from `src/abilities/`, with no Three.js:
  - `AbilityId` (equal to the catalog power strings) and `isAbilityId`;
  - `AbilityStateSave = {state: 'walk'|'flight'|'speed'|'blink'|'drift'; …bounded numbers}`;
  - `parseAbilityState(x: unknown): AbilityStateSave | null`;
  - display names.
- **B**: `OnFootContext {body; power: AbilityId | null; restored?: AbilityStateSave | null}` and `OnFootHooks.saveState?()`.
  - `enter` activates exactly `ctx.power`.
  - `exit('board')` deactivates it.
- **C**: a restore rule for each power. Flight never ends mid-air; speed resumes as braking.
- **D**: `playerHooks` exposes `ability() → {id, state, active, charge, cooldown, preview?}` and a bounded `abilityLog()` of `{t, from, to}`.
- **E**: keep the `game.player` fields the autopilot uses (:449-525).
- **F**: Ilex specs pass `&system=quiet` before step 10.

## 3. Cross-task risks and how to retire them early

- **Precision at 1e8 m.**
  - Step 1 unit-tests the origin round trip and the cruise integration.
  - Step 4 raises `bgCamera.far`.
  - Above about 120 km/s the ship rebases every step. Test A records `timings.sim`. If it is over budget, skip `refreshQueries` while CRUISING.
- **Proxies: 10 bodies now, 12 at M3** (54 level-0 roots now).
  - Test A measures time to `readyCount`, draw calls, triangles and heap against the charter L budgets, before W7 is final.
  - Until WORLDS B lands, Mars renders lit from the wrong side (176° off). This stays hidden behind the Sol flag.
- **Save bounds.**
  - Step 3 tests Neptune distance, 2e6 m/s cruise, the edge and the 4R bound in Node.
  - Reload #3 (mid-cruise) in test B proves them in the browser.
- **Test time on SwiftShader.**
  - Geometry, heat, light and saves are checked in Node, in milliseconds.
  - Test A is the only routine Sol journey: under 15 min at the Low preset, 640×360, rendering every 120th frame.
  - Test B (45–60 min) and the 5–7 h serial gate run once, at M2.
- **The Sun on routes.** Mars is behind the Sun at EPOCH. The step 1 route test proves the bypass in Node.
- **Mutable `BODY_IDS`.** `setPlaySystem` runs before `new Game` and in each Sol test's `beforeAll`.
- **Earth recognizable.** This waits on the W3 network blocker (charter O) and is recorded as blocked, not faked.

## 4. Start now vs waiting

- **Start now:**
  - steps 1, 2, 3 and 6;
  - the pure parts of step 5 (`Heat.ts` and the planner);
  - both IFACE packets.
- **Waiting on WORLDS:**
  - step 4 on A (a small change);
  - step 4's visuals on B (W7);
  - step 7 on C;
  - step 8 on E–G (W5/W6);
  - step 11 on H, W3 and W5–W8.
- **Waiting on PLAYER:**
  - step 9 on P2 (A and B);
  - step 11 on P4–P8 and D.